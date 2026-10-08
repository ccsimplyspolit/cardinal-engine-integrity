# Lobby roster from the Relic lobby data (no heap heuristics)

Build **16.3.11308.0**. The Hex-Rays export in `K:\aoe4_dlc\aoe4\gamesource\reversed`
is this exact build (`meta/paths.json`), so its RVAs apply to the live image.
Supersedes `2026-09-27-lobby-model-direct-read.md` (its `PlayerSlots2..8`
container is a map descriptor; the 0x1209xxx "slot" class is the in-match
scoreboard player).

Every field below is exercised by `tools/lobby_dump_test` — it compiles the
overlay's own `lobby_model_reader.inl` and runs it against full minidumps
(custom lobbies 13632 and 18816_redump, matches 37560 and 60644, menus 37560
and 52968). Snapshots contain other players' names: they go to `%TEMP%`.

## Session

```
[image + 0x7B41DA0]  std::vector<Session*> begin / end (+8)
  session = *begin
  session + 2088     lobby / match id: -1 none, -2 transitional, > 0 real
  session + 56       status: 1 configuring, 2 starting, 3 loading, 4 playing, 7 error
  session vtable     0x6294F88 MPCustomMatchSetup, 0x6294D38 AutoMatchSetup
  session + 2048     GameSetup (copied into the UI model at +6016 by sub_7B8810)
```

The id stays set for the whole match (dumps 37560 / 60644: status 4).

## Source 1: the lobby screen model (front end only)

```
[image + 0x7B41E28] app -> +728 UI app (vt 0x62BD018) -> +840 FrontEndModels
  (vt 0x62E4A58) -> +992 OnlineStatusModel (vt 0x631D130) -> +632 lobby model
```

- vtable 0x626B788 (CardinalCustomMatchLobbyModel, factory sub_569910); the base
  0x62EB258 only while dying (dtor sub_FD4CD0). Checks: refcount +16 != 0,
  parent +64 == OnlineStatusModel, +6008 == session.
- Rebuilt on the UI thread by sub_FD81C0 (GameSetup copy +6016, MatchInfo copy
  +6664 from the RLink party). A read is bracketed by the refresh generation
  (+88, == `qword_7B41E68` at refresh) and the MatchInfo lobby id (+6672 ==
  session id); a cleared or moved vector is *Transient*, never an empty lobby.
- +6848 host profile id. +6976/+6984 slot vector (16 records of 528 bytes).
- Lazy flags `[stamp][functor][arg][value]`: IsOnline 552/576, IsSkirmish
  664/688, IsAutoMatch 776/800, IsRanked 832/856, IsTeams 888/912, IsHost
  1224/1248. A value is current only while its stamp is the UI generation
  (`qword_7B41E68`, RVA 0x7B41E68) or pinned (0x7FFF…); otherwise unknown.
  Automatch and host are therefore taken from the session vtable and from
  host id == local id.

## Source 2: the RLink party (lobby, automatch and in match)

```
root = [image + 0x84C8F08] (vt 0x6534C10)
  root + 6024 account (vt 0x65361A0), +416 local profile id
  root + 6128 PartyInternal service (vt 0x6538EC8)
    +120 / +128 vector<shared_ptr<Party>> (16-byte entries)
Party + 408 lobby id   + 472 MatchInfo   + 656 host profile id
      + 784 / + 792 slot vector (same 528-byte records)
```

Read lock-free (the root mutex at +3496 is never taken): the vector bounds and
the lobby id are re-read after each copy. The lobby model copies exactly this
data: in dump 13632 both give the same 8 slots, ids, names and host. In a match
(37560, 60644) it is the only source.

## SlotInfo record (528 bytes)

| off | type | meaning |
|----:|------|---------|
| +0 | u32 | state: 1 closed, 2 AI; 0 = player when +8 is set, else open; 3/4/5 with an id = pending / non-participant (not a player row) |
| +8 | i64 | Relic profile id (= aoe4world `profile_id`), -1 none |
| +16 / +80 | wstring | profile name / alias (shown name; +80 first) |
| +176 / +184 / +192 | | statgroup / XP / level |
| +328 | wstring | platform user id (SteamID64 text on Steam) |
| +360 | u32 | platform: 3 Steam, 11 Xbox |
| +392 | i64 | station / peer id |
| +400 | u32 | RLink `teamID`: the slot index in custom lobbies (alliance mode, sub_633650), the team in matchmaking |
| +416 | i64 | raceID: -1 none, 254 mod civ, else race PBG |
| +424 | u8 | AI difficulty 0..6 (Easy .. Absurd); RLink `rankLevel` byte |
| +448 | vector<char> | options JSON, NUL-terminated |
| +476 | u32 | slot index (a record whose index differs = torn copy) |
| +520 | ptr | parsed SlotOptions, created lazily on the UI thread — not read |

Options JSON keys used: `m_playerReady`, `m_playerColour` (-1 auto, -2 empty),
`m_startingPosition`, `m_randomStartPosition`, `m_isRaceRandomlySelected`,
`m_hardwareType`, `m_inGame`, `m_aiPersonality`, and **`m_teamAlliance`**
(SlotOptions+288; writer sub_8374F0, reader sub_8359E0): base64 of an int32 —
0.. = "Team k+1", **10001 = Auto** (the default; AssignPlayers picks the team
at launch), **10002 = No Team** (everyone is an enemy), -1 on empty records.
Dumps: every lobby slot Auto; the 8-player match 7,7,1,2,1,2,0,0 (2v2v2v2).

### Teams in a match

The game's player table holds the team each player really plays in, Auto
resolved: `G = **(image + 0x84C7E18)`, count at G+24 (0 in the lobby),
448-byte entries at `*(G+16)` or inline at G+40: +0 human, +40 team, +120
profile id, +128 local player. Entries follow the occupied slots in order
(AI, or state 0 with a profile id; sub_686920). Dump 60644 (all Auto in the
lobby) resolved to a 4v4: 1*,0,1,1,0,0,1,0 (the human with AI slots 2, 3, 6).
The reader takes the team from this table when the session is loading or
playing, from +400 in matchmaking, otherwise from `m_teamAlliance`; an ally is
a real team index equal to the local one, No Team is always an enemy, Auto in
the lobby is shown as "Auto" (not known yet).

### Lobby size

The game never stores it: sub_7780B0(session) computes it and the lobby screen
shows that many records (sub_FDEE40). The reader does the same read-only
(`LobbyCapacity`):

- desc = `*(session+2048)` (ScenarioDesc); no desc → 8 (cfg.max_players);
- its 152-byte player records at +800/+808: the count of records whose u32 +4
  without bit 1 is 0 (an empty vector means 16);
- for a generated map (desc vtable 0x6400048) capped by `max_players` (i32
  +56) of the map-size property group 0x330100 keyed by (0, desc+876), found
  in the property-bag registry `[image+0x84464B8]` (FNV-1a 64 of the type,
  buckets +640, mask +664, sentinel +624; group vector +24/+32 sorted by
  (+100, +104); data = `**(group+320)[u32 image+0x778A998]`).

Dumps: 8 / 2 / 8 / 8 for 13632 / 18816 / 37560 / 60644. The rows are the ones
the lobby screen shows (sub_7781F0): every slot that is not closed, plus the
first closed slots in index order up to the size — the slots the host closed
inside the lobby. The options-JSON rule (in-lobby slots carry a JSON) is only
the fallback when the size cannot be read: live it lost host-closed slots and
the slot of a player who had just left.

## Change triggers

- Poll every 250 ms (`NativeOverridesLobbyService`, Present thread; one poll at
  a time): any change of kind, player, civ, team, colour, ready, start
  position, AI difficulty, lobby size or host rebuilds the roster at once.
- Chat manager `[image + 0x84C7538]`: vector<ChatChannel*> at +96/+104; the
  lobby channel has +160 == 3 and +112 == lobby id; +8 counts its messages
  (chat lines and the "joins / leaves the match" notices). The slots are
  re-read every poll anyway, so a message is counted (UI tooltip) and logged;
  the roster is rebuilt only when what it shows changed.
- Back in the menus with no lobby (no session id, no live world): the roster is
  cleared.

## Overlay behaviour

- The read runs always (not only with the lobby scan's "Enable"): it is a few
  pointer reads plus at most 16 x 528 bytes and the lobby's option JSONs. The
  heap fallback (no model and no party) still needs "Enable" and no Hold.
- In the match the roster is the match's players only (open / closed rows
  dropped), with the teams from the game's player table; a team read that
  later fails keeps the teams already read for that match.
- Ally / enemy: 1 = same real team as the local player, 2 = other team or No
  Team, 0 = not known yet (Auto in the lobby; the UI shows "Auto"). hud_alerts
  labels an ally TC only with a team-1 row; the observer HUD never puts a row
  on the other side's card.
- Civ change only in a lobby you host and only before launch
  (`CivWriteBlockLocked`: 1 not the host, 2 the match started, 3 a heap-scan
  roster, which cannot tell host from guest). Live, a write of another
  player's slot in someone else's lobby (76 heap copies) was followed by the
  lobby dropping the user 0.26 s later, after a 15 s render-thread stall.
- A lobby row writes exactly its party record: `EnsureCivWriteTargets` (the
  SteamID heap search of the old roster) skips `fromModel` rows. On 29.09
  02:13:38 it still ran for a Steam player in the user's own automatch lobby:
  42 s with the frame blocked in "ui.present" and 57 heap dwords written, 9
  of them not civ values. Xbox rows (no SteamID) never searched, which is why
  one Apply was instant and the next froze.
- Civ targets must be catalog civs (`IsKnownCivPbg`); Force PBG no longer
  passes 0xFFFFFFFF or a mistyped id through.
- Civ change / hold write the race of the RLink party's record (the UI model is
  a per-frame copy and is freed at match start). The targets follow the party
  vector if the game moves it within the same lobby and are dropped when the
  party is gone for ~1 s. Every writer re-checks a party target right before
  writing (`LobbyTargetValidNow`: the party found again, the slot index at
  +476, a zero high dword of the i64 race); the hold writes only over a value
  that is still a civ.
- A lobby that disappears for one poll (the transitional id -2, a torn read) is
  not a leave: the roster is cleared after ~1 s without a session outside a
  match.
- The slot records are re-read after decoding; a record that changed while its
  strings / JSON were being read makes the poll Transient.
- `tools/lobby_dump_test/run.cmd <dump>` checks slots, match teams, the
  ally / enemy relations and the civ write targets against a Python mirror of
  the same rules.

## Not mapped / open

- The leaderboard id -> mode mapping of the UserStatsCache
  (`*(root+6048)+1896`, 104-byte LeaderboardStat records) — ELO still comes
  from aoe4world.
- Skirmish without Relic Link and automatch lobbies were not in any dump.
- Automatch team before launch: `LobbySlotTeam` uses the record's +400 there,
  never verified. Live 2v2 lobbies (29.09) showed m_teamAlliance -1 on every
  slot and resolved teams 0,0,1,1 in slot order once loading. The `[LOBBY]`
  slot line now logs `pos=` (+400) and a `shown` line (self / ally / enemy /
  ?) per poll to settle it from one quick match.

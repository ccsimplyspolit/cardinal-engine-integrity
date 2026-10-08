# 2026-09-30 — Level spoof, Rank spoof and XP boost: what they can do, and the fixes

Request: study Rank spoof, Level spoof and XP boost (Lobby → Memory → Profile), check the logic,
the source and the offsets, check that they do not conflict, improve them. Build 16.3.11308.

## Who sees a spoof

Nobody but the local player. Traffic capture of this session (HTTP Debugger, 385 RelicCardinal
transactions, login → custom lobby vs AI → joined lobbies → relog):

- Other clients load a player's XP, level and ranked-season stats from the server:
  `GET /game/CommunityEvent/getEventStats?event_id=160&group_type=1&member_id=<their profile>`
  (profile record `[.., statgroup, xp, level, region, ..]` plus the event stats row) for every lobby
  member, and `getStatGroupsByProfileIDs` / `getProfileName`.
- The client never uploads its own level, XP or rating. The lobby `slotinfo` the host sends has a
  `rankLevel` per slot (0 in every capture, even for the ranked account), and `metaData` has no
  level or rank.
- After a skirmish there is no client → server XP report: only GETs (`getRecentMatchHistory`,
  `getStatGroupsByProfileIDs`, challenge progress). Match XP is the server's.

So all three are local display changes. The UI said "Other players see this level" and "Other
players see a rating you do not have", and XP boost promised "faster levelling"; the texts now say
what happens.

The one place the client sends its level: telemetry `LobbySessionStart`
(`elfcardinal-eventhub.servicebus.windows.net/telemetry/messages`,
`CellLobbySessionStartExtension {"level":101,"totalxpearned":183616}`), after every
`/game/login/platformlogin`. Its builder `sub_7D61B0` (RVA 0x7D61B0) reads `profile+200` (level) and
`profile+192` (XP) — the same `[statgroup][xp][level]` blob the level spoof writes. A reconnect with
the level spoof on would report a level that does not fit the XP.

## Offsets (verified)

| Model | Field | Offset | Source |
|---|---|---|---|
| LocalPlayerProfileModel | XP / CurrentLevelXP / NextLevelXP | +764 / +812 / +860 | getters sub_10BC220 / 10BC500 / 10BC7E0 |
| LocalPlayerProfileModel | Level | +908 (was "inferred") | getter sub_10BCAC0, slot +864 |
| MatchReportModel | PreviousXP / PreviousLevel | +2068 / +2116 | getters 0xF3D990 / 0xF3DCE0 |
| MatchReportModel | Match / Challenge / Total XPGain | +300 / +348 / +396 | 0xF38280 / 0xF385D0 / 0xF38920 |
| MatchReportModel | MatchXPWin / Time / Score | +1924 / +1972 / +2020 | 0xF3CFA0 / 0xF3D2F0 / 0xF3D640 |
| CommunityEventModel | CurrentRankScore (lazy) | +1712 | getter sub_12A2710, block +1664 |

The profile and match-report offsets were right. The rank one was right but the wrong target:

- `CurrentRankScore` is a lazy block. Its compute function `sub_12A71B0` copies `*(u32*)(obj+1964)`;
  the getter recomputes whenever the block generation differs from `qword_7B41E68`, which
  `sub_C5C080` increments every UI tick. A write to +1712 is undone on the next read.
- On full dump 38348 all 8 live CommunityEventModel objects had +1712 = 0 and generation -1 (no
  screen had read it). The old search ("+1712 within ±280 of the aoe4world 1v1 rating") could not
  find them: hence "Score not found in memory" / "often not found in this build".

The ranked-season record the lazy blocks are computed from (ctor `sub_12A5080`, compute functions
`sub_12A6880`…`sub_12A7230`), checked on dumps 38348 and 13632
(`tests/adversarial/golden/rank_season_16.3.11308.txt`):

| Offset | Field | Offset | Field |
|---|---|---|---|
| +1896 | placements (5) | +1956 | region rank |
| +1912 | personal statgroup (u64) | +1960 | region rank total |
| +1920 | leaderboard (u64) | **+1964** | **rating** (CurrentRankScore) |
| +1928 / +1932 | wins / losses | **+1968** | **rank level** (CurrentRank badge) |
| +1936 / +1940 / +1944 | streak / disputes / drops | +1976 | last match (u64) |
| +1948 / +1952 | rank / rank total | +1988 / +1992 | highest level / highest rating |
| +2008 | event id (160 solo s14, 161 teams) | +2016 | byte: the server sent a record |

The rank table is in the event config (`obj+176`): a vector of 232-byte entries at +248/+256, entry
+16 the level, +64 its minimum rating (`sub_AD9CE0`, `sub_12A7150`). In memory it is Season 14's
`1:0 2:400 … 8:800 … 17:1500 18:1600`, and the server's own record agrees (rating 845 → level 8).
A season without a server record has statgroup -1: whose it is cannot be told (both such objects on
dump 38348 belonged to opponents), so it is never written.

## Bugs fixed

1. **Holds ran only in a match.** `NativeOverridesService` returns until the match world is live,
   and it held the level / rank / XP-boost freezes, the XP-boost rescans and the rank half of "level
   and rank together". The lobby card, the profile and the match report are all outside a match.
   The holds now run from `NativeOverridesLobbyService` (every Present) in `SpoofHoldTick`.
2. **Rank spoof wrote the recomputed lazy value and could not find it.** It now finds the local
   player's CommunityEventModel objects by class descriptor (the image qword at descriptor+0x28 that
   points at "CommunityEventModel", found in non-executable image pages), keeps those whose record is
   a server record with our statgroup, and writes the rating, the rank level for it from the event's
   table (the badge follows), and highest rating / level when lower. The hold rewrites every 250 ms,
   keeps the server's newer value for Stop when the 120 s refresh copies one in, and rescans the heap
   chunks that held a record every 3 s outside a match (copies new screens make). Apply again = Stop +
   Apply, so the originals stay the server's. Without a statgroup Apply runs the identity lookup
   first and continues by itself.
3. **Level spoof leaked into telemetry on a reconnect.** `LobbyActionsPostReconnect` (the Reconnect
   button and the auto reconnect) calls `NativeOverridesBeforeLogin`, which puts the real level back
   and stops the level hold; a running level apply is cut short and restored when it ends.
4. **XP boost scanned the whole heap every 4 s through the match** (up to 12 s each, holding the
   shared worker so Apply / civ scans were refused). It now scans only outside a match, 4 s after a
   match ends, doubling to 30 s while no report shows up. It also found nothing while the level spoof
   was on (PreviousLevel is then the spoofed level) — both are accepted now — and it wrote the same
   number into all six fields; now Total = Match + Challenge and Match = Win + Time + Score.
5. **Results were invisible**: the native status is shown only on the Lobby pane. Level / rank / XP
   results now go to the footer status (translated where the text is fixed).

## Not changed

- The VEH disarm (`NativeOverridesDisarmLevelOnCrash`) still stops all three on any unfiltered
  first-chance 0xC… exception, even one the game handles. Conservative; Apply again re-arms.
- No way to make other players see a spoof was added: it would mean sending forged data to Relic
  (the only candidate, the host's `slotinfo.rankLevel`, is 0 in every capture and the lobby card
  reads `getEventStats`).

## Checks

- `tests/adversarial/test_rank_season_record.cpp`: 325 checks on 10 dump records (rank table, parse,
  plan, spoof round trip, junk rejection). `run_host.ps1` in a clean worktree: `[OK] adversarial host
  tests` (the stale `scoring_inventory.json` regenerated only for the run, as on origin).
- Release DLL built (MSBuild, no warnings in the changed files); Profile pane rendered in EN and RU
  (`tests\ui_preview\build_ui_pages.cmd`), ui preview test: 22 checks, no ID conflicts.
- Not run live: the game was not running during the session. To check in game: Rank spoof → Apply
  in the main menu, open the profile / a lobby: badge and rating change, `[RNK] season obj=…` lines
  in the log; Stop puts them back.

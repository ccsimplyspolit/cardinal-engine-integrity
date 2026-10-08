# 2026-09-30 — Dodge against ScarToolKIT, and the 15-minute restriction

The owner dodged a found 3v3 automatch at 21:29:25 and got a 15-minute
matchmaking restriction. They asked for a comparison with ScarToolKIT's
dodge. The check was static: STK binaries and recovered source, the game
export, and full dumps. No live process was touched.

## Result

- **Same leave.** Every STK build on disk makes the same game call as our
  Dodge: Relic `0x76D030` on the same session. Nothing in that call separates
  a leave through STK from a leave through the overlay.
- **The restriction is the server's standard answer.** Leaving a found
  matchmaking match draws it whoever the client is. Capture S1 in
  `analysis/net_api/docs/AOE4_NETWORK_API.md:11138-11151` shows a plain game
  quit, with no tool, 11.6 s after accepting a match. The next search got
  result 11 with a deadline exactly 900 s after the leave.
  - The 30 minutes on 30.09 at 01:20 came about 35 s after the previous
    deadline expired, which fits escalation. The rule itself is not
    established.
- **No other leave in that session.** The previous match ended normally at
  21:23:25, when the others left. The one Dodge call at 21:29:25 is the only
  leave in the log.

## ScarToolKIT, every build on disk

The four builds are A (28.08), B (v4), C (v4.1) and D (v4.2, the
`recovered_sln` source). They were compared as unpacked dumps, disassembly
normalised by address. The dodge worker and wrapper are identical in all four:

- **Check:** reads `begin = [img+0x7B41DA0]` and `end = [img+0x7B41DA8]`, and
  requires `begin != 0` and `begin != end`. It then takes `session = *begin`
  (the first element, a double dereference) and requires
  `session >= 0x10000`.
- **Call:** writes "ScarToolkit" and this stub into the game with
  `VirtualAllocEx` / `WriteProcessMemory`:
  `mov rcx, session; mov rdx, "ScarToolkit"; mov rax, img+0x76D030; call rax`.
  It runs the stub with `CreateRemoteThread`, waits up to 3 s and frees both
  allocations. It never reads the exit code.
- **Throttle:** 10 s (qword 10000 at its static init), not 8 s.
- **Gate:** its own heap scan must have found at least one player. It has no
  phase check (lobby, loading and match are all allowed).
- **Nothing else:** no build touches the automatch cooldown or its state:
  - no `0x76D140`, `0x3074100` or `0x30732B0`;
  - no Info+0x158, result 11 or ban flag;
  - no dodge in the helper DLL, the Lua / SCAR scripts or the server
    config.

## The call, checked against the game

`0x76D030` does three things:

1. It sets session state `+0x38` to 5.
2. When the match service `[0x7B41E28]+0x330` is live, it runs the
   end-of-match report (session vtbl `+0x120` = `0x896D90`) and posts
   `MatchResultPosted`.
3. It always jumps to RLink root vtbl `+0xF8`. On the 16.3 dump (52968) that
   slot is `sub_2F8EB10` = `mov rax,[rcx+0x17F0]`, which returns the **party
   service** (vtable `0x6538EC8`). `+0x17C0`, returned by vtbl `+0xF0`, is the
   Automatch2 service. The older notes named this call "the Automatch2 leave
   report", which was wrong.

The party service's vtbl `+0x1C0` is `sub_3010520` (LeaveMatch):

- It looks up the party session whose `+408` equals the match id.
- It checks `sub_300D890` (connected).
- If `+776 == 0`, it calls `sub_30354C0`, which sends one byte, `0x1F`
  (packet type 31), on the match connection.

The game then sends `advertisement/leave`, `leave` and `stoppolling commit=3`
over HTTP. None of these carries the caller, the thread, rdx or a reason:

- 0x76D030 does not read rdx. It passes it untouched to two calls that do not
  read it either.
- The only thread-dependent code on the path is the one-time init of a static
  log string.

## Differences, and what changed in the overlay

| | STK | Overlay before | Overlay now |
|---|---|---|---|
| target | `*begin`, vector non-empty | probed `[begin]`, `*begin`, `end`, `*end`; no bounds | `*begin` of a non-empty vector (`ReadSessionVector`) |
| object check | `>= 0x10000` | a Relic vtable with code at `+0x120` | vtable `+0x10` == the leave (`0x76D030`) |
| match id | none | none | must be > 0 (-1 none, -2 transitional) |
| already left (state 5) | calls again | calls again (a second Leave) | refused: "Dodge: already left this lobby." |
| loading / playing | allowed | allowed | allowed (unchanged) |
| GameApp write before the call | none | `MpBypassDataClear` | none |
| rdx | "ScarToolkit" | "ScarToolkit" | "ScarToolkit" (unread) |
| thread | remote thread | Relic UI thread (PostMessage) | Relic UI thread |
| status text | its own | "Left the lobby." when the post succeeded | "Leaving the lobby...", then the result from the window thread |

The status line under the button and the search-cooldown phase use the same
resolver (`ResolveSessionSlots`), so an emptied vector never reads a freed
session. The button's tooltip now names the restriction.

### Old probing vs the new target on full dumps

| Dump | Sessions | Old picks | New | Same object |
|---|---|---|---|---|
| 18816, 19944, 24044, 26392, 37560 (22:40), 37716, 40392, 53820, 60644 | 1 | `*slot0` | OK, state 4 | yes |
| 18816 redump | 1 | `*slot0` | OK, state 1 | yes |
| 37560 (22:29, menu) | 1 | `*slot0` | refused: match id -2 | — |
| 13568, 52968 (menu) | 0 | nothing | refused: empty vector | — |

Every live session is `MPCustomMatchSetup` `0x6294F88`. `AutoMatchSetup`
`0x6294D38` has the same `+0x10` (`0x76D030`) and `+0x18` (`0x76D140`). The
30.09 07:00 live dodge through the earlier session-vector resolver
(`fa4d571889`) left a found match as well
(`2026-09-30-info-dto-target-regression.md`).

## LOCAL-ONLY

1. **Lobby.** Press Dodge in a custom lobby. The log shows
   `[LOBBY] Dodge obj=*begin … match=… state=1 sessions=1`, then
   `Dodge UI-thread ok`, and the status bar reads "Left the lobby.".
2. **Menu.** Press it in the menu (the button stays enabled). The status bar
   reads "Dodge: not in a lobby", and the log shows
   `Dodge: no session (begin=… end=…)`.
3. **After the match.** Press it on the score screen (state 5). The status bar
   reads "Dodge: already left this lobby.".

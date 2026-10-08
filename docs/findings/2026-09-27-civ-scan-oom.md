# 2026-09-27 — 21:26 hang: the civ AUTO heap sweep ran for the whole match

The game (PID 46840, build 16.3.11308) froze at about 21:26 and was closed as
not responding. The civ roster sweep (`CivScanWorker`) had run back to back
for the whole 110-minute match, and each sweep also found what the sweeps
before it had left in the heap. That grew one sweep to about 3.5 GB and 55 s,
and the system ran out of commit.

## Evidence

| Time | Source | What |
|---|---|---|
| 19:27:56 | `LogFiles\unhandled.2026-09-27.19-27-56.txt` | game session starts |
| 19:37:41 | `Matches\aoe4_match_46840_20260927_193741.ndjson` | the only match of the session starts; last record 21:27:24, `timeSec` 6582 |
| 19:37:46 – 21:27:33 | `hh\debug-78fb47.log`, `after_heap` | 208 sweeps; a sweep was running for 4 835 s of the 6 587 s |
| 21:27:17 | System, Resource-Exhaustion-Detector 2004 | virtual memory exhausted: RelicCardinal.exe (46840) 14 450 290 688 B, steamwebhelper 2.9 GB, Discord 1.5 GB |
| 21:27:20 | System, Application Popup 26 | "virtual memory low" |
| 21:28:09 – 21:28:12 | Application, 1002 / WER AppHangB1 | RelicCardinal.exe not responding, closed |

The last sweep started at 21:26:38 and logged `after_heap` at 21:27:33, so the
commit exhaustion falls inside it. No BugSplat report exists for 46840. The
21:33 BugSplat report (`[Sync error]`, session up 283 s) belongs to the next
process, 53892 (see [the desync note](2026-09-27-start-desync-map-sight.md)).
The page file was fixed at C: 16 GB + D: 12 GB, with 31 GB RAM.

Sweeps from `after_heap` (anchors = Steam text anchors kept, small = regions
of 2 MiB or less):

| Time | anchors | elapsed | small regions | chased |
|---|---|---|---|---|
| 19:37:46 | 16 169 | 5.8 s | 6 215 | 496 |
| 19:41:12 | 1 064 489 | 10.1 s | 6 669 | 20 000 |
| 19:43:35 | 3 833 098 | 9.6 s | 9 429 | 18 271 |
| 19:48:14 | 9 057 353 | 14.5 s | 11 429 | 15 841 |
| 20:17:17 | 16 487 773 | 32.2 s | 19 741 | 20 000 |
| 21:05:52 | 19 056 819 | 51.8 s | 24 707 | 15 190 |
| 21:27:33 | 18 895 265 | 54.9 s | 42 667 | 20 000 |

## Mechanism

1. **The sweep only runs in a match, and it ran without a break.**
   `NativeOverridesService` returns until `RadarSimWorldLooksLive()`. With
   Lobby "Enable" (`g_civAuto`) on, its branch
   `g_civPlayers.empty() || now >= g_nextCivFullAt` started a new
   `CivScanWorker` 6 s (`kCivFullRescanMs`) after the previous one ended. In a
   match the roster cannot change, so every sweep after the first was waste.
2. **Each sweep feeds the next.** Every Steam text hit becomes a
   `SteamAnchor { address, std::string id, kind }`. 17 characters is past
   MSVC's SSO, so each id is its own heap block holding the ASCII text. The
   scan copies these strings again: the collectors' temporaries, the `kept`
   copies in `DropIsolatedTextAnchors`, the `insert` into the global vector,
   and the `Hit` copies in `FindLobbyCluster`. Freed blocks keep their text.
   The next sweep reads the whole private heap and finds those strings, in
   packed runs of distinct ids, which is exactly what `DropIsolatedTextAnchors`
   keeps. In a lobby, the region count held still while the anchors grew: six
   sweeps from 19:21:44 to 19:22:56 went 5 410 → 7 852 → 28 798 → 66 489 →
   75 595 → 134 692 anchors, while the small regions went 3 503 → 3 527. The
   heap had not grown; the anchors had. Each series starts over at 5–8 k after
   a pause, once the residue is overwritten.
3. **Memory.** An anchor costs about 96 B: 48 B `SteamAnchor` plus a 32 B
   string block with its heap header. `FindLobbyCluster` copies every text
   anchor again, 40 B plus the string. At 18.9 M anchors that is about 1.8 GB
   plus 1.7 GB in one sweep, before vector growth. These figures are computed
   from MSVC x64 layouts, not measured. The overlay log of 46840 was rotated
   away by the next launches, so the process commit over time was not
   recorded.

## Fix

- `civ_scan_policy.h` (new, pure): a full sweep is a per-match event. There is
  one at the start of the match. After that, a sweep runs only as a retry
  while the roster is empty or the cached refresh reports stale. Retries are
  at least `kRescanGapMs` (60 s) apart, counted from the start and again from
  the end, and a match gets at most `kMatchSweepLimit` (3). A new match is a
  live service call after more than 45 s without one. That is longer than the
  12 s age-up probe flicker and shorter than any lobby plus loading. The
  cached refresh (`RefreshCachedCivPlayers`, 750 ms) keeps running.
- `NativeOverridesService` uses the policy. A stale refresh no longer starts a
  sweep on any 750 ms tick.
- `ScanLobbyRegions`: `kMaximumCivAnchors` (1 M) stops a sweep and logs
  `[NATIVE] CivScan <phase>: anchor cap ...`. Lobby sweeps found 5 k–135 k.
  The region buffer is reserved once (8 MiB), because growing it region by
  region left freed heap copies of the smaller regions.

The scan's own strings are not scrubbed here. The "Lobby memory" session owns
that change (zeroing ids before free), together with the Relic lobby-model
reader that replaces the heap roster.

## Verification

- `tests/adversarial/test_civ_scan_policy.cpp` replays matches against the
  production policy. The service branch and its tail are mirrored in the
  test, not linked.
  - Old 6 s timer on the crash match (sweep 5.5 → 55 s): 224 sweeps. The log
    had 208.
  - Fixed: 1 sweep for the whole match, the cached refresh keeps running.
  - Empty roster or an always-stale cache: exactly 3 sweeps, at least 60 s
    apart.
  - 12 s age-up gaps: still one match.
  - A 60 s gap before the next match: that match sweeps within 1 s of its
    start.
  - The old behaviour put into the header fails the test: 224 sweeps.
- `native_overrides.cpp` compiles clean under `/W4 /sdl /permissive-`, both
  alone on HEAD and with the lobby-model work in the tree.
- The Python source tests that read `native_overrides.cpp` pass (73).
- Not verified live: no match has been played with this build yet. Until the
  game is restarted with it, keep Lobby "Enable" off during matches.

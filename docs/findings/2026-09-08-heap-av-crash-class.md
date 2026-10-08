# 2026-09-08 — in-match heap-allocator AV is a different crash class from the relock fail-fast

Session 00:41:07–00:42:35 (88 s, `9b9c9781` first run). Match started 00:42:04, process died 00:42:35 — **30 s into a live match**, `ents=321`. Log ends mid `[REGION]` snapshot with **no `[CRASH]` line**.

## Crash class taxonomy — do not conflate these two

| | relock crash (Sep 1–2) | this one (Sep 8) |
|---|---|---|
| WER code | `c0000409` | `c0000005` |
| Meaning | `STATUS_STACK_BUFFER_OVERRUN` / `__fastfail` | access violation |
| Faulting module | `StackHash_b4ee` | `ntdll.dll` `+0x3d5b2` |
| When | match exit / teardown | 30 s into a live match |
| `last_native` | `AI_LockSquad relock` | none — no crumb, no `[CRASH]` |

`ntdll+0x3d5b2` sits `+0xa72` past `RtlAllocateHeap` (`+0x3cb40`, nearest export below; `RtlReAllocateHeap` is the next one at `+0x42180`). So the AV is **inside the heap allocator**: the heap's own metadata was already damaged and the failing allocation is the victim, not the culprit. Four `AppHangB1` reports landed in the same second, which is what a damaged heap lock looks like to other threads.

**Why no `[CRASH]` line.** VEH writes that line for every exception it catches, and it allocates to do so. On a corrupted heap the handler faults a second time inside itself, so nothing reaches the log. A silent tail therefore means *heap* damage, and is not evidence of fail-fast — the Sep 1–2 fail-fasts are silent for the unrelated reason that `__fastfail` never dispatches to VEH at all.

## The relock teardown gate held

Not the crash from `2026-09-08-relock-teardown-scout-fasttc.md`. Relock kept posting normally to 00:42:33 (`cmd#113 label=ai_lock_army_relock ok=1`), and death was mid-match, not at exit.

One caveat on the probe: `Radar: Marks scan stopped — match world gone` fired at 00:42:09 while the match was plainly live (`ents=316`, and still 321 at 00:42:34). `ProbeSimWorldLive` therefore yields **false negatives in the first seconds after match load**, presumably across an EntityManager rebuild. For the relock gate that is benign (a skipped pass retries), but do not treat the probe as an authoritative "match is alive" oracle.

## Ruled out as the corrupting write

- **`bpName(sq)` in the relock crumb** (`9b9c9781`): every call `pcall`-wrapped, reads only.
- **The new `[AI] eco_goal` `LogWrite`**: 15 conversion specifiers against 15 arguments, types match, printed cleanly 4×. A format/argument mismatch here was the leading suspect because the line printed 200 ms before death.
- **The relay-region scan**: the 09-07 22:17–23:30 session ran it **87 times** and exited cleanly, so it does not corrupt the heap on its own.

Root cause is **not identified**. A heap AV needs the faulting thread's stack; the WER report directory is unreadable without elevation and carries no minidump.

## Actions taken

**WER LocalDumps armed** for the next occurrence — `HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\RelicCardinal.exe`, `DumpFolder=E:\aoe4_dumps`, `DumpType=2` (full memory — heap metadata is required, a stack-only minidump would just re-show the victim allocation), `DumpCount=3`. `E:` because a full dump of the in-match process is ~3 GB and `C:` has 29 GB free.

**Relay scan no longer starts in-match** (`RegionBlockService`). `ScanVectorRuns` `VirtualQuery`-walks the whole user address space and copies every committed private RW region (≤ 16 MB) through a heap buffer. In the menu that is ~0.3 s; in the ~2.8 GB in-match process the 09-07 log shows the cadence stretch from 45 s to 91 s, i.e. the walk held **~45 s out of every 91 s while the sim ticked**. The relay list is matchmaking data handed out at login and cannot change mid-match, so deferring to the menu costs nothing. Once a live list is in hand the refresh drops to `kScanIdleMs` (10 min) instead of 45 s. Manual Scan stays ungated. This is a load/hang fix on its own merits, not a claimed crash fix.

Also seen in the 09-07 log: two `[REGION] snapshot` lines at the identical millisecond (23:30:13.322), i.e. two scan workers finishing together. Not chased.

## Test suite

`test_injector_hardening.BridgeCmdTests.test_release_ignores_temp_commands` had been failing at HEAD, unrelated to any of the above. It required `#if defined(NDEBUG)` -> early return in `BridgeWatchPollCommands`, but that gate was **deliberately removed** (rationale in the comment above the function: Release is the only build ever injected, and the on-disk `.text` is encrypted, so a live image dump at the moment a crash reproduces is the only readable form of that code). The test was the stale side. Replaced with the contract that actually holds — reachable in Release, `DeleteFileW` consumes the drop, 200 ms rate limit kept, and a new `test_command_channel_is_per_user_temp` pinning the drop path to `GetTempPathW` so it cannot drift to a world-writable location. 93 tests green.

## Unverified after the 00:41 run

The match lasted 31 s, so most of `9b9c9781` never got exercised. Do not read "no crash at exit" into that run.

- **Relock teardown gate — untested.** Exit-to-menu never happened; the process died mid-match. (Verified in the 01:01 run below.)
- **Hippodrome Scout fix — untested.** The whole log has **zero** occurrences of `bp=`, `hippodrome` or `dummy_champion`. The scout never reached a lock decision, so the broadened name filter was never exercised. Nothing was relocked except villager-ish sids (`50014`, `50087`, …), all `skip-eco`. Still unverified after the 01:01 run too.

Two load-time costs worth noting, neither a heap lead:

- `[PRESENT] skip overlay 2.5s after 649 ms GPU Present` / `SKIP overlay reason=gpu_fault` at 00:42:04. `present_hr=0x00000000` on that line — Present returned `S_OK`, so this is **not** a device-removed/TDR event. `gpu_fault` is our own label for a slow Present, here a map-generation hitch. Overlay drawing resumed and was healthy (`UiD3D12OnPresent frame #4500` at 00:42:33).
- `Radar: Marks AVUI tree walk missed (25728 nodes, 2625 ms)` twice, then `Marks widget not found (2719 ms) — next attempt in 60000 ms`. Over 5 s of UI-tree walking inside the match's first 8 s.

Fast TC was **auto**-selected, not set by hand: `[00:41:18.717] [AI] lock mode auto -> fast_tc`.

## 01:01–01:11 run — teardown gate verified, region gate had a hole

Session 01:01:59, PID 19012, DLL `00:55:22` (the region-gate build). Match 01:03:09 → exit 01:10:58, ~9 GB working set at peak.

**Relock teardown gate: verified.** `Radar: Marks scan stopped — match world gone (8 MB in)` at 01:10:54, then a clean shutdown. Zero `[CRASH]`/`[SEH]` lines, zero WER events, no dump. This is the first real match teardown the gate has seen, and it held — which is what `9b9c9781` was for.

**The region gate was insufficient: it only gated the kick.** Observed cadence:

| Time | Event |
|---|---|
| 01:02:24 | scan #1 finishes (menu) |
| ~01:02:52 | scan #2 **kicked** — world not live yet, so the gate let it through |
| 01:03:06 | Relic Scenario Lua System starts |
| 01:03:10 | `ents=427` — world live |
| 01:03:17 | scan #2 **finishes** — 25 s of address-space copying straight through match load |

`RegionBlockService` checks liveness at kick time, and a walk already in flight cannot be stopped that way. Fixed by folding inside `ScanVectorRuns`: it re-checks `RadarSimWorldLooksLive()` per region and returns false, mirroring the marks scan's "match world gone" abort. `ScanWorker` bails without calling `FinishScan` on a fold — otherwise the short row set takes the "scan miss" path and overwrites a good menu snapshot with `ready=false`, leaving Apply reporting "no live snapshot" while its firewall rules are still installed.

The 10-minute idle interval did work: 2 scans in a 9-minute session, against 87 in the 72-minute session before the change.

## Fast TC — the 2nd TC lands, but stone never gets a worker

Live TC count from the eco-contest line changed exactly once all session:

```
01:03:08.701  ->  tc=1 age=1
01:08:09.199  ->  tc=2 age=1
```

The plan then released stone on its own: `ds` 300→160, stone share 0.46→0.04, gold back to 0.14, `op` 1→0. So the C++ side of Fast TC completes its cycle.

**But the assignment never reaches stone.** `want` against `have` across the opening:

```
01:04:49  want=F4/W11/G0/S10   have=F11/W3/G0/S0
01:05:33  want=F5/W9/G0/S13    have=F11/W6/G1/S0
01:06:15  want=F5/W9/G0/S15    have=F4/W20/G0/S0
01:06:55  want=F7/W7/G0/S17    have=F10/W14/G0/S0
```

`have` stone is **`S0` on every single line** while `want` climbs to 17. Wood tracks (`have=W20`), food tracks, gold tracks — stone alone never receives a villager. That is the user-visible "workers don't go to stone" complaint, and it sits in the actuator/assignment path, not in planning: the desire and the plan are both correct.

Second signal from the same lines: `idle` runs very high through the opening — `workers=21 idle=21` at 01:03:34, and 12–21 idle out of 20–21 workers throughout. Whether `idle` there means "standing still" or "available to reassign" has to be read out of the eco-contest source before concluding anything.

Not addressed in this commit. Next step is the SCAR-side assignment path (`__EcoAct_Apply` / `eco_contest`, `thin actuator v56`, "gathering REPLACE re-assert") and specifically why the stone bucket never binds.

## 01:31–01:58 — three distinct crash classes, and `last_native` cannot tell them apart

Three deaths in one evening, and they are not the same bug:

| | 01:31:10 | 01:52:14 | 01:58:21 |
|---|---|---|---|
| `[CRASH]` line | yes | yes | **none** |
| WER event | none | none | **none** |
| RVA | `0x1ED50B9` | `0x36A7E7F` | — |
| AV type | read from 0 | **write** to 0 | — |
| `scar_label` | `eco_ai_cuts` | `-` | — |
| `in_call` | **1** | **0** | — |
| `last_native` | `AI_LockSquad relock sid=50254` | `AI_LockSquad relock sid=50855` | `…sid=50080` (crumb file) |

All three reported `last_native=AI_LockSquad relock`, and for two of them that is provably wrong: 01:31 faulted *inside* `eco_ai_cuts` while the relock DoStrings had all returned `ok=1` moments earlier, and 01:52 faulted with `in_call=0` and `scar_label=-`, i.e. outside any SCAR call at all.

**`LogNoteLastNative` is a one-way marker.** It is written before a native that can AV and nothing ever cleared it, so the relock -- which rewrites it every ~400 ms -- names itself at any later crash. The 2026-09-08 relock teardown gate was chosen on exactly this evidence and therefore aimed at the wrong code. The trustworthy fields are `scar_label` / `in_call`, because `LogNoteScarBegin` / `LogNoteScarEnd` are paired. Fixed: the crumb is dropped on the relock success path. `NoteRelockSeh` prefers `g_relockAttemptSid` and only falls back to the crumb, so poisoning is unaffected.

**Why LocalDumps never produced a dump.** `VectoredHandler` logs and returns `EXCEPTION_CONTINUE_SEARCH`, and Relic's own handler then catches the AV — the process survived 01:31 and kept running for 20 minutes. WER only fires on an exception nobody handled, so `DumpType=2` had nothing to capture. Zero WER events across the whole evening confirm it. Getting a stack for these needs `MiniDumpWriteDump` inside our own VEH; there is no `MiniDumpWriteDump` anywhere in the tree today.

The 01:58 death is a third class again: no `[CRASH]` (so VEH saw no exception), no WER (so no unhandled exception either), no RA kick line, and `eco_ai_cuts` had been running `ok=1` fifty seconds earlier. `TerminateProcess` produces no WER, which is the leading reading. Naming the caller needs an `NtTerminateProcess` hook, which we do not have and which carries its own detection cost — not taken.

The documented relock-container race (`g_relockPoisonSids` / `g_relockNotArmy` / `g_relockSafeMiss` / `g_relockSafeSince`, `AI_BOT.md`) was audited: every mutation is under `RelockMapsGuard`. Only the two `.size()` reads in the pass log are unguarded, which tears an integer rather than a bucket. That mechanism is closed and is not the 01:58 signature.

## The 01:31 crash was ours: a zero player handle, forwarded

`__EcoAct_Apply` fetched the handle and guarded it like this:

```lua
local ok, player = pcall(Game_GetLocalPlayer)
if not (ok and player) then return end
```

In Lua only `nil` and `false` are falsy, so **a zero handle passes**, and it went on to every availability / income / score native as the first argument — matching `rcx=0` and the read from `0x0` exactly. `pcall` does not catch a native AV, so nothing downstream could save it. The same RVA had already been seen at 21:45:51 under `eco_farm_ring`, where only the retain-list fallout was fixed and the null itself was left in place.

Measured against the real actuator Lua with a zero handle, guard reverted vs fixed:

| | `availCalls` | `incomes` | `pushes` | `__EcoAct.gen` |
|---|---|---|---|---|
| old guard | 11 | 6 | 4 | 7 |
| fixed | 0 | 0 | 0 | −1 |

So the old form forwarded the zero into 21 native calls. Now rejected in `__EcoAct_Apply`, `__EcoAct_Restore`, `__ArmyLock_LockOneSid` and `kArmyRelockTick`. Four tests cover it, including that the guard does not latch (a zero pass must not disable the actuator) and that `gen` stays open so the next real commit still applies.

## The match that would not end

At 01:41–01:52 both enemies surrendered, the match did not end, and the user's own surrender button did nothing either. Cause **not** established. What is known: the SCAR VM was healthy — 4100 DoStrings between the 01:31 crash and the exit, every one `ok=1`, with a single `ok=0` (the crash itself). So a dead Lua rule scheduler does not fit. The eco actuator was parked from 01:31 onward, and the overlay wraps Relic `Rule_*`, which is where victory conditions live, but our own scripts do not go through `Rule_*` and kept working — so that remains a hypothesis, not a finding.

## The liveness probe is thread-affine, so the region fold was a no-op

`ProbeSimWorldLive` resolves the world through `CurrentTlsBlob()` — the TLS of
whichever thread calls it. A worker `std::thread` has no Relic TLS blob, so on
a worker the probe returns false unconditionally. The fold added in
`63090fa37c` sits inside `ScanVectorRuns`, which runs on exactly such a worker,
so it could never fire. Proof from 02:21 session: the world was live at
02:22:16 (`[WORLD] collect n=500`, `ents=500` at 02:22:17) and the walk still
ran to a **full snapshot at 02:22:49** with no `scan folded` line anywhere.

The probe's 150 ms cache was plain function statics shared by every thread, and
that is what hid the problem — a worker sometimes read the answer Present had
just computed, and sometimes served Present its own false. Both directions were
observed: `Marks scan stopped — match world gone` at 00:42:09 and 01:10:54
during plainly live matches (a worker false reaching a live-world decision), and
the region walk above (worker false, fold dead).

Fixed by publishing the Present-thread answer into an atomic
(`g_simWorldLivePub`, plus `g_matchSessionLivePub` for
`RadarMatchSessionLooksLive`, which is TLS-bound through both of its inputs) and
moving every worker call site onto it: the marks-scan abort, the region-scan
fold, `WorldCacheNeeded`, and the collect worker's cache-drop.

Two traps worth recording. First, `WorldCacheNeeded` runs on the collect worker
and gates on `if (RadarSimWorldLooksLive()) g_sawSimWorldThisSession = true;` —
with a thread-local cache that flag would never be set and the world collect
would stop entirely, so the shared cache was load-bearing, not just sloppy.
Second, making the cache thread-local is **not** safe: the window thread runs
every `ScarDoString` and reads the same value through `ScarInMatchWorld()`, and
there is no evidence its TLS resolves a sim blob — a false there blocks all
scripts. The cache therefore stays shared, and the fix is that no TLS-less
thread calls the probe any more.

## Capturing the game's own account of a death

Relic writes `Documents\My Games\Age of Empires IV\warnings.log` and **rotates
it on every launch**, with no backup. The 02:16:33 death record was already gone
by the time it was looked for, because the game had been relaunched at 02:18.

A watcher now copies `warnings.log`, the overlay log and `session_data.txt` into
`E:\aoe4_dumps\deaths\<stamp>` the moment `RelicCardinal` disappears. It adds no
hooks and no detection surface. First capture (`20260908_022545`) is a clean
user-initiated exit, which gives the baseline to compare against:

```
[GameApp] Requesting game quit with reason: Prompt Quit App
Unloading step: [...]            (the full sequence)
Application closed without errors
```

So a silent death is discriminated directly: no `Requesting game quit` and no
`Application closed without errors` means the process was killed, while a
`Requesting game quit with reason: …` line means the engine chose to exit and
names the reason. That settles the 01:58 / 02:16 class without an
`NtTerminateProcess` hook.

Incidental, from the same capture: `dwError=12029` (cannot connect) on
`HCHttpCallPerform` and a `401` on `ChatChannelCache`, consistent with the
region-block firewall rules this session installed for brazilsouth and
australiasoutheast.

## Fast TC — confirmed applying

The telemetry added in `9b9c9781` paid off immediately; it fired 4× this session:

```
[AI] eco_goal op=1 lock=fast_tc civ=mac df=642 dw=400 dg=220 ds=300
     g=0.43/0.29/0.03/0.25 tc=2 iu=0.45 ia=1.00 ic=0.10
```

`tc=2`, cost `dw=400 ds=300`, and the gatherer split `g=` (food/wood/gold/stone) puts **0.29 on wood and 0.25 on stone**. So the preset reaches the actuator with correct numbers — the remaining question for "workers don't gather / no 2nd TC" is whether the SCAR side acts on that split, not whether the C++ goal is right.

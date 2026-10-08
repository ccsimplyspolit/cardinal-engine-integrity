# 2026-09-12 — five-agent code audit: what was fixed, what was deferred

Five read-only audit agents over `internal/InternalInjector` (relock/LockOneSid,
eco_ai_cuts 09:34 AV, radar/marks/liveness, VEH/D3D12/Present, test coverage).
Everything below landed at HEAD unless marked deferred. Host suite green
(`run_host.ps1`, `[OK] adversarial host tests`).

## Landed

**WM_APP collisions were live at HEAD.** The 09-07 finding prescribed the
remap but the code never had it: `FOW_NATIVE == WM_SCAR_AI_COMMIT` (0x5346),
`FOW_MODE == LOCK_SKIP` (0x5347), lobby `Dodge == ARMY_RELOCK` (0x5348),
`AddAi == WORLD_PUBLISH` (0x5349), `Reconnect == ECO_OPEN` (0x534A). UiWndProc
order (SCAR → AI session → engine → lobby → relay) meant a lobby dodge posted
an army relock and the FOW native fired an AI commit. Remapped: engine
0x5350/51, lobby 0x5360–63, relay 0x5370; SCAR keeps 0x5343–0x534C.
Pin: `WindowMessageIdTests` in `test_overlay_present.py` (uniqueness +
ranges).

**VEH silent tail.** The crash handler allocated before anything reached
disk (`SessionRejoinOnCrash` → std::wstring/fopen_s, `OpenLogAppend` → path
building) — on a corrupted heap that is exactly the no-`[CRASH]` signature.
Now: log path cached at `LogInit`, crash write via `OpenCrashLogAppend`
(CreateFileW/WriteFile only), rejoin snapshot moved after the disk write
under its own `__try/__except`, and `g_vehDumping` clears in `__finally`
(a nested fault used to latch it and mute every later crash).

**Present stalls.** `SendMapHackOverlay` off the window thread now posts
(`PostMapHackOverlay`) instead of an unbounded `SendMessageW` — the FOW
hotkey path from Present ignores the result and the apply is idempotent.
D3D12 recover/flush now run under `D12PresentFilter` with stage labels
(`recover`/`flush`) — an AV there used to log a bare code via the outer
hooks.cpp wrapper.

**Game-over guard could crash or starve the relock** (the guard added in
2225572094). `Player_*` natives were called bare: a Lua error aborts the
relock chunk and reads as a refusal, `p==0` is the rcx=0 AV class, and a
0-for-no answer would have read as game-over (0 is truthy in Lua) and parked
the army. Now: every native pcall'd, zero/nil handle rejected before any
Player_*, answers compared to true/1 explicitly, pcall errors degrade
permissively (a guard that can stop the relock indefinitely already cost the
army once — 8d765c5baf). Six lupa tests in `GameOverGuardTests`.

**Villager EventRule spawn locked after Enable.** `lockSq` had no think
gate — same 4A70 class as the army EventRule (03:06:44). Gated on
`__ArmyLock_ThinkOn` / `AI_IsEnabled`, plus `player==0` reject. Four lupa
tests in `VillagerLockTests`.

**Sel / group / garrison locks required only "not WouldStrip" after
Enable.** A skip-map miss is not 4CE0 (03:50:55). All three now require
`__LockSafeStrip(sid)` when think is on; a fresh/busy pick retries on a
later tick instead of taking 4A70.

**Relock dedup blacked out the relock for 8 s.** The byte-identical scan
skip returned without clearing `g_armyRelockPosted`; the next post was
refused until the 8 s watchdog. Flag now clears on the dedup path.

**`g_spawnSeen` was the one unguarded two-thread container** (window-thread
`ClearSpawnWatch` vs collect-side `SpawnWatch` insert — the 03:00:52
bucket-smash shape). All sites under `RelockMapsGuard` now.

**`LockOneSid` had no alive check** (RPM `L.safe` can hold a squad that died
since the last collect). `Squad_IsAlive` gate added, mirroring `lockOne`.

**`kArmyOff` cleared `__ArmyLock_ThinkOn` and `kArmyOn` never restored it.**
Re-enabling the army lock with a live eco session left lockOne reading
ThinkOn=false + a lying AI_IsEnabled=false → LockSquad on tracked combat
(12:28 class). `kArmyOn` now sets ThinkOn when AI_IsEnabled is true.

**09:34 `eco_ai_cuts` AV (rva=0x1ED50B9, rcx=0) is the farm-ring sibling.**
The len=4608 chunk is apply (~1500 B) + farm ring (~3000 B) in one DoString,
labeled `eco_ai_cuts` whenever `haveAct`. `__EcoAct_Apply`'s zero-handle
guard is intact — but the farm body kept the old `if not player` guard, and
zero is truthy in Lua. Same RVA was already seen under `eco_farm_ring` at
21:45:51; that fix covered only the retain-list fallout. Fixed: farm head
rejects `player/tmpl/ebp/sg == 0` (and `SGroup_CreateIfNotFound` is pcall'd),
`Vill()` rejects 0 entity/squad, `pos`/`face` reject 0. `eco_contest` got
the same treatment (`E()`/`S()` returned 0 into `Entity_GetSquad`; player
guard; sg/eg pcall + 0-reject). `__EcoAct_WaterIgnored` (both copies) now
refuses `aiPlayer == 0` before the cache. Tests: `FarmRingZeroHandleTests`
runs the real emitted script under lupa (happy path + three zero-handle
cuts); textual pins for contest/water.

**Radar.** Region-scan kick reads `RadarSimWorldLivePublished()` like the
in-walk fold (a worker/TLS false can no longer start an in-match walk);
`RadarSimTickLooksLive` cache statics are atomic like ProbeSimWorldLive.

## Deferred (real, but not safe to rush)

- **`kRelockTryCap=1` + sorted `L.safe` starves combat** (relock finding 5):
  low-id villagers recycle to the front after the 30 s NotArmy hold and one
  pick/pass never reaches higher-id combat. Needs a PickRelockSid rework
  (skip workers/scouts by radar class), not a one-liner.
- **Marks scan has no match-end stop** and the probe's store-false-mid-
  refresh can abort it on a live match (00:42:09 false negative). Wants
  hysteresis + `StopMarksScanWorker` from `ScarNotifyMatchEnded`, plus the
  Lua game-over answer published to a C++ atomic.
- **World cache split observations**: `RadarPeekWorldCache` /
  `RadarCachedEntities` / `RadarCachedEntityName` each re-capture; a
  cross-thread pair can mix slots. Wants a single-snapshot struct.
- **Collect prev-reuse**: `FillRowOwner` copies owner/relation on an exact
  id hit without re-reading; a recycled id during teardown can publish a
  stale `relation==Self`.
- **Init timer** dies with its hwnd and is never retargeted; migrate
  destroys the fallback before the new SetTimer succeeds.
- **`eco_contest` is not in the SEH retain list**; a contest AV after the
  actuator parks can declare the VM dead and replay enable against a live
  match. Design decision needed (retain vs skip-after-park).
- **76 bare `__except(EXCEPTION_EXECUTE_HANDLER)`** sites swallow without
  logging. Own pass; ui_d3d12.cpp is the shape to copy.
- **rva=0x36A7E7F write-to-null at exit stays open.** Relic-native;
  discriminator is the second `[CRASH]` line's `scar_label`/`in_call`, never
  `last_native`.

## Test-coverage map

Full crash-class → test table came out of the audit. Strongest behavioral
pins already present: zero-handle Apply/Restore, scout-plan LockOneSid,
think-on Scan, Relic's first three monks, lockPbg fail-closed. Weakest
spots the audit flagged that this pass addressed: WM_APP uniqueness (was
none), game-over guard (was none), villager spawn gate (was none), dedup
flag (was none), farm ring (was emit-shape only). Still untested:
match-exit 0x36A7E7F gate, relock map race under concurrency, Present
SendMessage budget contract, `kRelicKickEnabled=false` kill switch,
ScarLuaReloadReady match-2 matrix.

# 2026-09-14 — сверка с remote `fea27989`

Local `main` was **behind 1**. User: сверка с ремоут коммитом.

[`fea279895c`](https://github.com/evers1nce1/AOE4HOOK/commit/fea279895c)
`fix(overlay): STK spawn lock and AI toggle` (skvaerok1, 02:33 +0300).

## Remote (already on `origin/main`)

| Дыра | Что сделали |
|---|---|
| Disable `AI_UnlockAll` / UnlockSquad army | `kHandover` + `kArmyOff` keep combat `+0x40`. Eco/buildings unlock only. Macedonia re-Enable handed army to Relic. |
| C++ `LockOneSid` after Enable | Relock **scan-only**. Spawn lock = Relic `GE_EntitySpawn` + `AI_LockSquad` on `event.entity` (STK `Hybrid_OnSpawn` / `ai_lock_army.lua`). No `Local.AddPlayerEvent`. 01:24 burst 50166–50178. |

Stamp they shipped: `stkOnSpawn+keepLock`.

## Local (this session, uncommitted before pull)

| Дыра | Что сделали |
|---|---|
| `AI_Enable(true)` with leftover WouldStrip | `StkAiTrackThinkEnableSafe`; `eco_ai_on_nothink`; retry 2 s. pid 38348 02:06:52 `would4A70-live=87 locked=0` → `rva=0x2A45959`. |
| Empty unlocked tracking still 4A70 | `StkAiTrackStampLockFlags` heap `+0x40` (not `.text`). `OffsetsWriteBytes` refuses RX / Relic `.text`. |

## Compose (kept both)

Remote keepLock **cuts the UnlockAll source** of the 87-row leftover.
Enable-true gate + heap stamp stay fail-closed for live-stack / empty
unlocked rows that keepLock does not cover.

Post-Enable combat lock is Relic EventRule only (remote). C++ does not
`LockOneSid`. Sel-lock still waits `g_thinkLive`.

Stamp: `stkOnSpawn+keepLock+noEn4A70+heapLock`.

`ai_session.cpp` / `stk_ai_track.h` / `test_ai_handover.py` auto-merged.
Conflicts resolved in `dllmain.cpp`, `AI_SESSION_HANDOFF.md`,
`AI_UNIT_CONTROL.md`, `findings/README.md`.

Host: `test_stk_think_enable`, `test_offsets_write`, `test_ai_handover`.
Not committed. `reversed/*.c` left dirty.

Inject `internal\x64\Release\DllInjector.exe` + neighbor DLL only.

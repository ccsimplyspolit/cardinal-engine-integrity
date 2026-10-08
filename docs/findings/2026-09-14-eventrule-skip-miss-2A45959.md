# 2026-09-14 — EventRule skip-map miss `rva=0x2A45959`

Zhu Xi / 宋 feudal ~11:19, «Войска атакованы!», then think crash.

## Observation

`C:\Users\Lanzerxyz\Documents\AOE4HSettings\Logs\aoe4_internal.log`

- Overlay boot `00:33:00` stamp **`+stkSpawn` only** (Release DLL file-locked;
  not the `+stkEco` fowctrl rebuild). DualFlag stayed `0x0001`.
- Second match of the overlay session. Crash `01:09:13.413`.
- `[CRASH] code=0xC0000005 rva=0x2A45959 av_addr=0x58 rax=0 in_call=0
  scar_tid=0 tid=14548` (think, not SCAR 14564).
- `last_native=army relock scan` (C++ HelperRun crumb). Relic EventRule
  does not update it.
- Zero `[STK] army relock lock sid=` in the whole log. Relock `attempt=0`.
- Immediately before AV:
  - `01:09:11.278` cache-spawn skip n=1
  - `01:09:11.629` cache-spawn skip n=7 `id0=1000008268`
  - `01:09:11.756` `ai_lock_skip_map` grew 2997→3298 bytes
  - `01:09:12.872` `ai_sel_pick`
  - `01:09:13.413` crash (~1.8 s after the 7-spawn)

## Finding

`lockOne` after Enable still `AI_LockSquad`'d Relic `GE_EntitySpawn`
(`__ArmyLock_SpawnEvent`) when Lua `__LockWouldStrip` was false. The
published skip-map is not live RPM. A skip-map miss is not 4CE0
(same class as 03:50:55). Think inserts tracking first → EventRule
LockSquad → inner `0x296D2E0` **4A70** → think `[rax+0x58]`.

Sel-pick 0.5 s before the AV is weaker: vill-only, `__LockSafeStrip`
after Enable. Relock scan itself did not LockSquad (stable hash
`0xD13F74F7`, no lock crumbs).

## Overlay change

After Enable, `lockOne` fail-closes even for SpawnEvent: pending only.
C++ `PickRelockSid` + `LockOneSid` (`Allow4CE0`, live `Safe4CE0`) is
the only post-Enable lock. Standing scan (AI off) still LockSquads.

Stamp `…+stkSpawn+stkEco+noEvt4A70`. Hold stays 2500 ms.

## Negative (do not reopen)

Think-off steal, `__ArmyLock_Tick`, `AI_LockSquads` / SweepLocks after
Enable, `Cmd_Stop` after Enable, empty-stack SafeStrip, EventRule
LockSquad on skip-map miss, WindowClear leftover, Enqueue neutralize,
Watcher / sibling / 7AB0 / FlushArm / EventSchedule / C8E4 / 77E8.

Inject `internal\x64\Release\DllInjector.exe` + neighbor
`InternalInjector.dll` only. Do not mix fowctrl into a process that
still has Release loaded.

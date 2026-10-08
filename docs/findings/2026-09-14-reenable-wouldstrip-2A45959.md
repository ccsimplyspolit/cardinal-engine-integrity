# 2026-09-14 — re-enable `AI_Enable(true)` with WouldStrip → `rva=0x2A45959`

Overlay session on Relic **PID 38348** (same process as the 01:45 RPM dump,
base `0x7FF773860000`). User toggled AI off/on (handover spam). Crash
**02:06:52.269**.

## Observation

`C:\Users\sshunko\Documents\AOE4HSettings\Logs\aoe4_internal.log`

```
02:06:11.889  [AI] session off handover=1
02:06:49.956  [AI] session wanted
02:06:52.097  ai_lock_army.lua standing lock
02:06:52.098  standing+slot combat=14 locked=0 would4A70-live=87
02:06:52.098  session re-enable: slot+army lock (before AI_Enable)
02:06:52.135  eco_ai_on / session on reenable=1
02:06:52.198  eco_ai_score hash=0xD13F74F7
02:06:52.198  army relock pass n=1 attempt=0
02:06:52.269  [CRASH] VEH 0xC0000005 rva=0x2A45959 av_type=0 av_addr=0x58 rax=0
              tid=3836 (think, not window 35868)
              scar=ai_sel_lock.lua scar_len=17445 in_call=1
              last_native=army relock scan
```

`cmd#1159 ai_sel_lock.lua` logged **ok at 02:06:52.292** — sel-lock DoString
was in flight. Think AV, not the window thread. Relock `attempt=0` (no
`LockOneSid`). Standing lock fail-closed the 87 WouldStrip rows (`locked=0`)
then `eco_ai_on` still called `AI_Enable(true)`.

Dump PE `…014529\00007ff773860000.RelicCardinal.exe.bin` at RVA `0x2A45959`:
`8B 48 58` = `mov ecx,[rax+0x58]`. Matches VEH `av_addr=0x58 rax=0`.
Function prelude `40 53 48 83 EC 20` at `0x2A45930`. Getter site `0x2924350`
is live in the same image.

ScarToolKIT `ai_risky.lua` / `ai_lock_army.lua` Enable-then-`pcall(AI_LockSquad)`
is the same class; overlay already inverted that order, but Enable-true on
leftover tracking was the remaining hole.

## Finding

`AI_Enable(false)` does **not** drop unlocked tracking rows. Re-enable
standing lock only 4CE0s Safe4CE0. `AI_Enable(true)` then starts think
`sub_2A45930`; getter `0x2924350` returns 0 → `[rax+0x58]`. Sel-lock install
(`AiCustomPushLive` on session `true`) is concurrent aggravation, not the
leaf.

Same RVA family as Zhu Xi relock / empty-stack SafeStrip / EventRule skip-map
miss, but **no overlay LockSquad** this time.

## Overlay change

- Stamp `+0x40` on empty leftover rows (`StkAiTrackStampLockFlags`, heap, not `.text`) then census **empty unlocked only**. Live WouldStrip (eco gather) does not defer Enable (see [enable-gate-empty-only](2026-09-14-enable-gate-empty-only.md)).
- After standing lock, if unsafe: `eco_ai_on_nothink` (`AI_Enable(false)`,
  `__ArmyLock_ThinkOn=false`, overlay `AOE4HOOK_ECO_CPP`). `g_thinkLive=false`.
  Return false so the caller does not `AiCustomPushLive` / sel-lock this tick.
- Retry Enable every 2 s (`TryLateRelicThink`). `AiSessionApplyDifficulty`
  does not Enable-true while think is deferred. `StkSelLockTick` waits for
  `g_thinkLive`.
- Stamp `+noEn4A70`. Compose with origin `fea27989` (keepLock + no
  C++ `LockOneSid`): UnlockAll was the leftover source for this 87-row
  census; the Enable-true gate stays as fail-closed for live-stack.

Host: `test_stk_think_enable.cpp`. Lua/source: `test_ai_handover.py`
(`test_think_enable_safe_refuses_would_strip`,
`test_enable_no_think_does_not_call_enable_true`).

## Negative (do not reopen)

Think-off steal / `AI_LockSquad` on WouldStrip, `__ArmyLock_Tick`,
`AI_LockSquads` / SweepLocks, `Cmd_Stop` after Enable, empty-stack `L.safe`,
EventRule LockSquad on skip-map miss, Relic `.text` plant, Watcher / Enqueue.

Inject `internal\x64\Release\DllInjector.exe` + neighbor
`InternalInjector.dll` only.

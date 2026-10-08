# 2026-09-14 — Enable gate: empty unlocked, not WouldStrip

## STK (canon)

`latest_extracted/ScarToolKIT/Lua_Scripts`:

| Script | Sequence |
|---|---|
| `ai_risky.lua` | `Game_AIControlLocalPlayer` → `AI_Enable(true)` → EventRule LockSquad combat |
| `ai_base_enable.lua` | Control → `AI_Enable(true)` → scoring hooks |
| `ai_lock_army.lua` | EventRule `event.entity` + `AI_LockSquad` combat only. No RPM. |
| `ai_disable.lua` | Remove listeners, `AI_Enable(false)`. **No** `AI_UnlockAll`. |

STK does not census tracking. Re-enable after eco is live still Enable-true.

## Overlay log (old DLL, pid session 01:44–02:06)

`Documents\AOE4HSettings\Logs\aoe4_internal.log`:

```
01:44:29  standing+slot combat=0 locked=0 would4A70-live=0  → eco_ai_on
01:44:44  spawn-watch combat=0 locked=0 would4A70-live=11
01:49:56  would4A70-live=26   (still combat=0)
01:51:27  re-enable would4A70-live=29 then eco_ai_on
02:06:52  re-enable would4A70-live=87 locked=0 → VEH rva=0x2A45959
```

`would4A70-live` grows while **combat=0**: Relic tracks villagers. Skip-map
WouldStrip is correct for `AI_LockSquad`. It is **wrong** as an Enable-true
gate: after any mid-match eco, `WouldStrip>0` forever → `eco_ai_on_nothink`
parks Relic train.

`TacticStackLive` is `tracking != 0` (fail-closed for LockSquad). That count
must not decide `AI_Enable`.

## Fix

1. Stamp empty unlocked `+0x40` (heap). Live gather stays unlocked.
2. `StkAiTrackEmptyUnlockedCount` = unlocked + empty **or** unreadable vec.
3. `ThinkEnableSafe` takes that count. Live WouldStrip is Enable-safe (STK).
4. Skip-map / `WouldStripCount` unchanged (never 4A70 a tracked sid).

Stamp `+emptyEn`. Host: `test_stk_think_enable`, `test_ai_handover`
`test_think_enable_safe_uses_empty_unlocked_not_would_strip`.

Follow-up: opening `AI_UnlockSquad` undid the stamp —
[open-unlock-vs-stamp](2026-09-14-open-unlock-vs-stamp.md).

# 2026-09-14 — `kEcoOpen` UnlockSquad vs empty stamp

## STK

`latest_extracted/ScarToolKIT/Lua_Scripts`:

| Script | Unlock / gather |
|---|---|
| `ai_risky.lua` / `ai_base_enable.lua` | Enable-true. No villager lock. No `AI_UnlockSquad`. |
| `ai_lock_army.lua` | Combat EventRule only. Eco stays unlocked for Relic. |
| `ai_lock_villager.lua` | Optional vill lock. Overlay army path does not use this. |
| `ai_disable.lua` | Enable-false. No `UnlockAll`. |

STK never stamps tracking and never unlocks idle vills to “let gather work”.
Gather is Relic `UpdateGathering` on **unlocked** eco.

## Overlay hole after `+emptyEn`

Heap stamp `tracking+0x40` on **empty** unlocked rows so Relic think
(`0x2923300`) skips them. Native `AI_LockSquad` on that row is still 4A70
(getter `0x2924350` → 0 → `rva=0x2A45959` `[rax+0x58]`).

`kEcoOpen` then did `AI_UnlockSquad` on every non-constructing villager
before `LocalCommand_SquadSquad` / `SquadEntity`. First enable of a match
stamps → Enable-true → posts opening kick → unlock clears `+0x40` → empty
unlocked → same think AV class as pid 38348 02:06:52.

Contest `__EcoCppLock` expiry called `AI_UnlockSquad` too. The table is no
longer written (contest never `LockSquad`); leftover rows were still a
live unlock.

Stamp only at Enable leaves a gap: vill finishes gather / spawn race
inserts an empty unlocked row while think is already on.

## Fix (`+noOpenUnl+tickStamp`)

1. `kEcoOpen` issues LocalCommand only. Local player orders work on a
   stamped (think-skipped) vill. No `AI_UnlockSquad`.
2. Contest / lock-maintenance expiry only drops `__EcoCppLock[k]`.
3. `StkAiTrackStampLockFlags` every live `AiSessionService` tick after the
   pending open/score steps. Log only when `stamped > 0`.
4. Status / think-enable log: empty-unlocked, not “tasked combat” /
   `would4A70=0`.

Host: `test_ai_handover` (`test_eco_open_does_not_unlock_after_stamp`,
`test_contest_expiry_does_not_unlock_squad`,
`test_empty_stamp_keeps_running_after_enable`), `test_eco_idle`,
`test_overlay_present` dllmain stamp.

See also [enable-gate-empty-only](2026-09-14-enable-gate-empty-only.md).

## Live (pid 42536, old DLL `+emptyEn` only)

`Documents\AOE4HSettings\Logs\aoe4_internal.log` same boot:

```
02:46:02  OverlayBoot …+emptyEn
02:46:46  Relic think enabled would4A70=0
02:46:46  opening gather kick (sheep SquadSquad + idle unlock)   ← 232 ms later
02:47:48  stamp lock flags n=8 live-stack=25 already=0 + Enable
02:49:48  stamp lock flags n=7 live-stack=27 already=4 + Enable
```

Opening unlock ran **after** Enable-true on this process. Think had not
AVed by 02:51 (contest + sel_pick still posting). The hole is confirmed
in the log; the new DLL is `+noOpenUnl+tickStamp` (LNK1104 — this Relic
still holds `Release\InternalInjector.dll`).

# 2026-09-14 — Disable must not UnlockAll army

## Observation

After overlay Disable, the player can command army (think off).
Re-Enable handed the army back to Relic (sshunko Macedonia).

## Cause

`kArmyOff` + `kHandover` called `AI_UnlockAll` / `AI_UnlockSquad` on
`__ArmyLock_LockedSquads` and cleared the table. Standing scan on the
next Enable then saw leftover tracking as WouldStrip and skipped.
Think took the unlocked combat.

## Fix

Keep combat `+0x40` across Disable. Unlock villagers / buildings only.
EventRule is removed and re-armed on Enable. Stamp `stkOnSpawn+keepLock`.

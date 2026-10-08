# 2026-09-14 — STK OnSpawn, no C++ LockOneSid

## Observation (01:24 inject)

Boot stamp had **no** `luaGate` / `stkOnSpawn` (`Memory +11 (PAGE_GUARD…)` only).
That is not the 01:19 Release image.

Live log `combat=2 locked=0` then C++ `pcall(__ArmyLock_LockOneSid,50166…50178)`
— overlay relock, not ScarToolKIT.

## STK (canon)

`scar/ScarToolKIT-main/lua_scripts/ai_lock_army.lua` and
`hybrid_c.scar` `Hybrid_OnSpawn`:

- `Rule_AddPlayerEvent(GE_EntitySpawn)` + `AI_LockSquad` on `event.entity`
- **No** `Local.AddPlayerEvent` (overlay world-feed / `event.id`, late vs think)
- **No** C++ `LockOneSid` after Enable
- **No** `Hybrid_SweepLocks` / `AI_LockSquads`

## Overlay

Standing scan while AI off. After Enable: Relic EventRule only, WouldStrip
still refuses a sid think already tracks. Cache-spawn skip while session live.
Relock is scan-only.

Stamp `stkOnSpawn luaGate2500+hold5+wasStrip+wfAfterDf+no4A70+stkEco`.
Hold 2500 unchanged.

Inject `internal\x64\Release\DllInjector.exe` + neighbor DLL only.
Boot line must contain `stkOnSpawn`.

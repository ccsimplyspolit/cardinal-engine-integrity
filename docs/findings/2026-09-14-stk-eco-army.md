# 2026-09-14 — STK Relic eco under overlay army lock

Product: Relic runs eco, the player owns the army. ScarToolKIT Lua we
adapted (not SweepLocks / `AI_LockSquads` / `GetDesiredTCCount=0`):

| STK | Overlay |
|---|---|
| `ai_risky.lua` ignoredTypes `scar_shinobi` | Shinobi is Relic's Koka scout analog (`isScoutLike` / `StkNameIsScout`). Same 4A70 class as starting scout if locked after think tracks it. |
| `ai_risky` / `ai_base_enable` villager score 4000, economy 2–3 | Army-lock Layer B floors `iEcon` at 1.0 so mass after ecoLock does not starve villagers (`iEcon` 0.42). Combat seats stay 0. Extra TCs stay overlay (`GetDesiredTCCount` not 0). |
| `combat=` log vs `locked=` | Census / cache-spawn use `StkNameIsLockableArmy` (official, scout, Relic monks, shinobi out). Live Zhu Xi `combat=19 locked=16` was official+scout+eco in `!worker`, not three unlocked spears. |

Do not port: `Hybrid_SweepLocks`, villager lock after Enable (Relic must keep new vills), STK `MilitaryScore2000` (Relic training the army).

Stamp `…+stkSpawn+stkEco`. Hold stays 2500 ms.

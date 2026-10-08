# Economic production scoring audit — 2026-09-26

Scope: all **145** hooks in the current source copy
`sdk/scar/sga/cardinal/Data/ai/cardinal_scoring_functions.scar`, including the
singular `ScoringFunction_Mills`. The catalog also contains 145 unique names;
older documentation saying 143 is stale. The table records every hook exactly
once, its source line and direct scorer/helper dependencies. Source review is
not a measurement of game throughput. Economy-bag group availability can still
override a positive hook and requires separate validation.

## Confirmed bottlenecks and changes

1. **Workers stopped below the requested cap.** The old overlay only appended
   `UnderCountLimit(vc)` to Relic's worker list. The original percentage cap,
   difficulty production delay, island fishing reserve and 40-minute reduction
   could already multiply that list by zero. The replacement uses `__EcoAct.vc`
   (8–200, same UI/runtime bounds), counts queued workers and retains native
   resource acquisition, population proportion and multiple-queued preference.
   Mongol population reserve and the Templar shared TC queue age-up guard remain.
   Actual game population capacity and unit availability are engine constraints.
2. **Some economic upgrades still became impossible.** Fresh Foodstuffs and
   Sultanate economic research bypassed the generic gathering replacement and
   kept the Easy/Castle and Normal/Imperial difficulty zeros. Their new lists
   match the existing economy/upgrade intent, native 300-second TTA and
   one-at-a-time research. Ottoman imperial economic upgrades retain their
   faction check and engine point requirements but remove the Easy-only zero.
3. **Officials were embargoed until 6:00.** Removing that timer allows the
   existing preference for the first two officials to operate earlier.
   Vehicle cap, population ratio, costs and native production validation remain.
4. **Land-only policy conflicted with map preferences.** On water maps, land
   trade and early mill branches were disabled despite all boats being banned.
   Mills now use their land branches on every map, and farms retain land need
   instead of the naval 18-farm branch. Land traders still require a real route,
   gold scarcity, existing timing and their count/population limits. Farm age
   minimums no longer depend on difficulty; their age, time and count conditions
   remain, together with placement, affordability and one foundation at a time.

Nine hooks are replaced in `ai_economy_scoring.h`. No global score multiplier,
new production director, free resource/technology grant, protected-code change
or extra recurring timer is introduced. Existing gather/wheelbarrow fixes,
land-only ban, user workers-only mode, army/TC caps, military demand and
counter scoring remain authoritative. An absent required factory produces an
explicit zero scorer where available. If even the Lua scorer factory is absent,
the fallback is an empty list (verified Relic MultiplyList zero at RVA 0x2D03940).
It does not silently omit a required safety gate. Scoring callbacks remain O(1);
all map/world scans stay outside them.

**Carcass transport is a separate issue:** `CollectiveHunting` is not
Professional Scouts. The common forester upgrade's economy group uses
`ScoringFunctions_NoScoring`, `max_current=0` and an unreachable production
threshold; increasing an economic multiplier cannot repair this. See
[scout carcass findings](2026-09-26-scout-carcass-delivery.md). Both hooks remain
unchanged here. Mine occupancy is a gathering-target decision, also separate
from this production scoring layer.

## Installation and reloading

Append `kAiEconomyScoringScript` after the existing scoring/affordability wrappers
in both the initial session script and the versioned runtime installer, and
before `kAiLandOnlyScript`. Call `__EcoAct_InstallEconomyScoring` after
`__EcoAct_InstallGathering`/`__EcoAct_InstallMilBld` in
`__EcoAct_LayerBInvalidate` and `__EcoAct_Apply`, before the same-generation early
return. Repeated install defines the same bodies; it never captures its own
wrapper or constructs a native scorer outside production context.

The shared replacements include their own affordability/foundation guards where
these were previously supplied by wrappers. A later call that reinstalls old
scoring bodies must be followed by the shared installer. `__EcoAct.wo=1` blocks
all eight non-worker replacements; worker production continues normally.
`__EcoAct.economyScoring=1` records that the shared policy was installed.

## Verification

`tests/adversarial/test_ai_economy_scoring.py` executes the actual Relic source
and shipped embedded Lua with controlled native gate results. It reproduces
stock zeros, verifies the corrected branch, checks queued worker cap, Templar
age-up blocking, route/vehicle/cost/placement/foundation guards, workers-only
mode, unavailable factories, repeated reload and exact 145-hook inventory.
These tests do not reproduce native utility magnitudes or prove improved
resources per minute in a running match. Recommended live evidence is sustained
TC production until the configured worker cap, officials before 6:00, early
land mills on a water map, and zero dock/boat production.

## Complete hook inventory

`KEEP` means the relevant restriction expresses availability, placement,
demand, composition, explicit caps or deliberate non-economic behavior. It is
not evidence that a larger number is beneficial. `BLOCK` is the explicit
land-only policy. Direct dependencies below are extracted from the original
body; nested behavior flows through the listed helper hooks.

| Hook | Source line | Disposition | Original direct dependencies |
| --- | ---: | --- | --- |
| `ScoringFunctions_CombatCommon` | 97 | KEEP specialized production/research/selection chain; no demonstrated economic zero to remove. | `MinimumGameTime`, `LuaScoringFunction`, `CounterScore`, `MultiplyListScoringFunction`, `MultipleProduced`, `TimeToAcquire`, `MaxScoringFunction`, `RemainingPersonnelPopCap` |
| `ScoringFunctions_CombatCommonNaval` | 122 | BLOCK: unconditional land-only policy; no naval production/research. | `MinimumGameTime`, `LuaScoringFunction`, `CounterScore`, `MultiplyListScoringFunction`, `MultipleProduced`, `TimeToAcquire`, `MaxScoringFunction`, `RemainingPersonnelPopCap` |
| `ScoringFunctions_Infantry` | 147 | KEEP specialized production/research/selection chain; no demonstrated economic zero to remove. | `ScoringFunctions_CombatCommon`, `StrategicIntention` |
| `ScoringFunctions_Khan` | 155 | KEEP one-Khan count/cost; remains a scout in economic mode. | `MinimumGameTime` |
| `ScoringFunctions_Elephant` | 164 | KEEP specialized production/research/selection chain; no demonstrated economic zero to remove. | `ScoringFunctions_Infantry`, `UnderCountLimit` |
| `ScoringFunctions_RangedInfantry` | 172 | KEEP specialized production/research/selection chain; no demonstrated economic zero to remove. | `ScoringFunctions_CombatCommon`, `StrategicIntention` |
| `ScoringFunctions_PlayerUpgradeCommon` | 180 | KEEP specialized production/research/selection chain; no demonstrated economic zero to remove. | `OnlyProduceOneAtATime`, `StrategicIntention`, `TimeToAcquire` |
| `ScoringFunctions_PlayerEconGatheringUpgrade` | 207 | KEEP existing correction: remove native gather-benefit zero, worker presence 0.2, native TTA and one research. | `ScoringFunctions_PlayerUpgradeCommon`, `LuaScoringFunction`, `PlayerGatheringUpgrade`, `PresenceOfMyTypes` |
| `ScoringFunctions_PlayerEconGatheringUpgradeSpecial` | 227 | KEEP existing correction: farm/ovoo presence 0.2; distinct from ordinary worker upgrades. | `ScoringFunctions_PlayerUpgradeCommon`, `LuaScoringFunction`, `PresenceOfMyTypes` |
| `ScoringFunctions_PlayerEconProductionUpgrade` | 244 | KEEP alias to corrected gathering upgrade; non-rate economic benefits remain enabled. | `ScoringFunctions_PlayerUpgradeCommon`, `LuaScoringFunction`, `PresenceOfMyTypes` |
| `ScoringFunctions_PlayerForceUpgrades` | 254 | KEEP faction/building purpose, native requirements and existing affordability guard. | `OnlyProduceOneAtATime`, `StrategicIntention`, `IncreaseOverTime` |
| `ScoringFunctions_SulGovernor` | 282 | KEEP faction/building purpose, native requirements and existing affordability guard. | `HasProductionQueue`, `OnlyProduceOneAtATime`, `LuaScoringFunction` |
| `ScoringFunctions_SulGovernorDeferred` | 292 | KEEP specialized production/research/selection chain; no demonstrated economic zero to remove. | No direct scoring factory call |
| `ScoringFunctions_SulPalaceGovernor` | 302 | KEEP faction/building purpose, native requirements and existing affordability guard. | `HasProductionQueue`, `LuaScoringFunction` |
| `ScoringFunctions_SulPalaceGovernorDeferred` | 311 | KEEP specialized production/research/selection chain; no demonstrated economic zero to remove. | No direct scoring factory call |
| `ScoringFunctions_PlayerSpecialCombatUpgrades` | 339 | KEEP military/native chain plus existing user army and economic-mode gates. | `OnlyProduceOneAtATime`, `StrategicIntention`, `TimeToAcquire` |
| `ScoringFunctions_PlayerEconNavalUpgrade` | 356 | BLOCK: unconditional land-only policy; no naval production/research. | `ScoringFunctions_PlayerUpgradeCommon`, `LuaScoringFunction`, `PresenceOfMyTypes` |
| `ScoringFunctions_PlayerEconWheelbarrowUpgrade` | 368 | KEEP existing economy+upgrade intent, one research and native TTA. | `OnlyProduceOneAtATime`, `StrategicIntention`, `TimeToAcquire` |
| `ScoringFunctions_PlayerUpgradeFreshFoodstuffs` | 383 | REPLACE: remove difficulty/age zero; economy+upgrade intention, one research and native TTA. | `OnlyProduceOneAtATime`, `StrategicIntention`, `TimeToAcquire`, `LuaScoringFunction` |
| `ScoringFunctions_PlayerUnitTierUpgrade` | 399 | KEEP specialized production/research/selection chain; no demonstrated economic zero to remove. | `ScoringFunctions_PlayerUpgradeCommon`, `TierUpgrade` |
| `ScoringFunctions_PlayerUnitCombatUpgrade` | 406 | KEEP specialized production/research/selection chain; no demonstrated economic zero to remove. | `ScoringFunctions_PlayerUpgradeCommon`, `LuaScoringFunction`, `MaxScoringFunction`, `ClampedScoringFunction`, `PresenceOfUpgradeableSquads`, `MilitaryPlayerUpgrade` |
| `ScoringFunctions_PlayerImperialCombatUpgrade` | 435 | KEEP military/native chain plus existing user army and economic-mode gates. | `LuaScoringFunction`, `OnlyProduceOneAtATime`, `StrategicIntention` |
| `ScoringFunctions_PlayerImperialEconUpgrade` | 459 | REPLACE: remove Easy zero; preserve Ottoman-only, one research and engine Vizier-point requirements. | `LuaScoringFunction`, `OnlyProduceOneAtATime`, `StrategicIntention` |
| `ScoringFunctions_PlayerCombatProductionUpgrade` | 480 | KEEP military/native chain plus existing user army and economic-mode gates. | `ScoringFunctions_PlayerUpgradeCommon`, `LuaScoringFunction`, `PresenceOfMyTypes` |
| `ScoringFunctions_PlayerNavalCombatProductionUpgrade` | 496 | BLOCK: unconditional land-only policy; no naval production/research. | `ScoringFunctions_PlayerUpgradeCommon`, `ShouldConsiderNaval`, `LuaScoringFunction`, `PresenceOfMyTypes` |
| `ScoringFunctions_NavalUnitCombatUpgrades_Sultanate` | 514 | BLOCK: unconditional land-only policy; no naval production/research. | `ScoringFunctions_NavalUnitCombatUpgrades` |
| `ScoringFunctions_PlayerEconUpgrade_Sultanate` | 519 | REPLACE: remove difficulty/age zero; economy+upgrade intention, one research and native TTA. | `ScoringFunctions_PlayerUpgradeCommon`, `LuaScoringFunction` |
| `ScoringFunctions_PlayerUnitCombatUpgrade_Sultanate` | 528 | KEEP specialized production/research/selection chain; no demonstrated economic zero to remove. | `ScoringFunctions_PlayerUpgradeCommon`, `LuaScoringFunction`, `MaxScoringFunction`, `ClampedScoringFunction`, `PresenceOfUpgradeableSquads`, `MilitaryPlayerUpgrade` |
| `ScoringFunctions_PlayerUnitCombatUpgradeAllDifficulties` | 555 | KEEP specialized production/research/selection chain; no demonstrated economic zero to remove. | `ScoringFunctions_PlayerUpgradeCommon`, `MaxScoringFunction`, `ClampedScoringFunction`, `PresenceOfUpgradeableSquads`, `MilitaryPlayerUpgrade` |
| `ScoringFunctions_PlayerUpgradeAllDifficulties` | 579 | KEEP military/native chain plus existing user army and economic-mode gates. | `ScoringFunctions_PlayerUpgradeCommon` |
| `ScoringFunctions_Trader` | 586 | REPLACE: remove naval map preference; keep real route, 35 cap, population ratio, gold scarcity, timing and costs. | `ShouldNotConsiderNaval`, `TradeRouteExistsScore`, `UnderCountLimit`, `PopulationPercentage`, `StrategicIntention`, `MinimumGameTime`, `LackOfSecuredResourceDeposits`, `RemainingPersonnelPopCap` |
| `ScoringFunctions_TraderUpgrade` | 610 | REPLACE: remove naval map preference; keep real route, trader presence and costs. | `ShouldNotConsiderNaval`, `TradeRouteExistsScore`, `StrategicIntention`, `PresenceOfMyTypes` |
| `ScoringFunctions_SiegeTower` | 651 | KEEP military/native chain plus existing user army and economic-mode gates. | `UnderCountLimit`, `PopulationPercentage`, `PresenceOfEnemyTypes`, `PresenceOfMyTypes`, `TimeToAcquire`, `PlannedPlacementScore`, `StrategicIntention` |
| `ScoringFunctions_RamTower` | 673 | KEEP military/native chain plus existing user army and economic-mode gates. | `UnderCountLimit`, `PresenceOfEnemyTypes`, `PresenceOfMyTypes`, `TimeToAcquire`, `StrategicIntention` |
| `ScoringFunctions_Siege` | 689 | KEEP military/native chain plus existing user army and economic-mode gates. | `UnderCountLimit`, `PresenceOfMyTypes`, `MultiplyListScoringFunction`, `MaxScoringFunction`, `PresenceOfEnemyTypes`, `StrategicIntention`, `LuaScoringFunction`, `PopulationPercentage`, `TimeToAcquire`, `MultipleProduced`, `RemainingPersonnelPopCap` |
| `ScoringFunctions_CombatSiege` | 742 | KEEP specialized production/research/selection chain; no demonstrated economic zero to remove. | `ScoringFunctions_CombatCommon`, `UnderCountLimit`, `PresenceOfMyTypes`, `MultiplyListScoringFunction`, `MaxScoringFunction`, `StrategicIntention`, `PopulationPercentage` |
| `ScoringFunctions_Dock` | 782 | BLOCK: unconditional land-only policy; no naval production/research. | `ShouldConsiderLimitedNaval`, `ShouldConsiderNaval`, `MaxScoringFunction`, `PlannedPlacementScore`, `UnderCountLimit`, `NotProducedRecently`, `LuaScoringFunction`, `ProductionQueueContention` |
| `ScoringFunctions_FishingBoat` | 815 | BLOCK: unconditional land-only policy; no naval production/research. | `ShouldConsiderLimitedNaval`, `MaxPopCapPercentage`, `ShouldConsiderNaval`, `ShouldConsiderDeepwaterFishDeposits`, `MultiplyListScoringFunction`, `MaxScoringFunction`, `PopulationPercentage`, `UnderCountLimit`, `TimeToAcquire`, `StrategicIntention`, `AlliedCombatFitnessVsStrongestEnemy`, `RemainingPersonnelPopCap` |
| `ScoringFunctions_TradeBoat` | 869 | BLOCK: unconditional land-only policy; no naval production/research. | `ShouldConsiderLimitedNaval`, `ShouldConsiderNaval`, `MinimumGameTime`, `MaxScoringFunction`, `TradeRouteExistsScore`, `UnderCountLimit`, `PopulationPercentage`, `StrategicIntention`, `LackOfSecuredResourceDeposits`, `RemainingPersonnelPopCap` |
| `ScoringFunctions_TransportBoat` | 894 | BLOCK: unconditional land-only policy; no naval production/research. | `MinimumGameTime`, `UnderCountLimit`, `LuaScoringFunction`, `MultiplyListScoringFunction`, `PopulationPercentage`, `MaxScoringFunction`, `PlayersAndCapturePointsOnDifferentIslands`, `PlayersOnDifferentIslands`, `ShouldConsiderLimitedNaval`, `ShouldConsiderNaval`, `NavalTransportRequired`, `TimeToAcquire`, `PresenceOfMyTypes`, `MaxPopCapPercentage`, `AlliedCombatFitnessVsStrongestEnemy`, `RemainingPersonnelPopCap` |
| `ScoringFunctions_NavalMilitary` | 947 | BLOCK: unconditional land-only policy; no naval production/research. | `ScoringFunctions_CombatCommonNaval`, `StrategicIntention`, `ShouldConsiderNaval`, `MaxPopCapPercentage` |
| `ScoringFunctions_WarShip` | 957 | BLOCK: unconditional land-only policy; no naval production/research. | `MinimumGameTime`, `LuaScoringFunction`, `CounterScore`, `MultiplyListScoringFunction`, `PresenceOfEnemyTypes`, `MaxScoringFunction`, `StrategicIntention`, `ShouldConsiderNaval`, `MultipleProduced`, `TimeToAcquire`, `MaxPopCapPercentage` |
| `ScoringFunctions_Fireship` | 992 | BLOCK: unconditional land-only policy; no naval production/research. | `ScoringFunctions_CombatCommonNaval`, `StrategicIntention`, `ShouldConsiderNaval`, `PresenceOfEnemyTypes` |
| `ScoringFunctions_Scouting` | 1003 | KEEP native scouting/count and user army gate; carcass work is a separate command/ability path. | `PopulationPercentage`, `MaxPopCapPercentage`, `TimeToAcquire`, `StrategicIntention`, `UnderCountLimit`, `AlliedCombatFitness`, `NoUpgradeProductionBlockedByThisProduction` |
| `ScoringFunctions_House` | 1036 | KEEP population need, house-busy/mode guard, one foundation and costs. | `PopCapGenerator` |
| `ScoringFunctions_Monk` | 1045 | KEEP religion/relic support and existing religious count/handover constraints. | `ClampedScoringFunction`, `StrategicIntention`, `PopulationPercentage`, `MaxPopCapPercentage`, `TimeToAcquire`, `UnderCountLimit`, `LuaScoringFunction`, `MultiplyListScoringFunction`, `MaxScoringFunction`, `MinimumGameTime` |
| `ScoringFunctions_HealingOnlyUnit` | 1121 | KEEP military/native chain plus existing user army and economic-mode gates. | `PopulationPercentage`, `MaxPopCapPercentage`, `TimeToAcquire`, `MinimumGameTime` |
| `ScoringFunctions_SultanateMonk` | 1131 | KEEP religion/relic support and existing religious count/handover constraints. | `ClampedScoringFunction`, `StrategicIntention`, `PopulationPercentage`, `MaxPopCapPercentage`, `TimeToAcquire`, `MinimumGameTime` |
| `ScoringFunctions_DefensiveStructuresCommon` | 1147 | KEEP military/native chain plus existing user army and economic-mode gates. | `ScoringFunctions_DefensiveStructuresCommonNaval`, `ScoringFunctions_DefensiveStructuresCommonLand` |
| `ScoringFunctions_DefensiveStructuresCommonLand` | 1160 | KEEP defense placement, threat and victory constraints. | `StrategicIntention`, `MultiplyListScoringFunction`, `MinimumTeamControlledSacredSites`, `TimeToAcquire`, `MaxScoringFunction`, `PlannedPlacementScore`, `AlliedCombatFitness`, `MinimumGameTime` |
| `ScoringFunctions_DefensiveStructuresCommonNaval` | 1179 | KEEP defense placement, threat and victory constraints. | `TimeToAcquire`, `PlannedPlacementScore`, `AlliedCombatFitness`, `MinimumGameTime` |
| `ScoringFunctions_TemplarFortress` | 1189 | KEEP defense placement, threat and victory constraints. | `ScoringFunctions_DefensiveStructuresCommon` |
| `ScoringFunctions_Keeps` | 1198 | KEEP defense placement, threat and victory constraints. | `ScoringFunctions_DefensiveStructuresCommon`, `UnderCountLimit` |
| `ScoringFunctions_WoodenFort` | 1216 | KEEP defense placement, threat and victory constraints. | `ScoringFunctions_DefensiveStructuresCommon`, `UnderCountLimit` |
| `ScoringFunctions_MongolOutposts` | 1238 | KEEP defense placement, threat and victory constraints. | `TimeToAcquire`, `PlannedPlacementScore`, `MinimumGameTime`, `PresenceOfMyTypes`, `AlliedCombatFitness`, `UnderCountLimit` |
| `ScoringFunctions_Outposts` | 1269 | KEEP defense placement, threat and victory constraints. | `ScoringFunctions_DefensiveStructuresCommon`, `UnderCountLimit` |
| `ScoringFunctions_Markets` | 1285 | KEEP first-market, cooldown, placement/timing, Sengoku special branch; no unconditional early spam. | `MinimumGameTime`, `UnderCountLimit`, `NotProducedRecently`, `PlannedPlacementScore`, `TimeToAcquire`, `StrategicIntention` |
| `ScoringFunctions_LandmarkCommon` | 1314 | KEEP faction age-up/landmark requirements, cost and exclusivity. | `TimeToAcquire`, `StrategicIntention` |
| `ScoringFunctions_LandmarkStandard` | 1327 | KEEP faction age-up/landmark requirements, cost and exclusivity. | `ScoringFunctions_LandmarkCommon` |
| `ScoringFunctions_LandmarkRandomA` | 1331 | KEEP faction age-up/landmark requirements, cost and exclusivity. | `ScoringFunctions_LandmarkCommon`, `MaxScoringFunction`, `RandomIntScore`, `LuaScoringFunction` |
| `ScoringFunctions_LandmarkRandomB` | 1347 | KEEP faction age-up/landmark requirements, cost and exclusivity. | `ScoringFunctions_LandmarkCommon`, `MaxScoringFunction`, `InverseRandomIntScore`, `LuaScoringFunction` |
| `ScoringFunctions_LandmarkOffensive` | 1363 | KEEP faction age-up/landmark requirements, cost and exclusivity. | `ScoringFunctions_LandmarkCommon`, `ClampedScoringFunction`, `RandomIntScore` |
| `ScoringFunctions_LandmarkDefensive` | 1371 | KEEP faction age-up/landmark requirements, cost and exclusivity. | `ScoringFunctions_LandmarkCommon` |
| `ScoringFunctions_LandmarkGreatWall` | 1375 | KEEP faction age-up/landmark requirements, cost and exclusivity. | `ScoringFunctions_LandmarkDefensive`, `PresenceOfMyTypes` |
| `ScoringFunctions_LandmarkEcon` | 1384 | KEEP faction age-up/landmark requirements, cost and exclusivity. | `ScoringFunctions_LandmarkCommon`, `ClampedScoringFunction`, `InverseRandomIntScore` |
| `ScoringFunctions_LandmarkEconTrader` | 1392 | KEEP faction age-up/landmark requirements, cost and exclusivity. | `ScoringFunctions_LandmarkCommon`, `TradeRouteExistsScore` |
| `ScoringFunctions_LandmarkSiege` | 1400 | KEEP faction age-up/landmark requirements, cost and exclusivity. | `ScoringFunctions_LandmarkCommon` |
| `ScoringFunctions_LandmarkMongolAge1Common` | 1404 | KEEP faction age-up/landmark requirements, cost and exclusivity. | `PlannedPlacementScore`, `StrategicIntention` |
| `ScoringFunctions_LandmarkMongolAge1Econ` | 1413 | KEEP faction age-up/landmark requirements, cost and exclusivity. | `ScoringFunctions_LandmarkMongolAge1Common` |
| `ScoringFunctions_LandmarkMongolAge1Offense` | 1417 | KEEP faction age-up/landmark requirements, cost and exclusivity. | `ScoringFunctions_LandmarkMongolAge1Common` |
| `ScoringFunctions_Wonder` | 1421 | KEEP victory-specific decision and affordability; not an economy multiplier. | `ClampedScoringFunction`, `TimeToAcquire`, `StrategicIntention`, `AlliedCombatFitnessVsStrongestEnemy` |
| `ScoringFunctions_DefensiveStructureUpgrades` | 1430 | KEEP defense placement, threat and victory constraints. | `StrategicIntention`, `LuaScoringFunction` |
| `ScoringFunctions_DefensiveUpgrade` | 1439 | KEEP military/native chain plus existing user army and economic-mode gates. | `StrategicIntention`, `TimeToAcquire` |
| `ScoringFunctions_LowerPriorityDefensiveUpgrade` | 1449 | KEEP defense placement, threat and victory constraints. | `ScoringFunctions_DefensiveUpgrade`, `InversePercentOfResourcesOwned` |
| `ScoringFunctions_WallTower` | 1458 | KEEP defense placement, threat and victory constraints. | `PlannedPlacementScore`, `StrategicIntention` |
| `ScoringFunction_Mills` | 1466 | REPLACE: land branches on every map; retain cooldown/need/placement, Japanese housing and English first mill; serialize foundations. | `MultiplyListScoringFunction`, `ShouldConsiderNaval`, `MinimumGameTime`, `NotProducedRecently`, `PlannedPlacementScore`, `ScarcityAndDeficiencyScore`, `StrategicIntention`, `ShouldNotConsiderNaval`, `MaximumGameTime`, `PresenceOfMyTypes`, `PlannedPlacementScoreValid`, `MaxScoringFunction`, `PopCapGenerator`, `UnderCountLimit`, `TimeToAcquire`, `LuaScoringFunction` |
| `ScoringFunctions_DropOffs` | 1583 | KEEP scarcity/failsafe/cooldown/placement plus existing lumber-busy and one-foundation guards; mine sharing is separate. | `MultiplyListScoringFunction`, `NotProducedRecently`, `AmountOfResourceNeeded`, `LowResourceIncome`, `IsProductionBlockedByThisResource`, `ScarcityAndDeficiencyScore`, `PlannedPlacementScoreValid`, `StrategicIntention`, `NoAvailableNearbyDepositsLeftOnColonizedIsland`, `MaxScoringFunction` |
| `ScoringFunctions_WorkerElephants` | 1654 | KEEP resource/dropoff need, population ratio and cooldown; distinct from Gatherer group. | `MultiplyListScoringFunction`, `MinimumGameTime`, `NotProducedRecently`, `AmountOfResourceNeeded`, `LowResourceIncome`, `IsProductionBlockedByThisResource`, `ScarcityAndDeficiencyScore`, `PopulationPercentage`, `StrategicIntention`, `MaxScoringFunction` |
| `ScoringFunctions_Yatai` | 1702 | KEEP per-PBG utility, count and cooldown for mobile dropoffs. | `MinimumGameTime`, `NotProducedRecently`, `LuaScoringFunction`, `UnderCountLimit` |
| `ScoringFunctions_ResourceGenerator` | 1731 | REPLACE: land need on every map and remove difficulty-only minimum handicaps; keep age/time/count, scarcity and placement. | `MultiplyListScoringFunction`, `ShouldNotConsiderNaval`, `TimeToAcquire`, `StrategicIntention`, `ScarcityAndDeficiencyScore`, `MinimumGameTime`, `IncreaseOverTime`, `ShouldConsiderNaval`, `UnderCountLimit`, `LuaScoringFunction`, `MaxScoringFunction`, `PlannedPlacementScoreIsMoreThan` |
| `ScoringFunctions_Ranch` | 1870 | KEEP cattle presence, age/count gates, placement, TTA and one foundation. | `LuaScoringFunction`, `UnderCountLimit`, `MultiplyListScoringFunction`, `TimeToAcquire`, `PlannedPlacementScore`, `StrategicIntention`, `MinimumGameTime`, `PresenceOfMyTypes`, `MaxScoringFunction` |
| `ScoringFunctions_ProductionBuilding` | 1903 | KEEP real queue contention, placement and cost; avoid unused production buildings. | `TimeToAcquire`, `PlannedPlacementScore`, `ProductionQueueContention` |
| `ScoringFunctions_HighValueResearchBuilding` | 1913 | KEEP time, placement and cost requirements. | `MinimumGameTime`, `TimeToAcquire`, `PlannedPlacementScore` |
| `ScoringFunctions_GoldenHordeLandmarks` | 1922 | KEEP faction age-up/landmark requirements, cost and exclusivity. | `ScoringFunctions_LandmarkCommon`, `TimeToAcquire`, `MinimumGameTime` |
| `ScoringFunctions_GoldenHordeLandmarksA` | 1929 | KEEP faction age-up/landmark requirements, cost and exclusivity. | `ScoringFunctions_GoldenHordeLandmarks`, `LuaScoringFunction` |
| `ScoringFunctions_GoldenHordeLandmarksB` | 1945 | KEEP faction age-up/landmark requirements, cost and exclusivity. | `ScoringFunctions_GoldenHordeLandmarks`, `LuaScoringFunction` |
| `ScoringFunctions_Monastery` | 1961 | KEEP religion/relic support and existing religious count/handover constraints. | `UnderCountLimit`, `PlannedPlacementScore`, `TimeToAcquire`, `NotProducedRecently`, `ProductionQueueContention`, `MultiplyListScoringFunction`, `MaxScoringFunction`, `PresenceOfMyTypes` |
| `ScoringFunctions_MosqueSultanate` | 1997 | KEEP religion/relic support and existing religious count/handover constraints. | `LuaScoringFunction` |
| `ScoringFunctions_MilitaryProductionBuilding` | 2004 | KEEP C++ demand, opening/eco lock, army capacity and affordability. | `PlannedPlacementScore`, `StrategicIntention`, `ProductionQueueContention`, `LuaScoringFunction`, `NotProducedRecently`, `RemainingPersonnelPopCap`, `UnderCountLimit` |
| `ScoringFunctions_MilitaryResearchBuilding` | 2039 | KEEP research/queue needs and costs; economic army lock does not disable it. | `TimeToAcquire`, `PlannedPlacementScore`, `UnderCountLimit`, `StrategicIntention`, `PresenceOfMyTypes`, `RemainingPersonnelPopCap` |
| `ScoringFunctions_Daimyo` | 2072 | KEEP military/native chain plus existing user army and economic-mode gates. | `PlannedPlacementScore`, `PresenceOfMyTypes`, `LuaScoringFunction`, `GroupNotProducedRecently`, `OneStructureFromGroupAtATime` |
| `ScoringFunctions_Gatherer` | 2132 | REPLACE: configured worker cap, queued units included; remove hidden percentage/difficulty/naval reductions; keep Templar shared queue protection. | `TimeToAcquire`, `MultipleProduced`, `MaxPopCapPercentage`, `PopulationPercentage`, `MultiplyListScoringFunction`, `LuaScoringFunction`, `NotProducedRecently`, `MaxScoringFunction`, `RemainingPersonnelPopCap`, `NoUpgradeProductionBlockedByThisProduction` |
| `ScoringFunctions_ExpansionTC` | 2268 | KEEP configured TC target, one foundation and costs; no unbounded TC spam. | `LuaScoringFunction`, `TimeToAcquire`, `UnderCountLimit`, `MultiplyListScoringFunction`, `ClampedScoringFunction`, `IslandNeedingExpansionBase`, `MaxScoringFunction`, `StrategicIntention`, `PlannedPlacementScore` |
| `ScoringFunctions_Pastures` | 2345 | KEEP actual scarcity, one foundation and costs. | `ScarcityAndDeficiencyScore` |
| `ScoringFunctions_NoScoring` | 2354 | KEEP empty/zero list; intentionally excluded groups include common Professional Scouts; never enable globally. | No direct scoring factory call |
| `ScoringFunctions_PlayerSiegeEngineerUpgrade` | 2360 | KEEP military/native chain plus existing user army and economic-mode gates. | `TimeToAcquire`, `StrategicIntention` |
| `ScoringFunctions_Official` | 2571 | REPLACE: remove six-minute embargo; keep initial two-official preference, vehicle cap and costs. | `UnderCountLimit`, `LuaScoringFunction`, `MultiplyListScoringFunction`, `PopulationPercentage`, `MaxScoringFunction`, `TimeToAcquire`, `StrategicIntention`, `VehicleUnderCountLimit`, `MinimumGameTime` |
| `ScoringFunctions_Cattle` | 2607 | KEEP existing early-cow correction and age limits; unrelated to deer transport. | `UnderCountLimit`, `LuaScoringFunction`, `PresenceOfMyTypes`, `MultiplyListScoringFunction`, `MinimumGameTime`, `MaxScoringFunction`, `TimeToAcquire`, `StrategicIntention` |
| `ScoringFunctions_MilitarySchool` | 2674 | KEEP military/native chain plus existing user army and economic-mode gates. | `TimeToAcquire`, `PlannedPlacementScore`, `StrategicIntention`, `UnderCountLimitFromStateModel` |
| `ScoringFunctions_WallAndGate` | 2685 | KEEP defense placement, threat and victory constraints. | `LuaScoringFunction` |
| `ScoringFunctions_Aqueduct` | 2690 | KEEP faction/building purpose, native requirements and existing affordability guard. | `LuaScoringFunction` |
| `ScoringFunctions_NavalUnitCombatUpgrades` | 2695 | BLOCK: unconditional land-only policy; no naval production/research. | `ScoringFunctions_PlayerUpgradeCommon`, `LuaScoringFunction`, `ShouldConsiderNaval`, `MaxScoringFunction`, `ClampedScoringFunction`, `PresenceOfUpgradeableSquads`, `MilitaryPlayerUpgrade` |
| `ScoringFunctions_FrenchLongGunsNavalUpgrade` | 2726 | BLOCK: unconditional land-only policy; no naval production/research. | `PresenceOfMyTypes`, `ShouldConsiderNaval` |
| `ScoringFunctions_OttomanMehter` | 2737 | KEEP military/native chain plus existing user army and economic-mode gates. | `UnderCountLimit`, `PresenceOfMyTypes`, `MultiplyListScoringFunction`, `MaxScoringFunction`, `StrategicIntention`, `TimeToAcquire`, `PopulationPercentage` |
| `ScoringFunctions_OttomanGreatBombard` | 2767 | KEEP military/native chain plus existing user army and economic-mode gates. | `UnderCountLimit`, `PresenceOfMyTypes`, `MultiplyListScoringFunction`, `MaxScoringFunction`, `PopulationPercentage`, `TimeToAcquire`, `MultipleProduced`, `StrategicIntention`, `RemainingPersonnelPopCap` |
| `ScoringFunctions_EnglishAbbeyKing` | 2805 | KEEP specialized production/research/selection chain; no demonstrated economic zero to remove. | `ScoringFunctions_CombatCommon`, `StrategicIntention`, `PresenceOfMyTypes` |
| `ScoringFunctions_Cistern` | 2817 | KEEP faction/building purpose, native requirements and existing affordability guard. | `UnderCountLimit`, `LuaScoringFunction`, `StrategicIntention`, `MultiplyListScoringFunction`, `MaxScoringFunction` |
| `ScoringFunctions_Shinobi` | 2851 | KEEP military/native chain plus existing user army and economic-mode gates. | `LuaScoringFunction`, `UnderCountLimit`, `MultipleProduced`, `TimeToAcquire`, `PopulationPercentage`, `PresenceOfMyTypes` |
| `ScoringFunctions_ShinobiUpgrade` | 2869 | KEEP military/native chain plus existing user army and economic-mode gates. | `ScoringFunctions_PlayerUpgradeCommon`, `PresenceOfMyTypes` |
| `ScoringFunctions_BannermanSamuraiMelee` | 2877 | KEEP military/native chain plus existing user army and economic-mode gates. | `UnderCountLimit`, `PresenceOfMyTypes`, `MultiplyListScoringFunction`, `TimeToAcquire`, `StrategicIntention`, `MaxScoringFunction` |
| `ScoringFunctions_BannermanSamuraiCavalry` | 2896 | KEEP military/native chain plus existing user army and economic-mode gates. | `UnderCountLimit`, `PresenceOfMyTypes`, `MultiplyListScoringFunction`, `TimeToAcquire`, `StrategicIntention`, `MaxScoringFunction` |
| `ScoringFunctions_BannermanSamuraiRanged` | 2916 | KEEP military/native chain plus existing user army and economic-mode gates. | `UnderCountLimit`, `PresenceOfMyTypes`, `MultiplyListScoringFunction`, `TimeToAcquire`, `StrategicIntention`, `MaxScoringFunction` |
| `ScoringFunctions_DaimyoUpgradeJapanese` | 2935 | KEEP military/native chain plus existing user army and economic-mode gates. | `ScoringFunctions_PlayerUpgradeCommon` |
| `ScoringFunctions_Ozutsu` | 2940 | KEEP military/native chain plus existing user army and economic-mode gates. | `PresenceOfMyTypes`, `PresenceOfEnemyTypes`, `StrategicIntention`, `LuaScoringFunction`, `MultiplyListScoringFunction`, `MaxScoringFunction`, `PopulationPercentage`, `TimeToAcquire`, `MultipleProduced` |
| `ScoringFunctions_Pagoda` | 2967 | KEEP religion/relic support and existing religious count/handover constraints. | `UnderCountLimit`, `TimeToAcquire`, `StrategicIntention` |
| `ScoringFunctions_Atabeg` | 2979 | KEEP military/native chain plus existing user army and economic-mode gates. | `LuaScoringFunction`, `UnderCountLimit`, `TimeToAcquire`, `StrategicIntention` |
| `ScoringFunctions_ByzantineEasternMercenaryContract` | 3001 | KEEP military/native chain plus existing user army and economic-mode gates. | `ScoringFunctions_PlayerUpgradeCommon`, `PresenceOfEnemyTypes` |
| `ScoringFunctions_ByzantineWesternMercenaryContract` | 3011 | KEEP military/native chain plus existing user army and economic-mode gates. | `ScoringFunctions_PlayerUpgradeCommon`, `PresenceOfEnemyTypes` |
| `ScoringFunctions_ByzantineSilkRoadMercenaryContract` | 3021 | KEEP military/native chain plus existing user army and economic-mode gates. | `ScoringFunctions_PlayerUpgradeCommon`, `PresenceOfEnemyTypes` |
| `ScoringFunctions_ByzantineMercenaryHouse` | 3031 | KEEP military/native chain plus existing user army and economic-mode gates. | `UnderCountLimit`, `ProductionQueueContention`, `LuaScoringFunction`, `TimeToAcquire`, `PlannedPlacementScore`, `StrategicIntention`, `MaxScoringFunction` |
| `ScoringFunctions_CustomScoringExample` | 3117 | KEEP selection/example helper; not an economic throughput control. | `LuaScoringFunction` |
| `ScoringFunctions_Towers_Militia` | 3180 | KEEP military/native chain plus existing user army and economic-mode gates. | `MaxScoringFunction`, `UnderCountLimit`, `MultiplyListScoringFunction`, `PresenceOfMyTypes` |
| `ScoringFunctions_Towers_Regular` | 3200 | KEEP military/native chain plus existing user army and economic-mode gates. | `PresenceOfMyTypes`, `MultipleProduced`, `MaxScoringFunction`, `CounterScore`, `LuaScoringFunction` |
| `ScoringFunctions_Towers_Siege` | 3215 | KEEP military/native chain plus existing user army and economic-mode gates. | `PresenceOfMyTypes`, `UnderCountLimit`, `MultiplyListScoringFunction`, `MaxScoringFunction`, `PopulationPercentage` |
| `ScoringFunctions_Towers_Handcannon` | 3246 | KEEP military/native chain plus existing user army and economic-mode gates. | `PresenceOfMyTypes`, `MaxScoringFunction`, `UnderCountLimit`, `MultiplyListScoringFunction` |
| `ScoringFunctions_Towers_HorseArcher` | 3271 | KEEP military/native chain plus existing user army and economic-mode gates. | `PresenceOfMyTypes`, `UnderCountLimit`, `CounterScore` |
| `ScoringFunctions_Towers_Monk` | 3288 | KEEP military/native chain plus existing user army and economic-mode gates. | `PresenceOfMyTypes`, `UnderCountLimit` |
| `ScoringFunctions_Manor` | 3303 | KEEP faction/building purpose, native requirements and existing affordability guard. | `StrategicIntention`, `NotProducedRecently`, `UnderCountLimit` |
| `ScoringFunctions_Random2ARuntime` | 3336 | KEEP selection/example helper; not an economic throughput control. | No direct scoring factory call |
| `ScoringFunctions_Random2BRuntime` | 3343 | KEEP selection/example helper; not an economic throughput control. | No direct scoring factory call |
| `ScoringFunctions_Random2A` | 3352 | KEEP selection/example helper; not an economic throughput control. | `ScoringFunctions_LandmarkCommon`, `LuaScoringFunction` |
| `ScoringFunctions_Random2B` | 3358 | KEEP selection/example helper; not an economic throughput control. | `ScoringFunctions_LandmarkCommon`, `LuaScoringFunction` |
| `ScoringFunctions_Random3ARuntime` | 3365 | KEEP selection/example helper; not an economic throughput control. | No direct scoring factory call |
| `ScoringFunctions_Random3BRuntime` | 3372 | KEEP selection/example helper; not an economic throughput control. | No direct scoring factory call |
| `ScoringFunctions_Random3CRuntime` | 3379 | KEEP selection/example helper; not an economic throughput control. | No direct scoring factory call |
| `ScoringFunctions_Random3A` | 3388 | KEEP selection/example helper; not an economic throughput control. | `ScoringFunctions_LandmarkCommon`, `LuaScoringFunction` |
| `ScoringFunctions_Random3B` | 3394 | KEEP selection/example helper; not an economic throughput control. | `ScoringFunctions_LandmarkCommon`, `LuaScoringFunction` |
| `ScoringFunctions_Random3C` | 3400 | KEEP selection/example helper; not an economic throughput control. | `ScoringFunctions_LandmarkCommon`, `LuaScoringFunction` |
| `ScoringFunctions_LancasterLevy` | 3407 | KEEP military/native chain plus existing user army and economic-mode gates. | `StrategicIntention`, `PresenceOfMyTypes`, `TimeToAcquire` |
| `ScoringFunctions_LancasterWynguardArmyCounterCavalry` | 3417 | KEEP military/native chain plus existing user army and economic-mode gates. | `StrategicIntention`, `PresenceOfEnemyTypes` |
| `ScoringFunctions_LancasterWynguardArmyCounterArchers` | 3424 | KEEP military/native chain plus existing user army and economic-mode gates. | `StrategicIntention`, `PresenceOfEnemyTypes` |
| `ScoringFunctions_LancasterWynguardArmySiegeSmall` | 3432 | KEEP military/native chain plus existing user army and economic-mode gates. | `StrategicIntention`, `PresenceOfMyTypes` |
| `ScoringFunctions_LancasterWynguardArmySiegeLarge` | 3441 | KEEP military/native chain plus existing user army and economic-mode gates. | `StrategicIntention`, `PresenceOfMyTypes`, `PresenceOfEnemyTypes` |
| `ScoringFunctions_SupportMilitary` | 3451 | KEEP specialized production/research/selection chain; no demonstrated economic zero to remove. | `ScoringFunctions_CombatCommon`, `StrategicIntention`, `PresenceOfMyTypes`, `PopulationPercentage`, `UnderCountLimit` |
| `ScoringFunctions_CollectiveHunting` | 3466 | KEEP distinct research and seven-minute gate; not Professional Scouts. | `StrategicIntention`, `MinimumGameTime` |

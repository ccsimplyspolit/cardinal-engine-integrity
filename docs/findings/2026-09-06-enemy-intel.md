# 2026-09-06 — Enemy intel / counter-plan

Build **16.3.11308.0**. Cloak off. Overlay world cache (not player FoW).
Landmark keys from `Documents\AOE4HSettings\NativeEspData\unit_intelligence.scar`
(aoe4world/data revision **b2cd3822**, 23 civs). Nothing guessed; gaps live in
`kAiEnemyIntelUnknowns`.

## What it is

Pure C++ `ai_enemy_intel.h/.cpp`. Host-tested. No Relic natives.

Snapshot in (`AiEnemyIntelInput`: civ, age, vills, gather, structures,
landmark blueprint names, observed mix) → `AiEnemyPlan` (archetype,
confidence, predicted mix + ETA, per-type building desire, favour/cut
families, Russian HUD). 35 s hold (`kAiEnemyHoldSec`); a higher threat
or a tower rush breaks it immediately.

Archetypes: boom, fast castle, feudal infantry / cavalry, archer mass,
tower rush, trade boom, naval, mixed, unknown.

## Data vs table

118 age-up landmarks in the scar (capital Abbasid TC and Rus hunting cabin
are tagged `|landmark|` in the data — **excluded**; age-4 wonders
**excluded**). 93 table keys. Every remaining data key matches a table
substring (longest match wins: `white_tower_eng` vs `white_tower_lan`,
`keep_control_sul` vs `keep_control_sul_ha_tug`).

Variant civs reuse the parent key (`_ha_01` / `_ha_mac` / `_ha_sen` /
`_ha_tug` / `_ha_gol`). `AiEnemyLandmarkCivAlias`: **je→fr, od→hr, ay→ab**.

## Signal fixes this pass

| Landmark | Was | Now | Why |
|---|---|---|---|
| Meinwerk Palace (`imperial_palace_of_paderborn_hre`) | Tech+Infantry | Tech | Data: "Technology Landmark". Infantry tag made HRE Meinwerk a feudal infantry opening. |
| Steppe Redoubt (`khara_khoto_mon`) | Defense+Produces | Eco | Data: "Economic Landmark" (ger/house). `kAiLmProduces` made the planner count it as a unique trainer. |

## Relic wiring (already in `ai_runtime`, not this file)

Collect worker `AiRuntimeOnPlanPublished`:

1. Fill `AiEnemyIntelInput` from the enemy `AiArmyComp` (planner census +
   landmark names + mix).
2. `AiEnemyIntelInfer` → blend predicted mix into `AiCounterSample` while
   `AiEnemyIntelPredictWeight` > 0 (0 once ≥6 visible army).
3. `AiEnemyIntelPublish`. `ApplyIntelCuts` ORs `cutFamilies` (runtime copy;
   canonical helper is now `AiEnemyIntelOrCuts`).
4. `__EcoAct_Apply` fields: `ei,wb,wa,ws,wg,wd`. SCAR
   `__EcoAct_MilBldWant` is O(1) (`BP_GetName` once).

Opening-phase **gate** is eco-owned. Feed:

`AiEnemyIntelThreatLevel() >= 2` → `AiEcoDesireInput.threat` →
`AiEcoGoalPlan.openingPhase` → `__EcoAct.op` → `__EcoAct_MilBldGate`
(zeros `ScoringFunctions_MilitaryProductionBuilding`). Per-type want
applies only after that gate is open.

HUD: `eplan.hudRu` on Scoring observatory and AI BRAIN (`Противник: …`).

## Unknowns (not guessed)

Abbasid/Ayyubid House of Wisdom **wing**, Ottoman Military School selected
unit, Chinese dynasty, Mongol landmark pack/move, Byzantine cistern oil,
Malian cattle state.

## Tests / build

`AOE4HOOK/tests/adversarial/test_ai_enemy_intel.cpp` +
`build_ai_enemy_intel.cmd`. School of Cavalry, Council Hall, 2-TC boom,
tower rush, hysteresis, blend, Meinwerk→fast castle, Hippodrome→cavalry,
`AiEnemyIntelOrCuts`, 23-civ coverage.

Host tests: all passed (`test_ai_enemy_intel.exe`).
Release|x64: `AOE4HOOK\internal\x64\Release\InternalInjector.dll` (2026-09-06 16:44, no LNK1104). Cloak off.

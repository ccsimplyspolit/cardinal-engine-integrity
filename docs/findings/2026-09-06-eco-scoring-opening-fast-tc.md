# 2026-09-06 — Eco scoring: opening gate, feudal upgrades, Fast TC

Workstream finish (Sep 5 leftovers). No live inject this turn. Host tests
`test_ai_eco_goal` + `test_ai_production_math`. Cloak off.

## Bugs

1. **Barracks at 0:00** — Relic `ScoringFunctions_MilitaryProductionBuilding`
   is `StrategicIntention({combat=1.0})` with no TimeToAcquire. Overlay
   combat intention alone bought a rax ahead of the Age II landmark.
2. **No horticulture / lumber / mining in Feudal** — Relic
   `PlayerGatheringUpgrade` Evaluate `0x2D00120` writes 0 unless gather
   ratio > 1. A later `op` Lua-0 on the same list (shared with the rax
   gate) kept the candidate dead until the 2nd Town Center.
3. **Fast TC** — treated as ecoLock (14 TCs), English 400w+300s forever,
   session ExpansionTC dropped `OneStructureFromGroupAtATime`, contest
   skipped stone at `tcN>=2` and used English costs before Layer B.

## What landed

| Layer | Change |
|-------|--------|
| A | `__EcoAct.op` zeros **only** MilitaryProductionBuilding (`__EcoAct_MilBldGate`). Gathering / ExpansionTC / House / landmarks stay ungated. Session ExpansionTC matches installer: UnderCount + SI + TTA clamp 0.85 + OneStructure + Afford. |
| A | Gathering REPLACE (session + installer, re-assert on Apply / LayerBInvalidate). No gather native. villager=0.2. No `__EcoAct_GathGate`. |
| B | `AiEcoGoalCompute` (`ai_eco_goal.h`): opening = Dark, or Feudal until 2nd TC / Castle underway, unless threat or `mass_army`. Fast TC target = 2. Civ costs from `unit_intelligence.scar`. Hoard sets `iUpgrade=0.45` (defer, not zero). Auto opening keeps `iUpgrade>=0.60`. |
| B | Lock-mode wood/stone/food floors apply **only while `goal.active`**. After 2 TCs + Feudal the reserve lifts so horticulture can run; `maxTc` stays 2. |
| Contest | `stoneBlocked = !hoard && tcN>=2`. Hoard re-asserts gatherer/income (`kContestGathFmt`). `AiEcoGoalInput` filled from planner snapshot (civ / stocks / match clock) so Mongol Fast TC is not English stone on the first ticks. |

Threat open: `AiEnemyIntelThreatLevel()>=2` or three enemy combatants /
mil bld + one (runtime). Squad lock filter and `ai_farm_layout.*` were
not touched.

## Failed / do not repeat

- Lua-0 gathering on the same `op` that zeros rax. Multiply list →
  horticulture stays 0 for the whole Auto Feudal 1-TC boom.
- Hardcoding `UnderCountLimit(9,10)` or leaving session ExpansionTC
  without OneStructure (installer REPLACE / session REPLACE: last writer
  wins).
- Keeping Fast TC 400/300 after the 2nd TC is up — the toggle then never
  “finishes” and Feudal eco stays on stone.

## Verify live

`Documents\AOE4HSettings\Logs\aoe4_internal.log`: `eco_goal op=` /
`eco contest hoard` / `opening gather kick`. HUD Scoring observatory:
`tc=2` on Fast TC, `iu` ~0.45 while hoarding, ≥0.60 on Auto Feudal.
No barracks foundation before Age II unless threat or mass_army.

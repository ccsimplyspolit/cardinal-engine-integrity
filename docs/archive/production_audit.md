# Production and combat audit

Status: initial map before edits, 2026-09-05. Evidence below is repository inspection; it is not an injected-match verification. The working tree already contains extensive changes, including all production files; this audit preserves them.

## Before map

`AiPlannerUpdate` consumes the collector cache, builds combat fighters and per-owner army needs, and publishes `AiPlanSnapshot`. Its per-unit combat rows retain current HP and reload. `AiRuntimeOnPlanPublished` converts the snapshot into role cuts/desires. `AiProductionUpdateFromPlan` separately selects a non-local army, ranks seven standard families plus at most one unique unit, and publishes a locked HUD observatory. Relic still owns actual production.

`unit_profile.cpp` loads `unit_intelligence.scar` into string-keyed packed profiles and a PBG-to-key index. Lookups copy profiles; family and unique picks scan the entire catalog. `CombatFillFighter` combines the catalog, live HP/reload, inferred national upgrades, and heuristic special-unit modifiers. `CombatUnitsToKill` estimates reciprocal attrition rather than simulating a battle. Production reconstructs enemies from `exactUnits` blueprint counts, losing the live row HP/reload information used by the planner.

## Confirmed code defects

| Finding | Before evidence | Consequence | Planned action |
|---|---|---|---|
| Unsynchronized catalog initialization | `unit_profile.cpp:958-965`, `1027-1032`: bool is set before maps/vectors finish being built | Present and collector can read partially built containers, including during rehash | Publish once with `std::call_once`; immutable afterward |
| Blend adds constructor reload | `ai_combat.cpp:1614-1650`; `CombatFighter::reload` defaults to 1.5 | Blending one fighter increases its reload by 1.5 seconds; damage estimate depends on sample count | Zero additive accumulator reload; regression over one/many identical fighters |
| Explicit producer filter is ignored | `unit_profile.cpp:1316-1322` bypasses all producer checks for Xbow/Gun/Knight | A caller asking for a keep can receive a stable/archery-only PBG | Bypass only the default producer filter; respect explicit hints |
| Unknown age becomes Imperial | `unit_profile.cpp:1296-1299`, `1352-1355`, `1429-1432` | Missing/invalid age permits age-IV catalog candidates | Reject unknown age in train selection; test negative/zero |
| Missing civ line invents English fighter | `ai_combat.cpp:1540-1551`: only gun fails after a civ lookup miss | Planner can request a unit family the civ does not possess | Fail all explicit-civ misses; retain documented generic fallback only without civ |
| Stale production invalidation | `ai_production.cpp:38-76` omits player ids, both smith/uni tiers, enemy age and queue-scan availability; unsigned casts of stock floats | Changed combat data may reuse stale rank; NaN stock conversion is undefined | Remove unsafe partial cache or make complete and tested; no unsigned float casts |
| Observatory commit data race/lost update | `ai_production.cpp:310-311` reads `g_obs` unlocked, later replaces it; `AiProductionNoteCommit` writes concurrently | UI commit acknowledgment can be lost | Preserve generation and latest commit under final publication lock |
| Current queue time is an estimate | `ai_production_math.h:47-55` multiplies all queues by 0.25 and averages all military buildings | Not a per-producer completion time | Label as estimate; exact queue end-times remain unknown |

## Confirmed limitations requiring contracts or coordinated changes

- `AiProductionUpdateFromPlan:258-273` treats every non-local owner as an enemy. `AiArmyComp` does not carry diplomacy. Parent must add relation and filter allied/neutral owners in runtime and production.
- Catalog age and producer names do not prove completed tier research, landmark choice, current building availability, resources, or population. `UnitProfileCollectObsoleteAttribs:1372-1420` infers obsolete from age/family, not a completed upgrade. It can lock unrelated same-family units and a usable predecessor before its replacement is engine-available. No claim of engine availability is justified by this catalog alone.
- `AiProdCandidate.available` currently means catalog eligibility and role allowance; no engine availability query is captured. Ranking is not proof of a Relic queue decision.
- Exact blueprint counts cover only one selected enemy and collapse live HP/reload; combat buffs infer research from age/buildings, including `CombatSmithTier`. These are estimates, not observed completed technologies.
- The obsolete list has a 96-entry caller buffer and silently returns that cap. The rank has 12 slots but currently generates only seven families plus one unique; it still omits additional unique and siege choices.
- `CombatUnitsToKill:1497-1518` clamps at 24 and uses heuristic connect/ability factors. The 24 is an undocumented model cap, not an engine bound. Removing it must keep invalid-data handling and integer conversions defined.
- Catalog strings have fixed buffers. Current data lengths must be checked before changing layouts; any overflow must be reported rather than assumed absent.

## Verification and benchmark plan

1. Compile isolated Windows host tests against the real `ai_combat.cpp` and `unit_profile.cpp`, supplying inert logging, file-path and live-read stubs. No game native calls and no shared DLL build.
2. Regress single-fighter blend identity, identical-army scale invariance, explicit civ failure, explicit producer exclusion, invalid ages, non-finite math, and simultaneous catalog first use.
3. Run existing counter/production math tests plus real catalog consistency checks across every civ, age and unit kind.
4. Benchmark pure combat evaluation at 100/500/1000 synthetic fighters (seven candidates), record mean/p95/p99/max. Compare repeated defender reconstruction with precomputed immutable fighters. These are host calculation costs, not frame-time or game FPS measurements.
5. Add persistent parallel workers only if measured pure calculation cost justifies synchronization and scheduling. No per-tick threads; no worker engine calls. Present never waits for this analysis.

Next: implement only reproduced defects, then append exact tests, results and residual limitations.

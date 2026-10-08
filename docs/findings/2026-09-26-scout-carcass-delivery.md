# Scout carcass delivery — 2026-09-26

## Confirmed causes

The overlay had no carcass pickup/delivery actuator. `ai_planner.cpp` treats
deer as exploration POIs; scouts normally remain under Relic AI control.
Increasing a food desire does not create a carcass transport job.

Decoded stock `ai/ai_economy/complete/default_economy.rgd`, default dataset:

| Production group, zero-based | Forester upgrades | Binding | max_current | base_scale | minimum_score_to_produce |
| --- | --- | --- | --- | --- | --- |
| 94 | common, mon, improved_mon, sul | ScoringFunctions_NoScoring | 0 | 0.00001 | 1 |
| 89 | byz, sul_ha_tug | ScoringFunctions_PlayerEconGatheringUpgrade | -1 | 700 | 200 |

The common Professional Scouts research is deliberately excluded by the stock
AI production group. This is stronger than a small food score. Replacing
`ScoringFunctions_NoScoring` globally would enable unrelated candidates and
would not remove the group's other constraints. `ScoringFunctions_CollectiveHunting`
is a different technology; changing it would not fix forester research.

Additional overlay defect: `radar.cpp::ClassifyName` classifies corpses as
`Resource`, but `DepositKindFromName` recognized hunt only in the `Animal`
branch. A delivered deer corpse could disappear from the C++ food contest.

## Game constraints

`sbps/races/english/unit_scout_1_eng`, default `squad_ability_ext`, lists
`pickup_carcass`, `pickup_carcass_no_boar`, and `scout_drop_off_all_at_entity`.
The `pickup_carcass_no_boar` ability requires a carriable animal target and
explicitly excludes `gaia_food_boar_corpse` and `food_cattle_corpse_mal`.
It also has a **race requirement** (Abbasid, Sultanate, Tughlaq), so using it
for English/HRE/Rus scouts would always fail despite owning the upgrade.
The actuator tries `pickup_carcass` and `pickup_carcass_no_boar`, accepting
only a variant the current squad can cast on the actual target.

Both require target types `animal` and `carriable`. The freshly decoded
`gaia_food_boar_corpse` has **no `carriable` type in default or xp3**, but has
it in the campaign dataset. Default-match boar corpses therefore remain food
for villagers at their location. Boar candidates are submitted only if the
live ability permits them (for example, the campaign dataset); the code does
not change their types or bypass prerequisites. Deer corpses are supported.

The shipped training scripts read the scout entity state-model integer
`pickup_attachments_count` to determine whether the scout carries a carcass.
`Squad_CanCastAbilityOnEntity` validates the real ability and target before
each command. No prerequisite, cost, unit capability, or protected code is changed.

Local evidence: `K:/aoe4_dlc/analysis/scout-haul-20260926/default_economy.json`,
decoded with the local AOEMods.Essence CLI from extracted build 16.3.11308 Attrib.
Ability and squad records are under `analysis/game_16.3.11308/attrib-json-rest`.
The boar dataset evidence is `analysis/scout-haul-20260926/gaia_food_boar_corpse.json`.

Producer lists were checked against extracted `attrib-raw/attrib/ebps/races`:
ordinary Byzantine mills offer common forester, while the Winery offers
`upgrade_scout_forester_byz`; Mongol Gers and Khara Khoto offer `_mon`;
Delhi food control offers `_sul`; the Tughlaq worker elephant offers
`_sul_ha_tug`. Japanese houses/storehouse, Ottoman/Malian food buildings,
Rus Hunting Cabin/High Trade House, Chinese granaries and the other standard
mills must be included as candidates. These variants are selected from the
live **producer blueprint**, not merely the player's civilization.

## Implemented behavior

`ai_scout_haul.h` and the existing `ai_session.cpp` eco contest cooperate:

1. C++ reads the fresh world snapshot. It selects owned land scouts, owned
   town centers and hunt corpses, excluding spent/fogged targets and corpses
   within 20 world units of any owned town center. Every eligible scout receives
   up to 16 ranked targets; existing missions retain their target.
2. Lua resolves the IDs again, checks current ownership, visibility, ability
   requirements and distance from home. Selected or player-locked scouts are
   skipped. Two scouts do not select the same target in one pass.
3. Empty scouts receive the actual pickup ability. Once cargo is observed,
   they receive the actual drop-off ability on their own town center. This
   also returns scouts already carrying a carcass when no ground targets exist.
4. Unchanged travel is preserved. Idle failures retry after 8 simulation
   seconds and a long stalled command after 60. Command submission is never
   treated as evidence of pickup or successful unloading.
5. If a visible corpse needs transport and the upgrade is missing, request
   the producer's Professional Scouts at an idle food research building or
   the Tughlaq worker elephant.
   Require Feudal Age and the live resource cost, skip existing research queues,
   and submit `LocalCommand_EntityUpgrade(..., instant=false, queued=true)`.
   Requests retry at most once per 30 simulation seconds. Fast TC/Fast Age
   goal modes defer this discretionary research. Workers-only mode blocks
   this research spending but permits hauling with abilities already available.
   The game's normal validation
   and paid production flow remain authoritative.
6. Food contest recognizes animal corpses classified as resources, so idle
   villagers can gather the delivered food. AI disable clears haul bookkeeping.

No new timer, native squad lock, game-memory write or code hook is introduced.
The existing session/SCAR trust checks and window-thread eco commit remain in use.
Status is inspectable through `__EcoScoutHaul`; phase changes emit
`[AOE4HOOK scout-haul]` in script output. `research-request` denotes a request,
not confirmation that the game accepted or completed the research.

## Validation and limits

22 host tests execute the real embedded Lua with mocked live state. They cover
pickup/delivery, missing upgrade, age/cost/queue checks, civ variants, owned TC,
player locks, duplicate claims, stale positions, missing APIs, command rejection,
retry timing and match-clock reset, including the real race restriction on
the no-boar ability, conditional boar support, and Winery versus ordinary mill.
C++ tests cover 23 corpse/scout/research-producer classification checks.
Existing handover and land-only regression suites also pass.

This is a static diagnosis and a tested actuator, not an observed live-match
success. Native AI can still retask a scout; this implementation deliberately
uses ordinary commands without acquiring a new native AI lock. A live match
must confirm that the normal command flow retains the order, that the research
is accepted by the actual producer, and that transport completes. It does not
make scouts kill living deer, lure boar, or carry non-carriable boar corpses.
No multiplayer synchronization claim
is made beyond the pre-existing AI session's documented restrictions.

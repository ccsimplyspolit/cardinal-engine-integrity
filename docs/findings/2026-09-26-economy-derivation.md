# Economy derived from the game source — 2026-09-26

Build 16.3.11308. Every number below was read from the runtime decompilation
(`K:\aoe4_dlc\aoe4\gamesource\reversed`, RVAs only), the extracted attributes
(`K:\aoe4_dlc\analysis\game_16.3.11308`) or the decoded `default` AI bags.
Nothing here is a live measurement of resources per minute.

## How Relic's production director decides (verified)

| Step | Function | Behaviour |
| --- | --- | --- |
| Group parameters | production-group attrib parser, `rva_02A00000_02AFFFFF.c` ~150560 | `base_scale` @+92, `minimum_score_to_produce` @+96, `max_current` @+100 |
| Candidate utility | `sub_2B6C360` | `v = base_scale`; for each scorer of the list: **if `v <= 0` or `v < min` stop**, else `v *= scorer`. Afterwards `v < min` → 0. Slot +384 = `v`; final +400 = max(+380, +384, +388) |
| Inherited utility | `sub_2B66500` | an unmet requirement receives the dependent's utility + 0.01 in its own slot, so a wanted unit pulls its production building |
| Selection | `sub_2BBA9F0` | candidates in utility order; the first construction candidate adds a blocker (`sub_2B15320` → `sub_2B152A0`) so no second construction is taken in the pass; squads have their own blocker (`sub_2B15270`). The base candidate vfunc +40 is `sub_2B65460` (`return 1`): **affordability is not a skip** |
| Resource demand | `sub_2BBA9F0` tail | costs of the selected candidates are summed and smoothed into the demand vector, 5% per pass |

Consequences:
- The check happens **before** each multiplication. A group with
  `base_scale < minimum_score_to_produce` is dead whatever its scorers return:
  `ScoringFunctions_Yatai` (500 < 501, `unit_yatai_1_jpn_ha_sen`) can only be
  produced through inherited utility. Not fixable from Lua.
- Lua scorers above 1.0 propagate (no clamp in MultiplyList `0x2D03940` or
  LuaScoringFunction `0x2D02750`). Put a multiplier first in the list.
- The top construction candidate is saved for (it blocks the others), so the
  ordering of construction utilities decides what gets built.

## Scorer semantics (verified)

| Scorer | Evaluate | Result |
| --- | --- | --- |
| `StrategicIntention` | `0x2CFDCD0` | weighted mean of `clamp(base+extra, 0, 1)`; no floor: `{combat=1}` at level 0 is **0** |
| `PopCapGenerator` | `0x2D02910` (factory `0x2C5B540`) | 1.0 when the population state (`sub_2BB9FC0`) is 3 — population + queue past the cap with `usable_popcap_extra_percentage` — else 0 |
| `TimeToAcquire` | `0x2CFF6C0` (factory `0x2C59620`) | `t = max_r((cost_r - stock_r) / income_r)` (∞ at zero income) + build time (ticks × 0.125 s) + requirement time; `t <= 0.01 → 0.01`; score `1 + (min-1)·t/maxSec` below `maxSec`, else `min`. Tuning: `in_acquire_time_max = 300`, `out_utility_score_min = 0.01` |

## Game data used by the planner

Villager (`unit_villager_1*`, `resource_gatherer_ext`):

| Resource | Rate /s | Carry |
| --- | ---: | ---: |
| wood, gold, stone, farm, sheep | 0.75 | 10 |
| berries | 0.69 (Abbasid/Delhi 0.8625, Tughlaq 0.858) | 10 |
| deer (`hunted_animal_flee`) | 0.825 | 25 |
| boar (`hunted_animal_danger`) | 0.9 | 25 |

Civ deviations: Order of the Dragon 0.9525 on everything (×1.27), 60 food /
23 s; Golden Horde 37 s; Lancaster sheep 0.9; Templar wood 0.63; French TC
production +10/15/20% by age (Jeanne none). Town Centers: 400 wood + 300 stone,
150 s; Chinese and Zhu Xi 75 s; Order of the Dragon 120 s; Mongol / Golden Horde
750 wood; Mali 400 wood + 350 gold. Every non-capital TC requires `feudal_age`
(the alternative `fast_expand` is a rogue-mode boon). Professional Scouts:
Feudal, 150 wood + 300 gold, 75 s; Rus research `upgrade_scout_forester_rus`
at its hunting cabin / food building / Muscovy Trade Company. A living deer is
not `carriable`; its corpse (`gaia_food_deer_corpse`, 350 food) is.

Relic's own gatherer preferences are civ-specific (Rus villagers +200 hunt,
Abbasid / Delhi villagers +100 berries); there is no general hunt preference.

## What changed

1. **Villager food floor** (`AiEcoVillagerFoodFloor`): `ceil(TCs × villFood /
   trainSec(age) × 1.2 / (0.75 × 0.8 × civGatherMul))` food gatherers, applied
   last in every mode. The 1.2 slack (2026-09-27) covers source changes —
   sheep run out around the age-up — after a French TC idled at the
   transition with the floor sized for the settled rate. One TC needs 5 (French
   6), two need 10; a food bank may cover at most half of the upkeep (180 s
   horizon), and food saved for the Age II landmark does not count.
2. **Second Town Center window** (auto / only_eco / mass_army / full AI /
   fast_tc; not workers_only, not fast_age, not a user ceiling of 1):
   bank the landmark → place it → the TC bill is gathered while it builds →
   the TC goes down when Age II lands. `ExpansionTC` gets `x2.5` once the bill
   is banked (800 × 2.5 × SI × clamped TTA ≥ 1615, above Manor 1400, DropOffs
   1050, Mills 1000, military buildings 1000), a needed House gets `x2.0`
   (2020) so population never stalls, and while no threat is present the
   non-essential spenders (`kEcoActTcReserveHooks`) are deferred until the TC
   stands or the stock exceeds the bill by 250. A banked TC that is not placed
   within 45 s releases the window for 90 s. ExpansionTC's intention is now
   `{economy=1}` only.
3. **Army lock no longer stops Relic training the army.** `combat` and
   `siege` are production intentions (`Infantry`, `RangedInfantry`,
   `CombatSiege` and `MilitaryProductionBuilding` multiply
   `StrategicIntention({combat=1})`). Zeroing them under the army lock gave
   every military unit and production building utility 0 — live 23:33
   (Ayyubid, 8 spears / 10 archers / 7 knights): no counter, no barracks, the
   age-up took the resources. Offense and the target multipliers stay parked.
4. **Spearmen are never family-cut while enemy cavalry is on the field** (mean
   horse + knight ≥ 4), whatever the dominant role.
5. **Hunting.** Living boar is no longer an idle-villager job; hunt ranks
   after sheep and before berries. With Professional Scouts researched a scout
   kills a living deer near home (110) and carries the corpse; the research
   request respects the TC reserve and uses the Rus variant at Rus producers.
6. **Civ table corrections**: French per-age TC bonus instead of a flat 19 s;
   Zhu Xi 75 s TC; Order of the Dragon gather multiplier.

## Verification

Host: `test_ai_eco_goal` (window, watch, civ table), `test_ai_production_math`
(floor, army lock, installer v63), `test_ai_counter_math` (spear guarantee),
`test_ai_tc_boom.py` (real Lua: boost, house, gate, idempotent re-wrap, body
order, priority arithmetic), `test_ai_scout_haul.py` (deer kill, reserve, Rus),
`test_eco_idle.py` (ownership and construction guards). A live match is still
needed to confirm the TC timing and the counter-army response.

## Open points

- ~~Abbasid / Ayyubid age up through a House of Wisdom wing research, which
  the world scan cannot see as a foundation: their second-TC window opens
  only when Age II lands.~~ Closed 2026-09-27: a queued House of Wisdom item
  (`hasProd && queueN > 0`, Dark Age) sets `AiArmyComp::ageUpResearching`,
  which `AiArmyFeudalLandmarkPlaced` counts as the placed landmark. See
  [2026-09-27](2026-09-27-antipick-lockmodes-threat.md).
- `AiEcoCivCostOf("ch")` keeps `lmCount = 2`; the Dark Age food reserve for
  Chinese is therefore 800. Not changed without an attrib check of the
  Chinese age-up requirement.
- The window's stand-down timer (`AiEcoTcWatch`) lives in the runtime only;
  the observatory split the contest reads does not apply it.

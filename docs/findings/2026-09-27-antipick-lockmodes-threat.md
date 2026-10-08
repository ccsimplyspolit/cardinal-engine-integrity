# 2026-09-27 — anti-pick data, lock modes, threat scope, one-TC matches

Follow-up to [2026-09-26 economy derivation](2026-09-26-economy-derivation.md).
Reports: "is the anti-pick right against aoe4world/data", "the Full AI
button sticks out of the menu", "the lock buttons do nothing mid-match",
"a barracks in the Dark Age when it should age up", "Ayyubids gather little
wood", "French forget food at the age-up".

## Anti-pick data: aoe4world/data vs the game

`github.com/aoe4world/data` main is `b2cd382` (2026-05-04, patch 16.1.9737),
the newest branch. The game is 16.3.11308. An audit
(`unit_intelligence.scar` against `analysis/game_16.3.11308` EBP `health_ext`
+ weapon `weapon_bag`) compared 548 combat units: 41 differed (damage 21,
attack interval 20, bonus 14, HP 4) — e.g. Mali spearman cavalry bonus 5–10
vs the game's 17–28, Desert Raider melee +13–19 vs cavalry missing, cannon,
Earl's Guard, repeater crossbow interval, Golden Horde bodyguard HP.

Engine rule (weapon `target_type_table`): a `target_unit_type_multipliers`
entry adds `base_damage_modifier` when the defender's `type_ext
unit_type_list` holds its `unit_type`. aoe4world `classes` are those tokens;
its modifier targets are the same tokens split into sorted words
(`light_melee_infantry` → `infantry+light+melee`).

Fixes:

1. **C++ bonus matching** (`ai_combat.cpp`). `ParseProfileBonuses` dropped
   every multi-word target, so the longbow's +6 vs `light_melee_infantry`
   (spearmen), springalds' vs `melee_infantry` and spearmen's `war_elephant`
   were lost; elephants got a `x0.25` guess. Now `CombatTypeKey` hashes the
   sorted words, fighters carry `bonusKey/bonusVal` and `classKey`, and
   `CombatBonusDamage` matches exactly when both sides are known (role
   buckets remain the fallback for table fighters).
2. **Generator reads the game** (`tools/generate_unit_intelligence.py
   --game-attrib <game_16.3.11308>`): HP, melee/ranged armor, primary weapon
   damage, attack interval (phases + one 0.125 s tick) and bonus by engine
   unit type override aoe4world for every unit with an EBP (749 applied).
3. **Hybrid units.** `primary_weapon` preferred any ranged weapon, so the
   Donso was modelled as a 5-damage javelin thrower (+5 vs cavalry), and Earl's
   Guard / Naginata Samurai Levy as ranged. A melee-class unit whose ranged
   weapons all have a minimum range (a periodic opener it cannot use in
   contact: Donso javelin, Earl's Guard dagger, levy yumi, min 2.5 tiles) now
   fights with its melee weapon. Earl's Guard carries the engine token
   `spearman_donso` but its war hammer has no cavalry bonus ("countered by
   knights"): it is heavy infantry now, not a spear.

4. **Counter role from armor** (`counter_for_armor`): the catalog's
   `counter` field was a fixed role map. Checked against aoe4world's own
   "Countered by …" text, 463 of 475 agreed; the misses were armored units
   whose map said archers (Heavy Spearman 4/4, Wynguard Footman 3/6, Rus
   Tribute, Black Rider → crossbowmen) and the unarmored Landsknecht (0/0,
   heavy class → crossbowmen, aoe4world says archers). With the game's armor
   the rule is: ranged armor ≥ 3 swaps archers for crossbowmen, a heavy-class
   unit with no armor is an archer target. Now 475 / 475. (The C++ counter
   uses the TTK math, not this field; the Lua hybrid and HUD read it.)

After regeneration 9 audit rows remain, all explained: the cannon's primary
weapon is `True Damage` 60 (+55 infantry / elephant, +450 building) and
matches the catalog — the audit script falls onto the Royal barrage ability;
the Desert Raider is a ranged-class hybrid whose melee stance (+13–19 vs
cavalry) is not modelled. `tools/test_unit_intelligence.py` and
`tools/test_ootd_power.py` fail on their coverage / spatial-model asserts with
the old catalog too (stale since buildings joined the catalog).

## Lock modes

| Button | Cause | Fix |
|--------|-------|-----|
| Full AI | third `SameLine` in a two-column row | own full-width row |
| Mass Army | the ecoLock blanket (all seven families cut) ran before the mode switch, and Mass Army kept it with `mass=1`: before the enemy fielded an army the button trained nothing | Mass Army trains against the counter's own cut (`roleCut`) |
| back to Auto | only explicit modes skipped the 35 s hysteresis; Mass Army → Auto sat out the hold with the old tactic applied | `AiCounterLive::lockMode`; any change commits at once |
| Full AI mid-match | an enable-time shape (no army lock, `Game_AIControlLocalPlayer`); a mid-match press changed only the cuts while the army stayed locked, and switched the `+0x40` stamp off over still-locked rows | the stamp runs whenever the army lock is live. Out of a running Full AI session the button re-arms (Disable → Enable: the army is locked before `AI_Enable`, empty-unlocked gate kept) and the player gets the army back. Into Full AI while the army is locked it does **not** re-arm: Disable keeps combat `+0x40` ([2026-09-14](2026-09-14-disable-keeps-army-lock.md)), so the army would stay locked anyway, and the Full AI enable skips the empty-unlocked gate — `AI_Enable(true)` over those rows is `rva=0x2A45959`. It applies from the next match; the tooltip and status line say so |

## Live evidence (aoe4_internal.log 2026-09-27, 00:48–02:51)

- `eco_goal ... tc=1` on every line of all five matches: `tc` is `maxTc`.
  `BuildOrderResolve` reports the current TC count for a guide that never
  mentions a Town Center; the auto-picked rush guides (French
  `team-knight-feudal-all-in`, Macedonian varangian rush, OotD fast
  burgrave) then capped the match at one TC. **The guide no longer lowers
  the ceiling** (user decision: "игнорируй tc=1").
- French 01:01: `threat=1` from 2:35 with `en={...}` all zero — an inferred
  aggression landmark (`AiEnemyIntelThreatLevel>=2`). That switched off the
  Dark Age opening (barracks at `iCombat 0.62`), kept the second-TC window
  from gathering (`peaceful` needed no threat) and stayed on all match.
- French: at 4:10, right after Feudal landed, `mass=1` (3 enemy spearmen
  somewhere) flipped the split to the fixed MASS `.32 / .28 / .34 / .06` — a
  third of the villagers to gold for spearmen and archers that cost none.
- Ayyubid (telemetry of 2026-09-26 22:52 and 23:43, villager positions vs
  resource sites): no lumber camp until 7:30 in one match, 0–4 of 14–20
  villagers near wood for eight minutes in the other. The auto-picked guide
  (`ayyubids-6mins-3tc`) has steps parsed as wood 0 and stone .36 in the
  Dark Age; max-then-renormalize diluted our wood share to ~.24. Their
  second-TC window also opened only when Age II landed: the wing research
  is not a foundation the scan could see.

## Threat, split in two

- `AiEcoBaseThreat(mine)`: three enemy combat units (scouts, workers,
  traders, monks excluded) within 125 units (~25 tiles) of an own Town
  Center, or an enemy tower / keep at the base. Counted in the planner's
  unit pass (`AiArmyComp::enemyNearBase`, `enemyTowersNearBase`). Stops the
  Dark Age opening and the second-TC gather.
- `AiEcoEnemyThreat(enemy)` (unchanged formula) and the counter's MASS /
  `anti_*` read: open military production from Age II, release the
  second-TC spending reserve; the TC bill keeps the gather split.

Order of play (user): bank the age-up, place the landmark, then the second
TC; counters when threatened. `AiEcoGoalCompute` follows it:

| | Dark Age | Feudal, 1 TC (window) | later |
|---|---|---|---|
| barracks gate (`op`) | closed unless base threat / Mass Army | open on any threat or MASS | open |
| TC gather split | from landmark placement | unless base threat / Mass Army | — |
| TC spending reserve | while calm | while calm | — |
| counter MASS reshapes the economy | only under base threat | only under base threat | yes |

## Economy fixes

- Food floor slack 1.2 (source changes around the age-up): one TC 5 food
  villagers (French 6), two 10.
- MASS split derived from the counter need (`AiEcoMassGatherSplit`):
  per-family bill (spearman 60f 20w, archer 30f 50w, horseman 100f 20w,
  man-at-arms 90f 20g, crossbowman 80f 40g, handcannoneer 120f 120g, knight
  140f 100g — the most common catalog price) over 90 s, plus villager upkeep
  and a house a minute per TC, averaged with the base split. Spear / archer /
  horse need → food .57, wood .29, gold .11.
- The guide's gather blend is skipped while the plan derives the split (Dark
  Age, second-TC window).
- Abbasid / Ayyubid: a queued House of Wisdom item in the Dark Age is the
  age-up in progress (`ageUpResearching`), so their TC window opens at the
  wing click like everyone else's landmark; a queued wing in Feudal marks
  the Castle age-up underway.
- `[AI] intents` now logs `base=` / `near=`, `tb=` / `tr=` and the gather
  split on change.

## Verification

Host: `test_ai_eco_goal` (Dark Age gate vs strategic / base threat, window
under threat / MASS / base threat), `test_ai_production_math` (floor slack,
French window, derived MASS split, MASS vs opening / window / base threat),
`test_ai_counter_math` (Mass Army without the blanket, lock-mode commit),
`test_ai_build_order` (raise-only ceiling, plan-owned split),
`test_ai_planner_threat` (new: base threat, wing age-up, Golden Tent),
`test_ai_catalog_combat` (Donso spear +17, Earl's Guard not a spear). A live
match is still needed for the timing.

## Open points

- A `[CRASH] source=VEH code=0xC0000005 rva=0x9701E1 av_addr=0x248
  last_native=army relock scan` at 01:20:40 (French match) was first-chance:
  the process went on to two more matches. Not investigated here.
- Desert Raider's melee stance and the Royal Cannon barrage are not in the
  combat model.
- The base-threat radius (125) and count (3) are policy, not game data.

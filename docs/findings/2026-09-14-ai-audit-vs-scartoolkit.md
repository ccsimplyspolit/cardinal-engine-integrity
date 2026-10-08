# 2026-09-14 — AI audit against ScarToolKIT and Relic's own scoring scar

Scope: the production-scoring half of the bot. The lock half is covered by
`2026-09-14-stk-eco-army.md` and `2026-09-14-stk-onspawn-no-cpp-relock.md`.

Reference used for "correct": not ScarToolKIT but
`sdk/scar/sga/cardinal/Data/ai/cardinal_scoring_functions.scar` — the game's
own file. STK is a second opinion, and it is wrong in places (below).

## STK V4.2 carries no AI change

`scar/Scartoolkit_crack_AOE4-main/updates_v42_20260908/COMPARE.md`:
"Lua_Scripts (8 files) — **byte-identical to V4.1**", "Lua overlay scripts in
the zip were not updated". The V4.2 release rebuilt the FOW helper PE only
(`module.pdb`, MSVC 14.0, Sep 1 2026). Every copy of `ai_lock_army.lua` in the
tree hashes `3190b84e8f8c` except one stale `exfil/source_code/store_dump`.

So there is nothing new to port. STK's AI is five scripts, frozen.

## Parity is already reached on the scripts

| STK | ours |
|---|---|
| `ai_base_enable.lua` | `sdk/lua/warmonger.lua` — 40/40 hooks, 22/22 `ReturnZero`, plus `ClampPresence` (Relic multiplies the list; a missing enemy type zeroed the whole candidate) |
| `ai_risky.lua` | `sdk/lua/risky_econ.lua` |
| `DebugHUD.lua` | `sdk/lua/DebugHUD.lua` |
| `ai_lock_army.lua` / `ai_lock_villager.lua` / `ai_disable.lua` | `stk_lua_lock.cpp` |

## Where STK is wrong

- **Positive combat whitelist.** `ai_lock_army.lua` names 26 `scar_*` types.
  `scar_military` is not a universal base type (23 mentions in the whole
  cardinal tree, mostly rogue/missionomatic), so the list is the filter.
  Types the game's own scripts use that the list does not name:
  `scar_militia`, `scar_kanabo`, `scar_onna_bugeisha`, `scar_wynguard_footman`,
  `scar_wynguard_ranger`, `scar_war_elephant`, `scar_javelin`, `scar_genitour`,
  `scar_genoese`, `scar_hospitaller`, `scar_khan`, `scar_scorpion`,
  `scar_trebuchet_traction`, `scar_trebuchet_cw`, `scar_galleass`,
  `scar_war_galley`, `scar_combat_ship`, `scar_fire_ship`, `scar_warship`.
  Under STK those stay with Relic. Our negative `ecoTypes` filter is the
  reason we do not have that class of bug.
- **`ScoringFunctions_Cavalry` is dead.** STK defines it; Relic's catalog has
  no such hook (cavalry PBGs bind Infantry / CombatCommon). We inherited the
  dead body in `warmonger.lua` — harmless, already noted in
  `ai_scoring_catalog.h`.
- **`Rule_RemovePlayerEvent` arity.** `ai_disable.lua` passes three arguments;
  `sdk/scar/sga/engine/Data/scar/rulesystem.scar:313` is
  `function Rule_RemovePlayerEvent(f, player)`. Lua drops the extra, so STK
  survives by luck. Our two-argument calls are the correct ones.

## Hook coverage, measured

145 `ScoringFunction(s)_*` in Relic's scar. 96 are wrapped or gated directly;
28 more inherit a gate because Relic's body calls a hook we control at
construction time (`Fireship`/`NavalMilitary` → `CombatCommonNaval`,
every landmark → `LandmarkCommon`, `Infantry`/`RangedInfantry`/`CombatSiege`/
`SupportMilitary` → `CombatCommon`). 21 are uncontrolled, and every one of
them is uncontrollable or deliberately free:

- `Random*Runtime` (5), `SulGovernorDeferred`, `SulPalaceGovernorDeferred`,
  `NoScoring`, `CustomScoringExample` — these return a float, not a list.
  They are `LuaScoringFunction` bodies, not wrap points.
- `PlayerUpgradeCommon` and its six callers — deliberate, documented: an
  upgrade for units already in the field must not be gated.
  `PlayerUnitCombatUpgradeAllDifficulties` self-gates anyway: its
  `PresenceOfUpgradeableSquads` / `MilitaryPlayerUpgrade(50)` max is 0 with an
  empty army, which zeros the whole multiplied list.
- `PlayerImperialEconUpgrade` (ottoman only), `PlayerUpgradeFreshFoodstuffs`,
  `ScoringFunction_Mills` — cheap eco, left alone on purpose.

The one real seam was `ScoringFunctions_DefensiveStructuresCommon` — now
closed, see below.

## Water on hybrid maps

WaterGate (`Dock`, `FishingBoat`) plus NavalGate (`CombatCommonNaval`,
`WarShip`) reaches every naval producer, because Relic's `Fireship` and
`NavalMilitary` build their list by calling `CombatCommonNaval`. `TradeBoat`,
`PlayerEconNavalUpgrade` and `DefensiveStructuresCommonNaval` are ungated but
unreachable without a dock, which WaterGate already zeroes. STK zeroes seven
naval hooks flat and leaves the naval *upgrades* scoring — the reverse gap.

Both natives behind the gate exist on 16.3.11308:
`AI_DoWeHaveWaterLanes(aiPlayer)` and `AIPlayer_IsOnAnIsland()` — note the
second takes **no** argument, which is why `ask()` retries with none.

## Fixed here

- `ScoringFunction_Mills` was missing from `kRelicScoringFunctionHooks`. Relic
  spells this one without the plural; the catalog held only the plural forms,
  so `AiEcoActAllInRelicCatalog` would have rejected the real name and
  accepted nothing in its place.
- `kEcoActWaterGateHooks` was the only gate table with no
  `AiEcoActAllInRelicCatalog` assert — it was added after that block. A typo
  in it would have wrapped a global Relic never calls and the hybrid gate
  would have gone quiet with nothing in the log.

Both are compile-time only. `AI_SetDifficulty` range stays 0..6 (STK uses 6).

## ElGate on the emplacement body

`ScoringFunctions_DefensiveStructuresCommon` joined `kEcoActElGateHooks`. One
wrap is four leaves: `TemplarFortress(0.3)`, `Keeps(0.6)`, `WoodenFort(0.6)`
and `Outposts(0.4)` do not build their own list, each calls the common body.
The per-leaf Afford wraps stay — they kill 0-resource ghosts, a different
thing.

Why ecoLock and not always: `live.ecoLock` is set only below Castle with
`enMil < 0.5` and `enArmy < 1.5`, or by an explicit `fast_age` / `fast_tc` /
`only_eco` / `workers_only` choice (`ai_counter_math.h`). There is no enemy
army on the map in either case, and Relic gates emplacements behind
`MinimumGameTime(7*60)` anyway. Relic's own `SI {defense=1, null=1}` lands
near 0.26 under ecoLock — low, but a keep is still ~1000 stone the boom
asked for. The *upgrade* hook stays ungated, as before.

The trap this surfaced: **the ElGate binder was not variadic.**
`DefensiveStructuresCommon(aiPlayer, minPlacement)` is the only wrapped hook
that takes a second argument, and it hands `minPlacement` to
`AIProductionScoring_PlannedPlacementScore`. The old
`function(aiPlayer) … captured(aiPlayer)` binder would have fed that native a
nil and taken all four leaves down with it. Both copies — the session inject
in `ai_session.cpp` and the actuator installer in `ai_runtime.cpp` — are now
`function(aiPlayer, ...)`, matching what the Water and Afford binders already
did. Every other ElGate leaf takes `aiPlayer` alone, so `...` is empty there.

`tests/adversarial/test_ai_elgate_wrap.py` pins it: both binders must forward,
Relic's four leaves must still route through the common body, and the shipped
binder text is executed against a model of Relic's bodies to prove
`minPlacement` arrives as 0.6 and the gate zeros only under ecoLock. Reverting
the binder to one argument turns `PLACEMENT_SEEN` to nil and the test red.

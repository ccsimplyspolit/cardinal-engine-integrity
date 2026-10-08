# 2026-09-08 — relock teardown crash, Hippodrome Scout, Fast TC telemetry

Three items from the live match feedback (screenshot: Македонская «Разведчик с ипподрома»). Evidence: user-1 log (`0x36A7E7F`) + user-2 log (`civ=mac`, `fast_tc` active, `0x1ED50B9`).

## 1. Match-exit crash — `AI_LockSquad relock` at teardown (green-lit to touch)

Both exit crashes carried `last_native=AI_LockSquad relock`:
- user-1: `rva=0x36A7E7F` av_type=1 (write) at 23:30:26, `in_call=0`.
- user-2: `rva=0x1ED50B9` av_type=0 (read) `scar=eco_farm_ring` sid=50153 at 23:17:31.

`ArmyRelockTick` / `StkLuaLockHandleArmyRelock` gated only on `g_armyLive`, which stays set while the sim world is torn down. A relock issued then hands `AI_LockSquad` a squad the engine is releasing. Fix: gate both on `RadarSimWorldLooksLive()` (the same `ProbeSimWorldLive` primitive the marks scan uses). Pure teardown guard — in-match lock behaviour unchanged. Effectiveness must be confirmed on a live exit (the probe has to trip before the world frees).

## 2. Hippodrome Scout locked away from the player

Real leaf (tests + catalog `hippodrome-scout-1`): `unit_dummy_champion_scout_byz_ha_mac`. In `isArmy` / `StkNameIsLockableArmy` / `ai_combat` / `ai_planner`, `isHippodromeFighterName` ran **before** the scout check and excluded only the two exact tokens `dummy_champion_scout` / `hippodrome_scout`. Any scout leaf lacking that exact substring was read as a fighter (`dummy_champion`) and locked.

Fix: in all four classifiers a hippodrome/champion unit whose leaf contains `scout` is never a fighter (the fighters — horseman, riddari/knight, Earl's Guard — never carry `scout`). Relock lock crumb now also carries `bp=` so a mis-locked unit names itself in one log line. Regression: `test_hippodrome_scout_leaf_variant_stays_with_player`.

If it still locks live, the `AI_LockSquad relock sid=… bp=…` crumb gives the exact runtime leaf to add.

## 3. Fast TC "workers don't gather / no 2nd TC"

The C++ plan **does** reach SCAR: user-2 log has 70 `cuts lock=fast_tc` + `eco_ai_cuts` ScarDoString during the `fast_tc` window, and the actuator sends `gf/gw/gg/gs`, income and `tc=maxTc` from `g_desire` every tick. Expansion TC cost (`400 wood + 300 stone`, `mo/gol` 750/0, `ma` 400w+350g) is catalog-correct.

But `AiCounterShouldCommit` only commits on cut/mass/ecoLock changes, so once Fast TC settles it produces **zero commits** — the `[AI] eco_goal` line (the one telemetry that shows the preset's gatherer split / TC target reaching the actuator) never printed under `fast_tc`. A whole session looked inert with no way to check it. Fix: emit `[AI] eco_goal` on the goal-lock `desDirty` path too (throttled 5 s). Observability only — the desire was already sent. Next `fast_tc` match now shows the actual `g=…/tc=…` so a wrong value (or Relic ignoring it) can finally be diagnosed.

Build: `AOE4HOOK.sln` InternalInjector Release x64. Host + `test_ai_handover` green (fixed pre-existing `pickup_relic` assert left half-migrated from the kick-init refactor).

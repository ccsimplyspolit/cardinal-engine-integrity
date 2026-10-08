# 2026-09-06 — C++ farm rings around every food drop-off

Session restore of the farm-ring workstream. Geometry already lived in
`ai_farm_layout.h` (host-tested). This pass finishes catalog aliases, stops
two anchors from claiming the same plot, and actually **commits** the SCAR
payload (it was planned on the collect worker and never applied).

Cloak stayed off. `ai_runtime.cpp` / `mp_bypass.cpp` not touched.
Plugins only in `Documents\AOE4HSettings` (not edited).

## What Relic will not do

`ScoringFunctions_ResourceGenerator` sites come from the engine placement
planner (`AIBuildStyle` `BS_Farm=26`). That enum has no SCAR setter — IDA
xref for `BS_Farm` is the enum registrar only. The planner emits the four
orthogonal cells next to a mill and stops (in-game 4-cross). Personality
`UnderCountLimit` is a total farm floor, not an 8-neighbour layout.
Hybrid `Place.FillRing` knew the 8-ring but `cppOwnsScan` skips
`Place.Audit` while `AOE4HOOK_ECO_CPP=true`.

Overlay **fills the gaps**. Relic still decides *when* farms are worth it
(`relic_no_farm_yet` until one own farm exists — that farm is the civ ebp).

## Anchors (not mill-only)

Catalog is `land_food_deposit_*` in
`Documents\AOE4HSettings\NativeEspData\unit_intelligence.scar` plus aoe4world
"drop off Food / all resources". Live radar names are Relic blueprints
(`building_town_center_eng`); HUD / slugs drop the underscore (`towncenter`,
`town-center`). `AiFarmNameHasI` now skips `_` and `-`.

| Kind | Footprint | Aura | Examples |
|------|-----------|------|----------|
| Mill | 2x2, pitch 8 | none | mill / `food_control` / farmhouse / ger / hunting cabin |
| Granary | 4x4, pitch 12 | Irrigated Field **30** world (`building_granary_aura_chi`) | CHI / ZX granary |
| Town center | 4x4, pitch 12 | none | every civ TC / capital, `towncenter` HUD name |
| Landmark | 4x4, pitch 12 | Winery **25** | Aachen, Kura, Grand Winery, High Trade House, King's Palace, Palace of Swabia, HRE (not OotD) Regnitz + monastery, Sena Matsuri |
| Manor | live occ. (default 2x2) | unknown | Lancaster manor (no `land_food_deposit` type; aoe4world all-resource) |

**Not** anchors (data has no food deposit): Kremlin, cistern, village,
Abbey of Kings, House of Wisdom, mosque, ovoo, pasture, cattle ranch,
OotD monastery, OotD Regnitz (`bamberg`/`regnitz` + `ha_01`).

Docks drop fish — not farm-ring centers.

## Commit path (was the live bug)

`AiPlannerUpdate` already called `AiFarmLayoutOnPlannerWorld`. Peek/mark
were `/OPT:REF`-kept but **never called**. `HandleAiCommitPosted` only
peeked the actuator; `TickCounter` only posted when the actuator was dirty.

Now:

1. `AiFarmLayoutAppendPending` appends `__EcoFarm` onto the same DoString
   as `__EcoAct` (`eco_ai_cuts`), or runs `eco_farm_ring` alone.
2. `TickCounter` also `PostAiCommit` when farm pending.
3. Counters-off + eco live still posts (farm-only apply; does **not**
   Restore the actuator).
4. Handover / disable / VM reset call `AiFarmLayoutReset()`.

Do **not** `PostMessage(WM_SCAR_AI_COMMIT)` from `ai_farm_layout.cpp` —
counters-off Restore would fire if the handler forgot to peek farm first.

Natives (Essence, not Cardinal-only): `Player_CanPlaceStructureOnPosition`,
`LocalCommand_PlayerSquadConstructBuilding`. Not `Player_CanConstructOnPosition`,
not hybrid `Cmd_Construct`.

## Overlap

TC + mill (or two mills) can request the same world cell. `AiFarmPlanSlots`
skips a candidate that overlaps an already-planned plot (centre distance
< 0.9 × farm width).

## Tests / build

`tests/adversarial/test_ai_farm_layout.cpp` — slugs, Kremlin/OotD negatives,
colocated-mill de-dupe. Build `Release|x64` →
`AOE4HOOK\internal\x64\Release\`.

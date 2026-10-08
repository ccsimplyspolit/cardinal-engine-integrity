# 2026-09-07 — aoe4world 0.0.2 catalog vs overlay fallbacks

Packed `unit_intelligence.scar` is primary. `k*` tables in `ai_combat.cpp` and
`kBuildingRu` in `unit_profile.cpp` are attrib-miss only. Combat lives in
`ai_combat.cpp` + `unit_profile.cpp` (no `ai_catalog_combat.*`). Skipped
`ai_eco_goal.h` (Jeanne villager 20s already verified). No RA ritual change.

## Applied

- Default civ `"eng"` → `"en"` (`ai_production.cpp`). Catalog civs use `en`.
  Empty civ + `CivTokenHas("eng")` made all seven families look untrainable.
- English-line `k*` fallbacks aligned to catalog English / Longbowman
  (`unit_archer_%d_eng`). Age-1 spear is Abbasid generic (English has no
  `unit_spearman_1_eng`). Age-1 archer stays generic (no English longbow).
- `FillBuilding` HP vs exact baseId: siege_workshop 2100, market 1000,
  keep 5000, farm 300, dock 1750, palisade 1350, wall_tower 3000, ger 1000.
  House 750 stays (non-Mali). Mali house 550 not special-cased (`FillBuilding`
  has no civ).
- Onna-Bugeisha `ApplyUnique` vsCav +10 removed (catalog 0).
- Overlay SCAR: `FOW_ExploreAll` → `FOW_PlayerExploreAll(player)`;
  `FOW_UIRevealAllEntities` → type-guarded `FOW_UIRevealAll`; keep
  `FOW_UIRevealAll_Transition`. Blips: `UI_CreateMinimapBlipOnPosFrom`.
- `stk_army_name.h`: silent needles `warriormonk` / `tradecart` / `merchant` /
  `fishing_ship` documented; live names already present.

## Left unfixed (safe skip)

- **kSiege**: matches no real siege unit. Comment only; do not pretend one row
  is ram+mangonel+springald.
- **mamluk range 3.5→4.5**: catalog Desert Raider (`unit_mamluk_*`) is melee
  ~0.29, not 4.5. Age-blind change would worsen other civs.
- **grenadier vsSiege +15**: catalog bonus is vs building. No vs-building field;
  do not flatten.
- **musofadi / javelin / sipahi / landsknecht / janissary / kipchak speed**:
  age-varying; do not flatten.
- **Gather rates / heal**: not in this catalog pass; unverifiable here.
- **RVA values**: no contradictions. Comment nits only:
  `known.h` EntityManager `sub_7FF6F69BC3C0` is RVA `0x3FC3C0`, not
  GetEntityManager `0x1909A10`. `kRelTableHandleRva` **is** sim-world enc
  `0x84942F0` (not reader `0xA64D80`). Do not retarget `kFowExploreAll`
  `0x1ABE220` to `FOW_PlayerExploreAll` `0x1ABE4D0`.

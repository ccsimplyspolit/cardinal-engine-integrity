# 2026-09-06 — Build-order Layer B wiring

Cloak off. Sibling import (`2026-09-06-build-order-import.md`) left Layer B
unwired. This change floors BO gatherer/income into `AiEcoComputeDesire` and
applies only through existing `__EcoAct_Apply`. Family cuts stay
`ai_counter_math`. Vs humans = OOS (sim-write). Keep `scar_trust`.

## Load / resolve

| When | What |
|------|------|
| `AiSessionSetEnabled(true)` | `AiBuildOrderStoreLoadIndex` reads `Documents\AOE4HSettings\BuildOrders\index.json` |
| Session on + each service tick | `AiBuildOrderStoreTickBind` → `BuildOrderPickSlug` (highest `score`) → parse `<civ>/<slug>.json` |
| Collect worker next to `AiEcoComputeDesire` | `BuildOrderResolve` on the cached `BuildOrderDoc` (snapshot only, no disk, no natives) |

Civ folder = overlay slug (`english`) via `BuildOrderCivSlug`. `od` maps to
`order_of_the_dragon` (UiCivIconKey maps `od` to Macedonian — wrong folder).
No preferred-slug config (`config.cpp` is another owner). 47 unresolved
unique-civ names stay `unresolved`; no invented attribs.

## Blend (do not replace)

`AiEcoBlendBuildOrder` (header, no file I/O):

- Floor `gFood…` from `gatherer*` then renormalize. Floor `food…` from
  `income*`. **Do not** alias `incomeFood` → `gFood`.
- Skip gatherer/income floors when Fine-tune apply owns that slice, or
  unmet Fast Age/TC (`goalActive`), or `ecoLock`, or `mass_army`.
- `desiredTcCount` → `__EcoAct.tc`, cap `userMaxTc`. Fast TC (`kAiEcoFastTcTarget = 2`) still wins.
- `ageUpPush` floors `iAge` unless Fine-tune intentions / `mass_army` /
  unmet Fast Age. Landmark attrib is HUD / placement hint only.
- Does not write `AiCounterCuts`, `ecoLock`, or `openingPhase`. A boom BO
  cannot unlock ecoLock military. `ApplyIntelCuts` still returns early on
  `ecoLock`.

Apply path is unchanged: worker desire → `AiEcoDesireKey` → lean
`__EcoAct_Apply` Layer B natives (income / gatherer / intentions / `tc`).

## HUD / counter-plan

`hudStepRu` + slug + landmark attrib on Scoring observatory and AI BOT
(next to enemy-intel `hudRu`). `nextTrainAttrib` is HUD only — not a
family unlock.

## Tests / build

- Host: `tests\adversarial\build_ai_build_order.cmd` (parse, resolve, picker,
  blend floors, ecoLock skip, Fast TC wins, userMaxTc, Fine-tune skip,
  no income→gatherer alias).
- Host: `test_ai_production_math.cpp` (ecoLock gatherer unchanged; Fast TC
  maxTc=2 vs BO tc=6).
- Host: `build_ai_build_order.cmd` + `build_ai_math.cmd` — all ok.
- `InternalInjector` **Release\|x64** → `AOE4HOOK\internal\x64\Release\InternalInjector.dll`
  (16:58:30, no LNK1104). Cloak off. No `mp_bypass` / `xbox_enforcement` / winhttp / hide edits.

## Files

- `ai_build_order.h` — `AiEcoBlendBuildOrder`, `BuildOrderCivSlug`
- `ai_build_order_store.h/.cpp` — window-thread I/O + cache
- `ai_production_math.h` — blend after goal / opening, before hoard
- `ai_runtime.cpp` / `ai_session.cpp` / `ai_production.cpp`
- observatory + radar HUD
- `docs/BUILD_ORDERS.md`

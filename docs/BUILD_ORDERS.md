# Build orders (Layer B wired)

Offline JSON under `Documents\AOE4HSettings\BuildOrders\<civ>\<slug>.json`.
Refresh: `python AOE4HOOK\tools\fetch_build_orders.py`.

This module **thinks** in C++ (`ai_build_order.h`) and **acts** through existing
`__EcoAct_Apply` Layer B natives. It is **not** a second trainer. Family cuts
stay in `ai_counter_math` — a boom BO does not unlock ecoLock military.

## Sources, limits, attribution

| Source | What we take | Auth | Limits | Credit |
|--------|----------------|------|--------|--------|
| [aoe4guides API](https://aoe4guides.com/api/api-docs/) | Top ~5 overlay BOs per civ (`orderBy=score&overlay=true`) | none | List returns **≤10**, no pagination. **30/min + 300/hour** lists, **120/min + 1200/hour** `/builds/{id}`. Honour `Cache-Control` (lists ≤60s, ids ≤5min). `429` + `RateLimit` / `Retry-After`. | **Credit and link** [aoe4guides.com](https://aoe4guides.com). Do not enumerate the corpus. Bulk: info@aoe4guides.com / [Discord](https://discord.gg/Nau9BN5E7J). API MIT ([jensbuehl/aoe4-guides-api](https://github.com/jensbuehl/aoe4-guides-api)). Frontend: [jensbuehl/aoe4-guides](https://github.com/jensbuehl/aoe4-guides). |
| Canonical API host | `https://aoe4-guides-api-7h2vti5ckq-ey.a.run.app` | | `aoe4guides.com/api` is a thin site proxy (most routes 404). Prefer Cloud Run. | |
| [aoe4world/data](https://github.com/aoe4world/data) CDN [data.aoe4world.com](https://data.aoe4world.com) | `attribName` for overlay `@building_…/house.webp@` slugs | none | Static JSON. Cache hours. | [Game Content Usage Rules](https://www.xbox.com/en-US/developers/rules). Explorer: [aoe4world/explorer](https://github.com/aoe4world/explorer). |
| Curated | One 2TC-style boom per civ, `source: "curated"` | — | Always written. Used when the network fails. Templar ages at HQ (commanderie), not a landmark. | Overlay author; still Microsoft ©. |

Age of Empires IV © Microsoft Corporation. Not affiliated.

Fair-use numbers live in `tsoa.json` `spec.description` on the API repo (canonical copy also rendered at [aoe4guides.com/apidoc](https://aoe4guides.com/apidoc)).

## On-disk schema

```json
{
  "schema": 1,
  "civ": "english",
  "slug": "curated-boom",
  "source": "curated",
  "steps": [
    {
      "time_s": 0,
      "villagers": 6,
      "age": 1,
      "gather": {"food": 6, "wood": 0, "gold": 0, "stone": 0,
                 "food_frac": 1.0, "wood_frac": 0.0, "gold_frac": 0.0, "stone_frac": 0.0},
      "build": [{"attrib": "building_house_control_eng", "unresolved": null}],
      "research": [],
      "age_up": null,
      "train": [],
      "note": "6 on sheep, house"
    }
  ]
}
```

`gather` values are **villager counts** on the step plus `*_frac` (already
normalized). Resolve still normalizes from the counts. `unresolved` is the
aoe4guides / aoe4world slug when Relic `attribName` is unknown.

`index.json` lists every civ. aoe4guides rows carry `author`, `score`, `likes`,
`views`, `season`, `rank` (1 = top of `orderBy=score`). Overlay JSON has no
score — the tool merges the catalog list (`/builds?orderBy=score`) onto the
overlay list (`overlay=true`). `BuildOrderPickSlug` reads this index.

## C++ API (`BuildOrderTargets`)

Host-testable. Header has **no** Windows / Lua / Relic natives.

`BuildOrderParse(json, &doc)` then `BuildOrderResolve(doc, input)`.

`BuildOrderPickSlug(indexJson, civ, preferredSlug, out, cap)` — no file I/O.
preferredSlug wins if that civ lists it; else highest `score`; else first
`aoe4guides` row; else `curated-boom`. The store no longer uses the fallbacks:

`BuildOrderPickUserSlug(indexJson, civ, preferredSlug, out, cap)` — the user's
choice (AI BOT → Build Order, `AiSettingsBuildOrderSlug`) only. An empty choice
or a slug this civ does not list binds **nothing**; the AI plans the economy
itself (2026-09-27, user decision: the automatic top-score guide bound rush
guides that describe only the Dark and Feudal Ages).

**Played out.** `BuildOrderTargets::finished` is set when the player is past
the guide's last age, or on the last step `kBuildOrderDoneGraceSec` (90 s) past
its time / `kBuildOrderDoneExtraVillagers` (5) past its villagers.
`BuildOrderTargetsLive` is then false: no blend, no TC ceiling, no age push, HUD
"build order done, the AI decides". `PickStep` used to hold the last step for
the rest of the match. Strict following is not the aim — a guide floors the
eco plan, it is not a script.

`currentAge` is the player's age (the engine's, see `ai_engine_age.h`), not the
step's: a guide held on a Feudal step priced Castle / Imperial incomes as
Feudal.

Names are the **EcoGoalPlan** contract. Copy them. `AiEcoDesire` uses shorter
aliases only on the apply struct — do not mix them in the BO module.

| BuildOrderTargets / AiEcoGoalPlan | AiEcoDesire (apply) | Relic / overlay sink (when wired) |
|-----------------------------------|---------------------|-----------------------------------|
| `gathererFood` | `gFood` | `AIPlayer_SetGathererDistributionOverride` |
| `gathererWood` | `gWood` | same |
| `gathererGold` | `gGold` | same |
| `gathererStone` | `gStone` | same |
| `incomeFood` | `food` | `AI_SetResourceIncomeDesire` (per-minute desire, not stock) |
| `incomeWood` | `wood` | same |
| `incomeGold` | `gold` | same |
| `incomeStone` | `stone` | same |
| `ageUpPush` | `iAge` | `AIPlayer_SetStrategicBaseIntention` key `"age_up"` (floor) |
| `desiredTcCount` | `maxTc` | `__EcoAct.tc` (ExpansionTC). May raise the ceiling, never lower it. Fast TC (2) still wins |
| `ageUpLandmarkAttrib` | — | HUD / placement hint. Relic still scores the landmark. |
| `nextBuildingAttrib[]` | — | HUD / future ExpansionTC hint — **not** a `ScoringFunctions_*` list |
| `nextResearchAttrib[]` `nextTrainAttrib[]` | — | HUD only until Layer A is designed |
| `hudStepRu` `hudStepEn` | — | AI BOT / radar HUD (`hudStepRu` is the Russian UI string; unrelated to Rus civ) |

`income*` Dark→Imperial rows match `AiEcoComputeDesire` `{520,280,220,0}` …
scaled by `0.35 + 0.65 * gatherer*`. `AiEcoBlendBuildOrder` floors
`AiEcoDesire.food` with `incomeFood` the same way `AiEcoGoalPlan` already
floors it. **Do not** copy `incomeFood` into `gFood`.

`gatherer*` always sums to 1. Overlay `@town-center@` icons are often rally
hints; `desiredTcCount` is 2 when any step mentions a TC, not `1 + mention count`.

## Wiring (2026-09-06)

1. **Load** — only with a chosen guide: `AiBuildOrderStoreBindCiv` returns before reading anything when `AiSettingsBuildOrderSlug()` is empty. Then `AiBuildOrderStoreLoadIndex`, `BuildOrderPickUserSlug`, `BuildOrders\<civ>\<slug>.json`. A different choice mid-match unbinds at the next `AiBuildOrderStoreTickBind`. Cache `BuildOrderDoc`. Civ key = overlay slug (`english`) via `BuildOrderCivSlug` (`od` → `order_of_the_dragon`, not UiCivIconKey's Macedonian).
2. **Resolve** — collect worker next to `AiEcoComputeDesire`. Snapshot only. No Relic natives.
3. **Blend, do not replace** — `AiEcoBlendBuildOrder` floors `gatherer*` → `gFood`… and `income*` → `food`… **before** `AiEcoDesireKey`. Fine-tune apply flags / unmet Fast Age-or-TC / `ecoLock` / `mass_army` skip those floors, and so does the eco plan's own split (`planOwnsGather`: the Dark Age and the second-TC window). Steps are parsed from notes — "build the 2nd TC with 8 wood villagers" becomes wood 0 — and max-then-renormalize turned those zeros into a quarter of the intended wood (live Ayyubid 2026-09-26: 0–4 of 14–20 villagers on wood for 8 minutes).
4. **Apply** — existing `__EcoAct_Apply` Layer B natives only.
5. **TC count** — `desiredTcCount` → `__EcoAct.tc`, raise-only, cap `userMaxTc`. Fast TC (`kAiEcoFastTcTarget = 2`) still wins. `BuildOrderResolve` reports the current TC count for a guide that never mentions one, and every auto-picked rush guide then capped the match at one TC (`tc=1` on every `eco_goal` line of 2026-09-27); the guide no longer lowers the ceiling.
6. **Age-up** — `ageUpPush` floors `iAge`. `ageUpLandmarkAttrib` is HUD / placement hint.
7. **HUD** — `hudStepRu` on Scoring observatory and AI BOT. Not Rus civ.
8. **Cuts** — `ai_counter_math` only. Boom BO does not unlock ecoLock military. `ApplyIntelCuts` still returns early on `ecoLock`.
9. **Safe / MP** — Layer B is sim-write. Keep `scar_trust`. Vs humans = OOS.
10. **Tests** — `test_ai_build_order.cpp` (blend) + `test_ai_production_math.cpp` (ecoLock / Fast TC). No JSON I/O in the header. File I/O is `ai_build_order_store.cpp`.

Host test: `AOE4HOOK/tests/adversarial/test_ai_build_order.cpp` (embedded fixture).
`AOE4HOOK/tests/adversarial/build_ai_build_order.cmd`.
# Reviewed opening execution (2026-09-28)

Ordinary imported guides remain advisory. An explicitly reviewed profile in
`tools/build_order_profiles/<aoe4guides-id>.json` adds `execution: "opening"`,
`complete_tcs`, and per-step `town_centers`, `requires_tcs` and
`requires_age_up`. Time and villager thresholds are both checked in order;
completed TCs, not foundations, unlock the next economy. The final completed
TC releases the opening immediately. Advancing beyond the guide's age also
releases it. A delayed opening does not expire just because its target time
passed.

The first profile is [Skimsh's Ayyubids 6mins 3TC](https://aoe4guides.com/builds/EkAZJeiSviH0eiIW3BxU).
It uses Culture Advancement (`upgrade_add_culture_wing_dark_a_abb_ha_01`),
verified at 200 food / 100 gold / 96 seconds in 16.3.11308 attributes. The
production scorer filters competing Dark wings and overrides the selected
wing's random veto while retaining affordability and age intention scoring.
It does not directly enqueue research. TC targets carry a local production
gate, count limit, priority and reserve; a target of three is more than a HUD
label or an increase of the general ceiling.

Gather allocations retain the wood workers represented as builders in the
source until Relic takes them to construction; zero wood in those source rows
must not empty the wood economy before the TC can be funded. The reviewed
opening takes precedence over automatic economy/counter splits. Base defence,
manual fine tuning, explicit Fast Age/Fast TC/Mass/Workers modes and a lower
user TC cap take precedence over execution. The selected guide's filename
and catalog entry do not change. Refresh reapplies the profile for this ID
and civilization; it does not infer executable objectives from arbitrary notes.

This is an adaptive opening, not an exact reproduction of every scout route,
straggler-tree assignment or force-drop click. Six minutes is the source's
target, not a measured completion guarantee. New behavior is host-tested;
an actual game remains to be verified.

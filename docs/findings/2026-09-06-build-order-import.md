# 2026-09-06 — Build-order import + C++ data module

Offline JSON in `Documents\AOE4HSettings\BuildOrders`. Tool:
`python AOE4HOOK\tools\fetch_build_orders.py`. C++: `ai_build_order.h/.cpp`.
**Not wired** into Layer B / `ai_runtime.cpp` / `ai_session.cpp`. Cloak off.

## Sources

| Source | What we take | Auth | Limits | Credit |
|--------|----------------|------|--------|--------|
| aoe4guides Cloud Run `aoe4-guides-api-7h2vti5ckq-ey.a.run.app` | Top 5 overlay BOs per civ (`orderBy=score&overlay=true`) | none | List ≤10, no pagination. 30/min + 300/hour lists, 120/min + 1200/hour `/builds/{id}`. Honour Cache-Control. | Credit **and** link [aoe4guides.com](https://aoe4guides.com). Do not crawl the corpus. |
| aoe4guides.com/api | Site proxy; most routes 404 | — | Last resort only | same |
| Catalog list (no `overlay`) | `score` / `likes` / `views` / author | none | Same list cap. Overlay JSON has **no** score. | same |
| [aoe4world/data](https://github.com/aoe4world/data) CDN | `attribName` via id / baseId / icon stem | none | Static JSON, cache hours | Xbox Game Content Usage Rules |
| Curated | One 2TC-style boom per civ | — | Offline `--offline` | Overlay author; still Microsoft © |

Age of Empires IV © Microsoft Corporation. Not affiliated.

Overlay step payload: `time`, `villager_count`, `resources.{food,wood,gold,stone}`, `age`, `notes[]` with `@folder/slug.webp@` icons. Site catalog `steps` strip those icons — do not convert from the catalog list.

## Fetch (this run)

`generated_utc` 2026-09-06T13:47:10Z. 23 civs.

| | Count |
|--|--|
| aoe4guides (top 5 / civ) | 115 |
| curated-boom | 23 |
| mapped attrib items | 2655 |
| unresolved items | 47 (was 153 before alias / icon-stem pass) |
| aoe4world keys | 2233 |

Leftover unresolved is civ-unique icon names missing from aoe4world/data (`towara-1`, Golden Horde tent carts, `imperial-examination`, `arrow-slits`, Tughlaq fort tiers). Kept as `unresolved` — do not invent attribs.

English #1 (score 7.91, Munchy, 7 likes): `english\2tc-white-tower-2026-copy-made-it-more-clear-wha-qmulvdvx.json`.

## C++ module (`BuildOrderTargets`)

Host-testable. No Windows / Lua / Relic natives.

| Call | Role |
|------|------|
| `BuildOrderParse` | Schema-1 JSON → `BuildOrderDoc` |
| `BuildOrderResolve` | time/vills/age/TC census → gatherer* (sum 1), income* (`kRow` Dark..Imp × 0.35+0.65×gatherer), `ageUpPush`, `desiredTcCount`, next attribs, HUD |
| `BuildOrderPickSlug` | index.json → slug (preferred, else highest `score`, else first aoe4guides, else curated-boom) |

Field names match `AiEcoGoalPlan`. Do not alias `incomeFood` → `gFood`.

## Deliberately not done

Layer B apply / `__EcoAct.tc` / Fine-tune blend. Config.ini preferred-slug key (`config.cpp` is another owner). Wiring plan stays in [BUILD_ORDERS.md](../BUILD_ORDERS.md).

## Verify

- Host: `tests\adversarial\build_ai_build_order.cmd` — all ok (parse, resolve, picker).
- Network fetch as above.
- `InternalInjector` **Release\|x64** → `AOE4HOOK\internal\x64\Release\InternalInjector.dll` (obj 16:44:59, dll 16:45:04). Cloak off. No `ai_runtime.cpp` / `mp_bypass.cpp` edits.

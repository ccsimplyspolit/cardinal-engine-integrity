# 2026-09-07 — полный уход от SCAR (разбор, не патч)

Инвентарь поверхностей: [scar-overlay-inventory](2026-09-07-scar-overlay-inventory.md).
Native AI: [native-ai-cpp](2026-09-07-native-ai-cpp.md). Канон слоёв: `AI_CONTROL_OWNERSHIP.md`, ADR-001.

«Уйти от SCAR» смешивает три разные вещи. Их нельзя закрыть одним решением.

## Три объекта

| # | Что имеют в виду | Реально? |
|---|---|---|
| 1 | Relic больше не крутит Lua | **Нет.** `Scenario Lua System` — загрузка миссии, bags, `ScoringFunctions_*` callback, Relic `Rule_*`. Это игра, не оверлей. |
| 2 | Продукт без Files / hybrid / `.scar` | Только если сознательно режем вкладки. Пользовательский SCAR — фича, не долг. |
| 3 | AI BOT без `Game_ScarDoString` `0xAA9B00` | Исследование. Think уже без SCAR. Act — нет. |

Дальше только **#3**, с оговоркой что #1 остаётся всегда, #2 — отдельно.

## Почему DoString вообще нужен

`ScarDoString` = compile строки + `lua_pcall` на **оконном** tid. Нативы — `lua_CFunction`: они снимают **userdata** (`PlayerID`, `SquadID`, `SGroup`), не сырые ptr из RPM.

Без Lua-стека C++ должен сам:

- достать `SimPlayer*` / `AIPlayer*` (`kAiPlayerList` читается, Control inner — нет в продукте);
- собрать **SGroup** как Relic-объект (не `{id…}` из радара);
- попасть в TLS окна **или** очередь AI tid `0x2922980`;
- для Layer A — либо оставить Lua-хуки, либо заменить director.

`pcall` не ловит AV. Неверный userdata / tid = тот же 4A70 / `0x1ED5529`.

## Стена Layer A (этого не обойти poke)

Relic production director **каждый** кандидат зовёт `_G.ScoringFunctions_*` → список factory → C++ `Evaluate` (`0x2D03940` …). Context: `*(AI+0x3EA0)+0x94`.

- RPM списков score **не** заменяет callback.
- `kEcoScoring` живёт потому что Relic `PlayerGatheringUpgrade` Evaluate `0x2D00120` даёт **0** (horticulture мёртв).
- Availability (`Player_SetSquadProductionAvailability`) режет семьи, **не** чинит gather-native.
- `LuaScoringFunction` per-candidate — всё ещё Lua, даже если тело O(1).

Без Lua на Layer A остаются только:

- **T** — выключить Relic trainer, сами `LocalCommand` train/build/research (второй director, ADR-001 B);
- патч Evaluate / hook table в `.text` (версия, RA, не продукт).

## Четыре траектории (не смешивать)

### L — тот же VM, без compile

Найти `lua_State` окна, `lua_getglobal` + `lua_pcall` нативов. Нет parse 40–52 ms.

Всё ещё SCAR. Relic state не экспортирует. `debug` вырезан. Фаза 2 `lua_tocfunction` — каталог RVA, не director. Enable с Present всё равно нельзя (TLS).

### M — BOT без DoString, Relic trainer жив

Inners на AI/window tid: Enable `0x2975660`, Lock `0x296D2E0` (до Enable), Layer B (`PushScore` `0x29C8A60` …), availability, gather `LocalCommand` если снять SGroup ABI.

`kEcoScoring` **не** ставим. Eco-апгрейды: C++ сам ресерит, или живём с нулём Relic.

Files / hybrid / world-feed **остаются** SCAR. Vs humans = OOS как сейчас.

Это максимум «ухода» без второго trainer.

### T — второй trainer, Relic AI off

`AI_Enable` false / нет слота. C++ `LocalCommand` + macro SendInput. Scoring не нужен.

Полный уход BOT от Relic-Lua **и** от Relic-AI. Цена: весь command ABI, pathing, queue, ages. Vs humans — только SendInput (`prod_macro` engine=0 уже). Offline — OOS не важен.

ADR-001 отверг это как продукт.

### Z — ноль overlay-DoString во всём процессе

M или T **плюс** вырезать Files, hybrid, probe, Debug HUD, Offline spawn, world-feed, `AOE4HOOK_Local.Pump`.

Relic Lua миссии всё равно живёт (#1). Это смена продукта, не оптимизация.

## Что уже не SCAR

Radar/ESP/FoW диски, FOWCTRL1, lobby Memory, AICTLR01 slab, collect/planner/runtime, observatory, macro SendInput.

## Честный потолок

Полный уход = Z + чтобы Relic не грузил Scenario Lua. Этого нет.

Практический потолок BOT: **M** (inners + дефолтный Relic scoring + C++ research на мёртвые eco-техи) **или** **T** (свой trainer).  
Сейчас мы в гибриде: C++ think + DoString act + Lua Layer A. Самый жирный DoString — `kEcoScoring` с Present (`SendMessage`).

Не начинать M/T, пока Enable не уйдёт с Present (`PostMessage`). Иначе новый ABI сядет на тот же hitch.

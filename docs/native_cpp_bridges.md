# Мосты оверлея для автора SCAR

Документ для человека, который пишет `.scar` / `.lua` под AOE4HOOK и **не видит исходников DLL**.  
Игра: Age of Empires IV **16.3.11308.0**. Схема snapshot: **10**. Метка: `16.3.11308.bridge12`. Lua **5.3** (песочница: нет `io` / `os`, см. LUA_RUNTIME.md).

Оверлей кладёт данные в тот же Relic SCAR VM, куда попадает ваш файл. Вы читаете `_G`, вызываете обычные нативы Relic и (если нужно) helpers `AOE4HOOK.*` / `SpatialWorldModel.*` / `MacroBridge.*`.

Плагины живут только здесь:

`Documents\AOE4HSettings`

Типичный путь: `C:\Users\<you>\Documents\AOE4HSettings`

---

## Оглавление

1. [Что оверлей делает за вас](#1-что-оверлей-делает-за-вас)
2. [Куда класть файлы](#2-куда-класть-файлы)
3. [Как грузится ваш скрипт](#3-как-грузится-ваш-скрипт)
4. [AV / OOS факты](#4-av--oos-факты)
5. [Три вида ID](#5-три-вида-id)
6. [Когда данные живые](#6-когда-данные-живые)
7. [Глобалы snapshot (полный словарь)](#7-глобалы-snapshot-полный-словарь)
8. [API `AOE4HOOK.*`](#8-api-aoe4hook)
9. [`AOE4HOOK_AI_PLAN`](#9-aoe4hook_ai_plan)
10. [`AOE4HOOK_AI_SETTINGS` и профили](#10-aoe4hook_ai_settings-и-профили) — вкладка **AI BOT**: [`docs/AI_BOT.md`](ai_bot.md)
11. [`SpatialWorldModel` и `UnitIntelligence`](#11-spatialworldmodel-и-unitintelligence)
12. [`MacroBridge` — очередь / cancel](#12-macrobridge--очередь--cancel)
13. [Обёртки `AOE4HOOK_Local` / `AOE4HOOK_Safe`](#13-обёртки-aoe4hook_local--aoe4hook_safe)
14. [Рецепты](#14-рецепты)
15. [Проверка без исходников](#15-проверка-без-исходников)
16. [Что попросить у владельца оверлея](#16-что-попросить-у-владельца-оверлея)

---

## 1. Что оверлей делает за вас

C++ **не** играет за вас и **не** ищет копейщиков. Он:

1. собирает кэш мира (тот же EntityManager, что Radar/ESP);
2. по тумблерам вкладки **Scripts → Send Data to Scar** отбирает строки;
3. раз в N секунд (ползунок) перезаписывает глобалы `_G.AOE4HOOK_*`.

Дальше ваш `.scar` читает массивы. Счётчики — `AOE4HOOK_CENSUS.players[id].by` / `.army`. Позиции — `AOE4HOOK_WORLD_DATA.entities` (`n` = имя, `k` = тип, `p` = xyz, `o` = Player_GetID).

| Канал | Откуда в Lua | Пишет симуляцию? | Зачем вам |
|---|---|---|---|
| **Send Data to Scar** | Present: присваивает `_G.AOE4HOOK_*` (и хвост `Pump`) | Нет | Мир, census, опционально PLAN |
| **Macro-bridge** | Вкладка Macro / ваш `pcall(MacroBridge.…)` | Да (очередь) | Train/cancel без клавиш |
| **Ваш файл** | Files / AUTO / вкладка Offline | Как напишете | Игровая логика |

World-feed по умолчанию **выключен**. Пока не включён **Send to SCAR**, снимка нет. Hybrid AUTO **не** публикует данные — только грузит скрипт. `AOE4HOOK_AI_SETTINGS` пишется **каждый** snapshot (holds/profile). `AOE4HOOK_AI_PLAN` — только если включён тумблер AI plan. Hybrid дополнительно получает SETTINGS на Load.

Шлите только нужные типы. Полный dump (все виды, census-all, cap 8192) — это `ScarDoString` на десятки КБ и просадка FPS. Кнопка **Lean snapshot** на вкладке Send.

---

## 2. Куда класть файлы

Корень: `Documents\AOE4HSettings`.

| Папка | Для вас |
|---|---|
| `Scar Scripts\` | Ваши `.scar`. Появляются как Run на вкладке Files. **AUTO** — только если включили на строке. |
| `Scar Scripts\` подпапки | Можно. Не кладите в `System`, `_system`, `Menu`, `ScarToolkit` — Files их не показывает и не запускает как пользовательские. |
| `Lua Scripts\` | `.lua` в ту же VM. |
| `NativeEspData\` | **Не трогать**, не дублировать. Оверлей грузит отсюда `unit_intelligence.scar`, `spatial_world_model.scar`, `aoe4hook_bridge.scar` сам, один раз на матч, **до** вашего файла. |
| `Scar Scripts\System\` | `local_rules.scar`, `checksum_wrappers.scar` — prepend оверлея, не Files. Не кладите сюда свой ИИ. |
| `Scar Scripts\_system\_auto\` | Скрыто. hybrid_o / hybrid_c. Не кладите свой файл с именем `*hybrid*` рядом, если не хотите mutex с hybrid. |
| `Scar Scripts\_system\_menu\Offline\Macro\` | `macro_bridge.scar`. Скрыто. Не копируйте в Files. |

Лимиты вашего файла:

- максимум **2 MiB**;
- нет байта `NUL`;
- UTF-8; BOM срежется;
- расширение `.scar` или `.lua`;
- без `..` и абсолютных путей в имени.

Не воссоздавайте `AOE4HOOK\plugins`, `Documents\ScarScripts`.

Не вызывайте `TimeRule_RemoveAll` / массовый `Rule_RemoveAll` в оверлейном файле — снесёте Pump и чужие interval.

Имена `hybrid`, `hybrid_o`, `hybrid_c`, `hybrid_core` заняты. Один hybrid на VM: `hybrid_c` и `hybrid_o*` вместе грузить нельзя.

---

## 3. Как грузится ваш скрипт

1. Матч начался, Relic Lua жива (state 3). Оверлей ждёт ещё **~2 с** (`classic_start` PostInit). Раньше Files пишет «enter a match».
2. Первый `.scar` с Files (или AUTO): bootstrap NativeEspData, **один раз** на эту VM:
   1. `scar_natives_live.scar` (если есть)
   2. `unit_intelligence.scar` (**нужен**)
   3. `AOE4HOOK_WORLD_FILTER={prefer=true, nativeFeedTtl=…}`
   4. `aoe4hook_bridge.scar` (если есть) → таблица `AOE4HOOK`
   5. `spatial_world_model.scar` (**нужен**)
3. Ваш текст оборачивается: `local_rules` + checksum catalog (один раз) + `pcall` + `Pump`.
4. World-feed (если Send to SCAR) независимо по ползунку перезаписывает `_G.AOE4HOOK_*`.

Если файл называется `hybrid_o*.scar`, оверлей **перед** ядром вставляет:

```lua
AOE4HOOK_HYBRID_FILE_PROFILE = 'offline' | 'risk' | 'safe'
AOE4HOOK_AI_SETTINGS = { ... }   -- снимок Online / Offline → AI на момент Load
-- затем System\hybrid_core.scar
-- затем ваш стаб
```

`hybrid_c.scar` получает только блок SETTINGS в начале.

Ваш обычный файл SETTINGS на Load **не** получает. Читайте `_G` после Publish или на своём interval.

`AOE4HOOK.BindFeed()` вызывается самим snapshot. Повторно звать безопасно.

---

## 4. AV / OOS факты

- **`Entity_GetPlayerOwner` / `Entity_GetPlayer` на строке радара.** Строка — Lua-таблица с `id`/`o`/`p`, не Relic userdata. Натив по ней AV. Владелец: `row.o` / `AOE4HOOK.Owner(id)` / `AOE4HOOK_GetPlayerOwner(id)`.
- **Не ждать userdata из feed.** `id` — число native entity id. Handle: `Entity_FromID` / `Entity_FromId` / `Squad_FromId` в `pcall`.
- **Не считать `inc` доходом движка.** Это `работники × фиксированные aoe4world rates`. `Player_GetResourceRate` в этой сборке часто 0.
- **Не звать `AIProductionScoring_*` с `Rule_AddInterval`.** Нужен Relic production scoring context. Иначе throw. `ida_ok=1` в SETTINGS ≠ «натив есть в `_G`».
- **`AIPlayer_PushScoreMultiplier` — не train cap.** Это target/military scoring. Lua-hold 0 (не заказывать тип) — другая система.
- **Sim-write vs человек = OOS**, если не договорились с владельцем (Allow OOS / профиль risk). Safe hybrid и SendInput симуляцию через нативы не пишут.
- **Не ставить `AOE4HOOK_MP_SAFE = false` насовсем.** Обёртки тогда пустят FOW/sim. Для одного вызова — как `macro_bridge`: сохранить, сбросить, вызвать orig, вернуть.
- Камеру / world-to-screen из feed **не** кормить в sim-команды как истину lockstep.

---

## 5. Три вида ID

| Что | Как выглядит | Где в feed | Как получить Relic-объект |
|---|---|---|---|
| **Player_GetID** | обычно 1000…2999 (не 1…8 слота лобби) | `row.o`, `AOE4HOOK_LOCAL_ID`, ключи `CENSUS.players`, `STOCKS`, `PLAN.lock` / `eco` | `World_GetPlayerAt` **не** равен этому числу. Ищите игрока циклом `Player_GetID(p)==id` или берите `Game_GetLocalPlayer` для локального |
| **native entity id** | uint32 | `row.id`, `PLAN.lock[pid]={id,…}` | `pcall(Entity_FromID, id)` (и алиасы `Entity_FromId`, `Entity_GetFromID`). Дальше `Entity_GetSquad` |
| **Relic handle** | userdata | в feed **нет** | только из нативов после FromID |

Слот дипломатии (HIDWORD packed): `row.hi` — **не** Player_GetID. Полей `ownerPlayerId` / `ownerSlot` в snapshot **нет**.

Ключи: C++ пишет `[1004]={…}` (целое; в Lua 5.3 `t[1004.0]` — тот же ключ). Читайте `t[oid]` и запасной `t[tonumber(oid)]`. Не `t["1004"]`, если сами не конвертировали.

---

## 6. Когда данные живые

```lua
local function feed_ok()
    local w = rawget(_G, "AOE4HOOK_WORLD_DATA")
    return type(w) == "table" and type(w.entities) == "table"
end
```

| Симптом | Смысл |
|---|---|
| `WORLD_DATA == nil` | Publish выкл, или ещё не было успешного snapshot, или не в матче |
| `generation` не меняется много секунд, мир стоит | **hash-skip**: мир и SETTINGS.holds-countdown не пересобирают чанк. Таблицы **заморожены**, это норма. `Pump` всё равно идёт |
| `generation` не меняется, юниты бегают на экране | Publish мёртв или фильтр отрезал всех. Смотрите `truncated`, `count` |
| `AOE4HOOK_AI_PLAN == nil` | выкл **AI plan blob** на World, или Publish был без плана |
| `SETTINGS` есть сразу после Load hybrid, но не у вашего файла | ожидаемо |
| `SpatialWorldModel._nativeFeedAt` старый, а `_G` свежий | Import только **staging**; commit на тике SWM. Для решений используйте `_G` или ждите commit |

TTL: `AOE4HOOK_WORLD_FILTER.nativeFeedTtl` (обычно 4…16 с, 8× интервал Publish).  
Интервал Publish: 0.20…1.00 с (не чаще 1 полного ScarDoString в секунду).

Максимум сущностей в чанке: до **8192** (слайдер World). `truncated=true` — обрезали.

Деревья (`k=4`) в кэше C++ **нет**. `treeCount` / `WORLD_DATA.trees` — отдельный сэмпл точек, не полный лес.

---

## 7. Глобалы snapshot (полный словарь)

Читать только через `rawget(_G, "ИМЯ")`. Snapshot **перезаписывает** таблицы целиком. Не держите ссылку на старый `entities` между тиками, если нужен актуальный мир — берите заново.

Алиасы после каждого publish:

```lua
AOE4HOOK_ESP_SNAPSHOT = AOE4HOOK_WORLD_DATA
AOE4HOOK.world / .ents / .census / .owners / .localId / .stocks / .game / .filter / .twd
AOE4HOOK_ENTS[id] = row
```

`AOE4HOOK.Settings()` / `.settings` — таблица `AOE4HOOK_AI_SETTINGS` (BindFeed). `AOE4HOOK.Ai()` — поле `.ai` пакета бота.

### 7.1 `AOE4HOOK_GAME`

| Поле | Тип | Смысл |
|---|---|---|
| `schema` | int | 10 (`kBridgeSchemaVersion`, `radar.cpp`) |
| `dllVersion` | string | например `16.3.11308.bridge8` |
| `generation` | int | счётчик собранных job; при hash-skip в Lua не растёт |
| `simTick` | int | тик сима |
| `camZoom` | number | камера |
| `minimapZoom` | number | |
| `collectAsync` | bool | |
| `collectMs` | int | |

### 7.2 `AOE4HOOK_WORLD_FILTER`

```lua
{ prefer = true, nativeFeedTtl = 8.0 }
```

### 7.3 `AOE4HOOK_HAS_OTHER_HUMAN`

**Удалена** из моста 30.08.2026: DLL её не публикует, `AOE4HOOK_GAME.hasOtherHuman` тоже нет.
Бот и `macro_bridge` работают во всех режимах. Код, который ещё читает эту
переменную, получает `nil`.

### 7.4 `AOE4HOOK_TWD`

**Не** входит в world snapshot Send. Отдельный push (ESP / Native TWD), не вкладка Send.

```lua
{ draw = 0|1, source = "native"|"overlay"|"off" }
```

Кольца TWD — отдельный `twd.scar` в System, не ваш файл. Радиус = **weapon from origin** (как native selection ring), не «огонь + footprint». Несколько орудий (стрелы + пушка / springald) — концентрические круги: в кэше `twdRadius` / `twdRadiusB` / `twdRadiusC`, в snapshot строки здания `r` / `r2` / `r3`. `padx` / `padz` — occupancy (алерт крестьян до стен), не сам круг.

### 7.5 `AOE4HOOK_LOCAL_ID`

Число `Player_GetID` локального. Может не приехать, если owner ещё не упакован.

### 7.6 `AOE4HOOK_OWNERS` и `AOE4HOOK_GetPlayerOwner`

Компактная карта **только выбранных** строк с валидным `row.o` (Player_GetID). Не полный dump мира и не дубли `ownerPlayerId` на каждой строке.

```lua
AOE4HOOK_OWNERS[nativeId] = Player_GetID   -- из row.o
AOE4HOOK.owners = AOE4HOOK_OWNERS          -- BindFeed

-- встроено в snapshot:
AOE4HOOK_GetPlayerOwner(h)  -- h = id или { id = ... }; читает I[id].o
```

Hybrid `W.OwnerStats` / `OwnersReady` ходит по этой таблице. Без неё канал владельцев `owner_channel_invalid`.

### 7.7 `AOE4HOOK_STOCKS`

Ключ = Player_GetID.

```lua
AOE4HOOK_STOCKS[1004] = { f = food, w = wood, g = gold, s = stone }
```

Пусто, если на World выкл stocks.

### 7.8 `AOE4HOOK_CENSUS`

```lua
{
  dtMs = 0,
  src = "native_workers" | "native_selected" | "off",
  rates = { food = 50, wood = 44, gold = 48, stone = 48 },  -- на работника / мин (aoe4world)
  world = {
    sheep, sheepWild, sheepTaken, deer, boar, wolf, fish,
    relics, sacred, sacredFree,
    poi, poiFree, poiCap, poiHerbalist, poiMerchant, poiWolfDen,
    poiRuins, poiOutpost, poiRonin,
    fishShore, fishDeep, gold, stone, berry, farms, trees
  },
  players = {
    [Player_GetID] = {
      u, b, w, army, scouts, idle, age,
      tc, monk, siege, rlc, hurt,
      bk = { cav, ranged, spear, heavy, siege, known },
      pwr,
      hi, rgb = {r,g,b},          -- опционально
      stk = { f, w, g, s },        -- опционально
      g = { food, wood, gold, stone },           -- сколько workers на ресурсе
      inc = { food, wood, gold, stone, src = "workers_x_aoe4world_rate" },
      by = { ["unit_spearman_2"] = 8, ... },     -- до 96 имён
    }
  }
}
```

`src="off"` — census выкл, `players={}`.

### 7.9 `AOE4HOOK_WORLD_DATA`

Верхний уровень:

| Поле | Смысл |
|---|---|
| `version` / `schemaVersion` | 10 |
| `dllVersion` | строка DLL |
| `source` | `"AOE4HOOK"` |
| `capturedMs` | GetTickCount64 (не game time) |
| `generation` | как в GAME |
| `total` | сущностей в кэше |
| `count` | сколько ушло в `entities` |
| `eligible` | прошли фильтр |
| `treeCount` | деревья, увиденные walk (не все в `entities`) |
| `dtMs` | |
| `simTick` | |
| `syncHash` / `canonicalEntityHash` | |
| `ownerRosterHash` | |
| `simFrozen` | bool |
| `nativeFeedTtl` | сек |
| `truncated` | bool |
| `entities` | массив строк (`ipairs`) |
| `census` | тот же объект, что `AOE4HOOK_CENSUS` |
| `data.entities` / `data.census` | те же ссылки |
| `localId` / `localHi` | если известны |
| `look` | `{x,z}` камеры, если look clip |
| `sightN` | `{own, enm}` |
| `tickSec` | **0.125** (8 Гц сима) |
| `simTime` | `simTick * 0.125` |
| `localSight` / `camZoom` / `minimapZoom` | |
| `map` | `{cx, cz, sx, sz}` если карта валидна |
| `pal` | `[hi]={id=Player_GetID, rgb={r,g,b}}` |
| `trees` | `{ n, s = { {x,z}, ... } }` сэмпл |
| `relM` | строка, если есть |
| `triggerLuaDump` | bool, редкий debug |

`filter` внутри WORLD_DATA (что владелец включил на World):

```lua
{
  own, ally, enemy, neutral,          -- 0/1 кто
  w, army, scout, herd, hunt, idleW, -- типы
  prodOnly, moving, look, lookR,
  motion, hp, combat, cat, queue, vis,
  census, censusAll, aabb, stk, ai,
  ttl, cap
}
```

Если `filter.hp=0`, в строках не будет `hp`/`hpm`. То же для motion, queue, vis, catalog, aabb.

### 7.10 Строка сущности (`entities[i]`)

Поле **есть только если** его посчитали и фильтр поля включён. Проверяйте `nil`.

| Поле | Тип | Смысл |
|---|---|---|
| `id` | int | native entity id |
| `n` | string | лист blueprint |
| `k` | int | 0 resource, 1 relic, 2 building, 3 unit, **4 tree нет в кэше**, 5 animal, 6 unknown |
| `p` | `{x,y,z}` | позиция |
| `fl` | int | флаги, если ≠ 0 |
| `o` | int | Player_GetID |
| `os` | int | 0 none, 1 packed-id, 2 packed-slot, 3 scan, 4 prev |
| `hi` | int | diplomacy index 0…15 |
| `rel` | int | 0 undef, **1 enemy**, **2 ally**, **3 neutral**, **4 self** |
| `mn` `mx` | `{x,y,z}` | AABB здания (`filter.aabb`) |
| `r` | number | TWD: weapon from origin (native selection) |
| `r2` `r3` | number | дополнительные орудия (если есть) |
| `hw` `hz` `hh` | number | half width/depth, height ESP |
| `padx` `padz` | number | TWD occupancy pad (не радиус круга) |
| `g` | int | veteran line / attrib _2/_3/_4 |
| `age` | int | 1…4 |
| `w` | 1 | worker |
| `gr` | 1…4 | gather food/wood/gold/stone |
| `rem` | number | остаток ресурса |
| `vx` `vz` `s` | number | скорость (`filter.motion`) |
| `hd` | number | heading deg |
| `wx` `wz` | number | waypoint ~2.5 с |
| `tk` `tx` `tz` | | цель: kind + xz |
| `prod` | 1 | здание с очередью |
| `qn` | int | длина очереди |
| `ms` `ds` | number | max/default speed (`filter.combat`) |
| `hp` `hpm` | number | (`filter.hp`) |
| `so` `si` | number | sight outer/inner |
| `fire` `melee` `rdy` | 0/1 | firing / melee / ready |
| `rr` `rt` | int | reload remain/total **тики** |
| `rrs` | number | remain × 0.125 с |
| `idle` | 1 | worker стоит без gather |
| `ghost` | 1 | ghost blueprint |
| `rlc` | 1 | несёт реликвию |
| `bkt` | string | strategy bucket каталога |
| `dps` `rng` `dmg` `armM` `armR` `pop` | number | каталог (`filter.cat`), только combat unit |
| `camo` `fow` `sp` | 1 | camouflage / in FoW / spotted (`filter.vis`) |

---

## 8. API `AOE4HOOK.*`

Модуль: `NativeEspData\aoe4hook_bridge.scar`. `apiRev = 7`. После bootstrap есть до вашего кода. Snapshot вызывает `BindFeed()`.

Если файла нет, snapshot всё равно ставит `AOE4HOOK.Get`. Полный Query — нет.

```lua
AOE4HOOK.BindFeed()           -- bool: WORLD_DATA таблица
AOE4HOOK.Get(id)              -- строка или nil
AOE4HOOK.Owner(id)            -- Player_GetID
AOE4HOOK.OwnerSlot(id)        -- hi
AOE4HOOK.Rows()               -- массив entities
AOE4HOOK.Dist / Dist2(a, b)   -- по p или {x,z}
AOE4HOOK.Query(filter)        -- см. ниже
AOE4HOOK.Near(origin, r, filter)
AOE4HOOK.Enemies(filter)      -- rel=1
AOE4HOOK.Workers(filter)
AOE4HOOK.Army(filter)         -- k=3, worker=false
AOE4HOOK.CountByName(playerId, needle)  -- census.players[id].by substring
AOE4HOOK.IdleWorkers(filter)
AOE4HOOK.Producers(filter)    -- prod=1
AOE4HOOK.IdleTownCenters(filter)
AOE4HOOK.Herdables(filter)    -- k=5 + имя sheep/goat/cattle/herdable
AOE4HOOK.PlayerEsp(filter)    -- по умолчанию rel=1
AOE4HOOK.ResHud(playerId?)    -- stocks + idle TC/workers
AOE4HOOK.Game()
AOE4HOOK.Look()               -- WORLD_DATA.look
AOE4HOOK.Map()
AOE4HOOK.Schema()             -- schema, dllVersion, generation
AOE4HOOK.Hp(id)               -- hp, hpm
AOE4HOOK.Census(playerId?)
AOE4HOOK.Stocks(playerId?)
AOE4HOOK.Filter()
AOE4HOOK.AiLockIntent()       -- {vill, army, building, source} из AOE4HOOK_AI_LOCK
AOE4HOOK.WouldStrip(sid)      -- true = tracking, +0x40==0, tactic stack live; AI_LockSquad = 4A70. sid = Squad_GetID
AOE4HOOK.LockSafe(sid)        -- not WouldStrip (no tracking, already locked, or empty stack)
AOE4HOOK.Settings()           -- AOE4HOOK_AI_SETTINGS
AOE4HOOK.Ai()                 -- SETTINGS.ai или nil: live, gen, personality, scoring, fineTune
AOE4HOOK.AiApplyPersonality(key)  -- AI_SetPersonality локальному игроку (4 ключа Relic)
AOE4HOOK.AiApplyPackage()     -- только personality из SETTINGS.ai (scoring/fine-tune — C++)
AOE4HOOK.ToolkitParity()      -- диагностика, не игровой API
```

`Query(filter)` — все поля опциональны, AND:

`kind`, `rel`, `owner` (= `o`), `ownerSrc` (`os`), `worker`, `idle`, `gather`, `inFow`, `camouflaged`, `spotted`, `ghost`, `relic`, `hasTarget`, `hasWaypoint`, `idleProd`, `hasProd`, `grade`, `age`, `bucket`, `minHp`, `maxHpFrac`, `name` (подстрока lowercase), `origin`/`p` + `radius`.

---

## 9. `AOE4HOOK_AI_PLAN`

Оверлейный RPS (каталог + HP/reload), **не** Relic combat и не ProductionScoring.

Нужен флажок World **AI plan blob**. Иначе `nil`.

AI BOT контрпик **больше не читает** эту таблицу из Lua. C++ думает на
`AiPlannerGetSnapshot()`. Сессия **не** re-DoString PLAN, пока `AiRuntimeArmed()`.
World-feed может всё ещё публиковать blob для SWM / hybrid. Каты идут
`__EcoAct_Apply`, не `__EcoCounter_Tick`. См. [AI_SCORING_PIPELINE.md](AI_SCORING_PIPELINE.md).

```lua
{
  capturedMs, scoutCount, enemyScouts, neutralSheep, neutralDeer, neutralRelics,
  scouts = { { scoutId, x, y, z, sheep, dist, isDropoff, isIntercept }, ... },
  food   = { { workerId, foodId, x, y, z, kind }, ... },
  auras  = { { kind, x, y, z, r }, ... },
  comp   = {  -- ipairs! не map
    { o = Player_GetID, age, w, spear, archer, horse, maa, knight, xbow,
      siege, monk, heal, inspire, dervish, bless, atkheal, cmonk, other,
      need = { spear, archer, horse, maa, xbow },
      keepArch = true|false }
  },
  lock      = { [Player_GetID] = { nativeId, ... } },  -- до 192, без workers
  buildings = { [Player_GetID] = { nativeId, ... } },
  eco       = {
    [Player_GetID] = {
      o, age, vills, rpsNeed, threat,
      mode = "MASS" | "UPGRADE",
      reason = string
    }
  }
}
```

`eco.mode`: age ≥ 3 и `rpsNeed > 0` → MASS, иначе UPGRADE; младше 3 — MASS без угрозы или при `rpsNeed ≥ 5`. Age-up, дома, pop cap **в PLAN нет**.

`need.archer` / `need.xbow`: каталог цивы, мягкие лучники → арбалет → порох **только если PBG тренируется в текущем возрасте** (`UnitProfileKindAvailable`). Иначе спрос остаётся на лучниках (и коннице / копьях, если конь / MAA / рыцарь ещё недоступны). Каталог Castle-xbow в феодале не считается «уже в ростере». `keepArch=true` (English `unit_archer_N_eng` / yeoman / yumi) — **не** менять лучников на xbow. Копья / MAA / конь / рыцарь не сливаются.

Контракт lock: native id → `Squad_FromId` / `Entity_FromID`. Не Relic handle.

После publish оверлей зовёт `SpatialWorldModel.ImportAiPlan` (или глобальный `SpatialWorldModel_ImportAiPlan`). Копия: `SpatialWorldModel._nativeAiPlan` / `.state.nativeAiPlan`. Если PLAN `nil`, эти поля чистятся.

---

## 10. `AOE4HOOK_AI_SETTINGS` и профили

Пишется **каждый** snapshot (даже без PLAN). На Load hybrid — ещё и в том же чанке, что ядро, до `Hybrid_Init`.

```lua
{
  profile = "offline" | "risk" | "safe",
  ida_ok = 1,                         -- аудит нативов в репо, не Has() в этом матче
  holdSec, holdUpgradeSec, firstSlotDelaySec, forcedQuietSec,
  villagerCap, villagerCapMin, villagerCapMax, armyCap, monkCap,
  holdByTimeMin, holdByPop,
  cancelNative, relicScoring, availabilityNative,  -- bool
  macroSync, safe,                                 -- bool
  civFilter,                                       -- 0/1
  villagerByAge = { n1, n2, n3, n4 },
  units = { villager=true, spear=true, ... },
  buildings = { tc=true, house=true, ... },
  civs = { eng=true, ..., oth=true },
  holds = { ["spear"] = 8.32, ... },  -- остаток секунд, только живые ключи
  builder = {                         -- AI BOT Scar builder (AI Profiles)
    profile = "Default",              -- stem файла
    lockU = { ["spearman"] = true, ... },
    lockB = { ... },
    lockG = { ["wheelbarrow"] = true, ... },
    qU = { ["man-at-arms"] = 8, ... },  -- queue then lock
    qB = { ["house"] = 5, ... },
  },
  ai = {                              -- пакет AI BOT (ссылки, не копия .ini/.lua)
    live = false,                     -- Live in match
    gen = 1,                          -- растёт на Load / смене ссылок
    personality = "default_campaign", -- ключ Relic или "" / restore
    scoring = "warmonger.lua",        -- файл в Lua Scripts или ""
    fineTune = "example_balanced",    -- stem AI Custom Templates или ""
  },
}
```

Семьи `units` (ровно эти ключи):  
`villager spear archer horseman maa knight xbow ram siege monk scout trader ship handcannon upgrade other`

Здания `buildings`:  
`tc house mill lumber mining farm barracks archery stable siege dock blacksmith university monastery`

Цивы `civs`:  
`eng fre hre rus chi abb del mal ott mon byz jap ayy jea dra zet kth hol od oth`

**Профили (как вести себя вам):**

| profile | Sim-write (takeover, Cancel, desire, availability) | Макрос владельца |
|---|---|---|
| `safe` | **нельзя** | принудительно SendInput |
| `offline` | можно vs AI | как на вкладке Macro |
| `risk` | можно, **OOS vs человек** | как Macro; Allow OOS — его риск |

`safe` в таблице всегда гасит `cancelNative` / `relicScoring` / `availabilityNative`.

Вкладка **AI BOT** (профили `.ini`, Fine-tuning, Scoring Lua, локи, AUTO hybrid): [`docs/AI_BOT.md`](ai_bot.md).

`holds`: оверлей шлёт leftover. Если вы делаете свой auto-hold, **не продлевайте** expire, пока текущий ещё в будущем (как hybrid `H.SetAuto` с `refresh ~= true`). Countdown в `_G` при hash-skip замирает — ориентир для логики: свой `World_GetGameTime() + sec` при **первом** появлении ключа.

`ida_ok=1` не проверяйте как «можно звать UnderCountLimit». Сначала `type(_G.AIProductionScoring_UnderCountLimit)=="function"` и понимание, что Rule tick — не scoring context.

Fallback имени файла: `AOE4HOOK_HYBRID_FILE_PROFILE`. Имеет смысл, если SETTINGS ещё нет. Если SETTINGS есть — **он главный**.

---

## 11. `SpatialWorldModel` и `UnitIntelligence`

Грузятся сами. Не `dofile` их из Files.

### SWM (версия в `SpatialWorldModel.VERSION`, сейчас ~18.21)

Оверлей на каждом publish:

1. `config.nativeFeedPrefer = true`, `config.nativeFeedTtl = …`
2. `ImportWorldData(WORLD_DATA)` — это **staging**, не сразу `state.entities`
3. `ImportAiPlan(PLAN)` или очистка native plan

Commit в `state` — на interval SWM. Свежесть: `SpatialWorldModel._nativeFeedAt` (game time).

Полезное:

```lua
SpatialWorldModel.GetState()
SpatialWorldModel.GetEntity(nativeId)
SpatialWorldModel.GetSquad(id)
SpatialWorldModel.GetUnitProfile(squadOrName)
SpatialWorldModel.GetPlayerComposition(playerId)  -- Player_GetID
SpatialWorldModel.GetBaseCenter(playerId)
SpatialWorldModel.QueryEntities({
    enemy = true, category = "unit", visible = true, minConfidence = 0.25,
    ownerId = oid, worker = false, idle = true, inFow = false,
    origin = pos, radius = 30, role = "gold",
})
SpatialWorldModel.QuerySquads(filter)
SpatialWorldModel.FindNearest(position, filter)
SpatialWorldModel.Distance2D(a, b)   -- Lua, не World_DistancePointToPoint
SpatialWorldModel.SetMode(SpatialWorldModel.MODE_SP | MODE_DEBUG | MODE_OBSERVER)
SpatialWorldModel.Configure({ nativeFeedTtl = 8, ... })  -- только существующие ключи config
```

Категории query завязаны на модель SWM (`unit`, `building`, `resource`, …), не на `k` строки радара. Для сырого `k` используйте `AOE4HOOK.Query`.

Не кормите в `Distance2D` / move-нативы битые точки — натив дистанции на stale point падает.

### UnitIntelligence

Каталог aoe4world, не Essence из EXE.

```lua
UnitIntelligence.Get("unit_spearman_2")     -- или полный attrib
UnitIntelligence.GetByPbgid(12345)
UnitIntelligence.ProfileForSquad(squad)
UnitIntelligence.StrategyBucket(name)
UnitIntelligence.Coverage()                 -- { blueprints, variations, civilizations, ... }
```

Имя в feed `row.n` — лист; `Get` нормализует. Нет профиля → `nil`, не ошибка.

---

## 12. `MacroBridge` — очередь / cancel

Таблица появляется, когда владелец открыл Macro sim-engine **или** вы нажали SCAR-кнопки, **или** файл `macro_bridge.scar` уже исполнялся. Сама по себе после bootstrap её может не быть.

```lua
if type(MacroBridge) ~= "table" then return end

MacroBridge.Queue(nativeBuildingId, "unit_spearman_2", pbgId, mode)
-- mode 0: Entity_QueueProductionItemByPBG
-- mode 1: LocalCommand_EntityBuildSquad (считать OOS)

MacroBridge.Run({
  action = "queue" | "cancel" | "stop",
  selected = false,          -- иначе Misc_GetSelectedEntities
  allSlots = false,          -- cancel: вся очередь; иначе слот 0
  seconds = 0,               -- 0 = один раз; 1…60 = pulse каждые 0.25 с
  want = 1,                  -- глубина очереди 1…8
  mode = 0,
  force = false,             -- принимается, ни на что не влияет (проверка vs human удалена)
  name = "unit_spearman_2",
  pbgid = 0,
  ids = { 123456 },          -- native entity id зданий
})

MacroBridge.Stop()
local st = MacroBridge.Status()  -- version, running, action, last, done, errors
```

Алиасы: `MacroBridge_Run`, `MacroBridge_Queue`, `MacroBridge_Stop`.

Поведение:

- vs human: отказа нет (проверка удалена вместе с `AOE4HOOK_HAS_OTHER_HUMAN`);
- cancel **не** трогает age_up / upgrade_age / wonder;
- orig-нативы через `AOE4HOOK_Local.orig` / `AOE4HOOK_Safe._sim_orig`, на время вызова `AOE4HOOK_MP_SAFE=false`;
- engine 2 / `LocalCommand_*` не считать lockstep-safe.

Не копируйте `macro_bridge.scar` в Files. Не вызывайте из профиля Safe, если договаривались не писать sim.

Оверлейный автопоезд SendInput **не** вызывает MacroBridge. Ваш скрипт, который Queue, — отдельный писатель очереди; не дерите слот с вкладкой Macro.

---

## 13. Обёртки `AOE4HOOK_Local` / `AOE4HOOK_Safe`

Каждый Files-запуск (не quiet-feed) получает:

1. `local_rules.scar` → `AOE4HOOK_Local` (`_v=10`)
2. `checksum_wrappers.scar` → `AOE4HOOK_Safe` (`_v=3`), один раз на VM

Следствия для вас:

- `Rule_Add` / `Rule_AddInterval` / `TimeRule_*` / часть EventRule идут в список Local и тикают с **Pump**, не с Relic Insert. Это задумано (без Insert).
- По умолчанию `AOE4HOOK_MP_SAFE = true`. FOW-sim нативы подменяются UI-вариантами. Блок SIM_BLOCK при флаге `AOE4HOOK_BLOCK_SIM` превращается в no-op.
- `AOE4HOOK_Safe.Policy(name)` → `"call_ok"` | `"divert_local"` | `"maybe_local"` | `"oos"` | `"unknown"`
- `AOE4HOOK_Safe.Can(name)` / `.Call(name, ...)`
- Тихий world-feed **не** оборачивает ваш код Push: только присваивания + Pump. Глобалы видны сразу.

Нужен настоящий sim-натив (как MacroBridge): orig из `AOE4HOOK_Local.orig[name]`, кратко снять MP_SAFE, `pcall`, вернуть флаг.

`LocalCommand_*` — command stream, не «обход checksum». Vs человек = OOS, пока не доказано иначе.

---

## 14. Рецепты

### Вражеские копейщики: count + позиции

Вкладка Send: **Enemy**, **Unit**, **Army**. Census вкл. Остальное выкл.

```lua
-- C++ уже отфильтровал. Читайте глобалы, не зовите Entity_GetPlayerOwner.

local function enemy_spears()
    if not AOE4HOOK.BindFeed() then return 0, {} end
    local rows = AOE4HOOK.Army({ rel = 1, name = "spear" }) -- rel 1 = enemy
    local n = #rows
    -- счётчик по имени (без обхода всех e[]), если Census включён:
    -- AOE4HOOK.CountByName(enemyPlayerId, "spear")
    return n, rows
end

-- rows[i].n  имя   rows[i].k  тип (3=unit)
-- rows[i].p  {x,y,z}         rows[i].o  Player_GetID
```

`AOE4HOOK_CENSUS.players[id].army` / `.bk.spear` / `.by["unit_spearman_2"]` — агрегаты. PLAN (антипик) — отдельный тумблер **AI plan**, таблица `AOE4HOOK_AI_PLAN`.

### Свежий ли мир

```lua
local function world_rows()
    local w = rawget(_G, "AOE4HOOK_WORLD_DATA")
    if type(w) ~= "table" then return nil end
    return w.entities or (w.data and w.data.entities)
end
```

### Свои idle TC

```lua
local oid = rawget(_G, "AOE4HOOK_LOCAL_ID")
local tcs = AOE4HOOK.IdleTownCenters({ owner = oid })
```

### Native id → squad (как hybrid)

```lua
local function squad_from_native(id)
    id = tonumber(id)
    if not id then return nil end
    local names = { "Squad_FromId", "Squad_FromID", "Entity_FromID", "Entity_FromId" }
    for i = 1, #names do
        local f = rawget(_G, names[i])
        if type(f) == "function" then
            local ok, obj = pcall(f, id)
            if ok and obj then
                if names[i]:find("Entity", 1, true) and type(Entity_GetSquad) == "function" then
                    local ok2, sq = pcall(Entity_GetSquad, obj)
                    if ok2 then return sq, obj end
                else
                    return obj
                end
            end
        end
    end
    return nil
end
```

### PLAN.lock локального игрока

```lua
local function my_lock_ids()
    local plan = rawget(_G, "AOE4HOOK_AI_PLAN")
    local oid = rawget(_G, "AOE4HOOK_LOCAL_ID")
    if type(plan) ~= "table" or type(plan.lock) ~= "table" or oid == nil then
        return nil
    end
    return plan.lock[oid] or plan.lock[tonumber(oid)]
end
```

### Слушаться SETTINGS (Online / Offline → AI)

```lua
local function settings()
    local st = rawget(_G, "AOE4HOOK_AI_SETTINGS")
    if type(st) == "table" then return st end
    return nil
end

local function profile()
    local st = settings()
    local fp = rawget(_G, "AOE4HOOK_HYBRID_FILE_PROFILE")
    local p = (st and st.profile) or fp or "safe"
    if p == "offline" or p == "risk" or p == "safe" then return p end
    return "safe"
end

local function sim_writes_ok()
    local p = profile()
    if p == "safe" then return false end
    return p == "offline" or p == "risk"
end

local function unit_on(key)
    local st = settings()
    if not st or type(st.units) ~= "table" then return true end
    if key == "manatarms" then key = "maa" end
    local v = st.units[key]
    if v == nil then return true end
    return v == true
end
```

### Hold с C++ (не продлевать)

```lua
-- свой expire[key] = gameTime + leftover, выставлять только если ключ новый
-- или предыдущий expire уже прошёл
```

Ключи hold те же, что `units` / макрос: `villager`, `spear`, `archer`, `horseman`, `maa`, `xbow`, `upgrade`, …

### Тик без Relic Insert

```lua
-- Rule_AddInterval(MyTick, 0.75) после загрузки оверлеем — попадёт в Local.Pump
-- Не вызывайте TimeRule_Insert.
```

### Не драться с hybrid

Не грузите второй hybrid. C++ оверлей сейчас использует единый `hybrid_core.scar`, который вызывается через ярлыки-пустышки (`hybrid_o_offline.scar`, `hybrid_o_risk.scar`, `hybrid_o_safe.scar`) для установки профиля безопасности.
**КРИТИЧНО:** Никогда не держите `hybrid_c.scar` (устаревшую легаси-версию) в папке автозагрузки `_system\_auto` одновременно с `hybrid_o`, иначе ИИ начнут конфликтовать, отменять друг другу команды, а рабочие и торговцы будут зависать.

Свой директор: другое имя файла, читайте те же `_G`. Либо расширяйте поведение, не вызывая `Game_AIControlLocalPlayer`, если `profile()=="safe"`.

### Новые функции ядра (Anti-Idle)

В `hybrid_core.scar` теперь встроены системы **Anti-Idle для рабочих и торговцев**:
1. **Рабочие:** Если отменить постройку фундамента, рабочий зависает, так как деревья не всегда передаются через мост (радиус 65м). Теперь скрипт автоматически находит ближайшее здание-приемник ресурсов (`lumber_camp`, `mining_camp`, `mill`, `town_center` в радиусе 90м) и отправляет рабочего кликом на него. Движок игры сам найдет ресурс.
2. **Торговцы:** Если фактория (`trading_post`) или рынок союзника находятся под туманом войны, встроенный ИИ может тупить. Функция `TraderAntiIdleTick` находит таких простаивающих торговцев (`trade_cart`, `trade_camel`) через `SpatialWorldModel.QueryEntities` и отправляет принудительный приказ `SCMD_DefaultAction` на ближайший нейтральный или союзный рынок. Функция успешно работает даже через Fog of War, если C++ мапхак видит координаты.

---

## 15. Проверка без исходников

Вкладка **Online**: `probe.scar`, `dump_vm.scar` (если владелец дал).  
Вкладки **OFFLINE (OOS RISK) -> AI Director**: директор `hybrid_o_offline` / `hybrid_o_risk`. Safe — только Online.  
`print` / `scartrace` попадают в `Documents\My Games\Age of Empires IV\warnings.log`.  
Лог оверлея: `Documents\AOE4HSettings\Logs\` и часто `%TEMP%\aoe4_internal.log`.

Минимум в матче после Publish:

```lua
pcall(print, "[chk] schema", (AOE4HOOK.Schema()))
pcall(print, "[chk] local", rawget(_G, "AOE4HOOK_LOCAL_ID"))
pcall(print, "[chk] rows", #(AOE4HOOK.Rows() or {}))
pcall(print, "[chk] plan", type(rawget(_G, "AOE4HOOK_AI_PLAN")))
pcall(print, "[chk] set", type(rawget(_G, "AOE4HOOK_AI_SETTINGS")))
pcall(print, "[chk] swm", type(rawget(_G, "SpatialWorldModel")))
pcall(print, "[chk] ui", type(rawget(_G, "UnitIntelligence")))
pcall(print, "[chk] mb", type(rawget(_G, "MacroBridge")))
-- ПРИМЕЧАНИЕ: переменная AOE4HOOK_HAS_OTHER_HUMAN полностью вырезана из движка (30.08.2026).
-- ИИ теперь работает во всех режимах без ограничений.
```

Ожидание:

- `schema` 10, `dllVersion` содержит `bridge`;
- `AOE4HOOK_AI_PLAN.lock[Player_GetID]` — массив чисел;
- `AOE4HOOK_AI_SETTINGS.profile` совпадает с Online (safe) или Offline → AI (offline/risk);
- Safe: ваш код не зовёт takeover/Cancel;
- `MacroBridge` может быть `nil`, пока не трогали Macro sim.

`Has()` натива: `type(rawget(_G, "Entity_CancelProductionQueueItem"))=="function"`. Имена часто XOR в EXE — в dump_vm части `Player_*` отсутствуют, это не баг вашего файла.

---

## 16. Что попросить у владельца оверлея

Без этого ваш `.scar` слепой или пишет OOS.

1. Вкладка **World → Publish (in-match)**.
2. Who preset **Hybrid** (own/ally/enemy/neutral + workers/army), если нужны враги и lock.
3. **AI plan blob**, если читаете `PLAN.lock` / `eco.mode`.
4. Поля **queue / hp / census / stocks**, если они вам нужны.
5. Интервал Publish (не чаще 1 Гц).
6. Вкладки **ONLINE (SAFE) -> Safe Core** и **OFFLINE (OOS RISK) -> AI Director** — ваш контракт на sim-write.
7. Macro engine и Allow OOS — только Offline → Macro, если вы зовёте `MacroBridge`.
8. Не жать **Offline → AI → Enable AI** в Safe, если ваш файл тоже не должен брать слот.
9. Пересобрать / реинжект DLL после смены схемы (смотрите `dllVersion`).

---

## Краткая модель

```
Publish (если вкл)
  → _G.AOE4HOOK_WORLD_DATA / _ENTS / _CENSUS / _PLAN / _SETTINGS / …
  → AOE4HOOK.BindFeed()
  → SWM.Import* (staging)
  → Pump  → ваши Rule_AddInterval

Load вашего .scar
  → NativeEsp (один раз)
  → local_rules + checksum
  → ваш код
  → (hybrid: SETTINGS уже в чанке)
```

World-feed — те же глобалы, что у мира и PLAN. Это не отдельный натив и не замена Pump. MacroBridge — второй канал, только производство, sim-write.

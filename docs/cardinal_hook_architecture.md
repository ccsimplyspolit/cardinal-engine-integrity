# InternalInjector — архитектура и модули

Игра: Age of Empires IV **16.3.11308.0**. Сборка: `internal\AOE4HOOK.sln`, цель `InternalInjector`, Release x64.

Объём: **~90 000 строк**, 40+ модулей. Документ описывает **устройство и контракты между модулями**, а не каждую статическую функцию — последнее при таком объёме быстро расходится с кодом и вводит в заблуждение. Публичный API каждого модуля — в его `.h`; здесь сказано, зачем модуль нужен, что он гарантирует и на чём об него спотыкаются.

---

## Оглавление

1. [Слои](#1-слои)
2. [Поток данных мира](#2-поток-данных-мира)
3. [Исполнение SCAR](#3-исполнение-scar)
4. [Модули](#4-модули)
5. [Инварианты и ловушки](#5-инварианты-и-ловушки)
6. [Как проверять до сборки](#6-как-проверять-до-сборки)

---

## 1. Слои

```
       игра (RelicCardinal.exe)
                 |
   engine / offsets / hooks      резолв адресов, D3D12-хук, VEH
                 |
        radar (кэш мира)         RPM-сбор сущностей, 1.2–2.3 Гц
          /      |      \
       esp    планировщик   мост SCAR
          \      |      /
         ui (ImGui, вкладки)
                 |
      сессия ИИ / локи / макро
```

Правило: **всё, что читает мир, читает кэш `radar`, а не память напрямую.** Кэш собирается воркером вне рендер-потока; Present только рисует.

---

## 2. Поток данных мира

### `radar.cpp` (15 500 строк) — центральный модуль

Собирает `RadarWorldEnt[]` — снимок сущностей: позиция, владелец, отношение, тип, скорость, курс, HP, очередь производства, цель атаки, видимость.

**Сбор по требованию.** `WorldComputeDemand()` вычисляет, какие поля вообще нужны в этом кадре. Дорогие поля читаются, только если кто-то их запросил:

| Флаг | Поля | Кто запрашивает |
| --- | --- | --- |
| `collect` | базовый набор | радар, обсервер, миникарта, алерты |
| `liveHz` | частота 2.3 Гц вместо 1.2 | радар, обсервер |
| `aiPlan` | запуск `AiPlannerUpdate` | мост, coach, макро, сессия, HUD ИИ |
| `liveExt` | `hpCur`/`hpMax` | ESP, обсервер, мост |
| `queues` | `queueN`, `hasProd` | макро, idle-алерты |
| `targets` | `tgtKind`, `hasWaypoint` | радар, ESP, мост |
| `deposits` | `resRemain` | ESP, мост |
| `vis` | `camouflaged`, `inFow`, `spotted` | ESP, мост |
| `aabb` | габариты | ESP, кольца ратуш |
| `uiSel` | `uiSelected` | ESP, билдер, макро, **лок подгрупп** |
| `gather` | `gather` | ESP, обсервер, алерты, **карточка дохода** |

**Это главный источник ошибок в проекте.** Новый потребитель обязан прописать себя в `WorldComputeDemand`, иначе поле молча остаётся нулём. Подробнее — §5.

### `ai_planner.cpp` — план из кэша

`AiPlannerUpdate()` считает `AiPlanSnapshot`: состав армий по игрокам, `need[]` (сколько чего нужно по RPS), экономический режим `MASS`/`UPGRADE` с текстовой причиной, планы разведки, назначения на еду, ауры. Cadence ~**2 с** если `AiRuntimeArmed()`, иначе ~10 с. Векторы `lock`/`buildings` (192/128) — **Lua-экспорт для SWM**, не лимит think.

`AiPlannerGetSnapshot()` отдаёт потокобезопасную копию. Её читают мост, C++ контрпик (`AiRuntimeOnPlanPublished`) и HUD AI BRAIN.

### `ai_runtime.cpp` / `ai_production.cpp` — think без natives

На том же collect worker: `ai_counter_math` (role / cuts / 35 с hysteresis) + observatory (`UnitProfilePickTrain`). Present только `PostMessage(WM_SCAR_AI_COMMIT)`. Apply — `__EcoAct_Apply` на оконном потоке. Lua `__EcoCounter_Tick` мёртв. Канон: `AI_SCORING_PIPELINE.md`, ADR-001.

### `ai_combat.cpp` — RPS-модель

Сколько юнитов какого типа нужно, чтобы убить одного вражеского. Учитывает тиры кузницы/университета, апгрейды, национальные бонусы. Отсюда `perCav` / `perSpear` / `perRanged` / `perHeavy` в снапшоте.

---

## 3. Исполнение SCAR

### `scar.cpp` — пути в Lua-VM

| Путь | Функция | Когда |
| --- | --- | --- |
| **Оконный поток** | `ScarExecuteOnWindowThread` | **рабочий путь** Enable / locks / Files (`SendMessage`) |
| **PostMessage каты** | `WM_SCAR_AI_COMMIT` / `WM_SCAR_ECO_CONTEST` | Present не ждёт SCAR; apply на оконном потоке |
| Мост | `ScarExecuteBridgeOnWindowThread` | снимок мира, `quiet=1` |
| ScarHelper | `ScarExecuteHelperThread` | **мёртв, не использовать** |

**ScarHelper (RVA `0xB7F150`) падает на каждом вызове.** Он читает собственный адрес возврата (`mov rcx,[rsp+0x38]`) и валидирует вызывающего; `CreateThread` из нашей DLL этой проверки не проходит, плюс у свежего потока нет потокового состояния Relic. За всю историю логов — ноль успешных вызовов. Детали и доказательство — `AI_SESSION_HANDOFF.md`.

### Композиция скрипта

`ScarAcquireLiveScript(script, quiet, lean)` собирает то, что реально уходит в VM:

- **обычный** (`quiet=0, lean=0`) — trust-заголовок + `local_rules.scar` (128 КБ) + `checksum_wrappers.scar` (141 КБ) + тело, всё в `loadstring`. Бутстрап шлётся один раз на VM.
- **quiet** — тело + константный `Pump`. Для моста: он идёт часто и большой.
- **lean** — тело + `Pump`, обёрнутое в `loadstring`, **без бутстрапа**. Для C++-скриптов, которым нужны только обычные нативы: сессия ИИ, локи. Lean **не** ждёт `kScarStartConditionsMs` (2 с) — это пол только для Files/hybrid с `Rule_*`.

`lean` не выставляет флаги «бутстрап отправлен» — иначе следующий Files/hybrid-скрипт остался бы без `AOE4HOOK_Local`.

### Что даёт рассинхрон

Аудит по каталогу `checksum_wrappers.scar` (`AOE4HOOK_Safe`): из нативов, которые зовёт сессия, **12 в секции `block`** — это sim-записи:

`Game_AIControlLocalPlayer`, `AI_Enable`, `AI_SetDifficulty`, `Game_EnableInput`, `AI_LockSquad(s)`, `AI_LockEntity`, `AI_UnlockSquad`, `AI_UnlockEntity`, `AI_UnlockAll`, `Player_SetSquadProductionAvailability`, `Player_SetEntityProductionAvailability`.

Ещё **5 в секции `divert`** — `Rule_Add`, `Rule_AddInterval`, `Rule_AddOneShot`, `Rule_AddPlayerEvent`, `Rule_Remove`. Список правил входит в поток контрольной суммы (`LuaRules_SerializeTimeRules`), и `local_rules.scar` уводит наши правила в приватный список именно ради этого. **При `lean` этой защиты нет.** Lock-путь AI BOT поэтому **не** ставит Relic TimeRules/EventRules: контрпик и гарнизон тикают с C++, новые боевые — spawn-watch по world cache. `UnsavedTimeRule_*` тот же список `LuaRules+0x20`, не обход. Overlay всё ещё помечает vs humans как десинк: `AI_Enable` пишет `AIWorldData`.

Остальные ~36 нативов — чтение, секция `ok`.

---

## 4. Модули

### Ядро

| Модуль | Строк | Роль |
| --- | --- | --- |
| `engine.cpp` | 2 864 | Запуск, D3D12-хук, VEH-обработчик крашей, FOW-флаги |
| `offsets.cpp` | 1 404 | Резолв RVA по сигнатурам + AOB-скан, проверка прологов |
| `hooks.cpp` | 872 | Present-хук, точка входа `HotkeysPoll` |
| `log.cpp` | 1 131 | `aoe4_internal.log`, дампы крашей, чтение `warnings.log` |
| `config.cpp` | 1 431 | `config.ini` — чтение/запись всех настроек |
| `fps_profile.cpp` | — | Present percentiles (p95/p99/1% low). `FpsSec::AiRuntime` = worker, `AiCommit` = window apply |

### Мир и отрисовка

| Модуль | Строк | Роль |
| --- | --- | --- |
| `radar.cpp` | 15 513 | Кэш мира, радар, обсервер-HUD, MAP TRACKER, **HUD AI BRAIN** |
| `esp.cpp` | 4 552 | Боксы, трассеры, кольца обзора; TWD = **weapon from origin** (как native selection), несколько орудий → `twdRadius` / `B` / `C` |
| `minimap_native_icons.cpp` | 639 | Иконки на нативной миникарте |
| `hud_drag.cpp` | — | Перетаскиваемые панели: слоты, сворачивание, позиции в конфиге |
| `hud_alerts.cpp` | 779 | TWD-алерт «крестьяне вне зоны» |

### ИИ

| Модуль | Строк | Роль |
| --- | --- | --- |
| `ai_session.cpp` | — | Сессия AI BOT: стадии инжекта, `PostAiCommit`, handover. Lean start delay **1 с**; контрпик ещё +1 с |
| `ai_runtime.cpp` | — | C++ counter + `__EcoAct` generation. `FpsSec::AiRuntime` = worker |
| `ai_production.cpp` | — | Observatory / rank. Не второй Relic director |
| `ai_counter_math.h` | — | Pure cuts. Host tests. Без Windows / Lua |
| `ai_scoring_catalog.h` | — | ScarDoc `AIProductionScoring_*` + Relic hook names |
| `ai_planner.cpp` | 1 029 | `AOE4HOOK_AI_PLAN` snapshot; 2 с если runtime armed |
| `ai_combat.cpp` | 1 586 | RPS-модель, `need[]` |
| `ai_builder.cpp` | 1 633 | Профили, локи/очереди билдера |
| `stk_lua_lock.cpp` | 912 | Army lock, villager lock, **подгруппы**, **гарнизон** |
| `unit_profile.cpp` | 1 579 | Характеристики юнитов, нац. бонусы, линии (`keepArcherLine`) |

### Интерфейс

| Модуль | Строк | Роль |
| --- | --- | --- |
| `ui.cpp` | 5 633 | Каркас ImGui, вкладки, применение конфига |
| `ui_scar_lanes.cpp` | — | Вкладки AI BOT / Probe / Offline |
| `ui_scripts.cpp` | 1 806 | Fine-tune, пресеты, Files |
| `ui_i18n.cpp` | 1 357 | Словарь переводов, **править вручную** — см. ниже |
| `docs_layout.cpp` | 1 252 | Встроенная справка |
| `ui_theme.h` | — | Токены: цвета, отступы, скругления, **размеры и шрифты** |

#### Оболочка и под-панели (12.09.2026)

Меню — одно окно `##aoe4menu` (`HudBegin`, `ui.cpp`), внутри сайдбар 220px +
хедер 64 + тело + футер 36. Всё, кроме виджетов, рисуется вручную на
`GetWindowDrawList()`; `BeginTabBar` в проекте не используется нигде. Тело —
`switch (g_menuTab)` по 14 вкладкам.

Тяжёлые вкладки разбиты на под-панели через `ui_impl::DrawSubTabRow` —
собственный примитив, он же обслуживает Макро и Монитор сети:

| Вкладка | Панели |
| --- | --- |
| ESP | Basic · Labels · Highlights · Colors |
| AI BOT | Session · Fine tuning |
| Радар | Display · Observer · Map · Colors |
| Offline | Spawn · Combat · World (две колонки сохранены) |
| Макро | Basic · Units · Timing · Live (второй уровень под SendInput / Sim) |

**`persists=false` обязателен** для панели, которой нет в `AppConfig`.
`DrawSubTabRow` зовёт `ConfigMarkDirty()` при смене, и для функционального
статика это ложь: футер скажет «Не сохранено», загорится точка, а
`ConfigService` через 2 с перепишет `config.ini` посреди матча ради значения,
которого в файле нет. Персистится только `g_macroPane` (внешний ряд Макро).

`ui_internal.h` помечен «Not a public API. Do not include from non-UI TUs» —
`esp.cpp`, `radar.cpp` и `prod_macro.cpp` объявляют `DrawSubTabRow` вперёд, а
не включают заголовок.

#### Переводы: генератор устарел

`kPairs` в `ui_i18n.cpp` ищется **бинарным поиском** (`Lookup` / `CmpKey`,
порядок байтов UTF-8 английского ключа), поэтому сортировка — требование
корректности, а не стиля: запись не на своём месте недостижима и молча
рендерится по-английски. Так и было с двумя записями `Only Eco`, вписанными
руками в раздел M.

**`gen_ui_i18n.py` запускать нельзя.** Его словарь отстал от
`ui_i18n.cpp` и содержит дубликаты ключей, которые Python молча сливает —
регенерация удалит живые переводы. Правило: вставлять в `kPairs` точечно, в
отсортированную позицию, и зеркалить ключ в генератор, чтобы расхождение не
росло.

Ключ перевода — **видимая подпись до `##`**. Переименовал подпись — потерял
перевод и сменил ImGui-идентификатор (`UiTr` возвращает `"Русский###English"`).

#### Проверка непереведённого

Сверка литералов со словарём должна покрывать **все** формы вызова, а не
только кнопки: слайдеры, комбо, поля ввода и `StkPair` дают подписи наравне с
`UiButton`. Узкий скан по девяти формам дал «чисто» при 45 непереведённых
строках. Сейчас покрыто 24 формы. Идентификаторы движка
(`AttackStructure`, `DefendStructure`, `EnemyClump`, `front_line`) остаются
английскими намеренно — их сверяют с сурсом.

### Прочее

`prod_macro.cpp` (4 479) — макро производства. `native_overrides.cpp` (5 910) — Lobby identity (aoe4world `profile_id`), spoof. `lobby_actions.cpp` — Dodge / Add AI / `LoginAsync` reconnect (`0x3109420`) / skip Search CD. `session_rejoin.cpp` — билет `Matches\rejoin_session.json` + неофициальный LoginAsync. `relay_failover.cpp` — `JoinSessionAsync` `0x2EFC430`. `mp_bypass.cpp` — dual-flag + снимок RA-окна для шапки. `scar_trust.cpp` (627) — сканер доверия к `.scar` (красная таблетка **Офлайн** в шапке). `region_block.cpp`, `ra_hide.cpp`, `maphack_fowctrl.cpp`, `game_keybinds.cpp`, `sdk_dump.cpp`.

---

## 5. Инварианты и ловушки

Каждая из них уже стоила отладочной сессии.

### 5.1 Поле кэша молчит, если его не запросили

Новый читатель `RadarWorldEnt` **обязан** прописаться в `WorldComputeDemand()`.

Класс безопасен там, где у поля есть парный флаг: `hpCur` проверяется через `haveHp`, габариты — через `hasAabb`. Потребитель видит «данных нет» и корректно вырождается.

**Опасны ровно два поля — `uiSelected` и `gather`**: парного флага у них нет, они молча читаются как ноль. Оба уже дали баги: лок подгрупп получал пустое выделение, карточка дохода показывала всех крестьян простаивающими.

### 5.2 ScarHelper мёртв

Не возвращайте `ScarExecuteHelperThread`. Всё идёт через `ScarExecuteOnWindowThread`.

### 5.3 Фиксированный буфер под генерируемый скрипт

`_snprintf_s(..., _TRUNCATE, ...)` **обрезает молча** — это не ошибка, возврата никто не проверяет. Скрипт подгрупп однажды перевалил за 6144 байта и уехал в игру обрезанным посреди `end`; симптом выглядел как «сломался Lua», хотя Lua был корректен.

Размер считайте из формата (`_scprintf`) в `std::string`.

### 5.4 `pcall` не ловит access violation

Обёртка `pcall` вокруг натива спасает от ошибки Lua, но не от AV внутри нативного кода. Попытка гасить тактику через `LocalCommand_Squad(..., SCMD_Stop, ...)` роняла VM прямо внутри скрипта, несмотря на `pcall`.

### 5.5 `AI_LockSquad` сносит тактику

Документация натива: *«Locks the squad and **disables its tactics (if any)**»*. Для отряда под планом ИИ (разведчики — у них отдельные `scoutPlans`) это означает разбор структуры на лету; следующий тик ИИ читает нулевой указатель (`rva=0x2A45959`, `[rax+0x58]`) и роняет игру.

`AI_LockSquads` (inner `0x296D680`) при наличии tracking **всегда** идёт в 4A70 — skip `+0x40` нет. После Enable батч небезопаснее одиночного лока. Подгруппы зовут только `AI_LockSquad` на крестьян.

Здания — `AI_LockEntity` (не strip тактик). Крестьяне — тот же `AI_LockSquad`; в нативе нет фильтра по типу. После Enable C++ RPM читает tracking-карту `AI+0x1000` (ключ = **Squad_GetID**, не radar id): нет объекта → 4CE0; `+0x40 != 0` → no-op; `+0x40 == 0` → skip (иначе 4A70). Карта публикуется в `AOE4HOOK_AI_LOCK.strip` через world snapshot. Sel/group/garrison читают её. Cache-spawn после Enable не зовёт натив. Разведчиков не лочим. Сессия лочит стоящую армию **до** `AI_Enable`. Новые боевые — Relic `GE_EntitySpawn`. См. `AI_UNIT_CONTROL.md`.

### 5.6 i18n правится руками

`ui_i18n.cpp` — бинарный поиск по отсортированным парам. Новую пару вставлять в `kPairs` руками, в отсортированную позицию, и зеркалить ключ в `gen_ui_i18n.py`. **Генератор не запускать**: его словарь отстал, регенерация удалит живые переводы (подробно — раздел о переводах выше). Смена английской строки без правки пары **теряет перевод**.

### 5.7 Профайлер: `(worker)` — не кадр

В FPS-профайлере строки с пометкой `(worker)` идут вне рендер-потока и на кадры не влияют. `collect_world (worker) 200 мс` при 100 FPS — норма. На этом легко сделать ложный вывод: значение имеет `present=` и итоговый FPS.

### 5.8 C2668: anonymous namespace vs `::MpBypass*`

В `mp_bypass.cpp` публичный API (`MpBypassDataClear`, `MpBypassAutoClearEnabled`, …) жил рядом с одноимёнными хелперами в anonymous namespace. MSVC **C2668**: неоднозначный вызов.

Фикс: хелперы `*Ns` (`DataClearNs`, `AutoClearEnabledNs`, `SetAutoClearNs`, `DataRestoreNs`, `MaybeDataClearNs`). Снаружи namespace — обёртки `MpBypass*` и вызовы `::MpBypassDataClear()` / `::MpBypassAutoClearEnabled()`. Поведение DualFlag не менялось. **Не** возвращать старые имена хелперам.

### 5.9 Клик по сайдбару в том же кадре, что кнопка вкладки

`DrawNativeOverridesTab`: клик **Лобби → Память** ещё зажат, когда рисуется **«Переподключить серверы»** → `LoginAsync` `0x3109420` в меню. Три кадра `BeginDisabled` / `inputLive`; лог `[MEM] Memory tab opened — ignore clicks 3 frames (no LoginAsync)`.

Шапка `RA S%u A%llu F%u` читает `MpBypassGetWindowSnapshot()`, не SCAR. Красная **Офлайн** — `ScarTrustGet() == ScarTrust_Offline`.

### 5.10 Present и оконный поток трогают одно и то же состояние

Два потока гоняют один и тот же код: `ArmyRelockTick` живёт внутри хука
Present (`hooks.cpp` → `ToolkitSlabsService` → `StkLuaLockTickAfterCollect`),
а `StkLuaLockHandleArmyRelock` — на оконном потоке из
`WM_SCAR_ARMY_RELOCK`. Флаг `g_armyRelockPosted` их **не** разделяет: он
сбрасывается в конце оконного обработчика, а собственная проверка
`ArmyRelockTick` стоит уже после её вызова `PickRelockSid`.

Отсюда три правила.

**Контейнеры релока — только под `g_relockMapsLock`.**
`g_relockPoisonSids`, `g_relockNotArmy`, `g_relockSafeMiss`,
`g_relockSafeSince` — обычные STL, и одновременные `try_emplace` и `erase`
на одной `unordered_map` рвут список бакетов. Лок берётся **после**
`StkAiTrackCollect` (он медленный и контейнеров не трогает) и отпускается
до логирования; `SRWLOCK` не рекурсивный, вложенных захватов быть не должно.

**Скрипт на оконный поток едет в `lParam`, не в глобале.**
`SendMessageW` синхронный, поэтому буфер отправителя жив всю дорогу и
глобал не нужен. Когда он был, поток Present успевал присвоить в него
скрипт другой длины, пока оконный компилировал предыдущий: `std::string`
перевыделялась, старый буфер освобождался, и Lua-компилятор игры разбирал
освобождённую кучу. Одна посылка = один `ScarWindowExec` на стеке
отправителя.

**Причину отказа читать только через out-параметр.** `ScarLastDetail()` —
один общий `char[256]` на весь процесс, в него пишет каждый поток, который
трогает VM. Читать его *после* возврата из вызова нельзя: получишь чужую
причину. У кого решение зависит от причины — травля отряда в армейском
локе, парковка актуатора — тот обязан звать
`ScarExecuteOnWindowThread(script, lean, detailOut, detailCap)`; копия
снимается на оконном потоке сразу после скрипта. Логировать причину можно
и по-старому.

**Present не ждёт бесконечно ничего.** Отправка на оконный поток идёт через
`SendMessageTimeoutW` с `SMTO_ABORTIFHUNG` и потолком 2000 мс (самый
тяжёлый легальный скрипт, `ai_lock_army.lua` на 32 КБ, укладывается в
442 мс). После таймаута диспетчер держится 5 с и отказывает сразу — иначе
последовательность включения ИИ из восьми скриптов отстояла бы восемь
таймаутов подряд и замёрзла дольше, чем без потолка вообще.

Два следствия, без которых потолок был бы хуже болезни. Первое: таймаут
`SendMessageTimeoutW` **не отменяет сообщение** — оконный поток может забрать
его потом, поэтому запрос живёт в куче со счётчиком ссылок, а не на стеке
отправителя; освобождает тот, кто закончил последним. Второе: причина
отказа при таймауте — строка `window thread timeout`, в ней нет `SEH`, и
путь релока честно считает это отказом, а не фолтом. Именно поэтому
ограничивать отправку было нельзя, пока причина не переехала в буфер
вызывающего: до этого таймаут был неотличим от фолта и травил бы отряды.

**Зависший Present сам себя называет.** `PresentExceptionFilter` печатает
стадию при фолте, но при *блокировке* не печатал никто: и таблица FPS, и
heartbeat оверлея пишутся из Present, так что когда он встаёт, лог просто
обрывается на середине. `HooksPresentWatchdogTick()` крутится на уже
существующем 4 Гц цикле писателя журнала (`match_journal.cpp`), и если
Present не заходил 3 с — пишет `[PRESENT] stalled … at stage=…`, а при
возврате `[PRESENT] resumed after …`. Читать лог по принципу «последняя
строка и есть виновник» нельзя: она может быть от рабочего потока.

Стадии мало: первый же реальный зависон дал `stage=ui.present`, то есть
«где-то в отрисовке оверлея» — на 4000 строк кода. Поэтому сторож ещё и
снимает сам поток: `SuspendThread` → `GetThreadContext` → RIP плюс скан
первого килобайта стека на адреса возврата, попадающие в исполняемые
страницы образов, → `ResumeThread`, и **только потом** запись в лог.
Порядок обязателен: у замороженного потока может быть загрузочный лок или
лок самого лога, и запись при живой заморозке повесила бы сторож о тот
поток, который он описывает. Адреса печатаются как `модуль+0x…`, этого
хватает, чтобы найти функцию в дизассемблере:

```
[PRESENT] stalled 3156 ms at stage=ui.present …
[PRESENT]   rip  ntdll.dll+0x9F344
[PRESENT]   ret  InternalInjector.dll+0x1A2B40
```

---

## 6. Как проверять до сборки

**Встроенный Lua** — выгрузить литерал из `.cpp` и прогнать парсером:

```bash
python -c "from luaparser import ast; ast.parse(open('script.lua').read())"
```

Скрипты, нарезанные на куски (соседние `R"STK(...)STK"` одной константы, `stk_embedded.cpp`), сначала склеить — по отдельности они не парсятся by design. `probe.scar`, `dump_vm.scar`, `twd.scar`, `macro_bridge.scar` в C++ больше не копируются: запасной текст берётся из canon RCDATA (`CanonEmbedReadText`), проверять сами файлы в `sdk/`.

**Нативы** — сверить с каталогом `sdk/scar/checksum_wrappers.scar`: секция `block` означает sim-запись и рассинхрон, `ok` — чтение.

**Сборка / инжект**:

```
MSBuild internal\AOE4HOOK.sln -t:InternalInjector -p:Configuration=Release -p:Platform=x64
```

`DllInjector.exe` в `internal\x64\Release\` грузит `InternalInjector.dll` рядом. По умолчанию выходит после APC; `--watch` ждёт RelicCardinal. `Release` и `Release_fowctrl` — те же фичи, разный OutDir. Если Release залочен — инжектите `x64\Release_fowctrl\`.

`LNK1104` значит, что DLL держит запущенная игра или `DllInjector.exe` (если инжектор ещё жив с `--watch`).

---

## Связанные документы

| Файл | О чём |
| --- | --- |
| `AI_BOT.md` | Вкладка AI BOT целиком |
| `AI_SCORING_PIPELINE.md` | Relic multiply-list, eco-zero, `__EcoAct`, observatory |
| `decisions/ADR-001-cpp-ai-runtime.md` | C++ думает, SCAR применяет |
| `AI_SESSION_HANDOFF.md` | Сессия, стадии инжекта, история крашей |
| `AI_UNIT_CONTROL.md` | Подгруппы, гарнизон, HUD AI BRAIN, монахи |
| `NATIVE_FEATURES.md` | Lobby / Memory, LoginAsync, Search CD, реле, unofficial rejoin, Save/Load vs AI, C2668 |
| `CPP_BRIDGES.md` | Контракт моста, `AOE4HOOK_AI_SETTINGS`, `AOE4HOOK_AI_PLAN` |
| `HYBRID_NATIVE_AUDIT.md` | Гейты Fine-tune / Cancel / scoring |

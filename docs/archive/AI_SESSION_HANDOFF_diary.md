# Handoff: AI BOT session (для следующего агента)

Дата: **2026-09-06** (песочный MP + контрпик C++ / `WM_SCAR_AI_COMMIT`). Репозиторий: `AOE4HOOK`.
Это **продолжение текущей работы**, не новый дизайн с нуля.

**MP 2026-09-06 (neutralize OFF):** две песочные игры на `16.3.11308.0` доехали до победы.
RA-окно не выделялось (`lastSlots=0`), DualFlag держался `0x0001`. Конфиг
`ra_neutralize=0` / `session_hold=0`, `slotSkip=0`. Это не тест `.text` neutralize.
Подробности и FPS: `docs/UPDATE_GUIDE.md` §9.5.

Прочитай этот файл целиком **до** правок. Затем сверься с кодом — источник правды:
`internal/InternalInjector/ai_session.cpp` + `ai_runtime.cpp` + `ai_production.cpp` +
`ai_counter_math.h` + `stk_lua_lock.cpp` + `stk_ai_track.cpp`.
`docs/AI_BOT.md` §3.1 / §3.4 и `docs/AI_SCORING_PIPELINE.md` должны совпадать:

- **слот** (`Game_AIControlLocalPlayer` если ещё не AI-игрок) + standing lock **в одном** ScarDoString, затем `AI_Enable` **без** повторного Control;
- новые боевые через Relic `GE_EntitySpawn` (4CE0);
- RPM skip 4A70 (`AI+0x1000` / `Squad_GetID` / `+0x40`);
- без Relic TimeRule `__ArmyLock_Tick` и без `AI_LockSquads` после Enable;
- контрпик: C++ на snapshot, SCAR только `__EcoAct_Apply` через **PostMessage** `WM_SCAR_AI_COMMIT`. Lua `__EcoCounter_Tick` мёртв.

Production scoring vs PushScore vs personality: `docs/AI_SCORING_PIPELINE.md`.
ADR: `docs/decisions/ADR-001-cpp-ai-runtime.md`.

---

## Кто пользователь и что он хочет

Вкладка **AI BOT** = одна сессия:

- Кнопка **Enable AI / Disable AI** (не «Eco AI» в UI; Relic — обычный встроенный ИИ).
- Relic ведёт экономику. **Игрок командует армией.** Крестьян **не** лочить.
- Disable: **все** юниты и здания возвращаются игроку (не только army lock).
- Опциональный **контрпик** — три галочки: юниты / здания / развитие. Если Off — Relic играет от своих данных.
- C++ только сессия + UI + **think** (`ai_runtime` / `ai_production`). Relic-нативы на **оконном потоке игры**. Present: `PostMessage(WM_SCAR_AI_COMMIT)` / `WM_SCAR_ECO_CONTEST`. Lean session / locks: `ScarExecuteOnWindowThread` (`SendMessageW`). **Не** ScarHelper. **Не** DoString катов из Present.

Язык UI: английские ключи + русский через `UiTr` / `UiTrVisible`. **Не** `UiTr` на видимый статус без `UiTrVisible` — иначе получится `Выкл###Off`.

Игра: Age of Empires IV **16.3.11308.0**. Настройки: `Documents\AOE4HSettings`.

Против людей / рейтинг = **десинк** (Enable AI пишет AIWorldData). Это известно и не «баг».

Флаг **wanted** сессии **не** персистится: после рестарта оверлея кнопка Off. Галочки контрпика, сложность, слайдеры — в `config.ini` `[scripts]`.

---

## Поток / известные AV (не ломай)

1. `Game_AIControlLocalPlayer` только на **потоке Relic**, всегда `pcall`. Конкретно — `ScarExecuteOnWindowThread` (`SendMessageW` на оконный поток игры). **Не** ScarHelper: тот путь падает всегда (см. раздел про краш). **Не** прямой вызов из Present-хука.
2. Не грузить `hybrid_core` / `hybrid_o_*` с кнопки AI BOT.
3. Пока сессия On — **не** лочить крестьян массово (`StkLuaLockSetVillagers` только off при handover). **Исключения:** подгруппы (`StkGroupLockOnAssign`) и лок выделения (`StkSelLockTick`) — игрок сам указал этих крестьян.
4. Не стартовать инжект вне матча. Lean-сессия: `ScarIsReady` + `ScarLeanScriptsAllowed` (без +2 с `kScarStartConditionsMs`). Files / hybrid с `Rule_*` по-прежнему ждут `ScarUserScriptsAllowed` (~2 с после live-VM).
5. Lua 5.1: **нет `goto`**, нет `bit32` как в 5.2.
6. `kPairs` в `ui_i18n.cpp` — binary search. **Не** править `ui_i18n.cpp` руками. Меняй `gen_ui_i18n.py`, затем `python gen_ui_i18n.py` в `internal/InternalInjector`.
7. Не воссоздавать `AOE4HOOK\plugins`, `AOE4HOOK-SCAR-Plugins`, `Documents\ScarScripts`.
8. Не редактировать план `c:\Users\Lanzerxyz\.cursor\plans\ai_bot_eco_session_adde9640.plan.md`.
9. Не спамить SCAR-вызовы из `AiSessionService` каждый кадр: флаги/модуль — один раз, PLAN не чаще 10 с и **вообще не** из сессии пока `AiRuntimeArmed()`. Present для катов — только `PostMessage(WM_SCAR_AI_COMMIT)`. (Историческое: `ScarExecuteHelperThread` держал `WaitForSingleObject` до 10 с на Present и давал FPS ~6; сессия с него ушла, но правило «не каждый кадр» остаётся.)

---

## Сборка

```
MSBuild: C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe
Solution: internal\AOE4HOOK.sln
Target: InternalInjector, Configuration=Release, Platform=x64
```

Выход:

- `internal\x64\Release\InternalInjector.dll`
- Инжектор: `internal\x64\Release\DllInjector.exe` — грузит `InternalInjector.dll` **рядом с собой**
- Рядом: `InternalInjectorStub.dll`, `BridgeWatch.exe`

`Release` и `Release_fowctrl` — **одинаковые фичи**, разный `OutDir`. Если DLL залочена живым инжектом — соберите в другой OutDir, не мешайте две копии в одном процессе.

`DllInjector` по умолчанию **выходит после успешного APC**. `--watch` / `-w` ждёт выхода RelicCardinal.

i18n:

```
cd internal\InternalInjector
python gen_ui_i18n.py
```

---

## Цепочка инжекта (актуальная, 2026-09-03)

Кнопка Enable **только взводит** `g_wanted`. Инжект в `AiSessionService` (pump из `ui.cpp` каждый Present).

После матч live (`ScarIsReady` + `ScarLeanScriptsAllowed` — **без** +2 с Files-гейта):

| Шаг | Когда | Что |
| --- | --- | --- |
| 1 | +**start delay** | **Слот + army lock**, затем think: `Game_AIControlLocalPlayer` (если `AI_IsAIPlayer` ещё false) + `AI_Enable(false)` + standing `AI_LockSquad` в одном `ai_lock_army.lua`; затем `eco_ai_on` = `AI_Enable(true)` + `AI_SetDifficulty` + `Game_EnableInput` **без** повторного Control. Статус: `AI on. Army locked for you.` |
| 2 | ещё +**1 с** | Если любая галочка контрпика: `AiRuntimeSetArmed` + `PostMessage(WM_SCAR_AI_COMMIT)` → install `__EcoAct_*` на оконном потоке. Статус: `AI on. Counterpick attached.` Если галочки Off — шаг пропускается. |

И первый, и повторный Enable лочат стоящую армию **до** `AI_Enable` в том же `AiSessionService`, **после** слота и **без** Control после лока. `g_liveOnceThisMatch` только для лога (Disable его не сбрасывает). Staged-пауза после Enable — краш 01:07; стоящий `__ArmyLock_Tick` при живом ИИ — краш 02:13; Control **после** лока — армия уезжает к Relic (лог 22:39).

Константы в `ai_session.cpp`:

- `g_startDelayMs` — **настраиваемая**, дефолт **1000**. Слайдер «Start delay» на вкладке (1..15 с), ключ `[scripts] ai_start_delay_sec`. **1 с на слайдере ≈ 1 с** до `AI_Enable`, если VM уже live.
- `kAiSessionBridgeDelayMs = 1000` (контрпик после Enable)

**Не** лочить стоящую армию *после* `AI_Enable`. Старый порядок (ИИ 5–10 с, потом `AI_LockSquad`) давал `rva=0x2A45959` / `av_addr=0x58` на Disable→Enable: ИИ успевал повесить тактики, лок их сносил, следующий тик читал NULL+0x58. **Не** звать `Game_AIControlLocalPlayer` *после* standing lock: слот пересоздаётся, `+0x40` сбрасывается, spawn-watch помечает всю армию как «уже видел» и не лочит снова. Повторный Enable: слот (если нужно) + лок в одном чанке, затем только `AI_Enable(true)`.

`kScarStartConditionsMs` (**2000 мс**, `scar.cpp`) остаётся для overlay-скриптов с `Rule_*` (Files AUTO / hybrid). Lean `AI_Enable` / STK-локи его **не** ждут (`ScarLeanScriptsAllowed`). Если мир / Scenario Lua ещё не ready, слайдер всё равно подождёт VM — это не «+2 с сверху».

UI на вкладке: `Starting in %u s` → `Counterpick in %u s` → статус live. «Army lock in %u s» больше не показывается — лок входит в шаг 1.

`AiSessionWantsWorldCache()` = `wanted && ecoLive`. Collect юнитов нужен **spawn-watch** даже без контрпика. `PublishPlan` сессии **пропускается** при `AiRuntimeArmed()`. `__EcoAct_*` / `PostAiCommit` ждут `AnyCounter()`. World-feed может всё ещё публиковать PLAN для SWM.

Hotkey army/villager lock без сессии поднимает тот же collect через `StkLuaLockArmyLive() || StkLuaLockVillagersLive()` (`radar.cpp` `stkLock`).

Порядок кадра (`hooks.cpp` `firstThisTick`): `AiSessionService` → **`RadarWorldService` (collect)** → `ToolkitSlabsService` → `StkLuaLockTickAfterCollect`. Spawn-watch **после** collect, иначе видит прошлый кадр. При `AiSessionLive()` cache-diff только логирует skip — лок новых боевых это EventRule.

**HUD:** `d.aiPlan` = feed/coach/macro/session **или** `AiSessionWanted() && AiHudWantsPlan()`. Если добавите ещё одного потребителя снапшота — не забудьте про ту же строку.

`PublishPlan()` после live — **no-op** пока `AiRuntimeArmed()` (C++ уже думает на snapshot). Fallback `kPlanIntervalMs` 10 с только если runtime выключен и нет `RadarWorldFeedActive()`. `PublishPlan(true)` в момент attach тоже не шлёт blob при armed.

Army lock зовётся **до** `AI_Enable` в том же кадре, что шаг 1, и **после** слота в том же Lua-чанке. `MaintainArmyLock` после live **не** сканирует стоящую армию (это и был краш Disable→Enable). `eco_ai_diff` тоже без Control — смена сложности не должна сносить локи.

---

## Почему так (баги, которые уже ловили)

### FPS ~6.6 Present

Профайлер: Present 6.6, спайки 120/120, `ScarDoString` label `eco_ai_counter_flags` по **~130–140 мс каждые ~150 мс**.

Причина: после live `AiSessionService` каждый кадр звал `InjectCounterFlags()` → Helper с `WaitForSingleObject` на Present.

Исправление: флаги/модуль **один раз** (и при смене галочек), не каждый Present. PLAN максимум раз в 10 с.

**Не возвращай** per-frame `InjectCounterModule` / `InjectCounterFlags`.

`collect_world ~80 мс` — воркер (`radar observer alerts twd scar-feed journal`). Это не тот же баг, что 6 FPS Present.

### Краш на старте матча — причина в ScarHelper (2026-09-01)

Две гипотезы оказались **неверными**, обе стоили теста в матче. Записываю их, чтобы не проверяли третий раз.

**Гипотеза 1 (неверна): «слишком много Helper в одном кадре».** Задержки поднимали 3–4 → 4 → 6 с, разбили на 3 шага — краш остался, всегда на ~8-й секунде.

**Гипотеза 2 (неверна): «272 КБ бутстрапа».** `ScarHelperRaw` звал `ScarAcquireLiveScript(script, quiet=false)` → `ComposeOverlayScar` приклеивал `local_rules.scar` (128 КБ) + `checksum_wrappers.scar` (141 КБ), и `eco_ai_on` уходил как 272850 Б. Добавили `lean` — размер упал до **1548 Б**, и краш остался **идентичным до регистров**: тот же `rva=0x2AEE1F8`, `av_type=1`, `rcx=0`, `rsi=15`. Размер был ни при чём.

**Настоящая причина: сам путь ScarHelper.** Пролог хелпера (RVA `0xB7F150`):

```
48 89 5C 24 08   mov [rsp+8], rbx
57               push rdi
48 83 EC 30      sub rsp, 0x30        ; rsp = R-0x38
48 8B D9         mov rbx, rcx         ; arg
48 8B 4C 24 38   mov rcx, [rsp+0x38]  ; = [R] = АДРЕС ВОЗВРАТА
E8 ...           call D02C
84 C0 / 74 42    test al,al / jz
```

Хелпер читает **свой адрес возврата** и валидирует вызывающего — ровно то, о чём предупреждает комментарий в `scar.h`: *«D02C(retaddr) skips overlay RA»*. Но `ScarHelperRaw` делал `CreateThread` на **нашу** обёртку `ScarHelperThreadProc`, которая уже звала хелпер — значит retaddr всё равно внутри `InternalInjector.dll`. Плюс свежий `CreateThread`-поток не имеет потокового состояния Relic → `rcx=0` и запись по мусорному адресу.

**Helper-путь не отработал НИ РАЗУ за всю историю лога:** `grep -c "ScarExecuteHelper: done ok=1"` → **0**. Все вызовы — AV по одному адресу.

**Фикс:** сессия и STK-локи переведены с `ScarExecuteHelperThread` на `ScarExecuteOnWindowThread(script, lean=true)`.

Почему это правильный путь:

- `SendMessageW(WM_SCAR_EXECUTE)` выполняет код на **оконном потоке игры** — поток Relic с живым SCAR/Lua-состоянием. Это **не** вызов из Present-хука.
- `bridge` идёт этим путём — **ok=1 × 23** за один матч.
- `ScarTakeAiControl` (`scar.cpp`, метка `AiPlayerForYou.scar`) гоняет **те же самые нативы** (`Game_AIControlLocalPlayer` + `AI_Enable` + `AI_SetDifficulty` + `Game_EnableInput`) через `ScarExecuteOnWindowThread` — и так было всегда.
- Побочно снимается запрет №9: больше нет `WaitForSingleObject` на 10 с в Present.

`lean=true` оставлен (композиция без бутстрапа, но `WrapScarCompileSafe` сохранён — синтаксическая ошибка не поднимет фатальный диалог «SCAR — execution suspended»). Бутстрап сессии не нужен: `AOE4HOOK_Local` / `AOE4HOOK_Safe` в её скриптах не встречаются, а `checksum_wrappers.scar` в шапке сам себя зовёт *«Advisory catalog only»*. Остальные (`ui.cpp` Files Run, hybrid, ai_builder) бутстрап получают как раньше.

`MatchReady()` больше не требует `gameScarHelper` — это была мёртвая связь с неработающим путём.

В логе искать `ScarExecute: one-shot len=... lean=1` (оконный путь), а **не** `ScarExecuteHelper: CreateThread`. Подтверждено в матче 2026-09-01.

### Краш `rva=0x2A45959` / `av_addr=0x58` — один натив, три сценария

Think-поток: геттер `0x2924350` вернул 0, `mov ecx, [rax+58h]` без NULL-check. `AI_LockSquad` без tracking → очередь 4CE0 (безопасно); с tracking и незалоченным объектом → 4A70 (strip тактик) → этот AV на следующем think.

**Сценарий A — Disable→Enable, лок через ~10 с (лог 01:07).** Коммит `4864ebf` правильно забрал армию в том же `AiSessionService`, что `eco_ai_on`. Неправильно: порядок `AI_Enable` затем `AI_LockSquad` и первый Enable оставлен на staged-паузе. Слитый фикс: лок **до** `AI_Enable` на каждом Enable.

**Сценарий B — стоящий `__ArmyLock_Tick` при живом ИИ (лог 02:13).** Тот же RVA без Toggle. `4864ebf` оставлял тик навсегда (idle вместо `Rule_Remove`) — это и есть 4A70 по уже трекаемым сквадам. Слитый фикс: тик снимается.

**Сценарий C — C++ cache-spawn после Enable (лог 22:49, повтор 23:10 на slot-fix DLL).** Кэш позже спавна → `AI_LockSquad` идёт в 4A70. Live RPM pid 52828: карта `*(AI+0x1000)+0x30` ключуется **Squad_GetID (~50xxx)**; radar/TLS id (~1e9) в этой карте не находится. Classify(radarId) давал ложный Safe4CE0. Слитый фикс: cache после Enable **не** зовёт натив; skip-таблица и `AOE4HOOK_AI_LOCK.strip` — ключи Squad_GetID из карты (world snapshot / `AOE4HOOK.WouldStrip`). Sel/group/garrison/lockOne не зовут натив по would-strip. DIY `+0x40` без 4A70 think не skip'ает (0x2923300 требует пустой tactic stack).

Полный разбор: `docs/AI_UNIT_CONTROL.md`, «Главный краш». **Не** гасить тактику `SCMD_Stop` и **не** ловить AV через `pcall`.

---

## Подгруппы, гарнизон и выделение крестьян

Полная дока: **`docs/AI_UNIT_CONTROL.md`**.

**Лок выделения** (`ai_sel_lock`, default On): выделенные `scar_villager` → `AI_LockSquad` **только если tactic stack пустой** (нет tracking → 4CE0; tracking + idle stack → лок без strip). Живая тактика (`WouldStrip`) — **не** звать натив; тик каждые 300 мс и ещё **15 с** после deselect. Лог: `sel skip-live sid=` затем `AI_LockSquad sel sid=`. После Enable это **не** no-op: раньше skip по «уже tracked» оставлял крестьян ИИ. Combat / scout / AI relic-monk не берём. C++ тик, без TimeRule. SWM `TickManualSelectionControl` в lean-сессии не живёт.

Гарнизон **работает** (подтверждено 2026-09-01): `[AOE4HOOK-GAR]|tick=14|scanned=8|ents=3|squads=3`. Ключ был в стороне опроса — `Entity_IsHoldingAny` на зданиях не срабатывал ни разу (`scanned=18, ents=0`), заработало через `Player_GetSquads` + `Squad_IsInHoldEntity`.

Чтение выделения для подгрупп прошло три итерации, две первые провалились молча:

1. RPM `ReadUiSelectionIds` (HUD+0x198 vec+0x3A0) — `n=0` на этой сборке.
2. `Misc_GetSelectedEntities` — `sel=0`.
3. Каскад: `Misc_GetSelectedSquads` → `Misc_IsSquadSelected` пообъектно → `Misc_GetSelectedEntities` → `Misc_IsEntitySelected`. Трассировка сообщает `via=`, каким способом получилось.

### Ловушка: фиксированный буфер под генерируемый Lua

2026-09-01. `StkGroupLockOnAssign` собирал скрипт в `char lua[6144]` через `_snprintf_s(..., _TRUNCATE, ...)`. Добавили зонд `busy=` — скрипт вырос до **6409 байт**, `_TRUNCATE` молча обрезал его посреди `end`, и игра показала:

```
[AOE4HOOK] compile: [string "local okP, player = ..."]:175: syntax error near 'if'
```

Обрезка **не логируется** — `_TRUNCATE` это не ошибка. Симптом выглядит как «сломался Lua», хотя Lua был корректен: выгрузка скрипта из C++ и прогон через `luaparser` дали `SYNTAX OK`.

Теперь размер считается из самого формата (`_scprintf`) и пишется в `std::string` — обрезка невозможна. **Не возвращайте фиксированные буферы под растущие скрипты.**

Диагностика, если снова увидите `compile:` с номером строки: выгрузите литерал из `.cpp`, соберите Lua, прогоните `luaparser`. Если он говорит OK — ищите обрезку, а не синтаксис.

---

### ОТКРЫТЫЙ РИСК: краш при локе занятого отряда

2026-09-01, 15:22:29. Сценарий: разведчик под управлением ИИ выполнял приказы движения, игрок положил его в подгруппу, затем сбил приказы — краш.

```
15:22:28.838  ScarDoString end label=ai_group_lock.lua ok=1
15:22:29.402  [CRASH] av_type=0 av_addr=0x58 rax=0 rva=0x2A45959
              scar=- scar_tid=0 in_call=0
```

**Краш вне SCAR-вызова**, через 564 мс после завершения скрипта. Это тик ИИ читает нулевой указатель по `+0x58` — похоже на висячую ссылку в плане ИИ на отряд, который у него забрали `AI_LockSquad`.

Почему army lock на Enable не падает так же: standing-скан идёт **до** `AI_Enable` (нет tracking → очередь 4CE0).

Hex-Rays 2026-09-02: **`AI_LockSquads` (inner `0x296D680`) всегда идёт в 4A70, если tracking-объект есть** — у него нет skip `[obj+0x40]`. Батч после Enable падает так же, как одиночный лок. `AI_LockSquad` (`0x296D2E0`) при уже залоченном (`+0x40 != 0`) — no-op.

Подгруппы при живом ИИ больше **не** зовут `AI_LockSquads` и **не** лочат combat/scout — только крестьяне + `AI_LockEntity` на здания. Гарнизон при живом ИИ лочит сквад/здание, только если это уже наша армия, группа, villager, или ИИ ещё выключен.

Не возвращать задержку после включения ИИ, интервал `__ArmyLock_Tick` на живом ИИ и `AI_LockSquads` после Enable.

---

## Контрпик (если галочки On)

Источник: C++ `AiPlanSnapshot` (`ai_planner` / `ai_combat` / `ai_counter_math`) —
`need[]`, MASS vs UPGRADE, smith/uni. Lua `_G.AOE4HOOK_AI_PLAN` для катов **не**
читается. Состав врага пока **role buckets**.

Три ключа `config.ini` `[scripts]` (default 0):

- `ai_counter_units`
- `ai_counter_buildings`
- `ai_counter_develop`

C++ pipeline (`ai_runtime.cpp`):

- `AiRuntimeSetArmed(true)` из `InjectCounterModule` / enable.
- Planner ~**2 с** (`AiRuntimeFastCompute`), иначе 10 с.
- Sample + `AiCounterComputePending` + hysteresis **35 с** (`kHoldSec`).
- Need-floor `maxNeed * 0.35` может **добавить** локи, не снять role cut.
- Present: `PostAiCommit` → `PostMessage(WM_SCAR_AI_COMMIT)`.
- Window: `HandleAiCommitPosted` — install `__EcoAct_*` один раз, затем lean
  `__EcoAct_Apply({gen, cuts})`. Skip unchanged generation.
- Галочки Off → `__EcoAct_Restore` (не ждать 35 с).
- `ITEM_LOCKED` общий слот: и Relic, и игрок не произведут залоченное.

Lua `__EcoCounter_Tick` / `kCounterOn` / `SAMPLE_SEC` **удалены**. Нет Relic
`Rule_AddInterval`. Lean-сессия не ставит `AOE4HOOK_Local`.

C++: collect для spawn-watch с шага 1 (`wanted && ecoLive`). `PublishPlan`
сессии no-op при `AiRuntimeArmed()`. `cap.fAi` в feed =
`worldFeedAiPlan || AiSessionWantsWorldCache()` — при Send to SCAR план может
уехать в Lua и без контрпика; HUD этого не требует. Observatories:
вкладка **Scoring observatory**, HUD **План / SCAR**.

Канон: `docs/AI_SCORING_PIPELINE.md`.

---

## Army lock (порядок = антикраш)

Файл: `internal/InternalInjector/stk_lua_lock.cpp` (`kArmyOn`).

Поведение:

- Сессия вызывает лок **до** `AI_Enable` в том же `AiSessionService` (первый Enable и повторный). Стоящая армия уходит игроку, пока у Relic ещё нет tracking.
- После Enable новые боевые — Relic `GE_EntitySpawn` (`Rule_AddPlayerEvent`, 4CE0 в том же тике). C++ spawn-watch при live-сессии **не** лочит cache-diff (radar id ≠ ключ карты). Would-strip публикуется как `AOE4HOOK_AI_LOCK.strip` / `__LockWouldStrip` (Squad_GetID). Worker-cache при villager-lock — skip. Relic EventRule fallback при пустом кэше ~3.5 с остаётся.
- Имена с `scout` (**Hippodrome Scout** / `dummy_champion_scout`, хан 1–2) не лочатся. **Hippodrome Horseman / Riddari** (`unit_dummy_champion_horseman_*` / `_knight_*`) — боевые, у игрока. У dummy PBG часто нет `scar_horseman`, лок идёт по имени.
- Обычные монахи: **не** `AI_LockSquad`, пока Relic их ведёт (тот же `AI_GetActiveTactic` NULL +0x58 / исторический `rva=0x2A45959`). Relic ИИ подбирает **реликвии** (`EntKind::Relic`), не `holy_site`. `__ArmyLock_GroundRelics` из кэша (лежащие, не святыня). `>0` или неизвестно — все обычные монахи у ИИ. `0` — лок **новых** на спавне навсегда (`__ArmyLock_PermMonk`). Уже бегущих за реликвией не трогать. Shaolin / warrior monk всегда игроку. Захват свободных святынь — hybrid `Cmd_AttackMoveThenCapture` (не lean-сессия; Safe не шлёт capture).
- Один скан стоящей армии при инжекте, и только если `AI_IsEnabled` ложь. **Нет** `__ArmyLock_Tick` TimeRule после Enable — standing `AI_LockSquad` по уже трекаемым сквадам это `rva=0x2A45959` (лог 02:13).
- Disable снимает lock, чистит spawn-seen и ставит `__ArmyLock_StandingScan`, чтобы следующий Enable снова прошёл стоящих.

Не вешать 35 с hysteresis контрпика на army lock. Не лочить виллов из сессии.

C++ retry стоящего лока после `g_ecoLive` **запрещён** — это тот же RVA.

---

## Disable / handover

`RunHandover` + `kHandover`:

- army lock off, villager lock off
- `AOE4HOOK_ECO_CPP = false` (`cppOwnsFlagRelease`) — hybrid AUTO / Files eco
  снова владеют своими слоями; `__EcoContest_Tick` возвращается из
  `__EcoContest_TickPrev` (enable паркует его за помеченным stub)
- `AiRuntimeSetArmed(false)` + `__EcoAct_Restore` (снимает семейные cuts,
  `lockPbg`, и `AIPlayer_PopScoreMultiplier` четырёх target-ключей id 1),
  сброс samples/live
- `AI_UnlockAll` + unlock сквадов и зданий (`AI_UnlockEntity`)
- restore `ITEM_DEFAULT` на затронутых BP
- `AI_Enable(false)` + `Game_EnableInput true`
- income desire / intentions / gatherer override не восстанавливаются — в
  `Essence_ScarFunctions.api` нет getter/clear натива

Не оставлять `AOE4HOOK_ECO_CPP=true` после handover: гибрид останется
выключенным до конца матча. Тест: `tests/adversarial/test_ai_handover.py`.

`StkClearVmModules` → `AiSessionOnVmReset()`.

---

## UI

`DrawAiSessionPane` в `ui_scar_lanes.cpp` (вкладка AI BOT = только эта панель).

- Enable / Disable (`Включить ИИ` / `Выключить ИИ`)
- Статус через `UiTrVisible`, не `UiTr`
- Три чекбокса контрпика всегда видны; live `AiSessionSetCounter`
- Если wanted: keep-camera, сложность, `DrawAiControls`, Save
- Scoring observatory collapsing header (`AiProductionGet`)

Старые Memory / Lua Features / Scar builder с вкладки **убраны**. Код в DLL ещё есть — не тащить обратно на AI BOT.

Tune после успешного шага 1: `AiSessionService` возвращает `true` один раз → `ui.cpp` может `AiCustomPushLive()`. Не возвращать `true` на шагах контрпика/army (повторный tune).

---

## Файлы сессии (трогать в первую очередь)

| Файл | Роль |
| --- | --- |
| `internal/InternalInjector/ai_session.cpp` | Сессия, задержки, `PostAiCommit` / `HandleAiCommitPosted`, handover |
| `internal/InternalInjector/ai_session.h` | API |
| `internal/InternalInjector/ai_runtime.cpp` | Worker think, `__EcoAct` installer / apply / restore |
| `internal/InternalInjector/ai_runtime.h` | `AiRuntimeSetArmed` / Peek / Mark |
| `internal/InternalInjector/ai_counter_math.h` | Pure cuts / role / ecoLock (host tests) |
| `internal/InternalInjector/ai_production.cpp` | Rank + observatory (`UnitProfilePickTrain`) |
| `internal/InternalInjector/ai_scoring_catalog.h` | ScarDoc factories + Relic hook names |
| `internal/InternalInjector/scar.h` | `WM_SCAR_AI_COMMIT` (`WM_APP+0x5346`) |
| `internal/InternalInjector/stk_lua_lock.cpp` | Army / villager lock Lua, spawn-watch, `StkSelLock*` (выделение крестьян), `StkGroupLock*`, `StkGarrisonLock*` |
| `internal/InternalInjector/stk_lua_lock.h` | `StkLuaLockTickAfterCollect`, army/vill live flags |
| `internal/InternalInjector/toolkit_slabs.cpp` | После collect зовёт spawn-watch |
| `internal/InternalInjector/hotkeys.cpp` | `PollControlGroupAssign` — детект Ctrl+0..9 |
| `internal/InternalInjector/ui_scar_lanes.cpp` | `DrawAiSessionPane`, галочка HUD, combo пресетов |
| `internal/InternalInjector/radar.cpp` | `ObserverDrawAiBrain` — панель `AI BRAIN` (рядом с MAP TRACKER) |
| `internal/InternalInjector/hud_drag.h` | слот `HudPanel::AiBrain` |
| `internal/InternalInjector/radar.cpp` | `WorldComputeDemand`, `cap.fAi`, demand why `ai-session` |
| `internal/InternalInjector/ai_planner.cpp` | `AOE4HOOK_AI_PLAN` |
| `internal/InternalInjector/unit_profile.cpp` | Каталог aoe4world, линии лучников (`keepArcherLine`) |
| `internal/InternalInjector/ui.cpp` | pump `AiSessionService` |
| `internal/InternalInjector/gen_ui_i18n.py` | ключи UI |
| `docs/AI_BOT.md` | общая дока вкладки |
| `docs/AI_SCORING_PIPELINE.md` | Relic multiply, eco-zero, `__EcoAct`, observatory |
| `docs/decisions/ADR-001-cpp-ai-runtime.md` | C++ думает, SCAR применяет |
| `docs/AI_UNIT_CONTROL.md` | подгруппы, гарнизон, HUD и **разбор крашей от `AI_LockSquad`** |
| `docs/AI_SESSION_HANDOFF.md` | этот файл |

Путь катов: Present `PostMessage(WM_SCAR_AI_COMMIT)` → `HandleAiCommitPosted` →
lean `HelperRunSoft` `__EcoAct_Apply`.
Путь Enable / locks: `ScarExecuteOnWindowThread` → `SendMessageW(WM_SCAR_EXECUTE)` →
`ScarExecuteUserScript(script, lean)` → `ScarDoStringRaw`.

`ScarHelperRaw` / `ScarExecuteHelperThread` (RVA `+0xB7F150`) остались в коде для других вызывающих, но **сессия ими не пользуется** — путь всегда падает.

---

## Нативы вкладки AI BOT (Hex-Rays 2026-09-02)

IDB: `K:\aoe4_dlc\7ff6f65c0000.RelicCardinal.exe.i64`, imagebase `0x7FF6F65C0000`. Lua-имена часто XOR; inner — RVA.

Краш `rva=0x2A45959`: `sub_7FF6F9005930` после геттера `0x2924350` делает `mov ecx, [rax+58h]` без NULL-check. `pcall` это не ловит.

| Native | Inner RVA | Для сессии | Краш-класс |
|---|---|---|---|
| `Game_AIControlLocalPlayer` | Lua C `0xC00090` → `0x696360` | **до** Enable, ставит слот в AI-список. Без этого `AI_Enable` не находит игрока | не 4A70; нужен живой GameWorld (`global+816`) |
| `AI_Enable` | `0x2975660` | байт `player+0x12F4` | think-гейт, тактики не сносит |
| `AI_SetDifficulty` | `0x294A390` | очередь лямбды 0..6 | нет |
| `Game_EnableInput` | `0xC000C0` | Keep camera | presentation, не lockstep |
| `AI_LockSquad` | `0x296D2E0` | standing до Enable; spawn-watch после | 4CE0 без tracking; 4A70 если tracking и `+0x40==0`; no-op если уже залочен |
| `AI_LockSquads` | `0x296D680` | **не звать после Enable** | tracking есть → **всегда 4A70**, skip `+0x40` нет |
| `AI_LockEntity` | `0x296CEB0` | здания / гарнизон | пишет `+120` в списке `player+4104`, не strip тактик |
| `AI_UnlockAll` | `0x296D090` | handover | снимает `+0x40`, восстанавливает тактики |
| Fine-tune (`SetPersonality`, desire, gatherer, intention, PushScore, …) | очередь `AI_DispatchOnPlayerId` | кнопки Fine-tune | throw на неизвестное имя intention/resource — `pcall` |
| `Player_Set*ProductionAvailability` | LuaLibPlayer | контрпик | sim-write / OOS vs humans, не AV |

Lean-сессия **не** ставит Relic TimeRules: контрпик и гарнизон тикают с C++; армия — spawn-watch. `UnsavedTimeRule_*` тот же список `LuaRules+0x20`, не обход serialize.

---

## Что ещё не сделано / проверить в игре

1. ~~Вход в матч без краша~~ — **ПОДТВЕРЖДЕНО в матче 2026-09-01, 12:02.** Все стадии `ok=1`, крашей 0:

   ```
   12:02:28.517  one-shot len=550 lean=1      <- ровно +6.0 с
   12:02:28.734  eco_ai_on       ok=1  1548 Б   (217 мс)
   12:02:33.524  ai_lock_army    ok=1  5422 Б   (6 мс)
   12:02:43.122  eco_ai_counter  ok=1 14500 Б   (3 мс)
   12:02:43.129  eco_ai_plan     ok=1  3674 Б
   ```

   Контрпик подтверждён и по данным: после подключения `bridge` вырос 8927 → 11761 → 12224 Б, т.е. `cap.fAi` включился и `AOE4HOOK_AI_PLAN` едет внутри world-snapshot каждые ~1.2 с. Контракт полей сверен: `comp{o, spear/archer/horse/maa/knight/xbow/siege, need{}, smith, uni, keepArch}` + `eco[id].mode` ↔ `pickRows` / `armyOf` / `ecoMode`.

   Диагностика на будущее: искать `ScarExecute: one-shot ... lean=1` и
   `thin actuator installed`. Строки `ScarExecuteHelper: CreateThread` для
   `eco_ai_on` быть **не должно**. Исторический лог выше ещё содержит
   `eco_ai_counter` / `eco_ai_plan` — это **старый** Lua-тик; сейчас apply =
   `eco_ai_act_install` / `eco_ai_cuts`, лог `obs gen=`.
2. Профайлер FPS: не должно быть стены `eco_ai_counter_flags` / `eco_ai_cuts`
   на каждом Present. Каты — `PostMessage(WM_SCAR_AI_COMMIT)`. Смотреть
   `FpsProfileGetPresentPercentiles` (p95/p99/1% low), не средний FPS.
   Песочная 3v3 2026-09-06: оверлей 1% low ~17, пики `svc_ai_session` +
   `ai_sel_pick`; поздняя игра ~52–58. `collect_world` 650+ ms — worker.
3. Контрпик: смена роли не чаще ~**35 с** (`kHoldSec`); planner ~**2 с** на
   worker. HUD **План / SCAR** (`generation / commitGen`). Не ждать Lua PLAN.
4. Army lock: standing-скан **до** `AI_Enable`; новые боевые — `[STK] spawn watch primed ...` затем `__ArmyLock_OnEntityId`. Relic fallback только если `[STK] spawn watch: Relic EventRule fallback`. Крестьяне и разведчики у Relic.
5. Disable: всё возвращается игроку.
5a. Disable → Enable в живом матче: лок снова **до** `AI_Enable` в том же вызове сервиса (краш 01:07). Слот (`Game_AIControlLocalPlayer`) **до** лока в том же `ai_lock_army.lua`, `eco_ai_on` **без** Control (лог 22:39: после Disable стоящая армия уезжала к Relic — Control шёл после лока, spawn-watch `primed self-units=N (no lock this pass)`). В логе: `[AI] session re-enable: slot+army lock (before AI_Enable)` до `eco_ai_on`, `[STK] army lock script ok slot=1`, без `[CRASH] rva=0x2A45959`. Не возвращать `__ArmyLock_Tick` на live ИИ (краш 02:13). Не возвращать `AI_LockSquads` после Enable (inner `0x296D680` всегда 4A70 при tracking).
6. ~~Обновить `docs/AI_BOT.md` §1 / §3.1 / §3.4~~ — C++ runtime, `WM_SCAR_AI_COMMIT`, без `__EcoCounter_Tick`.
7. ~~Hint контрпика в UI~~ — «Samples every 10 s, holds 35 s». Фактический sample = planner cadence (~2 с armed), hold = 35 с.
8. **`lean` больше не врёт про бутстрап (исправлено).** `ScarDoStringRaw` ставил `g_localRulesSent` / `g_checksumCatalogSent` на любом успешном не-quiet вызове, включая `lean`-вызовы, которые бутстрап **не отправляют**. Из-за этого сессия на старте матча помечала бутстрап установленным, и следующий Files Run / hybrid получал пустые `inst`/`catalog` — то есть работал без `AOE4HOOK_Local`. Условие теперь `if (!quiet && !lean)`.

9. **Мина `AiCustomPushLive` — переоценена вниз.** В `ui.cpp` (~5057) он зовётся **в том же кадре**, что и успешный шаг 1, и идёт не-lean путём (`ScarApplyAiTune` → `RunAiLuaWithCapture` → `ScarExecuteOnWindowThread` без `lean`) → тащит бутстрап 272 КБ. Сейчас спит: `g_aiTuneOnEnable` / `g_aiCustomEnabled` = `false`, все `ai_apply_*` в конфиге = 0. Стрельнёт, если включить «Re-apply Fine tuning after Enable» или «Enable custom template». Просто дать ему `lean` нельзя — `ai_tune` гейтится трастом (`ScarTrustLabelNeedsOffline`), а `lean` выкидывает trust-заголовок. Правильнее вынести его в отдельную стадию после army lock.
10. Бутстрап (`local_rules` + `checksum_wrappers`, 272 КБ) **ни разу не устанавливался успешно** ни в одном матче этого лога. Первый не-quiet вызов всегда получал его целиком. Сессия теперь идёт мимо (`lean`), но Files Run / hybrid / ai_builder по-прежнему потащат его — там он не проверен.

---

## Словарь

- **Мост** = world feed snapshot (`FormatScarSnapshot`) + `AOE4HOOK_AI_PLAN`. Не hybrid director.
- **Сессия** = `ai_session.cpp`, кнопка AI BOT.
- **Оконный поток** = `ScarExecuteOnWindowThread` (`SendMessageW` на поток окна игры). Рабочий путь сессии.
- **Helper** = `ScarExecuteHelperThread` (CreateThread + wait). Мёртвый путь: AV на каждом вызове.
- **Wanted** = кнопка On, инжект ещё может ждать матч/таймер.

---

## Чат, если нужен полный контекст

Cursor transcript: `50587851-8265-478c-a7c3-d0b28477a348`  
(полный JSONL в `agent-transcripts` этого workspace).

Пользователь пишет по-русски. Отвечать по-русски, идентификаторы кода — как в репо.

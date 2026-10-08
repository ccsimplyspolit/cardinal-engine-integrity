# Аудит SCAR/Lua оверлея против документации 16.3

Дата: 2026-09-24. База: `8742a761fb` + правки этого коммита.

## Что проверено

Все собственные скрипты: 43 файла (`sdk/scar`, `sdk/lua`, `sdk/NativeEspData`,
`sdk/aoe4hsettings/Scar Scripts`) и 117 Lua-литералов из C++ (~0.5 МБ:
`stk_lua_lock.cpp`, `ai_runtime.cpp`, `ai_session.cpp`, `stk_embedded.cpp`, …).
Разбор AST (luaparser) с учётом областей видимости; каждый глобальный вызов
(включая `pcall(F, …)` / `safe(F, …)`) сверен с:

- `sdk/scar/functions.json` — каталог 4423 имён, аргументы с пометкой `OPT_`;
- `sdk/scar/vm_census.json` — перепись живой VM (**Lua 5.3**: нет `loadstring`,
  `unpack`, `setfenv`, `bit32`, `io`, `os`, `debug`, `scartrace`);
- `sdk/scar/sga` — 845 скриптов Relic: реальная арность вызовов и определения
  Lua-функций (`player.scar`, `modifiers.scar`, `cardinal_scoring_functions.scar`).

Синтаксис: все 43 файла и все самостоятельные литералы парсятся; не парсятся
только куски, которые склеиваются в рантайме (`probe_scar.h`, `dump_vm_scar.h`
по частям, printf-шаблоны). BOM нет нигде.

Каталог не эталон по арности C-нативов: Relic сам зовёт `Modifier_Create` с 6
аргументами (в каталоге 4), `World_GetSquadsNearPoint` с 5 (в каталоге 4),
`Modify_WeaponDamage` объявлен с 4 параметрами (`modifiers.scar:910`, в каталоге
3). Сверять арность с вызовами в `sga`, не с `functions.json`/`_meta.lua`.

Все 321 вызов «отсутствующих в VM» `AIProductionScoring_*` — ложная тревога:
перепись снята без загруженного ИИ, фабрики существуют только внутри
production scoring context.

## Исправлено

**1. Запрет семейств в актуаторе ИИ не работал никогда.** `ITEM_*` в VM — это
userdata перечисления `Availability` (`ITEM_LOCKED = Availability(0)`,
`UNLOCKED(1)`, `REMOVED(2)`, `DEFAULT(3)`), а код проверял
`type(ITEM_LOCKED) == "number"` и падал в запасное `1`, то есть `ITEM_UNLOCKED`.
Мок в `test_ai_handover.py` задавал `ITEM_LOCKED = 1` и повторял ту же ошибку,
поэтому тесты молчали. Поведение по `AI_BOT.md:156–160` (галочка Unit, «и игрок
не произведёт заблокированное») теперь действительно включается.
Файлы: `ai_runtime.cpp` `__EcoAct_SetType` (установщик 59 → 60),
`hybrid_core.scar` `H.SetSquadTypeAvail`, `hybrid_c.scar` `lockType`.
**Отменено в тот же день — см. «Бой 24.09»: настоящий `ITEM_LOCKED` роняет
движок.** Теперь запрет семейств fail-closed (установщик 61).

**2. Поштучный запрет по PBG в `hybrid_core.scar` (`H.RestrictLowerTiers`)
отключён**, как уже отключён в C++ (`__EcoAct_ApplyPbg`): `BP_GetSquadBlueprint`
с именем из каталога ведёт к фатальному ассерту `rva=0x5961C7`, который `pcall`
не ловит. Запрета там всё равно не было (то же `1 = UNLOCKED`) — остался только
краш-риск.

**3. `risky_econ.lua`: `UI_ShowMessage` в VM нет** — обработчик ошибки
`OnUnitSpawn` сам падал. Заменено на `print`.

## Исправлено вторым заходом (владелец согласовал)

**A. Скрипты оверлея с 27.08 шли из Documents, а не из `sdk`.** По задумке
`DocsResolveExistingScarPathW` → `TryOverlayOwnedScar` сначала ищет `sdk`
рядом с DLL (`FindHookRoot`). Но `FindHookRoot` берёт путь из
`GetModuleHandleExW`/`GetModuleFileNameW`, а `ra_hide` (`UnlinkSelf`, с
`5f0e1f9b4f` от 27.08) вынимает модуль из списков загрузчика и затирает
`FullDllName`/`BaseDllName`. После этого путь пуст, `sdk` не находится, и каждый
системный, AUTO-, меню-скрипт, Lua оверлея и NativeEspData читается из копии в
`Documents\AOE4HSettings` — а её никто не обновлял. Доказательство: 23.09
`checksum_wrappers.scar ... (141758 bytes)` — это размер копии в Documents, в
`sdk` файл 141865 байт. Строка лога при этом всегда говорила «from Documents»,
какой бы файл ни читался. На 24.09 копии отставали: `hybrid_core.scar` 5010
строк против 8191, `twd.scar` 1282 против 1334, `NativeEspData` от 28–30.08,
трёх Lua-скриптов нет вовсе. Вывод для прошлых проверок: всё, что меняли в этих
`.scar` после конца августа, в бою не исполнялось, если файл не копировали
руками. Встроенный в C++ Lua (AI BOT, локи, Offline-кнопки) это не касалось.

Починка (слой скрытия не тронут): папка DLL запоминается в `DllMain`
(`DocsCaptureModuleDir`), пока загрузчик ещё знает модуль, и `ThisDllDir()`
берёт её из кэша. `DocsEnsureLayout` пишет `[Docs] overlay-owned scripts load
from <корень>` и обновляет существующие устаревшие копии в Documents (старые —
в `_arhive\overlay_copies_<время>\`, без бэкапа не перезаписывает, недостающие
не создаёт, переводы строк не считаются отличием), чтобы DLL, запущенная не из
репозитория, тоже получала актуальные файлы. Логи `[SCAR] … from <путь>` и
`[SCAR] <file> ok=… src=<путь|embedded>` называют реальный источник.
**Следствие:** со следующего инжекта игра впервые исполняет версии из `sdk` —
для гибридов, TWD, NativeEspData и скриптов меню это код, не проверенный в бою.

**D. Условия `Event_*` в `local_rules.scar` (`_v` 22 → 23).** Шимы получают
группу (SGroup/EGroup) или один отряд/объект, а условия звали
`Squad_IsUnderAttack(group)` без обязательного `time` и несуществующие
`Entity_IsSelected`/`Squad_IsSelected`: `under_attack`/`engaged`/`selected` не
срабатывали никогда, `out_of_combat` срабатывал сразу. Теперь семейство
определяется через `scartype` (как у Relic в `player.scar:330`) и зовётся
соответствующий натив: `SGroup_/EGroup_IsUnderAttack(g, ANY, t)`,
`SGroup_/EGroup_IsDoingAttack`, `Squad_/Entity_IsUnderAttack|IsAttacking(x, t)`,
`Misc_IsSGroupSelected/…`, `Player_CanSee{SGroup,EGroup,Squad,Entity}`. Время
по умолчанию 5 с (чаще всего у Relic); engaged = атакует или атакован (текст
документации); «не могу ответить» больше не считается «вне боя». Проверка
версии в `scar.cpp` и тесты обновлены; 9 lupa-тестов падают на старом коде.

**Fast Age.** 40000/0/40000 из `ff6f16ebf5` — намеренно (подтверждено
владельцем); тест и комментарий в `ai_production_math.h` приведены в
соответствие. Хост-набор впервые за день зелёный.

## Бой 24.09 14:22–14:51 (DLL 11:54) и третий заход

**Загрузка из sdk подтверждена в игре.** `[Docs] overlay-owned scripts load
from …\AOE4HOOK`, `refreshed 15 stale overlay copies in Documents (checked 36,
failed 0)` с бэкапом в `_arhive\overlay_copies_20260924_142219`,
`local_rules.scar from …\sdk\scar\local_rules.scar (135800 bytes)` (v23),
`checksum_wrappers … (141865 bytes)` — теперь размер из `sdk`.

**Регрессия от п.1 и её откат.** Первый же коммит актуатора
(`[AI] cuts gen=1 lock=auto ecoLock=1 … families_cut=7/7`, 14:31:56) упал:
`[SCAR] [SEH] ScarDoString code=0xC0000005 … label=eco_ai_cuts`, `actuator
parked after 1 SEH commits`. Весь матч без Layer B (желания дохода,
сборщики, намерения). 23.09 тот же `eco_ai_cuts` с дебютным «7/7» прошёл за 7
матчей десятки раз без AV, а между сборками в этом пути изменилось одно —
вместо `1` ушёл настоящий `ITEM_LOCKED`. Значит, до 24.09 натив либо отвергал
число, либо ставил UNLOCKED; реальный запрет AV-ит внутри движка. Вероятная
причина — список `BP_GetSquadBlueprintsWithType` содержит чертежи всех рас
(поштучные вызовы `ai_builder.scar` отдают один чертёж своей расы); адрес
падения не записан (VEH пишет его только в кольцо при `in_call`). Решение:
`__EcoAct_SetType`, `H.SetSquadTypeAvail`, `hybrid_c` `lockType` не зовут
натив вовсе и сообщают успех, чтобы поколение потреблялось и Layer B жил;
установщик 61; строка `[AI] thin actuator installed v61 (… family hard-cuts
off …)`. Галочка Unit из `AI_BOT.md` снова ничего не запрещает — как и было
всегда. Вернуть жёсткие запреты можно только новым механизмом (нулевые
скореры семейств в Layer A, как `ai_land_only.h`, или список, отфильтрованный
по расе игрока) и с проверкой в бою.

**Пункты 2–5 из первого отчёта о логе 23.09 сделаны:**
- Reveal Map (+11) больше не теряется: `ConsumeMemReveal` не сбрасывает флаг,
  пока SCAR не принимает пользовательские скрипты (`ScarUserScriptsAllowed`,
  `!ScarIsBusy`), оверлей тумана накладывается, когда выстрел прошёл.
- Отказ называет подворота: `[SCAR] skip user script: … why=<vm cooldown|no
  in-match world|lua reload settling|vm ready state|start-conditions floor|…>`,
  в деталях релока — то же (`ScarGateRefusal`).
- Сторож Present знает фазу кадра: «`not called for N ms … (loading,
  minimized or exiting)`» без снятия стека, если игра просто перестала звать
  Present (23.09 23:30:57 и 24.09 14:51:33 — выход); «inside the game's own
  Present (driver / GPU wait)» отдельно от блокировки в нашем коде. После
  фолта Present отметка жизни продолжает обновляться.
- Шум: `build_order skip: index.json unreadable` — один раз за сессию, не
  раз в 3 с; в окне лога (режим quiet) скрыты `MpBypass: data clear`, где ни
  одно значение не изменилось (1252 из 1253 строк за 24.09) — источник в
  `mp_bypass.cpp` не тронут, в файле лога строки остаются.

**Краш №1 повторился** (14:51:30): `rva=0x36A7E7F`, запись по нулю,
`tid=11228` (оконный поток), `in_call=0`, через 0.2 с — `match-end`. Причина
найдена в тот же вечер — следующий раздел. Скан Marks за 0.5 с до краша —
следствие конца матча (виджет миникарты уже разобран), а не причина; версия
про иконки радара снята.

## Краш №1 (`0x36A7E7F`): причина и починка (24.09 вечер)

**Это фатальный ассерт движка, а не случайный AV.** BugSplat кладёт дамп
каждого краша в `%TEMP%\release_16_3_0_rtm_x64*.dmp`: стеки потоков и 256
байт кода вокруг RIP. На `0x36A7E7F` стоит `call 0x3AE8210` (логгер ошибки) и
сразу `mov dword ptr [0], r15d` — так Relic роняет процесс. Аргументы:
`LuaConfig.cpp`, строка 1056, `"LUA -- luaconfig '%s'"`,
`EventRule_AddSquadEvent`. `.text` exe на диске зашифрован, а `.pdata`/`.xdata`
целы, поэтому поток раскручивается точно. Дампы 13.09 02:29 и 24.09 14:51 дают
один и тот же стек из 15 кадров, без наших кадров и без вызовов Lua:
`WinMain → … → 0x1802490` (выгрузка игры) `→ 0x1856420` («Shutting down game
event rule system») `→ 0x71CFC0` (разрушение вектора регистраций)
`→ 0x1880990` (деструктор регистрации) `→ 0x36A7B50` `LuaConfig::Unregister`
`→ 0x36A7E00` `GetType` → ассерт. Инструмент: `tools/relic_dump_stack.py`.

**Механизм.** LuaConfig держит свою таблицу на вершине стека главного
`lua_State` SCAR, и `Register`/`Unregister` это проверяют (строки 893 и 1056).
`Game_ScarDoString` возвращает вершину на место сама, но только когда сама
возвращается. Lua у Relic собрана на `setjmp/longjmp`. AV внутри натива,
которого вызвал наш чанк, раскручивается прямо до `__except` в
`ScarDoStringSeh` мимо эпилога DoString и мимо восстановления в
`luaD_pcall`/`luaD_rawrunprotected`. В `lua_State` остаются `top` и `ci`
мёртвого кадра, `errorJmp` на `jmp_buf` в снятом кадре, `errfunc`, счётчики
`nCcalls`/`nny`. Матч идёт дальше, потому что все вызовы относительны; «VM
retained» даже продолжает слать команды. На выходе снятие `EventRule_*` видит
на вершине не таблицу — ассерт. `errorJmp` в мёртвый кадр — вторая мина:
любая ошибка Lua вне `pcall` сделала бы `longjmp` в снятый стек.

**Совпадение по логам — каждый раз.** 24.09: `[SEH] ScarDoString … label=
eco_ai_cuts` в 14:31:56, краш в 14:51:30. 08.09
(`2026-09-08-heap-av-crash-class.md`): AV в `eco_ai_cuts` в 01:31, краш
`0x36A7E7F` в 01:52, «процесс прожил 20 минут». `AI_SESSION_HANDOFF.md`: relic
kick с AV каждые ~5 с и тот же краш на выходе. 23.09: 7 матчей без SEH и без
краша. `last_native=… relock` — устаревший крамб, как и установлено 08.09.
Два других дампа из `%TEMP%` — другие классы: 18.09 13:35 — фатал DX12
«Failed to Present … Device removed» (`rrToolsDX12.cpp:390`), 20.09 03:00 —
чтение строки по плохому указателю (`0x3EE01BA`).

**Починка** (`scar_lua_repair.h/.cpp`, `scar.cpp`). Перед каждым
`Game_ScarDoString` снимается снимок `lua_State` SCAR тем же путём, что у
самой DoString: `+0x12 mov rcx,[rip+d]` → `LuaSystemLookup(map,'SCAR')` →
`+0x18` → `+8`. Байты маршрута проверяются; если они другие, починка выключена
и лог это говорит. После SEH делается то же, что `luaD_pcall` на ошибке:
- открытые upvalue выше сохранённой вершины закрываются как в `luaF_close`;
  если значению нужен GC-барьер, upvalue закрывается как nil, при refcount 0
  отвязывается;
- возвращаются `top` (через смещение от `stack`), `ci`, `errorJmp`,
  `errfunc`, `nCcalls`, `nny`, `allowhook`.

Вызовов движка в самой починке нет. Смещения взяты из функций Relic 16.3, а не
из заголовка 5.3 — `stack` 0x30, `nCcalls` 0xC4 и `nny` 0xC6 от него
отличаются: `lua_pcallk` 0x3D10BE0, `luaD_rawrunprotected` 0x3D13DD0,
`luaF_close` 0x3D31D30. Снимок отказывается, если поля не похожи на
`lua_State`: `ci->func` вне `[stack, top)`, `allowhook` не 0/1, невыровненная
вершина. Лог при старте:
`[SCAR] lua repair armed: map slot rva=0x84CA6A8 lookup rva=0x36B2610`. После
каждого SEH: `[SCAR] [SEH] lua state repaired: top -N slots, ci restored,
errorJmp restored, upvals closed=… nil=… unlinked=…` или `NOT repaired:
<почему>`. Тесты: `test_scar_lua_repair.cpp` (поддельные
`lua_State`/стек/upvalue — восстановление, три случая закрытия upvalue, отказ
при вершине ниже снимка, перенос стека, санити снимка, декод маршрута по
байтам 16.3) и `LuaStateRepairWiringTests`.

**Проверено в бою 24.09 22:22–23:13:** 33 SEH восстановлены, выход без
краша — раздел «Бой 24.09 22:22–23:13» выше. Если в логе когда-нибудь
появится `lua repair off` — байты DoString после патча игры другие.

## Бой 24.09 22:22–23:13 (DLL 22:16): проверка починок

Сетевой матч, `standard_mode`, MapHack с 22:23:58, сессия ИИ весь матч.

**Краш №1 — починка подтверждена.** С 22:46:01 по 22:47:37 — 33 SEH
внутри `ai_lock_army_relock`, после каждого
`[SCAR] [SEH] lua state repaired: top -86 slots, ci restored, errorJmp
restored, upvals closed=1`, `NOT repaired` — ни одного. `Game Over` в
23:13:27, `match-end` в 23:13:32, игра вышла штатно: последняя строка
`warnings.log` — `Application closed without errors`, `[CRASH]` — 0, нового
дампа в `%TEMP%` нет. До починки первый же такой SEH гарантировал краш на
выходе. Маршрут до `lua_State` совпал с живыми байтами: `[SCAR] lua repair
armed: map slot rva=0x84CA6A8 lookup rva=0x36B2610`.

**Подтверждено попутно:** первый коммит актуатора `families_cut=7/7` прошёл
без SEH (запрет семейств fail-closed; днём здесь падал движок);
`consume +11 memReveal ok=1` при первом включении MapHack; сторож Present на
выходе — «`not called for 3047 ms … (loading, minimized or exiting)`»;
обновлены 4 копии в Documents с бэкапом.

**J закрыт по коду движка, без правок.** `Player_GetEntityCountByUnitType`
(0x19738C0) ищет тип через 0x36246E0; та делает `strlwr` имени, если сброшен
флаг `+9` глобальной таблицы строк (`&qword_86ABF18`, 0x3AE89F0). Флаг
инициализируется нулём (`word_86ABF20 = 0`), ~7000 мест его только читают,
писателя нет — поиск нечувствителен к регистру, `"Worker"` работает. Строка
зонда в лог не попала по другой причине (ниже), сам зонд безвреден.

**Новое:**
- **Шторм SEH в релоке.** 33 AV за 1,5 минуты. В чанк релока подмешаны
  религиозные цели (`AppendReligiousObjectives`: монахи к реликвиям и
  священным местам по id из кэша радара); первый AV — через 0,36 с после
  `ground relics=1 free sacred=0`, реликвии 1↔2. `NoteRelockSeh` без sid
  (`seh no sid`) ставит `g_relockSehAt`, и `ArmyRelockTick` уходит в режим
  догоняния — повтор раз в ~3 с вместо паузы. Адрес падения в файл не пишется
  (VEH для SEH внутри вызова пишет только в кольцо). Каждый SEH — раскрутка
  плюс синхронный сброс лога на главном потоке игры. Предложение: религиозные
  цели — отдельной меткой; без догоняния после SEH; парковка метки после 3
  SEH подряд; адрес падения в лог и для перехваченных SEH.
- **`print` не доходит до `warnings.log` в сетевой игре.** Ни одной строки
  `[STK]`/`[AOE4HOOK]` за матч, хотя чанки шли `ok=1`. Каналы на `print`
  (обратная связь выделения от 20.09, зонды) в таких матчах мертвы.
- **FPS** по `warnings.log`: 111–113 до MapHack, 102–104 после, 88–97 к
  концу. Микрофризы около 22:30 лог не объясняет; нужен профайлер
  (Debug → «FPS profiler» + «Log spikes»).

## Четвёртый заход (24.09 ночь): оставшиеся пункты, только безопасные

Правило отбора — урок `ITEM_LOCKED`: всё, что делает мёртвый вызов движка
живым или меняет значение/тип, уходящий в натив, считается новым непроверенным
действием, а не чисткой. Такие пункты отложены до проверки в бою.

**Сделано:**
- **B.** `hybrid_c.scar`: 22 константы (`RT_*`, `AGE_COST`, `INCOME`,
  `MODE_SCALE`, `AI_/MIL_/MONK_*`, `COUNTER_*`, `DIFF_*`, `MARKET`,
  `SCORING_API`, `ECON_TYPES`, …) переехали в одну таблицу `K` на своих
  местах и в том же порядке вычисления; удалены 4 функции без единого
  обращения (`BridgeOwnersCount`, `ArmyAhead`, `SlidingHold`,
  `NoteSelfDestroy`). Локалов верхнего уровня 196 → 171, свободных слотов в
  Lua 5.3 4 → 29. Проверено: ни одного затенения и ни одного обращения до
  объявления; настоящий Lua 5.3 компилирует; загрузка на заглушках API до и
  после проходит `Hybrid_Init` и определяет те же 59 глобалов. Новый
  `test_scar_compile.py`: весь `sdk` компилируется в Lua 5.3, в скриптах нет
  BOM, у `hybrid_c` и `spatial_world_model` не меньше 16 свободных локалов
  (сейчас 29 и 41).
- **F.** Над `LandmarkDarkAgeA/B` в `warmonger.lua` — пометка «16.3 не
  вызывает, пара Relic — `LandmarkRandomA/B` с китайской веткой»
  (у `Cavalry` пометка уже была). Переименование не делалось: это отдать
  выбор первого лендмарка профилю.
- **G (мусор в цепочках).** Удалены мёртвые ветки там, где у кода один
  источник: `sheep_herder.scar` — `Position_DistanceSquared`,
  `SGroup_AddSquad`, пустой вызов `World_SnapToPassable`; `hybrid_c.scar` —
  `getsimrate`. Отсутствие в VM проверено по переписи 16.3.11308.0 (5797
  имён), наши скрипты эти глобалы не определяют; живые запасные
  (`SGroup_Add`, `Misc_GetSimRate`, ручная дистанция) остались единственным
  путём, как и было.
- **I.** Удалены `eco_contest_scar.h`, `tools/_gen_eco_contest_h.py` и
  строка в `.vcxproj`: `kEcoContest` не подключался нигде, живой конкурс
  собирает `BuildEcoContestScript`.
- **J — зонд.** Разовая строка при старте сессии ИИ в `warnings.log`
  теперь кончается на `workers(Worker/worker)=N/M` (два read-only
  `Player_GetEntityCountByUnitType` для локального игрока). Теги типов в
  данных строчные (`|villager|worker|`), а `hybrid_core` (2 места) и
  `spatial_world_model` (1) спрашивают `"Worker"` и принимают 0 как ответ.
  Если N=0 при M>0 — регистр важен, заменить на `"worker"`; если N=M —
  закрыть пункт.

**Отложено как рискованное:** C (охрана имён перед `BP_GetSquadBlueprint`
меняет, какие имена доходят до натива), E (проверка места никогда не
работала — включить её значит впервые звать натив с настоящими аргументами),
H (перепись подтверждает, что числа равны перечислениям: `SCMD_Gather`=105,
`OT_Player`=0, `OT_Ally`=1, `ITEM_DEFAULT`=3 — замена поменяла бы только тип
аргумента), G «без замены» (`Player_IsGaia` → `World_OwnsSquad`,
`AITactic_AICommandSquadMove` — включает мёртвое поведение), `io.open`
в `stk_lua_lock.cpp` (переезд на `print`-канал включает мёртвые запросы).
Не тронуты из-за процесса, а не риска: мёртвые ветки в `combat_mods`,
`stk_lib`, `spawn` — их копии в `stk_embedded.cpp` генерируются из
Documents (`gen_stk_embedded.py`), а выигрыш косметический; `probe.scar`
перебирает `getsimrate`/`app_currenttime` намеренно — это зонд.

## Открыто — по важности

Исходный список третьего захода. Статус на 24.09 ночь — в разделах выше: B и
I сделаны, F помечен, G сделан в безопасной части, J закрыт по коду движка
(поиск типа нечувствителен к регистру); C, E, H и G «без замены» отложены до
проверки в бою.

**B. `hybrid_c.scar`: 196 одновременно живых локалов в главном чанке** при
лимите Lua 5.3 в 200. Четыре новых `local` на верхнем уровне — и файл не
скомпилируется целиком. Выносить в таблицы модулей.

**C. `BP_GetSquadBlueprint` с именами не из реестра** — тот же класс
`0x5961C7`: `ai_builder.scar:78`, `hybrid_core.scar:964`,
`macro_bridge.scar:153`, `spawn.scar:138`, `stk_lib.scar:216`. Relic делает это
безопасно: перебор `BP_GetPropertyBagGroupPathName(PBG_SquadProperties, id)`
(`combat_fitness_util.scar`) и вызов только с именами из реестра. Предлагается
общий `SafeSquadBP(name)` с кэшем множества имён.

**E. `hybrid_core.scar:5570`, `:5733`: `Player_CanConstructOnPosition(player,
ebp, pos)`** — сигнатура `(player, sgroupid, ebp, targetid, facing)`
(`player.scar:423`), вызов всегда падает в `pcall`, проверка места выключена.
Замена — `Player_CanPlaceStructureOnPosition(player, sgroup, ebp, pos, facing)`.

**F. Мёртвые хуки скоринга в `warmonger.lua`:** `ScoringFunctions_Cavalry`,
`LandmarkDarkAgeA/B` Relic 16.3 не вызывает; им соответствуют
`LandmarkRandomA/B`, но у Relic там особая ветка для китайцев
(`cardinal_scoring_functions.scar:1331`) — переименовывать только вместе с ней.

**G. Нативы, которых нет, без рабочей замены в цепочке:**
`AITactic_AICommandSquadMove` (`spatial_world_model.scar:5018` — разведка модели
мертва), `Player_IsGaia` (`spatial_world_model.scar:1307`,
`sheep_herder.scar:114/156` — есть `World_OwnsEntity`/`World_OwnsSquad`),
`getmapname` (`:5475`). С заменой в цепочке (просто мусор): `Squad_GetMaxHealth`,
`Entity_GetMaxHealth`, `SGroup_AddSquad`, `Position_DistanceSquared`,
`World_SnapToPassable` (результат ещё и отбрасывается), `getsimrate`,
`app_currenttime`, `os.clock`; `io.open`/`os.getenv` в `stk_lua_lock.cpp`
под guard — канал файлов в этой VM мёртв, работает `print`-канал.

**H. Сырые числа вместо перечислений** (значения верны, но это userdata):
`SCMD_Gather` → 105 (`kEcoOpen`, `ai_session.cpp:2213`, `eco_upgrades.lua:567`),
`OT_Player/OT_Ally` (`eco_upgrades.lua:413–414`), `ITEM_DEFAULT` → 3. Проверять
`X ~= nil`, не `type(X) == "number"`; для значений движка у Relic есть
`scartype(x) == ST_*`.

**I. Мёртвый эмбед `eco_contest_scar.h`**: `kEcoContest` нигде не подключён,
и его текст разошёлся с `eco_upgrades.lua` (генератор `_gen_eco_contest_h.py`
указывает на `k:\aoe4_dlc\...`).

**J. Проверить зондом:** регистр типа `"Worker"` в
`Player_GetEntityCountByUnitType` (`hybrid_core.scar:1942/3450`,
`spatial_world_model.scar:1247`) — в `sga` этот тип не встречается.

`string.format("%d", float)` (ошибка в 5.3): 53 вызова просмотрены, живых
случаев нет — аргументы под `math.floor`/целые счётчики.

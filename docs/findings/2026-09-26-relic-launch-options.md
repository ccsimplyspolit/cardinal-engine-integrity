# 2026-09-26 Параметры запуска Relic

Справочник: [RELIC_LAUNCH_OPTIONS.md](../RELIC_LAUNCH_OPTIONS.md). Журнал проходов 2026-09-06: [RELIC_COMMAND_LINE.md](../RELIC_COMMAND_LINE.md).

## Сохранённая база

Автоанализ заново не запускался и заново не нужен. IDB уже был разобран: `analysis_wait` занял 0.34 с, `functions_added=0`.

После работы сессии база записана на диск (`idb_save`, 2026-09-26 15:25, режим `headless-packed`):

`K:\aoe4_dlc\aoe4\gamesource\dump\ida-work\runtime_exe.i64`

Рядом лежат `runtime_exe.id0`, `.id1`, `.nam`. Очередь анализа пустая, функций **535025**. Следующее открытие этого файла — загрузка готовой базы, не новый автоанализ. Вторая копия в `dumps\...\ida\runtime_exe.i64` по-прежнему не открывается: у неё сломан `.nam`.

## Как смотрели

GUI `ida.exe` в этой сессии не держали. База открыта headless через multi-IDA MCP.

| | |
|--|--|
| Инстанс | `qv31` (idalib, порт 60689, pid 24168) |
| IDB | `K:\aoe4_dlc\aoe4\gamesource\dump\ida-work\runtime_exe.i64` |
| Imagebase | `0x7FF7A5500000` |
| Input, записанный в IDB | `modules_runtime\RelicCardinal.exe` (дамп 60644) |
| Функций после `analysis_wait` | 535025, `functions_added=0`, очереди пустые за 0.34 с |
| Steam exe | `D:\SteamLibrary\steamapps\common\Age of Empires IV\RelicCardinal.exe` **16.3.11308.0**, 144752932 байт, appmanifest buildid `24231237` |
| scardocs | тот же каталог Steam, `scardocs\html\function_list.htm` |

`py_eval` на этом headless-инстансе сервер не отдаёт (`Method not found`). Сверка шла через `imports_query`, `find_regex`, `xrefs_to`, `decompile`.

## Что совпало с каталогом 2026-09-06

| Проверка | Результат |
|----------|-----------|
| `GetCommandLineA` | импорт KERNEL32 `0x7FF7AABDE598` |
| `GetCommandLineW` | `0x7FF7AABDE5E0`, два потребителя: RVA `0x3AE9EC0` и `0x3AEA0D0` |
| `CommandLineToArgvW` | импорт SHELL32 `0x7FF7AABDF000` |
| Xref-дамп четырёх адресов (`GetCommandLineA`, `GetCommandLineW`, ` -notrap`, ` -nodbg`) | 496 записей, 184 уникальные функции. Две лишние относительно старых 182 — ingest по `GetCommandLineW` |
| Layer B, строки с пробелом и концом строки | ровно ` -nodbg` ` -notrap` ` -forcetrap` ` -wertest` ` -nonInteractiveMode` ` -notrace` |
| ` -nodbg` xref | только `Dev_NoDbg_Check` `0x7FF7A9077110` (RVA `0x3B77110`). Декомпил: флаг `g_Dev_NoDbgFlag`, один раз `g_Dev_NoDbgParsed`, возврат `!flag && IsDebuggerPresent()` |
| ` -notrap` xref | только trap init `0x7FF7A91021F0` (RVA `0x3C021F0`) |
| `Game_IsRTM` | строка `0x7FF7ACCA2961` (RVA `0x77A2961`), **0 xrefs** |
| `memory.bin` 147050496 | по одному вхождению каждого Layer B; ноль для ` -dev`, ` -rtm`, ` -windowed`, ` -noborder`, ` -nomovies`, ` -vulkan`, ` -novid`, ` -dx11`, ` -dx12`, ` -high` |

Новых имён слоя B этот проход не добавил.

Повтор той же базы без нового автоанализа (инстанс `qv31` ещё держал сохранённый IDB):

| Строка | Адрес | Кто читает |
|--------|--------|------------|
| `fakeDeviceType` | `0x7FF7ABAE9FC0` | RVA `0x3AEB3E0`, один xref |
| `use_legacy_presentation_serialization` | `0x7FF7AB90B028` | RVA `0x1BA0CA0`, ищет имя в таблице командной строки |

Повторная сверка декомпилята с `RELIC_LAUNCH_OPTIONS.md`: в таблице командной строки (шаг 72 байта, `qword_84D6B70`) нашлись имена, которых в справочнике не было. Они дописаны в раздел «Нашлись в игре». Среди них с живым эффектом: `locale`, `useLocOverlay`, `lock_input_device`, `maxthreads`, `heartBeatOverride`, `perfHeartBeatOverride`, `debugtoolport` (слушает, по умолчанию 35813), `logto`, `designlog`, `maxMeshLOD`, `overrideAnimEventLevel`, `useTerrainShotBlocking`, `mapgenRandomPositions`, `mapgenTeamsTogether`, `moviemodeframerate`, `start_activity`, `misc_frame_time_stat`, `MovieManagerLogSelectionDetail`, плюс короткие ключи пакета графики `DebugLevel`, `RRStateTracking`, `Aftermath`, `RenderdocSwitch`, `DRED`, `WarpDevice`.

`AppStartDelay`, `GameHooksPort`, `crc_block_limit` и `path_limit_precise` игра читает. У первых трёх разобранное число в видимом коде в поле не пишется (`GameHooksPort` остаётся 4602). `path_limit_precise` упирается в потолок 2 000 000, но в счётчик кладётся уже посчитанный лимит. `sfx_ui_frontend_card_play` — имя звука, не флаг.

`showXboxUI` и `showPS5UI` есть в Steam `scardocs` у `UI_IsXboxUI` и **отсутствуют** в строках IDB. Дисковый распакованный образ `RelicCardinal.unpacked_static.exe` на месте, 144 752 932 байт, тот же размер, что у Steam-exe. Живые строки флагов читались из runtime-образа в IDB, не из зашифрованного exe.

## Официальные тексты

scardocs (установленная копия) прямо описывают `-rtm` (`Game_IsRTM`), `-init test.lua` (`Misc_GetCommandLineString`), `-dev` для `Util_Grab` / `Util_ToggleAllowIntelEvents`, `-test_result_file` и `-TestLong` у тестового каркаса. Строк `TestConfig_*` в образе Relic по-прежнему нет: это документация движка, не обработчик этого ритейл-бинаря.

Сайт поддержки Age of Empires список параметров запуска не публикует. Сторонний разбор Steam appinfo (steamraw, app `1466860`) показывает у клиента пустую строку и `-publicTest` для веток Public Test / PUP QA / Practice, плюс `EssenceEditor.exe -publicTest`. `-publicTest` при этом есть и в Layer A самого `RelicCardinal.exe` (хост API).

## Сверка с `internal` (тот же день)

`ForceNoDbg` в `patch_game.cpp` пишет `1` в RVA `0x844B2ED` **один раз**, из `PatchGameRun`. Inject байт не пишет. `PatchGameTick` каждые 50 мс в окне 8 с зовёт только `ra_retitle::RetitleAll`. Строки «re-arm every 50 ms» и «при inject `DevForceNoDbg`» в каталоге и `UPDATE_GUIDE` были устаревшими; поправлены в этом проходе. Символа `DevForceNoDbg` в дереве нет.

До `relic_cmdline.cpp` вкладка показывала только байт. Байт ленивый: Steam `-nodbg` может ещё быть `0`, пока `Dev_NoDbg_Check` не вызывался. Ниже — что оверлей читает и пишет после этой сверки.

## Оверлей: строка запуска и три записи `.data`

`relic_cmdline.cpp` читает `GetCommandLineA` и три байта (`0x844B2ED`, `0x85A6C39`, `0x84421BC`). Отдельные кнопки на вкладке Patch Game, не внутри RUN:

- байт `-nodbg`;
- байт `Misc_IsDevMode` (`0x84421BC`), подпись «файловые хелперы»;
- допись SSO-ряда `dev` в вектор Layer A (`0x84D6B70`, ряд 72 байта), только если готовность `0x844B2EF` = 1 и `end < cap`. Свою кучу не растим. Relic `.text` не пишем.

Пробник шлёт `Misc_IsCommandLineOptionSet("dev")` и `Misc_IsDevMode()` на потоке окна и ждёт `%TEMP%\aoe4_cli_probe.txt`.

Оффлайн: `StkRates.Repair` (`repair_rate_modifier`; в `standard_mode.scar` этот вызов закомментирован), `GrantRes.Sandbox` (20000/20000/5000/10000, pop 200, instant build). Кнопка целей миссии переименована.

Дописать имя в таблицу Layer A не переигрывает старт. Слово влияет только на следующий вызов `Misc_IsCommandLineOptionSet` / `strstr`. Окно, устройство DirectX, потоки, предзагрузка, хост API и trap init к этому моменту уже отработали. Эффект матча (`-cheat`, `-no_fow`, скорости) повторяется нативами, не повторным чтением флага: `standard_mode.scar` забирает `Util_GetCommandLineArgument` один раз в `OnInit`. Значение (`-timer 15`) — это поле value в ряде из 72 байт; голое имя без value для `GetCommandLineInt` пустое.

## Подмена самой проверки

Общих ворот три, не 182.

`Dev_NoDbg_Check` `0x3B77110`: если `g_Dev_NoDbgParsed` (`0x85A6C39`) ещё 0, первый вызов заново читает строку Steam и **перезаписывает** флаг `0x844B2ED`. Подмена для всех вызывающих — оба байта в 1. Тело функции не патчится. В выгрузке по имени видны `0x3C03F10` (`__debugbreak` / `MEMORY[0]=0`), `0x293F9E0`, `0x202C860`. Каталог: 16 code xrefs. `IsDebuggerPresent` из IAT зовёт только эта функция и CRT.

`Misc_IsDevMode` `0xBD9D40` — восемь байт, `return` байта `0x84421BC`. Защёлки нет.

`Misc_IsCommandLineOptionSet` `0xBD9B20` каждый раз обходит живую таблицу (`0x3AF23B0`). Отдельного байта на имя нет. Подмена функции «всегда true» включила бы все флаги сразу.

Автотест `0x3B61B70` после первого вызова возвращает байт **`0x86AD414`** (`mov byte ptr [rip+0x4B4B859], al` на `0x3B61BB5`). В каталоге было `0x85AD414` — ошибка на `0x10000`, поправлено. Этот байт не откатывает сторож и журнал: те уже скопировали ответ при старте.

Остальные потребители `GetCommandLineA` держат свой `strstr` внутри себя. Общей функции, как `Dev_NoDbg_Check`, у них нет.

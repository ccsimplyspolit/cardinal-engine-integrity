# Реестр оффсетов и апдейт под новый патч AoE4

Этот документ — про **сбор всех RVA/оффсетов и переезд на новую сборку**
`RelicCardinal.exe`. Он о том, *как автоматически перенайти адреса*, когда
Relic выпускает патч. Глубокий разбор слоёв защиты (DualFlag, RA sliding
window, integrity, FairPlay, unpack) — в [UPDATE_GUIDE.md](UPDATE_GUIDE.md);
здесь — только механика оффсетов.

Текущий эталон: **16.3.11308.0**, PDB GUID `BCEA0647ACA7405B824B7D805C1D2B20`,
`SizeOfImage 0x8C3D000`.

---

## 1. Что где лежит

| Артефакт | Назначение |
|---|---|
| `sdk/offsets/RelicCardinal_16.3.11308.h` | Канонический список RVA, против которого компилируется инжектор. Правится **вручную** при переезде. |
| `sdk/offsets/registry.json` | **Сводный машинный реестр**: каждая RVA из исходников + секция + сигнатура (где выводится). Генерируется. |
| `sdk/offsets/registry.md` | Человекочитаемая таблица того же. Генерируется. |
| `docs/STRUCT_OFFSETS.md` | **Каталог оффсетов полей структур** (161 шт): `+0xNN` в игровые структуры. НЕ RVA, сигнатур нет — отдельный чеклист под апдейт. `tools/build_struct_offsets.py`. |
| `sdk/offsets/xref-index.json` | Кэш: target RVA → ссылающиеся инструкции (79 МБ, **не коммитится**, пересобирается ~180 с). |
| `sdk/scar/ScarNativeRvas.h` | 390 SCAR-нативов (wrapper + inner RVA). Резолвятся **только** в рантайме через `ScarNativesDump`; имён нет в статическом образе. |
| `sdk/structs/known.h` | Оффсеты полей структур (не адреса модуля) + несколько vtable RVA. |
| `tools/relic_offsets/` | Пакет: `image` (чтение образа), `scan` (AOB-поиск), `sig` (вывод сигнатур), `xref` (индекс ссылок), `source` (парсер констант), `registry` (сборка). |
| `tools/build_offset_registry.py` | Собирает `registry.json`/`registry.md` из исходников + эталонного образа. |
| `tools/resolve_offsets.py` | **Перерезолвит реестр на новом образе** — главный инструмент апдейта. |
| `tools/audit_relic_offsets.py` | Побайтовое сравнение исходных RVA против baseline+current PE (идентичность, не переезд). |
| `tools/verify_offsets_live.py` | RPM-проверка прологов/полей против живого процесса (без дебаггера). |

Инжектор сам по себе устойчив к части сдвигов: `offsets.cpp` при старте
сканирует по AOB и **кэширует результат по FileVersion** (`OffsetsResolveAll`
→ `offsets_<ver>.ini`). Если сигнатура жива — новый RVA подхватится в рантайме
без пересборки. Реестр/резолвер нужны, чтобы **заранее** знать, что переехало,
и починить то, чему рантайм-скан не поможет (data-глобалы, vtable, близнецы).

---

## 2. Как устроен сбор (188 RVA → сигнатуры)

`build_offset_registry.py` парсит именованные `constexpr … kX = 0x…;` из ~20
файлов инжектора и SDK, классифицирует каждое значение по секции эталонного
образа и выводит сигнатуру.

Итог на 16.3.11308 (см. шапку `registry.json`): **189 RVA** из исходников.

| Категория | Кол-во | Как перенаходится после патча |
|---|--:|---|
| `code:func`, уникальный пролог | **57** | Masked-AOB пролога, rip-disp/rel32 вайлдкарднуты. Уникален в `.text`. |
| `data`/`rdata` через xref | **79** | Находим ссылающуюся функцию по её сигнатуре → читаем свежий rip-disp → восстанавливаем адрес. |
| `code:func`, близнецы | **4** | Функции байт-в-байт совпадают в окне (`FOW_UnExploreAll`, `AiSetDifficulty`, `AiLockSquads`, `WorldSnapHeight`). Берём по индексу в отсортированном списке совпадений. |
| `data`/`rdata` ручной метод | **8** | 4 чистых RTTI-vtable (по имени класса), 1 vtable-слот (`SimWorld::Tick`, сверяется рантаймом), 3 близнеца-кэша (`RaHash*`, `UiScale`) — захардкожены в инжекторе. |
| `code:site` / внутренние | **41** | Адрес внутри функции (VEH-BP, CALL-слоты `CanSee`). Якорь = `enclosing_func + delta`: находим функцию по сигнатуре, прибавляем дельту. |
| Отсеяно (не адреса) | 10 | type-id/магии (`kPbgMapSizeType`, `kSteamId64HiDword`, …), случайно попавшие в диапазон образа. |

**136** сигнатурных RVA переносятся полностью автоматически по уникальной
сигнатуре (57 прологов + 79 data-через-xref); ещё **4** близнеца — по индексу,
и **8** data — по документированному методу (см. §5). `resolve_offsets.py`
помечает первые 140 как **MATCH** на идентичной сборке. Выведенные сигнатуры
**совпадают байт-в-байт** с проверенными в бою ручными AOB инжектора
(`kScarDoStringPrologue`, `kDodgePat`, `kSimWorldDoCommandPrologue` и т.д.) —
деривер воспроизводит то, чему уже доверяет код.

**Полнота гарантирована.** `source.audit_completeness` сканирует всё дерево
`internal/`+`sdk/` и падает, если появилась RVA-именованная константа в
диапазоне образа, которой нет в охвате реестра (тест
`test_offset_registry.py::CompletenessTests`). Исключения задокументированы:
`licensed_helper_map.cpp` (RVA другой DLL), `tests/` (фейковые адреса),
`tools/x64dbg-hidden/` (дублируют покрытые RVA).

### Почему сигнатура переживает патч

Между сборками «плывут» именно операнды, которые линкер релоцирует или которые
кодируют расстояние: rip-относительные смещения, rel32-таргеты call/jmp,
широкие абсолютные immediate-адреса. Деривер (`sig.build`) дизассемблирует
пролог, **вайлдкардит ровно эти байты**, оставляя опкоды и ModRM/регистры, и
растит окно по целым инструкциям, пока паттерн не станет уникальным в `.text`.
Уцелевает «форма» кода, а она при пересборке того же исходника меняется редко.

### Кросс-капчур валидация (16.3.11308)

Настоящей другой сборки для теста переезда пока нет (игра не менялась с 06.09),
но сигнатуры проверены на **трёх разных типах образа одной сборки** — это
отсекает зависимость от способа снятия и от рантайм-дрейфа байт:

| Образ | Тип | Результат |
|---|---|---|
| `unpacked_static.exe` | статический unpack с диска | 140 MATCH, 0 BROKEN |
| `…162737/…bin` | живой дамп модуля (база `0x7FF7…`, layout) | 140 MATCH, 0 BROKEN |
| `unpacked_gold_live_60644_memory` | живая память (рантайм-мутации `.text` от RA-integrity) | 140 MATCH, 0 BROKEN |

Одинаковый результат на другой ASLR-базе доказывает, что сигнатуры
RVA-независимы; совпадение на live-memory образе — что рантайм-правки integrity
в кластере `0x3DD0000–0x3F90000` не задевают ни один пролог/xref.

---

## 3. Ритуал апдейта

> Только образ модуля / unpack. On-disk `RelicCardinal.exe` **зашифрован** —
> его `.text` не код (кроме заголовков/`.rdata`/`.rsrc` — по ним считается
> идентичность сборки). Даём инструментам **unpacked PE** или **живой дамп**,
> никогда сам Steam-файл. Память машины близка к commit-лимиту, когда игра
> открыта (см. auto-memory «Вылет AoE4 Недостаточно памяти») — образ читается через
> mmap, не копируется в процесс.

### Шаг 0 — заметить патч

Steam `appmanifest_1466860.acf`: `buildid`. FileVersion exe. Мониторинг патч-нот
— см. auto-memory «Мониторинг патчей AoE4». Если `buildid` и SHA-256 exe не
изменились — это **не** апдейт движка (как 2026-09-20: дата файла сменилась,
байты нет; см. [findings/2026-09-20-offset-revalidation.md](findings/2026-09-20-offset-revalidation.md)).

### Шаг 1 — получить чистый образ новой сборки

```bash
# живой дамп модуля (игра запущена, только RPM, без дебаггера):
python tools/dump_relic_module.py           # → dumps/RelicCardinal_<pid>_<ts>/

# ИЛИ статический unpack с диска:
python -m unpacker rediscover && python -m unpacker unpack-disk
python -m unpacker audit                     # x25519 / leftover / gold-100
```

Канон распаковки — [RELIC_UNPACK_ALGORITHM.md](RELIC_UNPACK_ALGORITHM.md).
Прописать путь к образу для инструментов (per-machine, не коммитится):

```bash
echo '<путь к .unpacked_static.exe или к папке дампа>' > meta/offsets_reference.txt
```

### Шаг 2 — перерезолвить реестр на новом образе

```bash
python tools/resolve_offsets.py --image <новый образ> --json resolve.json
```

Вывод помечает каждую запись:

- **MATCH** — сигнатура нашлась на том же RVA. Ничего делать не нужно.
- **MOVED** — нашлась на новом RVA (печатается `-> 0xNEW (delta ±0x…)`).
  Обновить константу в исходнике на новый RVA.
- **BROKEN** — сигнатура не уникальна/не найдена. Перевыводить вручную (§4).
- **MANUAL** — изначально не автоподписываемо (RTTI-vtable, близнец, внутренний
  site). Проверить/перенести документированным методом (§5).

Тот же процесс в одну сборку даёт `139 MATCH + 49 MANUAL, 0 BROKEN` (самотест на
эталоне; MANUAL включает 41 внутренний site и 8 data-методов).

### Шаг 3 — починить MOVED/BROKEN

Для **MOVED**: получить готовый список правок по файлам и применить его вручную:

```bash
python tools/resolve_offsets.py --image <новый образ> --emit-updates updates.md
# updates.md: «file:line  kName  0xOLD -> 0xNEW» по каждому файлу
```

Заменить литерал RVA в файле из `refs[].file:line`. Большинство —
в `sdk/offsets/RelicCardinal_16.3.11308.h`; если сборка сменилась, переименовать
файл в `RelicCardinal_<new>.h` и обновить `#include`-ы.

Для **BROKEN**: функция изменилась настолько, что пролог перестал ловиться.
Если у неё в реестре есть строковый якорь (поле `strings`), `--deep` перенайдёт
её автоматически:

```bash
python tools/resolve_offsets.py --image <новый образ> --deep
# для каждой broken-функции со строками печатает RVA-кандидатов
```

Вручную то же самое (строки между сборками стабильнее кода) — без IDA:

```python
import sys; sys.path.insert(0, "tools")
from relic_offsets.image import open_image
from relic_offsets import xref, strings
img = open_image(r"<новый образ>"); xi = xref.build(img); st = strings.extract(img)
print(strings.find_functions_referencing(img, st, xi, "MatchResultPosted"))  # -> [Dodge]
```

Если строкового якоря нет — открыть новый образ в IDA (или idalib-MCP), найти
функцию по xref/соседям, взять новый RVA, перегенерировать сигнатуру (§4).

### Шаг 4 — пересобрать реестр и проверить в игре

```bash
python tools/build_offset_registry.py --image <новый образ> --rebuild-xref
```

Затем хостовые тесты и сборка DLL:

```bash
pwsh tests/adversarial/run_host.ps1          # включает test_offset_registry.py
```

Сборка `Release|x64` проектов `InternalInjector`, `DllInjector`, `WindowWatch`
(см. [UPDATE_GUIDE.md §2.4](UPDATE_GUIDE.md)). Финальная проверка — живая:
`verify_offsets_live.py` против процесса, затем ScarInit/оверлей в матче.
Правила MP-теста и «можно катить» — в [UPDATE_GUIDE.md §11–13](UPDATE_GUIDE.md).

---

## 4. Перевывод одной сигнатуры вручную

```python
import sys; sys.path.insert(0, "tools")
from relic_offsets.image import open_image
from relic_offsets import sig

img = open_image(r"<новый образ>")
print(sig.build(img, 0xAA9B00))              # пролог функции
# для data-глобала — через ссылающуюся функцию:
from relic_offsets import xref
xi = xref.build(img)                          # ~180 с (или xref.XrefIndex.load(cache))
site = xi.unique_site(0x7B41E28)
print(sig.build_xref(img, 0x7B41E28, site) or sig.build_xref_site(img, 0x7B41E28, site))
```

`sig.build` вернёт `unique: true` + `pattern`. Если `unique: false` и есть
`siblings` — функция-близнец, бери по `index`. `count > 1` без siblings — расширь
окно (`max_bytes=`) или добавь якорь вручную.

---

## 5. Методы для «ручных» записей

| Тип | Записи | Метод |
|---|---|---|
| Чистый RTTI-vtable (нет code-ссылки) | `kVtblRva` ×3 в `known.h` | Найти по имени класса: type descriptor `+0x28` = имя, `col_rva`/`vt_rva` в `sdk/rtti/classes.tsv`. См. auto-memory «Relic reflected-object header». |
| Vtable-слот функции | `kHardSimWorldTickVtRva` (`0x64C4B18`) | Сам слот хранит `&SimWorld::Tick`. `offsets.cpp` находит Tick по прологу и **сверяет**, что слот на него указывает — рантайм-кросс-чек, не статическая сигнатура. |
| Функции-близнецы | `FOW_UnExploreAll`, `AiSetDifficulty`, `AiLockSquadsInner`, `WorldSnapHeight` | Байт-в-байт совпадают с парой (Explore/UnExplore, LockSquad/LockSquads). Резолвер берёт по индексу в отсортированном списке; **сверить порядок** глазами в новом образе. |
| Близнецы-аксессоры (data) | `kRaHashGetClassNameW/GetWindowTextW` (`0x7AFDE00/08`), `kUiScaleIntern` | Ссылки из template-инстанцированных двойников (Watcher'ы `0x3F0A7D0`/`0x3F328D8`). Захардкожены в `ra_hide.cpp`/`radar.cpp`; два соседних 8-байтных глобала — младший ClassName, старший WindowText. |
| Внутренние site (VEH/CALL) | 41 шт: `kFowMinimapLosCall[]`, `kGetMgrLoadRva`, `kStateTreeLoadRva`, … | В `registry.json` у каждого `enclosing_func` + `delta`. Найти функцию по её сигнатуре, прибавить дельту; проверить, что байты на месте совпадают. |
| SCAR-нативы | `ScarNativeRvas.h` (390 с RVA) | **Только вживую.** Имён нативов **нет в статическом образе** (проверено: каталог строится в рантайме из SGA/динамически) — оффлайн-резолв невозможен. В матче Debug→Dump EVERYTHING → `ScarNativesDump` строит wrapper/inner RVA из живого каталога. `python tools/refresh_sdk.py`. |

### 5.1 Оффсеты полей структур

Отдельный класс — `+0xNN` внутрь игровых структур (SlotInfo, лобби-модель,
SimEntity, AIManager, RA-window). У них **нет сигнатуры**: при патче RVA-владелец
резолвится, но поле съезжает, и инжектор читает мусор. Каталог всех 161 —
**[STRUCT_OFFSETS.md](STRUCT_OFFSETS.md)** (`tools/build_struct_offsets.py`),
сгруппирован по структуре, с контекстом из комментариев. Метод переезда:
перепроверить каждое по свежему дампу (имя + комментарий — подсказка); многие
инжектор и так кросс-чекает в рантайме (поле должно указывать на разумное).
Тест `test_offset_registry.py::StructOffsetTests` ловит потерю парсинга.

---

## 6. Слой anti-tamper — отдельно от оффсетов

Переезд оффсетов **не** трогает обход анти-тампера. Это разные задачи:

- **RA sliding window / integrity / WindowWatcher** — RVA этих функций в реестре
  (`kRaEnqueue`, `kRaValidatorD02C`, `kRaWindowWatcher`, hasher `0x3E57050` и
  т.д.), но их **нельзя** патчить статически: hasher raw-load'ит `.text`. Обход —
  рантайм (`.data`-clear, neutralize, HV-hold). См. [UPDATE_GUIDE.md §9, §1.6](UPDATE_GUIDE.md).
- **Aegis (внешний протектор overlay)**: путь `--nullify-type0` на диске
  **больше не работает** — крашит игру illegal instruction (type3/type1 XOR-декрипт
  `.text` пропускаются). Актуальный обход — рантайм-hook `RA_Hasher` из
  инжектированной DLL, overlay на диске не трогать. См. auto-memory «Aegis
  type0 nullify» и [findings/2026-09-29-aegis-type0-safe-bypass.md](findings/2026-09-29-aegis-type0-safe-bypass.md).

После патча сначала оффсеты (этот документ), затем анти-тампер (UPDATE_GUIDE.md).

---

## 7. Ограничения

- Реестр покрывает **именованные скалярные RVA и массивы** из исходников +
  таблицу SCAR-нативов. Идентичность тела функции сохраняет оффсеты полей, но
  **не** проверяет поведение кучи/AI в реальном матче.
- Дамп в меню: список AI-игроков нулевой, часть world-структур не размаплена —
  heap-раскладки так не проверить.
- Резолвер читает только образ; он ничего не пишет и не подменяет RVA
  автоматически — решение по каждому MOVED/BROKEN за человеком.
- `xref-index.json` строится из `.pdata`-функций; leaf-функции без unwind-записи
  в индекс ссылок не попадают как источники (но сами подписываются по прологу).

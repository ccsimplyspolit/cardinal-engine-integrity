# AI BOT — полная документация

Игра: Age of Empires IV **16.3.11308.0**. Плагины живут только в `Documents\AOE4HSettings`.  
Типичный путь: `C:\Users\<you>\Documents\AOE4HSettings`.

Вкладка **AI BOT** — одна сессия (`DrawAiSessionPane`): **Enable AI** включает Relic ИИ, лочит боевую армию за игроком и по желанию подмешивает контрпик из данных оверлея. Memory AOB, Lua-локи и Scar-билдер с этой вкладки убраны (код в DLL ещё есть).

Словарь мира, ID сущностей и AV/OOS факты SCAR здесь **не** дублируются. Автор `.scar` читает `CPP_BRIDGES.md`. Аудит Relic-нативов Fine-tune / hybrid: `[HYBRID_NATIVE_AUDIT.md](hybrid_native_subsystem_audit.md)`. Production scoring vs PushScore vs personality: `[AI_SCORING_PIPELINE.md](AI_SCORING_PIPELINE.md)` (ADR-001). Карта папок: `PLUGINS.md`.

Не воссоздавайте `AOE4HOOK\plugins`, `AOE4HOOK-SCAR-Plugins`, `Documents\ScarScripts`.

---



## Оглавление

1. [Что делает вкладка и чего не делает](#1-что-делает-вкладка-и-чего-не-делает)
2. [Папки](#2-папки)
3. [Экран сверху вниз](#3-экран-сверху-вниз)
   - [3.1 Enable](#31-enable-staged-inject)
   - [3.2 Disable](#32-disable)
   - [3.3 Контрпик](#33-контрпик-данные-софта)
   - [3.4 C++ think / thin SCAR](#34-c-think--thin-scar)
4. [Три режима hybrid](#4-три-режима-hybrid)
5. [AI Profiles](#5-ai-profiles)
6. [AI Custom Templates (Fine-tuning)](#6-ai-custom-templates-fine-tuning)
7. [AI Templates (копии Data.sga)](#7-ai-templates-копии-datasga)
8. [Scoring Lua](#8-scoring-lua)
9. [Три вида локов](#9-три-вида-локов)
10. [Как грузится hybrid](#10-как-грузится-hybrid)
11. [Свои](#11-свои-scar-и-lua) `.scar` [и](#11-свои-scar-и-lua) `.lua`
12. `[AOE4HOOK_AI_SETTINGS](#12-aoe4hook_ai_settings)`
13. `config.ini` [— holds, капы, сложность](#13-configini--holds-капы-сложность)
14. [SCAR trust и хоткеи](#14-scar-trust-и-хоткеи)
15. [Рабочие сценарии](#15-рабочие-сценарии)
16. [Что какая папка не делает](#16-что-какая-папка-не-делает)
17. [Связанные файлы](#17-связанные-файлы)

---



## 1. Что делает вкладка и чего не делает

Оверлей **не** играет за вас и **не** подменяет VFS игры. Eco-бот — Relic. C++ держит сессию и инжектит SCAR на **оконном потоке игры** (`ScarExecuteOnWindowThread` → `SendMessageW`) — не из Present-хука и **не** через ScarHelper (тот путь всегда падал, см. `AI_SESSION_HANDOFF.md`).


| Делает | Не делает |
| --- | --- |
| Staged inject: army lock + AI (start delay) → контрпик (+1 с) на оконном потоке | Не грузит `hybrid_core` / `hybrid_o_*` с этой кнопки |
| `AI_LockSquad` на боевую армию **до** `AI_Enable` (стоящие + Relic `GE_EntitySpawn` после). Enable-true если пустой unlocked == 0 | Не лочит крестьян нативом; heap-stamp empty `+0x40` (think skip). `kEcoOpen` не `UnlockSquad`. После Enable не `LockSquads` / C++ `LockOneSid`; live WouldStrip eco не паркует think |
| Выключение: eco/здания unlock; **боевой +0x40 остаётся** (Disable→Enable больше не UnlockAll армии). Relic AI off | Не вызывает `Game_AIControlLocalPlayer` с Present / `ScarDoString` |
| Опциональный контрпик: C++ `ai_runtime` + `__EcoAct_Apply` (availability) | Не подменяет Relic-данные, если галочки контрпика выключены |
| Fine-tune (скоринг, gatherer, desire) + Save в `config.ini` | Не правит `DATA:AI/Personality` в Data.sga |


Против человека / рейтинг = **десинк** (Enable AI пишет AIWorldData).

Флаг сессии **не** пишется в `config.ini`: после рестарта оверлея кнопка Off. Сложность, галочки контрпика и слайдеры — да.

World-снимок для HUD / observatory оверлей считает сам (`AiPlannerGetSnapshot`). Контрпик **не** читает Lua `__EcoCounter_Tick` и **не** требует Send to SCAR. `AOE4HOOK_AI_PLAN` остаётся шиной для SWM / hybrid (world-feed); сессия **не** re-DoString этот blob, пока `AiRuntimeArmed()`.

---



## 2. Папки

Корень: `Documents\AOE4HSettings`.


| Папка                                                      | Роль для AI BOT                                                                                                                     |
| ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `AI Profiles\`                                             | Один `.ini` = один профиль. **Load** (повторный клик = перечитать с диска). Relic VFS **не** грузит. |
| `AI Custom Templates\`                                     | Fine-tuning `.ini`. Ссылка в профиле. **Apply AI package** пишет в этот матч. Relic VFS **не** читает. |
| `AI Templates\`                                            | Копии personality из Data.sga. Оверлей **никогда не Run**. Ключ пакета = 4 ключа Relic `AI_SetPersonality`. |
| `Lua Scripts\`                                             | Scoring presets (`warmonger.lua` / `risky_econ.lua`). **Apply AI package** в матче. |
| `Scar Scripts\_system\_auto\`                              | Скрыто от Files. Стабы `hybrid_o_safe.scar`, `hybrid_o_offline.scar`, `hybrid_o_risk.scar`, плюс `hybrid_o.scar` и `hybrid_c.scar`. |
| `Scar Scripts\System\hybrid_core.scar`                     | Тело директора. Prepend **только** на `hybrid_o`*, не на `hybrid_c`.                                                                |
| `Scar Scripts\_system\_menu\Online\AiScar\ai_builder.scar` | Apply locks / Clear. Скрыто от Files. |
| `Scar Scripts\` (корень, не System / `_system`)            | Ваши `.scar` → вкладка **Files**. AUTO opt-in на строке. |
| `NativeEspData\`                                           | SWM / UnitIntelligence. Оверлей грузит сам **до** вашего файла. Не дублировать. |
| `Config\config.ini`                                        | Holds, капы, `builder_profile`, `ai_difficulty`, trust. Часть ключей **без** виджетов на AI BOT.                                    |
| `Icons\`                                                   | PNG `{key}.png` для каталога билдера.                                                                                               |


Кнопки **Bot profile / Scoring / Personality / Fine-tune** на экране открывают эти четыре папки. Personality-папка — справочник bags; в матч идут ключи Relic через Apply AI package, не `.scar`.

---



## 3. Экран сверху вниз

Всегда:

- **Enable AI** / **Disable AI**
- Статус: Off / Waiting match / `AI on. Army locked for you.` / `AI on. Counterpick attached.`
  (ScarHelper — мёртвый путь, не статус кнопки)
- Три галочки **Optional AI: counterpick** (по умолчанию Off = Relic играет от своих данных)

Только если сессия On:

1. **Выделение** — галочка «Selected villagers stay mine» (`[scripts] ai_sel_lock`, **по умолчанию On**). Выделенные крестьяне уходят из Relic ИИ (`AI_LockSquad` на пустом tactic stack / 4CE0). Живая тактика — skip 4A70 и повтор, пока не станет idle (в том числе 15 с после deselect). Обычные монахи: пока на земле есть **реликвии** (не `holy_site`) — первые 3 у ИИ, остальные у игрока; `AI_LockSquad` по уже бегущему монаху — краш `AI_GetActiveTactic` NULL +0x58. Когда ground-relic count стал 0, первые трое проходят pending → stop → SafeStrip и навсегда переходят игроку. Shaolin / warrior monk всегда игроку. Захват святынь — отдельный hybrid `Cmd_AttackMoveThenCapture` (Safe не шлёт) и handover не задерживает. Разведчиков выделением не забираем. Подробности: **[AI_UNIT_CONTROL.md](AI_UNIT_CONTROL.md)**.
2. **Подгруппы** — галочка «Lock control groups to me (Ctrl+1..9)» (`[scripts] ai_group_lock`). Ctrl+0..9 лочит текущее выделение за игроком: **крестьяне** через `AI_LockSquad`, здания через `AI_LockEntity`. Combat после Enable не трогаем (уже army-locked). **`AI_LockSquads` не используется** — inner всегда 4A70 при tracking. ⚠ **Не кладите в подгруппу разведчика под управлением ИИ.** Подробности: **[AI_UNIT_CONTROL.md](AI_UNIT_CONTROL.md)**.
3. **Гарнизон** — галочка «Keep garrisoned units inside» (`[scripts] ai_garrison_lock`). C++ тик раз в 2 с (`StkGarrisonLockTick`, без Relic `Rule_AddInterval`) обходит **свои отряды** (`Player_GetSquads` → `Squad_IsInHoldEntity`). При живом ИИ лочит сквад/здание, только если это уже наша армия, группа, villager, или ИИ ещё выключен. Здание-держатель лочится обязательно: выгрузка идёт командой на здание. Пустое здание отпускается само. Ставится после army lock. Подробности: **[AI_UNIT_CONTROL.md](AI_UNIT_CONTROL.md)**.
4. **AI HUD** — галочка «Show AI HUD in match» (`[scripts] ai_hud`). Панель `AI BRAIN` в матче: перетаскивание по **Ctrl**, сворачивание кликом по заголовку, позиция в `[hud] ai_brain_x/y/custom`. Показывает: эпоху и крестьян, `MASS`/`UPGRADE` + `reason`, `need[]` («хочет строить»), активные галочки контрпика, состав врага с тирами кузницы/университета и `perCav`. При контрпике On: роль C++, **План / SCAR** (`generation / commitGen`), top-3 ранга observatory. Изменившийся Fine-tune скоринг подсвечивается **6 с**; при `apply=0` значения приглушены. Данные — `AiPlannerGetSnapshot()` + `AiProductionGet()`: **ни одного SCAR-вызова, нулевая цена по FPS**. Рисуется из `RadarDrawIntelWindows()` независимо от тумблера observer HUD, но под гардом `ScarVmIsCallable()`. На вкладке AI BOT тот же observatory в collapsing header **Scoring observatory**.
2. **Fine-tune preset** — combo со стемами `.ini` из `AI Custom Templates`; выбор сразу зовёт `AiCustomLoadSelected()` и заполняет ползунки. Кнопка **Reload preset from disk** перечитывает файл, если правили его на лету. Имя активного пресета видно в заголовке секции скоринга в HUD.
3. **Keep camera** + combo сложности (0..6, в живом матче шлёт `AI_SetDifficulty`)
2. Fine-tune из бывшего `DrawAiControls`: personality, income, intentions, gatherer, scoring (`front_line` / Defend / Attack / EnemyClump), max age, pop cap
3. **Save** в `Config/config.ini` `[scripts]` (`ai_difficulty`, `ai_counter_*`, `scarAi*`)

### 3.1 Enable (staged inject)

Кнопка **только взводит** `g_wanted`. Инжект в `AiSessionService` (pump из `ui.cpp` каждый Present).

Вне матча — статус `Waiting match`. После матч live (`ScarIsReady` + `ScarLeanScriptsAllowed`):

| Шаг | Задержка | Что | Статус |
| --- | --- | --- | --- |
| 1 | +**Start delay** (`g_startDelayMs`, слайдер 1..15 с, дефолт **1 с**) | **Слот + army lock** в одном `ai_lock_army.lua` (`Game_AIControlLocalPlayer` если ещё не AI-игрок, `AI_Enable(false)`, скан стоящих), затем Relic think: `AI_Enable(true)` + `AI_SetDifficulty` + `Game_EnableInput` **без** повторного Control. **Без** моста. | `AI on. Army locked for you.` |
| 2 | ещё +**1 с** (`kAiSessionBridgeDelayMs`) | Если любая галочка контрпика On: `AiRuntimeSetArmed(true)` + `PostMessage(WM_SCAR_AI_COMMIT)` → install `__EcoAct_*`. Если галочки Off — шаг пропускается. | `AI on. Counterpick attached.` |

`ScarUserScriptsAllowed()` (~2 с после live-VM) — пол для Files / hybrid с `Rule_*`. Lean `AI_Enable` его **не** ждёт: **1 с на слайдере ≈ 1 с**, если VM уже live.

**И первый, и повторный Enable в живом матче** лочат армию в том же вызове `AiSessionService`, что `eco_ai_on`: слот+лок **до** `AI_Enable`, Control **не** после лока. Staged-пауза после включения ИИ давала ему время повесить тактики, после чего `AI_LockSquad` их сносил (`rva=0x2A45959`). Control после лока сбрасывал стоящую армию (Disable→Enable). Разбор: `[AI_UNIT_CONTROL.md](AI_UNIT_CONTROL.md)`, раздел «Главный краш». Флаг `g_liveOnceThisMatch` только для лога; Disable его не сбрасывает.

Каждый шаг — отдельный `ScarExecuteOnWindowThread(script, lean=true)`: `SendMessageW(WM_SCAR_EXECUTE)` на оконный поток игры (поток Relic с живым Lua-состоянием). **Не** Present-хук и **не** ScarHelper.

UI на вкладке: `Starting in %u s` → `Counterpick in %u s` → статус live. «Army lock in %u s» больше нет — лок входит в шаг 1.

Контрпик: C++ считает на collect worker при каждом `AiPlannerUpdate` (~**2 с**, пока `AiRuntimeArmed()`). Удержание роли **35 с** (`kHoldSec` / `AiCounterShouldCommit`). Apply — hashed `__EcoAct_Apply` на оконном потоке (`WM_SCAR_AI_COMMIT`). Lua `__EcoCounter_Tick` **мёртв**. Relic `Rule_AddInterval` нет. `PublishPlan()` сессии **не** шлёт `AOE4HOOK_AI_PLAN`, пока runtime armed (`kPlanIntervalMs` 10 с остаётся только для fallback, если runtime выключен и нет world-feed).

Army lock: один скан стоящих, пока `AI_IsEnabled` ложь. После Enable — ScarToolKIT `ai_lock_army.lua` / `Hybrid_OnSpawn`: Relic `Rule_AddPlayerEvent(GE_EntitySpawn)` + `AI_LockSquad` на `event.entity`. **Нет** overlay `Local.AddPlayerEvent` (world-feed / `event.id`, поздно vs think, 01:09:13). Scan / cache-id после Enable только `pending-ai-live`. C++ relock **scan-only** — не `LockOneSid` (01:24 burst 50166–50178 → 4A70). WouldStrip отказывает сиду, который think уже трекает. `Cmd_Stop` не зовём (`rva=0x1ED5529`). Unlocked tracking не `L.safe` (23:34 4A70). Пока лок жив, Relic offense/naval и attack/front/clump = 0, **`iEcon` не ниже 1.0** (STK villager boom). `combat` и `siege` остаются как у роли: это намерения **производства** (`Infantry` / `RangedInfantry` / `CombatSiege` / `MilitaryProductionBuilding` умножают `StrategicIntention({combat=1})`, Evaluate `0x2CFDCD0` без нижней границы). С нулём армию не тренировал никто: 26.09 23:33 против 7 рыцарей ИИ не строил ни контр, ни казарм и ушёл в эпоху (разбор). Фильтр армии **отрицательный** (eco + scout): civ-unique игроку, синоби (30.09) и Жанна д'Арк во всех формах, крестьянка тоже (`isJeanne`, тип отряда `jeanne_d_arc`, 01.10). До handover `religion=1` и `monkCap>=3`. Relic's 3 монаха у ИИ; лишние обычные монахи при живом think не LockSquad (spawn pending). **Нет** `__ArmyLock_Tick` / `Hybrid_SweepLocks` / `AI_LockSquads`. Enable-true если `empty-unlocked==0` после heap-stamp (live eco WouldStrip не паркует, как STK). `kEcoOpen` не UnlockSquad; stamp каждый live-тик. Stamp `stkOnSpawn+keepLock+noEn4A70+heapLock+emptyEn+noOpenUnl+tickStamp`. Инжект только `internal\x64\Release\DllInjector.exe` + соседний DLL.

### 3.2 Disable

Eco и здания возвращаются игроку. **Боевой army lock (+0x40) не снимается** — иначе повторный Enable отдаёт армию Relic (WouldStrip leftover tracking).

- villager lock off; EventRule снимается и ставится снова на Enable
- restore `ITEM_DEFAULT` на затронутых BP контрпика (`__EcoAct_Restore`)
- `AI_UnlockSquad` / `AI_UnlockEntity` только не-армии (нет `AI_UnlockAll`)
- `AI_Enable(false)` + `Game_EnableInput true`

### 3.3 Контрпик (данные софта)

Три независимые галочки в `[scripts]`: `ai_counter_units`, `ai_counter_buildings`, `ai_counter_develop` (default 0).

Источник — C++ `AiPlanSnapshot` (`ai_planner` / `ai_combat` / `ai_counter_math`): `need[]` (spear/archer/horse/maa/xbow), `eco.mode` MASS vs UPGRADE, smith/uni. Lua `_G.AOE4HOOK_AI_PLAN` для контрпика **не** читается. Состав врага пока **role buckets**, не точный PBG.

Линии юнитов (каталог aoe4world / `unit_profile.cpp`): мягкие лучники → арбалет → порох **только если юнит тренируется сейчас** (`UnitProfileKindAvailable` на текущем возрасте). Иначе спрос остаётся на лучниках / коннице. Каталог может уже знать Castle xbow — в феодале это ещё не «есть в ростере». `keepArcherLine` (`keepArch` в PLAN): English `unit_archer_N_eng`, Lancaster yeoman, японский/Sengoku yumi — **не** менять на xbow. Копья / MAA / конь / рыцарь **не** сливаются в одну линию.

| Галочка | Если On | Если Off |
| --- | --- | --- |
| Unit | `Player_SetSquadProductionAvailability` по `scar_spearman` / `scar_archer` / … | Relic сам выбирает юнитов |
| Building | лок бараков / стрельбища / конюшни, которые PLAN не просит | Relic сам строит военные здания |
| Development | лок университета / кузницы в режиме MASS (пока враг не обогнал по тиру) | Relic сам качает развитие |

`ITEM_LOCKED` общий на слот (и игрок не произведёт заблокированное). Снимите галочку, если хотите полный ростер.

Hybrid `K.counterCut` / Files AUTO с этой вкладки **не** запускаются.

Старый Memory / Lua Features / Scar builder описан ниже в разделах 4–9 — с вкладки AI BOT больше не открывается.

### 3.4 C++ think / thin SCAR

**Think in C++. Act through Relic.** Relic по-прежнему тренирует. Overlay режет семьи и объясняет. Полный пайплайн: [AI_SCORING_PIPELINE.md](AI_SCORING_PIPELINE.md). ADR: ADR-001.

```text
collect worker → AiPlannerUpdate (~2 s armed)
              → AiRuntimeOnPlanPublished (35 s hysteresis)
              → ai_production observatory
Present: PostMessage(WM_SCAR_AI_COMMIT) only
window: HandleAiCommitPosted → lean __EcoAct_Apply
```

Present **не** зовёт `ScarExecuteOnWindowThread` / `SendMessage` для катов (тот же FPS-капкан, что per-frame `eco_ai_counter_flags`). Eco contest уже идёт через `WM_SCAR_ECO_CONTEST`.

Три слоя Relic **не смешивать**: `ScoringFunctions_*` (train) ≠ `PushScore` (target) ≠ `AI_SetPersonality` (bags). Eco gathering Relic часто даёт **0** (`PlayerGatheringUpgrade` RVA `0x2C59A90`) — сессия ставит lean скоринг (`ai_eco_act_lua.h`) (без этого натива, villager=0.2, TTA 300).

`LuaScoringFunction` только O(1). `__EcoCounter_Tick` мёртв. Капы `PLAN.lock` 192 / `buildings` 128 — размер Lua-экспорта для SWM, не лимит think.

---

## 4. Три режима hybrid

Задаётся `[security] mode=` в профиле (`safe` | `offline` | `risk`). Старые файлы с `[hybrid]` Load всё ещё читает. Live-значение — `AiSettingsProfile()`. При `safe` оверлей **принудительно** гасит `cancelNative`, `relicScoring`, `availabilityNative` и включает `macroSync`.


| mode      | Файл AUTO / Run         | Sim-write (takeover, Cancel native, desire, availability) | Макрос                          |
| --------- | ----------------------- | --------------------------------------------------------- | ------------------------------- |
| `safe`    | `hybrid_o_safe.scar`    | **нельзя**                                                | принудительно SendInput         |
| `offline` | `hybrid_o_offline.scar` | можно **против ИИ**; блок если в матче другой человек     | как вкладка Macro               |
| `risk`    | `hybrid_o_risk.scar`    | можно, **OOS vs человек**                                 | как Macro; Allow OOS — ваш риск |


Смысл директора (ядро `hybrid_core.scar`): **игрок командует армией, встроенный ИИ ведёт экономику**. Слот всегда локальный. `World_IsMultiplayerGame` ядро не спрашивает; человеческий сосед смотрит `AOE4HOOK_HAS_OTHER_HUMAN`.

Монахи: Relic подбирает реликвии. Пока на земле есть реликвии — первые 3 обычных монаха у ИИ, остальные у игрока. После сбора реликвий все монахи переходят игроку. Затем offline/risk может отдельно послать их на свободные святыни через `Cmd_AttackMoveThenCapture`; **Safe — observe, без capture.** Shaolin / warrior monk не отдаются ИИ ни на одном этапе.

Еда: английская мельница в attrib — `food_control` (`building_econ_food_control_eng`, в имени нет `mill`); кольцо ферм на мельнице — **8**. Wheelbarrow ставится в очередь **на мельницу** (aoe4world `producedBy=mill`; у монголов — TC).

`hybrid_c.scar` — старый директор, только vs AI, **никогда** вместе с `hybrid_o`*. AUTO для него не включайте, если на AI BOT уже AUTO у `hybrid_o_*`.

Стабы в `_auto` почти пустые: выставляют `AOE4HOOK_HYBRID_FILE_PROFILE`, если C++ его ещё не поставил. Тело — prepend `hybrid_core.scar`.

Лог hybrid: `[HYBRID_O]` в warnings / `aoe4_internal.log`. **probe.scar** лучше грузить первым (System → Probe), если нужны диагностические строки. В рейтинге Probe AUTO не включайте.

---



## 5. AI Profiles

Папка: `Documents\AOE4HSettings\AI Profiles`.

Оверлей сидит README + `Default.ini`, `Safe.ini`, `Warmonger.ini`, `RiskyEcon.ini`.

Relic **не** читает эту папку. Это только UI + таблица `AOE4HOOK_AI_SETTINGS.builder` + выбор hybrid/scoring/fine-tune.

### Формат `.ini`

Имя файла = stem (латиница, цифры, `_`, `-`). `[meta] name=` — подпись на экране.

```ini
[meta]
name=MyBuild

[security]
mode=offline

[personality]
key=

[fine_tune]
preset=

[scoring]
lua=

[lock_units]
spearman=1

[lock_buildings]
keep=1

[lock_upgrades]
wheelbarrow=1

[queue_units]
man-at-arms=8

[queue_buildings]
house=5
```


| Секция | Смысл |
| --- | --- |
| `[security] mode` | `safe` / `offline` / `risk`. Было `[hybrid]`. При Load, если AUTO уже был на **старом** стабе, оверлей переносит AUTO на новый файл. |
| `[personality] key` | Relic `AI_SetPersonality`: `default`, `default_campaign`, `default_skirmish`, `default_smoketest`, или `restore`. Пусто = нет. Bags из `AI Templates` сюда не ставятся. |
| `[fine_tune] preset` | Stem из `AI Custom Templates` без `.ini`. Load перечитывает файл. Пусто = нет пресета. |
| `[scoring] lua` | Файл в `Lua Scripts\`, например `warmonger.lua`. Пусто = нет. |
| `lock_*` | Полный лок. Ключ = aoe4world / каталог. |
| `queue_*` | `ключ=N`. Юниты 1–50, здания 1–20. |


`[civs]` больше не пишется. Цивы hybrid — `config.ini` `[ai_settings] civ=`.


Ключи локов: буквы, цифры, `_`, `-`, длина < 80. До 64 позиций в каждом списке.

Цивы в SETTINGS уходят как `civs={eng=true,...}`. Семьи юнитов/зданий для **holds/caps hybrid** (не lock-список билдера) живут в `config.ini` `[ai_settings]` `fam=` / `bld=`, не в профиле.

### Как создать профиль

1. AI BOT → **Add Profile** → имя, **Create**, или скопируйте `.ini` в папке.
2. Выставьте `[security]`, scoring, personality, fine-tune (на экране или в файле).
3. **Load** профиля.
4. Наберите локи в каталоге / очередях → **Apply locks** в матче.
5. **Save**.

**Revert** возвращает к последнему Load/Save stem, не к git.

---



## 6. AI Custom Templates (Fine-tuning)

Папка: `Documents\AOE4HSettings\AI Custom Templates`.

Это **не** personality bags игры. Apply зовёт Relic: `AI_SetPersonality`, economy override, desire, intentions, gatherer split, `AIPlayer_PushScoreMultiplier` (это **target/military scoring**, не train cap / не `AIProductionScoring_UnderCountLimit`), pop/age caps. Пишет **AIWorldData**. Vs AI / desync vs человек.

Safe-профиль этот путь **не** должен использовать (кнопка всё равно отправит нативы, если нажать в матче).

Пример: `example_balanced.ini`.

### Формат

```ini
[meta]
name=example_balanced
all_players=1

[personality]
combo=2
custom=default_campaign

[economy]
combo=2
custom=balanced

[income]
apply=0
food=780
wood=540
gold=420
stone=160
merc=0
militia=0
popcap=0

[intentions]
apply=0
economy=1
combat=1
offense=1
defense=1
expansion=1
age_up=1
upgrade=1

[gatherer]
apply=0
food=0.25
wood=0.25
gold=0.25
stone=0.25

[score]
apply=0
front_line=1
defend=1
attack=1
enemy_clump=1

[caps]
max_age=-1
pop_cap_mode=0
pop_cap=200
```

**Personality combo** (`scar_ai_catalog.h`):


| combo | Действие                        |
| ----- | ------------------------------- |
| 0     | Не менять                       |
| 1     | `AI_SetPersonality` → `default` |
| 2     | `default_campaign`              |
| 3     | `default_skirmish`              |
| 4     | `default_smoketest`             |
| 5     | Custom — строка `custom=`       |
| 6     | Restore defaults                |


В attrib **существуют только четыре** ключа `AI_SetPersonality`: `default`, `default_campaign`, `default_skirmish`, `default_smoketest`. `GetPersonality` возвращает **путь bag**, не этот ключ.

**Economy combo:**


| combo | Действие                                                 |
| ----- | -------------------------------------------------------- |
| 0     | Не менять                                                |
| 1     | Disable all overrides                                    |
| 2     | `balanced` (имя dump-скриптов, **не** файл `ai_economy`) |
| 3     | `default_economy`                                        |
| 4     | `default_economy_campaign`                               |
| 5     | `default_economy_towers`                                 |
| 6     | Custom — строка `custom=`                                |


Секции `income` / `intentions` / `gatherer` / `score` применяются только если `apply=1`.

`max_age`: `-1` = не трогать; иначе 0…3. `pop_cap_mode`: 0 skip.

### Как применить

1. Положите `.ini` в `AI Custom Templates`.
2. На AI BOT ссылка **Fine-tune preset** в профиле (пишется как `[fine_tune] preset=` при Save). **Load** перечитывает `.ini`.
3. В **живом матче** (SCAR ready) → **Apply AI package**.

`DrawAiControls` (personality / income / intentions / gatherer / scoring / caps) **подключён** — он рисуется на вкладке, когда сессия On (`ui_scar_lanes.cpp`, `DrawAiSessionPane`). `.ini` из этой папки — альтернатива ползункам, а не единственный путь.

`ida_ok=1` в SETTINGS ≠ «натив есть в `_G` этого матча». Перед экзотикой смотрите dump_vm / `type(_G.X)=="function"`.

---



## 7. AI Templates (копии Data.sga)

Папка: `Documents\AOE4HSettings\AI Templates`. Каталог: `CATALOG.txt`.

Источник: Data.sga `ai/personality` + ключи Attrib.sga `attrib/ai/ai_personality`. Сборка **16.3.11308.0**.

Оверлей **никогда не Run** эту папку. Правка файлов **не** меняет VFS игры. Игра грузит `DATA:AI/Personality/<stem>.scar`.

На AI BOT ключ пакета зовёт Relic `AI_SetPersonality` только с ключами `default` / `default_campaign` / `default_skirmish` / `default_smoketest` (или restore). Это **не** подмена bag из этой папки.

Lua-стемы GetPersonality (не ключи SetPersonality): `cardinal_default_skirmish`, `cardinal_default_campaign`, `cardinal_default_smoketest`, `cardinal_default_towers`, `camp_build_only`, `basic_personality_template`.

Дампы **без префикса** зовут `TimeRule_RemoveAll` в `Initialize`* — **не копируйте** их в `Scar Scripts`. Файлы `ai_pers_*.scar` — те же bags с закомментированным Initialize, безопаснее если очень нужно положить копию в Files.

Референс в репо: `AOE4HOOK\sdk\ai_personality` (не plugin root).

---



## 8. Scoring Lua

Это **не** hybrid desire и **не** Fine-tune PushScore. Relic **перемножает** список, который возвращает `ScoringFunctions_*` — один 0 убивает кандидата. Каталог и eco-zero: [AI_SCORING_PIPELINE.md](AI_SCORING_PIPELINE.md).

Файлы в `Lua Scripts\`. Ссылка на AI BOT + `[scoring] lua=` в профиле. **Load** восстанавливает ссылку; **Apply AI package** пишет в матч.


| Файл                | Поведение                                                                                                                                                                                                                          |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `warmonger.lua`     | Перезаписывает `ScoringFunctions_*` в этой VM: военный уклон, `GetDesiredTCCount=0`, виллы 4000 / армия 2000, осада/флот/стены/торговцы/монахи/wonder = 0. Потом Init: `Game_AIControlLocalPlayer` + `AI_Enable` difficulty **6**. |
| `risky_econ.lua`    | Villager-spam (`ScoringFunctions_Gatherer` 5000), `AI_Enable` difficulty **3**, economy `balanced`, `AI_LockSquad` на боевых спавнах кроме villager/monk/scout/fishing.                                                    |
| любой другой `.lua` | Попадёт в combo, если имя `[A-Za-z0-9_.-]+.lua` и это не `DebugHUD.lua`.                                                                                                                                                           |


**Apply AI package** / **Run security** (если lua выбран) = `LoadListedScript(..., lua=true)` в ту же ScarDoString VM.

Пишет AIWorldData + часто включает Relic AI. **Не для рейтинга.** Не путать с Lua-hold 0 в hybrid (оверлей запрещает тип без Relic scoring context).

`AI_DoString` мёртв; это ScarDoString, как STK Run.

---



## 9. Три вида локов

Их легко смешать. Это **три канала**.


| Канал               | Где на экране   | Механика                                                                                  | Relic AI                      | Vs человек                                                                              |
| ------------------- | --------------- | ----------------------------------------------------------------------------------------- | ----------------------------- | --------------------------------------------------------------------------------------- |
| Memory AICTLR01     | блок сверху     | C++ флаги → `AOE4HOOK_AI_LOCK.vill/army/bldg` пока Armed                                  | не включает                   | флаги только; hybrid AUTO interval на потоке Relic может `AI_LockSquad` по Memory-битам |
| Scar `AI_LockSquad` | AI Features     | STK `ai_lock_*.lua` на оконном потоке Relic; `scar_vill` / `scar_army` = hold             | **включает** при ON           | OOS                                                                                     |
| Builder lists       | каталог / queue | `SETTINGS.builder.lockU/B/G` + `qU`/`qB`. Apply locks: hold и/или `Player_Set*Availability` | Apply locks не требует Activate | availability = sim-write, Full safe / Safe profile = hold only                          |


**Relock Memory** = флаги. **Relock Lua** = повторный инжект на оконном потоке. Не смешивать: Memory никогда не зовёт `AI_LockSquad` с Present.

Макрос **никогда не жмёт** `build_`*. Relic ИИ всё ещё ставит дома/стены, пока его не режут Fine-tune / RestrictBuildingList (SCAR, desync vs человек).

### 9.1 Режимы блокировки: что меняется на лету (2026-09-27)

Кнопка режима посреди матча: `AiSettingsSetLockMode` → `AiPlannerForceRefresh`,
`AiSessionBumpPlan`, `PushOverlaySettingsLua`. Следующий тик runtime пересчитывает
вырезы семейств, Layer B и spec `__EcoAct`; смена режима коммитится сразу
(`AiCounterLive::lockMode`, без 35 с гистерезиса). Перезапуск ИИ не нужен, кроме
одного случая — **Full AI при живом замке армии**.

| Режим | На лету (следующий коммит) | Только при включении сессии |
|---|---|---|
| `auto` | вырезы по контрпику, desire / сплит / намерения, `op`, окно 2-го ТЦ (`tb`/`tr`) | замок армии, штамп `+0x40` (общие для всех, кроме Full AI) |
| `fast_age` | ecoLock (все 7 семейств), цель Age II в сплите, `ia` | — |
| `fast_tc` | ecoLock, цель 2 ТЦ (`tc`), сплит под счёт ТЦ | — |
| `mass_army` | вырезы только по контрпику (`roleCut`), MASS-сплит | — |
| `only_eco` | ecoLock, эко-сплит | — |
| `workers_only` | `wo=1` в spec: Lua-гейт скоринга (дома, эко-техи, здания), ecoLock | `wo=1` дополнительно ставится при инъекции скоринга, чтобы первый проход директора не поставил дом |
| `full_ai` | вырезов нет, ecoLock/MASS сняты | форма включения STK: `Game_AIControlLocalPlayer`, без замка армии, без штампа и гейта; замки выделения / групп / гарнизона выключаются |

Переходы:

- **Из Full AI** в любой режим — кнопка сама перевзводит сессию (Disable → Enable):
  армия снова ваша. С 27.09 обычное включение возвращает сохранённые
  переключатели «Выделенные крестьяне остаются моими», «Лочить группы»,
  «Держать гарнизон внутри» (раньше они оставались выключенными до перезагрузки
  конфига).
- **В Full AI при живом замке армии** — со следующего матча (статус и подсказка
  это говорят). Disable оставляет `+0x40` на боевых строках, а включение Full AI
  пропускает гейт пустых незалоченных строк (`rva=0x2A45959`). Эксперимент с
  передачей посреди матча — `kAiFullAiMidMatchHandover` (выключен, см.
  2026-09-27 cloud plan).
- **Замок крестьян хоткеем** (`HotkeysScarLockVillagers`) не зависит от режима.
  В `workers_only` он забирает у ИИ крестьян, которых тот должен распределять, —
  при этом режиме держите его выключенным.

---



## 10. Как грузится hybrid

1. Матч, Relic Lua жива. Files / hybrid с `Rule_*` ждут ~2 с после PostInit (`kScarStartConditionsMs`). Lean Enable AI этот пол не добавляет.
2. Первый overlay `.scar`: bootstrap NativeEspData (один раз на VM) — `scar_natives_live` → `unit_intelligence` → `aoe4hook_bridge` → `spatial_world_model`.
3. Для имени `hybrid_o*.scar` C++ **перед** текстом стаба вставляет:

```lua
AOE4HOOK_HYBRID_FILE_PROFILE = 'safe' | 'offline' | 'risk'
AOE4HOOK_AI_SETTINGS = { ... }   -- включая builder={...}
-- затем System\hybrid_core.scar
-- затем стаб
```

1. `hybrid_c.scar` получает только блок SETTINGS, без `hybrid_core`.
2. SETTINGS ещё раз пишется **каждый** world-snapshot (даже без PLAN), если Send to SCAR крутится. Hybrid дополнительно получает SETTINGS на Load.

Если SETTINGS уже есть, он **главнее** `AOE4HOOK_HYBRID_FILE_PROFILE`.

Имена `hybrid`, `hybrid_o`, `hybrid_c`, `hybrid_core` заняты. Не кладите свой файл с `hybrid` в имени рядом, если не хотите mutex.

Не вызывайте `TimeRule_RemoveAll` / массовый `Rule_RemoveAll` — снесёте Pump и чужие interval.

Версия ядра на диске: `HYBRID_O_VERSION` в `hybrid_core.scar` (сейчас `2.0-beta.8-stklock`).

---



## 11. Свои `.scar` и `.lua`

AI BOT не запускает произвольный файл из `Scar Scripts\`. Свой код:

1. Кладите `.scar` в `Documents\AOE4HSettings\Scar Scripts\` (подпапки можно). **Не** в `System`, `_system`, `Menu`, `ScarToolkit` — Files их не показывает.
2. Вкладка **Files**: Run и опционально AUTO на строке.
3. `.lua` — в `Lua Scripts\`, та же VM.
4. Лимиты: 2 MiB, без NUL, UTF-8 (BOM срежется), без `..` в имени.

Контракт чтения мира, census, PLAN, MacroBridge: **CPP_BRIDGES.md**. Кратко:

- World-feed выключен, пока нет Send to SCAR.
- `AOE4HOOK_AI_SETTINGS` на каждом snapshot (holds/profile/builder).
- `AOE4HOOK_AI_PLAN` — только тумблер AI plan на Send.
- Строка радара — Lua-таблица. **Не** звать `Entity_GetPlayerOwner` на ней. Владелец: `row.o`.
- `ida_ok=1` ≠ натив в `_G`.
- `AIPlayer_PushScoreMultiplier` ≠ train cap.
- Не звать `AIProductionScoring_*` с `Rule_AddInterval` (нужен production scoring context Relic).

Читать SETTINGS из своего файла: обычный Files-скрипт **не** получает prepend SETTINGS на Load (это только hybrid / ai_builder push). Читайте `_G.AOE4HOOK_AI_SETTINGS` после snapshot или на своём interval.

Пример минимального тика:

```lua
-- my_ai_helper.scar  →  Scar Scripts\
Rule_AddInterval(function()
    local st = rawget(_G, "AOE4HOOK_AI_SETTINGS")
    if type(st) ~= "table" then return end
    local b = st.builder
    -- lockU / lockB / qU / qB — ключи aoe4world
end, 2)
```

Не копируйте unprefixed dumps из AI Templates. Не ставьте `AOE4HOOK_MP_SAFE = false` насовсем.

---



## 12. `AOE4HOOK_AI_SETTINGS`

Полный словарь — CPP_BRIDGES §10. Поля, которые ставит AI BOT / config:

```lua
{
  profile = "offline" | "risk" | "safe",
  ida_ok = 1,
  holdSec, holdUpgradeSec, firstSlotDelaySec, forcedQuietSec,
  villagerCap, villagerCapMin, villagerCapMax, armyCap, monkCap,
  holdByTimeMin, holdByPop,
  cancelNative, relicScoring, availabilityNative,  -- bool; в safe всегда false для трёх native
  macroSync, safe,
  civFilter,
  villagerByAge = { n1, n2, n3, n4 },
  units = { villager=true, spear=true, ... },
  buildings = { tc=true, house=true, ... },
  civs = { eng=true, ..., oth=true },
  holds = { ["spear"] = 8.32, ... },
  builder = {
    profile = "Default",          -- stem AI Profiles
    lockU = { ["spearman"] = true, ... },
    lockB = { ... },
    lockG = { ["wheelbarrow"] = true, ... },
    qU = { ["man-at-arms"] = 8, ... },
    qB = { ["house"] = 5, ... },
  },
  ai = {
    live = false, gen = 1,
    personality = "", scoring = "", fineTune = "",
  },
}
```

Семьи `units`:  
`villager spear archer horseman maa knight xbow ram siege monk scout trader ship handcannon upgrade other`

Здания `buildings`:  
`tc house mill lumber mining farm barracks archery stable siege dock blacksmith university monastery`

`holds`: leftover секунд с оверлея. Свой auto-hold **не продлевает** expire, пока ключ ещё в будущем. Countdown при hash-skip snapshot замирает — ориентир: `World_GetGameTime() + sec` при **первом** появлении ключа.

---



## 13. `config.ini` — holds, капы, сложность

Файл: `Documents\AOE4HSettings\Config\config.ini`.

На AI BOT **нет** ползунков hold/cap/fam/bld. Они всё равно попадают в SETTINGS.

### `[ai_settings]`


| Ключ                                                      | Смысл (дефолты в коде)                                                               |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `profile`                                                 | 0 Safe / 1 Offline / 2 Risk — дублирует live; профиль `.ini` перезаписывает при Load |
| `hold_sec`                                                | Lua-hold после cancel (11)                                                           |
| `hold_upgrade_sec`                                        | Hold апгрейдов (11)                                                                  |
| `first_slot_delay_sec`                                    | 2                                                                                    |
| `forced_quiet_sec`                                        | 8                                                                                    |
| `villager_cap` / `_min` / `_max`                          | 112 / 24 / 118                                                                       |
| `army_cap` / `monk_cap`                                   | 80 / 1                                                                               |
| `hold_by_time_min` / `hold_by_pop`                        | 0                                                                                    |
| `cancel_native` / `relic_scoring` / `availability_native` | 0; в Safe принудительно 0                                                            |
| `macro_sync`                                              | 1                                                                                    |
| `auto_hybrid`                                             | зеркало AUTO AI BOT                                                                  |
| `civ_filter`                                              | 0 = все цивы                                                                         |
| `builder_profile`                                         | stem, например `Default`                                                             |
| `vill_by_age`                                             | четыре числа                                                                         |
| `fam=` / `bld=` / `civ=`                                  | csv 0/1                                                                              |


`relicScoring=1` включает `AIProductionScoring_UnderCountLimit` **только** offline/risk, live `Has()`, scoring context Relic, не Safe. По умолчанию выкл: Rule tick — не тот context.

`cancelNative=1` — `Entity_CancelProductionQueueItem` (sim). Safe = только SendInput.

`availabilityNative=1` — `Player_Set*Availability` / Restrict. Sim-write, vs AI.

### `[scripts]`

`ai_difficulty=` — см. §3.2. Других виджетов сложности на AI BOT нет.

---



## 14. SCAR trust и хоткеи

**Settings → SCAR trust** сканирует тело `.scar`/`.lua` перед Run. C++ Enable AI, spawn и Macro **не** этим гейтом.


| Режим         | Поведение                                                       | Hybrid                                                                                                                                                                                              |
| ------------- | --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Full safe** | Отказ sim / Cmd / AI setters (каталог ~1031 имён) + instant OOS | `hybrid_o_offline` / `_risk` **запрещены именем**. `hybrid_o_safe` в whitelist, но prepend `hybrid_core` содержит `"AI_Enable"` → скан обычно **режет Run**. Свои Files без запретных нативов — ок. |
| **Unsafe**    | Instant-читы всё ещё no-op. Cmd / AI / sim в тексте **можно**   | Safe-директор в рейтинге: этот режим + профиль `safe`, без Lua Activate / Fine-tune / scoring                                                                                                       |
| **Offline**   | Скана нет. Оригинальные нативы. Только vs AI                    | Offline / Risk hybrid, Fine-tune, scoring                                                                                                                                                           |


UI-подсказки: `hybrid_o_offline` / `hybrid_o_risk` / `ai_tune` помечены как «нужен Offline».

Whitelist Full safe (имя файла): `probe.scar`, `dump_vm.scar`, `hybrid_o_safe.scar`, `ai_builder.scar`, SWM/UI bootstrap, `local_rules` / checksums.

**Hotkeys:** Lock Villagers → Memory villager; AI features → Memory army. Production macro — вкладка Macro, не AI BOT.

---



## 15. Рабочие сценарии



### A. Рейтинг / vs человек (Safe)

1. Settings → **Unsafe** (если нужен hybrid) или Full safe без hybrid.
2. AI BOT → профиль **Safe** (`[security] mode=safe`).
3. Не жмите Lua Features Activate, Scar-локи, Apply AI package.
4. Memory Activate + локи — по желанию (флаги для hybrid).
5. AUTO / Run `hybrid_o_safe` — observe + Lua-hold; макрос SendInput.
6. World для своего скрипта: **Send Data to Scar**, Lean snapshot.
7. Probe AUTO в рейтинге не включать.



### B. Скирмиш / vs ИИ (директор + Fine-tune)

1. Settings → **Offline**.
2. Профиль **Default** или свой с `mode=offline`.
3. При необходимости Lua Features **Activate** (сложность из config).
4. Fine-tune preset → **Apply AI package** после старта матча.
5. Опционально Scoring Lua (Warmonger / RiskyEcon) — это уже «ИИ играет слот», не только eco-director.
6. AUTO `hybrid_o_offline`. Не включайте AUTO `hybrid_c`.
7. Builder: локи/очереди → Save → **Apply locks** в матче.
8. Не включать, если в лобби есть другой человек (`HAS_OTHER_HUMAN`).



### C. Risk / свой OOS vs человек

Только если вы это осознаёте. Профиль `mode=risk`, trust Offline или Unsafe. Fine-tune и Enable AI = гарантированный desync.

### D. Только Relic Full AI, без hybrid

Lua Features Activate, оба Scar-лока Off, AUTO hybrid выкл. Fine-tune/scoring по желанию. Vs AI.

### E. Написать scoring Lua

1. Скопируйте `warmonger.lua` → `Lua Scripts\my_score.lua`.
2. Переопределите нужные `ScoringFunctions_*`. Init, если нужен `AI_Enable`, пишите явно.
3. Выберите файл в combo → Save профиль → Apply AI package в матче.
4. Функции `AIProductionScoring_*` зовите **только** из scoring callback Relic, не из `Rule_AddInterval`.



### F. Свой SCAR рядом с hybrid

1. Файл в `Scar Scripts\my_mod.scar` без `hybrid` в имени.
2. Files AUTO или Run после того, как hybrid уже встал (или наоборот — смотрите mutex только у hybrid_*).
3. Читайте SETTINGS/WORLD с Send to SCAR.
4. Не снимайте чужие TimeRule.

---



## 16. Что какая папка не делает


| Папка / кнопка        | Не делает                                                  |
| --------------------- | ---------------------------------------------------------- |
| `AI Profiles`         | Не personality VFS, не Fine-tune нативы, не Files Run. Load = оверлей; Apply locks / scoring / personality / fine-tune = матч |
| `AI Custom Templates` | Игра её не читает. Пока не нажали Apply AI package — матч не меняется |
| `AI Templates`        | Не плагин, не Run, правка не меняет игру. Ключ пакета = 4 ключа Relic, не bag |
| AUTO hybrid           | Не Send Data, не PLAN, не Fine-tune                        |
| Memory Activate       | Не `AI_Enable`                                             |
| Lua Activate          | Не `Game_AIControlLocalPlayer`, не Memory slab             |
| Apply locks           | Не обязан включать Relic AI                                |
| Scoring Lua           | Не hybrid desire, не train UnderCountLimit через SETTINGS  |
| Fine-tune PushScore   | Не train cap                                               |
| Files ваш `.scar`     | Не получает prepend `hybrid_core`                          |
| Вкладка Offline | Не Director (он на AI BOT). **Save / Load match** — натив `Event_SaveWithName` (RVA `0x202B7D0`), vs AI / скирмиш. Не ranked rejoin. Журнал `Matches\` — статистика, не симуляция |


---



## 17. Связанные файлы


| Путь                                               | Зачем                                       |
| -------------------------------------------------- | ------------------------------------------- |
| `AOE4HOOK/docs/AI_BOT.md`                          | Этот документ                               |
| `AOE4HOOK/docs/AI_SCORING_PIPELINE.md`             | Relic multiply-list, eco-native=0, `__EcoAct`, observatory |
| `AOE4HOOK/docs/decisions/ADR-001-cpp-ai-runtime.md` | C++ думает, SCAR применяет                 |
| `AOE4HOOK/docs/AI_SESSION_HANDOFF.md`              | Стадии Enable, поток Present, история крашей |
| `AOE4HOOK/docs/AI_UNIT_CONTROL.md`                 | Подгруппы, гарнизон, HUD, spawn-watch, разбор `rva=0x2A45959` |
| `AOE4HOOK/docs/ARCHITECTURE.md`                    | Устройство DLL, слои, поток данных, инварианты |
| `AOE4HOOK/docs/CPP_BRIDGES.md`                 | Feed, SETTINGS, PLAN, AV/OOS факты, рецепты      |
| `AOE4HOOK/docs/HYBRID_NATIVE_AUDIT.md`         | Hex-Rays гейты Fine-tune / Cancel / scoring |
| `AOE4HOOK/sdk/scar/hybrid_core.scar`               | Тело директора                              |
| `AOE4HOOK/sdk/scar/ai_builder.scar`                | Apply locks / Clear                           |
| `AOE4HOOK/sdk/lua/warmonger.lua`, `risky_econ.lua` | Сиды Scoring Lua                            |
| `AOE4HOOK/docs/PLUGINS.md`                         | Карта `AOE4HSettings`                       |
| `Documents\AOE4HSettings\AI Profiles\README.txt`   | Короткая карточка папки                     |
| `Documents\AOE4HSettings\AI Templates\CATALOG.txt` | Ключи SetPersonality / Lua stems            |
| `AOE4HOOK/docs/SCARTOOLKIT_FULL_PARITY.md`         | Соответствие STK ↔ вкладки оверлея          |


Игра 16.3.11308.0. Схема snapshot **10**. Метка моста `16.3.11308.bridge12`. Lua 5.3 (LUA_RUNTIME.md).
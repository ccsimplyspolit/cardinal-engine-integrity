# AI BOT «не работает» — кампания Wallingford (24.09 ~23:39)

PID Relic `37532`, overlay session с `23:39:21`. Диагностика по live
`aoe4_internal.log` + `warnings.log` (debug session `e377de`).

## Что видно в бою

| Источник | Факт |
|---|---|
| `warnings.log` | `Starting mission: data:scenarios\campaign\angevin\ang_chp3_wallingford\...` |
| `warnings.log` | Load из `save:autosave\ang_chp3_wallingford - autosave0.sav` |
| `warnings.log` 23:39:30.997 | `Player Императрица Матильда set to AI Type: Local Human Takeover` |
| overlay 23:39:30.544 | `[AI] session on … think=1` — сессия считает себя включённой |
| overlay 23:39:30.464 | standing+slot: `combat=77 locked=0 would4A70-live=0` |
| overlay дальше | `locked=0` всегда; `would4A70-live` → 85–90; stamp `n=0 already=0 ai-owned≈85–90` |
| overlay 23:39:30.608 | `intents … iCombat=0.00 iOffense=0.00 iEcon=1.00` age=3 opening=0 |
| overlay | `families_cut=6/7`, actuator v61 (family hard-cuts fail-closed) |
| prev log 23:29 | тот же класс: `locked=0`, краш `rva=0x3AD6A86` `last_native=army relock scan` |

UI tip уже говорит: *Does not take campaign autotest control. Use vs AI / local.*

## Гипотезы

| Id | Гипотеза | Вердикт |
|---|---|---|
| H1 | Standing / stamp не держат `+0x40` на армии | **CONFIRMED** — корневой баг ниже |
| H2 | Кампания «не поддерживается» | **REJECTED как продукт** (AI BOT должен работать везде). Takeover ок |
| H3 | Counter режет военку | **CONFIRMED** как усилитель |
| H4 | Eco contest без jobs | **INCONCLUSIVE** |
| H5 | Сессия не стартовала | **REJECTED** |

## Корневой баг (код + лог)

`StkAiTrackCollect` звал `TacticStackLive` как `tracking != 0` и писал `NoteEverLive` на **каждый** unlocked ряд. Первый `LogArmy` после Enable помечал всю армию `WasEverLive` → stamp: `live-stack=0 already=0 ai-owned=89`, `n=0` навсегда. Personality на enable не вызывался → campaign/event Takeover часто без scoring bag (комментарий 18.09 в `ai_session.cpp`).

## Фикс (verify в бою)

1. `TacticStackLive` = `ReadTacticVec == Live`; EverLive только на live stack.
2. Сразу после `eco_ai_on` — `StkAiTrackStampLockFlags` + `postStamp` / `LogAgentDebug`.
3. `AI_SetPersonality(g_aiPersonalityCustom)` в enable / full_ai (дефолт `default_campaign`).
4. Инструментация остаётся до verify.

## Verify #2 (~23:57 PID 23804) — locked ok, но нет vill / develop

| Лог | Факт |
|---|---|
| emptyUnlocked=83 → `eco_ai_on_nothink` | think deferred |
| stamp n=74 → later `eco_ai_on` | think=1, locked=74 |
| intents | haveJobs=true, eco=0/op=0, iCombat=0 |
| `g_ecoScoringApplied` | first inject **before** SetPersonality |

### H6 (no vill / no develop)

`InjectEcoScoring` once-per-match + `__EcoActGathWrap==2` latch: after
`SetPersonality` bag replaces `ScoringFunctions_*`, wraps gone, re-inject
no-ops → Gatherer never rebound → Relic does not train villagers / develop.

**Fix:** `InjectEcoScoring(force)` clears wrap/orig latches; call after
`RunEcoOnThink` / `RunEcoOnFullAi` / difficulty re-apply. Probe adds
`wrapGath=` / `gathType=`.

## Откат и починка 25.09 00:12

Откат исходников на `7b827891` оставил штамп как был. Поломка была не в
personality, а в правке `TacticStackLive`: пустой tactic перестал считаться
живым, шесть стартовых поселенцев стали `empty-unlocked`, think остался
выключен (`eco_ai_on_nothink`, рейтинг 00:05:23). В кампании тот же проход
поставил `+0x40` на 74 ряда и забрал экономику.

Штамп / `NoteEverLive` в том заходе не менялись. В `eco_ai_on` / nothink / full_ai добавлен
`AI_SetPersonality` (поле UI, иначе `default_campaign`) и force re-inject
scoring, чтобы bag Takeover получил Gatherer, а latch `__EcoActGathWrap`
не оставлял обёртку на старой функции.

## Влито 00:29 — `b2b7435574` / `96d6136639`

Пользовательские коммиты: в `StkAiTrackCollect` `NoteEverLive` только при
`ReadTacticVec == Live`. `TacticStackLive` остаётся `tracking != 0`.
DLL `00:29:41`. Ворота think по-прежнему считают пустой незалоченный ряд,
которого ещё не было в ever-live.

## 00:32 матч против ИИ — Gatherer нет в _G

`warnings.log` 00:32:54.178: think enabled, `empty-unlocked=0`.
00:32:54.180: `pers=default_campaign` `gath=nil` `wrapGath=nil`
`missing=ScoringFunctions_Gatherer` `workers=6/6` `have=1/7` (единственный
хит — наш `ScoringFunctions_House`). Ворота think тут ни при чём.
Обёртка выходила, если оригинала нет, и оставляла глобал пустым.
Запасной Gatherer: `__EcoActGathWrap=3`.

## 00:51 — сессия возвращена к `96d6136639`

`96d6136639` сам по себе только текст finding. Рабочий код бота — его родитель
`b2b7435574` (штамп: `NoteEverLive` только при живом tactic). Поверх этого
`ai_session.cpp` добавлял `AI_SetPersonality` на каждый enable, force
re-inject scoring и запасной Gatherer. Это и есть текущая поломка (00:40–00:47:
think включён, развития нет). `ai_session.cpp`, `log.cpp`, `log.h` сняты с
`96d6136639`. `stk_ai_track.cpp` не трогался. DLL в процессе 38172 всё ещё
сборка 00:49, пока игра держит файл.

## Проверка 01:06 PID 37192, DLL 01:03:25

Сессия как в `96d61366`: один `eco scoring inject`, строки `RE-inject` нет (0).
`01:06:25` think enabled, `empty-unlocked=0`. `01:06:32` штамп `n=5`, дальше
`live-stack` 1→10, `eco_contest` 13 раз за минуту, `locked=5`. ИИ раздаёт
приказы. Пользователь: бот работает.

## Горнило 01:16 `rogue_mongol_steppe`

`warnings.log` 01:16:21.860: `have=1/7 pers=default_campaign`
`missing=ScoringFunctions_Gatherer,...` `workers=6/6`. Think включён,
`would4A70-live=12`, штампа нет. Скирмиш 01:06 эту ветку не проходит:
там Gatherer у Relic есть, обёртка `wrap==2` та же. Если оригинала нет,
ставится запасной список (`wrap=3`). `AI_SetPersonality` не вызывается.

## 01:23 скирмиш и 01:24 горнило на DLL 01:21

Скирмиш: `Starting mission` 01:23:24.493, lua settle +1000 мс с 01:23:27.035,
think 01:23:28.204, первый `live-stack=7` в 01:23:30.111. Это ~6 с:
2500 мс после Starting mission (ворота OP20) + `ai_start_delay_sec=1` +
первый тик Relic. Лишнюю секунду убрал (`ai_start_delay_sec=0`). Паузу 2500 мс
после Starting mission тоже убрал: `kScarLuaAfterLoadMs = 0`. Ожидание
строки Mission Start на втором матче остаётся.

Горнило `rogue_mongol_steppe`: проба 01:24:20 `have=2/7`, Gatherer уже не в
`missing`, рабочих всё ещё 6. В 01:24:51 `would4A70-live=12`, штампа нет.
Директор запасной глобал не вызывает. Очередь
`Entity_QueueProductionItemByPBG` на `scar_town_center` только внутри ветки
`wrap=3`. Первый вариант обходил `Player_GetSquads` как таблицу; это SGroup,
цикл сразу выходил (01:34:45 `would4A70-live=12`, штампа нет). Теперь
`SGroup_ForEach` и EBP из `scar_villager`. Колбэк ForEach — `(group, index, squad)`. `Entity_QueueProductionItemByPBG` в `local_rules` (_v=23) не вызывается при `AOE4HOOK_TRUST<2`, даже если `MP_SAFE` сброшен. Очередь горнила на время этого вызова ставит trust 2 и сразу возвращает прежний. Скирмиш правило не ставит.

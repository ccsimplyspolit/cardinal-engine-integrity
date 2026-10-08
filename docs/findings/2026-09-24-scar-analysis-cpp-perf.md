# SCAR_ANALYSIS + chat bb333049 → AI BOT / FPS (24.09 ночь)

Источник: агент-чат SCAR full audit, каталог
`AOE4HOOK/internal/SCAR_ANALYSIS` (2821 контракт; recursive ~928 на момент
среза цели; окрестность hook 397 закрыта заметками). Живые RVA —
`runtime_exe.i64` / 16.3.11308.0.

## Что говорит аудит про «C++ вместо SCAR»

Канон [`96_ALTERNATIVES/ARCHITECTURE.md`](..\ARCHITECTURE.md):

| Слой | Роль |
|---|---|
| C++ | snapshots, planner, UI, leaf **чтения** (FULL только чистые copy без calls) |
| SCAR callback | штатная игровая операция / command flow |
| Прямой call inner из DLL | **не** рекомендуемый путь (return address вне Relic; integrity) |

`AI_Enable` (`0x293FA40`): не poke `AI+0x12F4`. Callable → dispatcher
`0x29175D0` (реестр `0x84C8C08`) → AI tid queue `0x2922980` / invoke.
Запись gate без очереди/TLS/world checks — не эквивалент.

`AI_LockSquad` (`0x2949A60`): тот же dispatcher; успех wrapper ≠ lock уже
применён (очередь). C++ heap `tracking+0x40` на **пустом** tactic vec —
данные, не `.text` (уже продукт: stamp). Native Lock после Enable при live
stack = strip / `0x2A45959`.

`AI_SetPersonality` (`0x294A440`): ищет AIPlayer, зовёт `0x2924FB0`; bag
reload на **AI tick**, не Present ([native-ai-cpp](2026-09-07-native-ai-cpp.md)).

## Уже C++ (не трогать как «перенос»)

- Think / counter / production rank / eco contest **планирование**
- `StkAiTrackStampLockFlags` (после фикса EverLive 24.09)
- World cache / radar RPM reads
- Present: `PostMessage` commit/contest, не `SendMessage`

## Топ FPS-выигрышей: урезать ScarDoString, не inner RVA

По live Wallingford (`aoe4_internal.log` 23:39): каждые ~4 с
`ai_lock_army_relock`, часто `ai_sel_pick`, `eco_contest`, реже `eco_ai_cuts`,
периодический полный `bridge` (~170 KB).

1. **Relock / sel_pick cadence** — scan-only уже без LockOneSid; постить реже
   или только при dirty skip-map / pending spawn (средний пункт [ai-opt-backlog](2026-09-07-ai-opt-backlog.md)).
2. **Bridge** — не публиковать полный `AOE4HOOK_AI_PLAN`, пока runtime armed
   и hybrid не читает.
3. **Contest** — jobs в C++; SCAR только тонкий `Issue` batch; не retry того же
   hash чаще интервала (уже есть fp).
4. **Cuts** — lean apply; не reinstall actuator.
5. **Пробы / census** — `AI_IsEnabled` / difficulty / counts через RPM
   (`Player+1578`, `AI+0x12F4`, `Player+0x69C` … из карточек), не DoString.

## Не делать «для FPS»

- Poke `+0x12F4` / Reload bags с Present
- Прямые inner с DLL RIP ради Enable/Lock/Personality
- Второй SCAR OS-thread / свой `lua_State` без нативов
- Запись entity position / resources в обход command flow

## Связь с фиксом AI BOT «везде» (тот же вечер)

Stamp был мёртв из‑за `NoteEverLive` на любом unlocked (`TacticStackLive=ptr`).
Это ровно C++-путь, который аудит рекомендует для lock flag. Personality на
enable закрывает дыру campaign/event Takeover без scoring bag. Verify:
`postStamp>0` / `locked>0` в `debug-e377de.log` + `aoe4_internal.log`.

## Проход 25.09 00:03 (каталог, не live)

Пока рейтинг на PID 23804 / DLL 23:56 — игру не закрывали, DLL не пересобирали.

C++/RPM вместо горячего `ScarDoString`:

| Уже или можно читать | Поле |
|---|---|
| Lock stamp | `tracking+0x40` в `*(AI+0x1000)+0x30` |
| Слот / think | `AI_IsAIPlayer` = `Player+0x62A`; `AI_IsEnabled` = тот же байт + реестр `0x84C8C08` + `AIPlayer+0x12F4` |
| Ресурсы | `Player_GetResources` = 40 байт с `player+0x16C` |
| Позиция | `Entity+0x2C` (12 байт) |
| Сквады | список `player+0x6A0` |
| Selection | `Misc_GetSelectedSquads` контейнеры `+1000` / `+952` |

Остаётся SCAR: `LocalCommand_*` (submit `0x1AA5A50`; SquadSquad kind 4, SquadEntity kind 3), `GE_EntitySpawn` + `AI_LockSquad`, `AI_Enable`, `Game_AIControlLocalPlayer`, apply cuts / PushScore. Прямой call из DLL режет TopValidator `0x3DDD02C`. `AI_DoString` `0x293FAF0` — не overlay `ScarDoString` `0xAA9B00`.

## Рейтинг PID 23804, ~00:05–00:10 (warnings.log + overlay)

Relic `Local user framerate`: 158–194, провал **95.5** в 00:10:03, затем 130 и 154. В overlay за этот матч нет строк `[FPS]` (периодический table не писался) и нет `GPU Present` skip. Просадки совпали с `[WORLD] collect` **108 ms** и **115 ms** (`readFaults` 14k–34k, n≈712–717). До матча: SEH `army relock scan` в 23:59:02 и 00:01:04; GPU Present 472–535 ms. В матче SEH нет. `(E)` в warnings — лобби/Steam до 00:01, не сим. За ~5 мин SCAR: relock 58, eco_contest 47, cuts 35, bridge 10 × ~69 KB.

## 25.09 00:39 — что из каталога нельзя переносить в вызов из DLL

Карточки `SCAR_ANALYSIS` на функции, которыми живёт AI BOT:

| Функция | Карточка | Вывод |
|---|---|---|
| `AI_Enable` | `05_COMBAT/AI_Enable.md` | C++ poke gate не равен очереди/TLS/world. Остаётся SCAR |
| `AI_IsAIPlayer` | `05_COMBAT/AI_IsAIPlayer.md` | C++ alternative **UNKNOWN** (не чистый leaf). Direct call CONDITIONAL из‑за return address / TopValidator `0x3DDD02C` |
| `AI_IsEnabled` | `05_COMBAT/AI_IsEnabled.md` | Чтение `Player+0x62A` + реестр `0x84C8C08` + `AIPlayer+0x12F4`. Один байт gate не равен функции |
| `Player_GetResources` | `01_PLAYER/Player_GetResources.md` | C++ alternative **FULL** как копия в свой буфер. Рекомендация карточки: снять штатным callback и кешировать, не звать inner из DLL |
| `ScoringFunctions_Gatherer` | scoring context | Factory только внутри production scoring. 00:32:54 Takeover: `gath=nil` в `_G` |

Уже C++ и от сессии SCAR не зависит: план, cuts, desire, штамп `+0x40`, снимок radar (позиция, рабочие). Команды (`LocalCommand_*`, `AI_Enable`, `AI_LockSquad`, `AI_SetPersonality`) остаются тонким SCAR: иначе desync и TopValidator.

Сделано в этой сборке: если мешок не положил `ScoringFunctions_Gatherer` в `_G`, сессия ставит свой список (`__EcoActGathWrap=3`). DLL `InternalInjector.dll` 00:39:09.

## Прогон 00:40 (DLL 00:39) — запасной Gatherer не сдвинул бота

Think включился: `00:40:46.234 empty-unlocked=0`. Дальше 4 минуты
`would4A70-live` 12→16, `combat=0`, `locked=0`, `ecoLock=1 families_cut=7/7`,
в `warnings.log` нет age-up. Проба `gath=` в warnings не попала. Третий
`eco_ai_score_re` в ту же секунду имеет `len=2148` при первых двух 36–37 KB.

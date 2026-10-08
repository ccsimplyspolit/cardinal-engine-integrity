# Подгруппы, гарнизон, выделение и HUD ИИ

Игра: Age of Empires IV **16.3.11308.0**. Всё описанное живёт на вкладке **AI BOT** и работает только при включённой сессии (`Enable AI`).

Четыре независимые функции, добавленные поверх сессии:

| Функция | Галочка | Ключ `config.ini` `[scripts]` |
| --- | --- | --- |
| Лок выделения | `Selected villagers stay mine` | `ai_sel_lock` (**по умолчанию On**) |
| Лок подгрупп | `Lock control groups to me (Ctrl+1..9)` | `ai_group_lock` |
| Лок гарнизона | `Keep garrisoned units inside` | `ai_garrison_lock` |
| Панель AI BRAIN | `Show AI HUD in match` | `ai_hud` |

Галочки **не сохраняются автоматически** — жмите **Save**. `ai_sel_lock` при отсутствии ключа читается как On.

---

## 1. Что чем управляет

Разделение, которое легко перепутать:

| Кто | Что держит |
| --- | --- |
| **Army lock** (шаг 1 сессии, **до** `AI_Enable`) | **Все** боевые сквады. Стоящие лочатся, пока ИИ выключен. После Enable новые боевые — Relic `GE_EntitySpawn` + `AI_LockSquad` на `event.entity` (ScarToolKIT `Hybrid_OnSpawn`). Scan / cache-id только pending. C++ **не** зовёт `LockOneSid` (01:24 → 4A70). `Cmd_Stop` после Enable не зовём (`rva=0x1ED5529`). Relock scan-only. Пока армия у игрока, Relic attack/front/clump ≈ 0. Relock SEH **не** сбрасывает VM. |
| **Лок выделения** | Крестьяне, которых игрок **сейчас** выделил (+ 15 с после снятия, и пока они в здании) |
| **Лок подгрупп** | То, что игрок положил в Ctrl+1..9 — **крестьяне и здания** |
| **Лок гарнизона** | Отряды внутри зданий + сами здания-держатели |
| **Relic AI** | Всё остальное: экономика, застройка, апгрейды, стартовые разведчики. Синоби (30.09) и Жанна д'Арк в любой форме, крестьянка тоже (01.10), — у игрока |

Армия у игрока **независимо от подгрупп** — army lock забирает боевые сквады сам. Война за крестьян (выгнал в ратушу — ИИ вытащил обратно) закрывается локом выделения, не army lock.

---

## 2. Лок выделения крестьян

Это и есть ответ на «ИИ отменяет гарнизон крестьян». Relic eco-ИИ владеет крестьянами. Игрок даёт `SCMD` на ратушу, ИИ на следующем think снимает приказ и гонит обратно на ресурс. `pcall` вокруг приказа не помогает — приказ проходит, ИИ его перебивает.

**Алгоритм** (тот же, что `SpatialWorldModel.TickManualSelectionControl`, но lean-сессия SWM не грузит):

1. Тик C++ каждые 300 мс, `Misc_GetSelectedSquads` → крестьяне и уже залоченные обычные монахи.
2. На выделенного крестьянина — `AI_LockSquad`, если RPM видит **пустой** tactic stack (нет tracking → 4CE0; tracking + пустой stack → 4A70 только ставит лок). Живая тактика (`WouldStrip`) — **не** зовём натив; тик повторяет каждые 300 мс и ещё **15 с** после deselect, пока think не отпустит сквад. `SCMD_Stop` / `AI_LockSquads` не используются. Разведчиков этот тик не берёт.
3. Снял выделение — ещё **15 с** (`World_GetGameTime`), чтобы дойти до ратуши.
4. Пока `Squad_IsInHoldEntity` — лок держится (рейд). Вышел из здания и не выделен — сразу обратно ИИ.
5. **Монахи.** До латча или до 600 игровых с с первого появления (`monkOverdue`), что раньше, — ровно первые **2 обычных** монаха остаются у Relic (12.09: было 3), все остальные и все боевые монахи принадлежат игроку. Японские синто / буддист / landmark — обычные (`monk`, не только `scar_monk`). Пока двое у Relic, Layer B держит `religion=1` и `monkCap>=2`: иначе boom (`religion=0.12`) оставляет монахов стоять (13:22). Army-lock сажает Relic attack/offense, поэтому Relic после первого `PickUpRelic` больше не вешает следующий (13:47–13:58: 7↔6, монахи вернулись и стоят). Lean раз в 2.5 с шлёт `pickup_relic` / `monk_statetree_deposit_relic` только idle-бегунам; живой pickup/deposit не рестартим. Relic's 2 никогда не pending, не `Cmd_Stop` и не army-lock, пока не сработал латч и не истекли их 600 с (просроченный сборщик дальше как лишний: pending, `MONKS`, `MONKLIVE`): иначе сбор реликвий срывается, а relock по живому tracking даёт `rva=0x2A45959` (11:22). Пока think включён, `lockOne` по обычному монаху **не** зовёт `AI_LockSquad` (`rva=0x1ED5529`, 11:40, `in_call=1`) — только pending. Лишние монахи запрашиваются сразу, сборщики — по латчу (III эпоха + 300 игровых с) или через 600 игровых с после того, как скан впервые увидел юнит (`monkOverdue`, 01.10), что раньше. Запрос — `[AOE4HOOK_CONTROL MONKS]`; C++ ставит только +0x40: на пустой строке tactic сразу, на живой — только для sid из `[AOE4HOOK_CONTROL MONKLIVE]` (просрочен и не занят реликвией: не несёт, не подбирает, не сдаёт; после 720 с — в любом случае). Несущего реликвию до 720 с не запрашиваем вовсе. До 01.10 ждали только пустую строку, а think заполняет её в том же проходе: 19–145 с задержки, без верхней границы. Ничего из вектора не вынимается (4A70). Канал Lua→C++ — только `print` в warnings.log; если он молчит (первый матч 01.10), C++ пишет `control feedback silent`. Спавн без имени не считается армией. Святыни handover не задерживают. Shaolin / warrior monk / ikko всегда игроку.
   После реликвий hybrid (offline/risk) шлёт **каждой свободной** святыне `Cmd_AttackMoveThenCapture` (fallback `Cmd_MoveToThenCapture` / `Cmd_AttackMove`). **Safe не захватывает.** Lean AI BOT без hybrid capture-команд не шлёт.
6. **Разведчики** этим тиком не забираются. Тот же native, что краш Ctrl+1 на ИИ-скауте.
7. Ctrl+1..9 и галочка гарнизона имеют приоритет: их юнитов этот тик не отпускает.

`AI_LockSquads` не используется. Relic TimeRule нет.

Галочка **Unit control → Selected villagers stay mine**, ключ `ai_sel_lock`. По умолчанию On.

Долго держать крестьян у себя без выделения — Ctrl+1.

---

## 3. Лок подгрупп

Нажатие **Ctrl+0..9** снимает снимок текущего выделения и лочит его за игроком.

Поведение:

- Лочатся **крестьяне** (`AI_LockSquad`) и **здания** (`AI_LockEntity`). Combat держит army lock; после Enable новый боевой лочится Relic EventRule (`event.entity`). Scan / cache-id только pending. C++ `LockOneSid` после Enable нет. `Cmd_Stop` после Enable нет.
- **`AI_LockSquads` не используется.** Inner `0x296D680` при наличии tracking **всегда** идёт в 4A70 (нет skip `+0x40`). После Enable это тот же `rva=0x2A45959`.
- Переназначение подгруппы отпускает тех, кто из неё вышел — но только если они не состоят в другой подгруппе и не в `__ArmyLock_LockedSquads`.
- Выключение галочки и `Disable AI` возвращают ИИ то, что группа реально лочила (виллы/здания), не боевую армию.
- Состояние живёт в Lua: `__GroupSets[N] = { s = {sid...}, e = {eid...} }`, объединение в `__GroupLocked`.

### Как читается выделение

Это оказалось самым сложным местом. Три подхода, два из которых провалились **молча**:

1. **RPM** `ReadUiSelectionIds` (`HUD+0x198 vec+0x3A0`) — возвращает `n=0` на этой сборке. Поле `RadarWorldEnt.uiSelected` из-за этого всегда пустое.
2. **`Misc_GetSelectedEntities`** — возвращает `sel=0`.
3. **`Misc_GetSelectedSquads`** — **работает**.

Итоговый каскад в `StkGroupLockOnAssign`:

```
Misc_GetSelectedSquads  →  Misc_IsSquadSelected (пообъектно)
Misc_GetSelectedEntities →  Misc_IsEntitySelected (пообъектно)
```

Общее правило, подтверждённое дважды: **в AoE4 надо спрашивать сторону отрядов, а не сущностей.** Гарнизон починился ровно тем же переходом.

Если хоткеи подгрупп переназначены в игре с Ctrl+цифра — детект (`PollControlGroupAssign` в `hotkeys.cpp`) не сработает.

### ⚠ Главный краш: лок отряда с живой тактикой ИИ

Это **не** особенность подгрупп и **не** особенность разведчиков. Падает любой путь, который зовёт `AI_LockSquad` по отряду, который think-поток ИИ уже трекает.

Подпись одна и та же:

```
[CRASH] code=0xC0000005 rva=0x2A45959 av_type=0 av_addr=0x58 rax=0
        scar=-  scar_tid=0  in_call=0
```

`in_call=0` — краш **вне** SCAR-вызова, ~0.5 с после лока, в тике ИИ. Функция `sub_7FF6F9005930` (RVA `0x2A45930`): геттер `0x2924350` вернул 0, следующая инструкция `mov ecx, [rax+58h]` без проверки.

`AI_LockSquad` (`0x296D2E0`):

| Состояние отряда | Путь | Эффект |
| --- | --- | --- |
| Нет tracking-объекта | очередь **4CE0** (`player+0x3E30`) | лок, тактики не сносит |
| Tracking есть, `[obj+0x40]==0` | **4A70** (vtable+0x18 + strip `3920`) | тактики снесены → следующий think читает NULL+0x58 |
| Уже залочен (`+0x40 != 0`) | no-op | безопасно |

`AI_LockSquads` (`0x296D680`): tracking есть → **всегда 4A70**. Skip `+0x40` нет. После Enable батч падает так же, как N одиночных локов. В подгруппах не используется.

`AI_Enable` пишет только `player+0x12F4`. Think гейтится этим байтом; evaluator краша — **нет**. Отсюда: лок **до** `AI_Enable` (нет tracking → 4CE0), а не после. Страх «нет AI player → тот же AV» не подтверждается дампом: пустой геттер без предшествующего strip этот RVA не бьёт.

Документация натива: *«Locks the squad and **disables its tactics (if any)**»* — это как раз путь 4A70.

Здания — другой натив (`AI_LockEntity`, без strip 4A70). Крестьяне идут в тот же `AI_LockSquad`, что combat/scout: отдельного `scar_villager` в Hex-Rays нет. **Стартовый scout** / хан 1–2 army lock пропускает по `unit_scout_*` / `scar_scout`. **Hippodrome Scout** / **Riddari** / **арбалетчики Золотого Рога** — игроку на standing scan (AI выкл, 4CE0). После Enable `LockOneSid` **не** зовёт `AI_LockSquad` по `scar_scout` / `scar_hippodrome_scout`: Relic `scoutPlans` + 4A70 = `rva=0x2A45959` (03:03:05). У dummy PBG часто нет `scar_horseman`, лок на скан идёт по имени.

#### Краш 1 — Disable → Enable, лок через ~10 с после `AI_Enable` (2026-09-02 01:07)

43-я минута, French, эпоха 3, 41 боевой отряд:

```
01:07:22.004  [AI] session off handover=1      <- Disable: AI_UnlockAll, армия у ИИ
01:07:27.522  [AI] session on ...              <- Enable: AI_Enable(true)
01:07:37.285  [AI] session army lock on        <- +9.8 с: AI_LockSquad × 41
01:07:37.848  [CRASH] rva=0x2A45959 av_addr=0x58 rax=0 in_call=0
```

`Disable` отдаёт ИИ всю армию. Staged-пауза даёт ИИ время повесить тактики; потом `AI_LockSquad` идёт в 4A70.

Коммит `4864ebf` забирал армию **в том же** `AiSessionService`, что `eco_ai_on` — это нужно сохранить. Порядок там остался `AI_Enable` затем `AI_LockSquad`; лок **до** Enable не брали из страха «нет AI player». Натив говорит обратное: после Enable tracking уже может быть, и тот же кадр всё ещё гонка с think-потоком.

**Слитый фикс:** и первый Enable, и повторный лочат стоящую армию **до** `AI_Enable`, в том же вызове сервиса. Флаг `g_liveOnceThisMatch` (живёт от `AiSessionOnVmReset` до `AiSessionOnVmReset`, Disable его не трогает) только отличает лог.

#### Краш 2 — стоящий скан 1.5 с, пока ИИ уже живой (2026-09-02 02:13)

Тот же RVA, уже **без** Disable/Enable. Сессия включилась в 01:53 (`army lock on (before AI_Enable)`), AUTO hybrid выкл. В 02:13:30 — AV; за ~3 с до этого три спавна `unit_archer_3`. Тик `__ArmyLock_Tick` после 20 быстрых проходов всё ещё сканирует каждый 4-й (~6 с) и зовёт `AI_LockSquad` по сквадам, которые ИИ уже трекает → 4A70.

`4864ebf` как раз **оставлял** этот тик навсегда (idle вместо `Rule_Remove`), чтобы после Toggle подбирать то, что пропустил `GE_EntitySpawn`. Это чинит «монах остался у ИИ» ценой краша.

**Слитый фикс:** тик **снимается**. Relic `GE_EntitySpawn` с `event.entity` после Enable — `AI_LockSquad` (STK `Hybrid_OnSpawn`; 01:09:13 был late overlay `Local.AddPlayerEvent`, не Relic EventRule). Scan / cache-id после Enable **не** лочат (`pending-ai-live`). C++ не `LockOneSid`. Sid нет в RPM-карте ≠ 4CE0. C++ spawn-watch только prime + skip, пока `AiSessionLive()`. Повторный Enable снова делает один standing-скан, пока ИИ выключен. **Нет** `Hybrid_SweepLocks` / `__ArmyLock_Tick` / `AI_LockSquads` после Enable.

#### Краш 3 — cache-spawn после Enable, старая DLL (2026-09-02 22:49)

Тот же RVA. VEH `in_call=0`, поток think, `last SCAR=ai_sel_tick` (~188 мс до AV). Overlay-лог этой сессии стёрт реинжектом 23:04 (`wiped 41`). Relic `unhandled.2026-09-02.22-51-08` — рестарт; в `22-10-44` в 22:49:04 `BattleServerRelay` 280 мс (игра уже умирала).

Army Lua в том матче: `hash=0x4AC92DB5` / «GE_EntitySpawn only» — **старая DLL**, без slot-then-lock. `AUTO=0`, так что stale `hybrid_core` (Documents beta.6) **не** бежал. `ai_sel_lock=1`, group/garrison off. Последние `ai_lock_army_spawn` — 22:48:00 / 22:48:02 (ids 1000008290 / 1000008293), за ~61 с до AV.

Два 4A70-источника, оба живы в DLL *после* slot-fix (подтверждено в матче 23:05, hash `0x33E62F84`):

1. **C++ spawn-watch** шлёт `__ArmyLock_OnEntityId` после `AI_Enable`. Кэш позже спавна → think уже трекает → 4A70. В 23:10:51 и 23:10:57 та же DLL снова вызвала `ai_lock_army_spawn` (ids 1000006323 / 1000006325).
2. **Sel lock** — `__SelLock_Tick` каждые ~300 мс; первый `AI_LockSquad` по ИИ-крестьянину после Enable — тот же native. Эмпирика «36 мин без AV» не доказывает skip 4A70. `pcall` AV не ловит. Lua **не** читает tracking `+0x40`.

**Слитый фикс cache-пути (live RPM 2026-09-02 pid 52828):** `stk_ai_track.cpp` читает `*(AI+0x1000)+0x30` (16-byte `{u32 key, ptr}`). Ключ = **`Squad_GetID` (~50xxx)**, не radar/TLS id (~1.000.021.xxx) и не то, что Hex-Rays подписывает как `entity+0xA0` для этого вектора. Lua `lockOne` тоже на `Squad_GetID`. Skip-таблица и `AOE4HOOK_AI_LOCK.strip` публикуют эти ключи (world snapshot + sel tick + `ai_lock_skip_map`). Radar id в карте не ищется (miss ≠ «нет tracking»). После Enable C++ cache-spawn **не** зовёт `AI_LockSquad`. Relic EventRule с `event.entity` лочит (STK `Hybrid_OnSpawn`, `fea27989`). Cache `{id=…}` остаётся pending. C++ не `LockOneSid`. Unlocked tracking никогда не `L.safe` (23:34 empty stack всё ещё 4A70). Miss / unknown → skip, не 4CE0. Tracking → `__LockWouldStrip`. Think 0x2923300 skip locked только если tactic stack пустой — live-stack `+0x40` не крадёт. Native 4A70 на пустом unlocked по-прежнему AV; C++ stamp `+0x40` (куча, не `.text`) перед Enable. `__ArmyLock_Tick` снят. Think-off steal запрещён.

**Sel lock** после Enable: `WouldStrip` только если tactic stack **живой**. Idle / пустой stack — `AI_LockSquad` (4CE0 или 4A70 без strip). Gathering — skip натив и повтор каждые 300 мс плюс 15 с после deselect (`sel skip-live sid=` / `AI_LockSquad sel sid=`). Combat / scout / AI relic-monk по-прежнему не берём. `SCMD_Stop` не зовём.

**Не** `SCMD_Stop` перед локом. **Не** `AI_LockSquads` после Enable. **Не** `__ArmyLock_Tick`.

**Не** пытайтесь гасить тактику перед локом (`SCMD_Stop` уже пробовали — стало хуже) и **не** заворачивайте падающий натив в `pcall`: он не ловит AV.

### Ловушка: тик после Toggle vs standing 4A70

В логе 01:07 после Disable→Enable тик `__ArmyLock_Tick` снимал себя и не возвращался: `__ArmyLock_Installed` уже `true`, ранний `return` не ставил `Rule_AddInterval`. До конца матча оставался только `GE_EntitySpawn`. Коммит `4864ebf` оставил тик idle навсегда — и это краш 02:13.

Слитое поведение: тик **снимается намеренно**. После Enable новые боевые **не** лочатся Relic `GE_EntitySpawn` (pending; 01:09:13). Cache / Scan — pending. C++ backup — `Safe4CE0` из `%TEMP%\aoe4_army_pending.txt`. Стоящая армия на Toggle — один скан в `kArmyOn`, пока ИИ выключен (`__ArmyLock_StandingScan`). Монах, которого ИИ должен вести на реликвию, и так остаётся у ИИ по правилу keeper.

`Rule_AddInterval` под `__*_Installed` по-прежнему нельзя «убить и ждать, что re-inject его вернёт» — либо не снимать, либо снимать и не ставить снова, как с `__ArmyLock_Tick`. `GE_EntitySpawn` EventRule после Disable снимается в `kArmyOff` и **должен** ставиться снова в `kArmyOn` даже если `__ArmyLock_Installed` (иначе остаются только поздние cache-diff).

### Что уже пробовали и не помогло

Чтобы не ходить по кругу:

| Попытка | Результат |
| --- | --- |
| Батч `AI_LockSquads` вместо N × `AI_LockSquad` | Краш остался — inner всегда 4A70 при tracking |
| `LocalCommand_Squad(..., SCMD_Stop, ...)` перед локом | **Хуже**: AV прямо внутри скрипта (`in_call=1`), валит SCAR-VM. Откачено |
| Забирать армию в том же кадре, но **после** `AI_Enable` | Гонка с think; тот же RVA |
| Оставить `__ArmyLock_Tick` 1.5 с / каждый 4-й, пока ИИ live | Краш 02:13: standing 4A70 |
| Relic `Rule_AddPlayerEvent(GE_EntitySpawn)` после Enable **без** `event.entity` / со stale skip-map | EventRule 03:06:44 `sid=50353` и 01:09:13 7-spawn → 4A70. Сейчас: EventRule / cache `{id}` / Scan → pending; C++ только живой `Safe4CE0`; WouldStrip блокирует think-owned |
| Лок стоящих **до** `AI_Enable` + spawn-only после | Путь 4CE0 на standing; cache-after-Enable оказался 4A70 (краш 22:49 / лог 23:10) |
| RelockFresh + `L.safe` в тот же тик, что спавн | `rva=0x1ED5529` внутри `AI_LockSquad` (`in_call=1`, 11:40 / 12:02). SEH **не** сбрасывает VM. Один ядовитый sid уходит в `__ArmyLock_NativeSkip`; relock продолжает остальных. Вечный park оставлял `locked=63` при `combat→95` |
| Relock Scan зовёт `AI_LockSquad` после Enable | `rva=0x1ED5529` (12:15, `in_call=1`). Lua `io.open` не перезаписывает `aoe4_scar_last.txt`; VEH видел `standing+slot`, skip-first бил вслепую, `poison=0`, AV каждые 5–8 с. Теперь Scan только классифицирует; C++ пишет `AI_LockSquad relock sid=` и лочит один `L.safe` sid |
| `AI_IsEnabled` врёт / лок новорожденного `L.safe` | `rva=0x1ED5529` (12:28:40 sid=50270, 12:28:45 scan) и think `rva=0x2A45959` (12:28:55). `__ArmyLock_ThinkOn`; Scan/Stop/Lock раздельно; лок после 2 с в `L.safe` |

Важное про `pcall`: он ловит ошибки Lua, но **не** access violation внутри нативной функции. Обёртка `pcall` вокруг падающего натива не спасает.

Рабочая идея: **не гасить тактику, а не звать `AI_LockSquad`, пока think её держит.**

Что осталось, если AV вернётся: смотреть `last_native` в VEH (`%TEMP%\aoe4_scar_last.txt`). `AI_LockSquad spawn sid=` / `cache` — EventRule или окно до Enable. `AI_LockSquad sel sid=` — лок выделения, Lua не видит `+0x40`, полностью убрать 4A70 нельзя, не отказавшись от фичи.

---

## 4. Лок гарнизона

Тик **C++** `StkGarrisonLockTick` каждые 2 с (`pcall __GarrisonLock_Tick`). Relic `Rule_AddInterval` нет.

1. `Player_GetSquads` → для каждого `Squad_IsInHoldEntity(sq)`
2. Отряд в гарнизоне → `AI_LockSquad` **только если** ИИ выключен, или сквад уже в `__ArmyLock_LockedSquads` / группе, или это `scar_villager`. Чужой трекаемый combat в башне не лочим (4A70).
3. Здание-держатель через `SGroup_GetGarrisonedBuildingEntity` → `AI_LockEntity` (только для тех пассажиров, которых реально локнули)

Здание лочится обязательно для наших пассажиров: выгрузка отдаётся командой **на здание** (`Entity_UnloadAllFromHold`, `SCMD_UnloadSquads`), а не на отряд. Залочить только пассажиров недостаточно.

Когда здание пустеет, оба отпускаются автоматически — иначе за матч ИИ лишился бы всех крестьян, когда-либо заходивших в ратушу. Не отпускаются два случая: id закреплён подгруппой (`__GroupLocked`) или отряд под army lock.

Ставится **после** army lock, чтобы не соперничать за SCAR-вызовы на старте матча.

### Почему сначала не работало

Первая версия шла со стороны зданий: `Player_GetAllEntities` → `Entity_IsHoldingAny`. Натив существует и не падает, но **ни разу не вернул true** — трассировка показывала `scanned=18, ents=0` при живом гарнизоне. Переход на `Squad_IsInHoldEntity` починил сразу: `scanned=8, ents=3, squads=3`.

---

## 5. Панель AI BRAIN

Слот `HudPanel::AiBrain`. **Ctrl** — перетащить, клик по заголовку — свернуть, позиция в `[hud] ai_brain_x/y/custom`.

Содержимое: `AiPlannerGetSnapshot()` + при контрпике `AiProductionGet()`:

- эпоха и число крестьян, либо статус сессии
- `MASS` / `UPGRADE` + текстовая причина (`reason`)
- **Хочет строить** — `need[]`
- **Моя армия** / **Враг** — состав, тиры кузницы и университета, `perCav`
- **Контрпик** — роль C++, **План / SCAR** (`generation / commitGen`), top-3 ранга observatory
- **Скоринг** — Fine-tune фронт / оборона / атака / кучность + сбор Е/Д/З/К

Нулевые строки и пустые секции **не рисуются** — панель компактная в ранней игре и разрастается по ходу матча.

Изменившийся Fine-tune скоринг подсвечивается 6 с. При `apply=0` значения приглушены с пометкой — иначе легко решить, что они уходят в игру.

**Цена по FPS нулевая:** панель копирует снапшот / observatory. Ни одного своего SCAR-вызова. Каты идут `WM_SCAR_AI_COMMIT`, не из HUD.

### Ловушка: HUD не получал данные

`AiPlannerUpdate` вызывается только при `WorldComputeDemand().aiPlan`. Сессия раньше входила туда через `AiSessionWantsWorldCache()`, где было `&& AnyCounter()`. При выключенных галочках контрпика планировщик не работал — HUD показывал нули.

Исправлено: `AiSessionWantsWorldCache()` = `wanted && ecoLive` (spawn-watch без контрпика), плюс `d.aiPlan` имеет `|| (AiSessionWanted() && AiHudWantsPlan())`. При `AiRuntimeArmed()` planner ~2 с. **Появится новый потребитель снапшота — не забудьте про ту же строку.** Фильтры камеры / ESP не должны урезать AI-снимок.

Аналогичная ловушка была с `d.uiSel` для подгрупп: поле `uiSelected` заполняется только по запросу, и лок подгрупп его не запрашивал.

---

## 6. Что нельзя прочитать

Relic не даёт геттеров для fine-tune:

```
AI_SetResourceIncomeDesire( player, resourceType, desiredIncome )   -- только setter
AIPlayer_SetGathererDistributionOverride( player, luaGatherDistro ) -- только setter
```

Ни `AI_GetResourceIncomeDesire`, ни `GetGathererDistribution` не существует. Есть `AIPlayer_GetStateModelFloat(player, key)`, но он требует недокументированных внутренних ключей.

Поэтому при `apply=0` в меню дохода показывается **измеренная реальность** — сколько крестьян фактически на каждом ресурсе (`RadarCountOwnGatherers`), а не мёртвые числа пресета.

---

## 7. Диагностика

Зонды из отладки убраны, чтобы не тратить кадры. В `aoe4_internal.log` остались только событийные записи:

```
[STK] group lock on / off
[STK] group N assign sent (NNNN B)
[STK] garrison lock on (C++ tick, no TimeRule)
[STK] selection lock on / off
[STK] selection lock installed (C++ tick, no TimeRule)
sel skip-live sid=… / AI_LockSquad sel sid=…   -- warnings.log / last_native (живой stack vs реальный лок)
[STK] spawn watch primed self-units=N combat=C workers=W cache=M (no lock this pass)
[STK] army lock script ok slot=1 first=1 self-combat-cache=C workers=W
[STK] army native map why=standing+slot ai=… combat=C locked=L would4A70=N (keys=Squad_GetID)
[STK] army cache-spawn 4CE0 n=N id0=… skipped-4A70=0
[STK] army cache-spawn skip n_strip=N (no untracked combat; EventRule owns spawn)
[STK] army EventRule GE_EntitySpawn ok=…   -- warnings.log / scartrace
[STK] spawn watch: Relic EventRule fallback (cache empty …)   -- плохо: кэш не поднялся
```

Если понадобится вернуть подробности — трассировки писались через `print()` + `scartrace()` в **`Documents\My Games\Age of Empires IV\warnings.log`** (не в `aoe4_internal.log`), маркеры были `[AOE4HOOK-GRP]` и `[AOE4HOOK-GAR]`.

### Ловушка: обрезка генерируемого Lua

Скрипт подгрупп собирался в `char lua[6144]` через `_snprintf_s(..., _TRUNCATE, ...)`. Скрипт вырос до 6409 байт, `_TRUNCATE` **молча** обрезал его посреди `end`, и игра показала:

```
[AOE4HOOK] compile: [string "local okP, player = ..."]:175: syntax error near 'if'
```

Обрезка не является ошибкой и никуда не логируется — симптом выглядит как «сломался Lua», хотя Lua корректен.

Теперь размер считается из формата (`_scprintf`) и пишется в `std::string`. **Не возвращайте фиксированные буферы под растущие скрипты.**

Рецепт проверки перед сборкой:

```bash
# выгрузить литерал из .cpp, собрать Lua, прогнать парсером
python -c "from luaparser import ast; ast.parse(open('group.lua').read())"
```

Если парсер говорит OK, а игра ругается на синтаксис — ищите обрезку, а не синтаксис.

---

## 8. Файлы

| Файл | Роль |
| --- | --- |
| `internal/InternalInjector/stk_lua_lock.cpp` | `StkGroupLock*`, `StkGarrisonLock*`, `StkSelLock*`, army/villager lock, C++ spawn-watch |
| `internal/InternalInjector/hotkeys.cpp` | `PollControlGroupAssign` — детект Ctrl+0..9 |
| `internal/InternalInjector/radar.cpp` | `ObserverDrawAiBrain`, `RadarCountOwnGatherers`, демады `d.aiPlan` / `d.uiSel` |
| `internal/InternalInjector/hud_drag.h` | слот `HudPanel::AiBrain` |
| `internal/InternalInjector/ui_scar_lanes.cpp` | галочки и комбо пресетов на вкладке |
| `docs/AI_SESSION_HANDOFF.md` | сессия, стадии инжекта, история крашей |
| `docs/AI_BOT.md` | общая дока вкладки |

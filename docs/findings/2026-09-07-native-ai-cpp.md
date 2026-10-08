# 2026-09-07 — Native Relic AI vs C++ без SCAR

Сводка по вопросу: можно ли крутить Relic AI напрямую из C++, без `ScarDoString`.
Канон слоёв: [AI_SCORING_PIPELINE.md](../AI_SCORING_PIPELINE.md), [ADR-001](../decisions/ADR-001-cpp-ai-runtime.md), [AI_UNIT_CONTROL.md](../AI_UNIT_CONTROL.md), [HYBRID_NATIVE_AUDIT.md](../HYBRID_NATIVE_AUDIT.md).
RVA: `sdk/offsets/RelicCardinal_16.3.11308.h`, struct `sdk/structs/known.h` `AiPlayer`.

## Что такое «native AI»

Это **не** Lua-бот. Это C++ `AIPlayer` + свой **AI-поток** (SLIST лямбд `+4016`, очередь `kAiQueueOnPlayerThread` `0x2922980`). Think: `kAiThinkTrackingTick` `0x2923300`. Список слотов: `kAiPlayerList` `0x84C8C08`.

SCAR — только вход: XOR-имена → `lua_CFunction` wrapper → inner. Имена в IDA часто без xref.

## Слои (не смешивать)

| Слой | Объект | Типичный вход |
|---|---|---|
| Слот | `Game_AIControlLocalPlayer` создаёт `AIPlayer` | SCAR; `sim_write` / OOS |
| Гейт think | `AI_Enable` → inner `0x2975660` пишет только `AI+0x12F4` | SCAR; пок байта без слота = пустышка |
| Сложность / bag | `AI_SetDifficulty` `0x294A390` **ставит лямбду**; пишет на **AI tick** | same-shot Get врёт |
| Personality | `AI_SetPersonality` + `kAiReloadDifficultyBags` `0x2925030` **только AI tick** | не звать с Present |
| Lock | `AI_LockSquad` `0x296D2E0`: нет track → 4CE0 (`+0x3E30`); track → 4A70 strip | до Enable; после Enable только SafeStrip |
| **A** train | `ScoringFunctions_*` → multiply `Evaluate` (`0x2D03940` …) | context `*(AI+0x3EA0)+0x94` |
| **B** fine-tune | desire / gatherer / SI / `PushScore` `0x29C8A60` | target, не train |
| **C** bag | personality asset | `AI_SetPersonality` |

Оверлей уже: C++ think (worker) → `WM_SCAR_AI_COMMIT` → lean natives. Relic всё ещё TRAIN/BUILD/RESEARCH.

## Без SCAR — три двери

1. **RPM / poke полей** — **чтение** сима/кучи — штатный путь оверлея (radar, tracking map). **Запись `.text`** = hasher / integrity (`OffsetsWriteBytes` отказывает). Heap-poke `tracking+0x40` (пустой tactic vec) — данные, не код; слот по-прежнему создаёт только Control/`AI_Enable`. Пок `+0x12F4` не создаёт слот и не грузит bag. Писать `+0x1308` / Reload с Present = AV `0x1EF1180`.
2. **Inner RVA на AI-потоке** (`kAiQueueOnPlayerThread` / `kAiDispatchOnPlayerId`) — тот же C++, что зовут wrappers. Нужен полный ABI каждого inner + TLS этого tid. Не продукт; версия ломает. Vs humans = OOS как и SCAR-write.
3. **Свой `lua_State` + `lua_pcall`** — не «без Lua»: тот же VM, только без compile `ScarDoString`. Relic не отдаёт state как C-модуль (`dump_vm_scar.h`: debug вырезан). Фаза 2 `lua_tocfunction` — каталог RVA, не director.

`lua_newstate` / второй OS-поток SCAR — пустая VM без нативов / TLS.

## Вердикт

Think без SCAR — **уже**. Полный director без SCAR — **не делаем** (ADR-001 B). Прямые inner — только если цель «убрать compile DoString», и тогда очередь на **AI tid**, не Present и не collect.

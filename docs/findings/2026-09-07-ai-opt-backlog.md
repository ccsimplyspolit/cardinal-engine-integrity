# 2026-09-07 — что оптимизировать (AI / SCAR / Present)

Не патч. Очередь по leverage. Мерить `FpsProfileGetPresentPercentiles` в инжекте, не средний FPS.

Уже снято: think на worker, commit/contest `PostMessage`, world-publish с Present, hybrid queue/scan skip при `AOE4HOOK_ECO_CPP`, ESP geometry cache.

## Высокий leverage

1. **Enable с Present = `SendMessage` × N.** `UiServiceScripts` → `AiSessionService` → `StkLuaLockSetArmy` + `eco_ai_on` + `InjectEcoScoring` (`kEcoScoring`) + `kEcoOpen`. Один хитч на включение. **Снято с кадра (2026-09-07):** `StkSelLockTick` / garrison / vill-scan / AfterCollect больше не `SendMessage` с Present — см. [fps-crash-sel-relock](2026-09-07-fps-crash-sel-relock.md).
2. **Слить очередь окна.** Commit + contest + farm уже разные `WM_SCAR_*`, бюджет «один DoString на слайс». Один latest-wins чанк на tid окна.
3. **World-feed DoString (~40–52 ms, ≤1/s).** Не публиковать `AOE4HOOK_AI_PLAN`, если SWM/hybrid не читает и runtime armed.

## Средний

4. Contest: 8 с retry того же hash. Occupancy с C++ снимка вместо слепого re-issue.
5. Sel-lock — **posted**, не Present `SendMessage`. Осталось реже постить tick, если snapshot idle.
6. `kEcoScoring` один раз на матч — ок; не тащить на Present (п.1).

## Исследование, не продукт

7. Inner на AI tid (`0x2922980`) для Layer B / availability — убрать compile lean apply. ABI + OOS те же.
8. Не: второй SCAR-поток, poke `+0x12F4`, pairwise на Present, CRT helper.

Live p95/p99 vs baseline после инжекта ещё не сняты в этой сессии.

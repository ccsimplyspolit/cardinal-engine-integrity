# 2026-09-07 — FPS ~15 затем GPU AV (sel-lock SendMessage + relock skip-eco)

Live log: `Documents\AOE4HSettings\Logs\aoe4_internal.log`, inject **01:54:55**.
Present tid **32512**, window/SCAR tid **41376**, hwnd `0x3319E8`, ents=590.

Это не RA kick и не BEX64 в логе. Оверлей сам сажал Present, потом `UiD3D12OnPresent` ловил `0xC0000005` и прятал UI на 15 с.

## Симптомы (тот же матч)

| Время | Что |
|---|---|
| 01:54:58 | `[SEH] UiD3D12OnPresent code=0xC0000005`, skip overlay 15s (`gpu_fault`) |
| 01:55:13 | restore RTVs |
| 01:58:09 | AI session / eco scoring; дальше `svc_ai_session` 42–49 ms |
| 01:58:12+ | ESP 8–10 ms на Present; `collect_world` last=17 avg=**103.70** ms |
| 01:58:36–01:59:08 | FPS **15–21**, present **42–50 ms**, `scar=ai_sel_pick` **39–47 ms** |
| 01:59:21, 02:00:05 | ещё два GPU AV + 15s skip |
| 02:00:47–53 | `ai_lock_army_relock` каждые ~0.4 с, два DoString на волну, `[STK] army relock skip-eco sid=50xxx` (жители) |

## Корни

1. **Present = `SendMessage`.** `UiServiceScripts` → `AiSessionService` → `StkSelLockTick` / `StkGarrisonLockTick` → `HelperRun` → `ScarExecuteOnWindowThread` = `SendMessageW(WM_SCAR_EXECUTE)`. Пока поток окна крутит DoString (~40 ms) и очередь relock, DXGI Present стоит. Отсюда 15 FPS, не «тяжёлый ESP».
2. **`ToolkitSlabsService` на Present** звал `StkLuaLockTickAfterCollect` (задуман после collect worker). `VillagerScanTick` тоже `SendMessage` с Present.
3. **Army relock catch-up 400 ms × до 16 `LockOneSid`.** `L.safe` — весь tracking без tactic, включая жителей. Lua `isArmy` отклоняет eco, C++ через 30 с снимал skip-eco и начинал заново. Каждая волна: scan ~1326 B + до 16 lock DoString на tid окна.
4. **GPU AV после restore.** Present уже опаздывал; плюс recover делал только `ImGui_ImplDX12_InvalidateDeviceObjects` и не собирал PSO заново (NewFrame умеет, но после skip/restore это гонка).

`TickEcoContest` уже был `PostMessage`. Метка `eco_contest` на Present — глобальный `scar_label`, пока Present ждал чужой `SendMessage`.

## Патч (InternalInjector)

- Sel / garrison / vill-scan: только `PostMessage` (`WM_SCAR_SEL_LOCK` / `GARRISON` / `VILL_SCAN`). Мышь на Present, нативы на окне.
- `StkLuaLockTickAfterCollect` с Present убран, вызывается из collect worker после `PublishCollectedWorld`.
- Relock: `kRelockTryCap=1`; skip-eco **на весь матч** (не 30 с); полный `__ArmyLock_Scan` только если skip-map сменился или это первый pass.
- `ScarExecuteOnWindowThread`: тот же tid окна → `ScarExecuteUserScript` напрямую (без вложенного `SendMessage`).
- D3D12 recover: `Invalidate` + `CreateDeviceObjects`.

Enable (`eco_ai_on` / scoring / open) по-прежнему `SendMessage` с Present — один хитч на включение, не каждый кадр. См. [ai-opt-backlog](2026-09-07-ai-opt-backlog.md) п.1.

Повторная проверка 02:16: IDA GUI не открыта (`idb_list` пустой, `idb_open` 60644 timeout). Этот FPS-патч **IDB не менял**. `HandleSelLock` больше не гоняет `sel_tick` при `kind==0`.

Дыры с повторного прохода (02:31):

- **WM_APP collision (must-fix):** `UiWndProc` один hwnd. `AiSessionHandleWindowMessage` ест сообщение раньше engine/lobby/relay. `0x5346`–`0x534C` были заняты дважды (`WM_SCAR_AI_COMMIT` = FOW native, `SEL_LOCK` = lobby reconnect, `GARRISON` = relay retry, …). Engine → `0x5350/5351`, lobby → `0x5360–5363`, relay → `0x5370`. SCAR блок `0x5343–0x534C` exclusive. **09-12: ремап реально в заголовках + пин `WindowMessageIdTests` в `test_overlay_present.py` (уникальность + диапазоны). До этого момента документ описывал желаемое, а код всё ещё держал 5 живых коллизий.**
- **SpawnWatch на collect worker:** `RadarPeekWorldCache` → `CapturePresentWorldSnap` (ImGui `GetFrameCount`) + `HelperRun`/`SendMessage` гонка с Present на `g_windowThreadScript`. Spawn watch снова на Present; worker только Post (relock / vill-scan / skip-map).

## Не трогали

ScarHelper CRT `0xB7F150`. Poke `AI+0x12F4`. HV `--arm`.

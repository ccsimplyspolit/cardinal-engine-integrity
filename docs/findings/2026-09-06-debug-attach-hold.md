# 2026-09-06 — hide-dbg cycle on live Relic (no plant, no attach)

Канон: [RELIC_DEBUG_ATTACH.md](../RELIC_DEBUG_ATTACH.md).  
RPM: `AOE4HOOK/tools/live_ra_window.py`. Hidden launch: `tools/rbhost/Start-Dbg.ps1`.

**Не сажали** Watcher / 7AB0 / Enqueue. **Не** `debug_attach_pid` / File→Attach.

## До

PID **52920** `B=0x7FF7E64B0000` (hold с ~23:20, `-dev -nodbg -notrap`).

| | begin | slots | accum | flag |
|---|---|---|---|---|
| 23:39 RPM | 0 | **0** | 0 | 0 |

`text_snap_ok=true`. Окно RA не выделено.

## Что сделали

`Start-Process -Verb RunAs -WindowStyle Hidden` → `rbhost\Start-Dbg.ps1`  
→ `RuntimeBroker.exe` PID **52428** (23:39:54), path  
`C:\Program Files (x86)\rbhost\release\x64\RuntimeBroker.exe`.  
MCP HTTP `127.0.0.1:3000` → `status: ok`. Cursor `user-x64dbg` namespace = disconnected (`Not connected`) — Reload Window, не attach.

52920 после старта dbg **пропал**. Новый Relic **26976** StartTime **23:40:45**, тот же `B=0x7FF7E64B0000`.  
Порядок **сломан**: dbg раньше игры. Ритуал требует игру → inject → dbg.

Причина смерти 52920 не доказана (рестарт пользователя / Steam / WW). Не писать «hide убил hold».

## После (26976, dbg уже 50 с+)

| Когда | begin | slots | accum | flag |
|---|---|---|---|---|
| ~23:40:50 (T+5 с от Relic) | 0 | **0** | 0 | 0 |
| ~23:41:15 (T+20 с + wait 20 с) | `0x2a77f817270` | **3** | **600** | 1 |

Три слота, все `tag=0x20220002` (dec 539099138), kinds 6 / 1 / 3.  
`+10` live `0x7FF7EBBAA5A0` = `B+0x56FA5A0` (Watcher descriptor, не 7AB0).

Relic **жив**. Pack WW ≠ IAT-kick. Attach не делали (ожидание slots=11).

## Вывод

Hidden `rbhost` + titleboot **не** держат `slots=0` на T+20 с, если dbg уже стоит до/вместе с Relic.  
Первые секунды `begin=0` — ленивое окно, не победа hide.

Слоты можно не поднимать на hold без dbg (52920). С dbg без attach — классическая тройка `20220002`. Выключить их патчем `.text` по-прежнему нельзя.

Не attach на 26976, пока цель — пустое окно. Soft-bind `relicconnect` — когда Cursor снова видит MCP.

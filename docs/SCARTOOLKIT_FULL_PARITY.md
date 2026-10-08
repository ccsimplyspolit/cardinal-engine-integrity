# ScarToolKIT vs AOE4HOOK — full parity (live)

Date: 2026-08-31. Audit, not a port. **This file is the live table.**
[`SCARTOOLKIT_PARITY_GAP.md`](SCARTOOLKIT_PARITY_GAP.md) / `.csv` stay a 2026-08-29 snapshot (Autovill/AICTLR/Dodge/tracers/launch_mode were stale there).

Sources: STK recovered v3.9 i18n + hotkeys ecx + magics + v4 LUA ONLINE (`lua_scripts` 16 files). HOOK live `ui.cpp` sidebar, `config.ini` / `hotkeys.ini`, `Documents\AOE4HSettings`.

Machine table: [`SCARTOOLKIT_FULL_PARITY.csv`](SCARTOOLKIT_FULL_PARITY.csv). Filterable canvas: `stk-hook-parity.canvas.tsx`.

## Counts

| Status | Rows |
|---|---:|
| hook_has | 30 |
| hook_partial | 34 |
| missing | 3 |
| wont_port | 16 |
| overlay_only | 16 |
| **Total** | **99** |

| Layer | has | partial | missing | wont_port | overlay_only | rows |
|---|---:|---:|---:|---:|---:|---:|
| Memory | 17 | 17 | 3 | 1 | 0 | 38 |
| SCAR | 11 | 3 | 0 | 1 | 1 | 16 |
| Lua | 1 | 7 | 0 | 0 | 0 | 8 |
| External | 1 | 2 | 0 | 12 | 0 | 15 |
| Etc | 0 | 5 | 0 | 2 | 0 | 7 |
| OverlayOnly | 0 | 0 | 0 | 0 | 15 | 15 |

Trainer SCAR files (99 corpus) are **grouped** (spawn/rates/grant/combat/world). One STK scar ≠ one overlay button.

## Tab map

| STK (v3.9 + v4) | HOOK sidebar |
|---|---|
| Tab Lobby | Lobby → Memory |
| Tab Online Reveal/Alerts/HUDs/ESP/Macros/AI Features | Online Camera / Radar / ESP / Maphack; Macro; AI BOT |
| Tab Offline trainer | Offline → Scar/Lua → Cheats |
| Tab Custom Scripts + v4 LUA ONLINE | Scripts → Scar / Lua (Files + editor + launch_mode) |
| Tab Settings license/hotkeys/theme | System → Settings / Hotkeys (no license) |
| External EXE + helper PE + ESP2D HWND | DllInjector in-process; no helper PE; D3D ESP |

## How launch_mode maps

| launch_mode | Combo | STK analogue |
|---|---|---|
| 0 | Direct VM | Overlay default ScarDoString (STK did not use this entry) |
| 1 | File loader | Custom Force Loader dofile/loadfile |
| 2 | CRT helper (STK) | LUA ONLINE / AF04B0 CreateRemoteThread onto 0xB7F150 |

## Missing (port-worthy)

- `M11` **Team HUD / Econ AI overlay** — STK: Online → Team HUD / Econ AI. HOOK: — (no TeamHUD). Econ knobs: AI BOT Fine-tune / Holds
- `M31` **Lobby Kick** — STK: Lobby → Kick ##Kick. HOOK: — (tooltip: unresolved, not invented)
- `M32` **Lobby Lock / Unlock room** — STK: Lobby → Lock/Unlock. HOOK: —

## wont_port (do not implement)

License/HWID/updater/`scar_config.php`/Themida/process-blocker/helper PE mapper/Dodge CRT `0xEB990`/army-vill wipe/FogCmp `.text` patch/Discord.

## Overlay-only (not a STK gap)

NativeEspData, World Feed, DualFlag, ScarTrust, Radar, Probe/Dump VM, Hybrid lanes, Relic blips, TWD (weapon-from-origin, multi-weapon `r`/`r2`/`r3`), region block, level/XP spoof, atmosphere, Lobby Force reconnect (`LoginAsync` `0x3109420`), skip Search CD (local `IsAutomatchBanned`), unofficial rejoin ticket (`Matches\rejoin_session.json`), relay failover (`JoinSessionAsync` `0x2EFC430`), Memory 3-frame click ignore, Offline Save/Load match (`Event_SaveWithName`).

## Stale GAP rows now live

| GAP id | Was | Now |
|---|---|---|
| F005 Autovill SendInput | missing | hook_has Macro → Autovill |
| F006–F008 AICTLR | missing | hook_has AI BOT (locks at top of page) |
| F049 Force Loader | missing | hook_has launch_mode=1 |
| F059 CRT helper | wont_port | hook_partial launch_mode=2 (in-process CreateThread) |
| UI-LOBBY-DODGE | wont_port (CRT) | hook_has in-process 0x76D030; CRT still wont_port (M28) |
| UI-LOBBY-ADDAI | missing | hook_has |
| UI-ONLINE-SHEEP/ENEMY-TRACER | missing | hook_has ESP gear |
| HK-ECX-09–13 prod macro | missing | hook_has Macro |
| WPM-AICTLR01 | missing | hook_has slabs |

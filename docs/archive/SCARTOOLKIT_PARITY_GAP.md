# ScarToolKIT → AOE4HOOK parity gap

> **Live table:** [`SCARTOOLKIT_FULL_PARITY.md`](..\SCARTOOLKIT_FULL_PARITY.md) / [`SCARTOOLKIT_FULL_PARITY.csv`](..\SCARTOOLKIT_FULL_PARITY.csv) (2026-08-31). This GAP file and `SCARTOOLKIT_PARITY_GAP.csv` are a **historical snapshot** (2026-08-29). Do not treat Autovill, AICTLR, Dodge, tracers, or Force Loader as still missing.

## Current (2026-08-29 reverse-port close)

The CSV and the “Top 20 missing” table below are a **historical audit snapshot**. Live owners:

| Historical “missing” | Live owner | Status now |
|---|---|---|
| FogCmp `0x8D956F` / FogByte / TileCopy PAGE_GUARD | `engine.cpp` | **hook_has** (VEH; not integrity `0x3E77BD2`) |
| In-process Dodge | `lobby_actions.cpp` RVA `0x76D030` | **hook_has** (CRT Dodge still `wont_port`) |
| AICTLR +8/+9/+10 | `toolkit_slabs.cpp` + Scripts AI | **hook_has** |
| Production Macro / Autovill 4–7 | `hotkeys.cpp` + Config Autovill | **hook_has** (not 23× `RegisterHotKey`) |
| Resource HUD | `resource_hud.scar` + `ScarInjectResourceHud` | **hook_has** (no GDI HWND) |
| Sheep/enemy tracers | `esp.cpp` `sheep_tracer` / `enemy_tracer` | **hook_has** (D3D12, not GDI ESP2D) |
| Match auto bundle | Config + `ServiceMatchAutoload` | **hook_has** (no auto Full Reveal) |
| ZoomLUA 200.f cap | `zoom.cpp` `ZoomConsumeHelperCap` | **hook_has** (cap, not live eye) |
| Overlay HWND 200 | in-process OverlayToggle | **hook_partial** vs Win32 id 200 |
| Kick/Lock Relic | unresolved callees | **missing** / do not invent |
| Cloud empire / script store | — | **wont_port** (crack.dll CPR) |

UI: 9 tabs; `ui.cpp` thin shell + `ui_scripts.cpp` / `ui_debug.cpp` / `ui_config.cpp` / `ui_log.cpp`. No tab `crack` / `ScarToolkit`. `stk_lib.scar` is shared core.

Current implementation note: `F049` / `SCAR-039` is now covered by the Scripts launch-mode selector. `launch_mode=0` keeps the existing direct managed `ScarDoString` path; `launch_mode=1` stages user payloads under `AOE4HSettings\Lua Scripts` and loads them through `dofile`, with `loadfile + pcall` fallback. The historical counts and ranking below remain an audit snapshot.

**2026-08-29 restart (older note):** this markdown and `SCARTOOLKIT_PARITY_GAP.csv` remain the original audit snapshot. Live statuses after re-scan live in `AOE4HOOK/.codex/reverse-port/mapping.jsonl`. CSV still lists `Menu\ScarToolkit` paths; leftover runtime scars there = 0.

Read-only audit (historical). Machine table: `SCARTOOLKIT_PARITY_GAP.csv`. Refused Dodge CRT / helper DllMain / license: `SCARTOOLKIT_REFUSED_PORTS.md`. In-process Dodge/Add AI **are** ported.

| | Source | Destination |
|---|---|---|
| Product | Recovered ScarToolKIT V3.9 (`recovered_v2`, FEATURE_PARITY F001–F083, 99 scars, native WPM magics, hotkeys ecx 1–23, reconstructed `src/`) | AOE4HOOK InternalInjector + `Documents\AOE4HSettings` plugins |
| Imagebase (toolkit) | `0x7FF777A70000` — **never mix** with Relic ASLR VAs | Overlay is in-process (`Game_ScarDoString` RVA `0xAA9B00`) |
| Plugin root | Toolkit embedded PE strings | `C:\Users\sshunko\Documents\AOE4HSettings\` only. Overlay AUTO is opt-in. Do not recreate `AOE4HOOK\plugins`. |

Status values: `hook_has` | `hook_partial` | `missing` | `wont_port`.

## Do not port (already `wont_port`)

- License / activate / Stripe / HWID unbind / WinLicense / `[license] key=`
- Themida, anti-debug, IAT hide, PE-header wipe, 48-entry FNV process blocker
- Dodge `0xEB990` CRT + `CreateRemoteThread` into Relic
- Helper PE from `asset.php` / mapper RVA `0xC55D0` / `%TEMP%\*.tmp` remote map
- Toolkit SCAR inject `AF04B0` VirtualAllocEx + CRT into game helper `0xB7F150`
- External `VirtualProtectEx` FogCmp/FogByte patches on Relic from a helper process (in-process VEH PAGE_GUARD in `engine.cpp` is the overlay path; still never integrity `0x3E77BD2`)
- Forced update / `scar_config.php` live GET / Discord `billy_977` / maintenance toasts
- 029+031 army/vill **wipe** (`Entity_Kill` stitch)

Overlay Full Reveal already documents that the toolkit helper’s inner fog algorithm is unknown and is **not** reimplemented. Overlay maphack is UC SCAR + radar + an in-module `FOWCTRL1` slab (`implTag 'AOE4'`). `our_fow_helper.dll` is not injected.

## Counts

| Status | Rows | Meaning |
|---|---:|---|
| **hook_has** | **157** | Feature exists in overlay UI and/or AOE4HSettings with comparable behavior |
| **hook_partial** | **49** | Same intent, different primitive (in-process vs helper WPM/CRT, D3D12 vs GDI ESP2D, INSERT vs 23 hotkeys) |
| **missing** | **36** | Port-worthy gap |
| **wont_port** | **27** | Excluded or non-goal |
| **Total** | **269** | |

By layer in the CSV:

| Prefix | Rows | What |
|---|---:|---|
| `F001`–`F083` | 83 | FEATURE_PARITY.draft.csv |
| `HK-*` | 26 | Dispatcher ecx 0–23 + overlay chrome 200 + `hotkeys.ini` |
| `WPM-*` | 13 | Helper magics + mapper + Dodge |
| `CPP-*` | 14 | `recovered_v2/src` subsystems |
| `UI-*` | 26 | Tabs / lobby / online extras from `ui_map.md` + `ui_answers.json` |
| `SCAR-001`–`099` | 99 | Current 99-corpus files |
| `NESP-*` / `SYS-*` / extras | 8 | Overlay-only NativeEsp + checksum prepend + FogCmp non-goal |

F-row status split: **has 55 / partial 11 / missing 7 / wont_port 10**. Most trainer SCARs are in `Menu\Scripts\<Feature>\` (debug shots under `Menu\Debug\Debug\`). `Menu\ScarToolkit` is not a runtime root. The remaining work is **C++ host** (macros, locks, hotkeys, ESP tracers, resource HUD) and a few **SCAR** holes (force loader, 1v1 HUD exactness, army/vill **counts**).

## Top 20 highest-value missing items

Ranked for implementers. Layer = SCAR | C++ | NativeEsp. Do not implement `wont_port` rows.

| # | ID | Layer | Why it matters |
|---|---|---|---|
| 1 | `F005` + `HK-ECX-09`…`13` + `UI-ONLINE-MACRO-KEYS` | **C++** | Production Macro master + groups 4–7. Toolkit `SendInput` / `AttachThreadInput` / QWERTY·AZERTY. No overlay equivalent. Highest online-tab gap. |
| 2 | `F006` `F007` `F008` + `WPM-AICTLR01` + `HK-ECX-18/19` | **C++** | AI lock army / villager / building queue via `AICTLR01+8/+9/+10`. Overlay only has `AI_UnlockAll` (designer locks). Need a **non-helper** design (SCAR `AI_LockSquads` or native list locks) — do not map a helper PE. |
| 3 | `F011` + `HK-*` (all ecx) | **C++** | 23-slot `RegisterHotKey` (ids 100+slot, `MOD_NOREPEAT`) + persist. Overlay is INSERT-only. Bind existing features first (Full Reveal, Idle TC, Idle vill, Enemy TC, scores, debug, run buffer, zoom, ESP). |
| 4 | `WPM-RESHUD02` + `HK-ECX-05/21` | **C++** | Resource overlay HWND (`ADEFD0`, 590×rows, `##ResOverlay`). Observer `hud.scar` is not this window. |
| 5 | `WPM-SHEEPSP1` + `UI-ONLINE-SHEEP-TRACER` + `UI-ONLINE-SHEEP-ICON` | **C++** / **NativeEsp** | Sheep/TC ESP: icon, scale, tracer. Overlay has sheep highlight + minimap rings (`002` / radar), not toolkit tracer+icon chrome. Prefer overlay draw over a Relic magic slab. |
| 6 | `WPM-PLRESP01` + `UI-ONLINE-ENEMY-TRACER` + `HK-ECX-22` | **C++** | Player ESP tracer flag. D3D12 ESP exists (`esp.cpp`) without enemy-tracer lines. |
| 7 | `UI-ONLINE-ESP-BLDGS` | **C++** | Per-building ESP checkboxes (Barracks…Wall, cap 5). Overlay has kind filters only (`espFilter[7]`). |
| 8 | `WPM-FOWCTRL1-ZOOM` + `UI-ONLINE-ZOOMLUA` | **C++** / **SCAR** | Helper zoom +16/+20 at **200.f must not** be applied (smashes overlay zoom). Port ZoomLUA SCAR camera **or** a clamped slider; visfog atmosphere is not ZoomLUA. |
| 9 | `F049` / `SCAR-039` | **SCAR** | **Landed:** selected launch mode supports file-backed `dofile`/`loadfile` delivery for Files, editor, and forced loader. Sandbox remains the Documents root. |
| 10 | `UI-ONLINE-AUTOENABLE` | **C++** | Match bundle: Full Reveal + Idle TC + Sheep ESP + Zoom, 1/s, auto-off on end (`AF2940`). `fullRevealAuto` is forced 0 on save. |
| 11 | `HK-OVERLAY-200` | **C++** | Overlay click-through / TOPMOST chrome hotkey (Win32 id 200). |
| 12 | `UI-LOBBY-ADDAI` / `LOCK` / `KICK` | **C++** | Lobby Add AI, Lock/Unlock, Kick. Scan+Force civ+aoe4world ELO already exist (`native_overrides.cpp`). **Not** Dodge. |
| 13 | `F009` / `F010` | **C++** / **SCAR** | Toolkit `[ai_profiles]` + civ upgrade/research lock groups. Overlay personality/econ templates are a different schema. |
| 14 | `F076` / `SCAR-091` `SCAR-092` | **SCAR** | Exact 1v1 HUD flags + `Rule_Remove(Update1v1HUD)`. `hud.scar` UniversalHUD is a cousin, not the 091/092 scripts. |
| 15 | `F079` (counts only) | **SCAR** | Army/vill **counts** UI. Wipe stays `wont_port`. |
| 16 | `F080` / `WPM-2DESP001` | **C++** | GDI `ScarToolkit_ESP2D` HWND + helper flag. Overlay D3D12 ESP is the product path; remaining gap is tracers/building checkboxes/hotkey, not a second GDI window. |
| 17 | `F001` (inner fog) | **NativeEsp** / **C++** | `FOWCTRL1+8` is mirrored in-module; helper tile-fill is **unknown**. Do not invent FogByte. Optional: expose slab to an external WPM host with `implTag 'AOE4'` only. |
| 18 | `UI-SETTINGS-LANG` / `THEME` / `UI-FONTS` | **C++** | Six-locale i18n + editor theme + Noto 18px. Low combat value, high toolkit-chrome parity. |
| 19 | `F048` named save/load slots | **C++** | Files pane + AUTO exist; toolkit editor save/load slots do not. |
| 20 | `PLUGIN-GRANT-ALLIES` | **C++** | `grant_allies.scar` is on disk and in `kMenuScars` but ScarToolkit UI calls `GrantRes.Run(..., 'allies')`. Wire or delete the duplicate. |

NativeEsp already covers world feed (`spatial_world_model.scar`, `aoe4hook_bridge.scar`, `unit_intelligence.scar`). Highest NativeEsp-adjacent gaps are **sheep/player tracers** and **optional FOWCTRL1 export**, not a new SWM.

## How overlay already differs (do not regress)

| Toolkit | AOE4HOOK |
|---|---|
| External `OpenProcess(0x43A)` + CRT into Relic helper | DLL already in Relic; `Game_ScarDoString` |
| Helper PE plants magics in Relic RW | `FOWCTRL1` slab inside InternalInjector; other magics **absent** |
| D3D11 ImGui host + GDI ESP2D | D3D12 ImGui Present hook + `esp.cpp` / `radar.cpp` |
| Five tabs Lobby/Online/Offline/Custom/Settings | Native / ESP / Radar / Scripts / ScarToolkit / Camera / World |
| `hotkeys.ini` next to EXE | `Documents\AOE4HSettings\Config\config.ini` |
| AUTO implicit / inject on click | AUTO **opt-in** per Scripts row |

## F001–F083 summary

| Status | IDs |
|---|---|
| hook_has | F002 F003 F012–F045 F047 F050 F056 F062–F075 F077 F078 (55) |
| hook_partial | F001 F004 F009 F011 F046 F048 F060 F076 F080 F081 F083 (11) |
| missing | F005 F006 F007 F008 F010 F049 F079 (7) |
| wont_port | F051–F055 F057–F059 F061 F082 (10) |

Trainer SCARs in `AOE4HSettings\Scar Scripts\Menu\Scripts\` (plus AutoQueue / IdleBuildings / Maphack under the same tree; `debug_shots.scar` under `Menu\Debug\Debug\`): GrantRes, Rates, Spawn, CombatMods, Invuln, AutoHeal, InstantWin, Convert, AiShutdown, SheepHerder, CheatFoW, JeanneXp, AgeUp, HideUi, SheepWolves, InstantBuild, KillAnimals, PlayerHints, SelectedHints, ScoresNative, Debug, Lib (`stk_lib.scar`).

## Native WPM magics

| Magic | Toolkit | Overlay |
|---|---|---|
| `FOWCTRL1` | Scan Relic RW; WPM +8/+11/+16/+20; handshake secret in EXE | In-module slab; +8/+11 consumed by overlay APIs; +16/+20 **cap only** (`ZoomConsumeHelperCap`); handshake acks any nonzero +32 |
| `TCIDLE01` | WPM +8 | SCAR AutoQueue (F002 `hook_has`); no helper WPM |
| `SHEEPSP1` | WPM +8 + overlay opts | D3D12 sheep tracer + radar rings (`hook_has` chrome; no helper WPM) |
| `PLRESP01` | WPM +8 | D3D12 enemy tracer (`hook_has`; no helper WPM) |
| `2DESP001` | WPM +8 + GDI HWND | D3D12 ESP (`hook_has`; GDI HWND `wont_port`) |
| `RESHUD02` | Second swapchain HWND | Named `resource_hud.scar` (`hook_has`; HWND `wont_port`) |
| `AICTLR01` | WPM +8/+9/+10 | In-module slab `toolkit_slabs.cpp` (`hook_has`) |

## Hotkeys

Dispatcher `AEABD0` RVA `0x7ABD0`, incoming ecx = `slotN_action` 1–23 (`ui_answers.json` Q3). Overlay: `hotkeys.cpp` GetAsyncKeyState slots + Autovill SendInput; INSERT OverlayToggle in `hooks.cpp`. **No** toolkit `RegisterHotKey` ids 100+ (by design, not missing magics).

## Integrity

- Skirmish trainer rows: `stk_lib.scar` `ST.Sim` drops `AOE4HOOK_MP_SAFE` so wrappers pass; still **OOS vs humans**. UI already labels this.
- Full Reveal UC SCAR FOW natives: DualFlag risk vs humans; overlay ranked path is radar-only.
- Do not add Relic `.text` patches, helper PE maps, or CRT to close gaps.

## Sources

- `C:\Users\sshunko\Downloads\ScarToolKIT\recovered_v2\reports\FEATURE_PARITY.md`
- `...\tests\FEATURE_PARITY.draft.csv`
- `...\reports\ARCHITECTURE.md` `SCAR_LUA_CORPUS.md` `UNRESOLVED.md`
- `...\coverage_ledger.csv`
- `...\agents\ui-imgui\ui_map.md` `hotkeys.md`
- `...\agents\ida-core\ui_answers.json`
- `...\agents\helper-pe\helper_protocol.md`
- `...\agents\scar-injection\pipeline.md`
- `C:\Users\sshunko\Downloads\ScarToolKIT\recovered\NATIVE_FEATURES.md`
- `K:\aoe4_dlc\hh\AOE4HOOK\internal\AOE4HOOK_MAPHACK_IMPL.md`
- `K:\aoe4_dlc\hh\AOE4HOOK\internal\InternalInjector\` (`ui.cpp` + `ui_scripts.cpp` / `ui_debug.cpp` / `ui_config.cpp` / `ui_log.cpp`, `scar.cpp`, `esp.cpp`, `radar.cpp`, `maphack_fowctrl.cpp`, `engine.cpp`, `toolkit_slabs.cpp`, `hotkeys.cpp`, `native_overrides.cpp`, `zoom.cpp`)
- `C:\Users\sshunko\Documents\AOE4HSettings\` (`Scar Scripts\Menu\`, `NativeEspData\`, `Config\`)

CSV columns: `toolkit_id, toolkit_rva_or_script, aoe4hook_path, status, owner_agent, notes, integrity_risk`.

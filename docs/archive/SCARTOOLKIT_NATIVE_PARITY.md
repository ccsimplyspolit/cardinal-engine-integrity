# ScarToolKIT native magics vs AOE4HOOK

Date: 2026-08-28. Toolkit imagebase `0x7FF777A70000` (do not mix with Relic ASLR).
Host WPM magics are **helper-block flags**, not FogCmp. Overlay does **not** inject
the toolkit PE or `our_fow_helper.dll`. FOWCTRL1 lives in InternalInjector.

Safe ports are overlay draw + NativeEspData queries (no Relic `.text`, no CRT).

Cpp-agent work remaining: `Documents\AOE4HSettings\Logs\native_port_needed_cpp.txt`.

## Magic scoreboard

| Magic | QWORD (LE ASCII) | Toolkit | HOOK | Status |
|---|---|---|---|---|
| `FOWCTRL1` | `0x314C525443574F46` | WPM `+8` Full Reveal, `+11` map one-shot, `+16`/`+20` zoom | Slab in `maphack_fowctrl.cpp`. `+8` → `EngineCrackFullReveal`. `+11` → `ScarRevealMapOneShot`. `+16`/`+20` → `ZoomConsumeHelperCap` (Autodeclinate max) | **Present** (`+8`/`+11`/`+16`/`+20`) |
| `TCIDLE01` | `0x3130454C44494354` | WPM `+8` idle-TC **alert** (helper draw) | `RadarDrawIdleAlert` (`radarIdleAlert`). Query: `AOE4HOOK.IdleTownCenters` / `SpatialWorldModel.QueryIdleTownCenters`. Queue: AutoQueue SCAR (sim, not this magic) | **Present** (overlay + native query). No helper slab |
| `SHEEPSP1` | `0x3150535045454853` | WPM `+8` sheep/TC ESP | `esp`/`radar` `highlightSheep`. Query: `AOE4HOOK.Herdables` / `QueryHerdables` | **Present**. No helper slab |
| `PLRESP01` | `0x3130505345524C50` | WPM `+8` player ESP | `esp.cpp` enemy boxes (`espShowEnemy`). Query: `AOE4HOOK.PlayerEsp` / `QueryPlayerEsp` | **Present**. No helper slab |
| `2DESP001` | `0x3130305053454432` | WPM `+8` + HWND class `ScarToolkit_ESP2D` (`WS_EX_LAYERED\|TRANSPARENT\|TOPMOST\|TOOLWINDOW\|NOACTIVATE`, ~33 ms) | In-process `EspDraw` (D3D Present). No second overlay window | **Present** (better path). Do **not** create `ScarToolkit_ESP2D` |
| `RESHUD02` | `0x3230445548534552` | Helper + ImGui `##ResOverlay` | `RadarDrawObserverHud` + `AOE4HOOK_STOCKS`. Query: `AOE4HOOK.ResHud` / `GetResourceHud` | **Present**. No helper slab |
| `AICTLR01` | `0x3130524C54434941` | WPM `+8` vill / `+9` army / `+10` building lock | Read-only: `AOE4HOOK.AiLockIntent` / `GetAiLockIntent`. Manual selection tracking in SpatialWorldModel **does not** call `AI_LockSquad` (Present AV) | **Partial**. No Relic lock native. Optional C++ `AOE4HOOK_AI_LOCK` feed |

## Other native (non-magic) toolkit features

| Feature | Toolkit | HOOK | Port? |
|---|---|---|---|
| Zoom helper `+16`/`+20` (default 200.f) | FOWCTRL1 float as max-cap for helper | `zoom.cpp` writes Autodeclinate `info+0x10` min / `+0x14` max (UI 36–68 default, slider 10–400) | **Present**. Consume slab → `ZoomSetUiValues(36, cap)` + `ZoomApply`. Do not apply raw 200.f as live camera distance. |
| Auto-vill `SendInput` (`AEA540`) | `AttachThreadInput` + `SetForegroundWindow` + scan-code `SendInput`, QWERTY/AZERTY | AutoQueue / IdleVillagers SCAR. Idle TC queue is **sim** (`Entity_QueueProductionItemByPBG`), `AOE4HOOK_MP_SAFE` refuses | **Not SendInput**. SCAR equivalent present. Do not port synthetic input |
| ESP class `ScarToolkit_ESP2D` | External layered HWND + GDI `UpdateLayeredWindow` + RPM walker `B5E670` | Internal D3D ESP + same world cache as radar | **Present** (in-process). No HWND clone |
| Dodge CRT | `VirtualAllocEx` RWX stub + `CreateRemoteThread` | — | **Will not port** |
| Helper mapper `B355D0` / `asset.php` | Nested PE into Relic | FOWCTRL1 slab already in this DLL | **Will not port** |
| `VirtualProtectEx` Relic `.text` | Toolkit never imported it | Overlay never uses it | **Will not port** |
| License / HWID | WinLicense + WinHTTP | — | **Will not port** |

## NativeEspData APIs (this pass)

| Call | Magic | File |
|---|---|---|
| `AOE4HOOK.IdleTownCenters` | TCIDLE01 | `aoe4hook_bridge.scar` (apiRev 4) |
| `AOE4HOOK.Herdables` | SHEEPSP1 | same |
| `AOE4HOOK.PlayerEsp` | PLRESP01 | same |
| `AOE4HOOK.ResHud` | RESHUD02 | same |
| `AOE4HOOK.AiLockIntent` | AICTLR01 read | same; honors `AOE4HOOK_AI_LOCK` if C++ publishes it |
| `AOE4HOOK.ToolkitParity` | all | same |
| `SpatialWorldModel.QueryIdleTownCenters` | TCIDLE01 | `spatial_world_model.scar` 18.21 |
| `SpatialWorldModel.QueryHerdables` | SHEEPSP1 | same |
| `SpatialWorldModel.QueryPlayerEsp` | PLRESP01 | same |
| `SpatialWorldModel.GetResourceHud` | RESHUD02 | same |
| `SpatialWorldModel.GetAiLockIntent` | AICTLR01 | same |
| `SpatialWorldModel.GetToolkitParity` | all | same |

EntKind in the C++ feed: Resource=0 Relic=1 Building=2 Unit=3 Tree=4 Animal=5.

## HOOK file map (cpp, do not inject toolkit)

| Path | Role |
|---|---|
| `internal/InternalInjector/maphack_fowctrl.cpp` | FOWCTRL1 plant + handshake + `+8`/`+11` consume |
| `internal/InternalInjector/engine.cpp` | `EngineCrackFullReveal`, `EngineFogService` calls `MapHackFowCtrlService` |
| `internal/InternalInjector/zoom.cpp` | Autodeclinate zoom min/max |
| `internal/InternalInjector/esp.cpp` | 2D ESP / sheep / player boxes |
| `internal/InternalInjector/radar.cpp` | Idle alert, observer HUD, world feed |
| `internal/InternalInjector/fowctrl.h` | Layout only; DLL is **not** injected |

## Integrity

Toolkit host: OpenProcess `0x43A`, RW scan, WPM one byte on helper magics. Helper consume inside Relic is **unknown**. Overlay: data in our module + SCAR UI reveal (ranked = radar hold). NativeEspData never WPMs Relic and never calls `AI_LockSquad`.

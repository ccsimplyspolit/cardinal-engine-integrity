# ScarToolKIT C++ host port (InternalInjector)

Toolkit imagebase `0x7FF777A70000` (ScarToolKITU.exe). RVAs below are toolkit-only. RelicCardinal game RVAs are never added to that base.

HOOK is an **internal** D3D overlay in Relic. Toolkit is an **external** ImGui host. This port copies confirmed host behavior HOOK lacked, without cloning license, Themida, Dodge CRT, helper-PE map, Relic `.text` patches, or checksum spoof.

## Build artifacts (Release|x64)

User must re-inject; Relic was not injected from this session.

| File | Size | LastWriteTime |
|---|---|---|
| `AOE4HOOK\internal\x64\Release\InternalInjector.dll` | 11394048 | 2026-08-30 21:13:46 |
| `AOE4HOOK\internal\x64\Release\DllInjector.exe` | 188416 | 2026-08-28 09:57:56 |

### ScarToolkit buttons (post-SCAR-agent UI freeze)

Wired in `ui.cpp` from `Logs\scar_port_needed_ui.txt`. Existing `kMenuScars` filenames only.

| Button | Pane | File | Lua |
|---|---|---|---|
| **Set campaign time** + seconds slider | Offline / Debug | `debug_shots.scar` | `StkDebug.CampaignTime(n)` (015). CampaignCheat unchanged. |
| **Max HP set** + Set max HP slider | Offline / Selected combat | `combat_mods.scar` | `CombatMods.Health(n, 2)` (007 MODE=2). xN=0, add=1 kept. |
| **Army/vill counts** start/stop + army/vills checkboxes + **Apply count flags** | Online / Overlay alerts | `enemy_near_tc.scar` | `EnemyNearTC.StartCounts` / `StopCounts` / `SetCountFlags`. Counts only; no Entity_Kill. |
| **Grant food to allies** | Offline / Grant | `grant_allies.scar` | `GrantAllies.Run('RT_Food', amt)` — same shortcut, dedicated slot. General **Grant** still `GrantRes.Run`. No second Grant button. |
| Idle villager hotkey | Settings / hotkeys | `idle_buildings.scar` | Already `IdleVillagers.Start` (Scripts→Features has Start/Stop). |
| ZoomLUA / FOWCTRL1+16/+20 | Camera tab | *(no SCAR)* | Helper `zoomOn`/`zoomVal` → `ZoomSetUiValues(36, cap)` + `ZoomApply` Autodeclinate min/max. 200.f is a max cap, not live distance. No recovered ZoomLUA body. |
| **dofile {PATH}** (039) | Custom + Files | overlay loader | Path field + Load. Sandboxed to `Documents\AOE4HSettings`; delivery uses the selected direct or file-loader mode. No AUTO, no HTTP. |

## Landed

### UI / hotkeys (`AF8290` / `AEABD0` RVA `0x7ABD0`)

- No overlay sidebar tab named ScarToolkit. Trainer UI is Scripts → Alerts / Skirmish / Custom; lobby natives stay **LOBBY**; hotkeys/theme stay **Config**.
- Lobby pane is a stub: points at Native (civ/roster). **Not** `Overlay_DrawLobbyPanel` RVA `0xEE670` (Dodge / `##LobbyPremium` refused).
- Online = Full Reveal + overlay alerts (existing). Offline = skirmish trainer. Custom = editor with Load/Save/Run + `ScarLastDetail`. Settings = `hotkeys.ini`.
- `Documents\AOE4HSettings\Config\hotkeys.ini`: `[hotkeys]` `slotN_action/vk/mod`, `[editor] theme=`, `[ui] language=0..5`, `[autovill]`, `[ai_lock] lock_villager=`. **No `[license]` verification.**
- Dispatcher ecx wired when HOOK had no equivalent or only a menu button:
  - **8** Debug HUD (`debug_shots.scar` ShowDebugHud)
  - **9–13** production macro master/groups 4–7 (`SendInput`, QWERTY/AZERTY)
  - **19** villager lock flag (`AICTLR01+10`; no helper PE)
  - **21** overlay toggle (was hard-coded INSERT; now slot0 VK)
- Also mapped: Full Reveal, Reveal Map, Idle TC, idle villager, enemy-near-TC, scores, resource HUD, sheep ESP, 2D ESP, run editor.

### Attach / watchdog (`B897E0` / `B8CB70`)

- Overlay already lives in RelicCardinal; no `OpenProcess 0x43A`.
- DllInjector still uses `PROCESS_VM_OPERATION|READ|QUERY` (no `CREATE_THREAD` / `VM_WRITE`). After a successful APC it **exits** (overlay stays in Relic). `--watch` / `-w` then `OpenProcess(SYNCHRONIZE)` and waits until the game exits (`Game closed.`).
- `Release` vs `Release_fowctrl` = same features, different OutDir. If Release is locked, inject the fowctrl sibling DLL. Do not mix two InternalInjector images.
- Header pills: **MATCH/LOBBY** from world ents + VM, plus **VM0/1/3** (toolkit `QueryScarState` numbers). Header `RA S# A# F#` is Relic AC window (`MpBypassGetWindowSnapshot`), not SCAR. Red **Offline** is Scar Trust. Lobby **Memory** ignores clicks 3 frames so Force reconnect (`LoginAsync` `0x3109420`) does not fire from the sidebar.

### SCAR pipeline (`AF0290` / `AF04B0`)

- HOOK keeps `Game_ScarDoString` RVA `0xAA9B00` (not toolkit remote CRT helper).
- Ready-state **3** = VM live **and** world cache &gt; 0. User scripts with `Rule_*` (Files / hybrid) still wait **2s** after live (`kScarStartConditionsMs`). Lean AI BOT `AI_Enable` / STK locks skip that floor (`ScarLeanScriptsAllowed`). Quiet probe still has no `Rule_` wrap.
- Empty world: skip all DoString (user + quiet). After 400 ms empty, **`ScarNotifyMatchEnded`** clears `g_vmCallable` so the bridge cannot AV `0xC0000005` at dest `0x18`.

### Script editor

- Custom pane: Load/Save `Scar Scripts\custom_buffer.scar` (or named file), Run, last compile/SEH detail, plus sandboxed **dofile {PATH}**.
- The Scripts → Files selector also controls the editor and forced loader: **Direct VM (dev flag)** is the default and keeps the existing managed `ScarDoString` path; **File loader (dofile / loadfile)** writes the payload to `Documents\AOE4HSettings\Lua Scripts\quick_*.lua`, then sends a short in-process wrapper that tries `dofile` and falls back to `loadfile` + `pcall`.
- The setting is persisted as `[scripts] launch_mode=0` or `launch_mode=1` in `Config\config.ini`. It changes delivery of user SCAR/Lua payloads only; generated internal feature scripts keep their existing direct path.

### ESP lifecycle (`AE4A10` RVA `0x74A10`)

- Still D3D Present ImGui, **no** `ScarToolkit_ESP2D` layered HWND.
- Empty world already skips draw. `2DESP001+8` toggles the existing box ESP.

### FoW

- Unchanged: EngineCrack + in-module **FOWCTRL1**. No unknown inner fog, no helper PE.
- `+16`/`+20` zoom consume: `ZoomConsumeHelperCap` → Autodeclinate min/max. 200.f is a max-cap, not live camera distance.

### dofile `{PATH}` (F049 / SCAR-039)

- Overlay loader only: `ScarReadOverlayScarFile` + Files `ExecuteManagedScript`. In direct mode this remains the existing managed in-memory path; in file-loader mode the read payload is persisted as a temporary `.lua` and loaded by the VM with `dofile` / `loadfile`.
- Allowed root: `Documents\AOE4HSettings` (and subfolders). Relative paths join that root.
- Rejected: `..`, other drives, Relic EXE dir, InternalInjector dir, UNC / `\\?\` / `\\.\`, HTTP(S)/FTP/`file:`, non-`.scar`, ADS.
- No AUTO. Same classic_start gate as other user scripts (VM state 3 + 2s, no lobby DoString).
- UI: Scripts → Files and Scripts → Custom, path field + Load.

## Sibling magics (documented in `AOE4HOOK_MAPHACK_IMPL.md`)

`TCIDLE01` `SHEEPSP1` `PLRESP01` `2DESP001` `RESHUD02` `AICTLR01` in `.stkslab` RWS. Consume +8 (AICTLR +10) onto overlay toggles.

## Refused (will not port)

| Toolkit | RVA | Why |
|---|---|---|
| License / WinHTTP activate | — | Policy |
| Themida / anti-debug / IAT hide | `AF8290` prologue | Toolkit-only |
| Dodge CreateRemoteThread RWX stub | `0xEB990` | Refused |
| Mapper / `asset.php` helper PE | `0xC55D0` | Not recovered; extra integrity surface |
| `VirtualProtectEx` Relic | — | No Relic `.text` |
| FogCmp / FogByte / PAGE_GUARD | — | RA-lethal on this build |
| Checksum spoof | — | Refused |
| Overlay_DrawLobbyPanel Dodge / premium | `0xEE670` | Lobby widgets only |
| `ScarToolkit_ESP2D` HWND | `0x74A10` | Fights D3D hook |
| `OpenProcess` mask `0x43A` | `0x1197E0` | HOOK inject mask is already narrower |

## Remaining gaps (SCAR agent)

- Villager **lock** is a flag (`AICTLR01+10`). No SCAR that actually freezes villager AI (helper PE did that).
- Production macros are `SendInput` key taps, not toolkit helper engine bytes.
- Language combo stores `0..5` but does not swap overlay strings (no six i18n tables).
- Lobby Scan/Lock/Add AI / Dodge: not ported; Native tab has civ/roster only.
- Editor does not parse `warnings.log` markers the way Files Execute does (uses `ScarLastDetail` / SEH).

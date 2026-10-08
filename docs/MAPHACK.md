# AOE4HOOK maphack (product path)

ScarToolKIT-style **Full Reveal** / **Reveal Map (Memory)** in this overlay. No ScarToolKIT PE, no FogCmp / FogByte / PAGE_GUARD / ov+4.

## Build

Product configuration is **Release** (not `RelWithDebInfo` — this vcxproj has no such config; dumps / license / HWID do not change the MSVC name). FOWCTRL1 `+8` VEH Full Reveal, `+11` MemoryShot, and the licensed helper section-map are compiled into **every** config; they are not gated on `Release_fowctrl`.

```
msbuild AOE4HOOK\internal\InternalInjector\InternalInjector.vcxproj /p:Configuration=Release /p:Platform=x64
```

Deploy / inject:

- `AOE4HOOK\internal\x64\Release\InternalInjector.dll`
- optional sidecar `helper_pe_FOWCTRL1.dll` next to that DLL (PostBuild copies it from `internal\licensed_helper\` **if that file exists**; clones do not need it)

`DllInjector.exe` lives in the same `x64\Release\` folder and APC `LoadLibraryW` of `InternalInjector.dll` next to itself. Do not pass `Release_fowctrl\InternalInjector.dll` unless that is the only unlocked copy.

`Release_fowctrl` is an **OutDir alias** (identical ClCompile/Link, different folder — **same features**). It existed because a loaded `x64\Release\InternalInjector.dll` was file-locked. Prefer building **Release** while the game still holds `Release_fowctrl` (so Release is writable). If Release is locked: unload/reinject, or `msbuild ... /p:Configuration=Release_fowctrl` and inject that folder after restart — do not mix two InternalInjector images in one process.

Inject the usual way: `DllInjector` APC `LoadLibraryW` of `InternalInjector.dll` only. Default: **exit after successful APC** (overlay stays in Relic). `--watch` / `-w` waits for RelicCardinal to exit, then the injector exits.

`licensed_helper_map.cpp` section-maps the licensed FOW_DLL (TEMP hex16.tmp Hidden+Temporary) **without DllMain**. Present tick consumes helper `FOWCTRL1+11` via `ScarRevealMapMemoryShot`. Full Reveal `+8` is hold + `MapHackFowCtrlPortArm` (poison+VEH) + overlay radar — **not** UC combo, **not** FogCmp PAGE_GUARD.

Do **not** inject `recovered\helper_pe\our_fow_helper\our_fow_helper.dll`. Do **not** call the licensed PE’s DllMain (KiUser 8-byte hook). RE: `Downloads\ScarToolKIT\licensed_fetch\FOWCTRL1_HELPER_ANALYSIS.md`.

## Overlay: how to turn it on

Overlay toggle is hotkeys.ini `[hotkeys] slot0` (default INSERT). Full Reveal does not need SCAR. Memory consume does (in-match).

| UI | Control | API |
|---|---|---|
| **Scripts → Maphack** | **Full Reveal** toggle | `EngineCrackFullReveal` / `Disarm` → FOWCTRL1+8 + VEH + radar |
| **Scripts → Maphack** | **Reveal Map (Memory)** | `MapHackFowCtrlPulseMemReveal` → +11 + `ScarRevealMapMemoryShot` |
| **Debug** | TileCopy/FogCmp PAGE_GUARD | `EngineArmMapHackPageGuard` — crack path, **not** product Reveal |
| **Debug** | latch3 fallback | `EngineArmLatch3Fallback` — `B0 01 C3` at latch entry; works without Abc0Mgr. RA auto-restore `slots != 0` |
| **Debug** | ov+4 fallback | `EngineArmOv4Fallback` — write `*(*kAbc0Mgr)+4=1`, no `A0B550`. Same walk as VEH; skip if walk wait |

Do not also use **FoW toggle (skirmish/OOS)** (047 `CheatFoW` / `FOW_PlayerRevealAll`) for this — that is a different skirmish wrap and desyncs vs humans.

FACT: ScarToolKIT host does **not** patch FogCmp/TileCopy. Full Reveal = WPM `FOWCTRL1+8`. Memory = WPM `FOWCTRL1+11`.

What actually happens on Full Reveal:

1. Overlay radar hold (`RadarSetMaphackOverlay`).
2. FOWCTRL1 `+8` hold on the in-module slab (and helper slab if the toolkit host WPMs it).
3. Ported licensed algorithm: poison `*(*Abc0Mgr)+0x2DA0` with `0xDEADC0EF`. AV at `mov rax,[rcx+2D0h]` (AOB+22 / RVA `0x48532E`); VEH restores the register and `RIP += 108` lands on `0x48539A` `mov al,1` (latch success). This **skips** F90 / ov+4 / ov+13. Same boolean as latch3 `B0 01 C3`, without a `.text` write. **No** ntdll KiUser steal, **no** FogCmp / FogByte / PAGE_GUARD / UC combo.
4. Ranked: radar + VEH skip (no SCAR).

Reveal Map (Memory) pulses `+11` then `ScarRevealMapMemoryShot` (UC combo vs AI only). It does **not** set +8 and does **not** arm radar.

Relic `.text` is not patched on the product path. Integrity memcpy RVA `0x3E77BD2` is never PAGE_GUARD. Native D02C stays off (Lua Memory-shot already passes F448). **Debug fallback (not Full Reveal):** latch3 `B0 01 C3` (works without Abc0Mgr; auto-restore when RA `slots != 0`) and ov+4 write (no `A0B550`; same walk as VEH poison, so it cannot rescue `fog ptr walk wait`).

LOBBY Dodge: Relic `0x76D030` on the game UI thread (`PostMessage`). No `VirtualAlloc` RWX, no `CreateThread` — live 21:03:38 packed `slots=1 accum=30` ~115 ms after the toolkit 0x29 stub.

## Visibility layer over Full Reveal (01.10)

Camera tab -> **Night layer**. Full Reveal lights the whole map; this layer shades the ground by the player's own fog on top of it: clear where the player sees now, a haze where it has explored, dark where it has never been, plus one outline along the edge of sight.

Source: the game's fog grid, read-only (`fog_grid.h`). FogGrid = blob + (u32 world+0x2D0 - 0x56B585D7); per vision group a VISIBLE layer (+0xA0 table) and an EXPLORED layer (+0x160 table), 12-byte entries, one bit per cell in 16x16 tiles; group of the viewed player = i32 (blob + u32 world+0x378 - base)+0x104[world+0xC]. Header 64 B, 64-aligned, canary `DE C0 AD DE FE CA DD BA AD BA E1 FE CE FA AD DE` after the header and after the data. Cell (cx, cy) = (x / cs - originX, z / cs - originY). The +8 latch never touches this grid (its writers are the fog pass 0x21319E0, the EndFog job 0x204CAE0 and the explore fill 0x204C870), so it keeps the real vision under Full Reveal. Checked on dump 53820 (`tests/adversarial/fixtures/fog_dump53820.bin`, `test_fog_grid`): 128x128 cells of 4 m, 636 visible / 830 explored.

When the grid fails validation (a patch moved it, fog off) the player's units' catalogue sight discs are rasterised instead and the status line says so. Rendering is a ground mesh at cell resolution with per-vertex colour (edges blend in every direction), heights from the TWD terrain snap with its own fault latch; the HUD panels and the minimap are clipped out. Default: shown only while the +8 port is armed. Settings live in `[night]`. Cost: `esp_night`.

Reveal Map (Memory) and AI Map knowledge flood the explored / visible layer; the layer keeps the last real explored layer plus what has been seen since, and says so.

**Minimap.** The same field shades the overlay radar (`[night] radar`, `radar_dim`): `fog::ShadeRuns` merges each cell row into runs of equal shade (a 128x128 grid is a few hundred quads), projected with the dots' `ProjectWorldToRadar` and drawn every frame outside the radar's replay cache, with AA fill off so touching runs leave no seam. With Radar -> Auto-place over AoE4 minimap the radar lies on the game's minimap and the fog is clipped to its circle (a run on the edge goes cell by cell). The radar darkness is a share of the screen's (0.6): the game draws its own minimap icons under the overlay. Radar 2 gets the same shading inside its window.

## Full Reveal at match start, solo only (01.10)

Scripts -> Maphack -> **Arm at match start (solo)** (`full_reveal_solo_auto` in `[scripts]`). Arms the +8 hold 2 s into a match the game's type byte and the lobby roster both call single player or skirmish (`AiNetDecide == Solo`), and releases it at match end (`EngineFullRevealMatchEnded`, owner = auto). Network or unknown matches are never armed automatically; the manual toggle and the hotkey work there as before. No Reveal Map (Memory) pulse, so the explored layer stays real. Turning it off by hand keeps it off for that match. At injection it needs Config -> Autoload on inject.

`ScarNotifyMatchEnded` now disarms the +8 port before its early return: a non-retained ScarDoString SEH used to clear the VM flags first and leave 0xDEADC0EF in a dying fog manager.

## Weather / atmosphere (01.10)

Camera tab -> **Weather**. `Game_SaveInitAtmosphereSettings` / `Game_LoadAtmosphereSettings(file, name)` / `Game_TransitionToState(name, sec)`, the calls the Full Moon and Chaotic Climate modes make on skirmish maps. The files are `scenarios/atmosphere/*.aps` in `cardinal/archives/Scenarios.sga` (36 presets, `atmo_presets.h`), passed without the extension. The 06.09 pane guessed biome names and never loaded anything. Presentation only; the presets hold light, sky, colour LUT, cloud shadows and haze, no rain or snow. Settings live in `[camera]` (`atmo_auto`, `atmo_preset`, `atmo_sec`).

## 39 KB `Downloads\ScarToolKit.exe` (ESP_DLL/FOW, Mar 2026)

Different binary from packed V3.9 (39 424 B, PDB `ESP_DLL\FOW`, SHA-256 `c6c53c19…`). Do **not** run it on current Relic and do **not** copy its RVAs into `offsets.cpp`.

Its FoW is three **in-game** calls via RWX `CreateRemoteThread` (56 B stub, `OpenProcess(0x1FFFFF)`):

| Stub `offset.txt` | HOOK already (SCAR, in-match) |
|---|---|
| `transition` | `FOW_UIRevealAll_Transition(0.5)` — **keep** |
| `revealEntities` | `FOW_UIRevealAll` type-guarded (`FOW_UIRevealAllEntities` is not a live Lua name) |
| `revealAll` | `FOW_PlayerExploreAll(player)` orig (`FOW_ExploreAll` is not bound) |

HOOK **Reveal Map (Memory)** is that same UC combo through `ScarDoString` after pulsing FOWCTRL1+11. **Full Reveal** is +8 + VEH + radar, not this stub. The stub’s compiled RVAs (`0x1A7A3A0` / `0x1A7A340` / `0x1A79E80`) are an **old** Relic layout; on 16.3.11308 they will no-op or crash. `FOW_UIRevealAll` (no `_Transition`) is the ABC0+F9D0(dur=0) slam path if bound — overlay still `type()=='function'` (live dump 16.3.11308 does not bind it). Do not treat stub `revealAll` as a license to drop Transition or to retarget `kFowExploreAll` `0x1ABE220` to `0x1ABE4D0`.

ESP in that EXE is an external GDI HWND + another CRT decrypt stub. Overlay already draws in D3D Present. Name XOR / herdable globals in that file are also build-specific.

Product takeaway: Full Reveal = FOWCTRL1 `+8` + VEH + radar. Memory = `+11` + SCAR UC combo. Do not add that EXE’s CRT into Relic. Native `innerVa` calls are only worth it after live `ScarNativesDump` on this build, with the 0.5 transition arg, never the stub’s hardcoded RVAs.

## What we cannot clone from ScarToolKIT

Licensed FOW_DLL is an **optional** sidecar (`internal\licensed_helper\helper_pe_FOWCTRL1.dll`, gitignored `*.dll`). Overlay Full Reveal / MemoryShot already run on the in-module `FOWCTRL1` slab. If the sidecar is present, overlay maps sections only; helper threads / KiUser / fog pointer-walk do not run. Host WPM `+11` on that slab is consumed as `ScarRevealMapMemoryShot` (never mixes with +8). `+8` Full Reveal is `MapHackFowCtrlSetHold` + `MapHackFowCtrlPortArm` (poison+VEH) + radar. Zoom `+16/+20` is Autodeclinate **max-cap**. Handshake secret stays in their EXE — overlay acks any nonzero `+32`.

## Sibling WPM magics (in-module, `.stkslab` RWS)

Same pattern as FOWCTRL1: ASCII QWORD at +0, enable at +8, implTag `AOE4`. No Relic `.text`. `toolkit_slabs.cpp` consumes WPM then mirrors overlay state.

| Magic | +off | Overlay |
|---|---|---|
| `FOWCTRL1` | +8 / +11 / +16 / +20 | Full Reveal hold / Reveal Map Memory / zoom max-cap (`maphack_fowctrl.cpp` → `zoom.cpp`) |
| `TCIDLE01` | +8 | Radar idle production alert |
| `SHEEPSP1` | +8 | Radar + ESP sheep highlight |
| `PLRESP01` | +8 | ESP show-enemy |
| `2DESP001` | +8 | ESP boxes on (D3D Present, not `ScarToolkit_ESP2D` HWND) |
| `RESHUD02` | +8 rising | `ScarInjectResourceHud` |
| `AICTLR01` | +10 | Lock-villagers flag only (ecx 19; helper PE not present) |

Zoom `FOWCTRL1+16/+20` → `ZoomConsumeHelperCap` (Autodeclinate max, not live dist).

## Sibling magics (not FoW)

Toolkit also WPMs `TCIDLE01` / `SHEEPSP1` / `PLRESP01` / `2DESP001` / `RESHUD02` / `AICTLR01` into the **missing** helper. Overlay equivalents are overlay draw + NativeEspData queries — **not** extra Relic slabs and **not** `our_fow_helper.dll`. See `docs/SCARTOOLKIT_NATIVE_PARITY.md`.

# RelicCardinal command-line flags — full impact

Читаемый справочник по каждому флагу: [RELIC_LAUNCH_OPTIONS.md](RELIC_LAUNCH_OPTIONS.md). Этот файл — журнал проходов.

Age of Empires IV **16.3.11308.0**. Every token below was confirmed in IDA on the live pe-sieve image, then cross-checked against shipped SCAR bags.

2026-09-26 re-check, headless multi-IDA instance `qv31` (no GUI), same IDB `runtime_exe.i64`, imagebase `0x7FF7A5500000`. `GetCommandLineA` import `0x7FF7AABDE598`: together with `GetCommandLineW`, ` -notrap` and ` -nodbg` the xref dump is 496 records / 184 unique functions (the two extra functions are the `GetCommandLineW` ingest pair). Layer B space-anchored strings are still exactly six. `Game_IsRTM` at `0x7FF7ACCA2961` still has 0 xrefs. `Dev_NoDbg_Check` `0x7FF7A9077110` decompile matches the `-nodbg` gate below. Steam exe `D:\SteamLibrary\steamapps\common\Age of Empires IV\RelicCardinal.exe` is still **16.3.11308.0** (144 752 932 bytes, appmanifest buildid `24231237`). `memory.bin` has zero hits for ` -windowed`, ` -noborder`, ` -nomovies`, ` -vulkan`, ` -novid`, ` -dx11`, ` -dx12`, ` -high`, ` -dev`, ` -rtm`.

| | |
|--|--|
| IDB | `K:\aoe4_dlc\dumps\RelicCardinal_60644_20260906_full_analysis\ida\runtime_exe.i64` |
| Imagebase | `0x7FF7A5500000` (RVAs only; do not mix VAs) |
| Dump / PID | ProcDump folder `RelicCardinal_60644_20260906_full_analysis\`, PID **60644** |
| SCAR bags | `AOE4HOOK\sdk\scar\sga\` (engine + cardinal) |
| Session log | [findings/2026-09-06-relic-cmdline-flags.md](findings/2026-09-06-relic-cmdline-flags.md) |
| Attach ritual | [UPDATE_GUIDE.md](UPDATE_GUIDE.md) §2.3.1 |

Steam → Properties → Launch options. The window title becomes `Age of Empires IV -dev -nodbg` because Relic appends the **raw** command line after the product name. That is **not** proof a token has a handler.

There is **no whitelist**. Layer A stores every `-name` / `+name`. Unknown names sit in the table and do nothing until some C++ or SCAR queries them. Layer B `strstr` tokens **do** require a leading space (` -nodbg`).

---

## What no Steam flag does

None of these tokens, alone or together:

- disable Relic anti-debug / WindowWatcher / RA hasher / FairPlay
- hide debugger windows
- set `Misc_IsDevMode()` (that byte is independent — see below)
- unlock ranked / online “dev lobby”
- replace overlay `DllInjector --dev` (different binary, different flags)

`-dev -nodbg -notrap` is the **offline attach** line. It relaxes Relic’s own debugger/crash UI. It does not neutralize Relic integrity.

---

## How Relic parses argv

Two layers. A token can hit both.

### Layer A — generic table (SCAR `Misc_*`)

Built from `GetCommandLineW` + `CommandLineToArgvW` (RVA `0x3AE9EC0`). Skips `argv[0]`. Each later token becomes a 72-byte row:

| Offset | Field |
|--------|--------|
| +0 | `std::string` name (SSO; cap at +24) |
| +32 | `bool` has_value |
| +40 | `std::string` value |

Table: `.data` RVA `0x84D6B70` (begin) / `0x84D6B78` (end). Ready-flag: byte RVA `0x844B2EF` (`byte_7FF7AD94B2EF`). Lookup `_stricmp`, case-insensitive (RVA `0x3AF23B0`). Strips one leading `-` or `+-` from the **query** name.

| Native | RVA | Meaning |
|--------|-----|---------|
| `Misc_IsCommandLineOptionSet(name)` | `0xBD9B20` | token present |
| `Misc_GetCommandLineString(name)` | `0xBD9B80` | value; asserts if unset |
| `Misc_GetCommandLineInt(name)` | `0xBD9C90` | value as `%i` |
| `Util_GetCommandLineArgument(name)` | SCAR wrapper | `nil` or value; **call once per key** |

Forms that work:

```text
-dev
-timer 15
-missioncheat AGEUP:something
-argfile C:\opts.txt
-window  -width 1920  -height 1080
+dev
```

`/name` is **not** accepted. If the table is not ready yet, Layer A falls back to a raw scan of `GetCommandLineA` (RVA `0x3C053E0`) — substring match, no required leading space.

`-argfile path` (RVA `0x3AF2670`) reads more tokens from a file. Fail → MessageBox `Invalid parameter passed to the -argfile command` (skipped if `-nonInteractiveMode`).

### Layer B — early `strstr` (must be on the Steam line)

Runs at CRT / AppInit, often **before** the table exists. Compares a fixed ASCII blob **including the space**:

```text
" -nodbg"   " -notrap"   " -forcetrap"   " -wertest"
" -nonInteractiveMode"   " -notrace"
```

Steam launch options become `RelicCardinal.exe -dev -nodbg`, so the space is there. Concatenating without spaces (`-dev-nodbg`) fails Layer B. Injecting after init **cannot** undo trap-handler install.

`Game_IsCommandLineOptionSet` exists as a string (`0x7FF7ACC94D31`) with **zero xrefs** in this IDB. Use `Misc_*`.

State-tree conditions (option name comes from data, not a fixed C++ string): `FrontEnd_CommandLineOptionExists`, `FrontEndFlow_DevOnlyCommandLineSetCondition`, `FrontEndFlow_DevOrRTMCommandLineSetCondition`, `FrontEndFlow_DevOnlySkipBootflowCommandLineSetCondition`, `Condition_HasCommandLineArgument`.

---

## `Misc_IsDevMode()` ≠ `-dev`

| | `-dev` (Layer A `"dev"`) | `Misc_IsDevMode()` |
|--|--------------------------|---------------------|
| What | argv token | `.data` byte RVA **`0x84421BC`** |
| Reader | SCAR + two C++ boot paths | RVA `0xBD9D40` — `return byte` |
| Writer | **does not write this byte** | SimApp boot `sub_7FF7A6DBA800` (RVA `0x18BA800`): `byte = a1`, and `a1` is `*(object+104)` from wrapper `0x7FF7A6D2D5F0` |
| File I/O | no | three helpers + SCAR `Misc_GetFileSize` / `Misc_AppendToFile` / `Misc_QueryDirectory` refuse unless byte is 1 |

Live PID **39056** (Steam `-dev -nodbg -notrap`, **before** overlay): byte was **1**. That is one sample — it does **not** prove `-dev` writes the byte (SimApp `object+104` is still the writer). No no-`-dev` control tonight. SCAR that wants “launched with `-dev`” must still use `Misc_IsCommandLineOptionSet("dev")` if the byte can be 0 on other boots.

`debug_preroll` is the only shipped SCAR that requires **both**: `Misc_IsDevMode() and Misc_IsCommandLineOptionSet("debug_preroll")` (`engine/Data/scar/core.scar`).

File helpers (all return 0 / fail if the byte is 0):

| VA | Role |
|----|------|
| `0x7FF7A8C46040` | UTF-8 path → wide open / read (mode 2) |
| `0x7FF7A8C46620` | same, write/append path (mode 3) |
| `0x7FF7A8C46820` | exists / query (`sub_7FF7A8FFD900`) |
| `0x7FF7A8C46B10` | registers those as SCAR `Misc_GetFileSize`, `Misc_AppendToFile`, `Misc_QueryDirectory` |

**Permission:** host-disk file size / append / directory listing from SCAR. **Forbidden when byte=0** (retail). `-dev` does not grant this.

---

# Layer B — debugger / crash (must be Steam)

## `-nodbg`

| | |
|--|--|
| Match | exact ` -nodbg` (7 chars with space), `GetCommandLineA` + `strstr` |
| Parse | `Dev_NoDbg_Check` RVA `0x3B77110` (`0x7FF7A9077110`) |
| Flag | `.data` RVA `0x844B2ED` (`g_Dev_NoDbgFlag`) |
| Once | RVA `0x85A6C39` (`g_Dev_NoDbgParsed`) — parse once, then reuse |

```text
return !g_Dev_NoDbgFlag && IsDebuggerPresent();
```

When the flag is 1 the gate is **always false**. Sixteen code xrefs call this function (hang timeout, trap init, crash-dialog path, assert/`__debugbreak` sites). Those sites treat “debugger present” as a reason to `__debugbreak`, skip a UI, or change trap install.

**Does:** suppress Relic’s *own* `IsDebuggerPresent` reactions after the flag is cached.

**Does not:** hide windows, stop WindowWatcher, stop RA hasher, stop FairPlay, uninstall an already-installed trap handler.

The flag is **lazy**. Live PID **39056** (2026-09-06 23:16, Steam `"…RelicCardinal.exe" -dev -nodbg -notrap`, base `0x7FF7E43A0000`): byte and `parsed` stayed **0** until overlay `DevForceNoDbg` (was 0 → 1). `Dev_NoDbg_Check` had not run. Trap init still sees `strstr(" -notrap")` on the raw line and does **not** need this byte.

Overlay `ForceNoDbg` (`patch_game.cpp`) writes the same byte **once**, inside a confirmed Patch Game RUN. Inject does not write it (`auto_run=0`). The 50 ms loop after RUN is the retitle hammer (`kRetitlePeriodMs`, 8 s), not a nodbg re-arm. There is no `DevForceNoDbg` symbol in the current tree.

## `-notrap` / `-forcetrap` / `-wertest`

Trap-handler init RVA `0x3C021F0` (`0x7FF7A91021F0`). Global object `off_7FF7AD949D10`.

```text
skip_traps = strstr(" -notrap") || Dev_NoDbg_Check()
force      = strstr(" -forcetrap")
```

| Condition | What is installed |
|-----------|-------------------|
| `force \|\| !skip_traps` | real SEH/VEH crash object (`sub_7FF7A91D83D0`) |
| else (skip, not forced) | no-op vtable `off_7FF7ABB09BE8` (object zeroed, then stub vtable) |
| real traps **and** ` -wertest` | WER-test vtable `off_7FF7ABB0FF38` instead of the default crash object |

Then vfunc +168 / +136 run on the object. Then `strstr(" -nonInteractiveMode")` is passed to vfunc +96 (suppress crash UI).

**`-notrap` permission:** no Relic VEH/SEH crash wrapper. Useful so VS / x64dbg own the exception. **Forbidden:** Relic will not show its own crash dialog / WER path.

**`-forcetrap`:** forces the real handler even if `-notrap` or a live debugger (`Dev_NoDbg_Check`) would skip it.

**`-wertest`:** only meaningful when traps **are** installed. Swaps in the WER-test handler.

Must be on the Steam line. Inject after this function has run does **not** uninstall the real handler.

## `-nonInteractiveMode`

Hits Layer B **and** Layer A (`nonInteractiveMode`).

| Site | RVA / VA | Effect |
|------|----------|--------|
| Trap init vfunc +96 | `0x3C021F0` | tell crash object “no UI” |
| `NewHandler` (OOM) | `0x3C054E0` | **skip** `MessageBoxW`; still logs `failed to allocate` and fatal-crashes (`MEMORY[0]=0`) |
| Crash / assert dialog `0x7FF7A9072CE0` | `0x3B72CE0` | if token set, return **2** immediately (no string build, no `Dev_NoDbg_Check` dialog path) |
| Sister `0x7FF7A9072F70` | | if token set, skip the log-file callback |
| AppInit MessageBox sites | many | RAM warning, `-argfile` error, etc. skipped |

**Permission:** headless / CI — no modal dialogs. **Forbidden:** user never sees Relic MessageBoxes; OOM still kills the process.

## `-notrace`

Layer A name `notrace` (also a ` -notrace` string). Stack-walk / `dbghelp` capture (RVA `0x3AE7C80`) **skips** `StackWalk64` when set.

**Does:** no Relic stack walk on asserts. **Does not:** disable logging entirely.

---

# `-dev` — every C++ and SCAR change

Layer A name `"dev"`. There is **no** `" -dev"` string. Two C++ consumers + SCAR.

### C++ 1 — hang / logger (RVA `0x66BCE0`, `0x7FF7A5B6BCE0`)

Always (flag or not):

1. Start `Utility/LoggerThread` if not already up.
2. Allocate a 120-byte hang object, timeout **240000 ms** (4 min), thread name `Utility/Hang Detection`, worker `0x7FF7A5DCD570`.
3. Store it at `app+1352`. Install `off_7FF7AD948CB8 = sub_7FF7A5B68BD0`.

Then writes `*(WORD*)(app+720)`:

| Condition | Word | Bytes |
|-----------|------|--------|
| `-dev` **or** `-autotest` (`0x7FF7A9061B70` caches autotest into `0x86AD414`) | `0x0101` | `+720=1`, `+721=1` |
| neither | `0x0100` | `+720=0`, `+721=1` |

The extra low bit marks the hang-watch as **dev**. Hang thread still runs (page-fault / RAM warnings). `-logPageFaults` (same thread) logs `Tick -- There were [%u] hard and soft page faults…`.

### C++ 2 — display / log sinks (RVA `0x3B73180`, `0x7FF7A9073180`)

`v22 = 1` if `-autotest` **or** `-dev`. Allocates a **3616-byte** (`0xE20`) display object (`qword_7FF7AD9CD508`).

| `v22` | What happens |
|-------|----------------|
| 1 | copy **27** triples (0x408 bytes) from `unk_7FF7ACC85600` into `object+3576`; add callback `0x7FF7A9072CA0` (**Warnings** log: `-- Log file for all dbTracef messages --`); set `*(object+3568) = 1` |
| 0 | `*(object+3568) = 0` — no extra sinks |

Always installs:

- singleton+552 → `0x7FF7A90721B0` (**Unhandled** log: messages not properly caught)
- if `object+3600` set → `off_7FF7AD9CC9C8 = 0x7FF7A9072CE0` (crash-dialog; respects `-nonInteractiveMode`)
- if `object+3608` set → `off_7FF7AD9CC908 = 0x7FF7A9072F70`

The `exclusive_fullscreen` lookup at the **tail of this function is dead** — result discarded, then `return 1`. Real window-mode handling is `0x7FF7A5DD0340` (below).

### SCAR — only when `Misc_IsCommandLineOptionSet("dev")`

| Effect | File | Permission |
|--------|------|------------|
| Intel-event debugger (`_IntelDebug`, Replay/Next/Prev), `Util_ToggleAllowIntelEvents` | `engine/Data/scar/scarutil.scar` | step campaign VO / HUD intel |
| Broadcast cheat commands on `GE_BroadcastMessage` | `cardinal/Data/scar/gameplay/cheat.scar` | see cheat table below |
| Campaign training hooks | **commented out** in `training_missionzero.scar`, `campaigntraininggoals.scar` | none in this build |

`cheat.scar` **returns immediately** if `-dev` is absent. Commands (first token of a type-0 broadcast):

| Token | Action |
|-------|--------|
| `AGEUP` | next age upgrade (`feudal` → `castle` → `imperial`) via `LocalCommand_PlayerUpgrade` |
| `ECONOMY` | +1000 food/wood/gold/stone/merc |
| `FOW` | toggle `FOW_PlayerRevealAll` / unreveal+unexplore |
| `INVULNERABLE` | toggle min-cap invuln on all players’ squads + entities |
| `INSTANTBUILD` | ×100 harvest + construction + production |
| `DESTROYHOVERED` | `Entity_Kill` by id |
| `TELEPORTSELECTED` | warp selected squads to xyz |

These are **network broadcast** cheats. They require `-dev` on **that client’s** command line. They do not require `Misc_IsDevMode()`. They do not by themselves set `_match.is_cheat_enabled` (that is `-cheat`).

### `-dev` does **not**

- write `g_IsDevMode`
- skip frontend bootflow
- reveal fog (`-no_fow` / `-cheat` / lobby debug options)
- grant 20k resources (`-cheat`)
- disable RA / FairPlay / WindowWatcher
- install the Lua debugger socket (`-lua_debugger_port`)

---

# Frontend / boot

Predicate RVA **`0x3DC6DA0`** (`0x7FF7A92C6DA0`). Return **1** = skip bootflow (jump into a match). Return **0** = keep frontend.

```text
if !*(engine_obj + 720):          return 0   // engine bootflow disabled
if -dont_skip_bootflow:           return 0   // force frontend
if -start_scenario <path>:        copy path, return 1
if -load_game <path>:             copy path, return 1
if -replay <path>:                copy path, return 1
if -autotest:                     return 1
else:                             return 0
```

| Token | Value | Permission | Forbidden |
|-------|-------|------------|-----------|
| `dont_skip_bootflow` | flag | keep main menu even if other skip tokens are present | cannot auto-load a scenario from CLI while this is set |
| `start_scenario` | path | skip FE → load that scenario | no menu |
| `load_game` | path | skip FE → load save | no menu |
| `replay` | path | skip FE → play replay | no menu |
| `autotest` | flag | skip FE; also triggers `-dev`-like display sinks + hang bit + game-loop quit (`[GameApp] Requesting game quit`) | interactive play is not the point |
| `autotestmap` | mission name | ScriptedFrontEnd: which map autotest loads; missing → assert | |

Companion: `Game_StartSinglePlayerFromCommandLine` / `Game_StartSkirmishFromCommandLine` (registered in `0x7FF7A5FA6590`) consume Layer A from SCAR/Lua for scripted starts.

---

# Window / display (RVA `0x8D0340`, `0x7FF7A5DD0340`)

Settings key `qword_7FF7AD951558`. First match wins for mode:

| Token | Settings int | Meaning |
|-------|--------------|---------|
| `exclusive_fullscreen` | **1** | exclusive FS |
| `fullwindow` | **0** | borderless / full-window |
| `full_desktop` | **3** | cover desktop |
| `window` | **2** | windowed |

Then:

| Token | Effect |
|-------|--------|
| `AllowResize` | window style 31 instead of 30 |
| `window_x` / `window_y` | parse `%i`, set origin; also clears bit 3 of the style word |
| `window_x_negative` / `window_y_negative` | same, then **negate** that axis |
| `width` / `height` | parse `%i`; if absent, fall back to saved settings / desktop probe (`%zu:%zu:%zu:%zu`) |

Creates the HWND via `0x7FF7A907FC70` and stores it in `qword_7FF7AD9CCE48` (same pointer `NewHandler` uses for MessageBox parent).

`width` / `height` / `freemouse` / `lockedmouse` are also read in `0x7FF7A5DBA230` (mouse clip / free-look).

**Does not** change FOW, cheats, or integrity.

---

# Graphics / FX / archives / device

| Token | Site | Does | Forbids / notes |
|-------|------|------|-----------------|
| `nographicsautodetect` | `0x7FF7A5DBEEC0` | skip AGS auto-detect; log `Graphics Auto-Detect: no settings applied` | GPU quality not auto-applied |
| `forcesettingsgroup` | same | force named group (`graphicsquality_low`, `graphicsquality_low_and_locked`, …) | overrides user defaults |
| `nofx` | `0x7FF7A6CD5230` | skip loading `data:StateTrees\viz\StateTree.bin` + `fragments\StateTree.bin` | no FX viz trees |
| `fxlog` | same | enable FX / state-tree log | extra I/O |
| `nopatchload` | `0x7FF7A6DA1240` | skip patch-archive load; on `corrupt` / `missing` / `unmappable` log `Archive [%ls] is [%s]!` and **Skipping** instead of **Unable to continue** | can boot with a broken SGA (unstable) |
| `invbatchingoff` | `0x7FF7A9015650` | DATA / DATAPREVIEW / GENERIC path ctor | inventory batching off |
| `DXDebugDevice` | D3D path | D3D debug device (DRED / breadcrumbs / pagefaults). Messages say “run with `-DXDebugDevice`” | slower, debug layer required |
| `fakeDeviceType` | `0x7FF7A8FEB3E0` | override device enum. Known: `PC`, `XboxOne`, `XboxOneS`, `XboxOneX`, `XboxOneXDevkit`, `XboxScarlettLockhart`, `XboxScarlettAnaconda`, `XboxScarlettDevkit`, `XboxSeriesS`, `XboxSeriesX`, `Playstation5`, `PCHandHeld`, `SteamDeck`. Unknown → log `Encountered unknown device type passed in with fakeDeviceType: %s` and fall back to real device | UI / input / feature gates follow the **fake** platform |
| `sync_high` | AppInit `0x866370` | demand large 64-bit VAS | fail → MessageBox with MiB numbers |
| `sync_high_memory` | same | companion MiB int | |
| `MoviePlayerPixelCount` | `0x7FF7A6F1EF00` | treated as cmdline **or** config key for movie resolution pick | |

RR “Global Default Debug Features” pack (`0x7FF7A8C29B80`) — each is a Layer A flag that turns on a render-debug feature:

`RRStateTrackingOn`, `RRStateTracking1`, `RRStateTracking2`, `RRStateTrackingMeshCollections`, `RRStateTrackingIMGUI`, `RRStateDumpOnCrash`, `RRGPUTimer`, `RRSendTelemetry`, `RRBreakOnLoadFail`.

---

# Paths / Lua / config

Writable-folder boot `0x7FF7A5DB6A60`:

| Token | Effect |
|-------|--------|
| `logfiles` | base for `LogFiles\%s_%02d_%02d_%02dh-%02dm-%02ds` |
| `screenshots` | screenshot root |
| `userdata` | user data root |
| `log` | extra log path |
| `hd` | HD / high-res data root |
| `configtest` | use config-test tree; MessageBox on bad path |

`showdebugsettings` — SystemConfig loader (`0x7FF7A8B2C9C0`) exposes pending debug settings.

`luaconfig` — `LuaConfig.cpp` (`0x7FF7A722BEE0`) writes `terrain-layout-lua-log.txt` / `%s/terrain-layout-%u/%s` when set.

`-lua_debugger_port N` — `0x7FF7A8C110B0`. Opens a **listen socket** (default **8081**). Logs `[LuaDebugger] Binding socket on port %d`. Invalid `%hu` → log and keep 8081.

**Permission:** remote Lua debugger can attach to that port. Retail with this token is a listen socket on the machine.

`init` — scardocs example (`-init test.lua`); consumed where ScriptedFrontEnd / `Misc_GetCommandLineString("init")` is wired.

`no_ai_matchheartbeat` — AI match loop `0x7FF7A5CFEB10` skips the heartbeat job (`current_job` / `none`).

Generic “is this name on the line?” helpers (name comes from the caller / state tree, not a fixed string): `0x7FF7A5FA8B60`, `0x7FF7A5FE21E0`, `0x7FF7A7B40AF0`, `0x7FF7A92C6D40`, `0x7FF7A6C1A180` (int via `wcstol`).

---

# Match / debug SCAR (Layer A)

Read at mode init (`standard_mode.scar` and the same four lines in seasons / sandbox / none / map_monsters / koth / full_moon / chart_a_course / chaotic_climate).

## `-cheat`

Sets `_match.is_cheat_enabled`. For every **human** player at `OnInit`:

| Also triggered by lobby debug option | Effect |
|--------------------------------------|--------|
| `option_high_resources` | Food 20000, Wood 20000, Stone 5000, Gold 10000 |
| `option_high_popcap` | personnel cap **200** |
| `option_instant_build` | `cost_ticks_modifier` = 0.01 on every possible entity BP; `GE_ConstructionComplete` rule for finish-now |

**Does not** require `-dev`. **Does not** enable `cheat.scar` broadcast commands. **Does not** reveal fog (that is `-no_fow` or `option_reveal_map`).

## `-no_fow`

Sets `_match.revealMap`. At init: `FOW_PlayerRevealAll` for every human. Same as lobby `option_reveal_map`.

Lobby FOW enums still apply later (`option_fow_explore` → `FOW_ExploreAll`, `option_fow_reveal` → `FOW_ForceRevealAllUnblockedAreas`).

## `-no_units`

`SGroup_DestroyAllSquads` for **every** player (including AI). Log: `Removed all squads owned by Player %d`.

## `-no_gaia`

Destroy all neutral entities of type `animal`. Log: `All neutral animal entities removed`.

## `-debug`

`gamesetup.scar`: `__IsDebug = true` → `_ShowDebugMenu()`:

1. WITH INTRO — play NIS
2. NO INTRO — start mission, skip NIS
3. NO MISSION — no mission logic

Also extra prints in `challenge_mission_advancedcombat_automated.scar`. Toggle later via `GameSetup` helpers (`return __IsDebug` / set).

## `-score` / `-scores`

`gameplay/score.scar`: `score` = total only; `scores` = military + eco + total.

## `-timer N`

Wonder / sacred-site victory time = `N` **minutes** (`* 60` seconds) in `winconditions/wonder.scar` and `religious.scar`.

## Speed multipliers (every standard-like mode)

`StandardMode_SetSpeed` (`standard_mode.scar`) and the same block in seasons / sandbox / none / map_monsters / koth / full_moon / chart_a_course / chaotic_climate:

| Token | Field | Default |
|-------|-------|---------|
| `speed` | master default for the five below | 1 |
| `build_speed` | construction | `speed` |
| `repair_speed` | repair | `speed` |
| `gather_speed` | gather | `speed` |
| `upgrade_speed` | research | `speed` |
| `production_speed` | production | `speed` |

Value = `math.abs(tonumber(Util_GetCommandLineArgument(arg)))`. Missing / 0 → default. Applied as Relic `MUT_Multiplication` modifiers on every player. **Does not** require `-dev` or `-cheat`.

---

# `Game_IsRTM()` / `-rtm`

scardocs (`LuaLibGame.cpp`): “Using `-rtm` from the command line will cause this function to also return true in non-RTM builds.”

| | |
|--|--|
| Native | `Game_IsRTM` — XOR-encrypted name (RVA `0x77A2961` = 60644 VA `0x7FF7ACCA2961`, **0 xrefs**). Same XOR ritual as `AI_IsRTM` (`0x7FF7ACD198B1`, decoded in registrar `0x7FF7A7E9BB70`). Disk / `unpacked_static` / gold / oracle PE keep `cc eb e4…` at that RVA. Only a **live image** (60644 `memory.bin` / runtime IDB) has plaintext. Compact `.text` unpack does not decode `.rdata` names. |
| Sister | `AI_IsRTM` (AI bags: `utility.scar` / `debug.scar` skip debug paths when true) |
| C++ `"rtm"` literal | **not** the CLI check. `0x7FF7A5CD26B0` writes telemetry field `"%hs %hs", "rtm", branch`. Crash-dump helpers `0x7FF7A9105A70` / `0x7FF7A91EA820` format `%s_%s_%s` and happen to xref the same blob. |

This retail image has **no** Layer A `_stricmp("rtm")` consumer. The native still exists (in_vm). Probe: `Game_IsRTM()` or `Misc_IsCommandLineOptionSet("rtm")`.

SCAR when `Game_IsRTM()` is true:

| File | Effect |
|------|--------|
| `cardinal.scar` `cardinal_alert` | **return immediately** — no ALERT MessageBox (even with `-campaign_debug`) |
| `training.scar` | RTM branch of training UI |
| `army.scar` / `army_encounter.scar` / `cardinal_encounter.scar` | skip non-RTM debug |
| `rogue_rounds.scar` | `assert(Game_IsRTM(), …)` on bad subwave (RTM = quieter fail) |
| `rogue_tech_tree.scar` | extra debug only when **not** RTM |

`TestConfig_LoadFromCommandLine` is in scardocs (`engine/scar/test/testconfig.scar`) but **`TEST_CONFIG` / `TestConfig_*` strings are absent from every Relic PE copy** (60644 runtime image + 26392 pe-sieve bins) and from Relic heap in dumps that do not have overlay `scar_natives` / checksum-wrapper lists mapped (18816: only `HitTestConfiguration` false positives). 60644 full-dump hits sit next to `AOE4HOOK_TRUST` / `scar_natives_live.scar` — overlay name list, not a Relic-decoded registrar.

---

# Campaign / intel / training / rogue SCAR

| Token | File | Does |
|-------|------|------|
| `missioncheat MODE:VALUE` | `gamesetup.scar`, `missioncheatmenu.scar` | split on `:`; sets `_CheatMenuMode` / `_CheatMenuValue`; jumps campaign cheat-menu state (CTRL+Enter debug menu) |
| `debug_preroll` | `core.scar` | **only if** `Misc_IsDevMode()`: skip preroll, trigger from console |
| `delay_endsp` | `scarutil.scar` | delay end-of-SP intel if intel events are on |
| `skip_speech` | `speech.scar` | skip speech playback |
| `objectives_debug` | `core_objectives.scar` | objective debug prints |
| `campaign_debug` | `cardinal.scar` | campaign debug |
| `debugplans` | `core_encounter.scar` | `_b_debugEncounterPlans` |
| `immediateTags` | `training.scar` | training tags immediately |
| `notraining` | `training.scar` | disable training (also if `World_IsReplay()`) |
| `forceEnableTags` | `training.scar` | force training tags |
| `skipBaybarsTimer` | `abb_m5_mansurah.scar` | skip Baybars timer |
| `army_debug` | `ai/army.scar` | AI army debug |
| `army_encounter_debug` | same | encounter debug |
| `wave_generator_debug` | `ai/wave_generator.scar` | wave generator debug |
| `rogue_idle_squads_assert` | `rogue_rounds.scar`, scenario | assert on idle rogue squads |
| `littlegreenman` | `rogue_poi.scar` | force crop-circle POI |
| `objective_1` / `objective_2` | `rogue_objectives.scar` | force rogue side-objective **name** (value string) |
| `no_scripted_camera` | `missionomatic_actionlist.scar` | skip scripted cameras |
| POI table `.name` | `rogue_poi.scar` | if that name is on the CLI: `force_spawn = true`; optional value picks champion / siege SBP |
| `CampaignAutoTest` | every `*_automated.scar` (Abbasid M1–M8, Ugra, Lumen Shan, Ottoman challenge, advanced combat) | import test framework; `Game_AIControlLocalPlayer` + `AI_Enable`; run checkpoint script |
| `NoSwoopy` | same files | skip intro camera (`Game_SkipAllEvents`) |
| `CaptureLimassol` / `DestroyFamagusta` / `DestroyKyrenia` / `AccelerateEnemyAttacks` | `abb_m8_cyprus_objectives.scar` | force Cyprus debug objectives / speed enemy attacks |
| `SkipFranksGathering` / `SkipEconPhase` / `SkipArmyCountdown` | `abb_m1_tyre_objectives.scar` | skip Tyre phases (later tokens imply earlier ones) |
| `fullscreen_nis` | `cardinal_narrative.scar` | force fullscreen for intro/outro NIS (`Util_FullscreenMode`) |
| `rogue_stress_test` | `rogue_data.scar` | `ROGUE_STRESS_TEST = true` — extremely fast wave ramp (perf) |

POI CLI keys (force spawn): `poi_mine1`, `poi_village1`, `poi_village2`, `poi_siege1`, `poi_siege2`, `poi_knight`, `poi_allies1`, `poi_allies2`, `poi_camp_besieged1`–`4`, `poi_favored_champion`, `poi_random_champion`, `poi_shepherd`, `poi_relic1`, `poi_holy1`, `poi_hoard1`, `poi_hoard2`, `poi_great_wolf_den`, `poi_caravan1`, `poi_merchant_hoard`, `poi_great_ruins`, `poi_random_siege1`, `poi_random_siege2`, `poi_favored_siege`, `poi_mine2`, `poi_monastery`, `poi_cropcircle`, `poi_outpost1`, `poi_outpost2`, `poi_barracks`, `poi_stable`, `poi_archery_range`, `poi_keep`. Champion/siege value strings: `archer`, `berserker`, `crossbowman`, `hospitaller`, `engineer`, `horse_archer`, `horseman`, `knight`, `manatarms`, `mercenary`, `teutonic`, `spearman`, `great_trebuchet`, `mangonel`, `nest_of_bees`, `cannon`.

`rogue_data.scar` also uses `Misc_IsDevMode()` (the **byte**, not `-dev`) for a separate rogue debug path.

`Util_Grab` / `Util_ToggleAllowIntelEvents` scardocs: **only work with `-dev`**.

---

# Third pass — C++ Layer A that the first two catalogs missed

`GetCommandLineA` has **490 xrefs / 182 unique functions**. Most are the inlined “table ready? else raw scan” helper, so each unique function is a real consumer. Third pass harvested ~50. **Fourth pass harvested all 182** — see the section after this one.

False positives (not CLI): intern of attribute names (`fullscreen`, `display_name`, …) that happen to sit in the same function as a later Layer A check. `skipNIS` is a Lua/state-tree key via `0x7FF7A8BA97D0`, not proven Layer A.

## Paths / account / telemetry

| Token | Site RVA | Does | Forbidden / notes |
|-------|----------|------|-------------------|
| `wkdir` | `0x3B76130` | override game working directory (walks Layer A table with `_stricmp`) | relative `..` is canonicalized |
| `userdir` | same | override Documents/`My Games/Age of Empires IV` (must include a drive letter) | invalid → log, keep CSIDL_PERSONAL |
| `rlinkuserName` + `rlinkpassword` | `0xA8BB60` | RelicLink credentials from CLI; after one failed login they are **ignored** (`disregarding command line credentials`) | fallback `userdata:relicLinkAccount.ini` |
| `telemetrySession` | `0x7D26B0` | wide string copied into telemetry blob | |
| `forceVsync` | `0x18B3C70` | bool override → renderer vfunc +144 | |

## Memory / allocator (`0x8BC9C0`)

`memEnvConfig`, `verifyCopyOnDirty`, `relocateSimPools`, `protectUnusedMemory`, `trackTemporaryAllocationCallstacks`, `noMemoryProtection`.

## Networking / store (`0x90B3A0`, `0x8C0310`)

| Token | Does |
|-------|------|
| `publicTest` | API host `api-flight.ageofempires.com` |
| `force_test_server` | API host `api-dev.ageofempires.com` |
| `force_live_server` | force live (`api-dr.ageofempires.com`) even if other tokens would reroute |
| `noSteam` | skip Steam init path |
| `noWs` | skip Windows Store / `news.log` path |

Default host is `api-dr.ageofempires.com`. These tokens change **which Relic HTTP host this process talks to**. They do not disable FairPlay / WindowWatcher / RA.

## Render / D3D / Havok / threads

| Token | Site | Does |
|-------|------|------|
| `nulldevice` | `0x3618CC0` | null renderer |
| `enable_render_thread` / `disable_render_thread` | same | force / suppress render thread |
| `loadrenderdoc` | `0x3AE3200` | load RenderDoc; `d3dlog` then logs “turn off RenderDoc if you want to get logs” |
| `d3dlog` | same | D3D/DXGI debug info queues (`dxgidebug.dll`) |
| `frame_time_stats` / `frame_time_stat_graph` / `frame_times_exit_on_fixed` / `frame_time_fixed_samples` | `0x36BC280` | FPS/frame HUD + optional quit after N samples |
| `singlethreaded_presentation` | `0x1943200` | presentation on one thread |
| `animsystem_singlethreaded` | same | animation system single-thread |
| `nophysicsthreads` | `0x1B651D0` | no physics worker threads (`config\physics_globals.lua`) |
| `hkingamedebugger` / `hkdebugger` | `0x17D7380` | Havok in-game / Visual Debugger |
| `singlethreaded_ee_model` | `0x627560` | EE model single-thread |
| `disable_threading_mode_task_helping` | `0x627670` | disable task-helping |
| `multithread_ai_sim_if_workers_available_enabled` | `0x627E70` | AI sim multithread gate |
| `no_parallel_entity_trees` / `no_parallel_deferred_entity_trees` / `no_parallel_physical_trees` / `no_entity_tree_readonly_validation` | `0x2438B80` | entity-tree parallelism / validation |

## Game / scenario / desktop

| Token | Site | Does |
|-------|------|------|
| `pressanykey` / `startpaused` | `0x68B5C0` | with `autotest`: wait for key / start paused |
| `ageUpPrecache` | `0x3D0630` | age-up precache (also keyed off `autotest`) |
| `scarWarnings` / `disable_async_scenario_loading` | `0x683410` | Game Load — extra SCAR warnings; force sync scenario load |
| `nospeech` | `0x68CE70` | C++ skip speech at `InitializeGEWorld` (separate from SCAR `skip_speech`) |
| `replayvalidation` | `0x697640` / `0x697CA0` | on SCAR/AI fatal in autotest: exit instead of dialog (`Exiting due to … in autotest`) |
| `mod` / `noscarreport` / `dataPreview` / `archivePreview` | `0x202C860` | SCAR error-report / data-preview gates |
| `force_remote_desktop` / `ignore_remote_desktop` | `0x825BB0` | treat session as / ignore Teradici `pcoip_server.exe` + `GetSystemMetrics` |
| `map_gen_biome` / `map_gen_size` / `closeStarts` / `scenario_difficulty` / `force_real_match` | `0x82AB80` | scripted map-gen / mission start (`Failed to find mission [%s]`) |
| `disable_map_unplayable_decorator` | `0x1D01F40` | skip unplayable-map decorator |
| `perftest` | `0x66D100` | GameApp perf-test loop (`Game_StartSkirmish` / `Game_Wait` / `Game_Wait_SimTicks`) |
| `no_nfx` | `0x682290` | string in image is `"-no_nfx"`; Layer A still stores `no_nfx` |
| `warning_as_assert_AI` | `0x6917C0` | AI warnings become asserts |
| `xbox_live_links_count` | `0x8291F0` | int (`strtol`) — Xbox Live link budget |
| `noCloudSaves` | `0x8293C0` | skip cloud-save I/O |

`skipNIS` (C++ / Lua) is a **state-tree / `__g_co` variable**, not a proven Layer A token. Campaign `NoSwoopy` is the SCAR skip-intro flag.

---

# Fourth pass — complete dump + binary harvest (182/182)

Method (2026-09-06, IDB `runtime_exe.i64` / PID 60644 dump):

| Source | Result |
|--------|--------|
| `GetCommandLineA` | **490 xrefs, 182 unique functions**. Strings harvested from **every** unique function (`analyze_batch` strings-only). |
| `GetCommandLineW` | **4 xrefs, 2 functions** — Layer A ingest only (`0x3AE9EC0` / sister). No extra flag names. |
| Layer B `" -xxx"` strings | **exactly 6** (` -nodbg` ` -notrap` ` -forcetrap` ` -wertest` ` -nonInteractiveMode` ` -notrace`). |
| Table lookup `0x3AF23B0` | 75 xrefs. Extra consumers that do **not** call `GetCommandLineA`: gfx autodetect `0x8BEEC0`, Lua debugger `0x37110B0`, `forceVsync` `0x18B3C70`, RelicLink `0xA8BB60`, `wkdir`/`userdir` `0x3B76130`, `fakeDeviceType` `0x3AEB3E0`. Those were already in this catalog; re-harvested, no extra names. |
| Prefix regex `no_`/`force_`/`skip_`/`disable_`/`enable_` | 123 image strings. Most are **blueprint / attribute intern names** (0 CLI). Only names that sit in a GCLA or lookup consumer are listed below. |
| SCAR bags | Full `Misc_*` / `Util_GetCommandLineArgument` literal pass (engine + cardinal). Lua besides DebugHUD: **none**. |
| `Game_IsRTM` | Plaintext at `0x7FF7ACCA2961`, **0 xrefs** (XOR registrar). No Layer A `_stricmp("rtm")` in this image. scardocs still say `-rtm` forces the native true on non-RTM builds. |

Live PID was **not** stepped. Completeness is dump + IDB + shipped SCAR bags.

`nosteam` (`0x3DC6D40` rogue store) and `noSteam` (`0x8C0310`) are the **same** Layer A key (`_stricmp`).

## New C++ Layer A (not in passes 1–3)

Site RVA = VA − `0x7FF7A5500000`.

### Instance / input / cheats

| Token | Site RVA | Does | Forbids / notes |
|-------|----------|------|-----------------|
| `allow_multiple_instances` | `0x8B9E10` | skip Essence named mutex `Essence-0991177D-…` | without it, second instance `PostMessage` + `Shutting down app early` (return 3). Engine `+720` also skips the mutex. |
| `nocheats` | `0x97AA80` | if **set** (or engine `+720` is 0): do **not** register Cheat Menu / `Control+Shift+3` | SCAR `-cheat` / `-dev` broadcast cheats are separate |
| `no_challenges` | `0xA700C0` | skip challenge / event challenge load path | |
| `allowallcrossplay` | `0xA7B650` | if **set**: return 0 (skip platform cross-play gate) | unset → platform check can return 3 |
| `nopatchdownload` | `0xABB510` | skip patch-download object setup | different from `nopatchload` (already-loaded SGA) |
| `casterMode` | `0x3DC2240` | frontend flow picks caster/spectator UI string (+72) instead of default (+56) when object state is 2 | |
| `useAllInputDevices` | `0x3B712C0` | accept every attached input device | |
| `AllowTransitionalInput` | `0xC5DC70` | allow input during transition / load | |
| `autoGroupsEnabled` | `0xA49FD0` | force auto-groups on | |
| `hudrefresh` | `0x3DC7470` | bool predicate only (`return token present`) | caller decides HUD rebuild |
| `window_title` | `0x87F2A0` | override HWND title (else `Age of Empires IV` + raw cmdline) | |
| `localautotest` | `0x3CEA000` | local autotest sister of `autotest` (crash / report path) | |
| `noassert` | `0x3DCDA80` | `System::Initialize` — suppress Relic assert UI | process still runs |
| `debugwindow` | `0x8B4AF0` | AppInit debug window | |
| `chat_cue` | `0xB8FA30` | UI chat cue gate | |

### Scripted match / replay

| Token | Site RVA | Does |
|-------|----------|------|
| `maxslots` | `0x829ED0` | `%zu` slot count for scripted start |
| `teamslotN` / `teamraceN` / `aidifficultyN` | same | `%zu` / `%i` per-slot team, race, AI difficulty (`skirmish` / `campaign` branches) |
| `allowIncompatibleReplays` | `0x8709B0` | load replay whose version ≠ current (`Ignoring replay [%s] as it is version [%u]…` skipped) |
| `show_all_replay` | `0x875000` | list / show incompatible or hidden replays |
| `ReplayDesyncTest` | `0x8DC3D0` | replay desync test harness |

### Precache / CPU / files

| Token | Site RVA | Does |
|-------|----------|------|
| `disableRacePrecaching` | `0x3D08B0` / `0x1B43330` | skip race `.bin` precache |
| `precacheAllAges` | `0x5BCE40` | load `data:raceprecache\*.bin` for every age |
| `ignorePrecacheDenylist` | `0x17E7540` | ignore precache denylist |
| `warning_as_assert_precache` | `0x3B15CE0` | precache warnings → asserts |
| `disableCPUextensions` | `0x8B9330` | MATHBOX mode = `standard` (no SIMD extras) |
| `nofonts` | `0x8BB110` | skip FreeType / font init (`FT2 -- Initialization failed` path) |
| `filelog` | `0x8BC510` | write `Files-EngineData.txt` / `Files-ModData.txt` / `Files-AllData.txt` |
| `disableLuaDebug` | `0x8BFD50` | skip LSNC / Lua debug bind |
| `precacheSoundBanksAll` | `0xADCD50` | force all Wwise banks (`audio\wwiseconfig.lua`) |
| `memorybudget` | `0x1A6D9C0` | memory-budget override |

### Hang / logging / telemetry

| Token | Site RVA | Does |
|-------|----------|------|
| `noTimeOutDetection` | `0x87D570` | hang worker: do **not** self-crash on freeze (`FREEZE -- … Ignoring this hang`) |
| `logTelemetry` | `0x325B840` | extra telemetry file log |
| `entitylog` | `0x1FFC210` | entity spawn/despawn log |
| `debugTail` | `0x3B6DD50` | rotate / keep debug log tail (`%s%s%s.%zd%s`) |
| `noRepeatedLogMessages` | `0x3B71440` | collapse repeated log lines |
| `pathlogs` | `0x3B72230` | Pathfinding sink (`-- Log file for all messages related to Pathfinding --`) |
| `noextrasync` | `0x3B72900` | skip ExtraSyncLog |
| `memorystats` | `0x3BCC900` | memory-stats dump |
| `rulesdebug` | `0x976780` | SCAR rules debug (`data:scar\` event dump) |

### Mapgen / FX / video / render extras

| Token | Site RVA | Does |
|-------|----------|------|
| `map_gen_debug` | `0x18E99D0` | MapGen debug dumps / PNG score maps |
| `map_gen_test_layout` | `0x18EA590` | force test layout name |
| `map_gen_debug_scoremap` | `0x19018E0` | score-map dump (`all` = every layer) |
| `loadAllFX` | `0x977980` | load every FX bag (`_loadAllFX`) |
| `loadAllSkins` | `0x182BB20` | load every skin `.bin` |
| `fxloadimmediate` | `0x3744560` | FX load sync / immediate |
| `autoskipvideos` | `0x175D060` | image string is `"-autoskipvideos"`; Layer A key `autoskipvideos` |
| `noreflections` | `0x18F90B0` | skip reflection pass |
| `noBackgroundLoading` | `0x1A84650` | no background resource thread (`_EN` / `_SQ` locales) |
| `noStampSplats` / `noStampStrips` | `0x1B27930` / `0x1B29A90` | disable terrain stamp splats / strips |
| `MinimapCapture` | `0x1B64830` | minimap capture pipeline |
| `DecalBakeCapture` | `0x1B81260` | decal bake capture |
| `use_legacy_presentation_serialization` | `0x1BA0CA0` | old presentation serialize path |
| `VPXDisableAlpha` | `0x1DE11F0` | VPX movie alpha off |
| `disableminimap` | `0x379FA90` | no minimap render |
| `pointShadowSize` | `0x38272F0` | `%i` point-shadow resolution |
| `noShadowNormalBias` | same | no shadow normal bias |
| `singleshadowcascade` | `0x3827A00` | one shadow cascade |
| `mipdb` | `0x3999F90` | `config\TextureConfig.lua` mip debug |
| `force_inactive_dxdevice` | `0x1813EF0` / `0x3790AF0` | treat D3D device as inactive |
| `ideal_frame_rate` | `0x146AD50` | target FPS cap / ideal rate |
| `audioignorefocusloss` | `0x191B160` | keep audio when HWND loses focus |
| `disable_root_component_merge` | `0x5CA8C0` | skip root-component merge |
| `showDistricts` | `0x9DCB90` | district overlay |
| `showDefaultFocusStyle` | `0x1484C30` | default UI focus style |
| `showpersistentperformancecounter` | `0x599A80` | persistent perf counter HUD |
| `debug_relic_radial_menu` | `0x409630` | Relic radial-menu debug |
| `debug_kickers` | `0x1F92DB0` | kicker debug |
| `formationDisabled` | `0x2139AD0` | disable formations |
| `disable_root_motion` | `0x2661920` | no root-motion anim |
| `no_multithreaded_sim` | `0x8D76B0` | sim on one thread |
| `no_multithreaded_ai` | `0x291A1A0` | AI on one thread |
| `disable_threading_mode_dynamic_updates` | `0x36BAC90` | no dynamic thread-mode updates |
| `noAIResourceMultiplier` | `0x2AA1C30` | ignore `resource_multipliers` for AI |
| `use_pending_combat_fitness_data` | `0x2BFFAD0` | AI combat fitness uses pending data |
| `navigation_drive_directly_to_goal` | `0x2D343C0` | nav: drive straight to goal |
| `disable_hk_license_warning` | `0x36B3FE0` | mute Havok license banner (`0x3e11733f-…Physics.Age_of_Empires_4`) |
| `warning_as_assert_statetree` | `0x3662900` | state-tree warnings → asserts |
| `ReflectResetAbstractObjectsToDefault` | `0x3B34AE0` | reflection reset-to-default |

### PlayFab / sandbox (lookup-only, `0x8C6EF0`)

Not in the 182 GCLA set. Same function as `publicTest` / `force_*_server`:

| Token | Host / sandbox |
|-------|----------------|
| `force_dev_sandbox_1` | `age4-dev01` |
| `force_dev_sandbox_2` | `age4-dev02` |
| `force_dev_sandbox_3` | `age4-dev03` |
| `force_dev_sandbox_4` | `age4-dev04` |
| `force_dev_sandbox_5` | `age4-dev05` |

Also reads channel names `dr-activerelease1`, `flighting`, `aoetest`, `age4`. **Does not** disable FairPlay / WindowWatcher / RA.

### RR / DX debug pack extras (`0x3729B80`)

Already documented: `RRStateTrackingOn/1/2/MeshCollections/IMGUI`, `RRStateDumpOnCrash`, `RRGPUTimer`, `RRSendTelemetry`, `RRBreakOnLoadFail`. Same function also treats these as Layer A:

`NVAftermath`, `NVAftermathStageEventMarkers`, `NVAftermathDrawCallEventMarkers`, `DXDebugDriver`, `DXCrashOnHRESULT`, `DXDRED`, `DXDREDBreadcrumbs`, `DXDREDPagefault`, `DXDREDWatson`, `DXWarpDevice`, `DXPIXStageEventMarkers`, `DXAutoNameCommandLists`, `DXBreakOnWarning`, `DXBreakOnError`, `DXGpuBasedValidation`, `Renderdoc`, `DXDebugDevice`.

### Not CLI (verified this pass)

OpenSSL blobs (`no_tls1`, `no_ticket`, …). Weapon / EBP attribute intern (`enable_in_building`, `skip_cost`, `force_dropoff`, `no_map` in Party.cpp, `skip_reflection` as viz flag). `Game_IsCommandLineOptionSet` still **0 xrefs**. `TEST_CONFIG` / `TestConfig_LoadFromCommandLine` still **absent** from Relic PE (all dump copies) — see dump corpus below.

### Still not a C++ literal in this image

Frontend/state-tree **option names** (only condition *types* are in C++: `FrontEnd_CommandLineOptionExists`, `FrontEndFlow_DevOnlyCommandLineSetCondition`, …). `Game_IsRTM` body (XOR). `Misc_IsDevMode` `object+104` writer besides SimApp boot `0x18BA800`. Live PID 39056: Layer B line confirmed; nodbg byte lazy; IsDevMode byte=1 before overlay — [live-cli-c4sp3r](findings/2026-09-06-live-cli-c4sp3r.md).

---

# Dump corpus (same build, all Relic full dumps)

Fourth pass used only IDB `runtime_exe.i64` (PID 60644). Fifth pass compared every Relic PE copy and every full `.dmp` under `K:\aoe4_dlc\dumps` (plus `stk_v41` 42656). Inventory: `.cursor/rules/aoe4-dumps.mdc`. Session: [findings/2026-09-06-relic-cmdline-flags.md](findings/2026-09-06-relic-cmdline-flags.md).

| Check | Result |
|-------|--------|
| Build / SizeOfImage | **16.3.11308.0** / `0x8C3D000` on every dump that records version |
| Layer B `" -xxx"` in PE | same six: `nodbg` `notrap` `forcetrap` `wertest` `nonInteractiveMode` `notrace` |
| Extra Layer B in any full dump | **none** (` -dev` / ` -rtm` never appear as Layer B blobs) |
| `TestConfig_*` in Relic PE or Relic heap | **absent**. Overlay name-lists only |
| `Game_IsRTM` plaintext | PE 1 copy (0 xrefs). Heap SCAR table in every full dump except 13568/13632 (that PE page not captured) and 42656 (PE copy only) |
| Older IDB `7ff6f65c0000` | Downloads copy opened (`e83a5468`, base `0x7FF6F65C0000`, pe-sieve PID 16024). Same Layer B RVAs as 60644. Fewer functions (303k vs 535k). No extra flags. `K:\aoe4_dlc\7ff6f65c0000` is the larger sibling. |

Scanner: `AOE4HOOK/tools/scan_dumps_cli_needles.py`.

---

# Overlay (`DllInjector`) — do not mix with Steam

| Relic (Steam line) | Overlay (`DllInjector.exe`) |
|--------------------|-----------------------------|
| `-dev` | no injector flag — Steam only. Overlay Patch Game / `--patch-game` writes `-nodbg` **byte** `0x844B2ED` |
| `-nodbg` | Patch Game RUN `ForceNoDbg` writes RVA `0x844B2ED` once. Inject does not |
| `-notrap` | **no inject equivalent** — must be Steam |
| *(none)* | `--patch-game` / `--auto-patch` (оба пишут `auto_run=0`; AUTO выкл), `--watch` / `-w`, `--no-elevate` |

No `--bare` / `--dev` / `--ra-veh` / InjectBoot mapping. Relic `.text` neutralize stays **off**.

Recommended Steam line for stock x64dbg after HV hold (**offline / vs AI**):

```text
-dev -nodbg -notrap
```

Then `wait-hold`, then elevated `DllInjector.exe --patch-game` (`auto_run=0`), then **confirm** overlay Patch Game RUN (dangerous), then **stock** `x64dbg.exe`. Script: `AOE4HOOK/tools/Run-ProductDbgCycle.ps1`. Do **not** use `--ra-veh` with VS (INT3 conflict → `0xC000001D`). Do not `Start-X64dbgHidden.ps1` on the product path.

---

# Probe from SCAR

```lua
Debug_CmdLine("dev")          -- DebugHUD DCL
print(Misc_IsCommandLineOptionSet("dev"))
print(Misc_IsDevMode())
print(Util_GetCommandLineArgument("timer"))
```

Any string works — that is how you confirm an undocumented C++ token is on the line.

---

# RVA index (16.3.11308.0)

| Thing | RVA | VA in 60644 IDB |
|-------|-----|-----------------|
| `CommandLineToArgvW` ingest | `0x3AE9EC0` | `0x7FF7A8FE9EC0` |
| Table lookup | `0x3AF23B0` | `0x7FF7A8FF23B0` |
| Raw `GetCommandLineA` scan | `0x3C053E0` | `0x7FF7A91053E0` |
| `-argfile` | `0x3AF2670` | `0x7FF7A8FF2670` |
| Option table begin/end | `0x84D6B70` / `0x84D6B78` | `0x7FF7AD9D6B70` |
| Table-ready byte | `0x844B2EF` | `0x7FF7AD94B2EF` |
| `Misc_IsCommandLineOptionSet` | `0xBD9B20` | `0x7FF7A60D9B20` |
| `Misc_IsDevMode` | `0xBD9D40` | `0x7FF7A60D9D40` |
| `g_IsDevMode` byte | `0x84421BC` | `0x7FF7AD9421BC` |
| IsDevMode writer (SimApp boot) | `0x18BA800` | `0x7FF7A6DBA800` |
| `-nodbg` check | `0x3B77110` | `0x7FF7A9077110` |
| `-nodbg` flag | `0x844B2ED` | `0x7FF7AD94B2ED` |
| `-nodbg` parsed-once | `0x85A6C39` | `0x7FF7ADA6C39` |
| Trap init | `0x3C021F0` | `0x7FF7A91021F0` |
| OOM `NewHandler` | `0x3C054E0` | `0x7FF7A91054E0` |
| Crash-dialog (nonInteractive) | `0x3B72CE0` | `0x7FF7A9072CE0` |
| `-dev` hang-watch | `0x66BCE0` | `0x7FF7A5B6BCE0` |
| Hang worker / `logPageFaults` | `0x87D570` | `0x7FF7A5DCD570` |
| Autotest cache fn / byte | `0x3B61B70` / `0x86AD414` | `0x7FF7A9061B70` / `0x7FF7ADBAD414` |
| `-dev` / `-autotest` display sinks | `0x3B73180` | `0x7FF7A9073180` |
| Window mode | `0x8D0340` | `0x7FF7A5DD0340` |
| Bootflow skip | `0x3DC6DA0` | `0x7FF7A92C6DA0` |
| `-notrace` stack walk | `0x3AE7C80` | `0x7FF7A8FE7C80` |
| `-fakeDeviceType` | `0x3AEB3E0` | `0x7FF7A8FEB3E0` |
| `-nofx` / `-fxlog` | `0x17D5230` | `0x7FF7A6CD5230` |
| `-nopatchload` | `0x18A1240` | `0x7FF7A6DA1240` |
| Path overrides | `0x8B6A60` | `0x7FF7A5DB6A60` |
| Graphics autodetect | `0x8BEEC0` | `0x7FF7A5DBEEC0` |
| RR debug pack | `0x3729B80` | `0x7FF7A8C29B80` |
| Lua debugger socket | `0x37110B0` | `0x7FF7A8C110B0` |
| `-sync_high` AppInit | `0x866370` | (AppInit.cpp) |
| `-autotestmap` | `0xAA80A0` | ScriptedFrontEnd |
| `-wkdir` / `-userdir` | `0x3B76130` | `0x7FF7A9076130` |
| `-rlinkuserName` / `-rlinkpassword` | `0xA8BB60` | `0x7FF7A5F8BB60` |
| `-forceVsync` | `0x18B3C70` | `0x7FF7A6D13C70` |
| `-telemetrySession` | `0x7D26B0` | `0x7FF7A5CD26B0` |
| API host (`publicTest` / `force_*_server`) | `0x90B3A0` | `0x7FF7A5E0B3A0` |
| Memory-env flags | `0x8BC9C0` | `0x7FF7A5DBC9C0` |
| `-noSteam` / `-noWs` | `0x8C0310` | `0x7FF7A5DC0310` |
| RenderDoc / `d3dlog` | `0x3AE3200` | `0x7FF7A8FE3200` |
| Frame-time stats | `0x36BC280` | `0x7FF7A8BBC280` |
| Null device / render thread | `0x3618CC0` | `0x7FF7A8B18CC0` |
| Map-gen CLI | `0x82AB80` | `0x7FF7A5D2AB80` |
| `disable_map_unplayable_decorator` | `0x1D01F40` | `0x7FF7A7201F40` |
| PlayFab sandbox (`force_dev_sandbox_*`) | `0x8C6EF0` | `0x7FF7A5DC6EF0` |
| `-allow_multiple_instances` | `0x8B9E10` | `0x7FF7A5DB9E10` |
| `-nocheats` | `0x97AA80` | `0x7FF7A5E7AA80` |
| `-no_challenges` | `0xA700C0` | `0x7FF7A5F700C0` |
| `-allowallcrossplay` | `0xA7B650` | `0x7FF7A5F7B650` |
| `-nopatchdownload` | `0xABB510` | `0x7FF7A5FBB510` |
| `-casterMode` | `0x3DC2240` | `0x7FF7A92C2240` |
| `-hudrefresh` | `0x3DC7470` | `0x7FF7A92C7470` |
| `-noassert` | `0x3DCDA80` | `0x7FF7A92CDA80` |
| `-noTimeOutDetection` | `0x87D570` | `0x7FF7A5DCD570` |
| `-disableRacePrecaching` | `0x3D08B0` | `0x7FF7A58D08B0` |
| `-allowIncompatibleReplays` | `0x8709B0` | `0x7FF7A5D709B0` |
| Scripted slots (`maxslots` / `teamslotN`) | `0x829ED0` | `0x7FF7A5D29ED0` |
| `-no_multithreaded_sim` | `0x8D76B0` | `0x7FF7A5DD76B0` |
| `-no_multithreaded_ai` | `0x291A1A0` | `0x7FF7A7E1A1A0` |
| `-filelog` | `0x8BC510` | `0x7FF7A5DBC510` |
| `-disableLuaDebug` | `0x8BFD50` | `0x7FF7A5DBFD50` |
| `-map_gen_debug` | `0x18E99D0` | `0x7FF7A6DE99D0` |

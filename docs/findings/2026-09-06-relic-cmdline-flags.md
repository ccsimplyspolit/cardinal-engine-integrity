# 2026-09-06 Relic command-line flags

IDB `runtime_exe.i64` (60644, imagebase `0x7FF7A5500000`). Durable catalog: [RELIC_COMMAND_LINE.md](../RELIC_COMMAND_LINE.md).

## Parser (two layers)

1. **Table** — `GetCommandLineW` + `CommandLineToArgvW` RVA `0x3AE9EC0`. 72-byte rows at `0x84D6B70`. Lookup `_stricmp` `0x3AF23B0`. `Misc_IsCommandLineOptionSet` `0xBD9B20` strips leading `-`. **No whitelist** — any `-name` is stored.
2. **Early strstr** — exact blobs with leading space: ` -nodbg` ` -notrap` ` -forcetrap` ` -wertest` ` -nonInteractiveMode` ` -notrace`. Must be on Steam line (space from `exe -flag`).

`" -dev"` **does not exist**. `-dev` is Layer A name `"dev"` (`0x7FF7AB7858BC`).

## `-dev` C++

| RVA | Effect |
|-----|--------|
| `0x66BCE0` | hang-watch object `+0x2D0`: `0x0100` vs `0x0101` |
| `0x3B73180` | if not `-autotest`, copy dev window table `unk_7FF7ACC85600` into `0xE20` display object; also `exclusive_fullscreen` |

Does **not** write `g_IsDevMode` `0x84421BC`. `Misc_IsDevMode` (`0xBD9D40`) is a separate byte. File helpers `0x7FF7A8C46040` / `6620` / `6820` gate on that byte only.

## Layer B (already in UPDATE_GUIDE)

| Token | Site |
|-------|------|
| ` -nodbg` | `0x3B77110` → byte `0x844B2ED`, once `0x85A6C39` |
| ` -notrap` / ` -forcetrap` / ` -wertest` | trap init `0x3C021F0` |
| ` -nonInteractiveMode` | same + AppInit MessageBox skip |

## Other C++ names pulled from `_stricmp` / strings

`argfile`, `autotest`, `autotestmap`, `sync_high`, `sync_high_memory`, `notrace`, `dont_skip_bootflow`, `start_scenario`, `load_game`, `replay`, `fakeDeviceType`, `DXDebugDevice`, `exclusive_fullscreen`, `RRStateTracking*` / `RRGPUTimer` / `RRSendTelemetry` / `RRBreakOnLoadFail`.

`Game_IsCommandLineOptionSet` string has **0 xrefs**.

## SCAR

All `Misc_IsCommandLineOptionSet("…")` literals in `sdk/scar/sga` listed in the catalog (`cheat`, `no_fow`, `no_units`, `no_gaia`, `debug`, `timer`, `missioncheat`, intel/training/rogue keys).

## Deep dive (same day, second pass)

Decompiled every unique Layer A lookup caller and every Layer B consumer. Catalog rewritten: [RELIC_COMMAND_LINE.md](../RELIC_COMMAND_LINE.md).

### Confirmed writes

| Byte / word | Who writes | Not written by |
|-------------|------------|----------------|
| `g_IsDevMode` `0x84421BC` | SimApp boot `0x18BA800` from `*(object+104)` | **not** `-dev` |
| `g_Dev_NoDbgFlag` `0x844B2ED` | `Dev_NoDbg_Check` on first call; overlay `DevForceNoDbg` | |
| hang `app+720` | `0x66BCE0`: `0x0101` if `-dev` or `-autotest`, else `0x0100` | |
| display `object+3568` | `0x3B73180`: 1 if `-dev` or `-autotest` | |
| trap object `off_7FF7AD949D10` | `0x3C021F0`: real / no-op / WER-test vtable | inject cannot undo |

### Dead / unused in this function

`exclusive_fullscreen` lookup at the **tail** of `0x3B73180` is discarded (`return 1`). Real handler is window boot `0x8D0340`.

Bootflow predicate is RVA **`0x3DC6DA0`** (was listed as `0x3D76DA0` — typo). Logic: `dont_skip_bootflow` forces FE; `start_scenario` / `load_game` / `replay` / `autotest` skip.

### Window mode ints (`0x8D0340`)

`exclusive_fullscreen=1`, `fullwindow=0`, `window=2`, `full_desktop=3`. Then `AllowResize` (style 31 vs 30), `window_x/y` + negatives, `width`/`height`.

### `fakeDeviceType` allow-list

`PC`, `XboxOne`, `XboxOneS`, `XboxOneX`, `XboxOneXDevkit`, `XboxScarlettLockhart`, `XboxScarlettAnaconda`, `XboxScarlettDevkit`, `XboxSeriesS`, `XboxSeriesX`, `Playstation5`, `PCHandHeld`, `SteamDeck`. Else log and keep real device.

### New Layer A names this pass

`nofx`, `fxlog`, `nopatchload`, `logPageFaults`, `logfiles`, `screenshots`, `userdata`, `log`, `hd`, `configtest`, `nographicsautodetect`, `forcesettingsgroup`, `width`, `height`, `window`, `fullwindow`, `full_desktop`, `AllowResize`, `window_x`, `window_y`, `window_x_negative`, `window_y_negative`, `freemouse`, `lockedmouse`, `lua_debugger_port`, `luaconfig`, `showdebugsettings`, `invbatchingoff`, `no_ai_matchheartbeat`, `MoviePlayerPixelCount`.

### Still open

~200 `GetCommandLineA` xrefs include generic helpers whose **name** comes from a state tree / Lua string, not a C++ literal. Probe those with `Misc_IsCommandLineOptionSet`. Did not step live PID 60644 (dump/IDB only).

## Third pass (same day) — user was right, catalog was incomplete

`GetCommandLineA` = **490 xrefs, 182 unique functions**. First two passes only decompiled the unique `_stricmp` lookup callers (~25). The other ~157 are the inlined “table ready? else `GetCommandLineA` + raw scan” pattern — each is a real Layer A consumer.

### Method

1. Dumped unique `GetCommandLineA` functions from xref JSON.
2. `analyze_batch` `include_strings` (no decompile) on high-xref + first ~50 remaining.
3. Cross-checked SCAR bags for `Util_GetCommandLineArgument` / `Misc_IsCommandLineOptionSet` literals the catalog skipped (`speed*`, `CampaignAutoTest`, Cyprus/Tyre, `fullscreen_nis`, `rogue_stress_test`, POI `.name` keys).
4. `Game_IsRTM` string `0x7FF7ACCA2961` has **0 xrefs** (XOR). `AI_IsRTM` is XOR-decoded in `0x7FF7A7E9BB70`. C++ `"rtm"` at `0x7FF7ABAEDE18` is a telemetry/build-channel label, **not** the CLI handler. `TestConfig_*` strings are **absent** from this image.

### New C++ Layer A names

`wkdir`, `userdir`, `rlinkuserName`, `rlinkpassword`, `telemetrySession`, `forceVsync`, `memEnvConfig`, `verifyCopyOnDirty`, `relocateSimPools`, `protectUnusedMemory`, `trackTemporaryAllocationCallstacks`, `noMemoryProtection`, `publicTest`, `force_test_server`, `force_live_server`, `noSteam`, `noWs`, `nulldevice`, `enable_render_thread`, `disable_render_thread`, `loadrenderdoc`, `d3dlog`, `frame_time_stats`, `frame_time_stat_graph`, `frame_times_exit_on_fixed`, `frame_time_fixed_samples`, `singlethreaded_presentation`, `animsystem_singlethreaded`, `nophysicsthreads`, `hkingamedebugger`, `hkdebugger`, `singlethreaded_ee_model`, `disable_threading_mode_task_helping`, `multithread_ai_sim_if_workers_available_enabled`, `no_parallel_entity_trees`, `no_parallel_deferred_entity_trees`, `no_parallel_physical_trees`, `no_entity_tree_readonly_validation`, `pressanykey`, `startpaused`, `ageUpPrecache`, `scarWarnings`, `disable_async_scenario_loading`, `nospeech`, `replayvalidation`, `mod`, `noscarreport`, `dataPreview`, `archivePreview`, `force_remote_desktop`, `ignore_remote_desktop`, `map_gen_biome`, `map_gen_size`, `closeStarts`, `scenario_difficulty`, `force_real_match`, `disable_map_unplayable_decorator`, `perftest`, `no_nfx`, `warning_as_assert_AI`, `xbox_live_links_count`, `noCloudSaves`.

### New SCAR names

`speed`, `build_speed`, `repair_speed`, `gather_speed`, `upgrade_speed`, `production_speed`, `CampaignAutoTest`, `NoSwoopy`, `CaptureLimassol`, `DestroyFamagusta`, `DestroyKyrenia`, `AccelerateEnemyAttacks`, `SkipFranksGathering`, `SkipEconPhase`, `SkipArmyCountdown`, `fullscreen_nis`, `rogue_stress_test`, plus every `rogue_poi.scar` `.name` as a force-spawn key.

### Still open after third pass

- ~130 unique `GetCommandLineA` functions still unharvested (string pass not finished).
- `Game_IsRTM` C++ body (XOR native; no plaintext `"rtm"` lookup).
- Frontend/state-tree option **names** in bags (condition types are known; the tokens they query are data).
- `Misc_IsDevMode` `object+104` writer beyond SimApp boot.
- Live PID verify (dump/IDB only).

## Fourth pass (same day) — complete dump + binary

User: harvest **everything**. Session `a1220dbc`, IDB `runtime_exe.i64`, imagebase `0x7FF7A5500000`.

### Coverage

| Source | Count | Outcome |
|--------|-------|---------|
| `GetCommandLineA` xrefs | 490 / **182 unique fns** | strings harvested from **all 182** |
| `GetCommandLineW` | 4 / 2 fns | ingest only |
| Layer B `" -xxx"` | 6 strings | unchanged (`nodbg` `notrap` `forcetrap` `wertest` `nonInteractiveMode` `notrace`) |
| Lookup `0x3AF23B0` extra (no GCLA) | gfx / LuaDbg / VSync / RelicLink / wkdir / fakeDevice | re-harvested; no new names |
| Prefix regex `no_`/`force_`/`…` | 123 strings | most are bag attributes, not CLI |
| SCAR `Misc_*` / `Util_GetCommandLineArgument` | full sga | no new literals beyond pass 3 |
| `sdk/lua` besides DebugHUD | 0 CLI consumers | |

### New C++ tokens (see catalog § Fourth pass)

`allow_multiple_instances` (mutex skip, decompiled), `nocheats` (kills Cheat Menu / Ctrl+Shift+3, decompiled), `no_challenges`, `allowallcrossplay` (decompiled), `nopatchdownload` (decompiled), `casterMode` (FE string +72 vs +56, decompiled), `hudrefresh` (bool predicate, decompiled), `noassert`, `noTimeOutDetection`, `debugwindow`, `disableRacePrecaching`, `precacheAllAges`, `allowIncompatibleReplays`, `show_all_replay`, `ReplayDesyncTest`, `maxslots`/`teamslotN`/`teamraceN`/`aidifficultyN`, `disableCPUextensions`, `nofonts`, `filelog`, `disableLuaDebug`, `no_multithreaded_sim`, `no_multithreaded_ai`, `force_dev_sandbox_1`–`5` (`0x8C6EF0` → `age4-dev0N`), `map_gen_debug` / `map_gen_test_layout` / `map_gen_debug_scoremap`, `loadAllFX` / `loadAllSkins` / `fxloadimmediate`, `autoskipvideos`, `noreflections`, `noBackgroundLoading`, `noStampSplats`/`noStampStrips`, `MinimapCapture`, `DecalBakeCapture`, `disableminimap`, `pointShadowSize`, `noShadowNormalBias`, `singleshadowcascade`, `mipdb`, `force_inactive_dxdevice`, `ideal_frame_rate`, `audioignorefocusloss`, `logTelemetry`, `entitylog`, `debugTail`, `pathlogs`, `noextrasync`, `memorystats`, `noRepeatedLogMessages`, `useAllInputDevices`, `AllowTransitionalInput`, `autoGroupsEnabled`, `window_title`, `localautotest`, `chat_cue`, `showDistricts`, `showDefaultFocusStyle`, `showpersistentperformancecounter`, `debug_relic_radial_menu`, `debug_kickers`, `formationDisabled`, `disable_root_motion`, `disable_root_component_merge`, `ignorePrecacheDenylist`, `warning_as_assert_precache`, `warning_as_assert_statetree`, `disable_hk_license_warning`, `disable_threading_mode_dynamic_updates`, `noAIResourceMultiplier`, `use_pending_combat_fitness_data`, `navigation_drive_directly_to_goal`, `precacheSoundBanksAll`, `memorybudget`, `VPXDisableAlpha`, `use_legacy_presentation_serialization`, `ReflectResetAbstractObjectsToDefault`, plus RR/DX extras (`NVAftermath*`, `DXDRED*`, `DXWarpDevice`, `DXGpuBasedValidation`, …) in `0x3729B80`.

`nosteam` == `noSteam` (`_stricmp`).

### Closed vs still open

**Closed:** the ~130 unharvested GCLA functions. Layer B set is complete (6). GetCommandLineW has no extra flags.

**Still open:** `Game_IsRTM` C++ body (XOR, 0 xrefs on plaintext). Frontend bag option **names**. `object+104` besides SimApp boot. Live PID.

## Fifth pass (same day) — all dumps, not only 60644 IDB

User: we had not checked the other dumps. Correct. Fourth pass was IDB `runtime_exe.i64` only.

### What exists on disk (was missing from the short dump table)

Same build **16.3.11308.0**, SizeOfImage `0x8C3D000`. Inventory now in `.cursor/rules/aoe4-dumps.mdc`. Extra full dumps beyond the old six-row table: 19944, 26392 sdkpack `.dmp`, 37716, 40392, 13568, 13632, `stk_v41` 42656. `28496` folder still empty; `hh\RelicCardinal.DMP` cited by the 18816 manifest is **gone**. Older IDB `K:\aoe4_dlc\7ff6f65c0000.RelicCardinal.exe.i64` not re-opened (26392 `.bin` is that pe-sieve image).

### PE copies (hash differs — relocs applied; strings do not)

| Image | Layer B six | `TestConfig` | `Game_IsRTM` |
|-------|-------------|--------------|--------------|
| 60644 `modules_runtime\RelicCardinal.exe` | yes | 0 | 1 |
| 60644 `RelicCardinal.exe.memory.bin` | yes | 0 | 1 |
| 26392 `011254` `.bin` | yes | 0 | 1 |
| 26392 `011146` `.bin` | yes (+ spurious ` -Wb`) | 0 | 1 |

Naive ` -[A-Za-z]…` also hits OpenSSL `-DSHA1_ASM`, ` -DXDebugDevice` / ` -autotestmap` / ` -height` / ` -sync_high` (known Layer A with a leading space in a format string), and `bottomPrince` at `0x7FF7AB013EA0` (**0 xrefs** — word-list / HTML corpus, not CLI).

### Full-dump needles (file offsets, not VAs)

| Dump | Layer B each | ` -dev`/` -rtm` | `TestConfig` ASCII | `Game_IsRTM` | Notes |
|------|--------------|-----------------|--------------------|--------------|-------|
| 60644 10.5 GiB | 2 | 0 | 12 | 9 | extra 6 `TestConfig` = overlay `TestConfig_LoadFromCommandLine` + `AOE4HOOK_TRUST` |
| 18816 6.1 GiB | 2 | 0 | 6 | 6 | `TestConfig` = `Bamo*HitTestConfiguration` only |
| 18816 redump 4.1 GiB | 2 | 0 | 6 | 7 | same |
| 19944 8.4 GiB | 2 | 0 | 6 | 9 | same |
| 26392 sdkpack 7.8 GiB | 2 | 0 | 6 | 17 | same; `Misc_*` 301 (overlay/STK strings) |
| 53820 6.7 GiB | 2 | 0 | 6 | 9 | same |
| 37716 6.2 GiB | 2 | 0 | 6 | 15 | same |
| 40392 7.4 GiB | 2 | 0 | 6 | 18 | same |
| 13568 3.8 GiB | 2 | 0 | 6 | **0** | smaller dump; `Game_IsRTM` PE page not in file. `Game_IsCommandLineOptionSet` still 2 |
| 13632 4.0 GiB | 2 | 0 | 6 | **0** | same session as 13568 |
| 42656 (stk) 5.7 GiB | 2 | 0 | 6 | 1 | PE copy only (no extra SCAR heap table) |
| `hh\RelicCardinal.DMP` (28496) | — | — | — | — | **file gone** |

60644 `TestConfig_*` heap blob is the overlay native-name list (`Terrain_CreateSplat` … `TestConfig_LoadFromCommandLine` … then `AOE4HOOK_TRUST` / `scar_natives_live.scar`). It is **not** Relic decoding a stripped registrar. Every other dump has `TestConfig` count 6 = Bamo `HitTestConfiguration` only.

`Game_IsRTM` / `Game_IsCommandLineOptionSet` appear in Relic SCAR string tables in heap (next to `Game_QuitApp`, `campaign_debug`) with **0 PE xrefs** — XOR names, already catalogued. 13568/13632 missing `Game_IsRTM` is dump coverage, not a different binary.

Scanner: `AOE4HOOK/tools/scan_dumps_cli_needles.py`. **No extra Layer B token in any dump.** No new Steam flag. No inject equivalent for `-notrap`. Live PID still not stepped.

### Downloads `7ff6f65c0000` IDB — same image, less analysis

`C:\Users\sshunko\Downloads\sshunkogram Desktop\7ff6f65c0000.RelicCardinal.exe.i64` (1 813 605 874, SHA256 `DBB7B620…`, 2026-09-06 20:43). **Not** a copy of `K:\aoe4_dlc\7ff6f65c0000…` (2.49 GB, SHA256 `A3E012C3…`) and **not** 60644 `runtime_exe.i64`.

Opened MCP session `e83a5468` (no auto-analysis). Imagebase `0x7FF6F65C0000`. IDA `input_path` = `C:\Users\dm\Desktop\pe-sieve\dumps\process_16024\7ff6f65c0000.RelicCardinal.exe`. Closed without save.

| | Downloads 7ff6 | 60644 `runtime_exe` |
|--|----------------|---------------------|
| SizeOfImage / segments | same `.text` `0x56DD000` … `.rodata` `0x1000` | `0x8C3D000` (survey reports this) |
| Functions / named | 303 458 / 4 424 | 534 587 / 10 442 (+ 46 469 FLIRT) |
| ` -nodbg` RVA | `0x65EEC08` | `0x65EEC08` |
| `Game_IsRTM` RVA | `0x77A2961` | `0x77A2961` |
| `allow_multiple_instances` RVA | `0x62979F8` | `0x62979F8` |
| Layer B six / ` -dev` / ` -rtm` / `TestConfig` | 6 / 0 / 0 / 0 | same |

No extra CLI tokens. Prefer 60644 IDB (more functions, FLIRT, strings cache). `K:\aoe4_dlc\7ff6f65c0000` is the larger sibling of this pe-sieve family. **Never mix VAs** with 60644.

### C4SP3R zip — does not help CLI

`C:\Users\sshunko\Downloads\AoE4 Functions by C4SP3R_[unknowncheats.me]_(2).zip` (45 564, 2026-08-28): **one PE**, `AoE4 Functions by C4SP3R.exe` (100 864). No function list, no flag table. Static strings (already in [game-folder-unpack](2026-09-06-game-folder-unpack.md)): `scardocs\html\function_list.htm`, `RelicCardinal.ex`, `OpenProcess` / `ReadProcessMemory` / `NtSuspendProcess`. Same class as `ScarNativesDump` — live name scrape. We already have Steam scardocs + `sdk/scar` INDEX / `_meta.lua` / checksum wrappers. Static pass only (2026-09-06). User later authorized running it (`user-owned-tools.mdc`). Still does not add Layer A/B tokens or `TestConfig` C++ handlers — name scrape of scardocs + RPM.

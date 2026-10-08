# 2026-09-07 — Overlay paths that still need Relic SCAR/Lua

Inventory of **InternalInjector** (`AOE4HOOK/internal/InternalInjector`). No `_arhive`. Complements [native-ai-cpp](2026-09-07-native-ai-cpp.md) and [leave-scar](2026-09-07-leave-scar.md): think is already C++; this lists every remaining DoString / Relic-Lua surface.

Replace codes: **(a)** C++ RPM/write known fields **(b)** documented inner RVA on window/AI thread **(c)** SendInput **(d)** drop the feature.

Why: **hook** = Relic calls Lua back (scoring / EventRule / TimeRule). **oneshot** = overlay posts natives once. **user** = Files AUTO / Run. **bus** = C++ assigns `_G` for other Lua.

Risk: **TLS AV** (wrong thread / ScarHelper 0xB7F150). **OOS** (sim write vs humans). **RA** (DoString during load, DualFlag, fogByte poke). **4A70** (`AI_LockSquad` while Relic think holds tactics).

Entry: `Game_ScarDoString` RVA `0xAA9B00` (`scar.cpp` `ScarDoStringSeh`). Window thread only (`ScarExecuteOnWindowThread`). Lean skips `local_rules`+checksum. Helper CRT is dead for overlay-owned AI/locks.

## Product plumbing (not a feature)

| Path | File:fn | Why | Replace | Risk |
|---|---|---|---|---|
| DoString + WM_SCAR_EXECUTE | `scar.cpp:ScarExecuteOnWindowThread` 2512, `ScarHandleWindowMessage` 2499 | oneshot transport | keep; (b) only if each inner is queued on Relic tid | TLS if Present; RA if load |
| Quiet VM probe | `scar.cpp:ScarEnsureVmProbed` 2385 | oneshot `World_GetGameTime` type-check | (d) if first lean AI proves VM | RA if MapGen |
| Bootstrap prepend | `scar.cpp:ComposeOverlayScar` 2039 | user wrap: trust + `local_rules` + checksum | keep for Files; lean AI already skips | OOS if wrap Rule_* vs humans |
| TimeRule pump | `scar.cpp:ScarPumpLocalRules` 2619, `ScarLocalRuleService` 2630 | hook: overlay `AOE4HOOK_Local.Pump` for hybrid/Files timers | (d) if no Files/hybrid; else keep | hitch (~40ms DoString) |
| CRT helper | `scar.cpp:ScarExecuteHelperThread` 2537 | Files launch mode 2; D02C skip / AV | (d) overlay AI already window-thread | TLS AV 0xB7F150 |

## Files tab — SCAR by design (stay if AI BOT goes native)

`Documents\AOE4HSettings\Scar Scripts\` + `Lua Scripts\`. Overlay does **not** auto-run; AUTO is per-row.

| Path | File:fn | Why | Replace | Risk |
|---|---|---|---|---|
| Execute / Reload | `ui.cpp:LoadListedScript` 1988, `ExecuteManagedScript` 1637 | **user** | none — product | OOS if script writes sim; RA CRT mode |
| AUTO at match start | `ui.cpp:ServiceMatchAutoload` 5178 | **user** once per match | none | same; 2s startconditions gate |
| Injector editor | `ui_scripts.cpp:DrawScriptsInjectorEditor` 1287 | **user** buffer | none | trust catalog |
| dofile overlay path | `ui.cpp:LoadOverlayDofile` 2133 | **user** `.scar` under AOE4HSettings | none | path jail |
| Launch Direct/File/CRT | `ui.cpp:g_scriptLaunchMode` 148 | **user** VM entry | CRT=(d) | CRT TLS |
| System prepend | `local_rules.scar` / `checksum_wrappers.scar` via Compose | **user** infra | keep for Files Rule_* | wrapping Relic Rule_* = checksum if not Local |

Hidden from Files (still product SCAR, not Files-tab rows): `_system\_auto` hybrids, `_system\_menu` Online/Offline. User copies of those names in Scar Scripts still Run/AUTO.

Seeded Lua that Files can Run: `eco_upgrades.lua`, `warmonger.lua`, `risky_econ.lua`, `DebugHUD.lua` (`docs_layout.cpp` 741).

## Hybrid AUTO

| Path | File:fn | Why | Replace | Risk |
|---|---|---|---|---|
| hybrid_o_* + core | `ui.cpp:LoadListedScript` 2015 (prepend `hybrid_core` + `AOE4HOOK_AI_SETTINGS`) | **user** director: TimeRules + natives; Relic train still Layer A | (d) if C++ BOT owns eco (`AOE4HOOK_ECO_CPP`); else Files stay | OOS vs humans; hitch OwnedList if flag off |
| hybrid_c | same; never with hybrid_o | **user** old director | (d) or keep vs AI | OOS |
| Profile AUTO toggle | `ai_builder.cpp` ~1265 | **user** | none | — |
| Settings bus | `ui_scar_lanes.cpp:PushOverlaySettingsLua` 28 | **bus** `_G` | (a) unused if no hybrid | — |

When C++ BOT is on, hybrid must skip Layer A/B (`cppOwns*`). Hybrid without BOT still needs SCAR.

## World-feed / NativeEsp / TWD

| Path | File:fn | Why | Replace | Risk |
|---|---|---|---|---|
| Send Data to Scar | `radar.cpp:FormatScarSnapshot` 8941, `PublishScarSnapshot` 9438, `RadarScarBridgeTick` 11767, `WM_SCAR_WORLD_PUBLISH` | **bus** `_G.AOE4HOOK_WORLD_DATA` for SWM/hybrid | (d) if no Lua consumers; C++ radar already has the cache | hitch 48–52ms compile; RA if load |
| World filter TTL | `scar.cpp:ScarPublishWorldFilter` 3330 | **bus** | (d) with feed | — |
| NativeEsp bootstrap | `ui.cpp:BootstrapSpatialModel` 1882 (`scar_natives_live`, `unit_intelligence`, hook bridge, `spatial_world_model`) | **user/hook** Lua world model | (d) if Files/hybrid gone | TLS if not window |
| twd.scar rings | `radar.cpp:RadarPublishTwdScarMode` 11676 | **hook** `TWD_Tick` + **bus** `AOE4HOOK_TWD_WORLD` | (a)/(d) overlay ESP already draws; native mode is Lua | hitch |
| AI_LOCK flags | `toolkit_slabs.cpp:PublishAiLock` 135 | **bus** for hybrid Memory flags | (d) if no hybrid | — |

ESP/radar FoW bits are **C++** sight disks (`radar.cpp` ~4305), not SCAR.

## Probe / Dump VM / Debug HUD

| Path | File:fn | Why | Replace | Risk |
|---|---|---|---|---|
| probe.scar AUTO/Run | `ui_scar_lanes.cpp:DrawProbeTab` 892; `ui.cpp` `g_probeAuto` 246; fallback `scar.cpp:ScarKickProbe` 3859 (API unused by UI) | **user** + **hook** (`Rule_Add` spawn census). Read-only | keep as Files/Online diagnostic; (d) ranked | RA if AUTO in ranked (policy: don't) |
| dump_vm.scar | `ui_scar_lanes.cpp:DrawDumpVmPane` 169; `sdk_dump.cpp` ~993 | **user** VM census | (a) dump_vm is Lua `_G` walk — keep or (d) | hitch; don't AUTO |
| Load DebugHUD.lua | `ui_scar_lanes.cpp:DrawDebugHudPane` 192 | **user** XAML console | (d) overlay ImGui HUD | Relic UI |
| Show/Hide/Search/Call | `scar.cpp:ScarShowDebugHud` 3470 … `ScarDebugCall` 3515 | **oneshot** Relic `ShowDebugHUD` / `Debug_*` | (d) | Debug_FOWReveal = FOW+OOS |
| Retire old XAML HUD | `ui.cpp:UiRetireScarObserverHud` 5159; `hud_alerts.cpp:HudAlertsRetireScarXaml` 744 | oneshot cleanup | (d) after one match | — |

## AI BOT (still SCAR actuators)

Think is C++ (`ai_runtime` / `ai_production`). Relic still TRAINs via Layer A.

| Path | File:fn | Why | Replace | Risk |
|---|---|---|---|---|
| Enable sequence | `ai_session.cpp:AiSessionService` 2476, `BuildEnableScript` 145, `HelperRun` `eco_ai_on` 2519 | **oneshot** `AI_Enable` / `AI_SetDifficulty` / `Game_EnableInput` / park contest tick | (a) poke `AI+0x12F4` is empty without slot; (b) inner `0x2975660` on **AI tid** | OOS; RA; **4A70** if lock after Enable |
| Standing army lock | `stk_lua_lock.cpp:StkLuaLockSetArmy` 1533 (`kArmyOn`, `kEnsureAiSlot`) | **oneshot** `AI_LockSquad` combat; skip vill | (b) `AI_LockSquad` `0x296D2E0` on AI/window tid **before** Enable | **4A70** after Enable; 4CE0 if no track |
| Villager lock (optional STK) | `StkLuaLockSetVillagers` 1578; hotkeys `HotkeysSetScarLockVillagers` 556 | **oneshot** + spawn **hook** | (d) BOT wants vills unlocked | **4A70** if lock after Enable |
| Spawn watch / EventRule fallback | `stk_lua_lock.cpp` `kArmRelicSpawn` 1063, `FireEntityIds` 1644, cache-spawn ~1675 | **hook** `GE_EntitySpawn` if cache empty | (a) C++ cache-spawn already preferred | EventRule hitch |
| Army relock | `StkLuaLockHandleArmyRelock` 2053, `WM_SCAR_ARMY_RELOCK` | **oneshot** unique spawns | (b) same LockSquad inner | **4A70** |
| Skip-map publish | `StkLuaLockHandleSkipPublish` 2039 | **bus** tactic-skip ids | (a) if lock is C++ | — |
| Relic kick / monk | `ai_lock_relic_*` HelperRun 1227–1525 | **oneshot** LocalCommand / lock | (c) micro; (b) command inner | 4A70 / OOS |
| Group / garrison / sel-lock | `StkGroupLockOnAssign` 2186, `StkGarrisonLock*` 2652, `StkSelLock*` 3101 | **oneshot** LockSquad on selection | (c) for player orders; (b) lock inner | **4A70** sel-lock skip live tactics |
| Opening gather | `kEcoOpen` 878, `eco_ai_open` 2523 | **oneshot** `LocalCommand_SquadSquad/Entity` | (b) command inners on window tid; (c) click gather | OOS; sheep must be SquadSquad |
| Eco contest | `RunEcoContest` 2075, `WM_SCAR_ECO_CONTEST` 2123 | **oneshot** gather jobs from C++ list | same as open | OOS |
| Scoring install | `InjectEcoScoring` 860, `kEcoScoring` 187; duplicate installer `ai_runtime.cpp` ~533 | **hook** Relic calls `ScoringFunctions_*` per candidate | **cannot (a)**; (b) would reimplement Relic multiply/Evaluate ABI; overlay already O(1) LuaScoring | OOS vs humans (`scar_trust`); LuaScoring must stay O(1) |
| Actuator apply | `HandleAiCommitPosted` 1251, `AiRuntimePeekActuatorScript`; `__EcoAct_Apply` `ai_runtime.cpp` 487 | **oneshot** availability / Layer B natives | (b) `Player_SetSquadProductionAvailability` + desire inners on AI tid | OOS; SEH parks actuator |
| Farm ring | `AiFarmLayoutAppendPending` via same commit | **oneshot** place farms | (b) build command; (c) | OOS |
| Handover | `kHandover` 1066, `RunHandover` 2204 | **oneshot** UnlockAll + restore ticks | (b) unlock inner | leftover `AOE4HOOK_ECO_CPP` gates hybrid |
| Fine-tune UI | `scar.cpp:ScarApplyAiTune` 2739; `ui_scripts.cpp:AiCustomPushLive` 260 | **oneshot** Layer B/C | (b) on AI tid; bag reload invalidates Layer B | TLS if Present; OOS |
| Enable AI (Fine-tune pane) | `ui_scripts.cpp` `ScarTakeAiControl` 446; STK Lua pane `ui_scar_lanes.cpp` 359 | **oneshot** duplicate of session | prefer session; (d) duplicate UI | OOS; no `Game_AIControlLocalPlayer` from overlay |
| Memory AICTLR01 | `DrawAiMemoryPane` 304 | **not SCAR** (slab bytes); only `PublishAiLock` bus | (a) already | — |
| Scoring Lua profiles | `ai_builder.cpp` Load `warmonger.lua`/`risky_econ.lua` ~316 | **user hook** overwrite `ScoringFunctions_*` | Files stay; BOT uses `kEcoScoring` | OOS |
| Plan bus (unarmed only) | `PublishPlan` 2138 `eco_ai_plan` | **bus** `AOE4HOOK_AI_PLAN` | (d) while `AiRuntimeArmed`; world-feed owns SWM | hitch |

`eco_contest_scar.h` `kEcoContest` is **dead** (no C++ include). Live contest is C++ `BuildEcoContestScript`.

## Offline spawn / cheats (vs AI)

`stk_feature.cpp:StkRun` 114 + `stk_embedded.cpp` `kStkEmb[]` 2670. UI: `ui_scar_lanes.cpp:DrawOfflineAiTab` 915. Files Execute of these names is **retired** (`ui.cpp:RetiredOverlayScarName` 1108) — Offline menu still runs embedded bodies.

| Path | File:fn | Why | Replace | Risk |
|---|---|---|---|---|
| spawn.scar | `FireStkSpawn` 123 / StkPcall | **oneshot** `Squad_CreateAndSpawnToward` | (d) vs humans; (b) spawn inner vs AI | OOS; RA |
| grant_res / allies | StkPcall ~1013 | **oneshot** `Player_SetResource` | (a) resource fields if known; else (b) | OOS |
| combat_mods / invuln / rates / instant_* / age_up / convert / kill / jeanne / sheep_wolves / save_match | same pane | **oneshot** sim_write | (d) ranked; keep vs AI | OOS |
| auto_queue / auto_heal / sheep_herder / universal_micro | StkPcall + **hook** ticks | Relic TimeRule/select loop | (c) for micro; (d) vs humans | OOS |
| cheat_fow.scar | StkPcall 1234 | **oneshot** sim FoW wrap | Full Reveal is already **(a)** FOWCTRL1; this is sim | OOS vs AI too |
| debug_shots campaign | StkPcall 1272 | **oneshot** | (d) | — |
| Sim rate | `ScarSimRate*` 3583 | **oneshot** `Misc_SetSimRate` | (b) | OOS |
| Hide UI / music / scores / colour | `ScarHideUiExceptChat` 3439, `ScarShowNativeScores` 3348, `ScarSetLocalPlayerColour` 3408 | **oneshot** UI natives | (d) or keep | scores uses Local.AddInterval not Relic TimeRule |
| Camera input | `ScarSetCameraInput` 2924; AUTO `g_aiAutoCamera` | **oneshot** `Game_EnableInput` | (b) | — |
| PlayBeginOfMatch | `ScarPlayBeginOfMatch` 3311; AUTO `g_aiAutoMatch` | **oneshot** named `_G` | (d) | — |
| Player hints ping | `ScarPingPlayerHints` 3533; `hud_alerts.cpp` 733 | **oneshot** HintPoint | overlay ESP (d) | `Rule_AddOneShot` 8s |

## FOW via SCAR (product Full Reveal is **not** this)

| Path | File:fn | Why | Replace | Risk |
|---|---|---|---|---|
| Full Reveal hold | `engine.cpp` FOWCTRL1+8 VEH; `DrawScriptsFogPane` 1202 | **C++** — no SCAR | already (a) | RA if fogByte poke (`EngineSetScarFowHold` 2880 **refused**) |
| Reveal Map (Memory) | `maphack_fowctrl.cpp` + `ScarRevealMapMemoryShot` 3140 → `BuildRevealMapOneShotScript` | **oneshot** `FOW_UIRevealAll_Transition` + type-guarded `FOW_UIRevealAll` + orig `FOW_PlayerExploreAll(player)` | (a) FOWCTRL1+11 already pulsed; SCAR combo still used | OOS vs humans (blocked); RA |
| Relic blips | `ScarSetMaphackRelicBlips` 3010; `engine.cpp` 2713 | **oneshot** `UI_CreateMinimapBlipOnPosFrom` | overlay radar (d)/(a) | UI only |
| Hide reveal-map | `ScarRevealMapHide` 3144 | **oneshot** UnExploreAll | (a) | — |
| Hide FOW on Full Reveal off | `engine.cpp` 2836 `ScarSetFogReveal(false)` | **oneshot** UnReveal entities | (a) VEH off may suffice | — |
| Debug HUD FOW button | `ScarDebugCall("Debug_FOWReveal")` 250 | **oneshot** Relic debug | (d) | OOS |
| **Dead APIs** (no callers) | `ScarHoldFogEntities` 2992, `ScarSetFogFullReveal` 3160, `ScarRunFowNative` 3224, `ScarKickProbe` 3859 | leftover | (d) | — |

LuaFOW natives: call via ScarDoString on window thread only (`sdk/offsets` comment). Present vfunc = TLS AV.

## Macro

| Path | File:fn | Why | Replace | Risk |
|---|---|---|---|---|
| SendInput pane | `prod_macro.cpp` engine=0, `MacroForceSendInput` 3575 | **(c) already** | stay | ranked-ok |
| Sim queue / LocalCommand | `MacroBridgeEnsure` 2175, `macro_bridge.scar` | **oneshot** `Entity_QueueProductionItemByPBG` / `LocalCommand_EntityBuildSquad` | (c) Online; (b) vs AI | **OOS** vs humans |

## Not SCAR (do not inventory as Lua)

Lobby civ scan/write, FOWCTRL1 Full Reveal, ESP/radar collect, ImGui, DualFlag, AICTLR01 Memory locks, observer HUD C++.

## If AI BOT goes native

**Must keep SCAR:** Files tab Execute/AUTO, Lua Scripts, injector editor, user hybrids, probe (if offered), world-feed **if** any Documents script reads `AOE4HOOK_WORLD_DATA`, scoring **hooks** unless Relic Layer A is driven entirely by inner availability on AI tid (still OOS vs humans).

**Can leave SCAR:** BOT enable/lock/contest/actuator **if** (b) on AI/window tid with 4A70 ordering; Offline cheats stay SCAR-by-design vs AI; Macro sim → SendInput for humans.

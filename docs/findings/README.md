# Findings log

Dated notes from live RE / tooling. **Canon ritual and RVA tables** stay in [UPDATE_GUIDE.md](../UPDATE_GUIDE.md). This folder is the session trail so a later agent does not rediscover the same dead end.

Restored onto `main` after `2bfac27` from `cb70dba`: tools / WindowWatch / patchAT / DllInjector+Standalone `inject_boot` / this folder / RELIC_*. Overlay `InternalInjector` RA and AI-store stay out. Network Monitor finding text is `e66ae97`.

Newest first.

| Date | Note |
|------|------|
| 2026-09-30 | [Dodge against ScarToolKIT, and the 15-minute restriction](2026-09-30-dodge-stk-parity.md) (all 4 STK builds make the same call: 0x76D030 on *begin of a non-empty session vector from a remote thread, 10 s throttle, nothing on the cooldown; 0x76D030 leaves through the RLink party service (root vtbl+0xF8 = +0x17F0, sub_3010520 sends the 1-byte Leave), not Automatch2; a plain game quit drew the same 900 s in capture S1; Dodge now targets only *begin of a non-empty vector whose vtable+0x10 is the leave, with a real match id, refuses state 5, drops MpBypassDataClear and shows the result the window thread reports) |
| 2026-09-30 | [Aegis type0 nullify crashes the game](2026-09-30-aegis-type0-crash-explained.md) (`--nullify-type0` sets slot[0].size = 0, PackSection_Get(type 0) fails and the integrity dispatcher returns early, so the type3/type1 XOR decrypt of .text never runs: STATUS_ILLEGAL_INSTRUCTION at RVA 0x3DE24F0; cancels [the 2026-09-29 "safe bypass"](2026-09-29-aegis-type0-safe-bypass.md); the overlay patch keeps only the type10 permit list, anti-tamper stays a runtime matter (patchAT)) |
| 2026-09-30 | [Level spoof, Rank spoof, XP boost](2026-09-30-level-rank-xp-spoof-audit.md) (all three are local only: other clients load level / XP / rank from the server via `getEventStats`, match XP is server-side; the level reaches telemetry `LobbySessionStart` from the blob the spoof writes, now restored before a reconnect; holds ran only in a match; rank wrote the lazy +1712 that is recomputed every UI tick and was 0 until read — now the season record +1964 rating / +1968 badge from the event rank table, found by class descriptor; XP boost full-heap scan every 4 s in a match; dump-driven test) |
| 2026-09-30 | [Menu design audit 3: the panes the renders never showed](2026-09-30-menu-design-audit-3.md) (page renders now open every sub-tab (+21 panes, AI BOT with the AI on) and every accordion; i18n-miss and layout-overflow checks in the preview build; Fine tuning in cards, network rule fields back on the card, two-column pages 12 px too wide, Observer / ESP pane gating, settings that never marked the config dirty, roster ellipsis, civ and rank names, 57 translations; leftovers) |
| 2026-09-30 | [Dodge against the game source](2026-09-30-dodge-game-source.md) (0x76D030 reads no rdx: "ScarToolkit" never mattered; session vector matches the game; the leave report is unguarded, so a second press was a second report, now refused at state 5; the restriction is the server's answer to the game's own leave) |
| 2026-09-28 | [Menu and HUD design audit against mockup v3](2026-09-28-menu-design-audit.md) (21 pages + HUD rendered offscreen in 4 variants, 229 findings / 226 confirmed; shared layer: button widths for translations, long hints no longer lost, readable disabled primary, toggles centred, two-column card flow, one control column; pages, HUD alert stack and plate, ~900 translation pairs; leftovers) |
| 2026-09-28 | [Lobby roster from the Relic lobby data](2026-09-28-lobby-model-reader.md) (read-only: lobby screen model + RLink party, which also lives through the match; 528-byte slot record map; team = `m_teamAlliance` (10001 Auto, 10002 No Team), +400 is not the team; match teams from the game player table `**(img+0x84C7E18)`; lobby size is never stored, in-lobby slots carry the options JSON; chat channel counter; civ targets only in party records, re-checked at write time; offline dump test `tools/lobby_dump_test`; four review rounds) |
| 2026-09-28 | [What Aegis does to RelicCardinal.exe — mechanism map](2026-09-28-aegis-protector-map.md) (pack-time vs run-time; overlay AEAD X25519→HSalsa20→XSalsa20/skip32 + compact/fat XOR recipes; threaded VM `sub_3F910EC` + `0x397760C` helper, not devirtualized; 45E8 cloak/unlock + wyhash 99-budget; DirectX permit list decoded = Twitch/OBS/Streamline; sim-core RTTI hole confirmed, Aegis-cause hypothesis; `.text` fully decrypted, VM the only open surface) |
| 2026-09-28 | [On-disk crypt: the protector is Aegis](2026-09-06-relic-disk-crypt.md#aegis-build-log) (`Aegis_RelicCardinal.log` in the game folder: virtual map @ `0x8076800` is the ~10 MiB overlay; `RTTI Patching 21731 objects` — hypothesis for the missing Entity/Squad/Player RTTI; the CODEX “Arxan” label stays as history only; [IDA RA](2026-09-06-ida-ra-analysis.md): `0x65E052C` is `Friday` from a weekday table, no Frida strings in the image) |
| 2026-09-28 | [The bot ignored the gold vein beside its own mining camp](2026-09-28-gold-vein-ignored.md) (Macedonian 2v2: camp finished at 0:25.6 inside the 30 s food-first opening, builders sent to sheep; quota spent on busy sheep eaters Lua refused; own sheep marked the ally's; 4.8 m labels blind on veins; selection hold with a frozen clock; Lua-side quota, stay-local vein, floor-first food, bounded busy move with revert watch; two review rounds) |
| 2026-09-28 | [Network fog audit and Camera settings](2026-09-28-network-fog-audit.md) (three saved SyncErrors; Reveal Map's unconditional live permission; fail-closed native guard; stale solo cleanup cannot write network fog; Map knowledge under Camera → Reveal Map) |
| 2026-09-27 | [21:26 hang: civ AUTO heap sweep ran the whole match](2026-09-27-civ-scan-oom.md) (service runs only in a match; 6 s timer → 208 sweeps in 110 min; each sweep found the previous sweeps' SteamID strings, anchors 16k → 18.9M, 55 s and ~3.5 GB per sweep; commit exhausted 21:27:17; per-match sweep budget in `civ_scan_policy.h`, 1M anchor cap, match-replay test) |
| 2026-09-27 | [Start-of-match desync: AI map sight](2026-09-27-start-desync-map-sight.md) (unknown roster permitted a simulation fog write; frame 3/5 incidents; block unknown, default and legacy settings Off, production-service regression; second gate: the game's own network flag `0x84952B0+1`) |
| 2026-09-27 | [Selected villagers, ally-occupied veins, second-TC window](2026-09-27-selection-shared-vein-tc-window.md) (`sel skip-live` on every busy villager; think `0x2923300`: locked + live tactic keeps running, unlocked + empty is refilled in the same pass → selection stamped live; shared vein pull for busy miners; window keeps a base share, gold was 0.00 for 6–9 min) |
| 2026-09-27 | [Cloud refactor: scoring, script bridge, civilizations](2026-09-27-cloud-refactor.md) (game VM is Lua 5.3; one composer; hook-owner harness; shared layer back after a Relic reload; Markets stacking; late-game Afford; spec header + contract doc checked by tests; civ table: 10 of 23 civs on the wrong filter switch in Hybrid, 3 in prod_macro; MacroBridge false refusal; scoring cost budget) |
| 2026-09-27 | [Cloud analysis: one copy of every script, dead toggles, MSVC literal cap](2026-09-27-cloud-analysis.md) (shared Relic scoring bodies; twd / probe / dump_vm / macro_bridge fallbacks from the canon RCDATA; Buildings / Development counterpick toggles act; `kSelOn` 163 bytes under C2026; `**/Debug/` hid `debug_shots.scar`) |
| 2026-09-27 | [Cloud plan: embedded canon, engine age, build orders, late game, stone](2026-09-27-cloud-plan.md) (DLL renamed before link; RCDATA canon sync; `Player_GetCurrentAge` feed + Templar commanderie; guide only when chosen, done after its last step; selection 7 s / garrison 40 s; Full AI handover experiment; 15 military buildings at Age IV + 5 min; stone by bill; RE questions for 0x2A45959) |
| 2026-09-27 | [Anti-pick data, lock modes, threat scope, one-TC matches](2026-09-27-antipick-lockmodes-threat.md) (game 16.3 combat override + exact bonus types; Donso / Earl's Guard; Mass Army / Auto / Full AI buttons; base vs strategic threat; guide `tc=1` ignored; MASS split from the counter bill) |
| 2026-09-26 | [Economy derived from the game source](2026-09-26-economy-derivation.md) (director `sub_2B6C360`/`sub_2BBA9F0`; food floor; 2nd TC window x2.5 / House x2; army lock keeps `combat`; spear guarantee; scout deer kill) |
| 2026-09-26 | [Economic production scoring audit](2026-09-26-economy-scoring.md) (145 hooks; 9 replacements) |
| 2026-09-26 | [Scout carcass delivery](2026-09-26-scout-carcass-delivery.md) (pickup/drop-off actuator; Professional Scouts request) |
| 2026-09-26 | [WDK stays 26100](2026-09-26-wdk-26100.md) (live `ntoskrnl` `10.0.26100.9482`; kit `10.0.26100.0` GE; WDK 28000 is 26H1 + VS 2026) |
| 2026-09-26 | [HV BSOD log](2026-09-26-hv-bsod-log.md) (fatal VMEXIT writes CMOS before the bring-up return: RIP, RSP, CR3, CPU, stage; `cpu_fail` line gains `bsodrip`) |
| 2026-09-26 | [Power transition reason](2026-09-26-power-transition.md) (every shutdown: 1074/6006/6008/41 plus 30s last-alive; this boot's cause is wininit `0x50006` lsass `0xC0000374`) |
| 2026-09-26 | [BSOD forensics](2026-09-26-bsod-forensics.md) (kernel dump 2 + 24 GiB dedicated file; Event 41 code 0; lsass `0xC0000374`; `ZPPBUGCK1` leaves SVME before the dump writer) |
| 2026-09-26 | [Параметры запуска Relic](2026-09-26-relic-launch-options.md) (headless multi-IDA `qv31`; Layer B шесть; справочник [RELIC_LAUNCH_OPTIONS.md](../RELIC_LAUNCH_OPTIONS.md)) |
| 2026-09-26 | [Boot menu off](2026-09-26-bootmenu-off.md) (`displaybootmenu No`, `timeout 0`; `{memdiag}` stays a tool; default Windows 11) |
| 2026-09-26 | [Cursor logon once, elevated](2026-09-26-cursor-logon-once.md) (Limited PT10S + window-handle retry = late second window; task Highest, delay unset) |
| 2026-09-26 | [HV `654F0324` double shutdown](2026-09-26-hv-654f0324-double-shutdown.md) (load_ok 14:20; hold `status=10`; shutdown 14:31:04 and 14:35:49; empty Minidump; do not remap) |
| 2026-09-26 | [AC vs this board / Windows](2026-09-26-ac-board-windows.md) (DMI strings `1.0.2` / `MS-7C72F` / `BOURBON` overwritten; AGESA `1.3.0.1b Patch A` + ports still Hero; PCI `1043:8877`; 26H2 `26340.9482`) |
| 2026-09-26 | [HV launch refused, Event 41](2026-09-26-hv-launch-refused-event41.md) (boot 00:37 ping=`ud`; gate **21** Event 41 `2026-09-25T17:28:37` empty Minidump; sys `2D14EF01`; no kdu) |
| 2026-09-26 | [DEVICE_HUNG then `0x3AD6A86`](2026-09-26-present-device-hung-3ad6a86.md) (01:30:59 Present tid 27384; `rdi=887A0006`; DRED empty; no Event 41) |
| 2026-09-26 | [GitHub pull + Release](2026-09-26-github-pull-release.md) (`20da2d1d82` → `ab9dcfc4c9`; pack `ab9dcfc4c9`) |
| 2026-09-25 | [UNLOAD SCAR + DLL](2026-09-25-unload-scar-dll.md) (без PEB relink и без записи Relic `.text`; `NtUnmapViewOfSection` вне образа) |
| 2026-09-25 | [SCAR perf, monks, stamp ever-live](2026-09-25-scar-perf-monks.md) (C levels; full GC; `NoteEverLive` только при живом tactic; `b2b7435574`) |
| 2026-09-24 | [SCAR_ANALYSIS → C++/FPS](2026-09-24-scar-analysis-cpp-perf.md) (bb333049; +25.09 RPM-поля census/lock; команды остаются SCAR) |
| 2026-09-24 | [AI BOT Wallingford + H6 scoring re-inject](2026-09-24-ai-bot-campaign-wallingford.md) (locked fix; SetPersonality wipes Gatherer wraps; force reinject) |
| 2026-09-24 | [git main ref zeroed](2026-09-24-git-main-ref-zeroed.md) (`refs/heads/main` + `origin/main` = 41×NUL; tip `b2bd7cc` «anal 2» в objects; remote `7b827891`) |
| 2026-09-24 | [полный Rebuild](2026-09-24-rebuild-all.md) (`AOE4HOOK.sln` Community MSBuild + hv `mode=release` + auth no-SCM + titlehide; BuildTools props miss) |
| 2026-09-24 | [SCAR IDA session](2026-09-24-scar-ida-session.md) (e69670dc/c96d58e7; recursive **1067**; hook closed 236/388; hook 388; cursor hide/show singleton vt; Hex-Rays UI_Remove/SetPlayerDataContext job; 0 SAFE) |
| 2026-09-18 | [UI labs sibling](2026-09-18-aoe4hook-ui-labs.md) (`AOE4HOOK-UI\HANDOVER.md`; skeet не в DLL; порт 1.70→1.92.1 не начат) |
| 2026-09-18 | [Monk handover stops at was-strip](2026-09-18-monk-handover-boundary.md) (латч доходит, но `g_wasStrip` навсегда исключает монахов из выборки релока; решено оставить — снимать = `rva=0x1ED5529` / `0x2A45959`) |
| 2026-09-14 | [Opening unlock vs stamp](2026-09-14-open-unlock-vs-stamp.md) (`kEcoOpen`/`__EcoCppLock` не `UnlockSquad`; stamp каждый live-тик; `+noOpenUnl+tickStamp`) |
| 2026-09-14 | [Enable gate empty-only](2026-09-14-enable-gate-empty-only.md) (WouldStrip eco leftover ≠ Enable-block; STK Enable-true first; stamp `+emptyEn`) |
| 2026-09-14 | [Сверка `fea27989`](2026-09-14-remote-fea279-reconcile.md) (origin/main STK OnSpawn+keepLock + local WouldStrip gate / heap stamp; stamp `stkOnSpawn+keepLock+noEn4A70+heapLock`) |
| 2026-09-14 | [C++ read vs `.text` integrity](2026-09-14-cpp-read-vs-text-integrity.md) (RPM read OK; heap `+0x40` stamp; `OffsetsWriteBytes` refuses `.text`; `+heapLock`) |
| 2026-09-14 | [Re-enable WouldStrip `rva=0x2A45959`](2026-09-14-reenable-wouldstrip-2A45959.md) (pid 38348 02:06:52; Enable-true with would4A70=87 locked=0; `+noEn4A70`; `eco_ai_on_nothink`) |
| 2026-09-14 | [Fresh Relic dump 38348](2026-09-14-fresh-relic-dump-38348.md) (PE+141 modules+7.17 GiB RPM Memory64; slots=0; no PSS; 38872 PSS 1455 then death; Relic survived) |
| 2026-09-14 | [AI audit vs ScarToolKIT](2026-09-14-ai-audit-vs-scartoolkit.md) (V4.2 ships no AI change; 124/145 Relic hooks controlled; STK whitelist misses 19 unit types; `DefensiveStructuresCommon` ElGate + variadic binder; `ScoringFunction_Mills` + WaterGate assert) |
| 2026-09-14 | [Disable kept army +0x40](2026-09-14-disable-keeps-army-lock.md) (no `AI_UnlockAll` on combat; stamp `stkOnSpawn+keepLock`) |
| 2026-09-14 | [STK OnSpawn, no C++ LockOneSid](2026-09-14-stk-onspawn-no-cpp-relock.md) (Relic `GE_EntitySpawn` only; no `Local.AddPlayerEvent`; relock scan-only; stamp `stkOnSpawn`) |
| 2026-09-14 | [EventRule skip-map miss `rva=0x2A45959`](2026-09-14-eventrule-skip-miss-2A45959.md) (superseded: 01:09 was late `Local.AddPlayerEvent` + skip-map; STK path is Relic EventRule + `event.entity`; leftover hold stays 2500) |
| 2026-09-14 | [STK Relic eco under army lock](2026-09-14-stk-eco-army.md) (shinobi = Relic scout; `iEcon` floor 1.0; lockable-army census; stamp `+stkEco`) |
| 2026-09-14 | [STK spawn 4CE0 army lock](2026-09-14-stk-spawn-4ce0.md) (Relic `GE_EntitySpawn` `event.entity` same-tick 4CE0; Scan/cache pending; no SweepLocks; `Safe4CE0` backup; combat seats 0; stamp `+stkSpawn`; leftover hold stays 2500) |
| 2026-09-14 | [Нет запретов «не трогать»](2026-09-14-no-dont-touch-silos.md) (удалены gate .mdc; HashRec/mailbox/SHA/overlay-boot больше не rule) |
| 2026-09-14 | [NPT orig-exec ASID 4](2026-09-14-npt-orig-exec-asid4.md) (`stealth_npf_pick_view`; orig PFN R=1 W=0 X=1; hitch `orig=`; hasher HashRec; **no map**) |
| 2026-09-14 | [AMD 56421 GHCB ≠ Type-2 NPT](2026-09-14-amd-56421-ghcb-vs-npt.md) (user khub blob = Pub 56421 r2.04 SEV-ES/SNP; APM 15.25 / 33047 2.21.7 GPA NX; no kdu; `F98869A4` unmapped) |
| 2026-09-14 | [Patch Game AUTO off](2026-09-14-patch-game-auto-off.md) (forced `auto_run=0`; leftover ini ignored; RUN = red + confirm; Cycle 8g/8h hang) |
| 2026-09-13 | [empty-stack SafeStrip relock `rva=0x2A45959` sid=50120](2026-09-13-empty-stack-safestrip-2A45959.md) (pid 27332; DualFlag `slots=0`; `army relock lock sid=50120` then think AV 1.8s; unlocked tracking is never `L.safe`; no `Cmd_Stop`) |
| 2026-09-13 | [Zhu Xi 6:44 `rva=0x2A45959` after SafeStrip relock](2026-09-13-zhuxi-relock-2A45959.md) (pid 19352; cmd#588 then think AV 379 ms; `LockOneSid` must not 4A70 a sid Relic already tasked; no `Cmd_Stop`) |
| 2026-09-13 | [OP20 leftover = overlay in ~1.5s after Starting mission](2026-09-13-ra-op20-overlay-before-lua.md) (13:57 ungated Present; 14:56 hold4 slots=0 then OP20 T+1.48s; 15:06 hold5 Starting-mission+2500 slots=0 no leftover; writer `sub_3DDB29C`; no Enqueue plant) |
| 2026-09-13 | [Cycle 9 wininit 0x50006 / no OS DLL NPT](2026-09-13-hv-cycle9-wininit-50006.md) (A67B068F; Relic 21296 hold ok then wininit 0x50006; no new Event 41; ntdll trap off) |
| 2026-09-13 | [Cycle 9 HV reset](2026-09-13-hv-cycle9-reset.md) (op 8 leftover-first; query user DTB; hitch on mbox-ping; HV-only ritual; no remap 17E25811) |
| 2026-09-13 | [Cycle 8h post-41 usermode guard](2026-09-13-hv-cycle8h-post41-usermode-guard.md) (zpp_aoe4 leftover --cr3 Toolhelp refuse; sys still 17E25811; last_fix=22:32:18; launch_authorized=false; do not map) |
| 2026-09-13 | [Cycle 8h leftover NX status=8](2026-09-13-hv-cycle8h-leftover-nx-status8.md) (15720/10324/19956 `--clear --cr3` status=8 = `not_found`, not NX off; ping ud; blocked; no remap) |
| 2026-09-13 | [Goal not complete](2026-09-13-hv-goal-not-complete.md) (Done-when table; Event 41 22:07; ping ud; UpdateGoal **not** called) |
| 2026-09-13 | [Stock x64dbg Attach refused](2026-09-13-stock-x64dbg-attach-refused.md) (Event 41 22:07 this boot; ping ud; Relic none; no Attach / no kdu / no remap 17E25811) |
| 2026-09-13 | [Cycle 8h dual-nCR3 gap](2026-09-13-hv-cycle8h-dual-ncr3-gap.md) (PTE/NPF/HashRec-hit **not proven**; mailbox 1–12 no NPTE; hitch npf=0 map-time only; blocked by 41) |
| 2026-09-13 | [Cycle 8h RUN then 41](2026-09-13-cycle8h-run-then-41.md) (user RUN x3 on **3832**; Event 41 22:07; no DXGI; `auto_run=1` leftover; ping ud; no remap) |
| 2026-09-13 | [Cycle 8h Overlay RUN then 41](2026-09-13-hv-cycle8h-run-then-41.md) (Event 41 22:07; map `17E25811`; Relic 3832 died with host; leftover NX not queryable; do not remap) |
| 2026-09-13 | [Cycle 8h inject no AUTO](2026-09-13-cycle8h-inject-no-auto.md) (Relic **3832** `0x7FF7B6EE0000`; elevated APC; `auto_run=0`; slots=0; PEB unlink hides Toolhelp; no attach) |
| 2026-09-13 | [Cycle 8h hold GPU AV](2026-09-13-hv-cycle8h-hold-gpu-av.md) (Relic 15720 Present `0x3AD6BC6` after TimerQ hold; NVIDIA+Steam overlay heap; host pong; no remap; skip TimerQ) |
| 2026-09-13 | [Rebuild-HvCycle not hitch wait](2026-09-13-rebuild-hv-not-hitch-wait.md) (24s 21:12; Capture+clean+zpp_aoe4 stripped; sys `17E25811`; ELF still `E97A9C6E`; no kdu) |
| 2026-09-13 | [Event 41 21:06 no kdu](2026-09-13-event41-2106-no-kdu.md) (boot 21:05:57; hang 21:05:10; last map still 8g 20:38; disk `283427E1` compile-only) |
| 2026-09-13 | [Map-AfterZppu no sleep](2026-09-13-map-afterzppu-no-sleep.md) (WaitAlive + 50s poll + DriverEntry 12s `KeDelay` made `-Wait` look hung; not a map; not an 8g TDR fix) |
| 2026-09-13 | [Cycle 8g freeze then 41](2026-09-13-hv-cycle8g-freeze-then-41.md) (Event 41 20:49; Relic 6732 DXGI DEVICE_HUNG after AUTO RUN; do not remap `7B5C8989`) |
| 2026-09-13 | [Cycle 8e hang after hold](2026-09-13-hv-cycle8e-hold-hang.md) (Event 41 20:27; not nested kdu; KPTI CR3 ≠ owner DTB disarmed live NX; do not remap `AB7D293D` / `02F9B040`) |
| 2026-09-13 | [Canon product-cycle docs](2026-09-13-canon-product-cycle-docs.md) (project-map / ADR-007 / CLI table / Patch Game comments; stock x64dbg after HV+AUTO) |
| 2026-09-13 | [Product dbg cycle](2026-09-13-product-dbg-cycle.md) (HV hold → `DllInjector --patch-game` → stock x64dbg; script `Run-ProductDbgCycle.ps1`; does not map) |
| 2026-09-13 | [Cycle 8d hang after Relic AV](2026-09-13-hv-cycle8d-hang-after-relic-av.md) (Event 41 20:05; **not** nested kdu; LIVE 8e `AB7D293D` `load_ok` 20:18; disk 8f `02F9B040` `stealth_reap.h` + Map-AfterZppu exit 6; do not nested-map 8f / remap `A1EA2CF1`) |
| 2026-09-13 | [Cycle 8d hold slots=0](2026-09-13-hv-cycle8d-hold-empty.md) (idle map `A1EA2CF1`; Relic 34288 `0x7FF716E90000`; arm status=0; IDA closed 3256; hidden rbhost 60s empty) |
| 2026-09-13 | [IDA hosts xrefs](2026-09-13-ida-hosts-xref-confirm.md) (GUI on ida-work copy; 60644 packed `.nam` not VA; `strcpy` vortex-events `0x416CA70`; reputation host 0 strings; product hosts unchanged) |
| 2026-09-13 | [Cycle 8c Relic-live map Event 41](2026-09-13-hv-cycle8c-relic-live-map.md) (8b status=8 = leftover EPROCESS; 8c map kept Relic 36364 → 41 19:36; do not remap `D78C5065`) |
| 2026-09-13 | [Hosts trust/telem catalog](2026-09-13-hosts-trust-telem-catalog.md) (hosts deny only `reputation` + `vortex-events`; ESS/PlayFab/RTA/Windows vortex/UDP relay/SOCKS-class/GRE out) |
| 2026-09-13 | [DllInjector hosts before APC](2026-09-13-dllinjector-hosts-before-inject.md) (elevated injector writes dual-stack `reputation.xboxlive.com`; overlay Install no-op if complete; no ESS/XBL auth hosts) |
| 2026-09-13 | [Patch Game tab](2026-09-13-patch-game-tab.md) (overlay RUN after HV hold: user32 body / hide / `-nodbg`; no Relic `.text`; AI BOT untouched) |
| 2026-09-13 | [Cycle 8 user CR3 + HashRec](2026-09-13-hv-cycle8-user-cr3.md) (scan 0x800, test-as-you-go DTB; hasher `0xFFFFFFFE`; not hold 36888) |
| 2026-09-13 | [Hasher HashRec NPT emulate](2026-09-13-hv-hasher-hashrec.md) (`eax=0xFFFFFFFE` at `0x3E57050`; 45E8 stored hash; not `--eax 1`; not mapped, ping pong) |
| 2026-09-13 | [NPT dual-nCR3 vs EPT split](2026-09-13-npt-dual-ncr3-vs-ept-split.md) (AMD X⇒R; identity NX orig / stealth copy per vCPU; hasher vs Enqueue = same CR3, R vs fetch) |
| 2026-09-13 | [New PID RVA vs VA](2026-09-13-new-pid-rva-vs-va.md) (ASLR = база; locate/sigscan; hasher dest slots ≠ весь `.text`; 36888 Enqueue AOB at `0x3DD2550`) |
| 2026-09-13 | [Cycle 6 NPT ret stub](2026-09-13-hv-cycle6-npt-ret-stub.md) (dual-nCR3 identity original / execute-copy insn-exact ret at Enqueue/KickCtor/TimerQ; not WPM; Cycle 5 still mapped ping pong; Relic 36888 slots=0) |
| 2026-09-13 | [Always elevate](2026-09-13-always-elevate.md) (all HV/Relic/dbg/python launches RunAs; medium-IL schtasks denied ≠ missing HostPrep) |
| 2026-09-13 | [Cycle 4 stealth --file abort](2026-09-13-hv-cycle4-stealth-file-abort.md) (op 6 frozen; zpp_aoe4 stop on first status!=0; no map) |
| 2026-09-13 | [Cycle 3 hold hang](2026-09-13-hv-cycle3-hold-hang.md) (Relic 20068 23/39 status=10; Event 41 17:09; nop5+E8 falsified; no map) |
| 2026-09-13 | [Cycle 3 user execute](2026-09-13-hv-cycle3-user-execute.md) (no запускай ritual; gate flip; one Map-AfterZppu) |
| 2026-09-13 | [Cycle 3 запускай path](2026-09-13-hv-cycle3-zapuskay-path.md) (gate 20; exact Map-AfterZppu after запускай; Relic 5012/0x7FF7BABB0000 dead; no map) |
| 2026-09-13 | [Cycle 3 ELF rebuild](2026-09-13-hv-cycle3-elf-rebuild.md) (sys 16:45:29 SHA256 `5351E024…`; `stealth_nop5_e8_ok`; insn_boundary PASS; `launch_authorized=false`; no map) |
| 2026-09-13 | [Cycle 1 hold hang after load_ok](2026-09-13-hv-cycle1-hold-hang.md) (Relic 5012 AV execute@0; Event 41 16:32; cookie analyzed_failed; no map) |
| 2026-09-13 | [session 3305282e resume](2026-09-13-agent-session-3305282e-resume.md) (parent 16:28 success; grind `5d63478e` died after rbhost; Cycle 1 mapped; hold 20/39; no kdu) |
| 2026-09-13 | [Cycle 3 hold insn_starts_at](2026-09-13-hv-cycle3-hold-insn-boundary.md) (20/39 `status=10`; nop5+E8 skip left-scan; source only; do not remap) |
| 2026-09-13 | [agent context session rebase](2026-09-13-agent-context-session-rebase.md) (STEPS 3–5; VA=base+RVA; dest skip `0x3E58000`/`0x3F04000`/`0x3F2D000`; STALE_SIGNATURE; dead 15556/53020/31656; IDA MCP 10054, 60644 memory.bin 14/14 AOB) |
| 2026-09-13 | [agent context usermode/dbg](2026-09-13-agent-context-usermode-dbg.md) (STEPS 7–11: zpp_aoe4 modules, fail-closed writes, Vs AI, x64dbg unhidden then HV then hidden, 15s prove; no map; mailbox 1–12 untouched) |
| 2026-09-13 | [agent HV preflight STEPS 1-2](2026-09-13-agent-context-hv-preflight.md) (gate 21; ping ud; leftover SVME; OTHER AGENTS MUST DO; no map) |
| 2026-09-13 | [Cycle 1 C-bit window PTE](2026-09-13-hv-cycle1-cbit-window.md) (hyp held: 16:21:43 `load_ok` 1075200; keyed pong; do not remap) |
| 2026-09-13 | [HV crash-safe breadcrumbs](2026-09-13-hv-crash-safe-breadcrumbs.md) (K: Flush before kdu; HostPrep Capture first; no map; gate 20/21) |
| 2026-09-13 | [extra Windows Boot Manager / leftover ESP EFI](2026-09-13-windows-extra-bootmgr-efi.md) (NVRAM: one `{bootmgr}` on C: ESP; wiped EFI on SN520 + Toshiba ESPs; stale OSLOADER gone; Rollback kept) |
| 2026-09-13 | [non-map test suite](2026-09-13-hv-nonmap-test-suite.md) (Verify-AmdPort PASS; gate 21 cookie; ping ud; CrashDumpEnabled=0 live; no kdu) |
| 2026-09-13 | [cookie + HostPrep + gate 21](2026-09-13-hv-bsod-cookie-gate-memory.md) (Event 41 15:54; HostPrep exists; CrashDump 0/1/0; no kdu) |
| 2026-09-13 | [CrashDumpEnabled=3 after reboot](2026-09-13-hv-crashdump-not-zero.md) (0% hang not fixed; Event 41 15:54; cookie in_progress) |
| 2026-09-13 | [HV dump stuck at 0%](2026-09-13-hv-bsod-dump-zero-percent.md) (Event 41 = hang; dump writer 0%; gate was skipped; CrashDumpEnabled=0) |
| 2026-09-13 | [HV BSOD 15:18 sys hang](2026-09-13-hv-bsod-1518-sys-hang.md) (Event 41 x3; 15:07 sys 1073152 load_ok; 15:18 sys 1073664 hangs; no minidump) |
| 2026-09-13 | [Relic Temp DMP empty window](2026-09-13-relic-temp-dmp-empty-window.md) (15:12 snapshot 80000003; slots=0; original Enqueue; not the 15:23 hang) |
| 2026-09-13 | [HV BSOD nested map 26H2](2026-09-13-hv-bsod-nested-map-26h2.md) (15:07 load_ok peb=0x2e0; 15:18 second -map; Kernel-Power 41; no dump) |
| 2026-09-13 | [HV after Windows 26H2 26340](2026-09-13-hv-windows-26h2-26340.md) (ntos 26100.9482; PEB 0x2e0; MiGetPte 0x4408a0; offline audit PASS; SVM not mapped) |
| 2026-09-13 | [RA delayed kick = silent death](2026-09-13-ra-delayed-kick-silent-death.md) (killed not crashed, twice: slot `40230001` ~1 s after match start → silent stop in 2m15s / 3m15s; Steam `exit code 0`; `RA suppressed` label was false; `5638b2eaed` muted VEH for all threads; capture tool `tools/watch_relic_death.ps1` names the killer via ETW `NtOpenProcess` `PROCESS_TERMINATE`, verified vs `taskkill`) |
| 2026-09-13 | [HV full map + handoff](2026-09-13-hv-full-map-handoff.md) (goal not met; SVM dead; committed `<<<<<<<` in ELF/loader; next = resolve HEAD then one map then hold) |
| 2026-09-13 | [HV version-agnostic offsets](2026-09-13-hv-version-agnostic-offsets.md) (discover DTB/PEB/PID/links/userdtb at map-time; `userdtb_off=0` = KVAS off; no 26200/0x388 table; live SVM not remapped) |
| 2026-09-13 | [HV hold before debugger](2026-09-13-hv-hold-before-dbg.md) (NPT identity original / execute-copy not armed; status=8 after C-bit map; no x64dbg) |
| 2026-09-12 | [five-agent code audit](2026-09-12-five-agent-audit.md) (WM_APP remap actually landed + pinned; VEH silent tail; game-over guard self-crash; villager/sel/group/garrison 4A70 gates; farm-ring zero handle = 09:34 AV; deferred list) |
| 2026-09-12 | [HV WW empty then slots=3](2026-09-12-hv-ww-slots3-x64dbg.md) (42396 DualFlag at x64dbg 23:54; packed fill ~5m; 42408 new) |
| 2026-09-12 | [HV AIDA 25H2 + PCID нет](2026-09-12-hv-aida-25h2-pcid.md) (`Report.xml` 21:28; 26200.7171; PCID=нет → KPTI два CR3) |
| 2026-09-12 | [HV usermode finds, HV arms](2026-09-12-hv-usermode-find-hv-arm.md) (25H2 26200.7171; hold status=8 = KPTI kernel CR3; loader UserDirectoryTableBase; no x64dbg until apply) |
| 2026-09-12 | [HV hello 19/20 CLFLUSH copy_phys](2026-09-12-hv-hello-clflush.md) (leave 32/32; map 22:48; query explorer status=0) |
| 2026-09-12 | [HV MiGetPteAddress + ZPPU leave](2026-09-12-hv-migetpte-zppu.md) (RVA 0x405850; unload waits ping #UD 32/32) |
| 2026-09-12 | [HV remap without reboot](2026-09-12-hv-remap-without-reboot.md) (product = ZPPU leave then map; reboot aborted; SVM 21:29 live) |
| 2026-09-12 | [HV AIDA64/DxDiag PTE large](2026-09-12-hv-aida-dxdiag-pte.md) (5080 not 5090; 1GB pages; map 21:29 `copyphys_pte_fail`; reserved 4K next) |
| 2026-09-12 | [HV hello rax=2 after 34GiB+MDL](2026-09-12-hv-hello-mdl-rax2.md) (map 21:15 ping pong; GIF=0 MapLockedPages; PTE poke next) |
| 2026-09-12 | [HV hello rax=2 RAM PA>32GiB](2026-09-12-hv-hello-ram34.md) (map 20:59 copyphys_ok ping pong; identity 34 GiB) |
| 2026-09-12 | [HV copy_phys hello rax=2](2026-09-12-hv-copyphys-hello-rax2.md) (map 20:59 ping pong; MmCopyMemory GIF=0; MDL fix not mapped) |
| 2026-09-12 | [HV reboot + copy_phys map](2026-09-12-hv-reboot-copyphys.md) (not ZPPU; live 20:14 ping pong; task Map-Loader2044; sys 20:44) |
| 2026-09-12 | [HV copy_phys no mapwin](2026-09-12-hv-copyphys.md) (hello rax=2; dump 15843 0xDA 0x107 before live 20:14 SVM; MmCopyMemory reads only; sys 20:44 not mapped) |
| 2026-09-12 | [HV mapwin 0xDA](2026-09-12-hv-mapwin-0da.md) (SYSTEM_PTE_MISUSE 0x104; PoolTag `'ppzD'` vs KernelMode=0; loader 20:06) |
| 2026-09-12 | [HV VBS after planned reboot](2026-09-12-hv-vbs-after-reboot.md) (boot 19:45:14 HypervisorPresent=True; do not map) |
| 2026-09-12 | [HV AT catalog PID 46060](2026-09-12-hv-at-catalog-46060.md) (session dest live; hold skip dest pages `0x3F04000`/`0x3F2D000`; 35/27 arm; named RA_*) |
| 2026-09-12 | [HV Relic+WW slots=3](2026-09-12-hv-relic-ww-slots3.md) (PID 29604 menu; WW Release; CE; x64dbg.exe no attach; hello rax=2; prove watcher_pack) |
| 2026-09-12 | [HV ZPPX hello rax=2 / 4K mapwin](2026-09-12-hv-zppx-mapwin.md) (map 18:55 ping ok; not #UD; sys 19:23 not mapped; live SVM no second map) |
| 2026-09-12 | [HV map 17:59 BugCheck 0x1AA](2026-09-12-hv-map1759-1aa.md) (dump 10625; RIP=0 ErrorCode 0x10; not 0x109; not fxsave; do not remap) |
| 2026-09-12 | [HV map 17:59 query still 8](2026-09-12-hv-map1759-query8.md) (planned reboot 18:16; efer=4d01 ping ok; all names not_found; hold unarmed) |
| 2026-09-12 | [HV planned reboot + verify](2026-09-12-hv-planned-reboot-verify.md) (user ребут и проверка всего; map 17:59 after new boot; prove hv_hold) |
| 2026-09-12 | [HV ZPPU ≠ reboot remap](2026-09-12-hv-zppu-remap.md) (leave path exists; do not run on map 17:50; leftover SVME = hang) |
| 2026-09-12 | [HV map 17:50 query=8, AT not patched](2026-09-12-hv-map1750-query8.md) (FFXSR `efer=4d01`; query still 8; hold unarmed; sys 17:59 CS.RPL+handoff CR3 **not mapped**) |
| 2026-09-12 | [HV map 16:50 BugCheck 0x109 EFER](2026-09-12-hv-map1650-bsod-109.md) (PatchGuard type7; hitch `efer=d01` vs cpu_ok `4d01`; query=8; WW slots=3; no remap) |
| 2026-09-12 | [HV reboot then map 16:50](2026-09-12-hv-reboot-then-map.md) (no autostart; запускай after desktop) |
| 2026-09-12 | [HV universal modules + session dest + timers](2026-09-12-hv-universal-session-timers.md) (prove=hide_hold; dest skip `0x3E58000`; loader 16:50 not mapped) |
| 2026-09-12 | [HV AT-disable plug-in](2026-09-12-hv-at-disable-module.md) (hasher NPT-hook ok, plant/`eax=1` no; FairPlay out of HV) |
| 2026-09-12 | [HV TSC-hide map](2026-09-12-hv-tsc-hide-map.md) (aoe4-hv: mapped 15:21, ping 8/8, leftover=135, ZPPX hello ok; not Relic) |
| 2026-09-12 | [HV TSC hide slice](2026-09-12-hv-tsc-hide.md) (aoe4-hv: `svm_slices::tsc_hide` VMCB TSC_OFFSET + APERF; no RDTSC intercept; mapped 15:21) |
| 2026-09-12 | [HV Wave 4 handoff key / #MC / slices](2026-09-12-hv-wave4-handoff-slices.md) (aoe4-hv: per-boot key, leftover without VMMCALL, product #MC stash, svm_slices all false; not mapped) |
| 2026-09-12 | [HV MTF kind leak / stealth bounds / IDT](2026-09-12-hv-mtf-stealth-idt.md) (aoe4-hv: self-hidden MTF slot, stealth insn bounds, fill_host_idt, drop FS/GS snapshot) |
| 2026-09-11 | [HV usermode mailbox agent](2026-09-11-hv-usermode-agent.md) (aoe4-hv ZPPX: encrypted 4K mailbox; agent knows Relic; ELF does not plant RVA) |
| 2026-09-11 | [AMD VMCB Clean + dual ASID](2026-09-11-amd-vmcb-clean-asid.md) (aoe4-hv: resume no longer forces Clean=all; ASID 1/2/3; ZPPI PDPT; kind 9 no shared X) |
| 2026-09-11 | [NPT stealth ZPPN](2026-09-11-npt-stealth.md) (aoe4-hv dual-nCR3: data=original, exec=stub; no Relic RVA plant) |
| 2026-09-08 | [gamesource_unp_humanized](2026-09-08-gamesource-unp-humanized.md) (unpack-disk → named C; 66/66 match; leftover 651 472 B, overlap 0) |
| 2026-09-08 | [mid-match `rva=0x2A45959` after hippodrome relock](2026-09-08-riddari-relock-2A45959.md) (`LockOneSid` must not 4A70 `scar_scout` / `scar_hippodrome_scout`; `kRelockTryCap=1`) |
| 2026-09-08 | [Hippodrome Scout + Golden Horn crossbow to the player](2026-09-08-hippodrome-scout-player.md) (`scar_hippodrome_scout` / dummy+crossbow lock; starting `unit_scout_*` stays Relic) |
| 2026-09-08 | [in-match heap AV is not the relock fail-fast](2026-09-08-heap-av-crash-class.md) (`c0000005` in `RtlAllocateHeap` vs `c0000409`; silent tail = heap damage, VEH cannot log; LocalDumps `E:\aoe4_dumps` full; relay scan no longer starts in-match) |
| 2026-09-08 | [relock teardown / Hippodrome Scout / Fast TC telemetry](2026-09-08-relock-teardown-scout-fasttc.md) (relock gated on `RadarSimWorldLooksLive`; scout leaf = any `scout` not two tokens; `eco_goal` on goal-lock `desDirty`) |
| 2026-09-07 | [git main ref](2026-09-07-git-main-ref.md) (`refs/heads/main` = 41 NUL; restored `384cdc1c`) |
| 2026-09-07 | [Rebuild overlay](2026-09-07-rebuild-overlay.md) (`AOE4HOOK.sln` 22:06; HV нет; Git SCM off для Aoe4Auth) |
| 2026-09-07 | [catalog verify](2026-09-07-catalog-verify.md) (aoe4world 0.0.2 English fallbacks / `en` / building HP; no RVA retarget) |
| 2026-09-07 | [Hex-Rays reversed/](2026-09-07-hexrays-reversed.md) (одна функция = один файл; `gamesource/reversed/<bucket>/`; не в overlay git) |
| 2026-09-07 | [SCAR XOR](2026-09-07-scar-xor.md) (ключ `0x8B^i`; 2088/3190 строк; 975 LEA; AES maps всё ещё закрыты) |
| 2026-09-07 | [Hex-Rays readable](2026-09-07-hexrays-readable.md) (488031 → 87 shards + 65 named; RVA/types; `src/readable`) |
| 2026-09-07 | [SCAR overlay inventory](2026-09-07-scar-overlay-inventory.md) (every InternalInjector DoString path; Files stay; scoring = Relic hook) |
| 2026-09-07 | [Hex-Rays complete](2026-09-07-hexrays-complete.md) (45048 done 01:01; **488031**/534587 `.c` = 91.29%; lib 46500; fail 56; MCP 0) |
| 2026-09-07 | [полный уход от SCAR](2026-09-07-leave-scar.md) (три смысла; Layer A стена; пути L/M/T/Z; потолок = M или T) |
| 2026-09-07 | [AI/SCAR opt backlog](2026-09-07-ai-opt-backlog.md) (Enable=`SendMessage` с Present; coalesce WM; world-feed off) |
| 2026-09-07 | [native AI vs C++ без SCAR](2026-09-07-native-ai-cpp.md) (AI-поток / `+0x12F4` / inner queue; think уже C++; director без SCAR — нет) |
| 2026-09-07 | [полный Rebuild](2026-09-07-rebuild-all.md) (`AOE4HOOK.sln` + hv + auth + titlehide; WW LNK1104 → стоп 51712) |
| 2026-09-07 | [aoe4-hv не стартует](2026-09-07-aoe4-hv-status.md) (577 DSE; testsigning не live; билд 12800 B; не в System32; `--arm` не было) |
| 2026-09-07 | [Restore hide/tools/docs](2026-09-07-restore-hide-docs.md) (`cb70dba` → `main` after `2bfac27`; DLL RA/AI still out) |
| 2026-09-06 | [PAGE_GUARD hide?](2026-09-06-page-guard-hide.md) (читает одну страницу; KiUser hits=0 / UD2; RA guard = slots=3; не heartbeat) |
| 2026-09-06 | [FlushArm heartbeat](2026-09-06-flusharm-heartbeat.md) (`now+period` KUSER; `ra_emu.py heartbeat/write`; in-process tick) |
| 2026-09-06 | [RA emu](2026-09-06-ra-emu.md) (L0–L6 data-only; `ra_emu.py plan/hold/apply`; apply вне RA∪SNAP; **no plant**) |
| 2026-09-06 | [IatObj+8 RPM watch](2026-09-06-iatobj-writewatch.md) (`+8=0` 26976 90s slots=3 **and** 41064 `0→3`; WorkQ empty; heap 7AB0 = rdata clone; no plant) |
| 2026-09-06 | [Hide-dbg hold](2026-09-06-debug-attach-hold.md) (52920 slots=0; rbhost 52428; 26976 T+20s **slots=3** `20220002`; no attach / no plant) |
| 2026-09-07 | [WW 0→3 then 299](2026-09-07-hide-fix-ww.md) (41064: slots=3=WW, death=attach; bland `_src` + plugin rename; hold **53700** no attach) |
| 2026-09-06 | [MCP attach killed 41064](2026-09-06-debug-attach-41064.md) (`debug_attach_pid` + hide + rbhost; EP=0x48; recovery 51652 relicconnect; slots=3) |
| 2026-09-06 | [Debug attach canon](../RELIC_DEBUG_ATTACH.md) (hide ≠ plant; **soft-bind only**; WW слоты ≠ HashRec dest0) |
| 2026-09-06 | [Unpack pipeline](2026-09-06-unpack-pipeline.md) (`rediscover` по форме; `Run-RelicUnpackPipeline.ps1`; канон [RELIC_UNPACK_ALGORITHM.md](../RELIC_UNPACK_ALGORITHM.md); **no plant**) |
| 2026-09-06 | [RA kick emu](2026-09-06-ra-kick-emu.md) (data-only: expire / kick-TimerQ / `--iat-skip --hold` / SNAP windows; 26976 slots=0; **no plant**) |
| 2026-09-06 | [Full patch ≠ leftover](2026-09-06-full-patch-is-not-leftover.md) (Steam-exe не цель; HashRec не кроет SNAP; оверлей = продукт) |
| 2026-09-06 | [`g_RA_IatObj+8` / vtbl+10](2026-09-06-iatobj-slot.md) (писателя нет; RA `call [r*+10h]`=0; 52968 slots=3 при `+8=0`; live 52920 `+8=0`; **no plant**) |
| 2026-09-06 | [Post-unpack RA integrity](2026-09-06-ra-integrity-layer.md) (45E8 cloak vs unlock; PID **52920** dest0 leftover **621 219** @ slots=0) |
| 2026-09-06 | [Live CLI + C4SP3R](2026-09-06-live-cli-c4sp3r.md) (PID **52920** hold: overlay only, **slots=0** empty; WW 54060 closed) |
| 2026-09-06 | [Relic unpacker layers](2026-09-06-relic-unpacker.md) (Enqueue invert n=2327; footer→tableOff→105383 recs; spans keep formula∨n≥16) |
| 2026-09-06 | [7AB0 decrypt / re-find](2026-09-06-7ab0-decrypt-verify.md) (11 passes; 16-byte prologue ≠ unique; PID 40888 RPM; **no plant**) |
| 2026-09-06 | [who talks to 7AB0](2026-09-06-7ab0-enqueue.md) (`IatObj_Fwd` `0x3E1E2A4` + Sibling path-scan; `[+8]=0`; **no plant**) |
| 2026-09-06 | [VirusTotal Steam Relic](2026-09-06-vt-relic-disk.md) (SHA `5380c577…`; 0 comments; 0/69; idle sandbox; TEMP exe ≠ dropper) |
| 2026-09-06 | [VMP-Deob vs Relic](2026-09-06-vmp-deob-vs-relic.md) (private repo; C⊕P: 0 repeating page keys; Relic ≠ VMP) |
| 2026-09-06 | [max decrypt map](2026-09-06-gamesource-max-decrypt.md) (`.text` lift; overlay AEAD **закрыт** 23:34; 13 AES map-lua ещё без ключа; mydisasm not VMP) |
| 2026-09-06 | [AoE4 gamesource](2026-09-06-aoe4-gamesource.md) (`K:\aoe4_dlc\aoe4\gamesource`; resume 534k Hex-Rays; not IL2CPP) |
| 2026-09-06 | [7AB0 dispatcher](2026-09-06-7ab0-dispatch.md) (opcode switch + 11% 77E8 decoy; work queue decrypt; 40888 hashwalk slots=0) |
| 2026-09-06 | [Heartbeat emulator](2026-09-06-heartbeat-emu.md) (covers C8E4 expire only; stub+emu still 7AB0 IAT-kick) |
| 2026-09-06 | [Game folder unpack](2026-09-06-game-folder-unpack.md) (oracle PE + SGA; 13 AES map-lua без ключа; static unpack = `unpack-disk`) |
| 2026-09-06 | [On-disk Relic crypt](2026-09-06-relic-disk-crypt.md) (Steam+Arxan-class; ~79% `.text`; live lift + `unpack-disk`; не dearxan) |
| 2026-09-06 | [RA coverage audit](2026-09-06-ra-coverage-audit.md) (EventSchedule 100/100; Watcher 6× EvSched; dump=IDA; 7AB0 Hex-Rays still open) |
| 2026-09-06 | [Enqueue+SNAP death / --packs](2026-09-06-enqsnap-packs.md) (43676 slots=0 then dead 8s; EventSchedule first) |
| 2026-09-06 | [Relic CLI flags](2026-09-06-relic-cmdline-flags.md) (`-dev` / `-nodbg` / `-notrap` + table parser; fifth pass = all dumps; catalog [RELIC_COMMAND_LINE.md](../RELIC_COMMAND_LINE.md)) |
| 2026-09-06 | [45E8 HashRec map](2026-09-06-ida-hash-records.md) (43676: 3 SNAPs, 0 ptr hits; C8E4 tree 4 armed) |
| 2026-09-06 | [IAT pack writer 7AB0](2026-09-06-ida-iat-scan.md) (4 heartbeat keys; FlushArm refresh; stub = expire = IAT-kick) |
| 2026-09-06 | [IDA Enqueue + attach INT3](2026-09-06-ida-enqueue-callers.md) (63 xrefs; CAF8/1FDC retaddr `0xCC`; `--full`) |
| 2026-09-06 | [patchAT](2026-09-06-patchAT.md) (42764 6-byte ww IAT-kick +2s; 40280 nuclear death; no default plant) |
| 2026-09-06 | [relicconnect soft-bind](2026-09-06-relicconnect.md) (OpenProcess empty; File→Attach packs; cycle 7 host title `x64dbg-hidden` → WW +15s) |
| 2026-09-06 | [clean cycle 4940 / 38948 / 35720 / 18480](2026-09-06-clean-cycle.md) (cycle 7: post-connect 0, then WW 3; cycle 6 attach EP=0x48 → 8) |
| 2026-09-06 | [x64dbg settings audit](2026-09-06-x64dbg-settings.md) (Events/Engine/Gui/Misc/Exceptions + ScyllaHide no-inject; PID 38692 WW wait/`err=299`/slots 0→3→11) |
| 2026-09-06 | [x64dbg plugins vs WW](2026-09-06-x64dbg-plugins.md) (ScyllaHide WindowTitle only; no Inject/TitanHide/HyperHide) |
| 2026-09-06 | [WW launch slots=3 / attach slots=11](2026-09-06-ww-launch-attach.md) (sibling leaf `x64dbg.exe`; bland `RuntimeBroker.exe` + 50ms retitle; no Relic `.text`) |
| 2026-09-06 | [OS-body hide no Relic .text](2026-09-06-os-body-hide.md) (33376 lived: Relic IAT/strings OFF; 37388 `0x56FD3C0`) |
| 2026-09-06 | [x64dbg attach-on-PID 36208](2026-09-06-x64dbg-crash-catch.md#pid-36208-1716--game-first-attach-immediately-no-inject) (no inject; RIP `+0x3E9D280` junk; Relic died at boot) |
| 2026-09-06 | [Inject 36000 watcher+sibling ret 1](2026-09-06-inject-crash.md#pid-36000-1714--watchersibling-ret-1-only-iat-pack-kick) (WW pack gone; IAT `0x56FD380` slots=4→8; kick ~4s, no JUMPOUT) |
| 2026-09-06 | [Network Monitor tab + HTTP catalog](2026-09-06-network-monitor.md) (WinHTTP/WinINet/HC; rules in `Config\network_monitor.ini`; hooks default OFF after 27072) |
| 2026-09-06 | [Inject crash 27072 HTTP intercept](2026-09-06-inject-crash.md#pid-27072-1653--http-intercept-on-still-jumpout) (BEX64 RIP=0; `hooks=12` stolen=14 fallback; intercept default OFF) |
| 2026-09-06 | [Build-order Layer B wiring](2026-09-06-build-order-layer-b.md) (`AiEcoBlendBuildOrder` floors gatherer/income; Fast TC wins; boom BO does not unlock ecoLock) |
| 2026-09-06 | [x64dbg crash-catch ritual](2026-09-06-x64dbg-crash-catch.md) (dbg first, attach, then inject; 27072 WER dump; `AOE4_WindowHide`) |
| 2026-09-06 | [Attach cycle post-0x10E](2026-09-06-attach-cycle.md) (37124 neutralize ON / cloak OFF; Present then BEX64 ~1s; second inject blocked on UAC) |
| 2026-09-06 | [Inject crash 37124 + FairPlay off Relic .text](2026-09-06-inject-crash.md) (BEX64 RIP=0; winhttp/wininet/libHttpClient intercept) |
| 2026-09-06 | [Build-order import + C++ module](2026-09-06-build-order-import.md) (115 aoe4guides + 23 curated; `BuildOrderPickSlug`; not Layer B) |
| 2026-09-06 | [Live Relic + MCP snapshot 16:45](2026-09-06-live-mcp-snapshot.md) (Relic DOWN after 37124 AV; CE/x64dbg down; VS stdio up; `:5050` 406) |
| 2026-09-06 | [Eco scoring: opening gate, feudal upgrades, Fast TC](2026-09-06-eco-scoring-opening-fast-tc.md) (`op` rax-only; gathering not Lua-0; Fast TC = 2 TCs) |
| 2026-09-06 | [Farm rings around every food drop-off](2026-09-06-farm-rings.md) (TC/granary/landmarks; commit was planned-only) |
| 2026-09-06 | [x64dbg vs WindowWatcher hide (hashed GWTW / XOR chrome / ScyllaHide gaps)](2026-09-06-x64dbg-windowwatcher-hide.md) |
| 2026-09-06 | [Inject 37124 then Relic AV](2026-09-06-inject-37124-crash.md) (FairPlay Release in; cloak OFF; BEX64 `0xC0000005` ~1s after Present) |
| 2026-09-06 | [Enemy intel / counter-plan](2026-09-06-enemy-intel.md) (landmarks, Meinwerk/Steppe Redoubt signals, `__EcoAct` wiring) |
| 2026-09-06 | [Squad lock: negative army filter + 3-monk latch](2026-09-06-squad-lock-uniques-monks.md) (`LockOneSid` SafeStrip monks; hybrid quota 3) |
| 2026-09-06 | [FairPlay / reportMatch send-block + trust/VAC](2026-09-06-fairplay-block.md) (hooks `0x40D4E50` / `0x300E030`; mapper not POST) |
| 2026-09-06 | [Window hide + watcher stubs DEFAULT](2026-09-06-window-hide-default.md) |
| 2026-09-06 | [File encoding: UTF-8 no BOM; `mp_bypass*` stays UTF-16-LE](2026-09-06-file-encoding.md) |
| 2026-09-06 | [VS MCP :5050/sse autostart (CodingWithCalvin vs Unofficial)](2026-09-06-vs-mcp-sse-autostart.md) |
| 2026-09-06 | [BSOD 0x10E / CRT memcpy cloak](2026-09-06-bsod.md) |
| 2026-09-06 | [IDA RA cluster — finished analysis](2026-09-06-ida-ra-analysis.md) (IDB store + FairPlay/ESS SEND from autoscan; not per-function `.c`) |
| 2026-09-06 | [RA hasher / JUMPOUT / WindowWatcher / cycle](2026-09-06-ra-hasher-windowwatcher.md) |
| 2026-09-06 | [Xbox FairPlay vs local RA kick](2026-09-06-fairplay-vs-ra.md) (SEND chain folded) |
| 2026-09-06 | [Cheat Engine LUA_PATH / autorun / MCP](2026-09-06-ce-lua-path.md) |

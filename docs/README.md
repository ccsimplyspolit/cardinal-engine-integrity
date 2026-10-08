# Документация AOE4HOOK

`docs/` — **вход**, не полный архив. Канон по темам лежит рядом с кодом, который она описывает (SCAR-контракт у scars, оффсеты у дампов). Сюда не копируем 6000-строчные каталоги нативов.

Игра: Age of Empires IV **16.3.11308.0**. Плагины только в `Documents\AOE4HSettings`.

UI-лабы (лоадер-exe, макет skeet, план порта ImGui) **не в этом дереве**.
Канон: `C:\Users\Lanzerxyz\Documents\GitHub\AOE4HOOK-UI\HANDOVER.md`.
В `InternalInjector` скитовского меню нет (`MenuComputeMetrics` = 0). Не `git add` untracked `skeet loader\`.

---

## В этой папке

| Файл | О чём |
|------|--------|
| [AI_BOT.md](AI_BOT.md) | Вкладка AI BOT: профили, security, локи, Fine-tune, scoring Lua, personality keys, hybrid |
| [AI_SCORING_PIPELINE.md](AI_SCORING_PIPELINE.md) | Relic `ScoringFunctions_*` (multiply), eco-native=0, C++ rank / `__EcoAct`, observatory |
| [AI_SESSION_HANDOFF.md](AI_SESSION_HANDOFF.md) | Сессия Enable: lean-задержка, army lock, контрпик, `WM_SCAR_AI_COMMIT` |
| [decisions/ADR-001-cpp-ai-runtime.md](decisions/ADR-001-cpp-ai-runtime.md) | ADR: C++ думает, SCAR только применяет |
| [decisions/ADR-005-gamesource-unp-humanized.md](decisions/ADR-005-gamesource-unp-humanized.md) | ADR: читаемый слой unpack-disk, не второй Hex-Rays |
| [decisions/ADR-002-patchAT.md](decisions/ADR-002-patchAT.md) | ADR: RA-лаб `patchAT.exe`, не DllInjector |
| [AI_UNIT_CONTROL.md](AI_UNIT_CONTROL.md) | Подгруппы, гарнизон, монахи/реликвии, HUD, краш `AI_LockSquad` |
| [design/MENU_REDESIGN.md](design/MENU_REDESIGN.md) | Новое меню оверлея: утверждённый живой макет v3 (html), токены, полоски статусов, прозрачный сайдбар, растягивание, план переноса в ImGui |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Слои DLL, инварианты, C2668, 3-frame Memory |
| [NATIVE_FEATURES.md](NATIVE_FEATURES.md) | Нативы оверлея: Lobby / Memory (LoginAsync, кулдаун Search, rejoin, реле), ESP, FOW (не SCAR) |
| [MAPHACK.md](MAPHACK.md) | Full Reveal / FOWCTRL1, инжект Release vs fowctrl |
| [UPDATE_GUIDE.md](UPDATE_GUIDE.md) | Ритуал после патча (оффсеты, DualFlag, RA-окно) |
| [RELIC_UNPACK_ALGORITHM.md](RELIC_UNPACK_ALGORITHM.md) | Дисковый крипт: инварианты, rediscover, пайплайн dump→IDA→audit→git |
| [RELIC_RA_EMU.md](RELIC_RA_EMU.md) | Свои хуки в `.text`: слои L0–L6, бан-карта, `ra_emu.py` (не plant RA) |
| [RELIC_DEBUG_ATTACH.md](RELIC_DEBUG_ATTACH.md) | Live x64dbg: HV hold + `--patch-game` + stock exe; hidden rbhost fallback; слоты ≠ dest0 |
| [RELIC_LAUNCH_OPTIONS.md](RELIC_LAUNCH_OPTIONS.md) | Параметры запуска Relic: что делает каждый флаг (16.3.11308.0) |
| [RELIC_COMMAND_LINE.md](RELIC_COMMAND_LINE.md) | Журнал проходов IDA по тем же флагам (60644 + дампы) |
| [internal/SCAR_ANALYSIS](..\README.md) | Аудит SCAR 16.3.11308.0. IDA `660eb217`: IDA_SESSION, [finding](findings/2026-09-24-scar-ida-session.md) |
| [findings/](findings/README.md) | Датированные находки. 2026-09-26: [HV BSOD log](findings/2026-09-26-hv-bsod-log.md), [Power transition](findings/2026-09-26-power-transition.md), [BSOD forensics](findings/2026-09-26-bsod-forensics.md), [KickCtor aux=5](findings/2026-09-26-hv-kickctor-aux5.md), [Параметры запуска](findings/2026-09-26-relic-launch-options.md), [Boot menu off](findings/2026-09-26-bootmenu-off.md), [Cursor logon once](findings/2026-09-26-cursor-logon-once.md), [AC vs board/Windows](findings/2026-09-26-ac-board-windows.md), [HV launch refused, Event 41](findings/2026-09-26-hv-launch-refused-event41.md), [DEVICE_HUNG then `0x3AD6A86`](findings/2026-09-26-present-device-hung-3ad6a86.md). | 2026-09-25: [UNLOAD SCAR+DLL](findings/2026-09-25-unload-scar-dll.md). 2026-09-24: [полный Rebuild](findings/2026-09-24-rebuild-all.md), [SCAR IDA session](findings/2026-09-24-scar-ida-session.md). 2026-09-14: [Opening unlock vs stamp](findings/2026-09-14-open-unlock-vs-stamp.md), [Enable gate empty-only](findings/2026-09-14-enable-gate-empty-only.md), [Сверка `fea27989`](findings/2026-09-14-remote-fea279-reconcile.md), [C++ read vs `.text` integrity](findings/2026-09-14-cpp-read-vs-text-integrity.md), [Re-enable WouldStrip `rva=0x2A45959`](findings/2026-09-14-reenable-wouldstrip-2A45959.md), [Fresh Relic dump 38348](findings/2026-09-14-fresh-relic-dump-38348.md), [Disable keepLock](findings/2026-09-14-disable-keeps-army-lock.md), [STK OnSpawn](findings/2026-09-14-stk-onspawn-no-cpp-relock.md), [STK spawn 4CE0](findings/2026-09-14-stk-spawn-4ce0.md), [Нет запретов «не трогать»](findings/2026-09-14-no-dont-touch-silos.md), [NPT orig-exec ASID 4](findings/2026-09-14-npt-orig-exec-asid4.md), [AMD 56421 GHCB ≠ Type-2 NPT](findings/2026-09-14-amd-56421-ghcb-vs-npt.md), [Patch Game AUTO off](findings/2026-09-14-patch-game-auto-off.md). 2026-09-13: [Cycle 9 wininit 0x50006](findings/2026-09-13-hv-cycle9-wininit-50006.md), [Cycle 9 HV reset](findings/2026-09-13-hv-cycle9-reset.md), [Cycle 8h post-41 usermode guard](findings/2026-09-13-hv-cycle8h-post41-usermode-guard.md), [Cycle 8h leftover NX status=8](findings/2026-09-13-hv-cycle8h-leftover-nx-status8.md), [Goal not complete](findings/2026-09-13-hv-goal-not-complete.md), [Stock x64dbg Attach refused](findings/2026-09-13-stock-x64dbg-attach-refused.md), [Cycle 8h dual-nCR3 gap](findings/2026-09-13-hv-cycle8h-dual-ncr3-gap.md), [Cycle 8h RUN then 41](findings/2026-09-13-cycle8h-run-then-41.md), [Cycle 8h Overlay RUN then 41](findings/2026-09-13-hv-cycle8h-run-then-41.md), [Cycle 8h inject no AUTO](findings/2026-09-13-cycle8h-inject-no-auto.md), [Cycle 8h hold GPU AV](findings/2026-09-13-hv-cycle8h-hold-gpu-av.md), [Rebuild-HvCycle not hitch wait](findings/2026-09-13-rebuild-hv-not-hitch-wait.md), [Event 41 21:06 no kdu](findings/2026-09-13-event41-2106-no-kdu.md), [Map-AfterZppu no sleep](findings/2026-09-13-map-afterzppu-no-sleep.md), [Cycle 8g freeze then 41](findings/2026-09-13-hv-cycle8g-freeze-then-41.md), [Cycle 8e hang after hold](findings/2026-09-13-hv-cycle8e-hold-hang.md), [Canon product-cycle docs](findings/2026-09-13-canon-product-cycle-docs.md), [Product dbg cycle](findings/2026-09-13-product-dbg-cycle.md), [Cycle 8d hang after Relic AV](findings/2026-09-13-hv-cycle8d-hang-after-relic-av.md), [Cycle 8d hold slots=0](findings/2026-09-13-hv-cycle8d-hold-empty.md), [IDA hosts xrefs](findings/2026-09-13-ida-hosts-xref-confirm.md), [Cycle 8c Relic-live map Event 41](findings/2026-09-13-hv-cycle8c-relic-live-map.md), [Hosts trust/telem catalog](findings/2026-09-13-hosts-trust-telem-catalog.md), [DllInjector hosts before APC](findings/2026-09-13-dllinjector-hosts-before-inject.md), [Patch Game tab](findings/2026-09-13-patch-game-tab.md), [Cycle 8 user CR3 + HashRec](findings/2026-09-13-hv-cycle8-user-cr3.md), [Hasher HashRec NPT emulate](findings/2026-09-13-hv-hasher-hashrec.md), [NPT dual-nCR3 vs EPT split](findings/2026-09-13-npt-dual-ncr3-vs-ept-split.md), [New PID RVA vs VA](findings/2026-09-13-new-pid-rva-vs-va.md), [Cycle 6 NPT ret stub](findings/2026-09-13-hv-cycle6-npt-ret-stub.md), [Cycle 5 WW stealth fail-closed](findings/2026-09-13-hv-cycle5-stealth-fail-closed.md), [Always elevate](findings/2026-09-13-always-elevate.md), [Cycle 4 stealth --file abort](findings/2026-09-13-hv-cycle4-stealth-file-abort.md), [Cycle 3 hold hang](findings/2026-09-13-hv-cycle3-hold-hang.md), [Cycle 3 user execute](findings/2026-09-13-hv-cycle3-user-execute.md), [Cycle 3 запускай path](findings/2026-09-13-hv-cycle3-zapuskay-path.md), [Cycle 3 ELF rebuild](findings/2026-09-13-hv-cycle3-elf-rebuild.md), [session 3305282e resume](findings/2026-09-13-agent-session-3305282e-resume.md), [Cycle 3 hold insn](findings/2026-09-13-hv-cycle3-hold-insn-boundary.md), [agent context session rebase](findings/2026-09-13-agent-context-session-rebase.md), [agent context usermode/dbg](findings/2026-09-13-agent-context-usermode-dbg.md), [agent HV preflight STEPS 1-2](findings/2026-09-13-agent-context-hv-preflight.md), [Cycle 1 hold hang](findings/2026-09-13-hv-cycle1-hold-hang.md), [Cycle 1 C-bit window](findings/2026-09-13-hv-cycle1-cbit-window.md), [HV crash-safe breadcrumbs](findings/2026-09-13-hv-crash-safe-breadcrumbs.md), [extra WBM / leftover ESP EFI](findings/2026-09-13-windows-extra-bootmgr-efi.md), [non-map test suite](findings/2026-09-13-hv-nonmap-test-suite.md), [cookie + HostPrep + gate 21](findings/2026-09-13-hv-bsod-cookie-gate-memory.md), [HV dump 0%](findings/2026-09-13-hv-bsod-dump-zero-percent.md), [HV BSOD 15:18 sys](findings/2026-09-13-hv-bsod-1518-sys-hang.md), [Relic Temp DMP](findings/2026-09-13-relic-temp-dmp-empty-window.md), [HV BSOD nested map 26H2](findings/2026-09-13-hv-bsod-nested-map-26h2.md), [HV after Windows 26H2 26340](findings/2026-09-13-hv-windows-26h2-26340.md), [RA delayed kick = silent death](findings/2026-09-13-ra-delayed-kick-silent-death.md), [HV full map + handoff](findings/2026-09-13-hv-full-map-handoff.md), [HV version-agnostic offsets](findings/2026-09-13-hv-version-agnostic-offsets.md), [HV hold before debugger](findings/2026-09-13-hv-hold-before-dbg.md). 2026-09-12: [HV hello 19/20 CLFLUSH](findings/2026-09-12-hv-hello-clflush.md), [HV MiGetPteAddress + ZPPU leave](findings/2026-09-12-hv-migetpte-zppu.md), [HV remap without reboot](findings/2026-09-12-hv-remap-without-reboot.md), [HV AIDA64/DxDiag PTE large](findings/2026-09-12-hv-aida-dxdiag-pte.md), [HV hello rax=2 after 34GiB+MDL](findings/2026-09-12-hv-hello-mdl-rax2.md), [HV hello rax=2 RAM PA>32GiB](findings/2026-09-12-hv-hello-ram34.md), [HV copy_phys hello rax=2](findings/2026-09-12-hv-copyphys-hello-rax2.md), [HV reboot + copy_phys map](findings/2026-09-12-hv-reboot-copyphys.md), [HV copy_phys no mapwin](findings/2026-09-12-hv-copyphys.md), [HV VBS after reboot](findings/2026-09-12-hv-vbs-after-reboot.md), [HV AT catalog 46060](findings/2026-09-12-hv-at-catalog-46060.md), [HV Relic+WW slots=3](findings/2026-09-12-hv-relic-ww-slots3.md), [HV ZPPX hello rax=2 / 4K mapwin](findings/2026-09-12-hv-zppx-mapwin.md), [HV map 17:59 BugCheck 0x1AA](findings/2026-09-12-hv-map1759-1aa.md), [HV map 17:59 query still 8](findings/2026-09-12-hv-map1759-query8.md), [HV planned reboot + verify](findings/2026-09-12-hv-planned-reboot-verify.md), [HV ZPPU ≠ reboot remap](findings/2026-09-12-hv-zppu-remap.md), [HV map 17:50 query=8](findings/2026-09-12-hv-map1750-query8.md), [HV map 16:50 BugCheck 0x109 EFER](findings/2026-09-12-hv-map1650-bsod-109.md), [HV reboot then map 16:50](findings/2026-09-12-hv-reboot-then-map.md), [HV universal / session dest / timers](findings/2026-09-12-hv-universal-session-timers.md), [HV AT-disable](findings/2026-09-12-hv-at-disable-module.md), [HV TSC hide](findings/2026-09-12-hv-tsc-hide.md), [HV Wave 4 handoff / slices](findings/2026-09-12-hv-wave4-handoff-slices.md), [HV MTF / stealth bounds / IDT](findings/2026-09-12-hv-mtf-stealth-idt.md). 2026-09-11: [HV usermode mailbox agent](findings/2026-09-11-hv-usermode-agent.md), [AMD VMCB Clean + dual ASID](findings/2026-09-11-amd-vmcb-clean-asid.md), [NPT stealth ZPPN](findings/2026-09-11-npt-stealth.md). 2026-09-09: [IDA GUI crash](findings/2026-09-09-ida-gui-crash.md). 2026-09-08: [gamesource_unp_humanized](findings/2026-09-08-gamesource-unp-humanized.md). 2026-09-07: [Rebuild overlay](findings/2026-09-07-rebuild-overlay.md), [FPS/crash sel+relock](findings/2026-09-07-fps-crash-sel-relock.md), [Hex-Rays reversed/](findings/2026-09-07-hexrays-reversed.md), [Hex-Rays complete](findings/2026-09-07-hexrays-complete.md). Канон RVA — в UPDATE_GUIDE. Полный индекс — в [findings/README.md](findings/README.md). |
| [PLUGINS.md](PLUGINS.md) | Карта `Documents\AOE4HSettings` |
| [BUILD_ORDERS.md](BUILD_ORDERS.md) | aoe4guides / aoe4world fetch, `BuildOrderTargets`, Layer B blend (`AiEcoBlendBuildOrder`) |
| [SCARTOOLKIT_FULL_PARITY.md](SCARTOOLKIT_FULL_PARITY.md) + `.csv` | Живая таблица STK ↔ оверлей (вкладки, кнопки) |
| [SCARTOOLKIT_NATIVE_PARITY.md](SCARTOOLKIT_NATIVE_PARITY.md) | Снимок 08-28 (stub); полный текст в [archive](archive/SCARTOOLKIT_NATIVE_PARITY.md) |
| [SCARTOOLKIT_PARITY_GAP.md](SCARTOOLKIT_PARITY_GAP.md) | Снимок 08-29 (stub; CSV в archive). Не бэклог |
| [SCARTOOLKIT_CPP_PORT.md](SCARTOOLKIT_CPP_PORT.md) | Сессия порта 08-30 (stub); живое в NATIVE_FEATURES |
| [SCARTOOLKIT_REFUSED_PORTS.md](SCARTOOLKIT_REFUSED_PORTS.md) | Что сознательно не портируем |
| [archive/README.md](archive/README.md) | Устаревшие аудиты / дневники; не канон |

---

## Канон вне `docs/` (не дублировать)

### Автор SCAR / Lua (без исходников DLL)

| Путь | О чём |
|------|--------|
| [CPP_BRIDGES.md](CPP_BRIDGES.md) | Мост C++ → `_G`: WORLD_DATA, SETTINGS, PLAN, AOE4HOOK.*, AV/OOS факты |
| [HYBRID_NATIVE_AUDIT.md](HYBRID_NATIVE_AUDIT.md) | Relic-гейты Fine-tune / Cancel / scoring |
| [WRAPPERS.md](WRAPPERS.md) | XOR-имена, checksum wrappers |
| [CHECKSUM_AUDIT.md](CHECKSUM_AUDIT.md) | Аудит checksum |
| sdk/scar/INDEX.md | Имена нативов Relic (огромный список) |
| [sdk/README.md](..\README.md) | Как обновлять sdk (scardocs, RTTI, dump_vm) |
| scar/AGENTS.md | ScarToolKIT **V4.2** Hex-Rays: `recovered_sln/AOE4_ScarToolKIT`, readable HMAC/HWID/license/attach. `recovered_v42` — только заметки порта |

### UI labs (sibling repo)

| Путь | О чём |
|------|--------|
| `AOE4HOOK-UI\HANDOVER.md` | Лоадер + skeetmenu + menulab. Не оверлей. Порт ImGui только по спросу |

### Плагины на диске

| Путь | О чём |
|------|--------|
| [PLUGINS.md](PLUGINS.md) | Карта `Documents\AOE4HSettings` |
| `Documents\AOE4HSettings\README.txt` | То же, сидится оверлеем |
| `Documents\AOE4HSettings\AI Profiles\README.txt` | Карточка профилей билдера |

### Реверс / патч / FOW (не пользовательский гайд)

| Путь | О чём |
|------|--------|
| [UPDATE_GUIDE.md](UPDATE_GUIDE.md) | Ритуал после патча игры (оффсеты, DualFlag, zoom/radar/ESP AOB) |
| [SPATIAL_BRIDGE.md](SPATIAL_BRIDGE.md) | Stub; живая схема snapshot — [CPP_BRIDGES.md](CPP_BRIDGES.md) §7 |
| [FOW_SAFE_MODE_AUDIT.md](FOW_SAFE_MODE_AUDIT.md) | Stub; продукт Full Reveal — [MAPHACK.md](MAPHACK.md) |
| [NATIVE_FEATURES.md](NATIVE_FEATURES.md) | Нативы оверлея (не SCAR) |
| [CRUCIBLE_PERKS.md](CRUCIBLE_PERKS.md) | Офлайн → Crucible: поиск, изменение и отмена очков талантов |
| [MAPHACK.md](MAPHACK.md) | FOWCTRL1 / maphack |

`_arhive\from_AOE4HOOK\.codex\reverse-port\` — архив портирования, не канон.

---

## Сборка / инжект

Пользовательский путь: `AOE4HOOK\internal\x64\Release\DllInjector.exe` грузит `InternalInjector.dll` **рядом с собой** (APC `LoadLibraryW`). `--patch-game` / `--auto-patch` пишут `[patch_game] auto_run=0` до APC (**AUTO выкл**; leftover 1 сбрасывается). Overlay RUN только вручную + confirm. Product dbg: tools/Run-ProductDbgCycle.ps1. Не передавайте DLL из другого каталога, если рядом уже лежит рабочая копия.

**Один exe для раздачи:** проект `Standalone` → `AOE4HOOK\dist\AOE4HOOK.exe`. PreBuild `internal\Standalone\pack.ps1` собирает эталон **из git-дерева**, не из живой `Documents\AOE4HSettings` (она часто дырявая/старая): `sdk\scar` + `sdk\lua` + `sdk\NativeEspData` + `sdk\aoe4hsettings` + `sdk\ai_personality` + `x64\Release\icons`. При запуске: runtime в `%LOCALAPPDATA%\AOE4HOOK`, сид `Documents\AOE4HSettings` (канон оверлея обновляется с новым payload; `Config` / пользовательские Run-строки не трогает), затем `DllInjector`. Флаги: `--watch`, `--extract-only`, `--force-runtime`, `--force-settings`, `--nowait`.

**Канон внутри DLL.** `InternalInjector.dll` несёт канонические файлы AOE4HSettings (`NativeEspData`, `Scar Scripts\System`, `Scar Scripts\_system`, канонические `Lua Scripts`, `AI Templates` — тот же набор, что `pack.ps1` и `IsCanonSettings`) как RCDATA: `canon_embed.rc` указывает на файлы `sdk\`, и `rc.exe` берёт их текст при каждой сборке. Если рядом с DLL нет `sdk`, при старте (`DocsEnsureLayout`) копии в Documents сверяются со встроенными (хеш и текст без учёта CR): отсутствующие создаются, отличающиеся сначала сохраняются в `_arhive\canon_<дата>` и перезаписываются. `Config`, свои Run-скрипты, `AI Profiles`, `AI Custom Templates` не трогаются. Отключить: файл `Config\keep_documents_canon`. Добавили/переименовали канонический файл — `python tools\gen_canon_embed.py` (тест `test_canon_embed.py` падает, если список устарел).

`Release` и `Release_fowctrl` — **те же фичи**, разный `OutDir` (`x64\Release\` и `x64\Release_fowctrl\`, чтобы собрать, пока игра держит другой файл). Не грузите две `InternalInjector.dll` в один процесс. Залоченную живой игрой DLL перед линковкой переименовывает шаг `MoveLockedTargetAside` (`internal\InternalInjector\prelink_unlock.ps1`): файл уходит в `InternalInjector.dll.old_<дата_время>`, игра продолжает работать на старом образе, линкер пишет новый файл, `LNK1104` не возникает. Старые `.old_*` удаляются при следующей сборке, когда их никто не держит. Новая DLL подхватится при следующем инжекте в новый процесс игры.

**Проверка без игры:** `ci\ci.ps1` — MSBuild `InternalInjector` + `DllInjector` Release|x64, LauncherTests, затем `tests\adversarial\run_host.ps1` (C++ host-тесты + Python). `-Pack` добавляет Standalone, `-Auth` — тесты сервера авторизации. Тулчейн ищется через `vswhere -products *` (BuildTools подходит, Community не обязателен). Lua-тесты требуют `lupa` (`tests\adversarial\requirements.txt`); без него они пропускаются.

По умолчанию `DllInjector` **выходит после успешного APC** (оверлей остаётся в RelicCardinal). `--watch` / `-w` ждёт выхода игры, затем сам выходит.

Подробности FOW-сборки: [MAPHACK.md](MAPHACK.md). Сессия AI BOT: [AI_SESSION_HANDOFF.md](AI_SESSION_HANDOFF.md). Нативы лобби / Memory: [NATIVE_FEATURES.md](NATIVE_FEATURES.md).

## Шапка меню / две вкладки «Память»

- Сайдбар **Лобби → Память** (`DrawNativeOverridesTab`) — личность, Dodge, spoof, reconnect, rejoin, кулдаун Search. **Онлайн → Camera / Radar / ESP** — другая вкладка (`DrawOnlineMemoryTab`, внутренне `Online (Memory)`): камера, радар, ESP, Full Reveal. Это не одна панель.
- Клик по сайдбару в том же кадре попадал в **«Переподключить серверы»** → Relic `LoginAsync` RVA `0x3109420` в главном меню (краш 2026-09-03). Фикс: **3 кадра** игнор кликов; лог `[MEM] Memory tab opened — ignore clicks 3 frames (no LoginAsync)`.
- Шапка `RA S1 A10 F0` = снимок окна Relic AC (`MpBypassGetWindowSnapshot`): `S` = slots, `A` = accum, `F` = flag. Это **не** SCAR / радар / зонд. Красный текст — `slots≠0` или `accum≠0` или `flag≠0`. `S1 A10 F0` = один слот, мелкий accum, **не** пак на кик (`S3 A600` / `S3 A240`).
- Красная таблетка **Офлайн** = режим **Scar Trust** оверлея (`ScarTrust_Offline`), не «не в матче».

## Lobby (Memory) / реле / rejoin / Offline Save

Канон полей и RVA: [NATIVE_FEATURES.md](NATIVE_FEATURES.md). Кратко:

- Личность: aoe4world `profile_id` → Relic `getPersonalStat` (Steam aliases часто пустые). Overlay **WinHTTP ≠** ESS игры (у Relic — WinINet / RLink).
- **«Переподключить серверы»** / Force reconnect = натив `LoginAsync` RVA `0x3109420` (тот же путь, что колокольчик). Не хук HTTP-стека игры.
- **«Пропустить кулдаун поиска»** — локально обнуляет `IsAutomatchBanned` (профиль+`0xCC8`, геттер `0x10C4330`) и expire poll DTO+`0x158`. ESS `OnPollError` `0x3074C50` всё равно может отказать. После реинжекта тумблер снова Off.
- **Регионы реле** (Debug): Retry + авто при TCP drop → `JoinSessionAsync` `0x2EFC430` по login `relayServers` (stride 144). В матче один `relayIP`. Это **не** `StartLogin`. Hop Azure-региона mid-lockstep **не доказан**. Авто может промахнуться: смотрит Windows **TCP**-таблицу, не UDP.
- Официальный Relic `CanReconnect` — пока **жив** процесс. Неофициальный: `Documents\AOE4HSettings\Matches\rejoin_session.json` каждые 2 с + flush из VEH; кнопка **«Неофициальный rejoin»** = `LoginAsync`, без Leave. Это **не** lockstep после смерти процесса. `MatchHeartbeat` `0x7FEB10` — sim tick. `WSADuplicateSocket` не переживает `ExitProcess`. Хост `KillAllDropped` `0x6950F0` / `destructionFrame`.
- **Offline → Save / Load match**: натив `Event_SaveWithName` RVA `0x202B7D0`, скирмиш / vs AI, вкладка Offline. Не ranked world. Журнал `Matches\` — статистика оверлея, не снимок симуляции.
- Баннер статуса Age of Mythology **не** про AoE4; у AoE4 было техобслуживание **2 Sep 2026 21:00 UTC**.

## Чего в `docs/` нет (дыры)

Отдельных гайдов «как пользоваться вкладкой» нет. Сейчас это UI + STK-таблица + куски UPDATE_GUIDE:

- Overlay: ESP, Radar, Camera, Macro, Files, Offline spawn/grant, Send Data to Scar
- Hybrid director (`hybrid_core.scar`) — только внутри [AI_BOT.md](AI_BOT.md) §4 / §10
- Personality bags vs Fine-tune vs Scoring Lua vs Relic production scoring —
  [AI_BOT.md](AI_BOT.md) §6–8 и [AI_SCORING_PIPELINE.md](AI_SCORING_PIPELINE.md)

Сидируемые README в Documents пишет `docs_layout.cpp`; править текст там, не руками в Documents (оверлей перезапишет по маркеру).

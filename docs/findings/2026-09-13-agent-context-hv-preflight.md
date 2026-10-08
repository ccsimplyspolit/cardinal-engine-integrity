# 2026-09-13 Agent context: HV STEPS 1-2 (Preflight + Hypervisor)

**Do not map.** STEPS 1-2 only. No `kdu -map`, no `Map-AfterZppu` success path, no `Start-ZppLoader`, no `sc start Aoe4Hv`, no Relic, no x64dbg, no nested-map. Do not add mailbox op 13. Do not copy hypercall keys / `zpp key=` / PSK into committed docs.

Live this pass (~16:19 local, boot **15:54:23**): dump gate **21**, cookie `in_progress`, `launch_authorized=false`, `last_fix_time=null`, ping **ud**, HypervisorPresent=False, VBS=0, CrashDumpEnabled **0** / AutoReboot **1**, Minidump empty, Relic none. Event 41 **15:54:27**. Hitch copies are still the **15:07** `load_ok` session.

Related: [nested-map 26H2](2026-09-13-hv-bsod-nested-map-26h2.md), [15:18 sys hang](2026-09-13-hv-bsod-1518-sys-hang.md), [dump 0%](2026-09-13-hv-bsod-dump-zero-percent.md), [cookie + gate](2026-09-13-hv-bsod-cookie-gate-memory.md), [non-map suite](2026-09-13-hv-nonmap-test-suite.md), [crash-safe breadcrumbs](2026-09-13-hv-crash-safe-breadcrumbs.md), [26H2 offsets](2026-09-13-hv-windows-26h2-26340.md).

---

## SOURCES / источники (open first, in this order)

Canon for every HV agent. Do not skip to mapper because chat said the next step is `kdu`.

| # | Path | Why |
|---|---|---|
| 1 | `aoe4-hv/docs/cycle-state.json` | `status`, `launch_authorized`, `last_fix_time`, `last_event41`, `last_boot` |
| 2 | `aoe4-hv/docs/_bsod/map-attempt.json` | cookie. `in_progress` + newer `LastBootUpTime` = last map died |
| 3 | `aoe4-hv/docs/STATUS.md` | living checklist (top block is newest) |
| 4 | `aoe4-hv/docs/VMRUN_CYCLE.md` | session order; Event 41 / empty Minidump / torn log |
| 5 | `aoe4-hv/docs/Test-VmrunDumpGate.ps1` | exit **20** not authorized, **21** new crash/hang |
| 6 | `aoe4-hv/docs/Map-AfterZppu.ps1` | ping-pong abort + gate; **do not run** unless user said **запускай** after a real fix |
| 7 | `.cursor/rules/aoe4-hv-bsod-gate.mdc` + skills `aoe4-hv`, `hypervisor-amd-svm`, `hypervisor-analysis` | never resume a `kdu` plan |
| 8 | `aoe4-hv/docs/ZPP_CTL.md` + `hypervisor/include/zpp/hypervisor/mailbox.h` + `tools/zpp_ctl.py` + `tools/zpp_aoe4/` | ping / ZPPX / frozen ops 1-12. Do not paste keys from `ZPP_CTL.md` |
| 9 | `aoe4-hv/docs/decisions/007-universal-usermode-modules.md` | ABI freeze; no Relic strings in VMM |
| 10 | Hitch / loader: `docs/_bsod/hitch-host.log`, `zpp_loader-hitch.log`, `zpp_loader-k.log` (if present), `last-zpp-start.log`, `pre-map-trace.txt`, `%SystemRoot%\Temp\zpp_loader.log` | **mtime vs this boot**. Stale 15:07 is not this SVM |

Do not treat `aoe4-hv` README / old STATUS "Success of the next map" (15:21 TSC-hide) as this boot.

---

## STEP 1 — Preflight / префлайт (verified ~16:19 2026-09-13)

| Check | Live evidence | Pass? |
|---|---|---|
| `LastBootUpTime` | `2026-09-13T15:54:23` | — |
| Event **41** | `15:54:27`, `15:43:51`, `15:41:06`, `15:23:30` | hang/BSOD class |
| Event **6008** | `15:54:34` (unexpected; 1074 last is **14:22:12** planned, not this crash) | hang |
| Minidump | empty. `MEMORY.DMP` still **2026-09-12T17:32:36** | empty != no crash |
| Cookie | `in_progress`, `boot_at_attempt=2026-09-13T15:43:47`, sys **15:51:32** **1074688** B, ping `ud`, `gate_ok=true` **at 15:53**, `CrashDumpEnabled=3` **at that map** | **STOP** |
| `cycle-state.json` | `status=new_bsod`, `launch_authorized=false`, `last_fix_time=null`, `last_event41=2026-09-13T15:54:27` | **STOP** |
| `Test-VmrunDumpGate` | `ok=False` **code=21**. Cookie returns **before** filling `last_event41` — still look up Event 41 yourself | **STOP** |
| CrashControl live | `CrashDumpEnabled=0`, `AutoReboot=1`, `AlwaysKeepMemoryDump=0` | host workaround only |
| HostPrep source | `HostPrep-AtBoot.ps1` writes **0** (not 3). `last-hostprep.log` 15:54:50 is the **old** line (no CrashDump=0). Unelevated `Get-ScheduledTask` = Access denied, not missing | keep 0 |
| Hyper-V / VBS | HypervisorPresent=**False**, VBS status **0** | OK for SVM, **not** "HV dead" |
| CPUs | 32 logical | OK |
| Relic / x64dbg | none | OK |
| `last-zpp-start.log` | 15:53 Map-AfterZppu (Relic none, HV=False, messy python `ud`, sys 1074688) then silence; a later **gate 21** refuse line may be appended by dry-run — that is **not** a new map | torn-NUL was 15:37; this file is not all-NUL now |
| `%SystemRoot%\Temp\zpp_loader.log` | unelevated `Test-Path` / read = **Access denied** (file likely exists). Do not elevate in order to map | copy only after authorized `load_ok` |
| Hitch | `hitch-host.log` mtime **15:10:34**, `zpp_loader-hitch.log` **15:07:29** `load_ok` alloc `FFFFA77D24400000`. **Stale.** 15:53 never left hitch | ignore as "current SVM" |
| `zpp_loader-prev-20260913-155333.log` | rotated at 15:53; alloc `FFFF93FA2F000000`; ends at `copyphys_ok` **no** `load_ok` | leftover / incomplete DriverEntry, not success |

Gate 21 this boot is sufficient. Do not set `launch_authorized=true`. Do not clear the cookie. Do not rebuild "to try the same 15:51 sys again".

---

## STEP 2 — Hypervisor verification / проверка HV (this boot: SVM not resident)

| Check | How | This boot |
|---|---|---|
| ping | `python tools/zpp_ctl.py ping` (VEH; exit 2 = `#UD`) | **ud**, exit 2. Token via `Get-HvPingToken` = `ud` |
| HypervisorPresent | WMI | False — **expected while our SVM hides CPUID HV bit** |
| hello / mbox-ping / query | `zpp_aoe4.exe` **after** ping **pong** + `load_ok` | **do not run as green**. ping ud => same `#UD` class |
| `svme_already` | loader `validate_svm_cpu` if `EFER` bit 12 set (`windows_loader` ~RDMSR `C000_0080`) | not observed this boot (no map). If a map log shows it: leftover SVME, reboot, do not nested-map |

**Never DOUBLE-MAP.** ping **pong** = SVM already resident. HypervisorPresent=False is **not** dead. ping **ud** is **not** green and is **not** proof `EFER.SVME=0` on all 32 CPUs (partial launch / leftover SVME without VMMCALL intercept still `#UD`).

---

## Why 15:18 / 15:51 nested-map caused Event 41 (leftover SVME)

This product intercepts VMRUN from the guest as `#UD` (no nested SVM). A **second KDU `-map`** while any CPU still has `EFER.SVME=1` is not "nested SVM" in the APM sense — it is a second Type-2 bring-up on a CPU that already owns SVME. Loader should print `svme_already`; on 26H2 the box often **hangs** instead (Kernel-Power 41, dump writer **0%**, no minidump). Same class as Pass 18 leftover SVME.

### 15:18 (proven nested-map)

1. **15:07** first map **succeeded**: sys **1073152** B, hitch `load_ok`, `userdtb_off=0 peb=2e0 dtb=28 name=338 links=1d8 pid=1d0 ntos=10.0.26340.0`, `efer=4d01`, 32/32 `cpu_ok`. HypervisorPresent stayed **False** (CPUID HV bit hidden). Ping would have been **pong**.
2. **15:18** second `-map` of a rebuild (**1073664** B, mtime 15:18:15) **while that SVM was live**. `Map-AfterZppu.ps1` then only refused `HypervisorPresent=True`. `last-zpp-start.log` became **all-NUL**. Event 41 **15:23:30**. 26H2 PEB `0x2e0` was **not** the crash.

### 15:18 sys hung again on a "clean" boot (15:37)

First map of the **15:18** image after reboot: last-zpp-start **NUL** at 15:37, no hitch, Event 41 **15:41**. That image is unproven / CLOCK_WATCHDOG-class (DTB brute was `0x2000`; cap is now `kprocess_dtb_scan_max=0x400` in `kprocess_field.h`). Do not map 15:18-sized leftovers.

### 15:51 / 15:53 (leftover SVME + ping-ud hole)

- Sys/ELF rebuilt **15:51:32 / 15:51:31** **1074688 / 1024576** B (`0x400` DTB cap). Cookie: ping **ud**, `gate_ok=true` (`launch_authorized=true` at 15:53), `CrashDumpEnabled=3`.
- `last-zpp-start` 15:53 used **raw** `python ping 2>&1 | Out-String`. Python writes `ud` then extra text; PowerShell wrapped it as `NativeCommandError`. They still treated it as ud and **mapped**.
- Rotated Temp log ends `copyphys_ok` **without** `load_ok` — DriverEntry started, VMRUN path not proven complete. Hitch never refreshed (still 15:07).
- Event 41 **15:54:27**. Dump hung at 0% because CrashDumpEnabled was **3**. Live CrashControl is now **0** (workaround, not an SVM fix).
- ping **ud** did **not** protect this boot: leftover SVME / partial launch does not answer PING. The ping-pong abort only stops **pong**. Cookie `in_progress` + new boot is the durable signal.

`last_fix_time` is still **null**. Cap `0x400` did not save the 15:53 map. **No remap of 15:51 sys.** Next map needs a real SVM-side fix newer than 15:54:27 **and** user **запускай**.

---

## OTHER AGENTS MUST DO / что делать другим агентам

### NEVER DOUBLE-MAP

- [ ] `python tools/zpp_ctl.py ping` → token via `Get-HvPingToken` (not raw `Out-String`)
- [ ] **pong** or anything other than exact `ud` → **STOP**. ZPPU leave 32/32 (unproven on this 32-CPU box) or **reboot**. Never second `kdu -map`
- [ ] HypervisorPresent=False → **not** "no HV". Our hide keeps CPUID bit 31 clear while `EFER.SVME=1`
- [ ] ping **ud** → **not** green, **not** `SVME=0` on 32 CPUs
- [ ] cookie `in_progress` **this boot** (`Test-MapAttemptCookieCrash`: "do not nested-map") → STOP
- [ ] cookie `in_progress` + **newer** `LastBootUpTime` than `boot_at_attempt` → last map died → STOP, keep cookie
- [ ] hitch / `zpp_loader.log` `load_ok` from **this** map only. 15:07 hitch is leftover
- [ ] `Map-Loader2044.ps1` still checks **only** HypervisorPresent — **do not use it** as the product mapper
- [ ] Do not `sc start Aoe4Hv` (identity-NPT probe deleted; 577 DSE anyway)

### Dump gate / Event 41 / cookie / `last_fix_time`

- [ ] Read `cycle-state.json` + `map-attempt.json` **before** any mapper thought
- [ ] Dry-run only: `. docs/Test-VmrunDumpGate.ps1; Test-VmrunDumpGate` (or `Invoke-VmrunDumpGate.ps1`). Expect **21** while cookie is `in_progress` on a newer boot
- [ ] Exit **21** = new crash/hang. Exit **20** = not authorized. Do not "fix" by flipping `launch_authorized`
- [ ] Event 41 after `last_fix_time` (or `last_fix_time` null) = unanalyzed hang. Empty Minidump is normal at CrashDumpEnabled=0 and at 0% hang
- [ ] Event 6008 unexpected + no 1074 = not a planned reboot
- [ ] `last_fix_time` must be a **real** sys/ELF fix **newer** than last Event 41. Null = do not map
- [ ] User word **запускай** from **before** the last Event 41 / reboot is void
- [ ] Clear cookie only after `load_ok` **and** Windows alive minutes (not in the map turn)

### CrashDumpEnabled=0

- [ ] Live `HKLM\SYSTEM\CurrentControlSet\Control\CrashControl`: CrashDumpEnabled **0**, AutoReboot **1**. Never restore **3** (0% dump hang under leftover SVME; AutoReboot never fires)
- [ ] HostPrep must keep **0**. Source `HostPrep-AtBoot.ps1` writes 0. This boot's `last-hostprep.log` line may still be old format — trust live registry + source, not the old log sentence
- [ ] 0 means **no BugCheck code**. Photograph the screen if it sticks. Event 41 is the host signal. BlueScreenView empty is expected

### Smoke (only after an authorized `load_ok` + ping pong)

Do **not** run this list on ping **ud**. After a future authorized map:

1. `python tools/zpp_ctl.py ping` → **pong**, exit 0 (not rax garbage)
2. `out\debug\x86_64\zpp_aoe4.exe hello` then `mbox-ping` (ZPPX hello + mailbox op 3). Expect success / `status=0`
3. `out\debug\x86_64\zpp_aoe4.exe query --name explorer.exe`
4. Frozen mailbox ops 1-12 only (`generic_hv.json`, `mailbox.h`). Do not add op 13 to "make query work"

**query explorer.exe expected fields** (`zpp_aoe4.cpp`):

```
query status=%u cr3=%llx image=%llx name=explorer.exe
```

| Field | Expect |
|---|---|
| `status` | **0** (`um_command_status::success`). **8** = `not_found` (walk/name miss). 1..11 are other `um_command_status` |
| `cr3` | nonzero DTB after SME C-bit strip. **Not** KPTI kernel DTB as `target_cr3` for later stealth |
| `image` | nonzero. If status=0 and image=0, agent may print `query image_rpm=` from Toolhelp — that is usermode fallback, not ELF |
| `name` | `explorer.exe` (mailbox `name[16]`; ELF must use probe name — ADR-007) |

Do not query Relic as first proof. Do not `hold --apply` until explorer query is 0. Do not Attach x64dbg until hold.

`zpp_aoe4.exe selftest` (RFC 8439, no live VMM) is offline-only and does not authorize map.

### Files / RVAs / logs to open

**Windows / gate (this ntos snapshot — do not bake into ELF):**

| Item | Value |
|---|---|
| OS | 26H2 `26340.9482`; ntos file `10.0.26100.9482` |
| PEB | `0x2e0` (`PsGetProcessPeb`) |
| PID | `0x1d0` |
| ImageFileName | lea `0x338` |
| ActiveProcessLinks | `0x1d8` |
| `MiGetPteAddress` | body RVA **`0x4408a0`** (old `0x405850` is other code) |
| `userdtb_off=0` | KVAS off on this box; walk DTB `0x28` after C-bit |
| DTB brute cap | `kprocess_dtb_scan_max=0x400` (not `0x2000`) |

**Logs (mtime vs boot 15:54:23):**

| Path | Role |
|---|---|
| `aoe4-hv/docs/_bsod/map-attempt.json` | cookie |
| `aoe4-hv/docs/_bsod/pre-map-trace.txt` | last Flush line before kdu |
| `aoe4-hv/docs/last-zpp-start.log` | mapper stdout; all-NUL = died mid-write |
| `aoe4-hv/docs/_bsod/hitch-host.log` | host DPC; **15:07 stale** |
| `aoe4-hv/docs/_bsod/zpp_loader-hitch.log` | **15:07** `load_ok` |
| `aoe4-hv/docs/_bsod/zpp_loader-k.log` | K: dual-write (breadcrumbs; may be absent until next map) |
| `aoe4-hv/docs/_bsod/zpp_loader-prev-*.log` | rotated Temp log |
| `C:\Windows\Temp\zpp_loader.log` | live loader; ACL may deny unelevated |
| `aoe4-hv/docs/last-zpp-key.txt` | gitignored; **do not commit / quote** |
| `C:\Windows\Minidump\` | empty this series |
| System log 41 / 6008 / 1074 | times above |

**Do not plant Relic RVAs** (Watcher / `7AB0` / hasher) into the ELF. AT catalog stays in `tools/zpp_at.py` / JSON.

### What to PATCH in Map-AfterZppu if ping-pong abort missing

Current `docs/Map-AfterZppu.ps1` **has** the abort (`Get-HvPingToken` then exit 4). `Start-ZppLoader.ps1` has the same. If a revert / old copy only checks HypervisorPresent, restore **before** any map:

1. Dot-source `docs/HvCrashLog.ps1` (provides `Get-HvPingToken`).
2. Call it **after** `Test-VmrunDumpGate` fails closed, **before** wiping `last-zpp-start.log` / kdu.
3. Do **not** use `$pingOut = & python.exe $ctl ping 2>&1 | Out-String` — stderr `NativeCommandError` on `ud` produced the 15:53 mess and cannot be compared to `^ud$`.
4. Abort on **pong** and on any token that is not exactly `ud`:

```powershell
$ctl = Join-Path $Repo "tools\zpp_ctl.py"
$pingOne = Get-HvPingToken -Ctl $ctl
if ($pingOne -match '(?i)pong' -or $pingOne -notmatch '(?i)^ud$') {
    Write-Output ("[X] ping={0} SVM already resident. ZPPU leave 32/32 first. Nested-map = hang/BSOD." -f $pingOne)
    exit 4
}
```

5. Still refuse `HypervisorPresent` (that is **VBS/Hyper-V**, a different stop).
6. Still refuse cookie / gate 21. Ping abort does **not** replace the dump gate.
7. Patch `Map-Loader2044.ps1` the same way if anyone revives it — today it has **no** ping abort.

### Build artifacts vs live boot

| Artifact | mtime | bytes | vs boot 15:54:23 |
|---|---|---|---|
| `out/debug/x86_64/zpp_hypervisor` | 15:51:31 | 1024576 | **older than this boot**; this is the 15:53 corpse. Do not map |
| `out/debug/x86_64/zpp_loader.sys` | 15:51:32 | 1074688 | same |
| `out/debug/x86_64/zpp_aoe4.exe` | 15:07:16 | 197632 | older than sys; frozen ABI 1-12 so OK for later smoke, not a reason to remap |
| Last **good** mapped sys | 15:07:08 | **1073152** | gone (overwritten). hitch still describes it |
| 15:18 hang sys | 15:18:15 | **1073664** | overwritten by 15:51 |

Rule: do not map a sys whose mtime is **before** the last Event 41 unless `last_fix_time` is set **after** that Event 41. 15:51 < 15:54:27.

Offline `tests/Verify-AmdPort.ps1` PASS does **not** authorize VMRUN.

### Frozen ABI: no op 13; no Relic strings in VMM

`mailbox.h` / `generic_hv.json` / `tests/amd_layout.cpp`:

| op | name |
|---|---|
| 1 | `hello` |
| 2 | `hello_ack` |
| 3 | `ping` |
| 4 | `query_cr3` |
| 5 | `read_virt` |
| 6 | `stealth_arm` (`eax=0xFFFFFFFF` = NOP5 aux, **not** a new op) |
| 7 | `stealth_disarm` |
| 8 | `stealth_clear` |
| 9 | `hide` |
| 10 | `unhide` |
| 11 | `status` |
| 12 | `protect` |

Next unused op is **13**. Adding an op, changing `mailbox_msg` / wire, rotating PSK, or NPT PTE layout = remap tax. Game names/RVAs travel in mailbox `name[16]` + usermode JSON. ELF comments may say "Relic" in English; there must be **no** Relic process string, Watcher RVA, or `7AB0` plant in `hypervisor/` code. `bringup_stage` / `elfst=` breadcrumbs must stay **loader log**, not mailbox op 13.

Do not send ZPPH/ZPPU through `zpp_aoe4`. Overlay inject stays APC.

---

## What this pass did not do

No `kdu`, no mapper elevation, no Relic launch, no x64dbg, no mailbox ABI edits, no hypercall keys written here. Gate dry-run + ping + Event 41 + CrashControl + artifact mtimes only.

STEPS 3+ (map / hold / Relic) stay blocked until Event 41 is fixed in the image, `last_fix_time` is set after 15:54:27, cookie is no longer a dead `in_progress`, and the user says **запускай**.

---

## Live delta ~16:24 (parallel Cycle 1 map -- this agent did not kdu)

A sibling mapped sys **16:20:21** **1075200** B while this note was being written. **Do not nested-map.**

| Check | Result |
|---|---|
| Cookie | `in_progress` **this boot** `boot_at_attempt=2026-09-13T15:54:23` attempt **16:21:40** |
| Gate | **21** `cookie in_progress this boot -- do not nested-map` |
| `last-zpp-start.log` | mapper exit 1 (KDU success), `stage=load_ok` **16:21:43**, hitch_watch_begin, `userdtb_off=0 peb=2e0 dtb=28 name=338 links=1d8 pid=1d0` |
| hitch-host | mtime **16:24:21** (live, not the 15:07 corpse) |
| Event 41 newest | still **15:54:27** |
| HypervisorPresent | still **False** |
| ping **without** `ZPP_HYPERCALL_KEY` | **ud** exit 2 (Pass-25 fallback). Looks identical to "no SVM" |
| ping **with** gitignored `docs/last-zpp-key.txt` | **pong** exit 0 |
| hello / mbox-ping | `mbox-ping status=0` |
| `status` | `status=0 live=1 sites=0 hidden=0` |
| `query --name explorer.exe` | `query status=0 cr3=<nonzero> image=0 name=explorer.exe` then `query image_rpm=<usermode>` |

**This is the ping-abort hole.** `Get-HvPingToken` calls `python zpp_ctl.py ping` with **no** env key. Wrong/missing key -> HV injects `#UD` -> token `ud` -> Map-AfterZppu would **allow** a second `-map` on a live SVM. Cookie `in_progress this boot` is what currently blocks nested-map, not ping.

PATCH `Get-HvPingToken` / Map-AfterZppu (do not print/commit the key):

```powershell
$keyFile = Join-Path $Repo "docs\last-zpp-key.txt"
if (Test-Path -LiteralPath $keyFile) {
    $env:ZPP_HYPERCALL_KEY = (Get-Content -LiteralPath $keyFile -Raw).Trim()
}
$pingOne = Get-HvPingToken -Ctl $ctl
```

Then keep the existing pong / not-`^ud$` abort. After reboot the key file is stale; native `#UD` stays `ud` for any key. Same-boot remap still needs cookie + keyed ping.

Do not quote `zpp key=` / `last-zpp-key.txt` contents in findings. Cycle 1 finding: [2026-09-13-hv-cycle1-cbit-window.md](2026-09-13-hv-cycle1-cbit-window.md). Wait Windows-alive minutes before clearing the cookie. No second kdu.

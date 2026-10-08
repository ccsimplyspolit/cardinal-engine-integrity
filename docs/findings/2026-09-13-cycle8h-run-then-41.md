# Cycle 8h: manual Patch Game RUN then Event 41 (2026-09-13)

User pressed overlay **RUN** (not `DllInjector --patch-game`, not
`[PatchGame] AUTO RUN`). Relic **3832** lived ~3 min after the first RUN,
then host Kernel-Power **41**. **Do not map. Do not inject. Do not RUN.**

Map still `17E25811` (cookie `load_ok_pending_alive` stamp 21:39:35,
`boot_at_attempt=21:05:57`). Newer `LastBootUpTime=22:07:40` = that SVM
died. ping now **ud**. `HypervisorPresent=False`. Minidump empty
(`CrashDumpEnabled=0`). HostPrep capture
`aoe4-hv/docs/_bsod/crash-20260913-220808`.

## RUN left a disk trail

`Documents\AOE4HSettings\Config\config.ini` `[patch_game]` **now**:

| key | value |
|---|---|
| `auto_run` | **1** (was 0 at inject 22:01; saved 22:03:47 / 22:04:19) |
| `user32_body` | 1 |
| `ntdll_qsi` | 1 |

Next APC without rewriting `auto_run=0` will AUTO when the gate is green.
That is the 8g path. Leave the key at 0 before any future inject.

No `[PatchGame] AUTO RUN` line in `aoe4_internal.log` for 3832.

## Overlay log (3832, file survived reboot)

| Time | What |
|---|---|
| 22:01:52 | OverlayBoot / PEB unlink / Present hook. Inject `auto_run=0` |
| 22:01:52 | `[PatchGame] host self-check ok: slots=3 blocked` — **synthetic** unit test, not live WW |
| 22:01:54 | `gpu_fault` skip `present_hr=0` then 22:01:57 RESTORE RTVs. **Before** RUN |
| 22:03:48 | **RUN #1** `neutralize OFF (Patch Game RUN)` user32 **bodies=4 hooked=1** `-nodbg` PEB wipe. No QSI |
| 22:04:02 | **RUN #2** same; ntdll QSI refused (`08060001`) |
| 22:04:18 | **RUN #3** same; QSI refused; retitle=0 |
| 22:04:18 | hidden rbhost `jahjgw.exe` APPCRASH (parallel, not Relic) |
| 22:04:19 | config save (`auto_run=1`) |
| 22:06:36 | last overlay line: WORLD collect n=916. No DXGI. No VEH AV |
| 22:06:08 | 6008 "previous shutdown" (EventLog flush) |
| 22:07:40 / 22:07:45 | boot + Event **41** |

HUD `user32 body ON (4)` is `bodies=4`. Screenshot `0/4` was TSC/ImGui
garbled vowels (same family as Task Manager 16 GHz), not a failed hook.

## Event 1000 vs 41

| Source | Relic 3832 |
|---|---|
| Application **1000** (APPCRASH RelicCardinal) | **none** |
| AOE4HSettings / Temp Relic `.dmp` | **none** |
| Overlay `[CRASH]` / `0x887A0006` | **none** after RUN |
| Kernel-Power **41** | **22:07:45** (this crash) |
| 6008 | previous shutdown **22:06:08** |

WER after boot queued old BlueScreen buckets (`0xDA`/`0x1AA`/`0x109`,
build 26200) plus LiveKernelEvent **141** / **193** on **26340**. Those
are watchdog/TDR-class leftovers with no minidump, not a Relic 1000.

Hidden dbg **did** crash: `jahjgw.exe` 0.0.2.5
`C:\Program Files (x86)\rbhost\release\x64\jahjgw.exe` at **22:04:18**
`c0000005` in `wbemprox.dp64`+`0x23ff`. Dump
`CrashDumps\jahjgw.exe.29080.dmp`. Not stock `x64dbg.exe`. Window RPM
stayed `slots=0` until the hang. `powershell.exe.35948.dmp` 22:06:22 is
an agent shell, not Relic.

## 8g AUTO vs this manual RUN

| | 8g Relic **6732** | 8h Relic **3832** |
|---|---|---|
| How RUN fired | `[PatchGame] AUTO RUN` 20:46:43 after `--patch-game` | User button 22:03:48 / 22:04:02 / 22:04:18. No AUTO log |
| user32 bodies | yes, immediately | yes, **4** on first press |
| `gpu_fault` after RUN | **+0.4 s**, then loop | only at inject 22:01:54; **none** after RUN |
| DXGI | `0x887A0006` DEVICE_HUNG then `0x887A0005` 20:47:06 | **absent** |
| Relic VEH AV | `0x3AD6A86` rdi=`887A0006` | **absent** |
| Last overlay | Present stall / CRASH | WORLD collect 22:06:36 (~2.5 min after first RUN) |
| Host 41 | 20:49:03 (~55 s after AUTO) | 22:07:45 (~3 min after first RUN) |
| Event 1000 Relic | no (host died first) | no |

Same family: usermode hide (user32 bodies + retitle + `-nodbg`) on a
live SVM hold, then host 41 with empty Minidump. This one is **slower**
and **without** the DXGI latch. Do not treat "manual RUN is safer than
AUTO" as proven.

## UI umlauts / Task Manager 16 GHz

`PätchGämé` / `AOÉ4` and Task Manager clocks ~16 GHz are **tsc_hide**
(`VMCB TSC_OFFSET` + APERF/MPERF), not thermal throttle and not a bad
ImGui UTF-8 string. Font is Segoe UI. After this reboot SVM is down, so
those symptoms should be gone until the next map. Do not remap to "fix"
fonts.

## After reboot (live 22:11)

- ping **ud** — SVM **not** alive
- Relic **0**, DllInjector **0**, x64dbg / bwfwcu **0**
- `auto_run=1` still on disk (cleared to 0 after this capture so the next APC cannot AUTO)

## Capture / gate / clocks (this protocol pass)

Elevated `Capture-CrashContext.ps1` first: HostPrep
`crash-20260913-220808` (boot, ping_err) then full
`crash-20260913-221025` (ping **ud**). Gate **21**
`Test-VmrunDumpGate` cookie
`load_ok_pending_alive` attempt_boot `21:05:57` ≠ now_boot
`22:07:40` sys `21:12:19` bytes `1094656` (SHA256 `17E25811…`).

| After reboot (HV dead) | Value |
|---|---|
| Win32_Processor | Max=Current **4501** MHz, Load=0 |
| `\Processor Information(*)\Processor Frequency` | all 32 threads **4501** |
| `% Processor Performance` | ~112 (normal boost, not 16 GHz) |
| System nvlddmkm / 4101 21:55–22:10 | **none** (no TDR event) |
| overlay `aoe4_internal.log` NTFS mtime | **22:04:35** (17 s after RUN #3) |
| last overlay stamp in file | 22:06:36 WORLD collect |
| 6008 hang | 22:06:08 (~11 s after rearm `sites=3` 22:05:57) |

Task Manager «16 ГГц» was **tsc_hide APERF** on the previous SVM session.
After this reboot the counters are honest 4.5 GHz — the lie was SVM, not
thermal throttle. Overlay stamps after the NTFS mtime may be QPC-skewed;
treat 6008 `22:06:08` as the host hang clock.

## Do not

- `kdu` / nested-map / remap `17E25811` (or 8g `7B5C8989` …)
- inject / `--patch-game` / RUN / AUTO (`auto_run` reset to **0** after capture)
- hold dead **3832** / 15720 / 10324 / 19956 / 6732
- Attach / start hidden `jahjgw` / stock x64dbg
- WPM Relic `.text` / arm TimerQ / WW / sibling / 7AB0 / 45E8 / E8 flood
- `stealth --clear --cr3` while Relic lives (22:03:52 cleared **live** hold)

## NPT leftover (this file is overlay/41; dual-nCR3 is the sibling)

[hv-cycle8h-run-then-41](2026-09-13-hv-cycle8h-run-then-41.md): leftover NX
after 3832 death is **not** measurable (SVM off; Relic still mapping at
22:06:36). Identity PFN/NX bits exist only in `stealth_arm_primary_nx`
code, not a dump. hitch `npf=0` is map-time 21:19 only. Rearm `sites=3`
at 22:05:57 overlapped RUN.

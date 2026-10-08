# 2026-09-13 cookie + HostPrep task + gate 21 (mapper off)

Boot **15:54:23**. Event **41** 15:54:27. **6008** 15:54:34 (unexpected
at 15:52:58). No 1074. Minidump **empty**. BlueScreenView: nothing to
open. Ping not taken this pass (gate already 21). **Do not map.**

## Was there a BSOD?

Yes. Cookie `docs/_bsod/map-attempt.json` `in_progress` from attempt
boot **15:43:47** + live `LastBootUpTime` **15:54:23** =
last `kdu -map` died. `Test-VmrunDumpGate` dry-run **exit 21**
(`map-attempt cookie status=in_progress`). `launch_authorized=false`,
`status=new_bsod`. `last-zpp-start.log` is the 15:53 `Map-AfterZppu`
start (sys **1074688** / 15:51:32) then silence — not all-NUL this
time; the cookie is the durable signal after chat rollback.

hitch-host / `zpp_loader-hitch.log` are still the **15:07** `load_ok`
session (stale). No hitch from 15:53 — dump writer hung at 0% before
a live copy.

## 0% dump hang

Live CrashControl now **0 / AutoReboot=1 / AlwaysKeep=0**
(`Set-HvBringupCrashControl`). `HostPrep-AtBoot.ps1` source writes **0**
(do not revert to 3). This boot’s `last-hostprep.log` 15:54:50 is the
**old** log line (no `CrashDumpEnabled=0`) — HostPrep ran, then the
scheduled task vanished.

`Aoe4Hv-HostPrep` **exists** (elevated query: SYSTEM, last **15:54:34**,
result 0, same `HostPrep-AtBoot.ps1`). Unelevated
`Get-ScheduledTask` / `schtasks /Query` = **Access denied** — that is
not “task missing”. Do not run the full host installer to “fix” it.

This boot’s HostPrep log (15:54:50) is the **old** line (no
`CrashDumpEnabled=0`) — source on disk now writes **0**. Live
CrashControl is **0/1/0**. Next boot must keep 0. Autologon /
`Cursor-aoe4-hv` not touched.

## Cursor after reboot

Auto-starts. Task `Cursor-aoe4-hv` LastRun **15:54:46** result 0.
Startup + all-users StartUp + HKCU Run all present.
`last-cursor-autostart.log` 15:54:47.

## 15:18 vs 15:07 (static, not mapped)

`kprocess_dtb_scan_max` is already **0x400** in ELF + loader
(`kprocess_field.h`, `amd_layout` assert). 15:07 sys 1073152
`load_ok`. 15:18 sys 1073664 hung (likely the old 0x2000 DTB brute /
CLOCK_WATCHDOG). Current on-disk sys is **15:51 / 1074688** — already
the 0x400 image — and **that** is what 15:53 mapped after
`launch_authorized=true`. Cap alone did not save that boot.
**No rebuild this pass** (would invite remap). No `kdu`.

## Memory written this pass

Workspace alwaysApply `hh/.cursor/rules/aoe4-hv-bsod-gate.mdc`:
re-read skills + GitHub pointer-only; cookie first; never resume a
`kdu` plan; Cursor must come back; HostPrep task must exist.
Mirrored in `aoe4-hv` SKILL (`.cursor` + `.agents`) and
`aoe4-hv/.cursor/rules/no-launch-unanalyzed-dump.mdc`.

GitHub extras (pointer only, do not install HV):
[incident-triage-harness](https://github.com/madebyaris/advance-minimax-m2-cursor-rules/blob/main/.cursor/skills/incident-triage-harness/SKILL.md),
[bsod-analyzer](https://github.com/sitabanubanu/bsod-analyzer),
[gsd-forensics](https://github.com/jlima004/TaxonomySystem/blob/master/.cursor/skills/gsd-forensics/SKILL.md).

# 2026-09-13 Kernel-Power 41 x3 — 15:18 sys hang, still no minidump

Boot now: **2026-09-13 15:43:47**. Ping **ud**. Relic none. Minidump
**empty**. `MEMORY.DMP` still 12 Sep. CrashControl extra values from
`Enable-CrashCapture.ps1` did **not** survive (AlwaysKeep / CrashOnCtrlScroll
absent after this reboot).

## Three hangs (Event 41 + 6008)

| Event 41 (new boot) | Previous unexpected | What |
|---|---|---|
| 15:23:30 | 15:17:56 | Nested KDU on live **15:07** SVM |
| 15:41:06 | 15:36:40 | First clean map of **15:18** sys (`1073664` B). `last-zpp-start.log` mtime 15:37:15 = **3545 NUL**. hitch-host still 15:10. No `zpp_loader.log` |
| 15:43:51 | 15:42:24 | ~1 min after 15:41 boot. last-zpp-start **not** updated. Enable-CrashCapture / ping ran then; cause not a minidump |

Hang class: Kernel-Power 41, no BugCheck 1001, no dump. SVM wedged
before Windows wrote Minidump. Dump screen **stuck at 0%** so AutoReboot
never runs — see [2026-09-13-hv-bsod-dump-zero-percent.md](2026-09-13-hv-bsod-dump-zero-percent.md).

Host this pass: `Set-HvBringupCrashControl.ps1` (`CrashDumpEnabled=0`).
`Map-AfterZppu.ps1` now calls `Test-VmrunDumpGate` (Event 41 / torn log /
`launch_authorized`). Do not map this boot.

## 15:07 vs 15:18 sys

15:07 **worked**: `sys bytes=1073152` mtime 15:07:08, hitch
`load_ok` `peb=2e0 dtb=28 name=338`. That file is **gone** (overwritten).

Current `zpp_loader.sys` **1073664** B mtime **15:18:15** (rebuild while
the 15:07 SVM was still resident). Do **not** map this image again until
a new ELF/sys is built with DTB brute capped at `0x400` and a flushed
`docs/_bsod/pre-map.txt` exists **before** KDU.

## Relic Temp DMP (not this hang)

`%TEMP%\RelicCardinal.DMP` 15:12:12 is a **user snapshot** (`80000003`,
50 s, empty RA window, original Enqueue). Separate finding.

## Logging fix (source, not mapped)

- `Map-AfterZppu.ps1`: flushed `pre-map.txt`; **rotate** Temp loader log
  (do not delete); wait hitch-host before KDU.
- Hitch copies `zpp_loader-live.log` each second.
- ELF/loader DTB brute `kprocess_dtb_scan_max=0x400` (not 0x2000).

Do not `sc start Aoe4Hv`. Do not map this boot. Rebuild first, then one
map only when ping is `ud`.

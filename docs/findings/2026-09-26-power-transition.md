# 2026-09-26 — reason for every shutdown and restart

The boot that is running now (`2026-09-26T14:57:05`) ended the previous one
because **wininit** restarted the machine: **lsass.exe** died with
`-1073740940` (`0xC0000374` heap corruption). Event 1074 `0x50006`.
Registry `ShutdownTime` is `14:56:15`. `DirtyShutdown=1`.

Earlier the same afternoon, two resets had Event 41 `BugcheckCode=0` and
Event 6008 (14:31:04 and 14:35:49) with no recorded bugcheck. Report:
`aoe4-hv/docs/last-power-transition.txt`.

## What records the next one

| When | Where |
|---|---|
| Every 30s, and across a hard reset | `docs/_bsod/last-alive.txt` (task `Aoe4Hv-Alive`, SYSTEM, running). Also `C:\Windows\Temp\aoe4-last-alive.txt`. |
| Windows begins a shutdown or restart | Same task receives `Win32_ComputerShutdownEvent` and writes `docs/_bsod/shutdown-leaving.txt` (1074 process, reason code, kind). |
| Next boot | HostPrep runs `Collect-PowerTransition.ps1 -Phase Boot` → `docs/last-power-transition.txt`. Verdict is `bugcheck`, `critical_process`, `unexpected_reset`, or `planned_shutdown`. |
| Bugcheck while the new HV is mapped | CMOS `ZPBC` plus kernel dump after reboot (`ZPPBUGCK1`, already built). Triple-fault VMEXIT stores `ZPBS` / `ZPBI`. |
| lsass / csrss / wininit / services | Full user dump in `D:\AOE4HV-DUMP\wer` (already set). |

Fast startup is off (`HiberbootEnabled=0`) so Shut down is a full shutdown
and Event 6006/6008 stay meaningful. Shutdown Event Tracker is on
(`ShutdownReasonOn=1`), so a manual power-off asks for a reason.
`LastAliveStamp` interval is 60s.

Kernel dump type 2 is in the registry and still takes effect on the next
boot. A crash before that reboot still leaves last-alive, 1074/41/6008, and
the lsass dump. It does not yet leave `MEMORY.DMP`.

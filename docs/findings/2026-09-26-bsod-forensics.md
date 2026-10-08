# 2026-09-26 — BSOD forensics: kernel dump, events, CMOS

Live before the change: `CrashDumpEnabled=0`, `C:\Windows\Minidump` empty,
`MEMORY.DMP` still `2026-09-12` (3.2 GiB). C: pagefile 4096 MiB, D: 12288 MiB.
RAM 31.1 GiB. testsigning **No** (left off; unsigned sys stays on the mapper).

## What the journals already had

| Time | Event | Meaning |
|---|---|---|
| 14:32:42 | Kernel-Power **41** | `BugcheckCode=0`, all parameters 0. Not a saved bugcheck. Unexpected reset. |
| 14:37:36 | Kernel-Power **41** | Same, `BugcheckCode=0`. |
| 14:55:12 | User32 **1074** `0x50006` | `wininit` restarted because **lsass.exe** died. Status `-1073740940` = `0xC0000374` `STATUS_HEAP_CORRUPTION`. |
| 14:57:16 | EventLog **6008** | Unexpected shutdown after that restart. |

No Event **1001** (that is written only when a kernel dump exists). WHEA Errors
and Operational were already enabled. `Microsoft-Windows-Kernel-Power/Diagnostic`
was **disabled**. System log was 20 MiB. `C:\Windows\LiveKernelReports\WATCHDOG`
already has small dumps (newest `2026-09-26` 01:31, ~4.5 MiB) — those are live
watchdogs, not the 14:32 reset.

`CrashDumpEnabled=0` was HostPrep on purpose: with SVME still on, the Windows
dump writer sat at **0%** and AutoReboot never ran
([2026-09-13 dump at 0%](2026-09-13-hv-bsod-dump-zero-percent.md)).

## What is set now

`docs/Set-BsodForensics.ps1` (HostPrep and `Set-HvBringupCrashControl.ps1`
call it). Registry, needs **one reboot** before the kernel dump stack uses it:

| Setting | Value |
|---|---|
| `CrashDumpEnabled` | **2** (kernel) |
| `DedicatedDumpFile` | `\??\D:\AOE4HV-DUMP\dedicated.dmp` |
| `DumpFileSize` | **24576** MiB |
| `AlwaysKeepMemoryDump` | 1 |
| `AutoReboot` / `LogEvent` / `Overwrite` | 1 |
| Pagefile | C: 16384 MiB, D: 12288 MiB |
| LocalDumps full | `lsass.exe`, `csrss.exe`, `wininit.exe`, `services.exe` → `D:\AOE4HV-DUMP\wer` |
| Logs | System **128 MiB** (verified), Application **64 MiB**, WHEA 64 MiB, Kernel-Boot 32 MiB. `Microsoft-Windows-Kernel-Power/Diagnostic` left **disabled**: `wevtutil sl /e:true` hung past 15s |
| `bcdedit bootlog` | Yes (`C:\Windows\ntbtlog.txt`), verified |

Relic user dumps stay on `Enable-CrashCapture.ps1`.

BlueScreenView still reads **Minidump only**. A kernel dump is
`C:\Windows\MEMORY.DMP`. `Capture-CrashContext.ps1` writes `events.txt`,
copies small LiveKernelReports, and runs `cdb` on a `MEMORY.DMP` from this boot.

## SVM and the 0% hang

KDU frees the loader image when `DriverEntry` returns
`STATUS_INSUFFICIENT_POWER`. The bugcheck callback is a leaked nonpaged
executable page (`windows_loader/src/bsod_arm.cpp`), not code in the sys image.

On bugcheck it writes code + parameters into CMOS `0x58..0x7F` (magic `ZPBC`).
After `load_ok` it may `VMMCALL` leaf `0x133A`. The hypervisor writes the same
record and `leave_svm` **without** taking the hidden-page lock, so this CPU
runs the dump writer with SVME clear. The opcode `0F 01 D9` is patched into
that page at runtime; the built sys has **zero** occurrences.

Shutdown / invalid-VMCB exits (when intercepted) store magic `ZPBS` / `ZPBI`
and guest RIP in the same CMOS bytes. INIT is not touched (it freezes other
CPUs during a bugcheck).

Next map's `DriverEntry` harvests CMOS into
`docs/_bsod/bugcheck-cmos.log` (fallback `C:\Windows\Temp\aoe4-bugcheck-cmos.log`).

`out\debug\x86_64\zpp_loader.sys` rebuilt this turn contains `ZPPBUGCK1`.
`Map-AfterZppu.ps1` / `Start-ZppLoader.ps1` exit **22** if `CrashDumpEnabled`
is not 0 and the sys lacks that marker.

This boot's kernel still has the old dump type cached until reboot. Do not
treat a crash before that reboot as proof the new policy failed.

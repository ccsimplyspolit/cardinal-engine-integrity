# 2026-09-13 dump stuck at 0% — three Event 41, no minidump

Boot now: **2026-09-13 15:43:47**. Ping **ud**. Relic none. Do **not** map.

## What the screen is

BugCheck runs, then Windows dump writer sits at **0%**. Under leftover
SVME / broken NPT the dump I/O never finishes, so:

- AutoReboot never fires (user power-cycles)
- `C:\Windows\Minidump` stays empty
- no Event 1001
- only Kernel-Power **41** + EventLog **6008**

That is why a ping=`ud` reboot looked "clean" and the mapper ran again.

## Timeline (this afternoon)

| Time | What |
|------|------|
| 15:07 | first 26H2 map `load_ok` (peb=`0x2e0`) hitch still on disk |
| 15:17:56 | unexpected (nested `-map`) → Event 41 15:23:30, boot 15:23 |
| 15:18 | `zpp_loader.sys` rebuilt (this is the crashing image) |
| 15:37:15 | `last-zpp-start.log` 3545 **NUL** bytes — mapper died mid-write |
| 15:36:40 | unexpected → Event 41 15:41:06 |
| 15:42:24 | unexpected (0% hang / second power cycle) → Event 41 15:43:51, boot 15:43:47 |

`zpp_loader.log` missing this boot. Hitch copy still 15:07 only.
Minidump none. `MEMORY.DMP` still 12 Sep.

## Loop that must stop

`Map-AfterZppu.ps1` checked ping/`HypervisorPresent` and **skipped**
`Test-VmrunDumpGate`. Empty Minidump + ping `ud` was treated as a
green host. Gate now refuses Event 41 after `last_fix_time`, torn
start log, and `launch_authorized=false`.

Host: `Set-HvBringupCrashControl.ps1` sets `CrashDumpEnabled=0` so a
future BugCheck can AutoReboot instead of freezing at 0%. Relic WER
user dumps stay in `Documents\AOE4HSettings\Dumps\wer`.

**2026-09-13 16:03:** `HostPrep-AtBoot.ps1` was forcing Dump=**3** at
every boot, so the 0 did not survive 15:54. HostPrep +
`Install-VmrunCycleHost.ps1` now persist **0**. Not an SVM fix.

Do not map `out/debug/x86_64/zpp_loader.sys` **15:18:15** until that
image is fixed. 15:07 hitch is the last `load_ok`.

# 2026-09-13 CrashDumpEnabled=3 after reboot — 0% hang not fixed

Live **16:01**. Boot **15:54:23**. Event **41** 15:54:27, **6008** 15:54:34.
No **1074**. Minidump **empty**.

CrashControl now: **CrashDumpEnabled=3**, AutoReboot=1, AlwaysKeep=0.
`Set-HvBringupCrashControl` (0/1/0) did **not** survive this reboot.
So the dump writer at 0% is **not** fixed. Next BugCheck with 3 will
try to write a minidump again and can hang under SVME.

`launch_authorized=true` at 15:53 + map of 15:51 sys is the loop.
Cookie `docs/_bsod/map-attempt.json` now in_progress from boot 15:43.
Do not map.

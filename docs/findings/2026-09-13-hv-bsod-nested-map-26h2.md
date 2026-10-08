# 2026-09-13 BSOD after 26H2 map — nested KDU, not PEB 0x2e0

Boot after crash: **2026-09-13 15:23:26**. Event **41** Kernel-Power
15:23:30 (unexpected shutdown). **No** Event 1001, **no** new minidump
(`CrashDumpEnabled=3`, `Minidump` empty, `MEMORY.DMP` still 12 Sep).
Fits CLOCK_WATCHDOG / hang-reboot, not a completed BugCheck write.

Do **not** map again this boot until ping is `ud` **and** the ping-gate
in `Map-AfterZppu.ps1` is used. Do not `sc start Aoe4Hv`. Do not nested-map.

## What actually ran

First map **15:07** (`Watch-ZppHitch` + `zpp_loader-hitch.log`) **succeeded**:

- `copyphys_*_ok`, `load_ok`, `efer=4d01`, 32/32 `cpu_ok`
- discover **worked on 26H2 live**:
  `userdtb_off=0 peb=2e0 dtb=28 name=338 links=1d8 pid=1d0 ntos=10.0.26340.0 ntbuild=26340`
- KVAS off (`userdtb_off=0`) is valid here; PEB is **0x2e0**, not 0x550
- hitch: `exit=7c` MSR only, `npf=0`, `vmcall_skip`; watch ended 15:10:34
- HypervisorPresent stayed **False** (CPUID HV bit hidden)

`docs/last-zpp-start.log` mtime **15:18:48**, 3177 **NUL** bytes — mapper
started a **second** write then the box died. Hitch copy was not refreshed
(still the 15:07 `load_ok` log). Reboot 15:23.

## Cause

Nested KDU `-map` on a live SVM. `Map-AfterZppu.ps1` only refused
`HypervisorPresent=True`. This product keeps that bit off, so the script
treats a resident SVM as a clean host. Second `-map` with `EFER.SVME`
already set → hang / Kernel-Power 41. Same class as prior
`svme_already` notes.

26H2 offsets were **not** the crash. The 15:07 image already handed off
the live ntos layout.

## Fix (source)

`docs/Map-AfterZppu.ps1` and `docs/Start-ZppLoader.ps1` now abort unless
`python tools/zpp_ctl.py ping` is native **`ud`**. `pong` = ZPPU leave
32/32 first.

## Next (after this boot)

Ping is `ud` again (SVM died with the reboot). One map only. Do not map
twice. Do not start Relic as first VMRUN. Dump still 15843 until a new
minidump appears.

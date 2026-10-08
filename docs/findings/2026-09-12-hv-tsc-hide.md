# HV TSC hide slice (aoe4-hv)

Date: 2026-09-12. Tree: `aoe4-hv`. Not overlay. No Relic plant. Mapped 15:21 this boot (see 2026-09-12-hv-tsc-hide-map.md).

## What

`svm_slices::tsc_hide` on. Other named slices stay 0. `svm_bringup` stays true.
Not the death bundle. Not CPUID intercept. Not global RDTSC/RDTSCP intercept.

Guest RDTSC/RDTSCP see hardware `guest_TSC = physical + VMCB.TSC_OFFSET`.
The VMM writes `TSC_OFFSET = -shared_offset`. `commit_vmexit_tsc` adds
`min(handler, raphael_tsc_extra_cap)` on each vmm_code exit except APERF
(`keep_offset`) and HLT (idle decay only). Usermode CPUID�RDTSC probe path
still adds `raphael_tsc_extra_hw` (dead on bring-up: CPUID intercept off).

Leftover: loader measures RDTSC-CPUID-RDTSC without VMMCALL, plants
`msrpm_handoff.tsc_cpuid_leftover`. ELF copies into `tsc_roundtrip[]` and
seeds the shared offset before first VMRUN.

APERF/MPERF (`0xE7`/`0xE8`): MSRPM R+W; handler subtracts `tsc_offset`.

Constants: `tsc_raphael.h` target 56, extra_hw 400, extra_cap 4000.
Intel 220/920/3400 stay rejected.

APM 15.15.3 bit 0 (I) includes TSC offset; `vmcx().tsc_offset` dirties I.

## Honest gap

Inner SMCA 0x7C (GIF=0, skip `vmm_code`) does not update `TSC_OFFSET`.
That hitch remains visible in guest TSC.

## Verify

`build_windows.bat` + `tests/Verify-AmdPort.ps1` **ALL PASS** 2026-09-12 14:59
(ELF `zpp_hypervisor` + `zpp_loader.sys` rebuilt together). Offline only:
offline Verify 14:59; mapped 15:21; ping 8/8; ZPPX hello ok.

# HV map: TSC-hide ELF on clean boot

Date: 2026-09-12. Tree: `aoe4-hv`. Not overlay. No Relic plant.

## Why this map

User: map and check everything. Previous Pass 25 (boot 2026-09-11 09:18) is gone.
This boot: `LastBootUpTime=2026-09-12T14:54:47`. HypervisorPresent=False.
Relic not running. No new minidump visible. ELF+sys rebuilt 14:59
(`svm_slices::tsc_hide=1`, Wave 4 key/leftover). Verify-AmdPort ALL PASS.

Not a same-boot remap. Leftover SVME from Pass 25 died with the reboot.

## Gate

`launch_authorized` set for this user map. Mapper: `Start-ZppLoader.ps1`
(kdu -map). Not `sc start`. Not CPUID intercept. Not `svm_bringup=false`.

## Map result (2026-09-12 15:21)

`Start-ZppLoader.ps1` / kdu `-map` `out\debug\x86_64\zpp_loader.sys`.
Not `sc start`. Relic closed. Same boot as 14:54:47.

Loader: `zpp key=53e50527fa8d666 leftover=135`. `load_ok`, 32x `cpu_ok`,
`keep_va`, `vmcall_skip`, `hitch_watch_end efer=d01` (guest RDMSR hides SVME).
Hitch: `npf=0` `inner=0` `slow=0` `full7c~2e6` = APERF/MPERF MSRPM tax
on `tsc_hide`, not inner-SMCA miss.

`cycle-state.json`: `launch_returned`, `launch_authorized=false`. **Do not remap**.

## Usermode checks (15:26-15:28)

Set `ZPP_HYPERCALL_KEY=0x53e50527fa8d666` (15 hex digits). Fallback
`0x9C7A31E5` is the old Pass 25 image only.

| Check | Result |
|---|---|
| `python tools\zpp_ctl.py ping` x8 | **8/8 pong** |
| `python tools\zpp_vmmcall_ping.py --loops 8` | first run `#UD` (stub packed only low 32 bits of RBX); after packing full `imm64` **8/8** `host_tsc=0` qpc_med=24 |
| `python tools\zpp_tsc_bench.py` | CPUID intercept still off: ZPPT CPUID leaf eax=0; `rdtsc-cpuid(0x1)` med=180 (native band vs leftover 135) |
| `zpp_aoe4.exe selftest` | mailbox=4096 rfc8439=ok |
| `zpp_aoe4.exe hello` / `mbox-ping` | **ok** `hello cr3=... mbox-ping status=0` |
| HypervisorPresent | False |
| RelicCardinal | not running |
| hide / protect / ZPPU / ranked Relic | **not run** |

## Honest gaps

- Idle under this image is minutes, not Pass-23 100 min.
- Probe-hide hits stay 0: no CPUID intercept, so ZPPT-via-CPUID is dead by design.
- Inner SMCA `0x7C` still skips `vmm_code` (no TSC_OFFSET update on that path).
- `zpp_vmmcall_ping.py` must plant the full 64-bit key; low-32 truncation is `#UD`.


# HV Wave 4: handoff key, #MC stash, svm_slices (aoe4-hv)

Date: 2026-09-12. Tree: `aoe4-hv`. Not overlay. No Relic plant. Not mapped.

## What

0911-refactor deferred list, coded. `svm_bringup` stays true. Slices all false. ELF + `zpp_loader.sys` rebuilt together (handoff tail).

| Item | Code |
|---|---|
| Per-boot hypercall key | `msrpm_handoff.hypercall_key`. Loader RNG in `zpp_after_elf_load`. Log `zpp key=`. PONG `R8=0`. Tools: `ZPP_HYPERCALL_KEY`. Fallback `0x9C7A31E5` if key=0 (Pass 25 live). |
| #MC | Product IDT vector 18 = `host_mc_entry` -> stash `mc_status`/`mc_addr` -> `host_halt`. Bring-up does not LIDT (`private_idt=false`). |
| APERF/MPERF | Handler already subtracts `tsc_offset`. MSRPM R+W only if `svm_slices::tsc_hide` (false). |
| Split mega-flag | `svm_slices.h`: host_page_table, mtrr, cpuid_intercept, tsc_hide, protect_module_at_map, unmap_va, loader_vmmcall, private_idt. All 0. |
| tsc leftover | Loader measures RDTSC-CPUID-RDTSC without VMMCALL; plants `tsc_cpuid_leftover`. ELF copies into `tsc_roundtrip[]`. |
| Hello ZPPX | Mailbox is in this ELF. Live Pass 25 Hello stays `#UD` until remap. |

## Verify

`build_windows.bat` + `tests/Verify-AmdPort.ps1`. Do not remap this boot.

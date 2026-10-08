# HV MTF kind leak / stealth bounds / IDT (aoe4-hv)

Date: 2026-09-12. Tree: `aoe4-hv`. Not overlay. No Relic plant. Not mapped.

## What

Canon (NPT_STEALTH, APM VMSAVE, 0911-refactor-pass): dual-nCR3 stealth copy must be whole instructions; MTF close must not depend on a single overwritten kind slot; guest FS/GS bases are per-CPU VMSAVE state, not a CPU0 MSR snapshot.

- `handle_monitor_trap`: still idempotent hijack/shadow/hidden close. Self-hidden kernel write no longer shares kind 7 with ZPPM; `self_hidden_mtf_gpa[cpu]` survives nested NPF. Next kernel store NPFs again and re-arms MTF. Stealth/shadow nCR3 restore is flag-based, not kind-based. Hijack NX restore invalidates NPT TLB.
- `stealth_arm`: `insn_starts_at` (left-to-right 15-byte window) + `insns_cover_exact` before the patch. Walk is cloned before the stub is written. Mid-instruction / torn tail = refuse (guest `#UD` otherwise).
- Refactor: `fill_host_idt` is the only IDT builder (product `svm_host_idt`); deleted unused `host_idt[]`. `context_set_gpr` with `context_gpr`. `msrpm_physical` / `vmcs::msrpm`. Removed dead `ia32_fs_base`/`ia32_gs_base`.

## Verify

`build_windows.bat` + `tests/Verify-AmdPort.ps1` (RFC 8439 + insn_boundary + AMD objdump). Pass 25 stays the live map. Hello ZPPX still `#UD` until reboot + launch word.

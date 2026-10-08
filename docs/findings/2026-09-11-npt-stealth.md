# NPT stealth checks (ZPPN)

Date: 2026-09-11. Tree: `aoe4-hv`. Not overlay. No Relic plant.

## What

AMD NPT cannot do execute-only. `ZPPN` (`0x5A50504E`) splits views:

- identity nCR3: original PFN + NX (`trap_execute`) -- hasher **reads**
  original bytes, so checks still look enabled
- private nCR3 (this vCPU only): stub PFN
  `ENDBR64; mov eax, imm; ret` (or JMP to a guest handler)

Do not flip the shared identity PTE to the stub (other CPUs would read
the patch). Same-page SimpleSvmHook caveat still applies for the few
insns the stub nCR3 is live.

HV does **not** contain Relic RVAs. Overlay / `zpp_ctl stealth --target`
passes VAs later. No Watcher / 7AB0 / hasher plant from this module.

## Files

- `hypervisor/src/hypervisor/npt_stealth.cpp`
- `capture_config.h` leaf `hypercall_cpuid_stealth`
- `tools/zpp_ctl.py stealth`
- `aoe4-hv/docs/NPT_STEALTH.md`
- ADR-002 appendix

## Not done this turn

- Not mapped (`launch_authorized=false`). Do not Relic-first.
- Overlay does not yet enumerate check VAs into ZPPN.

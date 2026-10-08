# AMD VMCB Clean + dual ASID (aoe4-hv)

Date: 2026-09-11. Tree: `aoe4-hv`. Not overlay. No Relic plant. Not mapped
(`launch_authorized=false`). Pass 25 stay as-is this boot.

## What was wrong

Raphael has `CPUID.8000000A EDX.VmcbClean`. Bring-up resume did:

```
tlb_control = pending ? keep : 00h
vmcb_clean = 0xffffffff
```

APM 15.15.2: software must **clear** the bit for any control field it
wrote. `#VMEXIT` does not write the clean field back.

| Write | Clean bit | If resume forces all-clean |
|---|---|---|
| `nCR3` / `NP_ENABLE` | NP (4) | hardware may keep the **old** nested CR3 |
| `#DB` intercept (`set_mtf`) | I (0) | TF may never `#VMEXIT` |
| `guest_asid` | ASID (2) | dual-nCR3 view switch ignored |

ZPPN/ZPPI then look armed in software and still execute the original
page. Kind 9 also opened X=1 on the **shared** identity PTE for one
insn (other CPUs could run the real check).

ZPPI `create_shadow_page` copied `epdpt` (product 2 MiB PML4 0) and
always rewrote `shadow_epml4[0]`. Bring-up identity lives in
`identity_pdpt[pml4]`; GPA >= 512 GiB is not PML4 0.

ASID 1 on both identity and stealth nCR3 required a TLB flush on every
stub fire. APM 15.16: one ASID per nested table; NASID=32768 here.

Remote `invalidate_ept` during a guest VMRUN set `tlb_flush_pending`,
then the exit path cleared pending unconditionally so the 03h could be
dropped.

## Fix (coded, not mapped)

- Named clean bits in `vmcb.h` (Figure 15-4). `vmcs` clears I/NP/ASID/CR
  on those writes. Bring-up resume no longer assigns `vmcb_clean_all`.
- SMCA inner still all-clean when the path only touched uncached RIP/RAX.
- ASID 1 identity / 2 ZPPN / 3 ZPPI when `svm_nasid > 3`. View switch =
  nCR3+ASID, no TLB flush. Table edits use `TLB_CONTROL=01h`.
- `tlb_flush_gen`: consume a flush only if gen did not bump in-guest.
- ZPPI PDPT from the live `epml4[pml4]` target (`identity_pdpt` or `epdpt`).
- Kind 9: stealth copy + TF, never shared identity X=1.

Do not remap this boot. Next map = reboot + the launch word. Not
`svm_bringup=false`. Not Relic first. Not intercept CPUID.

Canon: `aoe4-hv/docs/STATUS.md`, `NPT_STEALTH.md`, ADR-002.

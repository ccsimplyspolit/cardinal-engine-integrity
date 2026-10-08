# NPT orig-exec ASID 4 wired to pick_view (2026-09-14)

Product Relic hold split-view on AMD SVM/NPT. Textbook «RAX=1 vs RAX=2»
is **not** Relic ABI. `RA_Hasher` `0x3E57050` returns 64-bit wyhash.
`--eax 1` and stub `RA_Integrity_45E8` `0x3E545E8` stay forbidden.

**Do not map.** `cycle-state.json` `launch_authorized=false`. Corpse
`A67B068F`. ping **ud**. Gate 20. User **запускай** still required.
Disk after Verify-AmdPort: sys **`2D14EF01`** ELF **`97FF02CF`**
`zpp_aoe4` **`DF3831E7`** (00:53:15). Orig-exec leaf **W=0**. Hitch
`orig=`. Not mapped. Prior disk `E8B2EBD5` (00:38) is superseded.

## What landed (source + offline tests)

`handle_stealth_npf` calls `stealth_npf_pick_view`:

| View | nCR3 / ASID | Who |
|---|---|---|
| none | identity 1 | data read (no NPF) |
| stub | stealth 2, copy PFN | owner execute / write |
| orig_exec | orig 4, original PFN R=1 W=0 X=1 | Guest_CR3 != owner_cr3 |

Missing orig/stealth walk is fail-closed: inject `#GP` (CPL3) / `#PF`
(CPL0). Must **not** `return false` into `open_guest_gpa` (that would
set identity X). Orig-exec leaf is **W=0** so a store cannot dirty the
hasher PFN. `handle_stealth_npf` re-runs `orig_ensure_walk` before the
view switch. Hitch ping (mailbox op 3, not a new op) appends `orig=`
(foreign/kernel orig-exec NPF count). `INVLPGA` still unused (GVA, not NPT).

Layout asserts: `asid_orig==4`, `mtf_kind_stealth_stub==8`,
`mtf_kind_stealth_orig==9`, `mtf_kind_stealth_foreign==12`.

Hold sites unchanged: Enqueue `0x3DD2550` / KickCtor `0x3E691F4` `eax=0`;
hasher HashRec `0xFFFFFFFE`; TimerQ skip; no OS DLL GPA.
HV `stealth_hold_rva_forbidden` refuses 45E8 / TimerQ / dest pages.

Plan (offline, no map this note): `handle_stealth_npf` → `stealth_npf_pick_view`;
layout `asid_orig==4` / kinds 8/9/12; ADR-002 + UPDATE_GUIDE + this finding;
`Verify-AmdPort` 0 at 00:53 on `2D14EF01`. Mermaid in
NPT_STEALTH.md uses orig **W=0**,
not the textbook RWX box.

Source after 00:53: `pick_view` **none** re-arms identity NX.
`open_guest_gpa` and `resume_with_mtf` refuse stealth GPAs. NPF dispatch
runs `handle_stealth_npf` before hijack/shadow/hide. Hide/ZPPI/hijack
must not `identity_access` a hooked 4K. Identity hooked leaf is
`identity_hold_nx` (W=0), not `trap_execute` (W=1). `cycle-state.json`
`disk_matches_source=false` — Map-AfterZppu / Start-ZppLoader / Cycle9-HvOnly
exit 6 until rebuild (`Rebuild-HvCycle` also sets the flag). Hitch parse
prints `orig=` after hold. Arm NX is before orig/stealth walk. No kdu
this note (Relic 38872 live).

## Not proven live

Mailbox 1–12 frozen: no NPTE dump. PTE bits / NPF-after-hold / HashRec
hit on a mapped sys are **not** claimed. Prior live RPM-original on
PID 3832 still only proves identity is not the stub.

## Docs

ADR-002 ASID 4 + kinds 8/9/11/12. NPT_STEALTH.md.
[UPDATE_GUIDE](../UPDATE_GUIDE.md) HV NPT. Older toy table:
[dual-nCR3 vs EPT](2026-09-13-npt-dual-ncr3-vs-ept-split.md).

## Do not

- kdu / Map-AfterZppu / wait-hold until **запускай**
- remap `A67B068F` / `29075A35` / `17E25811` / stale `2D14EF01`
- hasher `--eax 1` / NPT ntdll/user32 / TimerQ / mailbox op 13

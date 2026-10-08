# NPT dual-nCR3 vs Intel R/X split (2026-09-13)

Review of the textbook “shadow page + NPT split R/W vs X + CR3
filter” against `npt_stealth.cpp` on this Ryzen (AMD SVM). Mailbox
1–12 unchanged. No map this note.

## What the textbook wants

Three pieces are the product:

1. Shadow 4K copy with the stub; original PFN stays clean.
2. Integrity **reads** original bytes.
3. Only the target process **executes** the stub.

That is also our hold (Enqueue / KickCtor / TimerQ_Push ret stub,
hasher raw-load). The Intel-shaped recipe to get there does **not**
map onto AMD NPT.

## AMD: no execute-only

APM NPT: a page with X is readable. SimpleSvmHook: dual-nCR3, not
EPT execute-only. Skill `hypervisor-amd-svm`.

One PTE with “R/W → Page_Orig, X → Page_Shadow” is an **Intel EPT**
split. On NPT, turning X on the shadow PFN makes that PFN readable
too. Hasher on any vCPU that still has that PTE would see the stub
→ JUMPOUT.

Do **not** flip the shared identity PTE to the shadow PFN and clear
NX. Comment in `handle_stealth_npf`: other CPUs would execute/read
the wrong view.

## What we actually do (per vCPU)

| View | nCR3 / ASID | Hooked GPA PTE |
|---|---|---|
| Identity | `epml4` / ASID 1 | original PFN, `trap_execute` then **W=0**: R=1 NX |
| Stealth | cloned walk / ASID 2 | copy PFN, `identity_access`: RWX |

Pipeline:

1. `stealth_arm` copies the 4K into `stealth_page[]`, patches the
   copy (insn-exact ret stub / nop5 / jmp), NX on **identity** PTE.
2. Hasher **read**: identity R, original PFN, **no NPF**.
3. Fetch: identity NX → `VMEXIT_NPF` (ID). This vCPU
   `switch_to_stealth_ncr3` (ASID 2). Other CPUs stay identity.
4. `rFLAGS.TF` (AMD stand-in for Intel MTF) counts stub insns, then
   identity again so a later read on this CPU is original.

Writes: NPF → stealth copy; identity PFN stays golden.

## CR3 filter is not the hasher split

Relic hasher and Relic `RA_Enqueue` share the **same** user CR3.
Isolation is **read vs fetch**, not process vs process.

`owner_cr3` is stored. RIP==site.va **and** guest CR3==owner → stub
MTF length. Any other fetch of that GPA still switches to the
**copy** (original bytes + stubs). We do **not** enable X on
identity for a “foreign CR3”. Relic `.text` is not a shared DLL;
another process does not fetch that GPA under its own CR3.

Kernel DTB vs user DTB (KPTI) is why `select_user_cr3` exists.
Cycle 6 hold `status=8` = that walk failed **before** NPT mutate,
not a split-view bug.

## Toy “RAX=1 vs RAX=2”

| Textbook | Here |
|---|---|
| Epilogue `mov eax,1; ret` on shadow | Prologue insn-exact stub on copy (`eax=0` for Enqueue 6 / KickCtor 3 / TimerQ 3) |
| `#DB` poke `guest_regs->rax` without copy | Not used. Copy is the hook. |
| Other CR3 executes original and returns 2 | Not a Relic hold invariant. Identity is NX. |

Poking RAX on NPF without a copy does not stop Enqueue from packing
slots; the function still ran.

## Follow-up (2026-09-14)

Orig-exec nCR3 **ASID 4** is now the foreign-CR3 fetch path (original
PFN **R=1 W=0 X=1**, private walk). A store on orig-exec still NPFs onto
the stealth copy so hasher gold stays clean. Hasher vs Enqueue isolation
is still **read vs fetch on the same Relic user CR3**. Foreign orig-exec
of Enqueue is the **real** Enqueue (slots), not textbook `return 2`.
Policy: `stealth_npf_pick_view` in `handle_stealth_npf`. Hitch `orig=`
counts those NPFs (mailbox op 3 ASCII, not a new op).
[orig-exec ASID 4](2026-09-14-npt-orig-exec-asid4.md).

## Do not

- Intel EPT execute-only / single-PTE R vs X flip on this CPU
- Open X on the shared identity PTE
- NPT-protect dest leftover (`0x3E58000` / `0x3F04000` / `0x3F2D000`)
- Treat CR3 isolation as the hasher vs execute split
- Nested-map while ping=`pong`

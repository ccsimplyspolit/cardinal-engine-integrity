# Cycle 8h: dual-nCR3 gap closed as catalog (2026-09-13)

The quote «mailbox status=0 + живые прологи RPM» is the **entire** live
proof this cycle had. This note inventories mailbox 1–12, hitch, and
`npt_stealth.cpp` so the gap is **closed**, not left as «не разобрано».

**STOP.** ping **ud** (`cycle8h-ping-npt.txt` 22:16:51). Relic **0**.
Event **41** `22:07:45` on mapped `17E25811`. Do **not** map. Do **not**
add mailbox op 13.

PID **3832** `0x7FF7B6EE0000` CR3 `0x55ABF3000` (dead with host).

## Verdict

| Claim | Status |
|---|---|
| A Identity vs execute PTE (live bits) | **not proven** — **blocked by 41** (SVM off; no NPTE dump op) |
| A Invariant in code (what arm writes) | **specified** — not a live dump |
| A RPM / `read_virt` original prologues | **proven** while 3832 lived — proves identity **not stub**, not the split |
| B NPF after hold / RUN | **not proven** — no post-hold hitch sample; **do not write «NPF был»** |
| B hitch at map 21:19 | **proven** `inner=0 npf=0` (idle, before Relic) |
| C HashRec hit count | **not proven** — emulate exists, **no counter / no log line** |
| C HashRec **arm** `eax=0xFFFFFFFE` | **proven** apply `status=0` (21:38 and 22:05:57) |

Live PTE / NPF-after-hold / HashRec-hit need a **future** map that is
not `17E25811` **and** either hitch-after-hold or a new mailbox op.
Ops **1–12 stay frozen**.

## A — how to read NPTE (mailbox 1–12)

There is **no** read-NPTE path in the frozen ABI.

| op | What it returns | PTE? |
|---|---|---|
| 5 `read_virt` | guest bytes via guest CR3 + **identity** NPT (data) | no |
| 6 `stealth_arm` | `status` + `aux=stealth_site_count` | no |
| 11 `status` | `live`, `owner_cr3` (agent hello, **not** Relic DTB), `sites`, `hidden`, `next_seq` | no |
| 12 `protect` | `aux=stealth_page_count`, `size=pages` | no |
| 3 ping | `stealth_reap_stale()` then cpu index | no |

`mailbox_msg` has `op/seq/status/cr3/va/size/aux/image_base/name/data[]`.
No PFN, NX, W, ASID, nCR3 PA. Comment on op 12: «not op 13».

`zpp_aoe4 read --rva` is op 5. Same path as hasher raw-load: identity
leaf, original PFN. Seeing `44 89 4c 24 20…` / `48 8b c4 48 89…` /
`48 89 5c 24 20…` means **identity is not the stub**. It does **not**
prove stealth PFN ≠ identity PFN.

Last live reads (3832, `cycle8h-evidence2.txt` 22:03:52, before leftover
clear killed the hold):

| RVA | Identity `read_virt` |
|---|---|
| Enqueue `0x3DD2550` | `44 89 4c 24 20 55 53 56 57…` |
| KickCtor `0x3E691F4` | `48 8b c4 48 89 58 10…` |
| hasher `0x3E57050` | `48 89 5c 24 20 57 48 83 ec 30…` |
| TimerQ `0x3E672DC` | `48 85 c9 74 58…` (not stub; **not armed**) |
| WW / sibling | original; **not armed** |

No host dump of `stealth_pt[]` / `identity_epte`. Minidump empty.

### Code invariant (not a dump)

`npt_stealth.cpp` after a successful arm:

1. Copy 4K from GPA into `unprotected_memory.stealth_page[slot]`.
   `slot.original_pfn = primary->page_number()`.
2. `stealth_ensure_walk`: stealth leaf `page_number(elf_physical(copy)>>12)`
   then `identity_access()` (RWX on the **copy**).
3. Enqueue/KickCtor: `write_ret_stub` **on the copy only**. HashRec:
   `patch=0`, copy stays original (emulate on NPF, not a stub).
4. `stealth_arm_primary_nx(gpa, original_pfn)`: identity leaf
   `page_number(original_pfn)`, `trap_execute()`, then `write(false)`
   → identity **R=1 W=0 X=0**, same original PFN.
5. Execute NPF: `switch_to_stealth_ncr3()` (ASID 2). Comment at
   non-site fetch: do **not** open X on the shared identity PTE.

That is the SimpleSvmHook split **as written**. It was **not** read
back from either nCR3 this cycle.

## B — NPF trace

Hitch counters `full_npf` only when `exit==0x400` **during**
`hitch_watch` (one snapshot after `load_ok`). hitch-host ended
**21:22:29**. Relic 3832 started **21:38:49**. Hold **21:38** / rearm
**22:05:57**. **No** hitch sample after hold. Loader
`zpp_loader-live.log` last stage `vmcall_skip`; `npf=0` is idle.

Op 11 does not expose `full_npf`. No `asid` / `nCR3` line in usermode
logs. After 41: no SVM, no NPF.

Map-time 21:19: `hitch sample=0 inner=0 … npf=0` (32 CPU). That is
**before** any hooked 4K.

## C — HashRec hit

`stealth_hashrec_emulate` runs on execute NPF when
`eax_ret==0xFFFFFFFE` and RIP==site. **No** `++hits`. No DbgPrint.
Mailbox does not return emulate counts.

Apply (hold + rearm): `arm va=…37050 eax=0xfffffffe status=0`. Protect
`0x3E57000` `status=0`. 45E8 **not** armed. `--eax 1` **not** used.

Whether hasher **fetched** the site on 3832: **unknown**.

## Do not

- remap `17E25811` / add op 13 / invent PTE bits or «NPF был»
- treat RPM / `read_virt` as execute-copy proof
- inject / RUN / hold 3832

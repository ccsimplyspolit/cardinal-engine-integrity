# Cycle 6: NPT dual-nCR3 ret stub (2026-09-13)

Mailbox ops 1–12 unchanged. One hypothesis. Not guest WPM.

## Point

AMD NPT has no execute-only: a page that is executable is readable.
Hold is **two nCR3 views** of the same GPA:

| View | PTE | What sees it |
|---|---|---|
| Identity | original PFN, R=1 W=0 NX | hasher / raw load |
| Stealth | private execute-copy | instruction fetch (NPF → switch) |

The hasher must keep seeing golden Enqueue bytes. The CPU must not
run Enqueue / KickCtor / TimerQ_Push. That is an NPT problem, not a
`WriteProcessMemory` plant.

## Why the 10-byte builtin cannot do this

`write_builtin_stub` was ENDBR64 + `mov eax,imm32` + `ret` = **10**
bytes. Exact insn covers on 16.3.11308 (unpacked_static file bytes):

| RVA | Name | First insns | 10-byte cover |
|---|---|---|---|
| `0x3DD2550` | `RA_Enqueue` | 5+1+1+1+1 = 9, then `push r12` (2) | **tears** |
| `0x3E691F4` | `RA_KickCtor` | 3+4 = 7 | **tears** |
| `0x3E672DC` | `RA_TimerQ_Push` | 3 (`test rcx,rcx`) then `jz` (2) | 5 exact; 10 may cover later insns but nop5 does not disable the push |

Cycle 5 mapped HV can *target* those RVAs (outside the WW window
refuse) and still `hook_failed` on Enqueue because of the torn 10.

## Change

`stealth_arm` execute-copy ret stub length = smallest
`insns_cover_exact` in `[3,15]` (`min_need` 3 if `eax==0`, 6 if
`eax!=0`). Encode `xor eax,eax; ret` (+ nops) for 3–5, or
`mov eax,imm32; ret` (+ nops) for ≥6. MTF `step_insns` finishes the
stub including RET before identity NX (2 for compact mov; `n-1` for
xor+nops+ret). Dest leftover pages `0x3F04000` / `0x3F2D000` still
refused. WW-window refuse from Cycle 5 is gone (not used this hold:
three function entries only).

`zpp_at.py hold --apply` prefers `hold_npt_ret_rvas` (eax=0). Does
**not** arm the 14 WW E8 nops this cycle (Cycle 3 hang class =
successful WW execute-copy + continued `--file`). Cycle 4 abort on
first `status!=0` stays. Op 6 wire frozen.

`insn_boundary` Enqueue/KickCtor/TimerQ covers **PASS**.

## Live this boot (before remap)

| | |
|---|---|
| ping | **pong** (Cycle 5 `6D160457` still mapped) |
| Relic | **36888** `0x7FF6F8E70000` start 17:43:10 |
| slots | **0** (uninit) |
| WindowWatch | **38124** |
| x64dbg | none |
| cookie | `load_ok_pending_alive` — do not nested-map |

Do not open x64dbg while this PID can pack. Do not hold on Cycle 5
(Enqueue 10-byte tear). ZPPU leave 32/32 **done** 18:03 (`left=32/32`).
One Map-AfterZppu **load_ok** 18:03:46 sys `7B767084`. Hitch inner=0 npf=0.

## Hold this boot (18:07 / 18:10)

Relic **36888** `0x7FF6F8E70000` slots=0, WindowWatch **38124**.

`hold --apply` NPT ret list: Enqueue RPM `44894c24…` (golden). KickCtor
skipped because `dest_pages.json` lists `0x3E69000` (now limited to
leftover `0x3E58000`/`0x3F04000`/`0x3F2D000` for NPT ret). TimerQ not
reached.

First `--file` hello `rax=2`, retry query ok, **arm Enqueue
`status=8 sites=0`**. ABI: 8 = `not_found` (`mailbox_resolve_target` /
`select_user_cr3` did not translate the Enqueue VA). `stealth_arm` was
**not** entered — identity NPT not mutated. Cycle 4 abort fired anyway.

Second session (`stealth --rva 0x3DD2550 --eax 0`): hello ok, query
`cr3=73632e000 image=0`, same **status=8 sites=0**. Do not hammer.
Do not nested-map. Do not start x64dbg.

Next Relic should be a **new** `-dev -nodbg -notrap` PID on this Cycle 6
map (do not reuse 5012 / 20068 / this 36888 if walk stays 8).

## Artifacts

| | mtime | bytes | SHA256 |
|---|---|---|---|
| `zpp_loader.sys` | 2026-09-13T18:01:42 | 1076224 | `7B7670840CF4448395866AC3B340E3CCD93372733F27FF84E117BED9FA2CDDE3` |
| ELF `zpp_hypervisor` | 2026-09-13T18:01:41 | 1026280 | `A20097D466863A71D0587068F2C309265CBFC8B11D0B27AABC0E1AC452CD07A5` |

Not Cycle 3 corpse `5351E024`. Not Cycle 5 `6D160457`.

## Do not

- WPM Relic `.text` / Watcher / 7AB0
- NPT-protect dest leftover
- Stub Watcher prologue (IAT-kick)
- Nested-map while ping=`pong`
- Arm WW E8 flood / `0x3F5B04B` this cycle
- Treat packed slots as a pass

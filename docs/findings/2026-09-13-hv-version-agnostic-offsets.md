# 2026-09-13 HV version-agnostic EPROCESS discover

Host still Win11 Pro **25H2** `26200.7171` (AIDA 21:28). Product must
run on **Win10 22H2 … Win11 24H2/25H2 and later**, not a hardcoded
`26200.7171` / `0x388` / `PEB=0x550` table. Live SVM (map ~00:55) is
**not** remapped. Dump still 15843. Mailbox ops 1–12 frozen. No ZPPU,
no KDU `-map`, no nested-map, no Relic plant, no `sc start Aoe4Hv`.

## What was wrong

Mapped sys logged `zpp userdtb_off=0 peb=0`. Two separate facts:

1. **`userdtb_off=0` is valid** when KVAS/KPTI is off. Walk is
   `DirectoryTableBase` (stable KPROCESS slot **0x28**) after SME C-bit
   strip (`pte_phys_4k`, `ram_dtb` vs `identity_ram_bytes` 34 GiB).
2. **`peb=0` was a miss**, not “this build has no PEB”. Discover used
   `PsGetNextProcess` (often **not** exported) + host scan only. System
   has no PEB, so the log stayed `peb=0` with no named offsets / ntos
   build.

ELF `select_user_cr3` also named `0x388` / `0x280` / `0x158` as a
“25H2” candidate list and defaulted PEB reads to `0x550`. That is a
version table.

## What landed (source only; next map)

Loader `windows_loader/src/pe_file.cpp` at map-time, no build number
switch:

| Field | How |
|---|---|
| DirectoryTableBase | match current CR3 after C-bit strip; fallback 0x28 (KPROCESS ABI, not 24H2) |
| UserDirectoryTableBase | physical MZ walk of explorer/csrss/winlogon (section base first). Only DTB walks MZ ? **0** (KVAS off) |
| PEB | decode `PsGetProcessPeb` (`mov rax,[rcx+disp]`, CET/jmp). Else scan a live user EPROCESS |
| ImageFileName | pointer-diff of `PsGetProcessImageFileName` |
| UniqueProcessId | decode `PsGetProcessId`, else links-8 |
| ActiveProcessLinks | UniqueProcessId + LIST_ENTRY, else ImageFileName-0x160 heuristic |
| Process walk | `PsGetNextProcess` if exported, else `ActiveProcessLinks` from System |

Persist **always** (even `offsets_fail` / zeros):

`zpp userdtb_off=… peb=… dtb=… name=… links=… pid=… ntos=10.0.build.ubr ntbuild=…`

ELF: `select_user_cr3` = handoff DTB + user DTB, then brute `0x20..0x400`
when `probe_va` is set. `read_eprocess_peb` scans if handoff PEB is 0.
No `0x550` / `0x388` fallback. C-bit strip unchanged.

Decoder: `hypervisor/include/zpp/hypervisor/kprocess_field.h` (compile-time
tests in `tests/amd_layout.cpp`). ADR-007 updated.

## Not done this turn

Live map still has the old discover (`peb=0`). Do not remap until the
other agent finishes Steam / hold / NPT verify. Next authorized map
should log a non-zero `peb=` (export decode) and `userdtb_off=0` only
when KVAS is off.

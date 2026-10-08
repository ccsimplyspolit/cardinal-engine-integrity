# Cycle 8: user CR3 walk + hasher HashRec (2026-09-13)

Mailbox ops 1–12 unchanged. Overlay / Patch Game not used.

## Point

Cycle 6 hold on Relic **36888** was `status=8` before NPT mutate:
`select_user_cr3` collected up to 96 `ram_dtb` qwords from EPROCESS
`0x20..0x400`, then tested. A full bag dropped later
`UserDirectoryTableBase` (0x388 / 0x550). Kernel DirectoryTableBase
does not map Relic `.text` (KPTI). `stealth_arm` never ran.

Hasher HashRec (`eax=0xFFFFFFFE` at `0x3E57050`) still required so
45E8 `cmp rax,[obj+0x10]/[0x18]` matches while identity `.text` can
be RPM/WPM from other processes.

## Change

- ELF: with `probe_va`, test `read_guest_virtual` **as each** DTB
  candidate is found. Prefer UserDirectoryTableBase, then DirectoryTableBase,
  then brute `0x20..0x800`. No 96-slot cap.
- `kprocess_dtb_scan_max` 0x400 → 0x800.
- Mailbox resolve: keep the CR3 that **reads** the site VA, not only
  `guest_virtual_to_physical`.
- Hold list unchanged: Enqueue / KickCtor / TimerQ_Push ret stub
  `eax=0`; hasher HashRec; protect hasher page; skip dest leftover.

## Do not

- Nested-map while ping=`pong`
- Remap Cycle 3 sys `5351E024`
- Hold PID 36888 / 20068 / 5012
- `--eax 1` hasher / plant prologue / WPM `.text`
- Arm WW `0x3F0A7D0` / sibling `0x3F328D8` / 7AB0 / 45E8 / WW E8 flood

## Live

| Step | Result |
|---|---|
| Preflight 18:58 | Cycle 6 ping `pong`; Relic **36888** query `status=0` `cr3=73632e000`; `read Enqueue status=8` |
| Build 18:58:19 | sys `77C8BCF4…` Verify PASS (scan 0x800, test-as-you-go) |
| Leave 19:05 | ZPPU 32/32 ping `ud`; killed 36888 + WW 38124 |
| Map 19:05:35 | `load_ok` hitch inner=0 npf=0; `userdtb_off=0` peb=2e0 dtb=28 |
| Relic **3088** | `0x7FF6F8E70000` 19:09:20 slots=0; Steam `-dev -nodbg -notrap` |
| Hold | hello/query ok; **arm Enqueue `status=8` sites=0** (NPT not mutated) |
| query `--va` Enqueue | `status=8` |
| query `--va` image MZ | `status=8` |

Kernel DTB maps EPROCESS (query by name) but **no DTB in `0x20..0x800`** reads Relic user pages. Next: scan `0x2000` (= `kprocess_field_max`), remap.

## Live 8b / 8c (same day)

Scan `0x2000` (8b sys `8C9D7CDD`, map 19:18) still `read Enqueue status=8`
on Relic **36364**. Explorer HV MZ `status=0`. Root is leftover
`RelicCardinal` EPROCESS, not the scan window. 8c ELF skips leftovers
when `probe_va` is set. 8c map kept Relic across kdu → Event 41 19:36.
Do not remap `D78C5065`. See
[Cycle 8c Relic-live map](2026-09-13-hv-cycle8c-relic-live-map.md).

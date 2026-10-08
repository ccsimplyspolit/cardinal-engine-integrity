# Cycle 5: WW-family stealth fail-closed (2026-09-13 17:27)

Mailbox ops 1–12 unchanged. One hypothesis.

## Hypothesis

Cycle 3 hang was **NPT execute-copy on successful** WindowWatch-family
`stealth_arm` (23× `status=0`), not the `hook_failed` unwind. First
mailbox 10 was RVA `0x3F5B04B` (page `0x3F5B000`, adjacent success
`0x3F5A9CF` on `0x3F5A000`). Fail path already returned before identity
NX. Cycle 4 `--file` abort does not prevent the first 23 copies.

## Change

`stealth_arm` returns false **before** GPA copy / `stealth_arm_primary_nx`
when `image_base` is set and `target_va - image_base` is in Relic `.text`
RVA `[0x3F00000, 0x3F80000)` (WW / WW-clone / dest-skip enqueue pages
`0x3F04000` / `0x3F2D000`). Uses existing `mailbox_msg.image_base`
(`svm_bringup` leaves query PEB image 0; `zpp_aoe4` fills RPM base).
Op 6 request/response/status codes unchanged (`10` = refuse).

## Artifacts (not Cycle 3 corpse `5351E024`)

| | mtime | bytes | SHA256 |
|---|---|---|---|
| `zpp_loader.sys` | 2026-09-13T17:27:52 | 1075712 | `6D160457102911A45671842843FD1A2540AF48CBC7A9975660246C706A904FD5` |
| ELF `zpp_hypervisor` | 2026-09-13T17:27:51 | 1025576 | `89C94112F5948BB84826313C710E56982B0D83D7BE76ADF1E54AE7769C03FF03` |
| `zpp_aoe4.exe` | 2026-09-13T17:27:50 | 197632 | (image_base on op 6) |

`insn_boundary.exe` leftover E8 **PASS** (clang-cl rebuild). STEP 5 this
run is observation-only: **no wait-hold**.

## STEP 0 (elevated 17:24)

ping **ud**, VBS 0, Relic none, Event 41 **17:09:32**, Minidump 0, gate
**21** vs old last_fix 16:45:29, HostPrep Ready, RelicDMP 15:12:51
3876003113 B. IDA MCP: no session (WinError 10054). CE bridge down.

## Gate

`last_fix_time` = sys mtime **17:27:52** (after Event 41). User ordered
full cycle without «запускай». `status=ready_to_launch`
`launch_authorized=true`. Do not remap `5351E024`.

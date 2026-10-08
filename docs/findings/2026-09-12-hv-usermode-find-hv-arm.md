# 2026-09-12 usermode finds, HV only arms

Host: Windows **11 25H2** `CurrentBuild=26200` UBR **7171** (winver).
`ntoskrnl` file version still `10.0.26100.7171`. Same boot **21:25:38**.
SVM map **23:18** key `0x3c2181d55b46f07c`. Dump still 15843.

## What failed

`hold --apply` on live Relic used **this session's** image (not a previous
PID). WindowWatch PID **30636** `base=0x7FF6BC390000` slots=0, then a
later Relic **50796**. Stealth still `status=8 not_found` on every
Watcher-tag VA (`image+0x3E5D96D` ù). Query **without** `--va` was
`status=0` `cr3=kernel DirectoryTableBase`. Query **with** `--va` = MZ
at image base also `status=8`.

Cause: ELF treated hook VAs as MZ probes and then required usermode's
**kernel** CR3 (KPTI) to translate user `.text`. 25H2 EPROCESS/KPROCESS
field layout is not the 23H2 `PEB=0x550` table. WinAPI does not expose
CR3.

## Split (ADR-007)

| Layer | Job |
|---|---|
| Usermode (`zpp_at.py` RPM/Toolhelp) | PID, image base, dest skip, E8 sites. New each launch. |
| Loader (once per map) | `UserDirectoryTableBase` offset: `PsGetNextProcess` + `MmCopyVirtualMemory` + physical MZ walk of explorer. Log `zpp userdtb_off=` |
| HV op 6 | `stealth_arm(name, va, nop5)` only. No Relic RVA. `target_cr3=0`. |

AIDA 21:28 (`Report.xml`): **PCID ?? ??????????????**, INVPCID ??.
That is why kernel `query` CR3 does not walk Relic `.text`. See
[2026-09-12-hv-aida-25h2-pcid.md](2026-09-12-hv-aida-25h2-pcid.md).

Do not start x64dbg until hold apply returns 0.

## Code

- `windows_loader/src/pe_file.cpp` ù `discover_user_directory_table_base`
- `mailbox.cpp` ù do not reject kernel vs user CR3 mismatch
- `select_user_cr3` ù handed-off user DTB + brute `0x20..0x400` when probing
- `zpp_aoe4.cpp` ù query does not inherit stealth `--va`; arm `target_cr3=0`

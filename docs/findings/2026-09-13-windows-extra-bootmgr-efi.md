# 2026-09-13 extra Windows Boot Manager / leftover ESP EFI

User: delete every Windows Boot Manager except the live one, plus leftover
EFI copies. Not zpp `windows_loader`. **Do not map.**

## Before

Firmware `{fwbootmgr}` displayorder (timeout 1):

| GUID | What |
|------|------|
| `{ebb2d88b-af6d-11f1-bd74-806e6f6e6963}` | Windows Boot Manager `\EFI\Microsoft\Boot\bootmgfw.efi` on `\Device\HarddiskVolume10` |
| `{bootmgr}` | Windows Boot Manager on `\Device\HarddiskVolume5` (live) |
| `{ad4b9488-afc9-11f1-bd5f-806e6f6e6963}` | Windows Boot Manager on `\Device\HarddiskVolume3` |
| `{c379c0c1-…}` / `{c379c0c2-…}` / `{c379c0c3-…}` | UEFI CD/DVD, Removable, Network |

Three GPT ESPs:

| Disk | Partition | Size | IsSystem | Contents |
|------|-----------|------|----------|----------|
| 4 WD_BLACK SN850X (C:) | 3 | 512 MB | **True** | Live `bootmgfw.efi` + BCD mtime 15:54:32 |
| 3 WDC PC SN520 256G | 1 | 1 GB | False | Stale BCD; default OS `device=unknown` |
| 1 TOSHIBA DT01ACA100 | 1 | 100 MB | False | Clone of live BCD pointing at C: |

BCD also had a second `Windows 11` OSLOADER `{4333c4bc-…}` (not in
`{bootmgr}` displayorder) plus two WinRE entries with `ramdisk=[unknown]`.

## Done (elevated, 16:16–16:17)

1. Wiped `EFI\Microsoft` and `EFI\Boot` on the two non-system ESPs (now empty).
   Live ESP disk 4 p3 untouched.
2. `bcdedit /delete` extra firmware WBM `{ebb2d88b}` and `{ad4b9488}`.
3. `{fwbootmgr}` displayorder = `{bootmgr}` then CD/DVD, Removable, Network.
4. Deleted stale OSLOADER `{4333c4bc}` and unknown WinRE `{4333c4be}` /
   `{4333c4b9}`. Resume `{4333c4bb}` and device-option GUIDs were already gone.

Kept: `{current}` Windows 11 on C:, live WinRE `{4333c4c3}`, Windows Rollback
`{7254a080}` (`$WINDOWS.~BT` from today’s 26H2), firmware CD/DVD / USB / PXE.

Logs: `aoe4-hv/docs/_bsod/boot-efi-enum.txt`, `esp-volume-map.txt`,
`boot-efi-cleanup.txt`, `boot-efi-cleanup-bcd.txt`.

## After

Firmware: one Windows Boot Manager (`{bootmgr}` → Volume5
`\EFI\Microsoft\Boot\bootmgfw.efi`). OSLOADER displayorder: `{current}` only.

Empty ESP partitions on SN520 and Toshiba were **not** deleted (only EFI
files). UEFI may re-add a WBM if someone copies `bootmgfw.efi` back there.

No `kdu`. `launch_authorized` stays false.
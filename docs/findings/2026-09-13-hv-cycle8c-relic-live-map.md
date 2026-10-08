# Cycle 8c: leftover EPROCESS + Relic-live map hang (2026-09-13)

Mailbox ops 1–12 unchanged. Overlay / Patch Game not used. No hold after this map.

## Point

Cycle 8/8b `read Enqueue status=8` was not “no DTB in `0x20..0x2000`”.
Explorer HV-read of MZ is `status=0` `4d 5a`. Relic usermode RPM of
Enqueue is golden `44894c24…`, `QueryWorkingSetEx` Valid=1, GPA under
34 GiB. Same query CR3 `0x73632e000` on PID 36888 / 3088 / 36364.

`find_running_process` took the **first** `ImageFileName` match. Killed
Relic EPROCESS stays on `ActiveProcessLinks`. Query by name returns that
zombie DTB; `select_user_cr3` cannot read the live `.text`.

ELF 8c: `find_running_process(..., probe_va)` + mailbox resolve passes
`msg.va` so read/stealth/protect skip leftovers. Query (no VA) still
first-match. Not op 13.

## Live 8b (this boot 17:09:28, sys `8C9D7CDD`)

| Step | Result |
|---|---|
| Leave 19:17 | ZPPU 32/32 ping `ud`; killed 3088 |
| Map 19:18:12 | `load_ok` hitch inner=0 npf=0; Relic **none** at kdu |
| Relic **36364** | 19:21:33 `0x7FF6F8E70000` slots=0; Steam `-dev -nodbg -notrap` |
| query | `status=0` `cr3=73632e000` image_rpm=`7ff6f8e70000` |
| HV read Enqueue/hasher | `status=8` |
| HV read explorer MZ | `status=0` `4d5a` |
| usermode RPM | MZ `4d5a`; Enqueue golden; pages Valid |

## Live 8c (sys `D78C5065` 19:31:23, 1087488 B)

| Step | Result |
|---|---|
| Build 19:31:23 | ELF SHA256 `8694236A…157B`; Verify PASS |
| Leave keep Relic | armed=32/32 left=32/32; **kept 36364** |
| Map 19:32:06 | `load_ok` hitch inner=0 npf=0; Relic **live** at kdu |
| hitch | inner=0 until ~19:35; then host died |
| Event 6008 | previous shutdown **19:34:40** unexpected |
| Event 41 | **19:36:17** (boot **19:36:13**) |
| Minidump | empty (`CrashDumpEnabled=0`) |
| Capture | `docs/_bsod/crash-20260913-193850` |
| Gate | 21 cookie `in_progress` + newer boot |

Hold never ran. Ping after reboot = `ud`.

## Do not

- Remap Cycle 8c sys `D78C5065` (same crash image)
- Remap Cycle 8b `8C9D7CDD` / Cycle 3 `5351E024`
- `kdu -map` while Relic is live (`Map-AfterZppu` now exit 5)
- Hold PID 36888 / 20068 / 5012 / 3088 / 36364
- Nested-map / `sc start Aoe4Hv` / `--eax 1` hasher / WPM `.text`
- Treat ping=`ud` after this reboot as permission to map

## Next (not this turn)

New sys (not `D78C5065`) only after a real last_fix newer than Event 41
19:36:17. Map on idle (Relic none), then Steam Relic, then `hold --apply`.
8c leftover-EPROCESS walk stays in tree; it was **not** proven (no query
after 8c `load_ok`).

# Cycle 3 ELF rebuild (2026-09-13 16:45) — not mapped

SAFE slice after session `3305282e` Event **41**. Goal locked:
one SVM-map → Relic `-dev -nodbg -notrap` → fail-closed `hold --apply`
39/39 → Vs AI → visible x64dbg from
`C:\Program Files (x86)\rbhost` 60s. One hypothesis/cycle. Mailbox
ops 1–12 untouched. **No map this turn.**

## Gate (this boot)

| | |
|---|---|
| LastBootUpTime | **2026-09-13T16:32:44** |
| Event 41 | **2026-09-13T16:32:48** |
| 6008 | unexpected 16:30:34 |
| Minidump | empty (`CrashDumpEnabled=0`) |
| Capture | `docs/_bsod/boot-capture.json` stamp **163635**, boot matches |
| Cookie | `analyzed_failed` (attempt 16:21:40 on prior boot 15:54:23) |
| `cycle-state` | `status=new_bsod` `launch_authorized=false` |
| ping | **ud** |
| Relic 5012 | dead; image was `0x7FF7BABB0000` SizeOfImage `0x8C3D000` — do not reuse VA |

HostPrep Capture already ran this boot. Did **not** re-run
`Capture-CrashContext.ps1`. Did **not** `kdu` / `Map-AfterZppu` /
`Start-ZppLoader`.

## Cycle 3 (landed on disk)

Hypothesis unchanged: `insn_starts_at` 15-byte left-scan reports
mid-insn overlap on WW-clone / INT3-1FDC identity copies even when
usermode first byte is `E8` → mailbox `hook_failed` (**10**), hold
**20/39**.

| File | Change |
|---|---|
| `hypervisor/include/zpp/x64/insn_decode.h` | `stealth_nop5_e8_ok` — require `E8` + decode length 5 |
| `hypervisor/src/hypervisor/npt_stealth.cpp` | nop5+`E8` uses helper; skip left-scan; still fail-closed if not rel32 |
| `tests/insn_boundary.cpp` | leftover `48 8B 05` overlapping `E8` at +5: left-scan false, helper true. **PASS** |
| `tools/zpp_at.py` | unchanged: refuse retry after any `arm va=` |

Rebuild (`build_windows.bat`, **not mapped**):

| Artifact | mtime | size | SHA256 |
|---|---|---|---|
| `out/debug/x86_64/zpp_hypervisor` | 16:45:28 | 1025336 | `62CDC1EF77762E0AB4E6752988DEBBF8F29D88A109FA862D179BFF7735CE0822` |
| `out/debug/x86_64/zpp_loader.sys` | 16:45:29 | 1075200 | `5351E024F6321EBC4C3F99A82B8E576826C967A7C5B74340087A20AF7EAD5CF1` |

`last_fix_time=2026-09-13T16:45:29` is this sys mtime (newer than
Event 41). That is **not** launch permission.

## Do not

Map until user **запускай**. Nested-map. Hold on a live SVM that has
not idled minutes. Start x64dbg before 39/39. Reuse PID 5012 VA.
Quote `last-zpp-key.txt`. `sc start Aoe4Hv`.

Related: [Cycle 3 source](2026-09-13-hv-cycle3-hold-insn-boundary.md),
[Cycle 1 hold hang](2026-09-13-hv-cycle1-hold-hang.md),
[3305282e resume](2026-09-13-agent-session-3305282e-resume.md).

## Audit 16:51 (hashes re-checked, still not mapped)

Live LastBootUpTime **16:32:44**. Event **41** 16:32:48 / 6008 unexpected
16:30:34. Minidump empty. Keyed ping **ud**. Gate **20**. Relic none.
ELF/sys SHA256 match the table above. `insn_boundary` re-run **PASS**.
Dead VA `0x7FF7BABB0000` cleared from live `cycle-state` pid/image_base.
Launch commands: [Cycle 3 запускай path](2026-09-13-hv-cycle3-zapuskay-path.md).

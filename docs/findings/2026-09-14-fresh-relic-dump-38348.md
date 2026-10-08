# 2026-09-14 fresh Relic dump (PID 38348) — AT-safe RPM pack

User: полный свежий дамп в `K:\aoe4_dlc\dumps`, антитампер может закрыть игру.

## Canon this session

| | |
|---|---|
| PID | **38348** (still alive after dump) |
| Start | 2026-09-14 01:42:47 |
| Relic base | `0x7FF773860000` SizeOfImage `0x8C3D000` |
| Build | 16.3.11308.0 |
| Cmdline | `RelicCardinal.exe` only (no `-dev -nodbg -notrap`) |
| RA | `slots=0` begin=end=0 seed `0xFDFDFBCD1B3F5D7B` dispatcherOnce=`01` |
| Overlay | not in process |
| Recipe | `AOE4HOOK/tools/Capture-FreshRelicDump.ps1` elevated |

Index folder: `K:\aoe4_dlc\dumps\RelicCardinal_38348_20260914_014528_full\` (`STATUS=ok_full_relic_alive`).

| Sibling | What |
|---|---|
| `…014529\` | Relic PE `00007ff773860000.RelicCardinal.exe.bin` 147 050 496 B, CHECKS ok, 0 PAGE_GUARD |
| `…014530_ra\` | `.data` RA 19072 B, window empty |
| `…014531_sdkpack\` | **141** mapped PE, `--no-minidump` |
| `…014534_snapshot\` | `RelicCardinal_38348_full.dmp` **7 171 002 498** B Memory64; `maps.tsv`; `*_live_modules.csv` |

Full dmp: RPM copied **4 660 846 592**, RPM fail/zero **2 510 016 512** (GPU / inaccessible). dumpchk sees Memory64 **6999** ranges. ModuleListStream size mismatch (`0x6a86 != 0x3b80`) — writer had 4-byte pad after `NumberOfModules`; **IDA/RE = the `.bin`**, not WinDbg `lm`. Pad removed in `dump_relic_full_rpm.py` for the next dump.

No inject. No x64dbg attach. No `MiniDumpWriteDump` on the live PID.

## PID 38872 (same night, incomplete)

Titled match-ish WS ~9 GiB, same live base `0x7FF773860000`. Module PE + 154-module sdkpack OK, RA empty. `PssCaptureSnapshot` **winerr=1455** (`ERROR_NOT_ENOUGH_MEMORY`): Relic private ~9.5 GiB, free commit ~6.5 GiB. Relic still alive immediately after; process gone ~01:26, Steam started a new Relic. Treat PSS clone + `PROCESS_CREATE_PROCESS` on a fat Relic as AT-adjacent. Do not second-clone.

## Why this method

Live MiniDump suspends every thread → DualFlag / slots pack → death (24044). Second VA-clone on one online PID → death (37560). PSS clone needs a second commit copy of the VA — 1455 when the game is ~9 GiB. Streaming `VirtualQueryEx` + RPM does not suspend and does not duplicate commit.

## Tools

- `dump_relic_module.py` / `dump_ra_capture.py` / `dump_sdk_pack.py --no-minidump`
- `dump_relic_full_rpm.py` (new Memory64 writer)
- `Capture-FreshRelicDump.ps1` (elevate once, no nested RunAs)

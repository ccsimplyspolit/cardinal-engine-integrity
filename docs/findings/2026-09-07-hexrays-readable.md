# 2026-09-07 — Hex-Rays dump brought to readable form

User: «привести к читаемому виду» after the 488k pass finished.

## What shipped

Not original Relic C++. A stable layer over the 60644 Hex-Rays dump:

| Output | Path |
|---|---|
| 87 RVA shards | `aoe4/gamesource/src/readable/shards/rva_*.c` |
| 65 named (ra-map) | `src/readable/named/RA_*_0xRVA.c` |
| Index | `meta/readable-index.jsonl` (488031 rows) |
| Coverage | `meta/readable-coverage.json` |

Transforms (`tools/ida/readable.py`, 13 unittest):

- `__int64` / `_QWORD` / `__fastcall` → `int64_t` / `uint64_t`
- `sub_<VA>` / `JUMPOUT(0xVA)` / `qword_<VA>` → RVA
- ra-map names in calls (`RA_KickCtor` not `sub_3E691F4`)
- Header is RVA-first; session VA marked do-not-mix

Export: `tools/Export-Readable.py` (227s, parsed=488031 skipped=0).
Polish VA leftovers: `--polish-existing` (126 files).

## How to open

```text
K:\aoe4_dlc\aoe4\gamesource\src\readable\named\RA_Enqueue_0x3DD2550.c
K:\aoe4_dlc\aoe4\gamesource\src\readable\shards\rva_03D00000_03DFFFFF.c
```

Re-run: `pwsh -NoProfile -File tools\Run-ExportReadable.ps1`

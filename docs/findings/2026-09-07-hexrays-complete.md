# 2026-09-07 — Hex-Rays full pass finished (not 100% of all funcs)

User asked whether the planned IDA “decompile everything” job is running
and whether coverage is 100%.

## Status

**Done.** Worker pid **45048** finished at **01:01:49**. Process is
**dead**. IDA MCP `list_instances` / `idb_list` = **0**. Do not start a
second idalib on `dump\ida-work\runtime_exe.i64`.

Log: `K:\aoe4_dlc\aoe4\gamesource\dump\logs\full_decompile.out.log`  
Status: `dumps\RelicCardinal_60644_20260906_full_analysis\analysis\runtime_exe\status.json`  
Bodies: `...\runtime_exe\pseudocode\` — **488031** `.c` files (counted).

Opened **20:49:39**, queued **534587** / discovered **534587**,
imagebase `0x7FF7A5500000` (copy IDB). Cluster-first then skip-if-exists.

## Coverage (not 100% of the function list)

| Bucket | Count | Share of 534587 |
|---|---:|---:|
| `.c` bodies (`exported` 355794 + `exists` 132237) | **488031** | **91.29%** |
| skipped `FUNC_LIB` (by design) | 46500 | 8.70% |
| Hex-Rays fail (`No cfunc`) this run | 56 | 0.010% |
| queued / processed | 534587 | 100% of the work list |

Non-lib: **488031 / 488087 = 99.988%**. The 56 misses are Hex-Rays
`No cfunc`, not leftover work.

`meta\analysis-coverage.json` still has the **20:49** snapshot (24.74%
bodies). That file is stale until `Build-Catalog.py` is re-run.

## What this is not

- Not named Relic natives. Catalog at start: **56865** named, mostly
  MSVC RTTI/`nullsub`. `Player_*` / SCAR names stay XOR.
- Not a second IDA GUI on the canon `runtime_exe.i64` (60644). This
  pass used the **copy** under `aoe4\gamesource\dump\ida-work\`.
- Not Steam `original_exe` (still do not use).

Readable layer (same evening): [hexrays-readable](2026-09-07-hexrays-readable.md).

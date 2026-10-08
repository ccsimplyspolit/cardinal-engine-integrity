# 2026-09-06 — AoE4 gamesource batch analysis

User asked for a full auto-analysis tree modeled on
`C:\killscript\killscript-gamesource`. Created a **separate** folder (not inside
`hh` git):

`K:\aoe4_dlc\aoe4\gamesource`

AoE4 is Relic native, not IL2CPP. Copied pipeline shape only (catalog →
Hex-Rays resume → coverage). No Cpp2IL, no C# restore, no Steam-disk IDB as
source.

## What was already on disk (60644)

`run_analysis.ps1` + `ida_export.py` already started a full Hex-Rays pass:

| Target | functions.jsonl | `.c` files | status.json |
|---|---|---|---|
| runtime_exe (live, canon) | 534584 | ~132237 | decompile, processed 134800, fail 26 |
| original_exe (Steam disk) | 430745 | ~207650 | **do not use** |

`full_dump.i64` is 49 KB — empty minidump load, not a function DB.

## What this turn did

- Scaffold: `README`, `AGENTS`, `meta/paths.json`, `meta/ra-map.json` (44 RA_* + data RVAs).
- Tools: `Inventory-Sources.py`, `Build-Catalog.py`, `Seed-RaSources.py`,
  `tools/ida/full_decompile.py`, `Run-FullAnalysis.ps1`.
- MCP `idb_save` of session `a1220dbc` →
  `aoe4\gamesource\dump\ida-work\runtime_exe.i64` (compressed copy; original
  worker keeps the live IDB).
- Catalogs + junction to the existing 132k pseudocode dir.
- Headless idalib resume on the **copy** (`--no-auto-analysis --cluster-first`),
  writing back into the 60644 `runtime_exe\pseudocode` folder (skip-if-exists).
- Catalog at start: **534584** funcs, **132237** bodies (24.74%), **56865** named
  (mostly MSVC RTTI/`nullsub`, not Relic `Player_*` — those names are XOR'd).
- Decompile pid **45048**, log `aoe4\gamesource\dump\logs\full_decompile.out.log`.
  Opened copy IDB imagebase `0x7FF7A5500000`. Cluster-first wrote **44** RA `src\ra\*.c`
  (Enqueue / 7AB0 / FlushArm / Watcher / WorkQ). Then skipped 132237 and resumed
  at ~500 funcs/s. `src\ra` also has the older curated copies (D02C, Hasher, …).

## Follow-up (same evening)

User asked again to stand up the tree and run batch analysis. Tree already existed;
worker still alive. Added `tools\Harvest-Cli.py`, `tools\Watch-Decompile.ps1`,
wired CLI + SCAR index into `Run-FullAnalysis.ps1`.

| Check | Result |
|-------|--------|
| Hex-Rays pid 45048 | 20:58: **163600**/534587. **23:00:** **306700**/534587 (~57%). **01:01:49:** **done** export **355794** exists **132237** lib **46500** fail **56**; bodies **488031** (91.29%). Worker dead. [hexrays-complete](2026-09-07-hexrays-complete.md) |
| Layer B in `strings.jsonl` | exactly six, count 1 each |
| `TestConfig` plaintext | **0** |
| `Game_IsRTM` | 1 |
| SCAR docs names | 3190; 2038 plaintext in live strings; 1152 XOR/missing |

Do not start a second idalib on the same `dump\ida-work\runtime_exe.i64` copy.

Disk unpack (same tree, later the same day): `tools\unpacker` +
`Run-RelicUnpackPipeline.ps1`. Canon:
[RELIC_UNPACK_ALGORITHM.md](../RELIC_UNPACK_ALGORITHM.md).

## Do not

- Re-open Steam `RelicCardinal.exe` for auto-analysis
- Resume `original_exe` decompile
- Plant any RA heartbeat / Watcher stub
- Copy game PE/SGA binaries into gamesource

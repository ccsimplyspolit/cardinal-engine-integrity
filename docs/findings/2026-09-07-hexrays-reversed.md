# 2026-09-07 — one Hex-Rays function per file under `reversed/`

User: «каждую функцию в папку `\reversed\` в отдельный файл» + commit/push.

## Where

User asked to keep the tree **in this overlay repo**. Tracked path:

`AOE4HOOK/reversed/<bucket>/<Name>_0xRVA.c`

On disk that folder is a junction to
`K:\aoe4_dlc\aoe4\gamesource\reversed` (one copy). Workspace
`K:\aoe4_dlc\hh\reversed` points at the same tree.

Bucket = `RVA & ~0xFFFFF` (same 1 MiB windows as readable shards). Flat 488k
in one NTFS directory is not usable.

## Source

Split of already-cleaned `src/readable/shards` (runtime 60644). Not a second
Hex-Rays pass. Not original Relic C++. Export wrote **488 031** files in 87
buckets, 156.3 s.

- exporter: `AOE4HOOK/tools/Export-Reversed.py`
- wrapper: `AOE4HOOK/tools/Run-ExportReversed.ps1`
- path/split helpers + tests: `AOE4HOOK/tools/ida/readable.py` / `test_readable.py`
- index: `AOE4HOOK/meta/reversed-index.jsonl`
- coverage: `AOE4HOOK/meta/reversed-coverage.json`

Example: `reversed/03D00000/RA_Enqueue_0x3DD2550.c`

## Git

Only `evers1nce1/AOE4HOOK`. The extra `ccsimplyspolit/aoe4-gamesource` remote
is deleted; do not recreate it.

## Do not

- Mix VAs (imagebase `0x7FF7A5500000`)
- Treat 488k files as understood C++
- Start a second idalib on the worker copy IDB

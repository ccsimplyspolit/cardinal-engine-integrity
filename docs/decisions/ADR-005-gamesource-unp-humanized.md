# ADR-005: Humanized unpack-disk is a classified overlay, not a second gamesource

## Status

Accepted

## Date

2026-09-08

## Context

`RelicCardinal.unpacked_static.exe` is a PE. It is not readable C. The user
asked for `gamesource_unp_humanized` on top of unpack-disk. A second 534k
Hex-Rays pass on that PE would spend most of its budget on dest0 leftover
(session RA), which is the wrong image for RA bodies and duplicates the
60644 runtime catalog.

## Options considered

### A. New IDB + full Hex-Rays on unpacked_static
- Pros: PE preferred base `0x140000000`
- Cons: days of idalib; leftover dest0 still not live RA; SCAR names stay XOR

### B. Copy all 488k live shards and pretend they are static
- Cons: leftover spans would be labeled as disk plaintext

### C. Classify named catalog vs static bytes; copy C only on match (chosen)
- Pros: reuses 60644 Hex-Rays where compact XOR already matches live;
  leftover stays a map; small git tree
- Cons: not 488k coverage; leftover functions stay cards / live-only

## Decision

**C.** Tree: `AOE4HOOK/gamesource_unp_humanized/`. Exporter:
`gamesource/tools/Export-UnpHumanized.py` (`python -m unpacker humanize`).
Canon bodies remain `gamesource/` (runtime IDB). Canon crypt remains
`docs/RELIC_UNPACK_ALGORITHM.md`.

On 16.3.11308.0 the 66 named RVAs are `static_match` (0 leftover overlap).
Global leftover is still 651 472 B / 2636 runs.

## Consequences

- Do not open Steam exe or `unpacked_static.exe` as the IDA canon
- Do not plant RA because a humanized tree exists
- After a patch: `rediscover` → `unpack-disk` → `humanize`

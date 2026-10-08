# ADR-003: Relic disk unpacker is layered; oracle PE first

## Status

Accepted

## Date

2026-09-06

## Context

On-disk `RelicCardinal.exe` `.text` is ~79% ciphertext. We already have
a live image and a spliced analysis PE. The user wants a real unpacker
(understand the crypt, strip it step by step). A one-shot XOR / dearxan
/ VMP-Deob pass is already disproven.

## Options considered

### A. Only keep the oracle splice
- Pros: IDA-ready today; matches 60644 live `.text`
- Cons: no model of the crypt; every patch still needs a live dump

### B. Static key-stream unpacker (C⊕P period-N)
- Already **false**: 0 repeating 16/32-byte keys

### C. Layered unpacker (atlas → hunt stub → emulate / reimplement)
- Pros: each negative is recorded; stub hunt is evidence-gated
- Cons: full static unpack was blocked until the writer was named
  (`RA_Integrity_Dispatcher+0x183C`). That gate **landed** 2026-09-06.

## Decision

**C**, with **A** as the analysis image (60644 live `.text`). Step 5
is `python -m unpacker unpack-disk` → `RelicCardinal.unpacked_static.exe`
(99.276–99.328% vs every full dump; leftover = post-unpack RA). Gold
splice is 100% vs 52968 T+20s only.

CLI lives in `aoe4\gamesource\tools\unpacker\`. After a patch:
`python -m unpacker rediscover` (form hunt → `meta/unpacker-recipe.json`),
then `unpack-disk`. One wrapper: `Run-RelicUnpackPipeline.ps1`.
Oracle stays `AOE4HOOK\tools\rebuild_relic_analysis_pe.py`. Canon:
`AOE4HOOK/docs/RELIC_UNPACK_ALGORITHM.md`. Do not overwrite Steam.
Do not disassemble encrypted `.text`. Do not run dearxan.

## Consequences

- Findings go in `2026-09-06-relic-unpacker.md`
- 100% vs late live is **not** a disk-unpack target (RA keeps writing)
- `.rdata` native-name XOR is a separate ritual; static/oracle PEs keep
  disk ciphertext for `Game_IsRTM` etc.

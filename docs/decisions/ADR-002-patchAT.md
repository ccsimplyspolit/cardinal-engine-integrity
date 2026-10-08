# ADR-002: patchAT is a separate RA-site lab, not DllInjector

## Status

Accepted

## Date

2026-09-06

## Context

Hide (rbhost / VERSIONINFO / titlehide / relicconnect) does not keep
`slots=0` once Relic's Watcher/sibling period runs (cycle 7 +15 s, cycle 8
at dbg start, needles-final none). Overlay Relic `.text` neutralize is
compile-off (`AOE4H_RA_TEXT_NEUTRALIZE=0`) because hasher/JUMPOUT and PID
36000 IAT pack. The user wants an **IDA + live attach** loop that stubs
every function that grows slots, without loading more logic into
`InternalInjector.dll`.

## Options considered

### A. Turn neutralize back on inside InternalInjector
- Pros: already in-process, Present re-arm
- Cons: same hasher surface; overlay boot already has DXGI/SCAR; LNK1104
  while Relic holds the DLL; mixes product overlay with RA lab

### B. Keep hiding x64dbg chrome
- Pros: no Relic `.text`
- Cons: cycle 5–8: attach packs `01010001`; launch/period packs `20220002`
  even with Hidden host and bland titles

### C. External `patchAT.exe` (chosen)
- Pros: own OutDir; WPM catalog; save/restore; watch loop; add RVA after
  each IDA hit without rebuilding the overlay
- Cons: Relic `.text` is still hasher-visible; watcher-only (36000) left
  an IAT pack; `--enqueue` is nuclear

## Decision

`AOE4HOOK/patchAT/` is the lab. **`--apply` with empty mask refuses.**
`--iat` refused after PID **37836** (7AB0 pass → `slots=4` ~4s then dead,
same class as **42764** Watcher). `--ww` still plants if passed.
`--nuclear` killed **40280**. Hasher / JUMPOUT / KickCtor stay banned.
Overlay stay neutralize-off. `--snapww` refused (42848). Live **43676**: 4 heartbeat keys refreshed
by `RA_FlushArm`; stubbing Watcher expires them. `patchAT --hashwalk`
is RPM-only. `--enqsnap` refused (43676). `--packs` refused (6224: Watcher call-nop
+ SNAP still `slots=4` at 3s). `--hashwalk` now logs SNAP∩HashRec.

## Consequences

- New pack tag → IDA `+10` RVA → row in `sites.h` → `--apply` again
- Do not plant OS-export jmps or Relic IAT (packs `0x56FD3C0`)
- Existing slots are not cleared; apply **before** the first Enqueue
- 36000/42764 IAT pack writer is `RA_IatScan_7AB0` `0x3DD7AB0`; stubbing
  7AB0 itself is **37836** (same kick). Do not plant RA-cluster prologues.

# RelicCardinal dump, unpack and offset revalidation — 2026-09-20

The installed executable has not changed relative to the September 6 reference.
FileVersion/ProductVersion remain **16.3.11308.0**; the installed Steam manifest
reports build **24231237**. A September 20 modification time alone is not an
engine update. All 144,752,932 bytes of a fresh static unpack are identical to
the previous static-unpacked PE, including every section, headers and overlay.
No version-driven RVA or structure-layout migration is required.

## Evidence

Source: `D:\SteamLibrary\steamapps\common\Age of Empires IV\RelicCardinal.exe`.

| Artifact | SHA-256 |
|---|---|
| Original encrypted EXE | `5380c577805565817f528af6eac385263413fa6815553f9a31fa62561cb45e8c` |
| Fresh and September 6 static unpack | `bbf7857ccd6d60a335d26a3b8abab80275e99f306b920986b86827ad2b214921` |
| Raw module dump | `0a11cf510ea1e29e49e273e8bc7723f28b5484d9452c6ae240b3aa4040ef98d1` |
| Runtime analysis PE | `1f5fb76852ab6c16311acd5fb383a92c7eb7fc6bfa6f96e28d229a273afe5d2f` |

Evidence directory: `K:\aoe4_dlc\dumps\RelicCardinal_14484_20260920_162737`.
PID 14484, live base `0x7FF78AA80000`, image size `0x8C3D000`.
`dump_relic_module.py` read all **147,050,496 bytes**, with zero skipped guard
regions. This is a complete executable module dump, not a whole-process heap
snapshot. The game remained running. No debugger attach or game writes were used.

- `00007ff78aa80000.RelicCardinal.exe.bin`: original image-layout module dump.
- `RelicCardinal.runtime_analysis.exe`: all eight runtime sections, including
  their full virtual data, with raw offsets adjusted and live ImageBase recorded.
  This is an analysis artifact, not a replacement executable to launch.
- `unpack/RelicCardinal.original.exe`: preserved source copy.
- `unpack/RelicCardinal.unpacked_static.exe`: fresh output of the project unpacker.
- `unpack/unpack-summary.json`: full-PE and per-section comparison with baseline.
- `offsets-audit-final.json`: source-reference audit with per-RVA evidence.
- `offsets-live-final.json`: read-only live prologue/readability checks.
- `scar-natives-decoded.tsv`, `scar-catalog-changes.json`: refreshed peel metadata.

## Unpacker isolation

The legacy pipeline points at a Steam installation on C: and reuses a decoded
pack cache. `tools/unpack_relic_explicit.py` runs its existing `rediscover` and
`unpack-disk` modules with explicit inputs and a new output directory. It does
not reuse the old pack or overwrite the reference artifacts. Unsupported PE
layouts and mismatched live evidence are rejected; this adapter is not a
generic future-version unpacker.

The run rediscovered the same seed/R8 and all four unique RA signatures at their
existing RVAs. It applied **105,383 records**, with **zero skipped**. The final
4,096-byte plaintext `.text` tail, outside the legacy encrypted-page count, was
checked against the live dump. Static `.text` agrees with live by 99.323%; the
remaining session-dependent integrity bytes are the documented runtime layer,
not a version shift or missing compact records.

## Offset coverage and catalog corrections

The refreshed inventory covers **803 source references / 638 unique RVAs**:

- **592** code/read-only locations match the fresh runtime bytes after ASLR
  normalization. Where `.pdata` provides a range, the whole range is compared;
  otherwise a 32-byte span is compared. A `.pdata` range can be a function part.
- **46** mutable globals retain the same static definitions and addresses.
  Their live values are not expected to equal the file initializer.
- All **390** SCAR table rows are included, including the decimal-zero inner
  entry previously missed by the regex. The live verifier reports **50/50**
  primary checks and **390/390** native-row readability checks.
- The helper-DLL RVA in `licensed_helper_map.cpp` is explicitly excluded from
  the RelicCardinal inventory.

Full static-PE identity also rules out version drift for inline constants and
structure field offsets. It does not independently prove every historical
symbol label or exercise heap layouts in a match: this dump was taken in the
menu, where the AI-player list was null.

An existing extraction defect was discovered: `PeelWrapper` scanned individual
bytes for `E8`, accepted targets up to base+256 MiB, and walked past returns.
For `Misc_DoWeaponHitEffectOnPosition`, the `E8` ModRM byte of
`41 0F B6 E8` at RVA `0x1AC19DD` produced the bogus inner RVA `0x9F6A52D`,
outside the image. The first actual call is at `0x1AC19F6`, targeting `0x935BB0`.
Other examples borrowed calls from a neighbour: `EGroup_Count` has no inner
call; `Player_CanSeeEntity` and `Player_CanSeeSquad` tail-jump to `0x1DFFB70`
and `0x1E005A0` respectively.

The live collector now uses HDE64 instruction boundaries, stops at returns,
tail jumps, unsupported or truncated instructions, and accepts targets only
inside `.text`. Refreshed **58 diagnostic inner entries** in the merged SDK;
the 380-row source JSON/TXT catalogs retain their existing name coverage.
Actual wrapper RVAs are unchanged. A zero inner means the bounded walk did
not establish a target; it does not remove the native or claim it has no calls.
Some formerly populated entries were outside the 80-byte window and are now
left unresolved. These fields are diagnostic metadata, not gameplay call sites.

HDE64 and independent Capstone decoding agreed on **all 390 rows**. The live
verifier now rejects out-of-image/unreadable inners, wrong image sizes and
invalid SDK entries instead of returning success while skipping them.

## Validation

- Nine C++ regression checks cover operand-byte false calls, neighbouring
  functions, tail jumps, validator/inner pairs, truncation and range bounds.
- Six offline verifier tests cover failures previously silently accepted.
- Fresh module audit: no unmatched code/read-only locations or out-of-range RVAs.
- `InternalInjector` built successfully as `Release|x64` using
  `internal/x64/Release_ai_civ` as OutDir. The rebuilt standalone carries this DLL
  and the HDE64 license.

No in-match behavior test or reinjection was performed during this read-only
dump/audit session. The game executable and its running code were not modified.

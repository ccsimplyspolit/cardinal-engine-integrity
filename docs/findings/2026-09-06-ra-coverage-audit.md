# 2026-09-06 — RA coverage audit (what is 100%, what is not)

IDB `runtime_exe.i64` session `a1220dbc`, imagebase **`0x7FF7A5500000`**.
Build **16.3.11308.0**. **RVAs only.** This note exists because plant
decisions (`--enqsnap` / `--packs`) were made on a **partial** call graph:
Enqueue-only. That was incomplete. This pass enumerates the **other** arm.

## Verdict

I did **not** have 100% coverage before this audit. After this pass:

| Surface | Coverage | Evidence |
|---------|----------|----------|
| `RA_EventSchedule` **code** xrefs | **100 / 100** (`next_offset=null`) | `xref_query` to `RA_EventSchedule` |
| `RA_Enqueue` **code** xrefs | **62 / 62** (+ 1 data = 63 total earlier) | `xref_query` |
| `RA_KickCtor` | **1 code** (inside Enqueue) + **2 data** ptrs | `xref_query` any |
| `RA_TimerQ_Push` | **1 / 1** — only EventSchedule | `xref_query` |
| `RA_IatPack_77E8` callers | **8 / 8** | 4 inside 7AB0 + 4 helpers |
| `RA_IatPack_C8E4` callers | **7 / 7** | 4 helpers + CreateFileA/W/Sleep |
| `RA_FlushArm` callers | **16 / 16** | Watcher ×3, sibling ×1, helper, 11 clones |
| `mov r8d, 20220002h` | **37 / 37** | `find_bytes` |
| `mov r8d, 20DE00ADh` | **11 / 11** | `find_bytes` |
| `mov r8d, 021C0001h` | **2 / 2** | FlushArm + E300 |
| `cmp byte ptr [rax], 0CCh` in RA cluster | **2** (CAF8, 1FDC) + 1 outside (`0x7AC6C2AAE`) | `find_bytes` `80 38 CC` |
| Dump vs IDA bytes at 7 choke RVAs | **60644 runtime = 26392 pe-sieve = IDA** | Python slice |
| Steam / `modules_disk` Relic `.exe` | **encrypted, must not use** | same 7 RVAs mismatch |
| Full Hex-Rays of Watcher `0x422F` | **NOT** (MCP truncates; used xrefs + disasm) | — |
| Full Hex-Rays of FlushArm `0x1B97` | **NOT** (truncated earlier) | — |
| Full Hex-Rays of 7AB0 `0x1055` | **NOT** (truncated; callees catalogued) | — |
| 18816 / 53820 **full .dmp** page extract | **NOT this turn** | version+size match only |
| Older IDB `7ff6f65c0000.i64` | **NOT opened this turn** | same build expected |
| 11 clone bodies line-by-line | **NOT** (same size/`FlushArm`+`EventSchedule`+`Enqueue` pattern) | — |

So: **xref catalogs for the kick/slot pipeline are complete.** Full
decompile of the three huge functions is **not**. Plants that ignore
EventSchedule are incomplete by construction.

## Why `--packs` was the wrong cut

Watcher is not “4× Enqueue”. It is:

| Kind | Count | Example RVA |
|------|-------|-------------|
| `RA_FlushArm` | 3 | `0x3F0A851` `0x3F0B021` `0x3F0CEEF` |
| `RA_EventSchedule` | **6** | `0x3F0BFC4` `0x3F0C6A0` `0x3F0CC63` `0x3F0D93F` `0x3F0DF1A` `0x3F0E7B9` |
| `RA_Enqueue` | 4 | `0x3F0C142` `0x3F0C835` `0x3F0DA8B` `0x3F0E07B` |

Disasm at `0x3F0BFC4`: title-match path does
`mov r9d, 8000100h` then **`call RA_EventSchedule`** *before* the Enqueue
at `0x3F0C142`. `--packs` nop’d only the `E8` to Enqueue. The timer arm
stayed. Sibling: **2 EventSchedule** + 2 Enqueue. CAF8: **2 EventSchedule**
+ 1 Enqueue. 1FDC: **6 EventSchedule** + 3 Enqueue. 77E8/C8E4: EventSchedule
**first**, then Enqueue `20DE00AD`.

KickCtor **code** xref is still only Enqueue. The death without slots
(43676) is EventSchedule → TimerQ → later KickCtor (or the two KickCtor
**data** ptrs `0x7AF45318` / `0x7AF45324`).

## EventSchedule callers (100 sites, unique functions)

| Function | RVA | EvSched × | Enqueue × |
|----------|-----|-----------|-----------|
| `RA_Enqueue` | `0x3DD2550` | 2 | (self) |
| `RA_IatPack_77E8` | `0x3DD77E8` | 1 | 1 |
| `sub_…A004` | `0x3DDA004` | 3 | 0 |
| `sub_…B29C` / `B424` / `B60C` / `B7B8` | 7AB0 family | 1 each | 1 each |
| `RA_IatPack_C8E4` | `0x3DDC8E4` | 2 | 1 |
| `RA_TopValidator_D02C` | `0x3DDD02C` | 1 | 1 |
| `sub_…E3534` | `0x3DE3534` | 1 | 0 |
| `RA_RetaddrInt3_CAF8` | `0x3E1CAF8` | 2 | 1 |
| `RA_Scan_E300` | `0x3E1E300` | 2 | 1 |
| `RA_RetaddrInt3_1FDC` | `0x3E41FDC` | 6 | 3 |
| `RA_Integrity_Dispatcher` | `0x3E44034` | 5 | 3 |
| `RA_Integrity_45E8` | `0x3E545E8` | 4 | 3 |
| `sub_…58794` | `0x3E58794` | 1 | 0 |
| `RA_StringPack_2022` | `0x3E5D6F0` | 1 | 1 |
| `sub_…652DC` | `0x3E652DC` | 3 | 2 |
| `sub_…678E0` | `0x3E678E0` | 2 | 2 |
| `RA_FlushArm` | `0x3E8B3A0` | **2** | 1 (`021C0001`) |
| `sub_…8F644` | `0x3E8F644` | 1 | 1 |
| `sub_…94180` | `0x3E94180` | 2 | 1 |
| `sub_…A6BE0` | `0x3EA6BE0` | 2 | 1 |
| `RA_SiblingClassifier` | `0x3EAFA2C` | 1 | 0 |
| `RA_EpInt3Ctor` | `0x3EC3200` | 2 | 1 |
| `sub_…C6E64` / `D6604` / `DC9F8` / `03D80` | helpers | 1–2 | 1 |
| `RA_WindowWatcher` | `0x3F0A7D0` | **6** | 4 |
| `sub_…2D044` | `0x3F2D044` | 2 | 1 |
| `RA_WindowWatcher_Sibling` | `0x3F328D8` | **2** | 2 |
| `sub_…3424C` | `0x3F3424C` | 1 | 0 |
| MSVC `UnDecorator` | `0x3F3D75C` | 1 | 1 (false +) |
| 11 clones `0x3F59650`…`0x3F6ECE0` | ~`0x225D` each | **3 each** | **2 each** |

`sub_…A004` is **not** a SNAP memcmp. It formats SHA-256 hex blobs and
EventSchedules on `switch (v35)` cases 1/2/3. Do not treat it as the
7AB0 compare.

## Dump / static byte compare (16 bytes)

| Image | Enqueue / 7AB0 / Watcher / EvSched / FlushArm / Ww `E8`s |
|-------|----------------------------------------------------------|
| IDA `runtime_exe.i64` (60644) | baseline |
| `modules_runtime\RelicCardinal.exe.memory.bin` (60644) | **identical** |
| pe-sieve `26392` `00007ff7007b0000.RelicCardinal.exe.bin` | **identical** |
| Steam / `modules_disk` Relic `.exe` | **garbage** (encrypted) |

18816 / 53820 live CSVs: same file version **16.3.11308.0**, same
`147050496` image size as 60644. RVA copy is valid. I did **not** pull
those two 6 GB `.dmp` pages this turn.

## What this changes for the plant

A plant that only nops `call RA_Enqueue` cannot keep the game alive:
EventSchedule in the same fail-block still arms KickCtor. A plant that
stubs Enqueue’s body (43676) leaves every EventSchedule site live.

To actually stop slots **and** the 4–8 s death you must cover **both**
graphs, or a data-only gate that both read (not found; HashMap ∩ SNAP =
0 on 40888).

Writing Watcher `.text` still trips 7AB0 → 77E8 (6224 `slots=4`) even
when SNAP bytes are updated. 7AB0’s **compare algorithm** is still the
open Hex-Rays hole (function `0x1055`, 167 blocks). That is the one
remaining static gap that blocks a safe `.text` plant.

## Do not

- Analyze Steam `RelicCardinal.exe` on disk
- Claim Watcher is Enqueue-only
- `--packs` / `--enqsnap` again
- Mix VAs across 60644 / 26392 / 18816 / 53820

# 2026-09-06 — max decrypt map (gamesource, no extra IDB copy)

User: no resource cap; analyze disk + every runtime dump; use `C:\vmp\disasm`;
decrypt as far as possible. **Did not** copy the 5 GB loose IDB (`.i64+.id0+.id1`).
**Did not** open Steam PE or `original_exe.i64` as code. MCP/Hex-Rays resume
on the compressed IDB copy is untouched.

## What is already plaintext

Unrelocated `.text` (preferred `0x140000000`):

| Pair | pages same / differ |
|---|---|
| Steam disk == 60644 `modules_disk` | **22236 / 0** (SHA identical) |
| 60644 runtime PE == `memory.bin` | **22236 / 0** |
| **unpacked_analysis.exe == 60644 live** | **22236 / 0** |
| Steam disk vs live | 4596 / **17640 (79.33%)** |

So the **entire `.text` cipher is already lifted**. The analysis PE
`K:\aoe4_dlc\analysis\game_16.3.11308\RelicCardinal.unpacked_analysis.exe`
is the decrypt (disk headers + live `.text` + overlay stripped).

Spot-check (16 bytes):

| RVA | disk | all live + unpacked |
|---|---|---|
| Enqueue `0x3DD2550` | garbage `0011dcf6…` | `44 89 4C 24 20` prologue |
| 7AB0 `0x3DD7AB0` | garbage `427a92f1…` | `48 89 5C 24 20` prologue |
| Watcher `0x3F0A7D0` | same MSVC prologue (island) | same |
| EP `0x4FB0884` | `48 83 EC 28` CRT | same on disk and live |

26392 pe-sieve vs 60644 live: **214 pages (0.96%)** differ after unreloc.
**194 / 214** sit in RA band `0x3DD0000–0x3F90000` — runtime integrity /
self-mod after unpack, **not** leftover disk crypt. Two 26392 captures of
the same PID differ by 127 pages (same class). Extra dumps do not unlock
more of the Steam file.

## Still opaque (not `.text`)

| Blob | Why it stays shut |
|---|---|
| Steam overlay `0x8076800` **10 049 828** B | **Closed 23:34.** AEAD → `pack-decoded-static.bin`. Form hunt: `python -m unpacker rediscover`. Canon: [RELIC_UNPACK_ALGORITHM.md](../RELIC_UNPACK_ALGORITHM.md). This row was true at write time (overlay extracted, not decoded). |
| 13 Data.sga map `.lua` | AES-128 \| BufferCompress. No key in the install. |
| 1152 / 3190 SCAR names | not in live `strings.jsonl` — XOR wrappers. 2038 names **are** plaintext in the runtime image. |

`C:\vmp\disasm\mydisasm.exe` is a PE/RAW disassembler (LLVM), **not** a
VMProtect unpacker. Relic is not VMP. Do not run `C:\vmp` VMP tools on it.

## What this turn wrote / launched

- Junctions: `aoe4\gamesource\src\linked\*` → Steam, all dumps, SGA unpack,
  AOE4HSettings, `C:\vmp\disasm` (no binary copies).
- `tools\Compare-AllImages.py` → `meta\crypt-compare.json`
- `tools\Diff-LivePages.py` → `meta\live-page-diff.json`
- `tools\Index-ScarNatives.py` → 3190 names, `src\scar\function_list.txt`
- mydisasm RAW of RA RVAs → `src\disasm\ra\` (Enqueue 262 insns on live image)
- mydisasm full analyze of **unpacked** PE pid **32528** → `dump\mydisasm\`
- Hex-Rays resume still pid **45048**: ~163k/534k processed (do not attach IDA)

## Downloads `7ff6f65c0000` IDB

`C:\Users\sshunko\Downloads\sshunkogram Desktop\7ff6f65c0000.RelicCardinal.exe.i64`
is the **thin** pe-sieve IDB (PID 16024, base `0x7FF6F65C0000`, 1.81 GB).
Not Steam-disk. Not 60644. Not a byte-copy of `K:\aoe4_dlc\7ff6f65c0000…`
(2.49 GB, more analysis). Same RVAs; 303k vs 535k functions. Working
`.id0/.id1` showed up 20:53 after an earlier MCP open. Do not switch the
Hex-Rays resume onto it. Details: [relic-cmdline-flags](2026-09-06-relic-cmdline-flags.md#downloads-7ff6f65c0000-idb--same-image-less-analysis).

## Do not

- Copy `.id0/.id1` or reopen `original_exe.i64`
- Treat overlay / 13 AES maps as “just need another dump”
- Plant Watcher / 7AB0
- Mix VAs from `0x7FF6F65C0000` with 60644 `0x7FF7A5500000`

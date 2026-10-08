# 2026-09-06 — VMP-Deob vs RelicCardinal

User asked to read all of https://github.com/ccsimplyspolit/VMP-Deob then
decrypt Relic. The GitHub URL is **private (404)**. Local clone:

`C:\Users\sshunko\source\repos\VMP-Deob`

## What VMP-Deob actually is

Private research repo for **VMProtect 3.6+** (reference target
`FuckVacAgain.dll`, CS2). Six layers:

1. Packer — **all** `.text/.rdata/.data` `raw_size=0` on disk; payload in `.#?n`
2. VM — encrypted p-code + handler dispatch (`jmp r10` / classic table)
3. MBA entry stubs
4. AntiDebug — `int 2Dh`, direct syscall, `rdtsc`
5. AntiTamper — A/B/A routing CRC + self-scan
6. Junk sleds

Tools that matter conceptually: `extract_key_stream.py` (`C ⊕ P` → XOR
stream), `section_truth_map.py`, `vmp_unpacker_v36.py` (live section dump →
clean PE), `fva_devirt` (static VMP fingerprint). Full source-equivalent
devirt is explicitly out of scope (points at VMPAttack/NoVmp).

Not read cover-to-cover (VMP-only, not Relic): leaked `third_party/vmp-3.5.1`
(103 MB), `VMP_FULL_STUDY.md` 64 KB, PDFs, `bypass_kit` kernel, FVA handler
JSONL. Those assume a VMP VM.

## Relic is not VMP

Steam `RelicCardinal.exe` vs VMP 3.6 layout:

| Test | VMP 3.6 | Relic |
|---|---|---|
| `.text` raw_size | **0** | **`0x56DD000`** (full) |
| `.#?n` / `.#I5` / `.vmp*` | required | **none** |
| zero-raw sections | most of them | **none** |
| IAT | stubbed through VMP | normal MSVC |
| EP | VM stub | CRT `48 83 EC 28` on disk **and** live |

`CD 2D` / `add rsp,138h; ret` hits on the Steam PE are ciphertext false
positives (encrypted `.text` + overlay). Do not treat them as VMP AntiDebug.

**Did not** run `vmp_unpacker_v36.py`, `fva_hookbp`, `bypass_kit`, or VMPHide
on Relic / RelicCardinal.

## The one method that transfers: `C ⊕ P`

Same idea as `tools/analysis_suite/extract_key_stream.py`. Disk `.text` ⊕
60644 live `.text` (RVA-aligned):

| | |
|--|--|
| differ pages | 17640 / 22236 (79.33%) |
| repeating 16-byte XOR key | **0** pages |
| repeating 32-byte XOR key | **0** pages |
| unique per-page stream | **17640** |
| entropy on differ pages | 6.737 |
| autocorr period 16 / 4096 | 8.1% / 9.3% (not a usable period) |

VMP's OpcodeCryptor is XOR-only, so `C ⊕ P` recovers a reusable stream.
Arxan-class Relic does **not**: each encrypted page has its own stream.
There is **no** static period-N key that decrypts the Steam exe without the
live image.

`vmp_unpacker_v36` “read runtime sections, write clean PE” is already what
`modules_runtime\RelicCardinal.exe.memory.bin` +
`RelicCardinal.unpacked_analysis.exe` are.

Script: `aoe4\gamesource\tools\Recover-RelicKeyStream.py`  
Report: `aoe4\gamesource\meta\vmp-deob-vs-relic.json`

## Still encrypted after this

**Update 23:34:** overlay AEAD is ours (`unpack-disk` / `rediscover`), not
VMP-Deob. Still shut: 13 AES map luas, XOR SCAR names. VMP-Deob opens
none of them. Canon: [RELIC_UNPACK_ALGORITHM.md](../RELIC_UNPACK_ALGORITHM.md).

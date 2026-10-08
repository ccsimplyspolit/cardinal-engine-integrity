# 2026-09-06 — on-disk `RelicCardinal.exe` crypt

Build **16.3.11308.0**. Steam path
`C:\Program Files (x86)\Steam\steamapps\common\Age of Empires IV\RelicCardinal.exe`
(144 752 932 bytes). Runtime image
`K:\aoe4_dlc\dumps\RelicCardinal_60644_20260906_full_analysis\modules_runtime\RelicCardinal.exe.memory.bin`
(147 050 496 = `SizeOfImage` `0x8C3D000`). Compare by **RVA** (memory.bin is image layout, not file raw).

## What it is not

No brand strings / sections for **SteamStub**, **Denuvo**, **VMProtect**, **Themida**, **Enigma**. No `.bind` section. `UPX` hit is ciphertext (`UPXX`), not a packer. Import table on disk is a normal MSVC IAT (IPHLPAPI / WS2_32 / CRYPT32 / …). EP RVA `0x4FB0884` is the same CRT stub on disk and in the live image (`48 83 EC 28 E8 …`). Authenticode security dir is empty.

`C4SP3R.exe` is a SCAR-name dumper, **not** an unpacker. Do not run it.

## What it is

Three layers:

| Layer | On disk | What it does |
|-------|---------|--------------|
| Steamworks | `steam_api64.dll` string; no SteamStub overlay magic | Must launch via Steam. Not the `.text` cipher. |
| **Aegis** (vendor not publicly known) | no brand strings in the exe; its build log `Aegis_RelicCardinal.log` ships in the game folder ([below](#aegis-build-log)) | Virtualization + in-place **selective** `.text` encrypt; appends the overlay “virtual map”. PE headers / IAT / EP stay valid. |
| Relic custom | RA hasher, DualFlag, FairPlay, XOR native names | Runtime integrity / reporting. Not the disk cipher. |

Historical context only: the CODEX 2021 NFO named the stack **Steam + Arxan + Custom**. That was a scene label for a 2021 build, not evidence about 16.3; the Aegis log is direct evidence and replaces it.

### Aegis build log

`D:\SteamLibrary\steamapps\common\Age of Empires IV\Aegis_RelicCardinal.log` (1 611 bytes, mtime 2026-07-19 02:29, read 2026-09-28) is the protector's build log for `RelicCardinal.exe`. Its block list comes from `engine/tools/Foreign/Aegis/Retail/internal/BlockList.json` — Relic files Aegis as a third-party (`Foreign`) tool.

| Log line | What it says |
|----------|--------------|
| 12–16 | `Virtualization Seed: 1187590981`; `Pre-Main Stealth Startup: Enabled`; `Installed Stealth-Startup` |
| 17, 52 | 233 fake instructions inserted (`Instruction Count: 172498 (+233)`) |
| 18–19 | `RTTI Processing: RelicCardinal.exe`; `RTTI Patching 21731 objects` |
| 21–47 | BlockList.json 642 items (464 unique); studio report 6 / block 6 / notify 25; **Aegis block 386**, **Aegis report 41**; DirectX permit 3, Only-If permit 17, signed permit 7, always permit 0 |
| 49 | `Appending virtual map @ offset 0x8076800 for 10049732 bytes` |
| 51–55 | signed (seed as line 12); `DFH Bytes: 55356383`; `Metadata Size: 10049804`; `Virtualization Successful` |

**Hypothesis (not verified):** `RTTI Patching 21731 objects` may explain why sim-core classes (`Entity` / `Squad` / `Player`) are missing from `sdk/rtti/classes.tsv` (9 079 rows; 0 hits for `.?AVEntity@@` / `.?AVSquad@@` / `.?AVPlayer@@`). If Aegis rewrites or strips the RTTI of the objects it patches, an RTTI scan of the runtime image cannot see them. Not checked: which 21 731 objects were patched, and whether the missing classes are among them.

`.text` vs 60644 image: **17 640 / 22 237** 4 KiB pages differ (~79 %). **4 597** pages identical (plaintext islands, including a 5.5 MiB block at RVA `0x516B000` and the EP neighborhood). RA cluster `0x3DD0000–0x3DE0000` is mixed at 32-byte grain (1012 same / 1036 differ). Enqueue `0x3DD2550` and 7AB0 `0x3DD7AB0` are garbage on disk, real prologues in memory. XOR of those 64 bytes is high-entropy (not a repeating key).

Watcher `0x3F0A7D0` first 16 bytes match (MSVC prologue); the containing page is **not** wholly identical.

First 1 MiB of `.text`: disk entropy **7.913** vs live **6.921**. Slice `+0x100000` is a full 1 MiB **identical** island (entropy 6.504).

Overlay after last raw section (`0x8076800`, **10 049 828** bytes): entropy **7.999**, no `STEAM`/`VALVE` magic, “MZ” at +3658 is a false hit (`e_lfanew` junk). Not mapped into `SizeOfImage` — the runtime dump is zeros there. It is the Aegis “virtual map”: the log appends it at the same offset `0x8076800` (10 049 732 bytes; `Metadata Size: 10049804`). The 96 extra bytes on disk are not analyzed. Encrypted, not a second PE you can open.

`.rdata` start differs because of ASLR fixups, not encryption.

## Can we strip it?

The decrypted image **already exists**: pe-sieve / `modules_runtime\*.memory.bin` / IDA `runtime_exe.i64` (imagebase `0x7FF7A5500000`). That is the runtime lift. Analysis-only splice (disk headers + live `.text`): `K:\aoe4_dlc\analysis\game_16.3.11308\RelicCardinal.unpacked_analysis.exe` — see [game-folder-unpack](2026-09-06-game-folder-unpack.md). dearxan is FromSoft-only (wrong Arxan shape). **Update 23:34:** no-game static unpack is ours — `python -m unpacker unpack-disk` / `rediscover`. Canon: [RELIC_UNPACK_ALGORITHM.md](../RELIC_UNPACK_ALGORITHM.md). History: [relic-unpacker](2026-09-06-relic-unpacker.md).

Do not analyze Steam `RelicCardinal.exe` as code. Do not run dearxan / VMP-Deob.

## Do the extra dumps help decrypt the disk file?

**They already did the only useful part.** 60644 is a complete pair in one capture:

| File | What |
|------|------|
| `modules_disk\RelicCardinal.exe` | Steam ciphertext (same class as the install exe) |
| `modules_runtime\RelicCardinal.exe.memory.bin` | in-place plaintext after Aegis finished |
| `RelicCardinal_full.dmp` (~11 GB) | whole process **after** unpack |

Other Relic dumps (18816, 26392 pe-sieve, 37716, 40392, 53820, …) are the **same build**, same `SizeOfImage` `0x8C3D000`, taken from a **running** game (menu / match / STK up). 26392 `.text` at Enqueue / 7AB0 / Watcher already matched 60644. More PIDs = more ASLR copies of the same plaintext, not a second cipher.

What extra late dumps do **not** give:

- the page-key schedule (Aegis does not leave a repeating XOR; one C↔P pair already covers every encrypted page)
- a pre-TLS / create-time image (none of these dumps are that)
- a reason to keep opening on-disk PE in IDA

The 6–11 GB full dumps *could* still hold leftover heap state of the decryptor. That is a separate hunt, not “more dumps automatically unlock the exe”. For RE/RA the runtime module image is enough.

## Detect It Easy / NFD (user scan of Steam exe)

Reports next to the install exe (2026-09-06):

- `RelicCardinal.exe.DiE.txt`
- `RelicCardinal.exe.NFD.txt` (Nauz File Detector, same horsicq family)

Both say **PE64**, **MSVC 19.42.34444 / VS 2022 17.12**, Steam + D3D12 + Wwise. **No** SteamStub / Denuvo / VMP / Themida / Arxan name.

| Heuristic | DIE | NFD |
|-----------|-----|-----|
| Packer / protector | `(Heur) Packer: Generic` — `.text` compressed + strange overlay + high entropy | `(Heur) Protector: Generic [High entropy]` |
| Overlay | `0x08076800` size `0x995924` — **Неизвестно** | same offset/size — **Unknown** |

That overlay is the ~10 MiB blob we already measured (`0x8076800`, entropy 7.999). DIE/NFD stop at “generic high entropy”. They confirm the PE looks like a normal MSVC link with a packed `.text` and an unknown tail. They do **not** name a unpacker or give a key.

Other AoE4 tree exes (`EssenceEditor`, `GPUBurner`, BugSplat, `WebClient`) are separate binaries — not this crypt.

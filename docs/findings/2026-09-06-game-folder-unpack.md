# 2026-09-06 — Steam folder: what can be unpacked

Install: `C:\Program Files (x86)\Steam\steamapps\common\Age of Empires IV`
(build **16.3.11308.0**). Steam tree **not overwritten**. Output under
`K:\aoe4_dlc\analysis\game_16.3.11308\`.

## RelicCardinal.exe

On-disk `.text` is Arxan-class in-place crypt ([relic-disk-crypt](2026-09-06-relic-disk-crypt.md)).
Rebuilt analysis PE from 60644 `modules_runtime` + disk headers:

`K:\aoe4_dlc\analysis\game_16.3.11308\RelicCardinal.unpacked_analysis.exe`

- 17 640 / 22 237 `.text` pages replaced
- overlay ~10 MiB stripped
- ImageBase still `0x140000000` (disk `.rdata` / relocs kept)
- **IDA/DIE only.** Not a launcher. Do not copy over Steam exe.

User DIE/NFD dumps of the Steam exe: generic MSVC + high-entropy `.text` + unknown overlay `0x8076800`. No named packer. See [relic-disk-crypt](2026-09-06-relic-disk-crypt.md#detect-it-easy--nfd-user-scan-of-steam-exe).

Live image remains the canon: `modules_runtime\RelicCardinal.exe.memory.bin` /
IDA `runtime_exe.i64`.

**Update 23:34:** no-game static unpack is `python -m unpacker unpack-disk`
→ `RelicCardinal.unpacked_static.exe` (leftover = session RA). Overlay
AEAD is decoded; this oracle PE still strips overlay rather than
decrypting it. Canon: [RELIC_UNPACK_ALGORITHM.md](../RELIC_UNPACK_ALGORITHM.md).

## SGA (156 archives)

Relic `_ARCHIVE` v10. Almost all files are Store / zlib BufferCompress — **not
encrypted**. Already extracted (data, not Art/Sound/DX12):

`K:\aoe4_dlc\analysis\game_16.3.11308\unpacked\`

(`cardinal/archives/Data` ≈ 11 517 files; plus Campaign/Cordoba/Locale/UI/Xp3,
engine/common/tools Data).

**13 files** in `cardinal\archives\Data.sga` use storage byte `0x12` =
`AES128 | BufferCompress` (zlib then AES-128). Map luas only:

`scar/terrainlayout/skirmish_maps/{acropolis,african_waters,cliffside,golden_pit,gorge,haunted_gulch,highland,migration,mystical_river,sacred_crest,volcanic_island,wadden_sea}.lua`
and `scar/terrainlayout/test_maps/00_vivid_acropolis.lua`.

`Essence.Core.dll` `Archive.GetData()` throws `Key not set`. EssenceEditor
`CanDecrypt` only checks `Archive.Key` — **no key ships**. Documented by
[sga-archiver storage-type-18](https://github.com/BjornTheProgrammer/sga-archiver/blob/master/crates/sga/docs/storage-type-18.md).
Our reader skips them (`encryption` nibble). Do not pull the AES key from
live Relic for these 13 maps.

Art/Sound/rrtex SGAs: zlib packed, not crypt. Not extracted (size).

## Public unpackers (GitHub / UC)

| Tool | What it does | AoE4 RelicCardinal? |
|------|----------------|---------------------|
| **EssenceEditor.exe** (in the game folder) | Official SGA viewer | No exe crypt |
| [aoemods/AOEMods.Essence](https://github.com/aoemods/AOEMods.Essence) | SGA / rgd / rrtex / rrgeom CLI | No |
| [BjornTheProgrammer/sga-archiver](https://github.com/BjornTheProgrammer/sga-archiver) | SGA pack/unpack + type-18 writeup | No |
| [aoemods/zig-essence](https://github.com/aoemods/zig-essence) `sgatool` | SGA v10 | No |
| [Janne252/essence-archive-viewer](https://github.com/Janne252/essence-archive-viewer) | archived CoH viewer | No |
| [MAK-Relic-Tool/SGA-V10](https://github.com/MAK-Relic-Tool/SGA-V10) | Python SGA v10 plugin | No |
| [colaaaaaa123/arxan-static-patcher](https://github.com/colaaaaaa123/arxan-static-patcher) + dearxan | FromSoft GuardIT 12+ (ER / NR / AC6) | **No** — wrong Arxan shape |
| UC [AoE4 reversal](https://www.unknowncheats.me/forum/other-mmorpg-and-strategy/) | offsets / CE / kernel talk | **No unpacker.** Confirms newer Arxan; dump = live |

`C4SP3R.exe` is a SCAR-name dump, not an unpacker. User may authorize a run (`user-owned-tools.mdc`); it still does not decrypt on-disk `.text`.

User zip `Downloads\AoE4 Functions by C4SP3R_[unknowncheats.me]_(2).zip` (45 564): one PE `AoE4 Functions by C4SP3R.exe` (100 864). Strings only: `RelicCardinal.ex`, `scardocs\html\function_list.htm`, `OpenProcess` / `ReadProcessMemory` / `NtSuspendProcess`, PDB `...\AoE4 Functions by C4SP3R\x64\Release\`. Live name scrape of official SCAR docs + RPM. Does not decrypt on-disk `.text` or SGA AES-128. Same class as `ScarNativesDump`. Not executed.

Repo tools: `AOE4HOOK/tools/sga_mmap.py`, `extract_sga_v10.py`,
`unpack_game_data_sgas.py`, `rebuild_relic_analysis_pe.py`.
Relic `.text` no-game unpack (not in the table above):
`aoe4/gamesource/tools/unpacker` — [RELIC_UNPACK_ALGORITHM.md](../RELIC_UNPACK_ALGORITHM.md).

## Do not

- Overwrite Steam `RelicCardinal.exe`
- Run dearxan / UC kernel “AC bypass” on this title
- Treat Art.sga size as “still encrypted”

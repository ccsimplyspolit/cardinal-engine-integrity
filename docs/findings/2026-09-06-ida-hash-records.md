# 2026-09-06 — 45E8 HashRec map (`.data` expected hash)

IDB `runtime_exe.i64` session `a1220dbc`, imagebase **`0x7FF7A5500000`**.
**RVAs only.** Dump PID **60644** BSS holds live heap pointers; the
records themselves are **heap**, not in the IDB.

Do **not** plant Watcher / 7AB0. Lab command is **read-only**
`patchAT --hashwalk`.

## Why this path

42764 (ww) and 37836 (7AB0) died on IAT-kick, not JUMPOUT. 45E8 hashes
live `[obj+0x130]` with seed **r8=0**, then `cmp rax, [obj+0x10]`.
Mismatch decrements `g_RA_HashMismatchBudget` (`0x7542030`, dump **99**)
and only then `xor eax,eax` @ `0x3E55437`. Updating `[obj+0x10]` /
`[obj+0x18]` after a `.text` write is the remaining Relic lever.

## Map (MSVC `std::map`)

| IDB name | RVA | Dump 60644 heap ptr |
|----------|-----|---------------------|
| `g_RA_HashMapGate` | `0x7AF7AF0` | `0x22125F207D0` |
| `g_RA_HashMap` | `0x7AF7AF8` | `0x22125F20810` |
| `g_RA_HashKeyTree` | `0x7AF7B20` | `0x22125F20880` |

`RA_HashMap_FindOrInsert` `0x3E46BC0`: node `+0` Left `+8` Parent `+10`
Right `+19` Isnil `+20` key qword. **Return `node+0x28`**. New node
`memset(node+0x28, 0, 0x162)`. Do **not** call this live from patchAT
(it inserts).

Walk: `sentinel = *map`, inorder from `sentinel->_Left`.

## HashRec (`rdi` @ 45E8 `0x3E552A4`)

| Off | Field |
|-----|--------|
| `+0` | size (Hasher `a2` / memcpy Size) |
| `+0x10` | expected **source** hash |
| `+0x18` | expected **dest** hash |
| `+0x20` | dest addend (also compared to lookup key) |
| `+0xA0` | dest base; dest = base + addend |
| `+0x130` | source pointer (live `.text` or copy) |
| `+0x138` | refcount (`lock xadd`) |
| `+0x140` | lock-ish ptr |
| `+0x150` | copied-once flag |

Hasher @ `0x3E55314`: `xor r8d,r8d` then `Hasher(src, size, 0)`.
Memcpy @ `0x3E5547E`. Dest rolling-XOR: `size ^ g_RA_DestXorSeed`
(`0x7AF7688`, dump mutated) then `imul 0xDA942043DA942043` per qword.

Walker lists `0x7AFB910` / `918` / `920` look up by **`[obj+0x18]`**,
not the range table.

## F448 whitelist (not expected hashes)

Heap `g_RA_Whitelist` `0x7AF7B40`. Count qword then packed
`(start_rva << 32) \| end_rva`. Dump 60644: `0x22130C44A30` …
`0x22130C44AC0` (0x90 bytes). Binary search; only caller D02C.

## 45E8 Enqueue sites are **before** the hash

Calls @ `0x3E54D7F` / `4E0F` / `4EA6` sit on the early fail/init path
(map miss → `0x3E5583C`), not on the `cmp rax,[obj+0x10]` miss. First
~99 source mismatches do not JUMPOUT; KickCtor from a parallel IAT pack
can still kill first (36000 / 42764 / 37836).

## Lab

```
patchAT --hashwalk
```

RPM only. Dumps whitelist + HashMap + **SNAP** heap clones of Watcher
bytes. Do not `--apply --ww` until a live SNAP line exists and the clone
is patched in the same suspend window as the stub.

## Dump 60644 (offline `tools/hashwalk_dump.py`)

`RelicCardinal_full.dmp` (PID 60644, imagebase `0x7FF7A5500000`).

| Walk | Result |
|------|--------|
| F448 whitelist | **5** tiny ranges (`0x1ABE220`… / `0x696360` / `0xC00090`). **No** Watcher / sibling / 7AB0 |
| `g_RA_HashMap` | **368** records, `mysize=368`. Source is **heap** (`0x221…`), sizes `0x1222` / `0xCB8`. **hits=0** vs live Watcher VA |
| `g_RA_HashMapGate` | `mysize=172498` — **different** node type; do not parse as HashRec |
| `g_RA_HashKeyTree` | empty |
| Heap ptr to live Watcher VA | **none** in `0x221*` |
| Heap ptr to sibling / 7AB0 | 1 each (RA pointer tables, not HashRec) |
| Plaintext Watcher body | **1 copy**, 64-byte match at `0x22131026DB1` |

Watcher neighborhood snapshot: match **back `0x1530` + fwd `0x7140` = `0x8670`** bytes, window RVA **`0x3F092A0`**. Sibling / 7AB0 are **outside** this window. Header at snapshot start matches live `0x3F092A0` (`40 53 48 83 EC 20`…).

42764 class: 7AB0-family **memcmp live `.text` vs this heap clone** (not 45E8 `[obj+0x10]` of live Watcher). Updating HashMap expected hashes would **not** cover Watcher. Next write is the snapshot (offset `0x1530` into the `0x8670` window) **together with** a Watcher stub, under suspend — not another prologue-only plant.

`patchAT --hashwalk` now also `VirtualQueryEx` + 32-byte Watcher needle in private committed pages (`SNAP ww copy=…`).

## Live PID 42848 (2026-09-06 20:03, no overlay, no dbg)

Titled `Age of Empires IV -dev -nodbg -notrap`. base `0x7FF6F00D0000`.

`--hashwalk` matched the dump: HashMap **368 / hits=0**, whitelist **5 / hits=0**,
**one** SNAP `copy=0x1B4B450BDB1` `win_rva=0x3F092A0` `size=0x8670`.

`--snapww` (suspend + 6-byte pass on live Watcher **and** that clone; no sibling):

| t | probe |
|---|--------|
| 0–3 s | `slots=0` uninit, EP `48 83 EC 28` |
| ~4 s | **`slots=4 accum=0`** |
| ~6 s | RPM fail, Relic gone |

Same KickCtor class as 42764 / 37836. Matching the one Watcher clone is **not**
enough. Either a second clone / page-hash exists, or C8E4 IAT flush is not
tied to this snapshot. Do not `--snapww` again until that writer is found.

## Live PID 43676 (2026-09-06 20:06, relaunch, RPM only)

I launched Steam `-applaunch 1466860 -dev -nodbg -notrap`. Titled same.
`--hashwalk` now walks **ww / sib / 7AB0** prologues. **Three** disjoint
heap clones (one each). `--probe` after: `slots=0` uninit, Relic stayed up.

| tag | copy | back | fwd | win_rva | size | covers |
|-----|------|------|-----|---------|------|--------|
| ww | `0x201E25658D1` | `0x1530` | `0x7140` | `0x3F092A0` | `0x8670` | Watcher only (`sub` at window start) |
| sib | `0x201E257441C` | `0x33B0` | `0x5E40` | `0x3F2F528` | `0x91F0` | sibling; Watcher **outside** |
| 7ab0 | `0x201E249F3B6` | `0xA3D0` | `0x6C00` | `0x3DCD6E0` | `0x10FD0` | 7AB0 neighborhood; Watcher **outside** |

42848 `--snapww` left sib + 7AB0 clones untouched. Matching the Watcher
clone still IAT-kicked. Pointer scan (image + small heaps) for the three
copy/window-start qwords: **0 hits**. C8E4 is a **deadline flush** of
`g_RA_FlushTree` (4 armed nodes already present while `slots=0`) — see
[2026-09-06-ida-iat-scan.md](2026-09-06-ida-iat-scan.md). `--snapww`
refuses. `--hashwalk` / `--probe` only.

Script: `AOE4HOOK/tools/x64dbg-hidden/Run-HashWalk.ps1`.

## Live PID 40888 (20:28) + plants after 43676

`--hashwalk` SNAP-HASH (HashRec `src` ∩ clone `[copy-back, copy+fwd)`):
**overlap_hits=0** (368 records). The clones are not HashMap sources.
Updating `[obj+0x10]` would not fix Watcher `.text` writes.

`--enqsnap` / `--packs` on earlier PIDs: [2026-09-06-enqsnap-packs.md](2026-09-06-enqsnap-packs.md).
40888 left running, no plant.

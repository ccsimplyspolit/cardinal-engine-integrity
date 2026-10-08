# 2026-09-28 — what Aegis does to `RelicCardinal.exe` (mechanism map)

Extends [on-disk crypt](2026-09-06-relic-disk-crypt.md). Build **16.3.11308.0**.
The protector is **Aegis** (per its build log `Aegis_RelicCardinal.log`; a Relic-internal
fork filed under `engine/tools/Foreign/Aegis`, vendor not publicly named). This note
collects, in one place, **what each Aegis layer does** and **how far it is already
decrypted**. Read-only: assembled from the runtime image, the already-decoded overlay
`pack-decoded-static.bin`, the decompiled RA cluster, and the build log. No game process.

## TL;DR

Two time-phases. **Pack-time** (offline, at Relic's build): encrypt ~79% of `.text`,
virtualize a slice of functions, patch RTTI, append a ~10 MiB overlay carrying the
decrypt recipes + config. **Run-time** (in the live process): a pre-main stealth
bootstrap unseals `.text` before C++ inits, then a refcounted integrity layer keeps
individual regions cloaked and self-hashed for the rest of the session.

| Layer | What it does | Decrypted? |
|-------|--------------|-----------|
| `.text` selective cipher | 17 640 / 22 236 pages encrypted on disk | **Yes** — `unpack-disk` 99.285%; live image 100% plaintext |
| Overlay AEAD container | X25519 → HSalsa20 → XSalsa20/skip32 around the recipe table | **Yes** — key + catalog + all XOR recipes recovered |
| Virtualization (VM) | a threaded VM (`sub_3F910EC`, ~64.6 KiB) + ~10 MiB bytecode/metadata map | **No** — not devirtualized (VM ISA only sketched) |
| RTTI patching | 21 731 objects touched; sim-core type descriptors gone | Observation **confirmed**; Aegis as the cause is a **hypothesis** |
| Runtime integrity (45E8 / Hasher) | refcounted cloak/unlock of `.text` regions + wyhash self-check | Understood; session-only unlock **not** statically reproducible |
| Watch/permit config | block / report / notify / permit lists in the overlay | Small permit list **decoded**; big 386/41 lists stay hashed |

## 1. Pack/unpack mechanism (disk → plaintext `.text`)

Runs entirely inside `RA_Integrity_Dispatcher` `0x3E44034`, fired once from
`RA_Integrity_Dispatcher_Once` `0x3DDF150` as a **Pre-Main Stealth Startup** step
~110 ms after Resume — after `steam_api`, **before** the C++ `CRT$XCU` initializers.
So bulk `.text` is already plaintext before any C++ ctor runs (this is why TLS / EP /
`CRT$XCU` / IAT are all ruled out as the writer).

1. **Overlay** = raw bytes after the last section (`overlay_off = max(raw+rsz)` =
   `0x8076800`, 10 049 828 B, entropy ~8). Not in `SizeOfImage`, so the runtime image
   reads zero there. Reached at runtime via `sub_3E58220(base,size,footer,…)`.
2. **Footer** located by scanning the tail backward from `n-32`, step −1, bound `0x2000`.
   Four u64 at hit `p`: `A@p-8`, `B@p`, `C@p+8` (= tableSize `0x995884`), `D@p+16`.
   Valid when `D ^ ~(B*C) == A` (mod 2⁶⁴). `tableOff = (p-8)-C = 0`.
   `RA_PackFooter_Parse` `0x3F913AC`.
3. **AEAD** on `blob[0:0x995884]`. Header `hdr[0:32]=sk`, `hdr[32:64]=pk` (X25519).
   Body `blob[64:]`: `[0:16]` Poly1305 MAC, `[16:-8]` ciphertext, `[-8:]` extra8;
   `nonce24 = extra8 || 16×00`. Key order (reverse any step → wrong key):
   `shared = X25519(sk,pk)` → `k = HSalsa20(0¹⁶, shared)` → `XSalsa20-XOR(k, nonce, ct, skip32)`.
   `RA_PackIngest` `0x3F7D07C`, `crypto_box_beforenm` `0x3FB5050`,
   `crypto_core_hsalsa20` `0x3FC9210`, `crypto_secretbox_open` `0x3FB52E0`.
4. **Catalog** (`RA_PackSection_Get` `0x3F91340`): 24-byte slots, `ptr = table+776+off`,
   reject type ≥ `0x20`. type0 = 1.59 MiB HashMapGate blob, type1 = fat, type2 = seed(8),
   type3 = compact, type4 = wchar path. Seed → `g_RA_DestXorSeed` `0x7AF7688`
   (`0xFDFDFBCD1B3F5D7B`, live-only; disk differs).
5. **Apply** two record sets against `.text`:
   - **compact** (type3, 105 383 recs = 3175×`0x15` + 102 208×`0x16`): `+8` n, `+0x10` rva,
     `+0x38` type, `+0x39` payload. `0x16` = XOR in place; `0x15` = memcpy payload then XOR.
   - **fat** (type1, 174 recs = 40×1 + 133×7 + 1×6): ≥ `0x141` B; `0x15/0x16` → same XOR,
     other types → 16-slot HashRec registration into `g_RA_HashMap` (`RA_HashMap_FindOrInsert` `0x3E46BC0`).
   - **keystream**: `k = 0xDA942043DA942043 * (seed ^ n)`; per qword `dst ^= k; k *= r8`;
     tail `< 8` byte-wise with `k >>= 8`.
6. **Sentinel gate**: compact `rec+0x18 == ~rec+0x20` (fat `+0x120/+0x128`). TRUE → the
   deterministic disk keystream above (offline-reproducible → 99.285%). FALSE → a
   session cloak (`rdtsc` + `g_RA_UnlockPrng` `0x7AFD990`, rotates via `sub_3DE31A0`) that
   **cannot** be reproduced from disk — this is the "leftover" after static apply.
7. Regions made `PAGE_EXECUTE_READWRITE` (`sub_3F767F4` prot=64) around the apply, then
   restored and the whole image resealed (`sub_3F76778(-1, base, size)`); `byte_7AF7ABB = 1`.

## 2. Runtime protection

**Virtualization.** `sub_3F910EC` (`0x3F910EC`, ~64.6 KiB, Hex-Rays "No cfunc") is an
obfuscated stealth/VM shell. Qualitative markers (robust): `call next; ret; pop r10`
RIP-materialize idioms, `movabs rcx, imm64` rolling immediates, a **masked direct-syscall**
gate (`mov r10,rcx; not/xchg [rsp],r15; syscall`) that bypasses ntdll user hooks, heavy SIMD
(`paddq`/`pmuludq`/`pshufd`/`pxor`/`vpaddq`) as a wide integer mixer, and `int3` padding +
out-of-module `jmp` edges — i.e. it is built to **desync a linear disassembler**. Seed
`1187590981` (reused as the signing seed) drives the opcode encryption; bytecode/metadata =
the ~10 MiB "virtual map" at `0x8076800`. **Not devirtualized.**

⚠️ **Correction (verified 2026-09-28, do not trust linear disasm here).** An earlier reading
claimed the handlers all `call 0x397760C`, "the one shared decode/dispatch helper". That is a
**linear-sweep artifact**: `0x397760C` is not instruction-aligned (raw `88 d6 01 48 8b 4d f0
ff 15 07…`; a sane stream only begins at `+3`), and its aligned neighbours `sub_3977190` /
`sub_39776F0` are ordinary MSVC prologues, not a VM core. Because the shell overlaps
instructions on purpose, any exact call target, syscall count, or mnemonic histogram taken
from a single linear pass over `sub_3F910EC` is unreliable. Characterizing the VM (handler
dispatch, opcode/operand encoding, the `0x8076800` metadata layout) needs an **emulator or a
runtime trace**, not static disassembly — this is the real open item, and much larger than
everything else in this note.

**Integrity 45E8.** `RA_Integrity_45E8` `0x3E545E8` refcount-reveals/reconceals protected
`.text`, same `R8 = 0xDA942043DA942043`, two stores:
- **Cloak** (first refcount): `memcpy(dest,src)` then `*dest ^= k; k *= R8`,
  `k0 = R8*(g_RA_DestXorSeed ^ size)` — deterministic, XOR-reversible.
- **Unlock** (last refcount): `*dest = k; k *= R8` (**assign**), `k0 = R8*g_RA_UnlockPrng`
  (`0x7AFD990`, random per session) — **destroys** plaintext on drop; not statically recoverable.

**Hasher self-check.** `RA_Hasher` `0x3E57050` (wyhash: `0x9E3779B185EBCA87` … , 192-byte
secret table `0x56FB700`). Called twice in 45E8 — source before cloak, dest before unlock.
It raw-loads live `.text`, so a CRT-memcpy cloak does **not** hide it. On mismatch it stirs
the PRNG and decrements `g_RA_HashMismatchBudget` `0x7542030` (**99** on a clean menu);
budget ≤ 0 → bail. Tolerates ~99 mismatches before tripping. Do not stub 45E8/Hasher/Walker
or 14-byte-hook the hasher prologue (boot-kill).

## 3. Overlay config sections (decoded)

The overlay catalog's **small** sections (beyond the type0/1/2/3 decrypt recipes) carry
Aegis's watch/permit configuration. Decoded from `pack-decoded-static.bin`:

| type | size | content | maps to log line |
|------|------|---------|------------------|
| 10 | 130 | UTF-16, 3 DLLs: `TwitchNativeOverlay64.dll`, `graphics-hook64.dll`, `sl.interposer.dll` | **DirectX Permit list = 3** (Twitch / OBS graphics-hook / NVIDIA Streamline overlays explicitly allowed) |
| 5 | 128 | 32 × u32, all `.text` RVAs `0x2E8xxx–0x2EFxxx` | guarded/entry address list |
| 16 | 144 | u32 address pairs + small indices | address/index map |
| 7, 8 | 48 each | 12 × u32, opaque | hashes / keys |
| 6, 9, 11, 12, 14 | 200 … 3088 | opaque high-entropy blobs | encrypted / hashed config |

The big **block (386)** / **report (41)** / **notify (25)** lists are **not** plaintext
anywhere in the pack. Checked type0 (1.59 MiB): its head is `.text` RVAs in ascending order
(`0x00632190`, `0x00632195`, `0x0063219a`, …) interleaved with short hash fields — i.e. it is
the integrity **RVA → hash gate** (`g_RA_HashMapGate`), a self-check table, **not** a list of
module/window names. So the watch lists are stored **hashed** (opaque sections + the gate),
matching the long-standing observation that debugger/overlay needles in the image are
XOR/hashed, never literal. Only the 3-item DirectX permit list (§ type10) is in the clear.
Recovering the hashed lists' semantics would require dictionary hash-matching — out of scope
here (it is detection-list enumeration, not decryption of the protector).

## 4. RTTI patching — sim-core classes gone

Log line 19: `RTTI Patching 21731 objects`. `sdk/rtti/classes.tsv` (9 079 rows):
`.?AVEntity@@` / `.?AVSquad@@` / `.?AVPlayer@@` = **0** standalone records each (**confirmed**).
The substring hits (30 / 39 / 29) are all template args inside surviving
`std::function` / `_Ref_count_obj2` / `LuaBinding` records, owner ≠ the sim class. Every
sampled sim type (`ScarEntityPBG`, `EGroup`, `EntityManager`, `AIPlayer`, `Modifier`, …) has
0 own-records. What survives: STL (`std@@` owner 4 643), third-party SDK (Xbox GDK/Xal,
PlayFab, Havok, Alembic, websocketpp, libwebm, nlohmann), and Relic UI/net/glue
(`WPFGUI` 821, `RLink` 252, `LuaBinding` 220, `StateTree`, `Plat`). **The simulation core is
the hole.**

**Confirmed:** sim-core polymorphic classes have no resolvable MSVC RTTI record while
everything else does. **Hypothesis (not proven here):** that Aegis's RTTI-patching pass is
what stripped them. The static picture fits "sim-core RTTI removed", and 21 731 patched
> 9 079 resolvable is directionally consistent with mass removal — but the log names no
objects, and this TSV cannot distinguish protector-stripping from (a) the sim TUs built
`/GR-` or using Relic's own reflected-object identity (see memory `relic-reflected-object-header`),
(b) recovery-tool coverage gaps, or (c) relocated/renamed descriptors. Needs a
pre/post-protect RTTI diff or a live COL/TypeDescriptor scan to confirm.

## 5. Decrypted vs open

**Decrypted / understood:** the entire `.text` cipher (live image + `unpack-disk`), the
overlay AEAD container and all XOR recipes, the startup unseal path, the integrity
cloak/unlock math, the DirectX permit list.

**Open:**
- **VM devirtualization** — the only genuinely unopened crypto surface. The `sub_3F910EC`
  shell defeats linear disasm (see §2 correction), so handler dispatch, inline
  bytecode/operand encoding, and the `0x8076800` metadata layout need an emulator/trace, not
  static reading. Order of magnitude more work than everything above.
- Big block/report/notify lists — stored **hashed**, not as strings (§3); semantic recovery
  would be dictionary hash-matching (detection-list enumeration), deliberately not pursued.
- RTTI causal attribution (§4).
- 13 AES-128 map `.lua` in `Data.sga` — a **game** resource layer, not Aegis; no key ships.
- Session unlock branch is random by design; those dest bytes are never statically recoverable.

Method note: assembled by a 3-reader workflow over `pack-decoded-static.bin`, the decompiled
RA cluster (`reversed/03E00000`, `03F00000`), `meta/ra-map.json`, and the build log. RVAs are
IDB `0x7FF7A5500000`-based; do not mix session VAs.

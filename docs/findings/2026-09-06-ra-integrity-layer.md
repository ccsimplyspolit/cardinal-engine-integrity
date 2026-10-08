# 2026-09-06 — post-unpack RA integrity layer (45E8 dest)

User: after `.text` decrypt, another layer guards the image — dig that,
not WindowWatcher stubs.

Build **16.3.11308.0**. IDB `runtime_exe.i64` imagebase `0x7FF7A5500000`.
Live PID **52920** base `0x7FF7E64B0000` (started 23:20:12, `-dev -nodbg
-notrap`). **RVAs only.** No Relic `.text` plant. No MiniDump.

This is **not** the Watcher window pack (`tag=0x20220002` → slots). It
runs with **slots=0**.

## Two dest transforms in `RA_Integrity_45E8` (`0x3E545E8`)

Same `R8 = 0xDA942043DA942043`. Different store.

| Phase | When | Op | Key |
|---|---|---|---|
| **Cloak** | first refcount, after source Hasher + memcpy `0x3E5547E` | `*dest ^= k; k *= R8` | `k0 = (g_RA_DestXorSeed ^ n) * R8` at `0x3E55493` |
| **Unlock** | last refcount drop | `*dest = k; k *= R8` (assign) | `k0 = R8 * g_RA_UnlockPrng` (`xmm` `0x7AFD990`) |

Hasher `0x3E57050` raw-loads the **source** before memcpy (`0x3E55314`).
Dest hash is a second call (`0x3E555F3`). Mismatch decrements
`g_RA_HashMismatchBudget` (`0x7542030`). Budget **99** on this live
menu — no hash fails. `g_RA_JUMPOUT_Gate` (`0x7AFB0A0`) = **0**.

Do **not** stub 45E8 / hasher / Walker / kick ctor. Cloak CRT memcpy
does not hide the hasher (0x10E).

## Named RVAs (60644 IDB)

| Name | RVA | Live 52920 |
|---|---|---|
| `g_RA_DestXorSeed` | `0x7AF7688` | `0xFDFDFBCD1B3F5D7B` (same as 60644) |
| `g_RA_UnlockPrng` | `0x7AFD990` | `0xAE541D1F8E4CBB01` / `+8=0x91B9F0B18E4D718D` |
| `g_RA_HasherTable` | `0x56FB700` | 192-byte wyhash secrets; Large/Mid seed |
| `g_RA_HashMap` / gate / key tree | `0x7AF7AF8` / `0x7AF7AF0` / `0x7AF7B20` | heap, armed |
| `g_RA_ImageBase` / size | `0x7AF7B28` / `0x7AF7B30` | **equals** live base / `0x8C3D000` |
| `RA_Integrity_Walker` / B / C | `0x3E47000` / `0x3E48680` / `0x3E49CF0` | hasher callers (plus 45E8 ×2) |

`g_RA_UnlockPrng` is a **shared** session `xmm`, not RA-only (xrefs from
`0x3A25AC` / `0x3A26A4` as well as 45E8).

Hasher xrefs: Walker, Walker_B, Walker_C, 45E8 (`0x3E55314`,
`0x3E555F3`). Do not 14-byte hook the hasher prologue.

## Live dest0 vs `unpacked_static` (RPM, elevated)

Tool: `AOE4HOOK/tools/probe_ra_integrity.py` →
`aoe4/gamesource/meta/live-ra-integrity.json`. Dest slot 0 only
(`destRva = rva + [rec+0x90]`, 174 fat recs, 784 408 B).

| | 52920 menu ~T+8m | gold 52968 T+20s | 60644 |
|---|---|---|---|
| leftover | **621 219** | 612 209 | 651 472 |
| leftover in RA `0x3DD0000–0x3F90000` | 604 006 | 604 240 | 604 159 |
| leftover outside RA | 17 213 | 7 969 | 47 313 |
| dest0 **unlock** (`k*=R8` store) | **118**/174 | 117 | 127 |
| dest0 still **static** | 52 | — | — |
| dest0 still **cloak** | 3 | 3 | — |
| dest0 other | 1 (`n=12` @ `0x3F56B48`, too short for 2-qword detector) | — | — |
| RA window slots | **0** (begin=end=0) | 3 (Watcher) | — |
| hasher / 45E8 prolog | intact | — | — |

First leftover run is still dest `0x679533` (unlock, n=4642). Same
island as every prior leftover head.

**Observation:** leftover exists with **slots=0**. Integrity self-mod
does not need a debugger window. Watcher pack and dest0 unlock are
different layers.

**Observation:** 52 dests still match static (mostly 4642-byte clones
outside the RA band, same `live0`). 45E8 has not taken those dests.
Leftover is the 118 unlock + 3 cloak + 12-byte RA island, not “missing
XOR”.

**Observation:** menu T+8m unlock count (118) already matches T+20s
gold (117). Waiting longer does not unpack the 52 static dests.

## What this layer does *not* allow

- Patching live Relic `.text` and expecting the hasher to miss it.
- Scoring cloak against a late live PE (wrong oracle; use
  `leftover-gap` / dest0 classify).
- Treating leftover growth as a failed disk unpack.
- Neutralizing Watcher `.text` to “freeze” dest0 — Watcher is the
  other layer.

Next (no plant): HW-BP/VEH on hasher `0x3E57050` only if the hide-first
attach ritual is already up; restore `saved[]` around the raw-load.
Do not 14-byte hook that prologue.

WindowWatch PID **54060** was visible after the probe. Slots were still
0 at 23:28:07. Do not open x64dbg / C4SP3R on this PID if slots must
stay 0.

# 2026-09-06 — IAT pack writer (36000 / 42764)

IDB `runtime_exe.i64` session `a1220dbc`, imagebase `0x7FF7A5500000`.
**RVAs only.** Overlay `+8` / `+10` from `DumpRaSlot` (`mp_bypass.cpp`).

Watcher `.text` (any encoding) is **not** the 2 s packer. It is the
**target**. A separate data-only callback copies/compares a buffer and
then Enqueues `0x20DE00AD`.

## Why overlay showed `08050001` / `0x56FD380`

`08050001` / `08060001` immediates exist **only inside `RA_Enqueue`**
(`0x3DD26A4` / `0x3DD2694` and the twin at `28EC` / `28DC`). They are
stack members of `RA_TagInList`, not caller tags.

Live slot `+8=08050001` is Enqueue rewriting/selecting from that list.
Callers pass **`0x20DE00AD`**. `mp_bypass.h` already names that IAT pack
(`a2=0` kinds `6/3/1/5`). Overlay `kind 5` = IAT extra.

Slot `+10=0x56FD380` is **not** GetWindowTextW IAT (`0x56DF2C0`) and has
**0 code xrefs**. `RA_IatPack_77E8` decrypts `unk_7FF7AABF9AC8`
(RVA `0x56F9AC8`, xor key `57`) into the Enqueue object; `+10` is a field
of that blob. Same object in `RA_IatPack_C8E4`.

## Call chain (Watcher stub → kick, no JUMPOUT)

```
RA_WindowWatcher / sibling prologue write
  → RA_IatScan_7AB0   RVA 0x3DD7AB0   size 0x1055
       data xrefs only (ptr at 0x56FA4D0 = 7AB0)
       memcpy scanner (arg Size / Destination)
       calls RA_IatPack_77E8 ×4
  → RA_IatPack_77E8   RVA 0x3DD77E8   size 0x232
       RA_Enqueue(obj, 0, 0x20DE00AD, 12,
                  6,1,0,  3,1,0,  1,2,0,  5,10,20)
  → slots=4 kinds 6/3/1/5  KickCtor ~2–4 s
```

`RA_IatPack_C8E4` (`0x3DDC8E4`, size `0x47F`) is a **second** `20DE00AD`
writer (kind `6`, `a2=0`) + `RA_EventSchedule`. Callers: 77E8-family
(`AAA8` / `ADAC` / `AEC8` / `BE20`) and `0x3E1BE8` / `1C88` / `1D54`.

`RA_Scan_E300` (`0x3E1E300`) is also data-only and lists `RA_Enqueue` as a
callee, but has **no** `20DE00ADh` immediate. Not the 42764 writer.

`RA_Integrity_Dispatcher` still Enqueues `20DE00AD` (hashed / JUMPOUT
path). 36000 died on KickCtor **without** JUMPOUT → Dispatcher is not
the 2 s path.

## Prologues (IDB)

| RVA | Name | Bytes |
|-----|------|-------|
| `0x3DD7AB0` | `RA_IatScan_7AB0` | `48 89 5C 24 20 55 56 57` |
| `0x3DD77E8` | `RA_IatPack_77E8` | `48 8B C4 48 89 58 08` |
| `0x3DDC8E4` | `RA_IatPack_C8E4` | `48 8B C4 48 89 58 08` |

## Lab (`patchAT`)

**Closed.** PID **37836** (19:34, no overlay, no dbg): `--apply --iat`
7AB0 `B8 01 00 00 00 C3` only.

| t | probe |
|---|--------|
| 0–3 s | `slots=0` uninit, stub `already` |
| ~4 s | **`slots=4 accum=0`** EP still `48 83 EC 28` |
| ~6 s | RPM fail, Relic gone |

Same KickCtor class as Watcher 42764. 7AB0 is vtable `0x56FA4C0+0x10`
(`RA_IatObj_Ctor` `0x3DF510` also calls `Dispatcher_Once`). Prolog stub
skips tail `0x3E80060`. Another scanner (or Dispatcher) still packs
`20DE00AD`. `C8E4` is also flushed from `RA_FlushHook_CreateFileA` `0x3DE1BE8` /
`CreateFileW` `0x3DE1C88` / `Sleep` `0x3DE1D54` (FNV-cracked; not
`0x3E1BE8`). Those wrappers call C8E4 **then** the original API.

## C8E4 is a deadline flush, not a SNAP memcmp (PID 43676)

`g_RA_FlushTree` `0x7AFB6D8` → heap map. Node `+0x20` key, `+0x30`
deadline. `packEnable` `0x7542010` == 1. Clock = KUSER InterruptTime
mix at `0x3E765F0`.

Live titled 43676, no plant, `slots=0`:

| key | deadline |
|-----|----------|
| `0x4` | `0xD2CF87` |
| `0x8` | `0xD25A57` |
| `0x2710` | `0xD2CDF1` |
| `0x2711` | `0xD2CF87` |

`mysize=4 armed=4`. CreateFile/Sleep orig slots `0x7AFB3B10/18/20` are
**0** (hooks not installed or orig not stored). SNAP pointer scan of
image + small heaps: **0** hits on copy/window-start.

Plant → 7AB0 → C8E4 walks this tree → if `now > deadline` Enqueue
`20DE00AD` ×4. That is the ~4s `slots=4` class. Matching Watcher SNAP
does not clear these nodes.

## Heartbeats — finite keys, infinite refresh (not new checks)

Re-hashwalk ~7 min later: still **mysize=4**, same keys. Deadlines
**moved forward** (`0xD2CF87` → `0xD48FB5` on key `4`). No new nodes.

`RA_FlushArm` `0x3E8B3A0` (`B3A0(int key)`). Callers:

| Caller | ecx / key | Role |
|--------|-----------|------|
| Watcher +0x81 | `4` when `g_RA_WatcherBeat` `0x7542080` ≤ 0, then reset **100** | keepalive |
| Watcher +0x271F | `4` | same key |
| Watcher +0x851 | `rsi-0xC` (likely `8`) | key 8 |
| Sibling +0x17E | `4` | same key 4 |
| 10× ~0x225D clones (`0x3F59650` family) | `4` | compile-time copies, not runtime-generated |
| `0x3E152DC` | `4` | string/`:` scanner |

Ctor `RA_FlushTree_Ensure` `0x3E8B264` allocates the map + 2000/1000
timer. Erase is `RA_FlushTree_EraseKey` `0x3E8CF80`.

**Do not stub Watcher / sibling / 7AB0 / FlushArm.** They **refresh**
these 4 deadlines. Stub stops the beat → C8E4 sees expire → IAT pack.
That is why `--snapww` / `--ww` / `--iat` die at ~4 s. The remaining
SNAP clones are the same class, not “missed patches.”

Checks are **not** infinitely generated. Four keys, refreshed forever.

Do not stub C8E4 / CreateFile / Sleep (same .text class). `--hashwalk`
now dumps hooks + tree. IDB names saved.

`--iat` / `--iatpack` / `--ww` / `--snapww` refused. HashRec map
`g_RA_HashMap` `0x7AF7AF8`. See
[2026-09-06-ida-hash-records.md](2026-09-06-ida-hash-records.md).

`--nuclear` / `--enqueue` stay banned (40280). Overlay neutralize stays 0.

IDA names: `RA_FlushArm`, `RA_FlushTree_Ensure`, `RA_FlushTree_EraseKey`,
`g_RA_WatcherBeat`, `RA_IatScan_7AB0`, `RA_IatPack_77E8`, `RA_IatPack_C8E4`,
`RA_FlushHook_CreateFileA` / `_CreateFileW` / `_Sleep`,
`RA_InstallFlushHooks`, `RA_Scan_E300`. IDB saved.

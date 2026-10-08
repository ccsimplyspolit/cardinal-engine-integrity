# 2026-09-06 — 7AB0 decrypt / re-find (10+ passes)

Steam `RelicCardinal.exe` is **ciphertext** on most RA `.text`. One IDB
snapshot is not enough: some 4 KiB pages self-mod after unpack, and ASLR
moves every VA. This pass checks the IatObj / 7AB0 sites **11 ways**
and writes a restart ritual that does not trust a previous VA.

Tool: `K:\aoe4_dlc\aoe4\gamesource\tools\Verify-RaDecrypt.py`  
Report: `K:\aoe4_dlc\aoe4\gamesource\meta\ra-decrypt-verify.json`  
IDB: session `a1220dbc`, imagebase `0x7FF7A5500000`. **RVAs only.**  
Live RPM: PID **40888**, base `0x7FF6E6700000` (do not reuse this VA).

No plant. No `--ww` / `--iat` / FlushArm.

## Verdict

Decrypt of the **named prologues** is correct. After a game restart the
same sites are findable as `B + RVA` plus a **unique-length AOB**
(not the 16-byte MSVC prologue). We still do **not** have a safe patch
([7ab0-enqueue](2026-09-06-7ab0-enqueue.md)).

All 11 scripted passes `ok=true` on this run.

## What “encrypted” means here

| Layer | What it does to these RVAs |
|---|---|
| Steam disk `.text` | 7AB0 / Enqueue / Fwd / Ctor / FlushArm / Sibling / PathList / CbRegister are **garbage**. EP / Watcher / CrtInit / `ctor_tail_D4D8` are plaintext islands |
| In-place unpack | Live image = decrypt. Analysis PE `.text` == 60644 `memory.bin` |
| Runtime self-mod | 214 pages differ 60644 vs 26392; Ctor `0x3DDF000`, CbRegister `0x3F45000`, FlushArm `0x3E8B000` are in that set. **16-byte prologues still matched** every live image |
| ASLR | VAs change. `vtbl+10` and `g_RA_IatObj+0` are `B + RVA` |

Do not RE Steam `RelicCardinal.exe` as code. Unpacked BSS / vtbl stay
file-unrelocated (`0x140000000 + 7AB0`); only `.text` was spliced.

## 11 passes

| # | Check | Result |
|---|---|---|
| 1 | Disk ≠ live on encrypted RA spots | **pass** (CrtInit / D4D8 are islands, excluded) |
| 2 | Disk == live on EP / Watcher / CrtInit / D4D8 | **pass** (control: we did not swap files) |
| 3 | 60644 mem == 60644 PE == unpacked **code** | **pass** (BSS ignored) |
| 4 | IDA `get_bytes` == 60644 mem (16 B) | **pass** |
| 5 | Same 16 B on 7 live images (60644 ×2, unpacked, 26392 ×3, 13568) | **pass** |
| 6 | 26392 `011146` == `011254` at 7AB0 | **pass** |
| 7 | Other PIDs 13568 + 26392 sdkpack match 7AB0 / Fwd / EP | **pass** |
| 8 | Flag self-mod pages; still re-read Ctor / CbRegister | **flagged**, prologues still equal |
| 9 | Unique AOB in 60644 `.text` (`hits==1`) | **pass** (see lengths) |
| 10 | `QWORD[B+0x56FA4D0] == B+0x3DD7AB0` on every live image + disk preferred base | **pass** |
| 11 | Live RPM PID 40888 vs 60644 mem | **pass** (all code 16 B; unique 28 B 7AB0/Fwd also match) |

PID 40888 `g_RA_IatObj`: `[+0]=B+0x56FA4C0`, **`[+8]=0`**, `[+16]=0`.
Fwd is still a no-op on this process.

## Unique AOB (16-byte prologue is not enough)

MSVC `48 89 5C 24 20 55 56 57 41 54…` hits **334** times in `.text`.
Fwd’s 16-byte prologue hits **8685**. After a restart, **do not** AOB
16 bytes and pick a hit.

| Site | RVA | Unique `n` | `hits` in 60644 `.text` |
|---|---|---|---|
| `RA_IatScan_7AB0` | `0x3DD7AB0` | **28** | 1 |
| `RA_IatObj_Fwd` | `0x3E1E2A4` | **28** | 1 |
| `RA_Enqueue` | `0x3DD2550` | 16 | 1 |
| `RA_IatObj_Ctor` | `0x3DDF510` | 20 | 1 |
| `RA_SiblingPathScan` | `0x3E652DC` | 24 | 1 |
| `RA_IatObj_PathList` | `0x3E57EF4` | 24 | 1 |
| `RA_FlushArm` | `0x3E8B3A0` | 40 | 1 |
| `RA_IatObj_CrtInit` | `0x3A8F0C` | 16 | 1 (plaintext island) |
| `RA_IatObj_CbRegister` | `0x3F45064` | 16 | 1 |
| EP | `0x4FB0884` | 16 | 1 |

7AB0 28-byte needle (also IDA `a1220dbc` + PID 40888 RPM):

`48 89 5C 24 20 55 56 57 41 54 41 55 41 56 41 57 48 8D 6C 24 E9 48 81 EC 90 00 00 00`

Fwd 28-byte:

`48 89 5C 24 08 48 89 6C 24 10 48 89 74 24 18 57 48 83 EC 30 48 83 79 08 00 49 8B F9`

## Restart ritual

1. Do not open Steam `RelicCardinal.exe` as code.
2. `EnumProcessModules` / `patchAT --hashwalk` / pe-sieve → module base **B**.
3. `VA = B + RVA`. Never reuse `0x7FF7A5500000+…` or `0x7FF6E6700000+…`.
4. RPM the unique needle at `B+RVA`. If miss: AOB that needle in the live
   image; expect **one** hit, at that RVA.
5. Confirm `QWORD[B+0x56FA4D0] == B+0x3DD7AB0`.
6. Re-read Ctor / CbRegister; their **pages** self-mod even when the
   prologue is stable.
7. `g_RA_IatObj+8` is a snapshot (0 on 60644 / 26392 / 13568 / 40888),
   not a decrypt check.
8. Re-run `Verify-RaDecrypt.py` (it RPMs if Relic is up).
9. No plant.

## Do not

- Treat a 16-byte `48 89 5C 24…` hit as 7AB0
- Mix VAs across 60644 / 26392 / 13568 / 40888
- Trust unpacked PE for BSS / vtbl
- Stub Fwd / 7AB0 / FlushArm / Sibling because the bytes verified

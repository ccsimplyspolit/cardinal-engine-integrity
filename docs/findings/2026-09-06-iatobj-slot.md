# 2026-09-06 — `g_RA_IatObj+8` writer / `call [vtbl+10h]`

IDB `runtime_exe.i64` session `a1220dbc`, imagebase `0x7FF7A5500000`.
**RVAs only.** RPM-only. No plant. FlushArm / `--ww` / `--iat` stay off.

Canon object table: [7ab0-enqueue](2026-09-06-7ab0-enqueue.md).
Probe: `K:\aoe4_dlc\aoe4\gamesource\tools\Probe-IatObjSlot.py`
→ `aoe4/gamesource/meta/iatobj-slot.json`.

## Verdict

Nobody named writes `g_RA_IatObj+8`. There is no RA-cluster
`call [vtbl+10h]` that feeds 7AB0 `a4`. Live and dump `[+8]` stay **0**
even when slots already filled (52968 T+20s). Planting 7AB0 / Fwd is
still an IAT-kick.

## Static

| Check | Result |
|---|---|
| IDA xref `0x7AF3BC8` / `+16` / `0x56FA4D0` | **0** |
| Ctor stores to `+8` | **no** — `2344` ignores rcx |
| Fwd | **read** `[+8]`; 0 → return 0 |
| lea `g_RA_IatObj` | CrtInit, PathList×2, Sibling×2, CbRegister×4, atexit dtor |
| RA `0x3DD0000–0x3F90000` `call [r*+10h]` | **0** |
| RA `48 8B 0x FF 50 10` | **0** |
| `.text` rip-rel store to `+8` (`48 89 05`) | **0** |
| 7AB0 code xrefs | **0** (data: vtbl+10 + RVA table `0x89442EC`) |

Ctor tail `E8` at `0x3DDF554` → `0x3E1D4D8` (`1F 59 3E 48 89 58 10…`).
Neighbor `0x3E1D4A0` calls `[rbx+10h]` = object `+16`, thunk only
`0x3E42A30`. Not vtbl+10. Not a +8 writer.

## Live / dumps (`[+0]` = vtbl unless noted)

| Image | PID / base | `[+8]` | `[+16]` | vtbl+10 == 7AB0 |
|---|---|---|---|---|
| RPM watch 23:42 | **26976** `0x7FF7E64B0000` | **0** (90 s, no change) | 0 | yes; slots=3 accum=600 |
| RPM watch 23:46 | **41064** `0x7FF618680000` | **0** through `slots=0→3` | 0 | yes; died ~9 s after pack |
| probe 23:47 | **51652** `0x7FF618680000` | **0** | 0 | yes; window 3×`0x198` (Probe `slotCount` //8 = 153 — ignore) |
| live 23:26 | **52920** `0x7FF7E64B0000` | **0** | 0 | yes; slots begin/end 0 |
| 60644 mem | 60644 `0x7FF7A5500000` | 0 | 0 | yes |
| 52968 T+20s | 52968 `0x7FF7AD880000` | **0** | 0 | yes (process later slots=3) |
| 37560 menu | 37560 `0x7FF6196D0000` | 0 | 0 | yes |
| 37560 online PE | same | 0 | 0 | PE BSS zeroed — ignore |
| unpacked analysis | file-layout | garbage | garbage | preferred-base qword only |

Prior RPM 40888 / 26392 / 13568: `[+8]=0` ([decrypt-verify](2026-09-06-7ab0-decrypt-verify.md)).

## Do not

- Treat file-layout unpacked `.bss` as live IatObj
- Plant Fwd because “lock pair is the 7AB0 gate” — `[+8]` never arms
- Plant 7AB0 because vtbl+10 points at it — 37836
- MiniDump live Relic; File→Attach
- Mix VAs (52920 `0x7FF7E64B0000` ≠ 60644 `0x7FF7A5500000`)

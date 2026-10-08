# 2026-09-06 — RA kick emulator (data-only)

User: emulate the four failed plants (enqsnap / Watcher `ret 1` /
`--snapww` / WindowClear). Then **«а остальное?»** — 7AB0 IAT gate +
all SNAP clones, not another Relic `.text` plant.

Build **16.3.11308.0**. Tool: `AOE4HOOK/tools/ra_kick_emu.py`.
**RVAs only.** No Relic `.text`. Writes were **not** run on the hold
PIDs (52920, then 26976).

## What each plant actually missed

| Plant | Death | Emulator |
|---|---|---|
| Enqueue `31 C0 C3` + SNAP (`--enqsnap`) | slots=0, ~8s. C8E4 `now > node+0x30` → EventSchedule | `--keep-expire` WPM those four deadlines + beat=100 |
| Watcher / sibling `ret 1` | IAT `slots=4` 7AB0→77E8 | `--iat-skip` + `--hold` forces v8 in-range (`C50`/`C58`). **Racy / unproven** vs a stub |
| `--snapww` live+one clone | slots=4, death | SNAP scan + `--sync-snap` mirrors the **whole** live window onto ww/sib/7ab0/enq clones. **Does not** fix 7AB0 compare |
| `WindowClear` | `.data` only | `--drain-timerq` unlinks **only** C8E4 delays `526336` / `2097160` |

7AB0 is a dispatcher (`RA_IatScan_7AB0` `0x3DD7AB0`), not a memcmp.
`if (v8) { memset(a5,0,Size); goto tail; }` skips the opcode switch
(including 77E8). Tail always `0x3E80060`. 7AB0 **rewrites** C50/C58
every call — a one-shot `--iat-skip` lasts until the next 7AB0.
`--hold` is a rewrite loop, not a plant. Stubbing 7AB0 prologue still
IAT-kicked **37836**. Gate skip ≠ proven Watcher-stub survival.

Encode (`shift=0`): `stored = ~((shift<<56) | ((val<<shift)&0xFFFFFFFFFFFFFF))`.
Always-in-range: C50=`encode(0)`=`0xFFFFFFFFFFFFFFFF`,
C58=`encode(0xFFFFFFFF)`=`0xFFFFFFFF00000000`.
`decode(s) = (~s & 0xFFFFFFFFFFFFFF) >> (~s >> 56)`.
`v8 = (uint32)decode(C48^C40) ∈ [decode(C50), decode(C58))`.

Globals (RVA): SRW `0x7AF3C38`, C40–C58 `0x7AF3C40`…`C58`,
`g_RA_IatObj` `0x7AF3BC0` (live `[+8]=0`, `[+10]=0`).

## Live probes (RPM only, no write)

### PID 52920 (~23:36–23:39)

| | |
|---|---|
| RA window | begin=end=0, **slots=0** |
| packEnable `0x7542010` | **1** |
| Watcher beat `0x7542080` | moving (91→4) |
| FlushTree keys | `4` `8` `0x2710` `0x2711` armed |
| TimerQ `0x7AF6D88` | **286–288** nodes, **0** C8E4 kick delays |
| ww / sib / 7AB0 / Enqueue / EventSchedule / KickCtor | all **live** |
| iatGate | `skipSwitch=false` (v7 outside `[lo,hi)`) |
| iatObj+8 | **0** |

First SNAP pass (32-byte needle only) found one private copy each.
PID gone before the window-expand pass.

### PID 26976 (23:40:45 start, probe 23:40:55)

Same ASLR base **`0x7FF7E64B0000`**. Cmdline CIM empty this query.
**slots=0**. TimerQ **60** / kick delays **0**. Gate still
`skipSwitch=false`. IatObj vtbl `base+0x56FA4C0`, `+8=0`. Prologs live.

SNAP windows match 43676 / [ida-hash-records](2026-09-06-ida-hash-records.md):

| tag | copy | back | fwd | win_rva | size |
|-----|------|------|-----|---------|------|
| ww | `0x2A77F3D6DB1` | `0x1530` | `0x7140` | `0x3F092A0` | `0x8670` |
| sib | `0x2A77F3E58FC` | `0x33B0` | `0x5E40` | `0x3F2F528` | `0x91F0` |
| 7ab0 | `0x2A77F30EF46` | `0xA3D0` | `0x6C00` | `0x3DCD6E0` | `0x10FD0` |
| enq | `0x2A77F3099E6` | `0x4E70` | `0xC160` | `0x3DCD6E0` | `0x10FD0` |

Enqueue sits **inside** the 7AB0 SNAP (`0x3DD2550` ∈ `[0x3DCD6E0, +0x10FD0)`).
Same heap clone, different offset. Three disjoint windows, not four.

TimerQ is full on a healthy menu. Blind `list=0` would drop normal
EventSchedule. Drain refuses unless delay is `526336` (C8E4 packEnable=1)
or `2097160` (else branch). Do not auto-drain from overlay WindowClear.

## CLI

```
python AOE4HOOK/tools/ra_kick_emu.py                 # RPM probe (gate + SNAP)
python AOE4HOOK/tools/ra_kick_emu.py --keep-expire
python AOE4HOOK/tools/ra_kick_emu.py --drain-timerq
python AOE4HOOK/tools/ra_kick_emu.py --iat-skip --hold 8
python AOE4HOOK/tools/ra_kick_emu.py --sync-snap
python AOE4HOOK/tools/ra_kick_emu.py --plant          # refuse
```

JSON: `aoe4/gamesource/meta/ra-kick-emu.json`. Elevate OpenProcess.

## Honest gaps

- `--iat-skip` is racy. 7AB0 rewrites the gate. Tail `0x3E80060` still
  runs. Not tested against a Watcher / 7AB0 stub (those plants stay
  refused).
- `--sync-snap` without a plant is a no-op (live == clone). Sync + plant
  still lost to 7AB0’s own compare (42848, 6224).
- `--keep-expire` while Watcher is live fights a refresh that already
  works. Do not pair it with a stub on a slots=0 hold.
- Do not plant Enqueue / Watcher / 7AB0 to “test” the emu.

[heartbeat-emu](2026-09-06-heartbeat-emu.md) ·
[7AB0 dispatch](2026-09-06-7ab0-dispatch.md) ·
[enqsnap-packs](2026-09-06-enqsnap-packs.md)

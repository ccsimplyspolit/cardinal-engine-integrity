# 2026-09-06 — “full patch” is not more unpacker

User: so what do we actually do to get a full patch.

Build **16.3.11308.0**. **RVAs only.** No Relic `.text` plant this turn.

## Decision

There is **no** next unpacker step that yields a Steam-launchable
patched `RelicCardinal.exe`. Disk XOR is done. Leftover after compact
is session dest0 (cloak / unlock PRNG), already classified
([ra-integrity-layer](2026-09-06-ra-integrity-layer.md)).
`splice-gold` is 100% vs **one** live snapshot and stale a second later.

| If “full patch” means | Status | Do this |
|---|---|---|
| Readable image for IDA | **Done** | oracle PE + gold splice. Do not RE Steam exe |
| Overlay plays (SCAR / DualFlag / HUD) | **Done** | APC DLL + DXGI + `.data`. Relic `.text` banned |
| Static leftover = 0 forever | **Impossible** | unlock `*dest = k; k*=R8` is per-session (`0x7AFD990`) |
| Survive a write **inside** RA / Watcher / 7AB0 | **Failed** tonight | HashRec update does not cover SNAP clones; `--snapww` IAT-kicked |
| Survive a write **outside** HashRec ∪ SNAP windows | **Untested** | name the RVA first; refuse if it intersects the map |

## Why leftover ≠ “can’t patch”

`.text` ≈ 86.8 MiB. dest0 leftover on live 52920 is **621 KiB**, almost
all in `0x3DD0000–0x3F90000`. The rest already matches
`unpacked_static`. DualFlag / ScarDoString / overlay AOBs were never
waiting on those 621 KiB.

## Independent checkers (do not collapse)

1. **45E8 HashRec** — Hasher vs `[obj+0x10]` / `[+0x18]`. Fat 174 dest0.
   Live map **368** heap recs. Lever named, not live-proven: write
   `.text` then recompute both hashes
   ([ida-hash-records](2026-09-06-ida-hash-records.md)).
2. **SNAP heap clones** — ww / sib / 7AB0 memcmp vs live. HashRec
   `overlap_hits=0`. Matching one clone + live stub still died
   (`--snapww` PID 42848).
3. **7AB0 / C8E4 FlushArm** — IAT-kick if those bodies expire.
4. **WindowWatcher** — window title → slots. Hide, never stub.

Updating HashRec expected hashes is **only** lever (1). It does not
unlock Watcher or 7AB0.

## What to do next (pick one)

- **Product:** keep Relic `.text` banned. Nothing to plant.
- **One specific RVA** outside the map: check dest0 ∪ SNAP windows, then
  one live byte on a slots=0 PID.
- **HashRec-covered RVA:** HashRec `+0x10/+0x18` update in the same
  suspend as the write. Do not also stub Watcher.
- **Do not:** more leftover XOR, 45E8/`ret 1`, hasher 14-byte hook,
  `--snapww`, MiniDump live Relic.

## Slots stay empty (2026-09-06 23:33)

User: can we write a full patch so slots stay empty.

**No Relic `.text` patch does that and keeps Relic alive.** Already
tried:

| Plant | Result |
|---|---|
| Enqueue `31 C0 C3` + 7AB0 SNAP clone (`--enqsnap` 43676) | slots=0, dead ~8s. C8E4/77E8 `EventSchedule` still arms timers |
| Watcher / sibling `ret 1` | IAT-kick slots=4 (36000 / 42764) |
| `--snapww` live+one clone | slots=4 then death |
| `MpBypassWindowClear` | zeros `.data` only; heap timers stay |

Enqueue `0x3DD2550` sits inside the 7AB0 SNAP window. A 14-byte hook
there is the same class as `--enqsnap`.

What **does** keep slots empty (live 52920, begin=end=0): overlay hide
+ Relic `.text` banned + no leftover `x64dbg.exe`. Live step-debug:
[RELIC_DEBUG_ATTACH.md](../RELIC_DEBUG_ATTACH.md) (`rbhost` /
`Start-X64dbgHidden.ps1`). That is the slots patch. Do not write another
Relic `.text` stub.

## Hook / patch everything at once (2026-09-06 23:33)

User: patch or hook the whole cluster in one shot.

**Already did. Relic died faster, not slower.**

| Plant | PID | Result |
|---|---|---|
| `--nuclear` 7 sites | 40280 | Present ~3s, gone |
| `--packs` nop Enqueue×6 + ww/sib SNAP | 6224 | slots=4 at 3s, dead at 5s |
| `--enqsnap` Enqueue+7AB0 clone | 43676 | slots=0, dead ~8s |
| ww+sib `ret 1` | 36000 | IAT slots=4, kick ~4s |
| 7AB0 only | 37836 | slots=4 ~4s |

More writes = more SNAP / 7AB0 / FlushArm expire surfaces. HashRec does
not cover the three heap clones. 7AB0 has its **own** compare. Overlay
14-byte hooks on the same RVAs are the same class (hasher + SNAP).
Do not `--nuclear` again.

Data-only emu (no Relic `.text`):
`AOE4HOOK/tools/ra_kick_emu.py`. `--keep-expire` = C8E4 deadlines
(enqsnap expire). `--drain-timerq` = only delays `526336`/`2097160`.
`--iat-skip --hold` = 7AB0 v8 gate (racy; tail still runs).
`--sync-snap` = full SNAP windows onto heap clones (not 7AB0 compare).
Watcher stub / `--snapww` still **unproven**. Do not plant to test.
[ra-kick-emu](2026-09-06-ra-kick-emu.md).

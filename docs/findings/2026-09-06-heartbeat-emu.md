# 2026-09-06 — Watcher heartbeat emulator?

Question: stub Watcher `.text` (stop packs) and run our own heartbeat so
C8E4 does not expire.

## Two kicks, not one

| Mechanism | What | Live |
|-----------|------|------|
| Expire | Watcher/sibling/7AB0 stop calling `RA_FlushArm` → C8E4 `now > node+0x30` → EventSchedule then Enqueue `20DE00AD` | 43676 class (`slots=0` then dead) |
| `.text` mismatch | Any RA-cluster / SNAP-window write → 7AB0 → 77E8 IAT `slots=4` ~4 s | 36000, 42764, 37836, 6224 |

An emulator that only **refreshes** keys `4` / `8` / `0x2710` / `0x2711`
(or calls `RA_FlushArm` from the overlay) covers expire. It does **not**
cover 7AB0. Stub + fake beat still IAT-kicks. SNAP update does not save it
(6224, 42848). HashMap ∩ SNAP = 0.

Watcher already **is** the heartbeat: beat `0x7542080` → `FlushArm(4)` every
100 hits, plus sibling + 11 clones. Leave those bodies alone.

## What would not work

- Overlay thread `call RA_FlushArm` + Watcher `ret 1` — still a `.text` plant
- Writing `node+0x30` from `patchAT` + stub — same 7AB0
- Reimplementing Watcher’s title scan outside Relic — Watcher still runs
  unless stubbed; if stubbed, 7AB0

## What would

A data-only gate both EventSchedule and Enqueue read (not found), or the
7AB0 compare field (Hex-Rays still open). Hide cycles 5–8 already failed
for visible dbg titles.

`--hbkeep` is now data-only `ra_kick_emu.py --keep-expire` (FlushTree
`+0x30` + beat=100). It covers the **expire** half of `--enqsnap`.
`--iat-skip --hold` is the data-only 7AB0 **v8 gate** (C50/C58), not a
compare patch. 7AB0 rewrites those qwords every call; tail `0x3E80060`
still runs. Not proven against a Watcher stub. `--sync-snap` updates
heap SNAP windows only. Do not pair any of this with a Watcher /
Enqueue `.text` stub on a session that must stay slots=0.
[ra-kick-emu](2026-09-06-ra-kick-emu.md).

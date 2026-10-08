# 2026-09-06 — RPM write-watch `g_RA_IatObj+8` / runtime 7AB0 ptr

User: no plant. Watch `B+0x7AF3BC8` RPM-only (no Relic `.text` INT3), or find a
runtime fn-ptr into 7AB0 that IDA has no code xref for (EventSchedule / WorkQ),
with live opcode `a4`. Not FlushArm. Not `--ww` / `--iat`. Re-read `+8` after
match if 52920 still alive.

**52920 was already gone.** Hide-dbg cycle left **26976**, then **41064**, then
**51652**. Same build `16.3.11308.0`. RVAs only; do not mix VAs.

IDB `runtime_exe.i64` session `a1220dbc`, imagebase `0x7FF7A5500000`.

Tools (RPM, elevate):

- `aoe4/gamesource/tools/Watch-IatObjSlot.py` → `meta/iatobj-writewatch.jsonl`
- `aoe4/gamesource/tools/Scan-7ab0-fnptr.py` → `meta/7ab0-fnptr-scan.json`

## Verdict

PID **51652** (same ASLR `0x7FF618680000` as 41064, 23:47): `+8=0`, window
3×`0x198`. Probe prints `slotCount=153` because it divides by 8 — real count is 3.

`[+8]` does **not** arm when the RA window fills. 40–80 Hz RPM across
`slots=0 → 3` (41064) and a 90 s hold at `slots=3` (26976): `+8` stayed **0**.
EventSchedule does **not** queue 7AB0 (`a4` there is a **delay**, e.g. `532480`
/ special `526336`). WorkQ `qword_…D950[4]` was **0**. The only extra live
QWORD `== B+0x3DD7AB0` is a **PRIVATE clone of `.rdata` vtbl+10** (SNAP /
rdata mirror), not a call site. Live `a4` was **not** observed (queue empty;
no INT3).

## PID 26976 — 80 Hz × 90 s (already packed)

| | |
|--|--|
| B | `0x7FF7E64B0000` |
| watch | `B+0x7AF3BC8` = `0x7FF7EDFA3BC8` |
| t0 23:42:48 | `+8=0` `+16=0` vtbl+10=`B+0x3DD7AB0` slots=**3** accum=600 |
| next jsonl line | **none** — no qword change for the whole 90 s |
| 7AB0 prologue | `48 89 5C 24 20 55 56 57…` (live, not stub) |

Process gone before a match re-read. Not 52920.

## PID 41064 — 40 Hz across window fill

| t | slots | accum | `+8` | note |
|--|--|--|--|--|
| 23:46:19 | 0 | 0 | **0** | fresh ASLR `B=0x7FF618680000` |
| 23:46:33 | **3** | 600 | **0** | first change = window only; `+8` frozen |
| 23:46:42 | RPM fail | — | — | process died ~9 s after pack (IAT-kick class). We did not plant |

`+8` did not transition on the only moment it could have (Watcher pack).

## Runtime 7AB0 QWORD scan (41064, IMAGE+PRIVATE, 1.4 GB)

Needle `B+0x3DD7AB0` = `0x7FF61C457AB0`. **2 hits:**

| VA | What |
|--|--|
| `B+0x56FA4D0` | static vtbl+10 (IDA data xref; already known) |
| heap `0x24D8364BF60` | bytes == Relic `.rdata` at `0x56FA4B0…` (`_purecall`, `sub_…42BBC`, `RA_IatObj_Dtor`, `RA_IatObj_Slot8`, 7AB0, then `%zu` / `0x%lx`) |

Heap hit is a **rdata window copy**, not EventSchedule / WorkQ. `RA_IatObj_Slot8`
(`vtbl[1]`, RVA `0x3E21B38`) **rewrites vtbl** to `off_…A4C8`. It does **not**
write field `+8`.

## EventSchedule / WorkQ / opcode `a4`

`RA_EventSchedule` `0x3DD15E4`: `v114[0]=a4`; `if (a4==526336) call qword_…16398`;
node `+360 = a4`. 7AB0-family `sub_…B29C` calls
`EventSchedule(…, 532480, 0)` then `Enqueue(tag=0x40230001)`. **Delay**, not a
fn-ptr to 7AB0.

`g_RA_TimerQList` `0x7AF6D88`: 16 nodes walked; **none** `+360 == 7AB0`
(heap / `0` / `1`).

`RA_WorkQ_PeekSlot` `0x3F815F4` → `qword_…D950` RVA **`0x7AFD950`**. Live all
four slots **0**. No blob, so no `+24` tag / live `a4`.

7AB0 switch (Hex-Rays, still no caller): `a4` in `1…43`. `a4==25` / `14` / `35`
and the 26–43 chain (B7B8 / BED8 / B60C / B424 / ADAC+77E8 / AEC8+77E8 / …).
Without a populated WorkQ or an indirect call we **cannot** sample live `a4`
under the “no Relic INT3” rule.

Static still: 7AB0 **2 data xrefs** (vtbl+10 + leftover RVA triplet table
`0x89442EC` = `(0x3DD7AB0, 0x3DD8B05, …)` = **n=`0x1055` span**, not a call
table). Code xrefs **0**. `+8` xrefs **0**.

## Do not

- Treat the heap 7AB0 QWORD as “who calls 7AB0”
- Treat EventSchedule `a4` as 7AB0 opcode
- Plant Fwd / 7AB0 because `+8` “must arm in a match” — menu T+20s already
  packs slots with `+8=0` (52968, 26976, 41064)
- File→Attach / `--ww` / `--iat` / FlushArm
- MiniDump live Relic

## Next (still no plant)

Match re-read of `+8` needs a **held** PID (user thought 52920). Hardware DR0
on `B+0x7AF3BC8` still needs a debugger that WW will not pack, or CE DBVM
without Relic `.text` INT3. Live `a4` only if WorkQ `D950[i] != 0` — RPM the
blob `+24`.

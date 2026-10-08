# 2026-09-06 — Enqueue+SNAP died; next is call-site nop

IDB `runtime_exe.i64` `a1220dbc`, imagebase `0x7FF7A5500000`. Live PID **43676**
base `0x7FF6E6700000`. Overlay off. No dbg. **RVAs only.**

## Goal (unchanged)

Slots stay `0` forever, Relic stays up, any debugger can attach.

## PID 43676 `--enqsnap` (20:21)

Theory: `RA_Enqueue` `0x3DD2550` sits **inside** the 7AB0 SNAP window
(`win_rva=0x3DCD6E0` `size=0x10FD0`). HashMap **368 / hits=0** vs Enqueue VA
(sources are heap). One physical clone:

| tag | copy | Enqueue clone |
|-----|------|----------------|
| 7ab0 | `0x201E249F3B6` | `copy-0x5560` = `0x201E2499E56` |
| enq | `0x201E2499E56` | same bytes |

Suspend + `31 C0 C3` on live Enqueue **and** that clone. Watcher / FlushArm
left alone. EP stayed `48 83 EC 28`.

| t | probe |
|---|--------|
| 0–7 s | `slots=0` uninit |
| 8 s | RPM fail |
| after | Relic gone (`--probe`: not running) |

No IAT slot write (Enqueue body never ran). Kick is **not** only KickCtor
inside Enqueue.

## Why slots=0 still dies

`RA_IatPack_77E8` and `RA_IatPack_C8E4` both **`RA_EventSchedule` first**,
then `RA_Enqueue(20DE00AD)`. C8E4 expire (`now > node+0x30`, `packEnable==1`)
and 77E8 mismatch both arm a timer even if Enqueue is a no-op.

`RA_FlushArm` callees include `RA_EventSchedule` and one Enqueue
`tag=0x021C0001` (fail path — live 43676 had `slots=0` for 7+ min, so this
is not the heartbeat). Enqueue itself does **not** refresh flush deadlines;
it writes the slot window and may `RA_KickCtor`.

`--enqsnap` **refused**. Do not stub Enqueue / EventSchedule / 7AB0 / C8E4 /
77E8 prologues.

## PID 6224 `--packs` (20:26) — closed

Titled `Age of Empires IV -dev -nodbg -notrap`, same base `0x7FF6E6700000`.
Nop `call RA_Enqueue` ×6 + ww/sib SNAP (7ab0 window not written). Watcher
prologues stayed `48 89 5C 24 18`.

| t | probe |
|---|--------|
| 1–2 s | `slots=0` |
| 3–4 s | **`slots=4 accum=0`** (IAT / 77E8 class) |
| 5 s | RPM fail, Relic gone |

`--packs` **refused**. Mid-function Watcher write + SNAP update is the same
IAT-kick as prologue `--snapww`. SNAP memcmp is **not** the only check (or
the SNAP is hashed: HashMap `src` is heap). Next was `--hashwalk` SNAP-HASH. **PID 40888:** `SNAP-HASH walked=368
overlap_hits=0`. HashRec does **not** cover the three clones. Updating
`[obj+0x10]` would not have saved 6224. 7AB0 has its own compare
(not HashMap). PID **40888** left running, `slots=0`, no plant.

## Next lab: SNAP ∩ HashRec (not another prologue)

Nop only `call RA_Enqueue` (`E8` → `0F 1F 44 00 00`) at Watcher ×4 and
sibling ×2. Mirror into **ww / sib** SNAPs. Do **not** write the 7ab0
window. Heartbeat (`FlushArm(4)` / beat `0x7542080`) stays.

| name | RVA |
|------|-----|
| ww_enq0..3 | `0x3F0C142` `0x3F0C835` `0x3F0DA8B` `0x3F0E07B` |
| sib_enq0..1 | `0x3F337FF` `0x3F33E94` |

`--packsint3` adds CAF8/1FDC calls (outside all three SNAPs, HashMap miss):
`0x3E1CCE8` `0x3E421E2` `0x3E426F5` `0x3E429F8`.

Clone-family `0x3F5A9CF`… (11 ×2) not in `--packs` yet. Hide cycles packed
`20220002` from Watcher at dbg start; add clones only if slots rise.

## Do not

- `--enqsnap` / `--snapww` / `--apply --enqueue` / Watcher prologue
- File→Attach before `--packsint3` lives 30s
- OS-export jmp / ScyllaHide Inject into Relic

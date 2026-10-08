# ADR-004: RA emulator is data-only layers, not a Relic `.text` plant

## Status

Accepted

## Date

2026-09-06

## Context

The user wants to put their own hooks in Relic `.text` without IAT-kick /
expire-kick. Every plant of Watcher, 7AB0, Enqueue, FlushArm, EventSchedule
died (36000 / 37836 / 43676 / 42764). Overlay neutralize is compile-off.
CRT memcpy cloak BugCheck `0x10E`. PAGE_GUARD IntegrityCloak is Relic-UD2
risk. `g_RA_IatObj+8` never arms. 7AB0 has 0 code xrefs.

`ra_kick_emu.py` already covers four *failed plants* as `.data`/heap writes.
That is not yet a hook product.

## Options considered

### A. Stub RA bodies and “emu the heartbeat”
- Already **false**: stub + FlushArm refresh still 7AB0 IAT-kicks
  ([heartbeat-emu](../findings/2026-09-06-heartbeat-emu.md))

### B. Overlay PAGE_GUARD / CRT cloak as the emulator
- PAGE_GUARD: Relic uses the same slot for UD2; hits=0 then crash class
- CRT cloak: `0x10E`. Default OFF. Do not revive

### C. Hypervisor split-view (execute hooked, RA reads original)
- Would cover Hasher raw-load. Not this lab (no kernel/EPT in this repo)

### D. Data-only layered emulator + hook planner (chosen)
- L1 expire, L2 TimerQ kick-drain, L3 7AB0 v8-gate hold, L4 SNAP sync,
  L5 HashRec dest report, L6 **plan/apply only outside**
  RA ∪ SNAP ∪ dest0 ∪ named ban list
- First milestone that is still **untested**: a write *outside* those sets
  ([full-patch](../findings/2026-09-06-full-patch-is-not-leftover.md))
- RA-cluster hooks stay refused. `--plant` stays refused

## Decision

Canon: [RELIC_RA_EMU.md](../RELIC_RA_EMU.md). Lab CLI:
`AOE4HOOK/tools/ra_emu.py`. Kick-layer implementation stays in
`ra_kick_emu.py` (imported). Overlay does **not** grow neutralize /
memcpy cloak. patchAT `--ww` / `--iat` / `--enqsnap` stay refused.

## Consequences

- “Эмулятор” ≠ подмена 7AB0. 7AB0 switch and Hasher source-load are
  still live. L3 is racy. L4 does not fix 7AB0 compare
- Injector gateway: `ra_emu.py heartbeat` / `write`. FlushArm success is
  `deadline = KUSER_now + period` on four keys — not a Relic `.text` plant
- User hooks: `ra_emu.py plan --rva --len` first. `write`/`apply` refuse
  intersection with the ban map unless `--force` (7AB0 still sees bytes)
- In-process C++ trampolines wait until an *outside* write survives
  a live hold. Do not port this into `InternalInjector` this turn

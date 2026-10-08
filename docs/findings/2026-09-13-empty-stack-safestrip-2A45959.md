# 2026-09-13 — empty-stack SafeStrip relock `rva=0x2A45959` sid=50120

hold5+wfAfterDf session, pid 27332, Zhu Xi ~06:19, army AI on. Match
start DualFlag **23:28:19** `slots=0`. Process died **23:34:34**. Real
`0xC0000005`, Relic `warnings.log` `Application crashed.` WindowWatch
stayed `slots=0 flag=0` until RPM 299 (process gone). `op20` leftover
was not this death.

Same think leaf as
[Zhu Xi 6:44 SafeStrip relock](2026-09-13-zhuxi-relock-2A45959.md).
Live-stack `WasStrip` was not enough.

## Observation

```text
[23:25:28.442] OverlayBoot: ... luaGate2500+hold5+wasStrip+wfAfterDf
[23:28:19.244] [RA] match-start gate why=dualflag-after ok=1 slots=0
[23:34:32.650] [STK] army relock lock sid=50120
[23:34:32.650] [SCAR] cmd#532 label=ai_lock_army_relock ... ok
[23:34:34.492] [CRASH] VEH code=0xC0000005 rva=0x2A45959 av_addr=0x58
               rax=0 tid=18384 (not SCAR window 21056) in_call=0
               last_native=idle
[23:34:34.703] [STK] army native map ... combat=7 locked=2
               would4A70-live=26 safeStrip=7
```

`HelperRun` success wipes `last_native` to `idle`. No `was-strip` decline
for 50120. Named think: `sub_2A45930` RVA `0x2A45930`. Getter `0x2924350`
returned 0; next use is `[rax+0x58]`.

## Finding

`TacticStackLive` treated an empty tactic vec (`begin==end`) as idle, so
unlocked tracking became `L.safe` / `SafeStrip`. `NoteWasStrip` only ran
on a **live** stack. 50120 never showed live in RPM this session, so
`PickRelockSid` / `__ArmyLock_LockOneSid` still called **4A70**. Lua
`__LockWasStrip` was never filled from C++ (only tests planted the table).

Cmd_Stop after Enable is off (`rva=0x1ED5529`). An empty per-tracking
stack is not a drained think plan.

## Change

- Unlocked tracking is `WouldStrip` only. `StkAiTrackCollect` never fills
  `L.safe`. `TacticStackLive` fail-closed (`tracking != 0`).
- `FormatLockLua` writes `__LockWasStrip[sid]=true` for every strip id.
- Overlay stamp `...+wfAfterDf+no4A70`. `kScarLuaAfterLoadMs` stays 2500.
  No `Cmd_Stop`. No Watcher / sibling / 7AB0 / FlushArm / Enqueue.

After Enable, Relic-tasked combat stays with Relic. `locked` may stay low
versus `would4A70-live`. That is the crash tradeoff, not a longer Lua hold.

Regression: `test_unlocked_tracking_never_safestrip`.

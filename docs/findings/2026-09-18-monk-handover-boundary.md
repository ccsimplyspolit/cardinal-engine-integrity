# 2026-09-18 — monk handover stops at was-strip, by decision

Live match 01:11–01:13, Zhu Xi, relics collected mid-game.

## What the handover does and does not do

The latch fires and reaches Lua:

```text
[01:11:39.069] [STK] monk handover latched: ground_relics=0 (all monks -> player)
[01:11:39.073] [SCAR] cmd#857 label=ai_lock_relic_count ok      <- __ArmyLock_MonkHandover=true
```

After it: the skip-map regenerated four times, the relock ran with
`monk_handover=1`, no `relock decline`, no `[CRASH]`, no SEH.

What still does not happen is the two claimed runners changing hands, and the
reason is upstream of the monk logic. `PickRelockSid` refuses on the first
condition:

```cpp
if (sid == 0 || sid >= 100000000u || g_relockPoisonSids.count(sid)
    || StkAiTrackWasStrip(sid)
    || (extraSkip && extraSkip->count(sid)))
    continue;
```

`g_wasStrip` takes every row seen with a live tactic (`NoteWasStrip` in
`StkAiTrackCollect`) and is cleared only per match, so any squad Relic has ever
driven is permanently out of the relock's pick list. A monk that ran a relic is
exactly that. The relock is also always `scan-only (no LockOneSid)` in the log,
and the only path that locks is the Lua `GE_EntitySpawn` handler, which sees
new spawns.

So the real boundary is:

| monk | after the latch |
|---|---|
| spawned after the latch | locked to the player by the spawn event |
| the two claimed runners, and any monk Relic has driven | stays with the AI for the rest of the match |

That is why a match can show four monks with the AI rather than two: the claim
cap governs new claims only, and anything the AI has already driven is
unreachable.

## The commit that came before this

`4b6008f2a3` removed a genuine inconsistency: the relock's accept predicate
tested `__ArmyLock_MonkAi[sid]` without testing `__ArmyLock_MonkHandover`,
while `monkGoesToAi`, `__ArmyLock_StopOneSid` and the skip-map emitter all pair
the two. That fix is necessary and correct, and it is not sufficient — the
was-strip guard above refuses the same squads one layer earlier.

## Decision: leave it

Lifting the was-strip guard for monks after the latch would mean locking a
squad Relic has tasked. That is the `rva=0x1ED5529` class (lock a live relic
runner, 11:40 in_call=1) and the `rva=0x2A45959` class (unlocked tracking is
still 4A70 with an empty stack — 15:12:44 attempt=50087, 23:34:34 sid=50120).
Asked, and the answer was to keep it: **no crashes.**

So this is not an open defect. Two monks with the AI for the rest of a match
where relics were collected early is the intended cost of the crash rule. Do
not "fix" it by widening the relock pick list.

If it is ever revisited, the narrow version is: monks only, after the latch
only, only when `StkAiTrackClassify(sid) == Safe4CE0` and the
`kRelockSafe4CE0AgeMs` age has passed, and expect to verify it in a live
battle rather than a lobby.

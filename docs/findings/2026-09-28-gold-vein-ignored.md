# 2026-09-28 — "the bot ignores the gold vein" (Macedonian, 2v2)

Report 2026-09-27 23:56, screenshot at game 0:42: our mining camp stands
(finished, smoking) beside an 8000 gold vein, villagers F7 W0 G0 S0, pop 9.
Diagnosed from `aoe4_internal.log`, `warnings.log`, the match journal
`aoe4_match_20068_20260927_231121.ndjson` (segment from 2634.3 s: our capital
`(180,0)`, local player 1006) and the 16.3.11308 pseudocode.

## What happened (journal, 5 s per character)

```
            G on the vein  c at the camp  s on a sheep  T standing at the TC  . moving
1000007635  ..ccc..ssssssssssssss...GG..sssssss   builder: camp 0:06-0:25, then sheep
1000007636  ..cccc.ssssssssssssss...GG..sssssss   builder: same
1000007665          .TTT.TT.TTTTT...ww..wwww      trained 0:41.9, idle at the TC ~1 min
```

- Relic placed `building_econ_mining_camp_control_byz_ha_mac` at `(148,0)` at
  0:06.5, 12 m from vein `1000005005` `(136,0)`; it finished at 0:25.6 (the
  Macedonian `silver_deposit_byz_ha_mac` record appears at the camp then).
- Both builders walked back to the sheep at 0:30-0:35. The contest's
  30 s opening window (`kEcoOpenMs`, food first, quota free) was still open.
- The next villager stood idle at the TC from 0:45 to 1:45.
- Nobody touched the vein until the player right-clicked miners at 1:45.
  Those went back to the sheep after the selection hold ran out (2:10); the
  player turned the AI off at 2:28.
- Second Macedonian match of the same process (00:06): the camp finished at
  1:19, after the opening window, and its builders mined from 1:20 to 3:30.

## Causes

1. **Opening window.** The camp finished inside the 30 s food-first pass;
   its builders were idle and got sheep jobs.
2. **Quota spent on busy villagers.** After the opening the contest gave the
   gold/wood quota in C++ to every *standing* worker (`speed < 0.22`), which
   includes every sheep eater. Lua refused those jobs (`Squad_IsIdle` false),
   but C++ had already counted them, so the truly idle villager behind them
   got food or nothing useful. Chunk lengths at 0:37 / 0:45 decode to exactly
   that job set.
3. **Own sheep marked "teammate".** Any food node within 72 m (120 m in the
   opening) of an ally drop-off counted as the ally's, without an ownership
   check. Our starting sheep were 69 m from the ally TC, so the sheep pass
   skipped them and the eaters fell into the quota loop (cause 2).
4. **Nothing moves a busy villager.** The contest orders only idle squads;
   Relic's gathering manager re-labels only new villagers and surplus ones
   under its urgent rule, and it cannot see LocalCommands. The all-food start
   was frozen. (A wood-before-gold tie-break also sent a lone villager at the
   camp to a tree.)
5. **Blind gather labels.** `AssignWorkerGather` labelled a villager by the
   nearest node within 4.8 m of its centre. Miners stand on a vein's rim,
   6.7-11.3 m from the centre of the 8000 vein (median 8.2 m on a regular vein
   over five journals), so none were counted, while the Macedonian silver
   record at the camp centre labelled villagers at the camp as gold.
6. **Selection hold without a clock.** `__SelLock_Tick` is an
   `AOE4HOOK_Local` 0.5 s interval, but `L.Now()` without an argument returns
   the cached time and no pump in the DLL passes one. The release ran only on
   the next click: a villager clicked last stays held (out of the AI's reach)
   until the player clicks again.

Ruled out: the silver mechanic as a target (the record is a drop-off book for
the Varangian Arsenal, never gathered), a missing gold weight (the plan asked
for G1 at 0:42), Relic rounding, override cadence (`AIPlayer_UpdateGathering`
is an empty native), contest failures, and an enemy at the vein.

## Changes

- `ai_contest_plan.h` (new, host-tested): the normal and opening passes.
  - Quota in Lua: `Q = want - labelled have`, spent only on a squad Lua
    confirms idle; an idle squad's own label is credited back first. One `T()`
    line per standing worker with ordered alternatives and a fallback, so an
    idle villager always gets work. `T()` re-ranks the owed alternatives by
    the remaining relative debt at call time; food below the
    villager-production floor (`AiEcoVillagerFoodFloor`) comes first. It
    claims one-gatherer nodes (sheep, deer, trees) for the first squad it
    sends there; a later squad takes a free one of the same resource, then
    shares a claimed one of the most-owed resource rather than drop to a
    less-owed one. Nothing is reserved in C++ for workers Lua may refuse.
  - Stay-local: a worker within 16 m of a gold/stone node that has our mining
    drop-off within 16 m is offered that node first, in the opening too. A
    worker already labelled with that resource (a rim miner, or an idle
    builder on the rim inside the 10.5 m reach) keeps the offer but is not
    planned first.
  - Own food is never "teammate"; unowned food is the ally's only if an ally
    villager works it or the ally's drop-off is nearer than ours.
  - Deficit ties go to the nearer resource.
  - One bounded busy move per pass (`RB()`): from a resource over its quota,
    counted from what the workers stand at right now, onto a vein beside our
    mining drop-off whose resource is owed. Lua runs it only if the debt is
    still there after every idle villager was served and more than the want
    of the source resource are really gathering it (busy, not building,
    counted live, walking ones neither moved nor counted), so the
    villager-production floor holds and a builder on its way to a
    foundation is left alone. 45 s per worker; a revert watch turns it off
    for the match after two moves Relic took back, whether after arriving
    (arrival needs the target label) or on the way (seen walking 6 m closer,
    then standing on its old resource).
  - The labelled standing workers rotate through a 16-per-pass budget.
- `ai_session.cpp`: the food-first opening (and the `kEcoOpen` kick) only on
  the first enable of a match and within 60 s of its start; the kick skips
  the player's held villagers; enemy villagers, scouts and buildings without
  a weapon no longer blank our vein for 40 m, but a vein beside an enemy
  mining camp or TC (within 20 m, nearer than ours) is left alone; sticky
  labels for moving workers.
- `ai_shared_mine.h`: every miner counts toward the shared vein's 8-miner
  cap, including earlier pulls still walking there; only walking miners
  not already sent are pulled.
- `radar.cpp`: mineral reach 10.5 / 8 / 6.5 m (regular / small / tiny),
  nearest past its rim wins; `silver_deposit_byz` is not a node; minerals
  only on Resource entities.
- `stk_lua_lock.cpp`: the selection release tick is posted to the window
  thread at 1 Hz for 120 s after the last click, then every 5 s.

Two adversarial review rounds (five and four lenses, three skeptics per
finding) found the cursor that never rotated, capacity reserved by busy
workers, a false rebalance surplus, false reverts and reverts that never
counted, the shared-vein cap (twice), enemy-held veins, the rim builder
losing its vein offer, food below the floor losing the ranking, and a
rebalance that could take a builder walking to a foundation; all fixed
above. (Part of round two's verifier votes did not run: session limit.)

## Logs that prove it live

```
[AI] eco contest open=0 want F5/W2/G1/S0 have F6/W0/G0/S0 tries=8 (vein=1 free=1 labelled=6) rebalance=...
[AOE4HOOK_ECO CONTEST] iss=F0/W1/G1/S0 held=0 busy=6 ... q=...          (warnings.log)
[AI] eco rebalance held: worker=N stays on deposit D
[AI] eco rebalance reverted: worker=N left deposit D ... (1/2)
[AI] session on ... opening=0                                            (re-enable)
```

## Verification

Host: `test_ai_contest_plan` (live 0:42 and 0:25.6 geometry, teammate rule,
tie-break, stay-local, miners at their vein, rebalance, revert watch, batch
rotation), `test_eco_idle.py` (`T` / `RB` / `Flush` on Lua 5.3: busy squads
spend no quota, the idle one gets the vein, claims, re-ranking, live surplus,
fallback, held squads untouched), `test_ai_shared_mine` (cap with stationary
miners), full `run_host.ps1`.
MSBuild Release|x64 builds. Not yet seen in a match: whether Relic takes a
moved busy villager back (the revert watch reports it).

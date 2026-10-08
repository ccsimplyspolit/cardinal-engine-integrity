# 2026-09-27 — cloud plan: embedded canon, engine age, build orders, late game, stone

Follow-up to [anti-pick, lock modes, threat](2026-09-27-antipick-lockmodes-threat.md).
Done in a Linux cloud session: no MSBuild, no game, no IDA, no
`Documents\AOE4HSettings`. What needs them is marked **LOCAL-ONLY** below.
Host tests ran with g++ (`-std=c++17`, an MSVC CRT shim) and lupa; the DLL
sources that changed were syntax-checked with MinGW (not MSVC).

## Commits (main)

| Item | Commit | What |
|---|---|---|
| 1 | `972b27ddf1` | `MoveLockedTargetAside` before Link: a DLL locked by the game becomes `InternalInjector.dll.old_<stamp>`, no LNK1104 |
| 2 | `359e0a88bd` | canon AOE4HSettings files as RCDATA (`canon_embed.rc`, `tools/gen_canon_embed.py`); Documents sync without an sdk; `unit_profile` reads `sdk\NativeEspData` first |
| 3 | `fa53af07d9` | engine age fed back from the actuator (`ai_engine_age.h`); `ag=` / `atk=` / `aq={}` in the spec; build order keeps the player's age; Professional Scouts read `Player_GetCurrentAge` |
| 4 | `87ad095b5b` | build order only when the user picked it; `finished` after the last step |
| 5 | `d91c6bb3bf` | Templar commanderie (`kt`: 400f/200g, 60 s, `researchAgeUp`) |
| 6 | `490a88b91d`, `cb28f52ee3` | selection hold ≥ 7 s from the pick, then recheck; garrison ≤ 40 s per stay |
| 7 | `b7319190e1` | Full AI mid-match handover behind `kAiFullAiMidMatchHandover` (off) with a tracking census |
| 8 | `95af51bf36` | mode table (AI_BOT.md 9.1); toggles restored after Full AI |
| 9 | `83e1d124fe` | late game: 15 of each military building at Age IV + 5 min, productivity at + 15 min |
| 10 | `b6abac791b` | stone only for a bill |
| 12 | `d4ab5c52b4` | Enable hint names the army owner in Full AI |
| 13 | `d01c1af1e3`, `3817312c09` | review fixes: 31-bit age token, played-out guide on the HUD |

## 3. Age sources and their base

| Source | Base | Note |
|---|---|---|
| `Player_GetCurrentAge` | 1..4 | `AGE_DARK = 1` (`sdk/constants/vm_constants.h`); game scripts: French melee I at `>= 2` |
| hybrid `W.PlayerAge` | 1..4 | GetCurrentAge first; the 0..3 branch only fires for 0 |
| `S.posture.ourAge`, `me.age` | 1..4 | from `W.PlayerAge` |
| stk CLOCK (`__ArmyLock_PublishClock`) | 1..4 | raw GetCurrentAge; `StkControlFeedback` rejects <1 / >4 |
| `probe.scar` | raw | printed as is |
| C++ `AiArmyComp::age` | 1..4 **inferred** | unit grade digits + landmark names; lags for House of Wisdom wings and Templar commanderies |

Found and fixed: `BuildOrderResolve` overwrote `currentAge` with the step's
age, so a guide held on its last Feudal step priced Castle / Imperial incomes
as Feudal. The HUD's `currentAge + 1` is the age pushed for (now says so).

The engine value now wins for the local player (`AiEngineAgeResolve`, fresh
≤ 90 s): the actuator prints `[AOE4HOOK_ECO AGE] <token> <seq> <age>
<queued> END` on change or every 30 s, a 15 s heartbeat re-sends the
actuator. The token is 31 bits. (Correction, same day: the game VM is
Lua 5.3 with 64-bit integers, `docs/LUA_RUNTIME.md`; the mask is harmless,
not required.)

## 5. Age-up by research

`researchAgeUp` = Abbasid, Ayyubid, Templar. The queue scan (Lua, by item
name: `upgrade_age_*`, `*feudal_age`/`castle_age`/`imperial_age`, House of
Wisdom wings) covers every civ, so the DLC civs whose age-up is a research
are caught if their upgrade names follow those patterns. **LOCAL-ONLY:**
confirm the age-up upgrade names for gol, hl, hr, jin, mac, sen, tug and the
Abbasid / Ayyubid wing research names (attrib `upgrade_*` under
`races/<civ>`); Castle / Imperial commanderie bills for Templar.

## 6. Selection lock — why a gathering villager is never taken

Read from the Hex-Rays bodies in `reversed/` (16.3.11308):

- `sub_296D2E0` (`AI_LockSquad` inner): no tracking row → `sub_2924CE0`
  (4CE0 queue); row with `+0x40 == 0` → `sub_2924A70` (4A70); flag already
  set → no-op.
- `sub_2924A70` (4A70) removes from the AI's task list `a1[531..532]` every
  task whose vfunc `+24` claims the row (`sub_2923920`), clears the row's
  tactics (`a2+24` vfunc `+8`) and appends the row to the locked list
  `a1[538..540]` (AI+0x10D0).
- `sub_2A45930` (the crash leaf, `rva=0x2A45959`): a task's `a1+16` id is
  looked up with `sub_2924350` in the task lists `a1[531]` / `a1[534]`
  (entries with the `+12` byte set are skipped) and `v5[22]` (`+0x58`) is
  read without a null check. A task still referencing a task the strip just
  removed is that AV.
- Think `sub_2923300`: a row with `+0x40` is skipped only when its tactic
  vector is empty or its top entry is null; with a live stack the tactic
  keeps running. So the `+0x40` stamp cannot take a busy villager either.

Policy now: hold ≥ 7 s from the pick (config `ai_sel_hold_sec`, default 8,
floor 7), then keep only while selected, grouped or garrisoned with "Keep
garrisoned units inside" on, at most 40 s per stay (also the garrison lock's
own limit). Other unit types can use the empty-row claim behind
`kSelLockAllKinds` (off).

**RE questions for the local session (IDA + unpacker + game source):**

1. Callers of `sub_2A45930` — `sub_2AC5ED0`, `sub_2AC9810`, `sub_2AEC7D0`,
   `sub_2AC8650`: which task classes (vtables) are they, and which field of
   the parent holds the child task id read at `a1+16`?
2. `sub_2923920(ai, task)`: does it detach children / notify the parent
   plan, or only erase? Is there a Relic path that ends a task cleanly
   (the one a finished gather uses) that could run before a lock?
3. The `AI_UnlockSquad` inner: does it remove the row from `a1[538]`, clear
   `+0x40`, and leave the row in the same state as a fresh spawn (which
   think handles at `LABEL_45` → `sub_2B2C0A0`)? If yes, the empty-unlocked
   gate is about rows *stamped by us*, not every empty row.
4. `rva 0x1ED5529` (`sub_1ED54C0`, Cmd_Stop after Enable): which pointer is
   null — the squad's current order owner?
5. Does a player command on a villager with a live gather tactic end that
   tactic (task vfunc on "order overridden"), so the row empties by itself
   and the existing C++ empty-row claim takes it one tick later? A log with
   `[STK] C++ force-locked empty sid=... source=selection` right after a
   right-click answers this without IDA.
6. `+0x40` on a live stack: think runs the top tactic (`sub_2B2BF70`,
   `sub_2B2C230`); does anything there re-issue the gather order, or does
   the player's order stand?

## 7. Full AI mid-match (experiment, off)

Design behind `kAiFullAiMidMatchHandover`: Disable (combat keeps `+0x40`, no
`AI_UnlockSquad`) → Enable in the Full AI shape (`Game_AIControlLocalPlayer`
then `AI_Enable(true)`) → read-only tracking census before and 8 s after
(`[AI] full-ai handover before/after ai=... locked=... empty_unlocked=...`).
It relies on Control building a fresh AIPlayer (the 2026-09-07 table:
"creates AIPlayer"; 2026-09-02 22:39: "Control after lock drops the
standing army"). **LOCAL-ONLY:** RE of the `Game_AIControlLocalPlayer`
binding with an existing AI player (destroy + recreate or reuse?), then one
live run with the switch on; the census line decides.

## 9. Late game

`AiEcoLatePhaseUpdate` (runtime clock since Age IV): +5 min `lateMil`,
+15 min `lateEco`. Relic's `ScoringFunctions_MilitaryProductionBuilding`
ends with `UnderCountLimit(1/2/3)` and a `GroupUtility(-1, 0.25, 0)`; lists
are built when the bag loads, so `kAiLateGameScript` always returns Relic's
list with the native limit at 15 and moves the difficulty limit and
GroupUtility into callbacks. **Risk (LOCAL-ONLY):** the callback counts
`AIPlayer_GetNumPBG(Count_Current)`; if the native limit also counted
foundations / queued items, early games may now place a fourth barracks
while three are foundations. Watch the first live match.

## 10. Stone

`AiEcoStoneFor` (catalog costs): second TC 300 (not mo / gol / ma), a keep
while enemy military is at the base (900 from Castle; fr 810; tug 400 from
Feudal; Templar fortress 600 from Feudal; ja / sen Imperial; mo / gol
none), one-offs (ot 100, sen 375, by 240), standing shares (gol 0.05
bodyguards, hl 0.04 manors). **LOCAL-ONLY:** technology stone costs are not
in `unit_intelligence.scar` (techs are counted, not priced) — check the
attrib for civ techs that cost stone (Mongol improved techs at the Ovoo in
particular); build-order JSON under `Documents\AOE4HSettings\BuildOrders`
is not in the repo — a chosen guide still floors the stone share.

## 11. Scoring review — utilities by the director's formula

`v = base_scale`; per scorer: stop when `v <= 0` or `v < min`, else `v *= s`
(`sub_2B6C360`); `TimeToAcquire` `1 + (0.01-1)·t/300` (`0x2CFF6C0`);
`StrategicIntention` weighted mean of `clamp(base+extra,0,1)`
(`0x2CFDCD0`). Base scales from the decoded default bags (2026-09-26).

| Candidate (late game, Age IV) | Product | Utility |
|---|---|---|
| House, population blocked | 1010 × PopCap 1 | **1010** |
| Military building, phase 1, favoured type | 1000 × Placement 1 × SI 0.85 × TTA(50 s) 0.835 × want 1 | **≈ 710** |
| same, least-wanted type (want floored 0.5) | … × 0.5 | ≈ 355 |
| Mill, phase 2 (boost first) | 1000 × 2.0 × Relic mill branch (≈ 0.5–1) | ≈ 1000–2000 |
| ExpansionTC (not in the window) | 800 × 0.1 × TTA | ≈ 70 |

So a needed House still outranks a late barracks, the productivity phase
puts farms / mills above military buildings, and extra TCs stay out.

Proposals (not implemented; each is one Lua callback, O(1)):

1. **Keeps under base threat** — `ScoringFunctions_Keeps` =
   DefensiveStructuresCommon(0.6) + `UnderCountLimit(1/3/4)`. With the stone
   bill now present under base threat, a ×1.5 multiplier first in the list
   while `__EcoAct` carries base threat would let the keep compete with the
   counter army: e.g. base 1000 × 1.5 × SI(defense 0.6) × TTA(0.7) ≈ 630
   vs a counter unit ≈ 500–800. Needs a live read of the keep group's
   `minimum_score_to_produce` (LOCAL-ONLY).
2. **Blacksmith / university upgrades in the late phase** —
   `PlayerUnitCombatUpgrade` is SI({upgrade, combat}); in `lateMil` raise
   `iUpgrade` to 0.8 so 15 buildings do not outspend the tiers they train.
3. **Markets before 15:00** — `ScoringFunctions_Markets` has
   `MinimumGameTime(15 min)` (12 for mo / fr); the productivity phase starts
   later than that anyway, so the boost needs no change. Trader stays gated
   by `TradeRouteExistsScore` (no route, no carts).
4. **Monks** — HRE monk scoring uses `Player_HasUpgrade(feudal_age)`; with
   the engine age in `__EcoAct.age` the overlay could offer a variant that
   also works for civs whose Feudal is a research (only relevant if HRE-like
   logic is reused for such civs).

## 12. Anti-pick UI

Catalog untouched (regeneration is LOCAL-ONLY, needs the game attributes).
UI text fixed: the Enable hint said "You keep the army" in Full AI too.
The counterpick tooltip's 35 s hysteresis is still true for observed
tactics (lock-mode presses commit at once, documented in AI_BOT.md 9.1).

## LOCAL-ONLY checklist

- MSBuild `internal\AOE4HOOK.sln` Release|x64 (new: `canon_embed.rc`,
  `canon_embed.cpp`, the `MoveLockedTargetAside` target / PowerShell step).
- `tests\adversarial\run_host.ps1` with MSVC (new host tests:
  `test_canon_embed`, `test_ai_engine_age`, `.py`: `test_canon_embed`,
  `test_full_ai_handover`, `test_ai_engine_age`, `test_ai_late_game`).
- Standalone: inject from `%LOCALAPPDATA%` and read `[Docs] embedded canon`.
- Live match: `[AI] engine age=` / `[AI] age engine=… inferred=…` for
  Abbasid / Ayyubid / Templar; the second TC right after the commanderie;
  `[AI] late phase=1/2`; stone share 0 after the second TC; selection hold.
- The IDA questions in 6 and 7.

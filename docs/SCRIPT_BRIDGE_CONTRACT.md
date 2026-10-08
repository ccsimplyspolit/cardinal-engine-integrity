# C++ ↔ SCAR bridge contract (AI BOT actuator)

What the DLL and the game's Lua VM exchange while AI BOT owns the local
player's economy: the channels, the commit protocol, every key of the commit
spec, and the lines Lua prints back. The VM is Lua 5.3
([LUA_RUNTIME.md](LUA_RUNTIME.md)). Pinned by:

| What | Test |
| --- | --- |
| gen / dirty / ack transitions | `tests/adversarial/test_ai_commit_state.cpp` |
| The spec text, byte for byte | `tests/adversarial/test_ai_eco_act_spec.cpp` → `golden/eco_act_spec_{full,minimal}.lua` |
| The scripts C++ sends, byte for byte | `test_ai_scoring_script.cpp` → `golden/scoring_{session,installer}.lua` |
| Spec through the shipped installer: read/ignored keys, `gen`, partial success, player guard, locale, Lua → C++ lines | `test_eco_act_contract.py` |
| This document's key table against the code | `test_eco_act_contract.py` (`DocTests`) |
| Which layer owns each hook after inject / Apply / reload | `test_scoring_hook_owners.py` → `golden/scoring_hook_owners.json` |

## 1. Channels

| Direction | Carrier | Used for |
| --- | --- | --- |
| C++ → Lua | A Lua chunk run on the window thread by `HelperRunSoft(label, text)` (`ai_session.cpp`) | Inject, installer, commit spec, restore, Layer B invalidate |
| C++ → Lua | Globals the chunk assigns (`AOE4HOOK_ECO_CPP`, `__UnitControl_Token`, the `AOE4HOOK_*` snapshots in [CPP_BRIDGES.md](CPP_BRIDGES.md)) | Ownership flags and data |
| Lua → C++ | `print` into `warnings.log`; `scar.cpp` tails the last 256 KB, reparsed when size or mtime changes | Age feed, unit control, diagnostics (§5) |
| Lua → C++ | `io.open` file channels | **Dead in game**: the VM has no `io` (`sdk/scar/vm_census.json`). Do not add one. |

### How a chunk is sent (`scar.cpp` `ScarAcquireLiveScript`)

Every chunk runs through `Game_ScarDoString` on the Relic window thread, one
at a time (`g_scarBusy`). The gates are: in-match world, Scenario Lua loaded,
and the VM callable. Which wrapping the chunk gets depends on its path:

| Path | Who | Sent as |
| --- | --- | --- |
| ordinary | User scripts, Files, menu | Overlay bootstrap (`local_rules` + `checksum_wrappers`, `ComposeOverlayScar`) + body, in the compile-safe wrapper; waits for the start-conditions floor |
| lean | AI session and STK locks (`HelperRun` / `HelperRunSoft`) | Body + `AOE4HOOK_Local.Pump`, in the compile-safe wrapper; no bootstrap (compiling ~270 KB during start conditions faulted), no start-conditions floor |
| quiet | World-feed snapshot | Body + `Pump`, no wrapper, no success log |
| pump | Present / skip pump one-liner | As is |

The compile-safe wrapper (`scar_compile_safe.h`, run on 5.3 by
`test_scar_compile_safe.py`) carries the body as a long string and compiles
it with `loadstring`, or `load` in 5.3. A syntax or runtime error becomes a
`[AOE4HOOK] compile:` / `run:` line instead of Relic's fatal "execution
suspended" dialog. `pcall` does not cover an access violation inside a
native. For that, `HelperRunSoft` reports SEH to its caller, which parks
that feature for the match.

C++ never reads a Lua return value. What Lua did is known only from what it
prints, and for the commit spec not even that: see §3.

## 2. Scripts and their order

`AiScoringScriptAppend` (`ai_scoring_script.h`) composes both scripts from the
same parts; the golden copies are their exact text.

- **Session inject** (`InjectEcoScoring`, before `AI_Enable`, once per match):
  hook tables, shared layer, opening, economy, land only, late game, TC reserve,
  probe.
- **Installer** (`AiRuntimeInstallerScript`, label `eco_ai_act_install`): hook
  tables, actuator core, `__EcoAct.ver = kAiEcoActInstallerVersion`, shared
  layer, restore, economy, land only, engine age, late game, TC reserve.
  Re-sent whenever `g_actuatorVer != AiRuntimeInstallerVersion()` (a DLL with a
  new version installs over the old text in the same VM).
- **Commit** (label `eco_ai_cuts`, `eco_ai_cuts_farm` with the farm ring): the
  match-over guard, then the spec from `AiEcoActSpecAppendLua`
  (`ai_eco_act_spec.h`).
- **Layer B invalidate** (`kAiEcoActInvalidateLayerBLua`): after
  `AI_SetPersonality`, `AI_SetDifficulty` or an economy override.
- **Restore** (`AiRuntimeRestoreScript`, label `eco_ai_act_restore`): every
  counter channel off, or handover (sent twice there).

Every text above can run any number of times in the same VM. Re-running it
must give the same hook tables and the same `__EcoAct` state as running it
once; `test_scoring_hook_owners.py` checks this over the real Relic hook file.

### Lifecycle of a hook

A Relic personality or difficulty change reloads Relic's hook file, which puts
every `ScoringFunctions_*` global back to Relic's function.
`__EcoAct_InstallShared` and the layer installers therefore run from every
`__EcoAct_Apply` and every `__EcoAct_LayerBInvalidate`, not only at inject:

- a REPLACE body is assigned again;
- a wrap binds again only when its own wrapper is no longer in the hook's
  chain. `__EcoActWrapInner` (weak, wrapper → inner) is that chain;
  `__EcoAct_ChainHas` walks it and `__EcoAct_NoteWrap` records it.

A second Apply without a reload therefore changes no hook. A reload restores
every layer on the next commit. Each part runs in its own `pcall`, and a
failure is kept in `__EcoAct.installErr`.

## 3. Commit protocol

State in `ai_runtime.cpp` (`AiCommitState g_commit`, `ai_commit_state.h`),
under `g_lock`; `test_ai_commit_state.cpp` drives it through late acks,
enable → disable → enable, failed posts and the heartbeat:

| Name | Meaning |
| --- | --- |
| `gen` | Generation of the spec C++ wants live. Bumped on every change (samples, channels, desire, age producers, invalidate, 15 s age heartbeat `kAgeHeartbeatSec`). Never 0. |
| `dirty` | A post of `gen` is owed. |
| `ackPending` | The first post of `gen` went out; one more is owed. |
| `g_sessionEpoch` / `g_specAgeToken` | New per arm/disarm; the token tags the age line so a previous match's line in the log tail is not read as this one's. |

The flow:

1. `AiRuntimePeekActuatorScript` builds the spec **at send time** on the window
   thread from the current state, and returns it together with `gen`.
2. `HelperRunSoft` runs it. On success, `AiRuntimeMarkActuatorSent(gen)` clears
   `dirty` and flips `ackPending`, but only if the posted generation is still `gen`. A
   commit that raced a newer change leaves the newer one owed.
3. The next tick sees `ackPending` and sets `dirty` again, so **each
   generation is posted twice**. C++ cannot see whether Lua consumed it (the
   chunk wraps `__EcoAct_Apply` in `pcall`), so the second post is the retry.
4. After those two posts, a generation that Lua still refused is retried by
   the next bump. The age heartbeat bounds that wait at 15 s.

On the Lua side, in `__EcoAct_Apply(spec)`:

1. Re-assert the hooks (§2). This happens even for a generation already seen.
2. If `spec.gen == __EcoAct.gen`, return. No native is called.
3. Reject a missing or zero player before any native sees it. A native AV
   cannot be caught by `pcall`; see the 2026-09-08 note in the installer.
4. Apply the family cuts, then Layer B (`__EcoAct_ApplyDesire`).
5. `__EcoAct.gen = spec.gen` **only if every required native landed**. A
   refused required native leaves the old `gen`, so the re-post of the same
   generation retries it. Natives whose value did not change are not called
   again (`__EcoAct.prev`); the gatherer override is rewritten every time,
   because Relic restores the personality split between generations.

Partial success is therefore visible only inside Lua, as
`__EcoAct.gen != spec.gen` together with `__EcoAct.prev` for what did land.
Keys marked *best effort* below never hold `gen`.

`__EcoAct_LayerBInvalidate` forgets `prev` for the 26 Layer B keys and
re-asserts the hooks; C++ bumps `gen` with it so the values are written
again. `__EcoAct_Restore` returns the family cuts to open, pops the four
target-score ids it pushed, sets `gen = -1`, and releases the opening gate.
Income desire, intentions and the gatherer override have no getter or clear
native in `Essence_ScarFunctions.api`, so they stay at their last value until
Relic's own AI writes them.

## 4. The spec

One call:
`if type(__EcoAct_Apply)=='function' then pcall(__EcoAct_Apply,{...}) end`.
The **full** commit has 73 keys; the **minimal** one (no Layer B, no send
bits, no enemy read) has 22. Numbers are written with `%d`, `%u`, `%.0f`,
`%.2f` or `%.3f` through the DLL's static CRT (`/MT`). The DLL never calls
`setlocale`, so the decimal separator is always a dot.

Groups: **A** always; **L** when Layer B is live (`haveLayerB`); **W** building
counterpick, where `ei` is always sent and the rest only with `ei=1`; **I**, **G**,
**N**, **S** when the send mask carries income, gather, intentions or target
scores.

Read by: `Apply` is `__EcoAct_Apply`; `Desire` is `__EcoAct_ApplyDesire`
(a native call); `Age` is `__EcoAct_PublishAge`; `→ __EcoAct.x` is a scoring
flag the hooks read at evaluation time. *Required* means the key holds `gen`
until its native lands.

<!-- spec-keys:begin -->
| Key | Grp | Type | C++ source | Read by | Gen |
| --- | --- | --- | --- | --- | --- |
| `gen` | A | %u | `g_commit.gen` | Apply | — |
| `u` | A | bool | units channel | Apply: off clears every cut | — |
| `b` | A | bool | buildings channel | not read: C++ decides `ei` / `wb..wd` | — |
| `d` | A | bool | development channel | not read: C++ folds it into `iu` | — |
| `spear` | A | bool | `AiCounterCuts` | Apply (family cut, bookkeeping only) | required |
| `archer` | A | bool | `AiCounterCuts` | Apply (family cut, bookkeeping only) | required |
| `horse` | A | bool | `AiCounterCuts` | Apply (family cut, bookkeeping only) | required |
| `maa` | A | bool | `AiCounterCuts` | Apply (family cut, bookkeeping only) | required |
| `xbow` | A | bool | `AiCounterCuts` | Apply (family cut, bookkeeping only) | required |
| `gun` | A | bool | `AiCounterCuts` | Apply (family cut, bookkeeping only) | required |
| `knight` | A | bool | `AiCounterCuts` | Apply (family cut, bookkeeping only) | required |
| `mass` | A | bool | counter MASS read | not read: informational | — |
| `ecoLock` | A | bool | eco lock | → `__EcoAct.el` | — |
| `wo` | A | %d | workers only | → `__EcoAct.wo` | — |
| `ag` | A | %d | C++ age inference | Age: only when `Player_GetCurrentAge` is missing | — |
| `atk` | A | %u | `g_specAgeToken` | Age | — |
| `lockPbg` | A | {} | always empty | not read: per-PBG locks disabled (rva 0x5961C7) | — |
| `lockPbgId` | A | {} | always empty | not read: per-PBG locks disabled | — |
| `lockPbgSucc` | A | {} | always empty | not read: per-PBG locks disabled | — |
| `lockPbgSuccId` | A | {} | always empty | not read: per-PBG locks disabled | — |
| `aq` | A | {%u} | age producers | Age (queue read) | — |
| `tc` | L | %d | `maxTc` | → `__EcoAct.tc`, `GetDesiredTCCount` | — |
| `hb` | L | %d | `houseBusy` | → `__EcoAct.hb` | — |
| `lb` | L | %d | `lumberBusy` | → `__EcoAct.lb` | — |
| `wl` | L | %d | `woodLow` | → `__EcoAct.wl` | — |
| `vc` | L | %d | `villagerCap` | → `__EcoAct.vc` (8..200) | — |
| `af` | L | %d | `armyFull` | → `__EcoAct.af` | — |
| `ac` | L | %d | `armyCap` | → `__EcoAct.ac` (8..200) | — |
| `mc` | L | %d | `monkCap` | → `__EcoAct.mc` (1..24) | — |
| `op` | L | %d | `openingPhase` | → `__EcoAct.op` | — |
| `tb` | L | %d | `tcBoost` | → `__EcoAct.tb` | — |
| `tr` | L | %d | `tcReserve` | → `__EcoAct.tr` | — |
| `botc` | L | %d | `boTc` | → `__EcoAct.botc`; local opening TC gate (-1 normal, 0 wait, positive pending target count) | — |
| `bow` | L | %d | `boWing` | → `__EcoAct.bow`; local Ayyubid Advancement (0 normal, 1 hold, 2 ready) | — |
| `rw` | L | %.0f | `reserveWood` | → `__EcoAct.rw` | — |
| `rs` | L | %.0f | `reserveStone` | → `__EcoAct.rs` | — |
| `rg` | L | %.0f | `reserveGold` | → `__EcoAct.rg` | — |
| `tbx` | L | %.2f | `kAiEcoTcBoostMul` | → `__EcoAct.tbx` | — |
| `hbx` | L | %.2f | `kAiEcoHouseBoostMul` | → `__EcoAct.hbx` | — |
| `lm` | L | %d | `lateMil` | → `__EcoAct.lm` | — |
| `le` | L | %d | `lateEco` | → `__EcoAct.le` | — |
| `lmt` | L | %d | `kAiEcoLateMilTarget` | → `__EcoAct.lmt` | — |
| `lex` | L | %.2f | `kAiEcoLateEcoBoost` | → `__EcoAct.lex` | — |
| `ei` | W | %d | buildings channel and enemy read known | → `__EcoAct.ei` | — |
| `wb` | W | %.2f | barracks want | → `__EcoAct.wb` | — |
| `wa` | W | %.2f | archery want | → `__EcoAct.wa` | — |
| `ws` | W | %.2f | stable want | → `__EcoAct.ws` | — |
| `wg` | W | %.2f | siege want | → `__EcoAct.wg` | — |
| `wd` | W | %.2f | always 0 (land only) | → `__EcoAct.wd` | — |
| `df` | I | %.0f | `food` | Desire `AI_SetResourceIncomeDesire` | required |
| `dw` | I | %.0f | `wood` | Desire `AI_SetResourceIncomeDesire` | required |
| `dg` | I | %.0f | `gold` | Desire `AI_SetResourceIncomeDesire` | required |
| `ds` | I | %.0f | `stone` | Desire `AI_SetResourceIncomeDesire` | required |
| `dm` | I | %.0f | `merc` | Desire `AI_SetResourceIncomeDesire` | best effort |
| `dmi` | I | %.0f | `militia` | Desire `AI_SetResourceIncomeDesire` | best effort |
| `dpc` | I | %.0f | `popcap` | Desire `AI_SetResourceIncomeDesire` | best effort |
| `gf` | G | %.3f | `gFood` | Desire `AIPlayer_SetGathererDistributionOverride` | required |
| `gw` | G | %.3f | `gWood` | Desire (same call) | required |
| `gg` | G | %.3f | `gGold` | Desire (same call) | required |
| `gs` | G | %.3f | `gStone` | Desire (same call) | required |
| `ie` | N | %.2f | `iEcon` | Desire `SetStrategicBaseIntention economy` | required |
| `ic` | N | %.2f | `iCombat` | Desire `combat` | required |
| `io` | N | %.2f | `iOffense` | Desire `offense` | required |
| `id` | N | %.2f | `iDefense` | Desire `defense` | required |
| `ix` | N | %.2f | `iExp` | Desire `expansion` | best effort |
| `ia` | N | %.2f | `iAge` | Desire `age_up` | required |
| `iu` | N | %.2f | `iUpgrade` | Desire `upgrade` | required |
| `is` | N | %.2f | `iSiege` | Desire `siege` | required |
| `cn` | N | %.2f | `iNaval` | not read: `combat_naval` is pinned to 0 (land only) | — |
| `rl` | N | %.2f | `iReligion` | Desire `religion` | required |
| `nl` | N | %.2f | `iNull` | Desire `null` | required |
| `sf` | S | %.2f | `sFront` | Desire `PushScoreMultiplier front_line` | required |
| `sd` | S | %.2f | `sDefend` | Desire `DefendStructure` | required |
| `sa` | S | %.2f | `sAttack` | Desire `AttackStructure` | required |
| `sc` | S | %.2f | `sClump` | Desire `EnemyClump` | required |
<!-- spec-keys:end -->

The family cuts are fail-closed. Until 24.09 they passed the number 1, which
is `ITEM_UNLOCKED`, so no cut ever landed; passing the real `ITEM_LOCKED`
faulted inside the engine. `__EcoAct_SetType` now reports success without
calling a native, so the cuts are bookkeeping in `__EcoAct.prev` and never
hold `gen`.

## 5. Lines Lua prints for C++

A parsed line ends in `END` and a newline; a line without its newline may be
half written and is not used. The age parser walks back from the end of the
tail to the last line that is valid for this session's token. The control
parser looks only at the last line of each kind: when that one is incomplete
or foreign, it waits for the next print.

| Line | Printed by | Parsed by | Fields |
| --- | --- | --- | --- |
| `[AOE4HOOK_ECO AGE] <token> <seq> <age> <ageUpQueued> END` | `__EcoAct_PublishAge` (`ai_engine_age.h`) | `AiEngineAgeFeed::Read` | token = `atk` of this session; seq increases; age 1..4 |
| `[AOE4HOOK_CONTROL CLOCK] <token> <seq> <age> <sec> <hasMonk> <isDelhi> END` | `stk_control_feedback.h` | `StkControlFeedback::Read` | token = `__UnitControl_Token` |
| `[AOE4HOOK_CONTROL SEL] <token> <seq> <n> <id>… END` | `__UnitControl_PublishIds` | same | n ≤ 512 uint32 ids |
| `[AOE4HOOK_CONTROL MONKS] <token> <seq> <n> <id>… END` | `__UnitControl_PublishIds` | same | same |
| `[AOE4HOOK-AI]\|kind…` | `scar.cpp` AI probes | `scar.cpp` (`kAiMarker`) | diagnostics for the overlay log only |
| `[AOE4HOOK] …`, `[AOE4HOOK scout-haul] …` | various | not parsed | human-readable log |

### Lua 5.3 number rules for these lines

- `tostring(3.0)` is `"3.0"`, and `tostring` of an integer-valued float taken
  from a native is not an integer. C++ parses these fields into integers
  (`sscanf %d`, `istream >>`), which stop at the `.`, so the rest of the line
  no longer parses and the line is dropped. Integer fields are
  therefore written with `string.format('%d', n)` after checking that `n` is
  integral. `__UnitControl_PublishIds` skips an id that is not an integral
  positive number instead of printing it.
- `string.format('%d', 2.5)` raises in 5.3. Guard with
  `n == math.floor(n)` before formatting.
- Integers are 64-bit. The 31-bit mask on the age token is legacy and harmless.

## 6. Ownership flag

`AOE4HOOK_ECO_CPP = true` is set by the session inject. Hybrid AUTO
(`sdk/scar/hybrid_core.scar`, `hybrid_c.scar`) and the Files eco package read
it through `cppOwnsIntent`, `cppOwnsCuts`, `cppOwnsQueue` and `cppOwnsScan`, and
skip the natives C++ owns. The farm ring stays silent unless it is true.
Handover sets it to `false` before restore, so no slot is left gated with
nobody owning it.

# Relic production scoring pipeline (AoE4 16.3)

Sources: ScarDoc `Essence_ScarFunctions.api`, Relic
`sdk/scar/sga/cardinal/Data/ai/cardinal_scoring_functions.scar`,
`docs/HYBRID_NATIVE_AUDIT.md`, overlay `ai_scoring_catalog.h`,
`ai_session.cpp` / `ai_runtime.cpp` / `ai_production.cpp`.
Handshake / army lock: [AI_BOT.md](ai_bot.md), [AI_SESSION_HANDOFF.md](AI_SESSION_HANDOFF.md).
Decision: decisions/ADR-001-cpp-ai-runtime.md.
Inventory of every hook body (Relic's and the overlay's): `python tools/audit_ai_scoring.py`
→ ai_audit/scoring_inventory.md; it finds the scoring sources
itself and `--check` fails in the host tests when the committed copy is stale.

IDA Hex-Rays of `Evaluate` is no longer a blocker. Factory / Evaluate **RVAs**
were re-checked against gamesource 16.3 (`0x7FF7A5500000`) on 2026-09-14; see
[HYBRID_NATIVE_AUDIT.md](hybrid_native_subsystem_audit.md). The older pe-sieve IDB base
`0x7FF6F65C0000` is the same RVAs, different VAs. Do not mix dump VAs.

## Three different control layers

Do not mix these. They write different engine objects.

| Layer | What it decides | Typical APIs |
|---|---|---|
| **A. Production scoring** | What Relic wants TRAIN / BUILD / RESEARCH | `ScoringFunctions_*` → list of `AIProductionScoring_*` factories |
| **B. Fine-tune** | Income desire, gatherer split, **target** scoring | `AI_SetResourceIncomeDesire`, `AIPlayer_SetStrategicBaseIntention`, `AIPlayer_SetGathererDistributionOverride`, `AIPlayer_PushScoreMultiplier` (`front_line`, `DefendStructure`, `AttackStructure`, `EnemyClump`) |
| **C. Personality** | Bag key / personality asset | `AI_SetPersonality` |

`PushScore` is military **target** scoring (`LuaLibAIMilitaryTargetScoring.cpp`).
It is not a train scorer. `AIPlayer_SetStrategicBaseIntention` is not
`AIProductionScoring_StrategicIntention`.

## How Relic combines returned scorers

1. Relic production director is inside a **production scoring context**
   (`AIProductionScoring_CanPushProductionScoringFunction` reads
   `*(AIPlayer+16032)+148`). A `Rule_AddInterval` tick is **not** that context.
   Calling a factory outside it throws
   `"This function can only be called within a production scoring context"`.
2. `ScoringFunctions_X(aiPlayer)` returns a **list**. The director treats that
   list as **AND / multiply** (`1 × 0.8 × 0.9 × 0.0 = 0`). One zero kills the
   candidate. Confirmed: `MultiplyListScoringFunction` Evaluate RVA **`0x2D03940`**
   (factory `0x2C5D500`) starts at 1.0, `mulss` each child Evaluate, **early-out
   at ≤ 0**. An empty child list leaves the output **0** (not 1).
3. OR is explicit: wrap children in `AIProductionScoring_MaxScoringFunction`
   (factory `0x2C5C010`, Evaluate **`0x2D030D0`**: max of children, **empty = 0**,
   no early-out).
4. Nested AND is explicit: `AIProductionScoring_MultiplyListScoringFunction`.
5. Clamp: `AIProductionScoring_ClampedScoringFunction(min, max, inner)`
   (factory `0x2C5BED0`, Evaluate **`0x2D02F80`**: eval inner, clamp to
   object min@+0x18 / max@+0x1C).
6. Lua: `AIProductionScoring_LuaScoringFunction` (factory `0x2C5B3D0`,
   Evaluate **`0x2D02750`**) is called **per candidate**. Fail or a result `< 0`
   writes **0**. Overlay rule: the callback must be O(1). Heavy work belongs
   in C++.
7. Candidate utility (`sub_2B6C360`, verified 2026-09-26): start at the
   group's `base_scale` (+92); before **each** scorer, stop if the running value
   is `<= 0` or below `minimum_score_to_produce` (+96); otherwise multiply.
   A final value below the minimum is 0. No upper clamp: a Lua scorer above
   1.0 raises the candidate, and belongs first in the list. A group whose
   `base_scale` is below its minimum is dead (Yatai 500 < 501). Final utility
   is the max of three slots; unmet requirements inherit a dependent's
   utility + 0.01 (`sub_2B66500`), which is how a wanted unit buys its
   production building.
8. Selection (`sub_2BBA9F0`): candidates in utility order; the first
   construction candidate blocks every other construction candidate in the
   pass (`sub_2B15320` → `sub_2B152A0`), squads likewise. Affordability is
   **not** a skip (candidate vfunc +40 `sub_2B65460` returns 1): the top
   construction candidate is saved for. Selected costs feed a resource demand
   vector smoothed at 5% per pass.
9. `StrategicIntention` Evaluate `0x2CFDCD0` is the weighted mean of
   `clamp(level, 0, 1)`: a zero level zeroes the candidate. `PopCapGenerator`
   Evaluate `0x2D02910` is 0/1. Details and game data:
   findings/2026-09-26-economy-derivation.md.

`TimeToAcquire(aiPlayer, maxSec, gather, buildThis, buildReqs)` factory
`0x2C59620`, Evaluate **`0x2CFF6C0`**. Object: maxSec@+0x18, minScore@+0x1C
(copied from a global +0x244), flags gather@+0x20 / buildThis@+0x21 /
buildReqs@+0x22. Accumulated time `t` is floored at 0.01 s. Score is
`1 + (minScore-1)*t/maxSec` while `t < maxSec`, else `minScore` (Relic minScore
is ~0.01 → ~1 at t=0 and ~0.01 at the cap). Relic eco common uses **300 s**.
Do not reimplement TTA in Lua.

`CounterScore(aiPlayer, base)` factory `0x2C58DA0`, Evaluate **`0x2CFEA30`**.
Looks up Relic's chosen counter, clamps it to [0, 1]. If that value is
**exactly 0**, Evaluate writes **0** (not `base`). Otherwise
`base + (1-base)*counter`. Combat common uses `base = 0.1` **inside a Max()**
with personality, not multiplied with TimeToAcquire. That is why Relic can
still train when CounterScore is low.

`PlayerGatheringUpgrade(aiPlayer, scale, approxDist)`: factory RVA **`0x2C59A90`**.
Evaluate (vtable +0x10) RVA **`0x2D00120`**. Looks up the candidate PBG, compares
gather rates, returns `(bestRatio - 1) * scale` or **0.0** when the ratio is
≤ 1 (lookup miss, no readable delta, or upgrade does not beat current gather).
Relic uses `(10, 10)`. That 0 is multiplied into the list → horticulture /
lumber / mining never queue. Overlay **drops this native**.

`PresenceOfMyTypes` factory `0x2C615A0` / `PresenceOfEnemyTypes` `0x2C612C0`
share Evaluate **`0x2D04C30`**. Collects matching living squads (vtable +0x20),
then for each squad takes the **max** matching type-weight and **adds** it,
saturating at 1.0. Empty collect writes 0. Relic
`PresenceOfMyTypes({villager=0.01})` therefore needs ~100 villagers to
saturate. Overlay uses **0.2** (saturates around a realistic Dark Age count).
This scan is already engine-side — do not duplicate it in `LuaScoringFunction`.

`StrategicIntention` factory `0x2C59320`, Evaluate **`0x2CFDCD0`**: weighted
average of current intention levels vs the requested keys
(`sum(w_i * clamp(level_i,0,1)) / sum(w_i)`). An empty weight table writes
**1.0** (does not kill the multiply list).

Strategic intention **strings** (not an enum): `age_up`, `combat`,
`combat_naval`, `defense`, `economy`, `null`, `offense`, `religion`, `siege`,
`upgrade`.

Diagnostic native: `AIPlayer_GetSquadPBGProductionUtility`. Scoring-context
only; name-probe is not a ranking dump. Plaintext name (RVA `0x863BDDA`) has
no `lea` xref. Do not print it per candidate on the hot path.

## Overlay architecture (C++ thinks, Relic trains)

Relic still TRAINs / BUILDs / RESEARCHes after `AI_Enable`. Overlay ranks,
hard-cuts families, and explains. Do not invent a second trainer and do not
put army math in Lua (`__EcoCounter_Tick` is dead).

```text
GAME ENGINE
    │
    ▼
radar collect worker  (immutable world cache)
    │
    ▼
AiPlannerUpdate  (~2 s if AiRuntimeArmed(), else ~10 s)
    │
    ├─ AiRuntimeOnPlanPublished  (ai_counter_math + 35 s hysteresis)
    └─ AiProductionUpdateFromPlan  (rank + observatory, UnitProfilePickTrain)
    │
    ▼
dirty generation N  (latest-wins; late plan keeps last cuts)
    │
    ▼
Present AiSessionService
    │  PostMessage(WM_SCAR_AI_COMMIT) only  — never SendMessage / DoString here
    ▼
window thread  HandleAiCommitPosted
    │  install __EcoAct_* once, then lean __EcoAct_Apply if generation dirty
    ▼
thin SCAR  Player_SetSquadProductionAvailability per family
```

| File | Owns |
|---|---|
| `ai_scoring_catalog.h` | ScarDoc factories + Relic hook names. Not a second director |
| `ai_counter_math.h` | Pure cuts / role / ecoLock. Host-tested. No Windows / Lua |
| `ai_runtime.cpp` | Sample, hysteresis, actuator generation, installer / restore |
| `ai_production.cpp` | Rank + explain. HUD `AiProductionGet()` |
| `ai_session.cpp` | Enable, lean scoring (`ai_eco_act_lua.h`), `PostAiCommit` / `HandleAiCommitPosted` |
| `ai_planner.cpp` | Snapshot. `lock`/`buildings` Lua export caps 192/128 are **not** think caps |

CombatCommon (most military) stays Relic:

```text
MultipleProduced * TimeToAcquire * max(CounterScore, PersonalityPick*MinGameTime)
+ StrategicIntention(combat)
```

Overlay does **not** replace that list. It **hard-cuts** families via
`Player_SetSquadProductionAvailability`. `UnitProfilePickTrain` is the
canonical overlay tier resolver for ranking/HUD. Per-PBG predecessor locks are
disabled: generated catalog attribs are not guaranteed to belong to Relic's
runtime Squad PropertyBagGroup, and a mismatch traps at `rva=0x5961C7`.

Hard filters (role cut, knight-now locks horseman, ecoLock) run **before**
soft scores. Need-floor (`maxNeed * 0.35`) may **add** locks, never unlock a
role cut.

### Threads / FPS

| Where | Allowed | `FpsSec` |
|---|---|---|
| Collect / planner worker | Snapshot math only. No Relic natives | `AiPlanner`, `AiRuntime` |
| DXGI Present | Draw, `PostMessage`, wake collect | — |
| Relic window thread | `ScarDoString` / natives | `AiCommit`, `EcoContest` (Nested) |

Present **must not** `ScarExecuteOnWindowThread` / `SendMessage` for AI cuts
(same trap as eco contest: `WaitForSingleObject` on Present → FPS ~6).
Measure `FpsProfileGetPresentPercentiles` (p95 / p99 / max / 1% low / 0.1%
low), not average FPS. Recurring SCAR hitch from AI is a bug.

`WM_SCAR_*` (`scar.h`):

| Message | Value | Present | Window thread |
|---|---|---|---|
| `WM_SCAR_EXECUTE` | `WM_APP+0x5343` | **SendMessage** (user scripts / session lean) | `ScarDoString` |
| `WM_SCAR_BRIDGE_EXECUTE` | `+0x5344` | SendMessage | world-feed |
| `WM_SCAR_ECO_CONTEST` | `+0x5345` | **PostMessage** | gather jobs |
| `WM_SCAR_AI_COMMIT` | `+0x5346` | **PostMessage** | `__EcoAct_Apply` |

Session does **not** re-DoString full `AOE4HOOK_AI_PLAN` while `AiRuntimeArmed()`.
Radar world-feed may still publish the plan for SWM / hybrid. Workers never
call game natives. Camera / ESP filters must not shrink the AI snapshot.

### Thin SCAR actuator

Installer / restore: `AiRuntimeInstallerScript` / `AiRuntimeRestoreScript`.
Apply payload is generation + cut flags, not enemy composition:

```lua
__EcoAct_Apply({gen=N, u=0|1, b=0|1, d=0|1,
  spear=0|1, archer=0|1, horse=0|1, maa=0|1,
  xbow=0|1, gun=0|1, knight=0|1,
  lockPbg={}, lockPbgId={}})
```

`BP_GetSquadBlueprintsWithType` per family (`scar_spearman`, `scar_archer`,
…). Skip unchanged keys. O(types), not O(world). Unchanged generation = no
DoString. `__EcoAct_Apply` records `gen` only if every family cut and Layer B
native `pcall` landed (empty type list = success for this civ).
C++ posts the same gen once more on the next planner tick: Lua no-ops if
`gen` was consumed, retries if the first apply had no player or a native
miss. Do not heartbeat every tick. `__EcoAct_Restore` does **not** wipe
`prev` until every family unlock landed; disable / handover posts Restore twice
(second no-ops if the first succeeded).
Restore (installer v50) also `AIPlayer_PopScoreMultiplier`s the four target
keys the actuator pushed (`front_line` / `DefendStructure` /
`AttackStructure` / `EnemyClump`, id 1 — Push/Pop are keyed by
`AIScoreMultiplierID`, not a stack depth). Income desire, intentions and
the gatherer override have no getter / clear native in
`Essence_ScarFunctions.api`; they keep the last C++ value until another
owner writes them (documented, not restorable).

`kHandover` sets `AOE4HOOK_ECO_CPP = false` (`cppOwnsFlagRelease`) and gives
the parked `__EcoContest_Tick` back (`eco_ai_on` saves it as
`__EcoContest_TickPrev` behind a marked stub). Before v50 the flag stayed
`true` after AI BOT disable, so hybrid AUTO / `eco_upgrades.lua` remained
gated (`cppOwnsIntent` / `Cuts` / `Queue` / `Scan`, `Eco.InstallScoring`,
`__EcoContest_Impl`) for the rest of the match with nobody owning the slot.
The "all counter channels off, AI still live" path keeps the flag (session
still owns the slot and the C++ contest). Lua-mock coverage:
`tests/adversarial/test_ai_handover.py` (lupa; real embedded scripts).

Layer C → Layer B: `AI_SetPersonality` / economy override / `AI_SetDifficulty`
reload the bag. `__EcoAct_LayerBInvalidate()` (installer v50) forgets the
applied Layer B keys and `AiRuntimeInvalidateLayerB()` bumps a generation,
so one lean commit rewrites income / gatherer / intentions / target scores
after any such explicit action (Fine-tune apply, difficulty change).
Civ-specific income ids `dm` / `dmi` / `dpc` are best-effort like
`expansion`; base resources, gatherer, the ten intention strings and the
four target keys remain required for `gen`.

Safe / MP: availability natives are sim-write. Vs humans = OOS. Keep
`scar_trust`. Do not call `AIProductionScoring_*` factories from Safe or from
a Files `Rule_AddInterval` tick.

## Eco scoring override (root cause, not a random workaround)

Relic `ScoringFunctions_PlayerEconGatheringUpgrade`:

```text
PlayerUpgradeCommon = OnlyOne × StrategicIntention(upgrade=0.75, economy=0.25) × TTA(300)
+ DifficultyEconUpgradeScoring          -- Lua, 0 on Easy after Castle
+ PlayerGatheringUpgrade(10, 10)        -- native, often 0
+ PresenceOfMyTypes(villager=0.01, worker_elephant=0.01)
```

Overlay shared scoring bodies (`ai_eco_act_lua.h`, session inject + actuator installer) / hybrid `Eco.ScoreOf` /
`eco_upgrades.lua` (session is once per match; installer re-runs on
version bump — gathering used to stay Relic-native after a bump):

```text
OnlyOne × StrategicIntention(upgrade=1, economy=1)
  × Presence(villager=0.2, worker_elephant=0.2) × TTA(300)
```

`PlayerEconGatheringUpgradeSpecial` is Relic farm/ovoo presence (no gather
native). Overlay does **not** alias it to villager horticulture. Hybrid
`Eco.InstallScoring` uses `Eco.ScoreSpecial` (not `Eco.ScoreOf`).

```text
OnlyOne × StrategicIntention(upgrade=1, economy=1)
  × Presence(farm=0.2, ovoo_mon_ha_gol=0.2) × TTA(300)
```

Wheelbarrow matches Relic TTA 300 (no gather native). `GetDesiredTCCount` /
`ScoringFunctions_ExpansionTC` read `__EcoAct.tc` (default 10, ecoLock 14,
mass 6, ceiling 24), and permit only one Town Center foundation at a time.
ExpansionTC scores `StrategicIntention({economy=1})` (the upgrade key was
dropped: the second-TC window defers upgrades) and starts with
`__EcoAct_TcBoost` (`ai_tc_boom.h`): x2.5 while `__EcoAct.tb=1` and the live
stock covers `rw/rs/rg`. House ends with `__EcoAct_HouseBoost` (x2 while
`tb=1`), and `__EcoAct.tcHooks` get `__EcoAct_TcReserveGate` (0 while
`tr=1`). All three are per-evaluation callbacks; C++ owns the window
(`AiEcoGoalPlan::tcBoost/tcReserve`, `AiEcoTcWatch`).
Overlay ExpansionTC also clamps TTA to **0.85–1.0**
(Relic used 0.75). That floor ghosts unaffordable extra TCs unless Afford
is in the **function body**: the actuator installer **replaces**
`ScoringFunctions_ExpansionTC` (not wrap-once) and would drop a prior
Afford wrap. Keep ExpansionTC on `affHooks`: the Afford wrap binds again over
each new body (see "Re-assert" below), so it carries the gate twice (neutral).
`ai_eco_act_lua.h` / `eco_upgrades.lua` must not hardcode `UnderCountLimit(9,10)`
— that stomped C++ if the inject / Files Run ran after the actuator.
`eco_upgrades.lua` also REPLACES House (hb + Afford) and Cattle (invert
FirstCattle). Overlay refreshes the Documents copy if it lacks
`function ScoringFunctions_House`. Hybrid AUTO `Hybrid_Init` and
`Hybrid_EconomyTick` skip `Eco.InstallScoring` / `InstallExpansionTcScoring`
while `AOE4HOOK_ECO_CPP=true`. Those REPLACE bodies still read `__EcoAct.tc`
and keep Afford (hybrid_c had neither) so a tick before the C++ flag cannot
freeze `CFG.maxTc` or ghost unaffordable TCs. Hybrid `PostureTick` still ran
every eco tick and wrote `SetStrategicBaseIntention` (age_up / lock modes)
on top of C++ Layer B; Takeover still called `Game_AIControlLocalPlayer`
and dropped army locks. Both skip while the flag is on (`cppOwnsIntent`). Hybrid also skipped
`RestrictLowerTiers` / queue trim (`cppOwnsCuts`) so C++ family cuts are
not relocked and Relic queues are not cancelled under the C++ BOT.
Queue ticks skip `OwnedList` / `ProducerList` (`cppOwnsQueue`) so
hold/snap does not scan producers on the Relic thread after trim-off.
`PostureTick` / `Place.Audit` skip too (`cppOwnsScan`) so hybrid does
not relocate Relic rax/farms or `OwnedList` the map for HUD while C++
owns eco. Stuck-builder `Cmd_Stop` stays.

### Opening gate and explicit lock modes

`__EcoAct.op` (`AiEcoGoalPlan.openingPhase`) zeros **only**
`ScoringFunctions_MilitaryProductionBuilding`. Relic that hook is
`StrategicIntention({combat=1.0})` with no TimeToAcquire, so a Dark-Age
combat intention alone bought a barracks at 0:00 ahead of the landmark.
Layer B also drops `iCombat` / `iOffense` and raises `age_up` / `economy`
while `op` is on. Dark Age always; Feudal until the 2nd Town Center or a
Castle landmark is underway. Two threats, two scopes (2026-09-27):
`AiEcoBaseThreat` — three enemy combatants within 125 units (~25 tiles) of
an own Town Center, or an enemy tower / keep at the base — opens the gate in
any age and stops the second-TC gather. `AiEcoEnemyThreat` — an army
anywhere, a military building with a unit, or `AiEnemyIntelThreatLevel>=2`
— and the counter's own MASS / `anti_*` read open it from Age II only, and
release the second-TC spending reserve without taking its gather split.
`mass_army` opens it always. Live 2026-09-27 (French) read threat=1 at 2:35
with no enemy unit in sight and bought a Dark Age barracks. Do **not**
multiply `op` into gathering / ExpansionTC / House / landmarks.

The counter's MASS read reshapes the economy (`massArmy` in
`AiEcoComputeDesire`) only after the opening and the second-TC bill, or at
once under a base threat. Its gather split is priced from the counter need
(`AiEcoMassGatherSplit`: per-family unit bill from the catalog over 90 s,
plus villager upkeep and houses, averaged with the base split) instead of a
fixed .32 / .28 / .34 / .06.

Hoard (Fast TC / Fast Age while unmet) DEFERS
`PlayerEconGatheringUpgrade` via Layer B `iUpgrade=0.45` — never a Lua 0
on that list (multiply). Auto Feudal 1-TC keeps `iUpgrade>=0.60` so
horticulture can queue. Apply / LayerBInvalidate re-REPLACE the gather
body; Relic bag reload otherwise restores Evaluate `0x2D00120`.

`FastAgeUP` is an economy lock **while unmet** (age < Imperial): income
desire is food **2200**, gold **1100**, wood **120**, stone **0**.
`Fast TC` is the **2-TC boom** (`kAiEcoFastTcTarget=2`, `__EcoAct.tc=2`),
not ecoLock's 14. While unmet it reserves one Town Center (civ costs from
`AiEcoCivCostOf`: English 400w+300s, Mongol 750w/0s, Mali 400w+350g)
and contest prefers those deposits. Session and installer ExpansionTC
both serialize one foundation (`OneStructureFromGroupAtATime`) plus Afford.
When the goal lands, lock-mode floors lift so feudal eco / horticulture
run; `maxTc` stays 2. Contest re-asserts gatherer/income on every hoard
tick (`kContestGathFmt`) and fills `AiEcoGoalInput` from the planner
snapshot (civ / stocks / time) so the first ticks are not English-default.

Both modes zero new combat through `CombatGate`, warships and combat
upgrades through `ElGate`, and new military-production buildings through
`op` plus `el`. Existing queues and foundations are left intact: the queue API
cannot reliably distinguish an army item from a villager or economic action,
whereas the production gates stop new orders before resources are spent.

`Only Eco` applies those same hard production gates without imposing the Fast
Age food/gold ratio or the Fast TC wood/stone reserve. It keeps the ordinary
economic resource plan, Town Centers up to the user ceiling, and age-ups, while
the counter layer ignores every enemy army observation until the user leaves the
mode. It therefore creates no new military units, military buildings, combat
ships, or combat upgrades.

## Fine-tune vs production

Fine-tune `BuildAiTuneScript` pushes desire / intentions / **target**
multipliers. It must not call `AIProductionScoring_*`. Safe profile: no
sim-write scoring or availability vs humans (OOS). When Fine-tune owns
intentions it must still write Relic `siege` / `combat_naval` / `religion`
/ `null` (no UI knobs — follow the combat / defense sliders) so the
personality bag does not keep scoring rams / warships / sacred-site keeps.

## Artificial limits (this pass)

| Limit | Class | Action |
|---|---|---|
| Relic `PlayerGatheringUpgrade` zero | observed native context can yield zero; root cause needs a controlled live probe | drop native from eco hooks |
| Relic villager=0.01 (no elephant) | starve early eco techs | 0.2 villager + worker_elephant |
| Lua 10 s sample + 10 s `__EcoCounter_Tick` | Lua think rate | C++ compute on plan publish |
| `kPatchCap = 4` | hidden catch-up cap | removed earlier |
| `CombatUnitsToKill` clamp 8 | numeric cap | 24 |
| Lua `HOLD_SEC` 35 s | hysteresis (keep) | C++ `AiCounterShouldCommit` |
| User villagerCap / armyCap / lockMode | user strategy | keep |
| Hybrid `CFG.maxTc` | user strategy when C++ eco is off | C++ `__EcoAct.tc` when armed |
| Camera / ESP kind filters | render | AI session still demands units+buildings+relics |

## Relic `ScoringFunctions_*` catalog (144)

Combat: CombatCommon, CombatCommonNaval, Infantry, Khan, Elephant, RangedInfantry,
SupportMilitary.

Eco / upgrades: PlayerUpgradeCommon, PlayerEconGatheringUpgrade,
PlayerEconGatheringUpgradeSpecial, PlayerEconProductionUpgrade,
PlayerEconNavalUpgrade, PlayerEconWheelbarrowUpgrade, PlayerUpgradeFreshFoodstuffs,
PlayerUnitTierUpgrade, PlayerUnitCombatUpgrade, PlayerImperialCombatUpgrade,
PlayerImperialEconUpgrade, PlayerCombatProductionUpgrade,
PlayerNavalCombatProductionUpgrade, PlayerForceUpgrades,
PlayerSpecialCombatUpgrades, PlayerSiegeEngineerUpgrade,
PlayerUpgradeAllDifficulties, PlayerUnitCombatUpgradeAllDifficulties,
NavalUnitCombatUpgrades, NavalUnitCombatUpgrades_Sultanate,
PlayerEconUpgrade_Sultanate, PlayerUnitCombatUpgrade_Sultanate,
FrenchLongGunsNavalUpgrade.

Civ / unique: SulGovernor, SulGovernorDeferred, SulPalaceGovernor,
SulPalaceGovernorDeferred, Daimyo, DaimyoUpgradeJapanese, Shinobi, ShinobiUpgrade,
BannermanSamuraiMelee/Cavalry/Ranged, Ozutsu, Pagoda, Atabeg, Official, Cattle,
MilitarySchool, EnglishAbbeyKing, Cistern, OttomanMehter, OttomanGreatBombard,
ByzantineEastern/Western/SilkRoadMercenaryContract, ByzantineMercenaryHouse,
LancasterLevy, LancasterWynguardArmyCounterCavalry/Archers/SiegeSmall/SiegeLarge,
CollectiveHunting, GoldenHordeLandmarks{,A,B}, Manor.

Army / map: Trader, TraderUpgrade, SiegeTower, RamTower, Siege, CombatSiege,
Dock, FishingBoat, TradeBoat, TransportBoat, NavalMilitary, WarShip, Fireship,
Scouting, House, Monk, HealingOnlyUnit, SultanateMonk, DropOffs, WorkerElephants,
Yatai, ResourceGenerator, Ranch, ProductionBuilding, HighValueResearchBuilding,
Monastery, MosqueSultanate, MilitaryProductionBuilding, MilitaryResearchBuilding,
Gatherer, ExpansionTC, Pastures, Markets, WallAndGate, Aqueduct, Wonder, WallTower,
Defensive* / Landmark* / Towers_* / Random2* / Random3* / NoScoring /
CustomScoringExample.

Overlay currently overrides only: PlayerEconGatheringUpgrade,
PlayerEconGatheringUpgradeSpecial (farm/ovoo presence, not villager),
PlayerEconProductionUpgrade,
PlayerEconWheelbarrowUpgrade, ExpansionTC / GetDesiredTCCount (`__EcoAct.tc`),
House (one-at-a-time + O(1) `__EcoAct.hb` + Afford in the REPLACE body), DropOffs wrap (OneStructure; `lb`
zeros lumber names only via one `BP_GetName`), MilitaryProductionBuilding
(TTA 300 + O(1) woodLow + ElGate `el`), ResourceGenerator / Pastures / Ranch wrap
(OneStructure), Gatherer `UnderCountLimit(__EcoAct.vc)`, CombatCommon
O(1) armyFull (`__EcoAct.af`) and ecoLock (`__EcoAct.el`; unique combat
that skips CombatCommon shares `__EcoAct_CombatGate`, including
HealingOnlyUnit / SiegeTower / RamTower / Atabeg / Towers_* / Siege /
MilitarySchool / Daimyo / ByzantineMercenaryHouse — not CombatGate on Khan).
Relic Khan is MinimumGameTime(60) only; overlay wraps UnderCountLimit(1) +
Afford after the v18 restore (not affHooks). Scouting uses `__EcoAct_ScoutGate` (`af` only);
Relic `raceName` is set before orig (Mali must skip AlliedCombatFitness). Navy uses
`__EcoAct_NavalGate` (CombatCommonNaval + WarShip): `el`, **or** a hybrid map.
Dock + FishingBoat use `__EcoAct_WaterGate` (hybrid only, never `el`). Unique
combat upgrades + MilitaryProductionBuilding + DefensiveUpgrade use
`__EcoAct_ElGate` (`el` only) — no longer an alias of NavalGate, because that
one now fires on water and a land upgrade must not.
Monk/SultanateMonk/Towers_Monk `UnderCountLimit(__EcoAct.mc)`. Wrap names
live in `ai_scoring_catalog.h` (`kEcoAct*`) and are emitted as
`__EcoAct.uniqHooks` / `scoutHooks` / `navalHooks` / `waterHooks` / `elHooks` /
`monkHooks` / `affHooks`.

### Hybrid water gate (Dock + FishingBoat)

The player asked for the AI to never look at water or the port on hybrid maps.
Neither existing rule covered it: Dock was gated by nothing at all (it sits in
`affHooks`, which only kills what the AI cannot pay for), and FishingBoat is
deliberately outside NavalGate because under `el` on an island, fishing is the
correct play. `kEcoActWaterGateHooks` is therefore a third list keyed on map
class rather than on ecoLock.

Hybrid is asked of Relic, not guessed: `AI_DoWeHaveWaterLanes` for "is there
water" and `AIPlayer_IsOnAnIsland` for "are we stuck behind it". Three refusals
make it fail closed, and all three are deliberate — the expensive mistake is
gating naval on a real island, which leaves that AI with no game:

* a nil `aiPlayer` returns false before the cache is touched (a native asked
  about a nil player can answer a plausible-looking `false` rather than error);
* **both** natives must answer, since with the island half missing a hybrid map
  and an island map are indistinguishable;
* a missing or throwing native degrades to the pre-existing behaviour.

The result is cached per cuts generation: map class cannot change inside a
match, and the VM is retained across matches, so the flag must not outlive one.
The wrap is variadic (`function(aiPlayer, ...)`) because Dock and FishingBoat
are also in `affHooks`, whose wrapper is variadic — these leaves do take extra
arguments. TransportBoat is deliberately out of the list: on a hybrid map it is
how the army reaches the enemy, so cutting it strands the army rather than
saving eco. Not yet confirmed in a live hybrid match.
WallAndGate / Aqueduct / Manor / Cistern / mil / farm / dropoff / ExpansionTC /
Monastery / Markets / Cattle / CollectiveHunting / Trader / TraderUpgrade /
TradeBoat / Official / DefensiveStructureUpgrades / Wonder / LandmarkCommon /
LandmarkMongolAge1Common / FishingBoat / TransportBoat / PlayerForceUpgrades /
SulGovernor / SulPalaceGovernor wrap
(`__EcoAct_Afford` = `Player_CanAffordEntity`, hybrid AffordOk is off
while `AOE4HOOK_ECO_CPP`). Relic Wonder clamps TTA to **0.5–1.0** (ghosts
stay ≥0.5 × age_up). Landmark leaves call the 2-arg helpers — Afford bind
forwards `...`. Mongol Age1 has no TTA. Governors have no TTA (Deferred
returns 0/1 — do not wrap). ExpansionTC clamp floor **0.85** is the same
class of ghost — Afford is in the replaced body because the installer
REPLACE would drop bind-once. Relic House is PopCapGenerator only (no TTA);
session+installer REPLACE would drop bind-once on re-inject — Afford is in that body
too. Relic Cattle `FirstCattleScoring` is inverted (0 for t<6min) so
`Max(Start, Normal)` zeros the Mali opening cow — overlay REPLACES Cattle
(invert Start; Afford in the body; nils AffOrig). Do **not** ElGate
wonder/landmarks/governors
(ecoLock / fast_age still ages up when the candidate is affordable; Relic
state tree may pick an eco governor). ElGate unbinds names no longer in
`elHooks`. ExpansionTC / House / Cattle REPLACE — Afford lives in those
bodies.

**Re-assert (2026-09-27).** Relic reloads its hook file on
`AI_SetPersonality` / `AI_SetDifficulty` / an economy override, and every
`ScoringFunctions_*` is Relic's again. The shared layer used to bind each
table wrap once per VM (`origs[name]` captured → skip), so after a reload
only what `__EcoAct_Apply` re-ran came back (gathering, mil building,
economy, water, late game, TC reserve) and 66 of 107 overlay hooks stayed
Relic's for the rest of the match. Now `__EcoAct_InstallShared` runs every
part at inject and from each Apply / LayerBInvalidate: REPLACE bodies are
assigned again, and a wrap family binds a hook again only when its own
wrapper is no longer anywhere in that hook's chain (`__EcoActWrapInner`,
wrapper → what it wraps, shared with the late-game and TC-reserve layers).
A REPLACE by a later layer or a Files script therefore gets the wraps back
on the next commit instead of never. Proved on the composed scripts by
`tests/adversarial/test_scoring_hook_owners.py` (before a reload no list
changes; after one every list is as before it).
Do **not** NavalGate FishingBoat / TransportBoat — FishingBoat belongs to
WaterGate (hybrid only), TransportBoat to neither.
woodLow is feudal +
milBld≥1 + stockWood<50 so Dark Age opening wood does not starve the first
  barracks. Overlay rank treats xbow and gun as separate lines so Imperial
  handcannon does not replace arbalest demand. It uses `needGun` for
  `UnitTrainKind::Gun` (not `needXbow`). Empty-army TTK (`CombatCatalogJob`)
  calls `UnitProfilePickTrain` for that civ — Ottoman Castle janissary, not
  English `unit_handcannon_4_eng`. Knight fallback is job 6 (`unit_knight_*`),
  not horseman. Hysteresis commits a new **gun** family cut immediately
  (same as archer/xbow/horse family cuts; maa still waits 35 s).
  Knight demand: `CombatNeed` counts live knights toward the anti-ranged cav
  slot; when `knightNow` locks horseman, leftover `needHorse` is `NeedOf(Knight)`
  (anti_ranged keeps horsemen and does not fold).   Catch-up mix includes knights, siege, and unique Other so an all-knight /
  all-mangonel / all-shinobi army is not treated as empty (no fake spear/archer
  demand). Overlay still has no `NeedOf(Siege)` — Relic Siege / unique
  CombatGate train those. Anti-ranged TTK blends live knights into the
  horseman template; empty army still uses the horseman catalog. Counter
  `enArmy` includes unique Other so a feudal unique blob is not treated as
  "no army" (ecoLock would zero CombatGate). Other does not invent a family
  role — Relic unique hooks still train. Soft rank counts Other on horse/maa/
  xbow/gun/knight so observatory unique Extra is not 0 when pairwise fill
  fails. TTK remaps unclassified Other (melee → maa/xbow, ranged → archer)
  and `CombatFillFighter` keeps Other when HP>1, so pairwise unique Extra
  is not skipped. Empty-own catch-up vs unique Other / maa is maa, not
  spear/archer (feudal xbow may be untrainable). Knights still catch-up
  spears. Opening spear/archer leftover vs unique/maa is discarded (maa
  catch-up, not more spears). Siege-only / unique-only own army uses the
  enemy mix instead of copying a zero 7-kind list. Siege-dominant enemy does
  not MASS horsemen or copy leftover spears — Relic CombatSiege / Siege train.
  HUD vs that blob is «осада: Relic», not «антипик закрыт».
  `anti_siege` requires siege strictly above every other bucket (tied
  mangonels+archers stays anti_ranged; 5 mangonels + 10 maa stays anti_heavy).
  Castle+ `anti_siege` family-cuts horsemen so Relic CombatCommon does not
  MASS keshiks; feudal keeps the raid. Macro `PickUpgrade` does not treat
  siege as ranged (no ranged-armor pri 100 vs mangonels). Macro HUD counts
  gun/siege/unique (unique is not a scout chip). AI BRAIN «МОЯ АРМИЯ» /
  «ВРАГ» uses `CombatHeadcount` (gun + unique); стрелки include guns.
  A siege blob is «осада: Relic», not «no enemy army».
  Knights covering ranged at 2:1 zero `needMaa`.
  `NeedOf` / HUD «ХОЧЕТ СТРОИТЬ» zero every family cut (anti_ranged no longer
  shows spears). `PlayerSiegeEngineerUpgrade` and
  `PlayerSpecialCombatUpgrades` are ElGate (ecoLock only).
  `PlayerCombatProductionUpgrade` / `PlayerNavalCombatProductionUpgrade` /
  `PlayerImperialCombatUpgrade` are ElGate (Relic upgrade=0.75 still scores
  ~0.8 during ecoLock). `PlayerUpgradeAllDifficulties` is ElGate (no Presence).
  `DefensiveUpgrade` is ElGate (`{defense=0.25, upgrade=0.75}` ≈ 0.85 during
  ecoLock; `LowerPriorityDefensiveUpgrade` calls the helper — do not
  double-wrap). Do **not** ElGate `MilitaryResearchBuilding` (boom still
  wants a blacksmith). Do **not** ElGate `DefensiveStructureUpgrades`.
  Relic smith `PlayerUnitCombatUpgrade` / `PlayerUnitCombatUpgradeAllDifficulties`
  are not wrapped.
  Layer B `SetStrategicBaseIntention` now includes `siege`, `combat_naval`,
  `religion`, and `null` (ecoLock 0.12; `anti_siege` raises siege to 0.95).
  Lua spec keys: `is` / `cn` / `rl` / `nl`. Relic `{defense,null}` and
  sacred-site keep `Max` used the personality bag until these were set.
  Overlay still writes Relic-unknown `expansion` (Fine-tune slider / `iExp`)
  best-effort — Relic production never reads it; a reject must not block
  `gen`. Do not map `expansion`→`economy`.
  Monk Relic clamp 0.5/0.8 is not this layer — `__EcoAct.mc` caps monks.

## `AIProductionScoring_*` capability matrix (62)

| Factory | Role | Combine | Hot-path risk |
|---|---|---|---|
| MultiplyListScoringFunction | AND | product | zero kills; empty list = 0; Evaluate `0x2D03940` |
| MaxScoringFunction | OR | max | empty = 0; Evaluate `0x2D030D0` |
| ClampedScoringFunction | clamp | min..max inner | Evaluate `0x2D02F80` |
| LuaScoringFunction | callback(aiPlayer,pbg) | scalar | fail/<0 → 0; **must be O(1)**; Evaluate `0x2D02750` |
| CanPushProductionScoringFunction | gate | bool | factories only in scoring context |
| CounterScore | chosen counter | `base+(1-base)*s` | exact 0 writes 0; Evaluate `0x2CFEA30` |
| AlliedCombatFitness{,VsStrongestEnemy,VsWeakestEnemy} | army fitness | | |
| PresenceOfEnemyTypes / PresenceOfMyTypes | type weights | sum, saturate 1 | villager=0.01 starves; Evaluate `0x2D04C30` |
| EntityCombatUpgrade / MilitaryPlayerUpgrade / PresenceOfUpgradeableSquads / TierUpgrade / MaxWeaponDamage | tech / tier | TierUpgrade = count*scale clamp 0..1 | Evaluate `0x2D008C0`; Relic 0.05 is a soft bonus |
| HasProductionQueue / ProductionQueueContention | queues | | |
| OnlyProduceOneAtATime | techs / uniques | 0 if queued | Evaluate `0x2D01E70`; **not** for mass units |
| OneStructureFromGroupAtATime | buildings | | |
| UnderCountLimit / UnderCountLimitFromStateModel / VehicleUnderCountLimit | hard caps | 0 at cap | audit every use |
| MultipleProduced / NotProducedEver / NotProducedRecently / GroupNotProducedRecently | recency | | |
| TimeToAcquire | gather+build+reqs | 1 → minScore (~0.01) | Evaluate `0x2CFF6C0`; Relic eco 300s |
| AmountOfResourceNeeded / PercentOfResourcesOwned / InversePercentOfResourcesOwned / LowResourceIncome / ResourceGeneratorScore / PopCapGenerator / DeficiencyScore / ScarcityAndDeficiencyScore / PlayerGatheringUpgrade | economy | gather native often **0** | drop gather native |
| StrategicIntention | named intention | weighted avg | empty table = 1; Evaluate `0x2CFDCD0` |
| MinimumGameTime / MaximumGameTime / IncreaseOverTime | clock | | |
| PopulationPercentage / MaxPopCapPercentage / RemainingPersonnelPopCap | pop | | |
| IslandNeedingExpansionBase / PlannedPlacementScore* / TradeRouteExistsScore / NavalTransportRequired / ShouldConsiderNaval* / PlayersOnDifferentIslands* / LackOfSecuredResourceDeposits / ShouldConsiderDeepwaterFishDeposits | map/naval | | |
| RandomIntScore / InverseRandomIntScore / RandomChoiceFromRange | noise | | avoid in overlay |
| MinimumTeamControlledSacredSites / NoUpgradeProductionBlockedByThisProduction | niche | | |

## Observatory / tests

- AI BOT tab → **Scoring observatory** (`AiProductionGet`): gen / commit / role /
  exact enemy type count / PBG / unique / obsolete / CUT vs n/a.
- Pairwise `CombatUnitsToKill` vs `AiArmyComp.exactUnits` (all military
  blueprints, not first-N). Role buckets remain for Relic family cuts.
- `UnitProfileLookupByPbg` + `UnitProfilePickTrain` (incl. knight) +
  `UnitProfileHasHigherDirectTier` hard-filter obsolete predecessors.
- In-match HUD AI BRAIN: role, reason, **План / SCAR** (`generation / commitGen`),
  top-3 ranks. Copy only — no SCAR from Present.
- Host tests: `AOE4HOOK/tests/adversarial/test_ai_counter_math.cpp`
  (100 cav → anti_cav, hysteresis, role lock vs floor, knight-now locks horseman,
  unique Other is not empty ecoLock).
- Queue: `WorldComputeDemand.queues` is on when AI session is wanted. Local
  producers (TC / wooden fortress / donjon / manor / barracks / daimyo /
  Japanese forge / pagoda) are scanned every collect (`world_producer.h`).
  `ScanEntityIntel` peels vtable+0xA8 (queue) and +0x100 (attack target).
  Planner copies `hasProd` / `queueN` into `AiArmyComp`. Observatory shows
  mil queue / idle producers. Time-to-field adds a queue wait term.
- Obsolete low-tier PBG collection remains available for analysis/HUD, but the
  actuator does **not** apply it. Japanese `unit_samurai_1_jpn` / `_2_jpn`
  proved that an aoe4world attrib can resolve through the wrong runtime
  PropertyBagGroup and hit Relic's fatal assert `rva=0x5961C7` (write to null;
  `pcall` cannot catch it). Family cuts remain active; Relic
  `ScoringFunctions_PlayerUnitTierUpgrade` is still a soft preference.
- Eco contest: identical jobs are hash-skipped for 8 seconds, then retried
  because chunk success does not prove a gather order took effect. Standing
  workers are candidates even with a stale resource type; idle-only jobs check
  live `Squad_IsIdle` before issuing. Nearby sheep recovery considers every
  standing worker without consuming deposit slots for workers already gathering.
  Jobs are sorted so assignment order does not bust the skip. Opening `kEcoOpen` is **not**
  prepended to every contest (first enable already kicked gather). Fallback
  `kEcoOpen` runs **once** if C++ jobs fail during the opening window.
  Window-thread time is `FpsSec::EcoContest` (Nested, 12 ms budget).
- Eco scoring inject is hashed for the match (`g_ecoScoringApplied`); VM reset
  re-applies. Warmonger `PresenceOfEnemyTypes` is clamped 0.25..1.5 so a missing
  type does not multiply the candidate to 0. Relic has **no**
  `ScoringFunctions_Cavalry` (Warmonger's extra hook is dead unless a PBG binds it).
- FPS: `AiCommit` is Nested (window-thread SCAR hitch), not Worker.
  `FpsProfileBudgetMs` flags over-budget last times. Live p95/p99 still needs
  an injected match.

## Remaining blockers (do not "finish" in Lua)

- Queue TLS is demanded for AI session. Local producers (Relic attrib
  names: `building_unit_infantry_*` / `cavalry_*` / `ranged_*` / `siege_*`
  / `naval_*` / `religious_*`, not UI slugs `barracks`/`stable`/`dock`;
  plus TC, wooden fortress, donjon, manor, daimyo estate, mercenary house,
  Japanese forge, pagoda, …)
  are scanned every collect while the session is wanted — not 1/16 of the
  map. `ScanEntityIntel` peels entity vtable+0xA8 (queue) and +0x100
  (attack target) the same way as camo; no Relic vfunc call. Walk
  `0x10..0xA00` (local queue miss: `..0x1000`) is fallback. `hasProdScan`
  stays false only before a producer is in cache (pre-TC) or TLS on that
  building is unreadable. Unique-tech gates (`UniqGateReady` archery/barracks/
  stable) use the same Relic attrib helpers, not UI slugs.
- Relic may still offer a lower-tier PBG until its own `TierUpgrade` wins.
  Per-PBG hard locks are intentionally fail-closed after the live
  `0x5961C7` crash loop. Family cuts still lock archer/horseman via scar
  types; ApplyKey records `prev` only if every `SetType` succeeded, and
  `__EcoAct_Apply` records `gen` only if all family cuts and Layer B landed.
- Dedicated pairwise-matrix worker: **not** added. Exact types × 7 candidates
  is cheap on the collect worker. Do not put a matrix on Present.
- Do not strip `scar_trust`.
- Live FPS p95/p99 vs Relic baseline still needs an injected match.
- Live `GetSquadPBGProductionUtility` vs C++ rank still needs scoring context.
- Layer B is hashed into `__EcoAct_Apply`: income desire (food/wood/gold/stone
  plus `RT_Merc_Byz` / `RT_Militia_HRE` / `RT_Popcap` at 0 so the bag cannot
  steal ecoLock gatherers; Fine-tune sliders if you want extras), gatherer split,
  `SetStrategicBaseIntention`, and `PushScoreMultiplier` (front_line /
  DefendStructure / AttackStructure / EnemyClump, Pop then Push). Each Fine-tune
  toggle independently owns that slice. ExpansionTC / `GetDesiredTCCount` is
  C++ `__EcoAct.tc` (not Fine-tune).   `ai_eco_act_lua.h` reads that value (no
  hardcoded 9/10). Gathering / Special / ProductionUpgrade REPLACE lives in
  the installer too (Relic gather native otherwise returns on a version bump).
  House / DropOffs / mil-building / farm / villager / army / monk
  caps are Relic natives plus O(1) `__EcoAct.hb`/`wl`/`vc`/`af`/`el`/`mc` (one `BP_GetName` on
  DropOffs when lumberBusy).   ecoLock sets `el` so CombatCommon / unique
  combat (Shinobi, Ozutsu, Mehter, Bannerman, Lancaster, healers,
  siege towers, Atabeg, Towers_*, Siege, MilitarySchool, Daimyo,
  ByzantineMercenaryHouse) score 0 without replacing Relic lists. Relic Khan
  is MinimumGameTime(60) only — overlay wraps UnderCountLimit(1) + Afford
  after the v18 CombatGate restore (not CombatGate / ScoutGate / affHooks).
  Scouting is armyFull-only (`ScoutGate`). Relic Scouting reads global
  `raceName`; overlay sets it before orig so Mali is not fitness-gated.
  Navy is ecoLock-only (`NavalGate` on CombatCommonNaval + WarShip — not land
  `af`, not fishing/trade boats). Unique combat upgrades that skip
  CombatCommon (`ShinobiUpgrade`, DaimyoUpgradeJapanese, naval combat
  upgrades, `PlayerSiegeEngineerUpgrade`, `PlayerSpecialCombatUpgrades`) and
  `MilitaryProductionBuilding` /
  `PlayerCombatProductionUpgrade` /
  `PlayerNavalCombatProductionUpgrade` / `PlayerImperialCombatUpgrade` /
  `PlayerUpgradeAllDifficulties` / `DefensiveUpgrade` are `ElGate` (`el` only;
  not Relic smith building or `PlayerUnitCombatUpgradeAllDifficulties`, or
  `DefensiveStructureUpgrades`). Layer B sets Relic `siege` and
  `combat_naval`. Byzantine mercenary contracts unlock
  army → CombatGate. Wrap names are `kEcoAct*` in `ai_scoring_catalog.h` (session and installer
  prepend the same Lua tables). ExpansionTC /
  Monastery / Markets / Cattle / CollectiveHunting / Trader / TraderUpgrade /
  Official / DefensiveStructureUpgrades / TradeBoat / SulGovernor /
  SulPalaceGovernor / ExpansionTC multiply Afford (ExpansionTC Afford also
  lives in the installer REPLACE body). WallAndGate / Aqueduct / Manor / Cistern / mil /
  farm keep Relic lists but multiply `__EcoAct_Afford` (`Player_CanAffordEntity`;
  hybrid AffordOk is off while `AOE4HOOK_ECO_CPP`; WallTower / Keeps / smith /
  Trader / TradeBoat have no or weak TTA). woodLow is feudal + milBld + wood<50.
  Planner `needGun` is separate from `needXbow`; family type cuts therefore do
  not fold Imperial handcannon into arbalest. Per-PBG predecessor resolution is
  disabled (fatal PropertyBagGroup assert is outside `pcall`). ExpansionTC
  `maxTc` is C++ 10 / ecoLock 14 / mass 6, then the overlay
  **Max town centers** ceiling (default 10, same as hybrid `CFG.maxTc`).
  Hybrid AUTO does not re-assert `Eco.InstallScoring` while `AOE4HOOK_ECO_CPP=true`.
  Hybrid `PostureTick` / Takeover also skip Relic Layer B natives and
  `Game_AIControlLocalPlayer` while that flag is on (`cppOwnsIntent`).
  Hybrid predecessor locks (`RestrictLowerTiers`) and queue trim skip too
  (`cppOwnsCuts`) so C++ family ApplyKey is not unlocked-then-relocked.
  Hybrid queue ticks skip `OwnedList` / `ProducerList` (`cppOwnsQueue`) —
  hold/snap after trim-off was still a Relic-thread scan. Overlay settings
  / wall toggles still run. `PostureTick` / `Place.Audit` / `OnFoundation`
  skip (`cppOwnsScan`); stuck-builder stop stays.
  Safe/MP: availability is OOS.

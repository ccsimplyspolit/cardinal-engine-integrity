# Hybrid / AI Settings native audit

Canon Relic catalog is **16.3.11308** Hex-Rays at imagebase **`0x7FF7A5500000`**.
Quote **RVAs only**. Do not mix with pe-sieve IDB `0x7FF6F65C0000`
(`K:\aoe4_dlc\7ff6f65c0000.RelicCardinal.exe.i64`) — same RVAs, different VAs.

Gamesource: `K:\aoe4_dlc\aoe4\gamesource\reversed\`.
xor-bind: `gamesource/meta/scar-xor-bind.jsonl`. Many `funcs` entries are the
**LuaLib registrar** (e.g. `sub_2C5D880` for a pile of `AIProductionScoring_*`
names), not the C++ factory in the table below. Factories were re-read from
16.3 gamesource on 2026-09-14; wrapper RVAs match `sdk/scar/ScarNativeRvas.h`.

`ida_ok=1` in `AOE4HOOK_AI_SETTINGS`. TSV `CHECKSUM_MATRIX.tsv` `safe_read` on
Cancel / ProductionScoring / PushScore is **wrong**. Hex-Rays below is the gate.

Overlay think / cuts / eco-zero: [AI_SCORING_PIPELINE.md](AI_SCORING_PIPELINE.md).
This file is **gates only**. `PushScore` is target scoring, not `ScoringFunctions_*`.

## Catalog (gates; RVA = 16.3 gamesource)

| Native | Factory RVA | Inner RVA | Hex-Rays (16.3) | Overlay |
|---|---|---|---|---|
| `AIProductionScoring_UnderCountLimit` | `0x2C58970` | factory | Alloc `(maxCount, a3, flag)` size 40. Requires `*(AIPlayer+16032)+148` else throw `"This function can only be called within a production scoring context"`. **AIWorldData**. | offline/risk opt-in. A Rule tick is **not** that context — `pcall` fails unless Relic director is inside scoring. Default **off**. |
| `AIProductionScoring_CanPushProductionScoringFunction` | `0x2C58960` | flag read | `return *(uint8_t*)(*(AIPlayer+16032)+148)` — same flag (`+0x94`). Ten-byte getter. | Gate before factories. dump_vm often **missing** in overlay `_G`. |
| `AIProductionScoring_PlayerGatheringUpgrade` | `0x2C59A90` | Evaluate `0x2D00120` | Factory stores scale@+24 / dist@+28 (`+0x18`/`+0x1C`). Evaluate: gather-rate ratio; **`v53 <= 1.0` writes 0.0**; else `(v53-1)*scale`. | Overlay **drops** from eco hooks (`ai_eco_act_lua.h`). |
| `AIProductionScoring_MultiplyListScoringFunction` | `0x2C5D500` | Evaluate `0x2D03940` | Product of children (`mulss`), start 1.0, **early-out at <= 0**. Empty list leaves out=0. Context flag +148. | Do not push an empty child vector. |
| `AIProductionScoring_MaxScoringFunction` | `0x2C5C010` | Evaluate `0x2D030D0` | Max of children. Empty list leaves out=0. No early-out. | CombatCommon wraps CounterScore with personality this way. |
| `AIProductionScoring_ClampedScoringFunction` | `0x2C5BED0` | Evaluate `0x2D02F80` | Eval inner, clamp to min@+0x18 / max@+0x1C. | Overlay ExpansionTC clamps TTA 180s to [0.85, 1.0]. |
| `AIProductionScoring_LuaScoringFunction` | `0x2C5B3D0` | Evaluate `0x2D02750` | Pushes Lua callback + PBG; fail or result < 0 writes 0. | Callback **must be O(1)**. |
| `AIProductionScoring_TimeToAcquire` | `0x2C59620` | Evaluate `0x2CFF6C0` | `1+(minScore-1)*t/maxSec` if t<maxSec else minScore (~0.01). | Relic eco 300 s. Do not reimplement in Lua. |
| `AIProductionScoring_PresenceOfMyTypes` | `0x2C615A0` | Evaluate `0x2D04C30` | Shared Evaluate with Enemy. Sum per-squad max type-weight, saturate at 1.0; empty collect = 0. | villager=0.01 starves; overlay uses 0.2. |
| `AIProductionScoring_PresenceOfEnemyTypes` | `0x2C612C0` | Evaluate `0x2D04C30` | Same Evaluate; collect filters living enemies. | Warmonger clamps this 0.25..1.5 so a missing type is not a multiply-0. |
| `AIProductionScoring_CounterScore` | `0x2C58DA0` | Evaluate `0x2CFEA30` | Clamp lookup to [0,1]; exact 0 writes 0; else `base+(1-base)*s`. | CombatCommon puts this in Max() with personality. |
| `AIProductionScoring_OnlyProduceOneAtATime` | `0x2C5AB60` | Evaluate `0x2D01E70` | 0 if this production type is already in progress, else 1. | Eco techs / uniques. Not for mass units. |
| `AIProductionScoring_TierUpgrade` | `0x2C59BD0` | Evaluate `0x2D008C0` | `count * scale` clamped 0..1. Relic uses 0.05 (soft bonus). | Overlay per-PBG predecessor locks are disabled: catalog attrib lookup hit fatal `0x5961C7`. |
| `AIProductionScoring_PopulationPercentage` | `0x2C58BD0` | factory | Same context flag; args `(targetPct>0, dropOff!=0, flags)`. Train scoring, not attack. | Same gate as UnderCountLimit. |
| `AIProductionScoring_StrategicIntention` | `0x2C59320` | Evaluate `0x2CFDCD0` | Weighted average of current intention levels vs requested keys. Empty table writes 1.0. **Not** `AIPlayer_SetStrategicBaseIntention`. | Fine-tuning warning stands. |
| `AIPlayer_PushScoreMultiplier` | `0x29C8A60` | `0x2C0A470` | Binary-search multiplier stack, push `{key, weight}`. **Target / military scoring**. LuaLib registrar is `0x29C8DD0` (name getter), not this factory. | Fine-tuning only. Not train cap. SIM_BLOCK vs humans. |
| `AIPlayer_PushUnitTypeScoreMultiplier` | `0x29C8AF0` | `0x2C0A470` | Same inner. | same |
| `AIPlayer_PopScoreMultiplier` | `0x29C8AB0` | `0x2C0A600` | Pop target-score stack. | Fine-tuning pop-then-push |
| `Entity_CancelProductionQueueItem` | `0x19D6150` | `0x85241D0` | Production component `vtable+168`, queue index, TLS sim handle. **SimWorld write**. LuaLib registrar `0x19E48A0`. TSV `safe_read` is false. | offline/risk. Safe = SendInput only. |
| `Game_EnableInput` | `0xC000C0` | `0x3642640` | Posts presentation/input command (magic `-82518169`). Not SimWorld serialize. LuaLibGame table `0xC04130`. | ScarTakeAiControl camera. Safe may call for observe; hybrid Safe skips takeover. |
| `Game_AIControlLocalPlayer` | XOR name | LuaLibGame `0xC04130` | CHECKSUM `sim_oos` / `sim_write`. | offline/risk only. Vs humans = OOS. |
| `AI_Enable` | XOR `0x8634AF1`; decrypt stub `0x2950B30` | — | `sim_oos` / `ai`. | offline/risk. `ScarTakeAiControl` emits the same natives. |
| `AI_EnableAll` | XOR; stub `0x2950E20` | — | same | same |
| `AI_SetDifficulty` | XOR; stub `0x29516C0` | — | same | same |
| `AI_SetResourceIncomeDesire` | XOR `0x7817161`; stub `0x295B3B0` | — | `sim_oos` / `ai`. | Fine-tuning + hybrid desire. Not Safe. |
| `AIPlayer_SetStrategicBaseIntention` | XOR string RVA `0x863D001` | — | `sim_oos`. Not ProductionScoring_StrategicIntention. xor-bind has **no** func LEA. | Fine-tuning. |
| `AI_LockSquad` | XOR; decrypt stub `0x295A190` | — | `sim_oos`. Hybrid SweepLocks. | not Safe |
| `Player_SetSquadProductionAvailability` / `…Internal` | LuaLibPlayer | — | `sim_oos` / `sim_write`. Live hybrid calls **`Player_SetEntityProductionAvailability`** (no `Internal` suffix). | offline/risk opt-in. Default **off**. Safe = Macro family filter. |
| `Player_RestrictBuildingList` | CHECKSUM `sim_oos` | Lua `player.scar` | Restricts building list. | same |

`AIProductionScoring_*` Lua names also appear as XOR `.rdata` (UnderCountLimit string RVA `0x863F061`). Overlay VM still often has **zero** of the family (dump_vm). Live `Has()` required before any call.

LuaLib registrar for most scoring factories: **`0x2C5D880`**. Do not treat that RVA as UnderCountLimit's C++ body.

## C++ overlay (not Relic natives)

- `ai_combat.cpp` `CombatUnitsToKill` — aoe4world catalog + live HP/reload. Feeds planner `need[]`. **Not** engine combat.
- `ai_planner.cpp` `FillEcoPlans` — `eco.mode` MASS vs UPGRADE from `rpsNeed`. Hybrid reads `AOE4HOOK_AI_PLAN.eco.mode`. `lock[owner]={native entity ids}` → `Squad_FromId`. `need.archer`/`xbow` follow catalog lines **only if trainable now** (`UnitProfileKindAvailable` at current age); otherwise Feudal stays archers/horsemen. `keepArch` holds English longbow / yeoman / yumi.
- `prod_macro.cpp` `Hold` / `cancelWatchMs` — SendInput; lockstep-safe if `engine=0`. Synced to Lua-hold via `AOE4HOOK_AI_SETTINGS.holds` when `macroSync`.
- `ScarTakeAiControl` — ScarDoString `Game_AIControlLocalPlayer` + `AI_Enable` + `AI_SetDifficulty` + `Game_EnableInput`. Same as hybrid `P.Takeover`. Scripts tab / Fine-tuning. Vs humans = OOS. Safe profile must not use this path.
- Fine-tuning `BuildAiTuneScript` — desire / intentions / **target** `PushScoreMultiplier`. Does **not** call `AIProductionScoring_*`.

## Gate

| Key | Meaning |
|---|---|
| `ida_ok=1` | Hex-Rays pass recorded in this file. UI may show native toggles. |
| `relicScoring` | Default 0. UnderCountLimit(0) only if live `Has()` + `CanPush` + not Safe. |
| `cancelNative` | Default 0. `Entity_CancelProductionQueueItem`. Forced 0 in Safe. |
| `availabilityNative` | Default 0. Filter is Lua/Macro until a blueprint list exists. |
| Lua-hold + SendInput | No Relic native. Always allowed. |

Safe = observe + Lua-hold + Macro `engine=0`. Relic director does **not** drive the local slot.

## Advanced Native Integrations

### Anti-Idle for Traders (`SCMD_DefaultAction`)

xor-bind: name string `0x6434A70`, LuaLib `0x1FF5A00`.

`hybrid_core.scar` `P.TraderAntiIdleTick`: idle trader → nearest market/trading_post via `SpatialWorldModel.FindNearest`, then `LocalCommand_SquadEntity` with `SCMD_DefaultAction` or numeric **5** if the enum is nil. Uses `SGroup_Add` / `EGroup_Add` (scardocs names), not `SGroup_AddSquad`.

### Strict Building Restrictions (`availabilityNative`)

`H.RestrictAIBuildings()` (offline / OOS risk) calls
`Player_SetEntityProductionAvailability(player, pbg, ITEM_DEFAULT|ITEM_REMOVED)`.

Blueprint cache in `hybrid_core.scar` is **suffix** civ codes (`eng`, `fre`, `rus`, …)
on stems like `building_defense_keep_eng` — **not** `english_` / `french_` prefixes.
That old wording was a corrupted copy of this file.

This is a **sim-write**. Offline / risk only.

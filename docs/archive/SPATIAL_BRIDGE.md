# AOE4HOOK Spatial Bridge

The spatial bridge publishes a compact entity snapshot from the AOE4HOOK radar
collector into the shared SCAR Lua state. `SpatialWorldModel` also exposes an
early-game food planner and an adaptive sheep-route controller built on
documented SCAR world and AI functions.

The common SCAR model is stored at:

`C:\Users\sshunko\Documents\AOE4HSettings\NativeEspData\spatial_world_model.scar`

Its generated unit catalog is stored at:

`C:\Users\sshunko\Documents\AOE4HSettings\NativeEspData\unit_intelligence.scar`

Runnable overlay scripts live in `Documents\AOE4HSettings\Scar Scripts`. That folder is the **only** plugin source. When a script is executed through the AOE4HOOK menu, the unit catalog and then the spatial model are executed automatically as separate SCAR modules. Both are hidden from the manual script list.

## Safety and authority

- SCAR files are limited to 2 MiB, must be direct `.scar` children of the
  `Scar Scripts` folder and may not contain NUL bytes.
- The bridge is disabled by default.
- It publishes at most once per configured interval (2 seconds by default).
- Bridge execution does not clear or modify multiplayer feature flags.
- Documented SCAR data remains authoritative.
- ESP entities are merged into the common model by entity ID. Documented SCAR
  values take priority; flags and AABB are supplied by the hook.
- Camera and world-to-screen values are never sent into simulation logic.
- Exact early-food orders are disabled in replays.
- Scout routing never uses `LocalCommand_*`. It uses the documented
  `AITactic_AICommandSquadMove`; `AIPlayer_UpdateSkirmishScoutingTasks` is a
  rate-limited fallback only after a rejected direct move command.

## Enabling the bridge

1. Build and load the current `InternalInjector.dll`.
2. Enter a match and open the AOE4HOOK menu with Insert.
3. Execute any `.scar` script. The spatial model loads automatically.
4. In `SCAR SPATIAL BRIDGE`, enable `Publish ESP to SCAR`.
5. Leave tree positions disabled unless exact tree geometry is required.

The UI reports the last result, number of sent entities, serialized byte size,
and age of the last successful snapshot.

## SCAR loader and autoload

The `Scripts` tab reads direct `.scar` children from
`Documents\AOE4HSettings\Scar Scripts`. Every row has its own `ЗАГРУЖЕНО`, `НЕ ЗАГРУЖЕНО`,
`ЗАГРУЗКА` or `ОШИБКА` indicator. A selected script can be executed manually.
`AUTO` on a row loads that file at match start. Config Save / Load / Autoload on inject
are on the Config tab (`Documents\AOE4HSettings\Config\config.ini`).

Autoload can target any of the 23 civilizations in the current AOE4World data
set, or every civilization. Detection combines the stable value returned by
`Player_GetRace` with the always-English `Player_GetRaceName`, including variant
and DLC civilizations. The first six legacy option indices remain unchanged so
existing configuration files retain their meaning. A runtime marker detects a
new SCAR session and schedules the configured file again for the next match.

User scripts run inside `xpcall`. The loader records the script name, selected
nation filter, detected race, completion marker, Lua traceback and up to 16 KiB
of new `warnings.log` output in `%TEMP%\aoe4_internal.log`. Missing, empty,
oversized, unsafe and NUL-containing files receive explicit diagnostics. The
original SCAR output remains in
`Documents\My Games\Age of Empires IV\warnings.log`.

## Snapshot globals

Every successful publication assigns:

```lua
AOE4HOOK_WORLD_DATA = { -- also AOE4HOOK_ESP_SNAPSHOT
    version = 3,
    source = "AOE4HOOK",
    capturedMs = 0,
    total = 0,
    count = 0,
    treeCount = 0, -- trees seen in the sim walk (not all sent as rows)
    dtMs = 0,
    truncated = false,
    census = AOE4HOOK_CENSUS, -- full-cache counts; not truncated with entities
    entities = {
        {
            id = 0,
            n = "blueprint_leaf",
            k = 0,           -- 0 resource, 1 relic, 2 building, 3 unit, 4 tree, 5 animal
            f = 0,
            o = 1,           -- owner Player_GetID; also ownerId
            g = 2,           -- veteran line / attrib _2/_3/_4
            age = 2,
            w = 1,           -- worker
            gr = 1,          -- gather 1 food 2 wood 3 gold 4 stone
            vx = 0, vz = 0, s = 0, hd = 0,
            h = { x = 0, y = 0, z = 1 }, -- unit heading when moving
            wx = 0, wz = 0,  -- ~2.5s lookahead
            p = { x = 0, y = 0, z = 0 },
            mn = { x = 0, y = 0, z = 0 }, -- optional AABB
            mx = { x = 0, y = 0, z = 0 },
            r = 0,           -- TWD: weapon from origin (native selection ring)
            r2 = 0, r3 = 0,  -- extra weapons (cannon / springald / …)
            padx = 0, padz = 0, -- occupancy pad for worker alerts, not the circle
        },
    },
}
AOE4HOOK_CENSUS = {
    dtMs = 0,
    src = "native_workers",
    rates = { food = 50, wood = 44, gold = 48, stone = 48 }, -- per worker / min
    world = { sheep = 0, deer = 0, relics = 0, gold = 0, stone = 0, berry = 0, farms = 0, trees = 0 },
    players = {
        -- Keys are Player_GetID, never lobby/world index 1..15.
        [1004] = {
            u = 0, b = 0, w = 0, army = 0, scouts = 0, idle = 0, age = 1,
            g = { food = 0, wood = 0, gold = 0, stone = 0 },
            inc = { food = 0, wood = 0, gold = 0, stone = 0, src = "workers_x_aoe4world_rate" },
            by = { ["unit_spearman_2"] = 8 },
        },
    },
}
-- Array of rows (ipairs). Field o = Player_GetID. Not comp[1] and not comp[1004].
AOE4HOOK_AI_PLAN.comp = {
    { o = 1004, age = 2, w = 18, spear = 8, archer = 0, horse = 4, maa = 0, knight = 0,
      xbow = 0, siege = 0, monk = 0, other = 0,
      need = { spear = 6, archer = 0, horse = 2, maa = 0, xbow = 0 } },
}
```

`inc` is **not** `Player_GetResourceRate` (that API returns 0 in this build). It is
workers assigned to a deposit × aoe4world villager gather rates. Live HP is still
not in the C++ row: SimEntity health offset is unverified; SWM fills
`Entity_GetHealth` only when a SCAR handle exists.

The bridge then calls `SpatialWorldModel_ImportWorldData` when available.

## SpatialWorldModel modes

```lua
SpatialWorldModel.SetMode(SpatialWorldModel.MODE_SP)
SpatialWorldModel.SetMode(SpatialWorldModel.MODE_DEBUG)
SpatialWorldModel.SetMode(SpatialWorldModel.MODE_OBSERVER)
```

- `SP_CONTROLLER`: complete SCAR world for a local controller; default mode.
- `DEBUG_HOOK`: merges ESP fields with SCAR records by entity ID.
- `OBSERVER_REPLAY`: complete observer/replay model with ESP merge.

## Public model API

```lua
local state = SpatialWorldModel.GetState()
local esp = SpatialWorldModel.GetEspSnapshot()
local entity = SpatialWorldModel.GetEntity(entityId)
local squad = SpatialWorldModel.GetSquad(squadId)
local unit = SpatialWorldModel.GetUnitProfile(squad)
local composition = SpatialWorldModel.GetPlayerComposition(playerId)
local base = SpatialWorldModel.GetBaseCenter(playerId)

local enemies = SpatialWorldModel.QueryEntities({
    enemy = true,
    category = "unit",
    visible = true,
    minConfidence = 0.25,
})

local nearest, distance = SpatialWorldModel.FindNearest(position, {
    category = "resource",
    role = "gold",
})

local score, threats = SpatialWorldModel.ThreatAt(position, 30)

local analysis = SpatialWorldModel.AnalyzeEarlyFood(player)
local applied = SpatialWorldModel.OptimizeEarlyFood(player)
local lastPlan = SpatialWorldModel.GetEarlyFoodPlan(player)

SpatialWorldModel.RegisterAIController(player)
local scouting = SpatialWorldModel.AnalyzeScouting(player)
local refreshed = SpatialWorldModel.OptimizeScouting(player)
local lastScoutingPlan = SpatialWorldModel.GetScoutingPlan(player)

local ok, reason = SpatialWorldModel.RegisterManualSelectionControl(player, {
    releaseDelay = 15.0,
    interval = 0.20,
})
local manual = SpatialWorldModel.GetManualSelectionStatus()
```

`unit` contains the exact AOE4World profile for the squad blueprint: role,
strategy bucket, civilization/age, cost, population, train time, HP, speed,
range, damage, reload, DPS, armor, counter targets, weaknesses and threat
weight. `composition` exposes weighted `cav`, `spear`, `heavy`, `ranged`,
`siege` and `naval` buckets plus exact blueprint counts and total threat.

The model updates on a SCAR interval, keeps last-seen confidence, tracks player
identity independently from current human/AI control, and derives base centers
from known buildings.

## Early food planner

During the first 300 game seconds the planner ranks visible sheep, deer,
cattle, berries and farms around workers and valid food drop-offs. Its score
combines source-specific food/minute, first-trip distance, recurring drop-off
distance, carried food, remaining deposit, saturation and nearby enemy threat.

All national controllers call `OptimizeEarlyFood` from their existing economy
tick. It can temporarily lock at most two workers, issue `SCMD_Gather` against
the selected entity, and return them to the native AI after seven seconds in
every SCAR context.

Relevant configuration keys are `earlyFoodWindow`, `earlyFoodRadius`,
`earlyFoodMinGain`, `earlyFoodMaxAssignmentsPerPass`,
`earlyFoodWorkerCooldown`, `earlyFoodLockSeconds` and
`earlyFoodIssueCommands`.

## Adaptive sheep route planner

National scripts register their AI-controlled slot immediately after
`Game_AIControlLocalPlayer` and `AI_Enable`. During the first 300 game seconds
the model clusters all known neutral sheep, validates each cluster with
`AISquad_HasPathWithinDistance`, and divides reachable clusters into independent
zones when more than one scout is available.

Each zone is ordered by nearest insertion and then improved with deterministic
2-opt passes. Candidate utility includes sheep count, added route length, the
complete return path to the nearest Town Center, time remaining in the opening
window, exact military threat from `UnitIntelligence`, and whether an enemy
scout is likely to arrive first. Dangerous and unreachable clusters are removed
before route assignment. Ownership changes cause replanning; a target with no
measurable approach progress for 12 seconds is temporarily blocked so the scout
can continue with another cluster or return home.

The executor preserves a valid committed target across ordinary replans, does
not command a scout held by the manual-selection controller, and avoids
reissuing a move while the scout is already inside capture proximity. It returns
home when no profitable neutral sheep remain, local military threat is too high,
or the five-minute window ends. A rejected `AITactic_AICommandSquadMove` may
trigger one native scouting refresh every five seconds, but never while a scout
is manually held.

The log prefixes are `[SWM] scout-route` and `[SWM] scout-route-detail`.
Aggregate logs include planned sheep, dangerous/unreachable groups, held scouts,
commands and fallback status.

Relevant configuration keys are `scoutingEnabled`, `scoutingWindow`,
`scoutingClusterRadius`, `scoutingReplanInterval`, `scoutingCommandCooldown`,
`scoutingPathFactor`, `scoutingPathSlack`, `scoutingThreatRadius`,
`scoutingMaxThreat`, `scoutingContestMargin`, `scoutingStuckTimeout`,
`scoutingBlockedTargetTtl`, `scoutingTwoOptPasses`,
`scoutingRefreshInterval` and `scoutingReportInterval`.

## Manual selection handoff

The native AI keeps the local player slot. Each selected owned squad or building
is designer-locked immediately, remains under human control while selected and
for 15 seconds after deselection, and is then explicitly unlocked back to the
AI. Reselecting an object cancels the pending release. National production code
can call `IsManualSelectionHeld` to avoid changing a selected building queue.

`Misc_GetSelectedSquads` and `Misc_GetSelectedEntities` are local presentation
APIs. No multiplayer or replay guard is applied. The controller logs lock,
unlock, selection-error and reset counters through
`GetManualSelectionStatus()`.

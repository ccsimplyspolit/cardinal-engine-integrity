# 2026-09-06 — squad lock: negative army filter + 3-monk latch

Session workstream (restored). No new RVA. Product files only.

## Bug

With AI BOT on, some civ-unique military (landsknecht, streltsy, ghulam, ozutsu, musofadi, zhuge nu, javelin, szlachta, …) stayed with Relic. Agreed split: army = human, eco + scout = Relic.

Cause: standing `isArmy` used a **positive** `combatTypes` whitelist (~60 `scar_*` strings). A unique whose SBP carries none of those types never locked.

## Filter (done)

Negative filter in `stk_lua_lock.cpp` `kArmyOn` / `stk_army_name.h`:

- army = every owned squad minus eco leaves, scout, dummy/ghost, empty name
- Hippodrome fighters and combat monks (Shaolin / warrior monk / ikko / …) are army
- ordinary monks are not army until the handover latch

Host tests: `AOE4HOOK/tests/adversarial/test_stk_army_name.cpp`.

## 3-monk relic / sacred-site latch

`stk_monk_latch.h`: fire only when `AiSessionLive` and a prior cache pass saw a ground relic and the ground count is now 0. **Sacred-site count must not delay** (`test_stk_monk_latch.cpp`).

C++ `SyncGroundRelics` pushes `__ArmyLock_MonkHandover`. Relic's first three ordinary monks stay unlocked and get lean `ai_lock_relic_kick` (`pickup_relic` / deposit) while the latch is down. After latch:

- `isArmy` becomes true for every ordinary monk
- `lockOne` still refuses live-think `AI_LockSquad` (`rva=0x1ED5529`)
- `__ArmyLock_LockOneSid` now takes SafeStrip extras and the handed-over three (was a blanket `isOrdinaryMonk` refuse — latch never transferred control)
- successful monk LockOneSid writes `__ArmyLock_PermMonk` / `__ArmyLock_MonkMine`

Hybrid (`Documents\AOE4HSettings`):

- `hybrid_core.scar` `A.MonkNeed` was 999 while relics > 0 (every scholar to Relic). Now 3, 0 after latch, mirrors `__ArmyLock_MonkAi`
- `hybrid_c.scar` quota 1 → 3, same handover / STK tables; combat-monk names skip the relic claim (`warrior_monk` contains `monk`)

Offline/risk sacred capture (`H.TrySacredCapture`) still runs **after** relics==0 and does not hold the latch.

## Build (this turn)

Host tests `test_stk_army_name` / `test_stk_monk_latch` / `test_stk_relic_kick`: all ok.

`InternalInjector` **Release|x64** → `AOE4HOOK\internal\x64\Release\InternalInjector.dll` (16:45). Strings in the image: `NEGATIVE filter`, `AI_LockSquad relock monk sid=`. Old `isArmy(sq) or isOrdinaryMonk(sq)` refuse is gone.

First MSBuild collided C1041 on `Release\vc143.pdb` (parallel eco compile). Second pass after that job exited.

## Do not

- `AI_LockSquad` a Relic relic-runner with a live tactic (`rva=0x2A45959` / `0x1ED5529`)
- Wait on `__ArmyLock_FreeSacred` to hand monks to the player
- Restore a `combatTypes` whitelist
- Edit `ai_runtime.cpp` / `mp_bypass.cpp` from this workstream

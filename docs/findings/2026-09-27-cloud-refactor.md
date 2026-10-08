# 2026-09-27 — cloud refactor: scoring, script bridge, civilizations

Plan and stages: [REFACTOR_PLAN.md](../REFACTOR_PLAN.md). Contract:
[SCRIPT_BRIDGE_CONTRACT.md](../SCRIPT_BRIDGE_CONTRACT.md). Lua version:
[LUA_RUNTIME.md](../LUA_RUNTIME.md).

This was a Linux cloud session. It had no MSBuild, no game, no IDA and no
`Documents\AOE4HSettings`.
- Host tests ran with g++ (`-std=c++17` with an MSVC CRT shim) and with
  `lupa.lua53`.
- DLL sources that changed were syntax-checked with MinGW, not MSVC.
- GitHub CI (`ci/ci.ps1`, windows-latest) has had no runner since run #180
  (2026-09-14), so no Windows build ran.

Anything that needs the game is marked **LOCAL-ONLY**. Host tests and mocks
check the protocol and the shipped script text. They do not prove how Relic's
natives behave.

## Lua

The game VM is **Lua 5.3, high confidence**:
- `luaopen_base` at RVA 0x3D17E50;
- the live census `sdk/scar/vm_census.json` shows `_VERSION "Lua 5.3"` and
  `utf8`, with no `loadstring`, `setfenv`, `unpack`, `io`, `os`, `debug` or
  `package`.

Every Lua test now runs on `lupa.lua53`, and so do the four tools that used
another interpreter. Five documents that said 5.1 were corrected.

## Bugs fixed (each in its own commit, with a test that fails on the old code)

| Commit | Bug | Effect |
|---|---|---|
| `77e4dfb9e7` | Late-game boost and TC reserve each wrapped the other's wrapper again on every Apply | `ScoringFunctions_Markets` stacked ×2 and a gate per commit (×16 after three) |
| `99fa20b13f` | The late-game military building list dropped `__EcoAct_Afford` (from `83e1d124fe`) | Military buildings scored while unaffordable in the late phase |
| `c06b30bd0c` | The shared layer bound once per VM | After a Relic personality or difficulty reload, 66 of the 107 hooks the overlay touches stayed Relic's for the rest of the match |
| `3e3acc1f9f` | `CivSettingsKey` had no case for Macedonian, Templar or Lancaster | Their civ filter switches did nothing in prod_macro; "Other" switched them off |
| `f7cdacb7f3` | `H.CivAllowed` matched needles against names that are not Relic's race names | 10 of 23 civs used the wrong switch: variants hit their base civ, and Delhi, Templar and Lancaster fell to "Other" |
| `4ec9425245` | `MacroBridge` `allow()` kept the body of the removed vs-human refusal | Every call without `force` logged "refused vs human" and set `last = "vs_human"`, then ran anyway |
| `8961fd32ca` (part) | `__UnitControl_PublishIds` printed ids with `tostring` | On 5.3 an integral float prints as `123.0`, and the C++ parser drops the whole SEL / MONKS line |

## Changes proven equivalent

- **One composer.** `AiScoringScriptAppend` (`ai_scoring_script.h`)
  builds the session and installer scripts byte for byte as before
  (`968331607a`). The goldens in `tests/adversarial/golden/` pin both.
- **Spec serializer.** It moved into `ai_eco_act_spec.h`, writing into a
  `std::string` instead of fixed buffers. 200k random inputs gave
  byte-identical output. The goldens pin the full spec (73 keys) and the
  minimal one (22 keys).
- **Shared-layer installers.** Before a reload, every hook list is unchanged
  in every harness state (`golden/scoring_hook_owners.json`). The only
  difference is after a reload, which is the bug fix above.
- **Removed Gatherer wrap.** The superseded wrap was removed and the lists
  are unchanged. The Crucible villager ticker stays.

## Checks added

| Test | What it runs |
|---|---|
| `test_ai_scoring_script.cpp` | Composer output against the golden scripts |
| `test_scoring_hook_owners.py` | Golden scripts over Relic's `cardinal_scoring_functions.scar`: who defines, replaces or wraps each hook after inject, Apply, a Relic reload and invalidate, in 7 states; installer-first order; Crucible |
| `test_ai_eco_act_spec.cpp` | Spec bytes against the goldens |
| `test_eco_act_contract.py` | Spec through the shipped installer: which keys are read or ignored; `gen` consumed only when the required natives land; a refused native retried on the re-post; best-effort keys; no native call for an unchanged spec; zero or nil player; family cuts; age fallback; Lua → C++ lines; locale; the doc's key table |
| `test_civ_table.py` | `civ_table.h` against the census race names, prod_macro, ai_settings and every civ code the DLL compares; `H.CivAllowed` for 23 races × 20 switches |
| `test_scoring_cost.py` | VM instructions and native calls per overlay callback and per repeated Apply |
| `test_macro_bridge.py` | Shipped `macro_bridge.scar` does not report a refusal |
| `test_game_lua_runtime.py` | The test interpreter is 5.3 |

## Cost, and what could move to C++

These are Lua 5.3 VM instructions measured on the shipped scripts
(`test_scoring_cost.py`). They are not frame times.

| Path | How often | Cost |
|---|---|---|
| Overlay `LuaScoringFunction` callback | Per candidate per director pass | at most 61 instructions and 2 natives |
| `__EcoAct_Apply`, generation already seen | 2 posts per generation, plus the 15 s heartbeat | about 8k instructions, no native |
| `__EcoAct_Apply`, new generation | The same posts | about 8k instructions plus the Layer B natives that changed |

Relic calls the scoring callbacks from Lua, so they cannot move. They
already only read flags that C++ computes.

The periodic chunks are also already planned in C++, and Lua only issues the
natives. Each is fingerprinted, rate-limited, and posted to the window thread
rather than run on Present:

| Chunk | Interval |
|---|---|
| `eco_contest` | 8 s, or 2 s when hoarding; resent only on change or retry |
| `eco_ai_plan` | 10 s |
| `ai_sel_tick` | 1 s |
| `ai_garrison_tick` | 2 s |
| `ai_lock_army_relock` | 3 s dedup |
| Skip map | 1 s |

What Lua still does is what only the VM can do:
- issue commands;
- read the selection, production queues and `Player_GetCurrentAge`.

Nothing further moves without an in-game `FpsSec` profile (**LOCAL-ONLY**).
No FPS gain is claimed.

## Civilizations

`internal/InternalInjector/civ_table.h` is the one table of 23 civs in the
three spellings the overlay uses:

| Spelling | Where from | Note |
|---|---|---|
| Relic race | Census | |
| aoe4world code | prod_macro | `od` = Order of the Dragon |
| Civ filter key | ai_settings | `od` = Macedonian; Sengoku, Tughlaq, Golden Horde and Jin use "Other" |

The civ branches in the economy cost table (`ai_eco_goal.h`) and the enemy
landmark aliases all use valid codes. Variant landmarks are matched by
blueprint substring on purpose.

## Found, not changed

- Follow-up in `main`, `1e2a26f671`: six places tested an engine enum with
  `type(X) == 'number'`. The census shows these enums are userdata
  (`SquadCommandType(105)`, `OwnerType(n)`), so the fallback number was always
  what got sent. They now state that number, and `test_census_enums.py`
  forbids the pattern. Passing the userdata instead was not done: that would
  change native arguments without evidence. The sheep search still also asks
  for owner type 4, which is not an `OwnerType` (valid values are 0..3), and
  is **LOCAL-ONLY**.
- `__EcoAct_Afford` appears twice in ExpansionTC, House and Cattle. This is
  neutral because the multiply-list gives the same product.
- `__EcoAct_Apply` redefines `GetDesiredTCCount` with the body that
  `__EcoAct_InstallTcBodies` has just installed. The result is the same.
- The `io.open` channels are dead in game (no `io`). They are documented in
  the contract and not removed.
- Follow-up: the tooltip in `world_feed_tips.h` said "schema 9". It has no
  translation pair, so it now says 10, and `test_bridge_schema.py` ties it and
  CPP_BRIDGES.md to `kBridgeSchemaVersion`.
- Follow-up, bug, `bc86fa6f14`: `civFilter` (ini `civ_filter`) reached SCAR,
  but `H.CivAllowed` ignored it. Hybrid AUTO now applies the same rule as
  `AiSettingsCivKeyEnabled`.

## Baseline failures (unchanged, need Windows or data)

- `test_ai_build_order_store_image.py`
- `test_verify_offsets_live.py`
- `tools/test_unit_intelligence.py`
- `tools/test_ootd_power.py`

## LOCAL-ONLY checklist (a machine with the game)

1. Build the DLL with MSBuild (x64 Release) and run `tests\adversarial\run_host.ps1`.
2. **AI BOT reload.** Start a match with AI BOT on, then change the
   difficulty in the AI BOT tab.
   - The log must show a commit after it.
   - `__EcoAct.installErr` must be nil.
   - Markets must not grow its multiplier over several commits (`[AOE4HOOK] ai scoring layer` line).
3. **Unaffordable late game.** Past Age IV + 5 min, with no wood, no
   military building is placed.
4. **Civ filter**, for Delhi, Ayyubids, Order of the Dragon, Macedonian,
   Templar and Lancaster:
   - switch that civ off → Hybrid AUTO says "civ off" and prod_macro stops;
   - switch "Other" off → those civs keep running.
5. **Selection.** Select units with AI BOT on. `[AOE4HOOK_CONTROL SEL]` lines
   carry integer ids, and the selection hold works.
6. **MacroBridge.** `MacroBridge.Run{action="cancel",...}` without `force`:
   no "refused vs human" line.
7. **Frame times.** Record an `FpsSec::AiCommit` / `EcoContest` profile for
   one match before and after, and compare.

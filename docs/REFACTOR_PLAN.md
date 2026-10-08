# Refactor plan: scoring and the C++ ↔ Lua ↔ SCAR bridge

Branch `claude/refactor-scoring-bridge`, PR #4. Started 2026-09-27 in a Linux
cloud session. Scoring and the script bridge come first; everything else
follows only where it serves them. Each stage lands as its own commit with
its checks; the status column is kept current.

## 1. Environment and what can be proved here

| Check | Here | How |
|---|---|---|
| Header-only C++ math, planners, parsers | yes | g++ `-std=c++17` with an MSVC CRT shim (host tests) |
| DLL sources compile | partly | MinGW `-fsyntax-only`; MSVC extensions (SEH, `ifstream(wstring)`) are false positives |
| Shipped Lua / SCAR, embedded literals | yes | executed on **Lua 5.3** (the game's VM, `docs/LUA_RUNTIME.md`) via `lupa.lua53` against mocks |
| Generated files reproducible from a checkout | yes | `gen_canon_embed.py --check`, `gen_stk_embedded.py --check` |
| MSBuild product build, `run_host.ps1` with MSVC | **no** | GitHub Actions `ci/ci.ps1` on windows-latest exists, but no runner has been assigned since run #180 (2026-09-14): every job fails in ~5 s with no steps or logs. Account / billing side, outside the repo |
| Anything inside the game | **no** | no game, dumps, IDA or `Documents` here |

A mock run checks protocol, branches and bookkeeping. It never proves what a
Relic native returns. Nothing here is claimed as verified in game.

Materials referenced by docs but absent here (not used as evidence): the
owner's `Documents\AOE4HSettings`, `K:\aoe4_dlc`, IDA databases, live logs,
`_arhive/incoming/_scar_dev_handoff/scardocs/html` (the audit tool reads it
when present).

## 2. Baseline (before the first change)

- Repo: no submodules, no LFS objects. `sdk/` (35 MB) holds the canon
  scripts, the Relic SGA script dump (`sdk/scar/sga`), ScarDoc
  (`Essence_ScarFunctions.api`) and a live VM census. `reversed/` (2.1 GB) and
  `gamesource/` (573 MB) are Hex-Rays exports of RelicCardinal 16.3.
- Product: `internal/AOE4HOOK.sln` — `InternalInjector` (the overlay DLL,
  122k lines in 191 files), `DllInjector`, `Standalone` (packer),
  `InternalInjectorStub`, `BridgeWatch`, `WindowWatch`, `LauncherTests`,
  `patchAT`. `server/` is a separate .NET auth service.
- Tests: `tests/adversarial` (C++ host tests + Python/Lua), driven by
  `run_host.ps1` on Windows. Linux baseline: every host test passes except
  four that need Windows, a Release DLL or data:
  `test_ai_build_order_store_image.py`, `test_verify_offsets_live.py`,
  `tools/test_unit_intelligence.py` (needs a data root) and
  `tools/test_ootd_power.py` (known, documented in its docstring).
- Runtime threads: the collect worker builds the world cache and the AI
  plan (no natives); Present only draws and posts; the game's window thread
  runs every `ScarDoString` (`docs/ARCHITECTURE.md`, ADR-001).

## 3. Problems found, with sources

### A. Lua runtime (done, stage 1)

- A1. Docs said Lua 5.1; the game is Lua 5.3 (evidence in
  `docs/LUA_RUNTIME.md`). Host tests ran on lupa's default 5.5.

### B. Scoring

- B1. `tools/audit_ai_scoring.py` (the one scoring inventory) scans
  `ai_session.cpp` / `ai_runtime.cpp` but not `ai_eco_act_lua.h`,
  `ai_economy_scoring.h`, `ai_late_game.h`, `ai_land_only.h`,
  `ai_tc_boom.h` or `hybrid_c.scar`, where the live REPLACE bodies are;
  `docs/ai_audit/*` was generated once at import (`39fce34d3a`).
- B2. `ScoringFunctions_Gatherer` has three definitions: the shared wrap
  and the Crucible fallback in `ai_eco_act_lua.h`, and the REPLACE in
  `ai_economy_scoring.h` (`__EcoAct_InstallEconomyScoring`). Both injects
  append the latter right after the former and every `__EcoAct_Apply`
  re-runs it, so the wrap never survives; only the Crucible villager ticker
  in that block has an effect.
- B3. The session inject (`InjectEcoScoring`) and the actuator installer
  (`AiRuntimeInstallerScript`) each hand-assemble the same ordered layer
  list with small differences; the order is a correctness property
  (REPLACE before wrap, TC reserve last) kept only by comments.
- B4. No executable map of "which definition owns hook X after both
  injects" — needed before any scoring body is moved.

### C. Script lifecycle and the bridge

- C1. The `__EcoAct` spec (C++ `BuildScriptUnlocked` → Lua `__EcoAct_Apply`)
  has ~50 keys; `AI_SCORING_PIPELINE.md` names a subset. No table of key,
  type, range, writer, reader and whether `gen` waits on it.
- C2. Lua → C++ runs over `print` into `warnings.log`, tailed by
  `scar.cpp` (256 KB, reparsed on size/mtime change). The `io.open` file
  channels in `stk_lua_lock.cpp` never run in the game (no `io`); their C++
  readers read files nobody writes. Audit 2026-09-24 left them in place
  because switching them to `print` would enable requests that have never
  run.
- C3. Lua 5.3 number formatting: every line C++ parses must print integers.
  To audit per protocol.
- C4. `type(OT_Neutral) == 'number'` (`ai_session.cpp`) is never true
  (`OT_Neutral` is `OwnerType(3)` userdata). The fix changes the arguments a
  native gets; it needs a live check (audit H, deferred).
- C5. `docs/CPP_BRIDGES.md` contradicts itself (schema 7 vs 10;
  `AOE4HOOK_HAS_OTHER_HUMAN` "removed" in §15 but used in §7.3 / §12);
  `docs/ARCHITECTURE.md` §5.6 says to run `gen_ui_i18n.py`, the section
  above it forbids it.

### D. Civilizations (23)

- D1. Six independent civ tables with different code systems:
  unit_intelligence codes (`en`, `od` = Order of the Dragon, `mac`), AI
  settings buckets (`eng`, `dra` = Order of the Dragon, `od` = Macedonian),
  build-order slugs, `prod_macro` `CivFam`, `ui_icons`, and Relic race
  names (`sultanate`, `hre_ha_01`, `mongol_ha_gol`, …).
- D2. `hybrid_core.scar` `H.CivAllowed` matches Relic race names against
  needles `delhi`, `ayyub`, `jeanne`, `dravid`, `zhu`, `kith`, `holl`,
  `order`; the race names are `sultanate`, `abbasid_ha_01`, `french_ha_01`,
  `hre_ha_01`, `chinese_ha_01`, `templar`, `lancaster` (Relic SGA scripts).
  Seven per-civ switches are ignored, and `pairs()` order lets a variant
  take its parent's switch.
- D3. `prod_macro.cpp` `CivSettingsKey` has no case for Macedonian, so its
  `od` switch is ignored there too.

### E. SCAR → C++

- E1. The AI BOT already thinks in C++ (ADR-001); the heavy Lua left is the
  user-facing hybrid director (`hybrid_core.scar` 8.3k lines), SWM (5.8k)
  and per-tick Lua helpers. A measured list of what runs per tick, and what
  C++ already knows, is missing.

### F. Architecture

- F1. `radar.cpp` is 17k lines (world cache, radar, observer, HUD AI
  BRAIN, TWD publish). `ai_session.cpp` carries ~1k lines of Lua literals.

## 4. Stages

| # | Stage | Change | Verification | Status |
|---|---|---|---|---|
| 0 | Repo | drop every `.gitignore` (owner's request) | `git status` | done `4ed81ecd97` |
| 1 | Lua runtime | `docs/LUA_RUNTIME.md`; tests on `lupa.lua53` | all tests pass on 5.3; `test_game_lua_runtime.py` | done `6dd9c44785` |
| 2 | Scoring inventory | audit tool reads every scoring source; regenerate `docs/ai_audit`; a test fails when a new scoring source is not in the tool | tool run; test | done `8b9d6968ac` |
| 3 | Hook ownership | execute both composed injects on 5.3 mocks; record the final owner and factory list of every `ScoringFunctions_*` for fixed spec states (golden file) | golden test | done `d46f818350`, `3958c420d3` |
| 4 | One composition | one C++ function builds the session and installer scoring scripts from one ordered layer list | byte-identical scripts before / after; golden test | done `968331607a` |
| 5 | Dead Gatherer wrap | remove the superseded wrap, keep the Crucible ticker | golden test unchanged | done in `c06b30bd0c` |
| 6 | Bridge contract | `docs/SCRIPT_BRIDGE_CONTRACT.md`: every spec key and every Lua → C++ line; tests cross-check the doc against C++ and Lua | contract test; 5.3 number-format tests | done `8961fd32ca` + this doc commit |
| 7 | Civilizations | one canonical civ table; fix D2 / D3 (bug fixes, listed separately) | civ matrix test; `H.CivAllowed` on 5.3 per race | done `3e3acc1f9f`, `f7cdacb7f3`, `ecd0f86307` |
| 8 | SCAR → C++ | measure per-tick Lua work on mocks; move what C++ already computes without natives | call-count / cost tests | measured, nothing worth moving: `7c8627b2f4` (see findings) |
| 9 | Architecture | split only where a scoring / bridge change needs it | MinGW syntax; host tests | done where needed: `ai_eco_act_spec.h`, `civ_table.h`, `ai_scoring_script.h` |
| 10 | Docs, PR, report | update docs; in-game checklist | — | done: `docs/findings/2026-09-27-cloud-refactor.md` |

Rules for every stage: no reordering of scoring operations without an
equivalence test on the same inputs; no new weights, clamps, epsilons or
fallback scores; bug fixes are separate commits with the old example, the
cause and a regression test; Relic keeps training (the overlay ranks and
gates, it is not a second trainer).

## 5. Risks

- No MSVC build here: C++ changes stay small and are syntax-checked with
  MinGW; host tests compile the headers they touch. A C++ change that only
  MSVC would reject can still land; the Windows CI is the net once it has a
  runner again.
- Mocks encode the documented factory contracts
  (`AI_SCORING_PIPELINE.md`), not measured native values.
- Behaviour fixes (D2, D3) change what the AI does for those civs; they are
  listed for the in-game check.

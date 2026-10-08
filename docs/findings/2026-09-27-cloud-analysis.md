# 2026-09-27 — cloud analysis: one copy of every script, dead toggles, MSVC literal cap

Follow-up to [cloud plan](2026-09-27-cloud-plan.md): a whole-repo pass
after the plan items. Same Linux cloud session (no MSBuild, game, IDA or
`Documents\AOE4HSettings`); what needs them is **LOCAL-ONLY** below.

## Commits (main)

| Commit | What |
|---|---|
| `4b70fc89bf` | one copy of the Relic scoring bodies (`ai_eco_act_lua.h`) for the session inject and the actuator installer |
| `8ded16b21b` | the Buildings / Development counterpick toggles act (they only changed a HUD label) |
| `fd082f608c` | static-analysis cleanups (`<cstdint>`, one `ecoLock` expression, CopyStr bound first) |
| `6a88cbec4c` | `tools/test_ootd_power.py` reads `sdk\NativeEspData`; its known failure written down |
| `e2f55de417` | raw literals under MSVC's cap; `gen_stk_embedded.py` from the repo; `debug_shots.scar` tracked |
| `6d68a9162b` | probe / dump_vm / twd / macro_bridge fall back to the canon RCDATA; four drifted C++ copies removed |

## How it was checked

- Host tests: g++ `-std=c++17` with an MSVC CRT shim, lupa (Lua 5.5 and 5.1).
- Every embedded Lua literal (33 scripts) and every `sdk` SCAR / Lua file
  (49) compiled under lupa.
- Changed DLL sources: MinGW `-fsyntax-only` (not MSVC). `scar.cpp:543/568`
  (`std::ifstream` from a `std::wstring`) is an MSVC extension, not an error there.
- cppcheck and clang-tidy over the DLL sources; findings fixed or judged
  false positives (SEH, MSVC extensions). pyflakes over `tools/` and
  `tests/`: 93 unused imports, cosmetic, left alone.
- Spec keys the C++ sends against keys the Lua reads: found `b=` / `d=`
  (below). Config keys written but not read by name: colours are read by
  prefix, `fog_scar` / `look_clip` are reset on purpose.

## Two copies that had drifted

The rule this pass enforced: every script has one source in the repo, and
whatever the DLL carries is generated from it and checked by a test.

| Script | Was | Drift | Now |
|---|---|---|---|
| Relic scoring bodies | `kEcoScoring` (ai_session.cpp) + `kInstB..G` (ai_runtime.cpp) | installer gates indexed `__EcoAct` without a nil guard; only the session had the Crucible Gatherer fallback | `ai_eco_act_lua.h`, sent by both; `test_eco_act_lua.py` |
| twd.scar | `twd_embedded.h` from Documents | no `direct_world()`: a missing Documents file fell back to a TWD that ignores `AOE4HOOK_TWD_WORLD` | canon RCDATA via `CanonEmbedReadText` |
| probe.scar, dump_vm.scar | `probe_scar.h`, `dump_vm_scar.h` from Documents | code and header text | canon RCDATA |
| macro_bridge.scar | `macro_bridge_scar.h`, by hand | header comment | canon RCDATA |
| 18 one-shots | `stk_embedded.cpp` from Documents | a trailing newline in `instant_win.scar` only | generated from `sdk/aoe4hsettings`, `--check` in `test_instant_win_routes` |

`ScarExecuteNamedScript` writes its fallback into Documents when the file is
missing; with the old copies that meant writing a stale script
(`Config\keep_documents_canon` turns the canon sync off, so nothing fixed it).

## Dead toggles

The spec carried `b=` / `d=` and the session published
`AOE4HOOK_AI_COUNTER={buildings,develop}`, but no reader existed: the two
counterpick checkboxes changed only a HUD label, and the blacksmith /
university tiers already averaged in `AiCounterLive` were never used. Now
Buildings gates the per-type military building want (`ei` / `wb` / `wa` /
`ws`), and Development raises the upgrade intention to 0.85 when the enemy's
tier is ahead (`AiEcoDevelopBehind`).

## MSVC literal cap

MSVC stops at 16380 bytes per string literal (C2026); g++ has no cap, so the
host tests never saw it. `kSelOn` (stk_lua_lock.cpp) was at 16217 bytes and
`spawn.scar` embedded at 16015. `test_raw_literal_limit.py` fails at 16000
for every raw literal under `internal/`.

## Ignored source

`.gitignore`'s `**/Debug/` (build output) also matched
`sdk/aoe4hsettings/Scar Scripts/_system/_menu/Online/Debug/`, so
`debug_shots.scar` existed only on the machine that generated
`canon_embed.rc` (`1d2343fef9`); every clone failed in rc.exe. Restored from
the `stk_embedded.cpp` copy (the bytes the DLL already shipped), re-included,
and `test_canon_embed.py` fails when an rc source is ignored by git.

## Tests registered late

`run_host.ps1` never ran `test_ai_elgate_wrap`, `test_ai_land_only`,
`test_instant_win_routes` or `test_twd_height_cache`; it does now, plus the
new `test_eco_act_lua` and `test_raw_literal_limit`.

## Left as is

- `tools/test_ootd_power.py` fails: SWM v18's low-cost scan records only the
  local player's squads, the enemy army comes from the C++ feed this harness
  does not build (docstring).
- `stk_embedded.cpp` still carries the 18 one-shots as strings although the
  canon RCDATA has the same files. It is the primary source for one-shots
  (DLL before Documents), generated and checked, so it cannot drift; moving
  it onto `CanonEmbedReadText` waits until the RCDATA path is seen working in
  a live DLL.
- `test_ai_build_order_store_image.py` (needs a Release DLL + map),
  `test_verify_offsets_live.py` (Windows), `tools/test_unit_intelligence.py`
  (needs a data root) do not run here.

## LOCAL-ONLY

- MSBuild Release|x64: `canon_embed.cpp` (`CanonEmbedReadText`), the four
  call sites, the vcxproj without the removed headers.
- `tests\adversarial\run_host.ps1` with MSVC (C2026 for real).
- Live: rename `Documents\...\System\twd.scar`, pick TWD native, expect
  `[SCAR] twd.scar ok=1 ... src=embedded` and rings drawn; the same for
  Probe / Dump VM / a Macro command. `[Docs] embedded canon: no resource`
  means the RCDATA lookup failed.

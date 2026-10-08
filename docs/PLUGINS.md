# Single plugin root

All overlay plugins live in **`Documents\AOE4HSettings`**.

Typical path: `C:\Users\<you>\Documents\AOE4HSettings`

| Subfolder | What belongs there |
|-----------|--------------------|
| `Scar Scripts\` | Custom Run rows (Files loader). AUTO is opt-in. |
| `Scar Scripts\_system\_auto\` | Match AUTO (hybrids). Hidden from Files. AI BOT Run / AUTO. |
| `Scar Scripts\_system\_menu\Online\` | Online tab (probe, dump_vm, debug HUD). Hidden from Files. |
| `Scar Scripts\_system\_menu\Offline\` | Offline tab (spawn, grant, auto_queue, …). Hidden from Files. Vs AI only. |
| `Scar Scripts\System\` | `local_rules.scar`, `checksum_wrappers.scar` (prepended once per VM). `hybrid_core.scar` (prepended only onto `hybrid_o_*`). `twd.scar` Native TWD rings (not prepended). |
| `NativeEspData\` | `spatial_world_model.scar`, `unit_intelligence.scar`, `scar_natives_live.scar`, `aoe4hook_bridge.scar` (not listed as Run rows) |
| `Lua Scripts\` | Runnable `.lua` (`DebugHUD.lua`, `warmonger.lua` / `risky_econ.lua`, `eco_upgrades.lua`) |
| `AI Profiles\` | One `.ini` per AI BOT screen (`[security]`, `[ai] live=`, locks, linked scoring / personality / fine-tune). Relic VFS does not load this. |
| `AI Templates\` | Data.sga personality copies. Game VFS still loads `DATA:AI/Personality`. Overlay never Runs this folder. Apply personality = Relic keys. |
| `AI Custom Templates\` | Fine-tuning `.ini`. Linked from the profile. Apply on AI BOT writes this match (vs AI / desync). Relic VFS does not read this. |
| `Icons\` | AoE4 World PNG (`{key}.png`) for overlay UI. `python AOE4HOOK\tools\fetch_aoe4world_icons.py` |
| `BuildOrders\` | Per-civ build-order JSON (`<civ>\<slug>.json` + `index.json`). `python AOE4HOOK\tools\fetch_build_orders.py`. Not wired into Layer B yet. [BUILD_ORDERS.md](BUILD_ORDERS.md) |
| `Config\` | `config.ini`, offsets, windowwatch |
| `Logs\` | `aoe4_internal.log` |
| `Dumps\` | SDK / Relic dumps; `Dumps\vm_census\` for dump_vm TSV |
| `Matches\` | Journal `.ndjson` when World journal is on. Overlay **stats**, not a Relic world save. Vs AI Save/Load is the Offline tab (`Event_SaveWithName`). `rejoin_session.json` is an unofficial ticket (TCP/UDP + profile, every 2 s + VEH); not lockstep after process death. |

Do **not** recreate:

- `AOE4HOOK\plugins`
- `AOE4HOOK-SCAR-Plugins`
- `Documents\ScarScripts`

Edit scars here. Overlay does not auto-run files; AUTO is opt-in per Files row or the Online / Offline / AI BOT toggles.

AI BOT tab: `AOE4HOOK/docs/AI_BOT.md`.  
Каталог всей документации проекта (не только эта папка): `AOE4HOOK/docs/README.md`.

SCAR author contract (no overlay C++ source): `AOE4HOOK/sdk/scar/CPP_BRIDGES.md`.

Python tools: `AOE4HOOK\tools` (not a repo `plugins` folder). Game personality reference copies stay in `AOE4HOOK\sdk\ai_personality`.

# SCAR checksum / OOS audit

Build: `16.3.11308.0` · functions: **4423**

Docs: Steam `scardocs` (`function_list.htm`, `Essence_ScarFunctions.api`,
`scar_overview.htm`) + `sdk/scar/functions.json` (4423).

## Summary

| Class | Count | Wrapper |
|-------|------:|---------|
| `wrap_timerule` | 67 | local pump (`Rule_Add*` / `TimeRule_*`) |
| `wrap_eventrule` | 58 | local table + `AOE4HOOK_WORLD_DATA` spawn pump |
| `wrap_proximity` | 7 | local table (no engine Prox insert) |
| `wrap_fow_sim` | 32 | type-guarded `FOW_UIRevealAll` + Transition(0.5) |
| `sim_command` | 119 | **block** in `AOE4HOOK_MP_SAFE` (`LocalCommand_*` is still the command stream) |
| `sim_write` | 714 | **block** Entity_Destroy / Player_Set / Modify / Cheat |
| `ai` | 455 | block `AI_Set*` / `AI_Lock*` / `AI_Enable`; Get* allowed |
| `safe_read` | 1155 | passthrough |
| `safe_ui` | 837 | passthrough (HUD/camera/audio) |
| `safe_fow_ui` | 6 | passthrough (`FOW_UI*`) |
| `campaign` | 687 | training/mode lua — not overlay |
| `overlay` | 53 | Hybrid / SpatialWorldModel / Probe |
| `runtime` | 37 | Lua stdlib |
| `network` | 13 | session — do not touch |
| `unknown` | 183 | leftover; treat as sim_write if a setter |

## What can be wrapped vs cannot

Wrapped (checksum-neutral for overlay scripts, `AOE4HOOK_MP_SAFE=true`):

- TimeRule / Rule_Add* / UnsavedTimeRule_* → local pump (list `LuaRules+0x20` unchanged).
- EventRule / Rule_Add*Event / demolition notify → local table + WORLD_DATA spawn pump.
- Conditional Event_* / proximity → poll Prox_*/Count getters.
- FOW sim (`FOW_ExploreAll` is **not** a live Lua name; overlay uses
  `FOW_PlayerExploreAll(player)`). ForceReveal stays blocked in `GT_MP`. Maphack
  presentation uses type-guarded `FOW_UIRevealAll` + `FOW_UIRevealAll_Transition`
  (Entities is unbound on 16.3.11308). `EngineFogService` holds ABC0
  overlay, UI entities (2s), dest/GPU CALL fill (~1s), and RA `.text` watch.
- Cmd_ / LocalCommand_ / Entity_Destroy / Player_Set* / Modify_ / AI writes → **no-op** (feature blocked, not emulated).

Cannot make checksum-neutral without all peers running the same write:

- Any sim mutation: resources, production queue, spawn/kill, `Cmd_*`, `LocalCommand_*`.
- `Misc_SyncCheckVariable` (explicit checksum stream).
- Patching `LuaRules_SerializeTimeRules` / Relic `.text` / ov+4 / FowModeTick `0x44B550`.
  Relic `.text` is RA-lethal on this build (28 sites or latch+GpuUpload → `slots=4`
  kinds 6/3/1/5 callback `0x56FD380` → `0x71A`). Auto-restore does not cancel
  already-armed kick timers. Maphack does not arm Relic `.text`.

## Confirmed checksum surfaces (IDA / live, 16.3.11308.0)

- **TimeRules**: `LuaRules_SerializeTimeRules` RVA `0x225BD50` → list `LuaRules+0x20`.
  Insert: `TimeRule_Insert` `0x225DD90`. `UnsavedTimeRule_*` same list.
- **EventRules**: separate list; `Rule_RemoveAll` clears Time+Event+Conditional.
- **Sim FOW**: exploration tiles checksummed. `FOW_UI*` and `kFowVisualObj+0x60` / GpuUpload are not.
- **ov+4 / FowModeTick `0x44B550`**: instant OOS vs AI.
- **UI-reveal latch `kFowUiRevealLatch` (`0x485260`)**: presentation BOOL
  (`F90 && (ov+4 || ov+13 || observer)`). Live 2026-08-27: 3-byte `B0 01 C3`
  plus GpuUpload jmp `0x1916490` packed `slots=4` / `0x56FD380` in ~3s.
  Overlay does not patch this site. Never 24 HUD CanSee `E8`, VisualSync,
  TileCopy, or PAGE_GUARD.
- **`LocalCommand_*`**: Essence: “Send a … command”. Same command stream as `Cmd_*`. Not a bypass.

## Wrapper file

`Documents\AOE4HSettings\Scar Scripts\System\local_rules.scar` (`AOE4HOOK_Local`, pumped from Present).

Generated wrap tables: FOW_ON=20 FOW_OFF=10 SIM_BLOCK=1341.

`AOE4HOOK_MP_SAFE = true` (default): FOW sim redirected to UI; commands/writes no-op.
`AOE4HOOK_MP_SAFE = false`: natives pass through (OOS vs any other peer).

TSV: `sdk/scar/checksum_catalog.tsv`.

# FOW debug mode audit (AoE IV 16.3.11308)

## Result

The supported implementation is a one-shot SCAR action guarded by the documented
game type. It is enabled only for replay, single-player, or offline skirmish.
Multiplayer and unknown states fail closed. The implementation does not patch
Relic `.text`, hook `CanSee`, rewrite GPU bitplanes, write fog globals, or arm
`PAGE_GUARD`.

## Evidence used

| Source | Finding | Consequence |
|---|---|---|
| `crack.dll.i64` | The original path installs a custom exception dispatcher and guards a memcpy page. Its decrypted pattern is `E8 ?? ?? ?? ?? 48 8D 95 ?? ?? ?? ?? 49 8B CC E8 ?? ?? ?? ?? 4C 8B 8D`. | The mechanism is version-fragile and unsafe to transplant. |
| Current SDK / 16.3 image | That pattern hits RVA `0x3E77BD2`, the integrity memcpy, not FOW. The current TileCopy entry is RVA `0x3B58B00` with prologue `48 89 4C 24 08 53 56 57 41 56 41 57 48 83 EC 60`. | Never guard the old hit and never use it as an FOW signature. |
| Runtime log | The previous enable installed 28 patches (latch, GPU, TileCopy, VisualSync, and 24 `CanSee` call sites). A `KERNELBASE.dll` exception followed while that set was active. | Remove all runtime patching from the operational path. |
| Full and live read-only dumps | Fog bytes and visual/GPU object slots change with lifecycle; several captures had no live visual destination at `visual+0x60/+0x68`. | A fixed pointer/buffer hold is not a reliable state model. |
| SCAR documentation | `getgametype()` returns `GT_SP=0`, `GT_MP=1`, `GT_Skirmish=2`; `World_IsReplay()` and `UI_IsReplay()` are documented reads. | These reads form a fail-closed execution gate and correctly distinguish offline skirmish from actual multiplayer. |
| Checksum catalogue | Simulation FOW writes participate in lockstep state; UI/presentation reads and controls do not serialize into `LuaRules_SerializeTimeRules`. | Simulation FOW is used only when there are no remote peers. Replay uses presentation-only calls. |

## Runtime policy

| Mode | Allowed action |
|---|---|
| Replay | One UI entity reveal plus one terrain transition; no simulation write. |
| `GT_SP` / `GT_Skirmish` | Reversible `FOW_ForceRevealAllUnblockedAreas` / `FOW_PlayerRevealAll`, plus one UI transition. |
| `GT_MP` | No reveal. A diagnostic reason is stored in `AOE4HOOK_FowDebugReason`. |
| Unknown / failed reads | No reveal. |

The script deliberately avoids `FOW_ExploreAll` and `FOW_PlayerExploreAll` because
they alter explored history and cannot restore the exact prior state. Disable uses
the matching undo/unreveal calls and always clears presentation state.

## Stability changes

- `EngineFogService` is watch-only; it does not refresh FOW or restart a transition.
- `EngineArmMapHackPageGuard` always refuses and first removes any legacy hook set.
- Direct overlay/fog-mode messages are consumed without calling Relic natives.
- The UI calls immutable built-in FOW scripts, so a stale Documents override cannot
  silently remove the game-type gate.
- Radar visibility now fails closed: if local sight data is unavailable, non-local
  entities are marked in FOW instead of visible.

## Verification

- Release x64 build completed with MSBuild 17.14. The running game held the
  normal output name open, so the verified artifact was linked as
  `InternalInjector_safe.dll` without terminating the process.
- The exact embedded Lua strings were extracted from `scar.cpp`, parsed, and run
  against mocked `GT_SP`, `GT_Skirmish`, `GT_MP`, replay, fallback-offline, and
  unknown states. Multiplayer/unknown produced no reveal calls; replay produced
  presentation calls only; offline modes produced the reversible sim calls.
- All Documents `fow*.scar` compatibility scripts parse with `luaparser`.
- `audit_scar_api.py` reports zero errors and zero unresolved calls for the Maphack
  script directory; FOW calls remain correctly flagged as high-impact behavior.
- Static call-site search confirms the operational enable path does not call the
  legacy PAGE_GUARD, visual-hook, native-overlay, or periodic entity-hold routines.

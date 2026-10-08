# Deterministic State Synchronization & SCAR VM Checksum Boundary Audit (`4,423` Engine Functions)

- **Author:** Serhii Shunko (`cc.simply.spolit@gmail.com`)
- **Classification:** Deterministic Simulation Security & Desynchronization Auditing
- **Target Architecture:** Relic Cardinal Engine (`RelicCardinal.exe` x64, Build `16.3.11308.0`)

---

## 1. Executive Summary

In lockstep real-time strategy (RTS) engines, every peer in a multiplayer session independently simulates the deterministic world state from a shared stream of validated turn commands. If any function invoked by a script, UI callback, or subsystem mutates simulation-critical memory on a single client without going through the synchronized command queue, the rolling world-state checksum diverges (`Out-of-Sync` / `OOS`), terminating the session.

This audit classifies all **4,423** exported SCAR (Scripting at Relic) virtual machine bindings in `RelicCardinal.exe` across 14 architectural domains, identifying the exact boundary between **deterministic simulation-mutating primitives** (which affect the FNV-1a rolling state digest) and **presentation-only read/UI primitives**.

---

## 2. Classification Matrix of 4,423 SCAR Bindings

| Subsystem Domain | Audited Function Count | State Mutation Profile | Rolling Checksum Impact |
|---|---:|---|---|
| `safe_read` (World & Entity Queries) | `1,155` | Read-only state inspection | Checksum-neutral |
| `safe_ui` (HUD, Camera, Audio, Presentation) | `837` | Local presentation state only | Checksum-neutral |
| `sim_write` (Entity/Player/Resource Mutators) | `714` | Direct world-state mutation (`Entity_Destroy`, `Player_SetResource`, `Modify_*`) | **Immediate OOS if uncoordinated** |
| `campaign` (Single-Player Mission Orchestration) | `687` | Scenario state & narrative triggers | Mutates campaign state tree |
| `ai` (Autonomous AI Decision & Scoring Bindings) | `455` | AI blackboard & lock state (`AI_Set*`, `AI_Enable`) | Mutates AI controller state |
| `unknown / unclassified setters` | `183` | Internal engine state setters | Treated as simulation-mutating |
| `sim_command` (Authoritative Command Stream) | `119` | Enqueues deterministic turn commands (`Cmd_*`, `LocalCommand_*`) | Synchronized via network turn frame |
| `wrap_timerule` (Deterministic Scheduler) | `67` | Modifies `LuaRules+0x20` timer linked list (`Rule_Add*`, `TimeRule_*`) | Checksummed via `LuaRules_SerializeTimeRules` |
| `wrap_eventrule` (Simulation Event Bus) | `58` | Registers callbacks on simulation events (`Rule_AddEvent*`) | Checksummed via event rule serializer |
| `spatial_analysis` (Grid & Pathing Queries) | `53` | Read-only spatial index traversal | Checksum-neutral |
| `runtime` (Embedded Lua Standard Library) | `37` | Sandboxed VM table/math helpers | Checksum-neutral (fixed-point guarded) |
| `fow_simulation` (Fog-of-War Grid State) | `32` | Mutates authoritative visibility bitmasks | Checksummed in simulation state digest |
| `network` (Session & Transport Management) | `13` | Transport session control | Protected engine boundary |
| `wrap_proximity` (Spatial Trigger Volumes) | `7` | Inserts bounding volumes into proximity ticker | Checksummed in spatial trigger list |
| `safe_fow_ui` (Presentation Visibility) | `6` | Local render-layer transition state | Checksum-neutral |

---

## 3. Static Disassembly of Checksum Serialization Surfaces (`16.3.11308.0`)

Static analysis of `RelicCardinal.exe` in IDA Pro identified the primary state-serialization routines that feed the periodic OOS verification packet:

1. **Deterministic Timer Rules (`LuaRules_SerializeTimeRules`, RVA `0x225BD50`):**
   - Traverses the active timer-rule linked list at `LuaRules + 0x20` (populated via `TimeRule_Insert` at RVA `0x225DD90`).
   - Any uncoordinated insertion or removal in `LuaRules + 0x20` alters the serialized rule count and callback hash, immediately triggering a deterministic state mismatch across peers.
2. **Explicit Synchronization Variables (`Misc_SyncCheckVariable`):**
   - Appends named script variables directly into the per-turn verification stream for deterministic debugging.
3. **Authoritative Visibility & Entity State:**
   - Per-player exploration tile bitmasks, entity fixed-point coordinates, health pools, and active production queues are hashed every checksum interval.

---

## 4. Defensive Engineering Recommendations for Lockstep Engines

1. **Compile-Time Read/Write Capability Separation:** Separate VM registration tables into distinct `SimContext` (allowed to call `sim_write` and `wrap_timerule` only during synchronized simulation ticks) and `UIContext` (restricted strictly to `safe_read` and `safe_ui` bindings).
2. **Strict Context Guards on `LuaRules_Insert`:** Reject any invocation of `TimeRule_Insert` (`0x225DD90`) or `Rule_AddEvent` originating from asynchronous UI rendering frames (`Present` / HUD callbacks) to prevent accidental or malicious client desynchronization (`CWE-362`).

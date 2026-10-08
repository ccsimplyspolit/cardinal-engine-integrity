# Deterministic Simulation, SCAR Virtual Machine, and Desynchronization Auditing in the Cardinal Engine

**Author:** Sergey Shunko  
**Classification:** Real-Time Simulation Architecture & State Integrity Auditing  
**Engine:** Relic Cardinal Engine (Age of Empires IV x64)  

---

## 1. Abstract

Deterministic real-time strategy (RTS) architectures rely on lockstep simulation models where identical inputs produce bit-exact world states across all client instances. This technical whitepaper documents the deterministic state architecture of the Cardinal Engine (`RelicCardinal.exe`), examining the SCAR (Scripting at Relic) virtual machine integration, state checksum generation, and Out-of-Sync (OOS) desynchronization detection mechanisms.

---

## 2. Lockstep Simulation & Deterministic State Model

### 2.1 Simulation Tick Execution Pipeline
The Cardinal simulation pipeline advances in fixed discrete ticks (typically 8 to 20 simulation ticks per second, decoupled from visual frame rendering):

```
+-------------------------------------------------------------+
|                 Simulation Tick Pipeline                    |
+-------------------------------------------------------------+
| 1. Collect & Validate Remote Command Packets (Turn n)        |
| 2. Execute Deterministic Pathfinding & Spatial Grid Updates |
| 3. Step Combat Catalog & Projectile Systems                 |
| 4. Advance SCAR Scripting VM Operations                     |
| 5. Calculate World State Checksum (OOS Audit Digest)        |
+-------------------------------------------------------------+
```

### 2.2 Rolling State Hash Computation
At predetermined tick intervals (e.g., every 8 ticks), the engine computes a rolling hash of all deterministic entities:

```cpp
struct SimulationSyncDigest {
    uint32_t simulation_tick;
    uint32_t entity_count;
    uint64_t spatial_state_hash;
    uint64_t resource_state_hash;
    uint64_t combined_checksum;
};

uint64_t ComputeSimulationChecksum(const WorldState* world) {
    uint64_t digest = 0xCBF29CE484222325ULL; // FNV-1a 64-bit basis
    
    // 1. Hash dynamic entity positions and health states
    for (const Entity& ent : world->entities) {
        digest ^= ent.unique_id;
        digest *= 0x100000001B3ULL;
        
        digest ^= ent.position.x_fixed_point;
        digest *= 0x100000001B3ULL;
        
        digest ^= ent.position.y_fixed_point;
        digest *= 0x100000001B3ULL;
        
        digest ^= ent.health_fixed_point;
        digest *= 0x100000001B3ULL;
    }
    
    return digest;
}
```

---

## 3. SCAR (Scripting at Relic) Virtual Machine Sandboxing

SCAR scripts provide mission logic, custom triggers, and competitive rule definitions. The embedded SCAR interpreter executes inside a managed sandbox:
- **Floating-Point Determinism:** Standard IEEE 754 floating-point operations can diverge across different CPU microarchitectures (AMD vs Intel, AVX vs SSE2). The Cardinal Engine enforces strict fixed-point arithmetic or compiler fast-math disabling across all SCAR math primitives.
- **State Serialization:** SCAR script variables marked as networked or persistent are serialized through dedicated serialization tables to verify client parity.

---

## 4. Desynchronization (OOS) Detection & Forensic Tracing

When two clients in a session report diverging `combined_checksum` values for the same simulation tick:
1. **Desync Trigger:** The match host flags an Out-of-Sync state error.
2. **State Dump Serialization:** Both clients immediately serialize a detailed diagnostic dump of their local world state (`world_state_dump_<tick>.bin`).
3. **Differential Triage:** Binary diffing of the dumps identifies the exact entity, coordinate offset, or script variable that deviated, allowing developers to isolate non-deterministic code branches or client-side tampering.

# Cardinal Engine Binary Integrity, Anti-Tamper & Deterministic Simulation Research

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Type: Security Research / Advisory](https://img.shields.io/badge/Classification-Defensive%20Binary%20Audit-red.svg)]()
[![Target: Cardinal %2F Relic Engine](https://img.shields.io/badge/Target-Cardinal%20Engine%20x64-informational.svg)]()

## Overview

This repository documents comprehensive binary reverse engineering, security auditing, and anti-tamper mechanics of the **Cardinal Engine** (Age of Empires IV / Relic Entertainment) on Windows x64.

Our research covers client-side code integrity verification, PE section relocation-normalized hashing, Import Address Table (IAT) hook detection, SCAR virtual machine determinism, and Out-of-Sync (OOS) state integrity tracking across more than 4,400 audited engine APIs.

---

## Published Advisories & Technical Papers

### 1. Formal Security Advisories
- **[ADV-2026-002: Integrity Verification Routines and Import Address Table Auditing in High-Performance Game Engines](advisories/ADV-2026-002_anti_tamper_mechanics.md)**  
  *Technical review of engine integrity checkpoints, section protection validations, relocation filtering, and anti-tamper virtualization boundary analysis.*

### 2. Comprehensive Architectural Whitepapers
- **[SCAR Checksum & Out-Of-Sync (OOS) Audit across 4,423 Functions](docs/scar_checksum_oos_audit.md)**  
  *Comprehensive classification of 4,423 engine functions across `wrap_timerule`, `wrap_eventrule`, `sim_command`, `sim_write`, `ai`, and `safe_ui`, identifying checksum-neutral vs desync-inducing execution branches.*
- **[Cardinal Engine Native C++ Bridges & Subsystem Interop (46KB)](docs/native_cpp_bridges.md)**  
  *In-depth architectural analysis of native C++ engine bridges, internal symbol reflection, memory layouts, and data pipelines.*
- **[Cardinal Engine System Architecture & Injection Boundaries (31KB)](docs/cardinal_hook_architecture.md)**  
  *Complete architectural dissection of the Cardinal game process, task graph threading, memory protection, and binary hooking contracts.*
- **[AI Decision Scoring Pipeline & Dynamic Evaluation (45KB)](docs/ai_scoring_pipeline.md)**  
  *Detailed engineering breakdown of real-time utility curves, threat assessment trees, and resource scoring loops.*
- **[AI Session Handoff & State Synchronization (44KB)](docs/ai_session_handoff.md)**  
  *State preservation, thread context handoff, and cross-thread synchronization mechanics.*
- **[AI Unit Control Subsystem & Command Dispatch (33KB)](docs/ai_unit_control.md)**  
  *Unit micro-management architectures, movement pathing models, and simulation command queues.*
- **[Hybrid Native Subsystem & Spatial Model Auditing](docs/hybrid_native_subsystem_audit.md)**  
  *Analysis of spatial simulation models, probe hooks, and synchronization verification.*
- **[AI Control Ownership & Simulation Boundary Verification](docs/ai_control_ownership.md)**  
  *Auditing simulation ownership, commands dispatch, and authoritative control state.*
- **[Relic Cardinal Engine Architecture & Integrity Subsystems](docs/engine_integrity_architecture.md)**  
  *Detailed reverse engineering of `RelicCardinal.exe` (110MB+ x64 PE), relocation-normalized section hashing algorithms (`ComputeNormalizedSectionHash`), runtime IAT boundary validation (`ValidateIATIntegrity`), and hardware breakpoint detection (`GetThreadContext` -> `DR0`-`DR3`/`DR7`).*
- **[Deterministic Simulation, SCAR VM, and Desynchronization Auditing](docs/cardinal_engine_vm_and_desync.md)**  
  *Lockstep simulation tick pipelines, rolling FNV-1a state checksum algorithms, fixed-point math determinism, and Out-of-Sync (OOS) forensic state dumping.*

---

## Tooling & Static Analysis Automation

- **`tools/cardinal_iat_audit.py`**: Automated PE inspection script for auditing IAT integrity, identifying suspicious redirections outside authentic system DLL memory bounds, and locating detour trampolines.

---

## Lead Researcher & Verification

- **Lead Researcher:** Sergey Shunko
- **Field:** Binary Reverse Engineering, Windows Internals, Endpoint Security
- **Target:** Cardinal Engine x64 Native Binaries

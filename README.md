# Cardinal Engine Binary Integrity, Anti-Tamper Architecture & Deterministic Simulation Research

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Type: Security Research / Advisory](https://img.shields.io/badge/Classification-Defensive%20Binary%20Audit-red.svg)]()
[![Target: Cardinal %2F Relic Engine](https://img.shields.io/badge/Target-Cardinal%20Engine%20x64-informational.svg)]()

## Overview

This repository documents defensive binary security research, static disassembly analysis, and architectural auditing of the **Cardinal Engine** (`RelicCardinal.exe` x64) on Windows.

Our research covers relocation-normalized `.text` section hashing, Import Address Table (IAT) boundary validation, dynamic PE unpacking and section reconstruction for static analysis, SCAR virtual machine sandboxing, and deterministic lockstep simulation auditing across **4,423** engine bindings to prevent Out-of-Sync (OOS) state desynchronization.

---

## Published Advisories & Technical Whitepapers

### 1. Security Advisories
- **[ADV-2026-002: Integrity Checkpoints, Relocation Validation, and Anti-Tamper Virtualization in the Cardinal Engine](advisories/ADV-2026-002_anti_tamper_mechanics.md)**  
  *Technical analysis of relocation-masked `.text` checksumming, runtime IAT module-boundary verification, hardware debug register (`DR0`–`DR3`/`DR7`) auditing, and defensive recommendations for hardware-enforced integrity (Intel CET / Windows HVCI).*

### 2. Architectural Whitepapers
- **[Relic Cardinal Engine Architecture & Integrity Subsystems](docs/engine_integrity_architecture.md)**  
  *Detailed reverse engineering of relocation-normalized section hashing (`ComputeNormalizedSectionHash`), runtime IAT boundary validation (`ValidateIATIntegrity`), and hardware breakpoint inspection.*
- **[Deterministic Simulation, SCAR Virtual Machine, and Desynchronization Auditing](docs/cardinal_engine_vm_and_desync.md)**  
  *Lockstep simulation tick pipelines, rolling FNV-1a 64-bit world-state checksum computation (`ComputeSimulationChecksum`), IEEE 754 floating-point determinism hazards, and Out-of-Sync (OOS) forensic state dumping.*
- **[Deterministic State Synchronization & SCAR VM Checksum Boundary Audit (4,423 Functions)](docs/scar_checksum_oos_audit.md)**  
  *Classification of all 4,423 SCAR VM bindings across 14 architectural domains, mapping deterministic checksum serialization surfaces (`LuaRules_SerializeTimeRules` at RVA `0x225BD50`, `TimeRule_Insert` at RVA `0x225DD90`) and UI/Simulation capability separation.*
- **[Dynamic Unpacking, Section Restoration, and PE Reconstruction in the Cardinal Engine](docs/unpacker_and_pe_reconstruction.md)**  
  *Methodology for Original Entry Point (OEP) discovery via `PAGE_GUARD` transitions, Virtual-to-Raw section alignment restoration, and `.idata` Import Descriptor reconstruction for static analysis in IDA Pro.*

---

## Static Analysis Tooling

- **[`tools/cardinal_iat_audit.py`](tools/cardinal_iat_audit.py)** — Python `pefile` utility for auditing Portable Executable (PE) Import Address Tables and verifying import thunk RVA boundaries.

---

## Author & Contact

- **Lead Researcher:** Serhii Shunko
- **Contact:** `cc.simply.spolit@gmail.com`
- **Scope:** Binary Reverse Engineering, Windows x64 Internals, Deterministic Simulation Security

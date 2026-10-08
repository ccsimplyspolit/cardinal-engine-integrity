# Cardinal Engine Binary Integrity, Anti-Tamper & Deterministic Simulation Research

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Type: Security Research / Advisory](https://img.shields.io/badge/Classification-Defensive%20Binary%20Audit-red.svg)]()
[![Target: Cardinal %2F Relic Engine](https://img.shields.io/badge/Target-Cardinal%20Engine%20x64-informational.svg)]()

## Overview

This repository documents comprehensive binary reverse engineering, security auditing, and anti-tamper mechanics of the **Cardinal Engine** (Age of Empires IV / Relic Entertainment) on Windows x64.

Our research covers client-side code integrity verification, PE section relocation-normalized hashing, Import Address Table (IAT) hook detection, SCAR virtual machine determinism, and Out-of-Sync (OOS) state integrity tracking.

---

## Published Advisories & Technical Papers

### 1. Formal Security Advisories
- **[ADV-2026-002: Integrity Verification Routines and Import Address Table Auditing in High-Performance Game Engines](advisories/ADV-2026-002_anti_tamper_mechanics.md)**  
  *Technical review of engine integrity checkpoints, section protection validations, relocation filtering, and anti-tamper virtualization boundary analysis.*

### 2. Comprehensive Architectural Whitepapers
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

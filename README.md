# Cardinal Engine Binary Integrity, Anti-Tamper Architecture & Deterministic Simulation Research

[![CI](https://github.com/ccsimplyspolit/cardinal-engine-integrity/actions/workflows/ci.yml/badge.svg)](https://github.com/ccsimplyspolit/cardinal-engine-integrity/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23640496.svg)](https://doi.org/10.5281/zenodo.23640496)
[![Type: Security Research / Whitepapers](https://img.shields.io/badge/Classification-Defensive%20Binary%20Audit-red.svg)](AUDIT_PREP.md)
[![Target: Cardinal %2F Relic Engine](https://img.shields.io/badge/Target-Cardinal%20Engine%20x64-informational.svg)](AUDIT_PREP.md)

## Overview

This repository documents defensive binary security research, static disassembly analysis, and architectural auditing of the **Cardinal Engine** (`RelicCardinal.exe` x64) on Windows, paired with a zero-dependency PE32+ header, section alignment, and Import Address Table (IAT) boundary auditor (`tools/cardinal_iat_audit.py`).

This research covers relocation-normalized `.text` section hashing, Import Address Table (IAT) boundary validation, dynamic PE unpacking and section reconstruction for static analysis, SCAR virtual machine sandboxing, and deterministic lockstep simulation auditing across **4,423** engine bindings to prevent Out-of-Sync (OOS) state desynchronization.

---

## Architectural Whitepapers (`docs/`)

1. **[Relic Cardinal Engine Architecture & Integrity Subsystems](docs/engine_integrity_architecture.md)**  
   *Detailed reverse engineering of relocation-normalized section hashing (`ComputeNormalizedSectionHash`), runtime IAT boundary validation (`ValidateIATIntegrity`), and hardware breakpoint inspection.*
2. **[Deterministic Simulation, SCAR Virtual Machine, and Desynchronization Auditing](docs/cardinal_engine_vm_and_desync.md)**  
   *Lockstep simulation tick pipelines, rolling FNV-1a 64-bit world-state checksum computation (`ComputeSimulationChecksum`), IEEE 754 floating-point determinism hazards, and Out-of-Sync (OOS) forensic state dumping.*
3. **[Deterministic State Synchronization & SCAR VM Checksum Boundary Audit (4,423 Functions)](docs/scar_checksum_oos_audit.md)**  
   *Classification of all 4,423 SCAR VM bindings across 14 architectural domains, mapping deterministic checksum serialization surfaces (`LuaRules_SerializeTimeRules` at RVA `0x225BD50`, `TimeRule_Insert` at RVA `0x225DD90`) and UI/Simulation capability separation.*
4. **[Dynamic Unpacking, Section Restoration, and PE Reconstruction in the Cardinal Engine](docs/unpacker_and_pe_reconstruction.md)**  
   *Methodology for Original Entry Point (OEP) discovery via `PAGE_GUARD` transitions, Virtual-to-Raw section alignment restoration, and `.idata` Import Descriptor reconstruction for static analysis in IDA Pro.*

---

## Static Analysis Tooling & Audit Package

- **[Audit Preparation & Architecture Package (`AUDIT_PREP.md`)](AUDIT_PREP.md)** — Trail of Bits-style review goals, scope, relocation-normalized integrity diagram, and automated unit test suite (`3/3 PASS`).
- **[`tools/cardinal_iat_audit.py`](tools/cardinal_iat_audit.py)** — Zero-dependency PE32+ header, section alignment, and Import Address Table (IAT) boundary auditor (with optional `pefile` import enumeration).
- **[`test_cardinal_iat_audit.py`](test_cardinal_iat_audit.py)** — Automated unit test suite verifying synthetic PE32+ header/section parsing, CLI execution, and invalid MZ header rejection (`3/3 PASS`).

### Running the Unit Test Suite

```bash
python -m unittest discover -v
```

---

## Author & Contact

- **Lead Researcher:** Serhii Shunko (`@sshunko` / `@ccsimplyspolit`, ORCID [`0009-0002-4183-0361`](https://orcid.org/0009-0002-4183-0361))
- **Contact:** `cc.simply.spolit@gmail.com`
- **Scope:** Binary Reverse Engineering, Windows x64 Internals, Deterministic Simulation Security

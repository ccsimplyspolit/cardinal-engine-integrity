# Cardinal Engine Binary Integrity & Anti-Tamper Architecture Research

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Type: Security Research / Advisory](https://img.shields.io/badge/Classification-Defensive%20Binary%20Audit-red.svg)]()
[![Target: Cardinal / Relic Engine](https://img.shields.io/badge/Target-Cardinal%20Engine%20x64-informational.svg)]()

## Overview

This repository documents binary reverse engineering, security auditing, and anti-tamper mechanics of the **Cardinal Engine** (Age of Empires IV / Relic Entertainment) on Windows x64.

Our research covers the analysis of client-side code integrity, detection of unauthorized process memory modifications, PE section hashing, and the interaction between commercial anti-tamper virtualization layers and native engine execution.

---

## Published Advisories

- **[ADV-2026-002: Integrity Verification Routines and Import Address Table Auditing in High-Performance Game Engines](advisories/ADV-2026-002_anti_tamper_mechanics.md)**  
  *Technical review of engine integrity checkpoints, section protection validations, and anti-tamper virtualization boundary analysis.*

---

## Technical Highlights

- **Static & Dynamic Binary Analysis:** Disassembly and decompilation analysis of large-scale (100MB+) x64 native executables (`RelicCardinal.exe`).
- **Devirtualization & Boundary Analysis:** Mapping execution flow across virtualized anti-tamper stubs to identify runtime entry points.
- **Import Table & Trampoline Detection:** Analysis of engine-level runtime validation routines safeguarding against API hooking.

---

## Repository Structure

```
├── advisories/
│   └── ADV-2026-002_anti_tamper_mechanics.md # Research advisory on engine integrity verification
├── docs/
│   └── engine_integrity_architecture.md     # In-depth architectural analysis of Cardinal engine
├── tools/
│   └── cardinal_iat_audit.py                 # Tool for auditing IAT integrity and hooked exports
├── LICENSE                                   # MIT License
└── SECURITY.md                               # Security policy and contact
```

---

## Lead Researcher

- **Researcher:** Sergey Shunko
- **Field:** Binary Reverse Engineering, Windows Internals, Endpoint Security

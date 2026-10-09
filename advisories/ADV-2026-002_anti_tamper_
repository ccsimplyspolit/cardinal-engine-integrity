# Security Research Advisory: ADV-2026-002

- **Advisory ID:** ADV-2026-002
- **Title:** Integrity Checkpoints, Relocation Validation, and Anti-Tamper Virtualization in the Cardinal Engine
- **Published:** October 2026
- **Researcher:** Sergey Shunko
- **Classification:** Binary Security Analysis / Anti-Tamper Architecture
- **Target:** Cardinal Engine (Relic x64)

---

## Executive Summary

High-budget interactive simulations and strategy games implement multi-tiered client-side defenses combining code virtualization, section checksumming, and runtime thread integrity checks. This research advisory details the defensive architecture utilized by the Cardinal Engine to protect against unauthorized memory patch operations and binary tampering.

---

## Technical Findings & Vulnerability Mitigation

### 1. Relocation-Masked Section Integrity
The engine validates its `.text` segment integrity by comparing dynamic page hashes against compile-time hashes stored in protected metadata.
- **Relocation Normalization:** To prevent ASLR-induced false positives, the integrity scanner zeroes out 8-byte relocation targets based on the binary's `.reloc` table before hashing.
- **Inline Trampoline Detection:** Direct jumps (`E9` jmp) or indirect call trampolines (`FF 25`) injected into standard engine subsystems (such as network synchronization and deterministic simulation ticks) trigger crash-on-anomaly traps.

### 2. Runtime IAT Boundary Verification
The engine actively traverses its Import Address Table (IAT) at runtime to ensure external function pointers have not been redirected to non-system modules. If a pointer points outside legitimate system DLL bounds (`ntdll.dll`, `kernel32.dll`), execution is halted.

### 3. CPU Debug Register Auditing
Worker threads periodically query thread contexts (`GetThreadContext`) to detect hardware execution breakpoints configured in debug registers `DR0` through `DR3` and control register `DR7`.

*(Comprehensive architectural documentation, pseudocode implementations, and disassembly listings are documented in [docs/engine_integrity_architecture.md](../docs/engine_integrity_architecture.md)).*

---

## Defensive Engineering Best Practices

1. **Hardware-Enforced Integrity:** Modern applications should transition from software-based checksum loops to hardware-enforced protection mechanisms like Intel CET (Control-flow Enforcement Technology) and Windows HVCI (Hypervisor-Protected Code Integrity).
2. **Deterministic State Synchronization:** Rather than relying exclusively on client-side obfuscation, deterministic state verification on the host/server remains the most robust defense against client-side state manipulation.


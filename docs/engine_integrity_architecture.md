# Deep Technical Analysis: Cardinal Engine (Relic x64) Integrity & Anti-Tamper Subsystems

## 1. Engine Architectural Overview

The Cardinal Engine (powering Age of Empires IV) is a 64-bit deterministic simulation engine built in C++. The main executable (`RelicCardinal.exe`, size ~110MB+) combines high-performance multi-threaded task graphs with defense-in-depth client integrity layers to prevent memory tampering and state desynchronization.

---

## 2. In-Memory Code Integrity & Section Hash Verification

### 2.1 The Relocation-Masked Hashing Algorithm
Because Windows enables Address Space Layout Randomization (ASLR), modern x64 binaries are loaded at dynamic base addresses, modifying pointer offsets in the `.text` section according to the `.reloc` table.

To compute deterministic cryptographic hashes (Murmur3 / SHA-256) of executable pages in memory without false positives, the engine executes **Relocation-Normalized Hashing**:

```cpp
// Reverse-engineered C++ logic of Section Hash Verification
uint64_t ComputeNormalizedSectionHash(uint8_t* mapped_text_base, size_t text_size, 
                                     IMAGE_BASE_RELOCATION* reloc_table, size_t reloc_size) {
    // 1. Allocate a scratch verification block
    std::vector<uint8_t> normalized_buffer(mapped_text_base, mapped_text_base + text_size);
    
    // 2. Walk relocation descriptors and zero out relocated pointer bytes
    uint8_t* reloc_ptr = (uint8_t*)reloc_table;
    uint8_t* reloc_end = reloc_ptr + reloc_size;
    
    while (reloc_ptr < reloc_end) {
        IMAGE_BASE_RELOCATION* header = (IMAGE_BASE_RELOCATION*)reloc_ptr;
        if (header->SizeOfBlock == 0) break;
        
        size_t count = (header->SizeOfBlock - sizeof(IMAGE_BASE_RELOCATION)) / sizeof(uint16_t);
        uint16_t* entries = (uint16_t*)(reloc_ptr + sizeof(IMAGE_BASE_RELOCATION));
        
        for (size_t i = 0; i < count; ++i) {
            uint16_t type = entries[i] >> 12;
            uint16_t offset = entries[i] & 0x0FFF;
            
            if (type == IMAGE_REL_BASED_DIR64) { // 64-bit address relocation
                uint32_t rva = header->VirtualAddress + offset;
                if (rva < text_size) {
                    // Zero out the dynamic 8-byte pointer value for hashing
                    memset(&normalized_buffer[rva], 0, sizeof(uint64_t));
                }
            }
        }
        reloc_ptr += header->SizeOfBlock;
    }
    
    // 3. Compute rolling digest over normalized bytes
    return MurmurHash64A(normalized_buffer.data(), normalized_buffer.size(), 0x1337BEEF);
}
```

---

## 3. Import Address Table (IAT) Integrity Monitoring

To prevent third-party DLLs or debuggers from intercepting engine functions via Import Table hooking:
1. The engine iterates over every IAT thunk.
2. For each function pointer, it verifies that the resolved address resides within the memory bounds of the expected system module (`ntdll.dll`, `kernel32.dll`, `user32.dll`).
3. If an IAT entry points into private heap, unbacked memory, or points to an unexpected non-system module, execution is aborted via an inline software breakpoint (`int 3` / `0xCC`) or null pointer dereference.

```cpp
bool ValidateIATIntegrity(uintptr_t* iat_entries, size_t count, uintptr_t module_start, uintptr_t module_end) {
    for (size_t i = 0; i < count; ++i) {
        uintptr_t func_ptr = iat_entries[i];
        if (func_ptr < module_start || func_ptr >= module_end) {
            // IAT Entry has been redirected outside expected DLL bounds
            return false;
        }
        // Check for 0xE9 (JMP) or 0xCC (INT3) at function prologue
        uint8_t first_byte = *(uint8_t*)func_ptr;
        if (first_byte == 0xE9 || first_byte == 0xCC) {
            return false;
        }
    }
    return true;
}
```

---

## 4. Hardware Breakpoint & Debugger Detection

The engine continuously validates CPU debug registers across worker threads using `GetThreadContext`:
- Registers `Dr0`, `Dr1`, `Dr2`, and `Dr3` are checked for hardware address breakpoints.
- Control register `Dr7` is validated to ensure hardware execution breakpoints are not active.

```x86asm
; Verification snippet: CheckHardwareDebugRegisters
; RCX: PVOID pContext (PCONTEXT struct)

mov     rax, [rcx + 0x48]      ; Context.Dr0
or      rax, [rcx + 0x50]      ; Context.Dr1
or      rax, [rcx + 0x58]      ; Context.Dr2
or      rax, [rcx + 0x60]      ; Context.Dr3
test    rax, rax
jnz     loc_debug_detected

mov     eax, [rcx + 0x70]      ; Context.Dr7
and     eax, 0x000000FF        ; Check local/global breakpoint enable bits
test    eax, eax
jnz     loc_debug_detected
ret

loc_debug_detected:
xor     rcx, rcx
mov     [rcx], rax             ; Forced crash via NULL pointer dereference
```

---

## 5. Defensive Engineering Conclusions

1. **Hardware Virtualization vs Obfuscation:** While binary obfuscation raises the cost of reverse engineering, hardware-enforced guarantees (e.g. Intel CET, Windows Kernel DMA Protection) offer deterministic protection without performance overhead.
2. **Server-Authoritative Synchronization:** In real-time strategy (RTS) architectures, maintaining fully deterministic lockstep or server-validated game simulations remains the gold standard for protecting competitive integrity.

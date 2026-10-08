# Dynamic Unpacking, Section Restoration, and PE Reconstruction in the Cardinal Engine

**Author:** Sergey Shunko  
**Classification:** Binary Reverse Engineering & Executable Reconstruction  
**Target:** Relic Cardinal Engine (`RelicCardinal.exe` x64)  

---

## 1. Abstract

Commercial anti-tamper and binary protection envelopes wrap high-budget executables in encrypted sections, dynamic unpacking stubs, and virtualized entry gates. To enable thorough static analysis in disassemblers like IDA Pro or Ghidra, researchers must unpack the binary, locate the Original Entry Point (OEP), and reconstruct a valid Portable Executable (PE) image on disk.

This paper documents the technical methodology developed to unpack the 64-bit Cardinal Engine, recover corrupted section headers, rebuild the Import Address Table (IAT), and restore runtime relocations.

---

## 2. Protected PE Section Topology & Unpacking Lifecycle

Prior to unpacking, the on-disk binary exhibits high entropy and scrambled metadata:
- The primary `.text` section is filled with compressed/encrypted bytes or zeros.
- Execution begins at an obfuscated TLS callback or an entry stub located in a custom protection section (e.g., `.bind`, `.vmp`, or `.pdata`).
- During process initialization, the unpacker stub dynamically decrypts native code into process virtual memory, establishes runtime hooks, and eventually transfers control to the Original Entry Point (OEP).

```
+-----------------------------------------------------------------+
|                       Unpacking Stages                          |
+-----------------------------------------------------------------+
| Stage 1: Runtime Loader Initialization & TLS Callbacks          |
| Stage 2: In-Memory Decompression of Text/Rdata Pages            |
| Stage 3: Resolving Dynamic API Thunks & Hook Initialization     |
| Stage 4: Jump to Original Entry Point (OEP)                     |
| Stage 5: In-Memory Snapshot & PE Header Reconstruction          |
+-----------------------------------------------------------------+
```

---

## 3. Locating the Original Entry Point (OEP)

### 3.1 The Page Guard (`PAGE_GUARD`) Technique
Because the runtime unpacker must write to `.text` during decryption and subsequently execute from it, memory page transitions provide a deterministic hook for OEP trapping:

1. Allocate or mark target `.text` pages with `PAGE_NOACCESS` or `PAGE_GUARD`.
2. When the unpacker writes decompressed code to `.text`, intercept the `STATUS_GUARD_PAGE_VIOLATION` exception in a custom debugger or hypervisor harness.
3. Allow write operations to complete.
4. Re-apply `PAGE_GUARD` with read-only permissions.
5. The very first instruction fetch from `.text` triggers an execution exception: **the faulting instruction address (`RIP`) is the Original Entry Point (OEP)**.

### 3.2 Transition Signature
In the Cardinal Engine, the OEP exhibits standard MSVC x64 initialization signatures:
```x86asm
; OEP Routine Signature: __scrt_common_main_seh
sub     rsp, 28h
call    __security_init_cookie
call    sub_140XXXXXX          ; Initialize C runtime (CRT)
```

---

## 4. Reconstructing the PE Image & Section Headers

Once execution pauses at the OEP, the process memory contains fully hydrated code sections. However, a raw memory dump cannot be executed or properly parsed due to memory alignment discrepancies:

### 4.1 Header Fixing: Virtual vs Raw Layout
- **Memory Alignment (`0x1000` / 4KB):** In-memory sections are page-aligned.
- **File Alignment (`0x200` / 512B):** Disk-backed PE sections are aligned to sector boundaries.
- **Section Alignment Translation:** The unpacker tool parses each section header (`IMAGE_SECTION_HEADER`):
  $$\text{PointerToRawData} \leftarrow \text{VirtualAddress}$$
  $$\text{SizeOfRawData} \leftarrow \text{VirtualSize}$$
  This converts the dump into a valid unmapped PE where Virtual Offsets match Raw Offsets.

### 4.2 Import Address Table (IAT) Recovery
Anti-tamper envelopes obscure the standard Import Table by resolving Win32 APIs dynamically via custom hash lookups (`LoadLibrary` + `GetProcAddress`).
1. **IAT Scraper:** Scan engine pointer tables for contiguous arrays of pointers resolving into mapped system DLLs (`kernel32.dll`, `ntdll.dll`, `user32.dll`, `d3d12.dll`).
2. **Export Resolution:** Map each pointer back to its original function name or ordinal by traversing the export directory (`IMAGE_DIRECTORY_ENTRY_EXPORT`) of the host DLL.
3. **Rebuilding Import Descriptors:** Synthesize new `IMAGE_IMPORT_DESCRIPTOR` structures and append a clean `.idata` section to the dumped binary.

---

## 5. Defensive Analysis & Research Outcomes

Reconstructing clean, unpacked binaries of the Cardinal Engine enables:
- **Comprehensive Disassembly:** Allowing IDA Pro to analyze over 4,400 game functions without decompiler errors caused by encrypted bytes.
- **Accurate Call-Graph Analysis:** Identifying inter-subsystem communication between deterministic game simulation and network serialization layers.
- **Deterministic Vulnerability Auditing:** Auditing network packet parsers and SCAR scripting engine boundaries for memory safety defects.

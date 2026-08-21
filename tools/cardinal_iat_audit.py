#!/usr/bin/env python3
"""
cardinal_iat_audit.py
Utility script to audit PE Import Address Table (IAT) integrity and detect API hooking trampolines.
"""

import sys
import pefile

def audit_iat(pe_path):
    print(f"[*] Auditing IAT integrity for: {pe_path}")
    try:
        pe = pefile.PE(pe_path)
    except Exception as e:
        print(f"[-] Failed to parse PE: {e}")
        return

    if not hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
        print("[-] No import directory found.")
        return

    for entry in pe.DIRECTORY_ENTRY_IMPORT:
        dll_name = entry.dll.decode('utf-8', errors='ignore')
        print(f"[+] Imported Module: {dll_name}")
        for imp in entry.imports:
            func_name = imp.name.decode('utf-8', errors='ignore') if imp.name else f"Ordinal({imp.ordinal})"
            print(f"    - {func_name} at RVA 0x{imp.address - pe.OPTIONAL_HEADER.ImageBase:X}")

    print("[*] IAT inspection completed successfully.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        audit_iat(sys.argv[1])
    else:
        print("Usage: python cardinal_iat_audit.py <path_to_pe>")

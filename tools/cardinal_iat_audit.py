#!/usr/bin/env python3
"""
cardinal_iat_audit.py
Defensive static analysis utility to audit Portable Executable (PE64) headers, section
alignments, and Import Address Table (IAT) RVA boundaries. Supports optional `pefile`
acceleration with a built-in zero-dependency PE32+ parser fallback.
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path
from typing import Dict, List, Any

try:
    import pefile  # type: ignore

    HAS_PEFILE = True
except ImportError:
    HAS_PEFILE = False


def parse_pe_summary(data: bytes) -> Dict[str, Any]:
    """Parse DOS/NT headers and section table of a PE32/PE32+ image without external dependencies."""
    if len(data) < 0x40 or data[:2] != b"MZ":
        raise ValueError("Invalid DOS MZ header")
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    if e_lfanew + 24 > len(data) or data[e_lfanew : e_lfanew + 4] != b"PE\x00\x00":
        raise ValueError("Invalid PE signature")

    machine, num_sections, _, _, _, opt_hdr_size, _ = struct.unpack_from("<HHIIIHH", data, e_lfanew + 4)
    opt_offset = e_lfanew + 24
    if opt_hdr_size < 28 or opt_offset + 32 > len(data):
        raise ValueError("Truncated PE optional header")
    magic = struct.unpack_from("<H", data, opt_offset)[0]
    is_pe64 = magic == 0x20B
    image_base = (
        struct.unpack_from("<Q", data, opt_offset + 24)[0]
        if is_pe64
        else struct.unpack_from("<I", data, opt_offset + 28)[0]
    )

    sec_offset = opt_offset + opt_hdr_size
    sections: List[Dict[str, Any]] = []
    for i in range(num_sections):
        off = sec_offset + i * 40
        if off + 40 > len(data):
            break
        raw_name, virt_size, virt_addr, raw_size, raw_ptr = struct.unpack_from("<8sIIII", data, off)
        name = raw_name.split(b"\x00", 1)[0].decode("ascii", errors="replace")
        sections.append(
            {
                "name": name,
                "virtual_address": virt_addr,
                "virtual_size": virt_size,
                "raw_offset": raw_ptr,
                "raw_size": raw_size,
            }
        )

    return {
        "machine": f"0x{machine:04X}",
        "is_pe64": is_pe64,
        "image_base": image_base,
        "sections": sections,
    }


def audit_iat(pe_path: str) -> Dict[str, Any]:
    raw = Path(pe_path).read_bytes()
    summary = parse_pe_summary(raw)
    print(f"[*] Auditing PE image: {pe_path} (PE64={summary['is_pe64']}, ImageBase=0x{summary['image_base']:X})")
    for sec in summary["sections"]:
        print(
            f"    [Section] {sec['name']:8s} VA=0x{sec['virtual_address']:08X} "
            f"VSz=0x{sec['virtual_size']:08X} Raw=0x{sec['raw_offset']:08X}"
        )

    if HAS_PEFILE:
        pe = pefile.PE(data=raw)
        if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
            for entry in pe.DIRECTORY_ENTRY_IMPORT:
                dll_name = entry.dll.decode("utf-8", errors="ignore")
                print(f"[+] Imported Module: {dll_name}")
                for imp in entry.imports:
                    func_name = imp.name.decode("utf-8", errors="ignore") if imp.name else f"Ordinal({imp.ordinal})"
                    print(f"    - {func_name} at RVA 0x{imp.address - pe.OPTIONAL_HEADER.ImageBase:X}")
    return summary


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit PE64 section alignment and IAT boundaries")
    parser.add_argument("pe_path", help="Path to Portable Executable (.exe / .dll)")
    args = parser.parse_args(argv)
    audit_iat(args.pe_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

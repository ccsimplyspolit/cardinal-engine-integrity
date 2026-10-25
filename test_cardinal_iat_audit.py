import io
import struct
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.cardinal_iat_audit import main, parse_pe_summary


def build_minimal_pe64() -> bytes:
    dos = bytearray(0x40)
    dos[0:2] = b"MZ"
    struct.pack_into("<I", dos, 0x3C, 0x40)

    pe_hdr = bytearray(24)
    pe_hdr[0:4] = b"PE\x00\x00"
    struct.pack_into("<HHIIIHH", pe_hdr, 4, 0x8664, 1, 0, 0, 0, 0xF0, 0x0022)

    opt_hdr = bytearray(0xF0)
    struct.pack_into("<H", opt_hdr, 0, 0x020B)  # PE32+
    struct.pack_into("<Q", opt_hdr, 24, 0x140000000)

    sec_hdr = bytearray(40)
    struct.pack_into("<8sIIII", sec_hdr, 0, b".text\x00\x00\x00", 0x1000, 0x1000, 0x200, 0x200)

    return bytes(dos + pe_hdr + opt_hdr + sec_hdr)


class TestCardinalIatAudit(unittest.TestCase):
    def test_parse_minimal_pe64_header_and_sections(self):
        raw = build_minimal_pe64()
        info = parse_pe_summary(raw)
        self.assertTrue(info["is_pe64"])
        self.assertEqual(info["image_base"], 0x140000000)
        self.assertEqual(len(info["sections"]), 1)
        self.assertEqual(info["sections"][0]["name"], ".text")
        self.assertEqual(info["sections"][0]["virtual_address"], 0x1000)

    def test_rejects_invalid_mz_header(self):
        with self.assertRaises(ValueError):
            parse_pe_summary(b"NOT_A_PE")

    def test_cli_execution(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "minimal.exe"
            p.write_bytes(build_minimal_pe64())
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main([str(p)])
            self.assertEqual(rc, 0)
            self.assertIn("ImageBase=0x140000000", buf.getvalue())
            self.assertIn(".text", buf.getvalue())


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Unit tests for shader_dump_check.py (Agent 7, task #22). stdlib only, single process."""
from __future__ import annotations

import os
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shader_dump_check as sdc  # noqa: E402


def container(stage: str, physical: bytes, virtual_size: int = 0x40, bad_marker: bool = False) -> bytes:
    flags = 0x102A1100 | (1 if stage == "vs" else 0)
    hdr = struct.pack(">9I", flags, virtual_size, len(physical), 0, 0x24, 0x30, 0x38, 0, 0)
    virtual = hdr + b"\x11" * (virtual_size - len(hdr))
    marker = b"\xde\xad\xbe\xef" if bad_marker else hdr[8:12]
    return virtual + marker + physical


def write(path: str, data: bytes) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)


LOG = (
    "[2026-11-22 06:00:00.000] [warning] [core] [t1] Native GPU: placement pixel shader 0xAC448F28 backing 0xED23D540 "
    "prefix=0xC77B3ABB6F87ACD9 words=00000000 00000000 00000000 00000000 missing from AOT index\n"
    "[2026-11-22 06:00:00.001] [info] [core] [t1] Native GPU: dumped missing shader 'X\\placement-raw\\ps-C77B3ABB6F87ACD9.bin'\n"
    "[2026-11-22 06:00:00.002] [info] [core] [t1] Native GPU: dumped missing shader 'X\\placement-containers\\ps-0000000000000001.bin'\n"
    "[2026-11-22 06:00:00.003] [warning] [core] [t1] Native GPU: placement vertex shader 0xAC449538 backing 0xED23D3E0 "
    "prefix=0xDCD4AD8441398283 words=F2556004 600A1200 12000000 00006010 missing from AOT index\n"
)


class ShaderDumpCheckTest(unittest.TestCase):
    def make_run(self, tmp: str, ps_physical: bytes, vs_physical: bytes, bad_marker: bool = False) -> str:
        run = os.path.join(tmp, "run")
        dumps = os.path.join(run, "shader-dumps")
        write(os.path.join(dumps, "placement-raw", "ps-C77B3ABB6F87ACD9.bin"), ps_physical[:16])
        write(os.path.join(dumps, "placement-containers", "ps-0000000000000001.bin"),
              container("ps", ps_physical, bad_marker=bad_marker))
        write(os.path.join(dumps, "placement-raw", "vs-DCD4AD8441398283.bin"), vs_physical[:16])
        write(os.path.join(dumps, "placement-containers", "vs-0000000000000002.bin"), container("vs", vs_physical))
        with open(os.path.join(run, "game.log"), "w", encoding="utf-8") as fh:
            fh.write(LOG)
        return run

    def test_parse_container_ok_and_physical(self):
        phys = bytes(range(1, 33))
        c = sdc.parse_container(container("vs", phys), "vs")
        self.assertTrue(c["ok"], c["problems"])
        self.assertEqual(c["physical"], phys)
        self.assertEqual(c["header"]["physical_size"], 32)

    def test_parse_container_problems(self):
        c = sdc.parse_container(container("ps", b"\x00" * 16, bad_marker=True), "ps")
        self.assertFalse(c["ok"])
        self.assertTrue(any("marker" in p for p in c["problems"]))
        c2 = sdc.parse_container(container("vs", b"\x01" * 16), "ps")
        self.assertTrue(any("stage bit" in p for p in c2["problems"]))
        c3 = sdc.parse_container(b"\x00" * 10, "ps")
        self.assertTrue(any("short" in p for p in c3["problems"]))

    def test_report_zero_ps_and_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = self.make_run(tmp, b"\x00" * 32, struct.pack(">8I", 0xF2556004, 0x600A1200, 0x12000000, 0x6010, 1, 2, 3, 4))
            lines, problems = sdc.report(run, os.path.join(run, "shader-dumps"), None)
            text = "\n".join(lines)
            self.assertEqual(problems, 0, text)
            self.assertIn("dumped=2", text)
            self.assertIn("missing_aot=2", text)
            self.assertIn("ps 0xAC448F28 backing 0xED23D540 prefix C77B3ABB6F87ACD9", text)
            self.assertIn("raw ps-C77B3ABB6F87ACD9.bin (16 B, non-zero 0)", text)
            self.assertIn("ps: raw 1 (all-zero 1), containers 1 (physical all-zero 1, non-zero 0)", text)
            self.assertIn("vs: raw 1 (all-zero 0), containers 1 (physical all-zero 0, non-zero 1)", text)
            self.assertIn("raw vs-DCD4AD8441398283.bin: vs-0000000000000002.bin (16 B)", text)

    def test_missing_dumps_fail_and_bin_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = os.path.join(tmp, "run")
            os.makedirs(run)
            bin_dir = os.path.join(tmp, "bin")
            write(os.path.join(bin_dir, "a.bin"), b"abc")
            import hashlib
            with open(os.path.join(bin_dir, "MANIFEST.txt"), "w", encoding="utf-8-sig") as fh:
                fh.write(f"# m\na.bin\t3\t2026-11-22 03:44:58\t{hashlib.sha256(b'abc').hexdigest().upper()}\tsrc\n")
            lines, problems = sdc.report(run, os.path.join(run, "shader-dumps"), bin_dir)
            text = "\n".join(lines)
            self.assertEqual(problems, 1, text)  # no dumps; the bin check passes
            self.assertIn("MISSING", text)
            self.assertIn("bin dir check", text)
            self.assertIn("PASS (0 problem(s))", text)
            write(os.path.join(bin_dir, "written-by-game.log"), b"x")
            lines, problems = sdc.report(run, os.path.join(run, "shader-dumps"), bin_dir)
            self.assertEqual(problems, 2, "\n".join(lines))


if __name__ == "__main__":
    unittest.main(verbosity=1)

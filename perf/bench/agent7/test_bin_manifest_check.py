#!/usr/bin/env python3
"""Unit tests for bin_manifest_check.py (Agent 7, task #22). stdlib only, single process."""
from __future__ import annotations

import hashlib
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bin_manifest_check as bmc  # noqa: E402


def make_bin(tmp: str, files: dict[str, bytes]) -> str:
    rows = ["# test manifest", "# name\tsize\tmtime\tsha256\tsource"]
    for name, data in files.items():
        path = os.path.join(tmp, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(data)
        rows.append(f"{name}\t{len(data)}\t2026-11-22 03:44:58\t{hashlib.sha256(data).hexdigest().upper()}\tsrc\\{name}")
    with open(os.path.join(tmp, "MANIFEST.txt"), "w", encoding="utf-8-sig") as fh:
        fh.write("\n".join(rows) + "\n")
    return tmp


class BinManifestCheckTest(unittest.TestCase):
    FILES = {"legodimensions.exe": b"exe" * 100, "rexruntime.dll": b"dll", "sub\\data.bin": b"\x00\x01"}

    def test_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_bin(tmp, self.FILES)
            lines, problems = bmc.check(tmp, os.path.join(tmp, "MANIFEST.txt"))
        self.assertEqual(problems, 0, lines)
        self.assertEqual(lines[-1], "RESULT: PASS (0 problem(s))")
        self.assertIn("(3 listed files, hash on)", lines[0])

    def test_extra_file_and_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_bin(tmp, self.FILES)
            os.makedirs(os.path.join(tmp, "shader-dumps", "placement-raw"))
            with open(os.path.join(tmp, "game.log"), "w") as fh:
                fh.write("x")
            lines, problems = bmc.check(tmp, os.path.join(tmp, "MANIFEST.txt"))
        text = "\n".join(lines)
        self.assertEqual(problems, 3, text)  # game.log, shader-dumps, shader-dumps\placement-raw
        self.assertIn("FAIL extra file game.log", text)
        self.assertIn("FAIL extra dir  shader-dumps", text)

    def test_changed_and_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_bin(tmp, self.FILES)
            with open(os.path.join(tmp, "rexruntime.dll"), "wb") as fh:
                fh.write(b"DLL")  # same size, different bytes
            os.remove(os.path.join(tmp, "sub", "data.bin"))
            lines, problems = bmc.check(tmp, os.path.join(tmp, "MANIFEST.txt"))
            fast, fast_problems = bmc.check(tmp, os.path.join(tmp, "MANIFEST.txt"), do_hash=False)
        text = "\n".join(lines)
        self.assertEqual(problems, 2, text)
        self.assertIn("FAIL sha256   rexruntime.dll", text)
        self.assertIn("FAIL missing  sub", text)
        self.assertEqual(fast_problems, 1, fast)  # --no-hash misses the same-size change

    def test_no_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            lines, problems = bmc.check(tmp, os.path.join(tmp, "MANIFEST.txt"))
        self.assertEqual(problems, 1)
        self.assertTrue(lines[0].startswith("FAIL no manifest"))


if __name__ == "__main__":
    unittest.main(verbosity=1)

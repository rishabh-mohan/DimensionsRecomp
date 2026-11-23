#!/usr/bin/env python3
"""Unit tests for folded_tree_diff.py (Agent 7, task #13). stdlib only, single process.

  python bench/agent7/test_folded_tree_diff.py
"""
from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import folded_tree_diff as ftd  # noqa: E402

G0 = "sub_82000000 [guest 0x82000000]"
G1 = "sub_82000100 [guest 0x82000100]"
HOOK = "sub_83E46040 [hook of guest 0x83E46040]"
HEADER_TAIL = "path (indent = depth)"


def run(tmp, a_lines, wa, b_lines, wb, *extra):
    pa = os.path.join(tmp, "a.folded")
    pb = os.path.join(tmp, "b.folded")
    for path, lines in ((pa, a_lines), (pb, b_lines)):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = ftd.main([pa, str(wa), pb, str(wb), *extra])
    return rc, buf.getvalue().splitlines()


def row(na, nb, wa, wb, depth, name):
    return f"{ftd.fmt_row(na, nb, wa, wb)}  {'  ' * (depth - 1)}{name}"


def tree_rows(lines):
    """Rows of the tree table: from the header line to the first blank line."""
    start = next(i for i, l in enumerate(lines) if l.endswith(HEADER_TAIL)) + 1
    out = []
    for l in lines[start:]:
        if not l.strip():
            break
        out.append(l)
    return out


def leaf_rows(lines):
    start = next(i for i, l in enumerate(lines) if l.startswith("== leaves under root")) + 2
    return [l for l in lines[start:] if l.strip()]


class FmtRowTest(unittest.TestCase):
    def test_numbers_and_tilde(self):
        # a = 6*0.5 = 3, b = 8*0.25 = 2, d = -1, 2se = 2*sqrt(6*.25 + 8*.0625) = 2.828 -> '~'
        self.assertEqual(ftd.fmt_row(6, 8, 0.5, 0.25), "  3.000   2.000   -1.000~  2.828    6    8")

    def test_significant_has_no_tilde(self):
        s = ftd.fmt_row(0, 100, 1.0, 1.0)  # d = 100, 2se = 20
        self.assertIn("+100.000  20.000", s)
        self.assertNotIn("~", s)


class ParseTest(unittest.TestCase):
    def test_skips_blank_and_malformed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "x.folded")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("a;b 3\n\ngarbage\nx;y notanumber\na;b c;d 2\n")
            self.assertEqual(ftd.parse(p), [(["a", "b"], 3), (["a", "b c", "d"], 2)])


class TreeTest(unittest.TestCase):
    A = ["root;f1;g1 3", "root;f1;g2 1", "root;f2 2", "other 4", "", "garbage"]
    B = ["root;f1;g1 6", "root;f2 2"]

    def test_tree_root_outside_and_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc, lines = run(tmp, self.A, 0.5, self.B, 0.25, "--root", "^root$", "--min", "1",
                            "--labels", "a,b")
        self.assertEqual(rc, 0)
        self.assertTrue(lines[0].startswith("folded_tree_diff: A=a ("))
        self.assertIn("  samples: A total 10 (outside root 4), B total 8 (outside root 0)", lines)
        self.assertIn("  total ms/f: A 5.000, B 2.000; under root: A 3.000, B 2.000", lines)
        self.assertEqual(tree_rows(lines), [
            row(6, 8, 0.5, 0.25, 1, "root"),
            row(4, 6, 0.5, 0.25, 2, "f1"),   # children by A+B count: f1 (10) before f2 (4)
            row(3, 6, 0.5, 0.25, 3, "g1"),
            row(1, 0, 0.5, 0.25, 3, "g2"),
            row(2, 2, 0.5, 0.25, 2, "f2"),
        ])

    def test_min_and_depth(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, by_min = run(tmp, self.A, 0.5, self.B, 0.25, "--root", "^root$", "--min", "2")
            _, by_depth = run(tmp, self.A, 0.5, self.B, 0.25, "--root", "^root$", "--min", "1",
                              "--depth", "2")
        self.assertEqual([r.split()[-1] for r in tree_rows(by_min)], ["root", "f1", "g1", "f2"])
        self.assertEqual([r.split()[-1] for r in tree_rows(by_depth)], ["root", "f1", "f2"])

    def test_default_root_is_outermost(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, lines = run(tmp, self.A, 1.0, self.B, 1.0, "--min", "1", "--depth", "1")
        self.assertIn("  samples: A total 10 (outside root 0), B total 8 (outside root 0)", lines)
        self.assertEqual([r.split()[-1] for r in tree_rows(lines)], ["root", "other"])


class GuestOnlyTest(unittest.TestCase):
    A = [f"xstart;{G0};host_tramp;{G1};memcpy;deeper 5",
         f"xstart;{G0};{G1} 2",
         f"xstart;{G0};{HOOK};fn_inner 1"]
    B = [f"xstart;{G0};host_tramp;{G1};memcpy;deeper 1"]

    def test_trampolines_dropped_boundary_kept(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, lines = run(tmp, self.A, 1.0, self.B, 1.0, "--root", "^xstart$", "--guest-only",
                           "--leaves", "--min", "1")
        text = "\n".join(lines)
        self.assertNotIn("host_tramp", text)  # host frame between guest frames
        self.assertNotIn("deeper", text)      # below the boundary host frame
        self.assertEqual(tree_rows(lines), [
            row(8, 1, 1.0, 1.0, 1, "xstart"),
            row(8, 1, 1.0, 1.0, 2, "sub_82000000"),
            row(7, 1, 1.0, 1.0, 3, "sub_82000100"),
            row(5, 1, 1.0, 1.0, 4, "memcpy"),
            row(1, 0, 1.0, 1.0, 3, "hook:sub_83E46040"),
            row(1, 0, 1.0, 1.0, 4, "fn_inner"),
        ])
        # leaves by |delta|: boundary memcpy (4), guest self (2), host below a hook (1)
        self.assertEqual(leaf_rows(lines), [
            f"{ftd.fmt_row(5, 1, 1.0, 1.0)}  memcpy  <- sub_82000100",
            f"{ftd.fmt_row(2, 0, 1.0, 1.0)}  sub_82000100  (guest self)",
            f"{ftd.fmt_row(1, 0, 1.0, 1.0)}  fn_inner  <- hook:sub_83E46040",
        ])

    def test_short_names(self):
        self.assertEqual(ftd.short(G0), "sub_82000000")
        self.assertEqual(ftd.short(HOOK), "hook:sub_83E46040")
        self.assertEqual(ftd.short("Foo::Bar (near x.cpp:12)"), "Foo::Bar")
        self.assertTrue(ftd.is_guest("__savegprlr_14") and ftd.is_guest("xstart"))
        self.assertFalse(ftd.is_guest("memcpy"))


if __name__ == "__main__":
    unittest.main(verbosity=1)

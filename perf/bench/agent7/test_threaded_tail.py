#!/usr/bin/env python3
"""Tests for threaded_tail.py (stdlib unittest): python bench\\agent7\\test_threaded_tail.py"""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import threaded_tail as tt  # noqa: E402


class PureFunctions(unittest.TestCase):
    def test_rank_ties(self):
        self.assertEqual(tt.rank([3, 1, 3, 2]), [3.5, 1.0, 3.5, 2.0])

    def test_spearman(self):
        self.assertAlmostEqual(tt.spearman([1, 2, 3, 4], [10, 20, 30, 45]), 1.0)
        self.assertAlmostEqual(tt.spearman([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)
        self.assertIsNone(tt.spearman([1, 1, 1, 1], [1, 2, 3, 4]))

    def test_clusters_and_fano(self):
        self.assertEqual(tt.clusters([1, 2, 5, 20, 22], 3), [[1, 2, 5], [20, 22]])
        self.assertAlmostEqual(tt.fano([1, 1, 1, 1]), 0.0)
        self.assertAlmostEqual(tt.fano([0, 4, 0, 4]), 2.0)


class EndToEnd(unittest.TestCase):
    def test_synthetic_run(self):
        # 10 boot rows of 100 ms, then 200 window rows of 10 ms; every 20th window frame is 40 ms and carries
        # frame_slot_wait_ms = 30. pipeline_creations is constant (left out).
        with tempfile.TemporaryDirectory() as d:
            run = os.path.join(d, "0000-n9-r1")
            os.makedirs(run)
            window = [40.0 if i % 20 == 5 else 10.0 for i in range(200)]
            rows = [100.0] * 10 + window
            with open(os.path.join(run, "native-frames.csv"), "w", newline="\n") as f:
                f.write("frame,interval_ms,frame_slot_wait_ms,pipeline_creations\n")
                for k, x in enumerate(rows):
                    f.write("%d,%g,%g,0\n" % (k + 2, x, 30.0 if x == 40.0 else 0.0))
            with open(os.path.join(run, "perf.csv"), "w", newline="\n") as f:
                f.write("frame_time_us,apc_queue_depth\n0,0\n")
                for x in rows:
                    f.write("%d,%d\n" % (int(x * 1000), 1 if x == 40.0 else 0))
            fj = {"source": "native", "window": {"first_row": 11, "rows": 200},
                  "frames": 200, "mean_ms": sum(window) / 200}
            with open(os.path.join(run, "frames.json"), "w") as f:
                json.dump(fj, f)
            with open(os.path.join(run, "summary.txt"), "w") as f:
                f.write("boot     first frame signal at 1.00 s\n"
                        "floor    first-frame signal to the start mark 1.00 s (floor 1 s)\n")
            out = os.path.join(d, "out.txt")
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(tt.main([run, "--bin-s", "1", "-o", out, "--cond", "frame_slot_wait_ms:10",
                                          "--split", "frame_slot_wait_ms", "--cond", "pipeline_creations:1"]), 0)
            with open(out, encoding="utf-8") as f:
                text = f.read()
            self.assertIn("MATCH", text)
            self.assertIn("> 33 ms: 10", text)
            self.assertIn("10 in 10 cluster(s)", text)
            self.assertIn("perf.csv aligned with shift +1", text)
            line = [ln for ln in text.splitlines() if ln.strip().startswith("frame_slot_wait_ms")][0]
            self.assertIn("1.00", line)  # nz_slow and rho
            self.assertIn("pipeline_creations", text.split("constant or missing focus columns:")[1])
            pline = [ln for ln in text.splitlines() if ln.strip().startswith("perf.apc_queue_depth")][0]
            self.assertIn("1.00", pline)
            self.assertIn("cond frame_slot_wait_ms >= 10: 10 frames", text)
            self.assertIn("P(> 33 ms | >=) 1.000 (10), P(> 33 ms | <) 0.0000 (0)", text)
            self.assertIn("cond pipeline_creations: column constant or missing", text)
            self.assertIn("share of the excess 100%", text)


if __name__ == "__main__":
    unittest.main(verbosity=1)

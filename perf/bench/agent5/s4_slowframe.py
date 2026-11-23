#!/usr/bin/env python3
"""S4 helper (Agent 5, task #20): per-frame CPU-side invalidation volume.

Reads the lines that ReportSlowFrame writes to game.log when slow_frame_log_ms
is set (rexglue-sdk src/graphics/d3d12/command_processor.cpp:242-283, called
once per swap at :2193). With slow_frame_log_ms=1 every frame is logged.

'cpu-write invalidations Nx K KB' is frame_stats::kMemoryInvalidate: one count
and the page-rounded requested length (shared_memory.cpp:509) for every
SharedMemory invalidation callback, i.e. every PhysicalHeap::TriggerCallbacks
call that hit at least one GPU-watched page: MmSetAddressProtect ->
PhysicalHeap::Protect (xmemory.cpp:2128-2144), CPU write faults (4 KB each),
file reads, alloc/free. It is a volume, an upper bound for the re-upload. It
cannot tell whether the re-uploaded bytes changed: that is Agent 12's u
diagnostic (bench/agent12/s4_uhash.py).

Elapsed time is the running sum of the logged frame times, so the window is
exact only when every frame was logged (threshold below the shortest frame);
the script reports frame-index gaps. A run dir is read together with its
rotated logs, oldest first: game.N.log ... game.1.log, then game.log. Log files
given explicitly are read in the order given; a frame index that goes backwards
is counted and reported.

Derived (Agent 12, 06:16): KB per invalidation = sum KB / sum count (the lock
size; ~4 KB would mean fault-driven); F_max = mean KB / 256 + mean count (the
most 256 KB write faults per frame C1 could add); Agent 12's test: a mean count
of 5-15 confirms the chain, mean < 1 with p50 0 falsifies it.

usage: python s4_slowframe.py <run dir | log ...> [--from S] [--to S] [--json OUT]
       python s4_slowframe.py --selftest
"""
import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from collections import Counter

LINE = re.compile(
    r"slow frame #(?P<idx>\d+): (?P<ms>[\d.]+) ms \| gpu-thread idle (?P<idle>[\d.]+) \| "
    r"host-gpu wait (?P<wait>[\d.]+) \((?P<waitn>\d+)x\) \|.*?"
    r"cpu-write invalidations (?P<invn>\d+)x (?P<invkb>\d+) KB "
    r"\(on memexport pages (?P<mexn>\d+)x (?P<mexkb>\d+) KB\)")
TEX = re.compile(r"texture load (?P<ms>[\d.]+) \((?P<n>\d+)x\)")
ROT = re.compile(r"game\.(\d+)\.log$")


def pct(values, q):
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * q
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def log_files(path):
    """A log file -> [it]; a run dir -> its game logs, oldest first."""
    if not os.path.isdir(path):
        return [path]
    rot = []
    for name in os.listdir(path):
        m = ROT.match(name)
        if m:
            rot.append((int(m.group(1)), name))
    files = [os.path.join(path, name) for _, name in sorted(rot, reverse=True)]
    base = os.path.join(path, "game.log")
    if os.path.isfile(base):
        files.append(base)
    return files


def parse(paths):
    rows, gaps, back, prev, t = [], 0, 0, None, 0.0
    for path in paths:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = LINE.search(line)
                if not m:
                    continue
                idx = int(m["idx"])
                if prev is not None:
                    if idx > prev + 1:
                        gaps += idx - prev - 1
                    elif idx <= prev:
                        back += 1
                prev = idx
                ms = float(m["ms"])
                t += ms / 1000.0
                tex = TEX.search(line)
                rows.append({"idx": idx, "t": t, "ms": ms, "idle": float(m["idle"]),
                             "invn": int(m["invn"]), "invkb": int(m["invkb"]),
                             "mexn": int(m["mexn"]), "mexkb": int(m["mexkb"]),
                             "texms": float(tex["ms"]) if tex else None,
                             "texn": int(tex["n"]) if tex else None})
    return rows, gaps, back


def dist(values):
    if not values:
        return None
    return {"mean": round(sum(values) / len(values), 2), "p50": round(pct(values, 0.5), 2),
            "p90": round(pct(values, 0.9), 2), "p99": round(pct(values, 0.99), 2),
            "max": round(max(values), 2)}


def summarize(rows, gaps, back, t0, t1):
    win = [r for r in rows if t0 <= r["t"] <= t1]
    out = {"logged_frames": len(rows), "index_gaps": gaps, "index_backsteps": back,
           "elapsed_s": round(rows[-1]["t"], 2) if rows else 0.0,
           "window": [t0, t1], "frames": len(win)}
    if not win:
        return out
    secs = sum(r["ms"] for r in win) / 1000.0
    kb = [r["invkb"] for r in win]
    n = [r["invn"] for r in win]
    out.update({
        "window_s": round(secs, 2),
        "fps": round(len(win) / secs, 2) if secs else None,
        "frame_ms": dist([r["ms"] for r in win]),
        "inval_count_per_frame": dist(n),
        "inval_kb_per_frame": dist(kb),
        "inval_mb_per_s": round(sum(kb) / 1024.0 / secs, 1) if secs else None,
        "frames_with_zero_inval": round(sum(1 for v in n if v == 0) / len(win), 3),
        "memexport_page_kb_per_frame": dist([r["mexkb"] for r in win]),
    })
    sn, skb = sum(n), sum(kb)
    mean_n, mean_kb = sn / len(win), skb / len(win)
    out["inval_kb_per_inval"] = round(skb / sn, 1) if sn else None
    out["f_max_per_frame"] = round(mean_kb / 256.0 + mean_n, 1)
    out["top_kb_values"] = Counter(kb).most_common(8)
    out["top_count_values"] = Counter(n).most_common(6)
    out["texture_load_ms_per_frame"] = dist([r["texms"] for r in win if r["texms"] is not None])
    out["texture_load_count_per_frame"] = dist([r["texn"] for r in win if r["texn"] is not None])
    if mean_n < 1 and pct(n, 0.5) == 0:
        out["agent12_test"] = "falsified: mean < 1 and p50 0"
    elif 5 <= mean_n <= 15:
        out["agent12_test"] = "confirmed: mean %.2f per frame, in 5-15" % mean_n
    else:
        out["agent12_test"] = "not falsified; mean %.2f per frame is outside 5-15" % mean_n
    lo, hi = pct(kb, 0.25), pct(kb, 0.75)
    low = [r["ms"] for r in win if r["invkb"] <= lo]
    high = [r["ms"] for r in win if r["invkb"] >= hi]
    if low and high:
        out["frame_ms_low_vs_high_kb_quartile"] = [round(sum(low) / len(low), 2),
                                                   round(sum(high) / len(high), 2)]
    return out


def selftest():
    def frame(i, ms, invn, invkb, tex):
        return ("[2026-11-22 06:40:00.000] [info] [gpu] [t1] slow frame #%d: %.1f ms | "
                "gpu-thread idle 1.0 | host-gpu wait 0.0 (0x) | shader translate 0.0 (0x) | "
                "pipeline create 0.0 (0x), new 0 | texture load %s | readback 0x 0 KB, "
                "0 stalled | cpu-write invalidations %dx %d KB (on memexport pages 0x 0 KB) | "
                "memexport syncs 0 (0 KB), on demand 0 (0 KB)" % (i, ms, tex, invn, invkb))
    older = [frame(i, 10.0, i, 1024 * i, "1.5 (2x)") for i in range(2, 7)]
    newer = [frame(i, 10.0, i, 1024 * i, "1.5 (2x)") for i in range(7, 12)]
    newer.append("[03:20:00.000] [t4242] [info] slow frame #15: 20.0 ms | gpu-thread idle 2.0 | "
                 "host-gpu wait 0.0 (0x) | texture load 0.0 (0x) | readback 0x 0 KB, 0 stalled | "
                 "cpu-write invalidations 0x 0 KB (on memexport pages 0x 0 KB) | memexport syncs 0 (0 KB)")
    d = tempfile.mkdtemp()
    try:
        for name, lines in (("game.1.log", older), ("game.log", newer)):
            with open(os.path.join(d, name), "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        files = log_files(d)
        assert [os.path.basename(p) for p in files] == ["game.1.log", "game.log"], files
        rows, gaps, back = parse(files)
        s = summarize(rows, gaps, back, 0.0, 1e9)
        _, _, back_wrong = parse(list(reversed(files)))
    finally:
        shutil.rmtree(d)
    assert len(rows) == 11 and gaps == 3 and back == 0, (len(rows), gaps, back)
    assert back_wrong == 1, back_wrong
    assert abs(s["window_s"] - 0.12) < 1e-9, s["window_s"]
    assert s["inval_count_per_frame"]["max"] == 11
    assert s["inval_kb_per_frame"]["p50"] == 6144.0, s["inval_kb_per_frame"]
    assert abs(s["inval_mb_per_s"] - (sum(range(2, 12)) / 0.12)) < 0.1, s["inval_mb_per_s"]
    assert s["frames_with_zero_inval"] == round(1 / 11, 3)
    assert s["inval_kb_per_inval"] == 1024.0, s["inval_kb_per_inval"]
    assert abs(s["f_max_per_frame"] - 29.5) < 0.06, s["f_max_per_frame"]
    assert s["texture_load_count_per_frame"]["max"] == 2, s["texture_load_count_per_frame"]
    assert s["agent12_test"].startswith("confirmed"), s["agent12_test"]
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="*", help="run dir (rotated logs included) or log files, oldest first")
    ap.add_argument("--from", dest="t0", type=float, default=70.0,
                    help="window start, s after the first logged frame (a-prof: 70)")
    ap.add_argument("--to", dest="t1", type=float, default=220.0,
                    help="window end, s after the first logged frame (a-prof: 220)")
    ap.add_argument("--json")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.paths:
        ap.error("path required")
    files = []
    for p in a.paths:
        files += log_files(p)
    missing = [p for p in files if not os.path.isfile(p)]
    if not files or missing:
        print("no log file: %s" % (missing or a.paths), file=sys.stderr)
        return 1
    rows, gaps, back = parse(files)
    s = summarize(rows, gaps, back, a.t0, a.t1)
    s["log"] = files[-1]
    s["logs"] = files
    print(json.dumps(s, indent=1))
    if not rows:
        print("no 'slow frame #' lines: was slow_frame_log_ms set?", file=sys.stderr)
        return 1
    if gaps:
        print("warning: %d frames not logged; elapsed time undercounts" % gaps, file=sys.stderr)
    if back:
        print("warning: the frame index went backwards %d times: check the log order" % back,
              file=sys.stderr)
    if a.json:
        with open(a.json, "w", encoding="utf-8", newline="\n") as f:
            json.dump(s, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())

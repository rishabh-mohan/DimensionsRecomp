"""Per-frame CPU cost of each game-thread role in Agent 8's matrix run dirs (Agent 7, task #6, session 3).

Usage:
  python bench\\agent7\\w3_thread_per_frame.py --runs build\\agent8\\matrix\\20261122-0013\\runs
  python bench\\agent7\\w3_thread_per_frame.py <run dir> [<run dir> ...] [--diff n0:d0 ...]

Reads <run>\\threads.csv from bench/agent8/run/drivers/thread-cpu.ps1, where busy_pct = thread CPU s /
driver window s x 100 (100 = one core). It also reads <run>\\frames.json and reports
ms/frame = busy_pct / 100 x 1000 / fps.
fps is window.rows_by_end_bytes / window.end_bytes_window_s: the frames over the whole measure window,
which is the window the driver covers (it starts 1-3 s late and ends at the same mark). frames.json
mean_fps covers only the first 50 s of that window, so it is used only as a fallback.
Roles:
  main      "Main XThread"
  gpu_cmd   "GPU Commands"
  vsync     "GPU VSync"
  timerq    "TimerQueue"
  audio     names containing Audio or XMA
  render    the busiest other "XThread" (in native it logs the draws and presents)
  worker2   the next busiest XThread
  xt_other  the remaining XThreads
  other     everything else (unnamed threads, 0x... threads)
Run dirs without threads.csv are skipped (the cold runs).
Stdlib only, one thread.
"""
import argparse
import csv
import json
import os
import re
import statistics
import sys

ROLES = ("main", "render", "gpu_cmd", "timerq", "worker2", "vsync", "audio", "xt_other", "other")


def arm_of(run_dir):
    name = os.path.basename(os.path.normpath(run_dir))
    name = re.sub(r"^\d{4}-", "", name)
    return re.sub(r"([-_]r?\d+)$", "", name)


def fps_of(run_dir):
    with open(os.path.join(run_dir, "frames.json"), encoding="utf-8-sig") as f:
        fj = json.load(f)
    w = fj.get("window") or {}
    rows, secs = w.get("rows_by_end_bytes"), w.get("end_bytes_window_s")
    if rows and secs:
        return rows / secs, "measure", fj.get("mean_fps")
    return fj.get("mean_fps"), "mean_fps", fj.get("mean_fps")


def classify(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    busy = dict.fromkeys(ROLES, 0.0)
    names = {}
    xthreads = []
    for r in rows:
        name = (r.get("name") or "").strip()
        try:
            b = float(r.get("busy_pct") or 0)
        except ValueError:
            continue
        if "Main XThread" in name:
            role = "main"
        elif "GPU Commands" in name:
            role = "gpu_cmd"
        elif "GPU VSync" in name:
            role = "vsync"
        elif "TimerQueue" in name:
            role = "timerq"
        elif re.search(r"audio|xma", name, re.I):
            role = "audio"
        elif name.startswith("XThread"):
            xthreads.append((b, name))
            continue
        else:
            role = "other"
        busy[role] += b
        names.setdefault(role, name)
    xthreads.sort(key=lambda x: -x[0])
    for i, (b, name) in enumerate(xthreads):
        role = "render" if i == 0 else "worker2" if i == 1 else "xt_other"
        busy[role] += b
        names.setdefault(role, name)
    return busy, names


def handle(name):
    m = re.search(r"\((F[0-9A-F]{7})\)", name or "")
    return m.group(1) if m else (name or "-")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("run_dirs", nargs="*")
    ap.add_argument("--runs", help="a matrix runs dir: every sub-dir with threads.csv")
    ap.add_argument("--diff", action="append", default=None,
                    help="B:A arm pair to print B - A medians (default n0:d0 and n0:base when present)")
    a = ap.parse_args()
    dirs = list(a.run_dirs)
    if a.runs:
        dirs += [os.path.join(a.runs, d) for d in sorted(os.listdir(a.runs))]
    dirs = [d for d in dirs if os.path.exists(os.path.join(d, "threads.csv"))]
    if not dirs:
        print("no run dirs with threads.csv", file=sys.stderr)
        return 2
    print("ms of CPU per frame by thread role (busy_pct x 10 / fps; fps over the measure window)")
    hdr = "%-14s %-5s %7s " % ("run", "arm", "fps") + " ".join("%8s" % r for r in ROLES) + " %7s  %s" % (
        "total", "main% render% | render handle")
    print(hdr)
    by_arm = {}
    for d in dirs:
        fps, src, mean_fps = fps_of(d)
        busy, names = classify(os.path.join(d, "threads.csv"))
        ms = {r: busy[r] * 10.0 / fps for r in ROLES}
        ms["total"] = sum(ms[r] for r in ROLES)
        run = os.path.basename(os.path.normpath(d))
        arm = arm_of(d)
        print("%-14s %-5s %7.2f " % (run[:14], arm, fps) + " ".join("%8.3f" % ms[r] for r in ROLES)
              + " %7.3f  %5.1f %6.1f | %s%s" % (ms["total"], busy["main"], busy["render"],
                                               handle(names.get("render")),
                                               "" if src == "measure" else " (fps=%s)" % src))
        by_arm.setdefault(arm, []).append((fps, ms, busy))
    print("\nper-arm medians:")
    med = {}
    for arm, items in by_arm.items():
        m = {r: statistics.median(x[1][r] for x in items) for r in ROLES + ("total",)}
        m["fps"] = statistics.median(x[0] for x in items)
        m["main%"] = statistics.median(x[2]["main"] for x in items)
        m["render%"] = statistics.median(x[2]["render"] for x in items)
        med[arm] = m
        print("%-14s %-5s %7.2f " % ("median n=%d" % len(items), arm, m["fps"])
              + " ".join("%8.3f" % m[r] for r in ROLES) + " %7.3f  %5.1f %6.1f" % (
                  m["total"], m["main%"], m["render%"]))
    pairs = a.diff if a.diff else ["n0:d0", "n0:base"]
    for p in pairs:
        b, _, base = p.partition(":")
        if b in med and base in med:
            print("%-14s %-5s %7.2f " % ("diff", b + "-" + base, med[b]["fps"] - med[base]["fps"])
                  + " ".join("%+8.3f" % (med[b][r] - med[base][r]) for r in ROLES)
                  + " %+7.3f" % (med[b]["total"] - med[base]["total"]))
    print("\nNote: busy_pct is over the driver window (measure start + 1-3 s to measure end); fps is over the"
          " runner's measure window from frames.json, so the two windows differ by the driver's late start.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

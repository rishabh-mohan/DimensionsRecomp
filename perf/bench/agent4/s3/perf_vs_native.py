#!/usr/bin/env python3
"""Agent 4 S3: does perf.csv frame_time_us match native-frames.csv interval_ms on native runs?

For each run dir: take the scored window from frames.json (native-frames rows
first_row .. first_row+rows), find the perf.csv row offset that lines the two
per-frame series up (search +-2000 rows on the first 400 window frames), then
compare window stats from both sources. Reads only; prints a table, optional --json.

Usage: python bench/agent4/s3/perf_vs_native.py RUNDIR [RUNDIR ...] [--json OUT]
"""
import argparse
import csv
import json
import math
import os
import statistics
import sys


def column(path, name):
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader)
        i = header.index(name)
        out = []
        for row in reader:
            try:
                out.append(float(row[i]))
            except (IndexError, ValueError):
                out.append(float("nan"))
    return out


def stats(ms):
    s = sorted(ms)
    n = len(s)
    rank = lambda p: s[max(0, math.ceil(p * n) - 1)]
    total = sum(ms)
    return {"frames": n, "seconds": round(total / 1000.0, 3), "mean_fps": round(n / (total / 1000.0), 3),
            "mean_ms": round(total / n, 4), "median_ms": round(rank(0.5), 4), "p99_ms": round(rank(0.99), 4),
            "max_ms": round(s[-1], 4), "over33": sum(1 for x in ms if x > 33.0)}


def one(run):
    fj = json.load(open(os.path.join(run, "frames.json"), encoding="utf-8-sig"))
    if fj.get("source") != "native":
        return {"run": run, "error": f"frames.json source={fj.get('source')}"}
    first, rows = fj["window"]["first_row"], fj["window"]["rows"]
    nat = column(os.path.join(run, "native-frames.csv"), "interval_ms")
    draws = column(os.path.join(run, "native-frames.csv"), "draw_calls")
    perf = [x / 1000.0 for x in column(os.path.join(run, "perf.csv"), "frame_time_us")]
    nwin = nat[first:first + rows]
    probe = nwin[:400]
    best = None
    for k in range(-2000, 2001):
        lo = first + k
        if lo < 0 or lo + len(probe) > len(perf):
            continue
        err = sum(abs(perf[lo + i] - probe[i]) for i in range(len(probe)))
        if best is None or err < best[1]:
            best = (k, err)
    k = best[0]
    pwin = perf[first + k:first + k + rows]
    short = len(pwin) < rows
    m = min(len(pwin), len(nwin))
    diffs = [abs(pwin[i] - nwin[i]) for i in range(m)]
    sn, sp = stats(nwin), stats(pwin)
    return {"run": run, "native_first_row": first, "rows": rows, "perf_offset_rows": k,
            "perf_short": short, "probe_mean_abs_diff_ms": round(best[1] / len(probe), 5),
            "max_abs_diff_ms": round(max(diffs), 4), "frames_diff_gt_0p05ms": sum(1 for d in diffs if d > 0.05),
            "native": sn, "perf": sp,
            "mean_fps_delta_pct": round(100.0 * (sp["mean_fps"] - sn["mean_fps"]) / sn["mean_fps"], 4),
            "median_draw_calls": statistics.median(draws[first:first + rows])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--json")
    a = ap.parse_args()
    out = [one(r) for r in a.runs]
    print(f"{'run':<16} {'off':>5} {'maxdiff':>8} {'>.05':>5} {'fps nat':>9} {'fps perf':>9} {'d%':>8} "
          f"{'med nat':>8} {'med perf':>8} {'p99 nat':>8} {'p99 perf':>8} {'draws':>6}")
    for r in out:
        if "error" in r:
            print(f"{os.path.basename(r['run']):<16} {r['error']}")
            continue
        n, p = r["native"], r["perf"]
        print(f"{os.path.basename(r['run']):<16} {r['perf_offset_rows']:>5} {r['max_abs_diff_ms']:>8} "
              f"{r['frames_diff_gt_0p05ms']:>5} {n['mean_fps']:>9} {p['mean_fps']:>9} {r['mean_fps_delta_pct']:>8} "
              f"{n['median_ms']:>8} {p['median_ms']:>8} {n['p99_ms']:>8} {p['p99_ms']:>8} {r['median_draw_calls']:>6}")
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        json.dump(out, open(a.json, "w", encoding="utf-8"), indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())

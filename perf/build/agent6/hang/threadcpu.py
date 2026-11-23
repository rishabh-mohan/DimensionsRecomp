"""threadcpu.py - per-thread CPU (kernel vs user) from a run's threads*.csv; read-only, stdlib only.

usage: python -B threadcpu.py <run_dir> [<run_dir> ...] [--focus REGEX] [--from HH:MM:SS] [--to HH:MM:SS] [--top N]

threads*.csv columns: t_s,epoch_s,tid,name,cpu_ms,kernel_ms,user_ms,cycles (cumulative per thread; checked).
For each run: whole-run per-thread totals (top N by cpu), the focus threads' 2-s interval table inside
[--from, --to] (local time), and the top threads by CPU inside that window.
"""
import argparse
import csv
import glob
import os
import re
import statistics
import time


def load(run):
    files = sorted(glob.glob(os.path.join(run, "threads*.csv")))
    if not files:
        return None, None
    rows = {}
    names = {}
    with open(files[0], newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                tid = int(r["tid"])
                ep = float(r["epoch_s"])
                k = float(r["kernel_ms"])
                u = float(r["user_ms"])
            except (ValueError, KeyError, TypeError):
                continue
            if r.get("name"):
                names[tid] = r["name"]
            rows.setdefault(tid, []).append((ep, k, u))
    for v in rows.values():
        v.sort()
    return files[0], (rows, names)


def hms(ep):
    return time.strftime("%H:%M:%S", time.localtime(ep)) + f".{int((ep % 1) * 1000):03d}"


def to_epoch(day_ep, s):
    if not s:
        return None
    lt = time.localtime(day_ep)
    hh, mm, ss = (s.split(":") + ["0", "0"])[:3]
    return time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, int(hh), int(mm), 0, 0, 0, -1)) + float(ss)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--focus", default=r"GPU Commands|Main XThread|F80001A8")
    ap.add_argument("--from", dest="t0", default=None)
    ap.add_argument("--to", dest="t1", default=None)
    ap.add_argument("--top", type=int, default=8)
    a = ap.parse_args()
    fre = re.compile(a.focus)
    for run in a.runs:
        path, data = load(run)
        print("=" * 100)
        print(f"run {run}")
        if not data:
            print("  no threads*.csv")
            continue
        rows, names = data
        print(f"  file {os.path.basename(path)}  threads={len(rows)}")
        mono_bad = sum(1 for v in rows.values() for i in range(1, len(v)) if v[i][1] + 1e-6 < v[i - 1][1] or v[i][2] + 1e-6 < v[i - 1][2])
        print(f"  cumulative check: {mono_bad} decreasing samples")
        first = min(v[0][0] for v in rows.values())
        last = max(v[-1][0] for v in rows.values())
        print(f"  samples {hms(first)} .. {hms(last)}  ({last - first:.0f} s)")
        tot = []
        for tid, v in rows.items():
            k = v[-1][1] - v[0][1]
            u = v[-1][2] - v[0][2]
            tot.append((k + u, tid, k, u))
        tot.sort(reverse=True)
        print(f"  whole-run top {a.top} threads by CPU (delta first..last sample):")
        for c, tid, k, u in tot[: a.top]:
            print(f"    tid {tid:6d} {names.get(tid, ''):28.28s} cpu {c / 1000:8.1f}s  kernel {k / 1000:8.1f}s  user {u / 1000:7.1f}s  k%={100 * k / c if c else 0:5.1f}")
        focus = [tid for tid in rows if fre.search(names.get(tid, ""))]
        # per-interval stats for focus threads (whole run)
        for tid in focus:
            v = rows[tid]
            ks, us = [], []
            for i in range(1, len(v)):
                dt = v[i][0] - v[i - 1][0]
                if dt <= 0:
                    continue
                ks.append((v[i][1] - v[i - 1][1]) / (dt * 1000) * 100)
                us.append((v[i][2] - v[i - 1][2]) / (dt * 1000) * 100)
            if ks:
                print(f"  focus tid {tid} {names.get(tid, '')}: per-interval kernel% median {statistics.median(ks):5.1f} p90 {sorted(ks)[int(0.9 * (len(ks) - 1))]:5.1f} max {max(ks):5.1f} | user% median {statistics.median(us):5.1f} p90 {sorted(us)[int(0.9 * (len(us) - 1))]:5.1f} max {max(us):5.1f}  (n={len(ks)})")
        t0 = to_epoch(first, a.t0)
        t1 = to_epoch(first, a.t1)
        if t0 is None or t1 is None:
            continue
        print(f"  window {a.t0} .. {a.t1} (local)")
        for tid in focus:
            v = rows[tid]
            print(f"    tid {tid} {names.get(tid, '')}: interval end | dt s | kernel ms | user ms | kernel% | user%")
            for i in range(1, len(v)):
                if v[i][0] < t0 or v[i - 1][0] > t1:
                    continue
                dt = v[i][0] - v[i - 1][0]
                dk = v[i][1] - v[i - 1][1]
                du = v[i][2] - v[i - 1][2]
                print(f"      {hms(v[i][0])} | {dt:5.2f} | {dk:8.1f} | {du:7.1f} | {100 * dk / (dt * 1000) if dt > 0 else 0:6.1f} | {100 * du / (dt * 1000) if dt > 0 else 0:6.1f}")
        win = []
        for tid, v in rows.items():
            inside = [s for s in v if t0 <= s[0] <= t1]
            before = [s for s in v if s[0] < t0]
            if not inside or not before:
                continue
            a0 = before[-1]
            a1 = inside[-1]
            win.append(((a1[1] - a0[1]) + (a1[2] - a0[2]), tid, a1[1] - a0[1], a1[2] - a0[2], a1[0] - a0[0]))
        win.sort(reverse=True)
        print(f"  top {a.top} threads by CPU in the window:")
        for c, tid, k, u, dt in win[: a.top]:
            print(f"    tid {tid:6d} {names.get(tid, ''):28.28s} span {dt:5.1f}s cpu {c / 1000:6.2f}s kernel {k / 1000:6.2f}s user {u / 1000:6.2f}s")


if __name__ == "__main__":
    main()

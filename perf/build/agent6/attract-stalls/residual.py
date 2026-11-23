#!/usr/bin/env python3
"""Agent 6, task #18: what would a warm pipeline storage leave behind?

Single-threaded, read-only. For each run dir, classify every perf.csv frame
(row 0 is skipped) by what lies within +-2 rows of it:
  A  pipeline miss within +-2 rows        -> removed by warm shader storage (if pre-created)
  B  no pm, texture miss within +-2 rows  -> not persisted (texture cache is per launch)
  C  neither, draws >= 5000               -> draw throughput (heavy shots)
  D  neither, fewer draws                 -> other
excess = max(0, frame_ms - median of the 30 frames before).
Texture cost inside A is bounded with B's excess per texture miss.

usage: python residual.py <run dir> [...]
"""
import csv, os, statistics, sys

W = 2
HEAVY = 5000


def load(d):
    rows = []
    with open(os.path.join(d, "perf.csv"), newline="") as f:
        for r in csv.DictReader(f):
            try:
                rows.append((int(r["frame_time_us"]) / 1000.0, int(r["pipeline_cache_misses"]),
                             int(r["texture_cache_misses"]), int(r["draw_calls"])))
            except (KeyError, ValueError, TypeError):
                break
    return rows


def main(dirs):
    for d in dirs:
        rows = load(d)
        ft = [r[0] for r in rows]
        pm = [r[1] for r in rows]
        tm = [r[2] for r in rows]
        dr = [r[3] for r in rows]
        n = len(rows)
        cats = {k: {"n": 0, "gt100": 0, "gt250": 0, "sum250_s": 0.0, "exc_s": 0.0, "max_ms": 0.0,
                    "pm": 0, "tm": 0} for k in "ABCD"}
        for i in range(1, n):
            lo, hi = max(1, i - W), min(n, i + W + 1)
            near_pm = any(pm[j] > 0 for j in range(lo, hi))
            near_tm = any(tm[j] > 0 for j in range(lo, hi))
            k = "A" if near_pm else "B" if near_tm else "C" if dr[i] >= HEAVY else "D"
            base = statistics.median(ft[max(1, i - 30):i]) if i > 1 else 16.7
            c = cats[k]
            c["n"] += 1
            c["gt100"] += ft[i] > 100
            if ft[i] > 250:
                c["gt250"] += 1
                c["sum250_s"] += ft[i] / 1000.0
            c["exc_s"] += max(0.0, ft[i] - base) / 1000.0
            c["max_ms"] = max(c["max_ms"], ft[i])
            c["pm"] += pm[i]
            c["tm"] += tm[i]
        name = os.path.basename(os.path.normpath(d))
        print(f"=== {name}  rows={n}  pm={sum(pm)} tm={sum(tm)}")
        print(f"  {'cat':<4}{'frames':>7}{'>100':>6}{'>250':>6}{'sum>250_s':>10}{'excess_s':>10}{'max_ms':>8}{'pm':>5}{'tm':>5}")
        for k, c in cats.items():
            print(f"  {k:<4}{c['n']:>7}{c['gt100']:>6}{c['gt250']:>6}{c['sum250_s']:>10.2f}{c['exc_s']:>10.2f}"
                  f"{c['max_ms']:>8.0f}{c['pm']:>5}{c['tm']:>5}")
        b = cats["B"]
        per_tm = (b["exc_s"] / b["tm"]) if b["tm"] else 0.0
        a = cats["A"]
        tex_in_a = per_tm * a["tm"]
        resid = cats["B"]["exc_s"] + cats["C"]["exc_s"] + cats["D"]["exc_s"]
        print(f"  texture-only cost {per_tm * 1000:.1f} ms per tm (B); A holds {a['tm']} tm -> ~{tex_in_a:.2f} s of A")
        print(f"  warm-storage removable ~{a['exc_s'] - tex_in_a:.2f} s of {a['exc_s']:.2f} s excess in A; "
              f"left: B+C+D {resid:.2f} s + texture share of A {tex_in_a:.2f} s")


if __name__ == "__main__":
    main(sys.argv[1:] or ["build/agent3/runs/20261122-031756-bgate-long-devoff2",
                          "build/agent3/runs/20261122-032150-bgate-long-devoffB"])

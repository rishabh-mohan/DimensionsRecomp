#!/usr/bin/env python3
"""Agent 6, task #18: directional attribution of >250 ms frames + benchmark window stats.

Single-threaded, read-only. perf.csv row k = host time from XE_SWAP k-1 entry to XE_SWAP k
entry on the GPU thread; its counters cover the same span (Profiler::Flip at swap entry).
Per the SDK (pipeline_cache.cpp:795-813, d3d12/command_processor.cpp:2726-2729, 4236):
  - misses counted in row k come from frame k's draws;
  - sync creation (no pixel shader, or a mid-frame EndSubmission) costs row k;
  - async creation is awaited in IssueSwap(k) -> costs row k+1.
Classes for a frame > THRESH ms:
  P0    pm > 0 on the row
  P1    pm on row k-1 only (async wait at the previous swap)
  PRE   pm on k+1/k+2 only (stall precedes the misses: NOT explained by compile)
  P2    pm on k-2 only (not explained by the wait mechanism)
  heavy draws >= 5000, no pm in k-2..k+2
  none  anything else
Window: frames whose start lies in [H0+a, H0+a+w] (H0 = first 2823/366575 row).

usage: python attrib.py [--thresh 250] [--win 5.5 15] <run dir> [...]
"""
import argparse, csv, os, statistics

COLS = ["frame_time_us", "draw_calls", "vertices_processed", "pipeline_cache_misses",
        "texture_cache_misses", "command_buffer_stalls", "pipeline_cache_hits",
        "functions_dispatched", "interrupt_dispatches", "xma_frames_decoded", "active_threads"]


def load(d):
    rows = []
    with open(os.path.join(d, "perf.csv"), newline="") as f:
        for r in csv.DictReader(f):
            try:
                rows.append({c: int(r[c]) for c in COLS})
            except (KeyError, ValueError, TypeError):
                break
    return rows


def pct(xs, p):
    xs = sorted(xs)
    if not xs:
        return 0.0
    k = (len(xs) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--thresh", type=float, default=250.0)
    ap.add_argument("--win", type=float, nargs=2, default=[5.5, 15.0])
    ap.add_argument("dirs", nargs="*", default=["build/agent3/runs/20261122-031756-bgate-long-devoff2",
                                                 "build/agent3/runs/20261122-032150-bgate-long-devoffB"])
    a = ap.parse_args()
    for d in a.dirs:
        rows = load(d)
        n = len(rows)
        ms = [r["frame_time_us"] / 1000.0 for r in rows]
        pm = [r["pipeline_cache_misses"] for r in rows]
        start = [0.0] * n  # start time (s) of row k = sum of the rows before it
        for k in range(1, n):
            start[k] = start[k - 1] + ms[k - 1] / 1000.0
        rel = lambda k: start[k] - start[h0]  # H0+s, same convention as analyze_stalls.py (row starts)
        h0 = next(k for k in range(n) if rows[k]["draw_calls"] == 2823 and rows[k]["vertices_processed"] == 366575)
        name = os.path.basename(os.path.normpath(d))
        print(f"=== {name}  H0 row {h0 + 1} (1-based, as in report-250ms.txt)")
        cls_sum = {}
        print(f"  {'row':>5} {'H0+s':>7} {'ms':>6} {'cls':>5} {'draws':>6} {'pm':>3} {'tm':>3} {'cb':>4}  pm[k-2..k+2]   fdisp/ms idisp/ms")
        for k in range(1, n):
            if ms[k] <= a.thresh:
                continue
            g = lambda j: pm[j] if 0 < j < n else 0
            if pm[k] > 0:
                c = "P0"
            elif g(k - 1) > 0:
                c = "P1"
            elif g(k + 1) > 0 or g(k + 2) > 0:
                c = "PRE"
            elif g(k - 2) > 0:
                c = "P2"
            elif rows[k]["draw_calls"] >= 5000:
                c = "heavy"
            else:
                c = "none"
            s = cls_sum.setdefault(c, [0, 0.0])
            s[0] += 1
            s[1] += ms[k] / 1000.0
            r = rows[k]
            print(f"  {k + 1:>5} {rel(k):>7.2f} {ms[k]:>6.0f} {c:>5} {r['draw_calls']:>6} "
                  f"{pm[k]:>3} {r['texture_cache_misses']:>3} {r['command_buffer_stalls']:>4}  "
                  f"{[g(j) for j in range(k - 2, k + 3)]!s:<14} {r['functions_dispatched'] / ms[k]:>7.2f} {r['interrupt_dispatches'] / ms[k]:>7.2f}")
        tot = sum(v[1] for v in cls_sum.values())
        print("  by class: " + ", ".join(f"{c} {v[0]} fr {v[1]:.2f} s ({100 * v[1] / tot:.0f}%)" for c, v in sorted(cls_sum.items())))
        # typical guest-side rates for normal frames (for comparison)
        norm = [k for k in range(1, n) if 10 < ms[k] < 40]
        print(f"  normal frames: fdisp/ms med {statistics.median(rows[k]['functions_dispatched'] / ms[k] for k in norm):.2f}, "
              f"idisp/ms med {statistics.median(rows[k]['interrupt_dispatches'] / ms[k] for k in norm):.2f}")
        # benchmark window: rows whose start lies in [H0+w0, H0+w1]
        w0, w1 = a.win[0], a.win[0] + a.win[1]
        ks = [k for k in range(1, n) if w0 <= rel(k) <= w1]
        if ks:
            wm = [ms[k] for k in ks]
            print(f"  window H0+{w0:g}..H0+{w1:g} s: rows {ks[0] + 1}-{ks[-1] + 1}, {len(ks)} frames, {sum(wm) / 1000:.2f} s, "
                  f"med {statistics.median(wm):.1f} p95 {pct(wm, .95):.1f} p99 {pct(wm, .99):.1f} max {max(wm):.0f} ms, "
                  f">50ms {sum(x > 50 for x in wm)}, >100ms {sum(x > 100 for x in wm)}, >250ms {sum(x > 250 for x in wm)}, "
                  f"pm {sum(pm[k] for k in ks)}, tm {sum(rows[k]['texture_cache_misses'] for k in ks)}, "
                  f"max draws {max(rows[k]['draw_calls'] for k in ks)}")
            top = sorted(ks, key=lambda k: -ms[k])[:6]
            print("    top: " + "; ".join(f"r{k + 1} +{rel(k):.2f}s {ms[k]:.0f}ms d{rows[k]['draw_calls']} pm{pm[k]} tm{rows[k]['texture_cache_misses']}" for k in top))
        # heavy-shot segment: first row after H0+5 with draws >= 5000 and its timing
        hv = [k for k in range(h0, n) if rows[k]["draw_calls"] >= 9000]
        if hv:
            k = hv[0]
            print(f"  first >=9000-draw row after H0: r{k + 1} at H0+{rel(k):.2f} s ({ms[k]:.0f} ms, d{rows[k]['draw_calls']}, pm{pm[k]})")


if __name__ == "__main__":
    main()

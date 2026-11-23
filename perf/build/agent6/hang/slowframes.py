"""slowframes.py -- read-only: per-run stats of the GPU thread's 'slow frame #N' lines (task #16, gate A check).

Usage: python -B build/agent6/hang/slowframes.py <run_dir> [<run_dir> ...]
For each run: the cvars that matter, frame-time buckets by memexport-sync count, the cost per sync that the
listed categories don't explain, and the longest frames. Reads game.log and run.json only; writes nothing.
"""
import json
import os
import re
import statistics
import sys

RX = re.compile(
    r"^\[(?P<ts>[^\]]+)\] \[info\] \[gpu\] \[t\d+\] slow frame #(?P<n>\d+): (?P<ms>[\d.]+) ms"
    r" \| gpu-thread idle (?P<idle>[\d.]+) \| host-gpu wait (?P<hgw>[\d.]+) \((?P<hgwn>\d+)x\)"
    r" \| shader translate (?P<st>[\d.]+) \(\d+x\) \| pipeline create (?P<pc>[\d.]+) \(\d+x\), new \d+"
    r" \| texture load (?P<tl>[\d.]+) \(\d+x\).*?memexport syncs (?P<sy>\d+) \((?P<sykb>\d+) KB\)")
BUCKETS = [(0, 49), (50, 199), (200, 999), (1000, 10 ** 9)]


def fit(xs, ys):
    if len(xs) < 3:
        return None
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx == 0 or syy == 0:
        return None
    b = sxy / sxx
    return b, my - b * mx, sxy / (sxx * syy) ** 0.5


def one(run):
    name = os.path.basename(os.path.normpath(run))
    print(f"== {name}")
    try:
        rj = json.load(open(os.path.join(run, "run.json"), encoding="utf-8-sig"))
        cv = rj.get("cvars") or {}
        keep = {k: v for k, v in cv.items() if k != "framerate_limit"}
        print(f"   cvars (besides framerate_limit): {keep or 'none'}")
    except Exception as e:  # noqa: BLE001
        print(f"   run.json: {e}")
    rows = []
    with open(os.path.join(run, "game.log"), encoding="utf-8", errors="replace") as f:
        for line in f:
            if "slow frame #" not in line:
                continue
            m = RX.match(line)
            if not m:
                continue
            d = {k: (float(v) if k not in ("ts",) else v) for k, v in m.groupdict().items()}
            d["other"] = d["ms"] - d["idle"] - d["hgw"] - d["st"] - d["pc"] - d["tl"]
            rows.append(d)
    if not rows:
        print("   no parsable slow-frame lines")
        return
    ms = [r["ms"] for r in rows]
    print(f"   slow-frame lines {len(rows)}; min {min(ms):.1f} ms (the log threshold), median {statistics.median(ms):.1f},"
          f" >1 s {sum(x > 1000 for x in ms)}, >5 s {sum(x > 5000 for x in ms)}")
    print("   syncs bucket |    n | >1 s | mean ms | mean other ms | other ms per sync")
    for lo, hi in BUCKETS:
        b = [r for r in rows if lo <= r["sy"] <= hi]
        if not b:
            continue
        mo = statistics.fmean(r["other"] for r in b)
        msy = statistics.fmean(r["sy"] for r in b)
        per = mo / msy if msy else float("nan")
        lab = f"{lo}-{hi}" if hi < 10 ** 9 else f">={lo}"
        n1 = sum(r["ms"] > 1000 for r in b)
        print(f"   {lab:>12} | {len(b):4d} | {n1:4d} | {statistics.fmean(r['ms'] for r in b):7.1f} | {mo:13.1f} | {per:8.2f}")
    f1 = fit([r["sy"] for r in rows], [r["other"] for r in rows])
    if f1:
        print(f"   fit other_ms = {f1[1]:.1f} + {f1[0]:.3f} * syncs   (r = {f1[2]:.2f})")
    print("   longest frames: frame  wall  ms  syncs  host-gpu-wait(n)  idle  other")
    for r in sorted(rows, key=lambda r: -r["ms"])[:6]:
        print(f"     #{int(r['n'])} {r['ts'][11:]} {r['ms']:.1f} sy={int(r['sy'])} hgw={r['hgw']:.1f}({int(r['hgwn'])})"
              f" idle={r['idle']:.1f} other={r['other']:.1f}")


if __name__ == "__main__":
    for a in sys.argv[1:]:
        one(a)

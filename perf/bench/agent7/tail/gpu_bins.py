"""Bin gpu.csv (nvidia-smi 1 s samples) by 10 s of its own t_s. Read-only."""
import csv, os, sys

BASE = r"build\agent8\matrix\20261122-0452\runs"
for d in sys.argv[1:]:
    rows = list(csv.DictReader(open(os.path.join(BASE, d, "gpu.csv"), encoding="utf-8")))
    print("==", d, "rows", len(rows), "t_s %.1f..%.1f" % (float(rows[0]["t_s"]), float(rows[-1]["t_s"])))
    for b in range(7):
        sel = [x for x in rows if b * 10 <= float(x["t_s"]) < (b + 1) * 10]
        if not sel:
            continue
        u = [float(x["util_gpu"]) for x in sel]
        m = [float(x["gr_mhz"]) for x in sel]
        p = [float(x["power_w"]) for x in sel]
        th = ",".join(sorted(set(x["throttle"] for x in sel)))
        print("  %2d-%2ds util mean %4.0f%% max %3.0f%%  clk mean %5.0f min %5.0f  power %5.1f W  thr %s" % (
            b * 10, b * 10 + 10, sum(u) / len(u), max(u), sum(m) / len(m), min(m), sum(p) / len(p), th))

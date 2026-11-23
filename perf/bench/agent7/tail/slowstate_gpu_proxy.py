"""Does the GPU clock dip (gpu.csv) track the E-core slow state (sys.csv e_eff_mhz)? Read-only, stdlib.

For each run under build/agent8/matrix/<since..until>/runs with both files: 10 s bins over each file's own
time base (sys: epoch_s - first epoch_s; gpu: t_s), mean e_eff_mhz (and p_eff_mhz if present) vs GPU gr_mhz/power.
Prints per-run bins and the pooled Spearman across bins.
"""
import csv, os, sys

ROOT = r"build\agent8\matrix"
since, until = sys.argv[1], sys.argv[2]


def spearman(a, b):
    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for k, i in enumerate(o):
            r[i] = k
        return r
    ra, rb = rank(a), rank(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** 0.5
    return num / den if den else float("nan")


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


pool_e, pool_g, pool_w = [], [], []
hdr_done = False
for m in sorted(os.listdir(ROOT)):
    if not (len(m) == 13 and m[8] == "-" and since <= m <= until):
        continue
    rd = os.path.join(ROOT, m, "runs")
    if not os.path.isdir(rd):
        continue
    for r in sorted(os.listdir(rd)):
        sp, gp = os.path.join(rd, r, "sys.csv"), os.path.join(rd, r, "gpu.csv")
        if not (os.path.isfile(sp) and os.path.isfile(gp)):
            continue
        srows = list(csv.DictReader(open(sp, encoding="utf-8-sig")))
        grows = list(csv.DictReader(open(gp, encoding="utf-8-sig")))
        if not hdr_done:
            print("sys.csv columns:", ", ".join(srows[0].keys()) if srows else "-")
            hdr_done = True
        srows = [x for x in srows if f(x.get("epoch_s")) is not None and f(x.get("e_eff_mhz")) is not None]
        if not srows or not grows:
            continue
        e0 = f(srows[0]["epoch_s"])
        line = []
        for b in range(12):
            es = [f(x["e_eff_mhz"]) for x in srows if b * 10 <= f(x["epoch_s"]) - e0 < b * 10 + 10]
            ps = [f(x.get("p_eff_mhz")) for x in srows if b * 10 <= f(x["epoch_s"]) - e0 < b * 10 + 10
                  and f(x.get("p_eff_mhz")) is not None]
            gs = [x for x in grows if b * 10 <= float(x["t_s"]) < b * 10 + 10]
            if len(es) < 3 or len(gs) < 3:
                continue
            em = sum(es) / len(es)
            gm = sum(float(x["gr_mhz"]) for x in gs) / len(gs)
            gw = sum(float(x["power_w"]) for x in gs) / len(gs)
            pool_e.append(em)
            pool_g.append(gm)
            pool_w.append(gw)
            line.append("%d:E%4.0f%s/G%4.0f" % (b * 10, em, ("/P%4.0f" % (sum(ps) / len(ps))) if ps else "", gm))
        print("%s/%s  %s" % (m, r, "  ".join(line)))
if len(pool_e) >= 5:
    lowe = [g for e, g in zip(pool_e, pool_g) if e < 800]
    hie = [g for e, g in zip(pool_e, pool_g) if e >= 800]
    print("bins %d; Spearman(E MHz, GPU MHz) %.2f; Spearman(E MHz, GPU W) %.2f" % (
        len(pool_e), spearman(pool_e, pool_g), spearman(pool_e, pool_w)))
    if lowe and hie:
        print("GPU MHz mean in bins with E < 800: %.0f (n %d); E >= 800: %.0f (n %d)" % (
            sum(lowe) / len(lowe), len(lowe), sum(hie) / len(hie), len(hie)))

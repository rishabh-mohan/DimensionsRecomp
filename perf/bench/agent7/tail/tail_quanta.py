import os, sys, statistics
sys.path.insert(0, r"<workspace>\bench\agent7")
import native_frames_summary as nfs
import threaded_tail as tt

M = r"<workspace>\build\agent8\matrix\20261122-0452\runs"


def hist(vals, width=2.0, top=64.0):
    nb = int(top / width)
    h = [0] * (nb + 1)
    for v in vals:
        if v < 0:
            continue
        h[min(int(v / width), nb)] += 1
    return h


for run in sys.argv[1:]:
    d = os.path.join(M, run)
    rows = nfs.read_native_csv(os.path.join(d, "native-frames.csv"))
    t_all = [nfs.to_float(r["interval_ms"]) for r in rows]
    perf = tt.read_perf_rows(os.path.join(d, "perf.csv"))
    pt = [int(r["frame_time_us"]) / 1000.0 for r in perf]
    wins, note = nfs.runner_window(d, t_all, pt)
    lo, hi = wins["native"]
    W = rows[lo:hi]
    t = t_all[lo:hi]
    sw = [float(r["swap_present_cpu_ms"]) for r in W]
    n = len(t)
    ex, swx, rest = [], [], []
    for i in range(n):
        nb = [t[k] for k in range(max(0, i - 5), min(n, i + 6)) if k != i]
        nbs = [sw[k] for k in range(max(0, i - 5), min(n, i + 6)) if k != i]
        base = statistics.median(nb)
        e = t[i] - base
        if t[i] > 16.7:
            ex.append(e)
            s = sw[i] - statistics.median(nbs)
            swx.append(s)
            rest.append(e - s)
    print("=" * 20, run, "frames > 16.7 ms: %d" % len(ex))
    print("  excess over the +-5 neighbour median, 2 ms bins from 0 (count per bin):")
    print("   interval  ", hist(ex))
    print("   swap      ", hist(swx))
    print("   non-swap  ", hist(rest))
    # where are the peaks
    for lab, v in (("interval", ex), ("swap", swx), ("non-swap", rest)):
        big = sorted(x for x in v if x > 8)
        if big:
            print("  %s excess > 8 ms: n %d, p25 %.1f, median %.1f, p75 %.1f" % (
                lab, len(big), big[len(big) // 4], big[len(big) // 2], big[3 * len(big) // 4]))

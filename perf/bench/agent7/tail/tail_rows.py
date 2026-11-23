import csv, os, sys
sys.path.insert(0, r"<workspace>\bench\agent7")
import native_frames_summary as nfs
import threaded_tail as tt

M = r"<workspace>\build\agent8\matrix\20261122-0452\runs"
COLS = ["interval_ms", "swap_present_cpu_ms", "present_cpu_ms", "callbacks_enqueued", "callbacks_executed",
        "callbacks_pending", "frame_slot_wait_calls", "detailed_timing_enabled", "draw_calls"]
for run in sys.argv[1:]:
    d = os.path.join(M, run)
    rows = nfs.read_native_csv(os.path.join(d, "native-frames.csv"))
    t_all = [nfs.to_float(r["interval_ms"]) for r in rows]
    perf = tt.read_perf_rows(os.path.join(d, "perf.csv"))
    pt = [int(r["frame_time_us"]) / 1000.0 for r in perf]
    wins, note = nfs.runner_window(d, t_all, pt)
    lo, hi = wins["native"]
    W = rows[lo:hi]
    P = perf[lo + 1:hi + 1]
    t = t_all[lo:hi]
    cum = []
    a = 0.0
    for x in t:
        a += x
        cum.append(a / 1000.0)
    S = [i for i in range(len(t)) if t[i] > 33 and float(W[i]["swap_present_cpu_ms"]) >= 10]
    O = [i for i in range(len(t)) if t[i] > 33 and float(W[i]["swap_present_cpu_ms"]) < 5]
    print("=" * 30, run, "type S (swap>=10) %d, type O (swap<5) %d" % (len(S), len(O)))
    for lab, ids in (("S", S), ("O", O)):
        ts = sorted(t[i] for i in ids)
        sw = sorted(float(W[i]["swap_present_cpu_ms"]) for i in ids)
        print(" %s: interval median %.1f (min %.1f max %.1f); swap median %.1f; window s: %s" % (
            lab, ts[len(ts) // 2] if ts else 0, ts[0] if ts else 0, ts[-1] if ts else 0,
            sw[len(sw) // 2] if sw else 0, " ".join("%.1f" % cum[i] for i in ids)))
        # 10 s bins
        bins = [0] * 7
        for i in ids:
            bins[min(int(cum[i] // 10), 6)] += 1
        print("   per 10 s:", bins)
    for lab, ids in (("S", S[:3]), ("O", O[:3])):
        for i in ids:
            print(" -- %s frame at window %.2f s (row %d)" % (lab, cum[i], lo + i))
            for k in range(max(0, i - 3), min(len(t), i + 4)):
                r = W[k]
                print("   %+d " % (k - i) + " ".join("%s=%s" % (c.replace("_cpu_ms", "").replace("callbacks_", "cb_"),
                                                                r.get(c)) for c in COLS) +
                      " | perf fd=%s bqd=%s" % (P[k].get("functions_dispatched"), P[k].get("buffer_queue_depth")))

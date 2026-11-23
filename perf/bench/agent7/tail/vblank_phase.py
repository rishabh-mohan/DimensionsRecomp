"""Are the swap stalls gated by the 60 Hz display (DWM composition)? Read-only, stdlib.

t_k = cumulative interval_ms (the measurement point right after Present + the swap section). For frames with
swap_present_cpu_ms >= THR and, as a control, frames with swap < 1 ms (same count, evenly picked), find the
display period P in [16.60, 16.76] ms (step 0.0005) that maximizes the Rayleigh resultant R of phase(t_k mod P).
Uniform phases give R ~ sqrt(pi/(4n)) (plus the search inflation, hence the control).
"""
import cmath, math, os, sys

sys.path.insert(0, r"bench\agent7")
import native_frames_summary as nfs  # noqa: E402

BASE = r"build\agent8\matrix\20261122-0452\runs"
THR = float(os.environ.get("THR", "5"))


def best_r(times):
    best = (0.0, None, None)
    p = 16.60
    while p <= 16.76:
        z = sum(cmath.exp(2j * math.pi * (t % p) / p) for t in times) / len(times)
        if abs(z) > best[0]:
            best = (abs(z), p, (cmath.phase(z) % (2 * math.pi)) / (2 * math.pi) * p)
        p += 0.0005
    return best


for d in sys.argv[1:]:
    rd = os.path.join(BASE, d)
    rows = nfs.read_native_csv(os.path.join(rd, "native-frames.csv"))
    t = [float(r["interval_ms"]) for r in rows]
    wins, _ = nfs.runner_window(rd, t, [])
    lo, hi = wins["native"]
    swap = [float(r.get("swap_present_cpu_ms") or 0) for r in rows]
    cum, acc = [], 0.0
    for v in t:
        acc += v
        cum.append(acc)
    ev = [cum[i] for i in range(lo, hi) if swap[i] >= THR]
    slow = [cum[i] for i in range(lo, hi) if t[i] > 33.0]
    ctl_all = [cum[i] for i in range(lo, hi) if swap[i] < 1.0]
    step = max(1, len(ctl_all) // max(1, len(ev)))
    ctl = ctl_all[::step][:len(ev)]
    print("== %s  window frames %d" % (d, hi - lo))
    for name, xs in (("swap>=%g" % THR, ev), ("slow>33", slow), ("control swap<1", ctl)):
        if len(xs) < 5:
            print("  %-15s n %4d  -" % (name, len(xs)))
            continue
        r, p, ph = best_r(xs)
        print("  %-15s n %4d  best P %.4f ms  R %.3f  (uniform ~%.3f; p~exp(-nR^2)=%.2g)  phase %.1f ms" % (
            name, len(xs), p, r, math.sqrt(math.pi / (4 * len(xs))), math.exp(-len(xs) * r * r), ph))

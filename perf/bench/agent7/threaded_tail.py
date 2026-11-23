#!/usr/bin/env python3
"""Tail-latency breakdown of native runs in the runner's scored window (Agent 7, task #26).

For each run dir (needs native-frames.csv, frames.json and summary.txt; perf.csv, gpu.csv and proc.csv are optional)
it prints:
  1. the interval histogram, with the share of frames and of window time in each bucket;
  2. where the slow frames (interval_ms > --slow-ms, default 33) fall:
     - per --bin-s bin: frames, fps, p50, p99, slow count, GPU util/clock (gpu.csv), process CPU cores (proc.csv);
     - clusters (slow frames <= 3 frames apart), the gaps between slow frames, and the Fano factor of the
       per-second slow counts (about 1 = random, > 1 = bursts, < 1 = periodic);
     - the median interval of the frames around a slow frame (offsets -3..+3);
  3. which per-frame columns co-occur with the slow frames. For native-frames.csv columns and perf.csv columns
     (prefix perf., row-aligned by the best shift), it prints the mean in slow vs other frames, the share > 0, and
     the Spearman rank correlation with interval_ms over the window: same frame (rho), previous frame's column
     (rho-1) and next frame's column (rho+1).
A final table puts the focus columns of every run side by side.

Usage: python bench\\agent7\\threaded_tail.py <run dir> [<run dir> ...] [--slow-ms 33] [--bin-s 10] [--top 12]
           [--cond COL:THR ...] [--split COL ...] [-o OUT]
  --cond COL:THR  P(slow | COL >= THR) vs P(slow | COL < THR), the rate of COL >= THR per minute
  --split COL     share of the slow (and 20..slow ms) frames' excess interval that sits in COL's excess
Read-only, stdlib only, single thread. The window comes from native_frames_summary.runner_window (frames.json).
"""
import argparse
import bisect
import csv
import math
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import native_frames_summary as nfs  # noqa: E402

FOCUS = (
    "sync_calls", "sync_ms", "sync_other_ms", "sync_idle_ms", "sync_fence_ms", "sync_resource_ms",
    "sync_callback_ms", "sync_query_begin_ms", "sync_query_release_ms", "cpu_resource_wait_skips",
    "frame_slot_wait_calls", "frame_slot_wait_ms",
    "pipeline_creations", "pipeline_creation_ms", "temporal_pipeline_creations",
    "present_cpu_ms", "acquire_cpu_ms", "present_submit_cpu_ms", "swap_present_cpu_ms",
    "callbacks_enqueued", "callbacks_executed", "callbacks_pending",
    "bindings_ms", "begin_ms", "pipeline_ms", "issue_ms", "tail_ms",
    "texture_ms", "constants_ms", "vertices_ms", "buffer_hash_ms", "draw_calls", "buffer_converted_bytes",
)
PERF_FOCUS = (
    "perf.command_buffer_stalls", "perf.buffer_queue_depth", "perf.apc_queue_depth",
    "perf.critical_region_contentions", "perf.pipeline_cache_misses", "perf.texture_cache_misses",
    "perf.functions_dispatched", "perf.interrupt_dispatches", "perf.active_threads", "perf.draw_calls",
)
HIST_EDGES = (5.0, 8.0, 12.0, 16.7, 20.0, 25.0, 33.0, 40.0, 50.0, 70.0)
FF_RE = re.compile(r"first frame signal at ([0-9.]+) s")
FFWIN_RE = re.compile(r"first-frame signal to the start mark ([0-9.]+) s")


def fnum(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def pct(sorted_vals, p):
    return nfs.nearest_rank(sorted_vals, p)


def read_perf_rows(path):
    """perf.csv rows as dicts, indexed like native_frames_summary.read_perf_csv: a partial last row is dropped and
    rows whose frame_time_us isn't an integer are skipped."""
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return []
    lines = data.split(b"\n")
    if data and not data.endswith(b"\n"):
        lines = lines[:-1]
    if not lines:
        return []
    header = lines[0].strip().decode("ascii", "replace").split(",")
    if "frame_time_us" not in header:
        return []
    col = header.index("frame_time_us")
    out = []
    for raw in lines[1:]:
        raw = raw.strip()
        if not raw:
            continue
        parts = raw.decode("ascii", "replace").split(",")
        try:
            int(parts[col])
        except (ValueError, IndexError):
            continue
        out.append(dict(zip(header, parts)))
    return out


def rank(vals):
    """1-based ranks; ties get the average rank."""
    order = sorted(range(len(vals)), key=vals.__getitem__)
    r = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def pearson(x, y):
    n = len(x)
    if n < 3 or n != len(y):
        return None
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx <= 0 or syy <= 0:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sxx * syy)


def spearman(x, y):
    if len(x) < 3 or len(x) != len(y):
        return None
    return pearson(rank(x), rank(y))


def clusters(idx, max_gap):
    """Group sorted frame indices into runs whose neighbours are at most max_gap frames apart."""
    out = []
    for i in idx:
        if out and i - out[-1][-1] <= max_gap:
            out[-1].append(i)
        else:
            out.append([i])
    return out


def fano(counts):
    """Variance / mean of counts (about 1 for random arrivals, > 1 for bursts, < 1 for regular ones)."""
    if len(counts) < 2:
        return None
    m = sum(counts) / len(counts)
    if m <= 0:
        return None
    return statistics.pvariance(counts) / m


def read_series(path, cols):
    """[(t_s, {col: value})] from a runner csv with a t_s column (gpu.csv, proc.csv)."""
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    except OSError:
        return []
    out = []
    for r in rows:
        t = fnum(r.get("t_s"))
        if t is not None:
            out.append((t, {c: fnum(r.get(c)) for c in cols}))
    return out


def series_mean(series, t0, t1, col):
    vals = [v[col] for t, v in series if t0 <= t < t1 and v.get(col) is not None]
    return sum(vals) / len(vals) if vals else None


def window_start_proc_s(run_dir):
    """Process time (s after launch) of the window's start mark, from summary.txt; None if unknown."""
    try:
        with open(os.path.join(run_dir, "summary.txt"), encoding="utf-8-sig", errors="replace") as f:
            text = f.read()
    except OSError:
        return None
    a, b = FF_RE.search(text), FFWIN_RE.search(text)
    return float(a.group(1)) + float(b.group(1)) if a and b else None


def f2(v, spec="%.2f"):
    return "-" if v is None or (isinstance(v, float) and math.isnan(v)) else spec % v


def column_stats(vals, t, slow):
    """Means in slow/other frames, share > 0 in each, rho at lags 0, -1 (previous frame's value), +1, and pms:
    (column per ms of frame time in slow frames) / (the same in other frames). pms near 1 means the column just
    grows with the frame's length (a time-driven counter); well above 1 means it takes a bigger share of slow
    frames."""
    s_vals = [v for v, s in zip(vals, slow) if s]
    o_vals = [v for v, s in zip(vals, slow) if not s]
    s_t = sum(x for x, s in zip(t, slow) if s)
    o_t = sum(x for x, s in zip(t, slow) if not s)
    pms = None
    if s_vals and o_vals and s_t > 0 and o_t > 0 and sum(o_vals) > 0:
        pms = (sum(s_vals) / s_t) / (sum(o_vals) / o_t)
    res = {
        "all": sum(vals) / len(vals) if vals else None,
        "slow": sum(s_vals) / len(s_vals) if s_vals else None,
        "other": sum(o_vals) / len(o_vals) if o_vals else None,
        "nz_slow": sum(1 for v in s_vals if v > 0) / len(s_vals) if s_vals else None,
        "nz_other": sum(1 for v in o_vals if v > 0) / len(o_vals) if o_vals else None,
        "rho": spearman(vals, t),
        "rho_prev": spearman(vals[:-1], t[1:]),
        "rho_next": spearman(vals[1:], t[:-1]),
        "pms": pms,
    }
    return res


def cond_lines(name, thr, vals, t, slow_ms, minutes):
    """P(slow | column >= thr) against P(slow | column < thr), and how often the column reaches thr."""
    hit = [x for v, x in zip(vals, t) if v >= thr]
    miss = [x for v, x in zip(vals, t) if v < thr]
    n_slow = sum(1 for x in t if x > slow_ms)
    hs = sum(1 for x in hit if x > slow_ms)
    ms = sum(1 for x in miss if x > slow_ms)
    return ("  cond %s >= %g: %d frames (%.1f/min); P(> %g ms | >=) %s (%d), P(> %g ms | <) %s (%d); %s of the slow "
            "frames have it; median interval >= %s vs < %s ms" % (
                name, thr, len(hit), len(hit) / minutes if minutes else 0, slow_ms,
                f2(hs / len(hit) if hit else None, "%.3f"), hs, slow_ms,
                f2(ms / len(miss) if miss else None, "%.4f"), ms,
                f2(hs / n_slow if n_slow else None), f2(statistics.median(hit) if hit else None),
                f2(statistics.median(miss) if miss else None)))


def split_lines(name, vals, t, groups):
    """For each (label, lo, hi) group of frames by interval: how much of the interval's excess over the window
    median sits in the column's excess over its own median."""
    tm, vm = statistics.median(t), statistics.median(vals)
    out = []
    for label, lo, hi in groups:
        ids = [i for i, x in enumerate(t) if lo < x <= hi]
        if not ids:
            continue
        ex_t = sum(t[i] - tm for i in ids)
        ex_v = sum(vals[i] - vm for i in ids)
        ratios = sorted((vals[i] - vm) / (t[i] - tm) for i in ids if t[i] > tm)
        out.append("  split %s, frames %s (%d): mean interval %.2f (median %.2f), mean %s %.2f (median %.2f); "
                   "share of the excess %.0f%%, per-frame median %.0f%% (p25 %.0f%%, p75 %.0f%%)" % (
                       name, label, len(ids), sum(t[i] for i in ids) / len(ids), tm, name,
                       sum(vals[i] for i in ids) / len(ids), vm, 100.0 * ex_v / ex_t if ex_t else 0,
                       100.0 * pct(ratios, 0.5) if ratios else 0, 100.0 * pct(ratios, 0.25) if ratios else 0,
                       100.0 * pct(ratios, 0.75) if ratios else 0))
    return out


def analyse(run_dir, slow_ms, bin_s, top, emit, conds=(), splits=()):
    arm = nfs.arm_of(run_dir)
    rows = nfs.read_native_csv(os.path.join(run_dir, "native-frames.csv"))
    nat_t = [nfs.to_float(r.get("interval_ms")) for r in rows]
    perf_rows = read_perf_rows(os.path.join(run_dir, "perf.csv"))
    perf_t = [int(r["frame_time_us"]) / 1000.0 for r in perf_rows]
    wins, note = nfs.runner_window(run_dir, nat_t, perf_t)
    emit("")
    emit("=" * 100)
    emit("%s  (%s)" % (arm, run_dir))
    emit("window: " + note)
    if not wins or "native" not in wins:
        emit("  no usable native window; skipped")
        return None
    lo, hi = wins["native"]
    win_rows = rows[lo:hi]
    t = nat_t[lo:hi]
    n = len(t)
    st = sorted(t)
    total_s = sum(t) / 1000.0
    slow = [x > slow_ms for x in t]
    slow_idx = [i for i, s in enumerate(slow) if s]
    med = pct(st, 0.5)
    emit("frames %d over %.3f s = %.2f fps; mean %.3f, p50 %.3f, p95 %.3f, p99 %.3f, p99.9 %.3f, max %.3f ms; "
         "1%% low (mean of the slowest 1%%) %.2f fps; > %g ms: %d" % (
             n, total_s, n / total_s, total_s * 1000.0 / n, med, pct(st, 0.95), pct(st, 0.99), pct(st, 0.999),
             st[-1], 1000.0 / statistics.mean(st[-max(1, n // 100):]), slow_ms, len(slow_idx)))

    # 1. histogram
    counts = [0] * (len(HIST_EDGES) + 1)
    times = [0.0] * (len(HIST_EDGES) + 1)
    for x in t:
        k = bisect.bisect_left(HIST_EDGES, x)
        counts[k] += 1
        times[k] += x
    labels = (["<=%g" % HIST_EDGES[0]] + ["%g-%g" % (a, b) for a, b in zip(HIST_EDGES, HIST_EDGES[1:])] +
              [">%g" % HIST_EDGES[-1]])
    emit("histogram (ms: frames, %% of frames, %% of window time):")
    emit("  " + "  ".join("%s: %d %.1f%% %.1f%%" % (lab, c, 100.0 * c / n, 100.0 * tm / (total_s * 1000.0))
                         for lab, c, tm in zip(labels, counts, times) if c))
    excess = sum(x - med for x in t if x > slow_ms) / 1000.0
    emit("  time above the median spent in slow frames: %.2f s of %.2f s (%.1f%%)" % (
        excess, total_s, 100.0 * excess / total_s))

    # 2. time placement
    cum = []
    acc = 0.0
    for x in t:
        acc += x
        cum.append(acc / 1000.0)
    tp0 = window_start_proc_s(run_dir)
    gpu = read_series(os.path.join(run_dir, "gpu.csv"), ("util_gpu", "gr_mhz"))
    proc = read_series(os.path.join(run_dir, "proc.csv"), ("cpu_cores",))
    nb = int(math.ceil(cum[-1] / bin_s)) if cum else 0
    emit("per %g s bin (window s; proc s = window start %s s after launch; gpu/proc columns are means of their 1 s "
         "samples):" % (bin_s, f2(tp0)))
    emit("  %-9s %6s %7s %7s %7s %5s %7s %7s %6s" % (
        "window s", "frames", "fps", "p50", "p99", ">thr", "gpu %", "gr MHz", "cores"))
    for b in range(nb):
        ids = [i for i in range(n) if b * bin_s <= cum[i] - 1e-9 < (b + 1) * bin_s]
        if not ids:
            continue
        bt = sorted(t[i] for i in ids)
        span = sum(bt) / 1000.0
        g = c = m = None
        if tp0 is not None:
            a0, a1 = tp0 + b * bin_s, tp0 + (b + 1) * bin_s
            g, m = series_mean(gpu, a0, a1, "util_gpu"), series_mean(gpu, a0, a1, "gr_mhz")
            c = series_mean(proc, a0, a1, "cpu_cores")
        emit("  %4g-%-4g %6d %7.1f %7.2f %7.2f %5d %7s %7s %6s" % (
            b * bin_s, (b + 1) * bin_s, len(ids), len(ids) / span if span else 0, pct(bt, 0.5), pct(bt, 0.99),
            sum(1 for x in bt if x > slow_ms), f2(g, "%.0f"), f2(m, "%.0f"), f2(c)))
    per_s = [0] * (int(math.ceil(cum[-1])) if cum else 0)
    for i in slow_idx:
        per_s[min(int(cum[i]), len(per_s) - 1)] += 1
    cl = clusters(slow_idx, 3)
    sizes = [len(c) for c in cl]
    gaps_f = [b - a for a, b in zip(slow_idx, slow_idx[1:])]
    gaps_s = [cum[b] - cum[a] for a, b in zip(slow_idx, slow_idx[1:])]
    emit("slow frames: %d in %d cluster(s) (<= 3 frames apart); cluster sizes: %s" % (
        len(slow_idx), len(cl), ", ".join("%dx%d" % (sizes.count(k), k) for k in sorted(set(sizes)))))
    if gaps_s:
        gs = sorted(gaps_s)
        emit("  gaps between slow frames: frames median %d (min %d, max %d); seconds median %.2f, p10 %.2f, "
             "p90 %.2f, max %.2f; CV %.2f" % (
                 statistics.median(gaps_f), min(gaps_f), max(gaps_f), statistics.median(gs), pct(gs, 0.1),
                 pct(gs, 0.9), gs[-1], statistics.pstdev(gs) / statistics.mean(gs) if statistics.mean(gs) else 0))
    emit("  per-second slow counts: seconds with >= 1: %d of %d; max %d; Fano %s" % (
        sum(1 for x in per_s if x), len(per_s), max(per_s) if per_s else 0, f2(fano(per_s))))
    emit("  first slow frames at window s: %s" % ", ".join("%.2f" % cum[i] for i in slow_idx[:12]))
    if slow_idx:
        parts = []
        for k in range(-3, 4):
            v = sorted(t[i + k] for i in slow_idx if 0 <= i + k < n)
            parts.append("%+d: %.2f" % (k, statistics.median(v)) if v else "%+d: -" % k)
        emit("  median interval around a slow frame (window median %.2f): %s" % (med, "  ".join(parts)))
        nxt = [t[i + 1] for i in slow_idx if i + 1 < n]
        emit("  next frame < 0.5 x median (catch-up): %d of %d" % (sum(1 for x in nxt if x < 0.5 * med), len(nxt)))

    # 3. co-occurring columns
    shift = None
    if perf_t:
        best = None
        for sh in range(-2, 3):
            if lo + sh < 0 or hi + sh > len(perf_t):
                continue
            mae = sum(abs(perf_t[lo + i + sh] - t[i]) for i in range(n)) / n
            if best is None or mae < best[0]:
                best = (mae, sh)
        if best:
            shift = best[1]
            emit("perf.csv aligned with shift %+d (mean |perf frame_time - interval| %.3f ms)" % (best[1], best[0]))
    cols = {}
    for c in (win_rows[0].keys() if win_rows else []):
        if c in ("frame", "interval_ms"):
            continue
        vals = [fnum(r.get(c)) for r in win_rows]
        if any(v is None for v in vals) or max(vals) == min(vals):
            continue
        cols[c] = vals
    if shift is not None:
        prow = perf_rows[lo + shift:hi + shift]
        for c in (prow[0].keys() if prow else []):
            vals = [fnum(r.get(c)) for r in prow]
            if any(v is None for v in vals) or max(vals) == min(vals):
                continue
            cols["perf." + c] = vals
    res = {c: column_stats(v, t, slow) for c, v in cols.items()}
    emit("columns vs slow frames (constant columns left out; rho = Spearman with interval_ms over the window; "
         "pms = per-ms share in slow / other frames):")
    emit("  %-30s %10s %10s %10s %6s %6s %6s %6s %6s %6s" % (
        "column", "all", "slow", "other", "nz_s", "nz_o", "rho", "rho-1", "rho+1", "pms"))
    focus = [c for c in FOCUS + PERF_FOCUS if c in res]
    rest = sorted((c for c in res if c not in focus), key=lambda c: -abs(res[c]["rho"] or 0))[:top]
    for c in focus + ["--"] + rest:
        if c == "--":
            emit("  -- other columns by |rho| --")
            continue
        r = res[c]
        emit("  %-30s %10s %10s %10s %6s %6s %6s %6s %6s %6s" % (
            c, f2(r["all"], "%.4g"), f2(r["slow"], "%.4g"), f2(r["other"], "%.4g"), f2(r["nz_slow"]),
            f2(r["nz_other"]), f2(r["rho"]), f2(r["rho_prev"]), f2(r["rho_next"]), f2(r["pms"])))
    gone = [c for c in FOCUS if c not in res]
    if gone:
        emit("  constant or missing focus columns: " + ", ".join(gone))
    for spec in conds:
        name, _, thr = spec.rpartition(":")
        if name in cols:
            emit(cond_lines(name, float(thr), cols[name], t, slow_ms, total_s / 60.0))
        else:
            emit("  cond %s: column constant or missing" % name)
    for name in splits:
        if name in cols:
            for ln in split_lines(name, cols[name], t, ((">%g ms" % slow_ms, slow_ms, float("inf")),
                                                        ("20-%g ms" % slow_ms, 20.0, slow_ms))):
                emit(ln)
        else:
            emit("  split %s: column constant or missing" % name)
    return {"arm": arm, "n": n, "fps": n / total_s, "p50": med, "p99": pct(st, 0.99), "slow": len(slow_idx),
            "res": res}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dirs", nargs="+")
    ap.add_argument("--slow-ms", type=float, default=33.0)
    ap.add_argument("--bin-s", type=float, default=10.0)
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--cond", action="append", default=[], metavar="COL:THR",
                    help="print P(slow | COL >= THR) against P(slow | COL < THR); repeatable")
    ap.add_argument("--split", action="append", default=[], metavar="COL",
                    help="print the share of the slow frames' excess interval that sits in COL; repeatable")
    ap.add_argument("-o", "--out")
    a = ap.parse_args(argv)
    lines = []

    def emit(s):
        print(s)
        lines.append(s)

    emit("threaded_tail.py: slow frames = interval_ms > %g ms; runner window from frames.json" % a.slow_ms)
    results = [r for r in (analyse(d, a.slow_ms, a.bin_s, a.top, emit, a.cond, a.split) for d in a.run_dirs) if r]
    if len(results) > 1:
        emit("")
        emit("=" * 100)
        emit("side by side: mean over the window / mean in slow frames / rho")
        emit("  %-30s " % "column" + " ".join("%26s" % ("%s (%d slow)" % (r["arm"], r["slow"])) for r in results))
        for c in FOCUS + PERF_FOCUS:
            if not any(c in r["res"] for r in results):
                continue
            cells = []
            for r in results:
                x = r["res"].get(c)
                cells.append("%26s" % ("-" if not x else "%s / %s / %s" % (
                    f2(x["all"], "%.3g"), f2(x["slow"], "%.3g"), f2(x["rho"]))))
            emit("  %-30s " % c + " ".join(cells))
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

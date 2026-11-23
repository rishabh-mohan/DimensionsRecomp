"""Frame-time summary of Agent 8's run dirs for the native ON build (Agent 7, tasks #20 and #6).

Usage:
  python bench\\agent7\\native_frames_summary.py <run dir> [<run dir> ...] [--seconds 60] [--tail-skip 2]
         [--runner-window]

For each run dir:
  - perf.csv (`--perf_log_csv`, column frame_time_us; native builds write rows only with the
    perf-csv-rows patch): n, mean fps, mean, stddev, median, p99, p99.9 and max (ms), and
    frames > 33 ms / > 100 ms.
    The default window is the last --seconds of frame time, ending --tail-skip seconds before the
    last row. That is the end of the run, which goes past the runner's window: matrix runs keep
    going while the thread-cpu driver finishes.
  - --runner-window: use the runner's scored window from frames.json instead (window.first_row and
    rows, counted in frames.json's source file). The row base is not assumed: it is checked against
    frames.json mean_ms and frames, and the match is printed. The other file is shifted by one row:
    perf.csv has a leading 0 row, so perf row k+1 = native row k. Falls back to the tail window when
    frames.json is missing.
  - native-frames.csv (`LEGO_NATIVE_FRAME_METRICS=native-frames.csv`, column interval_ms): the
    same stats on the same kind of window, plus window means of the present-path columns and
    the last row's vsync, fps cap, output size, scene and present-source sizes, and FSR flags.
  - row check: perf.csv rows minus native-frames.csv rows (expect +1); gaps in the native frame
    column; the max over all native rows of spatial_fsr_presented (FSR 1 actually presented) and
    fsr_enabled (= NativeFsr3Enabled(), native FSR 3, not FSR 1).
  - proc.csv: mean and max cpu_cores over the 'measure' rows.
  - game.log: the lines that confirm which toggles were active, plus the adapter, swap-chain,
    settings and crash lines (first of each kind, digits ignored).
With several run dirs, a table follows, and per-arm medians (the arm is the run dir name
without its leading HHmm- and a trailing -rN / _N).
Percentiles are nearest-rank, sorted[ceil(p*n)-1], the same as bench/agent8/run/frame_summary.py.
bench/agent7/native3_boot_check.py imports the readers from here.
Stdlib only.
"""
import argparse
import csv
import json
import math
import os
import re
import statistics
import sys

LOG_PATTERNS = (
    "unlocked frame pacing margin",
    "frames-in-flight cap",
    "swap-chain latency wait",
    "swap-chain max frame latency",
    "display gamma updated",
    "presentation cap override",
    "D3D12 ready on",
    "threaded recording",
    "swap chain ready",
    "presented internal texture",
    "present override",
    "Native FSR 1",
    "Native settings:",
    "Native saved settings",
    "committed native settings",
    "Native preferences recovery",
    "is no longer offered",
    "Native setting is not registered",
    "Native GPU initialization failed",
    "Unhandled exception",
)
NATIVE_MEANS = ("frame_slot_wait_ms", "acquire_cpu_ms", "present_submit_cpu_ms",
                "swap_present_cpu_ms", "sync_calls", "sync_ms", "draw_calls")
NATIVE_LAST = ("native_vsync", "native_fps_limit_cvar", "output_width", "output_height",
               "fsr_enabled", "presentation_refresh_hz", "scene_render_width", "scene_render_height",
               "present_source_width", "present_source_height", "spatial_fsr_presented")
FSR_FLAGS = ("spatial_fsr_presented", "fsr_enabled")


def nearest_rank(sorted_vals, p):
    if not sorted_vals:
        return float("nan")
    k = max(1, math.ceil(p * len(sorted_vals)))
    return sorted_vals[min(k, len(sorted_vals)) - 1]


def tail_window(times_ms, seconds, tail_skip):
    """Indices [lo, hi) of the last `seconds` of frame time ending `tail_skip` s before the end."""
    hi = len(times_ms)
    skipped = 0.0
    while hi > 0 and skipped < tail_skip * 1000.0:
        hi -= 1
        skipped += max(times_ms[hi], 0.0)
    lo = hi
    total = 0.0
    while lo > 0 and total < seconds * 1000.0:
        lo -= 1
        total += max(times_ms[lo], 0.0)
    return lo, hi, total / 1000.0


def stats(vals_ms):
    v = [x for x in vals_ms if x > 0]
    if not v:
        return None
    s = sorted(v)
    total = sum(v)
    return {
        "n": len(v),
        "fps": len(v) / (total / 1000.0),
        "mean": total / len(v),
        "sd": statistics.pstdev(v),
        "p50": nearest_rank(s, 0.5),
        "p99": nearest_rank(s, 0.99),
        "p999": nearest_rank(s, 0.999),
        "max": s[-1],
        "gt33": sum(1 for x in v if x > 33.0),
        "gt100": sum(1 for x in v if x > 100.0),
    }


def fmt(st):
    if not st:
        return "no frames"
    return ("n={n} fps={fps:.2f} mean={mean:.3f} sd={sd:.3f} p50={p50:.3f} p99={p99:.3f} "
            "p99.9={p999:.3f} max={max:.3f} ms; >33ms={gt33} >100ms={gt100}").format(**st)


def read_perf_csv(path):
    with open(path, "rb") as f:
        data = f.read()
    lines = data.split(b"\n")
    if data and not data.endswith(b"\n"):
        lines = lines[:-1]  # partial last row
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
        parts = raw.split(b",")
        try:
            out.append(int(parts[col]) / 1000.0)
        except (ValueError, IndexError):
            pass
    return out


def read_native_csv(path):
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if r.get("interval_ms") not in (None, "")]


def to_float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


def load_json(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def runner_window(run_dir, native_t, perf_t):
    """The runner's scored window from frames.json as {"native"|"perf": (lo, hi)} 0-based slices.

    Returns (windows, note); windows is None when frames.json is missing or doesn't fit.
    """
    fj = load_json(os.path.join(run_dir, "frames.json"))
    if not fj:
        return None, "no frames.json; using the tail window"
    w = fj.get("window") or {}
    first, n, src = w.get("first_row"), w.get("rows"), fj.get("source")
    t = {"native": native_t, "perf": perf_t}.get(src)
    if not t or not first or not n:
        return None, "frames.json has no usable source/window (source=%s); using the tail window" % src
    best = None
    for base in (1, 0, 2):  # 0-based start = first_row - base
        lo, hi = first - base, first - base + n
        if lo < 0 or hi > len(t):
            continue
        st = stats(t[lo:hi])
        if not st:
            continue
        err = abs(st["mean"] - fj.get("mean_ms", st["mean"])) + (0 if st["n"] == fj.get("frames", st["n"]) else 1)
        if best is None or err < best[0]:
            best = (err, lo, hi, base, st)
    if best is None:
        return None, "frames.json window (first_row=%s rows=%s) is outside %s's %d rows" % (first, n, src, len(t))
    err, lo, hi, base, st = best
    wins = {src: (lo, hi)}
    other, shift = ("perf", 1) if src == "native" else ("native", -1)
    ot = {"native": native_t, "perf": perf_t}[other]
    if ot and lo + shift >= 0 and hi + shift <= len(ot):
        wins[other] = (lo + shift, hi + shift)
    note = ("frames.json source=%s first_row=%d rows=%d -> %s rows [%d, %d) 0-based (first_row-%d); "
            "mean %.4f vs frames.json %.4f, n %d vs %s: %s; %s window shifted %+d row" % (
                src, first, n, src, lo, hi, base, st["mean"], fj.get("mean_ms", float("nan")), st["n"],
                fj.get("frames"), "MATCH" if err < 0.0006 else "MISMATCH", other, shift))
    return wins, note


def native_row_check(perf_t, rows):
    """Lines for the row check (perf vs native rows, frame gaps, FSR flags over all rows)."""
    out = []
    if perf_t is not None and rows is not None:
        out.append("rows: perf.csv %d, native-frames.csv %d (perf - native = %+d; expect +1, perf.csv's "
                   "leading 0 row)" % (len(perf_t), len(rows), len(perf_t) - len(rows)))
    if rows:
        frames = []
        for r in rows:
            try:
                frames.append(int(r.get("frame")))
            except (TypeError, ValueError):
                pass
        gaps = sum(1 for x, y in zip(frames, frames[1:]) if y != x + 1)
        mx = []
        for c in FSR_FLAGS:
            vals = [v for v in (to_float(r.get(c)) for r in rows) if not math.isnan(v)]
            mx.append("%s=%s" % (c, ("%g" % max(vals)) if vals else "n/a"))
        out.append("native rows: frame %s..%s, %d gap(s); max over all rows: %s" % (
            frames[0] if frames else "?", frames[-1] if frames else "?", gaps, " ".join(mx)))
    return out


def proc_cpu(path):
    with open(path, newline="") as f:
        rows = [r for r in csv.DictReader(f) if r.get("phase") == "measure"]
    vals = [to_float(r.get("cpu_cores")) for r in rows]
    vals = [v for v in vals if not math.isnan(v)]
    if not vals:
        return None
    return sum(vals) / len(vals), max(vals)


def log_key(line):
    key = re.sub(r"^\S*\s*\S*\s*", "", line.strip())  # drop timestamp-ish prefix
    return re.sub(r"\d+", "#", key)


def log_lines(path, limit=24, patterns=LOG_PATTERNS):
    seen, out = set(), []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if any(p in line for p in patterns):
                key = log_key(line)
                if key in seen:
                    continue
                seen.add(key)
                out.append(line.rstrip())
                if len(out) >= limit:
                    break
    return out


def arm_of(run_dir):
    name = os.path.basename(os.path.normpath(run_dir))
    name = re.sub(r"^\d{4}-", "", name)
    return re.sub(r"([-_]r?\d+)$", "", name)


def summarise(run_dir, seconds, tail_skip, use_runner=False):
    res = {"dir": run_dir, "arm": arm_of(run_dir)}
    print("== %s (arm %s)" % (run_dir, res["arm"]))
    perf = os.path.join(run_dir, "perf.csv")
    nat = os.path.join(run_dir, "native-frames.csv")
    perf_t = read_perf_csv(perf) if os.path.exists(perf) else None
    rows = read_native_csv(nat) if os.path.exists(nat) else None
    nat_t = [to_float(r["interval_ms"]) for r in rows] if rows is not None else None
    wins = {}
    if use_runner:
        wins, note = runner_window(run_dir, nat_t or [], perf_t or [])
        print("  runner window: " + note)
        wins = wins or {}

    def pick(t, name):
        if name in wins:
            lo, hi = wins[name]
            return lo, hi, sum(max(x, 0.0) for x in t[lo:hi]) / 1000.0, "runner window"
        lo, hi, win = tail_window(t, seconds, tail_skip)
        return lo, hi, win, "tail window"

    if perf_t is not None:
        lo, hi, win, kind = pick(perf_t, "perf")
        res["perf"] = stats(perf_t[lo:hi])
        print("  perf.csv: %d rows, %s rows %d-%d (%.1f s): %s"
              % (len(perf_t), kind, lo + 1, hi, win, fmt(res["perf"])))
    else:
        print("  perf.csv: missing")
    if rows is not None:
        lo, hi, win, kind = pick(nat_t, "native")
        res["native"] = stats(nat_t[lo:hi])
        print("  native-frames.csv: %d rows, %s rows %d-%d (%.1f s): %s"
              % (len(nat_t), kind, lo + 1, hi, win, fmt(res["native"])))
        w = rows[lo:hi]
        if w:
            means = []
            for c in NATIVE_MEANS:
                vals = [to_float(r.get(c)) for r in w]
                vals = [v for v in vals if not math.isnan(v)]
                if vals:
                    means.append("%s=%.4f" % (c, sum(vals) / len(vals)))
            print("    window means: " + " ".join(means))
            print("    first row: " + " ".join("%s=%s" % (c, rows[0].get(c)) for c in NATIVE_LAST[6:]))
            print("    last row: " + " ".join("%s=%s" % (c, w[-1].get(c)) for c in NATIVE_LAST))
    else:
        print("  native-frames.csv: missing")
    for line in native_row_check(perf_t, rows):
        print("  " + line)
    proc = os.path.join(run_dir, "proc.csv")
    if os.path.exists(proc):
        res["cpu"] = proc_cpu(proc)
        if res["cpu"]:
            print("  proc.csv: cpu_cores mean=%.2f max=%.2f (measure rows)" % res["cpu"])
    log = os.path.join(run_dir, "game.log")
    if os.path.exists(log):
        lines = log_lines(log)
        print("  game.log toggles: %s" % ("none found" if not lines else ""))
        for line in lines:
            print("    " + line)
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("run_dirs", nargs="+")
    ap.add_argument("--seconds", type=float, default=60.0)
    ap.add_argument("--tail-skip", type=float, default=2.0)
    ap.add_argument("--runner-window", action="store_true",
                    help="use frames.json's scored window instead of the tail window")
    a = ap.parse_args()
    results = [summarise(d, a.seconds, a.tail_skip, a.runner_window) for d in a.run_dirs]
    if len(results) < 2:
        return 0
    print("\n%-28s %-6s %8s %8s %7s %8s %8s %8s %5s %6s" % (
        "run", "source", "fps", "mean", "sd", "p50", "p99", "p99.9", ">33", "cores"))
    by_arm = {}
    for r in results:
        src, st = ("perf", r.get("perf")) if r.get("perf") else ("native", r.get("native"))
        cores = r.get("cpu")[0] if r.get("cpu") else float("nan")
        if not st:
            print("%-28s no frames" % os.path.basename(os.path.normpath(r["dir"])))
            continue
        print("%-28s %-6s %8.2f %8.3f %7.3f %8.3f %8.3f %8.3f %5d %6.2f" % (
            os.path.basename(os.path.normpath(r["dir"]))[:28], src, st["fps"], st["mean"],
            st["sd"], st["p50"], st["p99"], st["p999"], st["gt33"], cores))
        by_arm.setdefault(r["arm"], []).append((st, cores))
    print("\nper-arm medians over runs:")
    for arm, items in by_arm.items():
        med = lambda k: statistics.median(s[k] for s, _ in items)
        cores = [c for _, c in items if not math.isnan(c)]
        print("  %-16s runs=%d fps=%.2f sd=%.3f p99=%.3f p99.9=%.3f cores=%s" % (
            arm, len(items), med("fps"), med("sd"), med("p99"), med("p999"),
            "%.2f" % statistics.median(cores) if cores else "n/a"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

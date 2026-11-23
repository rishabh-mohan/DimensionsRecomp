#!/usr/bin/env python3
"""Agent 6, task #18: first-view stalls in the attract sequence (analysis only).

Single-threaded, read-only over Agent 3's run dirs.  For every guest frame
slower than --threshold-ms (default 250) it reports what perf.csv, game.log and
samples.csv show around it, and it counts how many stalls coincide with
pipeline-cache misses (new pipeline / shader creation) or texture-cache misses.

Time alignment
  perf.csv has one row per guest swap; frame_time_us is the wall time between
  swaps, so C(k) = sum(frame_time_us[2..k]) is the time of swap k after swap 1.
  perf.csv is flushed every 60 rows, so each samples.csv / input.csv row with
  perf bytes B tells us: swap K(B) happened before t_s and swap K(B)+60 had not.
  That bounds T0 (swap 1, seconds after launch) from both sides.  The script
  prints the interval and its width; game.log times are converted to seconds
  after launch with run.json "started".

Usage
  python analyze_stalls.py RUN_DIR [RUN_DIR ...] [--threshold-ms 250]
                           [--out-dir DIR] [--log-window-s 2.0]
"""
from __future__ import annotations

import argparse
import bisect
import csv
import datetime as dt
import json
import os
import re
import statistics
import sys

PERF_COLS = [
    "frame_time_us", "fps", "draw_calls", "command_buffer_stalls",
    "vertices_processed", "xma_frames_decoded", "audio_frame_latency_us",
    "buffer_queue_depth", "functions_dispatched", "interrupt_dispatches",
    "active_threads", "apc_queue_depth", "critical_region_contentions",
    "texture_cache_hits", "texture_cache_misses", "pipeline_cache_hits",
    "pipeline_cache_misses",
]
LOG_RE = re.compile(
    r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\] \[(\w+)\] \[(\w+)\] \[t(\d+)\] (.*)$")


# --------------------------------------------------------------------------- io
def read_perf(path):
    """Return (rows, bytes_after) where bytes_after[k] = file bytes through row k
    (k = 1..n; bytes_after[0] = header bytes)."""
    with open(path, "rb") as f:
        data = f.read()
    lines = data.split(b"\n")
    pos = 0
    header = lines[0]
    pos += len(header) + 1
    cols = header.decode().strip().split(",")
    if cols != PERF_COLS:
        print(f"  ! perf.csv header differs: {cols}", file=sys.stderr)
    rows, bytes_after = [], [pos]
    for raw in lines[1:]:
        if not raw.strip():
            pos += len(raw) + 1
            continue
        vals = raw.decode().strip().split(",")
        if len(vals) != len(cols):
            break  # torn last line
        pos += len(raw) + 1
        rows.append({c: float(v) if "." in v else int(v) for c, v in zip(cols, vals)})
        bytes_after.append(pos)
    return rows, bytes_after


def read_csv_dicts(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def fnum(s, default=None):
    try:
        return float(s)
    except (TypeError, ValueError):
        return default


def read_log(path):
    entries = []
    if not os.path.exists(path):
        return entries
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    for line in text.split("\n"):
        line = line.rstrip("\r")
        m = LOG_RE.match(line)
        if m:
            ts = dt.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S.%f")
            entries.append({"ts": ts, "level": m.group(2), "cat": m.group(3),
                            "tid": int(m.group(4)), "msg": m.group(5)})
        elif entries and line:
            entries[-1]["msg"] += " | " + line.strip()
    return entries


def parse_started(run):
    s = run["started"]
    # e.g. 2026-11-22T03:21:52.5048447-06:00 -> local naive datetime
    m = re.match(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(\.\d+)?", s)
    base = dt.datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S")
    frac = float(m.group(2) or 0.0)
    return base + dt.timedelta(seconds=frac)


# ------------------------------------------------------------------- analysis
def log_category(msg):
    m = msg.lower()
    if "install" in m and "ntcreatefile" in m:
        return "INSTALL probe"
    if "ntcreatefile" in m or "ntopenfile" in m or "file" in m and "fail" in m:
        return "file open"
    if "shader" in m:
        return "shader"
    if "pipeline" in m or "pso" in m:
        return "pipeline"
    if "texture" in m:
        return "texture"
    if "toypad" in m:
        return "toypad"
    if "xamuserreadprofilesettings" in m:
        return "profile read"
    if "stub" in m:
        return "kernel stub"
    return "other"


def align_t0(rows, bytes_after, marks):
    """marks: list of (t_s, perf_bytes).  Returns (lo, hi, n_used, C, obs).

    obs: per flush observation (t_s, lo_i, hi_i): the last flushed row K was
    written after the previous mark with fewer bytes and by t_s, so
    offset = wall(K) - C(K) lies in (t_prev - C(K), t_s - C(K)]."""
    C = [0.0] * (len(rows) + 1)  # C[k] seconds from swap 1 to swap k (1-based)
    acc = 0.0
    for k in range(2, len(rows) + 1):
        acc += rows[k - 1]["frame_time_us"] / 1e6
        C[k] = acc
    lo, hi, used = -1e9, 1e9, 0
    n = len(rows)
    obs = []
    prev_t, prev_b = None, None
    for t_s, b in sorted(marks):
        if b is None or b <= bytes_after[0]:
            prev_t, prev_b = t_s, b
            continue
        K = bisect.bisect_right(bytes_after, b) - 1  # rows fully flushed
        if K < 1 or K > n or bytes_after[K] != b:
            prev_t, prev_b = t_s, b
            continue  # torn / unexpected
        hi = min(hi, t_s - C[K])
        if K % 60 == 0 and K + 60 <= n:
            lo = max(lo, t_s - C[K + 60])
        if prev_b is not None and prev_b < b and prev_t is not None:
            obs.append((t_s, prev_t - C[K], t_s - C[K]))
        used += 1
        prev_t, prev_b = t_s, b
    return lo, hi, used, C, obs


def local_offset(obs, t_est, window_s=30.0):
    """Intersect flush observations within +-window_s of t_est.
    Returns (offset, width); width < 0 means the observations disagree."""
    near = [o for o in obs if abs(o[0] - t_est) <= window_s]
    if not near:
        return None, None
    lo = max(o[1] for o in near)
    hi = min(o[2] for o in near)
    if lo <= hi:
        return (lo + hi) / 2.0, hi - lo
    return hi, hi - lo


def pct(vals, p):
    if not vals:
        return float("nan")
    v = sorted(vals)
    i = min(len(v) - 1, max(0, int(round(p / 100.0 * (len(v) - 1)))))
    return v[i]


def find_row(rows, draws, verts, start=1):
    for k in range(start, len(rows) + 1):
        r = rows[k - 1]
        if r["draw_calls"] == draws and r["vertices_processed"] == verts:
            return k
    return None


def analyze(run_dir, threshold_ms, log_window_s, out_dir):
    name = os.path.basename(os.path.normpath(run_dir))
    run = json.load(open(os.path.join(run_dir, "run.json"), encoding="utf-8-sig"))
    started = parse_started(run)
    rows, bytes_after = read_perf(os.path.join(run_dir, "perf.csv"))
    samples = read_csv_dicts(os.path.join(run_dir, "samples.csv"))
    inputs = read_csv_dicts(os.path.join(run_dir, "input.csv"))
    log = read_log(os.path.join(run_dir, "game.log"))
    for e in log:
        e["t"] = (e["ts"] - started).total_seconds()

    marks = []
    for s in samples:
        marks.append((fnum(s.get("t_s")), fnum(s.get("perf_csv_bytes"))))
    for r in inputs:
        marks.append((fnum(r.get("t_s")), fnum(r.get("perf_bytes"))))
    marks = [(t, int(b)) for t, b in marks if t is not None and b is not None]
    lo, hi, used, C, obs = align_t0(rows, bytes_after, marks)
    t0 = hi if hi < 1e8 else 0.0  # upper bound = latest possible swap-1 time
    t0_note = (f"global T0 bounds [{lo:.3f}, {hi:.3f}] s after launch (width {hi - lo:.3f} s, {used} marks); "
               f"per stall a local offset from flush observations within +-30 s is used")

    n = len(rows)
    ft_ms = [r["frame_time_us"] / 1000.0 for r in rows]
    pm = [r["pipeline_cache_misses"] for r in rows]
    tm = [r["texture_cache_misses"] for r in rows]
    h0 = find_row(rows, 2823, 366575)
    if h0 is None:
        h0 = next((k for k in range(1, n + 1) if rows[k - 1]["draw_calls"] >= 2000), None)
    first3d = find_row(rows, 625, 780)

    # samples by time, for cpu cores and private memory around a stall
    srows = []
    for s in samples:
        t = fnum(s.get("t_s"))
        if t is None:
            continue
        srows.append((t, fnum(s.get("cpu_s")), fnum(s.get("private_mb")),
                      fnum(s.get("threads")), fnum(s.get("ws_mb"))))
    srows.sort()
    stimes = [s[0] for s in srows]

    def cores_between(a, b):
        i = bisect.bisect_left(stimes, a)
        j = bisect.bisect_right(stimes, b) - 1
        if i > 0:
            i -= 1
        if j <= i or j >= len(srows):
            return None, None, None
        dc = srows[j][1] - srows[i][1]
        dtm = srows[j][0] - srows[i][0]
        return (dc / dtm if dtm > 0 else None), srows[i][2], srows[j][2]

    stalls = []
    for k in range(2, n + 1):
        r = rows[k - 1]
        if ft_ms[k - 1] <= threshold_ms:
            continue
        off, width = local_offset(obs, t0 + C[k])
        if off is None:
            off, width = t0, None
        t_end = off + C[k]
        t_start = t_end - ft_ms[k - 1] / 1000.0
        w = range(max(1, k - 5), min(n, k + 5) + 1)
        pm_same = pm[k - 1]
        pm_pm2 = sum(pm[j - 1] for j in range(max(1, k - 2), min(n, k + 2) + 1))
        tm_same = tm[k - 1]
        tm_pm2 = sum(tm[j - 1] for j in range(max(1, k - 2), min(n, k + 2) + 1))
        prev_pm = next((k - j for j in range(k, 0, -1) if pm[j - 1] > 0), None)
        prev30 = [rows[j - 1]["draw_calls"] for j in range(max(1, k - 30), k)]
        logs = [e for e in log if t_start - log_window_s <= e["t"] <= t_end + log_window_s]
        cats = {}
        for e in logs:
            c = log_category(e["msg"])
            d = cats.setdefault(c, {"n": 0, "tids": set(), "first": e})
            d["n"] += 1
            d["tids"].add(e["tid"])
        cores, pm0, pm1 = cores_between(t_start - 1.0, t_end + 1.0)
        if pm_same > 0:
            cls = "P"
        elif pm_pm2 > 0:
            cls = "P+-2"
        elif tm_same > 0 or tm_pm2 > 0:
            cls = "T"
        elif r["command_buffer_stalls"] >= 50:
            cls = "CB"
        elif r["draw_calls"] >= 5000:
            cls = "heavy"
        else:
            cls = "none"
        stalls.append({
            "row": k, "t_start": t_start, "t_end": t_end, "align_width_s": width,
            "h0_rel": (C[k - 1] - C[h0 - 1]) if h0 else None,
            "wall_start": (started + dt.timedelta(seconds=t_start)).strftime("%H:%M:%S.%f")[:-3],
            "frame_ms": ft_ms[k - 1], "draws": r["draw_calls"],
            "verts": r["vertices_processed"], "prev30_draws_med": statistics.median(prev30) if prev30 else None,
            "cb_stalls": r["command_buffer_stalls"], "funcs": r["functions_dispatched"],
            "ints": r["interrupt_dispatches"], "threads": r["active_threads"],
            "apc": r["apc_queue_depth"], "crit": r["critical_region_contentions"],
            "xma": r["xma_frames_decoded"], "bufq": r["buffer_queue_depth"],
            "tex_h": r["texture_cache_hits"], "tex_m": tm_same, "tex_m_pm2": tm_pm2,
            "pipe_h": r["pipeline_cache_hits"], "pipe_m": pm_same, "pipe_m_pm2": pm_pm2,
            "pipe_m_w5": sum(pm[j - 1] for j in w), "tex_m_w5": sum(tm[j - 1] for j in w),
            "rows_since_prev_pipe_miss": prev_pm, "cls": cls,
            "cores": cores, "priv_mb_before": pm0, "priv_mb_after": pm1,
            "log": {c: {"n": d["n"], "tids": sorted(d["tids"]),
                        "first_t": round(d["first"]["t"] - t_start, 3),
                        "first": d["first"]["msg"][:110]} for c, d in cats.items()},
        })

    # events: stall frames within 5 rows of each other
    events = []
    for s in stalls:
        if events and s["row"] - events[-1]["last"] <= 5:
            ev = events[-1]
            ev["last"] = s["row"]
            ev["stalls"].append(s)
        else:
            events.append({"first": s["row"], "last": s["row"], "stalls": [s]})
    for ev in events:
        a, b = ev["first"], ev["last"]
        base = statistics.median(ft_ms[max(1, a - 31):a - 1]) if a > 2 else 16.7
        span = range(max(2, a - 2), min(n, b + 2) + 1)
        ev["base_ms"] = round(base, 1)
        ev["stall_s"] = round(sum(s["frame_ms"] for s in ev["stalls"]) / 1000.0, 2)
        ev["excess_s"] = round(sum(max(0.0, ft_ms[j - 1] - base) for j in span) / 1000.0, 2)
        ev["pm"] = sum(pm[j - 1] for j in span)
        ev["tm"] = sum(tm[j - 1] for j in span)
        ev["cb_max"] = max(rows[j - 1]["command_buffer_stalls"] for j in span)
        ev["max_ms"] = round(max(ft_ms[j - 1] for j in span))
        ev["sig"] = f"{rows[a - 1]['draw_calls']}/{rows[a - 1]['vertices_processed']}"
        ev["h0_rel"] = ev["stalls"][0]["h0_rel"]
        ev["wall"] = ev["stalls"][0]["wall_start"]
        ev["t_start"] = ev["stalls"][0]["t_start"]
        ev["classes"] = "".join(sorted({s["cls"][0] for s in ev["stalls"]}))
        ev["ms_per_pm"] = round(ev["excess_s"] * 1000.0 / ev["pm"], 1) if ev["pm"] else None

    # converse: frames with pipeline misses, how slow are they
    def bucket(sel):
        v = [ft_ms[i] for i in sel]
        return {"n": len(v), "med_ms": round(pct(v, 50), 2) if v else None,
                "p90_ms": round(pct(v, 90), 2) if v else None,
                "gt100": sum(1 for x in v if x > 100), "gt250": sum(1 for x in v if x > threshold_ms),
                "sum_s": round(sum(v) / 1000.0, 2)}
    idx_pm = [i for i in range(1, n) if pm[i] > 0]
    idx_tm_only = [i for i in range(1, n) if tm[i] > 0 and pm[i] == 0]
    idx_none = [i for i in range(1, n) if tm[i] == 0 and pm[i] == 0]
    stall_time = sum(s["frame_ms"] for s in stalls) / 1000.0
    by_cls = {}
    for s in stalls:
        d = by_cls.setdefault(s["cls"], {"n": 0, "sum_s": 0.0})
        d["n"] += 1
        d["sum_s"] += s["frame_ms"] / 1000.0
    res = {
        "run": name, "rows": n, "t0_note": t0_note, "t0": t0, "h0_row": h0,
        "first3d_row": first3d, "threshold_ms": threshold_ms, "stalls": stalls,
        "events": [{k: v for k, v in ev.items() if k != "stalls"} for ev in events],
        "stall_count": len(stalls), "stall_time_s": round(stall_time, 2),
        "by_class": {k: {"n": v["n"], "sum_s": round(v["sum_s"], 2)} for k, v in by_cls.items()},
        "pipe_miss_total": sum(pm), "tex_miss_total": sum(tm),
        "frames_with_pipe_miss": bucket(idx_pm),
        "frames_with_tex_miss_only": bucket(idx_tm_only),
        "frames_without_miss": bucket(idx_none),
        "run_seconds": round(C[n], 2),
    }
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, f"{name}.stalls.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, default=str)
    with open(os.path.join(out_dir, f"{name}.stalls.csv"), "w", newline="", encoding="utf-8") as f:
        wcols = ["row", "wall_start", "t_start", "align_width_s", "h0_rel", "frame_ms", "cls", "draws",
                 "verts", "prev30_draws_med", "pipe_m", "pipe_m_pm2", "pipe_m_w5", "pipe_h",
                 "tex_m", "tex_m_pm2", "tex_m_w5", "tex_h", "cb_stalls", "funcs", "ints",
                 "threads", "apc", "crit", "xma", "bufq", "cores", "priv_mb_before",
                 "priv_mb_after", "rows_since_prev_pipe_miss", "log"]
        wr = csv.writer(f)
        wr.writerow(wcols)
        for s in stalls:
            wr.writerow([json.dumps(s[c]) if c == "log" else
                         (round(s[c], 3) if isinstance(s[c], float) else s[c]) for c in wcols])
    return res


def fmt(v, nd=2):
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def print_report(res):
    print(f"\n=== {res['run']}  ({res['rows']} perf rows, {res['run_seconds']} s of frames; "
          f"H0 row {res['h0_row']}, first 3D row {res['first3d_row']})")
    print("  " + res["t0_note"])
    print(f"  frames > {res['threshold_ms']:.0f} ms: {res['stall_count']} totalling {res['stall_time_s']} s; "
          f"by class {res['by_class']}")
    print(f"  pipeline misses total {res['pipe_miss_total']}, texture misses total {res['tex_miss_total']}")
    print(f"  frames with pipeline miss : {res['frames_with_pipe_miss']}")
    print(f"  frames with tex miss only : {res['frames_with_tex_miss_only']}")
    print(f"  frames without any miss   : {res['frames_without_miss']}")
    print("  EVENTS (stall frames within 5 rows; pm/tm/excess over rows first-2..last+2; excess vs 30-frame median before)")
    print("    " + " ".join(f"{h:>9}" for h in ("rows", "wall", "t_s", "H0+s", "sig", "frames", "stall_s",
                                               "excess_s", "max_ms", "pm", "tm", "cb_max", "ms/pm", "cls")))
    for ev in res["events"]:
        vals = (f"{ev['first']}-{ev['last']}", ev["wall"][3:], fmt(ev["t_start"]), fmt(ev["h0_rel"]), ev["sig"],
                len([1 for s in res["stalls"] if ev["first"] <= s["row"] <= ev["last"]]), ev["stall_s"],
                ev["excess_s"], ev["max_ms"], ev["pm"], ev["tm"], ev["cb_max"], fmt(ev["ms_per_pm"], 1),
                ev["classes"])
        print("    " + " ".join(f"{str(v):>9}" for v in vals))
    print("  FRAMES")
    hdr = ("row", "wall", "t_s", "+-s", "H0+s", "ms", "cls", "draws", "verts", "pm", "pm2", "tm", "tm2",
           "cbst", "pipe_h", "cores", "privMB")
    print("    " + " ".join(f"{h:>8}" for h in hdr))
    for s in res["stalls"]:
        vals = (s["row"], s["wall_start"][3:], fmt(s["t_start"]), fmt(s["align_width_s"]), fmt(s["h0_rel"]),
                f"{s['frame_ms']:.0f}", s["cls"], s["draws"], s["verts"], s["pipe_m"], s["pipe_m_pm2"],
                s["tex_m"], s["tex_m_pm2"], s["cb_stalls"], s["pipe_h"],
                fmt(s["cores"]), f"{fmt(s['priv_mb_before'], 0)}->{fmt(s['priv_mb_after'], 0)}")
        print("    " + " ".join(f"{str(v):>8}" for v in vals))
        for c, d in s["log"].items():
            print(f"             log {c}: n={d['n']} tids={d['tids']} first@{d['first_t']:+.2f}s {d['first'][:80]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--threshold-ms", type=float, default=250.0)
    ap.add_argument("--log-window-s", type=float, default=2.0)
    ap.add_argument("--out-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"))
    a = ap.parse_args()
    for r in a.runs:
        print_report(analyze(r, a.threshold_ms, a.log_window_s, a.out_dir))


if __name__ == "__main__":
    main()

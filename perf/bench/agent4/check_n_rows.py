#!/usr/bin/env python3
"""Agent 4 functional checks for the threaded native rows N1-N3 (S2.12, S3 task #3).

Reads finished run dirs only (game.log, run.json, frames.json, headroom.json,
threads.csv, proc.csv, summary.txt). Starts nothing, writes only --json.

Usage:
  python bench/agent4/check_n_rows.py --baseline DIR [DIR ...] --rows ROW=RUNDIR [ROW=RUNDIR ...]
         [--json OUT] [--examples N]

ROW is n1, n2 or n3. Baselines are non-threaded native n0 runs on the same bin
(window 3: build/agent8/matrix/20261122-0013/runs/{0016-cold-n0,0030-n0-r1,...}).

Expectations (from the code, draw.cpp / native_worker.cpp at draw.cpp SHA 50AA3B1D):
  all rows : 'Native GPU: threaded recording ON (LEGO_NATIVE_THREADED=1)' once
             'Native worker: last 600 frames' about once per 600 presents
             no warning/error type that the baselines never log
             no baseline warning type at > 2x the baseline max (and > max+4)
             run.json status OK, env as listed, clean close
  n1       : 'Native draw batches: serial workers=0'; worker thread 'Native GPU recording'
  n2       : 'Native draw batches: parallel workers=2'; worker thread 'Native GPU preparation'
  n3       : no 'Native draw batches' line at all: with LEGO_NATIVE_FULL_DRAW_PREPARATION=1
             the worker runs CoordinatorMain (native_worker.cpp:260) and draws go to
             CaptureFullDraw (draw.cpp:5177/5206), so NativeParallelDrawsEnabled(), whose
             one-time initializer prints the line (draw.cpp:5572-5583), is never called.
             The mode shows in threads.csv instead: 'Native GPU preparation' (coordinator),
             'Native GPU recording' (recorder, native_worker.cpp:346), 'Native GPU prepare N'.
Exit code: 0 if every row passes, 1 otherwise, 2 on usage errors.
"""
import argparse
import csv
import json
import math
import os
import re
import sys
from collections import Counter, OrderedDict

THREADED_ON = "Native GPU: threaded recording ON (LEGO_NATIVE_THREADED=1)"
BATCHES_RE = re.compile(r"Native draw batches: (\w+) workers=(\d+)")
WORKER_RE = re.compile(r"Native worker: last 600 frames tasks=(\d+) inline=(\d+) drains=(\d+) "
                       r"drain_wait=([\d.]+)ms throttle_wait=([\d.]+)ms")
LEVEL_RE = re.compile(r"^\[[^\]]*\] \[(warning|error|critical)\] \[(\w+)\] (?:\[t\d+\] )?(.*)$")

EXPECT = {
    "n1": {"batches": "serial workers=0",
           "env": {"LEGO_NATIVE_THREADED": "1"},
           "env_absent": ["LEGO_NATIVE_PREPARE_THREADS", "LEGO_NATIVE_FULL_DRAW_PREPARATION"],
           "threads_present": ["Native GPU recording"],
           "threads_absent": ["Native GPU preparation"]},
    "n2": {"batches": "parallel workers=2",
           "env": {"LEGO_NATIVE_THREADED": "1", "LEGO_NATIVE_PREPARE_THREADS": "2",
                   "LEGO_NATIVE_SNAPSHOT_STATE": "1"},
           "env_absent": ["LEGO_NATIVE_FULL_DRAW_PREPARATION"],
           "threads_present": ["Native GPU preparation"],
           "threads_absent": []},
    "n3": {"batches": None,
           "env": {"LEGO_NATIVE_THREADED": "1", "LEGO_NATIVE_PREPARE_THREADS": "2",
                   "LEGO_NATIVE_FULL_DRAW_PREPARATION": "1"},
           "env_absent": [],
           "threads_present": ["Native GPU preparation", "Native GPU recording", "Native GPU prepare"],
           "threads_absent": []},
}


def normalize(message):
    m = re.sub(r"0x[0-9A-Fa-f]+", "X", message)
    m = re.sub(r"\b[0-9A-Fa-f]{8,}\b", "H", m)
    m = re.sub(r"\d+(\.\d+)?", "#", m)
    return m


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def read_json(path):
    text = read_text(path)
    if text is None:
        return None
    try:
        return json.loads(text.lstrip("\ufeff"))
    except ValueError:
        return None


def scan_log(run):
    """Key lines and warning/error type counts over game.log and its rotations.

    The game log rotates at 5 MB and keeps 2 files (Agent 8, S3): read
    game.2.log/game.1.log (older) before game.log. If the first file does not
    start with the boot lines, earlier lines were lost: 'boot_lines_lost'.
    """
    out = {"exists": False, "files": [], "lines": 0, "threaded_on": 0, "threaded_off": 0, "batches": [],
           "worker_lines": 0, "worker_stats": [], "types": Counter(), "examples": {},
           "boot_lines_lost": False}
    paths = [os.path.join(run, n) for n in ("game.2.log", "game.1.log", "game.log")]
    paths = [p for p in paths if os.path.isfile(p)]
    if not paths:
        return out
    out["exists"] = True
    for path in paths:
        out["files"].append(f"{os.path.basename(path)} {os.path.getsize(path)} B")
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for number, raw in enumerate(f, 1):
                scan_line(out, raw, f"{os.path.basename(path)}:{number}", first=(path == paths[0] and number <= 3))
    if len(paths) > 1 and out["threaded_on"] == 0 and out["threaded_off"] == 0:
        out["boot_lines_lost"] = True
    return out


def scan_line(out, raw, where, first=False):
    line = raw.rstrip("\r\n")
    out["lines"] += 1
    if THREADED_ON in line:
        out["threaded_on"] += 1
    elif "Native GPU: threaded recording off" in line:
        out["threaded_off"] += 1
    b = BATCHES_RE.search(line)
    if b:
        out["batches"].append(f"{b.group(1)} workers={b.group(2)}")
    w = WORKER_RE.search(line)
    if w:
        out["worker_lines"] += 1
        out["worker_stats"].append([float(x) for x in w.groups()])
    lv = LEVEL_RE.match(line)
    if lv:
        key = f"[{lv.group(1)}] [{lv.group(2)}] {normalize(lv.group(3))}"
        out["types"][key] += 1
        if key not in out["examples"]:
            out["examples"][key] = f"{where}: {line[:240]}"


def thread_names(run):
    names = Counter()
    path = os.path.join(run, "threads.csv")
    if not os.path.isfile(path):
        return names, None
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        names[(r.get("name") or "").strip()] += 1
    return names, rows


def proc_peaks(run):
    """Peak thread count from proc.csv if it has a thread column."""
    path = os.path.join(run, "proc.csv")
    if not os.path.isfile(path):
        return None
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        cols = [c for c in (reader.fieldnames or []) if c and "thread" in c.lower()]
        if not cols:
            return None
        peak = None
        for r in reader:
            try:
                v = float(r[cols[0]])
            except (TypeError, ValueError):
                continue
            peak = v if peak is None else max(peak, v)
    return {"column": cols[0], "peak": peak}


def env_map(run_json):
    env = {}
    for item in ((run_json or {}).get("params") or {}).get("env") or []:
        if "=" in item:
            k, v = item.split("=", 1)
            env[k] = v
    return env


def check_run(row, run, baseline_types, baseline_max, examples_n):
    exp = EXPECT[row]
    res = OrderedDict(row=row, run=run, checks=[], info=OrderedDict())

    def check(name, ok, detail):
        res["checks"].append({"check": name, "ok": bool(ok), "detail": detail})

    rj = read_json(os.path.join(run, "run.json"))
    fj = read_json(os.path.join(run, "frames.json"))
    hj = read_json(os.path.join(run, "headroom.json"))
    summary = read_text(os.path.join(run, "summary.txt")) or ""
    log = scan_log(run)

    check("run.json status OK", rj is not None and rj.get("status") == "OK" and not rj.get("problems")
          and not rj.get("runner_error"),
          "missing" if rj is None else f"status={rj.get('status')} problems={rj.get('problems')} "
                                      f"runner_error={rj.get('runner_error')}")
    env = env_map(rj)
    bad_env = [f"{k}={env.get(k)!r} (want {v})" for k, v in exp["env"].items() if env.get(k) != v]
    bad_env += [f"{k} set ({env[k]})" for k in exp["env_absent"] if k in env]
    check("env as expected", not bad_env, "ok" if not bad_env else "; ".join(bad_env))
    check("game.log present, boot lines kept", log["exists"] and not log["boot_lines_lost"],
          f"{log['lines']} lines in {', '.join(log['files']) or 'no file'}"
          + ("; BOOT LINES LOST to rotation" if log["boot_lines_lost"] else ""))
    check("threaded recording ON once", log["threaded_on"] == 1 and log["threaded_off"] == 0,
          f"ON lines={log['threaded_on']} off lines={log['threaded_off']}")
    if exp["batches"] is None:
        check("no 'Native draw batches' line (full-prep path)", not log["batches"],
              f"found {log['batches']}" if log["batches"] else "absent, as the code predicts")
    else:
        check(f"'Native draw batches: {exp['batches']}'", log["batches"] == [exp["batches"]],
              f"found {log['batches'] or 'none'}")
    presents = (fj or {}).get("rows_total")
    if presents:
        want = presents / 600.0
        check("worker line per 600 presents", abs(log["worker_lines"] - want) <= 1.5,
              f"{log['worker_lines']} lines for {presents} presents (expect ~{want:.1f})")
    else:
        check("worker line per 600 presents", log["worker_lines"] > 0,
              f"{log['worker_lines']} lines (no frames.json rows_total)")
    names, _ = thread_names(run)
    missing = [n for n in exp["threads_present"] if not any(k.startswith(n) for k in names)]
    present = [n for n in exp["threads_absent"] if any(k.startswith(n) for k in names)]
    check("worker thread names", not missing and not present,
          ("ok: " + ", ".join(sorted(k for k in names if k.startswith("Native GPU"))))
          if not missing and not present else f"missing={missing} unexpected={present}")

    new = []
    increased = []
    for key, count in log["types"].most_common():
        if key not in baseline_types:
            new.append((key, count))
        else:
            bmax = baseline_max[key]
            if count > max(2 * bmax, bmax + 4):
                increased.append((key, count, bmax))
    check("no new warning/error types vs n0", not new,
          "none" if not new else "; ".join(f"{c}x {k}" for k, c in new[:examples_n]))
    check("no baseline warning type > 2x n0 max", not increased,
          "none" if not increased else "; ".join(f"{c}x (n0 max {b}) {k}" for k, c, b in increased[:examples_n]))
    res["new_types"] = [{"type": k, "count": c, "first": log["examples"][k]} for k, c in new]
    res["increased_types"] = [{"type": k, "count": c, "n0_max": b, "first": log["examples"][k]}
                              for k, c, b in increased]

    m = re.search(r"exit seen after ([\d.]+) s, killed (\w+), exit (0x[0-9A-Fa-f]+)", summary)
    check("clean close", bool(m) and m.group(2) == "False" and int(m.group(3), 16) == 0,
          m.group(0) if m else "no close line in summary.txt")

    cores = re.search(r"window cpu mean ([\d.]+) cores, max ([\d.]+) cores", summary)
    info = res["info"]
    info["cpu_cores_mean"] = float(cores.group(1)) if cores else None
    info["cpu_cores_max"] = float(cores.group(2)) if cores else None
    info["threads_seen"] = (hj or {}).get("threads")
    pk = proc_peaks(run)
    info["peak_threads_proc_csv"] = pk["peak"] if pk else None
    info["top_threads"] = [f"{t.get('name') or t.get('tid')} {t.get('busy_pct')}%" for t in ((hj or {}).get("top") or [])[:5]]
    info["gpu_util_mean"] = ((hj or {}).get("gpu") or {}).get("util_mean")
    if fj:
        info["window_frames"] = fj.get("frames")
        info["mean_fps_not_timing"] = fj.get("mean_fps")
        info["median_ms_not_timing"] = fj.get("median_ms")
        info["p99_ms_not_timing"] = fj.get("p99_ms")
    if log["worker_stats"]:
        cols = list(zip(*log["worker_stats"]))
        info["worker_mean_per_600"] = {n: round(sum(c) / len(c), 1) for n, c in
                                       zip(["tasks", "inline", "drains", "drain_wait_ms", "throttle_wait_ms"], cols)}
    info["valid_timing"] = (rj or {}).get("valid_timing")
    info["warning_lines_total"] = sum(log["types"].values())
    res["pass"] = all(c["ok"] for c in res["checks"])
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--baseline", nargs="+", required=True, help="n0 run dirs (non-threaded native, same bin)")
    ap.add_argument("--rows", nargs="+", required=True, help="ROW=RUNDIR with ROW in n1,n2,n3")
    ap.add_argument("--json", help="write the full result here")
    ap.add_argument("--examples", type=int, default=6)
    a = ap.parse_args()

    baseline_types = set()
    baseline_max = Counter()
    base_info = []
    for d in a.baseline:
        log = scan_log(d)
        if not log["exists"]:
            print(f"baseline {d}: no game.log", file=sys.stderr)
            return 2
        base_info.append({"run": d, "lines": log["lines"], "warning_lines": sum(log["types"].values()),
                          "threaded_on": log["threaded_on"], "batches": log["batches"]})
        for k, c in log["types"].items():
            baseline_types.add(k)
            baseline_max[k] = max(baseline_max[k], c)

    results = []
    for spec in a.rows:
        if "=" not in spec:
            print(f"bad row spec {spec!r} (want ROW=RUNDIR)", file=sys.stderr)
            return 2
        row, run = spec.split("=", 1)
        if row not in EXPECT:
            print(f"unknown row {row!r} (want n1, n2 or n3)", file=sys.stderr)
            return 2
        results.append(check_run(row, run, baseline_types, baseline_max, a.examples))

    print(f"baseline: {len(a.baseline)} n0 runs, {len(baseline_types)} warning/error types")
    for b in base_info:
        print(f"  {os.path.basename(b['run'])}: {b['lines']} lines, {b['warning_lines']} warning/error lines, "
              f"threaded_on={b['threaded_on']}, batches={b['batches'] or 'none'}")
    for r in results:
        print(f"\n== {r['row']} {'PASS' if r['pass'] else 'FAIL'}  {r['run']}")
        for c in r["checks"]:
            print(f"  [{'ok' if c['ok'] else 'FAIL'}] {c['check']}: {c['detail']}")
        for t in r["new_types"][:a.examples]:
            print(f"    new: {t['count']}x {t['type']}\n         first {t['first']}")
        for t in r["increased_types"][:a.examples]:
            print(f"    up : {t['count']}x (n0 max {t['n0_max']}) {t['type']}")
        print("  info: " + json.dumps(r["info"]))
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({"baseline": base_info, "rows": results}, f, indent=2)
    return 0 if all(r["pass"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())

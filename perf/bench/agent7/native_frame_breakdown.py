#!/usr/bin/env python3
"""Per-frame breakdown of native-frames.csv over the runner's measure window (Agent 7).

usage: python bench/agent7/native_frame_breakdown.py RUN_DIR [RUN_DIR ...]
           [--window bytes|seconds] [--all] [-o OUT.txt]

For each run dir: frames.json `window` gives the 0-based first data row of
native-frames.csv (`first_row`) and the row count, either the measure window by
CSV bytes (`rows_by_end_bytes`, default: this is the window the profile trigger
covers when profile_s == measure_s) or the first `seconds` of frame time
(`rows`). Prints the window mean and p50 of every numeric column, then the median
of the per-run means across runs. Columns that are 0 in every window row are
listed on one line (they are not measured in this build/config, or idle).

Stdlib only; one thread.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import sys

SKIP = {"frame"}
# Shown first, in this order, when present (the rest follow by mean, descending).
LEAD = ("interval_ms", "swap_present_cpu_ms", "present_cpu_ms", "present_submit_cpu_ms",
        "acquire_cpu_ms", "frame_slot_wait_ms", "sync_ms", "texture_ms", "constants_ms",
        "vertices_ms", "buffer_hash_ms", "bindings_ms", "begin_ms", "pipeline_ms", "issue_ms",
        "tail_ms", "pipeline_creation_ms", "draw_calls", "buffer_watch_hits",
        "buffer_watch_audits", "buffer_watch_mismatches", "texture_hash_bytes",
        "buffer_hash_bytes", "buffer_converted_bytes", "detailed_timing_enabled")


def load_window(run_dir: str, mode: str):
    with open(os.path.join(run_dir, "frames.json"), encoding="utf-8-sig") as f:
        fj = json.load(f)
    w = fj.get("window") or {}
    first = w.get("first_row")
    n = w.get("rows_by_end_bytes") if mode == "bytes" else w.get("rows")
    if first is None or not n:
        raise SystemExit(f"{run_dir}: frames.json has no usable window ({mode})")
    return fj, int(first), int(n)


def read_rows(path: str):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rd = csv.reader(f)
        head = next(rd)
        rows = [r for r in rd if r and len(r) == len(head)]
    return head, rows


def num(x: str):
    try:
        return float(x)
    except ValueError:
        return None


def breakdown(run_dir: str, mode: str):
    fj, first, n = load_window(run_dir, mode)
    src = fj.get("source")
    path = os.path.join(run_dir, "native-frames.csv")
    if src != "native" or not os.path.isfile(path):
        raise SystemExit(f"{run_dir}: no native-frames.csv window (frames.json source={src})")
    head, rows = read_rows(path)
    win = rows[first:first + n]
    if len(win) < n:
        print(f"warning: {run_dir}: window wants {n} rows from {first}, file has {len(win)}",
              file=sys.stderr)
    out = {}
    for k, col in enumerate(head):
        if col in SKIP:
            continue
        vals = [num(r[k]) for r in win]
        vals = [v for v in vals if v is not None]
        if not vals:
            continue
        out[col] = (statistics.fmean(vals), statistics.median(vals), max(vals))
    t = sum(v for v in (num(r[head.index("interval_ms")]) for r in win) if v) / 1000.0
    return {"run": os.path.basename(os.path.normpath(run_dir)), "rows": len(win), "first": first,
            "seconds": t, "fps": len(win) / t if t else 0.0, "cols": out, "order": head}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("runs", nargs="+")
    p.add_argument("--window", choices=("bytes", "seconds"), default="bytes")
    p.add_argument("--all", action="store_true", help="also list all-zero columns one per row")
    p.add_argument("-o", "--output")
    a = p.parse_args(argv)
    res = [breakdown(r, a.window) for r in a.runs]
    cols = []
    for r in res:
        for c in r["order"]:
            if c in r["cols"] and c not in cols:
                cols.append(c)
    zero = [c for c in cols if all(r["cols"].get(c, (0, 0, 0))[2] == 0 for r in res)]
    live = [c for c in cols if c not in zero]
    med = {c: statistics.median([r["cols"][c][0] for r in res if c in r["cols"]]) for c in live}
    lead = [c for c in LEAD if c in live]
    rest = sorted((c for c in live if c not in lead), key=lambda c: -med[c])
    L = [f"native-frames.csv window breakdown ({a.window} window; mean over window rows; "
         f"'med' = median of the per-run means)"]
    for r in res:
        L.append(f"  {r['run']}: rows {r['first']}..{r['first'] + r['rows'] - 1} "
                 f"({r['rows']} frames, {r['seconds']:.1f} s, {r['fps']:.2f} fps)")
    w = max([len(c) for c in live] + [6])
    hdr = f"{'column':<{w}}  {'med':>10}  " + "  ".join(f"{r['run'][:14]:>14}" for r in res)
    L += ["", hdr, "-" * len(hdr)]
    for c in lead + rest:
        cells = []
        for r in res:
            v = r["cols"].get(c)
            cells.append(f"{v[0]:>8.4f}/{v[1]:<5.3g}" if v else f"{'-':>14}")
        L.append(f"{c:<{w}}  {med[c]:>10.4f}  " + "  ".join(f"{x:>14}" for x in cells))
    L += ["", "cells: window mean/p50. all-zero in every window: " + (", ".join(zero) or "(none)")]
    text = "\n".join(L) + "\n"
    if a.output:
        os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
        with open(a.output, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

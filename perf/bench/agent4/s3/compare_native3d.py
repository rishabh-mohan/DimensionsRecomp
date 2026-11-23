#!/usr/bin/env python3
"""Agent 4, task #12 step 3: compare the native3d functional rows with the same rows on native2.

Reads finished run dirs only; starts nothing; writes only --json.

    python bench/agent4/s3/compare_native3d.py --new n0=DIR n2=DIR n3=DIR [--old ROW=DIR[;DIR...] ...] [--json OUT]

Old (native2-bin, draw.cpp batch 2) defaults:
  n0: window 3's n0 runs (build/agent8/matrix/20261122-0013/runs/{0016-cold-n0,0030-n0-r1,0042-n0-r2,0054-n0-r3,0104-n0-r4})
  n2: S3's N2 (build/agent8/matrix/s3-n2-0210/runs/0210-n2-r1)
  n3: S3's N3 (build/agent8/matrix/s3-n123-0205/runs/0208-n3-r1)

Per run: hash=0 cache-miss lines (and per present), other cache misses, warning/error types (normalized as in
check_n_rows.py), 'Native worker: last 600 frames' tasks (draws per frame), the draw-batches and presentation lines,
frames.json (not timing), CPU cores, the close line, the bin, and whether MANIFEST.txt names draw.cpp 5EA1F357.
Expected (task #12, Agent 1 and Agent 10): n2/n3 have no hash=0 line; n0 is unchanged; no new warning type;
draws per frame unchanged.
"""
import argparse
import json
import os
import re
import statistics
import sys
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import check_n_rows as cnr  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
M = os.path.join(ROOT, "build", "agent8", "matrix")
OLD = {
    "n0": [os.path.join(M, "20261122-0013", "runs", d)
           for d in ("0016-cold-n0", "0030-n0-r1", "0042-n0-r2", "0054-n0-r3", "0104-n0-r4")],
    "n2": [os.path.join(M, "s3-n2-0210", "runs", "0210-n2-r1")],
    "n3": [os.path.join(M, "s3-n123-0205", "runs", "0208-n3-r1")],
}
HASH0 = "Native GPU shader cache miss: hash=0x0000000000000000"
MISS_RE = re.compile(r"Native GPU shader cache miss: hash=0x([0-9A-Fa-f]{16})")
STAMP_RE = re.compile(r"^\[[^\]]*\] \[\w+\] \[\w+\] (?:\[t\d+\] )?")
DRAW_S33 = "5EA1F3576DCC2F90C7CBE410CFCDE093CB39D170A2BDD6259C3A85B41BE14410"


def run_metrics(run):
    out = OrderedDict(run=run)
    log = cnr.scan_log(run)
    hash0 = 0
    other = Counter()
    batches_lines, presentation = [], []
    for name in ("game.2.log", "game.1.log", "game.log"):
        path = os.path.join(run, name)
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for raw in f:
                if "shader cache miss" in raw:
                    if HASH0 in raw:
                        hash0 += 1
                    else:
                        m = MISS_RE.search(raw)
                        if m:
                            other[m.group(1).upper()] += 1
                if "Native draw batches" in raw:
                    batches_lines.append(STAMP_RE.sub("", raw.strip()))
                elif "Native presentation" in raw:
                    presentation.append(STAMP_RE.sub("", raw.strip()))
    fj = cnr.read_json(os.path.join(run, "frames.json")) or {}
    rj = cnr.read_json(os.path.join(run, "run.json")) or {}
    summary = cnr.read_text(os.path.join(run, "summary.txt")) or ""
    manifest = cnr.read_text(os.path.join(run, "MANIFEST.txt")) or ""
    presents = fj.get("rows_total")
    out["status"] = rj.get("status")
    out["bin"] = os.path.basename(rj.get("bin_dir") or "?")
    out["manifest_names_draw_5EA1F357"] = DRAW_S33 in manifest.upper() if manifest else None
    out["log_files"] = log["files"]
    out["boot_lines_lost"] = log["boot_lines_lost"]
    out["presents"] = presents
    out["hash0_lines"] = hash0
    out["hash0_per_present"] = round(hash0 / presents, 3) if presents else None
    out["other_miss_lines"] = sum(other.values())
    out["other_miss_hashes"] = len(other)
    out["warning_lines"] = sum(log["types"].values())
    out["types"] = dict(log["types"])
    tasks = [s[0] for s in log["worker_stats"]]
    out["worker_lines"] = len(tasks)
    if tasks:
        per_frame = [t / 600.0 for t in tasks]
        out["draws_per_frame"] = {"median": round(statistics.median(per_frame), 2),
                                  "min": round(min(per_frame), 2), "max": round(max(per_frame), 2),
                                  "values_x600": dict(Counter(int(t) for t in tasks).most_common(6))}
    else:
        out["draws_per_frame"] = None
    out["batches"] = batches_lines
    out["presentation"] = presentation[:2]
    out["fps_not_timing"] = fj.get("mean_fps")
    out["median_ms_not_timing"] = fj.get("median_ms")
    out["p99_ms_not_timing"] = fj.get("p99_ms")
    cores = re.search(r"window cpu mean ([\d.]+) cores, max ([\d.]+) cores", summary)
    out["cores_mean_max"] = [float(cores.group(1)), float(cores.group(2))] if cores else None
    close = re.search(r"exit seen after ([\d.]+) s, killed (\w+), exit (0x[0-9A-Fa-f]+)", summary)
    out["close"] = close.group(0) if close else None
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--new", nargs="+", required=True, help="ROW=RUNDIR (native3d), ROW in n0, n2, n3")
    ap.add_argument("--old", nargs="*", default=[], help="ROW=DIR[;DIR...] to override the native2 defaults")
    ap.add_argument("--json")
    a = ap.parse_args()
    old = dict(OLD)
    for spec in a.old:
        row, dirs = spec.split("=", 1)
        old[row] = dirs.split(";")
    new = OrderedDict()
    for spec in a.new:
        if "=" not in spec:
            print(f"bad --new {spec!r}", file=sys.stderr)
            return 2
        row, run = spec.split("=", 1)
        new[row] = run

    result = OrderedDict()
    ok_all = True
    for row, run in new.items():
        nm = run_metrics(run)
        om = [run_metrics(d) for d in old.get(row, [])]
        old_types = set().union(*(set(m["types"]) for m in om)) if om else set()
        new_types = sorted(set(nm["types"]) - old_types)
        gone_types = sorted(old_types - set(nm["types"]))
        checks = OrderedDict()
        checks["status OK"] = nm["status"] == "OK"
        checks["bin native3d-bin"] = nm["bin"] == "native3d-bin"
        checks["no hash=0 line"] = nm["hash0_lines"] == 0
        checks["no type absent from the native2 run(s)"] = not new_types
        if om and nm["draws_per_frame"] and all(m["draws_per_frame"] for m in om):
            # The light/heavy title phases give different values, and the runs have different warm-ups,
            # so the median is checked against the native2 per-line range, not its median.
            lo = min(m["draws_per_frame"]["min"] for m in om) - 0.5
            hi = max(m["draws_per_frame"]["max"] for m in om) + 0.5
            checks["draws/frame median within the native2 per-line range"] = (
                lo <= nm["draws_per_frame"]["median"] <= hi)
        if nm["presentation"] and om and om[0]["presentation"]:
            # focus= depends on which desktop the run had, not on the build.
            def unfocused(line):
                return re.sub(r" focus=\w+", "", line)
            checks["presentation line as native2 (focus= ignored)"] = (
                unfocused(nm["presentation"][0]) == unfocused(om[0]["presentation"][0]))
        ok = all(checks.values())
        ok_all &= ok
        result[row] = OrderedDict(new=nm, old=om, new_types=new_types, gone_types=gone_types,
                                  checks=checks, ok=ok)
        print(f"\n== {row} {'OK' if ok else 'CHECK'}  {run}")
        for k, v in checks.items():
            print(f"  [{'ok' if v else 'NO'}] {k}")
        print(f"  hash=0 lines: native3d {nm['hash0_lines']} ({nm['hash0_per_present']}/present over "
              f"{nm['presents']} presents); native2 " + ", ".join(
                  f"{m['hash0_lines']} ({m['hash0_per_present']}/present)" for m in om))
        print(f"  other cache-miss lines: native3d {nm['other_miss_lines']} ({nm['other_miss_hashes']} hashes); native2 "
              + ", ".join(f"{m['other_miss_lines']} ({m['other_miss_hashes']})" for m in om))
        print(f"  warning/error lines: native3d {nm['warning_lines']}; native2 "
              + ", ".join(str(m["warning_lines"]) for m in om))
        for t in new_types:
            print(f"    new type: {nm['types'][t]}x {t}")
        for t in gone_types:
            print(f"    gone    : {t}")
        print(f"  draws/frame (worker tasks/600): native3d {nm['draws_per_frame']}; native2 "
              + "; ".join(str(m["draws_per_frame"]) for m in om))
        print(f"  batches: native3d {nm['batches'] or 'none'}; native2 {om[0]['batches'] if om else '?'}")
        print(f"  presentation: native3d {nm['presentation'][:1]}")
        print(f"  info (not timing): fps {nm['fps_not_timing']} median {nm['median_ms_not_timing']} ms "
              f"p99 {nm['p99_ms_not_timing']} ms; cores {nm['cores_mean_max']}; close {nm['close']}; "
              f"MANIFEST names 5EA1F357: {nm['manifest_names_draw_5EA1F357']}; logs {nm['log_files']}")
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
    print("\ncompare:", "OK" if ok_all else "CHECK")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())

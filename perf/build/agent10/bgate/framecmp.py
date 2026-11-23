#!/usr/bin/env python3
"""Agent 10, B gate: per-frame evidence of whether the game acted on the route's menu presses.

Read-only. For each run dir: perf.csv (per frame) + route-report.txt (press rows with perf time).
Prints, per press: xma frames decoded, functions_dispatched and draw/vertex pairs in the press window
against the 1.5 s before it; then the xma bursts and the draw/vertex run-length timeline after --from.
Usage: python framecmp.py [--from 60] <run dir> [<run dir> ...]
"""
import csv
import re
import statistics
import sys

ROW = re.compile(r"\s*([\d.]+)\s+L(\d+)\s+(\w+)\s+(.*?)->.*?\|\s*perf\s+([\d.]+)")


def load(run):
    out, t = [], 0.0
    with open(run + "/perf.csv", newline="") as f:
        for r in csv.DictReader(f):
            t += int(r["frame_time_us"]) / 1e6
            out.append((t, {k: int(float(v)) for k, v in r.items()}))
    return out


def steps(run):
    res = []
    with open(run + "/route-report.txt", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = ROW.match(line)
            if m:
                res.append((float(m.group(1)), int(m.group(2)), m.group(3), m.group(4).strip(), float(m.group(5))))
    return res


def window(frames, a, b):
    return [r for t, r in frames if a <= t < b]


def summ(rows):
    if not rows:
        return "no frames"
    xma = sum(r["xma_frames_decoded"] for r in rows)
    fd = [r["functions_dispatched"] for r in rows]
    pairs = {}
    for r in rows:
        k = (r["draw_calls"], r["vertices_processed"])
        pairs[k] = pairs.get(k, 0) + 1
    top = sorted(pairs.items(), key=lambda kv: -kv[1])[:3]
    return "n=%3d xma=%4d fd med/max=%5d/%5d pairs=%s" % (
        len(rows), xma, statistics.median(fd), max(fd), " ".join("%d/%d:%d" % (k[0], k[1], v) for k, v in top))


def main(argv):
    start = 60.0
    if argv[:1] == ["--from"]:
        start, argv = float(argv[1]), argv[2:]
    for run in argv:
        frames, st = load(run), steps(run)
        print("=" * 100)
        print("RUN", run, "| frames", len(frames), "| perf end %.1f" % frames[-1][0])
        prev = None
        print("-- presses: window = (previous row's perf, press row's perf + 1.5 s); before = the 1.5 s before")
        for s in st:
            if s[2] == "press" and prev is not None:
                a, b = prev[4], s[4] + 1.5
                print("  L%-3d %-8s perf %6.1f | in:  %s" % (s[1], s[3], s[4], summ(window(frames, a, b))))
                print("  %-14s %6s | pre: %s" % ("", "", summ(window(frames, a - 1.5, a))))
            prev = s
        print("-- xma bursts (frames with xma_frames_decoded > 0; gap > 0.5 s splits)")
        bursts, cur = [], None
        for t, r in frames:
            if r["xma_frames_decoded"] > 0:
                if cur and t - cur[1] <= 0.5:
                    cur[1], cur[2], cur[3] = t, cur[2] + 1, cur[3] + r["xma_frames_decoded"]
                else:
                    cur = [t, t, 1, r["xma_frames_decoded"]]
                    bursts.append(cur)
        for b0, b1, n, tot in bursts:
            print("  %7.2f-%7.2f frames %4d xma %5d" % (b0, b1, n, tot))
        print("-- draw/vertex runs from perf %.0f (runs < 30 frames marked *)" % start)
        runs, cur = [], None
        for t, r in frames:
            if t < start:
                continue
            k = (r["draw_calls"], r["vertices_processed"])
            if cur and cur[0] == k:
                cur[2], cur[3] = t, cur[3] + 1
            else:
                cur = [k, t, t, 1]
                runs.append(cur)
        for k, t0, t1, n in runs:
            print("  %s %7.2f-%7.2f %5d frames  %d/%d" % ("*" if n < 30 else " ", t0, t1, n, k[0], k[1]))


if __name__ == "__main__":
    main(sys.argv[1:])

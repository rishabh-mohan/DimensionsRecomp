#!/usr/bin/env python3
"""framealign: estimate when given frames.csv rows were presented, in log time.

Usage: framealign.py RUNDIR --frames N [N ...]
Method: cumulative interval_ms gives time since the first frame; samples.csv
(harness t_s, frames_csv_bytes) gives how many rows existed at each sample,
which calibrates the harness time of the first frame (median over samples,
since flushing only delays rows). Harness time is converted to log time with
run.json close_sent_s and the log's "Window closing" line. Read-only.
"""
import argparse, csv, json, os, re, statistics, sys
from datetime import datetime

TS = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\]')


def ts(line):
    m = TS.match(line)
    return datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S.%f') if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run')
    ap.add_argument('--frames', nargs='+', type=int, required=True)
    a = ap.parse_args()
    fp = os.path.join(a.run, 'frames.csv')
    with open(fp, 'rb') as f:
        raw = f.read()
    lines = raw.split(b'\n')
    header = lines[0].decode().strip().split(',')
    ii = header.index('interval_ms')
    ends = []          # byte offset after each data row
    cum = []           # ms since the first data row
    off = len(lines[0]) + 1
    t = 0.0
    for i, ln in enumerate(lines[1:]):
        if not ln.strip():
            off += len(ln) + 1
            continue
        cols = ln.decode('utf-8', 'replace').split(',')
        if i > 0:
            try:
                t += float(cols[ii])
            except Exception:
                pass
        cum.append(t)
        off += len(ln) + 1
        ends.append(off)
    # calibrate with samples.csv
    offs = []
    with open(os.path.join(a.run, 'samples.csv'), newline='') as f:
        for r in csv.DictReader(f):
            try:
                tb = float(r['t_s']); nb = int(r['frames_csv_bytes'])
            except Exception:
                continue
            # rows complete at this sample
            lo, hi = 0, len(ends)
            while lo < hi:
                mid = (lo + hi) // 2
                if ends[mid] <= nb:
                    lo = mid + 1
                else:
                    hi = mid
            n = lo
            if n < 2:
                continue
            offs.append((tb - cum[n - 1] / 1000.0, tb, n))
    # rows can only appear late, so the smallest offsets are the tightest
    o_sorted = sorted(x[0] for x in offs)
    o_min = o_sorted[0]
    o_p10 = o_sorted[len(o_sorted) // 10]
    o_med = statistics.median(o_sorted)
    with open(os.path.join(a.run, 'run.json'), encoding='utf-8-sig') as f:
        j = json.load(f)
    close_s = float(j.get('close_sent_s'))
    log = open(os.path.join(a.run, 'game.log'), encoding='utf-8', errors='replace').read().splitlines()
    t0 = ts(log[0])
    tclose = next(ts(l) for l in log if 'Window closing' in l)
    h2l = (tclose - t0).total_seconds() - close_s   # log_rel = harness + h2l (upper bound)
    print('run %s: %d frame rows, %d calibration samples' % (a.run, len(cum), len(offs)))
    print('first-frame harness time: min %.2f s, p10 %.2f s, median %.2f s (rows only appear late, so min/p10 are tighter)' % (o_min, o_p10, o_med))
    print('harness->log offset: %+.2f s (WM_CLOSE sent at harness %.2f s; "Window closing" at log %.2f s)' % (h2l, close_s, (tclose - t0).total_seconds()))
    for n in a.frames:
        if n >= len(cum):
            print('frame #%d: out of range' % n)
            continue
        th = o_p10 + cum[n] / 1000.0
        cols = lines[n + 1].decode().split(',')
        print('frame #%d (csv frame=%s, interval %.1f ms): presented at harness ~%.2f s = log ~%.2f s; started at log ~%.2f s' % (
            n, cols[0], float(cols[ii]), th, th + h2l, th + h2l - float(cols[ii]) / 1000.0))
    return 0


if __name__ == '__main__':
    sys.exit(main())

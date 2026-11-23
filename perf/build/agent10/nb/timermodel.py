#!/usr/bin/env python3
"""timermodel: which clock does the front-end "leave the screen" timer follow? (Agent 10, task #17 1b tie-break)

Usage: timermodel.py RUNDIR [RUNDIR ...]
Per run (harness run dir with run.json, input.csv, perf.csv, game.log):
  - first frame (input.csv wait_first_frame t_s), press starts (press t_s - 0.85 s), and the
    front-end exit (first INSTALL batch, gap > 3 s, that starts after the first B press);
  - perf.csv rows (one row = one guest frame, frame_time_us), placed on the harness clock from the
    first frame: wall(k) = first_frame + sum(frame_time[0..k]);
  - from each anchor (first frame, START, A1, A2) to the exit: wall seconds, frames, and clamped
    game time sum(min(dt, c)) for several clamps c.
Runs that never leave report the value at the end of the run as a lower bound (">").
The table "spread" row is max-min over the runs that left. Read-only; one thread.
"""
import csv
import json
import os
import re
import sys
from datetime import datetime

LOGTS = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\]')
CLAMPS_MS = [16.667, 20.0, 25.0, 33.333, 50.0, 66.667, 100.0, 250.0, 1e9]
PRESS_LEAD = 0.85


def started_epoch(s):
    m = re.match(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(\.\d+)?', s)
    return datetime.strptime(m.group(1), '%Y-%m-%dT%H:%M:%S').timestamp() + (float(m.group(2)) if m.group(2) else 0.0)


def load(run_dir):
    run = json.load(open(os.path.join(run_dir, 'run.json'), encoding='utf-8-sig'))
    t0 = started_epoch(run['started'])
    ff = None
    presses = []
    with open(os.path.join(run_dir, 'input.csv'), encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            if row['cmd'] == 'wait_first_frame':
                ff = float(row['t_s'])
            elif row['cmd'] == 'press':
                presses.append((float(row['t_s']) - PRESS_LEAD, row['args']))
    first_b = next(t for t, a in presses if a.startswith('B'))
    stamps = []
    with open(os.path.join(run_dir, 'game.log'), encoding='utf-8', errors='replace') as f:
        for line in f:
            if 'INSTALL' in line:
                m = LOGTS.match(line)
                if m:
                    stamps.append(datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S.%f').timestamp() - t0)
    batches = []
    for s in stamps:
        if not batches or s - batches[-1] > 3.0:
            batches.append(s)
        else:
            pass
    starts = []
    prev = None
    for s in stamps:
        if prev is None or s - prev > 3.0:
            starts.append(s)
        prev = s
    exit_t = next((s for s in starts if s > first_b), None)
    dts = []
    with open(os.path.join(run_dir, 'perf.csv'), encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            dts.append(float(row['frame_time_us']) / 1000.0)
    anchors = {'FF': ff}
    names = [a for _, a in presses]
    anchors['START'] = presses[names.index('START')][0]
    a_list = [t for t, a in presses if a == 'A']
    anchors['A1'] = a_list[0]
    anchors['A2'] = a_list[1]
    return dict(dir=run_dir, tag=run.get('tag', os.path.basename(run_dir)), ff=ff, exit=exit_t, dts=dts,
                anchors=anchors, end=ff + sum(dts) / 1000.0)


def measure(r, anchor_t, stop_t):
    """frames and clamped sums for frames whose end time lies in (anchor_t, stop_t]."""
    wall = r['ff']
    n = 0
    sums = [0.0] * len(CLAMPS_MS)
    for dt in r['dts']:
        wall += dt / 1000.0
        if wall <= anchor_t:
            continue
        if wall > stop_t:
            break
        n += 1
        for i, c in enumerate(CLAMPS_MS):
            sums[i] += min(dt, c)
    return n, [s / 1000.0 for s in sums]


def main():
    runs = [load(d) for d in sys.argv[1:]]
    for r in runs:
        print(f"{r['tag']}: first frame {r['ff']:.2f} s, exit {('%.2f s' % r['exit']) if r['exit'] else 'none (end %.2f s)' % r['end']}, "
              f"{len(r['dts'])} perf rows; anchors " + ', '.join(f"{k}={v:.2f}" for k, v in r['anchors'].items()))
    for anchor in ['FF', 'START', 'A1', 'A2']:
        print(f"\n== anchor {anchor} -> exit (">" = run never left; value at run end)")
        hdr = ['run', 'wall_s', 'frames'] + [('c%.0fms' % c) if c < 1e8 else 'c_inf' for c in CLAMPS_MS]
        print('  ' + ' '.join(f"{h:>12}" for h in hdr))
        cols = {h: [] for h in hdr[1:]}
        for r in runs:
            a = r['anchors'][anchor]
            stop = r['exit'] if r['exit'] else r['end']
            n, sums = measure(r, a, stop)
            mark = '' if r['exit'] else '>'
            vals = [stop - a, n] + sums
            print('  ' + f"{r['tag'][:12]:>12} " + ' '.join(f"{mark}{v:>11.2f}" if isinstance(v, float) else f"{mark}{v:>11d}" for v in vals))
            if r['exit']:
                for h, v in zip(hdr[1:], vals):
                    cols[h].append(v)
        spread = [max(v) - min(v) if v else 0 for v in cols.values()]
        mean = [sum(v) / len(v) if v else 0 for v in cols.values()]
        print('  ' + f"{'spread':>12} " + ' '.join(f"{s:>12.2f}" for s in spread))
        print('  ' + f"{'spread/mean':>12} " + ' '.join(f"{(s / m if m else 0):>12.3f}" for s, m in zip(spread, mean)))


if __name__ == '__main__':
    main()

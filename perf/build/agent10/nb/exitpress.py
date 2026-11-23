#!/usr/bin/env python3
"""exitpress: where a b-gate-menus route run left the front end (Agent 10, task #17 1b tie-break).

Usage: exitpress.py RUNDIR [RUNDIR ...]
Per run:
  - harness start (run.json "started"), boot (wait_first_frame result), exit code;
  - every press step with log_lines before / at / after it (input.csv; t_s is written at the END
    of a step, so a press starts ~0.8 s before its t_s);
  - the INSTALL probe batches in game.log (lines containing "INSTALL", a new batch after a gap
    > 3 s), in harness seconds (log wall clock - started) and log wall clock.
The front-end exit is the first INSTALL batch after the first B press; the press that precedes
its start is reported. Read-only; one thread.
"""
import csv
import json
import os
import re
import sys
from datetime import datetime

LOGTS = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\]')


def started_epoch(run):
    s = run.get('started', '')
    m = re.match(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(\.\d+)?', s)
    if not m:
        return None
    return datetime.strptime(m.group(1), '%Y-%m-%dT%H:%M:%S').timestamp() + (float(m.group(2)) if m.group(2) else 0.0)


def install_batches(path, gap=3.0):
    batches = []
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            if 'INSTALL' not in line:
                continue
            m = LOGTS.match(line)
            if not m:
                continue
            t = datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S.%f').timestamp()
            if batches and t - batches[-1][1] <= gap:
                batches[-1][1] = t
                batches[-1][2] += 1
            else:
                batches.append([t, t, 1])
    return batches


def one(d):
    print('== %s' % d)
    try:
        with open(os.path.join(d, 'run.json'), encoding='utf-8-sig') as f:
            run = json.load(f)
    except (OSError, ValueError) as e:
        print('  run.json: %s' % e)
        run = {}
    t0 = started_epoch(run)
    print('  tag %s | started %s | exit %s (%s) | bin %s' % (run.get('tag'), run.get('started'), run.get('exit_code'),
                                                         run.get('close_method'), os.path.basename(str(run.get('bin_dir', '')))))
    rows = []
    with open(os.path.join(d, 'input.csv'), encoding='utf-8', errors='replace', newline='') as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        if r.get('cmd') == 'wait_first_frame':
            print('  boot: wait_first_frame at t=%s s: %s' % (r.get('t_s'), r.get('result')))
    presses = []
    for i, r in enumerate(rows):
        if r.get('cmd') != 'press':
            continue
        prev_ll = rows[i - 1].get('log_lines') if i else '-'
        next_ll = rows[i + 1].get('log_lines') if i + 1 < len(rows) else '-'
        presses.append((float(r['t_s']), r.get('args'), prev_ll, r.get('log_lines'), next_ll))
    print('  presses (t_s at step end; log_lines before / at / after):')
    for t, a, p, c, n in presses:
        print('    t=%7.2f  %-8s %5s / %5s / %5s' % (t, a, p, c, n))
    b = install_batches(os.path.join(d, 'game.log'))
    print('  INSTALL batches (harness s = log wall clock - started):')
    for s, e, n in b:
        hs = (s - t0) if t0 else float('nan')
        print('    %s  harness %7.2f s  %d lines over %.1f s' % (
            datetime.fromtimestamp(s).strftime('%H:%M:%S.%f')[:-3], hs, n, e - s))
    first_b = next((t for t, a, *_ in presses if a and a.split()[0] == 'B'), None)
    if t0 and first_b is not None:
        exitb = next(((s - t0, n) for s, e, n in b if (s - t0) > first_b - 1.0), None)
        if exitb:
            hs = exitb[0]
            before = [(t, a) for t, a, *_ in presses if t - 0.85 <= hs]
            bs = [t for t, a, *_ in presses if a and a.split()[0] == 'B']
            k = sum(1 for t in bs if t - 0.85 <= hs)
            last = before[-1] if before else None
            print('  -> front-end exit batch at harness %.2f s: after B press #%d (last press %s at t=%.2f, +%.2f s)' % (
                hs, k, last[1] if last else '-', last[0] if last else float('nan'), hs - last[0] if last else float('nan')))
        else:
            print('  -> no INSTALL batch after the first B press')
    print()


def main():
    for d in sys.argv[1:]:
        one(d)
    return 0


if __name__ == '__main__':
    sys.exit(main())

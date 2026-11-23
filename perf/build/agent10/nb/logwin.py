#!/usr/bin/env python3
"""Print game.log lines in a time window (seconds from the first log line), collapsing repeats.

usage: logwin.py RUNDIR --from-s A [--to-s B] [--max N] [--grep REGEX] [--level]
--level keeps only [warning]/[error]/[critical] lines. Repeated lines (same text with
numbers normalized) are counted and printed once, with the count, at first appearance.
Reads game.N.log (oldest first) then game.log.
"""
import argparse
import datetime as dt
import glob
import os
import re
import sys

TS = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+)\]')
NUM = re.compile(r'0x[0-9A-Fa-f]+|\d+')


def logs_of(run):
    rot = []
    for p in glob.glob(os.path.join(run, 'game.*.log')):
        m = re.search(r'game\.(\d+)\.log$', p)
        if m:
            rot.append((-int(m.group(1)), p))
    out = [p for _, p in sorted(rot)]
    if os.path.exists(os.path.join(run, 'game.log')):
        out.append(os.path.join(run, 'game.log'))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run')
    ap.add_argument('--from-s', type=float, default=0.0)
    ap.add_argument('--to-s', type=float, default=1e9)
    ap.add_argument('--max', type=int, default=200)
    ap.add_argument('--grep')
    ap.add_argument('--level', action='store_true')
    a = ap.parse_args()
    rx = re.compile(a.grep) if a.grep else None
    t0 = None
    order = []
    seen = {}
    for p in logs_of(a.run):
        with open(p, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                m = TS.match(line)
                if m:
                    t = dt.datetime.strptime(m.group(1)[:26], '%Y-%m-%d %H:%M:%S.%f')
                    if t0 is None:
                        t0 = t
                    cur = (t - t0).total_seconds()
                else:
                    continue
                if cur < a.from_s or cur > a.to_s:
                    continue
                if a.level and not re.search(r'\[(warning|error|critical)\]', line):
                    continue
                if rx and not rx.search(line):
                    continue
                body = line[m.end():].strip()
                key = NUM.sub('#', re.sub(r'\[t\d+\]', '', body))
                if key in seen:
                    seen[key][1] += 1
                    seen[key][3] = cur
                else:
                    seen[key] = [cur, 1, body, cur]
                    order.append(key)
    for k in order[:a.max]:
        first, n, body, last = seen[k]
        rep = '' if n == 1 else '  [x%d, last %.2fs]' % (n, last)
        print('%8.2fs %s%s' % (first, body[:260], rep))
    if len(order) > a.max:
        print('... %d more distinct lines' % (len(order) - a.max))
    return 0


if __name__ == '__main__':
    sys.exit(main())

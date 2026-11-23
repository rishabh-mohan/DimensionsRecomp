"""Agent 3, task #23: REPIN.md section 3b draw check for the rpm4 matrix: draws p10/p50/p90 per arm from each run's
native-frames.csv (draw_calls), over the timing window run-matrix printed ("window native-frames.csv rows A..B") and over
the whole file (zero rows left out). Read-only. Usage: python -B build/agent3/s4b/rpm4_draws.py [matrix_out] [run-matrix log]"""
import csv
import math
import os
import re
import sys

out = sys.argv[1] if len(sys.argv) > 1 else r'build\agent3\runs\rpm4-20261123-0620'
mlog = sys.argv[2] if len(sys.argv) > 2 else r'build\agent3\s4b\logs\rpm4.run-matrix.txt'
win, last = {}, None
for ln in open(mlog, encoding='utf-8', errors='replace'):
    m = re.match(r'\s*window\s+native-frames\.csv rows (\d+)\.\.(\d+)', ln)
    if m:
        last = (int(m.group(1)), int(m.group(2)))
    m = re.match(r'\s*-->\s+(\S+)-r1\s*:', ln)
    if m and last:
        win[m.group(1)] = last
        last = None


def pct(v, q):
    s = sorted(v)
    return s[max(0, math.ceil(q * len(s)) - 1)] if s else None


def stats(v):
    return 'n %5d  p10 %4s  p50 %4s  p90 %4s  min %4s  max %4s' % (
        len(v), pct(v, 0.10), pct(v, 0.50), pct(v, 0.90), min(v) if v else None, max(v) if v else None)


runs = os.path.join(out, 'runs')
res = {}
for d in sorted(os.listdir(runs)):
    m = re.match(r'^\d{4}-(\w+)-r1$', d)
    if not m:
        continue
    arm = m.group(1)
    rows = list(csv.DictReader(open(os.path.join(runs, d, 'native-frames.csv'), encoding='utf-8', errors='replace')))
    dc = [int(float(r['draw_calls'] or 0)) for r in rows]
    a, b = win.get(arm, (1, len(dc)))
    w = dc[a - 1:b]
    res[arm] = (pct(w, .1), pct(w, .5), pct(w, .9))
    print('%-6s window rows %d..%d: %s' % (arm, a, b, stats(w)))
    print('%-6s whole file (no zero rows):   %s' % (arm, stats([x for x in dc if x])))
if 'n0' in res and 'n0old' in res:
    print('n0 vs n0old window p10/p50/p90: %s vs %s -> %s' % (
        res['n0'], res['n0old'], 'EQUAL' if res['n0'] == res['n0old'] else 'DIFFER'))

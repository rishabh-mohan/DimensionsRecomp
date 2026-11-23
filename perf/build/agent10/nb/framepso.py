#!/usr/bin/env python3
"""framepso: longest frames and their pipeline creation cost, per run.

Usage: framepso.py RUNDIR [RUNDIR ...] [--top N]
Reads frames.csv; prints the column used for frame time, totals of
pipeline_creations / pipeline_creation_ms, the top-N frames with the PSO
columns, and the PSO cost in the 10 s before each top frame. Read-only.
"""
import argparse, csv, os, sys


def num(x):
    try:
        return float(x)
    except Exception:
        return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('runs', nargs='+')
    ap.add_argument('--top', type=int, default=5)
    a = ap.parse_args()
    for r in a.runs:
        p = os.path.join(r, 'frames.csv')
        with open(p, newline='', encoding='utf-8', errors='replace') as f:
            rows = list(csv.DictReader(f))
        cols = list(rows[0].keys()) if rows else []
        ft = next((c for c in ('frame_ms', 'frame_time_ms', 'cpu_frame_ms', 'dt_ms') if c in cols), None)
        if ft is None:
            ft = next((c for c in cols if c.endswith('_ms')), cols[1])
        tcol = next((c for c in ('t_s', 'time_s', 'elapsed_s', 't', 'time') if c in cols), None)
        print('== %s: %d frames; time col %s; frame col %s' % (r, len(rows), tcol, ft))
        tot_n = sum(num(x.get('pipeline_creations')) for x in rows)
        tot_ms = sum(num(x.get('pipeline_creation_ms')) for x in rows)
        print('   pipeline_creations %d, pipeline_creation_ms %.1f' % (tot_n, tot_ms))
        big = sorted(((num(x.get('pipeline_creation_ms')), i) for i, x in enumerate(rows)), reverse=True)[:a.top]
        print('   top PSO frames: ' + ', '.join('#%d %.1f ms (n=%s, frame %s ms, t=%s)' % (
            i, ms, rows[i].get('pipeline_creations'), rows[i].get(ft), rows[i].get(tcol) if tcol else '?') for ms, i in big))
        top = sorted(((num(x.get(ft)), i) for i, x in enumerate(rows)), reverse=True)[:a.top]
        for ms, i in top:
            t = num(rows[i].get(tcol)) if tcol else None
            win = [x for x in rows[max(0, i - 2000):i + 1]
                   if tcol is None or t - num(x.get(tcol)) <= 10.0]
            print('   frame #%d t=%s %s=%.1f pso n=%s ms=%s | prev10s pso n=%d ms=%.1f' % (
                i, rows[i].get(tcol) if tcol else '?', ft, ms,
                rows[i].get('pipeline_creations'), rows[i].get('pipeline_creation_ms'),
                sum(num(x.get('pipeline_creations')) for x in win),
                sum(num(x.get('pipeline_creation_ms')) for x in win)))
        print('   first cols: ' + ','.join(cols[:12]))


if __name__ == '__main__':
    sys.exit(main())

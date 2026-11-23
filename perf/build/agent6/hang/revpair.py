#!/usr/bin/env python3
"""Agent 6, task #25: compare named native runs (e.g. the reverse-order pair).

Targeted, single-threaded, read-only: reads frames.csv and game.log of the run dirs
given on the command line, nothing else.  Reuses scan_native.scan() for the totals and
adds the top frames by pipeline_creation_ms and by interval_ms.
usage: python revpair.py <run dir> [<run dir> ...]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scan_native  # noqa: E402


def top_frames(run, n=6):
    fr = os.path.join(run, 'frames.csv')
    if not os.path.exists(fr):
        fr = os.path.join(run, 'native-frames.csv')
    rows = []
    with open(fr, encoding='utf-8', errors='replace') as f:
        head = f.readline().strip().split(',')
        ia, ib, ic = head.index('pipeline_creation_ms'), head.index('pipeline_creations'), head.index('interval_ms')
        for line in f:
            p = line.split(',')
            if len(p) != len(head):
                continue
            rows.append((p[0], float(p[ib]), float(p[ia]), float(p[ic])))
    by_create = sorted(rows, key=lambda r: -r[2])[:n]
    by_iv = sorted(rows, key=lambda r: -r[3])[:n]
    over1s = [r for r in rows if r[3] >= 1000.0]
    return by_create, by_iv, over1s


def main():
    for d in sys.argv[1:]:
        run = os.path.abspath(d)
        r = scan_native.scan(run)
        if r is None:
            print('%s: not a native run (or no run.json)' % d)
            continue
        print('== %s' % r['run'])
        print('   bin %s exe %s started %s route %s elapsed %s' % (r['bin'], r['exe'], r['started'], r['route'], r['elapsed']))
        print('   frames %s  creations %s  creation_ms %.1f  max creation frame %.1f ms %s  max interval %.1f ms' % (
            r.get('frames'), r.get('pso_n'), r.get('pso_ms', 0.0), r.get('max_ms', 0.0), r.get('max_row'), r.get('max_iv', 0.0)))
        print('   STUCK-LOCK lines: %d %s; recipes saved %s; cold recipes %s' % (
            len(r.get('stuck', [])), ';'.join(r.get('stuck', [])[:4]), r.get('recipes_saved'), r.get('cold_recipes')))
        by_create, by_iv, over1s = top_frames(run)
        print('   top by creation ms (frame, creations, creation_ms, interval_ms):')
        for x in by_create:
            print('      %s  %4d  %8.1f  %8.1f' % (x[0], int(x[1]), x[2], x[3]))
        print('   top by interval ms:')
        for x in by_iv:
            print('      %s  %4d  %8.1f  %8.1f' % (x[0], int(x[1]), x[2], x[3]))
        print('   frames >= 1 s: %d, total %.1f s' % (len(over1s), sum(x[3] for x in over1s) / 1000.0))
    return 0


if __name__ == '__main__':
    sys.exit(main())

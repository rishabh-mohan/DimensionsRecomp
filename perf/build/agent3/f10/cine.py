# cine.py - the cinematic frames (story-load +15..+65 s) with the most draws, per run:
# perf.csv frame ms + draws, joined with the slow-frame line (syncs, host-gpu wait) when logged.
# usage: python -B cine.py label=<run dir> ...
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align, sync_profile

def main():
    for arg in sys.argv[1:]:
        label, run = arg.split('=', 1)
        mk = align.marks(run)
        ff = mk.get('first-frame', 0.0); sl = mk.get('story-load')
        if sl is None:
            print('=== %s: no story-load mark' % label); continue
        sf = {x[1]: x for x in sync_profile.frames(run)}
        rows = []
        with open(os.path.join(run, 'perf.csv'), encoding='utf-8', errors='replace') as f:
            t = ff
            for i, row in enumerate(csv.DictReader(f)):
                try:
                    us = float(row['frame_time_us'] or 0); dc = int(float(row.get('draw_calls') or 0))
                except ValueError:
                    continue
                t += us / 1e6
                rel = t - sl
                if 15 <= rel <= 65:
                    rows.append((i, rel, us / 1000.0, dc))
        n = len(rows)
        ms = sorted(r[2] for r in rows)
        print('=== %s  frames in story-load +15..+65 s: %d  frame ms median %.1f  max %.1f  frames >= 1 s: %d  sum of frames >= 1 s: %.1f s' % (
            label, n, ms[n // 2] if n else -1, ms[-1] if n else -1, sum(1 for x in ms if x >= 1000), sum(x for x in ms if x >= 1000) / 1000.0))
        top = sorted(rows, key=lambda r: -r[3])[:8]
        for i, rel, fms, dc in sorted(top, key=lambda r: r[1]):
            s = sf.get(i + 1)
            extra = ('syncs %4d  host-gpu wait %7.1f ms (%4dx)' % (s[6], s[4], s[5])) if s else 'no slow-frame line'
            print('  row %6d  %+6.1f s  %8.1f ms  draws %5d  %s' % (i, rel, fms, dc, extra))

if __name__ == '__main__':
    main()

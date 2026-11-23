# align.py - long frames from perf.csv on a timeline relative to the story-load mark
# usage: python -B align.py [--min-ms 700] label=<run dir> ...
# perf.csv has no clock: t = cumulative frame_time_us from the first row, anchored at
# the 'first-frame' mark of input.csv (t_s since run start); hang wall times from game logs.
import csv, json, os, re, sys, glob, datetime

def marks(run):
    out = {}
    with open(os.path.join(run, 'input.csv'), encoding='utf-8', errors='replace') as f:
        next(f, None)
        for line in f:
            c = line.rstrip('\n').split(',')
            if len(c) > 3 and c[2] == 'mark':
                out[c[3]] = float(c[0])
    return out

def started(run):
    with open(os.path.join(run, 'run.json'), encoding='utf-8-sig') as f:
        return float(json.load(f)['started_epoch_s'])

def hangs(run):
    out = []
    for p in glob.glob(os.path.join(run, '**', 'game*.log'), recursive=True):
        with open(p, encoding='utf-8', errors='replace') as f:
            for line in f:
                if 'STUCK-LOCK: critical section' in line:
                    ts = line[1:24]
                    out.append(datetime.datetime.strptime(ts, '%Y-%m-%d %H:%M:%S.%f').timestamp())
    return sorted(out)

def main():
    args = sys.argv[1:]
    min_ms = 700.0
    if args and args[0] == '--min-ms':
        min_ms = float(args[1]); args = args[2:]
    for arg in args:
        label, run = arg.split('=', 1)
        mk = marks(run); t0 = started(run)
        ff = mk.get('first-frame', 0.0); sl = mk.get('story-load')
        rows = []
        with open(os.path.join(run, 'perf.csv'), encoding='utf-8', errors='replace') as f:
            r = csv.DictReader(f)
            t = ff
            for i, row in enumerate(r):
                try:
                    us = float(row['frame_time_us'] or 0)
                except ValueError:
                    continue
                t += us / 1e6
                rows.append((i, t, us / 1000.0, row.get('draw_calls', '')))
        print('=== %s  perf rows %d  first-frame %.2f  story-load %s  last t %.1f s (vs end mark %s)' % (label, len(rows), ff, sl, rows[-1][1] if rows else -1, mk.get('end')))
        for h in hangs(run)[:1]:
            print('  STUCK-LOCK at run t %.1f s = story-load %+.1f s' % (h - t0, h - t0 - (sl or 0)))
        for i, t, ms, dc in rows:
            if ms >= min_ms:
                print('  row %6d  t %7.1f s  story-load %+7.1f s  %8.1f ms  draws %s' % (i, t, t - (sl or 0), ms, dc))

if __name__ == '__main__':
    main()

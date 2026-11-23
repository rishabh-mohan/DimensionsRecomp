"""W5b long-frame check (Agent 7, task #21). Read-only on build/agent8/matrix/**.

For every scored run of the given matrix folders:
  - re-cut the measured window from perf.csv using frames.json (first_row, rows) and check that
    median / p99 / p99.9 / max (nearest rank) match frames.json exactly;
  - count window frames over 8, 10 and 16.7 ms;
  - for frames over 10 ms: time in the window and the sys.csv sample that covers it
    (cpu util, eff MHz, E util) beside the run's window medians.
Usage: python -B tail_check.py <folder> [<folder> ...] -o tail-check.md
"""
import csv
import json
import math
import statistics
import sys
from pathlib import Path


def nearest_rank(sorted_vals, p):
    return sorted_vals[max(0, math.ceil(p * len(sorted_vals)) - 1)]


def find_key(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            r = find_key(v, key)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find_key(v, key)
            if r is not None:
                return r
    return None


def window_frames(run_dir):
    fj = json.loads((run_dir / 'frames.json').read_text(encoding='utf-8-sig'))
    w = fj['window']
    with open(run_dir / 'perf.csv', newline='') as f:
        rd = csv.reader(f)
        hdr = next(rd)
        ci = hdr.index('frame_time_us')
        vals = [row[ci] for row in rd]
    want = (round(fj['median_ms'], 3), round(fj['p99_ms'], 3), round(fj['p99_9_ms'], 3), round(fj['max_ms'], 3))
    for off in (w['first_row'] - 1, w['first_row'], w['first_row'] - 2, w['first_row'] + 1):
        ms = [float(v) / 1000.0 for v in vals[off:off + w['rows']]]
        s = sorted(ms)
        got = (round(nearest_rank(s, 0.5), 3), round(nearest_rank(s, 0.99), 3),
               round(nearest_rank(s, 0.999), 3), round(s[-1], 3))
        if got == want:
            return fj, ms, off, True
    return fj, [float(v) / 1000.0 for v in vals[w['first_row'] - 1:w['first_row'] - 1 + w['rows']]], None, False


def sys_rows(run_dir):
    with open(run_dir / 'sys.csv', newline='') as f:
        return [r for r in csv.DictReader(f)]


def main():
    args = sys.argv[1:]
    out = None
    if '-o' in args:
        i = args.index('-o')
        out = args[i + 1]
        args = args[:i] + args[i + 2:]
    lines = ['# W5b long-frame check (tail_check.py)', '',
             '- command: `python -B build/agent7/readout/tail_check.py ' + ' '.join(args) + (' -o ' + out if out else '') + '`',
             '- window = perf.csv rows from frames.json (first_row, rows); "verified" = median / p99 / p99.9 / max (nearest rank) equal frames.json',
             '- T = seconds from the window start (sum of frame times); sys sample = the sys.csv row whose 1 s interval holds window_start_epoch + T', '']
    runs = []
    for folder in args:
        fd = Path(folder)
        with open(fd / 'results.csv', newline='') as f:
            rows = [r for r in csv.DictReader(f) if r['scored'] == 'True']
        for r in rows:
            rd = Path(r['run_dir'])
            if not rd.is_absolute():
                rd = fd / 'runs' / rd.name
            fj, ms, off, ok = window_frames(rd)
            runj = json.loads((rd / 'run.json').read_text(encoding='utf-8-sig'))
            wse = find_key(runj, 'window_start_epoch')
            runs.append(dict(folder=fd.name, run=rd.name, arm=r['arm'], dir=rd, fj=fj, ms=ms, ok=ok, off=off, wse=wse))
    lines += ['## Per run', '',
              '| folder | run | arm | frames | verified | p99.9 ms | max ms | > 8 ms | > 10 ms | > 16.7 ms |',
              '|---|---|---|---|---|---|---|---|---|---|']
    for x in runs:
        ms = x['ms']
        x['n8'] = sum(1 for v in ms if v > 8.0)
        x['n10'] = sum(1 for v in ms if v > 10.0)
        x['n167'] = sum(1 for v in ms if v > 16.7)
        lines.append('| %s | %s | %s | %d | %s | %.3f | %.3f | %d | %d | %d |' % (
            x['folder'], x['run'], x['arm'], len(ms), 'yes' if x['ok'] else 'NO', x['fj']['p99_9_ms'], x['fj']['max_ms'],
            x['n8'], x['n10'], x['n167']))
    lines += ['', '## Per arm', '',
              '| arm | runs | runs with a frame > 8 ms | frames > 8 ms (total; median per run) | frames > 10 ms | frames > 16.7 ms | p99.9 ms median / max |',
              '|---|---|---|---|---|---|---|']
    for arm in sorted(set(x['arm'] for x in runs)):
        g = [x for x in runs if x['arm'] == arm]
        lines.append('| %s | %d | %d | %d; %.1f | %d | %d | %.3f / %.3f |' % (
            arm, len(g), sum(1 for x in g if x['n8']), sum(x['n8'] for x in g), statistics.median([x['n8'] for x in g]),
            sum(x['n10'] for x in g), sum(x['n167'] for x in g),
            statistics.median([x['fj']['p99_9_ms'] for x in g]), max(x['fj']['p99_9_ms'] for x in g)))
    lines += ['', '## Frames over 10 ms (with the sys.csv sample)', '',
              '| run | arm | T s | ms | sys sample wall | cpu util % (run median) | eff MHz (run median) | E util % (run median) |',
              '|---|---|---|---|---|---|---|---|']
    for x in runs:
        if not x['n10']:
            continue
        srows = sys_rows(x['dir'])
        wse = x['wse']
        win = [s for s in srows if wse is not None and wse <= float(s['epoch_s']) <= wse + 51.0]
        med = lambda k: statistics.median(float(s[k]) for s in win) if win else float('nan')
        t = 0.0
        for v in x['ms']:
            t += v / 1000.0
            if v > 10.0:
                wall = (wse or 0.0) + t
                cand = [s for s in srows if float(s['epoch_s']) - 1.05 < wall <= float(s['epoch_s'])]
                s = cand[0] if cand else None
                if s:
                    lines.append('| %s | %s | %.2f | %.2f | %s | %s (%.1f) | %s (%.0f) | %s (%.1f) |' % (
                        x['run'], x['arm'], t, v, s['wall'], s['cpu_util_pct'], med('cpu_util_pct'), s['eff_mhz'], med('eff_mhz'),
                        s['e_util_pct'], med('e_util_pct')))
                else:
                    lines.append('| %s | %s | %.2f | %.2f | - | - | - | - |' % (x['run'], x['arm'], t, v))
    big = [x for x in runs if x['fj']['p99_9_ms'] > 8.0]
    for x in big:
        lines += ['', '## Frames over 6 ms per 1 s bin: %s (%s)' % (x['run'], x['arm']), '']
        t = 0.0
        bins = {}
        for v in x['ms']:
            t += v / 1000.0
            if v > 6.0:
                b = int(t)
                bins.setdefault(b, []).append(v)
        for b in sorted(bins):
            vs = bins[b]
            lines.append('- T %d-%d s: %d frames > 6 ms (max %.2f, %d > 10 ms)' % (b, b + 1, len(vs), max(vs), sum(1 for v in vs if v > 10.0)))
    bad = [x['run'] for x in runs if not x['ok']]
    lines += ['', '- check: %d runs, %d verified against frames.json%s' % (len(runs), len(runs) - len(bad), ('; NOT verified: ' + ', '.join(bad)) if bad else '')]
    text = '\n'.join(lines) + '\n'
    if out:
        Path(out).write_text(text, encoding='utf-8')
    sys.stdout.write(text if not out else lines[-1] + '\n')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())

"""nrows.py (Agent 10, task #17 item 2): the S3.2 expectations for native n-rows. Read-only.

  python nrows.py --run LABEL=RUNDIR [LABEL=RUNDIR ...] [--seg 60] [--out report.txt]

Per run dir (game.2.log, game.1.log, game.log in that order; native-frames.csv):
  * 'Native GPU shader cache miss: hash=0x0' lines, other 'shader cache miss' lines, warning/error lines,
    and whether the boot lines survived the 5 MB log rotation (first file starts with the startup lines);
  * native-frames.csv draw_calls per frame: rows, mean, median, the 8 commonest values with their share, and
    the scene sequence: runs of one draw_calls value lasting >= --seg frames, consecutive repeats merged;
  * the 'Native draw batches' / 'threaded recording' lines.
The S3.2 rating (agent10-batch2-review.md section 13) expects: hash=0x0 drops sharply in n2/n3, n0 unchanged,
draws per frame unchanged (same commonest values, same scene sequence up to timing).
"""
import argparse
import collections
import csv
import os
import re
import statistics
import sys

HASH0 = 'Native GPU shader cache miss: hash=0x0'
MISS = 'shader cache miss'
LEVEL = re.compile(r'^\[[^\]]*\] \[(warning|error|critical)\] ')
BATCH = re.compile(r'Native draw batches: (\w+ workers=\d+)')


def logs(run):
    return [os.path.join(run, n) for n in ('game.2.log', 'game.1.log', 'game.log') if os.path.isfile(os.path.join(run, n))]


def scan(run, seg):
    r = collections.OrderedDict(run=run)
    files = logs(run)
    r['files'] = ', '.join(f'{os.path.basename(p)} {os.path.getsize(p):,} B' for p in files) or 'no game.log'
    c = collections.Counter()
    first = ''
    batches = []
    for i, p in enumerate(files):
        with open(p, encoding='utf-8', errors='replace') as fh:
            for n, line in enumerate(fh):
                if i == 0 and n == 0:
                    first = line.strip()[:120]
                c['lines'] += 1
                if HASH0 in line:
                    c['hash0'] += 1
                elif MISS in line:
                    c['miss_other'] += 1
                if LEVEL.match(line):
                    c['warn_err'] += 1
                if 'threaded recording ON' in line:
                    c['threaded_on'] += 1
                b = BATCH.search(line)
                if b:
                    batches.append(b.group(1))
    r['counts'] = dict(c)
    # A fresh game.log starts with the "GPU route: ..." line; if the first kept file starts later, rotation
    # (5 MB, game.log -> game.1.log -> game.2.log) dropped the start of the run.
    r['boot_kept'] = ('GPU route:' in first or 'Startup' in first or 'overlays' in first
                      or 'rexglue' in first.lower())
    r['first_line'] = first
    r['batches'] = batches
    nf = os.path.join(run, 'native-frames.csv')
    if os.path.isfile(nf):
        with open(nf, newline='', encoding='utf-8', errors='replace') as fh:
            dc = [int(float(x['draw_calls'])) for x in csv.DictReader(fh) if x.get('draw_calls') not in (None, '')]
        cnt = collections.Counter(dc)
        r['frames'] = len(dc)
        r['dc_mean'] = round(statistics.mean(dc), 2) if dc else None
        r['dc_median'] = statistics.median(dc) if dc else None
        r['dc_top'] = [(v, round(100.0 * k / len(dc), 1)) for v, k in cnt.most_common(8)]
        scenes, run_v, run_n = [], None, 0
        for v in dc + [None]:
            if v == run_v:
                run_n += 1
                continue
            if run_v is not None and run_n >= seg and (not scenes or scenes[-1][0] != run_v):
                scenes.append([run_v, run_n])
            elif run_v is not None and run_n >= seg:
                scenes[-1][1] += run_n
            run_v, run_n = v, 1
        r['scenes'] = scenes
    else:
        r['frames'] = None
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--run', nargs='+', action='extend', required=True)
    ap.add_argument('--seg', type=int, default=60)
    ap.add_argument('--out')
    o = ap.parse_args()
    W = []
    for spec in o.run:
        label, run = spec.split('=', 1)
        r = scan(run, o.seg)
        k = r['counts']
        W.append(f"== {label}  {run}")
        W.append(f"  logs: {r['files']}; boot lines kept: {r['boot_kept']} (first: {r['first_line'][:80]})")
        W.append(f"  lines {k.get('lines', 0):,}; hash=0x0 {k.get('hash0', 0):,}; other cache-miss {k.get('miss_other', 0):,}; "
                 f"warning/error {k.get('warn_err', 0):,}; threaded ON {k.get('threaded_on', 0)}; batches {r['batches'] or 'none'}")
        if r['frames']:
            W.append(f"  draw_calls: {r['frames']:,} frames, mean {r['dc_mean']}, median {r['dc_median']}, top {r['dc_top']}")
            W.append(f"  scenes (>= {o.seg} frames): " + ' -> '.join(f'{v}x{n}' for v, n in r['scenes'][:40]))
        else:
            W.append('  no native-frames.csv')
    text = '\n'.join(W) + '\n'
    if o.out:
        with open(o.out, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)
    print(text)


if __name__ == '__main__':
    sys.exit(main())

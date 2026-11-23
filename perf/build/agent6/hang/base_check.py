#!/usr/bin/env python3
"""Baseline STUCK-LOCK check for one run dir (read-only, single-threaded, small files only).

usage: python base_check.py <run dir> --at HH:MM:SS.fff [--sampler <cpu-sampler csv>] [--win 12]

Prints:
  - the STUCK-LOCK / FATAL / minidump lines of game.log;
  - run.json basics;
  - frames >= --min-frame s with their perf time (cumulative frame time from the first
    perf.csv row), and their offset from H0 (first 2823-draw / 366,575-vertex row);
  - the CPU sampler rows, samples.csv cores and gpu.csv rows within --win s of --at.
"""
import argparse
import csv
import datetime as dt
import json
import pathlib
import re

ap = argparse.ArgumentParser()
ap.add_argument('run')
ap.add_argument('--at', required=True, help='wall time of the STUCK-LOCK report, HH:MM:SS[.fff]')
ap.add_argument('--sampler', default='build/agent3/logs/cpu-sampler-0554.csv')
ap.add_argument('--win', type=float, default=12.0)
ap.add_argument('--min-frame', type=float, default=4.5)
a = ap.parse_args()
run = pathlib.Path(a.run)


def parse_iso(s):
    m = re.match(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d+))?', s)
    base = dt.datetime.strptime(m.group(1), '%Y-%m-%dT%H:%M:%S')
    frac = float('0.' + m.group(2)) if m.group(2) else 0.0
    return base + dt.timedelta(seconds=frac)


def tod(s):
    """HH:MM:SS[.fff] -> seconds of day."""
    h, m, sec = s.split(':')
    return int(h) * 3600 + int(m) * 60 + float(sec)


# 1. game.log
pat = re.compile(r'STUCK|0x84959edc|callers|\[FATAL\]|[Mm]inidump|hang-\d+\.dmp')
log = (run / 'game.log').read_text(encoding='utf-8', errors='replace').splitlines()
print(f'== game.log: {len(log)} lines')
for i, line in enumerate(log, 1):
    if pat.search(line):
        print(f'  L{i}: {line[:420]}')

# 2. run.json
rj = json.loads((run / 'run.json').read_text(encoding='utf-8-sig'))
started = parse_iso(rj.get('started') or rj.get('start'))
t0 = started.hour * 3600 + started.minute * 60 + started.second + started.microsecond / 1e6
at_rel = tod(a.at) - t0
print(f"== run.json: started {started.time()} exe {str(rj.get('exe_sha256', ''))[:8]} "
      f"exit {rj.get('exit_code')} close {rj.get('close_method')} {rj.get('close_seconds')} s "
      f"elapsed {rj.get('elapsed_s')} | report at launch+{at_rel:.2f} s")

# 3. perf.csv
rows = list(csv.DictReader(open(run / 'perf.csv', newline='')))
cum = 0.0
info = []
for i, r in enumerate(rows, 1):
    try:
        ft = float(r['frame_time_us']) / 1e6
    except (TypeError, ValueError):
        continue
    d = int(float(r.get('draw_calls') or 0))
    v = int(float(r.get('vertices_processed') or 0))
    info.append((i, cum, ft, d, v))
    cum += ft
h0 = next((x for x in info if x[3] == 2823 and x[4] == 366575), None)
print(f'== perf.csv: {len(info)} rows, {cum:.2f} s of frames; H0 '
      + (f'row {h0[0]} at perf {h0[1]:.2f} s' if h0 else 'not found'))
for (i, c, ft, d, v) in info:
    if ft >= a.min_frame:
        off = f'H0{c - h0[1]:+.2f}' if h0 else '-'
        print(f'  row {i}: frame {ft:.2f} s, perf {c:.2f}-{c + ft:.2f} s ({off}), draws {d}, verts {v}')
long_rows = [x for x in info if x[2] >= a.min_frame]
if long_rows:
    # Assume the longest frame contains the report; estimate launch -> first-frame offset.
    i, c, ft, d, v = max(long_rows, key=lambda x: x[2])
    print(f'  if row {i} contains the report: perf {c:.2f}-{c + ft:.2f} s ~ launch '
          f'{at_rel - 5.0:.1f} (hold start, report - 5 s) ... ; first frame at launch ~'
          f'{at_rel - 5.0 - c:.1f} s or later')

# 4. CPU sampler (wall clock)
sp = pathlib.Path(a.sampler)
if sp.exists():
    print(f'== {sp.name} within +-{a.win:.0f} s of {a.at}')
    cols = ['time', 'total_pct', 'msmpeng_cores', 'presentmon_x64_cores', 'dwm_cores', 'legodimensions_cores']
    print('  ' + ' '.join(cols))
    for r in csv.DictReader(open(sp, newline='')):
        try:
            if abs(tod(r['time']) - tod(a.at)) <= a.win:
                print('  ' + ' '.join(str(r.get(k, '')) for k in cols))
        except ValueError:
            pass

# 5. samples.csv (launch-relative)
smp = run / 'samples.csv'
if smp.exists():
    srows = [r for r in csv.DictReader(open(smp, newline='')) if r.get('cpu_s')]
    print(f'== samples.csv game cores within +-{a.win:.0f} s of launch+{at_rel:.1f}')
    prev = None
    for r in srows:
        t, c = float(r['t_s']), float(r['cpu_s'])
        if prev and abs(t - at_rel) <= a.win and t > prev[0]:
            print(f'  t {t:.1f}: {(c - prev[1]) / (t - prev[0]):.2f} cores  {r.get("note", "")[:60]}')
        prev = (t, c)

# 6. gpu.csv
gp = run / 'gpu.csv'
if gp.exists():
    grows = list(csv.DictReader(open(gp, newline='')))
    hdr = list(grows[0].keys()) if grows else []
    print(f'== gpu.csv: {len(grows)} rows; columns: {",".join(hdr)}')
    tcol = 't_s' if 't_s' in hdr else None
    n = 0
    for r in grows:
        try:
            if tcol:
                ok = abs(float(r[tcol]) - at_rel) <= a.win
            else:
                k = next(k for k in hdr if 'time' in k.lower())
                ts = r[k].strip().split(' ')[-1]
                ok = abs(tod(ts) - tod(a.at)) <= a.win
        except (ValueError, StopIteration, KeyError):
            continue
        if ok and n < 40:
            print('  ' + ','.join(str(r[k]) for k in hdr))
            n += 1

"""Agent 6 (task #8): read a6 §10.2 warm-boot runs (#32, pipeline_cache.cpp:564). READ-ONLY, single-threaded.
Usage:
  python build\\agent6\\s10-2\\s102_read.py <run dir or glob> [...] [--out file]
For each run it prints: the bin, the thread cvar, exit/close/dumps, the seed check, the storage lines (N and ms),
the gap from "Initializing shader storage" to the next guest line (SetInterruptCallback), first-frame time,
pipeline misses, xpso growth, early process thread counts, STUCK-LOCK episodes and the exit line.
Hang suspect: gap > translated_ms + created_ms + 5000 ms, or no SetInterruptCallback line after the storage lines.
"""
import csv
import glob
import json
import os
import re
import sys
from datetime import datetime

TS = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+)\] \[([a-z]+)\] \[([^\]]*)\] (?:\[t(\d+)\] )?(.*)$')
INIT = 'Initializing shader storage'
TRANS = re.compile(r'Translated (\d+) shaders from the storage in (\d+) milliseconds')
CREATED = re.compile(r'Created (\d+) graphics pipelines \(not including reading the descriptions\) from the storage in (\d+) milliseconds')
NEXT_GUEST = 'SetInterruptCallback'
EXIT_LINE = 'Title terminated; hard-exiting process'
STUCK_FIRST = 'still not acquired after'


def ts(s):
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f')


def read_log(path):
    out = []
    if not os.path.isfile(path):
        return out
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            m = TS.match(line.rstrip('\n'))
            if m:
                out.append((ts(m.group(1)), m.group(2), m.group(3), m.group(4), m.group(5)))
    return out


def one(run):
    r = {'run': os.path.basename(run.rstrip('\\/'))}
    rj = {}
    p = os.path.join(run, 'run.json')
    if os.path.isfile(p):
        with open(p, encoding='utf-8-sig') as f:
            rj = json.load(f)
    r['bin'] = os.path.basename(str(rj.get('bin_dir') or rj.get('BinDir') or '?').rstrip('\\/'))
    cmd = rj.get('command_line') or ''
    m = re.search(r'--d3d12_pipeline_creation_threads=(-?\d+)', cmd)
    r['threads'] = m.group(1) if m else 'default'
    r['exit'] = rj.get('exit_code')
    r['close'] = rj.get('close_method')
    r['dumps'] = len(rj.get('dumps') or [])
    r['crash_events'] = len(rj.get('crash_events') or [])
    seed = rj.get('seed_xenos') or {}
    seed_ok, xpso_growth = None, None
    for sf in seed.get('files') or []:
        ok = sf.get('sha256') and sf.get('sha256') == sf.get('copy_sha256')
        seed_ok = ok if seed_ok is None else (seed_ok and ok)
        if str(sf.get('name', '')).endswith('.xpso') and sf.get('bytes_after'):
            xpso_growth = (int(sf['bytes_after']) - int(sf['bytes'])) / 72.0
    r['seed_ok'] = seed_ok
    r['xpso_new'] = xpso_growth

    lines = read_log(os.path.join(run, 'game.log'))
    t0 = lines[0][0] if lines else None
    t_init = t_trans = t_created = t_next = None
    n_tr = ms_tr = n_cr = ms_cr = None
    stuck = 0
    exit_line = False
    for (t, lvl, cat, tid, msg) in lines:
        if t_init is None and INIT in msg:
            t_init = t
        m = TRANS.search(msg)
        if m and t_trans is None:
            t_trans, n_tr, ms_tr = t, int(m.group(1)), int(m.group(2))
        m = CREATED.search(msg)
        if m and t_created is None:
            t_created, n_cr, ms_cr = t, int(m.group(1)), int(m.group(2))
        if t_next is None and t_init is not None and NEXT_GUEST in msg:
            t_next = t
        if STUCK_FIRST in msg:
            stuck += 1
        if EXIT_LINE in msg:
            exit_line = True
    r['init_s'] = round((t_init - t0).total_seconds(), 2) if (t_init and t0) else None
    r['translated'] = (n_tr, ms_tr)
    r['created'] = (n_cr, ms_cr)
    r['gap_init_to_guest_ms'] = round((t_next - t_init).total_seconds() * 1000) if (t_next and t_init) else None
    r['gap_created_to_guest_ms'] = round((t_next - t_created).total_seconds() * 1000) if (t_next and t_created) else None
    budget = (ms_tr or 0) + (ms_cr or 0) + 5000
    r['hang_suspect'] = (t_init is not None) and (t_next is None or r['gap_init_to_guest_ms'] > budget)
    r['stuck_episodes'] = stuck
    r['exit_line'] = exit_line
    r['log_lines'] = len(lines)

    # summary.txt: first frame time.
    r['first_frame_s'] = None
    sp = os.path.join(run, 'summary.txt')
    if os.path.isfile(sp):
        with open(sp, encoding='utf-8', errors='replace') as f:
            m = re.search(r'frames first written ([\d.]+) s after launch', f.read())
            if m:
                r['first_frame_s'] = float(m.group(1))

    # perf.csv: frames, misses, first-30-frame max.
    r['frames'] = r['pm'] = r['first30_max_ms'] = None
    pp = os.path.join(run, 'perf.csv')
    if os.path.isfile(pp):
        with open(pp, newline='', encoding='utf-8', errors='replace') as f:
            rows = list(csv.DictReader(f))
        if rows:
            r['frames'] = len(rows)
            r['pm'] = sum(int(float(x.get('pipeline_cache_misses') or 0)) for x in rows)
            r['first30_max_ms'] = round(max(float(x['frame_time_us']) for x in rows[:30]) / 1000.0, 1)

    # samples.csv: process thread count early in the boot (info; the fix adds 2 temporary threads at default,
    # 11 with threads=0, for about the Created time).
    r['threads_early'] = None
    sp = os.path.join(run, 'samples.csv')
    if os.path.isfile(sp):
        with open(sp, newline='', encoding='utf-8', errors='replace') as f:
            rows = list(csv.DictReader(f))
        early = [(float(x['t_s']), int(float(x['threads']))) for x in rows if x.get('threads') and float(x['t_s']) <= 30]
        if early:
            r['threads_early'] = ' '.join(f'{int(t)}:{n}' for t, n in early[:30])
    return r


def main(argv):
    out = None
    if '--out' in argv:
        i = argv.index('--out')
        out = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    runs = []
    for g in argv:
        for p in sorted(glob.glob(g)):
            if os.path.isdir(p):
                runs.append(p)
    text = []
    for run in runs:
        r = one(run)
        text.append(f"== {r['run']}  bin={r['bin']}  threads={r['threads']}")
        text.append(f"   exit={r['exit']} close={r['close']} dumps={r['dumps']} crash_events={r['crash_events']} exit_line={r['exit_line']} stuck_episodes={r['stuck_episodes']}")
        text.append(f"   seed_ok={r['seed_ok']} storage_init_at={r['init_s']} s  translated={r['translated']}  created={r['created']}")
        text.append(f"   gap init->guest={r['gap_init_to_guest_ms']} ms  created->guest={r['gap_created_to_guest_ms']} ms  HANG_SUSPECT={r['hang_suspect']}")
        text.append(f"   first_frame={r['first_frame_s']} s  frames={r['frames']}  pm={r['pm']}  xpso_new={r['xpso_new']}  first30_max={r['first30_max_ms']} ms")
        text.append(f"   threads(t_s:n, first 30 s)={r['threads_early']}")
    s = '\n'.join(text)
    print(s)
    if out:
        with open(out, 'w', encoding='utf-8') as f:
            f.write(s + '\n')


if __name__ == '__main__':
    main(sys.argv[1:])

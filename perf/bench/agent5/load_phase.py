#!/usr/bin/env python3
"""Load-phase score for native runs (Agent 5, perf sprint S3, task #15).

The runner (bench/agent8/run/run-matrix.ps1) scores a window that starts at
least 60 s after the first frame, so it never sees the load phase. Every
matrix run is a fresh process, so every run pays the first-use texture and
buffer uploads in its first minute. This script scores that minute from the
files the runner already writes. It does not touch the runner or its outputs.

Per run, over the first --seconds (default 60) after the first frame:
  o33 o50 o100   frames with interval_ms > 33 / 50 / 100 ms
  hitch_ms       sum of (interval_ms - 33) over the frames > 33 ms
  max_ms p99_ms  max frame and p99 (nearest rank, sorted[ceil(p*n)-1], as the runner)
  fps            frames / seconds covered
  launch_ff_s    runner process start -> the game.log line
                 'Native presentation: frame=0' (ff_src log). Fallbacks:
                 tail = last frame (game.log 'Title terminated', else the
                 runner's WM_CLOSE time) minus the summed frame intervals
                 (reads 0.17-0.29 s high against log on 9 window-3/S3 runs);
                 signal = run.json first_frame_signal_s (last resort: its
                 zero point is not the process start mark; it reads 3-5 s
                 below log on the S3 runs and -4..+9 s off on window 3).
  ff_title_s     first frame -> the title, i.e. the draw-count switch: the
                 first frame from which draw_calls stays at or above the
                 midpoint of the light level (median of the first 5 s) and the
                 heavy level (median after --seconds) for 90% of the next 1 s.
                 On the window-3 and S3 native runs this is 0-1 -> 8 draws.
  launch_title_s launch_ff_s + ff_title_s
  title_max_ms   max frame from 2 s before to 5 s after the title switch (the
                 title's first-use uploads; 12.9-16.0 ms on quiet window-3 runs)
  o20_late       frames > 20 ms from 5 s to the end of the window. On quiet
                 runs every frame > 33 ms is in the first 1.4 s (startup burst,
                 per-run PSO compiles included) and o20_late is 0-2; busy
                 machines give hundreds (info flag 'noisy' above 20).
  ff_win_s       first frame -> start of the runner's scored window on the
                 frame clock: interval_ms summed over the rows before run.json
                 frames.window.first_row (the row count on disk at the start
                 mark, so it can only read early). Info flag win<60s if it is
                 below --win-floor (60) minus 0.5 s. Not a load-phase metric:
                 it checks Agent 1's 60 s floor. On the S3 runs it was
                 settle + warm-up + 0.2-0.4 s.
Frame times and draw counts come from native-frames.csv (perf.csv draw_calls
is 0 on native runs). perf.csv frame_time_us is read as a cross-check: its
first row is 0 and the rest are the native rows one-for-one (flag
perf_mismatch if the window max or o33 differ).

Excluded from the per-arm numbers (still listed per run): cold, short (fewer
than --seconds of frames), no_frames, no_title (native draw counts never
switch), light_phase (fewer than 30 INSTALL*.DAT FAILED lines in game*.log,
Agent 8's rule), status other than OK, and any runner excluding flag except
window_before_floor (which concerns the scored window, not the load phase).

Arms come from run.json 'tag' (or the run dir name without the HHMM- prefix):
'<arm>-r<rep>' or 'cold-<arm>'. With two or more arms, each arm is compared
with --ref (default u0 if present, else the first arm): difference of
medians and an exact two-sided permutation p for the rank-sum (Mann-Whitney)
statistic. The smallest p possible is 2/C(n1+n2, n1): 0.10 at 3v3, 0.029 at
4v4, 0.008 at 5v5.

usage:
  python bench/agent5/load_phase.py PATH [PATH ...] [--seconds 60] [--ref u0]
      [--title-draws N] [--win-floor 60] [--perf-only-ok] [--csv FILE] [--md FILE]
      [--json FILE] [--quiet]
PATH is a run dir, a matrix output dir (with runs/) or a parent of them;
dirs are searched 3 levels deep. Runs without native-frames.csv are skipped
unless --perf-only-ok. Stdlib only, one thread; writes files only when asked.
"""

import argparse
import bisect
import csv
import datetime as dt
import glob
import itertools
import json
import math
import os
import re
import statistics
import sys

THRESHOLDS = (33.0, 50.0, 100.0)
HITCH_MS = 33.0
FF_MARK = 'Native presentation: frame=0 '
TERM_MARK = 'Title terminated'
TS_RE = re.compile(r'^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?)\]')
INSTALL_RE = re.compile(r'INSTALL\d+_\d+\.DAT', re.IGNORECASE)
HHMM_RE = re.compile(r'^\d{4}-(.+)$')
REP_RE = re.compile(r'^(.*)-r(\d+)$')
SKIP_DIRS = {'cache', 'user', 'profiles', 'tracy'}
LIGHT_PHASE_MIN_INSTALL = 30
IGNORED_RUNNER_FLAGS = {'window_before_floor'}

# (key, label, decimals) for the summaries
METRICS = [
    ('launch_ff_s', 'launch->ff s', 2),
    ('ff_title_s', 'ff->title s', 2),
    ('launch_title_s', 'launch->title s', 2),
    ('title_max_ms', 'title max ms', 1),
    ('o33', 'o33', 0),
    ('o50', 'o50', 0),
    ('o100', 'o100', 0),
    ('hitch_ms', 'hitch ms', 0),
    ('max_ms', 'max ms', 1),
    ('p99_ms', 'p99 ms', 2),
    ('fps', 'fps', 0),
    ('o20_late', 'o20 5s+', 0),
]

CSV_FIELDS = [
    'matrix', 'run', 'tag', 'arm', 'rep', 'cold', 'mode', 'bin', 'src', 'rows', 'bad_rows',
    'total_s', 'launch_ref', 'launch_ff_s', 'ff_src', 'ff_log_s', 'ff_tail_s', 'ff_signal_s',
    'launch_log_s', 'ff_title_s', 'launch_title_s', 'light_draws', 'heavy_draws', 'title_thr',
    'title_max_ms', 'frames', 'fps', 'p50_ms', 'p99_ms', 'max_ms', 'o33', 'o50', 'o100', 'hitch_ms',
    'o20_late', 'ff_win_s',
    'perf_rows', 'perf_max_ms', 'perf_o33', 'install_fail', 'fps_cap', 'excluded',
    'flags_excl', 'flags_info', 'run_dir',
]


def parse_wall(value):
    if not isinstance(value, str) or not value.strip():
        return None
    value = value.strip()
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
        try:
            return dt.datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def load_json(path):
    try:
        with open(path, encoding='utf-8-sig') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def find_runs(paths, max_depth=3):
    out, seen = [], set()
    for path in paths:
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            print(f'warning: not a directory: {path}', file=sys.stderr)
            continue
        base = path.rstrip('\\/').count(os.sep)
        for root, dirs, files in os.walk(path):
            if 'native-frames.csv' in files or 'perf.csv' in files:
                if root not in seen:
                    seen.add(root)
                    out.append(root)
                dirs[:] = []
                continue
            if root.rstrip('\\/').count(os.sep) - base >= max_depth:
                dirs[:] = []
            else:
                dirs[:] = sorted(d for d in dirs if d.lower() not in SKIP_DIRS)
    return out


def read_frames(path, time_col, scale, draw_col='draw_calls', cap_col=None, drop_leading_zero=False):
    """Return (intervals_ms, draws, caps, bad_rows) or None if the file is unusable."""
    iv, draws, caps, bad = [], [], [], 0
    try:
        f = open(path, newline='', encoding='utf-8', errors='replace')
    except OSError:
        return None
    with f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            return None
        idx = {h.strip(): i for i, h in enumerate(header)}
        if time_col not in idx:
            return None
        ti, di, ci = idx[time_col], idx.get(draw_col), idx.get(cap_col) if cap_col else None
        width = len(header)
        leading = drop_leading_zero
        for row in reader:
            if len(row) != width:
                bad += 1
                continue
            try:
                v = float(row[ti]) * scale
                d = float(row[di]) if di is not None else math.nan
                c = float(row[ci]) if ci is not None else math.nan
            except ValueError:
                bad += 1
                continue
            if leading and v <= 0:
                continue
            leading = False
            iv.append(v)
            draws.append(d)
            caps.append(c)
    return iv, draws, caps, bad


def cumulative_s(iv):
    t, out = 0.0, []
    for v in iv:
        t += v / 1000.0
        out.append(t)
    return out


def nearest_rank(sorted_vals, p):
    if not sorted_vals:
        return None
    return sorted_vals[max(0, math.ceil(p * len(sorted_vals)) - 1)]


def window_stats(iv, t, seconds):
    k = bisect.bisect_right(t, seconds)  # frames that completed inside the window
    w = iv[:k]
    res = {'frames': len(w)}
    if not w:
        return res, k
    s = sorted(w)
    res['o33'], res['o50'], res['o100'] = (sum(1 for v in w if v > th) for th in THRESHOLDS)
    res['hitch_ms'] = sum(v - HITCH_MS for v in w if v > HITCH_MS)
    res['max_ms'] = s[-1]
    res['p99_ms'] = nearest_rank(s, 0.99)
    res['p50_ms'] = nearest_rank(s, 0.50)
    res['fps'] = len(w) / t[k - 1] if t[k - 1] > 0 else None
    return res, k


def title_switch(t, draws, seconds, title_draws=None, sustain_s=1.0, frac=0.9):
    """Seconds from the first frame to the draw-count switch, plus the levels used."""
    info = {'light_draws': None, 'heavy_draws': None, 'title_thr': None}
    n = len(draws)
    if n < 50 or any(math.isnan(d) for d in draws[:50]):
        return None, info
    k5 = max(1, bisect.bisect_right(t, 5.0))
    light = statistics.median(draws[:k5])
    ks = bisect.bisect_right(t, seconds)
    heavy = statistics.median(draws[ks:] if n - ks >= 200 else draws[(3 * n) // 4:])
    info['light_draws'], info['heavy_draws'] = light, heavy
    if title_draws is not None:
        thr = float(title_draws)
    elif heavy > light:
        thr = (light + heavy) / 2.0
    else:
        return None, info
    info['title_thr'] = thr
    prefix = [0]
    for d in draws:
        prefix.append(prefix[-1] + (1 if d >= thr else 0))
    j = 0
    for i in range(n):
        if draws[i] < thr:
            continue
        j = max(j, i)
        limit = t[i] + sustain_s
        while j < n and t[j] < limit:
            j += 1
        if j >= n:
            break
        if prefix[j + 1] - prefix[i] >= frac * (j - i + 1):
            return t[i], info
    return None, info


def scan_logs(run):
    res = {'have_log': False, 'first_wall': None, 'ff_wall': None, 'term_wall': None, 'install_fail': 0}
    logs = sorted(glob.glob(os.path.join(run, 'game*.log')))
    main = os.path.join(run, 'game.log')
    for lp in logs:
        res['have_log'] = True
        is_main = os.path.normcase(lp) == os.path.normcase(main)
        try:
            f = open(lp, encoding='utf-8', errors='replace')
        except OSError:
            continue
        with f:
            for line in f:
                if 'FAILED' in line and INSTALL_RE.search(line):
                    res['install_fail'] += 1
                if not is_main:
                    continue
                want_first = res['first_wall'] is None
                want_ff = res['ff_wall'] is None and FF_MARK in line
                want_term = TERM_MARK in line
                if want_first or want_ff or want_term:
                    m = TS_RE.match(line)
                    ts = parse_wall(m.group(1)) if m else None
                    if ts is None:
                        continue
                    if want_first:
                        res['first_wall'] = ts
                    if want_ff:
                        res['ff_wall'] = ts
                    if want_term:
                        res['term_wall'] = ts
    return res


def launch_wall(rj):
    if not isinstance(rj, dict):
        return None, None
    mark = rj.get('process_start_mark')
    if isinstance(mark, dict) and parse_wall(mark.get('wall')):
        return parse_wall(mark.get('wall')), 'process_start_mark'
    for key in ('process_start', 'start'):
        w = parse_wall(rj.get(key))
        if w:
            return w, key
    return None, None


_RESULTS = {}


def results_row(run):
    matrix_dir = os.path.dirname(os.path.dirname(run))
    path = os.path.join(matrix_dir, 'results.csv')
    if path not in _RESULTS:
        rows = {}
        if os.path.isfile(path):
            try:
                with open(path, newline='', encoding='utf-8-sig', errors='replace') as f:
                    for row in csv.DictReader(f):
                        rd = (row.get('run_dir') or '').rstrip('\\/')
                        if rd:
                            rows[os.path.basename(rd).lower()] = row
            except OSError:
                pass
        _RESULTS[path] = rows
    return _RESULTS[path].get(os.path.basename(run).lower())


def arm_of(run, rj):
    name = os.path.basename(run.rstrip('\\/'))
    tag = rj.get('tag') if isinstance(rj, dict) else None
    if not tag:
        m = HHMM_RE.match(name)
        tag = m.group(1) if m else name
    cold = tag.startswith('cold-')
    core = tag[5:] if cold else tag
    m = REP_RE.match(core)
    if m:
        return tag, m.group(1), int(m.group(2)), cold
    return tag, core, None, cold


def score_run(run, args):
    rj = load_json(os.path.join(run, 'run.json')) or {}
    tag, arm, rep, cold = arm_of(run, rj)
    native_path = os.path.join(run, 'native-frames.csv')
    perf_path = os.path.join(run, 'perf.csv')
    native = read_frames(native_path, 'interval_ms', 1.0, cap_col='native_fps_limit_cvar') \
        if os.path.isfile(native_path) else None
    perf = read_frames(perf_path, 'frame_time_us', 0.001, drop_leading_zero=True) \
        if os.path.isfile(perf_path) else None
    if native and native[0]:
        src, (iv, draws, caps, bad) = 'native', native
    elif perf and perf[0] and args.perf_only_ok:
        src, (iv, draws, caps, bad) = 'perf', perf
    else:
        return None
    r = {k: None for k in CSV_FIELDS}
    excl, info = [], []
    r.update(run_dir=run, matrix=os.path.basename(os.path.dirname(os.path.dirname(run))),
             run=os.path.basename(run), tag=tag, arm=arm, rep=rep, cold=cold, src=src,
             rows=len(iv), bad_rows=bad, mode=rj.get('mode') or 'boot',
             bin=os.path.basename(str(rj.get('bin_dir') or '').rstrip('\\/')) or None)
    t = cumulative_s(iv)
    r['total_s'] = t[-1] if t else 0.0
    stats, k = window_stats(iv, t, args.seconds)
    r.update(stats)
    if not stats['frames']:
        excl.append('no_frames')
    if r['total_s'] < args.seconds:
        excl.append('short')
    if cold:
        excl.append('cold')
    window_caps = [c for c in caps[:k] if not math.isnan(c)]
    if window_caps and max(window_caps) > 0:
        r['fps_cap'] = max(window_caps)
        info.append(f'cap{int(max(window_caps))}')
    elif window_caps:
        r['fps_cap'] = 0
    # perf.csv cross-check (native runs only)
    if src == 'native' and perf and perf[0]:
        pt = cumulative_s(perf[0])
        pstats, _ = window_stats(perf[0], pt, args.seconds)
        r['perf_rows'] = len(perf[0])
        r['perf_max_ms'] = pstats.get('max_ms')
        r['perf_o33'] = pstats.get('o33')
        if stats['frames'] and (pstats.get('max_ms') is None
                                or abs(pstats['max_ms'] - stats['max_ms']) > 1.0
                                or abs(pstats['o33'] - stats['o33']) > 1):
            info.append('perf_mismatch')
    elif src == 'native':
        info.append('no_perf_csv')
    else:
        info.append('perf_only')
    # title (draw-count switch)
    title, levels = title_switch(t, draws, args.seconds, args.title_draws)
    r.update(levels)
    r['ff_title_s'] = title
    if title is None and src == 'native':
        excl.append('no_title')
    if title is not None:
        a, b = bisect.bisect_left(t, title - 2.0), bisect.bisect_right(t, title + 5.0)
        r['title_max_ms'] = max(iv[a:b]) if b > a else None
    r['o20_late'] = sum(1 for v in iv[bisect.bisect_right(t, 5.0):k] if v > 20.0)
    if r['o20_late'] > 20:
        info.append('noisy')
    # the runner's scored window start on the frame clock (frames.window.first_row)
    frames_rj = rj.get('frames') if isinstance(rj.get('frames'), dict) else {}
    win_rj = frames_rj.get('window') if isinstance(frames_rj.get('window'), dict) else {}
    first_row = win_rj.get('first_row')
    if src == 'native' and isinstance(first_row, (int, float)) and 0 < first_row <= len(t):
        r['ff_win_s'] = t[int(first_row) - 1]
        if r['ff_win_s'] < args.win_floor - 0.5:
            info.append(f'win<{args.win_floor:g}s')
    # launch -> first frame
    logs = scan_logs(run)
    launch, launch_ref = launch_wall(rj)
    r['launch_ref'] = launch_ref
    if logs['have_log']:
        r['install_fail'] = logs['install_fail']
        if logs['install_fail'] < LIGHT_PHASE_MIN_INSTALL:
            excl.append('light_phase')
    else:
        info.append('no_log')
    if launch and logs['first_wall']:
        r['launch_log_s'] = (logs['first_wall'] - launch).total_seconds()
    if launch and logs['ff_wall']:
        r['ff_log_s'] = (logs['ff_wall'] - launch).total_seconds()
    end_wall = logs['term_wall']
    if end_wall is None and isinstance(rj.get('close'), dict):
        end_wall = parse_wall(rj['close'].get('wm_close_post_wall'))
    if launch and end_wall and t:
        r['ff_tail_s'] = (end_wall - launch).total_seconds() - t[-1]
    sig = rj.get('first_frame_signal_s')
    r['ff_signal_s'] = sig if isinstance(sig, (int, float)) else None
    for key, name in (('ff_log_s', 'log'), ('ff_tail_s', 'tail'), ('ff_signal_s', 'signal')):
        if r[key] is not None:
            r['launch_ff_s'], r['ff_src'] = r[key], name
            break
    if r['ff_src'] != 'log':
        info.append(f"ff_{r['ff_src'] or 'none'}")
    if r['launch_ff_s'] is not None and title is not None:
        r['launch_title_s'] = r['launch_ff_s'] + title
    # runner status and flags
    status = rj.get('status')
    if status and status != 'OK':
        excl.append(f'status:{status}')
    runner_flags = rj.get('flags_excluding')
    if not isinstance(runner_flags, list):
        row = results_row(run)
        runner_flags = (row.get('flags_excluding') or '').split() if row else []
    for flag in runner_flags:
        flag = str(flag)
        if flag in IGNORED_RUNNER_FLAGS:
            info.append(flag)
        elif flag != 'light_phase' or 'light_phase' not in excl:
            excl.append(f'runner:{flag}' if flag != 'light_phase' else 'light_phase')
    if r['mode'] != 'TIMING':
        info.append(f"mode:{r['mode']}")
    r['excluded'] = bool(excl)
    r['flags_excl'] = ' '.join(excl)
    r['flags_info'] = ' '.join(info)
    return r


def midranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for x in range(i, j + 1):
            ranks[order[x]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def perm_p(a, b, limit=300000):
    n1, n2 = len(a), len(b)
    if n1 < 2 or n2 < 2 or math.comb(n1 + n2, n1) > limit:
        return None
    ranks = midranks(list(a) + list(b))
    mean = n1 * (n1 + n2 + 1) / 2.0
    observed = abs(sum(ranks[:n1]) - mean)
    hits = total = 0
    for combo in itertools.combinations(ranks, n1):
        total += 1
        if abs(sum(combo) - mean) >= observed - 1e-9:
            hits += 1
    return hits / total


def fmt(value, decimals):
    if value is None:
        return '-'
    if isinstance(value, bool):
        return 'yes' if value else ''
    if isinstance(value, float):
        return f'{value:.{decimals}f}'
    return str(value)


def summarize(runs, args):
    arms = {}
    for r in runs:
        arms.setdefault(r['arm'], []).append(r)
    summary = {}
    for arm, rs in arms.items():
        inc = [r for r in rs if not r['excluded']]
        entry = {'n': len(inc), 'excluded': len(rs) - len(inc), 'metrics': {}}
        for key, _, _ in METRICS:
            vals = [r[key] for r in inc if r[key] is not None]
            if vals:
                entry['metrics'][key] = {'median': statistics.median(vals), 'min': min(vals),
                                         'max': max(vals), 'n': len(vals), 'values': vals}
        summary[arm] = entry
    ref = args.ref
    if ref is None:
        ref = 'u0' if 'u0' in summary else next(iter(summary), None)
    compare = []
    if ref in summary and len(summary) > 1:
        for arm, entry in summary.items():
            if arm == ref:
                continue
            row = {'arm': arm, 'ref': ref, 'n': entry['n'], 'n_ref': summary[ref]['n'], 'metrics': {}}
            for key, _, _ in METRICS:
                a = entry['metrics'].get(key)
                b = summary[ref]['metrics'].get(key)
                if a and b:
                    row['metrics'][key] = {'delta': a['median'] - b['median'],
                                           'p': perm_p(a['values'], b['values'])}
            compare.append(row)
    return summary, ref, compare


def render_md(runs, summary, ref, compare, args):
    out = []
    out.append(f'# Load-phase score: first {args.seconds:g} s after the first frame')
    out.append('')
    out.append('Frames over 33/50/100 ms, hitch ms = sum of (frame - 33 ms) over those frames, '
               'max and p99 (nearest rank) from native-frames.csv; launch = runner process start; '
               'ff = first frame (game.log "Native presentation: frame=0"); title = draw-count switch; '
               'title max = max frame from 2 s before to 5 s after the switch; o20 5s+ = frames > 20 ms '
               'from 5 s to the window end (busy-machine indicator); ff->win s = first frame to the '
               'start of the runner\'s scored window on the frame clock (info flag win<60s below the floor). '
               'Excluded runs are listed but left out of the arm numbers.')
    out.append('')
    out.append('## Runs')
    out.append('')
    cols = ['run', 'arm', 'rep', 'bin', 'launch->ff s', 'ff src', 'ff->title s', 'launch->title s',
            'draws', 'title max ms', 'frames', 'o33', 'o50', 'o100', 'hitch ms', 'max ms', 'p99 ms',
            'fps', 'o20 5s+', 'ff->win s', 'excluded by', 'info']
    out.append('| ' + ' | '.join(cols) + ' |')
    out.append('|' + '---|' * len(cols))
    for r in runs:
        draws = '-' if r['light_draws'] is None else f"{r['light_draws']:g}->{r['heavy_draws']:g}"
        cells = [r['run'], r['arm'], 'cold' if r['cold'] else fmt(r['rep'], 0), r['bin'] or '-',
                 fmt(r['launch_ff_s'], 2), r['ff_src'] or '-', fmt(r['ff_title_s'], 2),
                 fmt(r['launch_title_s'], 2), draws, fmt(r['title_max_ms'], 1), fmt(r['frames'], 0),
                 fmt(r.get('o33'), 0), fmt(r.get('o50'), 0), fmt(r.get('o100'), 0),
                 fmt(r.get('hitch_ms'), 0), fmt(r.get('max_ms'), 1), fmt(r.get('p99_ms'), 2),
                 fmt(r.get('fps'), 0), fmt(r['o20_late'], 0), fmt(r.get('ff_win_s'), 1),
                 r['flags_excl'] or '', r['flags_info'] or '']
        out.append('| ' + ' | '.join(cells) + ' |')
    out.append('')
    out.append('## Arms (median [min..max] over the included runs)')
    out.append('')
    cols = ['arm', 'n', 'excl'] + [label for _, label, _ in METRICS]
    out.append('| ' + ' | '.join(cols) + ' |')
    out.append('|' + '---|' * len(cols))
    for arm, entry in summary.items():
        cells = [arm, str(entry['n']), str(entry['excluded'])]
        for key, _, dec in METRICS:
            m = entry['metrics'].get(key)
            if not m:
                cells.append('-')
            elif m['n'] == 1:
                cells.append(fmt(m['median'], dec))
            else:
                cells.append(f"{fmt(m['median'], dec)} [{fmt(m['min'], dec)}..{fmt(m['max'], dec)}]")
        out.append('| ' + ' | '.join(cells) + ' |')
    if compare:
        out.append('')
        out.append(f'## Versus {ref} (difference of medians; exact two-sided rank-sum p)')
        out.append('')
        cols = ['arm', 'n vs n_ref'] + [label for _, label, _ in METRICS]
        out.append('| ' + ' | '.join(cols) + ' |')
        out.append('|' + '---|' * len(cols))
        for row in compare:
            cells = [row['arm'], f"{row['n']} vs {row['n_ref']}"]
            for key, _, dec in METRICS:
                m = row['metrics'].get(key)
                if not m:
                    cells.append('-')
                else:
                    p = '-' if m['p'] is None else f"{m['p']:.3f}"
                    cells.append(f"{m['delta']:+.{max(dec, 1)}f} (p {p})")
            out.append('| ' + ' | '.join(cells) + ' |')
        out.append('')
        out.append('p is "-" below 2 runs per side. Smallest possible p: 0.10 at 3 vs 3, 0.029 at 4 vs 4, '
                   '0.008 at 5 vs 5. Small counts (o50, o100) tie often; ties give large p.')
    return '\n'.join(out) + '\n'


def write_text(path, text):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('paths', nargs='+', help='run dirs, matrix output dirs or parents')
    ap.add_argument('--seconds', type=float, default=60.0, help='load window after the first frame (60)')
    ap.add_argument('--ref', default=None, help='reference arm for the comparison (u0 if present)')
    ap.add_argument('--title-draws', type=float, default=None,
                    help='draw-count threshold for the title switch (default: light/heavy midpoint)')
    ap.add_argument('--win-floor', type=float, default=60.0,
                    help='info flag win<Ns when the scored window starts earlier than this after the first frame (60)')
    ap.add_argument('--perf-only-ok', action='store_true',
                    help='also score runs that only have perf.csv (no title switch)')
    ap.add_argument('--csv', help='write the per-run table as CSV')
    ap.add_argument('--md', help='write the markdown report')
    ap.add_argument('--json', help='write runs, arms and comparisons as JSON')
    ap.add_argument('--quiet', action='store_true', help='do not print the markdown report')
    args = ap.parse_args(argv)

    dirs = find_runs(args.paths)
    runs = []
    for d in dirs:
        r = score_run(d, args)
        if r is not None:
            runs.append(r)
    if not runs:
        print('no runs with native-frames.csv found', file=sys.stderr)
        return 1
    summary, ref, compare = summarize(runs, args)
    md = render_md(runs, summary, ref, compare, args)
    if not args.quiet:
        sys.stdout.write(md)
    if args.md:
        write_text(args.md, md)
    if args.csv:
        os.makedirs(os.path.dirname(os.path.abspath(args.csv)), exist_ok=True)
        with open(args.csv, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=CSV_FIELDS, lineterminator='\n', extrasaction='ignore')
            w.writeheader()
            for r in runs:
                w.writerow({k: ('' if r.get(k) is None else
                                (f'{r[k]:.4f}' if isinstance(r[k], float) else r[k])) for k in CSV_FIELDS})
    if args.json:
        payload = {'seconds': args.seconds, 'ref': ref, 'runs': runs,
                   'arms': {a: {**e, 'metrics': {k: {kk: vv for kk, vv in m.items()}
                                                 for k, m in e['metrics'].items()}}
                            for a, e in summary.items()},
                   'compare': compare}
        write_text(args.json, json.dumps(payload, indent=1, default=str) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())

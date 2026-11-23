#!/usr/bin/env python3
"""W4b read-out add-on (Agent 7, task #29): p50, p99, 1% low and >33 ms frames per minute next to the mean fps, per
run and per arm, over each run's scored window, plus a scene check against the reference arm and the slow-state flag.

Usage:
  python bench\\agent7\\w4b_readout\\w4b_readout.py <matrix out dir> [-o OUT.md] [--json OUT.json] [--ref ARM]
         [--all] [--keep-flagged] [--no-timerq] [--scene-floor 0.015] [--scene-factor 2.0]
         [--slow-emhz 800] [--slow-rows 3] [--min-cover 0.9] [--bin-s 10]
         [--bg-ref DIR|none] [--bg-ref-cores X] [--bg-margin 1.0] [--sat-busy 0.97]

Input: a run-matrix.ps1 output dir (results.csv, matrix.json, runs\\<run>\\frames.json, the frame csv, run.json,
sys.csv, proc.csv). It writes nothing except -o and --json (and no __pycache__: sys.dont_write_bytecode).

Window: the runner's own scored window, i.e. frames.json window.first_row .. + window.rows of the frame csv that
frames.json names (perf.csv frame_time_us, or native-frames.csv interval_ms), rows parsed by frame_summary.py's rules,
frames with a frame time <= 0 left out. Every run is checked against frames.json (frames, mean fps, p50, p99, >33) and
results.csv (fps_mean).
  fps       frames / summed frame time (= frames.json mean_fps = results.csv fps_mean)
  p50, p99  nearest-rank, sorted[ceil(p*n)-1], as frame_summary.py (= results.csv median_ms, p99_ms)
  1% low    1000 / mean of the slowest max(1, n // 100) frame times in ms, in fps (task #26 definition)
  >33/min   frames over 33 ms per minute of summed frame time
Bins (task #9): fps, p99, 1% low and >33/min also per consecutive --bin-s (default 10) s of summed frame time
from the start of each run's scored window: a frame belongs to the bin in which it ends, a last part shorter than
half a bin is merged into the bin before it. Per run, plus the per-arm median of the kept runs per bin.
Kept runs, as matrix_recheck.py: scored, with frame stats, no real problems (matrix_recheck.classify), not excluded
(--keep-flagged keeps them), valid timing (--all keeps functional runs). Per arm: the median (min..max) across the kept
runs; an arm with fewer than 3 kept runs is marked n<3!. Deltas: arm median against the reference arm's median
(matrix.json ref arm, else "reference", else --ref), better/worse only when every run lies outside the reference
range, plus a per-round paired fps delta. When a kept run has the slow state in its window, a scene flag or a
background flag (BG+, or SAT unless every kept run is SAT), the arm and delta tables are repeated without those runs.
Scene check (perf.csv frames only): the time-weighted distribution of perf.csv draw_calls per frame over the window,
against the pooled windows of the kept reference runs: 1-D Wasserstein distance on ln(1 + draws) (0.10 ~ draws about
10 % apart on average; +-1 draw jitter costs ~0.005). A run is flagged SCENE? when its distance exceeds
max(--scene-floor, --scene-factor x the largest leave-one-out distance among the reference runs). The default floor
0.015 is calibrated on the 2026-11-21/22 matrices: runs in the same scene differ by 0.000-0.005 (window 3's d0 runs
0.000, 0346-d3-r1 0.005); window 3's light-phase run 0025-d11-r1 sits at 0.036 (draws 218 vs 226, 294.6 fps); unscored
cold runs at 0.016-0.019. The runner's phase flag (light_phase, INSTALL*.DAT fails, share of frames < 4.5 ms) is
shown next to it; window 3 predates it.
Slow state: matrix_recheck.slow_state / slow_txt (imported read-only from bench\\agent8\\run\\matrix_recheck.py:
onset s after the first-frame signal / share of window samples with the E-cores < 800 MHz, '!' = in the window) and
bench\\agent11\\timerq_slowstate.ps1 -Root <parent> -Since <dir name> (run read-only as a subprocess; onset s / share of
the samples from the first frame on; --no-timerq skips it).
Background load (Agent 1's add-on): per run, the system's busy cores minus the game's cores over the scored window
(run.json measure_start.epoch_s + frames.json window_s). System = logical CPUs x min(1, cpu_util_pct / cpu_perf_pct)
per sys.csv sample (_Total % Processor Utility / % Processor Performance = the busy share without the frequency
scaling); game = the slope of proc.csv cpu_s (placed on the epoch time line by its 'measure start' row). SAT = median
busy share >= --sat-busy: no spare CPU, so the background reading is only a floor. BG+ = not SAT and background >
reference + --bg-margin; reference = --bg-ref-cores, else the median of the unsaturated scored runs of --bg-ref
(default window 3, build\\agent8\\matrix\\20261122-0013), else of this matrix's own unsaturated scored runs. BG+ runs
(and SAT runs, unless every kept run is SAT) are left out of the clean arm table.
Stdlib only, one thread (plus one PowerShell process for timerq_slowstate.ps1).
"""
import argparse
import bisect
import csv
import importlib.util
import json
import math
import os
import re
import statistics
import subprocess
import sys

sys.dont_write_bytecode = True  # no __pycache__ next to Agent 8's tools (or here)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
RECHECK = os.path.join(REPO, 'bench', 'agent8', 'run', 'matrix_recheck.py')
TIMERQ = os.path.join(REPO, 'bench', 'agent11', 'timerq_slowstate.ps1')
SLOW_MS = 33.0
MATRIX_RE = re.compile(r'^\d{8}-\d{4}$')
# (key, +1 = higher is better / -1 = lower is better, decimals, label)
METRICS = (('fps', 1, 1, 'fps'), ('p50_ms', -1, 3, 'p50 ms'), ('p99_ms', -1, 2, 'p99 ms'),
           ('low1_fps', 1, 1, '1% low fps'), ('over33_min', -1, 1, '>33 ms/min'))
SAT_BUSY = 0.97  # median busy share from which a window counts as CPU-saturated
SCENE_FLOOR = 0.015  # same-scene runs 0.000-0.005 tonight; window 3's light-phase run 0025-d11-r1 0.036
BIN_S = 10.0  # task #9: per-run bins of this many seconds of summed frame time
# (key, decimals, label) of the per-bin tables
BIN_METRICS = (('fps', 1, 'fps'), ('p99_ms', 2, 'p99 ms'), ('low1_fps', 1, '1% low fps'),
               ('over33_min', 1, '>33 ms/min'))
W3_DIR = os.path.join(REPO, 'build', 'agent8', 'matrix', '20261122-0013')  # window 3: the default --bg-ref


def load_module(name, path):
    """Import a tool by its path, read-only (sys.dont_write_bytecode is set, so no .pyc is written next to it)."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mr = load_module('matrix_recheck', RECHECK)


def num(s):
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def load_json(path):
    try:
        with open(path, encoding='utf-8-sig') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def f(v, nd=2, dash='-'):
    return dash if v is None else '%.*f' % (nd, v)


def fsgn(v, nd=1, dash='-'):
    return dash if v is None else '%+.*f' % (nd, v)


def rng(a, nd):
    return '%s (%s..%s)' % (f(a['med'], nd), f(a['lo'], nd), f(a['hi'], nd))


def nearest_rank(s, num_, den):
    """frame_summary.py's percentile: sorted[ceil(num/den * n) - 1], exact integer arithmetic."""
    n = len(s)
    k = -(-num_ * n // den)
    return s[max(1, min(n, k)) - 1]


def load_frames(path, source, column, scale, extra=(), stop_after=None):
    """Frame times (us) and extra columns of the good rows of a frames csv, by frame_summary.py's rules: a row needs
    the header's field count, perf.csv rows need every field to be an integer, other sources need a float in the
    column; a last line without a newline is dropped. Good rows are indexed like frame_summary.load, so frames.json
    window.first_row applies. Returns (header, frame times, {extra column: values}); header None for an empty file."""
    with open(path, 'rb') as fh:
        data = fh.read()
    nl = data.find(b'\n')
    if nl < 0:
        return None, [], {}
    header = [h.strip() for h in data[:nl].decode('ascii', 'replace').rstrip('\r').split(',')]
    if column not in header:
        return header, [], {}
    col, width, integer = header.index(column), len(header), source == 'perf'
    xcols = [(c, header.index(c)) for c in extra if c in header]
    fts, xs = [], {c: [] for c, _ in xcols}
    pos, end = nl + 1, len(data)
    while pos < end:
        if stop_after is not None and len(fts) >= stop_after:
            break
        nl = data.find(b'\n', pos)
        if nl < 0:
            break
        parts = data[pos:nl].rstrip(b'\r').split(b',')
        pos = nl + 1
        try:
            if len(parts) != width:
                raise ValueError
            if integer:
                vals = [int(p) for p in parts]
                v = vals[col] if scale == 1.0 else vals[col] * scale
            else:
                v = float(parts[col]) * scale
        except ValueError:
            continue
        fts.append(v)
        for c, i in xcols:
            xs[c].append(num(parts[i]))
    return header, fts, xs


def window_stats(fts):
    """fps, p50, p99, 1% low and >33 ms per minute over frame times in us (values <= 0 left out)."""
    v = [x for x in fts if x > 0]
    n = len(v)
    if not n:
        return None
    s = sorted(v)
    total = float(sum(v))
    k = max(1, n // 100)
    over33 = sum(1 for x in v if x > SLOW_MS * 1000.0)
    return {
        'frames': n, 'window_s': total / 1e6, 'fps': n * 1e6 / total,
        'p50_ms': nearest_rank(s, 1, 2) / 1000.0, 'p99_ms': nearest_rank(s, 99, 100) / 1000.0,
        'low1_fps': 1e6 * k / float(sum(s[-k:])), 'low1_frames': k,
        'over33': over33, 'over33_min': over33 * 6e7 / total,
    }


def stat_bins(fts, bin_s=BIN_S):
    """window_stats per consecutive bin_s seconds of summed frame time from the window start (task #9), over the
    frames window_stats uses (frame times in us, values <= 0 left out). A frame belongs to the bin in which it ends
    (a frame ending exactly on a boundary closes the earlier bin); a last part shorter than bin_s / 2 is merged into
    the bin before it; a bin in which no frame ends (a frame longer than a bin) is kept with frames 0. Returns a
    list of dicts: bin (index), t0, t1 (s from the window start on the summed frame time line; t1 of the last bin =
    the window length) and window_stats' keys (frames 0 only for an empty bin)."""
    v = [x for x in fts if x > 0]
    if not v or not bin_s or bin_s <= 0:
        return []
    lim = bin_s * 1e6
    groups, cum = [], 0.0
    for x in v:
        cum += x
        b = int(max(0.0, cum - 1e-3) // lim)
        while len(groups) <= b:
            groups.append([])
        groups[b].append(x)
    total_s = cum / 1e6
    if len(groups) >= 2 and total_s - bin_s * (len(groups) - 1) < bin_s / 2.0:
        tail = groups.pop()
        groups[-1].extend(tail)
    out = []
    for i, g in enumerate(groups):
        d = {'bin': i, 't0': i * bin_s, 't1': total_s if i == len(groups) - 1 else (i + 1) * bin_s}
        d.update(window_stats(g) or {'frames': 0})
        out.append(d)
    return out


def check_run(st, fj, row):
    """Differences between this tool's window stats and frames.json / results.csv (an empty list = they agree)."""
    bad = []

    def cmp(label, mine, theirs, tol):
        t = num(theirs)
        if t is None:
            return
        if mine is None or abs(mine - t) > tol:
            bad.append('%s %s vs %s' % (label, mine, theirs))

    cmp('frames', st['frames'], fj.get('frames'), 0.5)
    cmp('fps', round(st['fps'], 3), fj.get('mean_fps'), 0.0006)
    cmp('p50', st['p50_ms'], fj.get('median_ms'), 1e-5)
    cmp('p99', st['p99_ms'], fj.get('p99_ms'), 1e-5)
    cmp('>33', st['over33'], fj.get('over_33ms'), 0.5)
    cmp('results.csv fps_mean', round(st['fps'], 3), row.get('fps_mean'), 0.0006)
    return bad


def scene_hist(draws, fts):
    """Time-weighted distribution {draws per frame: share of the window time} over frames with a frame time > 0."""
    h, tot = {}, 0.0
    for dc, t in zip(draws, fts):
        if t > 0 and dc is not None and dc >= 0:
            k = int(dc)
            h[k] = h.get(k, 0.0) + t
            tot += t
    if tot <= 0:
        return None
    return {k: v / tot for k, v in h.items()}


def draws_bins(draws, fts, bin_s=10.0):
    """Time-weighted mean draws per frame in consecutive bin_s seconds of summed frame time (a last partial bin kept)."""
    out, acc, dsum = [], 0.0, 0.0
    for dc, t in zip(draws, fts):
        if t <= 0 or dc is None:
            continue
        acc += t
        dsum += dc * t
        if acc >= bin_s * 1e6:
            out.append(round(dsum / acc, 1))
            acc, dsum = 0.0, 0.0
    if acc > 0:
        out.append(round(dsum / acc, 1))
    return out


def pool(hists):
    """Equal-weight mixture of distributions."""
    out = {}
    for h in hists:
        for k, v in h.items():
            out[k] = out.get(k, 0.0) + v / len(hists)
    return out


def w1_log(a, b):
    """1-D Wasserstein distance between two distributions over draw counts, on x = ln(1 + draws)."""
    xs = sorted(set(a) | set(b))
    fa = fb = d = 0.0
    for x, nx in zip(xs, xs[1:]):
        fa += a.get(x, 0.0)
        fb += b.get(x, 0.0)
        d += abs(fa - fb) * (math.log1p(nx) - math.log1p(x))
    return d


def wquantile(h, q):
    acc = 0.0
    ks = sorted(h)
    for k in ks:
        acc += h[k]
        if acc >= q - 1e-9:
            return k
    return ks[-1]


def wmean(h):
    return sum(k * v for k, v in h.items())


def parse_timerq(text, name):
    """Rows of timerq_slowstate.ps1's table for matrix dir `name`: {run dir name: {...}}."""
    out = {}
    for ln in (text or '').splitlines():
        t = ln.split()
        if len(t) >= 6 and t[0] == name:
            out[t[1]] = {'blocking': t[2], 'onset_s': t[3], 'slow_pct': t[4], 'span_s': t[5],
                         'fg': t[6] if len(t) > 6 else ''}
    return out


def run_timerq(matrix_dir, emhz, srows, timeout=900):
    """Agent 11's scan, unchanged and read-only: -Root <parent> -Since <dir name>. It also scans later matrix dirs;
    only this dir's rows are used. Returns (rows or None, note)."""
    d = os.path.abspath(matrix_dir)
    name, root = os.path.basename(d), os.path.dirname(d)
    if not MATRIX_RE.match(name):
        return None, 'skipped: the dir name is not yyyymmdd-hhmm'
    if not os.path.isfile(TIMERQ):
        return None, 'skipped: %s not found' % TIMERQ
    cmd = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', TIMERQ, '-Root', root, '-Since', name,
           '-EMhz', '%g' % emhz, '-MinRows', str(srows)]
    shown = 'powershell -NoProfile -ExecutionPolicy Bypass -File %s -Root %s -Since %s -EMhz %g -MinRows %d' % (
        os.path.relpath(TIMERQ, REPO), root, name, emhz, srows)
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as e:
        return None, 'failed (%s): %s' % (shown, e)
    if p.returncode != 0:
        err = (p.stderr or p.stdout or '').strip().splitlines()
        return None, 'failed (%s): exit %d%s' % (shown, p.returncode, (': ' + err[0]) if err else '')
    return parse_timerq(p.stdout, name), 'ran `%s`' % shown


def read_rows(path):
    """csv.DictReader rows of a file (None when it can't be read)."""
    try:
        with open(path, encoding='utf-8-sig', errors='replace', newline='') as fh:
            return list(csv.DictReader(fh))
    except OSError:
        return None


def interp(xs, ys, x):
    """Linear interpolation of ys(xs) (xs strictly ascending) at x; None outside [xs[0], xs[-1]]."""
    if not xs or x < xs[0] or x > xs[-1]:
        return None
    i = bisect.bisect_left(xs, x)
    if xs[i] == x:
        return ys[i]
    x0, x1 = xs[i - 1], xs[i]
    return ys[i - 1] + (ys[i] - ys[i - 1]) * (x - x0) / (x1 - x0)


def game_cpu(rd, rj, fj):
    """The game's cumulative CPU seconds from proc.csv on the epoch time line, and the scored window.
    proc.csv t_s are mapped to epoch s by its 'measure start' row = run.json measure_start.epoch_s (fallback: the
    first-frame signal, ff_signal_epoch_s = first_frame_signal_s). Window = [measure start, + frames.json window_s]:
    the runner's scored frames start at the measure start (frames.json window.start_bytes = the perf.csv size there).
    Returns ((epochs, cpu_s), (ws, we), None) or (None, None, note)."""
    prows = read_rows(os.path.join(rd, 'proc.csv')) if rd else None
    if prows is None:
        return None, None, 'no proc.csv'
    ms = rj.get('measure_start') if isinstance(rj.get('measure_start'), dict) else {}
    ms_e = num(ms.get('epoch_s'))
    if ms_e is None:
        sysb = rj.get('sys') if isinstance(rj.get('sys'), dict) else {}
        ms_e = num(sysb.get('window_start_epoch'))
    pts, t_ms = {}, None
    for r in prows:
        t, c = num(r.get('t_s')), num(r.get('cpu_s'))
        if t is None:
            continue
        if t_ms is None and 'measure start' in (r.get('note') or ''):
            t_ms = t
        if c is not None:
            pts[t] = c
    off = None
    if ms_e is not None and t_ms is not None:
        off = ms_e - t_ms
    else:
        ff_e, ff_t = num(rj.get('ff_signal_epoch_s')), num(rj.get('first_frame_signal_s'))
        if ff_e is not None and ff_t is not None:
            off = ff_e - ff_t
    if ms_e is None or off is None or not pts:
        return None, None, 'no measure-start time or no cpu_s in proc.csv'
    w = num((fj or {}).get('window_s'))
    if w is None:
        me = rj.get('measure_end') if isinstance(rj.get('measure_end'), dict) else {}
        me_e = num(me.get('epoch_s'))
        w = None if me_e is None else me_e - ms_e
    if not w or w <= 0:
        return None, None, 'no window length'
    ts = sorted(pts)
    return ([t + off for t in ts], [pts[t] for t in ts]), (ms_e, ms_e + w), None


def game_window(rd, rj, fj):
    """The game's cores over the scored window: proc.csv cpu_s at the two window ends (linear interpolation), else
    run.json window_cpu_cores_mean (the runner's mean over its measure-phase samples). Returns (cores or None, source
    or note, (epochs, cpu_s) or None, (ws, we) or None)."""
    series, win, note = game_cpu(rd, rj, fj)
    if series is not None:
        a, b = interp(series[0], series[1], win[0]), interp(series[0], series[1], win[1])
        if a is not None and b is not None:
            return (b - a) / (win[1] - win[0]), 'proc.csv', series, win
        note = 'proc.csv does not cover the window'
    rm = num(rj.get('window_cpu_cores_mean'))
    if rm is not None:
        return rm, 'run.json window_cpu_cores_mean', series, win
    return None, note, series, win


def bg_load(rd, rj, fj, sat_busy=SAT_BUSY):
    """Background CPU over the scored window = the system's busy cores minus the game's cores, per sys.csv sample
    whose interval centre lies in the window. System (sys.csv, 1 s PDH samples): logical CPUs x min(1, cpu_util_pct /
    cpu_perf_pct): _Total % Processor Utility over % Processor Performance = the busy share without the frequency
    scaling, in the units of process CPU time (live check without a game, 17 x 1 s samples, also with a 1 ms timer
    resolution: 0.01-0.07 above % Processor Time / 100). Game: the slope of proc.csv cpu_s over the same interval
    (else game_window's window value). SAT = median busy share >= sat_busy. Returns (dict or None, note)."""
    srows = read_rows(os.path.join(rd, 'sys.csv')) if rd else None
    if srows is None:
        return None, 'no sys.csv'
    gw, gsrc, series, win = game_window(rd, rj, fj)
    if win is None or series is None:
        return None, 'no scored-window time (%s)' % gsrc
    ws, we = win
    pe, pc = series
    n = num(rj.get('logical_cpus')) or float(os.cpu_count() or 0)
    ss = sorted((e, num(r.get('cpu_util_pct')), num(r.get('cpu_perf_pct')))
                for r, e in ((r, num(r.get('epoch_s'))) for r in srows) if e is not None)
    busy, bg, skipped = [], [], 0
    for (e0, _, _), (e1, u, p) in zip(ss, ss[1:]):
        if e1 <= e0 or not ws <= (e0 + e1) / 2.0 <= we:
            continue
        g0, g1 = interp(pe, pc, e0), interp(pe, pc, e1)
        g = (g1 - g0) / (e1 - e0) if g0 is not None and g1 is not None else gw
        if u is None or p is None or p <= 0 or g is None or not n:
            skipped += 1
            continue
        s = min(1.0, max(0.0, u / p))
        busy.append(s)
        bg.append(n * s - g)
    if not bg:
        return None, 'no usable sys.csv sample in the window'
    sb = sorted(bg)
    bmed = statistics.median(busy)
    return {'samples': len(bg), 'skipped': skipped, 'ncpu': n, 'window_s': we - ws, 'busy_med': bmed,
            'sys_cores': n * bmed, 'game_cores': gw, 'game_src': gsrc, 'bg_cores': statistics.median(bg),
            'bg_mean': statistics.fmean(bg), 'bg_p90': nearest_rank(sb, 9, 10), 'bg_max': sb[-1],
            'sat_share': sum(1 for x in busy if x >= sat_busy) / float(len(busy)), 'sat': bmed >= sat_busy}, 'ok'


def resolve_run_dir(d, r):
    """results.csv run_dir, else <matrix dir>\\runs\\<its base name> (a moved matrix)."""
    rd = (r.get('run_dir') or '').strip()
    if not rd or not os.path.isdir(rd):
        alt = os.path.join(d, 'runs', os.path.basename(rd.rstrip('\\/'))) if rd else ''
        rd = alt if alt and os.path.isdir(alt) else rd
    return rd


def bg_reference(ref_dir, sat_busy=SAT_BUSY):
    """Background reference from another matrix dir: the median background of its unsaturated scored runs that have
    sys.csv, plus the median game cores per arm over its scored windows (proc.csv)."""
    d = os.path.abspath(ref_dir)
    out = {'dir': d, 'name': os.path.basename(d), 'scored': 0, 'with_sys': 0, 'sat': 0, 'bg_values': [],
           'bg_med': None, 'game_by_arm': {}}
    rows = read_rows(os.path.join(d, 'results.csv'))
    if rows is None:
        out['note'] = 'no results.csv'
        return out
    games = {}
    for r in rows:
        if (r.get('scored') or '').strip().lower() != 'true':
            continue
        rd = resolve_run_dir(d, r)
        if not rd or not os.path.isdir(rd):
            continue
        out['scored'] += 1
        rj = load_json(os.path.join(rd, 'run.json'))
        fj = load_json(os.path.join(rd, 'frames.json'))
        rj = rj if isinstance(rj, dict) else {}
        fj = fj if isinstance(fj, dict) else None
        g = game_window(rd, rj, fj)[0]
        if g is not None:
            games.setdefault(r.get('arm', ''), []).append(g)
        if os.path.isfile(os.path.join(rd, 'sys.csv')):
            out['with_sys'] += 1
            b = bg_load(rd, rj, fj, sat_busy)[0]
            if b and b['sat']:
                out['sat'] += 1
            elif b:
                out['bg_values'].append(b['bg_cores'])
    out['game_by_arm'] = {a: {'med': statistics.median(v), 'n': len(v)} for a, v in games.items()}
    if out['bg_values']:
        out['bg_med'] = statistics.median(out['bg_values'])
    return out


def phase_text(r):
    lp = (r.get('light_phase') or '').strip().lower()
    dat = (r.get('install_dat_fail') or '').strip()
    ls = num(r.get('light_share'))
    if not lp and not dat and ls is None:
        return '-'
    bits = (['DAT fails %s' % dat] if dat else []) + (['<4.5 ms %.2f' % ls] if ls is not None else [])
    return ('LIGHT' if lp == 'true' else 'normal') + (' (%s)' % ', '.join(bits) if bits else '')


def arm_block(sel, order):
    out = {}
    for arm in order:
        rs = [x for x in sel if x['arm'] == arm]
        if not rs:
            continue
        a = {'n': len(rs), 'n_lt3': len(rs) < 3, 'runs': [x['name'] for x in rs],
             'slow': sum(1 for x in rs if x['slow_win']), 'scene_flags': sum(1 for x in rs if x['scene_flag'])}
        bgv = [x['bg']['bg_cores'] for x in rs if x.get('bg')]
        a['bg'] = {'med': statistics.median(bgv), 'lo': min(bgv), 'hi': max(bgv), 'n': len(bgv)} if bgv else None
        a['bg_plus'] = sum(1 for x in rs if 'BG+' in x.get('bg_flags', ()))
        a['sat'] = sum(1 for x in rs if 'SAT' in x.get('bg_flags', ()))
        for key, _, _, _ in METRICS:
            vals = [x['stats'][key] for x in rs]
            a[key] = {'med': statistics.median(vals), 'lo': min(vals), 'hi': max(vals)}
        m = a['fps']['med']
        a['fps']['spread_pct'] = 100.0 * (a['fps']['hi'] - a['fps']['lo']) / m if m else None
        out[arm] = a
    return out


def delta_block(arms, sel, ref):
    out = {}
    rr = arms.get(ref)
    if not rr:
        return out
    for arm, a in arms.items():
        if arm == ref:
            continue
        dd = {}
        for key, sign, _, _ in METRICS:
            am, rm = a[key]['med'], rr[key]['med']
            if a[key]['lo'] > rr[key]['hi']:
                v = 'better' if sign > 0 else 'worse'
            elif a[key]['hi'] < rr[key]['lo']:
                v = 'worse' if sign > 0 else 'better'
            else:
                v = 'overlap'
            dd[key] = {'delta': am - rm, 'pct': (100.0 * (am - rm) / rm) if rm else None, 'verdict': v}
        byr = {}
        for x in sel:
            byr.setdefault(x['round'], {})[x['arm']] = x['stats']['fps']
        pairs = [100.0 * (v[arm] - v[ref]) / v[ref] for v in byr.values() if arm in v and ref in v and v[ref]]
        dd['paired_fps_pct'] = {'med': statistics.median(pairs) if pairs else None, 'n': len(pairs),
                                'up': sum(1 for p in pairs if p > 0)}
        out[arm] = dd
    return out


def analyse(d, command, ref=None, use_all=False, keep_flagged=False, timerq=True, scene_floor=SCENE_FLOOR,
            scene_factor=2.0, emhz=800.0, srows=3, min_cover=0.9, bg_ref_dir=None, bg_ref_cores=None,
            bg_margin=1.0, sat_busy=SAT_BUSY, bin_s=BIN_S):
    d = os.path.abspath(d)
    res = os.path.join(d, 'results.csv')
    if not os.path.isfile(res):
        raise SystemExit('no results.csv in %s' % d)
    with open(res, encoding='utf-8-sig', errors='replace', newline='') as fh:
        rows = list(csv.DictReader(fh))
    mj = load_json(os.path.join(d, 'matrix.json')) or {}
    cfg = [x for x in (mj.get('arms') or []) if isinstance(x, dict) and x.get('id')]
    present = list(dict.fromkeys(r.get('arm', '') for r in rows))
    cfg_ids = [x['id'] for x in cfg]
    order = [i for i in cfg_ids if i in present] + [a for a in present if a not in cfg_ids]
    if ref is None:
        ref = next((x['id'] for x in cfg if x.get('ref') and x['id'] in present), None)
    if ref is None and mj.get('reference') in present:
        ref = mj.get('reference')
    if ref is None and order:
        ref = order[0]
    tq, tq_note = run_timerq(d, emhz, srows) if timerq else (None, 'skipped (--no-timerq)')

    runs = []
    for r in rows:
        rd = (r.get('run_dir') or '').strip()
        if not rd or not os.path.isdir(rd):
            alt = os.path.join(d, 'runs', os.path.basename(rd.rstrip('\\/'))) if rd else ''
            rd = alt if alt and os.path.isdir(alt) else rd
        name = os.path.basename(rd.rstrip('\\/')) if rd else ''
        rj = load_json(os.path.join(rd, 'run.json')) if rd else None
        rjd = rj if isinstance(rj, dict) else {}
        real, benign = mr.classify(rj if isinstance(rj, dict) else None, r, min_cover)
        scored = (r.get('scored') or '').strip().lower() == 'true'
        valid = (r.get('valid_timing') or '').strip().lower() == 'true'
        fx = mr.as_list(rjd.get('flags_excluding')) or (r.get('flags_excluding') or '').split()
        excluded = bool(rjd.get('excluded')) or bool(fx) or (r.get('excluded') or '').strip().lower() == 'true'
        fj = load_json(os.path.join(rd, 'frames.json')) if rd else None
        st, check, hist, src, fnote, bins, sbins = None, None, None, None, None, None, None
        if isinstance(fj, dict) and isinstance(fj.get('window'), dict):
            src = fj.get('source')
            col = fj.get('column')
            scale = num(fj.get('scale_to_us')) or 1.0
            base = os.path.basename(str(fj.get('file') or ''))
            fpath = os.path.join(rd, base) if base else ''
            if not (fpath and os.path.isfile(fpath)):
                fpath = str(fj.get('file') or '')
            first = int(num(fj['window'].get('first_row')) or 0)
            nrows = int(num(fj['window'].get('rows')) or 0)
            if col and fpath and os.path.isfile(fpath):
                extra = ('draw_calls',) if src == 'perf' else ()
                _, fts, xs = load_frames(fpath, src, col, scale, extra, stop_after=first + nrows)
                win = fts[first:first + nrows]
                st = window_stats(win)
                if st:
                    check = check_run(st, fj, r)
                    sbins = stat_bins(win, bin_s)
                if 'draw_calls' in xs:
                    dwin = xs['draw_calls'][first:first + nrows]
                    hist = scene_hist(dwin, win)
                    bins = draws_bins(dwin, win)
            else:
                fnote = 'frame csv not found'
        else:
            fnote = 'no frames.json window'
        has_frames = st is not None and num(r.get('median_ms')) is not None
        slow = mr.slow_state(rd, rjd, emhz, srows) if rd else None
        slow_win = bool(slow and slow['in_window'])
        fjd = fj if isinstance(fj, dict) else None
        gcores, gsrc = game_window(rd, rjd, fjd)[:2] if rd else (None, 'no run dir')
        bg, bg_note = bg_load(rd, rjd, fjd, sat_busy) if rd else (None, 'no run dir')
        keep = scored and has_frames and not real and (valid or use_all) and (not excluded or keep_flagged)
        why = []
        if not scored:
            why.append('cold (unscored)')
        if not has_frames:
            why.append(fnote or 'no frame stats')
        why.extend('problem: ' + p for p in real)
        if not valid:
            why.append('not timing%s' % (' (kept: --all)' if use_all else ''))
        if excluded:
            why.append('EXCLUDED: %s%s' % (', '.join(fx) or 'excluded', ' (kept: --keep-flagged)' if keep_flagged else ''))
        runs.append({
            'seq': r.get('seq'), 'round': r.get('round'), 'arm': r.get('arm', ''), 'rep': r.get('rep'), 'name': name,
            'run_dir': rd, 'scored': scored, 'valid': valid, 'excluded': excluded, 'flags_excluding': fx,
            'keep': keep, 'why': why, 'benign': benign, 'frames_source': src, 'stats': st, 'check': check,
            'hist': hist, 'draws_10s': bins, 'stat_bins': sbins, 'scene_d': None, 'scene_loo': False, 'scene_flag': False,
            'phase': phase_text(r), 'slow': slow, 'slow_txt': mr.slow_txt(slow), 'slow_win': slow_win,
            'timerq': (tq or {}).get(name) if name else None,
            'results_fps_mean': num(r.get('fps_mean')), 'status': r.get('status', ''),
            'median_ms_csv': num(r.get('median_ms')),
            'game_cores': gcores, 'game_src': gsrc, 'bg': bg, 'bg_note': bg_note, 'bg_flags': [], 'bg_flag': False,
        })

    # scene check: every run with perf.csv draws against the pooled kept reference windows
    ref_runs = [x for x in runs if x['arm'] == ref and x['keep'] and x['hist']]
    pool_from = 'kept'
    if not ref_runs:
        ref_runs = [x for x in runs if x['arm'] == ref and x['scored'] and x['hist']]
        pool_from = 'scored (no kept reference run with draws)'
    loo = []
    if len(ref_runs) >= 2:
        for x in ref_runs:
            x['scene_d'] = w1_log(x['hist'], pool([y['hist'] for y in ref_runs if y is not x]))
            x['scene_loo'] = True
            loo.append(x['scene_d'])
    thr = max(scene_floor, scene_factor * max(loo)) if loo else scene_floor
    pooled = pool([x['hist'] for x in ref_runs]) if ref_runs else None
    for x in runs:
        if x['hist'] is None or pooled is None:
            continue
        if not x['scene_loo']:
            if len(ref_runs) == 1 and x is ref_runs[0]:
                continue  # the only reference run: nothing to compare it with
            x['scene_d'] = w1_log(x['hist'], pooled)
        x['scene_flag'] = x['scene_d'] > thr

    # background load: the reference value and the per-run flags
    bgref = None
    if bg_ref_dir and os.path.isdir(bg_ref_dir) and os.path.abspath(bg_ref_dir) != d:
        bgref = bg_reference(bg_ref_dir, sat_busy)
    own = [x['bg']['bg_cores'] for x in runs if x['scored'] and x['bg'] and not x['bg']['sat']]
    if bg_ref_cores is not None:
        bg_ref, bg_src = bg_ref_cores, '--bg-ref-cores'
    elif bgref and bgref['bg_med'] is not None:
        bg_ref, bg_src = bgref['bg_med'], 'median of the %d unsaturated scored runs of %s' % (
            len(bgref['bg_values']), bgref['name'])
    elif own:
        bg_ref, bg_src = statistics.median(own), "median of this matrix's %d unsaturated scored runs%s" % (
            len(own), ' (%s has none)' % bgref['name'] if bgref else '')
    else:
        bg_ref, bg_src = None, 'none (no unsaturated scored run with sys.csv%s)' % (
            ' here or in %s' % bgref['name'] if bgref else '')
    kept_bg = [x for x in runs if x['keep'] and x['bg']]
    all_sat = bool(kept_bg) and all(x['bg']['sat'] for x in kept_bg)
    for x in runs:
        b = x['bg']
        if not b:
            continue
        if b['sat']:
            x['bg_flags'].append('SAT')
        elif bg_ref is not None and b['bg_cores'] > bg_ref + bg_margin:
            x['bg_flags'].append('BG+')
        x['bg_flag'] = 'BG+' in x['bg_flags'] or ('SAT' in x['bg_flags'] and not all_sat)

    kept = [x for x in runs if x['keep']]
    arms = arm_block(kept, order)
    deltas = delta_block(arms, kept, ref)
    clean = [x for x in kept if not x['slow_win'] and not x['scene_flag'] and not x['bg_flag']]
    arms_clean = arm_block(clean, order) if len(clean) != len(kept) else None
    deltas_clean = delta_block(arms_clean, clean, ref) if arms_clean is not None else None
    # task #9: per-arm median per bin across the kept runs (n = kept runs with frames in that bin)
    bin_arms = {}
    for arm in order:
        rs = [x['stat_bins'] for x in kept if x['arm'] == arm and x['stat_bins']]
        if not rs:
            continue
        cells = []
        for i in range(max(len(b) for b in rs)):
            got = [b[i] for b in rs if i < len(b) and b[i].get('frames')]
            c = {'bin': i, 'n': len(got)}
            for key, _, _ in BIN_METRICS:
                c[key] = statistics.median([g[key] for g in got]) if got else None
            cells.append(c)
        bin_arms[arm] = {'n': len(rs), 'bins': cells}

    # run-matrix summary.md's fps per arm: median of results.csv fps_mean over scored OK runs that are not excluded
    rm_fps = {}
    for arm in order:
        v = [x['results_fps_mean'] for x in runs if x['arm'] == arm and x['scored'] and x['status'] == 'OK'
             and x['median_ms_csv'] is not None and not x['excluded'] and x['results_fps_mean'] is not None]
        if v:
            rm_fps[arm] = statistics.median(v)
    return {
        'dir': d, 'title': mj.get('title', ''), 'command': command, 'ref': ref, 'order': order,
        'n_rows': len(runs), 'n_scored': sum(1 for x in runs if x['scored']), 'n_kept': len(kept),
        'keep_rule': 'kept = scored, frame stats, no real problems, %s, %s' % (
            'valid timing or not (--all)' if use_all else 'valid timing',
            'excluded kept (--keep-flagged)' if keep_flagged else 'not excluded'),
        'functional': sum(1 for x in kept if not x['valid']),
        'runs': runs, 'arms': arms, 'deltas': deltas, 'arms_clean': arms_clean, 'deltas_clean': deltas_clean,
        'scene': {'pool_from': pool_from, 'ref_runs': [x['name'] for x in ref_runs], 'loo': loo, 'threshold': thr,
                  'floor': scene_floor, 'factor': scene_factor,
                  'ref_p50': wquantile(pooled, 0.5) if pooled else None, 'ref_mean': wmean(pooled) if pooled else None},
        'timerq_note': tq_note, 'timerq_rows': len(tq) if tq is not None else None,
        'slow_rule': {'emhz': emhz, 'rows': srows}, 'run_matrix_fps': rm_fps,
        'bins': {'bin_s': bin_s, 'arms': bin_arms},
        'bg': {'ref': bg_ref, 'ref_src': bg_src, 'margin': bg_margin, 'sat_busy': sat_busy, 'ref_dir': bgref,
               'all_sat': all_sat, 'kept_with_bg': len(kept_bg),
               'sat_kept': sum(1 for x in kept_bg if x['bg']['sat'])},
    }


def arm_table(w, title, arms, ref):
    w('## ' + title)
    w('')
    if not arms:
        w('(no kept runs)')
        w('')
        return
    w('| arm | ref | n | fps | fps spread % | p50 ms | p99 ms | 1% low fps | >33 ms/min | slow state in window | scene flags '
      '| background cores (BG+ / SAT runs) |')
    w('|---|---|---|---|---|---|---|---|---|---|---|---|')
    for arm, a in arms.items():
        w('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %d of %d | %d | %s |' % (
            arm, '*' if arm == ref else '', '%d%s' % (a['n'], ' n<3!' if a['n_lt3'] else ''), rng(a['fps'], 1),
            f(a['fps']['spread_pct'], 1), rng(a['p50_ms'], 3), rng(a['p99_ms'], 2), rng(a['low1_fps'], 1),
            rng(a['over33_min'], 1), a['slow'], a['n'], a['scene_flags'],
            '%s%s (%d / %d)' % ('>=' if a['bg'] and a['sat'] and a['sat'] >= a['bg']['n'] else '',
                                rng(a['bg'], 1) if a['bg'] else '-', a['bg_plus'], a['sat'])))
    w('')


def delta_table(w, deltas, arms, ref):
    if arms and ref not in arms:
        w('No kept %s run in this table, so no deltas.' % ref)
        w('')
        return
    if not deltas:
        return
    w('Deltas against %s: arm median vs %s median; better / worse only when every run of the arm lies outside the '
      '%s range, else overlap.' % (ref, ref, ref))
    w('')
    w('| arm | n vs n | d fps | d p50 | d p99 | d 1% low | d >33 ms/min | paired d fps by round: median (rounds up / rounds) |')
    w('|---|---|---|---|---|---|---|---|')
    for arm, dd in deltas.items():
        cells = []
        for key, _, _, _ in METRICS:
            x = dd[key]
            if key == 'over33_min':
                cells.append('%s/min %s' % (fsgn(x['delta'], 1), x['verdict']))
            else:
                cells.append('%s%% %s' % (fsgn(x['pct'], 1), x['verdict']))
        p = dd['paired_fps_pct']
        w('| %s | %d vs %d | %s | %s | %s | %s | %s | %s |' % tuple(
            [arm, arms[arm]['n'], arms[ref]['n']] + cells
            + [('%s%% (%d / %d)' % (fsgn(p['med'], 1), p['up'], p['n'])) if p['n'] else '-']))
    w('')


def bins_section(w, R):
    """Task #9: per-run tables of fps, p99, 1% low and >33 ms/min per bin of the scored window, plus the per-arm
    median of the kept runs per bin."""
    bs = R['bins']['bin_s']
    runs = [x for x in R['runs'] if x.get('stat_bins')]
    w('## %g s bins of each run\'s scored window' % bs)
    w('')
    if not runs:
        w('(no run with a scored window)')
        w('')
        return
    ncol = max(len(x['stat_bins']) for x in runs)
    w('- bins: consecutive %g s of summed frame time from the start of the scored window (the frames of the Runs '
      'table); a frame belongs to the bin in which it ends; a last part shorter than %g s is merged into the bin '
      'before it (a 50.01 s window gives 5 bins, the last one 40-50.01 s); bin start and end times are in the '
      '--json output (runs[].stat_bins)' % (bs, bs / 2.0))
    w('- per bin, as for the whole window: p99 nearest-rank; 1% low = 1000 / mean of the slowest max(1, n // 100) '
      'frame times of the bin, in fps; >33 ms/min = frames over 33 ms per minute of the bin\'s summed frame time '
      '(the count in brackets); `-` = no such bin (a shorter window)')
    w('- arm rows: the median per bin across the kept runs of the arm (n = kept runs with that bin); the whole '
      'window column of an arm row is the arm table cell, median (min..max)')
    w('')
    heads = ['%g-%g s' % (i * bs, (i + 1) * bs) for i in range(ncol)]
    for key, nd, label in BIN_METRICS:
        w('### %s per %g s' % (label, bs))
        w('')
        w('| seq | run | kept | %s | whole window |' % ' | '.join(heads))
        w('|---|---|---|%s---|' % ('---|' * ncol))
        for x in runs:
            cells = []
            for i in range(ncol):
                b = x['stat_bins'][i] if i < len(x['stat_bins']) else None
                if b is None or not b.get('frames'):
                    cells.append('-' if b is None else '0 frames')
                elif key == 'over33_min':
                    cells.append('%s (%d)' % (f(b[key], nd), b['over33']))
                else:
                    cells.append(f(b[key], nd))
            st = x['stats'] or {}
            whole = f(st.get(key), nd)
            if key == 'over33_min' and st:
                whole = '%s (%d)' % (whole, st['over33'])
            w('| %s | %s | %s | %s | %s |' % (x['seq'], x['name'], 'yes' if x['keep'] else 'no', ' | '.join(cells),
                                             whole))
        for arm, A in R['bins']['arms'].items():
            cells = []
            for i in range(ncol):
                c = A['bins'][i] if i < len(A['bins']) else None
                cells.append('-' if c is None or c[key] is None else '%s (n=%d)' % (f(c[key], nd), c['n']))
            am = R['arms'].get(arm)
            w('| | **%s** median, %d kept | | %s | %s |' % (arm, A['n'], ' | '.join(cells),
                                                       rng(am[key], nd) if am else '-'))
        w('')


def report(R):
    out = []
    w = out.append
    ref = R['ref']
    runs = R['runs']
    w('# W4b read-out add-on (Agent 7, task #29): %s' % R['dir'])
    w('')
    if R.get('title'):
        w(R['title'])
        w('')
    w('- command: `%s`' % R['command'])
    w('- reference arm: %s; %d result rows, %d scored, %d kept (%s)' % (
        ref, R['n_rows'], R['n_scored'], R['n_kept'], R['keep_rule']))
    w('- window: each run\'s scored window as the runner cut it (frames.json window.first_row / rows of the frame csv '
      'it names); frames with a frame time <= 0 left out')
    w('- fps = frames / summed frame time; p50, p99 nearest-rank; 1% low = 1000 / mean of the slowest max(1, n // 100) '
      'frame times, in fps; >33 ms/min = frames over 33 ms per minute of summed frame time; arm cells = median '
      '(min..max) across the kept runs; n<3! = fewer than 3 kept runs')
    if R['functional']:
        w('')
        w('> **FUNCTIONAL ONLY**: %d of %d kept runs are not valid timing (kept by --all). Do not use these numbers as '
          'timing results.' % (R['functional'], R['n_kept']))
    B = R['bg']
    if B['sat_kept']:
        sat_bg = [x['bg']['bg_cores'] for x in runs if x['keep'] and x['bg'] and x['bg']['sat']]
        w('')
        w('> **CPU SATURATED**: %d of %d kept runs with sys.csv had a median busy share >= %.2f in the window (SAT): the '
          'game shared the CPU with >= %.1f cores of other work (median). More load (Defender) cannot raise that '
          'reading; it takes CPU from the game. Treat the timing of SAT runs as contended%s.' % (
              B['sat_kept'], B['kept_with_bg'], B['sat_busy'], statistics.median(sat_bg),
              '; every kept run is SAT, so SAT drops no run from the clean table' if B['all_sat'] else
              '; SAT runs are left out of the clean table'))
    w('')
    arm_table(w, 'Arms (kept runs)', R['arms'], ref)
    delta_table(w, R['deltas'], R['arms'], ref)
    if R['arms_clean'] is not None:
        arm_table(w, 'Arms without runs that have the slow state in the window, a scene flag or a background flag',
                  R['arms_clean'], ref)
        delta_table(w, R['deltas_clean'], R['arms_clean'], ref)

    w('## Runs')
    w('')
    w('| seq | round | arm | rep | kept | fps | p50 ms | p99 ms | 1% low fps | >33 ms/min | window s | check | '
      'draws/frame p50 (mean) | scene | phase | slow (recheck) | slow (timerq) | game cores | '
      'background cores (p90; busy %) | notes |')
    w('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    for x in runs:
        st = x['stats'] or {}
        if x['scene_d'] is not None:
            scene = '%.3f%s%s' % (x['scene_d'], ' loo' if x['scene_loo'] else '', ' SCENE?' if x['scene_flag'] else '')
        elif x['hist'] is not None:
            scene = 'ref (only run)' if x['arm'] == ref else '-'
        else:
            scene = 'n/a (%s frames)' % x['frames_source'] if x['frames_source'] and x['frames_source'] != 'perf' else '-'
        draws = '%d (%.0f)' % (wquantile(x['hist'], 0.5), wmean(x['hist'])) if x['hist'] else '-'
        tq = x['timerq']
        tqt = ('%s / %s%%' % ('no' if tq['onset_s'] == '-' else tq['onset_s'] + ' s', tq['slow_pct'])) if tq else '-'
        check = '-' if x['check'] is None else ('ok' if not x['check'] else 'MISMATCH')
        notes = '; '.join(x['why'] + x['benign'] + (['check: ' + ', '.join(x['check'])] if x['check'] else [])
                          + (['background: ' + x['bg_note']] if not x['bg'] and x['bg_note'] != 'no sys.csv' else []))
        gc = '-' if x['game_cores'] is None else '%.2f%s' % (x['game_cores'], '' if x['game_src'] == 'proc.csv' else '~')
        b = x['bg']
        bgt = ('%s%.1f (p90 %.1f; busy %.0f%%)%s' % ('>=' if b['sat'] else '', b['bg_cores'], b['bg_p90'],
                                                    100.0 * b['busy_med'], ''.join(' ' + t for t in x['bg_flags']))
               if b else '-')
        w('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
            x['seq'], x['round'], x['arm'], x['rep'], 'yes' if x['keep'] else 'no', f(st.get('fps'), 1),
            f(st.get('p50_ms'), 3), f(st.get('p99_ms'), 2), f(st.get('low1_fps'), 1), f(st.get('over33_min'), 1),
            f(st.get('window_s'), 1), check, draws, scene, x['phase'], x['slow_txt'], tqt, gc, bgt,
            notes.replace('|', '/') or '-'))
    w('')
    bins_section(w, R)

    S = R['scene']
    w('## Scene check (draws per frame against the pooled %s windows)' % ref)
    w('')
    w('- distance: 1-D Wasserstein distance between the time-weighted distributions of ln(1 + perf.csv draw_calls) over '
      'the scored windows (0.10 ~ draws about 10 % apart on average; +-1 draw jitter ~0.005; same-scene runs on '
      '2026-11-22 0.000-0.005, window 3\'s light-phase run 0025-d11-r1 0.036); `loo` = a reference run against the '
      'pool of the other reference runs')
    w('- reference pool: %s %s runs (%s); time-weighted draws/frame p50 %s, mean %s' % (
        len(S['ref_runs']), S['pool_from'], ', '.join(S['ref_runs']) or '-',
        '-' if S['ref_p50'] is None else '%d' % S['ref_p50'], f(S['ref_mean'], 0)))
    w('- threshold: max(floor %.3f, %.1f x largest leave-one-out distance %s) = %.3f%s' % (
        S['floor'], S['factor'], f(max(S['loo']) if S['loo'] else None, 3), S['threshold'],
        '' if S['loo'] else ' (fewer than 2 reference runs: floor only)'))
    flagged = [x for x in runs if x['scene_flag']]
    w('- flagged SCENE?: %s' % (', '.join('%s (%.3f%s)' % (x['name'], x['scene_d'], '' if x['keep'] else ', not kept')
                                          for x in flagged) or 'none'))
    nat = [x['name'] for x in runs if x['hist'] is None and x['frames_source'] and x['frames_source'] != 'perf']
    if nat:
        w('- not compared (frames not from perf.csv, so no guest draw counts in the window): %s' % ', '.join(nat))
    w('- per-run time-weighted mean draws/frame per 10 s of the window are in the --json output (draws_10s)')
    w('')

    w('## Slow state')
    w('')
    w('- slow (recheck): matrix_recheck.slow_state, imported read-only from bench/agent8/run/matrix_recheck.py: E-cores '
      'under %g MHz for %d+ sys.csv samples in a row; onset s after the first-frame signal / share of window samples; '
      '`!` = such a stretch overlaps the window (Agent 11: not a result); `no` = never; `-` = no sys.csv' % (
          R['slow_rule']['emhz'], R['slow_rule']['rows']))
    sw = [x for x in runs if x['scored'] and x['slow_win']]
    w('- scored runs with the slow state in the window: %s' % (', '.join(x['name'] for x in sw) or 'none'))
    w('- slow (timerq): bench/agent11/timerq_slowstate.ps1, %s; onset s after the first frame / share of the samples '
      'from the first frame to the last sample; %s of %d runs matched' % (
          R['timerq_note'], '-' if R['timerq_rows'] is None else str(R['timerq_rows']), len(runs)))
    w('')

    w('## Background load (system CPU minus the game\'s CPU over the scored window)')
    w('')
    w('- system = logical CPUs x min(1, cpu_util_pct / cpu_perf_pct) per sys.csv sample whose interval centre lies in '
      'the window (_Total % Processor Utility / % Processor Performance = the busy share without the frequency '
      'scaling); game = the slope of proc.csv cpu_s over the same interval; background = system - game')
    w('- game cores = cpu_s over the whole scored window (`~` = run.json window_cpu_cores_mean, where proc.csv does '
      'not cover the window); background cell = median (p90; median busy %) over the window samples')
    w('- SAT = median busy share >= %.2f: no spare CPU, so the background reading is a floor (`>=`): more load cannot '
      'raise it, it takes CPU from the game instead' % B['sat_busy'])
    w('- BG+ = not SAT and background > reference + %.1f cores; reference: %s%s' % (
        B['margin'], B['ref_src'], '' if B['ref'] is None else ' = %.2f cores' % B['ref']))
    RD = B['ref_dir']
    if RD:
        ga = ', '.join('%s %.2f (n=%d)' % (k, v['med'], v['n']) for k, v in RD['game_by_arm'].items()) or '-'
        w('- reference dir %s: %d scored runs, %d with sys.csv (%d of them SAT)%s; game cores there (median per arm, '
          'proc.csv over the scored window): %s' % (
              RD['name'], RD['scored'], RD['with_sys'], RD['sat'],
              ', so it gives no background value' if not RD['with_sys'] else '', ga))
    w('- SAT runs: %s' % (', '.join(x['name'] for x in runs if 'SAT' in x['bg_flags']) or 'none'))
    w('- BG+ runs: %s' % (', '.join('%s (%.1f cores)' % (x['name'], x['bg']['bg_cores'])
                                    for x in runs if 'BG+' in x['bg_flags']) or 'none'))
    nob = {}
    for x in runs:
        if not x['bg']:
            nob.setdefault(x['bg_note'], []).append(x['name'])
    if nob:
        w('- no background value: %s' % '; '.join('%s: %d run(s)' % (k, len(v)) for k, v in nob.items()))
    w('')

    w('## Checks')
    w('')
    withc = [x for x in runs if x['check'] is not None]
    bad = [x for x in withc if x['check']]
    w('- per run: %d of %d runs with a window agree with frames.json (frames, mean fps, p50, p99, >33) and with '
      'results.csv fps_mean%s' % (len(withc) - len(bad), len(withc), (
          '; MISMATCH: ' + '; '.join('%s: %s' % (x['name'], ', '.join(x['check'])) for x in bad)) if bad else ''))
    cells = []
    for arm, a in R['arms'].items():
        t = R['run_matrix_fps'].get(arm)
        mine = a['fps']['med']
        same = t is not None and abs(round(mine, 3) - t) < 0.0015
        cells.append('%s %.3f vs %s%s' % (arm, mine, f(t, 3), '' if same else ' (DIFFERENT: kept sets differ)'))
    w('- arm fps (median of the kept runs) vs run-matrix summary.md (median of results.csv fps_mean over scored OK '
      'runs that are not excluded): %s' % ('; '.join(cells) or '-'))
    w('')
    return '\n'.join(out) + '\n'


def to_json(R):
    J = dict(R)
    J['runs'] = []
    for x in R['runs']:
        y = {k: v for k, v in x.items() if k != 'hist'}
        if x['hist']:
            y['draws_p50'] = wquantile(x['hist'], 0.5)
            y['draws_mean'] = wmean(x['hist'])
        J['runs'].append(y)
    return J


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('dir', help='run-matrix.ps1 output dir (results.csv, matrix.json, runs\\)')
    ap.add_argument('-o', '--out', help='also write the markdown report here')
    ap.add_argument('--json', help='write every number (runs, arms, deltas, scene, slow) as json here')
    ap.add_argument('--ref', help='reference arm (default: matrix.json ref arm, else "reference")')
    ap.add_argument('--all', action='store_true', help='keep runs that are not valid timing (functional matrices)')
    ap.add_argument('--keep-flagged', action='store_true', help='keep runs with an excluding flag')
    ap.add_argument('--no-timerq', action='store_true', help='do not run bench/agent11/timerq_slowstate.ps1')
    ap.add_argument('--scene-floor', type=float, default=SCENE_FLOOR)
    ap.add_argument('--scene-factor', type=float, default=2.0)
    ap.add_argument('--slow-emhz', type=float, default=800.0)
    ap.add_argument('--slow-rows', type=int, default=3)
    ap.add_argument('--min-cover', type=float, default=0.9)
    ap.add_argument('--bg-ref', default=W3_DIR, help='matrix dir whose unsaturated scored runs give the background '
                    'reference (default: window 3); none = use this matrix\'s own runs')
    ap.add_argument('--bg-ref-cores', type=float, help='fixed background reference in cores (overrides --bg-ref)')
    ap.add_argument('--bg-margin', type=float, default=1.0, help='BG+ above reference + this many cores')
    ap.add_argument('--sat-busy', type=float, default=SAT_BUSY, help='SAT from this median busy share on')
    ap.add_argument('--bin-s', type=float, default=BIN_S, help='bin length (s of summed frame time) of the per-run '
                    'bins (default 10)')
    a = ap.parse_args(argv)
    command = 'python bench\\agent7\\w4b_readout\\w4b_readout.py ' + ' '.join(argv)
    bg_ref_dir = None if (a.bg_ref or '').strip().lower() in ('', 'none') else a.bg_ref
    R = analyse(a.dir, command, a.ref, a.all, a.keep_flagged, not a.no_timerq, a.scene_floor, a.scene_factor,
                a.slow_emhz, a.slow_rows, a.min_cover, bg_ref_dir, a.bg_ref_cores, a.bg_margin, a.sat_busy, a.bin_s)
    text = report(R)
    sys.stdout.write(text)
    if a.out:
        with open(a.out, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)
    if a.json:
        with open(a.json, 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(to_json(R), fh, indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())

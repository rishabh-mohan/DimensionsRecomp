#!/usr/bin/env python3
"""scan_matrix.py - read-only scan of one run-matrix dir (helper of Agent 8, 2026-11-23).

Usage:
  python -B scan_matrix.py <matrix dir> <out dir (a ...\\readout\\<w>\\scan dir)>
         [--timerq FILE] [--rules FILE] [--cmp-json FILE] [--phase FILE] [--claim w5]

Reads (never writes) results.csv, matrix.json and per run dir: run.json, frames.json, game*.log, perf.csv, sys.csv.
Writes only into <out dir>: scan.md, proof.csv, health.csv, slow.csv, bins.csv, warn_types.csv.

Definitions
- proof: lines of game*.log containing 'Host timer resolution set to 1 ms' / 'TimerQueue: precise wait
  (timer_queue_precise_wait)'; run.json env_set / params.env / params.cvar / args / bin_dir against matrix.json's arm.
- health: level counts of '[ts] [level] [cat] [tN] msg' lines; INSTALL .DAT FAILED = lines matching
  FAILED: path='d:\\INSTALL*.DAT (the runner's rule, 34 in a normal boot); warning types = '<cat>: <msg>' with hex
  (0x.., 6+ hex digits with a digit) and decimal numbers replaced by '#', the run dir path by <RUN>.
- slow state (Agent 11 / matrix_recheck rule): sys.csv rows with epoch_s >= ff_signal_epoch_s and an e_eff_mhz value;
  low = e_eff_mhz < 800; slow = 3+ low rows in a row; onset = first row of the first such stretch - ff;
  run low share = low rows / rows (timerq slow_pct); window rows = run.json sys.window_start_epoch <= epoch_s <=
  window_end_epoch (matrix_recheck's window share); window means over those rows.
- 10 s bins (as Agent 7's w4b_readout.stat_bins): frames.json window.first_row/rows of perf.csv (frame_time_us > 0),
  consecutive 10 s of summed frame time from the window start, a frame belongs to the bin in which it ends, a last
  part < 5 s merged into the bin before; fps = frames / summed frame time of the bin; draws p50 = nearest-rank median
  of draw_calls of the bin's frames. Bin sys means: sys.csv rows whose interval centre ((previous epoch + epoch) / 2)
  lies in [measure_start.epoch_s + t0, + t1). Slow bin = bin fps < 0.85 x the median of the run's own bins.
- Spearman: average ranks for ties; two-sided permutation p from 10000 shuffles (seed 12345).
Stdlib only, one thread.
"""
import argparse
import csv
import glob
import json
import math
import os
import random
import re
import statistics
import sys

sys.dont_write_bytecode = True

E_SLOW = 800.0
MIN_ROWS = 3
BIN_S = 10.0
SLOW_BIN = 0.85
P_BUSY = 90.0
PERMS = 10000

L1MS = 'Host timer resolution set to 1 ms'
LPREC = 'TimerQueue: precise wait (timer_queue_precise_wait)'
LOG_RE = re.compile(r'^\[(?P<ts>\d{4}-\d\d-\d\d [0-9:.]+)\] \[(?P<lvl>[^\]]+)\] \[(?P<cat>[^\]]+)\] '
                    r'(?:\[t\d+\] )?(?P<msg>.*)$')
DAT_RE = re.compile(r"FAILED: path='?d:\\INSTALL[^'\s]*\.DAT", re.I)
STUCK_RE = re.compile(r'STUCK[-_ ]?LOCK', re.I)
UNK_RE = re.compile(r'unknown cvar', re.I)
UNK2_RE = re.compile(r'(unknown|unrecogni[sz]ed|invalid)\W+(cvar|flag|option|argument|command)', re.I)
TIMER_RE = re.compile(r'TimerQueue|timer resolution|REX_TIMER|timer_queue', re.I)
STD_ARGS = ('--log_file=', '--perf_log_csv=', '--native_settings_load=false', '--discord_rpc=false',
            '--audio_mute=true', '--pause_when_unfocused=false')
R3_DROP_RE = re.compile(r'(\d{4}-[A-Za-z0-9]+-r\d+) \(R3 slow state in the window \((\d+) s / (\d+)% !\)\)')
R3_AT_RE = re.compile(r'(\d{4}-[A-Za-z0-9]+-r\d+) at (\d+) s')


def num(s):
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def load_json(p):
    try:
        with open(p, encoding='utf-8-sig') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def read_rows(p):
    try:
        with open(p, encoding='utf-8-sig', errors='replace', newline='') as fh:
            return list(csv.DictReader(fh))
    except OSError:
        return None


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / float(len(xs)) if xs else None


def nearest_rank(s, num_, den):
    n = len(s)
    k = -(-num_ * n // den)
    return s[max(1, min(n, k)) - 1]


def f(v, nd=1, dash='-'):
    return dash if v is None else '%.*f' % (nd, v)


def pc(v, nd=0, dash='-'):
    return dash if v is None else '%.*f' % (nd, 100.0 * v)


def norm_msg(msg, rd):
    s = msg
    if rd:
        s = re.sub(re.escape(rd), '<RUN>', s, flags=re.I)
    s = re.sub(r'0x[0-9A-Fa-f]+', '0x#', s)
    s = re.sub(r'\b(?=[0-9A-Fa-f]*\d)[0-9A-Fa-f]{6,}\b', '#', s)
    s = re.sub(r'\d+(?:\.\d+)?', '#', s)
    return re.sub(r'\s+', ' ', s).strip()


# ---------------------------------------------------------------- logs

def scan_logs(rd):
    R = {'files': [], 'lines': 0, 'n1ms': 0, 'nprec': 0, 'lvl': {}, 'fatal': 0, 'dat': 0, 'inst_other': 0,
         'warn_non': 0, 'stuck': 0, 'unk': 0, 'unk2': 0, 'closing': False, 'term': False, 'exec_done': False,
         'wtypes': {}, 'etypes': {}, 'ctypes': {}, 'timer_lines': {}, 'timer_raw': {}, 'other_timer': {},
         'odd_lines': []}
    for p in sorted(glob.glob(os.path.join(glob.escape(rd), 'game*.log'))):
        with open(p, encoding='utf-8', errors='replace') as fh:
            lines = fh.read().splitlines()
        R['files'].append('%s (%d lines)' % (os.path.basename(p), len(lines)))
        R['lines'] += len(lines)
        for ln in lines:
            if L1MS in ln:
                R['n1ms'] += 1
            if LPREC in ln:
                R['nprec'] += 1
            if DAT_RE.search(ln):
                R['dat'] += 1
            if STUCK_RE.search(ln):
                R['stuck'] += 1
                R['odd_lines'].append(ln.strip()[:220])
            if UNK_RE.search(ln):
                R['unk'] += 1
                R['odd_lines'].append(ln.strip()[:220])
            elif UNK2_RE.search(ln):
                R['unk2'] += 1
                R['odd_lines'].append(ln.strip()[:220])
            if 'FATAL' in ln:
                R['fatal'] += 1
                R['odd_lines'].append(ln.strip()[:220])
            if 'Window closing, shutting down' in ln:
                R['closing'] = True
            if 'Title terminated' in ln:
                R['term'] = True
            if 'Execution complete' in ln:
                R['exec_done'] = True
            m = LOG_RE.match(ln)
            if not m:
                continue
            lvl = m.group('lvl').lower()
            R['lvl'][lvl] = R['lvl'].get(lvl, 0) + 1
            msg = m.group('msg')
            key = '%s: %s' % (m.group('cat'), norm_msg(msg, rd))
            if TIMER_RE.search(msg):
                tk = '[%s] %s' % (lvl, key)
                R['timer_lines'][tk] = R['timer_lines'].get(tk, 0) + 1
                R['timer_raw'].setdefault(tk, msg.strip()[:200])
                if L1MS not in msg and LPREC not in msg:
                    R['other_timer'][tk] = R['other_timer'].get(tk, 0) + 1
            if lvl == 'warning':
                if 'INSTALL' in msg:
                    if not DAT_RE.search(msg):
                        R['inst_other'] += 1
                else:
                    R['warn_non'] += 1
                R['wtypes'][key] = R['wtypes'].get(key, 0) + 1
            elif lvl == 'error':
                R['etypes'][key] = R['etypes'].get(key, 0) + 1
                R['odd_lines'].append(ln.strip()[:220])
            elif lvl in ('critical', 'fatal'):
                R['ctypes'][key] = R['ctypes'].get(key, 0) + 1
                R['odd_lines'].append(ln.strip()[:220])
    return R


def normpath(p):
    return (p or '').replace('/', '\\').rstrip('\\').lower()


def proof_check(x, cfg):
    rj, lg = x['rj'], x['log']
    params = rj.get('params') or {}
    cvars = [str(c) for c in (params.get('cvar') or [])]
    env_set = rj.get('env_set') or {}
    penv = [str(e) for e in (params.get('env') or [])]
    args = [str(a) for a in (rj.get('args') or [])]
    ecv = [str(c) for c in (cfg.get('cvars') or [])]
    eenv = cfg.get('env') or {}
    x['cvars'] = cvars
    x['env_set'] = env_set
    x['exp_1ms'] = 1 if 'host_timer_resolution_ms=1' in ecv else 0
    x['exp_prec'] = 1 if 'timer_queue_precise_wait=true' in ecv else 0
    x['exp_env'] = 'REX_TIMER_WAIT_BLOCKING' in eenv
    x['has_env'] = 'REX_TIMER_WAIT_BLOCKING' in env_set
    x['bin'] = rj.get('bin_dir') or ''
    x['bin_ok'] = normpath(x['bin']).endswith(normpath(cfg.get('bin', '')))
    dev = []
    if lg['n1ms'] != x['exp_1ms']:
        dev.append('1 ms lines %d (expected %d)' % (lg['n1ms'], x['exp_1ms']))
    if lg['nprec'] != x['exp_prec']:
        dev.append('precise lines %d (expected %d)' % (lg['nprec'], x['exp_prec']))
    if x['has_env'] != x['exp_env']:
        dev.append('env_set REX_TIMER_WAIT_BLOCKING %s (expected %s)' % (
            'present' if x['has_env'] else 'absent', 'present' if x['exp_env'] else 'absent'))
    if x['has_env'] and str(env_set.get('REX_TIMER_WAIT_BLOCKING')) != '1':
        dev.append('REX_TIMER_WAIT_BLOCKING=%r (expected 1)' % env_set.get('REX_TIMER_WAIT_BLOCKING'))
    extra_env = sorted(set(env_set) - set(eenv))
    if extra_env:
        dev.append('extra env_set keys: %s' % ', '.join(extra_env))
    if sorted(penv) != sorted('%s=%s' % (k, v) for k, v in eenv.items()):
        dev.append('params.env %s (expected %s)' % (penv, ['%s=%s' % kv for kv in eenv.items()]))
    if cvars != ecv:
        dev.append('params.cvar %s (matrix.json %s)' % (cvars, ecv))
    miss = [c for c in ecv if '--' + c not in args]
    if miss:
        dev.append('cvars missing from args: %s' % ', '.join(miss))
    extra = [a for a in args if not a.startswith(STD_ARGS) and a[2:] not in ecv]
    if extra:
        dev.append('extra args: %s' % ', '.join(extra))
    if not x['bin_ok']:
        dev.append('bin_dir %s (matrix.json %s)' % (x['bin'], cfg.get('bin')))
    tag = rj.get('tag') or ''
    if tag and not x['name'].endswith(tag):
        dev.append('run.json tag %s vs dir %s' % (tag, x['name']))
    other_timer = dict(lg['other_timer'])
    x['other_timer'] = other_timer
    if other_timer:
        dev.append('other timer lines: %s' % '; '.join('%s x%d' % kv for kv in other_timer.items()))
    return dev


def health_check(x):
    lg = x['log']
    dev = []
    if len(lg['files']) != 1:
        dev.append('log files: %s' % (', '.join(lg['files']) or 'none'))
    if lg['dat'] != 34:
        dev.append('INSTALL .DAT FAILED %d (34 expected)' % lg['dat'])
    for k in ('error', 'critical', 'fatal'):
        if lg['lvl'].get(k):
            dev.append('[%s] x%d' % (k, lg['lvl'][k]))
    if lg['fatal']:
        dev.append('FATAL x%d' % lg['fatal'])
    if lg['stuck']:
        dev.append('STUCK-LOCK x%d' % lg['stuck'])
    if lg['unk']:
        dev.append('unknown cvar x%d' % lg['unk'])
    if lg['unk2']:
        dev.append('unknown/unrecognized flag-like lines x%d' % lg['unk2'])
    if not (lg['closing'] and lg['exec_done'] and lg['term']):
        dev.append('shutdown lines: closing %s, execution complete %s, terminated %s' % (
            lg['closing'], lg['exec_done'], lg['term']))
    other = sorted(set(lg['lvl']) - {'info', 'warning', 'error', 'critical', 'fatal', 'debug', 'trace'})
    if other:
        dev.append('other levels: %s' % ', '.join(other))
    return dev


# ---------------------------------------------------------------- sys.csv / slow state

def slow_scan(srows, ff, ws, we, me):
    pts = []
    for r in srows:
        t, e = num(r.get('epoch_s')), num(r.get('e_eff_mhz'))
        if t is None or e is None or t < ff:
            continue
        pts.append((t, e, r))
    S = {'n': len(pts)}
    if not pts:
        return S
    low = [e < E_SLOW for _, e, _ in pts]
    st, i, n = [], 0, len(pts)
    while i < n:
        if not low[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and low[j + 1]:
            j += 1
        if j - i + 1 >= MIN_ROWS:
            st.append((i, j))
        i = j + 1
    S['onset'] = (pts[st[0][0]][0] - ff) if st else None
    S['stretches'] = len(st)
    S['low_share'] = sum(low) / float(n)
    S['stretch_share'] = sum(j - i + 1 for i, j in st) / float(n)
    S['span'] = pts[-1][0] - ff
    S['in_win'] = any(pts[i][0] <= we and pts[j][0] >= ws for i, j in st)
    win = [(t, e, r) for t, e, r in pts if ws <= t <= we]
    S['win_n'] = len(win)
    S['win_low'] = (sum(1 for _, e, _ in win if e < E_SLOW) / float(len(win))) if win else None
    S['e_mean'] = mean([e for _, e, _ in win])
    S['p_mean'] = mean([num(r.get('p_eff_mhz')) for _, _, r in win])
    S['pu_mean'] = mean([num(r.get('p_util_pct')) for _, _, r in win])
    S['eu_mean'] = mean([num(r.get('e_util_pct')) for _, _, r in win])
    fg = [(r.get('fg_game') or '').strip() for _, _, r in win]
    S['fg_win'] = (sum(1 for v in fg if v == '1') / float(len(fg))) if fg else None
    S['fg0_before_end'] = sum(1 for t, _, r in pts if t <= me and (r.get('fg_game') or '').strip() != '1')
    S['fg_vals'] = '/'.join(sorted(set((r.get('fg_game') or '').strip() for _, _, r in pts)))
    # longest slow stretch inside the window (rows)
    S['win_longest'] = max([sum(1 for k in range(i, j + 1) if ws <= pts[k][0] <= we) for i, j in st] or [0])
    return S


def sys_centres(srows):
    pts = sorted(((num(r.get('epoch_s')), r) for r in srows if num(r.get('epoch_s')) is not None),
                 key=lambda p: p[0])
    out, prev = [], None
    for t, r in pts:
        out.append(((prev + t) / 2.0 if prev is not None else t - 0.5, r))
        prev = t
    return out


# ---------------------------------------------------------------- frames / bins

def load_frames(path, column, extra=(), stop_after=None):
    """frame_summary.py's rules (as w4b_readout.load_frames for perf.csv): a row needs the header's field count and
    every field an integer; a last line without a newline is dropped; good rows are indexed like frames.json."""
    with open(path, 'rb') as fh:
        data = fh.read()
    nl = data.find(b'\n')
    if nl < 0:
        return None, [], {}
    header = [h.strip() for h in data[:nl].decode('ascii', 'replace').rstrip('\r').split(',')]
    if column not in header:
        return header, [], {}
    col, width = header.index(column), len(header)
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
            vals = [int(p) for p in parts]
        except ValueError:
            continue
        fts.append(vals[col])
        for c, i in xcols:
            xs[c].append(vals[i])
    return header, fts, xs


def frame_bins(rd, fj, rj, srows):
    out = {'bins': [], 'check': []}
    win = fj.get('window') if isinstance(fj.get('window'), dict) else None
    if not win:
        out['note'] = 'no frames.json window'
        return out
    col = fj.get('column') or ''
    if fj.get('source') != 'perf' or col != 'frame_time_us':
        out['note'] = 'frame source %s/%s not handled' % (fj.get('source'), col)
        return out
    path = os.path.join(rd, os.path.basename(str(fj.get('file') or 'perf.csv')))
    first, nrows = int(num(win.get('first_row')) or 0), int(num(win.get('rows')) or 0)
    _, fts, xs = load_frames(path, col, ('draw_calls',), stop_after=first + nrows)
    wf = fts[first:first + nrows]
    wd = (xs.get('draw_calls') or [None] * len(fts))[first:first + nrows]
    pairs = [(t, dc) for t, dc in zip(wf, wd) if t > 0]
    if not pairs:
        out['note'] = 'no frames in the window'
        return out
    total = float(sum(t for t, _ in pairs))
    out['frames'], out['window_s'], out['fps'] = len(pairs), total / 1e6, len(pairs) * 1e6 / total
    if num(fj.get('frames')) is not None and abs(len(pairs) - num(fj.get('frames'))) > 0.5:
        out['check'].append('frames %d vs frames.json %s' % (len(pairs), fj.get('frames')))
    if num(fj.get('mean_fps')) is not None and abs(round(out['fps'], 3) - num(fj.get('mean_fps'))) > 0.0006:
        out['check'].append('fps %.3f vs frames.json %s' % (out['fps'], fj.get('mean_fps')))
    lim = BIN_S * 1e6
    groups, cum = [], 0.0
    for t, dc in pairs:
        cum += t
        b = int(max(0.0, cum - 1e-3) // lim)
        while len(groups) <= b:
            groups.append([])
        groups[b].append((t, dc))
    total_s = cum / 1e6
    if len(groups) >= 2 and total_s - BIN_S * (len(groups) - 1) < BIN_S / 2.0:
        tail = groups.pop()
        groups[-1].extend(tail)
    ms_e = num((rj.get('measure_start') or {}).get('epoch_s')) or num((rj.get('sys') or {}).get('window_start_epoch'))
    cents = sys_centres(srows)
    for i, g in enumerate(groups):
        t0 = i * BIN_S
        t1 = total_s if i == len(groups) - 1 else (i + 1) * BIN_S
        s = float(sum(t for t, _ in g))
        B = {'bin': i, 't0': t0, 't1': t1, 'frames': len(g), 'fps': (len(g) * 1e6 / s) if s > 0 else None}
        ds = sorted(dc for _, dc in g if dc is not None)
        B['draws_p50'] = nearest_rank(ds, 1, 2) if ds else None
        B['draws_tw'] = (sum(dc * t for t, dc in g if dc is not None) / s) if (s > 0 and ds) else None
        if ms_e is not None:
            a0, a1 = ms_e + t0, ms_e + t1
            last = i == len(groups) - 1
            sel = [r for c, r in cents if a0 <= c < a1 or (last and c == a1)]
            es = [e for e in (num(r.get('e_eff_mhz')) for r in sel) if e is not None]
            B['sys_n'] = len(sel)
            B['e_mean'] = mean(es)
            B['e_low'] = (sum(1 for e in es if e < E_SLOW) / float(len(es))) if es else None
            B['p_mean'] = mean([num(r.get('p_eff_mhz')) for r in sel])
            B['pu_mean'] = mean([num(r.get('p_util_pct')) for r in sel])
            B['eu_mean'] = mean([num(r.get('e_util_pct')) for r in sel])
        out['bins'].append(B)
    return out


# ---------------------------------------------------------------- stats

def ranks(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return r


def spearman(x, y, perms=PERMS, seed=12345):
    pts = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    n = len(pts)
    if n < 3:
        return n, None, None
    rx, ry = ranks([a for a, _ in pts]), ranks([b for _, b in pts])
    mx, my = sum(rx) / n, sum(ry) / n
    cx, cy = [a - mx for a in rx], [b - my for b in ry]
    sxx, syy = sum(a * a for a in cx), sum(b * b for b in cy)
    if sxx == 0 or syy == 0:
        return n, None, None
    den = math.sqrt(sxx * syy)
    rho = sum(a * b for a, b in zip(cx, cy)) / den
    rnd = random.Random(seed)
    cy2, hit = list(cy), 0
    for _ in range(perms):
        rnd.shuffle(cy2)
        if abs(sum(a * b for a, b in zip(cx, cy2)) / den) >= abs(rho) - 1e-12:
            hit += 1
    return n, rho, (hit + 1) / (perms + 1.0)


# ---------------------------------------------------------------- Agent 8 outputs

def parse_timerq(path, name):
    """Agent 11/8 timerq text: old layout (matrix run blocking onset slow_pct span fg ...) or the 3-mode layout
    with a header 'matrix run arm mode env pcvar precise ms1 onset_s slow_pct span_s fg flags'."""
    out = {}
    try:
        with open(path, encoding='utf-8-sig', errors='replace') as fh:
            lines = fh.read().splitlines()
    except OSError:
        return out
    hdr = None
    for ln in lines:
        t = ln.split()
        if not t:
            continue
        if t[0] == 'matrix':
            hdr = ({k: i for i, k in enumerate(t)}
                   if all(k in t for k in ('run', 'onset_s', 'slow_pct', 'span_s', 'ms1')) else None)
            continue
        if t[0] != name or len(t) < 6 or not re.match(r'^\d{4}-', t[1]):
            continue
        if hdr:
            def g(k):
                return t[hdr[k]] if (k in hdr and hdr[k] < len(t)) else None
            out[g('run')] = {'blocking': g('mode'), 'onset': None if g('onset_s') in (None, '-') else num(g('onset_s')),
                             'slow_pct': num(g('slow_pct')), 'span': num(g('span_s')), 'fg': g('fg') or '',
                             'ms1': num(g('ms1')), 'precise': num(g('precise')), 'env': g('env')}
        else:
            out[t[1]] = {'blocking': t[2], 'onset': None if t[3] == '-' else num(t[3]),
                         'slow_pct': num(t[4]), 'span': num(t[5]), 'fg': t[6] if len(t) > 6 else ''}
    return out


R7_RE = re.compile(r'(\d{4}-\S+) \((\S+), (\w+) wait\): 1 ms lines (\d+), precise lines (\d+), '
                   r'REX_TIMER_WAIT_BLOCKING (absent|=[^,\s]+)')
R7_RE2 = re.compile(r'(\d{4}-[^\s:]+): 1 ms lines (\d+), REX_TIMER_WAIT_BLOCKING ?(=[^,\s]+|absent)')


def parse_r7(path):
    try:
        with open(path, encoding='utf-8-sig', errors='replace') as fh:
            text = fh.read()
    except OSError:
        return {}
    m = re.search(r'## R7(.*?)(?:\n## |\Z)', text, re.S)
    sec = m.group(1) if m else ''
    res = {k: {'mode': md, 'ms1': int(a), 'precise': int(b), 'env': e} for k, _, md, a, b, e in R7_RE.findall(sec)}
    for k, a, e in R7_RE2.findall(sec):  # W4b layout: '- PASS: 1549-d11t-r1: 1 ms lines 1, REX_TIMER_WAIT_BLOCKING=1'
        res.setdefault(k, {'mode': None, 'ms1': int(a), 'precise': None, 'env': e.strip()})
    return res


def parse_rules(path):
    try:
        with open(path, encoding='utf-8-sig', errors='replace') as fh:
            text = fh.read()
    except OSError:
        return None, None
    m = re.search(r'## R3(.*?)(?:\n## |\Z)', text, re.S)
    sec = m.group(1) if m else ''
    at = {k: num(v) for k, v in R3_AT_RE.findall(sec)}
    drop = {k: (num(o), num(p)) for k, o, p in R3_DROP_RE.findall(sec)}
    if not at and not drop:
        return None, None
    return at, drop


def parse_cmp_json(path):
    J = load_json(path) if path else None
    out = {}
    if isinstance(J, dict):
        for r in J.get('runs') or []:
            if isinstance(r, dict) and r.get('stat_bins'):
                out[r.get('name')] = [num(b.get('fps')) for b in r['stat_bins']]
    return out


def parse_phase(path):
    J = load_json(path) if path else None
    out = {}
    if isinstance(J, list):
        for r in J:
            if isinstance(r, dict):
                out[r.get('run')] = r.get('slow_bins_s')
    return out


# ---------------------------------------------------------------- report helpers

def table(w, head, rows):
    w('| ' + ' | '.join(head) + ' |')
    w('|' + '---|' * len(head))
    for r in rows:
        w('| ' + ' | '.join(str(c).replace('|', '/') for c in r) + ' |')
    w('')


def write_csv(path, head, rows):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        cw = csv.writer(fh)
        cw.writerow(head)
        for r in rows:
            cw.writerow(['' if c is None else c for c in r])


def r1(v, nd=1):
    return None if v is None else round(v, nd)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('dir')
    ap.add_argument('out')
    ap.add_argument('--timerq')
    ap.add_argument('--rules')
    ap.add_argument('--cmp-json')
    ap.add_argument('--phase')
    ap.add_argument('--claim', default='')
    a = ap.parse_args()
    d = os.path.abspath(a.dir)
    out = os.path.abspath(a.out)
    if os.path.basename(out).lower() != 'scan' or '\\readout\\' not in out.lower():
        sys.exit('refusing to write outside a ...\\readout\\<w>\\scan dir: %s' % out)
    os.makedirs(out, exist_ok=True)
    mname = os.path.basename(d)

    rows = read_rows(os.path.join(d, 'results.csv')) or []
    mj = load_json(os.path.join(d, 'matrix.json')) or {}
    cfgs = {x['id']: x for x in (mj.get('arms') or []) if isinstance(x, dict) and x.get('id')}
    present = list(dict.fromkeys(r['arm'] for r in rows))
    order = [i for i in cfgs if i in present] + [i for i in present if i not in cfgs]
    ref = next((x['id'] for x in (mj.get('arms') or []) if x.get('ref') and x.get('id') in present), None) \
        or mj.get('reference')
    tq = parse_timerq(a.timerq, mname) if a.timerq else {}
    r3_at, r3_drop = parse_rules(a.rules) if a.rules else (None, None)
    cmpb = parse_cmp_json(a.cmp_json)
    phase = parse_phase(a.phase)

    runs = []
    for r in rows:
        name = os.path.basename((r.get('run_dir') or '').rstrip('\\/'))
        rd = os.path.join(d, 'runs', name)
        rj = load_json(os.path.join(rd, 'run.json')) or {}
        fj = load_json(os.path.join(rd, 'frames.json')) or {}
        x = {'seq': int(r['seq']), 'round': r.get('round'), 'arm': r['arm'], 'name': name, 'rd': rd,
             'scored': (r.get('scored') or '').lower() == 'true', 'valid': (r.get('valid_timing') or '').lower() == 'true',
             'fps_csv': num(r.get('fps_mean')), 'rj': rj, 'fj': fj}
        x['log'] = scan_logs(rd)
        x['proof_dev'] = proof_check(x, cfgs.get(r['arm'], {}))
        x['health_dev'] = health_check(x)
        ff = num(rj.get('ff_signal_epoch_s'))
        sysb = rj.get('sys') if isinstance(rj.get('sys'), dict) else {}
        ws = num(sysb.get('window_start_epoch')) or num((rj.get('measure_start') or {}).get('epoch_s'))
        we = num(sysb.get('window_end_epoch')) or num((rj.get('measure_end') or {}).get('epoch_s'))
        me = num((rj.get('measure_end') or {}).get('epoch_s')) or we
        srows = read_rows(os.path.join(rd, 'sys.csv')) or []
        x['slow'] = slow_scan(srows, ff, ws, we, me) if (ff and ws and we) else {'n': 0}
        x['sysw'] = sysb.get('window') if isinstance(sysb.get('window'), dict) else {}
        x['fr'] = frame_bins(rd, fj, rj, srows)
        x['fps'] = x['fr'].get('fps') if x['fr'].get('fps') is not None else num(fj.get('mean_fps'))
        x['rj_install_dat'] = (rj.get('light') or {}).get('install_dat_fail')
        runs.append(x)

    scored = [x for x in runs if x['scored']]
    # slow bins
    for x in runs:
        bins = x['fr']['bins']
        fl = [b['fps'] for b in bins if b.get('fps')]
        med = statistics.median(fl) if fl else None
        x['bin_med'] = med
        for b in bins:
            b['ratio'] = (b['fps'] / med) if (med and b.get('fps')) else None
            b['flag'] = bool(x['scored'] and b['ratio'] is not None and b['ratio'] < SLOW_BIN)
            b['e_cond'] = b.get('e_mean') is not None and b['e_mean'] < E_SLOW
            b['elow_half'] = b.get('e_low') is not None and b['e_low'] >= 0.5
            b['p_cond'] = b.get('pu_mean') is not None and b['pu_mean'] >= P_BUSY
            cb = cmpb.get(x['name'])
            b['cmp'] = cb[b['bin']] if cb and b['bin'] < len(cb) else None

    # ------------------------------------------------------------ CSVs
    write_csv(os.path.join(out, 'proof.csv'),
              ['seq', 'run', 'arm', 'scored', 'valid_timing', 'bin_dir', 'bin_ok', 'cvars', 'env_set',
               'n_1ms', 'exp_1ms', 'n_precise', 'exp_precise', 'env_blocking', 'exp_env_blocking', 'deviations'],
              [[x['seq'], x['name'], x['arm'], x['scored'], x['valid'], x['bin'], x['bin_ok'], ';'.join(x['cvars']),
                json.dumps(x['env_set']), x['log']['n1ms'], x['exp_1ms'], x['log']['nprec'], x['exp_prec'],
                x['has_env'], x['exp_env'], ' | '.join(x['proof_dev'])] for x in runs])
    write_csv(os.path.join(out, 'health.csv'),
              ['seq', 'run', 'arm', 'files', 'lines', 'info', 'warning', 'error', 'critical', 'FATAL_lines',
               'warning_non_install', 'install_dat_failed', 'runner_install_dat_fail', 'install_other_warn',
               'stuck_lock', 'unknown_cvar', 'unknown_flaglike', 'closing', 'exec_complete', 'terminated',
               'deviations'],
              [[x['seq'], x['name'], x['arm'], ' + '.join(x['log']['files']), x['log']['lines'],
                x['log']['lvl'].get('info', 0), x['log']['lvl'].get('warning', 0), x['log']['lvl'].get('error', 0),
                x['log']['lvl'].get('critical', 0), x['log']['fatal'], x['log']['warn_non'], x['log']['dat'],
                x['rj_install_dat'], x['log']['inst_other'], x['log']['stuck'], x['log']['unk'], x['log']['unk2'],
                x['log']['closing'], x['log']['exec_done'], x['log']['term'], ' | '.join(x['health_dev'])]
               for x in runs])
    write_csv(os.path.join(out, 'slow.csv'),
              ['seq', 'run', 'arm', 'scored', 'valid_timing', 'fps', 'sys_rows_from_ff', 'onset_s', 'timerq_onset_s',
               'r3_onset_s', 'run_low_share_pct', 'timerq_slow_pct', 'in_3plus_stretch_pct', 'stretches',
               'span_s', 'stretch_in_window', 'window_rows', 'window_e_low_pct', 'r3_window_pct',
               'window_longest_stretch_rows', 'e_eff_mean', 'p_eff_mean', 'p_util_mean', 'e_util_mean',
               'fg_window_share', 'fg_not1_rows_before_measure_end', 'runjson_e_eff', 'runjson_p_eff',
               'runjson_p_util', 'runjson_e_util'],
              [[x['seq'], x['name'], x['arm'], x['scored'], x['valid'], r1(x['fps'], 3), x['slow'].get('n'),
                r1(x['slow'].get('onset'), 1), (tq.get(x['name']) or {}).get('onset'),
                (r3_at or {}).get(x['name']), r1(None if x['slow'].get('low_share') is None else 100 * x['slow']['low_share']),
                (tq.get(x['name']) or {}).get('slow_pct'),
                r1(None if x['slow'].get('stretch_share') is None else 100 * x['slow']['stretch_share']),
                x['slow'].get('stretches'), r1(x['slow'].get('span'), 1), x['slow'].get('in_win'),
                x['slow'].get('win_n'), r1(None if x['slow'].get('win_low') is None else 100 * x['slow']['win_low']),
                ((r3_drop or {}).get(x['name']) or (None, None))[1], x['slow'].get('win_longest'),
                r1(x['slow'].get('e_mean'), 0), r1(x['slow'].get('p_mean'), 0), r1(x['slow'].get('pu_mean'), 2),
                r1(x['slow'].get('eu_mean'), 2), r1(x['slow'].get('fg_win'), 3), x['slow'].get('fg0_before_end'),
                x['sysw'].get('e_eff_mhz_mean'), x['sysw'].get('p_eff_mhz_mean'), x['sysw'].get('p_util_mean'),
                x['sysw'].get('e_util_mean')] for x in runs])
    brows = []
    for x in runs:
        for b in x['fr']['bins']:
            brows.append([x['seq'], x['name'], x['arm'], x['scored'], b['bin'], r1(b['t0'], 2), r1(b['t1'], 2),
                          b['frames'], r1(b['fps'], 2), r1(b['ratio'], 3), b['flag'], b['draws_p50'],
                          r1(b['draws_tw'], 1), b.get('sys_n'), r1(b.get('e_mean'), 0),
                          r1(None if b.get('e_low') is None else 100 * b['e_low'], 0), r1(b.get('p_mean'), 0),
                          r1(b.get('pu_mean'), 2), r1(b.get('eu_mean'), 2), r1(b['cmp'], 1),
                          r1(None if (b['cmp'] is None or b['fps'] is None) else b['fps'] - b['cmp'], 2)])
    write_csv(os.path.join(out, 'bins.csv'),
              ['seq', 'run', 'arm', 'scored', 'bin', 't0_s', 't1_s', 'frames', 'fps', 'fps_over_run_median_bin',
               'slow_bin', 'draws_p50', 'draws_timeweighted_mean', 'sys_rows', 'e_eff_mean', 'e_low_pct',
               'p_eff_mean', 'p_util_mean', 'e_util_mean', 'agent8_w4bjson_fps', 'diff_fps'], brows)

    # warning types per arm
    def arm_types(sel, key='wtypes'):
        u = {}
        for x in sel:
            for k, v in x['log'][key].items():
                e = u.setdefault(k, [0, 0, []])
                e[0] += 1
                e[1] += v
                e[2].append(x['name'])
        return u

    sc_by_arm = {arm: [x for x in scored if x['arm'] == arm] for arm in order}
    types_by_arm = {arm: arm_types(sc_by_arm[arm]) for arm in order}
    cold = [x for x in runs if not x['scored']]
    all_types = sorted(set(k for x in runs for k in x['log']['wtypes']))
    wt_rows = []
    for k in all_types:
        row = [k, sum(x['log']['wtypes'].get(k, 0) for x in runs)]
        for arm in order:
            e = types_by_arm[arm].get(k)
            row.append('%d/%d runs (%d)' % (e[0], len(sc_by_arm[arm]), e[1]) if e else '0/%d' % len(sc_by_arm[arm]))
        for x in cold:
            row.append(x['log']['wtypes'].get(k, 0))
        wt_rows.append(row)
    write_csv(os.path.join(out, 'warn_types.csv'),
              ['warning type (normalised)', 'total lines'] + ['%s scored' % arm for arm in order]
              + ['%s (cold)' % x['name'] for x in cold], wt_rows)

    def diff_types(arms_a, arms_b):
        A = {}
        for arm in arms_a:
            for k, e in types_by_arm[arm].items():
                A.setdefault(k, []).extend(e[2])
        B = set()
        for arm in arms_b:
            B |= set(types_by_arm[arm])
        return {k: v for k, v in A.items() if k not in B}

    # ------------------------------------------------------------ report
    L = []
    w = L.append
    w('# Read-only scan: %s (%s)' % (mname, mj.get('title', '')))
    w('')
    w('- matrix dir: %s; %d runs (%d scored, %d cold); reference arm %s; arms %s' % (
        d, len(runs), len(scored), len(cold), ref, ', '.join(order)))
    w('- script: %s (stdlib, read-only; rules in its docstring); CSVs next to this file: proof.csv, health.csv, '
      'slow.csv, bins.csv, warn_types.csv' % os.path.abspath(__file__))
    w('- Agent 8 inputs compared: timerq %s (%d rows of %s); rules %s; bins json %s (%d runs); phase %s' % (
        a.timerq or '-', len(tq), mname, a.rules or '-', a.cmp_json or '-', len(cmpb), a.phase or '-'))
    w('')

    # 1 proof
    w('## 1. Proof lines and arm configuration (all runs)')
    w('')
    w('Expected (from matrix.json arms): 1 ms line exactly once where the arm sets host_timer_resolution_ms=1, else 0; '
      'precise line exactly once where it sets timer_queue_precise_wait=true, else 0; REX_TIMER_WAIT_BLOCKING=1 in '
      'run.json env_set only where the arm has it; params.cvar, args and bin_dir equal to the arm.')
    w('')
    prow = []
    for x in runs:
        env = ', '.join('%s=%s' % kv for kv in x['env_set'].items()) or '-'
        prow.append([x['seq'], x['name'], x['arm'], ('scored' if x['scored'] else 'cold') + ('' if x['valid'] else ' (not timing)'),
                     '%s %s' % (os.path.basename(x['bin'].rstrip('\\/')), 'ok' if x['bin_ok'] else 'MISMATCH'),
                     '%d %s' % (len(x['cvars']), 'ok' if x['cvars'] == [str(c) for c in cfgs.get(x['arm'], {}).get('cvars', [])] else 'MISMATCH'),
                     env, '%d (%d)' % (x['log']['n1ms'], x['exp_1ms']), '%d (%d)' % (x['log']['nprec'], x['exp_prec']),
                     '; '.join(x['proof_dev']) or 'none'])
    table(w, ['seq', 'run', 'arm', 'kind', 'bin', 'cvars n', 'env_set', '1 ms lines (exp)', 'precise lines (exp)',
              'deviations'], prow)
    pdev = [(x['name'], dv) for x in runs for dv in x['proof_dev']]
    w('- proof deviations: %s' % ('; '.join('%s: %s' % p for p in pdev) if pdev else 'none (%d runs)' % len(runs)))
    r7 = parse_r7(a.rules) if a.rules else {}
    xdev, ntq = [], 0
    for x in runs:
        t = tq.get(x['name']) or {}
        if t.get('ms1') is not None:
            ntq += 1
            if int(t['ms1']) != x['log']['n1ms']:
                xdev.append('%s 1 ms lines mine %d vs timerq %s' % (x['name'], x['log']['n1ms'], t['ms1']))
            if t.get('precise') is not None and int(t['precise']) != x['log']['nprec']:
                xdev.append('%s precise lines mine %d vs timerq %s' % (x['name'], x['log']['nprec'], t['precise']))
            if t.get('env') in ('True', 'False') and (t['env'] == 'True') != x['has_env']:
                xdev.append('%s env mine %s vs timerq %s' % (x['name'], x['has_env'], t['env']))
        q = r7.get(x['name'])
        if q:
            if q['ms1'] != x['log']['n1ms']:
                xdev.append('%s 1 ms lines mine %d vs R7 %d' % (x['name'], x['log']['n1ms'], q['ms1']))
            if q['precise'] is not None and q['precise'] != x['log']['nprec']:
                xdev.append('%s precise lines mine %d vs R7 %d' % (x['name'], x['log']['nprec'], q['precise']))
            if (q['env'] != 'absent') != x['has_env']:
                xdev.append('%s env mine %s vs R7 %s' % (x['name'], x['has_env'], q['env']))
        elif r7 and any(v['precise'] is not None for v in r7.values()):
            xdev.append('%s not in R7' % x['name'])
    w('- vs Agent 8 (timerq ms1/precise/env columns: %d runs; rules.md R7 per-run lines: %d runs): %s' % (
        ntq, len(r7), '; '.join(xdev) if xdev else ('all agree' if (ntq or r7) else 'nothing to compare')))
    tl, traw = {}, {}
    for x in runs:
        for k, v in x['log']['timer_lines'].items():
            tl.setdefault(k, []).append('%s x%d' % (x['name'], v))
            traw.setdefault(k, x['log']['timer_raw'].get(k, k))
    for k, v in sorted(tl.items()):
        w('- timer-related log line `%s` (normalised `%s`): %d runs (%s)' % (traw[k], k, len(v), ', '.join(v)))
    w('')

    # 2 health
    w('## 2. game.log health (all runs)')
    w('')
    hrow = []
    for x in runs:
        lg = x['log']
        hrow.append([x['seq'], x['name'], x['arm'], ' + '.join(lg['files']) or '-', lg['lvl'].get('error', 0),
                     lg['lvl'].get('critical', 0), lg['fatal'], lg['lvl'].get('warning', 0), lg['warn_non'],
                     '%d (runner %s)' % (lg['dat'], x['rj_install_dat']), lg['inst_other'], lg['stuck'],
                     '%d / %d' % (lg['unk'], lg['unk2']),
                     'ok' if (lg['closing'] and lg['exec_done'] and lg['term']) else 'INCOMPLETE',
                     '; '.join(x['health_dev']) or 'none'])
    table(w, ['seq', 'run', 'arm', 'log files', '[error]', '[critical]', 'FATAL', '[warning] all', 'non-INSTALL [warning]',
              'INSTALL .DAT FAILED', 'other INSTALL warn', 'STUCK-LOCK', 'unknown cvar / flag-like', 'shutdown lines',
              'deviations'], hrow)
    hdev = [(x['name'], dv) for x in runs for dv in x['health_dev']]
    w('- health deviations: %s' % ('; '.join('%s: %s' % p for p in hdev) if hdev else 'none'))
    odd = [(x['name'], ln) for x in runs for ln in x['log']['odd_lines']]
    for nm, ln in odd[:40]:
        w('  - %s: `%s`' % (nm, ln))
    w('')
    w('Warning types (normalised; k/n scored runs of the arm that have it, total lines in brackets; cold runs separately):')
    w('')
    table(w, ['warning type', 'total'] + order + ['%s (cold)' % x['name'] for x in cold],
          [[r_[0]] + r_[1:] for r_ in wt_rows])
    if ref in types_by_arm:
        for arm in order:
            if arm == ref:
                continue
            dt = diff_types([arm], [ref])
            w('- types in %s (scored) but not in %s (scored): %s' % (
                arm, ref, '; '.join('`%s` (%s)' % (k, ', '.join(v)) for k, v in sorted(dt.items())) or 'none'))
            dt2 = diff_types([ref], [arm])
            w('- types in %s (scored) but not in %s (scored): %s' % (
                ref, arm, '; '.join('`%s` (%s)' % (k, ', '.join(v)) for k, v in sorted(dt2.items())) or 'none'))
        for x in cold:
            ck = sorted(k for k in x['log']['wtypes'] if k not in types_by_arm[ref])
            w('- types in the cold run %s but not in %s (scored): %s' % (
                x['name'], ref, '; '.join('`%s`' % k for k in ck) or 'none'))
    timer_arms = [arm for arm in order if arm.startswith('d11')]
    if 's0' in types_by_arm and timer_arms:
        dt = diff_types(timer_arms, ['s0'])
        w('- types in the timer arms %s (scored) but not in s0 (scored): %s' % (
            '/'.join(timer_arms), '; '.join('`%s` (%s)' % (k, ', '.join(v)) for k, v in sorted(dt.items())) or 'none'))
        dt2 = diff_types(['s0'], timer_arms)
        w('- types in s0 (scored) but not in any timer arm (scored): %s' % (
            '; '.join('`%s` (%s)' % (k, ', '.join(v)) for k, v in sorted(dt2.items())) or 'none'))
    et = {}
    for x in runs:
        for k, v in list(x['log']['etypes'].items()) + list(x['log']['ctypes'].items()):
            et.setdefault(k, []).append('%s x%d' % (x['name'], v))
    w('- [error]/[critical] types: %s' % ('; '.join('`%s` (%s)' % (k, ', '.join(v)) for k, v in sorted(et.items())) or 'none'))
    w('')

    # 3 slow state
    w('## 3. Slow state (sys.csv from the first frame on; E-cores < %.0f MHz for %d+ samples in a row)' % (E_SLOW, MIN_ROWS))
    w('')
    srow = []
    for x in runs:
        S = x['slow']
        t = tq.get(x['name']) or {}
        r3o = (r3_at or {}).get(x['name'])
        r3d = (r3_drop or {}).get(x['name'])
        srow.append([x['seq'], x['name'], x['arm'] + ('' if x['scored'] else ' (cold)'),
                     '%s / %s / %s' % (f(S.get('onset'), 1), f(t.get('onset'), 0) if t else '?', f(r3o, 0)),
                     '%s / %s' % (pc(S.get('low_share')), f(t.get('slow_pct'), 0) if t else '?'),
                     pc(S.get('stretch_share')), S.get('stretches', '-'),
                     'yes' if S.get('in_win') else 'no',
                     '%s / %s' % (pc(S.get('win_low')), f(r3d[1], 0) if r3d else '-'),
                     S.get('win_n', '-'), f(S.get('e_mean'), 0), f(S.get('p_mean'), 0), f(S.get('pu_mean'), 1),
                     f(S.get('eu_mean'), 1),
                     '%s / %s / %s / %s' % (x['sysw'].get('e_eff_mhz_mean', '-'), x['sysw'].get('p_eff_mhz_mean', '-'),
                                            x['sysw'].get('p_util_mean', '-'), x['sysw'].get('e_util_mean', '-')),
                     '%s (%s; %s)' % (pc(S.get('fg_win')), S.get('fg0_before_end', '-'), S.get('fg_vals', '-')),
                     f(x['fps'], 1)])
    table(w, ['seq', 'run', 'arm', 'onset s: mine / timerq / R3', 'run E<800 share %: mine / timerq',
              'in 3+ stretches %', 'stretches', 'stretch in window', 'window E<800 share %: mine / R3', 'window rows',
              'win E MHz', 'win P MHz', 'win P util %', 'win E util %', 'run.json sys.window E/P MHz, P/E util',
              'fg in window % (fg!=1 rows before measure end; fg values from ff)', 'window fps'], srow)
    # agreement
    agree = []
    for x in runs:
        S, t = x['slow'], tq.get(x['name'])
        if t is not None:
            mo = None if S.get('onset') is None else round(S['onset'])
            if mo != (None if t['onset'] is None else int(t['onset'])):
                agree.append('%s onset mine %s vs timerq %s' % (x['name'], f(S.get('onset'), 2), t['onset']))
            if S.get('low_share') is not None and round(100 * S['low_share']) != t['slow_pct']:
                agree.append('%s run share mine %.1f%% vs timerq %s%%' % (x['name'], 100 * S['low_share'], t['slow_pct']))
        elif tq:
            agree.append('%s not in timerq' % x['name'])
        if r3_at is not None and x['scored']:
            ro = r3_at.get(x['name'])
            mo = None if S.get('onset') is None else round(S['onset'])
            if (ro is None) != (mo is None) or (ro is not None and int(ro) != mo):
                agree.append('%s onset mine %s vs R3 %s' % (x['name'], f(S.get('onset'), 2), ro))
            rd_ = (r3_drop or {}).get(x['name'])
            if rd_ is not None and S.get('win_low') is not None and round(100 * S['win_low']) != rd_[1]:
                agree.append('%s window share mine %.1f%% vs R3 %s%%' % (x['name'], 100 * S['win_low'], rd_[1]))
            if bool(S.get('in_win')) != (rd_ is not None):
                agree.append('%s stretch in window mine %s vs R3 %s' % (x['name'], S.get('in_win'), rd_ is not None))
    sw = [x for x in scored if x['slow'].get('in_win')]
    ons = [x['slow']['onset'] for x in scored if x['slow'].get('onset') is not None]
    w('- scored runs with a 3+ stretch overlapping the window: %d of %d; onsets (scored) %s-%s s; never slow: %s' % (
        len(sw), len(scored), f(min(ons) if ons else None, 0), f(max(ons) if ons else None, 0),
        ', '.join(x['name'] for x in runs if x['slow'].get('onset') is None) or 'none'))
    w('- foreground: window fg share min %s %% over scored runs; rows with fg_game != 1 between the first frame and the '
      'measure end: %s' % (pc(min([x['slow'].get('fg_win') for x in scored if x['slow'].get('fg_win') is not None] or [None])),
                          ', '.join('%s %d' % (x['name'], x['slow'].get('fg0_before_end'))
                                    for x in runs if x['slow'].get('fg0_before_end')) or 'none'))
    w('- vs Agent 8 (timerq.txt onset rounded to 1 s and run share; rules.md R3 onset and window share): %s' % (
        '; '.join(agree) if agree else 'all agree'))
    mism = []
    for x in runs:
        sv = x['sysw']
        for k_mine, k_rj in (('e_mean', 'e_eff_mhz_mean'), ('p_mean', 'p_eff_mhz_mean'), ('pu_mean', 'p_util_mean'),
                             ('eu_mean', 'e_util_mean')):
            m_, t_ = x['slow'].get(k_mine), num(sv.get(k_rj))
            if m_ is not None and t_ is not None and abs(m_ - t_) > (1.0 if 'mhz' in k_rj else 0.05):
                mism.append('%s %s %.2f vs %s' % (x['name'], k_rj, m_, sv.get(k_rj)))
    w('- window means vs run.json sys.window (tolerance 1 MHz / 0.05 pts): %s' % ('; '.join(mism) or 'all agree'))
    w('')

    # 4 bins
    w('## 4. 10 s bins of the scored window (perf.csv frame times; sys.csv rows by interval centre)')
    w('')
    nb = max([len(x['fr']['bins']) for x in runs] or [0])
    heads = ['%d-%d s' % (i * BIN_S, (i + 1) * BIN_S) for i in range(nb)]

    def bin_table(title, fn):
        w('### ' + title)
        w('')
        rr = []
        for x in runs:
            if not x['fr']['bins']:
                continue
            cells = []
            for i in range(nb):
                b = x['fr']['bins'][i] if i < len(x['fr']['bins']) else None
                cells.append('-' if b is None else fn(b))
            rr.append([x['seq'], x['name'] + ('' if x['scored'] else ' (cold)')] + cells)
        table(w, ['seq', 'run'] + heads, rr)

    bin_table('fps per bin (`*` = below 0.85 x the run\'s median bin; ratio in bins.csv column fps_over_run_median_bin)',
              lambda b: '%s%s' % (f(b['fps'], 1), '*' if b['flag'] else ''))
    bin_table('draws/frame p50 per bin', lambda b: '%s' % b['draws_p50'])
    bin_table('E MHz mean per bin (E<800 share %)', lambda b: '%s (%s)' % (f(b.get('e_mean'), 0), pc(b.get('e_low'))))
    bin_table('P util % mean per bin', lambda b: f(b.get('pu_mean'), 1))
    bin_table('P MHz mean per bin', lambda b: f(b.get('p_mean'), 0))
    bin_table('E util % mean per bin', lambda b: f(b.get('eu_mean'), 1))
    fb = [(x, b) for x in scored for b in x['fr']['bins'] if b['flag']]
    w('Slow bins (scored runs):')
    w('')
    table(w, ['run', 'bin', 'fps', 'x run median bin', 'E MHz', 'E<800 share %', 'P util %', 'P MHz', 'E util %',
              'E mean < 800', 'P util >= 90'],
          [[x['name'], '%d-%d s' % (b['t0'], b['t0'] + BIN_S), f(b['fps'], 1), f(b['ratio'], 2), f(b.get('e_mean'), 0),
            pc(b.get('e_low')), f(b.get('pu_mean'), 1), f(b.get('p_mean'), 0), f(b.get('eu_mean'), 1),
            'yes' if b['e_cond'] else 'no', 'yes' if b['p_cond'] else 'no'] for x, b in fb])
    allb = [b for x in scored for b in x['fr']['bins']]
    ok_b = [b for b in allb if not b['flag']]

    def cnt(bs, key):
        return sum(1 for b in bs if b[key])
    w('- bins of scored runs: %d; slow: %d in %d runs (%s)' % (
        len(allb), len(fb), len(set(x['name'] for x, _ in fb)), ', '.join(sorted(set(x['name'] for x, _ in fb))) or '-'))
    for lab, bs in (('slow bins', [b for _, b in fb]), ('other bins', ok_b)):
        w('- %s (n=%d): E mean < 800 in %d; E<800 share >= 50%% in %d; P util >= 90 in %d; both E<800 and P>=90 in %d; '
          'neither in %d' % (lab, len(bs), cnt(bs, 'e_cond'), cnt(bs, 'elow_half'), cnt(bs, 'p_cond'),
                             sum(1 for b in bs if b['e_cond'] and b['p_cond']),
                             sum(1 for b in bs if not b['e_cond'] and not b['p_cond'])))
    wr = []
    for x in scored:
        bs = x['fr']['bins']
        sl = [b for b in bs if b['flag']]
        if sl:
            ot = [b for b in bs if not b['flag']]
            wr.append('%s: slow bins E %s MHz / P util %s vs other bins E %s / P util %s' % (
                x['name'], f(mean([b.get('e_mean') for b in sl]), 0), f(mean([b.get('pu_mean') for b in sl]), 1),
                f(mean([b.get('e_mean') for b in ot]), 0), f(mean([b.get('pu_mean') for b in ot]), 1)))
    for s_ in wr:
        w('  - ' + s_)
    rel = [(b['ratio'], b.get('e_mean'), b.get('e_low'), b.get('pu_mean')) for b in allb if b['ratio'] is not None]
    for lab, idx in (('E MHz mean', 1), ('E<800 share', 2), ('P util mean', 3)):
        n_, rho, p = spearman([r_[0] for r_ in rel], [r_[idx] for r_ in rel])
        w('- pooled bins (descriptive, bins of a run are not independent): Spearman of bin fps / run median bin vs bin '
          '%s: n=%d rho=%s (perm p %s)' % (lab, n_, f(rho, 2), f(p, 3)))
    if cmpb:
        diffs = [abs(b['fps'] - b['cmp']) for x in runs for b in x['fr']['bins'] if b['cmp'] is not None and b['fps']]
        w('- my bin fps vs Agent 8\'s %s stat_bins: %d bins compared, max |diff| %s fps' % (
            os.path.basename(a.cmp_json), len(diffs), f(max(diffs) if diffs else None, 3)))
    if phase:
        ne = {k: v for k, v in phase.items() if v}
        w('- Agent 8\'s phase.json slow_bins_s: %s (its criterion differs from the 0.85 x median rule here)' % (
            '; '.join('%s %s' % kv for kv in ne.items()) if ne else 'empty for all %d runs' % len(phase)))
    chk = [(x['name'], c) for x in runs for c in x['fr']['check']]
    w('- window fps/frames from perf.csv vs frames.json: %s' % ('; '.join('%s: %s' % c for c in chk) or
                                                             'all %d runs agree' % sum(1 for x in runs if x['fr'].get('fps'))))
    w('')

    # 5 correlations
    w('## 5. Spearman rank correlations across scored runs (window fps = frames / summed frame time)')
    w('')
    sets = [('scored', scored)]
    if any(not x['valid'] for x in scored):
        sets.append(('scored, valid timing only', [x for x in scored if x['valid']]))
    crow = []
    corr = {}
    for lab, sel in sets:
        fps = [x['fps'] for x in sel]
        for vname, fn in (('(a) window E<800 share', lambda x: x['slow'].get('win_low')),
                          ('(b) window mean e_eff_mhz', lambda x: x['slow'].get('e_mean')),
                          ('(c) window mean p_util_pct', lambda x: x['slow'].get('pu_mean')),
                          ('(d) run order (seq)', lambda x: float(x['seq'])),
                          ('extra: window mean p_eff_mhz', lambda x: x['slow'].get('p_mean')),
                          ('extra: window mean e_util_pct', lambda x: x['slow'].get('eu_mean')),
                          ('extra: onset s (never = 999)', lambda x: 999.0 if x['slow'].get('onset') is None else x['slow']['onset'])):
            n_, rho, p = spearman(fps, [fn(x) for x in sel])
            corr[(lab, vname)] = (n_, rho, p)
            crow.append([lab, vname, n_, f(rho, 3), f(p, 4)])
    table(w, ['run set', 'fps vs', 'n', 'rho', 'perm p (two-sided)'], crow)
    w('Scored runs by window fps (ascending):')
    w('')
    table(w, ['run', 'arm', 'seq', 'fps', 'win E<800 %', 'win E MHz', 'win P util %', 'win P MHz', 'run.json E MHz',
              'run.json P util %', 'onset s'],
          [[x['name'], x['arm'], x['seq'], f(x['fps'], 1), pc(x['slow'].get('win_low')), f(x['slow'].get('e_mean'), 0),
            f(x['slow'].get('pu_mean'), 1), f(x['slow'].get('p_mean'), 0), x['sysw'].get('e_eff_mhz_mean', '-'),
            x['sysw'].get('p_util_mean', '-'), f(x['slow'].get('onset'), 0)] for x in sorted(scored, key=lambda y: y['fps'])])

    if a.claim == 'w5':
        w('## 6. Agent 1\'s claim (SESSION2 18:34)')
        w('')
        w('Claim: the 3 slowest runs (base-r2 1817, d11t-r3 1821, s0-r2 1808) are the ones with P util 91-98.5 %% and '
          'the lowest E clocks (551-597 MHz); the fastest, base-r1 1757, had E at ~1174 MHz.')
        w('')
        sc = sorted(scored, key=lambda y: y['fps'])
        slow3, rest, fast = sc[:3], sc[3:], sc[-1]
        names3 = set(x['name'][:4] for x in slow3)
        w('- 3 slowest by window fps: %s -> %s the claimed set {1817, 1821, 1808}' % (
            ', '.join('%s %.1f fps' % (x['name'], x['fps']) for x in slow3),
            'same as' if names3 == {'1817', '1821', '1808'} else 'NOT'))
        w('- fastest: %s %.1f fps (claimed 1757-base-r1)' % (fast['name'], fast['fps']))
        for lab, km, kr in (('P util %', 'pu_mean', 'p_util_mean'), ('E MHz', 'e_mean', 'e_eff_mhz_mean')):
            w('- %s, 3 slowest: mine %s; run.json sys.window %s' % (
                lab, ', '.join('%s %s' % (x['name'][:4], f(x['slow'].get(km), 1)) for x in slow3),
                ', '.join('%s %s' % (x['name'][:4], x['sysw'].get(kr, '-')) for x in slow3)))
            vals_rest_m = [(x['slow'].get(km), x['name']) for x in rest if x['slow'].get(km) is not None]
            vals_rest_r = [(num(x['sysw'].get(kr)), x['name']) for x in rest if num(x['sysw'].get(kr)) is not None]
            if km == 'pu_mean':
                w('  - other %d scored runs: max P util mine %s (%s), run.json %s (%s)' % (
                    len(rest), f(max(vals_rest_m)[0], 1), max(vals_rest_m)[1], max(vals_rest_r)[0], max(vals_rest_r)[1]))
            else:
                w('  - other %d scored runs: min E MHz mine %s (%s), run.json %s (%s)' % (
                    len(rest), f(min(vals_rest_m)[0], 0), min(vals_rest_m)[1], min(vals_rest_r)[0], min(vals_rest_r)[1]))
        w('- fastest %s: E MHz mine %s, run.json %s; P util mine %s, run.json %s' % (
            fast['name'], f(fast['slow'].get('e_mean'), 0), fast['sysw'].get('e_eff_mhz_mean'),
            f(fast['slow'].get('pu_mean'), 1), fast['sysw'].get('p_util_mean')))
        pu_rank = sorted(scored, key=lambda y: -(y['slow'].get('pu_mean') or 0))
        e_rank = sorted(scored, key=lambda y: (y['slow'].get('e_mean') or 1e9))
        w('- top 4 by window P util (mine): %s' % ', '.join('%s %s' % (x['name'], f(x['slow'].get('pu_mean'), 1)) for x in pu_rank[:4]))
        w('- lowest 4 by window E MHz (mine): %s' % ', '.join('%s %s' % (x['name'], f(x['slow'].get('e_mean'), 0)) for x in e_rank[:4]))
        w('')

    text = '\n'.join(L) + '\n'
    with open(os.path.join(out, 'scan.md'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    # short console summary
    print('wrote %s' % os.path.join(out, 'scan.md'))
    print('proof deviations: %d; health deviations: %d; slow-state disagreements: %d; slow bins: %d' % (
        len(pdev), len(hdev), len(agree), len(fb)))
    for (lab, vname), (n_, rho, p) in corr.items():
        print('%s | %s | n=%d rho=%s p=%s' % (lab, vname, n_, f(rho, 3), f(p, 4)))
    return 0


if __name__ == '__main__':
    sys.exit(main())

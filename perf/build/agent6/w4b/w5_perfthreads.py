#!/usr/bin/env python3
"""w5_perfthreads.py - Agent 6, task #13 (W5 read-out support).  READ-ONLY over the matrix dir.

Per run (runs/<name>/):
  run.json      frame stats, sys window (P/E util + eff MHz), QPC-vs-epoch measure window
  headroom.json thread summary + GPU summary (util, clocks, power, temp, throttle samples)
  threads.csv   busy% per thread (normalised names: host-TID hex dropped, guest handle kept;
                a key thread may have handle aliases, e.g. X1A8 = F80001A8 or F80001AC)
  gpu.csv       per-sample NVML throttle-reason mask (0x20 = SW thermal slowdown), gr MHz, temp
  perf.csv      window rows chosen to match run.json frames.window (byte offsets / first_row),
                verified against run.json mean_ms + median_ms; per-frame means, per-second
                rates, a fixed-rate fit across runs (rate = k * fps + r), per-frame content
                constancy, and 10-s bins.

Question: do the slow runs differ in content/work (per-frame counters) or only in
speed/placement (same content, slower per frame; CPU/sys signals)?

v2 changes: thread aliases; fps = frames / window_s (perf.csv's fps column is the mean of
instantaneous fps, biased high); 5b fixed-rate fit; section 7 is now content constancy (the v1
decile decomposition is removed: functions_dispatched has a fixed per-second part, so its
per-frame mix follows the frame rate, not the scene); gpu.csv throttle reasons; SEP and Spearman
use the runs that have each metric (n printed); section 10 per-arm ranges.

Usage:
  python -B w5_perfthreads.py <matrix_dir> --out <report.txt> [--slow a,b,c]
Writes <report.txt> and <report.txt minus .txt>.json only.
"""
import argparse
import collections
import csv
import json
import math
import os
import re
import sys

ARM_RE = re.compile(r'^\d{4}-(cold-[A-Za-z0-9]+|[A-Za-z0-9]+)(?:-|$)')
HANDLE_RE = re.compile(r'^(.*?)\s*\((F[0-9A-Fa-f]{7})\)\s*$')
XTHREAD_RE = re.compile(r'^XThread[0-9A-Fa-f]+$')
HEXNAME_RE = re.compile(r'^0x[0-9A-Fa-f]+$')

RATE_COLS = ['draw_calls', 'vertices_processed', 'functions_dispatched', 'interrupt_dispatches',
             'xma_frames_decoded', 'command_buffer_stalls', 'critical_region_contentions',
             'texture_cache_hits', 'texture_cache_misses', 'pipeline_cache_hits', 'pipeline_cache_misses']
CONST_COLS = ['draw_calls', 'vertices_processed', 'texture_cache_hits', 'texture_cache_misses',
              'pipeline_cache_hits', 'pipeline_cache_misses', 'active_threads', 'interrupt_dispatches',
              'functions_dispatched']
FIT_NET = [('intr', 'interrupt_dispatches'), ('funcs', 'functions_dispatched')]
KEY_THREADS = [
    ('GPUCmd', ['GPU Commands (F8000018)']),
    ('Main', ['Main XThread (F800002C)']),
    ('X1A8', ['XThread (F80001A8)', 'XThread (F80001AC)']),
    ('TimerQ', ['rex::thread::TimerQueue']),
    ('X144', ['XThread (F8000144)']),
    ('unn1', ['<unnamed#1>']),
    ('VSync', ['GPU VSync (F800001C)']),
    ('X114', ['XThread (F8000114)']),
    ('X10C', ['XThread (F800010C)']),
    ('hex1', ['<0xhex#1>']),
    ('Audio', ['Audio Worker (F8000014)']),
    ('X070', ['XThread (F8000070)']),
    ('SDLAud', ['SDLAudioP*']),
    ('unn2', ['<unnamed#2>']),
]
DEFAULT_SLOW = '1808-s0-r2,1817-base-r2,1821-d11t-r3'
GPU_KEYS = ('util_mean', 'util_median', 'util_p90', 'util_max', 'mem_util_mean', 'clock_gr_mean',
            'clock_gr_min', 'power_w_mean', 'temp_max', 'throttle_power_samples', 'throttle_thermal_samples')
THROTTLE_BITS = ((0x1, 'GpuIdle'), (0x2, 'AppClk'), (0x4, 'SwPowerCap'), (0x8, 'HwSlowdown'),
                 (0x10, 'SyncBoost'), (0x20, 'SwThermal'), (0x40, 'HwThermal'), (0x80, 'HwPowerBrake'),
                 (0x100, 'DisplayClk'))
SPEED_KEYS = ('pf.frame_time_us', 'pf.fps')
FIXRATE_KEYS = ('pf.functions_dispatched', 'pf.interrupt_dispatches')
ARM_KEYS = [('f.mean_ms', '.3f'), ('f.median_ms', '.3f'), ('f.fps_true', '.1f'), ('cores_mean', '.2f'),
            ('thr.TimerQ', '.1f'), ('thr.GPUCmd', '.1f'), ('thr.Main', '.1f'), ('thr.X1A8', '.1f'),
            ('thr.X144', '.1f'), ('sys.p_util_mean', '.1f'), ('sys.e_eff_mhz_mean', '.0f'),
            ('pf.buffer_queue_depth', '.2f'), ('gpu.util_mean', '.1f'),
            ('gpu.throttle_thermal_samples', '.0f'), ('gpuc.gr_min', '.0f')]


def load_json(p):
    with open(p, 'r', encoding='utf-8-sig') as f:
        return json.load(f)


def g(d, *keys):
    for k in keys:
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


def num(v):
    try:
        if v is None or v == '':
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_int(v):
    s = ('' if v is None else str(v)).strip()
    if not s:
        return None
    try:
        return int(s, 16) if s.lower().startswith('0x') else int(float(s))
    except ValueError:
        return None


def hexv(v):
    return '?' if v is None else '0x%x' % v


def throttle_name(v):
    if v is None:
        return '?'
    if v == 0:
        return 'none'
    names = [nm for bit, nm in THROTTLE_BITS if v & bit]
    rest = v & ~sum(bit for bit, _ in THROTTLE_BITS)
    if rest:
        names.append('0x%x' % rest)
    return '+'.join(names)


def nearest_rank(sv, p):
    if not sv:
        return None
    return sv[max(0, math.ceil(p * len(sv)) - 1)]


def norm_thread(name):
    m = HANDLE_RE.match(name)
    if m:
        base, h = m.group(1).strip(), m.group(2).upper()
        if XTHREAD_RE.match(base):
            base = 'XThread'
        return '%s (%s)' % (base, h)
    if name == '':
        return '<unnamed>'
    if HEXNAME_RE.match(name):
        return '<0xhex>'
    return re.sub(r'\d+$', '*', name)


def read_threads(path):
    rows = []
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            rows.append((r.get('name') or '', num(r.get('busy_pct')) or 0.0,
                         num(r.get('cpu_s')) or 0.0, num(r.get('max_busy_pct'))))
    busy = {}
    ranked = {'<unnamed>': [], '<0xhex>': []}
    for name, b, c, mx in rows:
        k = norm_thread(name)
        if k in ranked:
            ranked[k].append((b, name))
            continue
        busy[k] = busy.get(k, 0.0) + b
    for k, lst in ranked.items():
        lst.sort(key=lambda t: -t[0])
        stem = k[1:-1]
        for i, (b, name) in enumerate(lst, 1):
            busy['<%s#%d>' % (stem, i)] = b
    total = sum(b for _, b, _, _ in rows)
    top = [(n, b) for n, b, _, _ in sorted(rows, key=lambda t: -t[1])[:8]]
    return busy, total, top, len(rows)


def read_gpu_csv(path):
    res = {'rows': 0, 'throttle': collections.Counter(), 'sw_thermal': 0, 'gr_min': None,
           'gr_min_throttled': None, 'temp_max': None, 't_first': None, 't_last': None,
           't_thr_first': None, 't_thr_last': None, 'cols': None}
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        rd = csv.DictReader(f)
        res['cols'] = rd.fieldnames
        for d in rd:
            res['rows'] += 1
            tv = parse_int(d.get('throttle'))
            res['throttle'][tv] += 1
            gr, tc, ts = num(d.get('gr_mhz')), num(d.get('temp_c')), num(d.get('t_s'))
            if ts is not None:
                if res['t_first'] is None:
                    res['t_first'] = ts
                res['t_last'] = ts
            if gr is not None:
                res['gr_min'] = gr if res['gr_min'] is None else min(res['gr_min'], gr)
            if tc is not None:
                res['temp_max'] = tc if res['temp_max'] is None else max(res['temp_max'], tc)
            if tv and tv & 0x20:
                res['sw_thermal'] += 1
                if gr is not None:
                    res['gr_min_throttled'] = gr if res['gr_min_throttled'] is None else min(
                        res['gr_min_throttled'], gr)
                if ts is not None:
                    if res['t_thr_first'] is None:
                        res['t_thr_first'] = ts
                    res['t_thr_last'] = ts
    return res


def perf_window(path, fr):
    w = fr.get('window') or {}
    first_row, nrows = w.get('first_row'), w.get('rows')
    fre, lre = w.get('first_row_end_offset'), w.get('last_row_end_offset')
    with open(path, 'rb') as f:
        data = f.read()
    parts = data.split(b'\n')
    header = parts[0]
    off = len(header) + 1
    ends, rows = [], []
    for ln in parts[1:]:
        off += len(ln) + 1
        if ln.strip() == b'':
            continue
        ends.append(off)
        rows.append(ln)
    cols = header.decode('utf-8-sig', 'replace').strip().split(',')
    info = {'header_bytes': len(header) + 1, 'rows_total': len(rows), 'first_row': first_row,
            'rows': nrows, 'want_mean_ms': num(fr.get('mean_ms')), 'want_median_ms': num(fr.get('median_ms'))}
    if not nrows or 'frame_time_us' not in cols:
        info['method'] = 'NO-WINDOW'
        return None, info
    fti = cols.index('frame_time_us')
    idx_by_end = {e: i for i, e in enumerate(ends)}
    cands = []
    if fre is not None:
        for nm, adj in (('end_after_lf', 0), ('end_at_lf', 1), ('end_at_cr', 2)):
            i = idx_by_end.get(fre + adj)
            if i is not None:
                cands.append((nm, i))
    if first_row is not None:
        cands += [('first_row_0based', first_row), ('first_row_1based', first_row - 1)]
    want_mean, want_med = info['want_mean_ms'], info['want_median_ms']
    chosen, tried = None, []
    for nm, i in cands:
        if i < 0 or i + nrows > len(rows):
            tried.append('%s@%d out-of-range' % (nm, i))
            continue
        ft = [float(r.decode('ascii').strip().split(',')[fti]) for r in rows[i:i + nrows]]
        mean = sum(ft) / len(ft) / 1000.0
        med = nearest_rank(sorted(ft), 0.5) / 1000.0
        ok = ((want_mean is None or abs(mean - want_mean) <= 0.0006) and
              (want_med is None or abs(med - want_med) <= 0.0006))
        tried.append('%s@%d mean %.4f med %.3f %s' % (nm, i, mean, med, 'MATCH' if ok else 'no'))
        if ok and chosen is None:
            chosen = (nm, i)
    info['tried'] = tried
    if chosen is None:
        info['method'] = 'NO-MATCH(fallback first_row)'
        chosen = ('fallback', first_row if first_row is not None else 0)
    else:
        info['method'] = chosen[0]
    i0 = chosen[1]
    if len(rows) >= nrows:
        i0 = max(0, min(i0, len(rows) - nrows))
    else:
        i0 = 0
    info['first_index'] = i0
    li = i0 + nrows - 1
    info['last_end'] = ends[li] if li < len(ends) else None
    info['last_end_ok'] = bool(lre is not None and info['last_end'] is not None and
                               (info['last_end'] - lre) in (0, 1, 2))
    win = rows[i0:i0 + nrows]
    ncol = len(cols)
    sums = [0.0] * ncol
    cidx = dict((c, cols.index(c)) for c in CONST_COLS if c in cols)
    counters = dict((c, collections.Counter()) for c in cidx)
    dci = cols.index('draw_calls') if 'draw_calls' in cols else None
    bins = {}
    cum, bad = 0.0, 0
    for ln in win:
        p = ln.decode('ascii').strip().split(',')
        if len(p) != ncol:
            bad += 1
            continue
        try:
            v = [float(x) for x in p]
        except ValueError:
            bad += 1
            continue
        for j in range(ncol):
            sums[j] += v[j]
        for c, j in cidx.items():
            counters[c][v[j]] += 1
        ft = v[fti]
        cum += ft / 1e6
        b = int(cum // 10.0)
        bb = bins.setdefault(b, [0, 0.0, 0.0])
        bb[0] += 1
        bb[1] += ft
        bb[2] += v[dci] if dci is not None else 0.0
    n = len(win) - bad
    info['bad_rows'] = bad
    info['n'] = n
    info['covered_s'] = cum
    means = dict((cols[j], sums[j] / n) for j in range(ncol)) if n else {}
    totals = dict((cols[j], sums[j]) for j in range(ncol))
    return {'means': means, 'totals': totals, 'counters': counters, 'bins': bins, 'cols': cols}, info


def collect(rd, r):
    m = r['m']
    rj = load_json(os.path.join(rd, 'run.json'))
    fr = rj.get('frames') or {}
    r['start'] = (rj.get('start') or '')[11:19]
    r['bin'] = os.path.basename((rj.get('bin_dir') or '').rstrip('\\/'))
    for k in ('frames', 'window_s', 'mean_ms', 'median_ms', 'p95_ms', 'p99_ms', 'p99_9_ms', 'max_ms',
              'share_lt_light'):
        m['f.' + k] = num(fr.get(k))
    if m.get('f.frames') and m.get('f.window_s'):
        m['f.fps_true'] = m['f.frames'] / m['f.window_s']
    m['cores_mean'] = num(rj.get('window_cpu_cores_mean'))
    m['cores_max'] = num(rj.get('window_cpu_cores_max'))
    sw = g(rj, 'sys', 'window') or {}
    for k in ('cpu_util_mean', 'eff_mhz_mean', 'eff_mhz_min', 'p_eff_mhz_mean', 'e_eff_mhz_mean',
              'p_util_mean', 'e_util_mean'):
        m['sys.' + k] = num(sw.get(k))
    qf = num(rj.get('qpc_frequency'))
    ms_, me_ = rj.get('measure_start') or {}, rj.get('measure_end') or {}
    if qf and ms_.get('qpc') is not None and me_.get('qpc') is not None:
        m['clk.qpc_s'] = (me_['qpc'] - ms_['qpc']) / qf
        m['clk.epoch_s'] = me_['epoch_s'] - ms_['epoch_s']
        m['clk.step_s'] = m['clk.epoch_s'] - m['clk.qpc_s']
    hp = os.path.join(rd, 'headroom.json')
    if os.path.exists(hp):
        hr = load_json(hp)
        for k in ('sum_busy_cores', 'headroom_pct', 'window_s', 'threads', 'named', 'top1_busy_pct'):
            m['hr.' + k] = num(hr.get(k))
        r['top1'] = hr.get('top1_name')
        gp = hr.get('gpu') or {}
        for k in GPU_KEYS:
            m['gpu.' + k] = num(gp.get(k))
        r['pstates'] = gp.get('pstates')
    else:
        r['notes'].append('no headroom.json')
    gc = os.path.join(rd, 'gpu.csv')
    if os.path.exists(gc):
        gi = read_gpu_csv(gc)
        r['gpu_csv'] = gi
        m['gpuc.rows'] = float(gi['rows'])
        m['gpuc.sw_thermal'] = float(gi['sw_thermal'])
        m['gpuc.gr_min'] = gi['gr_min']
        m['gpuc.temp_max'] = gi['temp_max']
    else:
        r['notes'].append('no gpu.csv')
    tp = os.path.join(rd, 'threads.csv')
    if os.path.exists(tp):
        busy, total, top, nthr = read_threads(tp)
        r['threads_busy'] = busy
        r['threads_top'] = top
        m['thr.total_cores'] = total / 100.0
        m['thr.count'] = float(nthr)
        for ab, keys_ in KEY_THREADS:
            val = None
            for i, key in enumerate(keys_):
                if key in busy:
                    val = busy[key]
                    if i:
                        r['aliases'].append('%s<-%s' % (ab, key))
                    break
            m['thr.' + ab] = val
    else:
        r['notes'].append('no threads.csv')
    pp = os.path.join(rd, 'perf.csv')
    if os.path.exists(pp):
        pw, info = perf_window(pp, fr)
        r['perf_info'] = info
        if pw:
            r['perf'] = pw
            ws = num(fr.get('window_s')) or info.get('covered_s')
            for c, v in pw['means'].items():
                m['pf.' + c] = v
            for c in RATE_COLS:
                if c in pw['totals'] and ws:
                    m['ps.' + c] = pw['totals'][c] / ws
    else:
        r['notes'].append('no perf.csv')


def counter_stats(c):
    n = float(sum(c.values()))
    if not n:
        return None
    top = c.most_common(3)
    return {'n': int(n), 'distinct': len(c), 'min': min(c), 'max': max(c),
            'mean': sum(v * k for v, k in c.items()) / n,
            'mode': top[0][0], 'mode_share': top[0][1] / n,
            'top': [(v, k / n) for v, k in top]}


def ols(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return None
    k = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    r0 = my - k * mx
    res = [y - (k * x + r0) for x, y in zip(xs, ys)]
    syy = sum((y - my) ** 2 for y in ys)
    r2 = (1.0 - sum(e * e for e in res) / syy) if syy > 0 else None
    return {'n': n, 'k': k, 'r': r0, 'r2': r2, 'res': res, 'maxres': max(abs(e) for e in res)}


def ranks(v):
    idx = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and v[idx[j + 1]] == v[idx[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            r[idx[k]] = avg
        i = j + 1
    return r


def pearson(x, y):
    n = len(x)
    if n < 3:
        return None
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx == 0 or syy == 0:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sxx * syy)


def spearman(x, y):
    return pearson(ranks(x), ranks(y))


def kind(k):
    if k.startswith('f.') or k in SPEED_KEYS:
        return 'speed'
    if k.startswith('ps.'):
        return 'rate'
    if k in FIXRATE_KEYS:
        return 'fixrate'
    return ''


def fmtv(v, spec):
    if v is None:
        return '-'
    if isinstance(v, str):
        return v
    try:
        return format(v, spec)
    except (TypeError, ValueError):
        return str(v)


def table(out, runs, cols, title, notes=(), end_blank=True):
    out.append(title)
    out.append('  %-17s %-9s %-8s' % ('run', 'arm', 'start') + ''.join(' %*s' % (w, h) for h, k, spec, w in cols))
    for r in runs:
        line = '  %-17s %-9s %-8s' % (r['name'], r['arm'], r.get('start', ''))
        for h, k, spec, w in cols:
            line += ' %*s' % (w, fmtv(r['m'].get(k), spec))
        if r['slow']:
            line += '  <SLOW'
        out.append(line)
    for nt in notes:
        out.append('  ' + nt)
    if end_blank:
        out.append('')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('matrix')
    ap.add_argument('--out', required=True)
    ap.add_argument('--slow', default=DEFAULT_SLOW)
    a = ap.parse_args()
    runs_dir = os.path.join(a.matrix, 'runs')
    names = sorted(d for d in os.listdir(runs_dir)
                   if os.path.isdir(os.path.join(runs_dir, d)) and ARM_RE.match(d))
    slow = set(s.strip() for s in a.slow.split(',') if s.strip())
    runs = []
    for nm in names:
        r = {'name': nm, 'arm': ARM_RE.match(nm).group(1), 'slow': nm in slow, 'm': {}, 'notes': [],
             'aliases': []}
        try:
            collect(os.path.join(runs_dir, nm), r)
        except Exception as e:  # report, keep going
            r['notes'].append('ERROR %s: %s' % (type(e).__name__, e))
        runs.append(r)
    missing_slow = sorted(slow - set(names))
    slow_runs = [r for r in runs if r['slow']]

    out = []
    out.append('W5 perf/threads/gpu/sys table v2 (Agent 6, task #13): %s' % os.path.abspath(a.matrix))
    out.append('runs %d; slow = %s%s' % (len(runs), ', '.join(sorted(slow)),
                                         ('; MISSING slow: %s' % missing_slow) if missing_slow else ''))
    out.append('read-only; sources per run: run.json, headroom.json, threads.csv, gpu.csv, perf.csv (window '
               'rows matched to run.json frames.window, verified vs run.json mean_ms/median_ms)')
    for r in runs:
        if r['notes']:
            out.append('  NOTE %s: %s' % (r['name'], '; '.join(r['notes'])))
    out.append('')

    out.append('0. perf.csv window self-check (method = which window rule reproduced run.json mean+median)')
    nmatch = 0
    for r in runs:
        pi = r.get('perf_info') or {}
        meth = pi.get('method', '-')
        if meth and not meth.startswith('NO-') and meth != '-':
            nmatch += 1
        pm = r['m']
        out.append('  %-17s method=%s first_index=%s first_row=%s rows=%s n=%s bad=%s last_end_ok=%s '
                   'mean %s vs run.json %s | median vs %s | covered_s=%s' % (
                       r['name'], meth, pi.get('first_index'), pi.get('first_row'), pi.get('rows'),
                       pi.get('n'), pi.get('bad_rows'), pi.get('last_end_ok'),
                       fmtv(pm.get('pf.frame_time_us') / 1000.0 if pm.get('pf.frame_time_us') is not None else None,
                            '.4f'),
                       fmtv(pi.get('want_mean_ms'), '.4f'), fmtv(pi.get('want_median_ms'), '.3f'),
                       fmtv(pi.get('covered_s'), '.3f')))
        if meth.startswith('NO-'):
            out.append('      tried: %s' % ' | '.join(pi.get('tried') or []))
    out.append('  windows reproduced: %d/%d' % (nmatch, len(runs)))
    out.append('')

    table(out, runs, [
        ('frames', 'f.frames', '.0f', 6), ('fps', 'f.fps_true', '.1f', 6), ('mean', 'f.mean_ms', '.3f', 6),
        ('med', 'f.median_ms', '.3f', 6), ('p99', 'f.p99_ms', '.3f', 6), ('max', 'f.max_ms', '.2f', 6),
        ('lt4.5', 'f.share_lt_light', '.3f', 6), ('cores', 'cores_mean', '.2f', 5),
        ('thrC', 'thr.total_cores', '.2f', 5), ('hrC', 'hr.sum_busy_cores', '.2f', 5),
        ('util', 'sys.cpu_util_mean', '.1f', 5), ('Putil', 'sys.p_util_mean', '.1f', 5),
        ('Eutil', 'sys.e_util_mean', '.1f', 5), ('effMHz', 'sys.eff_mhz_mean', '.0f', 6),
        ('P_MHz', 'sys.p_eff_mhz_mean', '.0f', 5), ('E_MHz', 'sys.e_eff_mhz_mean', '.0f', 5),
        ('clkstep', 'clk.step_s', '.3f', 7),
    ], '1. frames + CPU/sys window (run.json; fps = frames / window_s; thrC = sum threads.csv busy; '
       'hrC = headroom sum_busy_cores)')

    table(out, runs, [
        ('util', 'gpu.util_mean', '.1f', 5), ('med', 'gpu.util_median', '.1f', 5),
        ('p90', 'gpu.util_p90', '.1f', 5), ('max', 'gpu.util_max', '.0f', 4),
        ('memU', 'gpu.mem_util_mean', '.1f', 5), ('grMHz', 'gpu.clock_gr_mean', '.0f', 5),
        ('grMin', 'gpu.clock_gr_min', '.0f', 5), ('W', 'gpu.power_w_mean', '.2f', 6),
        ('tmax', 'gpu.temp_max', '.0f', 4), ('thrP', 'gpu.throttle_power_samples', '.0f', 4),
        ('thrT', 'gpu.throttle_thermal_samples', '.0f', 4),
    ], '2. GPU (headroom.json gpu, sampled over the measure window)', end_blank=False)
    for r in runs:
        if r.get('pstates') and r['pstates'] != 'P0 x50':
            out.append('  pstates %s: %s' % (r['name'], r['pstates']))
    out.append('  gpu.csv per run: rows | throttle mask value=count (NVML reasons) | min gr MHz all / SW-thermal '
               'rows | max temp | t_s range | SW-thermal t_s first..last')
    agree = nb = 0
    for r in runs:
        gi = r.get('gpu_csv')
        if not gi:
            out.append('    %-17s %-8s -' % (r['name'], r.get('start', '')))
            continue
        tv = ', '.join('%s=%d (%s)' % (hexv(v), c, throttle_name(v))
                       for v, c in sorted(gi['throttle'].items(), key=lambda t: (t[0] is None, t[0] or 0)))
        out.append('    %-17s %-8s rows %d | %s | grMin %s / %s | tmax %s | t %s..%s | swT %s..%s%s' % (
            r['name'], r.get('start', ''), gi['rows'], tv, fmtv(gi['gr_min'], '.0f'),
            fmtv(gi['gr_min_throttled'], '.0f'), fmtv(gi['temp_max'], '.0f'), fmtv(gi['t_first'], '.1f'),
            fmtv(gi['t_last'], '.1f'), fmtv(gi['t_thr_first'], '.1f'), fmtv(gi['t_thr_last'], '.1f'),
            '  <SLOW' if r['slow'] else ''))
        hv = r['m'].get('gpu.throttle_thermal_samples')
        if hv is not None:
            nb += 1
            agree += 1 if gi['sw_thermal'] == hv else 0
    out.append('  gpu.csv SW-thermal rows == headroom.json throttle_thermal_samples: %d/%d runs' % (agree, nb))
    out.append('')

    table(out, runs, [(ab, 'thr.' + ab, '.1f', 6) for ab, keys_ in KEY_THREADS] +
          [('nthr', 'thr.count', '.0f', 4)],
          '3. thread busy% (threads.csv). keys: ' +
          '; '.join('%s=%s' % (ab, '|'.join(keys_)) for ab, keys_ in KEY_THREADS), end_blank=False)
    al = ['%s %s' % (r['name'], ', '.join(r['aliases'])) for r in runs if r.get('aliases')]
    out.append('  handle aliases used: %s' % ('; '.join(al) if al else 'none'))
    keyset = set(k for _, ks in KEY_THREADS for k in ks)
    others = {}
    for r in runs:
        for k, b in (r.get('threads_busy') or {}).items():
            if k not in keyset and b >= 5.0:
                others.setdefault(k, {})[r['name']] = b
    out.append('  other threads with busy >= 5%% in any run: %d' % len(others))
    for k in sorted(others):
        out.append('    %-34s %s' % (k, ', '.join('%s=%.1f' % (n, b) for n, b in sorted(others[k].items()))))
    out.append('  top-8 raw thread names per run (name busy%):')
    for r in runs:
        out.append('    %-17s %s' % (r['name'], '; '.join('%s %.1f' % (n or '<unnamed>', b)
                                                        for n, b in (r.get('threads_top') or []))))
    out.append('')

    table(out, runs, [
        ('draw', 'pf.draw_calls', '.1f', 6), ('verts', 'pf.vertices_processed', '.0f', 6),
        ('funcs', 'pf.functions_dispatched', '.2f', 6), ('intr', 'pf.interrupt_dispatches', '.2f', 6),
        ('actThr', 'pf.active_threads', '.2f', 6), ('bufQ', 'pf.buffer_queue_depth', '.2f', 5),
        ('apcQ', 'pf.apc_queue_depth', '.3f', 5), ('crit', 'pf.critical_region_contentions', '.3f', 6),
        ('cbStl', 'pf.command_buffer_stalls', '.3f', 6), ('xma', 'pf.xma_frames_decoded', '.3f', 6),
        ('audLat', 'pf.audio_frame_latency_us', '.0f', 6), ('texH', 'pf.texture_cache_hits', '.2f', 6),
        ('texM', 'pf.texture_cache_misses', '.3f', 6), ('pipH', 'pf.pipeline_cache_hits', '.2f', 6),
        ('pipM', 'pf.pipeline_cache_misses', '.4f', 7), ('fpsI', 'pf.fps', '.1f', 6),
    ], '4. perf.csv window, per-frame means',
        notes=('fpsI = mean of perf.csv per-frame instantaneous fps (biased high); use fps in section 1.',
               'funcs and intr per frame include a fixed per-second part, so they rise when fps falls; see 5b.'))
    table(out, runs, [
        ('draw/s', 'ps.draw_calls', '.0f', 7), ('verts/s', 'ps.vertices_processed', '.0f', 8),
        ('funcs/s', 'ps.functions_dispatched', '.0f', 7), ('intr/s', 'ps.interrupt_dispatches', '.0f', 7),
        ('xma/s', 'ps.xma_frames_decoded', '.1f', 6), ('crit/s', 'ps.critical_region_contentions', '.2f', 6),
        ('cbStl/s', 'ps.command_buffer_stalls', '.2f', 7), ('texM/s', 'ps.texture_cache_misses', '.2f', 6),
        ('pipM/s', 'ps.pipeline_cache_misses', '.3f', 6),
    ], '5. perf.csv window, per-second rates (window totals / run.json frames.window_s)')

    fits = {}
    out.append('5b. fixed-rate fit across runs: ps.<col> = k * fps + r  (fps = run.json frames / window_s)')
    out.append('    k = part that scales with frames (per frame); r = per-second part independent of the frame rate')
    out.append('    %-28s %3s %11s %10s %10s %9s' % ('col', 'n', 'k', 'r', 'R2', 'max|res|'))
    for col in RATE_COLS:
        pts = [(r['m'].get('f.fps_true'), r['m'].get('ps.' + col), r['name']) for r in runs]
        pts = [p for p in pts if p[0] is not None and p[1] is not None]
        ft = ols([p[0] for p in pts], [p[1] for p in pts])
        if ft is None:
            out.append('    %-28s %3d   (no fit)' % (col, len(pts)))
            continue
        ft['res_by_run'] = dict((p[2], e) for p, e in zip(pts, ft['res']))
        fits[col] = ft
        out.append('    %-28s %3d %11.4f %10.2f %10s %9.3f' % (col, ft['n'], ft['k'], ft['r'],
                                                              fmtv(ft['r2'], '.6f'), ft['maxres']))
    out.append('    per run: gross/f = perf.csv per-frame mean; net/f = (ps - r) / fps; res/s = ps - fit; '
               'f-i/s = funcs/s - intr/s')
    hdr = '    %-17s %-9s %7s' % ('run', 'arm', 'fps')
    for ab, col in FIT_NET:
        hdr += ' | %-5s %7s %7s %7s' % (ab, 'gross/f', 'net/f', 'res/s')
    hdr += ' | %7s' % 'f-i/s'
    out.append(hdr)
    for r in runs:
        fps = r['m'].get('f.fps_true')
        line = '    %-17s %-9s %7s' % (r['name'], r['arm'], fmtv(fps, '.1f'))
        for ab, col in FIT_NET:
            ft = fits.get(col)
            ps = r['m'].get('ps.' + col)
            gross = r['m'].get('pf.' + col)
            net = (ps - ft['r']) / fps if (ft and ps is not None and fps) else None
            res = ft['res_by_run'].get(r['name']) if ft else None
            line += ' | %-5s %7s %7s %7s' % (ab, fmtv(gross, '.3f'), fmtv(net, '.3f'), fmtv(res, '+.2f'))
        fi = None
        if r['m'].get('ps.functions_dispatched') is not None and r['m'].get('ps.interrupt_dispatches') is not None:
            fi = r['m']['ps.functions_dispatched'] - r['m']['ps.interrupt_dispatches']
        line += ' | %7s' % fmtv(fi, '.1f')
        if r['slow']:
            line += '  <SLOW'
        out.append(line)
    out.append('')

    out.append('6. 10-s bins inside the window (by cumulative frame time): mean frame ms | mean draw calls | frames '
               '(the last bin holds the remainder of the window)')
    for r in runs:
        bins = (r.get('perf') or {}).get('bins') or {}
        ks = sorted(bins)
        out.append('  %-17s ms [%s] | draw [%s] | frames [%s]%s' % (
            r['name'],
            ', '.join('%.3f' % (bins[k][1] / bins[k][0] / 1000.0) for k in ks),
            ', '.join('%.1f' % (bins[k][2] / bins[k][0]) for k in ks),
            ', '.join('%d' % bins[k][0] for k in ks),
            '  <SLOW' if r['slow'] else ''))
    out.append('')

    content = {}
    out.append('7. per-frame content constancy in the window (perf.csv per-frame counters; replaces the v1 '
               'decile decomposition)')
    for col in CONST_COLS:
        per = []
        for r in runs:
            c = ((r.get('perf') or {}).get('counters') or {}).get(col)
            st = counter_stats(c) if c else None
            if st:
                per.append((r, st))
                content.setdefault(col, {})[r['name']] = st
        if not per:
            out.append('  %-22s no data' % col)
            continue
        if all(st['distinct'] == 1 for _, st in per) and len(set(st['min'] for _, st in per)) == 1:
            out.append('  %-22s all %d runs: every window frame = %g' % (col, len(per), per[0][1]['min']))
            continue
        out.append('  %-22s per run: distinct, min, max, mean, top-3 values (share)' % col)
        for r, st in per:
            out.append('    %-17s %5d %6g %6g %9.3f  %s%s' % (
                r['name'], st['distinct'], st['min'], st['max'], st['mean'],
                ', '.join('%g %.1f%%' % (v, s * 100) for v, s in st['top']),
                '  <SLOW' if r['slow'] else ''))
    out.append('')

    all_keys = sorted(set(k for r in runs for k, v in r['m'].items() if v is not None))
    early = set(n for n in names if n.startswith('1756-') or n.startswith('1757-'))

    def sep_rows(exclude):
        res = []
        for k in all_keys:
            if kind(k) == 'speed':
                continue
            sv = [r['m'].get(k) for r in slow_runs]
            if not sv or any(v is None for v in sv):
                continue
            rv = [r['m'][k] for r in runs
                  if not r['slow'] and r['name'] not in exclude and r['m'].get(k) is not None]
            if len(rv) < 5:
                continue
            lo_s, hi_s, lo_r, hi_r = min(sv), max(sv), min(rv), max(rv)
            flag = 'SEP-HIGH' if lo_s > hi_r else ('SEP-LOW' if hi_s < lo_r else '')
            mr = sum(rv) / len(rv)
            sd = math.sqrt(sum((v - mr) ** 2 for v in rv) / (len(rv) - 1))
            z = ((sum(sv) / len(sv)) - mr) / sd if sd > 0 else None
            res.append((k, flag, sv, lo_r, hi_r, z, len(rv)))
        res.sort(key=lambda t: (t[1] == '', -(abs(t[5]) if t[5] is not None else 0)))
        return res

    sep_json = {}
    for tag, title, excl in (('all', 'all other runs', set()),
                             ('noearly', 'other runs without the early runs (%s)' % ', '.join(sorted(early)),
                              early)):
        rows = sep_rows(excl)
        out.append('8. slow runs vs %s: SEP = every slow run above/below every other run that has the metric; '
                   'z = (mean slow - mean rest) / sd rest; n = other runs with the metric' % title)
        nsep = [t for t in rows if t[1]]
        out.append('   separating metrics: %d of %d (rate/fixrate-derived: %d); speed-identity metrics (f.*, '
                   'pf.frame_time_us, pf.fps) omitted' % (len(nsep), len(rows),
                                                          sum(1 for t in nsep if kind(t[0]))))
        for k, flag, sv, lo_r, hi_r, z, nr in rows[:50]:
            out.append('   %-9s %-7s %-32s slow [%s] rest %s..%s n=%d z %s' % (
                flag or '-', kind(k) or '-', k, ', '.join(fmtv(v, '.4g') for v in sv), fmtv(lo_r, '.4g'),
                fmtv(hi_r, '.4g'), nr, fmtv(z, '+.2f')))
        sep_json[tag] = [{'metric': k, 'flag': flag, 'slow': sv, 'rest_lo': lo_r, 'rest_hi': hi_r, 'z': z, 'n': nr}
                         for k, flag, sv, lo_r, hi_r, z, nr in rows]
        out.append('')

    warm = [r for r in runs if not r['arm'].startswith('cold')]

    def rho(group, k, fk):
        pts = [(r['m'][k], r['m'][fk]) for r in group
               if r['m'].get(k) is not None and r['m'].get(fk) is not None]
        if len(pts) < 8:
            return None, len(pts)
        return spearman([p[0] for p in pts], [p[1] for p in pts]), len(pts)

    corr = []
    for k in all_keys:
        if kind(k) == 'speed':
            continue
        ra, na = rho(runs, k, 'f.median_ms')
        rw, nw = rho(warm, k, 'f.median_ms')
        rwm, _ = rho(warm, k, 'f.mean_ms')
        corr.append((k, ra, rw, rwm, na, nw))
    corr.sort(key=lambda t: -(abs(t[2]) if t[2] is not None else 0))
    out.append('9. Spearman rho across runs vs frame median / mean (W = without cold-base), over the runs that have '
               'the metric (n / nW)')
    out.append('   %-32s %-7s %8s %8s %9s %6s' % ('metric', 'kind', 'rho_med', 'rho_medW', 'rho_meanW', 'n/nW'))
    for k, ra, rw, rwm, na, nw in corr[:45]:
        out.append('   %-32s %-7s %8s %8s %9s %6s' % (k, kind(k) or '-', fmtv(ra, '+.2f'), fmtv(rw, '+.2f'),
                                                     fmtv(rwm, '+.2f'), '%d/%d' % (na, nw)))
    out.append('')

    arms = []
    for r in runs:
        if r['arm'] not in arms:
            arms.append(r['arm'])
    out.append('10. per-arm ranges: min..max over the arm\'s runs; then the arm mean, with (mean without the slow '
               'run) where the arm has one')
    hdr = '  %-30s' % 'metric' + ''.join(' %-18s' % ('%s(%d)' % (am, sum(1 for r in runs if r['arm'] == am)))
                                         for am in arms)
    out.append(hdr)
    arm_json = {}
    for k, spec in ARM_KEYS:
        line = '  %-30s' % k
        for am in arms:
            vs = [r['m'][k] for r in runs if r['arm'] == am and r['m'].get(k) is not None]
            if not vs:
                cell = '-'
            elif len(vs) == 1:
                cell = fmtv(vs[0], spec)
            else:
                cell = '%s..%s' % (fmtv(min(vs), spec), fmtv(max(vs), spec))
            line += ' %-18s' % cell
        out.append(line)
    out.append('  means:')
    for k, spec in ARM_KEYS:
        line = '  %-30s' % k
        for am in arms:
            rr = [r for r in runs if r['arm'] == am and r['m'].get(k) is not None]
            if not rr:
                line += ' %-18s' % '-'
                continue
            vals = [r['m'][k] for r in rr]
            mean = sum(vals) / len(vals)
            fast = [r['m'][k] for r in rr if not r['slow']]
            cell = fmtv(mean, spec)
            mfast = None
            if fast and len(fast) != len(rr):
                mfast = sum(fast) / len(fast)
                cell += ' (%s)' % fmtv(mfast, spec)
            arm_json.setdefault(k, {})[am] = {'n': len(vals), 'min': min(vals), 'max': max(vals), 'mean': mean,
                                              'mean_without_slow': mfast}
            line += ' %-18s' % cell
        out.append(line)
    out.append('')

    text = '\n'.join(out) + '\n'
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    jpath = (a.out[:-4] if a.out.lower().endswith('.txt') else a.out) + '.json'

    def gpu_json(gi):
        if not gi:
            return None
        d = dict((k, v) for k, v in gi.items() if k != 'throttle')
        d['throttle'] = dict((hexv(v), c) for v, c in gi['throttle'].items())
        return d

    dump = {
        'version': 2, 'matrix': os.path.abspath(a.matrix), 'slow': sorted(slow),
        'runs': [dict((k, r.get(k)) for k in ('name', 'arm', 'start', 'bin', 'slow', 'm', 'perf_info',
                                              'threads_top', 'pstates', 'notes', 'top1', 'aliases'))
                 for r in runs],
        'gpu_csv': dict((r['name'], gpu_json(r.get('gpu_csv'))) for r in runs),
        'fits': dict((c, dict((k, v) for k, v in ft.items() if k != 'res')) for c, ft in fits.items()),
        'content': content,
        'sep': sep_json,
        'arms': arm_json,
    }
    with open(jpath, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(dump, f, indent=1, default=str)
    print('wrote %s (%d lines) and %s; windows reproduced %d/%d' % (a.out, len(out), jpath, nmatch, len(runs)))
    return 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Checker B, task #13 (W5 perf read-out): B6 spot-check (all 16 runs computed, 1817-base-r2 / 1825-base-r3 /
1821-d11t-r3 highlighted), B7 fixed-rate fit, B8 separation claims, plus B4x (frames between the Toypad B1 challenges).
Independent code, stdlib only. Reads build/agent8/matrix/20261122-1756/runs/<run>/{perf.csv,run.json,threads.csv,
gpu.csv,sys.csv,game.log} read-only. Output: perfcheck-out.txt next to this file.

perf.csv window: data rows [first_row, first_row + rows) with run.json frames.window.first_row (0-based data-row
index after the header) and frames.window.rows. Percentiles: nearest rank, sorted[ceil(p*n)-1].
"""
import sys
sys.dont_write_bytecode = True
import calendar
import csv
import datetime
import json
import math
import os
import re
import traceback
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
RUNS_DIR = os.path.join(ROOT, 'build', 'agent8', 'matrix', '20261122-1756', 'runs')
OUT = os.path.join(HERE, 'perfcheck-out.txt')

RUNS = ['1756-cold-base', '1757-base-r1', '1800-s0-r1', '1802-d11-r1', '1804-d11t-r1', '1806-d11p-r1',
        '1808-s0-r2', '1810-d11-r2', '1813-d11t-r2', '1815-d11p-r2', '1817-base-r2', '1819-d11-r3',
        '1821-d11t-r3', '1823-d11p-r3', '1825-base-r3', '1827-s0-r3']
SLOW = ('1808-s0-r2', '1817-base-r2', '1821-d11t-r3')
SPOT = ('1817-base-r2', '1825-base-r3', '1821-d11t-r3')
NEED = ['frame_time_us', 'buffer_queue_depth', 'functions_dispatched', 'interrupt_dispatches', 'draw_calls',
        'vertices_processed', 'active_threads']
HDR = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\] \[([a-z]+)\] \[([^\]]*)\] (?:\[t(\d+)\] )?(.*)$')

O = []


def w(s=''):
    O.append(s)


def arm_of(r):
    tag = r.split('-', 1)[1]
    return 'cold' if tag == 'cold-base' else tag.rsplit('-', 1)[0]


def short(r):
    return r.split('-', 1)[1]


def naive_secs(s):
    dt = datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f')
    return calendar.timegm(dt.timetuple()) + dt.microsecond / 1e6


def load_json(r):
    with open(os.path.join(RUNS_DIR, r, 'run.json'), 'r', encoding='utf-8-sig') as fh:
        return json.load(fh)


def load_perf(r):
    data = {c: [] for c in NEED}
    bad = blank = 0
    with open(os.path.join(RUNS_DIR, r, 'perf.csv'), 'r', newline='', encoding='utf-8', errors='replace') as fh:
        rd = csv.reader(fh)
        hdr = [h.strip() for h in next(rd)]
        idx = {h: i for i, h in enumerate(hdr)}
        for row in rd:
            if not row:
                blank += 1
                continue
            ok = len(row) == len(hdr)
            for c in NEED:
                v = None
                if ok:
                    try:
                        v = int(row[idx[c]])
                    except ValueError:
                        ok = False
                data[c].append(v)
            if not ok:
                bad += 1
    return hdr, data, bad, blank


def nr(srt, p):
    return srt[max(0, math.ceil(p * len(srt)) - 1)]


def wstats(ft, first, n):
    win = ft[first:first + n]
    if len(win) != n or any(v is None for v in win):
        return None
    srt = sorted(win)
    return dict(mean_ms=sum(win) / n / 1000.0, median_ms=nr(srt, 0.5) / 1000.0, p95_ms=nr(srt, 0.95) / 1000.0,
                p99_ms=nr(srt, 0.99) / 1000.0, p99_9_ms=nr(srt, 0.999) / 1000.0, min_ms=srt[0] / 1000.0,
                max_ms=srt[-1] / 1000.0, sum_s=sum(win) / 1e6)


def eq(a, b, dp):
    return b is not None and a is not None and abs(round(a, dp) - b) < 10 ** (-dp) / 2 + 1e-9


def mean(xs):
    return sum(xs) / len(xs) if xs else float('nan')


def read_csv_dicts(path):
    with open(path, 'r', newline='', encoding='utf-8-sig') as fh:
        return list(csv.DictReader(fh))


def thread_metrics(r):
    p = os.path.join(RUNS_DIR, r, 'threads.csv')
    if not os.path.exists(p):
        return None
    t = read_csv_dicts(p)
    for x in t:
        x['busy'] = float(x['busy_pct'])

    def pick(pred):
        return [(x['name'], x['busy']) for x in t if pred(x['name'])]
    res = dict(
        gpucmd=pick(lambda n: n == 'GPU Commands (F8000018)'),
        main=pick(lambda n: n == 'Main XThread (F800002C)'),
        x1a8=pick(lambda n: n.endswith('(F80001A8)')),
        x1ac=pick(lambda n: n.endswith('(F80001AC)')),
        timerq=pick(lambda n: n == 'rex::thread::TimerQueue'),
        x144=pick(lambda n: n.endswith('(F8000144)')),
        top=sorted(((x['busy'], x['name']) for x in t), reverse=True)[:7],
        n=len(t))
    return res


def one(lst):
    return lst[0][1] if len(lst) == 1 else (None if not lst else ('MULTI', lst))


def gpu_metrics(r):
    p = os.path.join(RUNS_DIR, r, 'gpu.csv')
    if not os.path.exists(p):
        return None
    g = read_csv_dicts(p)
    c = Counter(x['throttle'].strip() for x in g)
    t20 = [float(x['t_s']) for x in g if x['throttle'].strip() == '0x20']
    return dict(rows=len(g), counts=dict(c), n20=len(t20), t20=(min(t20), max(t20)) if t20 else None)


def sys_window(r, j):
    s = j.get('sys') or {}
    ws, we = s.get('window_start_epoch'), s.get('window_end_epoch')
    rows = read_csv_dicts(os.path.join(RUNS_DIR, r, 'sys.csv'))
    win = [x for x in rows if ws <= float(x['epoch_s']) <= we]
    pu = [float(x['p_util_pct']) for x in win if x['p_util_pct'] not in ('', None)]
    ee = [float(x['e_eff_mhz']) for x in win if x['e_eff_mhz'] not in ('', None)]
    return len(win), mean(pu), mean(ee)


def b1_epochs(r, j):
    """Epochs of the Toypad B1 challenge writes in game.log (log time -> epoch with the run.json wall/epoch offset)."""
    ps = j.get('process_start_mark') or j['measure_start']
    off = ps['epoch_s'] - naive_secs(ps['wall'])
    res = []
    with open(os.path.join(RUNS_DIR, r, 'game.log'), 'rb') as fh:
        for ln in fh.read().decode('utf-8', errors='replace').split('\n'):
            m = HDR.match(ln.rstrip('\r'))
            if m and m.group(5).startswith('Toypad[Write]'):
                b = m.group(5).split()
                if len(b) > 5 and b[5] == 'B1':
                    res.append(naive_secs(m.group(1)) + off)
    return res


def row_at(ft, first, ms_epoch, T):
    delta = T - ms_epoch
    acc = 0.0
    i = first
    if delta >= 0:
        while i < len(ft) and acc < delta:
            acc += (ft[i] or 0) / 1e6
            i += 1
        return i
    while i > 0 and acc < -delta:
        i -= 1
        acc += (ft[i] or 0) / 1e6
    return i


def ols(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    k = sxy / sxx
    c = my - k * mx
    res = [b - (k * a + c) for a, b in zip(x, y)]
    sst = sum((b - my) ** 2 for b in y)
    r2 = 1 - sum(e * e for e in res) / sst
    return k, c, r2, max(abs(e) for e in res), res


def main():
    w('checker B perfcheck.py: %s' % datetime.datetime.now().isoformat(timespec='seconds'))
    D = {}
    for r in RUNS:
        j = load_json(r)
        hdr, data, bad, blank = load_perf(r)
        fr = j['frames']
        win = fr['window']
        first, n = win['first_row'], win['rows']
        ft = data['frame_time_us']
        st = {o: wstats(ft, first + o, n) for o in (-1, 0, 1)}
        sl = slice(first, first + n)
        tot = {c: sum(data[c][sl]) for c in ('buffer_queue_depth', 'functions_dispatched', 'interrupt_dispatches')}
        const = {c: Counter(data[c][sl]) for c in ('draw_calls', 'vertices_processed', 'active_threads')}
        viol = {c: sum(v for k, v in const[c].items() if k != want)
                for c, want in (('draw_calls', 226), ('vertices_processed', 1022), ('active_threads', 30))}
        sw = sys_window(r, j)
        D[r] = dict(j=j, hdr=hdr, nrows=len(ft), bad=bad, blank=blank, first=first, n=n, st=st, tot=tot, const=const,
                    viol=viol, window_s=fr['window_s'], frames=fr['frames'], fps=n / fr['window_s'],
                    thr=thread_metrics(r), gpu=gpu_metrics(r), sysw=sw,
                    putil=j['sys']['window'].get('p_util_mean'), emhz=j['sys']['window'].get('e_eff_mhz_mean'),
                    sysrows=j['sys']['window'].get('rows'), ft=ft, b1=b1_epochs(r, j))

    w()
    w('== B6. perf.csv window recomputation (all 16 runs; * = the 3 spot-check runs)')
    w('%-16s %6s %6s %6s %5s | %-9s %-9s %-4s %-4s %-4s | %-7s %-7s %-4s | p95 p99 p999 min max | %-9s %-9s | %-9s %-9s | '
      'offset -1/+1 mean,median match' % ('run', 'rows', 'first', 'frames', 'bad', 'mean_me', 'mean_rj', 'ok', 'ok-1', 'ok+1',
                                          'med_me', 'med_rj', 'ok', 'sum_ft_s', 'window_s', 'fps_me', 'fps_rj'))
    for r in RUNS:
        x = D[r]
        fr = x['j']['frames']
        s0 = x['st'][0]
        pm = ' '.join('Y' if eq(s0[k], fr.get(k), 3) else 'N' for k in ('p95_ms', 'p99_ms', 'p99_9_ms', 'min_ms', 'max_ms'))
        offs = []
        for o in (-1, 1):
            so = x['st'][o]
            offs.append('%+d: %s,%s' % (o, 'Y' if so and eq(so['mean_ms'], fr['mean_ms'], 4) else 'N',
                                        'Y' if so and eq(so['median_ms'], fr['median_ms'], 3) else 'N'))
        w('%-16s %6d %6d %6d %5d | %-9.4f %-9.4f %-4s %-4s %-4s | %-7.3f %-7.3f %-4s | %s | %-9.4f %-9.4f | %-9.3f %-9.3f | %s'
          % (('*' if r in SPOT else ' ') + r, x['nrows'], x['first'], x['frames'], x['bad'] + x['blank'],
             s0['mean_ms'], fr['mean_ms'], 'Y' if eq(s0['mean_ms'], fr['mean_ms'], 4) else 'N',
             'Y' if x['st'][-1] and eq(x['st'][-1]['mean_ms'], fr['mean_ms'], 4) else 'N',
             'Y' if x['st'][1] and eq(x['st'][1]['mean_ms'], fr['mean_ms'], 4) else 'N',
             s0['median_ms'], fr['median_ms'], 'Y' if eq(s0['median_ms'], fr['median_ms'], 3) else 'N', pm,
             s0['sum_s'], x['window_s'], x['fps'], fr.get('mean_fps'), ' '.join(offs)))
    w('rows_total in run.json vs parsed: %s' % ', '.join('%s %s/%d' % (short(r), D[r]['j']['frames'].get('rows_total'),
                                                                        D[r]['nrows']) for r in RUNS))
    w('perf.csv header (first run): %s' % ','.join(D[RUNS[0]]['hdr']))
    w()
    w('per-frame means over the window, constancy checks, threads.csv busy_pct, sys window, gpu.csv:')
    w('%-16s %8s %8s %8s %8s | %-24s | %6s %6s %6s %6s %6s %6s | %6s %6s %4s | %6s %6s %3s | %s' % (
        'run', 'fps', 'bufQ', 'funcs/f', 'intr/f', 'viol draw/vert/actthr', 'GPUcmd', 'Main', 'X1A8', 'TimerQ', 'X144',
        'thr_n', 'Putil', 'E_MHz', 'rows', 'Pu_me', 'E_me', 'rws', 'gpu.csv throttle counts (0x20 n, t_s range)'))
    for r in RUNS:
        x = D[r]
        n = x['n']
        th = x['thr']
        if th:
            x1 = one(th['x1a8'])
            alias = ''
            if x1 is None:
                x1 = one(th['x1ac'])
                alias = '(AC)'
            vals = [one(th['gpucmd']), one(th['main']), x1, one(th['timerq']), one(th['x144'])]
            tv = ' '.join('%6s' % ('-' if v is None else (('%.1f' % v) if not isinstance(v, tuple) else 'MULTI')) for v in vals)
            tv += ' %6s' % ('%d%s' % (th['n'], alias))
        else:
            vals = [None] * 5
            tv = ' '.join('%6s' % 'n/a' for _ in range(6))
        x['tvals'] = dict(zip(('gpucmd', 'main', 'x1a8', 'timerq', 'x144'), vals))
        x['alias'] = bool(th and not th['x1a8'] and th['x1ac'])
        g = x['gpu']
        gs = ('%s (0x20 %d, %s)' % (g['counts'], g['n20'], g['t20'])) if g else 'n/a'
        sr, spu, see = x['sysw']
        w('%-16s %8.3f %8.4f %8.4f %8.4f | %-24s | %s | %6.2f %6.0f %4s | %6.2f %6.0f %3d | %s' % (
            ('*' if r in SPOT else ' ') + r, x['fps'], x['tot']['buffer_queue_depth'] / n,
            x['tot']['functions_dispatched'] / n, x['tot']['interrupt_dispatches'] / n,
            '%d/%d/%d' % (x['viol']['draw_calls'], x['viol']['vertices_processed'], x['viol']['active_threads']), tv,
            x['putil'], x['emhz'], x['sysrows'], spu, see, sr, gs))
    w('constancy value sets: %s' % '; '.join('%s %s' % (short(r), {c: sorted(D[r]['const'][c])[:4] for c in D[r]['const']})
                                              for r in SPOT))
    for r in SPOT + ('1800-s0-r1',):
        th = D[r]['thr']
        w('top threads %-14s: %s' % (r, ', '.join('%s %.1f' % (nm, b) for b, nm in th['top'])))
        w('   matches: %s' % {k: th[k] for k in ('gpucmd', 'main', 'x1a8', 'x1ac', 'timerq', 'x144')})
    w()

    w('== B7. fixed-rate fit over all 16 runs: per second = window total / run.json frames.window_s')
    fps = [D[r]['fps'] for r in RUNS]
    ips = [D[r]['tot']['interrupt_dispatches'] / D[r]['window_s'] for r in RUNS]
    fns = [D[r]['tot']['functions_dispatched'] / D[r]['window_s'] for r in RUNS]
    k, c, r2, mx, res = ols(fps, ips)
    w('interrupt_dispatches/s = k * fps + r: k %.4f r %.3f R2 %.7f max|res| %.4f' % (k, c, r2, mx))
    k2, c2, r22, mx2, res2 = ols(fps, fns)
    w('functions_dispatched/s = k * fps + r: k %.4f r %.3f R2 %.7f max|res| %.4f' % (k2, c2, r22, mx2))
    for i, r in enumerate(RUNS):
        w('  %-15s fps %8.3f intr/s %9.3f funcs/s %9.3f res_i %+7.3f res_f %+7.3f funcs-intr /s %8.3f' % (
            r, fps[i], ips[i], fns[i], res[i], res2[i], fns[i] - ips[i]))
    d = [f - i for f, i in zip(fns, ips)]
    w('funcs/s - intr/s: min %.3f max %.3f (rounded to 0.1: %s)' % (min(d), max(d), sorted(set('%.1f' % v for v in d))))
    w()

    w('== B8. separation: 3 slow runs vs the non-slow runs (cold-base has no threads.csv / gpu.csv)')
    met = {
        'P util (run.json sys.window p_util_mean)': ({r: D[r]['putil'] for r in RUNS}, 'high'),
        'E eff MHz (run.json sys.window e_eff_mhz_mean)': ({r: D[r]['emhz'] for r in RUNS}, 'low'),
        'buffer_queue_depth per frame': ({r: D[r]['tot']['buffer_queue_depth'] / D[r]['n'] for r in RUNS}, 'high'),
        'Main XThread busy': ({r: D[r]['tvals']['main'] for r in RUNS}, 'low'),
        'X1A8 busy (alias F80001AC where F80001A8 is missing)': ({r: D[r]['tvals']['x1a8'] for r in RUNS}, 'high'),
        'X144 busy': ({r: D[r]['tvals']['x144'] for r in RUNS}, 'high'),
        'GPU Commands busy': ({r: D[r]['tvals']['gpucmd'] for r in RUNS}, 'high'),
    }
    for name, (vals, dirn) in met.items():
        sv = [(r, vals[r]) for r in SLOW if vals.get(r) is not None]
        nv = [(r, vals[r]) for r in RUNS if r not in SLOW and vals.get(r) is not None]
        if dirn == 'high':
            sb = min(sv, key=lambda t: t[1])
            nb = max(nv, key=lambda t: t[1])
            ok = sb[1] > nb[1]
            w('%s: slow %s | slow min %.4g (%s) vs non-slow max %.4g (%s), %d non-slow runs -> strictly separating: %s'
              % (name, ', '.join('%s %.4g' % (short(r), v) for r, v in sv), sb[1], short(sb[0]), nb[1], short(nb[0]),
                 len(nv), ok))
        else:
            sb = max(sv, key=lambda t: t[1])
            nb = min(nv, key=lambda t: t[1])
            ok = sb[1] < nb[1]
            w('%s: slow %s | slow max %.4g (%s) vs non-slow min %.4g (%s), %d non-slow runs -> strictly separating: %s'
              % (name, ', '.join('%s %.4g' % (short(r), v) for r, v in sv), sb[1], short(sb[0]), nb[1], short(nb[0]),
                 len(nv), ok))
        w('    all: %s' % ', '.join('%s %s' % (short(r), '-' if vals.get(r) is None else '%.4g' % vals[r]) for r in RUNS))
    w('runs using the F80001AC alias for X1A8: %s' % [r for r in RUNS if D[r].get('alias')])
    w('TimerQueue busy by arm:')
    for a in ('base', 's0', 'd11', 'd11t', 'd11p'):
        v = [D[r]['tvals']['timerq'] for r in RUNS if arm_of(r) == a and D[r]['tvals']['timerq'] is not None]
        w('  %-5s %s  range %.1f..%.1f' % (a, ', '.join('%.1f' % x for x in v), min(v), max(v)))
    w('gpu.csv throttle 0x20 samples per run (run.json start):')
    for r in RUNS:
        g = D[r]['gpu']
        w('  %-15s start %s  %s' % (r, D[r]['j'].get('start'), ('0x20 %d of %d rows, t_s %s, values %s' % (
            g['n20'], g['rows'], g['t20'], g['counts'])) if g else 'no gpu.csv'))
    early = [r for r in RUNS if D[r]['gpu'] and D[r]['j'].get('start', '') < '2026-11-22 18:13' and D[r]['gpu']['n20']]
    w('runs started before 18:13 with any 0x20 sample: %s' % (early or 'none'))
    w()

    w('== B4x. frames between Toypad B1 challenges (perf.csv rows mapped to wall time from measure_start: row first_row '
      '~ measure_start.epoch_s, then cumulative frame_time_us)')
    for r in RUNS:
        x = D[r]
        j = x['j']
        mse = j['measure_start']['epoch_s']
        rows = [row_at(x['ft'], x['first'], mse, T) for T in x['b1']]
        iv = [b - a for a, b in zip(x['b1'], x['b1'][1:])]
        fr = [b - a for a, b in zip(rows, rows[1:])]
        w('  %-15s %-4s window fps %7.1f | B1 at s after measure_start %s | intervals s %s | frames between %s | '
          'fps in interval %s' % (r, 'SLOW' if r in SLOW else '', x['fps'],
                                  [round(T - mse, 1) for T in x['b1']], [round(v, 1) for v in iv], fr,
                                  [round(f / v, 1) for f, v in zip(fr, iv)]))


if __name__ == '__main__':
    rc = 0
    try:
        main()
    except Exception:
        w('!!! EXCEPTION')
        w(traceback.format_exc())
        rc = 1
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(O) + '\n')
    print('perfcheck rc %d, %d lines -> %s' % (rc, len(O), OUT))
    sys.exit(rc)

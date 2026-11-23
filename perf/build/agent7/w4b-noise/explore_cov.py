#!/usr/bin/env python3
"""Scratch (Agent 7, task #6): per-run host-state covariates from sys.json / results.csv and a quick ANCOVA check of
how much each one explains of the within-arm spread of ln(fps) and ln(median ms). Read-only; stdlib; one thread.
Run: python -B build\\agent7\\w4b-noise\\explore_cov.py"""
import csv
import json
import math
import os
import statistics
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
DIRS = [os.path.join(REPO, 'build', 'agent8', 'matrix', d) for d in ('20261122-1541', '20261122-1756')]


def f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load(d):
    rows = list(csv.DictReader(open(os.path.join(d, 'results.csv'), encoding='utf-8-sig')))
    out = []
    for r in rows:
        if r['scored'] != 'True' or r['valid_timing'] != 'True' or r['excluded'] == 'True':
            continue
        rd = r['run_dir']
        if not os.path.isdir(rd):
            rd = os.path.join(d, 'runs', os.path.basename(rd))
        sj = json.load(open(os.path.join(rd, 'sys.json'), encoding='utf-8'))['window']
        x = {'name': os.path.basename(rd), 'arm': r['arm'], 'round': r['round'], 'seq': int(r['seq']),
             'fps': f(r['fps_mean']), 'med': f(r['median_ms']), 'cores': f(r['cpu_cores_mean']),
             'ls': f(r['light_share']), 'p_util': sj.get('p_util_mean'), 'e_mhz': sj.get('e_eff_mhz_mean'),
             'e_util': sj.get('e_util_mean'), 'cpu_util': sj.get('cpu_util_mean'), 'p_mhz': sj.get('p_eff_mhz_mean')}
        x['nongame'] = x['cpu_util'] / 100.0 * 12.0 - x['cores'] if x['cpu_util'] is not None else None
        out.append(x)
    return out


def ancova(runs, ykey, xkeys):
    """Pooled within-arm OLS of ln(y) on xkeys (arm as factor). Returns (s_raw, s_adj, df_adj, b)."""
    g = {}
    for x in runs:
        g.setdefault(x['arm'], []).append(x)
    yc, Xc = [], []
    for lst in g.values():
        ym = statistics.fmean([math.log(x[ykey]) for x in lst])
        xm = [statistics.fmean([x[k] for x in lst]) for k in xkeys]
        for x in lst:
            yc.append(math.log(x[ykey]) - ym)
            Xc.append([x[k] - m for k, m in zip(xkeys, xm)])
    n, G, k = len(runs), len(g), len(xkeys)
    s_raw = math.sqrt(sum(v * v for v in yc) / (n - G))
    if k == 0:
        return s_raw, s_raw, n - G, []
    S = [[sum(r[i] * r[j] for r in Xc) for j in range(k)] for i in range(k)]
    c = [sum(r[i] * v for r, v in zip(Xc, yc)) for i in range(k)]
    if k == 1:
        b = [c[0] / S[0][0]]
    else:
        det = S[0][0] * S[1][1] - S[0][1] * S[1][0]
        b = [(S[1][1] * c[0] - S[0][1] * c[1]) / det, (S[0][0] * c[1] - S[1][0] * c[0]) / det]
    e = [v - sum(bi * ri for bi, ri in zip(b, r)) for r, v in zip(Xc, yc)]
    return s_raw, math.sqrt(sum(v * v for v in e) / (n - G - k)), n - G - k, b


for d in DIRS:
    runs = load(d)
    print('=== %s (%d kept runs) ===' % (os.path.basename(d), len(runs)))
    print('%-16s %5s %3s %7s %6s %5s %5s %6s %6s %6s %7s %6s' % (
        'run', 'arm', 'rnd', 'fps', 'med', 'ls', 'cores', 'p_util', 'e_mhz', 'e_util', 'nongame', 'p_mhz'))
    for x in sorted(runs, key=lambda r: r['seq']):
        print('%-16s %5s %3s %7.1f %6.3f %5.3f %5.2f %6.1f %6.0f %6.1f %7.2f %6.0f' % (
            x['name'], x['arm'], x['round'], x['fps'], x['med'], x['ls'], x['cores'], x['p_util'], x['e_mhz'],
            x['e_util'], x['nongame'], x['p_mhz']))
    arms = list(dict.fromkeys(x['arm'] for x in sorted(runs, key=lambda r: r['seq'])))
    print('arm means of each covariate (does it move with the arm?):')
    for k in ('ls', 'cores', 'p_util', 'e_mhz', 'e_util', 'nongame'):
        print('  %-8s %s' % (k, '  '.join('%s %.2f' % (a, statistics.fmean([x[k] for x in runs if x['arm'] == a]))
                                         for a in arms)))
    for ykey in ('fps', 'med'):
        print('ANCOVA on ln(%s): pooled within-arm SD raw -> adjusted (df), slope(s)' % ykey)
        for xk in ([], ['ls'], ['e_mhz'], ['p_util'], ['e_mhz', 'p_util'], ['nongame'], ['e_util'], ['cores']):
            s0, s1, df, b = ancova(runs, ykey, xk)
            print('  %-16s %.4f -> %.4f (df %d)  b=%s' % ('+'.join(xk) or 'none', s0, s1, df,
                                                         ', '.join('%.5f' % v for v in b)))
    print()

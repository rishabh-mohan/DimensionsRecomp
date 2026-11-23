#!/usr/bin/env python3
"""Self-test of noise_methods.py, readout.py and repeats.py on synthetic data, plus readout.py's regression on W4b
and W5 against RESULTS.md and repeats.py's W5 inputs (needs build/agent8/matrix/20261122-1541 and -1756;
--no-regression skips them).
Run: python -B test_noise_methods.py [--no-regression]"""
import datetime
import importlib.util
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('noise_methods', os.path.join(HERE, 'noise_methods.py'))
N = importlib.util.module_from_spec(spec)
spec.loader.exec_module(N)

FAILS = []
CHECKS = []


def check(name, cond):
    print('%s %s' % ('PASS' if cond else 'FAIL', name))
    CHECKS.append(name)
    if not cond:
        FAILS.append(name)


def near(a, b, tol=1e-9):
    return a is not None and b is not None and abs(a - b) <= tol


def test_std_mix():
    F, S = [2000] * 1000, [8000] * 250  # 2 s of 2 ms frames, 2 s of 8 ms frames
    m = N.std_mix(F, S, 0.5)  # half the time each: 250 + 62.5 frames per s
    check('std_mix fps', near(m['fps'], 312.5))
    check('std_mix p50 / p99', m['p50_ms'] == 2.0 and m['p99_ms'] == 8.0)
    check('std_mix 1% low', near(m['low1_fps'], 125.0))
    m0 = N.std_mix(F, S, 0.0)
    check('std_mix h_ref 0 = F only', near(m0['fps'], 500.0) and m0['p99_ms'] == 2.0 and near(m0['low1_fps'], 500.0))
    check('std_mix needs both phases', N.std_mix(F, [], 0.5) is None and N.std_mix(None, S, 0.5) is None)
    m3 = N.std_mix([2000] * 10, [40000] * 10, 0.5)
    check('std_mix >33/min', near(m3['over33_min'], 0.5 * 10 * 6e7 / 400000.0))


def test_sys_spans_and_labels():
    pts = [(0, 1500), (1, 1500), (2, 500), (3, 500), (4, 500), (5, 1500), (6, 500), (7, 500), (8, 1500),
           (9, 1500)]
    slow, short, cover = N.sys_spans(pts, 800, 3)
    check('sys_spans slow', slow == [(1, 4)])
    check('sys_spans short', short == [(5, 7)])
    check('sys_spans cover', cover == (0, 9))
    ends = [0.5 * i for i in range(1, 19)]  # 0.5 .. 9.0 s after a window start at epoch 0
    lab = N.label_sys(ends, 0.0, (slow, short, cover), 0.3)
    want = ['F', None, 'S', 'S', 'S', 'S', 'S', None, 'F', None, None, None, None, None, 'F', 'F', 'F', 'F']
    check('label_sys', lab == want)
    check('label_sys no sys.csv', N.label_sys(ends, 0.0, N.sys_spans([], 800, 3), 0.3) is None)
    slow2, _, _ = N.sys_spans([(0, 1500), (1, 500), (2, 500), (3, 500)], 800, 3)
    check('sys_spans stretch to the end', slow2 == [(0, 3)])


def test_label_roll():
    ft = [3000] * 500 + [8000] * 500
    ends, c = [], 0.0
    for v in ft:
        c += v
        ends.append(c / 1e6)
    lab, nsw, meds = N.label_roll(ft, ends, 51, 5.0, 0.0)
    check('label_roll switch', nsw == 1 and lab[499] == 'F' and lab[500] == 'S' and lab[0] == 'F' and lab[-1] == 'S')
    check('label_roll medians', meds[0] == 3.0 and meds[-1] == 8.0)
    lab2, _, _ = N.label_roll(ft, ends, 51, 5.0, 0.01)
    check('label_roll guard', sum(1 for l in lab2 if l is None) == 5 and lab2[495] == 'F' and lab2[501] == 'S')


def test_trim_t_agree():
    check('trimmed_mean', N.trimmed_mean([1, 2, 3, 4, 100], 0.2) == 3.0)
    check('trimmed_mean small n', N.trimmed_mean([5.0, 7.0], 0.2) == 6.0)
    check('t975', N.t975(3) == 3.182 and N.t975(11) == 2.201 and N.t975(22) == 2.086 and N.t975(0) is None)
    check('agreement', N.agreement(['F', 'S', None, 'S'], ['F', 'F', 'S', 'S']) == 2.0 / 3.0)


def test_summarize_paired_norm():
    def run(name, arm, rnd):
        return {'name': name, 'arm': arm, 'round': rnd}
    d0 = [(run('d0-r%d' % i, 'd0', str(i)), v) for i, v in enumerate([3.234, 3.069, 3.565, 3.734], 1)]
    xx = [(run('X-r%d' % i, 'X', str(i)), v) for i, v in enumerate([3.0, 3.1, 3.2, 3.3], 1)]
    s = N.summarize({'d0': d0, 'X': xx}, 'd0', ['d0', 'X'], -1)
    check('summarize band = summary.md 19.6', near(s['band_pct'], 100.0 * 0.665 / 3.3995, 1e-6))
    check('summarize delta', near(s['arms']['X']['delta_pct'], 100.0 * (3.15 - 3.3995) / 3.3995, 1e-9))
    check('summarize verdict in band', s['arms']['X']['verdict'] == 'within' and s['df'] == 6)
    runs = [x for x, _ in d0 + xx]
    vals = dict((x['name'], v) for x, v in d0 + xx)
    val = lambda x, k: vals[x['name']]
    p = N.paired(runs, val, 'v', 'd0', ['d0', 'X'])
    ds = [100.0 * (a - b) / b for a, b in zip([3.0, 3.1, 3.2, 3.3], [3.234, 3.069, 3.565, 3.734])]
    check('paired deltas', all(near(a, b) for a, b in zip(p['X']['deltas'], ds)) and p['X']['n'] == 4)
    check('paired range / up', near(p['X']['range'], max(ds) - min(ds)) and p['X']['up'] == 1)
    nv = N.round_norm(runs, val, 'v')
    check('round_norm keeps the in-round ratio', near(nv['X-r1'] / nv['d0-r1'], 3.0 / 3.234))


def test_ancova_solve_report():
    check('solve 2x2', all(near(a, b) for a, b in zip(N.solve([[2, 1], [1, 3]], [3, 5]), [0.8, 1.4])))
    inv = N.inverse([[2, 1], [1, 3]])
    check('inverse 2x2', all(near(inv[i][j], v) for (i, j), v in
                             zip([(0, 0), (0, 1), (1, 0), (1, 1)], [0.6, -0.2, -0.2, 0.4])))
    check('solve singular', N.solve([[1, 2], [2, 4]], [1, 2]) is None)
    # ln v = arm effect + 0.5 x + noise, noise orthogonal to x within each arm -> slope 0.5 exactly
    noise = [0.01, -0.01, -0.01, 0.01]
    xs = {'R': [1.0, 2.0, 3.0, 4.0], 'X': [2.0, 3.0, 4.0, 5.0]}
    eff = {'R': 0.0, 'X': 0.1}
    runs, vals = [], {}
    for arm in ('R', 'X'):
        for i in range(4):
            v = math.exp(eff[arm] + 0.5 * xs[arm][i] + noise[i])
            x = {'name': '%s-r%d' % (arm, i + 1), 'arm': arm, 'round': str(i + 1), 'seq': len(runs) + 1, 'keep': True,
                 'why': [], 'cov': {'c': xs[arm][i]}, 'raw': {'fps': v, 'p50_ms': 1000.0 / v, 'p99_ms': 2000.0 / v,
                                                              'low1_fps': v / 2.0}}
            runs.append(x)
            vals.setdefault(arm, []).append((x, v))
    s = N.ancova(vals, lambda x: [x['cov']['c']], 'R', ['R', 'X'], 1)
    check('ancova slope', near(s['b'][0], 0.5, 1e-9) and s['df'] == 5 and s['k'] == 1 and s['n_dropped'] == 0)
    check('ancova delta', near(s['arms']['X']['gm_delta_pct'], 100.0 * (math.exp(0.1) - 1.0), 1e-7))
    sd = math.sqrt(8 * 0.0001 / 5)
    check('ancova sd', near(s['sd_ln'], sd, 1e-9))
    hw = 2.571 * sd * math.sqrt(0.25 + 0.25 + 1.0 / 10.0)
    lo, hi = s['arms']['X']['ci_pct']
    check('ancova ci', near(lo, 100.0 * (math.exp(0.1 - hw) - 1.0), 1e-7) and near(hi, 100.0 * (math.exp(0.1 + hw) - 1.0), 1e-7))
    check('ancova adjusted ref vals', near(max(s['ref_vals']) / min(s['ref_vals']), math.exp(0.02), 1e-9))
    check('ancova drops runs without the covariate',
          N.ancova(vals, lambda x: [None] if x['name'] == 'X-r4' else [x['cov']['c']], 'R', ['R', 'X'], 1)['n_dropped'] == 1)
    ci = N.covariate_info(runs, ['R', 'X'], ('c',))
    check('covariate_info F', near(ci['c']['F'], 1.2) and ci['c']['df'] == [1, 6] and near(ci['c']['means']['X'], 3.5))
    # report() on a small synthetic result: every section renders, no '%%' left over
    methods = [dict(N.summarize(N.collect(runs, N.getter('raw'), 'fps'), 'R', ['R', 'X'], 1), method='raw',
                    label='raw', key='fps', metric='fps', nd=1),
               dict(s, method='L-x', label='L', key='fps', metric='fps', nd=1, covs=['c'])]
    params = {'emhz': 800.0, 'min_rows': 3, 'guard_s': 1.5, 'roll': 201, 'heavy_ms': 5.0, 'roll_guard_s': 0.5,
              'trim': 0.2, 'bin_s': 10.0, 'cpus': 12}
    R = {'dir': 'synthetic', 'title': 't', 'command': 'c', 'ref': 'R', 'order': ['R', 'X'], 'params': params,
         'h_ref': None, 'h2_ref': None, 'hT_ref': None, 'ls_check_max_abs': None, 'runs': runs, 'methods': methods,
         'paired': [{'src': 'raw', 'key': 'fps', 'metric': 'fps', 'nd': 1, 'sign': 1,
                     'arms': N.paired(runs, N.getter('raw'), 'fps', 'R', ['R', 'X'])}],
         'cov_info': ci, 'hist_roll_med': {'6': 10}}
    text = N.report(R)
    check('report renders', '## Covariates (L, D)' in text and '## Runs: T split and host state' in text
          and '| L-x | fps |' in text and '%%' not in text)


def test_round_block():
    rho = {'1': 0.0, '2': 0.1, '3': -0.05}
    eff = {'R': 0.0, 'X': 0.05}
    noise = {'R': [0.01, -0.02, 0.01], 'X': [-0.01, 0.02, -0.01]}  # pure arm x round interaction
    runs, vals = [], {}
    for arm in ('R', 'X'):
        for i, rnd in enumerate(('1', '2', '3')):
            x = {'name': '%s-r%s' % (arm, rnd), 'arm': arm, 'round': rnd}
            runs.append(x)
            vals.setdefault(arm, []).append((x, math.exp(1.0 + eff[arm] + rho[rnd] + noise[arm][i])))
    rounds, blk = N.round_block(runs)
    check('round_block dummies', rounds == ['1', '2', '3'] and blk(runs[1]) == [1.0, 0.0] and blk(runs[0]) == [0.0, 0.0])
    s = N.ancova(vals, blk, 'R', ['R', 'X'], 1)
    sd = math.sqrt(0.0012 / 2)
    check('B-block two-way fit', s['df'] == 2 and near(s['b'][0], 0.1, 1e-9) and near(s['b'][1], -0.05, 1e-9)
          and near(s['sd_ln'], sd, 1e-9))
    hw = 4.303 * sd * math.sqrt(2.0 / 3.0)
    lo, hi = s['arms']['X']['ci_pct']
    check('B-block delta and CI', near(s['arms']['X']['gm_delta_pct'], 100.0 * (math.exp(0.05) - 1.0), 1e-7)
          and near(lo, 100.0 * (math.exp(0.05 - hw) - 1.0), 1e-7) and near(hi, 100.0 * (math.exp(0.05 + hw) - 1.0), 1e-7))


def test_noise_case():
    spc = importlib.util.spec_from_file_location('noise_case', os.path.join(HERE, 'noise_case.py'))
    NC = importlib.util.module_from_spec(spc)
    spc.loader.exec_module(NC)
    r = NC.loo_resid([('a', 2.0), ('b', 1.0), ('c', 1.0)], -1)
    check('loo_resid ms: + = slower', near(r['a'], 100.0) and near(r['b'], 100.0 * (math.exp(-0.5 * math.log(2.0)) - 1.0)))
    r2 = NC.loo_resid([('a', 2.0), ('b', 1.0), ('c', 1.0)], 1)
    check('loo_resid fps: + = slower', near(r2['a'], -50.0) and near(r2['b'], 100.0 * (math.sqrt(2.0) - 1.0)))
    check('loo_resid needs 2 runs', NC.loo_resid([('a', 2.0)], 1) == {})
    runs = [{'name': 'a', 'arm': 'R', 'seq': 1, 'keep': True, 'ls_T': 0.8, 'cov': {'p_util': 95.0, 'e_mhz': 550.0}},
            {'name': 'b', 'arm': 'R', 'seq': 2, 'keep': True, 'ls_T': 0.9, 'cov': {'p_util': 95.0, 'e_mhz': 700.0}},
            {'name': 'c', 'arm': 'R', 'seq': 3, 'keep': True, 'ls_T': 0.9, 'cov': {'p_util': 80.0, 'e_mhz': 500.0}},
            {'name': 'd', 'arm': 'R', 'seq': 4, 'keep': False, 'cov': {'p_util': 99.0, 'e_mhz': 500.0}}]
    R = {'dir': 'synthetic', 'ref': 'R', 'runs': runs,
         'methods': [{'method': 'raw', 'key': 'p50_ms', 'cv_pct': 5.0, 'band_pct': 10.0,
                      'arms': {'R': {'runs': ['a', 'b', 'c'], 'vals': [2.0, 1.0, 1.0]}}}]}
    check('flagged_runs', NC.flagged_runs(R, 90.0, 600.0) == ['a'])
    text = NC.report(R, ['p50_ms', 'fps'], ['raw', 'T-std'], 90.0, 600.0)
    check('noise_case report', '| raw | +100.0 | +100.0 | 100 |' in text and '| 1 | a | R | yes | +100.0 |' in text
          and '%%' not in text and '## fps' not in text)


# ---------------------------------------------------------------- readout.py (task #14)
_RO = []
W4B = os.path.normpath(os.path.join(HERE, '..', '..', 'agent8', 'matrix', '20261122-1541'))
W5 = os.path.normpath(os.path.join(HERE, '..', '..', 'agent8', 'matrix', '20261122-1756'))
# pure arm x round interaction: every row (arm) and column (round) sums to 0
NOISE = {('R', '1'): 0.01, ('R', '2'): -0.01, ('R', '3'): 0.01, ('R', '4'): -0.01,
         ('X', '1'): -0.01, ('X', '2'): 0.02, ('X', '3'): -0.01, ('X', '4'): 0.0,
         ('Y', '1'): 0.0, ('Y', '2'): -0.01, ('Y', '3'): 0.0, ('Y', '4'): 0.01}


def get_ro():
    if not _RO:
        spc = importlib.util.spec_from_file_location('readout', os.path.join(HERE, 'readout.py'))
        mod = importlib.util.module_from_spec(spc)
        spc.loader.exec_module(mod)
        _RO.append(mod)
    return _RO[0]


_RP = []


def get_rp():
    if not _RP:
        spc = importlib.util.spec_from_file_location('repeats', os.path.join(HERE, 'repeats.py'))
        mod = importlib.util.module_from_spec(spc)
        spc.loader.exec_module(mod)
        _RP.append(mod)
    return _RP[0]


def synth_window(RO, round_eff, ls_arm=None, overlay=None, raw_x=1.0):
    """3 arms x 4 rounds, round-robin; ln(median ms) = 1 + arm (X +0.03) + round + NOISE; run 9 (Y-r3) is hot."""
    arm_eff = {'R': 0.0, 'X': 0.03, 'Y': 0.0}
    runs, seq = [], 0
    for rnd in ('1', '2', '3', '4'):
        for arm in ('R', 'X', 'Y'):
            seq += 1
            v = math.exp(1.0 + arm_eff[arm] + round_eff[rnd] + NOISE[(arm, rnd)])
            st = {'fps': 1000.0 / v, 'p50_ms': v, 'p99_ms': 2.0 * v, 'low1_fps': 500.0 / v}
            f = raw_x if arm == 'X' else 1.0
            raw = {'fps': st['fps'] / f, 'p50_ms': v * f, 'p99_ms': 2.0 * v * f, 'low1_fps': st['low1_fps'] / f}
            ls = 0.6 + NOISE[(arm, rnd)] + (ls_arm or {}).get(arm, 0.0)
            ov = (overlay or {}).get(rnd, 'best_efficiency')
            sj = {'window': {'overlay': {'first': ov, 'last': ov, 'changes': []},
                             'scheme': {'first': 'Balanced', 'last': 'Balanced', 'changes': []},
                             'ac': {'first': 1, 'last': 1, 'changes': []},
                             'batt_saver': {'first': 0, 'last': 0, 'changes': []}}, 'run': {}}
            hot = (arm, rnd) == ('Y', '3')
            runs.append({'seq': str(seq), 'round': rnd, 'arm': arm, 'rep': rnd,
                         'name': '%04d-%s-r%s' % (2000 + seq, arm, rnd), 'scored': True, 'valid': True,
                         'excluded': False, 'keep': True, 'why': [], 'raw': raw, 't_std': dict(st), 't_L': dict(st),
                         't_H': dict(st), 'ls_T': ls, 'light_ms': 4.5, 'power': RO.power_info(sj, 'sys.json'),
                         'cov': {'ls_T': ls, 'p_util': 95.0 if hot else 60.0, 'e_mhz': 550.0 if hot else 1500.0}})
    return runs


def test_readout_synthetic():
    RO = get_ro()
    check('f_sf d1 = 2 closed form', near(RO.f_sf(3.0, 2, 2), 0.25, 1e-9) and near(RO.f_sf(4.459, 2, 8), 0.05, 2e-4))
    check('f_sf 5 % points', near(RO.f_sf(4.066, 3, 8), 0.05, 5e-4) and near(RO.f_sf(3.478, 4, 10), 0.05, 5e-4)
          and near(RO.f_sf(4.965, 1, 10), 0.05, 5e-4))
    check('f_sf edges', RO.f_sf(0.0, 3, 8) == 1.0 and RO.f_sf(1e9, 3, 8) < 1e-12 and RO.f_sf(None, 3, 8) is None)
    order = ['R', 'X', 'Y']
    flat = {'1': 0.0, '2': 0.0, '3': 0.0, '4': 0.0}
    steps = {'1': 0.0, '2': -0.05, '3': -0.04, '4': -0.06}
    R0 = RO.compute(synth_window(RO, flat), order, 'R')
    t0 = R0['round_test']['p50_ms']
    check('readout: no round effect -> T-std', R0['decision']['primary'] == 'T-std' and near(t0['F'], 0.0, 1e-9)
          and near(t0['p'], 1.0, 1e-9) and t0['df'] == [3, 6])
    R1 = RO.compute(synth_window(RO, steps), order, 'R')
    t1 = R1['round_test']['p50_ms']
    check('readout: round effect -> B-block T-std (F by hand 10.375)', R1['decision']['primary'] == RO.BLOCK
          and near(t1['F'], 10.375, 1e-6) and t1['p'] < 0.05)
    check('readout: round terms', all(near(a, 100.0 * (math.exp(b) - 1.0), 1e-7)
                                      for a, b in zip(t1['terms_pct'], [-0.05, -0.04, -0.06])))
    x1 = R1['methods'][RO.BLOCK]['p50_ms']['arms']['X']
    check('readout: B-block delta = the arm effect', near(x1['gm_delta_pct'], 100.0 * (math.exp(0.03) - 1.0), 1e-7))
    ga = R0['guards']['a']
    check('readout guard a: no arm moves the mix', near(ga['F'], 0.0, 1e-9) and not ga['warn'] and ga['df'] == [2, 9])
    Rw = RO.compute(synth_window(RO, flat, ls_arm={'X': 0.1}), order, 'R')
    check('readout guard a: warning', Rw['guards']['a']['warn'] and Rw['guards']['a']['p'] < 0.001)
    gb = R0['guards']['b']
    check('readout guard b: raw agrees', len(gb['p50_ms']) == 2 and all(v == 'agrees' for k in ('p50_ms', 'fps')
                                                                       for v in gb[k].values()))
    Rc = RO.compute(synth_window(RO, flat, raw_x=1.5), order, 'R')
    check('readout guard b: raw contradicts', Rc['guards']['b']['p50_ms'] == {'X': 'CONTRADICTS', 'Y': 'agrees'})
    check('readout guard c: flag', R0['guards']['c']['flagged'] == ['2009-Y-r3'])
    check('readout overlap', RO.overlap((-1, 1), (0.5, 2)) and not RO.overlap((-1, 0), (0.5, 2)))
    try:
        RO.pick_ref({}, ['a', 'b'], 'a', 'zz')
        bad = False
    except SystemExit:
        bad = True
    check('readout pick_ref', bad and RO.pick_ref({'arms': [{'id': 'b', 'ref': True}]}, ['a', 'b'], 'b', None)[1]
          == 'matrix.json arm "ref": true' and RO.pick_ref({'reference': 'a'}, ['a', 'b'], 'a', None)[1]
          == 'matrix.json "reference"' and RO.pick_ref({}, ['a', 'b'], 'a', 'b') == ('b', '--ref'))
    p = RO.power_info({'window': {'overlay': {'first': 'a', 'last': 'b', 'changes': [1]}}}, 'sys.json')['overlay']
    check('readout power_info', p['value'] == 'a->b (1 change)' and p['changed']
          and RO.power_info({'window': {}}) is None and RO.power_info(None) is None)
    g = RO.g11(synth_window(RO, flat))
    check('readout g11 OK', g['status'] == 'OK' and 'overlay best_efficiency 12/12' in g['line']
          and 'no change inside any window' in g['line'])
    gm = RO.g11(synth_window(RO, flat, overlay={'1': 'best_performance'}))
    check('readout g11 MIXED', gm['status'] == 'MIXED' and gm['suggest'] == '--overlay best_efficiency --rounds 2,3,4')
    rc = synth_window(RO, flat)
    rc[4]['power'] = RO.power_info({'window': {'overlay': {'first': 'best_efficiency', 'last': 'best_performance',
                                                           'changes': [{'t': 1}]}}}, 'sys.json')
    gc = RO.g11(rc)
    check('readout g11 change in a window', gc['status'] == 'MIXED' and 'changed inside the window: 2005-X-r2'
          in gc['line'] and gc['suggest'] == '--overlay best_efficiency --rounds 1,3,4')
    check('readout g11 NO DATA', RO.g11([dict(x, power=None) for x in synth_window(RO, flat)])['status'] == 'NO DATA')
    go = RO.g11(synth_window(RO, flat, overlay=dict((r, 'best_performance') for r in '1234')))
    check('readout g11 other overlay', go['status'] == 'OK' and "not W5's best_efficiency" in go['line'])
    R1.update(dir='synthetic', title='t', command='c', ref_src='test', hT_ref=0.5, notes=['n'], g11=gm)
    text = RO.render(R1)
    check('readout render', '## Read-out' in text and '**Primary: B-block T-std.**' in text
          and '| **B-block T-std** | median ms |' in text and '## G11 power' in text and '(c) Host flag' in text
          and '| 2009-Y-r3 |' in text and '%%' not in text)


def norm_md(s):
    """RESULTS.md and the kit's markdown compared without bold and with \\* as *."""
    return s.replace('**', '').replace('\\*', '*').rstrip()


def test_readout_regression():
    """readout.py on W4b and W5 must give RESULTS.md's rows and numbers exactly (--no-regression skips this)."""
    if '--no-regression' in sys.argv:
        print('SKIP readout regression on W4b and W5 (--no-regression)')
        return
    RO = get_ro()
    with open(os.path.join(HERE, 'RESULTS.md'), encoding='utf-8') as f:
        res_text = f.read()
    res = set(norm_md(l) for l in res_text.splitlines())
    B = RO.BLOCK
    cases = (('W4b', W4B, {'raw': RO.MAIN, 'T-std': RO.MAIN, B: RO.MAIN}, ('raw', 'T-std', B)),
             ('W5', W5, {'raw': RO.MAIN, 'T-std': RO.MAIN + RO.TAILS, B: RO.MAIN}, ('raw', 'T-std')))
    out = {}
    for tag, d, rows, deltas in cases:
        if not os.path.isdir(d):
            check('%s matrix dir present (%s)' % (tag, d), False)
            continue
        R = RO.analyse(d, RO.parse_args([d]), 'self-test')
        text = RO.render(R)
        lines = [norm_md(l) for l in text.splitlines()]
        out[tag] = (R, text, lines)
        for mid, keys in rows.items():
            for key in keys:
                row = RO.table_row(R, mid, key)
                check('%s %s %s row as in RESULTS.md' % (tag, mid, RO.LABEL[key]),
                      row is not None and norm_md(row) in res and norm_md(row) in lines)
        for mid in deltas:
            row = RO.delta_row(R, mid, 'p50_ms')
            check('%s %s median-delta row as in RESULTS.md' % (tag, mid), row is not None and row in res and row in lines)
    if 'W4b' in out:
        R, text, lines = out['W4b']
        t = R['round_test']['p50_ms']
        terms = [abs(v) for v in t['terms_pct']]
        check('W4b decision: B-block T-std', R['decision']['primary'] == B and t['p'] < 0.05 and t['df'] == [3, 8])
        logs = [abs(100.0 * b) for b in t['b']]
        check('W4b round terms: RESULTS.md "3.1-4.1 % below round 1" = 100 |b|; the kit prints 100 (e^b - 1) = '
              '-4.0 / -3.1 / -3.9 %', all(v < 0 for v in t['terms_pct']) and '%.1f' % min(logs) == '3.1'
              and '%.1f' % max(logs) == '4.1' and [RO.sgn(v) for v in t['terms_pct']] == ['-4.0', '-3.1', '-3.9']
              and '3.1-4.1 % below round 1' in res_text and 'round 2 -4.0 %, round 3 -3.1 %, round 4 -3.9 %' in text)
        check('W4b light share F = 0.40 on (3, 11)', 'F = 0.40 on (3, 11)' in text and 'W4b F = 0.40 on (3, 11)' in res_text)
        check('W4b hT_ref 0.531', RO.fmt(R['hT_ref'], 3) == '0.531' and 'hT_ref = 0.531' in text)
        lst = '(%s)' % ', '.join(RO.short(n) for n in R['guards']['c']['flagged'])
        check('W4b flagged list', lst == '(d11t-r1, d11t-r2, d3-r3, d0-r3, B-r3, d11t-r4, d0-r4)' and lst in res_text
              and lst in text)
        st = R['guards']['c']['stats']
        check('W4b flagged residual means (noise-case-w4b)', [RO.sgn(st[m]['mean']) for m in ('raw', 'T-std', B)]
              == ['+13.1', '-0.6', '-0.1'] and [RO.fmt(st[m]['rms_others']) for m in ('raw', 'T-std', B)]
              == ['10.9', '3.1', '1.7'])
        check('W4b ref d0, 15 kept, B-r2 left out', R['ref'] == 'd0' and R['ref_src'].startswith('matrix.json')
              and sum(1 for x in R['runs'] if x['keep']) == 15 and R['n'].get('B') == 3)
        check('W4b G11 OK', R['g11']['status'] == 'OK')
        check('W4b guard b: raw agrees', all(v == 'agrees' for k in RO.MAIN for v in R['guards']['b'][k].values())
              and 'raw agrees for every arm' in text)
    if 'W5' in out:
        R, text, lines = out['W5']
        t = R['round_test']['p50_ms']
        check('W5 decision: T-std', R['decision']['primary'] == 'T-std' and t['p'] >= 0.05 and t['df'] == [2, 8])
        check('W5 round terms +0.8 and -0.2 % on median ms', [RO.sgn(v) for v in t['terms_pct']] == ['+0.8', '-0.2']
              and '+0.8 and -0.2 % on median ms' in res_text)
        check('W5 light share F = 0.33 on (4, 10)', 'F = 0.33 on (4, 10)' in text and 'W5 F = 0.33 on (4, 10)' in res_text)
        check('W5 hT_ref 0.213', RO.fmt(R['hT_ref'], 3) == '0.213' and 'hT_ref = 0.213' in text)
        byname = dict((x['name'], x) for x in R['runs'])
        flag = R['guards']['c']['flagged']
        check('W5 flagged runs', flag == ['1808-s0-r2', '1817-base-r2', '1821-d11t-r3'])
        check('W5 flag rows as in RESULTS.md', all(RO.flag_row4(byname[n]) in res and any(
            l.startswith(RO.flag_row4(byname[n]) + ' ') for l in lines) for n in flag))
        rs = R['guards']['c']['resid']
        check('W5 flagged residuals raw / T-std', ' / '.join(RO.sgn(rs['raw'][n]) for n in flag) == '+6.2 / +18.3 / +16.6'
              and ' / '.join(RO.sgn(rs['T-std'][n]) for n in flag) == '+1.0 / +5.4 / +3.8')
        st = R['guards']['c']['stats']
        check('W5 flagged residual means', [RO.sgn(st[m]['mean']) for m in ('raw', 'T-std', B)] == ['+13.7', '+3.4', '+3.0']
              and [RO.fmt(st[m]['share_pct'], 0) for m in ('T-std', B)] == ['25', '22']
              and [RO.fmt(st[m]['rms_others']) for m in ('raw', 'T-std')] == ['5.4', '2.1'])
        e = R['methods'][B]['p99_ms']['arms']['d11t']
        check('W5 B-block T-std p99 d11t [+2.1, +15.9]',
              '[%s, %s]' % (RO.sgn(e['ci_pct'][0]), RO.sgn(e['ci_pct'][1])) == '[+2.1, +15.9]')
        check('W5 G11 OK, best_efficiency 16/16', R['g11']['status'] == 'OK'
              and 'overlay best_efficiency 16/16' in R['g11']['line'])
        check('W5 ref base, 15 kept', R['ref'] == 'base' and sum(1 for x in R['runs'] if x['keep']) == 15)
        check('W5 guard b: raw agrees', all(v == 'agrees' for k in RO.MAIN for v in R['guards']['b'][k].values()))
        Rf = RO.analyse(W5, RO.parse_args([W5, '--ref', 'd11', '--rounds', '1,2', '--drop', 'base-r2']), 'self-test')
        whyf = dict((x['name'], x['why']) for x in Rf['runs'])
        check('readout filters on W5 (--ref, --rounds, --drop)', Rf['ref'] == 'd11' and Rf['ref_src'] == '--ref'
              and sum(1 for x in Rf['runs'] if x['keep']) == 9 and '--drop' in whyf['1817-base-r2']
              and 'round 3 not in --rounds' in whyf['1825-base-r3'] and Rf['n']['base'] == 1
              and Rf['arms'] == ['base', 's0', 'd11t', 'd11p'])
        RP = get_rp()
        cvw, ncalm, nkept = RP.cv_of(R)
        tm = RP.timing(RP.run_times(W5, R['runs']))
        check('repeats on W5: s = T-std sd_ln (2.1 %, df 10), 12 unflagged runs, minutes model = the measured 33.9 min',
              near(cvw['p50_ms']['s'], R['methods']['T-std']['p50_ms']['sd_ln']) and cvw['p50_ms']['df'] == 10
              and RO.fmt(100.0 * cvw['p50_ms']['s']) == '2.1' and ncalm == 12 and nkept == 15 and tm is not None
              and tm['runs'] == 15 and tm['cold'] == 1 and near(RP.minutes(5, 3, tm) * 60.0, tm['total_s'], 1e-6)
              and '%.1f' % (tm['total_s'] / 60.0) == '33.9')


def test_repeats_synthetic():
    RO, RP = get_ro(), get_rp()
    check('repeats chi2 quantiles (df 10: 3.247, 20.483; df 8: 17.535)', near(RP.chi2_ppf(0.025, 10), 3.247, 2e-3)
          and near(RP.chi2_ppf(0.975, 10), 20.483, 2e-3) and near(RP.chi2_ppf(0.975, 8), 17.535, 2e-3))
    check('repeats t quantiles (df 10: 2.228, 0.879; df 4: 2.776)', near(RP.t_ppf(0.975, 10), 2.228, 1e-3)
          and near(RP.t_ppf(0.80, 10), 0.879, 1e-3) and near(RP.t_ppf(0.975, 4), 2.776, 1e-3))
    check('repeats df: T-std A (n - 1), B-block (A - 1)(n - 1)', RP.df_of(5, 3) == 10 and RP.df_of(5, 3, True) == 8
          and RP.df_of(2, 3, True) == 2 and RP.df_of(6, 5) == 24)
    flat = {'1': 0.0, '2': 0.0, '3': 0.0, '4': 0.0}
    R0 = RO.compute(synth_window(RO, flat), ['R', 'X', 'Y'], 'R')
    s = R0['methods']['T-std']['p50_ms']
    lo, hi = s['arms']['X']['ci_pct']
    half = 100.0 * (math.exp((math.log1p(hi / 100.0) - math.log1p(lo / 100.0)) / 2.0) - 1.0)
    h = RP.hw_pct(s['sd_ln'], 4, RP.df_of(3, 4))
    check("repeats hw = the kit's band (4 vs 4 band and an arm's CI, 3 arms x 4)", near(h, s['hw44_pct'], 1e-9)
          and near(h, half, 1e-9) and RP.mde_pct(s['sd_ln'], 4, 9) > h)
    t0, sec = datetime.datetime(2026, 11, 22, 18, 0, 0), datetime.timedelta(seconds=1)
    tt = [{'name': 'cold', 'scored': False, 'start': t0, 'end': t0 + 100 * sec}] + [
        {'name': 'r%d' % i, 'scored': True, 'start': t0 + b * sec, 'end': t0 + (b + 120) * sec}
        for i, b in enumerate((110, 240, 370))]
    tm = RP.timing(tt)
    check('repeats minutes model (cold slot 110 s, slot 130 s, last run 120 s)', near(tm['slot_s'], 130.0)
          and near(tm['cold_slot_s'], 110.0) and near(tm['last_s'], 120.0) and near(tm['total_s'], 490.0)
          and near(RP.minutes(3, 1, tm), 490.0 / 60.0))
    lo_f, hi_f = RP.cv_range(10)
    check('repeats CV range on df 10: 0.699-1.755 x s', near(lo_f, 0.699, 1e-3) and near(hi_f, 1.755, 1e-3))


for fn in (test_std_mix, test_sys_spans_and_labels, test_label_roll, test_trim_t_agree, test_summarize_paired_norm,
           test_ancova_solve_report, test_round_block, test_noise_case, test_readout_synthetic,
           test_repeats_synthetic, test_readout_regression):
    fn()
print('RESULT %s (%d checks, %d failed)' % ('FAIL' if FAILS else 'PASS', len(CHECKS), len(FAILS)))
sys.exit(1 if FAILS else 0)

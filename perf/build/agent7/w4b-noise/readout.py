#!/usr/bin/env python3
"""T-std read-out kit (Agent 7, task #14): one short markdown + json per run-matrix window, read-only.

Usage:
  python -B build\\agent7\\w4b-noise\\readout.py DIR [-o OUT.md] [--json OUT.json] [--ref ARM] [--alpha 0.05]
         [--putil 90] [--emhz 600] [--overlay NAME] [--rounds 1,2] [--drop RUN[,RUN]] [--light-ms MS] [--all]
         [--normal-priority]

DIR: a bench/agent8 run-matrix.ps1 output dir (matrix.json, results.csv, runs/). The arms and their order come from
matrix.json (the arms present in results.csv). The reference arm is the arm with "ref": true, else matrix.json's
"reference", else the first arm; --ref overrides. Any number of runs per arm and any number of rounds.

Kept runs are chosen as in noise_methods.py (W4b, W5): scored (the cold run is not), valid timing (--all keeps the
others), not excluded, and with a scored frame window. --overlay, --rounds and --drop leave out more runs. Every
left-out run is listed with the reason.

It uses noise_methods.py's own functions, so W4b and W5 give the same numbers as RESULTS.md
(test_noise_methods.py checks this):
  T-std     Each run's scored frames are split at frames.json light_ms (4.5 ms). The light and heavy parts are
            re-mixed at one heavy-time share, hT_ref = the median over the kept runs. Output: the GM delta vs the
            ref with the pooled 95 % CI (df = runs - arms); summary.md's band on the ref's runs; the median delta.
  B-block   T-std in the two-way model ln v = arm + round (ANCOVA on round dummies). df = runs - arms - rounds + 1.
            Rounds are blocks of the round-robin order.
  Which one applies: the nested F test of the round terms on median ms (residual SS of one-way T-std vs B-block
            T-std, F(rounds - 1, df_B)). If p < --alpha, B-block T-std applies; otherwise T-std. With one round,
            T-std.
  Guards    (a) Light share (frames < light_ms) per arm, with a one-way F. T-std fixes the mix, so it hides an arm
            that moves the mix. p < --alpha is a warning, and T-light and T-heavy rows are added.
            (b) Raw GM deltas with the pooled CI (median ms, fps). Per arm: 'agrees' when raw's CI overlaps the
            primary's CI, else CONTRADICTS.
            (c) Host flag: sys.json window P util >= --putil and E-core MHz < --emhz (noise_case.py). Each flagged
            run gets its leave-one-out residual on median ms (+ = slower).
  G11       Per run: the power overlay, scheme, AC and battery saver from the sys.json window (run.json's copy is the
            fallback, as in Agent 12's w6_env_record.py). OK = one value of each (overlay, scheme, AC) in every run,
            with no change inside any window. Otherwise MIXED, with the --overlay and --rounds that read only the
            rounds in which every arm ran on one overlay.
Writes only -o and --json; without -o it prints the markdown to stdout. It lowers its own priority to Below Normal
(--normal-priority turns this off). Stdlib only, one thread.
"""
import argparse
import collections
import importlib.util
import json
import math
import os
import re
import statistics
import sys

sys.dont_write_bytecode = True  # no __pycache__ next to this file or the imported tools

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, fn):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, fn))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


N = _load('noise_methods', 'noise_methods.py')
NC = _load('noise_case', 'noise_case.py')
W = N.W
fmt, sgn, num = N.fmt, N.sgn, N.num

# (key, +1 = higher is better / -1 = lower is better, label as in RESULTS.md)
KEYS = (('p50_ms', -1, 'median ms'), ('fps', 1, 'fps'), ('p99_ms', -1, 'p99 ms'), ('low1_fps', 1, '1 % low fps'))
SIGN = dict((k, s) for k, s, _ in KEYS)
LABEL = dict((k, l) for k, _, l in KEYS)
MAIN, TAILS = ('p50_ms', 'fps'), ('p99_ms', 'low1_fps')
FIELDS = (('raw', 'raw'), ('T-std', 't_std'), ('T-light', 't_L'), ('T-heavy', 't_H'))
BLOCK = 'B-block T-std'
PRIMARIES = ('T-std', BLOCK)
RES_METHODS = ('raw', 'T-std', BLOCK)
# (key, sys.json field, label); G11 passes on one overlay, scheme and AC in every run with no change in a window
POWER = (('overlay', 'overlay', 'overlay'), ('scheme', 'scheme', 'scheme'), ('ac', 'ac', 'AC'),
         ('saver', 'batt_saver', 'saver'))
G11_KEYS = ('overlay', 'scheme', 'ac')
W5_OVERLAY = 'best_efficiency'


def below_normal():
    """Lower this process to Below Normal (Windows) or nice +5; best effort, True when it worked."""
    try:
        if os.name == 'nt':
            import ctypes
            k = ctypes.windll.kernel32
            k.GetCurrentProcess.restype = ctypes.c_void_p
            k.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
            return bool(k.SetPriorityClass(k.GetCurrentProcess(), 0x4000))
        os.nice(5)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------- F distribution (regularized incomplete beta)
def _betacf(a, b, x):
    """Continued fraction of the incomplete beta function (modified Lentz, Numerical Recipes betacf)."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 400):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        de = d * c
        h *= de
        if abs(de - 1.0) < 1e-15:
            break
    return h


def betai(a, b, x):
    """Regularized incomplete beta I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbt = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1.0 - x)
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(lbt) * _betacf(a, b, x) / a
    return 1.0 - math.exp(lbt) * _betacf(b, a, 1.0 - x) / b


def f_sf(F, d1, d2):
    """P(F(d1, d2) > F); None without F."""
    if F is None or d1 is None or d2 is None or d1 < 1 or d2 < 1:
        return None
    if F <= 0.0:
        return 1.0
    return betai(d2 / 2.0, d1 / 2.0, d2 / (d2 + d1 * F))


def pfmt(p):
    return '-' if p is None else ('< 0.001' if p < 0.001 else '%.3f' % p)


# ---------------------------------------------------------------- power (G11)
def tri(x):
    """Agent 12's w6_env_record.py form: 'value', or 'first->last', plus ' (n changes)'; None without data."""
    if not isinstance(x, dict):
        return None
    first, last, ch = x.get('first'), x.get('last'), x.get('changes') or []
    text = '%s' % first if first == last else '%s->%s' % (first, last)
    return text + (' (%d change%s)' % (len(ch), '' if len(ch) == 1 else 's') if ch else '')


def changed(x):
    return isinstance(x, dict) and (bool(x.get('changes')) or x.get('first') != x.get('last'))


def sys_block(rd):
    """(sys.json-like dict, source) as w6_env_record.sys_data: sys.json with a 'window' block, else run.json's copy."""
    if not rd or not os.path.isdir(rd):
        return None, None
    s = W.load_json(os.path.join(rd, 'sys.json'))
    if isinstance(s, dict) and isinstance(s.get('window'), dict):
        return s, 'sys.json'
    r = W.load_json(os.path.join(rd, 'run.json'))
    if isinstance(r, dict):
        for v in r.values():
            if isinstance(v, dict) and isinstance(v.get('window'), dict) and 'run' in v:
                return v, 'run.json'
    return None, None


def power_info(s, src=None):
    """{key: {value, first, changed, run_changed}} for overlay, scheme, ac and saver over the window, plus 'src';
    None without a window block or without any power field."""
    w = s.get('window') if isinstance(s, dict) else None
    if not isinstance(w, dict):
        return None
    r = s.get('run') if isinstance(s.get('run'), dict) else {}
    out = {}
    for key, field, _ in POWER:
        x = w.get(field)
        if isinstance(x, dict):
            out[key] = {'value': tri(x), 'first': x.get('first'), 'changed': changed(x),
                        'run_changed': changed(r.get(field))}
    if not out:
        return None
    out['src'] = src
    return out


def g11(runs):
    """G11 over every run with power data: value counts, changes inside a window, status OK / PARTIAL / MIXED /
    NO DATA, per-arm overlay counts, and for MIXED the --overlay / --rounds that keep only the rounds in which every
    scored run ran on one overlay."""
    n = len(runs)
    have = [x for x in runs if x.get('power')]
    if not have:
        return {'status': 'NO DATA', 'counts': {}, 'moved': {}, 'missing': [x['name'] for x in runs],
                'per_arm': {}, 'suggest': None,
                'line': 'NO DATA: no power fields in sys.json or run.json, so G11 is not checked.'}
    counts, moved, parts = {}, {}, []
    for key, _, label in POWER:
        vals = [(x, x['power'][key]) for x in have if key in x['power']]
        if not vals:
            continue
        cnt = collections.Counter(p['value'] for _, p in vals)
        counts[key] = dict(cnt)
        moved[key] = [x['name'] for x, p in vals if p['changed']]
        parts.append('%s %s' % (label, ', '.join('%s %d/%d' % (v, c, n) for v, c in cnt.most_common())))
    missing = [x['name'] for x in runs if not x.get('power')]
    mixed = any(len(counts.get(k) or {}) > 1 or moved.get(k) for k in G11_KEYS)
    status = 'MIXED' if mixed else ('PARTIAL' if missing else 'OK')
    ch = [x['name'] for x in runs if any(x['name'] in moved.get(k, []) for k, _, _ in POWER)]
    line = '%s: %s; %s' % (status, '; '.join(parts),
                           ('changed inside the window: ' + ', '.join(ch)) if ch else 'no change inside any window')
    if missing:
        line += '; no power data: %s' % ', '.join(missing)
    ov = counts.get('overlay') or {}
    if not mixed and len(ov) == 1 and list(ov)[0] != W5_OVERLAY:
        line += ("; the overlay is not W5's %s, so compare arms within this window only, not with W5's absolute "
                 "numbers" % W5_OVERLAY)
    per_arm = collections.OrderedDict()
    for x in have:
        if 'overlay' in x['power']:
            d = per_arm.setdefault(x['arm'], collections.Counter())
            d[x['power']['overlay']['value']] += 1
    suggest = None
    if mixed:
        byr = collections.OrderedDict()
        for x in runs:
            if x.get('scored'):
                byr.setdefault(x['round'], []).append(x)
        per = collections.OrderedDict()
        for rnd, xs in byr.items():
            ps = [(x.get('power') or {}).get('overlay') for x in xs]
            if ps and all(p and not p['changed'] for p in ps) and len(set(str(p['first']) for p in ps)) == 1:
                per.setdefault(str(ps[0]['first']), []).append(str(rnd))
        if per:
            best = max(per.items(), key=lambda kv: len(kv[1]))
            suggest = '--overlay %s --rounds %s' % (best[0], ','.join(best[1]))
            line += ('; read the pairs only over the rounds in which every arm ran on one overlay: rerun with %s'
                     % suggest)
        else:
            line += '; no round has every arm on one unchanged overlay'
    return {'status': status, 'counts': counts, 'moved': moved, 'missing': missing,
            'per_arm': dict((a, dict(c)) for a, c in per_arm.items()), 'suggest': suggest, 'line': line}


# ---------------------------------------------------------------- loading
def short(name):
    """Run name without the HHMM- prefix (1808-s0-r2 -> s0-r2)."""
    return re.sub(r'^\d{4}-', '', name or '')


def ns_methods(a):
    """noise_methods.py's default parameters; its loader also computes A, A2 and C, which are not used here."""
    return argparse.Namespace(all=a.all, emhz=800.0, min_rows=3, guard_s=1.5, roll=201, heavy_ms=5.0,
                              roll_guard_s=0.5, trim=0.2, bin_s=10.0, light_ms=a.light_ms,
                              cpus=os.cpu_count() or 12)


def pick_ref(mj, order, ref0, want):
    """(ref, where it came from); --ref must name an arm in results.csv."""
    if want:
        if want not in order:
            raise SystemExit('--ref %s: no such arm in results.csv (arms: %s)' % (want, ', '.join(order)))
        return want, '--ref'
    cfg = [x for x in (mj.get('arms') or []) if isinstance(x, dict) and x.get('id')]
    if any(x.get('ref') and x['id'] == ref0 for x in cfg):
        return ref0, 'matrix.json arm "ref": true'
    if ref0 is not None and mj.get('reference') == ref0:
        return ref0, 'matrix.json "reference"'
    return ref0, 'the first arm; matrix.json names no reference'


def load(d, a):
    """noise_methods.load_runs, then per run: power (G11), the run's excluding flags in its why, the --rounds /
    --drop / --overlay filters; then hT_ref and T-std as noise_methods.analyse (over the runs kept after the
    filters). Returns (runs, order, ref, ref_src, title, hT_ref, notes)."""
    runs, order, ref0, title, _ = N.load_runs(d, ns_methods(a))
    rows = W.read_rows(os.path.join(d, 'results.csv')) or []
    mj = W.load_json(os.path.join(d, 'matrix.json')) or {}
    if len(rows) != len(runs):
        raise SystemExit('results.csv changed while reading %s' % d)
    for x, r in zip(runs, rows):
        s, src = sys_block(W.resolve_run_dir(d, r))
        x['power'] = power_info(s, src)
        fx = (r.get('flags_excluding') or '').strip()
        if x['excluded'] and fx:
            x['why'] = ['excluded (%s)' % fx if y == 'excluded' else y for y in x['why']]
    ref, ref_src = pick_ref(mj, order, ref0, a.ref)
    notes = []
    want_r = [s.strip() for s in (a.rounds or '').split(',') if s.strip()]
    want_d = [s.strip() for s in (a.drop or '').split(',') if s.strip()]
    for s in want_r:
        if not any(str(x['round']) == s for x in runs):
            notes.append('--rounds %s matches no run' % s)
    for s in want_d:
        if not any(s in (x['name'], short(x['name'])) for x in runs):
            notes.append('--drop %s matches no run' % s)
    for x in runs:
        if not x['keep']:
            continue
        if want_r and str(x['round']) not in want_r:
            x['keep'] = False
            x['why'].append('round %s not in --rounds' % x['round'])
        if want_d and (x['name'] in want_d or short(x['name']) in want_d):
            x['keep'] = False
            x['why'].append('--drop')
        if a.overlay:
            p = (x.get('power') or {}).get('overlay')
            if not p or p['changed'] or str(p['first']) != a.overlay:
                x['keep'] = False
                x['why'].append('overlay %s, not --overlay %s' % (p['value'] if p else 'unknown', a.overlay))
    kept = [x for x in runs if x['keep']]
    hTs = [x['hT'] for x in kept if x.get('hT') is not None and 0.0 < x['hT'] < 1.0]
    hT_ref = statistics.median(hTs) if hTs else None
    for x in runs:
        x['t_std'] = N.std_mix(x.get('_TL'), x.get('_TH'), hT_ref)
        for k in ('_F', '_S', '_F2', '_S2', '_TL', '_TH'):
            x.pop(k, None)
    return runs, order, ref, ref_src, title, hT_ref, notes


# ---------------------------------------------------------------- numbers
def round_test(s1, s2, alpha):
    """Nested F test of the round terms: one-way (s1) vs two-way B-block (s2) residual SS of ln(value), on the same
    runs. Returns F, df, p, block (p < alpha) and the round terms in % vs the first round; None without B-block."""
    if not s1 or not s2 or s1.get('sd_ln') is None or s2.get('sd_ln') is None:
        return None
    k, df2 = s2.get('k') or 0, s2.get('df') or 0
    ss1, ss2 = s1['sd_ln'] ** 2 * s1['df'], s2['sd_ln'] ** 2 * df2
    if k < 1 or df2 < 1 or ss2 <= 0.0:
        return None
    F = max(0.0, ss1 - ss2) / k / (ss2 / df2)
    p = f_sf(F, k, df2)
    # terms_pct = 100 (e^b - 1), the kit's % convention; b = the fitted round terms on ln(value) (RESULTS.md's
    # "3.1-4.1 % below round 1" for W4b is 100 |b|; in the kit's % that is 3.1-4.0 %)
    return {'F': F, 'df': [k, df2], 'p': p, 'block': p is not None and p < alpha, 'b': list(s2.get('b') or []),
            'terms_pct': [100.0 * (math.exp(b) - 1.0) for b in s2.get('b') or []]}


def overlap(c1, c2):
    return c1[0] <= c2[1] and c2[0] <= c1[1]


def compute(runs, order, ref, alpha=0.05, putil=90.0, emhz=600.0):
    """Every number of the read-out from loaded runs (keep, raw, t_std, t_L, t_H, ls_T, cov, power per run)."""
    kept = [x for x in runs if x['keep']]
    arms = [arm for arm in order if arm != ref]
    rounds, blk = N.round_block(kept)
    M = collections.OrderedDict()
    for mid, field in FIELDS:
        g = N.getter(field)
        M[mid] = dict((key, N.summarize(N.collect(kept, g, key), ref, order, sign)) for key, sign, _ in KEYS)
    if len(rounds) >= 2:
        g = N.getter('t_std')
        M[BLOCK] = dict((key, N.ancova(N.collect(kept, g, key), blk, ref, order, sign)) for key, sign, _ in KEYS)
    rt = dict((key, round_test(M['T-std'].get(key), (M.get(BLOCK) or {}).get(key), alpha)) for key, _, _ in KEYS)
    # which one applies: the round terms on median ms
    t, tf = rt.get('p50_ms'), rt.get('fps')
    if M['T-std'].get('p50_ms') is None:
        prim, why = 'T-std', 'No T-std values for the ref arm %s, so there is nothing to compare (try --ref).' % ref
    elif t is None:
        prim = 'T-std'
        why = ('One round only, so T-std (no round test).' if len(rounds) < 2 else
               'B-block T-std could not be fitted (too few runs), so T-std.')
    else:
        txt = 'F = %.2f on (%d, %d), p = %s' % (t['F'], t['df'][0], t['df'][1], pfmt(t['p']))
        if t['block']:
            prim = BLOCK
            why = ('Round effect on median ms: %s < %g, so B-block T-std applies (df = runs - arms - rounds + 1); '
                   'T-std is shown beside it.' % (txt, alpha))
        else:
            prim = 'T-std'
            why = ('No round effect on median ms: %s >= %g, so T-std applies (df = runs - arms); B-block T-std is '
                   'shown beside it.' % (txt, alpha))
        if tf is not None and tf['block'] != t['block']:
            why += ' fps disagrees: F = %.2f on (%d, %d), p = %s.' % (tf['F'], tf['df'][0], tf['df'][1], pfmt(tf['p']))
    # guard (a): light share per arm
    ci = N.covariate_info(kept, order, ('ls_T',)).get('ls_T')
    ga = None
    if ci:
        p = f_sf(ci['F'], ci['df'][0], ci['df'][1]) if ci.get('F') is not None else None
        ga = dict(ci, p=p, warn=p is not None and p < alpha)
    # guard (b): raw vs the primary
    gb = {}
    for key in MAIN:
        sr, sp = M['raw'].get(key) or {}, (M.get(prim) or {}).get(key) or {}
        per = collections.OrderedDict()
        for arm in arms:
            er, ep = (sr.get('arms') or {}).get(arm), (sp.get('arms') or {}).get(arm)
            if er and ep and er.get('ci_pct') and ep.get('ci_pct'):
                per[arm] = 'agrees' if overlap(er['ci_pct'], ep['ci_pct']) else 'CONTRADICTS'
        gb[key] = per
    # guard (c): host flag and median-ms residuals
    flag = NC.flagged_runs({'runs': runs}, putil, emhz)
    res, stats = collections.OrderedDict(), collections.OrderedDict()
    for mid in RES_METHODS:
        s = (M.get(mid) or {}).get('p50_ms')
        if s:
            res[mid] = NC.residuals(s, SIGN['p50_ms'])
    for mid, r in res.items():
        fv = [r[nm] for nm in flag if nm in r]
        other = [v for nm, v in r.items() if nm not in flag]
        stats[mid] = {'mean': statistics.fmean(fv) if fv else None,
                      'rms_others': math.sqrt(statistics.fmean([v * v for v in other])) if other else None}
    raw_mean = (stats.get('raw') or {}).get('mean')
    for st in stats.values():
        st['share_pct'] = 100.0 * st['mean'] / raw_mean if (st['mean'] is not None and raw_mean) else None
    gc = {'putil': putil, 'emhz': emhz, 'flagged': flag, 'resid': res, 'stats': stats}
    nper = collections.OrderedDict((arm, sum(1 for x in kept if x['arm'] == arm)) for arm in order)
    unbal = [str(r) for r in rounds if set(x['arm'] for x in kept if x['round'] == r) != set(nper)]
    return {'tool': 'readout.py', 'runs': runs, 'order': order, 'ref': ref, 'arms': arms, 'n': nper,
            'rounds': rounds, 'unbalanced_rounds': unbal, 'alpha': alpha, 'methods': M, 'round_test': rt,
            'decision': {'primary': prim, 'why': why}, 'guards': {'a': ga, 'b': gb, 'c': gc},
            'light_ms': sorted(set(x['light_ms'] for x in runs if x.get('light_ms') is not None))}


def analyse(d, a, command=''):
    d = os.path.abspath(d)
    if not os.path.isfile(os.path.join(d, 'results.csv')):
        raise SystemExit('no results.csv in %s' % d)
    runs, order, ref, ref_src, title, hT_ref, notes = load(d, a)
    R = compute(runs, order, ref, a.alpha, a.putil, a.emhz)
    if R['unbalanced_rounds']:
        notes.append('rounds without every arm: %s (B-block handles this; check the order is round-robin)'
                     % ', '.join(R['unbalanced_rounds']))
    R.update(dir=d, title=title, command=command, ref_src=ref_src, hT_ref=hT_ref, notes=notes,
             params=dict((k, v) for k, v in vars(a).items() if k not in ('out', 'json')), g11=g11(runs))
    return R


# ---------------------------------------------------------------- markdown
def ci_cell(e):
    if not e or e.get('ci_pct') is None:
        return '-'
    return '%s [%s, %s]%s' % (sgn(e['gm_delta_pct']), sgn(e['ci_pct'][0]), sgn(e['ci_pct'][1]),
                              ' *' if e.get('ci_excludes_0') else '')


def summary_of(R, mid, key):
    return (R['methods'].get(mid) or {}).get(key)


def table_head(R):
    return ['| method | metric | %s band %% | pooled CV %% | 4 vs 4 band %% | df | %s |' % (
        R['ref'], ' | '.join('%s (n=%d)' % (arm, R['n'].get(arm, 0)) for arm in R['arms'])),
        '|---|---|---|---|---|---|%s' % ('---|' * len(R['arms']))]


def table_row(R, mid, key, bold=False):
    """RESULTS.md's row: method | metric | ref band | pooled CV | 4 vs 4 band | df | GM delta [CI] per arm."""
    s = summary_of(R, mid, key)
    if not s:
        return None
    cells = [ci_cell((s.get('arms') or {}).get(arm)) for arm in R['arms']]
    return '| %s | %s | %s | %s | %s | %d | %s |' % ('**%s**' % mid if bold else mid, LABEL[key], fmt(s['band_pct']),
                                                    fmt(s['cv_pct']), fmt(s['hw44_pct']), s['df'], ' | '.join(cells))


def delta_row(R, mid, key):
    """RESULTS.md's median-delta row: method | median delta vs the ref per arm."""
    s = summary_of(R, mid, key)
    if not s:
        return None
    return '| %s | %s |' % (mid, ' | '.join(sgn(((s.get('arms') or {}).get(arm) or {}).get('delta_pct'))
                                            for arm in R['arms']))


def flag_row4(x):
    """RESULTS.md's flag row: run | P util % | E MHz | light share."""
    c = x.get('cov') or {}
    return '| %s | %s | %s | %s |' % (x['name'], fmt(c.get('p_util')), fmt(c.get('e_mhz'), 0), fmt(x.get('ls_T'), 3))


def hits(R, mid, keys):
    out = []
    for key in keys:
        s = summary_of(R, mid, key) or {}
        for arm in R['arms']:
            e = (s.get('arms') or {}).get(arm)
            if e and e.get('ci_excludes_0'):
                out.append('%s %s %s' % (arm, LABEL[key], ci_cell(e)))
    return out


def round_line(R):
    parts = []
    base = R['rounds'][0] if R['rounds'] else '-'
    for key in MAIN:
        t = R['round_test'].get(key)
        if t:
            parts.append('%s: %s; F = %.2f on (%d, %d), p = %s' % (
                LABEL[key], ', '.join('round %s %s %%' % (r, sgn(v)) for r, v in zip(R['rounds'][1:], t['terms_pct'])),
                t['F'], t['df'][0], t['df'][1], pfmt(t['p'])))
    if not parts:
        return 'Round terms: none (%s).' % ('one round' if len(R['rounds']) < 2 else 'B-block could not be fitted')
    return 'Round terms of B-block T-std vs round %s: %s.' % (base, '. '.join(parts))


def render(R):
    out = []
    w = out.append
    ref, arms = R['ref'], R['arms']
    prim = R['decision']['primary']
    runs = R['runs']
    kept = [x for x in runs if x['keep']]
    left = [x for x in runs if not x['keep']]
    ga, gb, gc = R['guards']['a'], R['guards']['b'], R['guards']['c']
    flag = gc['flagged']
    alpha = R.get('alpha', 0.05)
    w('# T-std read-out: %s' % os.path.basename(str(R.get('dir') or '-').rstrip('\\/')))
    w('')
    if R.get('title'):
        w('- title: %s' % R['title'])
    w('- dir: `%s`' % R.get('dir', '-'))
    w('- command: `%s`' % R.get('command', '-'))
    w('- ref **%s** (%s); arms %s; rounds %s; kept %d of %d runs (%s); left out: %s.' % (
        ref, R.get('ref_src', '-'), ', '.join(arms) or 'none', ', '.join(str(r) for r in R['rounds']) or '-',
        len(kept), len(runs), ', '.join('%s %d' % (arm, n) for arm, n in R['n'].items()),
        '; '.join('%s (%s)' % (x['name'], ', '.join(x['why'])) for x in left) or 'none'))
    w('- T split: light = frame time < %s ms; hT_ref = %s (the median heavy-time share of the kept runs).' % (
        ', '.join('%g' % v for v in R.get('light_ms') or []) or '-', fmt(R.get('hT_ref'), 3)))
    w('- G11 power: %s' % R['g11']['line'])
    for nt in R.get('notes') or []:
        w('- note: %s' % nt)
    w('')
    # ---- read-out
    w('## Read-out')
    w('')
    w('- **Primary: %s.** %s' % (prim, R['decision']['why']))
    for key in MAIN:
        s = summary_of(R, prim, key) or {}
        w('- %s vs %s (%s): %s.' % (LABEL[key], ref, prim, '; '.join(
            '%s %s' % (arm, ci_cell((s.get('arms') or {}).get(arm))) for arm in arms) or '-'))
    ntest = len(arms) * len(KEYS)
    w('- CIs that exclude 0 (%s): median ms and fps: %s; tails: %s. That is %d tests (%d arms x 4 metrics) at 5 %%, '
      'so about %.1f can be `*` by chance.' % (prim, ', '.join(hits(R, prim, MAIN)) or 'none',
                                              ', '.join(hits(R, prim, TAILS)) or 'none', ntest, len(arms),
                                              0.05 * ntest))
    if ga and ga.get('F') is not None:
        a_txt = 'light share F = %.2f on (%d, %d), p = %s: %s' % (
            ga['F'], ga['df'][0], ga['df'][1], pfmt(ga['p']), 'WARNING, an arm may move the mix' if ga['warn'] else 'OK')
    else:
        a_txt = 'light share F: -'
    contra = ['%s %s' % (arm, LABEL[key]) for key in MAIN for arm, v in gb.get(key, {}).items() if v != 'agrees']
    b_txt = ('raw CONTRADICTS %s for %s' % (prim, ', '.join(contra))) if contra else 'raw agrees for every arm'
    c_txt = '%d of %d kept runs flagged%s' % (len(flag), len(kept),
                                              (' (%s)' % ', '.join(short(nm) for nm in flag)) if flag else '')
    w('- Guards: (a) %s; (b) %s; (c) %s. G11: %s.' % (a_txt, b_txt, c_txt, R['g11']['status']))
    w('')
    # ---- primary tables
    w('## T-std and B-block T-std')
    w('')
    w(round_line(R))
    w('')
    w('Cells: the GM delta vs %s in %%, with the pooled 95 %% CI; `*` = the CI excludes 0. Bold = the primary. '
      '%s band = (max - min) / median of %s\'s runs (summary.md). 4 vs 4 band = the 95 %% half-width for two arms of '
      '4 runs.' % (ref, ref, ref))
    w('')
    out.extend(table_head(R))
    for key in MAIN:
        for mid in PRIMARIES:
            row = table_row(R, mid, key, bold=(mid == prim))
            if row:
                w(row)
    w('')
    w('### Tails (noisier)')
    w('')
    out.extend(table_head(R))
    for key in TAILS:
        for mid in PRIMARIES:
            row = table_row(R, mid, key, bold=(mid == prim))
            if row:
                w(row)
    w('')
    w('### Median deltas on median ms (the summary.md form)')
    w('')
    verd = []
    for mid in RES_METHODS:
        s = summary_of(R, mid, 'p50_ms') or {}
        for arm in arms:
            e = (s.get('arms') or {}).get(arm)
            if e and e.get('verdict') not in (None, 'within'):
                verd.append('%s %s %s' % (mid, arm, e['verdict']))
    w('Verdicts against each method\'s own %s band: %s.' % (ref, ', '.join(verd) if verd else 'all `within`'))
    w('')
    w('| method | %s |' % ' | '.join(arms))
    w('|---|%s' % ('---|' * len(arms)))
    for mid in RES_METHODS:
        row = delta_row(R, mid, 'p50_ms')
        if row:
            w(row)
    w('')
    # ---- guards
    w('## Guards')
    w('')
    if ga and ga.get('F') is not None:
        w('**(a) Light share** (the share of frames < light_ms) per arm: %s. One-way F = %.2f on (%d, %d), p = %s. %s'
          % (', '.join('%s %s' % (arm, fmt(v, 3)) for arm, v in ga['means'].items()), ga['F'], ga['df'][0],
             ga['df'][1], pfmt(ga['p']),
             ('p < %g: an arm may move the mix, which T-std hides. Read T-light, T-heavy and the raw rows.' % alpha)
             if ga['warn'] else 'No arm moves the mix.'))
        if ga['warn']:
            w('')
            out.extend(table_head(R))
            for key in MAIN:
                for mid in ('T-light', 'T-heavy'):
                    row = table_row(R, mid, key)
                    if row:
                        w(row)
    else:
        w('**(a) Light share:** not available (fewer than 2 arms with kept runs).')
    w('')
    w('**(b) Raw GM deltas** with the pooled 95 %% CI. They must not contradict %s:' % prim)
    w('')
    out.extend(table_head(R))
    for key in MAIN:
        row = table_row(R, 'raw', key)
        if row:
            w(row)
    w('')
    w('Raw CI vs the %s CI (overlap = agrees): %s.' % (prim, '; '.join(
        '%s: %s' % (LABEL[key], ', '.join('%s %s' % (arm, v) for arm, v in gb.get(key, {}).items()) or '-')
        for key in MAIN)))
    w('')
    w('**(c) Host flag** (sys.json window P util >= %g %% and E-core MHz < %g): %d of %d kept runs%s.' % (
        gc['putil'], gc['emhz'], len(flag), len(kept), (' (%s)' % ', '.join(short(nm) for nm in flag)) if flag else ''))
    if flag:
        byname = dict((x['name'], x) for x in runs)
        mids = [mid for mid in RES_METHODS if mid in gc['resid']]
        w('Residual = leave-one-out on median ms: 100 (v / GM of the other runs of its arm - 1) %, + = slower. The flag '
          'is a warning, not a correction.')
        w('')
        w('| run | P util % | E MHz | light share | ' + ' | '.join(mids) + ' |')
        w('|---|---|---|---|' + '---|' * len(mids))
        for nm in flag:
            w('%s %s |' % (flag_row4(byname[nm]), ' | '.join(sgn(gc['resid'][mid].get(nm)) for mid in mids)))
        w('')
        st = gc['stats']
        w('Mean of the flagged runs: %s. RMS of the other kept runs: %s.' % (
            ', '.join('%s %s%s' % (mid, sgn(st[mid]['mean']), '' if mid == 'raw' or st[mid]['share_pct'] is None
                                   else ' (%s %% of raw)' % fmt(st[mid]['share_pct'], 0)) for mid in mids),
            ', '.join('%s %s' % (mid, fmt(st[mid]['rms_others'])) for mid in mids)))
    w('')
    if R['g11']['status'] != 'OK':
        w('## G11 power')
        w('')
        w(R['g11']['line'])
        if R['g11']['per_arm']:
            w('')
            w('Overlay per arm: %s.' % '; '.join('%s %s' % (arm, ', '.join('%s x%d' % kv for kv in c.items()))
                                                 for arm, c in R['g11']['per_arm'].items()))
        w('')
    # ---- runs
    w('## Runs')
    w('')
    flagset = set(flag)
    w('| seq | round | arm | run | kept | raw median ms | T-std median ms | raw fps | T-std fps | light share | '
      'P util % | E MHz | flag | overlay |')
    w('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    for x in runs:
        raw, ts, cv = x.get('raw') or {}, x.get('t_std') or {}, x.get('cov') or {}
        ov = ((x.get('power') or {}).get('overlay') or {}).get('value') or '-'
        w('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
            x.get('seq'), x.get('round'), x['arm'], x['name'], 'yes' if x['keep'] else 'no: ' + ', '.join(x['why']),
            fmt(raw.get('p50_ms'), 3), fmt(ts.get('p50_ms'), 3), fmt(raw.get('fps')), fmt(ts.get('fps')),
            fmt(x.get('ls_T'), 3), fmt(cv.get('p_util')), fmt(cv.get('e_mhz'), 0),
            'yes' if x['name'] in flagset else '', ov))
    w('')
    return '\n'.join(out) + '\n'


# ---------------------------------------------------------------- json and main
def run_rec(x, flagset):
    rec = dict((k, x.get(k)) for k in ('seq', 'round', 'arm', 'rep', 'name', 'scored', 'valid', 'excluded', 'keep',
                                       'why', 'hT', 'ls_T', 'ls_runner', 'light_ms', 'window_s', 'power'))
    for f in ('raw', 't_std', 't_L', 't_H'):
        v = x.get(f)
        rec[f] = dict((k, v.get(k)) for k, _, _ in KEYS) if isinstance(v, dict) else None
    rec['cov'] = dict((k, (x.get('cov') or {}).get(k)) for k in ('p_util', 'e_mhz', 'e_util', 'cpu_util', 'cores'))
    rec['flag'] = x['name'] in flagset
    return rec


def to_json(R):
    out = dict((k, R.get(k)) for k in ('tool', 'dir', 'title', 'command', 'params', 'ref', 'ref_src', 'order', 'arms',
                                       'n', 'rounds', 'unbalanced_rounds', 'alpha', 'hT_ref', 'light_ms', 'decision',
                                       'round_test', 'guards', 'g11', 'notes'))
    out['methods'] = R['methods']
    flagset = set(R['guards']['c']['flagged'])
    out['runs'] = [run_rec(x, flagset) for x in R['runs']]
    return out


def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('dir', help='run-matrix.ps1 output dir (matrix.json, results.csv, runs/)')
    ap.add_argument('-o', '--out', help='write the markdown here (without -o: stdout)')
    ap.add_argument('--json', help='write the numbers as json here')
    ap.add_argument('--ref', help='reference arm (default: matrix.json)')
    ap.add_argument('--alpha', type=float, default=0.05, help='level of the round-terms test and the light-share guard')
    ap.add_argument('--putil', type=float, default=90.0, help='host flag: sys.json window P util at or above this')
    ap.add_argument('--emhz', type=float, default=600.0, help='host flag: and E-core MHz below this')
    ap.add_argument('--overlay', help='keep only runs whose window ran on this power overlay, unchanged (G11 MIXED)')
    ap.add_argument('--rounds', help='keep only these rounds, e.g. 2,3 (G11 MIXED)')
    ap.add_argument('--drop', help='leave out these runs (name, or name without the HHMM- prefix), comma-separated')
    ap.add_argument('--light-ms', type=float, default=None, help='T split in ms (default: frames.json light_ms, 4.5)')
    ap.add_argument('--all', action='store_true', help='keep runs that are not valid timing')
    ap.add_argument('--normal-priority', action='store_true', help="don't lower this process to Below Normal")
    return ap.parse_args(argv)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    a = parse_args(argv)
    if not a.normal_priority:
        below_normal()
    command = 'python -B build\\agent7\\w4b-noise\\readout.py ' + ' '.join(argv)
    R = analyse(a.dir, a, command)
    text = render(R)
    if a.out:
        with open(a.out, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)
        head = text.split('\n## T-std and B-block T-std', 1)[0]
        sys.stdout.write(head.rstrip('\n') + '\n\nwrote %s\n' % a.out)
    else:
        sys.stdout.write(text)
    if a.json:
        with open(a.json, 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(to_json(R), fh, indent=1, default=str)
        sys.stdout.write('wrote %s\n' % a.json)
    return 0


if __name__ == '__main__':
    sys.exit(main())

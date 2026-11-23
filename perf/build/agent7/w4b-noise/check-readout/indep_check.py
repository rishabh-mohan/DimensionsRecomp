#!/usr/bin/env python3
"""Independent checker for Agent 7's task #14 (T-std read-out kit), checks 2-4.

Imports nothing from the kit (readout.py, noise_methods.py, noise_case.py, repeats.py). The T975 table is parsed
from noise_methods.py's source text (ast.literal_eval), not imported. F, t and chi-square use this file's own code
(numeric integration of the densities; closed form for chi-square on an even df). Stdlib only, one thread.
Read-only; writes only check-readout/indep.txt.
"""
import ast
import csv
import datetime
import json
import math
import os
import re
import statistics
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(KIT, '..', '..', '..'))
WDIR = {'W4b': os.path.join(REPO, 'build', 'agent8', 'matrix', '20261122-1541'),
        'W5': os.path.join(REPO, 'build', 'agent8', 'matrix', '20261122-1756')}
TAG = {'W4b': 'w4b', 'W5': 'w5'}
KEYS = (('p50_ms', -1, 'median ms'), ('fps', 1, 'fps'), ('p99_ms', -1, 'p99 ms'), ('low1_fps', 1, '1 % low fps'))
LABEL = dict((k, l) for k, _, l in KEYS)
SIGN = dict((k, s) for k, s, _ in KEYS)
BLOCK = 'B-block T-std'
OUT = []
NFAIL = [0]
NPASS = [0]


def rec(ok, name, detail=''):
    st = 'PASS' if ok else 'FAIL'
    if ok:
        NPASS[0] += 1
    else:
        NFAIL[0] += 1
    OUT.append('%s %s%s' % (st, name, (' | ' + detail) if detail else ''))


def info(msg):
    OUT.append('INFO ' + msg)


def read(p):
    with open(p, encoding='utf-8-sig') as f:
        return f.read()


def readj(p):
    with open(p, encoding='utf-8-sig') as f:
        return json.load(f)


def fmt(v, nd=1):
    return '-' if v is None else '%.*f' % (nd, v)


def sgn(v, nd=1):
    return '-' if v is None else '%+.*f' % (nd, v)


def pfmt(p):
    return '< 0.001' if p < 0.001 else '%.3f' % p


def norm(s):
    return s.replace('**', '').replace('\\*', '*').strip()


def close(a, b, rel=1e-9, ab=1e-9):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= max(ab, rel * max(abs(a), abs(b)))


# ------------------------------------------------ t table (parsed from the source text, not imported)
SRC = read(os.path.join(KIT, 'noise_methods.py'))
T975 = ast.literal_eval(re.search(r'^T975 = (\{.*?\})', SRC, re.S | re.M).group(1))


def t975(df):
    """As described: the table entry at the next lower df between entries (df > 30 is not needed here)."""
    if df is None or df < 1:
        return None
    if df > 30:
        return 1.96 + (T975[30] - 1.96) * 30.0 / df
    return T975[max(k for k in T975 if k <= df)]


# ------------------------------------------------ own distributions
def simpson(f, a, b, n=4000):
    n += n % 2
    h = (b - a) / n
    s = f(a) + f(b)
    for i in range(1, n):
        s += (4.0 if i % 2 else 2.0) * f(a + i * h)
    return s * h / 3.0


def _fc(d1, d2):
    return math.exp(0.5 * d1 * math.log(d1 / d2) - (math.lgamma(d1 / 2.0) + math.lgamma(d2 / 2.0)
                                                     - math.lgamma((d1 + d2) / 2.0)))


def f_sf_a(x, d1, d2, n=20000):
    """P(F(d1, d2) > x) = 1 - the F density integrated over [0, x] (x = y^2, smooth at 0)."""
    c = _fc(d1, d2)
    g = lambda y: 2.0 * c * y ** (d1 - 1) * (1.0 + d1 * y * y / d2) ** (-(d1 + d2) / 2.0)
    return 1.0 - simpson(g, 0.0, math.sqrt(x), n)


def f_sf_b(x, d1, d2, n=20000):
    """P(F(d1, d2) > x): the F density integrated over [x, inf) with z = x + u / (1 - u)."""
    c = _fc(d1, d2)

    def g(u):
        if u >= 1.0:
            return 0.0
        z = x + u / (1.0 - u)
        return c * z ** (d1 / 2.0 - 1.0) * (1.0 + d1 * z / d2) ** (-(d1 + d2) / 2.0) / (1.0 - u) ** 2
    return simpson(g, 0.0, 1.0, n)


def t_cdf(t, df, n=2000):
    c = math.exp(math.lgamma((df + 1) / 2.0) - math.lgamma(df / 2.0)) / math.sqrt(df * math.pi)
    v = simpson(lambda x: c * (1.0 + x * x / df) ** (-(df + 1) / 2.0), 0.0, abs(t), n)
    return 0.5 + v if t >= 0 else 0.5 - v


_TQ = {}


def t_ppf(p, df):
    if (p, df) not in _TQ:
        lo, hi = 0.0, 60.0
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if t_cdf(mid, df, 6000 if df < 3 else 2000) < p:
                lo = mid
            else:
                hi = mid
        _TQ[(p, df)] = 0.5 * (lo + hi)
    return _TQ[(p, df)]


def chi2_cdf_even(x, df):
    k = df // 2
    return 1.0 - math.exp(-x / 2.0) * sum((x / 2.0) ** j / math.factorial(j) for j in range(k))


def chi2_ppf_even(p, df):
    lo, hi = 0.0, 10.0 * df + 100.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if chi2_cdf_even(mid, df) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ------------------------------------------------ own estimators
def oneway(vals, ref, arms):
    """vals {arm: [(name, v)]}: pooled within-arm SD of ln v, df = runs - arms, GM deltas + CI, band, median deltas."""
    ss, df = 0.0, 0
    for lst in vals.values():
        lv = [math.log(v) for _, v in lst]
        if len(lv) >= 2:
            m = sum(lv) / len(lv)
            ss += sum((u - m) ** 2 for u in lv)
            df += len(lv) - 1
    sd = math.sqrt(ss / df)
    t = t975(df)
    rv = [v for _, v in vals[ref]]
    rmed = statistics.median(rv)
    lref = sum(math.log(v) for v in rv) / len(rv)
    S = {'sd': sd, 'df': df, 'band': 100.0 * (max(rv) - min(rv)) / rmed,
         'hw44': 100.0 * (math.exp(t * sd * math.sqrt(0.5)) - 1.0), 'arms': {}, 'adj': vals}
    for a in arms:
        if a not in vals:
            continue
        av = [v for _, v in vals[a]]
        dl = sum(math.log(v) for v in av) / len(av) - lref
        hw = t * sd * math.sqrt(1.0 / len(av) + 1.0 / len(rv))
        S['arms'][a] = {'n': len(av), 'gm': 100.0 * (math.exp(dl) - 1.0), 'lo': 100.0 * (math.exp(dl - hw) - 1.0),
                        'hi': 100.0 * (math.exp(dl + hw) - 1.0), 'excl': dl - hw > 0 or dl + hw < 0,
                        'delta': 100.0 * (statistics.median(av) - rmed) / rmed}
    return S


def gj_inverse(A):
    k = len(A)
    M = [[float(v) for v in A[i]] + [1.0 if i == j else 0.0 for j in range(k)] for i in range(k)]
    for c in range(k):
        p = max(range(c, k), key=lambda r: abs(M[r][c]))
        if abs(M[p][c]) < 1e-12:
            return None
        M[c], M[p] = M[p], M[c]
        pv = M[c][c]
        M[c] = [v / pv for v in M[c]]
        for r in range(k):
            if r != c and M[r][c] != 0.0:
                q = M[r][c]
                M[r] = [u - q * w for u, w in zip(M[r], M[c])]
    return [row[k:] for row in M]


def twoway(kv, ref, order, rounds):
    """kv [(name, arm, round, v)]: OLS of ln v on 1 + arm dummies (vs ref) + round dummies (vs the first round).
    Arm effect, its CI from (X'X)^-1, round terms b, residual SD and df; adjusted values ln v - (x - xbar) b."""
    arms = [a for a in order if a != ref and any(x[1] == a for x in kv)]
    rr = list(rounds[1:])
    X = [[1.0] + [1.0 if x[1] == a else 0.0 for a in arms] + [1.0 if x[2] == r else 0.0 for r in rr] for x in kv]
    y = [math.log(x[3]) for x in kv]
    N, P = len(X), len(X[0])
    XtX = [[sum(X[i][j] * X[i][l] for i in range(N)) for l in range(P)] for j in range(P)]
    Xty = [sum(X[i][j] * y[i] for i in range(N)) for j in range(P)]
    inv = gj_inverse(XtX)
    beta = [sum(inv[j][l] * Xty[l] for l in range(P)) for j in range(P)]
    res = [y[i] - sum(X[i][j] * beta[j] for j in range(P)) for i in range(N)]
    df = N - P
    sd = math.sqrt(sum(e * e for e in res) / df)
    t = t975(df)
    o = 1 + len(arms)
    b = beta[o:]
    xbar = [sum(X[i][o + j] for i in range(N)) / N for j in range(len(rr))]
    adj = {}
    for i, x in enumerate(kv):
        la = y[i] - sum((X[i][o + j] - xbar[j]) * b[j] for j in range(len(rr)))
        adj.setdefault(x[1], []).append((x[0], math.exp(la)))
    rv = [v for _, v in adj[ref]]
    rmed = statistics.median(rv)
    S = {'sd': sd, 'df': df, 'b': b, 'band': 100.0 * (max(rv) - min(rv)) / rmed,
         'hw44': 100.0 * (math.exp(t * sd * math.sqrt(0.5)) - 1.0), 'arms': {}, 'adj': adj, 'rss': sd * sd * df}
    for i, a in enumerate(arms):
        dl, vf = beta[1 + i], inv[1 + i][1 + i]
        hw = t * sd * math.sqrt(vf)
        av = [v for _, v in adj[a]]
        S['arms'][a] = {'n': len(av), 'gm': 100.0 * (math.exp(dl) - 1.0), 'lo': 100.0 * (math.exp(dl - hw) - 1.0),
                        'hi': 100.0 * (math.exp(dl + hw) - 1.0), 'excl': dl - hw > 0 or dl + hw < 0,
                        'delta': 100.0 * (statistics.median(av) - rmed) / rmed, 'varf': vf}
    return S


def loo(lst, sign):
    out = {}
    if len(lst) < 2:
        return out
    logs = [math.log(v) for _, v in lst]
    for i, (nm, _) in enumerate(lst):
        d = logs[i] - sum(u for j, u in enumerate(logs) if j != i) / (len(logs) - 1)
        out[nm] = 100.0 * (math.exp(-d if sign > 0 else d) - 1.0)
    return out


def cell(e):
    return '%s [%s, %s]%s' % (sgn(e['gm']), sgn(e['lo']), sgn(e['hi']), ' *' if e['excl'] else '')


def row_of(mid, key, S, arms):
    return '| %s | %s | %s | %s | %s | %d | %s |' % (mid, LABEL[key], fmt(S['band']), fmt(100.0 * S['sd']),
                                                    fmt(S['hw44']), S['df'], ' | '.join(cell(S['arms'][a]) for a in arms))


# ------------------------------------------------ check 2: re-run diffs
def jdiff(a, b, path=''):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                out.append('%s/%s missing on one side' % (path, k))
            else:
                out += jdiff(a[k], b[k], '%s/%s' % (path, k))
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append('%s: len %d vs %d' % (path, len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            out += jdiff(x, y, '%s[%d]' % (path, i))
    elif isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
        pass
    elif a != b or type(a) != type(b):
        out.append('%s: %r vs %r' % (path, a, b))
    return out


def check2():
    for tag in ('W4b', 'W5'):
        t = TAG[tag]
        a = read(os.path.join(KIT, 'readout-%s.md' % t)).split('\n')
        b = read(os.path.join(HERE, 'check-%s.md' % t)).split('\n')
        diffs = [i for i in range(max(len(a), len(b))) if (a[i] if i < len(a) else None) != (b[i] if i < len(b) else None)]
        ok = len(a) == len(b) and all(a[i].startswith('- command: ') and b[i].startswith('- command: ') for i in diffs)
        rec(ok, '2 %s md re-run vs readout-%s.md: only the "- command:" line differs' % (tag, t),
            '%d lines each side %d/%d; differing lines: %s' % (len(diffs), len(a), len(b),
                                                              ', '.join(str(i + 1) for i in diffs) or 'none'))
        for i in diffs:
            info('2 %s md line %d: kit  = %s' % (tag, i + 1, a[i] if i < len(a) else '<none>'))
            info('2 %s md line %d: mine = %s' % (tag, i + 1, b[i] if i < len(b) else '<none>'))
        ja = readj(os.path.join(KIT, 'readout-%s.json' % t))
        jb = readj(os.path.join(HERE, 'check-%s.json' % t))
        d = jdiff(ja, jb)
        bad = [x for x in d if not (x.startswith('/command') or x.startswith('/params'))]
        rec(not bad, '2 %s json re-run vs readout-%s.json: only command / params differ' % (tag, t),
            '%d differing paths, %d outside command/params%s' % (len(d), len(bad),
                                                                 (': ' + '; '.join(bad[:10])) if bad else ''))
        for x in d:
            info('2 %s json diff %s' % (tag, x))


# ------------------------------------------------ check 3a: RESULTS.md rows
def section(lines, start):
    i = next(i for i, l in enumerate(lines) if l.startswith(start))
    j = next((k for k in range(i + 1, len(lines)) if lines[k].startswith('## ')), len(lines))
    return lines[i:j]


def check3a():
    res = read(os.path.join(KIT, 'RESULTS.md')).splitlines()
    mains = [(m, k) for m in ('raw', 'T-std', BLOCK) for k in ('median ms', 'fps')]
    spec = {'W4b': ('## W4b', set(mains), {'raw', 'T-std', BLOCK}, 6, 3),
            'W5': ('## W5', set(mains) | {('T-std', 'p99 ms'), ('T-std', '1 % low fps')}, {'raw', 'T-std', BLOCK}, 8, 2)}
    for tag, (start, want_tab, want_dl, ntab, ndl) in spec.items():
        J = readj(os.path.join(KIT, 'readout-%s.json' % TAG[tag]))
        narms = len(J['arms'])
        md = set(norm(l) for l in read(os.path.join(KIT, 'readout-%s.md' % TAG[tag])).splitlines())
        tab, dl = [], []
        for l in section(res, start):
            if not l.startswith('|'):
                continue
            n = norm(l)
            cells = [c.strip() for c in n.strip('|').split('|')]
            if len(cells) == 6 + narms and (cells[0], cells[1]) in want_tab:
                tab.append(n)
            elif len(cells) == 1 + narms and cells[0] in want_dl:
                dl.append(n)
        rec(len(tab) == ntab and len(dl) == ndl, '3a %s RESULTS.md rows found' % tag,
            '%d table rows (want %d), %d median-delta rows (want %d)' % (len(tab), ntab, len(dl), ndl))
        for n in tab + dl:
            rec(n in md, '3a %s row verbatim in readout-%s.md' % (tag, TAG[tag]), n)


# ------------------------------------------------ check 3b-3d per window
def check3(tag):
    J = readj(os.path.join(KIT, 'readout-%s.json' % TAG[tag]))
    mdtext = read(os.path.join(KIT, 'readout-%s.md' % TAG[tag]))
    md = set(norm(l) for l in mdtext.splitlines())
    ref, order, arms, rounds = J['ref'], J['order'], J['arms'], J['rounds']
    M = J['methods']
    prim = J['decision']['primary']
    kept = [x for x in J['runs'] if x['keep']]
    # ---- 3b round test from the json summaries
    for key in ('p50_ms', 'fps'):
        s1, s2 = M['T-std'][key], M[BLOCK][key]
        k = len(rounds) - 1
        F = ((s1['sd_ln'] ** 2 * s1['df'] - s2['sd_ln'] ** 2 * s2['df']) / k) / (s2['sd_ln'] ** 2)
        pa, pb = f_sf_a(F, k, s2['df']), f_sf_b(F, k, s2['df'])
        rt = J['round_test'][key]
        extra = ''
        if k == 2:
            pc = (1.0 + 2.0 * F / s2['df']) ** (-s2['df'] / 2.0)
            extra = '; d1 = 2 closed form p = %.10f' % pc
        rec(close(F, rt['F'], 1e-9) and rt['df'] == [k, s2['df']] and abs(pa - rt['p']) < 1e-7 and abs(pb - rt['p']) < 1e-7,
            '3b %s round test on %s: F and p recomputed' % (tag, LABEL[key]),
            'mine F = %.6f on (%d, %d), p = %.8f (density 0..F) / %.8f (density F..inf)%s; json F = %.6f, p = %.8f, '
            'df %s' % (F, k, s2['df'], pa, pb, extra, rt['F'], rt['p'], rt['df']))
        if key == 'p50_ms':
            want = BLOCK if tag == 'W4b' else 'T-std'
            mine = BLOCK if pa < 0.05 else 'T-std'
            rec(mine == want == prim and rt['block'] == (pa < 0.05), '3b %s decision' % tag,
                'p = %.4f -> %s; json decision %s; expected %s' % (pa, mine, prim, want))
            txt = 'F = %.2f on (%d, %d), p = %s' % (F, k, s2['df'], pfmt(pa))
            rec(txt in mdtext, '3b %s md prints "%s"' % (tag, txt))
    # ---- 3c CI formula on the json summaries (primary tables, every arm)
    for mid in ('T-std', BLOCK):
        for key in ('p50_ms', 'fps'):
            s = M[mid][key]
            t = t975(s['df'])
            nref = s['arms'][ref]['n']
            for a in arms:
                e = s['arms'][a]
                dl = math.log1p(e['gm_delta_pct'] / 100.0)
                hw = t * s['sd_ln'] * math.sqrt(1.0 / e['n'] + 1.0 / nref)
                lo, hi = 100.0 * (math.exp(dl - hw) - 1.0), 100.0 * (math.exp(dl + hw) - 1.0)
                ok = close(lo, e['ci_pct'][0], 1e-9, 1e-9) and close(hi, e['ci_pct'][1], 1e-9, 1e-9)
                d = ('%s %s %s: df %d t %.3f sd %.6f n %d/%d -> [%.4f, %.4f]; json [%.4f, %.4f]'
                     % (mid, LABEL[key], a, s['df'], t, s['sd_ln'], e['n'], nref, lo, hi, e['ci_pct'][0], e['ci_pct'][1]))
                if ok:
                    rec(True, '3c %s CI = exp(dl +- t sd sqrt(1/n_a + 1/n_ref)) - 1' % tag, d)
                else:
                    info('3c %s simple CI formula does not hold for %s (checked below with the OLS variance)' % (tag, d))
    # ---- 3d own recompute from the per-run values (raw / T-std one-way, B-block by own OLS)
    for key, sign, _ in KEYS:
        for mid, field in (('raw', 'raw'), ('T-std', 't_std')):
            vals = {}
            for x in kept:
                v = (x.get(field) or {}).get(key)
                if v is not None and v > 0:
                    vals.setdefault(x['arm'], []).append((x['name'], v))
            S = oneway(vals, ref, arms)
            js = M[mid][key]
            ok = close(S['sd'], js['sd_ln']) and S['df'] == js['df'] and close(S['band'], js['band_pct']) and close(
                S['hw44'], js['hw44_pct']) and all(
                close(S['arms'][a]['gm'], js['arms'][a]['gm_delta_pct']) and close(S['arms'][a]['lo'], js['arms'][a]['ci_pct'][0])
                and close(S['arms'][a]['hi'], js['arms'][a]['ci_pct'][1]) and close(S['arms'][a]['delta'], js['arms'][a]['delta_pct'])
                and S['arms'][a]['excl'] == js['arms'][a]['ci_excludes_0'] for a in arms)
            row = row_of(mid, key, S, arms)
            printed = row in md
            need = (mid == 'T-std') or key in ('p50_ms', 'fps')
            rec(ok and (printed or not need), '3d %s own one-way %s %s vs json%s' % (tag, mid, LABEL[key],
                                                                                   ' and md row' if need else ''),
                'sd %.6f df %d; %s' % (S['sd'], S['df'], row if need else 'raw tails are not printed'))
            if mid == 'T-std':
                M.setdefault('_mine', {})[key] = S
            if key == 'p50_ms':
                drow = '| %s | %s |' % (mid, ' | '.join(sgn(S['arms'][a]['delta']) for a in arms))
                rec(drow in md, '3d %s own median-delta row %s' % (tag, mid), drow)
                M.setdefault('_raw', {})[mid] = S
        kv = [(x['name'], x['arm'], x['round'], x['t_std'][key]) for x in kept
              if (x.get('t_std') or {}).get(key) is not None and x['t_std'][key] > 0]
        B = twoway(kv, ref, order, rounds)
        js = M[BLOCK][key]
        ok = close(B['sd'], js['sd_ln']) and B['df'] == js['df'] and close(B['band'], js['band_pct']) and close(
            B['hw44'], js['hw44_pct']) and all(close(u, v) for u, v in zip(B['b'], js['b'])) and all(
            close(B['arms'][a]['gm'], js['arms'][a]['gm_delta_pct']) and close(B['arms'][a]['lo'], js['arms'][a]['ci_pct'][0])
            and close(B['arms'][a]['hi'], js['arms'][a]['ci_pct'][1]) and close(B['arms'][a]['delta'], js['arms'][a]['delta_pct'])
            and B['arms'][a]['excl'] == js['arms'][a]['ci_excludes_0'] for a in arms)
        row = row_of(BLOCK, key, B, arms)
        vf = ', '.join('%s %.4f (1/n_a + 1/n_ref = %.4f)' % (a, B['arms'][a]['varf'],
                                                            1.0 / B['arms'][a]['n'] + 1.0 / len(B['adj'][ref])) for a in arms)
        rec(ok and row in md, '3d %s own two-way OLS (B-block T-std) %s vs json and md row' % (tag, LABEL[key]),
            'sd %.6f df %d b %s; var factors: %s; %s' % (B['sd'], B['df'], ', '.join('%.5f' % u for u in B['b']), vf, row))
        if key == 'p50_ms':
            drow = '| %s | %s |' % (BLOCK, ' | '.join(sgn(B['arms'][a]['delta']) for a in arms))
            rec(drow in md, '3d %s own median-delta row %s' % (tag, BLOCK), drow)
            M['_raw'][BLOCK] = B
            terms = ', '.join('round %s %s %%' % (r, sgn(100.0 * (math.exp(u) - 1.0))) for r, u in zip(rounds[1:], B['b']))
            rec(('median ms: ' + terms) in mdtext, '3d %s round terms 100 (e^b - 1) from own OLS' % tag,
                '%s; 100 |b| = %s' % (terms, ' / '.join('%.2f' % abs(100.0 * u) for u in B['b'])))
            # F from the residual SS of the two own fits
            S1 = M['_mine']['p50_ms']
            k = len(rounds) - 1
            F2 = ((S1['sd'] ** 2 * S1['df'] - B['rss']) / k) / (B['rss'] / B['df'])
            rec(close(F2, J['round_test']['p50_ms']['F'], 1e-8), '3d %s round-test F from own one-way and own OLS' % tag,
                'F = %.6f' % F2)
    # ---- guard (a) light share F and p (own one-way ANOVA)
    g = {}
    for x in kept:
        g.setdefault(x['arm'], []).append(x['ls_T'])
    allv = [v for l in g.values() for v in l]
    m = sum(allv) / len(allv)
    ssb = sum(len(l) * (sum(l) / len(l) - m) ** 2 for l in g.values())
    ssw = sum(sum((v - sum(l) / len(l)) ** 2 for v in l) for l in g.values())
    d1, d2 = len(g) - 1, len(allv) - len(g)
    Fa = (ssb / d1) / (ssw / d2)
    pa = f_sf_a(Fa, d1, d2)
    txt = 'One-way F = %.2f on (%d, %d), p = %s.' % (Fa, d1, d2, pfmt(pa))
    ga = J['guards']['a']
    rec(txt in mdtext and close(Fa, ga['F'], 1e-9) and abs(pa - ga['p']) < 1e-7, '3d %s guard (a) light share' % tag,
        '%s json F %.6f p %.6f' % (txt, ga['F'], ga['p']))
    # ---- guard (c) flagged runs and residuals
    flag = [x['name'] for x in J['runs'] if x['keep'] and x['cov'].get('p_util') is not None
            and x['cov'].get('e_mhz') is not None and x['cov']['p_util'] >= 90.0 and x['cov']['e_mhz'] < 600.0]
    rec(flag == J['guards']['c']['flagged'], '3d %s guard (c) flagged runs (P util >= 90, E MHz < 600, kept)' % tag,
        ', '.join(flag))
    res = {}
    for mid in ('raw', 'T-std', BLOCK):
        S = M['_raw'][mid]
        r = {}
        for a, lst in S['adj'].items():
            r.update(loo(lst, -1))
        res[mid] = r
    byname = dict((x['name'], x) for x in J['runs'])
    okrows = []
    for nm in flag:
        x = byname[nm]
        line = '| %s | %s | %s | %s | %s |' % (nm, fmt(x['cov']['p_util']), fmt(x['cov']['e_mhz'], 0), fmt(x['ls_T'], 3),
                                              ' | '.join(sgn(res[mid].get(nm)) for mid in ('raw', 'T-std', BLOCK)))
        okrows.append((line in md, line))
    rec(all(o for o, _ in okrows), '3d %s guard (c) flag rows with own LOO residuals' % tag,
        ' ; '.join(l for _, l in okrows))
    parts, rms = [], []
    rawm = sum(res['raw'][n] for n in flag) / len(flag)
    for mid in ('raw', 'T-std', BLOCK):
        mn = sum(res[mid][n] for n in flag) / len(flag)
        oth = [v for n, v in res[mid].items() if n not in flag]
        parts.append('%s %s%s' % (mid, sgn(mn), '' if mid == 'raw' else ' (%s %% of raw)' % fmt(100.0 * mn / rawm, 0)))
        rms.append('%s %s' % (mid, fmt(math.sqrt(sum(v * v for v in oth) / len(oth)))))
    line = 'Mean of the flagged runs: %s. RMS of the other kept runs: %s.' % (', '.join(parts), ', '.join(rms))
    rec(line in mdtext, '3d %s guard (c) flagged mean / RMS line' % tag, line)


# ------------------------------------------------ check 4: REPEATS.md
def md_table_after(lines, marker):
    i = next(i for i, l in enumerate(lines) if l.strip().startswith(marker))
    j = next(j for j in range(i + 1, len(lines)) if lines[j].startswith('| repeats |'))
    head = [c.strip() for c in lines[j].strip().strip('|').split('|')]
    As = [int(re.match(r'(\d+) arms', c).group(1)) for c in head[1:]]
    cells, k = {}, j + 2
    while k < len(lines) and lines[k].startswith('|'):
        row = [c.strip() for c in lines[k].strip().strip('|').split('|')]
        for A, c in zip(As, row[1:]):
            cells[(A, int(row[0]))] = c
        k += 1
    return cells


def parse_t(s):
    for f in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.datetime.strptime(str(s).strip(), f)
        except ValueError:
            pass
    return None


def check4():
    RJ = readj(os.path.join(KIT, 'repeats.json'))
    rtext = read(os.path.join(KIT, 'REPEATS.md'))
    L = rtext.splitlines()
    J5 = readj(os.path.join(KIT, 'readout-w5.json'))
    J4 = readj(os.path.join(KIT, 'readout-w4b.json'))
    cv = RJ['cv']
    s = dict((k, cv[k]['s']) for k in ('p50_ms', 'fps', 'p99_ms', 'low1_fps'))
    # ---- s vs the read-out
    for k in s:
        rec(s[k] == J5['methods']['T-std'][k]['sd_ln'] and cv[k]['df'] == J5['methods']['T-std'][k]['df'] == 10,
            '4 s(%s) = readout-w5.json methods[T-std][%s].sd_ln' % (k, k), '%.12f, df %d' % (s[k], cv[k]['df']))
    # ---- unflagged-run s, own pooled SD
    flag = set(J5['guards']['c']['flagged'])
    calm = [x for x in J5['runs'] if x['keep'] and x['name'] not in flag]
    for k, want in (('p50_ms', '1.5'), ('fps', '1.2')):
        g = {}
        for x in calm:
            g.setdefault(x['arm'], []).append(math.log(x['t_std'][k]))
        ss = sum(sum((u - sum(l) / len(l)) ** 2 for u in l) for l in g.values())
        df = sum(len(l) - 1 for l in g.values())
        sc = math.sqrt(ss / df)
        rec(len(calm) == 12 and df == 7 and close(sc, cv[k]['s_calm'], 1e-12) and fmt(100 * sc) == want,
            '4 unflagged s (%s) over the 12 kept runs not flagged' % k,
            '%d runs, df %d, s = %.6f (%.1f %%); repeats.json s_calm %.6f' % (len(calm), df, sc, 100 * sc, cv[k]['s_calm']))
    # ---- T975 sanity (own t quantile)
    bad = [(d, v, t_ppf(0.975, d)) for d, v in sorted(T975.items()) if abs(t_ppf(0.975, d) - v) > 6e-4]
    rec(not bad, '4 T975 table entries vs own t quantile (to 3 decimals)', 'bad: %s' % bad if bad else
        '%d entries; df 24 uses %.3f' % (len(T975), t975(24)))
    # ---- timing from run.json
    W5 = WDIR['W5']
    with open(os.path.join(W5, 'results.csv'), encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    tt = []
    for r in rows:
        name = os.path.basename(r['run_dir'].rstrip('\\/'))
        j = readj(os.path.join(W5, 'runs', name, 'run.json'))
        tt.append({'name': name, 'scored': r['scored'].strip().lower() == 'true', 'start': parse_t(j.get('start')),
                   'end': parse_t(j.get('end')), 'raw_start': j.get('start'), 'raw_end': j.get('end')})
    sc = sorted([t for t in tt if t['scored']], key=lambda t: t['start'])
    cold = sorted([t for t in tt if not t['scored']], key=lambda t: t['start'])
    cold_slot = (sc[0]['start'] - cold[0]['start']).total_seconds()
    slot = (sc[-1]['start'] - sc[0]['start']).total_seconds() / (len(sc) - 1)
    last = (sc[-1]['end'] - sc[-1]['start']).total_seconds()
    total = (sc[-1]['end'] - cold[0]['start']).total_seconds()
    runmean = sum((t['end'] - t['start']).total_seconds() for t in sc) / len(sc)
    info('4 timing: %d scored + %d cold; cold %s .. first scored %s; last scored %s .. %s'
         % (len(sc), len(cold), cold[0]['raw_start'], sc[0]['raw_start'], sc[-1]['raw_start'], sc[-1]['raw_end']))
    tm = RJ['timing']
    rec(close(cold_slot, tm['cold_slot_s']) and close(slot, tm['slot_s']) and close(last, tm['last_s'])
        and close(total, tm['total_s']) and close(runmean, tm['run_mean_s']) and len(sc) == tm['runs'] == 15,
        '4 timing from run.json = repeats.json timing',
        'cold slot %.3f s, slot %.4f s, last %.3f s, run mean %.3f s, total %.3f s' % (cold_slot, slot, last, runmean, total))

    def minutes(A, n):
        return (cold_slot + (A * n - 1) * slot + last) / 60.0
    rec('%.1f' % (total / 60.0) == '33.9' and '%.1f' % minutes(5, 3) == '33.9' and close(minutes(5, 3) * 60, total, 1e-9),
        '4 measured total 33.9 min = model for 15 runs', 'measured %.4f min, model %.4f min' % (total / 60, minutes(5, 3)))
    base = (cold_slot + last - slot) / 60.0
    sent = ("From W5's run.json start/end: the cold run's slot %.2f min, then one slot of %.2f min per scored run (start "
            "to start; a run lasts %.0f s on average, the gap is %.0f s), and the last run %.2f min. Window = cold slot + "
            "(A n - 1) slots + the last run = %.2f + %.2f x A n min. Check: %d runs give %.1f min; measured %.1f min "
            "(%s-%s)." % (cold_slot / 60, slot / 60, runmean, slot - runmean, last / 60, base, slot / 60, len(sc),
                          minutes(5, 3), total / 60, cold[0]['start'].strftime('%H:%M:%S'),
                          sc[-1]['end'].strftime('%H:%M:%S')))
    rec(sent in rtext, '4 section 2 sentence rebuilt from run.json', sent)

    def hw(sv, n, df):
        return 100.0 * (math.exp(t975(df) * sv * math.sqrt(2.0 / n)) - 1.0)

    def mde(sv, n, df):
        return 100.0 * (math.exp((t975(df) + t_ppf(0.80, df)) * sv * math.sqrt(2.0 / n)) - 1.0)
    tabs = {
        'median ms': ('**median ms** (± %, df):', lambda A, n: '±%.1f (%d)' % (hw(s['p50_ms'], n, A * (n - 1)), A * (n - 1))),
        'fps': ('**fps** (± %, df):', lambda A, n: '±%.1f (%d)' % (hw(s['fps'], n, A * (n - 1)), A * (n - 1))),
        'tails': ('**Tails**', lambda A, n: '±%.1f / ±%.1f' % (hw(s['p99_ms'], n, A * (n - 1)),
                                                            hw(s['low1_fps'], n, A * (n - 1)))),
        'minutes': ('Minutes (scored runs):', lambda A, n: '%.1f (%d)' % (minutes(A, n), A * n)),
        'B-block': ('B-block spends', lambda A, n: '±%.1f (%d)' % (hw(s['p50_ms'], n, (A - 1) * (n - 1)),
                                                                 (A - 1) * (n - 1))),
        'MDE': ('100 (exp((t975 + t0.80)', lambda A, n: '%.1f' % mde(s['p50_ms'], n, A * (n - 1))),
        'CV 1/2/3': ('± % at CV', lambda A, n: ' / '.join('%.1f' % hw(c / 100.0, n, A * (n - 1)) for c in (1, 2, 3))),
    }
    for name, (marker, fn) in tabs.items():
        cells = md_table_after(L, marker)
        mism = ['(A %d, n %d) md %s mine %s' % (A, n, c, fn(A, n)) for (A, n), c in sorted(cells.items()) if c != fn(A, n)]
        rec(len(cells) == 15 and not mism, '4 REPEATS.md table %s: all %d cells recomputed' % (name, len(cells)),
            '; '.join(mism) if mism else 'e.g. (6 arms, 3) %s, (2 arms, 5) %s' % (cells.get((6, 3)), cells.get((2, 5))))
    # json grid vs own numbers
    gbad = []
    for g in RJ['grid']:
        A, n = g['arms'], g['repeats']
        for k in s:
            if not close(g['hw_pct'][k], hw(s[k], n, A * (n - 1)), 1e-9):
                gbad.append('hw %s %d/%d' % (k, A, n))
            if not close(g['hw_block_pct'][k], hw(s[k], n, (A - 1) * (n - 1)), 1e-9):
                gbad.append('hwB %s %d/%d' % (k, A, n))
            if not close(g['mde80_pct'][k], mde(s[k], n, A * (n - 1)), 1e-6):
                gbad.append('mde %s %d/%d' % (k, A, n))
        if not close(g['minutes'], minutes(A, n), 1e-9):
            gbad.append('min %d/%d' % (A, n))
        if g['df'] != A * (n - 1) or g['df_block'] != (A - 1) * (n - 1):
            gbad.append('df %d/%d' % (A, n))
    rec(not gbad, '4 repeats.json grid (hw, hw_block, mde80, minutes, df) vs own numbers', '; '.join(gbad) or
        '%d grid cells x 4 metrics' % len(RJ['grid']))
    # ---- chi-square range and the CV text
    q_lo, q_hi = chi2_ppf_even(0.025, 10), chi2_ppf_even(0.975, 10)
    lo_f, hi_f = math.sqrt(10.0 / q_hi), math.sqrt(10.0 / q_lo)
    rec('%.3f' % q_lo == '3.247' and '%.3f' % q_hi == '20.483' and close(lo_f, RJ['cv_range'][0], 1e-6)
        and close(hi_f, RJ['cv_range'][1], 1e-6), '4 chi-square df 10 quantiles and CV range',
        'q0.025 %.4f, q0.975 %.4f -> %.4f-%.4f x; repeats.json %s' % (q_lo, q_hi, lo_f, hi_f, RJ['cv_range']))
    t80 = dict((d, t_ppf(0.80, d)) for d in (4, 10, 24))
    rec(abs(t80[10] - 0.879) < 6e-4, '4 own t0.80 quantiles', 'df 4 %.4f, df 10 %.4f, df 24 %.4f' % (t80[4], t80[10], t80[24]))
    P = 'p50_ms'
    lines = []
    for n in (3, 4, 5):
        lines.append('- **repeats=%d:** median ms ±%.1f %% (6 arms) to ±%.1f %% (2 arms); fps ±%.1f to ±%.1f %%; %.0f min '
                     '(2 arms) to %.0f min (6 arms).' % (n, hw(s[P], n, 6 * (n - 1)), hw(s[P], n, 2 * (n - 1)),
                                                         hw(s['fps'], n, 6 * (n - 1)), hw(s['fps'], n, 2 * (n - 1)),
                                                         minutes(2, n), minutes(6, n)))
    sh34 = [100.0 * (1.0 - hw(s[P], 4, A * 3) / hw(s[P], 3, A * 2)) for A in (6, 2)]
    sh45 = [100.0 * (1.0 - hw(s[P], 5, A * 4) / hw(s[P], 4, A * 3)) for A in (6, 2)]
    lines.append('- Each repeat adds A runs of %.2f min. From 3 to 4 repeats the ± narrows by %.0f %% (6 arms) to %.0f %% '
                 '(2 arms); from 4 to 5 by %.0f-%.0f %%.' % (slot / 60.0, sh34[0], sh34[1], min(sh45), max(sh45)))
    fac = [mde(s[P], n, A * (n - 1)) / hw(s[P], n, A * (n - 1)) for A in (2, 3, 4, 5, 6) for n in (3, 4, 5)]
    lines.append("- An arm's true delta must be about %.2f-%.2f x its ± to give a `*` 80 %% of the time: with 6 arms that is "
                 "%s %% on median ms for 3 / 4 / 5 repeats." % (min(fac), max(fac), ' / '.join(
                     '%.1f' % mde(s[P], n, 6 * (n - 1)) for n in (3, 4, 5))))
    w4 = J4['methods']['T-std']
    lines.append("- W5's CV is itself an estimate on df 10: another window on the same Power mode can give %.2f-%.2f x these "
                 "± (95 %%). W4b (same overlay) had T-std CV %s %% on median ms, against W5's %s %%." % (
                     lo_f, hi_f, fmt(w4[P]['cv_pct']), fmt(100 * s[P])))
    lines.append("s = W5's T-std pooled SD of ln(value) over its 15 kept runs (df 10): median ms %s %%, fps %s %%, p99 %s %%, "
                 "1 %% low %s %%." % (fmt(100 * s[P]), fmt(100 * s['fps']), fmt(100 * s['p99_ms']), fmt(100 * s['low1_fps'])))
    sb = J5['methods'][BLOCK][P]
    lines.append("In W5 (no round effect) B-block's own s was %s %% on median ms (df %d), so there T-std applies." % (
        fmt(100 * sb['sd_ln']), sb['df']))
    lines.append("- W5's s comes from df 10. Its 95 %% range is %.2f-%.2f x s (chi-square), and every ± above scales with s "
                 "(nearly in proportion): for median ms, s could be %.1f-%.1f %%." % (lo_f, hi_f, 100 * s[P] * lo_f,
                                                                                     100 * s[P] * hi_f))
    lines.append("- W4b, on the same overlay, had T-std CV %s %% (median ms, df %d) and %s %% (fps); W5 has %s %% and %s %%."
                 % (fmt(w4[P]['cv_pct']), w4[P]['df'], fmt(w4['fps']['cv_pct']), fmt(100 * s[P]), fmt(100 * s['fps'])))
    lines.append("(W5's unflagged runs: %s %%; W4b B-block T-std: %s %%). High end: W5's %s %%" % (
        fmt(100 * cv[P]['s_calm']), fmt(J4['methods'][BLOCK][P]['cv_pct']), fmt(100 * s[P])))
    lines.append("(W4b: CV %s -> %s %% on median ms)" % (fmt(w4[P]['cv_pct']), fmt(J4['methods'][BLOCK][P]['cv_pct'])))
    for ln in lines:
        rec(ln in rtext, '4 REPEATS.md text rebuilt with own numbers', ln)


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    info('T975 parsed from noise_methods.py: %s' % T975)
    for name, fn in (('check2', check2), ('check3a', check3a), ('check3 W4b', lambda: check3('W4b')),
                     ('check3 W5', lambda: check3('W5')), ('check4', check4)):
        try:
            fn()
        except Exception as e:  # report and go on
            import traceback
            rec(False, '%s crashed: %r' % (name, e), traceback.format_exc().replace('\n', ' / '))
    OUT.append('RESULT %s (%d passed, %d failed)' % ('PASS' if not NFAIL[0] else 'FAIL', NPASS[0], NFAIL[0]))
    with open(os.path.join(HERE, 'indep.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(OUT) + '\n')
    print(OUT[-1])
    for l in OUT:
        if l.startswith('FAIL'):
            print(l[:600])
    return 0


if __name__ == '__main__':
    sys.exit(main())

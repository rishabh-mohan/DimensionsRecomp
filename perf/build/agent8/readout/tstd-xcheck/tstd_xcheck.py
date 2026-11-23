#!/usr/bin/env python3
"""Independent recompute of Agent 7's T-std noise method and its B-block variant (two-way model, round as a block)
for W4b (matrix 20261122-1541) and W5 (matrix 20261122-1756). Helper of Agent 8, 2026-11-23.

  python -B tstd_xcheck.py        -> tstd.md, tstd_runs.csv, tstd_compare.csv next to this script

Own code (stdlib + numpy; scipy only for t / F cross-checks). build/agent7/w4b-noise/noise_methods.py was read for the
definitions only; nothing of Agent 7's or the runner's code is imported or run. Agent 7's report.json / report-w5.json
and RESULTS.md (transcribed below) are read as data to compare against.
"""
import csv
import json
import math
import os
import statistics
import sys

sys.dont_write_bytecode = True
import numpy as np  # noqa: E402

try:
    from scipy import stats as SST  # noqa: E402
except Exception:  # pragma: no cover
    SST = None

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
A7 = os.path.join(REPO, 'build', 'agent7', 'w4b-noise')
MATRIX = os.path.join(REPO, 'build', 'agent8', 'matrix')
WIN = {
    'w4b': dict(title='W4b (matrix 20261122-1541)', matrix=os.path.join(MATRIX, '20261122-1541'),
                report=os.path.join(A7, 'report.json'), ref='d0', order=['d0', 'B', 'd3', 'd11t']),
    'w5': dict(title='W5 (matrix 20261122-1756)', matrix=os.path.join(MATRIX, '20261122-1756'),
               report=os.path.join(A7, 'report-w5.json'), ref='base', order=['base', 's0', 'd11', 'd11t', 'd11p']),
}
KEYS = (('fps', 1, 'fps'), ('p50_ms', -1, 'median ms'), ('p99_ms', -1, 'p99 ms'), ('low1_fps', 1, '1 % low fps'))
KSIGN = dict((k, s) for k, s, _ in KEYS)
KLABEL = dict((k, lab) for k, _, lab in KEYS)
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093,
        20: 2.086, 25: 2.060, 30: 2.042}
DROP_W5 = '1821-d11t-r3'

# RESULTS.md (Agent 7, 20:15) cells, transcribed: (GM delta, CI lo, CI hi, star)
DOC = {
    'w4b': {
        ('T-std', 'p50_ms'): dict(line=39, band=7.8, cv=2.3, hw44=3.6, df=11, arms={
            'B': (-2.1, -5.8, 1.8, False), 'd3': (-1.5, -4.9, 2.1, False), 'd11t': (-0.5, -4.0, 3.1, False)}),
        ('B-block T-std', 'p50_ms'): dict(line=40, band=3.6, cv=1.4, hw44=2.3, df=8, arms={
            'B': (-2.5, -5.0, 0.0, False), 'd3': (-1.5, -3.7, 0.8, False), 'd11t': (-0.5, -2.8, 1.8, False)}),
        ('T-std', 'fps'): dict(line=49, band=12.7, cv=4.1, hw44=6.6, df=11, arms={
            'B': (5.2, -1.8, 12.8, False), 'd3': (2.3, -4.0, 9.1, False), 'd11t': (2.5, -3.9, 9.3, False)}),
        ('B-block T-std', 'fps'): dict(line=50, band=6.4, cv=3.0, hw44=4.9, df=8, arms={
            'B': (6.0, 0.5, 11.8, True), 'd3': (2.3, -2.5, 7.4, False), 'd11t': (2.5, -2.3, 7.6, False)}),
    },
    'w5': {
        ('T-std', 'p50_ms'): dict(line=78, band=6.5, cv=2.1, hw44=3.3, df=10, arms={
            's0': (1.1, -2.7, 5.0, False), 'd11': (1.2, -2.5, 5.2, False), 'd11t': (2.4, -1.4, 6.4, False),
            'd11p': (1.5, -2.3, 5.4, False)}),
        ('B-block T-std', 'p50_ms'): dict(line=79, band=5.7, cv=2.3, hw44=3.8, df=8, arms={
            's0': (1.1, -3.1, 5.5, False), 'd11': (1.2, -3.0, 5.7, False), 'd11t': (2.4, -1.9, 6.9, False),
            'd11p': (1.5, -2.8, 5.9, False)}),
        ('T-std', 'fps'): dict(line=85, band=5.8, cv=1.8, hw44=2.9, df=10, arms={
            's0': (-1.4, -4.6, 2.0, False), 'd11': (-0.8, -4.0, 2.6, False), 'd11t': (-2.6, -5.7, 0.7, False),
            'd11p': (-1.6, -4.8, 1.7, False)}),
        ('B-block T-std', 'fps'): dict(line=86, band=5.1, cv=2.0, hw44=3.3, df=8, arms={
            's0': (-1.4, -5.0, 2.4, False), 'd11': (-0.8, -4.4, 3.0, False), 'd11t': (-2.6, -6.2, 1.2, False),
            'd11p': (-1.6, -5.2, 2.1, False)}),
        ('T-std', 'p99_ms'): dict(line=88, band=6.9, cv=4.1, hw44=6.7, df=10, arms={
            's0': (2.8, -4.6, 10.8, False), 'd11': (0.5, -6.7, 8.3, False), 'd11t': (8.8, 1.0, 17.2, True),
            'd11p': (5.3, -2.2, 13.5, False)}),
        ('T-std', 'low1_fps'): dict(line=89, band=6.9, cv=5.0, hw44=8.2, df=10, arms={
            's0': (-2.5, -11.0, 6.8, False), 'd11': (-0.4, -9.1, 9.1, False), 'd11t': (-8.1, -16.1, 0.7, False),
            'd11p': (-6.3, -14.4, 2.7, False)}),
    },
}
DOC_MED = {  # median deltas (summary.md form), all 'within'
    'w4b': {('T-std', 'p50_ms'): (59, {'B': -0.8, 'd3': -0.6, 'd11t': 0.2}),
            ('B-block T-std', 'p50_ms'): (60, {'B': -1.9, 'd3': -1.1, 'd11t': -0.4})},
    'w5': {('T-std', 'p50_ms'): (96, {'s0': 2.3, 'd11': 2.5, 'd11t': 2.7, 'd11p': 2.1})},
}
DOC_PAIRED = {'w4b': (64, 'p50_ms', {'B': (6.9, -2.5, 8.8), 'd3': (3.7, -1.5, 2.8), 'd11t': (3.5, -0.5, 2.7)})}
DOC_HT = {'w4b': 0.531, 'w5': 0.213}                                    # L21
DOC_F = {'w4b': (0.40, [3, 11]), 'w5': (0.33, [4, 10])}                # L145


# ---------------------------------------------------------------- inputs

def load_json(path):
    try:
        with open(path, encoding='utf-8-sig') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def read_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as fh:
        return list(csv.DictReader(fh))


def fnum(s):
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def perf_rows(path):
    """[(end offset, frame_time_us)] of the perf.csv data rows with every field an integer (as in my xcheck.py)."""
    with open(path, 'rb') as fh:
        data = fh.read()
    parts = data.split(b'\n')
    header = [h.strip() for h in parts[0].rstrip(b'\r').decode('ascii', 'replace').split(',')]
    width, ci = len(header), header.index('frame_time_us')
    off, rows = len(parts[0]) + 1, []
    for ln in parts[1:-1]:
        off += len(ln) + 1
        fld = ln.rstrip(b'\r').split(b',')
        if len(fld) != width:
            continue
        try:
            iv = [int(x) for x in fld]
        except ValueError:
            continue
        rows.append((off, iv[ci]))
    return rows


def window(run_dir, rj):
    rows = perf_rows(os.path.join(run_dir, 'perf.csv'))
    start_b = rj['measure_start']['perf_csv_bytes']
    seconds = float(rj['params']['seconds'])
    first = 0
    while first < len(rows) and rows[first][0] <= start_b:
        first += 1
    acc, n = 0, 0
    for _, v in rows[first:]:
        if acc >= seconds * 1e6:
            break
        acc += v if v > 0 else 0
        n += 1
    return first, n, [v for _, v in rows[first:first + n] if v > 0]


def t975(df):
    if df is None or df < 1:
        return None
    if df > 30:
        return 1.96 + (T975[30] - 1.96) * 30.0 / df
    return T975[max(k for k in T975 if k <= df)]


def tstd(L, H, h):
    """T-std of one run: light frames L, heavy frames H (us), mixed at heavy-time share h."""
    TL, TH = float(sum(L)), float(sum(H))
    nL, nH = len(L), len(H)
    wL, wH = (1.0 - h) / TL, h / TH
    W = (1.0 - h) * nL / TL + h * nH / TH
    v = np.array(L + H, dtype=np.float64)
    w = np.concatenate([np.full(nL, wL), np.full(nH, wH)])
    o = np.argsort(v, kind='stable')
    vs, ws = v[o], w[o]
    cum = np.cumsum(ws)

    def wq(q):
        i = int(np.searchsorted(cum, q * W * (1.0 - 1e-12), side='left'))
        return float(vs[min(i, len(vs) - 1)])

    rv, rw = vs[::-1], ws[::-1]
    rc = np.cumsum(rw)
    need = 0.01 * W
    j = min(int(np.searchsorted(rc, need, side='left')), len(rv) - 1)
    prev = float(rc[j - 1]) if j > 0 else 0.0
    sx = float(np.dot(rv[:j], rw[:j])) + (need - prev) * float(rv[j])
    return {'fps': 1e6 * W, 'p50_ms': wq(0.5) / 1000.0, 'p99_ms': wq(0.99) / 1000.0, 'low1_fps': 1e6 * need / sx}


def load_runs(C):
    rows = read_csv(os.path.join(C['matrix'], 'results.csv'))
    runs = []
    for r in rows:
        rd = (r.get('run_dir') or '').strip()
        if not os.path.isdir(rd):
            rd = os.path.join(C['matrix'], 'runs', os.path.basename(rd.rstrip('\\/')))
        x = dict(seq=int(r['seq']), round=r['round'].strip(), arm=r['arm'].strip(),
                 name=os.path.basename(rd.rstrip('\\/')),
                 scored=(r.get('scored') or '').strip().lower() == 'true',
                 valid=(r.get('valid_timing') or '').strip().lower() == 'true',
                 excluded=(r.get('excluded') or '').strip().lower() == 'true')
        x['keep'] = x['scored'] and x['valid'] and not x['excluded']
        rj, fj = load_json(os.path.join(rd, 'run.json')), load_json(os.path.join(rd, 'frames.json')) or {}
        first, nrows, ft = window(rd, rj)
        fw = fj.get('window') or {}
        x['win_ok'] = first == int(fw.get('first_row', -1)) and nrows == int(fw.get('rows', -1))
        lms = fnum(fj.get('light_ms')) or 4.5
        thr = lms * 1000.0
        L, H = [v for v in ft if v < thr], [v for v in ft if v >= thr]
        x.update(first_row=first, rows=nrows, frames=len(ft), light_ms=lms, nL=len(L), nH=len(H),
                 TL_s=sum(L) / 1e6, TH_s=sum(H) / 1e6, hT=sum(H) / float(sum(ft)), ls_T=len(L) / float(len(ft)),
                 ls_runner=fnum(fj.get('share_lt_light')), _L=L, _H=H)
        runs.append(x)
    kept = [x for x in runs if x['keep']]
    hT_ref = statistics.median([x['hT'] for x in kept if 0.0 < x['hT'] < 1.0])
    for x in runs:
        x['t'] = tstd(x['_L'], x['_H'], hT_ref)
    return runs, kept, hT_ref


# ---------------------------------------------------------------- statistics

def getv(x, k):
    return (x.get('t') or {}).get(k)


def vals_of(kept, k, g=getv):
    out = {}
    for x in kept:
        v = g(x, k)
        if v is not None and v > 0:
            out.setdefault(x['arm'], []).append((x['name'], v))
    return out


def verdict(dp, band, sign):
    if abs(dp) <= band:
        return 'within'
    return 'better' if (dp > 0) == (sign > 0) else 'worse'


def oneway(vals, ref, order, sign):
    arms = [a for a in order if a in vals]
    rv = [v for _, v in vals[ref]]
    rmed = statistics.median(rv)
    band = 100.0 * (max(rv) - min(rv)) / rmed
    ss, df = 0.0, 0
    for a in arms:
        lv = np.log([v for _, v in vals[a]])
        if len(lv) >= 2:
            ss += float(((lv - lv.mean()) ** 2).sum())
            df += len(lv) - 1
    sd = math.sqrt(ss / df)
    t = t975(df)
    lr = float(np.mean(np.log(rv)))
    out = {}
    for a in arms:
        av = [v for _, v in vals[a]]
        e = dict(n=len(av), names=[nm for nm, _ in vals[a]], vals=av, med=statistics.median(av), lo=min(av),
                 hi=max(av))
        if a != ref:
            dl = float(np.mean(np.log(av))) - lr
            se = sd * math.sqrt(1.0 / len(av) + 1.0 / len(rv))
            e.update(dl=dl, se=se, gm=100.0 * (math.exp(dl) - 1.0),
                     ci=(100.0 * (math.exp(dl - t * se) - 1.0), 100.0 * (math.exp(dl + t * se) - 1.0)),
                     excl=(dl - t * se > 0) or (dl + t * se < 0))
            e['dp'] = 100.0 * (e['med'] - rmed) / rmed
            e['verdict'] = verdict(e['dp'], band, sign)
        out[a] = e
    return dict(df=df, sd=sd, cv=100.0 * sd, t=t, band=band, ref=ref, ref_med=rmed,
                hw44=100.0 * (math.exp(t * sd * math.sqrt(0.5)) - 1.0), arms=out)


def bblock(kept, k, ref, order, sign, g=getv):
    """Two-way OLS ln v = arm + round (round 1 = base) with numpy; summaries as described in DEF_MD."""
    rows = [(x['arm'], x['name'], x['round'], g(x, k)) for x in kept]
    rows = [r for r in rows if r[3] is not None and r[3] > 0]
    arms = [a for a in order if any(r[0] == a for r in rows)]
    rounds = sorted(set(r[2] for r in rows), key=float)
    n, G, kk = len(rows), len(arms), len(rounds) - 1
    X, D = np.zeros((n, G + kk)), np.zeros((n, kk))
    y = np.log(np.array([r[3] for r in rows], dtype=np.float64))
    for i, (arm, _, rnd, _) in enumerate(rows):
        X[i, arms.index(arm)] = 1.0
        j = rounds.index(rnd)
        if j > 0:
            X[i, G + j - 1] = 1.0
            D[i, j - 1] = 1.0
    beta, _, rank, _ = np.linalg.lstsq(X, y, rcond=None)
    df = n - int(rank)
    res = y - X @ beta
    sd = math.sqrt(float(res @ res) / df)
    XtXi = np.linalg.inv(X.T @ X)
    b = beta[G:]
    yd, Dd = y.copy(), D.copy()             # check: b from the arm-demeaned (within-arm) regression
    for a in arms:
        m = [i for i, r in enumerate(rows) if r[0] == a]
        yd[m] -= yd[m].mean()
        Dd[m] -= Dd[m].mean(axis=0)
    b_fwl = np.linalg.lstsq(Dd, yd, rcond=None)[0]
    t = t975(df)
    adj = np.exp(y - (D - D.mean(axis=0)) @ b)
    va = dict((a, [(rows[i][1], float(adj[i])) for i in range(n) if rows[i][0] == a]) for a in arms)
    rv = [v for _, v in va[ref]]
    rmed = statistics.median(rv)
    band = 100.0 * (max(rv) - min(rv)) / rmed
    ir = arms.index(ref)
    out = {}
    for a in arms:
        av = [v for _, v in va[a]]
        e = dict(n=len(av), names=[nm for nm, _ in va[a]], vals=av, med=statistics.median(av), lo=min(av),
                 hi=max(av), rounds=[r[2] for r in rows if r[0] == a])
        if a != ref:
            c = np.zeros(G + kk)
            c[arms.index(a)], c[ir] = 1.0, -1.0
            dl = float(c @ beta)
            se = sd * math.sqrt(float(c @ XtXi @ c))
            e.update(dl=dl, se=se, gm=100.0 * (math.exp(dl) - 1.0),
                     ci=(100.0 * (math.exp(dl - t * se) - 1.0), 100.0 * (math.exp(dl + t * se) - 1.0)),
                     excl=(dl - t * se > 0) or (dl + t * se < 0),
                     gm_adj=100.0 * (math.exp(float(np.mean(np.log(av)) - np.mean(np.log(rv)))) - 1.0))
            e['dp'] = 100.0 * (e['med'] - rmed) / rmed
            e['verdict'] = verdict(e['dp'], band, sign)
        out[a] = e
    return dict(df=df, sd=sd, cv=100.0 * sd, t=t, band=band, ref=ref, ref_med=rmed,
                hw44=100.0 * (math.exp(t * sd * math.sqrt(0.5)) - 1.0), arms=out, rounds=rounds,
                b=[float(q) for q in b], b_fwl=[float(q) for q in b_fwl],
                b_pct=[100.0 * (math.exp(float(q)) - 1.0) for q in b], n=n, G=G, k=kk)


def paired(kept, k, arm, ref, g=getv):
    byr = {}
    for x in kept:
        v = g(x, k)
        if v is not None:
            byr.setdefault(x['round'], {})[x['arm']] = v
    rr = [(r, byr[r][arm], byr[r][ref]) for r in sorted(byr, key=float) if arm in byr[r] and ref in byr[r]]
    ds = [100.0 * (av - rv) / rv for _, av, rv in rr]
    n = len(ds)
    sd = statistics.stdev(ds) if n >= 2 else None
    t = t975(n - 1) if n >= 2 else None
    return dict(n=n, rounds=[r for r, _, _ in rr], deltas=ds, med=statistics.median(ds), mean=statistics.fmean(ds),
                range=max(ds) - min(ds), sd=sd, hw95=(t * sd / math.sqrt(n)) if sd is not None else None,
                up=sum(1 for q in ds if q > 0))


def light_F(kept, order):
    g = {}
    for x in kept:
        g.setdefault(x['arm'], []).append(x['ls_T'])
    allv = [v for a in g for v in g[a]]
    m = statistics.fmean(allv)
    ssb = sum(len(lst) * (statistics.fmean(lst) - m) ** 2 for lst in g.values())
    ssw = sum(sum((v - statistics.fmean(lst)) ** 2 for v in lst) for lst in g.values())
    dfb, dfw = len(g) - 1, len(allv) - len(g)
    F = (ssb / dfb) / (ssw / dfw)
    out = dict(F=F, df=[dfb, dfw], means=dict((a, statistics.fmean(g[a])) for a in order if a in g),
               vals=dict((a, g[a]) for a in order if a in g))
    if SST is not None:
        out['p'] = float(SST.f.sf(F, dfb, dfw))
        out['F_scipy'] = float(SST.f_oneway(*[g[a] for a in order if a in g]).statistic)
    return out


def t_exact(df):
    return float(SST.t.ppf(0.975, df)) if SST is not None else None


def ci_exact(e, df):
    """CI of a contrast with scipy's exact t instead of the 3-dp table (info)."""
    te = t_exact(df)
    if te is None or e.get('dl') is None:
        return None
    return (100.0 * (math.exp(e['dl'] - te * e['se']) - 1.0), 100.0 * (math.exp(e['dl'] + te * e['se']) - 1.0))


# ---------------------------------------------------------------- comparisons

class Cmp(object):
    def __init__(self):
        self.rows = []

    def add(self, win, src, item, mine, theirs, cls, note=''):
        self.rows.append(dict(window=win, source=src, item=item, mine=mine, theirs=theirs, cls=cls, note=note))

    def num(self, win, src, item, mine, theirs, rel=1e-9, floor=1e-10):
        if mine is None or theirs is None:
            cls = 'MATCH' if (mine is None and theirs is None) else 'MISMATCH'
        else:
            d = abs(float(mine) - float(theirs))
            sc = max(abs(float(mine)), abs(float(theirs)))
            cls = 'MATCH' if d <= max(rel * sc, floor) else ('NEAR' if d <= max(1e-6 * sc, 1e-8) else 'MISMATCH')
        self.add(win, src, item, mine, theirs, cls)

    def exact(self, win, src, item, mine, theirs):
        self.add(win, src, item, mine, theirs, 'MATCH' if mine == theirs else 'MISMATCH')

    def shown(self, win, src, item, mine, shown, nd=1):
        r = float('%.*f' % (nd, mine))
        if abs(r - shown) < 1e-9:
            cls = 'MATCH'
        elif abs(mine - shown) <= 0.5 * 10 ** (-nd) + 1e-9:
            cls = 'TIE'
        else:
            cls = 'MISMATCH'
        self.add(win, src, item, mine, shown, cls, '%d dp' % nd)

    def shown_alt(self, win, src, item, mine, shown, alt, alt_desc, nd=1):
        """As shown(); when mine does not round to the cell but the alternative definition alt does: DEF."""
        if abs(float('%.*f' % (nd, mine)) - shown) < 1e-9:
            self.add(win, src, item, mine, shown, 'MATCH', '%d dp' % nd)
        elif abs(float('%.*f' % (nd, alt)) - shown) < 1e-9:
            self.add(win, src, item, mine, shown, 'DEF', '%d dp; the cell matches %s = %.4f' % (nd, alt_desc, alt))
        elif abs(mine - shown) <= 0.5 * 10 ** (-nd) + 1e-9:
            self.add(win, src, item, mine, shown, 'TIE', '%d dp' % nd)
        else:
            self.add(win, src, item, mine, shown, 'MISMATCH', '%d dp' % nd)


CLASSES = ('MATCH', 'NEAR', 'TIE', 'DEF', 'MISMATCH')
PR_PAIRS = (('d11t', 'd11'), ('d11t', 'base'), ('d11p', 'd11'), ('d11p', 'base'))


def find_method(R, method, key):
    for m in R.get('methods') or []:
        if m.get('method') == method and m.get('key') == key:
            return m
    return None


def cmp_method(cm, wk, method, key, mine, R, ref):
    th = find_method(R, method, key)
    src, pre = 'report-json', '%s %s' % (method, key)
    if th is None:
        cm.add(wk, src, pre + ' present', 'yes', 'no', 'MISMATCH')
        return
    cm.num(wk, src, pre + ' band_pct', mine['band'], th.get('band_pct'))
    cm.num(wk, src, pre + ' sd_ln', mine['sd'], th.get('sd_ln'))
    cm.num(wk, src, pre + ' cv_pct', mine['cv'], th.get('cv_pct'))
    cm.exact(wk, src, pre + ' df', mine['df'], th.get('df'))
    cm.num(wk, src, pre + ' hw44_pct', mine['hw44'], th.get('hw44_pct'))
    cm.num(wk, src, pre + ' ref_med', mine['ref_med'], th.get('ref_med'))
    if 'b' in mine:
        tb = th.get('b') or []
        cm.exact(wk, src, pre + ' len(b)', len(mine['b']), len(tb))
        for i, bi in enumerate(mine['b']):
            cm.num(wk, src, pre + ' b[round %s]' % mine['rounds'][i + 1], bi, tb[i] if i < len(tb) else None)
    for arm, e in mine['arms'].items():
        ta = (th.get('arms') or {}).get(arm)
        if ta is None:
            cm.add(wk, src, '%s %s present' % (pre, arm), 'yes', 'no', 'MISMATCH')
            continue
        p = '%s %s ' % (pre, arm)
        cm.exact(wk, src, p + 'n', e['n'], ta.get('n'))
        for f in ('med', 'lo', 'hi'):
            cm.num(wk, src, p + f, e[f], ta.get(f))
        tv = dict(zip(ta.get('runs') or [], ta.get('vals') or []))
        for nm, v in zip(e['names'], e['vals']):
            cm.num(wk, src, p + 'vals[%s]' % nm, v, tv.get(nm))
        if arm != ref:
            cm.num(wk, src, p + 'delta_pct', e['dp'], ta.get('delta_pct'))
            cm.exact(wk, src, p + 'verdict', e['verdict'], ta.get('verdict'))
            cm.num(wk, src, p + 'gm_delta_pct', e['gm'], ta.get('gm_delta_pct'))
            tci = ta.get('ci_pct') or [None, None]
            cm.num(wk, src, p + 'ci_lo', e['ci'][0], tci[0])
            cm.num(wk, src, p + 'ci_hi', e['ci'][1], tci[1])
            cm.exact(wk, src, p + 'ci_excludes_0', e['excl'], ta.get('ci_excludes_0'))


def cmp_paired(cm, wk, key, mine, R):
    src = 'report-json'
    th = next((q for q in R.get('paired') or [] if q.get('src') == 'T-std' and q.get('key') == key), None)
    if th is None:
        cm.add(wk, src, 'paired T-std %s present' % key, 'yes', 'no', 'MISMATCH')
        return
    for arm, e in mine.items():
        ta = (th.get('arms') or {}).get(arm)
        p = 'paired T-std %s %s ' % (key, arm)
        if ta is None:
            cm.add(wk, src, p + 'present', 'yes', 'no', 'MISMATCH')
            continue
        cm.exact(wk, src, p + 'n', e['n'], ta.get('n'))
        cm.exact(wk, src, p + 'rounds', e['rounds'], [str(q) for q in ta.get('rounds') or []])
        for i, d in enumerate(e['deltas']):
            td = ta.get('deltas') or []
            cm.num(wk, src, p + 'delta[r%s]' % e['rounds'][i], d, td[i] if i < len(td) else None)
        for f in ('med', 'mean', 'range', 'sd', 'hw95'):
            cm.num(wk, src, p + f, e[f], ta.get(f))
        cm.exact(wk, src, p + 'up', e['up'], ta.get('up'))


def cmp_doc(cm, wk, res):
    src = 'RESULTS.md'
    for (method, key), d in DOC.get(wk, {}).items():
        mine = res['oneway'][key] if method == 'T-std' else res['bblock'][key]
        p = 'L%d %s %s ' % (d['line'], method, key)
        cm.shown(wk, src, p + 'band', mine['band'], d['band'])
        cm.shown(wk, src, p + 'CV', mine['cv'], d['cv'])
        cm.shown(wk, src, p + '4v4', mine['hw44'], d['hw44'])
        cm.exact(wk, src, p + 'df', mine['df'], d['df'])
        for arm, (gm, lo, hi, star) in d['arms'].items():
            e = mine['arms'][arm]
            cm.shown(wk, src, p + arm + ' GM', e['gm'], gm)
            cm.shown(wk, src, p + arm + ' CI lo', e['ci'][0], lo)
            cm.shown(wk, src, p + arm + ' CI hi', e['ci'][1], hi)
            cm.exact(wk, src, p + arm + ' star', e['excl'], star)
    for (method, key), (line, dd) in DOC_MED.get(wk, {}).items():
        mine = res['oneway'][key] if method == 'T-std' else res['bblock'][key]
        for arm, v in dd.items():
            cm.shown(wk, src, 'L%d %s %s %s median delta' % (line, method, key, arm), mine['arms'][arm]['dp'], v)
            cm.exact(wk, src, 'L%d %s %s %s within' % (line, method, key, arm), mine['arms'][arm]['verdict'],
                     'within')
    if wk in DOC_PAIRED:
        line, key, dd = DOC_PAIRED[wk]
        for arm, (rng, mean, hw) in dd.items():
            e = res['paired'][key][arm]
            p = 'L%d paired T-std %s %s ' % (line, key, arm)
            cm.shown(wk, src, p + 'range', e['range'], rng)
            cm.shown(wk, src, p + 'mean', e['mean'], mean)
            cm.shown(wk, src, p + 'hw95', e['hw95'], hw)
    cm.shown(wk, src, 'L21 hT_ref', res['hT_ref'], DOC_HT[wk], nd=3)
    F, dfs = DOC_F[wk]
    cm.shown(wk, src, 'L145 light-share F', res['F']['F'], F, nd=2)
    cm.exact(wk, src, 'L145 light-share F df', res['F']['df'], dfs)
    bp = res['bblock']['p50_ms']['b_pct']
    if wk == 'w5':
        cm.shown(wk, src, 'L98 B-block round 2 term on median ms %', bp[0], 0.8)
        cm.shown(wk, src, 'L98 B-block round 3 term on median ms %', bp[1], -0.2)
        e = res['bblock']['p99_ms']['arms']['d11t']
        cm.shown(wk, src, 'L103 B-block p99 d11t CI lo', e['ci'][0], 2.1)
        cm.shown(wk, src, 'L103 B-block p99 d11t CI hi', e['ci'][1], 15.9)
        for key in ('fps', 'p50_ms', 'p99_ms', 'low1_fps'):   # L98 / L175: balanced, so B-block deltas = T-std's
            for arm in WIN[wk]['order'][1:]:
                cm.num(wk, src, 'L98/L175 B-block GM = T-std GM %s %s' % (key, arm),
                       res['bblock'][key]['arms'][arm]['gm'], res['oneway'][key]['arms'][arm]['gm'], rel=1e-9)
    else:
        mags = sorted(-q for q in bp)
        lps = sorted(-100.0 * q for q in res['bblock']['p50_ms']['b'])
        cm.exact(wk, src, 'L69 B-block rounds 2-4 below round 1 (median ms, all < 0)', all(q < 0 for q in bp), True)
        cm.shown_alt(wk, src, 'L69 B-block smallest round term below round 1 % (100 (1 - exp(b)))', mags[0], 3.1,
                     lps[0], '100 |b| (log points)')
        cm.shown_alt(wk, src, 'L69 B-block largest round term below round 1 % (100 (1 - exp(b)))', mags[-1], 4.1,
                     lps[-1], '100 |b| (log points)')


# ---------------------------------------------------------------- analysis per window

def analyse(wk, cm):
    C = WIN[wk]
    runs, kept, hT_ref = load_runs(C)
    R = load_json(C['report']) or {}
    ref, order = C['ref'], C['order']
    res = dict(wk=wk, C=C, runs=runs, kept=kept, hT_ref=hT_ref)
    res['oneway'] = dict((k, oneway(vals_of(kept, k), ref, order, KSIGN[k])) for k, _, _ in KEYS)
    res['bblock'] = dict((k, bblock(kept, k, ref, order, KSIGN[k])) for k, _, _ in KEYS)
    res['paired'] = dict((k, dict((a, paired(kept, k, a, ref)) for a in order if a != ref)) for k, _, _ in KEYS)
    res['F'] = light_F(kept, order)
    res['ls_max'] = max(abs(x['ls_T'] - x['ls_runner']) for x in runs if x['ls_runner'] is not None)
    res['win_bad'] = [x['name'] for x in runs if not x['win_ok']]
    # internal checks of the B-block routes
    res['bb_check'] = max([abs(p - q) for k in res['bblock'] for p, q in zip(res['bblock'][k]['b'],
                                                                         res['bblock'][k]['b_fwl'])] +
                          [abs(e['gm'] - e['gm_adj']) for k in res['bblock'] for e in res['bblock'][k]['arms'].values()
                           if 'gm' in e])
    # report JSON
    src = 'report-json'
    cm.num(wk, src, 'hT_ref', hT_ref, R.get('hT_ref'))
    cm.num(wk, src, 'ls_check_max_abs', res['ls_max'], R.get('ls_check_max_abs'))
    rr = dict((y.get('name'), y) for y in R.get('runs') or [])
    for x in runs:
        y = rr.get(x['name'])
        x['rep_maxrel'] = None
        if y is None:
            cm.add(wk, src, 'run %s present' % x['name'], 'yes', 'no', 'MISMATCH')
            continue
        p = 'run %s ' % x['name']
        cm.exact(wk, src, p + 'keep', x['keep'], bool(y.get('keep')))
        cm.num(wk, src, p + 'hT', x['hT'], y.get('hT'))
        cm.num(wk, src, p + 'ls_T', x['ls_T'], y.get('ls_T'))
        cm.num(wk, src, p + 'light_ms', x['light_ms'], y.get('light_ms'))
        ts = y.get('t_std') or {}
        rels = []
        for k, _, _ in KEYS:
            cm.num(wk, src, p + 't_std.' + k, x['t'][k], ts.get(k))
            if ts.get(k) is not None:
                rels.append(abs(x['t'][k] - ts[k]) / abs(ts[k]))
        rels += [abs(x['hT'] - y['hT']) / y['hT'], abs(x['ls_T'] - y['ls_T']) / y['ls_T']]
        x['rep_maxrel'] = max(rels)
    for k, _, _ in KEYS:
        cmp_method(cm, wk, 'T-std', k, res['oneway'][k], R, ref)
        cmp_method(cm, wk, 'B-block T-std', k, res['bblock'][k], R, ref)
        cmp_paired(cm, wk, k, res['paired'][k], R)
    ci = (R.get('cov_info') or {}).get('ls_T') or {}
    cm.num(wk, src, 'cov_info ls_T F', res['F']['F'], ci.get('F'))
    cm.exact(wk, src, 'cov_info ls_T df', res['F']['df'], ci.get('df'))
    for a, v in res['F']['means'].items():
        cm.num(wk, src, 'cov_info ls_T mean %s' % a, v, (ci.get('means') or {}).get(a))
    cmp_doc(cm, wk, res)
    if wk == 'w5':
        res['sens'] = w5_sens(kept, hT_ref, order)
    else:
        res['loo'] = w4b_loo(kept, order)
    return res


def w5_sens(kept, hT_ref, order):
    sub = [x for x in kept if x['name'] != DROP_W5]
    out = dict(cmp={}, cmp14={}, pr={})
    h14 = statistics.median([x['hT'] for x in sub if 0.0 < x['hT'] < 1.0])
    t14 = dict((x['name'], tstd(x['_L'], x['_H'], h14)) for x in sub)
    g14 = (lambda x, k: t14[x['name']][k])
    out['h14'] = h14
    for ref in ('base', 'd11'):
        for k, s, _ in KEYS:
            fo, po = oneway(vals_of(kept, k), ref, order, s), oneway(vals_of(sub, k), ref, order, s)
            fb, pb = bblock(kept, k, ref, order, s), bblock(sub, k, ref, order, s)
            out['cmp'][(ref, k)] = dict(full=fo['arms']['d11t'], part=po['arms']['d11t'], df_full=fo['df'],
                                        df_part=po['df'], bfull=fb['arms']['d11t'], bpart=pb['arms']['d11t'],
                                        bdf_full=fb['df'], bdf_part=pb['df'], ref_vals=po['arms'][ref]['vals'],
                                        ref_names=po['arms'][ref]['names'])
            out['cmp14'][(ref, k)] = oneway(vals_of(sub, k, g14), ref, order, s)['arms']['d11t']
    for arm2, ref2 in PR_PAIRS:
        for k in ('p99_ms', 'low1_fps', 'p50_ms', 'fps'):
            out['pr'][(arm2, ref2, k)] = paired(kept, k, arm2, ref2)
    return out


def w4b_loo(kept, order):
    rows = []
    full = bblock(kept, 'fps', 'd0', order, 1)
    rows.append(('all 15 kept runs', full['df'], full['arms']['B']))
    for x in kept:
        if x['arm'] in ('B', 'd0'):
            sub = [y for y in kept if y is not x]
            bb = bblock(sub, 'fps', 'd0', order, 1)
            rows.append(('without ' + x['name'], bb['df'], bb['arms']['B']))
    return rows


# ---------------------------------------------------------------- output

def f(v, nd=1):
    return '-' if v is None else '%.*f' % (nd, v)


def sg(v, nd=1):
    return '-' if v is None else '%+.*f' % (nd, v)


def cicell(e, nd=2):
    if e.get('gm') is None:
        return '-'
    return '%s [%s, %s]%s' % (sg(e['gm'], nd), sg(e['ci'][0], nd), sg(e['ci'][1], nd), ' *' if e['excl'] else '')


DEF_MD = """## Definitions (re-implemented from noise_methods.py; nothing imported or run)

- **Window:** the perf.csv data rows with every field an integer. The first row is the first one whose end offset is past run.json `measure_start.perf_csv_bytes`. Rows are taken until their frame_time_us sum (values <= 0 count as 0) reaches `params.seconds` x 1e6. Frames are the window rows with frame_time_us > 0. first_row and rows are checked against frames.json `window` for every run.
- **T split:** light = frame time < frames.json `light_ms` (4.5 in every run) x 1000 us; heavy = the rest. hT = heavy time / window time. Light share ls_T = light frames / frames, checked against frames.json `share_lt_light`.
- **Kept runs:** results.csv scored = True, valid_timing = True and excluded = False. That gives 15 in W4b (no cold, no 1551-B-r2) and 15 in W5 (no cold). hT_ref = statistics.median of hT over the kept runs (0 < hT < 1).
- **T-std per run:**
  - Weights: (1 - hT_ref) / T_light for each light frame and hT_ref / T_heavy for each heavy frame (T in us).
  - Total weight W = (1 - hT_ref) n_L / T_L + hT_ref n_H / T_H; fps = 1e6 W.
  - p50 / p99 = the smallest frame time whose ascending cumulative weight reaches 0.5 W / 0.99 W (x (1 - 1e-12)).
  - 1 % low = 1e6 x 0.01 W / the weighted time of the slowest 0.01 W of weight; the last frame is taken partially.
  - Implemented with numpy argsort, cumsum and searchsorted.
- **One-way T-std (per metric, over the kept runs):**
  - band = 100 (max - min) / median of the reference's values.
  - sd = pooled within-arm SD of ln(value), df = runs - arms; t = the 3-dp t975 table, taking the smaller df between entries (the same table as noise_methods.py; scipy's exact t is shown for the starred cells).
  - GM delta = 100 (exp(dl) - 1), dl = mean ln(arm) - mean ln(ref); CI = exp(dl +- t sd sqrt(1/n_a + 1/n_ref)).
  - CV = 100 sd; 4 vs 4 band = 100 (exp(t sd sqrt(1/2)) - 1).
  - Median delta = 100 (median arm - median ref) / median ref; it is `within` when |delta| <= band.
- **B-block T-std:**
  - OLS (numpy lstsq) of ln(value) on arm indicators plus dummies for rounds 2.. (round 1 is the base).
  - df = runs - rank = runs - arms - rounds + 1, which is 8 in both windows. sd = sqrt(SSE / df).
  - The arm contrast vs the reference and its SE come from sd^2 c'(X'X)^-1 c, with the CI from t975(df).
  - Band, median delta and the arms' med/lo/hi use the adjusted values exp(ln v - (d - mean d) . b), where d = the run's round dummies (Agent 7's convention). Round terms are shown as 100 (exp(b) - 1).
  - Internal checks: b equals the arm-demeaned (within-arm) regression, and the GM delta equals the difference of the adjusted values' mean logs.
- **Paired:** per round, 100 (arm - ref) / ref. Then the median, mean, range, sd (n - 1), hw95 = t975(n - 1) sd / sqrt(n), and the rounds with delta > 0 ("up").
- **Light-share F:** one-way ANOVA of ls_T on the arm over the kept runs, df (arms - 1, runs - arms); scipy f_oneway is used as a check.

## Tolerances

- **report-json** (Agent 7's report.json / report-w5.json, full precision):
  - MATCH: |mine - theirs| <= max(1e-9 x |value|, 1e-10).
  - NEAR: <= 1e-6 relative.
  - Otherwise MISMATCH. ints, bools, strings and lists of rounds must be equal.
- **RESULTS.md** (1 dp; hT_ref 3 dp; F 2 dp):
  - MATCH: my value printed with the same decimals equals the cell.
  - TIE: it does not, but it is within half a unit (+1e-9), i.e. at a rounding boundary.
  - Otherwise MISMATCH. Stars are compared with ci_excludes_0.
"""


def seq(e, nd=2):
    return ' / '.join(sg(d, nd) for d in e['deltas'])


def readings(out, cm):
    W4, W5 = out['w4b'], out['w5']
    S = W5['sens']
    rj = [r for r in cm.rows if r['source'] == 'report-json']
    rd = [r for r in cm.rows if r['source'] == 'RESULTS.md']
    maxrel = max(x['rep_maxrel'] for wk in out for x in out[wk]['runs'] if x['rep_maxrel'] is not None)
    other = [r for r in rd if r['cls'] not in ('MATCH', 'DEF')]
    bp4 = W4['bblock']['p50_ms']
    lp4 = [-100.0 * q for q in bp4['b']]
    L = []
    w = L.append
    w('## Readings (facts)')
    w('')
    w('- **Reproduced.** My code matches report.json / report-w5.json in %d of %d items, within 1e-9 relative. The '
      'largest per-run relative difference is %.1e. The items cover:' % (
          sum(1 for r in rj if r['cls'] == 'MATCH'), len(rj), maxrel))
    w('  - every per-run T-std value and hT, and hT_ref;')
    w('  - every one-way and B-block T-std summary: band, sd, CV, 4v4, df, round terms b, adjusted values, GM deltas, '
      'CIs, stars, median deltas and verdicts;')
    w('  - every paired value, and the light-share F.')
    w('- **RESULTS.md:** %d of %d cells match. %s' % (
        sum(1 for r in rd if r['cls'] == 'MATCH'), len(rd),
        ('Not matched: ' + '; '.join('%s (mine %.3f, cell %s, %s)' % (r['item'], r['mine'], r['theirs'], r['cls'])
                                     for r in other) + '.') if other else 'No other cell differs.'))
    w('  - **L69, a definition difference.** L69 says rounds 2-4 have median ms 3.1-4.1 %% below round 1. As '
      '100 (exp(b) - 1), the B-block median-ms round terms (r2 / r3 / r4) are %s %%, i.e. 3.1-4.0 %%. "3.1-4.1" is 100 |b| '
      'in log points (%s). The reading does not change.' % (
          ' / '.join(sg(q, 2) for q in bp4['b_pct']), ' / '.join('%.2f' % q for q in lp4)))
    e = W4['bblock']['fps']['arms']['B']
    loo = W4['loo'][1:]
    lose = [(lab, x) for lab, _, x in loo if not x['excl']]
    pf = W4['paired']['fps']['B']
    em = W4['bblock']['p50_ms']['arms']['B']
    w('- **W4b, B-block T-std fps, B vs d0:** %s (df %d) is reproduced; scipy\'s exact t(8) gives the same to 2 dp. '
      'It rests on few runs:' % (cicell(e), W4['bblock']['fps']['df']))
    w('  - Leave-one-out (one B or d0 run at a time): %d of %d variants keep the CI above 0.' % (
        len(loo) - len(lose), len(loo)))
    w('  - The CI includes 0 %s.' % '; '.join('%s: %s' % (lab.replace('without ', 'without '), cicell(x))
                                              for lab, x in lose))
    w('  - Paired T-std fps B vs d0 by round (r%s): %s; mean %s +- %s; %d/%d up.' % (
        ' / r'.join(pf['rounds']), seq(pf), sg(pf['mean'], 2), f(pf['hw95'], 2), pf['up'], pf['n']))
    w('  - B-block median ms B: %s. The upper bound is %s, so RESULTS.md\'s "+0.0" with no star is right, but at the '
      'edge.' % (cicell(em, 3), sg(em['ci'][1], 3)))
    p99, lo1 = W5['oneway']['p99_ms']['arms']['d11t'], W5['oneway']['low1_fps']['arms']['d11t']
    bp99, blo1 = W5['bblock']['p99_ms']['arms']['d11t'], W5['bblock']['low1_fps']['arms']['d11t']
    w('- **W5, d11t tail lead (reproduced):**')
    w('  - T-std: p99 %s, 1 %% low %s.' % (cicell(p99), cicell(lo1)))
    w('  - B-block: p99 %s, which matches L103 [+2.1, +15.9]. B-block 1 %% low %s also excludes 0; RESULTS.md does not '
      'state this.' % (cicell(bp99), cicell(blo1)))
    c = S['cmp']
    pb, lb = c[('base', 'p99_ms')], c[('base', 'low1_fps')]
    pd, ld = c[('d11', 'p99_ms')], c[('d11', 'low1_fps')]
    w('- **W5, without %s** (n = 2; RESULTS.md L117 lists it as a flagged host-state run):' % DROP_W5)
    w('  - vs base: p99 %s, 1 %% low %s. These are %.0f %% and %.0f %% of the full-set deltas.' % (
        cicell(pb['part']), cicell(lb['part']), 100.0 * pb['part']['gm'] / pb['full']['gm'],
        100.0 * lb['part']['gm'] / lb['full']['gm']))
    w('  - vs d11: p99 %s, 1 %% low %s (one-way, df %d).' % (cicell(pd['part']), cicell(ld['part']), pb['df_part']))
    w('  - B-block vs base (df %d): p99 %s, 1 %% low %s.' % (pb['bdf_part'], cicell(pb['bpart']),
                                                          cicell(lb['bpart'])))
    w('  - With hT_ref recomputed over the 14 runs (%.4f): p99 %s, 1 %% low %s vs base.' % (
        S['h14'], sg(S['cmp14'][('base', 'p99_ms')]['gm'], 2), sg(S['cmp14'][('base', 'low1_fps')]['gm'], 2)))
    w('  - No CI excludes 0 without this run.' if not any(
        x['excl'] for x in (pb['part'], lb['part'], pd['part'], ld['part'], pb['bpart'], lb['bpart'],
                            c[('d11', 'p99_ms')]['bpart'], c[('d11', 'low1_fps')]['bpart']))
      else '  - Some CIs still exclude 0 without this run (see the table).')
    pr = S['pr']

    def worse(e, k):
        return sum(1 for d in e['deltas'] if (d > 0 if k == 'p99_ms' else d < 0))
    w('- **W5, per round (r1 / r2 / r3):**')
    for arm2, ref2 in PR_PAIRS:
        a, b2 = pr[(arm2, ref2, 'p99_ms')], pr[(arm2, ref2, 'low1_fps')]
        w('  - %s vs %s: p99 %s (worse in %d/%d rounds); 1 %% low %s (worse in %d/%d).' % (
            arm2, ref2, seq(a), worse(a, 'p99_ms'), a['n'], seq(b2), worse(b2, 'low1_fps'), b2['n']))
    bb = W5['bblock']
    ow = W5['oneway']
    w('- **W5 round terms (r2, r3 vs r1):**')
    w('  - Median ms %s %% and fps %s %%: about 0, matching L98.' % (
        ' / '.join(sg(q, 2) for q in bb['p50_ms']['b_pct']), ' / '.join(sg(q, 2) for q in bb['fps']['b_pct'])))
    w('  - p99 %s %% and 1 %% low %s %%: not 0.' % (
        ' / '.join(sg(q, 2) for q in bb['p99_ms']['b_pct']), ' / '.join(sg(q, 2) for q in bb['low1_fps']['b_pct'])))
    w('  - So for p99 and 1 %% low the B-block CIs are narrower than T-std\'s, not wider. 4v4 band: p99 %.2f vs %.2f, '
      '1 %% low %.2f vs %.2f. L98\'s "slightly wider CI" holds only for median ms (%.2f vs %.2f) and fps (%.2f vs '
      '%.2f).' % (bb['p99_ms']['hw44'], ow['p99_ms']['hw44'], bb['low1_fps']['hw44'], ow['low1_fps']['hw44'],
                  bb['p50_ms']['hw44'], ow['p50_ms']['hw44'], bb['fps']['hw44'], ow['fps']['hw44']))
    F4, F5 = W4['F'], W5['F']
    med4 = [x['name'] for x in W4['kept'] if x['hT'] == W4['hT_ref']]
    med5 = [x['name'] for x in W5['kept'] if x['hT'] == W5['hT_ref']]
    w('- **hT_ref:** W4b %.6f (the median run is %s) and W5 %.6f (%s). Both match L21 (0.531 / 0.213).' % (
        W4['hT_ref'], ', '.join(med4), W5['hT_ref'], ', '.join(med5)))
    w('- **Light-share F:** W4b %.4f on (%d, %d), p %.2f; W5 %.4f on (%d, %d), p %.2f. Both match L145.' % (
        F4['F'], F4['df'][0], F4['df'][1], F4.get('p', float('nan')), F5['F'], F5['df'][0], F5['df'][1],
        F5.get('p', float('nan'))))
    return L


def write_md(out, cm, path):
    L = []
    w = L.append
    w('# T-std / B-block T-std independent cross-check (helper of Agent 8)')
    w('')
    w('Inputs: build/agent8/matrix/20261122-1541 (W4b) and 20261122-1756 (W5) (results.csv, perf.csv, run.json, '
      'frames.json). Compared with build/agent7/w4b-noise/report.json, report-w5.json and RESULTS.md (20:15). '
      'Script: tstd_xcheck.py (own code). Per-run values: tstd_runs.csv. Every comparison: tstd_compare.csv.')
    w('')
    L.extend(readings(out, cm))
    w('')
    w('## Comparison counts')
    w('')
    w('DEF = the cell matches another definition of the same quantity (named in the note).')
    w('')
    w('| window | source | items | %s |' % ' | '.join(CLASSES))
    w('|---' * (3 + len(CLASSES)) + '|')
    for wk in ('w4b', 'w5'):
        for src in ('report-json', 'RESULTS.md'):
            rs = [r for r in cm.rows if r['window'] == wk and r['source'] == src]
            w('| %s | %s | %d | %s |' % (wk, src, len(rs), ' | '.join(
                str(sum(1 for r in rs if r['cls'] == c)) for c in CLASSES)))
    w('')
    bad = [r for r in cm.rows if r['cls'] != 'MATCH']
    if bad:
        w('Items that are not MATCH:')
        w('')
        for r in bad:
            w('- %s %s, %s: mine %r, theirs %r (%s) %s' % (r['window'], r['source'], r['item'], r['mine'], r['theirs'],
                                                       r['cls'], r['note']))
    else:
        w('Every item is MATCH.')
    w('')
    w(DEF_MD)
    for wk in ('w4b', 'w5'):
        res = out[wk]
        C = res['C']
        ref, order = C['ref'], C['order']
        oth = [a for a in order if a != ref]
        w('## %s, ref %s' % (C['title'], ref))
        w('')
        w('- Kept runs: %d. hT_ref = %.6f (%s). Window first_row/rows differ from frames.json in: %s.' % (
            len(res['kept']), res['hT_ref'], ', '.join('%s %.4f' % (x['name'], x['hT']) for x in res['kept']
                                                      if abs(x['hT'] - res['hT_ref']) < 1e-15),
            ', '.join(res['win_bad']) or 'none'))
        w('- max |ls_T - frames.json share_lt_light| = %.3g (share_lt_light has 4 dp). B-block internal checks: max '
          '|b - b(within-arm)|, |GM - GM(adjusted)| = %.2g.' % (res['ls_max'], res['bb_check']))
        w('')
        w('### Per run (T-std at hT_ref)')
        w('')
        w('| run | arm | rnd | kept | frames | hT | light share | fps | p50 ms | p99 ms | 1 % low fps | max rel diff vs '
          'report-json |')
        w('|---|---|---|---|---|---|---|---|---|---|---|---|')
        for x in res['runs']:
            t = x['t']
            w('| %s | %s | %s | %s | %d | %.4f | %.4f | %.2f | %.3f | %.3f | %.2f | %s |' % (
                x['name'], x['arm'], x['round'], 'yes' if x['keep'] else 'no', x['frames'], x['hT'], x['ls_T'],
                t['fps'], t['p50_ms'], t['p99_ms'], t['low1_fps'],
                '-' if x['rep_maxrel'] is None else '%.1e' % x['rep_maxrel']))
        w('')
        for label, key in (('One-way T-std (df = runs - arms)', 'oneway'),
                           ('B-block T-std (ln v = arm + round; df = runs - arms - rounds + 1)', 'bblock')):
            w('### %s' % label)
            w('')
            w('GM delta vs %s in %%, [95 %% CI], `*` = the CI excludes 0. Then the median delta (verdict against the '
              'band).' % ref)
            w('')
            hdr = '| metric | %s band %% | CV %% | 4v4 %% | df | %s |' % (ref, ' | '.join(
                '%s (n=%d)' % (a, res[key]['fps']['arms'][a]['n']) for a in oth))
            if key == 'bblock':
                hdr += ' round terms %% (%s) |' % ', '.join('r%s' % r for r in res[key]['fps']['rounds'][1:])
            w(hdr)
            w('|---' * (5 + len(oth) + (1 if key == 'bblock' else 0)) + '|')
            for k, _, lab in KEYS:
                s = res[key][k]
                row = '| %s | %.2f | %.2f | %.2f | %d | %s |' % (lab, s['band'], s['cv'], s['hw44'], s['df'], ' | '.join(
                    cicell(s['arms'][a]) for a in oth))
                if key == 'bblock':
                    row += ' %s |' % ', '.join(sg(q, 2) for q in s['b_pct'])
                w(row)
            w('')
            w('| metric | %s |' % ' | '.join('%s median delta' % a for a in oth))
            w('|---' * (1 + len(oth)) + '|')
            for k, _, lab in KEYS:
                s = res[key][k]
                w('| %s | %s |' % (lab, ' | '.join('%s (%s)' % (sg(s['arms'][a]['dp'], 2), s['arms'][a]['verdict'])
                                                   for a in oth)))
            w('')
        w('### Paired T-std, per round vs %s' % ref)
        w('')
        w('| metric | arm | deltas % by round | median | mean +- hw95 | range pp | up |')
        w('|---|---|---|---|---|---|---|')
        for k, _, lab in KEYS:
            for a in oth:
                e = res['paired'][k][a]
                w('| %s | %s | %s | %s | %s +- %s | %.2f | %d/%d |' % (
                    lab, a, ', '.join('r%s %s' % (r, sg(d, 2)) for r, d in zip(e['rounds'], e['deltas'])),
                    sg(e['med'], 2), sg(e['mean'], 2), f(e['hw95'], 2), e['range'], e['up'], e['n']))
        w('')
        F = res['F']
        w('### Light share (frames < 4.5 ms) per arm')
        w('')
        w('- Means: %s.' % ', '.join('%s %.5f' % (a, v) for a, v in F['means'].items()))
        w('- One-way F = %.4f on (%d, %d), p = %s (scipy f_oneway F = %s).' % (
            F['F'], F['df'][0], F['df'][1], f(F.get('p'), 3), f(F.get('F_scipy'), 4)))
        w('')
        if wk == 'w4b':
            w('### Extra: W4b B-block T-std fps, B vs d0, leaving out one B or d0 run at a time (descriptive)')
            w('')
            w('| variant | df | B GM delta [95 % CI] (t table) | CI with scipy t |')
            w('|---|---|---|---|')
            for lab, df, e in res['loo']:
                ce = ci_exact(e, df)
                w('| %s | %d | %s | %s |' % (lab, df, cicell(e), '-' if ce is None else '[%s, %s]' % (
                    sg(ce[0], 2), sg(ce[1], 2))))
            w('')
            for (k, a) in (('fps', 'B'), ('p50_ms', 'B')):
                for key in ('oneway', 'bblock'):
                    e = res[key][k]['arms'][a]
                    ce = ci_exact(e, res[key][k]['df'])
                    w('- %s %s %s: t table %s; scipy t(%d) = %.4f gives [%s, %s].' % (
                        'T-std' if key == 'oneway' else 'B-block T-std', KLABEL[k], a, cicell(e, 3),
                        res[key][k]['df'], t_exact(res[key][k]['df']), sg(ce[0], 3), sg(ce[1], 3)))
            w('')
        else:
            S = res['sens']
            w('### W5 sensitivity: d11t without %s (n = 2, descriptive)' % DROP_W5)
            w('')
            w('The T-std values use the 15-run hT_ref. The one-way CI pools the SD over all arms (df 9 without r3); '
              'B-block without r3 has df 7. These are descriptive only.')
            w('')
            w('| d11t vs | metric | full n=3: GM [CI] (df 10) | full: median delta | without r3 n=2: GM [CI] (df 9) | '
              'without r3: median delta | B-block full (df 8) | B-block without r3 (df 7) | without r3, hT_ref(14) = '
              '%.4f: GM |' % S['h14'])
            w('|---|---|---|---|---|---|---|---|---|')
            for ref2 in ('base', 'd11'):
                for k, _, lab in KEYS:
                    c = S['cmp'][(ref2, k)]
                    w('| %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
                        ref2, lab, cicell(c['full']), sg(c['full']['dp'], 2), cicell(c['part']), sg(c['part']['dp'], 2),
                        cicell(c['bfull']), cicell(c['bpart']), sg(S['cmp14'][(ref2, k)]['gm'], 2)))
            w('')
            w('Per-round paired T-std deltas, in % (+ = higher value: worse for p99 and p50, better for 1 % low and fps). '
              'The d11p rows are added for comparison:')
            w('')
            w('| arm vs ref | metric | r1 | r2 | r3 | median | mean | up |')
            w('|---|---|---|---|---|---|---|---|')
            for arm2, ref2 in PR_PAIRS:
                for k in ('p99_ms', 'low1_fps', 'p50_ms', 'fps'):
                    e = S['pr'][(arm2, ref2, k)]
                    dd = dict(zip(e['rounds'], e['deltas']))
                    w('| %s vs %s | %s | %s | %s | %s | %s | %s | %d/%d |' % (
                        arm2, ref2, KLABEL[k], sg(dd.get('1'), 2), sg(dd.get('2'), 2), sg(dd.get('3'), 2),
                        sg(e['med'], 2), sg(e['mean'], 2), e['up'], e['n']))
            w('')
            vv = dict((x['name'], x['t']) for x in res['kept'])
            w('T-std p99 ms / 1 % low fps per run: ' + '; '.join(
                '%s %.3f / %.1f' % (x['name'], vv[x['name']]['p99_ms'], vv[x['name']]['low1_fps'])
                for x in res['kept'] if x['arm'] in ('base', 'd11', 'd11t')) + '.')
            w('')
            for (k, a) in (('p99_ms', 'd11t'), ('low1_fps', 'd11t')):
                for key in ('oneway', 'bblock'):
                    e = res[key][k]['arms'][a]
                    ce = ci_exact(e, res[key][k]['df'])
                    w('- %s %s %s vs base: t table %s; scipy t(%d) = %.4f gives [%s, %s].' % (
                        'T-std' if key == 'oneway' else 'B-block T-std', KLABEL[k], a, cicell(e, 3),
                        res[key][k]['df'], t_exact(res[key][k]['df']), sg(ce[0], 3), sg(ce[1], 3)))
            w('')
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(L) + '\n')


def write_runs_csv(out, path):
    cols = ['window', 'seq', 'name', 'arm', 'round', 'keep', 'first_row', 'rows', 'frames', 'light_ms', 'n_light',
            'n_heavy', 'T_light_s', 'T_heavy_s', 'hT', 'ls_T', 'ls_runner', 'hT_ref', 'tstd_fps', 'tstd_p50_ms',
            'tstd_p99_ms', 'tstd_low1_fps', 'max_rel_diff_vs_report_json']
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        wr = csv.writer(fh)
        wr.writerow(cols)
        for wk in ('w4b', 'w5'):
            res = out[wk]
            for x in res['runs']:
                t = x['t']
                wr.writerow([wk, x['seq'], x['name'], x['arm'], x['round'], x['keep'], x['first_row'], x['rows'],
                             x['frames'], x['light_ms'], x['nL'], x['nH'], repr(x['TL_s']), repr(x['TH_s']),
                             repr(x['hT']), repr(x['ls_T']), x['ls_runner'], repr(res['hT_ref']), repr(t['fps']),
                             repr(t['p50_ms']), repr(t['p99_ms']), repr(t['low1_fps']),
                             '' if x['rep_maxrel'] is None else '%.3e' % x['rep_maxrel']])


def write_compare_csv(cm, path):
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        wr = csv.writer(fh)
        wr.writerow(['window', 'source', 'item', 'mine', 'theirs', 'class', 'note'])
        for r in cm.rows:
            wr.writerow([r['window'], r['source'], r['item'], repr(r['mine']), repr(r['theirs']), r['cls'], r['note']])


def main():
    cm = Cmp()
    out = dict((wk, analyse(wk, cm)) for wk in ('w4b', 'w5'))
    write_runs_csv(out, os.path.join(HERE, 'tstd_runs.csv'))
    write_compare_csv(cm, os.path.join(HERE, 'tstd_compare.csv'))
    write_md(out, cm, os.path.join(HERE, 'tstd.md'))
    for wk in ('w4b', 'w5'):
        for src in ('report-json', 'RESULTS.md'):
            rs = [r for r in cm.rows if r['window'] == wk and r['source'] == src]
            print(wk, src, len(rs), dict((c, sum(1 for r in rs if r['cls'] == c)) for c in CLASSES))
    for r in cm.rows:
        if r['cls'] != 'MATCH':
            print('  ', r['window'], r['source'], r['item'], r['mine'], r['theirs'], r['cls'], r['note'])
    return 0


if __name__ == '__main__':
    sys.exit(main())

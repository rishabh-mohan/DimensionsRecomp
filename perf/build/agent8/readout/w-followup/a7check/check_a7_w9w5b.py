#!/usr/bin/env python3
"""Check Agent 7's W9 / W5b read-out numbers against results.csv (Agent 8, task #20).

Independent of both pool_readout.py copies: it reads only results.csv of the four
matrix folders, plus ng_t (win_ngB_mean) from Agent 8's audit runs.csv for the
load-check numbers. Every number in the checked text is compared at the posted
number of decimals (agree = the recomputed value rounds to the posted one).

Run from the workspace root:
    python -B build/agent8/readout/w-followup/a7check/check_a7_w9w5b.py
"""
import csv
import hashlib
import math
import os
import re
import sys

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_MD = os.path.join(HERE, 'W9-W5b-check.md')
A7 = 'build/agent7/readout'
MISREAD = ('MISREAD: 2.31 is the "game" (game cores) column of audit.md L257; that row\'s "ng_t mean" is 2.56 '
           '(runs.csv win_ngB_mean 2.5579, z_t -0.0). Still below 2.8 and unflagged, so the point stands')
AUDIT = 'build/agent8/readout/w-followup/audit/runs.csv'
WIN = {
    'W9': dict(ref='off', arms=['off', 'q0', 'q125', 'q250', 'q500'],
               passes=[('build/agent8/matrix/20261123-0108', 0), ('build/agent8/matrix/20261123-0401', 4)]),
    'W5b': dict(ref='d11', arms=['d11', 'd11t', 'd11p'],
                passes=[('build/agent8/matrix/20261123-0155', 0), ('build/agent8/matrix/20261123-0451', 6)]),
}
LOWCLK = ['0407-q125-r1', '0409-q250-r1', '0419-q500-r2', '0423-q125-r3']
FLAG9 = ['0122-q125-r2', '0124-q250-r2', '0407-q125-r1', '0409-q250-r1', '0417-q250-r2', '0419-q500-r2',
         '0423-q125-r3']
SLOWQ = ['0407-q125-r1', '0423-q125-r3', '0409-q250-r1', '0417-q250-r2']
FLAG5 = ['0209-d11p-r3', '0213-d11t-r3', '0453-d11-r1', '0455-d11t-r1', '0457-d11p-r1', '0510-d11t-r3']
R1 = ['p1:r1', 'p2:r1']
RND = {'fps': 1, 'med': 3, 'p99': 2, 'p999': 2, 'cores': 2, 'eff': 0, 'light': 3}
FIELD = {'median ms': 'med', 'fps': 'fps', 'p99 ms': 'p99'}
FIELD_OF = {'raw median ms': 'med', 'raw fps': 'fps', 'raw p99 ms': 'p99', 'cpu cores change': 'cores'}
POOLS9 = {'all 40': [], 'no-flagged': FLAG9, 'no-lowclk-no-r1': LOWCLK + R1, 'no-lowclk': LOWCLK,
          'no-slow-q': SLOWQ, 'drop-p2-r1r3': ['p2:r1', 'p2:r3'], 'drop-r1-both': R1,
          'pass 1 only': ['p2'], 'pass 2 only': ['p1']}
FLAG5X = FLAG5 + ['0459-d11t-r2']  # + the runner's slow d11t r1-r2 (0455-d11t-r1 is already an audit flag)
POOLS5 = {'all 36': [], 'no-flagged': FLAG5X, 'no-loaded': FLAG5X + ['0520-d11p-r5', '0524-d11p-r6'],
          'no-audit-flag': FLAG5, 'no-slow-d11t': ['0455-d11t-r1', '0459-d11t-r2'], 'no-0221': ['0221-d11t-r5'],
          'no-p2-first3': ['0453-d11-r1', '0455-d11t-r1', '0457-d11p-r1'], 'drop-p2-r1r2': ['p2:r1', 'p2:r2'],
          'drop-r1-both': R1, 'pass 1 only': ['p2'], 'pass 2 only': ['p1']}


def sha16(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest().upper()[:16]


# ---------------------------------------------------------------- data
ALL, KEPT, NAMES, SHA = {}, {}, {}, {}
for w, cfg in WIN.items():
    ALL[w], KEPT[w] = [], []
    for p, (d, off) in enumerate(cfg['passes'], 1):
        path = os.path.join(d, 'results.csv')
        SHA[d] = sha16(path)
        with open(path, newline='', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                rl = int(r['round'])
                rec = dict(run=os.path.basename(r['run_dir'].rstrip('\\/')), arm=r['arm'], p=p, rl=rl,
                           rnd=rl + off if rl > 0 else 0, scored=r['scored'] == 'True', status=r['status'],
                           valid=r['valid_timing'] == 'True', excl=r['excluded'] == 'True',
                           frames=int(r['frames']), med=float(r['median_ms']), p99=float(r['p99_ms']),
                           p999=float(r['p999_ms']), mx=float(r['max_ms']), o33=int(r['over33']),
                           fps=float(r['fps_mean']), cores=float(r['cpu_cores_mean']),
                           light=float(r['light_share']) if r['light_share'] else float('nan'),
                           eff=float(r['eff_mhz']) if r['eff_mhz'] else float('nan'))
                ALL[w].append(rec)
                if rec['scored'] and rec['status'] == 'OK' and rec['valid'] and not rec['excl'] and rl > 0:
                    KEPT[w].append(rec)
    NAMES[w] = {r['run'] for r in ALL[w]}
RUN = {r['run']: r for w in ALL for r in ALL[w]}
NG, NGMAX, WU = {}, {}, {}  # window mean, window 1 s max, warm-up mean of non-game busy cores (audit runs.csv)
with open(AUDIT, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['run'] in RUN:
            for dd, k in ((NG, 'win_ngB_mean'), (NGMAX, 'win_ngB_max'), (WU, 'wu_ngB_mean')):
                if r[k]:
                    dd[r['run']] = float(r[k])


# ---------------------------------------------------------------- stats
TC = {}


def tcrit(df):
    if df not in TC:
        TC[df] = float(stats.t.ppf(0.975, df))
    return TC[df]


def ar(rows, a):
    return [r for r in rows if r['arm'] == a]


def rv(r, f, rnd=False):
    return round(r[f], RND[f]) if rnd else r[f]


def med(rows, f, rnd=False):
    return float(np.median([rv(r, f, rnd) for r in rows]))


def mean(rows, f, rnd=False):
    return float(np.mean([rv(r, f, rnd) for r in rows]))


def oneway(rows, f, arms, a, b, log, rnd=False):
    """a - b with the pooled one-way 95 % CI over all arms in rows (GM % if log)."""
    g = {}
    for r in rows:
        x = rv(r, f, rnd)
        g.setdefault(r['arm'], []).append(math.log(x) if log else x)
    N = sum(len(v) for v in g.values())
    df = N - len(g)
    ss = sum(sum((x - np.mean(v)) ** 2 for x in v) for v in g.values())
    s = math.sqrt(ss / df)
    d = float(np.mean(g[a]) - np.mean(g[b]))
    h = tcrit(df) * s * math.sqrt(1 / len(g[a]) + 1 / len(g[b]))
    if log:
        e = lambda x: 100.0 * (math.exp(x) - 1)
        return [e(d), e(d - h), e(d + h)], df, s
    return [d, d - h, d + h], df, s


def bblock(rows, f, arms, a, b, log):
    """a - b from the additive arm + round model (B-block), 95 % CI."""
    A = [x for x in arms if any(r['arm'] == x for r in rows)]
    R = sorted({r['rnd'] for r in rows})
    others = [x for x in A if x != b]
    X = np.array([[1.0] + [1.0 if r['arm'] == x else 0.0 for x in others] +
                  [1.0 if r['rnd'] == q else 0.0 for q in R[1:]] for r in rows])
    y = np.array([math.log(r[f]) if log else r[f] for r in rows])
    XtXi = np.linalg.inv(X.T @ X)
    beta = XtXi @ X.T @ y
    res = y - X @ beta
    df = len(y) - X.shape[1]
    s2 = float(res @ res) / df
    i = 1 + others.index(a)
    d = float(beta[i])
    h = tcrit(df) * math.sqrt(s2 * XtXi[i, i])
    if log:
        e = lambda x: 100.0 * (math.exp(x) - 1)
        return [e(d), e(d - h), e(d + h)]
    return [d, d - h, d + h]


def paired(rows, f, a, b, rnd=False):
    by = {}
    for r in rows:
        by.setdefault(r['rnd'], {})[r['arm']] = r
    ds, byround, byrun = [], {}, {}
    for q in sorted(by):
        v = by[q]
        if a in v and b in v:
            x, y = rv(v[a], f, rnd), rv(v[b], f, rnd)
            d = 100.0 * (x - y) / y
            ds.append(d)
            byround[q] = d
            byrun[v[a]['run']] = d
    n = len(ds)
    sd = float(np.std(ds, ddof=1)) if n > 1 else float('nan')
    hw = tcrit(n - 1) * sd / math.sqrt(n) if n > 1 else float('nan')
    hi = sum(1 for d in ds if d > 0)
    lo = sum(1 for d in ds if d < 0)
    k = min(hi, n - hi)
    p = min(1.0, 2.0 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)
    return dict(n=n, mean=float(np.mean(ds)), hw=hw, med=float(np.median(ds)), hi=hi, lo=lo, p=p, ds=ds,
                byround=byround, byrun=byrun)


def subset(rows, toks, w):
    for t in toks:
        if not re.fullmatch(r'p\d(:r\d+)?', t) and t not in NAMES[w]:
            sys.exit(f'unknown run token {t!r} for {w}')
    out = []
    for r in rows:
        drop = False
        for t in toks:
            m = re.fullmatch(r'p(\d)(?::r(\d+))?', t)
            if m:
                if r['p'] == int(m.group(1)) and (m.group(2) is None or r['rl'] == int(m.group(2))):
                    drop = True
            elif r['run'] == t:
                drop = True
        if not drop:
            out.append(r)
    return out


def anova(rows, f, arms):
    groups = [[r[f] for r in rows if r['arm'] == a] for a in arms]
    groups = [g for g in groups if g]
    F = float(stats.f_oneway(*groups).statistic)
    N = sum(len(g) for g in groups)
    return F, len(groups) - 1, N - len(groups)


def base(w, arm, rnd):
    q = [r for r in KEPT[w] if r['arm'] == arm and NG[r['run']] < 2.8]
    return {f: med(q, f, rnd) for f in ('fps', 'med', 'cores', 'eff')}, len(q)


def loaded(w, run, rnd):
    r = RUN[run]
    b, _ = base(w, r['arm'], rnd)
    fps, ms, cores, eff = rv(r, 'fps', rnd), rv(r, 'med', rnd), rv(r, 'cores', rnd), rv(r, 'eff', rnd)
    const = b['cores'] * b['eff'] / eff
    return dict(ng=NG[run], eff=eff, effp=100 * (eff / b['eff'] - 1), fps=fps, fpsp=100 * (fps / b['fps'] - 1),
                ms=ms, msp=100 * (ms / b['med'] - 1), cores=cores, coresd=cores - b['cores'], const=const,
                rest=cores - const, frames=r['frames'])


# ---------------------------------------------------------------- claims
NUM = re.compile(r'(?<![A-Za-z\d.])[-+]?\d+(?:\.\d+)?')
CL = []
LIGHT_NOTE = ("light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share "
              'rounded to 3 dp')


def gap(vs, ps, ds):
    """Largest |recomputed - posted| in last-digit units of the posted number, and the number of sign flips."""
    if vs is None or len(vs) != len(ps) or any(isinstance(v, float) and math.isnan(v) for v in vs):
        return None
    u = max((abs(v - p) / 10 ** -d for v, p, d in zip(vs, ps, ds)), default=0.0)
    fl = sum(1 for v, p, d in zip(vs, ps, ds) if abs(p) >= 10 ** -d - 1e-12 and v * p < 0)
    return u, fl


def fmtv(v, d):
    if isinstance(v, float) and math.isnan(v):
        return 'nan'
    if d == 0 and abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f'{v:.{d + 1}f}'


def claim(src, what, posted, vals, alt=None, alt_label='rounded inputs', cat='main', note=''):
    toks = NUM.findall(posted)
    ps = [float(t) for t in toks]
    ds = [len(t.split('.')[1]) if '.' in t else 0 for t in toks]

    def ok(vs):
        return vs is not None and len(vs) == len(ps) and all(
            not (isinstance(v, float) and math.isnan(v)) and abs(v - p) <= 0.5 * 10 ** -d + 1e-9
            for v, p, d in zip(vs, ps, ds))

    gs = [g for g in (gap(vals, ps, ds), gap(alt, ps, ds)) if g is not None]
    units, flips = min(gs) if gs else (None, None)
    if len(vals) != len(ps):
        verdict = f'PARSE ({len(ps)} posted vs {len(vals)} recomputed)'
        rec = ' '.join(fmtv(v, 3) for v in vals)
    else:
        rec = ' '.join(fmtv(v, d) for v, d in zip(vals, ds))
        if ok(vals):
            verdict = 'agree'
        elif alt is not None and ok(alt):
            verdict = f'agree ({alt_label})'
            rec += f' / {alt_label}: ' + ' '.join(fmtv(v, d) for v, d in zip(alt, ds))
        else:
            verdict = 'DISAGREE'
            if alt is not None and len(alt) == len(ps):
                rec += f' / {alt_label}: ' + ' '.join(fmtv(v, d) for v, d in zip(alt, ds))
    CL.append(dict(src=src, what=what, posted=posted, rec=rec, verdict=verdict, cat=cat, n=len(ps), note=note,
                   units=units, flips=flips))


def cells(line):
    s = line.strip()
    if not (s.startswith('|') and s.endswith('|')):
        return None
    return [c.strip() for c in s[1:-1].split('|')]


def is_sep(c):
    return all(re.fullmatch(r':?-{3,}:?', x) for x in c)


def read(fname):
    with open(os.path.join(A7, fname), encoding='utf-8') as f:
        return f.read().splitlines()


# ---------------------------------------------------------------- pool-*.md
PLIGHT = {}


def parse_pool(fname, w):
    cfg = WIN[w]
    ref, arms, rows = cfg['ref'], cfg['arms'], KEPT[w]
    sec = hdr = vname = vrows = None
    PLIGHT[w], pend = {}, []
    for i, line in enumerate(read(fname), 1):
        src = f'{fname} L{i}'
        if line.startswith('## '):
            sec, hdr, vname = line[3:].split('.')[0].strip(), None, None
            continue
        m = re.match(r'\*\*(\S+)\*\* \(left out: (.*?)\): primary', line)
        if m:
            vname = m.group(1)
            vrows = subset(rows, [t.strip() for t in m.group(2).split(',')], w)
            hdr = None
            continue
        c = cells(line)
        if c is None:
            hdr = None
            m = re.search(r'Light share per arm: (.*?)\. One-way F = ([\d.]+) on \((\d+), (\d+)\)', line)
            if m:
                pend.append((src, re.findall(r'(\w+) ([\d.]+)', m.group(1)), m.group(2), m.group(3), m.group(4)))
            continue
        if is_sep(c):
            continue
        if hdr is None:
            hdr = c
            continue
        if sec == '1':
            a = c[0]
            allr = ar(ALL[w], a)
            claim(src, f'{w} {a}: planned (+cold), rows, timed, kept, failed', ' '.join(c[1:6]),
                  [sum(1 for r in allr if r['rl'] > 0), sum(1 for r in allr if r['rl'] == 0), len(allr),
                   sum(1 for r in allr if r['rl'] > 0 and r['valid']), len(ar(rows, a)),
                   sum(1 for r in allr if r['status'] != 'OK')], cat='count')
        elif sec == '2' and c[0] == 'raw' and c[1] in FIELD:
            f = FIELD[c[1]]
            harms = [re.match(r'(\S+) \(n=(\d+)\)', x).groups() for x in hdr[6:]]
            for j, (a, n) in enumerate(harms):
                v, df, s = oneway(rows, f, arms, a, ref, True)
                claim(src, f'{w} raw {c[1]} GM % {a} vs {ref} [95 % CI], one-way', c[6 + j], v)
            claim(src, f'{w} raw {c[1]}: n per arm', ' '.join(n for _, n in harms),
                  [len(ar(rows, a)) for a, _ in harms], cat='count')
            v, df, s = oneway(rows, f, arms, harms[0][0], ref, True)
            refv = [r[f] for r in ar(rows, ref)]
            cv = 100 * s
            claim(src, f'{w} raw {c[1]}: {ref} band % ((max-min)/median), pooled CV %, 4 vs 4 band %, df',
                  ' '.join(c[2:6]),
                  [100 * (max(refv) - min(refv)) / float(np.median(refv)), cv,
                   100 * (math.exp(tcrit(df) * s * math.sqrt(0.5)) - 1), df], cat='aux',
                  note='4 vs 4 band = 100 (exp(t s sqrt(1/2)) - 1), s = pooled SD of ln')
        elif sec == '3' and c[0] == 'cpu cores':
            claim(src, f'{w} {ref} mean cores', c[1], [mean(ar(rows, ref), 'cores')])
            for j, a in enumerate([x.split(':')[0] for x in hdr[2:]]):
                lin = oneway(rows, 'cores', arms, a, ref, False)[0]
                g1 = oneway(rows, 'cores', arms, a, ref, True)[0]
                gb = bblock(rows, 'cores', arms, a, ref, True)
                claim(src, f'{w} cores {a}: mean; change [CI]; GM % one-way [CI]; GM % B-block [CI]', c[2 + j],
                      [mean(ar(rows, a), 'cores')] + lin + g1 + gb)
        elif sec == '4' and c[0] in ('raw median ms', 'raw fps', 'cpu cores'):
            f = {'raw median ms': 'med', 'raw fps': 'fps', 'cpu cores': 'cores'}[c[0]]
            for j, a in enumerate(hdr[1:]):
                P = paired(rows, f, a, ref)
                claim(src, f'{w} paired {c[0]} {a} vs {ref}: mean +- hw (med; higher k/n)', c[1 + j],
                      [P['mean'], P['hw'], P['med'], P['hi'], P['n']])
        elif sec == '5':
            pn = int(c[0])
            sub = [r for r in rows if r['p'] == pn]
            claim(src, f'{w} pass {pn}: kept', c[1], [len(sub)], cat='count')
            for j, a in enumerate([x.split(':')[0] for x in hdr[3:]]):
                claim(src, f'{w} pass {pn} alone: cores change {a} [CI]', c[3 + j].split(';')[-1],
                      oneway(sub, 'cores', arms, a, ref, False)[0])
        elif sec == '6' and vname and c[0] in FIELD_OF:
            f = FIELD_OF[c[0]]
            harms = [re.match(r'(\S+) \(n=(\d+)\)', x).groups() for x in hdr[1:]]
            if c[0] == 'raw median ms':
                claim(src, f'{w} {vname}: n per arm', ' '.join(n for _, n in harms),
                      [len(ar(vrows, a)) for a, _ in harms], cat='count')
            for j, (a, n) in enumerate(harms):
                claim(src, f'{w} {vname}: {c[0]} {a}', c[1 + j], oneway(vrows, f, arms, a, ref, f != 'cores')[0])
        elif sec == '8' and hdr[0] == 'seq':
            r = RUN.get(c[4])
            if r is None:
                claim(src, f'run {c[4]} not in results.csv', 'x', [], cat='run')
                continue
            claim(src, f'{c[4]}: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept',
                  ' '.join([c[7], c[8], c[10], c[11], c[12], c[16]]) + (' 1' if c[6].startswith('yes') else ' 0'),
                  [r['frames'], r['med'], r['fps'], r['p99'], r['cores'], r['eff'], 1 if r in rows else 0], cat='run')
            lt = NUM.findall(c[23])
            if lt:
                PLIGHT[w][c[4]] = float(lt[0])
            claim(src, f'{c[4]}: light share', c[23], [r['light']], cat='aux',
                  note=LIGHT_NOTE if lt and abs(float(lt[0]) - r['light']) > 0.0005 + 1e-9 else '')
    pl = [dict(r, light=PLIGHT[w][r['run']]) for r in rows if r['run'] in PLIGHT[w]]
    full = len(pl) == len(rows)
    for src, pairs, Fp, a1, a2 in pend:
        claim(src, f'{w} light share per arm (mean of results.csv light_share)', ' '.join(v for _, v in pairs),
              [mean(ar(rows, a), 'light') for a, _ in pairs],
              alt=[mean(ar(pl, a), 'light') for a, _ in pairs] if full else None,
              alt_label='posted run-table light shares', note=LIGHT_NOTE)
        claim(src, f'{w} light share one-way F (df1, df2)', f'{Fp} ({a1}, {a2})', list(anova(rows, 'light', arms)),
              alt=list(anova(pl, 'light', arms)) if full else None, alt_label='posted run-table light shares',
              cat='aux', note=LIGHT_NOTE)


# ---------------------------------------------------------------- W9.md tables
def match_pool(label):
    return max((k for k in POOLS9 if label.startswith(k)), key=len)


def parse_w9md():
    fname, w = 'W9.md', 'W9'
    ref, arms, rows = 'off', WIN[w]['arms'], KEPT[w]
    sec = hdr = metric = None
    for i, line in enumerate(read(fname), 1):
        src = f'{fname} L{i}'
        if line.startswith('## '):
            sec, hdr = line[3:].split('.')[0].strip(), None
            continue
        c = cells(line)
        if c is None:
            hdr = None
            continue
        if is_sep(c):
            continue
        if hdr is None:
            hdr = c
            continue
        h0 = hdr[0]
        if h0 == 'arm' and len(hdr) > 1 and hdr[1] == 'planned (+cold)':
            allr = ar(ALL[w], c[0])
            cold = [sum(1 for r in allr if r['rl'] == 0)] if '(+' in c[1] else []
            claim(src, f'W9 {c[0]}: planned (+cold), timed, kept, failed', ' '.join(c[1:5]),
                  [sum(1 for r in allr if r['rl'] > 0)] + cold +
                  [sum(1 for r in allr if r['rl'] > 0 and r['valid']), len(ar(rows, c[0])),
                   sum(1 for r in allr if r['status'] != 'OK')], cat='count')
        elif h0 == 'metric' and len(hdr) > 1 and hdr[1] == 'method':
            if c[0]:
                metric = c[0]
            if c[1] == 'raw' and metric in FIELD:
                for j, a in enumerate(hdr[2:]):
                    claim(src, f'W9 raw {metric} GM % {a} vs off [CI]', c[2 + j],
                          oneway(rows, FIELD[metric], arms, a, ref, True)[0])
        elif h0 == 'metric' and len(hdr) > 1 and hdr[1] == 'off' and c[0] == 'cores':
            claim(src, 'W9 off mean cores', c[1], [mean(ar(rows, 'off'), 'cores')])
            for j, a in enumerate(hdr[2:]):
                claim(src, f'W9 cores {a}: change [CI]; GM % one-way', c[2 + j].replace('*', ''),
                      oneway(rows, 'cores', arms, a, ref, False)[0] + [oneway(rows, 'cores', arms, a, ref, True)[0][0]])
        elif h0 == 'metric' and hdr[1:] == ['q0', 'q125', 'q250', 'q500'] and c[0] in ('raw median ms', 'raw fps', 'cores'):
            f = {'raw median ms': 'med', 'raw fps': 'fps', 'cores': 'cores'}[c[0]]
            for j, a in enumerate(hdr[1:]):
                P = paired(rows, f, a, ref)
                nn = len(NUM.findall(c[1 + j]))
                vals = [P['mean'], P['hw'], P['med'], P['hi'], P['n']] if nn == 5 else [P['mean'], P['hw'], P['hi'], P['n']]
                claim(src, f'W9 paired {c[0]} {a} vs off: mean +- hw (med; higher k/n)', c[1 + j], vals)
        elif h0 == 'arm' and len(hdr) > 1 and hdr[1] == 'fps':
            a = c[0]
            rs = ar(rows, a)
            top = max(rs, key=lambda r: r['mx'])
            m = re.match(r'([\d.]+)(?: \((\S+)\))?', c[4])
            note = ''
            if m.group(2):
                note = 'run agrees' if m.group(2) == top['run'] else f'longest-frame run: posted {m.group(2)}, recomputed {top["run"]}'
            o33 = sum(r['o33'] for r in rs)
            claim(src, f'W9 tails {a}: median fps, median p99, p99.9 median / mean, longest frame, frames > 33 ms',
                  f'{c[1]} {c[2]} {c[3]} {m.group(1)} {c[5]}',
                  [med(rs, 'fps'), med(rs, 'p99'), med(rs, 'p999'), mean(rs, 'p999'), top['mx'], o33],
                  alt=[med(rs, 'fps', True), med(rs, 'p99', True), med(rs, 'p999'), mean(rs, 'p999'), top['mx'], o33],
                  note=note)
        elif h0 == 'pass 2':
            p2 = [r for r in rows if r['p'] == 2]
            q, o = ar(p2, 'q500'), ar(p2, 'off')
            note = ''
            if c[0].startswith('cores'):
                vals = [mean(q, 'cores'), mean(o, 'cores'), mean(q, 'cores') - mean(o, 'cores'),
                        100 * (mean(q, 'cores') / mean(o, 'cores') - 1)]
                qr, or_ = mean(q, 'cores', True), mean(o, 'cores', True)
                alt = [qr, or_, qr - or_, 100 * (round(qr, 2) / or_ - 1)]
                note = 'rounded inputs: 2-dp run cores; the % uses the printed q500 mean'
            else:
                f = 'fps' if c[0].startswith('fps') else ('p999' if c[0].startswith('p99.9') else 'p99')
                vals = [med(q, f), med(o, f), 100 * (med(q, f) / med(o, f) - 1)]
                alt = [med(q, f, True), med(o, f, True), 100 * (med(q, f, True) / med(o, f, True) - 1)]
            claim(src, f'W9 pass 2 q500, off, change: {c[0]}', ' '.join(c[1:4]), vals, alt=alt, note=note)
        elif h0 == 'run' and len(hdr) > 2 and hdr[2] == 'ng_t':
            keys = ['ng', 'eff', 'cores', 'frames', 'fps', 'fpsp', 'msp']
            full, rr = loaded(w, c[0], False), loaded(w, c[0], True)
            claim(src, f'{c[0]}: ng_t (audit), eff MHz, cores, frames, fps (vs arm %), raw median ms vs arm %',
                  ' '.join([c[2], c[3], c[5], c[6], c[7], c[8]]), [full[k] for k in keys], alt=[rr[k] for k in keys])
        elif h0.startswith('pool (runs left out)'):
            sub = subset(rows, POOLS9[match_pool(c[0])], w)
            claim(src, f'W9 {c[0]}: n q500', c[1], [len(ar(sub, 'q500'))], cat='count')
            for col, f in ((7, 'med'), (8, 'fps'), (9, 'p99')):
                claim(src, f'W9 {c[0]}: q500 raw {f} GM % [CI]', c[col], oneway(sub, f, arms, 'q500', ref, True)[0])
        elif h0 == 'pool' and len(hdr) > 5 and hdr[5].startswith('q500 - q250'):
            sub = subset(rows, POOLS9[match_pool(c[0])], w)
            for j, a in enumerate(['q0', 'q125', 'q250', 'q500']):
                claim(src, f'W9 {c[0]}: cores change {a} [CI]', c[1 + j], oneway(sub, 'cores', arms, a, ref, False)[0],
                      alt=oneway(sub, 'cores', arms, a, ref, False, True)[0])
            for j, (a, b) in enumerate((('q500', 'q250'), ('q500', 'q125'))):
                if c[5 + j] != '-':
                    claim(src, f'W9 {c[0]}: cores {a} - {b} [CI]', c[5 + j], oneway(sub, 'cores', arms, a, b, False)[0],
                          alt=oneway(sub, 'cores', arms, a, b, False, True)[0])


# ---------------------------------------------------------------- W9.md prose
def hand_w9():
    F, w = 'W9.md', 'W9'
    rows, arms = KEPT[w], WIN[w]['arms']
    R = RUN
    nf = subset(rows, FLAG9, w)
    nr1 = subset(rows, R1, w)
    cores = lambda rs, a, b='off': oneway(rs, 'cores', arms, a, b, False)[0]
    gm = lambda rs, f, a, b='off': oneway(rs, f, arms, a, b, True)[0]
    claim(f'{F} L35', 'q500 cores change [CI], GM %', '-0.75 core [-0.86, -0.64], -30.0 %',
          cores(rows, 'q500') + [gm(rows, 'cores', 'q500')[0]])
    claim(f'{F} L35', 'no-flagged q500 cores change [CI]', '-0.79 core [-0.84, -0.73]', cores(nf, 'q500'))
    p2 = [r for r in rows if r['p'] == 2]
    q, o = ar(p2, 'q500'), ar(p2, 'off')
    claim(f'{F} L36', 'pass 2 q500 vs off: cores change, cores %, fps (medians) %, p99 median q500, off',
          '-0.70 core (-27.9 %), fps +1.1 %, p99 4.675 vs 4.985 ms',
          [mean(q, 'cores') - mean(o, 'cores'), 100 * (mean(q, 'cores') / mean(o, 'cores') - 1),
           100 * (med(q, 'fps') / med(o, 'fps') - 1), med(q, 'p99'), med(o, 'p99')],
          alt=[mean(q, 'cores', True) - mean(o, 'cores', True),
               100 * (round(mean(q, 'cores', True), 2) / mean(o, 'cores', True) - 1),
               100 * (med(q, 'fps', True) / med(o, 'fps', True) - 1), med(q, 'p99', True), med(o, 'p99', True)])
    claim(f'{F} L37', 'q0 cores change [CI]', '-0.03 core [-0.14, +0.08]', cores(rows, 'q0'))
    P = paired(rows, 'med', 'q0', 'off')
    claim(f'{F} L37', 'q0 raw median ms higher than off in k of n rounds', '8 of 8', [P['hi'], P['n']])
    lq = ['0407-q125-r1', '0409-q250-r1', '0417-q250-r2', '0419-q500-r2', '0423-q125-r3', '0425-q250-r3']
    claim(f'{F} L38', 'ng_t range of the 6 loaded q runs (audit win_ngB_mean)', '2.91 to 4.06',
          [min(NG[x] for x in lq), max(NG[x] for x in lq)])
    claim(f'{F} L38', 'no-flagged cores change q125, q250, q500', '-0.72, -0.72, -0.79',
          [cores(nf, a)[0] for a in ('q125', 'q250', 'q500')])
    claim(f'{F} L52', 'cold runs left out', '2', [sum(1 for r in ALL[w] if r['rl'] == 0)], cat='count')
    Fv, d1, d2 = anova(rows, 'light', arms)
    pl = [dict(r, light=PLIGHT[w][r['run']]) for r in rows if r['run'] in PLIGHT[w]]
    claim(f'{F} L78', 'light share per arm (mean of light_share)', '0.968 0.970 0.983 0.986 0.984',
          [mean(ar(rows, a), 'light') for a in arms])
    claim(f'{F} L78', 'light share one-way F (df1, df2)', '9.38 (4, 35)', [Fv, d1, d2],
          alt=list(anova(pl, 'light', arms)) if len(pl) == len(rows) else None, alt_label='posted run-table light shares',
          cat='aux', note=LIGHT_NOTE)
    claim(f'{F} L85', '0110-off-r1 fps (frames), 0112-q0-r1 fps, 0114-q125-r1 fps', '443.7 (22187), 414.6, 395.5',
          [R['0110-off-r1']['fps'], R['0110-off-r1']['frames'], R['0112-q0-r1']['fps'], R['0114-q125-r1']['fps']])
    claim(f'{F} L86', '0403-off-r1 fps', '408.9', [R['0403-off-r1']['fps']])
    o6 = [r for r in ar(rows, 'off') if r['run'] not in ('0110-off-r1', '0403-off-r1')]
    claim(f'{F} L87', 'fps range of the other 6 off runs', '382.2 to 386.6',
          [min(r['fps'] for r in o6), max(r['fps'] for r in o6)])
    o7 = [r for r in ar(rows, 'off') if r['run'] != '0110-off-r1']
    claim(f'{F} L88', '0110-off-r1 light share vs the other 7 off runs (range)', '0.982 vs 0.962 to 0.974',
          [R['0110-off-r1']['light'], min(r['light'] for r in o7), max(r['light'] for r in o7)],
          alt=[R['0110-off-r1']['light'], min(r['light'] for r in o6), max(r['light'] for r in o6)],
          alt_label='other 6 off runs')
    claim(f'{F} L88', '0110-off-r1 eff MHz; other 7 off runs eff range', '1992; 1907 to 2027',
          [R['0110-off-r1']['eff'], min(r['eff'] for r in o7), max(r['eff'] for r in o7)])
    P = paired(nr1, 'fps', 'q500', 'off')
    Pr = paired(nr1, 'fps', 'q500', 'off', True)
    claim(f'{F} L135', 'q500 vs off without each pass r1, raw fps: higher k of n; min, max, mean %; sign p',
          '6 of 6 (+0.91 to +1.64 %, mean +1.19 %, sign p 0.031)',
          [P['hi'], P['n'], min(P['ds']), max(P['ds']), P['mean'], P['p']],
          alt=[Pr['hi'], Pr['n'], min(Pr['ds']), max(Pr['ds']), Pr['mean'], Pr['p']])
    P = paired(nr1, 'med', 'q500', 'off')
    claim(f'{F} L135', 'q500 vs off without r1, raw median ms: lower k of n; range %', 'lower in 6 of 6 (-4.58 to -6.76 %)',
          [P['lo'], P['n'], max(P['ds']), min(P['ds'])])
    P1, P2 = paired(nr1, 'fps', 'q125', 'off'), paired(nr1, 'fps', 'q250', 'off')
    P1r, P2r = paired(nr1, 'fps', 'q125', 'off', True), paired(nr1, 'fps', 'q250', 'off', True)
    claim(f'{F} L136', 'without r1, raw fps higher: q125 k of n, q250 k of n; misses 0423-q125-r3 %, 0417-q250-r2 %',
          '5 of 6, 5 of 6; -4.36 %; -0.81 %',
          [P1['hi'], P1['n'], P2['hi'], P2['n'], P1['byrun']['0423-q125-r3'], P2['byrun']['0417-q250-r2']],
          alt=[P1r['hi'], P1r['n'], P2r['hi'], P2r['n'], P1r['byrun']['0423-q125-r3'], P2r['byrun']['0417-q250-r2']])
    claim(f'{F} L162', 'q500 cores change [CI]', '-0.75 [-0.86, -0.64]', cores(rows, 'q500'))
    claim(f'{F} L163', 'q500 raw p99 GM % [CI]', '-6.2 % [-9.7, -2.6]', gm(rows, 'p99', 'q500'))
    P = paired(nr1, 'fps', 'q500', 'off')
    Pr = paired(nr1, 'fps', 'q500', 'off', True)
    claim(f'{F} L164', 'q500 paired raw fps without r1: mean %, higher k of n', '+1.19 % (6 of 6)', [P['mean'], P['hi'], P['n']],
          alt=[Pr['mean'], Pr['hi'], Pr['n']])
    claim(f'{F} L166', 'q500 pooled raw fps GM % [CI]', '-1.3 % [-4.3, +1.7]', gm(rows, 'fps', 'q500'))
    claim(f'{F} L171', 'q0 cores change [CI] (GM % [CI])', '-0.03 [-0.14, +0.08] (-1.1 % [-6.7, +4.8])',
          cores(rows, 'q0') + gm(rows, 'cores', 'q0'))
    P = paired(rows, 'cores', 'q0', 'off')
    claim(f'{F} L171', 'q0 paired cores: lower in k of n rounds; mean +- hw %', '7 of 8; -1.09 +- 1.40 %',
          [P['lo'], P['n'], P['mean'], P['hw']])
    P = paired(rows, 'med', 'q0', 'off')
    claim(f'{F} L174', 'q0 raw median ms higher in k of n rounds (sign p)', '8 of 8 (sign p 0.008)', [P['hi'], P['n'], P['p']])
    P = paired(nr1, 'med', 'q0', 'off')
    claim(f'{F} L175', 'q0 without r1: higher k of n (p); raw range %; mean %', '6 of 6 (p 0.031): +0.12 to +1.31 % (mean +0.45 %)',
          [P['hi'], P['n'], P['p'], min(P['ds']), max(P['ds']), P['mean']])
    claim(f'{F} L179', 'q0 raw fps GM %, raw p99 GM %', '-1.4, -0.7',
          [gm(rows, 'fps', 'q0')[0], gm(rows, 'p99', 'q0')[0]])
    claim(f'{F} L180', 'light share q0 vs off', '0.970 vs 0.968', [mean(ar(rows, 'q0'), 'light'), mean(ar(rows, 'off'), 'light')])
    a, b = R['0407-q125-r1'], R['0423-q125-r3']
    c_, d_ = R['0409-q250-r1'], R['0417-q250-r2']
    claim(f'{F} L185', 'q125 r1/r3 (0407, 0423) cores range, mean frames (k); q250 0409/0417 mean frames (k)',
          '2.13 to 2.15 cores, ~18.3k; ~18.9k',
          [min(a['cores'], b['cores']), max(a['cores'], b['cores']), (a['frames'] + b['frames']) / 2000,
           (c_['frames'] + d_['frames']) / 2000])
    trio = ['0411-q500-r1', '0413-q0-r2', '0415-q125-r2']
    claim(f'{F} L207', '0411-q500-r1, 0413-q0-r2, 0415-q125-r2: ng_t range; fps each', '2.28 to 2.36; 388.7 / 385.1 / 391.0',
          [min(NG[x] for x in trio), max(NG[x] for x in trio)] + [R[x]['fps'] for x in trio])
    late = [r for r in rows if r['p'] == 2 and int(r['run'][:4]) >= 428 and NG[r['run']] >= 2.8]
    claim(f'{F} L208', 'pass-2 kept runs from 04:28 on with ng_t >= 2.8: count; ng_t of 0440-q0-r4', '1; 2.81',
          [len(late), NG['0440-q0-r4']], note='runs: ' + ', '.join(r['run'] for r in late))
    p1ng = [NG[r['run']] for r in rows if r['p'] == 1]
    p2q = [NG[r['run']] for r in rows if r['p'] == 2 and NG[r['run']] < 2.8]
    claim(f'{F} L209', 'pass 1: runs with ng_t >= 2.8, ng_t range; pass-2 quiet median ng_t', '0 (range 2.16 to 2.77); 2.33',
          [sum(1 for x in p1ng if x >= 2.8), min(p1ng), max(p1ng), float(np.median(p2q))])
    q125o = [r for r in ar(rows, 'q125') if r['run'] not in ('0407-q125-r1', '0423-q125-r3')]
    claim(f'{F} L211', "q125's other 6 runs: fps range, cores range", '387.8 to 395.5 fps at 1.73 to 1.89 cores',
          [min(r['fps'] for r in q125o), max(r['fps'] for r in q125o), min(r['cores'] for r in q125o), max(r['cores'] for r in q125o)])
    q250q = [r for r in ar(rows, 'q250') if NG[r['run']] < 2.8]
    claim(f'{F} L212', "q250's quiet runs: n; fps range, cores range", '5 quiet runs: 386.1 to 389.9 fps at 1.71 to 1.91 cores',
          [len(q250q), min(r['fps'] for r in q250q), max(r['fps'] for r in q250q), min(r['cores'] for r in q250q),
           max(r['cores'] for r in q250q)])
    qq = [r for r in rows if r['arm'] in ('q125', 'q250', 'q500') and NG[r['run']] < 2.8]
    oq = [r for r in ar(rows, 'off') if NG[r['run']] < 2.8]
    claim(f'{F} L219', 'quiet q125-q500 runs eff range vs quiet off runs eff range', '2108 to 2228 vs 1951 to 2027',
          [min(r['eff'] for r in qq), max(r['eff'] for r in qq), min(r['eff'] for r in oq), max(r['eff'] for r in oq)])
    lqv = [loaded(w, x, False) for x in lq]
    lqr = [loaded(w, x, True) for x in lq]
    claim(f'{F} L220', '6 loaded q runs: eff range; eff vs arm quiet median, % range', '1853 to 2075 MHz (-4 to -15 %)',
          [min(v['eff'] for v in lqv), max(v['eff'] for v in lqv), max(v['effp'] for v in lqv), min(v['effp'] for v in lqv)])
    v = loaded(w, '0421-off-r2', False)
    claim(f'{F} L221', '0421-off-r2: eff vs off quiet median %, eff', '-3 % (1907 MHz)', [v['effp'], v['eff']])
    claim(f'{F} L235', '6 loaded q runs: cores minus arm quiet median, range', '+0.20 to +0.38',
          [min(v['coresd'] for v in lqv), max(v['coresd'] for v in lqv)],
          alt=[min(v['coresd'] for v in lqr), max(v['coresd'] for v in lqr)])
    claim(f'{F} L236', '6 loaded q runs: cores at constant core x MHz, range', '1.81 to 2.11',
          [min(v['const'] for v in lqv), max(v['const'] for v in lqv)],
          alt=[min(v['const'] for v in lqr), max(v['const'] for v in lqr)])
    claim(f'{F} L237', '6 loaded q runs: rest, range', '+0.02 to +0.13',
          [min(v['rest'] for v in lqv), max(v['rest'] for v in lqv)],
          alt=[min(v['rest'] for v in lqr), max(v['rest'] for v in lqr)])
    v1, v2 = loaded(w, '0421-off-r2', False), loaded(w, '0440-q0-r4', False)
    r1_, r2_ = loaded(w, '0421-off-r2', True), loaded(w, '0440-q0-r4', True)
    claim(f'{F} L239', '0421-off-r2 ng_t, fps vs arm %; 0440-q0-r4 ng_t, fps vs arm %', '2.92: -0.9 %; 2.81: -0.5 %',
          [v1['ng'], v1['fpsp'], v2['ng'], v2['fpsp']], alt=[r1_['ng'], r1_['fpsp'], r2_['ng'], r2_['fpsp']])
    mid = [v for v in lqv if 2.85 <= v['ng'] < 3.45]
    midr = [v for v in lqr if 2.85 <= v['ng'] < 3.45]
    claim(f'{F} L241', 'q runs at ng_t 2.9-3.4: fps vs arm % range', '-0.7 to -2.6 %',
          [max(v['fpsp'] for v in mid), min(v['fpsp'] for v in mid)],
          alt=[max(v['fpsp'] for v in midr), min(v['fpsp'] for v in midr)])
    hi_ = [v for v in lqv if 3.65 <= v['ng'] < 4.15]
    hir = [v for v in lqr if 3.65 <= v['ng'] < 4.15]
    claim(f'{F} L242', 'q runs at ng_t 3.7-4.1: fps vs arm % range; raw median ms vs arm % range',
          '-2.8 to -6.3 % (raw median ms +5.9 to +9.0 %)',
          [max(v['fpsp'] for v in hi_), min(v['fpsp'] for v in hi_), min(v['msp'] for v in hi_), max(v['msp'] for v in hi_)],
          alt=[max(v['fpsp'] for v in hir), min(v['fpsp'] for v in hir), min(v['msp'] for v in hir), max(v['msp'] for v in hir)])
    top = sorted(rows, key=lambda r: -r['mx'])[:3]
    claim(f'{F} L249', 'three longest frames of the kept runs, ms', '37.29; 23.29; 20.63', [r['mx'] for r in top],
          note='runs: ' + ', '.join(r['run'] for r in top) + ' (posted: 0409-q250-r1, 0407-q125-r1, 0421-off-r2)')
    w5 = sorted(r['run'] for r in ALL['W5b'] if r['p'] == 2 and r['rl'] > 0 and r['scored'])[:4]
    claim(f'{F} L255', 'first four scored W5b-2 runs (04:54-05:02): ng_t range', '2.84-3.76',
          [min(NG[x] for x in w5), max(NG[x] for x in w5)], note='runs: ' + ', '.join(w5))
    claim(f'{F} L305', 'no-flagged raw p99 GM %: q125 vs q500', '-9.8 vs -6.4',
          [gm(nf, 'p99', 'q125')[0], gm(nf, 'p99', 'q500')[0]])
    n_ok = 0
    labels = ['all 40', 'no-flagged', 'no-lowclk', 'no-slow-q', 'drop-r1-both', 'no-lowclk-no-r1', 'pass 1 only', 'pass 2 only']
    for lab in labels:
        sub = subset(rows, POOLS9[lab], w)
        ch = {a: cores(sub, a)[0] for a in ('q0', 'q125', 'q250', 'q500')}
        n_ok += min(ch, key=ch.get) == 'q500'
    claim(f'{F} L311', 'q500 has the largest cores drop in k of the n subsets of the section 7 table', '8 of 8', [n_ok, len(labels)])
    d1_ = subset(rows, R1, w)
    d2_ = subset(rows, LOWCLK + R1, w)
    claim(f'{F} L313', 'quiet rounds: raw fps GM % (drop-r1-both, no-lowclk-no-r1); raw median ms GM % (same)',
          '+1.2 to +1.4 %; -5.9 to -6.2 %',
          [gm(d1_, 'fps', 'q500')[0], gm(d2_, 'fps', 'q500')[0], gm(d1_, 'med', 'q500')[0], gm(d2_, 'med', 'q500')[0]])
    claim(f'{F} L314', 'no-flagged q500 - q125 cores [CI]', '-0.071 [-0.132, -0.011]', cores(nf, 'q500', 'q125'),
          alt=oneway(nf, 'cores', arms, 'q500', 'q125', False, True)[0])
    for ln, a, b, posted in ((120, 'q500', 'q250', '-0.104 [-0.216, +0.008]'), (121, 'q500', 'q125', '-0.133 [-0.245, -0.020]'),
                             (122, 'q250', 'q125', '-0.029 [-0.141, +0.083]')):
        claim(f'{F} L{ln}', f'cores {a} - {b} [CI]', posted, cores(rows, a, b),
              alt=oneway(rows, 'cores', arms, a, b, False, True)[0])
    claim(f'{F} L259', 'no-flagged cores change q125, q250, q500 ("-0.72 each vs -0.79")', '-0.72, -0.72, -0.79',
          [cores(nf, a)[0] for a in ('q125', 'q250', 'q500')],
          alt=[oneway(nf, 'cores', arms, a, 'off', False, True)[0][0] for a in ('q125', 'q250', 'q500')])
    ex = [-cores(subset(rows, POOLS9[k], w), 'q500', 'q250')[0] for k in ('all 40', 'no-flagged', 'no-lowclk', 'no-slow-q')]
    claim(f'{F} L302', "q500's extra saving over q250, range over the 4 pools with that column (section 7)", '0.05-0.11',
          [min(ex), max(ex)])


# ---------------------------------------------------------------- W5b.md tables
SHACHK = []


def parse_w5bmd():
    fname, w = 'W5b.md', 'W5b'
    ref, arms, rows = WIN[w]['ref'], WIN[w]['arms'], KEPT[w]
    hdr = metric = None
    for i, line in enumerate(read(fname), 1):
        src = f'{fname} L{i}'
        c = cells(line)
        if c is None:
            hdr = None
            continue
        if is_sep(c):
            continue
        if hdr is None:
            hdr = c
            continue
        h0 = hdr[0]
        if h0 == 'pass' and len(hdr) > 3 and hdr[1] == 'folder':
            d = c[1].strip('`')
            SHACHK.append((src, d, c[3], SHA.get(d, 'not a checked folder')[:len(c[3])]))
        elif h0 == 'arm' and len(hdr) > 1 and hdr[1] == 'planned (+cold)':
            allr = ar(ALL[w], c[0])
            cold = [sum(1 for r in allr if r['rl'] == 0)] if '(+' in c[1] else []
            claim(src, f'W5b {c[0]}: planned (+cold), timed, kept, failed', ' '.join(c[1:5]),
                  [sum(1 for r in allr if r['rl'] > 0)] + cold +
                  [sum(1 for r in allr if r['rl'] > 0 and r['valid']), len(ar(rows, c[0])),
                   sum(1 for r in allr if r['status'] != 'OK')], cat='count')
        elif h0 == 'metric' and len(hdr) > 1 and hdr[1] == 'method':
            if c[0]:
                metric = c[0]
            if c[1] == 'raw' and metric in FIELD:
                for j, a in enumerate(hdr[2:]):
                    claim(src, f'W5b raw {metric} GM % {a} vs {ref} [CI]', c[2 + j],
                          oneway(rows, FIELD[metric], arms, a, ref, True)[0])
        elif h0 == 'metric' and len(hdr) > 1 and hdr[1] == ref and c[0] == 'cores':
            claim(src, f'W5b {ref} mean cores', c[1], [mean(ar(rows, ref), 'cores')])
            for j, a in enumerate(hdr[2:]):
                claim(src, f'W5b cores {a}: mean; change [CI]; GM % one-way', c[2 + j].replace('*', ''),
                      [mean(ar(rows, a), 'cores')] + oneway(rows, 'cores', arms, a, ref, False)[0] +
                      [oneway(rows, 'cores', arms, a, ref, True)[0][0]])
        elif h0 == 'metric' and hdr[1:] == arms[1:] and c[0] in ('raw median ms', 'raw fps', 'cores'):
            f = {'raw median ms': 'med', 'raw fps': 'fps', 'cores': 'cores'}[c[0]]
            for j, a in enumerate(hdr[1:]):
                P = paired(rows, f, a, ref)
                claim(src, f'W5b paired {c[0]} {a} vs {ref}: mean +- hw (med; higher k/n)', c[1 + j],
                      [P['mean'], P['hw'], P['med'], P['hi'], P['n']])
        elif h0 == 'arm' and len(hdr) > 1 and hdr[1].startswith('p99.9 ms median'):
            rs = ar(rows, c[0])
            top = max(rs, key=lambda r: r['mx'])
            m = re.match(r'([\d.]+)(?: \((\S+)\))?', c[4])
            note = ''
            if m.group(2):
                note = 'run agrees' if m.group(2) == top['run'] else f'longest-frame run: posted {m.group(2)}, recomputed {top["run"]}'
            claim(src, f'W5b tails {c[0]}: p99.9 median / mean, runs with a frame > 8 ms (max_ms), longest frame, frames > 33 ms',
                  f'{c[1]} {c[2]} {m.group(1)} {c[5]}',
                  [med(rs, 'p999'), mean(rs, 'p999'), sum(1 for r in rs if r['mx'] > 8), top['mx'], sum(r['o33'] for r in rs)],
                  note=note)
        elif h0.startswith('pass 2 ('):
            g = {a: ar([r for r in rows if r['p'] == 2], a) for a in arms}
            if c[0].startswith('cores'):
                vals, alt = [], []
                for rnd, out in ((False, vals), (True, alt)):
                    mm = {a: mean(g[a], 'cores', rnd) for a in arms}
                    out += [mm['d11'], mm['d11t'], mm['d11t'] - mm['d11'], mm['d11p'], mm['d11p'] - mm['d11']]
                claim(src, 'W5b pass 2 mean cores: d11; d11t (change); d11p (change)', ' '.join(c[1:4]), vals, alt=alt)
            elif c[0].startswith('fps'):
                mm = {a: med(g[a], 'fps') for a in arms}
                claim(src, 'W5b pass 2 median fps: d11; d11t (% vs d11); d11p (% vs d11)', ' '.join(c[1:4]),
                      [mm['d11'], mm['d11t'], 100 * (mm['d11t'] / mm['d11'] - 1), mm['d11p'], 100 * (mm['d11p'] / mm['d11'] - 1)])
            elif c[0].startswith('median ms'):
                claim(src, 'W5b pass 2 median of the run median ms: d11, d11t, d11p', ' '.join(c[1:4]),
                      [med(g[a], 'med') for a in arms])
            elif c[0].startswith("runner's"):
                vals = []
                for a in ('d11t', 'd11p'):
                    vals += [100 * (med(g[a], f) / med(g['d11'], f) - 1) for f in ('med', 'p99')]
                claim(src, "W5b pass 2 runner's d median %, d p99 % (medians of the run values): d11t, d11p",
                      ' '.join(c[2:4]), vals)
        elif h0 == 'arm' and hdr[1:3] == ['runs', 'median fps']:
            (b, n), (b2, _) = base(w, c[0], False), base(w, c[0], True)
            claim(src, f'W5b {c[0]} quiet runs (ng_t < 2.8): n, median fps, raw ms, cores, eff MHz', ' '.join(c[1:6]),
                  [n, b['fps'], b['med'], b['cores'], b['eff']], alt=[n, b2['fps'], b2['med'], b2['cores'], b2['eff']])
        elif h0 == 'run' and len(hdr) > 3 and hdr[2] == 'ng_t' and hdr[3].startswith('eff MHz'):
            spin = c[7] == '-'
            keys = ['ng', 'eff', 'effp', 'fps', 'fpsp', 'ms', 'msp', 'cores', 'coresd'] + ([] if spin else ['rest'])
            full, rr = loaded(w, c[0], False), loaded(w, c[0], True)
            pn = RUN[c[0]]['p']
            claim(src, f'W5b loaded {c[0]}: pass, ' + ', '.join(keys), ' '.join(c[1:7] + ([] if spin else [c[7]])),
                  [pn] + [full[k] for k in keys], alt=[pn] + [rr[k] for k in keys])
        elif h0.startswith('pool (runs left out)'):
            a = hdr[1].split()[-1]
            lab = max((k for k in POOLS5 if c[0].startswith(k)), key=len)
            sub = subset(rows, POOLS5[lab], w)
            m = re.search(r'\((\d+)\)', c[0])
            if m:
                claim(src, f'W5b {lab}: runs left out', m.group(1), [len(rows) - len(sub)], cat='count')
            claim(src, f'W5b {lab}: n {a}', c[1], [len(ar(sub, a))], cat='count')
            for col, f in ((7, 'med'), (8, 'fps')):
                claim(src, f'W5b {lab}: {a} raw {f} GM % [CI]', c[col], oneway(sub, f, arms, a, ref, True)[0])
            claim(src, f'W5b {lab}: {a} cores change [CI]', c[9], oneway(sub, 'cores', arms, a, ref, False)[0],
                  alt=oneway(sub, 'cores', arms, a, ref, False, True)[0])


# ---------------------------------------------------------------- W5b.md prose
def hand_w5b():
    F, w = 'W5b.md', 'W5b'
    rows, arms = KEPT[w], WIN[w]['arms']
    R, nan = RUN, float('nan')
    fm = lambda xs: float(np.mean(list(xs)))
    cores = lambda rs, a, b='d11', rnd=False: oneway(rs, 'cores', arms, a, b, False, rnd)[0]
    gm = lambda rs, f, a, b='d11': oneway(rs, f, arms, a, b, True)[0]
    nr1 = subset(rows, R1, w)
    g = {(p, a): [r for r in rows if r['p'] == p and r['arm'] == a] for p in (1, 2) for a in arms}

    def pr(rs, f, a, keys, rnd=False):
        P = paired(rs, f, a, 'd11', rnd)
        return [P[k] for k in keys]

    def pdiff(rs, f, a, b='d11'):
        by = {}
        for r in rs:
            by.setdefault(r['rnd'], {})[r['arm']] = r
        ds = [v[a][f] - v[b][f] for _, v in sorted(by.items()) if a in v and b in v]
        n = len(ds)
        m = float(np.mean(ds))
        h = tcrit(n - 1) * float(np.std(ds, ddof=1)) / math.sqrt(n)
        return [m, m - h, m + h, sum(1 for d in ds if d > 0), n]

    def wsp(pn, rnd):
        sub = [r for r in rows if r['p'] == pn]
        ngv = {r['run']: (round(NG[r['run']], 2) if rnd else NG[r['run']]) for r in sub}
        fpv = {r['run']: (round(r['fps'], 1) if rnd else r['fps']) for r in sub}
        cx = [ngv[r['run']] - float(np.median([ngv[s['run']] for s in sub if s['arm'] == r['arm']])) for r in sub]
        cy = [fpv[r['run']] - float(np.median([fpv[s['run']] for s in sub if s['arm'] == r['arm']])) for r in sub]
        res = stats.spearmanr(cx, cy)
        return [float(res.correlation), float(res.pvalue)]

    # verdicts table
    claim(f'{F} L42', 'cores change [CI] (GM %): d11t; d11p', '-0.22 [-0.25, -0.19] (-8.6 %), -0.20 [-0.23, -0.17] (-8.0 %)',
          cores(rows, 'd11t') + [gm(rows, 'cores', 'd11t')[0]] + cores(rows, 'd11p') + [gm(rows, 'cores', 'd11p')[0]])
    claim(f'{F} L42', 'd11t raw median ms higher than d11 in k of n rounds', '11 of 12', pr(rows, 'med', 'd11t', ['hi', 'n']))
    ld = {a: [loaded(w, r['run'], False) for r in ar(rows, a) if NG[r['run']] >= 2.8] for a in arms}
    ldr = {a: [loaded(w, r['run'], True) for r in ar(rows, a) if NG[r['run']] >= 2.8] for a in arms}
    claim(f'{F} L42', 'loaded runs (ng_t >= 2.8), mean fps vs the arm quiet median: d11t %, d11p %; n each',
          'd11t -3.0 %, d11p -1.1 % (n = 4, 4)',
          [fm(v['fpsp'] for v in ld['d11t']), fm(v['fpsp'] for v in ld['d11p']), len(ld['d11t']), len(ld['d11p'])],
          alt=[fm(v['fpsp'] for v in ldr['d11t']), fm(v['fpsp'] for v in ldr['d11p']), len(ldr['d11t']), len(ldr['d11p'])])
    mc = {a: mean(g[2, a], 'cores') for a in arms}
    mf = {a: med(g[2, a], 'fps') for a in arms}
    claim(f'{F} L43', "pass 2: d11p cores change (2 dp, 4 dp); runner's arm cores d11p, d11; d11p fps median %",
          '-0.20 core (-0.2045; runner 2.35 - 2.56), fps +0.07 %',
          [mc['d11p'] - mc['d11'], mc['d11p'] - mc['d11'], mc['d11p'], mc['d11'], 100 * (mf['d11p'] / mf['d11'] - 1)],
          note="the runner's -0.21 = 2.35 - 2.56 (its 2-dp arm values)")
    claim(f'{F} L43', 'pass 2: d11t cores change, d11t fps median %', 'd11t -0.21 core, fps -0.83 %',
          [mc['d11t'] - mc['d11'], 100 * (mf['d11t'] / mf['d11'] - 1)])
    q2 = {a: [r['fps'] for r in g[2, a] if NG[r['run']] < 2.8] for a in arms}
    claim(f'{F} L43', 'pass 2 quiet runs (ng_t < 2.8): d11t n, fps range; d11 fps range', '3 quiet runs at 384.7-385.7 fps; d11 385.0-385.4',
          [len(q2['d11t']), min(q2['d11t']), max(q2['d11t']), min(q2['d11']), max(q2['d11'])])
    w5 = sorted(r['run'] for r in ALL[w] if r['p'] == 2 and r['rl'] > 0 and r['scored'])[:4]
    claim(f'{F} L45', 'first four scored W5b-2 runs: window ng_t range', '2.84-3.76', [min(NG[x] for x in w5), max(NG[x] for x in w5)],
          note='runs: ' + ', '.join(w5))
    # section 1-2
    cold = sorted(r['run'] for r in ALL[w] if r['rl'] == 0)
    claim(f'{F} L57', 'cold runs left out (unscored)', '2', [len(cold)], cat='count', note='runs: ' + ', '.join(cold))
    nf = subset(rows, FLAG5X, w)
    claim(f'{F} L68', 'no-flagged: union size; n d11 / d11t / d11p', '7 runs, n = 11 / 8 / 10',
          [len(set(FLAG5X))] + [len(ar(nf, a)) for a in arms], cat='count')
    ldn = sorted(r['run'] for r in rows if NG[r['run']] >= 2.8 and r['run'] not in FLAG5X)
    nl = subset(rows, POOLS5['no-loaded'], w)
    claim(f'{F} L69', 'no-loaded: ng_t of 0520-d11p-r5, 0524-d11p-r6; runs left out (flagged or ng_t >= 2.8); n d11 / d11t / d11p',
          '(2.90) (2.88); 9 runs, n = 11 / 8 / 8',
          [NG['0520-d11p-r5'], NG['0524-d11p-r6'], len(set(FLAG5X) | {r['run'] for r in rows if NG[r['run']] >= 2.8})] +
          [len(ar(nl, a)) for a in arms], note='unflagged kept runs at ng_t >= 2.8: ' + ', '.join(ldn))
    claim(f'{F} L70', '0221-d11t-r5 window ng_t', '2.31', [NG['0221-d11t-r5']], note=MISREAD)
    pl = [dict(r, light=PLIGHT[w][r['run']]) for r in rows if r['run'] in PLIGHT[w]]
    full = len(pl) == len(rows)
    claim(f'{F} L81', 'light share per arm (mean of results.csv light_share): d11, d11t, d11p', '0.974 0.972 0.975',
          [mean(ar(rows, a), 'light') for a in arms], alt=[mean(ar(pl, a), 'light') for a in arms] if full else None,
          alt_label='posted run-table light shares', note=LIGHT_NOTE)
    claim(f'{F} L81', 'light share one-way F (df1, df2)', '1.18 (2, 33)', list(anova(rows, 'light', arms)),
          alt=list(anova(pl, 'light', arms)) if full else None, alt_label='posted run-table light shares', cat='aux',
          note=LIGHT_NOTE)
    three = ['0157-d11-r1', '0159-d11t-r1', '0201-d11p-r1']
    oth = [r for r in rows if r['run'] not in three]
    claim(f'{F} L84', 'fps of 0157-d11-r1, 0159-d11t-r1, 0201-d11p-r1; fps range of the other 33 kept runs',
          '415.1, 407.0, 395.9; others 367.1-393.0',
          [R[x]['fps'] for x in three] + [min(r['fps'] for r in oth), max(r['fps'] for r in oth)])
    l3, lo_ = [R[x]['light'] for x in three], [r['light'] for r in oth]
    claim(f'{F} L85', 'light share: those 3 (range) vs the other 33 kept runs (range)', '0.979-0.988 vs 0.962-0.978',
          [min(l3), max(l3), min(lo_), max(lo_)],
          alt=[min(PLIGHT[w][x] for x in three), max(PLIGHT[w][x] for x in three), min(PLIGHT[w][r['run']] for r in oth),
               max(PLIGHT[w][r['run']] for r in oth)] if full else None, alt_label='posted run-table light shares',
          note=LIGHT_NOTE)
    claim(f'{F} L86', 'round 1 raw fps % vs d11: d11t, d11p', 'd11t -1.95 %, d11p -4.63 %',
          [paired(rows, 'fps', a, 'd11')['byround'][1] for a in ('d11t', 'd11p')],
          alt=[paired(rows, 'fps', a, 'd11', True)['byround'][1] for a in ('d11t', 'd11p')])
    # section 3
    claim(f'{F} L119', 'cores d11t - d11p [CI]', '-0.016 [-0.047, +0.016]', cores(rows, 'd11t', 'd11p'),
          alt=cores(rows, 'd11t', 'd11p', True))
    claim(f'{F} L133', 'd11t without each pass r1: raw median ms higher k of n, sign p, mean %, median %; raw fps lower k of n, mean %, median %',
          '9 of 10 (sign p 0.021; mean +0.68 %, median +0.32 %); 7 of 10 (mean -0.69 %, median -0.21 %)',
          pr(nr1, 'med', 'd11t', ['hi', 'n', 'p', 'mean', 'med']) + pr(nr1, 'fps', 'd11t', ['lo', 'n', 'mean', 'med']),
          alt=pr(nr1, 'med', 'd11t', ['hi', 'n', 'p', 'mean', 'med'], True) + pr(nr1, 'fps', 'd11t', ['lo', 'n', 'mean', 'med'], True))
    claim(f'{F} L134', 'd11p without each pass r1: raw median ms higher k of n, mean %, median %; raw fps higher k of n, mean %, median %',
          '4 of 10 (mean +0.10 %, median -0.38 %); 7 of 10 (mean -0.23 %, median +0.07 %)',
          pr(nr1, 'med', 'd11p', ['hi', 'n', 'mean', 'med']) + pr(nr1, 'fps', 'd11p', ['hi', 'n', 'mean', 'med']),
          alt=pr(nr1, 'med', 'd11p', ['hi', 'n', 'mean', 'med'], True) + pr(nr1, 'fps', 'd11p', ['hi', 'n', 'mean', 'med'], True))
    badr = {R[x]['rnd'] for x in FLAG5X}
    qr = [r for r in rows if r['rnd'] not in badr]
    rset = sorted({r['rnd'] for r in qr})
    rnote = 'rounds ' + ', '.join(f'r{q}' for q in rset) + (' (as posted)' if rset == [1, 2, 4, 5, 6, 10, 11, 12] else ' (POSTED SET DIFFERS)')
    claim(f'{F} L136', 'rounds with no flagged run: d11t raw median ms higher k of n, sign p, mean %, median %',
          '7 of 8 (sign p 0.070; mean +0.48 %, median +0.30 %)', pr(qr, 'med', 'd11t', ['hi', 'n', 'p', 'mean', 'med']), note=rnote)
    claim(f'{F} L147', 'd11t p99.9 mean without 0221-d11t-r5', '5.58',
          [mean([r for r in ar(rows, 'd11t') if r['run'] != '0221-d11t-r5'], 'p999')])
    claim(f'{F} L148', 'paired p99.9 ms difference vs d11 [CI], higher k of n: d11t; d11p',
          '+0.659 ms [-0.475, +1.793], 6 of 12; +0.021 ms [-0.126, +0.168], 6 of 12',
          pdiff(rows, 'p999', 'd11t') + pdiff(rows, 'p999', 'd11p'))
    # section 4
    t2 = g[2, 'd11t']
    named = ['0455-d11t-r1', '0459-d11t-r2', '0510-d11t-r3']
    rest_ = [r['fps'] for r in t2 if r['run'] not in named]
    claim(f'{F} L163', 'pass 2 d11t: fps of 0455, 0459, 0510; the other runs: n, fps range; d11 quiet pass-2 fps range',
          '(367.1), (376.6), (379.3); other 3 at 384.7-385.7; d11 quiet 385.0-385.4',
          [R[x]['fps'] for x in named] + [len(rest_), min(rest_), max(rest_), min(q2['d11']), max(q2['d11'])])
    claim(f'{F} L164', 'd11t median fps: pass 2; pass 2 without 0455 and 0510; pass 1',
          '382.0 with them, 385.0 without; W5b first pass 384.2',
          [med(t2, 'fps'), med([r for r in t2 if r['run'] not in ('0455-d11t-r1', '0510-d11t-r3')], 'fps'), med(g[1, 'd11t'], 'fps')])
    sp = lambda rs: 100 * (max(r['med'] for r in rs) - min(r['med'] for r in rs)) / float(np.median([r['med'] for r in rs]))
    claim(f'{F} L166', 'pass 1 runner summary: median fps d11 / d11t / d11p; mean cores; median-ms spread % ((max-min)/median)',
          'fps 384.65 / 384.23 / 384.99; cores 2.54 / 2.31 / 2.34; spreads 10.1 / 10.3 / 4.4 %',
          [med(g[1, a], 'fps') for a in arms] + [mean(g[1, a], 'cores') for a in arms] + [sp(g[1, a]) for a in arms],
          alt=[med(g[1, a], 'fps') for a in arms] + [med(g[1, a], 'cores') for a in arms] + [sp(g[1, a]) for a in arms],
          alt_label='run-median cores')
    # section 5
    chs = {a: [cores(subset(rows, v, w), a)[0] for v in POOLS5.values()] for a in ('d11t', 'd11p')}
    lo12 = [paired(rows, 'cores', a, 'd11')['lo'] for a in ('d11t', 'd11p')]
    claim(f'{F} L174', 'cores lower than d11 in k of n rounds (smaller k of the 2 arms); section 6 cores change range: d11t, d11p',
          '12 of 12 rounds (both arms); d11t -0.21 to -0.23, d11p -0.19 to -0.21',
          [min(lo12), paired(rows, 'cores', 'd11t', 'd11')['n'], max(chs['d11t']), min(chs['d11t']), max(chs['d11p']), min(chs['d11p'])])
    claim(f'{F} L185', 'd11t raw median ms higher than d11: k of n rounds (sign p)', '11 of 12 rounds (sign p 0.006)',
          pr(rows, 'med', 'd11t', ['hi', 'n', 'p']))
    claim(f'{F} L186', 'd11t raw median ms higher than d11 without each pass r1: k of n (sign p)', '9 of 10 (p 0.021)',
          pr(nr1, 'med', 'd11t', ['hi', 'n', 'p']))
    claim(f'{F} L187', 'd11t raw median ms higher than d11 in the rounds with no flagged run: k of n (sign p)', '7 of 8 (p 0.070)',
          pr(qr, 'med', 'd11t', ['hi', 'n', 'p']), note=rnote)
    claim(f'{F} L189', 'd11p raw median ms higher: k of n (all), k of n (without r1), median round without r1 %',
          '5 of 12 rounds and 4 of 10 (median round -0.38 %)', pr(rows, 'med', 'd11p', ['hi', 'n']) + pr(nr1, 'med', 'd11p', ['hi', 'n', 'med']))
    claim(f'{F} L206', 'loaded runs: d11t n, mean fps vs arm %, mean ng_t; d11p n, mean fps %, mean ng_t',
          '4 runs -3.0 % at mean ng_t 3.11; 4 runs -1.1 % at 3.15',
          [len(ld['d11t']), fm(v['fpsp'] for v in ld['d11t']), fm(v['ng'] for v in ld['d11t']),
           len(ld['d11p']), fm(v['fpsp'] for v in ld['d11p']), fm(v['ng'] for v in ld['d11p'])],
          alt=[len(ldr['d11t']), fm(v['fpsp'] for v in ldr['d11t']), fm(round(v['ng'], 2) for v in ldr['d11t']),
               len(ldr['d11p']), fm(v['fpsp'] for v in ldr['d11p']), fm(round(v['ng'], 2) for v in ldr['d11p'])])
    claim(f'{F} L207', 'loaded runs, mean eff MHz vs the arm quiet median %: d11p, d11t', '-4.5 % vs -3.9 %',
          [fm(v['effp'] for v in ld['d11p']), fm(v['effp'] for v in ld['d11t'])],
          alt=[fm(v['effp'] for v in ldr['d11p']), fm(v['effp'] for v in ldr['d11t'])])
    alll, alllr = [v for a in arms for v in ld[a]], [v for a in arms for v in ldr[a]]
    nsp = lambda vs: [v for a in ('d11t', 'd11p') for v in vs[a]]
    claim(f'{F} L210', 'the 9 loaded runs: cores minus the arm quiet median, range; rest (d11t and d11p runs), range',
          '+0.01 to +0.09; -0.17 to +0.01',
          [min(v['coresd'] for v in alll), max(v['coresd'] for v in alll), min(v['rest'] for v in nsp(ld)), max(v['rest'] for v in nsp(ld))],
          alt=[min(v['coresd'] for v in alllr), max(v['coresd'] for v in alllr), min(v['rest'] for v in nsp(ldr)),
               max(v['rest'] for v in nsp(ldr))])
    claim(f'{F} L211', 'within-arm Spearman rho(ng_t, raw fps) and p (centred on pass x arm medians): pass 1; pass 2',
          '-0.67 (p 0.002); -0.32 (p 0.19)', wsp(1, False) + wsp(2, False), alt=wsp(1, True) + wsp(2, True), cat='aux')
    r0 = R['0221-d11t-r5']
    claim(f'{F} L215', '0221-d11t-r5: window ng_t, p99.9 ms, longest frame ms', 'ng_t 2.31; p99.9 11.672 ms; longest 26.37 ms',
          [NG['0221-d11t-r5'], r0['p999'], r0['mx']], note=MISREAD)
    bx = ['0213-d11t-r3', '0510-d11t-r3', '0453-d11-r1', '0221-d11t-r5']
    claim(f'{F} L224', 'audit 1 s max ng_t (win_ngB_max): 0213-d11t-r3, 0510-d11t-r3, 0453-d11-r1 vs 0221-d11t-r5',
          '8.04, 7.60, 7.49 vs 5.95', [NGMAX.get(x, nan) for x in bx])
    # section 6
    dn = {k: len(ar(subset(rows, v, w), 'd11')) for k, v in POOLS5.items()}
    exp = {'all 36': 12, 'no-slow-d11t': 12, 'no-0221': 12, 'no-flagged': 11, 'no-loaded': 11, 'no-audit-flag': 11,
           'no-p2-first3': 11, 'drop-p2-r1r2': 10, 'drop-r1-both': 10, 'pass 1 only': 6, 'pass 2 only': 6}
    badp = [k for k in exp if dn[k] != exp[k]]
    claim(f'{F} L270', 'd11 n per section 6 pool: 12; 11 (no-flagged, no-loaded, no-audit-flag, no-p2-first3); 10 (drop-round); 6 (one-pass)',
          '12 11 10 6', [dn['all 36'], dn['no-flagged'], dn['drop-r1-both'], dn['pass 1 only']] if not badp else [nan] * 4,
          cat='count', note=('pools that differ: ' + ', '.join(badp)) if badp else 'all 11 pools as stated')
    # section 7
    claim(f'{F} L285', 'cold runs: 0451-cold-d11 window ng_t, warm-up ng_t; 0155-cold-d11 window, warm-up',
          '2.55 and warm-up 1.94 (first pass cold: 2.39 / 1.93)',
          [NG.get('0451-cold-d11', nan), WU.get('0451-cold-d11', nan), NG.get('0155-cold-d11', nan), WU.get('0155-cold-d11', nan)])
    claim(f'{F} L287', 'first four scored W5b-2 runs: window ng_t; warm-up ng_t',
          '3.53 / 3.37 / 3.76 / 2.84, with warm-up ng_t 2.55 / 3.80 / 3.62 / 3.48',
          [NG[x] for x in w5] + [WU.get(x, nan) for x in w5], note='runs: ' + ', '.join(w5))

    def f3(pn):
        sc = sorted((r for r in ALL[w] if r['p'] == pn and r['rl'] > 0 and r['scored']), key=lambda r: r['run'])
        return [len(sc[:3]), len(sc[3:]), float(np.median([NG[r['run']] for r in sc[:3]])),
                float(np.median([NG[r['run']] for r in sc[3:]]))]
    v2, v1 = f3(2), f3(1)
    claim(f'{F} L288', 'first 3 scored runs vs the other 15, median ng_t: W5b-2; W5b-1', '3 vs 15: 3.53 vs 2.50; first pass 2.46 vs 2.56',
          v2 + v1[2:])
    claim(f'{F} L291', 'median ng_t of the kept runs, W5b-2 minus W5b-1: d11, d11t, d11p', 'd11 -0.03, d11t +0.09, d11p +0.16',
          [float(np.median([NG[r['run']] for r in g[2, a]])) - float(np.median([NG[r['run']] for r in g[1, a]])) for a in arms])
    bf = [base(w, a, False)[0]['fps'] for a in arms]
    claim(f'{F} L305', 'quiet runs (ng_t < 2.8): median fps, range over the 3 arms', '385.1-385.4 fps', [min(bf), max(bf)])


# ---------------------------------------------------------------- load-check.md
def parse_loadcheck():
    fname = 'load-check.md'
    w = hdr = None
    for i, line in enumerate(read(fname), 1):
        src = f'{fname} L{i}'
        if line.startswith('## '):
            w, hdr = line[3:].strip(), None
            continue
        c = cells(line)
        if c is None:
            hdr = None
            m = re.match(r'- (W9|W5b)-(\d): ng_t median ([\d.]+) \[([\d.]+)\.\.([\d.]+)\] over (\d+) kept runs; (\d+) at or '
                         r'above 2\.8; median of the rest ([\d.]+); Spearman rho\(ng_t, raw fps\) across runs ([-+]?[\d.]+) '
                         r'\(n (\d+), p [\d.]+\), within arm ([-+]?[\d.]+)', line)
            if m:
                ww, pn = m.group(1), int(m.group(2))
                sub = [r for r in KEPT[ww] if r['p'] == pn]
                vals, wvals = [], []
                for rd in (False, True):
                    ngd = {r['run']: (round(NG[r['run']], 2) if rd else NG[r['run']]) for r in sub}
                    fpd = {r['run']: (round(r['fps'], 1) if rd else r['fps']) for r in sub}
                    ng = [ngd[r['run']] for r in sub]
                    rho = float(stats.spearmanr(ng, [fpd[r['run']] for r in sub]).correlation)
                    vals.append([float(np.median(ng)), min(ng), max(ng), len(ng), sum(1 for x in ng if x >= 2.8),
                                 float(np.median([x for x in ng if x < 2.8])), rho, len(sub)])
                    cx, cy = [], []
                    for r in sub:
                        g = [s for s in sub if s['arm'] == r['arm']]
                        cx.append(ngd[r['run']] - float(np.median([ngd[s['run']] for s in g])))
                        cy.append(fpd[r['run']] - float(np.median([fpd[s['run']] for s in g])))
                    wvals.append([float(stats.spearmanr(cx, cy).correlation)])
                claim(src, f'{ww}-{pn}: ng_t median, min, max, n; count >= 2.8; median of the rest; Spearman rho(ng_t, fps), n',
                      ' '.join(m.group(k) for k in range(3, 11)), vals[0], alt=vals[1])
                claim(src, f'{ww}-{pn}: within-arm Spearman (centred on pass x arm medians)', m.group(11), wvals[0],
                      alt=wvals[1], cat='aux')
                continue
            m = re.match(r'- (full pool|no-lowclk|no-slow-q|no-flagged): (.*)$', line)
            if m and w in WIN:
                toks = {'full pool': [], 'no-lowclk': LOWCLK, 'no-slow-q': SLOWQ, 'no-flagged': FLAG9}[m.group(1)]
                sub = subset(KEPT[w], toks, w)
                for mm in re.finditer(r'(\w+) - (\w+) \(n (\d+) v (\d+)\): ([-+]?[\d.]+) \[([-+]?[\d.]+), ([-+]?[\d.]+)\] '
                                      r'(?:\* )?\(df (\d+)\)', m.group(2)):
                    a, b = mm.group(1), mm.group(2)
                    v, df, _ = oneway(sub, 'cores', WIN[w]['arms'], a, b, False)
                    vr = oneway(sub, 'cores', WIN[w]['arms'], a, b, False, True)[0]
                    nn = [len(ar(sub, a)), len(ar(sub, b))]
                    claim(src, f'{w} {m.group(1)}: cores {a} - {b}: n, n, change [CI], df',
                          ' '.join(mm.group(k) for k in range(3, 9)), nn + v + [df], alt=nn + vr + [df])
                continue
            m = re.match(r"- (\w+) vs (\w+), (raw median ms|raw fps|raw p99 ms|T-std median ms), (.*?): n (\d+), higher "
                         r"(\d+)/(\d+) \(sign p ([\d.]+)\), mean ([-+]?[\d.]+) %, median ([-+]?[\d.]+) %, per round (.*)$", line)
            if m and w in WIN:
                a, b, metric, which = m.group(1), m.group(2), m.group(3), m.group(4)
                if metric.startswith('T-std'):
                    continue
                f = {'raw median ms': 'med', 'raw fps': 'fps', 'raw p99 ms': 'p99'}[metric]
                rows = KEPT[w]
                if which == 'all rounds':
                    sub = rows
                elif which.startswith('without each pass'):
                    sub = subset(rows, R1, w)
                else:
                    fl = FLAG9 if w == 'W9' else FLAG5
                    bad = {RUN[x]['rnd'] for x in fl if RUN[x]['arm'] in (a, b)}
                    sub = [r for r in rows if r['rnd'] not in bad]
                pr = re.findall(r'r(\d+) ([-+]?[\d.]+)', m.group(11))
                posted = f'{m.group(5)} {m.group(6)}/{m.group(7)} p {m.group(8)} {m.group(9)} {m.group(10)} ' + ' '.join(x for _, x in pr)
                vals = []
                for rnd in (False, True):
                    P = paired(sub, f, a, b, rnd)
                    vals.append([P['n'], P['hi'], P['n'], P['p'], P['mean'], P['med']] +
                                [P['byround'].get(int(q), float('nan')) for q, _ in pr])
                note = '' if {int(q) for q, _ in pr} == set(paired(sub, f, a, b)['byround']) else 'ROUND SET DIFFERS'
                claim(src, f'{w} {a} vs {b}, {metric}, {which}: n, higher k/n, sign p, mean %, median %, per-round %',
                      posted, vals[0], alt=vals[1], note=note)
                continue
            m = re.match(r"Loaded runs vs d11's ng_t < 2\.8 median fps \(([\d.]+)\): (.*)$", line)
            if m:
                pairs = re.findall(r'(\d{4}-\w+-r\d+) \w+ ([-+]?[\d.]+) %', m.group(2))
                vals = []
                for rnd in (False, True):
                    b0, _ = base('W5b', 'd11', rnd)
                    vals.append([b0['fps']] + [100 * (rv(RUN[x], 'fps', rnd) / b0['fps'] - 1) for x, _ in pairs])
                claim(src, "W5b loaded runs vs d11's quiet median fps: base, then % per run",
                      m.group(1) + ' ' + ' '.join(x for _, x in pairs), vals[0], alt=vals[1])
                continue
            m = re.match(r'- check: t_crit\(35\) = ([\d.]+), t_crit\(7\) = ([\d.]+), t_crit\(11\) = ([\d.]+)', line)
            if m:
                claim(src, 't critical values (35, 7, 11)', ' '.join(m.groups()), [tcrit(35), tcrit(7), tcrit(11)], cat='aux')
            continue
        if is_sep(c):
            continue
        if hdr is None:
            hdr = c
            continue
        if hdr[0] == 'arm' and hdr[1].startswith('runs with ng_t'):
            (b, n), (b2, _) = base(w, c[0], False), base(w, c[0], True)
            claim(src, f'{w} {c[0]} quiet runs (ng_t < 2.8): n, median fps, raw ms, cores, eff MHz',
                  ' '.join([c[1], c[2], c[3], c[5], c[6]]), [n, b['fps'], b['med'], b['cores'], b['eff']],
                  alt=[n, b2['fps'], b2['med'], b2['cores'], b2['eff']])
        elif hdr[0] == 'run' and len(hdr) > 3 and hdr[3].startswith('eff MHz'):
            spin = c[8].startswith('-')
            keys = ['ng', 'eff', 'effp', 'fps', 'fpsp', 'ms', 'msp', 'cores', 'coresd'] + ([] if spin else ['const', 'rest'])
            full, rr = loaded(w, c[0], False), loaded(w, c[0], True)
            claim(src, f'{w} loaded {c[0]}: ' + ', '.join(keys), ' '.join([c[2], c[3], c[4], c[5], c[7]] + ([] if spin else [c[8], c[9]])),
                  [full[k] for k in keys], alt=[rr[k] for k in keys])


# ---------------------------------------------------------------- headline tables
def headline(w):
    cfg = WIN[w]
    ref, rows = cfg['ref'], KEPT[w]
    fl = FLAG9 if w == 'W9' else FLAG5
    out = [f'| subset | arm | n | median ms (median of runs) | fps median | fps mean | cores mean | cores vs {ref} [95 % CI] | raw median ms GM % vs {ref} [CI] | raw fps GM % vs {ref} [CI] |',
           '|---|---|---|---|---|---|---|---|---|---|']
    for lab, toks in (('all', []), ('pass 1', ['p2']), ('pass 2', ['p1']), ('no round 1', R1), ('no flagged', fl),
                      ('no r1, no flagged', R1 + fl)):
        sub = subset(rows, toks, w)
        for a in cfg['arms']:
            rs = ar(sub, a)
            if a == ref:
                tail = '- | - | -'
            else:
                c_ = oneway(sub, 'cores', cfg['arms'], a, ref, False)[0]
                m_ = oneway(sub, 'med', cfg['arms'], a, ref, True)[0]
                f_ = oneway(sub, 'fps', cfg['arms'], a, ref, True)[0]
                tail = (f'{c_[0]:+.3f} [{c_[1]:+.3f}, {c_[2]:+.3f}] | {m_[0]:+.1f} [{m_[1]:+.1f}, {m_[2]:+.1f}] | '
                        f'{f_[0]:+.1f} [{f_[1]:+.1f}, {f_[2]:+.1f}]')
            out.append(f'| {lab} | {a} | {len(rs)} | {med(rs, "med"):.3f} | {med(rs, "fps"):.1f} | {mean(rs, "fps"):.1f} | '
                       f'{mean(rs, "cores"):.3f} | {tail} |')
    return out


def textcheck(cls, fname='W9.md'):
    """Hand-coded claims: are the posted numbers still on the cited line (or the next 2) of the current file?
    Single-digit integers (counts are often written as words) are not required. Returns the miss count."""
    lines = [t.replace('\u2212', '-') for t in read(fname)]
    toks = lambda text: {t.lstrip('+-') for t in NUM.findall(text)}
    win = lambda i: toks(' '.join(lines[i - 1:i + 2]))
    bad = 0
    for c in cls:
        ln = int(c['src'].split(' L')[1])
        need = {t for t in toks(c['posted']) if not re.fullmatch(r'\d', t)}
        if ln <= len(lines) and need <= win(ln):
            continue
        hit = [i for i in range(1, len(lines) + 1) if need <= win(i)]
        c['note'] = (c['note'] + '; ' if c['note'] else '') + (f'TEXT MOVED: found at L{hit[0]}' if hit else f'TEXT NOT FOUND in {fname}')
        bad += 1
    return bad


def main():
    for w in WIN:
        cnt = {a: len(ar(KEPT[w], a)) for a in WIN[w]['arms']}
        print(w, 'kept', len(KEPT[w]), cnt)
    parse_pool('pool-W9.md', 'W9')
    parse_pool('pool-W5b.md', 'W5b')
    parse_w9md()
    k0 = len(CL)
    hand_w9()
    moved = textcheck(CL[k0:])
    parse_w5bmd()
    k1 = len(CL)
    hand_w5b()
    moved5 = textcheck(CL[k1:], 'W5b.md')
    parse_loadcheck()
    files = ['W9.md', 'W5b.md', 'pool-W9.md', 'pool-W5b.md', 'load-check.md']
    cats = ['main', 'count', 'run', 'aux']
    summ = {}
    for c in CL:
        fn = c['src'].split(' L')[0]
        key = (fn, c['cat'])
        s = summ.setdefault(key, dict(claims=0, nums=0, agree=0, rounded=0, other=0, dis=0, parse=0))
        s['claims'] += 1
        s['nums'] += c['n']
        if c['verdict'] == 'agree':
            s['agree'] += 1
        elif c['verdict'] == 'agree (rounded inputs)':
            s['rounded'] += 1
        elif c['verdict'].startswith('agree'):
            s['other'] += 1
        elif c['verdict'] == 'DISAGREE':
            s['dis'] += 1
        else:
            s['parse'] += 1
    tot = {k: sum(s[k] for s in summ.values()) for k in ('claims', 'nums', 'agree', 'rounded', 'other', 'dis', 'parse')}
    isdis = lambda c: c['verdict'] == 'DISAGREE' or c['verdict'].startswith('PARSE')
    main_dis = [c for c in CL if isdis(c) and c['cat'] != 'aux']
    aux_dis = [c for c in CL if isdis(c) and c['cat'] == 'aux']
    dd = [c for c in CL if c['verdict'] == 'DISAGREE']
    bins = [('0.5-0.6', 0.5, 0.6), ('0.6-1', 0.6, 1.0), ('1-2', 1.0, 2.0), ('> 2', 2.0, float('inf'))]
    dist = {lab: sum(1 for c in dd if c['units'] is not None and lo < c['units'] <= hi) for lab, lo, hi in bins}
    nflip = sum(c['flips'] or 0 for c in dd)
    big = [c for c in dd if (c['units'] or 0) > 2 or (c['flips'] or 0) > 0]

    def cause(c):
        if c['note'].startswith('MISREAD'):
            return 'misread'
        if 'light share' in c['what']:
            return 'light'
        if c['units'] is not None and c['units'] <= 1.0 + 1e-9 and not c['flips']:
            return 'rounding'
        return 'other'
    causes = {k: [c for c in dd if cause(c) == k] for k in ('rounding', 'light', 'misread', 'other')}
    cause_txt = (f'Disagreements by cause: rounding boundary (gap <= 1 unit, no flip; Agent 7 works from unrounded per-run '
                 f'inputs, results.csv has 3 dp): {len(causes["rounding"])}; light-share definition (per-run share +-0.001 '
                 f'and the one-way F built on it): {len(causes["light"])}; misread source column: {len(causes["misread"])}'
                 + (' (' + ', '.join(c['src'] for c in causes['misread']) + ')' if causes['misread'] else '')
                 + f'; other: {len(causes["other"])}'
                 + (' (' + ', '.join(c['src'] for c in causes['other']) + ')' if causes['other'] else '') + '.')
    fu = lambda c: '-' if c['units'] is None else f'{c["units"]:.2f}'
    ff = lambda c: '-' if c['flips'] is None else str(c['flips'])
    mt = {f: os.path.getmtime(os.path.join(A7, f)) for f in files}
    import time
    L = ['# Check of Agent 7\'s W9 / W5b numbers against results.csv', '',
         'Agent 8, task #20. Script: `build/agent8/readout/w-followup/a7check/check_a7_w9w5b.py` (run from the workspace root; '
         'it reads only results.csv and, for ng_t, `audit/runs.csv`; it shares no code with either pool_readout.py).', '',
         '## Inputs', '']
    for w, cfg in WIN.items():
        for p, (d, _) in enumerate(cfg['passes'], 1):
            L.append(f'- {w} pass {p}: `{d}/results.csv` sha256 {SHA[d]}...')
    L += ['- Checked files (Agent 7, read-only): ' + ', '.join(f'`{A7}/{f}` ({time.strftime("%H:%M", time.localtime(mt[f]))})' for f in files) + '.',
          '- Kept runs: scored, status OK, valid_timing, not excluded; cold runs out. '
          f'W9 {len(KEPT["W9"])} (8 per arm), W5b {len(KEPT["W5b"])} (12 per arm).',
          '- ng_t = `win_ngB_mean` (non-game busy cores, window mean) from `build/agent8/readout/w-followup/audit/runs.csv`.',
          '- Agree = every recomputed number rounds to the posted number at the posted decimals (ties count as agree). '
          '"agree (rounded inputs)" = it matches only when the inputs are first rounded the way the pool run tables print them '
          '(fps 1 dp, cores 2 dp, p99 2 dp, MHz 0 dp, ng_t 2 dp); load-check.md and parts of W9.md work from those tables '
          '(the W9.md pass-2 cores % also uses the printed q500 mean).',
          '- Gap = the largest |recomputed - posted| in a claim, in last-digit units of the posted number (0.5 = a rounding tie), '
          'taking the closer of the plain recompute and, where given, the rounded-input one. Sign flip = recomputed and posted '
          'on opposite sides of 0, with the posted number at least one unit from 0.',
          '- Not checkable from results.csv, so not checked: T-std, B-block T-std, T-light / T-heavy, 1 % low, thread busy %, '
          'sys.json util and P/E MHz, round-effect F tests, guard (b), the thread-cycle table, frame counts over 8 / 10 / 16.7 ms '
          '(results.csv has only the longest frame and the > 33 ms count), the quiet-gate process loads. '
          'Raw, CPU, count and run-level numbers are all checked; ng_t, its 1 s max and the warm-up ng_t come from the audit runs.csv.',
          '- Categories: main = deltas, CIs and per-arm values; count = run counts; run = the per-run tables (section 8); '
          'aux = method details (band %, CV %, 4 vs 4 band, df, within-arm Spearman, t critical values) plus the per-run '
          'light share and its one-way F (' + LIGHT_NOTE + ', so a run can differ by 0.001 and F moves; the per-arm light '
          'means are main claims).', '',
          '## Result', '',
          f'**{tot["claims"]} claims, {tot["nums"]} numbers: {tot["agree"] + tot["rounded"] + tot["other"]} agree '
          f'({tot["rounded"]} only with rounded inputs, {tot["other"]} with the stated alternative), {tot["dis"]} disagree, {tot["parse"]} parse problems.**', '',
          'Disagreements by gap (last-digit units): ' + '; '.join(f'{k}: {v}' for k, v in dist.items()) +
          f'. Sign flips: {nflip}. Hand-coded prose claims whose numbers are not on the cited line (or the next 2) of the current '
          f'file: W9.md {moved}, W5b.md {moved5}.', '', cause_txt, '',
          '| file | category | claims | numbers | agree | agree (rounded inputs) | agree (alternative) | disagree | parse |',
          '|---|---|---|---|---|---|---|---|---|']
    ix = next(i for i, s in enumerate(L) if s.startswith('- Checked files')) + 1
    L[ix:ix] = [f'- {src} cites `{d}/results.csv` sha256 prefix {posted}: ' +
                ('matches.' if actual == posted else f'DIFFERS (file: {actual}).') for src, d, posted, actual in SHACHK]
    for f in files:
        for c in cats:
            s = summ.get((f, c))
            if s:
                L.append(f'| {f} | {c} | {s["claims"]} | {s["nums"]} | {s["agree"]} | {s["rounded"]} | {s["other"]} | {s["dis"]} | {s["parse"]} |')
    L += ['']
    if main_dis:
        L += ['Claims that do not agree (main, count, run):', '',
              '| source | claim | posted | recomputed | verdict | gap (units) | sign flips | note |', '|---|---|---|---|---|---|---|---|']
        L += [f'| {c["src"]} | {c["what"]} | {c["posted"]} | {c["rec"]} | {c["verdict"]} | {fu(c)} | {ff(c)} | {c["note"]} |' for c in main_dis]
        L += ['']
    else:
        L += ['Every main, count and run claim agrees.', '']
    if aux_dis:
        L += ['Aux (method-detail) claims that do not agree:', '',
              '| source | claim | posted | recomputed | verdict | gap (units) | sign flips | note |', '|---|---|---|---|---|---|---|---|']
        L += [f'| {c["src"]} | {c["what"]} | {c["posted"]} | {c["rec"]} | {c["verdict"]} | {fu(c)} | {ff(c)} | {c["note"]} |' for c in aux_dis]
        L += ['']
    alts = [c for c in CL if c['verdict'].startswith('agree (') and c['verdict'] != 'agree (rounded inputs)']
    if alts:
        L += ['Claims that agree only with a stated alternative reading:', '']
        L += [f'- {c["src"]}: {c["what"]}: posted {c["posted"]}; recomputed {c["rec"]} ({c["verdict"]})' for c in alts]
        L += ['']
    for w in WIN:
        L += [f'## {w} per-arm headline numbers (recomputed from results.csv)', '',
              f'Deltas: cores = linear one-way pooled CI; median ms and fps = GM % with the pooled one-way CI on ln (df = runs - arms), '
              f'the same as the pool files\' raw rows.', '']
        L += headline(w)
        L += ['']
    L += ['## All claims', '', '| # | source | claim | posted | recomputed | verdict | gap (units) | note |', '|---|---|---|---|---|---|---|---|']
    L += [f'| {k} | {c["src"]} | {c["what"]} | {c["posted"]} | {c["rec"]} | {c["verdict"]} | {fu(c)} | {c["note"]} |' for k, c in enumerate(CL, 1)]
    with open(OUT_MD, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    print('claims', tot)
    print('gap', dist, 'flips', nflip, 'hand-claim text misses W9.md', moved, 'W5b.md', moved5)
    print(cause_txt)
    for s in SHACHK:
        print('SHA:', s[0], s[1], 'posted', s[2], 'file', s[3], 'OK' if s[2] == s[3] else 'DIFFERS')
    for c in main_dis + aux_dis:
        print('NOT AGREE:', c['src'], '|', c['what'], '| posted', c['posted'], '| rec', c['rec'], '|', c['verdict'], '| gap', fu(c),
              '| flips', ff(c), '|', c['note'])
    for c in big:
        print('LARGE GAP OR FLIP:', c['src'], '|', c['what'], '| gap', fu(c), '| flips', ff(c))
    for c in CL:
        if 'TEXT' in c['note']:
            print('TEXT CHECK:', c['src'], '|', c['posted'], '|', c['note'])
    print('wrote', OUT_MD)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Checker 2 (check-bct) for Agent 7 task #6: independent recompute of noise_methods.py's raw summary (item 1), B paired
and B-norm (2), C trimmed (3), D ANCOVAs + cov_info (4) and noise_case's flagged-run residuals (5), compared against
report.json / report-w5.json and noise-case-w4b.md / noise-case-w5.md. Does not import noise_methods.py, noise_case.py
or w4b_readout.py. Stdlib only, one thread. Writes only check-bct/check-out.txt and check-bct/mine-<window>.json.
Usage: python -B check_bct.py
"""
import csv
import json
import math
import os
import statistics
import sys

sys.dont_write_bytecode = True

REPO = r'<workspace>'
NOISE = os.path.join(REPO, 'build', 'agent7', 'w4b-noise')
OUTD = os.path.join(NOISE, 'check-bct')
WINDOWS = (('W4b', os.path.join(REPO, 'build', 'agent8', 'matrix', '20261122-1541'), 'report.json', 'noise-case-w4b.md'),
           ('W5', os.path.join(REPO, 'build', 'agent8', 'matrix', '20261122-1756'), 'report-w5.json', 'noise-case-w5.md'))
TQ = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201,
      12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131}
KEYS = ('fps', 'p50_ms', 'p99_ms', 'low1_fps')
SIGN = {'fps': 1, 'low1_fps': 1, 'p50_ms': -1, 'p99_ms': -1}
CPUS = 12
REL_TOL, PP_TOL = 1e-4, 0.01


def fnum(s):
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def truthy(s):
    return (s or '').strip().lower() == 'true'


def jload(path):
    with open(path, encoding='utf-8-sig') as fh:
        return json.load(fh)


# ---------------------------------------------------------------- frames and per-run numbers
def load_frame_column(path, source, column, scale, stop):
    """Good rows of a frames csv (header field count; perf: all fields int; else float column); the text after the
    last newline (empty or a truncated line) is dropped. Returns the column values of the first `stop` good rows."""
    with open(path, 'rb') as fh:
        data = fh.read()
    lines = data.split(b'\n')[:-1]
    if not lines:
        return []
    header = [h.strip() for h in lines[0].decode('ascii', 'replace').rstrip('\r').split(',')]
    ci, width = header.index(column), len(header)
    out = []
    for ln in lines[1:]:
        if len(out) >= stop:
            break
        parts = ln.rstrip(b'\r').split(b',')
        if len(parts) != width:
            continue
        try:
            if source == 'perf':
                iv = [int(p) for p in parts]
                v = iv[ci] if scale == 1.0 else iv[ci] * scale
            else:
                v = float(parts[ci]) * scale
        except ValueError:
            continue
        out.append(v)
    return out


def rank(s, num_, den):
    n = len(s)
    k = -(-num_ * n // den)  # ceil(num/den * n), exact
    return s[min(max(k, 1), n) - 1]


def raw_stats(ft):
    v = [x for x in ft if x > 0]
    n = len(v)
    if not n:
        return None
    s = sorted(v)
    k = max(1, n // 100)
    return {'n': n, 'fps': n * 1e6 / float(sum(v)), 'p50_ms': rank(s, 1, 2) / 1000.0,
            'p99_ms': rank(s, 99, 100) / 1000.0, 'low1_fps': 1000.0 / (sum(s[-k:]) / float(k) / 1000.0)}


def trim20(v):
    s = sorted(v)
    n = len(s)
    k = n // 5  # floor(0.2 n)
    core = s[k:n - k] if n - 2 * k > 0 else s
    return sum(core) / float(len(core))


def bins10(ft):
    """Frames grouped by the 10 s bin of summed frame time in which they end (ending on a boundary closes the
    earlier bin); a last part < 5 s merged into the bin before; empty bins dropped (they have no stats)."""
    lim = 10_000_000.0
    groups, cum = [], 0.0
    for x in ft:
        cum += x
        b = max(0, math.ceil(cum / lim) - 1)
        while len(groups) <= b:
            groups.append([])
        groups[b].append(x)
    if len(groups) >= 2 and cum / 1e6 - 10.0 * (len(groups) - 1) < 5.0:
        tail = groups.pop()
        groups[-1].extend(tail)
    return [raw_stats(g) for g in groups if g]


def load_window(d):
    with open(os.path.join(d, 'results.csv'), encoding='utf-8-sig', newline='') as fh:
        rows = list(csv.DictReader(fh))
    mj = jload(os.path.join(d, 'matrix.json'))
    present = []
    for r in rows:
        if r['arm'] not in present:
            present.append(r['arm'])
    ids = [a['id'] for a in mj.get('arms') or [] if isinstance(a, dict) and a.get('id')]
    order = [i for i in ids if i in present] + [p for p in present if p not in ids]
    ref = next((a['id'] for a in mj.get('arms') or [] if isinstance(a, dict) and a.get('ref') and a.get('id') in present),
               None) or (mj.get('reference') if mj.get('reference') in present else order[0])
    runs = []
    for r in rows:
        rd = (r.get('run_dir') or '').strip()
        name = os.path.basename(rd.rstrip('\\/'))
        if not os.path.isdir(rd):
            rd = os.path.join(d, 'runs', name)
        x = {'name': name, 'arm': r['arm'], 'round': r['round'], 'seq': r['seq'], 'csv': r}
        fj = jload(os.path.join(rd, 'frames.json'))
        win = fj['window']
        first, nrows = int(win['first_row']), int(win['rows'])
        fpath = os.path.join(rd, os.path.basename(fj['file']))
        if not os.path.isfile(fpath):
            fpath = fj['file']
        col = load_frame_column(fpath, fj.get('source'), fj['column'], fnum(fj.get('scale_to_us')) or 1.0, first + nrows)
        ft = [v for v in col[first:first + nrows] if v > 0]
        x['raw'] = raw_stats(ft)
        x['keep'] = (truthy(r.get('scored')) and truthy(r.get('valid_timing')) and not truthy(r.get('excluded'))
                     and x['raw'] is not None)
        lms = fnum(fj.get('light_ms')) or 4.5
        x['ls_T'] = sum(1 for v in ft if v < lms * 1000.0) / float(len(ft))
        x['c_frames'] = {'fps': 1e6 / trim20(ft)}
        bs = bins10(ft)
        x['bins_n'] = len(bs)
        x['c_bins'] = {k: trim20([b[k] for b in bs]) for k in ('fps', 'p99_ms', 'low1_fps')} if len(bs) >= 3 else None
        sw = jload(os.path.join(rd, 'sys.json'))['window']
        cu, cores = fnum(sw.get('cpu_util_mean')), fnum(r.get('cpu_cores_mean'))
        x['cov'] = {'ls_T': x['ls_T'], 'e_mhz': fnum(sw.get('e_eff_mhz_mean')), 'p_util': fnum(sw.get('p_util_mean')),
                    'e_util': fnum(sw.get('e_util_mean')), 'cpu_util': cu, 'cores': cores,
                    'nongame': cu / 100.0 * CPUS - cores if cu is not None and cores is not None else None}
        runs.append(x)
    return runs, order, ref


# ---------------------------------------------------------------- summaries
def lmean(vs):
    return sum(math.log(v) for v in vs) / len(vs)


def summ(vals, ref, order):
    """vals {arm: [(run, v)]}: ref band, pooled SD of ln v (arms with >= 2 runs), per-arm median / GM delta / CI."""
    rv = [v for _, v in vals[ref]]
    rmed = statistics.median(rv)
    ss, df = 0.0, 0
    for lst in vals.values():
        if len(lst) >= 2:
            m = lmean([v for _, v in lst])
            ss += sum((math.log(v) - m) ** 2 for _, v in lst)
            df += len(lst) - 1
    sd = math.sqrt(ss / df)
    t = TQ[df]
    lr = lmean(rv)
    arms = {}
    for arm in order:
        if arm not in vals:
            continue
        av = [v for _, v in vals[arm]]
        e = {'n': len(av), 'runs': [nm for nm, _ in vals[arm]], 'vals': av, 'med': statistics.median(av)}
        if arm != ref:
            e['delta_pct'] = 100.0 * (e['med'] - rmed) / rmed
            dl = lmean(av) - lr
            e['gm_delta_pct'] = 100.0 * (math.exp(dl) - 1.0)
            hw = t * sd * math.sqrt(1.0 / len(av) + 1.0 / len(rv))
            e['ci_pct'] = [100.0 * (math.exp(dl - hw) - 1.0), 100.0 * (math.exp(dl + hw) - 1.0)]
        arms[arm] = e
    return {'ref_vals': rv, 'band_pct': 100.0 * (max(rv) - min(rv)) / rmed, 'sd_ln': sd, 'cv_pct': 100.0 * sd,
            'df': df, 'hw44_pct': 100.0 * (math.exp(t * sd * math.sqrt(0.5)) - 1.0), 'arms': arms}


def inv(S):
    if len(S) == 1:
        return [[1.0 / S[0][0]]]
    a, b, c, d = S[0][0], S[0][1], S[1][0], S[1][1]
    det = a * d - b * c
    return [[d / det, -b / det], [-c / det, a / det]]


def ancova(vals, covf, ref, order):
    keep = {}
    for arm, lst in vals.items():
        for nm, v in lst:
            c = covf(nm)
            if c is None or any(u is None for u in c):
                continue
            keep.setdefault(arm, []).append((nm, v, [float(u) for u in c]))
    k = len(next(iter(keep.values()))[0][2])
    N, G = sum(len(l) for l in keep.values()), len(keep)
    df = N - G - k
    mx, my = {}, {}
    Sxx, Sxy = [[0.0] * k for _ in range(k)], [0.0] * k
    for arm, lst in keep.items():
        mx[arm] = [sum(c[i] for _, _, c in lst) / len(lst) for i in range(k)]
        my[arm] = lmean([v for _, v, _ in lst])
        for _, v, c in lst:
            dx = [c[i] - mx[arm][i] for i in range(k)]
            dy = math.log(v) - my[arm]
            for i in range(k):
                Sxy[i] += dx[i] * dy
                for j in range(k):
                    Sxx[i][j] += dx[i] * dx[j]
    Si = inv(Sxx)
    b = [sum(Si[i][j] * Sxy[j] for j in range(k)) for i in range(k)]
    gx = [sum(c[i] for l in keep.values() for _, _, c in l) / N for i in range(k)]
    adj = {arm: [(nm, math.exp(math.log(v) - sum((c[i] - gx[i]) * b[i] for i in range(k)))) for nm, v, c in lst]
           for arm, lst in keep.items()}
    rss = 0.0
    for arm, lst in keep.items():
        for _, v, c in lst:
            r = math.log(v) - my[arm] - sum((c[i] - mx[arm][i]) * b[i] for i in range(k))
            rss += r * r
    sd = math.sqrt(rss / df)
    t = TQ[df]
    s = summ(adj, ref, order)
    lr = lmean([v for _, v in adj[ref]])
    for arm, e in s['arms'].items():
        if arm == ref:
            continue
        d = [mx[arm][i] - mx[ref][i] for i in range(k)]
        q = sum(d[i] * Si[i][j] * d[j] for i in range(k) for j in range(k))
        dl = lmean(e['vals']) - lr
        hw = t * sd * math.sqrt(1.0 / e['n'] + 1.0 / len(adj[ref]) + q)
        e['ci_pct'] = [100.0 * (math.exp(dl - hw) - 1.0), 100.0 * (math.exp(dl + hw) - 1.0)]
    s.update(sd_ln=sd, cv_pct=100.0 * sd, df=df, hw44_pct=100.0 * (math.exp(t * sd * math.sqrt(0.5)) - 1.0), b=b)
    return s


def paired(kept, getv, ref, order):
    byr = {}
    for x in kept:
        v = getv(x)
        if v is not None:
            byr.setdefault(x['round'], {})[x['arm']] = v
    out = {}
    for arm in order:
        if arm == ref:
            continue
        rr = [(rnd, r[arm], r[ref]) for rnd, r in sorted(byr.items(), key=lambda kv: float(kv[0]))
              if arm in r and ref in r]
        if not rr:
            continue
        ds = [100.0 * (a - b) / b for _, a, b in rr]
        n = len(ds)
        mean = sum(ds) / n
        sd = math.sqrt(sum((q - mean) ** 2 for q in ds) / (n - 1)) if n >= 2 else None
        out[arm] = {'rounds': [r for r, _, _ in rr], 'deltas': ds, 'med': statistics.median(ds),
                    'range': max(ds) - min(ds), 'mean': mean,
                    'hw95': TQ[n - 1] * sd / math.sqrt(n) if sd is not None else None, 'up': sum(1 for q in ds if q > 0)}
    return out


def bnorm(kept, getv):
    byr = {}
    for x in kept:
        v = getv(x)
        if v is not None and v > 0:
            byr.setdefault(x['round'], []).append((x['name'], v))
    out = {}
    for lst in byr.values():
        g = math.exp(lmean([v for _, v in lst]))
        for nm, v in lst:
            out[nm] = v / g
    return out


def anova(groups, order):
    allv = [v for l in groups.values() for v in l]
    m = sum(allv) / len(allv)
    gm = {a: sum(l) / len(l) for a, l in groups.items()}
    ssb = sum(len(l) * (gm[a] - m) ** 2 for a, l in groups.items())
    ssw = sum((v - gm[a]) ** 2 for a, l in groups.items() for v in l)
    dfb, dfw = len(groups) - 1, len(allv) - len(groups)
    return {'means': {a: gm[a] for a in order if a in gm}, 'F': (ssb / dfb) / (ssw / dfw), 'df': [dfb, dfw]}


def collect(kept, getv):
    out = {}
    for x in kept:
        v = getv(x)
        if v is not None and v > 0:
            out.setdefault(x['arm'], []).append((x['name'], v))
    return out


def loo(vals, sign):
    out = {}
    for lst in vals.values():
        if len(lst) < 2:
            continue
        lg = [math.log(v) for _, v in lst]
        for i, (nm, _) in enumerate(lst):
            d = lg[i] - sum(u for j, u in enumerate(lg) if j != i) / (len(lg) - 1)
            out[nm] = 100.0 * (math.exp(-d if sign > 0 else d) - 1.0)
    return out


# ---------------------------------------------------------------- comparison
class Cmp:
    def __init__(self):
        self.mm, self.maxrel, self.maxpp, self.count = [], {}, {}, {}

    def c(self, item, label, mine, theirs, kind='rel', nd=None):
        self.count[item] = self.count.get(item, 0) + 1
        if mine is None or theirs is None:
            if not (mine is None and theirs is None):
                self.mm.append((item, label, theirs, mine))
            return
        if kind == 'exact':
            if mine != theirs:
                self.mm.append((item, label, theirs, mine))
            return
        if kind == 'rel':
            d = abs(mine - theirs) / abs(theirs) if theirs != 0 else abs(mine)
            self.maxrel[item] = max(self.maxrel.get(item, 0.0), d)
            if d > REL_TOL:
                self.mm.append((item, label, theirs, mine))
        elif kind == 'pp':
            d = abs(mine - theirs)
            self.maxpp[item] = max(self.maxpp.get(item, 0.0), d)
            if d > PP_TOL:
                self.mm.append((item, label, theirs, mine))
        elif kind == 'printed':  # theirs printed with nd decimals: mine must round to it
            d = abs(mine - theirs)
            key = item + ' (printed, %d dp)' % nd
            self.maxpp[key] = max(self.maxpp.get(key, 0.0), d)
            if d > 0.5 * 10 ** (-nd) + 1e-9:
                self.mm.append((item, label + ' [printed %d dp]' % nd, theirs, mine))


def cmp_summary(C, item, tag, mine, th, ancova_b=False):
    C.c(item, tag + ' band_pct', mine['band_pct'], th.get('band_pct'), 'pp')
    C.c(item, tag + ' sd_ln', mine['sd_ln'], th.get('sd_ln'))
    C.c(item, tag + ' cv_pct', mine['cv_pct'], th.get('cv_pct'), 'pp')
    C.c(item, tag + ' df', mine['df'], th.get('df'), 'exact')
    C.c(item, tag + ' hw44_pct', mine['hw44_pct'], th.get('hw44_pct'), 'pp')
    rv, trv = mine['ref_vals'], th.get('ref_vals') or []
    C.c(item, tag + ' ref_vals count', len(rv), len(trv), 'exact')
    for i, (a, b) in enumerate(zip(rv, trv)):
        C.c(item, tag + ' ref_vals[%d]' % i, a, b)
    if ancova_b:
        for i, (a, b) in enumerate(zip(mine['b'], th.get('b') or [])):
            C.c(item, tag + ' b[%d]' % i, a, b)
    tarms = th.get('arms') or {}
    C.c(item, tag + ' arms', sorted(mine['arms']), sorted(tarms), 'exact')
    for arm, e in mine['arms'].items():
        t = tarms.get(arm) or {}
        C.c(item, tag + ' %s n' % arm, e['n'], t.get('n'), 'exact')
        C.c(item, tag + ' %s runs' % arm, e['runs'], t.get('runs'), 'exact')
        for i, (a, b) in enumerate(zip(e['vals'], t.get('vals') or [])):
            C.c(item, tag + ' %s %s' % (arm, e['runs'][i]), a, b)
        C.c(item, tag + ' %s med' % arm, e['med'], t.get('med'))
        if 'delta_pct' in e:
            C.c(item, tag + ' %s delta_pct' % arm, e['delta_pct'], t.get('delta_pct'), 'pp')
            C.c(item, tag + ' %s gm_delta_pct' % arm, e['gm_delta_pct'], t.get('gm_delta_pct'), 'pp')
            tci = t.get('ci_pct') or [None, None]
            C.c(item, tag + ' %s ci lo' % arm, e['ci_pct'][0], tci[0], 'pp')
            C.c(item, tag + ' %s ci hi' % arm, e['ci_pct'][1], tci[1], 'pp')


def find_method(R, mid, key):
    return next((m for m in R['methods'] if m.get('method') == mid and m.get('key') == key), None)


def parse_md_tables(path):
    secs, cur = {}, None
    with open(path, encoding='utf-8') as fh:
        for ln in fh.read().splitlines():
            if ln.startswith('## '):
                cur = ln[3:].strip()
                secs[cur] = []
            elif cur and ln.startswith('|') and not ln.startswith('|---'):
                secs[cur].append([c.strip() for c in ln.strip().strip('|').split('|')])
    return secs


def pnum(s):
    if s in ('-', '', None):
        return None
    return fnum(s.replace('+', ''))


def main():
    C = Cmp()
    log = []
    w = log.append
    for wname, d, rjson, casemd in WINDOWS:
        R = jload(os.path.join(NOISE, rjson))
        runs, order, ref = load_window(d)
        kept = [x for x in runs if x['keep']]
        byname = {x['name']: x for x in runs}
        trun = {x['name']: x for x in R['runs']}
        w('== %s: dir %s, ref %s, order %s, kept %d of %d; left out: %s' % (
            wname, d, ref, ','.join(order), len(kept), len(runs), ', '.join(x['name'] for x in runs if not x['keep'])))
        C.c(wname + '-1', 'ref arm', ref, R.get('ref'), 'exact')
        C.c(wname + '-1', 'order', order, R.get('order'), 'exact')
        C.c(wname + '-4', 'params cpus', CPUS, (R.get('params') or {}).get('cpus'), 'exact')
        mine_out = {'ref': ref, 'order': order, 'runs': {}, 'methods': {}, 'paired': {}, 'cov_info': {}, 'case': {}}
        # ---- item 1: per-run raw vs JSON and results.csv
        it = wname + '-1'
        for x in runs:
            t = trun.get(x['name'])
            C.c(it, '%s keep' % x['name'], x['keep'], t.get('keep') if t else None, 'exact')
            if t is None:
                continue
            for k in KEYS:
                C.c(it, '%s raw %s' % (x['name'], k), x['raw'][k], (t.get('raw') or {}).get(k))
            C.c(it, '%s raw frames' % x['name'], x['raw']['n'], (t.get('raw') or {}).get('frames'), 'exact')
            r = x['csv']
            C.c(it + ' csv', '%s frames vs results.csv' % x['name'], x['raw']['n'], int(r['frames']), 'exact')
            C.c(it + ' csv', '%s median_ms vs results.csv' % x['name'], x['raw']['p50_ms'], fnum(r['median_ms']),
                'printed', 3)
            C.c(it + ' csv', '%s p99_ms vs results.csv' % x['name'], x['raw']['p99_ms'], fnum(r['p99_ms']), 'printed', 3)
            C.c(it + ' csv', '%s fps_mean vs results.csv' % x['name'], x['raw']['fps'], fnum(r['fps_mean']), 'printed', 3)
            mine_out['runs'][x['name']] = {k: x[k] for k in ('arm', 'round', 'keep', 'raw', 'ls_T', 'c_frames', 'c_bins',
                                                            'bins_n', 'cov')}
        ms = {}  # (method, key) -> my summary
        for k in KEYS:
            ms[('raw', k)] = summ(collect(kept, lambda x, k=k: x['raw'][k]), ref, order)
            th = find_method(R, 'raw', k)
            if th is None:
                C.mm.append((it, 'raw %s missing in JSON' % k, None, 'present'))
            else:
                cmp_summary(C, it, 'raw %s' % k, ms[('raw', k)], th)
        w('%s raw median-ms band (ref %s) = %.4f %%' % (wname, ref, ms[('raw', 'p50_ms')]['band_pct']))
        # ---- item 2: B paired raw and T-std, B-norm raw and T-std
        it = wname + '-2'
        for x in runs:
            t = trun.get(x['name']) or {}
            x['t_std'] = t.get('t_std')
            x['a_S'] = t.get('a_S')
        for field, src in (('raw', 'raw'), ('t_std', 'T-std')):
            for k in KEYS:
                g = (lambda x, k=k, field=field: (x.get(field) or {}).get(k))
                p = paired(kept, g, ref, order)
                mine_out['paired']['%s %s' % (src, k)] = p
                tp = next((q for q in R['paired'] if q.get('src') == src and q.get('key') == k), None)
                if tp is None:
                    C.mm.append((it, 'paired %s %s missing in JSON' % (src, k), None, 'present'))
                    continue
                C.c(it, 'paired %s %s arms' % (src, k), sorted(p), sorted(tp['arms']), 'exact')
                for arm, e in p.items():
                    te = tp['arms'].get(arm) or {}
                    tag = 'paired %s %s %s' % (src, k, arm)
                    C.c(it, tag + ' rounds', [str(r) for r in e['rounds']], [str(r) for r in te.get('rounds') or []],
                        'exact')
                    for i, (a, b) in enumerate(zip(e['deltas'], te.get('deltas') or [])):
                        C.c(it, tag + ' round %s delta' % e['rounds'][i], a, b, 'pp')
                    for f in ('med', 'range', 'mean', 'hw95'):
                        C.c(it, tag + ' ' + f, e[f], te.get(f), 'pp')
                    C.c(it, tag + ' up', e['up'], te.get('up'), 'exact')
                nv = bnorm(kept, g)
                s = summ(collect(kept, lambda x, nv=nv: nv.get(x['name'])), ref, order)
                ms[('B-norm ' + src, k)] = s
                th = find_method(R, 'B-norm ' + src, k)
                if th is None:
                    C.mm.append((it, 'B-norm %s %s missing in JSON' % (src, k), None, 'present'))
                else:
                    cmp_summary(C, it, 'B-norm %s %s' % (src, k), s, th)
            if field == 't_std':
                for k in KEYS:
                    ms[('T-std', k)] = summ(collect(kept, lambda x, k=k: (x.get('t_std') or {}).get(k)), ref, order)
        for k in KEYS:  # A-heavy summary from the JSON per-run a_S (needed for item 5's pooled CV / band)
            ms[('A-heavy', k)] = summ(collect(kept, lambda x, k=k: (x.get('a_S') or {}).get(k)), ref, order)
        # ---- item 3: C-frames, C-bins
        it = wname + '-3'
        for x in runs:
            t = trun.get(x['name'])
            if t is None:
                continue
            C.c(it, '%s c_frames fps' % x['name'], x['c_frames']['fps'], (t.get('c_frames') or {}).get('fps'))
            C.c(it, '%s bins_n' % x['name'], x['bins_n'], t.get('bins_n'), 'exact')
            for k in ('fps', 'p99_ms', 'low1_fps'):
                C.c(it, '%s c_bins %s' % (x['name'], k), (x['c_bins'] or {}).get(k), (t.get('c_bins') or {}).get(k))
        for field, mid, keys in (('c_frames', 'C-frames', ('fps',)), ('c_bins', 'C-bins', ('fps', 'p99_ms', 'low1_fps'))):
            for k in keys:
                s = summ(collect(kept, lambda x, k=k, field=field: (x.get(field) or {}).get(k)), ref, order)
                ms[(mid, k)] = s
                th = find_method(R, mid, k)
                if th is None:
                    C.mm.append((it, '%s %s missing in JSON' % (mid, k), None, 'present'))
                else:
                    cmp_summary(C, it, '%s %s' % (mid, k), s, th)
            for k in KEYS:
                if k not in keys and find_method(R, mid, k) is not None:
                    C.mm.append((it, '%s %s in JSON but not defined' % (mid, k), 'present', None))
        # ---- item 4: D ANCOVAs (+ L-ls for item 5), per-run covariates, cov_info
        it = wname + '-4'
        for x in runs:
            t = trun.get(x['name'])
            if t is None:
                continue
            for c in ('e_mhz', 'p_util', 'cpu_util', 'cores', 'nongame', 'ls_T', 'e_util'):
                C.c(it, '%s cov %s' % (x['name'], c), x['cov'][c], (t.get('cov') or {}).get(c))
            C.c(it, '%s cores_csv' % x['name'], x['cov']['cores'], t.get('cores_csv'))
        for mid, covs in (('L-ls', ('ls_T',)), ('D-emhz', ('e_mhz',)), ('D-putil', ('p_util',)),
                          ('D-emhz+putil', ('e_mhz', 'p_util')), ('D-nongame', ('nongame',))):
            for k in KEYS:
                s = ancova(collect(kept, lambda x, k=k: x['raw'][k]),
                           lambda nm, covs=covs: [byname[nm]['cov'][c] for c in covs], ref, order)
                ms[(mid, k)] = s
                th = find_method(R, mid, k)
                itm = it if mid != 'L-ls' else wname + '-5 (L-ls)'
                if th is None:
                    C.mm.append((itm, '%s %s missing in JSON' % (mid, k), None, 'present'))
                else:
                    cmp_summary(C, itm, '%s %s' % (mid, k), s, th, ancova_b=True)
        for key in ('ls_T', 'e_mhz', 'p_util', 'nongame', 'e_util', 'cores'):
            g = {}
            for x in kept:
                if x['cov'][key] is not None:
                    g.setdefault(x['arm'], []).append(x['cov'][key])
            a = anova(g, order)
            mine_out['cov_info'][key] = a
            t = (R.get('cov_info') or {}).get(key)
            if t is None:
                C.mm.append((it, 'cov_info %s missing in JSON' % key, None, 'present'))
                continue
            C.c(it, 'cov_info %s F' % key, a['F'], t.get('F'))
            C.c(it, 'cov_info %s df' % key, a['df'], t.get('df'), 'exact')
            for arm, v in a['means'].items():
                C.c(it, 'cov_info %s mean %s' % (key, arm), v, (t.get('means') or {}).get(arm))
        mine_out['methods'] = {'%s %s' % kk: v for kk, v in ms.items()}
        # ---- item 5: noise case (median ms, fps): LOO residuals of the flagged runs
        it = wname + '-5'
        flag = [x['name'] for x in kept if x['cov']['p_util'] is not None and x['cov']['e_mhz'] is not None
                and x['cov']['p_util'] >= 90.0 and x['cov']['e_mhz'] < 600.0]
        w('%s flagged (P util >= 90, E MHz < 600): %s' % (wname, ', '.join(flag) or 'none'))
        secs = parse_md_tables(os.path.join(NOISE, casemd))
        for k, lab in (('p50_ms', 'median ms'), ('fps', 'fps')):
            ft = secs.get('%s: the flagged runs' % lab) or []
            hdr = ft[0] if ft else []
            mdflag = hdr[1:hdr.index('flagged mean')] if 'flagged mean' in hdr else []
            if mdflag == ['(none flagged)']:
                mdflag = []
            C.c(it, '%s flagged runs' % lab, flag, mdflag, 'exact')
            rows = {r[0]: r for r in ft[1:]}
            every = secs.get('%s: every kept run (residual %%, + = slower)' % lab) or []
            ehdr = every[0] if every else []
            erows = {r[1]: r for r in every[1:]}
            raw_fmean = None
            for mid in ('raw', 'T-std', 'L-ls', 'A-heavy', 'D-emhz+putil', 'B-norm raw'):
                s = ms[(mid, k)]
                vals = {arm: list(zip(e['runs'], e['vals'])) for arm, e in s['arms'].items()}
                res = loo(vals, SIGN[k])
                fv = [res[nm] for nm in flag if nm in res]
                fmean = sum(fv) / len(fv) if fv else None
                if mid == 'raw':
                    raw_fmean = fmean
                share = 100.0 * fmean / raw_fmean if fmean is not None and raw_fmean else None
                oth = [v for nm, v in res.items() if nm not in flag]
                rms = math.sqrt(sum(v * v for v in oth) / len(oth)) if oth else None
                mine_out['case']['%s %s' % (mid, k)] = {'res': res, 'flagged_mean': fmean, 'share': share, 'rms': rms}
                w('%s %s %-13s flagged %s | mean %s | RMS others %s' % (
                    wname, lab, mid, ', '.join('%s %+.4f' % (nm, res[nm]) for nm in flag if nm in res),
                    '-' if fmean is None else '%+.4f' % fmean, '-' if rms is None else '%.4f' % rms))
                # full precision vs residuals from the JSON's own method values (their per-run values, my LOO)
                th = find_method(R, mid, k)
                if th is not None:
                    tres = loo({arm: list(zip(e.get('runs') or [], e.get('vals') or [])) for arm, e in th['arms'].items()},
                               SIGN[k])
                    for nm in res:
                        C.c(it, '%s %s %s residual vs JSON-vals residual' % (lab, mid, nm), res[nm], tres.get(nm), 'pp')
                r = rows.get(mid)
                if r is None:
                    C.mm.append((it, '%s %s row missing in %s' % (lab, mid, casemd), None, 'present'))
                    continue
                for i, nm in enumerate(mdflag):
                    C.c(it, '%s %s %s residual' % (lab, mid, nm), res.get(nm), pnum(r[1 + i]), 'printed', 1)
                j = 1 + len(mdflag) if mdflag else 2
                C.c(it, '%s %s flagged mean' % (lab, mid), fmean, pnum(r[j]), 'printed', 1)
                C.c(it, '%s %s flagged mean / raw %%' % (lab, mid), share, pnum(r[j + 1]), 'printed', 0)
                C.c(it, '%s %s RMS others' % (lab, mid), rms, pnum(r[j + 2]), 'printed', 1)
                C.c(it, '%s %s pooled CV' % (lab, mid), s['cv_pct'], pnum(r[j + 3]), 'printed', 1)
                C.c(it, '%s %s ref band' % (lab, mid), s['band_pct'], pnum(r[j + 4]), 'printed', 1)
                if mid in ehdr:
                    ci = ehdr.index(mid)
                    for nm, er in erows.items():
                        C.c(it, '%s %s %s residual (every-run table)' % (lab, mid, nm), res.get(nm), pnum(er[ci]),
                            'printed', 1)
        with open(os.path.join(OUTD, 'mine-%s.json' % wname.lower()), 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(mine_out, fh, indent=1)
    w('')
    w('== comparisons per item: count, max relative diff, max abs diff (pp)')
    for item in sorted(C.count):
        w('%-24s n=%-5d max rel %s  max pp %s' % (item, C.count[item],
                                                  '%.3g' % C.maxrel[item] if item in C.maxrel else '-',
                                                  '%.3g' % C.maxpp[item] if item in C.maxpp else '-'))
    for key in sorted(k for k in C.maxpp if k not in C.count):
        w('%-40s max abs diff %.4g' % (key, C.maxpp[key]))
    w('')
    w('== mismatches (%d): item | what | theirs | mine' % len(C.mm))
    for m in C.mm:
        w('%s | %s | %r | %r' % m)
    text = '\n'.join(log) + '\n'
    with open(os.path.join(OUTD, 'check-out.txt'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    sys.stdout.write(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Checker 1 (task #6): independent recompute of noise_methods.py's raw / T / A2 per-run numbers, the per-method
summaries (raw, T-std, T-light, T-heavy, A2-std, A2-light, A2-heavy) and the L-ls ANCOVA, for W4b and W5, compared
against build\\agent7\\w4b-noise\\report.json / report-w5.json. Own code (stdlib only, one thread); it does not import
noise_methods.py or w4b_readout.py. Writes only into build\\agent7\\w4b-noise\\check-phase\\.

Usage: python -B build\\agent7\\w4b-noise\\check-phase\\check_phase.py
"""
import bisect
import csv
import json
import math
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
NOISE = os.path.join(REPO, 'build', 'agent7', 'w4b-noise')
WINDOWS = (('W4b', os.path.join(REPO, 'build', 'agent8', 'matrix', '20261122-1541'), os.path.join(NOISE, 'report.json')),
           ('W5', os.path.join(REPO, 'build', 'agent8', 'matrix', '20261122-1756'), os.path.join(NOISE, 'report-w5.json')))
ROLL, HEAVY_MS, ROLL_GUARD_S, LIGHT_MS_DEFAULT = 201, 5.0, 0.5, 4.5
KEYS = ('fps', 'p50_ms', 'p99_ms', 'low1_fps')
TQ = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
      11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086}
REL_TOL, PP_TOL = 1e-4, 0.01
# method id -> per-run field of my numbers
SUMMARY_METHODS = (('raw', 'raw'), ('T-std', 't_std'), ('T-light', 't_L'), ('T-heavy', 't_H'),
                   ('A2-std', 'a2_std'), ('A2-light', 'a2_F'), ('A2-heavy', 'a2_S'))


def tq(df):
    if df in TQ:
        return TQ[df]
    return TQ[max(k for k in TQ if k <= df)] if df >= 1 else None


def med(v):
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def mean(v):
    return math.fsum(v) / len(v)


def read_frame_times(path, source, column, scale, first, nrows):
    """Good rows of the frames csv (header width; perf: every field an int; a last line without newline dropped),
    rows [first, first + nrows) of the good rows, values > 0."""
    with open(path, 'rb') as fh:
        lines = fh.read().split(b'\n')
    complete = lines[:-1]  # the piece after the last newline is incomplete (or empty)
    if not complete:
        return []
    header = [h.strip() for h in complete[0].decode('ascii', 'replace').rstrip('\r').split(',')]
    if column not in header:
        return []
    ci, width = header.index(column), len(header)
    good, need = [], first + nrows
    for ln in complete[1:]:
        if len(good) >= need:
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
        good.append(v)
    return [v for v in good[first:first + nrows] if v > 0]


def plain(ft):
    """fps, nearest-rank p50 / p99 (ms), 1% low (slowest max(1, n // 100) frames)."""
    if not ft:
        return None
    s = sorted(ft)
    n = len(s)
    k = max(1, n // 100)
    r50, r99 = -(-n * 50 // 100), -(-n * 99 // 100)  # ceil(p n), exact
    return {'fps': n * 1e6 / math.fsum(s), 'p50_ms': s[max(r50, 1) - 1] / 1000.0, 'p99_ms': s[max(r99, 1) - 1] / 1000.0,
            'low1_fps': 1000.0 / (math.fsum(s[n - k:]) / k / 1000.0)}


def mixed(L, H, h):
    """L, H frame classes mixed at heavy time share h: weight (1 - h) / TL per L frame, h / TH per H frame."""
    if not L or not H or h is None:
        return None
    TL, TH = math.fsum(L), math.fsum(H)
    wL, wH = (1.0 - h) / TL, h / TH
    sL, sH = sorted(L), sorted(H)
    tot = wL * len(sL) + wH * len(sH)
    uniq = sorted(set(sL) | set(sH))

    def cum(v):  # total weight of the frames <= v, from counts (no running sum)
        return wL * bisect.bisect_right(sL, v) + wH * bisect.bisect_right(sH, v)

    def wq(q):
        target = q * tot * (1.0 - 1e-12)
        if cum(uniq[-1]) < target:
            return uniq[-1]
        lo, hi = 0, len(uniq) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if cum(uniq[mid]) >= target:
                hi = mid
            else:
                lo = mid + 1
        return uniq[lo]

    need, acc, sx = 0.01 * tot, 0.0, 0.0
    for v in reversed(uniq):  # groups of equal value, slowest first; the last group taken partly
        gw = wL * (bisect.bisect_right(sL, v) - bisect.bisect_left(sL, v)) + \
            wH * (bisect.bisect_right(sH, v) - bisect.bisect_left(sH, v))
        if acc + gw >= need:
            sx += (need - acc) * v
            acc = need
            break
        acc += gw
        sx += gw * v
    return {'fps': 1e6 * tot, 'p50_ms': wq(0.5) / 1000.0, 'p99_ms': wq(0.99) / 1000.0, 'low1_fps': 1e6 * acc / sx}


def roll_classify(ft, ends, k, heavy_ms, guard_s):
    """Centred rolling median of k frames (window cut at the ends; upper median of an even window) > heavy_ms -> S;
    frames whose end time is within guard_s (strict) of a switch (the end of the frame before it) -> None."""
    n, half, thr = len(ft), k // 2, heavy_ms * 1000.0
    heavy = []
    for i in range(n):
        w = sorted(ft[max(0, i - half):min(n, i + half + 1)])
        heavy.append(w[len(w) // 2] > thr)
    sw = [ends[i - 1] for i in range(1, n) if heavy[i] != heavy[i - 1]]
    drop = [False] * n
    for s in sw:
        for j in range(bisect.bisect_right(ends, s - guard_s), bisect.bisect_left(ends, s + guard_s)):
            drop[j] = True
    return [None if drop[i] else ('S' if heavy[i] else 'F') for i in range(n)], len(sw)


def load(d):
    with open(os.path.join(d, 'results.csv'), encoding='utf-8-sig', newline='') as fh:
        rows = list(csv.DictReader(fh))
    with open(os.path.join(d, 'matrix.json'), encoding='utf-8-sig') as fh:
        mj = json.load(fh)
    cfg = [a['id'] for a in mj.get('arms', []) if isinstance(a, dict) and a.get('id')]
    present = []
    for r in rows:
        if r['arm'] not in present:
            present.append(r['arm'])
    order = [a for a in cfg if a in present] + [a for a in present if a not in cfg]
    refs = [a['id'] for a in mj.get('arms', []) if isinstance(a, dict) and a.get('ref') and a.get('id') in present]
    ref = refs[0] if refs else (mj.get('reference') if mj.get('reference') in present else order[0])
    runs = []
    for r in rows:
        rd = (r.get('run_dir') or '').strip()
        if not os.path.isdir(rd):
            alt = os.path.join(d, 'runs', os.path.basename(rd.rstrip('\\/')))
            rd = alt if os.path.isdir(alt) else rd
        x = {'name': os.path.basename(rd.rstrip('\\/')), 'arm': r['arm'], 'round': r['round'],
             'scored': r['scored'].strip().lower() == 'true', 'valid': r['valid_timing'].strip().lower() == 'true',
             'excluded': r['excluded'].strip().lower() == 'true'}
        ft = []
        try:
            with open(os.path.join(rd, 'frames.json'), encoding='utf-8-sig') as fh:
                fj = json.load(fh)
            win = fj['window']
            first, nrows = int(float(win['first_row'])), int(float(win['rows']))
            fpath = os.path.join(rd, os.path.basename(str(fj['file'])))
            if not os.path.isfile(fpath):
                fpath = str(fj['file'])
            ft = read_frame_times(fpath, fj.get('source'), fj['column'], float(fj.get('scale_to_us') or 1.0), first,
                                  nrows)
            x['source'], x['rows'] = fj.get('source'), nrows
            x['share_lt_light'] = fj.get('share_lt_light')
            x['light_ms'] = float(fj.get('light_ms') or LIGHT_MS_DEFAULT)
        except (OSError, ValueError, KeyError, TypeError) as e:
            x['load_error'] = repr(e)
        x['keep'] = x['scored'] and x['valid'] and not x['excluded'] and bool(ft)
        x['n'] = len(ft)
        if ft:
            ends, c = [], 0
            for v in ft:
                c += v
                ends.append(c / 1e6)
            x['raw'] = plain(ft)
            thr = x['light_ms'] * 1000.0
            TL = [v for v in ft if v < thr]
            TH = [v for v in ft if v >= thr]
            x['_TL'], x['_TH'] = TL, TH
            x['ls_T'] = len(TL) / float(len(ft))
            x['hT'] = math.fsum(TH) / math.fsum(ft)
            x['t_L'], x['t_H'] = plain(TL), plain(TH)
            lab, nsw = roll_classify(ft, ends, ROLL, HEAVY_MS, ROLL_GUARD_S)
            F2 = [v for v, l in zip(ft, lab) if l == 'F']
            S2 = [v for v, l in zip(ft, lab) if l == 'S']
            x['_F2'], x['_S2'] = F2, S2
            x['switches2'] = nsw
            x['a2_F'], x['a2_S'] = plain(F2), plain(S2)
            tf, ts = math.fsum(F2), math.fsum(S2)
            x['h2'] = ts / (tf + ts) if tf + ts > 0 else None
        runs.append(x)
    return runs, order, ref


def summary(byarm, ref, order):
    """byarm {arm: [(name, value)]} -> band, pooled SD of ln, per-arm deltas and CIs."""
    if ref not in byarm:
        return None
    rv = [v for _, v in byarm[ref]]
    rmed = med(rv)
    out = {'ref_vals': rv, 'ref_med': rmed, 'band_pct': 100.0 * (max(rv) - min(rv)) / rmed}
    ss, df = 0.0, 0
    for lst in byarm.values():
        if len(lst) >= 2:
            lv = [math.log(v) for _, v in lst]
            m = mean(lv)
            ss += math.fsum((u - m) ** 2 for u in lv)
            df += len(lv) - 1
    sd = math.sqrt(ss / df) if df else None
    t = tq(df) if df else None
    out.update(sd_ln=sd, cv_pct=100.0 * sd if sd is not None else None, df=df,
               hw44_pct=100.0 * (math.exp(t * sd * math.sqrt(0.5)) - 1.0) if sd is not None else None)
    lref = mean([math.log(v) for v in rv])
    arms = {}
    for arm in order:
        if arm not in byarm:
            continue
        av = [v for _, v in byarm[arm]]
        e = {'n': len(av), 'runs': [nm for nm, _ in byarm[arm]], 'vals': av, 'med': med(av)}
        if arm != ref:
            e['delta_pct'] = 100.0 * (e['med'] - rmed) / rmed
            e['verdict'] = 'within' if abs(e['delta_pct']) <= out['band_pct'] else None
            dl = mean([math.log(v) for v in av]) - lref
            e['gm_delta_pct'] = 100.0 * (math.exp(dl) - 1.0)
            if sd is not None:
                hw = t * sd * math.sqrt(1.0 / len(av) + 1.0 / len(rv))
                e['ci_pct'] = [100.0 * (math.exp(dl - hw) - 1.0), 100.0 * (math.exp(dl + hw) - 1.0)]
        arms[arm] = e
    out['arms'] = arms
    return out


def ancova_ls(byarm, xs, ref, order):
    """ln(value) on the light share with the arm as a factor; residual SS computed directly."""
    if ref not in byarm:
        return None
    G = len(byarm)
    n = sum(len(l) for l in byarm.values())
    df = n - G - 1
    my = {a: mean([math.log(v) for _, v in l]) for a, l in byarm.items()}
    mx = {a: mean([xs[nm] for nm, _ in l]) for a, l in byarm.items()}
    Sxx = math.fsum((xs[nm] - mx[a]) ** 2 for a, l in byarm.items() for nm, _ in l)
    Sxy = math.fsum((xs[nm] - mx[a]) * (math.log(v) - my[a]) for a, l in byarm.items() for nm, v in l)
    b = Sxy / Sxx
    xbar = mean([xs[nm] for l in byarm.values() for nm, _ in l])
    ssr = math.fsum((math.log(v) - my[a] - b * (xs[nm] - mx[a])) ** 2 for a, l in byarm.items() for nm, v in l)
    sd = math.sqrt(ssr / df)
    t = tq(df)
    adj = {a: [(nm, math.exp(math.log(v) - b * (xs[nm] - xbar))) for nm, v in l] for a, l in byarm.items()}
    rv = [v for _, v in adj[ref]]
    rmed = med(rv)
    out = {'b': [b], 'df': df, 'sd_ln': sd, 'cv_pct': 100.0 * sd, 'ref_vals': rv, 'ref_med': rmed,
           'band_pct': 100.0 * (max(rv) - min(rv)) / rmed, 'hw44_pct': 100.0 * (math.exp(t * sd * math.sqrt(0.5)) - 1.0)}
    arms = {}
    nref = len(byarm[ref])
    for arm in order:
        if arm not in adj:
            continue
        av = [v for _, v in adj[arm]]
        e = {'n': len(av), 'runs': [nm for nm, _ in adj[arm]], 'vals': av, 'med': med(av)}
        if arm != ref:
            e['delta_pct'] = 100.0 * (e['med'] - rmed) / rmed
            e['verdict'] = 'within' if abs(e['delta_pct']) <= out['band_pct'] else None
            dl = (my[arm] - my[ref]) - b * (mx[arm] - mx[ref])
            e['gm_delta_pct'] = 100.0 * (math.exp(dl) - 1.0)
            hw = t * sd * math.sqrt(1.0 / len(av) + 1.0 / nref + (mx[arm] - mx[ref]) ** 2 / Sxx)
            e['ci_pct'] = [100.0 * (math.exp(dl - hw) - 1.0), 100.0 * (math.exp(dl + hw) - 1.0)]
        arms[arm] = e
    out['arms'] = arms
    return out


class Cmp:
    def __init__(self):
        self.st = {}

    def _s(self, item):
        return self.st.setdefault(item, {'n': 0, 'maxrel': 0.0, 'maxrel_at': '', 'maxpp': 0.0, 'maxpp_at': '',
                                         'mism': []})

    def rel(self, item, where, mine, theirs):
        s = self._s(item)
        s['n'] += 1
        if mine is None or theirs is None:
            if (mine is None) != (theirs is None):
                s['mism'].append('%s: report %r, mine %r' % (where, theirs, mine))
            return
        r = 0.0 if mine == theirs else abs(mine - theirs) / max(abs(theirs), abs(mine), 1e-300)
        if r > s['maxrel']:
            s['maxrel'], s['maxrel_at'] = r, where
        if r > REL_TOL:
            s['mism'].append('%s: report %.10g, mine %.10g (rel %.3g)' % (where, theirs, mine, r))

    def pp(self, item, where, mine, theirs):
        s = self._s(item)
        s['n'] += 1
        if mine is None or theirs is None:
            if (mine is None) != (theirs is None):
                s['mism'].append('%s: report %r, mine %r' % (where, theirs, mine))
            return
        dd = abs(mine - theirs)
        if dd > s['maxpp']:
            s['maxpp'], s['maxpp_at'] = dd, where
        if dd > PP_TOL:
            s['mism'].append('%s: report %.6f, mine %.6f (diff %.4g pp)' % (where, theirs, mine, dd))

    def eq(self, item, where, mine, theirs):
        s = self._s(item)
        s['n'] += 1
        if mine != theirs:
            s['mism'].append('%s: report %r, mine %r' % (where, theirs, mine))


def cmp_summary(C, item, tag, mine, theirs, ancova=False):
    if mine is None or theirs is None:
        C.eq(item, tag + ' present', mine is not None, theirs is not None)
        return
    C.eq(item, tag + ' df', mine['df'], theirs['df'])
    rvm, rvt = mine['ref_vals'], theirs['ref_vals']
    C.eq(item, tag + ' n ref_vals', len(rvm), len(rvt))
    for i, (u, w) in enumerate(zip(rvm, rvt)):
        C.rel(item, tag + ' ref_vals[%d]' % i, u, w)
    C.rel(item, tag + ' ref_med', mine['ref_med'], theirs.get('ref_med'))
    C.pp(item, tag + ' band_pct', mine['band_pct'], theirs['band_pct'])
    C.rel(item, tag + ' sd_ln', mine['sd_ln'], theirs['sd_ln'])
    C.pp(item, tag + ' cv_pct', mine['cv_pct'], theirs['cv_pct'])
    C.pp(item, tag + ' hw44_pct', mine['hw44_pct'], theirs['hw44_pct'])
    if ancova:
        C.rel(item, tag + ' b', mine['b'][0], (theirs.get('b') or [None])[0])
    C.eq(item, tag + ' arms', sorted(mine['arms']), sorted(theirs['arms']))
    for arm, e in mine['arms'].items():
        f = theirs['arms'].get(arm)
        if f is None:
            continue
        at = '%s %s' % (tag, arm)
        C.eq(item, at + ' n', e['n'], f['n'])
        C.eq(item, at + ' runs', e['runs'], f['runs'])
        for i, (u, w) in enumerate(zip(e['vals'], f['vals'])):
            C.rel(item, at + ' vals[%d]' % i, u, w)
        C.rel(item, at + ' med', e['med'], f['med'])
        if 'delta_pct' in e or 'delta_pct' in f:
            C.pp(item, at + ' delta_pct', e.get('delta_pct'), f.get('delta_pct'))
            C.pp(item, at + ' gm_delta_pct', e.get('gm_delta_pct'), f.get('gm_delta_pct'))
            cm, cf = e.get('ci_pct'), f.get('ci_pct')
            C.pp(item, at + ' ci_lo', cm[0] if cm else None, cf[0] if cf else None)
            C.pp(item, at + ' ci_hi', cm[1] if cm else None, cf[1] if cf else None)
            C.eq(item, at + ' verdict within', e.get('verdict') == 'within', f.get('verdict') == 'within')


def check_window(label, d, rpath, log):
    runs, order, ref = load(d)
    kept = [x for x in runs if x['keep']]
    hTs = [x['hT'] for x in kept if x.get('hT') is not None and 0.0 < x['hT'] < 1.0]
    h2s = [x['h2'] for x in kept if x.get('h2') is not None and 0.0 < x['h2'] < 1.0]
    hT_ref = med(hTs) if hTs else None
    h2_ref = med(h2s) if h2s else None
    for x in runs:
        x['t_std'] = mixed(x.pop('_TL', None), x.pop('_TH', None), hT_ref)
        x['a2_std'] = mixed(x.pop('_F2', None), x.pop('_S2', None), h2_ref)
    with open(rpath, encoding='utf-8') as fh:
        R = json.load(fh)
    C = Cmp()
    log('## %s: %s' % (label, d))
    log('- report: %s (params roll %s heavy_ms %s roll_guard_s %s light_ms %s all %s)' % (
        rpath, R['params'].get('roll'), R['params'].get('heavy_ms'), R['params'].get('roll_guard_s'),
        R['params'].get('light_ms'), R['params'].get('all')))
    log('- mine: ref %s, order %s; kept %d; left out: %s' % (ref, order, len(kept), ', '.join(
        '%s (scored %s valid %s excluded %s n %d)' % (x['name'], x['scored'], x['valid'], x['excluded'], x['n'])
        for x in runs if not x['keep'])))
    log('- sources: %s; light_ms: %s' % (sorted(set(str(x.get('source')) for x in runs)),
                                         sorted(set(x.get('light_ms') for x in runs))))
    log('- mine hT_ref %.6f (report %.6f), h2_ref %.6f (report %.6f)' % (hT_ref, R['hT_ref'], h2_ref, R['h2_ref']))
    C.eq('0 selection', 'ref', ref, R['ref'])
    C.eq('0 selection', 'order', order, R['order'])
    rr = {x['name']: x for x in R['runs']}
    C.eq('0 selection', 'run names', sorted(x['name'] for x in runs), sorted(rr))
    C.eq('0 selection', 'kept names', sorted(x['name'] for x in kept), sorted(n for n, x in rr.items() if x['keep']))
    lsmax = 0.0
    for x in runs:
        t = rr.get(x['name'])
        if t is None or 'raw' not in x:
            continue
        nm = x['name']
        for k in KEYS:
            C.rel('1 raw', '%s raw.%s' % (nm, k), x['raw'][k], (t.get('raw') or {}).get(k))
        # item 2: T split
        if x.get('share_lt_light') is not None:
            dls = abs(x['ls_T'] - float(x['share_lt_light']))
            lsmax = max(lsmax, dls)
            if dls > 5e-5 + 1e-12:
                C._s('2 T split')['mism'].append('%s ls_T %.6f vs frames.json share_lt_light %s' % (
                    nm, x['ls_T'], x['share_lt_light']))
        C.rel('2 T split', '%s ls_T' % nm, x['ls_T'], t.get('ls_T'))
        C.rel('2 T split', '%s hT' % nm, x['hT'], t.get('hT'))
        for fld in ('t_L', 't_H', 't_std'):
            for k in KEYS:
                C.rel('2 T split', '%s %s.%s' % (nm, fld, k), (x.get(fld) or {}).get(k), (t.get(fld) or {}).get(k))
        C.rel('3 A2', '%s h2' % nm, x.get('h2'), t.get('h2'))
        C.eq('3 A2', '%s switches2' % nm, x.get('switches2'), t.get('switches2'))
        for fld in ('a2_F', 'a2_S', 'a2_std'):
            for k in KEYS:
                C.rel('3 A2', '%s %s.%s' % (nm, fld, k), (x.get(fld) or {}).get(k), (t.get(fld) or {}).get(k))
    C.rel('2 T split', 'hT_ref', hT_ref, R['hT_ref'])
    C.rel('3 A2', 'h2_ref', h2_ref, R['h2_ref'])
    log('- max |ls_T - frames.json share_lt_light| = %.3g (share_lt_light has 4 decimals); report ls_check_max_abs %s'
        % (lsmax, R.get('ls_check_max_abs')))
    tm = {}
    for s in R['methods']:
        tm[(s['method'], s['key'])] = s
    mine_methods = {}
    for mid, fld in SUMMARY_METHODS:
        for k in KEYS:
            byarm = {}
            for x in kept:
                v = (x.get(fld) or {}).get(k)
                if v is not None and v > 0:
                    byarm.setdefault(x['arm'], []).append((x['name'], v))
            m = summary(byarm, ref, order)
            mine_methods['%s %s' % (mid, k)] = m
            cmp_summary(C, '4 summaries', '%s/%s' % (mid, k), m, tm.get((mid, k)))
    xs = {x['name']: x['ls_T'] for x in kept}
    for k in KEYS:
        byarm = {}
        for x in kept:
            v = x['raw'][k]
            if v is not None and v > 0:
                byarm.setdefault(x['arm'], []).append((x['name'], v))
        m = ancova_ls(byarm, xs, ref, order)
        mine_methods['L-ls %s' % k] = m
        cmp_summary(C, '5 L-ls', 'L-ls/%s' % k, m, tm.get(('L-ls', k)), ancova=True)
    for item in sorted(C.st):
        s = C.st[item]
        log('- item %s: %s (%d comparisons; max rel %.3g at %s; max abs pp %.3g at %s)' % (
            item, 'OK' if not s['mism'] else 'MISMATCH x%d' % len(s['mism']), s['n'], s['maxrel'], s['maxrel_at'] or '-',
            s['maxpp'], s['maxpp_at'] or '-'))
        for m in s['mism'][:60]:
            log('    MISMATCH %s' % m)
    log('')
    mine = {'ref': ref, 'order': order, 'hT_ref': hT_ref, 'h2_ref': h2_ref,
            'runs': [{k: v for k, v in x.items() if not k.startswith('_')} for x in runs], 'methods': mine_methods}
    with open(os.path.join(HERE, 'mine-%s.json' % label.lower()), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(mine, fh, indent=1)
    return C


def main():
    lines = []

    def log(s):
        print(s)
        lines.append(s)

    log('# Checker 1: independent recompute of raw / T / A2 / summaries / L-ls (noise_methods.py)')
    log('')
    for label, d, rpath in WINDOWS:
        check_window(label, d, rpath, log)
    with open(os.path.join(HERE, 'check-phase.md'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(lines) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())

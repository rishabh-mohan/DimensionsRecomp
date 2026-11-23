#!/usr/bin/env python3
"""pool_readout.py (Agent 8, task #20): per-arm numbers for one window from one or more run-matrix passes, pooled and
per pass. Read-only on the inputs; lowers itself to Below Normal.

Usage: python -B pool_readout.py --name W6 --base s0 [--contrast p2fc-p2f ...] [--drop RUN,...] [--tails]
       [--md OUT.md] [--json OUT.json] PASSDIR [PASSDIR ...]

Kept runs: scored, status OK, valid_timing True, not excluded (the rule of noise_methods.py / readout.py), minus --drop.
A round is (pass, round), so pass 2 round 1 is its own round. Per arm: n, median of the run median_ms (and their mean),
mean fps_mean, mean cpu_cores_mean, frames. Paired per round vs the base (and for each --contrast A-B): median ms
difference, log-ratio mean with a 95 % t-CI shown as %, fps the same way, cpu cores as a difference; sign count with an
exact two-sided sign-test p.
--tails re-reads each run's perf.csv frames.json window (first_row, rows; data rows counted from 0 after the header)
and checks it against frames.json median/p99/p99.9/max/over_33ms (nearest-rank). If it matches, it counts frames over
6/8/10/16.7/33 ms per minute of window, the time share in frames over 6 ms, the 5th/25th/50th largest frame (in a 50 s
window: about once per 10 s / 2 s / 1 s; this does not depend on the frame count as p99.9 does), and >6 ms frames per
10 s bin.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import statistics as st
import sys

sys.dont_write_bytecode = True

T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
        21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042}
THR = (6.0, 8.0, 10.0, 16.7, 33.0)
TOPK = (5, 25, 50)
NAN = float('nan')


def below_normal():
    try:
        import ctypes
        k = ctypes.windll.kernel32
        k.SetPriorityClass(k.GetCurrentProcess(), 0x4000)
    except Exception:
        pass


def t975(df):
    if df <= 0:
        return NAN
    return T975.get(df, 2.0 if df < 60 else 1.96)


def truthy(v):
    return str(v).strip().lower() in ('true', '1', 'yes')


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return NAN


def isnan(x):
    return isinstance(x, float) and math.isnan(x)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        h.update(f.read())
    return h.hexdigest().upper()


def f_(x, nd=2, sign=False):
    if x is None or isnan(x):
        return '-'
    s = ('%+.' + str(nd) + 'f') if sign else ('%.' + str(nd) + 'f')
    return s % x


def pct(x):
    return (math.exp(x) - 1.0) * 100.0


def mean_ci(vals):
    n = len(vals)
    if n == 0:
        return dict(n=0, mean=NAN, sd=NAN, lo=NAN, hi=NAN)
    m = st.mean(vals)
    if n < 2:
        return dict(n=n, mean=m, sd=NAN, lo=NAN, hi=NAN)
    sd = st.stdev(vals)
    h = t975(n - 1) * sd / math.sqrt(n)
    return dict(n=n, mean=m, sd=sd, lo=m - h, hi=m + h)


def sign_count(vals):
    neg = sum(1 for v in vals if v < 0)
    pos = sum(1 for v in vals if v > 0)
    n = neg + pos
    if n == 0:
        return dict(neg=0, pos=0, ties=len(vals), p=NAN)
    k = min(neg, pos)
    p = min(1.0, 2.0 * sum(math.comb(n, i) for i in range(k + 1)) / 2.0 ** n)
    return dict(neg=neg, pos=pos, ties=len(vals) - n, p=p)


# ---------------------------------------------------------------- perf.csv tails

def nearest_rank(s, p):
    n = len(s)
    return s[max(1, math.ceil(p * n)) - 1]


def close3(x, y):
    if y is None:
        return False
    y = float(y)
    return abs(round(x, 3) - y) < 1e-9 or abs(x - y) <= 0.0005 + 1e-9


def tails_for(run_dir):
    fj = json.load(open(os.path.join(run_dir, 'frames.json'), encoding='utf-8-sig'))
    w = fj['window']
    first, rows = int(w['first_row']), int(w['rows'])
    col = fj.get('column') or 'frame_time_us'
    scale = float(fj.get('scale_to_us') or 1.0)
    allv = []
    with open(os.path.join(run_dir, 'perf.csv'), encoding='utf-8-sig', newline='') as f:
        ci = f.readline().rstrip('\r\n').split(',').index(col)
        for line in f:
            line = line.rstrip('\r\n')
            if line:
                allv.append(float(line.split(',')[ci]) * scale / 1000.0)
    for o in (0, -1, 1, -2, 2):
        win = allv[first + o:first + o + rows]
        if len(win) != rows or not rows:
            continue
        s = sorted(win)
        got = dict(median=nearest_rank(s, 0.5), p99=nearest_rank(s, 0.99), p999=nearest_rank(s, 0.999), max=s[-1])
        ok = all(close3(got[k], fj.get(j)) for k, j in
                 (('median', 'median_ms'), ('p99', 'p99_ms'), ('p999', 'p99_9_ms'), ('max', 'max_ms')))
        o33 = sum(1 for v in win if v > 33.0)
        ok = ok and o33 == int(fj.get('over_33ms') or 0)
        if not ok:
            continue
        wsec = float(fj.get('window_s') or (sum(win) / 1000.0))
        cnt = dict((t, sum(1 for v in win if v > t)) for t in THR)
        desc = s[::-1]
        bins6, t_ms = [0] * 5, 0.0
        imax, tmax = 0, 0.0
        for i, v in enumerate(win):
            if v > 6.0:
                bins6[min(4, int(t_ms // 10000.0))] += 1
            if v > win[imax]:
                imax, tmax = i, t_ms
            t_ms += v
        return dict(check='OK', offset=o, rows=rows, window_s=wsec, median=got['median'], p999=got['p999'],
                    max=got['max'], max_at_s=round(tmax / 1000.0, 3),
                    count=dict(('%g' % t, cnt[t]) for t in THR),
                    rate=dict(('%g' % t, cnt[t] * 60.0 / wsec) for t in THR),
                    top=dict((str(k), desc[k - 1] if len(desc) >= k else NAN) for k in TOPK),
                    share6=sum(v for v in win if v > 6.0) / (wsec * 1000.0),
                    share_lt_light=fj.get('share_lt_light'), bins6=bins6)
    return dict(check='MISMATCH', rows=rows, first_row=first, data_rows=len(allv))


# ---------------------------------------------------------------- results.csv

def load(dirs, drop):
    runs, inputs = [], []
    for pi, d in enumerate(dirs, 1):
        p = os.path.join(d, 'results.csv')
        inputs.append(dict(pass_=pi, dir=d, results_sha256=sha(p),
                           matrix_sha256=sha(os.path.join(d, 'matrix.json'))))
        with open(p, newline='', encoding='utf-8-sig') as f:
            for r in csv.DictReader(f):
                rd = (r.get('run_dir') or '').strip()
                name = os.path.basename(rd.rstrip('\\/'))
                if not os.path.isdir(rd):
                    rd = os.path.join(d, 'runs', name)
                x = dict(pass_=pi, round=(r.get('round') or '').strip(), arm=r['arm'].strip(), name=name,
                         run_dir=rd, scored=truthy(r.get('scored')), ok=(r.get('status') or '').strip() == 'OK',
                         valid=truthy(r.get('valid_timing')), excluded=truthy(r.get('excluded')),
                         median=fnum(r.get('median_ms')), fps=fnum(r.get('fps_mean')),
                         cpu=fnum(r.get('cpu_cores_mean')), frames=int(fnum(r.get('frames')) or 0),
                         p99=fnum(r.get('p99_ms')), p999=fnum(r.get('p999_ms')), max=fnum(r.get('max_ms')),
                         over33=fnum(r.get('over33')), window_s=fnum(r.get('window_s')),
                         flags_info=(r.get('flags_info') or '').strip(),
                         flags_excluding=(r.get('flags_excluding') or '').strip())
                x['timed'] = x['ok'] and x['valid'] and not x['excluded']
                x['dropped'] = name in drop
                x['keep'] = x['scored'] and x['timed'] and name not in drop
                runs.append(x)
    return runs, inputs


def arm_order(runs, base):
    seen = [base]
    for x in runs:
        if x['arm'] not in seen:
            seen.append(x['arm'])
    return seen


def paired(kept, a, b, key, kind):
    """per round (pass, round): value(a) vs value(b). kind 'lr' = log ratio, 'diff' = difference."""
    by = {}
    for x in kept:
        if x['arm'] in (a, b):
            by.setdefault((x['pass_'], int(x['round'])), {}).setdefault(x['arm'], []).append(x)
    out = []
    for rk in sorted(by):
        g = by[rk]
        if a not in g or b not in g:
            continue
        va = st.mean([key(x) for x in g[a]])
        vb = st.mean([key(x) for x in g[b]])
        if isnan(va) or isnan(vb):
            continue
        if kind == 'lr':
            if va <= 0 or vb <= 0:
                continue
            out.append(dict(round=rk, a=va, b=vb, d=math.log(va / vb), diff=va - vb))
        else:
            out.append(dict(round=rk, a=va, b=vb, d=va - vb, diff=va - vb))
    return out


def pair_summary(pl):
    ci = mean_ci([p['d'] for p in pl])
    sc = sign_count([p['diff'] for p in pl])
    return dict(ci=ci, sign=sc, mean_diff=st.mean([p['diff'] for p in pl]) if pl else NAN,
                rounds=[dict(round='p%d r%d' % p['round'], a=p['a'], b=p['b'], diff=p['diff']) for p in pl])


def tail_key(t, field, sub):
    def k(x):
        tl = x.get('tails') or {}
        if tl.get('check') != 'OK':
            return NAN
        v = tl[field]
        return float(v[sub]) if sub is not None else float(v)
    return k


def analyse(runs, arms, base, contrasts, passes, do_tails):
    kept = [x for x in runs if x['keep'] and x['pass_'] in passes]
    res = dict(passes=passes, arms={}, contrasts={})
    for arm in arms:
        xs = [x for x in kept if x['arm'] == arm]
        if not xs:
            continue
        meds = [x['median'] for x in xs]
        a = dict(n=len(xs), median_ms=st.median(meds), mean_median_ms=st.mean(meds),
                 fps=st.mean([x['fps'] for x in xs]), fps_median=st.median([x['fps'] for x in xs]),
                 cpu=st.mean([x['cpu'] for x in xs]),
                 frames_mean=st.mean([x['frames'] for x in xs]), frames_min=min(x['frames'] for x in xs),
                 frames_max=max(x['frames'] for x in xs), p99=st.mean([x['p99'] for x in xs]),
                 p999=st.mean([x['p999'] for x in xs]), p999_median=st.median([x['p999'] for x in xs]),
                 max_ms=max(x['max'] for x in xs), over33=sum(x['over33'] for x in xs),
                 cv_pct=(st.stdev(meds) / st.mean(meds) * 100.0) if len(meds) > 1 else NAN,
                 band_pct=((max(meds) - min(meds)) / st.median(meds) * 100.0))
        if arm != base:
            a['vs_base'] = dict(median=pair_summary(paired(kept, arm, base, lambda x: x['median'], 'lr')),
                                fps=pair_summary(paired(kept, arm, base, lambda x: x['fps'], 'lr')),
                                cpu=pair_summary(paired(kept, arm, base, lambda x: x['cpu'], 'diff')),
                                p999=pair_summary(paired(kept, arm, base, lambda x: x['p999'], 'diff')))
        if do_tails:
            ok = [x for x in xs if (x.get('tails') or {}).get('check') == 'OK']
            if ok:
                a['tails'] = dict(n=len(ok),
                                  rate=dict(('%g' % t, st.mean([x['tails']['rate']['%g' % t] for x in ok]))
                                            for t in THR),
                                  count_total=dict(('%g' % t, sum(x['tails']['count']['%g' % t] for x in ok))
                                                   for t in THR),
                                  top_median=dict((str(k), st.median([x['tails']['top'][str(k)] for x in ok]))
                                                  for k in TOPK),
                                  share6_mean=st.mean([x['tails']['share6'] for x in ok]),
                                  runs_with_over10=sum(1 for x in ok if x['tails']['count']['10'] > 0))
        res['arms'][arm] = a
    tail_metrics = (('rate6', '6'), ('rate8', '8'), ('rate10', '10'))
    for (ca, cb) in contrasts:
        c = dict(median=pair_summary(paired(kept, ca, cb, lambda x: x['median'], 'lr')),
                 fps=pair_summary(paired(kept, ca, cb, lambda x: x['fps'], 'lr')),
                 cpu=pair_summary(paired(kept, ca, cb, lambda x: x['cpu'], 'diff')),
                 p999=pair_summary(paired(kept, ca, cb, lambda x: x['p999'], 'diff')))
        res['contrasts']['%s-%s' % (ca, cb)] = c
    if do_tails:
        res['tail_pairs'] = {}
        pairs = [(arm, base) for arm in arms if arm != base] + list(contrasts)
        for (pa, pb) in pairs:
            d = {}
            for nm, t in tail_metrics:
                d[nm] = pair_summary(paired(kept, pa, pb, tail_key(t, 'rate', t), 'diff'))
            d['top25'] = pair_summary(paired(kept, pa, pb, tail_key(None, 'top', '25'), 'diff'))
            d['top5'] = pair_summary(paired(kept, pa, pb, tail_key(None, 'top', '5'), 'diff'))
            res['tail_pairs']['%s-%s' % (pa, pb)] = d
    return res


# ---------------------------------------------------------------- markdown

def ci_pct(s):
    ci = s['ci']
    if ci['n'] == 0:
        return '-'
    if isnan(ci['lo']):
        return '%s' % f_(pct(ci['mean']), 1, True)
    return '%s [%s, %s]' % (f_(pct(ci['mean']), 1, True), f_(pct(ci['lo']), 1, True), f_(pct(ci['hi']), 1, True))


def ci_abs(s, nd=2):
    ci = s['ci']
    if ci['n'] == 0:
        return '-'
    if isnan(ci['lo']):
        return f_(ci['mean'], nd, True)
    return '%s [%s, %s]' % (f_(ci['mean'], nd, True), f_(ci['lo'], nd, True), f_(ci['hi'], nd, True))


def sgn(s, neg_good=True):
    sc = s['sign']
    k = sc['neg'] if neg_good else sc['pos']
    return '%d/%d (p %s)' % (k, sc['neg'] + sc['pos'], f_(sc['p'], 3))


def write_md(path, a, runs, inputs, arms, base, contrasts, results, drop):
    L = []
    w = L.append
    w('# %s: pooled numbers (pool_readout.py)' % a.name)
    w('')
    w('Base arm `%s`. Kept runs: scored, status OK, valid timing, not excluded%s. A round is (pass, round).' %
      (base, (', minus --drop ' + ', '.join(sorted(drop))) if drop else ''))
    w('Paired = per round, arm vs base in the same round; % values are exp(mean log ratio) - 1 with a 95 % t-CI; '
      'sign count = rounds where the arm is lower (ms, cores) or higher (fps).')
    w('')
    w('| pass | dir | results.csv sha256 | matrix.json sha256 |')
    w('|---|---|---|---|')
    for i in inputs:
        w('| %d | `%s` | `%s` | `%s` |' % (i['pass_'], i['dir'].replace('\\', '/'), i['results_sha256'][:16],
                                          i['matrix_sha256'][:16]))
    w('')
    w('## Runs per arm')
    w('')
    w('| arm | pass | planned (scored) | timed (OK, valid, not excluded) | kept | cold run |')
    w('|---|---|---|---|---|---|')
    for arm in arms:
        for i in inputs:
            xs = [x for x in runs if x['arm'] == arm and x['pass_'] == i['pass_']]
            sc = [x for x in xs if x['scored']]
            cold = [x for x in xs if not x['scored']]
            w('| %s | %d | %d | %d | %d | %s |' % (arm, i['pass_'], len(sc), sum(1 for x in sc if x['timed']),
                                                 sum(1 for x in sc if x['keep']),
                                                 ', '.join('%s %s ms' % (x['name'], f_(x['median'], 3))
                                                           for x in cold) or '-'))
    for label, R in results:
        w('')
        w('## %s: per arm vs base `%s`' % (label, base))
        w('')
        w('| arm | n | median ms (median of runs) | vs base (pooled medians) | paired median | lower in | '
          'fps median | vs base | fps mean | paired fps | CPU cores | paired cores | frames mean (min-max) | '
          'band (max-min)/median | CV |')
        w('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
        bm = R['arms'].get(base, {}).get('median_ms', NAN)
        bf = R['arms'].get(base, {}).get('fps_median', NAN)
        for arm in arms:
            x = R['arms'].get(arm)
            if not x:
                continue
            vb = x.get('vs_base')
            w('| %s | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %d (%d-%d) | %s %% | %s %% |' % (
                arm, x['n'], f_(x['median_ms'], 3),
                '-' if arm == base else f_((x['median_ms'] / bm - 1) * 100, 1, True) + ' %',
                ci_pct(vb['median']) if vb else '-', sgn(vb['median']) if vb else '-', f_(x['fps_median'], 1),
                '-' if arm == base else f_((x['fps_median'] / bf - 1) * 100, 1, True) + ' %', f_(x['fps'], 1),
                ci_pct(vb['fps']) if vb else '-', f_(x['cpu'], 3), ci_abs(vb['cpu'], 3) if vb else '-',
                round(x['frames_mean']), x['frames_min'], x['frames_max'], f_(x['band_pct'], 1),
                f_(x['cv_pct'], 1)))
        if R['contrasts']:
            w('')
            w('| contrast | rounds | mean diff ms | paired median | lower in | paired fps | paired cores |')
            w('|---|---|---|---|---|---|---|')
            for k, c in R['contrasts'].items():
                w('| %s | %d | %s | %s | %s | %s | %s |' % (k, c['median']['ci']['n'], f_(c['median']['mean_diff'], 3, True),
                                                       ci_pct(c['median']), sgn(c['median']), ci_pct(c['fps']),
                                                       ci_abs(c['cpu'], 3)))
        w('')
        w('Per-round median ms difference (arm - base%s):' % ('; contrasts A - B' if R['contrasts'] else ''))
        w('')
        rows = [(arm, R['arms'][arm]['vs_base']['median']['rounds']) for arm in arms
                if arm in R['arms'] and 'vs_base' in R['arms'][arm]]
        rows += [(k, c['median']['rounds']) for k, c in R['contrasts'].items()]
        for nm, rr in rows:
            w('- %s: %s' % (nm, ', '.join('%s %s' % (r['round'], f_(r['diff'], 3, True)) for r in rr)))
        w('')
        w('Tail (results.csv): mean p99 / p99.9 ms, worst frame, frames over 33 ms; paired p99.9 diff vs base:')
        w('')
        w('| arm | p99 mean | p99.9 mean | p99.9 median | max ms | over 33 ms | paired p99.9 diff ms | higher in |')
        w('|---|---|---|---|---|---|---|---|')
        for arm in arms:
            x = R['arms'].get(arm)
            if not x:
                continue
            vb = x.get('vs_base')
            w('| %s | %s | %s | %s | %s | %d | %s | %s |' % (
                arm, f_(x['p99'], 3), f_(x['p999'], 3), f_(x['p999_median'], 3), f_(x['max_ms'], 2),
                int(x['over33']), ci_abs(vb['p999'], 3) if vb else '-', sgn(vb['p999'], False) if vb else '-'))
        if 'tail_pairs' in R:
            w('')
            w('Tail (perf.csv windows): frames over X ms per minute (mean of runs), totals, k-th largest frame '
              '(median of runs), time share over 6 ms:')
            w('')
            w('| arm | runs | >6 ms/min | >8 | >10 | >16.7 | >33 | total >10 / >16.7 / >33 | runs with >10 | '
              'top5 ms | top25 ms | top50 ms | share >6 ms |')
            w('|---|---|---|---|---|---|---|---|---|---|---|---|---|')
            for arm in arms:
                x = R['arms'].get(arm, {}).get('tails')
                if not x:
                    continue
                w('| %s | %d | %s | %s | %s | %s | %s | %d / %d / %d | %d | %s | %s | %s | %s %% |' % (
                    arm, x['n'], f_(x['rate']['6'], 2), f_(x['rate']['8'], 2), f_(x['rate']['10'], 2),
                    f_(x['rate']['16.7'], 2), f_(x['rate']['33'], 2), x['count_total']['10'],
                    x['count_total']['16.7'], x['count_total']['33'], x['runs_with_over10'],
                    f_(x['top_median']['5'], 3), f_(x['top_median']['25'], 3), f_(x['top_median']['50'], 3),
                    f_(x['share6_mean'] * 100, 3)))
            w('')
            w('| pair (A - B) | >6 ms/min diff [CI] | A higher in | >8 diff | A higher in | >10 diff | top25 diff ms | '
              'A higher in | top5 diff ms | A higher in |')
            w('|---|---|---|---|---|---|---|---|---|---|')
            for k, d in R['tail_pairs'].items():
                w('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
                    k, ci_abs(d['rate6'], 2), sgn(d['rate6'], False), ci_abs(d['rate8'], 2), sgn(d['rate8'], False),
                    ci_abs(d['rate10'], 2), ci_abs(d['top25'], 3), sgn(d['top25'], False), ci_abs(d['top5'], 3),
                    sgn(d['top5'], False)))
    if any(x.get('tails') for x in runs):
        w('')
        w('## Per run (perf.csv window check and tails)')
        w('')
        w('| run | pass | round | arm | frames | median | p99.9 | max (at s) | >6 | >8 | >10 | >16.7 | >33 | '
          'top25 | >6 per 10 s bin | check |')
        w('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
        for x in runs:
            t = x.get('tails')
            if not t:
                continue
            if t.get('check') != 'OK':
                w('| %s | %d | %s | %s | %d | | | | | | | | | | | %s |' % (x['name'], x['pass_'], x['round'], x['arm'],
                                                                      x['frames'], t.get('check')))
                continue
            c = t['count']
            w('| %s | %d | %s | %s | %d | %s | %s | %s (%s) | %d | %d | %d | %d | %d | %s | %s | OK (offset %d) |' % (
                x['name'], x['pass_'], x['round'], x['arm'], t['rows'], f_(t['median'], 3), f_(t['p999'], 3),
                f_(t['max'], 2), f_(t['max_at_s'], 1), c['6'], c['8'], c['10'], c['16.7'], c['33'],
                f_(t['top']['25'], 3), ' '.join(str(b) for b in t['bins6']), t['offset']))
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('dirs', nargs='+')
    ap.add_argument('--name', required=True)
    ap.add_argument('--base', required=True)
    ap.add_argument('--contrast', action='append', default=[], help='A-B, paired per round (repeatable)')
    ap.add_argument('--drop', default='', help='run folder names to leave out, comma-separated')
    ap.add_argument('--drop-rounds', default='', help='within-pass round numbers to leave out in every pass, e.g. 1')
    ap.add_argument('--tails', action='store_true', help='read perf.csv windows for the tail metrics')
    ap.add_argument('--md')
    ap.add_argument('--json')
    a = ap.parse_args(argv)
    below_normal()
    drop = set(s.strip() for s in a.drop.split(',') if s.strip())
    contrasts = [tuple(c.split('-', 1)) for c in a.contrast]
    runs, inputs = load(a.dirs, drop)
    names = set(x['name'] for x in runs)
    bad = sorted(drop - names)
    if bad:
        raise SystemExit('--drop names not found: %s' % ', '.join(bad))
    drop_rounds = set(s.strip() for s in a.drop_rounds.split(',') if s.strip())
    if drop_rounds:
        for x in runs:
            if x['scored'] and x['round'] in drop_rounds:
                x['keep'] = False
                drop.add(x['name'])
    arms = arm_order(runs, a.base)
    if a.tails:
        for x in runs:
            if x['scored'] and x['timed']:
                x['tails'] = tails_for(x['run_dir'])
    passes = sorted(set(x['pass_'] for x in runs))
    results = [('pooled' if len(passes) > 1 else 'pass 1', analyse(runs, arms, a.base, contrasts, passes, a.tails))]
    if len(passes) > 1:
        for p in passes:
            results.append(('pass %d' % p, analyse(runs, arms, a.base, contrasts, [p], a.tails)))
    mism = [x['name'] for x in runs if (x.get('tails') or {}).get('check') == 'MISMATCH']
    if a.md:
        write_md(a.md, a, runs, inputs, arms, a.base, contrasts, results, drop)
    if a.json:
        def clean(o):
            if isinstance(o, float) and math.isnan(o):
                return None
            if isinstance(o, dict):
                return dict((str(k), clean(v)) for k, v in o.items())
            if isinstance(o, (list, tuple)):
                return [clean(v) for v in o]
            return o
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump(clean(dict(name=a.name, base=a.base, drop=sorted(drop), inputs=inputs, arms=arms,
                                 results=dict((lbl, R) for lbl, R in results), runs=runs, tail_mismatch=mism)),
                      f, indent=1)
    R = results[0][1]
    print('%s (%s): %s' % (a.name, results[0][0], '; '.join(
        '%s n=%d med %s fps %s cpu %s%s' % (arm, x['n'], f_(x['median_ms'], 3), f_(x['fps'], 1), f_(x['cpu'], 3),
                                            (' paired %s' % ci_pct(x['vs_base']['median'])) if 'vs_base' in x else '')
        for arm, x in R['arms'].items())))
    if mism:
        print('perf.csv window MISMATCH: %s' % ', '.join(mism))
        return 3
    return 0


if __name__ == '__main__':
    sys.exit(main())

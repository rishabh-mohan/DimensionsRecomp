#!/usr/bin/env python3
"""Independent cross-check for Agent 8 (agy-grid task #20). Helper's own code: stdlib, scipy only for t quantiles.

Windows (folders under build/agent8/matrix/):
  W6  = 20261123-0009 (pass 1) + 20261123-0313 (pass 2), base s0
  W4c = 20261123-0239, base d0
  W9  = 20261123-0108 + 20261123-0401, base off
  W5b = 20261123-0155 + 20261123-0451, base d11
Reads results.csv (the statistics), runs/<run>/frames.json and run.json (transcription checks only) and
runs/<run>/perf.csv for every W6 run (window check and tail).
Writes only xcheck.md and xcheck.json next to this file.
"""
import bisect
import csv
import json
import math
import os
import statistics
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
MATRIX = os.path.join(ROOT, 'build', 'agent8', 'matrix')
OUT_MD = os.path.join(HERE, 'xcheck.md')
OUT_JSON = os.path.join(HERE, 'xcheck.json')

WINDOWS = [
    dict(name='W6', passes=['20261123-0009', '20261123-0313'], base='s0'),
    dict(name='W4c', passes=['20261123-0239'], base='d0'),
    dict(name='W9', passes=['20261123-0108', '20261123-0401'], base='off'),
    dict(name='W5b', passes=['20261123-0155', '20261123-0451'], base='d11'),
]
METRICS = [('median_ms', 'ms'), ('fps_mean', 'fps'), ('cpu_cores_mean', 'cores')]
THRESH = [('6', 6000), ('8', 8000), ('10', 10000), ('16.7', 16700), ('33', 33000)]
TAIL_WINDOW = 'W6'
ELEVATED_P999_MS = 6.0

try:
    from scipy.stats import t as _student_t

    def t975(df):
        return float(_student_t.ppf(0.975, df))
    T_SOURCE = 'scipy.stats.t.ppf(0.975, df)'
except Exception:  # pragma: no cover - fallback only
    _T975 = {1: 12.7062047, 2: 4.3026527, 3: 3.1824463, 4: 2.7764451, 5: 2.5705818, 6: 2.4469119, 7: 2.3646243,
             8: 2.3060041, 9: 2.2621572, 10: 2.2281389, 11: 2.2009852, 12: 2.1788128, 13: 2.1603687, 14: 2.1447867,
             15: 2.1314495, 16: 2.1199053, 17: 2.1098156, 18: 2.1009220, 19: 2.0930241, 20: 2.0859634}

    def t975(df):
        return _T975[df]
    T_SOURCE = 'Student t 0.975 table (scipy not available)'


# ---------------------------------------------------------------- helpers

def fnum(s):
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def inum(s):
    v = fnum(s)
    return int(round(v)) if v is not None else None


def load_json(path):
    try:
        with open(path, encoding='utf-8-sig') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def rank(s, num, den):
    """Nearest rank on an ascending list: s[ceil(num/den * n) - 1], in integer arithmetic."""
    n = len(s)
    k = (num * n + den - 1) // den
    return s[min(max(k, 1), n) - 1]


def mean(xs):
    return statistics.fmean(xs) if xs else None


def median(xs):
    return statistics.median(xs) if xs else None


def f3(v):
    if v is None:
        return 'n/a'
    if isinstance(v, bool):
        return 'yes' if v else 'no'
    if isinstance(v, int):
        return str(v)
    return '%.3f' % v


def s3(v):
    if v is None:
        return 'n/a'
    if isinstance(v, int) and not isinstance(v, bool):
        return '%+d' % v
    return '%+.3f' % v


def ci3(s):
    return 'n/a' if s.get('lo') is None else '[%+.3f, %+.3f]' % (s['lo'], s['hi'])


def round3(o):
    if isinstance(o, float):
        return round(o, 3) if math.isfinite(o) else None
    if isinstance(o, dict):
        return {str(k): round3(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [round3(v) for v in o]
    return o


TOL = {'r3': 0.0005, 'r4': 0.00005, 'r6': 0.0000005, 'us': 0.0000005}


def cmp(a, b, kind):
    """'ok' / 'MISMATCH' / 'n/a'. count: exact; us: same integer microsecond; rN: within half a unit of the N-th decimal."""
    if a is None or b is None:
        return 'n/a'
    if kind == 'count':
        return 'ok' if int(a) == int(b) else 'MISMATCH'
    return 'ok' if abs(float(a) - float(b)) <= TOL[kind] + 1e-9 else 'MISMATCH'


# ---------------------------------------------------------------- results.csv

def load_window(w):
    kept, left, odd = [], [], []
    for p, folder in enumerate(w['passes'], 1):
        with open(os.path.join(MATRIX, folder, 'results.csv'), newline='', encoding='utf-8-sig') as fh:
            rows = list(csv.DictReader(fh))
        for r in rows:
            name = r['run_dir'].replace('/', '\\').rstrip('\\').split('\\')[-1]
            rec = dict(window=w['name'], pass_=p, folder=folder, seq=int(r['seq']), round=int(r['round']), arm=r['arm'],
                       name=name, status=r['status'], scored=r['scored'], valid_timing=r['valid_timing'],
                       excluded=r['excluded'], flags_excluding=r['flags_excluding'], flags_info=r['flags_info'],
                       notes=r['notes'], frames=inum(r['frames']), window_s=fnum(r['window_s']),
                       median_ms=fnum(r['median_ms']), p99_ms=fnum(r['p99_ms']), p999_ms=fnum(r['p999_ms']),
                       max_ms=fnum(r['max_ms']), over33=inum(r['over33']), over100=inum(r['over100']),
                       fps_mean=fnum(r['fps_mean']), cpu_cores_mean=fnum(r['cpu_cores_mean']),
                       light_share=fnum(r['light_share']), run_path=os.path.join(MATRIX, folder, 'runs', name))
            rec['fps_recomputed'] = (rec['frames'] / rec['window_s']) if rec['frames'] and rec['window_s'] else None
            why = []
            if r['scored'] != 'True':
                why.append('scored=' + r['scored'])
            if r['valid_timing'] != 'True':
                why.append('valid_timing=' + r['valid_timing'])
            if r['excluded'] != 'False':
                why.append('excluded=' + r['excluded'])
            if why:
                rec['left_out'] = ', '.join(why)
                left.append(rec)
            else:
                kept.append(rec)
            if (r['status'] != 'OK' or r['flags_excluding'] or r['notes']
                    or r['flags_info'] not in ('', 'light_share_high')):
                odd.append(rec)
    return kept, left, odd


def arm_order(kept, base):
    order = [base]
    for r in sorted(kept, key=lambda x: (x['pass_'], x['seq'])):
        if r['arm'] not in order:
            order.append(r['arm'])
    return order


def arm_block(rows):
    if not rows:
        return None
    med = [r['median_ms'] for r in rows]
    fps = [r['fps_mean'] for r in rows]
    fre = [r['fps_recomputed'] for r in rows]
    cpu = [r['cpu_cores_mean'] for r in rows]
    return dict(n=len(rows), median_of_median_ms=median(med), mean_of_median_ms=mean(med),
                min_median_ms=min(med), max_median_ms=max(med),
                mean_fps=mean(fps), median_fps=median(fps), min_fps=min(fps), max_fps=max(fps),
                mean_fps_recomputed=mean(fre), median_fps_recomputed=median(fre),
                mean_cpu=mean(cpu), median_cpu=median(cpu), min_cpu=min(cpu), max_cpu=max(cpu),
                mean_frames=mean([r['frames'] for r in rows]),
                median_p99_ms=median([r['p99_ms'] for r in rows]), median_p999_ms=median([r['p999_ms'] for r in rows]),
                sum_over33=sum(r['over33'] for r in rows))


def deltas(a, b):
    if not a or not b:
        return None
    return dict(d_median_of_median_pct=100.0 * (a['median_of_median_ms'] / b['median_of_median_ms'] - 1.0),
                d_median_of_median_ms=a['median_of_median_ms'] - b['median_of_median_ms'],
                d_mean_fps_pct=100.0 * (a['mean_fps'] / b['mean_fps'] - 1.0),
                d_mean_fps=a['mean_fps'] - b['mean_fps'],
                d_mean_cpu_pct=100.0 * (a['mean_cpu'] / b['mean_cpu'] - 1.0),
                d_mean_cpu_cores=a['mean_cpu'] - b['mean_cpu'])


def summarize(vals):
    n = len(vals)
    if n == 0:
        return dict(n=0)
    m = mean(vals)
    out = dict(n=n, mean=m, median=median(vals), min=min(vals), max=max(vals), sd=None, df=n - 1, t975=None,
               hw95=None, lo=None, hi=None)
    if n > 1:
        sd = statistics.stdev(vals)
        t = t975(n - 1)
        hw = t * sd / math.sqrt(n)
        out.update(sd=sd, t975=t, hw95=hw, lo=m - hw, hi=m + hw)
    return out


def index_runs(rows):
    by, dup = {}, []
    for r in rows:
        key = (r['pass_'], r['round'], r['arm'])
        if key in by:
            dup.append(key)
        by[key] = r
    return by, dup


def paired(rows, arm, ref, metric, keep=None):
    by, dup = index_runs(rows)
    items, missing = [], []
    for (p, rd, a) in sorted(by):
        if a != arm or (keep is not None and not keep(p, rd)):
            continue
        b = by.get((p, rd, ref))
        if b is None:
            missing.append(dict(pass_=p, round=rd, run=by[(p, rd, a)]['name']))
            continue
        x, y = by[(p, rd, a)][metric], b[metric]
        items.append(dict(pass_=p, round=rd, arm_run=by[(p, rd, a)]['name'], ref_run=b['name'], arm=x, ref=y,
                          d=x - y, pct=100.0 * (x / y - 1.0)))
    for (p, rd, a) in sorted(by):
        if a == ref and (keep is None or keep(p, rd)) and (p, rd, arm) not in by:
            missing.append(dict(pass_=p, round=rd, run=by[(p, rd, a)]['name']))
    d = [it['d'] for it in items]
    pct = [it['pct'] for it in items]
    summ = dict(n=len(items), neg=sum(1 for v in d if v < 0), pos=sum(1 for v in d if v > 0),
                zero=sum(1 for v in d if v == 0), abs=summarize(d), pct=summarize(pct),
                mean_d_over_mean_ref_pct=(100.0 * mean(d) / mean([it['ref'] for it in items])) if items else None)
    return dict(items=items, missing=missing, duplicates=dup, summary=summ)


# ---------------------------------------------------------------- transcription checks (every run)

FJ_CHECKS = [  # (results.csv field, frames.json key, kind)
    ('frames', 'frames', 'count'), ('window_s', 'window_s', 'r3'), ('fps_mean', 'mean_fps', 'r3'),
    ('median_ms', 'median_ms', 'r3'), ('p99_ms', 'p99_ms', 'r3'), ('p999_ms', 'p99_9_ms', 'r3'),
    ('max_ms', 'max_ms', 'r3'), ('over33', 'over_33ms', 'count'), ('over100', 'over_100ms', 'count'),
    ('light_share', 'share_lt_light', 'r3'),
]


def transcription_checks(rec):
    out = []
    fj = load_json(os.path.join(rec['run_path'], 'frames.json'))
    rj = load_json(os.path.join(rec['run_path'], 'run.json'))
    if fj is None:
        out.append(dict(run=rec['name'], item='frames.json', source='frames.json', results=None, other=None,
                        result='MISSING'))
    else:
        for rk, fk, kind in FJ_CHECKS:
            out.append(dict(run=rec['name'], item=rk, source='frames.json ' + fk, results=rec[rk], other=fj.get(fk),
                            result=cmp(rec[rk], fj.get(fk), kind)))
    cpu = rj.get('window_cpu_cores_mean') if rj else None
    out.append(dict(run=rec['name'], item='cpu_cores_mean', source='run.json window_cpu_cores_mean',
                    results=rec['cpu_cores_mean'], other=cpu, result=cmp(rec['cpu_cores_mean'], cpu, 'r3')))
    fre = rec['fps_recomputed']
    if fre is None or rec['fps_mean'] is None:
        res = 'n/a'
    else:
        tol = fre * 0.0005 / rec['window_s'] + 0.0005
        res = 'ok' if abs(rec['fps_mean'] - fre) <= tol + 1e-9 else 'MISMATCH'
    out.append(dict(run=rec['name'], item='fps_mean', source='frames / window_s (results.csv, window_s rounded)',
                    results=rec['fps_mean'], other=fre, result=res))
    return out


# ---------------------------------------------------------------- perf.csv (W6)

def read_perf(path):
    """Returns (rows [(end_offset, frame_time_us)], bad_rows, partial_tail, file_bytes, header)."""
    with open(path, 'rb') as fh:
        data = fh.read()
    parts = data.split(b'\n')
    header = [h.strip() for h in parts[0].rstrip(b'\r').decode('ascii', 'replace').split(',')]
    width = len(header)
    ci = header.index('frame_time_us')
    off = len(parts[0]) + 1
    rows, bad = [], 0
    for ln in parts[1:-1]:  # parts[-1] = bytes after the last newline (b'' when the file ends with one)
        off += len(ln) + 1
        fld = ln.rstrip(b'\r').split(b',')
        if len(fld) != width:
            bad += 1
            continue
        try:
            iv = [int(x) for x in fld]
        except ValueError:
            bad += 1
            continue
        rows.append((off, iv[ci]))
    return rows, bad, len(parts[-1]) > 0, len(data), header


def perf_window(rec):
    run = rec['run_path']
    fj = load_json(os.path.join(run, 'frames.json'))
    rj = load_json(os.path.join(run, 'run.json'))
    rows, bad, partial, nbytes, header = read_perf(os.path.join(run, 'perf.csv'))
    w = fj['window']
    first, nrows = int(w['first_row']), int(w['rows'])
    win = rows[first:first + nrows]
    s = sorted(v for _, v in win if v > 0)
    m = len(s)
    tot = sum(s)
    win_s = tot / 1e6
    # own window from run.json's start offset and seconds (independent of first_row / rows)
    start_b = rj['measure_start']['perf_csv_bytes']
    secs = float(rj['params']['seconds'])
    f2 = 0
    while f2 < len(rows) and rows[f2][0] <= start_b:
        f2 += 1
    acc, n2 = 0, 0
    for _, v in rows[f2:]:
        if acc >= secs * 1e6:
            break
        acc += v if v > 0 else 0
        n2 += 1
    light_us = float(fj.get('light_ms', 4.5)) * 1000.0
    st = dict(rows_total=len(rows), bad_rows=bad, partial_tail=partial, first_row=first, rows=nrows,
              own_first_row=f2, own_rows=n2, start_bytes=start_b,
              first_row_end_offset=win[0][0] if win else None, last_row_end_offset=win[-1][0] if win else None,
              zero_rows=nrows - m, frames=m, window_s=win_s, mean_fps=m / win_s, mean_ms=tot / m / 1000.0,
              median_ms=rank(s, 1, 2) / 1000.0, p95_ms=rank(s, 95, 100) / 1000.0, p99_ms=rank(s, 99, 100) / 1000.0,
              p999_ms=rank(s, 999, 1000) / 1000.0, min_ms=s[0] / 1000.0, max_ms=s[-1] / 1000.0,
              over33=m - bisect.bisect_right(s, 33000), over100=m - bisect.bisect_right(s, 100000),
              share_lt_light=bisect.bisect_left(s, light_us) / m if light_us == int(light_us) else
              sum(1 for v in s if v < light_us) / m)
    st['counts'] = {k: m - bisect.bisect_right(s, us) for k, us in THRESH}
    st['rates_per_min'] = {k: c / win_s * 60.0 for k, c in st['counts'].items()}

    checks = []

    def add(item, mine, theirs, kind, src):
        checks.append(dict(run=rec['name'], item=item, source=src, mine=mine, theirs=theirs,
                           result=cmp(mine, theirs, kind)))
    add('rows_total', st['rows_total'], fj.get('rows_total'), 'count', 'frames.json')
    add('bad_rows', bad, fj.get('bad_rows'), 'count', 'frames.json')
    add('start_bytes', start_b, w.get('start_bytes'), 'count', 'frames.json window (mine = run.json measure_start)')
    add('first_row', f2, first, 'count', 'frames.json window (mine = first row ending past start_bytes)')
    add('rows', n2, nrows, 'count', 'frames.json window (mine = rows until the frame-time sum reaches seconds)')
    add('first_row_end_offset', st['first_row_end_offset'], w.get('first_row_end_offset'), 'count', 'frames.json window')
    add('last_row_end_offset', st['last_row_end_offset'], w.get('last_row_end_offset'), 'count', 'frames.json window')
    add('zero_rows', st['zero_rows'], w.get('zero_rows'), 'count', 'frames.json window')
    add('frames', m, fj.get('frames'), 'count', 'frames.json')
    add('window_s', win_s, fj.get('window_s'), 'r6', 'frames.json')
    add('mean_fps', st['mean_fps'], fj.get('mean_fps'), 'r3', 'frames.json')
    add('mean_ms', st['mean_ms'], fj.get('mean_ms'), 'r4', 'frames.json')
    for k, fk in (('median_ms', 'median_ms'), ('p95_ms', 'p95_ms'), ('p99_ms', 'p99_ms'), ('p999_ms', 'p99_9_ms'),
                  ('min_ms', 'min_ms'), ('max_ms', 'max_ms')):
        add(k, st[k], fj.get(fk), 'us', 'frames.json ' + fk)
    add('over33', st['over33'], fj.get('over_33ms'), 'count', 'frames.json over_33ms')
    add('over100', st['over100'], fj.get('over_100ms'), 'count', 'frames.json over_100ms')
    add('share_lt_light', st['share_lt_light'], fj.get('share_lt_light'), 'r4', 'frames.json')
    add('frames', m, rec['frames'], 'count', 'results.csv')
    add('window_s', win_s, rec['window_s'], 'r3', 'results.csv')
    add('fps_mean', st['mean_fps'], rec['fps_mean'], 'r3', 'results.csv')
    for k in ('median_ms', 'p99_ms', 'p999_ms', 'max_ms'):
        add(k, st[k], rec[k], 'us', 'results.csv')
    add('over33', st['over33'], rec['over33'], 'count', 'results.csv')
    add('over100', st['over100'], rec['over100'], 'count', 'results.csv')
    return st, checks, s


def tail_block(runs, sorted_frames):
    out = dict(n=len(runs), runs=[r['name'] for r in runs])
    for k, _ in THRESH:
        rates = [r['tail']['rates_per_min'][k] for r in runs]
        cnts = [r['tail']['counts'][k] for r in runs]
        out['gt' + k] = dict(median_rate_per_min=median(rates), mean_rate_per_min=mean(rates), sum_count=sum(cnts),
                             runs_with_any=sum(1 for c in cnts if c > 0), counts=cnts, rates_per_min=rates)
    out['p999_ms_per_run'] = [r['tail']['p999_ms'] for r in runs]
    out['median_p999_ms'] = median(out['p999_ms_per_run'])
    out['median_p99_ms'] = median([r['tail']['p99_ms'] for r in runs])
    pooled = sorted(v for r in runs for v in sorted_frames[(r['pass_'], r['name'])])
    out['pooled_frames'] = len(pooled)
    out['pooled_p999_ms'] = rank(pooled, 999, 1000) / 1000.0 if pooled else None
    out['runs_p999_gt_%s' % ELEVATED_P999_MS] = sum(1 for v in out['p999_ms_per_run'] if v > ELEVATED_P999_MS)
    return out


# ---------------------------------------------------------------- main

def main():
    t_start = time.time()
    J = dict(meta=dict(script=os.path.relpath(__file__, ROOT), generated=time.strftime('%Y-%m-%d %H:%M:%S'),
                       t_source=T_SOURCE, windows=WINDOWS,
                       filter='results.csv scored=True, valid_timing=True, excluded=False'),
             windows={}, transcription=None, w6_c1=None, w6_tail=None)
    all_checks = []
    W = {}
    for w in WINDOWS:
        kept, left, odd = load_window(w)
        order = arm_order(kept, w['base'])
        base = w['base']
        npass = len(w['passes'])
        by, dup = index_runs(kept)
        for r in kept + left:
            all_checks.extend(dict(window=w['name'], **c) for c in transcription_checks(r))
        sets = [('pooled', lambda r: True)] + [('pass %d' % p, (lambda p: (lambda r: r['pass_'] == p))(p))
                                               for p in range(1, npass + 1)] if npass > 1 else [('all', lambda r: True)]
        stats, dl = {}, {}
        for sname, f in sets:
            stats[sname] = {a: arm_block([r for r in kept if r['arm'] == a and f(r)]) for a in order}
            dl[sname] = {a: deltas(stats[sname][a], stats[sname][base]) for a in order if a != base}
        pr = {a: {m: paired(kept, a, base, m) for m, _ in METRICS} for a in order if a != base}
        pr_pass = {}
        if npass > 1:
            for p in range(1, npass + 1):
                pr_pass['pass %d' % p] = {a: {m: paired(kept, a, base, m, keep=(lambda p: (lambda pp, rd: pp == p))(p))
                                              for m, _ in METRICS} for a in order if a != base}
        # sensitivity: without round 1
        kept_nr1 = [r for r in kept if r['round'] != 1]
        st_nr1 = {a: arm_block([r for r in kept_nr1 if r['arm'] == a]) for a in order}
        dl_nr1 = {a: deltas(st_nr1[a], st_nr1[base]) for a in order if a != base}
        pr_nr1 = {a: {m: paired(kept, a, base, m, keep=lambda pp, rd: rd != 1) for m, _ in METRICS}
                  for a in order if a != base}
        # first scored run of each pass
        first_runs = []
        for p in range(1, npass + 1):
            pk = sorted([r for r in kept if r['pass_'] == p], key=lambda x: x['seq'])
            if not pk:
                continue
            f0 = pk[0]
            others = [r for r in pk[1:] if r['arm'] == f0['arm']]
            cold = [r for r in left if r['pass_'] == p]
            first_runs.append(dict(pass_=p, run=f0['name'], arm=f0['arm'], round=f0['round'], fps=f0['fps_mean'],
                                   median_ms=f0['median_ms'], cpu=f0['cpu_cores_mean'],
                                   others_n=len(others), others_median_fps=median([r['fps_mean'] for r in others]),
                                   others_median_ms=median([r['median_ms'] for r in others]),
                                   fps_above_others_pct=(100.0 * (f0['fps_mean'] / median([r['fps_mean'] for r in others]) - 1.0)) if others else None,
                                   arm_fps_rank=1 + sum(1 for r in pk if r['arm'] == f0['arm'] and r['fps_mean'] > f0['fps_mean']),
                                   cold_run=cold[0]['name'] if cold else None, cold_fps=cold[0]['fps_mean'] if cold else None))
        W[w['name']] = dict(w=w, kept=kept, left=left, odd=odd, order=order, dup=dup, stats=stats, deltas=dl,
                            paired=pr, paired_pass=pr_pass, stats_nr1=st_nr1, deltas_nr1=dl_nr1, paired_nr1=pr_nr1,
                            first_runs=first_runs, sets=[s for s, _ in sets])
        J['windows'][w['name']] = dict(
            passes=w['passes'], base=base, arms=order,
            rows_used=len(kept), rows_left_out=[dict(pass_=r['pass_'], seq=r['seq'], run=r['name'], arm=r['arm'],
                                                     reason=r['left_out']) for r in left],
            rows_flagged=[dict(pass_=r['pass_'], run=r['name'], status=r['status'], flags_excluding=r['flags_excluding'],
                               flags_info=r['flags_info'], notes=r['notes']) for r in odd],
            duplicate_keys=dup,
            runs=[dict(pass_=r['pass_'], seq=r['seq'], round=r['round'], arm=r['arm'], run=r['name'], frames=r['frames'],
                       window_s=r['window_s'], fps_mean=r['fps_mean'], fps_recomputed=r['fps_recomputed'],
                       median_ms=r['median_ms'], p99_ms=r['p99_ms'], p999_ms=r['p999_ms'], max_ms=r['max_ms'],
                       over33=r['over33'], cpu_cores_mean=r['cpu_cores_mean']) for r in kept],
            per_arm=stats, vs_base=dl, paired=pr, paired_by_pass=pr_pass,
            without_round1=dict(per_arm=st_nr1, vs_base=dl_nr1, paired=pr_nr1),
            first_scored_run_of_each_pass=first_runs)

    # transcription summary
    tr_mis = [c for c in all_checks if c['result'] != 'ok']
    J['transcription'] = dict(items=len(all_checks), ok=sum(1 for c in all_checks if c['result'] == 'ok'),
                              not_ok=tr_mis,
                              by_item={it: sum(1 for c in all_checks if c['item'] == it and c['result'] == 'ok')
                                       for it in sorted(set(c['item'] for c in all_checks))})

    # W6 C1
    w6 = W['W6']
    c1 = {m: paired(w6['kept'], 'p2fc', 'p2f', m) for m, _ in METRICS}
    J['w6_c1'] = dict(definition='p2fc - p2f, same pass and round', median_ms=c1['median_ms'],
                      fps_mean=c1['fps_mean'], cpu_cores_mean=c1['cpu_cores_mean'])

    # W6 tail
    tail_checks, sorted_frames, tail_runs = [], {}, []
    for r in sorted(w6['kept'] + w6['left'], key=lambda x: (x['pass_'], x['seq'])):
        st, ch, s = perf_window(r)
        r['tail'] = st
        tail_checks.extend(ch)
        sorted_frames[(r['pass_'], r['name'])] = s
        tail_runs.append(r)
    kept6 = [r for r in tail_runs if 'left_out' not in r]
    tblocks = {}
    for a in w6['order']:
        tblocks[a] = {}
        for sname, f in (('pass 1', lambda r: r['pass_'] == 1), ('pass 2', lambda r: r['pass_'] == 2),
                         ('pooled', lambda r: True)):
            rr = [r for r in kept6 if r['arm'] == a and f(r)]
            tblocks[a][sname] = tail_block(rr, sorted_frames)
    tc_bad = [c for c in tail_checks if c['result'] != 'ok']
    req = ('median_ms', 'p99_ms', 'p999_ms', 'max_ms', 'over33')
    req_fj = [c for c in tail_checks if c['source'].startswith('frames.json') and c['item'] in req]
    J['w6_tail'] = dict(
        window_rule='frames.json window.first_row (0-based index among perf.csv data rows) and window.rows; '
                    'frames = rows with frame_time_us > 0; nearest rank sorted[ceil(p*n)-1]',
        thresholds_ms=[k for k, _ in THRESH], rate='count / window_s * 60 (window_s = sum of the window frame times)',
        checks=dict(runs=len(tail_runs), items=len(tail_checks), ok=len(tail_checks) - len(tc_bad), not_ok=tc_bad,
                    required_five_vs_frames_json=dict(items=len(req_fj),
                                                      exact=sum(1 for c in req_fj if c['result'] == 'ok'))),
        runs=[dict(pass_=r['pass_'], seq=r['seq'], round=r['round'], arm=r['arm'], run=r['name'],
                   scored='left_out' not in r, **{k: v for k, v in r['tail'].items()}) for r in tail_runs],
        per_arm=tblocks)

    # ------------------------------------------------------------ markdown
    L = []
    a_ = L.append
    a_('# W6 / W4c / W9 / W5b cross-check (helper of Agent 8, task #20)')
    a_('')
    a_('Generated %s by xcheck_w.py in this folder (own code; stdlib, %s). Inputs (read only): build/agent8/matrix/'
       '<folder>/results.csv for the statistics; runs/<run>/frames.json and run.json for transcription checks; '
       'runs/<run>/perf.csv for every W6 run (task 4). Outputs: xcheck.md, xcheck.json (all values rounded to 3 '
       'decimals).' % (J['meta']['generated'], T_SOURCE))
    a_('')
    a_('Windows: ' + '; '.join('%s = %s, base %s' % (w['name'], ' + '.join(w['passes']), w['base']) for w in WINDOWS)
       + '. Pass k = the k-th folder.')
    a_('')

    # readings
    a_('## Readings (facts)')
    a_('')
    lo = [r for n in W for r in W[n]['left']]
    all_rows = [r for n in W for r in W[n]['kept'] + W[n]['left']]
    ls_high = sum(1 for r in all_rows if r['flags_info'] == 'light_share_high')
    a_('- **Rows used:** results.csv rows with scored=True, valid_timing=True and excluded=False: '
       + ', '.join('%s %d' % (n, len(W[n]['kept'])) for n in W) + '. Left out: %d rows, %s: %s. '
       'No row has a status other than OK, flags_excluding or notes; flags_info is light_share_high in %d of %d rows '
       '(info only).' % (len(lo), 'all with scored=False (the cold runs)' if all(r['left_out'] == 'scored=False'
                                                                               for r in lo) else 'see the lists',
                        ', '.join(r['name'] for r in lo), ls_high, len(all_rows))
       if not any(W[n]['odd'] for n in W) else '- **Rows used:** see the per-window lists (some rows carry flags).')
    a_('- **Transcription:** results.csv agrees with frames.json and run.json in %d of %d items over every run of the '
       '7 folders (frames, window_s, fps_mean, median, p99, p99.9, max, >33, >100, light share; cpu_cores_mean vs '
       'run.json window_cpu_cores_mean; fps_mean vs frames / window_s).' % (J['transcription']['ok'],
                                                                           J['transcription']['items']))
    a_('- **W6 window check:** %d runs (%s scored and %d cold), %d items, %d ok. The five required '
       'statistics (median, p99, p99.9, max, >33 ms) reproduce frames.json exactly in %d of %d. My own window bounds '
       '(first row ending past run.json measure_start.perf_csv_bytes, rows until the frame-time sum reaches 50 s / 30 s) '
       'equal frames.json first_row and rows in every run.' % (
           len(tail_runs), ' + '.join(str(sum(1 for r in kept6 if r['pass_'] == p)) for p in (1, 2)),
           len(tail_runs) - len(kept6), len(tail_checks), len(tail_checks) - len(tc_bad),
           J['w6_tail']['checks']['required_five_vs_frames_json']['exact'],
           J['w6_tail']['checks']['required_five_vs_frames_json']['items'])
       if not [c for c in tc_bad if c['item'] in ('first_row', 'rows')] else
       '- **W6 window check:** see the window-check section (bound mismatches).')
    c1s = c1['median_ms']['summary']
    a_('- **W6 C1 (p2fc - p2f, median ms), 10 rounds:** %s; negative in %d of %d (mean %s ms, 95 %% CI %s).' % (
        ', '.join(s3(it['d']) for it in c1['median_ms']['items']), c1s['neg'], c1s['n'], s3(c1s['abs']['mean']),
        ci3(c1s['abs'])))
    p2 = tblocks
    a_('- **W6 pass-2 p99.9 (median of runs):** p2fc %s, p2f %s, s0 %s, p2 %s ms. Runs above %.1f ms: p2fc %d/5, '
       'p2f %d/5, s0 %d/5, p2 %d/5 (details in the tail section).' % (
           f3(p2['p2fc']['pass 2']['median_p999_ms']), f3(p2['p2f']['pass 2']['median_p999_ms']),
           f3(p2['s0']['pass 2']['median_p999_ms']), f3(p2['p2']['pass 2']['median_p999_ms']), ELEVATED_P999_MS,
           p2['p2fc']['pass 2']['runs_p999_gt_%s' % ELEVATED_P999_MS], p2['p2f']['pass 2']['runs_p999_gt_%s' % ELEVATED_P999_MS],
           p2['s0']['pass 2']['runs_p999_gt_%s' % ELEVATED_P999_MS], p2['p2']['pass 2']['runs_p999_gt_%s' % ELEVATED_P999_MS]))
    fr_all = [(n, fr) for n in W for fr in W[n]['first_runs']]
    a_('- **First scored run of each pass** (always the base arm, round 1): ' + '; '.join(
        '%s p%d %s %s fps (%s %% vs the median of the arm\'s other %d runs in the pass)' % (
            n, fr['pass_'], fr['run'], f3(fr['fps']), s3(fr['fps_above_others_pct']), fr['others_n'])
        for n, fr in fr_all) + '.')
    a_('')

    # definitions
    a_('## Definitions')
    a_('')
    a_('- **Rows:** results.csv rows with scored=True, valid_timing=True, excluded=False. Round = results.csv round; '
       'pass = folder (pass 1 = first folder).')
    a_('- **Per arm:** n; median and mean of median_ms; mean and median of fps_mean (the results.csv column, which is '
       'frames / window_s with the unrounded window; recomputing frames / window_s from the 3-dp window_s agrees within '
       'its rounding); mean and median of cpu_cores_mean; mean frames; median of p99_ms and of p999_ms; sum of over33. '
       'Pooled = all used rows of the arm over both passes.')
    a_('- **Vs base:** 100 (arm / base - 1) of the pooled median of median_ms, of the mean fps_mean and of the mean '
       'cpu_cores_mean; CPU delta in cores = mean arm - mean base.')
    a_('- **Paired:** for each (pass, round) that has one run of the arm and one of the base: d = arm - base and '
       'pct = 100 (arm / base - 1). Counts of d < 0, d > 0 and d = 0; mean d and mean pct with 95 %% CI = mean +- '
       't975(df) sd / sqrt(n), df = pairs - 1, sd with n - 1 (%s). xcheck.json also has mean d / mean base (alt %%).'
       % T_SOURCE)
    a_('- **W6 C1:** p2fc - p2f per (pass, round), as in SESSION2 L3226/L3271 (median_ms; fps and CPU are added).')
    a_('- **W6 tail:** window = frames.json window.first_row (0-based index among the perf.csv data rows that have the '
       'header\'s field count and integer fields) and window.rows rows; frames = rows with frame_time_us > 0; '
       'window_s = their sum / 1e6. Nearest rank sorted[ceil(p n) - 1]. Counts are frames with frame_time_us > '
       '6000 / 8000 / 10000 / 16700 / 33000 us (strict, like over_33ms); rate = count / window_s x 60. Per arm and '
       'pass: the median of the per-run rates, the median of the per-run p99.9 and (extra) the p99.9 of the pooled '
       'frames.')
    a_('- **Tolerances (checks):** counts exact; ms statistics from perf.csv equal to the microsecond; values printed '
       'with 3 decimals within 0.0005 (4 decimals: 0.00005; window_s in frames.json: 5e-7).')
    a_('')

    # per window
    for n in W:
        X = W[n]
        w = X['w']
        base = w['base']
        a_('## %s (base %s; %s)' % (n, base, ' + '.join(w['passes'])))
        a_('')
        a_('Used %d rows; left out: %s.' % (len(X['kept']), ', '.join('%s (%s)' % (r['name'], r['left_out'])
                                                                    for r in X['left']) or 'none'))
        if X['dup']:
            a_('Duplicate (pass, round, arm) keys: %s.' % X['dup'])
        a_('')
        a_('### Per arm')
        a_('')
        a_('| arm | set | n | median of median_ms | mean median_ms | mean fps | median fps | mean CPU | median CPU '
           '| mean frames | median p99 ms | median p99.9 ms | sum >33 |')
        a_('|---|---|---|---|---|---|---|---|---|---|---|---|---|')
        for a in X['order']:
            for sname in X['sets']:
                b = X['stats'][sname][a]
                if not b:
                    continue
                a_('| %s | %s | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %d |' % (
                    a, sname, b['n'], f3(b['median_of_median_ms']), f3(b['mean_of_median_ms']), f3(b['mean_fps']),
                    f3(b['median_fps']), f3(b['mean_cpu']), f3(b['median_cpu']), f3(b['mean_frames']),
                    f3(b['median_p99_ms']), f3(b['median_p999_ms']), b['sum_over33']))
        a_('')
        a_('### Vs base (%s)' % base)
        a_('')
        a_('| arm | set | delta median-of-medians % | delta mean fps % | delta mean CPU % | delta mean CPU cores |')
        a_('|---|---|---|---|---|---|')
        for a in X['order']:
            if a == base:
                continue
            for sname in X['sets']:
                d = X['deltas'][sname][a]
                if d:
                    a_('| %s | %s | %s | %s | %s | %s |' % (a, sname, s3(d['d_median_of_median_pct']),
                                                          s3(d['d_mean_fps_pct']), s3(d['d_mean_cpu_pct']),
                                                          s3(d['d_mean_cpu_cores'])))
        a_('')
        a_('### Paired per round (arm - %s, same pass and round)' % base)
        a_('')
        a_('| arm | metric | pairs | neg / pos / 0 | mean d | 95 % CI d | mean % | 95 % CI % | per-round d |')
        a_('|---|---|---|---|---|---|---|---|---|')
        for a in X['order']:
            if a == base:
                continue
            for m, unit in METRICS:
                P = X['paired'][a][m]
                S = P['summary']
                per = '; '.join('p%d: %s' % (p, ' '.join(s3(it['d']) for it in P['items'] if it['pass_'] == p))
                                for p in sorted(set(it['pass_'] for it in P['items'])))
                a_('| %s | %s (%s) | %d | %d / %d / %d | %s | %s | %s | %s | %s |' % (
                    a, m, unit, S['n'], S['neg'], S['pos'], S['zero'], s3(S['abs']['mean']), ci3(S['abs']),
                    s3(S['pct']['mean']), ci3(S['pct']), per))
                if P['missing']:
                    a_('|  | missing pairs: %s |  |  |  |  |  |  |  |' % P['missing'])
        a_('')
        if X['paired_pass']:
            a_('Paired by pass (mean d [95 % CI], neg/pos):')
            a_('')
            a_('| arm | metric | ' + ' | '.join(X['paired_pass']) + ' |')
            a_('|---|---|' + '---|' * len(X['paired_pass']))
            for a in X['order']:
                if a == base:
                    continue
                for m, unit in METRICS:
                    cells = []
                    for pn in X['paired_pass']:
                        S = X['paired_pass'][pn][a][m]['summary']
                        cells.append('%s %s, %d/%d' % (s3(S['abs']['mean']), ci3(S['abs']), S['neg'], S['pos']))
                    a_('| %s | %s | %s |' % (a, m, ' | '.join(cells)))
            a_('')
        a_('### Sensitivity: without round 1 (the first scored run of each pass is the base arm\'s round-1 run)')
        a_('')
        a_('| arm | n arm / base | delta median-of-medians % | delta mean fps % | delta mean CPU cores | paired median_ms '
           'mean d [CI] neg/pos | paired fps mean d [CI] neg/pos | paired CPU mean d [CI] neg/pos |')
        a_('|---|---|---|---|---|---|---|---|')
        for a in X['order']:
            if a == base:
                continue
            d = X['deltas_nr1'][a]
            cells = []
            for m, _ in METRICS:
                S = X['paired_nr1'][a][m]['summary']
                cells.append('%s %s %d/%d' % (s3(S['abs']['mean']), ci3(S['abs']), S['neg'], S['pos']))
            a_('| %s | %d / %d | %s | %s | %s | %s |' % (a, X['stats_nr1'][a]['n'], X['stats_nr1'][base]['n'],
                                                     s3(d['d_median_of_median_pct']), s3(d['d_mean_fps_pct']),
                                                     s3(d['d_mean_cpu_cores']), ' | '.join(cells)))
        a_('')

    # C1
    a_('## W6 C1 = p2fc - p2f per round (all 10 rounds)')
    a_('')
    a_('| pass | round | p2fc run | p2f run | p2fc median_ms | p2f median_ms | C1 median_ms | C1 fps | C1 CPU cores |')
    a_('|---|---|---|---|---|---|---|---|---|')
    for it, itf, itc in zip(c1['median_ms']['items'], c1['fps_mean']['items'], c1['cpu_cores_mean']['items']):
        a_('| %d | %d | %s | %s | %s | %s | %s | %s | %s |' % (it['pass_'], it['round'], it['arm_run'], it['ref_run'],
                                                         f3(it['arm']), f3(it['ref']), s3(it['d']), s3(itf['d']),
                                                         s3(itc['d'])))
    for m, unit in METRICS:
        S = c1[m]['summary']
        a_('')
        a_('- %s: negative %d of %d, positive %d, zero %d; mean %s %s, 95 %% CI %s; mean %s %%, 95 %% CI %s.' % (
            m, S['neg'], S['n'], S['pos'], S['zero'], s3(S['abs']['mean']), unit, ci3(S['abs']), s3(S['pct']['mean']),
            ci3(S['pct'])))
    a_('')

    # tail
    a_('## W6 tail (perf.csv scored windows)')
    a_('')
    a_('### Window check')
    a_('')
    a_('%d runs, %d check items, %d ok, %d not ok. Items per run: rows_total, bad_rows, start_bytes (run.json), my own '
       'first_row and rows (from start_bytes and the window seconds), first/last row end offsets, zero_rows, frames, '
       'window_s, mean fps, mean ms, median, p95, p99, p99.9, min, max, >33, >100, light share (vs frames.json); frames, '
       'window_s, fps_mean, median, p99, p99.9, max, >33, >100 (vs results.csv).' % (
           len(tail_runs), len(tail_checks), len(tail_checks) - len(tc_bad), len(tc_bad)))
    if tc_bad:
        a_('')
        for c in tc_bad:
            a_('- %s %s (%s): mine %s, theirs %s -> %s' % (c['run'], c['item'], c['source'], c['mine'], c['theirs'],
                                                            c['result']))
    a_('')
    a_('### Per run')
    a_('')
    a_('| pass | seq | run | first_row | rows | frames | window_s | median | p99 | p99.9 | max | >6 | >8 | >10 | >16.7 '
       '| >33 | /min >6 | /min >8 | /min >10 | /min >16.7 | /min >33 |')
    a_('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    for r in tail_runs:
        t = r['tail']
        a_('| %d | %d | %s%s | %d | %d | %d | %s | %s | %s | %s | %s | %s | %s |' % (
            r['pass_'], r['seq'], r['name'], ' (cold, unscored)' if 'left_out' in r else '', t['first_row'], t['rows'],
            t['frames'], f3(t['window_s']), f3(t['median_ms']), f3(t['p99_ms']), f3(t['p999_ms']), f3(t['max_ms']),
            ' | '.join(str(t['counts'][k]) for k, _ in THRESH), ' | '.join(f3(t['rates_per_min'][k]) for k, _ in THRESH)))
    a_('')
    a_('### Per arm and pass (scored runs)')
    a_('')
    a_('| arm | set | n | median p99 | median p99.9 | pooled-frames p99.9 | runs p99.9 > %.1f | median /min >6 | >8 | >10 '
       '| >16.7 | >33 | runs with any >6 / >8 / >10 / >16.7 / >33 | sum >6 / >8 / >10 / >16.7 / >33 |' % ELEVATED_P999_MS)
    a_('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    for a in w6['order']:
        for sname in ('pass 1', 'pass 2', 'pooled'):
            B = tblocks[a][sname]
            a_('| %s | %s | %d | %s | %s | %s | %d | %s | %s | %s |' % (
                a, sname, B['n'], f3(B['median_p99_ms']), f3(B['median_p999_ms']), f3(B['pooled_p999_ms']),
                B['runs_p999_gt_%s' % ELEVATED_P999_MS],
                ' | '.join(f3(B['gt' + k]['median_rate_per_min']) for k, _ in THRESH),
                ' / '.join(str(B['gt' + k]['runs_with_any']) for k, _ in THRESH),
                ' / '.join(str(B['gt' + k]['sum_count']) for k, _ in THRESH)))
    a_('')
    a_('### Few runs or all? (pass 2, per run in round order)')
    a_('')
    a_('| arm | runs (round: p99.9 ms, >6 ms frames per min, >8, >10) | median p99.9 |')
    a_('|---|---|---|')
    for a in w6['order']:
        rr = sorted([r for r in kept6 if r['arm'] == a and r['pass_'] == 2], key=lambda x: x['round'])
        a_('| %s | %s | %s |' % (a, '; '.join('r%d: %s, %s, %s, %s' % (
            r['round'], f3(r['tail']['p999_ms']), f3(r['tail']['rates_per_min']['6']),
            f3(r['tail']['rates_per_min']['8']), f3(r['tail']['rates_per_min']['10'])) for r in rr),
            f3(tblocks[a]['pass 2']['median_p999_ms'])))
    a_('')
    for p in (2, 1):
        a_('Pass %d in run order (seq: run, p99.9 ms, >6 / >8 / >10 / >16.7 / >33 ms counts):' % p)
        a_('')
        a_('| seq | run | p99.9 | >6 | >8 | >10 | >16.7 | >33 | /min >6 |')
        a_('|---|---|---|---|---|---|---|---|---|')
        for r in [x for x in tail_runs if x['pass_'] == p]:
            t = r['tail']
            a_('| %d | %s%s | %s | %s | %s |' % (r['seq'], r['name'], ' (cold)' if 'left_out' in r else '',
                                              f3(t['p999_ms']), ' | '.join(str(t['counts'][k]) for k, _ in THRESH),
                                              f3(t['rates_per_min']['6'])))
        a_('')

    # oddities
    a_('## First scored run of each pass')
    a_('')
    a_('| window | pass | first scored run | fps | median ms | CPU | arm\'s other runs in the pass: n, median fps, median ms '
       '| fps vs them % | fps rank within the arm and pass | cold run fps |')
    a_('|---|---|---|---|---|---|---|---|---|---|')
    for n, fr in fr_all:
        a_('| %s | %d | %s | %s | %s | %s | %d, %s, %s | %s | %d | %s %s |' % (
            n, fr['pass_'], fr['run'], f3(fr['fps']), f3(fr['median_ms']), f3(fr['cpu']), fr['others_n'],
            f3(fr['others_median_fps']), f3(fr['others_median_ms']), s3(fr['fps_above_others_pct']), fr['arm_fps_rank'],
            fr['cold_run'], f3(fr['cold_fps'])))
    a_('')
    if tr_mis:
        a_('## Transcription items not ok')
        a_('')
        for c in tr_mis:
            a_('- %s %s %s (%s): results.csv %s, other %s -> %s' % (c['window'], c['run'], c['item'], c['source'],
                                                                     c['results'], c['other'], c['result']))
        a_('')

    for i in range(1, len(L)):  # separator rows get one '---' per header column
        if L[i].startswith('|---') and set(L[i]) <= set('|-'):
            L[i] = '|' + '---|' * (L[i - 1].count('|') - 1)
    with open(OUT_MD, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(L) + '\n')
    with open(OUT_JSON, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(round3(J), fh, indent=1)

    # ------------------------------------------------------------ stdout digest
    print('transcription: %d/%d ok' % (J['transcription']['ok'], J['transcription']['items']))
    for c in tr_mis[:20]:
        print('  TR', c['window'], c['run'], c['item'], c['results'], c['other'], c['result'])
    print('w6 window checks: %d runs, %d items, %d not ok' % (len(tail_runs), len(tail_checks), len(tc_bad)))
    for c in tc_bad[:20]:
        print('  WIN', c['run'], c['item'], c['source'], c['mine'], c['theirs'], c['result'])
    for n in W:
        X = W[n]
        print('==', n, 'used', len(X['kept']), 'left', [r['name'] for r in X['left']], 'odd', [r['name'] for r in X['odd']],
              'dup', X['dup'])
        for a in X['order']:
            b = X['stats'][X['sets'][0]][a]
            print('  %-5s n=%2d medmed=%.3f meanmed=%.3f fps=%.3f/%.3f cpu=%.3f/%.3f fr=%.1f p99=%.3f p999=%.3f o33=%d' % (
                a, b['n'], b['median_of_median_ms'], b['mean_of_median_ms'], b['mean_fps'], b['median_fps'],
                b['mean_cpu'], b['median_cpu'], b['mean_frames'], b['median_p99_ms'], b['median_p999_ms'], b['sum_over33']))
        for a in X['order']:
            if a == X['w']['base']:
                continue
            d = X['deltas'][X['sets'][0]][a]
            ps = ' | '.join('%s %+.3f %s (%+.3f%%) %d/%d' % (m, X['paired'][a][m]['summary']['abs']['mean'],
                                                          ci3(X['paired'][a][m]['summary']['abs']),
                                                          X['paired'][a][m]['summary']['pct']['mean'],
                                                          X['paired'][a][m]['summary']['neg'],
                                                          X['paired'][a][m]['summary']['pos']) for m, _ in METRICS)
            print('  %-5s dmed%%=%+.3f dfps%%=%+.3f dcpu%%=%+.3f dcpu=%+.3f || %s' % (
                a, d['d_median_of_median_pct'], d['d_mean_fps_pct'], d['d_mean_cpu_pct'], d['d_mean_cpu_cores'], ps))
        for fr in X['first_runs']:
            print('  first p%d %s fps %.3f others %s (%s%%) rank %d' % (fr['pass_'], fr['run'], fr['fps'],
                                                                      f3(fr['others_median_fps']),
                                                                      s3(fr['fps_above_others_pct']), fr['arm_fps_rank']))
    print('C1 median_ms:', ' '.join('%+.3f' % it['d'] for it in c1['median_ms']['items']), 'neg',
          c1['median_ms']['summary']['neg'])
    for a in w6['order']:
        for sname in ('pass 1', 'pass 2', 'pooled'):
            B = tblocks[a][sname]
            print('  tail %-4s %-6s p999med=%.3f pooled=%.3f gt6=%s gt8=%s gt10=%s gt16.7=%s gt33=%s p999runs=%s' % (
                a, sname, B['median_p999_ms'], B['pooled_p999_ms'],
                f3(B['gt6']['median_rate_per_min']), f3(B['gt8']['median_rate_per_min']),
                f3(B['gt10']['median_rate_per_min']), f3(B['gt16.7']['median_rate_per_min']),
                f3(B['gt33']['median_rate_per_min']), ' '.join('%.3f' % v for v in B['p999_ms_per_run'])))
    for r in tail_runs:
        t = r['tail']
        print('  run p%d %2d %-14s p999=%.3f max=%.3f counts=%s' % (r['pass_'], r['seq'], r['name'], t['p999_ms'],
                                                                   t['max_ms'], [t['counts'][k] for k, _ in THRESH]))
    print('wrote', OUT_MD, OUT_JSON, '%.1f s' % (time.time() - t_start))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""sysaudit.py - read-only disturbance audit of finished timing windows (helper of Agent 8).

usage: python -B sysaudit.py <tag> <matrix_dir> <out_dir> [<tag> <matrix_dir> <out_dir> ...]
Reads only <matrix_dir>/results.csv and <matrix_dir>/runs/*/{sys.csv,proc.csv,run.json};
writes only into <out_dir> (runs.csv, samples.csv, activity.csv, summary.json, report.md).
stdlib only, single thread.

Busy formulas (per 1 s sys.csv sample, interval (e_prev, e]):
  A  (add-on)  busy_A = 12 * min(1, cpu_util_pct / cpu_perf_pct)
  B  (per class, time based)
       f_P = 1700 (P LP nominal 'Processor Frequency'), f_E = 1.5*base_mhz - 850
       (from 12*base = 4*f_P + 8*f_E); if base > 1700 or f_E <= 0: f_P = f_E = base
       busy_P = p_util/100 * f_P / p_eff_mhz ; busy_E = e_util/100 * f_E / e_eff_mhz
       busy_B = 4*min(1,busy_P) + 8*min(1,busy_E)          (logical CPUs busy, time share)
  U  (utility, Agent 1 style) util_LP = 4*p_util/100 + 8*e_util/100 (= 12*cpu_util/100)
  game  = slope of proc.csv cpu_s interpolated on the epoch line over the same interval
  non-game ng_X = X - game
"""
import bisect, csv, json, math, os, random, statistics, sys

NLP, NP, NE = 12, 4, 8
FP_NOM = 1700.0
NPERM = 5000

CFG = {
    'w4b': {
        'group_name': 'flagged',
        'group': {
            '1545-B-r1': 'run 3: A2 prep-b4.py dry run 15:46:11-22',
            '1547-d3-r1': 'run 4: A2 shell checks 15:47:17-19/15:47:40-44 (warm-up); A11 reads from 15:48',
            '1549-d11t-r1': 'run 5: A11 reads/write 15:48-15:55',
            '1551-B-r2': 'run 6: A11 reads/write; A9 clang++ ~15:51-15:53 (valid_timing=False)',
            '1553-d3-r2': 'run 7: A11 reads/write (to 15:55)',
            '1600-d3-r3': 'run 10: A11 listings + Get-Process 16:01:54-16:02:36',
        },
        'acts': [
            ('A2 prep-b4.py dry run (1 thread)', '15:46:11', '15:46:22'),
            ('A2 shell check a', '15:47:17', '15:47:19'),
            ('A2 shell check b', '15:47:40', '15:47:44'),
            ('A11 python reads + 1 write', '15:48:00', '15:55:59'),
            ('A9 clang++ syntax checks (approx)', '15:51:00', '15:53:59'),
            ('A11 listings + Get-Process', '16:01:54', '16:02:36'),
        ],
    },
    'w5': {
        'group_name': 'slow',
        'group': {
            '1808-s0-r2': 'slow run (A1 note)',
            '1817-base-r2': 'slow run (A1 note)',
            '1821-d11t-r3': 'slow run (A1 note)',
        },
        'acts': [
            ('A1 cron turn 18:10 (no commands)', '18:10:00', '18:10:59'),
            ('A1 reply 18:21-18:22 (no commands)', '18:21:00', '18:22:59'),
        ],
    },
}


def ff(x):
    if x is None:
        return None
    if isinstance(x, bool):
        return float(x)
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    if s == '' or s.lower() in ('nan', 'none', 'null', 'na'):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def truthy(x):
    return str(x).strip().lower() in ('1', 'true', 'yes', 'y')


def read_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def sod(w):
    try:
        h, m, s = str(w).strip().split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)
    except Exception:
        return None


def clean(v):
    return [x for x in v if x is not None]


def med(v):
    v = clean(v)
    return statistics.median(v) if v else None


def mean(v):
    v = clean(v)
    return sum(v) / len(v) if v else None


def pct(v, p):
    v = sorted(clean(v))
    if not v:
        return None
    k = max(1, int(math.ceil(p / 100.0 * len(v))))
    return v[k - 1]


def mx(v):
    v = clean(v)
    return max(v) if v else None


def mn(v):
    v = clean(v)
    return min(v) if v else None


def share(v, cond):
    v = clean(v)
    return (sum(1 for x in v if cond(x)) / len(v)) if v else None


def f(x, nd=2):
    if x is None:
        return '-'
    if isinstance(x, bool):
        return 'Y' if x else 'N'
    if isinstance(x, int):
        return str(x)
    if isinstance(x, float):
        return f'{x:.{nd}f}'
    return str(x)


def pc(x, nd=0):
    return '-' if x is None else f'{100.0 * x:.{nd}f}'


def md(header, rows):
    L = ['| ' + ' | '.join(map(str, header)) + ' |', '|' + '|'.join('---' for _ in header) + '|']
    for r in rows:
        L.append('| ' + ' | '.join(map(str, r)) + ' |')
    return L


def busy(r):
    util, perf = ff(r.get('cpu_util_pct')), ff(r.get('cpu_perf_pct'))
    base = ff(r.get('base_mhz'))
    pe, ee = ff(r.get('p_eff_mhz')), ff(r.get('e_eff_mhz'))
    pu, eu = ff(r.get('p_util_pct')), ff(r.get('e_util_pct'))
    o = {'util': util, 'perf': perf, 'base': base, 'p_eff': pe, 'e_eff': ee, 'p_util': pu, 'e_util': eu}
    o['ratioA'] = util / perf if (util is not None and perf) else None
    o['busyA'] = NLP * min(1.0, o['ratioA']) if o['ratioA'] is not None else None
    o['bP_raw'] = o['bE_raw'] = o['bP'] = o['bE'] = o['busyB'] = o['bE_base_raw'] = None
    o['modelB'] = ''
    if None not in (base, pe, ee, pu, eu) and pe > 0 and ee > 0:
        fP, fE, model = FP_NOM, 1.5 * base - 850.0, 'B'
        if base > FP_NOM + 0.5 or fE <= 0:
            fP, fE, model = base, base, 'Bbase'
        o['bP_raw'] = pu / 100.0 * fP / pe
        o['bE_raw'] = eu / 100.0 * fE / ee
        o['bE_base_raw'] = eu / 100.0 * base / ee
        o['bP'] = min(1.0, o['bP_raw'])
        o['bE'] = min(1.0, o['bE_raw'])
        o['busyB'] = NP * o['bP'] + NE * o['bE']
        o['modelB'] = model
    if pu is not None and eu is not None:
        o['utilLP'] = NP * pu / 100.0 + NE * eu / 100.0
    elif util is not None:
        o['utilLP'] = NLP * util / 100.0
    else:
        o['utilLP'] = None
    return o


def load_proc(path, rj):
    rows = read_csv(path)
    ms = ff((rj.get('measure_start') or {}).get('epoch_s'))
    ffe = ff(rj.get('ff_signal_epoch_s'))
    off = None
    for r in rows:
        if 'measure start' in (r.get('note') or '').lower() and ms is not None:
            t = ff(r.get('t_s'))
            if t is not None:
                off = ms - t
                break
    if off is None:
        for r in rows:
            if 'first frame' in (r.get('note') or '').lower() and ffe is not None:
                t = ff(r.get('t_s'))
                if t is not None:
                    off = ffe - t
                    break
    pts = []
    if off is not None:
        for r in rows:
            t, c = ff(r.get('t_s')), ff(r.get('cpu_s'))
            if t is None or c is None:
                continue
            pts.append((t + off, c, ff(r.get('cpu_cores')), r.get('phase', ''), r.get('note', '')))
        pts.sort(key=lambda x: x[0])
    return pts, off


def interp(pts, xs, e, tol=1.5):
    n = len(pts)
    if n < 2 or e is None:
        return None
    if e < xs[0]:
        if xs[0] - e > tol:
            return None
        i = 1
    elif e > xs[-1]:
        if e - xs[-1] > tol:
            return None
        i = n - 1
    else:
        i = bisect.bisect_left(xs, e)
        if i == 0:
            i = 1
    e0, c0 = xs[i - 1], pts[i - 1][1]
    e1, c1 = xs[i], pts[i][1]
    if e1 == e0:
        return c1
    return c0 + (c1 - c0) * (e - e0) / (e1 - e0)


def process_run(rdir, name):
    with open(os.path.join(rdir, 'run.json'), encoding='utf-8-sig') as fh:
        rj = json.load(fh)
    sysrows = read_csv(os.path.join(rdir, 'sys.csv'))
    pts, off = load_proc(os.path.join(rdir, 'proc.csv'), rj)
    xs = [p[0] for p in pts]
    ms = ff((rj.get('measure_start') or {}).get('epoch_s'))
    me = ff((rj.get('measure_end') or {}).get('epoch_s'))
    sw = rj.get('sys') or {}
    if ms is None:
        ms = ff(sw.get('window_start_epoch'))
    if me is None:
        me = ff(sw.get('window_end_epoch'))
    ffe = ff(rj.get('ff_signal_epoch_s'))
    S = []
    prev_e = None
    for r in sysrows:
        e = ff(r.get('epoch_s'))
        if e is None:
            continue
        if prev_e is None or e - prev_e <= 0:
            prev_e = e
            continue
        c = 0.5 * (prev_e + e)
        b = busy(r)
        alive = truthy(r.get('game_alive'))
        if not alive:
            ph = 'nogame'
        elif ms is not None and me is not None and ms <= c <= me:
            ph = 'window'
        elif ffe is not None and ms is not None and ffe <= c < ms:
            ph = 'warmup'
        elif ffe is not None and c < ffe:
            ph = 'boot'
        else:
            ph = 'after'
        g = None
        c0, c1 = interp(pts, xs, prev_e), interp(pts, xs, e)
        if c0 is not None and c1 is not None:
            g = (c1 - c0) / (e - prev_e)
        if not alive and g is None:
            g = 0.0
        s = dict(b)
        s.update({'run': name, 'phase': ph, 't_s': ff(r.get('t_s')), 'epoch': e, 'dt': e - prev_e,
                  'wall': r.get('wall', ''), 'sod': sod(r.get('wall', '')), 'game': g,
                  'idle_s': ff(r.get('idle_s')), 'fg_game': r.get('fg_game', ''),
                  'input_desktop': r.get('input_desktop', ''), 'screensaver': r.get('screensaver', ''),
                  'ac': r.get('ac', ''), 'scheme': r.get('scheme', ''), 'overlay': r.get('overlay', ''),
                  'tz_passive': ff(r.get('tz_passive_min_pct')), 'tz_temp': ff(r.get('tz_temp_max_c'))})
        for k, bk in (('ngA', 'busyA'), ('ngB', 'busyB'), ('ngU', 'utilLP')):
            s[k] = (s[bk] - g) if (s.get(bk) is not None and g is not None) else None
        S.append(s)
        prev_e = e
    return rj, S, pts, xs, ms, me, ffe, off


def phase_stats(S, pts, xs, a, b):
    st = {'n': len(S), 'dur_s': (b - a) if (a is not None and b is not None) else None}
    if a is not None and b is not None:
        rows = [p for p in pts if a + 1e-6 < p[0] <= b + 0.25]
        st['game_cores_mean'] = mean([p[2] for p in rows])
        c0, c1 = interp(pts, xs, a), interp(pts, xs, b)
        st['game_slope'] = (c1 - c0) / (b - a) if (c0 is not None and c1 is not None and b > a) else None
    else:
        st['game_cores_mean'] = st['game_slope'] = None

    def col(k):
        return [s.get(k) for s in S]
    for k in ('busyA', 'busyB', 'utilLP', 'game', 'p_util', 'e_util', 'p_eff', 'e_eff', 'base', 'util', 'perf'):
        st[k + '_mean'] = mean(col(k))
    for k in ('ngA', 'ngB', 'ngU'):
        v = col(k)
        st[k + '_med'] = med(v)
        st[k + '_mean'] = mean(v)
        st[k + '_p90'] = pct(v, 90)
        st[k + '_max'] = mx(v)
        st[k + '_min'] = mn(v)
    bp, be = mean(col('bP')), mean(col('bE'))
    st['P_busy_pct'] = None if bp is None else 100 * bp
    st['E_busy_pct'] = None if be is None else 100 * be
    st['P_util_mean'] = st['p_util_mean']
    st['E_util_mean'] = st['e_util_mean']
    st['P_sat_share'] = share(col('bP'), lambda x: x >= 0.97)
    st['P_util97_share'] = share(col('p_util'), lambda x: x >= 97)
    st['E_sat_share'] = share(col('bE'), lambda x: x >= 0.97)
    st['ratioA_gt1_share'] = share(col('ratioA'), lambda x: x > 1.0)
    st['bP_raw_max'] = mx(col('bP_raw'))
    st['bE_raw_max'] = mx(col('bE_raw'))
    st['e_lt800_share'] = share(col('e_eff'), lambda x: x < 800)
    cur = best = 0
    for s in S:
        x = s.get('e_eff')
        if x is not None and x < 800:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    st['slow_run_max'] = best
    st['slow_state'] = best >= 3
    st['idle_min'] = mn(col('idle_s'))
    st['fg_game_share'] = share([truthy(s.get('fg_game')) for s in S], lambda x: x)
    for k in ('input_desktop', 'screensaver', 'ac', 'scheme', 'overlay'):
        st[k] = '|'.join(sorted(set(str(s.get(k, '')) for s in S)))
    st['base_min'] = mn(col('base'))
    st['base_max'] = mx(col('base'))
    st['tz_passive_min'] = mn(col('tz_passive'))
    st['tz_temp_max'] = mx(col('tz_temp'))
    st['wall_first'] = S[0]['wall'] if S else ''
    st['wall_last'] = S[-1]['wall'] if S else ''
    st['ngB_of_means'] = (st['busyB_mean'] - st['game_slope']) if (st['busyB_mean'] is not None and st['game_slope'] is not None) else None
    st['ngU_of_means'] = (st['utilLP_mean'] - st['game_slope']) if (st['utilLP_mean'] is not None and st['game_slope'] is not None) else None
    return st


def ranks(v):
    idx = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and v[idx[j + 1]] == v[idx[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            r[idx[k]] = avg
        i = j + 1
    return r


def spearman(x, y, nperm=NPERM, seed=20261122):
    pairs = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    n = len(pairs)
    if n < 5:
        return None, n, None
    rx = ranks([p[0] for p in pairs])
    ry = ranks([p[1] for p in pairs])
    mxr, myr = sum(rx) / n, sum(ry) / n
    cx = [v - mxr for v in rx]
    cy = [v - myr for v in ry]
    sxx, syy = sum(v * v for v in cx), sum(v * v for v in cy)
    if sxx == 0 or syy == 0:
        return None, n, None
    d = sum(a * b for a, b in zip(cx, cy))
    rho = d / math.sqrt(sxx * syy)
    rnd = random.Random(seed)
    cy2 = cy[:]
    thr = abs(d) - 1e-9
    cnt = 0
    for _ in range(nperm):
        rnd.shuffle(cy2)
        if abs(sum(a * b for a, b in zip(cx, cy2))) >= thr:
            cnt += 1
    return rho, n, (cnt + 1) / (nperm + 1)


def match_results(res, name):
    for key in ('run_dir', 'run', 'name', 'label'):
        for r in res:
            v = r.get(key)
            if v and os.path.basename(str(v).rstrip('\\/')) == name:
                return r
    for r in res:
        for v in r.values():
            if v and os.path.basename(str(v).rstrip('\\/')) == name:
                return r
    return None


def bp_fmt(v):
    if v is None:
        return '-'
    if isinstance(v, list):
        return str(len(v)) + ((':' + '|'.join(map(str, v)))[:50] if v else '')
    if isinstance(v, dict):
        return json.dumps(v)[:50]
    return str(v)


CPU_HDR = ['#', 'run', 'fps', 'game', 'busy_t', 'ng_t med', 'ng_t p90', 'ng_t max', 'ngA med', 'util_LP',
           'ng_u med', 'ng_u mean', 'ng_u p90', 'P busy%', 'E busy%', 'P util%', 'P sat%', 'P MHz', 'E MHz', 'E<800%']


def cpu_row(r, st):
    return [r['idx'], r['run'] + ('' if r['scored'] else ' (unscored)') + ('' if r['valid'] else ' (invalid)'),
            f(r['fps'], 1), f(st['game_slope']), f(st['busyB_mean']), f(st['ngB_med']), f(st['ngB_p90']),
            f(st['ngB_max']), f(st['ngA_med']), f(st['utilLP_mean']), f(st['ngU_med']), f(st['ngU_mean']),
            f(st['ngU_p90']), f(st['P_busy_pct'], 1), f(st['E_busy_pct'], 1), f(st['P_util_mean'], 1),
            pc(st['P_sat_share']), f(st['p_eff_mean'], 0), f(st['e_eff_mean'], 0), pc(st['e_lt800_share'])]


CTX_HDR = ['#', 'run', 'window wall', 'n', 'game proc-mean', 'game run.json', 'idle_min s', 'fg_game%', 'desktop',
           'scrsvr', 'ac', 'overlay', 'schemes', 'base MHz', 'tz_pass min', 'tz max C', 'slow-run max',
           'bp_win', 'bp_wu', 'ticks_sk', 'ticks_sk_win']


def ctx_row(r, st):
    return [r['idx'], r['run'], st['wall_first'][:8] + '-' + st['wall_last'][:8], st['n'],
            f(st['game_cores_mean']), f(ff(r['window_cpu_cores_mean_runjson'])), f(st['idle_min'], 0),
            pc(st['fg_game_share']), st['input_desktop'], st['screensaver'], st['ac'], st['overlay'],
            len(st['scheme'].split('|')), f(st['base_min'], 0) + '-' + f(st['base_max'], 0),
            f(st['tz_passive_min'], 0), f(st['tz_temp_max'], 0), st['slow_run_max'],
            bp_fmt(r['build_procs_window']), bp_fmt(r['build_procs_warmup']), f(r['ticks_skipped']),
            f(r['ticks_skipped_window'])]


SPEAR_KEYS = ['ngB_med', 'ngB_mean', 'ngA_med', 'ngU_med', 'ngU_mean', 'P_busy_pct', 'P_util_mean',
              'P_sat_share', 'E_busy_pct', 'e_eff_mean', 'e_lt800_share', 'game_slope', 'idle_min']

SAMPLE_COLS = ['idx', 'run', 'phase', 't_s', 'epoch', 'wall', 'dt', 'busyA', 'busyB', 'utilLP', 'game', 'ngA',
               'ngB', 'ngU', 'bP_raw', 'bE_raw', 'bE_base_raw', 'ratioA', 'p_util', 'e_util', 'p_eff', 'e_eff',
               'base', 'util', 'perf', 'idle_s', 'fg_game', 'modelB']


def run_matrix(tag, mdir, odir):
    os.makedirs(odir, exist_ok=True)
    cfg = CFG.get(tag, {'group_name': 'group', 'group': {}, 'acts': []})
    L = []
    P = L.append
    res = read_csv(os.path.join(mdir, 'results.csv'))
    P(f'# sysaudit {tag}: {mdir}')
    P('')
    P('results.csv columns: ' + ','.join(res[0].keys() if res else []))
    rd = os.path.join(mdir, 'runs')
    names = sorted(d for d in os.listdir(rd) if os.path.isdir(os.path.join(rd, d)))
    runs, allS = [], []
    for i, name in enumerate(names, 1):
        try:
            rj, S, pts, xs, ms, me, ffe, off = process_run(os.path.join(rd, name), name)
        except Exception as ex:
            P(f'ERROR {name}: {ex!r}')
            continue
        rr = match_results(res, name)
        if rr is None:
            P(f'WARNING: no results.csv row for {name}')
            rr = {}
        scored = truthy(rr.get('scored')) if 'scored' in rr else ('cold' not in name)
        valid = truthy(rr.get('valid_timing')) if 'valid_timing' in rr else truthy(rj.get('valid_timing'))
        for s in S:
            s['idx'] = i
        W = [s for s in S if s['phase'] == 'window']
        U = [s for s in S if s['phase'] == 'warmup']
        info = {'idx': i, 'run': name, 'build': name.split('-')[1] if '-' in name else name,
                'scored': scored, 'valid': valid, 'fps': ff(rr.get('fps_mean')),
                'res_cpu_cores': ff(rr.get('cpu_cores_mean')),
                'win': phase_stats(W, pts, xs, ms, me), 'wu': phase_stats(U, pts, xs, ffe, ms),
                'build_procs_window': rj.get('build_procs_window'),
                'build_procs_warmup': rj.get('build_procs_warmup'),
                'ticks_skipped': rj.get('ticks_skipped'), 'ticks_skipped_window': rj.get('ticks_skipped_window'),
                'window_cpu_cores_mean_runjson': rj.get('window_cpu_cores_mean'),
                'ms': ms, 'me': me, 'ffe': ffe, 'proc_offset': off, 'S': S}
        runs.append(info)
        allS.extend(S)
    sc = [r for r in runs if r['scored']]
    # fps relative to build median (valid scored runs)
    bmed = {}
    for b in sorted(set(r['build'] for r in sc)):
        v = [r['fps'] for r in sc if r['build'] == b and r['valid'] and r['fps'] is not None]
        bmed[b] = med(v)
    for r in runs:
        r['fps_rel'] = (r['fps'] / bmed[r['build']]) if (r['scored'] and r['fps'] and bmed.get(r['build'])) else None

    # ---- interpretation check
    P('')
    P('## Busy-share interpretation check (window + warm-up samples, all runs)')
    WS = [s for s in allS if s['phase'] in ('window', 'warmup')]
    rA = [s['ratioA'] for s in WS]
    bEr = [s['bE_raw'] for s in WS if s['modelB'] == 'B']
    bPr = [s['bP_raw'] for s in WS if s['modelB'] == 'B']
    bEb = [s['bE_base_raw'] for s in WS]
    nbase = sum(1 for s in WS if s['modelB'] == 'Bbase')
    P(f'- samples: {len(WS)}; model-B fallback (base>1700) samples: {nbase}; base_mhz range {f(mn([s["base"] for s in WS]),0)}-{f(mx([s["base"] for s in WS]),0)}')
    P(f'- A total util/perf: share >1.00 {pc(share(rA, lambda x: x > 1.0), 1)} %, >1.02 {pc(share(rA, lambda x: x > 1.02), 1)} %, max {f(mx(rA), 3)}, median {f(med(rA), 3)}')
    P(f'- B busy_E raw (f_E=1.5*base-850): share >1.02 {pc(share(bEr, lambda x: x > 1.02), 1)} %, >1.05 {pc(share(bEr, lambda x: x > 1.05), 1)} %, max {f(mx(bEr), 3)}, median {f(med(bEr), 3)}')
    P(f'- B busy_P raw (f_P=1700): share >1.02 {pc(share(bPr, lambda x: x > 1.02), 1)} %, max {f(mx(bPr), 3)}, median {f(med(bPr), 3)}')
    P(f'- E with f=base_mhz instead: share >1.02 {pc(share(bEb, lambda x: x > 1.02), 1)} %, max {f(mx(bEb), 3)}, median {f(med(bEb), 3)}')
    slowS = [s for s in WS if s['e_eff'] is not None and s['e_eff'] < 800]
    fastS = [s for s in WS if s['e_eff'] is not None and s['e_eff'] >= 800]
    for lab, X in (('slow (e_eff<800)', slowS), ('fast (e_eff>=800)', fastS)):
        P(f'- {lab}: n={len(X)}; e_util med {f(med([s["e_util"] for s in X]), 2)} (min {f(mn([s["e_util"] for s in X]), 2)}, max {f(mx([s["e_util"] for s in X]), 2)}); E busy_B med {pc(med([s["bE"] for s in X]), 1)} %; P busy med {pc(med([s["bP"] for s in X]), 1)} %; p_util med {f(med([s["p_util"] for s in X]), 1)}; e_eff med {f(med([s["e_eff"] for s in X]), 0)}; busy_B med {f(med([s["busyB"] for s in X]))}; util_LP med {f(med([s["utilLP"] for s in X]))}; ng_t med {f(med([s["ngB"] for s in X]))}; ng_u med {f(med([s["ngU"] for s in X]))}')

    # ---- phase pools
    P('')
    P('## Pooled by phase (all runs)')
    rows = []
    for ph in ('boot', 'warmup', 'window', 'after', 'nogame'):
        X = [s for s in allS if s['phase'] == ph]
        if not X:
            continue
        rows.append([ph, len(X), f(med([s['busyB'] for s in X])), f(med([s['busyA'] for s in X])),
                     f(med([s['utilLP'] for s in X])), f(med([s['game'] for s in X])), f(med([s['ngB'] for s in X])),
                     f(med([s['ngU'] for s in X])), f(med([s['e_eff'] for s in X]), 0), pc(share([s['e_eff'] for s in X], lambda x: x < 800))])
    L.extend(md(['phase', 'n', 'busy_t med', 'busy_A med', 'util_LP med', 'game med', 'ng_t med', 'ng_u med', 'E MHz med', 'E<800%'], rows))

    # ---- tables
    for ph, key in (('Measurement window', 'win'), ('Warm-up (first frame -> window start)', 'wu')):
        P('')
        P(f'## {ph}: CPU (busy_t = time-based model B, LPs of 12; ng = minus game slope; ngA = add-on formula; util_LP = utility-based)')
        L.extend(md(CPU_HDR, [cpu_row(r, r[key]) for r in runs]))
    P('')
    P('## Window: context (run.json build_procs/ticks are whole-run fields)')
    L.extend(md(CTX_HDR, [ctx_row(r, r['win']) for r in runs]))
    P('')
    P('## Warm-up: context')
    L.extend(md(CTX_HDR, [ctx_row(r, r['wu']) for r in runs]))

    # ---- group comparison
    gname, G = cfg['group_name'], cfg['group']
    F = [r for r in sc if r['run'] in G]
    R = [r for r in sc if r['run'] not in G]
    pool = {}
    for k in ('ngB', 'ngU', 'ngA'):
        pool[k] = pct([s[k] for r in R for s in r['S'] if s['phase'] == 'window'], 90)
    groups = {'group_name': gname, 'group_runs': [r['run'] for r in F], 'rest_runs': [r['run'] for r in R],
              'rest_pooled_p90': pool, 'metrics': {}, 'per_run': {}}
    if F:
        P('')
        P(f'## Group comparison, window, scored runs: {gname} (n={len(F)}) vs rest (n={len(R)})')
        rows = []
        for key in ('ngB_med', 'ngB_mean', 'ngB_p90', 'ngA_med', 'ngU_med', 'ngU_mean', 'ngU_p90', 'P_busy_pct',
                    'P_util_mean', 'P_sat_share', 'E_busy_pct', 'p_eff_mean', 'e_eff_mean', 'e_lt800_share',
                    'game_slope', 'idle_min', 'fps', 'fps_rel'):
            if key in ('fps', 'fps_rel'):
                fv, rv = [r[key] for r in F], [r[key] for r in R]
            else:
                fv, rv = [r['win'][key] for r in F], [r['win'][key] for r in R]
            above = [r['run'] for r, v in zip(F, fv) if v is not None and mx(rv) is not None and v > mx(rv)]
            below = [r['run'] for r, v in zip(F, fv) if v is not None and mn(rv) is not None and v < mn(rv)]
            groups['metrics'][key] = {'group_med': med(fv), 'group_min': mn(fv), 'group_max': mx(fv),
                                      'rest_med': med(rv), 'rest_min': mn(rv), 'rest_max': mx(rv),
                                      'above_rest_max': above, 'below_rest_min': below}
            nd = 3 if key in ('fps_rel', 'P_sat_share', 'e_lt800_share') else 2
            rows.append([key, f'{f(med(fv), nd)} [{f(mn(fv), nd)}..{f(mx(fv), nd)}]',
                         f'{f(med(rv), nd)} [{f(mn(rv), nd)}..{f(mx(rv), nd)}]', ','.join(above) or '-', ','.join(below) or '-'])
        L.extend(md(['metric', f'{gname} median [min..max]', 'rest median [min..max]', 'above rest max', 'below rest min'], rows))
    P('')
    P(f'## Bursts: 1 s window samples above the rest-pooled p90 (ng_t {f(pool["ngB"])}, ng_u {f(pool["ngU"])}, ngA {f(pool["ngA"])})' +
      ('' if F else ' (no group: rest = all scored runs)'))
    rows = []
    for r in sc:
        W = [s for s in r['S'] if s['phase'] == 'window']
        cnts = {}
        for k in ('ngB', 'ngU', 'ngA'):
            v = clean([s[k] for s in W])
            cnts[k] = (sum(1 for x in v if pool[k] is not None and x > pool[k]), len(v))
        walls = [s['wall'][:8] for s in W if s['ngU'] is not None and pool['ngU'] is not None and s['ngU'] > pool['ngU']]
        groups['per_run'][r['run']] = {'burst_ngB': cnts['ngB'], 'burst_ngU': cnts['ngU'], 'burst_ngA': cnts['ngA'], 'burst_ngU_walls': walls}
        rows.append([r['idx'], r['run'], gname if r['run'] in G else 'rest', f'{cnts["ngB"][0]}/{cnts["ngB"][1]}',
                     f'{cnts["ngU"][0]}/{cnts["ngU"][1]}', f'{cnts["ngA"][0]}/{cnts["ngA"][1]}',
                     f(r['win']['ngB_max']), f(r['win']['ngU_max']), ' '.join(walls)[:120]])
    L.extend(md(['#', 'run', 'grp', 'ng_t>p90', 'ng_u>p90', 'ngA>p90', 'ng_t max', 'ng_u max', 'walls of ng_u bursts'], rows))

    # ---- activity alignment
    act_rows = []
    P('')
    P('## Known activity vs 1 s samples (sample wall = end of its 1 s interval)')
    rows = []
    for (label, a, b) in cfg['acts']:
        A, B = sod(a), sod(b) + 0.999
        hits = [s for s in allS if s['sod'] is not None and A <= s['sod'] <= B]
        if not hits:
            rows.append([label, f'{a}-{b}', '-', 'no samples (between runs / outside sys.csv)', '', '', '', '', '', ''])
            continue
        keys = []
        for s in hits:
            kk = (s['idx'], s['run'], s['phase'])
            if kk not in keys:
                keys.append(kk)
        for kk in keys:
            X = [s for s in hits if (s['idx'], s['run'], s['phase']) == kk]
            r = next(x for x in runs if x['run'] == kk[1])
            for s in X:
                act_rows.append([label, a, b, s['idx'], s['run'], s['phase'], s['wall'], s['busyB'], s['utilLP'], s['game'],
                                 s['ngB'], s['ngU'], s['ngA'], s['p_util'], s['e_eff'], pool['ngB'], pool['ngU']])
            nB = sum(1 for s in X if s['ngB'] is not None and pool['ngB'] is not None and s['ngB'] > pool['ngB'])
            nU = sum(1 for s in X if s['ngU'] is not None and pool['ngU'] is not None and s['ngU'] > pool['ngU'])
            rows.append([label, f'{a}-{b}', f'{kk[0]} {kk[1]}', f'{kk[2]} {X[0]["wall"][:8]}-{X[-1]["wall"][:8]} n={len(X)}',
                         f'{f(mean([s["ngB"] for s in X]))} / {f(mx([s["ngB"] for s in X]))}',
                         f'{f(mean([s["ngU"] for s in X]))} / {f(mx([s["ngU"] for s in X]))}',
                         f'{f(r["win"]["ngB_med"])} / {f(r["win"]["ngU_med"])}',
                         f'{f(r["wu"]["ngB_med"])} / {f(r["wu"]["ngU_med"])}', f'{nB} / {nU}',
                         f'{f(mean([s["p_util"] for s in X]), 1)} / {f(mean([s["e_eff"] for s in X]), 0)}'])
    L.extend(md(['activity', 'time', 'run', 'phase, samples', 'ng_t mean/max', 'ng_u mean/max', 'run window med t/u',
                 'run warm-up med t/u', 'n > rest p90 t/u', 'P util / E MHz'], rows))

    # ---- Spearman
    spear = {}
    P('')
    P(f'## Spearman rank correlation with window fps (permutation p, {NPERM} perms, two-sided); fps_rel = fps / median fps of the same build (valid runs)')
    rows = []
    for lab, X in (('all scored', sc), ('valid scored', [r for r in sc if r['valid']])):
        for key in SPEAR_KEYS:
            x = [r['win'][key] for r in X]
            r1, n1, p1 = spearman(x, [r['fps'] for r in X])
            r2, n2, p2 = spearman(x, [r['fps_rel'] for r in X])
            spear[f'{lab}|{key}'] = {'rho_fps': r1, 'n': n1, 'p_fps': p1, 'rho_fps_rel': r2, 'n_rel': n2, 'p_fps_rel': p2}
            rows.append([lab, key, f'{f(r1, 3)} (n={n1}, p={f(p1, 3)})', f'{f(r2, 3)} (n={n2}, p={f(p2, 3)})'])
    L.extend(md(['set', 'window metric', 'rho vs fps', 'rho vs fps_rel'], rows))

    # ---- write files
    with open(os.path.join(odir, 'samples.csv'), 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(SAMPLE_COLS)
        for s in allS:
            w.writerow([('' if s.get(c) is None else (round(s[c], 4) if isinstance(s.get(c), float) else s.get(c))) for c in SAMPLE_COLS])
    statkeys = sorted(runs[0]['win'].keys()) if runs else []
    with open(os.path.join(odir, 'runs.csv'), 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        head = ['idx', 'run', 'build', 'phase', 'scored', 'valid_timing', 'fps_mean', 'fps_rel', 'results_cpu_cores_mean',
                'runjson_window_cpu_cores_mean', 'build_procs_window', 'build_procs_warmup', 'ticks_skipped', 'ticks_skipped_window', 'group']
        w.writerow(head + statkeys)
        for r in runs:
            for ph, key in (('window', 'win'), ('warmup', 'wu')):
                st = r[key]
                w.writerow([r['idx'], r['run'], r['build'], ph, r['scored'], r['valid'], r['fps'], r['fps_rel'], r['res_cpu_cores'],
                            r['window_cpu_cores_mean_runjson'], bp_fmt(r['build_procs_window']), bp_fmt(r['build_procs_warmup']),
                            r['ticks_skipped'], r['ticks_skipped_window'], (gname if r['run'] in G else 'rest')] +
                           [('' if st[k] is None else (round(st[k], 4) if isinstance(st[k], float) else st[k])) for k in statkeys])
    with open(os.path.join(odir, 'activity.csv'), 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['activity', 'act_start', 'act_end', 'idx', 'run', 'phase', 'wall', 'busy_t', 'util_LP', 'game', 'ng_t', 'ng_u',
                    'ngA', 'p_util', 'e_eff', 'rest_p90_ng_t', 'rest_p90_ng_u'])
        for row in act_rows:
            w.writerow([('' if v is None else (round(v, 4) if isinstance(v, float) else v)) for v in row])
    summ = {'tag': tag, 'matrix': mdir, 'build_median_fps': bmed, 'groups': groups, 'spearman': spear,
            'runs': [{k: v for k, v in r.items() if k != 'S'} for r in runs]}
    with open(os.path.join(odir, 'summary.json'), 'w', encoding='utf-8') as fh:
        json.dump(summ, fh, indent=1, default=str)
    with open(os.path.join(odir, 'report.md'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L) + '\n')
    return {'tag': tag, 'odir': odir, 'runs': runs, 'sc': sc, 'allS': allS}


def cross(allm):
    L = ['', '## Cross-matrix comparison (scored runs; medians over runs of per-run window values)']
    keys = ['ngB_med', 'ngA_med', 'ngU_med', 'ngU_mean', 'busyB_mean', 'utilLP_mean', 'game_slope', 'P_busy_pct',
            'P_util_mean', 'E_busy_pct', 'p_eff_mean', 'e_eff_mean', 'e_lt800_share', 'idle_min']
    rows = []
    for key in keys:
        row = [key]
        for tag, m in allm.items():
            v = [r['win'][key] for r in m['sc']]
            row.append(f'{f(med(v), 3)} [{f(mn(v), 3)}..{f(mx(v), 3)}]')
        rows.append(row)
    for ph in ('nogame', 'boot'):
        for lab, k in (('busy_t', 'busyB'), ('util_LP', 'utilLP')):
            row = [f'{ph} samples: {lab} med (n)']
            for tag, m in allm.items():
                X = [s[k] for s in m['allS'] if s['phase'] == ph]
                row.append(f'{f(med(X))} (n={len(clean(X))})')
            rows.append(row)
    L.extend(md(['metric'] + list(allm.keys()), rows))
    return L


def main(argv):
    if len(argv) < 3 or len(argv) % 3:
        print(__doc__)
        return 2
    allm = {}
    for i in range(0, len(argv), 3):
        tag, mdir, odir = argv[i:i + 3]
        allm[tag] = run_matrix(tag, mdir, odir)
        print(f'{tag}: wrote {odir}')
    if len(allm) > 1:
        L = cross(allm)
        for m in allm.values():
            with open(os.path.join(m['odir'], 'report.md'), 'a', encoding='utf-8') as fh:
                fh.write('\n'.join(L) + '\n')
        print('\n'.join(L))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

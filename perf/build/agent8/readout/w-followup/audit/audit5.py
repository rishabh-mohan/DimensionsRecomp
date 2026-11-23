"""audit5.py - section 5 of audit.py (Agent 8 follow-up items, 11:57Z). Imported by audit.py, which runs as __main__.
Read-only on build/agent8/matrix; stdlib only."""
import math, random, re, statistics
from collections import Counter
import __main__ as A
import sysaudit as SA
from sysaudit import ff, med, mean, mx, mn, share, f, pc, md, clean

EP_0313 = ['0325-p2f-r2', '0327-p2fc-r2', '0329-s0-r2', '0331-p2f-r3', '0333-p2fc-r3', '0335-s0-r3', '0337-p2-r3', '0339-p2fc-r4']
W4C_FOCUS = ['0251-B-r3', '0253-B-r4']
W61_FOCUS = [('0023-p2fc-r2', 0, 12), ('0031-s0-r3', None, None), ('0037-s0-r4', None, None), ('0039-p2-r4', 8, 22)]
_S3, _S9, _S4 = '20261123-0313', '20261123-0009', '20261123-0239'
A8_N6 = {(_S3, '0325-p2f-r2'): '33', (_S3, '0327-p2fc-r2'): '40', (_S3, '0329-s0-r2'): '58', (_S3, '0331-p2f-r3'): '40',
         (_S3, '0333-p2fc-r3'): '34', (_S3, '0335-s0-r3'): '44', (_S3, '0337-p2-r3'): '40', (_S3, '0339-p2fc-r4'): '34',
         (_S3, '0352-p2f-r5'): '21 (all 0-10)', (_S4, '0251-B-r3'): '22 (20 in 30-40)', (_S4, '0253-B-r4'): '35 (8/2/12/9/4)',
         (_S9, '0023-p2fc-r2'): '40 (31 in 0-10)', (_S9, '0031-s0-r3'): '29 (2/7/1/10/9)', (_S9, '0037-s0-r4'): '43 (10/14/4/8/7)',
         (_S9, '0039-p2-r4'): '17 (all 10-20)'}
FB_STAMPS = (_S9, _S3, _S4)
THR = (6.0, 8.0, 10.0, 16.7)
BIN_S = 10.0
PC = ('pipeline_cache_misses', 'texture_cache_misses', 'command_buffer_stalls', 'critical_region_contentions', 'interrupt_dispatches')
PK = ('pipe', 'tex', 'cbs', 'crit', 'intr')


def sg(fn, x):
    try:
        return fn(x)
    except (KeyError, TypeError, ZeroDivisionError, AttributeError, IndexError):
        return None


def frame_bins(r, pw):
    fr, col = pw['frames'], pw['col']
    msv = [x[4] for x in fr]
    medft = statistics.median(msv) if msv else None
    lag = A.FLUSH_ROWS * medft / 1000.0 if medft else 0.0
    nb = max(1, int(round(pw['sum_s'] / BIN_S)))
    S = r['_S']
    ends, dts = [s['epoch'] for s in S], [s['dt'] for s in S]
    ci = [col.get(c) for c in PC]
    o = {'n': len(fr), 'median_ms': medft, 'lag_s': lag, 'sum_s': pw['sum_s'], 'nb': nb, 'max': max(msv) if msv else None,
         'cnt': {t: 0 for t in THR}, 'bins': [{'n': 0, 'n6': 0, 'n10': 0, 'max': 0.0} for _ in range(nb)],
         'tot': dict.fromkeys(PK, 0.0), 'tot6': dict.fromkeys(PK, 0.0), 'n6_pipe': 0, 'list6': [], 'sec': {}}
    for (k, i, t0, t1, x, vals) in fr:
        B = o['bins'][min(nb - 1, int(t1 // BIN_S))]
        B['n'] += 1
        B['max'] = max(B['max'], x)
        for t in THR:
            if x > t:
                o['cnt'][t] += 1
        pv = [(ff(vals[j]) if (j is not None and j < len(vals)) else None) or 0.0 for j in ci]
        for kk, v in zip(PK, pv):
            o['tot'][kk] += v
        si = A.at(ends, dts, r['ms'] + t1 - lag / 2)
        if si is not None:
            sd = o['sec'].setdefault(si, {'n': 0, 'n6': 0, 'max': 0.0, **dict.fromkeys(PK, 0.0)})
            sd['n'] += 1
            sd['max'] = max(sd['max'], x)
            for kk, v in zip(PK, pv):
                sd[kk] += v
            if x > 6.0:
                sd['n6'] += 1
        if x > 6.0:
            B['n6'] += 1
            for kk, v in zip(PK, pv):
                o['tot6'][kk] += v
            o['n6_pipe'] += 1 if pv[0] > 0 else 0
            o['list6'].append((round(t1, 3), round(x, 2)))
        if x > 10.0:
            B['n10'] += 1
    return o


def thr_int(x):
    s = str(x or '').strip()
    try:
        return int(s, 16) if s.lower().startswith('0x') else int(float(s))
    except ValueError:
        return None


def gpu_window(r):
    if r.get('ms') is None:
        return {'n': 0}, []
    rows = A.load_gpu(r['rdir'], r['local_off'])
    me = r['me'] or r['ms'] + 50
    W = [g for g in rows if r['ms'] - 0.6 <= g['epoch'] <= me + 0.6]
    for g in W:
        g['T'] = g['epoch'] - r['ms']

    def col(k):
        return [ff(g.get(k)) for g in W]
    gr, tc, pw, ut = col('gr_mhz'), col('temp_c'), col('power_w'), col('util_gpu')
    th = clean([thr_int(g.get('throttle')) for g in W])
    return ({'n': len(W), 'gr_mean': mean(gr), 'gr_min': mn(gr), 'gr_max': mx(gr), 'gr_first5': mean(gr[:5]), 'gr_last5': mean(gr[-5:]),
             'temp_mean': mean(tc), 'temp_max': mx(tc), 'temp_first5': mean(tc[:5]), 'temp_last5': mean(tc[-5:]),
             'power_mean': mean(pw), 'util_mean': mean(ut), 'util_min': mn(ut), 'mem_mhz': med(col('mem_mhz')),
             'thr': dict(Counter('0x%x' % t for t in th)), 'thermal_share': share(th, lambda t: bool(t & 0x60)),
             'power_share': share(th, lambda t: bool(t & 0x84)), 'pstates': sorted(set(str(g.get('pstate')) for g in W))}, W)


def proc_window(r):
    rows = A.load_proc_rows(r['rdir'], r['proc_off'])
    if r.get('ms') is None:
        return {'n': 0}, rows
    me = r['me'] or r['ms'] + 50
    W = [p for p in rows if r['ms'] + 0.5 < p['epoch'] <= me + 0.5]
    o = {'n': len(W), 'responding': sorted(set(str(p.get('responding', '')) for p in W))}
    for k in ('cpu_cores', 'free_ram_gb', 'ws_mb', 'commit_mb', 'threads', 'handles'):
        v = [ff(p.get(k)) for p in W]
        o[k + '_mean'], o[k + '_min'], o[k + '_max'] = mean(v), mn(v), mx(v)
    return o, rows


def sec_records(r, fb, grows, prows):
    S = r['_S']
    ends, dts = [s['epoch'] for s in S], [s['dt'] for s in S]
    gm, pm = {}, {}
    for g in grows:
        i = A.at(ends, dts, g['epoch'])
        if i is not None:
            gm.setdefault(i, []).append(g)
    for p in prows:
        i = A.at(ends, dts, p['epoch'])
        if i is not None:
            pm.setdefault(i, []).append(p)
    out = []
    for i, s in enumerate(S):
        if s['phase'] != 'window':
            continue
        sd, G, Pp = fb['sec'].get(i, {}), gm.get(i, []), pm.get(i, [])
        x = {'T': s['epoch'] - r['ms'], 'wall': s['wall'][:8], 'n': sd.get('n', 0), 'n6': sd.get('n6', 0), 'max': sd.get('max')}
        for kk in PK:
            x[kk] = sd.get(kk)
        for kk, sk in (('ngB', 'ngB'), ('ngU', 'ngU'), ('p_util', 'p_util'), ('e_util', 'e_util'), ('p_eff', 'p_eff'),
                       ('e_eff', 'e_eff'), ('game', 'game'), ('idle', 'idle_s')):
            x[kk] = s.get(sk)
        for kk, pk in (('pcores', 'cpu_cores'), ('pthr', 'threads'), ('ws', 'ws_mb'), ('free', 'free_ram_gb')):
            x[kk] = mean([ff(p.get(pk)) for p in Pp])
        for kk, gk in (('gr', 'gr_mhz'), ('temp', 'temp_c'), ('gpow', 'power_w'), ('gutil', 'util_gpu')):
            x[kk] = mean([ff(g.get(gk)) for g in G])
        x['thr'] = '/'.join(sorted(set(str(g.get('throttle')) for g in G))) or '-'
        out.append(x)
    return out


BK = ('ngB', 'ngU', 'p_util', 'e_util', 'p_eff', 'e_eff', 'game', 'gr', 'temp', 'gpow', 'gutil', 'pcores', 'free')
BIN_HDR = ['bin s', 'frames', '>6', '>10', 'max ms', 'secs', 'ng_t', 'ng_t max', 'ng_u', 'P util', 'E util', 'P MHz', 'E MHz', 'game',
           'GPU MHz', 'GPU C', 'GPU W', 'GPU util', 'proc cores', 'free GB']


def bin_stats(recs, fb):
    out = []
    for b in range(fb['nb']):
        X = [x for x in recs if max(0, min(fb['nb'] - 1, int((x['T'] - 0.5) // BIN_S))) == b]
        B = fb['bins'][b]
        d = {'bin': '%d-%d' % (b * BIN_S, (b + 1) * BIN_S), 'frames': B['n'], 'n6': B['n6'], 'n10': B['n10'], 'max': B['max'],
             'secs': len(X), 'ngB_max': mx([x['ngB'] for x in X])}
        d.update({k: mean([x[k] for x in X]) for k in BK})
        out.append(d)
    return out


def bin_rows(bs):
    return [[d['bin'], d['frames'], d['n6'], d['n10'], f(d['max'], 2), d['secs'], f(d['ngB']), f(d['ngB_max']), f(d['ngU']),
             f(d['p_util'], 1), f(d['e_util'], 1), f(d['p_eff'], 0), f(d['e_eff'], 0), f(d['game']), f(d['gr'], 0), f(d['temp'], 1),
             f(d['gpow'], 2), f(d['gutil'], 1), f(d['pcores']), f(d['free'])] for d in bs]


def hot_line(name, bs):
    hb = max(bs, key=lambda d: d['n6'])
    rest = [d for d in bs if d is not hb]

    def vs(k, nd=2):
        return '%s vs %s' % (f(hb[k], nd), f(mean([d[k] for d in rest]), nd))
    return ('%s: most >6 ms frames in bin %s s (%d of %d); that bin vs the mean of the other bins: ng_t %s, ng_t 1 s max %s, ng_u %s, '
            'P util %s, P MHz %s, E MHz %s, game %s, GPU MHz %s, GPU C %s, GPU util %s, free RAM GB %s.'
            % (name, hb['bin'], hb['n6'], sum(d['n6'] for d in bs), vs('ngB'), vs('ngB_max'), vs('ngU'), vs('p_util', 1), vs('p_eff', 0),
               vs('e_eff', 0), vs('game'), vs('gr', 0), vs('temp', 1), vs('gutil', 1), vs('free')))


SEC_HDR = ['T end s', 'wall', 'frames', '>6', 'max ms', 'pipe', 'tex', 'cbs', 'crit', 'intr', 'ng_t', 'ng_u', 'P util', 'E util', 'P MHz',
           'E MHz', 'game', 'proc cores', 'threads', 'ws MB', 'free GB', 'GPU MHz', 'GPU C', 'GPU W', 'GPU util', 'throttle']


def sec_rows(recs, t0, t1):
    return [[f(x['T'], 2), x['wall'], x['n'], x['n6'], f(x['max'], 2)] + [f(x[k], 0) for k in PK] +
            [f(x['ngB']), f(x['ngU']), f(x['p_util'], 1), f(x['e_util'], 1), f(x['p_eff'], 0), f(x['e_eff'], 0), f(x['game']),
             f(x['pcores']), f(x['pthr'], 0), f(x['ws'], 0), f(x['free']), f(x['gr'], 0), f(x['temp'], 0), f(x['gpow'], 2),
             f(x['gutil'], 0), x['thr']] for x in recs if t0 <= x['T'] - 0.5 < t1]


def perm_p(a, b, nperm=5000, seed=7):
    a, b = clean(a), clean(b)
    if len(a) < 2 or len(b) < 2:
        return None
    obs = abs(statistics.median(a) - statistics.median(b))
    pool, na, rng, hit = a + b, len(a), random.Random(seed), 0
    for _ in range(nperm):
        rng.shuffle(pool)
        if abs(statistics.median(pool[:na]) - statistics.median(pool[na:])) >= obs - 1e-12:
            hit += 1
    return (hit + 1) / (nperm + 1)


def sign_p(pos, neg):
    n = pos + neg
    if not n:
        return None
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(min(pos, neg) + 1)) / 2.0 ** n)


def rng_s(v, nd=2):
    return '%s [%s..%s]' % (f(med(v), nd), f(mn(v), nd), f(mx(v), nd))


def grp_cmp(XA, XB, la, lb, metrics):
    rows, out = [], {}
    for name, fn, nd in metrics:
        a, b = [sg(fn, x) for x in XA], [sg(fn, x) for x in XB]
        ca, cb = clean(a), clean(b)
        sep = '-'
        if ca and cb and min(ca) > max(cb):
            sep = 'all %s > all %s' % (la, lb)
        elif ca and cb and max(ca) < min(cb):
            sep = 'all %s < all %s' % (la, lb)
        d = (med(a) - med(b)) if (ca and cb) else None
        p = perm_p(a, b)
        rows.append([name, rng_s(a, nd), rng_s(b, nd), f(d, nd), f(p, 3), sep])
        out[name] = {'a_med': med(a), 'b_med': med(b), 'diff': d, 'perm_p': p, 'sep': sep}
    return rows, out


SK = ('ngB', 'ngU', 'p_util', 'e_util', 'p_eff', 'e_eff', 'game', 'gutil', 'gr', 'temp', 'pcores', 'free', 'intr')


def sec_compare(items):
    H, N, per, ns = {k: [] for k in SK}, {k: [] for k in SK}, {k: [] for k in SK}, [0, 0]
    for recs in items:
        R = [x for x in recs if x['n'] >= 50]
        h, n = [x for x in R if x['n6'] >= 1], [x for x in R if x['n6'] == 0]
        ns[0] += len(h)
        ns[1] += len(n)
        for k in SK:
            H[k] += [x[k] for x in h]
            N[k] += [x[k] for x in n]
            if h and len(n) >= 5:
                a, b = med([x[k] for x in h]), med([x[k] for x in n])
                if a is not None and b is not None:
                    per[k].append(a - b)
    rows = []
    for k in SK:
        pos, neg = sum(1 for v in per[k] if v > 0), sum(1 for v in per[k] if v < 0)
        rows.append([k, f(med(H[k])), f(med(N[k])), f(med(per[k])), '%d/%d' % (pos, neg), f(sign_p(pos, neg), 3)])
    return rows, ns


SECCMP_HDR = ['metric (per s)', 'seconds with >6 ms frame: median', 'other seconds: median', 'median per-run diff', 'runs diff >0 / <0', 'sign p']


def log_in(r, t0, t1, maxn=20):
    lo, ms = r['local_off'], r['ms']
    X = ['T %.2f %s [%s] [%s] %s' % (t + lo - ms, A.hms(t)[:12], lvl, cat, msg[:80]) for (t, lvl, cat, tid, msg) in r['log']['_entries']
         if t is not None and lo is not None and ms is not None and t0 <= t + lo - ms <= t1]
    return X[:maxn], len(X)


RUN_HDR = ['#', 'run', 'win wall', 'fps', 'fps_rel', '>6/>10/>16.7', 'A8 >6', 'max ms', 'ng_t mean', 'ng_t max', 'ng_u mean', 'bursts',
           'wu ng_t', 'P util', 'P MHz', 'E MHz', 'game', 'threads/handles', 'commit MB', 'free GB min', 'GPU MHz (min)', 'GPU C mean/max',
           'GPU W', 'GPU util', 'thermal %', 'pipe all/>6fr', 'batt %', 'build procs']


def run_row(r, fb, gs, ps, mark=''):
    w, wu = r['win'], r['wu']
    bat = [s.get('batt_pct') for s in r['_S'] if s['phase'] == 'window']
    return [r['idx'], r['run'] + mark + ('' if r['scored'] else ' (unscored)'), r['win_wall'], f(r['res_fps_mean'], 1), f(r.get('fps_rel'), 3),
            ('%d/%d/%d' % (fb['cnt'][6.0], fb['cnt'][10.0], fb['cnt'][16.7])) if fb else '-', A8_N6.get((r['stamp'], r['run']), ''),
            f(fb['max'], 2) if fb else '-', f(w.get('ngB_mean')), f(w.get('ngB_max')), f(w.get('ngU_mean')), (r.get('burst') or {}).get('ngB', '-'),
            f(wu.get('ngB_mean')), f(w.get('P_util_mean'), 1), f(w.get('p_eff_mean'), 0), f(w.get('e_eff_mean'), 0), f(w.get('game_slope')),
            '%s/%s' % (f(ps.get('threads_mean'), 0), f(ps.get('handles_mean'), 0)), f(ps.get('commit_mb_mean'), 0), f(ps.get('free_ram_gb_min')),
            '%s (%s)' % (f(gs.get('gr_mean'), 0), f(gs.get('gr_min'), 0)), '%s/%s' % (f(gs.get('temp_mean'), 1), f(gs.get('temp_max'), 0)),
            f(gs.get('power_mean'), 2), f(gs.get('util_mean'), 1), pc(gs.get('thermal_share')),
            ('%d/%d' % (fb['tot']['pipe'], fb['tot6']['pipe'])) if fb else '-', ('%s-%s' % (bat[0], bat[-1])) if bat else '-',
            str(r.get('build_procs_window'))[:20]]


MET = [('>6 ms frames', lambda x: float(x[1]['cnt'][6.0]), 0), ('>10 ms frames', lambda x: float(x[1]['cnt'][10.0]), 0),
       ('max frame ms', lambda x: x[1]['max'], 2), ('fps_rel', lambda x: x[0]['fps_rel'], 3), ('ng_t mean', lambda x: x[0]['win']['ngB_mean'], 2),
       ('ng_t 1 s max', lambda x: x[0]['win']['ngB_max'], 2), ('ng_u mean', lambda x: x[0]['win']['ngU_mean'], 2),
       ('ng_t bursts', lambda x: float(x[0]['burst']['ngB']), 0), ('warm-up ng_t', lambda x: x[0]['wu']['ngB_mean'], 2),
       ('P util %', lambda x: x[0]['win']['P_util_mean'], 1), ('E util %', lambda x: x[0]['win']['E_util_mean'], 1),
       ('P MHz', lambda x: x[0]['win']['p_eff_mean'], 0), ('E MHz', lambda x: x[0]['win']['e_eff_mean'], 0),
       ('game cores', lambda x: x[0]['win']['game_slope'], 2), ('game threads', lambda x: x[3]['threads_mean'], 0),
       ('game handles', lambda x: x[3]['handles_mean'], 0), ('game commit MB', lambda x: x[3]['commit_mb_mean'], 0),
       ('free RAM GB min', lambda x: x[3]['free_ram_gb_min'], 2), ('GPU MHz mean', lambda x: x[2]['gr_mean'], 0),
       ('GPU MHz min', lambda x: x[2]['gr_min'], 0), ('GPU temp C', lambda x: x[2]['temp_mean'], 1), ('GPU power W', lambda x: x[2]['power_mean'], 2),
       ('GPU util %', lambda x: x[2]['util_mean'], 1), ('GPU thermal-throttle share', lambda x: x[2]['thermal_share'], 2),
       ('pipeline misses', lambda x: x[1]['tot']['pipe'], 0), ('texture misses', lambda x: x[1]['tot']['tex'], 0),
       ('cb stalls', lambda x: x[1]['tot']['cbs'], 0), ('crit contentions', lambda x: x[1]['tot']['crit'], 0),
       ('interrupt_dispatches /s', lambda x: x[1]['tot']['intr'] / x[1]['sum_s'], 1)]


# ----------------------------------------------------------------------------- section 5, part 1 (items 1-4)
def section5(P, L, J, folders, fbs):
    X = J.setdefault('extra', {})
    RUN = {(st, r['run']): r for st in folders for r in folders[st]['runs'] if not r.get('err')}
    G, PR = {}, {}
    for k, r in RUN.items():
        try:
            G[k] = gpu_window(r)
        except Exception as ex:
            G[k] = ({'n': 0, 'err': repr(ex)}, [])
        try:
            PR[k] = proc_window(r)
        except Exception as ex:
            PR[k] = ({'n': 0, 'err': repr(ex)}, [])
    REC = {k: sec_records(RUN[k], fb, G[k][1], PR[k][1]) for k, fb in fbs.items() if k in RUN}

    def item(r):
        k = (r['stamp'], r['run'])
        return (r, fbs.get(k), G[k][0], PR[k][0])

    def ok(st):
        return [r for r in folders[st]['runs'] if not r.get('err')]

    def scored(st):
        return [r for r in ok(st) if r['scored']]

    def bins_of(st, run):
        k = (st, run)
        return bin_stats(REC[k], fbs[k]) if k in REC else []

    X['gpu_window'] = {'%s/%s' % k: v[0] for k, v in G.items()}
    X['proc_window'] = {'%s/%s' % k: v[0] for k, v in PR.items()}
    P('')
    P('## 5. Follow-up items (Agent 8, 11:57Z)')
    P('')
    P('Sources per run: sys.csv (host, 1 s), proc.csv (legodimensions.exe only, 1 s; its free_ram_gb is system-wide), gpu.csv (NVML, window only, ~1.07 s), '
      'perf.csv (per frame). **There is no per-process data for other processes and no disk counter in the matrix folders**, so a non-game process cannot be named from '
      'these files; the proxies are ng_t/ng_u (host CPU minus game), free RAM, P/E clocks, the GPU state and the game\'s own counters. Frame counts use T end '
      '(summed frame_time_us from the window start) in 10 s bins; per-second rows map each frame to the sys sample containing measure_start + T end - lag/2. '
      '"A8 >6" = Agent 8\'s count from mine/*.md, for checking. thermal % = share of GPU samples with an NVML thermal throttle bit (0x20 SW / 0x40 HW).')

    # ---- 5.1
    st = _S3
    sc = scored(st)
    P('')
    P('### 5.1 W6-2 (0313) tail episode 03:24-03:40: the 8 EP runs vs the other 12 scored runs')
    P('')
    L.extend(md(RUN_HDR, [run_row(*item(r), mark=' EP' if r['run'] in EP_0313 else '') for r in ok(st)]))
    ep = [item(r) for r in sc if r['run'] in EP_0313]
    ot = [item(r) for r in sc if r['run'] not in EP_0313]
    rows, out = grp_cmp(ep, ot, 'EP', 'other', MET)
    P('')
    P('EP (n=%d) vs other scored runs (n=%d): median [min..max], difference of medians, two-sided permutation p (5000 perms), separation:' % (len(ep), len(ot)))
    P('')
    L.extend(md(['metric', 'EP', 'other', 'diff', 'perm p', 'separation'], rows))
    allx = ep + ot
    n6 = [sg(lambda x: float(x[1]['cnt'][6.0]), x) for x in allx]
    spr = {name: SA.spearman(n6, [sg(fn, x) for x in allx], nperm=2000) for name, fn, nd in MET[3:]}
    P('')
    P('Spearman across the %d scored runs, >6 ms frame count vs: ' % len(allx) + '; '.join('%s rho %s (p %s)' % (k, f(v[0], 2), f(v[2], 3)) for k, v in spr.items()))
    ra, na = sec_compare([REC[(st, x[0]['run'])] for x in ep])
    rb, nb = sec_compare([REC[(st, r['run'])] for r in sc])
    pool = [x for r in sc for x in REC[(st, r['run'])] if x['n'] >= 50]
    rs = SA.spearman([float(x['n6']) for x in pool], [x['ngB'] for x in pool], nperm=1)
    P('')
    P('Per second (window seconds with >= 50 frames): seconds containing a >6 ms frame vs the other seconds. Pooled medians, the median of the per-run differences, '
      'runs with difference >0 / <0 and a two-sided sign test across runs (seconds within a run are autocorrelated, so no pooled p). Keys: ngB = ng_t, ngU = ng_u, '
      'gutil/gr/temp = GPU util/MHz/C, pcores = game cores (proc.csv), free = free RAM GB, intr = interrupt_dispatches summed over the frames of that second.')
    P('')
    P('EP runs (%d spike seconds, %d other seconds):' % tuple(na))
    P('')
    L.extend(md(SECCMP_HDR, ra))
    P('')
    P('All %d scored 0313 runs (%d spike seconds, %d other seconds); pooled per-second Spearman of the >6 ms count vs ng_t: rho %s (n=%s):' % (len(sc), nb[0], nb[1], f(rs[0], 3), rs[1]))
    P('')
    L.extend(md(SECCMP_HDR, rb))
    X['ep_0313'] = {'ep_runs': EP_0313, 'cmp': out, 'spearman_n6': spr, 'sec_ep': ra, 'sec_all': rb, 'nsec_ep': na, 'nsec_all': nb,
                    'sec_rho_n6_ngB': rs, 'per_run_n6': {x[0]['run']: x[1]['cnt'][6.0] for x in allx}}

    # ---- 5.2
    st = _S4
    sc = scored(st)
    P('')
    P('### 5.2 W4c (0239): 0251-B-r3 (burst at 30-40 s) and 0253-B-r4 (spread) vs the other scored runs')
    P('')
    L.extend(md(RUN_HDR, [run_row(*item(r), mark=' FOCUS' if r['run'] in W4C_FOCUS else '') for r in ok(st)]))
    rk = []
    for name, fn, nd in MET:
        vals = [(sg(fn, item(r)), r['run']) for r in sc]
        vv = sorted([v for v, _ in vals if v is not None], reverse=True)
        cell = []
        for fr_ in W4C_FOCUS:
            v = next((v for v, n in vals if n == fr_), None)
            cell.append('%s (%s)' % (f(v, nd), ('%d' % (vv.index(v) + 1)) if v is not None else '-'))
        rk.append([name] + cell + [rng_s([v for v, n in vals if n not in W4C_FOCUS], nd)])
    P('')
    P('Value (rank among the %d scored runs, 1 = highest) of each focus run, and the other runs\' median [min..max]:' % len(sc))
    P('')
    L.extend(md(['metric'] + W4C_FOCUS + ['other runs'], rk))
    X['w4c'] = {'ranks': rk}
    for fr_ in W4C_FOCUS:
        bs = bins_of(st, fr_)
        if not bs:
            continue
        P('')
        P(hot_line(fr_, bs))
        P('')
        L.extend(md(BIN_HDR, bin_rows(bs)))
        X['w4c'][fr_] = {'bins': bs, 'list6': fbs[(st, fr_)]['list6']}
    k = (st, '0251-B-r3')
    if k in REC:
        P('')
        P('0251-B-r3 per second, T 25-45 s:')
        P('')
        L.extend(md(SEC_HDR, sec_rows(REC[k], 25, 45)))
        lg, nlg = log_in(RUN[k], 25, 45)
        P('')
        P('game.log entries at T 25-45 s (%d): %s' % (nlg, ' || '.join(lg) or 'none'))
        X['w4c']['0251_sec'] = sec_rows(REC[k], 25, 45)

    # ---- 5.3
    st = _S9
    P('')
    P('### 5.3 W6-1 (0009) short bursts: 0023-p2fc-r2, 0031-s0-r3, 0037-s0-r4, 0039-p2-r4')
    P('')
    L.extend(md(RUN_HDR, [run_row(*item(r), mark=' FOCUS' if r['run'] in [z[0] for z in W61_FOCUS] else '') for r in ok(st)]))
    X['w61'] = {}
    for fr_, t0, t1 in W61_FOCUS:
        bs = bins_of(st, fr_)
        if not bs:
            continue
        P('')
        P(hot_line(fr_, bs))
        P('')
        L.extend(md(BIN_HDR, bin_rows(bs)))
        X['w61'][fr_] = {'bins': bs, 'list6': fbs[(st, fr_)]['list6']}
        if t0 is not None:
            P('')
            P('%s per second, T %d-%d s:' % (fr_, t0, t1))
            P('')
            L.extend(md(SEC_HDR, sec_rows(REC[(st, fr_)], t0, t1)))
            lg, nlg = log_in(RUN[(st, fr_)], t0, t1)
            P('')
            P('game.log entries at T %d-%d s (%d): %s' % (t0, t1, nlg, ' || '.join(lg) or 'none'))
            X['w61'][fr_]['sec'] = sec_rows(REC[(st, fr_)], t0, t1)

    # ---- 5.4
    st, fr_ = _S3, '0352-p2f-r5'
    k = (st, fr_)
    P('')
    P('### 5.4 0352-p2f-r5: the first 10 s (21 frames >6 ms per Agent 8, the 45.67 ms frame at T 7.44-7.49 s)')
    if k in REC:
        bs = bins_of(st, fr_)
        P('')
        P(hot_line(fr_, bs))
        P('')
        L.extend(md(BIN_HDR, bin_rows(bs)))
        P('')
        P('Per second, T 0-12 s:')
        P('')
        L.extend(md(SEC_HDR, sec_rows(REC[k], 0, 12)))
        lg, nlg = log_in(RUN[k], -2, 12, 40)
        P('')
        P('game.log entries at T -2..12 s (%d): %s' % (nlg, ' || '.join(lg) or 'none'))
        P('')
        P('>6 ms frames (T end s, ms): ' + ', '.join('%.2f/%.2f' % z for z in fbs[k]['list6']))
        X['spike_0352'] = {'bins': bs, 'sec': sec_rows(REC[k], 0, 12), 'list6': fbs[k]['list6'], 'log': lg}
    section5b(P, L, J, folders, fbs, RUN, G, PR, REC)


# ----------------------------------------------------------------------------- section 5, part 2 (item 5, W5b onset, warnings)
def pre_samples(r):
    out = []
    for s in r['_S']:
        if s['phase'] != 'nogame':
            break
        out.append(s)
    return out


def section5b(P, L, J, folders, fbs, RUN, G, PR, REC):
    X = J['extra']

    def ok(st):
        return [r for r in folders[st]['runs'] if not r.get('err')]

    def frel(r, st):
        if r.get('fps_rel') is not None:
            return r['fps_rel']
        base = re.sub(r'^cold-?', '', r['arm'])
        m = folders[st]['F']['arm_fps_med'].get(base)
        return (r['res_fps_mean'] / m) if (m and r.get('res_fps_mean')) else None

    P('')
    P('### 5.5 First runs after the idle gate: CPU clocks and GPU thermal state')
    P('')
    P('The quiet/idle gate is not logged in the matrix folders (runner logs hold only run-timing lines; there is no gate log), so its timing is not visible here. '
      '"gap" = previous run\'s last sys sample (for a cold run, the previous folder\'s last run) to this run\'s first sys sample. "pre" = sys samples before the game '
      'process exists (host only; busy_t = all-host busy cores). fps_rel of a cold run = its fps / the base arm\'s scored median (the cold window is 30 s from +30 s, '
      'so it is not strictly comparable). GPU values are window means (gpu.csv covers the window only).')
    hdr = ['#', 'run', 'start', 'gap s', 'pre n', 'pre busy_t', 'pre P/E MHz', 'wu P/E MHz', 'win P/E MHz', 'res eff MHz', 'fps', 'fps_rel', 'median ms',
           'GPU MHz mean (first5/last5)', 'GPU C first5/mean/max', 'GPU W', 'GPU util', 'thermal %', '>6 frames']
    prev, idle_rows, summ = None, {}, []
    for lab, st in A.MATS:
        rows = []
        R = ok(st)
        for r in R:
            k = (st, r['run'])
            gs = G[k][0]
            pre = pre_samples(r)
            gap = ((r['_S'][0]['epoch'] - r['_S'][0]['dt']) - prev['_S'][-1]['epoch']) if (prev and prev.get('_S') and r.get('_S')) else None
            fb = fbs.get(k)
            rows.append([r['idx'], r['run'] + ('' if r['scored'] else ' (unscored)'), r['start_wall'], f(gap, 0), len(pre),
                         f(mean([s.get('busyB') for s in pre])), '%s/%s' % (f(mean([s.get('p_eff') for s in pre]), 0), f(mean([s.get('e_eff') for s in pre]), 0)),
                         '%s/%s' % (f(r['wu'].get('p_eff_mean'), 0), f(r['wu'].get('e_eff_mean'), 0)),
                         '%s/%s' % (f(r['win'].get('p_eff_mean'), 0), f(r['win'].get('e_eff_mean'), 0)), f(r.get('res_eff_mhz'), 0),
                         f(r.get('res_fps_mean'), 1), f(frel(r, st), 3), f(r.get('res_median_ms'), 3),
                         '%s (%s/%s)' % (f(gs.get('gr_mean'), 0), f(gs.get('gr_first5'), 0), f(gs.get('gr_last5'), 0)),
                         '%s/%s/%s' % (f(gs.get('temp_first5'), 1), f(gs.get('temp_mean'), 1), f(gs.get('temp_max'), 0)),
                         f(gs.get('power_mean'), 2), f(gs.get('util_mean'), 1), pc(gs.get('thermal_share')), fb['cnt'][6.0] if fb else '-'])
            prev = r
        idle_rows[st] = rows
        if st in FB_STAMPS:
            P('')
            P('%s (%s):' % (lab, st))
            P('')
            L.extend(md(hdr, rows))
        e3, rest = R[:3], R[3:]
        sc = [r for r in R if r['scored']]

        def gv(rr, key):
            return [G[(st, r['run'])][0].get(key) for r in rr]
        sp1 = SA.spearman(gv(sc, 'gr_mean'), [r['fps_rel'] for r in sc], nperm=2000)
        sp2 = SA.spearman(gv(sc, 'temp_mean'), [r['fps_rel'] for r in sc], nperm=2000)
        sp3 = SA.spearman([float(r['idx']) for r in sc], [r['fps_rel'] for r in sc], nperm=2000)
        summ.append([lab, st[-4:], f(frel(R[0], st), 3), f(med([frel(r, st) for r in R[1:3]]), 3), f(med([frel(r, st) for r in rest]), 3),
                     '%s / %s / %s' % (f(gv(R[:1], 'temp_first5')[0], 1), f(med(gv(R[1:3], 'temp_first5')), 1), f(med(gv(rest, 'temp_first5')), 1)),
                     '%s / %s / %s' % (f(gv(R[:1], 'gr_mean')[0], 0), f(med(gv(R[1:3], 'gr_mean')), 0), f(med(gv(rest, 'gr_mean')), 0)),
                     '%s / %s / %s' % (pc(gv(R[:1], 'thermal_share')[0]), pc(med(gv(R[1:3], 'thermal_share'))), pc(med(gv(rest, 'thermal_share')))),
                     '%s / %s / %s' % (f(R[0]['win'].get('p_eff_mean'), 0), f(med([r['win'].get('p_eff_mean') for r in R[1:3]]), 0),
                                       f(med([r['win'].get('p_eff_mean') for r in rest]), 0)),
                     '%s (p %s)' % (f(sp1[0], 2), f(sp1[2], 3)), '%s (p %s)' % (f(sp2[0], 2), f(sp2[2], 3)), '%s (p %s)' % (f(sp3[0], 2), f(sp3[2], 3))])
    P('')
    P('All 7 folders: cold run / runs 2-3 (median) / the rest (median); Spearman over scored runs vs fps_rel:')
    P('')
    L.extend(md(['window', 'folder', 'fps_rel cold', 'fps_rel runs 2-3', 'fps_rel rest', 'GPU C first5', 'GPU MHz mean', 'GPU thermal %', 'win P MHz',
                 'rho GPU MHz vs fps_rel', 'rho GPU C vs fps_rel', 'rho run order vs fps_rel'], summ))
    X['idle_thermal'] = {'rows': idle_rows, 'summary': summ}

    # ---- 5.6 W5b onset
    P('')
    P('### 5.6 W5b-2 (0451) extra load after the CrossDeviceService holdback: timeline (W5b-1 for comparison)')
    P('')
    P('Warm-up + window sys samples of all runs in time order; baseline = median ng_t of runs 8 onwards; "above" = 30 s rolling median of ng_t > baseline + 0.5 core. '
      'pre = host-only samples before the game starts (busy_t of the whole host).')
    on = {}
    for st in ('20261123-0155', '20261123-0451'):
        R = ok(st)
        late = set(r['run'] for r in R[7:])
        smp = sorted((s['epoch'], s['ngB'], s['wall'][:8], r['run']) for r in R for s in r['_S']
                     if s['phase'] in ('warmup', 'window') and s.get('ngB') is not None)
        base = med([x[1] for x in smp if x[3] in late])
        roll, j = [], 0
        for i, x in enumerate(smp):
            while smp[j][0] < x[0] - 30:
                j += 1
            roll.append(statistics.median([y[1] for y in smp[j:i + 1]]))
        ab = [x for x, m in zip(smp, roll) if base is not None and m > base + 0.5]
        runs_ab = Counter(x[3] for x in ab)
        on[st] = {'baseline': base, 'n': len(smp), 'n_above': len(ab), 'first': ab[0][2] if ab else None, 'last': ab[-1][2] if ab else None,
                  'runs_above': dict(runs_ab)}
        P('')
        P('%s: baseline ng_t %s; above in %d of %d samples; first %s, last %s; per run: %s' % (
            st, f(base), len(ab), len(smp), on[st]['first'] or '-', on[st]['last'] or '-',
            ', '.join('%s %d' % kv for kv in sorted(runs_ab.items())) or 'none'))
        P('')
        rows = []
        for r in R[:8]:
            pre = pre_samples(r)
            rows.append([r['idx'], r['run'], r['start_wall'], len(pre), f(mean([s.get('busyB') for s in pre])), f(r['wu'].get('ngB_mean')),
                         f(r['win'].get('ngB_mean')), f(r['win'].get('ngB_max')), runs_ab.get(r['run'], 0)])
        L.extend(md(['#', 'run', 'start', 'pre n', 'pre busy_t', 'wu ng_t', 'win ng_t', 'win ng_t max', 'samples above'], rows))
    X['w5b_onset'] = on

    # ---- game.log warnings (section 4 add-on)
    P('')
    P('### 5.7 game.log warning lines (section 4 add-on): top patterns (digits/hex masked) over all 7 folders')
    P('')
    wc, wr, wf, nr = Counter(), Counter(), {}, 0
    for lab, st in A.MATS:
        for r in ok(st):
            nr += 1
            seen = set()
            for (t, lvl, cat, tid, msg) in r['log']['_entries']:
                if lvl != 'warning':
                    continue
                kk = '[%s] %s' % (cat, re.sub(r'0x[0-9a-fA-F]+|\d+', '#', msg)[:90])
                wc[kk] += 1
                wf.setdefault(kk, Counter())[lab] += 1
                seen.add(kk)
            for kk in seen:
                wr[kk] += 1
    rows = [[kk.replace('|', '/'), n, '%d/%d' % (wr[kk], nr), ' '.join('%s:%d' % (lab, wf[kk][lab]) for lab, _ in A.MATS if wf[kk][lab])]
            for kk, n in wc.most_common(12)]
    L.extend(md(['pattern', 'lines', 'runs with it', 'per folder'], rows))
    P('')
    P('%d distinct warning patterns in total; patterns present in fewer than half of the runs: %s' % (
        len(wc), '; '.join('%s (%d runs)' % (kk[:70].replace('|', '/'), wr[kk]) for kk in wc if wr[kk] < nr / 2)[:900] or 'none'))
    X['warnings'] = {'top': rows, 'n_patterns': len(wc), 'runs': nr}

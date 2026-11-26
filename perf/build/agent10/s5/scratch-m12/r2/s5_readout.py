#!/usr/bin/env python3
"""s5_readout.py - Phase 0.3 baseline read-out from s5_gates.py JSON (M12, session 3, 2026-11-25).

Descriptive, CF1 method (build/agent8/session3/confirm/readout_night.py):
  arm value     = median of run values; 95 % percentile bootstrap CI of the arm median (runs resampled, 20000, seed 1)
  contrast A:B  = median(A) - median(B), in units and % of median(B), 95 % percentile bootstrap CI (runs resampled
                  within each arm, 20000 draws, seed 1); cross-check: paired-by-round log ratio, mean and t-CI
  wording       = 'A higher' / 'A lower' when the CI excludes 0, else 'not resolved'; never 'equal'
Arms = (bin dir basename, cap arm). Contrasts: every bin vs --ref within each cap arm; uncapped vs cap60 within each
bin (info). Runs with verdict VOID are always dropped; --exclude-flagged also drops FLAG runs (sensitivity variant).
Missing arms (no runs, or all dropped) are listed as 'not run' / 'no valid runs' and their contrasts are skipped with a
note; no arm is required (matrix-s5-baseline: ship60, nat60, natU, optional native4bp at cap60).

Usage: python -B s5_readout.py GATES.json [GATES.json ...] [--ref devfinal2] [--exclude-flagged] [--json OUT]
       python -B s5_readout.py --selftest
Stdlib only.
"""
import argparse, json, math, random, re, statistics as st, sys

T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131}
METRICS = [  # key, label, source
    ('fps', 'fps', 'm'), ('median_ms', 'median ms', 'm'), ('p99_ms', 'p99 ms', 'm'), ('low1_ms', '1% low ms', 'm'),
    ('max_ms', 'max ms', 'm'), ('ge100_pm', '>=100 ms /min', 'd'), ('ge250_pm', '>=250 ms /min', 'd'),
    ('n_ge100', '>=100 ms n', 'm'), ('n_ge250', '>=250 ms n', 'm'),
    ('util_gpu', 'GPU util %', 't'), ('gr_mhz', 'GPU clock MHz', 't'), ('power_w', 'GPU W', 't'),
    ('temp_c', 'GPU temp C', 't'), ('thermal_share', 'thermal share', 't'), ('powercap_share', 'power-cap share', 't'),
    ('start_temp_c', 'start temp C', 'c'), ('nongame_mean', 'nongame cores', 'h')]
CONTRAST = ['fps', 'p99_ms', 'low1_ms', 'max_ms', 'ge100_pm', 'ge250_pm', 'util_gpu', 'gr_mhz', 'power_w', 'thermal_share']


def run_values(r):
    m, g = r.get('metrics') or {}, r['gates']
    v = {}
    for k, _, src in METRICS:
        if src == 'm':
            v[k] = m.get(k)
        elif src == 't':
            v[k] = g['thermal'].get(k)
        elif src == 'c':
            v[k] = g['cooldown'].get('start_temp_c')
        elif src == 'h':
            v[k] = g['host'].get('nongame_mean')
    ws = m.get('window_s')
    v['ge100_pm'] = m['n_ge100'] / ws * 60 if ws else None
    v['ge250_pm'] = m['n_ge250'] / ws * 60 if ws else None
    return v


def boot_med(vals, n, seed):
    rnd = random.Random(seed)
    ms = sorted(st.median([vals[rnd.randrange(len(vals))] for _ in vals]) for _ in range(n))
    return ms[int(0.025 * n)], ms[int(0.975 * n) - 1]


def boot_diff(va, vb, n, seed):
    rnd = random.Random(seed)
    ds = []
    for _ in range(n):
        ra = [va[rnd.randrange(len(va))] for _ in va]
        rb = [vb[rnd.randrange(len(vb))] for _ in vb]
        ds.append(st.median(ra) - st.median(rb))
    ds.sort()
    return ds[int(0.025 * n)], ds[int(0.975 * n) - 1]


def paired(a, b, key):
    ka = {x['round']: x['v'][key] for x in a if x['round'] is not None and x['v'].get(key) is not None}
    kb = {x['round']: x['v'][key] for x in b if x['round'] is not None and x['v'].get(key) is not None}
    common = sorted(set(ka) & set(kb))
    d = [math.log(ka[c] / kb[c]) for c in common if ka[c] > 0 and kb[c] > 0]
    if len(d) < 2:
        return None
    m, sd = st.mean(d), st.stdev(d)
    h = T975.get(len(d) - 1, 2.0) * sd / math.sqrt(len(d))
    return {'n': len(d), 'pct': (math.exp(m) - 1) * 100, 'lo': (math.exp(m - h) - 1) * 100, 'hi': (math.exp(m + h) - 1) * 100}


def fmt(v, nd=2):
    return '-' if v is None else '%.*f' % (nd, v)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('gates', nargs='*')
    p.add_argument('--ref', default='devfinal2', help='substring of the reference bin (contrast denominator)')
    p.add_argument('--exclude-flagged', action='store_true')
    p.add_argument('--round-regex', default=r'(?:^|[-_])r(\d+)(?:$|[-_])', help='round number from the run tag / dir')
    p.add_argument('--draws', type=int, default=20000)
    p.add_argument('--seed', type=int, default=1)
    p.add_argument('--json', default=None)
    p.add_argument('--selftest', action='store_true')
    a = p.parse_args(argv)
    if a.selftest:
        return selftest()
    runs = []
    for f in a.gates:
        with open(f, encoding='utf-8-sig') as fh:
            runs += json.load(fh)['runs']
    rx = re.compile(a.round_regex)
    L, arms, dropped = [], {}, []
    seen = {}  # (bin, cap) -> runs in, including dropped ones
    for r in runs:
        b = str(r.get('bin_dir') or r['renderer']).rstrip('\\/').replace('\\', '/').split('/')[-1]
        cap = r['gates']['cap'].get('arm')
        seen[(b, cap)] = seen.get((b, cap), 0) + 1
        if r['verdict'] == 'VOID' or (a.exclude_flagged and r['verdict'] == 'FLAG'):
            dropped.append((r.get('tag') or r['run_dir'], r['verdict']))
            continue
        if not r.get('metrics') or r['metrics'].get('fps') is None:
            dropped.append((r.get('tag') or r['run_dir'], 'no metrics'))
            continue
        mm = rx.search(str(r.get('tag') or '')) or rx.search(r['run_dir'].replace('\\', '/').split('/')[-1])
        arms.setdefault((b, cap), []).append({'tag': r.get('tag'), 'verdict': r['verdict'],
                                              'round': int(mm.group(1)) if mm else None, 'v': run_values(r)})
    L.append('# s5_readout: %d runs in, %d used, %d dropped (%s); variant %s; bootstrap %d draws seed %d' % (
        len(runs), sum(len(x) for x in arms.values()), len(dropped), ', '.join('%s:%s' % d for d in dropped) or '-',
        'exclude VOID+FLAG' if a.exclude_flagged else 'exclude VOID', a.draws, a.seed))
    out = {'arms': {}, 'contrasts': [], 'dropped': dropped, 'variant': 'no-flag' if a.exclude_flagged else 'all-valid'}
    for key in sorted(arms):
        rs = arms[key]
        L.append('')
        L.append('== arm %s / cap %s: n %d (%s)' % (key[0], key[1], len(rs), ' '.join('%s%s' % (x['tag'], '' if x['verdict'] == 'PASS' else '[F]') for x in rs)))
        ad = {}
        for k, lab, _ in METRICS:
            vals = [x['v'][k] for x in rs if x['v'].get(k) is not None]
            if not vals:
                continue
            med = st.median(vals)
            lo, hi = boot_med(vals, a.draws, a.seed) if len(vals) >= 2 else (None, None)
            ad[k] = {'n': len(vals), 'median': med, 'lo': lo, 'hi': hi, 'min': min(vals), 'max': max(vals)}
            L.append('  %-16s median %10s  95%% CI [%s, %s]  range %s..%s  (n %d)' % (
                lab, fmt(med, 3), fmt(lo, 3), fmt(hi, 3), fmt(min(vals), 3), fmt(max(vals), 3), len(vals)))
        out['arms']['%s|%s' % key] = ad
    # missing arms (e.g. matrix-s5-baseline has no xenos uncapped arm): reported, never required
    bins = sorted({k[0] for k in seen})
    allcaps = sorted({k[1] for k in seen if k[1] is not None} | {'60', 'none'}, key=str)
    out['missing'] = {}
    for b in bins:
        for c in allcaps:
            if (b, c) not in arms:
                why = 'not run' if (b, c) not in seen else 'no valid runs (%d in, all dropped)' % seen[(b, c)]
                out['missing']['%s|%s' % (b, c)] = why
                L.append('')
                L.append('== arm %s / cap %s: %s' % (b, c, why))
    pairs = []
    caps = sorted({k[1] for k in arms}, key=str)
    for cap in caps:
        refs = [k for k in arms if k[1] == cap and a.ref in k[0]]
        others = [k for k in sorted(arms) if k[1] == cap and a.ref not in k[0]]
        if not refs and others:
            L.append('')
            L.append('== contrast cap %s: no %s arm (%s), bin-vs-ref contrast not available for %s' % (
                cap, a.ref, 'not run' if not any(a.ref in k[0] and k[1] == cap for k in seen) else 'no valid runs',
                ', '.join(k[0] for k in others)))
        for rk in refs:
            for k in sorted(arms):
                if k[1] == cap and k != rk:
                    pairs.append((k, rk, 'bin vs ref'))
    for b in sorted({k[0] for k in arms}):
        if (b, 'none') in arms and (b, '60') in arms:
            pairs.append(((b, 'none'), (b, '60'), 'uncapped vs cap60 (info)'))
    for A, B, why in pairs:
        L.append('')
        L.append('== contrast %s/%s : %s/%s  (%s; %% of B; CI = bootstrap; paired = by round)' % (A[0], A[1], B[0], B[1], why))
        for k in CONTRAST:
            va = [x['v'][k] for x in arms[A] if x['v'].get(k) is not None]
            vb = [x['v'][k] for x in arms[B] if x['v'].get(k) is not None]
            if not va or not vb:
                continue
            ma, mb = st.median(va), st.median(vb)
            d = ma - mb
            lo, hi = boot_diff(va, vb, a.draws, a.seed) if len(va) >= 2 and len(vb) >= 2 else (None, None)
            pct = d / mb * 100 if mb else None
            plo = lo / mb * 100 if (lo is not None and mb) else None
            phi = hi / mb * 100 if (hi is not None and mb) else None
            word = 'n<2' if lo is None else ('A higher' if lo > 0 else ('A lower' if hi < 0 else 'not resolved'))
            pr = paired(arms[A], arms[B], k)
            L.append('  %-14s A %10s  B %10s  d %9s  %7s%%  CI [%s, %s]%%  %-12s paired %s' % (
                dict((m[0], m[1]) for m in METRICS)[k], fmt(ma, 3), fmt(mb, 3), fmt(d, 3), fmt(pct, 1), fmt(plo, 1), fmt(phi, 1),
                word, '-' if pr is None else 'n%d %+.1f%% [%+.1f, %+.1f]' % (pr['n'], pr['pct'], pr['lo'], pr['hi'])))
            out['contrasts'].append({'A': '%s|%s' % A, 'B': '%s|%s' % B, 'kind': why, 'metric': k, 'a': ma, 'b': mb,
                                     'd': d, 'pct': pct, 'lo_pct': plo, 'hi_pct': phi, 'word': word, 'paired': pr})
    sys.stdout.write('\n'.join(L) + '\n')
    if a.json:
        with open(a.json, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(out, f, indent=1)
            f.write('\n')
    return 0


def selftest():
    import io, contextlib, os, tempfile
    def mk(tag, b, cap, fps, verdict='PASS'):
        return {'tag': tag, 'run_dir': 'x/' + tag, 'bin_dir': 'build/agent2/' + b, 'renderer': 'x', 'verdict': verdict,
                'metrics': {'fps': fps, 'median_ms': 1000 / fps, 'p99_ms': 50.0, 'low1_ms': 80.0, 'max_ms': 300.0,
                            'n_ge100': 6, 'n_ge250': 1, 'window_s': 120.0},
                'gates': {'thermal': {'util_gpu': 90, 'gr_mhz': 1400, 'power_w': 25, 'temp_c': 85, 'thermal_share': 0.6,
                                      'powercap_share': 0.2}, 'cooldown': {'start_temp_c': 55}, 'host': {'nongame_mean': 1.0},
                          'cap': {'arm': cap}}}
    runs = []
    for i in range(1, 6):
        runs.append(mk('xen-c60-r%d' % i, 'devfinal2-bin', '60', 45 + i * 0.2))
        runs.append(mk('nat-c60-r%d' % i, 'nativefinal2-bin', '60', 55 + i * 0.2))
        runs.append(mk('nat-unc-r%d' % i, 'nativefinal2-bin', 'none', 75 + i * 0.2))
    runs.append(mk('nat-c60-r9', 'nativefinal2-bin', '60', 10, verdict='VOID'))
    # matrix-s5-baseline shape: no xenos uncapped arm; optional native4bp cap60 arm, here all VOID; a no-fps run
    runs.append(mk('n4bp-c60-r1', 'native4bp-bin', '60', 58, verdict='VOID'))
    nofps = mk('nat-c60-r8', 'nativefinal2-bin', '60', 50, verdict='FLAG')
    nofps['metrics']['fps'] = None
    runs.append(nofps)
    td = tempfile.mkdtemp(prefix='readout-selftest-', dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scratch'))
    f = os.path.join(td, 'g.json')
    with open(f, 'w') as fh:
        json.dump({'runs': runs}, fh)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        main([f, '--json', os.path.join(td, 'r.json'), '--draws', '2000'])
    with open(os.path.join(td, 'r.json')) as fh:
        o = json.load(fh)
    c = [x for x in o['contrasts'] if x['metric'] == 'fps' and x['A'] == 'nativefinal2-bin|60' and x['B'] == 'devfinal2-bin|60'][0]
    u = [x for x in o['contrasts'] if x['metric'] == 'fps' and x['kind'].startswith('uncapped')][0]
    checks = [('void + no-fps dropped', len(o['dropped']) == 3),
              ('nat vs xen fps +22.0%', abs(c['pct'] - (55.6 - 45.6) / 45.6 * 100) < 0.01 and c['word'] == 'A higher'),
              ('paired n5', c['paired'] and c['paired']['n'] == 5),
              ('p99 not resolved', [x for x in o['contrasts'] if x['metric'] == 'p99_ms' and x['A'] == c['A'] and x['B'] == c['B']][0]['word'] == 'not resolved'),
              ('uncapped vs cap60 native', u['A'] == 'nativefinal2-bin|none' and u['word'] == 'A higher'),
              ('arm CI', o['arms']['devfinal2-bin|60']['fps']['lo'] is not None),
              ('S6 Xu not run', o['missing'].get('devfinal2-bin|none') == 'not run'),
              ('S6 n4bp all dropped', str(o['missing'].get('native4bp-bin|60', '')).startswith('no valid runs')),
              ('S6 uncapped no-ref note', 'no devfinal2 arm (not run)' in buf.getvalue()),
              ('S6 no n4bp contrast', not any('native4bp' in x['A'] for x in o['contrasts']))]
    ok = all(x[1] for x in checks)
    for name, good in checks:
        print('%-28s %s' % (name, 'ok' if good else 'BAD'))
    print('SELFTEST', 'PASS' if ok else 'FAIL', td)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

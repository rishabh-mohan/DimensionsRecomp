#!/usr/bin/env python3
"""s5_confound.py - S5 P0.3 host-load confound read-out (M12). POST-HOC, NON-GATING.

M16 (window 20261125-1804) found that nongame CPU load and the effective CPU clock differ by arm: ship60 / n4bp60
runs had 5.3-7.5 nongame cores at ~1.6-1.75 GHz, nat60 runs 3.0-3.8 cores at ~2.7 GHz (MsMpEng 1.35-1.8 vs ~0.9
cores). This script reads the gates JSON (s5_gates.py --json) plus each run's sys.csv / frame csv. It never changes a
gate verdict and is not a gate.

Per run (scored, non-VOID; VOID rows are listed but not summarised):
  host: nongame_cores mean, eff_mhz mean (effective CPU clock), game_cores mean, MsMpEng cores (sys.csv top_cpu,
        'name:pid:cores;...', mean over snapshot rows, 0 when absent), top nongame processes;
  gpu:  thermal share, GPU temp, util, clock (from the gates JSON);
  per second in the scoring window (frames binned by end time, launch clock; sys.csv row t_s in [s, s+1)):
        corr(nongame, frames/s), corr(eff_mhz, frames/s);
        LOW-LOAD seconds (nongame < --low-thr, default 4.0 cores) vs HIGH-LOAD seconds: count, fps (frames / their
        frame time), median frame time.
Per arm (arm = run tag '<arm>-r<k>', else bin|cap): medians and ranges of the above, plus a confound check across
arms (nongame median spread > --ng-spread cores or eff_mhz spread > --mhz-spread %), and a POST-HOC low-load fps /
median contrast for the --vs pairs (difference of arm medians, % of B, bootstrap CI as s5_readout).

The confound statement is always printed at the top. Wording rule: no "X % slower/faster" for any arm pair
without the confound caveat; the low-load comparison selects seconds on a host variable after the fact, so it is
descriptive only (different scene mix per second, few seconds in high-load arms).

Usage: python -B s5_confound.py GATES.json [--vs A:B ...] [--low-thr 4.0] [--json OUT]
       python -B s5_confound.py --selftest
Stdlib only; imports s5_gates (axis helpers) and s5_readout (bootstrap) from this folder.
"""
import argparse, json, math, os, re, statistics as st, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s5_gates as G  # noqa: E402
import s5_readout as R  # noqa: E402

CONFOUND = ('CONFOUND (window 20261125-1804): host load and effective CPU clock varied during the window. M16 saw '
            '5.3-7.5 nongame cores at ~1.6-1.75 GHz in ship60/n4bp60 runs vs 3.0-3.8 cores at ~2.7 GHz in nat60 runs '
            '(MsMpEng 1.35-1.8 vs ~0.9 cores); the per-run table and the confound check below give the whole set. '
            'Arm fps / p99 contrasts may mix renderer effect with host load / CPU clock: do NOT state '
            '"<arm> X% slower/faster" without this caveat. The low-load section is post-hoc and non-gating.')


def frame_axis(rd):
    """Window-independent frame axis exactly as s5_gates.analyse: frame end times (launch clock) + frame times (ms)."""
    perf = G.rcsv(os.path.join(rd, 'perf.csv')) or []
    ft = [G.fnum(r.get('frame_time_us'), 0.0) / 1000.0 for r in perf]
    if not ft:
        for nm in ('native-frames.csv', 'frames.csv'):
            fr = G.rcsv(os.path.join(rd, nm))
            if fr and 'interval_ms' in fr[0]:
                ft = [G.fnum(r.get('interval_ms'), 0.0) for r in fr]
                break
    ff = None
    for r in G.rcsv(os.path.join(rd, 'input.csv')) or []:
        if r.get('cmd') == 'wait_first_frame':
            ff = G.fnum(r.get('t_s'))
            break
    acc, tend = (ff if ff is not None else 0.0), []
    for v in ft:
        acc += v / 1000.0
        tend.append(acc)
    return tend, ft


def corr(a, b):
    if len(a) < 3:
        return None
    ma, mb = st.mean(a), st.mean(b)
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((y - mb) ** 2 for y in b)
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(va * vb) if va and vb else None


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def subset(fts):
    if not fts:
        return {'frames': 0, 'fps': None, 'median_ms': None}
    tot = sum(fts) / 1000.0
    return {'frames': len(fts), 'fps': len(fts) / tot if tot else None, 'median_ms': st.median(fts)}


def analyse_run(r, a):
    rd = r['run_dir']
    sp = r['gates'].get('span') or {}
    win = sp.get('window')
    th = r['gates'].get('thermal') or {}
    out = {'tag': r.get('tag'), 'verdict': r['verdict'], 'run_dir': rd,
           'thermal_share': th.get('thermal_share'), 'temp_c': th.get('temp_c'), 'util_gpu': th.get('util_gpu'),
           'gr_mhz': th.get('gr_mhz'), 'fps_gate': (r.get('metrics') or {}).get('fps'), 'notes': []}
    if not win:
        out['notes'].append('no window in gates JSON')
        return out
    T0, T1 = float(win[0]), float(win[1])
    tend, ft = frame_axis(rd)
    # gates JSON rounds the window to 0.01 s: allow 0.0051 s at both ends
    wi = [i for i in range(len(ft)) if tend[i] - ft[i] / 1000.0 >= T0 - 0.0051 and tend[i] <= T1 + 0.0051]
    gf = (r.get('metrics') or {}).get('frames')
    out['frames'] = len(wi)
    if gf is not None and abs(len(wi) - gf) > 2:
        out['notes'].append('window frames %d != gates %d (axis mismatch; per-second numbers unreliable)' % (len(wi), gf))
    sysr = G.rcsv(os.path.join(rd, 'sys.csv'))
    if not sysr:
        out['notes'].append('no sys.csv')
        return out
    rows = [x for x in sysr if G.fnum(x.get('t_s')) is not None and T0 <= G.fnum(x.get('t_s')) <= T1]
    out['sys_rows'] = len(rows)
    out['nongame'] = mean([G.fnum(x.get('nongame_cores')) for x in rows])
    out['eff_mhz'] = mean([G.fnum(x.get('eff_mhz')) for x in rows])
    out['game_cores'] = mean([G.fnum(x.get('game_cores')) for x in rows])
    procs, snaps = {}, 0
    for x in rows:
        tc = x.get('top_cpu') or ''
        if not tc:
            continue
        snaps += 1
        for it in tc.split(';'):
            p = it.rsplit(':', 2)
            if len(p) == 3 and G.fnum(p[2]) is not None:
                nm = p[0].strip()
                procs[nm] = procs.get(nm, 0.0) + G.fnum(p[2])
    out['top_snaps'] = snaps
    out['msmpeng'] = (sum(v for k, v in procs.items() if k.lower().startswith('msmpeng')) / snaps) if snaps else None
    out['top'] = [(k, round(v / snaps, 2)) for k, v in sorted(procs.items(), key=lambda kv: -kv[1])[:6]] if snaps else []
    if 'eff_mhz' not in (sysr[0] or {}):
        out['notes'].append('sys.csv has no eff_mhz column')
    # per second: frames by end-time second; sys row per second (t_s in [s, s+1))
    sec_ng, sec_mhz = {}, {}
    for x in rows:
        t = G.fnum(x.get('t_s'))
        s = int(math.floor(t))
        sec_ng[s] = G.fnum(x.get('nongame_cores'))
        sec_mhz[s] = G.fnum(x.get('eff_mhz'))
    per = {}
    for i in wi:
        per.setdefault(int(math.floor(tend[i])), []).append(ft[i])
    full = [s for s in per if s >= math.ceil(T0) and s + 1 <= T1]  # whole seconds inside the window only
    pairs = [(sec_ng[s], sec_mhz.get(s), len(per[s])) for s in full if sec_ng.get(s) is not None]
    out['corr_ng_fps'] = corr([p[0] for p in pairs], [p[2] for p in pairs])
    pm = [p for p in pairs if p[1] is not None]
    out['corr_mhz_fps'] = corr([p[1] for p in pm], [p[2] for p in pm])
    lo_ft = [v for s in full if sec_ng.get(s) is not None and sec_ng[s] < a.low_thr for v in per[s]]
    hi_ft = [v for s in full if sec_ng.get(s) is not None and sec_ng[s] >= a.low_thr for v in per[s]]
    out['low_secs'] = sum(1 for s in full if sec_ng.get(s) is not None and sec_ng[s] < a.low_thr)
    out['high_secs'] = sum(1 for s in full if sec_ng.get(s) is not None and sec_ng[s] >= a.low_thr)
    out['low'] = subset(lo_ft)
    out['high'] = subset(hi_ft)
    return out


def arm_of(r):
    m = re.match(r'^(.+)-r(\d+)$', str(r.get('tag') or ''))
    if m:
        return m.group(1)
    b = str(r.get('bin_dir') or r.get('renderer')).rstrip('\\/').replace('\\', '/').split('/')[-1]
    return '%s|%s' % (b, (r['gates'].get('cap') or {}).get('arm'))


def f(v, nd=2):
    return '-' if v is None else '%.*f' % (nd, v)


COLS = [('nongame', 'nongame cores', 2), ('eff_mhz', 'eff CPU MHz', 0), ('msmpeng', 'MsMpEng cores', 2),
        ('game_cores', 'game cores', 2), ('thermal_share', 'thermal share', 2), ('temp_c', 'GPU temp C', 1),
        ('fps_gate', 'fps (gate window)', 2), ('low_fps', 'low-load fps', 2), ('low_med', 'low-load median ms', 2),
        ('low_share', 'low-load sec share', 2), ('high_fps', 'high-load fps', 2), ('corr_ng_fps', 'corr(ng, fps/s)', 2)]


def flat(x):
    lo, hi = x.get('low') or {}, x.get('high') or {}
    ns = (x.get('low_secs') or 0) + (x.get('high_secs') or 0)
    return dict(x, low_fps=lo.get('fps'), low_med=lo.get('median_ms'), high_fps=hi.get('fps'),
                low_share=(x.get('low_secs') or 0) / ns if ns else None)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('gates', nargs='*')
    p.add_argument('--vs', action='append', default=[], metavar='A:B', help='post-hoc low-load contrast, arm A vs arm B')
    p.add_argument('--low-thr', type=float, default=4.0, help='low-load second: nongame_cores < this')
    p.add_argument('--ng-spread', type=float, default=1.0, help='confound check: arm nongame medians differ by > this')
    p.add_argument('--mhz-spread', type=float, default=10.0, help='confound check: arm eff_mhz medians differ by > this %%')
    p.add_argument('--unscored-tag', default=r'^(?:cold-|warm\d+-)')
    p.add_argument('--draws', type=int, default=20000)
    p.add_argument('--seed', type=int, default=1)
    p.add_argument('--json', default=None)
    p.add_argument('--selftest', action='store_true')
    a = p.parse_args(argv)
    if a.selftest:
        return selftest()
    runs = []
    for fn in a.gates:
        with open(fn, encoding='utf-8-sig') as fh:
            runs += json.load(fh)['runs']
    un = re.compile(a.unscored_tag)
    L = ['# s5_confound (POST-HOC, NON-GATING): low-load second = nongame < %.1f cores; gates JSON %s' % (a.low_thr, ', '.join(a.gates)),
         '# ' + CONFOUND, '']
    per, arms = [], {}
    for r in runs:
        if un.search(str(r.get('tag') or '')):
            continue
        x = flat(analyse_run(r, a))
        x['arm'] = arm_of(r)
        per.append(x)
        if r['verdict'] != 'VOID':
            arms.setdefault(x['arm'], []).append(x)
    L.append('== per run (VOID runs listed, not summarised)')
    L.append('  %-14s %-6s ' % ('run', 'verd') + ' '.join('%10s' % c[1][:10] for c in COLS) + '  top nongame (cores)')
    for x in sorted(per, key=lambda x: (x['arm'], str(x['tag']))):
        L.append('  %-14s %-6s ' % (x['tag'], x['verdict']) + ' '.join('%10s' % f(x.get(c[0]), c[2]) for c in COLS) +
                 '  ' + ', '.join('%s %.2f' % t for t in x.get('top') or []))
        for n in x['notes']:
            L.append('     note: %s' % n)
    L.append('')
    L.append('== per arm (non-VOID runs): median [range] (n)')
    summ = {}
    for arm in sorted(arms):
        xs = arms[arm]
        summ[arm] = {}
        cells = []
        for k, lab, nd in COLS:
            v = [x.get(k) for x in xs if x.get(k) is not None]
            if v:
                summ[arm][k] = {'median': st.median(v), 'min': min(v), 'max': max(v), 'n': len(v)}
                cells.append('%s %s [%s..%s]' % (lab, f(st.median(v), nd), f(min(v), nd), f(max(v), nd)))
        L.append('  %-8s n %d: %s' % (arm, len(xs), '; '.join(cells)))
    # confound check across arms
    L.append('')
    ngm = {k: v['nongame']['median'] for k, v in summ.items() if 'nongame' in v}
    mhz = {k: v['eff_mhz']['median'] for k, v in summ.items() if 'eff_mhz' in v}
    flags = []
    if len(ngm) >= 2 and max(ngm.values()) - min(ngm.values()) > a.ng_spread:
        flags.append('nongame medians differ by %.2f cores (> %.1f): %s' % (
            max(ngm.values()) - min(ngm.values()), a.ng_spread, ', '.join('%s %.2f' % kv for kv in sorted(ngm.items()))))
    if len(mhz) >= 2 and min(mhz.values()) > 0 and (max(mhz.values()) / min(mhz.values()) - 1) * 100 > a.mhz_spread:
        flags.append('eff CPU MHz medians differ by %.0f%% (> %.0f%%): %s' % (
            (max(mhz.values()) / min(mhz.values()) - 1) * 100, a.mhz_spread, ', '.join('%s %.0f' % kv for kv in sorted(mhz.items()))))
    L.append('== confound check: %s' % ('PRESENT - ' + '; '.join(flags) if flags else
                                       ('not detected in this set (spreads within %.1f cores / %.0f%%)' % (a.ng_spread, a.mhz_spread)
                                        if ngm else 'no host data')))
    # post-hoc low-load contrasts
    cons = []
    for spec in a.vs:
        A, _, B = spec.partition(':')
        L.append('')
        if A not in arms or B not in arms:
            L.append('== post-hoc low-load %s vs %s: not available (arm missing)' % (A, B))
            continue
        L.append('== POST-HOC low-load contrast %s vs %s (seconds with nongame < %.1f only; non-gating, descriptive; %% of B)' % (A, B, a.low_thr))
        for k, lab in (('low_fps', 'low-load fps'), ('low_med', 'low-load median ms'), ('fps_gate', 'all-seconds fps')):
            va = [x[k] for x in arms[A] if x.get(k) is not None]
            vb = [x[k] for x in arms[B] if x.get(k) is not None]
            if not va or not vb:
                L.append('  %-20s n/a (A n %d, B n %d)' % (lab, len(va), len(vb)))
                continue
            ma, mb = st.median(va), st.median(vb)
            lo, hi = R.boot_diff(va, vb, a.draws, a.seed) if len(va) >= 2 and len(vb) >= 2 else (None, None)
            pct = (ma - mb) / mb * 100 if mb else None
            word = 'n<2' if lo is None else ('A higher' if lo > 0 else ('A lower' if hi < 0 else 'not resolved'))
            L.append('  %-20s A %8s  B %8s  d %+.3f  %s%%  CI [%s, %s]%%  %s  (low-load secs A %s / B %s)' % (
                lab, f(ma, 3), f(mb, 3), ma - mb, f(pct, 1), f(lo / mb * 100 if lo is not None and mb else None, 1),
                f(hi / mb * 100 if hi is not None and mb else None, 1), word,
                sum(x.get('low_secs') or 0 for x in arms[A]), sum(x.get('low_secs') or 0 for x in arms[B])))
            cons.append({'A': A, 'B': B, 'metric': k, 'a': ma, 'b': mb, 'pct': pct, 'lo': lo, 'hi': hi, 'word': word})
    L.append('')
    L.append('# wording: report the arm contrasts from s5_readout together with the confound check above; the low-load '
             'rows are post-hoc (selection on a host variable, different scene mix, few low-load seconds in loaded arms).')
    sys.stdout.write('\n'.join(L) + '\n')
    if a.json:
        with open(a.json, 'w', encoding='utf-8', newline='\n') as fh:
            json.dump({'confound_statement': CONFOUND, 'low_thr': a.low_thr, 'runs': per, 'arms': summ,
                       'confound_flags': flags, 'posthoc_lowload': cons}, fh, indent=1, default=str)
            fh.write('\n')
    return 0


def selftest():
    import io, contextlib, csv, tempfile
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scratch')
    os.makedirs(base, exist_ok=True)
    td = tempfile.mkdtemp(prefix='confound-selftest-', dir=base)
    ga = G.parser().parse_args(['--span', '120', '--cap', 'auto'])
    def d3(t):
        return 220 if t < 82 else (790 if t < 105 else (3000 + 1500 * (int(t / 7) % 3) if t < 275 else 766))
    def mk(name, loaded, busy_ng, quiet_ng, mhz_busy, mhz_quiet, msmp):
        # frames: 30 ms in 'busy' seconds (int(t) % 20 >= 10 when loaded, never otherwise), else 20 ms
        st_ = {'t': 3.5}
        def busy(t):
            return loaded and int(t) % 20 >= 10
        def ftf(i):
            v = 30.0 if busy(st_['t']) else 20.0
            st_['t'] += v / 1000.0
            return v
        rd = os.path.join(td, name)
        G._mk(rd, d3, n=12000, ft_fn=ftf, run_extra={'tag': name, 'effective_cap': 60})
        n = int(st_['t']) + 1
        with open(os.path.join(rd, 'sys.csv'), 'w', newline='') as fh:
            w = csv.writer(fh)
            w.writerow(['t_s', 'epoch_s', 'idle_s', 'fg_game', 'game_alive', 'screensaver', 'ac', 'batt_saver', 'scheme',
                        'overlay', 'nongame_cores', 'game_cores', 'eff_mhz', 'top_cpu'])
            for s in range(n):
                b = busy(s + 0.5)
                w.writerow([s + 0.5, 1000.0 + s, 100 + s, 1, 1, 0, 1, 0, 'Balanced', 'best', busy_ng if b else quiet_ng, 2.0,
                            mhz_busy if b else mhz_quiet,
                            'MsMpEng:4242:%.2f;node:77:0.50;System:4:0.10' % msmp])
        return rd
    rds = [mk('ship60-r1', True, 7.0, 3.0, 1600, 2700, 1.6), mk('ship60-r2', True, 6.5, 3.5, 1650, 2700, 1.5),
           mk('nat60-r1', False, 3.2, 3.2, 2700, 2700, 0.9), mk('nat60-r2', False, 3.4, 3.4, 2700, 2700, 0.9),
           mk('cold-nat60', False, 3.0, 3.0, 2700, 2700, 0.9)]
    rs = [G.analyse(rd, ga) for rd in rds]
    G.set_rules(rs, ga)
    gj = os.path.join(td, 'g.json')
    with open(gj, 'w') as fh:
        json.dump({'runs': rs}, fh, default=str)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        main([gj, '--vs', 'ship60:nat60', '--json', os.path.join(td, 'c.json'), '--draws', '2000'])
    txt = buf.getvalue()
    with open(os.path.join(td, 'c.json')) as fh:
        o = json.load(fh)
    pr = {x['tag']: x for x in o['runs']}
    s1 = pr.get('ship60-r1', {})
    lowc = [c for c in o['posthoc_lowload'] if c['metric'] == 'low_fps']
    allc = [c for c in o['posthoc_lowload'] if c['metric'] == 'fps_gate']
    checks = [
        ('confound statement printed', 'CONFOUND' in txt.splitlines()[1]),
        ('cold run skipped', 'cold-nat60' not in pr),
        ('verdicts not VOID', all(x['verdict'] != 'VOID' for x in o['runs'])),
        ('frames match gates', not any('mismatch' in n for x in o['runs'] for n in x['notes'])),
        ('MsMpEng parsed', s1.get('msmpeng') is not None and abs(s1['msmpeng'] - 1.6) < 1e-6),
        ('nongame mean ~5', s1.get('nongame') is not None and 4.6 < s1['nongame'] < 5.4),
        ('eff MHz mean ~2150', s1.get('eff_mhz') is not None and 2000 < s1['eff_mhz'] < 2300),
        ('low-load fps ~50', s1.get('low', {}).get('fps') is not None and 49 < s1['low']['fps'] < 51),
        ('high-load fps ~33', s1.get('high', {}).get('fps') is not None and 32 < s1['high']['fps'] < 35),
        ('corr(ng, fps) < -0.9', s1.get('corr_ng_fps') is not None and s1['corr_ng_fps'] < -0.9),
        ('confound PRESENT', any('nongame' in fl for fl in o['confound_flags']) and any('MHz' in fl for fl in o['confound_flags'])),
        ('all-seconds ship lower', bool(allc) and allc[0]['word'] == 'A lower'),
        ('low-load ship ~ nat', bool(lowc) and abs(lowc[0]['pct']) < 2.0),
        ('top procs', s1.get('top') and s1['top'][0][0] == 'MsMpEng'),
    ]
    ok = all(c[1] for c in checks)
    for name, good in checks:
        print('%-28s %s' % (name, 'ok' if good else 'BAD'))
    if not ok:
        print(txt)
    print('SELFTEST', 'PASS' if ok else 'FAIL', td)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""M8 night read-out (2026-11-25). Read-only on run-matrix pass dirs; stdlib only; BelowNormal.

Usage: python -B readout_night.py --name WC --base s0 --contrast win3:s0 ... [--min-round 2] [--json OUT] PASSDIR...

Kept runs: scored, status OK, valid_timing True, excluded False, round >= --min-round.
Per run: median_ms / p99_ms (frames.json, nearest rank), 1% low (mean of the slowest 1 % frame times in the perf.csv
window, re-read from perf.csv; checked against frames.json median), fps_mean, process cores (window mean), eff/P/E MHz
(sys.json window), TimerQueue busy % (threads.csv, window), slow state (sys.csv e_eff_mhz < 800 for >= 3 rows in the
window), flags_info.
Contrast A:B: difference of the arm medians of the run values (A - B), in ms and % of B, 95 % percentile bootstrap CI
(runs resampled within each arm, 20000 draws, seed 1). Also the paired-by-round log ratio (mean, t-CI) as a cross-check.
"""
import argparse, csv, json, math, os, random, statistics as st, sys

sys.dont_write_bytecode = True
try:
    import ctypes
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
except Exception:
    pass

T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
        21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060, 26: 2.056}


def jload(p):
    with open(p, encoding='utf-8-sig') as f:
        return json.load(f)


def truthy(v):
    return str(v).strip().lower() in ('true', '1', 'yes')


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def perf_window(rd, fj):
    """frame times (ms) of the frames.json window (its file/column/scale), data rows counted from 0 after the header."""
    w = fj['window']
    first, n = w['first_row'], w['rows']
    scale = float(fj.get('scale_to_us') or 1.0) / 1000.0
    path = fj.get('file') or os.path.join(rd, 'perf.csv')
    if not os.path.exists(path):
        path = os.path.join(rd, os.path.basename(path))
    out = []
    with open(path, encoding='utf-8-sig', newline='') as f:
        r = csv.reader(f)
        hdr = next(r)
        ci = hdr.index(fj.get('column') or 'frame_time_us')
        for i, row in enumerate(r):
            if i < first:
                continue
            if i >= first + n:
                break
            out.append(float(row[ci]) * scale)
    return out


def nearest(sorted_v, p):
    return sorted_v[max(0, math.ceil(p * len(sorted_v)) - 1)]


def threads_tq(rd):
    p = os.path.join(rd, 'threads.csv')
    if not os.path.exists(p):
        return None
    best = None
    with open(p, encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            if 'TimerQueue' in (row.get('name') or ''):
                b = fnum(row.get('busy_pct'))
                if b is not None and (best is None or b > best):
                    best = b
    return best


def slow_state(rd, j):
    p = os.path.join(rd, 'sys.csv')
    s = j.get('sys') or {}
    a, b = s.get('window_start_epoch'), s.get('window_end_epoch')
    if not os.path.exists(p) or a is None:
        return None
    run, mx = 0, 0
    with open(p, encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            ep = fnum(row.get('epoch_s'))
            if ep is None or ep < a or ep > b:
                continue
            e = fnum(row.get('e_eff_mhz'))
            run = run + 1 if (e is not None and e < 800) else 0
            mx = max(mx, run)
    return mx


def load(passes, min_round):
    runs = []
    for pi, d in enumerate(passes):
        with open(os.path.join(d, 'results.csv'), encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
        # slot = position of the run within its round (order of seq)
        byround = {}
        for r in rows:
            byround.setdefault(r['round'], []).append(r)
        for rr in byround.values():
            rr.sort(key=lambda x: int(x['seq']))
            for k, x in enumerate(rr, 1):
                x['_slot'] = k
        for r in rows:
            rd = r['run_dir']
            j = jload(os.path.join(rd, 'run.json'))
            fj = j['frames']
            rec = dict(pass_i=pi + 1, pass_dir=os.path.basename(d), seq=int(r['seq']), round=int(r['round']),
                       arm=r['arm'], slot=r['_slot'], name=os.path.basename(rd), scored=truthy(r['scored']),
                       status=r['status'], valid=truthy(r['valid_timing']), excluded=truthy(r['excluded']),
                       flags_info=r['flags_info'], flags_ex=r['flags_excluding'], exit_code=j.get('exit_code'),
                       wer=j.get('werfault_seen'), dumps=len(j.get('foreign_crash_dumps') or []) + len(j.get('artifacts') or []),
                       start=j.get('start'), bin=os.path.basename(j.get('bin_dir') or ''))
            rec['kept'] = rec['scored'] and rec['status'] == 'OK' and rec['valid'] and not rec['excluded'] and rec['round'] >= min_round
            rec['median'] = fj['median_ms']
            rec['p99'] = fj['p99_ms']
            rec['fps'] = fj['mean_fps']
            rec['light'] = fj.get('share_lt_light')
            rec['cores'] = j.get('window_cpu_cores_mean')
            sw = ((j.get('sys') or {}).get('window') or {})
            rec['eff'] = sw.get('eff_mhz_mean', fnum(r.get('eff_mhz')))
            rec['p_eff'] = sw.get('p_eff_mhz_mean')
            rec['e_eff'] = sw.get('e_eff_mhz_mean')
            ft = perf_window(rd, fj)
            s = sorted(ft)
            chk = abs(nearest(s, 0.5) - fj['median_ms']) < 0.0015 and abs(nearest(s, 0.99) - fj['p99_ms']) < 0.0015
            k = max(1, len(s) // 100)
            worst = s[-k:]
            rec['low1_ms'] = sum(worst) / len(worst)
            rec['low1_fps'] = 1000.0 / rec['low1_ms']
            rec['win_check'] = chk
            rec['over8'] = sum(1 for x in s if x > 8.0)
            rec['tq'] = threads_tq(rd)
            rec['slow_rows'] = slow_state(rd, j)
            gl = os.path.join(rd, 'game.log')
            stuck = 0
            if os.path.exists(gl):
                with open(gl, encoding='utf-8', errors='replace') as f:
                    stuck = sum(1 for ln in f if 'STUCK' in ln.upper())
            rec['stuck'] = stuck
            runs.append(rec)
    return runs


def boot_diff(a, b, key, n=20000, seed=1):
    va, vb = [x[key] for x in a], [x[key] for x in b]
    ma, mb = st.median(va), st.median(vb)
    rnd = random.Random(seed)
    ds = []
    for _ in range(n):
        ra = [va[rnd.randrange(len(va))] for _ in va]
        rb = [vb[rnd.randrange(len(vb))] for _ in vb]
        ds.append(st.median(ra) - st.median(rb))
    ds.sort()
    lo, hi = ds[int(0.025 * n)], ds[int(0.975 * n) - 1]
    return ma, mb, ma - mb, lo, hi


def paired(a, b, key):
    ka = {(x['pass_i'], x['round']): x[key] for x in a}
    kb = {(x['pass_i'], x['round']): x[key] for x in b}
    common = sorted(set(ka) & set(kb))
    d = [math.log(ka[c] / kb[c]) for c in common]
    if len(d) < 2:
        return None
    m, sd = st.mean(d), st.stdev(d)
    t = T975.get(len(d) - 1, 2.0)
    h = t * sd / math.sqrt(len(d))
    neg = sum(1 for x in d if x < 0)
    return len(d), (math.exp(m) - 1) * 100, (math.exp(m - h) - 1) * 100, (math.exp(m + h) - 1) * 100, neg


def fmt(v, nd=3):
    return '-' if v is None else ('%.*f' % (nd, v))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', required=True)
    ap.add_argument('--base', required=True)
    ap.add_argument('--contrast', action='append', default=[])
    ap.add_argument('--min-round', type=int, default=1)
    ap.add_argument('--drop-flag', default='')
    ap.add_argument('--drop', default='')
    ap.add_argument('--json')
    ap.add_argument('passes', nargs='+')
    a = ap.parse_args()
    runs = load(a.passes, a.min_round)
    if a.drop_flag:
        for r in runs:
            if a.drop_flag in r['flags_info'].split(';') or a.drop_flag in r['flags_info']:
                r['kept'] = False
    for r in runs:
        if r['name'] in a.drop.split(','):
            r['kept'] = False
    kept = [r for r in runs if r['kept']]
    arms = []
    for r in runs:
        if r['arm'] not in arms:
            arms.append(r['arm'])
    by = {x: [r for r in kept if r['arm'] == x] for x in arms}
    print('## %s (min round %d%s%s)' % (a.name, a.min_round, ', drop flag ' + a.drop_flag if a.drop_flag else '',
                                        ', drop ' + a.drop if a.drop else ''))
    print('passes: ' + ', '.join(os.path.basename(p) for p in a.passes))
    print('runs %d, kept %d; window re-read check fails: %d' % (len(runs), len(kept), sum(1 for r in runs if not r['win_check'])))
    print()
    print('| arm | n | median ms | p99 ms | 1%% low ms (fps) | fps mean | cores | eff MHz (P/E) | TimerQueue busy %% max | slow rows max | STUCK | >8ms frames |')
    print('|---|---|---|---|---|---|---|---|---|---|---|---|')
    for x in arms:
        v = by[x]
        if not v:
            print('| %s | 0 |' % x)
            continue
        md = lambda k: st.median([r[k] for r in v])
        mn = lambda k: st.mean([r[k] for r in v if r[k] is not None]) if any(r[k] is not None for r in v) else None
        tqs = [r['tq'] for r in v if r['tq'] is not None]
        sls = [r['slow_rows'] for r in v if r['slow_rows'] is not None]
        print('| %s | %d | %.3f | %.3f | %.3f (%.0f) | %.1f | %.2f | %.0f (%s/%s) | %s | %s | %d | %d |' % (
            x, len(v), md('median'), md('p99'), md('low1_ms'), md('low1_fps'), mn('fps'), mn('cores'), mn('eff'),
            fmt(mn('p_eff'), 0), fmt(mn('e_eff'), 0), fmt(max(tqs) if tqs else None, 1), max(sls) if sls else '-',
            sum(r['stuck'] for r in v), sum(r['over8'] for r in v)))
    print()
    cons = a.contrast or ['%s:%s' % (x, a.base) for x in arms if x != a.base]
    print('| contrast | metric | A | B | A-B | % of B | 95% bootstrap CI (%) | excl. 0 | paired-round mean % [t-CI] (A<B rounds) |')
    print('|---|---|---|---|---|---|---|---|---|')
    out = {'name': a.name, 'contrasts': []}
    for c in cons:
        A, B = c.split(':')
        if not by.get(A) or not by.get(B):
            continue
        for key, lab in (('median', 'median ms'), ('fps', 'fps mean'), ('p99', 'p99 ms'), ('low1_ms', '1% low ms'),
                         ('cores', 'cores')):
            ma, mb, d, lo, hi = boot_diff(by[A], by[B], key)
            pr = paired(by[A], by[B], key)
            pct = d / mb * 100
            ex = 'yes' if (lo > 0 or hi < 0) else 'no'
            prs = '-' if pr is None else '%+.1f [%+.1f, %+.1f] (%d/%d)' % (pr[1], pr[2], pr[3], pr[4], pr[0])
            print('| %s vs %s | %s | %.3f | %.3f | %+.3f | %+.1f | [%+.1f, %+.1f] | %s | %s |' % (
                A, B, lab, ma, mb, d, pct, lo / mb * 100, hi / mb * 100, ex, prs))
            out['contrasts'].append(dict(A=A, B=B, metric=key, a=ma, b=mb, d=d, pct=pct, lo=lo / mb * 100,
                                         hi=hi / mb * 100, paired=pr))
    print()
    # order effects: residual of ln(median) vs the arm mean, by slot / pass / round
    am = {x: st.mean([math.log(r['median']) for r in by[x]]) for x in arms if by[x]}
    for r in kept:
        r['res'] = (math.exp(math.log(r['median']) - am[r['arm']]) - 1) * 100
    def grp(k):
        g = {}
        for r in kept:
            g.setdefault(r[k], []).append(r['res'])
        return ' '.join('%s:%+.1f%%(n%d)' % (kk, st.mean(vv), len(vv)) for kk, vv in sorted(g.items()))
    print('order effects (mean residual of run median vs its arm mean): slot ' + grp('slot'))
    print('  pass ' + grp('pass_i') + ';  round ' + grp('round'))
    effs = [(r['eff'], r['res']) for r in kept if r['eff']]
    if len(effs) > 2:
        mx_, my_ = st.mean(e for e, _ in effs), st.mean(q for _, q in effs)
        sxy = sum((e - mx_) * (q - my_) for e, q in effs)
        sxx = sum((e - mx_) ** 2 for e, _ in effs)
        syy = sum((q - my_) ** 2 for _, q in effs)
        rr = sxy / math.sqrt(sxx * syy) if sxx and syy else float('nan')
        print('  clock: corr(eff MHz, residual) r = %.2f over %d runs; slope %.2f %%/100 MHz' % (rr, len(effs), sxy / sxx * 100 if sxx else float('nan')))
    print()
    print('<details><summary>per-run</summary>')
    print()
    print('| pass | run | arm | rnd | slot | kept | median | p99 | 1% low ms | >8ms | cores | eff (P/E) | TQ % | slow | exit | WER | dumps | STUCK | flags_info |')
    print('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    for r in runs:
        print('| %d | %s | %s | %d | %d | %s | %.3f | %.3f | %.3f | %d | %s | %s (%s/%s) | %s | %s | %s | %s | %d | %d | %s |' % (
            r['pass_i'], r['name'], r['arm'], r['round'], r['slot'], 'Y' if r['kept'] else '-', r['median'], r['p99'],
            r['low1_ms'], r['over8'], fmt(r['cores'], 2), fmt(r['eff'], 0), fmt(r['p_eff'], 0), fmt(r['e_eff'], 0), fmt(r['tq'], 1),
            r['slow_rows'], r['exit_code'], r['wer'], r['dumps'], r['stuck'], r['flags_info']))
    print()
    print('</details>')
    print()
    if a.json:
        out['runs'] = runs
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=1, default=str)


if __name__ == '__main__':
    main()

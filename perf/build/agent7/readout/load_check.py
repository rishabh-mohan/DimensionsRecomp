#!/usr/bin/env python3
"""load_check.py: host-load checks behind the W9 / W5b formal read-outs (read-only, stdlib only).

Inputs, all read-only:
  - build/agent7/readout/pool-W9.md and pool-W5b.md: the section 8 run tables written by pool_readout.py
    (per-run raw / T-std median ms, raw fps, cores, thread busy %, sys.json eff MHz);
  - Agent 8's build/agent8/readout/w-followup/audit/audit.md, section 2: ng_t = non-game busy cores
    (window mean, sys.csv) per run.
Output: markdown (stdout, or -o FILE).

What it prints:
  0. per pass: the ng_t spread of the kept runs and Spearman rho(ng_t, raw fps) with a t-approximation p;
  1. per run with ng_t >= 2.8: fps / median ms / cores vs the same arm's runs with ng_t < 2.8 (medians),
     plus the cores a constant core x MHz product would give at the run's clock (q / d11t / d11p arms);
  2. thread cycles (busy % x eff GHz) of the Main and GPU Commands threads by group (W9);
  3. pooled linear CIs of cores differences between arms (df = runs - arms), for the read-out variants;
  4. paired per-round sign counts used in the read-outs (all rounds, without each pass's round 1, and
     without the rounds that hold a flagged run).
Usage: python -B build/agent7/readout/load_check.py -o build/agent7/readout/load-check.md
"""
import math
import os
import re
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
AUDIT = os.path.join(ROOT, 'build', 'agent8', 'readout', 'w-followup', 'audit', 'audit.md')
POOL = {'W9': os.path.join(HERE, 'pool-W9.md'), 'W5b': os.path.join(HERE, 'pool-W5b.md')}
LOADED = 2.8  # ng_t at or above this = a loaded run (folder medians 2.37-2.58, audit.md section 2)


def below_normal():
    if os.name == 'nt':
        try:
            import ctypes
            k = ctypes.windll.kernel32
            k.SetPriorityClass(k.GetCurrentProcess(), 0x4000)  # BELOW_NORMAL_PRIORITY_CLASS
        except Exception:
            pass


def fnum(s):
    try:
        return float(s)
    except ValueError:
        return None


def pool_runs(path):
    rows, in8 = [], False
    with open(path, encoding='utf-8') as fh:
        for ln in fh:
            if ln.startswith('## '):
                in8 = ln.startswith('## 8.')
                continue
            if not in8 or not ln.startswith('|'):
                continue
            c = [x.strip() for x in ln.strip().strip('|').split('|')]
            if not c[0].isdigit():
                continue
            rows.append({'seq': int(c[0]), 'pass': int(c[1]), 'round': c[2], 'arm': c[3], 'run': c[4],
                         'start': c[5], 'kept': c[6].startswith('yes'), 'frames': int(c[7]),
                         'raw_med': float(c[8]), 't_med': float(c[9]), 'fps': float(c[10]), 'p99': float(c[11]),
                         'cores': float(c[12]), 'main': fnum(c[13]), 'gpu': fnum(c[14]), 'tq': fnum(c[15]),
                         'eff': float(c[16]), 'eutil': float(c[20])})
    return rows


def audit_ngt(path):
    ng = {}
    with open(path, encoding='utf-8') as fh:
        for ln in fh:
            if not ln.startswith('|'):
                continue
            c = [x.strip() for x in ln.strip().strip('|').split('|')]
            if len(c) < 15 or not c[0].isdigit():
                continue
            run = c[1].split(' ')[0]
            if re.match(r'^\d{4}-', run) and run not in ng:  # first hit = the section 2 table
                v = fnum(c[5])
                if v is not None:
                    ng[run] = v
    return ng


# --- Student t (regularized incomplete beta, Numerical Recipes betacf) ---
def _betacf(a, b, x):
    fpmin = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > fpmin else fpmin)
    h = d
    for m in range(1, 400):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > fpmin else fpmin)
        c = 1.0 + aa / c
        c = c if abs(c) > fpmin else fpmin
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > fpmin else fpmin)
        c = 1.0 + aa / c
        c = c if abs(c) > fpmin else fpmin
        de = d * c
        h *= de
        if abs(de - 1.0) < 3e-14:
            break
    return h


def _betai(a, b, x):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_p2(t, df):
    return _betai(df / 2.0, 0.5, df / (df + t * t))


def t_crit(df, alpha=0.05):
    lo, hi = 0.0, 200.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if t_p2(mid, df) > alpha:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def sign_p(higher, n):
    k = max(higher, n - higher)
    tail = sum(math.comb(n, i) for i in range(k, n + 1)) / 2.0 ** n
    return min(1.0, 2.0 * tail)


def pct(a, b):
    return 100.0 * (a / b - 1.0)


def pooled_diffs(runs, arms, pairs, key='cores'):
    g = dict((arm, [r[key] for r in runs if r['arm'] == arm]) for arm in arms)
    n_all = sum(len(v) for v in g.values())
    df = n_all - len(arms)
    ss = sum(sum((x - st.mean(v)) ** 2 for x in v) for v in g.values())
    s = math.sqrt(ss / df)
    tc = t_crit(df)
    out = []
    for a, b in pairs:
        d = st.mean(g[a]) - st.mean(g[b])
        hw = tc * s * math.sqrt(1.0 / len(g[a]) + 1.0 / len(g[b]))
        out.append((a, b, len(g[a]), len(g[b]), d, hw, df))
    return out


def fmt_diff(row):
    a, b, na, nb, d, hw, df = row
    star = ' *' if abs(d) > hw else ''
    return '%s - %s (n %d v %d): %+.3f [%+.3f, %+.3f]%s (df %d)' % (a, b, na, nb, d, d - hw, d + hw, star, df)


def load_table(runs, ng, spin_arms, out):
    kept = [r for r in runs if r['kept']]
    arms = []
    for r in kept:
        if r['arm'] not in arms:
            arms.append(r['arm'])
    base = {}
    out.append('| arm | runs with ng_t < %.1f | median fps | median raw ms | median T-std ms | median cores | median eff MHz |'
               % LOADED)
    out.append('|---|---|---|---|---|---|---|')
    for arm in arms:
        cl = [r for r in kept if r['arm'] == arm and ng.get(r['run'], 0.0) < LOADED]
        b = dict((k, st.median([r[k] for r in cl])) for k in ('fps', 'raw_med', 't_med', 'cores', 'eff'))
        b['n'] = len(cl)
        base[arm] = b
        out.append('| %s | %d | %.1f | %.3f | %.3f | %.3f | %.0f |' % (arm, b['n'], b['fps'], b['raw_med'], b['t_med'],
                                                                      b['cores'], b['eff']))
    out.append('')
    out.append('| run | arm | ng_t | eff MHz (vs arm) | fps (vs arm) | raw median ms (vs arm) | T-std median ms (vs arm) | '
               'cores (vs arm) | cores at constant core x MHz | rest |')
    out.append('|---|---|---|---|---|---|---|---|---|---|')
    hits = sorted([r for r in kept if ng.get(r['run'], 0.0) >= LOADED], key=lambda r: -ng[r['run']])
    for r in hits:
        b = base[r['arm']]
        if r['arm'] in spin_arms:
            exp_s, rest_s = '- (spin arm)', '-'
        else:
            exp = b['cores'] * b['eff'] / r['eff']
            exp_s, rest_s = '%.2f' % exp, '%+.2f' % (r['cores'] - exp)
        out.append('| %s | %s | %.2f | %.0f (%+.1f %%) | %.1f (%+.1f %%) | %.3f (%+.1f %%) | %.3f (%+.1f %%) | %.2f (%+.2f) | %s | %s |'
                   % (r['run'], r['arm'], ng[r['run']], r['eff'], pct(r['eff'], b['eff']), r['fps'], pct(r['fps'], b['fps']),
                      r['raw_med'], pct(r['raw_med'], b['raw_med']), r['t_med'], pct(r['t_med'], b['t_med']),
                      r['cores'], r['cores'] - b['cores'], exp_s, rest_s))
    out.append('')
    missing = [r['run'] for r in kept if r['run'] not in ng]
    if missing:
        out.append('No ng_t in audit.md for: %s' % ', '.join(missing))
        out.append('')
    return base


def paired(runs, a, b, key, drop_rounds=(), drop_runs=()):
    """Per-round % deltas a vs b; drop_runs skips any round in which a's or b's run is listed."""
    kept = [r for r in runs if r['kept']]
    rounds = sorted(set(int(r['round']) for r in kept))
    d = []
    for rd in rounds:
        if rd in drop_rounds:
            continue
        ra = [r for r in kept if r['arm'] == a and int(r['round']) == rd]
        rb = [r for r in kept if r['arm'] == b and int(r['round']) == rd]
        if ra and rb:
            if ra[0]['run'] in drop_runs or rb[0]['run'] in drop_runs:
                continue
            d.append((rd, pct(ra[0][key], rb[0][key])))
    return d


def ranks(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2.0 + 1.0  # average rank for ties
        i = j + 1
    return r


def spearman(xs, ys):
    """Spearman rho with the usual t approximation for p (df = n - 2)."""
    rx, ry = ranks(xs), ranks(ys)
    mx, my = st.mean(rx), st.mean(ry)
    sxy = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sxx = sum((a - mx) ** 2 for a in rx)
    syy = sum((b - my) ** 2 for b in ry)
    rho = sxy / math.sqrt(sxx * syy)
    n = len(xs)
    t = rho * math.sqrt((n - 2) / max(1e-12, 1.0 - rho * rho))
    return rho, n, t_p2(t, n - 2)


def ng_lines(runs, ng, label, out):
    """Per pass: ng_t spread of the kept runs and Spearman rho(ng_t, raw fps)."""
    kept = [r for r in runs if r['kept']]
    for p in sorted(set(r['pass'] for r in kept)):
        rs = [r for r in kept if r['pass'] == p and r['run'] in ng]
        v = [ng[r['run']] for r in rs]
        cl = [x for x in v if x < LOADED]
        rho, n, pv = spearman(v, [r['fps'] for r in rs])
        # within arm: centre ng_t and fps on this pass's per-arm medians, so arm effects drop out
        med = {}
        for arm in set(r['arm'] for r in rs):
            ar = [r for r in rs if r['arm'] == arm]
            med[arm] = (st.median([ng[r['run']] for r in ar]), st.median([r['fps'] for r in ar]))
        rho_w, n_w, pv_w = spearman([ng[r['run']] - med[r['arm']][0] for r in rs],
                                    [r['fps'] - med[r['arm']][1] for r in rs])
        out.append('- %s-%d: ng_t median %.2f [%.2f..%.2f] over %d kept runs; %d at or above %.1f; median of the rest %.2f; '
                   'Spearman rho(ng_t, raw fps) across runs %+.2f (n %d, p %.3f), within arm %+.2f (p %.3f, approximate)'
                   % (label, p, st.median(v), min(v), max(v), len(v), len(v) - len(cl), LOADED, st.median(cl), rho, n, pv,
                      rho_w, pv_w))
    out.append('')


def fmt_paired(label, d):
    vals = [x for _, x in d]
    hi = sum(1 for x in vals if x > 0)
    m = st.mean(vals)
    return ('%s: ' % label if label else '') + \
        'n %d, higher %d/%d (sign p %.3f), mean %+.2f %%, median %+.2f %%, per round %s' % (
            len(vals), hi, len(vals), sign_p(hi, len(vals)), m, st.median(vals),
            ', '.join('r%d %+.2f' % (rd, x) for rd, x in d))


def main(argv):
    below_normal()
    out_path = None
    if len(argv) >= 2 and argv[0] == '-o':
        out_path = argv[1]
    ng = audit_ngt(AUDIT)
    out = ['# Load checks for the W9 / W5b read-outs (load_check.py)', '',
           '- inputs: `build/agent7/readout/pool-W9.md`, `pool-W5b.md` (section 8 run tables) and ng_t from '
           '`build/agent8/readout/w-followup/audit/audit.md` section 2 (%d runs read)' % len(ng),
           '- loaded run = ng_t >= %.1f non-game busy cores (window mean); baselines = medians of the same arm\'s '
           'kept runs below that' % LOADED,
           '- "cores at constant core x MHz" = baseline cores x baseline eff MHz / run eff MHz: what the run would use if '
           'it did the same cycles per second at its lower clock; rest = observed - that', '']

    # ---------------- W9 ----------------
    w9 = pool_runs(POOL['W9'])
    out += ['## W9', '', '### Host load per pass (audit ng_t)', '']
    ng_lines(w9, ng, 'W9', out)
    out += ['### Loaded runs vs the same arm', '']
    load_table(w9, ng, ('off', 'q0'), out)
    kept = [r for r in w9 if r['kept']]
    out += ['### Thread cycles (busy % x eff GHz; a rough cycle rate)', '',
            '| group | runs | Main XThread | GPU Commands |', '|---|---|---|---|']
    groups = [('off', lambda r: r['arm'] == 'off'), ('q0', lambda r: r['arm'] == 'q0'),
              ('q125-q500, ng_t < %.1f' % LOADED, lambda r: r['arm'] in ('q125', 'q250', 'q500') and ng[r['run']] < LOADED),
              ('q125-q500, ng_t >= %.1f' % LOADED, lambda r: r['arm'] in ('q125', 'q250', 'q500') and ng[r['run']] >= LOADED)]
    for label, f in groups:
        rs = [r for r in kept if f(r)]
        mc = [r['main'] * r['eff'] / 1000.0 for r in rs]
        gc = [r['gpu'] * r['eff'] / 1000.0 for r in rs]
        out.append('| %s | %d | %.1f-%.1f (median %.1f) | %.1f-%.1f (median %.1f) |' % (
            label, len(rs), min(mc), max(mc), st.median(mc), min(gc), max(gc), st.median(gc)))
    out.append('')
    out += ['Per loaded q run: ' + '; '.join('%s Main %.1f GPU %.1f' % (r['run'], r['main'] * r['eff'] / 1000.0,
                                                                      r['gpu'] * r['eff'] / 1000.0)
                                            for r in kept if r['arm'] in ('q125', 'q250', 'q500') and ng[r['run']] >= LOADED), '']

    arms9 = ['off', 'q0', 'q125', 'q250', 'q500']
    variants9 = [('full pool', ()),
                 ('no-lowclk', ('0407-q125-r1', '0409-q250-r1', '0419-q500-r2', '0423-q125-r3')),
                 ('no-slow-q', ('0407-q125-r1', '0423-q125-r3', '0409-q250-r1', '0417-q250-r2')),
                 ('no-flagged', ('0122-q125-r2', '0124-q250-r2', '0407-q125-r1', '0409-q250-r1', '0417-q250-r2',
                                 '0419-q500-r2', '0423-q125-r3'))]
    pairs9 = [('q500', 'off'), ('q500', 'q250'), ('q500', 'q125'), ('q250', 'q125')]
    out += ['### Cores differences between arms (pooled linear CI, all 5 arms in the pool)', '']
    for label, drop in variants9:
        rs = [r for r in kept if r['run'] not in drop]
        out.append('- %s: %s' % (label, '; '.join(fmt_diff(x) for x in pooled_diffs(rs, arms9, pairs9))))
    out.append('')

    out += ['### Paired per-round counts', '']
    p1r1 = (1, 5)  # round 1 of each pass (pooled rounds 1 and 5): off ran first
    for a, key, lab in (('q0', 'raw_med', 'raw median ms'), ('q0', 't_med', 'T-std median ms'),
                        ('q500', 'fps', 'raw fps'), ('q500', 'raw_med', 'raw median ms'),
                        ('q125', 'fps', 'raw fps'), ('q250', 'fps', 'raw fps')):
        out.append('- %s vs off, %s, all rounds: %s' % (a, lab, fmt_paired('', paired(w9, a, 'off', key))))
        out.append('- %s vs off, %s, without each pass\'s round 1: %s' % (
            a, lab, fmt_paired('', paired(w9, a, 'off', key, p1r1))))
    flag9 = variants9[3][1]
    for a, key, lab in (('q500', 'fps', 'raw fps'), ('q500', 'raw_med', 'raw median ms')):
        out.append('- %s vs off, %s, without rounds holding a flagged run (no-flagged list): %s' % (
            a, lab, fmt_paired('', paired(w9, a, 'off', key, (), flag9))))
    out.append('')

    # ---------------- W5b ----------------
    w5 = pool_runs(POOL['W5b'])
    out += ['## W5b', '', '### Host load per pass (audit ng_t)', '']
    ng_lines(w5, ng, 'W5b', out)
    out += ['### Loaded runs vs the same arm', '']
    base5 = load_table(w5, ng, ('d11',), out)
    kept5 = [r for r in w5 if r['kept']]
    out += ['Loaded runs vs d11\'s ng_t < %.1f median fps (%.1f): ' % (LOADED, base5['d11']['fps']) +
            '; '.join('%s %s %+.1f %%' % (r['run'], r['arm'], pct(r['fps'], base5['d11']['fps']))
                      for r in sorted([r for r in kept5 if ng.get(r['run'], 0.0) >= LOADED], key=lambda r: -ng[r['run']])), '']
    arms5 = ['d11', 'd11t', 'd11p']
    out += ['### Cores differences (pooled linear CI)', '']
    out.append('- full pool: %s' % '; '.join(fmt_diff(x) for x in pooled_diffs(kept5, arms5, [('d11t', 'd11'), ('d11p', 'd11'), ('d11t', 'd11p')])))
    out.append('')
    out += ['### Paired per-round counts', '']
    r1 = (1, 7)
    for a, key, lab in (('d11t', 'raw_med', 'raw median ms'), ('d11p', 'raw_med', 'raw median ms'),
                        ('d11t', 'fps', 'raw fps'), ('d11p', 'fps', 'raw fps'), ('d11t', 'p99', 'raw p99 ms'),
                        ('d11p', 'p99', 'raw p99 ms')):
        out.append('- %s vs d11, %s, all rounds: %s' % (a, lab, fmt_paired('', paired(w5, a, 'd11', key))))
        out.append('- %s vs d11, %s, without each pass\'s round 1: %s' % (a, lab, fmt_paired('', paired(w5, a, 'd11', key, r1))))
    flag5 = ('0209-d11p-r3', '0213-d11t-r3', '0453-d11-r1', '0455-d11t-r1', '0457-d11p-r1', '0510-d11t-r3')
    for a, key, lab in (('d11t', 'raw_med', 'raw median ms'), ('d11t', 'fps', 'raw fps'),
                        ('d11p', 'raw_med', 'raw median ms'), ('d11p', 'fps', 'raw fps')):
        out.append('- %s vs d11, %s, without rounds holding an audit-flagged run: %s' % (
            a, lab, fmt_paired('', paired(w5, a, 'd11', key, (), flag5))))
    out.append('')
    out.append('- check: t_crit(35) = %.4f, t_crit(7) = %.4f, t_crit(11) = %.4f' % (t_crit(35), t_crit(7), t_crit(11)))
    text = '\n'.join(out) + '\n'
    if out_path:
        with open(out_path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)
        sys.stdout.write('wrote %s\n' % out_path)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

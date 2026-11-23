#!/usr/bin/env python3
"""Recompute the W6 / W4c headline numbers from results.csv only (Agent 7, task #21), read-only, stdlib only.

Checks two sets of claims against the raw results.csv columns:
  - the runner headlines (summary.md, as posted in perf-notes/SESSION2.md 01:05 / 03:09 / 03:58): per arm the median of
    the run medians, the median fps, the mean cpu cores, median p99 / p99.9, the ref band (max - min) / median, the
    deltas vs the ref and the per-round contrasts;
  - Agent 8's pooled numbers (build/agent8/readout/w-followup/mine/W6.md, W4c.md): pooled medians, paired
    exp(mean ln ratio) - 1 with a 95 % t CI per round (a round = pass + round), sign counts, paired cores.
A claim agrees when the recomputed value rounds to the posted one (|diff| <= half of the last posted digit).

Usage: python -B build\\agent7\\readout\\recompute_headlines.py [-o OUT.md]
"""
import argparse
import csv
import math
import os
import statistics
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
MX = os.path.join(REPO, 'build', 'agent8', 'matrix')
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086}


def t975(df):
    return T975.get(df, 1.96)


def num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def load(stamp, p):
    with open(os.path.join(MX, stamp, 'results.csv'), newline='', encoding='utf-8-sig') as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for r in rows:
        ok = ((r.get('scored') or '').lower() == 'true' and (r.get('status') or '') == 'OK'
              and (r.get('valid_timing') or '').lower() == 'true' and (r.get('excluded') or '').lower() != 'true')
        x = {'pass': p, 'round': r.get('round'), 'arm': r.get('arm'), 'ok': ok, 'name': os.path.basename(
            (r.get('run_dir') or '').rstrip('\\/')), 'med': num(r.get('median_ms')), 'p99': num(r.get('p99_ms')),
             'p999': num(r.get('p999_ms')), 'max': num(r.get('max_ms')), 'over33': num(r.get('over33')),
             'fps_col': num(r.get('fps_mean')), 'cores': num(r.get('cpu_cores_mean')), 'frames': num(r.get('frames')),
             'window_s': num(r.get('window_s'))}
        x['fps_fw'] = x['frames'] / x['window_s'] if x['frames'] and x['window_s'] else None
        out.append(x)
    return out


def arm_runs(runs, arm):
    return [x for x in runs if x['ok'] and x['arm'] == arm]


def med(runs, arm, k):
    return statistics.median([x[k] for x in arm_runs(runs, arm)])


def mean(runs, arm, k):
    return statistics.fmean([x[k] for x in arm_runs(runs, arm)])


def band(runs, arm):
    v = [x['med'] for x in arm_runs(runs, arm)]
    return 100.0 * (max(v) - min(v)) / statistics.median(v)


def by_round(runs, a, b, k='med'):
    """[(round key, value of a, value of b)] over the rounds in which both ran (a round = pass + round)."""
    d = {}
    for x in runs:
        if x['ok']:
            d.setdefault((x['pass'], int(x['round'])), {})[x['arm']] = x[k]
    return [(rk, v[a], v[b]) for rk, v in sorted(d.items()) if a in v and b in v]


def paired_ratio(runs, a, b, k):
    rr = by_round(runs, a, b, k)
    ls = [math.log(u / v) for _, u, v in rr]
    n = len(ls)
    m, sd = statistics.fmean(ls), statistics.stdev(ls)
    hw = t975(n - 1) * sd / math.sqrt(n)
    return (100.0 * (math.exp(m) - 1.0), 100.0 * (math.exp(m - hw) - 1.0), 100.0 * (math.exp(m + hw) - 1.0), n,
            sum(1 for q in ls if q < 0))


def paired_diff(runs, a, b, k):
    rr = by_round(runs, a, b, k)
    ds = [u - v for _, u, v in rr]
    n = len(ds)
    m, sd = statistics.fmean(ds), statistics.stdev(ds)
    hw = t975(n - 1) * sd / math.sqrt(n)
    return m, m - hw, m + hw, n


def sign_p(k, n):
    """Two-sided exact sign test."""
    tail = sum(math.comb(n, i) for i in range(0, min(k, n - k) + 1)) / 2.0 ** n
    return min(1.0, 2.0 * tail)


class Checker:
    def __init__(self):
        self.rows, self.bad = [], 0

    def claim(self, src, what, posted, value, nd):
        ok = value is not None and abs(value - posted) <= 0.5 * 10 ** (-nd) + 1e-9
        self.bad += 0 if ok else 1
        self.rows.append((src, what, ('%.*f' % (nd, posted)), ('%.4f' % value) if value is not None else '-',
                          'agree' if ok else 'DISAGREE'))

    def note(self, src, what, posted, value, verdict):
        self.rows.append((src, what, posted, value, verdict))
        if verdict.startswith('DISAGREE'):
            self.bad += 1


def runner_block(c, tag, runs, ref, arms, claims):
    """claims: {arm: (median ms, fps, cores)} plus deltas; posted with the runner's rounding."""
    for arm, (pm, pf, pc) in claims.items():
        if pm is not None:
            c.claim(tag, '%s median of run medians, ms' % arm, pm, med(runs, arm, 'med'), 2)
        if pf is not None:
            nd = len(repr(pf).split('.')[1]) if '.' in repr(pf) else 0  # the posted precision
            c.claim(tag, '%s fps (median of results.csv fps_mean)' % arm, pf, med(runs, arm, 'fps_col'), nd)
        if pc is not None:
            c.claim(tag, '%s cpu cores (mean of cpu_cores_mean)' % arm, pc, mean(runs, arm, 'cores'), 2)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('-o', '--out')
    a = ap.parse_args(argv)
    c = Checker()
    w6a, w6b = load('20261123-0009', 1), load('20261123-0313', 2)
    w6 = w6a + w6b
    w4c = load('20261123-0239', 1)

    # ---------------- W6 runner, pass 1 (SESSION2 01:05; summary.md of 0009)
    t = 'W6-1 runner'
    runner_block(c, t, w6a, 's0', None, {'s0': (2.44, 385.15, 2.50), 'p2': (2.47, 385.56, None),
                                         'p2f': (2.45, 387.72, None), 'p2fc': (2.16, 466.3, 2.28)})
    c.claim(t, 's0 band (max - min) / median, %', 21.4, band(w6a, 's0'), 1)
    c.claim(t, 'p2fc vs s0: median-of-medians delta, %', -11.8, 100 * (med(w6a, 'p2fc', 'med') / med(w6a, 's0', 'med') - 1), 1)
    c.claim(t, 'p2fc vs s0: fps delta (medians), %', 21, 100 * (med(w6a, 'p2fc', 'fps_col') / med(w6a, 's0', 'fps_col') - 1), 0)
    c.claim(t, 'p2fc vs s0: cores (means), core', -0.22, mean(w6a, 'p2fc', 'cores') - mean(w6a, 's0', 'cores'), 2)
    for (rk, u, v), posted in zip(by_round(w6a, 'p2fc', 'p2f'), (-0.06, -0.16, -0.30, -0.30, -0.28)):
        c.claim(t, 'C1 = p2fc - p2f median ms, round %d' % rk[1], posted, u - v, 2)
    fast = [arm for arm in ('s0', 'p2', 'p2f', 'p2fc')
            if min(arm_runs(w6a, arm), key=lambda x: x['med'])['round'] == '1']
    c.note(t, 'round 1 faster for every arm (r1 = the arm\'s fastest run)', 'yes', ', '.join(fast) or 'none',
           'agree' if len(fast) == 4 else 'DISAGREE (only %s)' % (', '.join(fast) or 'none'))

    # ---------------- W6 runner, pass 2 (SESSION2 03:58)
    t = 'W6-2 runner'
    runner_block(c, t, w6b, 's0', None, {'s0': (2.48, 385.0, 2.53), 'p2': (2.47, 385.2, 2.53),
                                         'p2f': (2.45, 385.9, 2.55), 'p2fc': (2.13, 469.8, 2.26)})
    c.claim(t, 's0 band (max - min) / median, %', 8.4, band(w6b, 's0'), 1)
    c.claim(t, 'p2fc vs s0: median-of-medians delta, %', -14, 100 * (med(w6b, 'p2fc', 'med') / med(w6b, 's0', 'med') - 1), 0)
    c.claim(t, 'p2fc vs s0: fps delta (medians), %', 22, 100 * (med(w6b, 'p2fc', 'fps_col') / med(w6b, 's0', 'fps_col') - 1), 0)
    c.claim(t, 'p2fc vs s0: cores (means), core', -0.27, mean(w6b, 'p2fc', 'cores') - mean(w6b, 's0', 'cores'), 2)
    for (rk, u, v), posted in zip(by_round(w6b, 'p2fc', 'p2f'), (-0.34, -0.27, -0.32, -0.28, -0.32)):
        c.claim(t, 'C1 = p2fc - p2f median ms, round %d' % rk[1], posted, u - v, 2)
    c.claim(t, 'p2fc p99 ms (median of runs)', 5.04, med(w6b, 'p2fc', 'p99'), 2)
    c.claim(t, 's0 p99 ms (median of runs)', 5.00, med(w6b, 's0', 'p99'), 2)
    c.claim(t, 'p2fc p99.9 ms (median of runs)', 6.49, med(w6b, 'p2fc', 'p999'), 2)
    c.claim(t, 's0 p99.9 ms (median of runs)', 5.74, med(w6b, 's0', 'p999'), 2)
    c.claim(t, 'p2f p99.9 ms (median of runs)', 6.40, med(w6b, 'p2f', 'p999'), 2)
    o33 = [(x['name'], x['over33']) for x in w6b if x['ok'] and (x['over33'] or 0) > 0]
    c.note(t, 'one >33 ms frame, in p2f r5', 'p2f r5: 1', '; '.join('%s: %d' % (n, v) for n, v in o33) or 'none',
           'agree' if len(o33) == 1 and o33[0][0].endswith('p2f-r5') and o33[0][1] == 1 else 'DISAGREE')
    n10 = sum(1 for _, u, v in by_round(w6, 'p2fc', 'p2f') if u < v)
    c.claim('W6 both runner', 'C1 faster rounds of 10', 10, n10, 0)

    # ---------------- W6, Agent 8 pooled (mine/W6.md)
    t = 'W6 Agent 8 pooled'
    c.claim(t, 'p2fc vs s0 pooled median of medians, %', -12.8, 100 * (med(w6, 'p2fc', 'med') / med(w6, 's0', 'med') - 1), 1)
    for (lab, a1, b1, k, posted) in (('p2fc vs s0 paired median ms %', 'p2fc', 's0', 'med', (-10.3, -13.6, -6.9)),
                                     ('p2fc vs s0 paired fps (frames / window) %', 'p2fc', 's0', 'fps_fw', (18.0, 14.1, 22.0)),
                                     ('p2fc - p2f paired median ms %', 'p2fc', 'p2f', 'med', (-10.7, -13.1, -8.3)),
                                     ('p2fc - p2f paired fps %', 'p2fc', 'p2f', 'fps_fw', (18.4, 15.2, 21.8)),
                                     ('p2 vs s0 paired median ms %', 'p2', 's0', 'med', (-0.0, -3.0, 3.1)),
                                     ('p2f vs s0 paired median ms %', 'p2f', 's0', 'med', (0.4, -2.1, 3.1))):
        g, lo, hi, n, low = paired_ratio(w6, a1, b1, k)
        for part, pv, vv in zip(('', ' CI lo', ' CI hi'), posted, (g, lo, hi)):
            c.claim(t, lab + part, pv, vv, 1)
    g, lo, hi, n = paired_diff(w6, 'p2fc', 's0', 'cores')
    for part, pv, vv in zip(('', ' CI lo', ' CI hi'), (-0.249, -0.303, -0.195), (g, lo, hi)):
        c.claim(t, 'p2fc - s0 paired cores' + part, pv, vv, 3)
    g, lo, hi, n = paired_diff(w6, 'p2fc', 'p2f', 'cores')
    c.claim(t, 'p2fc - p2f paired cores', -0.288, g, 3)
    low = sum(1 for _, u, v in by_round(w6, 'p2fc', 's0') if u < v)
    c.claim(t, 'p2fc lower than s0 in rounds of 10', 9, low, 0)
    c.claim(t, 'sign test p (9/10)', 0.021, sign_p(low, 10), 3)
    c.claim(t, 's0 fps mean (frames / window)', 392.3, mean(w6, 's0', 'fps_fw'), 1)
    c.claim(t, 'p2fc fps mean (frames / window)', 462.6, mean(w6, 'p2fc', 'fps_fw'), 1)
    c.claim(t, 'p2fc pass 1 fps mean', 458.9, mean(w6a, 'p2fc', 'fps_fw'), 1)
    c.claim(t, 'p2fc pass 2 fps mean', 466.2, mean(w6b, 'p2fc', 'fps_fw'), 1)
    c.claim(t, 'p2fc p99 mean ms', 4.981, mean(w6, 'p2fc', 'p99'), 3)
    c.claim(t, 's0 p99 mean ms', 5.016, mean(w6, 's0', 'p99'), 3)
    c.claim(t, 'p2fc p99.9 mean ms', 6.088, mean(w6, 'p2fc', 'p999'), 3)
    c.claim(t, 's0 p99.9 mean ms', 6.364, mean(w6, 's0', 'p999'), 3)

    # ---------------- W4c runner (SESSION2 03:09; summary.md of 0239)
    t = 'W4c runner'
    runner_block(c, t, w4c, 'd0', None, {'d0': (2.47, 385.35, 2.53), 'B': (2.50, 383.91, 2.60)})
    c.claim(t, 'd0 band (max - min) / median, %', 10, band(w4c, 'd0'), 0)
    c.claim(t, 'B vs d0 median-of-medians delta, %', 1.3, 100 * (med(w4c, 'B', 'med') / med(w4c, 'd0', 'med') - 1), 1)
    c.claim(t, 'B vs d0 fps delta (medians), %', -0.4, 100 * (med(w4c, 'B', 'fps_col') / med(w4c, 'd0', 'fps_col') - 1), 1)
    c.claim(t, 'B - d0 cores (means), core', 0.07, mean(w4c, 'B', 'cores') - mean(w4c, 'd0', 'cores'), 2)
    c.claim(t, 'B p99 ms (median of runs)', 4.91, med(w4c, 'B', 'p99'), 2)
    c.claim(t, 'd0 p99 ms (median of runs)', 4.94, med(w4c, 'd0', 'p99'), 2)
    c.claim(t, 'B p99.9 ms (median of runs)', 5.62, med(w4c, 'B', 'p999'), 2)
    c.claim(t, 'd0 p99.9 ms (median of runs)', 5.62, med(w4c, 'd0', 'p999'), 2)
    for (rk, u, v), posted in zip(by_round(w4c, 'B', 'd0'), (0.23, 0.04, 0.05, -0.00, 0.01, 0.05)):
        c.claim(t, 'B - d0 median ms, round %d' % rk[1], posted, u - v, 2)
    slower = sum(1 for _, u, v in by_round(w4c, 'B', 'd0') if round(u - v, 2) > 0)
    c.claim(t, 'B slower in rounds of 6 (2-decimal ms)', 5, slower, 0)

    # ---------------- W4c, Agent 8 (mine/W4c.md)
    t = 'W4c Agent 8'
    g, lo, hi, n, low = paired_ratio(w4c, 'B', 'd0', 'med')
    for part, pv, vv in zip(('', ' CI lo', ' CI hi'), (2.6, -1.2, 6.5), (g, lo, hi)):
        c.claim(t, 'B vs d0 paired median ms %' + part, pv, vv, 1)
    c.claim(t, 'B lower in rounds of 6', 1, low, 0)
    g, lo, hi, n, low = paired_ratio(w4c, 'B', 'd0', 'fps_fw')
    for part, pv, vv in zip(('', ' CI lo', ' CI hi'), (-1.7, -4.9, 1.7), (g, lo, hi)):
        c.claim(t, 'B vs d0 paired fps %' + part, pv, vv, 1)
    g, lo, hi, n = paired_diff(w4c, 'B', 'd0', 'cores')
    for part, pv, vv in zip(('', ' CI lo', ' CI hi'), (0.063, -0.007, 0.133), (g, lo, hi)):
        c.claim(t, 'B - d0 paired cores' + part, pv, vv, 3)
    c.claim(t, 'd0 fps mean', 391.5, mean(w4c, 'd0', 'fps_fw'), 1)
    c.claim(t, 'B fps mean', 384.6, mean(w4c, 'B', 'fps_fw'), 1)
    c.claim(t, 'd0 p99 mean', 4.930, mean(w4c, 'd0', 'p99'), 3)
    c.claim(t, 'B p99 mean', 4.901, mean(w4c, 'B', 'p99'), 3)

    out = ['# W6 / W4c headline numbers recomputed from results.csv (Agent 7, task #21)', '',
           'Kept runs: scored, status OK, valid timing, not excluded (cold runs out). Runner = summary.md / SESSION2.md;'
           ' Agent 8 = build/agent8/readout/w-followup/mine/W6.md and W4c.md. agree = the recomputed value rounds to the'
           ' posted one.', '', '**%d claims, %d disagree.**' % (len(c.rows), c.bad), '',
           '| source | claim | posted | recomputed | verdict |', '|---|---|---|---|---|']
    out += ['| %s | %s | %s | %s | %s |' % r for r in c.rows]
    # context numbers
    out += ['', '## Context (not claims)', '']
    for tag, runs in (('W6 pass 1', w6a), ('W6 pass 2', w6b), ('W6 pooled', w6), ('W4c', w4c)):
        arms = list(dict.fromkeys(x['arm'] for x in runs if x['ok']))
        out.append('- %s: %s' % (tag, '; '.join(
            '%s n=%d med %.3f ms, fps med %.2f (frames/window med %.2f, mean %.2f), cores mean %.3f, p99 med %.3f / mean '
            '%.3f, p99.9 med %.3f / mean %.3f, max %.2f, >33 total %d' % (
                arm, len(arm_runs(runs, arm)), med(runs, arm, 'med'), med(runs, arm, 'fps_col'),
                med(runs, arm, 'fps_fw'), mean(runs, arm, 'fps_fw'), mean(runs, arm, 'cores'), med(runs, arm, 'p99'),
                mean(runs, arm, 'p99'), med(runs, arm, 'p999'), mean(runs, arm, 'p999'),
                max(x['max'] for x in arm_runs(runs, arm)), sum(x['over33'] or 0 for x in arm_runs(runs, arm)))
            for arm in arms)))
    text = '\n'.join(out) + '\n'
    if a.out:
        with open(a.out, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)
        print('wrote %s: %d claims, %d disagree' % (a.out, len(c.rows), c.bad))
        for r in c.rows:
            if r[4] != 'agree':
                print('  %s | %s | posted %s | recomputed %s | %s' % r)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())

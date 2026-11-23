#!/usr/bin/env python3
"""Repeats note (Agent 7, task #14): from a measured window (default W5), the 95 % CI half-width per arm vs the ref
and the window minutes for 3, 4 and 5 repeats with 2-6 arms (the ref included), to choose repeats=<n>.

Usage:
  python -B build\\agent7\\w4b-noise\\repeats.py [DIR] [-o REPEATS.md] [--json repeats.json] [--ref ARM]

Model, as readout.py / noise_methods.summarize: an arm's GM delta vs the ref, both with n kept runs, has the 95 %
half-width hw = 100 (exp(t975(df) s sqrt(2/n)) - 1) %, with s = the pooled SD of ln(value) (the CV) and df = A (n - 1)
for T-std or (A - 1)(n - 1) for B-block T-std (A = arms, the ref included). t975 is the kit's table (between entries
the smaller df), so these are the bands the kit will print. s and its df come from DIR's T-std read-out over all its
kept runs. Minutes come from DIR's run.json start/end times: the cold run's slot + (A n - 1) run slots + the last run.
Read-only on DIR; writes only -o and --json. Below Normal priority, stdlib only, one thread.
"""
import argparse
import collections
import datetime
import importlib.util
import json
import math
import os
import statistics
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, fn):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, fn))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RO = _load('readout', 'readout.py')
N, W = RO.N, RO.W
W5_DIR = os.path.join(N.REPO, 'build', 'agent8', 'matrix', '20261122-1756')
NS = (3, 4, 5)            # repeats
AS = (2, 3, 4, 5, 6)      # arms, the ref included (1-5 arms vs the ref)
GUESS = (1.0, 2.0, 3.0)   # Best performance: CV guesses in %
P, F = 'p50_ms', 'fps'


# ---------------------------------------------------------------- distributions
def gammp(a, x):
    """Regularized lower incomplete gamma P(a, x) (Numerical Recipes gser / gcf)."""
    if x <= 0.0:
        return 0.0
    lg = -x + a * math.log(x) - math.lgamma(a)
    if x < a + 1.0:
        ap, d = a, 1.0 / a
        s = d
        for _ in range(5000):
            ap += 1.0
            d *= x / ap
            s += d
            if abs(d) < abs(s) * 1e-16:
                break
        return s * math.exp(lg)
    tiny = 1e-300
    b = x + 1.0 - a
    c, d = 1.0 / tiny, 1.0 / b
    h = d
    for i in range(1, 5000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        d = d if abs(d) > tiny else tiny
        c = b + an / c
        c = c if abs(c) > tiny else tiny
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < 1e-16:
            break
    return 1.0 - math.exp(lg) * h


def _bisect(cdf, p, lo, hi):
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def chi2_ppf(p, df):
    return _bisect(lambda x: gammp(df / 2.0, x / 2.0), p, 0.0, 10.0 * df + 100.0)


def t_cdf(t, df):
    tail = 0.5 * RO.betai(df / 2.0, 0.5, df / (df + t * t))
    return tail if t < 0 else 1.0 - tail


def t_ppf(p, df):
    return _bisect(lambda t: t_cdf(t, df), p, -200.0, 200.0)


def cv_range(df):
    """95 % range of the true SD as factors of a pooled SD estimated on df (chi-square)."""
    return math.sqrt(df / chi2_ppf(0.975, df)), math.sqrt(df / chi2_ppf(0.025, df))


# ---------------------------------------------------------------- the band and its cost
def df_of(A, n, block=False):
    """Residual df of the read-out: T-std A (n - 1); B-block T-std (A - 1)(n - 1) (n rounds of A runs)."""
    return (A - 1) * (n - 1) if block else A * (n - 1)


def hw_pct(s, n, df):
    """The kit's 95 % half-width of an arm vs the ref, n runs each: 100 (exp(t975(df) s sqrt(2/n)) - 1)."""
    t = N.t975(df)
    if t is None or s is None:
        return None
    return 100.0 * (math.exp(t * s * math.sqrt(2.0 / n)) - 1.0)


def mde_pct(s, n, df, power=0.80):
    """The true delta whose CI excludes 0 with this power (shifted-t approximation): (t975 + t_power) s sqrt(2/n)."""
    t = N.t975(df)
    if t is None or s is None:
        return None
    return 100.0 * (math.exp((t + t_ppf(power, df)) * s * math.sqrt(2.0 / n)) - 1.0)


def parse_t(v):
    s = str(v or '').strip()
    for f in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S'):
        try:
            return datetime.datetime.strptime(s, f)
        except ValueError:
            pass
    return None


def run_times(d, runs):
    """Per run (in results.csv order, as readout.load): scored, and run.json start / end as datetimes."""
    rows = W.read_rows(os.path.join(d, 'results.csv')) or []
    out = []
    for x, r in zip(runs, rows):
        rd = W.resolve_run_dir(d, r)
        rj = (W.load_json(os.path.join(rd, 'run.json')) if rd else None) or {}
        out.append({'name': x['name'], 'scored': bool(x.get('scored')), 'start': parse_t(rj.get('start')),
                    'end': parse_t(rj.get('end'))})
    return out


def timing(tt):
    """The window's time model: cold slot (cold start to the first scored start), run slot (start to start over the
    scored runs, valid or not), the last run's length, and the measured total; None with < 2 timed scored runs."""
    sc = sorted((t for t in tt if t['scored'] and t['start'] and t['end']), key=lambda t: t['start'])
    if len(sc) < 2:
        return None
    cold = sorted((t for t in tt if not t['scored'] and t['start'] and t['end']), key=lambda t: t['start'])
    t0 = cold[0]['start'] if cold else sc[0]['start']
    run_s = [(t['end'] - t['start']).total_seconds() for t in sc]
    return {'runs': len(sc), 'cold': len(cold), 'cold_slot_s': (sc[0]['start'] - t0).total_seconds(),
            'slot_s': (sc[-1]['start'] - sc[0]['start']).total_seconds() / (len(sc) - 1),
            'last_s': run_s[-1], 'run_mean_s': statistics.fmean(run_s),
            'total_s': (sc[-1]['end'] - t0).total_seconds(), 'from': t0.strftime('%H:%M:%S'),
            'to': sc[-1]['end'].strftime('%H:%M:%S')}


def minutes(A, n, tm):
    """Window minutes for A arms x n repeats: the cold slot, A n - 1 run slots (start to start), the last run."""
    return (tm['cold_slot_s'] + (A * n - 1) * tm['slot_s'] + tm['last_s']) / 60.0


# ---------------------------------------------------------------- the inputs from a read-out
def cv_of(R):
    """Per metric: T-std s (pooled SD of ln value) and df over all kept runs, B-block T-std's, and T-std's over the
    kept runs without the host flag (guard c). Returns (cv, unflagged runs, kept runs)."""
    kept = [x for x in R['runs'] if x['keep']]
    flag = set(R['guards']['c']['flagged'])
    calm = [x for x in kept if x['name'] not in flag]
    out = collections.OrderedDict()
    for key, sign, _ in RO.KEYS:
        st = (R['methods'].get('T-std') or {}).get(key) or {}
        bb = (R['methods'].get(RO.BLOCK) or {}).get(key) or {}
        q = N.summarize(N.collect(calm, N.getter('t_std'), key), R['ref'], R['order'], sign) or {}
        out[key] = {'s': st.get('sd_ln'), 'df': st.get('df'), 's_block': bb.get('sd_ln'), 'df_block': bb.get('df'),
                    's_calm': q.get('sd_ln'), 'df_calm': q.get('df')}
    return out, len(calm), len(kept)


def build(R, tm, command, label=None):
    cv, ncalm, nkept = cv_of(R)
    folder = os.path.basename(R['dir'].rstrip('\\/'))
    grid = []
    for A in AS:
        for n in NS:
            g = {'arms': A, 'vs_ref': A - 1, 'repeats': n, 'runs': A * n,
                 'minutes': minutes(A, n, tm) if tm else None, 'df': df_of(A, n), 'df_block': df_of(A, n, True),
                 'hw_pct': {}, 'hw_block_pct': {}, 'mde80_pct': {}, 'guess_hw_pct': {}}
            for key, _, _ in RO.KEYS:
                s = cv[key]['s']
                g['hw_pct'][key] = hw_pct(s, n, g['df'])
                g['hw_block_pct'][key] = hw_pct(s, n, g['df_block'])
                g['mde80_pct'][key] = mde_pct(s, n, g['df'])
            for c in GUESS:
                g['guess_hw_pct']['%g' % c] = hw_pct(c / 100.0, n, g['df'])
            grid.append(g)
    df0 = cv[P]['df']
    return {'tool': 'repeats.py', 'made': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'command': command,
            'dir': R['dir'], 'window': label or folder, 'folder': folder, 'ref': R['ref'], 'kept': nkept,
            'unflagged': ncalm, 'flagged': list(R['guards']['c']['flagged']), 'g11': R['g11']['line'],
            'primary': R['decision']['primary'], 'cv': cv, 'cv_range': cv_range(df0) if df0 else None,
            'timing': tm, 'grid': grid, 'guess_cv_pct': list(GUESS)}


# ---------------------------------------------------------------- markdown
def pm(v):
    return '-' if v is None else '±%.1f' % v


def pc(v):
    return '-' if v is None else '%.1f' % (100.0 * v)


def table(cols, cell):
    lines = ['| repeats | %s |' % ' | '.join('%d arms (%d vs ref)' % (A, A - 1) for A in cols),
             '|---|%s' % ('---|' * len(cols))]
    for n in NS:
        lines.append('| %d | %s |' % (n, ' | '.join(cell(A, n) for A in cols)))
    return lines


def render(D):
    out = []
    w = out.append
    G = dict(((g['arms'], g['repeats']), g) for g in D['grid'])
    cv, tm, rng = D['cv'], D['timing'], D['cv_range']
    lo_a, hi_a = AS[0], AS[-1]
    w('# Repeats note for the GO lines (W6-W10), from %s%s' % (
        D['window'], '' if D['window'] == D['folder'] else ' (%s)' % D['folder']))
    w('')
    w('Agent 7, task #14, %s. Made by `%s`; read-only on `%s` (ref %s; %d kept runs; its read-out: %s).' % (
        D['made'], D['command'], D['dir'], D['ref'], D['kept'], D['primary']))
    w('')
    w('"Arms" = arms in the window, the ref included: %d-%d arms = %d-%d arms vs the ref (W6\'s draft has 6: s0 + 5). '
      '"±" = the 95 %% CI half-width of one arm\'s GM delta vs the ref, as the read-out kit prints it, when every arm '
      'keeps all its runs. Minutes = the window itself (cold run + scored runs), not the gates before it.' % (
          lo_a, hi_a, lo_a - 1, hi_a - 1))
    w('')
    # ---- short answer
    w('## Short answer (Power mode as in %s)' % D['window'])
    w('')
    for n in NS:
        a, b = G[(lo_a, n)], G[(hi_a, n)]
        w('- **repeats=%d:** median ms %s %% (%d arms) to %s %% (%d arms); fps %s to %s %%; %.0f min (%d arms) to '
          '%.0f min (%d arms).' % (n, pm(b['hw_pct'][P]), hi_a, pm(a['hw_pct'][P]), lo_a, pm(b['hw_pct'][F]),
                                   pm(a['hw_pct'][F]), a['minutes'] or 0, lo_a, b['minutes'] or 0, hi_a))
    sh34 = [100.0 * (1.0 - G[(A, 4)]['hw_pct'][P] / G[(A, 3)]['hw_pct'][P]) for A in (hi_a, lo_a)]
    sh45 = [100.0 * (1.0 - G[(A, 5)]['hw_pct'][P] / G[(A, 4)]['hw_pct'][P]) for A in (hi_a, lo_a)]
    w('- Each repeat adds A runs of %.2f min. From 3 to 4 repeats the ± narrows by %.0f %% (%d arms) to %.0f %% '
      '(%d arms); from 4 to 5 by %.0f-%.0f %%.' % (tm['slot_s'] / 60.0, sh34[0], hi_a, sh34[1], lo_a,
                                                 min(sh45), max(sh45)))
    fac = [g['mde80_pct'][P] / g['hw_pct'][P] for g in D['grid'] if g['hw_pct'][P]]
    w('- An arm\'s true delta must be about %.2f-%.2f x its ± to give a `*` 80 %% of the time: with %d arms that is '
      '%s %% on median ms for 3 / 4 / 5 repeats.' % (min(fac), max(fac), hi_a, ' / '.join(
          '%.1f' % G[(hi_a, n)]['mde80_pct'][P] for n in NS)))
    if rng:
        w('- %s\'s CV is itself an estimate on df %d: another window on the same Power mode can give %.2f-%.2f x these '
          '± (95 %%). W4b (same overlay) had T-std CV 2.3 %% on median ms, against %s\'s %s %%.' % (
              D['window'], cv[P]['df'], rng[0], rng[1], D['window'], pc(cv[P]['s'])))
    w('- Best performance: the CV is unknown; the formula and a guess are in the last section.')
    w('')
    # ---- T-std half-widths
    w('## 1. ± per arm, T-std (no round effect, as %s)' % D['window'])
    w('')
    w('± = 100 (exp(t975(df) s sqrt(2/n)) - 1) %%, df = A (n - 1); t975 = the kit\'s table (between entries the smaller '
      'df: df 24 uses 2.086). s = %s\'s T-std pooled SD of ln(value) over its %d kept runs (df %s): median ms %s %%, '
      'fps %s %%, p99 %s %%, 1 %% low %s %%. A left-out run (invalid timing, excluded) lowers n for its arm and '
      'widens its ±.' % (D['window'], D['kept'], cv[P]['df'], pc(cv[P]['s']), pc(cv[F]['s']),
                         pc(cv['p99_ms']['s']), pc(cv['low1_fps']['s'])))
    w('')
    for key, label in ((P, 'median ms'), (F, 'fps')):
        w('**%s** (± %%, df):' % label)
        w('')
        out.extend(table(AS, lambda A, n, key=key: '%s (%d)' % (pm(G[(A, n)]['hw_pct'][key]), G[(A, n)]['df'])))
        w('')
    w('**Tails** (± %, p99 ms / 1 % low fps):')
    w('')
    out.extend(table(AS, lambda A, n: '%s / %s' % (pm(G[(A, n)]['hw_pct']['p99_ms']),
                                                   pm(G[(A, n)]['hw_pct']['low1_fps']))))
    w('')
    # ---- minutes
    w('## 2. Minutes per window')
    w('')
    if tm:
        base = (tm['cold_slot_s'] + tm['last_s'] - tm['slot_s']) / 60.0
        w('From %s\'s run.json start/end: the cold run\'s slot %.2f min, then one slot of %.2f min per scored run (start '
          'to start; a run lasts %.0f s on average, the gap is %.0f s), and the last run %.2f min. Window = cold slot + '
          '(A n - 1) slots + the last run = %.2f + %.2f x A n min. For %s\'s own %d runs that is its measured %.1f min '
          '(%s-%s), by construction. Not included: the quiet gate and the other gates before the cold run, and the '
          'read-out.' % (
              D['window'], tm['cold_slot_s'] / 60.0, tm['slot_s'] / 60.0, tm['run_mean_s'],
              tm['slot_s'] - tm['run_mean_s'], tm['last_s'] / 60.0, base, tm['slot_s'] / 60.0, D['window'],
              tm['runs'], tm['total_s'] / 60.0, tm['from'], tm['to']))
        w('')
        w('Minutes (scored runs):')
        w('')
        out.extend(table(AS, lambda A, n: '%.1f (%d)' % (G[(A, n)]['minutes'], A * n)))
    else:
        w('No run.json start/end times in %s.' % D['dir'])
    w('')
    # ---- B-block
    w('## 3. If a window has a round effect (B-block T-std)')
    w('')
    w('B-block spends rounds - 1 df on the rounds: df = (A - 1)(n - 1). It pays when the round effect is large (W4b: '
      'CV 2.3 -> 1.4 %% on median ms); with few arms the df cost is large. Median ms at %s\'s T-std s (± %%, df):' %
      D['window'])
    w('')
    out.extend(table(AS, lambda A, n: '%s (%d)' % (pm(G[(A, n)]['hw_block_pct'][P]), G[(A, n)]['df_block'])))
    w('')
    w('In %s (no round effect) B-block\'s own s was %s %% on median ms (df %s), so there T-std applies.' % (
        D['window'], pc(cv[P]['s_block']), cv[P]['df_block']))
    w('')
    # ---- MDE
    w('## 4. Smallest true delta seen 80 % of the time (median ms, T-std)')
    w('')
    w('100 (exp((t975 + t0.80) s sqrt(2/n)) - 1) %, with t0.80 the 80 % t quantile on the same df. Smaller true deltas '
      'are mostly read as "not shown", not as "no effect".')
    w('')
    out.extend(table(AS, lambda A, n: '%.1f' % G[(A, n)]['mde80_pct'][P]))
    w('')
    # ---- CV uncertainty
    w('## 5. How sure the CV is')
    w('')
    if rng:
        w('- %s\'s s comes from df %d. Its 95 %% range is %.2f-%.2f x s (chi-square), and every ± above scales with s '
          '(nearly in proportion): for median ms, s could be %.1f-%.1f %%.' % (
              D['window'], cv[P]['df'], rng[0], rng[1], 100.0 * cv[P]['s'] * rng[0], 100.0 * cv[P]['s'] * rng[1]))
    w('- W4b, on the same overlay, had T-std CV 2.3 %% (median ms, df 11) and 4.1 %% (fps); %s has %s %% and %s %%. '
      'So about 2 %% on median ms looks typical for this Power mode.' % (D['window'], pc(cv[P]['s']), pc(cv[F]['s'])))
    w('- %s\'s %d kept runs without the host flag (guard c: %s) have s = %s %% on median ms and %s %% on fps (df %s). '
      'That is the CV when no run hits the P-thread / E-core clock state.' % (
          D['window'], D['unflagged'], ', '.join(RO.short(x) for x in D['flagged']) or 'none', pc(cv[P]['s_calm']),
          pc(cv[F]['s_calm']), cv[P]['df_calm']))
    w('')
    # ---- Best performance
    w('## 6. Best performance (CV unknown)')
    w('')
    w('If the user switches Power mode to Best performance, %s\'s CV no longer applies: the clocks, E-core parking '
      'and heat change, and no window has been measured on it.' % D['window'])
    w('')
    w('- Formula: ± = 100 (exp(t975(A (n - 1)) CV sqrt(2/n)) - 1) %, CV = the T-std pooled SD of ln(value) as a '
      'fraction (the kit\'s "pooled CV %" column / 100). Minutes as in section 2.')
    w('- Guess: CV 1-3 %% on median ms. Low end: no host-flag runs (%s\'s unflagged runs: %s %%; W4b B-block T-std: '
      '1.4 %%). High end: %s\'s %s %% plus heat or turbo swings. The first Best-performance window measures it.' % (
          D['window'], pc(cv[P]['s_calm']), D['window'], pc(cv[P]['s'])))
    w('')
    w('± %% at CV %s %% (T-std df):' % ' / '.join('%g' % c for c in GUESS))
    w('')
    out.extend(table(AS, lambda A, n: ' / '.join('%.1f' % G[(A, n)]['guess_hw_pct']['%g' % c] for c in GUESS)))
    w('')
    return '\n'.join(out) + '\n'


# ---------------------------------------------------------------- main
def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('dir', nargs='?', default=W5_DIR, help='the measured window (default W5: %(default)s)')
    ap.add_argument('-o', '--out', help='write the markdown here (without -o: stdout)')
    ap.add_argument('--json', help='write the numbers as json here')
    ap.add_argument('--ref', help='reference arm (default: matrix.json)')
    ap.add_argument('--label', help='window name in the text (default: W5 for the W5 folder, else the folder name)')
    ap.add_argument('--normal-priority', action='store_true', help="don't lower this process to Below Normal")
    return ap.parse_args(argv)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    a = parse_args(argv)
    if not a.normal_priority:
        RO.below_normal()
    d = os.path.abspath(a.dir)
    label = a.label or ('W5' if os.path.normcase(d) == os.path.normcase(os.path.abspath(W5_DIR)) else None)
    command = 'python -B build\\agent7\\w4b-noise\\repeats.py ' + ' '.join(argv)
    R = RO.analyse(d, RO.parse_args([d] + (['--ref', a.ref] if a.ref else [])), command)
    D = build(R, timing(run_times(d, R['runs'])), command, label)
    text = render(D)
    if a.out:
        with open(a.out, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)
        head = text.split('\n## 1. ', 1)[0]
        sys.stdout.write(head.rstrip('\n') + '\n\nwrote %s\n' % a.out)
    else:
        sys.stdout.write(text)
    if a.json:
        with open(a.json, 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(D, fh, indent=1, default=str)
        sys.stdout.write('wrote %s\n' % a.json)
    return 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Noise case (Agent 7, task #6): how far each kept run sits from its own arm under each noise method, read from
noise_methods.py's --json output (no frame data needed).

Per kept run, method and metric: the leave-one-out residual 100 (v / GM(the other runs of its arm) - 1) %, signed
so that + = slower (ms as is, fps inverted). ANCOVA methods (L, D) use their adjusted values. Host-state flag
(Agent 1, W5): sys.json window P-core util >= --putil and E-core MHz < --emhz. Per metric the report gives each
flagged run's residual per method, the flagged runs' mean (and its share of raw's), the RMS of the other kept runs,
and the method's pooled CV and reference band from the JSON; then every kept run's residuals.

Usage: python -B noise_case.py REPORT.json [-o OUT.md] [--metric p50_ms] [--metric fps] [--putil 90] [--emhz 600]
       [--methods raw,T-std,...]
Stdlib only, one thread; reads REPORT.json, writes only -o (stdout without -o).
"""
import argparse
import json
import math
import statistics
import sys

sys.dont_write_bytecode = True

DEFAULT_METHODS = ('raw', 'T-std', 'T-light', 'T-heavy', 'L-ls', 'A-heavy', 'A2-std', 'A2-light', 'D-emhz',
                   'D-putil', 'D-emhz+putil', 'D-nongame', 'C-frames', 'C-bins', 'B-norm raw', 'B-norm T-std',
                   'B-block raw', 'B-block T-std')
SIGN = {'fps': 1, 'low1_fps': 1, 'p50_ms': -1, 'p99_ms': -1}
LABEL = {'fps': 'fps', 'low1_fps': '1% low fps', 'p50_ms': 'median ms', 'p99_ms': 'p99 ms'}


def loo_resid(pairs, sign):
    """{run: leave-one-out residual %} for one arm's [(run, value)]; + = slower. Empty with < 2 runs."""
    out = {}
    if len(pairs) < 2:
        return out
    logs = [math.log(v) for _, v in pairs]
    for i, (name, _) in enumerate(pairs):
        d = logs[i] - statistics.fmean([u for j, u in enumerate(logs) if j != i])
        out[name] = 100.0 * (math.exp(-d if sign > 0 else d) - 1.0)
    return out


def flagged_runs(R, putil, emhz):
    """Names of the kept runs with sys.json window P util >= putil and E MHz < emhz."""
    out = []
    for x in R.get('runs') or []:
        c = x.get('cov') or {}
        if (x.get('keep') and c.get('p_util') is not None and c.get('e_mhz') is not None
                and c['p_util'] >= putil and c['e_mhz'] < emhz):
            out.append(x['name'])
    return out


def residuals(m, sign):
    out = {}
    for e in (m.get('arms') or {}).values():
        out.update(loo_resid(list(zip(e.get('runs') or [], e.get('vals') or [])), sign))
    return out


def seqkey(x):
    try:
        return float(x.get('seq'))
    except (TypeError, ValueError):
        return 0.0


def fmt(v, nd=1, plus=True):
    if v is None:
        return '-'
    return ('%+.*f' if plus else '%.*f') % (nd, v)


def report(R, metrics, methods, putil, emhz, src='-'):
    lines = []
    w = lines.append
    kept = [x for x in R.get('runs') or [] if x.get('keep')]
    byname = dict((x['name'], x) for x in kept)
    flag = flagged_runs(R, putil, emhz)
    w('# Noise case (Agent 7, task #6)')
    w('')
    w('- report: `%s`; dir: `%s`; reference arm %s; kept runs %d' % (src, R.get('dir'), R.get('ref'), len(kept)))
    w('- residual = leave-one-out: 100 (v / GM of the other runs of the same arm - 1) %, + = slower (fps inverted); '
      'the ANCOVA methods (L, D) use their adjusted values.')
    desc = []
    for nm in flag:
        x, c = byname[nm], byname[nm].get('cov') or {}
        desc.append('%s (P util %s %%, E %s MHz, light share %s)' % (nm, fmt(c.get('p_util'), 1, False),
                                                                   fmt(c.get('e_mhz'), 0, False),
                                                                   fmt(x.get('ls_T'), 3, False)))
    w('- host-state flag: sys.json window P util >= %g %% and E MHz < %g: %s' % (putil, emhz,
                                                                               '; '.join(desc) or 'no run'))
    for metric in metrics:
        sign = SIGN.get(metric, -1)
        found = []
        for mid in methods:
            m = next((m for m in R.get('methods') or [] if m.get('method') == mid and m.get('key') == metric), None)
            if m is not None:
                found.append((mid, m, residuals(m, sign)))
        if not found:
            continue
        raw_mean = None
        w('')
        w('## %s: the flagged runs' % LABEL.get(metric, metric))
        w('')
        w('| method | %s | flagged mean | flagged mean / raw %% | RMS of the other runs | pooled CV %% | ref band %% |'
          % ' | '.join(flag or ['(none flagged)']))
        w('|---|%s---|---|---|---|---|' % ('---|' * max(1, len(flag))))
        for mid, m, res in found:
            fv = [res[nm] for nm in flag if nm in res]
            fmean = statistics.fmean(fv) if fv else None
            if mid == 'raw':
                raw_mean = fmean
            share = (100.0 * fmean / raw_mean) if (fmean is not None and raw_mean) else None
            other = [v for nm, v in res.items() if nm not in flag]
            rms = math.sqrt(statistics.fmean([v * v for v in other])) if other else None
            cells = [fmt(res.get(nm)) for nm in flag] or ['-']
            w('| %s | %s | %s | %s | %s | %s | %s |' % (mid, ' | '.join(cells), fmt(fmean), fmt(share, 0, False),
                                                       fmt(rms, 1, False), fmt(m.get('cv_pct'), 1, False),
                                                       fmt(m.get('band_pct'), 1, False)))
        w('')
        w('## %s: every kept run (residual %%, + = slower)' % LABEL.get(metric, metric))
        w('')
        w('| seq | run | arm | flag | %s |' % ' | '.join(mid for mid, _, _ in found))
        w('|---|---|---|---|%s' % ('---|' * len(found)))
        for x in sorted(kept, key=seqkey):
            w('| %s | %s | %s | %s | %s |' % (x.get('seq', '-'), x['name'], x.get('arm', '-'),
                                              'yes' if x['name'] in flag else '',
                                              ' | '.join(fmt(res.get(x['name'])) for _, _, res in found)))
    return '\n'.join(lines) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('report_json')
    ap.add_argument('-o', '--out')
    ap.add_argument('--metric', action='append', choices=sorted(SIGN))
    ap.add_argument('--putil', type=float, default=90.0)
    ap.add_argument('--emhz', type=float, default=600.0)
    ap.add_argument('--methods', default=','.join(DEFAULT_METHODS))
    a = ap.parse_args(argv)
    with open(a.report_json, encoding='utf-8') as f:
        R = json.load(f)
    text = report(R, a.metric or ['p50_ms', 'fps'], [s for s in a.methods.split(',') if s], a.putil, a.emhz,
                  a.report_json)
    if a.out:
        with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())

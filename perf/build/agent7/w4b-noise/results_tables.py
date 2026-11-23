#!/usr/bin/env python3
"""Per-method tables of arm deltas and noise bands, for RESULTS.md.

Agent 7, task #6 (was #30). Reads the report JSONs written by noise_methods.py
(W4b: report.json, W5: report-w5.json) and writes results-tables.md.

For each window and metric there is one row per method:
- the ref band (summary.md's rule on the method's values);
- the pooled within-arm CV of ln(value), and that CV over raw's CV;
- the 95 % band for 4 vs 4 runs;
- df;
- for each arm, the median delta (with the verdict against the ref band) and
  the GM delta with its pooled 95 % CI.
The paired within-round deltas follow.

Read-only, stdlib only, one process.

    python -B results_tables.py [-o results-tables.md] [NAME=report.json ...]
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INPUTS = ['W4b=' + os.path.join(HERE, 'report.json'),
                  'W5=' + os.path.join(HERE, 'report-w5.json')]
METRICS = ('median ms', 'fps', 'p99 ms', '1% low fps')
PAIRED_METRICS = ('median ms', 'fps')
# Most useful first; methods not listed here follow in the JSON's order.
ORDER = ('raw', 'T-std', 'B-block T-std', 'B-norm T-std', 'L-ls',
         'D-emhz+putil', 'D-emhz', 'D-putil', 'D-nongame',
         'A2-std', 'A2-light', 'A2-heavy', 'A-std', 'A-light', 'A-heavy',
         'T-light', 'T-heavy', 'C-frames', 'C-bins',
         'B-norm raw', 'B-block raw', 'B-norm A-std', 'B-norm A-heavy',
         'B-block A-heavy')


def fnum(v, nd=1, sign=True):
    if v is None:
        return '-'
    return ('%+.*f' if sign else '%.*f') % (nd, v)


def rank(name):
    return ORDER.index(name) if name in ORDER else len(ORDER)


def arm_cell(a):
    """'median delta verdict (n); GM delta [lo, hi]' with * when the CI excludes 0."""
    if not a or not a.get('n'):
        return '-'
    s = '%s %s (n=%d)' % (fnum(a.get('delta_pct')), a.get('verdict', '?'), a['n'])
    ci = a.get('ci_pct')
    if a.get('gm_delta_pct') is not None and ci and None not in ci:
        s += '; GM %s [%s, %s]%s' % (fnum(a['gm_delta_pct']), fnum(ci[0]), fnum(ci[1]),
                                     ' *' if a.get('ci_excludes_0') else '')
    return s


def method_name(m):
    name = m['method']
    covs = m.get('covs')
    if covs and not name.startswith('B-block'):
        name += ' (on %s)' % ', '.join(covs)
    return name


def window_section(name, path, rep):
    ref = rep['ref']
    arms = [a for a in rep['order'] if a != ref]
    kept = [r for r in rep['runs'] if r.get('keep')]
    out = ['## %s: `%s`, ref %s, arms %s' % (name, os.path.basename(rep['dir'].rstrip('\\/')),
                                              ref, ', '.join(arms)), '']
    out.append('- report: `%s`; kept runs %d; hT_ref %.3f; h2_ref %.3f; h_ref %.3f.'
               % (os.path.basename(path), len(kept), rep.get('hT_ref') or 0.0,
                  rep.get('h2_ref') or 0.0, rep.get('h_ref') or 0.0))
    out.append('- Arm cells: median delta vs %s in %% with the verdict against the %s band '
               '(`within`, `better`, `worse`), then the GM delta with the pooled 95 %% CI '
               '(`*` = the CI excludes 0).' % (ref, ref))
    out.append('')
    methods = rep['methods']
    raw_cv = dict((m['metric'], m.get('cv_pct')) for m in methods if m['method'] == 'raw')
    for metric in METRICS:
        rows = [m for m in methods if m['metric'] == metric]
        rows.sort(key=lambda m: rank(m['method']))
        out += ['### %s, %s' % (name, metric), '']
        hdr = ['method', 'runs', 'df', '%s band %%' % ref, 'pooled CV %', 'CV / raw CV',
               '95 % band 4 vs 4'] + arms
        out.append('| ' + ' | '.join(hdr) + ' |')
        out.append('|' + '---|' * len(hdr))
        for m in rows:
            marms = m.get('arms', {})
            runs = sum(a.get('n', 0) for a in marms.values())
            rc, cv = raw_cv.get(metric), m.get('cv_pct')
            ratio = '%.2f' % (cv / rc) if (rc and cv is not None) else '-'
            cells = [method_name(m), str(runs), str(m.get('df', '-')),
                     fnum(m.get('band_pct'), sign=False), fnum(cv, sign=False), ratio,
                     fnum(m.get('hw44_pct'), sign=False)]
            cells += [arm_cell(marms.get(a)) for a in arms]
            out.append('| ' + ' | '.join(cells) + ' |')
        out.append('')
    out += ['### %s, paired within-round deltas vs %s' % (name, ref), '',
            'Per arm, the deltas vs %s in the same round: median, range (max - min, pp), '
            'mean +- the 95 %% t half-width, and the rounds in which the arm\'s value is higher.' % ref, '']
    hdr = ['source', 'metric', 'arm', 'rounds', 'deltas %', 'median %', 'range pp',
           'mean +- 95 %', 'higher']
    out.append('| ' + ' | '.join(hdr) + ' |')
    out.append('|' + '---|' * len(hdr))
    for p in rep.get('paired', []):
        if p['metric'] not in PAIRED_METRICS:
            continue
        for a in arms:
            d = p['arms'].get(a)
            if not d or not d.get('n'):
                continue
            out.append('| %s | %s | %s | %s | %s | %s | %s | %s +- %s | %s of %d |' % (
                p['src'], p['metric'], a, ','.join(d.get('rounds', [])),
                ', '.join(fnum(x) for x in d.get('deltas', [])), fnum(d.get('med')),
                fnum(d.get('range'), sign=False), fnum(d.get('mean')),
                fnum(d.get('hw95'), sign=False), d.get('up', '-'), d['n']))
    out.append('')
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('inputs', nargs='*', help='NAME=report.json (default: W4b and W5)')
    ap.add_argument('-o', '--out', default=os.path.join(HERE, 'results-tables.md'))
    args = ap.parse_args(argv)
    inputs = args.inputs or DEFAULT_INPUTS
    out = ['# Per-method deltas and bands (Agent 7, task #6, was #30)', '',
           'Generated by `results_tables.py` from noise_methods.py\'s report JSONs. '
           'Method definitions: report.md / report-w5.md headers and DESIGN.md. '
           'The narrative and recommendation are in RESULTS.md.', '']
    for item in inputs:
        name, _, path = item.partition('=')
        if not path:
            name, path = os.path.splitext(os.path.basename(item))[0], item
        with open(path, encoding='utf-8') as f:
            rep = json.load(f)
        out += window_section(name, path, rep)
    text = '\n'.join(out).rstrip('\n') + '\n'
    with open(args.out, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    print('wrote %s (%d lines)' % (args.out, text.count('\n')))
    return 0


if __name__ == '__main__':
    sys.exit(main())

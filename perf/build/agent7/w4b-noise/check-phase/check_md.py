#!/usr/bin/env python3
"""Checker 1, part 2: the .md reports (report.md, report-w5.md) against my own numbers (mine-w4b.json, mine-w5.json
written by check_phase.py), at the displayed decimals, for the header refs, the Runs / Runs T tables (raw, T, A2
columns) and the band and CI tables of raw, T-std, T-light, T-heavy, A2-std, A2-light, A2-heavy and L-ls.

Usage: python -B build\\agent7\\w4b-noise\\check-phase\\check_md.py
"""
import json
import os
import re
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
NOISE = os.path.dirname(HERE)
PAIRS = (('W4b', os.path.join(NOISE, 'report.md'), os.path.join(HERE, 'mine-w4b.json')),
         ('W5', os.path.join(NOISE, 'report-w5.md'), os.path.join(HERE, 'mine-w5.json')))
LABEL = {'fps': ('fps', 1, 1), 'median ms': ('p50_ms', 3, -1), 'p99 ms': ('p99_ms', 2, -1),
         '1% low fps': ('low1_fps', 1, 1)}
MINE_METHODS = ('raw', 'T-std', 'T-light', 'T-heavy', 'A2-std', 'A2-light', 'A2-heavy', 'L-ls')
FIELD = {'raw': 'raw', 'T-std': 't_std', 'T-light': 't_L', 'T-heavy': 't_H', 'A2-std': 'a2_std', 'A2-light': 'a2_F',
         'A2-heavy': 'a2_S'}


def cells(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


def main():
    out = []
    log = out.append
    total_bad = 0
    for label, md, mj in PAIRS:
        with open(md, encoding='utf-8') as fh:
            lines = fh.read().splitlines()
        with open(mj, encoding='utf-8') as fh:
            M = json.load(fh)
        ref, order = M['ref'], M['order']
        others = [a for a in order if a != ref]
        bad, n = [], [0]

        def chk(where, disp, mine, nd):
            n[0] += 1
            if disp == '-' or mine is None:
                if (disp == '-') != (mine is None):
                    bad.append('%s: md %r, mine %r' % (where, disp, mine))
                return
            v = float(disp)
            if abs(mine - v) > 0.5 * 10 ** (-nd) * (1 + 1e-9) + 1e-12:
                bad.append('%s: md %s, mine %.*f (%.8g)' % (where, disp, nd, mine, mine))

        def eq(where, a, b):
            n[0] += 1
            if a != b:
                bad.append('%s: md %r, mine %r' % (where, a, b))

        text = '\n'.join(lines)
        m = re.search(r'h2_ref = ([0-9]+\.[0-9]+|-)', text)
        chk('header h2_ref', m.group(1) if m else 'missing', M['h2_ref'], 3)
        m = re.search(r'hT_ref = ([0-9]+\.[0-9]+|-)', text)
        chk('header hT_ref', m.group(1) if m else 'missing', M['hT_ref'], 3)
        sec, ri, rti = None, 0, 0
        seen = set()
        for ln in lines:
            if ln.startswith('## '):
                sec = ln[3:].strip()
                continue
            if not ln.startswith('|') or ln.startswith('|---'):
                continue
            c = cells(ln)
            if c[0] in ('method', 'seq', 'source', 'covariate', 'rolling median ms'):
                continue
            if sec == 'Bands and deltas per method' and c[0] in MINE_METHODS and c[1] in LABEL:
                key, nd, sign = LABEL[c[1]]
                S = M['methods'].get('%s %s' % (c[0], key))
                tag = '%s/%s' % (c[0], c[1])
                seen.add(('band', tag))
                if S is None:
                    bad.append('%s: in md, not in mine' % tag)
                    continue
                rvs = [s.strip() for s in c[2].split(',')]
                eq(tag + ' n ref vals', len(rvs), len(S['ref_vals']))
                for i, (dv, mv) in enumerate(zip(rvs, S['ref_vals'])):
                    chk('%s ref_vals[%d]' % (tag, i), dv, mv, nd)
                chk(tag + ' band', c[3], S['band_pct'], 1)
                chk(tag + ' cv', c[4], S['cv_pct'], 1)
                chk(tag + ' hw44', c[5], S['hw44_pct'], 1)
                for arm, cell in zip(others, c[6:]):
                    e = S['arms'].get(arm)
                    if cell == '-':
                        eq('%s %s present' % (tag, arm), False, e is not None and e.get('delta_pct') is not None)
                        continue
                    mm = re.match(r'([+-][0-9.]+) (in|better|worse) \(n=(\d+)\)$', cell)
                    if not mm or e is None:
                        bad.append('%s %s: cell %r, mine %r' % (tag, arm, cell, e))
                        continue
                    chk('%s %s delta' % (tag, arm), mm.group(1), e['delta_pct'], 1)
                    dp = e['delta_pct']
                    vd = 'in' if abs(dp) <= S['band_pct'] else ('better' if (dp > 0) == (sign > 0) else 'worse')
                    eq('%s %s verdict' % (tag, arm), mm.group(2), vd)
                    eq('%s %s n' % (tag, arm), int(mm.group(3)), e['n'])
            elif sec and sec.startswith('Pooled 95') and c[0] in MINE_METHODS and c[1] in LABEL:
                key, nd, sign = LABEL[c[1]]
                S = M['methods'].get('%s %s' % (c[0], key))
                tag = '%s/%s' % (c[0], c[1])
                seen.add(('ci', tag))
                if S is None:
                    bad.append('%s: in md CI table, not in mine' % tag)
                    continue
                eq(tag + ' df', int(c[2]), S['df'])
                for arm, cell in zip(others, c[3:]):
                    e = S['arms'].get(arm)
                    if cell == '-':
                        eq('%s %s ci present' % (tag, arm), False, bool(e and e.get('ci_pct')))
                        continue
                    mm = re.match(r'([+-][0-9.]+) \[([+-][0-9.]+), ([+-][0-9.]+)\]( \*)?$', cell)
                    if not mm or not e or not e.get('ci_pct'):
                        bad.append('%s %s: cell %r, mine %r' % (tag, arm, cell, e))
                        continue
                    chk('%s %s gm' % (tag, arm), mm.group(1), e['gm_delta_pct'], 1)
                    chk('%s %s ci_lo' % (tag, arm), mm.group(2), e['ci_pct'][0], 1)
                    chk('%s %s ci_hi' % (tag, arm), mm.group(3), e['ci_pct'][1], 1)
                    excl = e['ci_pct'][0] > 0 or e['ci_pct'][1] < 0
                    eq('%s %s excludes 0' % (tag, arm), bool(mm.group(4)), excl)
            elif sec == 'Runs':
                x = M['runs'][ri]
                ri += 1
                w = 'Runs row %d (%s)' % (ri, x['name'])
                eq(w + ' arm', c[2], x['arm'])
                eq(w + ' kept', c[3], 'yes' if x['keep'] else 'no')
                raw = x.get('raw') or {}
                chk(w + ' raw fps', c[4], raw.get('fps'), 1)
                chk(w + ' raw median', c[5], raw.get('p50_ms'), 3)
                chk(w + ' raw p99', c[6], raw.get('p99_ms'), 2)
                chk(w + ' h (A2)', c[15], x.get('h2'), 3)
                eq(w + ' A2 switches', c[16], '-' if x.get('switches2') is None else str(x['switches2']))
            elif sec == 'Runs: T split and host state':
                x = M['runs'][rti]
                rti += 1
                w = 'Runs T row %d (%s)' % (rti, x['name'])
                eq(w + ' arm', c[2], x['arm'])
                chk(w + ' ls own', c[4], x.get('ls_T'), 3)
                chk(w + ' hT', c[5], x.get('hT'), 3)
                chk(w + ' T-light fps', c[6], (x.get('t_L') or {}).get('fps'), 1)
                chk(w + ' T-light median', c[7], (x.get('t_L') or {}).get('p50_ms'), 3)
                chk(w + ' T-heavy fps', c[8], (x.get('t_H') or {}).get('fps'), 1)
                chk(w + ' T-std fps', c[9], (x.get('t_std') or {}).get('fps'), 1)
                chk(w + ' A2-light fps', c[10], (x.get('a2_F') or {}).get('fps'), 1)
        for mid in MINE_METHODS:
            for lab, (key, nd, sign) in LABEL.items():
                if M['methods'].get('%s %s' % (mid, key)) is not None:
                    for t in ('band', 'ci'):
                        if (t, '%s/%s' % (mid, lab)) not in seen:
                            bad.append('%s/%s: missing from the md %s table' % (mid, lab, t))
        eq('Runs rows', ri, len(M['runs']))
        eq('Runs T rows', rti, len(M['runs']))
        log('## %s: %s' % (label, md))
        log('- %d comparisons at the displayed decimals: %s' % (n[0], 'OK' if not bad else 'MISMATCH x%d' % len(bad)))
        for b in bad[:80]:
            log('    MISMATCH ' + b)
        # A2 coverage note
        kept = [x for x in M['runs'] if x['keep']]
        zero = [x['name'] for x in kept if not x.get('h2')]
        log('- A2 coverage: kept runs with h2 = 0 (no heavy frames, so no A2-heavy / A2-std value): %d of %d%s' % (
            len(zero), len(kept), (' (%s)' % ', '.join(zero)) if zero else ''))
        for key in ('fps',):
            S = M['methods'].get('A2-heavy %s' % key)
            if S:
                log('- A2-heavy %s runs per arm: %s; df %s' % (key, ', '.join(
                    '%s %d' % (a, e['n']) for a, e in S['arms'].items()), S['df']))
        log('- h2 per kept run: %s' % ', '.join('%s %.4f' % (x['name'], x.get('h2') or 0.0) for x in kept))
        log('')
        total_bad += len(bad)
    text = '\n'.join(out) + '\n'
    sys.stdout.write(text)
    with open(os.path.join(HERE, 'check-md.md'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())

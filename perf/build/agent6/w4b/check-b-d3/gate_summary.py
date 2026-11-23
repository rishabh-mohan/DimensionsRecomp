#!/usr/bin/env python3
"""check-b-d3 (Agent 6 task #5, read-only checker): summarise the 32 gate_logdiff.py JSONs written next to this
script (<brun>__vs__<arun>.json, B side = arm run, A side = warm d0 run) plus gate_exitcodes.csv (brun,arun,exit).
Stdlib only, single-threaded; run with python -B. Writes gate_summary.txt next to this script and prints it."""
import csv
import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
D0 = ['1542-d0-r1', '1558-d0-r2', '1604-d0-r3', '1611-d0-r4']
ARMS = [('B', ['1545-B-r1', '1551-B-r2', '1606-B-r3', '1613-B-r4']),
        ('d3', ['1547-d3-r1', '1553-d3-r2', '1600-d3-r3', '1615-d3-r4'])]


def load_codes():
    codes = {}
    with open(os.path.join(HERE, 'gate_exitcodes.csv'), encoding='utf-8-sig') as fh:
        for row in csv.DictReader(fh):
            codes[(row['brun'].strip(), row['arun'].strip())] = int(row['exit'])
    return codes


def main():
    codes = load_codes()
    out = []
    w = out.append
    for arm, runs in ARMS:
        w('=== arm %s vs warm d0 (gate B side = arm run, A side = d0 run) ===' % arm)
        w('%-12s %-11s %4s %-7s %4s %5s %4s %5s %4s  %s' % (
            'arm run', 'd0 run', 'exit', 'verdict', 'find', 'notes', 'new', 'gone', 'chg',
            'lines A/B | levels B | unimpl A/B | crit B | fail_counts B | boot A/B | files A/B | warn kinds/lines A, B'))
        agg = Counter()
        msgs, per_run, match_set = [], {}, Counter()
        for b in runs:
            verdicts = []
            for a in D0:
                jp = os.path.join(HERE, '%s__vs__%s.json' % (b, a))
                ex = codes.get((b, a))
                agg['pairs'] += 1
                if not os.path.exists(jp):
                    agg['missing_json'] += 1
                    w('%-12s %-11s %4s  NO JSON' % (b, a, ex))
                    verdicts.append('NOJSON/%s' % ex)
                    continue
                with open(jp, encoding='utf-8') as fh:
                    r = json.load(fh)
                d, v = r['diff'], r['verdict']
                verdicts.append('%s/%s' % (v, ex))
                agg['PASS' if v == 'PASS' else 'FAIL'] += 1
                if ex not in (0, 1) or (ex == 0) != (v == 'PASS'):
                    agg['exit_verdict_mismatch'] += 1
                agg['findings'] += len(r['findings'])
                agg['notes'] += len(r['notes'])
                agg['new'] += d['new_in_b_total']
                agg['gone'] += d['gone_in_b_total']
                agg['count_changes'] += d['count_changes_total']
                sa, sb = r['a'], r['b']
                w('%-12s %-11s %4s %-7s %4d %5d %4d %5d %4d  %d/%d | %s | %d/%d | %d | %s | %s/%s | %d/%d | %d/%d, %d/%d' % (
                    b, a, ex, v, len(r['findings']), len(r['notes']), d['new_in_b_total'], d['gone_in_b_total'],
                    d['count_changes_total'], sa['lines'], sb['lines'],
                    ' '.join('%s=%d' % kv for kv in sorted(sb['levels'].items())),
                    sa['unimplemented'], sb['unimplemented'], sb['critical'], sb['fail_counts'] or '{}',
                    sa['boot_lines_found'], sb['boot_lines_found'], len(sa['files']), len(sb['files']),
                    sa['warn_messages'], sa['warn_lines'], sb['warn_messages'], sb['warn_lines']))
                for f in r['findings']:
                    msgs.append('  FINDING %s vs %s: %s' % (b, a, f))
                for n in r['notes']:
                    msgs.append('  NOTE    %s vs %s: %s' % (b, a, n))
                for x in d['new_in_b']:
                    msgs.append('  NEW     %s vs %s: %d x %s' % (b, a, x['count'], x['msg']))
                for x in d['gone_in_b']:
                    msgs.append('  GONE    %s vs %s: %d x %s' % (b, a, x['count'], x['msg']))
                for x in d['count_changes']:
                    msgs.append('  CHANGE  %s vs %s: A %d B %d %s' % (b, a, x['a'], x['b'], x['msg']))
                for m in r['match']:
                    match_set[m] += 1
            per_run[b] = verdicts
        w('per arm run, verdict/exit vs %s:' % ', '.join(D0))
        for b in runs:
            w('  %-12s %s' % (b, '  '.join(per_run[b])))
        w('totals: ' + ', '.join('%s %d' % (k, agg[k]) for k in (
            'pairs', 'PASS', 'FAIL', 'findings', 'notes', 'new', 'gone', 'count_changes', 'exit_verdict_mismatch',
            'missing_json')))
        w('match-check strings (x pairs):')
        for m, c in sorted(match_set.items()):
            w('  %2d x %s' % (c, m))
        w('non-zero findings/notes/new/gone/count-change entries (%d):' % len(msgs))
        out.extend(msgs or ['  none'])
        w('')
    txt = '\n'.join(out)
    with open(os.path.join(HERE, 'gate_summary.txt'), 'w', encoding='utf-8') as fh:
        fh.write(txt + '\n')
    print(txt)


if __name__ == '__main__':
    main()

"""Summarise the 16 gate_logdiff JSONs (d11t B-side x d0 A-side) in this dir. Stdlib only, read-only."""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
rows = []
for p in sorted(glob.glob(os.path.join(HERE, '*__vs__*.json'))):
    name = os.path.basename(p)[:-5]
    b, a = name.split('__vs__')
    with open(p, 'r', encoding='utf-8') as fh:
        r = json.load(fh)
    d = r['diff']
    rows.append((b, a, r, d))
    print('%-14s vs %-11s verdict=%s findings=%d notes=%d new=%d gone=%d chg=%d | A lines=%d warnK=%d warnL=%d unimpl=%d crit=%d | B lines=%d warnK=%d warnL=%d unimpl=%d crit=%d boot=%s/%s' % (
        b, a, r['verdict'], len(r['findings']), len(r['notes']), d['new_in_b_total'], d['gone_in_b_total'],
        d['count_changes_total'], r['a']['lines'], r['a']['warn_messages'], r['a']['warn_lines'],
        r['a']['unimplemented'], r['a']['critical'], r['b']['lines'], r['b']['warn_messages'], r['b']['warn_lines'],
        r['b']['unimplemented'], r['b']['critical'], r['a']['boot_lines_found'], r['b']['boot_lines_found']))
    for f in r['findings']:
        print('    FINDING: %s' % f)
    for n in r['notes']:
        print('    NOTE: %s' % n)
    for x in d['new_in_b']:
        print('    NEW  %d  %s' % (x['count'], x['msg']))
    for x in d['gone_in_b']:
        print('    GONE %d  %s' % (x['count'], x['msg']))
    for x in d['count_changes']:
        print('    CHG  A%d B%d  %s' % (x['a'], x['b'], x['msg']))
print('pairs=%d all_pass=%s total_findings=%d total_new=%d total_gone=%d total_chg=%d' % (
    len(rows), all(r['verdict'] == 'PASS' for _, _, r, _ in rows), sum(len(r['findings']) for _, _, r, _ in rows),
    sum(d['new_in_b_total'] for *_, d in rows), sum(d['gone_in_b_total'] for *_, d in rows),
    sum(d['count_changes_total'] for *_, d in rows)))
# per-run side summaries (levels, match lines) once per run
seen = set()
for b, a, r, d in rows:
    for side, run in (('a', a), ('b', b)):
        if run in seen:
            continue
        seen.add(run)
        s = r[side]
        print('SIDE %-14s levels=%s fail=%s unimpl=%d reloc=%d poolcopy=%s slotreg=%d slotext=%d files=%d' % (
            run, json.dumps(s['levels'], sort_keys=True), json.dumps(s['fail_counts'], sort_keys=True),
            s['unimplemented'], s['reloc_lr_83F9B660'], json.dumps(s['poolcopy_callers'], sort_keys=True),
            s['slot_registered'], s['slot_extended'], len(s['files'])))

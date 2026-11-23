"""One-off check (helper of Agent 8): fps rank of flagged runs and arm fps medians with/without them.
Reads runs.csv in this dir only. Run with python -B."""
import csv, os, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(HERE, 'runs.csv'), newline='')))
order = []
for r in rows:
    if r['stamp'] not in order:
        order.append(r['stamp'])
for s in order:
    sc = [r for r in rows if r['stamp'] == s and r['scored'] == 'True']
    srt = sorted(sc, key=lambda r: float(r['fps_mean']))
    rank = {r['run']: i + 1 for i, r in enumerate(srt)}
    fl = [r for r in sc if r['flag'].strip() not in ('', '-')]
    print('%s %s n=%d lowest5: %s' % (sc[0]['window'], s, len(sc), ', '.join('%s %.1f' % (r['run'], float(r['fps_mean'])) for r in srt[:5])))
    for r in fl:
        print('  FLAG %s fps %.1f rel %s rank %d/%d ng_t %.2f' % (r['run'], float(r['fps_mean']), r['fps_rel'], rank[r['run']], len(sc), float(r['win_ngB_mean'])))
    arms = sorted(set(r['arm'] for r in sc))
    out = []
    for a in arms:
        al = [float(r['fps_mean']) for r in sc if r['arm'] == a]
        ex = [float(r['fps_mean']) for r in sc if r['arm'] == a and r not in fl]
        out.append('%s %.1f/%s(n%d)' % (a, st.median(al), ('%.1f' % st.median(ex)) if ex else '-', len(ex)))
    print('  arm fps med all/excl-flagged: ' + '; '.join(out))

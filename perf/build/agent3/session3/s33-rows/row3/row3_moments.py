"""#33 row 3: pick the screenshot moments from existing hidden-desktop runs (M3). Light: reads logs only.
Usage: python -B row3_moments.py --run <label>=<run dir> [...] [--top 12] [--out moments.txt]
Per run: FF (first slow-frame line) vs run.json started, the scene anchors (row3_log.events), and for every run the
1-s bins (relative to FF) with the most dropped draws / new pipelines. Bins are compared across runs to see how
stable the attract timing is relative to FF.
"""
import argparse, collections, datetime, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import row3_log

ap = argparse.ArgumentParser()
ap.add_argument('--run', action='append', required=True)
ap.add_argument('--top', type=int, default=12)
ap.add_argument('--out')
a = ap.parse_args()
lines = []
def say(s=''):
    lines.append(s); print(s)

for spec in a.run:
    label, run = spec.split('=', 1)
    rj = json.load(open(os.path.join(run, 'run.json'), encoding='utf-8-sig'))
    st = datetime.datetime.fromisoformat(rj['started'][:26])
    d = row3_log.parse(run)
    ff = d['ff']
    ev = row3_log.events(d)
    last = (d['frames'][-1][0] - ff).total_seconds() if ff else 0
    say('== %s  %s  cvars %s' % (label, os.path.basename(run), json.dumps(rj.get('cvars'))))
    say('   logs %s; FF = started + %.2f s; last frame FF+%.1f s; frames %d; resolve-after-drop lines %d'
        % (','.join(d['files']), (ff - st).total_seconds(), last, len(d['frames']), len(d['rad'])))
    say('   anchors (s after FF): ' + ', '.join('%s %.2f' % kv for kv in ev.items()))
    bins = collections.defaultdict(lambda: [0, 0, 0, 0.0])  # dropped, new, rad, max ms
    for (t, _, ms, new, dr) in d['frames']:
        b = int((t - ff).total_seconds())
        bins[b][0] += dr; bins[b][1] += new; bins[b][3] = max(bins[b][3], ms)
    for t in d['rad']:
        bins[int((t - ff).total_seconds())][2] += 1
    tot_dr = sum(v[0] for v in bins.values())
    say('   dropped draws total %d in %d 1-s bins' % (tot_dr, sum(1 for v in bins.values() if v[0])))
    key = 0 if tot_dr else 1
    top = sorted(bins.items(), key=lambda kv: -kv[1][key])[:a.top]
    say('   top 1-s bins by %s (FF+s: dropped/new/rad/max ms): ' % ('dropped' if key == 0 else 'new') +
        '; '.join('%d: %d/%d/%d/%.0f' % (b, v[0], v[1], v[2], v[3]) for b, v in sorted(top)))
    # Drop clusters (frames with dropped > 0, gaps < 0.5 s) relative to the first 3D frame (A3D).
    if 'first-3d' in ev and tot_dr:
        a3d = ff + datetime.timedelta(seconds=ev['first-3d'])
        cl = []
        for (t, _, ms, new, dr) in d['frames']:
            if dr <= 0:
                continue
            if cl and (t - cl[-1]['t1']).total_seconds() < 0.5:
                c = cl[-1]; c['t1'] = t; c['n'] += 1; c['sum'] += dr; c['max'] = max(c['max'], dr); c['new'] += new
            else:
                cl.append({'t0': t, 't1': t, 'n': 1, 'sum': dr, 'max': dr, 'new': new})
        big = sorted(sorted(cl, key=lambda c: -c['sum'])[:a.top], key=lambda c: c['t0'])
        say('   top drop clusters (A3D+s start..end, frames, dropped sum/max per frame, new in cluster): ' +
            '; '.join('%+.1f..%+.1f %df %d/%d n%d' % ((c['t0'] - a3d).total_seconds(), (c['t1'] - a3d).total_seconds(),
                                                    c['n'], c['sum'], c['max'], c['new']) for c in big))
    if 'first-3d' in ev:
        a3 = ev['first-3d']
        say('   anchors vs A3D: ' + ', '.join('%s %+.2f' % (k, v - a3) for k, v in ev.items()))
if a.out:
    with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')

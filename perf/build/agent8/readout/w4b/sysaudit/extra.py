#!/usr/bin/env python3
# extra.py - follow-up checks on sysaudit outputs (reads only the two sysaudit dirs + the run dirs listed in summary.json).
import csv, json, os, statistics, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))


def ff(x):
    try:
        return float(x)
    except Exception:
        return None


def load(p):
    with open(p, newline='', encoding='utf-8-sig') as fh:
        return list(csv.DictReader(fh))


def med(v):
    v = [x for x in v if x is not None]
    return statistics.median(v) if v else None


def mean(v):
    v = [x for x in v if x is not None]
    return sum(v) / len(v) if v else None


def f(x, nd=2):
    return '-' if x is None else f'{x:.{nd}f}'


def rng(v, nd=2):
    v = [x for x in v if x is not None]
    return f'{f(med(v), nd)} [{f(min(v), nd)}..{f(max(v), nd)}]' if v else '-'


def bins(S, t0, width=10):
    out = {}
    for s in S:
        k = int((s['epoch'] - t0) // width)
        out.setdefault(k, []).append(s)
    rows = []
    for k in sorted(out):
        X = out[k]
        rows.append(f"| {X[0]['phase']} | {X[0]['wall'][:8]} | {len(X)} | {f(mean([x['ngB'] for x in X]))} | {f(mean([x['ngU'] for x in X]))} | "
                     f"{f(mean([x['game'] for x in X]))} | {f(mean([x['p_util'] for x in X]), 1)} | {f(100 * mean([x['bE'] for x in X]), 1)} | {f(mean([x['e_eff'] for x in X]), 0)} |")
    return ['| phase | from | n | ng_t | ng_u | game | P util% | E busy% | E MHz |', '|---|---|---|---|---|---|---|---|---|'] + rows


def main():
    out_all = {}
    for tag, sub, trace_runs in (('w4b', 'w4b', ['1558-d0-r2', '1600-d3-r3', '1545-B-r1', '1547-d3-r1']),
                                 ('w5', 'w5', ['1808-s0-r2', '1817-base-r2', '1819-d11-r3', '1821-d11t-r3', '1757-base-r1'])):
        d = os.path.join(ROOT, 'build', 'agent8', 'readout', sub, 'sysaudit')
        summ = json.load(open(os.path.join(d, 'summary.json'), encoding='utf-8'))
        G = summ['groups']
        grp, rest = G['group_runs'], G['rest_runs']
        p90 = G['rest_pooled_p90']
        runs = {r['run']: r for r in summ['runs']}
        S = load(os.path.join(d, 'samples.csv'))
        for s in S:
            for k in ('epoch', 'ngB', 'ngU', 'ngA', 'game', 'p_util', 'e_util', 'p_eff', 'e_eff', 'bP_raw', 'bE_raw', 'busyB', 'utilLP', 'dt'):
                s[k] = ff(s.get(k))
            s['bP'] = None if s['bP_raw'] is None else min(1.0, s['bP_raw'])
            s['bE'] = None if s['bE_raw'] is None else min(1.0, s['bE_raw'])
        L = [f'# extra checks {tag}', '']
        # 1. bursts vs state
        W = [s for s in S if s['phase'] == 'window' and s['run'] in grp + rest]
        bu = [s for s in W if s['ngU'] is not None and s['ngU'] > p90['ngU']]
        bt = [s for s in W if s['ngB'] is not None and s['ngB'] > p90['ngB']]
        L.append(f"- window samples (scored): {len(W)}; ng_u > rest p90 ({f(p90['ngU'])}): {len(bu)}, of which E>=800 MHz: {sum(1 for s in bu if s['e_eff'] is not None and s['e_eff'] >= 800)}; "
                 f"ng_t > rest p90 ({f(p90['ngB'])}): {len(bt)}, of which E<800 MHz: {sum(1 for s in bt if s['e_eff'] is not None and s['e_eff'] < 800)}")
        fastW = [s for s in W if s['e_eff'] is not None and s['e_eff'] >= 800]
        slowW = [s for s in W if s['e_eff'] is not None and s['e_eff'] < 800]
        L.append(f"- window samples E>=800: n={len(fastW)}, ng_u med {f(med([s['ngU'] for s in fastW]))}, ng_t med {f(med([s['ngB'] for s in fastW]))}, E busy med {f(100 * med([s['bE'] for s in fastW]), 1)} %; "
                 f"E<800: n={len(slowW)}, ng_u med {f(med([s['ngU'] for s in slowW]))}, ng_t med {f(med([s['ngB'] for s in slowW]))}, E busy med {f(100 * med([s['bE'] for s in slowW]), 1)} %")
        # dt check
        dts = [s['dt'] for s in S if s['phase'] in ('window', 'warmup') and s['dt'] is not None]
        L.append(f"- sys.csv sample spacing in warm-up+window: median {f(med(dts), 3)} s, max {f(max(dts), 3)} s, intervals > 1.5 s: {sum(1 for x in dts if x > 1.5)}")
        big = [(s['run'], s['phase'], s['wall'][:8], round(s['dt'], 2)) for s in S if s['phase'] in ('window', 'warmup') and s['dt'] is not None and s['dt'] > 1.5]
        if big:
            L.append('  - gaps: ' + '; '.join(f'{a} {b} {c} dt={e}' for a, b, c, e in big[:20]))
        # 2. state-matched per run (slow samples only)
        L += ['', '## Window, slow-state samples only (E < 800 MHz): per-run medians', '',
              '| run | grp | n slow | ng_t | ng_u | game | P busy% | E busy% | P util% | n fast | ng_t fast | ng_u fast |', '|---|---|---|---|---|---|---|---|---|---|---|---|']
        per = {}
        for name in sorted(grp + rest):
            X = [s for s in W if s['run'] == name and s['e_eff'] is not None and s['e_eff'] < 800]
            Y = [s for s in W if s['run'] == name and s['e_eff'] is not None and s['e_eff'] >= 800]
            per[name] = {'n': len(X), 'ngB': med([s['ngB'] for s in X]), 'ngU': med([s['ngU'] for s in X]), 'game': med([s['game'] for s in X]),
                         'bP': med([s['bP'] for s in X]), 'bE': med([s['bE'] for s in X]), 'pu': med([s['p_util'] for s in X])}
            L.append(f"| {name} | {'G' if name in grp else 'rest'} | {len(X)} | {f(per[name]['ngB'])} | {f(per[name]['ngU'])} | {f(per[name]['game'])} | "
                     f"{f(None if per[name]['bP'] is None else 100 * per[name]['bP'], 1)} | {f(None if per[name]['bE'] is None else 100 * per[name]['bE'], 1)} | {f(per[name]['pu'], 1)} | "
                     f"{len(Y)} | {f(med([s['ngB'] for s in Y]))} | {f(med([s['ngU'] for s in Y]))} |")
        L.append('')
        for k, lab in (('ngB', 'ng_t'), ('ngU', 'ng_u'), ('pu', 'P util'), ('game', 'game')):
            gv = [per[n][k] for n in grp if per[n]['n'] >= 5]
            rv = [per[n][k] for n in rest if per[n]['n'] >= 5]
            above = [n for n in grp if per[n]['n'] >= 5 and rv and per[n][k] is not None and per[n][k] > max(x for x in rv if x is not None)]
            L.append(f"- slow-state {lab}: {G['group_name']} {rng(gv)} vs rest {rng(rv)}; above rest max: {', '.join(above) or '-'} (runs with >= 5 slow samples)")
        # 3. traces
        for name in trace_runs:
            r = runs.get(name)
            if not r:
                continue
            X = [s for s in S if s['run'] == name and s['phase'] in ('boot', 'warmup', 'window')]
            t0 = r['ffe'] if r.get('ffe') else X[0]['epoch']
            L += ['', f"## 10 s bins from first frame: {name} (fps {r['fps']})", '']
            L += bins([s for s in X if s['phase'] in ('warmup', 'window')], t0)
        # 1757 check
        if tag == 'w5':
            r = runs['1757-base-r1']
            rd = os.path.join(ROOT, 'build', 'agent8', 'matrix', '20261122-1756', 'runs', '1757-base-r1')
            rj = json.load(open(os.path.join(rd, 'run.json'), encoding='utf-8-sig'))
            L += ['', '## 1757-base-r1 window coverage', '',
                  f"- run.json: measure_start {rj.get('measure_start')}, measure_end {rj.get('measure_end')}, window_wall_s {rj.get('window_wall_s')}, window_cpu_cores_mean {rj.get('window_cpu_cores_mean')}, ff {rj.get('ff_signal_epoch_s')}"]
            P = load(os.path.join(rd, 'proc.csv'))
            L.append('- proc.csv rows: %d; last 4: %s' % (len(P), ' || '.join(f"t={p['t_s']} ph={p['phase']} cpu_s={p['cpu_s']} cores={p['cpu_cores']} note={p['note']}" for p in P[-4:])))
            pm = [p for p in P if p.get('phase') == 'measure']
            L.append('- proc measure rows: %d, t %s..%s' % (len(pm), pm[0]['t_s'] if pm else '-', pm[-1]['t_s'] if pm else '-'))
            Wr = [s for s in S if s['run'] == '1757-base-r1' and s['phase'] == 'window']
            L.append('- window sys samples: %d, game None: %d, walls %s..%s, dt>1.5: %s' % (len(Wr), sum(1 for s in Wr if s['game'] is None), Wr[0]['wall'], Wr[-1]['wall'],
                                                                                         [(s['wall'][:8], round(s['dt'], 2)) for s in Wr if s['dt'] and s['dt'] > 1.5]))
        txt = '\n'.join(L) + '\n'
        with open(os.path.join(d, 'extra.md'), 'w', encoding='utf-8') as fh:
            fh.write(txt)
        print(txt)


if __name__ == '__main__':
    main()

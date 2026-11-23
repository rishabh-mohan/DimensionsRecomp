#!/usr/bin/env python3
"""S4 u diagnostic over the no-input 3D attract (Agent 12, run-2 task #13).

Finds the attract landmarks in perf.csv with harness/attract-report.py's rules:
  front end = first 220/534 frame; EXIT = first 220/540 frame after it (the fade);
  A0 = first 218/222 frame after EXIT (the load before the attract);
  H0 = first 2823/366575 frame after A0, else the first frame after A0 with >= 2000 draws (anchor_fallback).
Rows are timed like attract-report.py: a row's time is its start, the sum of the earlier rows'
frame_time_us ("perf s"). The run's "S4 upload hash" lines are scored with bench/agent12/s4_uhash.py by S4
frame number (S4 frame N = perf.csv data row N, +--offset), so log rotation can't shift a window.

Windows: front end (front end .. EXIT), A0 .. H0, H0 .. H0+150 s (heavy 3D, the primary), attract-report's
default window (H0+6.5 s for 11 s), the tail (H0+170 s .. end), and 10 s buckets over H0 .. H0+150 s.

usage: python s4_uhash_attract.py <run dir> [--json OUT] [--offset 0] [--span 150]
"""
import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s4_uhash as U  # noqa: E402


def load_perf(run):
    rows, t = [], 0.0
    with open(os.path.join(run, 'perf.csv'), newline='', encoding='utf-8', errors='replace') as f:
        for i, row in enumerate(csv.DictReader(f), 1):
            try:
                ft = float(row['frame_time_us'] or 0) / 1e6
                d = int(float(row['draw_calls'] or 0))
                v = int(float(row['vertices_processed'] or 0))
            except (KeyError, TypeError, ValueError):
                continue
            rows.append({'i': i, 't': t, 'd': d, 'v': v, 'ms': ft * 1000.0})
            t += ft
    return rows


def first(rows, start, pred):
    if start is None:
        return None
    for k in range(start, len(rows)):
        if pred(rows[k]):
            return k
    return None


def sig_is(s):
    d, v = (int(x) for x in s.split('/'))
    return lambda r: r['d'] == d and r['v'] == v


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('run')
    ap.add_argument('--json')
    ap.add_argument('--offset', type=int, default=0, help='S4 frame = perf row + offset (default 0)')
    ap.add_argument('--span', type=float, default=150.0, help='primary window length after H0, s')
    a = ap.parse_args()
    rows = load_perf(a.run)
    if not rows:
        sys.exit('no perf.csv rows')
    fe = first(rows, 0, sig_is('220/534'))
    ex = first(rows, None if fe is None else fe + 1, sig_is('220/540'))
    a0 = first(rows, None if ex is None else ex + 1, sig_is('218/222'))
    h0 = first(rows, None if a0 is None else a0 + 1, sig_is('2823/366575'))
    fallback = False
    if a0 is not None and h0 is None:
        h0 = first(rows, a0 + 1, lambda r: r['d'] >= 2000)
        fallback = True
    end_t = rows[-1]['t']
    lm = {}
    for name, k in (('front_end', fe), ('exit', ex), ('a0', a0), ('h0', h0)):
        lm[name] = None if k is None else {'row': rows[k]['i'], 'perf_s': round(rows[k]['t'], 2)}
    print('perf.csv: %d rows, %.1f perf s' % (len(rows), end_t))
    print('landmarks: ' + '; '.join('%s %s' % (n, 'none' if v is None else 'row %d at perf %.2f s'
                                               % (v['row'], v['perf_s'])) for n, v in lm.items())
          + ('; H0 by fallback (first >= 2000 draws)' if fallback else ''))

    files = U.resolve([a.run])
    s4, slow, first_idx = U.parse(files)
    print('S4 lines %d (frames %s..%s), slow-frame lines %d, first slow index %s, files %d'
          % (len(s4), s4[0]['frame'] if s4 else '-', s4[-1]['frame'] if s4 else '-', slow, first_idx,
             len(files)))

    def span(t0, t1):
        ks = [k for k in range(len(rows)) if t0 <= rows[k]['t'] < t1]
        return ks

    def score(name, ks):
        if not ks:
            print('%-14s no perf rows' % name)
            return None
        fa, fb = rows[ks[0]]['i'] + a.offset, rows[ks[-1]]['i'] + a.offset
        s = U.summarize(s4, slow, 0, 0, (fa, fb), [5, 8, 15], first_idx)
        draws = sorted(rows[k]['d'] for k in ks)
        ms = sorted(rows[k]['ms'] for k in ks)
        s['perf_s'] = [round(rows[ks[0]]['t'], 2), round(rows[ks[-1]]['t'], 2)]
        s['perf_rows'] = len(ks)
        s['median_draws'] = draws[len(draws) // 2]
        s['median_frame_ms'] = round(ms[len(ms) // 2], 2)
        if not s.get('frames') or s.get('u_block') is None:
            print('%-14s perf %7.1f-%7.1f s rows %5d frames %s: no u (S4 frames %d..%d)'
                  % (name, s['perf_s'][0], s['perf_s'][1], len(ks), s.get('frames'), fa, fb))
            return s
        ub = s['u_block_per_frame']
        print('%-14s perf %7.1f-%7.1f s n=%5d draws~%5d ms~%7.1f | u_block %.4f (pf p10/p50/p90 '
              '%s/%s/%s) u_page %.4f | KB/f %7.1f | CB/f %6.2f B/f %6.2f | P1 %s..%s KB/f'
              % (name, s['perf_s'][0], s['perf_s'][1], s['frames'], s['median_draws'],
                 s['median_frame_ms'], s['u_block'], ub['p10'], ub['p50'], ub['p90'], s['u_page'],
                 s['upload_kb_per_frame']['mean'], s['changed_blocks_per_frame']['mean'],
                 s['blocks_per_frame']['mean'], s['p1_reupload_kb_per_frame_lower'],
                 s['p1_reupload_kb_per_frame_upper']))
        return s

    out = {'run': os.path.abspath(a.run), 'landmarks': lm, 'anchor_fallback': fallback,
           's4_lines': len(s4), 'slow_lines': slow, 'first_slow_index': first_idx, 'windows': {},
           'buckets10': []}
    if fe is not None and ex is not None:
        out['windows']['front_end'] = score('front end', list(range(fe, ex)))
    if a0 is not None and h0 is not None:
        out['windows']['a0_to_h0'] = score('A0..H0', list(range(a0, h0)))
    if h0 is not None:
        t_h = rows[h0]['t']
        out['windows']['h0_span'] = score('H0..+%gs' % a.span, span(t_h, t_h + a.span))
        out['windows']['default_window'] = score('H0+6.5..17.5', span(t_h + 6.5, t_h + 17.5))
        out['windows']['tail'] = score('H0+170..end', span(t_h + 170.0, end_t + 1.0))
        vals = []
        t = 0.0
        while t < a.span:
            s = score('  +%3d s' % t, span(t_h + t, t_h + t + 10.0))
            if s and s.get('u_block') is not None:
                out['buckets10'].append({'from': t, 'frames': s['frames'], 'u_block': s['u_block'],
                                         'kb': s['upload_kb_per_frame']['mean'],
                                         'draws': s['median_draws']})
                vals.append(s['u_block'])
            t += 10.0
        if vals:
            print('10 s buckets over H0..+%gs: %d, u_block min %.4f p50 %.4f max %.4f'
                  % (a.span, len(vals), min(vals), U.pct(vals, 0.5), max(vals)))
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=1)
        print('wrote', a.json)
    return 0 if h0 is not None else 1


if __name__ == '__main__':
    sys.exit(main())

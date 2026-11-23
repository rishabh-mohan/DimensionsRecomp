#!/usr/bin/env python3
"""Agent 6, task #25: align frames.csv, perf.csv, samples.csv and game.log for one run.

Read-only, stdlib only, single-threaded.  All times are seconds since the harness
launch (run.json "started"), which is the base samples.csv uses for t_s.

frames.csv and perf.csv carry no clock, so each row's end time is T0 + the cumulative
interval.  T0 is bracketed from the buffered flushes seen in samples.csv: a row that is
on disk at sample k ended at or before t_k, and the first row not yet on disk was
written after t_(k-1).

usage: python align.py <run_dir> [--from S] [--to S] [--frames 16321,16322] [--slow 250]
"""
import argparse
import bisect
import datetime as dt
import json
import os
import re
import sys
from collections import Counter, defaultdict

LOG_RE = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\] \[(\w+)\] \[(\w+)\] \[t(\d+)\] (.*)$')
KEY_RE = re.compile(r'STUCK|Minidump|teardown|recipe|FATAL|deadlock|timed out|device lost|removed', re.I)


def parse_started(s):
    m = re.match(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(\.\d+)?', s)
    base = dt.datetime.strptime(m.group(1), '%Y-%m-%dT%H:%M:%S')
    return base + dt.timedelta(seconds=float(m.group(2) or 0.0))


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load_samples(path):
    rows = []
    with open(path, encoding='utf-8', newline='') as f:
        header = f.readline().strip().split(',')
        for line in f:
            parts = line.rstrip('\r\n').split(',', len(header) - 1)
            if len(parts) < len(header) - 1:
                continue
            d = dict(zip(header, parts))
            rows.append({'t': fnum(d.get('t_s')), 'cpu': fnum(d.get('cpu_s')),
                         'threads': fnum(d.get('threads')), 'handles': fnum(d.get('handles')),
                         'log': fnum(d.get('log_bytes')), 'perf': fnum(d.get('perf_csv_bytes')),
                         'frames': fnum(d.get('frames_csv_bytes')),
                         'note': (d.get('note') or '').strip()})
    return rows


def load_csv_offsets(path, wanted):
    """Rows with their end byte offset; numeric columns in `wanted` only."""
    rows = []
    with open(path, 'rb') as f:
        head = f.readline()
        off = len(head)
        header = head.decode('utf-8', 'replace').strip().split(',')
        idx = {k: header.index(k) for k in wanted if k in header}
        for raw in f:
            off += len(raw)
            if not raw.endswith(b'\n'):
                break
            parts = raw.decode('utf-8', 'replace').strip().split(',')
            if len(parts) != len(header):
                continue
            r = {'end_off': off}
            for k, i in idx.items():
                r[k] = fnum(parts[i])
            rows.append(r)
    return header, rows


def add_cum(rows, key, scale):
    c = 0.0
    for r in rows:
        r['cum0'] = c
        c += (r.get(key) or 0.0) * scale
        r['cum'] = c


def fit_t0(rows, samples, key):
    """Bracket T0 from flushes.  Returns (lo, hi, n_flushes, n_on_row_boundary, worst)."""
    ends = [r['end_off'] for r in rows]
    lo, hi = -1e18, 1e18
    lo_arg = hi_arg = None
    nflush = boundary = 0
    prev_t = prev_b = None
    for s in samples:
        b = s[key]
        if b is None or s['t'] is None:
            continue
        if prev_b is not None and b > prev_b and rows:
            nflush += 1
            j = bisect.bisect_right(ends, b) - 1  # last row fully on disk
            if j >= 0 and ends[j] == b:
                boundary += 1
                up, low = j, j + 1
            else:
                up, low = j + 1, j + 2  # a partial row is on disk: it was written by t_k
            if 0 <= up < len(rows):
                ub = s['t'] - rows[up]['cum']
                if ub < hi:
                    hi, hi_arg = ub, (s['t'], up)
            if 0 <= low < len(rows):
                lb = prev_t - rows[low]['cum']
                if lb > lo:
                    lo, lo_arg = lb, (prev_t, low)
        prev_t, prev_b = s['t'], b
    return lo, hi, nflush, boundary, lo_arg, hi_arg


def sig(msg):
    m = re.sub(r'0x[0-9a-fA-F]+|\b[0-9a-fA-F]{6,}\b|\d+(\.\d+)?', '#', msg)
    return m[:70]


def load_log(path, started):
    lines = []
    with open(path, 'rb') as f:
        off = 0
        for raw in f:
            off += len(raw)
            text = raw.decode('utf-8', 'replace').rstrip('\r\n')
            m = LOG_RE.match(text)
            if not m:
                continue
            wall = dt.datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S.%f')
            lines.append({'t': (wall - started).total_seconds(), 'wall': m.group(1)[11:],
                          'lvl': m.group(2), 'cat': m.group(3), 'tid': int(m.group(4)),
                          'msg': m.group(5), 'end_off': off})
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run')
    ap.add_argument('--from', dest='t_from', type=float)
    ap.add_argument('--to', dest='t_to', type=float)
    ap.add_argument('--frames', default='')
    ap.add_argument('--slow', type=float, default=250.0)
    ap.add_argument('--maxkey', type=int, default=60)
    a = ap.parse_args()
    run = a.run
    j = json.load(open(os.path.join(run, 'run.json'), encoding='utf-8-sig'))
    started = parse_started(j['started'])
    samples = load_samples(os.path.join(run, 'samples.csv'))
    fcols = ['frame', 'interval_ms', 'draw_calls', 'present_cpu_ms', 'sync_ms', 'frame_slot_wait_ms',
             'texture_ms', 'pipeline_creations', 'pipeline_creation_ms', 'pipeline_ms', 'issue_ms',
             'acquire_cpu_ms', 'swap_present_cpu_ms']
    _, frames = load_csv_offsets(os.path.join(run, 'frames.csv'), fcols)
    add_cum(frames, 'interval_ms', 1e-3)
    pcols = ['frame_time_us', 'draw_calls', 'active_threads', 'critical_region_contentions',
             'pipeline_cache_misses', 'functions_dispatched', 'interrupt_dispatches']
    _, perf = load_csv_offsets(os.path.join(run, 'perf.csv'), pcols)
    add_cum(perf, 'frame_time_us', 1e-6)
    log = load_log(os.path.join(run, 'game.log'), started)

    print('run      :', run)
    print('started  :', j['started'], '| exe', j.get('exe_sha256', '')[:8], '| elapsed', j.get('elapsed_s'),
          '| close_sent', j.get('close_sent_s'), '| exit', j.get('exit_code'), '| dumps', len(j.get('dumps') or []))
    if log:
        print('first log line at %.3f s after launch (log-relative = launch-relative - %.3f)' % (log[0]['t'], log[0]['t']))
    print('frames rows %d, sum interval %.2f s | perf rows %d, sum frame_time %.2f s' % (
        len(frames), frames[-1]['cum'] if frames else 0, len(perf), perf[-1]['cum'] if perf else 0))

    fits = {}
    for name, rows, key in (('frames', frames, 'frames'), ('perf', perf, 'perf')):
        lo, hi, n, nb, la, ha = fit_t0(rows, samples, key)
        fits[name] = (lo, hi)
        ok = 'OK' if lo <= hi else 'CONFLICT (model wrong)'
        print('T0[%s]: lo %.3f hi %.3f width %.3f s | %d flushes, %d on row boundaries | %s | lo from %s, hi from %s'
              % (name, lo, hi, hi - lo, n, nb, ok, la, ha))
    lo, hi = fits['frames']
    t0 = (lo + hi) / 2 if lo <= hi else hi
    plo, phi = fits['perf']
    pt0 = (plo + phi) / 2 if plo <= phi else phi
    print('using T0 frames = %.3f s, perf = %.3f s (frame row i ends at T0 + cum_i)' % (t0, pt0))

    # perf <-> frames row offset: best match of interval_ms vs frame_time_us
    best = None
    for k in range(-3, 4):
        hits = tot = 0
        for i in range(0, min(len(frames), len(perf)), 7):
            p = i + k
            if 0 <= p < len(perf):
                tot += 1
                fi, pf = frames[i]['interval_ms'], perf[p]['frame_time_us']
                if fi is not None and pf is not None and abs(fi - pf / 1000.0) < 0.05:
                    hits += 1
        if tot and (best is None or hits > best[1]):
            best = (k, hits, tot)
    poff = best[0] if best else 0
    print('perf row = frames row %+d (%d/%d sampled rows match within 0.05 ms)' % (poff, best[1], best[2]))

    want = [int(x) for x in a.frames.split(',') if x.strip()]
    byframe = {int(r['frame']): i for i, r in enumerate(frames) if r.get('frame') is not None}
    if a.t_from is None or a.t_to is None:
        spans = [(t0 + frames[byframe[f]]['cum0'], t0 + frames[byframe[f]]['cum']) for f in want if f in byframe]
        if spans:
            a.t_from = min(s for s, _ in spans) - 10 if a.t_from is None else a.t_from
            a.t_to = max(e for _, e in spans) + 10 if a.t_to is None else a.t_to
        else:
            a.t_from, a.t_to = 0.0, 1e9
    w0, w1 = a.t_from, a.t_to
    print('window   : %.1f .. %.1f s after launch' % (w0, w1))

    # fps per 10 s from the first frame
    if frames:
        first_end = t0 + frames[0]['cum']
        bins = Counter(int((t0 + r['cum'] - first_end) // 10) for r in frames)
        print('fps per 10 s from the first frame end (%.2f s): %s' % (
            first_end, ' '.join('%d:%.1f' % (first_end + 10 * b, bins[b] / 10.0) for b in sorted(bins))))

    print('\n== samples in window (t, dcpu, threads, handles, dlog, dframes, dperf, note)')
    prev = None
    for s in samples:
        if prev is not None and s['t'] is not None and w0 <= s['t'] <= w1:
            def d(k):
                if s[k] is None or prev[k] is None:
                    return '-'
                return '%d' % (s[k] - prev[k])
            print('%6.1f  %5.2f  %3d  %5d  %7s  %7s  %6s  %s' % (
                s['t'], (s['cpu'] or 0) - (prev['cpu'] or 0), s['threads'] or 0, s['handles'] or 0,
                d('log'), d('frames'), d('perf'), s['note']))
        prev = s

    # log flush check: bytes logged by timestamp vs bytes on disk
    print('\n== log on disk vs log by timestamp (bytes), window samples')
    lt = [l['t'] for l in log]
    for s in samples:
        if s['t'] is not None and w0 <= s['t'] <= w1 and s['log'] is not None:
            k = bisect.bisect_right(lt, s['t']) - 1
            by_ts = log[k]['end_off'] if k >= 0 else 0
            print('%6.1f disk %7d  stamped-by-t %7d  buffered %6d' % (s['t'], s['log'], by_ts, by_ts - s['log']))

    print('\n== frames in window with interval >= %.0f ms or pipeline creations (launch-relative s)' % a.slow)
    print(' frame    start      end   interval  pso_n  pso_ms  present  draws  sync_ms  slot_ms  tex_ms  | perf: thr crc miss')
    for i, r in enumerate(frames):
        st, en = t0 + r['cum0'], t0 + r['cum']
        if en < w0 or st > w1:
            continue
        if (r['interval_ms'] or 0) >= a.slow or (r['pipeline_creations'] or 0) > 0 or int(r['frame'] or -1) in want:
            p = perf[i + poff] if 0 <= i + poff < len(perf) else {}
            print('%6d  %7.3f  %7.3f  %8.1f  %5d  %7.1f  %7.1f  %5d  %7.1f  %7.1f  %6.1f  | %3s %3s %4s' % (
                r['frame'], st, en, r['interval_ms'] or 0, r['pipeline_creations'] or 0,
                r['pipeline_creation_ms'] or 0, r['present_cpu_ms'] or 0, r['draw_calls'] or 0,
                r['sync_ms'] or 0, r['frame_slot_wait_ms'] or 0, r['texture_ms'] or 0,
                '%d' % p['active_threads'] if p.get('active_threads') is not None else '-',
                '%d' % p['critical_region_contentions'] if p.get('critical_region_contentions') is not None else '-',
                '%d' % p['pipeline_cache_misses'] if p.get('pipeline_cache_misses') is not None else '-'))

    win = [l for l in log if w0 <= l['t'] <= w1]
    print('\n== log lines in window: %d; per thread: %s' % (
        len(win), ', '.join('t%d=%d' % kv for kv in Counter(l['tid'] for l in win).most_common())))
    print('\n== per-thread silences >= 1.0 s inside the window (gap between consecutive lines)')
    byt = defaultdict(list)
    for l in log:
        byt[l['tid']].append(l)
    for tid, ls in sorted(byt.items(), key=lambda kv: -len(kv[1])):
        for x, y in zip(ls, ls[1:]):
            if y['t'] >= w0 and x['t'] <= w1 and y['t'] - x['t'] >= 1.0:
                print('t%-6d %8.3f -> %8.3f  (%5.2f s)  before: %s | after: %s' % (
                    tid, x['t'], y['t'], y['t'] - x['t'], x['msg'][:70], y['msg'][:70]))

    print('\n== per-second signatures (thread: count x signature), window')
    per = defaultdict(Counter)
    for l in win:
        per[(int(l['t']), l['tid'])][sig(l['msg'])] += 1
    for (sec, tid) in sorted(per):
        c = per[(sec, tid)]
        print('%4d t%-6d %s' % (sec, tid, ' | '.join('%dx %s' % (n, s) for s, n in c.most_common(3))))

    print('\n== key lines in window (warn+, STUCK, Minidump, teardown, recipe...)')
    n = 0
    for l in win:
        if l['lvl'] in ('warning', 'error', 'critical') or KEY_RE.search(l['msg']):
            n += 1
            if n <= a.maxkey:
                print('%8.3f %s t%-6d %-8s %s' % (l['t'], l['wall'], l['tid'], l['lvl'], l['msg'][:190]))
    if n > a.maxkey:
        print('... %d more key lines' % (n - a.maxkey))

    for f in want:
        if f not in byframe:
            print('\nframe %d: not in frames.csv' % f)
            continue
        i = byframe[f]
        r = frames[i]
        st, en = t0 + r['cum0'], t0 + r['cum']
        inside = [l for l in log if st <= l['t'] <= en]
        print('\n== frame %d: %.3f .. %.3f s (+-%.3f), interval %.1f ms, pso %d / %.1f ms; %d log lines inside: %s' % (
            f, st, en, (hi - lo) / 2 if lo <= hi else float('nan'), r['interval_ms'], r['pipeline_creations'] or 0,
            r['pipeline_creation_ms'] or 0, len(inside),
            ', '.join('t%d=%d' % kv for kv in Counter(l['tid'] for l in inside).most_common())))
        for tid in sorted(set(l['tid'] for l in inside)):
            ls = [l for l in inside if l['tid'] == tid]
            print('   t%-6d first %8.3f %s' % (tid, ls[0]['t'], ls[0]['msg'][:110]))
            print('   t%-6d last  %8.3f %s' % (tid, ls[-1]['t'], ls[-1]['msg'][:110]))
    return 0


if __name__ == '__main__':
    sys.exit(main())

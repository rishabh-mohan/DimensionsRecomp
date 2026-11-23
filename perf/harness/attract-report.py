#!/usr/bin/env python3
"""harness/attract-report.py - the front-end idle exit and the no-input 3D attract sequence, from perf.csv (task #16,
session 3, Agent 3). Python 3 stdlib only, one thread. Agent runs sit on a hidden desktop: everything from them is
FUNCTIONAL ONLY. A timing needs a user-started run on the interactive desktop (Agent 8's runner).

  python harness/attract-report.py RUN [RUN ...] [--anchor 2823/366575] [--offset 6.5] [--seconds 11] [--min-rows 110]
         [--heavy-draws 2000] [--stall-ms 1000] [--window-stall-ms 250] [--peak-draws 9800] [--sub 18.2:2.3]
         [--steady-ms 250] [--shots-min 8] [--floor 60] [--label 'FUNCTIONAL ONLY'] [--json OUT] [--out TXT]
The defaults are the proposed timing window (perf-notes/agent3-run-harness.md, section 7.4): H0 + 6.5 s for 11 s, a
steady 4-8k-draw stretch (8019/1043795 -> 5145/879111 or 5194/879213). The cold Xenos shader storage (a fresh
<run>/user in every run) puts first-use compile stalls at fixed points around it (perf-notes/agent6-attract-stalls.md,
section 8): the last one before it runs H0 + 4.63-5.36 s (730 ms in devoff2), and after it the heavy segment (>= 9.8k
draws, throughput-bound) starts at H0 + 18.2 s, followed by the 12.4k-draw shot at H0 + 20.9 s (a 4-6 s stall, pm 67).
--sub reports the heavy segment (H0 + 18.2 s for 2.3 s) as an info sub-window; agent runs have too few frames there
(7-23) to score it. --label goes on the stats line (a user-desktop run: e.g. 'timing').

Times: perf s = frame time summed from the first perf.csv row (= wall time since the first swap). A frame's time is
its START (the previous row's swap), so a stall is placed where it begins. Signatures are draw_calls/vertices_processed.
Per run:
  front end  first 220/534 frame; EXIT = first 220/540 frame after it (the 60-frame fade); A0 = first 218/222 frame
             after the fade (the load before the attract). idle = EXIT - release of the last press. The game polls
             XInputGetState once per frame, so a press row's frame = input.csv pad_reads - offset (offset = final
             pad_reads - frame rows, else 4), and the release is the row time minus the press gap (default 0.6 s).
  H0         first frame of --anchor after A0 (the first heavy scene); if absent, the first frame after A0 with
             draws >= --heavy-draws (flag anchor_fallback)
  landmarks  starts of front end, fade, load, title, 625/780 (first 3D frame) and anchor runs after the front end:
             a second pass of the sequence shows up as repeats; H0 period = gap between anchor starts >= 30 s apart
  shots      runs of one exact signature with >= --shots-min frames, and stalls (frames >= --stall-ms), against A0
             and H0, with the pipeline/texture cache misses (per-frame counters) of the run or frame
  steady     the longest stretches after H0 with no frame >= --steady-ms and no pipeline miss (median draws shown)
  window     start = H0 + --offset s (first frame starting at or after it), length = shortest run of rows whose frame
             times sum to >= --seconds (like bench/agent8/run/frame_summary.py --seconds); nearest-rank percentiles
             as in frame_summary.py (sorted[ceil(p*n)-1], median = p50). Excluding flags: no_front_end, no_exit,
             no_anchor, short_window, few_rows (< --min-rows), light_window (median draws < --heavy-draws),
             stall_in_window (a frame >= --window-stall-ms: a compile stall slid in, or a hitch),
             window_reaches_heavy (a frame with >= --peak-draws draws: the heavy segment slid in),
             window_before_floor (start < --floor s after the first frame).
             Info: anchor_fallback, pipeline_misses_in_window, texture_misses_in_window, content_may_lag (window
             median > 100 ms: slow frames delayed the 12.4k shot by 0.9 s in one run, so a slow run's window may
             hold less of the sequence).
  sub        --sub OFFSET:SECONDS (default 18.2:2.3; 'none' turns it off): the same stats for a second stretch, info
             only, never a flag; 'contaminated' if it holds a frame >= --stall-ms or >= 12000 draws (the 12.4k shot).
With several runs: a cross-run table of shot starts against H0 (same order and timing?).
Exit code: 0 every run has a valid window, 1 otherwise, 2 bad arguments or no perf.csv.
"""
import argparse
import csv
import json
import os
import sys

FRONT, FADE, LOAD, TITLE, FIRST3D = (220, 534), (220, 540), (218, 222), (226, 1022), (625, 780)


def sig_arg(s):
    d, v = s.split('/')
    return int(d), int(v)


def sub_arg(s):
    if s.strip().lower() in ('', 'none', 'off'):
        return None
    o, d = s.split(':')
    return float(o), float(d)


def fmt(sig):
    return '%d/%d' % sig


def load_perf(path):
    with open(path, 'rb') as f:
        data = f.read()
    nl = data.find(b'\n')
    if nl < 0:
        return None
    hdr = data[:nl].decode('ascii', 'replace').strip().split(',')
    idx = {h: i for i, h in enumerate(hdr)}
    names = ['frame_time_us', 'draw_calls', 'vertices_processed', 'pipeline_cache_misses', 'texture_cache_misses']
    if any(n not in idx for n in names):
        return None
    cols = {n: [] for n in names}
    pos = nl + 1
    while True:
        e = data.find(b'\n', pos)
        if e < 0:
            break
        parts = data[pos:e].rstrip(b'\r').split(b',')
        pos = e + 1
        if len(parts) != len(hdr):
            continue
        try:
            vals = [int(p) for p in parts]
        except ValueError:
            continue
        for n in names:
            cols[n].append(vals[idx[n]])
    return cols


def nearest_rank(s, num, den):
    n = len(s)
    k = -(-num * n // den)
    return s[max(1, min(n, k)) - 1]


def frame_stats(fts_us):
    fts = [v for v in fts_us if v > 0]
    if not fts:
        return dict(frames=0)
    s = sorted(fts)
    tot = sum(fts)
    r = lambda v: round(v / 1000.0, 3)
    return dict(frames=len(fts), window_s=round(tot / 1e6, 3), mean_fps=round(len(fts) * 1e6 / tot, 2),
                mean_ms=round(tot / len(fts) / 1000.0, 3), median_ms=r(nearest_rank(s, 1, 2)),
                p95_ms=r(nearest_rank(s, 95, 100)), p99_ms=r(nearest_rank(s, 99, 100)),
                p99_9_ms=r(nearest_rank(s, 999, 1000)), min_ms=r(s[0]), max_ms=r(s[-1]),
                over_33ms=sum(1 for v in fts if v > 33000), over_100ms=sum(1 for v in fts if v > 100000))


def median(xs):
    s = sorted(xs)
    return s[(len(s) - 1) // 2] if s else None


def find(sigs, want, start=0, end=None):
    end = len(sigs) if end is None else end
    for i in range(max(0, start), end):
        if sigs[i] == want:
            return i
    return None


def run_starts(sigs, want, start):
    """First frame of every run of signature `want` from `start` on."""
    out = []
    for i in range(max(0, start), len(sigs)):
        if sigs[i] == want and (i == 0 or sigs[i - 1] != want):
            out.append(i)
    return out


def analyse(rd, a):
    rep = dict(run=os.path.abspath(rd), name=os.path.basename(os.path.normpath(rd)), flags_excluding=[], flags_info=[])
    perf = load_perf(os.path.join(rd, 'perf.csv')) if os.path.isfile(os.path.join(rd, 'perf.csv')) else None
    if not perf or not perf['frame_time_us']:
        rep['error'] = 'no perf.csv frame rows'
        rep['flags_excluding'].append('no_perf')
        return rep, None
    ft, dc, vx = perf['frame_time_us'], perf['draw_calls'], perf['vertices_processed']
    pm, tm = perf['pipeline_cache_misses'], perf['texture_cache_misses']
    n = len(ft)
    sigs = list(zip(dc, vx))
    swap = []
    acc = 0
    for v in ft:
        acc += v
        swap.append(acc / 1e6)
    st = lambda k: swap[k - 1] if k > 0 else 0.0          # start time of frame k (perf s)
    rep['frame_rows'] = n
    rep['perf_s'] = round(swap[-1], 2)
    info = {}
    try:
        with open(os.path.join(rd, 'run.json'), encoding='utf-8-sig') as f:
            info = json.load(f)
    except (OSError, ValueError):
        pass
    rep['bin'] = info.get('bin_dir')
    ins = info.get('input_script') or {}
    rep['script'] = ins.get('script')
    rep['script_sha256'] = ins.get('script_sha256')

    i534 = find(sigs, FRONT)
    if i534 is None:
        rep['flags_excluding'].append('no_front_end')
        return rep, (sigs, st, ft, pm, tm)
    rep['front_end_perf_s'] = round(st(i534), 2)
    iexit = find(sigs, FADE, i534)
    ia0 = find(sigs, LOAD, iexit) if iexit is not None else None

    # idle delay: release of the last press -> EXIT
    rows = []
    try:
        with open(os.path.join(rd, 'input.csv'), newline='', encoding='utf-8-sig') as f:
            rows = list(csv.DictReader(f))
    except OSError:
        pass
    last = None
    for r in rows:
        if r.get('cmd') in ('press', 'hold', 'stick', 'trigger'):
            last = r
    if last is not None:
        reads_end = ins.get('pad_reads')
        off = int(reads_end) - n if isinstance(reads_end, int) else None
        off = off if off is not None and 0 <= off <= 20 else 4
        frame = int(last['pad_reads']) - off
        gap = 0.0
        if last['cmd'] == 'press':
            parts = (last.get('args') or '').split()
            gap = (int(parts[3]) if len(parts) > 3 else 600) / 1000.0
        rel = st(max(0, min(n - 1, frame))) - gap
        rep['last_input'] = dict(line=int(last['line']), cmd=last['cmd'], args=last['args'], t_s=float(last['t_s']),
                                 pad_offset=off, release_perf_s=round(rel, 2))
        end_t = st(iexit) if iexit is not None else swap[-1]
        rep['idle_s'] = round(end_t - rel, 2)
        rep['idle_frames'] = (iexit if iexit is not None else n) - max(0, min(n - 1, frame))
    if iexit is None:
        rep['flags_excluding'].append('no_exit')
        rep['screen_s'] = round(swap[-1] - st(i534), 2)
        return rep, (sigs, st, ft, pm, tm)
    rep['exit_perf_s'] = round(st(iexit), 2)
    rep['screen_s'] = round(st(iexit) - st(i534), 2)
    if ia0 is None:
        rep['flags_excluding'].append('no_anchor')
        return rep, (sigs, st, ft, pm, tm)
    t0 = st(ia0)
    rep['a0_perf_s'] = round(t0, 2)

    h0 = find(sigs, a.anchor, ia0)
    if h0 is None:
        h0 = next((i for i in range(ia0, n) if dc[i] >= a.heavy_draws), None)
        if h0 is not None:
            rep['flags_info'].append('anchor_fallback')
    if h0 is not None:
        th = st(h0)
        rep['h0'] = dict(sig=fmt(sigs[h0]), perf_s=round(th, 2), after_a0_s=round(th - t0, 2), after_exit_s=round(th - st(iexit), 2))
    else:
        th = None
        rep['flags_excluding'].append('no_anchor')

    # landmarks after the front end (a loop shows up as repeats)
    marks = []
    for sig, label in ((FRONT, 'front end'), (FADE, 'fade'), (LOAD, 'load'), (TITLE, 'title'), (FIRST3D, 'first 3D frame'),
                       (a.anchor, 'anchor')):
        last_t = -1e9
        for i in run_starts(sigs, sig, i534):
            if st(i) - last_t >= 5.0:
                marks.append((st(i), fmt(sig), label))
            last_t = st(i)
    big = [i for i in range(ia0, n) if dc[i] >= 12000]
    last_t = -1e9
    for i in big:
        if st(i) - last_t >= 30.0:
            marks.append((st(i), fmt(sigs[i]), '>= 12000 draws'))
        last_t = st(i)
    marks.sort()
    rep['landmarks'] = [dict(perf_s=round(t, 2), sig=s, what=w, after_a0_s=round(t - t0, 2)) for t, s, w in marks]
    hs = [t for t, s, w in marks if w == 'anchor']
    rep['anchor_passes'] = len(hs)
    rep['anchor_period_s'] = [round(hs[k + 1] - hs[k], 2) for k in range(len(hs) - 1) if hs[k + 1] - hs[k] >= 30.0]

    # shots and stalls after A0
    shots = []
    i = ia0
    while i < n:
        j = i
        while j + 1 < n and sigs[j + 1] == sigs[i]:
            j += 1
        if j - i + 1 >= a.shots_min:
            shots.append(dict(sig=fmt(sigs[i]), after_a0_s=round(st(i) - t0, 2),
                              after_h0_s=round(st(i) - th, 2) if th is not None else None,
                              dur_s=round(swap[j] - st(i), 2), frames=j - i + 1,
                              median_ms=round(median(ft[i:j + 1]) / 1000.0, 1), max_ms=round(max(ft[i:j + 1]) / 1000.0, 1),
                              pm=sum(pm[i:j + 1]), tm=sum(tm[i:j + 1])))
        i = j + 1
    rep['shots'] = shots
    rep['stalls'] = [dict(after_a0_s=round(st(k) - t0, 2), after_h0_s=round(st(k) - th, 2) if th is not None else None,
                          ms=round(ft[k] / 1000.0, 1), sig=fmt(sigs[k]), prev=fmt(sigs[k - 1]), pm=pm[k], tm=tm[k])
                     for k in range(ia0, n) if ft[k] >= a.stall_ms * 1000]
    rep['pm_after_a0'] = sum(pm[ia0:])

    if th is None:
        return rep, (sigs, st, ft, pm, tm)
    # steady stretches after H0
    segs = []
    i = h0
    while i < n:
        if ft[i] >= a.steady_ms * 1000 or pm[i] > 0:
            i += 1
            continue
        j = i
        while j + 1 < n and ft[j + 1] < a.steady_ms * 1000 and pm[j + 1] == 0:
            j += 1
        segs.append((swap[j] - st(i), i, j))
        i = j + 1
    segs.sort(reverse=True)
    rep['steady'] = [dict(after_h0_s=round(st(i) - th, 2), dur_s=round(d, 2), frames=j - i + 1,
                          median_draws=median(dc[i:j + 1]), heavy_share=round(sum(1 for x in dc[i:j + 1] if x >= a.heavy_draws) / (j - i + 1), 2),
                          median_ms=round(median(ft[i:j + 1]) / 1000.0, 1), max_ms=round(max(ft[i:j + 1]) / 1000.0, 1))
                     for d, i, j in segs[:5]]

    # the scored window
    ts = th + a.offset
    k0 = next((k for k in range(h0, n) if st(k) >= ts - 1e-9), None)
    win = dict(anchor=fmt(a.anchor), offset_s=a.offset, seconds=a.seconds, first_row=k0)
    if k0 is None:
        rep['flags_excluding'].append('short_window')
        rep['window'] = win
        return rep, (sigs, st, ft, pm, tm)
    acc, k = 0, k0
    while k < n and acc < a.seconds * 1e6:
        acc += max(ft[k], 0)
        k += 1
    short = acc < a.seconds * 1e6
    w = range(k0, k)
    win.update(rows=len(w), start_perf_s=round(st(k0), 2), ff_to_window_s=round(st(k0), 2),
               end_perf_s=round(swap[k - 1], 2), short=short,
               median_draws=median([dc[x] for x in w]), median_vertices=median([vx[x] for x in w]),
               peak_draws=max([dc[x] for x in w] or [0]),
               heavy_share=round(sum(1 for x in w if dc[x] >= a.heavy_draws) / max(1, len(w)), 3),
               pm=sum(pm[x] for x in w), tm=sum(tm[x] for x in w),
               stalls=sum(1 for x in w if ft[x] >= a.window_stall_ms * 1000), stall_ms=a.window_stall_ms,
               first_sig=fmt(sigs[k0]), last_sig=fmt(sigs[k - 1]))
    win.update(frame_stats([ft[x] for x in w]))
    rep['window'] = win
    if short:
        rep['flags_excluding'].append('short_window')
    if len(w) < a.min_rows:
        rep['flags_excluding'].append('few_rows')
    if (win['median_draws'] or 0) < a.heavy_draws:
        rep['flags_excluding'].append('light_window')
    if win['stalls']:
        rep['flags_excluding'].append('stall_in_window')
    if st(k0) < a.floor - 0.5:
        rep['flags_excluding'].append('window_before_floor')
    if win['pm']:
        rep['flags_info'].append('pipeline_misses_in_window')
    if win['tm']:
        rep['flags_info'].append('texture_misses_in_window')
    if win['peak_draws'] >= a.peak_draws:
        rep['flags_excluding'].append('window_reaches_heavy')
    if (win.get('median_ms') or 0) > 100:
        rep['flags_info'].append('content_may_lag')
    if a.sub:
        so, ss = a.sub
        ks = next((k for k in range(h0, n) if st(k) >= th + so - 1e-9), None)
        sub = dict(offset_s=so, seconds=ss)
        if ks is not None:
            acc2, k2 = 0, ks
            while k2 < n and acc2 < ss * 1e6:
                acc2 += max(ft[k2], 0)
                k2 += 1
            ws = range(ks, k2)
            sub.update(rows=len(ws), start_perf_s=round(st(ks), 2), end_perf_s=round(swap[k2 - 1], 2),
                       short=acc2 < ss * 1e6, median_draws=median([dc[x] for x in ws]),
                       peak_draws=max([dc[x] for x in ws] or [0]), pm=sum(pm[x] for x in ws), tm=sum(tm[x] for x in ws),
                       contaminated=any(ft[x] >= a.stall_ms * 1000 or dc[x] >= 12000 for x in ws),
                       first_sig=fmt(sigs[ks]), last_sig=fmt(sigs[k2 - 1]))
            sub.update(frame_stats([ft[x] for x in ws]))
        rep['sub_window'] = sub
    return rep, (sigs, st, ft, pm, tm)


def text(rep, a):
    L = text_body(rep, a)
    if not rep.get('error'):
        L.append('  flags excluding: %s; info: %s; valid window: %s' % (
            ', '.join(rep['flags_excluding']) or 'none', ', '.join(rep['flags_info']) or 'none', not rep['flags_excluding']))
    return L


def text_body(rep, a):
    L = ['== %s  (%s rows, %s perf s; bin %s)' % (rep['name'], rep.get('frame_rows'), rep.get('perf_s'), rep.get('bin'))]
    if rep.get('error'):
        return L + ['  ' + rep['error']]
    if 'front_end_perf_s' not in rep:
        return L + ['  front end (220/534) not reached']
    li = rep.get('last_input')
    L.append('  front end 220/534 at perf %.2f; last input L%s %s %s, released at perf %s; ' % (
        rep['front_end_perf_s'], li and li['line'], li and li['cmd'], li and li['args'], li and li['release_perf_s'])
        + ('EXIT (220/540) at perf %.2f: idle %.2f s / %d frames after the release, %.2f s on the screen'
           % (rep['exit_perf_s'], rep['idle_s'], rep['idle_frames'], rep['screen_s']) if 'exit_perf_s' in rep
           else 'NO EXIT: %s s idle to the end, %.2f s on the screen' % (rep.get('idle_s'), rep['screen_s'])))
    if 'a0_perf_s' not in rep:
        return L
    h = rep.get('h0')
    L.append('  A0 (218/222 load) at perf %.2f; H0 %s' % (rep['a0_perf_s'], 'none' if not h else
             '%s at perf %.2f = A0 + %.2f s = EXIT + %.2f s' % (h['sig'], h['perf_s'], h['after_a0_s'], h['after_exit_s'])))
    L.append('  landmarks (perf s / after A0): ' + '; '.join('%.1f/%+.1f %s %s' % (m['perf_s'], m['after_a0_s'], m['what'], m['sig'])
                                                            for m in rep['landmarks']))
    L.append('  anchor passes %d; period %s' % (rep['anchor_passes'], rep['anchor_period_s'] or '-'))
    L.append('  shots (>= %d frames of one signature; s after A0 / after H0, duration, frames, median/max ms, pipeline/texture misses):' % a.shots_min)
    for s in rep['shots']:
        L.append('    %+8.2f %+8.2f  %6.2f s %5d  %-14s %6.1f %7.1f ms  pm %3d tm %3d' % (
            s['after_a0_s'], s['after_h0_s'] if s['after_h0_s'] is not None else float('nan'), s['dur_s'], s['frames'],
            s['sig'], s['median_ms'], s['max_ms'], s['pm'], s['tm']))
    L.append('  stalls (frames >= %d ms; s after A0 / after H0; the frame before):' % a.stall_ms)
    for s in rep['stalls']:
        L.append('    %+8.2f %+8.2f  %7.1f ms  %-14s pm %3d tm %3d  (prev %s)' % (
            s['after_a0_s'], s['after_h0_s'] if s['after_h0_s'] is not None else float('nan'), s['ms'], s['sig'], s['pm'], s['tm'], s['prev']))
    if 'steady' in rep:
        L.append('  steady stretches after H0 (no frame >= %d ms, no pipeline miss), longest first:' % a.steady_ms)
        for s in rep['steady']:
            L.append('    H0 %+7.2f s for %6.2f s, %5d frames, median draws %5s, heavy share %.2f, median %.1f ms, max %.1f ms' % (
                s['after_h0_s'], s['dur_s'], s['frames'], s['median_draws'], s['heavy_share'], s['median_ms'], s['max_ms']))
    w = rep.get('window')
    if w and w.get('rows'):
        L.append('  window H0 %+.1f s for %.1f s: rows %d (perf %.2f-%.2f, %s -> %s), median draws %s, peak %s, heavy share %.2f, pm %d, tm %d, frames >= %d ms: %d'
                 % (w['offset_s'], w['seconds'], w['rows'], w['start_perf_s'], w['end_perf_s'], w['first_sig'], w['last_sig'],
                    w['median_draws'], w['peak_draws'], w['heavy_share'], w['pm'], w['tm'], w['stall_ms'], w['stalls']))
        if w.get('frames'):
            L.append('    frames %d over %.2f s = %.2f fps; ms median %.2f p95 %.2f p99 %.2f max %.2f; >33 ms %d, >100 ms %d (%s)'
                     % (w['frames'], w['window_s'], w['mean_fps'], w['median_ms'], w['p95_ms'], w['p99_ms'], w['max_ms'], w['over_33ms'], w['over_100ms'], a.label))
    sw = rep.get('sub_window')
    if sw and sw.get('rows'):
        L.append('  sub-window H0 %+.1f s for %.1f s (info only): rows %d (perf %.2f-%.2f, %s -> %s), median draws %s, peak %s, pm %d, tm %d%s%s'
                 % (sw['offset_s'], sw['seconds'], sw['rows'], sw['start_perf_s'], sw['end_perf_s'], sw['first_sig'], sw['last_sig'],
                    sw['median_draws'], sw['peak_draws'], sw['pm'], sw['tm'], '; SHORT' if sw['short'] else '',
                    '; CONTAMINATED' if sw['contaminated'] else ''))
        if sw.get('frames'):
            L.append('    frames %d over %.2f s = %.2f fps; ms median %.2f p95 %.2f max %.2f (%s)'
                     % (sw['frames'], sw['window_s'], sw['mean_fps'], sw['median_ms'], sw['p95_ms'], sw['max_ms'], a.label))
    return L


def cross(reps):
    have = [r for r in reps if r.get('h0') and r.get('shots')]
    if len(have) < 2:
        return []
    L = ['== cross-run: shot starts against H0 (s; first run of each signature; delta = run - %s)' % have[0]['name']]
    firsts = []
    for r in have:
        d = {}
        for s in r['shots']:
            d.setdefault(s['sig'], s['after_h0_s'])
        firsts.append(d)
    order = sorted(firsts[0], key=lambda s: firsts[0][s])
    labels = [r['name'][16:] if len(r['name']) > 16 and r['name'][8] == '-' and r['name'][15] == '-' else r['name'] for r in have]
    wd = max([22] + [len(x) + 2 for x in labels])
    L.append('  %-14s' % 'signature' + ''.join(x.rjust(wd) for x in labels))
    for s in order:
        cells = []
        for d in firsts:
            if s in d:
                cells.append('%+9.2f (%+6.2f)' % (d[s], d[s] - firsts[0][s]))
            else:
                cells.append('-')
        L.append('  %-14s' % s + ''.join(c.rjust(wd) for c in cells))
    return L


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('runs', nargs='+')
    ap.add_argument('--anchor', type=sig_arg, default=(2823, 366575))
    ap.add_argument('--offset', type=float, default=6.5)
    ap.add_argument('--seconds', type=float, default=11.0)
    ap.add_argument('--min-rows', type=int, default=110)
    ap.add_argument('--peak-draws', type=int, default=9800)
    ap.add_argument('--window-stall-ms', type=int, default=250)
    ap.add_argument('--sub', type=sub_arg, default=(18.2, 2.3))
    ap.add_argument('--label', default='FUNCTIONAL ONLY')
    ap.add_argument('--heavy-draws', type=int, default=2000)
    ap.add_argument('--stall-ms', type=int, default=1000)
    ap.add_argument('--steady-ms', type=int, default=250)
    ap.add_argument('--shots-min', type=int, default=8)
    ap.add_argument('--floor', type=float, default=60.0)
    ap.add_argument('--json')
    ap.add_argument('--out')
    a = ap.parse_args()
    reps, lines = [], []
    for rd in a.runs:
        if not os.path.isdir(rd):
            print('no such run dir: %s' % rd, file=sys.stderr)
            return 2
        rep, _ = analyse(rd, a)
        reps.append(rep)
        lines += text(rep, a) + ['']
    lines += cross(reps)
    out = '\n'.join(lines)
    print(out)
    if a.out:
        with open(a.out, 'w', encoding='utf-8') as f:
            f.write(out + '\n')
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump(dict(args={k: (fmt(v) if k == 'anchor' else v) for k, v in vars(a).items() if k not in ('json', 'out', 'runs')},
                           runs=reps), f, indent=1)
    return 0 if all(not r['flags_excluding'] for r in reps) else 1


if __name__ == '__main__':
    sys.exit(main())

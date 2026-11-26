#!/usr/bin/env python3
"""s5_gates.py - per-run validity gates for S5 gameplay-route runs (M12, session 3, 2026-11-25).

Route: harness/routes/attract-long.txt (START, A, A, then ~380 s idle; the attract 3D plays by itself).
Window (M8 contract, 17:22): starts at the first frame with draws >= --anchor (1500) and lasts --span seconds.
  Default --anchor-mode sustained: the first frame that starts >= --anchor-hold (1.0 s) of frames all >= 1500 draws
  (offsf has transient single >=1500 frames inside the pre-3D phase); --anchor-mode first = the literal rule.
3D-reached check: any frame with draws >= --thr3d (600), else VOID.

Gates (each PASS / FLAG / VOID / NODATA; run verdict = VOID if any VOID, else FLAG if any FLAG/NODATA, else PASS):
  clean     exit 0, wm_close, no WER / dump / crash event
  cold      seed_xenos null (cold shader cache); VOID if seeded unless --warm
  3d        first >=thr3d frame exists; anchor (>=anchor draws) exists; anchor sustain; anchor-to-last-press time
  span      window covered (+ --margin s before the close); window must not run past the end of the attract 3D
            (low-band or flat-draws detector): past >= 5 s -> VOID, 0-5 s -> FLAG
  input     route presses all ok, none inside the window, script alive through the window end, no error/timeouts,
            pad dll loaded by the game pid
  cooldown  run.json cooldown record (tolerant parse); missing / timed out -> FLAG; start temps reported
  thermal   NVML throttle bits in the window: SwThermal|HwThermal share is a covariate (thermal_limited above
            --thermal-flag, verdict unchanged); set rule: |share - arm median| > --thermal-outlier -> FLAG;
            hardware brake (HwSlowdown|HwThermal|HwPowerBrake) share above --hw-void -> VOID
  host      sys.csv in the window: battery / saver / scheme or overlay change / screensaver / not foreground /
            user input / game dead -> VOID; hidden-desktop mode -> FLAG; nongame cores > set median + 1.0 -> FLAG;
            no sys.csv -> NODATA
  cap       effective cap (runner field, cvars, native frames.csv cvar) vs --cap; observed window fps
  align     time axis (first-frame t + cumulative frame times) vs elapsed_s and vs input.csv perf_rows

Time axis: t(row i end) = input.csv wait_first_frame t_s + sum(frame_time_us[0..i]) / 1e6 (seconds from launch).
gpu.csv t_s is taken as seconds from launch; sys.csv uses epoch_s - run.json started_epoch_s.
Draws: xenos = perf.csv draw_calls; native = frames.csv draw_calls (perf.csv has none), offset auto-fitted on
interval_ms vs frame_time (expected: frames row k <-> perf row k+1).

Usage:  python -B s5_gates.py RUN_DIR [RUN_DIR ...] [--span 120] [--cap 60|none|auto] [--json OUT] [--route FILE]
        python -B s5_gates.py --selftest
Stdlib only.
"""
import argparse, csv, json, math, os, re, statistics, sys, tempfile

THERMAL_BITS = 0x20 | 0x40          # SwThermalSlowdown | HwThermalSlowdown
HW_BRAKE_BITS = 0x8 | 0x40 | 0x80   # HwSlowdown | HwThermalSlowdown | HwPowerBrakeSlowdown
PCAP_BIT = 0x4                      # SwPowerCap
ORDER = {'PASS': 0, 'NODATA': 1, 'FLAG': 1, 'VOID': 2}


def fnum(s, d=None):
    try:
        v = float(s)
        return v if math.isfinite(v) else d
    except (TypeError, ValueError):
        return d


def rcsv(path):
    if not os.path.isfile(path):
        return None
    with open(path, newline='', encoding='utf-8-sig', errors='replace') as f:
        return list(csv.DictReader(f))


def rjson(path):
    if not os.path.isfile(path):
        return {}
    with open(path, encoding='utf-8-sig') as f:
        return json.load(f)


def find_key(obj, names):
    """First value whose key (case-insensitive) is in names, searched depth-first in dicts."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in names:
                return v
        for v in obj.values():
            r = find_key(v, names)
            if r is not None:
                return r
    return None


def p_nearest(sorted_vals, p):
    return sorted_vals[max(0, math.ceil(p * len(sorted_vals)) - 1)]


def frame_metrics(ft):
    """CF1 definitions: fps = frames / window s; p99 nearest rank; 1% low = mean of slowest max(1, n//100)."""
    n = len(ft)
    if not n:
        return {}
    s = sorted(ft)
    k = max(1, n // 100)
    tot = sum(ft) / 1000.0
    return {'frames': n, 'window_s': round(tot, 3), 'fps': round(n / tot, 3) if tot else None,
            'median_ms': round(statistics.median(ft), 3), 'p99_ms': round(p_nearest(s, 0.99), 3),
            'low1_ms': round(sum(s[-k:]) / k, 3), 'max_ms': round(s[-1], 3),
            'n_ge100': sum(1 for v in ft if v >= 100), 'n_ge250': sum(1 for v in ft if v >= 250),
            'at60_share': round(sum(1 for v in ft if 16.0 <= v <= 17.4) / n, 3)}


def gate(st, why, **kw):
    d = {'status': st, 'why': why}
    d.update(kw)
    return d


def native_offset(perf_ft, fr_rows):
    """Best offset o such that frames row k <-> perf row k+o, by median |interval_ms - frame_time|."""
    iv = [fnum(r.get('interval_ms'), 0.0) for r in fr_rows]
    best = None
    for o in (-1, 0, 1, 2, 3):
        diffs = []
        for k in range(0, min(len(iv), 20000)):
            j = k + o
            if 0 <= j < len(perf_ft):
                diffs.append(abs(iv[k] - perf_ft[j]))
        if diffs:
            m = statistics.median(diffs)
            if best is None or m < best[1]:
                best = (o, m)
    return best or (1, None)


def route_presses(route):
    if not route or not os.path.isfile(route):
        return None
    n = 0
    with open(route, encoding='utf-8-sig') as f:
        for line in f:
            t = line.split('#', 1)[0].split()
            if t and t[0].lower() == 'press':
                n += 1
    return n


def analyse(rd, a):
    run = rjson(os.path.join(rd, 'run.json'))
    perf = rcsv(os.path.join(rd, 'perf.csv')) or []
    # native frame metrics: run-timing.ps1 -Frames native writes native-frames.csv (rt L274), run-game.ps1 writes
    # frames.csv; try both (as score3d.py load_frames), first one with interval_ms + draw_calls wins
    frames, frames_name = None, None
    for nm in ('native-frames.csv', 'frames.csv'):
        fr = rcsv(os.path.join(rd, nm))
        if fr and 'interval_ms' in fr[0] and 'draw_calls' in fr[0]:
            frames, frames_name = fr, nm
            break
    gpu = rcsv(os.path.join(rd, 'gpu.csv'))
    inp = rcsv(os.path.join(rd, 'input.csv')) or []
    sysr = rcsv(os.path.join(rd, 'sys.csv'))
    out = {'run_dir': rd, 'tag': run.get('tag'), 'bin_dir': run.get('bin_dir'), 'gates': {}, 'info': {}}
    G, I = out['gates'], out['info']

    ft = [fnum(r.get('frame_time_us'), 0.0) / 1000.0 for r in perf]
    renderer = a.renderer
    pd = [int(fnum(r.get('draw_calls'), 0)) for r in perf]
    no_perf = not ft and bool(frames)
    if no_perf:  # no perf.csv rows: frame times from the native csv interval_ms (offset 0)
        ft = [fnum(r.get('interval_ms'), 0.0) for r in frames]
    if renderer == 'auto':
        renderer = 'native' if (frames is not None and not any(pd)) or 'native' in str(run.get('bin_dir', '')).lower() else 'xenos'
    out['renderer'] = renderer
    foff = 1
    if renderer == 'native' and frames:
        off, md = (0, 0.0) if no_perf else native_offset(ft, frames)
        foff = off
        fd = [int(fnum(r.get('draw_calls'), 0)) for r in frames]
        dr = [0] * len(ft)
        for k, d in enumerate(fd):
            j = k + off
            if 0 <= j < len(ft):
                dr[j] = d
        I['draws_source'] = '%s offset %+d (median |interval-frame_time| %s ms)%s' % (
            frames_name, off, None if md is None else round(md, 3), '; no perf.csv: frame times = interval_ms' if no_perf else '')
    else:
        dr = pd
        I['draws_source'] = 'perf.csv'

    # ---- time axis ----
    ff = None
    for r in inp:
        if r.get('cmd') == 'wait_first_frame':
            ff = fnum(r.get('t_s'))
            break
    I['first_frame_t'] = ff
    t0 = ff if ff is not None else 0.0
    tend, acc = [], t0
    for v in ft:
        acc += v / 1000.0
        tend.append(acc)
    last_t = tend[-1] if tend else None
    I['perf_rows'] = len(ft)
    I['perf_last_t'] = None if last_t is None else round(last_t, 2)

    # ---- clean ----
    why = []
    if run.get('exit_code') != 0:
        why.append('exit %s' % run.get('exit_code'))
    if run.get('close_method') != 'wm_close':
        why.append('close %s' % run.get('close_method'))
    if run.get('wer_seen'):
        why.append('WER')
    if run.get('dumps'):
        # run-timing lists every .dmp it collected in dumps; dumps of other processes / other pids are also listed in
        # foreign_crash_dumps (not a problem, rt L757-761): only the rest count
        foreign = {os.path.basename(str(x).replace('\\', '/')).lower() for x in (run.get('foreign_crash_dumps') or [])}
        own = [x for x in run['dumps'] if os.path.basename(str(x).replace('\\', '/')).lower() not in foreign]
        if own:
            why.append('dumps %d' % len(own))
    if run.get('crash_events'):
        why.append('crash events %d' % len(run['crash_events']))
    if run.get('exited_early'):
        why.append('exited early')
    pid = run.get('pid')
    dmps = [f for f in os.listdir(rd) if f.lower().endswith('.dmp')]
    own_dmp = [f for f in dmps if pid is not None and f.lower() == ('legodimensions.exe.%s.dmp' % pid).lower()]
    if own_dmp:
        why.append('own-pid dump in run dir: %s' % own_dmp[0])
    fdmp = [f for f in dmps if f not in own_dmp]
    G['clean'] = gate('VOID' if why else 'PASS', '; '.join(why) or 'exit 0, wm_close %.2f s, no WER/dump%s' % (
        run.get('close_seconds') or -1, '; info: foreign dump(s) %s' % ', '.join(fdmp) if fdmp else ''))

    # ---- runner verdict (run-timing.ps1 status / valid_timing / excluded; absent on run-game.ps1 runs) ----
    why = []
    rst = run.get('status')
    if rst is not None and rst != 'OK':
        why.append('runner status %s (%s)' % (rst, '; '.join(str(x) for x in (run.get('problems') or [])) or '-'))
    if run.get('valid_timing') is False:
        why.append('valid_timing false (%s)' % ('; '.join(str(x) for x in (run.get('valid_timing_why') or [])) or '-'))
    if run.get('excluded') is True:
        why.append('runner excluded (%s)' % (', '.join(str(x) for x in (run.get('flags_excluding') or [])) or '-'))
    if why:
        G['runner'] = gate('VOID', '; '.join(why))
    elif rst is None and 'valid_timing' not in run and 'excluded' not in run:
        G['runner'] = gate('PASS', 'n/a: no runner status fields (not a run-timing run)')
    else:
        G['runner'] = gate('PASS', 'status %s, valid_timing %s, excluded %s%s' % (
            rst, run.get('valid_timing'), run.get('excluded'),
            '; info flags: %s' % ', '.join(str(x) for x in run['flags_info']) if run.get('flags_info') else ''))

    # ---- cold ----
    seed = run.get('seed_xenos')
    if seed in (None, '', False):
        G['cold'] = gate('PASS', 'seed_xenos null (cold)')
    else:
        G['cold'] = gate('PASS' if a.warm else 'VOID', 'seeded: %s' % (seed,))

    # ---- 3D / anchor ----
    i3d = next((i for i, d in enumerate(dr) if d >= a.thr3d), None)
    ia_first = next((i for i, d in enumerate(dr) if d >= a.anchor), None)
    # sustained anchor: first frame that starts a stretch of >= anchor_hold s with every frame >= anchor draws
    # (offsf: single >=1500 frames at 108-111 s inside the 790-draw pre-3D phase; full 3D from 128 s)
    ia_sus, rs = None, None
    for i, d in enumerate(dr):
        if d >= a.anchor:
            if rs is None:
                rs = i
            if tend[i] - (tend[rs] - ft[rs] / 1000.0) >= a.anchor_hold:
                ia_sus = rs
                break
        else:
            rs = None
    ia = ia_sus if a.anchor_mode == 'sustained' else ia_first
    t_first = None if ia_first is None else tend[ia_first] - ft[ia_first] / 1000.0
    t_sus = None if ia_sus is None else tend[ia_sus] - ft[ia_sus] / 1000.0
    I['anchor_first_t'] = None if t_first is None else round(t_first, 2)
    I['anchor_sustained_t'] = None if t_sus is None else round(t_sus, 2)
    rwin = find_key(run, {'window_start_s', 'score_start_s', 'scoring_start_s', 'window_t0_s', 'window_start_t'})
    I['runner_window_start'] = rwin
    presses = [r for r in inp if r.get('cmd') == 'press']
    last_press = max((fnum(r.get('t_s'), 0.0) for r in presses), default=None)
    alt = {}
    for th in (600, 1000, 1500, 2000):
        j = next((i for i, d in enumerate(dr) if d >= th), None)
        alt[str(th)] = None if j is None else round(tend[j] - ft[j] / 1000.0, 2)
    I['first_t_by_draws'] = alt
    I['max_draws'] = max(dr) if dr else 0
    T0 = T1 = None
    if i3d is None or ia is None:
        G['3d'] = gate('VOID', 'no frame >= %d draws' % a.thr3d if i3d is None else
                       'no %s anchor (>= %d draws%s)' % (a.anchor_mode, a.anchor, ' for %.1f s' % a.anchor_hold if a.anchor_mode == 'sustained' else ''),
                       t3d=None, anchor_t=None)
    else:
        t3d = tend[i3d] - ft[i3d] / 1000.0
        T0 = tend[ia] - ft[ia] / 1000.0
        T1 = T0 + a.span
        win10 = [dr[i] for i in range(ia, len(dr)) if tend[i] <= T0 + 10.0]
        sustain = sum(1 for d in win10 if d >= a.thr3d) / len(win10) if win10 else 0.0
        since = None if last_press is None else T0 - last_press
        st, w = 'PASS', []
        if sustain < a.sustain_min:
            st = 'FLAG'; w.append('anchor sustain %.2f < %.2f (frames >= %d in first 10 s)' % (sustain, a.sustain_min, a.thr3d))
        if since is not None and since > a.anchor_late:
            st = 'FLAG'; w.append('anchor %.1f s after last press > %.0f' % (since, a.anchor_late))
        if t_first is not None and t_sus is not None and abs(t_sus - t_first) > 2.0:
            w.append('info: first >=%d frame at %.1f s is transient; sustained anchor %.1f s (%s used)' % (
                a.anchor, t_first, t_sus, a.anchor_mode))
        rw = fnum(rwin)
        if rw is not None and abs(rw - T0) > 1.0:
            st = 'FLAG'; w.append('runner window start %.2f s != gate anchor %.2f s' % (rw, T0))
        G['3d'] = gate(st, '; '.join(w) or 'ok', t3d=round(t3d, 2), anchor_t=round(T0, 2),
                       anchor_minus_last_press=None if since is None else round(since, 2),
                       anchor_minus_3d=round(T0 - t3d, 2), sustain10=round(sustain, 3))

    # ---- span + end of attract 3D ----
    wi = []
    if T0 is not None:
        wi = [i for i in range(ia, len(ft)) if tend[i] <= T1 + 1e-9]
        need = T1 + a.margin
        # end of attract 3D, two detectors, the earlier one wins:
        #  (1) low band: first stretch >= end_low_hold s after the anchor with every frame below the renderer's
        #      low-band draw count (xenos 1000: post-attract 680-950 then flat 766 in offsf, 3D never < 1000 for 5 s;
        #      native 120: native 3D scenes run at 155-700 draws, front end 2-60);
        #  (2) flat: first stretch >= end_hold s where max - min <= max(end_abs, end_rel * min) (static screen;
        #      attract scenes change every <= ~12 s).
        low = a.end_low_native if renderer == 'native' else a.end_low_xenos
        e_low, rs = None, None
        for i in range(ia, len(dr)):
            if dr[i] < low:
                if rs is None:
                    rs = i
                if tend[i] - (tend[rs] - ft[rs] / 1000.0) >= a.end_low_hold:
                    e_low = tend[rs] - ft[rs] / 1000.0
                    break
            else:
                rs = None
        e_flat, s0, lo, hi = None, ia, None, None
        for i in range(ia, len(dr)):
            d = dr[i]
            lo = d if lo is None else min(lo, d)
            hi = d if hi is None else max(hi, d)
            while hi - lo > max(a.end_abs, a.end_rel * lo) and s0 < i:
                s0 += 1
                seg = dr[s0:i + 1]
                lo, hi = min(seg), max(seg)
            if tend[i] - (tend[s0] - ft[s0] / 1000.0) >= a.end_hold:
                e_flat = tend[s0] - ft[s0] / 1000.0
                break
        cands = [e for e in (e_low, e_flat) if e is not None]
        end3d = min(cands) if cands else None
        ends = {'end3d_t': None if end3d is None else round(end3d, 2),
                'end3d_low_t': None if e_low is None else round(e_low, 2),
                'end3d_flat_t': None if e_flat is None else round(e_flat, 2),
                'window': [round(T0, 2), round(T1, 2)], 'span_s': a.span}
        if last_t is None or last_t < need:
            G['span'] = gate('VOID', 'SHORT: perf ends %.1f s < window end %.1f + margin %.0f (need -Seconds >= ~%.0f)'
                             % (last_t or 0, T1, a.margin, math.ceil(need + 1)), **ends)
        else:
            past = 0.0 if end3d is None else max(0.0, T1 - end3d)
            st = 'VOID' if past >= 5.0 else ('FLAG' if past > 0 else 'PASS')
            G['span'] = gate(st, ('window runs %.1f s past end of 3D at %.1f s' % (past, end3d)) if past > 0 else
                             'covered: %.1f s of frames after window end; end of 3D %s' % (
                                 last_t - T1, 'not seen' if end3d is None else 'at %.1f s (%.1f s after window)' % (end3d, end3d - T1)),
                             **ends)
    else:
        G['span'] = gate('VOID', 'no anchor, no window')

    # ---- input ----
    isc = run.get('input_script') or {}
    why_v, why_f = [], []
    if not isc:
        why_v.append('no input_script record')
    else:
        if isc.get('error'):
            why_v.append('error %s' % isc.get('error'))
        if isc.get('timeouts'):
            why_v.append('timeouts %s' % isc.get('timeouts'))
        if isc.get('dll_loaded_by_pid') != run.get('pid'):
            why_v.append('pad dll pid %s != game pid %s' % (isc.get('dll_loaded_by_pid'), run.get('pid')))
    bad = [r for r in presses if not str(r.get('result', '')).lower().startswith('ok')]
    if bad:
        why_v.append('%d press(es) not ok' % len(bad))
    exp = route_presses(a.route) if a.route else None
    if exp is None:
        exp = a.presses
    if len(presses) != exp:
        why_v.append('presses %d != route %d' % (len(presses), exp))
    in_win = [r for r in presses if T0 is not None and T0 <= fnum(r.get('t_s'), -1) <= T1]
    if in_win:
        why_v.append('%d press(es) inside the window' % len(in_win))
    # script steps only: vpadhost writes an 'end' row at Finish() after the close (and an 'error' row on a script
    # error), which would always satisfy the alive check
    last_in = max((fnum(r.get('t_s'), 0.0) for r in inp if str(r.get('cmd', '')).lower() not in ('end', 'error')), default=None)
    done = isc.get('steps_done'); total = isc.get('steps_total')
    completed = (done is not None and done == total) or isc.get('stopped_by_script') or isc.get('last_step') == 'stop'
    alive = completed or (T1 is not None and last_in is not None and last_in >= T1 - a.step_gap)
    if T1 is not None and not alive:
        why_v.append('script last step %.1f s < window end %.1f - %.0f' % (last_in or -1, T1, a.step_gap))
    phys = find_key(run, {'input_during_window', 'user_input_in_window'})
    if phys:
        why_v.append('user input during window (runner field)')
    G['input'] = gate('VOID' if why_v else ('FLAG' if why_f else 'PASS'), '; '.join(why_v + why_f) or
                      'presses %d ok, none in window; steps %s/%s (%s), last step t %.1f' % (
                          len(presses), done, total, 'completed' if completed else isc.get('last_step'), last_in or -1),
                      last_press_t=last_press, steps_done=done, steps_total=total)

    # ---- cooldown ----
    cd = find_key(run, {'cooldown', 'gpu_cooldown', 'cooldown_record'})
    g_t = [(fnum(r.get('t_s')), fnum(r.get('temp_c'))) for r in (gpu or [])]
    g_t = [(t, c) for t, c in g_t if t is not None and c is not None]
    start_c = g_t[0][1] if g_t else None
    at_anchor = next((c for t, c in g_t if T0 is not None and t >= T0), None)
    if isinstance(cd, dict):
        met = find_key(cd, {'met', 'ok', 'reached'})
        to = find_key(cd, {'timed_out', 'timeout_hit', 'timedout'})
        if to:
            G['cooldown'] = gate('FLAG', 'cooldown timed out', record=cd, start_temp_c=start_c, temp_at_anchor_c=at_anchor)
        elif met is False:
            G['cooldown'] = gate('FLAG', 'cooldown not met', record=cd, start_temp_c=start_c, temp_at_anchor_c=at_anchor)
        elif met:
            G['cooldown'] = gate('PASS', 'cooldown met', record=cd, start_temp_c=start_c, temp_at_anchor_c=at_anchor)
        else:
            G['cooldown'] = gate('FLAG', 'cooldown record without met/timed_out', record=cd, start_temp_c=start_c,
                                 temp_at_anchor_c=at_anchor)
    else:
        G['cooldown'] = gate('FLAG', 'no cooldown record in run.json (first gpu.csv temp %s C)' % start_c,
                             start_temp_c=start_c, temp_at_anchor_c=at_anchor)

    # ---- thermal + GPU covariates ----
    if gpu is None:
        G['thermal'] = gate('NODATA', 'no gpu.csv')
    elif T0 is None:
        G['thermal'] = gate('NODATA', 'no window')
    else:
        rows = [r for r in gpu if fnum(r.get('t_s')) is not None and T0 <= fnum(r['t_s']) <= T1]
        def thr(r):
            try:
                return int(str(r.get('throttle', '0')), 16)
            except ValueError:
                return 0
        n = len(rows)
        if not n:
            G['thermal'] = gate('NODATA', 'no gpu.csv samples in window')
        else:
            th = sum(1 for r in rows if thr(r) & THERMAL_BITS) / n
            hw = sum(1 for r in rows if thr(r) & HW_BRAKE_BITS) / n
            pc = sum(1 for r in rows if thr(r) & PCAP_BIT) / n
            def med(k):  # median of the 1 Hz samples in the window (READOUT-PLAN-P03 section 3)
                v = [fnum(r.get(k)) for r in rows]
                v = [x for x in v if x is not None]
                return round(statistics.median(v), 2) if v else None
            cov = {'samples': n, 'expected': round(a.span), 'thermal_share': round(th, 3), 'hw_brake_share': round(hw, 3),
                   'powercap_share': round(pc, 3), 'util_gpu': med('util_gpu'), 'gr_mhz': med('gr_mhz'),
                   'power_w': med('power_w'), 'temp_c': med('temp_c'),
                   'p0_share': round(sum(1 for r in rows if r.get('pstate') == 'P0') / n, 3)}
            st, w = 'PASS', []
            if hw > a.hw_void:
                st = 'VOID'; w.append('hardware brake share %.2f > %.2f' % (hw, a.hw_void))
            if th > a.thermal_flag:
                w.append('thermal-limited %.2f > %.2f (covariate; set rule: arm outlier -> FLAG)' % (th, a.thermal_flag))
                cov['thermal_limited'] = True
            if n < 0.8 * a.span:
                st = max(st, 'FLAG', key=ORDER.get); w.append('gpu samples %d < 80%% of %.0f' % (n, a.span))
            G['thermal'] = gate(st, '; '.join(w) or 'thermal %.2f, hw %.2f' % (th, hw), **cov)

    # ---- host ----
    if sysr is None:
        G['host'] = gate('NODATA', 'no sys.csv (host-busy, battery, foreground, user input unknown)', nongame_mean=None)
    elif T0 is None:
        G['host'] = gate('NODATA', 'no window', nongame_mean=None)
    else:
        se = fnum(run.get('started_epoch_s'))
        def st_t(r):
            e = fnum(r.get('epoch_s'))
            return e - se if (e is not None and se is not None) else fnum(r.get('t_s'))
        rows = [r for r in sysr if st_t(r) is not None and T0 <= st_t(r) <= T1]
        why = []
        if not rows:
            G['host'] = gate('NODATA', 'no sys.csv rows in window', nongame_mean=None)
        else:
            if any(r.get('ac') == '0' for r in rows): why.append('on battery')
            if any(r.get('batt_saver') == '1' for r in rows): why.append('battery saver')
            if len({r.get('scheme') for r in rows}) > 1: why.append('power scheme change')
            if len({r.get('overlay') for r in rows}) > 1: why.append('power overlay change')
            if any(r.get('screensaver') == '1' for r in rows): why.append('screensaver')
            hidden = 'hidden desktop' in str(run.get('mode', '')).lower() or run.get('on_timing_desktop') is False
            fg0 = sum(1 for r in rows if r.get('fg_game') == '0')
            if fg0 and not hidden: why.append('game not foreground in %d/%d rows' % (fg0, len(rows)))
            if any(r.get('game_alive') == '0' for r in rows): why.append('game not alive')
            idle = [fnum(r.get('idle_s')) for r in rows]
            if any(b is not None and p is not None and b < p - 0.5 for p, b in zip(idle, idle[1:])):
                why.append('user input (idle_s reset)')
            ng = [fnum(r.get('nongame_cores')) for r in rows]
            ng = [x for x in ng if x is not None]
            m = round(sum(ng) / len(ng), 3) if ng else None
            G['host'] = gate('VOID' if why else ('PASS' if m is not None else 'NODATA'),
                             '; '.join(why) or ('nongame %.3f cores (set rule applied below)' % m if m is not None else 'no nongame_cores'),
                             nongame_mean=m, rows=len(rows))
            if hidden and G['host']['status'] == 'PASS':
                G['host']['status'] = 'FLAG'
                G['host']['why'] = 'hidden-desktop run (mode %r): foreground check not applicable; ' % run.get('mode') + G['host']['why']

    # ---- frame metrics + cap ----
    wft = [ft[i] for i in wi]
    met = frame_metrics(wft)
    out['metrics'] = met
    eff = find_key(run, {'effective_cap', 'fps_cap_effective', 'cap_effective', 'effective_fps_cap'})
    cv = run.get('cvars') or {}
    ck = ('native_fps_limit', 'framerate_limit') if renderer == 'native' else ('framerate_limit', 'native_fps_limit')
    cvcap = cv.get(ck[0], cv.get(ck[1])) if isinstance(cv, dict) else None
    ncap = None
    if renderer == 'native' and frames and wi:
        vals = {frames[k].get('native_fps_limit_cvar') for k in range(len(frames)) if wi[0] <= k + foff <= wi[-1]}
        ncap = ','.join(sorted(v for v in vals if v))
    I['cap_sources'] = {'runner_effective': eff, 'cvar': cvcap, 'native_frames_cvar': ncap}
    want = a.cap
    if not met or met.get('fps') is None:
        G['cap'] = gate('NODATA', 'no window frames' if not met else
                        'window frame-time sum 0 (%d frames): no fps' % met['frames'], arm=None if want == 'auto' else want)
    else:
        fps = met['fps']; w = []; st = 'PASS'
        reported = eff if eff is not None else cvcap
        if reported is None and ncap and ',' not in ncap:
            reported = ncap
        if want == 'auto':
            # 60 -> cap60 arm; anything else (none, 0, 240 native default) -> uncapped arm, where a
            # non-zero cap VOIDs unless --native-default-ok accepts the native default
            want = '60' if fnum(reported) is not None and abs(fnum(reported) - 60) <= 0.5 else 'none'
        rep_n = fnum(reported)
        if want == '60':
            if rep_n is not None and abs(rep_n - 60) > 0.5:
                st = 'VOID'; w.append('reported cap %s != 60' % reported)
            elif reported is None:
                st = 'FLAG'; w.append('no reported cap')
            if fps > a.cap_hi:
                st = 'VOID'; w.append('fps %.2f > %.1f: cap not applied' % (fps, a.cap_hi))
            elif fps >= a.cap_lo:
                w.append('at cap (fps %.2f)' % fps)
            else:
                w.append('below cap: GPU-bound info (fps %.2f, at60 share %.2f)' % (fps, met['at60_share']))
        else:
            # numeric compare: runner effective_cap is an int, the frames cvar a string
            native_default = renderer == 'native' and a.native_default_ok and rep_n is not None and abs(rep_n - 240) <= 0.5
            if rep_n not in (None, 0.0) and not native_default:
                st = 'VOID'; w.append('reported cap %s on uncapped arm' % reported)
            if 59.0 <= fps <= 61.0 and met['at60_share'] >= 0.8:
                st = max(st, 'FLAG', key=ORDER.get); w.append('looks capped at 60 (at60 share %.2f)' % met['at60_share'])
            w.append('fps %.2f' % fps)
        G['cap'] = gate(st, '; '.join(w), arm=want, reported=reported)

    # ---- alignment ----
    w = []; st = 'PASS'
    el = fnum(run.get('close_sent_s')) or fnum(run.get('elapsed_s'))
    if el is not None and last_t is not None:
        drift = last_t - el
        I['axis_minus_close_s'] = round(drift, 2)
        if abs(drift) > a.align_tol:
            st = 'FLAG'; w.append('perf axis ends %.2f s vs close %.2f s' % (last_t, el))
    devs = []
    for r in inp:
        pr = fnum(r.get('perf_rows')); t = fnum(r.get('t_s'))
        if pr is not None and t is not None and 1 <= pr <= len(tend):
            devs.append(tend[int(pr) - 1] - t)
    if devs:
        I['axis_vs_input_perf_rows_s'] = {'n': len(devs), 'median': round(statistics.median(devs), 3),
                                          'max_abs': round(max(abs(x) for x in devs), 3)}
        if max(abs(x) for x in devs) > a.align_tol:
            st = 'FLAG'; w.append('input.csv perf_rows vs axis max %.2f s' % max(abs(x) for x in devs))
    if ff is None:
        st = 'FLAG'; w.append('no wait_first_frame row')
    G['align'] = gate(st, '; '.join(w) or 'ok')
    return out


def set_rules(runs, a):
    ng = [r['gates']['host'].get('nongame_mean') for r in runs]
    ng = [x for x in ng if x is not None]
    if len(ng) >= 3:
        med = statistics.median(ng); lim = med + a.host_margin
        for r in runs:
            h = r['gates']['host']
            if h.get('nongame_mean') is not None and h['status'] == 'PASS':
                h['set_median'] = round(med, 3); h['limit'] = round(lim, 3)
                if h['nongame_mean'] > lim:
                    h['status'] = 'FLAG'; h['why'] = 'host-busy: nongame %.3f > set median %.3f + %.1f' % (h['nongame_mean'], med, a.host_margin)
    elif ng:
        for r in runs:
            h = r['gates']['host']
            if h['status'] == 'PASS':
                h['why'] += ' (set < 3 runs: median rule not applied)'
    arms = {}
    for r in runs:
        th = r['gates']['thermal']
        if 'thermal_share' in th:
            arms.setdefault((os.path.basename(str(r.get('bin_dir') or r['renderer']).rstrip('\\/')), r['gates']['cap'].get('arm')), []).append(r)
    for key, rs in arms.items():
        if len(rs) < 3:
            continue
        med = statistics.median(r['gates']['thermal']['thermal_share'] for r in rs)
        for r in rs:
            th = r['gates']['thermal']
            th['arm_median'] = round(med, 3)
            if abs(th['thermal_share'] - med) > a.thermal_outlier and th['status'] == 'PASS':
                th['status'] = 'FLAG'
                th['why'] = 'thermal outlier: share %.2f vs arm %s/%s median %.2f (> +-%.2f); ' % (
                    th['thermal_share'], key[0], key[1], med, a.thermal_outlier) + th['why']
    for r in runs:
        r['verdict'] = max((g['status'] for g in r['gates'].values()), key=ORDER.get)
        if r['verdict'] == 'NODATA':
            r['verdict'] = 'FLAG'


def report(runs, a):
    L = ['# s5_gates: span %.0f s, anchor >= %d draws, 3D >= %d, cap %s, margin %.0f s' % (a.span, a.anchor, a.thr3d, a.cap, a.margin)]
    if getattr(a, 'skipped', None) is not None:
        L.append('# runs-root %s: %d scored (tag ~ %s), %d skipped: %s' % (
            a.runs_root, len(runs), a.scored_tag, len(a.skipped), ', '.join(a.skipped) or '-'))
    for r in runs:
        L.append('')
        L.append('== %s [%s] verdict %s' % (r['tag'] or os.path.basename(r['run_dir']), r['renderer'], r['verdict']))
        for k in ('clean', 'runner', 'cold', '3d', 'span', 'input', 'cooldown', 'thermal', 'host', 'cap', 'align'):
            g = r['gates'][k]
            L.append('  %-8s %-6s %s' % (k, g['status'], g['why']))
        g3 = r['gates']['3d']
        if g3.get('anchor_t') is not None:
            L.append('  3d info: t3d %.2f anchor %.2f (last press +%s, 3D +%.2f) sustain10 %.2f; first >=%d %s, sustained %s, runner %s; first t by draws %s' % (
                g3['t3d'], g3['anchor_t'], g3['anchor_minus_last_press'], g3['anchor_minus_3d'], g3['sustain10'], a.anchor,
                r['info']['anchor_first_t'], r['info']['anchor_sustained_t'], r['info']['runner_window_start'], r['info']['first_t_by_draws']))
        sp = r['gates']['span']
        if 'end3d_t' in sp:
            L.append('  end of 3D: %s (low band %s, flat %s); window %s' % (sp['end3d_t'], sp['end3d_low_t'], sp['end3d_flat_t'], sp['window']))
        th = r['gates']['thermal']
        if 'util_gpu' in th:
            L.append('  gpu: util %s%% gr %s MHz %s W temp %s C P0 %.2f powercap %.2f (n %d)' % (
                th['util_gpu'], th['gr_mhz'], th['power_w'], th['temp_c'], th['p0_share'], th['powercap_share'], th['samples']))
        m = r.get('metrics') or {}
        if m and m.get('fps') is not None:
            L.append('  window: %d frames %.1f s fps %.2f med %.2f p99 %.2f 1%%low %.2f max %.1f ms; >=100 %d >=250 %d; at60 %.2f' % (
                m['frames'], m['window_s'], m['fps'], m['median_ms'], m['p99_ms'], m['low1_ms'], m['max_ms'], m['n_ge100'], m['n_ge250'], m['at60_share']))
        elif m:
            L.append('  window: %d frames, frame-time sum 0 (no fps)' % m['frames'])
        L.append('  axis: first frame %s, draws %s, axis-close %s s, vs input perf_rows %s' % (
            r['info'].get('first_frame_t'), r['info'].get('draws_source'), r['info'].get('axis_minus_close_s'), r['info'].get('axis_vs_input_perf_rows_s')))
    return '\n'.join(L) + '\n'


def parser():
    p = argparse.ArgumentParser()
    p.add_argument('runs', nargs='*')
    p.add_argument('--runs-root', default=None, help='add every subdir of this runs\\ folder whose run.json tag matches --scored-tag')
    p.add_argument('--scored-tag', default=r'^(?!cold-|warm\d+-).+-r\d+$',
                   help='run.json tag regex for --runs-root (run-matrix scored tags <arm>-r<k>; cold-* / warm<j>-* skipped)')
    p.add_argument('--span', type=float, default=120.0)
    p.add_argument('--anchor', type=int, default=1500)
    p.add_argument('--anchor-hold', type=float, default=1.0, help='sustained anchor: all frames >= anchor for this long (s)')
    p.add_argument('--anchor-mode', choices=['sustained', 'first'], default='sustained')
    p.add_argument('--thr3d', type=int, default=600)
    p.add_argument('--margin', type=float, default=2.0)
    p.add_argument('--anchor-late', type=float, default=90.0, help='FLAG if anchor - last press > this (s)')
    p.add_argument('--end-low-xenos', type=int, default=1000, help='end of 3D low band (xenos draws) ...')
    p.add_argument('--end-low-native', type=int, default=120, help='end of 3D low band (native draws) ...')
    p.add_argument('--end-low-hold', type=float, default=5.0, help='... held this long (s)')
    p.add_argument('--end-abs', type=int, default=10, help='end of 3D: draw range <= max(end-abs, end-rel*min) ...')
    p.add_argument('--end-rel', type=float, default=0.05)
    p.add_argument('--end-hold', type=float, default=20.0, help='... for this long (s)')
    p.add_argument('--sustain-min', type=float, default=0.5, help='FLAG if share of frames >= thr3d in 10 s after anchor < this')
    p.add_argument('--thermal-outlier', type=float, default=0.25, help='set rule: FLAG if |thermal share - arm median| > this')
    p.add_argument('--cap', choices=['60', 'none', 'auto'], default='auto')
    p.add_argument('--cap-lo', type=float, default=57.0)
    p.add_argument('--cap-hi', type=float, default=61.5)
    p.add_argument('--native-default-ok', action='store_true', help='uncapped arm: accept native default cvar (240)')
    p.add_argument('--thermal-flag', type=float, default=0.10)
    p.add_argument('--hw-void', type=float, default=0.05)
    p.add_argument('--host-margin', type=float, default=1.0)
    p.add_argument('--step-gap', type=float, default=12.0)
    p.add_argument('--align-tol', type=float, default=3.0)
    p.add_argument('--presses', type=int, default=3)
    p.add_argument('--route', default=None)
    p.add_argument('--renderer', choices=['auto', 'xenos', 'native'], default='auto')
    p.add_argument('--warm', action='store_true')
    p.add_argument('--json', default=None)
    p.add_argument('--selftest', action='store_true')
    return p


# ---------------- selftest ----------------
def scored_dirs(root, a):
    """Subdirs of a run-matrix runs\\ folder whose run.json tag matches a.scored_tag (dir names are <HHmm>-<tag>, plus
    -r<i> on a name collision, so the tag is read from run.json, not parsed from the dir name). Sets a.skipped."""
    rx = re.compile(a.scored_tag)
    keep, a.skipped = [], []
    for name in sorted(os.listdir(root)):
        d = os.path.join(root, name)
        if not os.path.isdir(d):
            continue
        tag = None
        try:
            with open(os.path.join(d, 'run.json'), encoding='utf-8-sig') as f:
                tag = json.load(f).get('tag')
        except (OSError, ValueError):
            pass
        if tag is not None and rx.search(str(tag)):
            keep.append(os.path.abspath(d))
        else:
            a.skipped.append('%s(%s)' % (name, 'no run.json tag' if tag is None else tag))
    return keep


def _mk(d, draws_fn, n=30000, ft_ms=20.0, run_extra=None, presses=(54, 63, 72), gpu_thr='0x0', sys_rows=True,
        seconds=None, native=False, cd={'met': True}, ng=1.0, steps_done=91, frames_name='frames.csv', no_perf=False,
        ft_fn=None, draws_i=None, input_stop=None, util_fn=None, files=()):
    os.makedirs(d, exist_ok=True)
    ff = 3.5
    fts = [ft_fn(i) if ft_fn else ft_ms for i in range(n)]
    total = ff + sum(fts) / 1000.0
    sec = seconds if seconds is not None else total
    run = {'tag': os.path.basename(d), 'bin_dir': 'x\\nativefinal2-bin' if native else 'x\\devfinal2-bin', 'pid': 7,
           'exit_code': 0, 'close_method': 'wm_close', 'close_seconds': 0.8, 'wer_seen': False, 'dumps': [],
           'crash_events': [], 'exited_early': False, 'seed_xenos': None, 'close_sent_s': round(sec, 2),
           'elapsed_s': round(sec + 1, 2), 'started_epoch_s': 1000.0, 'cvars': {},
           'input_script': {'steps_total': 91, 'steps_done': steps_done, 'last_step': 'stop' if steps_done == 91 else 'halted',
                            'timeouts': 0, 'error': None, 'dll_loaded_by_pid': 7, 'stopped_by_script': steps_done == 91}}
    if cd is not None:
        run['cooldown'] = cd
    run.update(run_extra or {})
    with open(os.path.join(d, 'run.json'), 'w') as f:
        json.dump(run, f)
    dfn = (lambda i, t: draws_i(i)) if draws_i else (lambda i, t: draws_fn(t))
    if not no_perf:
        with open(os.path.join(d, 'perf.csv'), 'w', newline='') as f:
            w = csv.writer(f); w.writerow(['frame_time_us', 'fps', 'draw_calls'])
            t = ff
            for i in range(n):
                t += fts[i] / 1000.0
                w.writerow([round(fts[i] * 1000), 0, 0 if native else dfn(i, t)])
    if native:
        with open(os.path.join(d, frames_name), 'w', newline='') as f:
            w = csv.writer(f); w.writerow(['frame', 'interval_ms', 'draw_calls', 'native_fps_limit_cvar'])
            if no_perf:  # frames row k = frame k (offset 0), exact intervals
                t = ff
                for k in range(n):
                    t += fts[k] / 1000.0
                    w.writerow([k + 1, fts[k], dfn(k, t), 0])
            else:        # frames row k <-> perf row k + 1
                t = ff + fts[0] / 1000.0
                for k in range(n - 1):
                    t += fts[k + 1] / 1000.0
                    w.writerow([k + 2, fts[k + 1] + (0.5 if k % 2 else -0.5), dfn(k + 1, t), 0])
    with open(os.path.join(d, 'input.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['t_s', 'line', 'cmd', 'args', 'result', 'perf_rows'])
        w.writerow([ff, 1, 'wait_first_frame', '240', 'ok', 1])
        for p in presses:
            w.writerow([p, 5, 'press', 'A', 'ok x1', int((p - ff) * 1000 / ft_ms)])
        tt = 80.0
        while tt < min(sec, 472, input_stop if input_stop is not None else 1e9):
            w.writerow([tt, 9, 'sleep', '10', 'ok', int((tt - ff) * 1000 / ft_ms)]); tt += 10
        w.writerow([round(sec + 1.0, 2), 0, 'end', '', 'steps %d/91; timeouts 0' % steps_done, ''])  # vpadhost Finish()
    with open(os.path.join(d, 'gpu.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['t_s', 'pstate', 'gr_mhz', 'temp_c', 'power_w', 'util_gpu', 'throttle'])
        for s in range(int(sec)):
            w.writerow([float(s), 'P0', 1500, 70, 20, util_fn(s) if util_fn else 99, gpu_thr(s) if callable(gpu_thr) else gpu_thr])
    for fn in files:
        open(os.path.join(d, fn), 'wb').close()
    if sys_rows:
        with open(os.path.join(d, 'sys.csv'), 'w', newline='') as f:
            w = csv.writer(f); w.writerow(['t_s', 'epoch_s', 'idle_s', 'fg_game', 'game_alive', 'screensaver', 'ac',
                                           'batt_saver', 'scheme', 'overlay', 'nongame_cores'])
            for s in range(int(sec)):
                w.writerow([s + 0.5, 1000.0 + s, 100 + s, 1, 1, 0, 1, 0, 'Balanced', 'best', ng])


def selftest():
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scratch')
    os.makedirs(base, exist_ok=True)
    td = tempfile.mkdtemp(prefix='selftest-', dir=base)
    ok = True
    a = parser().parse_args(['--span', '120', '--cap', 'none'])
    def d3(t):  # front end 220, pre-3D 790 at 82 s, 3D scenes (change every 7 s) from 105 s, flat 766 after 275 s
        return 220 if t < 82 else (790 if t < 105 else (3000 + 1500 * (int(t / 7) % 3) if t < 275 else 766))
    cases = [
        ('good', dict(draws_fn=d3, n=17000), {'verdict': 'PASS'}),
        ('short', dict(draws_fn=d3, n=10000), {'span': 'VOID'}),
        ('past3d', dict(draws_fn=d3, n=17000), {'span': 'VOID'}, ['--span', '180']),
        ('no3d', dict(draws_fn=lambda t: 220, n=17000), {'3d': 'VOID'}),
        ('thermal', dict(draws_fn=d3, n=17000, gpu_thr='0x20'), {'thermal': 'PASS', 'verdict': 'PASS'}),
        ('hwbrake', dict(draws_fn=d3, n=17000, gpu_thr='0x80'), {'thermal': 'VOID'}),
        ('nosys', dict(draws_fn=d3, n=17000, sys_rows=False), {'host': 'NODATA', 'verdict': 'FLAG'}),
        ('nocool', dict(draws_fn=d3, n=17000, cd=None), {'cooldown': 'FLAG'}),
        ('cooltimeout', dict(draws_fn=d3, n=17000, cd={'met': False, 'timed_out': True}), {'cooldown': 'FLAG'}),
        ('seeded', dict(draws_fn=d3, n=17000, run_extra={'seed_xenos': 'x'}), {'cold': 'VOID'}),
        ('exit1', dict(draws_fn=d3, n=17000, run_extra={'exit_code': 1}), {'clean': 'VOID'}),
        ('pressinwin', dict(draws_fn=d3, n=17000, presses=(54, 63, 72, 150)), {'input': 'VOID'}),
        ('capfail', dict(draws_fn=d3, n=30000, ft_ms=8.0, run_extra={'effective_cap': 60}), {'cap': 'VOID'}, ['--cap', '60']),
        ('capgpu', dict(draws_fn=d3, n=12000, ft_ms=22.0, run_extra={'effective_cap': 60}), {'cap': 'PASS'}, ['--cap', '60']),
        ('uncap60', dict(draws_fn=d3, n=17000, ft_ms=16.667, run_extra={'effective_cap': 0}), {'cap': 'FLAG'}),
        ('cap60ok', dict(draws_fn=d3, n=17000, ft_ms=16.667, run_extra={'effective_cap': 60}), {'cap': 'PASS', 'verdict': 'PASS'}, ['--cap', '60']),
        ('native', dict(draws_fn=d3, n=40000, ft_ms=6.0, native=True), {'verdict': 'PASS'}),
        ('halted_ok', dict(draws_fn=d3, n=17000, steps_done=40), {'input': 'PASS'}),
        ('spike', dict(draws_fn=lambda t: 6000 if 90.0 <= t < 90.03 else d3(t), n=17000), {'3d': 'PASS', 'anchor105': True}),
        ('spikefirst', dict(draws_fn=lambda t: 6000 if 90.0 <= t < 90.03 else d3(t), n=17000), {'anchor105': False}, ['--anchor-mode', 'first']),
        ('runnerwin', dict(draws_fn=d3, n=17000, run_extra={'window_start_s': 90.0}), {'3d': 'FLAG'}),
        # M10 E10.2 fixes
        ('B1nativefr', dict(draws_fn=d3, n=40000, ft_ms=6.0, native=True, frames_name='native-frames.csv'),
         {'verdict': 'PASS', 'src_native_frames': True}),
        ('B1noperf', dict(draws_fn=d3, n=40000, ft_ms=6.0, native=True, frames_name='native-frames.csv', no_perf=True),
         {'3d': 'PASS', 'span': 'PASS', 'cap': 'PASS', 'src_native_frames': True}),
        ('S1foreign', dict(draws_fn=d3, n=17000, files=('chrome.exe.123.dmp', 'legodimensions.exe.99.dmp'),
                           run_extra={'dumps': ['r\\chrome.exe.123.dmp', 'r\\legodimensions.exe.99.dmp'],
                                      'foreign_crash_dumps': ['r\\chrome.exe.123.dmp', 'r\\legodimensions.exe.99.dmp']}),
         {'clean': 'PASS', 'verdict': 'PASS'}),
        ('S1own', dict(draws_fn=d3, n=17000, files=('legodimensions.exe.7.dmp',),
                       run_extra={'dumps': ['r\\legodimensions.exe.7.dmp'], 'foreign_crash_dumps': []}), {'clean': 'VOID'}),
        ('S1ownfile', dict(draws_fn=d3, n=17000, files=('legodimensions.exe.7.dmp',)), {'clean': 'VOID'}),
        ('S2statusok', dict(draws_fn=d3, n=17000, run_extra={'status': 'OK', 'valid_timing': True, 'excluded': False,
                                                              'flags_info': ['cooldown_timeout']}), {'runner': 'PASS', 'verdict': 'PASS'}),
        ('S2problem', dict(draws_fn=d3, n=17000, run_extra={'status': 'PROBLEM', 'problems': ['dialogs: x']}), {'runner': 'VOID'}),
        ('S2invalid', dict(draws_fn=d3, n=17000, run_extra={'status': 'OK', 'valid_timing': False}), {'runner': 'VOID'}),
        ('S2excluded', dict(draws_fn=d3, n=17000, run_extra={'status': 'OK', 'excluded': True, 'flags_excluding': ['light_phase']}),
         {'runner': 'VOID'}),
        ('S3median', dict(draws_fn=d3, n=17000, util_fn=lambda s: 0 if s % 4 == 0 else 100), {'util100': True}),
        ('S4deadscript', dict(draws_fn=d3, n=17000, steps_done=40, input_stop=100.0), {'input': 'VOID'}),
        ('S5zeroft', dict(draws_fn=d3, n=6000, ft_fn=lambda i: 20.0 if i < 5000 else 0.0,
                          draws_i=lambda i: 3000 if i >= 5000 else 220), {'cap': 'NODATA', 'span': 'VOID'},
         ['--anchor-mode', 'first']),
        # runner effective_cap is an int (240), frames cvar a string: compare numerically
        ('natdef240ok', dict(draws_fn=d3, n=40000, ft_ms=6.0, native=True, frames_name='native-frames.csv',
                             run_extra={'effective_cap': 240}), {'cap': 'PASS'}, ['--native-default-ok']),
        ('natdef240', dict(draws_fn=d3, n=40000, ft_ms=6.0, native=True, frames_name='native-frames.csv',
                           run_extra={'effective_cap': 240}), {'cap': 'VOID'}),
    ]
    for c in cases:
        name, kw, exp = c[0], c[1], c[2]
        aa = parser().parse_args(['--span', '120', '--cap', 'none'] + (c[3] if len(c) > 3 else []))
        rd = os.path.join(td, name)
        _mk(rd, **kw)
        try:
            r = analyse(rd, aa)
            set_rules([r], aa)
            report([r], aa)
        except Exception as e:  # a crash is a failed case, not a crashed selftest
            ok = False
            print('%-12s BAD exception %r' % (name, e))
            continue
        def val(k):
            if k == 'verdict':
                return r['verdict']
            if k == 'anchor105':
                return abs((r['gates']['3d'].get('anchor_t') or 0) - 105.0) < 0.5
            if k == 'src_native_frames':
                return str(r['info'].get('draws_source', '')).startswith('native-frames.csv')
            if k == 'util100':
                return r['gates']['thermal'].get('util_gpu') == 100
            return r['gates'][k]['status']
        got = {k: val(k) for k in exp}
        good = got == exp
        ok &= good
        print('%-12s %s expected %s got %s' % (name, 'ok ' if good else 'BAD', exp, got))
        if not good:
            for k, g in r['gates'].items():
                print('     %-8s %-6s %s' % (k, g['status'], g['why']))
    # set-level host rule
    rs = []
    for i, ng in enumerate((1.0, 1.1, 0.9, 1.0, 2.5)):
        rd = os.path.join(td, 'host%d' % i)
        _mk(rd, draws_fn=d3, n=17000, ng=ng)
        rs.append(analyse(rd, a))
    set_rules(rs, a)
    got = [r['gates']['host']['status'] for r in rs]
    good = got == ['PASS'] * 4 + ['FLAG']
    ok &= good
    print('%-12s %s got %s' % ('host-set', 'ok ' if good else 'BAD', got))
    # set-level thermal outlier rule (within arm)
    rs = []
    for i, thr in enumerate(('0x20', '0x20', '0x20', '0x20', '0x0')):
        rd = os.path.join(td, 'therm%d' % i)
        _mk(rd, draws_fn=d3, n=17000, gpu_thr=thr)
        rs.append(analyse(rd, a))
    set_rules(rs, a)
    got = [r['gates']['thermal']['status'] for r in rs]
    good = got == ['PASS'] * 4 + ['FLAG']
    ok &= good
    print('%-12s %s got %s' % ('thermal-set', 'ok ' if good else 'BAD', got))
    # --runs-root scored filter: run-matrix dir names <HHmm>-<tag>[-r<i> on collision]; tag read from run.json
    rr = os.path.join(td, 'runsroot')
    for dn, tag in (('1840-cold-ship60', 'cold-ship60'), ('1840-cold-ship60-r2', 'cold-ship60'), ('1846-warm1-nat60', 'warm1-nat60'),
                    ('1850-ship60-r1', 'ship60-r1'), ('1856-n4bp60-r1', 'n4bp60-r1'), ('1902-natU-r2', 'natU-r2'), ('junk', None)):
        os.makedirs(os.path.join(rr, dn))
        if tag:
            with open(os.path.join(rr, dn, 'run.json'), 'w') as f:
                json.dump({'tag': tag}, f)
    got = [os.path.basename(x) for x in scored_dirs(rr, a)]
    good = got == ['1850-ship60-r1', '1856-n4bp60-r1', '1902-natU-r2'] and len(a.skipped) == 4
    ok &= good
    print('%-12s %s got %s skipped %s' % ('runs-root', 'ok ' if good else 'BAD', got, a.skipped))
    print('SELFTEST', 'PASS' if ok else 'FAIL', td)
    return 0 if ok else 1


def main():
    a = parser().parse_args()
    if a.selftest:
        return selftest()
    a.runs = list(a.runs)
    if a.runs_root:
        a.runs += scored_dirs(a.runs_root, a)
    if not a.runs:
        parser().print_help()
        return 2
    runs = [analyse(os.path.abspath(rd), a) for rd in a.runs]
    set_rules(runs, a)
    sys.stdout.write(report(runs, a))
    if a.json:
        with open(a.json, 'w', encoding='utf-8', newline='\n') as f:
            json.dump({'args': vars(a), 'runs': runs}, f, indent=1, default=str)
            f.write('\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())

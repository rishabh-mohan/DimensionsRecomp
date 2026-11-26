#!/usr/bin/env python3
"""S5 3D-only scorer (Agent 8). Python 3, stdlib only (+ frame_summary.py from this folder).

  python score3d.py RUNDIR [RUNDIR ...] [--reach-draws 600] [--start-draws 1500] [--span 120]
                    [--expect-cap N] [--json OUT] [--csv OUT] [--quiet]
  python score3d.py --summary RESULTS.CSV [--out summary3d.md]

Per run dir (run-timing.ps1 or harness\\run-game.ps1 layout):
  frames   native: native-frames.csv (run-timing -Frames native) or frames.csv (run-game), columns interval_ms +
           draw_calls; xenos: perf.csv, frame_time_us + draw_calls. Clock = running sum of frame times from the
           first row (the frame source's own clock; t of a frame = its end).
  reached  first frame with draw_calls >= --reach-draws (600): the "3D reached" check. Never = VOID.
  start    the anchor (M12 S5-GATES.md, sustained): the first frame that starts >= --anchor-hold s (1.0) of frames
           all >= --start-draws (1500, the same scene event on both renderers) at or after reached; --anchor-hold 0 =
           the literal first frame >= --start-draws (s3d_first_start_s, reported always). Times = frame starts.
           s3d_window_start_s = the start on the launch clock (input.csv wait_first_frame t_s + frame clock, the
           s5_gates.py axis); --write-runjson puts it in run.json window_start_s (+ effective_cap, score3d).
  span     the shortest run of frames from the start frame whose frame-time sum is >= --span s (120). Less than
           --span s of frames after the start = VOID short_span.
  metrics  frame_summary.stats on the span (nearest-rank median / p99, mean fps, over_33/100ms) + 1 % low =
           mean of the worst max(1, n//100) frame times (readout_night.py rule) and its fps; draws median and
           share3d = share of span frames with draws >= --reach-draws (info).
  gpu      gpu.csv rows inside the span. Alignment: input.csv wait_first_frame t_s when present (input_wff: gpu.csv
           and input.csv both count from the process start), else frame clock 0 on the runner clock = run.json
           first_frame_signal_s - (sum of the first 60 perf.csv rows: the first fflush) for perf, - 0 for native;
           tick resolution 1 s, so +-1 s. run-game runs have no first-frame signal: frame 0 = process start
           (the boot lag, a few s, is ignored; align = approx_process_start). Shares over the span rows:
           thermal (throttle & 0x60, sw/hw thermal slowdown), powercap (& 0x4), hwslow (& 0x8); medians of
           temp_c, gr_mhz, power_w, util_gpu; temp max.
  cap      expected = --expect-cap, else from the args (xenos --framerate_limit=N, default 0; native
           --native_fps_limit=N, default 240). seen: native = the frames csv column native_fps_limit_cvar in the
           span (else the game.log "Native presentation: ... fps_limit_cvar=N" line); a native mismatch = VOID
           cap_mismatch. Xenos has no runtime readout: seen = args (cap_source args).
  route    run.json input_script: error or pad_reads 0 = VOID route_failed; timeouts = info.
  run      run.json status other than OK (run-timing) = VOID run_status_<status>.
Exit 0 always for scoring (VOID is a result); 2 bad arguments.
"""
import argparse
import csv
import json
import os
import re
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frame_summary as fs  # noqa: E402

CSV_KEYS = ['run_dir', 's3d_status', 's3d_void_reason', 's3d_renderer', 's3d_source', 's3d_reached_s', 's3d_start_s',
            's3d_span_s', 's3d_avail_s', 's3d_frames', 's3d_fps', 's3d_median_ms', 's3d_p99_ms', 's3d_low1_ms',
            's3d_low1_fps', 's3d_over33', 's3d_over100', 's3d_draws_med', 's3d_share3d', 'gpu_rows', 'gpu_align',
            'gpu_thermal_share', 'gpu_powercap_share', 'gpu_hwslow_share', 'gpu_temp_med', 'gpu_temp_max',
            'gpu_gr_mhz_med', 'gpu_power_w_med', 'gpu_util_med', 'cap_expected', 'cap_seen', 'cap_source',
            'cooldown_wait_s', 'cooldown_temp_start_c', 'cooldown_flag', 'route_steps', 'route_timeouts',
            's3d_reach_draws', 's3d_start_draws', 's3d_span_req_s',
            's3d_anchor_hold_s', 's3d_first_start_s', 's3d_launch_offset_s', 's3d_window_start_s']


def input_wff(rd):
    """input.csv wait_first_frame t_s (s from the process start), or None."""
    p = os.path.join(rd, 'input.csv')
    if not os.path.exists(p):
        return None
    try:
        for r in read_rows(p):
            if r.get('cmd') == 'wait_first_frame':
                return num(r.get('t_s'))
    except (OSError, csv.Error):
        pass
    return None


def write_runjson(rd, r):
    """Adds the runner fields s5_gates.py cross-checks to run.json (S5-GATES.md contract 3/4): window_start_s
    (launch clock, sustained anchor), effective_cap (seen cap), and a score3d summary. Other keys are kept."""
    p = os.path.join(rd, 'run.json')
    rj = read_json(p)
    if rj is None:
        return False
    rj['window_start_s'] = r['s3d_window_start_s'] if r['s3d_window_start_s'] != '' else None
    rj['window_span_s'] = r['s3d_span_s'] if r['s3d_span_s'] != '' else None
    rj['effective_cap'] = r['cap_seen'] if r['cap_seen'] != '' else None
    rj['effective_cap_source'] = r['cap_source']
    rj['score3d'] = {k: r[k] for k in CSV_KEYS if k != 'run_dir'}
    tmp = p + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rj, f, indent=2)
    os.replace(tmp, p)
    return True


def read_json(p):
    try:
        with open(p, encoding='utf-8-sig') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def read_rows(p):
    with open(p, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def num(v, d=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def load_frames(rd, rj):
    """-> renderer, source name, [(dt_s, draws, row)]"""
    for name in ('native-frames.csv', 'frames.csv'):
        p = os.path.join(rd, name)
        if os.path.exists(p):
            rows = read_rows(p)
            if rows and 'interval_ms' in rows[0] and 'draw_calls' in rows[0]:
                return 'native', name, [(num(r['interval_ms'], 0.0) / 1e3, int(num(r['draw_calls'], 0)), r) for r in rows]
    p = os.path.join(rd, 'perf.csv')
    if os.path.exists(p):
        rows = read_rows(p)
        return 'xenos', 'perf.csv', [(num(r['frame_time_us'], 0.0) / 1e6, int(num(r['draw_calls'], 0)), r) for r in rows]
    return None, None, []


def game_args(rj):
    if not rj:
        return []
    a = rj.get('args')
    if isinstance(a, list):
        return [str(x) for x in a]
    cl = rj.get('command_line') or ''
    return cl.split()


def arg_val(args, name):
    for a in args:
        m = re.match(r'^-*%s=(.*)$' % re.escape(name), a)
        if m:
            return m.group(1)
    return None


def log_cap(rd):
    p = os.path.join(rd, 'game.log')
    try:
        with open(p, encoding='utf-8', errors='replace') as f:
            for ln in f:
                m = re.search(r'Native presentation:.*fps_limit_cvar=(-?\d+)', ln)
                if m:
                    return int(m.group(1))
    except OSError:
        pass
    return None


def mode(vals):
    return max(set(vals), key=vals.count) if vals else None


def score(rd, reach=600, start_draws=1500, span=120.0, expect_cap=None, hold=1.0):
    rd = os.path.abspath(rd)
    rj = read_json(os.path.join(rd, 'run.json')) or {}
    out = {k: '' for k in CSV_KEYS}
    out.update(run_dir=rd, s3d_reach_draws=reach, s3d_start_draws=start_draws, s3d_span_req_s=span, s3d_anchor_hold_s=hold)
    wff = None
    void = []
    renderer, src, fr = load_frames(rd, rj)
    out.update(s3d_renderer=renderer or '', s3d_source=src or '')
    status = rj.get('status')
    if status and status not in ('OK',):
        void.append('run_status_%s' % status)
    # cap
    args = game_args(rj)
    if renderer == 'native':
        a = arg_val(args, 'native_fps_limit')
        exp = int(a) if a not in (None, '') else 240
    else:
        a = arg_val(args, 'framerate_limit')
        exp = int(a) if a not in (None, '') else 0
    if expect_cap is not None:
        exp = int(expect_cap)
    out['cap_expected'] = exp
    # route
    inp = rj.get('input_script') if isinstance(rj.get('input_script'), dict) else None
    if inp:
        out['route_steps'] = '%s/%s' % (inp.get('steps_done'), inp.get('steps_total'))
        out['route_timeouts'] = inp.get('timeouts', '')
        if inp.get('error'):
            void.append('route_failed: %s' % inp.get('error'))
        elif inp.get('pad_reads') is not None and inp.get('pad_reads') <= 0:
            void.append('route_failed: pad never read')
    # cooldown
    cool = rj.get('cooldown') if isinstance(rj.get('cooldown'), dict) else None
    if cool:
        out.update(cooldown_wait_s=cool.get('waited_s', ''), cooldown_temp_start_c=cool.get('temp_start_c', ''),
                   cooldown_flag=cool.get('flag') or '')
    if not fr:
        void.append('no frames csv')
        return finish(out, void, None)
    # frame clock
    t = 0.0
    tend = []
    for dt, _, _ in fr:
        t += dt
        tend.append(t)
    total = t
    i_reach = next((i for i, (_, d, _) in enumerate(fr) if d >= reach), None)
    if i_reach is None:
        void.append('never reached 3D (no frame with >= %d draws; max %d)' % (reach, max(d for _, d, _ in fr)))
        return finish(out, void, None)
    out['s3d_reached_s'] = round(tend[i_reach], 2)
    # Anchor (M12 S5-GATES.md, sustained mode): the first frame that starts >= hold s of frames all >= start_draws
    # (offsf: single >= 1500 frames at 108-111 s inside the 790-draw pre-3D phase; full 3D from 128.5 s). hold 0 =
    # the literal first frame >= start_draws. Times are frame starts, as in s5_gates.py.
    i_first = next((i for i in range(i_reach, len(fr)) if fr[i][1] >= start_draws), None)
    i_start, rs = None, None
    if hold <= 0:
        i_start = i_first
    else:
        for i in range(i_reach, len(fr)):
            if fr[i][1] >= start_draws:
                if rs is None:
                    rs = i
                if tend[i] - (tend[rs] - fr[rs][0]) >= hold:
                    i_start = rs
                    break
            else:
                rs = None
    if i_first is not None:
        out['s3d_first_start_s'] = round(tend[i_first] - fr[i_first][0], 2)
    if i_start is None:
        void.append('no anchor: no %s >= %d draws after 3D was reached' % ('%.1f s run of frames' % hold if hold > 0 else 'frame', start_draws))
        return finish(out, void, None)
    s0 = tend[i_start] - fr[i_start][0]
    out['s3d_start_s'] = round(s0, 2)
    out['s3d_avail_s'] = round(total - s0, 2)
    # launch clock (s5_gates.py time axis): input.csv wait_first_frame t_s + frame clock
    wff = input_wff(rd)
    if wff is not None:
        out['s3d_launch_offset_s'] = round(wff, 3)
        out['s3d_window_start_s'] = round(wff + s0, 2)
    acc, j = 0.0, i_start
    sel = []
    while j < len(fr) and acc < span:
        acc += fr[j][0]
        sel.append(fr[j])
        j += 1
    out['s3d_span_s'] = round(acc, 3)
    if acc < span:
        void.append('short_span: %.1f s of frames after the 3D start (< %g s)' % (acc, span))
    fts = [dt * 1e6 for dt, _, _ in sel if dt > 0]
    if fts:
        s = fs.stats(fts)
        srt = sorted(fts)
        k = max(1, len(srt) // 100)
        low1 = sum(srt[-k:]) / k / 1000.0
        dr = [d for _, d, _ in sel]
        out.update(s3d_frames=s['frames'], s3d_fps=s['mean_fps'], s3d_median_ms=s['median_ms'], s3d_p99_ms=s['p99_ms'],
                   s3d_low1_ms=round(low1, 4), s3d_low1_fps=round(1000.0 / low1, 3), s3d_over33=s['over_33ms'],
                   s3d_over100=s['over_100ms'], s3d_draws_med=st.median(dr),
                   s3d_share3d=round(sum(1 for d in dr if d >= reach) / len(dr), 4))
    # cap seen
    if renderer == 'native':
        col = [int(num(r.get('native_fps_limit_cvar'), -999)) for _, _, r in sel if r.get('native_fps_limit_cvar') not in (None, '')]
        if col:
            out.update(cap_seen=mode(col), cap_source='frames_csv')
            if len(set(col)) > 1:
                void.append('cap_changed_in_span: %s' % sorted(set(col)))
        else:
            lc = log_cap(rd)
            out.update(cap_seen=lc if lc is not None else '', cap_source='game_log' if lc is not None else 'none')
        if out['cap_seen'] == '' or int(out['cap_seen']) != exp:
            void.append('cap_mismatch: expected %s, seen %s (%s)' % (exp, out['cap_seen'], out['cap_source']))
    else:
        out.update(cap_seen=exp if expect_cap is None else (int(arg_val(args, 'framerate_limit') or 0)), cap_source='args')
        if int(out['cap_seen']) != exp:
            void.append('cap_mismatch: expected %s, args %s' % (exp, out['cap_seen']))
    # gpu
    gp = os.path.join(rd, 'gpu.csv')
    if os.path.exists(gp):
        g = read_rows(gp)
        ff = rj.get('first_frame_signal_s')
        if wff is not None:
            origin = wff   # gpu.csv t_s and input.csv t_s both count from the process start (runner clock)
            out['gpu_align'] = 'input_wff'
        elif ff is not None:
            lead = sum(dt for dt, _, _ in fr[:60]) if renderer == 'xenos' else 0.0
            origin = float(ff) - lead
            out['gpu_align'] = 'ff_signal-%.2f' % lead
        else:
            origin = 0.0
            out['gpu_align'] = 'approx_process_start'
        lo, hi = origin + s0, origin + s0 + acc
        rows = [r for r in g if num(r.get('t_s')) is not None and lo <= num(r['t_s']) < hi]
        out['gpu_rows'] = len(rows)
        if rows:
            thr = [int(r['throttle'], 16) if (r.get('throttle') or '').startswith('0x') else None for r in rows]
            thr = [x for x in thr if x is not None]
            if thr:
                out['gpu_thermal_share'] = round(sum(1 for x in thr if x & 0x60) / len(thr), 4)
                out['gpu_powercap_share'] = round(sum(1 for x in thr if x & 0x4) / len(thr), 4)
                out['gpu_hwslow_share'] = round(sum(1 for x in thr if x & 0x8) / len(thr), 4)

            def med(c):
                v = [num(r.get(c)) for r in rows if num(r.get(c)) is not None]
                return round(st.median(v), 2) if v else ''
            out.update(gpu_temp_med=med('temp_c'), gpu_gr_mhz_med=med('gr_mhz'), gpu_power_w_med=med('power_w'),
                       gpu_util_med=med('util_gpu'))
            tv = [num(r.get('temp_c')) for r in rows if num(r.get('temp_c')) is not None]
            out['gpu_temp_max'] = max(tv) if tv else ''
    return finish(out, void, None)


def finish(out, void, _):
    out['s3d_status'] = 'VOID' if void else 'OK'
    out['s3d_void_reason'] = '; '.join(void)
    return out


def summary(results, out_md):
    rows = read_rows(results)
    arms = []
    for r in rows:
        if r.get('arm') and r['arm'] not in arms:
            arms.append(r['arm'])
    L = ['# S5 3D-only summary', '', '- source: %s' % os.path.abspath(results),
         '- per arm: medians over scored runs with s3d_status OK and no excluding flag; VOID and excluded runs are counted, never averaged',
         '- this table is descriptive; A/B claims come from the readout (bootstrap CIs), quoted as "not shown different" unless the CI excludes 0', '',
         '| arm | scored | OK | VOID | excl | fps | median ms | p99 ms | 1% low fps | 3D start s | thermal share | powercap share | temp med C | gr MHz med | cap exp/seen |',
         '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']

    def md(v):
        v = [num(x) for x in v if num(x) is not None]
        return '%.2f' % st.median(v) if v else '-'
    for a in arms:
        sc = [r for r in rows if r.get('arm') == a and r.get('scored') == 'True']
        ok = [r for r in sc if r.get('s3d_status') == 'OK' and r.get('excluded') != 'True']
        vd = [r for r in sc if r.get('s3d_status') == 'VOID']
        ex = [r for r in sc if r.get('excluded') == 'True']
        caps = sorted(set('%s/%s' % (r.get('cap_expected'), r.get('cap_seen')) for r in sc))
        L.append('| %s | %d | %d | %d | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
            a, len(sc), len(ok), len(vd), len(ex), md([r['s3d_fps'] for r in ok]), md([r['s3d_median_ms'] for r in ok]),
            md([r['s3d_p99_ms'] for r in ok]), md([r['s3d_low1_fps'] for r in ok]), md([r['s3d_start_s'] for r in ok]),
            md([r['gpu_thermal_share'] for r in ok]), md([r['gpu_powercap_share'] for r in ok]),
            md([r['gpu_temp_med'] for r in ok]), md([r['gpu_gr_mhz_med'] for r in ok]), ' '.join(caps)))
    L += ['', '## Runs', '', '| # | round | arm | status | 3D | reached s | start s | span s | fps | median | p99 | 1% low fps | thermal | temp | cooldown s | flags | void reason |',
          '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        L.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
            r.get('seq'), r.get('round'), r.get('arm'), r.get('status'), r.get('s3d_status'), r.get('s3d_reached_s'),
            r.get('s3d_start_s'), r.get('s3d_span_s'), r.get('s3d_fps'), r.get('s3d_median_ms'), r.get('s3d_p99_ms'),
            r.get('s3d_low1_fps'), r.get('gpu_thermal_share'), r.get('gpu_temp_med'), r.get('cooldown_wait_s'),
            ' '.join(x for x in (r.get('flags_excluding'), r.get('flags_info'), r.get('cooldown_flag')) if x),
            (r.get('s3d_void_reason') or '').replace('|', '/')))
    txt = '\n'.join(L) + '\n'
    if out_md:
        with open(out_md, 'w', encoding='utf-8', newline='\n') as f:
            f.write(txt)
    return txt


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('rundirs', nargs='*')
    ap.add_argument('--reach-draws', type=int, default=600)
    ap.add_argument('--start-draws', type=int, default=1500)
    ap.add_argument('--span', type=float, default=120.0)
    ap.add_argument('--expect-cap', type=int, default=None)
    ap.add_argument('--anchor-hold', type=float, default=1.0, help='sustained anchor: all frames >= --start-draws for this long (s); 0 = first frame')
    ap.add_argument('--write-runjson', action='store_true', help='add window_start_s, effective_cap and score3d to each run.json')
    ap.add_argument('--json', default=None, help='write the result (one run: an object; several: a list)')
    ap.add_argument('--csv', default=None)
    ap.add_argument('--quiet', action='store_true')
    ap.add_argument('--summary', default=None, help='results.csv of a run-matrix out dir')
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    if a.summary:
        t = summary(a.summary, a.out)
        if not a.quiet:
            print(t)
        return 0
    if not a.rundirs:
        ap.print_usage()
        return 2
    res = [score(rd, a.reach_draws, a.start_draws, a.span, a.expect_cap, a.anchor_hold) for rd in a.rundirs]
    if a.write_runjson:
        for r in res:
            if not write_runjson(r['run_dir'], r):
                print('note: no readable run.json in %s (not updated)' % r['run_dir'])
    if a.json:
        with open(a.json, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(res[0] if len(res) == 1 else res, f, indent=1)
    if a.csv:
        with open(a.csv, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=CSV_KEYS)
            w.writeheader()
            w.writerows(res)
    if not a.quiet:
        for r in res:
            print('%s [%s %s] %s%s' % (os.path.basename(r['run_dir']), r['s3d_renderer'], r['s3d_source'], r['s3d_status'],
                                        (' (' + r['s3d_void_reason'] + ')') if r['s3d_void_reason'] else ''))
            print('   reached(>=%s) %s s  start(>=%s, hold %s s) %s s [launch clock %s s; first >=%s %s s]  span %s s (avail %s s)  frames %s  fps %s  median %s ms  p99 %s ms  1%%low %s fps  draws med %s  share3d %s' % (
                r['s3d_reach_draws'], r['s3d_reached_s'], r['s3d_start_draws'], r['s3d_anchor_hold_s'], r['s3d_start_s'], r['s3d_window_start_s'],
                r['s3d_start_draws'], r['s3d_first_start_s'], r['s3d_span_s'], r['s3d_avail_s'],
                r['s3d_frames'], r['s3d_fps'], r['s3d_median_ms'], r['s3d_p99_ms'], r['s3d_low1_fps'], r['s3d_draws_med'], r['s3d_share3d']))
            print('   gpu rows %s (%s): thermal %s powercap %s hwslow %s  temp med %s max %s  gr %s MHz  power %s W  util %s  | cap exp %s seen %s (%s) | route %s timeouts %s | cooldown %s s %s %s' % (
                r['gpu_rows'], r['gpu_align'], r['gpu_thermal_share'], r['gpu_powercap_share'], r['gpu_hwslow_share'],
                r['gpu_temp_med'], r['gpu_temp_max'], r['gpu_gr_mhz_med'], r['gpu_power_w_med'], r['gpu_util_med'],
                r['cap_expected'], r['cap_seen'], r['cap_source'], r['route_steps'], r['route_timeouts'],
                r['cooldown_wait_s'], r['cooldown_temp_start_c'], r['cooldown_flag']))
    return 0


if __name__ == '__main__':
    sys.exit(main())

"""SMOKE-FINAL2 first-3D post-check (M8, session 3) for run-game.ps1 attract runs of the final2 bin pair.
Usage: python -B smoke3d_post.py --arm xenos=<run dir> --arm native=<run dir> [--out FILE]
       (the arm name is the check-defaults mode: xenos or native)
Per arm, read-only:
  clean exit    run.json exit_code 0, not exited early, close_method wm_close, no WER / crash events / dumps
  plain default run.json cvars empty; env only the harness's own LEGO_NATIVE_FRAME_METRICS + AGENT3_VPAD
  route         input_script: error null, timeouts 0, pad dll loaded by the game pid, wait_first_frame ok,
                START / A / A pressed ok, every step up to the close done (steps_done >= the steps before the close)
  first 3D      xenos: perf.csv draw_calls >= 600 (the attract's 625/780 frame);
                native (PROXY, perf.csv has no draw counts): >= 5 new 'Native GPU' shader/surface/texture lines in
                game.log after the idle-10 mark (the front end is idle by then; the attract load makes new ones),
                plus gpu.csv util_gpu median after the first such line vs before (info)
  no_wait       0 game.log lines with d3d12_pipeline_creation_no_wait
  defaults      build/agent2/final/check-defaults.py <log> --mode <arm> PASS (rotated logs are joined first)
Exit 0 = every check of every arm PASS.
"""
import argparse, csv, json, os, re, subprocess, sys, statistics as st
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
CD = os.path.join(ROOT, 'build', 'agent2', 'final', 'check-defaults.py')
TH = 600
ACT = re.compile(r'Native GPU: (placement|unrecognized) (vertex|pixel) shader|Native GPU: created surface|'
                 r'Native GPU: adopted guest texture|shader not present in AOT')
TS = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\]')
out = []


def say(s=''):
    out.append(s)
    print(s)


def log_lines(rd):
    """game.N.log (oldest first) then game.log -> list of lines, and the joined path for check-defaults."""
    rot = sorted([f for f in os.listdir(rd) if re.fullmatch(r'game\.\d+\.log', f)], key=lambda f: -int(f.split('.')[1]))
    files = rot + ['game.log']
    lines = []
    for f in files:
        p = os.path.join(rd, f)
        if os.path.exists(p):
            with open(p, encoding='utf-8', errors='replace') as fh:
                lines += fh.read().splitlines()
    if rot:
        jp = os.path.join(HERE, 'post', os.path.basename(rd) + '-game-joined.log')
        os.makedirs(os.path.dirname(jp), exist_ok=True)
        with open(jp, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('\n'.join(lines) + '\n')
        return lines, jp, files
    return lines, os.path.join(rd, 'game.log'), files


def check_arm(mode, rd):
    fails = []

    def check(name, ok, info=''):
        say(('PASS ' if ok else 'FAIL ') + name + (': ' + str(info) if info != '' else ''))
        if not ok:
            fails.append(name)

    say('== arm %s: %s' % (mode, rd))
    with open(os.path.join(rd, 'run.json'), encoding='utf-8-sig') as f:
        J = json.load(f)
    say('INFO bin %s; exe sha256 %s; desktop %s; started %s; elapsed %s s; seconds_requested %s' % (
        J.get('bin_dir'), (J.get('exe_sha256') or '')[:16], J.get('desktop'), J.get('started'), J.get('elapsed_s'), J.get('seconds_requested')))
    check('clean exit', J.get('exit_code') == 0 and not J.get('exited_early') and J.get('close_method') in ('wm_close', 'script_stop', None)
          and not J.get('wer_seen') and not J.get('crash_events') and not J.get('dumps'),
          'exit %s early %s close %s %.2f s wer %s crash_events %d dumps %d' % (
              J.get('exit_code_hex'), J.get('exited_early'), J.get('close_method'), J.get('close_seconds') or 0,
              J.get('wer_seen'), len(J.get('crash_events') or []), len(J.get('dumps') or [])))
    env = J.get('env') or {}
    check('plain default (no cvars; env only harness LEGO_NATIVE_FRAME_METRICS/AGENT3_VPAD)',
          not (J.get('cvars') or {}) and set(env) <= {'LEGO_NATIVE_FRAME_METRICS', 'AGENT3_VPAD'},
          'cvars %s env %s' % (J.get('cvars'), sorted(env)))
    cl = J.get('command_line') or ''
    extra = [a for a in cl.split()[1:] if a.split('=')[0] not in ('--log_file', '--log_flush_interval', '--perf_log_csv', '--native_settings_load',
                                                                  '--discord_rpc', '--audio_mute', '--pause_when_unfocused', '--input_backend')]
    check('no extra game args', not extra, ' '.join(extra) or 'none')

    # route
    I = J.get('input_script') or {}
    rows = []
    ic = os.path.join(rd, 'input.csv')
    if os.path.exists(ic):
        with open(ic, encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
    ok_ff = any(r['cmd'] == 'wait_first_frame' and r['result'].startswith('ok') for r in rows)
    presses = [(r['args'], r['result']) for r in rows if r['cmd'] == 'press']
    ok_press = [a for a, res in presses if res.startswith('ok')] == ['START', 'A', 'A']
    close_s = J.get('close_sent_s') or J.get('elapsed_s') or 0
    marks = [r['args'] for r in rows if r['cmd'] == 'mark']
    check('route: pad loaded by the game, no error/timeouts, first frame + START/A/A ok',
          I.get('error') is None and I.get('timeouts') == 0 and I.get('dll_loaded_by_pid') == J.get('pid') and ok_ff and ok_press
          and (I.get('pad_active_reads') or 0) > 0,
          'steps_done %s/%s last %s; marks %d (last %s); presses %s; pad_active_reads %s; close at %.1f s' % (
              I.get('steps_done'), I.get('steps_total'), I.get('last_step'), len(marks), marks[-1] if marks else '-',
              ' '.join('%s:%s' % p for p in presses), I.get('pad_active_reads'), close_s))
    late_steps = [r for r in rows if float(r['t_s']) > close_s - 12]
    check('route: steps ran up to the close (a step within 12 s of the close)', bool(late_steps) or I.get('stopped_by_script'),
          'last row t=%s %s %s' % ((rows[-1]['t_s'], rows[-1]['cmd'], rows[-1]['args']) if rows else ('-', '-', '-')))

    lines, logp, files = log_lines(rd)
    say('INFO game log files %s, %d lines' % ('+'.join(files), len(lines)))

    # first 3D
    first = None
    pf = os.path.join(rd, 'perf.csv')
    t, mx, n = 0.0, 0, 0
    if os.path.exists(pf):
        with open(pf, encoding='utf-8-sig', newline='') as f:
            for r in csv.DictReader(f):
                n += 1
                t += float(r['frame_time_us'] or 0) / 1e6
                d = int(float(r['draw_calls'] or 0))
                mx = max(mx, d)
                if first is None and d >= TH:
                    first = (round(t, 1), n, d)
    if mode == 'xenos':
        check('first 3D (perf.csv draw_calls >= %d)' % TH, first is not None,
              ('at perf %.1f s, frame %d, %d draws' % first if first else 'never') + '; max draws %d over %d frames / %.1f s' % (mx, n, t))
        if first:
            check('first 3D + >= 60 s of run after it', t - first[0] >= 60, 'perf %.1f s after first 3D' % (t - first[0]))
    else:
        idle = next((r for r in rows if r['cmd'] == 'mark' and r['args'] == 'idle-10'), None)
        k0 = int(idle['log_lines']) if idle and idle.get('log_lines', '').lstrip('-').isdigit() else None
        tsl = []
        for i, l in enumerate(lines):
            m = TS.match(l)
            if m and ACT.search(l):
                tsl.append((i, datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S.%f')))
        t_start = datetime.fromisoformat(J['started'][:26]) if J.get('started') else None
        late = [x for x in tsl if k0 is not None and x[0] >= k0]
        rel = lambda ts: round((ts - t_start.replace(tzinfo=None)).total_seconds(), 1) if t_start else None
        check('first 3D PROXY (native): >= 5 new Native GPU shader/surface/texture lines after the idle-10 mark', k0 is not None and len(late) >= 5,
              'idle-10 at log line %s; %d lines after it, first at %s s after launch, last at %s s' % (
                  k0, len(late), rel(late[0][1]) if late else '-', rel(late[-1][1]) if late else '-'))
        bins = {}
        for _, ts in tsl:
            r_ = rel(ts)
            if r_ is not None:
                bins[int(r_ // 20) * 20] = bins.get(int(r_ // 20) * 20, 0) + 1
        say('INFO Native GPU activity lines per 20 s after launch: ' + ', '.join('%d-%d: %d' % (k, k + 20, v) for k, v in sorted(bins.items())))
        gp = os.path.join(rd, 'gpu.csv')
        if late and os.path.exists(gp) and t_start:
            a3 = rel(late[0][1])
            with open(gp, encoding='utf-8-sig', newline='') as f:
                g = [(float(r['t_s']), float(r['util_gpu'] or 0)) for r in csv.DictReader(f)]
            pre = [u for s, u in g if a3 - 40 <= s < a3]
            post = [u for s, u in g if a3 + 5 <= s < a3 + 45]
            if pre and post:
                say('INFO gpu.csv util_gpu median 40 s before the proxy point %.0f %% vs 5-45 s after %.0f %% (gpu.csv t_s ~ launch time)' % (
                    st.median(pre), st.median(post)))
            check('first 3D proxy + >= 60 s of run after it', close_s - a3 >= 60, '%.1f s' % (close_s - a3))
        if t:
            b = {}
            tt = 0.0
            with open(pf, encoding='utf-8-sig', newline='') as f:
                for r in csv.DictReader(f):
                    x = float(r['frame_time_us'] or 0)
                    tt += x / 1e6
                    b.setdefault(int(tt // 20) * 20, []).append(x / 1e3)
            say('INFO perf.csv median frame ms per 20 s of frame time: ' + ', '.join(
                '%d-%d: %.2f' % (k, k + 20, sorted(v)[len(v) // 2]) for k, v in sorted(b.items())))

    nw = [l for l in lines if 'd3d12_pipeline_creation_no_wait' in l]
    check('no game.log line with d3d12_pipeline_creation_no_wait', not nw, '%d%s' % (len(nw), (': ' + nw[0][:160]) if nw else ''))

    cp = subprocess.run([sys.executable, '-B', CD, logp, '--mode', mode], capture_output=True, text=True)
    say('--- check-defaults --mode %s (exit %d)' % (mode, cp.returncode))
    say(cp.stdout.rstrip())
    check('check-defaults --mode %s PASS' % mode, cp.returncode == 0 and 'RESULT PASS' in cp.stdout, 'exit %d' % cp.returncode)
    say('ARM %s: %s' % (mode, 'ALL PASS' if not fails else 'FAIL: ' + '; '.join(fails)))
    say()
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arm', action='append', required=True, help='xenos=<run dir> or native=<run dir>')
    ap.add_argument('--out')
    a = ap.parse_args()
    say('# smoke3d_post %s (check-defaults %s)' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), CD))
    allf = []
    for s in a.arm:
        mode, rd = s.split('=', 1)
        if mode not in ('xenos', 'native'):
            say('FAIL bad arm %s' % s)
            allf.append(s)
            continue
        try:
            allf += ['%s: %s' % (mode, f) for f in check_arm(mode, os.path.abspath(rd))]
        except Exception as e:
            say('FAIL arm %s: %s: %s' % (mode, type(e).__name__, e))
            allf.append('%s: exception' % mode)
    say('RESULT: ' + ('ALL PASS' if not allf else 'FAIL (%d): %s' % (len(allf), '; '.join(allf))))
    if a.out:
        with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(out) + '\n')
    return 1 if allf else 0


if __name__ == '__main__':
    sys.exit(main())

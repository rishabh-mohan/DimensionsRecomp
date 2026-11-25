"""M8 SMOKE-FINAL2 checker for one plain first-boot run (Overseer brief 22:10Z, option (a) 22:11Z).
Usage: python check_final2.py <run dir> --mode xenos|native
Checks: run.json clean exit (0x0, not exited early, no kill), no dialogs / WerFault / crash artifacts,
first 3D = first frame with draw_calls >= 600 (perf.csv for xenos, native-frames.csv for native),
no game.log line containing d3d12_pipeline_creation_no_wait, check-defaults.py --mode <mode> PASS.
Read-only. Exit 0 = all PASS.
"""
import argparse, csv, json, os, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
CD = os.path.join(ROOT, 'build', 'agent2', 'final', 'check-defaults.py')
TH = 600
fails = []


def check(name, ok, info=''):
    print(('PASS ' if ok else 'FAIL ') + name + (': ' + str(info) if info != '' else ''))
    if not ok:
        fails.append(name)


ap = argparse.ArgumentParser()
ap.add_argument('run')
ap.add_argument('--mode', required=True, choices=['xenos', 'native'])
a = ap.parse_args()
rd = os.path.abspath(a.run)
print('# check_final2 %s --mode %s' % (rd, a.mode))

with open(os.path.join(rd, 'run.json'), encoding='utf-8-sig') as f:
    J = json.load(f)
cl = J.get('close') or {}
check('clean exit', J.get('exit_code_hex') == '0x00000000' and not J.get('exited_early') and not cl.get('killed'),
      'exit=%s exited_early=%s killed=%s close_wait=%s s watch=%s s' % (J.get('exit_code_hex'), J.get('exited_early'),
                                                                     cl.get('killed'), cl.get('exit_wait_s'), J.get('watch_s')))
check('no dialogs', not J.get('dialogs'), J.get('dialogs'))
check('no WerFault', not J.get('werfault_seen'), J.get('werfault_seen'))
check('no crash artifacts', not J.get('artifacts'), J.get('artifacts'))
check('no args beyond the harness defaults (no -Cvar/-Env)', not J.get('env') and not any(x.startswith('--') and '=' in x and x.split('=')[0] not in
      ('--log_file', '--perf_log_csv', '--native_settings_load', '--discord_rpc', '--audio_mute', '--pause_when_unfocused')
      for x in J.get('args', [])), ' '.join(x.split('=')[0] for x in J.get('args', [])))
print('INFO not_responding_samples=%s sample_errors=%s peak_ws_mb=%s first_window_s=%s build_procs_max=%s sys_busy_mean=%s other_cores_mean=%s' % (
    J.get('not_responding_samples'), J.get('sample_errors'), J.get('peak_ws_mb'), J.get('first_window_s'),
    J.get('build_procs_max'), J.get('sys_busy_pct_mean'), J.get('other_cores_mean')))

# first 3D
if a.mode == 'xenos':
    src = 'perf.csv'
    p = os.path.join(rd, src)
    first, t, mx, n = None, 0.0, 0, 0
    if os.path.exists(p):
        with open(p, encoding='utf-8-sig', newline='') as f:
            for r in csv.DictReader(f):
                n += 1
                t += float(r['frame_time_us']) / 1e6
                d = int(float(r['draw_calls'] or 0))
                mx = max(mx, d)
                if first is None and d >= TH:
                    first = (round(t, 1), n, d)
    check('first 3D (draw_calls >= %d in %s)' % (TH, src), first is not None,
          ('at %.1f s of frame time, frame %d, %d draws' % first if first else 'never') + '; frames %d, max draws %d, %.1f s' % (n, mx, t))

# game.log
gl = os.path.join(rd, 'game.log')
with open(gl, encoding='utf-8', errors='replace') as f:
    lines = f.read().splitlines()
nw = [l for l in lines if 'd3d12_pipeline_creation_no_wait' in l]
check('no game.log line with d3d12_pipeline_creation_no_wait', not nw, '%d lines%s' % (len(nw), (': ' + nw[0][:160]) if nw else ''))
print('INFO game.log %d lines; last: %s' % (len(lines), lines[-1][:160] if lines else ''))

# GPU-activity timeline (both modes; the native first-3D proxy)
import re
from datetime import datetime
TS = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\]')
ACT = re.compile(r'Native GPU: (placement|unrecognized) (vertex|pixel) shader|Native GPU: created surface|Native GPU: adopted guest texture|shader not present in AOT')
t0, act = None, []
for l in lines:
    m = TS.match(l)
    if not m:
        continue
    ts = datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S.%f')
    t0 = t0 or ts
    if ACT.search(l):
        act.append((ts - t0).total_seconds())
bins = {}
for s in act:
    bins[int(s // 20) * 20] = bins.get(int(s // 20) * 20, 0) + 1
print('INFO GPU-activity lines (shader/surface/texture) per 20 s of log time: ' + (', '.join('%d-%d s: %d' % (k, k + 20, v) for k, v in sorted(bins.items())) or 'none'))
# perf.csv frame time per 20 s of frame time (step at scene change)
pf = os.path.join(rd, 'perf.csv')
if os.path.exists(pf):
    t, b = 0.0, {}
    with open(pf, encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            x = float(r['frame_time_us'] or 0)
            t += x / 1e6
            k = int(t // 20) * 20
            b.setdefault(k, []).append(x / 1e3)
    print('INFO perf.csv median frame ms per 20 s of frame time: ' + ', '.join(
        '%d-%d: %.2f (n %d)' % (k, k + 20, sorted(v)[len(v) // 2], len(v)) for k, v in sorted(b.items())))
if a.mode == 'native':
    late = [s for s in act if s >= 100]
    check('first 3D PROXY (native): >= 5 new GPU shader/surface lines >= 100 s after the first log line', len(late) >= 5,
          '%d lines, first at %s s (Xenos attract 3D came at ~130-150 s)' % (len(late), round(late[0], 1) if late else '-'))

# check-defaults
cp = subprocess.run([sys.executable, '-B', CD, gl, '--mode', a.mode], capture_output=True, text=True)
print('--- check-defaults --mode %s (exit %d)' % (a.mode, cp.returncode))
print(cp.stdout.rstrip())
if cp.stderr.strip():
    print('stderr: ' + cp.stderr.strip()[:400])
check('check-defaults --mode %s PASS' % a.mode, cp.returncode == 0 and 'RESULT PASS' in cp.stdout, 'exit %d' % cp.returncode)

print('RESULT: ' + ('ALL PASS' if not fails else 'FAIL: ' + '; '.join(fails)))
sys.exit(1 if fails else 0)

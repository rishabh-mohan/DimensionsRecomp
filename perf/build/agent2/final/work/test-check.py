import subprocess, sys, os
D = os.path.dirname(os.path.abspath(__file__))
CHK = os.path.join(D, '..', 'check-defaults.py')
P = '[2026-11-25 07:00:00.000] [info] [core] [t1] '
RT_NEW = ('Final defaults: physical_protect_hold_global_lock=true(default) physical_protect_keep_watch=true(default) '
          'host_timer_resolution_ms=1(default) host_timer_throttling_optout=true(default) precise_guest_sleep=true(default) '
          'wait_timeout_round_up=true(default) cs_spin=true(default) spinlock_pause_spin=true(default) '
          'clock_lockfree=true(default) tls_bounds_fix=true(default) timer_queue_precise_wait=true(default)')
GPU_NEW = 'Final defaults (GPU): shared_memory_single_hold_rearm=true(default) physical_protect_keep_watch_verify=false(default)'
X = [RT_NEW, GPU_NEW, 'Host timer resolution set to 1 ms (background opt-out on)',
     'C1 keep-watch: on (with physical_protect_hold_global_lock)', 'TimerQueue: precise wait (timer_queue_precise_wait)',
     'C1 keep-watch: first kept protect at ED19F000, 299892736 bytes',
     'GPU wait back-off: ON (quantum 500 us, spin 30 us); stats OFF; GetData hook built.']
N = [RT_NEW, 'Host timer resolution set to 1 ms (background opt-out on)',
     'C1 keep-watch: on, but blocked for this process (native renderer)',
     'TimerQueue: precise wait (timer_queue_precise_wait)', 'Native GPU: shader miss cache ON (build default)']
RT_OFF = RT_NEW.replace('=true(default)', '=false(cmdline)').replace('=1(default)', '=0(cmdline)')
O = [RT_OFF, GPU_NEW.replace('rearm=true(default)', 'rearm=false(cmdline)'),
     'GPU wait back-off: OFF (LEGO_GPU_WAIT_BACKOFF_US=off).']
cases = [
 ('xenos-good', X, 'xenos', 0),
 ('xenos-cmdline-src', [X[0].replace('cs_spin=true(default)', 'cs_spin=true(cmdline)')] + X[1:], 'xenos', 1),
 ('xenos-env-backoff-missing', X[:-1], 'xenos', 1),
 ('xenos-verify-on', X + ['C1 verify: on. Hashing CPU uploads'], 'xenos', 1),
 ('xenos-unregistered', [X[0].replace('tls_bounds_fix=true(default)', 'tls_bounds_fix=unregistered')] + X[1:], 'xenos', 1),
 ('native-good', N, 'native', 0),
 ('native-mc-off', N[:-1] + ['Native GPU: shader miss cache OFF (LEGO_NATIVE_SHADER_MISS_CACHE set)'], 'native', 1),
 ('off-good', O, 'off', 0),
 ('native-old-good', ['Native GPU: shader miss cache ON (build default)'], 'native-old', 0),
 ('native-old-but-new-sdk', N, 'native-old', 1),
 ('off-but-default-on', X, 'off', 1),
 ('xenos-stats-on', X[:-1] + ['GPU wait back-off: ON (quantum 500 us, spin 30 us); stats ON; GetData hook built.'],
  'xenos', 1),
 ('xenos-no-getdata-hook', X[:-1] + ['GPU wait back-off: ON (quantum 500 us, spin 30 us); stats OFF.'], 'xenos', 1),
 ('legacy-stats-on', X[2:-1] + ['GPU wait back-off: ON (quantum 500 us, spin 30 us); stats ON; GetData hook built.'],
  'legacy', 1),
 ('legacy-good', X[2:], 'legacy', 0),
 ('native-old-with-new-gpu-dll', ['Native GPU: shader miss cache ON (build default)', GPU_NEW], 'native-old', 1),
]
bad = 0
for name, lines, mode, exp in cases:
    p = os.path.join(D, f'synth-{name}.log')
    open(p, 'w').write(''.join(P + l + '\n' for l in lines))
    r = subprocess.run([sys.executable, CHK, p, '--mode', mode], capture_output=True, text=True)
    ok = r.returncode == exp
    bad += not ok
    print(f'{"ok " if ok else "BAD"} {name:28} mode={mode:6} rc={r.returncode} want {exp}  {r.stdout.strip().splitlines()[-1]}')
    os.remove(p)
print('SYNTH', 'PASS' if not bad else f'FAIL {bad}')

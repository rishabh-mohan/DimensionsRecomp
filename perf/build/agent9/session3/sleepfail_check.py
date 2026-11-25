"""M9 S3T-9 item 4: independent sleep_fail check of a Q = 500 stats row (read-only).

Usage: python sleepfail_check.py <run dir>
Finds every field by name (sleep_sum comes before sleep_fail; never parse by position).
Exit 0 = PASS (init line Q 500 + stats ON exactly once, >= 1 stats line, every stats line parsed,
sleep_fail == 0 on every line, sleeps > 0, run.json env Q 500 + stats 1, exit code 0, no STUCK-LOCK).
"""
import json, os, re, sys

run = sys.argv[1]
log = open(os.path.join(run, 'game.log'), encoding='utf-8', errors='replace').read().splitlines()
fails = []


def check(name, ok, detail=''):
    print(('PASS ' if ok else 'FAIL ') + name + (': ' + str(detail) if detail != '' else ''))
    if not ok:
        fails.append(name)


init = [l for l in log if 'GPU wait back-off:' in l]
check('exactly one back-off line', len(init) == 1, len(init))
check('it is ON, quantum 500 us, spin 30 us, stats ON',
      bool(init) and 'GPU wait back-off: ON (quantum 500 us, spin 30 us); stats ON; GetData hook built.' in init[0],
      init[0].split('] ', 4)[-1] if init else '')

stats = [l for l in log if 'GPU wait stats (5 s):' in l]
check('stats lines present', len(stats) > 0, len(stats))
FIELDS = {
    'sleep': r'\bsleep (\d+) sleep_sum',          # the count; anchored on the next name so 'sleep>' etc. never match
    'sleep_sum_ms': r'\bsleep_sum ([\d.]+) ms',
    'sleep_fail': r'\bsleep_fail (\d+)',
    'yield': r'\byield (\d+)',
    'pause': r'\bpause (\d+)',
    'l1_waits': r'\bL1 waits (\d+)',
    'l1_polls': r'\bL1 waits \d+ polls (\d+)',
    'l2_waits': r'\bL2 tries \d+ waits (\d+)',
}
tot = {k: 0.0 for k in FIELDS}
bad = 0
nz = []
for i, l in enumerate(stats):
    vals = {}
    for k, rx in FIELDS.items():
        m = re.search(rx, l)
        if not m:
            bad += 1
            break
        vals[k] = float(m.group(1))
    else:
        for k in FIELDS:
            tot[k] += vals[k]
        if vals['sleep_fail'] != 0:
            nz.append((i, l[:24], vals['sleep_fail']))
check('every stats line has every field', bad == 0, '%d unparsed' % bad)
check('sleep_fail == 0 on every line', not nz, nz[:5] if nz else 'all %d lines 0' % len(stats))
check('sleeps happened (Q > 0 path exercised)', tot['sleep'] > 0, int(tot['sleep']))
print('totals: ' + ', '.join('%s %s' % (k, ('%.2f' % v) if k.endswith('_ms') else int(v)) for k, v in tot.items()))
if tot['sleep']:
    print('mean sleep %.3f ms per sleep (Q = 0.5 ms; timer granularity adds the rest)' %
          (tot['sleep_sum_ms'] / tot['sleep']))

stuck = [l for l in log if 'STUCK-LOCK' in l]
check('no STUCK-LOCK', not stuck, len(stuck))
rj = json.load(open(os.path.join(run, 'run.json'), encoding='utf-8-sig'))
env = rj.get('env', {})
check('run.json env Q 500, stats 1, no spin override',
      env.get('LEGO_GPU_WAIT_BACKOFF_US') == '500' and env.get('LEGO_GPU_WAIT_STATS') == '1'
      and 'LEGO_GPU_WAIT_SPIN_US' not in env, {k: v for k, v in env.items() if k.startswith('LEGO_GPU')})
check('exit code 0, not exited early', rj.get('exit_code') == 0 and rj.get('exited_early') is False,
      (rj.get('exit_code'), rj.get('exited_early')))
print('bin_dir ' + str(rj.get('bin_dir')))
print('RESULT: %s (%d FAIL)' % ('PASS' if not fails else 'FAIL', len(fails)))
sys.exit(1 if fails else 0)

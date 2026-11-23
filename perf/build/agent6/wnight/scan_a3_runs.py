"""scan_a3_runs.py -- read-only (Agent 6, task #19): one line per Agent 3 run dir from this evening.

Prints tag, bin, env (minus the harness's own keys), cvars, input script and exit code from run.json, so a
devoff4b attract run with nothing set can be picked as the 'off' reference for the expect-w9.json test.
Usage: python -B build/agent6/wnight/scan_a3_runs.py [glob, default build/agent3/runs/20261122-2*]
"""
import glob
import json
import os
import sys

pat = sys.argv[1] if len(sys.argv) > 1 else os.path.join('build', 'agent3', 'runs', '20261122-2*')
for d in sorted(glob.glob(pat)):
    p = os.path.join(d, 'run.json')
    if not os.path.exists(p):
        continue
    try:
        with open(p, encoding='utf-8-sig') as fh:
            j = json.load(fh)
    except Exception as e:  # noqa: BLE001
        print(os.path.basename(d), 'ERR', e)
        continue
    env = {k: v for k, v in (j.get('env') or {}).items() if k not in ('LEGO_NATIVE_FRAME_METRICS', 'AGENT3_VPAD')}
    cv = j.get('cvars') or {}
    sc = os.path.basename(((j.get('input_script') or {}).get('script') or ''))
    print('%-44s bin=%-13s env=%s cvars=%s script=%s exit=%s log=%s' % (
        os.path.basename(d), os.path.basename(str(j.get('bin_dir') or '')), env, cv, sc, j.get('exit_code'),
        j.get('log_bytes')))

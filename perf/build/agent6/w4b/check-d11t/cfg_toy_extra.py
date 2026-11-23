"""Extra context for the d11t check (read-only, stdlib): per-run arm config from run.json (bin_dir, cvars, env) for
d0 + d11t, and the raw Toypad lines (timestamp kept, payload cut to 8 bytes) of the runs whose handshake is doubled.
  python -B build/agent6/w4b/check-d11t/cfg_toy_extra.py
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..', 'build', 'agent8', 'matrix', '20261122-1541', 'runs'))
CFG_RUNS = ['1542-d0-r1', '1558-d0-r2', '1604-d0-r3', '1611-d0-r4', '1549-d11t-r1', '1556-d11t-r2', '1602-d11t-r3',
            '1608-d11t-r4', '1541-cold-d0']
TOY_RUNS = ['1604-d0-r3', '1600-d3-r3']
for run in CFG_RUNS:
    with open(os.path.join(RUNS, run, 'run.json'), 'r', encoding='utf-8-sig') as fh:
        rj = json.load(fh)
    p = rj.get('params', {})
    print('%-13s tag=%s bin=%s cvar=%s env=%s env_set=%s valid_timing=%s flags=%s' % (
        run, rj.get('tag'), os.path.basename(str(rj.get('bin_dir'))), p.get('cvar'), p.get('env'), rj.get('env_set'),
        rj.get('valid_timing'), rj.get('flags')))
for run in TOY_RUNS:
    print('--- Toypad lines of %s' % run)
    with open(os.path.join(RUNS, run, 'game.log'), 'r', encoding='utf-8-sig', errors='replace') as fh:
        for line in fh:
            if 'Toypad' in line or 'Portal' in line:
                line = line.rstrip()
                m = re.match(r'^(.*Toypad\[(?:Write|Read )\] )(.*)$', line)
                if m:
                    line = m.group(1) + ' '.join(m.group(2).split()[:8]) + ' ...'
                print('   ' + line[:170])

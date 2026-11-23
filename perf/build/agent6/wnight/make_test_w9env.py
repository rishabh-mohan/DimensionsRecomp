#!/usr/bin/env python3
"""Negative test for w9_envcheck.py (Agent 6, task #22). Writes only under
build/agent6/wnight/test-w9env/ (deleted and rebuilt on every run).

Builds a synthetic matrix dir in the night layout (matrix.json, runs/<HHMM>-<arm>-rN/
run.json + game.log; env_set as a dict and params.env as a 'K=V' list, like Agent 8's
runner) with 3 good runs and 6 bad ones, runs check_dir() on it and compares each
run's verdict with the expected one.

Usage: python -B build/agent6/wnight/make_test_w9env.py
Exit:  0 every verdict as expected, 1 otherwise.
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w9_envcheck  # noqa: E402

ROOT = os.path.join(HERE, 'test-w9env')
STAMP = '[2026-11-23 00:00:01.000] [info] [gpu] [t1] '
INIT = STAMP + 'GPU wait back-off: ON (quantum {q} us, spin {s} us); stats {st}; GetData hook built.\n'
FILLER = STAMP + 'Toypad: pad 1 ready\n'


def env(q, s='30'):
    return {'LEGO_GPU_WAIT_BACKOFF_US': str(q), 'LEGO_GPU_WAIT_SPIN_US': str(s)}


# name: (env_set, params.env, game.log lines, expected verdict prefix / substring)
CASES = {
    '0001-q0-r1':   (env(0), env(0), [INIT.format(q=0, s=30, st='OFF')], 'OK'),
    '0002-cold-q125': (env(125), env(125), [INIT.format(q=125, s=30, st='OFF')], 'OK'),
    '0003-off-r1':  ({}, {}, [], 'OK'),
    '0004-q125-r1': (env(250), env(250), [INIT.format(q=250, s=30, st='OFF')], 'env_set'),
    '0005-q125-r2': (env(125), env(125), [INIT.format(q=250, s=30, st='OFF')], 'quantum 250 != env 125'),
    '0006-q0-r2':   (env(0), env(0), [INIT.format(q=0, s=30, st='OFF')] * 2, '2 back-off lines'),
    '0007-off-r2':  ({}, {}, [INIT.format(q=0, s=30, st='OFF')], '1 back-off lines (want 0)'),
    '0008-q0-r3':   (env(0), env(0), [INIT.format(q=0, s=30, st='OFF'),
                                      STAMP + "LEGO_GPU_WAIT_SPIN_US='x' is not a plain number\n"],
                     '"is not a plain number"'),
    '0009-off-r3':  ({'LEGO_GPU_WAIT_STATS': '1'}, {'LEGO_GPU_WAIT_STATS': '1'}, [], 'env_set'),
}


def main():
    if os.path.exists(w9_envcheck.HOLD):
        print('HOLD file present: not running.')
        return 3
    if os.path.isdir(ROOT):
        shutil.rmtree(ROOT)
    os.makedirs(os.path.join(ROOT, 'runs'))
    matrix = {'title': 'synthetic W9 test (make_test_w9env.py)', 'arms': [
        {'id': 'off', 'env': {}},
        {'id': 'q0', 'env': env(0)},
        {'id': 'q125', 'env': env(125)},
    ]}
    with open(os.path.join(ROOT, 'matrix.json'), 'w', encoding='utf-8') as f:
        json.dump(matrix, f, indent=1)
    for name, (env_set, penv, lines, _exp) in CASES.items():
        rd = os.path.join(ROOT, 'runs', name)
        os.makedirs(rd)
        rj = {'status': 'OK', 'env_set': env_set,
              'params': {'env': ['%s=%s' % kv for kv in penv.items()]}}
        # utf-8-sig on purpose: the real run.json files carry a BOM.
        with open(os.path.join(rd, 'run.json'), 'w', encoding='utf-8-sig') as f:
            json.dump(rj, f, indent=1)
        with open(os.path.join(rd, 'game.log'), 'w', encoding='utf-8') as f:
            f.write(FILLER)
            f.writelines(lines)
            f.write(FILLER)
    out = []
    bad = w9_envcheck.check_dir(ROOT, out.append)
    rows = {}
    for line in out:
        head = line.split(' ', 1)[0]
        if head in CASES:
            rows[head] = line
    fails = 0
    for name, case in CASES.items():
        exp = case[3]
        row = rows.get(name, '')
        verdict = row.split('  ')[-1].strip() if row else '(no row)'
        ok = (verdict == 'OK') if exp == 'OK' else (verdict.startswith('MISMATCH') and exp in verdict)
        fails += not ok
        print('%-4s %-15s expect %-34s got %s' % ('PASS' if ok else 'FAIL', name, exp, verdict))
    want_bad = sum(1 for c in CASES.values() if c[3] != 'OK')
    if bad != want_bad:
        fails += 1
        print('FAIL mismatch count %d, want %d' % (bad, want_bad))
    print('RESULT: %s (%d case(s) failed)' % ('PASS' if not fails else 'FAIL', fails))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())

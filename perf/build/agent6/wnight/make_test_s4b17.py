"""Task #19 (Agent 6): build the W9 expect-file test folder build/agent6/wnight/test-s4b17 from Agent 3's
devoff4b functional runs. It copies only game*.log, run.json and sys.csv; build/agent3 is read, never written.
Usage: python -B build/agent6/wnight/make_test_s4b17.py
"""
import glob
import json
import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SRC = os.path.join(ROOT, 'build', 'agent3', 'runs')
DST = os.path.join(ROOT, 'build', 'agent6', 'wnight', 'test-s4b17')
BIN = 'build/agent2/devoff4b-bin'
RUNS = [  # (Agent 3 run dir, test run dir; the arm is the part after the 4-digit prefix)
    ('20261122-223103-s4b-17-gw-p1', '2231-p1-r1'),
    ('20261122-220947-s4b-18-gw-q250', '2209-q250s-r1'),
    ('20261122-205356-s4b-01-off', '2053-off-r1'),
]


# --neg: a negative test. The same logs under the wrong W9 arm names must FAIL: s4b18 (Q 250, stats ON) as q250
# (W9's q250 is stats OFF) and s4b17 (back-off OFF, stats ON) as q0 (ON, quantum 0, stats OFF).
RUNS_NEG = [
    ('20261122-205356-s4b-01-off', '2053-off-r1'),
    ('20261122-220947-s4b-18-gw-q250', '2209-q250-r1'),
    ('20261122-223103-s4b-17-gw-p1', '2231-q0-r1'),
]


def main():
    global DST, RUNS
    if '--neg' in sys.argv[1:]:
        DST, RUNS = DST + '-neg', RUNS_NEG
    assert os.path.normpath(DST).startswith(os.path.normpath(os.path.join(ROOT, 'build', 'agent6', 'wnight')))
    if os.path.isdir(DST):
        shutil.rmtree(DST)
    os.makedirs(os.path.join(DST, 'runs'))
    for src, dst in RUNS:
        s, d = os.path.join(SRC, src), os.path.join(DST, 'runs', dst)
        os.makedirs(d)
        files = sorted(glob.glob(os.path.join(s, 'game*.log')))
        files += [os.path.join(s, x) for x in ('run.json', 'sys.csv') if os.path.exists(os.path.join(s, x))]
        nbytes = 0
        for f in files:
            shutil.copy2(f, d)
            nbytes += os.path.getsize(f)
        rj = {}
        if os.path.exists(os.path.join(s, 'run.json')):
            with open(os.path.join(s, 'run.json'), encoding='utf-8-sig') as fh:
                rj = json.load(fh)
        init, stats, sleep_fail = [], 0, set()
        for lf in sorted(glob.glob(os.path.join(d, 'game*.log'))):
            with open(lf, encoding='utf-8', errors='replace') as fh:
                for line in fh:
                    if 'GPU wait back-off' in line:
                        init.append(line.strip()[line.find('GPU wait'):][:120])
                    if 'GPU wait stats (5 s):' in line:
                        stats += 1
                        i = line.find('sleep_fail ')
                        if i >= 0:
                            sleep_fail.add(line[i + 11:].split()[0].strip(',;.'))
        print('%s <- %s: %d files, %d bytes' % (dst, src, len(files), nbytes))
        print('    run.json keys:', sorted(rj.keys()))
        print('    env:', json.dumps(rj.get('env')), 'env_set:', json.dumps(rj.get('env_set')),
              'cvars:', json.dumps(rj.get('cvars')), 'status:', rj.get('status'), 'bin:', rj.get('bin_dir') or rj.get('bin'))
        print('    init lines (%d):' % len(init), init[:3])
        print('    STATS lines: %d, sleep_fail values: %s' % (stats, sorted(sleep_fail)))
    matrix = {
        'title': 'TEST ONLY (Agent 6, task #19): expect-w9.json on Agent 3 devoff4b functional runs s4b17, s4b18, s4b-01',
        'reference': 'off',
        'notes': [
            'Not a timed window. Arms p1 and q250s are gate-only arms (not W9 arms); off is s4b-01-off (menus route).',
            "cvars [] and env {} for every arm, because Agent 3's run.json records cvars {} and keeps the env under "
            "'env', not 'env_set', so the kit reads {} for both. The real W9 arms are in bench/agent8/run/matrix-window9.json.",
        ],
        'arms': [
            {'id': 'off', 'bin': BIN, 'cvars': [], 'env': {}, 'note': 's4b-01-off: no LEGO_GPU_WAIT_* key'},
            {'id': 'p1', 'bin': BIN, 'cvars': [], 'env': {}, 'note': 's4b17: LEGO_GPU_WAIT_STATS=1 (real env)'},
            {'id': 'q250s', 'bin': BIN, 'cvars': [], 'env': {}, 'note': 's4b18: BACKOFF_US=250 + STATS=1 (real env)'},
        ],
    }
    if RUNS is RUNS_NEG:
        matrix['title'] = 'NEGATIVE TEST ONLY (Agent 6, task #19): s4b18 labelled q250 and s4b17 labelled q0 must FAIL'
        matrix['arms'] = [
            {'id': 'off', 'bin': BIN, 'cvars': [], 'env': {}, 'note': 's4b-01-off: no LEGO_GPU_WAIT_* key'},
            {'id': 'q250', 'bin': BIN, 'cvars': [], 'env': {}, 'note': 'really s4b18 (Q 250, stats ON)'},
            {'id': 'q0', 'bin': BIN, 'cvars': [], 'env': {}, 'note': 'really s4b17 (back-off OFF, stats ON)'},
        ]
    with open(os.path.join(DST, 'matrix.json'), 'w', encoding='utf-8') as fh:
        json.dump(matrix, fh, indent=1)
    print('wrote', os.path.relpath(DST, ROOT))


if __name__ == '__main__':
    main()

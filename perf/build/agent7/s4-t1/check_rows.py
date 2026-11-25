#!/usr/bin/env python3
"""check_rows.py - static checks of the S4-T1 (#21) row files (Agent 7, task #17).

Reads only; writes only check_rows.out.txt beside this file. Stdlib only, no game, no build.
Run (Below Normal):  python -B build/agent7/s4-t1/check_rows.py
Exit 0 = every check passed.

Checks
  * the 4 matrices (F1, F3, W8b draft, W1) parse and use only run-matrix.ps1's fields (lists parsed live from run-matrix.ps1 L49-55);
  * timing fields and cvars equal bench/agent4/matrix-native-threaded.json; frames=perf; thread-cpu driver;
  * each arm's env equals its intended set (n0 / th2 / th3 from the template's own arms, + CHAIN_PRIORITY=3,
    + QUERY_TRACE_FROM=0 for F3); exactly one ref arm = "reference";
  * W8b uses only the 11 keys of build/agent8/w8w9/ENV-KEYS-F1.txt; no TIMING / trace keys anywhere;
  * queue rows parse, use only run-matrix parameters, need ready-s4t1 + ready-later + their matrix copy;
    run count and minutes per row, against est;
  * SHA256SUMS.txt matches the staged files, and before/ still equals the S4b sources (snap1).
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(HERE, 'check_rows.out.txt')
SNAP = 'build/agent2/snap1/DimensionsRecomp/rexlego/src/gpu_native'  # CMAKE_HOME_DIRECTORY of snap1-on + src
S_FULL, S_QUICK = 158, 150  # s/run: full = window-3 observed; quick = Agent 3's g3q basis (600 s / 4 runs)

out, fails = [], []


def log(s=''):
    out.append(s)
    print(s)


def check(cond, msg):
    log(('PASS ' if cond else 'FAIL ') + msg)
    if not cond:
        fails.append(msg)


def rd(rel):
    with open(os.path.join(ROOT, rel), 'rb') as f:
        return f.read()


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


# ---- harness field lists, parsed live -------------------------------------------------------------
rm = rd('bench/agent8/run/run-matrix.ps1').decode('utf-8', 'replace')


def ps_list(name):
    m = re.search(r'\$' + name + r'\s*=\s*@\((.*?)\)', rm, re.S)
    return re.findall(r"'([^']+)'", m.group(1)) if m else []


TOP, ARMK, QUICKK = ps_list('TopKeys'), ps_list('ArmKeys'), ps_list('QuickKeys')
head = rm.split('$ErrorActionPreference')[0]
PARAMS = {p.lower() for p in re.findall(r'\[(?:string\[\]|string|int|switch)\]\$(\w+)', head)}
log('run-matrix fields: top %d, arm %d, quick %d; params: %s' % (len(TOP), len(ARMK), len(QUICKK), ' '.join(sorted(PARAMS))))
check(len(TOP) >= 15 and len(ARMK) >= 12 and 'only' in PARAMS and 'nocold' in PARAMS, 'run-matrix lists parsed')

f1txt = rd('build/agent8/w8w9/ENV-KEYS-F1.txt').decode('utf-8', 'replace')
m = re.search(r'\$AllowedEnv\s*=\s*@\((.*?)\)', f1txt, re.S)
F1 = re.findall(r"'([^']+)'", m.group(1)) if m else []
check(len(F1) == 11 and 'LEGO_NATIVE_CHAIN_PRIORITY' in F1, 'ENV-KEYS-F1 list: %d keys, CHAIN_PRIORITY in it' % len(F1))

# ---- template and intended env sets ---------------------------------------------------------------
tpl = json.loads(rd('bench/agent4/matrix-native-threaded.json'))
tarms = {a['id']: a for a in tpl['arms']}
CVARS = tarms['n0']['cvars']
N0 = dict(tarms['n0']['env'])
TH2 = dict(tarms['th2']['env'])
TH3 = dict(tarms['th3']['env'])
check(N0 == {'LEGO_NATIVE_FRAME_METRICS': '<run>\\native-frames.csv'}, 'template n0 env = FRAME_METRICS only')
check(TH3 == dict(N0, LEGO_NATIVE_THREADED='1', LEGO_NATIVE_PREPARE_THREADS='2', LEGO_NATIVE_FULL_DRAW_PREPARATION='1'),
      'template th3 env = n0 + THREADED=1, PREPARE_THREADS=2, FULL_DRAW_PREPARATION=1')
check(TH2 == dict(N0, LEGO_NATIVE_THREADED='1', LEGO_NATIVE_PREPARE_THREADS='2', LEGO_NATIVE_SNAPSHOT_STATE='1'),
      'template th2 env = n0 + THREADED=1, PREPARE_THREADS=2, SNAPSHOT_STATE=1')
CP3 = {'LEGO_NATIVE_CHAIN_PRIORITY': '3'}
QT = {'LEGO_NATIVE_QUERY_TRACE_FROM': '0'}
S4T1, OLD = '<NATIVE4B-S4T1>', '<NATIVE4B>'
FORBID = {'LEGO_NATIVE_TIMING', 'LEGO_NATIVE_STATE_CALLS', 'LEGO_NATIVE_PARALLEL_DRAWS', 'LEGO_NATIVE_TRACE_DIR',
          'LEGO_DUMP_MISSING_SHADERS', 'LEGO_SAMPLE_PROFILE', 'LEGO_SAMPLE_PROFILE_TRIGGER', 'LEGO_NATIVE_SNAPSHOT_TRACE'}
SAME_TOP = ['warmup_s', 'warmup_from', 'measure_s', 'settle_s', 'cooldown_s', 'boot_timeout_s', 'close_timeout_s',
            'menu_s', 'order', 'sys_csv', 'quick']


def u(*ds):
    r = {}
    for d in ds:
        r.update(d)
    return r


EXPECT = {
    'matrix-s4t1-f1.json': ('n0', False, 2, [('n0', S4T1, N0, 2), ('th3old', OLD, TH3, 2), ('th3', S4T1, TH3, 2),
                                             ('th3cp3', S4T1, u(TH3, CP3), 2), ('th2', S4T1, TH2, 1),
                                             ('th2cp3', S4T1, u(TH2, CP3), 1)]),
    'matrix-s4t1-f3.json': ('n0q', False, 2, [('n0q', S4T1, u(N0, QT), 2), ('th3q', S4T1, u(TH3, QT), 2),
                                              ('th3cp3q', S4T1, u(TH3, CP3, QT), 1)]),
    'matrix-w8b-draft.json': ('n0', True, 4, [('n0', S4T1, N0, 4), ('th3', S4T1, TH3, 4), ('th3cp', S4T1, u(TH3, CP3), 4)]),
    'matrix-s4t1-w1.json': ('n0', False, 1, [('n0', S4T1, N0, 1), ('th3', S4T1, TH3, 1), ('th3cp', S4T1, u(TH3, CP3), 1)]),
}
MX = {}
placeholders = {}
for name, (ref, cold, rep, arms) in EXPECT.items():
    log('')
    log('== ' + name)
    raw = open(os.path.join(HERE, name), 'rb').read()
    check(not raw.startswith(b'\xef\xbb\xbf') and raw.decode('ascii', 'strict') is not None, 'ASCII, no BOM')
    mx = json.loads(raw)
    MX[name] = mx
    check(set(mx) <= set(TOP), 'top-level fields allowed: ' + ', '.join(sorted(set(mx) - set(TOP))) if set(mx) - set(TOP) else 'top-level fields allowed')
    check(set(mx.get('quick', {})) <= set(QUICKK), 'quick fields allowed')
    check(all(mx.get(k) == tpl.get(k) for k in SAME_TOP), 'timing fields = template (%s)' % ', '.join(SAME_TOP))
    check(mx['reference'] == ref and mx['cold_run'] is cold and mx['repeats'] == rep,
          'reference=%s cold_run=%s repeats=%d' % (ref, cold, rep))
    refs = [a['id'] for a in mx['arms'] if a.get('ref')]
    check(refs == [ref], 'exactly one ref arm = reference (%s)' % refs)
    check([a['id'] for a in mx['arms']] == [a[0] for a in arms], 'arm ids/order: ' + ' '.join(a['id'] for a in mx['arms']))
    for a, (aid, abin, aenv, arep) in zip(mx['arms'], arms):
        bad = set(a) - set(ARMK)
        ok = (not bad and a['bin'] == abin and a['env'] == aenv and a['repeats'] == arep and a['cvars'] == CVARS
              and a.get('frames') == 'perf' and a.get('driver') == 'drivers/thread-cpu.ps1' and not (set(a['env']) & FORBID))
        extra = sorted(set(a['env']) - set(N0))
        check(ok, 'arm %-8s bin %-15s x%d env n0+%s%s' % (aid, a['bin'], a['repeats'], extra, (' BAD FIELDS %s' % bad) if bad else ''))
    for tok in re.findall(r'<[A-Z0-9][A-Z0-9-]*>', raw.decode('ascii')):
        placeholders.setdefault(tok, set()).add(name)
    if name in ('matrix-w8b-draft.json', 'matrix-s4t1-w1.json'):
        tag = 'W8b' if name == 'matrix-w8b-draft.json' else 'W1'
        keys = sorted({k for a in mx['arms'] for k in a['env']})
        check(set(keys) <= set(F1), tag + ' env keys all in ENV-KEYS-F1: ' + ', '.join(keys))
        envs = {a['id']: a['env'] for a in mx['arms']}
        check(envs['th3'] == u(envs['n0'], {'LEGO_NATIVE_THREADED': '1', 'LEGO_NATIVE_PREPARE_THREADS': '2',
                                            'LEGO_NATIVE_FULL_DRAW_PREPARATION': '1'}) and envs['th3cp'] == u(envs['th3'], CP3),
              tag + ' th3 = n0 + 3 keys; th3cp = th3 + CHAIN_PRIORITY=3 (ENV-KEYS-F1 th/thcp)')
    if name == 'matrix-s4t1-w1.json' and 'matrix-w8b-draft.json' in MX:
        w8 = MX['matrix-w8b-draft.json']
        same = all(a['env'] == b['env'] and a['cvars'] == b['cvars'] and a['bin'] == b['bin'] and a['id'] == b['id']
                   for a, b in zip(mx['arms'], w8['arms'])) and len(mx['arms']) == len(w8['arms'])
        check(same, 'W1 arms = W8b arms (ids, bin, env, cvars); only repeats/cold differ')


def runs_for(mx, margs):
    only, repeats, nocold, quick = [], 0, False, False
    i = 0
    while i < len(margs):
        t = margs[i].lower()
        if t == '-only':
            only = [x for x in re.split(r'[,;\s]+', margs[i + 1]) if x]
            i += 1
        elif t == '-repeats':
            repeats = int(margs[i + 1])
            i += 1
        elif t == '-nocold':
            nocold = True
        elif t == '-quick':
            quick = True
        i += 1
    arms = [a for a in mx['arms'] if not only or a['id'] in only]
    n = sum(repeats if repeats > 0 else a.get('repeats', mx.get('repeats', 3)) for a in arms)
    cold = 0 if nocold or not mx.get('cold_run') else len({a['bin'] for a in arms})
    return n, cold, quick


log('')
log('== queue-s4t1.jsonl')
rows = []
for ln in open(os.path.join(HERE, 'queue-s4t1.jsonl'), encoding='ascii').read().splitlines():
    if not ln.strip() or ln.startswith('#'):
        continue
    rows.append(json.loads(ln))
check([r['id'] for r in rows] == ['s4t1-f1', 's4t1-f3', 's4t1-w1'], 'row ids: ' + ' '.join(r['id'] for r in rows))
total_min = 0.0
for r in rows:
    base = os.path.basename(r['matrix'])
    copy = r['matrix']
    flags = [t for t in r['matrix_args'] if t.startswith('-')]
    ok = (base in MX and copy.startswith('build\\agent3\\s4b\\s4t1\\') and copy in r['needs']
          and 'build\\agent3\\s4b\\ready-s4t1' in r['needs'] and 'build\\agent3\\s4b\\ready-later' in r['needs']
          and all(t[1:].lower() in PARAMS for t in flags) and r.get('args') == [])
    n, cold, quick = runs_for(MX[base], r['matrix_args'])
    sec = (n + cold) * (S_QUICK if quick else S_FULL)
    total_min += sec / 60
    check(ok and r['est'] >= sec, '%s: %s %s -> %d scored + %d cold runs, %s, about %.0f min (est %d s >= %d s)'
          % (r['id'], base, ' '.join(r['matrix_args']), n, cold, 'quick' if quick else 'full', sec / 60, r['est'], sec))
log('queue total about %.0f min of runs (plus checks)' % total_min)
w8 = MX['matrix-w8b-draft.json']
n, cold, quick = runs_for(w8, [])
check(n + cold == 13, 'W8b full window: %d scored + %d cold = %d runs, about %.0f min at %d s/run (planner 142 s: %.0f min)'
      % (n, cold, n + cold, (n + cold) * S_FULL / 60, S_FULL, (n + cold) * 142 / 60))

log('')
log('== placeholders (replace in a copy; a bin dir without MANIFEST.txt skips its arms)')
for tok, files in sorted(placeholders.items()):
    log('  %-16s %s' % (tok, ', '.join(sorted(files))))
check(set(placeholders) == {S4T1, OLD}, 'only the two bin placeholders are used')

log('')
log('== staged diff: SHA256SUMS.txt vs files, before/ vs S4b sources')
sums = {}
for ln in open(os.path.join(HERE, 'SHA256SUMS.txt'), encoding='ascii').read().splitlines():
    mm = re.search(r'\b([0-9A-Fa-f]{64})\b\s+\*?(\S+)', ln)
    if mm:
        sums[mm.group(2).replace('\\', '/')] = mm.group(1).upper()
check(len(sums) >= 7, 'SHA256SUMS.txt entries: %d' % len(sums))
for rel, h in sorted(sums.items()):
    p = os.path.join(HERE, rel)
    if os.path.isfile(p):
        check(sha(open(p, 'rb').read()) == h, 'sha256 %s %s...' % (rel, h[:16]))
    else:
        check(False, 'listed file missing: ' + rel)
for f in ('native_worker.cpp', 'native_recording.cpp', 'native_preparation.h'):
    b = open(os.path.join(HERE, 'before', 'src', 'gpu_native', f), 'rb').read()
    s = rd(SNAP + '/' + f)
    check(b == s, 'before/%s == %s/%s (%s...)' % (f, SNAP, f, sha(s)[:16]))

log('')
log('RESULT: %s (%d failed)' % ('ALL CHECKS PASS' if not fails else 'FAIL', len(fails)))
for f in fails:
    log('  FAILED: ' + f)
with open(OUT, 'w', encoding='ascii', newline='\n') as fh:
    fh.write('\n'.join(out) + '\n')
sys.exit(0 if not fails else 1)

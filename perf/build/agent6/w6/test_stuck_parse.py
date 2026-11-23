#!/usr/bin/env python3
"""Agent 6, task #16: unit check of w6_kit's STUCK-LOCK parser and H1/H2 site tagging on the 3 real hang logs
(Agent 3's gate A, s4b-24 and s4b-20 runs; read-only). Each run's own legodimensions.map is used, else devoff4b's.
  python -B build/agent6/w6/test_stuck_parse.py      exit 0 = every episode parsed and tagged H1
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w6_kit as k  # noqa: E402

RUNS = os.path.join(k.ROOT, 'build', 'agent3', 'runs')
FALLBACK_MAP = os.path.join(k.ROOT, 'build', 'agent2', 'devoff4b-bin', 'legodimensions.map')
CASES = [('gate A', '20261122-210906-w6-gateA-p2fcv-level'),
         ('s4b-24', '20261122-220520-s4b-24-w6-c1'),
         ('s4b-20', '20261122-221447-s4b-20-m1-level')]
FIELDS = ('ts', 'cs', 'after_s', 'owner_tid', 'owner_lr', 'owner_callers', 'waiter_lr', 'pm4', 'dump')

bad = 0
starts = []
for name, d in CASES:
    rd = os.path.join(RUNS, d)
    mp = os.path.join(rd, 'legodimensions.map')
    if not os.path.exists(mp):
        mp = FALLBACK_MAP
    starts = k.map_funcs(mp)
    r = k.scan_log(rd, list(k.EP_TEXTS))
    eps = r['episodes']
    print('== %s: %s; map %s (%d funcs); episodes %d; episode lines %s; levels %s; other error/critical %d'
          % (name, d, os.path.relpath(mp, k.ROOT), len(starts), len(eps), dict(r['ep_lines']), dict(r['levels']),
             r['other_err_n']))
    if len(eps) != 1:
        bad += 1
        print('  MISMATCH: want exactly 1 episode')
    for e in eps:
        lr = int(e['owner_lr'], 16) if e['owner_lr'] else None
        site, f = k.site_of(lr, starts)
        missing = [x for x in FIELDS if e.get(x) in (None, '', [])]
        where = ('sub_%08X+0x%X' % (f, lr - f)) if (f is not None and lr is not None) else str(f)
        ok = site == 'H1' and not missing and e['lines'] == 6
        bad += 0 if ok else 1
        print('  %s  site %s (%s)  lines %d  %s' % ('OK' if ok else 'MISMATCH', site, where, e['lines'],
                                                  ('missing ' + ','.join(missing)) if missing else 'all fields'))
        for x in FIELDS:
            print('    %-13s %s' % (x, e.get(x)))
h2f = k.func_of(starts, k.H2_ADDR)
print('H2 address 83FB09F0 is in %s' % (('sub_%08X' % h2f) if h2f else 'NO FUNCTION'))
if not h2f:
    bad += 1
nomap = [k.site_of(0x83FAF188, [])[0], k.site_of(0x83FAF200, [])[0], k.site_of(0x83FBF868, [])[0],
         k.site_of(0x83FB09F0, [])[0], k.site_of(0x82000000, [])[0]]
print('no-map fallback (83FAF188, 83FAF200, 83FBF868, 83FB09F0, 82000000): %s' % nomap)
if nomap != ['H1', 'H1', 'H1', 'H2', 'other']:
    bad += 1
print('RESULT %s' % ('PASS' if not bad else 'FAIL (%d)' % bad))
sys.exit(1 if bad else 0)

#!/usr/bin/env python3
"""M10: per-run game.log proof lines for the WC windows (plan notes of matrix-windowC.json). Read-only."""
import csv, os, sys

sys.dont_write_bytecode = True
P = {
    'c1on': 'C1 keep-watch: on (with physical_protect_hold_global_lock)',
    'c1first': 'C1 keep-watch: first kept protect at',
    'c1verify': 'C1 verify: on',
    'timer1ms': 'Host timer resolution set to 1 ms (background opt-out on)',
    'precise': 'TimerQueue: precise wait (timer_queue_precise_wait)',
    'backoff': 'GPU wait back-off: ON (quantum 500 us, spin 30 us); stats OFF; GetData hook built.',
    'anyback': 'GPU wait back-off',
    'bad1': 'Recovered stale physical page protection',
    'bad2': 'Unhandled guest physical write fault',
    'bad3': 'PhysicalHeap::Protect failed',
    'bad4': 'is not a plain number',
}
EXP = {
    's0': dict(c1on=0, c1first=0, c1verify=0, timer1ms=0, precise=0, backoff=0),
    'c1np': dict(c1on='>0', c1first='>0', c1verify=0, timer1ms=0, precise=0, backoff=0),
    'p2fc': dict(c1on='>0', c1first='>0', c1verify=0, timer1ms=0, precise=0, backoff=0),
    'win3': dict(c1on='>0', c1first='>0', c1verify=0, timer1ms='>0', precise=1, backoff=1),
}
bad_total = 0
for d in sys.argv[1:]:
    with open(os.path.join(d, 'results.csv'), encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            rd = r['run_dir']; arm = r['arm']
            cnt = {k: 0 for k in P}
            with open(os.path.join(rd, 'game.log'), encoding='utf-8', errors='replace') as g:
                for ln in g:
                    for k, s in P.items():
                        if s in ln:
                            cnt[k] += 1
            prob = []
            for k, e in EXP[arm].items():
                ok = (cnt[k] > 0) if e == '>0' else (cnt[k] == e)
                if not ok:
                    prob.append('%s=%d(exp %s)' % (k, cnt[k], e))
            if arm != 'win3' and cnt['anyback']:
                prob.append('anyback=%d' % cnt['anyback'])
            for k in ('bad1', 'bad2', 'bad3', 'bad4'):
                if cnt[k]:
                    prob.append('%s=%d' % (k, cnt[k]))
            bad_total += bool(prob)
            print('%s %-16s %-5s %s' % (os.path.basename(d), os.path.basename(rd), arm, 'OK' if not prob else 'BAD ' + ' '.join(prob)))
print('runs with problems:', bad_total)

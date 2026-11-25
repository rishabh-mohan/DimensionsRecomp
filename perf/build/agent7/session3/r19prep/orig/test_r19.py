#!/usr/bin/env python3
"""test_r19.py - selftest for r19_gate.py and check_queue_r19.py on synthetic data (M7, S3T-7 A).

Run (Below Normal, from the workspace root):  python -B build/agent7/session3/test_r19.py
Prints one line per case and 'SELFTEST PASS n/n' or 'SELFTEST FAIL k/n'. Writes nothing.
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import r19_gate as g  # noqa: E402
import check_queue_r19 as q  # noqa: E402

T = '[2026-11-26 10:%02d:%02d.000] [%s] [gpu] [t100] %s'
EXIT = '[2026-11-26 10:59:00.000] [info] [core] [t1] Title terminated; hard-exiting process.'
WD = '[2026-11-26 10:59:03.000] [warning] [core] [t1] Shutdown wedged past the close request; hard-exiting.'
_t = [0]


def L(msg, lvl='info'):
    _t[0] += 10
    return T % (_t[0] // 60 % 60, _t[0] % 60, lvl, msg)


def sinit(n=64):
    return L('d3d12_submit_split_kb: splitting submissions at %d KB of deferred commands' % n)


def ainit():
    return L('d3d12_async_submit: submitting splits on the submit thread (3 slots)')


def actr(fr, sub, ch, qm=2, fw=0, fwu=0, dw=None, dwu=None, wu=None):
    dw = fr if dw is None else dw
    return L('d3d12_async_submit: frame=%d submission=%d chunks=%d queued_max=%d full_waits=%d full_wait_us=%d '
             'drains_waited=%d drain_wait_us=%d worker_us=%d' % (fr, sub, ch, qm, fw, fwu, dw,
                                                                  dwu if dwu is not None else dw * 3,
                                                                  wu if wu is not None else ch * 40))


def sctr(fr, sub, sp, failed=0, hq=0, hs=0, hp=0):
    return L('d3d12_submit_split: frame=%d submission=%d splits=%d failed=%d held_query=%d held_scratch=%d '
             'held_pipelines=%d' % (fr, sub, sp, failed, hq, hs, hp))


BASE = [L('boot', 'info'), L('some other line')]


def on_log(hq=5, fw=0, qm=2, n=64, extra=None, drop_async=False, wd=False):
    lines = BASE + [sinit(n), ainit()]
    if not drop_async:
        lines += [actr(100, 300, 10, qm=qm, fw=fw), sctr(100, 300, 10, hq=hq),
                  actr(700, 2100, 60, qm=qm, fw=fw * 2), sctr(700, 2100, 60, hq=hq * 2)]
    lines += extra or []
    lines += [EXIT] + ([WD] if wd else [])
    return lines


CASES = []


def case(name, lines, row, want, n=None):
    CASES.append((name, lines, row, want, n))


# row a
case('a clean', BASE + [EXIT], 'a', 'PASS')
case('a split init present', BASE + [sinit(), EXIT], 'a', 'FAIL')
case('a async warn present', BASE + [L(g.WARN_OFF, 'warning'), EXIT], 'a', 'FAIL')
case('a watchdog off row = note only', BASE + [EXIT, WD], 'a', 'PASS')
# row b
case('b one warn', BASE + [L(g.WARN_OFF, 'warning'), EXIT], 'b', 'PASS')
case('b no warn', BASE + [EXIT], 'b', 'FAIL')
case('b two warns', BASE + [L(g.WARN_OFF, 'warning'), L(g.WARN_OFF, 'warning'), EXIT], 'b', 'FAIL')
case('b warn at info level', BASE + [L(g.WARN_OFF, 'info'), EXIT], 'b', 'FAIL')
case('b warn + async init', BASE + [L(g.WARN_OFF, 'warning'), ainit(), EXIT], 'b', 'FAIL')
case('b warn + split init', BASE + [L(g.WARN_OFF, 'warning'), sinit(), EXIT], 'b', 'FAIL')
# row i
case('i splits', BASE + [sinit(64), sctr(100, 300, 5), sctr(700, 2100, 40), EXIT], 'i', 'PASS', '64')
case('i wrong N in init', BASE + [sinit(32), sctr(100, 300, 5), EXIT], 'i', 'FAIL', '64')
case('i failed > 0', BASE + [sinit(64), sctr(100, 300, 5, failed=1), EXIT], 'i', 'FAIL', '64')
case('i async line', BASE + [sinit(64), ainit(), sctr(100, 300, 5), EXIT], 'i', 'FAIL', '64')
case('i no split line', BASE + [sinit(64), EXIT], 'i', 'INCOMPLETE', '64')
case('i split counter decreases', BASE + [sinit(64), sctr(100, 300, 9), sctr(700, 2100, 4), EXIT], 'i', 'FAIL', '64')
case('i two inits', BASE + [sinit(64), sinit(64), sctr(100, 300, 5), EXIT], 'i', 'FAIL', '64')
# ON rows
case('c good (held_query 0 not gating)', on_log(hq=0), 'c', 'PASS', '64')
case('g good', on_log(hq=0), 'g', 'PASS', '64')
case('f good', on_log(hq=3), 'f', 'PASS', '64')
case('c queued_max 4', on_log(qm=4), 'c', 'FAIL', '64')
case('c no async init', [l for l in on_log() if 'submit thread' not in l], 'c', 'FAIL', '64')
case('c staying-off warn', on_log(extra=[L(g.WARN_OFF, 'warning')]), 'c', 'FAIL', '64')
case('c create-thread error', on_log(extra=[L('d3d12_async_submit: failed to create the submit thread, staying off',
                                                'error')]), 'c', 'FAIL', '64')
case('c split failed=1', on_log(extra=[sctr(800, 2400, 70, failed=1, hq=10)]), 'c', 'FAIL', '64')
case('c async counter decreases', on_log(extra=[actr(800, 2400, 50)]), 'c', 'FAIL', '64')
case('c wrong N', on_log(n=32), 'c', 'FAIL', '64')
case('d no split due (fallback A)', on_log(drop_async=True), 'd', 'INCOMPLETE', '64')
case('d good', on_log(hq=0), 'd', 'PASS', '64')
case('c watchdog -> FLAG', on_log(hq=0, wd=True), 'c', 'FLAG', '64')
case('j good fifo filled', on_log(fw=3, n=16), 'j', 'PASS', '16')
case('j fifo never filled', on_log(fw=0, n=16), 'j', 'INCOMPLETE', '16')
case('j queued_max 4', on_log(fw=3, qm=4, n=16), 'j', 'FAIL', '16')
case('e good', on_log(hq=5), 'e', 'PASS', '64')
case('e no queries', on_log(hq=0), 'e', 'FAIL', '64')
case('e no split at all', on_log(drop_async=True), 'e', 'INCOMPLETE', '64')
case('e watchdog -> FLAG', on_log(hq=5, wd=True), 'e', 'FLAG', '64')


def verdict(lines, row, n):
    res, flags = g.gate(lines, row, n=n)
    return 'FAIL' if res.fails else ('INCOMPLETE' if res.incomplete else ('FLAG' if flags else 'PASS')), res


def queue_cases():
    rows, errs = q.load_rows(os.path.join(HERE, 'queue-r19.jsonl'))
    out = []

    def nfail(rs):
        return sum(1 for t, _ in q.check(rs, set()) if t == 'FAIL')

    out.append(('queue as written: 0 FAIL', not errs and nfail(rows) == 0))

    def mut(fn):
        rs = copy.deepcopy(rows)
        fn(rs)
        return nfail(rs) > 0

    def find(rs, rid):
        return [r for _, r in rs if r['id'] == rid][0]

    def swap_cg(rs):
        ic = [k for k, (_, r) in enumerate(rs) if r['id'] == 'r19c'][0]
        ig = [k for k, (_, r) in enumerate(rs) if r['id'] == 'r19g'][0]
        rs[ic], rs[ig] = rs[ig], rs[ic]
    out.append(('mut: c and g swapped -> FAIL', mut(swap_cg)))
    out.append(('mut: go-r19on dropped from c -> FAIL', mut(
        lambda rs: find(rs, 'r19c')['needs'].remove('build\\agent3\\session3\\go-r19on'))))
    out.append(('mut: go-r19on added to i -> FAIL', mut(
        lambda rs: find(rs, 'r19i')['needs'].append('build\\agent3\\session3\\go-r19on'))))
    out.append(('mut: chain marker of b wrong -> FAIL', mut(
        lambda rs: find(rs, 'r19b')['needs'].__setitem__(2, 'build\\agent3\\session3\\r19-ok-i'))))

    def add_cvar(rid, cv):
        def f(rs):
            a = find(rs, rid)['args']
            k = a.index('-Cvar')
            a[k + 1] += ';' + cv
        return f
    out.append(('mut: #33 cvar on e -> FAIL', mut(add_cvar('r19e', 'd3d12_pipeline_creation_no_wait=true'))))
    out.append(('mut: res scaling on c -> FAIL', mut(add_cvar('r19c', 'draw_resolution_scale_x=2'))))

    def ctr_bin(rs):
        a = find(rs, 'r19f')['args']
        a[a.index('-BinDir') + 1] = 'build\\agent2\\devoff4b-ctr-bin'
    out.append(('mut: ctr bin on f -> FAIL', mut(ctr_bin)))
    out.append(('mut: ready-N dropped from d -> FAIL', mut(
        lambda rs: find(rs, 'r19d')['needs'].remove('build\\agent3\\s4b\\ready-N'))))
    out.append(('mut: -Env added to j -> FAIL', mut(
        lambda rs: find(rs, 'r19j')['args'].extend(['-Env', 'LEGO_GPU_NATIVE=1']))))
    out.append(('mut: async on ref r19r10 -> FAIL', mut(add_cvar('r19r10', 'd3d12_async_submit=true'))))
    out.append(('mut: duplicate id -> FAIL', mut(lambda rs: find(rs, 'r19b').__setitem__('id', 'r19a'))))
    out.append(('mut: existing id clash -> FAIL',
                sum(1 for t, _ in q.check(rows, {'r19e'}) if t == 'FAIL') > 0))
    return out


def main():
    n = ok = 0
    for name, lines, row, want, nkb in CASES:
        got, res = verdict(lines, row, nkb)
        n += 1
        good = got == want
        ok += good
        print('%s  gate %-38s row %s want %-10s got %s' % ('ok  ' if good else 'BAD ', name, row, want, got))
        if not good:
            for ln in res.lines:
                print('        ' + ln)
    for name, good in queue_cases():
        n += 1
        ok += bool(good)
        print('%s  queue %s' % ('ok  ' if good else 'BAD ', name))
    print('SELFTEST %s %d/%d' % ('PASS' if ok == n else 'FAIL', ok, n))
    return 0 if ok == n else 1


if __name__ == '__main__':
    sys.exit(main())

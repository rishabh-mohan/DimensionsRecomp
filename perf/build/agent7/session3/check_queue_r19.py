#!/usr/bin/env python3
"""check_queue_r19.py - static check of queue-r19.jsonl against ROWS-R19.md and M10's #19 conditions (M7, S3T-7 A).

Read-only, stdlib only. Run from the workspace root (Below Normal):
  python -B build/agent7/session3/check_queue_r19.py [queue file] [--ws WS]
Exit 0 ALL CHECKS PASS, 1 any check failed.

Checks
  Q1 every non-comment line is a JSON object with id, est, needs (list), args (list, even length after -BinDir..);
     ids unique, tags unique; no id already in build/agent3/s4b/queue.jsonl or queue-state.jsonl (done ids can't
     re-run; s4b-queue.ps1 L121-132).
  Q2 #19 rows appear in M10's order a, b, i, c, g, j, d, f, e (r19-rating (b) 2); every ref row before every #19 row.
  Q3 #19 rows use -BinDir build\\agent2\\devoff4b-r19-bin (placeholder) and need ready-r19 and go-quiet; ref rows use
     build\\agent2\\devoff4b-bin and need ready-s4b-off and go-quiet.
  Q4 chain: #19 row k (k > a) needs r19-ok-<previous row>; ON rows (c g j d f e) need go-r19on; OFF rows don't.
  Q5 a row whose args contain <N> needs ready-N; a row that needs ready-N contains <N>; d3d12_debug=true needs ready-dbg.
  Q6 cvar sets match ROWS-R19.md section 2 exactly (per row), and refs match S4b rows 10/11/13/15/25.
  Q7 combination guard (S2): no d3d12_pipeline_creation_no_wait, no *resolution_scale*, no native_* cvar, no -Env,
     no ctr/native bin, d3d12_async_submit only on #19 rows.
  Q8 the -Seconds / -InputScript / -StatsWarmup / toypad of each #19 row equal those of its source S4b row shape.
Live chain (r19prep, M10 r19-rows-mp-rating C2): i16 and g16 are the 16 KB substitutes for i and g. File order is
  a, b, i, i16, c, g, g16, j, d, f, e; the r19-ok chain runs over M10's 9 slots (i16 fills slot i, g16 slot g), so Q2/Q4
  check the slots. M3 picks the path from the ref r19r10 by writing r19-pathN (r10 splits at N) or r19-path16 (C2 'no
  split'), never both:
  Q9 rows i, c, g, f need r19-pathN and have "unless": r19-path16; rows i16, g16 need r19-path16 and have "unless":
     r19-pathN (s4b-queue.ps1 L133-135 drops a row whose unless-file exists); no other row has a path marker or unless.
  Q10 with --expect-n K: build/agent3/s4b/ready-N line 1 == K (<N> stays a placeholder in the args, r19-rating (b) 6).
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WS_DEFAULT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
BIN19 = 'build\\agent2\\devoff4b-r19-bin'
BINREF = 'build\\agent2\\devoff4b-bin'
ORDER = ['a', 'b', 'i', 'i16', 'c', 'g', 'g16', 'j', 'd', 'f', 'e']
SLOT = {'i16': 'i', 'g16': 'g'}
SLOTS = ['a', 'b', 'i', 'c', 'g', 'j', 'd', 'f', 'e']
ON = {'c', 'g', 'g16', 'j', 'd', 'f', 'e'}
PATHN = {'i', 'c', 'g', 'f'}
PATH16 = {'i16', 'g16'}
M = 'build\\agent3\\s4b\\'
G = 'build\\agent3\\session3\\'
MENUS = 'harness\\routes\\b-gate-menus-long.txt'
LEVEL = 'build\\agent3\\toypad\\routes\\level-l.txt'
SPLITN = 'd3d12_submit_split_kb=<N>'
ASYNC = 'd3d12_async_submit=true'
# row -> (cvars set, seconds, input script, stats warmup, toypad)
SPEC19 = {
    'a': (set(), '420', MENUS, None, False),
    'b': ({ASYNC}, '90', None, None, False),
    'i': ({SPLITN}, '420', MENUS, None, False),
    'i16': ({'d3d12_submit_split_kb=16'}, '420', MENUS, None, False),
    'c': ({SPLITN, ASYNC}, '420', MENUS, None, False),
    'g': ({'d3d12_debug=true', SPLITN, ASYNC}, '420', MENUS, None, False),
    'g16': ({'d3d12_debug=true', 'd3d12_submit_split_kb=16', ASYNC}, '420', MENUS, None, False),
    'j': ({'d3d12_submit_split_kb=16', ASYNC}, '420', MENUS, None, False),
    'd': ({SPLITN, ASYNC, 'framerate_limit=0'}, '180', None, '20', False),
    'f': ({SPLITN, 'd3d12_readback_memexport=true', ASYNC}, '420', MENUS, None, False),
    'e': ({'framerate_limit=0', SPLITN, ASYNC}, '600', LEVEL, None, True),
}
SPECREF = {
    'r19r10': ({SPLITN}, '420', MENUS, None, False),
    'r19r11': ({'d3d12_submit_split_kb=16'}, '420', MENUS, None, False),
    'r19r13': ({SPLITN, 'd3d12_readback_memexport=true'}, '420', MENUS, None, False),
    'r19r15': ({'d3d12_debug=true', SPLITN}, '420', MENUS, None, False),
    'r19r25': ({SPLITN, 'framerate_limit=0'}, '180', None, '20', False),
}


def argmap(args):
    m = {}
    i = 0
    while i < len(args):
        k = args[i]
        if k == '-GpuLog':
            m[k] = True
            i += 1
            continue
        m[k] = args[i + 1] if i + 1 < len(args) else None
        i += 2
    return m


def load_rows(path):
    rows, errs = [], []
    with open(path, 'r', encoding='utf-8') as fh:
        for ln, line in enumerate(fh, 1):
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            try:
                rows.append((ln, json.loads(s)))
            except ValueError as e:
                errs.append('L%d not JSON: %s' % (ln, e))
    return rows, errs


def known_ids(ws):
    ids = set()
    for name in ('queue.jsonl', 'queue-state.jsonl'):
        p = os.path.join(ws, 'build', 'agent3', 's4b', name)
        if not os.path.isfile(p):
            continue
        with open(p, 'r', encoding='utf-8-sig', errors='replace') as fh:
            for line in fh:
                s = line.strip().lstrip('#').strip()
                if s.startswith('{'):
                    try:
                        ids.add(json.loads(s).get('id'))
                    except ValueError:
                        pass
    return ids


def check(rows, existing_ids):
    out = []

    def chk(cond, msg):
        out.append(('PASS' if cond else 'FAIL', msg))

    ids = [r.get('id') for _, r in rows]
    tags = [argmap(r.get('args', [])).get('-Tag') for _, r in rows]
    chk(len(ids) == len(set(ids)), 'Q1 ids unique (%d rows)' % len(ids))
    chk(len(tags) == len(set(tags)) and None not in tags, 'Q1 tags unique and present')
    clash = sorted(set(ids) & existing_ids)
    chk(not clash, 'Q1 no id already in queue.jsonl / queue-state.jsonl %s' % (clash or ''))
    for ln, r in rows:
        ok = isinstance(r.get('est'), int) and isinstance(r.get('needs'), list) and isinstance(r.get('args'), list)
        chk(ok, 'Q1 L%d %s has int est, list needs, list args' % (ln, r.get('id')))
    r19 = [(ln, r) for ln, r in rows if r.get('id', '').startswith('r19') and not r['id'].startswith('r19r')]
    refs = [(ln, r) for ln, r in rows if r.get('id', '').startswith('r19r')]
    order = [r['id'][3:] for _, r in r19]
    chk(order == ORDER, 'Q2 #19 row order %s == %s' % (','.join(order), ','.join(ORDER)))
    chk(sorted(r['id'] for _, r in refs) == sorted(SPECREF), 'Q2 ref rows %s' % sorted(r['id'] for _, r in refs))
    if refs and r19:
        chk(max(ln for ln, _ in refs) < min(ln for ln, _ in r19), 'Q2 every ref row before every #19 row')
    for ln, r in refs + r19:
        rid = r['id']
        is19 = not rid.startswith('r19r')
        row = rid[3:] if is19 else rid
        am = argmap(r['args'])
        needs = r['needs']
        cv = set(x for x in (am.get('-Cvar') or '').split(';') if x)
        spec = SPEC19[row] if is19 else SPECREF[rid]
        # Q3
        if is19:
            chk(am.get('-BinDir') == BIN19, 'Q3 %s bin %s' % (rid, am.get('-BinDir')))
            chk(M + 'ready-r19' in needs and G + 'go-quiet' in needs, 'Q3 %s needs ready-r19 + go-quiet' % rid)
        else:
            chk(am.get('-BinDir') == BINREF, 'Q3 %s bin %s' % (rid, am.get('-BinDir')))
            chk(M + 'ready-s4b-off' in needs and G + 'go-quiet' in needs, 'Q3 %s needs ready-s4b-off + go-quiet' % rid)
            chk(not any('r19-ok' in x or 'go-r19on' in x for x in needs), 'Q3 %s (ref) needs no #19 chain marker' % rid)
        # Q4 (chain over M10's 9 slots; i16/g16 fill slots i/g)
        if is19:
            k = SLOTS.index(SLOT.get(row, row))
            okm = [x for x in needs if 'r19-ok-' in x]
            want = [G + 'r19-ok-' + SLOTS[k - 1]] if k > 0 else []
            chk(okm == want, 'Q4 %s chain needs %s (has %s)' % (rid, want, okm))
            chk((G + 'go-r19on' in needs) == (row in ON), 'Q4 %s go-r19on %s' % (rid, 'needed' if row in ON else 'absent'))
        # Q9 (path markers, C2)
        pm = sorted(x for x in needs if 'r19-path' in x)
        if is19 and row in PATHN:
            chk(pm == [G + 'r19-pathN'] and r.get('unless') == G + 'r19-path16',
                'Q9 %s needs r19-pathN, unless r19-path16 (needs %s, unless %s)' % (rid, pm, r.get('unless')))
        elif is19 and row in PATH16:
            chk(pm == [G + 'r19-path16'] and r.get('unless') == G + 'r19-pathN',
                'Q9 %s needs r19-path16, unless r19-pathN (needs %s, unless %s)' % (rid, pm, r.get('unless')))
        else:
            chk(not pm and 'unless' not in r, 'Q9 %s has no path marker and no unless' % rid)
        # Q5
        hasn = '<N>' in ' '.join(r['args'])
        chk(hasn == (M + 'ready-N' in needs), 'Q5 %s <N> in args %s == needs ready-N' % (rid, hasn))
        chk(('d3d12_debug=true' in cv) == (M + 'ready-dbg' in needs), 'Q5 %s d3d12_debug <-> ready-dbg' % rid)
        # Q6
        chk(cv == spec[0], 'Q6 %s cvars %s == spec %s' % (rid, sorted(cv), sorted(spec[0])))
        # Q7
        bad = [x for x in cv if x.startswith('d3d12_pipeline_creation_no_wait') or 'resolution_scale' in x
               or x.startswith('native_')]
        chk(not bad, 'Q7 %s no #33/res-scaling/native cvar %s' % (rid, bad or ''))
        chk('-Env' not in am, 'Q7 %s no -Env (native/env combos)' % rid)
        b = (am.get('-BinDir') or '').lower()
        chk('ctr' not in b and 'native' not in b, 'Q7 %s bin is not ctr/native' % rid)
        chk(is19 or not any(x.startswith('d3d12_async_submit') for x in cv), 'Q7 %s async only on #19 rows' % rid)
        # Q8
        shape = (am.get('-Seconds'), am.get('-InputScript'), am.get('-StatsWarmup'), bool(r.get('toypad')))
        chk(shape == spec[1:], 'Q8 %s seconds/route/warmup/toypad %s == %s' % (rid, shape, spec[1:]))
    return out


def ready_n(ws):
    try:
        with open(os.path.join(ws, 'build', 'agent3', 's4b', 'ready-N'), 'r', encoding='utf-8-sig') as fh:
            return fh.readline().strip()
    except OSError:
        return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('queue', nargs='?', default=os.path.join(HERE, 'r19prep', 'queue-r19-live.jsonl'))
    ap.add_argument('--ws', default=WS_DEFAULT)
    ap.add_argument('--expect-n', help='Q10: ready-N line 1 must equal this')
    a = ap.parse_args(argv)
    rows, errs = load_rows(a.queue)
    out = [('FAIL', e) for e in errs] + check(rows, known_ids(a.ws))
    if a.expect_n:
        got = ready_n(a.ws)
        out.append(('PASS' if got == a.expect_n else 'FAIL', 'Q10 ready-N line 1 %r == %r' % (got, a.expect_n)))
    for tag, msg in out:
        print('%-5s %s' % (tag, msg))
    nf = sum(1 for t, _ in out if t == 'FAIL')
    print('ALL CHECKS PASS (%d checks)' % len(out) if nf == 0 else 'CHECKS FAILED: %d of %d' % (nf, len(out)))
    return 1 if nf else 0


if __name__ == '__main__':
    sys.exit(main())

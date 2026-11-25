#!/usr/bin/env python3
"""mp3_query_seq.py - MP3 "queries/readbacks complete before the guest reads them" checker, #21 S4-T1 row F3.

Implements FUNCTIONAL-ROWS.md F3 pass rules 1-3 (build/agent7/s4-t1/FUNCTIONAL-ROWS.md L131-151, matrix-s4t1-f3.json
notes; THREADED-PROOFS-TODO.md row MP3). Rule 4 (check_n_rows passes) stays with bench/agent4/check_n_rows.py.
Read-only, stdlib only, one thread; no game, no build. Lowers its own priority to Below Normal.

Run (from the workspace root):
  python -B build/agent7/session3/mp/mp3_query_seq.py --dir <F3 run-matrix out dir> [--json OUT]
  python -B build/agent7/session3/mp/mp3_query_seq.py --ref <n0q-r1> --ref <n0q-r2> --cand <run> [--cand ...]

Exit: 0 PASS, 1 FAIL, 2 INCOMPLETE (a run without query lines = the row's UNCLEAR, a missing run or log, fewer
than 2 ref runs).

Trace line (DimensionsRecomp/rexlego/src/gpu_native/queries.cpp:56-69 = snap1 queries.cpp:67, logged from
GetQueryData :195 the first time a query's result is handed to the guest, i.e. after its fence completed):
  [ts] [info] [core] [tNNNN] Native query value frame=<g_probe_frame> fsr=<true|false> size=<W>x<H>
      query=<guest address, 8 hex> draws=<host draws inside the query> samples=<scaled sample sum>
  with LEGO_NATIVE_QUERY_TRACE_FROM=0: every frame, at most 128 lines per FSR mode (6 modes) per process.
Also counted: 'Native GPU: unsupported query' (ERROR, queries.cpp:53) and 'query 0x... invalidated by failed draw'
(WARNING; a failed query, the guest gets E_FAIL).

Sequence of a run = its trace lines in log order (game.N.log ... game.log). Each query address is renamed to its
first-appearance index (slot), because guest heap addresses need not match between runs.

Agreement of two runs A, B (difflib.SequenceMatcher(autojunk=False).ratio(), 1.0 = identical, 0 = disjoint):
  draws     the draws sequence
  visible   the (draws, samples > 0) sequence: the occlusion verdict the guest acts on
  pairs     the exact (draws, samples) sequence
  order     the (slot, draws) sequence: which query the guest gets back in which order
Info only: line count, slots, zero-sample share, median frame lag of matched (slot, draws) pairs (B - A).

Pass rules
  Q1  every run has at least 1 trace line, else INCOMPLETE (FUNCTIONAL-ROWS L147: UNCLEAR, needs a route that
      issues queries).
  Q2  0 'unsupported query' lines in every run (L148), else FAIL.
  Q3  for each comparison CAND vs AGAINST (--dir: th3q vs n0q and th3cp3q vs th3q, as L149-150) and each metric:
      every candidate run's mean agreement with the AGAINST runs >= noise - --tol, where noise = the agreement of
      the first two runs of --noise-arm (default the ref arm: n0q-r1 vs n0q-r2). --tol defaults to 0.05 (my
      choice: with one noise pair and 2-4 candidate pairs a literal ">=" fails about half of equivalent runs).
  Q4  failed queries ('invalidated by failed draw') per candidate run no more than 2x the ref max and the ref max + 4
      (check_n_rows.py's warning-type rule), else FAIL.
"""
import argparse
import difflib
import importlib.util
import json
import os
import re
import statistics
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))


def _sibling(name, fn):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, fn))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


M2 = _sibling('mp2_same_frames', 'mp2_same_frames.py')
log_files, arm_runs, Result, below_normal = M2.log_files, M2.arm_runs, M2.Result, M2.below_normal

TRACE = re.compile(r'Native query value frame=(\d+) fsr=(\w+) size=(\d+)x(\d+) query=([0-9A-Fa-f]+) '
                   r'draws=(\d+) samples=(\d+)')
UNSUPPORTED = re.compile(r'Native GPU: unsupported query')
FAILED_DRAW = re.compile(r'query 0x[0-9A-Fa-f]+ invalidated by failed draw')
CREATED = re.compile(r'Native GPU: created hardware occlusion query')
METRICS = ('draws', 'visible', 'pairs', 'order')


def read_run(run):
    """{'name', 'files', 'seq': [(frame, fsr, w, h, addr, draws, samples)], 'unsupported', 'failed', 'created'}."""
    files = log_files(run)
    x = {'run': run, 'name': os.path.basename(os.path.normpath(run)), 'files': files, 'seq': [],
         'unsupported': 0, 'failed': 0, 'created': 0, 'unsupported_ex': []}
    for p in files:
        with open(p, encoding='utf-8', errors='replace') as fh:
            for ln in fh:
                m = TRACE.search(ln)
                if m:
                    f, fsr, w, h, addr, d, s = m.groups()
                    x['seq'].append((int(f), fsr, int(w), int(h), addr.upper(), int(d), int(s)))
                    continue
                if UNSUPPORTED.search(ln):
                    x['unsupported'] += 1
                    if len(x['unsupported_ex']) < 3:
                        x['unsupported_ex'].append(ln.strip()[-120:])
                elif FAILED_DRAW.search(ln):
                    x['failed'] += 1
                elif CREATED.search(ln):
                    x['created'] += 1
    slots = {}
    x['slots'] = []
    for r in x['seq']:
        x['slots'].append(slots.setdefault(r[4], len(slots)))
    return x


def views(x):
    seq, sl = x['seq'], x['slots']
    return {'draws': [r[5] for r in seq],
            'visible': [(r[5], r[6] > 0) for r in seq],
            'pairs': [(r[5], r[6]) for r in seq],
            'order': list(zip(sl, [r[5] for r in seq]))}


def ratio(a, b):
    if not a and not b:
        return 1.0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def lag(xa, xb):
    """Median frame difference (B - A) over matched (slot, draws) pairs; None without matches."""
    va, vb = views(xa)['order'], views(xb)['order']
    sm = difflib.SequenceMatcher(None, va, vb, autojunk=False)
    d = []
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            d.append(xb['seq'][blk.b + k][0] - xa['seq'][blk.a + k][0])
    return statistics.median(d) if d else None


def agree(xa, xb):
    va, vb = views(xa), views(xb)
    return dict((m, ratio(va[m], vb[m])) for m in METRICS)


def summary(x):
    n = len(x['seq'])
    z = sum(1 for r in x['seq'] if r[6] == 0)
    fr = [r[0] for r in x['seq']]
    return ('%s: %d trace lines, %d slots, zero-sample share %s, frames %s..%s, unsupported %d, failed-draw '
            'invalidations %d, created-query lines %d' % (
                x['name'], n, len(set(x['slots'])), '%.3f' % (z / float(n)) if n else '-',
                min(fr) if fr else '-', max(fr) if fr else '-', x['unsupported'], x['failed'], x['created']))


def evaluate(refs, comps, a, noise_runs=None):
    """refs: ref run dirs; comps: [(label, cand dirs, against dirs)]; noise_runs: dirs of the noise arm (default
    refs). Returns (Result, data)."""
    res = Result()
    cache = {}

    def get(d):
        if d not in cache:
            cache[d] = read_run(d) if os.path.isdir(d) else None
        return cache[d]

    noise_runs = refs if noise_runs is None else noise_runs
    data = {'params': {k: v for k, v in vars(a).items() if k != 'json'}, 'runs': {}, 'noise': None,
            'comparisons': []}
    every = list(dict.fromkeys(list(refs) + list(noise_runs) + [c for _, cs, ag in comps for c in list(cs) + list(ag)]))
    res.check(len(refs) >= 2, 'ref runs: %d (need 2)%s' % (len(refs), ': ' + ', '.join(
        os.path.basename(os.path.normpath(r)) for r in refs) if refs else ''), incomplete=True)
    for d in every:
        x = get(d)
        nm = os.path.basename(os.path.normpath(d))
        if x is None:
            res.check(False, 'Q1 %s: no run dir' % nm, incomplete=True)
            continue
        if not x['files']:
            res.check(False, 'Q1 %s: no game log' % nm, incomplete=True)
            continue
        res.info(summary(x))
        if x['seq']:
            why = ''
        elif not x['created']:
            why = ' - UNCLEAR: the route created no hardware query (created-query lines 0); needs a route that issues queries'
        else:
            why = (' - UNCLEAR: %d created-query lines but no trace line: LEGO_NATIVE_QUERY_TRACE_FROM not set, or no '
                   'query result reached the guest (failed-draw invalidations %d)' % (x['created'], x['failed']))
        res.check(len(x['seq']) > 0, 'Q1 %s: has query trace lines (%d)%s' % (nm, len(x['seq']), why),
                  incomplete=True)
        res.check(x['unsupported'] == 0, "Q2 %s: 0 'unsupported query' lines (%d)%s" % (
            nm, x['unsupported'], ': ' + ' | '.join(x['unsupported_ex']) if x['unsupported_ex'] else ''))
        data['runs'][nm] = {k: v for k, v in x.items() if k not in ('seq', 'slots')}
        data['runs'][nm]['lines'] = len(x['seq'])
    # noise
    nz = [get(d) for d in noise_runs[:2]]
    noise = None
    if len(nz) == 2 and all(x and x['seq'] for x in nz):
        noise = agree(nz[0], nz[1])
        res.info('noise (%s vs %s): %s; frame lag %s' % (nz[0]['name'], nz[1]['name'], ', '.join(
            '%s %.3f' % (m, noise[m]) for m in METRICS), lag(nz[0], nz[1])))
    else:
        res.check(False, 'Q3 noise pair: needs 2 noise-arm runs with trace lines', incomplete=True)
    data['noise'] = noise
    # ref max of failed-draw invalidations
    rx = [get(d) for d in refs]
    fmax = max([x['failed'] for x in rx if x] or [0])
    for label, cands, against in comps:
        comp = {'label': label, 'pairs': [], 'per_cand': {}}
        res.check(bool(cands), '%s: candidate runs found: %d' % (label, len(cands)), incomplete=True)
        res.check(bool(against), '%s: comparison runs found: %d' % (label, len(against)), incomplete=True)
        ag = [get(d) for d in against]
        ag = [x for x in ag if x and x['seq']]
        for c in cands:
            xc = get(c)
            if not xc:
                continue
            lim = max(2 * fmax, fmax + 4)
            res.check(xc['failed'] <= lim, 'Q4 %s %s: failed-draw invalidations %d <= max(2 x ref max, ref max + 4) '
                      '= %d' % (label, xc['name'], xc['failed'], lim))
            if not xc['seq'] or not ag:
                continue
            scores = [agree(xa, xc) for xa in ag]
            for xa, s in zip(ag, scores):
                comp['pairs'].append({'against': xa['name'], 'cand': xc['name'], 'agree': s, 'lag': lag(xa, xc)})
                res.info('%s %s vs %s: %s; frame lag %s' % (label, xc['name'], xa['name'], ', '.join(
                    '%s %.3f' % (m, s[m]) for m in METRICS), comp['pairs'][-1]['lag']))
            mean = dict((m, statistics.fmean([s[m] for s in scores])) for m in METRICS)
            comp['per_cand'][xc['name']] = mean
            if noise is not None:
                for m in METRICS:
                    res.check(mean[m] >= noise[m] - a.tol, 'Q3 %s %s: %s agreement %.3f >= noise %.3f - tol %g' % (
                        label, xc['name'], m, mean[m], noise[m], a.tol))
        data['comparisons'].append(comp)
    return res, data


def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument('--dir', help='F3 run-matrix out dir (runs/<HHMM>-<arm>-r<k>)')
    ap.add_argument('--ref-arm', default='n0q', help='reference arm in --dir mode (default n0q)')
    ap.add_argument('--comp', action='append', default=None,
                    help='CAND:AGAINST arm pair in --dir mode (repeat; default th3q:n0q and th3cp3q:th3q)')
    ap.add_argument('--noise-arm', default=None, help='arm whose first two runs give the noise (default --ref-arm)')
    ap.add_argument('--ref', action='append', default=[], help='reference run dir (repeat; first two = noise pair)')
    ap.add_argument('--cand', action='append', default=[], help='candidate run dir, compared with the --ref runs')
    ap.add_argument('--tol', type=float, default=0.05, help='agreement tolerance below the noise (default 0.05)')
    ap.add_argument('--json', help='write the result as JSON')
    ap.add_argument('--normal-priority', action='store_true', help="don't lower this process to Below Normal")
    return ap.parse_args(argv)


def main(argv=None):
    a = parse_args(sys.argv[1:] if argv is None else list(argv))
    if not a.normal_priority:
        below_normal()
    if a.dir:
        refs = arm_runs(a.dir, a.ref_arm)
        noise_runs = arm_runs(a.dir, a.noise_arm) if a.noise_arm else refs
        comps = []
        for spec in (a.comp or ['th3q:n0q', 'th3cp3q:th3q']):
            ca, _, aa = spec.partition(':')
            aa = aa or a.ref_arm
            comps.append(('%s vs %s' % (ca, aa), arm_runs(a.dir, ca), arm_runs(a.dir, aa)))
    elif a.ref or a.cand:
        refs, noise_runs = a.ref, a.ref
        comps = [('cand vs ref', a.cand, a.ref)]
    else:
        print('INCOMPLETE give --dir, or --ref and --cand')
        return 2
    res, data = evaluate(refs, comps, a, noise_runs)
    print('mp3_query_seq %s' % (a.dir or 'explicit runs'))
    for ln in res.lines:
        print(ln)
    print('RESULT: %s (%d failed, %d incomplete)' % (res.verdict, len(res.fails), len(res.incomplete)))
    if a.json:
        data.update(verdict=res.verdict, checks=res.lines, fails=res.fails, incomplete=res.incomplete, dir=a.dir)
        with open(a.json, 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(data, fh, indent=1, default=str)
    return 1 if res.fails else (2 if res.incomplete else 0)


if __name__ == '__main__':
    sys.exit(main())

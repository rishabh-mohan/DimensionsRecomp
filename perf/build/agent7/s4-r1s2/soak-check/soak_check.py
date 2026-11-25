#!/usr/bin/env python3
"""soak_check.py - counter-line checker for the S4 #19 (R1 stage 2) soak (M7, session 3, S3T-7).

Implements SOAK.md pass rules 3-5 (build/agent7/s4-r1s2/SOAK.md) on one run's game log. Read-only; stdlib only;
no game, no build. Rules 1, 2 and 6 stay with their own tools (s4b_check.py fail markers and close, logdiff
--allow-new 'd3d12_async_submit: ', the sys.csv slow state).

Run (Below Normal, from the workspace root):
  python -B build/agent7/s4-r1s2/soak-check/soak_check.py <run dir | game.log> [--row e|j] [--json out.json]

Exit: 0 PASS, 1 FAIL, 2 INCOMPLETE (no log, or too few counter lines to judge).

Line formats (new/sdk/src/graphics/d3d12/command_processor.cpp, after-file numbers; logger prefix
"[YYYY-MM-DD HH:MM:SS.mmm] [info] [gpu] [tNNNN] "):
  :1956  d3d12_async_submit: submitting splits on the submit thread (3 slots)        init, once per SetupContext
  :1944  d3d12_async_submit: needs d3d12_submit_split_kb above 0, staying off        WARN  -> FAIL
  :1959  d3d12_async_submit: failed to create the submit thread, staying off         ERROR -> FAIL
  :4581  d3d12_async_submit: frame= submission= chunks= queued_max= full_waits= full_wait_us= drains_waited=
         drain_wait_us= worker_us=                                                   about every 10 s
  :4475  d3d12_submit_split: frame= submission= splits= failed= held_query= held_scratch= held_pipelines=
  #18's init (S4b): d3d12_submit_split_kb: splitting submissions at N KB ...

Checks
  A1 the async init line appears (exactly once per segment; a segment starts at each init line, because
     SetupContext resets both stat blocks, cp.cpp:1213 and :1940); no 'staying off' / 'failed to create' line.
  A2 every async counter line has all 9 keys; within a segment frame, submission, chunks, queued_max (a running
     max), full_waits, full_wait_us, drains_waited, drain_wait_us and worker_us never decrease (rule 3).
  A3 queued_max <= --max-queued (3 = kAsyncSubmitSlots, cp.h:902) in every line (rule 3).
  A4 chunks > 0 in the last line of each segment (rule 3), and at least --min-lines async counter lines in total.
  S1 every split counter line has all 7 keys and failed = 0 (rule 4); its counters never decrease in a segment.
  S2 held_query > 0 in at least one split line (rule 4: queries ran).
  X1 both families come from the GPU Commands thread, so merged in log order frame and submission never decrease.
  X2 chunks vs splits (async mode): EndSubmissionAsync logs after ++chunks (cp.cpp:4539) and before the caller's
     ++splits (:4462), so with the cvar on for the whole segment an async line's chunks = splits + 1 at that
     moment, and a split line's splits = chunks. Across snapshots: an async line's chunks >= the last split line's
     splits + 1, and a split line's splits >= the last async line's chunks.
  J1 (--row j only) full_waits > 0 in the last async line (the FIFO filled).
  Report (rule 5): per-frame and per-second deltas between the first and last async counter line of the longest
  segment: chunks, submissions, drains_waited, drain_wait_us, full_wait_us, worker_us.

Log files: <run dir>/game.log plus rotated game.1.log, game.2.log ... (5 MB rotation, 2 kept; older first).
If the log rotated and the init line is gone, A1 reports INCOMPLETE for that segment instead of FAIL.
"""
import argparse
import glob
import json
import os
import re
import sys

PREFIX = re.compile(r'^\[(\d{4}-\d\d-\d\d) (\d\d):(\d\d):(\d\d(?:\.\d+)?)\]')
KV = re.compile(r'([a-z_]+)=(-?\d+)\b')
ASYNC = 'd3d12_async_submit: '
SPLIT = 'd3d12_submit_split: '
INIT_ASYNC = 'd3d12_async_submit: submitting splits on the submit thread'
INIT_SPLIT = 'd3d12_submit_split_kb: splitting submissions'
BAD_ASYNC = ('d3d12_async_submit: needs d3d12_submit_split_kb above 0',
             'd3d12_async_submit: failed to create the submit thread')
ASYNC_KEYS = ['frame', 'submission', 'chunks', 'queued_max', 'full_waits', 'full_wait_us', 'drains_waited',
              'drain_wait_us', 'worker_us']
SPLIT_KEYS = ['frame', 'submission', 'splits', 'failed', 'held_query', 'held_scratch', 'held_pipelines']
REPORT_KEYS = ['chunks', 'submission', 'drains_waited', 'drain_wait_us', 'full_wait_us', 'worker_us']


def log_files(path):
    """Oldest first: game.N.log ... game.1.log, game.log."""
    if os.path.isfile(path):
        return [path]
    if not os.path.isdir(path):
        return []
    rot = []
    for p in glob.glob(os.path.join(path, 'game.*.log')):
        m = re.match(r'game\.(\d+)\.log$', os.path.basename(p))
        if m:
            rot.append((int(m.group(1)), p))
    files = [p for _, p in sorted(rot, reverse=True)]
    if os.path.isfile(os.path.join(path, 'game.log')):
        files.append(os.path.join(path, 'game.log'))
    return files


def secs(line):
    m = PREFIX.match(line)
    if not m:
        return None
    # day changes are rare in a 10-min soak; fold the date in as whole days of the month
    day = int(m.group(1)[8:10])
    return ((day * 24 + int(m.group(2))) * 60 + int(m.group(3))) * 60 + float(m.group(4))


def parse(lines):
    """Events in log order: (kind, lineno, t, payload)."""
    ev = []
    for i, raw in enumerate(lines, 1):
        line = raw.rstrip('\r\n')
        if INIT_ASYNC in line:
            ev.append(('init_async', i, secs(line), line))
        elif any(b in line for b in BAD_ASYNC):
            ev.append(('bad_async', i, secs(line), line))
        elif INIT_SPLIT in line:
            ev.append(('init_split', i, secs(line), line))
        elif ASYNC in line:
            body = line.split(ASYNC, 1)[1]
            ev.append(('async', i, secs(line), {k: int(v) for k, v in KV.findall(body)}))
        elif SPLIT in line:
            body = line.split(SPLIT, 1)[1]
            ev.append(('split', i, secs(line), {k: int(v) for k, v in KV.findall(body)}))
    return ev


class Result:
    def __init__(self):
        self.lines = []
        self.fails = []
        self.incomplete = []

    def check(self, cond, msg, incomplete=False):
        tag = 'PASS' if cond else ('INCOMPLETE' if incomplete else 'FAIL')
        self.lines.append('%-10s %s' % (tag, msg))
        if not cond:
            (self.incomplete if incomplete else self.fails).append(msg)

    def info(self, msg):
        self.lines.append('           ' + msg)


def monotonic(seq, keys, family, res, seg):
    bad = []
    for a, b in zip(seq, seq[1:]):
        for k in keys:
            if k in a[3] and k in b[3] and b[3][k] < a[3][k]:
                bad.append('L%d->L%d %s %d->%d' % (a[1], b[1], k, a[3][k], b[3][k]))
    res.check(not bad, 'seg %d: %s counters never decrease over %d lines%s'
              % (seg, family, len(seq), (': ' + '; '.join(bad[:5]) + (' ...' if len(bad) > 5 else '')) if bad else ''))


def check_events(ev, row='e', max_queued=3, min_lines=2, rotated=False):
    res = Result()
    n_async = sum(1 for e in ev if e[0] == 'async')
    n_split = sum(1 for e in ev if e[0] == 'split')
    n_init = sum(1 for e in ev if e[0] == 'init_async')
    res.info('lines: async init %d, async counter %d, split counter %d, split init %d'
             % (n_init, n_async, n_split, sum(1 for e in ev if e[0] == 'init_split')))

    bad = [e for e in ev if e[0] == 'bad_async']
    res.check(not bad, "no 'staying off' / 'failed to create the submit thread' line%s"
              % (': L%d %s' % (bad[0][1], bad[0][3][-80:]) if bad else ''))

    # segments: a new one at each async init line (SetupContext resets both stat blocks)
    segs, cur = [], {'init': None, 'ev': []}
    for e in ev:
        if e[0] == 'init_async':
            if cur['init'] is not None or cur['ev']:
                segs.append(cur)
            cur = {'init': e, 'ev': []}
        elif e[0] in ('async', 'split'):
            cur['ev'].append(e)
    if cur['init'] is not None or cur['ev']:
        segs.append(cur)
    if not segs:
        res.check(False, 'async init line present (no d3d12_async_submit line at all)', incomplete=True)
        res.check(False, 'at least %d async counter lines (found 0)' % min_lines, incomplete=True)
        return res, None

    res.check(len(segs) == 1, 'one segment (one SetupContext): %d' % len(segs))
    held_any = False
    best = None
    for si, s in enumerate(segs, 1):
        a = [e for e in s['ev'] if e[0] == 'async']
        sp = [e for e in s['ev'] if e[0] == 'split']
        if s['init'] is None:
            res.check(False, 'seg %d: async init line before its counter lines%s'
                      % (si, ' (log rotated: the init line may be in a dropped file)' if rotated else ''),
                      incomplete=rotated)
        else:
            res.check(True, 'seg %d: async init line L%d' % (si, s['init'][1]))
        # A2 keys + monotonic
        miss = [(e[1], sorted(set(ASYNC_KEYS) - set(e[3]))) for e in a if set(ASYNC_KEYS) - set(e[3])]
        res.check(not miss, 'seg %d: every async counter line has the 9 keys%s'
                  % (si, ': L%d lacks %s' % miss[0] if miss else ''))
        monotonic(a, ASYNC_KEYS, 'async', res, si)
        # A3
        over = [e for e in a if e[3].get('queued_max', 0) > max_queued]
        res.check(not over, 'seg %d: queued_max <= %d (max %s)'
                  % (si, max_queued, max([e[3].get('queued_max', 0) for e in a]) if a else '-'))
        # A4
        if a:
            res.check(a[-1][3].get('chunks', 0) > 0, 'seg %d: chunks > 0 (last line L%d: %d)'
                      % (si, a[-1][1], a[-1][3].get('chunks', 0)))
        # S1
        miss = [(e[1], sorted(set(SPLIT_KEYS) - set(e[3]))) for e in sp if set(SPLIT_KEYS) - set(e[3])]
        res.check(not miss, 'seg %d: every split counter line has the 7 keys%s'
                  % (si, ': L%d lacks %s' % miss[0] if miss else ''))
        failed = [e for e in sp if e[3].get('failed', 0) != 0]
        res.check(not failed, 'seg %d: failed = 0 in every split line (%d lines)%s'
                  % (si, len(sp), ': L%d failed=%d' % (failed[0][1], failed[0][3]['failed']) if failed else ''))
        monotonic(sp, [k for k in SPLIT_KEYS], 'split', res, si)
        held_any = held_any or any(e[3].get('held_query', 0) > 0 for e in sp)
        # X1 merged frame/submission order
        merged = s['ev']
        bad = []
        for p, q in zip(merged, merged[1:]):
            for k in ('frame', 'submission'):
                if k in p[3] and k in q[3] and q[3][k] < p[3][k]:
                    bad.append('L%d(%s)->L%d(%s) %s %d->%d' % (p[1], p[0], q[1], q[0], k, p[3][k], q[3][k]))
        res.check(not bad, 'seg %d: merged async+split lines: frame and submission never decrease%s'
                  % (si, ': ' + '; '.join(bad[:3]) if bad else ''))
        # X2 chunks vs splits
        bad = []
        last_split, last_chunks = None, None
        for e in merged:
            if e[0] == 'async' and 'chunks' in e[3]:
                if last_split is not None and e[3]['chunks'] < last_split + 1:
                    bad.append('L%d chunks=%d < last splits %d + 1' % (e[1], e[3]['chunks'], last_split))
                last_chunks = e[3]['chunks']
            elif e[0] == 'split' and 'splits' in e[3]:
                if last_chunks is not None and e[3]['splits'] < last_chunks:
                    bad.append('L%d splits=%d < last chunks %d' % (e[1], e[3]['splits'], last_chunks))
                last_split = e[3]['splits']
        res.check(not bad, 'seg %d: chunks/splits consistent (every split went async)%s'
                  % (si, ': ' + '; '.join(bad[:3]) if bad else ''))
        if best is None or len(a) > len(best):
            best = a
    res.check(n_async >= min_lines, 'at least %d async counter lines (found %d)' % (min_lines, n_async),
              incomplete=True)
    res.check(held_any, 'held_query > 0 in at least one split line (queries ran)'
              if n_split else 'held_query > 0 in at least one split line (no split line found)')
    if row == 'j':
        last = best[-1][3] if best else {}
        res.check(last.get('full_waits', 0) > 0, 'row j: full_waits > 0 (last line: %s)' % last.get('full_waits', '-'))

    rep = None
    if best and len(best) >= 2:
        f, l = best[0], best[-1]
        df = l[3].get('frame', 0) - f[3].get('frame', 0)
        dt = (l[2] - f[2]) if (l[2] is not None and f[2] is not None) else None
        rep = {'first_line': f[1], 'last_line': l[1], 'frames': df, 'seconds': dt, 'per_frame': {},
               'per_second': {}, 'delta': {}}
        for k in REPORT_KEYS:
            d = l[3].get(k, 0) - f[3].get(k, 0)
            rep['delta'][k] = d
            rep['per_frame'][k] = (d / df) if df > 0 else None
            rep['per_second'][k] = (d / dt) if dt else None
        res.info('rule 5, L%d..L%d: %d frames over %s s' % (f[1], l[1], df, '%.1f' % dt if dt else '?'))
        for k in REPORT_KEYS:
            pf, ps = rep['per_frame'][k], rep['per_second'][k]
            res.info('  %-14s delta %-12d per frame %-12s per s %s' % (
                k + ('s' if k == 'submission' else ''), rep['delta'][k],
                '%.4f' % pf if pf is not None else '-', '%.2f' % ps if ps is not None else '-'))
    return res, rep


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('path', help='run dir (reads game.log and rotated game.N.log) or one log file')
    ap.add_argument('--row', choices=['e', 'j'], default='e', help='e = soak (default), j = queue pressure')
    ap.add_argument('--max-queued', type=int, default=3)
    ap.add_argument('--min-lines', type=int, default=2)
    ap.add_argument('--json', help='write the result as JSON')
    a = ap.parse_args(argv)
    files = log_files(a.path)
    if not files:
        print('INCOMPLETE no game log at %s' % a.path)
        return 2
    lines = []
    for p in files:
        with open(p, 'r', encoding='utf-8', errors='replace') as fh:
            lines.extend(fh.readlines())
    res, rep = check_events(parse(lines), row=a.row, max_queued=a.max_queued, min_lines=a.min_lines,
                            rotated=len(files) > 1)
    verdict = 'FAIL' if res.fails else ('INCOMPLETE' if res.incomplete else 'PASS')
    print('soak_check %s row %s: %s' % (a.path, a.row, ', '.join(os.path.basename(p) for p in files)))
    for ln in res.lines:
        print(ln)
    print('RESULT: %s (%d failed, %d incomplete)' % (verdict, len(res.fails), len(res.incomplete)))
    if a.json:
        with open(a.json, 'w', encoding='ascii', newline='\n') as fh:
            json.dump({'path': a.path, 'row': a.row, 'files': files, 'verdict': verdict, 'checks': res.lines,
                       'fails': res.fails, 'incomplete': res.incomplete, 'rule5': rep}, fh, indent=1)
    return 1 if res.fails else (2 if res.incomplete else 0)


if __name__ == '__main__':
    sys.exit(main())

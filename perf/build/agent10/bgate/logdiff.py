"""Agent 10 (task #9): compare game.log files of a candidate build with baseline runs, for the B game gate.
READ-ONLY. Usage:
  python build\\agent10\\bgate\\logdiff.py --base <glob> [--base <glob> ...] --cand <glob> [--cand <glob> ...] [--min-level warning]
Each glob matches game.log files (or run dirs that contain one). Lines are '[ts] [level] [cat] [tid] message'; a line that
doesn't start with '[' continues the previous one and is ignored. Messages are normalized (hex, numbers, quoted paths)
so that the same message type from different runs compares equal.
Output:
  per log: line counts by level, the fail-marker counts and clean-exit (the normal exit line);
  NEW: normalized (level, cat, msg) keys at or above --min-level that appear in a candidate log but in no baseline log;
  MORE: keys whose candidate count per log exceeds the baseline maximum per log by more than max(5, 2x);
  GONE: keys present in every baseline log but missing from a candidate log (a skipped code path, or a marker lost);
  MARKER CHECK: a fail marker counted more often in a candidate log than in any baseline log, or a candidate log
  without the clean-exit line when every baseline log has it.
02:36 change: the 'fatal' marker no longer matches the normal exit line "Title terminated; hard-exiting process."
(every 0013-matrix log had fatal=1 from it); that line is now counted as clean-exit.
"""
import argparse
import collections
import glob
import os
import re
import sys

LEVELS = ['trace', 'debug', 'info', 'warning', 'error', 'critical']
LINE = re.compile(r'^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+)\] \[([a-z]+)\] \[([^\]]*)\] (?:\[t\d+\] )?(.*)$')
MARKERS = [
    ('not-in-module', re.compile(r'not in any registered module', re.I)),
    ('crash-guard', re.compile(r'crash guard', re.I)),
    ('unimplemented', re.compile(r'unimplemented|REX_UNIMPLEMENTED', re.I)),
    ('exception', re.compile(r'exception|0xC0000409|0xC00000FD|stack overflow|access violation|0xC0000005', re.I)),
    ('watchdog/hang', re.compile(r'watchdog|hang detected|deadlock|timed out', re.I)),
    ('fatal', re.compile(r'fatal|abort|(?<!Title )terminat', re.I)),
]
EXIT_LINE = re.compile(r'Title terminated; hard-exiting process')
NORM = [
    (re.compile(r'[A-Za-z]:\\[^\s"\']+'), '<path>'),
    (re.compile(r'0x[0-9A-Fa-f]+'), '0x#'),
    (re.compile(r'\b[0-9A-Fa-f]{8,}\b'), '#h'),
    (re.compile(r'\d+(\.\d+)?'), '#'),
]


def norm(msg):
    for rx, rep in NORM:
        msg = rx.sub(rep, msg)
    return msg[:200]


def logs(globs):
    out = []
    for g in globs:
        for p in sorted(glob.glob(g)):
            if os.path.isdir(p):
                p = os.path.join(p, 'game.log')
            if os.path.isfile(p):
                out.append(p)
    return out


def read(path):
    keys = collections.Counter()
    levels = collections.Counter()
    marks = collections.Counter()
    first = last = None
    with open(path, encoding='utf-8', errors='replace') as f:
        for ln in f:
            m = LINE.match(ln.rstrip('\r\n'))
            if not m:
                continue
            ts, lvl, cat, msg = m.groups()
            first = first or ts
            last = ts
            levels[lvl] += 1
            keys[(lvl, cat, norm(msg))] += 1
            for name, rx in MARKERS:
                if rx.search(msg):
                    marks[name] += 1
            if EXIT_LINE.search(msg):
                marks['clean-exit'] += 1
    return keys, levels, marks, first, last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', action='append', required=True)
    ap.add_argument('--cand', action='append', required=True)
    ap.add_argument('--min-level', default='warning', choices=LEVELS)
    a = ap.parse_args()
    floor = LEVELS.index(a.min_level)
    base, cand = logs(a.base), logs(a.cand)
    if not base or not cand:
        sys.exit('no logs: base %d, cand %d' % (len(base), len(cand)))
    data = {p: read(p) for p in base + cand}
    print('# logdiff: %d baseline logs, %d candidate logs, min level %s' % (len(base), len(cand), a.min_level))
    print('## per log (lines by level; fail markers; clean-exit)')
    for p in base + cand:
        keys, levels, marks, first, last = data[p]
        tag = 'BASE' if p in base else 'CAND'
        lv = ' '.join('%s=%d' % (l, levels[l]) for l in LEVELS if levels[l])
        mk = ' '.join('%s=%d' % (n, marks[n]) for n, _ in MARKERS if marks[n]) or 'no fail markers'
        print('%s %s | %s..%s | %s | %s | clean-exit=%d' % (tag, os.path.relpath(p), (first or '-')[11:19],
                                                           (last or '-')[11:19], lv, mk, marks['clean-exit']))
    bmax = collections.Counter()
    bseen = collections.Counter()
    for p in base:
        for k, n in data[p][0].items():
            bmax[k] = max(bmax[k], n)
            bseen[k] += 1
    print('## NEW keys (level >= %s; in a candidate log, in no baseline log)' % a.min_level)
    newc = 0
    for p in cand:
        for k, n in sorted(data[p][0].items()):
            if LEVELS.index(k[0]) >= floor and k not in bmax:
                newc += 1
                print('NEW %s x%d [%s] [%s] %s' % (os.path.relpath(p), n, k[0], k[1], k[2]))
    print('## MORE keys (level >= %s; candidate count > baseline max + max(5, baseline max))' % a.min_level)
    for p in cand:
        for k, n in sorted(data[p][0].items()):
            if LEVELS.index(k[0]) >= floor and k in bmax and n > bmax[k] + max(5, bmax[k]):
                print('MORE %s x%d (baseline max %d) [%s] [%s] %s' % (os.path.relpath(p), n, bmax[k], k[0], k[1], k[2]))
    print('## GONE keys (any level; in every baseline log, missing from a candidate log)')
    for p in cand:
        for k in sorted(k for k, s in bseen.items() if s == len(base)):
            if k not in data[p][0]:
                print('GONE %s [%s] [%s] %s' % (os.path.relpath(p), k[0], k[1], k[2]))
    print('## MARKER CHECK (fail marker above the baseline max per log; clean-exit missing)')
    mmax = collections.Counter()
    for p in base:
        for n, _ in MARKERS:
            mmax[n] = max(mmax[n], data[p][2][n])
    every_exit = all(data[p][2]['clean-exit'] for p in base)
    flags = 0
    for p in cand:
        marks = data[p][2]
        for n, _ in MARKERS:
            if marks[n] > mmax[n]:
                flags += 1
                print('FLAG %s %s=%d (baseline max %d)' % (os.path.relpath(p), n, marks[n], mmax[n]))
        if every_exit and not marks['clean-exit']:
            flags += 1
            print('FLAG %s no clean-exit line (every baseline log has one)' % os.path.relpath(p))
    print('# NEW total %d, marker flags %d' % (newc, flags))


if __name__ == '__main__':
    main()

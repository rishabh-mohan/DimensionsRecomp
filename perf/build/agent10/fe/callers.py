#!/usr/bin/env python3
"""callers: functions in snapB3 that call (or tail-call) the given names (Agent 10, read-only).
  callers.py NAME ..."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import livein

names = sys.argv[1:]
pat = re.compile(r'(?<![\w.])(%s)\(ctx, base\)' % '|'.join(map(re.escape, names)))
hits = {n: [] for n in names}
for tu, name, lines in livein.funcs(livein.GEN['B']):
    for i, l in enumerate(lines):
        for m in pat.finditer(l):
            hits[m.group(1)].append('%s TU %d line +%d%s' % (name, tu, i, ' (tail)' if 'return' in l else ''))
for n in names:
    print('%s: %d call sites' % (n, len(hits[n])))
    for h in hits[n][:40]:
        print('   ' + h)

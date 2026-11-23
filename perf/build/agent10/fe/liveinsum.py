#!/usr/bin/env python3
"""liveinsum: group livein-B.txt read-first patterns by variable and by line shape (Agent 10, read-only)."""
import re, collections

L = open(r'build\agent10\fe\livein-B.txt', encoding='utf-8').read().split('\n')
pat = re.compile(r'^\s+(\d+)\s+(read|read-loop|mfcr) (\S+): (.*?)   e\.g\. (.*)$')
byvar, byshape, kinds = collections.Counter(), collections.Counter(), collections.Counter()
other = []
for l in L:
    m = pat.match(l)
    if not m:
        continue
    c, kind, var, line, ex = int(m.group(1)), m.group(2), m.group(3), m.group(4), m.group(5)
    kinds[kind] += c
    byvar[var] += c
    if re.match(r'^if \(!?cr\d\.\w+\) return;$', line):
        shape = 'if (crN.bit) return;'
    elif re.match(r'^if \(!?cr\d\.\w+\) goto loc_N;$', line):
        shape = 'if (crN.bit) goto loc;'
    elif line.startswith('ctx.R.u64 = (cr'):
        shape = 'ctx.R.u64 = (crN.lt<<..)|..(mfocrf-style)'
    else:
        shape = 'other'
        other.append('%6d %s %s: %s   e.g. %s' % (c, kind, var, line, ex.split(';')[0]))
    byshape[shape] += c
print('kinds:', dict(kinds))
print('by var:', dict(byvar.most_common()))
print('by shape:', dict(byshape.most_common()))
print('other shapes (%d):' % len(other))
for o in other[:80]:
    print(o)

#!/usr/bin/env python3
"""show: print a generated function from snap1 (A) or snapB3 (B) with line numbers (Agent 10, read-only).

  show.py SIDE NAME [TU] [FROM] [TO]     SIDE = A or B; TU is a hint (searched first); lines FROM..TO (0-based)
"""
import os, re, sys

GEN = dict(A=r'build\agent2\snap1\DimensionsRecomp\rexlego\generated\default',
           B=r'build\agent2\snapB3\DimensionsRecomp\rexlego\generated\default')


def find(side, name, tu=None):
    d = GEN[side]
    allt = sorted(int(m.group(1)) for m in (re.match(r'^legodimensions_recomp\.(\d+)\.cpp$', f)
                                             for f in os.listdir(d)) if m)
    order = ([tu] if tu is not None else []) + [t for t in allt if t != tu]
    pat = re.compile((r'^(?:DEFINE_REX_FUNC\(%s\)|PPC_FUNC_IMPL\(__imp__%s\)|PPC_FUNC\(%s\))' % (name, name, name)).encode(), re.M)
    for t in order:
        with open(os.path.join(d, 'legodimensions_recomp.%d.cpp' % t), 'rb') as f:
            data = f.read()
        m = pat.search(data)
        if m:
            e = data.find(b'\n}', m.start())
            return t, data[m.start():(e + 2) if e >= 0 else len(data)].decode('utf-8', 'replace').split('\n')
    return None, []


if __name__ == '__main__':
    side, name = sys.argv[1], sys.argv[2]
    tu = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] != '-' else None
    a = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    t, lines = find(side, name, tu)
    b = int(sys.argv[5]) if len(sys.argv) > 5 else len(lines) - 1
    print('== %s %s TU %s (%d lines)' % (side, name, t, len(lines)))
    for i in range(max(0, a), min(len(lines), b + 1)):
        print('%4d  %s' % (i, lines[i].rstrip('\r')))

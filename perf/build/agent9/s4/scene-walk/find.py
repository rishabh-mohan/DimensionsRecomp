#!/usr/bin/env python3
"""Read-only lookup helper for the scene-walk analysis (Agent 9 helper, S4).

Usage (always via bench/agent9/cpu2.ps1):
  python find.py map  NAME [NAME...]        -> map lines (object file = TU) for each sub_ name
  python find.py def  TU_NUM NAME [NAME...] -> line range of DEFINE_REX_FUNC(NAME) in legodimensions_recomp.TU_NUM.cpp
  python find.py grep FILE REGEX [MAX]      -> numbered matching lines of FILE
  python find.py calls TU_NUM NAME          -> callees (sub_XXXXXXXX tokens) inside the body of NAME, with line numbers
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
GEN = os.path.join(ROOT, 'baseline', 'DimensionsRecomp', 'rexlego', 'generated', 'default')
MAP = os.path.join(ROOT, 'build', 'agent2', 'devoff2-bin', 'legodimensions.map')


def tu_path(n):
    return os.path.join(GEN, 'legodimensions_recomp.%s.cpp' % n)


def cmd_map(names):
    want = set(names)
    pat = re.compile(r'\b(sub_[0-9A-Fa-f]{8})\b')
    with open(MAP, 'r', encoding='latin-1') as f:
        for line in f:
            for m in pat.finditer(line):
                if m.group(1) in want:
                    print(line.rstrip())
                    break


def func_ranges(path, names):
    want = set(names)
    out = {}
    cur = None
    start = None
    defpat = re.compile(r'^\s*(?:DEFINE_REX_FUNC|REX_FUNC|PPC_FUNC_IMPL|PPC_FUNC)\((sub_[0-9A-Fa-f]{8}|__imp__sub_[0-9A-Fa-f]{8})\)')
    with open(path, 'r', encoding='latin-1') as f:
        for i, line in enumerate(f, 1):
            m = defpat.match(line)
            if m:
                if cur is not None:
                    out[cur] = (start, i - 1)
                    cur = None
                nm = m.group(1).replace('__imp__', '')
                if nm in want:
                    cur = nm
                    start = i
        if cur is not None:
            out[cur] = (start, i)
    return out


def cmd_def(tu, names):
    r = func_ranges(tu_path(tu), names)
    for n in names:
        print(n, r.get(n))


def cmd_grep(path, regex, mx):
    pat = re.compile(regex)
    c = 0
    with open(path, 'r', encoding='latin-1') as f:
        for i, line in enumerate(f, 1):
            if pat.search(line):
                print('%d: %s' % (i, line.rstrip()[:240]))
                c += 1
                if c >= mx:
                    break


def cmd_calls(tu, name):
    r = func_ranges(tu_path(tu), [name])
    if name not in r:
        print('not found')
        return
    s, e = r[name]
    pat = re.compile(r'\b(sub_[0-9A-Fa-f]{8})\b|\b(REX_CALL_INDIRECT[A-Z_]*|PPC_CALL_INDIRECT_FUNC|ctx\.ctr)\b')
    with open(tu_path(tu), 'r', encoding='latin-1') as f:
        for i, line in enumerate(f, 1):
            if i < s:
                continue
            if i > e:
                break
            if i == s:
                continue
            if 'sub_' in line or 'INDIRECT' in line or 'bctrl' in line:
                print('%d: %s' % (i, line.rstrip()[:200]))
    print('range', s, e)


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        sys.exit(2)
    if a[0] == 'map':
        cmd_map(a[1:])
    elif a[0] == 'def':
        cmd_def(a[1], a[2:])
    elif a[0] == 'grep':
        cmd_grep(a[1], a[2], int(a[3]) if len(a) > 3 else 400)
    elif a[0] == 'calls':
        cmd_calls(a[1], a[2])
    else:
        print(__doc__)
        sys.exit(2)

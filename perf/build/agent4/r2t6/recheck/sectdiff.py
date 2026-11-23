#!/usr/bin/env python3
"""Task #25 helper (read-only): compare two mc_smoke_check logs (CRLF or LF) section by section.
usage: python sectdiff.py A.txt B.txt [-v]   (-v prints the differing lines)"""
import difflib
import sys

TAGS = ('C1 ', 'C2 ', 'OFF events', 'ON events', 'C3 ', 'C4 ', 'RESULT')


def read_text(path):
    """Decode by BOM: logs saved with a PowerShell '>' are UTF-16 LE (Agent 3's r6 log); --out files are UTF-8."""
    with open(path, 'rb') as f:
        raw = f.read()
    if raw[:2] in (b'\xff\xfe', b'\xfe\xff'):
        return raw.decode('utf-16')
    if raw[:3] == b'\xef\xbb\xbf':
        raw = raw[3:]
    return raw.decode('utf-8', errors='replace')


def sections(path):
    lines = read_text(path).replace('\r\n', '\n').rstrip('\n').split('\n')
    order, out, cur = ['header'], {'header': []}, 'header'
    for line in lines:
        for tag in TAGS:
            if line.startswith(tag):
                cur = tag.strip()
                if cur not in out:
                    order.append(cur)
                    out[cur] = []
        out[cur].append(line)
    return order, out


def main():
    (oa, a), (ob, b) = sections(sys.argv[1]), sections(sys.argv[2])
    names = oa + [n for n in ob if n not in oa]
    for name in names:
        la, lb = a.get(name, []), b.get(name, [])
        print(f'{name:10s} {"same" if la == lb else "DIFF"}  lines {len(la)} / {len(lb)}')
        if la != lb and '-v' in sys.argv:
            for d in list(difflib.unified_diff(la, lb, lineterm='', n=0))[2:]:
                print('    ' + d[:220])


if __name__ == '__main__':
    main()

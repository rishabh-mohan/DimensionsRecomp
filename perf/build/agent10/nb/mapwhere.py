#!/usr/bin/env python3
"""Find the containing function for guest addresses in a lld/link .map (read-only).

usage: mapwhere.py MAPFILE ADDR [ADDR ...]
Looks for symbols named sub_XXXXXXXX (recompiled guest functions) and __imp__*
aliases whose name encodes a guest address; prints the closest sub_ at or below
each address, the next one above, and any alias names of that function.
"""
import re
import sys
import bisect

SUB = re.compile(r'\bsub_([0-9A-Fa-f]{8})\b')


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    mp = argv[0]
    targets = [int(a, 16) for a in argv[1:]]
    addrs = set()
    with open(mp, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            for m in SUB.finditer(line):
                addrs.add(int(m.group(1), 16))
    srt = sorted(addrs)
    print('map %s: %d distinct sub_ addresses' % (mp, len(srt)))
    for t in targets:
        i = bisect.bisect_right(srt, t) - 1
        lo = srt[i] if i >= 0 else None
        hi = srt[i + 1] if i + 1 < len(srt) else None
        print('%08X: in sub_%08X (+0x%X); next sub_%08X' % (t, lo or 0, t - (lo or 0), hi or 0))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

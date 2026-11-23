#!/usr/bin/env python3
"""mapsym: targeted lookup of a few symbols in ONE linker map (single sequential read, no tree scan).

Usage: mapsym.py MAP SYM [SYM ...]
Prints every map line that has one of the SYMs or __imp__<SYM> as a whole token (the last token is
the defining object), so a hooked guest function shows its public in a host object (REX_HOOK) and
its __imp__ alias in a generated TU. Read-only.
"""
import sys


def main():
    path, syms = sys.argv[1], sys.argv[2:]
    want = set(syms) | {'__imp__' + s for s in syms}
    hits = {w: [] for w in want}
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            if 'sub_' not in line:
                continue
            if not any(s in line for s in syms):
                continue
            toks = line.split()
            for t in toks:
                if t in want:
                    hits[t].append(' '.join(toks))
    for s in syms:
        objs = {}
        for n in (s, '__imp__' + s):
            if hits[n]:
                for h in hits[n]:
                    print('%-24s %s' % (n, h))
                objs[n] = hits[n][0].split()[-1]
            else:
                print('%-24s <not in map>' % n)
        pub = objs.get(s, '')
        if not pub:
            kind = '?'
        elif 'legodimensions_recomp.' in pub:
            kind = 'guest (public in generated TU %s)' % pub
        else:
            kind = 'HOOKED (public in host object %s)' % pub
        print('  -> %s: %s' % (s, kind))
    return 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
# verify-bins.py (M2 successor, session 3): verify staged bin dirs against their MANIFEST.txt.
#
#   python build/agent2/session3/verify-bins.py <bin dir> [<bin dir> ...] [--out FILE]
#
# Every MANIFEST row (name TAB size TAB mtime TAB sha256 TAB source) must exist with that size and sha256, and every
# file in the dir (except MANIFEST.txt) must have a row. Read-only. Exit 0 = 0 FAIL.
import argparse, hashlib, os, sys, time


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('bins', nargs='+')
    ap.add_argument('--out')
    a = ap.parse_args()
    out, fails = [], 0
    say = lambda s: (out.append(s), print(s))
    say('# verify-bins %s' % time.strftime('%Y-%m-%d %H:%M:%S'))
    for b in a.bins:
        b = os.path.abspath(b)
        mf = os.path.join(b, 'MANIFEST.txt')
        if not os.path.isfile(mf):
            say('FAIL %s: no MANIFEST.txt' % b)
            fails += 1
            continue
        rows = {}
        with open(mf, encoding='utf-8', errors='replace') as f:
            for line in f:
                if line.startswith('#') or '\t' not in line:
                    continue
                c = line.rstrip('\r\n').split('\t')
                if len(c) >= 4:
                    rows[c[0].replace('/', os.sep)] = c
        files = sorted(os.path.relpath(os.path.join(dp, fn), b) for dp, _, fns in os.walk(b) for fn in fns
                       if not (dp == b and fn == 'MANIFEST.txt'))
        bf = 0
        for n in files:
            if n not in rows:
                say('  FAIL %s: extra file %s (no MANIFEST row)' % (os.path.basename(b), n))
                bf += 1
        for n, c in sorted(rows.items()):
            p = os.path.join(b, n)
            if not os.path.isfile(p):
                say('  FAIL %s: missing %s' % (os.path.basename(b), n))
                bf += 1
                continue
            if str(os.path.getsize(p)) != c[1] or sha(p) != c[3].upper():
                say('  FAIL %s: %s size/sha256 differs from its row' % (os.path.basename(b), n))
                bf += 1
        say('%s %s: %d rows, %d files, %d FAIL; MANIFEST sha256 %s' % ('PASS' if not bf else 'FAIL', b, len(rows),
                                                                      len(files), bf, sha(mf)))
        fails += bf
    say('RESULT: %d FAIL' % fails)
    if a.out:
        with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(out) + '\n')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())

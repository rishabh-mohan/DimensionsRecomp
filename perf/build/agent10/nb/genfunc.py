#!/usr/bin/env python3
"""genfunc: print a generated guest function body and mark addresses in it.

Usage: genfunc.py GENDIR FUNC_ADDR [--mark ADDR ...] [--all] [--max-lines N]
Finds the definition of sub_<FUNC_ADDR> in GENDIR/*.cpp with a bytes search
(DEFINE_REX_FUNC(sub_X), PPC_FUNC_IMPL(__imp__sub_X) or PPC_FUNC(sub_X)),
prints the body up to the next definition or the closing brace at column 0,
and tags every line that mentions a --mark address (hex, any case, with or
without 0x, e.g. "ctx.lr = 0x82BCE244" or "loc_82BCE240"). Stops after the
first definition unless --all. Read-only.
v2 (05:30): v1 only knew PPC_FUNC* and missed DEFINE_REX_FUNC (rexglue).
"""
import argparse, os, re, sys

DEF_KEYS = (b'DEFINE_REX_FUNC(%s)', b'PPC_FUNC_IMPL(__imp__%s)', b'PPC_FUNC(%s)')
NEXT_DEF = re.compile(rb'^(?:DEFINE_REX_FUNC\(|PPC_FUNC_IMPL\(|PPC_FUNC\()', re.M)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('gendir')
    ap.add_argument('func')
    ap.add_argument('--mark', nargs='*', default=[])
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--max-lines', type=int, default=4000)
    ap.add_argument('--tu', nargs='*', default=None,
                    help='only read legodimensions_recomp.<N>.cpp for these N (targeted read, no tree scan)')
    a = ap.parse_args()
    func = a.func.upper().replace('0X', '')
    name = ('sub_' + func).encode()
    keys = [k % name for k in DEF_KEYS]
    marks = [m.upper().replace('0X', '') for m in a.mark]
    mark_re = re.compile(r'(?i)\b(?:0x)?(?:loc_|sub_)?(' + '|'.join(marks) + r')\b') if marks else None
    found = 0
    scanned = 0
    files = (['legodimensions_recomp.%s.cpp' % n for n in a.tu] if a.tu is not None
             else sorted(os.listdir(a.gendir)))
    for fn in files:
        if not fn.endswith('.cpp') or not os.path.exists(os.path.join(a.gendir, fn)):
            continue
        p = os.path.join(a.gendir, fn)
        with open(p, 'rb') as f:
            data = f.read()
        scanned += 1
        if a.tu is not None:
            names = re.findall(rb'^DEFINE_REX_FUNC\((\w+)\)', data, re.M)
            print('-- %s: %d DEFINE_REX_FUNC, first %s, last %s' % (
                fn, len(names), names[0].decode() if names else '-', names[-1].decode() if names else '-'))
        for key in keys:
            k = data.find(key)
            if k < 0:
                continue
            ls = data.rfind(b'\n', 0, k) + 1
            le = data.find(b'\n', k)
            nxt = NEXT_DEF.search(data, le)
            end = nxt.start() if nxt else len(data)
            body = data[ls:end].replace(b'\r\n', b'\n').decode('utf-8', 'replace').splitlines()
            print('== %s:%d  (%d lines, key %s)' % (fn, data.count(b'\n', 0, ls) + 1, len(body), key.decode()))
            for i, ln in enumerate(body[:a.max_lines]):
                tag = ''
                if mark_re is not None:
                    hits = sorted({m.group(1).upper() for m in mark_re.finditer(ln)})
                    if hits:
                        tag = '   <<< ' + ','.join(hits)
                print('%5d  %s%s' % (i + 1, ln.rstrip(), tag))
            if len(body) > a.max_lines:
                print('... (%d more lines)' % (len(body) - a.max_lines))
            found += 1
            break
        if found and not a.all:
            break
    if not found:
        print('sub_%s: definition not found in %s (%d TUs scanned)' % (func, a.gendir, scanned))
    return 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
# pe-imports.py (Agent 2, board run 2 task #1): list the DLL imports (normal + delay-load) of PE files, read-only.
#   python build/agent2/s4b/pe-imports.py [--want NAME.dll] FILE...
# Prints one line per file: the imported DLL names (sorted, lower case); with --want, whether each file imports NAME.
import argparse, os, struct, sys


def imports(path):
    with open(path, 'rb') as f:
        data = f.read()
    pe = struct.unpack_from('<I', data, 0x3C)[0]
    if data[pe:pe + 4] != b'PE\0\0':
        raise ValueError('not a PE file')
    nsec, = struct.unpack_from('<H', data, pe + 6)
    optsz, = struct.unpack_from('<H', data, pe + 20)
    opt = pe + 24
    magic, = struct.unpack_from('<H', data, opt)
    dd = opt + (112 if magic == 0x20B else 96)
    secs = []
    so = opt + optsz
    for i in range(nsec):
        vsize, va, rsize, rptr = struct.unpack_from('<IIII', data, so + 40 * i + 8)
        secs.append((va, max(vsize, rsize), rptr))

    def off(rva):
        for va, sz, rptr in secs:
            if va <= rva < va + sz:
                return rva - va + rptr
        raise ValueError('rva %x not in a section' % rva)

    def cstr(rva):
        o = off(rva)
        return data[o:data.index(b'\0', o)].decode('ascii', 'replace')

    out = {}
    for idx, kind, step, name_at in ((1, 'import', 20, 12), (13, 'delay', 32, 4)):
        rva, size = struct.unpack_from('<II', data, dd + 8 * idx)
        if not rva:
            continue
        o = off(rva)
        while True:
            desc = data[o:o + step]
            if len(desc) < step or not any(desc):
                break
            nrva, = struct.unpack_from('<I', desc, name_at)
            if nrva:
                out[cstr(nrva).lower()] = kind
            o += step
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--want', default='')
    ap.add_argument('files', nargs='+')
    a = ap.parse_args()
    want = a.want.lower()
    for p in a.files:
        try:
            im = imports(p)
        except Exception as e:  # noqa: BLE001
            print('%s: ERROR %s' % (p, e))
            continue
        names = ' '.join('%s%s' % (n, '(delay)' if k == 'delay' else '') for n, k in sorted(im.items()))
        tag = ''
        if want:
            tag = ' [%s %s]' % ('IMPORTS' if want in im else 'no', want)
        print('%s: %d DLLs%s: %s' % (os.path.relpath(p), len(im), tag, names))
    return 0


if __name__ == '__main__':
    sys.exit(main())

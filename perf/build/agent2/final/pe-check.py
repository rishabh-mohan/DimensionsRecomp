#!/usr/bin/env python3
# pe-check.py (M2, 2026-11-25): D5 PE checks of final-defaults rating C20B6FDB. Read-only.
#
#   python build/agent2/final/pe-check.py --new NEW.dll|exe --ref REF.dll|exe [--allow-add DLL!SUBSTR ...]
#          [--added-exported-by DLL=PATH] [--ref-count DLL=N]
#
# PE32+ only. Compares:
#   exports (names, sorted) NEW == REF;
#   imports (per DLL, by name or #ordinal; normal and delay-load tables) NEW == REF, except that each --allow-add
#   DLL!SUBSTR must match exactly one name added in NEW for that DLL and there are no other added or removed names;
#   --added-exported-by DLL=PATH: every name added for DLL must be an export of PATH (e.g. the devoff4b rexruntime.dll);
#   --ref-count DLL=N: REF imports exactly N names from DLL (e.g. rexruntime.dll=115).
# Exit 0 = PASS, 1 = FAIL. Prints one PASS/FAIL line per check, then RESULT.
import argparse, struct, sys


class PE:
    def __init__(self, path):
        self.path = path
        self.d = d = open(path, 'rb').read()
        pe = struct.unpack_from('<I', d, 0x3C)[0]
        if d[pe:pe + 4] != b'PE\0\0':
            raise ValueError('%s: not a PE file' % path)
        nsec = struct.unpack_from('<H', d, pe + 6)[0]
        optsz = struct.unpack_from('<H', d, pe + 20)[0]
        self.opt = opt = pe + 24
        if struct.unpack_from('<H', d, opt)[0] != 0x20B:
            raise ValueError('%s: not PE32+' % path)
        self.ndir = struct.unpack_from('<I', d, opt + 108)[0]
        self.secs = []
        for i in range(nsec):
            s = opt + optsz + 40 * i
            vs, va, rs, ra = struct.unpack_from('<IIII', d, s + 8)
            self.secs.append((va, max(vs, rs), ra))

    def dir(self, i):
        if i >= self.ndir:
            return 0, 0
        return struct.unpack_from('<II', self.d, self.opt + 112 + 8 * i)

    def off(self, rva):
        for va, sz, ra in self.secs:
            if va <= rva < va + sz:
                return rva - va + ra
        raise ValueError('%s: RVA 0x%X not in any section' % (self.path, rva))

    def cstr(self, rva):
        o = self.off(rva)
        return self.d[o:self.d.index(b'\0', o)].decode('latin-1')

    def exports(self):
        rva, _ = self.dir(0)
        if not rva:
            return []
        e = self.off(rva)
        n = struct.unpack_from('<I', self.d, e + 24)[0]
        names = self.off(struct.unpack_from('<I', self.d, e + 32)[0])
        return sorted(self.cstr(struct.unpack_from('<I', self.d, names + 4 * i)[0]) for i in range(n))

    def _thunks(self, rva):
        out, o = [], self.off(rva)
        while True:
            t = struct.unpack_from('<Q', self.d, o)[0]
            if not t:
                return out
            out.append('#%d' % (t & 0xFFFF) if t >> 63 else self.cstr((t & 0x7FFFFFFF) + 2))
            o += 8

    def imports(self):
        imp = {}
        rva, _ = self.dir(1)
        o = self.off(rva) if rva else None
        while o is not None:
            oft, _, _, name, ft = struct.unpack_from('<IIIII', self.d, o)
            if not (oft or name or ft):
                break
            imp.setdefault(self.cstr(name).lower(), []).extend(self._thunks(oft or ft))
            o += 20
        rva, _ = self.dir(13)  # delay-load
        o = self.off(rva) if rva else None
        while o is not None:
            attr, name, _, _, intr = struct.unpack_from('<IIIII', self.d, o)
            if not (name or intr):
                break
            imp.setdefault('delay:' + self.cstr(name).lower(), []).extend(self._thunks(intr))
            o += 32
        return {k: sorted(v) for k, v in imp.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--new', required=True)
    ap.add_argument('--ref', required=True)
    ap.add_argument('--allow-add', action='append', default=[])
    ap.add_argument('--added-exported-by', action='append', default=[])
    ap.add_argument('--ref-count', action='append', default=[])
    a = ap.parse_args()
    fails = []

    def check(what, ok, detail=''):
        print('%s %s%s' % ('PASS' if ok else 'FAIL', what, (': ' + detail) if detail else ''), flush=True)
        if not ok:
            fails.append(what)

    new, ref = PE(a.new), PE(a.ref)
    en, er = new.exports(), ref.exports()
    check('exports equal (%d new, %d ref)' % (len(en), len(er)), en == er,
          'added %s; removed %s' % (sorted(set(en) - set(er))[:10], sorted(set(er) - set(en))[:10]))
    inew, iref = new.imports(), ref.imports()
    print('imports: new %s' % ', '.join('%s %d' % (k, len(v)) for k, v in sorted(inew.items())))
    print('imports: ref %s' % ', '.join('%s %d' % (k, len(v)) for k, v in sorted(iref.items())))
    allow = {}
    for s in a.allow_add:
        dll, sub = s.split('!', 1)
        allow.setdefault(dll.lower(), []).append(sub)
    for rc in a.ref_count:
        dll, n = rc.split('=')
        got = len(iref.get(dll.lower(), []))
        check('ref imports %d name(s) from %s (expect %s)' % (got, dll, n), got == int(n))
    check('same imported DLL set', sorted(inew) == sorted(iref),
          'added %s; removed %s' % (sorted(set(inew) - set(iref)), sorted(set(iref) - set(inew))))
    for dll in sorted(set(inew) | set(iref)):
        n, r = inew.get(dll, []), iref.get(dll, [])
        added = sorted(set(n) - set(r))
        removed = sorted(set(r) - set(n))
        dup = len(n) != len(set(n)) or len(r) != len(set(r))
        subs = allow.get(dll, [])
        if not subs:
            check('imports from %s unchanged (%d)' % (dll, len(r)), not added and not removed and not dup,
                  'added %s; removed %s' % (added[:10], removed[:10]))
            continue
        ok = not removed and not dup and len(added) == len(subs)
        for sub in subs:
            m = [x for x in added if sub in x]
            ok = ok and len(m) == 1
            print('  allowed add %s!%s -> %s' % (dll, sub, m))
        check('imports from %s == ref %d + exactly %d allowed (%s)' % (dll, len(r), len(subs), ', '.join(subs)), ok,
              'added %s; removed %s' % (added, removed))
        for spec in a.added_exported_by:
            d2, path = spec.split('=', 1)
            if d2.lower() == dll:
                ex = set(PE(path).exports())
                miss = [x for x in added if x not in ex]
                check('added %s imports are exports of %s' % (dll, path), not miss, str(miss))
    print('RESULT: %s' % ('PASS' if not fails else 'FAIL (%d: %s)' % (len(fails), '; '.join(fails))))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())

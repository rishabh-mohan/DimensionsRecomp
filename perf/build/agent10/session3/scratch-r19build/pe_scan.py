"""Read-only PE scan: list exports of a DLL, and which names each given PE imports from a named DLL."""
import struct, sys

def load(path):
    d = open(path, 'rb').read()
    pe = struct.unpack_from('<I', d, 0x3C)[0]
    nsec = struct.unpack_from('<H', d, pe + 6)[0]
    optsz = struct.unpack_from('<H', d, pe + 20)[0]
    opt = pe + 24
    magic = struct.unpack_from('<H', d, opt)[0]
    ddoff = opt + (112 if magic == 0x20B else 96)
    dirs = [struct.unpack_from('<II', d, ddoff + 8 * i) for i in range(16)]
    secs = []
    so = opt + optsz
    for i in range(nsec):
        vs, va, rs, rp = struct.unpack_from('<IIII', d, so + 40 * i + 8)
        secs.append((va, max(vs, rs), rp))
    def off(rva):
        for va, sz, rp in secs:
            if va <= rva < va + sz:
                return rva - va + rp
        raise ValueError(hex(rva))
    def cstr(rva):
        o = off(rva)
        return d[o:d.index(b'\0', o)].decode('latin1')
    return d, dirs, off, cstr, magic

def exports(path):
    d, dirs, off, cstr, _ = load(path)
    rva, sz = dirs[0]
    if not rva:
        return []
    o = off(rva)
    nnames, faddr, naddr = struct.unpack_from('<I', d, o + 24)[0], 0, struct.unpack_from('<I', d, o + 32)[0]
    return sorted(cstr(struct.unpack_from('<I', d, off(naddr) + 4 * i)[0]) for i in range(nnames))

def imports_from(path, dll):
    d, dirs, off, cstr, magic = load(path)
    rva, sz = dirs[1]
    out = []
    if not rva:
        return out
    o = off(rva)
    while True:
        oft, ts, fc, name, ft = struct.unpack_from('<IIIII', d, o)
        if not name:
            break
        if cstr(name).lower() == dll.lower():
            t = off(oft or ft)
            step, flag = (8, 1 << 63) if magic == 0x20B else (4, 1 << 31)
            while True:
                v = struct.unpack_from('<Q' if step == 8 else '<I', d, t)[0]
                if not v:
                    break
                out.append('#%d' % (v & 0xFFFF) if v & flag else cstr((v & 0x7FFFFFFF) + 2))
                t += step
        o += 20
    return sorted(out)

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'exports':
        e = exports(sys.argv[2])
        print('exports', len(e))
        for n in e:
            print('   ', n)
    else:
        dll = sys.argv[2]
        for p in sys.argv[3:]:
            i = imports_from(p, dll)
            print(p, 'imports from', dll, len(i))
            for n in i:
                print('   ', n)

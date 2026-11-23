"""handleinfo.py -- read-only: minidump handle details + nearest DLL exports (task #16 follow-up, 22:33).

Usage:
  python -B build/agent6/hang/handleinfo.py <dump> <hex handle>[,<hex handle>...] [--exports DLL=0xRVA,0xRVA ...]

For each handle: the object type, its name, handle and pointer counts, and the object info that the dump
recorded (event type and state, semaphore count, mutant state). DLL is a file name in C:\\Windows\\System32
or a path; for each RVA it prints the nearest export at or below it. Reads only; writes nothing.
"""
import collections
import os
import struct
import sys


def rd(f, off, n):
    f.seek(off)
    return f.read(n)


def mstr(f, rva):
    if not rva:
        return ""
    (ln,) = struct.unpack("<I", rd(f, rva, 4))
    return rd(f, rva + 4, ln).decode("utf-16-le", "replace")


INFO = {0: "none", 1: "thread1", 2: "mutant1", 3: "mutant2", 4: "process1", 5: "process2",
        6: "event1", 7: "section1", 8: "semaphore1"}


def handles(path, want):
    with open(path, "rb") as f:
        _sig, _ver, nstreams, dir_rva = struct.unpack("<IIII", rd(f, 0, 16))
        hs = None
        for i in range(nstreams):
            st, size, rva = struct.unpack("<III", rd(f, dir_rva + 12 * i, 12))
            if st == 12:
                hs = (size, rva)
        if not hs:
            print("  no HandleData stream")
            return
        _size, rva = hs
        hsz, dsz, n, _ = struct.unpack("<IIII", rd(f, rva, 16))
        print(f"  handle stream: header={hsz} descriptor={dsz} handles={n}")
        types = collections.Counter()
        found = set()
        for i in range(n):
            d = rd(f, rva + hsz + i * dsz, dsz)
            h, trva, orva, attr, acc, hcnt, pcnt = struct.unpack_from("<QIIIIII", d, 0)
            oinfo = struct.unpack_from("<I", d, 32)[0] if dsz >= 40 else 0
            tname = mstr(f, trva)
            types[tname] += 1
            if h not in want:
                continue
            found.add(h)
            oname = mstr(f, orva)
            print(f"  handle 0x{h:X}: type={tname!r} name={oname!r} attributes=0x{attr:X} access=0x{acc:X} "
                  f"handle_count={hcnt} pointer_count={pcnt}")
            r = oinfo
            hops = 0
            while r and hops < 8:
                hops += 1
                nxt, itype, isz = struct.unpack("<III", rd(f, r, 12))
                data = rd(f, r + 12, isz)
                if itype == 6 and isz >= 8:
                    et, es = struct.unpack_from("<Ii", data, 0)
                    kind = "notification (manual reset)" if et == 0 else "synchronization (auto reset)"
                    print(f"    event: {kind}, state={es} ({'signaled' if es else 'not signaled'})")
                elif itype == 8 and isz >= 8:
                    cur, mx = struct.unpack_from("<ii", data, 0)
                    print(f"    semaphore: count={cur} max={mx}")
                else:
                    print(f"    info {INFO.get(itype, itype)} size={isz}: {data[:32].hex()}")
                r = nxt
        for h in sorted(want - found):
            print(f"  handle 0x{h:X}: not in the dump's handle table")
        print("  handle types: " + ", ".join(f"{k or '?'}={v}" for k, v in types.most_common(12)))


def exports(dll):
    path = dll if os.path.isabs(dll) or os.sep in dll or "/" in dll else os.path.join(r"C:\Windows\System32", dll)
    with open(path, "rb") as f:
        data = f.read()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    optsz = struct.unpack_from("<H", data, pe + 20)[0]
    opt = pe + 24
    magic = struct.unpack_from("<H", data, opt)[0]
    ts = struct.unpack_from("<I", data, pe + 8)[0]
    dd = opt + (112 if magic == 0x20B else 96)
    exp_rva, _exp_size = struct.unpack_from("<II", data, dd)
    secs = []
    for i in range(nsec):
        s = opt + optsz + 40 * i
        vsz, va, rawsz, rawptr = struct.unpack_from("<IIII", data, s + 8)
        secs.append((va, max(vsz, rawsz), rawptr))

    def off(rva):
        for va, sz, raw in secs:
            if va <= rva < va + sz:
                return rva - va + raw
        raise ValueError(hex(rva))

    e = off(exp_rva)
    nfun, nnames, afun, anames, aords = struct.unpack_from("<IIIII", data, e + 20)
    funcs = [struct.unpack_from("<I", data, off(afun) + 4 * i)[0] for i in range(nfun)]
    names = {}
    for i in range(nnames):
        nrva = struct.unpack_from("<I", data, off(anames) + 4 * i)[0]
        ordi = struct.unpack_from("<H", data, off(aords) + 2 * i)[0]
        o = off(nrva)
        names[ordi] = data[o:data.index(b"\0", o)].decode("ascii", "replace")
    table = sorted((rva, names.get(i, f"#{i}")) for i, rva in enumerate(funcs) if rva)
    return path, ts, table


def nearest(table, rva):
    best = None
    for frva, name in table:
        if frva <= rva:
            best = (frva, name)
        else:
            break
    return best


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    dump = argv[0]
    want = {int(x, 16) for x in argv[1].split(",") if x}
    print(f"dump {dump}")
    handles(dump, want)
    if "--exports" in argv:
        for spec in argv[argv.index("--exports") + 1:]:
            dll, _, rvas = spec.partition("=")
            path, ts, table = exports(dll)
            print(f"  exports of {path} (timestamp {ts:08X}, {len(table)} exports):")
            for r in rvas.split(","):
                rva = int(r, 16)
                hit = nearest(table, rva)
                print(f"    +0x{rva:X}: " + (f"{hit[1]}+0x{rva - hit[0]:X}" if hit else "(below first export)"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

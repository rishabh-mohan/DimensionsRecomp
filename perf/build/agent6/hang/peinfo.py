"""peinfo.py - print the RSDS (PDB path/guid/age) of PE files; read-only, stdlib only.
usage: python -B peinfo.py <pe> [<pe> ...]   (missing files are skipped)
"""
import os
import struct
import sys


def rsds(path):
    with open(path, "rb") as f:
        data = f.read()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe:pe + 4] != b"PE\0\0":
        return []
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    optsz = struct.unpack_from("<H", data, pe + 20)[0]
    opt = pe + 24
    magic = struct.unpack_from("<H", data, opt)[0]
    dd = opt + (112 if magic == 0x20B else 96)
    dbg_rva, dbg_size = struct.unpack_from("<II", data, dd + 6 * 8)
    secs = []
    so = opt + optsz
    for i in range(nsec):
        _name, vsize, va, rawsize, rawptr = struct.unpack_from("<8sIIII", data, so + i * 40)
        secs.append((va, max(vsize, rawsize), rawptr))

    def r2o(rva):
        for va, sz, rp in secs:
            if va <= rva < va + sz:
                return rva - va + rp
        return None

    off = r2o(dbg_rva)
    out = []
    if off is None:
        return out
    for i in range(dbg_size // 28):
        _ch, ts, _maj, _mi, typ, sz, _rva, ptr = struct.unpack_from("<IIHHIIII", data, off + i * 28)
        if typ == 2:
            d = data[ptr:ptr + sz]
            if d[:4] == b"RSDS":
                age = struct.unpack_from("<I", d, 20)[0]
                p = d[24:].split(b"\0")[0].decode("utf-8", "replace")
                out.append((p, d[4:20].hex(), age, ts))
    return out


for p in sys.argv[1:]:
    if not os.path.exists(p):
        print(f"{p}: not found")
        continue
    for path, guid, age, ts in rsds(p):
        st = "exists" if os.path.exists(path) else "MISSING"
        print(f"{p}: ts={ts:08X} pdb={path} [{st}] guid={guid} age={age}")

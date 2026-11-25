"""Read-only scan of .ninja_deps files: list outputs whose latest deps include given header names."""
import struct, sys, collections

def read_deps(path):
    data = open(path, 'rb').read()
    sig = b'# ninjadeps\n'
    assert data.startswith(sig), 'bad signature'
    pos = len(sig)
    (version,) = struct.unpack_from('<i', data, pos); pos += 4
    paths = []
    deps = {}
    while pos + 4 <= len(data):
        (size,) = struct.unpack_from('<I', data, pos); pos += 4
        is_deps = bool(size & 0x80000000)
        size &= 0x7FFFFFFF
        rec = data[pos:pos + size]; pos += size
        if is_deps:
            out_id = struct.unpack_from('<i', rec, 0)[0]
            hdr = 12 if version >= 4 else 8
            n = (size - hdr) // 4
            ins = struct.unpack_from('<%di' % n, rec, hdr)
            deps[out_id] = ins
        else:
            name = rec[:-4].rstrip(b'\0').decode('utf-8', 'replace')
            paths.append(name)
    return version, paths, deps

def main():
    pats = [p.lower() for p in sys.argv[2:]]
    version, paths, deps = read_deps(sys.argv[1])
    print('file', sys.argv[1], 'version', version, 'paths', len(paths), 'outputs-with-deps', len(deps))
    hits = collections.defaultdict(set)
    pch_outputs = set()
    for out_id, ins in deps.items():
        out = paths[out_id]
        for i in ins:
            p = paths[i].lower().replace('\\', '/')
            for pat in pats:
                if p.endswith(pat):
                    hits[pat].add(out)
            if p.endswith('.pch') or 'cmake_pch' in p:
                pch_outputs.add(out)
    for pat in pats:
        outs = sorted(hits[pat])
        print('pattern', pat, 'outputs', len(outs))
        for o in outs:
            print('   ', o)
    print('outputs depending on a pch/cmake_pch:', len(pch_outputs))
    for o in sorted(pch_outputs)[:20]:
        print('   ', o)
    # headers matching the basename anywhere (any directory), to catch copies (install/include etc.)
    for pat in pats:
        base = pat.rsplit('/', 1)[-1]
        cands = sorted({p for p in paths if p.lower().replace('\\', '/').endswith('/' + base)})
        print('paths ending in', base, ':', len(cands))
        for c in cands:
            print('   ', c)

if __name__ == '__main__':
    main()

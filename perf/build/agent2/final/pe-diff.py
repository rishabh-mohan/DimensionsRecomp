#!/usr/bin/env python3
# pe-diff.py (M2, 2026-11-25): D3 of rating C20B6FDB (full-SDK fallback). Lists EVERY differing byte range between
# two PE files and classifies it: 'TimeDateStamp' (COFF header, export dir, debug dir entries), 'debug-dir' (inside a
# debug directory entry or the data it points to), else 'OTHER (section X @ RVA)'. Read-only.
#
#   python build/agent2/final/pe-diff.py NEW REF
# Exit 0 = only TimeDateStamp/debug-dir ranges (or identical), 1 = any OTHER range or a size difference.
import struct, sys


def layout(d):
    pe = struct.unpack_from('<I', d, 0x3C)[0]
    nsec = struct.unpack_from('<H', d, pe + 6)[0]
    optsz = struct.unpack_from('<H', d, pe + 20)[0]
    opt = pe + 24
    secs = []
    for i in range(nsec):
        s = opt + optsz + 40 * i
        nm = d[s:s + 8].rstrip(b'\0').decode('latin-1')
        vs, va, rs, ra = struct.unpack_from('<IIII', d, s + 8)
        secs.append((nm, va, max(vs, rs), ra, rs))

    def off(rva):
        for _, va, sz, ra, _ in secs:
            if va <= rva < va + sz:
                return rva - va + ra
        return None
    fields = {pe + 8: 'COFF TimeDateStamp'}
    ranges = []
    erva = struct.unpack_from('<I', d, opt + 112)[0]
    if erva and off(erva) is not None:
        fields[off(erva) + 4] = 'export dir TimeDateStamp'
    drva, dsz = struct.unpack_from('<II', d, opt + 112 + 8 * 6)
    if drva and off(drva) is not None:
        o = off(drva)
        ranges.append((o, o + dsz, 'debug-dir'))
        for k in range(dsz // 28):
            e = o + 28 * k
            fields[e + 4] = 'debug entry TimeDateStamp'
            sz, _, praw = struct.unpack_from('<III', d, e + 16)
            if praw:
                ranges.append((praw, praw + sz, 'debug-dir data'))
    return secs, fields, ranges


def main():
    new, ref = (open(p, 'rb').read() for p in sys.argv[1:3])
    if len(new) != len(ref):
        print('FAIL size %d vs %d B' % (len(new), len(ref)))
        return 1
    secs, fields, ranges = layout(ref)
    runs, j, n = [], 0, len(new)
    CH = 1 << 16
    for c0 in range(0, n, CH):
        if new[c0:c0 + CH] == ref[c0:c0 + CH]:
            continue
        j = max(j, c0)
        while j < min(c0 + CH, n):
            if new[j] != ref[j]:
                k = j
                while k < n and new[k] != ref[k]:
                    k += 1
                runs.append((j, k))
                j = k
            else:
                j += 1
    bad = 0
    for s, e in runs:
        cls = next((nm for f, nm in fields.items() if f <= s and e <= f + 4), None)
        cls = cls or next((nm for a, b, nm in ranges if a <= s and e <= b), None)
        if not cls:
            sec = next(('%s @ RVA 0x%X' % (nm, s - ra + va) for nm, va, _, ra, rs in secs if ra <= s < ra + rs),
                       'headers')
            cls = 'OTHER (%s)' % sec
            bad += 1
        print('0x%08X-0x%08X %5d B  %s' % (s, e, e - s, cls))
    print('RESULT: %s (%d range(s), %d OTHER)' % ('PASS' if not bad else 'FAIL', len(runs), bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())

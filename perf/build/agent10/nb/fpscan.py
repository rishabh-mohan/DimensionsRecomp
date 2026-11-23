"""fpscan.py: find native GPU fingerprints and LEGODX1 shader-pack headers in exe files.

Usage: python fpscan.py EXE [EXE ...]
For each exe: count each 16-hex fingerprint seen after 'LEGO Dimensions native GPU ',
list every 'LEGODX1\\0' magic with the 16 bytes at +32 (the pack's build fingerprint),
and count raw occurrences of the fingerprints given with --fp.
Read-only.
"""
import argparse
import mmap
import re
import sys


def scan(path, fps):
    out = []
    with open(path, 'rb') as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        try:
            out.append(f'{path}: {len(mm):,} B')
            seen = {}
            for m in re.finditer(rb'LEGO Dimensions native GPU ([0-9a-f]{16})', mm):
                seen.setdefault(m.group(1).decode(), []).append(m.start())
            for k, v in seen.items():
                out.append(f'  build string fingerprint {k}: {len(v)}x at ' + ', '.join(hex(x) for x in v[:6]))
            if not seen:
                out.append('  build string fingerprint: none')
            packs = [m.start() for m in re.finditer(rb'LEGODX1\x00', mm)]
            out.append(f'  LEGODX1 magic: {len(packs)}x')
            for p in packs[:20]:
                hdr = mm[p:p + 160]
                ver = int.from_bytes(hdr[8:12], 'little') if len(hdr) >= 12 else -1
                abi = int.from_bytes(hdr[12:16], 'little') if len(hdr) >= 16 else -1
                fpb = hdr[32:48]
                try:
                    fps_s = fpb.decode('ascii')
                except UnicodeDecodeError:
                    fps_s = fpb.hex()
                out.append(f'    at {hex(p)}: version {ver} abi {abi} fingerprint@+32 {fps_s!r}')
            for fp in fps:
                n = len(re.findall(re.escape(fp.encode()), mm))
                out.append(f'  raw "{fp}": {n}x')
        finally:
            mm.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('exe', nargs='+')
    ap.add_argument('--fp', action='append', default=[])
    a = ap.parse_args()
    for e in a.exe:
        print('\n'.join(scan(e, a.fp)))
    return 0


if __name__ == '__main__':
    sys.exit(main())

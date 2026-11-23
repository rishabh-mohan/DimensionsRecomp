"""C3 detail for the r6 miss-cache smoke: where the (guest, stage) sets differ.

For each unrecognized_shader (guest, stage) that is only in OFF or only in ON,
print rows, frames, first/last elapsed s and frame, so relocated heap shaders
can be paired by route time and rows per frame.
"""
import re
import sys
from collections import defaultdict

RX = re.compile(r'guest= (\d+) stage= (\d+)')


def scan(path):
    d = defaultdict(lambda: [0, set(), None, None, None, None])  # rows, frames, first_ms, first_f, last_ms, last_f
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        next(f, None)
        for line in f:
            parts = line.split('\t', 4)
            if len(parts) < 5 or parts[2] != 'unrecognized_shader':
                continue
            m = RX.search(parts[4])
            if not m:
                continue
            key = (int(m.group(1)), int(m.group(2)))
            ms = float(parts[0])
            fr = int(parts[1])
            e = d[key]
            e[0] += 1
            e[1].add(fr)
            if e[2] is None:
                e[2], e[3] = ms, fr
            e[4], e[5] = ms, fr
    return d


def main():
    off_p, on_p = sys.argv[1], sys.argv[2]
    off, on = scan(off_p), scan(on_p)
    only_off = sorted(set(off) - set(on), key=lambda k: off[k][2])
    only_on = sorted(set(on) - set(off), key=lambda k: on[k][2])
    st = {6: 'VS', 7: 'PS'}

    def show(tag, d, keys):
        print(f'{tag}-only ({len(keys)}):')
        for k in keys:
            e = d[k]
            nf = len(e[1])
            print(f'  {st.get(k[1], k[1])} 0x{k[0]:08X}  rows {e[0]:6d} frames {nf:6d} ({e[0] / nf:.2f}/frame)'
                  f'  first {e[2] / 1000.0:7.1f} s (f{e[3]})  last {e[4] / 1000.0:7.1f} s (f{e[5]})')

    show('OFF', off, only_off)
    show('ON', on, only_on)
    print('partners (in both):')
    for g in (0xAC4AF3A4, 0xAC5AFEBC, 0xAC4AF1C8, 0xAC5AFDE0):
        for s in (6, 7):
            k = (g, s)
            if k in off and k in on:
                for tag, d in (('OFF', off), ('ON', on)):
                    e = d[k]
                    print(f'  {tag} {st[s]} 0x{g:08X} rows {e[0]} frames {len(e[1])} first {e[2] / 1000.0:.1f} s'
                          f' last {e[4] / 1000.0:.1f} s')
    print(f'sets: OFF {len(off)} keys, ON {len(on)} keys, common {len(set(off) & set(on))}')


if __name__ == '__main__':
    main()

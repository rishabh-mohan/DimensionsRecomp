"""M16 CG7: per-window missing-draw table. Usage: cg7_win.py <events.tsv> name:lo_ms:hi_ms [...]
For each window: frames, draw_missing totals, and per (last unrecognized VS, last unrecognized PS) pair at each
draw_missing event: count, VS-missing, PS-missing, first/last (frame, ms)."""
import collections, ctypes, re, sys
k = ctypes.windll.kernel32
k.SetPriorityClass(k.GetCurrentProcess(), 0x00004000)  # BELOW_NORMAL
P = sys.argv[1]
W = []
for a in sys.argv[2:]:
    n, lo, hi = a.split(':')
    W.append((n, float(lo), float(hi)))
G = re.compile(r'guest(?:_vs|_ps)?=\s*(\d+)')
S = re.compile(r'stage=\s*(\d+)')
frames = collections.Counter()
tot = collections.Counter()
pairs = {n: {} for n, _, _ in W}
last = {6: None, 7: None}
with open(P, 'rb') as f:
    for l in f:
        p = l.rstrip(b'\r\n').split(b'\t', 4)
        if len(p) < 5:
            continue
        e = p[2]
        if e not in (b'frame', b'unrecognized_shader', b'draw_missing_vertex_shader', b'draw_missing_pixel_shader'):
            continue
        try:
            ts = float(p[0]); fr = int(p[1])
        except ValueError:
            continue
        d = p[4].decode('ascii', 'replace')
        if e == b'unrecognized_shader':
            g = G.search(d); s = S.search(d)
            if g and s:
                last[int(s.group(1))] = int(g.group(1))
            continue
        for n, lo, hi in W:
            if lo <= ts <= hi:
                if e == b'frame':
                    frames[n] += 1
                    continue
                vs = e == b'draw_missing_vertex_shader'
                tot[(n, 'VS' if vs else 'PS')] += 1
                key = (last[6], last[7])
                r = pairs[n].setdefault(key, [0, 0, 0, (fr, ts), (fr, ts)])
                r[0] += 1; r[1 if vs else 2] += 1; r[4] = (fr, ts)
print('== trace', P)
for n, lo, hi in W:
    print('== window %s [%.0f, %.0f] ms: frames %d, draw_missing VS %d PS %d' % (
        n, lo, hi, frames[n], tot[(n, 'VS')], tot[(n, 'PS')]))
    print('   %-9s %-9s %7s %7s %7s  %-22s %-22s' % ('VS', 'PS', 'draws', 'VSmiss', 'PSmiss', 'first(frame,ms)', 'last'))
    for (v, ps), (c, a, b, f0, f1) in sorted(pairs[n].items(), key=lambda x: -x[1][0]):
        fmt = lambda x: '%08X' % x if x is not None else '-'
        print('   %-9s %-9s %7d %7d %7d  %-22s %-22s' % (fmt(v), fmt(ps), c, a, b,
              '%d,%.1f' % f0, '%d,%.1f' % f1))

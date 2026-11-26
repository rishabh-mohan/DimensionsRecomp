"""M16 CG7 read-only trace scan: event histogram, raw samples, per-guest miss/unrecognized tallies, inserts,
identity events. Usage: cg7_scan.py <events.tsv> [<guest hex> ...]  (guest list = also dump every event for them,
max 3 samples per event type)."""
import collections, ctypes, re, sys
k = ctypes.windll.kernel32
k.SetPriorityClass(k.GetCurrentProcess(), 0x00004000)  # BELOW_NORMAL
P = sys.argv[1]
WANT = {int(x, 16) for x in sys.argv[2:]}
G = re.compile(r'guest(?:_vs|_ps)?=\s*(\d+)')
hist, samp = collections.Counter(), collections.defaultdict(list)
per = {}  # (event, guest) -> [count, first(frame,ts), last]
raw_ins, raw_id = [], []
wsamp = collections.defaultdict(list)
skip = {b'texture_fetch_changed', b'texture_color_authority', b'texture_header_refresh', b'texture_upload_changed',
        b'frame'}
first_frame = last_frame = None
with open(P, 'rb') as f:
    for l in f:
        p = l.rstrip(b'\r\n').split(b'\t', 4)
        if len(p) < 4:
            continue
        e = p[2]
        hist[e] += 1
        if e == b'frame':
            if first_frame is None:
                first_frame = (p[0], p[1])
            last_frame = (p[0], p[1])
        if e in skip:
            continue
        d = p[4].decode('ascii', 'replace') if len(p) > 4 else ''
        if len(samp[e]) < 2:
            samp[e].append(l.decode('ascii', 'replace').rstrip())
        if e == b'shader_miss_cache_insert':
            raw_ins.append(l.decode('ascii', 'replace').rstrip())
        if b'identity' in e:
            raw_id.append(l.decode('ascii', 'replace').rstrip())
        m = G.search(d)
        if m:
            g = int(m.group(1))
            key = (e.decode(), g)
            fr, ts = int(p[1]), float(p[0])
            if key not in per:
                per[key] = [0, (fr, ts), (fr, ts)]
            per[key][0] += 1
            per[key][2] = (fr, ts)
            if g in WANT and len(wsamp[key]) < 3:
                wsamp[key].append(l.decode('ascii', 'replace').rstrip())
print('== trace', P)
print('first frame', first_frame, 'last frame', last_frame)
for e, n in sorted(hist.items(), key=lambda x: -x[1]):
    print('  %10d %s' % (n, e.decode('ascii', 'replace')))
print('== samples')
for e, s in samp.items():
    for x in s:
        print('  ', x[:300])
print('== per (event, guest): count, first (frame, ts), last  [draw_missing and unrecognized only, sorted by event,count]')
for (e, g), (n, a, b) in sorted(per.items(), key=lambda x: (x[0][0], -x[1][0])):
    if e.startswith('draw_missing') or e == 'unrecognized_shader':
        print('  %-28s %08X %7d first %s last %s' % (e, g, n, a, b))
print('== inserts (%d)' % len(raw_ins))
for x in raw_ins:
    print('  ', x[:300])
print('== identity events (%d)' % len(raw_id))
for x in raw_id[:200]:
    print('  ', x[:300])
if WANT:
    print('== wanted guest samples')
    for key, s in wsamp.items():
        for x in s:
            print('  ', x[:300])

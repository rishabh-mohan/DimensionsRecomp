"""Dropped native draws over time from a native trace events.tsv (read-only, Agent 4 task #29).

usage: missing_timeline.py EVENTS_TSV [BUCKET_S]
Per bucket of trace time (elapsed_ms ~ time since the first frame): frames, median draw_calls,
draw_missing_vertex_shader / draw_missing_pixel_shader counts and the guest addresses involved.
"""
import collections
import statistics
import sys

path = sys.argv[1]
bucket_s = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
draws = collections.defaultdict(list)
miss_vs = collections.Counter()
miss_ps = collections.Counter()
addrs = collections.defaultdict(collections.Counter)
tot = collections.Counter()
first_seen = {}
with open(path, encoding='utf-8', errors='replace') as f:
    next(f)
    for line in f:
        parts = line.rstrip('\r\n').split('\t')
        if len(parts) < 5:
            continue
        ev = parts[2]
        if ev not in ('frame', 'draw_missing_vertex_shader', 'draw_missing_pixel_shader'):
            continue
        try:
            t = float(parts[0]) / 1000.0
        except ValueError:
            continue
        b = int(t // bucket_s)
        det = parts[4]
        if ev == 'frame':
            for tok_i, tok in enumerate(det.split()):
                if tok == 'draw_calls=':
                    try:
                        draws[b].append(float(det.split()[tok_i + 1]))
                    except (IndexError, ValueError):
                        pass
                    break
            continue
        key = det.split('=')[0].strip()
        try:
            a = int(det.split('=')[1].split()[0])
        except (IndexError, ValueError):
            a = -1
        name = '%s:%08X' % (key, a & 0xFFFFFFFF)
        (miss_vs if ev.endswith('vertex_shader') else miss_ps)[b] += 1
        addrs[b][name] += 1
        tot[name] += 1
        first_seen.setdefault(name, t)

print('totals:', ', '.join('%s=%d (first %.1f s)' % (k, v, first_seen[k]) for k, v in tot.most_common()))
for b in sorted(set(draws) | set(miss_vs) | set(miss_ps)):
    d = draws.get(b, [])
    nf = len(d)
    print('%6.0f-%-6.0f frames=%5d draws p50=%7.1f  miss_vs=%6d miss_ps=%6d  per_frame=%6.1f  %s' % (
        b * bucket_s, (b + 1) * bucket_s, nf, statistics.median(d) if d else -1, miss_vs[b], miss_ps[b],
        (miss_vs[b] + miss_ps[b]) / nf if nf else -1,
        ' '.join('%s=%d' % (k.split(':')[1], v) for k, v in addrs[b].most_common(4))))

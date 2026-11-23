#!/usr/bin/env python3
"""idlecount.py - Agent 10, B gate tie-break helper (read-only).

For each run dir (Agent 3's harness: input.csv + perf.csv, 1 perf row = 1 frame):
  - map every input.csv step to a perf.csv frame index through perf_bytes (perf.csv size at that step;
    the file is flushed in ~1 s chunks, so indices are +-~60 frames);
  - find the scene segments (draw_calls/vertices pairs held for >= MIN_HOLD frames);
  - report, for the last pad press, the frames and seconds (sum of frame_time_us) until the first segment
    change after it (or the end of perf.csv), and the mean fps in that window.
Usage: python idlecount.py <run dir> [<run dir> ...]
"""
import csv
import os
import sys

MIN_HOLD = 30


def load_perf(path):
    with open(path, 'rb') as f:
        data = f.read()
    rows = []
    offsets = []  # byte offset just past each data line
    pos = 0
    header = None
    for raw in data.split(b'\n'):
        end = pos + len(raw) + 1
        line = raw.decode('ascii', 'replace').strip()
        pos = end
        if not line:
            continue
        if header is None:
            header = line.split(',')
            continue
        parts = line.split(',')
        if len(parts) != len(header):
            continue
        try:
            rows.append({k: int(v) for k, v in zip(header, parts)})
        except ValueError:
            continue
        offsets.append(min(end, len(data)))
    return rows, offsets


def frame_at_bytes(offsets, nbytes):
    # number of complete rows inside the first nbytes bytes
    lo, hi = 0, len(offsets)
    while lo < hi:
        mid = (lo + hi) // 2
        if offsets[mid] <= nbytes:
            lo = mid + 1
        else:
            hi = mid
    return lo


def segments(rows):
    segs = []
    start = 0
    for i in range(1, len(rows) + 1):
        if i == len(rows) or (rows[i]['draw_calls'], rows[i]['vertices_processed']) != (
                rows[start]['draw_calls'], rows[start]['vertices_processed']):
            segs.append((start, i, rows[start]['draw_calls'], rows[start]['vertices_processed']))
            start = i
    return segs


def main(dirs):
    for d in dirs:
        rows, offsets = load_perf(os.path.join(d, 'perf.csv'))
        cum = [0.0]
        for r in rows:
            cum.append(cum[-1] + r['frame_time_us'] / 1e6)
        with open(os.path.join(d, 'input.csv'), newline='') as f:
            steps = list(csv.DictReader(f))
        print('=== %s  (%d frames, %.2f s of frame time)' % (d, len(rows), cum[-1]))
        presses = []
        for s in steps:
            if s['cmd'] in ('press', 'mark'):
                fi = frame_at_bytes(offsets, int(s['perf_bytes'] or 0))
                print('  t=%7s  L%-3s %-5s %-12s -> frame %5d  perf %7.2f s' % (
                    s['t_s'], s['line'], s['cmd'], s['args'], fi, cum[min(fi, len(rows))]))
                if s['cmd'] == 'press':
                    presses.append((s, fi))
        long_segs = [g for g in segments(rows) if g[1] - g[0] >= MIN_HOLD]
        print('  scene segments held >= %d frames:' % MIN_HOLD)
        for a, b, dc, vx in long_segs:
            print('    frames %5d-%5d  perf %7.2f-%7.2f s  %d/%d  (%d frames, %.1f s)' % (
                a, b - 1, cum[a], cum[b], dc, vx, b - a, cum[b] - cum[a]))
        if not presses:
            continue
        s, fi = presses[-1]
        nxt = None
        for a, b, dc, vx in segments(rows):
            if a > fi and b - a >= 1 and (dc, vx) != (rows[fi]['draw_calls'], rows[fi]['vertices_processed']):
                nxt = (a, dc, vx)
                break
        stop = nxt[0] if nxt else len(rows)
        secs = cum[stop] - cum[fi]
        print('  last press L%s %s at frame %d (perf %.2f s, scene %d/%d)' % (
            s['line'], s['args'], fi, cum[fi], rows[fi]['draw_calls'], rows[fi]['vertices_processed']))
        if nxt:
            print('  -> first scene change at frame %d (perf %.2f s, %d/%d): %d frames, %.2f s after the press, %.1f fps' % (
                nxt[0], cum[nxt[0]], nxt[1], nxt[2], stop - fi, secs, (stop - fi) / secs if secs else 0))
        else:
            print('  -> no scene change before the end: %d frames, %.2f s after the press, %.1f fps' % (
                stop - fi, secs, (stop - fi) / secs if secs else 0))


if __name__ == '__main__':
    main(sys.argv[1:])

"""Line up the game.log 'Native worker: last 600 frames' lines with native-frames.csv.

Per 600-guest-frame chunk: wall time, fps, slow (>33 ms) and swap>=10 ms counts, throttle_wait share of wall time,
drains/inline. Anchors: chunk k ends at guest swap 600k; the worker present count is the frame column (+-1).
Also checks the alignment by time (t0 = 'Native presentation: frame=0' line + cumulative interval_ms).
Read-only, stdlib, single thread.
"""
import csv, json, os, re, sys
from datetime import datetime

sys.path.insert(0, r"bench\agent7")
import native_frames_summary as nfs  # noqa: E402

BASE = r"build\agent8\matrix\20261122-0452\runs"
PAT = re.compile(r"\[\d{4}-\d\d-\d\d (\d\d:\d\d:\d\d\.\d+)\].*Native worker: last 600 frames tasks=(\d+) inline=(\d+) "
                 r"drains=(\d+) drain_wait=([\d.]+)ms throttle_wait=([\d.]+)ms")
P0 = re.compile(r"\[\d{4}-\d\d-\d\d (\d\d:\d\d:\d\d\.\d+)\].*Native presentation: frame=0 ")


def ts(s):
    return datetime.strptime(s, "%H:%M:%S.%f")


def spearman(a, b):
    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for k, i in enumerate(o):
            r[i] = k
        return r
    ra, rb = rank(a), rank(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** 0.5
    return num / den if den else float("nan")


for d in sys.argv[1:]:
    rd = os.path.join(BASE, d)
    rows = nfs.read_native_csv(os.path.join(rd, "native-frames.csv"))
    t = [float(r["interval_ms"]) for r in rows]
    wins, note = nfs.runner_window(rd, t, [])
    lo, hi = wins["native"] if wins and "native" in wins else (0, len(rows))
    frame = [int(float(r["frame"])) for r in rows]
    swap = [float(r.get("swap_present_cpu_ms") or 0) for r in rows]
    t0 = None
    chunks = []
    with open(os.path.join(rd, "game.log"), encoding="utf-8", errors="replace") as f:
        for line in f:
            m0 = P0.search(line)
            if m0 and t0 is None:
                t0 = ts(m0.group(1))
            m = PAT.search(line)
            if m:
                chunks.append((ts(m.group(1)),) + tuple(float(x) for x in m.groups()[1:]))
    print("=" * 100)
    print(d, "window rows [%d, %d) frames %d..%d; %d worker lines" % (lo, hi, frame[lo], frame[hi - 1], len(chunks)))
    if not chunks:
        continue
    # time alignment: frame whose cumulative time matches each log line
    cum, acc = [], 0.0
    for v in t:
        acc += v
        cum.append(acc)
    print(" k  log time      fr_end  fr_by_time  in_win  wall_s   fps  slow swap10  thr_ms/f  thr_share  drains inline drain_ms")
    xs, ys = [], []
    prev_ts = None
    for k, (tm, tasks, inl, drn, dwait, thr) in enumerate(chunks, 1):
        fe = 600 * k
        by_time = None
        if t0 is not None:
            dt_ms = (tm - t0).total_seconds() * 1000.0
            by_time = next((frame[i] for i, c in enumerate(cum) if c >= dt_ms), frame[-1])
        idx = [i for i, fr in enumerate(frame) if fe - 600 < fr <= fe]
        if not idx:
            continue
        wall = sum(t[i] for i in idx) / 1000.0
        slow = sum(1 for i in idx if t[i] > 33.0)
        s10 = sum(1 for i in idx if swap[i] >= 10.0)
        inwin = sum(1 for i in idx if lo <= i < hi) / len(idx)
        share = thr / 1000.0 / wall if wall else float("nan")
        print("%2d  %s  %6d  %10s  %5.2f  %6.2f  %5.1f  %4d  %5d  %8.2f  %9.2f  %6d %6d %8.1f" % (
            k, tm.strftime("%H:%M:%S"), fe, by_time, inwin, wall, len(idx) / wall, slow, s10, thr / 600.0, share,
            drn, inl, dwait))
        if inwin > 0.5:
            xs.append(share)
            ys.append(slow)
    if len(xs) >= 3:
        print("chunks mostly in window: %d; Spearman(throttle share, slow count) = %.2f" % (len(xs), spearman(xs, ys)))

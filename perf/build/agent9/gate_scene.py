"""Per-step scene segments (draws/vertices run-lengths) for the two B-gate runs.

Maps each route step to a perf.csv row index through input.csv's perf_bytes column,
then prints the run-length segments of (draw_calls, vertices_processed) inside each step.
Read-only; single-threaded.
"""
import csv, sys, io

RUNS = {
    "A": r"build/agent3/runs/20261122-030511-bgate-a",
    "B": r"build/agent3/runs/20261122-030752-bgate-b",
}


def load(run):
    data = open(run + "/perf.csv", "rb").read()
    rows = []  # (end_offset, ft_us, draws, verts)
    pos = 0
    header = None
    for line in data.splitlines(keepends=True):
        pos += len(line)
        s = line.decode("ascii", "replace").strip()
        if not s:
            continue
        if header is None:
            header = s.split(",")
            ift = header.index("frame_time_us")
            idr = header.index("draw_calls")
            ive = header.index("vertices_processed")
            continue
        f = s.split(",")
        try:
            rows.append((pos, int(f[ift]), int(f[idr]), int(f[ive])))
        except (ValueError, IndexError):
            pass
    steps = list(csv.DictReader(open(run + "/input.csv", newline="")))
    return rows, steps


def row_at(rows, nbytes):
    # number of rows fully written at nbytes
    lo, hi = 0, len(rows)
    while lo < hi:
        mid = (lo + hi) // 2
        if rows[mid][0] <= nbytes:
            lo = mid + 1
        else:
            hi = mid
    return lo


def segs(rows, a, b, min_frames=1):
    out = []
    cur = None
    n = 0
    dur = 0
    for r in rows[a:b]:
        key = (r[2], r[3])
        if key != cur:
            if cur is not None:
                out.append((cur, n, dur))
            cur, n, dur = key, 0, 0
        n += 1
        dur += r[1]
    if cur is not None:
        out.append((cur, n, dur))
    return [s for s in out if s[1] >= min_frames]


def fmt(sl, limit=12):
    parts = ["%d/%d x%d(%.2fs)" % (k[0], k[1], n, d / 1e6) for (k, n, d) in sl]
    if len(parts) > limit:
        parts = parts[: limit // 2] + ["... %d more ..." % (len(parts) - limit)] + parts[-limit // 2 :]
    return "; ".join(parts)


def main():
    minf = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    res = {}
    for tag, run in RUNS.items():
        rows, steps = load(run)
        cum = []
        t = 0
        for r in rows:
            t += r[1]
            cum.append(t)
        res[tag] = (rows, steps, cum)
        print("%s: %d rows, %.1f s frame time" % (tag, len(rows), t / 1e6))
    print("min_frames per segment shown: %d" % minf)
    sa, sb = res["A"][1], res["B"][1]
    prev = {"A": 0, "B": 0}
    for i in range(len(sa)):
        la = sa[i]
        lb = sb[i] if i < len(sb) else None
        print("\n== L%s %s %s" % (la["line"], la["cmd"], la["args"]))
        for tag, st in (("A", la), ("B", lb)):
            if st is None:
                continue
            rows, steps, cum = res[tag]
            pb = int(st["perf_bytes"] or 0)
            idx = row_at(rows, pb) if st["cmd"] != "end" else len(rows)
            a = prev[tag]
            ps = cum[a - 1] / 1e6 if a > 0 else 0.0
            pe = cum[idx - 1] / 1e6 if idx > 0 else 0.0
            print("  %s t=%7s rows %5d-%5d perf %6.1f-%6.1f | %s" % (tag, st["t_s"], a, idx, ps, pe, fmt(segs(rows, a, idx, minf))))
            prev[tag] = idx


if __name__ == "__main__":
    main()

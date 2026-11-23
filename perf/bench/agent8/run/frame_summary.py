#!/usr/bin/env python3
"""Frame-time summary of a frames csv. Python 3, stdlib only.

  python frame_summary.py CSV [--skip-rows N | --start-bytes B | --skip-seconds S]
                          [--rows N | --seconds S] [--end-bytes B]
                          [--column NAME] [--scale F] [--json OUT] [--label TEXT] [--quiet]

Sources (auto-detected from the header unless --column is given):
  perf    rexglue perf.csv (--perf_log_csv, core/perf/counter.cpp): 17 integer counters, the first is
          frame_time_us (host-QPC interval between XE_SWAPs); fflushed every 60 rows and at exit.
  native  LEGO_NATIVE_FRAME_METRICS csv (device.cpp): header frame,interval_ms,...; interval_ms is a float
          present-to-present (steady_clock); std::ofstream buffering, so rows reach the disk at irregular
          buffer-sized flushes (byte marks still work: only complete rows up to the offset count).
  --column NAME picks any column; --scale F multiplies it to microseconds (default 1000 for *_ms, else 1).
A last line without a newline (partial row) is dropped and reported as truncated_last_line.

Window: drop the first --skip-rows N data rows, or every row that ends at or before byte offset
--start-bytes B (the csv size sampled at the start of the measure window), or the shortest run of rows
summing to >= --skip-seconds S. Then stop after --rows N rows, or, with --seconds S, after the shortest
run of rows whose frame-time sum is >= S seconds (at most one frame of overshoot). Without
--seconds/--rows, --end-bytes B ends the window at the last row that ends at or before byte B; with
--seconds it is only a cross-check (rows_by_end_bytes, end_bytes_minus_seconds_rows).

Rows with a frame time <= 0 (perf.csv: the first swap has no previous swap, so it is 0) are kept in the
row counts but left out of the statistics (zero_rows). Percentiles are nearest-rank on the sorted
frame times: value = sorted[ceil(p * n) - 1]; the median is p50 (the lower middle for even n).
over_33ms / over_100ms count frame times > 33 ms / > 100 ms (a 33.3 ms frame counts as > 33 ms).
"""
import argparse
import json
import os
import sys

N_FIELDS = 17
FIRST = "frame_time_us"
NATIVE_COL = "interval_ms"


def load(path, column=None, scale=None):
    """Returns header, rows [(end_offset, frame_time_us)], info dict."""
    with open(path, "rb") as f:
        data = f.read()
    info = dict(file=os.path.abspath(path), file_bytes=len(data), header_ok=False, header_fields=0,
                rows_total=0, bad_rows=0, truncated_last_line=False, newlines=data.count(b"\n"),
                source=None, column=None, scale_to_us=None)
    rows = []
    if not data:
        return None, rows, info
    nl = data.find(b"\n")
    if nl < 0:
        info["truncated_last_line"] = True
        return None, rows, info
    header = [h.strip() for h in data[:nl].decode("ascii", "replace").rstrip("\r").split(",")]
    info["header_fields"] = len(header)
    if column is None:
        if header[0] == FIRST:
            column, src, dscale = FIRST, "perf", 1.0
        elif NATIVE_COL in header:
            column, src, dscale = NATIVE_COL, "native", 1000.0
        else:
            column, src, dscale = header[0], "unknown", 1.0
    else:
        src, dscale = "custom", (1000.0 if column.endswith("_ms") else 1.0)
    if scale is None:
        scale = dscale
    info.update(source=src, column=column, scale_to_us=scale)
    info["header_ok"] = (len(header) == N_FIELDS) if src == "perf" else (column in header and src != "unknown")
    if column not in header:
        return header, rows, info
    col = header.index(column)
    width = len(header)
    integer = src == "perf"
    pos = nl + 1
    end = len(data)
    while pos < end:
        nl = data.find(b"\n", pos)
        if nl < 0:
            info["truncated_last_line"] = True
            break
        line = data[pos:nl].rstrip(b"\r")
        pos = nl + 1
        parts = line.split(b",")
        try:
            if len(parts) != width:
                raise ValueError
            if integer:
                vals = [int(p) for p in parts]  # perf.csv: every field is an integer
                v = vals[col] if scale == 1.0 else vals[col] * scale
            else:
                v = float(parts[col]) * scale
        except ValueError:
            info["bad_rows"] += 1
            continue
        rows.append((pos, v))
    info["rows_total"] = len(rows)
    return header, rows, info


def nearest_rank(s, num, den):
    n = len(s)
    k = -(-num * n // den)  # ceil(num/den * n), exact integer arithmetic
    return s[max(1, min(n, k)) - 1]


def ms(v):
    return round(v / 1000.0, 6)


def light_bins(fts, thr, bin_s=10.0):
    """Share of frames under thr per consecutive bin_s seconds of summed frame time (a last partial bin is kept)."""
    out, acc, n, k = [], 0.0, 0, 0
    for v in fts:
        acc += v
        n += 1
        if v < thr:
            k += 1
        if acc >= bin_s * 1e6:
            out.append(round(k / n, 3))
            acc, n, k = 0.0, 0, 0
    if n:
        out.append(round(k / n, 3))
    return out


def stats(fts, light_ms=None):
    """fts: frame times in us (zeros already removed). light_ms: also report the share of frames under it
    (window 3: the light title phase runs mostly under 4.5 ms, the heavy phase 20-40%)."""
    out = dict(frames=len(fts))
    if not fts:
        out.update(window_s=0.0, mean_fps=None, mean_ms=None, median_ms=None, p95_ms=None, p99_ms=None,
                   p99_9_ms=None, min_ms=None, max_ms=None, over_33ms=0, over_100ms=0,
                   light_ms=light_ms, share_lt_light=None, share_lt_light_bins_10s=[])
        return out
    s = sorted(fts)
    total = sum(fts)
    out.update(
        window_s=round(total / 1e6, 6),
        mean_fps=round(len(fts) * 1e6 / total, 3),
        mean_ms=round(total / len(fts) / 1000.0, 4),
        median_ms=ms(nearest_rank(s, 1, 2)),
        p95_ms=ms(nearest_rank(s, 95, 100)),
        p99_ms=ms(nearest_rank(s, 99, 100)),
        p99_9_ms=ms(nearest_rank(s, 999, 1000)),
        min_ms=ms(s[0]), max_ms=ms(s[-1]),
        over_33ms=sum(1 for v in fts if v > 33000),
        over_100ms=sum(1 for v in fts if v > 100000),
        light_ms=light_ms, share_lt_light=None, share_lt_light_bins_10s=[],
    )
    if light_ms:
        thr = light_ms * 1000.0
        out['share_lt_light'] = round(sum(1 for v in fts if v < thr) / len(fts), 4)
        out['share_lt_light_bins_10s'] = light_bins(fts, thr)
    return out


def summarise(path, skip_rows=None, start_bytes=None, rows_limit=None, end_bytes=None, seconds=None,
              label=None, skip_seconds=None, column=None, scale=None, light_ms=4.5):
    header, rows, info = load(path, column, scale)
    res = dict(info)
    res["label"] = label
    res["percentile_method"] = "nearest-rank: sorted[ceil(p*n)-1]; median = p50"
    first = 0
    if start_bytes is not None:
        first = sum(1 for e, _ in rows if e <= start_bytes)
    elif skip_seconds is not None:
        acc = 0
        for _, v in rows:
            if acc >= skip_seconds * 1e6:
                break
            acc += max(v, 0)
            first += 1
    elif skip_rows:
        first = min(skip_rows, len(rows))
    avail = rows[first:]
    by_end = None
    if end_bytes is not None:
        by_end = sum(1 for e, _ in rows if e <= end_bytes) - first
    end_by = "eof"
    short = False
    if seconds is not None:
        target = seconds * 1e6
        acc, n = 0, 0
        for _, v in avail:
            if acc >= target:
                break
            acc += max(v, 0)
            n += 1
        if acc >= target:
            end_by = "seconds"
        else:
            short = True
        win = avail[:n]
    elif rows_limit is not None:
        win = avail[:rows_limit]
        end_by = "rows"
        short = len(win) < rows_limit
    elif by_end is not None:
        win = avail[:max(by_end, 0)]
        end_by = "end-bytes"
    else:
        win = avail
    fts = [v for _, v in win if v > 0]
    res["window"] = dict(
        skip_rows=skip_rows, start_bytes=start_bytes, rows_limit=rows_limit, end_bytes=end_bytes,
        seconds=seconds, first_row=first, rows=len(win), end_by=end_by, short=short,
        zero_rows=len(win) - len(fts), rows_by_end_bytes=by_end,
        end_bytes_minus_seconds_rows=(by_end - len(win)) if (by_end is not None and seconds is not None) else None,
        end_bytes_window_s=(round(sum(max(v, 0) for _, v in avail[:max(by_end, 0)]) / 1e6, 6)
                            if by_end is not None else None),
        first_row_end_offset=win[0][0] if win else None, last_row_end_offset=win[-1][0] if win else None,
    )
    res.update(stats(fts, light_ms))
    res["frame_time_valid"] = bool(fts)
    return res


def text(r):
    w = r["window"]
    lines = []
    if r.get("label"):
        lines.append(f"[{r['label']}]")
    lines.append(f"{r['source']} csv {r['file']}: {r['file_bytes']} bytes, {r['rows_total']} rows, column "
                 f"{r['column']} x{r['scale_to_us']} -> us, header {'ok' if r['header_ok'] else 'BAD'} "
                 f"({r['header_fields']} fields), bad rows {r['bad_rows']}, "
                 f"truncated last line {'yes' if r['truncated_last_line'] else 'no'}")
    lines.append(f"window   rows {w['first_row']}..{w['first_row'] + w['rows'] - 1} ({w['rows']} rows, end by "
                 f"{w['end_by']}{', SHORT' if w['short'] else ''}; {w['zero_rows']} zero rows left out)")
    if w["rows_by_end_bytes"] is not None:
        lines.append(f"         rows flushed by end mark: {w['rows_by_end_bytes']} "
                     f"(frame-time sum {w['end_bytes_window_s']} s)"
                     + (f"; minus seconds-cut rows: {w['end_bytes_minus_seconds_rows']:+d}"
                        if w["end_bytes_minus_seconds_rows"] is not None else ""))
    if not r["frames"]:
        lines.append("frames   none in the window")
    else:
        lines.append(f"frames   {r['frames']} over {r['window_s']:.3f} s = {r['mean_fps']:.2f} fps mean")
        lines.append(f"frame ms median {r['median_ms']:.3f}  p95 {r['p95_ms']:.3f}  p99 {r['p99_ms']:.3f}  "
                     f"p99.9 {r['p99_9_ms']:.3f}  max {r['max_ms']:.3f}  >33ms {r['over_33ms']}  >100ms {r['over_100ms']}  "
                     f"(nearest-rank)")
        if r.get("share_lt_light") is not None:
            lines.append(f"light    share of frames < {r['light_ms']} ms: {r['share_lt_light']:.3f}; per 10 s: "
                         + " ".join(f"{x:.2f}" for x in r["share_lt_light_bins_10s"]))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--skip-rows", type=int)
    g.add_argument("--start-bytes", type=int)
    g.add_argument("--skip-seconds", type=float, help="drop the shortest run of rows summing to >= S seconds")
    ap.add_argument("--rows", type=int)
    ap.add_argument("--end-bytes", type=int)
    ap.add_argument("--seconds", type=float)
    ap.add_argument("--column", help="frame-time column (default: frame_time_us, else interval_ms)")
    ap.add_argument("--scale", type=float, help="multiplier from the column unit to microseconds")
    ap.add_argument("--json")
    ap.add_argument("--label")
    ap.add_argument("--light-ms", type=float, default=4.5,
                    help="report share_lt_light = share of window frames under this many ms (default 4.5; 0 = off)")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    if a.rows is not None and a.seconds is not None:
        ap.error("--rows and --seconds are exclusive")
    if not os.path.isfile(a.csv):
        print(f"no such file: {a.csv}", file=sys.stderr)
        return 2
    r = summarise(a.csv, a.skip_rows, a.start_bytes, a.rows, a.end_bytes, a.seconds, a.label, a.skip_seconds,
                  a.column, a.scale, a.light_ms or None)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(r, f, indent=2)
    if not a.quiet:
        print(text(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())

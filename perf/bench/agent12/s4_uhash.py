#!/usr/bin/env python3
"""S4 u diagnostic parser (Agent 12, task #27): re-upload share of unchanged bytes.

Reads the per-frame lines that the staged shared_memory_upload_hash_log patch
(build/agent12/s4-diag/upload-hash-log.diff) writes to game.log:

  S4 upload hash: frame F calls C ranges R pages P (K KB) first N unchanged U
  changed X blocks B changed_blocks CB pages_in_changed_blocks PCB u_page f u_block f

u = share of each re-upload that copies bytes the GPU already has. Over a
window the script weights by pages (sum unchanged / sum (pages - first)), it
does not average the per-frame values. u_block is what P1 (keep the write watch
over a lock) could skip at its 256 KB fault granularity. Both are upper bounds:
an identical rewrite counts as unchanged here but still faults under P1.

P1's downside from the same lines: changed_blocks per frame is a lower bound on
P1's write-watch faults per frame (one per written 256 KB block), blocks per
frame an upper bound; pages_in_changed_blocks is a lower bound on P1's
re-upload and changed_blocks x 256 KB an upper bound (block widening).

Logs: a run dir is read with its rotated logs, oldest first (game.N.log ...
game.1.log, then game.log), like bench/agent5/s4_slowframe.py. Log files given
explicitly are read in the order given.

Time base: when the run also had slow_frame_log_ms set, the elapsed time is the
running sum of the ReportSlowFrame frame times (same as bench/agent5/
s4_slowframe.py) and each S4 line takes the time of the last slow-frame line
before it; the default window is 70-220 s. If the first slow-frame index read
is above 50, older logs were lost and that time base is shifted: the output
then has a "warning", and --frames A:B should be used. Without slow-frame lines
the window is by S4 frame number (--frames A:B), default all but the first 20%.

usage: python s4_uhash.py <run dir | log files, oldest first> [--from S] [--to S]
                          [--frames A:B] [--fault-us 5,8,15] [--json OUT]
       python s4_uhash.py --selftest
"""
import argparse
import json
import os
import re
import sys
import tempfile

S4 = re.compile(
    r"S4 upload hash: frame (?P<frame>\d+) calls (?P<calls>\d+) ranges (?P<ranges>\d+) "
    r"pages (?P<pages>\d+) \((?P<kb>\d+) KB\) first (?P<first>\d+) unchanged (?P<unch>\d+) "
    r"changed (?P<chg>\d+) blocks (?P<blocks>\d+) changed_blocks (?P<cblocks>\d+) "
    r"pages_in_changed_blocks (?P<pcb>\d+) u_page (?P<up>-?[\d.]+) u_block (?P<ub>-?[\d.]+)")
# ReportSlowFrame (rexglue-sdk src/graphics/d3d12/command_processor.cpp:242-283); only the
# index and the frame time are needed here.
SLOW = re.compile(r"slow frame #(?P<idx>\d+): (?P<ms>[\d.]+) ms \|")
ROT = re.compile(r"^game\.(\d+)\.log$")
# In a complete log the first slow frame is #2 (a-vol, 0620-a-vol-r1/game.1.log:43).
LOST_LOG_FIRST_INDEX = 50


def pct(values, q):
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * q
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def dist(values):
    if not values:
        return None
    return {"mean": round(sum(values) / len(values), 3), "p10": round(pct(values, 0.1), 3),
            "p50": round(pct(values, 0.5), 3), "p90": round(pct(values, 0.9), 3),
            "max": round(max(values), 3)}


def resolve(paths):
    """Run dirs expand to their rotated logs, oldest first; files are kept in the given order."""
    files = []
    for path in paths:
        if not os.path.isdir(path):
            files.append(path)
            continue
        rot = []
        for name in os.listdir(path):
            m = ROT.match(name)
            if m:
                rot.append((int(m[1]), name))
        found = [os.path.join(path, name) for _, name in sorted(rot, reverse=True)]
        base = os.path.join(path, "game.log")
        if os.path.isfile(base):
            found.append(base)
        elif not found and os.path.isfile(os.path.join(path, "log.txt")):
            found.append(os.path.join(path, "log.txt"))
        if not found:
            raise SystemExit(f"no game.log in {path}")
        files += found
    return files


def parse(paths):
    rows, slow_frames, t, first_idx = [], 0, None, None
    for path in paths:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = SLOW.search(line)
                if m:
                    if first_idx is None:
                        first_idx = int(m["idx"])
                    t = (t or 0.0) + float(m["ms"]) / 1000.0
                    slow_frames += 1
                    continue
                m = S4.search(line)
                if not m:
                    continue
                r = {k: int(m[k]) for k in ("frame", "calls", "ranges", "pages", "kb", "first",
                                            "unch", "chg", "blocks", "cblocks", "pcb")}
                r["up"], r["ub"], r["t"] = float(m["up"]), float(m["ub"]), t
                rows.append(r)
    return rows, slow_frames, first_idx


def summarize(rows, slow_frames, t0, t1, frames, fault_us, first_slow_idx=None):
    out = {"s4_lines": len(rows), "slow_frame_lines": slow_frames,
           "first_slow_frame_index": first_slow_idx}
    timed = slow_frames > 0 and any(r["t"] is not None for r in rows)
    if timed and not frames:
        win = [r for r in rows if r["t"] is not None and t0 <= r["t"] <= t1]
        out["window"] = {"by": "elapsed s (sum of slow-frame ms)", "from": t0, "to": t1}
        if first_slow_idx is not None and first_slow_idx > LOST_LOG_FIRST_INDEX:
            out["warning"] = (f"first slow-frame index is {first_slow_idx}: older logs are "
                              f"missing, so the elapsed-time window is shifted; use --frames A:B")
    else:
        if frames:
            a, b = frames
        else:
            ordered = sorted(r["frame"] for r in rows)
            a = ordered[len(ordered) // 5] if ordered else 0
            b = ordered[-1] if ordered else 0
        win = [r for r in rows if a <= r["frame"] <= b]
        out["window"] = {"by": "S4 frame number", "from": a, "to": b}
    out["frames"] = len(win)
    if not win:
        return out
    pages = sum(r["pages"] for r in win)
    first = sum(r["first"] for r in win)
    unch = sum(r["unch"] for r in win)
    pcb = sum(r["pcb"] for r in win)
    re_pages = pages - first
    kb_per_page = (sum(r["kb"] for r in win) / pages) if pages else 4.0
    out.update({
        "frame_span": [win[0]["frame"], win[-1]["frame"]],
        "frames_missing_in_span": (win[-1]["frame"] - win[0]["frame"] + 1) - len(win),
        "kb_per_page": round(kb_per_page, 3),
        "pages_per_frame": dist([r["pages"] for r in win]),
        "upload_kb_per_frame": dist([r["kb"] for r in win]),
        "first_share": round(first / pages, 4) if pages else None,
        "u_page": round(unch / re_pages, 4) if re_pages else None,
        "u_block": round(1.0 - pcb / re_pages, 4) if re_pages else None,
        "u_page_per_frame": dist([r["up"] for r in win if r["up"] >= 0]),
        "u_block_per_frame": dist([r["ub"] for r in win if r["ub"] >= 0]),
        "calls_per_frame": dist([r["calls"] for r in win]),
        "ranges_per_frame": dist([r["ranges"] for r in win]),
        "blocks_per_frame": dist([r["blocks"] for r in win]),
        "changed_blocks_per_frame": dist([r["cblocks"] for r in win]),
        "today_reupload_kb_per_frame": round(re_pages * kb_per_page / len(win), 1),
        "p1_reupload_kb_per_frame_lower": round(pcb * kb_per_page / len(win), 1),
        "p1_reupload_kb_per_frame_upper": round(
            sum(r["cblocks"] for r in win) * 256.0 / len(win), 1),
    })
    cb = out["changed_blocks_per_frame"]["mean"]
    bl = out["blocks_per_frame"]["mean"]
    out["p1_faults_per_frame"] = {"lower_changed_blocks": cb, "upper_blocks": bl}
    out["p1_fault_ms_per_frame"] = {
        f"{us:g}us": [round(cb * us / 1000.0, 3), round(bl * us / 1000.0, 3)] for us in fault_us}
    return out


def selftest():
    lines = []
    for i in range(1, 301):  # 300 frames of 1000/60 ms -> 5 s
        lines.append(f"[info] [gpu] slow frame #{i}: 16.667 ms | gpu-thread idle 1.0 | host-gpu "
                     f"wait 0.0 (0x) | cpu-write invalidations 3x 512 KB (on memexport pages 0x "
                     f"0 KB)\n")
        if i == 1:
            lines.append("[info] [gpu] S4 upload hash: frame 1 calls 1 ranges 1 pages 100 (400 KB) "
                         "first 100 unchanged 0 changed 0 blocks 2 changed_blocks 0 "
                         "pages_in_changed_blocks 0 u_page -1.0000 u_block -1.0000\n")
        elif i % 2 == 0:
            lines.append(f"[info] [gpu] S4 upload hash: frame {i} calls 2 ranges 3 pages 128 "
                         f"(512 KB) first 0 unchanged 96 changed 32 blocks 2 changed_blocks 1 "
                         f"pages_in_changed_blocks 64 u_page 0.7500 u_block 0.5000\n")
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "game.log")
        with open(p, "w", encoding="utf-8") as f:
            f.writelines(lines)
        rows, slow, first = parse([p])
        assert slow == 300 and len(rows) == 151 and first == 1, (slow, len(rows), first)
        s = summarize(rows, slow, 0.99, 4.01, None, [5, 8, 15], first)
        # t of frame i is i x 16.667 ms: even frames 60..240 fall in 0.99-4.01 s -> 91 lines
        assert s["frames"] == 91, s["frames"]
        assert "warning" not in s
        assert s["u_page"] == 0.75 and s["u_block"] == 0.5, (s["u_page"], s["u_block"])
        assert s["first_share"] == 0.0 and s["kb_per_page"] == 4.0
        assert s["today_reupload_kb_per_frame"] == 512.0
        assert s["p1_reupload_kb_per_frame_lower"] == 256.0
        assert s["p1_reupload_kb_per_frame_upper"] == 256.0
        assert s["p1_faults_per_frame"] == {"lower_changed_blocks": 1.0, "upper_blocks": 2.0}
        assert s["p1_fault_ms_per_frame"]["8us"] == [0.008, 0.016]
        # frame-number window (no slow-frame lines): drop them and check the default 20% cut
        rows2 = [dict(r, t=None) for r in rows]
        s2 = summarize(rows2, 0, 70.0, 220.0, None, [8])
        assert s2["window"]["by"] == "S4 frame number" and s2["window"]["from"] == 60, s2["window"]
        assert s2["frames"] == 121, s2["frames"]
        s3 = summarize(rows2, 0, 70.0, 220.0, (1, 1), [8])
        assert s3["frames"] == 1 and s3["u_page"] is None and s3["first_share"] == 1.0
        # rotated logs in a run dir are read oldest first: game.2.log, game.1.log, game.log
        rd = os.path.join(d, "rot")
        os.mkdir(rd)
        for name, part in (("game.2.log", lines[:150]), ("game.1.log", lines[150:300]),
                           ("game.log", lines[300:]), ("game.txt", ["noise\n"])):
            with open(os.path.join(rd, name), "w", encoding="utf-8") as f:
                f.writelines(part)
        files = resolve([rd])
        assert [os.path.basename(x) for x in files] == ["game.2.log", "game.1.log", "game.log"], files
        rows_r, slow_r, first_r = parse(files)
        assert (slow_r, len(rows_r), first_r) == (300, 151, 1), (slow_r, len(rows_r), first_r)
        sr = summarize(rows_r, slow_r, 0.99, 4.01, None, [8], first_r)
        assert sr["frames"] == 91 and sr["u_page"] == 0.75 and "warning" not in sr
        # oldest file lost: the first slow-frame index is late, so the output warns
        rows_l, slow_l, first_l = parse(files[1:])
        assert first_l > LOST_LOG_FIRST_INDEX, first_l
        assert "warning" in summarize(rows_l, slow_l, 0.99, 4.01, None, [8], first_l)
        assert "warning" not in summarize(rows_l, slow_l, 0.99, 4.01, (100, 300), [8], first_l)
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="*", help="run dir (rotated logs included) or log files, "
                                             "oldest first")
    ap.add_argument("--from", dest="t0", type=float, default=70.0,
                    help="window start, s after the first logged frame (default 70)")
    ap.add_argument("--to", dest="t1", type=float, default=220.0,
                    help="window end, s (default 220)")
    ap.add_argument("--frames", help="window by S4 frame number, A:B (overrides --from/--to)")
    ap.add_argument("--fault-us", default="5,8,15",
                    help="cost per write-watch fault in us for the P1 estimate (default 5,8,15)")
    ap.add_argument("--json")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.paths:
        ap.error("path required")
    frames = tuple(int(x) for x in a.frames.split(":")) if a.frames else None
    fault_us = [float(x) for x in a.fault_us.split(",") if x]
    files = resolve(a.paths)
    rows, slow, first = parse(files)
    out = {"files": [os.path.basename(x) for x in files]}
    out.update(summarize(rows, slow, a.t0, a.t1, frames, fault_us, first))
    text = json.dumps(out, indent=1)
    print(text)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    return 0 if out.get("frames") else 1


if __name__ == "__main__":
    sys.exit(main())

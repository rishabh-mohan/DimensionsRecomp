"""Idle frames from the last pad input to the screen exit (220/534 -> 220/540), per run.

Method (Agent 9, session 3, for Agent 10's B-gate verdict):
- perf.csv has one row per frame (frame_time_us, draw_calls, vertices_processed).
- input.csv gives, per route step, pad_reads (XInputGetState calls so far; the game polls once per frame) and
  pad_active_reads (polls that saw a held button). Both are exact at the step's end, unlike perf_bytes, which only
  moves in the game's 60-row flush blocks.
- The last input poll = pad_reads before the last press step + that step's active polls (the button is held at the
  start of the step). Poll index -> frame row through offset = pad_reads - rows at the end of the run (the game polls
  a few times before its first frame); the per-step flush-block bounds must agree with it (printed as a check).
- Exit = the first frame after the last input whose draws/vertices are the --exit scene (default 220/540). Also printed:
  the first frame that leaves the scene held at the last input, and the frames since that scene first appeared.
Read-only; single-threaded.
Usage: python build/agent9/idle_frames.py RUN_DIR [RUN_DIR ...] [--exit 220/540]
"""
import csv, os, re, sys
from datetime import datetime


def load_perf(run):
    data = open(os.path.join(run, "perf.csv"), "rb").read()
    rows, ends = [], []
    header = None
    pos = 0
    for line in data.splitlines(keepends=True):
        pos += len(line)
        s = line.decode("ascii", "replace").strip()
        if not s:
            continue
        if header is None:
            header = s.split(",")
            ift, idr, ive = (header.index(k) for k in ("frame_time_us", "draw_calls", "vertices_processed"))
            continue
        f = s.split(",")
        try:
            rows.append((int(f[ift]), int(f[idr]), int(f[ive])))
            ends.append(pos)
        except (ValueError, IndexError):
            pass
    return rows, ends


def rows_at(ends, nbytes):
    lo, hi = 0, len(ends)
    while lo < hi:
        mid = (lo + hi) // 2
        if ends[mid] <= nbytes:
            lo = mid + 1
        else:
            hi = mid
    return lo


def started_at(run):
    try:
        for line in open(os.path.join(run, "route-report.txt"), encoding="utf-8", errors="replace"):
            m = re.search(r"started (\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+)", line)
            if m:
                return datetime.fromisoformat(m.group(1)[:26])
    except OSError:
        pass
    return None


def install_probes(run, t0):
    """(first, last, count) launch-relative seconds of NtCreateFile INSTALL probe lines, grouped into passes."""
    out = []
    try:
        for line in open(os.path.join(run, "game.log"), encoding="utf-8", errors="replace"):
            if "INSTALL" in line and "NtCreateFile" in line:
                m = re.match(r"\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+)\]", line)
                if m and t0 is not None:
                    out.append((datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S.%f") - t0).total_seconds())
    except OSError:
        pass
    passes = []
    for t in out:
        if passes and t - passes[-1][1] < 2.0:
            passes[-1][1] = t
            passes[-1][2] += 1
        else:
            passes.append([t, t, 1])
    return passes


def analyse(run, exit_scene):
    rows, ends = load_perf(run)
    steps = list(csv.DictReader(open(os.path.join(run, "input.csv"), newline="")))
    name = os.path.basename(os.path.normpath(run))
    done = bool(steps) and steps[-1]["cmd"] == "end"
    print("\n== %s  (%d frame rows, %s)" % (name, len(rows), "finished" if done else "NOT FINISHED"))
    if not rows or not steps:
        return None
    presses = [i for i, s in enumerate(steps) if s["cmd"] == "press"]
    li = presses[-1]
    prev, last = steps[li - 1], steps[li]
    act = int(last["pad_active_reads"]) - int(prev["pad_active_reads"])
    poll_first = int(prev["pad_reads"])          # polls before the last press began
    poll_last_active = poll_first + act           # last poll with the button held (contiguous hold at step start)
    end_polls = int(steps[-1]["pad_reads"]) if done else None
    offset = end_polls - len(rows) if done else 3
    # Check the offset against each step's flush-block bounds: rows_on_disk <= frames < rows_on_disk + 60.
    lo, hi = -10**9, 10**9
    for s in steps[1:-1]:
        pb = int(s["perf_bytes"] or 0)
        if pb <= 0:
            continue
        r = rows_at(ends, pb)
        p = int(s["pad_reads"])
        lo, hi = max(lo, p - r - 59), min(hi, p - r)
    ok = lo <= offset <= hi
    last_row = poll_last_active - offset          # frame row of the last input poll (0-based)
    held = (rows[last_row][1], rows[last_row][2]) if 0 <= last_row < len(rows) else None
    # first frame of the held scene (walk back while equal)
    r0 = last_row
    while r0 > 0 and (rows[r0 - 1][1], rows[r0 - 1][2]) == held:
        r0 -= 1
    leave = next((r for r in range(last_row + 1, len(rows)) if (rows[r][1], rows[r][2]) != held), None)
    ex = next((r for r in range(last_row + 1, len(rows)) if (rows[r][1], rows[r][2]) == exit_scene), None)

    def secs(a, b):
        return sum(x[0] for x in rows[a:b]) / 1e6

    cum = 0
    perf_at = []
    for x in rows:
        cum += x[0]
        perf_at.append(cum / 1e6)
    print("  last press: L%s %s; %d active polls; last active poll %d -> frame %d (perf %.2f s); offset %d (block check %s: %d..%d)"
          % (last["line"], last["args"], act, poll_last_active, last_row, perf_at[last_row], offset,
             "ok" if ok else "FAIL", lo, hi))
    print("  scene at the last input %s/%s, first shown at frame %d (perf %.2f s)" % (held[0], held[1], r0, perf_at[r0]))
    res = {"run": name, "done": done}
    if leave is not None:
        print("  first frame off %s/%s: %d (%s/%s), %d idle frames, %.2f s of frame time"
              % (held[0], held[1], leave, rows[leave][1], rows[leave][2], leave - last_row, secs(last_row, leave)))
    if ex is not None:
        n, t = ex - last_row, secs(last_row, ex)
        nxt = ex
        while nxt < len(rows) and (rows[nxt][1], rows[nxt][2]) == exit_scene:
            nxt += 1
        after = "%s/%s" % (rows[nxt][1], rows[nxt][2]) if nxt < len(rows) else "end"
        print("  EXIT %d/%d at frame %d (perf %.2f s): %d idle frames after the last input, %.2f s of frame time (%.1f fps); "
              "%d frames / %.2f s since the scene appeared; %d exit frames, then %s"
              % (exit_scene[0], exit_scene[1], ex, perf_at[ex], n, t, n / t if t else 0, ex - r0, secs(r0, ex), nxt - ex, after))
        res.update(exit_frames=n, exit_secs=t, since_scene=ex - r0)
    else:
        n, t = len(rows) - last_row, secs(last_row, len(rows))
        print("  NO EXIT to %d/%d: %d idle frames to the end, %.2f s of frame time (%.1f fps); %d frames since the scene appeared"
              % (exit_scene[0], exit_scene[1], n, t, n / t if t else 0, len(rows) - r0))
        res.update(exit_frames=None, idle_to_end=n)
    t0 = started_at(run)
    ps = install_probes(run, t0)
    if ps:
        print("  INSTALL probe passes (launch-relative s, lines): " + "; ".join("%.1f-%.1f x%d" % (a, b, c) for a, b, c in ps))
    return res


def main():
    args = sys.argv[1:]
    exit_scene = (220, 540)
    if "--exit" in args:
        i = args.index("--exit")
        d, v = args[i + 1].split("/")
        exit_scene = (int(d), int(v))
        del args[i : i + 2]
    for run in args:
        analyse(run, exit_scene)


if __name__ == "__main__":
    main()

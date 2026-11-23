#!/usr/bin/env python3
"""Agent 6, task #18: scan real run dirs for boot gap, shader-storage state and
first-view pipeline-miss cost, in launch order (single-threaded, read-only).

For each dir with perf.csv + game.log:
  started        run.json "started" (else first game.log timestamp)
  exe            legodimensions.exe size + mtime (hard links share both)
  gap_s          "Initializing shader storage" -> next log line (boot gap)
  xsh/xpso       size at end; seeded=yes if the file was created before launch
  pm, pm_frames  pipeline misses and frames that have them
  pm_excess_s    sum over pm frames (and the next 2 rows) of frame time above
                 the median of the 30 frames before
  ms/miss        pm_excess / pm
  ev_row2        frame time of the first rows with misses (the boot event)
  menu_pm        pipeline misses and excess in the first 150 s after frame 1
"""
import csv, datetime as dt, glob, json, os, re, statistics, sys

ROOTS = ["build/agent3/runs/*", "build/agent8/runs/*", "build/agent8/matrix/*/runs/*"]
LOG_TS = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\]")


def ts(s):
    return dt.datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")


def scan(d):
    perf, log = os.path.join(d, "perf.csv"), os.path.join(d, "game.log")
    if not (os.path.exists(perf) and os.path.exists(log)):
        return None
    exe = os.path.join(d, "legodimensions.exe")
    if not os.path.exists(exe) or os.path.getsize(exe) < 50_000_000:
        return None
    st = os.stat(exe)
    started = None
    rj = os.path.join(d, "run.json")
    if os.path.exists(rj):
        try:
            j = json.load(open(rj, encoding="utf-8-sig"))
            s = j.get("started") or j.get("start") or ""
            m = re.match(r"(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})(\.\d+)?", s)
            if m:
                started = dt.datetime.strptime(m.group(1) + " " + m.group(2), "%Y-%m-%d %H:%M:%S") + \
                    dt.timedelta(seconds=float(m.group(3) or 0))
        except Exception:
            pass
    lines = open(log, encoding="utf-8", errors="replace").read().split("\n")
    stamps = [(ts(m.group(1)), l) for l in lines for m in [LOG_TS.match(l)] if m]
    if not stamps:
        return None
    if started is None:
        started = stamps[0][0]
    gap = None
    for i, (t, l) in enumerate(stamps):
        if "Initializing shader storage" in l:
            if i + 1 < len(stamps):
                gap = (stamps[i + 1][0] - t).total_seconds()
            break
    cache = {}
    for ext in ("xsh", "xpso"):
        fs = glob.glob(os.path.join(d, "user", "cache", "shaders", "shareable", "*." + ext)) + \
            glob.glob(os.path.join(d, "user", "cache", "shaders", "shareable", "*", "*." + ext))
        if fs:
            f = fs[0]
            s2 = os.stat(f)
            ctime = dt.datetime.fromtimestamp(s2.st_ctime)
            cache[ext] = (s2.st_size, ctime < started - dt.timedelta(seconds=1), ctime)
    rows = []
    with open(perf, newline="") as f:
        rd = csv.DictReader(f)
        for r in rd:
            try:
                rows.append((int(r["frame_time_us"]) / 1000.0, int(r["pipeline_cache_misses"]),
                             int(r["texture_cache_misses"]), int(r["draw_calls"])))
            except (KeyError, ValueError, TypeError):
                break
    if len(rows) < 100:
        return None
    ft = [r[0] for r in rows]
    pm = [r[1] for r in rows]
    exc_tot, cum = 0.0, 0.0
    menu_pm, menu_exc = 0, 0.0
    counted = set()
    t_of = []
    for x in ft:
        cum += x / 1000.0
        t_of.append(cum)
    for i in range(1, len(rows)):
        if pm[i] <= 0:
            continue
        base = statistics.median(ft[max(1, i - 30):i]) if i > 1 else 16.7
        e = 0.0
        for j in range(i, min(len(rows), i + 3)):
            if j in counted:
                continue
            counted.add(j)
            e += max(0.0, ft[j] - base)
        exc_tot += e
        if t_of[i] < 150:
            menu_pm += pm[i]
            menu_exc += e
    first_pm = [(i, pm[i], ft[i]) for i in range(1, min(len(rows), 400)) if pm[i] > 0][:3]
    return {
        "dir": d.replace("\\", "/"), "started": started, "exe": f"{st.st_size // 1000000}MB@{dt.datetime.fromtimestamp(st.st_mtime):%m%d-%H%M}",
        "gap_s": gap, "cache": cache, "rows": len(rows), "secs": round(t_of[-1], 1),
        "pm": sum(pm), "pm_frames": sum(1 for x in pm if x > 0), "pm_excess_s": round(exc_tot / 1000.0, 2),
        "ms_per_miss": round(exc_tot / sum(pm), 1) if sum(pm) else None,
        "menu_pm": menu_pm, "menu_exc_s": round(menu_exc / 1000.0, 2),
        "menu_ms_per_miss": round(menu_exc / menu_pm, 1) if menu_pm else None,
        "first_pm": first_pm, "max_ms": round(max(ft), 0),
    }


def main():
    out = []
    for pat in ROOTS:
        for d in sorted(glob.glob(pat)):
            if os.path.isdir(d):
                try:
                    r = scan(d)
                except Exception as e:  # keep going
                    print(f"! {d}: {e}", file=sys.stderr)
                    r = None
                if r:
                    out.append(r)
    out.sort(key=lambda r: r["started"])
    print(f"{'started':<15} {'exe':<15} {'gap_s':>6} {'xsh':>14} {'xpso':>13} {'secs':>6} {'pm':>4} {'pmfr':>4} "
          f"{'exc_s':>6} {'ms/pm':>6} {'menu_pm':>7} {'mexc_s':>6} {'mms/pm':>6} {'max_ms':>7}  first_pm(row,pm,ms)  dir")
    for r in out:
        c = r["cache"]
        xsh = f"{c['xsh'][0]}{'S' if c['xsh'][1] else ''}" if "xsh" in c else "-"
        xpso = f"{c['xpso'][0]}{'S' if c['xpso'][1] else ''}" if "xpso" in c else "-"
        print(f"{r['started']:%m%d %H:%M:%S}  {r['exe']:<15} {r['gap_s'] if r['gap_s'] is not None else '-':>6} {xsh:>14} {xpso:>13} "
              f"{r['secs']:>6} {r['pm']:>4} {r['pm_frames']:>4} {r['pm_excess_s']:>6} {str(r['ms_per_miss']):>6} "
              f"{r['menu_pm']:>7} {r['menu_exc_s']:>6} {str(r['menu_ms_per_miss']):>6} {r['max_ms']:>7}  "
              f"{[(a, b, round(c2)) for a, b, c2 in r['first_pm']]}  {r['dir'].split('build/')[-1]}")
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "scan_runs.json"), "w"),
              default=str, indent=1)


if __name__ == "__main__":
    main()

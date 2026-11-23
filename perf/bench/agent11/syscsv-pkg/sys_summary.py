#!/usr/bin/env python3
"""Summary of a sys.csv written by drivers/sys-csv.ps1 (1 s system-state log). Python 3, stdlib only.

  python sys_summary.py --csv RUN\\sys.csv --start-epoch S --end-epoch E [--out RUN\\sys.json] [--interval 1.0]

Blocks: "window" = the rows with S <= epoch_s <= E (Unix seconds, the clock of run-timing.ps1 Get-Epoch),
"run" = every row. Each block: rows, span_s, max_gap_s, idle_min_s, input_events, fg_game_share, game_alive_all,
desktop_not_default_rows, screensaver_rows, cpu_util_mean, eff_mhz_mean, eff_mhz_min, p_eff_mhz_mean, e_eff_mhz_mean,
p_util_mean, e_util_mean, tz_passive_min, tz_temp_max_c, and for ac / batt_saver / batt_pct / scheme / overlay
{"first", "last", "changes": [{t_s, epoch_s, from, to}]} (blank cells are skipped, so blank -> value is no change).
input_events counts samples with idle_s < (t_s - previous t_s) - 0.05 (input since the previous sample; the previous
sample is the previous row of the file). The first window row counts only if its input time epoch_s - idle_s is at or
after S (input just before the window start is not "during the window").
flags (window): input_during_window, not_foreground (fg_game_share < 0.99), on_battery, battery_saver, power_change
(scheme / overlay / ac changed), thermal_passive (tz_passive_min < 100), desktop_not_default, screensaver, sample_gaps
(max_gap_s > 2.5 x interval), short_window (rows < 0.8 x (E - S) / interval).
Blank cells are None; a last line without a newline (driver killed mid-write) is dropped (file.truncated_last_line).
Exit 0 with a summary (also for a header-only csv: rows 0, short_window); exit 1 and {"error": ...} (in --out too)
when the csv is missing, empty, has no complete header line or no t_s / epoch_s column. One "SYS ..." line on stdout.
"""
import argparse
import csv
import json
import math
import os
import sys

COLUMNS = ["t_s", "epoch_s", "wall", "idle_s", "fg_pid", "fg_game", "game_alive", "input_desktop", "screensaver",
           "cpu_util_pct", "cpu_perf_pct", "base_mhz", "eff_mhz", "p_eff_mhz", "e_eff_mhz", "p_util_pct", "e_util_pct",
           "tz_passive_min_pct", "tz_temp_max_c", "ac", "batt_saver", "batt_pct", "scheme", "overlay"]
TEXT = {"wall", "input_desktop", "scheme", "overlay"}
TRACKED = ["ac", "batt_saver", "batt_pct", "scheme", "overlay"]
FLAG_NAMES = ["input_during_window", "not_foreground", "on_battery", "battery_saver", "power_change",
              "thermal_passive", "desktop_not_default", "screensaver", "sample_gaps", "short_window"]


class CsvError(Exception):
    pass


def num(s):
    s = s.strip()
    if not s:
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    if math.isnan(v) or math.isinf(v):
        return None
    return int(v) if v.is_integer() and abs(v) < 1e15 and "." not in s else v


def load(path):
    if not os.path.isfile(path):
        raise CsvError("no such file: %s" % path)
    with open(path, "rb") as f:
        data = f.read()
    info = dict(bytes=len(data), header_ok=False, rows=0, bad_rows=0, truncated_last_line=False, missing_columns=[])
    if not data.strip():
        raise CsvError("empty csv: %s" % path)
    text = data.decode("utf-8-sig", "replace")
    lines = text.split("\n")
    info["truncated_last_line"] = not text.endswith("\n")
    lines = lines[:-1]  # "" after the last newline, or the partial last row
    lines = [ln.rstrip("\r") for ln in lines]
    if not lines or not lines[0].strip():
        raise CsvError("no complete header line in %s" % path)
    header = [h.strip() for h in next(csv.reader([lines[0]]))]
    info["header_ok"] = header[:len(COLUMNS)] == COLUMNS  # extra columns after the known ones (pkg_w ...) are allowed
    info["missing_columns"] = [c for c in COLUMNS if c not in header]
    if "t_s" not in header or "epoch_s" not in header:
        raise CsvError("not a sys.csv (no t_s / epoch_s column): %s" % path)
    idx = {c: header.index(c) for c in COLUMNS if c in header}
    rows = []
    for fields in csv.reader(lines[1:]):
        if not fields or (len(fields) == 1 and not fields[0].strip()):
            continue
        if len(fields) != len(header):
            info["bad_rows"] += 1
            continue
        r = {c: None for c in COLUMNS}
        for c, i in idx.items():
            v = fields[i]
            r[c] = (v.strip() or None) if c in TEXT else num(v)
        if r["t_s"] is None or r["epoch_s"] is None:
            info["bad_rows"] += 1
            continue
        r["_i"] = len(rows)
        rows.append(r)
    info["rows"] = len(rows)
    return rows, info


def vals(rows, col):
    return [r[col] for r in rows if r[col] is not None]


def mean(xs, d):
    return round(sum(xs) / len(xs), d) if xs else None


def tracked(rows, col):
    first = last = prev = None
    changes = []
    for r in rows:
        v = r[col]
        if v is None:
            continue
        if first is None:
            first = v
        elif v != prev:
            changes.append({"t_s": r["t_s"], "epoch_s": r["epoch_s"], "from": prev, "to": v})
        prev = last = v
    return {"first": first, "last": last, "changes": changes}


def block(rows, all_rows, win_start=None):
    n = len(rows)
    b = {"rows": n,
         "first_epoch_s": rows[0]["epoch_s"] if n else None,
         "last_epoch_s": rows[-1]["epoch_s"] if n else None,
         "span_s": round(rows[-1]["t_s"] - rows[0]["t_s"], 3) if n else None}
    gaps = [rows[k]["t_s"] - rows[k - 1]["t_s"] for k in range(1, n)]
    b["max_gap_s"] = round(max(gaps), 3) if gaps else None
    idles = vals(rows, "idle_s")
    b["idle_min_s"] = min(idles) if idles else None
    ev = 0
    for k, r in enumerate(rows):
        i = r["_i"]
        if i == 0 or r["idle_s"] is None:
            continue
        dt = r["t_s"] - all_rows[i - 1]["t_s"]
        if r["idle_s"] < dt - 0.05:
            if k == 0 and win_start is not None and r["epoch_s"] - r["idle_s"] < win_start:
                continue
            ev += 1
    b["input_events"] = ev
    fg = vals(rows, "fg_game")
    b["fg_game_share"] = round(sum(fg) / len(fg), 4) if fg else None
    alive = vals(rows, "game_alive")
    b["game_alive_all"] = all(v == 1 for v in alive) if alive else None
    b["desktop_not_default_rows"] = sum(1 for r in rows if r["input_desktop"] is not None and r["input_desktop"] != "Default")
    b["screensaver_rows"] = sum(1 for r in rows if r["screensaver"] == 1)
    b["cpu_util_mean"] = mean(vals(rows, "cpu_util_pct"), 2)
    eff = vals(rows, "eff_mhz")
    b["eff_mhz_mean"] = mean(eff, 0)
    b["eff_mhz_min"] = min(eff) if eff else None
    b["p_eff_mhz_mean"] = mean(vals(rows, "p_eff_mhz"), 0)
    b["e_eff_mhz_mean"] = mean(vals(rows, "e_eff_mhz"), 0)
    b["p_util_mean"] = mean(vals(rows, "p_util_pct"), 2)
    b["e_util_mean"] = mean(vals(rows, "e_util_pct"), 2)
    tzp = vals(rows, "tz_passive_min_pct")
    b["tz_passive_min"] = min(tzp) if tzp else None
    tzt = vals(rows, "tz_temp_max_c")
    b["tz_temp_max_c"] = max(tzt) if tzt else None
    for c in TRACKED:
        b[c] = tracked(rows, c)
    return b


def flags_for(w, wrows, start, end, interval):
    f = []
    if w["input_events"] > 0:
        f.append("input_during_window")
    if w["fg_game_share"] is not None and w["fg_game_share"] < 0.99:
        f.append("not_foreground")
    if any(r["ac"] == 0 for r in wrows):
        f.append("on_battery")
    if any(r["batt_saver"] == 1 for r in wrows):
        f.append("battery_saver")
    if w["scheme"]["changes"] or w["overlay"]["changes"] or w["ac"]["changes"]:
        f.append("power_change")
    if w["tz_passive_min"] is not None and w["tz_passive_min"] < 100:
        f.append("thermal_passive")
    if w["desktop_not_default_rows"] > 0:
        f.append("desktop_not_default")
    if w["screensaver_rows"] > 0:
        f.append("screensaver")
    if w["max_gap_s"] is not None and w["max_gap_s"] > 2.5 * interval:
        f.append("sample_gaps")
    if w["rows"] < 0.8 * (end - start) / interval:
        f.append("short_window")
    return f


def fmt(x, d=0, unit=""):
    if x is None:
        return "-"
    if isinstance(x, float):
        x = round(x, d)
        s = ("%." + str(d) + "f") % x if d > 0 else str(int(round(x)))
    else:
        s = str(x)
    return s + unit


def line(res):
    w, r = res["window"], res["run"]
    share = None if w["fg_game_share"] is None else w["fg_game_share"] * 100.0
    sch = w["scheme"]["last"] if w["rows"] else r["scheme"]["last"]
    ovl = w["overlay"]["last"] if w["rows"] else r["overlay"]["last"]
    return ("SYS window %d rows/%s s (run %d rows/%s s): fg_game %s, input_events %d, idle_min %s, eff %s MHz "
            "(min %s; P %s / E %s), util %s (P %s / E %s), tz_passive_min %s, temp_max %s, ac %s, saver %s, batt %s, "
            "scheme '%s', overlay %s, game_alive_all %s; flags: %s" % (
                w["rows"], fmt(w["span_s"], 1), r["rows"], fmt(r["span_s"], 1), fmt(share, 1, "%"), w["input_events"],
                fmt(w["idle_min_s"], 1, " s"), fmt(w["eff_mhz_mean"]), fmt(w["eff_mhz_min"]), fmt(w["p_eff_mhz_mean"]),
                fmt(w["e_eff_mhz_mean"]), fmt(w["cpu_util_mean"], 1, "%"), fmt(w["p_util_mean"], 1),
                fmt(w["e_util_mean"], 1), fmt(w["tz_passive_min"], 0), fmt(w["tz_temp_max_c"], 1, " C"),
                fmt(w["ac"]["last"]), fmt(w["batt_saver"]["last"]), fmt(w["batt_pct"]["last"], 0, "%"),
                sch if sch is not None else "-", ovl if ovl is not None else "-", w["game_alive_all"],
                ", ".join(res["flags"]) if res["flags"] else "none"))


def write_json(path, obj):
    if not path:
        return
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=1)
        f.write("\n")


def main():
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Summary of a sys-csv.ps1 sys.csv over a measure window.")
    ap.add_argument("--csv", required=True)
    ap.add_argument("--start-epoch", type=float, required=True)
    ap.add_argument("--end-epoch", type=float, required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--interval", type=float, default=1.0)
    a = ap.parse_args()
    interval = a.interval if a.interval > 0 else 1.0
    csv_path = os.path.abspath(a.csv)
    try:
        rows, info = load(csv_path)
    except (CsvError, OSError) as e:
        err = {"error": str(e), "csv": csv_path, "window_start_epoch": a.start_epoch, "window_end_epoch": a.end_epoch}
        try:
            write_json(a.out, err)
        except OSError as e2:
            print("SYS error: cannot write %s: %s" % (a.out, e2))
        print("SYS error: %s" % e)
        return 1
    wrows = [r for r in rows if a.start_epoch <= r["epoch_s"] <= a.end_epoch]
    w = block(wrows, rows, a.start_epoch)
    run = block(rows, rows)
    res = {"csv": csv_path, "window_start_epoch": a.start_epoch, "window_end_epoch": a.end_epoch,
           "interval_s": interval, "flags": flags_for(w, wrows, a.start_epoch, a.end_epoch, interval),
           "window": w, "run": run, "file": info}
    text = line(res)
    res["summary"] = text
    try:
        write_json(a.out, res)
    except OSError as e:
        print("SYS error: cannot write %s: %s" % (a.out, e))
        return 1
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

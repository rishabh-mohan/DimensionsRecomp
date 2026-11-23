#!/usr/bin/env python3
"""W6 environment record (Agent 12, task #11, 2026-11-22): the power overlay and the quiet gate.

Agent 1 (19:31) asked that W6's gates also record (1) the power overlay, which was
best_efficiency in every W5 run, and (2) whether the relaxed Defender gate was used.

(1) Power overlay, per run, from the run's sys.json (written when the matrix has
    "sys_csv": true; sampled each second by bench/agent8/run/drivers/sys-csv.ps1 and summarised
    by the runner; run.json's copy is the fallback): scheme, overlay, AC and battery saver at the
    window's first and last row, plus any change inside the window. The runner already excludes
    a run whose window sees a power change; this adds the view across runs: which overlays
    occur, and whether every arm ran under the same one.
(2) Quiet gate, from --gate-log. Two log formats:
    - Agent 5's night launcher (bench/agent5/launch/run-night.ps1) writes one line per gate:
      "HH:mm:ss quiet gate: STRICT (MsMpEng a/b/c, OfficeClickToRun a/b/c, CrossDeviceService
      a/b/c)" or "HH:mm:ss quiet gate: RELAXED (<same>; after N min)". A window starts after
      either. RELAXED = MsMpEng passed only under the 30-min rule (<= 1.2 cores, stable).
      "GAVE UP (...; window not started)" and "DEADLINE (...; window not started)" mean that no
      window ran (exit 3: wrong gate log?). Its files: bench/agent5/launch/status/
      window-<id>-<HHmm>.log (the one to give for a window), status/log.txt and status/gate.txt;
      never status-dryrun/<tag>/. The last gate line in the log wins.
    - build/agent1/w5/quiet-check.ps1's log ("HH:MM:SS pass|FAIL n/N | Defender x Office y
      CrossDevice z ... | busy b of 12 ...", then "QUIET" or "NOT QUIET after M min"). QUIET = the
      strict gate passed (Defender, Office and CrossDevice each < 0.1 core for 3 one-minute
      averages). NOT QUIET, with the window run anyway = the relaxed gate was used, as in W5
      (17:51:55, Defender 0.77-1.14 cores).
    --gate sets it by hand and wins over the log.
Also per run: the non-game load over the window, as in Agent 1's W5 note (SESSION2 18:34):
cpu_util_mean x logical CPUs / 100 - the game's cpu_cores_mean. It includes Defender, the
samplers and any agent activity. A scored run more than NG_MARGIN (1.0) cores above the scored
median is flagged (information for the read-out, not an exit code). The time before "quiet
gate" on a launcher line is the gate's end, for the gap to the window start (the matrix dir's
HHMM). A gate line inside the start minute is 0 min, a gap across midnight is unwrapped, and the
text WARNs if the gap is more than 30 min or the gate line comes after the start (task #24 fix).

usage: python w6_env_record.py <matrix out dir> [--gate-log FILE] [--gate strict|relaxed|none]
                               [--ncpu N] [--json OUT]
       python w6_env_record.py --selftest
Last line: "RECORD: overlay ...; quiet gate ...". Exit 0: one overlay in every run, no change
inside any window, and the gate is known. 1: the overlay differs between runs or changes inside
a window. 3: a run has no sys data, the gate is not recorded, or the gate log says that no
window started (GAVE UP / DEADLINE). 2: usage, or no results.csv.
"""
import argparse
import collections
import csv
import io
import json
import os
import re
import statistics
import sys
import tempfile

W5_OVERLAY = "best_efficiency"
GATE_START = re.compile(r"^(?P<ts>\d\d:\d\d:\d\d) start: limit (?P<limit>[\d.]+) core, need (?P<need>\d+)")
GATE_SAMPLE = re.compile(
    r"^(?P<ts>\d\d:\d\d:\d\d) (?P<res>pass|FAIL) (?P<ok>\d+)/(?P<need>\d+) \| Defender (?P<defender>[\d.]+) "
    r"Office (?P<office>[\d.]+) CrossDevice (?P<cross>[\d.]+).*?\| busy (?P<busy>[\d.]+) of (?P<n>\d+)")
GATE_QUIET = re.compile(r"^(?P<ts>\d\d:\d\d:\d\d) QUIET\s*$")
GATE_NOT = re.compile(r"^(?P<ts>\d\d:\d\d:\d\d) NOT QUIET after (?P<min>\d+) min")
GATE_LINE = re.compile(r"(?i)\bquiet gate\b\W*(?P<mode>strict|relaxed|gave up|deadline)\b")
GATE_PROCS = re.compile(r"\b(?P<name>MsMpEng|OfficeClickToRun|CrossDeviceService) (?P<v>[^,;)]+)")  # a/b/c, as '0.00'; 'unreadable' and 'n/a' give None
NO_WINDOW = ("gave up", "deadline")  # launcher gate results after which no window ran
DIR_TIME = re.compile(r"\d{8}-(?P<hh>\d\d)(?P<mm>\d\d)(?:-\d+)?$")
LINE_TIME = re.compile(r"(?:^|[ T\[])(\d\d:\d\d:\d\d)")  # a time before "quiet gate" on a launcher line
NG_MARGIN = 1.0  # flag a scored run whose non-game load is this many cores above the scored median


def read_json(path):
    try:
        with open(path, encoding="utf-8-sig") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def sys_data(run_dir):
    s = read_json(os.path.join(run_dir, "sys.json"))
    if isinstance(s, dict) and isinstance(s.get("window"), dict):
        return s, "sys.json"
    r = read_json(os.path.join(run_dir, "run.json"))
    if isinstance(r, dict):
        for v in r.values():
            if isinstance(v, dict) and isinstance(v.get("window"), dict) and "run" in v:
                return v, "run.json"
    return None, None


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def load(mdir, ncpu):
    with open(os.path.join(mdir, "results.csv"), encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    runs = []
    for row in rows:
        rd = row.get("run_dir") or ""
        if not os.path.isdir(rd):
            alt = os.path.join(mdir, "runs", os.path.basename(rd.replace("\\", "/")))
            if os.path.isdir(alt):
                rd = alt
        s, src = sys_data(rd) if os.path.isdir(rd) else (None, None)
        w = (s or {}).get("window") or {}
        util, cores = num(w.get("cpu_util_mean")), num(row.get("cpu_cores_mean"))
        runs.append({
            "seq": row.get("seq"), "round": row.get("round"), "arm": row.get("arm"),
            "rep": row.get("rep"), "scored": row.get("scored") == "True",
            "status": row.get("status"), "excluded": row.get("excluded") == "True",
            "flags": ";".join(x for x in (row.get("flags_excluding"), row.get("flags_info")) if x),
            "run_dir": rd, "sys_src": src,
            "scheme": w.get("scheme"), "overlay": w.get("overlay"), "ac": w.get("ac"),
            "saver": w.get("batt_saver"), "overlay_run": ((s or {}).get("run") or {}).get("overlay"),
            "eff_mhz": w.get("eff_mhz_mean"), "p_mhz": w.get("p_eff_mhz_mean"),
            "e_mhz": w.get("e_eff_mhz_mean"), "util": util, "game_cores": cores,
            "nongame": (round(util * ncpu / 100 - cores, 2)
                        if util is not None and cores is not None else None),
        })
    return runs


def tri(x):
    if not isinstance(x, dict):
        return "-"
    first, last, ch = x.get("first"), x.get("last"), x.get("changes") or []
    text = f"{first}" if first == last else f"{first}->{last}"
    return text + (f" ({len(ch)} change{'' if len(ch) == 1 else 's'})" if ch else "")


def changed(x):
    return isinstance(x, dict) and (bool(x.get("changes")) or x.get("first") != x.get("last"))


def parse_gate(path):
    g = {"source": path, "mode": None, "how": None, "end": None, "limit": None, "samples": [],
         "procs": {}, "manual": False}
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError as exc:
        g["how"] = f"unreadable ({exc.strerror})"
        return g
    for line in lines:
        m = GATE_START.match(line)
        if m:  # a new check in the same log restarts the record
            g.update(mode=None, how=None, end=None, limit=float(m.group("limit")), samples=[], procs={})
            continue
        m = GATE_SAMPLE.match(line)
        if m:
            g["samples"].append({"ts": m.group("ts"), "pass": m.group("res") == "pass",
                                 "defender": float(m.group("defender")),
                                 "office": float(m.group("office")),
                                 "cross": float(m.group("cross")), "busy": float(m.group("busy"))})
            continue
        m = GATE_QUIET.match(line)
        if m:
            g.update(mode="strict", how="QUIET", end=m.group("ts"))
            continue
        m = GATE_NOT.match(line)
        if m:
            g.update(mode="relaxed", how=f"NOT QUIET after {m.group('min')} min", end=m.group("ts"))
            continue
        m = GATE_LINE.search(line)
        if m:
            t = LINE_TIME.search(line[:m.start()])
            procs = {p.group("name"): [num(v) for v in p.group("v").strip().replace("n/a", "na").split("/")]
                     for p in GATE_PROCS.finditer(line, m.end())}
            g.update(mode=m.group("mode").lower(), how=line.strip()[:240],
                     end=t.group(1) if t else None, procs=procs)  # the last gate line wins
    return g


def rng(vals):
    return f"{min(vals):.2f}-{max(vals):.2f}" if vals else "-"


def gate_text(g, start):
    if g is None:
        return "NOT RECORDED (give --gate-log or --gate)"
    if g["manual"]:
        return f"{g['mode'].upper()} (set by hand with --gate)"
    if g["mode"] is None:
        return f"UNKNOWN: {g['source']}: {g['how'] or 'no QUIET / NOT QUIET / quiet gate line'}"
    text = f"{g['mode'].upper()}: {g['source']}: '{g['how']}'"
    if g["end"]:
        text += f" at {g['end']}"
    s = g["samples"]
    if s:
        d = [x["defender"] for x in s]
        fails = sum(1 for x in s if not x["pass"])
        text += (f" (strict limit {g['limit']} core; {len(s)} one-minute samples, {fails} FAIL; "
                 f"Defender {rng(d)} cores, last {min(10, len(d))}: {rng(d[-10:])}; "
                 f"busy {rng([x['busy'] for x in s])} CPUs)")
    if g["mode"] in NO_WINDOW:
        text += "; the launcher started no window after this gate: is this the right gate log?"
    elif g["end"] and start:
        h, m, sec = (int(x) for x in g["end"].split(":"))
        # Minutes from the gate line to the window start (the dir's HHMM). The sum has no date, so a gap of more than
        # 12 h either way is a wrap across midnight (gate 23:58:20, dir 0003: 5 min). Task #24 fix: the old "% 1440"
        # turned a gate line inside the start minute (00:09:01, dir 0009) into "1440 min later" and a WARN.
        gap = start[0] * 60 + start[1] - (h * 60 + m + sec / 60.0)
        if gap <= -720:
            gap += 1440
        elif gap > 720:
            gap -= 1440
        text += f"; the window started at {start[0]:02d}:{start[1]:02d}, "
        if gap > -1:  # the dir name has whole minutes: a gate line inside the start minute is at the start
            text += f"{max(gap, 0.0):.0f} min later"
            if gap > 30:
                text += " (WARN: more than 30 min: is this the right gate log?)"
        else:
            text += (f"{-gap:.0f} min before the gate line (WARN: the gate line is after the window start: "
                     "is this the right gate log?)")
    return text


def record(mdir, gate_log=None, gate=None, ncpu=None, out=None):
    out = out or sys.stdout
    ncpu = ncpu or os.cpu_count() or 12

    def w(text=""):
        print(text, file=out)

    if not os.path.isfile(os.path.join(mdir, "results.csv")):
        w(f"no results.csv in {mdir}")
        return 2, None
    runs = load(mdir, ncpu)
    if not runs:
        w(f"results.csv in {mdir} has no runs")
        return 2, None
    m = DIR_TIME.search(os.path.basename(os.path.normpath(mdir)))
    start = (int(m.group("hh")), int(m.group("mm"))) if m else None
    g = None
    if gate:
        g = {"source": None, "mode": gate, "how": None, "end": None, "limit": None,
             "samples": [], "procs": {}, "manual": True}
    elif gate_log:
        g = parse_gate(gate_log)
    w(f"W6 environment record: {mdir} ({len(runs)} runs in results.csv; {ncpu} logical CPUs)")
    w("| # | arm | rep | status | flags | scheme | overlay (window) | overlay (run) | AC | saver | "
      "eff MHz (P/E) | game cores | non-game cores | sys |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in runs:
        mhz = "-" if r["eff_mhz"] is None else f"{r['eff_mhz']:.0f} ({r['p_mhz']:.0f}/{r['e_mhz']:.0f})"
        w(f"| {r['seq']} | {r['arm']} | {r['rep'] if r['scored'] else 'cold'} | {r['status']}"
          f"{' excl' if r['excluded'] else ''} | {r['flags'] or '-'} | {tri(r['scheme'])} | "
          f"{tri(r['overlay'])} | {tri(r['overlay_run'])} | {tri(r['ac'])} | {tri(r['saver'])} | "
          f"{mhz} | {r['game_cores'] if r['game_cores'] is not None else '-'} | "
          f"{r['nongame'] if r['nongame'] is not None else '-'} | {r['sys_src'] or 'MISSING'} |")
    have = [r for r in runs if isinstance(r["overlay"], dict)]
    missing = [r for r in runs if r["sys_src"] is None or not isinstance(r["overlay"], dict)]
    by_val = collections.Counter(tri(r["overlay"]) for r in have)
    moved = [r for r in have if changed(r["overlay"])]
    uniform = len(by_val) == 1 and not moved
    if uniform:
        val = next(iter(by_val))
        ov = f"{val} in {len(have)}/{len(runs)} runs, no change inside any window"
        if val != W5_OVERLAY:
            ov += f" (differs from W5's {W5_OVERLAY}: don't compare absolute numbers with W5)"
    elif have:
        per_arm = collections.defaultdict(collections.Counter)
        for r in have:
            per_arm[r["arm"]][tri(r["overlay"])] += 1
        ov = ("MIXED: " + ", ".join(f"{v} x{c}" for v, c in by_val.most_common()) + "; per arm: "
              + "; ".join(f"{a} " + ", ".join(f"{v} x{c}" for v, c in cnt.items())
                          for a, cnt in per_arm.items()))
        if moved:
            ov += "; changed inside the window: " + ", ".join(f"#{r['seq']} {r['arm']}" for r in moved)
    else:
        ov = "NO DATA (no run has sys data)"
    w(f"power overlay: {ov}")
    outside = [r for r in have if changed(r["overlay_run"]) and not changed(r["overlay"])]
    if outside:
        w("note: the overlay changed outside the window (boot or close) in "
          + ", ".join(f"#{r['seq']} {r['arm']} ({tri(r['overlay_run'])})" for r in outside))
    schemes = collections.Counter(tri(r["scheme"]) for r in have)
    acs = collections.Counter(tri(r["ac"]) for r in have)
    savers = collections.Counter(tri(r["saver"]) for r in have)
    w("scheme: " + ", ".join(f"{v} x{c}" for v, c in schemes.items()) + "; AC: "
      + ", ".join(f"{v} x{c}" for v, c in acs.items()) + "; battery saver: "
      + ", ".join(f"{v} x{c}" for v, c in savers.items()))
    scored = [r["nongame"] for r in runs if r["scored"] and r["nongame"] is not None]
    cold = [r["nongame"] for r in runs if not r["scored"] and r["nongame"] is not None]
    ng = (f"{rng(scored)} cores (median {statistics.median(scored):.2f}) in {len(scored)} scored runs"
          if scored else "-")
    if cold:
        w(f"non-game load: {ng}; unscored/cold {', '.join(f'{x:.2f}' for x in cold)}")
    else:
        w(f"non-game load: {ng}")
    flagged = []
    if scored:
        med = statistics.median(scored)
        flagged = [r for r in runs if r["scored"] and r["nongame"] is not None and r["nongame"] > med + NG_MARGIN]
        w(f"non-game load flag (scored runs above the median {med:.2f} + {NG_MARGIN:.1f} cores): "
          + (", ".join(f"#{r['seq']} {r['arm']} r{r['rep']} {r['nongame']:.2f}" for r in flagged) or "none"))
    if missing:
        w("WARN: no sys data in " + ", ".join(f"#{r['seq']} {r['arm']}" for r in missing))
    gt = gate_text(g, start)
    w(f"quiet gate: {gt}")
    gate_short = "NOT RECORDED" if g is None else ((g["mode"] or "UNKNOWN").upper()
                                                    + (" (by hand)" if g["manual"] else "")
                                                    + (" (no window started: wrong gate log?)"
                                                       if g["mode"] in NO_WINDOW else ""))
    if uniform:
        ov_short = f"{next(iter(by_val))} ({len(have)}/{len(runs)}, no change)"
    else:
        ov_short = "MIXED" if have else "NO DATA"
    w(f"RECORD: overlay {ov_short}; quiet gate {gate_short}; non-game load {rng(scored)} cores")
    code = 1 if (have and not uniform) else (
        3 if (missing or g is None or g["mode"] is None or g["mode"] in NO_WINDOW) else 0)
    res = {"tool": "w6_env_record.py", "matrix_dir": mdir, "exit": code, "overlay": ov,
           "overlay_uniform": uniform, "gate": g, "gate_text": gt, "runs": runs,
           "nongame_scored": scored, "nongame_flagged": [r["seq"] for r in flagged]}
    return code, res


def selftest():
    def tri_v(v):
        return {"first": v, "last": v, "changes": []}

    def sysj(overlay="best_efficiency", last=None, changes=(), util=50.0):
        win = {"cpu_util_mean": util, "eff_mhz_mean": 1000.0, "p_eff_mhz_mean": 1900.0,
               "e_eff_mhz_mean": 800.0, "scheme": tri_v("Balanced"), "ac": tri_v(1),
               "batt_saver": tri_v(0),
               "overlay": {"first": overlay, "last": last or overlay, "changes": list(changes)}}
        return {"window": win, "run": dict(win), "summary": "SYS test"}

    quiet = ["17:31:51 start: limit 0.1 core, need 3 consecutive 1-min averages, max 20 min, 12 logical CPUs"]
    quiet += [f"17:3{i}:52 pass {i - 1}/3 | Defender 0.0{i}0 Office 0.000 CrossDevice 0.020 Search 0.004 | "
              f"busy 2.26 of 12 | top x=1.00" for i in (2, 3, 4)]
    quiet += ["17:34:52 QUIET"]
    notq = ["17:31:51 start: limit 0.1 core, need 3 consecutive 1-min averages, max 20 min, 12 logical CPUs",
            "17:32:52 FAIL 0/3 | Defender 1.137 Office 0.000 CrossDevice 0.028 Search 0.004 | busy 4.26 of 12 "
            "| top msmpeng=1.14", "17:33:53 FAIL 0/3 | Defender 0.888 Office 0.000 CrossDevice 0.029 Search "
            "0.009 | busy 5.12 of 12 | top msmpeng=0.89", "17:51:55 NOT QUIET after 20 min"]
    good = [("s0", sysj(), "sys.json"), ("p2", sysj(), "sys.json"), ("p2f", sysj(), "sys.json"),
            ("p2fc", sysj(), "sys.json")]
    cases = [
        ("uniform overlay, strict gate", good, quiet, None, 0,
         lambda r: r["overlay_uniform"] and r["gate"]["mode"] == "strict" and r["nongame_scored"] == [3.0] * 4),
        ("one run on another overlay, relaxed gate", good[:3] + [("p2fc", sysj("balanced"), "sys.json")],
         notq, None, 1, lambda r: not r["overlay_uniform"] and r["gate"]["mode"] == "relaxed"
         and "MIXED" in r["overlay"] and "p2fc balanced x1" in r["overlay"]),
        ("overlay changes inside a window", good[:3] + [
            ("p2fc", sysj("best_efficiency", "balanced", [{"t": 5, "to": "balanced"}]), "sys.json")],
         quiet, None, 1, lambda r: "changed inside the window: #4 p2fc" in r["overlay"]),
        ("a run without sys data", good[:3] + [("p2fc", None, "sys.json")], quiet, None, 3,
         lambda r: r["overlay_uniform"]),
        ("no gate given", good, None, None, 3, lambda r: r["gate"] is None),
        ("--gate wins over the log", good, quiet, "relaxed", 0,
         lambda r: r["gate"]["mode"] == "relaxed" and r["gate"]["manual"]),
        ("run.json fallback; Agent 5's launcher RELAXED line",
         [(a, s, "run.json") for a, s, _ in good],
         ["17:20:02 launcher start", "17:50:12 quiet gate: RELAXED (MsMpEng 0.91/0.88/0.95, OfficeClickToRun "
          "0.00/0.00/0.00, CrossDeviceService 0.02/0.03/0.02; after 30 min)"], None, 0,
         lambda r: r["overlay_uniform"] and r["gate"]["mode"] == "relaxed" and r["gate"]["end"] == "17:50:12"
         and r["gate"]["procs"]["MsMpEng"] == [0.91, 0.88, 0.95] and "6 min later" in r["gate_text"]
         and all(x["sys_src"] == "run.json" for x in r["runs"]) and r["nongame_flagged"] == []),
        ("another overlay in every run", [(a, sysj("balanced"), f) for a, _, f in good], quiet, None, 0,
         lambda r: r["overlay_uniform"] and "differs from W5" in r["overlay"]),
        ("a busy run is flagged (5.40 > median 3.00 + 1.0)", good[:3] + [("p2fc", sysj(util=70.0), "sys.json")],
         quiet, None, 0, lambda r: r["nongame_flagged"] == ["4"]),
        ("Agent 5's launcher GAVE UP line: no window started, exit 3", good,
         ["17:50:12 quiet gate: GAVE UP (MsMpEng unreadable/1.88/1.95, OfficeClickToRun n/a/0.00/0.00, "
          "CrossDeviceService 0.02/0.03/0.02; after 120 min; window not started)"], None, 3,
         lambda r: r["gate"]["mode"] == "gave up" and "started no window" in r["gate_text"]
         and "window started at" not in r["gate_text"] and r["gate"]["procs"]["MsMpEng"] == [None, 1.88, 1.95]
         and r["gate"]["procs"]["OfficeClickToRun"] == [None, 0.0, 0.0]),
    ]
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        for n, (name, runs, gate_lines, gate, want, extra) in enumerate(cases, 1):
            mdir = os.path.join(tmp, f"case{n}", "20261122-1756")
            os.makedirs(os.path.join(mdir, "runs"))
            rows = []
            for i, (arm, sj, where) in enumerate(runs, 1):
                rd = os.path.join(mdir, "runs", f"18{i:02d}-{arm}-r1")
                os.makedirs(rd)
                if sj is not None:
                    with open(os.path.join(rd, where), "w", encoding="utf-8") as fh:
                        json.dump(sj if where == "sys.json" else {"sys": sj, "status": "OK"}, fh)
                rows.append({"seq": i, "round": 1, "arm": arm, "rep": 1, "scored": "True",
                             "status": "OK", "excluded": "False", "flags_excluding": "",
                             "flags_info": "", "cpu_cores_mean": "3.0", "run_dir": rd})
            with open(os.path.join(mdir, "results.csv"), "w", encoding="utf-8", newline="") as fh:
                wr = csv.DictWriter(fh, fieldnames=list(rows[0]), quoting=csv.QUOTE_ALL)
                wr.writeheader()
                wr.writerows(rows)
            gate_log = None
            if gate_lines:
                gate_log = os.path.join(tmp, f"case{n}-gate.log")
                with open(gate_log, "w", encoding="utf-8", newline="") as fh:
                    fh.write("".join(x + "\r\n" for x in gate_lines))
            code, r = record(mdir, gate_log=gate_log, gate=gate, ncpu=12, out=io.StringIO())
            try:
                ok = code == want and bool(extra(r))
            except (KeyError, TypeError, IndexError):
                ok = False
            results.append((ok, f"{name}: exit {code} (want {want})"))
        code, r = record(os.path.join(tmp, "nothing-here"), out=io.StringIO())
        results.append((code == 2 and r is None, f"no results.csv: exit {code}"))
        buf = io.StringIO()
        record(os.path.join(tmp, "case2", "20261122-1756"), gate_log=os.path.join(tmp, "case2-gate.log"),
               ncpu=12, out=buf)
        text = buf.getvalue()
        results.append(("at 17:51:55" in text and "17:56, 4 min later" in text
                        and "Defender 0.89-1.14 cores" in text,
                        "gate text: end time, gap to the window start, Defender range"))
        strict = (" quiet gate: STRICT (MsMpEng 0.00/0.00/0.00, OfficeClickToRun 0.00/0.00/0.00, "
                  "CrossDeviceService 0.00/0.00/0.00)")
        gap_log = os.path.join(tmp, "gap-gate.log")

        def gap_text(ts, start):
            with open(gap_log, "w", encoding="utf-8", newline="") as fh:
                fh.write(ts + strict + "\r\n")
            return gate_text(parse_gate(gap_log), start)

        for ts, start, want_in, warn, what in (  # task #24: the gap without the old "% 1440"
                ("00:09:01", (0, 9), "00:09, 0 min later", False,
                 "a gate line inside the start minute (00:09:01, dir 0009; the old code said '1440 min')"),
                ("23:58:20", (0, 3), "00:03, 5 min later", False, "across midnight (23:58:20, dir 0003)"),
                ("23:20:00", (0, 3), "00:03, 43 min later (WARN: more than 30 min", True,
                 "43 min across midnight (23:20:00, dir 0003) is a WARN"),
                ("00:15:00", (0, 9), "00:09, 6 min before the gate line (WARN: the gate line is after the window "
                 "start", True, "a gate line 6 min after the window start (00:15:00, dir 0009) is a WARN")):
            t = gap_text(ts, start)
            results.append((want_in in t and ("WARN" in t) == warn, f"gate gap: {what}"))
    for ok, text in results:
        print(f"{'ok  ' if ok else 'FAIL'} {text}")
    bad = sum(1 for ok, _ in results if not ok)
    print(f"SELFTEST {'PASS' if not bad else 'FAIL'} ({len(results) - bad}/{len(results)} checks)")
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description="W6 environment record: the power overlay per run and "
                                             "the quiet gate (strict or relaxed).")
    ap.add_argument("matrix_dir", nargs="?", help="a run-matrix output dir (with results.csv)")
    ap.add_argument("--gate-log", metavar="FILE", help="the launcher's window log (bench/agent5/launch/status/"
                                                             "window-<id>-<HHmm>.log) or a quiet-check log")
    ap.add_argument("--gate", choices=("strict", "relaxed", "none"), help="set the gate by hand")
    ap.add_argument("--ncpu", type=int, help="logical CPUs (default: this PC's)")
    ap.add_argument("--json", metavar="OUT", help="also write the record as JSON")
    ap.add_argument("--selftest", action="store_true", help="run the built-in tests")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.matrix_dir:
        ap.error("give a matrix output dir")
    code, res = record(a.matrix_dir, gate_log=a.gate_log, gate=a.gate, ncpu=a.ncpu)
    if a.json and res is not None:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1)
    return code


if __name__ == "__main__":
    sys.exit(main())

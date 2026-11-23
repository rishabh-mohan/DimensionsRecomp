#!/usr/bin/env python3
"""P2 counter check (Agent 12): P2's memexport full-buffer fallback counter.

Written for task #32 (16:59). Revised in task #11 (19:5x) after an independent read-only
check against the s4-p2c source and S4b's composed trees.

Reads a run's game.log and prints the counter that s4-p2c adds to ReportSlowFrame's
slow-frame line. Sources: build/agent12/s4-p2c/memexport-full-buffer-counter.diff 29E02E24...;
in S4b, src/graphics/d3d12/command_processor.cpp L290-304 of the composed trees
build/agent2/s4b-check/o1-v3 and o2-v3. The line:

  slow frame #N: X ms | ... | memexport syncs S (K KB), on demand D (K KB) | memexport full-buffer Fx (total T)

  F  fallback draws in that frame: memexporting draws with no known destination range,
     for which IssueDraw calls RangeWrittenByGpu(0, SharedMemory::kBufferSize).
  T  running total since process start. The count is taken on every swap, before the
     slow_frame_log_ms threshold, so T also counts frames that were not logged and frames
     in rotated logs that are gone. The last counter line's T covers the process up to
     that frame. Draws after it (the tail) are not covered.

The field is printed only when slow_frame_log_ms is set, and only by builds with s4-p2c
(S4b). Use slow_frame_log_ms=1: then every frame is logged and the tail is only the
shutdown. The counter does not depend on P2's cvar (shared_memory_single_hold_rearm): it
counts the path with P2 on or off.

Processes: a new process starts at a "Startup: launching the module" line, where the frame
index restarts, or where T falls.

RESULT (last line) and exit code:
  PASS     (exit 0) T = 0 in every process, and every process has counter lines.
  FAIL     (exit 1) T > 0 in some process: the fallback ran. P2 ON waits for Agent 1's cap
           decision (b2r S22).
  PARTIAL  (exit 3) T = 0 where the counter shows, but some process in the logs has no
           counter lines (no slow-frame lines at all, or lines without the field), or lines
           without the field sit inside a process with it (two builds in one log?). Not a pass.
  NO DATA  (exit 3) no counter field at all: no slow-frame lines (slow_frame_log_ms unset, or
           the log level hides info lines), lines without the field (no s4-p2c), or no log.
  ERROR    (exit 4) the script failed (an unreadable file, or a bug). Exit 2 is a usage error.

WARNs that leave the verdict as it is:
  - a process's last slow-frame line has no field (cut off at exit);
  - the log goes on more than 5 s after a process's last counter line (fallback draws in that
    time are not in T);
  - several processes (T is the sum of their last totals; the max T on any line is printed
    too);
  - T rises by less than a frame's F.

Coverage: a PASS covers only the scenes the run went through. The script also sums the
memexport fields of the same lines (invalidations on memexport pages, syncs, on demand).
Any of them above 0 means memexporting draws with known ranges ran in the logged frames.
All 0 is not proof that no memexporting draw ran. The log's time range is printed, so a
stale game.log can be spotted (for example, when this run logged somewhere else).

Not counted, by s4-p2c's design: a fallback draw that hits an error return after its
RequestRange(0, kBufferSize) upload but before RangeWrittenByGpu. Only error paths do this.

Logs: a run dir is read with its rotated logs, oldest first: game.N.log ... game.1.log, then
game.log. spdlog renames N-1 to N, so game.1.log is the newest rotated file. If none of these
exist, log.txt is read. Log files given explicitly are read in the order given. If the cvar
log_file is empty, the SDK writes logs/<app>_NNN.log instead: give those files explicitly.

--bin PATH: also report whether the .exe/.dll files in PATH contain the field's format string,
i.e. whether that build has s4-p2c. PATH is a file, or a dir that is searched with its
subfolders. Informational only.

usage: python p2c_check.py <run dir | log files, oldest first> [--json OUT] [--bin PATH]
       python p2c_check.py --selftest
"""
import argparse
import datetime
import io
import json
import os
import re
import sys
import tempfile

# The slow-frame line: s4-p2c new/command_processor.cpp L279-284; S4b o1-v3/o2-v3
# src/graphics/d3d12/command_processor.cpp L291-296. Un-anchored, like
# bench/agent5/s4_slowframe.py, so a field added after this one later still matches.
SLOW = re.compile(r"slow frame #(?P<idx>\d+): (?P<ms>[\d.]+) ms \|")
FIELD = re.compile(r"\| memexport full-buffer (?P<f>\d+)x \(total (?P<t>\d+)\)")
MEMEXPORT = re.compile(
    r"\(on memexport pages (?P<pc>\d+)x (?P<pkb>\d+) KB\) \| "
    r"memexport syncs (?P<sc>\d+) \((?P<skb>\d+) KB\), on demand (?P<dc>\d+) \((?P<dkb>\d+) KB\)")
# spdlog's file pattern "[%Y-%m-%d %H:%M:%S.%e] [%l] [%n] [t%t] %v" (SDK include/rex/logging/types.h L80).
STAMP = re.compile(r"^\[(?P<ts>\d{4}-\d\d-\d\d \d\d:\d\d:\d\d(?:\.\d+)?)\]")
# Logged once per process before the first frame (the game's startup log).
START = re.compile(r"\] Startup: launching the module\b")
ROT = re.compile(r"^game\.(\d+)\.log$")
# The field's format string as it sits in the binary (fmt keeps the literal).
LITERAL = b"memexport full-buffer {}x (total {})"
# S4b's format string, copied from o1-v3 command_processor.cpp L291-296. The selftest builds its
# lines from it ("{}" and "{:.1f}" mean the same in fmt and in Python's str.format).
REAL_FORMAT = ("slow frame #{}: {:.1f} ms | gpu-thread idle {:.1f} | host-gpu wait {:.1f} ({}x) | "
               "shader translate {:.1f} ({}x) | pipeline create {:.1f} ({}x), new {} | "
               "texture load {:.1f} ({}x) | readback {}x {} KB, {} stalled | "
               "cpu-write invalidations {}x {} KB (on memexport pages {}x {} KB) | "
               "memexport syncs {} ({} KB), on demand {} ({} KB) | "
               "memexport full-buffer {}x (total {})")
# In a complete log with slow_frame_log_ms=1 the first slow frame is #2 (ReportSlowFrame's
# first call always returns).
LOST_LOG_FIRST_INDEX = 50
TAIL_WARN_S = 5.0
EXIT = {"PASS": 0, "FAIL": 1, "PARTIAL": 3, "NO DATA": 3, "ERROR": 4}
ME_KEYS = ("page_inval", "page_kb", "syncs", "sync_kb", "on_demand", "on_demand_kb")


def resolve(paths):
    """Run dirs expand to their rotated logs, oldest first; files are kept in the given order."""
    files, missing = [], []
    for path in paths:
        if os.path.isfile(path):
            files.append(path)
            continue
        if not os.path.isdir(path):
            missing.append(path)
            continue
        rot = []
        for name in os.listdir(path):
            m = ROT.match(name)
            if m:
                rot.append((int(m.group(1)), name))
        found = [os.path.join(path, name) for _, name in sorted(rot, reverse=True)]
        base = os.path.join(path, "game.log")
        if os.path.isfile(base):
            found.append(base)
        elif not found and os.path.isfile(os.path.join(path, "log.txt")):
            found.append(os.path.join(path, "log.txt"))
        if not found:
            missing.append(base)
        files += found
    return files, missing


def parse_ts(ts):
    if not ts:
        return None
    try:
        return datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f" if "." in ts else "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def new_proc(start=None):
    return {"start": start, "first": None, "first_idx": None, "last": None, "last_idx": None,
            "slow_lines": 0, "field_lines": 0, "nofield_lines": 0, "first_nofield": None,
            "last_nofield": None, "last_is_nofield": False, "last_counter": None, "last_ts": None,
            "end_ts": None, "total": 0, "f_sum": 0, "hit_lines": 0, "max_f": 0, "first_hit": None}


def scan(files):
    s = {"files": files, "lines": 0, "slow_lines": 0, "field_lines": 0, "nofield_lines": 0,
         "first_ts": None, "last_ts": None, "max_t": 0, "processes": [], "notes": [], "warnings": [],
         "memexport": dict({k: 0 for k in ME_KEYS}, parsed_lines=0, active_lines=0,
                           first_active=None)}
    me = s["memexport"]
    proc = None

    def begin(start=None):
        p = new_proc(start)
        s["processes"].append(p)
        return p

    for path in files:
        name = os.path.basename(path)
        with open(path, encoding="utf-8", errors="replace") as fh:
            for lineno, line in enumerate(fh, 1):
                s["lines"] += 1
                where = f"{name}:{lineno}"
                stamp = STAMP.match(line)
                ts = stamp.group("ts") if stamp else None
                if ts:
                    if s["first_ts"] is None:
                        s["first_ts"] = ts
                    s["last_ts"] = ts
                if START.search(line):
                    proc = begin(where)
                    proc["end_ts"] = ts
                    continue
                m = SLOW.search(line)
                if not m:
                    if proc is not None and ts:
                        proc["end_ts"] = ts
                    continue
                s["slow_lines"] += 1
                idx = int(m.group("idx"))
                fm = FIELD.search(line)
                f, t = (int(fm.group("f")), int(fm.group("t"))) if fm else (None, None)
                if proc is not None and proc["slow_lines"] and (
                        idx <= proc["last_idx"] or (fm is not None and t < proc["total"])):
                    if idx > proc["last_idx"]:
                        s["warnings"].append(
                            f"{where}: T fell from {proc['total']} to {t} with no frame-index "
                            "restart; counted as a new process")
                    proc = None
                if proc is None:
                    proc = begin()
                if ts:
                    proc["end_ts"] = ts
                proc["slow_lines"] += 1
                if proc["first"] is None:
                    proc["first"], proc["first_idx"] = where, idx
                proc["last"], proc["last_idx"] = where, idx
                mx = MEMEXPORT.search(line)
                if mx:
                    vals = [int(mx.group(k)) for k in ("pc", "pkb", "sc", "skb", "dc", "dkb")]
                    for key, val in zip(ME_KEYS, vals):
                        me[key] += val
                    me["parsed_lines"] += 1
                    if vals[0] or vals[2] or vals[4]:
                        me["active_lines"] += 1
                        if me["first_active"] is None:
                            me["first_active"] = where
                if fm is None:
                    s["nofield_lines"] += 1
                    proc["nofield_lines"] += 1
                    if proc["first_nofield"] is None:
                        proc["first_nofield"] = where
                    proc["last_nofield"] = where
                    proc["last_is_nofield"] = True
                    continue
                proc["last_is_nofield"] = False
                s["field_lines"] += 1
                proc["field_lines"] += 1
                s["max_t"] = max(s["max_t"], t)
                if t - proc["total"] < f:
                    s["warnings"].append(
                        f"{where}: T rose by {t - proc['total']}, less than this frame's F {f}")
                proc.update(last_counter=where, last_ts=ts, total=t)
                proc["f_sum"] += f
                if f:
                    proc["hit_lines"] += 1
                    proc["max_f"] = max(proc["max_f"], f)
                if t and proc["first_hit"] is None:
                    proc["first_hit"] = {"at": where, "frame": idx, "ts": ts, "f": f, "t": t}
    procs = s["processes"]
    for i, p in enumerate(procs, 1):
        p["unlogged"] = p["total"] - p["f_sum"]
        p["cut"] = p["field_lines"] > 0 and p["nofield_lines"] == 1 and p["last_is_nofield"]
        p["mixed"] = p["field_lines"] > 0 and p["nofield_lines"] > 0 and not p["cut"]
        p["kind"] = "counter" if p["field_lines"] else ("no field" if p["slow_lines"] else "no slow lines")
        a, b = parse_ts(p["last_ts"]), parse_ts(p["end_ts"])
        p["tail_s"] = round((b - a).total_seconds(), 3) if (p["field_lines"] and a and b) else None
        if p["cut"]:
            s["warnings"].append(f"process {i}: its last slow-frame line ({p['last_nofield']}) has no "
                                 "counter field: cut off at exit?")
        if p["mixed"]:
            s["warnings"].append(
                f"process {i}: {p['nofield_lines']} slow-frame lines have no counter field (first "
                f"{p['first_nofield']}, last {p['last_nofield']}) among {p['field_lines']} with it: "
                "logs from two builds?")
        if p["tail_s"] is not None and p["tail_s"] > TAIL_WARN_S:
            s["warnings"].append(
                f"process {i}: the log goes on {p['tail_s']:.1f} s after its last counter line "
                f"({p['last_ts']} to {p['end_ts']}): fallback draws in that time are not in T")
    counted = [p for p in procs if p["field_lines"]]
    if len(procs) > 1:
        s["warnings"].append(
            f"{len(procs)} processes in these logs; T is the sum of the last totals of the "
            f"{len(counted)} with counter lines (max T on any line: {s['max_t']})")
    first = next((p for p in procs if p["slow_lines"]), None)
    if first is not None and first["first_idx"] > LOST_LOG_FIRST_INDEX:
        if first["start"] is None:
            s["notes"].append(f"the first logged frame is #{first['first_idx']} and the process "
                              "start is not in these logs: older rotated logs are gone (or "
                              "slow_frame_log_ms was above 1); T still counts those frames")
        else:
            s["notes"].append(f"the first logged frame is #{first['first_idx']} although the "
                              f"process start is in the log ({first['start']}): slow_frame_log_ms "
                              "was above most frame times; T still counts the frames not logged")
    return s


def verdict(s, missing):
    if missing:
        return "NO DATA", None, "not found: " + ", ".join(missing)
    if not s["files"]:
        return "NO DATA", None, "no log files"
    procs = s["processes"]
    counted = [p for p in procs if p["field_lines"]]
    if not counted:
        if s["slow_lines"] == 0:
            return ("NO DATA", None, "no slow-frame lines: slow_frame_log_ms was not set, or the "
                    "log level hides info lines")
        return ("NO DATA", None, f"{s['slow_lines']} slow-frame lines, none with the counter "
                "field: this build has no s4-p2c")
    total = sum(p["total"] for p in counted)
    if total:
        return ("FAIL", total, "the memexport full-buffer fallback ran; P2 ON waits for Agent 1's "
                "cap decision (b2r S22)")
    parts = []
    for i, p in enumerate(procs, 1):
        if p["kind"] == "no slow lines":
            parts.append(f"process {i} has no slow-frame lines")
        elif p["kind"] == "no field":
            parts.append(f"process {i} has {p['nofield_lines']} slow-frame lines without the field")
        elif p["mixed"]:
            parts.append(f"process {i} mixes lines with and without the field")
    if parts:
        return "PARTIAL", 0, "T = 0 where the counter shows, but " + "; ".join(parts) + ": not a pass"
    return "PASS", 0, "the memexport full-buffer fallback never ran, up to the last logged frame"


def contains(path, needle, chunk=8 << 20):
    keep = len(needle) - 1
    tail = b""
    with open(path, "rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                return False
            buf = tail + block
            if needle in buf:
                return True
            tail = buf[-keep:] if keep else b""


def scan_bin(path):
    if os.path.isdir(path):
        targets = []
        for root, dirs, names in os.walk(path):
            dirs.sort()
            targets += [os.path.join(root, n) for n in sorted(names) if n.lower().endswith((".exe", ".dll"))]
    elif os.path.isfile(path):
        targets = [path]
    else:
        return {"path": path, "error": "not found", "scanned": [], "found_in": []}
    return {"path": path, "error": None, "scanned": targets,
            "found_in": [t for t in targets if contains(t, LITERAL)]}


def report(r, out):
    def w(text=""):
        print(text, file=out)

    w("P2 counter check: memexport full-buffer fallback (s4-p2c field "
      "'memexport full-buffer Fx (total T)')")
    for path in r["missing"]:
        w(f"not found: {path}")
    if r["files"]:
        dirs = {os.path.dirname(p) for p in r["files"]}
        if len(dirs) == 1:
            w(f"logs, oldest first ({len(r['files'])}) in {dirs.pop() or '.'}: "
              + ", ".join(os.path.basename(p) for p in r["files"]))
        else:
            w(f"logs, in this order ({len(r['files'])}): " + ", ".join(r["files"]))
    w(f"lines {r['lines']}; slow-frame lines {r['slow_lines']}: {r['field_lines']} with the counter "
      f"field, {r['nofield_lines']} without")
    if r["first_ts"]:
        w(f"log time range: {r['first_ts']} .. {r['last_ts']}")
    for i, p in enumerate(r["processes"], 1):
        started = f"started {p['start']}" if p["start"] else "start not in these logs"
        if not p["slow_lines"]:
            w(f"process {i} ({started}): no slow-frame lines; its log ends {p['end_ts']}")
            continue
        w(f"process {i} ({started}): frames #{p['first_idx']}..#{p['last_idx']} ({p['first']} .. "
          f"{p['last']}); {p['field_lines']} counter lines, {p['nofield_lines']} without the field")
        if not p["field_lines"]:
            continue
        tail = f", {p['tail_s']:.1f} s later" if p["tail_s"] is not None else ""
        w(f"  last counter line {p['last_counter']} at {p['last_ts']}; its log ends {p['end_ts']}{tail}")
        w(f"  T = {p['total']}: F on logged lines {p['f_sum']}, in frames not logged {p['unlogged']}")
        h = p["first_hit"]
        if h:
            w(f"  first T > 0: {h['at']}, frame #{h['frame']}, {h['ts']}, F {h['f']}, T {h['t']}")
            w(f"  logged frames with F > 0: {p['hit_lines']}, max F {p['max_f']}")
    me = r["memexport"]
    if r["slow_lines"]:
        if not me["parsed_lines"]:
            w("memexport fields: not found on the slow-frame lines")
        elif me["active_lines"]:
            w(f"memexport activity: {me['active_lines']} of {me['parsed_lines']} slow-frame lines "
              f"(first {me['first_active']}): invalidations on memexport pages {me['page_inval']}x "
              f"{me['page_kb']} KB, syncs {me['syncs']} ({me['sync_kb']} KB), on demand "
              f"{me['on_demand']} ({me['on_demand_kb']} KB)")
        else:
            w(f"memexport activity: none on {me['parsed_lines']} slow-frame lines, so a PASS covers "
              "only frames without known-range memexport activity")
    for note in r["notes"]:
        w(f"note: {note}")
    for warn in r["warnings"]:
        w(f"WARN: {warn}")
    b = r["bin"]
    if b is not None:
        if b["error"]:
            w(f"bin: {b['path']}: {b['error']}")
        elif b["found_in"]:
            base = b["path"] if os.path.isdir(b["path"]) else os.path.dirname(b["path"])
            w("bin: the counter's format string is in "
              + ", ".join(os.path.relpath(p, base) for p in b["found_in"]) + " (this build has s4-p2c)")
        else:
            w(f"bin: the counter's format string is in none of the {len(b['scanned'])} .exe/.dll "
              f"files in {b['path']} (no s4-p2c)")
    total = f" (total {r['total']})" if r["total"] is not None else ""
    w(f"RESULT: {r['verdict']}{total}: {r['reason']}")


def check(paths, json_out=None, bin_path=None, out=None):
    out = out or sys.stdout
    files, missing = resolve(paths)
    s = scan(files)
    v, total, reason = verdict(s, missing)
    r = {"tool": "p2c_check.py", "verdict": v, "exit": EXIT[v], "total": total, "reason": reason,
         "missing": missing, "bin": scan_bin(bin_path) if bin_path else None}
    r.update({k: s[k] for k in ("files", "lines", "slow_lines", "field_lines", "nofield_lines",
                                "first_ts", "last_ts", "max_t", "processes", "memexport", "notes",
                                "warnings")})
    report(r, out)
    if json_out:
        with open(json_out, "w", encoding="utf-8") as fh:
            json.dump(r, fh, indent=1)
    return EXIT[v], r


def safe_check(paths, json_out=None, bin_path=None, out=None, _impl=None):
    """check(), but an exception gives RESULT: ERROR and exit 4, so it can't be read as FAIL (1)."""
    out = out or sys.stdout
    try:
        return (_impl or check)(paths, json_out=json_out, bin_path=bin_path, out=out)
    except Exception as exc:  # noqa: BLE001 - any failure must end in a RESULT line
        print(f"RESULT: ERROR: {type(exc).__name__}: {exc}", file=out)
        return EXIT["ERROR"], None


def selftest():
    def body(idx, f=None, t=None, pages=(0, 0), syncs=(0, 0), od=(0, 0), ms=2.6):
        text = REAL_FORMAT.format(idx, ms, 0.0, 0.0, 0, 0.0, 0, 0.0, 0, 0, 0.0, 1, 0, 0, 0, 2, 3848,
                                  pages[0], pages[1], syncs[0], syncs[1], od[0], od[1],
                                  f or 0, t or 0)
        if f is None:  # a build without s4-p2c prints the same line without its last field
            text = text[:text.rindex(" | memexport full-buffer ")]
        return text

    def slow(idx, f=None, t=None, cut=0, **kw):
        text = f"[2026-11-22 17:00:{idx % 60:02d}.000] [info] [gpu] [t34316] " + body(idx, f, t, **kw)
        return text[:-cut] if cut else text

    other = ("[2026-11-22 17:00:00.001] [info] [gpu] [t34316] S4 upload hash: frame 5 calls 2 "
             "ranges 2 pages 961 (3844 KB) first 0 unchanged 959 changed 2 blocks 17 "
             "changed_blocks 2 pages_in_changed_blocks 65 u_page 0.9979 u_block 0.9324")
    start = "[2026-11-22 17:00:00.000] [info] [core] [t21588] Startup: launching the module"
    end = "[2026-11-22 17:00:59.000] [info] [core] [t21588] Title terminated; hard-exiting process."

    def p0(r):
        return r["processes"][0]

    cases = [
        ("PASS; rotated logs are read oldest first",
         {"game.2.log": [slow(2, 0, 0), other], "game.1.log": [slow(3, 0, 0)],
          "game.log": [other, slow(4, 0, 0), slow(5, 0, 0)]}, "PASS", 0,
         lambda r: [os.path.basename(p) for p in r["files"]] == ["game.2.log", "game.1.log",
                                                                 "game.log"]
         and r["field_lines"] == 4 and len(r["processes"]) == 1 and not r["warnings"]),
        ("FAIL; F on logged lines plus frames not logged",
         {"game.log": [slow(2, 0, 0), slow(3, 2, 2), slow(4, 0, 5), slow(5, 1, 6)]}, "FAIL", 6,
         lambda r: p0(r)["f_sum"] == 3 and p0(r)["unlogged"] == 3 and p0(r)["hit_lines"] == 2
         and p0(r)["max_f"] == 2 and p0(r)["first_hit"]["frame"] == 3 and not r["warnings"]),
        ("FAIL; only frames that were not logged",
         {"game.log": [slow(2, 0, 0), slow(9, 0, 4)]}, "FAIL", 4,
         lambda r: p0(r)["f_sum"] == 0 and p0(r)["unlogged"] == 4
         and p0(r)["first_hit"] == {"at": "game.log:2", "frame": 9,
                                    "ts": "2026-11-22 17:00:09.000", "f": 0, "t": 4}),
        ("NO DATA; slow-frame lines without the field (a build without s4-p2c)",
         {"game.log": [start, slow(2), other, slow(3)]}, "NO DATA", None,
         lambda r: "no s4-p2c" in r["reason"] and r["slow_lines"] == 2),
        ("NO DATA; no slow-frame lines",
         {"game.log": [start, other, other]}, "NO DATA", None,
         lambda r: "slow_frame_log_ms" in r["reason"] and r["slow_lines"] == 0),
        ("two processes (the frame index restarts)",
         {"game.log": [slow(2, 0, 0), slow(100, 1, 4), slow(2, 0, 0), slow(3, 0, 0)]}, "FAIL", 4,
         lambda r: len(r["processes"]) == 2 and r["max_t"] == 4
         and any("2 processes" in x for x in r["warnings"])),
        ("T falls with no frame-index restart",
         {"game.log": [slow(2, 0, 3), slow(3, 0, 1)]}, "FAIL", 4,
         lambda r: len(r["processes"]) == 2
         and any("no frame-index restart" in x for x in r["warnings"])),
        ("last line cut off at exit: PASS with a WARN",
         {"game.log": [slow(2, 0, 0), slow(3, 0, 0), slow(4, 0, 0, cut=12)]}, "PASS", 0,
         lambda r: r["nofield_lines"] == 1 and p0(r)["cut"] and not p0(r)["mixed"]
         and any("cut off" in x for x in r["warnings"])),
        ("PARTIAL; lines from two builds in one process",
         {"game.log": [slow(2), slow(3, 0, 0), slow(4, 0, 0)]}, "PARTIAL", 0,
         lambda r: p0(r)["mixed"] and any("two builds" in x for x in r["warnings"])),
        ("memexport activity is summed",
         {"game.log": [slow(2, 0, 0, pages=(3, 12)), slow(3, 0, 0, syncs=(1, 64), od=(2, 8)),
                       slow(4, 0, 0)]}, "PASS", 0,
         lambda r: r["memexport"]["active_lines"] == 2 and r["memexport"]["page_inval"] == 3
         and r["memexport"]["page_kb"] == 12 and r["memexport"]["syncs"] == 1
         and r["memexport"]["sync_kb"] == 64 and r["memexport"]["on_demand"] == 2
         and r["memexport"]["first_active"] == "game.log:1"),
        ("older rotated logs gone (no process start in the logs)",
         {"game.log": [slow(72648, 0, 0), slow(72649, 0, 0)]}, "PASS", 0,
         lambda r: any("older rotated logs" in x for x in r["notes"])),
        ("start in the log but the first logged frame is #120 (threshold above 1)",
         {"game.log": [start, slow(120, 0, 0), slow(121, 0, 0)]}, "PASS", 0,
         lambda r: any("slow_frame_log_ms was above" in x for x in r["notes"])
         and p0(r)["start"] == "game.log:1"),
        ("FAIL; the real format with large values (1234.5 ms, T 123456789)",
         {"game.log": [start, slow(2, 0, 123456786, ms=1234.5, pages=(5, 20), syncs=(2, 8), od=(1, 4)),
                       slow(3, 3, 123456789, ms=45.0)]}, "FAIL", 123456789,
         lambda r: p0(r)["f_sum"] == 3 and p0(r)["unlogged"] == 123456786
         and r["memexport"]["page_inval"] == 5 and r["memexport"]["sync_kb"] == 8
         and r["memexport"]["on_demand_kb"] == 4 and r["max_t"] == 123456789),
        ("PARTIAL; a process without the field beside one with T = 0",
         {"game.log": [start, slow(2), slow(3), end, start, slow(2, 0, 0), slow(3, 0, 0)]},
         "PARTIAL", 0,
         lambda r: [p["kind"] for p in r["processes"]] == ["no field", "counter"]
         and "process 1 has 2 slow-frame lines without the field" in r["reason"]),
        ("PARTIAL; a started process that logged no slow-frame lines",
         {"game.log": [start, other, end, start, slow(2, 0, 0), slow(3, 0, 0)]}, "PARTIAL", 0,
         lambda r: [p["kind"] for p in r["processes"]] == ["no slow lines", "counter"]
         and "process 1 has no slow-frame lines" in r["reason"]),
        ("PASS with a WARN; the log goes on 56 s after the last counter line",
         {"game.log": [start, slow(2, 0, 0), slow(3, 0, 0), end]}, "PASS", 0,
         lambda r: p0(r)["tail_s"] == 56.0 and any("not in T" in x for x in r["warnings"])),
    ]
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        for n, (name, logs, want_v, want_total, extra) in enumerate(cases, 1):
            run_dir = os.path.join(tmp, f"case{n}")
            os.makedirs(run_dir)
            for fname, lines in logs.items():
                with open(os.path.join(run_dir, fname), "w", encoding="utf-8", newline="") as fh:
                    fh.write("".join(x + "\r\n" for x in lines))
            code, r = check([run_dir], out=io.StringIO())
            try:
                ok = (r["verdict"] == want_v and r["total"] == want_total
                      and code == EXIT[want_v] and bool(extra(r)))
            except (IndexError, KeyError, TypeError):
                ok = False
            results.append((ok, f"{name}: {r['verdict']}, total {r['total']}, exit {code}"))
        code, r = check([os.path.join(tmp, "no-such-run")], out=io.StringIO())
        results.append((code == 3 and "not found" in r["reason"],
                        f"missing run dir: {r['verdict']}, exit {code}"))
        given = [os.path.join(tmp, "case1", "game.log"), os.path.join(tmp, "case1", "game.1.log")]
        code, r = check(given, out=io.StringIO())
        results.append((r["files"] == given and len(r["processes"]) == 2,
                        f"explicit files keep the given order: {r['verdict']}, "
                        f"{len(r['processes'])} processes"))
        out_json = os.path.join(tmp, "r.json")
        code, r = check([os.path.join(tmp, "case2")], json_out=out_json, out=io.StringIO())
        with open(out_json, encoding="utf-8") as fh:
            j = json.load(fh)
        results.append((j["verdict"] == "FAIL" and j["total"] == 6 and j["exit"] == 1,
                        f"--json: {j['verdict']}, total {j['total']}"))
        lf_dir = os.path.join(tmp, "lf")
        os.makedirs(lf_dir)
        with open(os.path.join(lf_dir, "game.log"), "w", encoding="utf-8", newline="") as fh:
            fh.write("".join(x + "\n" for x in [start, slow(2, 0, 0), slow(3, 1, 1)]))
        code, r = check([lf_dir], out=io.StringIO())
        results.append((r["verdict"] == "FAIL" and r["total"] == 1 and r["field_lines"] == 2,
                        f"LF-only log: {r['verdict']}, total {r['total']}"))
        bin_dir = os.path.join(tmp, "bin")
        os.makedirs(os.path.join(bin_dir, "sdk"))
        for fname, data in (("game.exe", b"\0" * 10 + LITERAL + b"\0" * 10),
                            ("rexruntime.dll", b"\0" * 64),
                            ("notes.txt", LITERAL),
                            (os.path.join("sdk", "rexsdk.dll"), b"\0" + LITERAL)):
            with open(os.path.join(bin_dir, fname), "wb") as fh:
                fh.write(data)
        exe = os.path.join(bin_dir, "game.exe")
        results.append((contains(exe, LITERAL, chunk=16)
                        and not contains(exe, LITERAL + b"x", chunk=16),
                        "--bin search across a chunk boundary"))
        b = scan_bin(bin_dir)
        results.append(([os.path.basename(p) for p in b["found_in"]] == ["game.exe", "rexsdk.dll"]
                        and len(b["scanned"]) == 3, "--bin scans .exe/.dll files, subfolders too"))
        buf = io.StringIO()
        check([os.path.join(tmp, "case1")], bin_path=bin_dir, out=buf)
        last = buf.getvalue().strip().splitlines()[-1]
        results.append((last == "RESULT: PASS (total 0): the memexport full-buffer fallback never "
                        "ran, up to the last logged frame", "RESULT line format"))

        def boom(*_a, **_k):
            raise OSError(13, "Permission denied")

        buf = io.StringIO()
        code, r = safe_check([tmp], out=buf, _impl=boom)
        results.append((code == 4 and r is None and buf.getvalue().startswith("RESULT: ERROR: "),
                        f"an exception gives RESULT: ERROR, exit {code} (not FAIL's 1)"))
    for ok, text in results:
        print(f"{'ok  ' if ok else 'FAIL'} {text}")
    bad = sum(1 for ok, _ in results if not ok)
    print(f"SELFTEST {'PASS' if not bad else 'FAIL'} ({len(results) - bad}/{len(results)} checks)")
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(
        description="P2 counter check: the memexport full-buffer fallback total (s4-p2c) from a "
                    "run's game.log. Exit 0 PASS (total 0), 1 FAIL, 3 PARTIAL or NO DATA (not a "
                    "pass), 4 ERROR, 2 usage.")
    ap.add_argument("paths", nargs="*", help="run dir(s) or log files, oldest first")
    ap.add_argument("--json", metavar="OUT", help="also write the result as JSON")
    ap.add_argument("--bin", metavar="PATH",
                    help="also check the .exe/.dll files in PATH (and its subfolders) for the "
                         "counter's format string")
    ap.add_argument("--selftest", action="store_true", help="run the built-in tests")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.paths:
        ap.error("give a run dir or log files")
    code, _ = safe_check(a.paths, json_out=a.json, bin_path=a.bin)
    return code


if __name__ == "__main__":
    sys.exit(main())

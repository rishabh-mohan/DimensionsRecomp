#!/usr/bin/env python3
"""W6 gate kit (Agent 12, task #15, 2026-11-22): every W6 gate, G1-G12, on a finished matrix, in one command.

usage: python build/agent12/w6-gates/run_gates.py <matrix out dir> [--status DIR | --window-log FILE]
           [--gate-log FILE | --gate strict|relaxed] [--side DIR ...] [--gate-a DIR] [--ncpu N]
           [--one-bin] [--json OUT] [--expect FIXTURE.json] [--brief] [--force]
       python build/agent12/w6-gates/run_gates.py --selftest
       (run_gates.ps1 next to this file takes the same arguments)

Read-only. It reads the matrix dir (matrix.json, plan.txt, results.csv, runs/*), the bins that matrix.json names,
the launcher's status dir and the side-run dirs, and writes only the --json file. It lowers its own priority to
Below Normal. It stops (exit 4) while perf-notes/WINDOW-HOLD.txt exists, unless --force.
Nothing is W6-specific. The arms, their bins, cvars and env come from matrix.json; the planned arms and run count come
from plan.txt; the runs come from results.csv. A gate whose switch no run arm sets is n/a: G4 needs
shared_memory_single_hold_rearm=true in a run arm, and G5-G7 need physical_protect_keep_watch=true.
The launcher's window log (window-<id>-<HHmm>.log) is found from --status (default: both launcher status dirs
that exist, night bench/agent5/launch/status and day bench/agent5/day/status (N6); the report names the one used)
by (1) an END line whose out dir is this dir, (2) a runner-<tag>.txt naming this dir, or
(3) a START line within 3 min of the dir's YYYYMMDD-HHMM. A match in both dirs at the same strength is ambiguous:
no window log (CHECK); give --status or --window-log. Its END line feeds G3, and its quiet-gate line feeds G12,
unless --gate-log or --gate is given.

Gates (the numbers in W6-GATES.md v2):
  G1  every switch rated      MANUAL: each arm's switches beyond the common set, for the reviewer
  G2  one bin per arm         run.json bin_dir = the arm's bin; the run's MANIFEST.txt and exe/dll copies = the bin's
                              (SHA-256); with --one-bin, FAIL unless the run arms use one bin. P2 bins: p2c_check
                              --bin finds s4-p2c. Side runs and gate A are on a P2 bin (or a matrix bin), their
                              exe_sha256 (or exe copy) is the bin's, and they share one exe_sha256
  G3  runs complete           results rows = the plan.txt estimate; arms and per-arm counts = plan.txt; each run has
                              status OK, exit 0x00000000, wm_close, runner exit 0 and a run.json; launcher END line exit 0
  G4  P2 fallback never runs  p2c_check on each --side and --gate-a dir (PENDING without them); the worst verdict
  G5  C1 verify (gate A)      'C1 verify: on' and 'first kept protect' present, 0 'C1 verify K:'/'F:' lines, and
                              gate A sets physical_protect_keep_watch_verify=true (PENDING without --gate-a)
  G6  keep only under G       CODE: met in code (Agent 10, b2r S21)
  G7  inert on native         CODE: met in code (and any native-blocked lines that were seen)
  G8  nothing stale/new       no stale-protection / write-fault / Protect-failed line anywhere; keep-watch runs and
                              sides are on and keeping; gate_logdiff of every run against the merged reference-arm
                              runs: a FAIL finding is FAIL, NEW warning/error messages are CHECK
  G9  launch-only switches    run.json params.cvar = the arm's cvars; each --k=v is in args, and no other arm's switch
                              is; env_set and toml_set = the arm's
  G10 per-run validity        scored runs valid and not excluded; each switch's proof line (1 ms timer, opt-out,
                              precise wait, keep-watch, verify), and none without the switch; no timing-forbidden
                              switch; free RAM >= min_free_ram_gb; a switch this kit knows no proof line for: CHECK;
                              the slow state (E-cores < 800 MHz for >= 3 samples overlapping the window) as information
  G11 power overlay           w6_env_record: one overlay in every run, no change inside a window; one power scheme,
                              AC and battery-saver value in every run, none changing inside a window
  G12 quiet gate              w6_env_record: STRICT or RELAXED (MsMpEng averages or Defender range), else NOT RECORDED
                              or NO WINDOW; CHECK if the gate line is more than 30 min before the window start or after it
Output: header, per-gate details (not with --brief), one table (gate, status, key number), w6_env_record's RECORD
line, then 'GATES: G1 <status>; ...; exit N'.
Exit: 1 a gate FAILs; 3 nothing FAILs, but a gate is CHECK, PENDING, NO DATA, NOT RECORDED, NO WINDOW, PARTIAL or
ERROR (a kit crash inside one gate is ERROR on that gate; the other gates still run); 0 otherwise (MANUAL, CODE and
n/a don't count); 2 usage, or no matrix.json/results.csv; 4 WINDOW-HOLD.txt exists; 6 the kit itself failed outside
the gates (it prints the traceback and 'GATES: ERROR; exit 6': never exit 1). With --expect: 0 when every expectation
in the fixture holds, else 5.
"""
import sys

sys.dont_write_bytecode = True  # read-only kit: no __pycache__ next to other agents' modules

import argparse  # noqa: E402
import csv  # noqa: E402
import glob  # noqa: E402
import hashlib  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import statistics  # noqa: E402
import tempfile  # noqa: E402
import traceback  # noqa: E402
from collections import Counter, OrderedDict  # noqa: E402
from datetime import datetime  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
for _p in (os.path.join(REPO, "bench", "agent8", "run"), os.path.join(REPO, "build", "agent12", "p2c-check"), HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gate_logdiff  # noqa: E402  (Agent 8's B-gate log diff; used read-only)
import p2c_check  # noqa: E402
import w6_env_record as envrec  # noqa: E402

HOLD = os.path.join(REPO, "perf-notes", "WINDOW-HOLD.txt")
STATUS_DIR = os.path.join(REPO, "bench", "agent5", "launch", "status")
DAY_STATUS_DIR = os.path.join(REPO, "bench", "agent5", "day", "status")  # N6: day windows log here
STATUS_DIRS = (STATUS_DIR, DAY_STATUS_DIR)
STATUS_RANK = ["FAIL", "ERROR", "CHECK", "PARTIAL", "NO DATA", "NO WINDOW", "NOT RECORDED", "PENDING",
               "MANUAL", "CODE", "PASS", "n/a"]
SOFT = {"ERROR", "CHECK", "PARTIAL", "NO DATA", "NO WINDOW", "NOT RECORDED", "PENDING"}
GATE_NAMES = {"G1": "every switch rated", "G2": "one bin per arm, as built", "G3": "every planned run completed",
              "G4": "P2's fallback never runs", "G5": "C1 verify on gate A", "G6": "keep only under G",
              "G7": "inert on native", "G8": "nothing stale, no new errors", "G9": "launch-only switches as planned",
              "G10": "per-run validity", "G11": "power overlay", "G12": "quiet gate"}
P2_SWITCH = "shared_memory_single_hold_rearm"
LOCK_SWITCH = "physical_protect_hold_global_lock"
KW_SWITCH = "physical_protect_keep_watch"
VERIFY_SWITCH = "physical_protect_keep_watch_verify"
LINES = OrderedDict([
    ("timer1ms", "Host timer resolution set to 1 ms"),
    ("optout", "Host timer resolution set to 1 ms (background opt-out on)"),
    ("precise", "TimerQueue: precise wait (timer_queue_precise_wait)"),
    ("kw_on", "C1 keep-watch: on (with physical_protect_hold_global_lock)"),
    ("kw_nolock", "C1 keep-watch: on, but physical_protect_hold_global_lock is off"),
    ("kw_native", "C1 keep-watch: on, but blocked for this process (native renderer)"),
    ("kw_first", "C1 keep-watch: first kept protect at"),
    ("verify_on", "C1 verify: on"),
    ("verify_k", "C1 verify K:"),
    ("verify_f", "C1 verify F:"),
])
BAD_LINES = ("Recovered stale physical page protection", "Unhandled guest physical write fault",
             "PhysicalHeap::Protect failed")
NO_LINE = {"framerate_limit", P2_SWITCH, LOCK_SWITCH, "precise_guest_sleep", "wait_timeout_round_up", "cs_spin",
           "spinlock_pause_spin", "clock_lockfree", "tls_bounds_fix"}  # no log line: the recorded list (G9) is the proof
PROOF_SWITCHES = {"host_timer_resolution_ms", "host_timer_throttling_optout", "timer_queue_precise_wait", KW_SWITCH,
                  VERIFY_SWITCH}
FORBIDDEN = {"shared_memory_upload_hash_log", "slow_frame_log_ms"}  # side runs only
KNOWN = NO_LINE | PROOF_SWITCHES | FORBIDDEN
SLOW_MHZ, SLOW_MIN = 800.0, 3  # the slow state: E-cores below 800 MHz for >= 3 samples overlapping the window
P2C_STATUS = {"PASS": "PASS", "FAIL": "FAIL", "PARTIAL": "PARTIAL", "NO DATA": "NO DATA", "ERROR": "ERROR"}
END_RE = re.compile(r"window (?P<id>\S+) END: runner exit (?P<code>-?\w+) \((?P<meaning>.*?)\) after "
                    r"(?P<min>[\d.]+) min; out dir (?P<dir>.+?)(?:; SUSPECT: (?P<suspect>.*?))?\s*$")
START_RE = re.compile(r"^(?P<date>\d{4}-\d\d-\d\d) (?P<time>\d\d:\d\d:\d\d) (?P<dry>\[dry\] )?window (?P<id>\S+) START\b")
RUNNER_OUT = re.compile(r"^\s*out dir:\s*(?P<dir>.+?)\s*$")
DIR_STAMP = re.compile(r"(?P<d>\d{8})-(?P<hh>\d\d)(?P<mm>\d\d)(?:-\d+)?$")
PLAN_ARM = re.compile(r"^\s+(?P<id>[^\s:]+): bin (?P<bin>[^;]+);(?P<rest>.*)$")


class UsageError(Exception):
    pass


def lower_priority():
    if os.name != "nt":
        return
    try:
        import ctypes
        k = ctypes.windll.kernel32
        k.GetCurrentProcess.restype = ctypes.c_void_p
        k.SetPriorityClass.argtypes = (ctypes.c_void_p, ctypes.c_uint32)
        k.SetPriorityClass(k.GetCurrentProcess(), 0x00004000)  # BELOW_NORMAL_PRIORITY_CLASS
    except Exception:  # noqa: BLE001 - best effort
        pass


def read_json(path):
    try:
        with open(path, encoding="utf-8-sig") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def read_lines(path):
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as fh:
            return fh.read().splitlines()
    except OSError:
        return []


def norm_path(p, base=REPO):
    if not p:
        return ""
    p = str(p).strip().strip('"')
    if not os.path.isabs(p):
        p = os.path.join(base, p)
    return os.path.normcase(os.path.normpath(p))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def is_true(v):
    return str(v).strip().lower() in ("true", "1", "yes", "on")


def kv_norm(x):
    """A 'k=v' list or a {k: v} dict -> {k (lower case, no leading dashes): v (true/false lower case)}."""
    items = []
    if isinstance(x, dict):
        items = list(x.items())
    elif isinstance(x, (list, tuple)):
        for s in x:
            k, _, v = str(s).partition("=")
            items.append((k, v))
    out = OrderedDict()
    for k, v in items:
        k = str(k).strip().lstrip("-").lower()
        v = "" if v is None else str(v).strip()
        if v.lower() in ("true", "false"):
            v = v.lower()
        if k:
            out[k] = v
    return out


def env_norm(x):
    return OrderedDict((k.upper(), v) for k, v in kv_norm(x).items())


def fmt_kv(d):
    return ", ".join(f"{k}={v}" for k, v in d.items()) or "-"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest().upper()


def cnt_text(c):
    if not c:
        return "-"
    if len(c) == 1:
        return str(next(iter(c)))
    return ", ".join(f"{k} x{v}" for k, v in c.most_common())


def rng(vals):
    return f"{min(vals):.2f}-{max(vals):.2f}" if vals else "-"


def overall_exit(statuses):
    if "FAIL" in statuses:
        return 1
    if any(s in SOFT for s in statuses):
        return 3
    return 0


def parse_plan(path):
    p = {"found": False, "estimate": None, "estimate_cold": None, "arms": OrderedDict(), "cold": [], "rounds": 0,
         "sys_csv": None}
    lines = read_lines(path)
    if not lines:
        return p
    p["found"] = True
    in_arms, loose = False, None
    for line in lines:
        if line.strip() == "arms:":
            in_arms = True
            continue
        if line and not line[0].isspace():
            in_arms = False
        if in_arms:
            m = PLAN_ARM.match(line)
            if m:
                r = re.search(r"(?:^|;)\s*x(\d+)\s*(?:;|$)", m.group("rest"))
                p["arms"][m.group("id")] = {"bin": m.group("bin").strip(), "repeats": int(r.group(1)) if r else None}
            continue
        m = re.match(r"^cold\s+(?P<id>\S+) \(", line)
        if m:
            p["cold"].append(m.group("id"))
            continue
        m = re.match(r"^estimate (\d+) runs \((\d+) cold\)", line)
        if m:
            p["estimate"], p["estimate_cold"] = int(m.group(1)), int(m.group(2))
            continue
        m = re.match(r"^estimate\s+(\d+) runs\b", line)
        if m and loose is None:
            loose = int(m.group(1))
            continue
        if re.match(r"^round \d+\s", line):
            p["rounds"] += 1
        elif line.startswith("sys.csv"):
            p["sys_csv"] = (line.split()[1:2] or [""])[0].rstrip(":").lower() == "on"  # 'sys.csv    on: drivers\...'
    if p["estimate"] is None and loose is not None:
        p["estimate"] = loose
    return p


def end_lines(path):
    return [m for m in (END_RE.search(line) for line in read_lines(path)) if m]


def find_window_log(status_dir, mdir):
    """The launcher's window log for this out dir: (path, how) or (None, why)."""
    if not status_dir:
        return None, "no status dir"
    if not os.path.isdir(status_dir):
        return None, f"no status dir {status_dir}"
    want = norm_path(mdir)
    logs = sorted(glob.glob(os.path.join(status_dir, "window-*.log")))
    for p in logs:
        if any(norm_path(m.group("dir")) == want for m in end_lines(p)):
            return p, "its END line names this out dir"
    for p in sorted(glob.glob(os.path.join(status_dir, "runner-*.txt"))):
        for line in read_lines(p):
            m = RUNNER_OUT.match(line)
            if m and norm_path(m.group("dir")) == want:
                tag = os.path.basename(p)[len("runner-"):-len(".txt")]
                wl = os.path.join(status_dir, f"window-{tag}.log")
                if os.path.isfile(wl):
                    return wl, f"{os.path.basename(p)} names this out dir"
    m = DIR_STAMP.search(os.path.basename(os.path.normpath(mdir)))
    if m:
        t0 = datetime.strptime(m.group("d") + m.group("hh") + m.group("mm"), "%Y%m%d%H%M")
        best = None
        for p in logs:
            for line in read_lines(p):
                s = START_RE.match(line)
                if s and not s.group("dry"):
                    ts = datetime.strptime(f"{s.group('date')} {s.group('time')}", "%Y-%m-%d %H:%M:%S")
                    gap = (t0 - ts).total_seconds()
                    if -60 <= gap <= 180 and (best is None or abs(gap) < best[0]):
                        best = (abs(gap), p, s.group("time"))
        if best:
            return best[1], f"its START line at {best[2]} is {best[0]:.0f} s from the out dir's time"
    return None, f"no window log in {status_dir} names this out dir"


def find_window_log_any(status_dirs, mdir):
    """N6: find_window_log over several status dirs (night and day). A match by END line or runner file beats a
    START-time match; two dirs matching at the same strength is ambiguous, so no window log (the gate says CHECK)."""
    dirs = [d for d in status_dirs if d and os.path.isdir(d)]
    if not dirs:
        return None, "no status dir (" + ", ".join(os.path.relpath(d, REPO) for d in status_dirs) + " don't exist)"
    hits, misses = [], []
    for d in dirs:
        p, how = find_window_log(d, mdir)
        (hits if p else misses).append((p, how, d))
    strong = [h for h in hits if "START line" not in h[1]]
    pick = strong or hits
    if len(pick) == 1:
        p, how, d = pick[0]
        return p, f"{how}; found in {os.path.relpath(d, REPO)}"
    if len(pick) > 1:
        return None, "ambiguous: " + "; ".join(f"{os.path.relpath(p, REPO)} ({how})" for p, how, _ in pick) + \
            " (give --status or --window-log)"
    return None, "no window log names this out dir in " + ", ".join(os.path.relpath(d, REPO) for d in dirs)


def count_lines(path):
    """Proof-line counts and bad lines in the rotated game*.log set of a run dir."""
    c = OrderedDict((k, 0) for k in LINES)
    bad = Counter()
    files = gate_logdiff.log_files(path) if path and os.path.isdir(path) else []
    for fp in files:
        with open(fp, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if "Host timer" in line or "TimerQueue" in line or "C1 " in line:
                    for k, needle in LINES.items():
                        if needle in line:
                            c[k] += 1
                if "hysical" in line:
                    for b in BAD_LINES:
                        if b in line:
                            bad[b] += 1
    return c, bad, len(files)


def empty_scan(path):
    return dict(input=os.path.abspath(path) if path else "", files=[], lines=0, levels=Counter(),
                boot_lines_found=False, fail=Counter(), fail_examples={}, unimpl=0, unimpl_examples=[], reloc=0,
                poolcopy_callers=Counter(), slot_registered=0, slot_extended=0, warn=Counter(), warn_example={},
                critical=0, critical_examples=[])


def merge_scans(scans, label):
    """The reference arm's runs as one gate_logdiff 'A' side: max counts, union of the message kinds."""
    a = empty_scan("")
    a["input"] = label
    with_files = [s for s in scans if s["files"]]
    a["boot_lines_found"] = bool(with_files) and all(s["boot_lines_found"] for s in with_files)
    for s in scans:
        a["lines"] += s["lines"]
        a["levels"].update(s["levels"])
        a["fail"].update(s["fail"])
        for k, v in s["fail_examples"].items():
            a["fail_examples"].setdefault(k, v)
        if s["unimpl"] > a["unimpl"]:
            a["unimpl"], a["unimpl_examples"] = s["unimpl"], list(s["unimpl_examples"])
        a["reloc"] = max(a["reloc"], s["reloc"])
        a["poolcopy_callers"] |= s["poolcopy_callers"]
        a["slot_registered"] = max(a["slot_registered"], s["slot_registered"])
        a["slot_extended"] = max(a["slot_extended"], s["slot_extended"])
        a["critical"] += s["critical"]
        a["critical_examples"] += s["critical_examples"][:max(0, 3 - len(a["critical_examples"]))]
        for k, v in s["warn"].items():
            a["warn"][k] = max(a["warn"][k], v)
            a["warn_example"].setdefault(k, s["warn_example"].get(k, ""))
    a["files"] = with_files[0]["files"][:1] if with_files else []  # one entry: no false 'rotated' note
    return a


def proof_check(cv, c):
    """One run's log-line proof, from its arm's cvars and its line counts: a list of problems."""
    p = []
    if cv.get("host_timer_resolution_ms") == "1":
        if c["timer1ms"] < 1:
            p.append("no 'Host timer resolution set to 1 ms' line (host_timer_resolution_ms=1)")
        elif is_true(cv.get("host_timer_throttling_optout")) and c["optout"] < 1:
            p.append("the 1 ms line lacks '(background opt-out on)' (host_timer_throttling_optout=true)")
    elif c["timer1ms"]:
        p.append(f"{c['timer1ms']} 'Host timer resolution set to 1 ms' line(s) without host_timer_resolution_ms=1")
    if is_true(cv.get("timer_queue_precise_wait")):
        if c["precise"] != 1:
            p.append(f"{c['precise']} 'TimerQueue: precise wait' lines (want exactly 1)")
    elif c["precise"]:
        p.append(f"{c['precise']} 'TimerQueue: precise wait' line(s) without timer_queue_precise_wait=true")
    if is_true(cv.get(KW_SWITCH)):
        if c["kw_on"] < 1:
            p.append(f"no '{LINES['kw_on']}' line")
        if c["kw_first"] < 1:
            p.append(f"no '{LINES['kw_first']}' line")
        for k in ("kw_nolock", "kw_native"):
            if c[k]:
                p.append(f"{c[k]} '{LINES[k]}' line(s)")
    else:
        for k in ("kw_on", "kw_nolock", "kw_native", "kw_first"):
            if c[k]:
                p.append(f"{c[k]} '{LINES[k]}' line(s) without {KW_SWITCH}=true")
    if is_true(cv.get(VERIFY_SWITCH)):
        if c["verify_on"] < 1:
            p.append(f"no 'C1 verify: on' line ({VERIFY_SWITCH}=true)")
    elif c["verify_on"]:
        p.append(f"{c['verify_on']} 'C1 verify: on' line(s) without {VERIFY_SWITCH}=true")
    for k in ("verify_k", "verify_f"):
        if c[k]:
            p.append(f"{c[k]} '{LINES[k]}' line(s) (a page changed since its upload)")
    return p


def forbidden(cv):
    p = []
    if is_true(cv.get("shared_memory_upload_hash_log")):
        p.append("shared_memory_upload_hash_log=true is for side runs only (it changes timing)")
    v = cv.get("slow_frame_log_ms")
    if v not in (None, "", "0"):
        p.append(f"slow_frame_log_ms={v} is for side runs only (it changes timing)")
    return p


def slow_state(rd):
    """E-core slow state over a run's window, from sys.csv and sys.json; None without them."""
    sj = read_json(os.path.join(rd, "sys.json")) if rd else None
    path = os.path.join(rd, "sys.csv") if rd else ""
    if not isinstance(sj, dict) or not os.path.isfile(path):
        return None
    ws, we = num(sj.get("window_start_epoch")), num(sj.get("window_end_epoch"))
    if ws is None or we is None:
        return None
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            t = num(row.get("epoch_s"))
            if t is not None:
                rows.append((t, num(row.get("e_eff_mhz"))))
    rows.sort(key=lambda r: r[0])
    in_win = [e for t, e in rows if ws <= t <= we]
    slow_in = sum(1 for e in in_win if e is not None and e < SLOW_MHZ)
    longest, cur = 0, []
    for t, e in rows + [(None, None)]:
        if e is not None and e < SLOW_MHZ:
            cur.append(t)
            continue
        if cur and cur[0] <= we and cur[-1] >= ws:
            longest = max(longest, len(cur))
        cur = []
    return {"rows": len(in_win), "slow": slow_in, "longest": longest, "stretch": longest >= SLOW_MIN}


class Gate:
    def __init__(self, gid, name):
        self.id, self.name, self.status, self.key, self.details = gid, name, "PASS", "", []

    def worse(self, status):
        if STATUS_RANK.index(status) < STATUS_RANK.index(self.status):
            self.status = status

    def d(self, text):
        self.details.append(text)

    def as_dict(self):
        return {"id": self.id, "name": self.name, "status": self.status, "key": self.key, "details": self.details}


class Kit:
    def __init__(self, a):
        self.a = a
        self.mdir = os.path.abspath(a.matrix_dir)
        mj = read_json(os.path.join(self.mdir, "matrix.json"))
        if not isinstance(mj, dict) or not isinstance(mj.get("arms"), list):
            raise UsageError(f"no readable matrix.json with arms in {self.mdir}")
        rpath = os.path.join(self.mdir, "results.csv")
        if not os.path.isfile(rpath):
            raise UsageError(f"no results.csv in {self.mdir}")
        with open(rpath, encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
        if not rows:
            raise UsageError(f"results.csv in {self.mdir} has no runs")
        self.mj = mj
        self.arms = OrderedDict()
        for x in mj["arms"]:
            if isinstance(x, dict) and x.get("id"):
                self.arms[str(x["id"])] = {"id": str(x["id"]), "bin": x.get("bin") or "", "bin_abs": norm_path(x.get("bin")),
                                           "cvars": kv_norm(x.get("cvars")), "env": env_norm(x.get("env")),
                                           "toml": kv_norm(x.get("toml")), "ref": bool(x.get("ref")), "known": True}
        self.ref = mj.get("reference") or next((i for i, x in self.arms.items() if x["ref"]), None)
        self.plan = parse_plan(os.path.join(self.mdir, "plan.txt"))
        self.unimpl_re = re.compile(gate_logdiff.UNIMPL_DEFAULT)
        self.runs = []
        for row in rows:
            rd = (row.get("run_dir") or "").strip()
            if rd and not os.path.isdir(rd):
                alt = os.path.join(self.mdir, "runs", os.path.basename(rd.replace("\\", "/").rstrip("/")))
                rd = alt if os.path.isdir(alt) else rd
            isdir = bool(rd) and os.path.isdir(rd)
            rj = read_json(os.path.join(rd, "run.json")) if isdir else None
            arm = row.get("arm") or ""
            if arm not in self.arms:
                self.arms[arm] = {"id": arm, "bin": "", "bin_abs": "", "cvars": OrderedDict(), "env": OrderedDict(),
                                  "toml": OrderedDict(), "ref": False, "known": False}
            scored = row.get("scored") == "True"
            try:
                seq = int(row.get("seq") or 0)
            except ValueError:
                seq = 0
            counts, bad, nlogs = count_lines(rd if isdir else "")
            self.runs.append({
                "seq": seq, "arm": arm, "rep": row.get("rep") or "", "scored": scored, "row": row,
                "label": f"#{seq} {arm} " + (f"r{row.get('rep')}" if scored else "cold"),
                "run_dir": rd if isdir else "", "run_json": rj if isinstance(rj, dict) else None,
                "counts": counts, "bad": bad, "nlogs": nlogs,
                "scan": gate_logdiff.scan(rd, self.unimpl_re) if isdir else empty_scan(rd),
                "slow": slow_state(rd) if isdir else None})
        seen = {r["arm"] for r in self.runs}
        self.run_arms = [i for i in self.arms if i in seen]
        sets = [set(self.arms[i]["cvars"].items()) for i in self.run_arms]
        common = set.intersection(*sets) if sets else set()
        if len(self.run_arms) == 1:
            common = {kv for kv in common if kv[0] == "framerate_limit"}
        self.common = OrderedDict(sorted(common))
        self.p2_arms = [i for i in self.run_arms if is_true(self.arms[i]["cvars"].get(P2_SWITCH))]
        self.kw_arms = [i for i in self.run_arms if is_true(self.arms[i]["cvars"].get(KW_SWITCH))]
        self.sides = [self.load_side(p, os.path.basename(os.path.normpath(p))) for p in (a.side or [])]
        self.gate_a = self.load_side(a.gate_a, "gate A (" + os.path.basename(os.path.normpath(a.gate_a)) + ")") \
            if a.gate_a else None
        self.bins = {}
        if a.window_log:
            self.window_log, self.window_how = a.window_log, "given with --window-log"
        else:
            if a.status:
                self.window_log, self.window_how = find_window_log(a.status, self.mdir)
            else:  # N6: night and day launcher folders
                self.window_log, self.window_how = find_window_log_any(STATUS_DIRS, self.mdir)
        self.window_end, self.window_end_other = None, []
        if self.window_log:
            for m in end_lines(self.window_log):
                if norm_path(m.group("dir")) == norm_path(self.mdir):
                    self.window_end = m
                else:
                    self.window_end_other.append(m)
        if a.gate:
            self.gate_log, self.gate_how = None, f"--gate {a.gate} (by hand)"
        elif a.gate_log:
            self.gate_log, self.gate_how = a.gate_log, "given with --gate-log"
        elif self.window_log:
            self.gate_log, self.gate_how = self.window_log, "the launcher's window log"
        else:
            self.gate_log, self.gate_how = None, "none (give --gate-log, --status, --window-log or --gate)"

    def load_side(self, path, label):
        d = path if os.path.isdir(path) else os.path.dirname(os.path.abspath(path))
        rj = read_json(os.path.join(d, "run.json"))
        rj = rj if isinstance(rj, dict) else None
        counts, bad, nlogs = count_lines(d if os.path.isdir(d) else "")
        rjd = rj or {}
        cv = rjd.get("cvars") or (rjd.get("params") or {}).get("cvar")  # the harness's run.json, or the runner's
        return {"label": label, "dir": d, "run_json": rj, "cvars": kv_norm(cv),
                "env": env_norm(rjd.get("env") or rjd.get("env_set")), "counts": counts, "bad": bad, "nlogs": nlogs,
                "scan": gate_logdiff.scan(d, self.unimpl_re) if os.path.isdir(d) else empty_scan(d)}

    def bin_info(self, babs, disp):
        if babs in self.bins:
            return self.bins[babs]
        info = {"display": disp, "exists": bool(babs) and os.path.isdir(babs), "manifest": None,
                "files": OrderedDict(), "exe_sha": None, "sha": {}, "abs": babs}
        if info["exists"]:
            man = os.path.join(babs, "MANIFEST.txt")
            if os.path.isfile(man):
                info["manifest"] = sha256(man)
            for n in sorted(os.listdir(babs)):
                p = os.path.join(babs, n)
                if os.path.isfile(p) and n.lower().endswith((".exe", ".dll")):
                    info["files"][n] = os.path.getsize(p)
        self.bins[babs] = info
        return info

    @staticmethod
    def bin_sha(b, n):
        """SHA-256 of file n in bin b, hashed once per run of the kit."""
        if n not in b["sha"]:
            b["sha"][n] = sha256(os.path.join(b["abs"], n))
        return b["sha"][n]

    # ---------------------------------------------------------------- gates
    def g1(self):
        g = Gate("G1", "every switch rated")
        g.status = "MANUAL"
        parts = []
        for i in self.run_arms:
            x = self.arms[i]
            extra = OrderedDict((k, v) for k, v in x["cvars"].items() if self.common.get(k) != v)
            parts.append(f"{i} {len(extra)}" + (f"+{len(x['env'])} env" if x["env"] else "")
                         + (f"+{len(x['toml'])} toml" if x["toml"] else ""))
            g.d(f"{i}{' (ref)' if i == self.ref else ''}: bin {x['bin'] or '?'}; beyond the common set: {fmt_kv(extra)}"
                + (f"; env {fmt_kv(x['env'])}" if x["env"] else "") + (f"; toml {fmt_kv(x['toml'])}" if x["toml"] else ""))
        unknown = sorted({k for i in self.run_arms for k in self.arms[i]["cvars"]} - KNOWN)
        if unknown:
            g.d("switches this kit has no rule for (rate them by hand; G10 knows no log line for them): "
                + ", ".join(unknown))
        g.d("rate every switch above against W6-GATES.md G1 (Agent 10's b2r ratings): the kit only lists them")
        g.key = (f"{len(self.run_arms)} arms; switches beyond the common set ({fmt_kv(self.common)}): "
                 + ", ".join(parts))
        return g

    def g2(self):
        g = Gate("G2", "one bin per arm, as built")
        ok = 0
        for r in self.runs:
            x = self.arms[r["arm"]]
            probs = []
            if not x["known"]:
                probs.append("arm not in matrix.json")
            else:
                b = self.bin_info(x["bin_abs"], x["bin"])
                rj = r["run_json"]
                if rj is None:
                    probs.append("no run.json")
                elif norm_path(rj.get("bin_dir")) != x["bin_abs"]:
                    probs.append(f"run.json bin_dir {rj.get('bin_dir')} is not the arm's bin {x['bin']}")
                man = os.path.join(r["run_dir"], "MANIFEST.txt") if r["run_dir"] else ""
                if not b["exists"]:
                    probs.append(f"bin {x['bin']} not found")
                elif b["manifest"] is None:
                    probs.append(f"bin {x['bin']} has no MANIFEST.txt")
                elif not man or not os.path.isfile(man):
                    probs.append("no MANIFEST.txt copy in the run dir")
                elif sha256(man) != b["manifest"]:
                    probs.append("the run's MANIFEST.txt differs from the bin's")
                for n, size in b["files"].items():
                    p = os.path.join(r["run_dir"], n) if r["run_dir"] else ""
                    if not p or not os.path.isfile(p):
                        probs.append(f"no {n} copy")
                    elif os.path.getsize(p) != size:
                        probs.append(f"{n} {os.path.getsize(p)} B, the bin's {size} B")
                    elif sha256(p) != self.bin_sha(b, n):
                        probs.append(f"{n} differs from the bin's (same size, other SHA-256)")
            if probs:
                g.worse("FAIL")
                g.d(f"{r['label']}: " + "; ".join(probs))
            else:
                ok += 1
        used = OrderedDict()
        for i in self.run_arms:
            if self.arms[i]["known"]:
                used.setdefault(self.arms[i]["bin_abs"], []).append(i)
        for babs, ids in used.items():
            b = self.bin_info(babs, self.arms[ids[0]]["bin"])
            g.d(f"bin {b['display']}: arms {', '.join(ids)}; MANIFEST.txt sha256 "
                f"{(b['manifest'] or '-')[:16]}; " + (", ".join(f"{n} {s} B" for n, s in b["files"].items()) or "no exe/dll")
                + "".join(f"; {n} sha256 {self.bin_sha(b, n)[:16]}" for n in b["files"] if n.lower().endswith(".exe")))
        key = f"{ok}/{len(self.runs)} runs on their arm's bin (MANIFEST + exe/dll SHA-256); {len(used)} bin" \
              + ("s" if len(used) != 1 else "")
        if getattr(self.a, "one_bin", False):
            if len(used) > 1:
                g.worse("FAIL")
                g.d(f"--one-bin: the run arms use {len(used)} bins, not one")
            key += "; one bin required (--one-bin)"
        if self.p2_arms:
            p2bins = OrderedDict((self.arms[i]["bin_abs"], self.arms[i]["bin"]) for i in self.p2_arms)
            found = 0
            for babs, disp in p2bins.items():
                target = babs if os.path.isdir(babs) else next(
                    (r["run_dir"] for r in self.runs if r["run_dir"] and self.arms[r["arm"]]["bin_abs"] == babs), None)
                sb = p2c_check.scan_bin(target) if target else {"error": "not found", "found_in": [], "scanned": []}
                if sb["found_in"]:
                    found += 1
                    g.d(f"p2c_check --bin {disp}: the counter's format string is in "
                        + ", ".join(os.path.basename(p) for p in sb["found_in"]) + " (this build has s4-p2c)")
                else:
                    g.worse("FAIL")
                    g.d(f"p2c_check --bin {disp}: " + (sb.get("error") or f"the format string is in none of the "
                                                       f"{len(sb['scanned'])} .exe/.dll files") + " (no s4-p2c)")
            key += f"; s4-p2c in {found}/{len(p2bins)} P2 bin" + ("s" if len(p2bins) != 1 else "")
        sides = self.sides + ([self.gate_a] if self.gate_a else [])
        if sides:
            pick = self.p2_arms or self.kw_arms or self.run_arms
            allowed = OrderedDict((self.arms[i]["bin_abs"], self.arms[i]["bin"]) for i in pick if self.arms[i]["known"])
            what = "P2" if self.p2_arms else ("keep-watch" if self.kw_arms else "matrix")
            shas, sok = OrderedDict(), 0
            for s in sides:
                probs = []
                rj = s["run_json"]
                if rj is None:
                    probs.append("no run.json")
                else:
                    bd = norm_path(rj.get("bin_dir"))
                    if bd not in allowed:
                        probs.append(f"bin_dir {rj.get('bin_dir')} is not a {what} arm's bin "
                                     f"({', '.join(allowed.values())})")
                    else:
                        b = self.bin_info(bd, allowed[bd])
                        man = os.path.join(s["dir"], "MANIFEST.txt")
                        if os.path.isfile(man) and b["manifest"] and sha256(man) != b["manifest"]:
                            probs.append("its MANIFEST.txt copy differs from the bin's")
                        exe = next((n for n in b["files"] if n.lower().endswith(".exe")), None)
                        if exe and rj.get("exe_sha256"):
                            if b["exe_sha"] is None:
                                b["exe_sha"] = sha256(os.path.join(bd, exe))
                            if str(rj["exe_sha256"]).upper() != b["exe_sha"]:
                                probs.append(f"exe_sha256 {str(rj['exe_sha256'])[:16]} is not the bin's "
                                             f"{exe} {b['exe_sha'][:16]}")
                        elif exe and os.path.isfile(os.path.join(s["dir"], exe)):
                            if sha256(os.path.join(s["dir"], exe)) != self.bin_sha(b, exe):
                                probs.append(f"its {exe} copy is not the bin's (SHA-256)")
                        elif exe:
                            g.d(f"side {s['label']}: no exe_sha256 in run.json and no {exe} copy: bin_dir and "
                                f"MANIFEST only")
                    if rj.get("exe_sha256"):
                        shas[s["label"]] = str(rj["exe_sha256"]).upper()
                if probs:
                    g.worse("FAIL")
                    g.d(f"side {s['label']}: " + "; ".join(probs))
                else:
                    sok += 1
            if len(set(shas.values())) > 1:
                g.worse("FAIL")
                g.d("side runs differ in exe_sha256: " + ", ".join(f"{k} {v[:16]}" for k, v in shas.items()))
            key += f"; side runs {sok}/{len(sides)} on the {what} bin"
        g.key = key
        return g

    def g3(self):
        g = Gate("G3", "every planned run completed")
        p, n = self.plan, len(self.runs)
        if not p["found"]:
            g.worse("CHECK")
            g.d("no plan.txt: the planned run count and arms are unknown")
        elif p["estimate"] is None:
            g.worse("CHECK")
            g.d("plan.txt has no 'estimate N runs (C cold)' line")
        elif n != p["estimate"]:
            g.worse("FAIL")
            g.d(f"results.csv has {n} runs; plan.txt estimate {p['estimate']}")
        planned = list(p["arms"])
        if planned:
            missing = [i for i in planned if i not in self.run_arms]
            extra = [i for i in self.run_arms if i not in planned]
            if missing or extra:
                g.worse("FAIL")
                g.d(f"arms planned but not run: {', '.join(missing) or '-'}; run but not planned: {', '.join(extra) or '-'}")
            for i in planned:
                want_s, want_c = p["arms"][i]["repeats"], p["cold"].count(i)
                got_s = sum(1 for r in self.runs if r["arm"] == i and r["scored"])
                got_c = sum(1 for r in self.runs if r["arm"] == i and not r["scored"])
                if (want_s is not None and got_s != want_s) or got_c != want_c:
                    g.worse("FAIL")
                    g.d(f"arm {i}: {got_s} scored + {got_c} cold runs; plan.txt x{want_s} + {want_c} cold")
        elif p["found"]:
            g.worse("CHECK")
            g.d("plan.txt lists no arms")
        if planned:
            def per_arm(i, s, c):
                return f"{i} x{s}" + (f"+{c} cold" if c else "")
            g.d("plan.txt: " + ", ".join(per_arm(i, p["arms"][i]["repeats"], p["cold"].count(i)) for i in planned)
                + "; results.csv: " + ", ".join(per_arm(i, sum(1 for r in self.runs if r["arm"] == i and r["scored"]),
                                                        sum(1 for r in self.runs if r["arm"] == i and not r["scored"]))
                                                for i in self.run_arms))
        ok = 0
        for r in self.runs:
            row, probs = r["row"], []
            if row.get("status") != "OK":
                probs.append(f"status {row.get('status')}")
            if (row.get("exit_code") or "").lower() != "0x00000000":
                probs.append(f"exit {row.get('exit_code') or '?'}")
            if not (row.get("close") or "").startswith("wm_close"):
                probs.append(f"close '{row.get('close') or ''}'")
            if (row.get("runner_exit") or "") != "0":
                probs.append(f"runner exit {row.get('runner_exit') or '?'}")
            if r["run_json"] is None:
                probs.append("no run.json")
            if probs:
                g.worse("FAIL")
                g.d(f"{r['label']}: " + "; ".join(probs))
            else:
                ok += 1
        key = (f"{ok}/{n} runs OK, exit 0x00000000, wm_close, runner exit 0; plan.txt "
               + (f"{p['estimate']} runs" if p["estimate"] is not None else "no estimate")
               + (f" ({p['estimate_cold']} cold)" if p["estimate_cold"] is not None else "")
               + f"; arms {len([i for i in planned if i in self.run_arms])}/{len(planned)} as planned")
        m = self.window_end
        if self.window_log and m:
            txt = f"launcher END: runner exit {m.group('code')} ({m.group('meaning')}) after {m.group('min')} min"
            if m.group("code") != "0" or m.group("suspect"):
                g.worse("FAIL")
                txt += f"; SUSPECT: {m.group('suspect')}" if m.group("suspect") else ""
            g.d(f"{txt} ({self.window_log})")
            key += f"; launcher END exit {m.group('code')}" + ("; SUSPECT" if m.group("suspect") else "")
        elif self.window_log:
            g.worse("CHECK")
            other = "; ".join(f"END for {x.group('dir')}" for x in self.window_end_other) or "no END line"
            g.d(f"launcher log {self.window_log}: no END line for this out dir ({other}): still running, or cut off?")
            key += "; launcher END missing"
        else:
            g.d(f"launcher window log: none ({self.window_how})")
            key += "; no launcher log"
        g.key = key
        return g

    def g4(self):
        g = Gate("G4", "P2's fallback never runs")
        if not self.p2_arms:
            g.status, g.key = "n/a", f"no run arm sets {P2_SWITCH}=true"
            return g
        targets = self.sides + ([self.gate_a] if self.gate_a else [])
        if not targets:
            g.status = "PENDING"
            g.key = "no side runs given (--side, --gate-a): p2c_check runs on side 1, side 2 and gate A"
            return g
        res = []
        for s in targets:
            buf = io.StringIO()
            _, r = p2c_check.safe_check([s["dir"]], out=buf)
            v = r["verdict"] if r else "ERROR"
            nw = sum(1 for line in buf.getvalue().splitlines() if line.startswith("WARN:"))
            res.append(f"{s['label']} {v}" + (f" T={r['total']}" if r and r.get("total") is not None else "")
                       + (f" ({nw} WARN)" if nw else ""))
            g.worse(P2C_STATUS.get(v, "ERROR"))
            for line in buf.getvalue().splitlines():
                if line.startswith(("RESULT:", "WARN:", "memexport", "log time range", "note:")):
                    g.d(f"{s['label']}: {line}")
        npass = sum(1 for x in res if " PASS" in x)
        g.key = f"PASS in {npass}/{len(res)}: " + ", ".join(res)
        return g

    def g5(self):
        g = Gate("G5", "C1 verify on gate A")
        if not self.kw_arms:
            g.status, g.key = "n/a", f"no run arm sets {KW_SWITCH}=true"
            return g
        if not self.gate_a:
            g.status, g.key = "PENDING", "no gate A run given (--gate-a)"
            return g
        c, cv = self.gate_a["counts"], self.gate_a["cvars"]
        probs = []
        if c["verify_on"] < 1:
            probs.append("no 'C1 verify: on' line")
        if c["kw_first"] < 1:
            probs.append(f"no '{LINES['kw_first']}' line")
        if c["verify_k"] or c["verify_f"]:
            probs.append(f"{c['verify_k']} 'C1 verify K:' and {c['verify_f']} 'C1 verify F:' lines")
        if not is_true(cv.get(VERIFY_SWITCH)):
            probs.append(f"its run.json cvars don't set {VERIFY_SWITCH}=true")
        if self.gate_a["nlogs"] == 0:
            probs.append("no game*.log")
        for x in probs:
            g.d(f"{self.gate_a['label']}: {x}")
        if probs:
            g.worse("FAIL")
        g.key = (f"{self.gate_a['label']}: verify on {c['verify_on']}, first kept {c['kw_first']}, "
                 f"K {c['verify_k']}, F {c['verify_f']}; {VERIFY_SWITCH}={cv.get(VERIFY_SWITCH, 'unset')}")
        return g

    def g6(self):
        g = Gate("G6", "keep only under G")
        if not self.kw_arms:
            g.status, g.key = "n/a", f"no run arm sets {KW_SWITCH}=true"
        else:
            g.status, g.key = "CODE", "met in code: the keep path requires owns_lock() (Agent 10, b2r S21)"
        return g

    def g7(self):
        g = Gate("G7", "inert on native")
        if not self.kw_arms:
            g.status, g.key = "n/a", f"no run arm sets {KW_SWITCH}=true"
            return g
        g.status = "CODE"
        seen = [r["label"] for r in self.runs if r["counts"]["kw_native"]]
        seen += [s["label"] for s in self.sides + ([self.gate_a] if self.gate_a else []) if s["counts"]["kw_native"]]
        if seen:
            g.d("native-blocked line seen in: " + ", ".join(seen))
        g.key = f"met in code (Agent 10, b2r S21); native-blocked lines in {len(seen)} runs"
        return g

    def g8(self):
        g = Gate("G8", "nothing stale, no new errors")
        sides = self.sides + ([self.gate_a] if self.gate_a else [])
        nbad = 0
        for r in self.runs + sides:
            if r["bad"]:
                nbad += 1
                g.worse("FAIL")
                g.d(f"{r['label']}: " + ", ".join(f"{v}x '{k}'" for k, v in r["bad"].items()))
        kw_items = [(r["label"], r["counts"]) for r in self.runs if r["arm"] in self.kw_arms]
        kw_items += [(s["label"], s["counts"]) for s in sides if is_true(s["cvars"].get(KW_SWITCH))]
        kw_ok = 0
        for label, c in kw_items:
            probs = []
            if c["kw_on"] < 1:
                probs.append(f"no '{LINES['kw_on']}'")
            if c["kw_first"] < 1:
                probs.append(f"no '{LINES['kw_first']}'")
            if c["kw_nolock"]:
                probs.append(f"{c['kw_nolock']}x '{LINES['kw_nolock']}'")
            if probs:
                g.worse("FAIL")
                g.d(f"keep-watch {label}: " + "; ".join(probs))
            else:
                kw_ok += 1
        ref_runs = [r for r in self.runs if r["arm"] == self.ref]
        find_runs, new_runs, kinds, examples = 0, 0, Counter(), {}
        if not ref_runs:
            g.worse("CHECK")
            g.d(f"no runs of the reference arm '{self.ref}': logdiff skipped")
        else:
            A = merge_scans([r["scan"] for r in ref_runs], f"{self.ref} x{len(ref_runs)}")
            g.d(f"logdiff reference: {self.ref} x{len(ref_runs)} merged ({A['lines']} log lines, {len(A['warn'])} "
                f"warning/error kinds); {sum(1 for r in self.runs if r['scan']['files'])}/{len(self.runs)} runs have "
                f"a game*.log to compare")
            for r in self.runs:
                findings, notes, _, diff = gate_logdiff.compare(A, r["scan"], 10)
                if findings:
                    find_runs += 1
                    g.worse("FAIL")
                    for f in findings:
                        g.d(f"logdiff {r['label']}: FAIL {f}")
                if diff["new_in_b_total"]:
                    new_runs += 1
                    for x in diff["new_in_b"]:
                        kinds[x["msg"]] += 1
                        examples.setdefault(x["msg"], x["example"])
                    if diff["new_in_b_total"] > len(diff["new_in_b"]):
                        kinds[f"(+{diff['new_in_b_total'] - len(diff['new_in_b'])} more kinds in {r['label']})"] += 1
            if kinds:
                g.worse("CHECK")
                for msg, cnt in kinds.most_common():
                    g.d(f"logdiff NEW vs {self.ref} in {cnt} run(s): {msg[:200]}"
                        + (f" | e.g. {examples[msg][:160]}" if msg in examples else ""))
        for s in sides:
            sc = s["scan"]
            fails = {k: v for k, v in sc["fail"].items() if v}
            if fails or sc["critical"] or not sc["files"]:
                g.worse("FAIL")
                g.d(f"side {s['label']}: " + (", ".join(f"{v}x '{k}'" for k, v in fails.items()) or "")
                    + (f" {sc['critical']} [critical] lines" if sc["critical"] else "")
                    + ("" if sc["files"] else "no game*.log"))
        g.d("by hand: the frame hash or screenshot matches the reference arm at the same point (W6-GATES G8)")
        key = f"stale/fault/Protect-failed lines in {nbad}/{len(self.runs) + len(sides)} runs"
        if kw_items:
            key += f"; keep-watch on+keeping {kw_ok}/{len(kw_items)}"
        if ref_runs:
            key += (f"; logdiff vs {self.ref} (x{len(ref_runs)}): FAIL findings in {find_runs}, NEW messages in "
                    f"{new_runs}/{len(self.runs)} runs ({len(kinds)} kinds)")
        if sides:
            key += f"; sides {len(sides)} checked for fail patterns"
        g.key = key
        return g

    def g9(self):
        g = Gate("G9", "launch-only switches as planned")
        keys = set()
        for i in self.run_arms:
            keys |= set(self.arms[i]["cvars"])
        ok = 0
        for r in self.runs:
            x, rj, probs = self.arms[r["arm"]], r["run_json"], []
            if rj is None:
                probs.append("no run.json")
            else:
                got = kv_norm((rj.get("params") or {}).get("cvar"))
                if dict(got) != dict(x["cvars"]):
                    probs.append(f"params.cvar {fmt_kv(got)} is not the arm's {fmt_kv(x['cvars'])}")
                args = [str(y).strip().lower() for y in (rj.get("args") or [])]
                for k, v in x["cvars"].items():
                    if f"--{k}={v}".lower() not in args:
                        probs.append(f"--{k}={v} not in args")
                for k in sorted(keys - set(x["cvars"])):
                    if any(y.startswith(f"--{k}=") for y in args):
                        probs.append(f"args set --{k}, which the arm doesn't")
                env = env_norm(rj.get("env_set"))
                if dict(env) != dict(x["env"]):
                    probs.append(f"env_set {fmt_kv(env)} is not the arm's {fmt_kv(x['env'])}")
                toml = kv_norm(rj.get("toml_set"))
                if dict(toml) != dict(x["toml"]):
                    probs.append(f"toml_set {fmt_kv(toml)} is not the arm's {fmt_kv(x['toml'])}")
            if probs:
                g.worse("FAIL")
                g.d(f"{r['label']}: " + "; ".join(probs))
            else:
                ok += 1
        g.d("hands off, no dev console during the window: procedural (C1 v3 latches keep_watch and "
            "hold_global_lock at init; other cvars are read live)")
        g.key = f"{ok}/{len(self.runs)} runs: params.cvar, args, env_set and toml_set = the arm's"
        return g

    def g10(self):
        g = Gate("G10", "per-run validity")
        scored = [r for r in self.runs if r["scored"]]
        valid = proof_ok = ram_ok = 0
        slow_n = slow_known = 0
        need_vals = set()
        unknown_all = set()
        for r in self.runs:
            x, row, rj = self.arms[r["arm"]], r["row"], r["run_json"] or {}
            if r["scored"]:
                why = []
                if row.get("valid_timing") != "True":
                    vw = rj.get("valid_timing_why")
                    vw = "; ".join(str(y) for y in vw) if isinstance(vw, list) else (vw or row.get("notes") or "")
                    why.append(f"not valid timing ({vw})" if vw else "not valid timing")
                if row.get("excluded") == "True":
                    why.append("excluded")
                if row.get("flags_excluding"):
                    why.append(f"flags_excluding {row['flags_excluding']}")
                if row.get("light_phase") == "True":
                    why.append("light_phase")
                if why:
                    g.worse("FAIL")
                    g.d(f"{r['label']}: " + "; ".join(why)
                        + (f" [flags_info {row.get('flags_info')}]" if row.get("flags_info") else ""))
                else:
                    valid += 1
            probs = proof_check(x["cvars"], r["counts"]) + forbidden(x["cvars"])
            if r["nlogs"] == 0:
                probs.append("no game*.log")
            if probs:
                g.worse("FAIL")
                g.d(f"{r['label']}: " + "; ".join(probs))
            else:
                proof_ok += 1
            free = num(rj.get("free_ram_gb_at_start"))
            need = num((rj.get("params") or {}).get("min_free_ram_gb")) or 6.0
            need_vals.add(need)
            if free is None:
                g.worse("CHECK")
                g.d(f"{r['label']}: no free_ram_gb_at_start in run.json")
            elif free < need:
                g.worse("FAIL")
                g.d(f"{r['label']}: free RAM {free:.2f} GB at start < {need:g} GB")
            else:
                ram_ok += 1
            if r["scored"] and r["slow"] is not None:
                slow_known += 1
                slow_n += 1 if r["slow"]["stretch"] else 0
        for i in self.run_arms:
            x = self.arms[i]
            runs = [r for r in self.runs if r["arm"] == i]
            shown = [k for k in LINES if any(r["counts"][k] for r in runs)]
            g.d(f"proof lines {i}: " + (", ".join(f"{k} " + ",".join(str(r['counts'][k]) for r in runs) for k in shown)
                                        or "none") + f" ({len(runs)} runs)")
            nl = [k for k in x["cvars"] if k in NO_LINE and k != "framerate_limit"]
            if nl:
                g.d(f"  {i}: no log line for {', '.join(nl)}: the recorded cvar list (G9) is the proof")
            if x["env"]:
                g.d(f"  {i}: env {fmt_kv(x['env'])}: run.json env_set (G9) is the proof")
            unknown = [k for k in x["cvars"] if k not in KNOWN]
            if unknown:
                unknown_all.update(unknown)
                g.worse("CHECK")
                g.d(f"  {i}: no proof line known for {', '.join(unknown)}: check by hand")
        slow = [f"{r['label']} {r['slow']['slow']}/{r['slow']['rows']} (longest {r['slow']['longest']})"
                for r in scored if r["slow"] and r["slow"]["slow"]]
        g.d(f"slow state (info; E-cores < {SLOW_MHZ:.0f} MHz for >= {SLOW_MIN} samples overlapping the window): "
            f"{slow_n}/{slow_known} scored runs; slow samples in the window: " + ("; ".join(slow) or "none"))
        need_txt = "/".join(f"{v:g}" for v in sorted(need_vals)) or "6"
        g.key = (f"{valid}/{len(scored)} scored runs valid; proof lines ok in {proof_ok}/{len(self.runs)} runs; "
                 f"free RAM >= {need_txt} GB in {ram_ok}/{len(self.runs)}; slow state {slow_n}/{slow_known} "
                 f"scored (info)"
                 + (f"; no proof line known for {len(unknown_all)} switch(es): {', '.join(sorted(unknown_all))}, "
                    f"check by hand" if unknown_all else ""))
        return g

    def g11_g12(self):
        g11, g12 = Gate("G11", "power overlay"), Gate("G12", "quiet gate")
        buf = io.StringIO()
        try:
            _, res = envrec.record(self.mdir, gate_log=self.gate_log, gate=self.a.gate, ncpu=self.a.ncpu, out=buf)
        except Exception as exc:  # noqa: BLE001 - any failure must show as ERROR, not as a pass
            res = None
            buf.write(f"w6_env_record failed: {type(exc).__name__}: {exc}\n")
        text = buf.getvalue().splitlines()
        self.record_line = next((x for x in reversed(text) if x.startswith("RECORD:")), None)
        self.env_text = text
        if res is None:
            for gg in (g11, g12):
                gg.status, gg.key = "ERROR", "w6_env_record gave no result"
                gg.details += text[-3:]
            return g11, g12
        for line in text:
            if line.startswith(("power overlay:", "note:", "scheme:", "WARN:")):
                g11.d(line)
            elif line.startswith(("quiet gate:", "non-game load")):
                g12.d(line)
        if self.window_log:  # run-night.ps1 (21:13) logs the scheme once at window start, and warns on no sys_csv
            for line in read_lines(self.window_log):
                if "power scheme at the start:" in line or "sys_csv" in line:
                    g11.d("launcher: " + line.strip())
        runs = res["runs"]
        have = [x for x in runs if isinstance(x["overlay"], dict)]
        missing = [x for x in runs if x["sys_src"] is None or not isinstance(x["overlay"], dict)]
        ov = Counter(envrec.tri(x["overlay"]) for x in have)
        if have and not res["overlay_uniform"]:
            g11.worse("FAIL")
        elif missing:
            g11.worse("NO DATA")
        if self.mj.get("sys_csv") is not True:
            g11.d("matrix.json doesn't set \"sys_csv\": true, so the runs have no sys.csv/sys.json")
            if not have:
                g11.worse("NO DATA")
        for name, fld in (("scheme", "scheme"), ("AC", "ac"), ("battery saver", "saver")):
            vals = Counter(envrec.tri(x[fld]) for x in have if isinstance(x.get(fld), dict))
            moved = [f"#{x['seq']} {x['arm']}" for x in have if envrec.changed(x.get(fld))]
            if len(vals) > 1 or moved:
                g11.worse("FAIL")
                g11.d(f"{name} is not one value in every run: {cnt_text(vals)}"
                      + (f"; changed inside the window in {', '.join(moved)}" if moved else ""))
        g11.key = (f"overlay {cnt_text(ov)} in {len(have)}/{len(runs)} runs"
                   + (", no change inside any window" if res["overlay_uniform"] else ", MIXED or changed")
                   + f"; scheme {cnt_text(Counter(envrec.tri(x['scheme']) for x in have))}"
                   + f"; AC {cnt_text(Counter(envrec.tri(x['ac']) for x in have))}"
                   + f"; saver {cnt_text(Counter(envrec.tri(x['saver']) for x in have))}")
        gt = res["gate"]
        scored = res["nongame_scored"]
        ng = (f"non-game load {rng(scored)} cores (median {statistics.median(scored):.2f}), "
              f"{len(res['nongame_flagged'])} flagged" if scored else "non-game load -")
        if gt is None:
            g12.status, g12.key = "NOT RECORDED", f"no gate log ({self.gate_how}); {ng}"
            return g11, g12
        if gt["manual"]:
            g12.key = f"{gt['mode'].upper()} (set by hand with --gate); {ng}"
            return g11, g12
        src = os.path.basename(gt["source"] or "")
        if gt["mode"] is None:
            g12.status = "NOT RECORDED"
            g12.key = f"no quiet-gate line in {src} ({gt['how'] or 'no QUIET / NOT QUIET / quiet gate line'}); {ng}"
            return g11, g12
        mode = gt["mode"].upper()
        how = gt["how"] if gt["how"] and len(gt["how"]) < 40 else ""
        parts = [f"{mode}" + (f" ({how})" if how else "") + (f" at {gt['end']}" if gt["end"] else "") + f" [{src}]"]
        if gt["procs"]:
            parts.append(", ".join(f"{k} " + "/".join("?" if v is None else f"{v:.2f}" for v in vals)
                                   for k, vals in gt["procs"].items()))
        elif gt["samples"]:
            d = [s["defender"] for s in gt["samples"]]
            parts.append(f"Defender {rng(d)} cores over {len(d)} one-min samples")
        parts.append(ng)
        if gt["mode"] in envrec.NO_WINDOW:
            g12.status = "NO WINDOW"
            parts.append("the launcher started no window after this gate")
        gtext = res.get("gate_text") or ""
        if "WARN: more than 30 min" in gtext:
            g12.worse("CHECK")
            parts.append("the gate line is > 30 min before the window: the right gate log?")
        elif "WARN: the gate line is after the window start" in gtext:
            g12.worse("CHECK")
            parts.append("the gate line is after the window start: the right gate log?")
        g12.key = "; ".join(parts)
        return g11, g12

    # ---------------------------------------------------------------- run + report
    def run(self, out):
        self.record_line, self.env_text = None, []
        gates = []
        for fn, ids in ((self.g1, ["G1"]), (self.g2, ["G2"]), (self.g3, ["G3"]), (self.g4, ["G4"]), (self.g5, ["G5"]),
                        (self.g6, ["G6"]), (self.g7, ["G7"]), (self.g8, ["G8"]), (self.g9, ["G9"]), (self.g10, ["G10"]),
                        (self.g11_g12, ["G11", "G12"])):
            try:
                got = fn()
                gates += list(got) if isinstance(got, tuple) else [got]
            except Exception as exc:  # noqa: BLE001 - a kit bug shows as ERROR on that gate; the others still run
                tb = traceback.format_exc().strip().splitlines()
                for gid in ids:
                    g = Gate(gid, GATE_NAMES[gid])
                    g.status = "ERROR"
                    g.key = f"the kit failed in this gate: {type(exc).__name__}: {exc} (send the output to Agent 12)"
                    g.details += tb[-4:]
                    gates.append(g)
        self.gates = gates
        self.exit = overall_exit([g.status for g in gates])
        self.report(out)
        return self.exit

    def report(self, out):
        def w(text=""):
            print(text, file=out)

        p = self.plan
        w(f"=== W6 gate kit (run_gates.py): {self.mdir} ===")
        w(f"matrix   {self.mj.get('title') or '-'}")
        w(f"ref      {self.ref or '-'}; sys_csv {str(self.mj.get('sys_csv')).lower()}; plan.txt "
          + (f"{p['estimate']} runs ({p['estimate_cold']} cold)" if p["estimate"] is not None else "has no estimate"))
        parts = []
        for i in self.run_arms:
            s = sum(1 for r in self.runs if r["arm"] == i and r["scored"])
            c = sum(1 for r in self.runs if r["arm"] == i and not r["scored"])
            parts.append(f"{i} x{s}" + (f" (+{c} cold)" if c else ""))
        notrun = [i for i, x in self.arms.items() if x["known"] and i not in self.run_arms]
        w(f"arms run {', '.join(parts)} ({len(self.runs)} runs)"
          + (f"; in matrix.json but not run: {', '.join(notrun)}" if notrun else ""))
        bins = OrderedDict()
        for i in self.run_arms:
            bins.setdefault(self.arms[i]["bin"] or "?", []).append(i)
        w("bins     " + "; ".join(f"{b}: {', '.join(ids)}" for b, ids in bins.items()))
        w(f"switches P2 ({P2_SWITCH}=true): {', '.join(self.p2_arms) or 'none'}; keep-watch ({KW_SWITCH}=true): "
          f"{', '.join(self.kw_arms) or 'none'}")
        w(f"launcher window log: {self.window_log or 'none'} ({self.window_how})")
        w(f"quiet-gate source: {self.gate_log or '-'} ({self.gate_how})")
        sides = self.sides + ([self.gate_a] if self.gate_a else [])
        if sides:
            w("side runs: " + "; ".join(f"{s['label']} = {s['dir']}" for s in sides))
        if not self.a.brief:
            for g in self.gates:
                w("")
                w(f"--- {g.id} {g.name}: {g.status} ---")
                for d in g.details:
                    w(f"  {d}")
        w("")
        w("| gate | status | key number |")
        w("|---|---|---|")
        for g in self.gates:
            w(f"| {g.id} {g.name} | {g.status} | {g.key.replace('|', '/')} |")
        w("")
        w(self.record_line or "RECORD: (w6_env_record.py gave no RECORD line)")
        w("GATES: " + "; ".join(f"{g.id} {g.status}" for g in self.gates) + f"; exit {self.exit}")

    def as_dict(self):
        return {
            "tool": "run_gates.py", "matrix_dir": self.mdir, "title": self.mj.get("title"), "reference": self.ref,
            "plan": {k: v for k, v in self.plan.items() if k != "arms"}, "plan_arms": self.plan["arms"],
            "run_arms": self.run_arms, "p2_arms": self.p2_arms, "kw_arms": self.kw_arms,
            "window_log": self.window_log, "window_how": self.window_how, "gate_log": self.gate_log,
            "gate_how": self.gate_how, "gates": [g.as_dict() for g in self.gates], "record": self.record_line,
            "exit": self.exit,
            "runs": [{"seq": r["seq"], "arm": r["arm"], "rep": r["rep"], "scored": r["scored"],
                      "run_dir": r["run_dir"], "logs": r["nlogs"], "counts": r["counts"], "bad": dict(r["bad"]),
                      "slow": r["slow"]} for r in self.runs],
            "sides": [{"label": s["label"], "dir": s["dir"], "counts": s["counts"], "bad": dict(s["bad"]),
                       "cvars": s["cvars"]} for s in self.sides + ([self.gate_a] if self.gate_a else [])],
        }


def check_expect(path, kit, out):
    fx = read_json(path)
    if not isinstance(fx, dict):
        print(f"EXPECT: MISMATCH (fixture {path} unreadable)", file=out)
        return 5
    by_id = {g.id: g for g in kit.gates}
    checks = []
    if "exit" in fx:
        checks.append((fx["exit"] == kit.exit, f"exit {kit.exit} (want {fx['exit']})"))
    for gid, want in (fx.get("gates") or {}).items():
        g = by_id.get(gid)
        if g is None:
            checks.append((False, f"{gid}: no such gate"))
            continue
        if "status" in want:
            checks.append((g.status == want["status"], f"{gid} status {g.status} (want {want['status']})"))
        for sub in want.get("key", []):
            checks.append((sub in g.key, f"{gid} key has '{sub}'"))
        for sub in want.get("details", []):
            checks.append((any(sub in d for d in g.details), f"{gid} details have '{sub}'"))
        for sub in want.get("not_details", []):
            checks.append((not any(sub in d for d in g.details), f"{gid} details lack '{sub}'"))
    if "record" in fx:
        checks.append((kit.record_line == fx["record"], f"RECORD line = '{fx['record']}'"))
    bad = [t for okk, t in checks if not okk]
    for t in bad:
        print(f"EXPECT FAIL: {t}", file=out)
    print(f"EXPECT: {'OK' if not bad else 'MISMATCH'} ({len(checks) - len(bad)}/{len(checks)} checks; "
          f"{os.path.basename(path)})", file=out)
    return 0 if not bad else 5


def selftest_w6(ok):
    """End to end on a synthetic W6-like matrix: P2 and keep-watch arms, side 1, gate A and a launcher window log."""
    def write(path, lines, mode="w"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, mode, encoding="utf-8", newline="") as fh:
            fh.write("".join(x + "\r\n" for x in lines))

    def slow(i, f=0, t=0):
        return (f"[2026-11-23 05:00:{i:02d}.000] [info] [gpu] [t3] " + p2c_check.REAL_FORMAT.format(
            i, 2.6, 0.0, 0.0, 0, 0.0, 0, 0.0, 0, 0, 0.0, 1, 0, 0, 0, 2, 3848, 0, 0, 0, 0, 0, 0, f, t))

    def info(ts, msg, lvl="info"):
        return f"[2026-11-23 {ts}.000] [{lvl}] [core] [t1] {msg}"

    with tempfile.TemporaryDirectory() as tmp:
        b = os.path.join(tmp, "bin")
        write(os.path.join(b, "MANIFEST.txt"), ["S4b test bin"])
        with open(os.path.join(b, "legodimensions.exe"), "wb") as fh:
            fh.write(b"MZ exe " * 100)
        with open(os.path.join(b, "rexgpu-xenos.dll"), "wb") as fh:
            fh.write(b"MZ dll " + p2c_check.LITERAL + b" end")
        base = ["framerate_limit=0"]
        p2 = base + [f"{P2_SWITCH}=true"]
        p2f = p2 + [f"{LOCK_SWITCH}=true"]
        p2fc = p2f + [f"{KW_SWITCH}=true", f"{VERIFY_SWITCH}=false"]
        arms = OrderedDict([("s0", base), ("p2", p2), ("p2f", p2f), ("p2fc", p2fc)])
        md = os.path.join(tmp, "matrix", "20261123-0650")
        os.makedirs(md)
        with open(os.path.join(md, "matrix.json"), "w", encoding="utf-8") as fh:
            json.dump({"title": "W6 test", "reference": "s0", "sys_csv": True, "arms": [
                {"id": i, "ref": i == "s0", "bin": b, "cvars": cv, "env": {}} for i, cv in arms.items()]}, fh)
        write(os.path.join(md, "plan.txt"), ["=== timing matrix: W6 test ===", "arms:"]
              + [f"       {i}: bin {b}; frames perf; x3; warm-up 55 s" for i in arms]
              + [f"cold     s0 ({b}): unscored, before round 1", "round 1  s0 p2 p2f p2fc", "round 2  p2 p2f p2fc s0",
                 "round 3  p2f p2fc s0 p2", "estimate 13 runs (1 cold), about 33 min"])
        rows = []
        for seq, (arm, rep) in enumerate([("s0", "0")] + [(i, str(r)) for r in (1, 2, 3) for i in arms], 1):
            rd = os.path.join(md, "runs", f"0650{seq:02d}-{arm}-r{rep}")
            os.makedirs(rd)
            for n in ("MANIFEST.txt", "legodimensions.exe", "rexgpu-xenos.dll"):
                shutil.copyfile(os.path.join(b, n), os.path.join(rd, n))
            with open(os.path.join(rd, "run.json"), "w", encoding="utf-8") as fh:
                json.dump({"bin_dir": b, "params": {"cvar": arms[arm], "min_free_ram_gb": 6},
                           "args": ["--frames", "perf"] + [f"--{x}" for x in arms[arm]], "env_set": {}, "toml_set": {},
                           "free_ram_gb_at_start": 12.5}, fh)
            log = [info("06:51:00", "GPU route: d3d12 (test)"), info("06:51:01", "test warning 5", "warning")]
            if arm == "p2fc":
                log += [info("06:51:02", LINES["kw_on"] + "."), info("06:51:09", LINES["kw_first"] + " 0x1000.")]
            write(os.path.join(rd, "game.log"), log)
            rows.append({"seq": seq, "round": rep, "arm": arm, "rep": rep, "scored": rep != "0", "status": "OK",
                         "valid_timing": True, "exit_code": "0x00000000", "close": "wm_close", "runner_exit": 0,
                         "excluded": False, "flags_excluding": "", "flags_info": "", "light_phase": False,
                         "cpu_cores_mean": 2.0, "run_dir": rd, "notes": ""})
        with open(os.path.join(md, "results.csv"), "w", encoding="utf-8", newline="") as fh:
            wr = csv.DictWriter(fh, fieldnames=list(rows[0]))
            wr.writeheader()
            wr.writerows(rows)
        exe_sha = sha256(os.path.join(b, "legodimensions.exe")).lower()

        def side(name, cv, extra):
            d = os.path.join(tmp, "sides", name)
            write(os.path.join(d, "game.log"), [info("05:00:00", "Startup: launching the module"),
                                                info("05:00:00", "GPU route: d3d12 (test)")] + extra
                  + [slow(i) for i in range(2, 8)])
            with open(os.path.join(d, "run.json"), "w", encoding="utf-8") as fh:
                json.dump({"bin_dir": b, "exe_sha256": exe_sha, "cvars": dict(x.split("=", 1) for x in cv)}, fh)
            return d
        s1 = side("side1", p2f + ["shared_memory_upload_hash_log=true", "slow_frame_log_ms=1"], [])
        ga = side("gateA", p2f + [f"{KW_SWITCH}=true", f"{VERIFY_SWITCH}=true", "slow_frame_log_ms=1"],
                  [info("05:00:01", LINES["kw_on"] + "."), info("05:00:01", LINES["verify_on"] + "."),
                   info("05:00:01", LINES["kw_first"] + " 0x1000.")])
        sd = os.path.join(tmp, "status")
        write(os.path.join(sd, "window-W6-0650.log"), [  # run-night.ps1's order: gate (L633), scheme (L711), START
            "06:49:30 quiet gate: STRICT (MsMpEng 0.02/0.02/0.02, OfficeClickToRun 0.00/0.00/0.00, "
            "CrossDeviceService 0.01/0.01/0.01)",
            "2026-11-23 06:50:00 power scheme at the start: Power Scheme GUID: 381b4222 (Balanced)",
            "2026-11-23 06:50:01 window W6 START (estimate 41 min, about 07:31): test",
            f"2026-11-23 07:31:02 window W6 END: runner exit 0 (matrix done) after 41 min; out dir {md}"])
        ns = argparse.Namespace(matrix_dir=md, status=sd, window_log=None, gate_log=None, gate=None, side=[s1],
                                gate_a=ga, ncpu=12, brief=True)
        kit = Kit(ns)
        code = kit.run(io.StringIO())
        st, key = {g.id: g.status for g in kit.gates}, {g.id: g.key for g in kit.gates}
        want = {"G1": "MANUAL", "G2": "PASS", "G3": "PASS", "G4": "PASS", "G5": "PASS", "G6": "CODE", "G7": "CODE",
                "G8": "PASS", "G9": "PASS", "G10": "PASS", "G11": "NO DATA", "G12": "PASS"}
        bad = {k: st.get(k) for k in want if st.get(k) != want[k]}
        ok(not bad, "W6-like matrix: every gate's status" + (f" (wrong: {bad})" if bad else ""))
        ok("s4-p2c in 1/1 P2 bin" in key["G2"] and "side runs 2/2 on the P2 bin" in key["G2"],
           "W6-like: G2 finds s4-p2c in the P2 bin; side 1 and gate A on it")
        ok("13/13 runs OK" in key["G3"] and "arms 4/4" in key["G3"] and "launcher END exit 0" in key["G3"],
           "W6-like: G3 with the launcher's END line")
        ok(key["G4"].startswith("PASS in 2/2"), "W6-like: G4 p2c_check PASS on side 1 and gate A")
        ok("keep-watch on+keeping 4/4" in key["G8"] and "NEW messages in 0/13" in key["G8"],
           "W6-like: G8 keep-watch on 3 p2fc runs + gate A; logdiff NEW 0")
        ok(key["G12"].startswith("STRICT") and "MsMpEng 0.02/0.02/0.02" in key["G12"],
           "W6-like: G12 STRICT with the MsMpEng averages, from the window log")
        ok(code == 3, "W6-like: exit 3 (G11 has no sys data)")
        ok(any("power scheme at the start: Power Scheme GUID: 381b4222 (Balanced)" in d
               for d in next(g for g in kit.gates if g.id == "G11").details), "W6-like: G11 quotes the launcher's scheme line")
        write(os.path.join(rows[4]["run_dir"], "game.log"),
              [info("06:52:00", "Recovered stale physical page protection at 0x2000", "warning")], "a")
        write(os.path.join(ga, "game.log"), [info("05:00:07", "C1 verify K: page 0x3000 changed since its upload",
                                                  "warning")], "a")
        write(os.path.join(s1, "game.log"), [info("05:00:00", "Startup: launching the module")]
              + [slow(i, 1 if i == 5 else 0, 1 if i >= 5 else 0) for i in range(2, 8)])
        kit = Kit(ns)
        code = kit.run(io.StringIO())
        st = {g.id: g.status for g in kit.gates}
        ok(st["G4"] == "FAIL" and st["G5"] == "FAIL" and st["G8"] == "FAIL" and st["G10"] == "PASS" and code == 1,
           "W6-like with faults (fallback on side 1, verify K: on gate A, a stale line): G4, G5, G8 FAIL, exit 1")
        # a kit fault must never look like a gate result (checker a8f50f28, findings 1-4)
        kit = Kit(ns)
        kit.g9 = lambda: 1 // 0
        code = kit.run(io.StringIO())
        st, key = {g.id: g.status for g in kit.gates}, {g.id: g.key for g in kit.gates}
        ok(len(kit.gates) == 12 and st["G9"] == "ERROR" and "ZeroDivisionError" in key["G9"] and st["G10"] == "PASS"
           and code == 1, "a crash in one gate: that gate is ERROR (with the exception); the other 11 still run")
        ok(overall_exit(["PASS", "ERROR", "MANUAL"]) == 3, "ERROR alone is exit 3, never 0 or 1")
        real_run, buf, err, old = Kit.run, io.StringIO(), io.StringIO(), (sys.stdout, sys.stderr)
        Kit.run = lambda self, out: 1 // 0
        sys.stdout, sys.stderr = buf, err
        try:
            code = main([md, "--status", sd, "--brief", "--force"])
        finally:
            Kit.run = real_run
            sys.stdout, sys.stderr = old
        ok(code == 6 and "GATES: ERROR; exit 6" in buf.getvalue() and "ZeroDivisionError" in err.getvalue(),
           "a crash outside the gates: traceback, 'GATES: ERROR; exit 6', exit 6")
        kit = Kit(ns)
        kit.arms["p2"]["cvars"]["brand_new_switch"] = "true"
        g = kit.g10()
        ok(g.status == "CHECK" and "no proof line known for 1 switch(es): brand_new_switch" in g.key,
           "G10: a switch with no known proof line is CHECK, named in the key")
        dll = os.path.join(rows[2]["run_dir"], "rexgpu-xenos.dll")
        with open(dll, "r+b") as fh:
            fh.write(b"N")
        ns.one_bin = True
        g = Kit(ns).g2()
        ok(g.status == "FAIL" and "12/13 runs" in g.key and "one bin required (--one-bin)" in g.key
           and any("rexgpu-xenos.dll differs from the bin's (same size, other SHA-256)" in d for d in g.details),
           "G2: a dll copy of the same size but another SHA-256 FAILs")
        shutil.copyfile(os.path.join(b, "rexgpu-xenos.dll"), dll)
        b2 = os.path.join(tmp, "bin2")
        shutil.copytree(b, b2)
        mj = read_json(os.path.join(md, "matrix.json"))
        mj["arms"][0]["bin"] = b2
        with open(os.path.join(md, "matrix.json"), "w", encoding="utf-8") as fh:
            json.dump(mj, fh)
        for r in rows:
            if r["arm"] == "s0":
                rj = read_json(os.path.join(r["run_dir"], "run.json"))
                rj["bin_dir"] = b2
                with open(os.path.join(r["run_dir"], "run.json"), "w", encoding="utf-8") as fh:
                    json.dump(rj, fh)
        g = Kit(ns).g2()
        ok(g.status == "FAIL" and "13/13 runs" in g.key and "2 bins" in g.key
           and any("--one-bin: the run arms use 2 bins" in d for d in g.details), "G2 --one-bin: s0 on a second bin FAILs")
        ns.one_bin = False
        g = Kit(ns).g2()
        ok(g.status == "PASS" and "13/13 runs" in g.key and "2 bins" in g.key and "one bin" not in g.key,
           "G2 without --one-bin: two bins, each run on its arm's bin, PASS")

        def fl(v, last=None):
            return {"first": v, "last": v if last is None else last, "changes": [] if last is None else [{"t": 1}]}

        def sysjson(odd=False):
            for r in rows:
                win = {"overlay": fl("best_efficiency"), "scheme": fl("Balanced"), "ac": fl(1), "batt_saver": fl(0),
                       "cpu_util_mean": 40.0}
                if odd and r["seq"] == 6:
                    win["scheme"] = fl("High performance")
                if odd and r["seq"] == 7:
                    win["ac"] = fl(1, 0)
                with open(os.path.join(r["run_dir"], "sys.json"), "w", encoding="utf-8") as fh:
                    json.dump({"window": win, "run": {"overlay": fl("best_efficiency")}}, fh)
        sysjson()
        g11 = Kit(ns).g11_g12()[0]
        ok(g11.status == "PASS" and "13/13 runs, no change inside any window" in g11.key,
           "G11: one overlay, scheme, AC and saver value in every run: PASS")
        sysjson(odd=True)
        g11 = Kit(ns).g11_g12()[0]
        ok(g11.status == "FAIL" and any("scheme is not one value in every run" in d for d in g11.details)
           and any(d.startswith("AC is not one value") and "changed inside the window in #7 p2" in d
                   for d in g11.details), "G11: another scheme in one run, AC changing inside one window: FAIL")
        old_gate = os.path.join(tmp, "gate-0610.log")
        write(old_gate, ["06:10:00 quiet gate: STRICT (MsMpEng 0.02/0.02/0.02, OfficeClickToRun 0.00/0.00/0.00, "
                         "CrossDeviceService 0.01/0.01/0.01)"])
        ns.gate_log = old_gate
        g12 = Kit(ns).g11_g12()[1]
        ns.gate_log = None
        ok(g12.status == "CHECK" and "> 30 min before the window" in g12.key,
           "G12: a gate line 40 min before the window start is CHECK")
        write(old_gate, ["06:50:01 quiet gate: STRICT (MsMpEng 0.02/0.02/0.02, OfficeClickToRun 0.00/0.00/0.00, "
                         "CrossDeviceService 0.01/0.01/0.01)"])
        ns.gate_log = old_gate
        g12 = Kit(ns).g11_g12()[1]
        ok(g12.status == "PASS" and "the right gate log" not in g12.key
           and any("06:50, 0 min later" in d for d in g12.details),
           "G12: a gate line inside the start minute (06:50:01, dir 0650) is PASS at 0 min (task #24 fix)")
        write(old_gate, ["06:55:00 quiet gate: STRICT (MsMpEng 0.02/0.02/0.02, OfficeClickToRun 0.00/0.00/0.00, "
                         "CrossDeviceService 0.01/0.01/0.01)"])
        g12 = Kit(ns).g11_g12()[1]
        ns.gate_log = None
        ok(g12.status == "CHECK" and "after the window start" in g12.key,
           "G12: a gate line 5 min after the window start is CHECK")
        s3 = os.path.join(tmp, "sides", "side3")  # made by the timing runner: params.cvar list, no exe_sha256
        os.makedirs(s3)
        for n in ("MANIFEST.txt", "legodimensions.exe"):
            shutil.copyfile(os.path.join(b, n), os.path.join(s3, n))
        write(os.path.join(s3, "game.log"), [info("05:10:00", "Startup: launching the module")]
              + [slow(i) for i in range(2, 8)])
        with open(os.path.join(s3, "run.json"), "w", encoding="utf-8") as fh:
            json.dump({"bin_dir": b, "params": {"cvar": p2f + ["slow_frame_log_ms=1"]}, "env_set": {}}, fh)
        ns.side = [s1, s3]
        kit = Kit(ns)
        g = kit.g2()
        ns.side = [s1]
        ok(kit.sides[1]["cvars"].get(P2_SWITCH) == "true" and g.status == "PASS"
           and "side runs 3/3 on the P2 bin" in g.key,
           "a side run in the timing runner's format (params.cvar, no exe_sha256): cvars read, exe copy SHA-256 checked")


def selftest():
    results = []

    def ok(cond, text):
        results.append((bool(cond), text))

    def write(path, lines):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write("".join(x + "\r\n" for x in lines))

    m = END_RE.search("2026-11-23 07:31:02 window W6 END: runner exit 0 (matrix done) after 41 min; out dir "
                      "C:\\r\\build\\agent8\\matrix\\20261123-0650")
    ok(m and m.group("code") == "0" and m.group("dir").endswith("20261123-0650") and not m.group("suspect"),
       "END line parsed")
    m = END_RE.search("2026-11-23 07:31:02 window W6 END: runner exit 1 (runs failed (2)) after 41.5 min; out dir "
                      "D:\\x\\20261123-0650; SUSPECT: no summary.md")
    ok(m and m.group("code") == "1" and m.group("dir") == "D:\\x\\20261123-0650"
       and m.group("suspect") == "no summary.md" and m.group("meaning") == "runs failed (2)", "END line with SUSPECT")
    with tempfile.TemporaryDirectory() as tmp:
        md = os.path.join(tmp, "matrix", "20261123-0650")
        os.makedirs(md)
        s1 = os.path.join(tmp, "s1")
        write(os.path.join(s1, "window-W5-0500.log"), [f"2026-11-23 05:41:00 window W5 END: runner exit 0 (ok) after 40 "
                                                       f"min; out dir {os.path.join(tmp, 'matrix', '20261123-0500')}"])
        write(os.path.join(s1, "window-W6-0640.log"), ["2026-11-23 06:40:00 window W6 START (estimate 41 min, about "
                                                       "07:21): x", f"2026-11-23 07:31:02 window W6 END: runner exit 0 "
                                                       f"(ok) after 41 min; out dir {md}"])
        p, how = find_window_log(s1, md)
        ok(p and p.endswith("window-W6-0640.log") and "END" in how, "window log found by its END line")
        s2 = os.path.join(tmp, "s2")
        write(os.path.join(s2, "window-W7-0700.log"), ["2026-11-23 07:00:00 window W7 START (estimate 41 min, about "
                                                       "07:41): x"])
        write(os.path.join(s2, "runner-W7-0700.txt"), ["runner start", f"out dir: {md}"])
        p, how = find_window_log(s2, md)
        ok(p and p.endswith("window-W7-0700.log") and "runner-W7-0700.txt" in how, "window log found by runner file")
        s3 = os.path.join(tmp, "s3")
        write(os.path.join(s3, "window-W8-0649.log"), ["2026-11-23 06:49:30 window W8 START (estimate 41 min, about "
                                                       "07:30): x"])
        write(os.path.join(s3, "window-W9-0400.log"), ["2026-11-23 04:00:00 window W9 START (estimate 41 min, about "
                                                       "04:41): x"])
        p, how = find_window_log(s3, md)
        ok(p and p.endswith("window-W8-0649.log") and "START" in how, "window log found by its START time")
        s4 = os.path.join(tmp, "s4")
        write(os.path.join(s4, "window-W9-0400.log"), ["2026-11-23 06:49:30 [dry] window W9 START (estimate 41 min, "
                                                       "about 07:30): x"])
        p, how = find_window_log(s4, md)
        ok(p is None, "no window log: a dry-run START doesn't count")
        p, how = find_window_log_any((os.path.join(tmp, "none"), s3, s2), md)
        ok(p and p.endswith("window-W7-0700.log") and "found in" in how,
           "N6: two status dirs, a runner-file match beats a START-time match")
        p, how = find_window_log_any((s1, s2), md)
        ok(p is None and how.startswith("ambiguous"), "N6: two status dirs matching alike are ambiguous")
        p, how = find_window_log_any((os.path.join(tmp, "none"), s4), md)
        ok(p is None and "no window log" in how, "N6: no match in any status dir")
        plan = os.path.join(tmp, "plan.txt")
        write(plan, ["=== timing matrix: t ===", "arms:",
                     "       s0: bin build/agent2/b; frames perf; x3; warm-up 55 s; group w6 (ref); cvars framerate_limit=0",
                     "         note text: bin nothing; x9;", "       p2: bin build/agent2/b; frames perf; x3; warm-up 55 s",
                     "cold     s0 (build/agent2/b): unscored, before round 1", "round 1  s0 p2", "round 2  p2 s0",
                     "round 3  s0 p2", "estimate 7 runs (1 cold), about 17 min (warm boot 12 s)", "",
                     "--- preflight ---", "sys.csv    on: drivers\\sys-csv.ps1", "estimate   7 runs, about 17 min"])
        pp = parse_plan(plan)
        ok(pp["estimate"] == 7 and pp["estimate_cold"] == 1 and list(pp["arms"]) == ["s0", "p2"]
           and pp["arms"]["s0"]["repeats"] == 3 and pp["cold"] == ["s0"] and pp["rounds"] == 3 and pp["sys_csv"],
           "plan.txt parsed (arms, repeats, cold, estimate, rounds, sys.csv)")
        rd = os.path.join(tmp, "run1")
        os.makedirs(rd)
        with open(os.path.join(rd, "sys.json"), "w", encoding="utf-8") as fh:
            json.dump({"window_start_epoch": 100, "window_end_epoch": 110}, fh)
        write(os.path.join(rd, "sys.csv"), ["t_s,epoch_s,e_eff_mhz"] + [
            f"{t - 90},{t},{700 if t in (97, 98, 99, 100, 105, 106) else 900}" for t in range(90, 116)])
        st = slow_state(rd)
        ok(st and st["stretch"] and st["longest"] == 4 and st["slow"] == 3 and st["rows"] == 11,
           "slow state: a 4-sample stretch overlapping the window start")
        write(os.path.join(rd, "sys.csv"), ["t_s,epoch_s,e_eff_mhz"] + [
            f"{t - 90},{t},{700 if t in (95, 96, 97, 105, 106) else 900}" for t in range(90, 116)])
        st = slow_state(rd)
        ok(st and not st["stretch"] and st["longest"] == 2 and st["slow"] == 2,
           "slow state: a 3-sample stretch before the window doesn't count")
    d11 = {"framerate_limit": "0", "host_timer_resolution_ms": "1", "host_timer_throttling_optout": "true"}
    c0 = OrderedDict((k, 0) for k in LINES)

    def c(**kw):
        x = OrderedDict(c0)
        x.update(kw)
        return x
    p2fc = {P2_SWITCH: "true", LOCK_SWITCH: "true", KW_SWITCH: "true", VERIFY_SWITCH: "false"}
    ok(not proof_check(dict(d11, timer_queue_precise_wait="true"), c(timer1ms=1, optout=1, precise=1)), "d11p proof ok")
    ok(not proof_check(d11, c(timer1ms=1, optout=1)), "d11 proof ok")
    ok(proof_check({"framerate_limit": "0"}, c(precise=1)), "a precise-wait line without the switch fails")
    ok(proof_check(dict(d11, timer_queue_precise_wait="true"), c(timer1ms=1, optout=1, precise=2)),
       "two precise-wait lines fail")
    ok(proof_check(d11, c(timer1ms=1)), "the 1 ms line without '(background opt-out on)' fails")
    ok(proof_check({"framerate_limit": "0"}, c(timer1ms=1, optout=1)), "a 1 ms line without the switch fails")
    ok(not proof_check(p2fc, c(kw_on=1, kw_first=1)), "p2fc proof ok")
    ok(proof_check(p2fc, c(kw_on=1, kw_first=1, verify_on=1)), "p2fc with 'C1 verify: on' fails")
    ok(proof_check(p2fc, c(kw_nolock=1, kw_first=1)), "keep-watch without the lock fails")
    ok(proof_check(p2fc, c(kw_on=1)), "keep-watch without a first kept protect fails")
    ok(proof_check({P2_SWITCH: "true"}, c(kw_on=1)), "a keep-watch line without the switch fails")
    ok(not proof_check({P2_SWITCH: "true", LOCK_SWITCH: "true"}, c()), "p2f proof ok (no log line)")
    ok(proof_check(dict(p2fc, **{VERIFY_SWITCH: "true"}), c(kw_on=1, kw_first=1, verify_on=1, verify_k=1)),
       "a 'C1 verify K:' line fails")
    ok(kv_norm(["A=True", " b = 1 ", "--c=x"]) == {"a": "true", "b": "1", "c": "x"}, "kv_norm on a list")
    ok(kv_norm({"A": True, "n": 0}) == {"a": "true", "n": "0"}, "kv_norm on a dict")
    ok(env_norm({"rex_timer_wait_blocking": 1}) == {"REX_TIMER_WAIT_BLOCKING": "1"}, "env_norm")
    ok(forbidden({"slow_frame_log_ms": "1"}) and not forbidden({"slow_frame_log_ms": "0"})
       and forbidden({"shared_memory_upload_hash_log": "true"}) and not forbidden({"framerate_limit": "0"}),
       "timing-forbidden switches")
    ok(overall_exit(["PASS", "MANUAL", "n/a", "CODE"]) == 0 and overall_exit(["PASS", "CHECK"]) == 3
       and overall_exit(["PENDING", "PASS"]) == 3 and overall_exit(["CHECK", "FAIL"]) == 1, "exit codes")
    s_a, s_b = empty_scan(""), empty_scan("")
    s_a["files"], s_b["files"] = [{"path": "a", "bytes": 1}], [{"path": "b", "bytes": 1}]
    s_a["boot_lines_found"] = s_b["boot_lines_found"] = True
    s_a["warn"]["[warning] [x] one #"], s_b["warn"]["[warning] [x] two #"] = 2, 5
    s_a["warn_example"]["[warning] [x] one #"], s_b["warn_example"]["[warning] [x] two #"] = "one 1", "two 2"
    merged = merge_scans([s_a, s_b], "ref x2")
    s_c = empty_scan("")
    s_c["files"], s_c["boot_lines_found"] = [{"path": "c", "bytes": 1}], True
    s_c["warn"]["[warning] [x] two #"] = 1
    s_c["warn"]["[warning] [x] three #"] = 1
    s_c["warn_example"]["[warning] [x] three #"] = "three 3"
    s_c["warn_example"]["[warning] [x] two #"] = "two 2"
    findings, notes, _, diff = gate_logdiff.compare(merged, s_c, 10)
    ok(not findings and not notes and diff["new_in_b_total"] == 1 and diff["new_in_b"][0]["msg"].endswith("three #"),
       "logdiff against merged reference runs: one NEW kind, no false notes")
    s_c["fail"]["REX_FATAL"] = 1
    s_c["fail_examples"]["REX_FATAL"] = "REX_FATAL x"
    findings, _, _, _ = gate_logdiff.compare(merged, s_c, 10)
    ok(len(findings) == 1 and "REX_FATAL" in findings[0], "logdiff: a fail pattern is a finding")
    try:
        selftest_w6(ok)
    except Exception as exc:  # noqa: BLE001 - a crash in the end-to-end case is a failed check
        import traceback
        where = traceback.extract_tb(exc.__traceback__)[-1]
        ok(False, f"W6-like matrix: {type(exc).__name__}: {exc} (line {where.lineno} in {where.name})")
    for good, text in results:
        print(f"{'ok  ' if good else 'FAIL'} {text}")
    nbad = sum(1 for good, _ in results if not good)
    print(f"SELFTEST {'PASS' if not nbad else 'FAIL'} ({len(results) - nbad}/{len(results)} checks)")
    return 1 if nbad else 0


def main(argv=None):
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="W6 gate kit: every W6 gate (G1-G12) on a finished matrix dir.")
    ap.add_argument("matrix_dir", nargs="?", help="a run-matrix output dir (matrix.json, plan.txt, results.csv, runs/)")
    ap.add_argument("--status", metavar="DIR", help="the launcher's status dir to search for the window log "
                                                     "(default: bench/agent5/launch/status and bench/agent5/day/status, those that exist)")
    ap.add_argument("--window-log", metavar="FILE", help="the launcher's window-<id>-<HHmm>.log (skips the search)")
    ap.add_argument("--gate-log", metavar="FILE", help="the quiet-gate log for G12 (default: the window log)")
    ap.add_argument("--gate", choices=("strict", "relaxed"), help="set G12's gate by hand")
    ap.add_argument("--side", metavar="DIR", action="append", default=[], help="a side-run dir (side 1-3), repeatable")
    ap.add_argument("--gate-a", metavar="DIR", help="the gate-A run dir")
    ap.add_argument("--ncpu", type=int, help="logical CPUs for the non-game load (default: this PC's)")
    ap.add_argument("--json", metavar="OUT", help="also write the gates as JSON")
    ap.add_argument("--expect", metavar="FIXTURE", help="compare with a fixture JSON: exit 0 if it holds, else 5")
    ap.add_argument("--one-bin", action="store_true", help="G2 FAILs unless the run arms use one bin (W6: one bin "
                                                           "everywhere)")
    ap.add_argument("--brief", action="store_true", help="table and RECORD line only")
    ap.add_argument("--force", action="store_true", help="run even while perf-notes/WINDOW-HOLD.txt exists")
    ap.add_argument("--selftest", action="store_true", help="run the built-in tests")
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    lower_priority()
    if os.path.exists(HOLD) and not a.force:
        print("perf-notes/WINDOW-HOLD.txt exists: a timed window is running; not starting (--force after it ends)")
        return 4
    if a.selftest:
        return selftest()
    if not a.matrix_dir:
        ap.print_usage()
        return 2
    try:
        kit = Kit(a)
    except UsageError as exc:
        print(f"run_gates: {exc}", file=sys.stderr)
        return 2
    except Exception:  # noqa: BLE001 - a kit bug must never look like a gate FAIL (exit 1)
        traceback.print_exc()
        print("run_gates: ERROR: the kit failed while reading the matrix (send this output to Agent 12)")
        print("GATES: ERROR; exit 6")
        return 5 if a.expect else 6
    try:
        code = kit.run(sys.stdout)
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        print("run_gates: ERROR: the kit failed while reporting (send this output to Agent 12)")
        print("GATES: ERROR; exit 6")
        return 5 if a.expect else 6
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(kit.as_dict(), fh, indent=1)
    if a.expect:
        return check_expect(a.expect, kit, sys.stdout)
    return code


if __name__ == "__main__":
    sys.exit(main())

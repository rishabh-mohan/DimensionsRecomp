"""S3T-12 item 3 (N6): patch the staged copy build/agent12/w6-gates-n6/run_gates.py so that, without --status,
the window log is searched in both launcher status folders (night: bench/agent5/launch/status, day:
bench/agent5/day/status) and the report names the folder used. Exact-anchor replaces; asserts each anchor is unique.
Writes only build/agent12/w6-gates-n6/run_gates.py and build/agent12/session3/n6/n6-run_gates.diff."""
import hashlib, os, subprocess

A12 = r"<workspace>\build\agent12"
ORIG = os.path.join(A12, "w6-gates", "run_gates.py")
NEW = os.path.join(A12, "w6-gates-n6", "run_gates.py")
src = open(ORIG, "rb").read().decode("utf-8")
nl = "\r\n" if "\r\n" in src else "\n"
s = src.replace("\r\n", "\n")

R = [
    # docstring
    ("The launcher's window log (bench/agent5/launch/status/window-<id>-<HHmm>.log) is found from --status (default:\n"
     "that dir, if it exists) by (1) an END line whose out dir is this dir, (2) a runner-<tag>.txt naming this dir, or\n"
     "(3) a START line within 3 min of the dir's YYYYMMDD-HHMM.",
     "The launcher's window log (window-<id>-<HHmm>.log) is found from --status (default: both launcher status dirs\n"
     "that exist, night bench/agent5/launch/status and day bench/agent5/day/status (N6); the report names the one used)\n"
     "by (1) an END line whose out dir is this dir, (2) a runner-<tag>.txt naming this dir, or\n"
     "(3) a START line within 3 min of the dir's YYYYMMDD-HHMM. A match in both dirs at the same strength is ambiguous:\n"
     "no window log (CHECK); give --status or --window-log."),
    # constants
    ('STATUS_DIR = os.path.join(REPO, "bench", "agent5", "launch", "status")\n',
     'STATUS_DIR = os.path.join(REPO, "bench", "agent5", "launch", "status")\n'
     'DAY_STATUS_DIR = os.path.join(REPO, "bench", "agent5", "day", "status")  # N6: day windows log here\n'
     'STATUS_DIRS = (STATUS_DIR, DAY_STATUS_DIR)\n'),
    # new helper after find_window_log
    ('    return None, f"no window log in {status_dir} names this out dir"\n\n',
     '    return None, f"no window log in {status_dir} names this out dir"\n\n\n'
     'def find_window_log_any(status_dirs, mdir):\n'
     '    """N6: find_window_log over several status dirs (night and day). A match by END line or runner file beats a\n'
     '    START-time match; two dirs matching at the same strength is ambiguous, so no window log (the gate says CHECK)."""\n'
     '    dirs = [d for d in status_dirs if d and os.path.isdir(d)]\n'
     '    if not dirs:\n'
     '        return None, "no status dir (" + ", ".join(os.path.relpath(d, REPO) for d in status_dirs) + " don\'t exist)"\n'
     '    hits, misses = [], []\n'
     '    for d in dirs:\n'
     '        p, how = find_window_log(d, mdir)\n'
     '        (hits if p else misses).append((p, how, d))\n'
     '    strong = [h for h in hits if "START line" not in h[1]]\n'
     '    pick = strong or hits\n'
     '    if len(pick) == 1:\n'
     '        p, how, d = pick[0]\n'
     '        return p, f"{how}; found in {os.path.relpath(d, REPO)}"\n'
     '    if len(pick) > 1:\n'
     '        return None, "ambiguous: " + "; ".join(f"{os.path.relpath(p, REPO)} ({how})" for p, how, _ in pick) + \\\n'
     '            " (give --status or --window-log)"\n'
     '    return None, "no window log names this out dir in " + ", ".join(os.path.relpath(d, REPO) for d in dirs)\n\n'),
    # Kit: default search
    ('            sd = a.status or (STATUS_DIR if os.path.isdir(STATUS_DIR) else None)\n'
     '            self.window_log, self.window_how = find_window_log(sd, self.mdir) if sd else (\n'
     '                None, f"not searched ({os.path.relpath(STATUS_DIR, REPO)} doesn\'t exist; give --status or --window-log)")\n',
     '            if a.status:\n'
     '                self.window_log, self.window_how = find_window_log(a.status, self.mdir)\n'
     '            else:  # N6: night and day launcher folders\n'
     '                self.window_log, self.window_how = find_window_log_any(STATUS_DIRS, self.mdir)\n'),
    # argparse help
    ('"(default bench/agent5/launch/status, if it exists)")',
     '"(default: bench/agent5/launch/status and bench/agent5/day/status, '
     'those that exist)")'),
    # selftest: add N6 cases after the dry-run case
    ('        ok(p is None, "no window log: a dry-run START doesn\'t count")\n',
     '        ok(p is None, "no window log: a dry-run START doesn\'t count")\n'
     '        p, how = find_window_log_any((os.path.join(tmp, "none"), s3, s2), md)\n'
     '        ok(p and p.endswith("window-W7-0700.log") and "found in" in how,\n'
     '           "N6: two status dirs, a runner-file match beats a START-time match")\n'
     '        p, how = find_window_log_any((s1, s2), md)\n'
     '        ok(p is None and how.startswith("ambiguous"), "N6: two status dirs matching alike are ambiguous")\n'
     '        p, how = find_window_log_any((os.path.join(tmp, "none"), s4), md)\n'
     '        ok(p is None and "no window log" in how, "N6: no match in any status dir")\n'),
]
for old, new in R:
    assert s.count(old) == 1, ("anchor count", s.count(old), old[:70])
    s = s.replace(old, new)
open(NEW, "wb").write(s.replace("\n", nl).encode("utf-8"))

out = os.path.join(A12, "session3", "n6")
os.makedirs(out, exist_ok=True)
r = subprocess.run(["git", "diff", "--no-index", "--no-color", "w6-gates/run_gates.py", "w6-gates-n6/run_gates.py"],
                   cwd=A12, capture_output=True)
diff = r.stdout.replace(b"a/w6-gates-n6/", b"b/w6-gates/").replace(b"b/w6-gates-n6/", b"b/w6-gates/")
open(os.path.join(out, "n6-run_gates.diff"), "wb").write(diff)
for p in (ORIG, NEW, os.path.join(out, "n6-run_gates.diff")):
    print(hashlib.sha256(open(p, "rb").read()).hexdigest().upper()[:16], os.path.relpath(p, A12))

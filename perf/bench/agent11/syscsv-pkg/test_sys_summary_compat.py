#!/usr/bin/env python3
"""test_sys_summary_compat.py - Agent 11, 2026-11-22. Python 3, stdlib only, ASCII.

Checks that Agent 8's bench/agent8/run/sys_summary.py still reads a sys.csv written by the
staged package-power sampler (bench/agent11/syscsv-pkg/LdSys.cs: 4 extra columns at the
end, pkg_w,pp0_w,pp1_w,dram_w), and that the staged 1-line fix in
bench/agent11/syscsv-pkg/sys_summary.py (header_ok = the known columns form a prefix of
the header) changes nothing else.

Inputs (defaults: the newest test_syscsv_pkg.ps1 run under build/agent11/syscsv-pkg/test):
  --new  a sys.csv with the 4 extra columns (from an NN-staged run dir)
  --old  a sys.csv in the original 24-column format (from an NN-orig run dir), optional
Runs both scripts on each file over its whole epoch range, writes their JSON to
build/agent11/syscsv-pkg/compat/<stamp>/ and compares them.
Pass: every run exits 0; on the new file the original reports header_ok false with no
missing columns (expected: this is the gap the fix closes) and the staged copy reports
true; on the old file both report true; apart from header_ok the JSON is identical.
Writes nothing outside the out dir. Exit 0 pass, 1 fail, 2 no input / bad arguments.
"""
import argparse
import csv
import glob
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ORIG = os.path.join(ROOT, "bench", "agent8", "run", "sys_summary.py")
STAGED = os.path.join(HERE, "sys_summary.py")
TESTROOT = os.path.join(ROOT, "build", "agent11", "syscsv-pkg", "test")


def newest(pattern):
    c = [p for p in glob.glob(pattern) if os.path.isfile(p)]
    c.sort(key=os.path.getmtime)
    return c[-1] if c else None


def epoch_range(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))
    hdr = [h.strip() for h in rows[0]]
    i = hdr.index("epoch_s")
    vals = []
    for r in rows[1:]:
        try:
            vals.append(float(r[i]))
        except (ValueError, IndexError):
            pass
    if len(vals) < 2:
        raise ValueError("fewer than 2 epoch_s values in %s" % path)
    return vals[0], vals[-1], len(hdr)


def run(script, csv_path, s, e, out):
    cmd = [sys.executable, script, "--csv", csv_path, "--start-epoch", "%.3f" % s,
           "--end-epoch", "%.3f" % e, "--out", out]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    data = None
    if os.path.isfile(out):
        with open(out, encoding="utf-8-sig") as fh:
            data = json.load(fh)
    return p.returncode, data, (p.stdout or "").strip(), (p.stderr or "").strip()


def find_key(d, key):
    if isinstance(d, dict):
        if key in d:
            return d[key]
        for v in d.values():
            r = find_key(v, key)
            if r is not None:
                return r
    elif isinstance(d, list):
        for v in d:
            r = find_key(v, key)
            if r is not None:
                return r
    return None


def diff_paths(a, b, path="", skip=("header_ok",)):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k in skip:
                continue
            if k not in a or k not in b:
                out.append(path + "/" + k)
            else:
                out.extend(diff_paths(a[k], b[k], path + "/" + k, skip))
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(path + "[len]")
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                out.extend(diff_paths(x, y, "%s[%d]" % (path, i), skip))
    elif a != b:
        out.append(path)
    return out


def main():
    ap = argparse.ArgumentParser(description="sys_summary.py compatibility with the package-power columns")
    ap.add_argument("--new", help="sys.csv with the 4 extra columns")
    ap.add_argument("--old", help="sys.csv in the original 24-column format")
    ap.add_argument("--out-dir", help="default build/agent11/syscsv-pkg/compat/<stamp>")
    a = ap.parse_args()
    new = a.new or newest(os.path.join(TESTROOT, "*", "*-staged", "sys.csv"))
    old = a.old or newest(os.path.join(TESTROOT, "*", "*-orig", "sys.csv"))
    if not new or not os.path.isfile(new):
        print("RESULT: NO INPUT - no new-format sys.csv (run test_syscsv_pkg.ps1 first or pass --new)")
        return 2
    for s in (ORIG, STAGED):
        if not os.path.isfile(s):
            print("RESULT: NO INPUT - missing %s" % s)
            return 2
    out_dir = a.out_dir or os.path.join(ROOT, "build", "agent11", "syscsv-pkg", "compat",
                                        time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(out_dir, exist_ok=True)
    bad = []
    lines = ["orig   %s" % os.path.relpath(ORIG, ROOT), "staged %s" % os.path.relpath(STAGED, ROOT)]
    cases = [("new", new, False)]
    if old and os.path.isfile(old):
        cases.append(("old", old, True))
    else:
        lines.append("old-format file: none found, skipped")
    for name, path, orig_ok in cases:
        try:
            s, e, ncol = epoch_range(path)
        except (OSError, ValueError, IndexError) as ex:
            bad.append("%s: cannot read %s: %s" % (name, path, ex))
            continue
        lines.append("%s: %s (%d columns, epoch %.1f-%.1f)" % (name, os.path.relpath(path, ROOT), ncol, s, e))
        res = {}
        for tag, script in (("orig", ORIG), ("staged", STAGED)):
            out = os.path.join(out_dir, "%s-%s.json" % (name, tag))
            rc, data, so, se = run(script, path, s, e, out)
            res[tag] = data if rc == 0 else None
            hk = find_key(data, "header_ok") if data is not None else None
            mc = find_key(data, "missing_columns") if data is not None else None
            lines.append("  %-6s exit %d header_ok=%s missing_columns=%s" % (tag, rc, hk, mc))
            lines.append("  %-6s stdout: %s" % (tag, so[:240]))
            if se:
                lines.append("  %-6s stderr: %s" % (tag, se[:300]))
            if rc != 0 or data is None:
                bad.append("%s/%s: exit %d or no JSON" % (name, tag, rc))
                continue
            want = orig_ok if tag == "orig" else True
            if hk is not want:
                bad.append("%s/%s: header_ok=%s, expected %s" % (name, tag, hk, want))
            if mc not in ([], None):
                bad.append("%s/%s: missing_columns=%s" % (name, tag, mc))
        if res.get("orig") is not None and res.get("staged") is not None:
            d = diff_paths(res["orig"], res["staged"])
            lines.append("  JSON differences apart from header_ok: %s" % (", ".join(d) if d else "none"))
            if d:
                bad.append("%s: JSON differs at %s" % (name, ", ".join(d[:10])))
    lines.append("RESULT: %s" % ("PASS" if not bad else "FAIL - " + "; ".join(bad)))
    text = "\n".join(lines)
    print(text)
    with open(os.path.join(out_dir, "result.txt"), "w", encoding="ascii", errors="replace", newline="\n") as fh:
        fh.write(text + "\n")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())

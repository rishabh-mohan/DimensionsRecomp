"""Tests for bench/agent7/native3_boot_check.py (Agent 7, task #6, session 3).

Usage: python bench\\agent7\\test_native3_boot_check.py [-v]
Runs the checker on two real run dirs and five synthetic fixtures, and compares the group verdicts with
the expected ones:
  real-n0    window-3 0030-n0-r1 (native2, --native_settings_frontend=false), --ref 0042-n0-r2:
             A FAIL, B PASS, C PASS, exit 1
  real-2315  build/agent8/runs/2315-native (native-bin, frontend on, the S2 throw): A PASS, B FAIL, C FAIL, exit 1
  pos        n0-r1 with the frontend flag removed from run.json (its toml has native_settings_frontend = true),
             --bin-dir native2-bin, --ref 0042-n0-r2: A PASS, B PASS, C PASS, D PASS, exit 0
  fsr1       pos, plus spatial_fsr_presented=1 on the last 100 rows and a "Native FSR 1:" warning: C FAIL, exit 1
  crash      pos, plus the last lines of the 2315 game.log, exited_early/werfault/exit code in run.json and a
             .dmp: B FAIL, exit 1
  cli-true   pos with the toml set to false and --native_settings_frontend=true on the command line: A PASS
             (the command line wins), exit 0
  cli-false  pos with --native_settings_frontend=false on the command line (the toml says true): A FAIL, exit 1
Fixtures and the checker's output (<case>.txt) go to build/agent7/native3-check-test/ and are rebuilt on every
run. Stdlib only, one thread.
"""
import csv
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
M = os.path.join(ROOT, "build", "agent8", "matrix", "20261122-0013", "runs")
N0 = os.path.join(M, "0030-n0-r1")
REF = os.path.join(M, "0042-n0-r2")
CRASH = os.path.join(ROOT, "build", "agent8", "runs", "2315-native")
BIN2 = os.path.join(ROOT, "build", "agent2", "native2-bin")
OUT = os.path.join(ROOT, "build", "agent7", "native3-check-test")
CHECK = os.path.join(ROOT, "bench", "agent7", "native3_boot_check.py")
COPY = ("run.json", "game.log", "legodimensions.toml", "native-frames.csv", "perf.csv", "frames.json",
        "MANIFEST.txt", "proc.csv")
VERBOSE = "-v" in sys.argv


def fixture(name):
    d = os.path.join(OUT, name)
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
    for f in COPY:
        if os.path.exists(os.path.join(N0, f)):
            shutil.copy2(os.path.join(N0, f), d)
    edit_json(d, drop_frontend)
    return d


def edit_json(d, fn):
    path = os.path.join(d, "run.json")
    with open(path, encoding="utf-8-sig") as f:
        rj = json.load(f)
    fn(rj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rj, f, indent=2)


def drop_frontend(rj):
    rj["args"] = [x for x in rj.get("args", []) if "native_settings_frontend" not in x]
    params = rj.get("params") or {}
    params["cvar"] = [x for x in params.get("cvar", []) if "native_settings_frontend" not in x]


def set_toml(d, value):
    path = os.path.join(d, "legodimensions.toml")
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    new, n = re.subn(r"(?m)^(\s*native_settings_frontend\s*=\s*)\S+", r"\g<1>" + value, text)
    assert n == 1, "toml has %d native_settings_frontend lines" % n
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(new)


def append_log(d, lines):
    with open(os.path.join(d, "game.log"), "a", encoding="utf-8") as f:
        for line in lines:
            f.write(line.rstrip("\r\n") + "\n")


def set_fsr1(d):
    path = os.path.join(d, "native-frames.csv")
    with open(path, newline="") as f:
        rows = list(csv.reader(f))
    col = rows[0].index("spatial_fsr_presented")
    for r in rows[-100:]:
        r[col] = "1"
    with open(path, "w", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows(rows)
    append_log(d, ["[fixture] [warning] Native FSR 1: presentation setup failed; using the native spatial copy"])


def make_crash(d):
    with open(os.path.join(CRASH, "game.log"), encoding="utf-8", errors="replace") as f:
        append_log(d, f.read().splitlines()[-6:])

    def fn(rj):
        rj.update(exited_early=True, werfault_seen=True, exit_code=-1073740940, exit_code_hex="0xC0000374")
    edit_json(d, fn)
    open(os.path.join(d, "legodimensions.exe.1234.dmp"), "wb").close()


def run(name, d, extra, expect, code):
    p = subprocess.run([sys.executable, CHECK, d] + extra, capture_output=True, text=True)
    with open(os.path.join(OUT, name + ".txt"), "w", encoding="utf-8") as f:
        f.write(p.stdout + p.stderr)
    m = re.search(r"^VERDICT (.*) -> (\w+) \(exit (\d+)\)", p.stdout, re.M)
    got = dict(re.findall(r"([A-D])=(\w+)", m.group(1))) if m else {}
    ok = bool(m) and p.returncode == code and all(got.get(g) == v for g, v in expect.items())
    print("%-10s %s exit %d (want %d); %s; want %s" % (
        name, "OK  " if ok else "FAIL", p.returncode, code, m.group(0) if m else "no VERDICT line",
        " ".join("%s=%s" % kv for kv in sorted(expect.items()))))
    if VERBOSE or not ok:
        print(p.stdout + p.stderr)
    return ok


def main():
    os.makedirs(OUT, exist_ok=True)
    res = [run("real-n0", N0, ["--ref", REF], {"A": "FAIL", "B": "PASS", "C": "PASS"}, 1),
           run("real-2315", CRASH, [], {"A": "PASS", "B": "FAIL", "C": "FAIL"}, 1)]
    pos = fixture("pos")
    res.append(run("pos", pos, ["--bin-dir", BIN2, "--ref", REF], {"A": "PASS", "B": "PASS", "C": "PASS", "D": "PASS"}, 0))
    d = fixture("fsr1")
    set_fsr1(d)
    res.append(run("fsr1", d, ["--bin-dir", BIN2], {"A": "PASS", "B": "PASS", "C": "FAIL"}, 1))
    d = fixture("crash")
    make_crash(d)
    res.append(run("crash", d, ["--bin-dir", BIN2], {"A": "PASS", "B": "FAIL", "C": "PASS"}, 1))
    d = fixture("cli-true")
    set_toml(d, "false")
    edit_json(d, lambda rj: rj["args"].append("--native_settings_frontend=true"))
    res.append(run("cli-true", d, ["--bin-dir", BIN2], {"A": "PASS", "B": "PASS", "C": "PASS"}, 0))
    d = fixture("cli-false")
    edit_json(d, lambda rj: rj["args"].append("--native_settings_frontend=false"))
    res.append(run("cli-false", d, ["--bin-dir", BIN2], {"A": "FAIL", "B": "PASS", "C": "PASS"}, 1))
    print("%d/%d cases OK" % (sum(res), len(res)))
    return 0 if all(res) else 1


if __name__ == "__main__":
    sys.exit(main())

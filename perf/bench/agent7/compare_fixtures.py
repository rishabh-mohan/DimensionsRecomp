"""Compare stale-fixture failures between two run_tests.ps1 tags (default baseline vs after).

PowerShell wraps native stderr at the console width, and the tag changes path
lengths, so logs are compared after joining lines: every compiler diagnostic
(file basename, line, column, kind, first 60 message characters), Python
exception names and "N errors generated" totals must match exactly.
"""
import difflib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2] / "build" / "agent7"
base_tag = sys.argv[1] if len(sys.argv) > 1 else "baseline"
new_tag = sys.argv[2] if len(sys.argv) > 2 else "after"
DIAG = re.compile(r"([\w\-]+\.(?:cpp|cc|h|hpp|inl)):(\d+):(\d+): (fatal error|error|warning): (.{0,60})")
EXC = re.compile(r"\b(\w+(?:Error|Exception))\b")
TOTAL = re.compile(r"(\d+) errors? generated|(\d+) warnings? and (\d+) errors? generated")


def facts(tag, name):
    log = ROOT / f"tests-{tag}" / name / "run.log"
    if not log.exists():
        return None
    text = log.read_text(errors="replace").replace("\r", "").replace("\n", "")
    text = text.replace(f"tests-{tag}", "tests-TAG")
    text = re.sub(r"\s+", " ", text)
    diags = [f"{m[0]}:{m[1]}:{m[2]}: {m[3]}: {m[4]}" for m in DIAG.findall(text)]
    excs = sorted(set(EXC.findall(text)) - {"NativeCommandError"})
    totals = ["".join(t) for t in TOTAL.findall(text)]
    passes = [p for p in re.findall(r"PASS[^|]{0,40}", text)]
    return diags + ["exceptions: " + ",".join(excs)] + ["totals: " + ";".join(totals)] + ["pass: " + str(len(passes))]


def exit_codes(tag):
    codes = {}
    for line in (ROOT / f"tests-{tag}" / "summary.txt").read_text().splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1].startswith("exit="):
            codes[parts[0]] = parts[1]
    return codes


base, new = exit_codes(base_tag), exit_codes(new_tag)
bad = 0
for name, code in base.items():
    stem = name.rsplit(".", 1)[0]
    a, b = facts(base_tag, stem), facts(new_tag, stem)
    same = a == b
    if new.get(name) != code or not same:
        bad += 1
    print(f"{name:34} {code:7} -> {new.get(name, 'missing'):7} diagnostics {'same' if same else 'DIFFERENT'}"
          f" ({max(len(a or []) - 3, 0)} compiler diagnostics)")
    if not same:
        for line in difflib.unified_diff(a or [], b or [], base_tag, new_tag, lineterm="", n=0):
            print("    " + line[:200])
print("RESULT:", "no change against baseline" if not bad else f"{bad} fixture(s) changed")
sys.exit(1 if bad else 0)

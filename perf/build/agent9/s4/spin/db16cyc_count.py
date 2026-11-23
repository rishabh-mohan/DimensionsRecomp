# db16cyc_count.py -- Agent 9, task #32 extra (07:3x). Read-only, 1 thread.
# Counts the SMT/delay hint sites in the A tree's generated source (the codegen emits only a comment for them,
# src/codegen/builders/system.cpp:51-73), grouped by function. Input: one tree root; output: a text report.
import os, re, sys, collections

root = sys.argv[1]
out = sys.argv[2]
pat_hint = re.compile(rb"^\t// (db\d+cyc|cctp[lmh])\b")
pat_func = re.compile(rb"^DEFINE_REX_FUNC\((sub_[0-9A-Fa-f]{8}|[A-Za-z_][A-Za-z0-9_]*)\)")
pat_bdnz = re.compile(rb"^\t// bdnz ")

totals = collections.Counter()
per_func = collections.defaultdict(collections.Counter)
where = {}
files = sorted(f for f in os.listdir(root) if f.endswith(".cpp"))
nbytes = 0
for fn in files:
    with open(os.path.join(root, fn), "rb") as f:
        data = f.read()
    nbytes += len(data)
    if b"cyc " not in data and b"// cctp" not in data:
        continue
    func = None
    prev_db = False
    for ln, line in enumerate(data.split(b"\n"), 1):
        m = pat_func.match(line)
        if m:
            func = m.group(1).decode()
            where.setdefault(func, "%s:%d" % (fn.replace("legodimensions_recomp.", "TU").replace(".cpp", ""), ln))
            prev_db = False
            continue
        m = pat_hint.match(line)
        if m:
            k = m.group(1).decode()
            totals[k] += 1
            per_func[func][k] += 1
            if k.startswith("db") and not prev_db:
                totals["db_runs"] += 1
                per_func[func]["db_runs"] += 1
            prev_db = k.startswith("db")
            continue
        if prev_db and pat_bdnz.match(line):
            totals["db_runs_then_bdnz"] += 1
            per_func[func]["db_runs_then_bdnz"] += 1
        if line.startswith(b"\t// "):
            prev_db = False

lines = []
lines.append("A tree: %s (%d .cpp files, %d bytes read)" % (root, len(files), nbytes))
lines.append("Totals: " + ", ".join("%s %d" % (k, totals[k]) for k in sorted(totals)))
lines.append("Functions with any hint: %d; with db*cyc: %d" % (
    len(per_func), sum(1 for c in per_func.values() if any(k.startswith("db") and k != "db_runs" and
                                                           k != "db_runs_then_bdnz" for k in c))))
lines.append("")
lines.append("function      first-line   " + "  ".join(["db16", "dbN(other)", "runs", "runs+bdnz", "cctpl", "cctpm",
                                                       "cctph"]))
def key(item):
    c = item[1]
    return -sum(v for k, v in c.items() if k.startswith("db") and k[2:3].isdigit())
for func, c in sorted(per_func.items(), key=key):
    other = sum(v for k, v in c.items() if re.match(r"db\d+cyc$", k) and k != "db16cyc")
    lines.append("%-13s %-12s %4d  %10d  %4d  %9d  %5d  %5d  %5d" % (
        func, where.get(func, "?"), c["db16cyc"], other, c["db_runs"], c["db_runs_then_bdnz"], c["cctpl"],
        c["cctpm"], c["cctph"]))
with open(out, "w", newline="\n", encoding="ascii") as f:
    f.write("\n".join(lines) + "\n")
print("\n".join(lines[:4]))
print("functions listed:", len(per_func), "-> " + out)

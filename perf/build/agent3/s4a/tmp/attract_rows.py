"""Agent 3 S4a: perf.csv row numbers (1-based data rows = S4 frame numbers) for attract-report landmarks."""
import csv, sys

run = sys.argv[1]
rows = []
with open(run + r"\perf.csv", newline="") as f:
    rd = csv.reader(f)
    hdr = next(rd)
    for r in rd:
        if len(r) < 5:
            continue
        try:
            rows.append((int(r[0]), int(r[2]), int(r[4])))
        except ValueError:
            continue
# perf s of row i = sum of frame times of rows before i (a frame's time is its start)
t = [0.0]
for ft, _, _ in rows:
    t.append(t[-1] + ft / 1e6)

def first(sig, start=0):
    d, v = sig
    for i in range(start, len(rows)):
        if rows[i][1] == d and rows[i][2] == v:
            return i
    return None

fe = first((220, 534))
ex = first((220, 540), fe) if fe is not None else None
a0 = first((218, 222), ex) if ex is not None else None
h0 = first((2823, 366575), a0) if a0 is not None else None
print("rows", len(rows), "perf_s_total %.2f" % t[len(rows)])
for name, i in (("front_end", fe), ("EXIT", ex), ("A0", a0), ("H0", h0)):
    print("%-9s row %s perf %.2f" % (name, (i + 1) if i is not None else None, t[i] if i is not None else float("nan")))
if h0 is not None:
    end = t[h0] + 150.0
    j = next((k for k in range(h0, len(rows)) if t[k] >= end), None)
    print("H0+150s  row %s perf %.2f" % ((j + 1) if j is not None else "past end", t[j] if j is not None else t[len(rows)]))

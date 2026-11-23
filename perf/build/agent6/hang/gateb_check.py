"""gateb_check.py -- read-only (Agent 6, 22:55, after Agent 12's 22:51 note): context for gate B's STUCK-LOCK.

1) Agent 2's snap1-on native build (-j 8, 20:53:30-22:39:52 per build/agent2/snap4b-steps.txt L20-21):
   from .ninja_log (last invocation), the edges running at probe times and the mean number of running
   edges per minute from 22:00 to the end.
2) gate B game.log: slow-frame lines >= 100 ms and every warning/error/critical line in 22:25:50-22:26:45.
Usage: python -B build/agent6/hang/gateb_check.py      (reads only; writes nothing)
"""
import datetime as dt
import os
import re

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
NINJA = os.path.join(WS, "build", "agent2", "snap1-on", ".ninja_log")
RUN = os.path.join(WS, "build", "agent3", "runs", "20261122-222313-w6-gateB-p2fc-level")
DAY = dt.date(2026, 11, 22)
BEGIN = dt.datetime.combine(DAY, dt.time(20, 53, 30))
END = dt.datetime.combine(DAY, dt.time(22, 39, 52))
PROBES = ["22:23:13", "22:25:50", "22:26:01", "22:26:24", "22:26:29", "22:26:31", "22:30:41"]
LO, HI = "22:25:50", "22:26:45"


def at(hms):
    h, m, s = map(int, hms.split(":"))
    return dt.datetime.combine(DAY, dt.time(h, m, s))


def ninja():
    segs, cur, last = [], [], -1
    with open(NINJA, encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("#"):
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) < 4:
                continue
            try:
                s, e = int(p[0]), int(p[1])
            except ValueError:
                continue
            if e < last and cur:
                segs.append(cur)
                cur = []
            cur.append((s, e, p[3]))
            last = e
    if cur:
        segs.append(cur)
    seg = segs[-1]
    mx = max(e for _, e, _ in seg)
    mn = min(s for s, _, _ in seg)
    base = END - dt.timedelta(milliseconds=mx)
    print(f"== .ninja_log: {len(segs)} segment(s) (split where end_ms drops); last: {len(seg)} edges, "
          f"min start {mn / 1000:.1f} s, max end {mx / 1000:.1f} s")
    print(f"   time base = END - max end = {base.time()} (BEGIN stamp {BEGIN.time()}, diff "
          f"{(base - BEGIN).total_seconds():+.1f} s)")
    for pr in PROBES:
        ms = (at(pr) - base).total_seconds() * 1000
        act = sorted(x for x in seg if x[0] <= ms <= x[1])
        print(f"   {pr} (t+{ms / 1000:.0f} s): {len(act)} edge(s) running")
        for s0, e0, n in act[:10]:
            print(f"      {s0 / 1000:8.1f}-{e0 / 1000:8.1f} s ({(e0 - s0) / 1000:7.1f} s)  {n[-100:]}")
    print("   mean running edges per minute (local start of minute):")
    t = at("22:00:00")
    row = []
    while t < END:
        a = (t - base).total_seconds() * 1000
        b = a + 60000
        busy = sum(max(0, min(e0, b) - max(s0, a)) for s0, e0, _ in seg) / 60000
        row.append(f"{t.strftime('%H:%M')} {busy:4.1f}")
        t += dt.timedelta(minutes=1)
    for i in range(0, len(row), 8):
        print("     " + " | ".join(row[i:i + 8]))


TS = re.compile(r"^\[\d{4}-\d\d-\d\d (\d\d:\d\d:\d\d)\.\d+\] \[(\w+)\]")
SF = re.compile(r"slow frame #\d+: ([\d.]+) ms")


def log():
    print(f"== gate B game.log, {LO}-{HI}: slow-frame lines >= 100 ms, and warning/error/critical lines")
    n_sf = 0
    with open(os.path.join(RUN, "game.log"), encoding="utf-8", errors="replace") as f:
        for line in f:
            m = TS.match(line)
            if not m or not (LO <= m.group(1) <= HI):
                continue
            if "slow frame #" in line:
                n_sf += 1
                x = SF.search(line)
                if x and float(x.group(1)) >= 100:
                    print("   " + line.rstrip()[:420])
            elif m.group(2) in ("warning", "error", "critical"):
                print("   " + line.rstrip()[:420])
    print(f"   ({n_sf} slow-frame lines in the window)")


if __name__ == "__main__":
    ninja()
    log()

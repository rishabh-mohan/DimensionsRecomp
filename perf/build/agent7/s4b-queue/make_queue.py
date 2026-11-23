#!/usr/bin/env python3
"""Agent 7, task #19: write queue-s4b.jsonl (Agent 3's queue.jsonl format) for the S4b agent rows,
then cross-check it against the table in QUEUE.md. It writes only queue-s4b.jsonl. Run with python -B."""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
QUEUE_MD = HERE / "QUEUE.md"
OUT = HERE / "queue-s4b.jsonl"
PRESENT = HERE.parents[2] / "perf-notes" / "agent7-present.md"

# scenario -> (est s, args before -Tag, args after -Tag)
SCEN = {
    "M": (265, ["-Seconds", "420"], ["-InputScript", "harness\\routes\\b-gate-menus-long.txt"]),
    "A": (440, ["-Seconds", "420", "-StatsWarmup", "20"], ["-InputScript", "harness\\routes\\attract-long.txt"]),
    "B90": (115, ["-Seconds", "90"], []),
    "T180": (205, ["-Seconds", "180", "-StatsWarmup", "20"], []),
}
READY = {
    "<S4B-OFF>": "ready-s4b-off",
    "<S4B-NAT>": "ready-s4b-nat",
    "<S4B-CTR>": "ready-s4b-ctr",
    "<S4B-CG26>": "ready-s4b-cg26",
}
C1 = "physical_protect_hold_global_lock=true;physical_protect_keep_watch=true"
ROWS = [  # (row, tag, bin, cvars, env, scenario): the agent rows of QUEUE.md
    (1, "off", "<S4B-OFF>", "", "", "M"),
    (2, "off-nat", "<S4B-NAT>", "native_settings_frontend=false", "", "M"),
    (3, "off-attract", "<S4B-OFF>", "", "", "A"),
    (4, "c1v", "<S4B-OFF>", C1 + ";physical_protect_keep_watch_verify=true", "", "M"),
    (5, "c1-nat", "<S4B-NAT>", "native_settings_frontend=false;" + C1, "", "M"),
    (6, "c1-warn", "<S4B-OFF>", "physical_protect_keep_watch=true", "", "B90"),
    (8, "p2c-attract", "<S4B-OFF>", "shared_memory_single_hold_rearm=true;slow_frame_log_ms=1", "", "A"),
    (9, "ctr", "<S4B-CTR>", "", "", "M"),
    (10, "r1-n", "<S4B-OFF>", "d3d12_submit_split_kb=<N>", "", "M"),
    (11, "r1-16", "<S4B-OFF>", "d3d12_submit_split_kb=16", "", "M"),
    (12, "r1-attract", "<S4B-OFF>", "d3d12_submit_split_kb=<N>", "", "A"),
    (13, "r1-rbme", "<S4B-OFF>", "d3d12_submit_split_kb=<N>;d3d12_readback_memexport=true", "", "M"),
    (14, "dbg-off", "<S4B-OFF>", "d3d12_debug=true", "", "M"),
    (15, "dbg-r1", "<S4B-OFF>", "d3d12_debug=true;d3d12_submit_split_kb=<N>", "", "M"),
    (16, "ctr-r1", "<S4B-CTR>", "d3d12_submit_split_kb=<N>", "", "M"),
    (17, "gw-p1", "<S4B-OFF>", "", "LEGO_GPU_WAIT_STATS=1", "A"),
    (18, "gw-q250", "<S4B-OFF>", "", "LEGO_GPU_WAIT_BACKOFF_US=250;LEGO_GPU_WAIT_STATS=1", "M"),
    (19, "m1", "<S4B-OFF>", "shared_memory_upload_nontemporal_copy=true", "", "M"),
    (21, "cg26", "<S4B-CG26>", "", "", "M"),
    (22, "w6-p2fi", "<S4B-OFF>", "shared_memory_single_hold_rearm=true;physical_protect_hold_global_lock=true", "", "M"),
    (24, "w6-c1", "<S4B-OFF>", "shared_memory_single_hold_rearm=true;" + C1, "", "M"),
    (25, "w7-r1-title", "<S4B-OFF>", "d3d12_submit_split_kb=<N>;framerate_limit=0", "", "T180"),
]
USER_ROWS = {7, 20, 23}
OPTIONAL_ROWS = {26}
SUBSET = [1, 4, 10, 8, 2, 5]
CONDITIONAL = {14, 15, 19, 21}  # debug layer, M1 bench, #26-ON bin
GAP_S = 10


def entry(row, tag, binp, cvars, env, scen):
    est, head, tail = SCEN[scen]
    args = ["-BinDir", binp] + head + ["-Tag", f"s4b-{row:02d}-{tag}"] + tail
    if cvars:
        args += ["-Cvar", cvars]
    if env:
        args += ["-Env", env]
    needs = "build\\agent3\\s4b\\" + ("ready-N" if "<N>" in cvars else READY[binp])
    return {"id": f"s4b{row:02d}", "est": est, "needs": needs, "args": args}


def table_rows(text):
    rows = {}
    for line in text.split("\n"):
        m = re.match(r"^\| (\d+) \| ", line)
        if m:
            rows[int(m.group(1))] = [c.strip() for c in line.strip()[1:-1].split(" | ")]
    return rows


def main():
    fails = []
    lines = ["# Agent 7 S4b queue draft (task #19), Agent 3's queue.jsonl format, written by make_queue.py. "
             "Replace each <S4B-*> with Agent 2's bin folder and <N> with the split size before running. "
             "Rows 7, 20, 23 (user, level load) and 26 (optional) are in QUEUE.md only."]
    lines += [json.dumps(entry(*r), separators=(",", ":")) for r in ROWS]
    OUT.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))

    # 1. the jsonl parses back, one entry per agent row, the S4a keys only
    back = [json.loads(s) for s in OUT.read_text(encoding="utf-8").split("\n") if s and not s.startswith("#")]
    if len(back) != len(ROWS) or any(set(e) != {"id", "est", "needs", "args"} for e in back):
        fails.append("jsonl round trip")

    # 2. the table: rows 1..26 in order, 8 cells each, and every agent row as in ROWS
    rows = table_rows(QUEUE_MD.read_text(encoding="utf-8"))
    if sorted(rows) != list(range(1, 27)):
        fails.append(f"table row numbers {sorted(rows)}")
    bad = [n for n, c in rows.items() if len(c) != 8]
    if bad:
        fails.append(f"rows without 8 cells: {bad}")
    for row, tag, binp, cvars, env, scen in ROWS:
        c = rows.get(row, [""] * 8)
        want_cv = f"`{cvars}`" if cvars else (f"`-Env {env}`" if env else None)
        if c[2] != f"`{binp}`":
            fails.append(f"row {row} bin {c[2]!r}")
        if (want_cv and c[3] != want_cv) or (not want_cv and not c[3].startswith("none")):
            fails.append(f"row {row} cvars {c[3]!r}")
        if not c[4].startswith(f"{scen} ({SCEN[scen][0]})"):
            fails.append(f"row {row} scenario {c[4]!r}")
    for n, c in rows.items():
        if c[7] != ("**yes**" if n in USER_ROWS else "no"):
            fails.append(f"row {n} user {c[7]!r}")
        if n in USER_ROWS and not c[4].startswith("L ("):
            fails.append(f"row {n} user row without L")
    agent = {r[0] for r in ROWS}
    if agent | USER_ROWS | OPTIONAL_ROWS != set(rows) or agent & USER_ROWS:
        fails.append("agent/user/optional rows don't cover the table")

    # 3. the totals quoted in QUEUE.md
    est = {r[0]: SCEN[r[5]][0] for r in ROWS}
    tot_s = sum(est.values())
    wall_min = (tot_s + GAP_S * len(est)) / 60
    sub_min = (sum(est[n] for n in SUBSET) + GAP_S * len(SUBSET)) / 60
    cond = {n: s for n, s in est.items() if n not in CONDITIONAL}
    cond_min = (sum(cond.values()) + GAP_S * len(cond)) / 60
    readers = {}
    for n, c in rows.items():
        if n in OPTIONAL_ROWS:
            continue
        for who, mins in re.findall(r"(A\d+) (\d+)", c[6]):
            readers[who] = readers.get(who, 0) + int(mins)
    owners = sum(v for k, v in readers.items() if k != "A3")
    print(f"agent runs {len(est)}, est {tot_s} s, with gaps {wall_min:.1f} min; user runs {len(USER_ROWS)}; "
          f"subset {SUBSET} {sub_min:.1f} min; without conditional rows {len(cond)} runs {cond_min:.1f} min")
    print(f"readers (rows 1-25): {dict(sorted(readers.items()))}, owners {owners}")
    expect = (len(est) == 22 and tot_s == 6320 and round(wall_min) == 109 and round(sub_min) == 30
              and len(cond) == 18 and round(cond_min) == 91 and readers.get("A3") == 73 and owners == 68)
    if not expect:
        fails.append("totals differ from the ones quoted in QUEUE.md")

    # 4. LF only and no BOM in the files of this task
    for p in (QUEUE_MD, OUT, PRESENT, pathlib.Path(__file__)):
        b = p.read_bytes()
        if b.count(b"\r") or b.startswith(b"\xef\xbb\xbf"):
            fails.append(f"{p.name}: CR or BOM")
    print(f"QUEUE.md table rows {len(rows)}; jsonl entries {len(back)}")
    print("RESULT", "PASS" if not fails else "FAIL: " + "; ".join(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

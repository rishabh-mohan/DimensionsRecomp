# Compare staged sys_summary.py vs the original on existing sys.csv files (window epochs from each run's sys.json).
import json, os, subprocess, sys
WS = r"<workspace>"
ORIG = os.path.join(WS, r"bench\agent8\run\sys_summary.py")
NEW = os.path.join(WS, r"build\agent8\session3\staged\sys_summary.py")
OUT = os.path.join(WS, r"build\agent8\session3\staged\test\old")
NEW_KEYS = ["nongame_rows", "nongame_cores_mean", "nongame_cores_max", "nongame_ge_thr_share", "game_cores_mean",
            "disk_MBps_mean", "disk_MBps_max", "proc_rows", "proc_nongame_cores_mean", "nongame_io_MBps_mean",
            "nongame_io_MBps_max", "top_cpu_procs", "top_io_procs"]
os.makedirs(OUT, exist_ok=True)
ok = True
for run in sys.argv[1:]:
    sj = json.load(open(os.path.join(run, "sys.json"), encoding="utf-8"))
    s, e = str(sj["window_start_epoch"]), str(sj["window_end_epoch"])
    name = os.path.basename(run)
    res = {}
    for tag, script in (("orig", ORIG), ("new", NEW)):
        o = os.path.join(OUT, "%s.%s.json" % (name, tag))
        p = subprocess.run([sys.executable, script, "--csv", os.path.join(run, "sys.csv"), "--start-epoch", s,
                            "--end-epoch", e, "--out", o], capture_output=True, text=True)
        res[tag] = (p.returncode, p.stdout.strip(), json.load(open(o, encoding="utf-8")))
    (co, lo, jo), (cn, ln, jn) = res["orig"], res["new"]
    for d in (jo, jn):
        d.pop("csv", None)
    # expected differences: new keys (null), nongame_thr, file.proc_columns
    extra_top = sorted(set(jn) - set(jo))
    extra_w = sorted(set(jn["window"]) - set(jo["window"]))
    extra_f = sorted(set(jn["file"]) - set(jo["file"]))
    same = True
    for k in jo:
        if k in ("window", "run", "file"):
            for kk in jo[k]:
                if jo[k][kk] != jn[k].get(kk):
                    same = False; print("  DIFF", k, kk, jo[k][kk], jn[k].get(kk))
        elif jo[k] != jn[k]:
            same = False; print("  DIFF", k, jo[k], jn[k])
    nulls = all(jn["window"][k] is None for k in NEW_KEYS) and all(jn["run"][k] is None for k in NEW_KEYS)
    print("%s: exit orig %d new %d; summary line identical %s; orig keys identical %s; new top keys %s; new window keys %d all null %s; file extra %s (proc_columns=%s); flags orig %s new %s; old sys.json flags %s"
          % (name, co, cn, lo == ln, same, extra_top, len(extra_w), nulls, extra_f, jn["file"]["proc_columns"], jo["flags"], jn["flags"], sj["flags"]))
    ok = ok and co == 0 and cn == 0 and lo == ln and same and nulls and set(extra_w) == set(NEW_KEYS)
print("ALL OK" if ok else "MISMATCH")

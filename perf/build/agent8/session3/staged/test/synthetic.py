# Synthetic sys.csv with the new per-process columns -> run the staged sys_summary.py and check keys / flag.
import json, os, subprocess, sys
WS = r"<workspace>"
NEW = os.path.join(WS, r"build\agent8\session3\staged\sys_summary.py")
D = os.path.join(WS, r"build\agent8\session3\staged\test")
sys.path.insert(0, os.path.dirname(NEW))
import sys_summary as ss

base = ("{t:.3f},{ep:.3f},03:30:{s:02d}.000,{idle:.3f},111,1,1,Default,0,40.00,100.00,1700,1700,1800,1600,40.00,40.00,,,1,0,100,"
        "Balanced,best_performance")
hdr = ",".join(ss.ALL_COLUMNS)
E0 = 1795600000.0
rows = []
for k in range(60):
    t = 1.0 + k
    # nongame: 1.0 except seconds 20..39 = 4.0 (a load episode); proc snapshot every 5th row
    ng = 4.0 if 20 <= k < 40 else 1.0
    cells = [base.format(t=t, ep=E0 + k, s=k % 60, idle=100.0 + k), "%.3f" % ng, "2.100"]
    if k % 5 == 0:
        topc = "MsMpEng.exe:6368:%.3f;svchost.exe:4452:0.500" % (ng - 0.6)
        topi = "SearchIndexer.exe:900:%.2f" % (50.0 if 20 <= k < 40 else 0.5)
        cells += ["%.3f" % (ng - 0.1), "%.2f" % (50.0 if 20 <= k < 40 else 0.5)]
    else:
        topc = topi = ""
        cells += ["", ""]
    cells += ["%.2f" % (40.0 if 20 <= k < 40 else 1.0), topc, topi]
    rows.append(",".join(cells))
p = os.path.join(D, "synthetic-sys.csv")
with open(p, "w", encoding="utf-8", newline="") as f:
    f.write(hdr + "\r\n" + "\r\n".join(rows) + "\r\n")


def run(s, e, extra=()):
    o = os.path.join(D, "synthetic-%d-%d.json" % (s, e))
    r = subprocess.run([sys.executable, NEW, "--csv", p, "--start-epoch", str(E0 + s), "--end-epoch", str(E0 + e), "--out", o]
                       + list(extra), capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), json.load(open(o, encoding="utf-8"))


ok = True
# A: window 20..39 (all load): mean 4.0 -> nongame_load; B: window 0..59: mean 2.0 -> no flag; C: B with --nongame-thr 1.5 -> flag
for tag, s, e, extra, want in (("A", 20, 39, (), True), ("B", 0, 59, (), False), ("C", 0, 59, ("--nongame-thr", "1.5"), True)):
    code, line, j = run(s, e, extra)
    w = j["window"]
    got = "nongame_load" in j["flags"]
    print("%s exit %d flag %s (want %s) thr %s nongame mean %s max %s share>=thr %s rows %s game %s disk %s/%s proc_rows %s proc_ng %s io %s/%s"
          % (tag, code, got, want, j["nongame_thr"], w["nongame_cores_mean"], w["nongame_cores_max"], w["nongame_ge_thr_share"],
             w["nongame_rows"], w["game_cores_mean"], w["disk_MBps_mean"], w["disk_MBps_max"], w["proc_rows"],
             w["proc_nongame_cores_mean"], w["nongame_io_MBps_mean"], w["nongame_io_MBps_max"]))
    print("   top_cpu", w["top_cpu_procs"])
    print("   top_io ", w["top_io_procs"])
    print("   line:", line[line.find("flags:"):])
    ok = ok and code == 0 and got == want and j["file"]["header_ok"] and j["file"]["proc_columns"]
# expected for A: nongame mean 4.0, share 1.0; MsMpEng core_s = 4 proc rows x 3.4 cores x 5 s = 68.0
code, line, j = run(20, 39)
w = j["window"]
ok = ok and w["nongame_cores_mean"] == 4.0 and w["nongame_ge_thr_share"] == 1.0 and w["top_cpu_procs"][0]["proc"] == "MsMpEng.exe:6368" \
    and abs(w["top_cpu_procs"][0]["core_s"] - 68.0) < 1e-6 and abs(w["top_cpu_procs"][0]["cores_mean"] - 3.4) < 1e-6
print("ALL OK" if ok else "MISMATCH")

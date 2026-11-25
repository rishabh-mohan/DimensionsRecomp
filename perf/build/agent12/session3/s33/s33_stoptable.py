import sys,os,json,glob
# s33_stoptable.py: R4 per-run table for #33 row 4 (stop1..7) from my onstop jsons + run.json + H0
sys.argv=[sys.argv[0]]
exec(open(r"build\agent12\session3\s33\s33stop_timeline.py").read().split("base=")[0])
PLAN={"s33stop1":203,"s33stop2":205,"s33stop3":153,"s33stop4":146,"s33stop5":230,"s33stop6":231,"s33stop7":192}
D=r"build\agent12\session3\s33"
print("| row | S plan | seconds_requested | exit | counts | last_miss_gap_s | misses_in_window | close_method | close s | wedge | H0 | close-H0 |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|")
for rid,S in PLAN.items():
    p=os.path.join(D,rid+".onstop.json")
    if not os.path.exists(p): continue
    o=json.load(open(p,encoding="utf-8-sig")); run=o["run"]
    j=json.load(open(os.path.join(R,run,"run.json"),encoding="utf-8-sig"))
    ex=0 if o.get("counts") else (3 if all(o.get("clean",{}).values()) else 1)
    try:
        f,ms,cc=scan(run); big=[m for m in ms if m[2]>=30]; h0=max(big,key=lambda m:m[2])[0] if big else None
    except Exception as e: h0=None; cc=None
    print("| %s | %d | %s%s | %d | %s | %s | %s | %s | %s | %s | %s | %s |"%(rid,S,j.get("seconds_requested")," OK" if j.get("seconds_requested")==S else " MISMATCH",ex,o.get("counts"),o.get("last_miss_gap_s"),o.get("misses_in_window"),j.get("close_method"),j.get("close_seconds"),o.get("watchdog_wedge_lines"),"-" if h0 is None else "%.2f"%h0,"-" if (h0 is None or cc is None) else "%.2f"%(cc-h0)))

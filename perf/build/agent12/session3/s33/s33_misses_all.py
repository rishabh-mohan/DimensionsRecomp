import sys
sys.argv=[sys.argv[0]]
exec(open(r"build\agent12\session3\s33\s33stop_timeline.py").read().split("base=")[0])
import os
runs=[d for d in sorted(os.listdir(R)) if d.startswith("20261125") and "s33" in d]
for r in runs:
    try:
        f,ms,cc=scan(r)
    except Exception as e:
        print(r,"ERR",e); continue
    t0,j=start(r)
    sel=[m for m in ms if 170<=m[0]<=235]
    print(r,"close %s"%(None if cc is None else round(cc,2)),"misses 170-235:"," ".join("%.2f(n%d)"%(m[0],m[2]) for m in sel))

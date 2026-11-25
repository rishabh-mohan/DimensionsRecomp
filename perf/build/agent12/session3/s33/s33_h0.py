import sys
sys.argv=[sys.argv[0]]
exec(open(r"build\agent12\session3\s33\s33stop_timeline.py").read().split("base=")[0])
import os
runs=[d for d in sorted(os.listdir(R)) if d.startswith("20261125") and "s33" in d]
rel={}
for r in runs:
    try:
        f,ms,cc=scan(r)
    except Exception as e:
        print(r,"ERR",e); continue
    if not ms: print(r,"no misses"); continue
    big=[m for m in ms if m[2]>=30]
    print(r,"close",None if cc is None else round(cc,2),"misses",len(ms),"big(new>=30):"," ".join("%.2f(n%d)"%(m[0],m[2]) for m in big))
    if not big: continue
    h0=max(big,key=lambda m:m[2])[0]
    w=[m for m in ms if 100<=m[0]<=140 and m[2]<30]
    print("   H0 %.2f | abs 100-140 small:"%h0," ".join("%.2f(n%d)"%(m[0],m[2]) for m in w))
    after=[m for m in ms if h0+1<=m[0]<=h0+100]
    print("   rel H0 +1..+100:"," ".join("+%.2f(n%d)"%(m[0]-h0,m[2]) for m in after))
    if cc is not None:
        last=[m for m in ms if m[0]<=cc]
        if last: print("   close at %.2f = H0+%.2f; last miss before close %.2f (gap %.3f)"%(cc,cc-h0,last[-1][0],cc-last[-1][0]))

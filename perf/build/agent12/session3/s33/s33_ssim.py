import sys
sys.argv=[sys.argv[0]]
exec(open(r"build\agent12\session3\s33\s33stop_timeline.py").read().split("base=")[0])
full=["20261125-070859-s33-basesf","20261125-071741-s33-offsf","20261125-095932-s33-onsf"]
allr=full+["20261125-100935-s33-stop1","20261125-101423-s33-stop2"]
H={};P={};CL={}
for r in allr:
    f,ms,cc=scan(r); h0=max(ms,key=lambda m:m[2])[0]; H[r]=h0; P[r]=[m[0]-h0 for m in ms]; CL[r]=cc
print("H0:",{r[-6:]:round(v,2) for r,v in H.items()})
res=[]
S=140.0
while S<=240.01:
    # A: 3 full-run patterns x 5 H0 values
    a=sum(1 for p in full for r in allr if any(S-2<=H[r]+o<=S for o in P[p]))/15.0
    # B: 5 own runs (stop runs only valid before their close)
    own=[r for r in allr if CL[r]>S]
    b=sum(1 for r in own if any(S-2<=H[r]+o<=S for o in P[r]))
    res.append((round(S,1),a,b,len(own))); S+=0.1
best=sorted(res,key=lambda x:-x[1])
print("top S by A (3 patterns x 5 H0):")
seen=[]
for s,a,b,n in best:
    if any(abs(s-x)<1.5 for x in seen): continue
    seen.append(s); print("  S %.1f  A %.0f%%  own %d/%d"%(s,a*100,b,n))
    if len(seen)>=12: break
for s0 in (152.3,192.0,230.0,231.0):
    for s,a,b,n in res:
        if abs(s-s0)<0.05: print("S %.1f A %.0f%% own %d/%d"%(s,a*100,b,n))

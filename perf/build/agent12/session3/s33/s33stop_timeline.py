import sys,os,re,json,datetime,collections
sys.path.insert(0,r"build\agent10\bgate"); import logdiff as L
R=r"build\agent3\runs"
def start(run):
    j=json.load(open(os.path.join(R,run,"run.json"),encoding="utf-8-sig"))
    return datetime.datetime.fromisoformat(j["started"][:26]), j
def logs(run):
    fs=[f for f in os.listdir(os.path.join(R,run)) if re.match(r"game(\.\d+)?\.log$",f)]
    fs.sort(key=lambda f:-int(f.split(".")[1]) if f.count(".")==2 else 0)
    return [os.path.join(R,run,f) for f in fs]
def scan(run):
    t0,_=start(run); first={}; misses=[]; close=None
    for p in logs(run):
        for ln in open(p,encoding="utf-8",errors="replace"):
            m=L.LINE.match(ln.rstrip("\r\n"))
            if not m: continue
            ts,lvl,cat,msg=m.groups()
            t=(datetime.datetime.strptime(ts[:23],"%Y-%m-%d %H:%M:%S.%f")-t0).total_seconds()
            k=(lvl,cat,L.norm(msg)); first.setdefault(k,t)
            x=re.search(r"slow frame #(\d+): ([\d.]+) ms .*new (\d+) \|",msg)
            if x and int(x.group(3))>0: misses.append((round(t,2),int(x.group(1)),int(x.group(3)),float(x.group(2))))
            if "Window closing, shutting down" in msg: close=t
    return first,misses,close
base="20261125-071741-s33-offsf"; cand="20261125-100935-s33-stop1"
fb,mb,_=scan(base); fc,mc,cc=scan(cand)
gone=[k for k in fb if k not in fc]
print("GONE",len(gone))
fam=collections.defaultdict(list)
for k in gone:
    lvl,cat,msg=k
    f=("Toypad["+re.search(r"Toypad\[(Read |Write)\]",msg).group(1)+"]") if re.search(r"Toypad\[(Read |Write)\]",msg) else "Toypad: pad mode" if re.search(r"Toypad: pad [#\d]+ mode",msg) else "slow frame" if "slow frame #" in msg else "upload hash" if re.search(r"S[#\d] upload hash",msg) else "OTHER %s [%s] %s"%(lvl,cat,msg[:90])
    fam[f].append((fb[k],lvl))
for f,v in sorted(fam.items()):
    ts=sorted(t for t,_ in v); print("%-60s x%-3d levels %s  first-in-base %.1f..%.1f s"%(f,len(v),dict(collections.Counter(l for _,l in v)),ts[0],ts[-1]))
early=[(fb[k],k) for k in gone if fb[k]<204]
print("GONE keys first appearing in base before 204 s:",len(early))
for t,k in sorted(early)[:10]: print("  %.1f %s"%(t,k))
print("cand close line at %.2f s"%cc)
def show(name,ms,lo,hi):
    sel=[m for m in ms if lo<=m[0]<=hi]
    print(name,"misses in [%d,%d] s:"%(lo,hi),len(sel)); 
    for m in sel: print("   t %.2f frame #%d new %d %.1f ms"%m)
show("offsf",mb,180,230); show("stop1",mc,180,230)

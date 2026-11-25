import sys,os,re,json,datetime
# s33_dropframes.py <run>...: slow-frame lines with new>0 or dropped draws>0, plus nearby non-slow-frame gpu lines
R=r"build\agent3\runs"
for run in sys.argv[1:]:
    rd=os.path.join(R,run); j=json.load(open(os.path.join(rd,"run.json"),encoding="utf-8-sig"))
    t0=datetime.datetime.fromisoformat(j["started"][:26])
    print("==",run,"seed copy_sha256:",[ (f["name"][-4:],f["copy_sha256"][:8],f["bytes_after"]) for f in (j.get("seed_xenos") or {}).get("files",[])])
    fs=sorted([x for x in os.listdir(rd) if re.match(r"game(\.\d+)?\.log$",x)],key=lambda x:-int(x.split(".")[1]) if x.count(".")==2 else 0)
    lines=[]
    for x in fs: lines+=open(os.path.join(rd,x),encoding="utf-8",errors="replace").read().splitlines()
    idx=[]
    for i,ln in enumerate(lines):
        m=re.search(r"slow frame #(\d+): ([\d.]+) ms",ln)
        if not m: continue
        nw=re.search(r"new (\d+)",ln); dd=re.search(r"dropped draws (\d+)",ln); fw=re.search(r"forced pipeline waits ([\d.]+) \S* ?\((\d+)",ln)
        n=int(nw.group(1)) if nw else 0; d=int(dd.group(1)) if dd else 0
        if n>0 or d>0:
            ts=datetime.datetime.strptime(ln[1:24],"%Y-%m-%d %H:%M:%S.%f"); pc=re.search(r"pipeline create ([\d.]+) \((\d+)x\)",ln)
            print("  t %.2f frame #%s %.1f ms new %d drops %d pcreate %s forced %s"%((ts-t0).total_seconds(),m.group(1),float(m.group(2)),n,d,pc.groups() if pc else None,fw.groups() if fw else None))
            idx.append(i)
    # non-slow-frame lines within +-30 lines of the miss frames, gpu category
    seen=set()
    for i in idx:
        for k in range(max(0,i-30),min(len(lines),i+5)):
            ln=lines[k]
            if k in seen or "slow frame #" in ln or "Toypad" in ln: continue
            seen.add(k); print("    ctx:",ln[:220])

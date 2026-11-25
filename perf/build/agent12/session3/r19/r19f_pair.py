import re,sys,csv,statistics as st
run=r"build\agent3\runs\20261125-094143-r19f-rbme-async-n"
ev=[]
for i,l in enumerate(open(run+r"\game.log",encoding="utf-8",errors="replace"),1):
    m=re.search(r"d3d12_submit_split: .*?splits=(\d+)",l)
    if m: ev.append((i,"S",int(m.group(1))))
    m=re.search(r"d3d12_async_submit: .*?chunks=(\d+)",l)
    if m: ev.append((i,"A",int(m.group(1))))
print("events",len(ev)); 
for e in ev[-4:]: print(e)
bad=0;ps=None;pc=None;leads=[]
for i,k,v in ev:
    if k=="S":
        if pc is not None and v<pc: bad+=1; print("BAD S",i,v,pc)
        ps=v
    else:
        if ps is not None:
            if v<ps+1: bad+=1; print("BAD A",i,v,ps)
            leads.append(v-ps)
        pc=v
print("violations",bad,"leads min/max/last",min(leads),max(leads),leads[-1])
# load profile
for name,path in (("r19f",run),("r19r13",r"build\agent3\runs\20261125-090250-r19r13-s4b13-rbme")):
    rows=list(csv.DictReader(open(path+r"\perf.csv",encoding="utf-8",errors="replace")))
    k=[c for c in rows[0] if "draw" in c.lower()][0]
    d=sorted(float(r[k]) for r in rows if r[k])
    print(name,k,"n",len(d),"med",st.median(d),"p90",d[int(0.9*(len(d)-1))],"max",max(d),">1500 %.1f%%"%(100*sum(x>1500 for x in d)/len(d)))

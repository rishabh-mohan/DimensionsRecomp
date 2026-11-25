import re
ev=[]
for i,l in enumerate(open(r"build\agent3\runs\20261125-094615-r19e-level-soak-async-n\game.log",encoding="utf-8",errors="replace"),1):
    m=re.search(r"d3d12_submit_split: frame=(\d+).*?splits=(\d+)",l)
    if m: ev.append((i,"S",int(m.group(1)),int(m.group(2))))
    m=re.search(r"d3d12_async_submit: frame=(\d+).*?chunks=(\d+)",l)
    if m: ev.append((i,"A",int(m.group(1)),int(m.group(2))))
pairs=[];j=0
while j<len(ev)-1:
    a,b=ev[j],ev[j+1]
    if a[1]!=b[1] and abs(b[0]-a[0])<=3: pairs.append((a,b)); j+=2
    else: print("unpaired",a); j+=1
order={"AS":0,"SA":0}
d=[]
for a,b in pairs:
    order[a[1]+b[1]]+=1
    A=a if a[1]=="A" else b; S=b if a[1]=="A" else a
    d.append(A[3]-S[3])
print("pairs",len(pairs),"order",order,"chunks-splits min/max",min(d),max(d),"last",d[-1],"equal",sum(x==0 for x in d))

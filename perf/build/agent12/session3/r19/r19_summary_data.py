import re,os,glob,json
R=r"build\agent3\runs"
ids=["r19r11","r19r10","r19r13","r19r15","r19r25","r19a","r19b","r19i","r19c","r19g","r19j","r19d","r19f","r19e"]
dirs=sorted(d for d in os.listdir(R) if d.startswith("20261125"))
for i in ids:
    m=[d for d in dirs if re.search(r"-%s-"%i,d+"-")]
    if not m: print(i,"NO RUN");continue
    d=m[-1]; last_a=last_s=None; ns=na=0
    for l in open(os.path.join(R,d,"game.log"),encoding="utf-8",errors="replace"):
        if "d3d12_async_submit: frame" in l: last_a=l; na+=1
        if "d3d12_submit_split: frame" in l: last_s=l; ns+=1
    def g(l,k):
        if not l: return "-"
        x=re.search(k+r"=(\d+)",l); return x.group(1) if x else "-"
    slow="?"
    for c in (os.path.join(r"build\agent3\s4b\r19\checks",d+".txt"),os.path.join(r"build\agent3\s4b\logs",i+".check.txt")):
        if os.path.exists(c):
            raw=open(c,"rb").read()
            t=raw.decode("utf-16") if raw[:2] in (b"\xff\xfe",b"\xfe\xff") else raw.decode("utf-8","replace")
            x=re.search(r"sys.csv slow state: (\{.*\})",t)
            if x: j=json.loads(x.group(1)); slow="%s E%s"%(j["slow"],j["e_eff_mhz_median"]); break
    print(i,d,"split_lines",ns,"splits",g(last_s,"splits"),"async_lines",na,"chunks",g(last_a,"chunks"),"qmax",g(last_a,"queued_max"),"full_waits",g(last_a,"full_waits"),"held_q",g(last_s,"held_query"),"slow",slow)

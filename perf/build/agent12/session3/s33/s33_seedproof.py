import sys,os,re,json,hashlib
# usage: s33_seedproof.py <run dir name> ; read-only seed proof for #33 row 5
R=r"build\agent3\runs"; SRC=r"build\agent3\runs\20261125-071741-s33-offsf\user\cache\shaders\shareable"
run=sys.argv[1]; rd=os.path.join(R,run)
def h8(p): return hashlib.sha256(open(p,"rb").read()).hexdigest()[:8].upper()
ok=True
try:
    j=json.load(open(os.path.join(rd,"run.json"),encoding="utf-8-sig"))
    sx=j.get("seed_xenos"); print("run.json seed_xenos:",json.dumps(sx)[:600])
    if not sx or not str((sx or {}).get("source_dir","")).rstrip("\\/").endswith(r"20261125-071741-s33-offsf\user\cache\shaders\shareable"): print("SEED source_dir: BAD"); ok=False
    else: print("SEED source_dir: ok")
except FileNotFoundError: print("run.json: missing (run still going?)"); ok=False
src={f:(os.path.getsize(os.path.join(SRC,f)),h8(os.path.join(SRC,f))) for f in os.listdir(SRC)}
print("source:",src)
dst=os.path.join(rd,"user","cache","shaders","shareable")
for f,(n,h) in src.items():
    p=os.path.join(dst,f)
    if not os.path.exists(p): print("run cache MISSING",f); ok=False; continue
    n2=os.path.getsize(p); h2=h8(p); pre=open(p,"rb").read(n)==open(os.path.join(SRC,f),"rb").read()
    print("run cache %s size %d (src %d) sha %s; same=%s; src is prefix=%s"%(f,n2,n,h2,h2==h,pre))
    if not pre: ok=False
logs=sorted([x for x in os.listdir(rd) if re.match(r"game(\.\d+)?\.log$",x)],key=lambda x:-int(x.split(".")[1]) if x.count(".")==2 else 0)
hits=[]
for x in logs:
    for ln in open(os.path.join(rd,x),encoding="utf-8",errors="replace"):
        if re.search(r"from the storage|Initializing shader storage",ln): hits.append(x+": "+ln.strip()[:200])
for l in hits[:6]: print(l)
m=[re.search(r"Translated (\d+) shaders from the storage",l) for l in hits]; m=[int(x.group(1)) for x in m if x]
print("storage translated:",m)
if not m or m[0]==0: ok=False
print("SEEDPROOF", "OK" if ok else "NOT OK")
sys.exit(0 if ok else 1)

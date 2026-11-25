import sys
_av=sys.argv[1:]
sys.argv=[sys.argv[0]]
exec(open(r"build\agent12\session3\s33\s33stop_timeline.py").read().split("base=")[0])
base="20261125-071741-s33-offsf"; a="20261125-101423-s33-stop2"; b="20261125-104222-s33-stop3"
if len(_av)==2: a,b=_av
fb,_,_=scan(base); fa,_,ca=scan(a); fc,_,cc=scan(b)
ga={k for k in fb if k not in fa}; gc={k for k in fb if k not in fc}
print("GONE",a[-5:],len(ga),b[-5:],len(gc))
for k in sorted(gc-ga): print("only in %s GONE: first-in-base %.1f s; in %s first at %s; %s"%(b[-5:],fb[k],a[-5:],None if k not in fa else round(fa[k],1),k))
for k in sorted(ga-gc): print("only in %s GONE: first-in-base %.1f s; in %s first at %s; %s"%(a[-5:],fb[k],b[-5:],None if k not in fc else round(fc[k],1),k))

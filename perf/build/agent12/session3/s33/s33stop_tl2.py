import sys
src=open(r"build\agent12\session3\s33\s33stop_timeline.py").read()
cand=sys.argv[1]; lim=float(sys.argv[2]) if len(sys.argv)>2 else 204
if len(sys.argv)>3: src=src.replace('base="20261125-071741-s33-offsf"','base=%r'%sys.argv[3])
src=src.replace('cand="20261125-100935-s33-stop1"','cand=%r'%cand).replace("<204",("<%s"%lim)).replace('show("stop1"','show("cand"')
sys.argv=[sys.argv[0]]
exec(src)

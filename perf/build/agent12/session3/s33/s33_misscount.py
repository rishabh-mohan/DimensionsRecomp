import sys
sys.argv=[sys.argv[0]]
exec(open(r"build\agent12\session3\s33\s33stop_timeline.py").read().split("base=")[0])
f,ms,cc=scan("20261125-102000-s33-offwarm")
print("offwarm misses",len(ms),"new total",sum(m[2] for m in ms),"max new",max([m[2] for m in ms] or [0]))
print(" ".join("%.1f(n%d)"%(m[0],m[2]) for m in ms[:40]))

import hashlib
R=r"build\agent3\runs\%s\user\cache\shaders\shareable\5752084B.rtv.d3d12.xpso"
src=open(R%"20261125-071741-s33-offsf","rb").read()
a=open(R%"20261125-102000-s33-offwarm","rb").read(); b=open(R%"20261125-103108-s33-onwarm","rb").read()
print("prefix", a[:len(src)]==src, b[:len(src)]==src, "header-region check: first 16 B equal", a[:16]==b[:16]==src[:16])
ta=a[len(src):]; tb=b[len(src):]
print("tail bytes", len(ta), len(tb), "72-B records", len(ta)/72, len(tb)/72)
ra=[ta[i:i+72] for i in range(0,len(ta),72)]; rb=[tb[i:i+72] for i in range(0,len(tb),72)]
ha=[hashlib.sha256(r).hexdigest()[:8] for r in ra]; hb=[hashlib.sha256(r).hexdigest()[:8] for r in rb]
print("offw recs", ha); print("onw  recs", hb)
print("onw subset of offw:", set(hb)<=set(ha), "only offw:", sorted(set(ha)-set(hb)), "only onw:", sorted(set(hb)-set(ha)))
# src record size sanity: does src length - header divide by 72?
print("src len", len(src), "src%72", len(src)%72)
X=r"build\agent3\runs\%s\user\cache\shaders\shareable\5752084B.xsh"
xa=open(X%"20261125-102000-s33-offwarm","rb").read(); xb=open(X%"20261125-103108-s33-onwarm","rb").read()
print("xsh identical between arms:", xa==xb, len(xa))

import sys, re, collections
def parse(p):
    for line in open(p, encoding="utf-8", errors="replace"):
        line = line.rstrip("\n"); i = line.rfind(" ")
        if i > 0: yield line[:i].split(";"), int(line[i+1:])
w = {"a": 0.077385, "b": 0.078485}
res = {}
for lab, path in (("a", sys.argv[1]), ("b", sys.argv[2])):
    c = collections.Counter(); leafc = collections.Counter()
    for fr, n in parse(path):
        k = next((j for j, f in enumerate(fr) if f.startswith("rexgpu-xenos.dll!")), None)
        if k is None: c["(no xenos frame)"] += n; continue
        j = k
        while j < len(fr) and fr[j].startswith("rexgpu-xenos.dll!"): j += 1
        last_x = fr[j-1]
        b = fr[j] if j < len(fr) else "(xenos self) " + last_x
        b = re.sub(r"\(near [^)]*\)", "", b).strip()[:90]
        c[b] += n
        leafc[re.sub(r"\(near [^)]*\)", "", fr[-1]).strip()[:70] + "  | " + b[:50]] += n
    res[lab] = (c, leafc)
print("boundary out of rexgpu-xenos.dll (first named/non-xenos frame), ms/f a | b (n)")
keys = set(res["a"][0]) | set(res["b"][0])
for k in sorted(keys, key=lambda k: -(res["a"][0][k] + res["b"][0][k])):
    na, nb = res["a"][0][k], res["b"][0][k]
    if na + nb >= 4: print(f"{na*w['a']:6.3f} {nb*w['b']:6.3f}  ({na:3d},{nb:3d})  {k}")
print()
print("leaf | boundary, ms/f a | b (n)")
keys = set(res["a"][1]) | set(res["b"][1])
for k in sorted(keys, key=lambda k: -(res["a"][1][k] + res["b"][1][k]))[:25]:
    na, nb = res["a"][1][k], res["b"][1][k]
    print(f"{na*w['a']:6.3f} {nb*w['b']:6.3f}  ({na:3d},{nb:3d})  {k}")

import csv
R=r"build\agent3\runs\\"
c=list(csv.DictReader(open(R+r"20261125-094615-r19e-level-soak-async-n\input.csv")))
b=list(csv.DictReader(open(R+r"20261122-210059-s4b-L0-off-level\input.csv")))
print("rows",len(c),len(b))
assert [r["line"] for r in c]==[r["line"] for r in b], "line seq differs"
pc=pb=0.0; acc=0.0
for rc,rb in zip(c,b):
    tc=float(rc["t_s"]);tb=float(rb["t_s"]); dc=tc-pc; db=tb-pb; pc,pb=tc,tb
    d=dc-db; acc+=d
    same = rc["result"]==rb["result"]
    if abs(d)>=1.0 or rc["cmd"] in("mark",) or not same and rc["cmd"]!="start":
        print(f'L{rc["line"]:>4} {rc["cmd"]:<16} {rc["args"][:28]:<28} cand {tc:7.2f} (+{dc:6.2f}) base {tb:7.2f} (+{db:6.2f}) d {d:+6.2f} cum {acc:+7.2f} | {rc["result"][:40]} | {rb["result"][:40] if not same else "="}')
print("last t cand",c[-1]["t_s"],"base",b[-1]["t_s"])
to_c=[r["line"] for r in c if "timeout" in r["result"].lower()]; to_b=[r["line"] for r in b if "timeout" in r["result"].lower()]
print("timeouts cand",len(to_c),"base",len(to_b),"same set",to_c==to_b, to_c[:3], to_c[-3:])

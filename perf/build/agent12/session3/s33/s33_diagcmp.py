"""Compare per-dest taint/heal tables of two arms in a diagd_report text.
usage: s33_diagcmp.py <diagd.report.txt>"""
import re, sys
arms, cur = {}, None
for ln in open(sys.argv[1], encoding='utf-8', errors='replace'):
    m = re.match(r'== run \S+\s+\(arm (\w+)\)', ln)
    if m:
        cur = arms.setdefault(m.group(1), {}); continue
    m = re.match(r'\s+([0-9A-F]{8})\s+(\d+)\s+(\d+)\s+(\d+)\s+\S+\s+([\d.]+)/([\d.]+)\s+(\w+)', ln)
    if m and cur is not None:
        cur[m.group(1)] = dict(t=int(m.group(2)), e=int(m.group(3)), h=int(m.group(4)),
                               med=float(m.group(5)), mx=float(m.group(6)), end=m.group(7))
a, b = list(arms)[:2]
A, B = arms[a], arms[b]
print(f'{a}: {len(A)} dests, eps {sum(v["e"] for v in A.values())}, heals {sum(v["h"] for v in A.values())}, not ok at end {[k for k,v in A.items() if v["end"]!="ok"]}')
print(f'{b}: {len(B)} dests, eps {sum(v["e"] for v in B.values())}, heals {sum(v["h"] for v in B.values())}, not ok at end {[k for k,v in B.items() if v["end"]!="ok"]}')
print(f'only in {b}:', ', '.join(f'{k} (eps {B[k]["e"]}, max {B[k]["mx"]:.3f}s)' for k in sorted(set(B) - set(A))) or '-')
print(f'only in {a}:', ', '.join(f'{k} (eps {A[k]["e"]}, max {A[k]["mx"]:.3f}s)' for k in sorted(set(A) - set(B))) or '-')
print(f'common dests where {b} max latency > {a} max latency:')
for k in sorted(set(A) & set(B)):
    if B[k]['mx'] > A[k]['mx']:
        print(f'   {k}: {a} {A[k]["mx"]:.3f}s (eps {A[k]["e"]}) -> {b} {B[k]["mx"]:.3f}s (eps {B[k]["e"]})')
print(f'max latency overall: {a} {max(v["mx"] for v in A.values()):.3f}s, {b} {max(v["mx"] for v in B.values()):.3f}s')
print(f'dests with max latency > 1 s: {a} ' + ', '.join(f'{k} {v["mx"]:.3f}' for k, v in A.items() if v['mx'] > 1) +
      f' | {b} ' + ', '.join(f'{k} {v["mx"]:.3f}' for k, v in B.items() if v['mx'] > 1))

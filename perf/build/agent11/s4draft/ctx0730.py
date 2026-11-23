import re, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
src = open('build/agent11/s4draft/passb.py', encoding='utf-8').read()
src = src.split('# ---------------- gate ----------------')[0]
sys.argv = ['x', 'S4', '--dry', '0000']
g = {}
exec(src, g)
docs = {'S4': open('perf-notes/S4-DRAFT.md', encoding='utf-8').read(), 'FN': open('perf-notes/FINDINGS-AND-CHANGES.md', encoding='utf-8').read()}
def lno(t, pos):
    return t.count('\n', 0, pos) + 1
for d, E in (('S4', g['S4E']), ('FN', g['FNE'])):
    t = docs[d]
    for name, old, rep in E:
        i = t.find(old)
        if i < 0:
            print('CTX %s %s: NOT FOUND' % (d, name)); continue
        print('CTX %s %s L%d: ...%s[[%s]]%s...' % (d, name, lno(t, i), t[max(0, i - 220):i].replace('\n', ' / '), old[:70].replace('\n', ' / '), t[i + len(old):i + len(old) + 120].replace('\n', ' / ')))
print('==== keyword hits')
pat = re.compile(r'still due|pending|due by|~10:00|until the (?:W9|W5b|formal|read)|W5b read-out|W5b\'s read-out|read-outs? (?:land|are due)|lean', re.I)
for d, t in docs.items():
    for m in pat.finditer(t):
        i = m.start()
        print('KW %s L%d: ...%s...' % (d, lno(t, i), t[max(0, i - 160):i + 120].replace('\n', ' / ')))
print('==== A8C gap>2')
A = open('build/agent8/readout/w-followup/a7check/W9-W5b-check.md', encoding='utf-8').read()
seen = set()
for line in A.split('\n'):
    m = re.search(r'\| DISAGREE \| ([\d.]+) \|', line)
    if m and float(m.group(1)) > 2:
        cells = [c.strip() for c in line.split('|')]
        key = tuple(c for c in cells if re.search(r'\.md L\d+', c))[:1] + (m.group(1),)
        if key not in seen:
            seen.add(key)
            print('GAP>2', line[:260])

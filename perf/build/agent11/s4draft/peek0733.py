import re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
t = open('perf-notes/S4-DRAFT.md', encoding='utf-8').read()
old = 'Agent 4 does it (run-2 task #12, since 19:42; L2730, L2744).'
i = -1
while True:
    i = t.find(old, i + 1)
    if i < 0:
        break
    print('OCC L%d: ...%s[[OLD]]%s...' % (t.count('\n', 0, i) + 1, t[max(0, i - 300):i].replace('\n', ' / '), t[i + len(old):i + len(old) + 200].replace('\n', ' / ')))
A = open('build/agent8/readout/w-followup/a7check/W9-W5b-check.md', encoding='utf-8').read().split('\n')
print('A8C lines', len(A))
for k, s in enumerate(A[:45], 1):
    print('A8C L%d: %s' % (k, s[:700]))
for s in A:
    m = re.search(r'\| DISAGREE \| ([\d.]+) \|', s)
    if m and float(m.group(1)) > 2 and not re.match(r'\| \d+ \|', s):
        print('GAP>2 ' + s[:400])

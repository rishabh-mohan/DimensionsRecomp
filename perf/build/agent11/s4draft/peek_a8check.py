import re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
p = 'build/agent8/readout/w-followup/a7check/W9-W5b-check.md'
t = open(p, 'rb').read().decode('utf-8', errors='replace')
L = re.split(r'\r\n|\n|\r', t)
print('lines', len(L))
for i, s in enumerate(L[:45]):
    print('H%d: %s' % (i + 1, s[:700]))
n = 0
for i, s in enumerate(L[45:], 46):
    if re.search(r'^#|[Vv]erdict|MISMATCH|FAIL|[Dd]isagree|[Ss]ummary', s):
        print('M%d: %s' % (i, s[:400])); n += 1
        if n > 40: print('...more'); break

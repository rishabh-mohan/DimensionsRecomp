import re, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
def rd(p):
    b = open(p, 'rb').read()
    return b.decode('utf-16') if b[:2] in (b'\xff\xfe', b'\xfe\xff') else b.decode('utf-8', errors='replace')
S2 = re.split(r'\r\n|\n|\r', rd('perf-notes/SESSION2.md'))
print('SESSION2 lines', len(S2))
for i in range(3324, len(S2)):
    print('S2 L%d: %s' % (i + 1, S2[i][:1500]))
A = re.split(r'\r\n|\n|\r', rd('build/agent8/readout/w-followup/a7check/W9-W5b-check.md'))
print('A8C lines', len(A))
for i, s in enumerate(A, 1):
    if i <= 40 or re.search(r'claims|Disagreements by gap|W5b\.md L|revis|07:2|Sign flips', s):
        if i <= 40 or not s.startswith('|'):
            print('A8C L%d: %s' % (i, s[:600]))
cnt = sum(1 for s in A if s.startswith('| W5b.md'))
print('A8C rows citing W5b.md:', cnt, ' DISAGREE rows:', sum(1 for s in A if '| DISAGREE |' in s))
for s in A:
    if '| DISAGREE |' in s and ('W5b.md' in s):
        print('  W5bDIS ' + s[:300])
for p in ['build/agent7/HANDOFF.md', 'build/agent8/HANDOFF.md', 'build/agent7/readout/W5b.md', 'build/agent5/scrnsave-fix/install-log.txt']:
    print(p, os.path.exists(p) and os.path.getsize(p))

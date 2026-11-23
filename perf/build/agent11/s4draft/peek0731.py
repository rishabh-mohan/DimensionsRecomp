import re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
def rd(p):
    b = open(p, 'rb').read()
    return b.decode('utf-16') if b[:2] in (b'\xff\xfe', b'\xfe\xff') else b.decode('utf-8', errors='replace')
R = re.split(r'\r\n|\n|\r', rd('build/agent3/f10/RESULTS.md'))
print('RESULTS lines', len(R))
for i, s in enumerate(R, 1):
    if re.search(r'never|2736|1644|C1 off|burst|worst|largest|biggest|max sync|syncs in one frame', s, re.I):
        print('R L%d: %s' % (i, s[:700]))
T = re.split(r'\r\n|\n|\r', rd('build/agent3/f10/f10-table.md'))
for i, s in enumerate(T, 1):
    if re.search(r'2736|1644|max|burst|sync', s, re.I):
        print('T L%d: %s' % (i, s[:500]))
S4 = rd('perf-notes/S4-DRAFT.md').split('\n')
for i, s in enumerate(S4, 1):
    if s.startswith('| 38 |') or s.startswith('| 24 |') or s.startswith('| 11 |'):
        print('S4 L%d: %s' % (i, s[:1600]))
FN = rd('perf-notes/FINDINGS-AND-CHANGES.md').split('\n')
for i, s in enumerate(FN, 1):
    if re.search(r'rating is pending|precise_wait|precise wait|not built', s):
        print('FN L%d: %s' % (i, s[:900]))

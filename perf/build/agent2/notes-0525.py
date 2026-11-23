"""Agent 2 - RESUME block update (05:25): Agent 10's nativeB 1b verdict. Backup first; counted replacement; LF kept.
  python build\\agent2\\notes-0525.py
"""
import hashlib
import os
import re
import shutil
import sys
import time

R = r'<workspace>'
F = os.path.join(R, 'perf-notes', 'agent2-baseline.md')
BK = os.path.join(R, 'build', 'agent2', 'notes-backup')
now = time.strftime('%H:%M')
with open(F, 'rb') as f:
    raw = f.read()
if b'\r\n' in raw:
    sys.exit('REFUSED: CRLF')
t = raw.decode('utf-8')
old = '    of the pair logs.\n'
new = ('    of the pair logs.\n'
       '  - Agent 10, nativeB 1b route pair vs native3d (05:24, codegen-review "1b verdict"): PASS. B 54/54, exit 0, no\n'
       '    errors, logdiff NEW 0 / MORE 0, slot heap and pool copy MATCH, the same 26 scene teardowns in order. Caveats:\n'
       '    the placement relocation lr=83F9B660 site is not covered (heap-layout dependent, not a diff); the front-end\n'
       '    exit came at a different press (same class as OFF pair 1). Recommends no rollback; optional reversed-order\n'
       '    tie-break pair before 08:30 if the slot has room; level-change route for both in window 4.\n')
if t.count(old) != 1:
    sys.exit('REFUSED: anchor found %d times (nothing written)' % t.count(old))
t = t.replace(old, new)
t2 = re.sub(r'\A(# Agent 2: build pipeline - RESUME NOTE \(.*?; updated )\d\d:\d\d\)', r'\g<1>%s)' % now, t, count=1)
if t2 == t:
    sys.exit('REFUSED: header time not updated (nothing written)')
bk = os.path.join(BK, 'agent2-baseline.md.' + time.strftime('%H%M%S'))
shutil.copy2(F, bk)
b = t2.encode('utf-8')
with open(F, 'wb') as f:
    f.write(b)
print('backup %s; wrote %d B, sha256 %s, CRLF %d' % (bk, len(b), hashlib.sha256(b).hexdigest()[:16].upper(),
                                                    b.count(b'\r\n')))

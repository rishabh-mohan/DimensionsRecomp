"""Agent 2 - 05:56: RESUME block: Agent 1's 05:55 reminder (06:33-07:15 Agent 8's attract scenes need an idle
machine: no builds or compiles, no recursive searches, no reads over ~100 MB, batched tool calls, 1 thread).
Counted replacements, backup first, LF kept."""
import hashlib
import os
import re
import shutil
import sys
import time

R = r'<workspace>'
NOTES = os.path.join(R, 'perf-notes', 'agent2-baseline.md')
A = ("of the SDK, DimensionsRecomp or build trees; targeted reads only, <= 2 threads. No builds\n"
     "or game runs from 08:30")
B = ("of the SDK, DimensionsRecomp or build trees; targeted reads only, <= 2 threads. Agent 1 (05:55): 06:33-07:15 are\n"
     "Agent 8's attract scenes on an idle machine: no builds or compiles, no recursive searches, no reads over ~100 MB,\n"
     "batched tool calls, 1 thread (I have nothing pending). No builds\n"
     "or game runs from 08:30")
raw = open(NOTES, 'rb').read()
if b'\r\n' in raw:
    sys.exit('REFUSED: CRLF')
t = raw.decode('utf-8')
if t.count(A) != 1:
    sys.exit('REFUSED: span found %d times (nothing written)' % t.count(A))
t = t.replace(A, B)
t, n = re.subn(r'\A(# Agent 2: build pipeline - RESUME NOTE \(.*?; updated )\d\d:\d\d\)',
               r'\g<1>%s)' % time.strftime('%H:%M'), t)
if n != 1:
    sys.exit('REFUSED: header not found (nothing written)')
bk = os.path.join(R, 'build', 'agent2', 'notes-backup', 'agent2-baseline.md.' + time.strftime('%H%M%S'))
shutil.copy2(NOTES, bk)
b = t.encode('utf-8')
open(NOTES, 'wb').write(b)
print('notes updated (backup %s): %d B, sha256 %s, LF only: %s'
      % (os.path.basename(bk), len(b), hashlib.sha256(b).hexdigest()[:16].upper(), b'\r\n' not in b))
print(t.split('\n')[0])
print('\n'.join(t.split('\n')[12:16]))

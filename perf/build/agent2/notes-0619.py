"""Agent 2 - 06:19: RESUME block: Agent 8's build all-clear moves later (#25 base 06:33 to ~06:52, q to ~07:15 if
its gate passes, maybe Agent 5's a-vol; hard end 07:30; Agent 8 messages me when the last run ends).
Counted replacement, backup first, LF kept."""
import hashlib
import os
import re
import shutil
import sys
import time

R = r'<workspace>'
NOTES = os.path.join(R, 'perf-notes', 'agent2-baseline.md')
A = ("maybe an attract re-run; Agent 8 sends the build all-clear about 06:50 (it gives a gap between runs if a build gets\n"
     "a GO first).")
B = ("maybe an attract re-run; then (Agent 8, 06:19) #25 base 06:33 to ~06:52, q to ~07:15 if its gate passes, maybe\n"
     "Agent 5's a-vol; hard end 07:30. Agent 8 messages me when the last run ends (the build all-clear), and gives a gap\n"
     "between runs if a build gets a GO first.")
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
print('\n'.join(t.split('\n')[9:13]))

"""Agent 2 - 06:20: RESUME block: re-wrap the long 05:31/05:55 lines and add Agent 10's 06:19 1b tie-break result
(every must-match item passes again; only the front-end exit timing is reopened, not a fail item, no rollback;
Agent 1 picks a/b/c). Span replacement with unique anchors, backup first, LF kept."""
import hashlib
import os
import re
import shutil
import sys
import time

R = r'<workspace>'
NOTES = os.path.join(R, 'perf-notes', 'agent2-baseline.md')
START = 'between runs if a build gets a GO first. Agent 1 (05:31)'
STOP = 'batched tool calls, 1 thread (I have nothing pending). No builds'
NEW = ("between runs if a build gets a GO first. Agent 1 (05:31): while a game runs (Agent 8's queue until\n"
       "about 07:15), no recursive searches or scans of the SDK, DimensionsRecomp or build trees; targeted reads\n"
       "only, <= 2 threads. Agent 1 (05:55): 06:33-07:15 are Agent 8's attract scenes on an idle machine: no builds or\n"
       "compiles, no recursive searches, no reads over ~100 MB, batched tool calls, 1 thread (I have nothing pending).\n"
       "Agent 10 (06:19): the reversed-order 1b tie-break passes every must-match item again; only the front-end exit\n"
       "timing is reopened (nativeB leaves ~12 s earlier on native; not a fail item, no rollback); Agent 1 picks (a)\n"
       "accept, (b) diff the fade code's codegen snap1 vs snapB3, or (c) more runs. No builds")
raw = open(NOTES, 'rb').read()
if b'\r\n' in raw:
    sys.exit('REFUSED: CRLF')
t = raw.decode('utf-8')
if t.count(START) != 1 or t.count(STOP) != 1:
    sys.exit('REFUSED: anchors found %d / %d times (nothing written)' % (t.count(START), t.count(STOP)))
i = t.index(START)
j = t.index(STOP, i) + len(STOP)
if j - i > 700:
    sys.exit('REFUSED: span is %d chars (nothing written)' % (j - i))
t = t[:i] + NEW + t[j:]
t, n = re.subn(r'\A(# Agent 2: build pipeline - RESUME NOTE \(.*?; updated )\d\d:\d\d\)',
               r'\g<1>%s)' % time.strftime('%H:%M'), t)
if n != 1:
    sys.exit('REFUSED: header not found (nothing written)')
bk = os.path.join(R, 'build', 'agent2', 'notes-backup', 'agent2-baseline.md.' + time.strftime('%H%M%S'))
shutil.copy2(NOTES, bk)
b = t.encode('utf-8')
open(NOTES, 'wb').write(b)
L = t.split('\n')
print('notes updated (backup %s): %d B, sha256 %s, LF only: %s, longest of lines 1-30: %d'
      % (os.path.basename(bk), len(b), hashlib.sha256(b).hexdigest()[:16].upper(), b'\r\n' not in b,
         max(len(x) for x in L[:30])))
print(L[0])
print('\n'.join(L[9:20]))

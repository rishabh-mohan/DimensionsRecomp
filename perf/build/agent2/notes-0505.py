"""Agent 2 - RESUME block update (05:05): Agent 9's OK of the S3e clones. Backup first; counted replacements; LF kept.
  python build\\agent2\\notes-0505.py
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
pairs = [
    ('It is prepared, not built (S3e section below; Agent 9 reviews the diffs).',
     'It is prepared, not built (S3e section below; Agent 9 OK at 05:00).'),
    ('  S3e-notes.txt: exit 4 before any build (log moved to `rbt-logs/test-snap3e-run.txt`). stop-snap.ps1 was not run.\n',
     '  S3e-notes.txt: exit 4 before any build (log moved to `rbt-logs/test-snap3e-run.txt`). stop-snap.ps1 was not run.\n'
     '- Agent 9 (05:00): OK, no objections (`perf-notes/agent9-codegen.md` S4.0). Hashes rechecked; make-s3e-clones.py\n'
     '  A16E05AD rerun in a scratch copy gives all 7 outputs byte for byte; every changed line checked; the guard matches\n'
     '  all 10 sample driver names and not itself; with the live hash faked in-process the dry run is 9/9 (rules and\n'
     '  notes 4 lines each, nothing written). Cosmetic nit: the stop-snap.ps1 comment says "04:5x"; left as is, so the\n'
     '  reviewed hash 705233E5 stays.\n'),
]
for old, new in pairs:
    if t.count(old) != 1:
        sys.exit('REFUSED: anchor found %d times: %s (nothing written)' % (t.count(old), old[:50]))
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

"""Agent 2 - RESUME block update (05:07): Agent 1 05:05 - native3d passed, draw.cpp committed as game 08933a7, no
S3e/native3e tonight, keep the S3e tools unused for S4. Backup first; counted replacements; LF kept.
  python build\\agent2\\notes-0507.py
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
    ('stays prepared and unbuilt unless Agent 1 says otherwise. Agent 8\'s all-clear',
     'stays prepared and unbuilt unless Agent 1 says otherwise.\n'
     'Agent 1 (05:05): native3d passed; draw.cpp is committed as game 08933a7 (pushed); NO S3e/native3e tonight; keep\n'
     'the S3e tools unused for S4. Checked 05:06: 08933a7 changes only draw.cpp against 001336f (+5 lines), and its blob\n'
     '(cbf8567d) == snap1\'s and live draw.cpp (checkout 5EA1F357, 306,557 B), so S3d == game 08933a7 + SDK c5fe668 +\n'
     'the uncommitted pre-sprint plume and simde edits. Agent 8\'s all-clear'),
    ("**S3e (PREPARED 04:46, NOT BUILT; only at Agent 1's explicit GO with Agent 4's new draw.cpp sha256, before 08:30)**",
     "**S3e (PREPARED 04:46, NOT BUILT; Agent 1 05:05: not tonight, keep the tools unused for S4)**\n"
     "- For S4: the S3e tools assume snap1 is at S3d (newest STATE-S3d-*.tsv) and one draw.cpp row; for another base\n"
     "  or tag, regenerate them the same way (make-s3e-clones.py pattern) and get Agent 9's review again."),
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

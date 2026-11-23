"""Agent 2 - RESUME block update (05:01): Agent 8's native3d rows show 0 hash=0 lines, so the native3e trigger is not
met; the inventory all-clear comes after Agent 8's warm run (~05:45-05:50), before Agent 7's shader dump.
Backup first; counted replacements; LF kept.  python build\\agent2\\notes-0501.py
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
old = ("the S3e diffs, then Agent 1's GO with the sha; start only after Agent 8's window (~05:50), never after 06:45. By\n")
new = ("the S3e diffs, then Agent 1's GO with the sha; start only after Agent 8's window (~05:50), never after 06:45.\n"
       "05:00, Agent 8: the native3d rows show 0 hash=0 lines (n0, n2, n3), so the native3e trigger is NOT met; S3e\n"
       "stays prepared and unbuilt unless Agent 1 says otherwise. Agent 8's all-clear for the 1-min inventory run comes\n"
       "right after its warm run (~05:45-05:50) and before Agent 7's shader dump, so run it at once and keep it short. By\n")
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

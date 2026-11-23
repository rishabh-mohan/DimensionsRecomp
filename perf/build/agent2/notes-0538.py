"""Agent 2 - 05:38: the Staged bins table mixes units: every row but nativeB gives MiB (2^20 B) labelled MB;
the nativeB row gave decimal MB (364,566,976 B = 364.6 MB = 347.7 MiB). Make it 347.7 and say MiB in the header.
Counted replacements, backup first, LF kept."""
import hashlib
import os
import shutil
import sys
import time

R = r'<workspace>'
NOTES = os.path.join(R, 'perf-notes', 'agent2-baseline.md')
REPL = [
    ('| `nativeB-bin` | 04:34:06 | 8, 364.6 MB |', '| `nativeB-bin` | 04:34:06 | 8, 347.7 MB |'),
    ('\n**Staged bins** (in `build/agent2/`; file counts exclude MANIFEST.txt;',
     '\n**Staged bins** (in `build/agent2/`; file counts exclude MANIFEST.txt; MB here = MiB, 2^20 B;'),
]
raw = open(NOTES, 'rb').read()
if b'\r\n' in raw:
    sys.exit('REFUSED: CRLF')
t = raw.decode('utf-8')
for a, b in REPL:
    if t.count(a) != 1:
        sys.exit('REFUSED: %r found %d times (nothing written)' % (a[:40], t.count(a)))
    t = t.replace(a, b)
bk = os.path.join(R, 'build', 'agent2', 'notes-backup', 'agent2-baseline.md.' + time.strftime('%H%M%S'))
shutil.copy2(NOTES, bk)
b = t.encode('utf-8')
open(NOTES, 'wb').write(b)
print('notes updated (backup %s): %d B, sha256 %s, LF only: %s'
      % (os.path.basename(bk), len(b), hashlib.sha256(b).hexdigest()[:16].upper(), b'\r\n' not in b))

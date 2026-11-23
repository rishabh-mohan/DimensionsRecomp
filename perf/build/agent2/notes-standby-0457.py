"""Agent 2 - RESUME block update (04:57): Agent 8's window to ~05:50, Agent 1's S3e GO conditions and time limits,
inventory.py ready, Agent 10's nativeB 1a static PASS. Backup first; counted replacements; LF kept.
  python build\\agent2\\notes-standby-0457.py
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
errs = []


def rep(old, new, n=1, what=''):
    global t
    c = t.count(old)
    if c != n:
        errs.append('%s: expected %d, found %d' % (what or old[:60], n, c))
        return
    t = t.replace(old, new)


rep('posted to Agents 1, 8, 9 and 10. Task #14 is DONE (`@@done 14` at 04:37). Agent 8 profiles on an idle machine from\n'
    'about 04:41 to 05:42 (s0-s2, native3d, the nativeB pair, attract): tell Agent 8 before any build of mine. No builds\n',
    'posted to Agents 1, 8, 9 and 10. Task #14 is DONE (`@@done 14` at 04:37). Agent 8 profiles on an idle machine from\n'
    'about 04:41 to about 05:50 (s0-s2, native3d, the nativeB pair, attract + Agent 3\'s warm devoff3 run): no build,\n'
    'hashing or disk walk of mine until Agent 8 says the window has ended; tell Agent 8 before any build. No builds\n',
    what='Agent 8 window')
rep('with the new draw.cpp sha256. It is prepared, not built (S3e section below; Agent 9 reviews the diffs). By ~06:30: a\n'
    '"Build inventory" table in this file, for the user report and the next restart prompt (delete nothing).**',
    'with the new draw.cpp sha256. It is prepared, not built (S3e section below; Agent 9 reviews the diffs). Agent 1\n'
    '(04:55): the GO needs Agent 4\'s read of the native3d rows (~05:02) and its step 1, Agent 10\'s SAFE, Agent 9\'s OK of\n'
    'the S3e diffs, then Agent 1\'s GO with the sha; start only after Agent 8\'s window (~05:50), never after 06:45. By\n'
    '06:30: the "Build inventory" table in this file, for the user report and the next restart prompt (delete nothing):\n'
    '`inventory.py` is ready (light test 04:56 OK: 10 bins, MANIFEST hashes == the table below); the full run,\n'
    '`python build\\agent2\\inventory.py --insert` (exe re-hash + dir sizes, ~1 min), comes after Agent 8\'s all-clear\n'
    'and after native3e if it is built; it inserts the tables between the inventory markers above **Staged bins**.**',
    what='standby')
rep('    MANIFEST pins (SHA256SUMS 24ce1493), gate PASS (525 DB entries, 432 TUs), host regs 378 (0 new / 0 gone).\n',
    '    MANIFEST pins (SHA256SUMS 24ce1493), gate PASS (525 DB entries, 432 TUs), host regs 378 (0 new / 0 gone).\n'
    '  - Agent 10, nativeB 1a static (04:55): PASS (statecmp + --full MATCH, sumscheck MATCH, lrsites PASS, hookset PASS\n'
    '    with 181 hooks, warncmp CHECK host-only); both pair runs start cold (fresh run dirs); 1b verdict within 20 min\n'
    '    of the pair logs.\n', what='Agent 10 1a')
rep("  (-> `prep-s3e.py`, `run-s3e.ps1`), `notes-s3e-prep.py`.\n",
    "  (-> `prep-s3e.py`, `run-s3e.ps1`), `notes-s3e-prep.py`, `notes-standby-0457.py`, `inventory.py`.\n", what='scripts')
t2 = re.sub(r'\A(# Agent 2: build pipeline - RESUME NOTE \(.*?; updated )\d\d:\d\d\)', r'\g<1>%s)' % now, t, count=1)
if t2 == t:
    errs.append('header time not updated')
t = t2
if errs:
    print('REFUSED (nothing written):')
    for e in errs:
        print('  ' + e)
    sys.exit(1)
bk = os.path.join(BK, 'agent2-baseline.md.' + time.strftime('%H%M%S'))
shutil.copy2(F, bk)
b = t.encode('utf-8')
with open(F, 'wb') as f:
    f.write(b)
print('backup %s; wrote %d B, sha256 %s, CRLF %d' % (bk, len(b), hashlib.sha256(b).hexdigest()[:16].upper(),
                                                    b.count(b'\r\n')))

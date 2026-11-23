"""Agent 2 - small follow-up to notes-s4est.py: add Agent 1's 07:08 message to the task #30 RESUME paragraph and
fix one wrap ("~61 / s"). Anchored, counted; refuses unless the notes are 30C54BDE704C0C36 (LF only)."""
import hashlib, os, sys, time

R = r'<workspace>'
NOTES = os.path.join(R, 'perf-notes', 'agent2-baseline.md')
BKDIR = os.path.join(R, 'build', 'agent2', 'notes-backup')
EXPECT = '30C54BDE704C0C36'
REPS = [
    ('no timers; window 4 waits for the user (~10:00).**\n',
     'no timers; window 4 waits for the user (~10:00). Agent 1 (07:08): C1 staging went to Agent 12, so no task for me\n'
     'tonight; answer Agent 11 by message; no builds or bin dirs.**\n'),
    ('Regen: ~130 s (887 files, 467.3 MB) + gen-check ~61\n  s; or Agent 9',
     'Regen: ~130 s (887 files, 467.3 MB) + gen-check\n  ~61 s; or Agent 9'),
]

data = open(NOTES, 'rb').read()
h0 = hashlib.sha256(data).hexdigest().upper()
if not h0.startswith(EXPECT):
    print('REFUSED: sha', h0[:16]); sys.exit(2)
if b'\r' in data:
    print('REFUSED: CR'); sys.exit(2)
text = data.decode('utf-8')
for old, new in REPS:
    c = text.count(old)
    if c != 1:
        print('REFUSED: count', c, repr(old[:50])); sys.exit(2)
    new.encode('ascii')
    text = text.replace(old, new, 1)
bk = os.path.join(BKDIR, 'agent2-baseline.md.' + time.strftime('%H%M%S'))
if os.path.exists(bk):
    print('REFUSED: backup exists'); sys.exit(2)
open(bk, 'wb').write(data)
out = text.encode('utf-8')
open(NOTES, 'wb').write(out)
back = open(NOTES, 'rb').read()
if back != out:
    print('REFUSED: read-back mismatch'); sys.exit(2)
print('backup', os.path.basename(bk), len(data), h0[:16])
print('notes ', len(back), hashlib.sha256(back).hexdigest().upper()[:16], 'lines', text.count('\n'),
      'CR' if b'\r' in back else 'LF-only', 'delta', len(back) - len(data))

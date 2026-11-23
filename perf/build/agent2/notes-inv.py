"""Agent 2 - after the full inventory run (`inventory.py --insert`): update the RESUME block of
perf-notes/agent2-baseline.md (counted replacements, backup first, LF kept). Reads the totals from
build/agent2/inventory.md and refuses (writes nothing) on any problem, mismatch or a --light run.
  python build/agent2/notes-inv.py HH:MM      (HH:MM = the time of Agent 8's all-clear)
"""
import hashlib
import os
import re
import shutil
import sys
import time

R = r'<workspace>'
A = os.path.join(R, 'build', 'agent2')
NOTES = os.path.join(R, 'perf-notes', 'agent2-baseline.md')
BEGIN, END = '<!-- inventory:begin -->', '<!-- inventory:end -->'

clear = sys.argv[1] if len(sys.argv) > 1 else ''
if not re.fullmatch(r'\d\d:\d\d', clear):
    sys.exit('usage: notes-inv.py HH:MM (the time of the all-clear)')
with open(os.path.join(A, 'inventory.md'), encoding='utf-8') as f:
    inv = f.read()


def one(pat):
    m = re.findall(pat, inv)
    if len(m) != 1:
        sys.exit('REFUSED: %r found %d times in inventory.md (nothing written)' % (pat, len(m)))
    return m[0]


if 'PROBLEMS' in inv or '--light' in inv or 'MISMATCH' in inv:
    sys.exit('REFUSED: inventory.md has PROBLEMS / MISMATCH or is a --light run (nothing written)')
gen = one(r'\(generated (\d\d:\d\d) by')
nbins = one(r'all (\d+) match their MANIFEST rows')
staged = one(r'Staged bins total ([\d.]+ [GM]iB)')
yes = one(r'could be deleted later\): ([\d.]+ [GM]iB)')
ag = one(r'its staged bins\): ([\d.]+ [GM]iB)')
free = one(r'Free C: ([\d.]+ GiB)')

with open(NOTES, 'rb') as f:
    raw = f.read()
if b'\r\n' in raw:
    sys.exit('REFUSED: the notes file has CRLF line ends')
t = raw.decode('utf-8')
if t.count(inv) != 1 or t.count(BEGIN) != 1 or t.count(END) != 1:
    sys.exit('REFUSED: the notes do not hold exactly one copy of the current inventory block (nothing written)')

now = time.strftime('%H:%M')
spans = [
    ("Agent 8 profiles on an idle machine from", "tell Agent 8 before any build.",
     "Agent 8's idle-machine window (04:41 to\n"
     "~05:50: s0-s2, native3d, the nativeB pair, attract + Agent 3's warm devoff3 run) gave me its all-clear at %s for\n"
     "the inventory run (done %s); Agent 7's shader dump comes next, so ask Agent 8 before any build or long disk job."
     % (clear, gen)),
    ("Agent 8's all-clear for the 1-min inventory run comes", "above **Staged bins**.**",
     '"Build inventory" (Agent 1, 04:39, due 06:30): DONE at %s,\n'
     'inserted by `python build/agent2/inventory.py --insert` (all %s exe re-hashes match their MANIFEST rows, 0\n'
     'problems): staged bins %s; build/agent2 in total %s; the "yes" rows (could be deleted later) %s; free C %s.\n'
     'The tables are just below, also in `build/agent2/inventory.md` and `.tsv`; re-running the same command refreshes\n'
     'them (it replaces the block between the inventory markers). Delete nothing until Agent 1 or the user says so.**'
     % (gen, nbins, staged, ag, yes, free)),
]
for a, b, new in spans:
    if t.count(a) != 1 or t.count(b) != 1:
        sys.exit('REFUSED: span %r / %r not found exactly once (nothing written)' % (a[:30], b[:30]))
    i = t.index(a)
    j = t.index(b, i) + len(b)
    if j - i > 1500:
        sys.exit('REFUSED: span %r is %d chars (too long; nothing written)' % (a[:30], j - i))
    t = t[:i] + new + t[j:]
t, n = re.subn(r'\A# Agent 2: build pipeline - RESUME NOTE \(session 3, task #14 done, standby; updated \d\d:\d\d\)',
               '# Agent 2: build pipeline - RESUME NOTE (session 3, task #14 done, inventory done, standby; updated %s)'
               % now, t)
if n != 1:
    sys.exit('REFUSED: header line not found (nothing written)')
bk = os.path.join(A, 'notes-backup', 'agent2-baseline.md.' + time.strftime('%H%M%S'))
shutil.copy2(NOTES, bk)
b = t.encode('utf-8')
with open(NOTES, 'wb') as f:
    f.write(b)
print('notes updated (backup %s): %d B, sha256 %s, LF only: %s'
      % (os.path.basename(bk), len(b), hashlib.sha256(b).hexdigest()[:16].upper(), b'\r\n' not in b))

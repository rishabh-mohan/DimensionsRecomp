"""Agent 2 - 05:41: RESUME block after the inventory: Agent 8's queue after my run (S11, reverse-order native pair,
Agent 11's throttling pairs, maybe attract; build all-clear ~06:50), Agent 1's 05:31 rule (no recursive scans of the
SDK, DimensionsRecomp or build trees while a game runs; <= 2 threads), and a re-wrap of the inventory lines.
Counted replacements, backup first, LF kept."""
import hashlib
import os
import shutil
import sys
import time

R = r'<workspace>'
NOTES = os.path.join(R, 'perf-notes', 'agent2-baseline.md')
REPL = [
    ("the inventory run (done 05:39); Agent 7's shader dump comes next, so ask Agent 8 before any build or long disk "
     "job. No builds\nor game runs from 08:30",
     "the inventory run (done 05:39:16, 7.8 s). Then S11, the reverse-order native pair, Agent 11's throttling pairs and\n"
     "maybe an attract re-run; Agent 8 sends the build all-clear about 06:50 (it gives a gap between runs if a build gets\n"
     "a GO first). Agent 1 (05:31): while a game runs (Agent 8's queue until about 07:15), no recursive searches or scans\n"
     "of the SDK, DimensionsRecomp or build trees; targeted reads only, <= 2 threads. No builds\nor game runs from 08:30"),
    ('problems): staged bins 2.79 GiB; build/agent2 in total 12.41 GiB; the "yes" rows (could be deleted later) 5.56 '
     'GiB; free C 244.4 GiB.\nThe tables are just below, also in `build/agent2/inventory.md` and `.tsv`; re-running the '
     'same command refreshes\nthem (it replaces the block between the inventory markers). Delete nothing until Agent 1 '
     'or the user says so.**',
     'problems): staged bins 2.79 GiB; build/agent2 in total 12.41 GiB; the "yes" rows (could be deleted\n'
     'later) 5.56 GiB (5.1 GiB of it the snapB/snapB3 trees, after the B decision); free C 244.4 GiB. The tables are\n'
     'just below, also in `build/agent2/inventory.md` and `.tsv`; re-running the same command refreshes them (it\n'
     'replaces the block between the inventory markers; a full run walks the build trees, so only when no game runs).\n'
     'Delete nothing until Agent 1 or the user says so.**'),
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
lines = t.split('\n')
print('notes updated (backup %s): %d B, sha256 %s, LF only: %s, longest RESUME line %d'
      % (os.path.basename(bk), len(b), hashlib.sha256(b).hexdigest()[:16].upper(), b'\r\n' not in b,
         max(len(x) for x in lines[:40] if not x.startswith(('|', '**Build inventory**', '- ')))))

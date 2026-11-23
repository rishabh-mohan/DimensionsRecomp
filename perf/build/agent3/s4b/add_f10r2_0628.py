"""Agent 3, task #23 (Agent 1, 11-23 06:23): append the second f10a/f10b pair (f10a2, f10b2) to queue.jsonl.

Same bins, sets and settings as f10a/f10b (untimed, vpad L route, slow_frame_log_ms=1, tags via the fixed sidecar);
only the id and the -Tag change. est 620 s (the 600 s cap + start/stop), so the queue's -GamesClosed guard keeps even a
hung run inside the 07:20 limit. Both rows also need ready-f10r2 (created after rpm4 is DONE and the queue restarted
with -LastLaunch/-GamesClosed for 07:20). Backs queue.jsonl up to queue.jsonl.bak-0628 first. Idempotent."""
import json
import os
import shutil
import sys

here = os.path.dirname(os.path.abspath(__file__))
q = os.path.join(here, 'queue.jsonl')
bak = q + '.bak-0628'
raw = open(q, 'rb').read()
rows = {}
for ln in raw.decode('utf-8').splitlines():
    s = ln.strip()
    if s.startswith('{'):
        d = json.loads(s)
        rows[d['id']] = d
have = [k for k in ('f10a2', 'f10b2') if k in rows]
if have:
    print('already in queue.jsonl: %s (nothing changed)' % have)
    sys.exit(0)
if not os.path.exists(bak):
    shutil.copy2(q, bak)
new = []
for src, nid, tag in (('f10a', 'f10a2', 'f10a2-m1-sfl-level'), ('f10b', 'f10b2', 'f10b2-p2fc-level')):
    d = json.loads(json.dumps(rows[src]))
    d['id'] = nid
    d['est'] = 620
    d['needs'] = list(d['needs']) + ['build\\agent3\\s4b\\ready-f10r2']
    a = d['args']
    a[a.index('-Tag') + 1] = tag
    d['note'] = ('task #23 second pair (Agent 1 06:23): same bins, set and settings as %s, after rpm4, same host-load '
                 'logging; every game run must end by 07:20 (the night launcher restores settings at 07:30), so skip '
                 'rather than run late. Was: %s' % (src, rows[src].get('note', '')))
    new.append(d)
nl = b'\r\n' if b'\r\n' in raw else b'\n'
out = b'' if (not raw or raw.endswith(b'\n')) else nl
for d in new:
    out += json.dumps(d).encode('utf-8') + nl
with open(q, 'ab') as f:
    f.write(out)
print('backup: %s' % bak)
for d in new:
    print('added %s: est %s, tag %s, needs %s' % (d['id'], d['est'], d['args'][d['args'].index('-Tag') + 1], d['needs']))

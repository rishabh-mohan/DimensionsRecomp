"""prep_0550.py - Agent 3, task #23 (Agent 1, 11-23 05:45): this morning only f10a, f10b and then the native4b
re-pin rows (rpb0, rpm4) may run, all before 12:00. Changes build/agent3/s4b/queue.jsonl (backup .bak-0550):
  - every pending row except f10a, f10b, rpb0 and rpm4 is commented out ('#' + the line; the queue skips '#' lines),
    so nothing else can launch when ready-later exists;
  - rpm4 also needs build\\agent3\\s4b\\ready-rpm4, which I create only after rpb0's boot check passes (REPIN.md 3a);
  - a '#' header line records why.
Done rows (in queue-state.jsonl) are left as they are (the queue skips them anyway).
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
Q = os.path.join(HERE, '..', 's4b', 'queue.jsonl')
STATE = os.path.join(HERE, '..', 's4b', 'queue-state.jsonl')
KEEP = ('f10a', 'f10b', 'rpb0', 'rpm4')
RPM4_NEED = 'build\\agent3\\s4b\\ready-rpm4'

raw = open(Q, 'rb').read().decode('utf-8-sig')
crlf = '\r\n' in raw
lines = raw.replace('\r\n', '\n').split('\n')
if any(l.startswith('# 05:50 task #23') for l in lines):
    sys.exit('already prepared')
done = set()
for l in open(STATE, encoding='utf-8-sig'):
    l = l.strip()
    if l:
        r = json.loads(l)
        if not r.get('aborted'):
            done.add(r.get('id'))
out, off, kept = [], [], []
for l in lines:
    t = l.strip()
    if not t.startswith('{'):
        out.append(l)
        continue
    r = json.loads(t)
    rid = r.get('id')
    if rid in done:
        out.append(l)
    elif rid in KEEP:
        if rid == 'rpm4':
            needs = r.get('needs') or []
            needs = [needs] if isinstance(needs, str) else list(needs)
            if RPM4_NEED not in needs:
                needs.append(RPM4_NEED)
            r['needs'] = needs
            l = json.dumps(r)
        out.append(l)
        kept.append(rid)
    else:
        out.append('#' + l)
        off.append(rid)
missing = [k for k in KEEP if k not in kept]
if missing:
    sys.exit('rows not found or already done: %s' % missing)
out.insert(0, '# 05:50 task #23 (Agent 1, 11-23 05:45): only f10a, f10b, rpb0, rpm4 run this morning (rpm4 after '
              'ready-rpm4 = rpb0 boot check PASS); the other pending rows are commented out. Backup: queue.jsonl.bak-0550')
shutil.copy2(Q, Q + '.bak-0550')
s = '\n'.join(out)
with open(Q, 'wb') as f:
    f.write((s.replace('\n', '\r\n') if crlf else s).encode('utf-8'))
print('kept %s; commented out %d: %s' % (kept, len(off), ' '.join(off)))

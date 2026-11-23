# 22:33 per Agent 1 (22:32): after s4b17, launch nothing more tonight. rpb0/rpm4 (re-pin), s4b19 and every
# other remaining row wait for ready-later (after tonight's windows, when Agent 1 wakes Agent 3).
import json, shutil

P = r'build\agent3\s4b\queue.jsonl'
LATER = 'build\\agent3\\s4b\\ready-later'
shutil.copy(P, P + '.bak-2233')
lines = open(P, encoding='utf-8-sig').read().splitlines()
out = []
for l in lines:
    if l.strip().startswith('{'):
        r = json.loads(l)
        if r['id'] in ('rpb0', 'rpm4', 's4b19'):
            n = r.get('needs', [])
            n = [n] if isinstance(n, str) else list(n)
            if LATER not in n:
                n.append(LATER)
            r['needs'] = n
        out.append(json.dumps(r))
    else:
        out.append(l)
out.insert(next(i for i, l in enumerate(out) if l.strip().startswith('{')),
           '# 22:33 (stop_2233.py, Agent 1 22:32): nothing launches after s4b17 tonight; rpb0/rpm4/s4b19 also need ready-later.')
with open(P, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(out) + '\n')
import os
for l in out:
    if l.strip().startswith('{'):
        r = json.loads(l)
        miss = [n.split('\\')[-1] for n in (r['needs'] if isinstance(r['needs'], list) else [r['needs']])
                if not os.path.exists(n)]
        print(r['id'], 'ELIGIBLE' if not miss else 'blocked by ' + ','.join(miss))

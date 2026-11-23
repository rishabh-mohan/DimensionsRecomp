# build/agent3/s4b/reorder_2210.py - Agent 3, one-off queue reorder (22:10). Backup: queue.jsonl.bak-2210.
# s4b20 (ready-m1, Agent 5 22:09) goes after s4b18 (W9 rows first, Agent 1 21:45); w6gB (C1 level-load coverage, Agent 1
# 21:54) and the re-pin go before s4b04/s4b08 so that both fit before LastLaunch 23:10; s4bV0 = C1-OFF verify baseline for
# Agent 10 (row-7 F 92 question), gated on ready-v0 (made only on Agent 1's OK).
import json
import os
import shutil

p = os.path.join('build', 'agent3', 's4b', 'queue.jsonl')
shutil.copyfile(p, p + '.bak-2210')
with open(p, encoding='utf-8') as f:
    lines = f.read().splitlines()
hdr = [ln for ln in lines if not ln.lstrip().startswith('{')]
rows, order0 = {}, []
for ln in lines:
    if ln.lstrip().startswith('{'):
        d = json.loads(ln)
        rows[d['id']] = ln
        order0.append(d['id'])
v0 = {"id": "s4bV0", "est": 265,
      "needs": ["build\\agent3\\s4b\\ready-s4b-off", "build\\agent3\\s4b\\ready-v0"],
      "args": ["-BinDir", "build\\agent2\\devoff4b-bin", "-Seconds", "420", "-Tag", "s4b-V0-c1off-verify",
               "-InputScript", "harness\\routes\\b-gate-menus-long.txt", "-Cvar",
               "physical_protect_hold_global_lock=true;physical_protect_keep_watch=false;physical_protect_keep_watch_verify=true"]}
if 's4bV0' not in rows:
    rows['s4bV0'] = json.dumps(v0, separators=(',', ':'))
new = ['s4b01', 's4bL0', 'w6gA', 'w6s2', 'w6s1', 'g3q', 's4b23', 's4b07', 'w6s3', 's4b22', 's4b24', 's4b18', 's4b20',
       'w6gB', 'rpb0', 'rpm4', 's4b04', 's4bV0', 's4b08', 's4b02', 's4b05', 's4b06', 's4b03', 's4b09', 's4b11', 's4b14',
       's4b10', 's4b12', 's4b13', 's4b15', 's4b16', 's4b25', 's4b19', 's4b21', 's4b17']
have = set(rows)
assert sorted(new) == sorted(have), sorted(set(new) ^ have)
note = ('# 22:10: s4b20 (ready-m1) after s4b18; w6gB + the re-pin before s4b04/s4b08 (both must fit before 23:10); '
        's4bV0 = C1-OFF verify baseline (Agent 10), needs ready-v0 = Agent 1 OK.')
if note not in hdr:
    hdr.append(note)
out = hdr + [rows[i] for i in new]
with open(p + '.tmp', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write('\n'.join(out) + '\n')
os.replace(p + '.tmp', p)
print('rows', len(new), 'order', ' '.join(new))

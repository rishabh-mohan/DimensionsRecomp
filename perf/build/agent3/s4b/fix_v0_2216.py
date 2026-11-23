# build/agent3/s4b/fix_v0_2216.py - Agent 3, one-off (22:16): s4bV0 to Agent 12's control spec = row 7 exactly
# (devoff4b-bin, L route + tags, 600 s cap) with only physical_protect_keep_watch=false. Still gated on ready-v0.
import json
import os
import shutil

p = os.path.join('build', 'agent3', 's4b', 'queue.jsonl')
shutil.copyfile(p, p + '.bak-2216')
with open(p, encoding='utf-8') as f:
    lines = f.read().splitlines()
v0 = {"id": "s4bV0", "est": 560, "toypad": True,
      "needs": ["build\\agent3\\s4b\\ready-s4b-off", "build\\agent3\\s4b\\ready-v0"],
      "args": ["-BinDir", "build\\agent2\\devoff4b-bin", "-Seconds", "600", "-Tag", "s4b-V0-c1off-verify-level",
               "-InputScript", "build\\agent3\\toypad\\routes\\level-l.txt", "-Cvar",
               "physical_protect_hold_global_lock=true;physical_protect_keep_watch=false;physical_protect_keep_watch_verify=true"]}
out, n = [], 0
for ln in lines:
    if ln.lstrip().startswith('{') and json.loads(ln).get('id') == 's4bV0':
        ln = json.dumps(v0, separators=(',', ':'))
        n += 1
    elif ln.startswith('# 22:10:'):
        ln = ln.replace('s4bV0 = C1-OFF verify baseline (Agent 10)', 's4bV0 = C1-OFF verify control (Agent 12 spec 22:15: row 7 + keep_watch=false)')
    out.append(ln)
assert n == 1, n
for ln in out:
    if ln.lstrip().startswith('{'):
        json.loads(ln)
with open(p + '.tmp', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write('\n'.join(out) + '\n')
os.replace(p + '.tmp', p)
print('s4bV0 replaced:', json.dumps(v0)[:200])

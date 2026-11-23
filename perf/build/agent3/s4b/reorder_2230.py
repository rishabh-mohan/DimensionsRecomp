# 22:30 queue change per Agent 1 (22:27): s4b17 right after w6gB (W9's third gate), then the re-pin
# (rpb0, rpm4) on Agent 4's hand-off. s4b04 / s4b08 / s4bV0 and a new long-cap p2fc + verify level-load
# row (S21 A, cap > 600 s) run after tonight's windows, when Agent 1 wakes Agent 3: they need ready-later.
# Every other remaining row also needs ready-later, so nothing unplanned fills the gap before the re-pin.
# s4b19 is the one optional gap row: it needs ready-gap, created by hand only if it can end before ~22:50.
import json, shutil

P = r'build\agent3\s4b\queue.jsonl'
LATER = 'build\\agent3\\s4b\\ready-later'
GAP = 'build\\agent3\\s4b\\ready-gap'
shutil.copy(P, P + '.bak-2230')
lines = open(P, encoding='utf-8-sig').read().splitlines()
head = [l for l in lines if l.strip() and not l.strip().startswith('{')]
rows = [json.loads(l) for l in lines if l.strip().startswith('{')]
by = {r['id']: r for r in rows}


def need(r, m):
    n = r.get('needs', [])
    n = [n] if isinstance(n, str) else list(n)
    if m not in n:
        n.append(m)
    r['needs'] = n


ga = by['w6gA']['args']
cv = ga[ga.index('-Cvar') + 1]
assert 'physical_protect_keep_watch_verify=true' in cv and 'shared_memory_single_hold_rearm=true' in cv, cv
if 's4bLV' not in by:
    lv = {'id': 's4bLV', 'est': 1860, 'toypad': True,
          'needs': ['build\\agent3\\s4b\\ready-s4b-off', LATER],
          'args': ['-BinDir', 'build\\agent2\\devoff4b-bin', '-Seconds', '1800', '-Tag', 's4b-LV-p2fcv-level-long',
                   '-InputScript', 'build\\agent3\\toypad\\routes\\level-l.txt', '-Cvar', cv],
          'note': 'S21 A (b2r L1065): one p2fc + verify run must reach the level before C1 goes default-ON; '
                  'cap > 600 s (gate A cvars, L route + tags). After tonight\'s windows (Agent 1 22:27).'}
    rows.append(lv)
    by['s4bLV'] = lv

first = ['s4b01', 's4bL0', 'w6gA', 'w6s2', 'w6s1', 'g3q', 's4b23', 's4b07', 'w6s3', 's4b22', 's4b24', 's4b18',
         's4b20', 'w6gB', 's4b17', 'rpb0', 'rpm4', 's4b19']
later_first = ['s4b04', 's4bV0', 's4b08', 's4bLV']
order = first + later_first + [r['id'] for r in rows if r['id'] not in first + later_first]
for i in order:
    if i == 's4b19':
        need(by[i], GAP)
    elif i not in first:
        need(by[i], LATER)
head.append('# 22:30 reorder (reorder_2230.py): s4b17 -> re-pin; s4b19 = optional gap row (ready-gap); '
            'the rest wait for ready-later (after tonight\'s windows).')
with open(P, 'w', encoding='utf-8', newline='\n') as f:
    for h in head:
        f.write(h + '\n')
    for i in order:
        f.write(json.dumps(by[i]) + '\n')
for i in order:
    print(i, [n.split('\\')[-1] for n in (by[i]['needs'] if isinstance(by[i]['needs'], list) else [by[i]['needs']])])

#!/usr/bin/env python3
"""Read-only checks of perf-notes/agent6-attract-stalls.md after patch_note.py and patch_s11_1.py."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
NOTE = HERE.parents[2] / 'perf-notes' / 'agent6-attract-stalls.md'
BAK = HERE / 'agent6-attract-stalls.md.bak-0500'
BAK2 = HERE / 'agent6-attract-stalls.md.bak-0620'

b = NOTE.read_bytes()
t = b.decode('utf-8')
lines = t.split('\n')[:-1] if t.endswith('\n') else t.split('\n')
fails = 0


def chk(name, ok, extra=''):
    global fails
    fails += 0 if ok else 1
    print(('PASS ' if ok else 'FAIL ') + name + (f'  [{extra}]' if extra else ''))


chk('no BOM', not b.startswith(b'\xef\xbb\xbf'))
chk('no CRLF', b'\r\n' not in b)
chk('no U+FFFD', '\ufffd' not in t)
chk('ends with LF', b.endswith(b'\n'))
chk('backup is the 26,072 B original', BAK.exists() and BAK.stat().st_size == 26072)
chk('pre-11.1 backup is the 45,344 B version', BAK2.exists() and BAK2.stat().st_size == 45344)

heads = [l for l in lines if l.startswith('## ') or l.startswith('### ')]
want = ['## Bottom line'] + [f'## {i}.' for i in range(1, 10)] + [
    '## 10. S4 items (for Agent 10)', '### 10.1 ', '### 10.2 ', '### 10.3 ',
    '## 11. Diagnostic run spec', '### 11.1 Results']
got_ok = len(heads) >= len(want) and all(
    any(h.startswith(w) for h in heads) for w in want)
order = [next((i for i, h in enumerate(heads) if h.startswith(w)), -1) for w in want]
chk('headings present and in order', got_ok and order == sorted(order) and -1 not in order,
    ' | '.join(h[:28] for h in heads if not h.startswith('### 3.')))
chk('## 10. once', t.count('\n## 10.') == 1)
chk('## 11. once', t.count('\n## 11.') == 1)
chk('### 11.1 once and last', t.count('\n### 11.1 ') == 1 and heads[-1].startswith('### 11.1 Results'))

i7 = next(i for i, l in enumerate(lines) if l.startswith('## 7.'))
i8 = next(i for i, l in enumerate(lines) if l.startswith('## 8.'))
sec7 = lines[i7:i8]
chk('section 7 has the proposal note', '> [!NOTE]' in sec7 and any(
    'Proposal for after window 4' in l for l in sec7))
alerts = [i for i, l in enumerate(lines) if l.startswith('> [!')]
# The original FUNCTIONAL ONLY warning (L6) plus the section 7 note;
# alerts must not be adjacent or nested.
chk('two alerts, not adjacent', len(alerts) == 2 and alerts[1] - alerts[0] > 3,
    ', '.join(f'L{i + 1}' for i in alerts))
chk('status line updated', lines[2].startswith('Status: **analysis done, 2026-11-22 ~04:30. §10'))
chk('status line mentions §11.1', '§11.1' in lines[2])
chk('11.1 has the Q3 total row and the decision',
    '| all | 49 |' in t and 'Decision: skip §10.1' in t)
for ref, n in (('§10.1', 2), ('§10.2', 2), ('§10.3', 2), ('spec in §11', 2), ('§11 arm B', 1),
               ('§11.1', 3)):
    c = t.count(ref)
    chk(f'ref {ref!r} >= {n}', c >= n, str(c))
chk("no stale '§6.1'", t.count('§6.1') == 0, str(t.count('§6.1')))

# Table shape: every row of a table has the header's column count.
bad = []
i = 0
while i < len(lines):
    if lines[i].startswith('|'):
        j = i
        while j < len(lines) and lines[j].startswith('|'):
            j += 1
        cols = [l.count('|') for l in lines[i:j]]
        if len(set(cols)) != 1:
            bad.append(f'L{i + 1}-{j}: {cols}')
        i = j
    else:
        i += 1
chk('tables have consistent column counts', not bad, '; '.join(bad))

print(f'{len(b)} B, {len(lines)} lines')
sys.exit(1 if fails else 0)

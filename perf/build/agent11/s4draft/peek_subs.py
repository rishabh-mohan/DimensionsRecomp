# -*- coding: utf-8 -*-
# peek_subs.py - read-only: where run11.py's sub targets sit in the current S4-DRAFT, plus a key scan.
# Usage: python build\agent11\s4draft\peek_subs.py [full line numbers...]
import ast
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'<workspace>'
if os.path.exists(os.path.join(ROOT, 'perf-notes', 'WINDOW-HOLD.txt')):
    print('HOLD EXISTS - stop')
    sys.exit(1)
draft = open(os.path.join(ROOT, 'perf-notes', 'S4-DRAFT.md'), 'rb').read().decode('utf-8')
lines = draft.split('\n')
src = open(os.path.join(ROOT, 'build', 'agent11', 's4draft', 'run11.py'), 'rb').read().decode('utf-8')
tree = ast.parse(src)
QUIET = len(sys.argv) > 1
for node in ([] if QUIET else tree.body):
    if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') == 'SUBS':
        for elt in node.value.elts:
            name = ast.literal_eval(elt.elts[0])
            try:
                tgt = ast.literal_eval(elt.elts[1])
            except Exception:
                print('%-22s target not literal' % name)
                continue
            c = draft.count(tgt)
            ln = draft[:draft.index(tgt)].count('\n') + 1 if c else 0
            print('%-22s count %d at L%d' % (name, c, ln))
KEYS = ['re-pin', 'S4c', '17:10', 'W5 waits', "double-click", 'task #35', 'Launcher review', '#24 +']
print('--- key scan (L, len, keys, head)')
for i, l in enumerate([] if QUIET else lines):
    ks = [k for k in KEYS if k in l]
    if ks:
        print('L%d len %d %s :: %s' % (i + 1, len(l), ks, l[:150]))
CK = ['re-pin', 'S4c', 'slow-state check']
for a in sys.argv[1:]:
    if a.startswith('find:'):
        k = a[5:]
        print('=== find %r: %s' % (k, [i + 1 for i, l in enumerate(lines) if k in l]))
        continue
    if a.endswith('c'):
        n = int(a[:-1])
        l = lines[n - 1]
        print('=== L%d contexts (len %d)' % (n, len(l)))
        for k in CK:
            p = l.find(k)
            while p >= 0:
                print('  [%s @%d] …%s…' % (k, p, l[max(0, p - 220):p + 220]))
                p = l.find(k, p + 1)
        continue
    n = int(a)
    print('=== L%d (len %d)' % (n, len(lines[n - 1])))
    print(lines[n - 1])

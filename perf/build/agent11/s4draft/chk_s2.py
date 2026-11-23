# chk_s2.py - read-only: SESSION2 line counting (LF vs splitlines) and b2r rows/sections 37-39.
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
R = r'<workspace>'
if os.path.exists(os.path.join(R, 'perf-notes', 'WINDOW-HOLD.txt')):
    print('HOLD exists: stop')
    sys.exit(1)
b = open(os.path.join(R, 'perf-notes', 'SESSION2.md'), 'rb').read()
t = b.decode('utf-8')
print('SESSION2: LF %d, CR %d, splitlines %d, split %d, ends with LF %s' % (
    b.count(b'\n'), b.count(b'\r'), len(t.splitlines()), len(t.split('\n')), b.endswith(b'\n')))
seps = ['\x0b', '\x0c', '\x1c', '\x1d', '\x1e', '\x85', '\u2028', '\u2029', '\r']
for i, l in enumerate(t.split('\n')):
    for s in seps:
        if s in l:
            print('  L%d has %r: %s' % (i + 1, s, l[:120].encode('unicode_escape').decode()))
r = open(os.path.join(R, 'perf-notes', 'agent10-batch2-review.md'), 'rb').read().decode('utf-8', 'replace').split('\n')
print('b2r lines', len(r))
for i, l in enumerate(r):
    if (l.startswith('#') and any(k in l for k in ('37', '38', '39'))) or l.startswith(('| 37 ', '| 38 ', '| 39 ')):
        print('  b2r L%d: %s' % (i + 1, l[:200]))

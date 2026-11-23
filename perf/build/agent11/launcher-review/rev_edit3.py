# rev_edit3.py - REVIEW.md: the CD64BC93 / 3EFC5312 interim (Agent 11, task #10). One-match substitutions, sha gate.
# Usage: python rev_edit3.py [--apply]
import hashlib, sys, shutil, datetime, os
D = r'<workspace>\build\agent11\launcher-review'
P = os.path.join(D, 'REVIEW.md')
GATE = '52BB48354880B3359E59D57AD6065DC9100CF004E67EA83200D0376F3C9054A6'
apply = len(sys.argv) > 1 and sys.argv[1] == '--apply'
b = open(P, 'rb').read()
h = hashlib.sha256(b).hexdigest().upper()
if h != GATE:
    print('GATE FAIL', h); sys.exit(1)
t = b.decode('utf-8')
if '\r' in t:
    print('CR in file'); sys.exit(1)
sec = open(os.path.join(D, 'rev3-section.md'), 'rb').read().decode('utf-8')
if '\r' in sec or not sec.endswith('\n\n'):
    print('section file: CR or bad ending'); sys.exit(1)
row1 = ('| p-2114 (21:13:38) | run-night.ps1 | CD64BC93017083B1190CA6AB858E60A1956A1B2DE02588D4EAA20031A1AD439C | '
        '71,763 B, 944 LF lines, ASCII, no BOM, ParseFile 0 errors. Copy and checks: [p-2114-CD64BC93](p-2114-CD64BC93/). '
        'Diff v3→CD64: +138/-41, read in full. Interim read below |\n')
row2 = ('| p-2119 (21:15:40) | run-night.ps1 | 3EFC5312D0982E77D0F92D154D54EB063D9495A63812432113DEE65859630E5C | '
        '72,276 B, 948 LF lines, ASCII, no BOM, ParseFile 0 errors. Copy and checks: [p-2119-3EFC5312](p-2119-3EFC5312/). '
        'Diff CD64→3EFC: +5/-1 (F1 only). Interim read below |\n')
subs = [
    ('Status: **PRE-READ (20:58, updated 21:03; v3 interim 21:15)**, not yet the formal verdict.',
     'Status: **PRE-READ (20:58, updated 21:03; interims: v3 at 21:15, CD64BC93 and 3EFC5312 at 21:25)**, not yet the formal verdict.'),
    ('\n| (20:53:42) | README.md | 39ECF5C21234B500… |',
     '\n' + row1 + row2 + '| (20:53:42) | README.md | 39ECF5C21234B500… |'),
    ("## Verdict so far: SAFE once Agent 10's (5) driver fix is in\n",
     "## Verdict so far: SAFE (Agent 10's (5) driver fix is in since v3); the formal verdict waits for the final version\n"),
    ('\n## Next (when Agent 5 asks)\n',
     '\n' + sec + '## Next (when Agent 5 asks)\n'),
]
for i, (o, n) in enumerate(subs):
    c = t.count(o)
    if c != 1:
        print('SUB', i, 'count', c); sys.exit(2)
    t = t.replace(o, n)
nb = t.encode('utf-8')
print(('APPLY' if apply else 'DRY OK'), len(subs), 'subs', len(b), '->', len(nb), 'B', t.count('\n'), 'LF')
if apply:
    bk = os.path.join(D, 'REVIEW.%s-%s.md' % (datetime.datetime.now().strftime('%H%M'), GATE[:8]))
    shutil.copyfile(P, bk)
    open(P, 'wb').write(nb)
    print('new sha', hashlib.sha256(open(P, 'rb').read()).hexdigest().upper(), 'backup', os.path.basename(bk))

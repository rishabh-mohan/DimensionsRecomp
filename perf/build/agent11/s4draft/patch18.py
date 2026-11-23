# -*- coding: utf-8 -*-
# patch18.py - apply patch18.txt (one-match substring edits) to run18.py and fnd5.py, for Agent 8's revised wording in
# W6.md (06:39) and W4c.md (06:40). Each file is written only if every pair matches exactly once; a timestamped .bak is kept.
import datetime, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'<workspace>'
D = os.path.join(ROOT, 'build', 'agent11', 's4draft')
if os.path.exists(os.path.join(ROOT, 'perf-notes', 'WINDOW-HOLD.txt')):
    sys.exit('HOLD exists: stop')
txt = open(os.path.join(D, sys.argv[1] if len(sys.argv) > 1 else 'patch18.txt'), 'rb').read().decode('utf-8').replace('\r\n', '\n')
pairs, cur, mode, buf, old = {}, None, None, [], None
for ln in txt.split('\n'):
    if mode is None:
        if ln.startswith('@@ '):
            cur = ln[3:].strip(); pairs.setdefault(cur, [])
        elif ln == '<<<':
            mode, buf = 'old', []
        elif ln.strip():
            sys.exit('bad line: ' + ln[:60])
    elif mode == 'old':
        if ln == '===':
            old, buf, mode = '\n'.join(buf), [], 'new'
        else:
            buf.append(ln)
    else:
        if ln == '>>>':
            pairs[cur].append((old, '\n'.join(buf))); mode = None
        else:
            buf.append(ln)
if mode is not None:
    sys.exit('unterminated block')
stamp = datetime.datetime.now().strftime('%H%M')
for fn, pl in pairs.items():
    p = os.path.join(D, fn); b = open(p, 'rb').read(); t = b.decode('utf-8'); bad = 0
    for i, (o, n) in enumerate(pl):
        c = t.count(o)
        if c != 1:
            print('FAIL %s pair %d matches %d: %r' % (fn, i + 1, c, o[:70])); bad += 1; continue
        t = t.replace(o, n)
    if bad:
        print('NOT written: %s (%d bad pairs)' % (fn, bad)); continue
    bk = '%s.%s.bak' % (p, stamp)
    if os.path.exists(bk):
        print('NOT written: backup exists ' + bk); continue
    open(bk, 'wb').write(b); nb = t.encode('utf-8'); open(p, 'wb').write(nb)
    print('patched %s: %d pairs, %d -> %d B, backup %s' % (fn, len(pl), len(b), len(nb), os.path.basename(bk)))

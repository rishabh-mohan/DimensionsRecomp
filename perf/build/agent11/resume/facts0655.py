# -*- coding: utf-8 -*-
# facts0655.py - read-only fact gathering for RESUME draft 2. Writes build/agent11/resume/facts-0655.txt.
import glob, os, re, sys, datetime
ROOT = r'<workspace>'
if os.path.exists(os.path.join(ROOT, 'perf-notes', 'WINDOW-HOLD.txt')):
    sys.exit('HOLD exists: stop')
out = []
def P(s=''):
    out.append(s)
def lines(rel):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return None
    b = open(p, 'rb').read()
    if b[:2] in (b'\xff\xfe', b'\xfe\xff'):
        t = b.decode('utf-16', errors='replace')
    else:
        t = b.decode('utf-8', errors='replace')
    t = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '?', t)
    return re.split(r'\r\n|\n|\r', t)
def rng(rel, a, b=None):
    L = lines(rel)
    P('=== %s L%d-%s' % (rel, a, b if b else 'end'))
    if L is None:
        P('  MISSING'); return
    b = b or len(L)
    for i in range(a, min(b, len(L)) + 1):
        P('%d: %s' % (i, L[i - 1]))
def grep(rel, pat, ctx=0, maxn=40):
    L = lines(rel)
    P('=== grep %r in %s' % (pat, rel))
    if L is None:
        P('  MISSING'); return
    n = 0
    for i, l in enumerate(L, 1):
        if re.search(pat, l):
            for j in range(max(1, i - ctx), min(len(L), i + ctx) + 1):
                P('%d: %s' % (j, L[j - 1][:600]))
            n += 1
            if n >= maxn:
                P('  (max hits)'); break
    P('  hits: %d' % n)
def ls(pat):
    P('=== ls %s' % pat)
    for p in sorted(glob.glob(os.path.join(ROOT, pat))):
        st = os.stat(p)
        P('  %s  %d B  %s' % (os.path.relpath(p, ROOT), st.st_size, datetime.datetime.fromtimestamp(st.st_mtime).strftime('%m-%d %H:%M:%S')))
P('generated ' + datetime.datetime.now().strftime('%H:%M:%S'))
S2 = 'perf-notes/SESSION2.md'
L = lines(S2); P('SESSION2 lines: %d' % len(L))
rng(S2, 3126, 3133)
rng(S2, 3318)
rng('perf-notes/agent10-batch2-review.md', 2466, 2485)
rng('build/agent9/cg26-check/README.md', 1, 20)
for a, b in ((14, 19), (39, 39), (332, 334)):
    rng('bench/agent8/run/run-matrix.ps1', a, b)
for a, b in ((7, 7), (16, 16), (157, 157), (192, 194)):
    rng('bench/agent5/launch/README.md', a, b)
grep('build/agent9/s4-t1-preread.md', r'NoCold', 1)
grep('build/agent10/t27/r21-s4t1.md', r'1-3|1–3|value 3|=3|EcoQoS', 0)
grep('perf-notes/S4-DRAFT.md', r'LEGO_NATIVE_CHAIN_PRIORITY', 0)
grep('perf-notes/RESUME.md', r'LEGO_NATIVE_CHAIN_PRIORITY|#21', 0)
ls('build/agent3/runs/rp*')
ls('build/agent3/runs/rp*/*.txt')
ls('build/agent3/s4b/logs/f10*.check.txt')
for p in sorted(glob.glob(os.path.join(ROOT, 'build/agent3/s4b/logs/f10*.check.txt'))):
    rng(os.path.relpath(p, ROOT).replace('\\', '/'), 1, 14)
ls('build/agent3/s4b/*.md')
ls('build/agent8/readout/w-followup/*.md')
ls('build/agent8/readout/w-followup/mine/*.md')
ls('build/agent8/readout/w-followup/a7/*.md')
ls('build/agent7/*')
ls('build/agent10/t27/*')
ls('build/agent5/scrnsave-fix/*')
ls('build/agent2/devoff4b-cg26-bin*')
rng('build/agent5/scrnsave-fix/install-log.txt', 1)
open(os.path.join(ROOT, 'build', 'agent11', 'resume', 'facts-0655.txt'), 'wb').write('\n'.join(out).encode('utf-8'))
print('wrote facts-0655.txt, %d lines' % len(out))

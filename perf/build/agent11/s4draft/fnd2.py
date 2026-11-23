# -*- coding: utf-8 -*-
# fnd2.py - FINDINGS-AND-CHANGES.md finding 10 update for task #10 (Agent 11): tonight's runs, Agent 6's
# mechanism (message 22:52, build/agent6/hang/cp-state-s4b24-s4b20.md) and the after-S4 candidate.
# Usage: python fnd2.py --dry | --apply. One-match edit, sha + line gates, hashed backup, LF, no BOM.
import datetime, difflib, hashlib, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'<workspace>'
P = lambda r: os.path.join(ROOT, *r.split('/'))
F, HOLD = P('perf-notes/FINDINGS-AND-CHANGES.md'), P('perf-notes/WINDOW-HOLD.txt')
DRY, APPLY = '--dry' in sys.argv, '--apply' in sys.argv
if DRY == APPLY:
    sys.exit('usage: fnd2.py --dry | --apply')
sha = lambda b: hashlib.sha256(b).hexdigest().upper()
fails = []
def fail(m):
    fails.append(m); print('FAIL:', m)
if os.path.exists(HOLD):
    sys.exit('HOLD exists: stop')
raw = open(F, 'rb').read(); H0 = sha(raw)
print('findings %s %d B %d LF' % (H0[:8], len(raw), raw.count(b'\n')))
if not H0.startswith('CD160A60') or raw.count(b'\n') != 365 or b'\r' in raw or raw.startswith(b'\xef\xbb\xbf'):
    sys.exit('findings gate FAIL')
old = raw.decode('utf-8')
s2 = open(P('perf-notes/SESSION2.md'), 'rb').read().decode('utf-8').split('\n')
def S(n, *subs):
    for s in subs:
        if s not in s2[n - 1]:
            fail('SESSION2 L%d lacks %r' % (n, s))
S(2927, '1244 memexport syncs, against 5-62 normally'); S(2990, '(8 clang++)')
S(3010, '**C1 OFF**', '**same** STUCK-LOCK'); S(3012, "the 83FAF200 variant of finding 10 isn't caused by C1")
S(3081, '4 of 13 runs tonight (w6gA, s4b24, s4b20, w6gB), all recovered, all under the -j8 build')
S(3108, "W6's timed runs are title + attract only"); S(3112, 'W6 does not test finding 10')
S(3114, 'CheckSubmissionFence', 'WaitForSingleObject(fence_completion_event_, INFINITE)', 'no rexgpu symbols')
S(3116, 'render tid 0x17 holds CS 0x84959EDC while polling a fence'); S(3118, 'The 5 s detector needs a slow CP')
S(3119, 'All 3 hangs Agent 6 analysed happened under the -j8 build')
S(3120, 'two untimed vpad L-route rows on the quiet host', 'slow_frame_log_ms=1'); S(3121, "s4b20's set (C1 OFF)")
S(3122, "w6gB's set (p2fc)"); S(3124, 'memexport readback full-path sync')
for f in ('build/agent6/hang/cp-state-s4b24-s4b20.md', 'build/agent6/hang/cp-state-gateA.md'):
    if not os.path.exists(P(f)):
        fail('missing ' + f)
ADD = '\n'.join([
 "- **Tonight's runs and the likely mechanism (Agent 6, 22:52; `build/agent6/hang/cp-state-s4b24-s4b20.md`, gate A: `cp-state-gateA.md`):** 4 of 13 functional runs hit it (w6gA, s4b24, s4b20, w6gB). All recovered, and all ran while an 8-job build kept the PC at 100 % (SESSION2 L2990, L3081). From the gate A, s4b24 and s4b20 crash dumps (function names inferred; the GPU backend has no symbols): the render thread holds the graphics lock while it polls a GPU fence, and the main thread waits for that lock. Meanwhile the GPU command thread is in a draw that reads memexport data back, and on that path it ends the submission and waits, with no timeout, until the GPU has finished every draw before it. So the 5 s report fires whenever the GPU command thread is slow: verify mode in gate A, a starved PC in all three, or very many of these syncs (L3114-3119). It needs neither verify nor C1: s4b20 had both off (L3010-3012). It hasn't been seen on a quiet PC. Tonight's timing windows run the title and attract screens only, so they don't test it; the direct test is two untimed level runs on the quiet PC after the last window, one with C1 off and one with it on (L3108, L3112-3123).",
 "- **Possible speedup after S4 (Agent 6):** the readback's fast path skips the wait only when the other slot's submission has already finished, so same-key draws inside one submission alternate between the fast and the full path. When the GPU runs behind, nearly every such draw takes the full path: a submit, a round trip, a wake-up and a second copy. Gate A's 9.7 s frame logged 1244 of these syncs, against 5-62 normally (L2927). It isn't measured at normal speed yet; the quiet-PC level runs will give the counts (L3120, L3124).",
])
new = old
def line(name, prefix, fn):
    global new
    L = new.split('\n'); ix = [i for i, l in enumerate(L) if l.startswith(prefix)]
    if len(ix) != 1:
        fail('line %s matches %d' % (name, len(ix))); return
    L[ix[0]] = fn(L[ix[0]]); new = '\n'.join(L); print('line', name, 'L%d' % (ix[0] + 1))
line('f10', "- **For S4 (proposals, off by default):** the fix for the standard path's busy-waiting wait loop", lambda l: l + '\n' + ADD)
nb = new.encode('utf-8')
if b'\r' in nb:
    fail('CR')
print('new %d B, %d LF (+%d)' % (len(nb), nb.count(b'\n'), nb.count(b'\n') - raw.count(b'\n')))
if nb.count(b'\n') != 367:
    fail('expected 367 LF')
ol, nl = old.split('\n'), new.split('\n'); dry = []
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=ol, b=nl, autojunk=False).get_opcodes():
    if tag != 'equal':
        dry.append('=== %s old L%d-%d -> new L%d-%d' % (tag, i1 + 1, i2, j1 + 1, j2))
        dry += ['--- %d: %s' % (i + 1, ol[i]) for i in range(i1, i2)] + ['+++ %d: %s' % (j + 1, nl[j]) for j in range(j1, j2)]
        print(dry[-1 - (i2 - i1) - (j2 - j1)])
T = datetime.datetime.now().strftime('%H%M'); BK = 'FINDINGS-AND-CHANGES.%s-%s.md' % (T, H0[:8])
if DRY:
    open(P('build/agent11/s4draft/fnd2-dry.txt'), 'wb').write(('\n'.join(dry) + '\n').encode('utf-8'))
    print('DRY: %d failures' % len(fails)); sys.exit(1 if fails else 0)
if fails or os.path.exists(HOLD):
    sys.exit('not written')
bk = P('build/agent11/s4draft/' + BK)
if os.path.exists(bk) or sha(open(F, 'rb').read()) != H0:
    sys.exit('backup exists or findings changed')
open(bk, 'wb').write(raw)
open(F, 'wb').write(nb); chk = open(F, 'rb').read()
print('WROTE sha256 %s %d B %d LF CR %d; backup %s' % (sha(chk), len(chk), chk.count(b'\n'), chk.count(b'\r'), BK))

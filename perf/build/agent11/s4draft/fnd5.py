# -*- coding: utf-8 -*-
# fnd5.py - FINDINGS-AND-CHANGES under task #25 (Nov 23), pass A: Agent 8's W6 and W4c read-outs, Agent 12's gates, Agent 6's logdiffs,
# Agent 3's quiet-PC rows, Agent 5's screensaver fix, the cross-window caveat and #30's state.
# Usage: python fnd5.py --dry | --apply. One-match edits, sha + line gates, source string checks, hashed backup, LF, no BOM.
import datetime, difflib, hashlib, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'<workspace>'
P = lambda r: os.path.join(ROOT, *r.split('/'))
DOC, HOLD = P('perf-notes/FINDINGS-AND-CHANGES.md'), P('perf-notes/WINDOW-HOLD.txt')
DRY, APPLY = '--dry' in sys.argv, '--apply' in sys.argv
if DRY == APPLY:
    sys.exit('usage: fnd5.py --dry | --apply')
sha = lambda b: hashlib.sha256(b).hexdigest().upper()
fails = []
def fail(m):
    fails.append(m); print('FAIL:', m)
if os.path.exists(HOLD):
    sys.exit('HOLD exists: stop')
raw = open(DOC, 'rb').read(); H0 = sha(raw)
print('findings %s %d B %d LF' % (H0[:8], len(raw), raw.count(b'\n')))
if not H0.startswith('FC702231') or raw.count(b'\n') != 404 or b'\r' in raw or raw.startswith(b'\xef\xbb\xbf'):
    sys.exit('findings gate FAIL')
old = raw.decode('utf-8')
def SRC(rel, *subs):
    if not os.path.isfile(P(rel)):
        fail('missing ' + rel); return
    t = open(P(rel), 'rb').read().decode('utf-8')
    for s in subs:
        if s not in t:
            fail('%s lacks %r' % (rel, s))
SRC('build/agent8/readout/w-followup/W6.md', 'the paired median frame time is **−10.3 % [−13.6, −6.9]**', 'fps is **+18.0 % [+14.1, +22.0]**',
    'CPU is **−0.249 cores [−0.303, −0.195]**', 'p2fc − p2f was negative in **10 of 10 rounds**', '**p2 and p2f have no timing effect.**',
    '**The pass-2 tail comes from an episode that hit all four arms, not from p2fc.**', 'It hit every arm, and the medians stayed in line.', "**The episode's cause is unknown.**",
    'frames of 4.5 ms or more have a median +2.9 % [+2.3, +3.5]', "Agent 7's p99 is +1.7 % [+0.9, +2.6]", 'C1 alone is untested.',
    'A verify-on build might give back part of the gain.', 'W4b and W5 (`build/agent8/matrix/20261122-1541`, `20261122-1756`) ran on the **best_efficiency** overlay and **before** the Defender exclusion',
    '**Cause: GPU warm-up (audit §5.5).**', 'the GPU ran above its steady clock in the first runs', "Almost every other run sat at 832 MHz, the GPU's thermal limit", 'warm the GPU before scoring, since tonight its clock settled only after 5-13 min of game load.', 'Also rotate the first arm across rounds.', '**Lead: at steady state this host looks GPU-limited.**', 'a change that only saves CPU would show up as fewer cores rather than more fps')
SRC('build/agent8/readout/w-followup/W4c.md', '**+2.6 % [−1.2, +6.5]** (B was lower in 1 of 6 rounds)', 'fps is **−1.7 % [−4.9, +1.7]**',
    'CPU is **+0.063 cores [−0.007, +0.133]**', "Don't adopt B for performance.", 'It is neutral or slightly slower and uses slightly more CPU (both leads).')
SRC('build/agent12/w6-gates/NIGHT-RESULTS.md', '## Verdicts: all 7 windows PASS', '**The timed runs are clean.**', '**W5 ran under `best_efficiency`.**')
SRC('build/agent6/wnight/RESULTS.md', '**No FAIL in any of the 7 dirs (135 runs).**', '0 STUCK-LOCK, 0 dumps;', 'are exactly the switch proof lines')
SRC('build/agent3/f10/RESULTS.md', '**No hang on a quiet host.**', 'This is n = 1 per set.', 'The worst frame was 2.89 s in f10b and 1.79 s in f10a.',
    '4.9-8.0 s (gate B, same set as f10b) and 12.0 s (s4b20, same set as f10a), and all four of those runs hung',
    'took 0.29-0.98 ms on the quiet host and 1.79-6.05 ms under the build', "f10b's 2736-sync frames still cost 2.66-2.89 s on the quiet host",
    "**f10a's set (M1, C1 off) never makes the 2736-sync bursts.**", '**The starved host, not the GPU, stretched the stall.**', 'about 8 busy threads')
SRC('build/agent5/scrnsave-fix/README.md', 'Result, 23 Nov 06:14:40: **45/45 PASS**', 'after Agent 8 (owner of run-matrix.ps1) and Agent 10 have read this delta')
SRC('build/agent10/t27/scrnsave-delta.md', '**Verdict: SAFE.** Install it with `install-scrnsave.ps1`')
cm = open(P('DimensionsRecomp/rexlego/CMakeLists.txt'), 'rb').read().decode('utf-8').split('\n')
if 'LEGODIMENSIONS_SCENE_WALK_PROBE' not in cm[158] or 'FATAL_ERROR' not in (cm[160] + cm[161]):
    fail('rexlego/CMakeLists.txt L159-162 not as expected')
if os.path.exists(P('DimensionsRecomp/rexlego/src/scene_walk_probe.cpp')):
    fail('scene_walk_probe.cpp exists now')
print('checks done')
T = datetime.datetime.now().strftime('%H:%M'); BK = 'FINDINGS-AND-CHANGES.%s-%s.md' % (T.replace(':', ''), H0[:8])
U = '<workspace>/'
CMP = ("**Comparing with older windows.** Last night's windows ran on the best-performance power overlay, after the Defender exclusion for `build` "
       "was added; W4b and W5 ran on best-efficiency, before it. So compare arms within a window; absolute numbers don't carry over to W4b, W5 or "
       "older windows. Agent 8 also found that each window's first scored run was unusually fast: after the idle gap the graphics chip was still cool and ran above its steady, heat-limited speed for the first 5 to 13 minutes. That makes the measured gains a little smaller, so "
       "future windows should warm the chip up with throw-away runs first and rotate which arm goes first. Once warm, this PC looks limited by its graphics chip (a lead), so a change that only saves CPU time would show up as lower CPU use rather than more fps.")
LOCK = ("**The stuck game lock (finding 10) on a quiet PC.** Agent 3 ran two level runs on the quiet PC this morning: one with C1 off and one with "
        "P2 + fix (i) + C1. Neither hung. Their slowest frames took 1.8 and 2.9 s, against 4.9-12 s, and a hang in all four runs, under last night's "
        "8-job build. That's one run per set, and the margin is modest; a second pair runs this morning.")
Q10 = ("- **The quiet-PC test (Nov 23, Agent 3, `build/agent3/f10/RESULTS.md`): no hang.** With the same sync bursts, each host-to-GPU round trip "
       "took 0.3-1.0 ms on the quiet PC against 1.8-6.1 ms under the build, so the busy host, not the GPU, stretched the stalls. P2 + fix (i) + C1's "
       "biggest bursts (2736 syncs in one frame) still took 2.7-2.9 s, so a busier or slower PC could push one past the 5 s detector; the set with C1 "
       "off never makes those bursts. One run per set; a second pair runs this morning, and a controlled-load repeat and a loaded s4b20-style row are "
       "offered.")
CHK = ("- This morning's checks: [gates](" + U + "build/agent12/w6-gates/NIGHT-RESULTS.md) (Agent 12), [logdiffs](" + U +
       "build/agent6/wnight/RESULTS.md) (Agent 6), the read-outs [W6](" + U + "build/agent8/readout/w-followup/W6.md) and [W4c](" + U +
       "build/agent8/readout/w-followup/W4c.md) (Agent 8), the [quiet-PC rows](" + U + "build/agent3/f10/RESULTS.md) (Agent 3) and the [screensaver fix](" +
       U + "build/agent5/scrnsave-fix/README.md) (Agent 5)")
new = old
def sub(name, o, n):
    global new
    c = new.count(o)
    if c != 1:
        fail('sub %s matches %d' % (name, c)); return
    new = new.replace(o, n); print('sub', name)
def line(name, prefix, fn):
    global new
    L = new.split('\n'); ix = [i for i, l in enumerate(L) if l.startswith(prefix)]
    if len(ix) != 1:
        fail('line %s matches %d' % (name, len(ix))); return
    L[ix[0]] = fn(L[ix[0]]); new = '\n'.join(L); print('line', name, 'L%d' % (ix[0] + 1))
sub('title', "(as of Nov 23, 06:02: the night's windows are done", "(as of Nov 23, @T@: the night's windows are done")
sub('alert', "The numbers below are Agent 1's runner summaries from the night; the formal read-outs (Agents 7 and 8) land this morning and may change them.",
    "The W6 and W4c rows below are Agent 8's formal read-outs; the W9 and W5b rows are still Agent 1's runner summaries, until their read-outs land.")
sub('night', "the builds unchanged. Second-pass figures are in brackets:",
    "the builds unchanged. Agent 12's checks passed all 7 windows, and Agent 6 found no failure in the 135 runs' logs: no stuck lock, no crash dump, "
    "and no new log line beyond each switch's own proof line. In the W9 and W5b rows, second-pass figures are in brackets:")
sub('w6', "| **P2 + fix (i) + C1 (verification off): frame time −11.8% [−14%], fps +21% [+22%], 0.22 [0.27] core less**, faster in all 10 rounds. P2 "
    "alone and fix (i) alone: no change. The slowest 0.1% of frames was a bit slower (6.49 vs 5.74 ms in the second pass), which the read-out checks | keep it |",
    "| **Agent 8's formal read-out (both passes): P2 + fix (i) + C1 (verification off) cuts frame time by 10% (95% interval 7 to 14%), with fps +18% "
    "and 0.25 core less.** All of it comes from C1, which was faster than P2 + fix (i) alone in 10 of 10 rounds; P2 alone and fix (i) alone change "
    "nothing. The slower 0.1% tail in the second pass came from a short spell of slow frames that hit every arm (its cause wasn't recorded), not from C1. A lead: frames over 4.5 ms may "
    "be 2-3% slower. Not timed yet: C1 alone, and C1 with verification on | keep it |")
sub('w4c', "| B: frame time +1.3%, fps −0.4%, slower in 5 of 6 rounds. W4b's +6% fps hint didn't come back. No second pass (skipped for the wrap-up) | drop B |",
    "| **Agent 8's formal read-out: no gain.** Frame time +2.6% (95% interval −1.2 to +6.5%), fps −1.7%, slightly more CPU; B was faster in only 1 "
    "of 6 rounds. W4b's +6% fps hint didn't come back on last night's settings. No second pass (skipped for the wrap-up) | drop B |")
line('cmp', "So the night's only frame-time win is C1 (with P2 and fix (i)).", lambda l: l + '\n\n' + CMP)
sub('fix', "Agents 5 and 8 stage the proper fix this morning, reviewed by Agents 8 and 10, before the launcher is used again.",
    "Agent 5 has staged the proper fix; all 45 of its tests pass, and Agent 10 rated it safe. It goes in after the launcher exits at 07:30, once Agent 8 has read "
    "it, and before the launcher is used again.\n\n" + LOCK)
sub('after', "the formal read-outs settle the four leans;", "the W9 and W5b read-outs settle the last two leans;")
line('q10', '- **Possible speedup after S4 (Agent 6):** the readback', lambda l: l + '\n' + Q10)
sub('s4b30', "the render-thread busy-wait back-off (#24) and the scene-walk probe (#30). Every new switch is off,",
    "the render-thread busy-wait back-off (#24) and the build option for the scene-walk probe (#30; the probe's own code isn't written yet, so the "
    "option stays off). Every new switch is off,")
line('src', '- Restart doc: [RESUME.md]', lambda l: l + '\n' + CHK)
for tok, val in (('@T@', T),):
    if tok in old:
        fail('token %s in doc' % tok)
    new = new.replace(tok, val)
def bad_rows(t):
    out, L, i = set(), t.split('\n'), 0
    while i < len(L):
        if L[i].startswith('|'):
            h, j = L[i].count('|'), i
            while j < len(L) and L[j].startswith('|'):
                if L[j].count('|') != h: out.add(L[j])
                j += 1
            i = j
        else:
            i += 1
    return out
if bad_rows(new) - bad_rows(old):
    fail('table pipe counts changed')
nb = new.encode('utf-8')
if b'\r' in nb or '@T@' in new:
    fail('CR or token left')
print('new %d B, %d LF (+%d)' % (len(nb), nb.count(b'\n'), nb.count(b'\n') - raw.count(b'\n')))
if nb.count(b'\n') != 410:
    fail('expected 410 LF')
ol, nl = old.split('\n'), new.split('\n'); dry = []
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=ol, b=nl, autojunk=False).get_opcodes():
    if tag != 'equal':
        dry.append('=== %s old L%d-%d -> new L%d-%d' % (tag, i1 + 1, i2, j1 + 1, j2))
        dry += ['--- %d: %s' % (i + 1, ol[i]) for i in range(i1, i2)] + ['+++ %d: %s' % (j + 1, nl[j]) for j in range(j1, j2)]
        print(dry[-1 - (i2 - i1) - (j2 - j1)])
if DRY:
    open(P('build/agent11/s4draft/fnd5-dry.txt'), 'wb').write(('\n'.join(dry) + '\n').encode('utf-8'))
    print('DRY: %d failures' % len(fails)); sys.exit(1 if fails else 0)
if fails or os.path.exists(HOLD):
    sys.exit('not written')
bk = P('build/agent11/s4draft/' + BK)
if os.path.exists(bk) or sha(open(DOC, 'rb').read()) != H0:
    sys.exit('backup exists or doc changed')
open(bk, 'wb').write(raw)
open(DOC, 'wb').write(nb); chk = open(DOC, 'rb').read()
print('WROTE sha256 %s %d B %d LF CR %d; backup %s' % (sha(chk), len(chk), chk.count(b'\n'), chk.count(b'\r'), BK))

# -*- coding: utf-8 -*-
# fnd4.py - FINDINGS-AND-CHANGES under task #25 (Nov 23): a top section for the break (the night's windows from Agent 1's runner
# summaries, the commits, what's next), history labels on the session-3 sections, an S4 batch entry and sources. SESSION2 L3202-3313.
# Usage: python fnd4.py --dry | --apply. One-match edits, sha + line gates, hashed backup, LF, no BOM.
import datetime, difflib, hashlib, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'<workspace>'
P = lambda r: os.path.join(ROOT, *r.split('/'))
DOC, HOLD = P('perf-notes/FINDINGS-AND-CHANGES.md'), P('perf-notes/WINDOW-HOLD.txt')
DRY, APPLY = '--dry' in sys.argv, '--apply' in sys.argv
if DRY == APPLY:
    sys.exit('usage: fnd4.py --dry | --apply')
sha = lambda b: hashlib.sha256(b).hexdigest().upper()
fails = []
def fail(m):
    fails.append(m); print('FAIL:', m)
if os.path.exists(HOLD):
    sys.exit('HOLD exists: stop')
raw = open(DOC, 'rb').read(); H0 = sha(raw)
print('findings %s %d B %d LF' % (H0[:8], len(raw), raw.count(b'\n')))
if not H0.startswith('7635F766') or raw.count(b'\n') != 367 or b'\r' in raw or raw.startswith(b'\xef\xbb\xbf'):
    sys.exit('findings gate FAIL')
old = raw.decode('utf-8')
s2 = open(P('perf-notes/SESSION2.md'), 'rb').read().decode('utf-8').split('\n')
d4 = open(P('perf-notes/S4-DRAFT.md'), 'rb').read()
if not sha(d4).startswith('1B0BB0DC'):
    fail('S4-DRAFT is not 1B0BB0DC')
d4 = d4.decode('utf-8')
def S(n, *subs):
    for s in subs:
        if n > len(s2) or s not in s2[n - 1]:
            fail('SESSION2 L%d lacks %r' % (n, s))
def D(*subs):
    for s in subs:
        if s not in d4:
            fail('S4-DRAFT lacks %r' % s)
S(3203, 'The user double-clicked RUN-NIGHT.cmd at 23:47:19')
S(3215, '**00:03:40 GO refused:**')
S(3216, "removed HKCU\\Control Panel\\Desktop SCRNSAVE.EXE (it was '')", 'which throws when the value is missing')
S(3217, 'Dry runs never change the screensaver, so the 40/40 tests could not catch this.')
S(3218, 'Fix at 00:05:37', 'ScreenSaveActive stays 0, so the screensaver is still None')
S(3223, '21/21 OK, 20 scored, 0 excluded', 'Gate STRICT (MsMpEng 0.00); bins unchanged')
S(3225, '**p2fc 2.16 ms (466 fps, 2.28 cores): -11.8 % median frame time, +21 % fps, -0.22 core vs s0.**')
S(3228, 'P2 alone and fix (i) alone show no change.')
S(3236, 'fps unchanged (+1 %), median -6 %')
S(3237, 'q500 4.62 / 5.52 ms (off 4.98 / 5.63)')
S(3247, '**d11p (precise) 2.50 / 385 / 2.34 (-0.20 core, -8 %).**')
S(3256, '**B 2.50 / 383.9 / 2.60: median +1.3 %, fps -0.4 %, +0.07 core.**')
S(3257, 'B was slower in 5 of 6 rounds and tied in 1.')
S(3258, "**W4b's B +6.0 % fps hint did not repeat:**")
S(3266, '**W6-2 (03:13:22-03:56:11, 42.8 min):**')
S(3270, '**p2fc 2.13 / 469.8 / 2.26 [2.16 / 466 / 2.28]: median -14 %, fps +22 %, -0.27 core vs s0.')
S(3271, 'so 10 of 10 over both passes')
S(3272, 'p99.9 6.49 vs 5.74', 'whether fix (i) or C1 adds rare slow frames')
S(3273, "is tonight's only frame-time win", "W9's back-off and W5b's wait modes save CPU only.")
S(3282, 'p99 4.68 vs 4.99')
S(3283, 'q125 and q250 were less steady this pass:')
S(3287, 'Over both passes q500 saves the most CPU (0.70-0.79 core) with no fps loss')
S(3291, '**W5b-2 (04:51:58-05:30:42, 38.7 min):**')
S(3295, '-0.21 core (-8 %), fps unchanged.**')
S(3296, 'd11p kept fps in both passes; d11t lost 0.8 % this pass. Lean: d11p.')
S(3297, 'a break of a few days to a week is coming')
S(3298, '**W4c second pass skipped**')
S(3301, 'Readouts: Agents 7 and 8 (formal, both passes)')
S(3304, 'Agents 5 and 8: stage the screensaver/StrictMode fix; install it after the launcher exits at 07:30.')
S(3308, 'both public forks')
S(3309, 'Commits on perf/opt, pushed to mine without force: rexglue-sdk 5350b1d', 'DimensionsRecomp b0bd3b4')
S(3310, 'Third-party worktree changes stay uncommitted.', 'plume via tools/gpu-aot/prepare_plume.py', 'simde via rexglue-sdk/scripts/prepare_simde.py')
S(3311, 'Notes/scripts/results are not pushed.', 'will ask the user when they wake')
S(3312, 'SCRNSAVE fix staged and installed after 07:30 (5; reviews by 8 and 10)', 'screenshot kit (4)')
S(3198, '**#1 screenshot check: Monday**')
D("the noise band is ±19.6% (d0's run spread)", 'the noise band is ±20.4%', '2.91 cores (−15%)',
  'every arm is within the noise band, and d11t and d11p use ~0.4 core (~13%) less game CPU',
  'SAFE from me (22:31) and from Agent 10 (22:33', 'The launcher set froze at 23:24:43',
  'At 19:47 Agent 10 rated the folded S4b + S4c compose check PASS, SAFE to build, landing OFF',
  'three independent applies give the same 16 files, 13 SDK and 3 game', '**S4a landed live at 14:56 and is committed**',
  '#7, #8, #5 and #38 OFF, #32 always on (output-identical, b2r §27) and #2 OFF on native4',
  "every staged S4b item is rated (C1 v3, M1, #18/#20 step 1, P2's counter and #26",
  "codegen option `db16cyc_pause`, default OFF", 'CMake option `LEGODIMENSIONS_SCENE_WALK_PROBE`')
for f in ('DimensionsRecomp/tools/gpu-aot/prepare_plume.py', 'DimensionsRecomp/rexglue-sdk/scripts/prepare_simde.py'):
    if not os.path.isfile(P(f)):
        fail('missing ' + f)
for d in ('0009', '0108', '0155', '0239', '0313', '0401', '0451'):
    if not os.path.isdir(P('build/agent8/matrix/20261123-' + d)):
        fail('no results folder 20261123-' + d)
print('checks done')
T = datetime.datetime.now().strftime('%H:%M'); BK = 'FINDINGS-AND-CHANGES.%s-%s.md' % (T.replace(':', ''), H0[:8])
U = '<workspace>/'
TOP = '\n'.join([
 "## Before the break (Nov 23)",
 "",
 "> [!IMPORTANT]",
 "> **The project pauses from ~13:00 today for a few days to a week.** Start again from [RESUME.md](" + U + "perf-notes/RESUME.md): "
 "what's committed, the results, the decisions still open and the next steps. The full plan and its history are in [S4-DRAFT.md](" + U +
 "perf-notes/S4-DRAFT.md). The numbers below are Agent 1's runner summaries from the night; the formal read-outs (Agents 7 and 8) land this "
 "morning and may change them.",
 "",
 "**What's committed.** `perf/opt` now holds S4a and the S4b + S4c build, with every new switch off by default: rexglue-sdk `5350b1d` and "
 "DimensionsRecomp `b0bd3b4`, pushed to your forks without force. The plume and simde edits stay uncommitted; "
 "`DimensionsRecomp/tools/gpu-aot/prepare_plume.py` and `DimensionsRecomp/rexglue-sdk/scripts/prepare_simde.py` rebuild them from tracked "
 "patches. The notes, scripts and results aren't pushed yet; Agent 1 will ask you where they should go.",
 "",
 "**Last night's windows.** You double-clicked RUN-NIGHT at 23:47. Agent 5's launcher ran four windows from 00:09 to 03:06, then a second "
 "pass of W6, W9 and W5b from 03:13 to 05:31. Every run in every window was OK, on the uncapped title screen, with the quiet gate strict and "
 "the builds unchanged. Second-pass figures are in brackets:",
 "",
 "| Window | What it compared | Result | Lean |",
 "|---|---|---|---|",
 "| W6 | The upload path on the S4b build: P2, fix (i) and the re-upload fix C1 | **P2 + fix (i) + C1 (verification off): frame time −11.8% "
 "[−14%], fps +21% [+22%], 0.22 [0.27] core less**, faster in all 10 rounds. P2 alone and fix (i) alone: no change. The slowest 0.1% of "
 "frames was a bit slower (6.49 vs 5.74 ms in the second pass), which the read-out checks | keep it |",
 "| W9 | The render thread's busy-wait back-off (#24) at four sleep sizes | **500 µs: 0.70-0.79 core less (−28 to −31%)**, fps +1%, and the "
 "slowest 1% of frames a bit faster. 125 and 250 µs save a little less and were unsteady in the second pass | 500 µs |",
 "| W5b | The timer thread's wait modes | **Precise wait: 0.20 [0.21] core less, fps unchanged in both passes.** The blocking wait saves "
 "about the same but lost 0.8% fps in the second pass | precise |",
 "| W4c | Codegen B against batch 2, again | B: frame time +1.3%, fps −0.4%, slower in 5 of 6 rounds. W4b's +6% fps hint didn't come back. "
 "No second pass (skipped for the wrap-up) | drop B |",
 "",
 "So the night's only frame-time win is C1 (with P2 and fix (i)). The back-off and the precise timer wait save CPU without changing the "
 "frame rate.",
 "",
 "**One hiccup.** The first GO was refused at 00:03: the launcher had deleted the screensaver's empty `SCRNSAVE.EXE` registry value instead "
 "of leaving it empty, and the runner's strict check failed on the missing value. The tests couldn't catch this, because dry runs never "
 "touch the screensaver. Agent 1 put the empty value back at 00:05 (the screensaver stayed off), and the night ran as planned. Agents 5 and "
 "8 stage the proper fix this morning, reviewed by Agents 8 and 10, before the launcher is used again.",
 "",
 "**Since session 3** (Nov 22; details in S4-DRAFT):",
 "- Window 4 (W4b, 15:41-16:17) and W5 (17:56-18:29): no frame-time change cleared the noise band (±19.6% and ±20.4%), but the timer "
 "settings cut the game's CPU by ~0.4-0.5 core.",
 "- S4a went live and was committed at 14:56. The S4b + S4c build (C1 v3, the back-off #24 and more, all off) was built that evening, "
 "checked by Agent 3's functional runs, and is now committed too.",
 "- Agents 10 and 11 rated Agent 5's night launcher SAFE (22:31-22:33). It froze at 23:24 and ran last night's windows.",
 "",
 "**Your answers on file:** the Toy Pad tags, yes (17:27); the Defender exclusion, added (23:16; comparisons with W4b, W5 and older windows "
 "carry a caveat); the native screenshot check, yes (it was planned for an hour today, so it moves to after the break; Agent 4 stages the "
 "kit); the pop-in opt-in, yes, off by default. Still open: the simde patch (question 2 below) and where the notes go.",
 "",
 "**After the break** (details in RESUME.md): the formal read-outs settle the four leans; then W7 (#19), the native windows W8a and W8b "
 "(#21), the codegen window (CG26), the pop-in opt-in (#33), your screenshot check (#1), a confirmation window, the keep/drop calls, a final "
 "build with the kept switches on by default, and the write-up. On a new, faster PC, the baselines have to be measured again first.",
 ""])
T1 = ("**Newer windows:** W4b and W5 (Nov 22) and last night's W6, W9, W5b and W4c are summarized in the top section, with the full numbers "
      "in S4-DRAFT (\"Changed since 23:29\" and \"Changed since 15:54\"). Window 3 and matrix 1 below ran before the Windows Update of Nov 22, "
      "so compare them with later windows only with that caveat.")
S4B = '\n'.join([
 "",
 "### S4a, S4b and S4c: committed on `perf/opt` (Nov 22-23)",
 "- **S4a** (live and committed at 14:56 on Nov 22): the upload-hash diagnostic (#7), P2 (#8), fix (i) (#5) and the precise timer wait "
 "(#38), all off; the warm-boot pipeline fix (#32), always on, because Agent 10 rated it output-identical; and on native builds the "
 "miss-cache stopgap (#2), off.",
 "- **S4b + S4c** (built on the evening of Nov 22, committed on Nov 23 as rexglue-sdk `5350b1d` and DimensionsRecomp `b0bd3b4`): the "
 "re-upload fix C1 v3 with its counter and log line, P2's fallback counter, the non-temporal upload copy M1 (#11), the submit split (#18) "
 "and the deferred-command-list counters (#20 step 1), the codegen pause option (#26; the CG26 build turns it on), the render-thread busy-wait "
 "back-off (#24) and the scene-walk probe (#30). Every new switch is off, and Agent 10 rated the combined change SAFE to build, landing off. "
 "16 files: 13 in the SDK and 3 in the game.",
 "- The switch names, their defaults and the lean for each are in RESUME.md."])
SRC = ("- Restart doc: [RESUME.md](" + U + "perf-notes/RESUME.md). Last night's results: [20261123-0009](" + U + "build/agent8/matrix/20261123-0009) "
       "(W6), [-0108](" + U + "build/agent8/matrix/20261123-0108) (W9), [-0155](" + U + "build/agent8/matrix/20261123-0155) (W5b), [-0239](" + U +
       "build/agent8/matrix/20261123-0239) (W4c), [-0313](" + U + "build/agent8/matrix/20261123-0313) (W6, second pass), [-0401](" + U +
       "build/agent8/matrix/20261123-0401) (W9, second pass) and [-0451](" + U + "build/agent8/matrix/20261123-0451) (W5b, second pass)")
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
sub('title', '# Perf sprint: findings and changes (as of 12:50, session 3 resumed after a Windows Update restart)\n',
    '# Perf sprint: findings and changes (as of Nov 23, @T@: the night\'s windows are done, and the project pauses for a break)\n')
sub('w4head', '\n## Next: timing window 4 (still ready after the restart)\n',
    '\n' + TOP + '\n## Window 4 as planned (it ran on Nov 22, 15:41-16:17; kept for the record)\n')
sub('qhead', "### Questions for you (window 4 doesn't wait on them)\n", '### Questions for you (1, 3, 4 and 5 are answered; 2 is open)\n')
sub('where', '\n## Where things stand\n', '\n## Where things stood at 12:50 on Nov 22 (session 3; for today, see the top section)\n')
sub('leads', '\n## Leads for the next round (S4, forming overnight)\n',
    '\n## Leads for the next round (S4, as of the morning of Nov 22; their current state is in S4-DRAFT and RESUME.md)\n')
line('t1', '### 1. In-game timing', lambda l: l + '\n\n' + T1)
line('s4b', '- Items still to be profiled first:', lambda l: l + '\n' + S4B)
line('src', '- Session log: [SESSION2.md]', lambda l: l + '\n' + SRC)
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
if nb.count(b'\n') != 404:
    fail('expected 404 LF')
ol, nl = old.split('\n'), new.split('\n'); dry = []
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=ol, b=nl, autojunk=False).get_opcodes():
    if tag != 'equal':
        dry.append('=== %s old L%d-%d -> new L%d-%d' % (tag, i1 + 1, i2, j1 + 1, j2))
        dry += ['--- %d: %s' % (i + 1, ol[i]) for i in range(i1, i2)] + ['+++ %d: %s' % (j + 1, nl[j]) for j in range(j1, j2)]
        print(dry[-1 - (i2 - i1) - (j2 - j1)])
if DRY:
    open(P('build/agent11/s4draft/fnd4-dry.txt'), 'wb').write(('\n'.join(dry) + '\n').encode('utf-8'))
    print('DRY: %d failures' % len(fails)); sys.exit(1 if fails else 0)
if fails or os.path.exists(HOLD):
    sys.exit('not written')
bk = P('build/agent11/s4draft/' + BK)
if os.path.exists(bk) or sha(open(DOC, 'rb').read()) != H0:
    sys.exit('backup exists or doc changed')
open(bk, 'wb').write(raw)
open(DOC, 'wb').write(nb); chk = open(DOC, 'rb').read()
print('WROTE sha256 %s %d B %d LF CR %d; backup %s' % (sha(chk), len(chk), chk.count(b'\n'), chk.count(b'\r'), BK))

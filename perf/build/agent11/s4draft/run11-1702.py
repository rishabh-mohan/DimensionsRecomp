# -*- coding: utf-8 -*-
# run11.py - S4-DRAFT pass for board-run-2 task #35 (Agent 11): W4b's result, the order from W5 on,
# the 3-mode slow-state script. Usage: python build\agent11\s4draft\run11.py --dry | --apply
# --dry writes nothing. --apply takes a hashed backup first, then writes the draft (LF, no BOM).
import datetime
import difflib
import hashlib
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'<workspace>'


def P(rel):
    return os.path.join(ROOT, *rel.split('/'))


DRAFT = P('perf-notes/S4-DRAFT.md')
HOLD = P('perf-notes/WINDOW-HOLD.txt')
DRY = '--dry' in sys.argv
APPLY = '--apply' in sys.argv
if DRY == APPLY:
    print('usage: run11.py --dry | --apply')
    sys.exit(2)

# Set before applying.
CHECK = "Its check against W4b's runs is pending."
WAIT = "W5 (the user's double-click) and its read-out, the S4b + S4c build, and Agent 5's ask for the launcher review."

fails = []


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def fail(m):
    fails.append(m)
    print('FAIL:', m)


def die(m):
    print('FAIL:', m)
    sys.exit(1)


if os.path.exists(HOLD):
    die('perf-notes/WINDOW-HOLD.txt exists: stop')

raw = open(DRAFT, 'rb').read()
H0 = sha(raw)
print('draft %s… %d B, %d lines' % (H0[:8], len(raw), raw.count(b'\n')))
if not H0.startswith('14C2A482'):
    die('draft is not 14C2A482')
if raw.count(b'\n') != 476:
    die('draft line count')
if b'\r' in raw or raw.startswith(b'\xef\xbb\xbf'):
    die('draft CR/BOM')
old = raw.decode('utf-8')

# ---------------------------------------------------------------- source checks
s2raw = open(P('perf-notes/SESSION2.md'), 'rb').read()
S2H = sha(s2raw)
s2 = s2raw.decode('utf-8').split('\n')
S2N = len(s2raw.decode('utf-8').splitlines())
print('SESSION2 %s… %d lines' % (S2H[:8], S2N))


def S(n, *subs):
    line = s2[n - 1] if n - 1 < len(s2) else ''
    for s in subs:
        if s not in line:
            fail('SESSION2 L%d lacks %r' % (n, s))


S(2600, 'At 16:00, unless W4b has started: Agent 2 builds B4, then S4b with C1 v3.')
S(2605, '16:35 Agent 1: W4b done', '15:41-16:17', 'd11t saves ~15 % CPU')
S(2607, '20261122-1541', 'WinSta0\\Default', '17/17 OK', '1 shared cold run + 4 Latin-square rounds')
S(2608, 'title screen, uncapped', 'median of run medians', 'ref d0 = devoff2', '±19.6 %', "d0's run spread")
S(2612, '| d0 devoff2 |', '3.40 (3.07..3.73)', '| ref |', '10.73', '239.7', '3.44')
S(2613, '| B devoffB |', '3.23 (2.88..3.53); 3.03 without run 6', '−4.9 %; −10.8 % without run 6', '10.50', '255.1', '3.35')
S(2614, '| d3 devoff3 |', '3.21 (2.89..4.26)', '−5.4 %', '10.49', '248.9', '3.38')
S(2615, '| d11t devoff2 + timer bundle + blocking wait |', '3.36 (3.02..3.86)', '−1.1 %', '10.94', '237.7', '2.91 (−15 %)')
S(2617, 'no frame-time change clears the noise band', 'd11t holds frame time with ~0.5 core less CPU')
S(2618, '1551-B-r2', 'valid_timing=False', '3 clang++ processes', "most likely Agent 9's #22 syntax checks",
  "FUNCTIONAL ONLY banner", 'The read-out recomputes without it.')
S(2624, 'never read_file or write_file outside the workspace', 'WINDOW-HOLD.txt')
S(2625, 'read-out (Agent 8, with Agents 7 and 6)', 'W5 on the S3d line', "B's gain isn't significant",
  'the S3d line needs no build', 'B4 deferred',
  'S4b on the S3d line with C1 v3 and S4c folded in, so the native re-pin happens once')
S(2627, '16:46 Agent 1: W5 promoted (S3d line)', "double-click")
S(2630, 'RUN-WINDOW5-S3D.cmd` 5467F1BE', 'matrix-window5-s3d.json` 4D7D689B')
S(2631, '1 cold run + 3 rotated rounds (base, s0, d11, d11t, d11p), 16 runs, ~37 min')
S(2632, 'build/agent1/w5/W5-INPUTS-1642.txt')
S(2635, "If it hasn't started by 17:10, the S4b build goes first and W5 moves to the overnight launcher (Agent 5).")


def fh(rel):
    b = open(P(rel), 'rb').read()
    return sha(b), b


h, _ = fh('bench/agent8/RUN-WINDOW5-S3D.cmd')
if not h.startswith('5467F1BE'):
    fail('RUN-WINDOW5-S3D.cmd is %s' % h[:8])
h, _ = fh('bench/agent8/run/matrix-window5-s3d.json')
if not h.startswith('4D7D689B'):
    fail('matrix-window5-s3d.json is %s' % h[:8])
h, _ = fh('build/agent1/w5/W5-INPUTS-1642.txt')
print('W5-INPUTS-1642.txt %s…' % h[:8])
h, rd = fh('build/agent8/readout/w5-draft/README.md')
rdl = rd.decode('utf-8', 'replace').split('\n')
rd3 = [i + 1 for i, l in enumerate(rdl) if '3-mode' in l.lower()]
print('w5-draft README %s…, 3-mode lines %s, 14:23 lines %s' % (
    h[:8], rd3, [i + 1 for i, l in enumerate(rdl) if '14:23' in l]))
if not rd3:
    fail('README has no 3-mode line')
if not any('14:23' in l for l in rdl):
    fail('README has no 14:23')
RDL = ', L' + ', L'.join(str(n) for n in rd3) if rd3 else ''
P1H, p1 = fh('bench/agent11/timerq_slowstate.ps1')
m1 = datetime.datetime.fromtimestamp(os.path.getmtime(P('bench/agent11/timerq_slowstate.ps1')))
print('timerq_slowstate.ps1 %s… %d B, %d lines, mtime %s' % (P1H[:8], len(p1), p1.count(b'\n'), m1))
if m1 >= datetime.datetime(2026, 11, 22, 15, 41):
    fail('the original slow-state script changed after W4b started')
if b'REX_TIMER_WAIT_BLOCKING' not in p1:
    fail('original lacks REX_TIMER_WAIT_BLOCKING')
P3H, p3 = fh('bench/agent11/timerq_slowstate_3mode.ps1')
print('timerq_slowstate_3mode.ps1 %s… %d B, %d lines, CR %d' % (P3H[:8], len(p3), p3.count(b'\n'), p3.count(b'\r')))
if any(c > 127 for c in p3) or p3.startswith(b'\xef\xbb\xbf'):
    fail('3-mode script is not ASCII')
if b"'TimerQueue: precise wait (timer_queue_precise_wait)'" not in p3:
    fail('3-mode script lacks the precise line')

# ---------------------------------------------------------------- text
T = datetime.datetime.now().strftime('%H:%M')
BK = 'S4-DRAFT.%s-%s.md' % (T.replace(':', ''), H0[:8])

NEWBLOCK = '\n'.join([
    '**Changed since 15:54** (board-run-2 task #35, @T@; the 15:54 version is kept in `build/agent11/s4draft/@BK@`):',
    "- **W4b is done** (SESSION2 16:35, L2605-2618): the user's double-click ran it at 15:41-16:17 (`build/agent8/matrix/20261122-1541`, on WinSta0\\Default), 17 of 17 runs OK (1 shared cold run + 4 Latin-square rounds). Title screen, uncapped; medians of run medians, against d0 = devoff2; the noise band is ±19.6% (d0's run spread):",
    '  - d0 devoff2: 3.40 ms (3.07..3.73), p99 10.73 ms, 239.7 fps, 3.44 cores;',
    '  - B devoffB: 3.23 ms (2.88..3.53), −4.9% (3.03 ms and −10.8% without run 6), p99 10.50 ms, 255.1 fps, 3.35 cores;',
    '  - d3 devoff3: 3.21 ms (2.89..4.26), −5.4%, p99 10.49 ms, 248.9 fps, 3.38 cores;',
    '  - d11t (devoff2 + the timer bundle + the blocking wait): 3.36 ms (3.02..3.86), −1.1%, p99 10.94 ms, 237.7 fps, 2.91 cores (−15%);',
    "  - **no frame-time change clears the noise band, and d11t holds frame time with ~0.5 core less CPU** (Agent 1's verdict before the read-out, L2617). Run 6 (`1551-B-r2`) is invalid (valid_timing=False: 3 clang++ processes, most likely Agent 9's #22 syntax checks), hence summary.md's FUNCTIONAL ONLY banner; the read-out recomputes B without it (L2618). The read-out is Agent 8's, with Agents 7 and 6 (L2625). All of W4b ran after the Windows Update, so it is internally comparable (§2c).",
    "- **The order from W5 on** (Agent 1, task #35, 16:48; SESSION2 L2625 and L2635; §2c): (1) **W5 now**, on the S3d line (B's gain isn't significant and the S3d line needs no build, so B4 is deferred); (2) **the S4b + S4c build**: S4b on the S3d line with C1 v3, with S4c (#24 + #30) folded in; (3) **the functional queue**; (4) **W6 by Agent 5's launcher**; (5) **W7-W10 overnight**, each as its gates pass; (6) **the native re-pin once, on native4b**. If W5 hasn't started by 17:10, the S4b build goes first and W5 moves to Agent 5's overnight launcher (L2635).",
    "- **W5 promoted** (Agent 1, 16:46; L2627-2635): `bench/agent8/RUN-WINDOW5-S3D.cmd` 5467F1BE… with `bench/agent8/run/matrix-window5-s3d.json` 4D7D689B…; PlanOnly: 1 cold run + 3 rotated rounds of base, s0, d11, d11t and d11p, 16 runs, ~37 min; inputs frozen in `build/agent1/w5/W5-INPUTS-1642.txt`. It waits for the user's double-click.",
    "- **S4c's re-pin question is answered:** with S4c folded into the S4b build, native3d and nativeB are re-pinned once, on native4b (L2625; Agent 1, task #35), as the 13:04 plan had it (Still open; §4b).",
    "- **W5's slow-state check uses a new 3-mode copy**, `bench/agent11/timerq_slowstate_3mode.ps1` (@P3H@…, task #35), as Agent 1 decided at 14:23 (`build/agent8/readout/w5-draft/README.md`). A run is precise if its game.log has `TimerQueue: precise wait (timer_queue_precise_wait)` (precise wins: with the cvar on, the env var isn't read), else blocking if env_set names REX_TIMER_WAIT_BLOCKING (presence-only), else spin. It flags a precise cvar without the line, the line without the cvar, env + precise, more than one precise line and a missing game.log, and its per-arm table marks mixed modes. The run selection and slow-state math are the original's. The original, `timerq_slowstate.ps1` (@P1H@…), stays frozen as a W4b read-out input. @CHECK@",
    "- **Launchers:** task #24 (my review of Agent 8's launcher) was cancelled, so the 15:54 list's \"Launcher review\" item is history; I review Agent 5's launcher (`bench/agent5/launch/`, for W6 and the overnight windows) read-only when Agent 5 asks (task #35).",
    '- **Waiting at @T@:** @WAIT@',
    "- Updated: the header; Still open (S4b inputs, S4a, the timed windows and S4c, plus two new items: W5 and Agent 5's launcher); §2b step 5; §2c (the start rule, Before reading fps, W5's and W6's rows and a new \"Order from W5 on\" paragraph); §4b (a 16:35-16:48 answer, the re-pin question and Possible changes); §5 (the slow-state check); and §6 (SESSION2, a11 and W5's files). Fixed: W6's row still said C1 v2; S4b takes v3 (b2r §35).",
]) + '\n\n'

SUBS = [
    ('header',
     'then at 15:54 under task #24 (see "Changed since 14:42").',
     'then at 15:54 under task #24 (see "Changed since 14:42"), then at @T@ under task #35 (see "Changed since 15:54").'),
    ('new list',
     '**Changed since 14:42** (board-run-2 task #24, 15:54;',
     NEWBLOCK + '**Changed since 14:42** (board-run-2 task #24, 15:54;'),
    ('still open heading',
     '**Still open (15:54; updated as inputs land):**',
     '**Still open (@T@; updated as inputs land):**'),
    ('still open S4b',
     "S4b's bases are live since 14:56, and at 16:00, unless W4b has started, Agent 2 builds B4, then S4b with C1 v3 (SESSION2 L2600).",
     "S4b's bases are live since 14:56. W4b ran first, so B4 is deferred (B's gain isn't significant), and S4b is built on the S3d line with C1 v3 and S4c folded in, after W5, or first if W5 hasn't started by 17:10 (SESSION2 L2625 and L2635; Changed since 15:54)."),
    ('still open S4a',
     'Agent 2 built nothing more before W4b (since 15:34: B4, then S4b, at 16:00 unless W4b has started; SESSION2 L2598-2600).',
     'Agent 2 built nothing more before W4b (since 15:34: B4, then S4b, at 16:00 unless W4b has started; SESSION2 L2598-2600; since 16:35 B4 is deferred, and S4b + S4c come after W5, L2625).'),
    ('still open windows',
     "- **Timed windows need the user's double-click** (SESSION2 15:34, L2572-2579): `bench/agent8/RUN-WINDOW4B.cmd`, or Agent 8's launcher `bench/agent8-launch/RUN-W4B-THEN-W5.cmd` (it waits for quiet and readiness, then runs W4b and W5), which I review read-only when it comes (task #24). Agent runs stay functional only (§2c).",
     "- **Timed windows need the user's double-click** (SESSION2 15:34, L2572-2579): W4b ran that way (15:41-16:17, L2605-2607), and W5 waits for it on `bench/agent8/RUN-WINDOW5-S3D.cmd` (promoted 16:46, L2627-2635). W6, and W7-W10 overnight as their gates pass, go through Agent 5's launcher (`bench/agent5/launch/`; Agent 1, task #35), which I review read-only when Agent 5 asks; task #24's review of Agent 8's launcher was cancelled. Agent runs stay functional only (§2c)."),
    ('still open S4c',
     "- **S4c (Agent 1, ~15:35):** #24 + #30 go into an incremental build after S4b (§2a). Open for Agent 1: C1 (S4b) and S4c's CMake edit each change the native fingerprint, so are native3d and nativeB re-pinned after each build, or only after S4c? The 13:04 plan had one re-pin for all three (b2r §26).",
     "- **S4c (Agent 1, ~15:35; answered at 16:35):** #24 + #30 were to go into an incremental build after S4b (§2a). Now S4c is folded into the S4b build on the S3d line, so the native fingerprint changes once, and native3d and nativeB are re-pinned once, on native4b (SESSION2 L2625; Agent 1, task #35), as the 13:04 plan had it (b2r §26)."),
    ('still open new items',
     '- Ratings still missing: see §4b.\n\n**Abbreviations used in the tables:**',
     "- **W5 and its read-out:** W5 waits for the user's double-click (promoted 16:46; ~37 min). Agent 8 reads out W4b with Agents 7 and 6 (SESSION2 L2625); W5's read-out (`build/agent8/readout/w5-draft/`) uses the 3-mode slow-state check (§2b step 5).\n"
     "- **Agent 5's launcher** (`bench/agent5/launch/`; W6, then W7-W10 overnight): my read-only review waits for Agent 5's ask (task #35).\n"
     '- Ratings still missing: see §4b.\n\n**Abbreviations used in the tables:**'),
    ('2b step 5',
     '   - the slow-state check (`bench/agent11/timerq_slowstate.ps1`);',
     "   - the slow-state check (`bench/agent11/timerq_slowstate.ps1`; from W5 on, its 3-mode copy `bench/agent11/timerq_slowstate_3mode.ps1`, which also names each run's timer mode: spin, blocking or precise);"),
    ('2c start rule',
     "only the user's double-click starts a timed window: `bench/agent8/RUN-WINDOW4B.cmd`, or Agent 8's launcher `bench/agent8-launch/RUN-W4B-THEN-W5.cmd`, which waits for the quiet and readiness checks, then runs W4b and W5.",
     "only the user's double-click starts a timed window. W4b ran that way at 15:41-16:17 (SESSION2 L2605), and W5 waits on `bench/agent8/RUN-WINDOW5-S3D.cmd` (promoted 16:46); W6, and W7-W10 overnight as their gates pass, go through Agent 5's launcher (`bench/agent5/launch/`; Agent 1, task #35)."),
    ('2c before fps',
     '   - the slow-state check per run;',
     '   - the slow-state check per run (from W5 on, `bench/agent11/timerq_slowstate_3mode.ps1`; its mode column must match each arm: spin for base, s0 and d11, blocking for d11t, precise for d11p);'),
    ('W5 row',
     "| S4a + §2b passed (done; S4a live 14:56); window 4's result (Agent 8's launcher runs W5 right after W4b, SESSION2 L2578) | base / s0 / d11 / d11t / d11p | 1 cold + 5 × 3 = 16 | ~40 | Is s0 the same as base? What does the blocking wait do alone (d11 vs d11t)? Precise vs blocking? |",
     "| S4a + §2b passed (done; S4a live 14:56); window 4's result (done 16:17: no frame-time change clears the noise band, so W5 runs on the S3d line and B4 is deferred; promoted 16:46 as `bench/agent8/RUN-WINDOW5-S3D.cmd` with `bench/agent8/run/matrix-window5-s3d.json`, inputs frozen in `build/agent1/w5/W5-INPUTS-1642.txt`; SESSION2 L2625-2635) | base / s0 / d11 / d11t / d11p | 1 cold + 5 × 3 = 16 | ~37 | Is s0 the same as base? What does the blocking wait do alone (d11 vs d11t)? Precise vs blocking? Each run's slow state and timer mode from the 3-mode script (§2b step 5) |"),
    ('W6 row',
     'for C1, S4b with C1 v2 and §21 A-D passed | s0 / #8',
     "for C1, S4b with C1 v3 (b2r §35) and §21 A-D passed; started by Agent 5's launcher (Agent 1, task #35) | s0 / #8"),
    ('order paragraph',
     '\n\nOptions already defined in F (L26-33):',
     "\n\n**Order from W5 on** (Agent 1, task #35, 16:48; SESSION2 L2625 and L2635): (1) W5 now, on the S3d line (B4 deferred); (2) the S4b + S4c build: S4b on the S3d line with C1 v3, with S4c (#24 + #30) folded in; (3) the functional queue (my reading: Agent 7's S4b queue, `build/agent7/s4b-queue/`); (4) W6 by Agent 5's launcher; (5) W7-W10 overnight, each once its \"needs first\" column is met; (6) the native re-pin once, on native4b. If W5 hasn't started by 17:10, the S4b build goes first and W5 moves to Agent 5's overnight launcher. Every window from W5 on is after the Windows Update: compare arms within a window, and give the environment caveat above for any comparison with window 3 or earlier."
     '\n\nOptions already defined in F (L26-33):'),
    ('4b decisions',
     "- **~15:35 (task #24):** S4a is live and committed (14:56); S4b takes C1 v3 and leaves #24 + #30 for an incremental S4c (§2a); timed windows start only on the user's double-click (§2c).",
     "- **~15:35 (task #24):** S4a is live and committed (14:56); S4b takes C1 v3 and leaves #24 + #30 for an incremental S4c (§2a); timed windows start only on the user's double-click (§2c).\n"
     "- **16:35-16:48 (SESSION2 L2605-2635; Agent 1, task #35):** W4b is done, with every arm within the noise band (d11t: ~15% less CPU). W5 runs now on the S3d line (B4 deferred); then the S4b + S4c build (S3d line, C1 v3, S4c folded in); then the functional queue; W6 by Agent 5's launcher; W7-W10 overnight as their gates pass; and the native re-pin once, on native4b (§2c). This answers the S4c re-pin question."),
    ('4b re-pin',
     "- **S4c's re-pin (for Agent 1, since ~15:35):** C1 in S4b and #24 + #30's CMake edit in S4c each change the native fingerprint: re-pin native3d and nativeB after each build, or only after S4c? (13:04 planned one re-pin for all three, b2r §26.)",
     "- **S4c's re-pin: answered** (asked ~15:35; SESSION2 L2625; Agent 1, task #35): S4c is folded into the S4b build, so native3d and nativeB are re-pinned once, on native4b, as 13:04 planned (b2r §26)."),
    ('4b possible changes',
     "Since 14:42: #32's gate result, S4a's landing and commits, the S4b/S4c split and the double-click rule (Changed since 14:42).",
     "Since 14:42: #32's gate result, S4a's landing and commits, the S4b/S4c split and the double-click rule (Changed since 14:42). Since 15:54: W4b's result and the order from W5 on (Changed since 15:54). Next: W5's result, read with §2c's environment caveat and the 3-mode slow-state check, and Agent 5's launcher."),
    ('5 slow state',
     "  - A8 runs `timerq_slowstate.ps1` over W4b's fg=1 runs.",
     "  - A8 runs `timerq_slowstate.ps1` over W4b's fg=1 runs (that script stays frozen), and its 3-mode copy `timerq_slowstate_3mode.ps1` over W5's (task #35: spin, blocking or precise, from env_set and the precise line)."),
    ('6 SESSION2',
     'the screensaver and app closures held L2602).',
     "the screensaver and app closures held L2602). Re-read at @T@ (@S2N@ lines, @S2H@…): 16:35 L2605-2625 (W4b's run L2607; the result table L2610-2615; the verdicts L2617; run 6 L2618; agent activity in the window L2619-2623; the fixes and the HOLD file L2624; next L2625); 16:46 L2627-2635 (W5's files L2630; PlanOnly L2631; the frozen inputs L2632; agents idle and the 17:10 rule L2635)."),
    ('6 a11 + W5',
     '`build/agent11/s4a/AGENT3-SPEC.md` (13:28, 1DA33FD3…): the #38 ON smoke spec.',
     "`build/agent11/s4a/AGENT3-SPEC.md` (13:28, 1DA33FD3…): the #38 ON smoke spec. `bench/agent11/timerq_slowstate_3mode.ps1` (@P3H@…, task #35): the 3-mode slow-state check for W5; the original `timerq_slowstate.ps1` (@P1H@…) stays frozen.\n"
     "- **W5** (read at @T@): `bench/agent8/RUN-WINDOW5-S3D.cmd` (5467F1BE…), `bench/agent8/run/matrix-window5-s3d.json` (4D7D689B…; arms, env, cvars and proof lines), `build/agent1/w5/W5-INPUTS-1642.txt` and `build/agent8/readout/w5-draft/README.md` (Agent 1's 14:23 decision on the 3-mode copy@RDL@)."),
]

new = old
for name, o, n in SUBS:
    c = new.count(o)
    if c != 1:
        fail('sub %r matches %d times' % (name, c))
        continue
    ln = new[:new.index(o)].count('\n') + 1
    new = new.replace(o, n)
    print('sub %-22s at L%d' % (name, ln))

TOKENS = [('@T@', T), ('@BK@', BK), ('@S2N@', str(S2N)), ('@S2H@', S2H[:8]), ('@P1H@', P1H[:8]),
          ('@P3H@', P3H[:8]), ('@CHECK@', CHECK), ('@WAIT@', WAIT), ('@RDL@', RDL)]
for tok, val in TOKENS:
    if tok in old:
        fail('token %s already in the draft' % tok)
    new = new.replace(tok, val)
for tok, _ in TOKENS:
    if tok in new:
        fail('token %s left' % tok)


def table_issues(text):
    lines = text.split('\n')
    bad, rows, i = set(), 0, 0
    while i < len(lines):
        if lines[i].startswith('|'):
            hdr = lines[i].count('|')
            j = i
            while j < len(lines) and lines[j].startswith('|'):
                rows += 1
                if lines[j].count('|') != hdr:
                    bad.add(lines[j])
                j += 1
            i = j
        else:
            i += 1
    return bad, rows


ob, orows = table_issues(old)
nb, nrows = table_issues(new)
if nb - ob:
    fail('table pipe counts: %d new bad rows' % len(nb - ob))
print('table rows: %d before, %d after; uneven rows before %d, after %d' % (orows, nrows, len(ob), len(nb)))
nbytes = new.encode('utf-8')
if b'\r' in nbytes or nbytes.startswith(b'\xef\xbb\xbf'):
    fail('new text has CR or BOM')
if new.count('**Changed since 15:54**') != 1:
    fail('Changed since 15:54 heading count')
print('new: %d B, %d lines (+%d)' % (len(nbytes), nbytes.count(b'\n'), nbytes.count(b'\n') - raw.count(b'\n')))

# changed line ranges
sm = difflib.SequenceMatcher(a=old.split('\n'), b=new.split('\n'), autojunk=False)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag != 'equal':
        print('  %s old L%d-%d -> new L%d-%d' % (tag, i1 + 1, i2, j1 + 1, j2))

# scan the current-state sections (from **Sources:** on) for items this pass may have missed
KEYS = ['re-pin', 'S4c', "Agent 8's launcher", 'agent8-launch', 'RUN-W4B-THEN-W5', 'B4', 'Launcher review',
        'timerq_slowstate', 'W4B.cmd']
nl = new.split('\n')
start = next(i for i, l in enumerate(nl) if l.startswith('**Sources:**'))
print('scan from L%d:' % (start + 1))
for i in range(start, len(nl)):
    ks = [k for k in KEYS if k in nl[i]]
    if ks:
        p = nl[i].index(ks[0])
        print('  L%d %s: …%s…' % (i + 1, ks, nl[i][max(0, p - 140):p + 140]))

if DRY:
    print('--- new block ---')
    print(new[new.index('**Changed since 15:54**'):new.index('**Changed since 14:42**')])
    print('DRY RUN: %d failures; nothing written' % len(fails))
    sys.exit(1 if fails else 0)

if fails:
    die('%d failures; nothing written' % len(fails))
if os.path.exists(HOLD):
    die('perf-notes/WINDOW-HOLD.txt exists: stop')
bk = P('build/agent11/s4draft/' + BK)
if os.path.exists(bk):
    die('backup exists: ' + bk)
open(bk, 'wb').write(raw)
if sha(open(bk, 'rb').read()) != H0:
    die('backup hash mismatch')
print('backup %s = %s…' % (bk, H0[:8]))
if sha(open(DRAFT, 'rb').read()) != H0:
    die('draft changed during the run')
open(DRAFT, 'wb').write(nbytes)
chk = open(DRAFT, 'rb').read()
print('WROTE S4-DRAFT.md sha256 %s, %d B, %d lines, CR %d, BOM %s' % (
    sha(chk), len(chk), chk.count(b'\n'), chk.count(b'\r'), chk.startswith(b'\xef\xbb\xbf')))

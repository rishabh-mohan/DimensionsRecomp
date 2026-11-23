# -*- coding: utf-8 -*-
# run11.py - S4-DRAFT pass for task #10 (run 2 after the 17:27 agy-grid relaunch; the old board-run-2 #35;
# Agent 11): W4b's result, decision 1, W5's run, the order from W5 on with tonight's targets, and the
# 3-mode slow-state script. The 17:02 version (never applied) is kept as run11-1702.py.
# Usage: python build\agent11\s4draft\run11.py --dry | --apply
# --dry writes only build/agent11/s4draft/run11-dry.txt (the changed lines in full), never the draft.
# --apply takes a hashed backup first, then writes the draft (LF, no BOM).
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
DRYOUT = P('build/agent11/s4draft/run11-dry.txt')
DRY = '--dry' in sys.argv
APPLY = '--apply' in sys.argv
if DRY == APPLY:
    print('usage: run11.py --dry | --apply')
    sys.exit(2)

# Set before applying.
CHECK = ("Its independent check (a subagent, 19:37-19:54; `build/agent11/s4a/slowstate3-check/REPORT.md`, @RPH@…) "
         "PASSES: on W4b the copy gives the original's 17 runs with identical onset, slow share, span and fg (the 4 d11t "
         "runs blocking, the other 13 spin); on W5 the copy and the original agree on all 16 runs (the 3 d11t runs "
         "blocking, the 3 d11p runs precise, the rest spin); neither window has a flag or a mixed arm; a Python recompute "
         "matches all 33 runs in all 13 columns; and synthetic cases produce every mode and flag. It lists seven "
         "edge-case fragilities (for example, the precise-cvar match has no left boundary, the env test is presence-only, "
         "and a long arm name cuts the flags column in the text table, not in the CSV); none is triggered by W4b's or "
         "W5's runs, so the script stays @P3H@… (the result and the list went to Agent 8 at @T@).")
WAIT = ("Agent 8's W5 read-out (task #7), with Agent 6's W5 logdiff (L2757-2761); the S4b + S4c bins (devoff4b "
        "~20:25-20:30, native4b ~21:00, then CTR and CG26); Agent 3's S4b queue (to ~22:50-23:00); Agent 4's native "
        "re-pin on native4b (run-2 task #12); and Agent 5's ask for the launcher review (its RUN-NIGHT.cmd and README "
        "were due ~20:40; the review requests by 21:30, reviewed by ~22:30).")

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
if not H0.startswith('0CB74A52'):
    die('draft is not 0CB74A52')
if raw.count(b'\n') != 476:
    die('draft line count')
if b'\r' in raw or raw.startswith(b'\xef\xbb\xbf'):
    die('draft CR/BOM')
old = raw.decode('utf-8')

# ---------------------------------------------------------------- source checks
s2raw = open(P('perf-notes/SESSION2.md'), 'rb').read()
S2H = sha(s2raw)
s2 = s2raw.decode('utf-8').split('\n')
# count LF lines, as the citations do (splitlines() also breaks at the two U+0085 characters in L1856 and L1860)
S2N = s2raw.count(b'\n') + (0 if s2raw.endswith(b'\n') else 1)
print('SESSION2 %s… %d lines' % (S2H[:8], S2N))


def S(n, *subs):
    line = s2[n - 1] if n - 1 < len(s2) else ''
    for s in subs:
        if s not in line:
            fail('SESSION2 L%d lacks %r' % (n, s))


# cited from the 17:02 version (SESSION2 is append-only)
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
# new since 17:02
S(2637, '17:07 Agent 1: pause for the agy-grid relaunch', 'before W5')
S(2643, "The 17:10 'go' timer (task-627) is cancelled")
S(2647, '17:36 Agent 1: resumed after the agy-grid relaunch', 'decision 1 (Toy Pad tags) = yes')
S(2649, 'Relaunch state (17:27):', 'board reset to run 2')
S(2651, 'W5 inputs re-hashed at 17:31', 'W5-INPUTS-1731.txt', '27/27 identical to W5-INPUTS-1642.txt')
S(2653, 'The user is present for W5', 'double-click `bench/agent8/RUN-WINDOW5-S3D.cmd`')
S(2654, 'Decision 1 (Toy Pad tags): yes', '(user, 17:27)', 'Batman, Gandalf, Wyldstyle', 'hidden-desktop test runs',
  'under the 02:11 harness-only rules', 'user-mode only, no drivers or system-wide installs',
  'never in a staged `build/agent2/*-bin`', 'saves isolated in the run folder', 'builds at <= 2 threads',
  'S4b queue rows 7, 20 and 23 (level loads) are no longer skipped', "C1 ON's verify-mode level load (b2r §21 A) can run")
S(2655, 'the old tasks #25-#35 are re-issued as run-2 tasks')
S(2657, '17:41 Agent 1: run-2 task numbers')
S(2659, '#1 Agent 2 (old #28, S4b + S4c build)', '#2 Agent 3 (old #29, S4b functional queue, Toy Pad rows now in)',
  '#4 Agent 5 (old #27, overnight launcher', '#7 Agent 8 (old #26, W4b/W5 read-outs, W6 promotion)',
  '#9 Agent 10 (old #34, compose-check rating, launcher safety read)',
  '#10 Agent 11 (old #35, S4-DRAFT + FINDINGS decision 1, 3-mode script, launcher review)')
S(2662, '17:52 Agent 1: quiet gate NOT QUIET after 20 min; W5 starts anyway', "user's option 1 with its 17:52 fallback")
S(2664, 'all FAIL on Defender alone', 'MsMpEng 0.76-1.14 cores')
S(2667, 'Caveat for the W5 read-out (Agent 8):', 'Defender was steady at ~0.9 core', 'real-time work, no scan')
S(2670, '18:34 Agent 1: W5 done at 18:29')
S(2672, '`build/agent8/matrix/20261122-1756`, 17:56-18:29, 16/16 runs OK, 15 scored, 0 excluding flags',
  'light_share_high', 'no frames over 33 ms', 'run-2 task #7')
S(2674, '| arm | median ms (min..max) | d median | p99 ms | game CPU cores |')
S(2676, '| base (devoff3, S3d) | 2.55 (2.41..2.93) | ref | 7.49 | 3.17 |', '+-20.4 %')
S(2677, '| s0 (devoff4, S4a) | 2.69 (2.52..2.76) | +5.5 % | 7.58 | 3.22 |')
S(2678, '| d11 | 2.61 (2.56..2.62) | +2.6 % | 7.45 | 3.17 |')
S(2679, '| d11t | 2.65 (2.55..3.03) | +4.0 % | 7.84 | 2.74 |')
S(2680, '| d11p | 2.62 (2.58..2.64) | +3.1 % | 7.72 | 2.75 |')
S(2682, 'd11t and d11p use ~0.4 core less game CPU', 'about -13 %', 'at about the same frame time',
  'It holds in all 3 rounds')
S(2684, 'power overlay best_efficiency** in every run', "It's the same for all arms, so the A/B is fair, but it caps absolute speed.")
S(2685, '15 W i7-1255U (2P + 8E, 12 threads)', 'flat at 1.92-1.95 GHz')
S(2686, '~3.0-3.6 logical CPUs per run', "Defender's ~0.9")
S(2687, 'The three slowest runs', 'P threads nearly saturated', 'the lowest E-core clocks',
  "the S4a arms' +3-5 % sits inside that noise")
S(2690, 'Both are fixed in `build/agent1/hold/hold-manager.ps1`')
S(2692, 'Paused (user, 18:21): nothing started after W5.')
S(2694, '19:31 Agent 1: restart after the pause', 'sleeps at 00:00')
S(2696, 'the fixed HOLD manager runs as task-135')
S(2697, "'go' to all agents at 19:31")
S(2699, "Agent 2's S4b + S4c bins ~20:30", "Agent 3's S4b functional queue (Toy Pad rows included) to ~22:50")
S(2700, "Agent 5's launcher ready for review by 21:30 and reviewed by Agents 10 and 11 by ~22:30")
S(2701, 'The user double-clicks `bench/agent5/launch/RUN-NIGHT.cmd` at ~23:45 and leaves the PC')
S(2702, "W6's GO only after Agent 3's queue passes and Agent 8 promotes W6")
S(2703, 'Every timed run starts by 06:45 and ends before 07:30')
S(2704, 'Agent 8** runs the W5 read-out now', 'SESSION2 17:52 and 18:34')
S(2706, '19:35 Agent 1: S4b is a full rebuild', '-j8 (Below Normal)')
S(2708, "C1's xmemory.h reaches all 440 generated TUs in each game tree, plus 199 SDK TUs")
S(2712, 'CTR adds ~10 min after native4b; CG26 comes last.')
S(2713, 'Decision: -j8 at Below Normal.')
S(2714, 'No timed window can start before 00:00', "the launcher's gate also refuses while clang/ninja run")
S(2716, 'devoff4b is staged first, so Agent 3 can start')
S(2717, 'devoff4b ~20:25-20:30 and native4b ~21:00, then CTR, then CG26', "Agent 3's S4b queue runs to ~22:50-23:00",
  'W6 is still on for after 00:00')
# new since the 19:50 dry run
S(2719, '19:42 Agent 1:', 'Agent 4 next: the native re-pin on native4b')
S(2730, "**Agent 4's next task:** the native re-pin, once, on native4b.", 'adapts REPIN.md', 'C1 v3, and #24 in through S4c',
  "after Agent 2's CMake re-run and on the staged native4b-bin",
  "hands the boot check and the identity/n-row matrix to Agent 3's queue", 'No `-Go` without my word',
  "I announce the pin after Agent 3's checks")
S(2732, '19:47 Agent 1: Agent 10 rates the folded S4b + S4c compose check PASS, SAFE to build (landing OFF)',
  'Agent 3 explores the level route')
S(2734, '`build/agent2/s4b-compose-1932-c1v3.txt` 77F0017A', 'b2r row 39 and §38')
S(2735, 'Three independent applies give the same 16 files (13 SDK, 3 game)')
S(2737, '**Gates for the build (relayed to Agent 2):**')
S(2738, 'Land exactly the 16 files and check them by hash, not by exit code.')
S(2739, 'memory_watch.cpp must be 70829846', 'with CRLF')
S(2742, 'A full SDK rebuild plus a codegen-tool rebuild.')
S(2743, "The folded devoff map is devoff4's 27 hooked aliases plus exactly sub_83FBF7D0, sub_83FAF180, sub_83FB09E8 and "
  "sub_83FC0C10 (31)", 'skip_lr stays off')
S(2744, 'One native re-pin on native4b (Agent 4, task #12).')
S(2745, 'snap1 equals S4a plus exactly these 16 files, and the W5 bins (devoff3, devoff4) re-hash unchanged.')
S(2747, '19:43, Agent 3:', '1-3 route-exploration runs for rows 7, 20 and 23 on devoff4-bin', '<= 15 min each',
  '>= 6 GB of RAM free', 'it stops when devoff4b is staged',
  'Nobody has driven the game past the Toy Pad front-end screen yet.')
S(2749, "19:49 Agent 1: Agent 6's run-2 task #5 done (the W4b logdiff is clean)", 'Agent 6 next: the W5 logdiff')
S(2751, '`build/agent8/matrix/20261122-1541`', 'every arm against the 4 warm d0 runs')
S(2752, 'B, d3 and d11t have 0 gate FAIL findings, 0 NEW, 0 MORE and 0 GONE.',
  'All 17 runs exit 0, with no dumps, WER or STUCK.')
S(2753, 'Host timer resolution set to 1 ms (background opt-out on)', 'in 4/4 runs')
S(2754, 'd3-r3 has one benign handle-value difference', 'come from harness timing, not from an arm')
S(2755, 'Two read-only checker subagents confirmed every arm')
S(2756, '`build/agent6/w4b/out-20261122-1541/`', 'The per-arm findings went to Agent 8.')
S(2757, "the same logdiff on W5 (`20261122-1756`) for Agent 8's read-out")
S(2758, 's0 against d11, d11t and d11p (same bin)')
S(2759, 'base against s0 (devoff3 vs devoff4)')
S(2760, 'the cold base run against the warm ones')
S(2761, 'a look at the logs of the three slow runs')
S(2763, '19:55: Agent 5 launcher ETA; Agent 3 exploration run lx1 started')
S(2766, 'run-night.ps1 is 551 lines and parses')
S(2767, 'RUN-NIGHT.cmd and the README are due ~20:40.',
  'All -DryRun tests and the review requests to Agents 10/11 by 21:30; fixes by 23:00.')
S(2768, 'The relaxed MsMpEng gate is in as specified: strict for 30 min after a GO, then ≤1.2 cores with spread ≤0.2 over '
  'the last 3 one-min averages', 'logged as "relaxed gate"')
S(2769, 'W6 draft gets finalized once an S4b bin appears in build/agent2 (none yet).')
S(2770, '`build/agent3/runs/20261122-195210-lx1-devoff4` started 19:52')
S(2771, 'S4b build at -j8 (8 clang++), 8.2 GB RAM free, no HOLD/GO/STOP.')
S(2773, '20:06: PreToolUse hook errors are not a HOLD signal')
S(2777, 'only an existing `perf-notes/WINDOW-HOLD.txt` means a window is running.')


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
for rel in ('build/agent1/w5/W5-INPUTS-1731.txt', 'build/agent8/matrix/20261122-1756/summary.md'):
    if not os.path.exists(P(rel)):
        fail('missing ' + rel)
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
if not P1H.startswith('38A3F6AC'):
    fail('the original slow-state script is not 38A3F6AC')
if b'REX_TIMER_WAIT_BLOCKING' not in p1:
    fail('original lacks REX_TIMER_WAIT_BLOCKING')
P3H, p3 = fh('bench/agent11/timerq_slowstate_3mode.ps1')
print('timerq_slowstate_3mode.ps1 %s… %d B, %d lines, CR %d' % (P3H[:8], len(p3), p3.count(b'\n'), p3.count(b'\r')))
if not P3H.startswith('E9049B33'):
    fail('3-mode script is not E9049B33 (the hash sent to Agent 8)')
if any(c > 127 for c in p3) or p3.startswith(b'\xef\xbb\xbf'):
    fail('3-mode script is not ASCII')
if b"'TimerQueue: precise wait (timer_queue_precise_wait)'" not in p3:
    fail('3-mode script lacks the precise line')
FH, _ = fh('perf-notes/FINDINGS-AND-CHANGES.md')
print('FINDINGS %s…' % FH[:8])
if not FH.startswith('CD160A60'):
    fail('FINDINGS is not CD160A60 (the 19:37 decision-1 state)')
RPH, rp = fh('build/agent11/s4a/slowstate3-check/REPORT.md')
print('slowstate3 REPORT.md %s… %d B, %d lines' % (RPH[:8], len(rp), rp.count(b'\n')))
if not RPH.startswith('B1A6C165'):
    fail("REPORT.md is not B1A6C165 (the subagent's 19:54 report)")
L5D = P('bench/agent5/launch')
if os.path.isdir(L5D):
    f5 = sorted(f for _, _, fs in os.walk(L5D) for f in fs)
    L5 = "`bench/agent5/launch/` exists at @T@ (%s%s); my review waits for Agent 5's ask." % (
        ', '.join('`%s`' % f for f in f5) if f5 else 'empty', '' if 'RUN-NIGHT.cmd' in f5 else '; no `RUN-NIGHT.cmd` yet')
else:
    L5 = "`bench/agent5/launch/` doesn't exist yet at @T@."
print('launch dir:', L5)

# ---------------------------------------------------------------- text
T = datetime.datetime.now().strftime('%H:%M')
BK = 'S4-DRAFT.%s-%s.md' % (T.replace(':', ''), H0[:8])

NEWBLOCK = '\n'.join([
    '**Changed since 15:54** (task #10, run 2 after the 17:27 agy-grid relaunch, = the old board-run-2 task #35; 19:37 and @T@; the 15:54 version is kept in `build/agent11/s4draft/S4-DRAFT.1937-14C2A482.md` and the 19:37 one in `build/agent11/s4draft/@BK@`):',
    "- **W4b is done** (SESSION2 16:35, L2605-2618): the user's double-click ran it at 15:41-16:17 (`build/agent8/matrix/20261122-1541`, on WinSta0\\Default), 17 of 17 runs OK (1 shared cold run + 4 Latin-square rounds). Title screen, uncapped; medians of run medians, against d0 = devoff2; the noise band is ±19.6% (d0's run spread):",
    '  - d0 devoff2: 3.40 ms (3.07..3.73), p99 10.73 ms, 239.7 fps, 3.44 cores;',
    '  - B devoffB: 3.23 ms (2.88..3.53), −4.9% (3.03 ms and −10.8% without run 6), p99 10.50 ms, 255.1 fps, 3.35 cores;',
    '  - d3 devoff3: 3.21 ms (2.89..4.26), −5.4%, p99 10.49 ms, 248.9 fps, 3.38 cores;',
    '  - d11t (devoff2 + the timer bundle + the blocking wait): 3.36 ms (3.02..3.86), −1.1%, p99 10.94 ms, 237.7 fps, 2.91 cores (−15%);',
    "  - **no frame-time change clears the noise band, and d11t holds frame time with ~0.5 core less CPU** (Agent 1's verdict before the read-out, L2617). Run 6 (`1551-B-r2`) is invalid (valid_timing=False: 3 clang++ processes, most likely Agent 9's #22 syntax checks), hence summary.md's FUNCTIONAL ONLY banner; the read-out recomputes B without it (L2618). The read-out is Agent 8's, with Agents 7 and 6 (L2625). All of W4b ran after the Windows Update, so it is internally comparable (§2c).",
    "  - **Agent 6's W4b logdiff is clean** (19:49, L2749-2756): against the 4 warm d0 runs, B, d3 and d11t have 0 gate FAIL findings, 0 NEW, 0 MORE and 0 GONE; all 17 runs exit 0, with no dumps, WER or STUCK; the only d11t-only line is the required \"Host timer resolution set to 1 ms (background opt-out on)\", in 4 of 4 runs; d3-r3's one handle-value difference is benign, and the Toypad 8-vs-10 line counts come from harness timing, not from an arm. Two read-only checker subagents confirmed every arm; the output is in `build/agent6/w4b/out-20261122-1541/`, and the per-arm findings went to Agent 8.",
    "- **Decision 1 = yes** (the user, 17:27; SESSION2 L2654), recorded at 19:37 by `build/agent11/s4draft/dec1.py`: Agent 3 may use generated virtual Toy Pad tags (Batman, Gandalf, Wyldstyle) in its hidden-desktop test runs, under the 02:11 harness-only rules (user-mode only, no drivers or system-wide installs, never in a staged `build/agent2/*-bin`, saves isolated in the run folder, builds at ≤ 2 threads). S4b queue rows 7, 20 and 23 (level loads) are in, and C1 ON's verify-mode level load (b2r §21 A) can run. Edited then: §4a item 1, Decisions item 3, §2b fix (i), rows 4 and 24, and FINDINGS Q1 (L127) with its Leads C1 row (L155).",
    "- **The order from W5 on** (Agent 1, 16:48, re-issued in task #10; SESSION2 L2625, L2694-2717; §2c): (1) **W5**: the user's double-click after the 17:27 resume ran it at 17:56-18:29 (below); (2) **the S4b + S4c build** (run-2 task #1, Agent 2): S4b on the S3d line with C1 v3 and S4c (#24 + #30) folded in, B4 deferred (B's gain isn't significant). It is a full rebuild (C1's `xmemory.h` reaches all 440 generated TUs in each game tree, plus 199 SDK TUs), so at 19:35 Agent 1 raised Agent 2's cap to -j8 at Below Normal: devoff4b ~20:25-20:30, native4b ~21:00, then CTR, then CG26 (L2706-2717; the 19:31 target was ~20:30, L2699). At 19:47 Agent 10 rated the folded S4b + S4c compose check PASS, SAFE to build, landing OFF (`build/agent2/s4b-compose-1932-c1v3.txt`: three independent applies give the same 16 files, 13 SDK and 3 game; b2r row 39, §38; Agent 9's S4c package itself was rated landing OFF SAFE at ~16:20, b2r row 38, §37), with five gates for the build: the 16 files landed and checked by hash (memory_watch.cpp with CRLF), a full SDK and codegen-tool rebuild, the folded devoff map at exactly 31 hooked aliases with skip_lr off, one native re-pin on native4b, and snap1 = S4a plus the 16 files, with the W5 bins re-hashing unchanged (L2732-2745); (3) **the functional queue**: Agent 3's S4b queue (run-2 task #2, Toy Pad rows in), from devoff4b on, to ~22:50-23:00 (L2699, L2716-2717); until devoff4b is staged, Agent 3 may do 1-3 route-exploration runs for rows 7, 20 and 23 on devoff4-bin (hidden desktop, functional only, ≤ 15 min each, with ≥ 6 GB of RAM free; nobody has driven the game past the Toy Pad front-end screen yet; L2747; the first, lx1, started at 19:52, L2770); (4) **W6 by Agent 5's launcher**: the user double-clicks `bench/agent5/launch/RUN-NIGHT.cmd` at ~23:45 and leaves the PC; no timed window starts before 00:00 (the launcher's gate also refuses while clang/ninja run); W6's GO comes only after Agent 3's queue passes and Agent 8 promotes W6 (L2701-2702, L2714); (5) **W7-W10 overnight**, each as its gates pass; every timed run starts by 06:45 and ends before 07:30 (L2703); (6) **the native re-pin once, on native4b**, by Agent 4 (run-2 task #12, since 19:42): it adapts REPIN.md and its two draft matrices to native4b (C1 v3, #24 in through S4c), runs dry-run checks after Agent 2's CMake re-run and on the staged native4b-bin, and hands the boot check and the identity/n-row matrix to Agent 3's queue; no `-Go` without Agent 1's word, and Agent 1 announces the pin after Agent 3's checks (L2730, L2744). The 16:46 fallback (the S4b build first if W5 hadn't started by 17:10, L2635) lapsed: the 17:07 pause cancelled the 17:10 timer (L2643), and W5 ran after the resume.",
    "- **W5 is done** (SESSION2 18:34, L2670-2692): promoted at 16:46 (`bench/agent8/RUN-WINDOW5-S3D.cmd` 5467F1BE… with `bench/agent8/run/matrix-window5-s3d.json` 4D7D689B…; 1 cold run + 3 rotated rounds of base, s0, d11, d11t and d11p, 16 runs; inputs frozen in `build/agent1/w5/W5-INPUTS-1642.txt`, identical again at 17:31; L2627-2635, L2651). It started although the quiet gate failed on Defender alone (~0.9 core of real-time work, no scan; the user's option 1 with its 17:52 fallback, L2662-2668), and ran at 17:56-18:29 into `build/agent8/matrix/20261122-1756`: 16 of 16 runs OK, 15 scored, 0 excluding flags (only the info flag light_share_high), no frames over 33 ms (L2672). Agent 1's quick look (median ms with the runs' min..max, against base = devoff3 on the S3d line; the noise band is ±20.4%):",
    '  - base (devoff3, S3d): 2.55 ms (2.41..2.93), p99 7.49 ms, 3.17 cores;',
    '  - s0 (devoff4, S4a): 2.69 ms (2.52..2.76), +5.5%, p99 7.58 ms, 3.22 cores;',
    '  - d11: 2.61 ms (2.56..2.62), +2.6%, p99 7.45 ms, 3.17 cores;',
    '  - d11t: 2.65 ms (2.55..3.03), +4.0%, p99 7.84 ms, 2.74 cores;',
    '  - d11p: 2.62 ms (2.58..2.64), +3.1%, p99 7.72 ms, 2.75 cores;',
    "  - **every arm is within the noise band, and d11t and d11p use ~0.4 core (~13%) less game CPU at about the same frame time**, in all 3 rounds (L2674-2682). Every run had the power overlay best_efficiency (the same for all arms, so the A/B is fair, but it caps absolute speed); the 15 W i7-1255U's P-cores were flat at 1.92-1.95 GHz; the non-game load was ~3.0-3.6 logical CPUs per run, Defender's ~0.9 included; and the three slowest runs are the three with the P threads nearly saturated and the lowest E-core clocks, so the S4a arms' +3-5% sits inside that noise (L2684-2687). The formal read-out is Agent 8's (run-2 task #7; its inputs are SESSION2 17:52 and 18:34, L2704), with the 3-mode slow-state check (next item), Agent 6's W5 logdiff (s0 against d11, d11t and d11p; base against s0; the cold run against the warm ones; the three slow runs' logs; L2757-2761) and the Defender caveat (L2667). All of W5 ran after the Windows Update, like W4b (§2c).",
    "- **W5's slow-state check: the 3-mode copy is ready**, `bench/agent11/timerq_slowstate_3mode.ps1` (@P3H@…), as Agent 1 decided at 14:23 (`build/agent8/readout/w5-draft/README.md`@RDL@); its path went to Agent 8 at 19:40. A run is precise if its game.log has `TimerQueue: precise wait (timer_queue_precise_wait)` (precise wins: with the cvar on, the env var isn't read), else blocking if env_set names REX_TIMER_WAIT_BLOCKING (presence-only), else spin. It flags a precise cvar without the line, the line without the cvar, env + precise, more than one precise line and a missing game.log, and its per-arm table marks mixed modes. The run selection and slow-state math are the original's; the original, `timerq_slowstate.ps1` (@P1H@…), stays frozen as a W4b read-out input. A 19:34 fix: PS 5.1's automatic table view stops at 10 columns, which hid span_s, fg and flags, so the columns are now named. My runs (not the read-out): on W5, the cold run, base, s0 and d11 are spin, d11t blocking and d11p precise, with 0 flags and no mixed arm; all 15 scored runs reach the slow state (the cold run doesn't); mean onset d11p 2 s, d11t 6, d11 14, s0 21, base 38; mean slow share base 50.2%, s0 60.5, d11 65.3, d11t 74.8, d11p 73.5. Onset tracks run order (later runs reach it sooner in every arm, in W4b too), so it is not an arm effect. On W4b it gives the original's rows (d11t blocking, the rest spin). @CHECK@",
    "- **S4c's re-pin question is answered:** with S4c folded into the S4b build, native3d and nativeB are re-pinned once, on native4b (SESSION2 L2625; Agent 1's order, re-issued in task #10), as the 13:04 plan had it (Still open; §2a's S4c paragraph; §4b). Agent 4 does it (run-2 task #12, since 19:42; L2730, L2744).",
    "- **Launchers:** task #24 (my review of Agent 8's launcher) was cancelled, so the 15:54 list's \"Launcher review\" item is history. W6, and W7-W10 overnight, go through Agent 5's launcher (run-2 task #4; its entry is `bench/agent5/launch/RUN-NIGHT.cmd`, which the user double-clicks at ~23:45): ready for review by 21:30, and reviewed read-only by Agents 10 and 11 by ~22:30 (run-2 tasks #9 and #10; SESSION2 L2659, L2700-2701). At 19:55 Agent 5 reported `run-night.ps1` parsing at 551 lines, with `RUN-NIGHT.cmd` and its README due ~20:40, every -DryRun test and the review requests by 21:30, and fixes by 23:00; its relaxed Defender gate is in: strict for 30 min after a GO, then ≤ 1.2 cores with a spread ≤ 0.2 over the last three one-minute averages, logged as \"relaxed gate\" (L2765-2769). @L5@",
    '- **Waiting at @T@:** @WAIT@',
    "- Updated at @T@: the header; Still open (S4b inputs, with Agent 10's 19:47 rating of the folded compose check; S4a; #24; the timed windows; S4c, with Agent 4's re-pin; plus two new items: W5's read-out and Agent 5's launcher); the W4b abbreviation; row 24; §1g item 10; §2a (S4b's #24 item and its \"whatever is rated\" item, and the S4c paragraph); §2b step 5; §2c (the start rule, Before reading fps, W5's and W6's rows and a new \"Order from W5 on\" paragraph); §4b (five answers from 16:35 to 19:49, the re-pin question and Possible changes); §5 (the slow-state check); and §6 (SESSION2, a11 and W5's files). Fixed: W6's row still said C1 v2; S4b takes v3 (b2r §35). Updated at 19:37 for decision 1: §4a item 1, Decisions item 3, §2b fix (i) and rows 4 and 24.",
]) + '\n\n'

SUBS = [
    ('header',
     'then at 15:54 under task #24 (see "Changed since 14:42").',
     'then at 15:54 under task #24 (see "Changed since 14:42"), then at 19:37 and @T@ under task #10 (run 2 after the 17:27 agy-grid relaunch; the old board-run-2 #35; see "Changed since 15:54").'),
    ('new list',
     '**Changed since 14:42** (board-run-2 task #24, 15:54;',
     NEWBLOCK + '**Changed since 14:42** (board-run-2 task #24, 15:54;'),
    ('still open heading',
     '**Still open (15:54; updated as inputs land):**',
     '**Still open (@T@; updated as inputs land):**'),
    ('still open S4b',
     "S4b's bases are live since 14:56, and at 16:00, unless W4b has started, Agent 2 builds B4, then S4b with C1 v3 (SESSION2 L2600).",
     "S4b's bases are live since 14:56. W4b ran first, so B4 is deferred (B's gain isn't significant); S4b is built on the S3d line with C1 v3 and S4c folded in, so its #24 + #30 parts are back in the one build (SESSION2 L2625). Agent 2 builds it since the 19:31 'go' (run-2 task #1): a full rebuild, at -j8 Below Normal since 19:35, with devoff4b expected ~20:25-20:30 and native4b ~21:00, then CTR, then CG26 (L2697, L2706-2717). At 19:47 Agent 10 rated the folded S4b + S4c compose check PASS, SAFE to build, landing OFF (`build/agent2/s4b-compose-1932-c1v3.txt`, 16 files; b2r row 39, §38), with five gates for the build (L2732-2745; Changed since 15:54)."),
    ('still open S4a',
     'Agent 2 built nothing more before W4b (since 15:34: B4, then S4b, at 16:00 unless W4b has started; SESSION2 L2598-2600).',
     "Agent 2 built nothing more before W4b (since 15:34: B4, then S4b, at 16:00 unless W4b has started; SESSION2 L2598-2600; since 16:35 B4 is deferred, and the S4b + S4c build came after W5, from the 19:31 'go' on, L2625 and L2697)."),
    ('still open #24',
     'since ~15:35 it goes into an incremental S4c with #30, after S4b (Agent 1, task #24; §2a).',
     'since ~15:35 it was to go into an incremental S4c with #30, after S4b (Agent 1, task #24), and since 16:35 S4c is folded into the S4b build, so it lands with #30 and C1 after all (SESSION2 L2625; §2a).'),
    ('still open windows',
     "- **Timed windows need the user's double-click** (SESSION2 15:34, L2572-2579): `bench/agent8/RUN-WINDOW4B.cmd`, or Agent 8's launcher `bench/agent8-launch/RUN-W4B-THEN-W5.cmd` (it waits for quiet and readiness, then runs W4b and W5), which I review read-only when it comes (task #24). Agent runs stay functional only (§2c).",
     "- **Timed windows need the user's double-click** (SESSION2 15:34, L2572-2579): W4b ran that way at 15:41-16:17 (L2605-2607), and W5 at 17:56-18:29, after the 17:27 resume (`bench/agent8/RUN-WINDOW5-S3D.cmd`, promoted 16:46; L2653, L2672). W6, and W7-W10 overnight as their gates pass, go through Agent 5's launcher, `bench/agent5/launch/RUN-NIGHT.cmd`: the user double-clicks it at ~23:45; no timed window starts before 00:00; W6's GO comes only after Agent 3's S4b queue passes and Agent 8 promotes W6; and every timed run starts by 06:45 and ends before 07:30 (L2699-2703, L2714). Agents 10 and 11 review the launcher read-only by ~22:30 (L2700); task #24's review of Agent 8's launcher was cancelled. Agent runs stay functional only (§2c)."),
    ('still open S4c',
     "- **S4c (Agent 1, ~15:35):** #24 + #30 go into an incremental build after S4b (§2a). Open for Agent 1: C1 (S4b) and S4c's CMake edit each change the native fingerprint, so are native3d and nativeB re-pinned after each build, or only after S4c? The 13:04 plan had one re-pin for all three (b2r §26).",
     "- **S4c (Agent 1, ~15:35; answered at 16:35):** #24 + #30 were to go into an incremental build after S4b (§2a). Now S4c is folded into the S4b build on the S3d line, so the native fingerprint changes once, and native3d and nativeB are re-pinned once, on native4b (SESSION2 L2625; Agent 1's order, re-issued in task #10), as the 13:04 plan had it (b2r §26). Agent 4 does it (run-2 task #12, since 19:42; L2730, L2744)."),
    ('still open new items',
     '- Ratings still missing: see §4b.\n\n**Abbreviations used in the tables:**',
     "- **W5's read-out:** W5 ran at 17:56-18:29 (SESSION2 L2670-2692; Changed since 15:54). In Agent 1's quick look every arm is within the noise band, and d11t and d11p use ~0.4 core less game CPU. The formal read-out is Agent 8's (run-2 task #7; `build/agent8/readout/w5-draft/`), with the 3-mode slow-state check (§2b step 5), Agent 6's W5 logdiff (L2757-2761) and the Defender caveat (L2667).\n"
     "- **Agent 5's launcher** (`bench/agent5/launch/RUN-NIGHT.cmd`; W6, then W7-W10 overnight): ready for review by 21:30; Agents 10 and 11 review it read-only by ~22:30; the user double-clicks it at ~23:45 (SESSION2 L2700-2701); at 19:55, its `RUN-NIGHT.cmd` and README were due ~20:40, and fixes by 23:00 (L2767).\n"
     '- Ratings still missing: see §4b.\n\n**Abbreviations used in the tables:**'),
    ('W4b abbreviation',
     "  - W4b = timing window 4 (tonight's runner, `bench/agent8/RUN-WINDOW4B.cmd`; only the user's double-click starts it, on that file or on Agent 8's launcher `bench/agent8-launch/RUN-W4B-THEN-W5.cmd`, §2c).",
     "  - W4b = timing window 4 (`bench/agent8/RUN-WINDOW4B.cmd`; the user's double-click ran it at 15:41-16:17, into `build/agent8/matrix/20261122-1541`; §2c)."),
    ('row 24 status',
     'since ~15:35 in an incremental S4c with #30, after S4b (Agent 1, task #24; §2a); risk medium',
     'since ~15:35 in S4c with #30, which since 16:35 is folded into the S4b build (SESSION2 L2625; §2a); risk medium'),
    ('1g item 10',
     "since ~15:35, #24 + #30 go into S4c after S4b's C1, so that saving holds only if the re-pin waits for S4c (Still open).",
     "since ~15:35, #24 + #30 were to go into S4c after S4b's C1, and since 16:35 S4c is folded into the S4b build, so the saving holds: one re-pin, on native4b (SESSION2 L2625)."),
    ('2a #24 item',
     'since ~15:35 they go into an incremental S4c after S4b instead (Agent 1, task #24; S4c below).',
     'since ~15:35 they were to go into an incremental S4c after S4b (Agent 1, task #24), and since 16:35 S4c is folded into the S4b build, so they land with C1 after all, with one native re-pin, on native4b (SESSION2 L2625; S4c below).'),
    ('2a whatever item',
     '#24 (rated; since ~15:35 in S4c with #30, below, not S4b; at 13:04 it was to land with #30 and C1 for one re-pin, b2r §26)',
     '#24 (rated; with #30 in S4c, which since 16:35 is folded into this build, so it lands with C1 for one re-pin after all, as planned at 13:04, b2r §26; SESSION2 L2625; S4c below)'),
    ('2a S4c head',
     '**S4c: an incremental build after S4b (Agent 1, task #24, ~15:35).**',
     "**S4c: folded into the S4b build since 16:35** (SESSION2 L2625; Agent 1's order, re-issued in task #10; at ~15:35 it was to be an incremental build after S4b, Agent 1, task #24)."),
    ('2a S4c rebuild',
     'No `xmemory.h` change, so no full rebuild.',
     "No `xmemory.h` change, so S4c alone would need no full rebuild; S4b is one anyway, since C1's `xmemory.h` reaches all 440 generated TUs in each game tree, plus 199 SDK TUs (SESSION2 19:35, L2708)."),
    ('2a S4c re-pin',
     'so after C1 changes the fingerprint in S4b, S4c changes it again: re-pin native3d and nativeB after each build, or only after S4c (open, for Agent 1; my reading).',
     'so with S4c in the S4b build, C1 and these edits change the fingerprint once, and native3d and nativeB are re-pinned once, on native4b (answered at 16:35, L2625; open from ~15:35 until then).'),
    ('2a S4c queue',
     'those move or change with S4c (my reading).',
     "with S4c folded in, that premise holds again, and Agent 3 runs the S4b queue (run-2 task #2, SESSION2 L2659; my reading); Agent 4 does the one re-pin, on native4b (run-2 task #12, L2730, L2744), and hands its boot check and identity/n-row matrix to Agent 3's queue."),
    ('2b step 5',
     '   - the slow-state check (`bench/agent11/timerq_slowstate.ps1`);',
     "   - the slow-state check (`bench/agent11/timerq_slowstate.ps1`; from W5 on, its 3-mode copy `bench/agent11/timerq_slowstate_3mode.ps1`, which also names each run's timer mode: spin, blocking or precise);"),
    ('2c start rule',
     "only the user's double-click starts a timed window: `bench/agent8/RUN-WINDOW4B.cmd`, or Agent 8's launcher `bench/agent8-launch/RUN-W4B-THEN-W5.cmd`, which waits for the quiet and readiness checks, then runs W4b and W5.",
     "only the user's double-click starts a timed window. W4b ran that way at 15:41-16:17 (SESSION2 L2605), and W5 at 17:56-18:29 (L2672). W6, and W7-W10 overnight as their gates pass, go through Agent 5's launcher, `bench/agent5/launch/RUN-NIGHT.cmd`, which the user double-clicks at ~23:45 before leaving the PC: no timed window starts before 00:00 (its gate also refuses while clang/ninja run), W6's GO comes only after Agent 3's S4b queue passes and Agent 8 promotes W6, and every timed run starts by 06:45 and ends before 07:30 (L2701-2703, L2714)."),
    ('2c before fps',
     '  - the slow-state check per run;',
     '  - the slow-state check per run (from W5 on, `bench/agent11/timerq_slowstate_3mode.ps1`; its mode column must match each arm: in W5, spin for base, s0 and d11, blocking for d11t and precise for d11p, which it does);'),
    ('W5 row',
     "| S4a + §2b passed (done; S4a live 14:56); window 4's result (Agent 8's launcher runs W5 right after W4b, SESSION2 L2578) | base / s0 / d11 / d11t / d11p | 1 cold + 5 × 3 = 16 | ~40 | Is s0 the same as base? What does the blocking wait do alone (d11 vs d11t)? Precise vs blocking? |",
     "| S4a + §2b passed (done; S4a live 14:56); window 4's result (done 16:17: no frame-time change clears the noise band, so W5 ran on the S3d line and B4 is deferred; promoted 16:46 as `bench/agent8/RUN-WINDOW5-S3D.cmd` with `bench/agent8/run/matrix-window5-s3d.json`, inputs frozen in `build/agent1/w5/W5-INPUTS-1642.txt`; SESSION2 L2625-2635). **Done 17:56-18:29** (`build/agent8/matrix/20261122-1756`, 16 of 16 OK, 15 scored; L2672): every arm within the noise band (±20.4%), and d11t and d11p use ~0.4 core less game CPU (L2674-2682); the read-out is Agent 8's | base / s0 / d11 / d11t / d11p | 1 cold + 5 × 3 = 16 | ~37 (ran 33) | Is s0 the same as base? What does the blocking wait do alone (d11 vs d11t)? Precise vs blocking? Each run's slow state and timer mode from the 3-mode script (§2b step 5) |"),
    ('W6 row',
     'for C1, S4b with C1 v2 and §21 A-D passed | s0 / #8',
     "for C1, S4b with C1 v3 (b2r §35) and §21 A-D passed (A's verify-mode level load can run since decision 1, §4a); GO only after Agent 3's S4b queue passes and Agent 8 promotes W6; started by Agent 5's launcher, not before 00:00 (SESSION2 L2702, L2714) | s0 / #8"),
    ('order paragraph',
     '\n\nOptions already defined in F (L26-33):',
     "\n\n**Order from W5 on** (Agent 1, 16:48, re-issued in task #10; SESSION2 L2625, L2694-2717): (1) W5: done at 17:56-18:29, the user's double-click after the 17:27 resume (L2653, L2672); (2) the S4b + S4c build: S4b on the S3d line with C1 v3, with S4c (#24 + #30) folded in (B4 deferred), its compose check rated PASS, SAFE to build (Agent 10, 19:47; b2r §38; L2732-2745); Agent 2, at -j8 Below Normal since 19:35: devoff4b ~20:25-20:30, native4b ~21:00, then CTR, then CG26; (3) the functional queue: Agent 3's S4b queue, with Toy Pad rows 7, 20 and 23 in (decision 1, §4a), to ~22:50-23:00; (4) W6 by Agent 5's launcher, `bench/agent5/launch/RUN-NIGHT.cmd` (the user's double-click at ~23:45; nothing timed before 00:00; W6's GO only after Agent 3's queue passes and Agent 8 promotes W6); (5) W7-W10 overnight, each once its \"needs first\" column is met; every timed run starts by 06:45 and ends before 07:30; (6) the native re-pin once, on native4b, by Agent 4 (run-2 task #12; its boot check and identity/n-row matrix run in Agent 3's queue; L2730, L2744). Every window from W5 on is after the Windows Update: compare arms within a window, and give the environment caveat above for any comparison with window 3 or earlier."
     '\n\nOptions already defined in F (L26-33):'),
    ('4b decisions',
     "- **~15:35 (task #24):** S4a is live and committed (14:56); S4b takes C1 v3 and leaves #24 + #30 for an incremental S4c (§2a); timed windows start only on the user's double-click (§2c).",
     "- **~15:35 (task #24):** S4a is live and committed (14:56); S4b takes C1 v3 and leaves #24 + #30 for an incremental S4c (§2a); timed windows start only on the user's double-click (§2c).\n"
     "- **16:35-16:48 (SESSION2 L2605-2635; Agent 1's order, re-issued in task #10):** W4b is done, with every arm within the noise band (d11t: ~15% less CPU). W5 next, on the S3d line (B4 deferred); then the S4b + S4c build (S3d line, C1 v3, S4c folded in); then the functional queue; W6 by Agent 5's launcher; W7-W10 overnight as their gates pass; and the native re-pin once, on native4b (§2c). This answers the S4c re-pin question.\n"
     "- **17:27 (the user; L2654):** decision 1 = yes: generated virtual Toy Pad tags in Agent 3's hidden-desktop runs, under the 02:11 harness-only rules; S4b queue rows 7, 20 and 23 are in, and C1 ON's verify-mode level load (b2r §21 A) can run (§4a item 1).\n"
     "- **17:52-18:34 (L2662-2692):** W5 started although the quiet gate failed on Defender (~0.9 core) and ran at 17:56-18:29; in Agent 1's quick look every arm is within the noise band, and d11t and d11p use ~0.4 core less game CPU (Changed since 15:54). The read-out is Agent 8's.\n"
     "- **19:31-19:35 (L2694-2717):** tonight's targets (the user sleeps at 00:00): the S4b + S4c bins, at -j8 Below Normal (devoff4b ~20:25-20:30, native4b ~21:00); Agent 3's S4b queue to ~22:50-23:00; Agent 5's launcher reviewed by ~22:30 and double-clicked by the user at ~23:45; no timed window before 00:00; W6's GO only after Agent 3's queue passes and Agent 8 promotes W6; every timed run starts by 06:45 and ends before 07:30.\n"
      "- **19:42-19:49 (L2719-2761):** Agent 4 does the native re-pin, once, on native4b (run-2 task #12; no `-Go` without Agent 1's word); Agent 10 rates the folded S4b + S4c compose check PASS, SAFE to build, landing OFF, with five gates for the build (b2r row 39, §38); until devoff4b is staged, Agent 3 may explore the level route for rows 7, 20 and 23 on devoff4-bin; and Agent 6's W4b logdiff is clean, with its W5 logdiff next, for Agent 8's read-out (Changed since 15:54)."),
    ('4b re-pin',
     "- **S4c's re-pin (for Agent 1, since ~15:35):** C1 in S4b and #24 + #30's CMake edit in S4c each change the native fingerprint: re-pin native3d and nativeB after each build, or only after S4c? (13:04 planned one re-pin for all three, b2r §26.)",
     "- **S4c's re-pin: answered** (asked ~15:35; SESSION2 L2625; Agent 1's order, re-issued in task #10): S4c is folded into the S4b build, so native3d and nativeB are re-pinned once, on native4b, as 13:04 planned (b2r §26). Agent 4 does it (run-2 task #12, since 19:42; L2730, L2744)."),
    ('4b possible changes',
     "Since 14:42: #32's gate result, S4a's landing and commits, the S4b/S4c split and the double-click rule (Changed since 14:42).",
     "Since 14:42: #32's gate result, S4a's landing and commits, the S4b/S4c split and the double-click rule (Changed since 14:42). Since 15:54: W4b's result with Agent 6's clean logdiff, the order from W5 on, decision 1, W5's run with Agent 1's quick look, tonight's targets, b2r §37-§38 (Agent 9's S4c package and the folded compose check) and Agent 4's re-pin task (Changed since 15:54). Next: Agent 8's W5 read-out (with Agent 6's W5 logdiff; read with §2c's environment caveat, the Defender caveat and the 3-mode slow-state check), the S4b + S4c bins, Agent 3's queue, Agent 4's re-pin and Agent 5's launcher."),
    ('5 slow state',
     "  - A8 runs `timerq_slowstate.ps1` over W4b's fg=1 runs.",
     "  - A8 runs `timerq_slowstate.ps1` over W4b's fg=1 runs (that script stays frozen), and its 3-mode copy `timerq_slowstate_3mode.ps1` over W5's (spin, blocking or precise, from env_set and the precise line; task #10). In W5 every scored run reaches the slow state, the modes match the arms, and onset tracks run order (my run; the read-out is Agent 8's; Changed since 15:54)."),
    ('6 SESSION2',
     'the screensaver and app closures held L2602).',
     "the screensaver and app closures held L2602). Re-read at @T@ (@S2N@ lines, @S2H@…): 16:35 L2605-2625 (W4b's run L2607; the result table L2610-2615; the verdicts L2617; run 6 L2618; agent activity in the window L2619-2623; the fixes and the HOLD file L2624; next L2625); 16:46 L2627-2635 (W5's files L2630; PlanOnly L2631; the frozen inputs L2632; agents idle and the 17:10 rule L2635); 17:07 L2637-2645 (the pause before W5; the 17:10 timer cancelled L2643); 17:36 L2647-2655 (the relaunch state L2649; W5's inputs re-hashed L2651; the user present for W5 L2653; decision 1 = yes L2654; the re-issued tasks L2655); 17:41 L2657-2660 (run-2 task numbers L2659; the quiet check L2660); 17:52 L2662-2668 (NOT QUIET on Defender L2664; the Defender caveat for the read-out L2667); 18:34 L2670-2692 (W5's run L2672; the table L2674-2680; CPU L2682; the environment per run L2683-2688; the HOLD manager's bugs L2689-2690; the pause L2692); 19:31 L2694-2704 (the restart L2696-2697; tonight's targets L2698-2703; Agent 8's read-out L2704); 19:35 L2706-2717 (S4b is a full rebuild L2708; -j8 Below Normal L2713-2716; the expected times L2717); 19:42 L2719-2730 (Agent 4's mc_smoke_check v2 L2721-2729; its native re-pin task L2730); 19:47 L2732-2747 (the folded compose file L2734-2736; the build gates L2737-2745, with the re-pin L2744; the hand-apply note L2746; Agent 3's route exploration L2747); 19:49 L2749-2761 (W4b's logdiff L2751-2756; Agent 6's W5 logdiff L2757-2761); 19:55 L2763-2771 (Agent 5's ETA and the relaxed Defender gate L2765-2769; Agent 3's lx1 L2770; the machine at 19:55 L2771); 20:06 L2773-2777 (hook errors are not a HOLD signal)."),
    ('6 a11 + W5',
     '`build/agent11/s4a/AGENT3-SPEC.md` (13:28, 1DA33FD3…): the #38 ON smoke spec.',
     "`build/agent11/s4a/AGENT3-SPEC.md` (13:28, 1DA33FD3…): the #38 ON smoke spec. `bench/agent11/timerq_slowstate_3mode.ps1` (@P3H@…, task #10): the 3-mode slow-state check for W5; the original `timerq_slowstate.ps1` (@P1H@…) stays frozen.\n"
     "- **W5** (read at @T@): `bench/agent8/RUN-WINDOW5-S3D.cmd` (5467F1BE…), `bench/agent8/run/matrix-window5-s3d.json` (4D7D689B…; arms, env, cvars and proof lines), `build/agent1/w5/W5-INPUTS-1642.txt` (identical again at 17:31 in `W5-INPUTS-1731.txt`, SESSION2 L2651), `build/agent8/readout/w5-draft/README.md` (Agent 1's 14:23 decision on the 3-mode copy@RDL@) and the run, `build/agent8/matrix/20261122-1756` (summary.md; each run's run.json, sys.csv and game.log, read by the 3-mode script)."),
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

# @CHECK@, @WAIT@ and @L5@ go first: they may contain @T@.
TOKENS = [('@CHECK@', CHECK), ('@WAIT@', WAIT), ('@L5@', L5), ('@RPH@', RPH[:8]), ('@T@', T), ('@BK@', BK), ('@S2N@', str(S2N)),
          ('@S2H@', S2H[:8]), ('@P1H@', P1H[:8]), ('@P3H@', P3H[:8]), ('@RDL@', RDL)]
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
print("'task #35' %d -> %d; 'task #10' %d -> %d" % (old.count('task #35'), new.count('task #35'),
                                                   old.count('task #10'), new.count('task #10')))
print('new: %d B, %d lines (+%d)' % (len(nbytes), nbytes.count(b'\n'), nbytes.count(b'\n') - raw.count(b'\n')))

# changed line ranges
ol, nl = old.split('\n'), new.split('\n')
sm = difflib.SequenceMatcher(a=ol, b=nl, autojunk=False)
dry = []
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag != 'equal':
        print('  %s old L%d-%d -> new L%d-%d' % (tag, i1 + 1, i2, j1 + 1, j2))
        dry.append('=== %s old L%d-%d -> new L%d-%d' % (tag, i1 + 1, i2, j1 + 1, j2))
        dry += ['--- old L%d: %s' % (i + 1, ol[i]) for i in range(i1, i2)]
        dry += ['+++ new L%d: %s' % (j + 1, nl[j]) for j in range(j1, j2)]

# scan the current-state sections (from **Sources:** on) for items this pass may have missed
KEYS = ['re-pin', 'S4c', "Agent 8's launcher", 'agent8-launch', 'RUN-W4B-THEN-W5', 'B4', 'Launcher review',
        'timerq_slowstate', 'W4B.cmd', '17:10', 'W5 waits', 'waits for the user', 'task #35', 'double-click']
start = next(i for i, l in enumerate(nl) if l.startswith('**Sources:**'))
print('scan from L%d:' % (start + 1))
for i in range(start, len(nl)):
    ks = [k for k in KEYS if k in nl[i]]
    if ks:
        p = nl[i].index(ks[0])
        print('  L%d %s: …%s…' % (i + 1, ks, nl[i][max(0, p - 110):p + 110]))

if DRY:
    open(DRYOUT, 'wb').write(('\n'.join(dry) + '\n').encode('utf-8'))
    print('wrote %s (%d lines)' % (DRYOUT, len(dry)))
    print('DRY RUN: %d failures; the draft is not written' % len(fails))
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

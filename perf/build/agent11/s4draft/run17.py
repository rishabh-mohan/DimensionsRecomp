# -*- coding: utf-8 -*-
# run17.py - S4-DRAFT under task #25 (Nov 23): the night's windows from Agent 1's runner summaries and the wrap-up (SESSION2 L3202-3313).
# Usage: python run17.py --dry | --apply. One-match edits, sha + line gates, hashed backup, LF, no BOM.
import datetime, difflib, hashlib, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'<workspace>'
P = lambda r: os.path.join(ROOT, *r.split('/'))
DRAFT, HOLD = P('perf-notes/S4-DRAFT.md'), P('perf-notes/WINDOW-HOLD.txt')
DRY, APPLY = '--dry' in sys.argv, '--apply' in sys.argv
if DRY == APPLY:
    sys.exit('usage: run17.py --dry | --apply')
sha = lambda b: hashlib.sha256(b).hexdigest().upper()
fails = []
def fail(m):
    fails.append(m); print('FAIL:', m)
if os.path.exists(HOLD):
    sys.exit('HOLD exists: stop')
raw = open(DRAFT, 'rb').read(); H0 = sha(raw)
print('draft %s %d B %d LF' % (H0[:8], len(raw), raw.count(b'\n')))
if not H0.startswith('C43A0DD9') or raw.count(b'\n') != 534 or b'\r' in raw or raw.startswith(b'\xef\xbb\xbf'):
    sys.exit('draft gate FAIL')
old = raw.decode('utf-8')
s2 = open(P('perf-notes/SESSION2.md'), 'rb').read().decode('utf-8').split('\n')
print('SESSION2 %d split lines' % len(s2))
def S(n, *subs):
    for s in subs:
        if n > len(s2) or s not in s2[n - 1]:
            fail('SESSION2 L%d lacks %r' % (n, s))
S(3202, '### 23:50 - Agent 1: user started RUN-NIGHT; user in bed')
S(3203, 'The user double-clicked RUN-NIGHT.cmd at 23:47:19')
S(3204, 'real launcher pid 19960', 'deadline 07:30')
S(3209, 'the user will wake **closer to 11:00**')
S(3211, 'can take a **second pass** of any window that is too close to call (same GO line)', 'a second pass cannot overwrite the first')
S(3214, '### 01:05 - Agent 1: W6 done; GO refusal fixed (screensaver value)')
S(3215, '**00:03:40 GO refused:**', 'run-matrix.ps1 -PlanOnly exit 1')
S(3216, "Set-ScreensaverNone (run-night.ps1 L461-467) removed HKCU\\Control Panel\\Desktop SCRNSAVE.EXE (it was '')",
  "run-matrix.ps1 L417 reads `$scr.'SCRNSAVE.EXE'` under Set-StrictMode -Version 2 (common.ps1 L4), which throws when the value is missing")
S(3217, 'Dry runs never change the screensaver, so the 40/40 tests could not catch this.')
S(3218, 'Fix at 00:05:37, with no launcher or pinned file touched', "re-created SCRNSAVE.EXE = ''", 'ScreenSaveActive stays 0, so the screensaver is still None')
S(3219, 'ACCEPTED 00:06:00')
S(3220, "either run-matrix L417 reads the value via PSObject.Properties, or the launcher sets SCRNSAVE.EXE to '' instead of removing it")
S(3221, 'run-day.ps1 probably has the same code.')
S(3222, '**W6 (00:09:02-00:51:52, 42.8 min):**')
S(3223, '21/21 OK, 20 scored, 0 excluded', 'Gate STRICT (MsMpEng 0.00); bins unchanged; out build/agent8/matrix/20261123-0009')
S(3224, 's0 2.44 ms median (385 fps, 2.50 cores); p2 2.47 (386 fps); p2f 2.45 (388 fps)')
S(3225, '**p2fc 2.16 ms (466 fps, 2.28 cores): -11.8 % median frame time, +21 % fps, -0.22 core vs s0.**')
S(3226, '-0.06, -0.16, -0.30, -0.30, -0.28 ms, so p2fc was faster in 5 of 5 rounds')
S(3227, "s0's band is +-21.4 %", 'round 1 was faster for every arm (likely thermal)')
S(3228, 'P2 alone and fix (i) alone show no change.')
S(3233, '**W9 (01:08:53-01:51:23, 42.5 min):**', '21/21 OK, 20 scored, 0 excluded', 'out build/agent8/matrix/20261123-0108')
S(3235, 'off 2.46 / 386 / 2.51 (ref); q0 2.48 / 387 / 2.49 (no change).')
S(3236, '**q125 2.31 / 389 / 1.82; q250 2.31 / 389 / 1.77; q500 2.31 / 390 / 1.72.**', 'fps unchanged (+1 %), median -6 %')
S(3237, 'q125 4.47 / 5.01, q250 4.50 / 5.11, q500 4.62 / 5.52 ms (off 4.98 / 5.63)', 'its tail is a little worse than q125/q250')
S(3239, 'off must have no back-off init line; each q arm exactly one ON line')
S(3243, '**W5b (01:55:28-02:33:54, 38.4 min):**', '19/19 OK, 18 scored, 0 excluded', 'bins unchanged (devoff4-bin); out build/agent8/matrix/20261123-0155')
S(3245, 'd11 (spin) 2.51 / 385 / 2.54 (ref).')
S(3246, '**d11t (blocking) 2.51 / 384 / 2.31 (-0.23 core, -9 %).**')
S(3247, '**d11p (precise) 2.50 / 385 / 2.34 (-0.20 core, -8 %).**', 'tightest spread (4.4 %)', 'p99 (4.78 vs 4.85)')
S(3249, 'Same direction and order as W5 (d11t -13.7 %, d11p -12.2 % game CPU), but smaller.')
S(3253, '**W4c (02:39:46-03:05:58, 26.2 min):**', '13/13 OK, 12 scored, 0 excluded', '(d0 = devoff2-bin, B = devoffB-bin); out build/agent8/matrix/20261123-0239')
S(3255, 'd0 2.47 / 385.4 / 2.53 (ref).')
S(3256, '**B 2.50 / 383.9 / 2.60: median +1.3 %, fps -0.4 %, +0.07 core.**', 'p99 4.91 vs 4.94')
S(3257, 'B was slower in 5 of 6 rounds and tied in 1.')
S(3258, "**W4b's B +6.0 % fps hint did not repeat:**")
S(3259, '**Second passes start now**')
S(3266, '**W6-2 (03:13:22-03:56:11, 42.8 min):**', '21/21 OK, 20 scored, 0 excluded', 'out build/agent8/matrix/20261123-0313')
S(3268, 's0 2.48 / 385.0 / 2.53 [2.44 / 385 / 2.50] (ref).')
S(3269, 'p2 2.47 / 385.2 / 2.53 [2.47 / 386 / 2.52]', 'p2f 2.45 / 385.9 / 2.55 [2.45 / 388 / 2.56]', 'no change, as in the first pass.')
S(3270, '**p2fc 2.13 / 469.8 / 2.26 [2.16 / 466 / 2.28]: median -14 %, fps +22 %, -0.27 core vs s0. Runner verdict this time: FASTER (outside noise).**')
S(3271, '-0.34, -0.27, -0.32, -0.28, -0.32 ms', 'so 10 of 10 over both passes')
S(3272, 'p2fc p99 5.04 vs s0 5.00 (flat), p99.9 6.49 vs 5.74', "p2f's p99.9 is 6.40 too, with one >33 ms frame in r5", 'whether fix (i) or C1 adds rare slow frames')
S(3273, "p2fc (P2 + fix (i) + C1 v3, verify off) is tonight's only frame-time win", "W9's back-off and W5b's wait modes save CPU only.")
S(3277, '**W9-2 (04:01:16-04:44:08, 42.8 min):**', '21/21 OK, 20 scored, 0 excluded', 'out build/agent8/matrix/20261123-0401')
S(3279, 'off 2.46 / 384.9 / 2.50 [2.46 / 386 / 2.51]', 'q0 2.47 / 385.5 / 2.47 [2.48 / 387 / 2.49]: no change.')
S(3280, 'q125 2.39 / 378.9 / 1.96 [2.31 / 389 / 1.82]: -0.54 core, fps -1.6 %.')
S(3281, 'q250 2.37 / 382.8 / 1.95 [2.31 / 389 / 1.77]: -0.55 core, fps -0.5 %.')
S(3282, '**q500 2.32 / 389.2 / 1.80 [2.31 / 390 / 1.72]: -0.70 core (-28 %), fps +1.1 %, median -5.9 %. p99 4.68 vs 4.99, p99.9 5.40 vs 5.58. Runner verdict: FASTER (outside noise).**')
S(3283, 'q125 and q250 were less steady this pass:')
S(3286, 'q500 kept a normal frame count in all 4 runs')
S(3287, 'Over both passes q500 saves the most CPU (0.70-0.79 core) with no fps loss, and this pass it also had the best tail. Lean: q500.')
S(3291, '**W5b-2 (04:51:58-05:30:42, 38.7 min):**', '19/19 OK, 18 scored, 0 excluded', 'The quiet gate held the start back 3 min (CrossDeviceService',
  'then passed STRICT', 'out build/agent8/matrix/20261123-0451')
S(3293, 'd11 (spin) 2.51 / 385.2 / 2.56 [2.51 / 385 / 2.54]')
S(3294, 'd11t (blocking) 2.52 / 382.0 / 2.35 [2.51 / 384 / 2.31]: -0.21 core, fps -0.8 %')
S(3295, '**d11p (precise) 2.51 / 385.5 / 2.35 [2.50 / 385 / 2.34]: -0.21 core (-8 %), fps unchanged.**')
S(3296, 'd11p kept fps in both passes; d11t lost 0.8 % this pass. Lean: d11p.')
S(3297, 'a break of a few days to a week is coming', 'A 2-hour grace period starts ~11-12', 'aim to finish by ~13:00')
S(3298, '**W4c second pass skipped**', 'The launcher stays idle until it exits at 07:30. No more timed windows before the break.')
S(3301, 'Readouts: Agents 7 and 8 (formal, both passes), Agent 6 (logdiffs), Agent 12 (gates).')
S(3302, 'Agent 3: quiet-host f10a/f10b rows (finding 10).')
S(3304, 'Agents 5 and 8: stage the screensaver/StrictMode fix; install it after the launcher exits at 07:30.')
S(3306, '### 05:44 - Agent 1: S4b/S4c code pushed to GitHub; wrap-up tasks sent')
S(3309, 'the 16 S4b/S4c files in build/agent2/s4b/HASHES.txt were copied from build/agent2/snap1 into the live trees after a hash check',
  'Commits on perf/opt, pushed to mine without force: rexglue-sdk 5350b1d (13 files',
  'DimensionsRecomp b0bd3b4 (memory_watch.cpp, CMakeLists.txt, new gpu_wait_backoff.cpp, SDK pointer)')
S(3310, 'Third-party worktree changes stay uncommitted.', 'plume via tools/gpu-aot/prepare_plume.py + tools/gpu-aot/patches (winsdk-compat holds S1+p2)',
  'simde via rexglue-sdk/scripts/prepare_simde.py + rexglue-sdk/patches/simde-native-m64-stream.patch')
S(3311, 'Notes/scripts/results are not pushed.', 'a public perf/ folder, a private repo they create, or local only')
S(3312, 'SCRNSAVE fix staged and installed after 07:30 (5; reviews by 8 and 10)', 'No builds or timed runs this morning.')
# Files and folders the new text cites.
MX = {'matrix-window9.json': 'CE0AD75792B47D59876C864B39797CD877404F911D12F92E6CC9C4351D747610',
      'matrix-window5b.json': '23575AAAE9DCBB85C9965AC8A3A8794916FFA881C09C656A6512C7EE462D5F76',
      'matrix-window4c.json': 'E2E3E4DAAF7D30C7B8B2D28D21911E6EACDA5260963F9B99095EE70C09022396'}
for js, h in MX.items():
    if sha(open(P('bench/agent8/run/' + js), 'rb').read()) != h:
        fail('bench/agent8/run/%s hash differs' % js)
for d in ('0009', '0108', '0155', '0239', '0313', '0401', '0451'):
    if not os.path.isdir(P('build/agent8/matrix/20261123-' + d)):
        fail('no results folder 20261123-' + d)
for f in ('build/agent2/s4b/HASHES.txt', 'build/agent2/native4b-bin/MANIFEST.txt', 'DimensionsRecomp/tools/gpu-aot/prepare_plume.py',
          'DimensionsRecomp/tools/gpu-aot/patches/plume-winsdk-compat.patch', 'DimensionsRecomp/rexglue-sdk/scripts/prepare_simde.py',
          'DimensionsRecomp/rexglue-sdk/patches/simde-native-m64-stream.patch', 'build/agent1/night/GO-W6.txt', 'build/agent1/night/GO-W9.txt',
          'build/agent1/night/GO-W5b.txt', 'build/agent1/night/GO-W4c.txt', 'bench/agent5/launch/RUN-NIGHT.cmd'):
    if not os.path.isfile(P(f)):
        fail('missing ' + f)
mt = datetime.datetime.fromtimestamp(os.path.getmtime(P('build/agent2/native4b-bin/MANIFEST.txt'))).strftime('%m-%d %H:%M:%S')
if mt != '11-22 22:40:12':
    fail('native4b MANIFEST time ' + mt)
pin = open(P('build/agent4/repin/pin-native4b-2243.txt'), 'rb').read().decode('utf-8')
for s in ('repin_check.ps1 2026-11-22 22:43:15  DRY RUN', 'built fingerprint 9b40acbbef4c57b3 is new', 'not a current pin', 'SUMMARY: 0 FAIL, 0 WARN; exit 0'):
    if s not in pin:
        fail('pin record lacks %r' % s)
print('cited files checked')
T = datetime.datetime.now().strftime('%H:%M'); BK = 'S4-DRAFT.%s-%s.md' % (T.replace(':', ''), H0[:8])
BLOCK = '\n'.join([
 "**Changed since 23:29** (task #25, Nov 23: the night's windows and the wrap-up before the break; @T@; the 23:29 version is kept in "
 "`build/agent11/s4draft/@BK@`). The numbers below are Agent 1's runner summaries, not the formal read-outs; I replace them as the read-outs land:",
 "- **The night (SESSION2 L3202-3263):** the user double-clicked `bench/agent5/launch/RUN-NIGHT.cmd` at 23:47:19 (launcher pid 19960, deadline "
 "07:30; L3203-3204). **The first GO was refused at 00:03:40:** the runner's plan check (`run-matrix.ps1 -PlanOnly`) exited 1, because the "
 "launcher's Set-ScreensaverNone (run-night.ps1 L461-467) had removed the `SCRNSAVE.EXE` value under `HKCU\\Control Panel\\Desktop` (it was ''), "
 "and run-matrix.ps1 L417 reads that value under Set-StrictMode -Version 2 (common.ps1 L4), which throws when it is missing. Dry runs never change "
 "the screensaver, so the 40/40 launcher tests couldn't catch it. Agent 1 re-created the value as '' at 00:05:37 (no launcher or pinned file "
 "touched; ScreenSaveActive stayed 0, so the screensaver stayed None), and the GO was accepted at 00:06:00 (L3215-3219). The windows then ran in "
 "the planned order, W6, W9, W5b and W4c (00:09-03:06). Because the user wakes at ~11:00, the launcher's time to 06:45 went to second passes of "
 "W6, W9 and W5b with the same GO lines, each into a new results folder (L3209-3211, L3259-3262); W4c's second pass was skipped for the wrap-up "
 "(L3298). native4b-bin was staged by 22:40 (its MANIFEST.txt is from 22:40:12; my 23:29 Waiting line still expected it), and Agent 4's dry-run "
 "re-pin check at 22:43 reports 0 FAIL, 0 WARN (`build/agent4/repin/pin-native4b-2243.txt`: the built fingerprint 9b40acbbef4c57b3 is new, not "
 "a current pin); the re-pin rows haven't run (§2c).",
 "- **Every window:** runner exit 0, every run OK, 0 excluded, the quiet gate STRICT, the bins unchanged. Median ms / fps / CPU cores, with the "
 "second pass in brackets:",
 "  - **W6** (devoff4b; 00:09:02-00:51:52, `build/agent8/matrix/20261123-0009`, and 03:13:22-03:56:11, `20261123-0313`; 21 of 21 runs each, "
 "20 scored): s0 2.44 / 385 / 2.50 [2.48 / 385.0 / 2.53]; p2 2.47 / 386 / 2.52 [2.47 / 385.2 / 2.53] and p2f 2.45 / 388 / 2.56 [2.45 / 385.9 "
 "/ 2.55], so P2 alone and fix (i) alone change nothing; **p2fc (P2 + fix (i) + C1 v3, verify off) 2.16 / 466 / 2.28 [2.13 / 469.8 / 2.26]: "
 "median −11.8 % [−14 %], fps +21 % [+22 %], −0.22 [−0.27] core against s0.** C1's own effect, p2fc − p2f per round, was −0.06 to −0.34 ms, "
 "faster in 10 of 10 rounds over both passes. The runner said \"within noise\" in the first pass only because s0's band was ±21.4 % (round 1 "
 "was fast for every arm, likely thermal), and FASTER (outside noise) in the second. Tail: p2fc's p99 5.04 against s0's 5.00 ms (flat) and "
 "p99.9 6.49 against 5.74; p2f's p99.9 is 6.40 too, with one frame over 33 ms (r5), so the formal read-out checks whether fix (i) or C1 adds "
 "rare slow frames. **p2fc is the night's only frame-time win** (L3222-3229, L3266-3273).",
 "  - **W9** (#24's back-off on devoff4b; 01:08:53-01:51:23, `20261123-0108`, and 04:01:16-04:44:08, `20261123-0401`; 21 of 21 each, 20 "
 "scored): off 2.46 / 386 / 2.51 [2.46 / 384.9 / 2.50]; q0 no change; q125 2.31 / 389 / 1.82 [2.39 / 378.9 / 1.96]; q250 2.31 / 389 / 1.77 "
 "[2.37 / 382.8 / 1.95]; **q500 2.31 / 390 / 1.72 [2.32 / 389.2 / 1.80]: 0.70-0.79 core less (−28 to −31 %), fps +1 %, median −6 %,** and "
 "FASTER (outside noise) in the second pass. Tail (p99 / p99.9 ms): in the first pass q500 4.62 / 5.52 against off's 4.98 / 5.63, a little "
 "worse than q125 (4.47 / 5.01) and q250 (4.50 / 5.11); in the second, q500 4.68 / 5.40 against 4.99 / 5.58, the best tail. q125 and q250 "
 "were unsteady in the second pass (two runs each with low frame counts; q125 fps −1.6 %), while q500 kept normal frame counts in all its runs. "
 "**Lean: q500** (L3233-3239, L3277-3287).",
 "  - **W5b** (the timer wait modes on devoff4-bin; 01:55:28-02:33:54, `20261123-0155`, and 04:51:58-05:30:42, `20261123-0451`, which the "
 "quiet gate held back 3 min for CrossDeviceService before a STRICT pass; 19 of 19 each, 18 scored): d11 (spin) 2.51 / 385 / 2.54 [2.51 / "
 "385.2 / 2.56]; d11t (blocking) 2.51 / 384 / 2.31 [2.52 / 382.0 / 2.35]: −0.23 [−0.21] core, fps −0.8 % in the second pass; **d11p "
 "(precise) 2.50 / 385 / 2.34 [2.51 / 385.5 / 2.35]: −0.20 [−0.21] core (−8 %), fps unchanged in both passes,** with the tightest spread and "
 "a slightly better p99 (4.78 against 4.85 ms). The same direction and order as W5 (d11t −13.7 %, d11p −12.2 % game CPU), but smaller. "
 "**Lean: d11p** (L3243-3249, L3291-3296).",
 "  - **W4c** (codegen B again: d0 = devoff2-bin, B = devoffB-bin; 02:39:46-03:05:58, `20261123-0239`; 13 of 13, 12 scored): d0 2.47 / "
 "385.4 / 2.53; B 2.50 / 383.9 / 2.60: median +1.3 %, fps −0.4 %, +0.07 core, p99 4.91 against 4.94 ms; B was slower in 5 of 6 rounds and "
 "tied in 1. W4b's +6.0 % fps hint for B did not repeat. **Lean: drop B** (L3253-3258).",
 "- **The leans, before the formal read-outs:** keep p2fc (P2 + fix (i) + C1 v3, verify off), the night's only frame-time win; the back-off "
 "at Q = 500 µs; the precise timer wait (d11p) over the blocking one; drop codegen B. The back-off and the wait modes save CPU only (L3273, "
 "L3287, L3296, L3258). The decisions rest on the formal read-outs of both passes (Agents 7 and 8, ~10:00), Agent 6's logdiffs (for W9: no "
 "back-off init line in off, and exactly one ON line per q arm) and dumpstacks, and Agent 12's gates (L3239, L3301, L3312). Agent 3 runs the "
 "two quiet-host finding-10 rows this morning (f10a, f10b; L3302; §5).",
 "- **The wrap-up before the break (L3297-3312):** the user pauses the project for a few days to a week from ~13:00, with a 2-hour grace "
 "period from ~11-12. No builds and no timed runs this morning, and no more timed windows before the break; the launcher stays idle until it "
 "exits at 07:30. The 16 S4b/S4c files (`build/agent2/s4b/HASHES.txt`) were hash-checked and copied from `build/agent2/snap1` into the live "
 "trees, then committed on perf/opt and pushed to the remote `mine` without force: rexglue-sdk 5350b1d (13 files) and DimensionsRecomp "
 "b0bd3b4 (memory_watch.cpp, CMakeLists.txt, the new gpu_wait_backoff.cpp and the SDK pointer). So perf/opt holds S4a plus S4b/S4c, with every "
 "new switch OFF. The third-party changes stay uncommitted and are rebuilt from tracked files: plume by "
 "`DimensionsRecomp/tools/gpu-aot/prepare_plume.py` with the patches in `DimensionsRecomp/tools/gpu-aot/patches/` (`plume-winsdk-compat.patch` "
 "holds S1 + p2), simde by `DimensionsRecomp/rexglue-sdk/scripts/prepare_simde.py` with "
 "`DimensionsRecomp/rexglue-sdk/patches/simde-native-m64-stream.patch`. The notes, scripts and results aren't pushed; Agent 1 asks the user "
 "where they go. The SCRNSAVE fix (run-matrix.ps1 L417 reads the value through PSObject.Properties, or the launcher sets '' instead of "
 "removing it; run-day.ps1 probably has the same code) is staged by Agents 5 and 8 and installed after 07:30, with reviews by Agents 8 and 10, "
 "before RUN-DAY or another night (L3220-3221, L3304, L3312). The restart doc is `perf-notes/RESUME.md`.",
 "- Updated at @T@ (SESSION2 to L3313): the header; this block; Decisions item 2; Still open (the timed windows, W5's read-out, Agent 5's "
 "launcher); §2c (the W6 and W9 rows, new W5b and W4c rows, and \"As run\" in the order paragraph); §4b (a 23:47-05:44 entry and Possible "
 "changes); §5 (finding 10); §6 (the night's sources)."])
W6DONE = ("**Done** 00:09:02-00:51:52 (`build/agent8/matrix/20261123-0009`) and again 03:13:22-03:56:11 (`20261123-0313`), 21 of 21 OK each, 20 "
          "scored (runner summaries): p2fc −11.8 % [−14 %] median, +21 % [+22 %] fps and −0.22 [−0.27] core against s0, faster in 10 of 10 "
          "rounds over both passes; p2 and p2f no change; the formal read-out checks p2fc's p99.9 (6.49 against 5.74 ms) (SESSION2 L3222-3229, "
          "L3266-3273; Changed since 23:29)")
W9DONE = ("As run: devoff4b, `bench/agent8/run/matrix-window9.json` (CE0AD757…) with the GO `only=off,q0,q125,q250,q500 repeats=4` (1 + 5 × 4 "
          "= 21 runs, ~43 min; s4b17 and s4b18 PASS). **Done** 01:08:53-01:51:23 (`build/agent8/matrix/20261123-0108`) and again "
          "04:01:16-04:44:08 (`20261123-0401`), 21 of 21 OK each, 20 scored (runner summaries): q500 uses 0.70-0.79 core less (−28 to −31 %) "
          "with fps +1 % and a better p99 than off (4.62 against 4.98 ms; 4.68 against 4.99); q125 and q250 save a little less and were unsteady "
          "in the second pass; lean q500 (L3233-3239, L3277-3287; Changed since 23:29)")
W5B = ("| **W5b: timer wait modes again** (devoff4-bin) | W5's lead (d11t and d11p ~0.4 core less game CPU at the same frame time); "
       "`bench/agent8/run/matrix-window5b.json` (23575AAA…) with the GO `only=d11,d11t,d11p repeats=6`. **Done** 01:55:28-02:33:54 "
       "(`build/agent8/matrix/20261123-0155`) and again 04:51:58-05:30:42 (`20261123-0451`), 19 of 19 OK each, 18 scored (runner summaries): "
       "d11t −0.23 [−0.21] core, with fps −0.8 % in the second pass; d11p −0.20 [−0.21] core (−8 %), with fps unchanged in both; lean d11p "
       "(SESSION2 L3243-3249, L3291-3296; Changed since 23:29) | d11 / d11t / d11p | 1 + 3 × 6 = 19 | ~38 (ran 38.4 and 38.7) | Blocking "
       "against precise wait: the CPU each saves, and any fps or p99 cost |")
W4C = ("| **W4c: codegen B again** | W4b's B hint (fps +6.0 %, n = 3; Agent 8's interim read-out); `bench/agent8/run/matrix-window4c.json` "
       "(E2E3E4DA…) with the GO `only=d0,B repeats=6`. **Done** 02:39:46-03:05:58 (`build/agent8/matrix/20261123-0239`), 13 of 13 OK, 12 "
       "scored (runner summary): B median +1.3 %, fps −0.4 %, +0.07 core, slower in 5 of 6 rounds, so the hint did not repeat; lean: drop B. "
       "The second pass was skipped for the wrap-up (L3253-3258, L3298; Changed since 23:29) | d0 (devoff2) / B (devoffB) | 1 + 2 × 6 = 13 | "
       "~26 (ran 26.2) | Does W4b's fps hint for B hold? |")
ASRUN = (" **As run (Nov 23; SESSION2 L3202-3313):** (1)-(3) as above; (4) the user double-clicked RUN-NIGHT.cmd at 23:47:19, and after the "
         "screensaver-value fix at 00:05:37 the launcher ran the night order W6, W9, W5b and W4c (00:09-03:06), then second passes of W6, W9 "
         "and W5b (03:13-05:31; W4c's was skipped); (5) W7 (#19 isn't rated or built), W8a, W8b and W10 didn't run: W8a, W8b and W10 had moved "
         "to Monday's day session (L3043-3048), and the break that starts at ~13:00 on Monday moves all four to after it "
         "(`perf-notes/RESUME.md`); (6) native4b-bin was staged by 22:40, and Agent 4's dry-run re-pin check at 22:43 reports 0 FAIL, 0 WARN "
         "(`build/agent4/repin/pin-native4b-2243.txt`), but the re-pin rows (rpb0/rpm4) wait in Agent 3's queue after f10a/f10b (L3169), so "
         "native4b isn't pinned yet (Changed since 23:29).")
DEC2 = (" **Night of Nov 22-23:** W6, W9, W5b and W4c ran through the launcher, with second passes of W6, W9 and W5b; the leans are p2fc, q500, "
        "d11p and dropping B, pending the formal read-outs. W7, W8a, W8b and W10 wait until after the break (Changed since 23:29; §2c).")
SO142 = (" **Overnight (Nov 23):** the user double-clicked RUN-NIGHT.cmd at 23:47:19, and the launcher ran W6, W9, W5b and W4c plus second "
         "passes of W6, W9 and W5b by 05:31; no more timed windows before the break (Changed since 23:29).")
SO144 = " The formal read-outs of tonight's windows, both passes, are Agents 7 and 8's, due ~10:00 (L3301; Changed since 23:29)."
SO145 = (" **Overnight:** its one problem was the GO refusal at 00:03:40 (the removed SCRNSAVE.EXE value, re-created by hand at 00:05:37); "
         "Agents 5 and 8 stage the code fix, installed after the launcher exits at 07:30, with reviews by Agents 8 and 10 (SESSION2 "
         "L3215-3221, L3304, L3312; Changed since 23:29).")
E4B = ("- **23:47-05:44 (L3202-3313):** the night ran W6, W9, W5b and W4c, then second passes of W6, W9 and W5b, after the SCRNSAVE GO refusal "
       "(00:03:40) and its fix (00:05:37); the leans from the runner summaries are p2fc, q500, d11p and dropping B, and the formal read-outs "
       "decide; W4c's second pass was skipped. The wrap-up before the break: the S4b/S4c code is on perf/opt (rexglue-sdk 5350b1d, "
       "DimensionsRecomp b0bd3b4), there are no builds or timed runs this morning, and `perf-notes/RESUME.md` is the restart doc (Changed since "
       "23:29).")
POSS_O = ("Next: the windows, Agent 8's and Agent 12's read-outs, the post-window rows (finding 10's two L-route rows, s4bV0, s4bLV and the "
          "re-pin) and Monday's day session (W8a, W8b, W10).")
POSS_N = ("Since 23:29: the night's windows with Agent 1's runner summaries and leans, the SCRNSAVE GO refusal and its fix, and the wrap-up "
          "commits (Changed since 23:29). Next, before the break: the formal read-outs of both passes (Agents 7 and 8), Agent 6's logdiffs, "
          "Agent 12's gates and Agent 3's f10a/f10b rows. After it: s4bV0, s4bLV, the re-pin rows, W7, W8a, W8b and W10 "
          "(`perf-notes/RESUME.md`).")
F10 = (" **Nov 23:** Agent 3 runs the two quiet-host rows (f10a, f10b) this morning as part of the wrap-up (L3302); I fold their result in "
       "when it lands, and the W6 read-out reports STUCK-LOCK counts per arm (L2902-2907).")
SRC = ("- **The night of Nov 22-23 and the wrap-up** (read at @T@): SESSION2 L3202-3313 (23:50 L3202-3212; 01:05, W6 and the GO refusal, "
       "L3214-3230; 01:52, W9, L3232-3240; 02:36, W5b, L3242-3250; 03:09, W4c and the second-pass plan, L3252-3263; 03:58, W6-2, L3265-3274; "
       "04:46, W9-2, L3276-3288; 05:33, W5b-2 and the wrap-up plan, L3290-3304; 05:44, the commits, L3306-3312). Results: "
       "`build/agent8/matrix/20261123-0009` (W6), `-0108` (W9), `-0155` (W5b), `-0239` (W4c), `-0313` (W6-2), `-0401` (W9-2) and `-0451` "
       "(W5b-2). The GO files `build/agent1/night/GO-W6.txt`, `GO-W9.txt`, `GO-W5b.txt` and `GO-W4c.txt`; the copied S4b/S4c files' record "
       "`build/agent2/s4b/HASHES.txt`; Agent 4's re-pin dry run `build/agent4/repin/pin-native4b-2243.txt`.")
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
sub('D3', ", and at 23:29 with the user's 23:16-23:24 answers (Agent 1, 23:25).",
    ", at 23:29 with the user's 23:16-23:24 answers (Agent 1, 23:25), and on Nov 23 at @T@ under task #25, the wrap-up before the break (see \"Changed since 23:29\").")
line('block', '**Changed since 15:54** (task #10', lambda l: BLOCK + '\n\n' + l)
sub('dec2', 'so a W5+ plan that leans on window 3 or earlier results has to say so. See §2c.',
    'so a W5+ plan that leans on window 3 or earlier results has to say so. See §2c.' + DEC2)
sub('so142', "task #24's review of Agent 8's launcher was cancelled. Agent runs stay functional only (§2c).",
    "task #24's review of Agent 8's launcher was cancelled. Agent runs stay functional only (§2c)." + SO142)
sub('so144', "and d11t's p99 is a lead only; Agent 6's W5 logdiff is clean (SESSION2 L2839-2843, L2918).",
    "and d11t's p99 is a lead only; Agent 6's W5 logdiff is clean (SESSION2 L2839-2843, L2918)." + SO144)
sub('so145', 'The day-launcher files (`build/agent5/day-draft/`) are rated after the windows (L3092).',
    'The day-launcher files (`build/agent5/day-draft/`) are rated after the windows (L3092).' + SO145)
sub('w6row', 'the functional set is complete (L2968-2972, L2985, L3048, L3080) |',
    'the functional set is complete (L2968-2972, L2985, L3048, L3080). ' + W6DONE + ' |')
sub('w9row', 'the Q = 250 functional pair done (a9 S5.2.4 steps 1-2) |', 'the Q = 250 functional pair done (a9 S5.2.4 steps 1-2). ' + W9DONE + ' |')
line('rows', '| **W10: codegen**', lambda l: l + '\n' + W5B + '\n' + W4C)
sub('order', 'give the environment caveat above for any comparison with window 3 or earlier.',
    'give the environment caveat above for any comparison with window 3 or earlier.' + ASRUN)
line('4b', '- **21:55-23:25 (L2921-3199):**', lambda l: l + '\n' + E4B)
sub('poss', POSS_O, POSS_N)
sub('f10', 'the suspected cause, one VirtualQuery per upload, is another candidate for after S4 (L3133).',
    'the suspected cause, one VirtualQuery per upload, is another candidate for after S4 (L3133).' + F10)
line('src', '- **W5** (read at 20:07):', lambda l: l + '\n' + SRC)
for tok, val in (('@T@', T), ('@BK@', BK)):
    if tok in old:
        fail('token %s in draft' % tok)
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
for r in (W5B, W4C):
    if r.count('|') != 7:
        fail('new row has %d pipes' % r.count('|'))
nb = new.encode('utf-8')
if b'\r' in nb or '@T@' in new or '@BK@' in new:
    fail('CR or token left')
print('new %d B, %d LF (+%d)' % (len(nb), nb.count(b'\n'), nb.count(b'\n') - raw.count(b'\n')))
if nb.count(b'\n') != 549:
    fail('expected 549 LF')
ol, nl = old.split('\n'), new.split('\n'); dry = []
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=ol, b=nl, autojunk=False).get_opcodes():
    if tag != 'equal':
        dry.append('=== %s old L%d-%d -> new L%d-%d' % (tag, i1 + 1, i2, j1 + 1, j2))
        dry += ['--- %d: %s' % (i + 1, ol[i]) for i in range(i1, i2)] + ['+++ %d: %s' % (j + 1, nl[j]) for j in range(j1, j2)]
        print(dry[-1 - (i2 - i1) - (j2 - j1)])
if DRY:
    open(P('build/agent11/s4draft/run17-dry.txt'), 'wb').write(('\n'.join(dry) + '\n').encode('utf-8'))
    print('DRY: %d failures' % len(fails)); sys.exit(1 if fails else 0)
if fails or os.path.exists(HOLD):
    sys.exit('not written')
bk = P('build/agent11/s4draft/' + BK)
if os.path.exists(bk) or sha(open(DRAFT, 'rb').read()) != H0:
    sys.exit('backup exists or draft changed')
open(bk, 'wb').write(raw)
open(DRAFT, 'wb').write(nb); chk = open(DRAFT, 'rb').read()
print('WROTE sha256 %s %d B %d LF CR %d; backup %s' % (sha(chk), len(chk), chk.count(b'\n'), chk.count(b'\r'), BK))

# -*- coding: utf-8 -*-
# run18.py - S4-DRAFT under task #25 (Nov 23), pass A: the formal sources that landed by 06:40 (Agent 12's gates,
# Agent 6's logdiffs, Agent 3's f10 rows, Agent 5's SCRNSAVE fix, Agent 8's W4c and W6 read-outs), row 30's state.
# Usage: python run18.py --dry | --apply. One-match edits, sha + line gates, source string checks, hashed backup, LF, no BOM.
import datetime, difflib, hashlib, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = r'<workspace>'
P = lambda r: os.path.join(ROOT, *r.split('/'))
DOC, HOLD = P('perf-notes/S4-DRAFT.md'), P('perf-notes/WINDOW-HOLD.txt')
DRY, APPLY = '--dry' in sys.argv, '--apply' in sys.argv
if DRY == APPLY:
    sys.exit('usage: run18.py --dry | --apply')
sha = lambda b: hashlib.sha256(b).hexdigest().upper()
fails = []
def fail(m):
    fails.append(m); print('FAIL:', m)
if os.path.exists(HOLD):
    sys.exit('HOLD exists: stop')
raw = open(DOC, 'rb').read(); H0 = sha(raw)
print('s4draft %s %d B %d LF' % (H0[:8], len(raw), raw.count(b'\n')))
if not H0.startswith('1B0BB0DC') or raw.count(b'\n') != 549 or b'\r' in raw or raw.startswith(b'\xef\xbb\xbf'):
    sys.exit('s4draft gate FAIL')
old = raw.decode('utf-8')
def SRC(rel, *subs):
    if not os.path.isfile(P(rel)):
        fail('missing ' + rel); return
    t = open(P(rel), 'rb').read().decode('utf-8')
    for s in subs:
        if s not in t:
            fail('%s lacks %r' % (rel, s))
W6 = 'build/agent8/readout/w-followup/W6.md'
W4C = 'build/agent8/readout/w-followup/W4c.md'
G12 = 'build/agent12/w6-gates/NIGHT-RESULTS.md'
A6 = 'build/agent6/wnight/RESULTS.md'
F10 = 'build/agent3/f10/RESULTS.md'
SCR = 'build/agent5/scrnsave-fix/README.md'
SRC(W6, '**p2fc\'s gain is solid.**', 'the paired median frame time is **−10.3 % [−13.6, −6.9]** (p2fc was lower in 9 of 10 rounds, sign test p 0.021)',
    'fps is **+18.0 % [+14.1, +22.0]** and CPU is **−0.249 cores [−0.303, −0.195]**, so CPU time per frame drops by about 24 %',
    '**−9.9 % [−12.5, −7.3]', '**+17.0 % [+14.2, +19.8]', '−8.9 % [−16.2, −1.0] in pass 1 and −11.7 % [−15.1, −8.3] in pass 2',
    '−9.4 to −12.2 % median, +16.9 to +20.3 % fps and −0.22 to −0.27 cores, and every one of those CIs excludes 0',
    'The pooled raw ratios are −12.8 % and +21.8 %.', 'Without round 1 they are −12.2 % [−13.2, −11.3] (8 of 8 rounds)',
    'p2fc − p2f was negative in **10 of 10 rounds**: −0.062 to −0.338 ms, mean −0.261 ms [−0.322, −0.199], sign test p 0.002',
    'p2: −0.0 % [−3.0, +3.1] median', 'p2f: +0.4 % [−2.1, +3.1] median', 'p2f uses **+0.039 cores [+0.006, +0.072]**',
    '**The pass-2 tail comes from an episode that hit all four arms, not from p2fc.**', 'From about 03:25 to 03:41, an episode hit 8 consecutive runs across all four arms.',
    'Each of those runs had 33-58 frames over 6 ms, against 1-6 in the other pass-2 runs (21 in 0352, all in one burst).', "The episode covered 3 of p2fc's 5 pass-2 runs", 'No recorded host CPU, clock, GPU or memory counter shows its cause (audit §5.1).', "**The episode's cause is unknown.** No recorded host or game counter shows it (audit §5.1)",
    'The paired p99.9 difference p2fc − s0 is −0.276 ms [−0.951, +0.400] pooled (p2fc higher in 5 of 10 rounds)',
    'Without the episode runs, the p99.9 medians are 5.682 ms (p2fc) and 5.714 ms (s0).', 'p2fc had **0 frames over 16.7 ms** in 231k frames',
    's0 had 1 and p2f had 11.', 'That is a host burst.', "Agent 7's p99 is +1.7 % [+0.9, +2.6]", 'frames of 4.5 ms or more have a median +2.9 % [+2.3, +3.5]',
    '1 % low fps is unchanged (−1.3 % [−4.9, +2.5])', 'all 42 runs were clean', '0 KILLED, 0 STUCK-LOCK, 0 hang dumps and 0 slow-state runs',
    "Agent 11's 3-mode timerq copy found 0 slow runs in both passes", 'A verify-on build might give back part of the gain.',
    "W6 has no C1-only arm", 'It is the same with and without the flagged runs',
    'results.csv agrees with frames.json/run.json in 1620 of 1620 items over all 7 night folders',
    '**Cause: GPU warm-up (audit §5.5).**', 'the GPU ran above its steady clock in the first runs', "Almost every other run sat at 832 MHz, the GPU's thermal limit", 'Run fps follows the GPU clock', 'The earlier lead (the fast state removes the cost C1 removes) is withdrawn.', '**Lead: at steady state this host looks GPU-limited.** After round 1, s0, p2 and p2f ran at 97-100 % GPU utilisation.', 'p2fc ran at 86-89 % (82 % in the host-loaded 0023) while giving 18 % more fps.', 'That is roughly 27 % less GPU-busy time per frame (utilisation ÷ fps, from a coarse NVML counter).', 'So p2fc probably also cuts GPU-side work, and a change that only saves CPU would show up as fewer cores rather than more fps.', 'warm the GPU before scoring, since tonight its clock settled only after 5-13 min of game load.', 'add discarded runs until gpu.csv shows the steady clock.', 'Also rotate the first arm across rounds.', 'reads as WARN')
SRC(W4C, '- **B gives no gain.**', '**+2.6 % [−1.2, +6.5]** (B was lower in 1 of 6 rounds)', '1/6 (p 0.219)',
    'fps is **−1.7 % [−4.9, +1.7]** and CPU is **+0.063 cores [−0.007, +0.133]**. Every CI includes 0.',
    "Agent 7's T-std read-out agrees: +2.7 % [−0.8, +6.3] median and −2.0 % [−4.8, +1.0] fps.",
    "gives B **+1.4 % [+0.5, +2.3]", "**−0.8 % [−1.0, −0.6]", '(light-share WARNING)',
    "B's extra >6 ms frames all come from two back-to-back runs, 0251-B-r3 and 0253-B-r4, between 02:51 and 02:56.",
    "Without those two runs, B's tails match d0's.", "It is W4c's only flagged run.", 'all 13 runs were clean',
    "Don't adopt B for performance.", "W4c shows that B gives no gain on tonight's host. It does not show why W4b's hint appeared.",
    'ran on the **best_efficiency** overlay', '| W4c | +9.5 % |', '| W6 (pass 1 / pass 2) | +15.9 % / +8.6 % |', '+15.0 % / +6.3 %', '+8.0 % / +2.0 %',
    'W4b showed B at +6.4 % fps (+15.1 % without its run 6).', "so W4c refutes the hint only for tonight's host", 'The per-second audit shows host CPU load in both: a 2-second burst in 0251 and raised load through 0253.', 'Telling 1 % apart from 0 would need a second pass with a GPU warm-up before scoring', '**Cause: GPU warm-up (audit §5.5).**', 'the GPU ran above its steady 832 MHz in the first runs', 'In W4c that was 1021 MHz for d0-r1 and 855 MHz for B-r1; every later run sat at 832 MHz.', '**Lead: at steady state this host looks GPU-limited.** d0 and B ran at 98-100 % GPU utilisation at 832 MHz.', 'warm the GPU before scoring, since tonight its clock settled only after 5-13 min of game load.', 'Also rotate the first arm across rounds.')
SRC(G12, '## Verdicts: all 7 windows PASS', '"WARN, finding 10, Agent 1 22:25"', '`hang-36276.dmp`', '**The timed runs are clean.**',
    'Every window passes G2, G3, G9, G10, G11 and G12.', '#8 p2fc r2, 4.64', '#4 q125 r1, 4.62; #12 q125 r3, 4.58',
    '**W5 ran under `best_efficiency`.**', 'best_performance', 'There are 0 hits in all 7, so no process was left over.', 'MsMpEng')
SRC(A6, '**No FAIL in any of the 7 dirs (135 runs).**', '6 runs miss the `Execution complete` line. This is a benign race in the hard-exit path',
    "the shutdown watchdog fired 3 s after WM_CLOSE", "It's a first sighting: 1 of 135 runs.", '0 STUCK-LOCK, 0 dumps;',
    'are exactly the switch proof lines', '42 of 42 runs OK, with 0 mismatches', '| W4c | b, cold-d0 | 0 | 0 NEW, GONE or ONLY keys. |',
    'precise wait', 'keep-watch', 'WM_CLOSE + 2 s')
SRC(F10, '**No hang on a quiet host.**', '0 STUCK-LOCK events and 0 dumps', 'to the end of the L route with 3/3 tags. This is n = 1 per set.',
    'The worst frame was 2.89 s in f10b and 1.79 s in f10a.', "the detector's 5 s threshold",
    '4.9-8.0 s (gate B, same set as f10b) and 12.0 s (s4b20, same set as f10a), and all four of those runs hung',
    '**The starved host, not the GPU, stretched the stall.**', 'took 0.29-0.98 ms on the quiet host and 1.79-6.05 ms under the build',
    '60921 syncs in gate B vs 45458 in f10b', "f10b's 2736-sync frames still cost 2.66-2.89 s on the quiet host",
    'so a busier host or a slower PC could push one past 5 s', "**f10a's set (M1, C1 off) never makes the 2736-sync bursts.**",
    'Processor(_Total) at most 40 % over 10 s', 'No build process', 'f10a ran 05:58-06:05', 'f10b 06:08-06:16',
    'shared_memory_upload_nontemporal_copy=true', 'slow_frame_log_ms=1', 'devoff4b', 'about 8 busy threads', 'A second quiet pair')
SRC(SCR, 'Result, 23 Nov 06:14:40: **45/45 PASS**', 'L417-419 only.', 'read with the existing `Get-P` (L65, reads through `PSObject.Properties`)',
    "A missing value reads as ''", '565D30D40DC5025AD63FD9B9F606724BABC167BC81FCB6FBEB6362B603977112',
    'pins the fixed night launcher `565D30D4...` instead of `16B90FA8...` (Agent 10\'s condition 1)', 'repo-relative paths (N1)', 'N2 (L57', '(N3)',
    '`Remove-ItemProperty` only in `Restore-Screensaver`', 'after Agent 8 (owner of run-matrix.ps1) and Agent 10 have read this delta',
    'has exited at 07:30')
SRC('build/agent10/t27/scrnsave-delta.md', '**Verdict: SAFE.** Install it with `install-scrnsave.ps1`', '**Verdict: SAFE.** Both scripts copy nothing unless every check passes')
SRC('build/agent5/scrnsave-fix/install-log.txt', 'install-scrnsave.ps1 -Check starts', 'REFUSED: a launcher process is running: pid 19960', 'nothing was copied')
cm = open(P('DimensionsRecomp/rexlego/CMakeLists.txt'), 'rb').read().decode('utf-8').split('\n')
if 'LEGODIMENSIONS_SCENE_WALK_PROBE' not in cm[158] or 'OFF' not in cm[158] or 'FATAL_ERROR' not in (cm[160] + cm[161]):
    fail('rexlego/CMakeLists.txt L159-162 not as expected')
if os.path.exists(P('DimensionsRecomp/rexlego/src/scene_walk_probe.cpp')):
    fail('scene_walk_probe.cpp exists now')
for d in ('build/agent12/w6-gates/night', 'build/agent6/w6', 'build/agent8/readout/w-followup/a7', 'build/agent8/readout/w-followup/mine',
          'build/agent3/runs/20261123-055810-f10a-m1-sfl-level', 'build/agent3/runs/20261123-060847-f10b-p2fc-level'):
    if not os.path.isdir(P(d)):
        fail('no dir ' + d)
for f in ('build/agent8/readout/w-followup/audit/audit.md', 'build/agent8/readout/w-followup/xcheck/xcheck.md', 'build/agent6/wnight/w9_envcheck.py',
          'build/agent5/scrnsave-fix/results/summary-new-061440.txt', 'build/agent11/resume/facts-perfopt.md',
          'build/agent5/scrnsave-fix/new/day/run-day.ps1', 'build/agent5/scrnsave-fix/day-update.ps1', 'build/agent5/scrnsave-fix/install-scrnsave.ps1'):
    if not os.path.isfile(P(f)):
        fail('no file ' + f)
print('checks done')
T = datetime.datetime.now().strftime('%H:%M'); BK = 'S4-DRAFT.%s-%s.md' % (T.replace(':', ''), H0[:8])
W6F = ("    - **Agent 8's formal read-out (06:39, `build/agent8/readout/w-followup/W6.md`; both passes pooled as 10 rounds): p2fc's gain is solid.** "
       "Paired median frame time −10.3 % [−13.6, −6.9] (p2fc lower in 9 of 10 rounds, sign test p 0.021), fps +18.0 % [+14.1, +22.0] and −0.249 core "
       "[−0.303, −0.195], so CPU time per frame drops by about 24 %; Agent 7's primary read-out (B-block T-std) agrees: −9.9 % [−12.5, −7.3] median and "
       "+17.0 % [+14.2, +19.8] fps. It holds in each pass (−8.9 % [−16.2, −1.0] and −11.7 % [−15.1, −8.3]) and in every sensitivity cut, with and without "
       "the flagged runs (−9.4 to −12.2 % median, +16.9 to +20.3 % fps, −0.22 to −0.27 core; every CI excludes 0). The runner's −14 % / +22 % are pass-2 "
       "ratios of the arm medians (pooled: −12.8 % / +21.8 %), and round 1 favours s0 in both passes, from GPU warm-up (after the idle gap the GPU ran above its steady 832 MHz, its thermal limit, in the first runs, and run fps follows the GPU clock; audit §5.5): without round 1 the paired median is −12.2 % "
       "[−13.2, −11.3] (8 of 8 rounds). **C1 is confirmed:** p2fc − p2f was negative in 10 of 10 rounds, mean −0.261 ms [−0.322, −0.199] (p 0.002), "
       "and p2 and p2f are null (−0.0 % [−3.0, +3.1] and +0.4 % [−2.1, +3.1] median; p2f's +0.039 core [+0.006, +0.072] is a lead). **The pass-2 p99.9 "
       "comes from an episode that hit all four arms, not from p2fc:** from about 03:25 to 03:41, 8 consecutive runs had 33-58 frames over 6 ms (against 1-6), 3 of "
       "them p2fc's, and no recorded host or game counter shows its cause (audit §5.1); the paired p99.9 difference p2fc − s0 is −0.276 ms [−0.951, +0.400], the medians without the episode are 5.682 ms (p2fc) and "
       "5.714 ms (s0), and p2fc had 0 frames over 16.7 ms in 231k (s0 1, p2f 11; p2f's 45.67 ms frame in 0352 was a host burst). Lead: heavy frames "
       "may be ~2-3 % slower (Agent 7's p99 +1.7 % [+0.9, +2.6]; frames of 4.5 ms or more +2.9 % [+2.3, +3.5]), while raw p99 isn't higher and the "
       "1 % low fps doesn't move (−1.3 % [−4.9, +2.5]). Lead: at steady state this host looks GPU-limited: after round 1, s0, p2 and p2f ran at 97-100 % GPU utilisation and p2fc at 86-89 % while giving 18 % more fps, roughly 27 % less GPU-busy time per frame (a coarse NVML counter), so p2fc probably also cuts GPU-side work, and a change that only saves CPU would show up as fewer cores rather than more fps. All 42 runs clean: 0 KILLED, STUCK-LOCK, hang dumps or slow-state runs (my 3-mode timerq copy "
       "found 0 slow runs). Caveats: there is no C1-only arm, and keep-watch was timed with verify off, so a verify-on build might give back part of "
       "the gain. **Verdict: p2fc gains, solidly, all from C1; p2 and p2f have no timing effect.**")
W4CF = ("    - **Agent 8's formal read-out (06:40, `build/agent8/readout/w-followup/W4c.md`): B gives no gain.** Paired median +2.6 % [−1.2, +6.5] "
        "(B lower in 1 of 6 rounds, p 0.219), fps −1.7 % [−4.9, +1.7] and +0.063 core [−0.007, +0.133]; every CI includes 0, and Agent 7's T-std "
        "agrees (+2.7 % [−0.8, +6.3] median, −2.0 % [−4.8, +1.0] fps). Lead, not a finding: without round 1, T-std gives B +1.4 % [+0.5, +2.3] median "
        "and −0.8 % [−1.0, −0.6] fps (with a light-share warning), so B may be about 1 % slower. B's extra frames over 6 ms all come from 0251-B-r3 and "
        "0253-B-r4 (02:51-02:56; 0253 is the window's only flagged run), where the per-second audit shows host CPU load (a 2 s burst in 0251, raised load through 0253), and without them B's tails match d0's. All 13 runs clean. W4b showed B at +6.4 % fps (+15.1 % without its run 6), outside W4c's fps CI, but W4b ran on "
        "best_efficiency and before the Defender exclusion, so W4c refutes the hint only for tonight's host and doesn't show why it appeared. "
        "**Verdict: don't adopt B for performance;** telling 1 % from 0 would need a second pass with a GPU warm-up before scoring.")
FS = '\n'.join([
 "- **The formal sources so far (@T@; §6):**",
 "  - **Agent 12's gates** (`build/agent12/w6-gates/NIGHT-RESULTS.md`): all 7 windows PASS, and every window passes G2, G3, G9, G10, G11 and G12 "
 "(STRICT, MsMpEng 0.00), with 0 leftover processes. W6's raw G8 FAIL in both passes comes only from side gate A's finding-10 dump "
 "(`hang-36276.dmp`, waived as \"WARN, finding 10, Agent 1 22:25\"); the timed runs are clean. Flagged runs (non-game load): p2fc r2 in W6's first "
 "pass (4.64), q125 r1 and r3 in W9's second (4.62, 4.58); each verdict is also given without the rounds that hold one. G11: every night run had "
 "the best_performance overlay, with no change inside a window, but W5 ran on best_efficiency (and so did W4b, per Agent 8), so absolute numbers "
 "don't compare across.",
 "  - **Agent 6's logdiffs** (`build/agent6/wnight/RESULTS.md`): no FAIL in the 7 dirs (135 runs), 0 STUCK-LOCK and 0 dumps, and the ONLY keys "
 "are exactly the switch proof lines (p2fc's 3 C1 keep-watch lines, the q arms' back-off init line, d11p's `TimerQueue: precise wait` line; none in "
 "W4c). W9's env and quantum proof: 42 of 42 runs OK, 0 mismatches. NOTEs: 6 runs miss the `Execution complete` line (a benign race in the "
 "hard-exit path), and in W9's `0128-off-r2` the shutdown watchdog fired 3 s after WM_CLOSE, after a valid measured window: a first sighting, 1 of "
 "135; if it recurs, a dump at about WM_CLOSE + 2 s would show where the UI thread is.",
 "  - **Agent 8's read-outs:** W4c and W6 (first posted 06:17 and 06:31, revised 06:40 and 06:39), under their bullets above; W9's and W5b's are pending. In every window the first scored "
 "run, the base arm's, was its fastest (+2.0 to +15.9 % fps over that arm's other runs), which shrinks the paired gains. The cause is GPU warm-up (audit §5.5): after each idle gap the GPU ran above its steady 832 MHz, its thermal limit, in the first runs, and run fps follows the GPU clock. Agent 8 suggests "
 "warming the GPU before scoring, for example with discarded runs until gpu.csv shows the steady clock (it settled after 5-13 min of game load), and rotating the first arm across rounds. Lead: at steady state this host looks GPU-limited (every arm without C1 ran at 97-100 % GPU utilisation at 832 MHz in W6 and W4c), so a change that only saves CPU would show up as fewer cores rather than more fps. An independent cross-check agrees with results.csv in 1620 of 1620 items "
 "over the 7 night folders.",
 "  - **Agent 3's f10 rows** (`build/agent3/f10/RESULTS.md`, 06:22): no hang on a quiet host, n = 1 per set; a second quiet pair runs this morning (§5).",
 "  - **Agent 5's SCRNSAVE fix** (`build/agent5/scrnsave-fix/README.md`): staged, 45/45 tests PASS at 06:14:40, rated SAFE by Agent 10 (next bullet).",
 "  - **The leans now:** keep p2fc (the W6 read-out confirms it) and drop B (the W4c read-out confirms it); q500 and d11p stay runner-summary "
 "leans, with clean gates and logdiffs, until the W9 and W5b read-outs."])
UPD = ("- Updated at @T@ (the formal sources): the header; this block (the intro, the W6 and W4c read-out sub-bullets, the formal-sources bullet and "
       "the SCRNSAVE sentence); Decisions item 2; Still open (the night's read-outs, in W5's item); row 30 (only its CMake option is committed); §2c "
       "(the W6, W9, W5b and W4c rows); §4b (a 05:58-06:40 entry and Possible changes); §5 (finding 10: the quiet-host rows); §6 (the formal sources).")
H4B = ("- **05:58-06:40 (the formal sources; Changed since 23:29):** Agent 12's gates: all 7 windows PASS. Agent 6's logdiffs: no FAIL in 135 runs. "
       "Agent 3's quiet-host rows f10a and f10b: no hang, n = 1 per set (§5). Agent 5's SCRNSAVE fix: staged, 45/45 tests, rated SAFE by Agent 10. Agent 8's formal read-outs: "
       "W4c, no gain for B (06:17), and W6, p2fc's gain solid and all from C1 (06:31), revised at 06:40 and 06:39 with the same numbers (the pass-2 tail's episode has no recorded cause, round 1's bias is GPU warm-up, and a lead that the host is GPU-limited at steady state). W9's and W5b's read-outs are pending.")
F10P = ("**Nov 23, the quiet-host rows (Agent 3, `build/agent3/f10/RESULTS.md`, 06:22): no hang on a quiet host.** f10a (s4b20's set: M1 = "
        "`shared_memory_upload_nontemporal_copy=true`, C1 off) ran 05:58-06:05 and f10b (gate B's p2fc set) 06:08-06:16, both on devoff4b with "
        "`slow_frame_log_ms=1`, after a quiet gate (no build process, Processor(_Total) at most 40 % over 10 s). Both reached the end of the L route "
        "with 3/3 tags, with 0 STUCK-LOCK and 0 dumps. The worst frame was 1.79 s (f10a) and 2.89 s (f10b), under the detector's 5 s threshold, "
        "against 4.9-8.0 s (gate B, f10b's set) and 12.0 s (s4b20, f10a's set) under the -j8 build, where all four runs hung. The starved host, not "
        "the GPU, stretched the stall: for the same frames and sync counts, each host-to-GPU round trip took 0.29-0.98 ms quiet against 1.79-6.05 ms "
        "under the build, and more draws took the full-path sync under load (60921 syncs in gate B against 45458 in f10b). The margin is modest: "
        "f10b's 2736-sync frames still cost 2.66-2.89 s, so a busier host or a slower PC could push one past 5 s, while f10a's set (M1, C1 off) never "
        "makes those bursts. n = 1 per set; a second quiet pair (n = 2) runs this morning, with its summary due after 07:20 (Agent 1, 06:34), and a "
        "controlled-load repeat (~8 busy threads) and an s4b20-style row under load with the slow-frame log are offered, not run. The night's 135 "
        "timed runs had 0 STUCK-LOCK (Agent 6; the W6 and W4c read-outs: 0 at every owner site).")
S6 = ("- **The formal sources** (read at @T@): Agent 12's gates `build/agent12/w6-gates/NIGHT-RESULTS.md` (per-window outputs in "
      "`build/agent12/w6-gates/night/`); Agent 6's logdiffs `build/agent6/wnight/RESULTS.md` (W6's in `build/agent6/w6/`; the W9 env and quantum "
      "check `build/agent6/wnight/w9_envcheck.py`); Agent 8's read-outs `build/agent8/readout/w-followup/W4c.md` and `W6.md` (with `a7/`, `mine/`, "
      "`audit/audit.md` and `xcheck/xcheck.md` beside them); Agent 3's quiet-host rows `build/agent3/f10/RESULTS.md` (runs "
      "`build/agent3/runs/20261123-055810-f10a-m1-sfl-level` and `20261123-060847-f10b-p2fc-level`); Agent 5's SCRNSAVE fix "
      "`build/agent5/scrnsave-fix/README.md` (tests `build/agent5/scrnsave-fix/results/summary-new-061440.txt`); the committed state's fact sheet "
      "`build/agent11/resume/facts-perfopt.md`.")
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
    r = fn(L[ix[0]])
    if r is None:
        fail('line %s: unexpected text' % name); return
    L[ix[0]] = r; new = '\n'.join(L); print('line', name, 'L%d' % (ix[0] + 1))
sub('head', 'and on Nov 23 at 05:55 under task #25', 'and on Nov 23 at 05:55 and @T@ under task #25')
sub('intro', "The numbers below are Agent 1's runner summaries, not the formal read-outs; I replace them as the read-outs land:",
    "At 05:55 the numbers below were Agent 1's runner summaries. At @T@, Agent 8's formal read-outs of W6 and W4c are added under their bullets, "
    "W9 and W5b are still runner summaries, and Agent 12's gates, Agent 6's logdiffs, Agent 3's f10 rows and the SCRNSAVE fix's tests are in (the "
    "05:55 version is kept in `build/agent11/s4draft/@BK@`):")
line('w6', '  - **W6** (devoff4b; 00:09:02-00:51:52', lambda l: l + '\n' + W6F)
line('w4c', '  - **W4c** (codegen B again: d0 = devoff2-bin', lambda l: l + '\n' + W4CF)
line('leans', '- **The leans, before the formal read-outs:**', lambda l: l + '\n' + FS)
sub('scrn', "The SCRNSAVE fix (run-matrix.ps1 L417 reads the value through PSObject.Properties, or the launcher sets '' instead of removing it; "
    "run-day.ps1 probably has the same code) is staged by Agents 5 and 8 and installed after 07:30, with reviews by Agents 8 and 10, before RUN-DAY "
    "or another night (L3220-3221, L3304, L3312).",
    "The SCRNSAVE fix is staged by Agent 5 in `build/agent5/scrnsave-fix/` (45/45 tests PASS at 06:14:40): run-matrix.ps1 L417-419 read the four "
    "screensaver values with its existing `Get-P` (L65, through PSObject.Properties), so a missing value reads as ''; the night launcher sets '' "
    "instead of removing the value and removes it only in Restore-Screensaver (new run-night.ps1 565D30D4…); the day draft had the same code and is "
    "regenerated from the fixed launcher into `build/agent5/scrnsave-fix/new/day/`, with make-run-day.ps1 pinning 565D30D4… instead of 16B90FA8… (Agent 10's condition 1, met in staged form) and N1-N3 fixed; `day-update.ps1` copies it into `build/agent5/day-draft/` after the install. "
    "Agent 10 rated the delta and its install tooling SAFE (`build/agent10/t27/scrnsave-delta.md`), and `install-scrnsave.ps1 -Check` refused at 06:36 while the night launcher ran, copying nothing, as designed (`build/agent5/scrnsave-fix/install-log.txt`). It is installed after the launcher exits at 07:30, once Agent 8 (run-matrix.ps1's owner) has read the delta too, and before RUN-DAY or "
    "another night (L3220-3221, L3304, L3312).")
line('upd', '- Updated at 05:55 (SESSION2 to L3313):', lambda l: l + '\n' + UPD)
sub('open', "The formal read-outs of tonight's windows, both passes, are Agents 7 and 8's, due ~10:00 (L3301; Changed since 23:29).",
    "The formal read-outs of tonight's windows, both passes, are Agents 7 and 8's (L3301): W4c's and W6's landed at 06:17 and 06:31, and W9's and "
    "W5b's are due by ~10:00 (Changed since 23:29).")
sub('dec2', 'the leans are p2fc, q500, d11p and dropping B, pending the formal read-outs.',
    "the leans are p2fc, q500, d11p and dropping B; Agent 8's formal read-outs confirm p2fc (W6: −10.3 % median, all from C1) and dropping B "
    "(W4c: no gain), and W9's and W5b's are pending.")
R30O = '| proposed |'
R30N = ("| proposed. **Only its CMake option is committed** (b0bd3b4, OFF): the probe source `src/scene_walk_probe.cpp/.h` isn't written, so turning "
        "the option on stops at configure, by design (`DimensionsRecomp/rexlego/CMakeLists.txt` L159-162; Nov 23) |")
line('r30', '| 30 | Scene-walk count probe', lambda l: l[:-len(R30O)] + R30N if l.endswith(R30O) else None)
sub('w6row', "the formal read-out checks p2fc's p99.9 (6.49 against 5.74 ms) (SESSION2 L3222-3229, L3266-3273; Changed since 23:29) |",
    "the formal read-out checks p2fc's p99.9 (6.49 against 5.74 ms) (SESSION2 L3222-3229, L3266-3273; Changed since 23:29). **Formal read-out "
    "(Agent 8, 06:39; 10 rounds pooled): p2fc's gain is solid,** paired median −10.3 % [−13.6, −6.9], fps +18.0 % [+14.1, +22.0], −0.249 core "
    "[−0.303, −0.195], all from C1 (p2fc − p2f lower in 10 of 10 rounds); p2 and p2f no timing effect; the pass-2 p99.9 came from an episode "
    "(~03:25-03:41, cause unrecorded) that hit all four arms, not from p2fc; lead: heavy frames may be ~2-3 % slower; the same verdict with and without the flagged runs. "
    "Gates PASS in both passes (G8's raw FAIL is gate A's waived finding-10 dump, read as WARN; the timed runs are clean; flagged: p2fc r2 in pass "
    "1); Agent 6: 0 FAIL, and p2fc's only ONLY keys are its 3 C1 keep-watch lines |")
sub('w9row', 'lean q500 (L3233-3239, L3277-3287; Changed since 23:29) |',
    "lean q500 (L3233-3239, L3277-3287; Changed since 23:29). Gates PASS in both passes (flagged: q125 r1 and r3 in pass 2); Agent 6: 0 FAIL, the "
    "back-off init line only in the q arms, and the env and quantum proof 42 of 42; the shutdown watchdog fired once, 3 s after WM_CLOSE "
    "(0128-off-r2, after a valid measured window; a first sighting, 1 of 135). Formal read-out pending |")
sub('w5brow', 'lean d11p (SESSION2 L3243-3249, L3291-3296; Changed since 23:29) |',
    "lean d11p (SESSION2 L3243-3249, L3291-3296; Changed since 23:29). Gates PASS in both passes; Agent 6: 0 FAIL, and the only ONLY key is "
    "d11p's `TimerQueue: precise wait` line. The night ran on best_performance and W5 on best_efficiency (G11), so W5b and W5 agree in direction "
    "and order only. Formal read-out pending |")
sub('w4crow', '13 of 13 OK, 12 scored (runner summary): B median +1.3 %, fps −0.4 %, +0.07 core, slower in 5 of 6 rounds, so the hint did not '
    'repeat; lean: drop B.',
    "13 of 13 OK, 12 scored (runner summary): B median +1.3 %, fps −0.4 %, +0.07 core, slower in 5 of 6 rounds, so the hint did not repeat; lean: "
    "drop B. **Formal read-out (Agent 8, 06:40): no gain;** paired median +2.6 % [−1.2, +6.5] (B lower in 1 of 6 rounds), fps −1.7 % [−4.9, +1.7], "
    "+0.063 core [−0.007, +0.133], every CI including 0, and Agent 7's T-std agrees; lead: without round 1, B may be ~1 % slower; all 13 runs "
    "clean; gates PASS; Agent 6: no ONLY keys. W4b (B +6.4 % fps) ran on best_efficiency, before the Defender exclusion, so this refutes its hint only for tonight's host "
    "and doesn't show why it appeared. **Verdict: don't adopt B for performance.**")
line('h4b', '- **23:47-05:44 (L3202-3313):**', lambda l: l + '\n' + H4B)
sub('poss', "Next, before the break: the formal read-outs of both passes (Agents 7 and 8), Agent 6's logdiffs, Agent 12's gates and Agent 3's "
    "f10a/f10b rows.",
    "Since 05:55: Agent 12's gates, Agent 6's logdiffs, Agent 3's f10a/f10b rows, Agent 8's W4c and W6 read-outs and the SCRNSAVE fix's tests "
    "(Changed since 23:29). Next, before the break: the W9 and W5b read-outs (Agents 7 and 8) and Agent 3's second quiet pair.")
sub('f10', "**Nov 23:** Agent 3 runs the two quiet-host rows (f10a, f10b) this morning as part of the wrap-up (L3302); I fold their result in "
    "when it lands, and the W6 read-out reports STUCK-LOCK counts per arm (L2902-2907).", F10P)
line('s6', '- **The night of Nov 22-23 and the wrap-up** (read at 05:55):', lambda l: l + '\n' + S6)
for tok, val in (('@T@', T), ('@BK@', BK)):
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
if b'\r' in nb or '@T@' in new or '@BK@' in new:
    fail('CR or token left')
print('new %d B, %d LF (+%d)' % (len(nb), nb.count(b'\n'), nb.count(b'\n') - raw.count(b'\n')))
if nb.count(b'\n') != 561:
    fail('expected 561 LF')
ol, nl = old.split('\n'), new.split('\n'); dry = []
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=ol, b=nl, autojunk=False).get_opcodes():
    if tag != 'equal':
        dry.append('=== %s old L%d-%d -> new L%d-%d' % (tag, i1 + 1, i2, j1 + 1, j2))
        dry += ['--- %d: %s' % (i + 1, ol[i]) for i in range(i1, i2)] + ['+++ %d: %s' % (j + 1, nl[j]) for j in range(j1, j2)]
        print(dry[-1 - (i2 - i1) - (j2 - j1)])
if DRY:
    open(P('build/agent11/s4draft/run18-dry.txt'), 'wb').write(('\n'.join(dry) + '\n').encode('utf-8'))
    print('DRY: %d failures' % len(fails)); sys.exit(1 if fails else 0)
if fails or os.path.exists(HOLD):
    sys.exit('not written')
bk = P('build/agent11/s4draft/' + BK)
if os.path.exists(bk) or sha(open(DOC, 'rb').read()) != H0:
    sys.exit('backup exists or doc changed')
open(bk, 'wb').write(raw)
open(DOC, 'wb').write(nb); chk = open(DOC, 'rb').read()
print('WROTE sha256 %s %d B %d LF CR %d; backup %s' % (sha(chk), len(chk), chk.count(b'\n'), chk.count(b'\r'), BK))

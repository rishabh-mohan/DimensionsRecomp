# Agent 11, task #25 pass B (07:25): gated edits of S4-DRAFT.md (S4) and FINDINGS-AND-CHANGES.md (FN).
# Usage: python passb.py S4|FN --dry|--apply HHMM
# Gates: sha prefix + LF count + no CR/BOM; every old text exactly once; SRC quotes present in the sources;
# cited SESSION2/PROPOSAL lines hold the quoted text; backticked paths exist; style checks; backup on apply.
import sys, re, os, hashlib, shutil
sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')

doc, mode, TT = sys.argv[1], sys.argv[2], sys.argv[3]
assert doc in ('S4', 'FN') and mode in ('--dry', '--apply') and re.fullmatch(r'\d{4}', TT)
T = TT[:2] + ':' + TT[2:]
DOCS = {
    'S4': ('perf-notes/S4-DRAFT.md', '017085DF', 561, 'build/agent11/s4draft/S4-DRAFT.%s-017085DF.md' % TT),
    'FN': ('perf-notes/FINDINGS-AND-CHANGES.md', '9AF761BE', 410, 'build/agent11/s4draft/FINDINGS-AND-CHANGES.%s-9AF761BE.md' % TT),
}
path, pre, nlf, backup = DOCS[doc]
WS = '<workspace>/'
fails = []

def rd(p):
    b = open(p, 'rb').read()
    return b.decode('utf-16') if b[:2] in (b'\xff\xfe', b'\xfe\xff') else b.decode('utf-8', errors='replace')

def lines(p):
    return re.split(r'\r\n|\n|\r', rd(p))

# ---------------- sources ----------------
W9 = 'build/agent7/readout/W9.md'
P5 = 'build/agent7/readout/pool-W5b.md'
TC = 'build/agent7/readout/tail-check.md'
A8C = 'build/agent8/readout/w-followup/a7check/W9-W5b-check.md'
F10 = 'build/agent3/f10/RESULTS.md'
F10R = 'build/agent10/t27/f10-rating.md'
R21 = 'build/agent10/t27/r21-s4t1.md'
R1S2 = 'build/agent7/s4-r1s2/README.md'
S33D = 'build/agent6/s33-popin/DESIGN.md'
S33C = 'build/agent6/s33-popin/CHECK.txt'
S2 = 'perf-notes/SESSION2.md'
A4H = 'build/agent4/HANDOFF.md'
PROP = 'build/agent8/w-followup/PROPOSAL.md'

SRC = {
    W9: ['-0.75 core [-0.86, -0.64], -30.0 % *. No p99 or 1 % low loss in any method.',
         'Same pick: -0.79 core [-0.84, -0.73]. p99 and 1 % low are better than off (T-std p99 -0.8 % *, 1 % low +2.2 % *).',
         '-0.70 core (-27.9 %), fps +1.1 %, p99 4.675 vs 4.985 ms',
         'No CPU drop: -0.03 core [-0.14, +0.08]. Raw median ms is higher in 8 of 8 rounds.',
         'costs ~0.5-0.8 % median frame time. The saving needs Q > 0.',
         'All 6 slow q runs ran during two load bursts in pass 2 (ng_t 2.91-4.06). The same arms ran normally before, between and after the bursts.',
         'Without the flagged runs, q125 and q250 sit next to q500: cores -0.72 each vs -0.79.',
         'The pool numbers its rounds 1-4 (pass 1) and 5-8 (pass 2).', 'all 40 kept runs', 'without the 7 flagged runs',
         'ng_t = non-game busy cores', 'Two host-load flags apply'],
    A8C: ['728 claims, 3072 numbers: 699 agree (65 only with rounded inputs, 0 with the stated alternative), 29 disagree, 0 parse problems.',
          'Disagreements by gap (last-digit units): 0.5-0.6: 14; 0.6-1: 4; 1-2: 8; > 2: 3. Sign flips: 0.',
          'it shares no code with either pool_readout.py',
          '| pool-W9.md L201 | W9 light share one-way F (df1, df2) | 9.38 (4, 35) | 9.679 4 35 | DISAGREE | 29.86 |',
          '| pool-W5b.md L226 | W5b light share one-way F (df1, df2) | 1.18 (2, 33) | 1.214 2 33 | DISAGREE | 3.43 |',
          '| W9.md L78 | light share one-way F (df1, df2) | 9.38 (4, 35) | 9.679 4 35 | DISAGREE | 29.86 |'],
    P5: ['kept 36 of 38 runs (d11 12, d11t 12, d11p 12)', 'pooled rounds 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12',
         'Primary: B-block T-std.** Round effect on median ms: F = 4.11 on (11, 22), p = 0.002',
         '| **B-block T-std** | median ms | 3.3 | 1.6 | 2.4 | 22 | +1.2 [-0.2, +2.6] | +0.5 [-0.9, +1.9] |',
         '| **B-block T-std** | fps | 2.9 | 1.2 | 1.8 | 22 | -1.1 [-2.1, -0.0] * | -0.7 [-1.8, +0.3] |',
         '| **B-block T-std** | p99 ms | 1.7 | 0.7 | 1.1 | 22 | +0.3 [-0.3, +1.0] | +0.0 [-0.6, +0.6] |',
         '| **B-block T-std** | 1 % low fps | 11.6 | 4.5 | 6.9 | 22 | -2.8 [-6.5, +1.0] | -0.2 [-4.0, +3.7] |',
         '| cpu cores | 2.55 | 2.33; -0.22 [-0.25, -0.19]; -8.6 [-9.8, -7.4] *; -8.6 [-9.6, -7.6] * | 2.34; -0.20 [-0.23, -0.17]; -8.0 [-9.2, -6.8] *; -8.0 [-9.0, -7.0] * |',
         '| TimerQueue busy % | 23.17 | 1.97;', '| 2.08; -21.08',
         '**no-slow-d11t** (left out: 0455-d11t-r1, 0459-d11t-r2)',
         '| B-block T-std fps | -0.4 [-1.2, +0.3] | -0.7 [-1.4, -0.1] * |',
         'overlay best_performance 38/38', "compare arms within this window only, not with W5's absolute numbers",
         '(19 rows; rounds 7-12 pooled; windows 04:53:03-05:29:47'],
    TC: ['| 20261123-0155 | 0221-d11t-r5 | d11t | 19119 | yes | 11.672 | 26.366 | 38 | 27 | 6 |'],
    F10: ['Status: **done, n = 2 per set.**', "| f10a2 | s4b20's (M1, C1 off) | 06:32-06:40 | PASS |", "| f10b2 | gate B's (p2fc) | 06:40-06:47 | PASS |",
          'One-sided Fisher exact p = 0.07 (0/4 quiet vs 4/6 loaded', "Under last night's -j8 build, 4 of the 6 runs in the same hour hung",
          'Quiet worst frames: 1.79 s (f10a), 1.54 s (f10a2), 2.89 s (f10b), 1.79 s (f10b2).',
          'Under the build: 7.98 s (gate B), 9.66 s (gate A), 12.04 s (s4b20), 13.14 s (s4b24).',
          'waited 5-30x longer per round trip than on the quiet host, and the CPU-only part of the frame grew 1.7-2.4x',
          "GPU clocks weren't logged", 'That could explain a modest slowdown, not a 5-30x one.',
          '**Retracted from n = 1:** "under load more draws took the full-path sync".',
          "f10a 18810 vs f10a2 28030, and f10b 45458 vs f10b2 77236. f10b2's total is more than gate B's 60921.",
          'Which bursts happen depends on timing.', 'One more quiet pair with no hang would give p = 0.03 (0/6 vs 4/6).',
          '| 0.98 (f10b), 0.21 (f10b2) | 6.05 (gate B, hung)', '| 0.29 and 0.37 (f10b), 0.18 (f10b2) | 1.79 (gate B, hung)'],
    F10R: ["Agent 10, 2026-11-23 06:55 (cross-checked against Agent 3's RESULTS.md at 07:05)", '**Verdict: all 4 rows PASS.**',
           '**finding 10 stays a load-only WARN.**', "hasn't run yet. It's a precondition for C1 default-ON",
           "Not reproducing the hang doesn't fix it, because the mechanism is still there.", "a third quiet pair, which gives p = 0.03 if it's clean;"],
    R21: ['| (a) default-off test bed | **SAFE** |', '| (b) value 3 in F1, F3, W1 and W8b | **SAFE-IF** the 5 conditions in (b) hold |',
          '| (c) MP4 restatement and the §9 code reads | **ACCEPTED**, with one wording fix (§9.2) and one addition (F-CA under MP4 gap 2) |',
          '5. **A th2 hang is checked against F-CA first.** My helper found a th2-only deadlock path that exists without #21',
          'The EcoQoS half of value 3', 'Running values 1 and 2 only if 3 helps'],
    R1S2: ['(OFF by default, kInitOnly)', '+320/-1 over 5 files', 'proofs P1-P10 | ALL PASS 23:10'],
    S33D: ['It touches 4 files with 10 hunks, +105/-24. `git apply --check` passes with no offsets', 'Lifecycle `kRequiresRestart`'],
    S33C: ['(item #33, staged only; nothing applied or built)', 'Base: DimensionsRecomp/rexglue-sdk at HEAD 5350b1d'],
    S2: ['cvar d3d12_pipeline_creation_no_wait default OFF, apply --check OK on 5350b1d, not built', 'rpb0 and rpm4 PASS',
         'Agent 10 rated the day-session draft SAFE-IF (build/agent10/t27/day-draft-rating.md)',
         '(1) regenerate run-day.ps1 from the SCRNSAVE-fixed run-night.ps1',
         '(2) install per README-DAY L136-139 only after the night launcher has exited, then compare hashes; (3) Agent 11 rates it too.',
         "The install and Agent 11's rating wait until after the break.", 'day condition 1 met in staged form (run-day B67EBD6C from run-night 565D30D4)',
         'Agent 5 does (1) staged only in build/agent5/'],
    A4H: ['Pin record PASS (22:43, 0 FAIL, 0 WARN). Agent 3, 2026-11-23: boot check rpb0 PASS; matrix rpm4 PASS on every section 3(b) check. Agent 1 announces the pin.'],
    PROP: ['`GO W8a matrix-window8a.json A06E5E3AAEE25B079532DE8BFC9134D7462B5F842ECB9FADA19B6FD8DD8A475E only=n0,mc repeats=6`. 13 runs, 27.4 min, runner 30.',
           'only=n4,n4mc repeats=6`. Same size.',
           "W8a still needs: native4b-bin with Agent 2's MANIFEST sha, Agent 4's re-pin, and PASS on rpb0/rpm4 and s4b02/s4b05.",
           "promoted OK at 22:35:01 (`stage-W8a4-223501.txt`, with native4's r5/r6 functional cover)"],
}
LINECHK = [(S2, 3302, 'Agent 3: quiet-host f10a/f10b rows'), (S2, 3317, 'Agent 10 rated the day-session draft'), (S2, 3318, 'No day runs before the break'),
           (S2, 3325, 'Second pair approved'), (S2, 3326, 'day condition 1 met'), (S2, 3332, 'rpb0 and rpm4 PASS'),
           (PROP, 77, 'W8a'), (PROP, 78, 'GO W8a matrix-window8a.json'), (PROP, 80, 'W8a still needs'), (PROP, 81, 'W8a4 needs'), (PROP, 119, 'promoted OK at 22:35:01')]
SHACHK = [('build/agent8/w-followup/matrix-window8a.json', 'A06E5E3A')]

# ---------------- edits ----------------
S4E = [
('S1 intro', '''are in (the 05:55 version is kept in `build/agent11/s4draft/S4-DRAFT.0655-1B0BB0DC.md`):''',
 '''are in (the 05:55 version is kept in `build/agent11/s4draft/S4-DRAFT.0655-1B0BB0DC.md`). At {T}, Agent 7's formal W9 read-out and pooled W5b table are added under their bullets, with Agent 8's check of their numbers (the formal W5b read-out is still due); Agent 3's second quiet pair (f10, n = 2), Agent 10's f10 and #21 ratings and the re-pin rows are in too (the 06:55 version is kept in `build/agent11/s4draft/S4-DRAFT.{TT}-017085DF.md`):'''),
('S2 W9 sub-bullet', '''**Lean: q500** (L3233-3239, L3277-3287).''',
 '''**Lean: q500** (L3233-3239, L3277-3287).
    - **Agent 7's formal read-out (07:01, `build/agent7/readout/W9.md`; both passes pooled as 8 rounds, 40 kept runs): q500.** The largest CPU drop, −0.75 core [−0.86, −0.64] (−30.0 %), with no p99 or 1 % low loss in any method; without the 7 flagged runs (host-load flags), −0.79 core [−0.84, −0.73], with p99 (−0.8 %) and the 1 % low (+2.2 %) better than off (T-std; both CIs exclude 0). The runner's pass-2 numbers agree (−0.70 core, −27.9 %; fps +1.1 %; p99 4.675 against 4.985 ms). **Drop q0:** −0.03 core [−0.14, +0.08], and its raw median is higher in 8 of 8 rounds (~0.5-0.8 %); the saving needs Q > 0. **q125 and q250's unsteadiness is host-triggered, not an arm defect:** all 6 slow q runs fell in two bursts of background load in pass 2 (non-game busy cores 2.91-4.06), the same arms ran normally before, between and after them, and without the flagged runs both save 0.72 core against q500's 0.79. Agent 8's check of Agent 7's W9 and W5b numbers against results.csv (07:16, `build/agent8/readout/w-followup/a7check/W9-W5b-check.md`; its own script, with no code shared): 699 of 728 claims agree; the other 29 differ by small amounts (26 by at most 2 in the last digit; the other 3 are light-share F values, which results.csv's rounded light share can't reproduce exactly), with no sign flips.'''),
('S3 W5b sub-bullet', '''**Lean: d11p** (L3243-3249, L3291-3296).''',
 '''**Lean: d11p** (L3243-3249, L3291-3296).
    - **Agent 7's pooled table (07:02, `build/agent7/readout/pool-W5b.md`; 12 rounds, 36 kept runs; primary B-block T-std, as the round effect is significant, p = 0.002); the formal W5b read-out is still due.** d11p: −0.20 core [−0.23, −0.17] (−8.0 %), median +0.5 % [−0.9, +1.9], fps −0.7 % [−1.8, +0.3], p99 +0.0 % [−0.6, +0.6], 1 % low −0.2 % [−4.0, +3.7]. d11t: −0.22 core [−0.25, −0.19] (−8.6 %), median +1.2 % [−0.2, +2.6], fps −1.1 % [−2.1, −0.0] (the CI just excludes 0), 1 % low −2.8 % [−6.5, +1.0]. TimerQueue busy drops from 23.17 % (d11) to 1.97 % (d11t) and 2.08 % (d11p). Long frames (`build/agent7/readout/tail-check.md`, 06:54): d11t had the only frames over 16.7 ms, six, all within about 3 s of one run (0221-d11t-r5, pass 1). Without d11t's two slow pass-2 runs (0455-d11t-r1, 0459-d11t-r2), d11t's fps change is −0.4 % [−1.2, +0.3] and d11p's −0.7 % [−1.4, −0.1], so neither mode is clearly free of a small fps cost. G11: best_performance in 38 of 38 runs, so compare arms within W5b only, not with W5's absolute numbers.'''),
('S4 decisions f10', '''Agent 3 runs the two quiet-host finding-10 rows this morning (f10a, f10b; L3302; §5).''',
 '''Agent 3 ran the quiet-host finding-10 rows this morning, two pairs (f10a and f10b, then f10a2 and f10b2; L3302, L3325, L3332; §5).'''),
('S5 sources head', '''- **The formal sources so far (06:55; §6):**''', '''- **The formal sources so far (06:55, updated at {T}; §6):**'''),
('S6 A8 bullet', '''under their bullets above; W9's and W5b's are pending.''',
 '''under their bullets above. W9's formal read-out and W5b's pooled table are Agent 7's (07:01 and 07:02, under their bullets above), and Agent 8 checked their numbers against results.csv (07:16); the formal W5b read-out is still due.'''),
('S7 f10 bullet', '''(`build/agent3/f10/RESULTS.md`, 06:22): no hang on a quiet host, n = 1 per set; a second quiet pair runs this morning (§5).''',
 '''(`build/agent3/f10/RESULTS.md`, 06:22; n = 2 at 06:59): no hang on a quiet host in 4 of 4 runs (f10a, f10b, f10a2, f10b2), against 4 hangs in 6 runs under the -j8 build in the same hour (one-sided Fisher p = 0.07: it fits load as the trigger, but it isn't proof). Agent 10 (`build/agent10/t27/f10-rating.md`, 06:55, cross-checked at 07:05): all 4 rows PASS, and finding 10 stays a load-only WARN (§5).'''),
('S8 leans now', '''keep p2fc (the W6 read-out confirms it) and drop B (the W4c read-out confirms it); q500 and d11p stay runner-summary leans, with clean gates and logdiffs, until the W9 and W5b read-outs.''',
 '''keep p2fc (the W6 read-out confirms it), drop B (the W4c read-out confirms it) and the back-off at q500 (the W9 read-out confirms it, and drops q0); d11p stays the lean over d11t on Agent 7's pooled table until the formal W5b read-out (both save ~0.2 core; d11t costs ~1 % fps and had the only frames over 16.7 ms).'''),
('S9 updated-at', '''§5 (finding 10: the quiet-host rows); §6 (the formal sources).''',
 '''§5 (finding 10: the quiet-host rows); §6 (the formal sources).
- Updated at {T} (the W9 read-out, the W5b pool, f10 n = 2): the header; this block (the intro, the W9 and W5b sub-bullets, the f10 sentence of the decisions paragraph, the formal-sources bullets and the leans); Still open (W5's item, Agent 5's launcher); Decisions item 2; rows 19, 21, 33 and 34; §2c (the W8a, W9 and W5b rows, and the re-pin in the order paragraph); §4b (a 06:17-07:16 entry, Ratings still missing, the re-pin answer and Possible changes); §5 (finding 10: n = 2); §6 (the new sources).'''),
('S10 W5 item', '''W4c's and W6's landed at 06:17 and 06:31, and W9's and W5b's are due by ~10:00 (Changed since 23:29).''',
 '''W4c's and W6's landed at 06:17 and 06:31 (Agent 8), W9's at 07:01 (Agent 7; Agent 8 checked its numbers at 07:16), and W5b's pooled table at 07:02 (Agent 7); the formal W5b read-out is still due (Changed since 23:29).'''),
('S11 launcher item', '''with reviews by Agents 8 and 10 (SESSION2 L3215-3221, L3304, L3312; Changed since 23:29).''',
 '''with reviews by Agents 8 and 10 (SESSION2 L3215-3221, L3304, L3312; Changed since 23:29). At 06:05, Agent 10 rated the day-launcher draft SAFE-IF (`build/agent10/t27/day-draft-rating.md`): regenerate run-day.ps1 from the fixed run-night.ps1, install it only after the night launcher has exited and compare hashes, and my rating too. The regenerated run-day.ps1 (B67EBD6C, from run-night.ps1 565D30D4) is staged in `build/agent5/` only; the install and my rating wait until after the break (SESSION2 L3317-3318, L3326).'''),
('S12 decision 2', '''Agent 8's formal read-outs confirm p2fc (W6: −10.3 % median, all from C1) and dropping B (W4c: no gain), and W9's and W5b's are pending.''',
 '''the formal read-outs confirm p2fc (Agent 8's W6: −10.3 % median, all from C1), dropping B (Agent 8's W4c: no gain) and q500 (Agent 7's W9: −0.75 core, −30.0 %, with no p99 or 1 % low loss; drop q0); W5b's formal read-out is still due, and Agent 7's pooled table keeps d11p as the lean (both wait modes save ~0.2 core).'''),
('S13 row 19', '''| #18; A10's rating; A1's GO | design only; risk medium-high (F) |''',
 '''| #18; A10's rating; A1's GO | staged in `build/agent7/s4-r1s2/` (Nov 22, 23:10-23:32: an SDK diff, +320/−1 over 5 files, kInitOnly; proofs P1-P10 ALL PASS; functional rows, a soak plan and a W7 matrix draft beside it); not built, not rated; risk medium-high (F) |'''),
('S14a row 21 switch+rating', '''| env `LEGO_NATIVE_CHAIN_PRIORITY=1`; unset = OFF | **not rated.** F's "Agent 10 wants one more code proof" has no source in A10's notes (b2r §25 correction 6): its only threaded-mode asks are b2r row 16 item 3 (the n2/n3 rows, plus §15.4's proofs 2-5), and they are for `LEGO_NATIVE_THREADED` itself |''',
 '''| env `LEGO_NATIVE_CHAIN_PRIORITY` (values 1-3; the rows use 3, which includes an EcoQoS opt-out); unset = OFF | **rated by A10 (06:32, `build/agent10/t27/r21-s4t1.md`):** (a) the default-off test bed SAFE; (b) value 3 in F1, F3, W1 and W8b SAFE-IF 5 conditions, the fifth being F-CA, a th2-only deadlock path that exists without #21 (check a th2 hang against it first); (c) the MP4 restatement ACCEPTED, with F-CA recorded under MP4 gap 2. (Before the rating: F's "Agent 10 wants one more code proof" had no source in A10's notes, b2r §25 correction 6.) |'''),
('S14b row 21 status', '''| A10's rating; §15.4 must-prove 1-5 for threaded mode; #22's results (inconclusive: the slow state, see #22) | proposed; risk low-medium |''',
 '''| A10's rating (done: SAFE-IF); §15.4 must-prove 1-5 for threaded mode; #22's results (inconclusive: the slow state, see #22) | staged in `build/agent7/s4-t1/`, not built; risk low-medium |'''),
('S15a row 33 switch', '''| cvar, false (placeholder name `d3d12_async_pipeline_no_wait`) |''', '''| cvar `d3d12_pipeline_creation_no_wait`, false (kRequiresRestart) |'''),
('S15b row 33 status', '''opt-in and off by default (23:24) | proposed |''',
 '''opt-in and off by default (23:24) | staged in `build/agent6/s33-popin/` (06:28-06:47: an SDK patch, 4 files, +105/−24; `git apply --check` passes on 5350b1d; nothing applied or built) |'''),
('S16 row 34 status', '''| counts the draws #33 skips | with #33 | #33 | optional |''', '''| counts the draws #33 skips | with #33 | #33 | in #33's staged patch (`build/agent6/s33-popin/DESIGN.md`) |'''),
('S17 W8a row', '''| **W8a: native shaders** | native S4a |''',
 '''| **W8a: native shaders** | native S4a. Staged (Agent 8): `build/agent8/w-followup/matrix-window8a.json` (A06E5E3A…) with the GO `only=n0,mc repeats=6` (13 runs, 27.4 min, runner 30); it still needs native4b-bin with Agent 2's MANIFEST sha, Agent 4's re-pin (rpb0 and rpm4 PASS on Nov 23; Agent 1 announces the pin) and PASS on s4b02/s4b05. Fallback W8a4: `only=n4,n4mc`, the same size, on native4's r5/r6 functional cover, promoted at 22:35 (`build/agent8/w-followup/PROPOSAL.md` L77-81, L119) |'''),
('S18 W9 row', '''a first sighting, 1 of 135). Formal read-out pending |''',
 '''a first sighting, 1 of 135). **Formal read-out (Agent 7, 07:01): q500**, −0.75 core [−0.86, −0.64] (−30.0 %) with no p99 or 1 % low loss; without the 7 flagged runs −0.79 core, with p99 and the 1 % low better than off; drop q0; q125 and q250's slow runs are host-triggered (two load bursts in pass 2); Agent 8's check of the numbers: 699 of 728 claims agree, no sign flips (Changed since 23:29, the W9 sub-bullet) |'''),
('S19 W5b row', '''so W5b and W5 agree in direction and order only. Formal read-out pending |''',
 '''so W5b and W5 agree in direction and order only. **Agent 7's pooled table (07:02):** d11p −0.20 core (−8.0 %), fps −0.7 % [−1.8, +0.3]; d11t −0.22 core (−8.6 %), fps −1.1 % [−2.1, −0.0], and the only frames over 16.7 ms (six, in run 0221-d11t-r5); TimerQueue busy 23.17 % → ~2 %; the formal W5b read-out is still due (Changed since 23:29, the W5b sub-bullet) |'''),
('S20 order (6)', '''but the re-pin rows (rpb0/rpm4) wait in Agent 3's queue after f10a/f10b (L3169), so native4b isn't pinned yet (Changed since 23:29).''',
 '''and the re-pin rows ran in Agent 3's queue after f10a/f10b and both PASS (rpb0 at 06:17, rpm4 at 06:20; `build/agent3/runs/rpb0-20261123-0617`, `build/agent3/runs/rpm4-20261123-0620`; SESSION2 L3325, L3332), so only Agent 1's announcement is left, and until then the pin stays native4 (`build/agent4/HANDOFF.md`; Changed since 23:29).'''),
('S21 4b entry', '''W9's and W5b's read-outs are pending.''',
 '''W9's and W5b's read-outs are pending.
- **06:17-07:16 (the re-pin rows, f10 n = 2, the W9 read-out and the W5b pool; Changed since 23:29):** Agent 7's formal W9 read-out (07:01): q500, −0.75 core (−30.0 %) with no p99 or 1 % low loss; drop q0; q125 and q250's unsteadiness is host-triggered. Agent 7's pooled W5b table (07:02): d11p −0.20 and d11t −0.22 core, fps −0.7 and −1.1 %; the formal W5b read-out is still due. Agent 8's check of both against results.csv (07:16): 699 of 728 claims agree, no sign flips. Agent 3's second quiet pair (f10a2 and f10b2, 06:32-06:47): no hang, so 0 of 4 quiet runs against 4 of 6 under the -j8 build (p = 0.07); Agent 10 rates all 4 rows PASS, and finding 10 stays a load-only WARN. The re-pin rows rpb0 and rpm4 PASS; Agent 1 announces the pin. Agent 10 rated #21 (06:32: SAFE / SAFE-IF / ACCEPTED, with F-CA). Recorded now: #19 (Nov 22) and #33 (06:28-06:47) are staged, not rated or built, and so is W8a's matrix (Agent 8).'''),
('S22 ratings missing', '''- **Ratings still missing:** #6 (no code yet), #19, #21 (F's "one more code proof" has no source in Agent 10's notes, b2r §25), #25, #33.''',
 '''- **Ratings still missing:** #6 (no code yet), #19 (staged), #25, #33 (staged). #21 was rated at 06:32 on Nov 23 (`build/agent10/t27/r21-s4t1.md`; row 21).'''),
('S23 re-pin answer', '''Agent 4 does it (run-2 task #12, since 19:42; L2730, L2744).''',
 '''Agent 4 does it (run-2 task #12, since 19:42; L2730, L2744). Done except the announcement: the pin record PASS at 22:43 (0 FAIL, 0 WARN), and on Nov 23 the boot check rpb0 and the matrix rpm4 PASS; Agent 1 announces the pin (`build/agent4/HANDOFF.md`).'''),
('S24 possible changes', '''the SCRNSAVE fix's tests (Changed since 23:29). Next, before the break: the W9 and W5b read-outs (Agents 7 and 8) and Agent 3's second quiet pair. After it: s4bV0, s4bLV, the re-pin rows, W7, W8a, W8b and W10 (`perf-notes/RESUME.md`).''',
 '''the SCRNSAVE fix's tests (Changed since 23:29). Since 06:55: Agent 7's W9 read-out and W5b pool with Agent 8's check, the second quiet pair with Agent 10's rating, the re-pin rows, #21's rating, and the staged #19, #33 and W8a (Changed since 23:29). Next, before the break: Agent 7's formal W5b read-out, the SCRNSAVE install and Agent 1's re-pin announcement. After it: s4bV0, s4bLV, W7, W8a, W8b and W10 (`perf-notes/RESUME.md`).'''),
('S25a f5 n=1 claim', '''and more draws took the full-path sync under load (60921 syncs in gate B against 45458 in f10b).''',
 '''and at n = 1 more draws seemed to take the full-path sync under load (60921 syncs in gate B against 45458 in f10b; withdrawn at n = 2, below).'''),
('S25b f5 n=2', '''n = 1 per set; a second quiet pair (n = 2) runs this morning, with its summary due after 07:20 (Agent 1, 06:34), and a controlled-load repeat (~8 busy threads) and an s4b20-style row under load with the slow-frame log are offered, not run.''',
 '''**The second quiet pair (f10a2 06:32-06:40, f10b2 06:40-06:47; RESULTS.md at 06:59) didn't hang either: 0 of 4 quiet runs against 4 of 6 under the -j8 build in the same hour (one-sided Fisher p = 0.07; one more clean pair would give 0.03), which fits load as the trigger but isn't proof.** The quiet worst frames were 1.79, 1.54, 2.89 and 1.79 s, against 7.98-13.14 s under the build. In gate B's stall frames the same GPU work waited 5-30 times longer per round trip than on the quiet host, and the CPU-only part of the frame grew 1.7-2.4 times; GPU clocks weren't logged, and on this laptop a busy CPU could slow the GPU a little, but not 5-30 times. n = 2 withdraws n = 1's "more draws took the full-path sync under load": the quiet totals vary a lot for the same set (f10a 18810 against f10a2 28030; f10b 45458 against f10b2 77236, more than gate B's 60921), because which bursts happen depends on timing. Agent 10 (`build/agent10/t27/f10-rating.md`, 06:55, cross-checked at 07:05): all 4 rows PASS, finding 10 stays a load-only WARN, and s4bLV (p2fc + verify, a precondition for C1 default-ON) hasn't run; not reproducing the hang doesn't fix it, because the mechanism is still there. Offered, not run: a third quiet pair, a controlled-load repeat (~8 busy threads) and an s4b20-style row under load with the slow-frame log.'''),
('S26 sources', '''the committed state's fact sheet `build/agent11/resume/facts-perfopt.md`.''',
 '''the committed state's fact sheet `build/agent11/resume/facts-perfopt.md`.
- **Added at {T}:** Agent 7's formal W9 read-out `build/agent7/readout/W9.md` (07:01; pooled numbers in `build/agent7/readout/pool-W9.md`, the loaded-run table in `build/agent7/readout/load-check.md`), its pooled W5b table `build/agent7/readout/pool-W5b.md` (07:02) and long-frame check `build/agent7/readout/tail-check.md` (06:54); Agent 8's check of both against results.csv, `build/agent8/readout/w-followup/a7check/W9-W5b-check.md` (07:16); Agent 3's n = 2 write-up `build/agent3/f10/RESULTS.md` (06:59; table `build/agent3/f10/f10-table.md`; the second pair's runs `build/agent3/runs/20261123-063244-f10a2-m1-sfl-level` and `build/agent3/runs/20261123-064014-f10b2-p2fc-level`); Agent 10's ratings `build/agent10/t27/f10-rating.md` (f10), `build/agent10/t27/r21-s4t1.md` (#21) and `build/agent10/t27/day-draft-rating.md` (the day launcher); the re-pin rows `build/agent3/runs/rpb0-20261123-0617` and `build/agent3/runs/rpm4-20261123-0620` (`build/agent4/HANDOFF.md`); the staged #19 (`build/agent7/s4-r1s2/README.md`), #21 (`build/agent7/s4-t1/README.md`), #33 (`build/agent6/s33-popin/DESIGN.md`, `build/agent6/s33-popin/CHECK.txt`) and W8a (`build/agent8/w-followup/PROPOSAL.md`); Agent 1's `build/agent1/HANDOFF.md` (07:05); SESSION2 to L3337.'''),
]

L = lambda rel: WS + rel
FNE = [
('F1 title', '''(as of Nov 23, 06:55: the night's windows are done, and the project pauses for a break)''',
 '''(as of Nov 23, {T}: the night's windows are done, and the project pauses for a break)'''),
('F2 alert', '''The W6 and W4c rows below are Agent 8's formal read-outs; the W9 and W5b rows are still Agent 1's runner summaries, until their read-outs land.''',
 '''The W6 and W4c rows below are Agent 8's formal read-outs, and the W9 row is Agent 7's; the W5b row is Agent 7's pooled table until its formal read-out lands.'''),
('F3 W9 row', '''| **500 µs: 0.70-0.79 core less (−28 to −31%)**, fps +1%, and the slowest 1% of frames a bit faster. 125 and 250 µs save a little less and were unsteady in the second pass | 500 µs |''',
 '''| **500 µs: 0.75 core less (−30%), with no loss in the slowest frames.** Without the 7 runs hit by background load, 0.79 core less, and the slowest frames even a bit faster. 125 and 250 µs save a little less; their unsteady runs all fell in two bursts of background load in the second pass. With a zero sleep it saves nothing | 500 µs |'''),
('F4 W5b row', '''| **Precise wait: 0.20 [0.21] core less, fps unchanged in both passes.** The blocking wait saves about the same but lost 0.8% fps in the second pass | precise |''',
 '''| **Precise wait: 0.20 core less (−8%); its fps change (−0.7%) is within the noise.** The blocking wait saves about the same (0.22 core) but costs about 1% fps, and it had the only frames over 16.7 ms (six, all in one run). These are Agent 7's pooled numbers; the formal read-out is still due | precise |'''),
('F5 f10 summary', '''**The stuck game lock (finding 10) on a quiet PC.** Agent 3 ran two level runs on the quiet PC this morning: one with C1 off and one with P2 + fix (i) + C1. Neither hung. Their slowest frames took 1.8 and 2.9 s, against 4.9-12 s, and a hang in all four runs, under last night's 8-job build. That's one run per set, and the margin is modest; a second pair runs this morning.''',
 '''**The stuck game lock (finding 10) on a quiet PC.** Agent 3 ran two pairs of level runs on the quiet PC this morning, each pair with C1 off and with P2 + fix (i) + C1. None of the four hung, against 4 hangs in 6 runs under last night's 8-job build. Their slowest frames took 1.5-2.9 s, against 8-13 s under the build; the detector fires at 5 s. That fits the busy PC as the trigger, but it isn't proof yet (p = 0.07), and the margin is modest. Agent 10 rates all four runs PASS, so finding 10 stays a warning that applies only under load.'''),
('F6 after the break', '''the W9 and W5b read-outs settle the last two leans; then W7 (#19),''',
 '''the formal W5b read-out settles the last lean (W9's confirmed 500 µs); then W7 (#19),'''),
('F7a quiet-PC waits', '''each host-to-GPU round trip took 0.3-1.0 ms on the quiet PC against 1.8-6.1 ms under the build''',
 '''each host-to-GPU round trip took 0.2-1.0 ms on the quiet PC against 1.8-6.1 ms in a run that hung under the build'''),
('F7b quiet-PC bursts', '''still took 2.7-2.9 s,''', '''still took up to 2.9 s,'''),
('F7c quiet-PC n=2', '''One run per set; a second pair runs this morning, and a controlled-load repeat and a loaded s4b20-style row are offered.''',
 '''A second pair didn't hang either: 0 of 4 quiet runs against 4 of 6 under the build (p = 0.07), which fits load as the trigger without proving it. Agent 10 rates all four runs PASS, and finding 10 stays a load-only warning ([rating](''' + L('build/agent10/t27/f10-rating.md') + ''')). A third quiet pair, a controlled-load repeat and a loaded s4b20-style row are offered, not run.'''),
('F8a sources A7', '''/build/agent8/readout/w-followup/W4c.md) (Agent 8), the [quiet-PC rows]''',
 '''/build/agent8/readout/w-followup/W4c.md) (Agent 8), [W9](''' + L('build/agent7/readout/W9.md') + ''') and the [W5b pool](''' + L('build/agent7/readout/pool-W5b.md') + ''') (Agent 7), [Agent 8's check of them](''' + L('build/agent8/readout/w-followup/a7check/W9-W5b-check.md') + '''), the [quiet-PC rows]'''),
('F8b sources A10', '''/build/agent3/f10/RESULTS.md) (Agent 3) and the [screensaver fix]''',
 '''/build/agent3/f10/RESULTS.md) (Agent 3) with [Agent 10's rating](''' + L('build/agent10/t27/f10-rating.md') + '''), and the [screensaver fix]'''),
]

# ---------------- gate ----------------
raw = open(path, 'rb').read()
sha = hashlib.sha256(raw).hexdigest().upper()
if not sha.startswith(pre):
    print('ABORT sha', sha[:16], 'expected', pre); sys.exit(1)
if raw.startswith(b'\xef\xbb\xbf') or b'\r' in raw or raw.count(b'\n') != nlf:
    print('ABORT format: bom', raw.startswith(b'\xef\xbb\xbf'), 'cr', raw.count(b'\r'), 'lf', raw.count(b'\n')); sys.exit(1)
text = raw.decode('utf-8')
print('GATE OK', path, sha[:16], len(raw), 'B', nlf, 'LF')

for p, quotes in SRC.items():
    if not os.path.exists(p):
        fails.append('SRC missing file ' + p); continue
    t = rd(p)
    for q in quotes:
        if q not in t:
            fails.append('SRC not found in %s: %s' % (p, q[:90]))
for p, n, q in LINECHK:
    Ls = lines(p)
    if len(Ls) < n or q not in Ls[n - 1]:
        fails.append('LINE %s L%d lacks %r' % (p, n, q))
if len(lines(S2)) < 3337:
    fails.append('SESSION2 shorter than 3337 lines')
for p, px in SHACHK:
    h = hashlib.sha256(open(p, 'rb').read()).hexdigest().upper()
    if not h.startswith(px):
        fails.append('SHA %s %s != %s' % (p, h[:8], px))

edits = S4E if doc == 'S4' else FNE
new = text
for name, old, rep in edits:
    rep = rep.replace('{TT}', TT).replace('{T}', T)
    c = new.count(old)
    if c != 1:
        fails.append('TARGET %s occurs %d times' % (name, c)); continue
    new = new.replace(old, rep, 1)
    added = rep.replace(old, '') if rep.startswith(old) else rep
    if '\r' in rep:
        fails.append('CR in ' + name)
    for m in re.finditer(r'`((?:build|bench|perf-notes)/[^`\s]+)`', rep):
        if not os.path.exists(m.group(1).rstrip('/')):
            fails.append('PATH %s: %s' % (name, m.group(1)))
    for m in re.finditer(re.escape(WS) + r'([^)\s]+)\)', rep):
        if not os.path.exists(m.group(1)):
            fails.append('LINK %s: %s' % (name, m.group(1)))
    if doc == 'S4':
        if re.search(r'\d%', added):
            fails.append('STYLE S4 %% without space in ' + name)
        if re.search(r'(?<![\w/.\-+])-\d', added):
            fails.append('STYLE S4 ASCII minus in %s: %s' % (name, re.search(r'.{0,20}(?<![\w/.\-+])-\d.{0,10}', added).group(0)))
        if re.search(r'<user>|rishabh|file:///|https?://|[A-Za-z]:\\\\|\\\\Users\\\\', added, re.I):
            fails.append('PERSONAL in ' + name)
    else:
        if re.search(r'\d %', added):
            fails.append('STYLE FN space before %% in ' + name)
        if re.search(r'(?<![\w/.\-+])-\d', added):
            fails.append('STYLE FN ASCII minus in ' + name)
        if re.search(r'rishabh|https?://', added, re.I):
            fails.append('PERSONAL in ' + name)
    print('EDIT %-26s +%d chars' % (name, len(rep) - len(old)))

nb = new.encode('utf-8')
print('NEW', hashlib.sha256(nb).hexdigest().upper()[:16], len(nb), 'B', nb.count(b'\n'), 'LF (was %d)' % nlf)

if mode == '--dry':
    open('build/agent11/s4draft/passb-%s-dry.md' % doc, 'wb').write(nb)
    print('---- PEEK')
    for p, pats, rng in [(S33D, r'#34|dropped|skipp|counter', None), (F10, r'never|2736|C1 off|f10a2', None),
                         (F10R, r'.', (40, 50)), (TC, r'.', (48, 58))]:
        for i, s in enumerate(lines(p), 1):
            if rng and not (rng[0] <= i <= rng[1]):
                continue
            if re.search(pats, s):
                print('%s L%d: %s' % (os.path.basename(p), i, s[:400]))

if fails:
    print('FAIL %d' % len(fails))
    for f in fails:
        print('  ' + f)
    sys.exit(2)

if mode == '--apply':
    if os.path.exists(backup):
        print('ABORT backup exists', backup); sys.exit(1)
    shutil.copyfile(path, backup)
    if hashlib.sha256(open(backup, 'rb').read()).hexdigest().upper() != sha:
        print('ABORT backup mismatch'); sys.exit(1)
    open(path, 'wb').write(nb)
    chk = open(path, 'rb').read()
    print('WROTE', path, hashlib.sha256(chk).hexdigest().upper(), len(chk), 'B', chk.count(b'\n'), 'LF', 'CR', chk.count(b'\r'), 'backup', backup)
else:
    print('DRY OK (no FAIL)')

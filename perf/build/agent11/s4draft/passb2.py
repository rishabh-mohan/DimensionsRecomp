# Agent 11, task #25 pass B v2 (07:35): passb.py's gated edits, revised for Agent 7's formal W5b read-out (07:21)
# and Agent 8's revised check (07:31, now covering W5b.md too). passb.py stays frozen; this file overrides some of
# its edits and sources. Usage: python passb2.py S4|FN --dry|--apply HHMM
import sys, re
src = open('build/agent11/s4draft/passb.py', encoding='utf-8').read()
head, gate = src.split('# ---------------- gate ----------------')
# the backup path doesn't exist until the apply step writes it
gate = gate.replace("if not os.path.exists(m.group(1).rstrip('/')):", "if not os.path.exists(m.group(1).rstrip('/')) and m.group(1) != backup:")
assert 'and m.group(1) != backup' in gate
g = {'__name__': '__main__'}
exec(head, g)
S4E, FNE, SRC, L, fails = g['S4E'], g['FNE'], g['SRC'], g['L'], g['fails']

A8T = '07:34'  # v2.1: Agent 8's check revised again at 07:34 (MISREAD cause for 0221's ng_t)
A8AG = '880 of 912 claims agree'
def tok(s):
    return s.replace('{A8T}', A8T).replace('{A8AG}', A8AG)

def setE(lst, name, rep, old=None):
    for i, (n, o, r) in enumerate(lst):
        if n == name:
            lst[i] = (n, o if old is None else old, tok(rep))
            return
    raise SystemExit('no edit ' + name)

def delE(lst, name):
    n0 = len(lst)
    lst[:] = [e for e in lst if e[0] != name]
    assert len(lst) == n0 - 1, name

W5B = 'build/agent7/readout/W5b.md'
A8C = g['A8C']
SRC[A8C] = ['**912 claims, 3718 numbers: 880 agree (82 only with rounded inputs, 2 with the stated alternative), 32 disagree, 0 parse problems.**',
            'Disagreements by gap (last-digit units): 0.5-0.6: 15; 0.6-1: 6; 1-2: 5; > 2: 6. Sign flips: 0.',
            'it shares no code with either pool_readout.py',
            "- Checked files (Agent 7, read-only): `build/agent7/readout/W9.md` (07:01), `build/agent7/readout/W5b.md` (07:21), `build/agent7/readout/pool-W9.md` (06:26), `build/agent7/readout/pool-W5b.md` (07:02), `build/agent7/readout/load-check.md` (06:40).",
            '| W5b.md L70 | 0221-d11t-r5 window ng_t | 2.31 | 2.558 | DISAGREE | 24.79 |']
SRC[W5B] = ['Agent 7, 2026-11-23 (task #21).',
            '| Which wait mode? | **d11p, narrowly** (over d11t; both save CPU vs d11) |',
            'Both cut ~0.2 core: d11t -0.22 [-0.25, -0.19] (-8.6 % *), d11p -0.20 [-0.23, -0.17] (-8.0 % *).',
            "d11t: B-block fps -1.1 % [-2.1, -0.0] *, raw median ms higher in 11 of 12 rounds, and the window's only stutter cluster (0221-d11t-r5).",
            'd11p: fps -0.7 [-1.8, +0.3], p99 +0.0, 1 % low -0.2, with no consistent per-round cost.',
            "The frames don't separate the arms: fps d11t -0.2 [-1.0, +0.7], d11p -0.7 [-1.5, +0.0]. The pick then rests on the loaded runs themselves (d11t lost -3.0 % fps vs d11p -1.1 % at similar load, n = 4 each) and on 0221, which isn't flagged.",
            "| Runner's numbers (pass 2) | **agree** |",
            "| W5's d11t tail lead | **not reproduced** | p99 +0.3 % [-0.3, +1.0] (W5: +8.2 % [+0.5, +16.6]).",
            'The CPU saving is reproduced, smaller (-8.6 % vs -13.7 %).',
            "| W5b-2's quiet gate | **it worked at the start only** | It held W5b-2 back 3 min for a CrossDeviceService spike (0.68-0.87 core) and then passed. Load came back ~6 min after the holdback, during the first scored run, and hit the first 4 scored runs (ng_t 2.84-3.76). | All 4 are flagged. Without them, no verdict changes. |",
            '- **Primary: B-block T-std.** The round effect on median ms is F = 4.11 on (11, 22), p = 0.002', "The effect is pass 1's round 1 alone", 'So pooling is fine.',
            '| TimerQueue busy % | 23.17 | 1.97; -21.19 [-21.82, -20.56]; -91.5 % * | 2.08; -21.08 [-21.72, -20.45]; -91.1 % * |',
            '- d11t - d11p cores: -0.016 [-0.047, +0.016], n.s.',
            '2. **Quiet runs: all three arms are level.**', '| d11 | 11 | 385.1 |', '| d11t | 8 | 385.2 |', '| d11p | 8 | 385.4 |',
            '- 11 of 12 rounds (sign p 0.006);', 'The typical size is about +0.3 % (median round +0.32 % without round 1).',
            "**d11t's 4 loaded runs lost -3.0 % fps on average** at a mean ng_t of 3.11. **d11p's 4 lost -1.1 %** at a mean ng_t of 3.15.",
            'n = 4 loaded runs per arm, picked after the fact: this is a pattern, not a test.',
            "So the cluster lines up with a 1-2 s host-wide burst (E cores busy, clock down), while the game's own CPU stayed flat, the GPU went partly idle and the frame queue was full. The cause isn't identified.",
            "It is one event in 36 runs. It fell on d11t, but one event can't show that d11t is more prone.",
            '| d11 | 5.390 / 5.429 | 2 | 2 / 1 / 0 |', '| d11t | 5.479 / 6.088 | 3 | 46 / 28 / 6 | 26.37 (0221-d11t-r5) | 0 |', '| d11p | 5.429 / 5.450 | 4 | 6 / 2 / 0 |',
            "- a per-run quiet check: re-check the gate's processes before each run, and wait or flag the run if one is >= 0.1 core;",
            '- log the top CPU processes once a second during each run, so the source of a burst can be named;',
            '- flag any run with window ng_t >= 2.8, or re-run it at the end;',
            '- rotate the round-1 order, or add unscored warm-up runs (the position effect, section 2).',
            '- **Pick d11p (narrowly) over d11t.** Both beat d11 on CPU.',
            '- **d11p vs d11:** -0.20 core (-8.0 % *) for fps -0.7 % [-1.8, +0.3] (median round +0.04 %), p99 +0.0 % and 1 % low -0.2 %. So there is no p99 or 1 % low loss beyond the spread.',
            '- **Optional follow-up**, only if d11t is still a candidate: d11t vs d11p vs d11 under a controlled background load',
            'power overlay best_performance in 38 of 38 runs', 'Compare W5b only within itself.',
            'W5b, W9, W6 and W4c ran after the Defender exclusion for `build/` (~23:16 on Nov 22); W4b and W5 ran before it.',
            '| d11p | 12 | 12 | 12 | 0 | 0 | 0 | 0 | - |', '0221-d11t-r5, the run with the stutter cluster, isn\'t flagged: its window ng_t was 2.31']
SRC[g['F10']] = SRC[g['F10']] + ['- **The M1 set (f10a, f10a2; C1 off) makes no cinematic bursts.**',
                                 'f10a2 (M1 set) also has the 1644-sync frame: #10487 at +60.2 s, 1540.7 ms']
SRC['perf-notes/S4-DRAFT.md'] = ['| 38 | **Precise timer wait** (A11, finding 6) |', '**SAFE** as a default-off candidate (b2r row 15, §14)',
                                 'devoff4 and native4 = S3d + #7, #8, #5 and #38 (all OFF) + #32 (always on)']

# Agent 8's gaps > 2: the 4 light-share F values and one run's ng_t (0221-d11t-r5, cited twice), nothing else.
big = {}
for line in open(A8C, encoding='utf-8').read().split('\n'):
    m = re.search(r'\| DISAGREE \| ([\d.]+) \|', line)
    if m and float(m.group(1)) > 2:
        loc = re.search(r'\| ((?:pool-)?W\w+\.md L\d+) \|', line)
        kind = 'F' if 'light share one-way F' in line else ('ng' if '0221-d11t-r5' in line and 'ng_t' in line else 'other')
        big[loc.group(1) if loc else '?'] = kind
kinds = sorted(big.values())
if kinds != ['F', 'F', 'F', 'F', 'ng', 'ng']:
    fails.append('A8C gaps > 2 are not 4 light-share F + 2 ng_t of 0221: %r' % sorted(big.items()))

# ---------------- S4 overrides ----------------
REPIN = ''' Done except the announcement: the pin record PASS at 22:43 (0 FAIL, 0 WARN), and on Nov 23 the boot check rpb0 and the matrix rpm4 PASS; Agent 1 announces the pin (`build/agent4/HANDOFF.md`).'''
delE(S4E, 'S23 re-pin answer')
S4E.append(('S23a re-pin, Still open', '''Agent 4 does it (run-2 task #12, since 19:42; L2730, L2744).\n- **W5's read-out:**''',
            '''Agent 4 does it (run-2 task #12, since 19:42; L2730, L2744).''' + REPIN + '''\n- **W5's read-out:**'''))
S4E.append(('S23b re-pin, 4b', '''Agent 4 does it (run-2 task #12, since 19:42; L2730, L2744).\n- **Possible changes after this draft:**''',
            '''Agent 4 does it (run-2 task #12, since 19:42; L2730, L2744).''' + REPIN + '''\n- **Possible changes after this draft:**'''))
S4E.insert(0, ('S0 header times', '''and on Nov 23 at 05:55 and 06:55 under task #25, the wrap-up before the break''',
               '''and on Nov 23 at 05:55, 06:55 and {T} under task #25, the wrap-up before the break'''))
setE(S4E, 'S1 intro', '''are in (the 05:55 version is kept in `build/agent11/s4draft/S4-DRAFT.0655-1B0BB0DC.md`). At {T}, Agent 7's formal W9 and W5b read-outs are added under their bullets, with Agent 8's check of their numbers; Agent 3's second quiet pair (f10, n = 2), Agent 10's f10 and #21 ratings and the re-pin rows are in too (the 06:55 version is kept in `build/agent11/s4draft/S4-DRAFT.{TT}-017085DF.md`):''')
setE(S4E, 'S2 W9 sub-bullet', '''**Lean: q500** (L3233-3239, L3277-3287).
    - **Agent 7's formal read-out (07:01, `build/agent7/readout/W9.md`; both passes pooled as 8 rounds, 40 kept runs): q500.** The largest CPU drop, −0.75 core [−0.86, −0.64] (−30.0 %), with no p99 or 1 % low loss in any method; without the 7 flagged runs (host-load flags), −0.79 core [−0.84, −0.73], with p99 (−0.8 %) and the 1 % low (+2.2 %) better than off (T-std; both CIs exclude 0). The runner's pass-2 numbers agree (−0.70 core, −27.9 %; fps +1.1 %; p99 4.675 against 4.985 ms). **Drop q0:** −0.03 core [−0.14, +0.08], and its raw median is higher in 8 of 8 rounds (~0.5-0.8 %); the saving needs Q > 0. **q125 and q250's unsteadiness is host-triggered, not an arm defect:** all 6 slow q runs fell in two bursts of background load in pass 2 (non-game busy cores 2.91-4.06), the same arms ran normally before, between and after them, and without the flagged runs both save 0.72 core against q500's 0.79. Agent 8 checked Agent 7's numbers against results.csv with its own script, which shares no code with Agent 7's (`build/agent8/readout/w-followup/a7check/W9-W5b-check.md`, revised at {A8T}; it covers both read-outs and the tables behind them: W9.md, W5b.md, pool-W9.md, pool-W5b.md and load-check.md): {A8AG}, and none flips sign. Of the other 32, 26 differ by at most 2 in the last digit, 4 are light-share F values (results.csv's rounded light share can't reproduce them exactly), and 2 are one run's background load (0221-d11t-r5's non-game busy cores: 2.31 in the W5b read-out against 2.56 from Agent 8's audit table; below the read-out's 2.8 cut for loaded runs either way).''')
setE(S4E, 'S3 W5b sub-bullet', '''**Lean: d11p** (L3243-3249, L3291-3296).
    - **Agent 7's formal read-out (07:21, `build/agent7/readout/W5b.md`; both passes pooled as 12 rounds, 36 kept runs; primary B-block T-std, since the round effect is significant, p = 0.002, and comes from pass 1's round 1 alone; the passes agree, so pooling is fine): d11p, narrowly over d11t.** Both save the same ~0.2 core, all of it from the TimerQueue thread (busy 23.17 % → 1.97 % in d11t and 2.08 % in d11p): d11p −0.20 core [−0.23, −0.17] (−8.0 %), d11t −0.22 core [−0.25, −0.19] (−8.6 %), a difference that isn't significant. On quiet runs all three arms are level (385.1-385.4 fps). d11p shows no consistent frame cost: fps −0.7 % [−1.8, +0.3] (median round +0.04 %), p99 +0.0 % [−0.6, +0.6], 1 % low −0.2 % [−4.0, +3.7]. d11t: fps −1.1 % [−2.1, −0.0] (the CI just excludes 0), a raw median frame time above d11's in 11 of 12 rounds (typically about +0.3 %), and the window's only stutter cluster (0221-d11t-r5 in pass 1, with all six of the window's frames over 16.7 ms; it lines up with a 1-2 s host-wide burst while the game's own CPU stayed flat; one event in 36 runs, cause not identified; `build/agent7/readout/tail-check.md`, `build/agent7/readout/cluster-0221.txt`). Without the 7 flagged runs (host load), the frames don't separate the two (fps d11t −0.2 % [−1.0, +0.7], d11p −0.7 % [−1.5, +0.0]); the pick then rests on the loaded runs (d11t lost 3.0 % fps against d11p's 1.1 % at similar load, n = 4 each, picked after the fact: a pattern, not a test) and on 0221, hence "narrowly". The runner's pass-2 numbers agree. W5's d11t tail lead is not reproduced (p99 +0.3 % [−0.3, +1.0] against W5's +8.2 % [+0.5, +16.6]); the CPU saving is, but smaller (−8.6 % against −13.7 %). W5b-2's quiet gate worked at the start only: load came back ~6 min after its 3-minute holdback and hit the first 4 scored runs (all flagged; no verdict changes without them). Agent 7 recommends, for later windows, a per-run quiet check, logging the top CPU processes once a second, flagging (or re-running at the end) any run with non-game load ≥ 2.8 cores, and rotating the round-1 order or adding unscored warm-up runs; and, only if d11t is still a candidate, a d11t/d11p/d11 test under a controlled background load. G11: best_performance in 38 of 38 runs, so compare arms within W5b only, not with W5's absolute numbers (W5 also ran before the Defender exclusion). Agent 8's check covers this read-out too (the W9 bullet above).''')
setE(S4E, 'S6 A8 bullet', '''under their bullets above. W9's and W5b's formal read-outs are Agent 7's (07:01 and 07:21, under their bullets above), and Agent 8 checked their numbers against results.csv (revised at {A8T}; see the W9 bullet).''')
setE(S4E, 'S8 leans now', '''keep p2fc (the W6 read-out confirms it), drop B (the W4c read-out confirms it), the back-off at q500 (the W9 read-out confirms it, and drops q0) and the precise timer wait d11p (the W5b read-out picks it, narrowly over d11t: both save ~0.2 core, but d11t costs ~1 % fps, more under load, and had the window's only stutter cluster). All four leans now rest on formal read-outs.''')
setE(S4E, 'S9 updated-at', '''§5 (finding 10: the quiet-host rows); §6 (the formal sources).
- Updated at {T} (the W9 and W5b read-outs, f10 n = 2): the header; this block (the intro, the W9 and W5b sub-bullets, the f10 sentence of the decisions paragraph, the formal-sources bullets and the leans); Still open (the S4c re-pin, W5's item, Agent 5's launcher); Decisions item 2; rows 19, 21, 33 and 34; §2c (the W8a, W9 and W5b rows, and the re-pin in the order paragraph); §4b (a 06:17-07:31 entry, Ratings still missing, the re-pin answer and Possible changes); §5 (finding 10: n = 2); §6 (the new sources).''')
setE(S4E, 'S10 W5 item', '''W4c's and W6's landed at 06:17 and 06:31 (Agent 8), and W9's and W5b's at 07:01 and 07:21 (Agent 7, with Agent 8's check of their numbers, revised at {A8T}), so all four are in (Changed since 23:29).''')
setE(S4E, 'S12 decision 2', '''the formal read-outs confirm all four: p2fc (Agent 8's W6: −10.3 % median, all from C1), dropping B (Agent 8's W4c: no gain), q500 (Agent 7's W9: −0.75 core, −30.0 %, with no p99 or 1 % low loss; drop q0) and d11p (Agent 7's W5b: −0.20 core, −8.0 %, with no consistent frame cost; narrowly over d11t, which saves the same but costs ~1 % fps).''')
setE(S4E, 'S18 W9 row', '''a first sighting, 1 of 135). **Formal read-out (Agent 7, 07:01): q500**, −0.75 core [−0.86, −0.64] (−30.0 %) with no p99 or 1 % low loss; without the 7 flagged runs −0.79 core, with p99 and the 1 % low better than off; drop q0; q125 and q250's slow runs are host-triggered (two load bursts in pass 2); Agent 8's check of the W9 and W5b numbers: {A8AG}, no sign flips (Changed since 23:29, the W9 sub-bullet) |''')
setE(S4E, 'S19 W5b row', '''so W5b and W5 agree in direction and order only. **Formal read-out (Agent 7, 07:21): d11p, narrowly over d11t.** Both save ~0.2 core (d11p −0.20, −8.0 %; d11t −0.22, −8.6 %), all from the TimerQueue thread (busy 23.17 % → ~2 %); d11p has no consistent frame cost (fps −0.7 % [−1.8, +0.3], p99 +0.0 %); d11t costs ~1 % fps (−1.1 % [−2.1, −0.0]), more under load, and had the window's only stutter cluster (run 0221-d11t-r5); without the 7 flagged runs the frames don't separate the two; W5's d11t tail lead is not reproduced (Changed since 23:29, the W5b sub-bullet) |''')
setE(S4E, 'S21 4b entry', '''W9's and W5b's read-outs are pending.
- **06:17-07:31 (the re-pin rows, f10 n = 2, the W9 and W5b read-outs; Changed since 23:29):** Agent 7's formal W9 read-out (07:01): q500, −0.75 core (−30.0 %) with no p99 or 1 % low loss; drop q0; q125 and q250's unsteadiness is host-triggered. Agent 7's formal W5b read-out (07:21): d11p, narrowly over d11t; both save ~0.2 core (−0.20 and −0.22), d11p with no consistent frame cost, d11t with ~1 % fps lost, more under load, and the window's only stutter cluster; without the flagged runs the frames don't separate the two, and W5's d11t tail lead is not reproduced. Agent 8's check of both read-outs and their tables against results.csv (revised at {A8T}): {A8AG}, no sign flips. Agent 3's second quiet pair (f10a2 and f10b2, 06:32-06:47): no hang, so 0 of 4 quiet runs against 4 of 6 under the -j8 build (p = 0.07); Agent 10 rates all 4 rows PASS, and finding 10 stays a load-only WARN. The re-pin rows rpb0 and rpm4 PASS; Agent 1 announces the pin. Agent 10 rated #21 (06:32: SAFE / SAFE-IF / ACCEPTED, with F-CA). Recorded now: #19 (Nov 22) and #33 (06:28-06:47) are staged, not rated or built, and so is W8a's matrix (Agent 8).''')
setE(S4E, 'S24 possible changes', '''the SCRNSAVE fix's tests (Changed since 23:29). Since 06:55: Agent 7's W9 and W5b read-outs with Agent 8's check, the second quiet pair with Agent 10's rating, the re-pin rows, #21's rating, and the staged #19, #33 and W8a (Changed since 23:29). Next, before the break: the SCRNSAVE install and Agent 1's re-pin announcement. After it: s4bV0, s4bLV, W7, W8a, W8b and W10 (`perf-notes/RESUME.md`).''')
S4E.append(('S25c f5 C1-off bursts', '''while f10a's set (M1, C1 off) never makes those bursts.''',
            '''while f10a's set (M1, C1 off) makes none of those cinematic 2736-sync bursts, in either of its runs at n = 2 (f10a2 had the smaller 1644-sync burst in the level, 1.54 s; below).'''))
setE(S4E, 'S26 sources', '''the committed state's fact sheet `build/agent11/resume/facts-perfopt.md`.
- **Added at {T}:** Agent 7's formal read-outs `build/agent7/readout/W9.md` (07:01; pooled numbers in `build/agent7/readout/pool-W9.md`) and `build/agent7/readout/W5b.md` (07:21; pooled numbers in `build/agent7/readout/pool-W5b.md`), with the loaded-run table `build/agent7/readout/load-check.md`, the long-frame check `build/agent7/readout/tail-check.md` and the look at the 0221 cluster `build/agent7/readout/cluster-0221.txt`; Agent 8's check of their numbers against results.csv, `build/agent8/readout/w-followup/a7check/W9-W5b-check.md` (revised at {A8T}); Agent 3's n = 2 write-up `build/agent3/f10/RESULTS.md` (06:59; table `build/agent3/f10/f10-table.md`; the second pair's runs `build/agent3/runs/20261123-063244-f10a2-m1-sfl-level` and `build/agent3/runs/20261123-064014-f10b2-p2fc-level`); Agent 10's ratings `build/agent10/t27/f10-rating.md` (f10), `build/agent10/t27/r21-s4t1.md` (#21) and `build/agent10/t27/day-draft-rating.md` (the day launcher); the re-pin rows `build/agent3/runs/rpb0-20261123-0617` and `build/agent3/runs/rpm4-20261123-0620` (`build/agent4/HANDOFF.md`); the staged #19 (`build/agent7/s4-r1s2/README.md`), #21 (`build/agent7/s4-t1/README.md`), #33 (`build/agent6/s33-popin/DESIGN.md`, `build/agent6/s33-popin/CHECK.txt`) and W8a (`build/agent8/w-followup/PROPOSAL.md`); Agent 1's `build/agent1/HANDOFF.md` (07:05); SESSION2 to L3337.''')

# ---------------- FN overrides ----------------
setE(FNE, 'F2 alert', '''The W6 and W4c rows below are Agent 8's formal read-outs, and the W9 and W5b rows are Agent 7's.''')
setE(FNE, 'F4 W5b row', '''| **Precise wait: 0.20 core less (−8%), with no consistent cost in frame rate or the slowest frames.** The blocking wait saves about the same (0.22 core) but costs about 1% fps, more under background load, and it had the only stutter (six frames over 16.7 ms, all in one run). The pick is narrow: without the runs hit by background load, the frames alone don't separate the two | precise |''')
setE(FNE, 'F6 after the break', '''W7 (#19),''')
FNE.append(('F7d quiet-PC C1-off bursts', '''the set with C1 off never makes those bursts.''',
            '''the set with C1 off made none of those bursts in either of its runs (its biggest, 1644 syncs in one frame, took 1.5 s).'''))
setE(FNE, 'F8a sources A7', '''/build/agent8/readout/w-followup/W4c.md) (Agent 8), [W9](''' + L('build/agent7/readout/W9.md') + ''') and [W5b](''' + L(W5B) + ''') (Agent 7), [Agent 8's check of their numbers](''' + L(A8C) + '''), the [quiet-PC rows]''')
FNE.append(('F9 finding 6 for S4', '''- **For S4:** Agent 11 staged a cleaner fix (`timer_queue_precise_wait`, OFF by default, not built): 1.9% CPU and 5.4% stale in the bench. Agent 10's rating is pending.''',
            '''- **For S4:** Agent 11 staged a cleaner fix (`timer_queue_precise_wait`, OFF by default): 1.9% CPU and 5.4% stale in the bench. Agent 10 rated it safe as a default-off candidate, and it is in S4a, off by default. In W5b (Nov 23) it saved 0.20 core (−8%) with no consistent cost in frame rate or the slowest frames; Agent 7's read-out picks it, narrowly, over the blocking wait, which saves about the same but costs about 1% fps.'''))

# ---------------- v2.1 (07:41): Agent 8's 07:34 revision, the launcher's end, the SCRNSAVE install, #33's rating,
# Agent 7's W6/W4c headline recompute, Agent 1's "all four final" message (~07:38) ----------------
def modE(lst, name, old_sub, new_sub):
    old_sub, new_sub = tok(old_sub), tok(new_sub)
    for i, (n, o, r) in enumerate(lst):
        if n == name:
            assert r.count(old_sub) == 1, (name, old_sub[:60])
            lst[i] = (n, o, r.replace(old_sub, new_sub))
            return
    raise SystemExit('no edit ' + name)

INST = 'build/agent5/scrnsave-fix/install-log.txt'
R33 = 'build/agent10/t27/r33-popin.md'
HL = 'build/agent7/readout/headlines-W6-W4c.md'
A7H = 'build/agent7/HANDOFF.md'
SRC[A8C] = SRC[A8C] + ['misread source column: 2 (W5b.md L70, W5b.md L215)',
                       'MISREAD: 2.31 is the "game" (game cores) column of audit.md L257; that row\'s "ng_t mean" is 2.56',
                       'Still below 2.8 and unflagged, so the point stands']
SRC[INST] = ["done: 3 file(s) copied, all three files have the 'after' hashes",
             'installed bench\\agent5\\launch\\run-night.ps1: 565D30D4', 'installed bench\\agent5\\launch\\README.md: B7CEBD63',
             'installed bench\\agent8\\run\\run-matrix.ps1: 1A522CDF', 'run-day.ps1 = the staged B67EBD6C']
if not re.search(r'(?m)^2026-11-23 07:33:57\s+done: 3 file\(s\) copied', g['rd'](INST)):
    fails.append('INST: no 07:33:57 done line')
SRC[R33] = ['Read-only work on 2026-11-23, 07:24-07:36', '- **OFF (the default): SAFE.**',
            '- **ON (cvar true), as an opt-in test: SAFE-IF**, under these conditions:',
            '1. The default stays false, with `kRequiresRestart`',
            '2. Row 1 (cvar off, patched bin against the base bin) shows identity before anyone reads ON timings',
            "3. The user's row-3 review on a visible desktop gates any recommendation",
            '4. The first test bin leaves out hunk #5 (S1 below).', '- No BLOCKER. 2 SHOULD and 4 NIT.',
            '**S1 SHOULD: build the first test bin without hunk #5**',
            '**S2 SHOULD: run the resolve-after-drop diagnostic (d) before any recommendation**',
            '2. Each dropped draw adds one counter']
SRC[HL] = ['**116 claims, 2 disagree.**']
SRC[A7H] = ['116 claims, 114 agree, 2 differ by rounding only', "final after the checker's fixes"]
g['LINECHK'] = list(g['LINECHK']) + [
    (g['S2'], 3339, 'Launcher pid 19960 ended 07:30:14 at its deadline (exit 0): screensaver restored'),
    (g['S2'], 3339, 'Hold manager (task-135) ended 07:30:04 with a clean HOLD log for all 7 windows'),
    (g['S2'], 3341, 'Told Agent 5 it may install the SCRNSAVE fix (#26) once Agent 8 has read the delta.')]
g['SHACHK'] = list(g['SHACHK']) + [('bench/agent5/launch/run-night.ps1', '565D30D4'), ('bench/agent5/launch/README.md', 'B7CEBD63'),
                                   ('bench/agent8/run/run-matrix.ps1', '1A522CDF'), ('build/agent5/day-draft/run-day.ps1', 'B67EBD6C'),
                                   (R33, 'ED632154')]

modE(S4E, 'S2 W9 sub-bullet',
     "and 2 are one run's background load (0221-d11t-r5's non-game busy cores: 2.31 in the W5b read-out against 2.56 from Agent 8's audit table; below the read-out's 2.8 cut for loaded runs either way).",
     "and 2 give one run's background load from the wrong column (0221-d11t-r5: the W5b read-out's 2.31 is the audit table's game-cores figure, and the run's non-game busy cores were 2.56; still below the read-out's 2.8 cut for loaded runs, so its point stands).")
modE(S4E, 'S6 A8 bullet', '(revised at {A8T}; see the W9 bullet).',
     "(revised at {A8T}; see the W9 bullet). The other way round, Agent 7 recomputed Agent 8's W6 and W4c headline numbers from results.csv: 116 claims, 114 agree, and the other 2 differ by rounding only (`build/agent7/readout/headlines-W6-W4c.md`). Agent 1 calls all four read-outs final (~07:38).")
modE(S4E, 'S8 leans now', 'All four leans now rest on formal read-outs.',
     'All four leans now rest on formal read-outs. Open points (Agent 1, ~07:38): there is no C1-only arm, verify is off, and the three winners (p2fc, q500, d11p) were never timed together.')
setE(S4E, 'S9 updated-at', '''§5 (finding 10: the quiet-host rows); §6 (the formal sources).
- Updated at {T} (the W9 and W5b read-outs, f10 n = 2, the SCRNSAVE install, #33's rating): the header; this block (the intro, the W9 and W5b sub-bullets, the SCRNSAVE sub-bullet, the f10 sentence of the decisions paragraph, the formal-sources bullets, the leans and the wrap-up bullet's SCRNSAVE sentence); Still open (the S4c re-pin, W5's item, Agent 5's launcher); Decisions item 2; rows 19, 21, 33 and 34; §2c (the W8a, W9 and W5b rows, and the re-pin in the order paragraph); §4b (a 06:17-07:38 entry, Ratings still missing, the re-pin answer and Possible changes); §5 (finding 10: n = 2); §6 (the new sources).''')
modE(S4E, 'S11 launcher item', 'the install and my rating wait until after the break (SESSION2 L3317-3318, L3326).',
     "the day launcher's install and my rating wait until after the break (SESSION2 L3317-3318, L3326). The night launcher ended at its 07:30 deadline (07:30:14, exit 0, screensaver restored; the hold manager at 07:30:04 with a clean HOLD log for all 7 windows; L3339), and on Agent 1's go (L3341) Agent 5 installed the SCRNSAVE fix at 07:33:57: run-night.ps1 565D30D4…, its README B7CEBD63… and run-matrix.ps1 1A522CDF… all have the 'after' hashes, and `day-update.ps1` re-made the day draft from the new run-night.ps1 (run-day.ps1 B67EBD6C…; `build/agent5/scrnsave-fix/install-log.txt`).")
setE(S4E, 'S15b row 33 status', '''opt-in and off by default (23:24) | staged in `build/agent6/s33-popin/` (06:28-06:47: an SDK patch, 4 files, +105/−24; `git apply --check` passes on 5350b1d; nothing applied or built); **rated by A10 (07:24-07:36, `build/agent10/t27/r33-popin.md`): OFF SAFE; ON as an opt-in test SAFE-IF**, 4 conditions: the default stays false with kRequiresRestart; row 1 (cvar off against the base bin) shows identity before any ON timing is read; the user's row-3 review on a visible desktop gates any recommendation; the first test bin leaves out hunk #5. No BLOCKER; 2 SHOULD (S1: that first bin without hunk #5; S2: the resolve-after-drop diagnostic (d) before any recommendation) and 4 NIT |''')
setE(S4E, 'S16 row 34 status', '''| counts the draws #33 skips | with #33 | #33 | in #33's staged patch (`build/agent6/s33-popin/DESIGN.md`) and rated with it (`build/agent10/t27/r33-popin.md`) |''')
setE(S4E, 'S21 4b entry', '''W9's and W5b's read-outs are pending.
- **06:17-07:38 (the re-pin rows, f10 n = 2, the W9 and W5b read-outs, the launcher's end, the SCRNSAVE install and #33's rating; Changed since 23:29):** Agent 7's formal W9 read-out (07:01): q500, −0.75 core (−30.0 %) with no p99 or 1 % low loss; drop q0; q125 and q250's unsteadiness is host-triggered. Agent 7's formal W5b read-out (07:21): d11p, narrowly over d11t; both save ~0.2 core (−0.20 and −0.22), d11p with no consistent frame cost, d11t with ~1 % fps lost, more under load, and the window's only stutter cluster; without the flagged runs the frames don't separate the two, and W5's d11t tail lead is not reproduced. Agent 8's check of both read-outs and their tables against results.csv (revised at {A8T}): {A8AG}, no sign flips; Agent 7's recompute of Agent 8's W6 and W4c headlines: 114 of 116 agree, the other 2 by rounding only. Agent 1 (~07:38): all four read-outs are final; open points: no C1-only arm, verify off, and the three winners never timed together. Agent 3's second quiet pair (f10a2 and f10b2, 06:32-06:47): no hang, so 0 of 4 quiet runs against 4 of 6 under the -j8 build (p = 0.07); Agent 10 rates all 4 rows PASS, and finding 10 stays a load-only WARN. The re-pin rows rpb0 and rpm4 PASS; Agent 1 announces the pin. Agent 10 rated #21 (06:32: SAFE / SAFE-IF / ACCEPTED, with F-CA) and #33 (07:36: OFF SAFE; ON as an opt-in test SAFE-IF, 4 conditions; 2 SHOULD). The night launcher ended at its 07:30 deadline and the hold manager with a clean HOLD log (L3339); Agent 5 installed the SCRNSAVE fix at 07:33:57. Recorded now: #19 (Nov 22) is staged, not rated or built; #33 (06:28-06:47) is staged and rated, not built; W8a's matrix is staged (Agent 8).''')
setE(S4E, 'S22 ratings missing', '''- **Ratings still missing:** #6 (no code yet), #19 (staged), #25. #21 was rated at 06:32 on Nov 23 (`build/agent10/t27/r21-s4t1.md`; row 21) and #33 at 07:36 (`build/agent10/t27/r33-popin.md`; row 33).''')
setE(S4E, 'S24 possible changes', '''the SCRNSAVE fix's tests (Changed since 23:29). Since 06:55: Agent 7's W9 and W5b read-outs with Agent 8's check (and Agent 7's recompute of the W6 and W4c headlines), the second quiet pair with Agent 10's rating, the re-pin rows, #21's and #33's ratings, the staged #19, #33 and W8a, the night launcher's clean end and the SCRNSAVE install (Changed since 23:29). Next, before the break: the post-install tests and Agent 1's re-pin announcement. After it: s4bV0, s4bLV, W7, W8a, W8b and W10 (`perf-notes/RESUME.md`).''')
modE(S4E, 'S26 sources', "Agent 1's `build/agent1/HANDOFF.md` (07:05); SESSION2 to L3337.",
     "Agent 1's `build/agent1/HANDOFF.md` (07:05); Agent 7's recompute of Agent 8's W6 and W4c headlines `build/agent7/readout/headlines-W6-W4c.md` and its `build/agent7/HANDOFF.md` (07:31); Agent 10's #33 rating `build/agent10/t27/r33-popin.md` (07:36); Agent 5's `build/agent5/scrnsave-fix/install-log.txt` (the install at 07:33:57); SESSION2 to L3341.")
S4E.append(('S27 SCRNSAVE sub-bullet',
            "  - **Agent 5's SCRNSAVE fix** (`build/agent5/scrnsave-fix/README.md`): staged, 45/45 tests PASS at 06:14:40, rated SAFE by Agent 10 (next bullet).",
            "  - **Agent 5's SCRNSAVE fix** (`build/agent5/scrnsave-fix/README.md`): staged, 45/45 tests PASS at 06:14:40, rated SAFE by Agent 10 (`build/agent10/t27/scrnsave-delta.md`); installed at 07:33:57, after the night launcher ended at 07:30:14 (all three files have the 'after' hashes; `build/agent5/scrnsave-fix/install-log.txt`)."))
S4E.append(('S28 wrap-up SCRNSAVE',
            "It is installed after the launcher exits at 07:30, once Agent 8 (run-matrix.ps1's owner) has read the delta too, and before RUN-DAY or another night (L3220-3221, L3304, L3312).",
            "It was installed at 07:33:57, after the launcher had exited at 07:30:14 with the screensaver restored (L3339; Agent 1's go, conditional on Agent 8's read of the delta as run-matrix.ps1's owner: L3341), and before RUN-DAY or another night (L3220-3221, L3304, L3312): all three files have the 'after' hashes, and `day-update.ps1` re-made the day draft from the new run-night.ps1 (run-day.ps1 B67EBD6C…; `build/agent5/scrnsave-fix/install-log.txt`)."))

setE(FNE, 'F2 alert', '''The W6 and W4c rows below are Agent 8's formal read-outs, and the W9 and W5b rows are Agent 7's. All four are final, and each agent re-checked the other's numbers against the raw results: they agree apart from rounding and a few small slips, none of which changes a verdict.''')
modE(FNE, 'F8a sources A7', "[Agent 8's check of their numbers](" + L(A8C) + ")",
     "[Agent 8's check of their numbers](" + L(A8C) + ") and [Agent 7's check of Agent 8's](" + L(HL) + ")")
FNE.append(('F10 SCRNSAVE installed',
            "Agent 5 has staged the proper fix; all 45 of its tests pass, and Agent 10 rated it safe. It goes in after the launcher exits at 07:30, once Agent 8 has read it, and before the launcher is used again.",
            "Agent 5 staged the proper fix; all 45 of its tests passed, and Agent 10 rated it safe. The launcher stopped on time at 07:30 and put the screensaver settings back, and Agent 5 installed the fix at 07:33, before the launcher is used again."))
FNE.append(('F11 popin rated',
            "They still need Agent 6's implementation, Agent 10's rating, a build, and your look at the pop-in on a visible desktop.",
            "Agent 6 has written the change (not built yet), and Agent 10 rated it: safe while off, and safe to test when switched on under four conditions, one of which is your look at the pop-in on a visible desktop before anyone recommends it. It still needs a build and that look."))
FNE.append(('F12 confirmation window', "a confirmation window,", "a confirmation window (the three winning changes have never been timed together),"))

for lst in (S4E, FNE):
    for n, o, r in lst:
        assert '{A8' not in r, n
exec(gate, g)

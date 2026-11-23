# W5 read-out: build/agent8/matrix/20261122-1756 (Agent 8, run-2 task #7)

W5 = Window 5, the S3d line, run 17:56-18:29 on the user's desktop with the agents held. It had 16 runs: 1 cold base run
(unscored) and 3 rounds of the 5 arms, rotated each round.

| arm | bin | cvars and env | TimerQueue wait |
|---|---|---|---|
| base (ref) | devoff3 = S3d (W4b's d3 bin) | none | spin |
| s0 | devoff4 = S4a, every new switch off | none | spin |
| d11 | devoff4 | the 8 timer cvars | spin |
| d11t | devoff4 | the 8 timer cvars + REX_TIMER_WAIT_BLOCKING=1 | blocking |
| d11p | devoff4 | the 8 timer cvars + timer_queue_precise_wait=true | precise |

## Summary

- **Strict pass: FAIL, no verdict for any arm.** R3 drops all 15 scored runs, because the slow state is inside every window with the game in the foreground. R6 also drops 1821-d11t-r3.
- **Frame time: no arm differs from base or from s0.**
  - Every with-flagged row reads `overlap` at n = 3.
  - No 95 % CI on median ms or fps excludes 0, with the raw values or with T-std (Agent 7's final method).
  - T-std puts all four S4a arms 1-2.5 % slower than base. None of these deltas is significant.
- **One lead, not a verdict: d11t's tail.**
  - T-std p99 is +8.8 % vs base [+1.0, +17.2], the only one of the 16 T-std tests vs base (4 arms x 4 metrics) whose CI excludes 0.
  - B-block T-std, the better model for the tail metrics (their round terms are 3-7 %), gives p99 [+2.1, +15.9]\* and 1 % low −8.1 % [−14.2, −1.6]\*.
  - Against d11 (same bin and cvars; only the wait differs), p99 is +8.2 %, and both models' CIs exclude 0.
  - Without 1821-d11t-r3, the deepest-slow-state run, the deltas halve (p99 +4.6 %, 1 % low −3.6 % vs base) and no CI excludes 0.
  - d11 is about 0 on p99, so the lead points at the new wait modes, REX_TIMER_WAIT_BLOCKING=1 most. d11p points the same way, by less, and its CIs include 0.
- **Game CPU is the one measurable difference:**
  - d11t −13.7 % vs base, **better**;
  - d11p −12.2 %, **better**;
  - the saving is the TimerQueue spin that blocking and precise waits remove.
- **Proof and health.**
  - R7 proof is OK in all 15 scored runs.
  - game.log is clean in 16/16 runs (my scanner and Agent 6's logdiff).
- **Host state.** The 3 slow runs (1808, 1817, 1821) are the deep end of the slow state:
  - P util 91-98.5 % and E-cores at 550-597 MHz;
  - their work-based non-game CPU is not elevated.

## What ran and how it was tested

- **Read-out command.** 19:36:42-19:37:29:
  `powershell -NoProfile -ExecutionPolicy Bypass -File build\agent8\scratch\w5-readout.ps1 -Stamp 20261122-1756 -OutDir build\agent8\readout\w5`.
  - It follows the procedure in [agent8-window3.md](../../../../perf-notes/agent8-window3.md), section "W5 read-out procedure" (L920-1058).
  - 8 steps, all exit 0: recheck, recheck-drop, add-on (w5.md), add-on `--ref s0` (w5-s0.md), timerq3, phase, rules, rules-nodrop.
- **Tools.**
  - `bench/agent8/run/matrix_recheck.py`: a W5 input, run unchanged and without `--write`, so nothing was written into the W5 folder.
  - Agent 7's `bench/agent7/w4b_readout/w4b_readout.py`: sha256 `EF1ABEC8…6175C7C4`, 13:31:11, 54,424 B.
    - This is **not** the 7C7A0673… hash that my notes call frozen. Agent 7 added the 10 s bins in task #9 and says the other numbers are unchanged.
    - The add-on's own check agrees with frames.json and results.csv on 16 of 16 runs, and with summary.md's arm fps to 0.001.
  - Agent 11's `bench/agent11/timerq_slowstate_3mode.ps1`: sha256 `E9049B33…4CA59E`, 19:34:20. This is the hash Agent 11 sent, and it includes its 19:34 table fix.
  - Mine: `build/agent8/scratch/phase_switch.py` and `w5_rules.py`.
- **W5 inputs.** At 19:44, after the read-out, I re-hashed the 27 files in `build/agent1/w5/W5-INPUTS-1642.txt`: 0 mismatches.
- **Test 1: dry run on W4b** (19:33, `build/agent8/readout/w5-dry-1541/`). Every step exits 0, and the R7, timerq3 and R5 results are as the procedure expects.
- **Test 2: made-up R7 proof cases** (19:43; [TEST2.md](../../scratch/r7test/TEST2.md), script [r7_cases.py](../../scratch/r7test/r7_cases.py)): **TEST2 PASS**.
  - The cases are copies of W5's small per-run files.
  - A copy with no edits reproduces rules-nodrop.md's R0-R7 sections exactly.
  - These breaks each FAIL R7 with the right reason:
    - REX_TIMER_WAIT_BLOCKING in a d11p env_set;
    - 0 precise lines in a d11p log;
    - 2 precise lines in a d11p log;
    - no 1 ms line in a d11 log;
    - a spin run at 5 % TimerQueue;
    - the env var leaked into base.
  - Every R5 row with a failing arm reads `no verdict (proof)`. A failing reference reads `reference (proof FAIL!)`.
- **Agent 7's final noise method (T-std),** rerun at 20:27 into [noise/](noise/) with his scripts, read-only on the matrix:
  - `build/agent7/w4b-noise/noise_methods.py`, sha256 `A29AF479…F320B4AF` (19:53:34);
  - `noise_case.py`, sha256 `1F3C467E…3B23D152`.
  - The outputs (report-w5.md, 384 lines; noise-case-w5.md, 89 lines) are identical to Agent 7's. The only differing line is the command or path line in each file.
- **Subagents (read-only, run by me):**
  - **Scanner:** game.log health, 10 s bins with E/P values per bin, slow-state stretches. See [scan/scan.md](scan/scan.md).
  - **sys.csv auditor:** see [sysaudit/audit.md](sysaudit/audit.md), with report.md, extra.md and the CSVs.
  - **Cross-checker:** recomputed 1,017 numbers from the run files: 0 MISMATCH, 16 definition differences, 4 rounding ties. See [xcheck/xcheck.md](xcheck/xcheck.md).
  - **T-std and B-block recompute** ([tstd.md](../tstd-xcheck/tstd.md), cross-checker, 20:45): its own numpy code recomputes every per-run T-std value, both models and every CI from the run files. W5: 845 of 845 numbers match Agent 7's report-w5.json and 151 of 151 match his RESULTS.md, 0 MISMATCH. It also ran the sensitivity checks under "d11t's tail".
- **Agent 11's 3-mode check:** PASS (`build/agent11/s4a/slowstate3-check/REPORT.md`). None of its 7 edge cases occurs in W5.
- **Variants:** [variants.md](variants.md), from `build/agent8/scratch/readout_variants.py`. It covers all runs, the runs without 1821, and the slow-state bins.
- **Agent 6's logdiff:** `build/agent6/w4b/out-20261122-1756-vs-s0/` and `out-20261122-1756-vs-base/`.

## Verdicts

**Strict pass ([rules.md](rules.md)): overall FAIL, no verdict for any arm.**

- R3 drops all 15 scored runs: the slow state is in the window, with the game in the foreground (see below).
- R6 also drops 1821-d11t-r3: BG+, 8.17 background cores against the 7.16 reference.
  - This marks the deep slow state, not extra work: 1821's work-based non-game CPU is 3.39, inside the other runs' range (see Host state).
- Everything else passes:
  - R0: 16 rows, 3 scored runs per arm;
  - R1;
  - R2: fg = 1 in 15 of 15 runs;
  - R4: draws/frame p50 226 in every run, scene distance 0.000;
  - R7: proof OK in every run.

**With the flagged runs ([rules-nodrop.md](rules-nodrop.md)).** This pass ignores the R3/R4/R6 drops; the R7, n and scene rules still apply. Every row reads `overlap`, which means no measurable difference at n = 3.

| arm | n | fps median (min..max) | p50 ms | p99 ms | 1% low fps | vs base: fps / p50 / p99 / 1% low | paired fps by round (up / rounds) | decision |
|---|---|---|---|---|---|---|---|---|
| base | 3 | 355.6 (289.2..384.6) | 2.546 | 7.49 | 118.1 | ref | - | reference |
| s0 | 3 | 333.4 (309.9..360.0) | 2.687 | 7.58 | 118.4 | -6.2 / +5.5 / +1.1 / +0.2 % | +1.2 % (2 / 3) | fps -6.2 % overlap |
| d11 | 3 | 351.3 (350.3..352.5) | 2.612 | 7.45 | 120.1 | -1.2 / +2.6 / -0.5 / +1.7 % | -0.9 % (1 / 3) | fps -1.2 % overlap |
| d11t | 3 | 338.5 (277.1..358.7) | 2.647 | 7.84 | 113.1 | -4.8 / +4.0 / +4.6 / -4.3 % | -12.0 % (1 / 3) | fps -4.8 % overlap |
| d11p | 3 | 343.3 (335.3..356.9) | 2.624 | 7.72 | 114.8 | -3.4 / +3.1 / +3.1 / -2.8 % | -5.7 % (1 / 3) | fps -3.4 % overlap |

| pair (second arm = reference) | fps / p50 | paired fps (up / rounds) | decision |
|---|---|---|---|
| d11 vs s0 (the 8 timer cvars) | +5.4 / -2.8 % | +5.1 % (2 / 3) | overlap |
| d11t vs s0 | +1.5 / -1.5 % | +1.5 % (2 / 3) | overlap |
| d11p vs s0 | +3.0 / -2.3 % | +3.0 % (2 / 3) | overlap |
| d11t vs d11 (blocking wait alone) | -3.7 / +1.3 % | -3.4 % (1 / 3) | overlap |
| d11p vs d11 (precise wait alone) | -2.3 / +0.5 % | -2.0 % (1 / 3) | overlap |
| d11p vs d11t (precise vs blocking) | +1.4 / -0.9 % | +1.4 % (2 / 3) | overlap |

- **Without the flagged runs:** R3 leaves no runs.
  - Applying only R6's drop (R3 ignored) leaves d11t with n = 2: 348.6 fps (338.5..358.7), −2.0 % vs base; p50 2.597 ms, +2.0 %. That is no verdict at n 2 vs 3. Every other row is as above ([variants.md](variants.md)).
- **Game CPU is the one measurable difference** (rule R5, [variants.md](variants.md)):

  | arm | cores, median (min..max) | vs base | decision |
  |---|---|---|---|
  | d11t | 2.72 (2.67..2.84) | −13.7 % | **better** |
  | d11p | 2.77 (2.69..2.78) | −12.2 % | **better** |
  | s0 | | +1.3 % | overlap |
  | d11 | | +0.9 % | overlap |

  - Without 1821, d11t has n = 2 (−14.5 %): no verdict.
  - See "Game CPU" below.
- NOTE: base's round-1 run is 1757, right after the cold run. Its 384.6 fps is more than 1 % outside its rounds 2+ (289.2..355.6).
- Timing claims come only from the rows above. None of them shows a frame-time difference.

### Agent 7's final noise method: T-std (primary)

Agent 7's recommendation (`build/agent7/w4b-noise/RESULTS.md` L140-151) is T-std:
- Split each run's frames at the runner's 4.5 ms light threshold.
- Re-mix light and heavy frames at one fixed heavy-time share, hT_ref = 0.213 (the median of the kept runs).
- Compute fps, p50, p99 and 1 % low over the reweighted frames.
- Give per-arm GM deltas vs base with the pooled 95 % CI, df = runs − arms = 10.

B-block T-std (arm + round) is only needed when the round terms are large. W5's round terms are +0.8 / −0.2 % on median ms (fps −0.7 / −0.5 %), so **T-std stands for median ms and fps**. The numbers come from my rerun ([noise/report-w5.md](noise/report-w5.md)) and are identical to Agent 7's.

The tail metrics are different ([tstd.md](../tstd-xcheck/tstd.md)). Their round terms (r2, r3 vs r1) are +3.1 / +5.7 % on p99 and −3.1 / −7.3 % on 1 % low. So for p99 and 1 % low B-block is the better model, and its CIs are narrower, not wider: the 4 vs 4 band (the CI half-width of a 4 vs 4 comparison) is 5.6 against 6.7 % on p99 and 6.1 against 8.2 % on 1 % low.

| vs base | median ms | fps | p99 ms (noisier) | 1 % low fps (noisier) |
|---|---|---|---|---|
| s0 | +1.1 [−2.7, +5.0] | −1.4 [−4.6, +2.0] | +2.8 [−4.6, +10.8] | −2.5 [−11.0, +6.8] |
| d11 | +1.2 [−2.5, +5.2] | −0.8 [−4.0, +2.6] | +0.5 [−6.7, +8.3] | −0.4 [−9.1, +9.1] |
| d11t | +2.4 [−1.4, +6.4] | −2.6 [−5.7, +0.7] | **+8.8 [+1.0, +17.2] \*** | −8.1 [−16.1, +0.7] |
| d11p | +1.5 [−2.3, +5.4] | −1.6 [−4.8, +1.7] | +5.3 [−2.2, +13.5] | −6.3 [−14.4, +2.7] |

`*` = the CI excludes 0.

- **Band** (base's 3 runs, (max − min) / median):
  - median ms: raw 20.4 %, T-std 6.5 %;
  - fps: raw 26.8 %, T-std 5.8 %.
- **Pooled within-arm CV:**
  - median ms: 6.5 % raw, 2.1 % T-std;
  - fps: 9.7 % raw, 1.8 % T-std.
- **Median deltas in the summary.md form:** all `within` the T-std band: +2.3 / +2.5 / +2.7 / +2.1 % on median ms.
- **Guards** (RESULTS.md L144-147):
  - (a) **Light share per arm:** one-way F = 0.33 on (4, 10). No arm moves the light/heavy mix, so T-std does not hide an arm effect.
  - (b) **Raw GM deltas with the pooled CI** (the next table): every T-std delta lies inside its raw CI, so there is no contradiction.
  - (c) **Host-state flag** (P util ≥ 90 % and E < 600 MHz): it catches exactly 1808-s0-r2, 1817-base-r2 and 1821-d11t-r3.
    - For these 3 runs, T-std leaves 25 % of raw's median-ms excess: +3.4 % mean, against an RMS of 2.1 % for the other 12 runs.
    - Their light frames are slow too: +0.9 / +6.0 / +3.3 %.
- **Reading.**
  - In median ms and fps, no arm differs from base by more than about ±4-6 %.
  - The S4a-vs-S3d direction (1-2.5 % slower) is a hint; more base runs would settle it.
  - L-ls puts d11, d11t and d11p at +2.4 to +2.8 % with CIs that exclude 0. L-ls is a sensitivity method only, and D-emhz+putil does not confirm it.
- **d11t's tail, a lead** (the B-block, d11, per-round and without-1821 numbers are from [tstd.md](../tstd-xcheck/tstd.md)).
  - p99 is +8.8 % (the CI excludes 0); B-block T-std confirms it with [+2.1, +15.9]\*.
  - 1 % low is −8.1 %: n.s. with T-std [−16.1, +0.7], but B-block gives [−14.2, −1.6]\*. RESULTS.md does not state the B-block 1 % low result.
  - Against d11 (same bin and cvars; only the wait differs): p99 +8.2 %, T-std [+0.5, +16.6]\* and B-block [+1.6, +15.3]\*; 1 % low −7.7 %, B-block [−13.8, −1.2]\*.
  - Per round (r1 / r2 / r3), d11t is worse than base in all 3: p99 +9.9 / +1.3 / +15.6 %, 1 % low −8.7 / −0.8 / −14.3 %. Against d11: p99 +8.1 / +2.7 / +14.2 %. Most of the size is in r1 and r3.
  - T-heavy 1 % low: d11t −8.5 % [−14.4, −2.3]\* and d11p −11.0 % [−16.7, −4.8]\*.
  - d11 is about 0 on all of these, so the tail points at the new wait modes, blocking most. d11p points the same way by less: worse than d11 in 3 of 3 rounds (p99 +7.0 / +2.6 / +5.0 %), but its p99 and 1 % low CIs include 0 in both models.
  - Agent 7's band rule on the B-block medians reads p99 `worse` for s0 (+4.8 %), d11t (+9.1 %) and d11p (+6.2 %), against base's narrow adjusted band (4.1 %). That rule is weaker than the CIs and does not single out d11t.
  - It is 1 of 16 T-std tests at 5 %, so treat it as a lead for a later window, not a verdict.
  - 1821-d11t-r3, the deepest-slow-state run and one of the 3 host-flagged runs, is in d11t. Without it (d11t n = 2), no CI excludes 0:

    | d11t vs | model | p99 % | 1 % low % |
    |---|---|---|---|
    | base | T-std, df 9 | +4.57 [−1.48, +10.99] | −3.59 [−10.44, +3.78] |
    | base | B-block, df 7 | +5.30 [−0.12, +11.00] | −4.85 [−10.20, +0.83] |
    | d11 | T-std, df 9 | +4.06 [−1.96, +10.45] | −3.22 [−10.09, +4.19] |

    - The T-std deltas vs base shrink to 52 % (p99) and 44 % (1 % low) of the full-set ones. With hT_ref recomputed over the 14 runs (0.2102) they are +4.59 / −3.60 %.
    - So the lead rests largely on 1821 (r3) and on round 1. It is still worth a test in a later window (W6 has no timer arms).

### Raw pooled CI (my procedure's noise step; T-std guard b)

Method: the pooled within-arm SD of ln(value) over the 15 kept runs (df 10). Sources: [pair-ci.md](pair-ci.md), and Agent 7's `build/agent7/w4b-noise/report-w5.md`.

| metric | pooled SD | 95 % band, 3 vs 3 |
|---|---|---|
| median ms | 6.48 % | +-12.5 % |
| fps | 9.66 % | +-19.2 % |
| p99 | 9.25 % | +-18.3 % |
| 1% low | 9.56 % | +-19.0 % |

| comparison | median ms: geo-mean delta [95 % CI] | fps: geo-mean delta [95 % CI] |
|---|---|---|
| s0 vs base | +1.3 [-9.9, +14.0] | -2.0 [-17.8, +16.8] |
| d11 vs base | -0.9 [-11.9, +11.5] | +3.1 [-13.5, +22.9] |
| d11t vs base | +4.3 [-7.3, +17.3] | -5.2 [-20.5, +13.0] |
| d11p vs base | -0.2 [-11.3, +12.3] | +1.3 [-15.0, +20.7] |
| d11 vs s0 | -2.2 [-13.0, +10.1] | +5.3 [-11.7, +25.5] |
| d11t vs s0 | +2.9 [-8.5, +15.8] | -3.3 [-18.9, +15.3] |
| d11p vs s0 | -1.5 [-12.4, +10.9] | +3.4 [-13.3, +23.2] |
| d11t vs d11 | +5.2 [-6.5, +18.4] | -8.1 [-22.9, +9.5] |
| d11p vs d11 | +0.7 [-10.5, +13.3] | -1.8 [-17.6, +17.1] |
| d11p vs d11t | -4.3 [-14.9, +7.7] | +6.9 [-10.3, +27.4] |

- My recompute (`build/agent8/scratch/w5_pair_ci.py`) reproduces Agent 7's vs-base CIs to 0.1 pp. The pair rows are mine, with the same method.
- **No CI excludes 0**, for any of median, fps, p99 or 1% low. That is the same answer as the min..max rule.
  - d11t's largest gaps come from 1821-d11t-r3, the run deepest in the slow state (E 551 MHz, P util 91.4 %):
    - p99 +14.8 % vs base and +13.3 % vs d11;
    - 1% low −11.2 % vs d11.
- **Agent 7's heavy-phase-only cut (A-heavy)** shows d11 better than base in all 3 rounds:
  - p99: -10.2 / -5.7 / -2.9 %;
  - 1% low: +14.8 / +9.3 / +3.6 %;
  - but its pooled CI includes 0 (p99 -6.3 [-16.8, +5.5]).

  Agent 7's final write-up keeps the sys.csv split (A) out of the verdict: it is undefined on most W5 runs. So this is a lead for a later window, not a verdict.
- **Host state explains most of the spread:**
  - Leaving out the post-cold run (1757) gives SD 5.9 %.
  - Leaving out 1757 and the 3 deep-slow-state runs (1808, 1817, 1821) gives 2.4 % (df 6). That cut is chosen by outcome, so it is information only.
  - T-std reaches 2.1 % without dropping any run.

## Proof (R7, README proof-and-gates table)

| arm | mode | 1 ms lines | precise lines | REX_TIMER_WAIT_BLOCKING | TimerQueue % of a core, median (min..max) | busiest 1 s | proof |
|---|---|---|---|---|---|---|---|
| base | spin | 0/0/0 | 0/0/0 | absent | 49.0 (39.5..60.5) | 75.6 | ok |
| s0 | spin | 0/0/0 | 0/0/0 | absent | 50.6 (46.5..55.4) | 71.4 | ok |
| d11 | spin | 1/1/1 | 0/0/0 | absent | 49.0 (47.5..51.1) | 73.4 | ok |
| d11t | blocking | 1/1/1 | 0/0/0 | 1/1/1 | 4.5 (4.0..4.5) | 14.2 | ok |
| d11p | precise | 1/1/1 | 1/1/1 | absent | 5.2 (4.2..5.9) | 13.7 | ok |

- The README expects 1-2 % for d11p. It measured 4.2-5.9 %, close to blocking (4.0-4.5 %).
  - d11p-r1 (5.2 %) and d11p-r3 (5.9 %) get NOTEs at the README's 5 % gate. The read-out gate is 15 %, as for W4b's d11t at 5.0-6.0 %.
  - CPU cannot tell d11t from d11p; only the precise line does.
- Every config check passes: params.cvar = the arm's cvars, env_set keys = the arm's env keys, and bin_dir ends with the arm's bin.
- timerq3 gives mode = arm config on 15 of 15 scored runs (base, s0 and d11 spin; d11t blocking; d11p precise), with 0 flags and 0 MIXED arms.

## game.log health

- **Scanner** ([scan/scan.md](scan/scan.md)):
  - 16/16 runs have 0 [error], [critical], FATAL or STUCK lines, and a normal shutdown.
  - Every run has the same 40 warnings in 5 types. No line type is specific to one arm.
  - Only the Toypad R/W counts differ (8-12, Read = Write); the other 43 line types match.
  - Proof lines:
    - the 1 ms line is in all 9 d11/d11t/d11p runs;
    - the precise line is in the 3 d11p runs;
    - the REX env var is only in d11t;
    - 0 deviations.
- **Agent 6's logdiff** (20:26; gate_logdiff.py read-only, plus an exact-text diff vs s0 and vs base):
  - **Exit.** All 16 runs exit 0x0 after one WM_CLOSE (0.67-0.91 s) and are never killed. WER, dumps, dialogs and not-responding are all 0, and perf.csv never stalled.
  - **Frames.** 0 frames over 33 ms; the max frame is 10.6-19.4 ms.
  - **Gate vs s0 and vs base:** FAIL / NEW / MORE / GONE = 0 for every arm.
    - 65 of the 70 exact log keys are in all 16 runs. The other 5 are the 2 mode lines and 3 IoDismount handle variants (a benign handle-slot race).
  - **Mode lines:**
    - "Host timer resolution set to 1 ms (background opt-out on)": once in 9/9 d11/d11t/d11p runs, 0/7 elsewhere.
    - "TimerQueue: precise wait": once in 3/3 d11p runs, 0/13 elsewhere.
    - d11t's blocking wait logs nothing by design (timer_queue.cpp:59). It is confirmed by run.json env_set in 3/3 runs, and the var is in 0/13 others.
  - **base (S3d) vs s0 (S4a):** no line difference. This is expected: at their defaults, S4a's changes add no log lines.
  - **Cold vs warm base:** the exact text is identical. Boot is slower: boot_s 6.01 vs 4.02-5.01 s.
  - **Toypad:** the normal count is 10/10.
    - 12/12 is the doubled startup handshake (base-r3, d11t-r1, d11t-r2).
    - d11t-r3 has 8/8: only 3 challenges came before the close.
    - This is game-side timing, not an error.
  - **Slow runs:** the logs of 1808, 1817 and 1821 show nothing different.
  - **Clock step:** 1757 has a +8.30 s wall-clock step inside its window (QPC 50.007 s vs epoch 58.306 s). Frame stats are QPC-based and unaffected.

## Game CPU

| arm | game cores, median (min..max) | mean | vs base (median) | decision (R5) | vs s0 (mean) | vs d11 (mean) |
|---|---|---|---|---|---|---|
| base | 3.15 (2.90..3.46) | 3.17 | ref | reference | | |
| s0 | 3.19 (3.08..3.38) | 3.22 | +1.3 % | overlap | | |
| d11 | 3.18 (3.16..3.19) | 3.17 | +0.9 % | overlap | | |
| d11t | 2.72 (2.67..2.84) | 2.74 | −13.7 % | **better** | −14.8 % | −13.6 % |
| d11p | 2.77 (2.69..2.78) | 2.75 | −12.2 % | **better** | −14.7 % | −13.5 % |

- **Mean vs base mean:** d11t −13.5 %, d11p −13.4 %. Blocking and precise together vs the three spin arms: −13.9 %. This confirms Agent 1's ~13 %.
- **Round pairs:** d11t and d11p are lower than every spin arm in the same round, in 18/18 pairs; the mean gap is −0.44 core.
- **Per round vs base:**

  | round | d11t and d11p vs base | note |
  |---|---|---|
  | r1 | −0.13 to −0.18 cores (−4.5 to −6.2 %) | |
  | r2 | −0.77 to −0.79 (−22 to −23 %; d11t −0.786, −22.7 %) | base-r2 is 1817, a deep-slow-state run at 3.46 |
  | r3 | −0.31 to −0.37 | |
- **Source of the saving:** the TimerQueue thread's spin, 46.5-60.5 % of a core in the spin arms vs 4.0-5.9 % in blocking/precise, about 0.45 core.
- **W4b shows the same:** d11t 2.81-3.00 cores vs d0 3.34-3.53, −15.3 %, better in every variant.
- 1757's game value comes from run.json (2.90): the clock step leaves 7 window samples without a proc value.
- "Same frame time" holds only at arm level: d11t-r3 (1821) has p50 +18.9 % vs base-r3.

## Slow state (R3) in the foreground: for Agents 1 and 11

- **Every scored run hits it.**
  - All 15 have E-cores under 800 MHz for 3+ samples inside the window, with fg = 1. Onsets are 1-87 s and slow shares 13-96 % (timerq3).
  - The cold run has none. W4b was the same, 16 of 16.
  - So R3 drops every run in both windows. The comparison has to come from the with-flagged pass and T-std.
- **In W5 it flickers, so the binary flag does not separate runs.**
  - Median 7 slow stretches per run (W4b 1.5).
  - Window mean E clock: 550-749 MHz in 14 of 15 runs (1757: 1174).
  - 65 of the 71 bins with normal fps also have E < 800 MHz (scan.md §4).
- **Depth goes with low fps.**
  - The 3 slowest runs, 1821 (277.1 fps), 1817 (289.2) and 1808 (309.9), have the top 3 P util: 91.4 / 98.5 / 91.5 %, next 86.4.
  - They also have the bottom 3 E clocks: 551 / 554 / 597 MHz, next 609.
  - The fastest run, 1757 (384.6 fps), ran at E 1174 MHz with P util 73.3 %.
  - Spearman vs fps (n = 15):

    | measure | rho |
    |---|---|
    | E busy | −0.979 |
    | P util | −0.957 |
    | E MHz | +0.846 |
    | E<800 share | −0.688 |
    | onset | −0.19 |
    | P MHz (flat, about 1.92-1.94 GHz) | −0.07 |
    | run position | +0.04 |

  - Caveats:
    - P util includes the game's own CPU (the slow runs' game load is 3.38 vs 3.08);
    - the tests are uncorrected and collinear.
- **The onset follows position in the window, not the arm.**
  - 4/5 round-1 runs start late (6-87 s), 2/5 in round 2 and 1/5 in round 3. 8 of the 15 onsets are at 1-4 s.
  - The mean onset by arm (table below) is therefore confounded with run order, in W4b too (Agent 11's caution). It is not an arm effect.

  | arm | mean onset | mean slow % |
  |---|---|---|
  | d11p | 2 s | 73.5 |
  | d11t | 6 s | 74.8 |
  | d11 | 14 s | 65.3 |
  | s0 | 21 s | 60.5 |
  | base | 38 s | 50.2 |

- **Contrast with W4b.**
  - In W4b, an onset inside the window cut the 10 s bins by 30-45 % (1542, 1545, 1547, 1553, 1558).
  - In W5 the bins do not drop at the onset. The slow runs are slow in every bin.
- **Suggested rule change.** R3 as a binary drop removes everything in both windows. A depth covariate would work instead:
  - P util or E MHz;
  - or Agent 7's host flag, P util ≥ 90 % and E < 600 MHz, used as a warning;
  - or T-std, which removes about three quarters of the deep-state excess.

## Host state and disturbance (sys.csv)

Sources: the auditor's [sysaudit/audit.md](sysaudit/audit.md), with report.md and extra.md. The method is the same as W4b's audit:
- ng_t = time-based busy logical CPUs − game cores; this is the add-on's "background";
- ng_u = work-based (utility × logical CPUs) − game cores; this is Agent 1's method.

**Agent 1's notes, checked against sys.csv** (SESSION2 17:52 and 18:34):
- **best_efficiency overlay in every run:** confirmed, 16/16.
  - Also unchanged in every run: AC, the Default desktop, no screensaver, fg_game 100 %.
  - build_procs 0 and ticks_skipped 0 everywhere. No user input (idle 74 s → 1974 s).
- **P clocks flat at ~1.93 GHz:** confirmed. 1920-1945 MHz in every scored window.
- **The 3 slow runs = P saturation + E at 551-597 MHz:** confirmed for P util and for the E clock, with one nuance.
  - P util is 91.4-98.5 %, all above the others' max of 86.4.
  - The E clock is 550-597 MHz, all below the others' min of 609.
  - Nuance: the "saturation" is in utility, not in time. Time-based P busy is 80-87 %, and P sat (the share of samples with P busy ≥ 97 %) is 0 in the slow runs.
- **d11t/d11p use ~13 % less game CPU:** confirmed, −13.5 / −13.4 % on the mean vs base.
- **Defender at ~0.9 core when W5 started:** this cannot be checked from the matrix.
  - sys.csv has system totals only, and proc.csv and threads.csv hold only the game.
  - A grep for MsMpEng, Defender, NisSrv and antimalware found 0 hits.
  - The figure exists only in Agent 1's quiet-1731.log.

**The 7.16-core "background" is occupancy, not 7 cores of other load.**
- The add-on's reference of 7.16 is the ng_t median (7.158).
- The work-based ng_u is 3.30 [3.03..4.40], which matches Agent 1's ~3.0-3.6 logical CPUs.
- The gap is E-core busy time at a low clock: E busy is 93 % in slow samples.
- There are no SAT runs: busy_t max is 11.42 of 12.

**The 3 slow runs vs the other 12** (medians [min..max]):

| measure | slow 3 (1808, 1817, 1821) | other 12 |
|---|---|---|
| fps | 289.2 [277.1..309.9] | 351.3 [333.4..384.6] |
| P util % | 91.5 [91.4..98.5] | 80.4 [73.3..86.4] |
| P busy % (time-based) | 80.8 [80.3..86.7] | 71.0 [64.5..76.4] |
| E busy % | 97.1 [94.9..99.4] | 88.3 [76.0..92.9] |
| E MHz | 554 [550..597] | 722 [609..1174] |
| E<800 share | 1.00 [0.94..1.00] | 0.81 [0.26..0.96] |
| P MHz | 1931 [1923..1938] | 1934 [1920..1945] |
| ng_t | 8.01 [7.65..8.17] | 6.80 [5.70..7.85] |
| ng_u | 3.20 [3.03..3.39] | 3.31 [3.04..4.40] |
| game cores | 3.38 [2.84..3.46] | 3.08 [2.67..3.19] |

- **Slow-state samples only:** P util 94.6 vs 80.4, ng_u 3.20 vs 3.25, ng_t 8.01 vs 7.00.
- **Each slow run is the highest game-CPU run of its arm** (Agent 6 sees the same), +0.1-0.3 core over same-build peers.
- **R6's BG+ on 1821 marks the deep slow state, not a process.** Spearman: fps vs ng_u −0.03 (p 0.92); fps vs ng_t −0.94.

**Known activity:**
- **Agent 1's cron turn at 18:10** (1808's window, 44 samples): ng_u 2.99 vs the run's 3.03, and 0 samples above the p90 (3.79). E was already low from 18:09:14, in the warm-up.
- **Agent 1's reply at 18:21-22:**
  - End of 1819's window: ng_u 3.04, 0 samples above p90.
  - 1821's boot, warm-up and the first 21 s of its window: window ng_u 3.45, 3 samples above p90.
  - 1821's warm-up was the only one in the slow state (from 18:21:48). 1821 then stayed at the E floor until 18:23:28, after the reply had ended.
- **1817** overlaps no logged activity and is just as slow.
- **ng_u bursts:** only 1757 has a cluster, 26/43 samples, all in its fast-state first ~25 s.
- **Call:** no W5 run shows a non-game work burst that can be tied to logged activity.

**Data quality:**
- **1757's clock step.** Its wall clock stepped +8.3 s at 17:59:48 (sys.csv epoch gap 9.29 s; Agent 6 sees +8.30 s in the log). 7 window samples have no proc value, so its game cores come from run.json.
- **Frame and process data:** frame stats are QPC-based. perf.csv and proc.csv are complete.
- **Missing data:** the tz_* columns are empty and power-limit data is not logged. So sys.csv cannot show what drives the E-clock drop.

**W4b vs W5** (medians over scored runs):

| measure | W4b | W5 |
|---|---|---|
| ng_t | 8.13 | 7.16 |
| ng_u (median) | 3.29 | 3.30 |
| P busy / P util % | 90 / 99 | 72 / 83 |
| E busy % | 98 | 90 |
| E MHz | 611 | 699 |
| E<800 share | 0.96 | 0.86 |
| busy_t | 11.40 | 10.12 |

- The equal ng_u medians are structural: ng_u is pinned near 3.2-3.4 in the slow state.
- At comparable clocks (fast-state warm-ups at E ~1.6-1.8 GHz), W4b's non-game work was about 1-3 nominal cores higher:
  - fast-state warm-ups: 5.62-7.59 vs 4.88;
  - cold-run warm-up: 8.27 vs 6.38.

  That fits the other agents working during W4b.

**Auditor caveats:**
- ng_u is pinned at ~3.2-3.4 in the slow state, so use it as a demand measure only in fast samples.
- ng_t and busy saturate.
- E busy uses an empirical fit, f_E = 1.5 × base − 850.
- Agent 1's activity times are coarse.
- The Spearman tests are uncorrected and collinear.
- The 800 MHz threshold is arbitrary.
- Not done: the headroom.json dGPU check (1817: 86 °C, 24 W, no throttle flag).

## Drift between the windows (not a verdict)

base runs W4b's d3 bin (devoff3) with the same window:

| | fps median (min..max) | p50 |
|---|---|---|
| W5 base | 355.6 (289.2..384.6) | 2.546 ms |
| W4b d3 | 248.9 (198.4..298.6) | 3.215 ms |
| change | +42.9 % | -20.8 % |

- Both windows come after the 08:29 Windows Update.
- **W4b** ran with the other agents working: add-on background median 8.14 cores, 5-6 SAT runs.
- **W5** ran with the agents held: background median 7.16, no SAT runs.
- **Load and host state:**
  - On the work-based measure, the non-game load inside the scored windows was the same (ng_u 3.29 vs 3.30, pinned by the slow state).
  - W4b sat deeper in the slow state: E 611 vs 699 MHz, P util 99 vs 83 %, E<800 share 0.96 vs 0.86.
  - At comparable clocks, W4b's non-game work was about 1-3 cores higher.
- So the +42.9 % is mostly host state, not the bin.

## 10 s bins (w5.md, scanner)

- **Draws and frame times.** Draws/frame p50 is 226 in every bin, and no frame is over 33 ms. The scanner's bin fps matches w5.json's stat_bins (78 bins, max |diff| 0.000).
- **First 10 s.** In 13 of 15 scored runs, the 0-10 s bin is slower than the 10-20 s bin. The per-arm medians are 287-333 fps for 0-10 s against 336-366 fps for 10-20 s.
- **Slow bins** (bin fps ≤ 0.85 × the run's median bin): 4 of 75, in 3 runs. Each sits at a lower E clock and a higher P util than the same run's other bins:

  | run | bin | fps | x run median | E MHz | P util % | same run's other bins: E MHz / P util % |
  |---|---|---|---|---|---|---|
  | 1800-s0-r1 | 0-10 s | 284.9 | 0.85 | 581 | 98.1 | 761 / 83.5 |
  | 1804-d11t-r1 | 0-10 s | 296.4 | 0.82 | 586 | 90.3 | 728 / 77.6 |
  | 1804-d11t-r1 | 30-40 s | 303.7 | 0.84 | 611 | 89.9 | 728 / 77.6 |
  | 1813-d11t-r2 | 0-10 s | 287.2 | 0.77 | 550 | 90.5 | 772 / 72.8 |

- **1821 and 1817 are slow in every bin** (258-320 and 274-311 fps; E 538-587 MHz, P util 89-101 %). That points to a host state over the whole window, not a phase change inside it.
- **The other 71 bins:** only 13 have P util ≥ 90 %, but 65 have E < 800 MHz.
- **Pooled-bin Spearman** of bin fps / run median vs (descriptive, since bins of one run are not independent):
  - E MHz +0.43;
  - E<800 share −0.42;
  - P util −0.46.
- The slow-bin table in variants.md is uninformative: base has a single run with slow bins.

## Cross-check

- **Cross-checker** ([xcheck/xcheck.md](xcheck/xcheck.md), [xcheck_compare.csv](xcheck/xcheck_compare.csv)): an independent recompute from the run files of every number in my W5 tables, 1,017 in all.
  - 0 MISMATCH.
  - 16 definition differences.
  - 4 rounding ties: 1757 light share 0.945, 1813 fps 358.8, 1821 cpu 2.83, and the d11t cpu max.
  - It corrected 2 draft numbers, both now in this file: d11t vs base in round 2 is −0.786 cores (−22.7 %), and d11p's mean vs base's mean is −13.4 %.
- **Agent 7's tables:**
  - My rerun of his scripts on W5 is identical to his outputs.
  - His two checkers found 0 mismatches for T-std.
  - T-std and B-block T-std, recomputed independently ([tstd.md](../tstd-xcheck/tstd.md)): 845 of 845 numbers match report-w5.json and 151 of 151 match RESULTS.md, 0 MISMATCH. It adds the B-block 1 % low CI, the d11t vs d11 CIs, the per-round deltas and the without-1821 sensitivity used above.
- **Agreement between sources:**
  - The scanner and the auditor agree on the 3 slow runs and on the E/P facts.
  - Agent 6's log facts agree with the scanner: 40 warnings, 0 errors, the mode lines in 9/9 and 3/3 runs, and the Toypad counts.
  - Agent 7's host flag catches the same 3 runs.
  - Agent 6's perf, threads and GPU pass (#13, 20:55; `build/agent6/w4b/out-20261122-1756-vs-s0/perf-threads.txt`) agrees and adds:
    - Every window frame of every run does the same work (226 draws, 1022 vertices, 0 cache misses, 30 active threads), so the slow runs are not content.
    - The 3 slow runs lie outside every other run on P util (91.4-98.5 % vs ≤ 86.4 %), E MHz (551-597 vs ≥ 609), buffer queue depth (3.17-3.52 vs ≤ 2.96), main XThread busy (72.5-77.1 % vs ≥ 82.5 %) and GPU memory util (19.6-20.6 % vs ≥ 22.5 %). The same work runs slower per CPU-second, which points to CPU placement or contention.
    - The TimerQueue thread is 4.0-5.9 % busy in d11t and d11p against 39.5-60.5 % in base, s0 and d11: the source of the game-CPU saving.
    - The GPU's software thermal throttle (6 runs, from 18:13 on, none in base-r2 or d11t-r3) does not track frame time.
    - The two earliest runs (cold base 17:56, base-r1 17:57) had E-cores at 1683 / 1174 MHz, against 551-749 MHz in every later run, and were the fastest. That fits the NOTE on 1757 under "Verdicts".

## Files

- [rules.md](rules.md) (strict) and [rules-nodrop.md](rules-nodrop.md) (with flagged).
- [w5.md](w5.md) and w5.json: the add-on, reference base, 10 s bins and background.
- [w5-s0.md](w5-s0.md): the support pass with `--ref s0`.
- [timerq3.txt](timerq3.txt) and timerq3.csv.
- [phase.txt](phase.txt) and phase.json.
- recheck.txt and recheck-dropslow.txt.
- [pair-ci.md](pair-ci.md): raw pooled CIs, including the pair rows.
- [variants.md](variants.md): all runs, without 1821, slow-state bins.
- [noise/](noise/): Agent 7's T-std and other methods (report-w5.md/json, noise-case-w5.md, stdout.txt).
- [scan/](scan/), [sysaudit/](sysaudit/), [xcheck/](xcheck/): the subagents' outputs.
- [../tstd-xcheck/](../tstd-xcheck/): the independent T-std and B-block recompute for W4b and W5 (tstd.md, tstd_runs.csv, tstd_compare.csv, tstd_xcheck.py).
- summary.md: a copy of the runner's.

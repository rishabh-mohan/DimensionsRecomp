# Task #6 (was #30): a noise method for W4b's +-19.6 % band. Results (Agent 7, 20:15)

**Answer.** Use **T-std** for W5's read-out. When the window has a round effect, as W4b does, use **B-block T-std**.

- **What T-std does.** Each run's frames are split at the runner's 4.5 ms light threshold. The light and heavy parts are then re-mixed at one fixed heavy-time share, hT_ref, the median over the kept runs.
- **Why it works.** In both windows most of the run-to-run spread is the light/heavy mix. The mix follows the host state: the E-core clock drops from about 1500 to about 550 MHz while the P-threads saturate. It does not follow the arm.
- **W4b, median ms (d0's 4 runs):**
  - the band falls from 19.6 to 7.8 %;
  - the pooled within-arm CV falls from 12.2 to 2.3 %;
  - the 95 % band for 4 vs 4 runs falls from 20.9 to 3.6 %.
  - B-block T-std brings these to 3.6 / 1.4 / 2.3 %.
- **W5, median ms (base's 3 runs):** the band falls from 20.4 to 6.5 % and the CV from 6.5 to 2.1 %.

Full per-method tables for both windows and all 4 metrics are in [results-tables.md](results-tables.md), generated from the report JSONs by [results_tables.py](results_tables.py). The method definitions are in the headers of [report.md](report.md) and [report-w5.md](report-w5.md), and in [DESIGN.md](DESIGN.md).

## Methods

| id | per-run value | used for |
|---|---|---|
| raw | the run-matrix numbers over the whole scored window | reference |
| **T-std** | frames split at 4.5 ms (light < 4.5 ms, the runner's `share_lt_light`); each frame weighted (1 - hT_ref)/T_light or hT_ref/T_heavy, so every run has the same heavy-time share hT_ref (W4b 0.531, W5 0.213); fps, p50, p99 and 1 % low over the reweighted frames | **primary** |
| T-light / T-heavy | light frames only / heavy frames only | the task's "heavy-phase frames only" |
| **B-block T-std** | T-std in a two-way model, arm + round; df = runs - arms - rounds + 1 | **windows with a round effect** |
| B-norm | each run divided by its round's GM; one-way CI with df = runs - arms | do not use its CI: the df is too high (8 is right in both windows, not 11 or 10) |
| B paired | per-arm deltas vs the ref within each round | cross-check |
| L-ls | ANCOVA of ln(value) on the run's light share, with arm as a factor | sensitivity only |
| D-* | ANCOVA on sys.json covariates: E-core MHz (emhz), P util (putil), non-game CPUs (nongame) | sensitivity only |
| A-* | phase split by the sys.csv slow state (e_eff_mhz < 800 for >= 3 samples, Agent 11) | fails: 9 of 15 W4b runs are in the slow state for the whole window, and the split is undefined on most W5 runs |
| A2-* | phase split by a 201-frame rolling median > 5 ms | works on W4b, but W5 has no heavy phase (h2_ref 0.001) |
| C-frames / C-bins | 20 % trimmed mean of frame times / trimmed mean of the 10 s bins | no gain: the noise is per run, not per frame or bin |

## W4b (`build/agent8/matrix/20261122-1541`): ref d0; 15 kept runs

Left out: the cold run, and 1551-B-r2 (valid_timing false). Cells: GM delta vs d0 in %, with the pooled 95 % CI. `*` = the CI excludes 0.

| method | metric | d0 band % | pooled CV % | 4 vs 4 band % | df | B (n=3) | d3 (n=4) | d11t (n=4) |
|---|---|---|---|---|---|---|---|---|
| raw | median ms | 19.6 | 12.2 | 20.9 | 11 | -8.3 [-25.3, +12.6] | -0.9 [-18.1, +19.8] | -0.1 [-17.4, +20.8] |
| **T-std** | median ms | 7.8 | 2.3 | 3.6 | 11 | -2.1 [-5.8, +1.8] | -1.5 [-4.9, +2.1] | -0.5 [-4.0, +3.1] |
| **B-block T-std** | median ms | 3.6 | 1.4 | 2.3 | 8 | -2.5 [-5.0, +0.0] | -1.5 [-3.7, +0.8] | -0.5 [-2.8, +1.8] |
| B-norm T-std (CI too narrow) | median ms | 3.7 | 1.2 | 1.9 | 11 | -2.4 [-4.4, -0.4] * | -1.5 [-3.3, +0.4] | -0.5 [-2.4, +1.4] |
| L-ls | median ms | 11.9 | 4.7 | 7.6 | 10 | -2.0 [-9.7, +6.3] | -0.6 [-7.7, +6.9] | -2.8 [-9.7, +4.6] |
| A2-light | median ms | 8.1 | 6.0 | 9.8 | 11 | -5.6 [-14.6, +4.5] | -2.6 [-11.3, +6.9] | +0.1 [-8.8, +9.9] |
| A2-std | median ms | 9.2 | 7.3 | 12.1 | 10 | -4.9 [-15.9, +7.6] | -2.1 [-13.5, +10.7] | +0.1 [-10.7, +12.3] |
| D-emhz+putil | median ms | 10.4 | 7.1 | 12.0 | 9 | +3.0 [-10.6, +18.6] | +5.3 [-6.7, +18.9] | +2.9 [-9.7, +17.2] |
| B-block raw | median ms | 17.6 | 12.7 | 23.0 | 8 | -10.3 [-28.7, +12.8] | -0.9 [-19.5, +21.9] | -0.1 [-18.8, +22.9] |
| A-heavy | median ms | 99.0 | 23.7 | 44.7 | 11 | -18.5 [-45.3, +21.5] | -5.5 [-34.7, +36.8] | -18.7 [-43.8, +17.7] |
| raw | fps | 23.6 | 14.7 | 25.6 | 11 | +13.5 [-11.3, +45.2] | +2.5 [-18.4, +28.8] | -0.7 [-21.0, +24.7] |
| **T-std** | fps | 12.7 | 4.1 | 6.6 | 11 | +5.2 [-1.8, +12.8] | +2.3 [-4.0, +9.1] | +2.5 [-3.9, +9.3] |
| **B-block T-std** | fps | 6.4 | 3.0 | 4.9 | 8 | **+6.0 [+0.5, +11.8] \*** | +2.3 [-2.5, +7.4] | +2.5 [-2.3, +7.6] |
| C-bins | fps | 18.8 | 14.5 | 25.3 | 11 | +14.6 [-10.1, +46.2] | +1.7 [-18.8, +27.4] | +1.0 [-19.4, +26.5] |
| C-frames | fps | 33.2 | 18.7 | 33.7 | 11 | +15.0 [-16.0, +57.4] | +3.2 [-22.9, +38.0] | -1.2 [-26.2, +32.1] |

Median deltas, the summary.md form, all `within` the method's own band:

| method | B | d3 | d11t |
|---|---|---|---|
| raw | -10.8 | -5.4 | -1.1 |
| T-std | -0.8 | -0.6 | +0.2 |
| B-block T-std | -1.9 | -1.1 | -0.4 |

Paired within-round deltas on median ms:
- raw: ranges 15.1 / 37.1 / 34.7 pp;
- T-std: ranges 6.9 / 3.7 / 3.5 pp; mean +- 95 % = B -2.5 +- 8.8, d3 -1.5 +- 2.8, d11t -0.5 +- 2.7.

**Reading.**
- **d3 and d11t:** no difference from d0 beyond about +-3-4 %.
- **B (codegen B):** probably a few % faster than d0 in mix-matched frames: fps +5 to +6 %, median ms -2 to -2.5 %. The CI excludes 0 only for B-block fps, with n = 3. Treat it as a hint.
- **Round effect:** round 1 is slower. In B-block T-std, rounds 2-4 have median ms 3.1-4.1 % below round 1, and d0-r1's light frames are 22 % slower than d0's other runs. That is why B-block helps here.

## W5 (`build/agent8/matrix/20261122-1756`): ref base = devoff3 (S3d); 15 kept runs

s0, d11, d11t and d11p share devoff4 (S4a). 3 runs per arm; the cold run is left out.

| method | metric | base band % | pooled CV % | 4 vs 4 band % | df | s0 | d11 | d11t | d11p |
|---|---|---|---|---|---|---|---|---|---|
| raw | median ms | 20.4 | 6.5 | 10.7 | 10 | +1.3 [-9.9, +14.0] | -0.9 [-11.9, +11.5] | +4.3 [-7.3, +17.3] | -0.2 [-11.3, +12.3] |
| **T-std** | median ms | 6.5 | 2.1 | 3.3 | 10 | +1.1 [-2.7, +5.0] | +1.2 [-2.5, +5.2] | +2.4 [-1.4, +6.4] | +1.5 [-2.3, +5.4] |
| B-block T-std | median ms | 5.7 | 2.3 | 3.8 | 8 | +1.1 [-3.1, +5.5] | +1.2 [-3.0, +5.7] | +2.4 [-1.9, +6.9] | +1.5 [-2.8, +5.9] |
| L-ls | median ms | 0.7 | 0.9 | 1.5 | 9 | +1.0 [-0.7, +2.7] | +2.4 [+0.7, +4.2] * | +2.6 [+0.9, +4.4] * | +2.8 [+1.1, +4.5] * |
| D-emhz+putil | median ms | 1.2 | 2.1 | 3.4 | 8 | -0.2 [-4.4, +4.3] | +0.4 [-4.2, +5.2] | +4.1 [-1.0, +9.4] | +1.5 [-3.9, +7.3] |
| A-heavy | median ms | 9.4 | 4.3 | 7.0 | 10 | -0.2 [-7.7, +8.0] | -4.2 [-11.4, +3.6] | +0.1 [-7.4, +8.3] | -4.9 [-12.1, +2.9] |
| B-block raw | median ms | 17.1 | 7.0 | 12.1 | 8 | +1.3 [-11.2, +15.6] | -0.9 [-13.1, +13.1] | +4.3 [-8.6, +19.0] | -0.2 [-12.5, +13.9] |
| raw | fps | 26.8 | 9.7 | 16.4 | 10 | -2.0 [-17.8, +16.8] | +3.1 [-13.5, +22.9] | -5.2 [-20.5, +13.0] | +1.3 [-15.0, +20.7] |
| **T-std** | fps | 5.8 | 1.8 | 2.9 | 10 | -1.4 [-4.6, +2.0] | -0.8 [-4.0, +2.6] | -2.6 [-5.7, +0.7] | -1.6 [-4.8, +1.7] |
| B-block T-std | fps | 5.1 | 2.0 | 3.3 | 8 | -1.4 [-5.0, +2.4] | -0.8 [-4.4, +3.0] | -2.6 [-6.2, +1.2] | -1.6 [-5.2, +2.1] |
| C-frames | fps | 20.2 | 6.8 | 11.3 | 10 | -0.7 [-12.3, +12.4] | +2.0 [-9.9, +15.5] | -3.5 [-14.8, +9.2] | +1.2 [-10.5, +14.6] |
| **T-std** | p99 ms | 6.9 | 4.1 | 6.7 | 10 | +2.8 [-4.6, +10.8] | +0.5 [-6.7, +8.3] | **+8.8 [+1.0, +17.2] \*** | +5.3 [-2.2, +13.5] |
| **T-std** | 1 % low fps | 6.9 | 5.0 | 8.2 | 10 | -2.5 [-11.0, +6.8] | -0.4 [-9.1, +9.1] | -8.1 [-16.1, +0.7] | -6.3 [-14.4, +2.7] |

Median deltas on median ms, all `within`:

| method | s0 | d11 | d11t | d11p |
|---|---|---|---|---|
| raw | +5.5 | +2.6 | +4.0 | +3.1 |
| T-std | +2.3 | +2.5 | +2.7 | +2.1 |

W5 has no round effect: the B-block round terms are +0.8 and -0.2 % on median ms. So B-block T-std has the same deltas as T-std, with a slightly wider CI from the 2 df it spends. W5 has no A2 heavy phase, so A2 is undefined there.

**Reading.**
- **Frame time:** no arm differs from base beyond about +-4-6 %.
- **S4a vs S3d:** all four S4a arms point the same way, 1-2.5 % slower than base (T-std). L-ls puts d11, d11t and d11p at +2.4 to +2.8 % (CI excludes 0), but D-emhz+putil does not confirm it. Treat it as a hint that S4a's light frames are slightly slower; more base runs would settle it.
- **Tail, a hint:** d11t's p99 is about 9 % worse and its 1 % low about 8 % worse (T-std). B-block T-std confirms the p99 ([+2.1, +15.9]) and L-ls agrees. d11 (the same build without the blocking timer wait) is about 0 on both, so the difference points at `REX_TIMER_WAIT_BLOCKING=1`. It is one of 16 T-std tests (4 arms x 4 metrics) at 5 %, so treat it as a lead and not a result.

## The noise cases

From [noise-case-w5.md](noise-case-w5.md) and [noise-case-w4b.md](noise-case-w4b.md), written by [noise_case.py](noise_case.py).
- **Residual:** leave-one-out, the run vs the GM of the other runs of its arm, in % (+ = slower).
- **Flag:** sys.json window P util >= 90 % and E-core MHz < 600.

**W5** (Agent 1's case). The flag catches exactly the three slow runs:

| run | P util % | E MHz | light share |
|---|---|---|---|
| 1808-s0-r2 | 91.5 | 597 | 0.822 |
| 1817-base-r2 | 98.5 | 554 | 0.765 |
| 1821-d11t-r3 | 91.4 | 551 | 0.763 |

Median-ms residuals of those three, mean of the three, and what is left of raw's excess. The RMS of the other 12 runs is in brackets:

| method | s0-r2 / base-r2 / d11t-r3 | mean | left of raw [RMS others] |
|---|---|---|---|
| raw | +6.2 / +18.3 / +16.6 | +13.7 | 100 % [5.4] |
| **T-std** | +1.0 / +5.4 / +3.8 | +3.4 | **25 %** [2.1] |
| B-block T-std | | +3.0 | 22 % |
| L-ls | | -0.4 | -3 % [1.1] |
| D-emhz+putil | | +1.2 | 9 %, but d11t-r3 is still +6.1 |
| A-heavy | | | 60 % |
| D-nongame | | | 81 % |
| B-norm raw | | | 87 % |

- On fps, T-std leaves 14 % of raw's excess, C-frames 67 % and C-bins 111 %.
- The flagged runs' light frames are slow too (T-light +0.9 / +6.0 / +3.3 %). So the host state slows every frame a little, as well as shifting the mix. T-std removes the mix part, which is about three quarters.
- The fastest W5 run, base-r1, has the E-cores at 1174 MHz right after the cold run.

**W4b.** The flag is common here: 7 of 15 runs (d11t-r1, d11t-r2, d3-r3, d0-r3, B-r3, d11t-r4, d0-r4).
- Median-ms mean excess of the flagged runs: raw +13.1 % (RMS of the others 10.9), T-std -0.6 % (3.1), B-block T-std -0.1 % (1.7), A2-std +7.6 % (58 % of raw), D-emhz+putil +2.6 % (20 %), D-nongame 75 %, B-norm raw 81 %.
- One flagged run is fast in raw (d11t-r4, -8.9 %), so the flag is a warning, not a correction.

## Recommendation for W5's read-out

1. **Primary: T-std.** Report per-arm GM deltas vs base with the pooled 95 % CI (df = runs - arms) on median ms and fps. Add p99 and 1 % low with the same method, marked as noisier. Keep the summary.md-style median delta against the T-std ref band for continuity. On W5 the T-std band is 6.5 % (median ms) and 5.8 % (fps), against raw's 20.4 / 26.8 %.
2. **Rounds.** Check the B-block round terms. If they are large, as in W4b (3-4 %), use B-block T-std, with df = runs - arms - rounds + 1. For W5 they are about 0, so T-std stands.
3. **Guards, on every read-out:**
   - (a) **Light share per arm with its one-way F.** T-std fixes the mix, so it hides an arm that changes the mix. W5 F = 0.33 on (4, 10) and W4b F = 0.40 on (3, 11), so no arm moves the mix in either window.
   - (b) **Raw GM deltas with the pooled CI.** They must not contradict T-std.
   - (c) **The host-state flag list.**
4. **Not for the verdict:**
   - B-norm's CI (too narrow);
   - L-ls and D-* (sensitivity only: L's covariate comes from the outcome, D-putil and cores include the game's own CPU, and cores is arm-affected, F = 8.1 in W5);
   - A (undefined or 1-2 runs per arm), A2 (no heavy phase in W5) and C (no gain).
5. **For W6 (Agent 1's call; it needs the user by 23:30).**
   - **Where the noise comes from:** the host state. Every sys.csv row has the Balanced scheme with the best_efficiency overlay, and the E-cores drop to about 550 MHz while the P-threads saturate.
   - **Likely fix at the source:** the best-performance power overlay or P-core affinity for the game. That would likely remove most of the spread before any statistics.

## Caveats

- **The light share comes from the outcome.** It is computed from the same frame times. T-std uses it only to set the mix, and the F guard checks that no arm moves it. L-ls regresses on it, so L-ls can absorb part of an arm effect.
- **T-light p99 and 1 % low are degenerate:** they are capped at 4.5 ms.
- **Small n.** n = 3 per arm in W5 and for B in W4b. The range bands on 3-4 runs are noisy; prefer the CIs.
- **e_eff_mhz is undefined in the source:** it may include idle time.
- **Multiple tests:** many methods x metrics x arms, so a single `*` is a lead, not a result.

## Checks

- **Self-test:** [test_noise_methods.py](test_noise_methods.py), RESULT PASS, 44 checks, 0 failed. It covers B-block with a hand-computed 2-arm x 3-round case (b, sd, df = 2, CI with t = 4.303), the loo residual signs and the host flag.
- **Checker 1** (independent code that imports neither noise_methods.py nor w4b_readout.py): 0 mismatches in both windows.
  - Checked: raw for all runs, the T split and hT_ref, the light-share check, A2, the per-method summaries (raw, T-std, T-light, T-heavy and A2 x 4 metrics), and the L-ls ANCOVA.
  - Max relative difference 7e-14. The numbers in report.md (1219) and report-w5.md (1300) also agree.
  - Files: [check-phase/](check-phase/).
- **Checker 2:** 0 mismatches in both windows, within 1e-13 pp.
  - Checked: raw vs summary.md and results.csv, B paired, B-norm (raw, T-std), C-frames and C-bins, the D ANCOVAs and cov_info, and noise_case.
  - Files: [check-bct/](check-bct/).
- **B-block (added after the checkers started):** no independent recompute. Its consistency checks hold:
  - in W5, which is balanced, its deltas equal T-std's and B-norm's exactly;
  - its CV equals B-norm's x sqrt(df_norm / 8): W5 2.0 to 2.3, W4b 1.2 to 1.4.
- **Not recomputed independently:** A (the sys.csv split). It is not recommended.

## Files (`build/agent7/w4b-noise/`)

- **Code:** noise_methods.py (methods and reports), test_noise_methods.py, noise_case.py (residuals and the host flag), results_tables.py (results-tables.md). explore_cov.py is scratch.
- **Outputs:** report.md / report.json (W4b), report-w5.md / report-w5.json (W5), results-tables.md, noise-case-w4b.md, noise-case-w5.md.
- **Commands** (read-only, one process each, about 10 s on an idle machine):
  - `python -B build\agent7\w4b-noise\noise_methods.py [<matrix dir>] -o <md> --json <json>`; the default dir is W4b.
  - `python -B build\agent7\w4b-noise\noise_case.py <json> -o <md>`
  - `python -B build\agent7\w4b-noise\results_tables.py`

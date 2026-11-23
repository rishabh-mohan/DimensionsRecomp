# T-std / B-block T-std independent cross-check (helper of Agent 8)

Inputs: build/agent8/matrix/20261122-1541 (W4b) and 20261122-1756 (W5) (results.csv, perf.csv, run.json, frames.json). Compared with build/agent7/w4b-noise/report.json, report-w5.json and RESULTS.md (20:15). Script: tstd_xcheck.py (own code). Per-run values: tstd_runs.csv. Every comparison: tstd_compare.csv.

## Readings (facts)

- **Reproduced.** My code matches report.json / report-w5.json in 1585 of 1585 items, within 1e-9 relative. The largest per-run relative difference is 1.1e-15. The items cover:
  - every per-run T-std value and hT, and hT_ref;
  - every one-way and B-block T-std summary: band, sd, CV, 4v4, df, round terms b, adjusted values, GM deltas, CIs, stars, median deltas and verdicts;
  - every paired value, and the light-share F.
- **RESULTS.md:** 241 of 242 cells match. No other cell differs.
  - **L69, a definition difference.** L69 says rounds 2-4 have median ms 3.1-4.1 % below round 1. As 100 (exp(b) - 1), the B-block median-ms round terms (r2 / r3 / r4) are -4.04 / -3.09 / -3.90 %, i.e. 3.1-4.0 %. "3.1-4.1" is 100 |b| in log points (4.12 / 3.14 / 3.98). The reading does not change.
- **W4b, B-block T-std fps, B vs d0:** +5.98 [+0.49, +11.77] * (df 8) is reproduced; scipy's exact t(8) gives the same to 2 dp. It rests on few runs:
  - Leave-one-out (one B or d0 run at a time): 3 of 7 variants keep the CI above 0.
  - The CI includes 0 without 1542-d0-r1: +3.70 [-0.97, +8.59]; without 1545-B-r1: +3.50 [-1.98, +9.29]; without 1611-d0-r4: +6.11 [-0.52, +13.19]; without 1613-B-r4: +6.73 [-0.19, +14.12].
  - Paired T-std fps B vs d0 by round (r1 / r3 / r4): +14.71 / +1.34 / +4.62; mean +6.89 +- 17.31; 3/3 up.
  - B-block median ms B: -2.509 [-4.960, +0.004]. The upper bound is +0.004, so RESULTS.md's "+0.0" with no star is right, but at the edge.
- **W5, d11t tail lead (reproduced):**
  - T-std: p99 +8.76 [+0.95, +17.18] *, 1 % low -8.08 [-16.10, +0.69].
  - B-block: p99 +8.76 [+2.10, +15.86] *, which matches L103 [+2.1, +15.9]. B-block 1 % low -8.08 [-14.16, -1.58] * also excludes 0; RESULTS.md does not state this.
- **W5, without 1821-d11t-r3** (n = 2; RESULTS.md L117 lists it as a flagged host-state run):
  - vs base: p99 +4.57 [-1.48, +10.99], 1 % low -3.59 [-10.44, +3.78]. These are 52 % and 44 % of the full-set deltas.
  - vs d11: p99 +4.06 [-1.96, +10.45], 1 % low -3.22 [-10.09, +4.19] (one-way, df 9).
  - B-block vs base (df 7): p99 +5.30 [-0.12, +11.00], 1 % low -4.85 [-10.20, +0.83].
  - With hT_ref recomputed over the 14 runs (0.2102): p99 +4.59, 1 % low -3.60 vs base.
  - No CI excludes 0 without this run.
- **W5, per round (r1 / r2 / r3):**
  - d11t vs d11: p99 +8.06 / +2.74 / +14.22 (worse in 3/3 rounds); 1 % low -8.82 / -1.28 / -12.71 (worse in 3/3).
  - d11t vs base: p99 +9.87 / +1.32 / +15.59 (worse in 3/3 rounds); 1 % low -8.70 / -0.75 / -14.30 (worse in 3/3).
  - d11p vs d11: p99 +6.95 / +2.58 / +4.97 (worse in 3/3 rounds); 1 % low -7.93 / -3.70 / -6.04 (worse in 3/3).
  - d11p vs base: p99 +8.73 / +1.16 / +6.22 (worse in 3/3 rounds); 1 % low -7.81 / -3.18 / -7.75 (worse in 3/3).
- **W5 round terms (r2, r3 vs r1):**
  - Median ms +0.77 / -0.17 % and fps -0.72 / -0.48 %: about 0, matching L98.
  - p99 +3.11 / +5.72 % and 1 % low -3.14 / -7.32 %: not 0.
  - So for p99 and 1 % low the B-block CIs are narrower than T-std's, not wider. 4v4 band: p99 5.63 vs 6.67, 1 % low 6.10 vs 8.22. L98's "slightly wider CI" holds only for median ms (3.77 vs 3.35) and fps (3.31 vs 2.91).
- **hT_ref:** W4b 0.531229 (the median run is 1608-d11t-r4) and W5 0.212886 (1802-d11-r1). Both match L21 (0.531 / 0.213).
- **Light-share F:** W4b 0.4000 on (3, 11), p 0.76; W5 0.3329 on (4, 10), p 0.85. Both match L145.

## Comparison counts

DEF = the cell matches another definition of the same quantity (named in the note).

| window | source | items | MATCH | NEAR | TIE | DEF | MISMATCH |
|---|---|---|---|---|---|---|---|
| w4b | report-json | 740 | 740 | 0 | 0 | 0 | 0 |
| w4b | RESULTS.md | 91 | 90 | 0 | 0 | 1 | 0 |
| w5 | report-json | 845 | 845 | 0 | 0 | 0 | 0 |
| w5 | RESULTS.md | 151 | 151 | 0 | 0 | 0 | 0 |

Items that are not MATCH:

- w4b RESULTS.md, L69 B-block largest round term below round 1 % (100 (1 - exp(b))): mine 4.036467247783648, theirs 4.1 (DEF) 1 dp; the cell matches 100 |b| (log points) = 4.1202

## Definitions (re-implemented from noise_methods.py; nothing imported or run)

- **Window:** the perf.csv data rows with every field an integer. The first row is the first one whose end offset is past run.json `measure_start.perf_csv_bytes`. Rows are taken until their frame_time_us sum (values <= 0 count as 0) reaches `params.seconds` x 1e6. Frames are the window rows with frame_time_us > 0. first_row and rows are checked against frames.json `window` for every run.
- **T split:** light = frame time < frames.json `light_ms` (4.5 in every run) x 1000 us; heavy = the rest. hT = heavy time / window time. Light share ls_T = light frames / frames, checked against frames.json `share_lt_light`.
- **Kept runs:** results.csv scored = True, valid_timing = True and excluded = False. That gives 15 in W4b (no cold, no 1551-B-r2) and 15 in W5 (no cold). hT_ref = statistics.median of hT over the kept runs (0 < hT < 1).
- **T-std per run:**
  - Weights: (1 - hT_ref) / T_light for each light frame and hT_ref / T_heavy for each heavy frame (T in us).
  - Total weight W = (1 - hT_ref) n_L / T_L + hT_ref n_H / T_H; fps = 1e6 W.
  - p50 / p99 = the smallest frame time whose ascending cumulative weight reaches 0.5 W / 0.99 W (x (1 - 1e-12)).
  - 1 % low = 1e6 x 0.01 W / the weighted time of the slowest 0.01 W of weight; the last frame is taken partially.
  - Implemented with numpy argsort, cumsum and searchsorted.
- **One-way T-std (per metric, over the kept runs):**
  - band = 100 (max - min) / median of the reference's values.
  - sd = pooled within-arm SD of ln(value), df = runs - arms; t = the 3-dp t975 table, taking the smaller df between entries (the same table as noise_methods.py; scipy's exact t is shown for the starred cells).
  - GM delta = 100 (exp(dl) - 1), dl = mean ln(arm) - mean ln(ref); CI = exp(dl +- t sd sqrt(1/n_a + 1/n_ref)).
  - CV = 100 sd; 4 vs 4 band = 100 (exp(t sd sqrt(1/2)) - 1).
  - Median delta = 100 (median arm - median ref) / median ref; it is `within` when |delta| <= band.
- **B-block T-std:**
  - OLS (numpy lstsq) of ln(value) on arm indicators plus dummies for rounds 2.. (round 1 is the base).
  - df = runs - rank = runs - arms - rounds + 1, which is 8 in both windows. sd = sqrt(SSE / df).
  - The arm contrast vs the reference and its SE come from sd^2 c'(X'X)^-1 c, with the CI from t975(df).
  - Band, median delta and the arms' med/lo/hi use the adjusted values exp(ln v - (d - mean d) . b), where d = the run's round dummies (Agent 7's convention). Round terms are shown as 100 (exp(b) - 1).
  - Internal checks: b equals the arm-demeaned (within-arm) regression, and the GM delta equals the difference of the adjusted values' mean logs.
- **Paired:** per round, 100 (arm - ref) / ref. Then the median, mean, range, sd (n - 1), hw95 = t975(n - 1) sd / sqrt(n), and the rounds with delta > 0 ("up").
- **Light-share F:** one-way ANOVA of ls_T on the arm over the kept runs, df (arms - 1, runs - arms); scipy f_oneway is used as a check.

## Tolerances

- **report-json** (Agent 7's report.json / report-w5.json, full precision):
  - MATCH: |mine - theirs| <= max(1e-9 x |value|, 1e-10).
  - NEAR: <= 1e-6 relative.
  - Otherwise MISMATCH. ints, bools, strings and lists of rounds must be equal.
- **RESULTS.md** (1 dp; hT_ref 3 dp; F 2 dp):
  - MATCH: my value printed with the same decimals equals the cell.
  - TIE: it does not, but it is within half a unit (+1e-9), i.e. at a rounding boundary.
  - Otherwise MISMATCH. Stars are compared with ci_excludes_0.

## W4b (matrix 20261122-1541), ref d0

- Kept runs: 15. hT_ref = 0.531229 (1608-d11t-r4 0.5312). Window first_row/rows differ from frames.json in: none.
- max |ls_T - frames.json share_lt_light| = 4.72e-05 (share_lt_light has 4 dp). B-block internal checks: max |b - b(within-arm)|, |GM - GM(adjusted)| = 6.9e-13.

### Per run (T-std at hT_ref)

| run | arm | rnd | kept | frames | hT | light share | fps | p50 ms | p99 ms | 1 % low fps | max rel diff vs report-json |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1541-cold-d0 | d0 | 0 | no | 9776 | 0.1312 | 0.9229 | 264.01 | 3.543 | 7.264 | 117.23 | 1.2e-16 |
| 1542-d0-r1 | d0 | 1 | yes | 12821 | 0.3652 | 0.8075 | 224.66 | 3.389 | 11.344 | 80.76 | 0.0e+00 |
| 1545-B-r1 | B | 1 | yes | 15857 | 0.2809 | 0.8703 | 257.69 | 3.172 | 10.553 | 85.24 | 3.3e-16 |
| 1547-d3-r1 | d3 | 1 | yes | 11549 | 0.5737 | 0.6709 | 240.79 | 3.264 | 11.002 | 84.02 | 1.7e-16 |
| 1549-d11t-r1 | d11t | 1 | yes | 10321 | 0.6834 | 0.5601 | 241.79 | 3.288 | 11.036 | 83.21 | 5.1e-16 |
| 1551-B-r2 | B | 2 | no | 11723 | 0.5688 | 0.6543 | 242.48 | 3.414 | 11.343 | 76.51 | 0.0e+00 |
| 1553-d3-r2 | d3 | 2 | yes | 14932 | 0.3651 | 0.8243 | 258.10 | 3.109 | 10.828 | 80.91 | 1.8e-16 |
| 1556-d11t-r2 | d11t | 2 | yes | 11029 | 0.6546 | 0.5989 | 251.08 | 3.194 | 11.192 | 76.09 | 1.9e-16 |
| 1558-d0-r2 | d0 | 2 | yes | 13523 | 0.4734 | 0.7464 | 256.67 | 3.177 | 10.371 | 80.19 | 1.8e-16 |
| 1600-d3-r3 | d3 | 3 | yes | 9923 | 0.7322 | 0.5134 | 248.35 | 3.189 | 11.718 | 74.75 | 3.8e-16 |
| 1602-d11t-r3 | d11t | 3 | yes | 13859 | 0.4651 | 0.7488 | 261.40 | 3.186 | 10.286 | 81.02 | 5.3e-16 |
| 1604-d0-r3 | d0 | 3 | yes | 11154 | 0.6522 | 0.6001 | 253.08 | 3.191 | 10.242 | 88.51 | 4.8e-16 |
| 1606-B-r3 | B | 3 | yes | 11538 | 0.6317 | 0.6263 | 256.47 | 3.139 | 10.662 | 85.46 | 3.3e-16 |
| 1608-d11t-r4 | d11t | 4 | yes | 12747 | 0.5312 | 0.7015 | 254.91 | 3.158 | 10.377 | 87.37 | 4.9e-16 |
| 1611-d0-r4 | d0 | 4 | yes | 10696 | 0.6830 | 0.5650 | 251.10 | 3.141 | 10.387 | 86.02 | 1.7e-16 |
| 1613-B-r4 | B | 4 | yes | 13791 | 0.4773 | 0.7425 | 262.71 | 3.157 | 10.194 | 88.35 | 1.6e-16 |
| 1615-d3-r4 | d3 | 4 | yes | 13339 | 0.5042 | 0.7228 | 260.24 | 3.142 | 9.989 | 89.83 | 1.6e-16 |

### One-way T-std (df = runs - arms)

GM delta vs d0 in %, [95 % CI], `*` = the CI excludes 0. Then the median delta (verdict against the band).

| metric | d0 band % | CV % | 4v4 % | df | B (n=3) | d3 (n=4) | d11t (n=4) |
|---|---|---|---|---|---|---|---|
| fps | 12.70 | 4.12 | 6.62 | 11 | +5.25 [-1.80, +12.79] | +2.32 [-4.03, +9.10] | +2.50 [-3.86, +9.29] |
| median ms | 7.79 | 2.30 | 3.64 | 11 | -2.08 [-5.79, +1.77] | -1.48 [-4.94, +2.11] | -0.53 [-4.02, +3.09] |
| p99 ms | 10.62 | 4.88 | 7.89 | 11 | -1.03 [-8.82, +7.42] | +2.74 [-4.77, +10.84] | +1.31 [-6.10, +9.30] |
| 1 % low fps | 9.97 | 5.67 | 9.23 | 11 | +3.04 [-6.33, +13.34] | -1.90 [-10.19, +7.15] | -2.35 [-10.60, +6.65] |

| metric | B median delta | d3 median delta | d11t median delta |
|---|---|---|---|
| fps | +2.22 (within) | +0.45 (within) | +0.36 (within) |
| median ms | -0.85 (within) | -0.58 (within) | +0.19 (within) |
| p99 ms | +1.68 (within) | +5.16 (within) | +3.16 (within) |
| 1 % low fps | +2.48 (within) | -1.10 (within) | -1.53 (within) |

### B-block T-std (ln v = arm + round; df = runs - arms - rounds + 1)

GM delta vs d0 in %, [95 % CI], `*` = the CI excludes 0. Then the median delta (verdict against the band).

| metric | d0 band % | CV % | 4v4 % | df | B (n=3) | d3 (n=4) | d11t (n=4) | round terms % (r2, r3, r4) |
|---|---|---|---|---|---|---|---|---|
| fps | 6.35 | 2.95 | 4.93 | 8 | +5.98 [+0.49, +11.77] * | +2.32 [-2.49, +7.36] | +2.50 [-2.31, +7.56] | +7.07, +5.74, +6.74 |
| median ms | 3.65 | 1.41 | 2.33 | 8 | -2.51 [-4.96, +0.00] | -1.48 [-3.72, +0.82] | -0.53 [-2.79, +1.79] | -4.04, -3.09, -3.90 |
| p99 ms | 7.77 | 4.45 | 7.53 | 8 | -0.81 [-8.46, +7.47] | +2.74 [-4.45, +10.47] | +1.31 [-5.78, +8.93] | -2.24, -2.45, -6.78 |
| 1 % low fps | 10.70 | 4.71 | 7.98 | 8 | +1.53 [-6.73, +10.53] | -1.90 [-9.15, +5.92] | -2.35 [-9.57, +5.44] | -4.40, -1.23, +5.51 |

| metric | B median delta | d3 median delta | d11t median delta |
|---|---|---|---|
| fps | +3.72 (within) | +1.53 (within) | +1.27 (within) |
| median ms | -1.90 (within) | -1.06 (within) | -0.42 (within) |
| p99 ms | +0.50 (within) | +1.50 (within) | +1.91 (within) |
| 1 % low fps | +3.07 (within) | +1.97 (within) | -0.35 (within) |

### Paired T-std, per round vs d0

| metric | arm | deltas % by round | median | mean +- hw95 | range pp | up |
|---|---|---|---|---|---|---|
| fps | B | r1 +14.71, r3 +1.34, r4 +4.62 | +4.62 | +6.89 +- 17.31 | 13.37 | 3/3 |
| fps | d3 | r1 +7.18, r2 +0.56, r3 -1.87, r4 +3.64 | +2.10 | +2.38 +- 6.23 | 9.05 | 3/4 |
| fps | d11t | r1 +7.63, r2 -2.18, r3 +3.29, r4 +1.52 | +2.40 | +2.56 +- 6.48 | 9.80 | 3/4 |
| median ms | B | r1 -6.40, r3 -1.63, r4 +0.51 | -1.63 | -2.51 +- 8.79 | 6.91 | 1/3 |
| median ms | d3 | r1 -3.69, r2 -2.14, r3 -0.06, r4 +0.03 | -1.10 | -1.46 +- 2.85 | 3.72 | 1/4 |
| median ms | d11t | r1 -2.98, r2 +0.54, r3 -0.16, r4 +0.54 | +0.19 | -0.52 +- 2.67 | 3.52 | 2/4 |
| p99 ms | B | r1 -6.97, r3 +4.10, r4 -1.86 | -1.86 | -1.58 +- 13.77 | 11.07 | 1/3 |
| p99 ms | d3 | r1 -3.01, r2 +4.41, r3 +14.41, r4 -3.83 | +0.70 | +2.99 +- 13.47 | 18.24 | 2/4 |
| p99 ms | d11t | r1 -2.72, r2 +7.92, r3 +0.43, r4 -0.10 | +0.17 | +1.38 +- 7.27 | 10.63 | 2/4 |
| 1 % low fps | B | r1 +5.56, r3 -3.45, r4 +2.71 | +2.71 | +1.61 +- 11.43 | 9.00 | 2/3 |
| 1 % low fps | d3 | r1 +4.05, r2 +0.90, r3 -15.54, r4 +4.43 | +2.47 | -1.54 +- 15.06 | 19.98 | 3/4 |
| 1 % low fps | d11t | r1 +3.03, r2 -5.11, r3 -8.46, r4 +1.57 | -1.77 | -2.24 +- 8.68 | 11.49 | 2/4 |

### Light share (frames < 4.5 ms) per arm

- Means: d0 0.67975, B 0.74638, d3 0.68282, d11t 0.65231.
- One-way F = 0.4000 on (3, 11), p = 0.756 (scipy f_oneway F = 0.4000).

### Extra: W4b B-block T-std fps, B vs d0, leaving out one B or d0 run at a time (descriptive)

| variant | df | B GM delta [95 % CI] (t table) | CI with scipy t |
|---|---|---|---|
| all 15 kept runs | 8 | +5.98 [+0.49, +11.77] * | [+0.49, +11.77] |
| without 1542-d0-r1 | 7 | +3.70 [-0.97, +8.59] | [-0.97, +8.59] |
| without 1545-B-r1 | 7 | +3.50 [-1.98, +9.29] | [-1.98, +9.28] |
| without 1558-d0-r2 | 7 | +6.74 [+0.85, +12.98] * | [+0.85, +12.97] |
| without 1604-d0-r3 | 7 | +7.03 [+0.67, +13.80] * | [+0.67, +13.80] |
| without 1606-B-r3 | 7 | +7.77 [+1.32, +14.62] * | [+1.32, +14.62] |
| without 1611-d0-r4 | 7 | +6.11 [-0.52, +13.19] | [-0.52, +13.19] |
| without 1613-B-r4 | 7 | +6.73 [-0.19, +14.12] | [-0.19, +14.12] |

- T-std fps B: t table +5.245 [-1.797, +12.793]; scipy t(11) = 2.2010 gives [-1.797, +12.793].
- B-block T-std fps B: t table +5.982 [+0.492, +11.772] *; scipy t(8) = 2.3060 gives [+0.492, +11.772].
- T-std median ms B: t table -2.082 [-5.790, +1.772]; scipy t(11) = 2.2010 gives [-5.790, +1.772].
- B-block T-std median ms B: t table -2.509 [-4.960, +0.004]; scipy t(8) = 2.3060 gives [-4.960, +0.004].

## W5 (matrix 20261122-1756), ref base

- Kept runs: 15. hT_ref = 0.212886 (1802-d11-r1 0.2129). Window first_row/rows differ from frames.json in: none.
- max |ls_T - frames.json share_lt_light| = 4.44e-05 (share_lt_light has 4 dp). B-block internal checks: max |b - b(within-arm)|, |GM - GM(adjusted)| = 5.3e-13.

### Per run (T-std at hT_ref)

| run | arm | rnd | kept | frames | hT | light share | fps | p50 ms | p99 ms | 1 % low fps | max rel diff vs report-json |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1756-cold-base | base | 0 | no | 11875 | 0.0688 | 0.9657 | 365.09 | 2.567 | 5.721 | 146.98 | 0.0e+00 |
| 1757-base-r1 | base | 1 | yes | 19230 | 0.1189 | 0.9445 | 362.73 | 2.496 | 7.064 | 125.74 | 2.3e-16 |
| 1800-s0-r1 | s0 | 1 | yes | 16669 | 0.2614 | 0.8690 | 344.30 | 2.639 | 7.451 | 121.25 | 7.0e-16 |
| 1802-d11-r1 | d11 | 1 | yes | 17519 | 0.2129 | 0.8945 | 350.34 | 2.620 | 7.182 | 125.91 | 1.1e-16 |
| 1804-d11t-r1 | d11t | 1 | yes | 16925 | 0.2391 | 0.8865 | 344.63 | 2.625 | 7.761 | 114.80 | 1.2e-16 |
| 1806-d11p-r1 | d11p | 1 | yes | 17168 | 0.2285 | 0.8924 | 347.03 | 2.610 | 7.681 | 115.92 | 7.4e-16 |
| 1808-s0-r2 | s0 | 2 | yes | 15496 | 0.3589 | 0.8215 | 345.40 | 2.616 | 7.848 | 113.74 | 7.5e-16 |
| 1810-d11-r2 | d11 | 2 | yes | 17567 | 0.2010 | 0.9034 | 348.63 | 2.625 | 7.481 | 119.28 | 6.0e-16 |
| 1813-d11t-r2 | d11t | 2 | yes | 17938 | 0.1812 | 0.9156 | 351.32 | 2.575 | 7.686 | 117.76 | 1.1e-15 |
| 1815-d11p-r2 | d11p | 2 | yes | 17847 | 0.1761 | 0.9170 | 348.50 | 2.609 | 7.674 | 114.87 | 0.0e+00 |
| 1817-base-r2 | base | 2 | yes | 14462 | 0.4367 | 0.7649 | 342.28 | 2.663 | 7.586 | 118.65 | 1.1e-15 |
| 1819-d11-r3 | d11 | 3 | yes | 17624 | 0.2075 | 0.9021 | 351.20 | 2.564 | 7.609 | 115.44 | 1.2e-16 |
| 1821-d11t-r3 | d11t | 3 | yes | 13858 | 0.4540 | 0.7629 | 335.59 | 2.699 | 8.691 | 100.76 | 8.5e-16 |
| 1823-d11p-r3 | d11p | 3 | yes | 16769 | 0.2560 | 0.8810 | 345.74 | 2.608 | 7.987 | 108.46 | 2.6e-16 |
| 1825-base-r3 | base | 3 | yes | 17778 | 0.2050 | 0.9002 | 353.74 | 2.556 | 7.519 | 117.58 | 1.2e-16 |
| 1827-s0-r3 | s0 | 3 | yes | 18000 | 0.1887 | 0.9089 | 354.43 | 2.542 | 7.493 | 117.75 | 4.8e-16 |

### One-way T-std (df = runs - arms)

GM delta vs base in %, [95 % CI], `*` = the CI excludes 0. Then the median delta (verdict against the band).

| metric | base band % | CV % | 4v4 % | df | s0 (n=3) | d11 (n=3) | d11t (n=3) | d11p (n=3) |
|---|---|---|---|---|---|---|---|---|
| fps | 5.78 | 1.82 | 2.91 | 10 | -1.36 [-4.58, +1.96] | -0.78 [-4.02, +2.56] | -2.56 [-5.74, +0.72] | -1.62 [-4.83, +1.69] |
| median ms | 6.53 | 2.09 | 3.35 | 10 | +1.09 [-2.69, +5.01] | +1.25 [-2.53, +5.18] | +2.40 [-1.42, +6.37] | +1.49 [-2.30, +5.42] |
| p99 ms | 6.94 | 4.10 | 6.67 | 10 | +2.83 [-4.55, +10.79] | +0.49 [-6.73, +8.26] | +8.76 [+0.95, +17.18] * | +5.33 [-2.24, +13.47] |
| 1 % low fps | 6.88 | 5.01 | 8.22 | 10 | -2.54 [-11.03, +6.77] | -0.39 [-9.07, +9.12] | -8.08 [-16.10, +0.69] | -6.27 [-14.44, +2.68] |

| metric | s0 median delta | d11 median delta | d11t median delta | d11p median delta |
|---|---|---|---|---|
| fps | -2.36 (within) | -0.96 (within) | -2.58 (within) | -1.90 (within) |
| median ms | +2.35 (within) | +2.50 (within) | +2.70 (within) | +2.07 (within) |
| p99 ms | -0.35 (within) | -0.51 (within) | +3.22 (within) | +2.15 (within) |
| 1 % low fps | -0.76 (within) | +0.53 (within) | -3.24 (within) | -3.18 (within) |

### B-block T-std (ln v = arm + round; df = runs - arms - rounds + 1)

GM delta vs base in %, [95 % CI], `*` = the CI excludes 0. Then the median delta (verdict against the band).

| metric | base band % | CV % | 4v4 % | df | s0 (n=3) | d11 (n=3) | d11t (n=3) | d11p (n=3) | round terms % (r2, r3) |
|---|---|---|---|---|---|---|---|---|---|
| fps | 5.05 | 1.99 | 3.31 | 8 | -1.36 [-5.00, +2.41] | -0.78 [-4.44, +3.01] | -2.56 [-6.15, +1.17] | -1.62 [-5.25, +2.14] | -0.72, -0.48 |
| median ms | 5.73 | 2.27 | 3.77 | 8 | +1.09 [-3.15, +5.50] | +1.25 [-2.99, +5.67] | +2.40 [-1.88, +6.88] | +1.49 [-2.76, +5.92] | +0.77, -0.17 |
| p99 ms | 4.12 | 3.36 | 5.63 | 8 | +2.83 [-3.47, +9.55] | +0.49 [-5.67, +7.04] | +8.76 [+2.10, +15.86] * | +5.33 [-1.13, +12.20] | +3.11, +5.72 |
| 1 % low fps | 3.47 | 3.63 | 6.10 | 8 | -2.54 [-8.98, +4.36] | -0.39 [-6.97, +6.66] | -8.08 [-14.16, -1.58] * | -6.27 [-12.47, +0.36] | -3.14, -7.32 |

| metric | s0 median delta | d11 median delta | d11t median delta | d11p median delta |
|---|---|---|---|---|
| fps | -2.12 (within) | -1.20 (within) | -3.04 (within) | -2.26 (within) |
| median ms | +1.40 (within) | +1.75 (within) | +2.53 (within) | +1.94 (within) |
| p99 ms | +4.76 (worse) | +1.20 (within) | +9.12 (worse) | +6.22 (worse) |
| 1 % low fps | -3.57 (worse) | -0.94 (within) | -8.70 (worse) | -6.93 (worse) |

### Paired T-std, per round vs base

| metric | arm | deltas % by round | median | mean +- hw95 | range pp | up |
|---|---|---|---|---|---|---|
| fps | s0 | r1 -5.08, r2 +0.91, r3 +0.20 | +0.20 | -1.33 +- 8.13 | 5.99 | 2/3 |
| fps | d11 | r1 -3.42, r2 +1.86, r3 -0.72 | -0.72 | -0.76 +- 6.55 | 5.27 | 1/3 |
| fps | d11t | r1 -4.99, r2 +2.64, r3 -5.13 | -4.99 | -2.49 +- 11.05 | 7.77 | 1/3 |
| fps | d11p | r1 -4.33, r2 +1.82, r3 -2.26 | -2.26 | -1.59 +- 7.77 | 6.15 | 1/3 |
| median ms | s0 | r1 +5.73, r2 -1.76, r3 -0.55 | -0.55 | +1.14 +- 9.99 | 7.49 | 1/3 |
| median ms | d11 | r1 +4.97, r2 -1.43, r3 +0.31 | +0.31 | +1.28 +- 8.21 | 6.39 | 2/3 |
| median ms | d11t | r1 +5.17, r2 -3.30, r3 +5.59 | +5.17 | +2.49 +- 12.47 | 8.90 | 2/3 |
| median ms | d11p | r1 +4.57, r2 -2.03, r3 +2.03 | +2.03 | +1.52 +- 8.27 | 6.60 | 2/3 |
| p99 ms | s0 | r1 +5.48, r2 +3.45, r3 -0.35 | +3.45 | +2.86 +- 7.35 | 5.82 | 2/3 |
| p99 ms | d11 | r1 +1.67, r2 -1.38, r3 +1.20 | +1.20 | +0.49 +- 4.08 | 3.05 | 2/3 |
| p99 ms | d11t | r1 +9.87, r2 +1.32, r3 +15.59 | +9.87 | +8.92 +- 17.84 | 14.27 | 3/3 |
| p99 ms | d11p | r1 +8.73, r2 +1.16, r3 +6.22 | +6.22 | +5.37 +- 9.59 | 7.57 | 3/3 |
| 1 % low fps | s0 | r1 -3.57, r2 -4.14, r3 +0.15 | -3.57 | -2.52 +- 5.78 | 4.28 | 1/3 |
| 1 % low fps | d11 | r1 +0.13, r2 +0.53, r3 -1.82 | +0.13 | -0.38 +- 3.13 | 2.35 | 2/3 |
| 1 % low fps | d11t | r1 -8.70, r2 -0.75, r3 -14.30 | -8.70 | -7.92 +- 16.91 | 13.55 | 0/3 |
| 1 % low fps | d11p | r1 -7.81, r2 -3.18, r3 -7.75 | -7.75 | -6.25 +- 6.59 | 4.62 | 0/3 |

### Light share (frames < 4.5 ms) per arm

- Means: base 0.86986, s0 0.86650, d11 0.89999, d11t 0.85499, d11p 0.89676.
- One-way F = 0.3329 on (4, 10), p = 0.850 (scipy f_oneway F = 0.3329).

### W5 sensitivity: d11t without 1821-d11t-r3 (n = 2, descriptive)

The T-std values use the 15-run hT_ref. The one-way CI pools the SD over all arms (df 9 without r3); B-block without r3 has df 7. These are descriptive only.

| d11t vs | metric | full n=3: GM [CI] (df 10) | full: median delta | without r3 n=2: GM [CI] (df 9) | without r3: median delta | B-block full (df 8) | B-block without r3 (df 7) | without r3, hT_ref(14) = 0.2102: GM |
|---|---|---|---|---|---|---|---|---|
| base | fps | -2.56 [-5.74, +0.72] | -2.58 | -1.38 [-4.68, +2.04] | -1.63 | -2.56 [-6.15, +1.17] | -1.13 [-4.89, +2.79] | -1.37 |
| base | median ms | +2.40 [-1.42, +6.37] | +2.70 | +1.13 [-2.87, +5.30] | +1.72 | +2.40 [-1.88, +6.88] | +0.59 [-3.60, +4.96] | +1.22 |
| base | p99 ms | +8.76 [+0.95, +17.18] * | +3.22 | +4.57 [-1.48, +10.99] | +2.72 | +8.76 [+2.10, +15.86] * | +5.30 [-0.12, +11.00] | +4.59 |
| base | 1 % low fps | -8.08 [-16.10, +0.69] | -3.24 | -3.59 [-10.44, +3.78] | -2.00 | -8.08 [-14.16, -1.58] * | -4.85 [-10.20, +0.83] | -3.60 |
| d11 | fps | -1.79 [-4.99, +1.52] | -1.63 | -0.60 [-3.92, +2.84] | -0.68 | -1.79 [-5.41, +1.97] | -0.35 [-4.14, +3.60] | -0.59 |
| d11 | median ms | +1.14 [-2.64, +5.06] | +0.19 | -0.11 [-4.07, +4.00] | -0.76 | +1.14 [-3.09, +5.56] | -0.65 [-4.79, +3.67] | -0.11 |
| d11 | p99 ms | +8.24 [+0.47, +16.61] * | +3.74 | +4.06 [-1.96, +10.45] | +3.24 | +8.24 [+1.61, +15.30] * | +4.79 [-0.60, +10.47] | +4.06 |
| d11 | 1 % low fps | -7.73 [-15.77, +1.08] | -3.76 | -3.22 [-10.09, +4.19] | -2.52 | -7.73 [-13.82, -1.20] * | -4.48 [-9.85, +1.22] | -3.22 |

Per-round paired T-std deltas, in % (+ = higher value: worse for p99 and p50, better for 1 % low and fps). The d11p rows are added for comparison:

| arm vs ref | metric | r1 | r2 | r3 | median | mean | up |
|---|---|---|---|---|---|---|---|
| d11t vs d11 | p99 ms | +8.06 | +2.74 | +14.22 | +8.06 | +8.34 | 3/3 |
| d11t vs d11 | 1 % low fps | -8.82 | -1.28 | -12.71 | -8.82 | -7.61 | 0/3 |
| d11t vs d11 | median ms | +0.19 | -1.90 | +5.27 | +0.19 | +1.18 | 2/3 |
| d11t vs d11 | fps | -1.63 | +0.77 | -4.45 | -1.63 | -1.77 | 1/3 |
| d11t vs base | p99 ms | +9.87 | +1.32 | +15.59 | +9.87 | +8.92 | 3/3 |
| d11t vs base | 1 % low fps | -8.70 | -0.75 | -14.30 | -8.70 | -7.92 | 0/3 |
| d11t vs base | median ms | +5.17 | -3.30 | +5.59 | +5.17 | +2.49 | 2/3 |
| d11t vs base | fps | -4.99 | +2.64 | -5.13 | -4.99 | -2.49 | 1/3 |
| d11p vs d11 | p99 ms | +6.95 | +2.58 | +4.97 | +4.97 | +4.83 | 3/3 |
| d11p vs d11 | 1 % low fps | -7.93 | -3.70 | -6.04 | -6.04 | -5.89 | 0/3 |
| d11p vs d11 | median ms | -0.38 | -0.61 | +1.72 | -0.38 | +0.24 | 1/3 |
| d11p vs d11 | fps | -0.95 | -0.04 | -1.55 | -0.95 | -0.85 | 0/3 |
| d11p vs base | p99 ms | +8.73 | +1.16 | +6.22 | +6.22 | +5.37 | 3/3 |
| d11p vs base | 1 % low fps | -7.81 | -3.18 | -7.75 | -7.75 | -6.25 | 0/3 |
| d11p vs base | median ms | +4.57 | -2.03 | +2.03 | +2.03 | +1.52 | 2/3 |
| d11p vs base | fps | -4.33 | +1.82 | -2.26 | -2.26 | -1.59 | 1/3 |

T-std p99 ms / 1 % low fps per run: 1757-base-r1 7.064 / 125.7; 1802-d11-r1 7.182 / 125.9; 1804-d11t-r1 7.761 / 114.8; 1810-d11-r2 7.481 / 119.3; 1813-d11t-r2 7.686 / 117.8; 1817-base-r2 7.586 / 118.7; 1819-d11-r3 7.609 / 115.4; 1821-d11t-r3 8.691 / 100.8; 1825-base-r3 7.519 / 117.6.

- T-std p99 ms d11t vs base: t table +8.765 [+0.954, +17.180] *; scipy t(10) = 2.2281 gives [+0.954, +17.180].
- B-block T-std p99 ms d11t vs base: t table +8.765 [+2.100, +15.864] *; scipy t(8) = 2.3060 gives [+2.100, +15.864].
- T-std 1 % low fps d11t vs base: t table -8.085 [-16.096, +0.692]; scipy t(10) = 2.2281 gives [-16.097, +0.692].
- B-block T-std 1 % low fps d11t vs base: t table -8.085 [-14.160, -1.580] *; scipy t(8) = 2.3060 gives [-14.160, -1.580].


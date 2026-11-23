# T-std read-out: W6

- title: Window 6 (Agent 5's draft v2, finalized 2026-11-22 21:16 for build/agent2/devoff4b-bin): upload path on the S4b bin. s0 (every switch OFF) vs p2 = #8 P2, p2f = #8 + #5 fix (i), p2fc = #8 + #5 + #4 C1 v3 keep-watch (verify off); f and fc = the decision table's arms without P2
- dir: `<workspace>\build\agent8\readout\w-followup\pool\W6`
- command: `python -B build\agent7\w4b-noise\readout.py build\agent8\readout\w-followup\pool\W6 --drop 0352-p2f-r5 -o build\agent8\readout\w-followup\a7\W6-pool-no0352.md --json build\agent8\readout\w-followup\a7\W6-pool-no0352.json`
- ref **s0** (matrix.json arm "ref": true); arms p2, p2f, p2fc; rounds 1, 2, 3, 4, 5, 6, 7, 8, 9, 10; kept 39 of 42 runs (s0 10, p2 10, p2f 9, p2fc 10); left out: 0009-cold-s0 (cold (unscored)); 0313-cold-s0 (cold (unscored)); 0352-p2f-r5 (--drop).
- T split: light = frame time < 4.5 ms; hT_ref = 0.058 (the median heavy-time share of the kept runs).
- G11 power: OK: overlay best_performance 42/42; scheme Balanced 42/42; AC 1 42/42; saver 0 42/42; no change inside any window; the overlay is not W5's best_efficiency, so compare arms within this window only, not with W5's absolute numbers
- note: rounds without every arm: 10 (B-block handles this; check the order is round-robin)

## Read-out

- **Primary: B-block T-std.** Round effect on median ms: F = 5.50 on (9, 26), p = < 0.001 < 0.05, so B-block T-std applies (df = runs - arms - rounds + 1); T-std is shown beside it.
- median ms vs s0 (B-block T-std): p2 +0.1 [-2.8, +3.1]; p2f +0.9 [-2.1, +4.1]; p2fc -9.9 [-12.5, -7.2] *.
- fps vs s0 (B-block T-std): p2 -0.3 [-2.7, +2.2]; p2f -1.0 [-3.5, +1.5]; p2fc +17.0 [+14.2, +19.9] *.
- CIs that exclude 0 (B-block T-std): median ms and fps: p2fc median ms -9.9 [-12.5, -7.2] *, p2fc fps +17.0 [+14.2, +19.9] *; tails: p2fc p99 ms +1.7 [+0.8, +2.6] *. That is 12 tests (3 arms x 4 metrics) at 5 %, so about 0.6 can be `*` by chance.
- Guards: (a) light share F = 11.04 on (3, 35), p = < 0.001: WARNING, an arm may move the mix; (b) raw agrees for every arm; (c) 0 of 39 kept runs flagged. G11: OK.

## T-std and B-block T-std

Round terms of B-block T-std vs round 1: median ms: round 2 +14.2 %, round 3 +11.4 %, round 4 +11.7 %, round 5 +12.2 %, round 6 +8.6 %, round 7 +12.2 %, round 8 +11.7 %, round 9 +12.5 %, round 10 +12.5 %; F = 5.50 on (9, 26), p = < 0.001. fps: round 2 -10.5 %, round 3 -8.4 %, round 4 -8.2 %, round 5 -8.9 %, round 6 -6.1 %, round 7 -8.5 %, round 8 -8.4 %, round 9 -9.1 %, round 10 -8.9 %; F = 5.33 on (9, 26), p = < 0.001.

Cells: the GM delta vs s0 in %, with the pooled 95 % CI; `*` = the CI excludes 0. Bold = the primary. s0 band = (max - min) / median of s0's runs (summary.md). 4 vs 4 band = the 95 % half-width for two arms of 4 runs.

| method | metric | s0 band % | pooled CV % | 4 vs 4 band % | df | p2 (n=10) | p2f (n=9) | p2fc (n=10) |
|---|---|---|---|---|---|---|---|---|
| T-std | median ms | 20.1 | 4.7 | 7.0 | 35 | +0.1 [-4.1, +4.5] | +0.7 [-3.6, +5.2] | -9.9 [-13.7, -6.0] * |
| **B-block T-std** | median ms | 7.9 | 3.2 | 4.8 | 26 | +0.1 [-2.8, +3.1] | +0.9 [-2.1, +4.1] | -9.9 [-12.5, -7.2] * |
| T-std | fps | 18.1 | 3.9 | 5.7 | 35 | -0.3 [-3.7, +3.3] | -0.8 [-4.3, +2.8] | +17.0 [+13.0, +21.1] * |
| **B-block T-std** | fps | 6.6 | 2.6 | 3.9 | 26 | -0.3 [-2.7, +2.2] | -1.0 [-3.5, +1.5] | +17.0 [+14.2, +19.9] * |

### Tails (noisier)

| method | metric | s0 band % | pooled CV % | 4 vs 4 band % | df | p2 (n=10) | p2f (n=9) | p2fc (n=10) |
|---|---|---|---|---|---|---|---|---|
| T-std | p99 ms | 3.4 | 0.9 | 1.3 | 35 | -0.5 [-1.3, +0.3] | +0.2 [-0.6, +1.1] | +1.7 [+0.9, +2.6] * |
| **B-block T-std** | p99 ms | 3.1 | 1.0 | 1.4 | 26 | -0.5 [-1.4, +0.4] | +0.2 [-0.7, +1.1] | +1.7 [+0.8, +2.6] * |
| T-std | 1 % low fps | 15.5 | 4.5 | 6.7 | 35 | +2.4 [-1.7, +6.7] | +0.8 [-3.3, +5.1] | -1.3 [-5.2, +2.8] |
| **B-block T-std** | 1 % low fps | 8.7 | 2.8 | 4.2 | 26 | +2.4 [-0.2, +5.1] | +1.0 [-1.7, +3.8] | -1.3 [-3.9, +1.3] |

### Median deltas on median ms (the summary.md form)

Verdicts against each method's own s0 band: B-block T-std p2fc better.

| method | p2 | p2f | p2fc |
|---|---|---|---|
| raw | +0.3 | -0.5 | -12.8 |
| T-std | +0.6 | -0.2 | -12.1 |
| B-block T-std | +0.9 | +0.1 | -11.3 |

## Guards

**(a) Light share** (the share of frames < light_ms) per arm: s0 0.965, p2 0.967, p2f 0.972, p2fc 0.978. One-way F = 11.04 on (3, 35), p = < 0.001. p < 0.05: an arm may move the mix, which T-std hides. Read T-light, T-heavy and the raw rows.

| method | metric | s0 band % | pooled CV % | 4 vs 4 band % | df | p2 (n=10) | p2f (n=9) | p2fc (n=10) |
|---|---|---|---|---|---|---|---|---|
| T-light | median ms | 20.7 | 4.8 | 7.2 | 35 | +0.2 [-4.1, +4.7] | +1.1 [-3.4, +5.8] | -9.8 [-13.7, -5.8] * |
| T-heavy | median ms | 1.6 | 0.6 | 0.9 | 35 | -0.2 [-0.8, +0.3] | +0.2 [-0.4, +0.8] | +2.9 [+2.3, +3.5] * |
| T-light | fps | 18.6 | 4.0 | 5.8 | 35 | -0.3 [-3.8, +3.4] | -0.9 [-4.5, +2.9] | +17.6 [+13.4, +21.9] * |
| T-heavy | fps | 6.6 | 1.9 | 2.8 | 35 | +1.0 [-0.7, +2.8] | +0.2 [-1.6, +2.0] | -2.1 [-3.8, -0.3] * |

**(b) Raw GM deltas** with the pooled 95 % CI. They must not contradict B-block T-std:

| method | metric | s0 band % | pooled CV % | 4 vs 4 band % | df | p2 (n=10) | p2f (n=9) | p2fc (n=10) |
|---|---|---|---|---|---|---|---|---|
| raw | median ms | 21.2 | 4.9 | 7.3 | 35 | -0.0 [-4.4, +4.6] | +0.4 [-4.2, +5.1] | -10.3 [-14.3, -6.2] * |
| raw | fps | 20.3 | 4.3 | 6.3 | 35 | -0.0 [-3.8, +3.9] | -0.2 [-4.1, +3.9] | +18.0 [+13.5, +22.7] * |

Raw CI vs the B-block T-std CI (overlap = agrees): median ms: p2 agrees, p2f agrees, p2fc agrees; fps: p2 agrees, p2f agrees, p2fc agrees.

**(c) Host flag** (sys.json window P util >= 90 % and E-core MHz < 600): 0 of 39 kept runs.

## Runs

| seq | round | arm | run | kept | raw median ms | T-std median ms | raw fps | T-std fps | light share | P util % | E MHz | flag | overlay |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | s0 | 0009-cold-s0 | no: cold (unscored) | 2.367 | 2.345 | 399.4 | 405.4 | 0.958 | 64.6 | 1841 |  | best_performance |
| 2 | 1 | s0 | 0010-s0-r1 | yes | 2.079 | 2.096 | 446.1 | 441.1 | 0.983 | 64.3 | 2006 |  | best_performance |
| 3 | 1 | p2 | 0012-p2-r1 | yes | 2.047 | 2.054 | 441.7 | 439.4 | 0.978 | 66.4 | 2021 |  | best_performance |
| 4 | 1 | p2f | 0014-p2f-r1 | yes | 2.197 | 2.210 | 425.7 | 421.2 | 0.982 | 65.3 | 1986 |  | best_performance |
| 5 | 1 | p2fc | 0016-p2fc-r1 | yes | 2.135 | 2.146 | 473.1 | 468.9 | 0.982 | 67.0 | 2112 |  | best_performance |
| 6 | 2 | p2 | 0019-p2-r2 | yes | 2.350 | 2.353 | 402.3 | 401.4 | 0.973 | 63.9 | 2005 |  | best_performance |
| 7 | 2 | p2f | 0021-p2f-r2 | yes | 2.463 | 2.468 | 387.8 | 386.4 | 0.973 | 62.8 | 1983 |  | best_performance |
| 8 | 2 | p2fc | 0023-p2fc-r2 | yes | 2.307 | 2.306 | 426.9 | 427.3 | 0.973 | 63.4 | 1852 |  | best_performance |
| 9 | 2 | s0 | 0025-s0-r2 | yes | 2.602 | 2.589 | 368.1 | 371.2 | 0.958 | 62.9 | 1778 |  | best_performance |
| 10 | 3 | p2f | 0027-p2f-r3 | yes | 2.436 | 2.438 | 387.7 | 387.4 | 0.971 | 64.1 | 2012 |  | best_performance |
| 11 | 3 | p2fc | 0029-p2fc-r3 | yes | 2.139 | 2.144 | 466.3 | 464.3 | 0.978 | 65.6 | 2084 |  | best_performance |
| 12 | 3 | s0 | 0031-s0-r3 | yes | 2.445 | 2.435 | 384.9 | 388.3 | 0.961 | 65.6 | 1978 |  | best_performance |
| 13 | 3 | p2 | 0033-p2-r3 | yes | 2.472 | 2.470 | 385.0 | 385.8 | 0.967 | 63.3 | 1958 |  | best_performance |
| 14 | 4 | p2fc | 0035-p2fc-r4 | yes | 2.157 | 2.165 | 471.2 | 467.9 | 0.980 | 64.2 | 2075 |  | best_performance |
| 15 | 4 | s0 | 0037-s0-r4 | yes | 2.429 | 2.406 | 385.2 | 391.6 | 0.954 | 67.5 | 1978 |  | best_performance |
| 16 | 4 | p2 | 0039-p2-r4 | yes | 2.488 | 2.484 | 381.9 | 383.3 | 0.965 | 63.8 | 1926 |  | best_performance |
| 17 | 4 | p2f | 0041-p2f-r4 | yes | 2.454 | 2.454 | 386.8 | 386.8 | 0.969 | 64.1 | 1967 |  | best_performance |
| 18 | 5 | s0 | 0043-s0-r5 | yes | 2.457 | 2.447 | 385.2 | 387.6 | 0.962 | 63.8 | 1986 |  | best_performance |
| 19 | 5 | p2 | 0045-p2-r5 | yes | 2.471 | 2.465 | 385.6 | 387.1 | 0.965 | 62.9 | 1984 |  | best_performance |
| 20 | 5 | p2f | 0047-p2f-r5 | yes | 2.455 | 2.455 | 386.8 | 386.8 | 0.970 | 62.7 | 1972 |  | best_performance |
| 21 | 5 | p2fc | 0049-p2fc-r5 | yes | 2.178 | 2.182 | 457.2 | 455.2 | 0.978 | 65.7 | 2045 |  | best_performance |
| 22 | 0 | s0 | 0313-cold-s0 | no: cold (unscored) | 1.986 | 1.982 | 448.3 | 450.3 | 0.972 | 66.7 | 2045 |  | best_performance |
| 23 | 6 | s0 | 0315-s0-r1 | yes | 2.270 | 2.275 | 417.3 | 416.0 | 0.975 | 64.0 | 1983 |  | best_performance |
| 24 | 6 | p2 | 0317-p2-r1 | yes | 2.418 | 2.418 | 394.2 | 394.1 | 0.970 | 64.8 | 1990 |  | best_performance |
| 25 | 6 | p2f | 0319-p2f-r1 | yes | 2.446 | 2.448 | 387.7 | 387.1 | 0.971 | 62.9 | 1996 |  | best_performance |
| 26 | 6 | p2fc | 0321-p2fc-r1 | yes | 2.108 | 2.111 | 471.3 | 469.9 | 0.978 | 65.8 | 2105 |  | best_performance |
| 27 | 7 | p2 | 0323-p2-r2 | yes | 2.469 | 2.469 | 385.6 | 385.6 | 0.969 | 64.2 | 1973 |  | best_performance |
| 28 | 7 | p2f | 0325-p2f-r2 | yes | 2.442 | 2.440 | 385.9 | 386.9 | 0.968 | 63.9 | 1979 |  | best_performance |
| 29 | 7 | p2fc | 0327-p2fc-r2 | yes | 2.175 | 2.178 | 470.3 | 468.3 | 0.979 | 65.0 | 2084 |  | best_performance |
| 30 | 7 | s0 | 0329-s0-r2 | yes | 2.476 | 2.464 | 381.9 | 384.8 | 0.964 | 64.9 | 1971 |  | best_performance |
| 31 | 8 | p2f | 0331-p2f-r3 | yes | 2.449 | 2.448 | 385.9 | 386.5 | 0.969 | 64.1 | 1976 |  | best_performance |
| 32 | 8 | p2fc | 0333-p2fc-r3 | yes | 2.129 | 2.131 | 468.1 | 467.2 | 0.977 | 66.1 | 2094 |  | best_performance |
| 33 | 8 | s0 | 0335-s0-r3 | yes | 2.467 | 2.457 | 383.7 | 386.4 | 0.964 | 62.7 | 1961 |  | best_performance |
| 34 | 8 | p2 | 0337-p2-r3 | yes | 2.486 | 2.477 | 383.9 | 386.2 | 0.964 | 62.5 | 1965 |  | best_performance |
| 35 | 9 | p2fc | 0339-p2fc-r4 | yes | 2.195 | 2.195 | 451.5 | 451.8 | 0.975 | 65.5 | 2008 |  | best_performance |
| 36 | 9 | s0 | 0341-s0-r4 | yes | 2.476 | 2.469 | 385.0 | 386.6 | 0.965 | 64.3 | 1951 |  | best_performance |
| 37 | 9 | p2 | 0343-p2-r4 | yes | 2.448 | 2.438 | 385.2 | 387.8 | 0.962 | 64.8 | 1978 |  | best_performance |
| 38 | 9 | p2f | 0345-p2f-r4 | yes | 2.472 | 2.476 | 386.5 | 385.3 | 0.973 | 62.8 | 1962 |  | best_performance |
| 39 | 10 | s0 | 0348-s0-r5 | yes | 2.477 | 2.470 | 385.6 | 387.3 | 0.965 | 63.3 | 1991 |  | best_performance |
| 40 | 10 | p2 | 0350-p2-r5 | yes | 2.527 | 2.510 | 375.5 | 379.2 | 0.958 | 64.1 | 1934 |  | best_performance |
| 41 | 10 | p2f | 0352-p2f-r5 | no: --drop | 2.443 | 2.438 | 385.1 | 386.7 | 0.968 | 64.2 | 1974 |  | best_performance |
| 42 | 10 | p2fc | 0354-p2fc-r5 | yes | 2.128 | 2.137 | 469.8 | 465.7 | 0.982 | 66.1 | 2080 |  | best_performance |


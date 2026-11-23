# T-std read-out: W6

- title: Window 6 (Agent 5's draft v2, finalized 2026-11-22 21:16 for build/agent2/devoff4b-bin): upload path on the S4b bin. s0 (every switch OFF) vs p2 = #8 P2, p2f = #8 + #5 fix (i), p2fc = #8 + #5 + #4 C1 v3 keep-watch (verify off); f and fc = the decision table's arms without P2
- dir: `<workspace>\build\agent8\readout\w-followup\pool\W6`
- command: `python -B build\agent7\w4b-noise\readout.py build\agent8\readout\w-followup\pool\W6 --rounds 2,3,4,5,7,8,9,10 -o build\agent8\readout\w-followup\a7\W6-pool-noR1.md --json build\agent8\readout\w-followup\a7\W6-pool-noR1.json`
- ref **s0** (matrix.json arm "ref": true); arms p2, p2f, p2fc; rounds 2, 3, 4, 5, 7, 8, 9, 10; kept 32 of 42 runs (s0 8, p2 8, p2f 8, p2fc 8); left out: 0009-cold-s0 (cold (unscored)); 0010-s0-r1 (round 1 not in --rounds); 0012-p2-r1 (round 1 not in --rounds); 0014-p2f-r1 (round 1 not in --rounds); 0016-p2fc-r1 (round 1 not in --rounds); 0313-cold-s0 (cold (unscored)); 0315-s0-r1 (round 6 not in --rounds); 0317-p2-r1 (round 6 not in --rounds); 0319-p2f-r1 (round 6 not in --rounds); 0321-p2fc-r1 (round 6 not in --rounds).
- T split: light = frame time < 4.5 ms; hT_ref = 0.061 (the median heavy-time share of the kept runs).
- G11 power: OK: overlay best_performance 42/42; scheme Balanced 42/42; AC 1 42/42; saver 0 42/42; no change inside any window; the overlay is not W5's best_efficiency, so compare arms within this window only, not with W5's absolute numbers

## Read-out

- **Primary: T-std.** No round effect on median ms: F = 0.55 on (7, 21), p = 0.789 >= 0.05, so T-std applies (df = runs - arms); B-block T-std is shown beside it.
- median ms vs s0 (T-std): p2 -0.4 [-2.3, +1.6]; p2f -0.6 [-2.6, +1.4]; p2fc -11.7 [-13.4, -9.9] *.
- fps vs s0 (T-std): p2 +0.4 [-1.6, +2.4]; p2f +0.3 [-1.7, +2.3]; p2fc +18.9 [+16.5, +21.3] *.
- CIs that exclude 0 (T-std): median ms and fps: p2fc median ms -11.7 [-13.4, -9.9] *, p2fc fps +18.9 [+16.5, +21.3] *; tails: p2fc p99 ms +1.4 [+0.5, +2.4] *. That is 12 tests (3 arms x 4 metrics) at 5 %, so about 0.6 can be `*` by chance.
- Guards: (a) light share F = 33.52 on (3, 28), p = < 0.001: WARNING, an arm may move the mix; (b) raw agrees for every arm; (c) 0 of 32 kept runs flagged. G11: OK.

## T-std and B-block T-std

Round terms of B-block T-std vs round 2: median ms: round 3 -2.4 %, round 4 -2.2 %, round 5 -1.8 %, round 7 -1.7 %, round 8 -2.2 %, round 9 -1.4 %, round 10 -1.7 %; F = 0.55 on (7, 21), p = 0.789. fps: round 3 +2.3 %, round 4 +2.5 %, round 5 +1.8 %, round 7 +2.2 %, round 8 +2.3 %, round 9 +1.5 %, round 10 +1.8 %; F = 0.60 on (7, 21), p = 0.747.

Cells: the GM delta vs s0 in %, with the pooled 95 % CI; `*` = the CI excludes 0. Bold = the primary. s0 band = (max - min) / median of s0's runs (summary.md). 4 vs 4 band = the 95 % half-width for two arms of 4 runs.

| method | metric | s0 band % | pooled CV % | 4 vs 4 band % | df | p2 (n=8) | p2f (n=8) | p2fc (n=8) |
|---|---|---|---|---|---|---|---|---|
| **T-std** | median ms | 7.5 | 1.9 | 2.9 | 28 | -0.4 [-2.3, +1.6] | -0.6 [-2.6, +1.4] | -11.7 [-13.4, -9.9] * |
| B-block T-std | median ms | 5.2 | 2.1 | 3.1 | 21 | -0.4 [-2.5, +1.8] | -0.6 [-2.7, +1.5] | -11.7 [-13.5, -9.7] * |
| **T-std** | fps | 5.3 | 1.9 | 2.9 | 28 | +0.4 [-1.6, +2.4] | +0.3 [-1.7, +2.3] | +18.9 [+16.5, +21.3] * |
| B-block T-std | fps | 2.8 | 2.0 | 3.1 | 21 | +0.4 [-1.7, +2.6] | +0.3 [-1.8, +2.5] | +18.9 [+16.4, +21.4] * |

### Tails (noisier)

| method | metric | s0 band % | pooled CV % | 4 vs 4 band % | df | p2 (n=8) | p2f (n=8) | p2fc (n=8) |
|---|---|---|---|---|---|---|---|---|
| **T-std** | p99 ms | 2.9 | 0.9 | 1.3 | 28 | -0.5 [-1.5, +0.4] | -0.2 [-1.1, +0.8] | +1.4 [+0.5, +2.4] * |
| B-block T-std | p99 ms | 3.0 | 1.0 | 1.4 | 21 | -0.5 [-1.5, +0.5] | -0.2 [-1.2, +0.8] | +1.4 [+0.4, +2.5] * |
| **T-std** | 1 % low fps | 16.4 | 5.8 | 8.7 | 28 | +3.1 [-2.9, +9.3] | -0.9 [-6.6, +5.1] | -1.0 [-6.7, +5.0] |
| B-block T-std | 1 % low fps | 10.7 | 4.8 | 7.3 | 21 | +3.1 [-1.9, +8.3] | -0.9 [-5.7, +4.1] | -1.0 [-5.8, +4.0] |

### Median deltas on median ms (the summary.md form)

Verdicts against each method's own s0 band: raw p2fc better, T-std p2fc better, B-block T-std p2fc better.

| method | p2 | p2f | p2fc |
|---|---|---|---|
| raw | +0.0 | -0.8 | -12.4 |
| T-std | +0.3 | -0.4 | -11.8 |
| B-block T-std | +0.6 | -0.3 | -11.6 |

## Guards

**(a) Light share** (the share of frames < light_ms) per arm: s0 0.961, p2 0.965, p2f 0.970, p2fc 0.978. One-way F = 33.52 on (3, 28), p = < 0.001. p < 0.05: an arm may move the mix, which T-std hides. Read T-light, T-heavy and the raw rows.

| method | metric | s0 band % | pooled CV % | 4 vs 4 band % | df | p2 (n=8) | p2f (n=8) | p2fc (n=8) |
|---|---|---|---|---|---|---|---|---|
| T-light | median ms | 7.4 | 2.0 | 2.9 | 28 | -0.4 [-2.3, +1.7] | -0.3 [-2.3, +1.7] | -11.7 [-13.5, -9.9] * |
| T-heavy | median ms | 1.6 | 0.6 | 0.9 | 28 | -0.2 [-0.8, +0.4] | +0.2 [-0.4, +0.8] | +2.8 [+2.1, +3.4] * |
| T-light | fps | 5.5 | 2.0 | 2.9 | 28 | +0.4 [-1.7, +2.5] | +0.3 [-1.7, +2.4] | +19.5 [+17.1, +22.0] * |
| T-heavy | fps | 6.7 | 2.4 | 3.5 | 28 | +1.2 [-1.2, +3.7] | -0.5 [-2.9, +1.9] | -2.0 [-4.3, +0.4] |

**(b) Raw GM deltas** with the pooled 95 % CI. They must not contradict T-std:

| method | metric | s0 band % | pooled CV % | 4 vs 4 band % | df | p2 (n=8) | p2f (n=8) | p2fc (n=8) |
|---|---|---|---|---|---|---|---|---|
| raw | median ms | 7.0 | 2.0 | 3.0 | 28 | -0.6 [-2.6, +1.5] | -1.1 [-3.1, +1.0] | -12.2 [-14.0, -10.4] * |
| raw | fps | 4.5 | 2.1 | 3.1 | 28 | +0.8 [-1.3, +3.0] | +1.1 [-1.1, +3.3] | +20.3 [+17.7, +22.9] * |

Raw CI vs the T-std CI (overlap = agrees): median ms: p2 agrees, p2f agrees, p2fc agrees; fps: p2 agrees, p2f agrees, p2fc agrees.

**(c) Host flag** (sys.json window P util >= 90 % and E-core MHz < 600): 0 of 32 kept runs.

## Runs

| seq | round | arm | run | kept | raw median ms | T-std median ms | raw fps | T-std fps | light share | P util % | E MHz | flag | overlay |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | s0 | 0009-cold-s0 | no: cold (unscored) | 2.367 | 2.347 | 399.4 | 404.7 | 0.958 | 64.6 | 1841 |  | best_performance |
| 2 | 1 | s0 | 0010-s0-r1 | no: round 1 not in --rounds | 2.079 | 2.098 | 446.1 | 440.3 | 0.983 | 64.3 | 2006 |  | best_performance |
| 3 | 1 | p2 | 0012-p2-r1 | no: round 1 not in --rounds | 2.047 | 2.056 | 441.7 | 438.6 | 0.978 | 66.4 | 2021 |  | best_performance |
| 4 | 1 | p2f | 0014-p2f-r1 | no: round 1 not in --rounds | 2.197 | 2.212 | 425.7 | 420.4 | 0.982 | 65.3 | 1986 |  | best_performance |
| 5 | 1 | p2fc | 0016-p2fc-r1 | no: round 1 not in --rounds | 2.135 | 2.148 | 473.1 | 468.0 | 0.982 | 67.0 | 2112 |  | best_performance |
| 6 | 2 | p2 | 0019-p2-r2 | yes | 2.350 | 2.355 | 402.3 | 400.7 | 0.973 | 63.9 | 2005 |  | best_performance |
| 7 | 2 | p2f | 0021-p2f-r2 | yes | 2.463 | 2.470 | 387.8 | 385.8 | 0.973 | 62.8 | 1983 |  | best_performance |
| 8 | 2 | p2fc | 0023-p2fc-r2 | yes | 2.307 | 2.308 | 426.9 | 426.5 | 0.973 | 63.4 | 1852 |  | best_performance |
| 9 | 2 | s0 | 0025-s0-r2 | yes | 2.602 | 2.592 | 368.1 | 370.6 | 0.958 | 62.9 | 1778 |  | best_performance |
| 10 | 3 | p2f | 0027-p2f-r3 | yes | 2.436 | 2.439 | 387.7 | 386.7 | 0.971 | 64.1 | 2012 |  | best_performance |
| 11 | 3 | p2fc | 0029-p2fc-r3 | yes | 2.139 | 2.146 | 466.3 | 463.4 | 0.978 | 65.6 | 2084 |  | best_performance |
| 12 | 3 | s0 | 0031-s0-r3 | yes | 2.445 | 2.437 | 384.9 | 387.6 | 0.961 | 65.6 | 1978 |  | best_performance |
| 13 | 3 | p2 | 0033-p2-r3 | yes | 2.472 | 2.472 | 385.0 | 385.1 | 0.967 | 63.3 | 1958 |  | best_performance |
| 14 | 4 | p2fc | 0035-p2fc-r4 | yes | 2.157 | 2.167 | 471.2 | 467.0 | 0.980 | 64.2 | 2075 |  | best_performance |
| 15 | 4 | s0 | 0037-s0-r4 | yes | 2.429 | 2.408 | 385.2 | 390.9 | 0.954 | 67.5 | 1978 |  | best_performance |
| 16 | 4 | p2 | 0039-p2-r4 | yes | 2.488 | 2.485 | 381.9 | 382.7 | 0.965 | 63.8 | 1926 |  | best_performance |
| 17 | 4 | p2f | 0041-p2f-r4 | yes | 2.454 | 2.455 | 386.8 | 386.2 | 0.969 | 64.1 | 1967 |  | best_performance |
| 18 | 5 | s0 | 0043-s0-r5 | yes | 2.457 | 2.449 | 385.2 | 387.0 | 0.962 | 63.8 | 1986 |  | best_performance |
| 19 | 5 | p2 | 0045-p2-r5 | yes | 2.471 | 2.467 | 385.6 | 386.4 | 0.965 | 62.9 | 1984 |  | best_performance |
| 20 | 5 | p2f | 0047-p2f-r5 | yes | 2.455 | 2.457 | 386.8 | 386.1 | 0.970 | 62.7 | 1972 |  | best_performance |
| 21 | 5 | p2fc | 0049-p2fc-r5 | yes | 2.178 | 2.184 | 457.2 | 454.3 | 0.978 | 65.7 | 2045 |  | best_performance |
| 22 | 0 | s0 | 0313-cold-s0 | no: cold (unscored) | 1.986 | 1.984 | 448.3 | 449.4 | 0.972 | 66.7 | 2045 |  | best_performance |
| 23 | 6 | s0 | 0315-s0-r1 | no: round 6 not in --rounds | 2.270 | 2.277 | 417.3 | 415.3 | 0.975 | 64.0 | 1983 |  | best_performance |
| 24 | 6 | p2 | 0317-p2-r1 | no: round 6 not in --rounds | 2.418 | 2.421 | 394.2 | 393.4 | 0.970 | 64.8 | 1990 |  | best_performance |
| 25 | 6 | p2f | 0319-p2f-r1 | no: round 6 not in --rounds | 2.446 | 2.449 | 387.7 | 386.5 | 0.971 | 62.9 | 1996 |  | best_performance |
| 26 | 6 | p2fc | 0321-p2fc-r1 | no: round 6 not in --rounds | 2.108 | 2.113 | 471.3 | 468.9 | 0.978 | 65.8 | 2105 |  | best_performance |
| 27 | 7 | p2 | 0323-p2-r2 | yes | 2.469 | 2.471 | 385.6 | 385.0 | 0.969 | 64.2 | 1973 |  | best_performance |
| 28 | 7 | p2f | 0325-p2f-r2 | yes | 2.442 | 2.442 | 385.9 | 386.2 | 0.968 | 63.9 | 1979 |  | best_performance |
| 29 | 7 | p2fc | 0327-p2fc-r2 | yes | 2.175 | 2.180 | 470.3 | 467.4 | 0.979 | 65.0 | 2084 |  | best_performance |
| 30 | 7 | s0 | 0329-s0-r2 | yes | 2.476 | 2.467 | 381.9 | 384.1 | 0.964 | 64.9 | 1971 |  | best_performance |
| 31 | 8 | p2f | 0331-p2f-r3 | yes | 2.449 | 2.450 | 385.9 | 385.8 | 0.969 | 64.1 | 1976 |  | best_performance |
| 32 | 8 | p2fc | 0333-p2fc-r3 | yes | 2.129 | 2.133 | 468.1 | 466.2 | 0.977 | 66.1 | 2094 |  | best_performance |
| 33 | 8 | s0 | 0335-s0-r3 | yes | 2.467 | 2.460 | 383.7 | 385.7 | 0.964 | 62.7 | 1961 |  | best_performance |
| 34 | 8 | p2 | 0337-p2-r3 | yes | 2.486 | 2.479 | 383.9 | 385.6 | 0.964 | 62.5 | 1965 |  | best_performance |
| 35 | 9 | p2fc | 0339-p2fc-r4 | yes | 2.195 | 2.198 | 451.5 | 450.9 | 0.975 | 65.5 | 2008 |  | best_performance |
| 36 | 9 | s0 | 0341-s0-r4 | yes | 2.476 | 2.472 | 385.0 | 386.0 | 0.965 | 64.3 | 1951 |  | best_performance |
| 37 | 9 | p2 | 0343-p2-r4 | yes | 2.448 | 2.440 | 385.2 | 387.2 | 0.962 | 64.8 | 1978 |  | best_performance |
| 38 | 9 | p2f | 0345-p2f-r4 | yes | 2.472 | 2.478 | 386.5 | 384.7 | 0.973 | 62.8 | 1962 |  | best_performance |
| 39 | 10 | s0 | 0348-s0-r5 | yes | 2.477 | 2.473 | 385.6 | 386.7 | 0.965 | 63.3 | 1991 |  | best_performance |
| 40 | 10 | p2 | 0350-p2-r5 | yes | 2.527 | 2.514 | 375.5 | 378.6 | 0.958 | 64.1 | 1934 |  | best_performance |
| 41 | 10 | p2f | 0352-p2f-r5 | yes | 2.443 | 2.441 | 385.1 | 386.0 | 0.968 | 64.2 | 1974 |  | best_performance |
| 42 | 10 | p2fc | 0354-p2fc-r5 | yes | 2.128 | 2.139 | 469.8 | 464.8 | 0.982 | 66.1 | 2080 |  | best_performance |


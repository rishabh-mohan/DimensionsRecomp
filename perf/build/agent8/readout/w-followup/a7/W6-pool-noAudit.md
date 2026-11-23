# T-std read-out: W6

- title: Window 6 (Agent 5's draft v2, finalized 2026-11-22 21:16 for build/agent2/devoff4b-bin): upload path on the S4b bin. s0 (every switch OFF) vs p2 = #8 P2, p2f = #8 + #5 fix (i), p2fc = #8 + #5 + #4 C1 v3 keep-watch (verify off); f and fc = the decision table's arms without P2
- dir: `<workspace>\build\agent8\readout\w-followup\pool\W6`
- command: `python -B build\agent7\w4b-noise\readout.py build\agent8\readout\w-followup\pool\W6 --drop 0023-p2fc-r2,0025-s0-r2,0339-p2fc-r4,0352-p2f-r5 -o build\agent8\readout\w-followup\a7\W6-pool-noAudit.md --json build\agent8\readout\w-followup\a7\W6-pool-noAudit.json`
- ref **s0** (matrix.json arm "ref": true); arms p2, p2f, p2fc; rounds 1, 2, 3, 4, 5, 6, 7, 8, 9, 10; kept 36 of 42 runs (s0 9, p2 10, p2f 9, p2fc 8); left out: 0009-cold-s0 (cold (unscored)); 0023-p2fc-r2 (--drop); 0025-s0-r2 (--drop); 0313-cold-s0 (cold (unscored)); 0339-p2fc-r4 (--drop); 0352-p2f-r5 (--drop).
- T split: light = frame time < 4.5 ms; hT_ref = 0.057 (the median heavy-time share of the kept runs).
- G11 power: OK: overlay best_performance 42/42; scheme Balanced 42/42; AC 1 42/42; saver 0 42/42; no change inside any window; the overlay is not W5's best_efficiency, so compare arms within this window only, not with W5's absolute numbers
- note: rounds without every arm: 2, 9, 10 (B-block handles this; check the order is round-robin)

## Read-out

- **Primary: B-block T-std.** Round effect on median ms: F = 5.62 on (9, 23), p = < 0.001 < 0.05, so B-block T-std applies (df = runs - arms - rounds + 1); T-std is shown beside it.
- median ms vs s0 (B-block T-std): p2 +1.0 [-1.9, +4.0]; p2f +1.9 [-1.2, +5.0]; p2fc -9.8 [-12.5, -6.9] *.
- fps vs s0 (B-block T-std): p2 -1.0 [-3.2, +1.2]; p2f -1.8 [-4.0, +0.5]; p2fc +17.4 [+14.7, +20.1] *.
- CIs that exclude 0 (B-block T-std): median ms and fps: p2fc median ms -9.8 [-12.5, -6.9] *, p2fc fps +17.4 [+14.7, +20.1] *; tails: p2fc p99 ms +1.4 [+0.5, +2.4] *. That is 12 tests (3 arms x 4 metrics) at 5 %, so about 0.6 can be `*` by chance.
- Guards: (a) light share F = 10.31 on (3, 32), p = < 0.001: WARNING, an arm may move the mix; (b) raw agrees for every arm; (c) 0 of 36 kept runs flagged. G11: OK.

## T-std and B-block T-std

Round terms of B-block T-std vs round 1: median ms: round 2 +9.7 %, round 3 +11.4 %, round 4 +11.6 %, round 5 +12.2 %, round 6 +8.6 %, round 7 +12.2 %, round 8 +11.6 %, round 9 +12.6 %, round 10 +12.7 %; F = 5.62 on (9, 23), p = < 0.001. fps: round 2 -6.7 %, round 3 -8.4 %, round 4 -8.2 %, round 5 -8.9 %, round 6 -6.1 %, round 7 -8.5 %, round 8 -8.4 %, round 9 -8.8 %, round 10 -9.1 %; F = 6.21 on (9, 23), p = < 0.001.

Cells: the GM delta vs s0 in %, with the pooled 95 % CI; `*` = the CI excludes 0. Bold = the primary. s0 band = (max - min) / median of s0's runs (summary.md). 4 vs 4 band = the 95 % half-width for two arms of 4 runs.

| method | metric | s0 band % | pooled CV % | 4 vs 4 band % | df | p2 (n=10) | p2f (n=9) | p2fc (n=8) |
|---|---|---|---|---|---|---|---|---|
| T-std | median ms | 15.3 | 4.6 | 6.8 | 32 | +0.9 [-3.3, +5.3] | +1.6 [-2.8, +6.1] | -10.0 [-14.0, -5.9] * |
| **B-block T-std** | median ms | 4.8 | 3.0 | 4.5 | 23 | +1.0 [-1.9, +4.0] | +1.9 [-1.2, +5.0] | -9.8 [-12.5, -6.9] * |
| T-std | fps | 14.5 | 3.6 | 5.3 | 32 | -0.9 [-4.2, +2.5] | -1.5 [-4.8, +2.0] | +17.6 [+13.5, +21.8] * |
| **B-block T-std** | fps | 5.3 | 2.3 | 3.4 | 23 | -1.0 [-3.2, +1.2] | -1.8 [-4.0, +0.5] | +17.4 [+14.7, +20.1] * |

### Tails (noisier)

| method | metric | s0 band % | pooled CV % | 4 vs 4 band % | df | p2 (n=10) | p2f (n=9) | p2fc (n=8) |
|---|---|---|---|---|---|---|---|---|
| T-std | p99 ms | 3.2 | 0.8 | 1.2 | 32 | -0.4 [-1.2, +0.4] | +0.3 [-0.5, +1.1] | +1.5 [+0.6, +2.4] * |
| **B-block T-std** | p99 ms | 3.0 | 0.9 | 1.3 | 23 | -0.4 [-1.3, +0.5] | +0.3 [-0.6, +1.2] | +1.4 [+0.5, +2.4] * |
| T-std | 1 % low fps | 15.4 | 4.6 | 6.8 | 32 | +2.6 [-1.7, +7.1] | +1.0 [-3.3, +5.5] | -0.3 [-4.7, +4.3] |
| **B-block T-std** | 1 % low fps | 7.0 | 2.5 | 3.8 | 23 | +2.4 [-0.1, +5.0] | +1.0 [-1.6, +3.6] | +0.1 [-2.5, +2.7] |

### Median deltas on median ms (the summary.md form)

Verdicts against each method's own s0 band: B-block T-std p2fc better.

| method | p2 | p2f | p2fc |
|---|---|---|---|
| raw | +0.5 | -0.3 | -13.0 |
| T-std | +0.8 | +0.0 | -12.3 |
| B-block T-std | +1.0 | +0.5 | -11.2 |

## Guards

**(a) Light share** (the share of frames < light_ms) per arm: s0 0.966, p2 0.967, p2f 0.972, p2fc 0.979. One-way F = 10.31 on (3, 32), p = < 0.001. p < 0.05: an arm may move the mix, which T-std hides. Read T-light, T-heavy and the raw rows.

| method | metric | s0 band % | pooled CV % | 4 vs 4 band % | df | p2 (n=10) | p2f (n=9) | p2fc (n=8) |
|---|---|---|---|---|---|---|---|---|
| T-light | median ms | 16.0 | 4.7 | 7.0 | 32 | +1.0 [-3.3, +5.6] | +1.9 [-2.6, +6.7] | -10.0 [-14.1, -5.7] * |
| T-heavy | median ms | 1.6 | 0.6 | 0.9 | 32 | -0.2 [-0.8, +0.4] | +0.3 [-0.3, +0.9] | +2.8 [+2.2, +3.5] * |
| T-light | fps | 14.8 | 3.7 | 5.4 | 32 | -1.0 [-4.3, +2.5] | -1.5 [-5.0, +2.0] | +18.2 [+13.9, +22.5] * |
| T-heavy | fps | 6.6 | 2.0 | 2.9 | 32 | +1.1 [-0.7, +3.0] | +0.3 [-1.6, +2.2] | -1.7 [-3.6, +0.3] |

**(b) Raw GM deltas** with the pooled 95 % CI. They must not contradict B-block T-std:

| method | metric | s0 band % | pooled CV % | 4 vs 4 band % | df | p2 (n=10) | p2f (n=9) | p2fc (n=8) |
|---|---|---|---|---|---|---|---|---|
| raw | median ms | 16.2 | 4.8 | 7.2 | 32 | +0.8 [-3.6, +5.5] | +1.2 [-3.4, +6.0] | -10.5 [-14.6, -6.1] * |
| raw | fps | 16.6 | 4.0 | 5.9 | 32 | -0.7 [-4.3, +3.1] | -0.9 [-4.6, +3.0] | +18.7 [+14.1, +23.5] * |

Raw CI vs the B-block T-std CI (overlap = agrees): median ms: p2 agrees, p2f agrees, p2fc agrees; fps: p2 agrees, p2f agrees, p2fc agrees.

**(c) Host flag** (sys.json window P util >= 90 % and E-core MHz < 600): 0 of 36 kept runs.

## Runs

| seq | round | arm | run | kept | raw median ms | T-std median ms | raw fps | T-std fps | light share | P util % | E MHz | flag | overlay |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | s0 | 0009-cold-s0 | no: cold (unscored) | 2.367 | 2.345 | 399.4 | 405.5 | 0.958 | 64.6 | 1841 |  | best_performance |
| 2 | 1 | s0 | 0010-s0-r1 | yes | 2.079 | 2.096 | 446.1 | 441.3 | 0.983 | 64.3 | 2006 |  | best_performance |
| 3 | 1 | p2 | 0012-p2-r1 | yes | 2.047 | 2.054 | 441.7 | 439.6 | 0.978 | 66.4 | 2021 |  | best_performance |
| 4 | 1 | p2f | 0014-p2f-r1 | yes | 2.197 | 2.210 | 425.7 | 421.3 | 0.982 | 65.3 | 1986 |  | best_performance |
| 5 | 1 | p2fc | 0016-p2fc-r1 | yes | 2.135 | 2.146 | 473.1 | 469.0 | 0.982 | 67.0 | 2112 |  | best_performance |
| 6 | 2 | p2 | 0019-p2-r2 | yes | 2.350 | 2.352 | 402.3 | 401.5 | 0.973 | 63.9 | 2005 |  | best_performance |
| 7 | 2 | p2f | 0021-p2f-r2 | yes | 2.463 | 2.468 | 387.8 | 386.5 | 0.973 | 62.8 | 1983 |  | best_performance |
| 8 | 2 | p2fc | 0023-p2fc-r2 | no: --drop | 2.307 | 2.305 | 426.9 | 427.4 | 0.973 | 63.4 | 1852 |  | best_performance |
| 9 | 2 | s0 | 0025-s0-r2 | no: --drop | 2.602 | 2.589 | 368.1 | 371.3 | 0.958 | 62.9 | 1778 |  | best_performance |
| 10 | 3 | p2f | 0027-p2f-r3 | yes | 2.436 | 2.437 | 387.7 | 387.5 | 0.971 | 64.1 | 2012 |  | best_performance |
| 11 | 3 | p2fc | 0029-p2fc-r3 | yes | 2.139 | 2.144 | 466.3 | 464.4 | 0.978 | 65.6 | 2084 |  | best_performance |
| 12 | 3 | s0 | 0031-s0-r3 | yes | 2.445 | 2.435 | 384.9 | 388.4 | 0.961 | 65.6 | 1978 |  | best_performance |
| 13 | 3 | p2 | 0033-p2-r3 | yes | 2.472 | 2.470 | 385.0 | 385.9 | 0.967 | 63.3 | 1958 |  | best_performance |
| 14 | 4 | p2fc | 0035-p2fc-r4 | yes | 2.157 | 2.165 | 471.2 | 468.1 | 0.980 | 64.2 | 2075 |  | best_performance |
| 15 | 4 | s0 | 0037-s0-r4 | yes | 2.429 | 2.406 | 385.2 | 391.7 | 0.954 | 67.5 | 1978 |  | best_performance |
| 16 | 4 | p2 | 0039-p2-r4 | yes | 2.488 | 2.483 | 381.9 | 383.4 | 0.965 | 63.8 | 1926 |  | best_performance |
| 17 | 4 | p2f | 0041-p2f-r4 | yes | 2.454 | 2.453 | 386.8 | 387.0 | 0.969 | 64.1 | 1967 |  | best_performance |
| 18 | 5 | s0 | 0043-s0-r5 | yes | 2.457 | 2.447 | 385.2 | 387.7 | 0.962 | 63.8 | 1986 |  | best_performance |
| 19 | 5 | p2 | 0045-p2-r5 | yes | 2.471 | 2.465 | 385.6 | 387.2 | 0.965 | 62.9 | 1984 |  | best_performance |
| 20 | 5 | p2f | 0047-p2f-r5 | yes | 2.455 | 2.455 | 386.8 | 386.9 | 0.970 | 62.7 | 1972 |  | best_performance |
| 21 | 5 | p2fc | 0049-p2fc-r5 | yes | 2.178 | 2.182 | 457.2 | 455.3 | 0.978 | 65.7 | 2045 |  | best_performance |
| 22 | 0 | s0 | 0313-cold-s0 | no: cold (unscored) | 1.986 | 1.982 | 448.3 | 450.5 | 0.972 | 66.7 | 2045 |  | best_performance |
| 23 | 6 | s0 | 0315-s0-r1 | yes | 2.270 | 2.275 | 417.3 | 416.1 | 0.975 | 64.0 | 1983 |  | best_performance |
| 24 | 6 | p2 | 0317-p2-r1 | yes | 2.418 | 2.418 | 394.2 | 394.2 | 0.970 | 64.8 | 1990 |  | best_performance |
| 25 | 6 | p2f | 0319-p2f-r1 | yes | 2.446 | 2.448 | 387.7 | 387.2 | 0.971 | 62.9 | 1996 |  | best_performance |
| 26 | 6 | p2fc | 0321-p2fc-r1 | yes | 2.108 | 2.110 | 471.3 | 470.0 | 0.978 | 65.8 | 2105 |  | best_performance |
| 27 | 7 | p2 | 0323-p2-r2 | yes | 2.469 | 2.468 | 385.6 | 385.7 | 0.969 | 64.2 | 1973 |  | best_performance |
| 28 | 7 | p2f | 0325-p2f-r2 | yes | 2.442 | 2.440 | 385.9 | 387.0 | 0.968 | 63.9 | 1979 |  | best_performance |
| 29 | 7 | p2fc | 0327-p2fc-r2 | yes | 2.175 | 2.178 | 470.3 | 468.5 | 0.979 | 65.0 | 2084 |  | best_performance |
| 30 | 7 | s0 | 0329-s0-r2 | yes | 2.476 | 2.464 | 381.9 | 384.9 | 0.964 | 64.9 | 1971 |  | best_performance |
| 31 | 8 | p2f | 0331-p2f-r3 | yes | 2.449 | 2.448 | 385.9 | 386.6 | 0.969 | 64.1 | 1976 |  | best_performance |
| 32 | 8 | p2fc | 0333-p2fc-r3 | yes | 2.129 | 2.130 | 468.1 | 467.4 | 0.977 | 66.1 | 2094 |  | best_performance |
| 33 | 8 | s0 | 0335-s0-r3 | yes | 2.467 | 2.456 | 383.7 | 386.5 | 0.964 | 62.7 | 1961 |  | best_performance |
| 34 | 8 | p2 | 0337-p2-r3 | yes | 2.486 | 2.477 | 383.9 | 386.3 | 0.964 | 62.5 | 1965 |  | best_performance |
| 35 | 9 | p2fc | 0339-p2fc-r4 | no: --drop | 2.195 | 2.195 | 451.5 | 451.9 | 0.975 | 65.5 | 2008 |  | best_performance |
| 36 | 9 | s0 | 0341-s0-r4 | yes | 2.476 | 2.469 | 385.0 | 386.7 | 0.965 | 64.3 | 1951 |  | best_performance |
| 37 | 9 | p2 | 0343-p2-r4 | yes | 2.448 | 2.438 | 385.2 | 387.9 | 0.962 | 64.8 | 1978 |  | best_performance |
| 38 | 9 | p2f | 0345-p2f-r4 | yes | 2.472 | 2.476 | 386.5 | 385.4 | 0.973 | 62.8 | 1962 |  | best_performance |
| 39 | 10 | s0 | 0348-s0-r5 | yes | 2.477 | 2.470 | 385.6 | 387.4 | 0.965 | 63.3 | 1991 |  | best_performance |
| 40 | 10 | p2 | 0350-p2-r5 | yes | 2.527 | 2.510 | 375.5 | 379.3 | 0.958 | 64.1 | 1934 |  | best_performance |
| 41 | 10 | p2f | 0352-p2f-r5 | no: --drop | 2.443 | 2.438 | 385.1 | 386.8 | 0.968 | 64.2 | 1974 |  | best_performance |
| 42 | 10 | p2fc | 0354-p2fc-r5 | yes | 2.128 | 2.137 | 469.8 | 465.9 | 0.982 | 66.1 | 2080 |  | best_performance |


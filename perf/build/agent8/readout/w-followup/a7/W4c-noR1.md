# T-std read-out: 20261123-0239

- title: Window 4c (Agent 8, run-2 task #7 follow-up): codegen B repeat. B = devoffB (S2 sources + codegen B) vs d0 = devoff2 (S2 sources + S1 codegen), 6 round-robin rounds
- dir: `<workspace>\build\agent8\matrix\20261123-0239`
- command: `python -B build\agent7\w4b-noise\readout.py build\agent8\matrix\20261123-0239 --rounds 2,3,4,5,6 -o build\agent8\readout\w-followup\a7\W4c-noR1.md --json build\agent8\readout\w-followup\a7\W4c-noR1.json`
- ref **d0** (matrix.json arm "ref": true); arms B; rounds 2, 3, 4, 5, 6; kept 10 of 13 runs (d0 5, B 5); left out: 0239-cold-d0 (cold (unscored)); 0241-d0-r1 (round 1 not in --rounds); 0243-B-r1 (round 1 not in --rounds).
- T split: light = frame time < 4.5 ms; hT_ref = 0.061 (the median heavy-time share of the kept runs).
- G11 power: OK: overlay best_performance 13/13; scheme Balanced 13/13; AC 1 13/13; saver 0 13/13; no change inside any window; the overlay is not W5's best_efficiency, so compare arms within this window only, not with W5's absolute numbers

## Read-out

- **Primary: T-std.** No round effect on median ms: F = 0.33 on (4, 4), p = 0.847 >= 0.05, so T-std applies (df = runs - arms); B-block T-std is shown beside it.
- median ms vs d0 (T-std): B +1.4 [+0.5, +2.3] *.
- fps vs d0 (T-std): B -0.8 [-1.0, -0.6] *.
- CIs that exclude 0 (T-std): median ms and fps: B median ms +1.4 [+0.5, +2.3] *, B fps -0.8 [-1.0, -0.6] *; tails: none. That is 4 tests (1 arms x 4 metrics) at 5 %, so about 0.2 can be `*` by chance.
- Guards: (a) light share F = 9.53 on (1, 8), p = 0.015: WARNING, an arm may move the mix; (b) raw agrees for every arm; (c) 0 of 10 kept runs flagged. G11: OK.

## T-std and B-block T-std

Round terms of B-block T-std vs round 2: median ms: round 3 -0.7 %, round 4 -0.2 %, round 5 +0.1 %, round 6 -0.1 %; F = 0.33 on (4, 4), p = 0.847. fps: round 3 +0.2 %, round 4 +0.0 %, round 5 +0.0 %, round 6 +0.2 %; F = 1.59 on (4, 4), p = 0.333.

Cells: the GM delta vs d0 in %, with the pooled 95 % CI; `*` = the CI excludes 0. Bold = the primary. d0 band = (max - min) / median of d0's runs (summary.md). 4 vs 4 band = the 95 % half-width for two arms of 4 runs.

| method | metric | d0 band % | pooled CV % | 4 vs 4 band % | df | B (n=5) |
|---|---|---|---|---|---|---|
| **T-std** | median ms | 1.6 | 0.6 | 1.0 | 8 | +1.4 [+0.5, +2.3] * |
| B-block T-std | median ms | 1.2 | 0.8 | 1.5 | 4 | +1.4 [+0.0, +2.7] * |
| **T-std** | fps | 0.4 | 0.1 | 0.2 | 8 | -0.8 [-1.0, -0.6] * |
| B-block T-std | fps | 0.2 | 0.1 | 0.3 | 4 | -0.8 [-1.1, -0.6] * |

### Tails (noisier)

| method | metric | d0 band % | pooled CV % | 4 vs 4 band % | df | B (n=5) |
|---|---|---|---|---|---|---|
| **T-std** | p99 ms | 1.6 | 0.5 | 0.8 | 8 | +0.2 [-0.5, +1.0] |
| B-block T-std | p99 ms | 0.9 | 0.5 | 1.0 | 4 | +0.2 [-0.6, +1.1] |
| **T-std** | 1 % low fps | 1.8 | 4.8 | 8.1 | 8 | -4.7 [-11.1, +2.2] |
| B-block T-std | 1 % low fps | 8.3 | 5.0 | 10.4 | 4 | -4.7 [-12.7, +4.1] |

### Median deltas on median ms (the summary.md form)

Verdicts against each method's own d0 band: B-block T-std B worse.

| method | B |
|---|---|
| raw | +1.3 |
| T-std | +1.3 |
| B-block T-std | +2.0 |

## Guards

**(a) Light share** (the share of frames < light_ms) per arm: d0 0.966, B 0.971. One-way F = 9.53 on (1, 8), p = 0.015. p < 0.05: an arm may move the mix, which T-std hides. Read T-light, T-heavy and the raw rows.

| method | metric | d0 band % | pooled CV % | 4 vs 4 band % | df | B (n=5) |
|---|---|---|---|---|---|---|
| T-light | median ms | 1.5 | 0.6 | 1.0 | 8 | +1.7 [+0.8, +2.6] * |
| T-heavy | median ms | 0.8 | 0.5 | 0.8 | 8 | +0.0 [-0.7, +0.7] |
| T-light | fps | 0.4 | 0.2 | 0.3 | 8 | -0.8 [-1.1, -0.5] * |
| T-heavy | fps | 0.8 | 1.8 | 3.0 | 8 | -1.7 [-4.3, +1.0] |

**(b) Raw GM deltas** with the pooled 95 % CI. They must not contradict T-std:

| method | metric | d0 band % | pooled CV % | 4 vs 4 band % | df | B (n=5) |
|---|---|---|---|---|---|---|
| raw | median ms | 1.7 | 0.6 | 0.9 | 8 | +1.1 [+0.3, +2.0] * |
| raw | fps | 0.4 | 0.3 | 0.5 | 8 | -0.4 [-0.8, -0.0] * |

Raw CI vs the T-std CI (overlap = agrees): median ms: B agrees; fps: B agrees.

**(c) Host flag** (sys.json window P util >= 90 % and E-core MHz < 600): 0 of 10 kept runs.

## Runs

| seq | round | arm | run | kept | raw median ms | T-std median ms | raw fps | T-std fps | light share | P util % | E MHz | flag | overlay |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | d0 | 0239-cold-d0 | no: cold (unscored) | 2.186 | 2.192 | 426.5 | 424.0 | 0.976 | 64.4 | 1921 |  | best_performance |
| 2 | 1 | d0 | 0241-d0-r1 | no: round 1 not in --rounds | 2.246 | 2.259 | 421.8 | 417.8 | 0.979 | 63.7 | 1988 |  | best_performance |
| 3 | 1 | B | 0243-B-r1 | no: round 1 not in --rounds | 2.472 | 2.478 | 388.5 | 386.9 | 0.972 | 64.7 | 1980 |  | best_performance |
| 4 | 2 | B | 0245-B-r2 | yes | 2.512 | 2.518 | 383.9 | 382.3 | 0.972 | 64.5 | 1958 |  | best_performance |
| 5 | 2 | d0 | 0247-d0-r2 | yes | 2.471 | 2.469 | 385.0 | 385.6 | 0.966 | 62.7 | 1979 |  | best_performance |
| 6 | 3 | d0 | 0249-d0-r3 | yes | 2.451 | 2.451 | 386.4 | 386.4 | 0.967 | 64.8 | 1979 |  | best_performance |
| 7 | 3 | B | 0251-B-r3 | yes | 2.502 | 2.502 | 383.4 | 383.4 | 0.969 | 63.9 | 1937 |  | best_performance |
| 8 | 4 | B | 0253-B-r4 | yes | 2.491 | 2.490 | 382.0 | 382.2 | 0.968 | 62.1 | 1837 |  | best_performance |
| 9 | 4 | d0 | 0255-d0-r4 | yes | 2.493 | 2.489 | 385.0 | 385.8 | 0.965 | 62.8 | 1977 |  | best_performance |
| 10 | 5 | d0 | 0257-d0-r5 | yes | 2.491 | 2.491 | 385.1 | 385.1 | 0.967 | 62.6 | 1957 |  | best_performance |
| 11 | 5 | B | 0259-B-r5 | yes | 2.498 | 2.501 | 383.9 | 382.9 | 0.970 | 63.9 | 1947 |  | best_performance |
| 12 | 6 | B | 0301-B-r6 | yes | 2.510 | 2.520 | 385.9 | 382.6 | 0.977 | 62.7 | 1966 |  | best_performance |
| 13 | 6 | d0 | 0303-d0-r6 | yes | 2.465 | 2.461 | 385.6 | 386.7 | 0.965 | 64.6 | 2000 |  | best_performance |


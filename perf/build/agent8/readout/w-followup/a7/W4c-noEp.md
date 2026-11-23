# T-std read-out: 20261123-0239

- title: Window 4c (Agent 8, run-2 task #7 follow-up): codegen B repeat. B = devoffB (S2 sources + codegen B) vs d0 = devoff2 (S2 sources + S1 codegen), 6 round-robin rounds
- dir: `<workspace>\build\agent8\matrix\20261123-0239`
- command: `python -B build\agent7\w4b-noise\readout.py build\agent8\matrix\20261123-0239 --drop 0251-B-r3,0253-B-r4 -o build\agent8\readout\w-followup\a7\W4c-noEp.md --json build\agent8\readout\w-followup\a7\W4c-noEp.json`
- ref **d0** (matrix.json arm "ref": true); arms B; rounds 1, 2, 3, 4, 5, 6; kept 10 of 13 runs (d0 6, B 4); left out: 0239-cold-d0 (cold (unscored)); 0251-B-r3 (--drop); 0253-B-r4 (--drop).
- T split: light = frame time < 4.5 ms; hT_ref = 0.058 (the median heavy-time share of the kept runs).
- G11 power: OK: overlay best_performance 13/13; scheme Balanced 13/13; AC 1 13/13; saver 0 13/13; no change inside any window; the overlay is not W5's best_efficiency, so compare arms within this window only, not with W5's absolute numbers
- note: rounds without every arm: 3, 4 (B-block handles this; check the order is round-robin)

## Read-out

- **Primary: T-std.** No round effect on median ms: F = 1.24 on (5, 3), p = 0.458 >= 0.05, so T-std applies (df = runs - arms); B-block T-std is shown beside it.
- median ms vs d0 (T-std): B +2.8 [-1.7, +7.6].
- fps vs d0 (T-std): B -1.9 [-5.6, +2.0].
- CIs that exclude 0 (T-std): median ms and fps: none; tails: none. That is 4 tests (1 arms x 4 metrics) at 5 %, so about 0.2 can be `*` by chance.
- Guards: (a) light share F = 2.36 on (1, 8), p = 0.163: OK; (b) raw agrees for every arm; (c) 0 of 10 kept runs flagged. G11: OK.

## T-std and B-block T-std

Round terms of B-block T-std vs round 1: median ms: round 2 +5.4 %, round 3 +5.5 %, round 4 +7.1 %, round 5 +5.5 %, round 6 +5.3 %; F = 1.24 on (5, 3), p = 0.458. fps: round 2 -4.5 %, round 3 -5.1 %, round 4 -5.3 %, round 5 -4.5 %, round 6 -4.3 %; F = 1.22 on (5, 3), p = 0.464.

Cells: the GM delta vs d0 in %, with the pooled 95 % CI; `*` = the CI excludes 0. Bold = the primary. d0 band = (max - min) / median of d0's runs (summary.md). 4 vs 4 band = the 95 % half-width for two arms of 4 runs.

| method | metric | d0 band % | pooled CV % | 4 vs 4 band % | df | B (n=4) |
|---|---|---|---|---|---|---|
| **T-std** | median ms | 9.5 | 3.0 | 5.0 | 8 | +2.8 [-1.7, +7.6] |
| B-block T-std | median ms | 4.4 | 2.8 | 6.5 | 3 | +3.6 [-2.8, +10.3] |
| **T-std** | fps | 8.5 | 2.6 | 4.3 | 8 | -1.9 [-5.6, +2.0] |
| B-block T-std | fps | 3.6 | 2.4 | 5.6 | 3 | -2.5 [-7.7, +3.0] |

### Tails (noisier)

| method | metric | d0 band % | pooled CV % | 4 vs 4 band % | df | B (n=4) |
|---|---|---|---|---|---|---|
| **T-std** | p99 ms | 1.4 | 0.4 | 0.7 | 8 | +0.1 [-0.6, +0.7] |
| B-block T-std | p99 ms | 0.9 | 0.6 | 1.3 | 3 | -0.1 [-1.3, +1.2] |
| **T-std** | 1 % low fps | 1.8 | 0.7 | 1.1 | 8 | +0.0 [-1.0, +1.1] |
| B-block T-std | 1 % low fps | 1.0 | 0.6 | 1.4 | 3 | +0.2 [-1.1, +1.6] |

### Median deltas on median ms (the summary.md form)

Verdicts against each method's own d0 band: all `within`.

| method | B |
|---|---|
| raw | +1.5 |
| T-std | +1.8 |
| B-block T-std | +2.6 |

## Guards

**(a) Light share** (the share of frames < light_ms) per arm: d0 0.968, B 0.973. One-way F = 2.36 on (1, 8), p = 0.163. No arm moves the mix.

**(b) Raw GM deltas** with the pooled 95 % CI. They must not contradict T-std:

| method | metric | d0 band % | pooled CV % | 4 vs 4 band % | df | B (n=4) |
|---|---|---|---|---|---|---|
| raw | median ms | 10.0 | 3.2 | 5.3 | 8 | +2.6 [-2.2, +7.6] |
| raw | fps | 9.6 | 2.9 | 4.9 | 8 | -1.5 [-5.7, +2.9] |

Raw CI vs the T-std CI (overlap = agrees): median ms: B agrees; fps: B agrees.

**(c) Host flag** (sys.json window P util >= 90 % and E-core MHz < 600): 0 of 10 kept runs.

## Runs

| seq | round | arm | run | kept | raw median ms | T-std median ms | raw fps | T-std fps | light share | P util % | E MHz | flag | overlay |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | d0 | 0239-cold-d0 | no: cold (unscored) | 2.186 | 2.190 | 426.5 | 424.6 | 0.976 | 64.4 | 1921 |  | best_performance |
| 2 | 1 | d0 | 0241-d0-r1 | yes | 2.246 | 2.256 | 421.8 | 418.4 | 0.979 | 63.7 | 1988 |  | best_performance |
| 3 | 1 | B | 0243-B-r1 | yes | 2.472 | 2.477 | 388.5 | 387.4 | 0.972 | 64.7 | 1980 |  | best_performance |
| 4 | 2 | B | 0245-B-r2 | yes | 2.512 | 2.516 | 383.9 | 382.8 | 0.972 | 64.5 | 1958 |  | best_performance |
| 5 | 2 | d0 | 0247-d0-r2 | yes | 2.471 | 2.468 | 385.0 | 386.1 | 0.966 | 62.7 | 1979 |  | best_performance |
| 6 | 3 | d0 | 0249-d0-r3 | yes | 2.451 | 2.450 | 386.4 | 386.9 | 0.967 | 64.8 | 1979 |  | best_performance |
| 7 | 3 | B | 0251-B-r3 | no: --drop | 2.502 | 2.500 | 383.4 | 384.0 | 0.969 | 63.9 | 1937 |  | best_performance |
| 8 | 4 | B | 0253-B-r4 | no: --drop | 2.491 | 2.488 | 382.0 | 382.7 | 0.968 | 62.1 | 1837 |  | best_performance |
| 9 | 4 | d0 | 0255-d0-r4 | yes | 2.493 | 2.487 | 385.0 | 386.3 | 0.965 | 62.8 | 1977 |  | best_performance |
| 10 | 5 | d0 | 0257-d0-r5 | yes | 2.491 | 2.489 | 385.1 | 385.7 | 0.967 | 62.6 | 1957 |  | best_performance |
| 11 | 5 | B | 0259-B-r5 | yes | 2.498 | 2.500 | 383.9 | 383.4 | 0.970 | 63.9 | 1947 |  | best_performance |
| 12 | 6 | B | 0301-B-r6 | yes | 2.510 | 2.518 | 385.9 | 383.1 | 0.977 | 62.7 | 1966 |  | best_performance |
| 13 | 6 | d0 | 0303-d0-r6 | yes | 2.465 | 2.459 | 385.6 | 387.2 | 0.965 | 64.6 | 2000 |  | best_performance |


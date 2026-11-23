# T-std read-out: 20261123-0451

- title: Window 5b (Agent 8, run-2 task #7 follow-up): TimerQueue wait modes on devoff4 (S4a), all with the 8 timer cvars. d11 (spin wait) vs d11t (blocking wait, REX_TIMER_WAIT_BLOCKING=1) vs d11p (precise wait, timer_queue_precise_wait=true)
- dir: `<workspace>\build\agent8\matrix\20261123-0451`
- command: `python -B build\agent7\w4b-noise\readout.py build\agent8\matrix\20261123-0451 -o build\agent8\readout\w-followup\a7\W5b-p2.md --json build\agent8\readout\w-followup\a7\W5b-p2.json`
- ref **d11** (matrix.json arm "ref": true); arms d11t, d11p; rounds 1, 2, 3, 4, 5, 6; kept 18 of 19 runs (d11 6, d11t 6, d11p 6); left out: 0451-cold-d11 (cold (unscored)).
- T split: light = frame time < 4.5 ms; hT_ref = 0.048 (the median heavy-time share of the kept runs).
- G11 power: OK: overlay best_performance 19/19; scheme Balanced 19/19; AC 1 19/19; saver 0 19/19; no change inside any window; the overlay is not W5's best_efficiency, so compare arms within this window only, not with W5's absolute numbers

## Read-out

- **Primary: T-std.** No round effect on median ms: F = 0.09 on (5, 10), p = 0.993 >= 0.05, so T-std applies (df = runs - arms); B-block T-std is shown beside it.
- median ms vs d11 (T-std): d11t +1.6 [-0.3, +3.6]; d11p +0.3 [-1.6, +2.2].
- fps vs d11 (T-std): d11t -1.5 [-3.0, +0.0]; d11p -0.8 [-2.3, +0.8].
- CIs that exclude 0 (T-std): median ms and fps: none; tails: none. That is 8 tests (2 arms x 4 metrics) at 5 %, so about 0.4 can be `*` by chance.
- Guards: (a) light share F = 1.66 on (2, 15), p = 0.222: OK; (b) raw agrees for every arm; (c) 0 of 18 kept runs flagged. G11: OK.

## T-std and B-block T-std

Round terms of B-block T-std vs round 1: median ms: round 2 +0.3 %, round 3 -0.1 %, round 4 -0.3 %, round 5 +0.5 %, round 6 -0.1 %; F = 0.09 on (5, 10), p = 0.993. fps: round 2 -0.2 %, round 3 +0.2 %, round 4 +0.5 %, round 5 -0.2 %, round 6 +0.3 %; F = 0.09 on (5, 10), p = 0.991.

Cells: the GM delta vs d11 in %, with the pooled 95 % CI; `*` = the CI excludes 0. Bold = the primary. d11 band = (max - min) / median of d11's runs (summary.md). 4 vs 4 band = the 95 % half-width for two arms of 4 runs.

| method | metric | d11 band % | pooled CV % | 4 vs 4 band % | df | d11t (n=6) | d11p (n=6) |
|---|---|---|---|---|---|---|---|
| **T-std** | median ms | 1.6 | 1.6 | 2.4 | 15 | +1.6 [-0.3, +3.6] | +0.3 [-1.6, +2.2] |
| B-block T-std | median ms | 1.7 | 1.9 | 3.0 | 10 | +1.6 [-0.8, +4.1] | +0.3 [-2.1, +2.7] |
| **T-std** | fps | 2.2 | 1.2 | 1.9 | 15 | -1.5 [-3.0, +0.0] | -0.8 [-2.3, +0.8] |
| B-block T-std | fps | 2.5 | 1.5 | 2.4 | 10 | -1.5 [-3.4, +0.4] | -0.8 [-2.6, +1.2] |

### Tails (noisier)

| method | metric | d11 band % | pooled CV % | 4 vs 4 band % | df | d11t (n=6) | d11p (n=6) |
|---|---|---|---|---|---|---|---|
| **T-std** | p99 ms | 2.7 | 1.0 | 1.5 | 15 | +0.1 [-1.0, +1.3] | +0.3 [-0.9, +1.5] |
| B-block T-std | p99 ms | 1.6 | 0.9 | 1.4 | 10 | +0.1 [-1.0, +1.3] | +0.3 [-0.9, +1.4] |
| **T-std** | 1 % low fps | 7.3 | 2.6 | 4.0 | 15 | -0.6 [-3.8, +2.7] | -0.4 [-3.5, +2.9] |
| B-block T-std | 1 % low fps | 4.8 | 2.7 | 4.3 | 10 | -0.6 [-3.9, +2.8] | -0.4 [-3.7, +3.1] |

### Median deltas on median ms (the summary.md form)

Verdicts against each method's own d11 band: all `within`.

| method | d11t | d11p |
|---|---|---|
| raw | +0.5 | -0.1 |
| T-std | +0.4 | +0.1 |
| B-block T-std | +0.7 | +0.4 |

## Guards

**(a) Light share** (the share of frames < light_ms) per arm: d11 0.974, d11t 0.971, d11p 0.974. One-way F = 1.66 on (2, 15), p = 0.222. No arm moves the mix.

**(b) Raw GM deltas** with the pooled 95 % CI. They must not contradict T-std:

| method | metric | d11 band % | pooled CV % | 4 vs 4 band % | df | d11t (n=6) | d11p (n=6) |
|---|---|---|---|---|---|---|---|
| raw | median ms | 1.5 | 1.6 | 2.4 | 15 | +1.7 [-0.2, +3.7] | +0.3 [-1.6, +2.2] |
| raw | fps | 2.1 | 1.4 | 2.1 | 15 | -1.7 [-3.4, -0.1] * | -0.8 [-2.4, +0.9] |

Raw CI vs the T-std CI (overlap = agrees): median ms: d11t agrees, d11p agrees; fps: d11t agrees, d11p agrees.

**(c) Host flag** (sys.json window P util >= 90 % and E-core MHz < 600): 0 of 18 kept runs.

## Runs

| seq | round | arm | run | kept | raw median ms | T-std median ms | raw fps | T-std fps | light share | P util % | E MHz | flag | overlay |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | d11 | 0451-cold-d11 | no: cold (unscored) | 2.094 | 2.105 | 441.8 | 437.7 | 0.987 | 63.2 | 1979 |  | best_performance |
| 2 | 1 | d11 | 0453-d11-r1 | yes | 2.483 | 2.484 | 393.0 | 392.8 | 0.976 | 65.7 | 1866 |  | best_performance |
| 3 | 1 | d11t | 0455-d11t-r1 | yes | 2.647 | 2.639 | 367.1 | 369.2 | 0.966 | 63.5 | 1882 |  | best_performance |
| 4 | 1 | d11p | 0457-d11p-r1 | yes | 2.457 | 2.449 | 386.0 | 387.8 | 0.969 | 58.5 | 1776 |  | best_performance |
| 5 | 2 | d11t | 0459-d11t-r2 | yes | 2.582 | 2.580 | 376.6 | 377.0 | 0.972 | 61.7 | 1941 |  | best_performance |
| 6 | 2 | d11p | 0501-d11p-r2 | yes | 2.499 | 2.501 | 385.4 | 385.0 | 0.975 | 62.3 | 1972 |  | best_performance |
| 7 | 2 | d11 | 0504-d11-r2 | yes | 2.512 | 2.511 | 385.2 | 385.2 | 0.974 | 62.7 | 1984 |  | best_performance |
| 8 | 3 | d11p | 0506-d11p-r3 | yes | 2.515 | 2.521 | 385.9 | 384.6 | 0.978 | 60.3 | 1943 |  | best_performance |
| 9 | 3 | d11 | 0508-d11-r3 | yes | 2.521 | 2.523 | 385.0 | 384.5 | 0.975 | 62.5 | 1962 |  | best_performance |
| 10 | 3 | d11t | 0510-d11t-r3 | yes | 2.528 | 2.516 | 379.3 | 382.5 | 0.966 | 62.6 | 1917 |  | best_performance |
| 11 | 4 | d11 | 0512-d11-r4 | yes | 2.517 | 2.519 | 385.4 | 385.0 | 0.975 | 62.4 | 1974 |  | best_performance |
| 12 | 4 | d11t | 0514-d11t-r4 | yes | 2.518 | 2.519 | 384.7 | 384.6 | 0.974 | 62.2 | 1978 |  | best_performance |
| 13 | 4 | d11p | 0516-d11p-r4 | yes | 2.504 | 2.505 | 385.5 | 385.1 | 0.975 | 62.6 | 1961 |  | best_performance |
| 14 | 5 | d11t | 0518-d11t-r5 | yes | 2.520 | 2.520 | 385.7 | 385.7 | 0.974 | 63.1 | 1965 |  | best_performance |
| 15 | 5 | d11p | 0520-d11p-r5 | yes | 2.586 | 2.585 | 375.6 | 376.0 | 0.972 | 63.3 | 1912 |  | best_performance |
| 16 | 5 | d11 | 0522-d11-r5 | yes | 2.506 | 2.504 | 385.0 | 385.7 | 0.972 | 63.8 | 1992 |  | best_performance |
| 17 | 6 | d11p | 0524-d11p-r6 | yes | 2.529 | 2.529 | 382.1 | 382.5 | 0.973 | 61.2 | 1902 |  | best_performance |
| 18 | 6 | d11 | 0526-d11-r6 | yes | 2.510 | 2.509 | 385.2 | 385.4 | 0.973 | 64.1 | 1975 |  | best_performance |
| 19 | 6 | d11t | 0528-d11t-r6 | yes | 2.519 | 2.521 | 385.4 | 384.9 | 0.975 | 62.2 | 1963 |  | best_performance |


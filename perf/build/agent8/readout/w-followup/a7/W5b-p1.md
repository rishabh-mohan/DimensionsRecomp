# T-std read-out: 20261123-0155

- title: Window 5b (Agent 8, run-2 task #7 follow-up): TimerQueue wait modes on devoff4 (S4a), all with the 8 timer cvars. d11 (spin wait) vs d11t (blocking wait, REX_TIMER_WAIT_BLOCKING=1) vs d11p (precise wait, timer_queue_precise_wait=true)
- dir: `<workspace>\build\agent8\matrix\20261123-0155`
- command: `python -B build\agent7\w4b-noise\readout.py build\agent8\matrix\20261123-0155 -o build\agent8\readout\w-followup\a7\W5b-p1.md --json build\agent8\readout\w-followup\a7\W5b-p1.json`
- ref **d11** (matrix.json arm "ref": true); arms d11t, d11p; rounds 1, 2, 3, 4, 5, 6; kept 18 of 19 runs (d11 6, d11t 6, d11p 6); left out: 0155-cold-d11 (cold (unscored)).
- T split: light = frame time < 4.5 ms; hT_ref = 0.051 (the median heavy-time share of the kept runs).
- G11 power: OK: overlay best_performance 19/19; scheme Balanced 19/19; AC 1 19/19; saver 0 19/19; no change inside any window; the overlay is not W5's best_efficiency, so compare arms within this window only, not with W5's absolute numbers

## Read-out

- **Primary: B-block T-std.** Round effect on median ms: F = 10.14 on (5, 10), p = 0.001 < 0.05, so B-block T-std applies (df = runs - arms - rounds + 1); T-std is shown beside it.
- median ms vs d11 (B-block T-std): d11t +0.7 [-1.1, +2.6]; d11p +0.8 [-1.1, +2.6].
- fps vs d11 (B-block T-std): d11t -0.6 [-1.8, +0.6]; d11p -0.7 [-1.9, +0.5].
- CIs that exclude 0 (B-block T-std): median ms and fps: none; tails: none. That is 8 tests (2 arms x 4 metrics) at 5 %, so about 0.4 can be `*` by chance.
- Guards: (a) light share F = 0.29 on (2, 15), p = 0.754: OK; (b) raw agrees for every arm; (c) 0 of 18 kept runs flagged. G11: OK.

## T-std and B-block T-std

Round terms of B-block T-std vs round 1: median ms: round 2 +6.0 %, round 3 +7.8 %, round 4 +6.2 %, round 5 +5.1 %, round 6 +5.8 %; F = 10.14 on (5, 10), p = 0.001. fps: round 2 -4.4 %, round 3 -5.6 %, round 4 -4.4 %, round 5 -4.1 %, round 6 -4.2 %; F = 13.69 on (5, 10), p = < 0.001.

Cells: the GM delta vs d11 in %, with the pooled 95 % CI; `*` = the CI excludes 0. Bold = the primary. d11 band = (max - min) / median of d11's runs (summary.md). 4 vs 4 band = the 95 % half-width for two arms of 4 runs.

| method | metric | d11 band % | pooled CV % | 4 vs 4 band % | df | d11t (n=6) | d11p (n=6) |
|---|---|---|---|---|---|---|---|
| T-std | median ms | 9.0 | 2.8 | 4.4 | 15 | +0.7 [-2.7, +4.3] | +0.8 [-2.7, +4.3] |
| **B-block T-std** | median ms | 3.3 | 1.4 | 2.2 | 10 | +0.7 [-1.1, +2.6] | +0.8 [-1.1, +2.6] |
| T-std | fps | 7.0 | 2.1 | 3.3 | 15 | -0.6 [-3.2, +2.0] | -0.7 [-3.3, +1.9] |
| **B-block T-std** | fps | 2.2 | 0.9 | 1.5 | 10 | -0.6 [-1.8, +0.6] | -0.7 [-1.9, +0.5] |

### Tails (noisier)

| method | metric | d11 band % | pooled CV % | 4 vs 4 band % | df | d11t (n=6) | d11p (n=6) |
|---|---|---|---|---|---|---|---|
| T-std | p99 ms | 2.8 | 1.1 | 1.6 | 15 | +0.6 [-0.8, +1.9] | -0.2 [-1.6, +1.1] |
| **B-block T-std** | p99 ms | 1.3 | 0.6 | 1.0 | 10 | +0.6 [-0.2, +1.4] | -0.2 [-1.0, +0.6] |
| T-std | 1 % low fps | 3.7 | 6.2 | 9.9 | 15 | -5.1 [-12.1, +2.5] | -0.0 [-7.4, +8.0] |
| **B-block T-std** | 1 % low fps | 9.9 | 6.0 | 9.9 | 10 | -5.1 [-12.1, +2.5] | -0.0 [-7.4, +7.9] |

### Median deltas on median ms (the summary.md form)

Verdicts against each method's own d11 band: all `within`.

| method | d11t | d11p |
|---|---|---|
| raw | -0.0 | -0.5 |
| T-std | -0.0 | -0.5 |
| B-block T-std | +0.4 | +0.0 |

## Guards

**(a) Light share** (the share of frames < light_ms) per arm: d11 0.975, d11t 0.973, d11p 0.975. One-way F = 0.29 on (2, 15), p = 0.754. No arm moves the mix.

**(b) Raw GM deltas** with the pooled 95 % CI. They must not contradict B-block T-std:

| method | metric | d11 band % | pooled CV % | 4 vs 4 band % | df | d11t (n=6) | d11p (n=6) |
|---|---|---|---|---|---|---|---|
| raw | median ms | 10.1 | 3.2 | 4.9 | 15 | +0.9 [-3.0, +4.9] | +0.8 [-3.1, +4.8] |
| raw | fps | 8.7 | 2.6 | 4.0 | 15 | -0.9 [-4.0, +2.4] | -0.7 [-3.8, +2.6] |

Raw CI vs the B-block T-std CI (overlap = agrees): median ms: d11t agrees, d11p agrees; fps: d11t agrees, d11p agrees.

**(c) Host flag** (sys.json window P util >= 90 % and E-core MHz < 600): 0 of 18 kept runs.

## Runs

| seq | round | arm | run | kept | raw median ms | T-std median ms | raw fps | T-std fps | light share | P util % | E MHz | flag | overlay |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | d11 | 0155-cold-d11 | no: cold (unscored) | 2.306 | 2.322 | 419.0 | 415.3 | 0.983 | 66.1 | 2012 |  | best_performance |
| 2 | 1 | d11 | 0157-d11-r1 | yes | 2.288 | 2.311 | 415.1 | 409.4 | 0.988 | 63.2 | 1995 |  | best_performance |
| 3 | 1 | d11t | 0159-d11t-r1 | yes | 2.347 | 2.363 | 407.0 | 402.9 | 0.984 | 61.5 | 1961 |  | best_performance |
| 4 | 1 | d11p | 0201-d11p-r1 | yes | 2.435 | 2.446 | 395.9 | 393.7 | 0.979 | 60.9 | 1955 |  | best_performance |
| 5 | 2 | d11t | 0203-d11t-r2 | yes | 2.496 | 2.494 | 385.7 | 386.2 | 0.971 | 61.6 | 1984 |  | best_performance |
| 6 | 2 | d11p | 0205-d11p-r2 | yes | 2.511 | 2.517 | 384.9 | 383.4 | 0.977 | 61.8 | 1926 |  | best_performance |
| 7 | 2 | d11 | 0207-d11-r2 | yes | 2.528 | 2.533 | 384.0 | 382.7 | 0.976 | 62.0 | 1962 |  | best_performance |
| 8 | 3 | d11p | 0209-d11p-r3 | yes | 2.544 | 2.547 | 381.8 | 380.6 | 0.976 | 59.2 | 1861 |  | best_performance |
| 9 | 3 | d11 | 0211-d11-r3 | yes | 2.542 | 2.537 | 381.5 | 382.5 | 0.970 | 62.6 | 1957 |  | best_performance |
| 10 | 3 | d11t | 0213-d11t-r3 | yes | 2.606 | 2.590 | 371.7 | 375.2 | 0.962 | 60.3 | 1838 |  | best_performance |
| 11 | 4 | d11 | 0215-d11-r4 | yes | 2.526 | 2.524 | 384.2 | 384.5 | 0.972 | 64.2 | 1949 |  | best_performance |
| 12 | 4 | d11t | 0217-d11t-r4 | yes | 2.532 | 2.532 | 383.3 | 383.3 | 0.973 | 60.5 | 1930 |  | best_performance |
| 13 | 4 | d11p | 0219-d11p-r4 | yes | 2.505 | 2.505 | 384.8 | 384.9 | 0.973 | 62.5 | 1948 |  | best_performance |
| 14 | 5 | d11t | 0221-d11t-r5 | yes | 2.498 | 2.492 | 382.4 | 384.2 | 0.972 | 61.5 | 1955 |  | best_performance |
| 15 | 5 | d11p | 0223-d11p-r5 | yes | 2.500 | 2.496 | 385.1 | 386.2 | 0.970 | 62.1 | 1955 |  | best_performance |
| 16 | 5 | d11 | 0225-d11-r5 | yes | 2.492 | 2.490 | 385.1 | 386.0 | 0.970 | 63.4 | 1952 |  | best_performance |
| 17 | 6 | d11p | 0227-d11p-r6 | yes | 2.489 | 2.494 | 386.2 | 384.8 | 0.977 | 61.1 | 1946 |  | best_performance |
| 18 | 6 | d11 | 0229-d11-r6 | yes | 2.504 | 2.504 | 385.7 | 385.9 | 0.972 | 63.2 | 1959 |  | best_performance |
| 19 | 6 | d11t | 0231-d11t-r6 | yes | 2.531 | 2.534 | 385.1 | 384.7 | 0.974 | 61.1 | 1972 |  | best_performance |


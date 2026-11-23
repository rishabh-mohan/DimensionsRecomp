# T-std read-out: W5b

- title: Window 5b (Agent 8, run-2 task #7 follow-up): TimerQueue wait modes on devoff4 (S4a), all with the 8 timer cvars. d11 (spin wait) vs d11t (blocking wait, REX_TIMER_WAIT_BLOCKING=1) vs d11p (precise wait, timer_queue_precise_wait=true)
- dir: `<workspace>\build\agent8\readout\w-followup\pool\W5b`
- command: `python -B build\agent7\w4b-noise\readout.py build\agent8\readout\w-followup\pool\W5b --drop 0209-d11p-r3,0213-d11t-r3,0453-d11-r1,0455-d11t-r1,0457-d11p-r1,0510-d11t-r3 -o build\agent8\readout\w-followup\a7\W5b-pool-noFlag.md --json build\agent8\readout\w-followup\a7\W5b-pool-noFlag.json`
- ref **d11** (matrix.json arm "ref": true); arms d11t, d11p; rounds 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12; kept 30 of 38 runs (d11 11, d11t 9, d11p 10); left out: 0155-cold-d11 (cold (unscored)); 0209-d11p-r3 (--drop); 0213-d11t-r3 (--drop); 0451-cold-d11 (cold (unscored)); 0453-d11-r1 (--drop); 0455-d11t-r1 (--drop); 0457-d11p-r1 (--drop); 0510-d11t-r3 (--drop).
- T split: light = frame time < 4.5 ms; hT_ref = 0.048 (the median heavy-time share of the kept runs).
- G11 power: OK: overlay best_performance 38/38; scheme Balanced 38/38; AC 1 38/38; saver 0 38/38; no change inside any window; the overlay is not W5's best_efficiency, so compare arms within this window only, not with W5's absolute numbers
- note: rounds without every arm: 3, 9 (B-block handles this; check the order is round-robin)

## Read-out

- **Primary: B-block T-std.** Round effect on median ms: F = 6.41 on (10, 17), p = < 0.001 < 0.05, so B-block T-std applies (df = runs - arms - rounds + 1); T-std is shown beside it.
- median ms vs d11 (B-block T-std): d11t +0.6 [-0.6, +1.9]; d11p +0.7 [-0.5, +1.9].
- fps vs d11 (B-block T-std): d11t -0.4 [-1.3, +0.5]; d11p -0.7 [-1.5, +0.1].
- CIs that exclude 0 (B-block T-std): median ms and fps: none; tails: none. That is 8 tests (2 arms x 4 metrics) at 5 %, so about 0.4 can be `*` by chance.
- Guards: (a) light share F = 0.04 on (2, 27), p = 0.957: OK; (b) raw agrees for every arm; (c) 0 of 30 kept runs flagged. G11: OK.

## T-std and B-block T-std

Round terms of B-block T-std vs round 1: median ms: round 2 +6.0 %, round 3 +7.4 %, round 4 +6.3 %, round 5 +5.1 %, round 6 +5.8 %, round 8 +6.8 %, round 9 +6.5 %, round 10 +6.1 %, round 11 +7.0 %, round 12 +6.3 %; F = 6.41 on (10, 17), p = < 0.001. fps: round 2 -4.4 %, round 3 -5.2 %, round 4 -4.4 %, round 5 -4.1 %, round 6 -4.2 %, round 8 -5.0 %, round 9 -4.5 %, round 10 -4.4 %, round 11 -5.0 %, round 12 -4.5 %; F = 7.61 on (10, 17), p = < 0.001.

Cells: the GM delta vs d11 in %, with the pooled 95 % CI; `*` = the CI excludes 0. Bold = the primary. d11 band = (max - min) / median of d11's runs (summary.md). 4 vs 4 band = the 95 % half-width for two arms of 4 runs.

| method | metric | d11 band % | pooled CV % | 4 vs 4 band % | df | d11t (n=9) | d11p (n=10) |
|---|---|---|---|---|---|---|---|
| T-std | median ms | 9.0 | 2.2 | 3.3 | 27 | +0.4 [-1.7, +2.5] | +0.5 [-1.5, +2.6] |
| **B-block T-std** | median ms | 3.3 | 1.3 | 1.9 | 17 | +0.6 [-0.6, +1.9] | +0.7 [-0.5, +1.9] |
| T-std | fps | 7.0 | 1.7 | 2.4 | 27 | -0.3 [-1.8, +1.3] | -0.6 [-2.1, +0.9] |
| **B-block T-std** | fps | 2.2 | 0.9 | 1.3 | 17 | -0.4 [-1.3, +0.5] | -0.7 [-1.5, +0.1] |

### Tails (noisier)

| method | metric | d11 band % | pooled CV % | 4 vs 4 band % | df | d11t (n=9) | d11p (n=10) |
|---|---|---|---|---|---|---|---|
| T-std | p99 ms | 2.7 | 0.8 | 1.1 | 27 | -0.0 [-0.7, +0.7] | +0.1 [-0.6, +0.8] |
| **B-block T-std** | p99 ms | 1.2 | 0.7 | 1.0 | 17 | +0.1 [-0.6, +0.7] | +0.2 [-0.4, +0.8] |
| T-std | 1 % low fps | 3.7 | 4.8 | 7.3 | 27 | -2.7 [-6.9, +1.8] | -0.5 [-4.7, +4.0] |
| **B-block T-std** | 1 % low fps | 9.5 | 4.9 | 7.6 | 17 | -2.8 [-7.4, +2.0] | -0.6 [-5.1, +4.1] |

### Median deltas on median ms (the summary.md form)

Verdicts against each method's own d11 band: all `within`.

| method | d11t | d11p |
|---|---|---|
| raw | +0.3 | -0.3 |
| T-std | +0.4 | -0.3 |
| B-block T-std | +0.3 | +0.2 |

## Guards

**(a) Light share** (the share of frames < light_ms) per arm: d11 0.974, d11t 0.974, d11p 0.975. One-way F = 0.04 on (2, 27), p = 0.957. No arm moves the mix.

**(b) Raw GM deltas** with the pooled 95 % CI. They must not contradict B-block T-std:

| method | metric | d11 band % | pooled CV % | 4 vs 4 band % | df | d11t (n=9) | d11p (n=10) |
|---|---|---|---|---|---|---|---|
| raw | median ms | 10.1 | 2.4 | 3.6 | 27 | +0.4 [-1.8, +2.7] | +0.5 [-1.7, +2.7] |
| raw | fps | 8.7 | 2.0 | 2.9 | 27 | -0.3 [-2.1, +1.5] | -0.6 [-2.3, +1.2] |

Raw CI vs the B-block T-std CI (overlap = agrees): median ms: d11t agrees, d11p agrees; fps: d11t agrees, d11p agrees.

**(c) Host flag** (sys.json window P util >= 90 % and E-core MHz < 600): 0 of 30 kept runs.

## Runs

| seq | round | arm | run | kept | raw median ms | T-std median ms | raw fps | T-std fps | light share | P util % | E MHz | flag | overlay |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | d11 | 0155-cold-d11 | no: cold (unscored) | 2.306 | 2.321 | 419.0 | 415.8 | 0.983 | 66.1 | 2012 |  | best_performance |
| 2 | 1 | d11 | 0157-d11-r1 | yes | 2.288 | 2.309 | 415.1 | 409.8 | 0.988 | 63.2 | 1995 |  | best_performance |
| 3 | 1 | d11t | 0159-d11t-r1 | yes | 2.347 | 2.361 | 407.0 | 403.4 | 0.984 | 61.5 | 1961 |  | best_performance |
| 4 | 1 | d11p | 0201-d11p-r1 | yes | 2.435 | 2.443 | 395.9 | 394.1 | 0.979 | 60.9 | 1955 |  | best_performance |
| 5 | 2 | d11t | 0203-d11t-r2 | yes | 2.496 | 2.493 | 385.7 | 386.6 | 0.971 | 61.6 | 1984 |  | best_performance |
| 6 | 2 | d11p | 0205-d11p-r2 | yes | 2.511 | 2.516 | 384.9 | 383.9 | 0.977 | 61.8 | 1926 |  | best_performance |
| 7 | 2 | d11 | 0207-d11-r2 | yes | 2.528 | 2.532 | 384.0 | 383.2 | 0.976 | 62.0 | 1962 |  | best_performance |
| 8 | 3 | d11p | 0209-d11p-r3 | no: --drop | 2.544 | 2.546 | 381.8 | 381.0 | 0.976 | 59.2 | 1861 |  | best_performance |
| 9 | 3 | d11 | 0211-d11-r3 | yes | 2.542 | 2.535 | 381.5 | 382.9 | 0.970 | 62.6 | 1957 |  | best_performance |
| 10 | 3 | d11t | 0213-d11t-r3 | no: --drop | 2.606 | 2.589 | 371.7 | 375.6 | 0.962 | 60.3 | 1838 |  | best_performance |
| 11 | 4 | d11 | 0215-d11-r4 | yes | 2.526 | 2.523 | 384.2 | 384.9 | 0.972 | 64.2 | 1949 |  | best_performance |
| 12 | 4 | d11t | 0217-d11t-r4 | yes | 2.532 | 2.531 | 383.3 | 383.7 | 0.973 | 60.5 | 1930 |  | best_performance |
| 13 | 4 | d11p | 0219-d11p-r4 | yes | 2.505 | 2.503 | 384.8 | 385.3 | 0.973 | 62.5 | 1948 |  | best_performance |
| 14 | 5 | d11t | 0221-d11t-r5 | yes | 2.498 | 2.491 | 382.4 | 384.7 | 0.972 | 61.5 | 1955 |  | best_performance |
| 15 | 5 | d11p | 0223-d11p-r5 | yes | 2.500 | 2.495 | 385.1 | 386.6 | 0.970 | 62.1 | 1955 |  | best_performance |
| 16 | 5 | d11 | 0225-d11-r5 | yes | 2.492 | 2.487 | 385.1 | 386.5 | 0.970 | 63.4 | 1952 |  | best_performance |
| 17 | 6 | d11p | 0227-d11p-r6 | yes | 2.489 | 2.492 | 386.2 | 385.2 | 0.977 | 61.1 | 1946 |  | best_performance |
| 18 | 6 | d11 | 0229-d11-r6 | yes | 2.504 | 2.502 | 385.7 | 386.3 | 0.972 | 63.2 | 1959 |  | best_performance |
| 19 | 6 | d11t | 0231-d11t-r6 | yes | 2.531 | 2.531 | 385.1 | 385.2 | 0.974 | 61.1 | 1972 |  | best_performance |
| 20 | 0 | d11 | 0451-cold-d11 | no: cold (unscored) | 2.094 | 2.105 | 441.8 | 437.6 | 0.987 | 63.2 | 1979 |  | best_performance |
| 21 | 7 | d11 | 0453-d11-r1 | no: --drop | 2.483 | 2.484 | 393.0 | 392.7 | 0.976 | 65.7 | 1866 |  | best_performance |
| 22 | 7 | d11t | 0455-d11t-r1 | no: --drop | 2.647 | 2.639 | 367.1 | 369.2 | 0.966 | 63.5 | 1882 |  | best_performance |
| 23 | 7 | d11p | 0457-d11p-r1 | no: --drop | 2.457 | 2.449 | 386.0 | 387.7 | 0.969 | 58.5 | 1776 |  | best_performance |
| 24 | 8 | d11t | 0459-d11t-r2 | yes | 2.582 | 2.580 | 376.6 | 377.0 | 0.972 | 61.7 | 1941 |  | best_performance |
| 25 | 8 | d11p | 0501-d11p-r2 | yes | 2.499 | 2.501 | 385.4 | 384.9 | 0.975 | 62.3 | 1972 |  | best_performance |
| 26 | 8 | d11 | 0504-d11-r2 | yes | 2.512 | 2.512 | 385.2 | 385.2 | 0.974 | 62.7 | 1984 |  | best_performance |
| 27 | 9 | d11p | 0506-d11p-r3 | yes | 2.515 | 2.521 | 385.9 | 384.6 | 0.978 | 60.3 | 1943 |  | best_performance |
| 28 | 9 | d11 | 0508-d11-r3 | yes | 2.521 | 2.523 | 385.0 | 384.4 | 0.975 | 62.5 | 1962 |  | best_performance |
| 29 | 9 | d11t | 0510-d11t-r3 | no: --drop | 2.528 | 2.516 | 379.3 | 382.4 | 0.966 | 62.6 | 1917 |  | best_performance |
| 30 | 10 | d11 | 0512-d11-r4 | yes | 2.517 | 2.519 | 385.4 | 384.9 | 0.975 | 62.4 | 1974 |  | best_performance |
| 31 | 10 | d11t | 0514-d11t-r4 | yes | 2.518 | 2.519 | 384.7 | 384.6 | 0.974 | 62.2 | 1978 |  | best_performance |
| 32 | 10 | d11p | 0516-d11p-r4 | yes | 2.504 | 2.505 | 385.5 | 385.1 | 0.975 | 62.6 | 1961 |  | best_performance |
| 33 | 11 | d11t | 0518-d11t-r5 | yes | 2.520 | 2.521 | 385.7 | 385.7 | 0.974 | 63.1 | 1965 |  | best_performance |
| 34 | 11 | d11p | 0520-d11p-r5 | yes | 2.586 | 2.585 | 375.6 | 376.0 | 0.972 | 63.3 | 1912 |  | best_performance |
| 35 | 11 | d11 | 0522-d11-r5 | yes | 2.506 | 2.504 | 385.0 | 385.6 | 0.972 | 63.8 | 1992 |  | best_performance |
| 36 | 12 | d11p | 0524-d11p-r6 | yes | 2.529 | 2.529 | 382.1 | 382.5 | 0.973 | 61.2 | 1902 |  | best_performance |
| 37 | 12 | d11 | 0526-d11-r6 | yes | 2.510 | 2.509 | 385.2 | 385.4 | 0.973 | 64.1 | 1975 |  | best_performance |
| 38 | 12 | d11t | 0528-d11t-r6 | yes | 2.519 | 2.521 | 385.4 | 384.9 | 0.975 | 62.2 | 1963 |  | best_performance |


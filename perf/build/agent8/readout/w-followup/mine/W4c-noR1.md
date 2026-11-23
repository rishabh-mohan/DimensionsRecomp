# W4c: pooled numbers (pool_readout.py)

Base arm `d0`. Kept runs: scored, status OK, valid timing, not excluded, minus --drop 0241-d0-r1, 0243-B-r1. A round is (pass, round).
Paired = per round, arm vs base in the same round; % values are exp(mean log ratio) - 1 with a 95 % t-CI; sign count = rounds where the arm is lower (ms, cores) or higher (fps).

| pass | dir | results.csv sha256 | matrix.json sha256 |
|---|---|---|---|
| 1 | `build/agent8/matrix/20261123-0239` | `A4F0ACC2CD2FB49A` | `E2E3E4DAAF7D30C7` |

## Runs per arm

| arm | pass | planned (scored) | timed (OK, valid, not excluded) | kept | cold run |
|---|---|---|---|---|---|
| d0 | 1 | 6 | 6 | 5 | 0239-cold-d0 2.186 ms |
| B | 1 | 6 | 6 | 5 | - |

## pass 1: per arm vs base `d0`

| arm | n | median ms (median of runs) | vs base (pooled medians) | paired median | lower in | fps median | vs base | fps mean | paired fps | CPU cores | paired cores | frames mean (min-max) | band (max-min)/median | CV |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d0 | 5 | 2.471 | - | - | - | 385.1 | - | 385.4 | - | 2.534 | - | 19272 (19249-19321) | 1.7 % | 0.7 % |
| B | 5 | 2.502 | +1.3 % | +1.1 [-0.1, +2.4] | 1/5 (p 0.375) | 383.9 | -0.3 % | 383.8 | -0.4 [-0.9, +0.0] | 2.606 | +0.072 [-0.017, +0.160] | 19193 (19103-19297) | 0.8 % | 0.3 % |

Per-round median ms difference (arm - base):

- B: p1 r2 +0.041, p1 r3 +0.051, p1 r4 -0.002, p1 r5 +0.007, p1 r6 +0.045

Tail (results.csv): mean p99 / p99.9 ms, worst frame, frames over 33 ms; paired p99.9 diff vs base:

| arm | p99 mean | p99.9 mean | p99.9 median | max ms | over 33 ms | paired p99.9 diff ms | higher in |
|---|---|---|---|---|---|---|---|
| d0 | 4.956 | 5.606 | 5.606 | 10.26 | 0 | - | - |
| B | 4.902 | 5.962 | 5.670 | 20.66 | 0 | +0.356 [-0.341, +1.053] | 3/5 (p 1.000) |

Tail (perf.csv windows): frames over X ms per minute (mean of runs), totals, k-th largest frame (median of runs), time share over 6 ms:

| arm | runs | >6 ms/min | >8 | >10 | >16.7 | >33 | total >10 / >16.7 / >33 | runs with >10 | top5 ms | top25 ms | top50 ms | share >6 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d0 | 5 | 3.84 | 0.24 | 0.24 | 0.00 | 0.00 | 1 / 0 / 0 | 1 | 5.952 | 5.551 | 5.350 | 0.041 % |
| B | 5 | 14.40 | 7.20 | 5.28 | 1.20 | 0.00 | 22 / 5 / 0 | 2 | 5.895 | 5.575 | 5.442 | 0.230 % |

| pair (A - B) | >6 ms/min diff [CI] | A higher in | >8 diff | A higher in | >10 diff | top25 diff ms | A higher in | top5 diff ms | A higher in |
|---|---|---|---|---|---|---|---|---|---|
| B-d0 | +10.56 [-11.89, +33.01] | 2/5 (p 1.000) | +6.96 [-5.16, +19.08] | 2/2 (p 0.500) | +5.04 [-4.75, +14.83] | +0.175 [-0.272, +0.622] | 2/5 (p 1.000) | +3.592 [-3.417, +10.601] | 3/5 (p 1.000) |

## Per run (perf.csv window check and tails)

| run | pass | round | arm | frames | median | p99.9 | max (at s) | >6 | >8 | >10 | >16.7 | >33 | top25 | >6 per 10 s bin | check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0241-d0-r1 | 1 | 1 | d0 | 21090 | 2.246 | 5.647 | 6.03 (44.9) | 1 | 0 | 0 | 0 | 0 | 5.577 | 0 0 0 0 1 | OK (offset 0) |
| 0243-B-r1 | 1 | 1 | B | 19427 | 2.472 | 5.574 | 7.39 (16.4) | 2 | 0 | 0 | 0 | 0 | 5.511 | 0 1 0 0 1 | OK (offset 0) |
| 0245-B-r2 | 1 | 2 | B | 19197 | 2.512 | 5.518 | 6.08 (48.1) | 1 | 0 | 0 | 0 | 0 | 5.435 | 0 0 0 0 1 | OK (offset 0) |
| 0247-d0-r2 | 1 | 2 | d0 | 19252 | 2.471 | 5.560 | 7.08 (12.2) | 3 | 0 | 0 | 0 | 0 | 5.498 | 1 1 0 0 1 | OK (offset 0) |
| 0249-d0-r3 | 1 | 3 | d0 | 19321 | 2.451 | 5.568 | 6.08 (1.7) | 1 | 0 | 0 | 0 | 0 | 5.511 | 1 0 0 0 0 | OK (offset 0) |
| 0251-B-r3 | 1 | 3 | B | 19173 | 2.502 | 6.259 | 20.66 (33.9) | 22 | 17 | 15 | 5 | 0 | 5.880 | 1 1 0 20 0 | OK (offset 0) |
| 0253-B-r4 | 1 | 4 | B | 19103 | 2.491 | 6.820 | 14.07 (29.9) | 35 | 13 | 7 | 0 | 0 | 6.266 | 8 2 12 9 4 | OK (offset 0) |
| 0255-d0-r4 | 1 | 4 | d0 | 19249 | 2.493 | 5.637 | 10.26 (0.7) | 6 | 1 | 1 | 0 | 0 | 5.551 | 2 0 1 1 2 | OK (offset 0) |
| 0257-d0-r5 | 1 | 5 | d0 | 19255 | 2.491 | 5.606 | 6.25 (25.2) | 3 | 0 | 0 | 0 | 0 | 5.577 | 0 1 1 1 0 | OK (offset 0) |
| 0259-B-r5 | 1 | 5 | B | 19196 | 2.498 | 5.670 | 6.05 (48.7) | 2 | 0 | 0 | 0 | 0 | 5.575 | 1 0 0 0 1 | OK (offset 0) |
| 0301-B-r6 | 1 | 6 | B | 19297 | 2.510 | 5.542 | 5.99 (2.6) | 0 | 0 | 0 | 0 | 0 | 5.490 | 0 0 0 0 0 | OK (offset 0) |
| 0303-d0-r6 | 1 | 6 | d0 | 19281 | 2.465 | 5.657 | 6.45 (43.7) | 3 | 0 | 0 | 0 | 0 | 5.633 | 2 0 0 0 1 | OK (offset 0) |

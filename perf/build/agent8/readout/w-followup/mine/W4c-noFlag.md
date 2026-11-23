# W4c: pooled numbers (pool_readout.py)

Base arm `d0`. Kept runs: scored, status OK, valid timing, not excluded, minus --drop 0253-B-r4. A round is (pass, round).
Paired = per round, arm vs base in the same round; % values are exp(mean log ratio) - 1 with a 95 % t-CI; sign count = rounds where the arm is lower (ms, cores) or higher (fps).

| pass | dir | results.csv sha256 | matrix.json sha256 |
|---|---|---|---|
| 1 | `build/agent8/matrix/20261123-0239` | `A4F0ACC2CD2FB49A` | `E2E3E4DAAF7D30C7` |

## Runs per arm

| arm | pass | planned (scored) | timed (OK, valid, not excluded) | kept | cold run |
|---|---|---|---|---|---|
| d0 | 1 | 6 | 6 | 6 | 0239-cold-d0 2.186 ms |
| B | 1 | 6 | 6 | 5 | - |

## pass 1: per arm vs base `d0`

| arm | n | median ms (median of runs) | vs base (pooled medians) | paired median | lower in | fps median | vs base | fps mean | paired fps | CPU cores | paired cores | frames mean (min-max) | band (max-min)/median | CV |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d0 | 6 | 2.468 | - | - | - | 385.3 | - | 391.5 | - | 2.533 | - | 19575 (19249-21090) | 10.0 % | 3.9 % |
| B | 5 | 2.502 | +1.4 % | +3.1 [-1.5, +8.0] | 0/5 (p 0.062) | 383.9 | -0.4 % | 385.1 | -1.9 [-6.1, +2.5] | 2.576 | +0.045 [-0.023, +0.112] | 19258 (19173-19427) | 1.6 % | 0.6 % |

Per-round median ms difference (arm - base):

- B: p1 r1 +0.226, p1 r2 +0.041, p1 r3 +0.051, p1 r5 +0.007, p1 r6 +0.045

Tail (results.csv): mean p99 / p99.9 ms, worst frame, frames over 33 ms; paired p99.9 diff vs base:

| arm | p99 mean | p99.9 mean | p99.9 median | max ms | over 33 ms | paired p99.9 diff ms | higher in |
|---|---|---|---|---|---|---|---|
| d0 | 4.930 | 5.612 | 5.621 | 10.26 | 0 | - | - |
| B | 4.887 | 5.713 | 5.574 | 20.66 | 0 | +0.105 [-0.310, +0.520] | 2/5 (p 1.000) |

Tail (perf.csv windows): frames over X ms per minute (mean of runs), totals, k-th largest frame (median of runs), time share over 6 ms:

| arm | runs | >6 ms/min | >8 | >10 | >16.7 | >33 | total >10 / >16.7 / >33 | runs with >10 | top5 ms | top25 ms | top50 ms | share >6 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d0 | 6 | 3.40 | 0.20 | 0.20 | 0.00 | 0.00 | 1 / 0 / 0 | 1 | 5.935 | 5.564 | 5.350 | 0.037 % |
| B | 5 | 6.48 | 4.08 | 3.60 | 1.20 | 0.00 | 15 / 5 / 0 | 1 | 5.872 | 5.511 | 5.336 | 0.124 % |

| pair (A - B) | >6 ms/min diff [CI] | A higher in | >8 diff | A higher in | >10 diff | top25 diff ms | A higher in | top5 diff ms | A higher in |
|---|---|---|---|---|---|---|---|---|---|
| B-d0 | +3.84 [-11.15, +18.83] | 2/5 (p 1.000) | +4.08 [-7.25, +15.41] | 1/1 (p 1.000) | +3.60 [-6.39, +13.59] | +0.019 [-0.232, +0.270] | 1/5 (p 0.375) | +2.510 [-4.620, +9.641] | 2/5 (p 1.000) |

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

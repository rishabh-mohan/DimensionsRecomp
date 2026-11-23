# W4c: pooled numbers (pool_readout.py)

Base arm `d0`. Kept runs: scored, status OK, valid timing, not excluded. A round is (pass, round).
Paired = per round, arm vs base in the same round; % values are exp(mean log ratio) - 1 with a 95 % t-CI; sign count = rounds where the arm is lower (ms, cores) or higher (fps).

| pass | dir | results.csv sha256 | matrix.json sha256 |
|---|---|---|---|
| 1 | `build/agent8/matrix/20261123-0239` | `A4F0ACC2CD2FB49A` | `E2E3E4DAAF7D30C7` |

## Runs per arm

| arm | pass | planned (scored) | timed (OK, valid, not excluded) | kept | cold run |
|---|---|---|---|---|---|
| d0 | 1 | 6 | 6 | 6 | 0239-cold-d0 2.186 ms |
| B | 1 | 6 | 6 | 6 | - |

## pass 1: per arm vs base `d0`

| arm | n | median ms (median of runs) | vs base (pooled medians) | paired median | lower in | fps median | vs base | fps mean | paired fps | CPU cores | paired cores | frames mean (min-max) | band (max-min)/median | CV |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d0 | 6 | 2.468 | - | - | - | 385.3 | - | 391.5 | - | 2.533 | - | 19575 (19249-21090) | 10.0 % | 3.9 % |
| B | 6 | 2.500 | +1.3 % | +2.6 [-1.2, +6.5] | 1/6 (p 0.219) | 383.9 | -0.4 % | 384.6 | -1.7 [-4.9, +1.7] | 2.596 | +0.063 [-0.007, +0.133] | 19232 (19103-19427) | 1.6 % | 0.6 % |

Per-round median ms difference (arm - base):

- B: p1 r1 +0.226, p1 r2 +0.041, p1 r3 +0.051, p1 r4 -0.002, p1 r5 +0.007, p1 r6 +0.045

Tail (results.csv): mean p99 / p99.9 ms, worst frame, frames over 33 ms; paired p99.9 diff vs base:

| arm | p99 mean | p99.9 mean | p99.9 median | max ms | over 33 ms | paired p99.9 diff ms | higher in |
|---|---|---|---|---|---|---|---|
| d0 | 4.930 | 5.612 | 5.621 | 10.26 | 0 | - | - |
| B | 4.901 | 5.897 | 5.622 | 20.66 | 0 | +0.285 [-0.274, +0.843] | 3/6 (p 1.000) |

Tail (perf.csv windows): frames over X ms per minute (mean of runs), totals, k-th largest frame (median of runs), time share over 6 ms:

| arm | runs | >6 ms/min | >8 | >10 | >16.7 | >33 | total >10 / >16.7 / >33 | runs with >10 | top5 ms | top25 ms | top50 ms | share >6 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d0 | 6 | 3.40 | 0.20 | 0.20 | 0.00 | 0.00 | 1 / 0 / 0 | 1 | 5.935 | 5.564 | 5.350 | 0.037 % |
| B | 6 | 12.40 | 6.00 | 4.40 | 1.00 | 0.00 | 22 / 5 / 0 | 2 | 5.883 | 5.543 | 5.389 | 0.196 % |

| pair (A - B) | >6 ms/min diff [CI] | A higher in | >8 diff | A higher in | >10 diff | top25 diff ms | A higher in | top5 diff ms | A higher in |
|---|---|---|---|---|---|---|---|---|---|
| B-d0 | +9.00 [-8.45, +26.45] | 3/6 (p 1.000) | +5.80 [-3.84, +15.44] | 2/2 (p 0.500) | +4.20 [-3.51, +11.91] | +0.135 [-0.218, +0.488] | 2/6 (p 0.688) | +2.982 [-2.545, +8.509] | 3/6 (p 1.000) |

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

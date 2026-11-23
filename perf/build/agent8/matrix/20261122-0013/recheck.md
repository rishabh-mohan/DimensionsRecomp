# Matrix recheck: <workspace>\build\agent8\matrix\20261122-0013

Window 3: devoff2 (ref) vs baseline, devoff2 + Agent 11 ON bundle, native2 N0 (and devoff2 + Agent 12 ON bundle if it fits). Uncapped, title loop, no input

19 result rows; 16 scored runs kept (0 of them with only benign problems); min window cover 90%.

## Runs

| seq | round | arm | rep | status | kept | median ms | fps | p99 ms | >33 | >100 | window s | marks s | cpu cores | top1 thread busy % (name) | gpu util % | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | d0 | 0 | OK | no | 3.18 | 330.1 | 5.9 | 1 | 1 | 30.0 | 30.0 | 3.02 | - | - | unscored (cold) |
| 2 | 0 | base | 0 | OK | no | 3.87 | 210.9 | 11.2 | 1 | 1 | 30.0 | 43.2 | 3.58 | - | - | unscored (cold) |
| 3 | 0 | n0 | 0 | OK | no | 6.60 | 145.6 | 11.5 | 0 | 0 | 30.0 | 43.4 | 2.44 | - | - | unscored (cold) |
| 4 | 1 | d0 | 1 | OK | yes | 7.05 | 163.6 | 12.3 | 1 | 0 | 50.0 | 175.5 | 3.36 | 86.7 (GPU Commands (F8000018)) | 54 |  |
| 5 | 1 | base | 1 | OK | yes | 7.16 | 160.3 | 12.3 | 0 | 0 | 50.0 | 85.3 | 3.46 | 87.6 (GPU Commands (F8000018)) | 54 |  |
| 6 | 1 | d11 | 1 | OK | yes | 3.40 | 294.6 | 7.5 | 0 | 0 | 50.0 | 229.4 | 3.48 | 82.1 (GPU Commands (F8000018)) | 41 |  |
| 7 | 1 | n0 | 1 | OK | yes | 6.69 | 143.4 | 11.4 | 0 | 0 | 50.0 | 80.7 | 2.44 | 77.1 (Main XThread (F8000024)) | 50 |  |
| 8 | 2 | base | 2 | OK | yes | 7.13 | 160.9 | 12.2 | 0 | 0 | 50.0 | 103.9 | 3.41 | 87.7 (GPU Commands (F8000018)) | 54 |  |
| 9 | 2 | d11 | 2 | OK | yes | 7.11 | 160.3 | 12.6 | 0 | 0 | 50.0 | 67.9 | 3.52 | 85.6 (GPU Commands (F8000018)) | 56 |  |
| 10 | 2 | n0 | 2 | OK | yes | 6.87 | 136.7 | 12.6 | 0 | 0 | 50.0 | 64.4 | 2.55 | 76.9 (Main XThread (F8000024)) | 48 |  |
| 11 | 2 | d0 | 2 | OK | yes | 6.98 | 167.3 | 11.9 | 0 | 0 | 50.0 | 76.5 | 3.62 | 86.2 (GPU Commands (F8000018)) | 56 |  |
| 12 | 3 | d11 | 3 | OK | yes | 7.19 | 157.8 | 12.2 | 0 | 0 | 50.0 | 207.9 | 3.79 | 86.7 (GPU Commands (F8000018)) | 56 |  |
| 13 | 3 | n0 | 3 | OK | yes | 6.55 | 146.6 | 11.0 | 0 | 0 | 50.0 | 41.4 | 2.38 | 73.8 (Main XThread (F8000024)) | 50 |  |
| 14 | 3 | d0 | 3 | OK | yes | 7.10 | 161.5 | 12.4 | 0 | 0 | 50.0 | 60.8 | 3.49 | 87.4 (GPU Commands (F8000018)) | 57 |  |
| 15 | 3 | base | 3 | OK | yes | 7.10 | 160.8 | 12.5 | 0 | 0 | 50.0 | 86.4 | 3.56 | 86.2 (GPU Commands (F8000018)) | 54 |  |
| 16 | 4 | n0 | 4 | OK | yes | 6.72 | 143.1 | 11.3 | 0 | 0 | 50.0 | 37.3 | 2.42 | 74.9 (Main XThread (F8000024)) | 43 |  |
| 17 | 4 | d0 | 4 | OK | yes | 7.09 | 162.1 | 12.2 | 0 | 0 | 50.0 | 93.8 | 3.61 | 87.1 (GPU Commands (F8000018)) | 54 |  |
| 18 | 4 | base | 4 | OK | yes | 7.12 | 160.8 | 12.4 | 0 | 0 | 50.0 | 136.4 | 3.57 | 87.4 (GPU Commands (F8000018)) | 54 |  |
| 19 | 4 | d11 | 4 | OK | yes | 7.16 | 157.5 | 12.3 | 0 | 0 | 50.0 | 113.0 | 3.60 | 86.9 (GPU Commands (F8000018)) | 54 |  |

`marks s` is the wall time between the measure marks (summary.txt `align` line); it should be close to the planned window.

## Arms (kept runs)

| group | arm | ref | n | median of medians (min..max) ms | p99 ms | p99.9 ms | >33 ms per min | >100 ms per min | cpu cores (min..max) | boot s | fps | top1 thread busy % (min..max), n | thread cores | gpu util % mean (p90) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| w3 | d0 | * | 4 | 7.067 (6.977..7.100) | 12.2 | 14.2 | 0.3 | 0.00 | 3.55 (3.36..3.62) | 8.5 | 162.9 | 86.9 (86.2..87.4), 4 | 3.48 | 55 (60) |
| w3 | base |  | 4 | 7.123 (7.101..7.155) | 12.3 | 14.5 | 0.0 | 0.00 | 3.51 (3.41..3.57) | 8.5 | 160.8 | 87.5 (86.2..87.7), 4 | 3.49 | 54 (59) |
| w3 | d11 |  | 4 | 7.135 (3.401..7.187) | 12.3 | 14.3 | 0.0 | 0.00 | 3.56 (3.48..3.79) | 21.6 | 159.0 | 86.2 (82.1..86.9), 4 | 3.53 | 55 (58) |
| w3 | n0 |  | 4 | 6.707 (6.555..6.875) | 11.3 | 14.1 | 0.0 | 0.00 | 2.43 (2.38..2.55) | 19.1 | 143.2 | 75.9 (73.8..77.1), 4 | 2.43 | 49 (52) |

## Deltas against each group reference

| group | arm | vs | delta median ms (%) | paired by round: median delta (min..max), rounds faster | delta p99 ms | delta >33/min | delta cpu cores | delta fps % | paired delta top1 busy pts (n) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| w3 | base | d0 | 0.056 (0.8%) | 0.071 (0.001..0.149), 0 of 4 | 0.1 | -0.3 | -0.04 | -1.3 | 0.6 (4) | SLOWER: every run above the reference range |
| w3 | d11 | d0 | 0.068 (1.0%) | 0.078 (-3.646..0.137), 1 of 4 | 0.0 | -0.3 | 0.00 | -2.3 | -0.7 (4) | within noise (ranges overlap) |
| w3 | n0 | d0 | -0.360 (-5.1%) | -0.360 (-0.545..-0.102), 4 of 4 | -0.9 | -0.3 | -1.12 | -12.1 | -10.9 (4) | FASTER: every run below the reference range |

## One-line results

- base vs d0: median 7.12 vs 7.07 ms (delta 0.06, 0.8%; paired 0.07, 0/4 rounds faster), fps 160.8 vs 162.9 (-1.3%), p99 12.3 vs 12.2, >33/min 0.0 vs 0.3, >100/min 0.00 vs 0.00, cpu 3.51 vs 3.55 cores, top1 thread busy 87.5 vs 86.9 % (paired 0.6); ref range 6.98..7.10; n 4/4; SLOWER: every run above the reference range
- d11 vs d0: median 7.13 vs 7.07 ms (delta 0.07, 1.0%; paired 0.08, 1/4 rounds faster), fps 159.0 vs 162.9 (-2.3%), p99 12.3 vs 12.2, >33/min 0.0 vs 0.3, >100/min 0.00 vs 0.00, cpu 3.56 vs 3.55 cores, top1 thread busy 86.2 vs 86.9 % (paired -0.7); ref range 6.98..7.10; n 4/4; within noise (ranges overlap)
- n0 vs d0: median 6.71 vs 7.07 ms (delta -0.36, -5.1%; paired -0.36, 4/4 rounds faster), fps 143.2 vs 162.9 (-12.1%), p99 11.3 vs 12.2, >33/min 0.0 vs 0.3, >100/min 0.00 vs 0.00, cpu 2.43 vs 3.55 cores, top1 thread busy 75.9 vs 86.9 % (paired -10.9); ref range 6.98..7.10; n 4/4; FASTER: every run below the reference range

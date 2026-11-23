# Matrix recheck: <workspace>\build\agent8\matrix\20261122-1541

Window 4 (Agent 8, session 3): B = devoffB (codegen B) vs d0 = devoff2 (primary), then d3 = devoff3; W4b adds d11t = window 3's d11 + REX_TIMER_WAIT_BLOCKING=1

17 result rows; 15 scored runs kept (0 of them with only benign problems); min window cover 90%; 0 scored runs flagged excluded (dropped); 16 scored runs with the slow state in their window (E-cores < 800 MHz for 3+ samples; kept; --drop-slow drops them).

## Runs

| seq | round | arm | rep | status | kept | median ms | fps | p99 ms | >33 | >100 | window s | marks s | ff->win s | light | slow | cpu cores | top1 thread busy % (name) | gpu util % | flags | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | d0 | 0 | OK | no | 3.08 | 325.9 | 5.9 | 0 | 0 | 30.0 | 30.0 | 60.0 | 0.923 | no | 2.92 | - | - | light_share_high | unscored (cold) |
| 2 | 1 | d0 | 1 | OK | yes | 3.23 | 256.4 | 10.8 | 0 | 0 | 50.0 | 50.0 | 60.0 | 0.807 | 93 s / 35% ! | 3.37 | 89.0 (GPU Commands (F8000018)) | 68 | light_share_high |  |
| 3 | 1 | B | 1 | OK | yes | 2.88 | 317.1 | 9.4 | 0 | 0 | 50.0 | 50.0 | 60.0 | 0.870 | 94 s / 32% ! | 3.14 | 79.5 (GPU Commands (F8000018)) | 75 | light_share_high |  |
| 4 | 1 | d3 | 1 | OK | yes | 3.35 | 231.0 | 11.1 | 0 | 0 | 50.0 | 50.0 | 60.0 | 0.671 | 76 s / 70% ! | 3.45 | 84.0 (GPU Commands (F8000018)) | 64 | light_share_high |  |
| 5 | 1 | d11t | 1 | OK | yes | 3.86 | 206.4 | 11.5 | 0 | 0 | 50.0 | 50.0 | 60.0 | 0.560 | 61 s / 96% ! | 3.00 | 83.2 (GPU Commands (F8000018)) | 64 | - |  |
| 6 | 2 | B | 2 | OK | no | 3.53 | 234.5 | 11.5 | 0 | 0 | 50.0 | 50.0 | 60.0 | 0.654 | 1 s / 64% ! | 3.43 | 86.5 (GPU Commands (F8000018)) | 68 | light_share_high build_procs_warmup build_procs_window | not timing (build processes: clang++:34584 clang++:36068 clang++:6544) |
| 7 | 2 | d3 | 2 | OK | yes | 2.89 | 298.6 | 9.7 | 0 | 0 | 50.0 | 50.0 | 60.0 | 0.824 | 84 s / 54% ! | 3.18 | 78.7 (Main XThread (F800002C)) | 71 | light_share_high |  |
| 8 | 2 | d11t | 2 | OK | yes | 3.57 | 220.6 | 12.2 | 0 | 0 | 50.0 | 50.0 | 60.0 | 0.599 | 63 s / 96% ! | 2.94 | 86.1 (GPU Commands (F8000018)) | 63 | - |  |
| 9 | 2 | d0 | 2 | OK | yes | 3.07 | 270.4 | 9.9 | 0 | 0 | 50.0 | 50.0 | 60.0 | 0.746 | 72 s / 76% ! | 3.34 | 79.8 (GPU Commands (F8000018)) | 71 | light_share_high |  |
| 10 | 3 | d3 | 3 | OK | yes | 4.26 | 198.4 | 12.9 | 0 | 0 | 50.0 | 50.0 | 60.0 | 0.513 | 54 s / 100% ! | 3.52 | 85.6 (GPU Commands (F8000018)) | 58 | - |  |
| 11 | 3 | d11t | 3 | OK | yes | 3.02 | 277.2 | 9.9 | 0 | 0 | 50.0 | 50.0 | 60.0 | 0.749 | 1 s / 96% ! | 2.81 | 77.4 (GPU Commands (F8000018)) | 73 | light_share_high |  |
| 12 | 3 | d0 | 3 | OK | yes | 3.56 | 223.1 | 10.7 | 0 | 0 | 50.0 | 50.0 | 60.0 | 0.600 | 2 s / 100% ! | 3.53 | 83.1 (GPU Commands (F8000018)) | 67 | light_share_high |  |
| 13 | 3 | B | 3 | OK | yes | 3.44 | 230.8 | 11.0 | 0 | 0 | 50.0 | 50.0 | 60.0 | 0.626 | 4 s / 100% ! | 3.48 | 84.8 (GPU Commands (F8000018)) | 70 | light_share_high |  |
| 14 | 4 | d11t | 4 | OK | yes | 3.16 | 254.9 | 10.4 | 0 | 0 | 50.0 | 50.0 | 60.0 | 0.702 | 1 s / 100% ! | 2.90 | 80.7 (GPU Commands (F8000018)) | 69 | light_share_high |  |
| 15 | 4 | d0 | 4 | OK | yes | 3.73 | 213.9 | 11.0 | 0 | 0 | 50.0 | 50.0 | 60.0 | 0.565 | 4 s / 100% ! | 3.52 | 83.2 (GPU Commands (F8000018)) | 68 | - |  |
| 16 | 4 | B | 4 | OK | yes | 3.03 | 275.8 | 10.0 | 0 | 0 | 50.0 | 50.0 | 60.0 | 0.743 | 3 s / 90% ! | 3.35 | 79.0 (GPU Commands (F8000018)) | 73 | light_share_high |  |
| 17 | 4 | d3 | 4 | OK | yes | 3.08 | 266.8 | 9.9 | 0 | 0 | 50.0 | 50.0 | 60.0 | 0.723 | 1 s / 98% ! | 3.37 | 77.8 (GPU Commands (F8000018)) | 68 | light_share_high |  |

`marks s` is the wall time between the measure marks (summary.txt `align` line); it should be close to the planned window. `ff->win s` is first-frame signal to window start (floor: min_window_after_ff_s); `light` is the share of window frames under light_ms; flags ending in `!` are excluding flags. `slow` is the slow-state onset in s after the first-frame signal / the share of window sys.csv samples with the E-cores under 800 MHz; `!` = a stretch of 3+ such samples overlaps the window (Agent 11: not a result); `no` = never; `-` = no sys.csv.

## Arms (kept runs)

| group | arm | ref | n | median of medians (min..max) ms | p99 ms | p99.9 ms | >33 ms per min | >100 ms per min | cpu cores (min..max) | boot s | fps | top1 thread busy % (min..max), n | thread cores | gpu util % mean (p90) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| w4 | d0 | * | 4 | 3.399 (3.069..3.734) | 10.7 | 13.4 | 0.0 | 0.00 | 3.44 (3.34..3.53) | 4.0 | 239.7 | 83.2 (79.8..89.0), 4 | 3.45 | 68 (78) |
| w4 | B |  | 3 | 3.033 (2.884..3.435) | 10.0 | 12.3 | 0.0 | 0.00 | 3.35 (3.14..3.48) | 4.0 | 275.8 | 79.5 (79.0..84.8), 3 | 3.35 | 73 (81) |
| w4 | d3 |  | 4 | 3.215 (2.894..4.264) | 10.5 | 13.1 | 0.0 | 0.00 | 3.41 (3.18..3.52) | 5.5 | 248.9 | 81.3 (77.8..85.6), 4 | 3.42 | 66 (80) |
| w4 | d11t |  | 4 | 3.363 (3.025..3.857) | 10.9 | 14.1 | 0.0 | 0.00 | 2.92 (2.81..3.00) | 4.5 | 237.7 | 82.0 (77.4..86.1), 4 | 2.92 | 67 (76) |

## Deltas against each group reference

| group | arm | vs | delta median ms (%) | paired by round: median delta (min..max), rounds faster | delta p99 ms | delta >33/min | delta cpu cores | delta fps % | paired delta top1 busy pts (n) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| w4 | B | d0 | -0.366 (-10.8%) | -0.350 (-0.701..-0.130), 3 of 3 | -0.7 | 0.0 | -0.09 | 15.1 | -4.2 (3) | within noise (ranges overlap) |
| w4 | d3 | d0 | -0.185 (-5.4%) | -0.031 (-0.652..0.699), 2 of 4 | -0.2 | 0.0 | -0.03 | 3.8 | -3.0 (4) | within noise (ranges overlap) |
| w4 | d11t | d0 | -0.036 (-1.1%) | -0.020 (-0.576..0.623), 2 of 4 | 0.2 | 0.0 | -0.52 | -0.8 | -4.1 (4) | within noise (ranges overlap) |

## One-line results

- B vs d0: median 3.03 vs 3.40 ms (delta -0.37, -10.8%; paired -0.35, 3/3 rounds faster), fps 275.8 vs 239.7 (15.1%), p99 10.0 vs 10.7, >33/min 0.0 vs 0.0, >100/min 0.00 vs 0.00, cpu 3.35 vs 3.44 cores, top1 thread busy 79.5 vs 83.2 % (paired -4.2); ref range 3.07..3.73; n 3/4; within noise (ranges overlap)
- d3 vs d0: median 3.21 vs 3.40 ms (delta -0.18, -5.4%; paired -0.03, 2/4 rounds faster), fps 248.9 vs 239.7 (3.8%), p99 10.5 vs 10.7, >33/min 0.0 vs 0.0, >100/min 0.00 vs 0.00, cpu 3.41 vs 3.44 cores, top1 thread busy 81.3 vs 83.2 % (paired -3.0); ref range 3.07..3.73; n 4/4; within noise (ranges overlap)
- d11t vs d0: median 3.36 vs 3.40 ms (delta -0.04, -1.1%; paired -0.02, 2/4 rounds faster), fps 237.7 vs 239.7 (-0.8%), p99 10.9 vs 10.7, >33/min 0.0 vs 0.0, >100/min 0.00 vs 0.00, cpu 2.92 vs 3.44 cores, top1 thread busy 82.0 vs 83.2 % (paired -4.1); ref range 3.07..3.73; n 4/4; within noise (ranges overlap)

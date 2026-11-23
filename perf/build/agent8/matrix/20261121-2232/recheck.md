# Matrix recheck: <workspace>\build\agent8\matrix\20261121-2232

Quiet window 1: baseline-bin vs devoff1-bin, both at defaults. Title/attract loop, no input needed

12 result rows; 10 scored runs kept (1 of them with only benign problems); min window cover 90%.

## Runs

| seq | round | arm | rep | status | kept | median ms | p99 ms | >33 | >100 | window s | marks s | cpu cores | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | base | 0 | OK | no | 16.66 | 18.8 | 1 | 1 | 30.0 | 30.0 | 2.15 | unscored (cold) |
| 2 | 0 | r0 | 0 | OK | no | 16.66 | 19.7 | 0 | 0 | 30.0 | 30.0 | 2.13 | unscored (cold) |
| 3 | 1 | base | 1 | OK | yes | 16.66 | 19.4 | 0 | 0 | 60.0 | 60.0 | 2.22 |  |
| 4 | 1 | r0 | 1 | OK | yes | 16.67 | 19.5 | 0 | 0 | 60.0 | 60.0 | 2.29 |  |
| 5 | 2 | r0 | 2 | OK | yes | 16.67 | 23.9 | 0 | 0 | 60.0 | 60.0 | 2.42 |  |
| 6 | 2 | base | 2 | OK | yes | 16.66 | 18.6 | 0 | 0 | 60.0 | 60.0 | 2.13 |  |
| 7 | 3 | base | 3 | OK | yes | 16.67 | 22.5 | 0 | 0 | 60.0 | 60.5 | 2.29 |  |
| 8 | 3 | r0 | 3 | PROBLEM | yes | 16.66 | 21.2 | 0 | 0 | 60.0 | 60.0 | 2.41 | foreign dumps: fakedimensions.exe.48456.dmp |
| 9 | 4 | r0 | 4 | OK | yes | 16.66 | 19.4 | 0 | 0 | 60.0 | 60.0 | 2.09 |  |
| 10 | 4 | base | 4 | OK | yes | 16.67 | 18.2 | 0 | 0 | 60.0 | 60.0 | 2.05 |  |
| 11 | 5 | base | 5 | OK | yes | 16.66 | 18.1 | 0 | 0 | 60.0 | 60.0 | 1.91 |  |
| 12 | 5 | r0 | 5 | OK | yes | 16.66 | 19.5 | 1 | 0 | 60.0 | 60.0 | 2.00 |  |

`marks s` is the wall time between the measure marks (summary.txt `align` line); it should be close to the planned window.

## Arms (kept runs)

| group | arm | ref | n | median of medians (min..max) ms | p99 ms | p99.9 ms | >33 ms per min | >100 ms per min | cpu cores (min..max) | boot s | fps |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ab | base | * | 5 | 16.661 (16.656..16.666) | 18.6 | 20.8 | 0.0 | 0.00 | 2.13 (1.91..2.29) | 7.0 | 60.0 |
| ab | r0 |  | 5 | 16.665 (16.657..16.670) | 19.5 | 23.8 | 0.2 | 0.00 | 2.29 (2.00..2.42) | 8.0 | 60.0 |

## Deltas against each group reference

| group | arm | vs | delta median ms (%) | paired by round: median delta (min..max), rounds faster | delta p99 ms | delta >33/min | delta cpu cores | verdict |
|---|---|---|---|---|---|---|---|---|
| ab | r0 | base | 0.004 (0.0%) | 0.004 (-0.009..0.014), 2 of 5 | 0.9 | 0.2 | 0.16 | within noise (ranges overlap) |

## One-line results

- r0 vs base: median 16.66 vs 16.66 ms (delta 0.00, 0.0%; paired 0.00, 2/5 rounds faster), p99 19.5 vs 18.6, >33/min 0.2 vs 0.0, >100/min 0.00 vs 0.00, cpu 2.29 vs 2.13 cores; ref range 16.66..16.67; n 5/5; within noise (ranges overlap)

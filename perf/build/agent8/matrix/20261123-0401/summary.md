# Timing matrix: Window 9 (Agent 8, run-2 task #7 follow-up): #24 GPU-wait back-off sweep on devoff4b (S4b + S4c). off (back-off OFF, nothing set) vs Q = 0 / 125 / 250 / 500 us (LEGO_GPU_WAIT_BACKOFF_US) with spin 30 us

- matrix: <workspace>\bench\agent8\run\matrix-window9.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261123-0401
- started 2026-11-23 04:01, ended 04:44; 21 runs (21 OK), 20 scored; desktop WinSta0\Default
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 20 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

## Group w9: ref off (ref arm of the group), noise band +-5.8 %

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| off | 4/4 | 4 | 0 | 2.46 (2.33..2.47) | 5.8 | 4.99 | 5.58 | 0 | 0 | 384.88 | 2.5 |  |  |  | ref |
| q0 | 4/4 | 4 | 0 | 2.47 (2.46..2.47) | 0.3 | 4.93 | 5.59 | 0 | 0 | 385.47 | 2.47 | 0.3 | -1.2 |  | within noise |
| q125 | 4/4 | 4 | 0 | 2.39 (2.3..2.51) | 9 | 4.81 | 5.56 | 0 | 0 | 378.91 | 1.96 | -2.8 | -3.4 |  | within noise |
| q250 | 4/4 | 4 | 0 | 2.37 (2.32..2.46) | 5.7 | 4.69 | 5.58 | 0.3 | 0 | 382.78 | 1.95 | -3.9 | -6 |  | within noise |
| q500 | 4/4 | 4 | 0 | 2.32 (2.31..2.36) | 2 | 4.68 | 5.4 | 0 | 0 | 389.24 | 1.8 | -5.9 | -6.3 |  | FASTER (outside noise) |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | off | 0 | OK | True |  | 4.01 | 60 | 13502 | 1.984 | 4.892 | 0 | 0 | 2.484 | 0.976 | wm_close 0.5 s | light_share_high | 0401-cold-off |  |
| 2 | 1 | off | 1 | OK | True |  | 4 | 60 | 20446 | 2.325 | 4.912 | 0 | 0 | 2.438 | 0.974 | wm_close 0.5 s | light_share_high | 0403-off-r1 |  |
| 3 | 1 | q0 | 1 | OK | True |  | 4 | 60 | 19291 | 2.465 | 4.913 | 0 | 0 | 2.493 | 0.97 | wm_close 0.5 s | light_share_high | 0405-q0-r1 |  |
| 4 | 1 | q125 | 1 | OK | True |  | 4.01 | 60 | 18250 | 2.477 | 5.364 | 0 | 0 | 2.147 | 0.956 | wm_close 0.6 s | light_share_high | 0407-q125-r1 |  |
| 5 | 1 | q250 | 1 | OK | True |  | 5.01 | 60 | 18909 | 2.46 | 4.867 | 1 | 0 | 2.106 | 0.976 | wm_close 0.5 s | light_share_high | 0409-q250-r1 |  |
| 6 | 1 | q500 | 1 | OK | True |  | 4.01 | 60 | 19435 | 2.316 | 4.622 | 0 | 0 | 1.725 | 0.985 | wm_close 0.5 s | light_share_high | 0411-q500-r1 |  |
| 7 | 2 | q0 | 2 | OK | True |  | 4.02 | 60 | 19258 | 2.472 | 4.896 | 0 | 0 | 2.456 | 0.97 | wm_close 0.6 s | light_share_high | 0413-q0-r2 |  |
| 8 | 2 | q125 | 2 | OK | True |  | 4 | 60 | 19549 | 2.295 | 4.453 | 0 | 0 | 1.755 | 0.992 | wm_close 0.4 s | light_share_high | 0415-q125-r2 |  |
| 9 | 2 | q250 | 2 | OK | True |  | 4 | 60 | 18958 | 2.377 | 4.743 | 0 | 0 | 1.934 | 0.981 | wm_close 0.5 s | light_share_high | 0417-q250-r2 |  |
| 10 | 2 | q500 | 2 | OK | True |  | 4.02 | 60 | 19291 | 2.356 | 4.726 | 0 | 0 | 2.026 | 0.981 | wm_close 0.5 s | light_share_high | 0419-q500-r2 |  |
| 11 | 2 | off | 2 | OK | True |  | 5.01 | 60 | 19108 | 2.469 | 5.101 | 0 | 0 | 2.545 | 0.962 | wm_close 0.5 s | light_share_high | 0421-off-r2 |  |
| 12 | 3 | q125 | 3 | OK | True |  | 4.01 | 60 | 18422 | 2.51 | 5.118 | 0 | 0 | 2.133 | 0.964 | wm_close 0.6 s | light_share_high | 0423-q125-r3 |  |
| 13 | 3 | q250 | 3 | OK | True |  | 4 | 60 | 19321 | 2.356 | 4.635 | 0 | 0 | 1.981 | 0.985 | wm_close 0.5 s | light_share_high | 0425-q250-r3 |  |
| 14 | 3 | q500 | 3 | OK | True |  | 4.02 | 60 | 19490 | 2.309 | 4.665 | 0 | 0 | 1.731 | 0.983 | wm_close 0.5 s | light_share_high | 0427-q500-r3 |  |
| 15 | 3 | off | 3 | OK | True |  | 4.02 | 60 | 19260 | 2.458 | 4.992 | 0 | 0 | 2.519 | 0.964 | wm_close 0.5 s | light_share_high | 0429-off-r3 |  |
| 16 | 3 | q0 | 3 | OK | True |  | 4.01 | 60 | 19360 | 2.468 | 4.944 | 0 | 0 | 2.457 | 0.969 | wm_close 0.4 s | light_share_high | 0431-q0-r3 |  |
| 17 | 4 | q250 | 4 | OK | True |  | 4.01 | 60 | 19457 | 2.324 | 4.529 | 0 | 0 | 1.789 | 0.988 | wm_close 0.5 s | light_share_high | 0433-q250-r4 |  |
| 18 | 4 | q500 | 4 | OK | True |  | 4 | 60 | 19492 | 2.319 | 4.685 | 0 | 0 | 1.71 | 0.983 | wm_close 0.4 s | light_share_high | 0435-q500-r4 |  |
| 19 | 4 | off | 4 | OK | True |  | 4.01 | 60 | 19229 | 2.466 | 4.982 | 0 | 0 | 2.49 | 0.966 | wm_close 0.5 s | light_share_high | 0438-off-r4 |  |
| 20 | 4 | q0 | 4 | OK | True |  | 4.01 | 60 | 19201 | 2.473 | 4.964 | 0 | 0 | 2.46 | 0.968 | wm_close 0.5 s | light_share_high | 0440-q0-r4 |  |
| 21 | 4 | q125 | 4 | OK | True |  | 4.01 | 60 | 19469 | 2.309 | 4.512 | 0 | 0 | 1.791 | 0.989 | wm_close 0.6 s | light_share_high | 0442-q125-r4 |  |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | off | cold |  | light_share_high | 0401-cold-off |
| 2 | off | 1 |  | light_share_high | 0403-off-r1 |
| 3 | q0 | 1 |  | light_share_high | 0405-q0-r1 |
| 4 | q125 | 1 |  | light_share_high | 0407-q125-r1 |
| 5 | q250 | 1 |  | light_share_high | 0409-q250-r1 |
| 6 | q500 | 1 |  | light_share_high | 0411-q500-r1 |
| 7 | q0 | 2 |  | light_share_high | 0413-q0-r2 |
| 8 | q125 | 2 |  | light_share_high | 0415-q125-r2 |
| 9 | q250 | 2 |  | light_share_high | 0417-q250-r2 |
| 10 | q500 | 2 |  | light_share_high | 0419-q500-r2 |
| 11 | off | 2 |  | light_share_high | 0421-off-r2 |
| 12 | q125 | 3 |  | light_share_high | 0423-q125-r3 |
| 13 | q250 | 3 |  | light_share_high | 0425-q250-r3 |
| 14 | q500 | 3 |  | light_share_high | 0427-q500-r3 |
| 15 | off | 3 |  | light_share_high | 0429-off-r3 |
| 16 | q0 | 3 |  | light_share_high | 0431-q0-r3 |
| 17 | q250 | 4 |  | light_share_high | 0433-q250-r4 |
| 18 | q500 | 4 |  | light_share_high | 0435-q500-r4 |
| 19 | off | 4 |  | light_share_high | 0438-off-r4 |
| 20 | q0 | 4 |  | light_share_high | 0440-q0-r4 |
| 21 | q125 | 4 |  | light_share_high | 0442-q125-r4 |

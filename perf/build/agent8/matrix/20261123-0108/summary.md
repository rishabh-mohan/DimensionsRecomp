# Timing matrix: Window 9 (Agent 8, run-2 task #7 follow-up): #24 GPU-wait back-off sweep on devoff4b (S4b + S4c). off (back-off OFF, nothing set) vs Q = 0 / 125 / 250 / 500 us (LEGO_GPU_WAIT_BACKOFF_US) with spin 30 us

- matrix: <workspace>\bench\agent8\run\matrix-window9.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261123-0108
- started 2026-11-23 01:08, ended 01:51; 21 runs (21 OK), 20 scored; desktop WinSta0\Default
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 20 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

## Group w9: ref off (ref arm of the group), noise band +-16.4 %

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| off | 4/4 | 4 | 0 | 2.46 (2.08..2.49) | 16.4 | 4.98 | 5.63 | 0 | 0 | 386.2 | 2.51 |  |  |  | ref |
| q0 | 4/4 | 4 | 0 | 2.48 (2.34..2.49) | 6 | 4.91 | 5.61 | 0 | 0 | 386.97 | 2.49 | 0.9 | -1.4 |  | within noise |
| q125 | 4/4 | 4 | 0 | 2.31 (2.3..2.32) | 1 | 4.47 | 5.01 | 0 | 0 | 389.49 | 1.82 | -6.1 | -10.1 |  | within noise |
| q250 | 4/4 | 4 | 0 | 2.31 (2.29..2.34) | 2.1 | 4.5 | 5.11 | 0 | 0 | 389.34 | 1.77 | -5.9 | -9.6 |  | within noise |
| q500 | 4/4 | 4 | 0 | 2.31 (2.3..2.32) | 1 | 4.62 | 5.52 | 0 | 0 | 390.08 | 1.72 | -6 | -7.1 |  | within noise |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | off | 0 | OK | True |  | 3.02 | 60 | 13154 | 2.143 | 4.969 | 0 | 0 | 2.336 | 0.976 | wm_close 0.5 s | light_share_high | 0108-cold-off |  |
| 2 | 1 | off | 1 | OK | True |  | 3.01 | 60 | 22187 | 2.083 | 4.742 | 0 | 0 | 2.515 | 0.982 | wm_close 0.5 s | light_share_high | 0110-off-r1 |  |
| 3 | 1 | q0 | 1 | OK | True |  | 3.01 | 60 | 20730 | 2.342 | 4.836 | 0 | 0 | 2.503 | 0.976 | wm_close 0.5 s | light_share_high | 0112-q0-r1 |  |
| 4 | 1 | q125 | 1 | OK | True |  | 3 | 60 | 19775 | 2.297 | 4.459 | 0 | 0 | 1.819 | 0.992 | wm_close 0.5 s | light_share_high | 0114-q125-r1 |  |
| 5 | 1 | q250 | 1 | OK | True |  | 3 | 60 | 19496 | 2.293 | 4.469 | 0 | 0 | 1.709 | 0.992 | wm_close 0.5 s | light_share_high | 0116-q250-r1 |  |
| 6 | 1 | q500 | 1 | OK | True |  | 3.02 | 60 | 19535 | 2.297 | 4.59 | 0 | 0 | 1.704 | 0.986 | wm_close 0.5 s | light_share_high | 0118-q500-r1 |  |
| 7 | 2 | q0 | 2 | OK | True |  | 3.01 | 60 | 19424 | 2.475 | 4.897 | 0 | 0 | 2.49 | 0.97 | wm_close 0.6 s | light_share_high | 0120-q0-r2 |  |
| 8 | 2 | q125 | 2 | OK | True |  | 3.02 | 60 | 19388 | 2.319 | 4.54 | 0 | 0 | 1.893 | 0.988 | wm_close 0.5 s | light_share_high | 0122-q125-r2 |  |
| 9 | 2 | q250 | 2 | OK | True |  | 3.02 | 60 | 19306 | 2.341 | 4.637 | 0 | 0 | 1.909 | 0.984 | wm_close 0.5 s | light_share_high | 0124-q250-r2 |  |
| 10 | 2 | q500 | 2 | OK | True |  | 3.01 | 60 | 19505 | 2.31 | 4.623 | 0 | 0 | 1.702 | 0.986 | wm_close 0.5 s | light_share_high | 0126-q500-r2 |  |
| 11 | 2 | off | 2 | OK | True |  | 3.02 | 60 | 19291 | 2.463 | 4.997 | 0 | 0 | 2.521 | 0.964 | wm_close 3.2 s | light_share_high | 0128-off-r2 |  |
| 12 | 3 | q125 | 3 | OK | True |  | 3.01 | 60 | 19483 | 2.296 | 4.465 | 0 | 0 | 1.728 | 0.992 | wm_close 0.5 s | light_share_high | 0131-q125-r3 |  |
| 13 | 3 | q250 | 3 | OK | True |  | 3.01 | 60 | 19485 | 2.302 | 4.455 | 0 | 0 | 1.732 | 0.992 | wm_close 0.5 s | light_share_high | 0133-q250-r3 |  |
| 14 | 3 | q500 | 3 | OK | True |  | 3.01 | 60 | 19472 | 2.319 | 4.619 | 0 | 0 | 1.729 | 0.985 | wm_close 0.5 s | light_share_high | 0135-q500-r3 |  |
| 15 | 3 | off | 3 | OK | True |  | 3.01 | 60 | 19155 | 2.487 | 4.965 | 0 | 0 | 2.522 | 0.968 | wm_close 0.5 s | light_share_high | 0137-off-r3 |  |
| 16 | 3 | q0 | 3 | OK | True |  | 3.01 | 60 | 19100 | 2.49 | 5.017 | 0 | 0 | 2.486 | 0.967 | wm_close 0.6 s | light_share_high | 0139-q0-r3 |  |
| 17 | 4 | q250 | 4 | OK | True |  | 3 | 60 | 19451 | 2.324 | 4.524 | 0 | 0 | 1.727 | 0.989 | wm_close 0.5 s | light_share_high | 0141-q250-r4 |  |
| 18 | 4 | q500 | 4 | OK | True |  | 3.01 | 60 | 19504 | 2.31 | 4.673 | 0 | 0 | 1.728 | 0.983 | wm_close 0.5 s | light_share_high | 0143-q500-r4 |  |
| 19 | 4 | off | 4 | OK | True |  | 3.01 | 60 | 19330 | 2.451 | 4.988 | 0 | 0 | 2.497 | 0.966 | wm_close 0.5 s | light_share_high | 0145-off-r4 |  |
| 20 | 4 | q0 | 4 | OK | True |  | 3.01 | 60 | 19274 | 2.483 | 4.916 | 0 | 0 | 2.48 | 0.969 | wm_close 0.5 s | light_share_high | 0147-q0-r4 |  |
| 21 | 4 | q125 | 4 | OK | True |  | 3.02 | 60 | 19468 | 2.315 | 4.483 | 0 | 0 | 1.856 | 0.991 | wm_close 0.5 s | light_share_high | 0149-q125-r4 |  |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | off | cold |  | light_share_high | 0108-cold-off |
| 2 | off | 1 |  | light_share_high | 0110-off-r1 |
| 3 | q0 | 1 |  | light_share_high | 0112-q0-r1 |
| 4 | q125 | 1 |  | light_share_high | 0114-q125-r1 |
| 5 | q250 | 1 |  | light_share_high | 0116-q250-r1 |
| 6 | q500 | 1 |  | light_share_high | 0118-q500-r1 |
| 7 | q0 | 2 |  | light_share_high | 0120-q0-r2 |
| 8 | q125 | 2 |  | light_share_high | 0122-q125-r2 |
| 9 | q250 | 2 |  | light_share_high | 0124-q250-r2 |
| 10 | q500 | 2 |  | light_share_high | 0126-q500-r2 |
| 11 | off | 2 |  | light_share_high | 0128-off-r2 |
| 12 | q125 | 3 |  | light_share_high | 0131-q125-r3 |
| 13 | q250 | 3 |  | light_share_high | 0133-q250-r3 |
| 14 | q500 | 3 |  | light_share_high | 0135-q500-r3 |
| 15 | off | 3 |  | light_share_high | 0137-off-r3 |
| 16 | q0 | 3 |  | light_share_high | 0139-q0-r3 |
| 17 | q250 | 4 |  | light_share_high | 0141-q250-r4 |
| 18 | q500 | 4 |  | light_share_high | 0143-q500-r4 |
| 19 | off | 4 |  | light_share_high | 0145-off-r4 |
| 20 | q0 | 4 |  | light_share_high | 0147-q0-r4 |
| 21 | q125 | 4 |  | light_share_high | 0149-q125-r4 |

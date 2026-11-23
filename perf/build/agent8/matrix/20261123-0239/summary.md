# Timing matrix: Window 4c (Agent 8, run-2 task #7 follow-up): codegen B repeat. B = devoffB (S2 sources + codegen B) vs d0 = devoff2 (S2 sources + S1 codegen), 6 round-robin rounds

- matrix: <workspace>\bench\agent8\run\matrix-window4c.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261123-0239
- started 2026-11-23 02:39, ended 03:05; 13 runs (13 OK), 12 scored; desktop WinSta0\Default
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 12 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

## Group w4c: ref d0 (ref arm of the group), noise band +-10 %

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d0 | 6/6 | 6 | 0 | 2.47 (2.25..2.49) | 10 | 4.94 | 5.62 | 0 | 0 | 385.35 | 2.53 |  |  |  | ref |
| B | 6/6 | 6 | 0 | 2.5 (2.47..2.51) | 1.6 | 4.91 | 5.62 | 0 | 0 | 383.91 | 2.6 | 1.3 | -0.5 |  | within noise |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | d0 | 0 | OK | True |  | 4.01 | 60 | 12796 | 2.186 | 4.948 | 0 | 0 | 2.486 | 0.976 | wm_close 0.5 s | light_share_high | 0239-cold-d0 |  |
| 2 | 1 | d0 | 1 | OK | True |  | 3.01 | 60 | 21090 | 2.246 | 4.798 | 0 | 0 | 2.525 | 0.979 | wm_close 0.5 s | light_share_high | 0241-d0-r1 |  |
| 3 | 1 | B | 1 | OK | True |  | 3.01 | 60 | 19427 | 2.472 | 4.899 | 0 | 0 | 2.547 | 0.972 | wm_close 0.5 s | light_share_high | 0243-B-r1 |  |
| 4 | 2 | B | 2 | OK | True |  | 3.01 | 60 | 19197 | 2.512 | 4.896 | 0 | 0 | 2.561 | 0.972 | wm_close 0.5 s | light_share_high | 0245-B-r2 |  |
| 5 | 2 | d0 | 2 | OK | True |  | 3 | 60 | 19252 | 2.471 | 4.937 | 0 | 0 | 2.526 | 0.966 | wm_close 0.5 s | light_share_high | 0247-d0-r2 |  |
| 6 | 3 | d0 | 3 | OK | True |  | 3.01 | 60 | 19321 | 2.451 | 4.912 | 0 | 0 | 2.508 | 0.968 | wm_close 0.5 s | light_share_high | 0249-d0-r3 |  |
| 7 | 3 | B | 3 | OK | True |  | 3.01 | 60 | 19173 | 2.502 | 4.933 | 0 | 0 | 2.599 | 0.969 | wm_close 0.5 s | light_share_high | 0251-B-r3 |  |
| 8 | 4 | B | 4 | OK | True |  | 3.01 | 60 | 19103 | 2.491 | 4.973 | 0 | 0 | 2.697 | 0.968 | wm_close 0.5 s | light_share_high | 0253-B-r4 |  |
| 9 | 4 | d0 | 4 | OK | True |  | 3.01 | 60 | 19249 | 2.493 | 4.965 | 0 | 0 | 2.54 | 0.965 | wm_close 0.5 s | light_share_high | 0255-d0-r4 |  |
| 10 | 5 | d0 | 5 | OK | True |  | 3.01 | 60 | 19255 | 2.491 | 4.934 | 0 | 0 | 2.594 | 0.967 | wm_close 0.5 s | light_share_high | 0257-d0-r5 |  |
| 11 | 5 | B | 5 | OK | True |  | 3.01 | 60 | 19196 | 2.498 | 4.926 | 0 | 0 | 2.565 | 0.97 | wm_close 0.5 s | light_share_high | 0259-B-r5 |  |
| 12 | 6 | B | 6 | OK | True |  | 4 | 60 | 19297 | 2.51 | 4.78 | 0 | 0 | 2.607 | 0.977 | wm_close 0.5 s | light_share_high | 0301-B-r6 |  |
| 13 | 6 | d0 | 6 | OK | True |  | 4 | 60 | 19281 | 2.465 | 5.034 | 0 | 0 | 2.503 | 0.965 | wm_close 0.5 s | light_share_high | 0303-d0-r6 |  |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | d0 | cold |  | light_share_high | 0239-cold-d0 |
| 2 | d0 | 1 |  | light_share_high | 0241-d0-r1 |
| 3 | B | 1 |  | light_share_high | 0243-B-r1 |
| 4 | B | 2 |  | light_share_high | 0245-B-r2 |
| 5 | d0 | 2 |  | light_share_high | 0247-d0-r2 |
| 6 | d0 | 3 |  | light_share_high | 0249-d0-r3 |
| 7 | B | 3 |  | light_share_high | 0251-B-r3 |
| 8 | B | 4 |  | light_share_high | 0253-B-r4 |
| 9 | d0 | 4 |  | light_share_high | 0255-d0-r4 |
| 10 | d0 | 5 |  | light_share_high | 0257-d0-r5 |
| 11 | B | 5 |  | light_share_high | 0259-B-r5 |
| 12 | B | 6 |  | light_share_high | 0301-B-r6 |
| 13 | d0 | 6 |  | light_share_high | 0303-d0-r6 |

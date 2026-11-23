# Timing matrix: Window 5b (Agent 8, run-2 task #7 follow-up): TimerQueue wait modes on devoff4 (S4a), all with the 8 timer cvars. d11 (spin wait) vs d11t (blocking wait, REX_TIMER_WAIT_BLOCKING=1) vs d11p (precise wait, timer_queue_precise_wait=true)

- matrix: <workspace>\bench\agent8\run\matrix-window5b.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261123-0155
- started 2026-11-23 01:55, ended 02:33; 19 runs (19 OK), 18 scored; desktop WinSta0\Default
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 18 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

## Group w5b: ref d11 (ref arm of the group), noise band +-10.1 %

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d11 | 6/6 | 6 | 0 | 2.51 (2.29..2.54) | 10.1 | 4.85 | 5.42 | 0 | 0 | 384.65 | 2.54 |  |  |  | ref |
| d11t | 6/6 | 6 | 0 | 2.51 (2.35..2.61) | 10.3 | 4.86 | 5.55 | 0 | 0 | 384.23 | 2.31 | 0 | 0.1 |  | within noise |
| d11p | 6/6 | 6 | 0 | 2.5 (2.44..2.54) | 4.4 | 4.78 | 5.36 | 0 | 0 | 384.99 | 2.34 | -0.5 | -1.5 |  | within noise |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | d11 | 0 | OK | True |  | 4.01 | 60 | 12571 | 2.306 | 4.661 | 0 | 0 | 2.545 | 0.983 | wm_close 0.6 s | light_share_high | 0155-cold-d11 |  |
| 2 | 1 | d11 | 1 | OK | True |  | 3.01 | 60 | 20755 | 2.288 | 4.551 | 0 | 0 | 2.456 | 0.988 | wm_close 0.5 s | light_share_high | 0157-d11-r1 |  |
| 3 | 1 | d11t | 1 | OK | True |  | 3.01 | 60 | 20353 | 2.347 | 4.633 | 0 | 0 | 2.291 | 0.984 | wm_close 0.5 s | light_share_high | 0159-d11t-r1 |  |
| 4 | 1 | d11p | 1 | OK | True |  | 3 | 60 | 19798 | 2.435 | 4.719 | 0 | 0 | 2.323 | 0.979 | wm_close 0.5 s | light_share_high | 0201-d11p-r1 |  |
| 5 | 2 | d11t | 2 | OK | True |  | 3.01 | 60 | 19285 | 2.496 | 4.851 | 0 | 0 | 2.293 | 0.971 | wm_close 0.5 s | light_share_high | 0203-d11t-r2 |  |
| 6 | 2 | d11p | 2 | OK | True |  | 3.02 | 60 | 19246 | 2.511 | 4.748 | 0 | 0 | 2.375 | 0.977 | wm_close 0.5 s | light_share_high | 0205-d11p-r2 |  |
| 7 | 2 | d11 | 2 | OK | True |  | 3.01 | 60 | 19201 | 2.528 | 4.794 | 0 | 0 | 2.525 | 0.976 | wm_close 0.5 s | light_share_high | 0207-d11-r2 |  |
| 8 | 3 | d11p | 3 | OK | True |  | 3 | 60 | 19091 | 2.544 | 4.8 | 0 | 0 | 2.372 | 0.976 | wm_close 0.5 s | light_share_high | 0209-d11p-r3 |  |
| 9 | 3 | d11 | 3 | OK | True |  | 3 | 60 | 19074 | 2.542 | 4.9 | 0 | 0 | 2.588 | 0.97 | wm_close 0.5 s | light_share_high | 0211-d11-r3 |  |
| 10 | 3 | d11t | 3 | OK | True |  | 3.02 | 60 | 18588 | 2.606 | 5.102 | 0 | 0 | 2.386 | 0.962 | wm_close 0.5 s | light_share_high | 0213-d11t-r3 |  |
| 11 | 4 | d11 | 4 | OK | True |  | 3.01 | 60 | 19211 | 2.526 | 4.865 | 0 | 0 | 2.581 | 0.972 | wm_close 0.5 s | light_share_high | 0215-d11-r4 |  |
| 12 | 4 | d11t | 4 | OK | True |  | 3.02 | 60 | 19167 | 2.532 | 4.868 | 0 | 0 | 2.291 | 0.973 | wm_close 0.5 s | light_share_high | 0217-d11t-r4 |  |
| 13 | 4 | d11p | 4 | OK | True |  | 3.01 | 60 | 19243 | 2.505 | 4.85 | 0 | 0 | 2.327 | 0.972 | wm_close 0.5 s | light_share_high | 0219-d11p-r4 |  |
| 14 | 5 | d11t | 5 | OK | True |  | 4.02 | 60 | 19119 | 2.498 | 4.986 | 0 | 0 | 2.315 | 0.972 | wm_close 0.5 s | light_share_high | 0221-d11t-r5 |  |
| 15 | 5 | d11p | 5 | OK | True |  | 3 | 60 | 19254 | 2.5 | 4.867 | 0 | 0 | 2.321 | 0.97 | wm_close 0.5 s | light_share_high | 0223-d11p-r5 |  |
| 16 | 5 | d11 | 5 | OK | True |  | 3.01 | 60 | 19254 | 2.492 | 4.881 | 0 | 0 | 2.543 | 0.97 | wm_close 0.5 s | light_share_high | 0225-d11-r5 |  |
| 17 | 6 | d11p | 6 | OK | True |  | 3.01 | 60 | 19309 | 2.489 | 4.763 | 0 | 0 | 2.296 | 0.977 | wm_close 0.5 s | light_share_high | 0227-d11p-r6 |  |
| 18 | 6 | d11 | 6 | OK | True |  | 3.01 | 60 | 19284 | 2.504 | 4.842 | 0 | 0 | 2.541 | 0.972 | wm_close 0.5 s | light_share_high | 0229-d11-r6 |  |
| 19 | 6 | d11t | 6 | OK | True |  | 3.01 | 60 | 19257 | 2.531 | 4.82 | 0 | 0 | 2.287 | 0.974 | wm_close 0.5 s | light_share_high | 0231-d11t-r6 |  |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | d11 | cold |  | light_share_high | 0155-cold-d11 |
| 2 | d11 | 1 |  | light_share_high | 0157-d11-r1 |
| 3 | d11t | 1 |  | light_share_high | 0159-d11t-r1 |
| 4 | d11p | 1 |  | light_share_high | 0201-d11p-r1 |
| 5 | d11t | 2 |  | light_share_high | 0203-d11t-r2 |
| 6 | d11p | 2 |  | light_share_high | 0205-d11p-r2 |
| 7 | d11 | 2 |  | light_share_high | 0207-d11-r2 |
| 8 | d11p | 3 |  | light_share_high | 0209-d11p-r3 |
| 9 | d11 | 3 |  | light_share_high | 0211-d11-r3 |
| 10 | d11t | 3 |  | light_share_high | 0213-d11t-r3 |
| 11 | d11 | 4 |  | light_share_high | 0215-d11-r4 |
| 12 | d11t | 4 |  | light_share_high | 0217-d11t-r4 |
| 13 | d11p | 4 |  | light_share_high | 0219-d11p-r4 |
| 14 | d11t | 5 |  | light_share_high | 0221-d11t-r5 |
| 15 | d11p | 5 |  | light_share_high | 0223-d11p-r5 |
| 16 | d11 | 5 |  | light_share_high | 0225-d11-r5 |
| 17 | d11p | 6 |  | light_share_high | 0227-d11p-r6 |
| 18 | d11 | 6 |  | light_share_high | 0229-d11-r6 |
| 19 | d11t | 6 |  | light_share_high | 0231-d11t-r6 |

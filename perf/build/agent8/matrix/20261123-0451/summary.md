# Timing matrix: Window 5b (Agent 8, run-2 task #7 follow-up): TimerQueue wait modes on devoff4 (S4a), all with the 8 timer cvars. d11 (spin wait) vs d11t (blocking wait, REX_TIMER_WAIT_BLOCKING=1) vs d11p (precise wait, timer_queue_precise_wait=true)

- matrix: <workspace>\bench\agent8\run\matrix-window5b.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261123-0451
- started 2026-11-23 04:51, ended 05:30; 19 runs (19 OK), 18 scored; desktop WinSta0\Default
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 18 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

## Group w5b: ref d11 (ref arm of the group), noise band +-1.5 %

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d11 | 6/6 | 6 | 0 | 2.51 (2.48..2.52) | 1.5 | 4.82 | 5.36 | 0 | 0 | 385.18 | 2.56 |  |  |  | ref |
| d11t | 6/6 | 6 | 0 | 2.52 (2.52..2.65) | 5.1 | 4.84 | 5.48 | 0 | 0 | 382 | 2.35 | 0.5 | 0.4 |  | within noise |
| d11p | 6/6 | 6 | 0 | 2.51 (2.46..2.59) | 5.1 | 4.85 | 5.49 | 0 | 0 | 385.45 | 2.35 | -0.1 | 0.6 |  | within noise |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | d11 | 0 | OK | True |  | 4.01 | 60 | 13255 | 2.094 | 4.613 | 0 | 0 | 2.48 | 0.987 | wm_close 0.4 s | light_share_high | 0451-cold-d11 |  |
| 2 | 1 | d11 | 1 | OK | True |  | 4 | 60 | 19649 | 2.483 | 4.917 | 0 | 0 | 2.602 | 0.976 | wm_close 0.6 s | light_share_high | 0453-d11-r1 |  |
| 3 | 1 | d11t | 1 | OK | True |  | 5.01 | 60 | 18357 | 2.647 | 5.008 | 0 | 0 | 2.365 | 0.966 | wm_close 0.5 s | light_share_high | 0455-d11t-r1 |  |
| 4 | 1 | d11p | 1 | OK | True |  | 4.01 | 60 | 19302 | 2.457 | 4.922 | 0 | 0 | 2.368 | 0.969 | wm_close 0.5 s | light_share_high | 0457-d11p-r1 |  |
| 5 | 2 | d11t | 2 | OK | True |  | 4.01 | 60 | 18832 | 2.582 | 4.877 | 0 | 0 | 2.339 | 0.972 | wm_close 0.6 s | light_share_high | 0459-d11t-r2 |  |
| 6 | 2 | d11p | 2 | OK | True |  | 4 | 60 | 19273 | 2.499 | 4.807 | 0 | 0 | 2.274 | 0.975 | wm_close 0.5 s | light_share_high | 0501-d11p-r2 |  |
| 7 | 2 | d11 | 2 | OK | True |  | 4.01 | 60 | 19259 | 2.512 | 4.821 | 0 | 0 | 2.545 | 0.974 | wm_close 0.5 s | light_share_high | 0504-d11-r2 |  |
| 8 | 3 | d11p | 3 | OK | True |  | 4.01 | 60 | 19295 | 2.515 | 4.804 | 0 | 0 | 2.354 | 0.978 | wm_close 0.5 s | light_share_high | 0506-d11p-r3 |  |
| 9 | 3 | d11 | 3 | OK | True |  | 4 | 60 | 19251 | 2.521 | 4.774 | 0 | 0 | 2.59 | 0.976 | wm_close 0.6 s | light_share_high | 0508-d11-r3 |  |
| 10 | 3 | d11t | 3 | OK | True |  | 4.01 | 60 | 18965 | 2.528 | 5.021 | 0 | 0 | 2.311 | 0.966 | wm_close 0.5 s | light_share_high | 0510-d11t-r3 |  |
| 11 | 4 | d11 | 4 | OK | True |  | 4.02 | 60 | 19271 | 2.517 | 4.814 | 0 | 0 | 2.569 | 0.975 | wm_close 0.5 s | light_share_high | 0512-d11-r4 |  |
| 12 | 4 | d11t | 4 | OK | True |  | 4.01 | 60 | 19236 | 2.518 | 4.767 | 0 | 0 | 2.342 | 0.974 | wm_close 0.5 s | light_share_high | 0514-d11t-r4 |  |
| 13 | 4 | d11p | 4 | OK | True |  | 4.01 | 60 | 19273 | 2.504 | 4.843 | 0 | 0 | 2.38 | 0.975 | wm_close 0.5 s | light_share_high | 0516-d11p-r4 |  |
| 14 | 5 | d11t | 5 | OK | True |  | 4.01 | 60 | 19288 | 2.52 | 4.77 | 0 | 0 | 2.359 | 0.974 | wm_close 0.5 s | light_share_high | 0518-d11t-r5 |  |
| 15 | 5 | d11p | 5 | OK | True |  | 4.01 | 60 | 18778 | 2.586 | 4.847 | 0 | 0 | 2.375 | 0.972 | wm_close 0.5 s | light_share_high | 0520-d11p-r5 |  |
| 16 | 5 | d11 | 5 | OK | True |  | 4.01 | 60 | 19250 | 2.506 | 4.855 | 0 | 0 | 2.535 | 0.972 | wm_close 0.5 s | light_share_high | 0522-d11-r5 |  |
| 17 | 6 | d11p | 6 | OK | True |  | 4.02 | 60 | 19108 | 2.529 | 4.882 | 0 | 0 | 2.373 | 0.973 | wm_close 0.5 s | light_share_high | 0524-d11p-r6 |  |
| 18 | 6 | d11 | 6 | OK | True |  | 4.01 | 60 | 19260 | 2.51 | 4.807 | 0 | 0 | 2.51 | 0.973 | wm_close 0.5 s | light_share_high | 0526-d11-r6 |  |
| 19 | 6 | d11t | 6 | OK | True |  | 4.01 | 60 | 19268 | 2.519 | 4.794 | 0 | 0 | 2.366 | 0.975 | wm_close 0.5 s | light_share_high | 0528-d11t-r6 |  |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | d11 | cold |  | light_share_high | 0451-cold-d11 |
| 2 | d11 | 1 |  | light_share_high | 0453-d11-r1 |
| 3 | d11t | 1 |  | light_share_high | 0455-d11t-r1 |
| 4 | d11p | 1 |  | light_share_high | 0457-d11p-r1 |
| 5 | d11t | 2 |  | light_share_high | 0459-d11t-r2 |
| 6 | d11p | 2 |  | light_share_high | 0501-d11p-r2 |
| 7 | d11 | 2 |  | light_share_high | 0504-d11-r2 |
| 8 | d11p | 3 |  | light_share_high | 0506-d11p-r3 |
| 9 | d11 | 3 |  | light_share_high | 0508-d11-r3 |
| 10 | d11t | 3 |  | light_share_high | 0510-d11t-r3 |
| 11 | d11 | 4 |  | light_share_high | 0512-d11-r4 |
| 12 | d11t | 4 |  | light_share_high | 0514-d11t-r4 |
| 13 | d11p | 4 |  | light_share_high | 0516-d11p-r4 |
| 14 | d11t | 5 |  | light_share_high | 0518-d11t-r5 |
| 15 | d11p | 5 |  | light_share_high | 0520-d11p-r5 |
| 16 | d11 | 5 |  | light_share_high | 0522-d11-r5 |
| 17 | d11p | 6 |  | light_share_high | 0524-d11p-r6 |
| 18 | d11 | 6 |  | light_share_high | 0526-d11-r6 |
| 19 | d11t | 6 |  | light_share_high | 0528-d11t-r6 |

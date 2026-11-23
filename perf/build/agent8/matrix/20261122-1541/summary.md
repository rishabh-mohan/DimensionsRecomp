# Timing matrix: Window 4 (Agent 8, session 3): B = devoffB (codegen B) vs d0 = devoff2 (primary), then d3 = devoff3; W4b adds d11t = window 3's d11 + REX_TIMER_WAIT_BLOCKING=1

- matrix: <workspace>\bench\agent8\run\matrix-window4.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261122-1541
- started 2026-11-22 15:41, ended 16:17; 17 runs (17 OK), 16 scored; desktop WinSta0\Default
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 16 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

> **FUNCTIONAL ONLY**: 1 of 17 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group w4: ref d0 (ref arm of the group), noise band +-19.6 %

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d0 | 4/4 | 4 | 0 | 3.4 (3.07..3.73) | 19.6 | 10.73 | 13.37 | 0 | 0 | 239.71 | 3.44 |  |  |  | ref |
| B | 4/4 | 3 | 0 | 3.23 (2.88..3.53) | 20 | 10.5 | 12.73 | 0 | 0 | 255.13 | 3.35 | -4.9 | -2.2 |  | within noise |
| d3 | 4/4 | 4 | 0 | 3.21 (2.89..4.26) | 42.6 | 10.49 | 13.12 | 0 | 0 | 248.88 | 3.38 | -5.4 | -2.3 |  | within noise |
| d11t | 4/4 | 4 | 0 | 3.36 (3.02..3.86) | 24.7 | 10.94 | 14.14 | 0 | 0 | 237.74 | 2.91 | -1.1 | 1.9 |  | within noise |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | d0 | 0 | OK | True |  | 6.01 | 60 | 9776 | 3.081 | 5.871 | 0 | 0 | 2.919 | 0.923 | wm_close 0.8 s | light_share_high | 1541-cold-d0 |  |
| 2 | 1 | d0 | 1 | OK | True |  | 4.02 | 60 | 12821 | 3.234 | 10.766 | 0 | 0 | 3.366 | 0.808 | wm_close 1.1 s | light_share_high | 1542-d0-r1 |  |
| 3 | 1 | B | 1 | OK | True |  | 5.01 | 60 | 15857 | 2.884 | 9.398 | 0 | 0 | 3.142 | 0.87 | wm_close 0.9 s | light_share_high | 1545-B-r1 |  |
| 4 | 1 | d3 | 1 | OK | True |  | 5.01 | 60 | 11549 | 3.347 | 11.098 | 0 | 0 | 3.449 | 0.671 | wm_close 0.8 s | light_share_high | 1547-d3-r1 |  |
| 5 | 1 | d11t | 1 | OK | True |  | 4 | 60 | 10321 | 3.857 | 11.494 | 0 | 0 | 3.004 | 0.56 | wm_close 0.7 s |  | 1549-d11t-r1 |  |
| 6 | 2 | B | 2 | OK | False |  | 6 | 60 | 11723 | 3.53 | 11.518 | 0 | 0 | 3.43 | 0.654 | wm_close 0.8 s | light_share_high build_procs_warmup build_procs_window | 1551-B-r2 | not timing: build processes: clang++:34584 clang++:36068 clang++:6544 |
| 7 | 2 | d3 | 2 | OK | True |  | 6 | 60 | 14932 | 2.894 | 9.709 | 0 | 0 | 3.179 | 0.824 | wm_close 0.9 s | light_share_high | 1553-d3-r2 |  |
| 8 | 2 | d11t | 2 | OK | True |  | 5 | 60 | 11029 | 3.568 | 12.17 | 0 | 0 | 2.937 | 0.599 | wm_close 0.8 s |  | 1556-d11t-r2 |  |
| 9 | 2 | d0 | 2 | OK | True |  | 4 | 60 | 13523 | 3.069 | 9.923 | 0 | 0 | 3.34 | 0.746 | wm_close 0.9 s | light_share_high | 1558-d0-r2 |  |
| 10 | 3 | d3 | 3 | OK | True |  | 7 | 60 | 9923 | 4.264 | 12.899 | 0 | 0 | 3.523 | 0.513 | wm_close 0.9 s |  | 1600-d3-r3 |  |
| 11 | 3 | d11t | 3 | OK | True |  | 5.02 | 60 | 13859 | 3.025 | 9.865 | 0 | 0 | 2.812 | 0.749 | wm_close 0.8 s | light_share_high | 1602-d11t-r3 |  |
| 12 | 3 | d0 | 3 | OK | True |  | 4 | 60 | 11154 | 3.565 | 10.698 | 0 | 0 | 3.527 | 0.6 | wm_close 0.9 s | light_share_high | 1604-d0-r3 |  |
| 13 | 3 | B | 3 | OK | True |  | 4.01 | 60 | 11538 | 3.435 | 10.989 | 0 | 0 | 3.48 | 0.626 | wm_close 0.9 s | light_share_high | 1606-B-r3 |  |
| 14 | 4 | d11t | 4 | OK | True |  | 4.01 | 60 | 12747 | 3.158 | 10.377 | 0 | 0 | 2.896 | 0.702 | wm_close 0.8 s | light_share_high | 1608-d11t-r4 |  |
| 15 | 4 | d0 | 4 | OK | True |  | 5.02 | 60 | 10696 | 3.734 | 10.965 | 0 | 0 | 3.517 | 0.565 | wm_close 0.8 s |  | 1611-d0-r4 |  |
| 16 | 4 | B | 4 | OK | True |  | 4.01 | 60 | 13791 | 3.033 | 10.008 | 0 | 0 | 3.349 | 0.742 | wm_close 1 s | light_share_high | 1613-B-r4 |  |
| 17 | 4 | d3 | 4 | OK | True |  | 4.01 | 60 | 13339 | 3.082 | 9.874 | 0 | 0 | 3.372 | 0.723 | wm_close 0.9 s | light_share_high | 1615-d3-r4 |  |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | d0 | cold |  | light_share_high | 1541-cold-d0 |
| 2 | d0 | 1 |  | light_share_high | 1542-d0-r1 |
| 3 | B | 1 |  | light_share_high | 1545-B-r1 |
| 4 | d3 | 1 |  | light_share_high | 1547-d3-r1 |
| 6 | B | 2 |  | light_share_high build_procs_warmup build_procs_window | 1551-B-r2 |
| 7 | d3 | 2 |  | light_share_high | 1553-d3-r2 |
| 9 | d0 | 2 |  | light_share_high | 1558-d0-r2 |
| 11 | d11t | 3 |  | light_share_high | 1602-d11t-r3 |
| 12 | d0 | 3 |  | light_share_high | 1604-d0-r3 |
| 13 | B | 3 |  | light_share_high | 1606-B-r3 |
| 14 | d11t | 4 |  | light_share_high | 1608-d11t-r4 |
| 16 | B | 4 |  | light_share_high | 1613-B-r4 |
| 17 | d3 | 4 |  | light_share_high | 1615-d3-r4 |

# Timing matrix: Window C, pass 2 (M8, session 3 task S3T-8; RESUME section 7 step 9): confirmation window on devoff4b (S4b + S4c, every switch OFF by default). s0 (all OFF) vs win3 = the three winners together (p2fc + d11p + q500) vs c1np = fix (i) + C1 v3 without P2 (verify off) vs p2fc (W6's winner, the anchor). Round 1 is the GPU warm-up and is discarded in the read-out

- matrix: <workspace>\bench\agent8\run\matrix-windowC2.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261125-0440
- started 2026-11-25 04:40, ended 05:14; 17 runs (17 OK), 16 scored; desktop WinSta0\Default
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 16 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

## Group wc: ref s0 (ref arm of the group), noise band +-2.7 %

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s0 | 4/4 | 4 | 0 | 2.01 (1.97..2.02) | 2.7 | 4.93 | 5.7 | 0 | 0 | 452.98 | 2.44 |  |  |  | ref |
| p2fc | 4/4 | 4 | 0 | 2.09 (2.07..2.11) | 2.1 | 4.97 | 5.68 | 0 | 0 | 473.71 | 2.27 | 4 | 0.9 |  | SLOWER (outside noise) |
| c1np | 4/4 | 4 | 0 | 2.08 (2.07..2.1) | 1.6 | 5 | 5.68 | 0 | 0 | 474.14 | 2.26 | 3.6 | 1.4 |  | SLOWER (outside noise) |
| win3 | 4/4 | 4 | 0 | 2.11 (2.1..2.18) | 3.5 | 4.2 | 4.72 | 0 | 0 | 490.71 | 1.53 | 5.2 | -14.8 |  | SLOWER (outside noise) |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | p2fc | 0 | OK | True |  | 4 | 60 | 14196 | 2.061 | 4.95 | 0 | 0 | 2.134 | 0.982 | wm_close 0.4 s | light_share_high | 0440-cold-p2fc |  |
| 2 | 1 | p2fc | 1 | OK | True |  | 4.01 | 60 | 23696 | 2.093 | 4.895 | 0 | 0 | 2.29 | 0.982 | wm_close 0.5 s | light_share_high | 0442-p2fc-r1 |  |
| 3 | 1 | c1np | 1 | OK | True |  | 4.01 | 60 | 23748 | 2.068 | 5.046 | 0 | 0 | 2.267 | 0.977 | wm_close 0.5 s | light_share_high | 0444-c1np-r1 |  |
| 4 | 1 | win3 | 1 | OK | True |  | 3.01 | 60 | 24734 | 2.177 | 3.966 | 0 | 0 | 1.504 | 0.998 | wm_close 0.5 s | light_share_high | 0446-win3-r1 |  |
| 5 | 1 | s0 | 1 | OK | True |  | 4.01 | 60 | 22469 | 2.023 | 5.005 | 0 | 0 | 2.426 | 0.972 | wm_close 0.6 s | light_share_high | 0448-s0-r1 |  |
| 6 | 2 | c1np | 2 | OK | True |  | 3.01 | 60 | 23694 | 2.085 | 4.971 | 0 | 0 | 2.267 | 0.98 | wm_close 0.5 s | light_share_high | 0450-c1np-r2 |  |
| 7 | 2 | win3 | 2 | OK | True |  | 4.01 | 60 | 24571 | 2.112 | 4.2 | 0 | 0 | 1.546 | 0.996 | wm_close 0.6 s | light_share_high | 0452-win3-r2 |  |
| 8 | 2 | s0 | 2 | OK | True |  | 4.02 | 60 | 22741 | 1.994 | 4.963 | 0 | 0 | 2.4 | 0.974 | wm_close 0.6 s | light_share_high | 0454-s0-r2 |  |
| 9 | 2 | p2fc | 2 | OK | True |  | 4.01 | 60 | 23880 | 2.08 | 4.981 | 0 | 0 | 2.279 | 0.98 | wm_close 0.5 s | light_share_high | 0456-p2fc-r2 |  |
| 10 | 3 | win3 | 3 | OK | True |  | 4.02 | 60 | 24502 | 2.103 | 4.233 | 0 | 0 | 1.504 | 0.995 | wm_close 0.5 s | light_share_high | 0458-win3-r3 |  |
| 11 | 3 | s0 | 3 | OK | True |  | 4.01 | 60 | 22858 | 1.969 | 4.895 | 0 | 0 | 2.406 | 0.974 | wm_close 0.5 s | light_share_high | 0500-s0-r3 |  |
| 12 | 3 | p2fc | 3 | OK | True |  | 4.01 | 60 | 23533 | 2.07 | 5.058 | 0 | 0 | 2.252 | 0.974 | wm_close 0.5 s | light_share_high | 0502-p2fc-r3 |  |
| 13 | 3 | c1np | 3 | OK | True |  | 4.01 | 60 | 23308 | 2.102 | 4.92 | 0 | 0 | 2.267 | 0.98 | wm_close 3.2 s | light_share_high | 0504-c1np-r3 |  |
| 14 | 4 | s0 | 4 | OK | True |  | 5.02 | 60 | 22557 | 2.02 | 4.856 | 0 | 0 | 2.508 | 0.976 | wm_close 0.6 s | light_share_high | 0506-s0-r4 |  |
| 15 | 4 | p2fc | 4 | OK | True |  | 4 | 60 | 23677 | 2.114 | 4.963 | 0 | 0 | 2.273 | 0.979 | wm_close 0.6 s | light_share_high | 0508-p2fc-r4 |  |
| 16 | 4 | c1np | 4 | OK | True |  | 4.01 | 60 | 23724 | 2.075 | 5.022 | 0 | 0 | 2.238 | 0.978 | wm_close 0.5 s | light_share_high | 0510-c1np-r4 |  |
| 17 | 4 | win3 | 4 | OK | True |  | 4.01 | 60 | 24319 | 2.109 | 4.2 | 0 | 0 | 1.561 | 0.996 | wm_close 0.6 s | light_share_high | 0513-win3-r4 |  |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | p2fc | cold |  | light_share_high | 0440-cold-p2fc |
| 2 | p2fc | 1 |  | light_share_high | 0442-p2fc-r1 |
| 3 | c1np | 1 |  | light_share_high | 0444-c1np-r1 |
| 4 | win3 | 1 |  | light_share_high | 0446-win3-r1 |
| 5 | s0 | 1 |  | light_share_high | 0448-s0-r1 |
| 6 | c1np | 2 |  | light_share_high | 0450-c1np-r2 |
| 7 | win3 | 2 |  | light_share_high | 0452-win3-r2 |
| 8 | s0 | 2 |  | light_share_high | 0454-s0-r2 |
| 9 | p2fc | 2 |  | light_share_high | 0456-p2fc-r2 |
| 10 | win3 | 3 |  | light_share_high | 0458-win3-r3 |
| 11 | s0 | 3 |  | light_share_high | 0500-s0-r3 |
| 12 | p2fc | 3 |  | light_share_high | 0502-p2fc-r3 |
| 13 | c1np | 3 |  | light_share_high | 0504-c1np-r3 |
| 14 | s0 | 4 |  | light_share_high | 0506-s0-r4 |
| 15 | p2fc | 4 |  | light_share_high | 0508-p2fc-r4 |
| 16 | c1np | 4 |  | light_share_high | 0510-c1np-r4 |
| 17 | win3 | 4 |  | light_share_high | 0513-win3-r4 |

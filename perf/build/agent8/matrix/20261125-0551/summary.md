# Timing matrix: Window C, pass 1 (M8, session 3 task S3T-8; RESUME section 7 step 9): confirmation window on devoff4b (S4b + S4c, every switch OFF by default). s0 (all OFF) vs win3 = the three winners together (p2fc + d11p + q500) vs c1np = fix (i) + C1 v3 without P2 (verify off) vs p2fc (W6's winner, the anchor). Round 1 is the GPU warm-up and is discarded in the read-out

- matrix: <workspace>\bench\agent8\run\matrix-windowC.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261125-0551
- started 2026-11-25 05:51, ended 06:25; 17 runs (17 OK), 16 scored; desktop WinSta0\Default
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 16 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

## Group wc: ref s0 (ref arm of the group), noise band +-11.8 %

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s0 | 4/4 | 4 | 0 | 2 (1.96..2.2) | 11.8 | 4.98 | 5.73 | 0 | 0 | 452.97 | 2.46 |  |  |  | ref |
| win3 | 4/4 | 4 | 0 | 2.11 (2.1..2.13) | 1.5 | 4.18 | 4.7 | 0 | 0 | 492.88 | 1.48 | 5.4 | -16 |  | within noise |
| c1np | 4/4 | 4 | 0 | 2.1 (2.08..2.13) | 2.6 | 4.95 | 5.7 | 0 | 0 | 473.8 | 2.27 | 4.6 | -0.6 |  | within noise |
| p2fc | 4/4 | 4 | 0 | 2.13 (2.05..2.15) | 5 | 5.01 | 5.69 | 0 | 0 | 466.74 | 2.27 | 6 | 0.5 |  | within noise |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | s0 | 0 | OK | True |  | 4 | 60 | 14451 | 2.156 | 4.547 | 0 | 0 | 2.188 | 0.989 | wm_close 0.4 s | light_share_high | 0551-cold-s0 |  |
| 2 | 1 | s0 | 1 | OK | True |  | 4 | 60 | 22528 | 2.018 | 4.877 | 0 | 0 | 2.482 | 0.976 | wm_close 0.5 s | light_share_high | 0552-s0-r1 |  |
| 3 | 1 | win3 | 1 | OK | True |  | 3 | 60 | 24439 | 2.114 | 4.156 | 0 | 0 | 1.504 | 0.996 | wm_close 0.5 s | light_share_high | 0554-win3-r1 |  |
| 4 | 1 | c1np | 1 | OK | True |  | 5.02 | 60 | 23829 | 2.134 | 4.919 | 0 | 0 | 2.275 | 0.98 | wm_close 0.5 s | light_share_high | 0556-c1np-r1 |  |
| 5 | 1 | p2fc | 1 | OK | True |  | 4.01 | 60 | 22590 | 2.152 | 5.077 | 0 | 0 | 2.28 | 0.972 | wm_close 0.5 s | light_share_high | 0558-p2fc-r1 |  |
| 6 | 2 | win3 | 2 | OK | True |  | 3.01 | 60 | 24619 | 2.132 | 4.18 | 0 | 0 | 1.482 | 0.997 | wm_close 0.5 s | light_share_high | 0601-win3-r2 |  |
| 7 | 2 | c1np | 2 | OK | True |  | 4 | 60 | 23644 | 2.102 | 4.904 | 0 | 0 | 2.263 | 0.981 | wm_close 0.5 s | light_share_high | 0603-c1np-r2 |  |
| 8 | 2 | p2fc | 2 | OK | True |  | 4.01 | 60 | 23085 | 2.104 | 4.934 | 0 | 0 | 2.303 | 0.978 | wm_close 0.5 s | light_share_high | 0605-p2fc-r2 |  |
| 9 | 2 | s0 | 2 | OK | True |  | 5.01 | 60 | 21524 | 2.199 | 5.138 | 0 | 0 | 2.485 | 0.965 | wm_close 0.4 s | light_share_high | 0607-s0-r2 |  |
| 10 | 3 | c1np | 3 | OK | True |  | 4.01 | 60 | 23737 | 2.093 | 4.982 | 0 | 0 | 2.309 | 0.979 | wm_close 0.5 s | light_share_high | 0609-c1np-r3 |  |
| 11 | 3 | p2fc | 3 | OK | True |  | 4.01 | 60 | 23767 | 2.046 | 5.105 | 0 | 0 | 2.204 | 0.973 | wm_close 0.5 s | light_share_high | 0611-p2fc-r3 |  |
| 12 | 3 | s0 | 3 | OK | True |  | 4.01 | 60 | 22771 | 1.991 | 5.038 | 0 | 0 | 2.435 | 0.973 | wm_close 0.5 s | light_share_high | 0613-s0-r3 |  |
| 13 | 3 | win3 | 3 | OK | True |  | 3.01 | 60 | 24683 | 2.112 | 4.189 | 0 | 0 | 1.481 | 0.997 | wm_close 0.5 s | light_share_high | 0615-win3-r3 |  |
| 14 | 4 | p2fc | 4 | OK | True |  | 4 | 60 | 23591 | 2.147 | 4.812 | 0 | 0 | 2.302 | 0.982 | wm_close 0.6 s | light_share_high | 0617-p2fc-r4 |  |
| 15 | 4 | s0 | 4 | OK | True |  | 4 | 60 | 22842 | 1.962 | 4.921 | 0 | 0 | 2.455 | 0.974 | wm_close 3.2 s | light_share_high | 0619-s0-r4 |  |
| 16 | 4 | win3 | 4 | OK | True |  | 4.01 | 60 | 24669 | 2.101 | 4.194 | 0 | 0 | 1.451 | 0.997 | wm_close 0.5 s | light_share_high | 0621-win3-r4 |  |
| 17 | 4 | c1np | 4 | OK | True |  | 4.01 | 60 | 23556 | 2.08 | 5.05 | 0 | 0 | 2.232 | 0.976 | wm_close 0.5 s | light_share_high | 0623-c1np-r4 |  |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | s0 | cold |  | light_share_high | 0551-cold-s0 |
| 2 | s0 | 1 |  | light_share_high | 0552-s0-r1 |
| 3 | win3 | 1 |  | light_share_high | 0554-win3-r1 |
| 4 | c1np | 1 |  | light_share_high | 0556-c1np-r1 |
| 5 | p2fc | 1 |  | light_share_high | 0558-p2fc-r1 |
| 6 | win3 | 2 |  | light_share_high | 0601-win3-r2 |
| 7 | c1np | 2 |  | light_share_high | 0603-c1np-r2 |
| 8 | p2fc | 2 |  | light_share_high | 0605-p2fc-r2 |
| 9 | s0 | 2 |  | light_share_high | 0607-s0-r2 |
| 10 | c1np | 3 |  | light_share_high | 0609-c1np-r3 |
| 11 | p2fc | 3 |  | light_share_high | 0611-p2fc-r3 |
| 12 | s0 | 3 |  | light_share_high | 0613-s0-r3 |
| 13 | win3 | 3 |  | light_share_high | 0615-win3-r3 |
| 14 | p2fc | 4 |  | light_share_high | 0617-p2fc-r4 |
| 15 | s0 | 4 |  | light_share_high | 0619-s0-r4 |
| 16 | win3 | 4 |  | light_share_high | 0621-win3-r4 |
| 17 | c1np | 4 |  | light_share_high | 0623-c1np-r4 |

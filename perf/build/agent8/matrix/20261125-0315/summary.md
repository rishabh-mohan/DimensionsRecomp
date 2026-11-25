# Timing matrix: Window C, pass 1 (M8, session 3 task S3T-8; RESUME section 7 step 9): confirmation window on devoff4b (S4b + S4c, every switch OFF by default). s0 (all OFF) vs win3 = the three winners together (p2fc + d11p + q500) vs c1np = fix (i) + C1 v3 without P2 (verify off) vs p2fc (W6's winner, the anchor). Round 1 is the GPU warm-up and is discarded in the read-out

- matrix: <workspace>\bench\agent8\run\matrix-windowC.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261125-0315
- started 2026-11-25 03:15, ended 03:50; 17 runs (17 OK), 16 scored; desktop WinSta0\Default
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 16 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

## Group wc: ref s0 (ref arm of the group), noise band +-2.8 %

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s0 | 4/4 | 4 | 0 | 2 (1.96..2.02) | 2.8 | 4.97 | 5.76 | 0 | 0 | 452.98 | 2.45 |  |  |  | ref |
| win3 | 4/4 | 4 | 0 | 2.12 (2.1..2.19) | 4.4 | 4.18 | 4.77 | 0 | 0 | 485.75 | 1.54 | 5.5 | -15.8 |  | SLOWER (outside noise) |
| c1np | 4/4 | 4 | 0 | 2.08 (2.07..2.19) | 5.5 | 4.99 | 5.71 | 0 | 0 | 474.36 | 2.28 | 3.8 | 0.6 |  | SLOWER (outside noise) |
| p2fc | 4/4 | 4 | 0 | 2.1 (2.09..2.17) | 3.4 | 4.96 | 5.67 | 0 | 0 | 471.6 | 2.29 | 4.9 | 0 |  | SLOWER (outside noise) |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | s0 | 0 | OK | True |  | 4.01 | 60 | 14293 | 2.09 | 5.195 | 0 | 0 | 2.201 | 0.977 | wm_close 0.4 s | light_share_high | 0315-cold-s0 |  |
| 2 | 1 | s0 | 1 | OK | True |  | 4 | 60 | 22510 | 2.016 | 5.12 | 0 | 0 | 2.445 | 0.971 | wm_close 0.6 s | light_share_high | 0317-s0-r1 |  |
| 3 | 1 | win3 | 1 | OK | True |  | 3.01 | 60 | 24580 | 2.101 | 4.191 | 0 | 0 | 1.467 | 0.996 | wm_close 0.5 s | light_share_high | 0319-win3-r1 |  |
| 4 | 1 | c1np | 1 | OK | True |  | 3.01 | 60 | 23835 | 2.072 | 5.057 | 0 | 0 | 2.29 | 0.976 | wm_close 0.5 s | light_share_high | 0321-c1np-r1 |  |
| 5 | 1 | p2fc | 1 | OK | True |  | 4.01 | 60 | 23489 | 2.109 | 5.03 | 0 | 0 | 2.312 | 0.978 | wm_close 0.5 s | light_share_high | 0323-p2fc-r1 |  |
| 6 | 2 | win3 | 2 | OK | True |  | 4.01 | 60 | 23866 | 2.119 | 4.27 | 0 | 0 | 1.56 | 0.994 | wm_close 0.7 s | light_share_high | 0325-win3-r2 |  |
| 7 | 2 | c1np | 2 | OK | True |  | 5 | 60 | 22923 | 2.187 | 4.911 | 0 | 0 | 2.296 | 0.98 | wm_close 0.5 s | light_share_high | 0327-c1np-r2 |  |
| 8 | 2 | p2fc | 2 | OK | True |  | 4.01 | 60 | 23515 | 2.095 | 4.995 | 0 | 0 | 2.271 | 0.977 | wm_close 0.5 s | light_share_high | 0329-p2fc-r2 |  |
| 9 | 2 | s0 | 2 | OK | True |  | 4 | 60 | 22787 | 1.96 | 4.911 | 0 | 0 | 2.471 | 0.973 | wm_close 0.5 s | light_share_high | 0332-s0-r2 |  |
| 10 | 3 | c1np | 3 | OK | True |  | 4.01 | 60 | 23610 | 2.079 | 5.08 | 0 | 0 | 2.278 | 0.975 | wm_close 0.5 s | light_share_high | 0334-c1np-r3 |  |
| 11 | 3 | p2fc | 3 | OK | True |  | 4 | 60 | 23799 | 2.094 | 4.934 | 0 | 0 | 2.293 | 0.981 | wm_close 0.5 s | light_share_high | 0336-p2fc-r3 |  |
| 12 | 3 | s0 | 3 | OK | True |  | 3 | 60 | 22644 | 2.003 | 4.882 | 0 | 0 | 2.479 | 0.975 | wm_close 0.5 s | light_share_high | 0338-s0-r3 |  |
| 13 | 3 | win3 | 3 | OK | True |  | 4.01 | 60 | 24089 | 2.195 | 4.101 | 0 | 0 | 1.636 | 0.997 | wm_close 0.5 s | light_share_high | 0340-win3-r3 |  |
| 14 | 4 | p2fc | 4 | OK | True |  | 3 | 60 | 23647 | 2.166 | 4.791 | 0 | 0 | 2.289 | 0.982 | wm_close 0.7 s | light_share_high | 0342-p2fc-r4 |  |
| 15 | 4 | s0 | 4 | OK | True |  | 4.01 | 60 | 22655 | 2.006 | 5.022 | 0 | 0 | 2.423 | 0.972 | wm_close 0.5 s | light_share_high | 0344-s0-r4 |  |
| 16 | 4 | win3 | 4 | OK | True |  | 3.02 | 60 | 24486 | 2.111 | 4.168 | 0 | 0 | 1.503 | 0.997 | wm_close 0.5 s | light_share_high | 0346-win3-r4 |  |
| 17 | 4 | c1np | 4 | OK | True |  | 4 | 60 | 23827 | 2.084 | 4.932 | 0 | 0 | 2.252 | 0.981 | wm_close 0.5 s | light_share_high | 0348-c1np-r4 |  |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | s0 | cold |  | light_share_high | 0315-cold-s0 |
| 2 | s0 | 1 |  | light_share_high | 0317-s0-r1 |
| 3 | win3 | 1 |  | light_share_high | 0319-win3-r1 |
| 4 | c1np | 1 |  | light_share_high | 0321-c1np-r1 |
| 5 | p2fc | 1 |  | light_share_high | 0323-p2fc-r1 |
| 6 | win3 | 2 |  | light_share_high | 0325-win3-r2 |
| 7 | c1np | 2 |  | light_share_high | 0327-c1np-r2 |
| 8 | p2fc | 2 |  | light_share_high | 0329-p2fc-r2 |
| 9 | s0 | 2 |  | light_share_high | 0332-s0-r2 |
| 10 | c1np | 3 |  | light_share_high | 0334-c1np-r3 |
| 11 | p2fc | 3 |  | light_share_high | 0336-p2fc-r3 |
| 12 | s0 | 3 |  | light_share_high | 0338-s0-r3 |
| 13 | win3 | 3 |  | light_share_high | 0340-win3-r3 |
| 14 | p2fc | 4 |  | light_share_high | 0342-p2fc-r4 |
| 15 | s0 | 4 |  | light_share_high | 0344-s0-r4 |
| 16 | win3 | 4 |  | light_share_high | 0346-win3-r4 |
| 17 | c1np | 4 |  | light_share_high | 0348-c1np-r4 |

# Timing matrix: Window 6 (Agent 5's draft v2, finalized 2026-11-22 21:16 for build/agent2/devoff4b-bin): upload path on the S4b bin. s0 (every switch OFF) vs p2 = #8 P2, p2f = #8 + #5 fix (i), p2fc = #8 + #5 + #4 C1 v3 keep-watch (verify off); f and fc = the decision table's arms without P2

- matrix: <workspace>\bench\agent8\run\matrix-window6.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261123-0313
- started 2026-11-23 03:13, ended 03:56; 21 runs (21 OK), 20 scored; desktop WinSta0\Default
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 20 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

## Group w6: ref s0 (ref arm of the group), noise band +-8.4 %

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s0 | 5/5 | 5 | 0 | 2.48 (2.27..2.48) | 8.4 | 5 | 5.74 | 0 | 0 | 385.02 | 2.53 |  |  |  | ref |
| p2 | 5/5 | 5 | 0 | 2.47 (2.42..2.53) | 4.4 | 5.01 | 5.66 | 0 | 0 | 385.24 | 2.53 | -0.3 | 0.3 |  | within noise |
| p2f | 5/5 | 5 | 0 | 2.45 (2.44..2.47) | 1.2 | 4.99 | 6.4 | 0.2 | 0 | 385.91 | 2.55 | -1.2 | -0.2 |  | within noise |
| p2fc | 5/5 | 5 | 0 | 2.13 (2.11..2.19) | 4.1 | 5.04 | 6.49 | 0 | 0 | 469.83 | 2.26 | -14 | 0.8 |  | FASTER (outside noise) |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | s0 | 0 | OK | True |  | 4 | 60 | 13448 | 1.986 | 5.082 | 0 | 0 | 2.403 | 0.972 | wm_close 0.5 s | light_share_high | 0313-cold-s0 |  |
| 2 | 1 | s0 | 1 | OK | True |  | 4 | 60 | 20868 | 2.27 | 4.869 | 0 | 0 | 2.491 | 0.975 | wm_close 0.5 s | light_share_high | 0315-s0-r1 |  |
| 3 | 1 | p2 | 1 | OK | True |  | 4.01 | 60 | 19711 | 2.418 | 4.868 | 0 | 0 | 2.551 | 0.97 | wm_close 0.4 s | light_share_high | 0317-p2-r1 |  |
| 4 | 1 | p2f | 1 | OK | True |  | 4.01 | 60 | 19387 | 2.446 | 4.92 | 0 | 0 | 2.556 | 0.971 | wm_close 0.5 s | light_share_high | 0319-p2f-r1 |  |
| 5 | 1 | p2fc | 1 | OK | True |  | 4.01 | 60 | 23564 | 2.108 | 5.038 | 0 | 0 | 2.272 | 0.978 | wm_close 0.4 s | light_share_high | 0321-p2fc-r1 |  |
| 6 | 2 | p2 | 2 | OK | True |  | 4.01 | 60 | 19279 | 2.469 | 4.926 | 0 | 0 | 2.572 | 0.969 | wm_close 0.5 s | light_share_high | 0323-p2-r2 |  |
| 7 | 2 | p2f | 2 | OK | True |  | 4.02 | 60 | 19297 | 2.442 | 5.02 | 0 | 0 | 2.519 | 0.968 | wm_close 0.5 s | light_share_high | 0325-p2f-r2 |  |
| 8 | 2 | p2fc | 2 | OK | True |  | 4.02 | 60 | 23514 | 2.175 | 4.933 | 0 | 0 | 2.289 | 0.979 | wm_close 0.6 s | light_share_high | 0327-p2fc-r2 |  |
| 9 | 2 | s0 | 2 | OK | True |  | 4 | 60 | 19097 | 2.476 | 5.088 | 0 | 0 | 2.522 | 0.964 | wm_close 0.5 s | light_share_high | 0329-s0-r2 |  |
| 10 | 3 | p2f | 3 | OK | True |  | 4.01 | 60 | 19296 | 2.449 | 5.021 | 0 | 0 | 2.563 | 0.969 | wm_close 0.5 s | light_share_high | 0331-p2f-r3 |  |
| 11 | 3 | p2fc | 3 | OK | True |  | 4 | 60 | 23403 | 2.129 | 5.046 | 0 | 0 | 2.248 | 0.977 | wm_close 0.5 s | light_share_high | 0333-p2fc-r3 |  |
| 12 | 3 | s0 | 3 | OK | True |  | 4.01 | 60 | 19185 | 2.467 | 5.092 | 0 | 0 | 2.5 | 0.964 | wm_close 0.5 s | light_share_high | 0335-s0-r3 |  |
| 13 | 3 | p2 | 3 | OK | True |  | 4 | 60 | 19195 | 2.486 | 5.036 | 0 | 0 | 2.558 | 0.964 | wm_close 0.4 s | light_share_high | 0337-p2-r3 |  |
| 14 | 4 | p2fc | 4 | OK | True |  | 4.01 | 60 | 22576 | 2.195 | 5.095 | 0 | 0 | 2.218 | 0.975 | wm_close 0.4 s | light_share_high | 0339-p2fc-r4 |  |
| 15 | 4 | s0 | 4 | OK | True |  | 4.02 | 60 | 19252 | 2.476 | 4.952 | 0 | 0 | 2.567 | 0.964 | wm_close 0.5 s | light_share_high | 0341-s0-r4 |  |
| 16 | 4 | p2 | 4 | OK | True |  | 4.01 | 60 | 19263 | 2.448 | 5.015 | 0 | 0 | 2.441 | 0.962 | wm_close 0.5 s | light_share_high | 0343-p2-r4 |  |
| 17 | 4 | p2f | 4 | OK | True |  | 4.01 | 60 | 19327 | 2.472 | 4.881 | 0 | 0 | 2.613 | 0.973 | wm_close 0.6 s | light_share_high | 0345-p2f-r4 |  |
| 18 | 5 | s0 | 5 | OK | True |  | 4.01 | 60 | 19279 | 2.477 | 4.998 | 0 | 0 | 2.555 | 0.965 | wm_close 0.6 s | light_share_high | 0348-s0-r5 |  |
| 19 | 5 | p2 | 5 | OK | True |  | 4.01 | 60 | 18775 | 2.527 | 5.07 | 0 | 0 | 2.511 | 0.958 | wm_close 0.5 s | light_share_high | 0350-p2-r5 |  |
| 20 | 5 | p2f | 5 | OK | True |  | 4.01 | 60 | 19258 | 2.443 | 4.987 | 1 | 0 | 2.514 | 0.968 | wm_close 0.6 s | light_share_high | 0352-p2f-r5 |  |
| 21 | 5 | p2fc | 5 | OK | True |  | 4.01 | 60 | 23492 | 2.128 | 4.848 | 0 | 0 | 2.249 | 0.982 | wm_close 0.4 s | light_share_high | 0354-p2fc-r5 |  |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | s0 | cold |  | light_share_high | 0313-cold-s0 |
| 2 | s0 | 1 |  | light_share_high | 0315-s0-r1 |
| 3 | p2 | 1 |  | light_share_high | 0317-p2-r1 |
| 4 | p2f | 1 |  | light_share_high | 0319-p2f-r1 |
| 5 | p2fc | 1 |  | light_share_high | 0321-p2fc-r1 |
| 6 | p2 | 2 |  | light_share_high | 0323-p2-r2 |
| 7 | p2f | 2 |  | light_share_high | 0325-p2f-r2 |
| 8 | p2fc | 2 |  | light_share_high | 0327-p2fc-r2 |
| 9 | s0 | 2 |  | light_share_high | 0329-s0-r2 |
| 10 | p2f | 3 |  | light_share_high | 0331-p2f-r3 |
| 11 | p2fc | 3 |  | light_share_high | 0333-p2fc-r3 |
| 12 | s0 | 3 |  | light_share_high | 0335-s0-r3 |
| 13 | p2 | 3 |  | light_share_high | 0337-p2-r3 |
| 14 | p2fc | 4 |  | light_share_high | 0339-p2fc-r4 |
| 15 | s0 | 4 |  | light_share_high | 0341-s0-r4 |
| 16 | p2 | 4 |  | light_share_high | 0343-p2-r4 |
| 17 | p2f | 4 |  | light_share_high | 0345-p2f-r4 |
| 18 | s0 | 5 |  | light_share_high | 0348-s0-r5 |
| 19 | p2 | 5 |  | light_share_high | 0350-p2-r5 |
| 20 | p2f | 5 |  | light_share_high | 0352-p2f-r5 |
| 21 | p2fc | 5 |  | light_share_high | 0354-p2fc-r5 |

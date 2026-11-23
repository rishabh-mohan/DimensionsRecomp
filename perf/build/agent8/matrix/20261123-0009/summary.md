# Timing matrix: Window 6 (Agent 5's draft v2, finalized 2026-11-22 21:16 for build/agent2/devoff4b-bin): upload path on the S4b bin. s0 (every switch OFF) vs p2 = #8 P2, p2f = #8 + #5 fix (i), p2fc = #8 + #5 + #4 C1 v3 keep-watch (verify off); f and fc = the decision table's arms without P2

- matrix: <workspace>\bench\agent8\run\matrix-window6.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261123-0009
- started 2026-11-23 00:09, ended 00:51; 21 runs (21 OK), 20 scored; desktop WinSta0\Default
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 20 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

## Group w6: ref s0 (ref arm of the group), noise band +-21.4 %

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s0 | 5/5 | 5 | 0 | 2.44 (2.08..2.6) | 21.4 | 5.06 | 5.78 | 0 | 0 | 385.15 | 2.5 |  |  |  | ref |
| p2 | 5/5 | 5 | 0 | 2.47 (2.05..2.49) | 17.8 | 4.96 | 5.66 | 0 | 0 | 385.56 | 2.52 | 1.1 | -2 |  | within noise |
| p2f | 5/5 | 5 | 0 | 2.45 (2.2..2.46) | 10.8 | 4.93 | 5.55 | 0 | 0 | 387.72 | 2.56 | 0.4 | -2.4 |  | within noise |
| p2fc | 5/5 | 5 | 0 | 2.16 (2.13..2.31) | 8 | 4.97 | 5.68 | 0 | 0 | 466.3 | 2.28 | -11.8 | -1.6 |  | within noise |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | s0 | 0 | OK | True |  | 4.01 | 60 | 11985 | 2.367 | 5.272 | 0 | 0 | 2.524 | 0.958 | wm_close 0.6 s | light_share_high | 0009-cold-s0 |  |
| 2 | 1 | s0 | 1 | OK | True |  | 4.01 | 60 | 22304 | 2.079 | 4.727 | 0 | 0 | 2.425 | 0.982 | wm_close 0.6 s | light_share_high | 0010-s0-r1 |  |
| 3 | 1 | p2 | 1 | OK | True |  | 4 | 60 | 22087 | 2.047 | 4.852 | 0 | 0 | 2.472 | 0.978 | wm_close 0.5 s | light_share_high | 0012-p2-r1 |  |
| 4 | 1 | p2f | 1 | OK | True |  | 4 | 60 | 21286 | 2.197 | 4.804 | 0 | 0 | 2.554 | 0.982 | wm_close 0.5 s | light_share_high | 0014-p2f-r1 |  |
| 5 | 1 | p2fc | 1 | OK | True |  | 4.01 | 60 | 23654 | 2.135 | 4.876 | 0 | 0 | 2.321 | 0.982 | wm_close 0.5 s | light_share_high | 0016-p2fc-r1 |  |
| 6 | 2 | p2 | 2 | OK | True |  | 4.01 | 60 | 20116 | 2.35 | 4.935 | 0 | 0 | 2.491 | 0.973 | wm_close 0.5 s | light_share_high | 0019-p2-r2 |  |
| 7 | 2 | p2f | 2 | OK | True |  | 4.01 | 60 | 19392 | 2.463 | 4.896 | 0 | 0 | 2.589 | 0.973 | wm_close 0.5 s | light_share_high | 0021-p2f-r2 |  |
| 8 | 2 | p2fc | 2 | OK | True |  | 4 | 60 | 21347 | 2.307 | 5.151 | 0 | 0 | 2.215 | 0.973 | wm_close 0.6 s | light_share_high | 0023-p2fc-r2 |  |
| 9 | 2 | s0 | 2 | OK | True |  | 4.01 | 60 | 18404 | 2.602 | 5.083 | 0 | 0 | 2.576 | 0.958 | wm_close 0.5 s | light_share_high | 0025-s0-r2 |  |
| 10 | 3 | p2f | 3 | OK | True |  | 4 | 60 | 19386 | 2.436 | 4.991 | 0 | 0 | 2.522 | 0.971 | wm_close 0.5 s | light_share_high | 0027-p2f-r3 |  |
| 11 | 3 | p2fc | 3 | OK | True |  | 4.02 | 60 | 23316 | 2.139 | 4.973 | 0 | 0 | 2.244 | 0.978 | wm_close 0.5 s | light_share_high | 0029-p2fc-r3 |  |
| 12 | 3 | s0 | 3 | OK | True |  | 4.02 | 60 | 19245 | 2.445 | 5.056 | 0 | 0 | 2.491 | 0.96 | wm_close 0.5 s | light_share_high | 0031-s0-r3 |  |
| 13 | 3 | p2 | 3 | OK | True |  | 4.01 | 60 | 19252 | 2.472 | 4.957 | 0 | 0 | 2.596 | 0.967 | wm_close 0.6 s | light_share_high | 0033-p2-r3 |  |
| 14 | 4 | p2fc | 4 | OK | True |  | 4.01 | 60 | 23561 | 2.157 | 4.834 | 0 | 0 | 2.326 | 0.98 | wm_close 0.5 s | light_share_high | 0035-p2fc-r4 |  |
| 15 | 4 | s0 | 4 | OK | True |  | 4.01 | 60 | 19258 | 2.429 | 5.292 | 0 | 0 | 2.531 | 0.954 | wm_close 0.5 s | light_share_high | 0037-s0-r4 |  |
| 16 | 4 | p2 | 4 | OK | True |  | 4.01 | 60 | 19093 | 2.488 | 4.993 | 0 | 0 | 2.516 | 0.965 | wm_close 0.5 s | light_share_high | 0039-p2-r4 |  |
| 17 | 4 | p2f | 4 | OK | True |  | 4.01 | 60 | 19342 | 2.454 | 4.933 | 0 | 0 | 2.554 | 0.969 | wm_close 0.5 s | light_share_high | 0041-p2f-r4 |  |
| 18 | 5 | s0 | 5 | OK | True |  | 4.01 | 60 | 19259 | 2.457 | 5.001 | 0 | 0 | 2.496 | 0.962 | wm_close 0.5 s | light_share_high | 0043-s0-r5 |  |
| 19 | 5 | p2 | 5 | OK | True |  | 4.01 | 60 | 19278 | 2.471 | 4.995 | 0 | 0 | 2.513 | 0.965 | wm_close 0.5 s | light_share_high | 0045-p2-r5 |  |
| 20 | 5 | p2f | 5 | OK | True |  | 4.02 | 60 | 19342 | 2.455 | 4.988 | 0 | 0 | 2.562 | 0.97 | wm_close 0.5 s | light_share_high | 0047-p2f-r5 |  |
| 21 | 5 | p2fc | 5 | OK | True |  | 4.02 | 60 | 22862 | 2.178 | 5.017 | 0 | 0 | 2.279 | 0.978 | wm_close 0.5 s | light_share_high | 0049-p2fc-r5 |  |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | s0 | cold |  | light_share_high | 0009-cold-s0 |
| 2 | s0 | 1 |  | light_share_high | 0010-s0-r1 |
| 3 | p2 | 1 |  | light_share_high | 0012-p2-r1 |
| 4 | p2f | 1 |  | light_share_high | 0014-p2f-r1 |
| 5 | p2fc | 1 |  | light_share_high | 0016-p2fc-r1 |
| 6 | p2 | 2 |  | light_share_high | 0019-p2-r2 |
| 7 | p2f | 2 |  | light_share_high | 0021-p2f-r2 |
| 8 | p2fc | 2 |  | light_share_high | 0023-p2fc-r2 |
| 9 | s0 | 2 |  | light_share_high | 0025-s0-r2 |
| 10 | p2f | 3 |  | light_share_high | 0027-p2f-r3 |
| 11 | p2fc | 3 |  | light_share_high | 0029-p2fc-r3 |
| 12 | s0 | 3 |  | light_share_high | 0031-s0-r3 |
| 13 | p2 | 3 |  | light_share_high | 0033-p2-r3 |
| 14 | p2fc | 4 |  | light_share_high | 0035-p2fc-r4 |
| 15 | s0 | 4 |  | light_share_high | 0037-s0-r4 |
| 16 | p2 | 4 |  | light_share_high | 0039-p2-r4 |
| 17 | p2f | 4 |  | light_share_high | 0041-p2f-r4 |
| 18 | s0 | 5 |  | light_share_high | 0043-s0-r5 |
| 19 | p2 | 5 |  | light_share_high | 0045-p2-r5 |
| 20 | p2f | 5 |  | light_share_high | 0047-p2f-r5 |
| 21 | p2fc | 5 |  | light_share_high | 0049-p2fc-r5 |

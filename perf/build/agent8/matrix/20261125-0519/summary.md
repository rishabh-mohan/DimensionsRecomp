# Timing matrix: Window 10 (M8, session 3; shape from build/agent9/session3/CG26-W10-REVIEW.md, a copy of W4c with new arms): codegen CG26 timing. cg26 = devoff4b relinked with the 10 CG26 TUs vs s0 = devoff4b, every switch OFF, 6 round-robin rounds

- matrix: <workspace>\bench\agent8\run\matrix-window10.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261125-0519
- started 2026-11-25 05:19, ended 05:45; 13 runs (13 OK), 12 scored; desktop WinSta0\Default
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 12 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

## Group w10: ref s0 (ref arm of the group), noise band +-12.8 %

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s0 | 6/6 | 6 | 0 | 1.99 (1.96..2.22) | 12.8 | 4.95 | 5.72 | 0 | 0 | 452.35 | 2.45 |  |  |  | ref |
| cg26 | 6/6 | 6 | 0 | 2.06 (1.97..2.14) | 8.4 | 5.05 | 5.8 | 0 | 0 | 454.65 | 2.4 | 3.3 | 2 |  | within noise |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | s0 | 0 | OK | True |  | 4.01 | 60 | 13846 | 1.994 | 5.163 | 0 | 0 | 2.378 | 0.973 | wm_close 0.5 s | light_share_high | 0519-cold-s0 |  |
| 2 | 1 | s0 | 1 | OK | True |  | 4.02 | 60 | 22733 | 1.968 | 4.977 | 0 | 0 | 2.442 | 0.971 | wm_close 0.5 s | light_share_high | 0521-s0-r1 |  |
| 3 | 1 | cg26 | 1 | OK | True |  | 4.01 | 60 | 22512 | 2.067 | 5.006 | 0 | 0 | 2.455 | 0.975 | wm_close 0.5 s | light_share_high | 0523-cg26-r1 |  |
| 4 | 2 | cg26 | 2 | OK | True |  | 4 | 60 | 22167 | 2.141 | 5.185 | 0 | 0 | 2.429 | 0.968 | wm_close 0.5 s | light_share_high | 0525-cg26-r2 |  |
| 5 | 2 | s0 | 2 | OK | True |  | 4 | 60 | 21257 | 2.217 | 5.072 | 0 | 0 | 2.48 | 0.968 | wm_close 0.5 s | light_share_high | 0527-s0-r2 |  |
| 6 | 3 | s0 | 3 | OK | True |  | 4.01 | 60 | 22863 | 1.963 | 4.833 | 0 | 0 | 2.457 | 0.977 | wm_close 0.5 s | light_share_high | 0529-s0-r3 |  |
| 7 | 3 | cg26 | 3 | OK | True |  | 4.03 | 60 | 23120 | 1.968 | 5.096 | 0 | 0 | 2.356 | 0.972 | wm_close 0.5 s | light_share_high | 0531-cg26-r3 |  |
| 8 | 4 | cg26 | 4 | OK | True |  | 3.01 | 60 | 22832 | 1.986 | 5.317 | 0 | 0 | 2.357 | 0.969 | wm_close 0.5 s | light_share_high | 0533-cg26-r4 |  |
| 9 | 4 | s0 | 4 | OK | True |  | 4.01 | 60 | 22575 | 2.004 | 4.857 | 0 | 0 | 2.46 | 0.975 | wm_close 0.5 s | light_share_high | 0535-s0-r4 |  |
| 10 | 5 | s0 | 5 | OK | True |  | 3.01 | 60 | 22488 | 2.045 | 4.941 | 0 | 0 | 2.42 | 0.976 | wm_close 0.5 s | light_share_high | 0537-s0-r5 |  |
| 11 | 5 | cg26 | 5 | OK | True |  | 4.01 | 60 | 22633 | 2.124 | 4.889 | 0 | 0 | 2.429 | 0.976 | wm_close 0.5 s | light_share_high | 0539-cg26-r5 |  |
| 12 | 6 | cg26 | 6 | OK | True |  | 5.01 | 60 | 23104 | 2.044 | 4.793 | 0 | 0 | 2.401 | 0.978 | wm_close 0.5 s | light_share_high | 0541-cg26-r6 |  |
| 13 | 6 | s0 | 6 | OK | True |  | 4 | 60 | 22662 | 1.974 | 4.966 | 0 | 0 | 2.427 | 0.972 | wm_close 0.5 s | light_share_high | 0543-s0-r6 |  |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | s0 | cold |  | light_share_high | 0519-cold-s0 |
| 2 | s0 | 1 |  | light_share_high | 0521-s0-r1 |
| 3 | cg26 | 1 |  | light_share_high | 0523-cg26-r1 |
| 4 | cg26 | 2 |  | light_share_high | 0525-cg26-r2 |
| 5 | s0 | 2 |  | light_share_high | 0527-s0-r2 |
| 6 | s0 | 3 |  | light_share_high | 0529-s0-r3 |
| 7 | cg26 | 3 |  | light_share_high | 0531-cg26-r3 |
| 8 | cg26 | 4 |  | light_share_high | 0533-cg26-r4 |
| 9 | s0 | 4 |  | light_share_high | 0535-s0-r4 |
| 10 | s0 | 5 |  | light_share_high | 0537-s0-r5 |
| 11 | cg26 | 5 |  | light_share_high | 0539-cg26-r5 |
| 12 | cg26 | 6 |  | light_share_high | 0541-cg26-r6 |
| 13 | s0 | 6 |  | light_share_high | 0543-s0-r6 |

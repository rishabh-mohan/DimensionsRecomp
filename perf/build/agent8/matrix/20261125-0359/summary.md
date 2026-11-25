# Timing matrix: Window 8a (Agent 8, run-2 task #7 follow-up): #2 shader miss cache on native4b (S4b + S4c native, every switch OFF). n0 (miss cache OFF) vs mc (LEGO_NATIVE_SHADER_MISS_CACHE=1), native frames, 6 round-robin rounds

- matrix: <workspace>\bench\agent8\run\matrix-window8a.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261125-0359
- started 2026-11-25 03:59, ended 04:29; 15 runs (15 OK), 14 scored; desktop WinSta0\Default
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 14 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

## Group w8a: ref n0 (ref arm of the group), noise band +-9.7 %

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| n0 | 7/7 | 7 | 0 | 3 (2.8..3.09) | 9.7 | 4.58 | 5.92 | 0 | 0 | 319.79 | 1.86 |  |  |  | ref |
| mc | 7/7 | 7 | 0 | 2.15 (2.14..2.21) | 3.3 | 3.02 | 3.74 | 0 | 0 | 461.24 | 1.89 | -28.6 | -34.1 |  | FASTER (outside noise) |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | n0 | 0 | OK | True |  | 5.01 | 60 | 11898 | 2.4235 | 3.6406 | 0 | 0 | 1.712 | 0.998 | wm_close 0.6 s | light_share_high | 0359-cold-n0 |  |
| 2 | 1 | n0 | 1 | OK | True |  | 4.02 | 60 | 17502 | 2.7953 | 4.262 | 0 | 0 | 1.841 | 0.994 | wm_close 0.5 s | light_share_high | 0400-n0-r1 |  |
| 3 | 1 | mc | 1 | OK | True |  | 5.01 | 60 | 22987 | 2.1473 | 3.1441 | 0 | 0 | 1.853 | 1 | wm_close 0.5 s | light_share_high | 0402-mc-r1 |  |
| 4 | 2 | mc | 2 | OK | True |  | 4 | 60 | 23063 | 2.1371 | 3.3154 | 0 | 0 | 2.092 | 1 | wm_close 0.6 s | light_share_high | 0404-mc-r2 |  |
| 5 | 2 | n0 | 2 | OK | True |  | 5.01 | 60 | 15789 | 3.0038 | 5.8897 | 0 | 0 | 1.86 | 0.952 | wm_close 0.5 s | light_share_high | 0407-n0-r2 |  |
| 6 | 3 | n0 | 3 | OK | True |  | 4.01 | 60 | 16569 | 2.9733 | 4.3693 | 0 | 0 | 1.872 | 0.992 | wm_close 0.5 s | light_share_high | 0409-n0-r3 |  |
| 7 | 3 | mc | 3 | OK | True |  | 4.01 | 60 | 23052 | 2.1476 | 3.0113 | 0 | 0 | 1.83 | 1 | wm_close 0.5 s | light_share_high | 0411-mc-r3 |  |
| 8 | 4 | mc | 4 | OK | True |  | 4.01 | 60 | 23082 | 2.1451 | 3.0184 | 0 | 0 | 1.784 | 1 | wm_close 0.5 s | light_share_high | 0413-mc-r4 |  |
| 9 | 4 | n0 | 4 | OK | True |  | 4.01 | 60 | 16537 | 2.979 | 4.4023 | 0 | 0 | 1.842 | 0.991 | wm_close 0.5 s | light_share_high | 0415-n0-r4 |  |
| 10 | 5 | n0 | 5 | OK | True |  | 4.01 | 60 | 15800 | 3.0874 | 4.9354 | 0 | 0 | 1.838 | 0.98 | wm_close 0.6 s | light_share_high | 0417-n0-r5 |  |
| 11 | 5 | mc | 5 | OK | True |  | 4 | 60 | 23116 | 2.1457 | 2.8929 | 0 | 0 | 1.817 | 1 | wm_close 0.6 s | light_share_high | 0419-mc-r5 |  |
| 12 | 6 | mc | 6 | OK | True |  | 4 | 60 | 23134 | 2.1453 | 2.8496 | 0 | 0 | 1.773 | 1 | wm_close 0.5 s | light_share_high | 0421-mc-r6 |  |
| 13 | 6 | n0 | 6 | OK | True |  | 4.01 | 60 | 15951 | 3.0745 | 4.5831 | 0 | 0 | 1.842 | 0.988 | wm_close 0.4 s | light_share_high | 0423-n0-r6 |  |
| 14 | 7 | n0 | 7 | OK | True |  | 4 | 60 | 15990 | 3.0385 | 5.0446 | 0 | 0 | 1.9 | 0.979 | wm_close 0.5 s | light_share_high | 0425-n0-r7 |  |
| 15 | 7 | mc | 7 | OK | True |  | 4 | 60 | 21096 | 2.2089 | 4.3538 | 0 | 0 | 2.058 | 0.992 | wm_close 0.4 s | light_share_high | 0427-mc-r7 |  |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | n0 | cold |  | light_share_high | 0359-cold-n0 |
| 2 | n0 | 1 |  | light_share_high | 0400-n0-r1 |
| 3 | mc | 1 |  | light_share_high | 0402-mc-r1 |
| 4 | mc | 2 |  | light_share_high | 0404-mc-r2 |
| 5 | n0 | 2 |  | light_share_high | 0407-n0-r2 |
| 6 | n0 | 3 |  | light_share_high | 0409-n0-r3 |
| 7 | mc | 3 |  | light_share_high | 0411-mc-r3 |
| 8 | mc | 4 |  | light_share_high | 0413-mc-r4 |
| 9 | n0 | 4 |  | light_share_high | 0415-n0-r4 |
| 10 | n0 | 5 |  | light_share_high | 0417-n0-r5 |
| 11 | mc | 5 |  | light_share_high | 0419-mc-r5 |
| 12 | mc | 6 |  | light_share_high | 0421-mc-r6 |
| 13 | n0 | 6 |  | light_share_high | 0423-n0-r6 |
| 14 | n0 | 7 |  | light_share_high | 0425-n0-r7 |
| 15 | mc | 7 |  | light_share_high | 0427-mc-r7 |

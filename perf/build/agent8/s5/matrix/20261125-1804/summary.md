# Timing matrix: S5 Phase 0.3 baseline: gameplay route (attract-long pad), 3D-only score; ship60, nat60, n4bp60 x4 at cap60 + natU x2 (info)

- matrix: <workspace>\build\agent8\s5\matrix-s5-baseline.json (copy in matrix.json); out: <workspace>\build\agent8\s5\matrix\20261125-1804
- started 2026-11-25 18:04, ended 19:24; 17 runs (17 OK), 14 scored; desktop WinSta0\Default
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 14 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

## Group base: ref ship60 (ref arm of the group), noise band +-22.3 %

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ship60 | 4/4 | 4 | 0 | 20.21 (19.23..23.75) | 22.3 | 59.45 | 113.78 | 386.8 | 9.92 | 44.51 | 1.32 |  |  |  | ref |
| nat60 | 4/4 | 4 | 0 | 16.71 (16.7..16.73) | 0.2 | 57.76 | 94.24 | 248.5 | 6.5 | 50.26 | 1.03 | -17.3 | -2.8 | -35.8 | within noise |
| n4bp60 | 4/4 | 4 | 0 | 16.77 (16.75..17.02) | 1.6 | 76 | 170.09 | 308.7 | 20.42 | 46.59 | 1.19 | -17 | 27.8 | -20.2 | within noise |
| natU | 2/2 | 2 | 0 | 5.77 (5.21..6.34) | 19.5 | 61.31 | 123.5 | 249.8 | 11.83 | 106.34 | 1.83 | -71.4 | 3.1 | -35.4 | FASTER (outside noise) |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | ship60 | 0 | OK | True |  | 5.01 | 60 | 4957 | 16.704 | 64.175 | 320 | 23 | 1.737 | 0 | wm_close 2 s | nongame_load | 1805-cold-ship60 |  |
| 2 | cold | nat60 | 0 | OK | True |  | 9.01 | 60 | 5256 | 16.7091 | 50.7805 | 211 | 6 | 1.179 | 0 | wm_close 1.1 s | nongame_load | 1809-cold-nat60 |  |
| 3 | cold | n4bp60 | 0 | OK | True |  | 6.02 | 60 | 4044 | 16.7291 | 123.178 | 586 | 61 | 1.392 | 0 | wm_close 1.1 s | nongame_load | 1812-cold-n4bp60 |  |
| 4 | 1 | ship60 | 1 | OK | True |  | 5.01 | 90 | 6269 | 23.747 | 113.829 | 1729 | 82 | 1.749 | 0.006061572818631 | wm_close 1.4 s | nongame_load | 1815-ship60-r1 |  |
| 5 | 1 | nat60 | 1 | OK | True |  | 5.01 | 90 | 8681 | 16.726 | 66.9803 | 1006 | 8 | 1.092 | 0 | wm_close 0.7 s | nongame_load | 1820-nat60-r1 |  |
| 6 | 1 | n4bp60 | 1 | OK | True |  | 5.01 | 90 | 6865 | 17.0209 | 129.916 | 1135 | 158 | 1.392 | 0 | wm_close 1.4 s | nongame_load | 1825-n4bp60-r1 |  |
| 7 | 1 | natU | 1 | OK | True |  | 8.01 | 90 | 17823 | 5.2085 | 72.5009 | 681 | 61 | 1.984 | 0.411434663075801 | wm_close 1.4 s | nongame_load | 1830-natU-r1 |  |
| 8 | 2 | nat60 | 2 | OK | True |  | 7.01 | 90 | 8701 | 16.7103 | 79.9207 | 604 | 65 | 1.132 | 0.000114929318469 | wm_close 0.7 s | nongame_load | 1835-nat60-r2 |  |
| 9 | 2 | n4bp60 | 2 | OK | True |  | 5.01 | 90 | 8310 | 16.7788 | 78.5966 | 809 | 44 | 1.16 | 0 | wm_close 0.6 s |  | 1839-n4bp60-r2 |  |
| 10 | 2 | natU | 2 | OK | True |  | 4 | 90 | 20461 | 6.335 | 50.1098 | 818 | 10 | 1.675 | 0.363325350667123 | wm_close 0.7 s |  | 1844-natU-r2 |  |
| 11 | 2 | ship60 | 2 | OK | True |  | 5.02 | 90 | 8470 | 19.234 | 50.064 | 789 | 8 | 1.188 | 0.00495867768595 | wm_close 0.6 s |  | 1849-ship60-r2 |  |
| 12 | 3 | n4bp60 | 3 | OK | True |  | 5.01 | 90 | 8464 | 16.7568 | 73.4092 | 899 | 28 | 1.149 | 0 | wm_close 0.7 s |  | 1854-n4bp60-r3 |  |
| 13 | 3 | ship60 | 3 | OK | True |  | 5.01 | 90 | 7923 | 20.459 | 62.077 | 926 | 17 | 1.243 | 0.002019437081913 | wm_close 0.6 s |  | 1859-ship60-r3 |  |
| 14 | 3 | nat60 | 3 | OK | True |  | 4.01 | 90 | 9394 | 16.7019 | 48.5433 | 779 | 2 | 0.955 | 0 | wm_close 0.5 s |  | 1904-nat60-r3 |  |
| 15 | 4 | ship60 | 4 | OK | True |  | 5.01 | 90 | 8100 | 19.965 | 56.829 | 1198 | 12 | 1.113 | 0.008641975308642 | wm_close 0.6 s |  | 1909-ship60-r4 |  |
| 16 | 4 | nat60 | 4 | OK | True |  | 5.01 | 90 | 9486 | 16.7006 | 45.8055 | 593 | 3 | 0.922 | 0 | wm_close 0.5 s |  | 1914-nat60-r4 |  |
| 17 | 4 | n4bp60 | 4 | OK | True |  | 4.01 | 90 | 8796 | 16.7462 | 60.1112 | 862 | 15 | 1.077 | 0 | wm_close 0.8 s |  | 1919-n4bp60-r4 |  |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | ship60 | cold |  | nongame_load | 1805-cold-ship60 |
| 2 | nat60 | cold |  | nongame_load | 1809-cold-nat60 |
| 3 | n4bp60 | cold |  | nongame_load | 1812-cold-n4bp60 |
| 4 | ship60 | 1 |  | nongame_load | 1815-ship60-r1 |
| 5 | nat60 | 1 |  | nongame_load | 1820-nat60-r1 |
| 6 | n4bp60 | 1 |  | nongame_load | 1825-n4bp60-r1 |
| 7 | natU | 1 |  | nongame_load | 1830-natU-r1 |
| 8 | nat60 | 2 |  | nongame_load | 1835-nat60-r2 |

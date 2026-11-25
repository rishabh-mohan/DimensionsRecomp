# Timing matrix: M8 session 3 smoke: functional check of the installed runner improvements (warmup_runs, new results.csv columns, 31-column sys.csv sampler). Hidden desktop, -Quick, never scored (m8-runner-rating.md C08604D8, C4/C5).

- matrix: <workspace>\build\agent8\session3\smoke\matrix-smoke.json (copy in matrix.json); out: <workspace>\build\agent8\session3\smoke\out-0734
- started 2026-11-25 07:34, ended 07:39; 4 runs (4 OK), 2 scored; desktop WinSta0\exebox-4C75JTA7J52ARY4ODDXJ3XE3WR; -Quick
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 2 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

> **FUNCTIONAL ONLY**: -Quick run; 4 of 4 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group smoke: ref s0 (ref arm of the group), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s0 | 1/1 | 0 | 0 | 2.95 (2.95..2.95) | 0 | 22.83 | 148.34 | 90 | 24 | 257.22 | 2.09 |  |  |  | ref |
| s0b | 1/1 | 0 | 0 | 3.06 (3.06..3.06) | 0 | 17.73 | 116.96 | 62 | 18 | 257.87 | 2.53 | 3.8 | -22.3 | -31.1 | no noise band |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | s0 | 0 | OK | False |  | 5.02 | 20 | 3529 | 2.294 | 11.004 | 7 | 3 | 2.223 | 0.93425899688297 | wm_close 0.7 s | light_share_high never_foreground nongame_load | 0734-cold-s0 | not timing: desktop WinSta0\exebox-4C75JTA7J52ARY4ODDXJ3XE3WR is not WinSta0\Default |
| 2 | warm | s0b | 0 | OK | False |  | 12 | 20 | 5339 | 2.928 | 46.698 | 81 | 22 | 1.922 | 0.757070612474246 | wm_close 0.8 s | light_share_high never_foreground nongame_load | 0735-warm1-s0b | not timing: desktop WinSta0\exebox-4C75JTA7J52ARY4ODDXJ3XE3WR is not WinSta0\Default |
| 3 | 1 | s0 | 1 | OK | False |  | 8.02 | 20 | 7717 | 2.946 | 22.833 | 45 | 12 | 2.094 | 0.846054166126733 | wm_close 0.8 s | light_share_high never_foreground nongame_load | 0736-s0-r1 | not timing: desktop WinSta0\exebox-4C75JTA7J52ARY4ODDXJ3XE3WR is not WinSta0\Default |
| 4 | 1 | s0b | 1 | OK | False |  | 11.06 | 20 | 7737 | 3.058 | 17.731 | 31 | 9 | 2.53 | 0.78867778208608 | wm_close 0.7 s | light_share_high never_foreground nongame_load | 0738-s0b-r1 | not timing: desktop WinSta0\exebox-4C75JTA7J52ARY4ODDXJ3XE3WR is not WinSta0\Default |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | s0 | cold |  | light_share_high never_foreground nongame_load | 0734-cold-s0 |
| 2 | s0b | warm |  | light_share_high never_foreground nongame_load | 0735-warm1-s0b |
| 3 | s0 | 1 |  | light_share_high never_foreground nongame_load | 0736-s0-r1 |
| 4 | s0b | 1 |  | light_share_high never_foreground nongame_load | 0738-s0b-r1 |

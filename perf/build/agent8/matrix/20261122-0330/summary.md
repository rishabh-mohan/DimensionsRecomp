# Timing matrix: Session 3 functional checks (agent slot, hidden desktop, NOT timing): d0t = devoff2 + REX_TIMER_WAIT_BLOCKING=1 (Agent 11) next to d0f = devoff2

- matrix: <workspace>\bench\agent8\run\matrix-s3-functional.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261122-0330
- started 2026-11-22 03:30, ended 03:34; 2 runs (2 OK), 2 scored; desktop WinSta0\exebox-OW7KJJJMKYBHPDBZXLFAPVIU6W
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 2 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

> **FUNCTIONAL ONLY**: 2 of 2 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group s3: ref d0f (ref arm of the group), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d0f | 1/1 | 0 | 0 | 4.19 (4.19..4.19) | 0 | 45.51 | 68.54 | 195.6 | 1.2 | 145.19 | 2.4 |  |  |  | ref |
| d0t | 1/1 | 0 | 0 | 6.5 (6.5..6.5) | 0 | 63.94 | 91.31 | 357.5 | 2.4 | 90.88 | 2.06 | 55.2 | 40.5 | 82.8 | no noise band |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | d0f | 1 | OK | False |  | 7.02 | 60 | 7261 | 4.191 | 45.512 | 163 | 1 | 2.401 | 0.552 | wm_close 5.1 s | never_foreground | 0330-d0f-r1 | not timing: desktop WinSta0\exebox-OW7KJJJMKYBHPDBZXLFAPVIU6W is not WinSta0\Default |
| 2 | 1 | d0t | 1 | OK | False |  | 10.01 | 60 | 4545 | 6.505 | 63.94 | 298 | 2 | 2.064 | 0.211 | wm_close 1.2 s | never_foreground | 0332-d0t-r1 | not timing: desktop WinSta0\exebox-OW7KJJJMKYBHPDBZXLFAPVIU6W is not WinSta0\Default |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | d0f | 1 |  | never_foreground | 0330-d0f-r1 |
| 2 | d0t | 1 |  | never_foreground | 0332-d0t-r1 |

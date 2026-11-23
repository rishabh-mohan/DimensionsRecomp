# Timing matrix: S4 invalidation volume (Agent 5, task #20): one functional devoff2 run with slow_frame_log_ms=1 (logging only, not for timing)

- matrix: <workspace>\bench\agent5\matrix-s4-invalvol.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261122-0620
- started 2026-11-22 06:20, ended 06:24; 1 runs (1 OK), 1 scored; desktop WinSta0\exebox-5EAK6AEJUL54DUW4ZDEK36UVXE
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 1 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

> **FUNCTIONAL ONLY**: 1 of 1 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group functional: ref a-vol (ref arm of the group), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| a-vol | 1/1 | 0 | 0 | 5.98 (5.98..5.98) | 0 | 63.01 | 92.68 | 406.8 | 3.6 | 87.65 | 2.28 |  |  |  | ref |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | a-vol | 1 | OK | False |  | 11.02 | 70 | 13148 | 5.981 | 63.012 | 1017 | 9 | 2.28 | 0.297 | wm_close 1.1 s | never_foreground | 0620-a-vol-r1 | not timing: desktop WinSta0\exebox-5EAK6AEJUL54DUW4ZDEK36UVXE is not WinSta0\Default |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | a-vol | 1 |  | never_foreground | 0620-a-vol-r1 |

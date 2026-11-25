# Timing matrix: M8 session 3 smoke: functional check of the installed runner improvements (warmup_runs, new results.csv columns, 31-column sys.csv sampler). Hidden desktop, -Quick, never scored (m8-runner-rating.md C08604D8, C4/C5).

- matrix: <workspace>\build\agent8\session3\smoke\matrix-smoke.json (copy in matrix.json); out: <workspace>\build\agent8\session3\smoke\ab-1-p0
- started 2026-11-25 07:40, ended 07:41; 1 runs (1 OK), 1 scored; desktop WinSta0\exebox-IDAFWVQGHOKI6XCZAAJQ22AYWL; -Quick
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 1 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

> **FUNCTIONAL ONLY**: -Quick run; 1 of 1 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group smoke: ref s0 (ref arm of the group), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s0 | 1/1 | 0 | 0 | 2.65 (2.65..2.65) | 0 | 14.31 | 105.13 | 65.9 | 23.98 | 289.21 | 2.15 |  |  |  | ref |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | s0 | 1 | OK | False |  | 5.02 | 20 | 8684 | 2.647 | 14.308 | 33 | 12 | 2.151 | 0.889912482726854 | wm_close 0.8 s | light_share_high never_foreground nongame_load | 0740-s0-r1 | not timing: desktop WinSta0\exebox-IDAFWVQGHOKI6XCZAAJQ22AYWL is not WinSta0\Default |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | s0 | 1 |  | light_share_high never_foreground nongame_load | 0740-s0-r1 |

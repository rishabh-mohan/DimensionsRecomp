# Timing matrix: NATIVE3D zero-code checks (agent slot, hidden desktop, functional, NOT timing): Agent 7's specs for Agent 1's slot item 3b (06:29). n2t/n3t/n2s on build/agent2/native3d-bin

- matrix: <workspace>\bench\agent8\zero\matrix-native3d-zero-code.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261122-0655
- started 2026-11-22 06:55, ended 06:57; 1 runs (1 OK), 1 scored; desktop WinSta0\exebox-Z6GPK4FJA27AD6EDS7HLIJPEVI
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 1 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

> **FUNCTIONAL ONLY**: 1 of 1 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group native3d: ref n3t (first arm (no ref set)), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| n3t | 1/1 | 0 | 0 | 5.89 (5.89..5.89) | 0 | 37.2 | 57.54 | 114 | 0 | 122.91 | 1.91 |  |  |  | ref |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | n3t | 1 | OK | False |  | 9.01 | 60 | 7375 | 5.894 | 37.1996 | 114 | 0 | 1.913 | 0.068 | wm_close 2.7 s | never_foreground | 0655-n3t-r1 | not timing: desktop WinSta0\exebox-Z6GPK4FJA27AD6EDS7HLIJPEVI is not WinSta0\Default |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | n3t | 1 |  | never_foreground | 0655-n3t-r1 |

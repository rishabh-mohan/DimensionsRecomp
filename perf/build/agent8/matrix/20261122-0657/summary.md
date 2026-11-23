# Timing matrix: NATIVE3D zero-code checks (agent slot, hidden desktop, functional, NOT timing): Agent 7's specs for Agent 1's slot item 3b (06:29). n2t/n3t/n2s on build/agent2/native3d-bin

- matrix: <workspace>\bench\agent8\zero\matrix-native3d-zero-code.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261122-0657
- started 2026-11-22 06:57, ended 06:59; 1 runs (1 OK), 1 scored; desktop WinSta0\exebox-Z6GPK4FJA27AD6EDS7HLIJPEVI
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 1 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

> **FUNCTIONAL ONLY**: 1 of 1 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group native3d: ref n2s (first arm (no ref set)), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| n2s | 1/1 | 0 | 0 | 6.18 (6.18..6.18) | 0 | 32.8 | 50.44 | 69 | 0 | 123.58 | 1.99 |  |  |  | ref |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | n2s | 1 | OK | False |  | 9.02 | 60 | 7415 | 6.179 | 32.799 | 69 | 0 | 1.992 | 0.01 | wm_close 1 s | never_foreground | 0657-n2s-r1 | not timing: desktop WinSta0\exebox-Z6GPK4FJA27AD6EDS7HLIJPEVI is not WinSta0\Default |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | n2s | 1 |  | never_foreground | 0657-n2s-r1 |

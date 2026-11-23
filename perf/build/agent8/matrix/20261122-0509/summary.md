# Timing matrix: Agent 7, task #22 step 1: shader dump run on native3d-bin (agent slot, hidden desktop OK, NOT timing). One arm: sd = n0 config + LEGO_DUMP_MISSING_SHADERS=<run>\shader-dumps

- matrix: <workspace>\bench\agent7\matrix-shader-dump.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261122-0509
- started 2026-11-22 05:09, ended 05:11; 1 runs (1 OK), 1 scored; desktop WinSta0\exebox-HVWYEOOSPZ42UGVQIK5VHAIZQU
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 1 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

> **FUNCTIONAL ONLY**: 1 of 1 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group native3d: ref sd (ref arm of the group), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sd | 1/1 | 0 | 0 | 9.44 (9.44..9.44) | 0 | 30.73 | 42.02 | 38 | 0 | 93.56 | 1.66 |  |  |  | ref |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | sd | 1 | OK | False |  | 11.02 | 60 | 5615 | 9.4369 | 30.7317 | 38 | 0 | 1.665 | 0.062 | wm_close 3.4 s |  | 0509-sd-r1 | not timing: desktop WinSta0\exebox-HVWYEOOSPZ42UGVQIK5VHAIZQU is not WinSta0\Default |

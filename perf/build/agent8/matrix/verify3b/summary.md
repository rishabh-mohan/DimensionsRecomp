# Timing matrix: Window 3: devoff2 (ref) vs baseline, devoff2 + Agent 11 ON bundle, native2 N0 (and devoff2 + Agent 12 ON bundle if it fits). Uncapped, title loop, no input

- matrix: <workspace>\bench\agent8\run\matrix-window3.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\verify3b
- started 2026-11-21 23:44, ended 23:48; 2 runs (2 OK), 2 scored; desktop WinSta0\exebox-SXQB2J5NQCBLSAODQXEXWYGD6H
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians

> **FUNCTIONAL ONLY**: 2 of 2 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group w3: ref d0 (ref arm of the group), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d0 | 1/1 | 0 | 3.72 (3.72..3.72) | 0 | 13.02 | 24.99 | 6 | 0 | 226.86 | 2.73 |  |  |  | ref |
| n0 | 1/1 | 0 | 9.2 (9.2..9.2) | 0 | 30.27 | 53.14 | 42 | 0 | 101.34 | 1.96 | 147.2 | 132.4 | 600 | no noise band |

## Runs

| # | round | arm | rep | status | valid | boot s | frames | median ms | p99 ms | >33 | >100 | cpu | close | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | d0 | 1 | OK | False | 8.01 | 11343 | 3.72 | 13.021 | 5 | 0 | 2.73 | wm_close 1.1 s | 2344-d0-r1 | not timing: desktop WinSta0\exebox-SXQB2J5NQCBLSAODQXEXWYGD6H is not WinSta0\Default |
| 2 | 1 | n0 | 1 | OK | False | 12.01 | 5067 | 9.1974 | 30.2654 | 35 | 0 | 1.96 | wm_close 1.3 s | 2346-n0-r1 | not timing: desktop WinSta0\exebox-SXQB2J5NQCBLSAODQXEXWYGD6H is not WinSta0\Default, build processes: clang++:21676 |

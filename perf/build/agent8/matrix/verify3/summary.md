# Timing matrix: Window 3: devoff2 (ref) vs baseline, devoff2 + Agent 11 ON bundle, devoff2 + Agent 12 ON bundle. Uncapped (framerate_limit=0), title loop, no input

- matrix: <workspace>\bench\agent8\run\matrix-window3.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\verify3
- started 2026-11-21 23:34, ended 23:37; 2 runs (0 OK), 2 scored; desktop WinSta0\exebox-IW4HBGG43BZHP4ZZR4S7KMR34E
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians

> **FUNCTIONAL ONLY**: 2 of 2 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group w3: ref d0 (ref arm of the group), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d0 | 0/1 | 0 |  (..) |  |  |  |  |  |  |  |  |  |  | ref |
| base | 0/1 | 0 |  (..) |  |  |  |  |  |  |  |  |  |  | no OK runs |

## Runs

| # | round | arm | rep | status | valid | boot s | frames | median ms | p99 ms | >33 | >100 | cpu | close | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | d0 | 1 | PROBLEM | False | 8.02 | 3615 | 3.805 | 36.311 | 46 | 0 | 2.061 | wm_close 2.5 s | 2334-d0-r1 | RUNNER ERROR: Stream was not readable. (run-timing.ps1 line 323) / SHORT WINDOW: only 24.550508 s of frames after the start mark / not timing: desktop WinSta0\exebox-IW4HBGG43BZHP4ZZR4S7KMR34E is not WinSta0\Default, no complete window |
| 2 | 1 | base | 1 | PROBLEM | False | 11.01 | 614 | 10.689 | 81.784 | 165 | 1 | 1.952 | wm_close 2.7 s | 2336-base-r1 | RUNNER ERROR: The process cannot access the file '<workspace>\build\agent8\matrix\verify3\runs\2336-base-r1\proc.csv' because it is being used by another process. (run-timing.ps1 line 323) / SHORT WINDOW: only 13.42146 s of frames after the start mark / not timing: desktop WinSta0\exebox-IW4HBGG43BZHP4ZZR4S7KMR34E is not WinSta0\Default, no complete window |

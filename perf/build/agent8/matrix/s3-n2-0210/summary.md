# Timing matrix: NATIVE ON build, FUNCTIONAL rows (hidden desktop OK, not timing): Agent 4 N1-N3 threaded paths and F1/F2 state-call counts, Agent 6 P1/P2 PSO counters

- matrix: <workspace>\bench\agent8\run\matrix-native-functional.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\s3-n2-0210
- started 2026-11-22 02:10, ended 02:12; 1 runs (1 OK), 1 scored; desktop WinSta0\exebox-57EZY2EV33A7IIWBEM7GSO27QD
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians

> **FUNCTIONAL ONLY**: 1 of 1 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group threaded: ref n2 (first arm (no ref set)), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| n2 | 1/1 | 0 | 6.66 (6.66..6.66) | 0 | 24.72 | 41.5 | 32 | 0 | 135.41 | 1.92 |  |  |  | ref |

## Runs

| # | round | arm | rep | status | valid | boot s | frames | median ms | p99 ms | >33 | >100 | cpu | close | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | n2 | 1 | OK | False | 10.03 | 8125 | 6.6639 | 24.7184 | 32 | 0 | 1.922 | wm_close 2.7 s | 0210-n2-r1 | not timing: desktop WinSta0\exebox-57EZY2EV33A7IIWBEM7GSO27QD is not WinSta0\Default |

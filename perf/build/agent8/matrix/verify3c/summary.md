# Timing matrix: Window 3: devoff2 (ref) vs baseline, devoff2 + Agent 11 ON bundle, native2 N0 (and devoff2 + Agent 12 ON bundle if it fits). Uncapped, title loop, no input

- matrix: <workspace>\bench\agent8\run\matrix-window3.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\verify3c
- started 2026-11-22 00:03, ended 00:07; 2 runs (2 OK), 2 scored; desktop WinSta0\exebox-KBQVC7YAQRWQSURCGLYIMVMP7J
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians

> **FUNCTIONAL ONLY**: 2 of 2 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group w3: ref base (first arm (no ref set)), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| base | 1/1 | 0 | 3.83 (3.83..3.83) | 0 | 41.01 | 68.22 | 148.8 | 1.2 | 138.4 | 2.11 |  |  |  | ref |
| d11 | 1/1 | 0 | 3.8 (3.8..3.8) | 0 | 40.8 | 61.63 | 181.1 | 1.2 | 141.74 | 2.25 | -0.9 | -0.5 | 21.7 | no noise band |

## Runs

| # | round | arm | rep | status | valid | boot s | frames | median ms | p99 ms | >33 | >100 | cpu | close | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | base | 1 | OK | False | 11 | 6921 | 3.831 | 41.011 | 124 | 1 | 2.11 | wm_close 1.7 s | 0003-base-r1 | not timing: desktop WinSta0\exebox-KBQVC7YAQRWQSURCGLYIMVMP7J is not WinSta0\Default |
| 2 | 1 | d11 | 1 | OK | False | 12.49 | 7090 | 3.798 | 40.795 | 151 | 1 | 2.247 | wm_close 4.9 s | 0005-d11-r1 | not timing: desktop WinSta0\exebox-KBQVC7YAQRWQSURCGLYIMVMP7J is not WinSta0\Default |

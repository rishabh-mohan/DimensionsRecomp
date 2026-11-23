# Timing matrix: NATIVE ON build, FUNCTIONAL rows (hidden desktop OK, not timing): Agent 4 N1-N3 threaded paths and F1/F2 state-call counts, Agent 6 P1/P2 PSO counters

- matrix: <workspace>\bench\agent8\run\matrix-native-functional.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\s3-n123-0205
- started 2026-11-22 02:05, ended 02:09; 3 runs (2 OK), 3 scored; desktop WinSta0\exebox-JCFBR4XUTV6VRUUNTOV3ZJJETY
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians

> **FUNCTIONAL ONLY**: 3 of 3 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group threaded: ref n1 (ref arm of the group), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| n1 | 1/1 | 0 | 8.04 (8.04..8.04) | 0 | 41.41 | 67.72 | 132 | 0 | 108.43 | 1.75 |  |  |  | ref |
| n2 | 0/1 | 0 |  (..) |  |  |  |  |  |  |  |  |  |  | no OK runs |
| n3 | 1/1 | 0 | 10.53 (10.53..10.53) | 0 | 25.34 | 58.75 | 32 | 0 | 90.23 | 1.98 | 31 | -38.8 | -75.8 | no noise band |

## Runs

| # | round | arm | rep | status | valid | boot s | frames | median ms | p99 ms | >33 | >100 | cpu | close | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | n1 | 1 | OK | False | 16.09 | 6506 | 8.036 | 41.4128 | 132 | 0 | 1.75 | wm_close 2.4 s | 0205-n1-r1 | not timing: desktop WinSta0\exebox-JCFBR4XUTV6VRUUNTOV3ZJJETY is not WinSta0\Default, build processes: rexglue:61380 |
| 2 | 1 | n2 | 1 | NOT STARTED |  |  |  |  |  |  |  |  |  |  | free RAM 5.77 GB is under 6 GB: not starting |
| 3 | 1 | n3 | 1 | OK | False | 11.01 | 5414 | 10.5293 | 25.341 | 32 | 0 | 1.979 | wm_close 0.8 s | 0208-n3-r1 | not timing: desktop WinSta0\exebox-JCFBR4XUTV6VRUUNTOV3ZJJETY is not WinSta0\Default, build processes: rexglue:68676 |

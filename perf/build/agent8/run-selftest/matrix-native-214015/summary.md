# Timing matrix: selftest native + seed chain (fake exe)

- matrix: <workspace>\build\agent8\run-selftest\matrix-test\matrix-st-native.json (copy in matrix.json); out: <workspace>\build\agent8\run-selftest\matrix-native-214015
- started 2026-11-21 21:40, ended 21:40; 3 runs (0 OK), 3 scored; desktop WinSta0\exebox-3LMYHDBXIEQA4QZFS6Z436D4MI; -Quick
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians

> **FUNCTIONAL ONLY**: -Quick run; 3 of 3 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group n: ref N1 (ref arm of the group), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N1 | 0/1 | 0 |  (..) |  |  |  |  |  |  |  |  |  |  | ref |
| N2 | 0/1 | 0 |  (..) |  |  |  |  |  |  |  |  |  |  | no OK runs |
| N3 | 0/1 | 0 |  (..) |  |  |  |  |  |  |  |  |  |  | no OK runs |

## Runs

| # | round | arm | rep | status | valid | boot s | frames | median ms | p99 ms | >33 | >100 | cpu | close | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | N1 | 1 | NOT STARTED |  |  |  |  |  |  |  |  |  |  | free RAM 5.76 GB is under 6 GB: not starting |
| 2 | 1 | N2 | 1 | SKIPPED |  |  |  |  |  |  |  |  |  |  | seed source arm N1 has no completed run in this matrix |
| 3 | 1 | N3 | 1 | SKIPPED |  |  |  |  |  |  |  |  |  |  | seed source arm N2 has no completed run in this matrix |

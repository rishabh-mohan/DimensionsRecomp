# Timing matrix: selftest native + seed chain (fake exe)

- matrix: <workspace>\build\agent8\run-selftest\matrix-test\matrix-st-native.json (copy in matrix.json); out: <workspace>\build\agent8\run-selftest\matrix-native-024642
- started 2026-11-22 02:46, ended 02:47; 3 runs (3 OK), 3 scored; desktop WinSta0\exebox-3GG3R3L5QXDCKHYQEM26VOFDH5; -Quick
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians

> **FUNCTIONAL ONLY**: -Quick run; 3 of 3 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group n: ref N1 (ref arm of the group), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N1 | 1/1 | 0 | 16 (16..16) | 0 | 120 | 120 | 119.8 | 59.92 | 51.93 | 0 |  |  |  | ref |
| N2 | 1/1 | 0 | 16 (16..16) | 0 | 120 | 120 | 119.8 | 59.92 | 51.93 | 0.02 | 0 | 0 | 0 | no noise band |
| N3 | 1/1 | 0 | 16 (16..16) | 0 | 120 | 120 | 119.8 | 59.92 | 51.93 | 0.01 | 0 | 0 | 0 | no noise band |

## Runs

| # | round | arm | rep | status | valid | boot s | frames | median ms | p99 ms | >33 | >100 | cpu | close | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | N1 | 1 | OK | False | 2.01 | 156 | 16 | 120 | 6 | 3 | 0.005 | wm_close 0.1 s | 0246-N1-r1 | not timing: desktop WinSta0\exebox-3GG3R3L5QXDCKHYQEM26VOFDH5 is not WinSta0\Default |
| 2 | 1 | N2 | 1 | OK | False | 2 | 156 | 16 | 120 | 6 | 3 | 0.016 | wm_close 0 s | 0246-N2-r1 | not timing: desktop WinSta0\exebox-3GG3R3L5QXDCKHYQEM26VOFDH5 is not WinSta0\Default |
| 3 | 1 | N3 | 1 | OK | False | 2.01 | 156 | 16 | 120 | 6 | 3 | 0.01 | wm_close 0.1 s | 0247-N3-r1 | not timing: desktop WinSta0\exebox-3GG3R3L5QXDCKHYQEM26VOFDH5 is not WinSta0\Default |

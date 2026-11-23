# Timing matrix: NATIVE ON build, Agent 5 uploads (task #4): u0 batch-2 defaults, u1 legacy upload CPU paths, u2 texture staging pool. Title/attract loop from boot, no input needed

- matrix: <workspace>\bench\agent8\run\matrix-native-uploads.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261122-0438
- started 2026-11-22 04:38, ended 04:51; 4 runs (4 OK), 3 scored; desktop WinSta0\exebox-4FL55QZSZVCFAAG22A54PM7YM7
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 3 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

> **FUNCTIONAL ONLY**: 4 of 4 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group upload-diag: ref s0 (ref arm of the group), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s0 | 1/1 | 0 | 0 | 8.94 (8.94..8.94) | 0 | 23.89 | 37.7 | 15 | 0 | 109.02 | 1.85 |  |  |  | ref |
| s1 | 1/1 | 0 | 0 | 9.06 (9.06..9.06) | 0 | 42.28 | 72.73 | 120.5 | 0 | 94.61 | 1.86 | 1.3 | 77 | 703.3 | no noise band |
| s2 | 1/1 | 0 | 0 | 8.56 (8.56..8.56) | 0 | 23.29 | 37.47 | 13.5 | 0 | 110.44 | 1.91 | -4.3 | -2.5 | -10 | no noise band |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | s0 | 0 | OK | False |  | 15 | 60 | 4178 | 7.7991 | 14.3809 | 0 | 0 | 1.906 | 0.267 | wm_close 1 s |  | 0439-cold-s0 | not timing: desktop WinSta0\exebox-4FL55QZSZVCFAAG22A54PM7YM7 is not WinSta0\Default |
| 2 | 1 | s0 | 1 | OK | False |  | 7.01 | 60 | 13083 | 8.9428 | 23.8879 | 30 | 0 | 1.849 | 0.079 | wm_close 0.6 s |  | 0441-s0-r1 | not timing: desktop WinSta0\exebox-4FL55QZSZVCFAAG22A54PM7YM7 is not WinSta0\Default |
| 3 | 1 | s1 | 1 | OK | False |  | 8.01 | 60 | 11353 | 9.0558 | 42.2831 | 241 | 0 | 1.864 | 0.027 | wm_close 1.1 s |  | 0444-s1-r1 | not timing: desktop WinSta0\exebox-4FL55QZSZVCFAAG22A54PM7YM7 is not WinSta0\Default |
| 4 | 1 | s2 | 1 | OK | False |  | 10 | 60 | 13253 | 8.5591 | 23.2916 | 27 | 0 | 1.908 | 0.047 | wm_close 0.8 s |  | 0447-s2-r1 | not timing: desktop WinSta0\exebox-4FL55QZSZVCFAAG22A54PM7YM7 is not WinSta0\Default |

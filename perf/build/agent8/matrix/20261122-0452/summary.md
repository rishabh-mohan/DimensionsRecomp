# Timing matrix: NATIVE3D functional check (agent slot, hidden desktop OK, NOT timing): Agent 4 task #12 step 3, the S3.2 hash=0 guard. n0/n2/n3 on build/agent2/native3d-bin

- matrix: <workspace>\bench\agent4\s3\matrix-native3d-functional.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261122-0452
- started 2026-11-22 04:52, ended 04:59; 3 runs (3 OK), 3 scored; desktop WinSta0\exebox-JKI2BEK5MTCCNER6JE33KV5K6L
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 3 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

> **FUNCTIONAL ONLY**: 3 of 3 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group native3d: ref n0 (ref arm of the group), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| n0 | 1/1 | 0 | 0 | 9.26 (9.26..9.26) | 0 | 23.74 | 34.85 | 8 | 0 | 101.04 | 1.91 |  |  |  | ref |
| n2 | 1/1 | 0 | 0 | 7.21 (7.21..7.21) | 0 | 33.69 | 54.46 | 74 | 0 | 109.63 | 1.83 | -22.2 | 41.9 | 825.1 | no noise band |
| n3 | 1/1 | 0 | 0 | 6.68 (6.68..6.68) | 0 | 32.26 | 51.44 | 68 | 0 | 116.71 | 2.07 | -27.9 | 35.9 | 750 | no noise band |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | n0 | 1 | OK | False |  | 9.01 | 60 | 6063 | 9.2646 | 23.7357 | 8 | 0 | 1.908 | 0.003 | wm_close 0.8 s |  | 0452-n0-r1 | not timing: desktop WinSta0\exebox-JKI2BEK5MTCCNER6JE33KV5K6L is not WinSta0\Default |
| 2 | 1 | n2 | 1 | OK | False |  | 9.01 | 60 | 6578 | 7.2119 | 33.6926 | 74 | 0 | 1.833 | 0.001 | wm_close 1.1 s |  | 0454-n2-r1 | not timing: desktop WinSta0\exebox-JKI2BEK5MTCCNER6JE33KV5K6L is not WinSta0\Default |
| 3 | 1 | n3 | 1 | OK | False |  | 8.02 | 60 | 7003 | 6.6794 | 32.2597 | 68 | 0 | 2.07 | 0.014 | wm_close 2.9 s |  | 0456-n3-r1 | not timing: desktop WinSta0\exebox-JKI2BEK5MTCCNER6JE33KV5K6L is not WinSta0\Default |

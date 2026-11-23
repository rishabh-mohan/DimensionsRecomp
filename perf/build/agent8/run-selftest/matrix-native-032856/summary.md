# Timing matrix: selftest native + seed chain (fake exe)

- matrix: <workspace>\build\agent8\run-selftest\matrix-test\matrix-st-native.json (copy in matrix.json); out: <workspace>\build\agent8\run-selftest\matrix-native-032856
- started 2026-11-22 03:28, ended 03:29; 3 runs (3 OK), 3 scored; desktop WinSta0\exebox-YOFUE7NUMYT4IYOVVGVDAXT6Q2; -Quick
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 3 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

> **FUNCTIONAL ONLY**: -Quick run; 3 of 3 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group n: ref N1 (ref arm of the group), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N1 | 1/1 | 0 | 0 | 16 (16..16) | 0 | 120 | 120 | 119.8 | 59.92 | 51.93 | 0.01 |  |  |  | ref |
| N2 | 1/1 | 0 | 0 | 16 (16..16) | 0 | 120 | 120 | 119.8 | 59.92 | 51.93 | 0.02 | 0 | 0 | 0 | no noise band |
| N3 | 1/1 | 0 | 0 | 16 (16..16) | 0 | 120 | 120 | 119.8 | 59.92 | 51.93 | 0 | 0 | 0 | 0 | no noise band |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | N1 | 1 | OK | False |  | 2.01 | 3 | 156 | 16 | 120 | 6 | 3 | 0.01 | 0 | wm_close 0 s | install_marker_lost | 0328-N1-r1 | not timing: desktop WinSta0\exebox-YOFUE7NUMYT4IYOVVGVDAXT6Q2 is not WinSta0\Default |
| 2 | 1 | N2 | 1 | OK | False |  | 2.01 | 3 | 156 | 16 | 120 | 6 | 3 | 0.016 | 0 | wm_close 0.1 s | install_marker_lost | 0329-N2-r1 | not timing: desktop WinSta0\exebox-YOFUE7NUMYT4IYOVVGVDAXT6Q2 is not WinSta0\Default |
| 3 | 1 | N3 | 1 | OK | False |  | 2 | 3 | 156 | 16 | 120 | 6 | 3 | 0 | 0 | wm_close 0 s | install_marker_lost | 0329-N3-r1 | not timing: desktop WinSta0\exebox-YOFUE7NUMYT4IYOVVGVDAXT6Q2 is not WinSta0\Default |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | N1 | 1 |  | install_marker_lost | 0328-N1-r1 |
| 2 | N2 | 1 |  | install_marker_lost | 0329-N2-r1 |
| 3 | N3 | 1 |  | install_marker_lost | 0329-N3-r1 |

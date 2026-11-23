# Timing matrix: selftest matrix (fake exe)

- matrix: <workspace>\build\agent8\run-selftest\matrix-test\matrix-st.json (copy in matrix.json); out: <workspace>\build\agent8\run-selftest\matrix-032745
- started 2026-11-22 03:27, ended 03:28; 5 runs (5 OK), 4 scored; desktop WinSta0\exebox-YOFUE7NUMYT4IYOVVGVDAXT6Q2; -Quick
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 4 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

> **FUNCTIONAL ONLY**: -Quick run; 5 of 5 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group g: ref A (ref arm of the group), noise band +-0 %

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 2/2 | 0 | 0 | 16 (16..16) | 0 | 120 | 120 | 119.8 | 59.92 | 51.93 | 0 |  |  |  | ref |
| B | 2/2 | 0 | 0 | 16 (16..16) | 0 | 120 | 120 | 119.8 | 59.92 | 51.93 | 0 | 0 | 0 | 0 | within noise |
| C | 0/0 | 0 | 0 |  (..) |  |  |  |  |  |  |  |  |  |  | SKIPPED: bin build\agent8\run-selftest\no-such-bin is missing or has no MANIFEST.txt (not staged yet?) |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | A | 0 | OK | False |  | 2 | 3 | 156 | 16 | 120 | 6 | 3 | 0.005 | 0 | wm_close 0.1 s | install_marker_lost | 0327-cold-A | not timing: desktop WinSta0\exebox-YOFUE7NUMYT4IYOVVGVDAXT6Q2 is not WinSta0\Default |
| 2 | 1 | A | 1 | OK | False |  | 2.01 | 3 | 156 | 16 | 120 | 6 | 3 | 0 | 0 | wm_close 0.1 s | install_marker_lost | 0328-A-r1 | not timing: desktop WinSta0\exebox-YOFUE7NUMYT4IYOVVGVDAXT6Q2 is not WinSta0\Default |
| 3 | 1 | B | 1 | OK | False |  | 2.01 | 5 | 156 | 16 | 120 | 6 | 3 | 0 | 0 | wm_close 0.1 s | install_marker_lost | 0328-B-r1 | not timing: desktop WinSta0\exebox-YOFUE7NUMYT4IYOVVGVDAXT6Q2 is not WinSta0\Default |
| 4 | 2 | B | 2 | OK | False |  | 2.01 | 5 | 156 | 16 | 120 | 6 | 3 | 0 | 0 | wm_close 0.1 s | install_marker_lost | 0328-B-r2 | not timing: desktop WinSta0\exebox-YOFUE7NUMYT4IYOVVGVDAXT6Q2 is not WinSta0\Default |
| 5 | 2 | A | 2 | OK | False |  | 2.02 | 3 | 156 | 16 | 120 | 6 | 3 | 0.005 | 0 | wm_close 0.1 s | install_marker_lost | 0328-A-r2 | not timing: desktop WinSta0\exebox-YOFUE7NUMYT4IYOVVGVDAXT6Q2 is not WinSta0\Default |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | A | cold |  | install_marker_lost | 0327-cold-A |
| 2 | A | 1 |  | install_marker_lost | 0328-A-r1 |
| 3 | B | 1 |  | install_marker_lost | 0328-B-r1 |
| 4 | B | 2 |  | install_marker_lost | 0328-B-r2 |
| 5 | A | 2 |  | install_marker_lost | 0328-A-r2 |

## Skipped arms

- C: bin build\agent8\run-selftest\no-such-bin is missing or has no MANIFEST.txt (not staged yet?)

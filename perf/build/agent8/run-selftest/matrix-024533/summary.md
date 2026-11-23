# Timing matrix: selftest matrix (fake exe)

- matrix: <workspace>\build\agent8\run-selftest\matrix-test\matrix-st.json (copy in matrix.json); out: <workspace>\build\agent8\run-selftest\matrix-024533
- started 2026-11-22 02:45, ended 02:46; 5 runs (5 OK), 4 scored; desktop WinSta0\exebox-3GG3R3L5QXDCKHYQEM26VOFDH5; -Quick
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians

> **FUNCTIONAL ONLY**: -Quick run; 5 of 5 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group g: ref A (ref arm of the group), noise band +-0 %

| arm | OK/runs | valid | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 2/2 | 0 | 16 (16..16) | 0 | 120 | 120 | 119.8 | 59.92 | 51.93 | 0 |  |  |  | ref |
| B | 2/2 | 0 | 16 (16..16) | 0 | 120 | 120 | 119.8 | 59.92 | 51.93 | 0 | 0 | 0 | 0 | within noise |
| C | 0/0 | 0 |  (..) |  |  |  |  |  |  |  |  |  |  | SKIPPED: bin build\agent8\run-selftest\no-such-bin is missing or has no MANIFEST.txt (not staged yet?) |

## Runs

| # | round | arm | rep | status | valid | boot s | frames | median ms | p99 ms | >33 | >100 | cpu | close | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | A | 0 | OK | False | 2.01 | 156 | 16 | 120 | 6 | 3 | 0 | wm_close 0.1 s | 0245-cold-A | not timing: desktop WinSta0\exebox-3GG3R3L5QXDCKHYQEM26VOFDH5 is not WinSta0\Default, build processes: ninja:96532 |
| 2 | 1 | A | 1 | OK | False | 2.01 | 156 | 16 | 120 | 6 | 3 | 0.01 | wm_close 0 s | 0245-A-r1 | not timing: desktop WinSta0\exebox-3GG3R3L5QXDCKHYQEM26VOFDH5 is not WinSta0\Default |
| 3 | 1 | B | 1 | OK | False | 2 | 156 | 16 | 120 | 6 | 3 | 0.005 | wm_close 0 s | 0246-B-r1 | not timing: desktop WinSta0\exebox-3GG3R3L5QXDCKHYQEM26VOFDH5 is not WinSta0\Default |
| 4 | 2 | B | 2 | OK | False | 2.01 | 156 | 16 | 120 | 6 | 3 | 0.005 | wm_close 0.1 s | 0246-B-r2 | not timing: desktop WinSta0\exebox-3GG3R3L5QXDCKHYQEM26VOFDH5 is not WinSta0\Default |
| 5 | 2 | A | 2 | OK | False | 2.01 | 156 | 16 | 120 | 6 | 3 | 0 | wm_close 0.1 s | 0246-A-r2 | not timing: desktop WinSta0\exebox-3GG3R3L5QXDCKHYQEM26VOFDH5 is not WinSta0\Default |

## Skipped arms

- C: bin build\agent8\run-selftest\no-such-bin is missing or has no MANIFEST.txt (not staged yet?)

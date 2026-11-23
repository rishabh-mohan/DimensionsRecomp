# Timing matrix: Agent 11 task #24: execution-speed opt-out pairs, devoff2 d0 (off) vs d0e (on)

- matrix: <workspace>\build\agent11\pthrottle\pairs\20261122-0600-meta\pthrottle-pairs.json (copy in matrix.json); out: <workspace>\build\agent11\pthrottle\pairs\20261122-0600
- started 2026-11-22 06:00, ended 06:18; 6 runs (6 OK), 6 scored; desktop WinSta0\exebox-V3ZHZVK3TOQGKBPS47I7GMAF2M
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 1 of 6 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

> **FUNCTIONAL ONLY**: 6 of 6 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group pt: ref d0 (ref arm of the group), noise band +-39.7 %

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d0 | 3/3 | 0 | 0 | 4.84 (4.61..6.54) | 39.7 | 62.65 | 98.78 | 468.1 | 5.33 | 93.23 | 2.28 |  |  |  | ref |
| d0e | 2/3 | 0 | 1 | 6.92 (6.78..7.05) | 3.9 | 66.45 | 102.77 | 454 | 5.67 | 74.23 | 2.28 | 42.8 | 6.1 | -3 | SLOWER (outside noise) |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | d0 | 1 | OK | False |  | 10 | 60 | 9580 | 4.614 | 62.654 | 617 | 9 | 2.324 | 0.485 | wm_close 1.2 s | never_foreground | 0600-d0-r1 | not timing: desktop WinSta0\exebox-V3ZHZVK3TOQGKBPS47I7GMAF2M is not WinSta0\Default |
| 2 | 1 | d0e | 1 | OK | False |  | 10.01 | 60 | 6898 | 7.052 | 61.6 | 611 | 5 | 2.327 | 0.148 | wm_close 2 s | never_foreground | 0604-d0e-r1 | not timing: desktop WinSta0\exebox-V3ZHZVK3TOQGKBPS47I7GMAF2M is not WinSta0\Default |
| 3 | 2 | d0e | 2 | OK | False | EXCL | 12.01 | 60 | 14237 | 2.917 | 39.967 | 257 | 1 | 2.079 | 0.659 | wm_close 3.4 s | light_phase never_foreground | 0607-d0e-r2 | not timing: desktop WinSta0\exebox-V3ZHZVK3TOQGKBPS47I7GMAF2M is not WinSta0\Default / EXCLUDED: light_phase |
| 4 | 2 | d0 | 2 | OK | False |  | 8.01 | 60 | 7479 | 6.537 | 62.178 | 722 | 5 | 2.313 | 0.258 | wm_close 4.3 s | never_foreground | 0610-d0-r2 | not timing: desktop WinSta0\exebox-V3ZHZVK3TOQGKBPS47I7GMAF2M is not WinSta0\Default |
| 5 | 3 | d0 | 3 | OK | False |  | 12.03 | 60 | 8395 | 4.842 | 66.881 | 768 | 10 | 2.202 | 0.457 | wm_close 0.8 s | never_foreground | 0613-d0-r3 | not timing: desktop WinSta0\exebox-V3ZHZVK3TOQGKBPS47I7GMAF2M is not WinSta0\Default |
| 6 | 3 | d0e | 3 | OK | False |  | 9.02 | 60 | 6465 | 6.781 | 71.3 | 751 | 12 | 2.234 | 0.201 | wm_close 1 s | ticks_skipped never_foreground | 0616-d0e-r3 | not timing: desktop WinSta0\exebox-V3ZHZVK3TOQGKBPS47I7GMAF2M is not WinSta0\Default |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | d0 | 1 |  | never_foreground | 0600-d0-r1 |
| 2 | d0e | 1 |  | never_foreground | 0604-d0e-r1 |
| 3 | d0e | 2 | light_phase | never_foreground | 0607-d0e-r2 |
| 4 | d0 | 2 |  | never_foreground | 0610-d0-r2 |
| 5 | d0 | 3 |  | never_foreground | 0613-d0-r3 |
| 6 | d0e | 3 |  | ticks_skipped never_foreground | 0616-d0e-r3 |

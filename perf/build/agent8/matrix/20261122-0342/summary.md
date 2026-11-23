# Timing matrix: Window 4 (Agent 8, session 3): B = devoffB (codegen B) vs d0 = devoff2 (primary), then d3 = devoff3; optional d0t = devoff2 + REX_TIMER_WAIT_BLOCKING=1

- matrix: <workspace>\bench\agent8\run\matrix-window4.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261122-0342
- started 2026-11-22 03:42, ended 03:48; 5 runs (5 OK), 4 scored; desktop WinSta0\exebox-DMTARMUBZWO2RQC7CO33E3NBBO; -Quick
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 4 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

> **FUNCTIONAL ONLY**: -Quick run; 5 of 5 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group w4: ref d0 (ref arm of the group), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d0 | 1/1 | 0 | 0 | 3.51 (3.51..3.51) | 0 | 38.75 | 78.56 | 171 | 3 | 172.11 | 2.2 |  |  |  | ref |
| B | 1/1 | 0 | 0 | 3.89 (3.89..3.89) | 0 | 61.7 | 92.87 | 509.7 | 3 | 100.35 | 2.13 | 10.7 | 59.2 | 198.2 | no noise band |
| d3 | 1/1 | 0 | 0 | 4.2 (4.2..4.2) | 0 | 55.23 | 101.91 | 416.1 | 5.99 | 94.2 | 1.9 | 19.6 | 42.5 | 143.4 | no noise band |
| d0t | 1/1 | 0 | 0 | 3.56 (3.56..3.56) | 0 | 32.91 | 48.58 | 99 | 3 | 166.34 | 1.68 | 1.4 | -15.1 | -42.1 | no noise band |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | d0 | 0 | OK | False |  | 8.01 | 20 | 2171 | 3.269 | 21.385 | 5 | 0 | 2.356 | 0.723 | wm_close 1.7 s | light_share_high build_procs_window never_foreground | 0342-cold-d0 | not timing: desktop WinSta0\exebox-DMTARMUBZWO2RQC7CO33E3NBBO is not WinSta0\Default, build processes: cmake:18536 |
| 2 | 1 | d0 | 1 | OK | False |  | 13.02 | 20 | 3443 | 3.513 | 38.748 | 57 | 1 | 2.204 | 0.673 | wm_close 1.2 s | light_share_high build_procs_warmup build_procs_window never_foreground | 0343-d0-r1 | not timing: desktop WinSta0\exebox-DMTARMUBZWO2RQC7CO33E3NBBO is not WinSta0\Default, build processes: clang++:2596 clang++:71516 clang++:74468 clang++:93592 cmake:82296 ninja:49476 |
| 3 | 1 | B | 1 | OK | False |  | 13.01 | 20 | 2008 | 3.888 | 61.7 | 170 | 1 | 2.127 | 0.583 | wm_close 4.2 s | build_procs_warmup never_foreground | 0344-B-r1 | not timing: desktop WinSta0\exebox-DMTARMUBZWO2RQC7CO33E3NBBO is not WinSta0\Default, build processes: ninja:96856 |
| 4 | 1 | d3 | 1 | OK | False |  | 10.01 | 20 | 1888 | 4.201 | 55.226 | 139 | 2 | 1.896 | 0.526 | wm_close 3.4 s | never_foreground | 0346-d3-r1 | not timing: desktop WinSta0\exebox-DMTARMUBZWO2RQC7CO33E3NBBO is not WinSta0\Default |
| 5 | 1 | d0t | 1 | OK | False |  | 11.01 | 20 | 3327 | 3.562 | 32.909 | 33 | 1 | 1.683 | 0.659 | wm_close 2 s | light_share_high never_foreground | 0347-d0t-r1 | not timing: desktop WinSta0\exebox-DMTARMUBZWO2RQC7CO33E3NBBO is not WinSta0\Default |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | d0 | cold |  | light_share_high build_procs_window never_foreground | 0342-cold-d0 |
| 2 | d0 | 1 |  | light_share_high build_procs_warmup build_procs_window never_foreground | 0343-d0-r1 |
| 3 | B | 1 |  | build_procs_warmup never_foreground | 0344-B-r1 |
| 4 | d3 | 1 |  | never_foreground | 0346-d3-r1 |
| 5 | d0t | 1 |  | light_share_high never_foreground | 0347-d0t-r1 |

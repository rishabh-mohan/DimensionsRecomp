# Timing matrix: Window 4 (Agent 8, session 3): B = devoffB (codegen B) vs d0 = devoff2 (primary), then d3 = devoff3; optional d0t = devoff2 + REX_TIMER_WAIT_BLOCKING=1

- matrix: <workspace>\bench\agent8\run\matrix-window4.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261122-0336
- started 2026-11-22 03:36, ended 03:42; 6 runs (6 OK), 3 scored; desktop WinSta0\exebox-DMTARMUBZWO2RQC7CO33E3NBBO; -Quick
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 3 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

> **FUNCTIONAL ONLY**: -Quick run; 6 of 6 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group w4: ref d0 (ref arm of the group), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d0 | 1/1 | 0 | 0 | 4.06 (4.06..4.06) | 0 | 44.33 | 69.02 | 215.6 | 2.99 | 129.7 | 2.25 |  |  |  | ref |
| B | 1/1 | 0 | 0 | 3.37 (3.37..3.37) | 0 | 34.63 | 48.94 | 144 | 3 | 190.23 | 2.45 | -16.8 | -21.9 | -33.2 | no noise band |
| d3 | 1/1 | 0 | 0 | 6.81 (6.81..6.81) | 0 | 95.56 | 253.54 | 617.3 | 26.97 | 61.38 | 2.03 | 68 | 115.6 | 186.3 | no noise band |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | d0 | 0 | OK | False |  | 9.02 | 20 | 2956 | 2.894 | 14.113 | 0 | 0 | 2.47 | 0.838 | wm_close 1 s | light_share_high never_foreground | 0336-cold-d0 | not timing: desktop WinSta0\exebox-DMTARMUBZWO2RQC7CO33E3NBBO is not WinSta0\Default |
| 2 | cold | B | 0 | OK | False |  | 11.02 | 20 | 2123 | 3.288 | 21.644 | 4 | 0 | 2.206 | 0.704 | wm_close 0.9 s | light_share_high never_foreground | 0337-cold-B | not timing: desktop WinSta0\exebox-DMTARMUBZWO2RQC7CO33E3NBBO is not WinSta0\Default |
| 3 | cold | d3 | 0 | OK | False |  | 11.01 | 20 | 1255 | 5.02 | 40.067 | 22 | 0 | 2.282 | 0.422 | wm_close 1.7 s | never_foreground | 0338-cold-d3 | not timing: desktop WinSta0\exebox-DMTARMUBZWO2RQC7CO33E3NBBO is not WinSta0\Default |
| 4 | 1 | d0 | 1 | OK | False |  | 11.01 | 20 | 2599 | 4.057 | 44.331 | 72 | 1 | 2.248 | 0.542 | wm_close 1.6 s | never_foreground | 0339-d0-r1 | not timing: desktop WinSta0\exebox-DMTARMUBZWO2RQC7CO33E3NBBO is not WinSta0\Default |
| 5 | 1 | B | 1 | OK | False |  | 11.02 | 20 | 3805 | 3.374 | 34.63 | 48 | 1 | 2.446 | 0.714 | wm_close 1 s | light_share_high never_foreground | 0340-B-r1 | not timing: desktop WinSta0\exebox-DMTARMUBZWO2RQC7CO33E3NBBO is not WinSta0\Default |
| 6 | 1 | d3 | 1 | OK | False |  | 10 | 20 | 1229 | 6.814 | 95.562 | 206 | 9 | 2.031 | 0.353 | wm_close 2.5 s | never_foreground | 0341-d3-r1 | not timing: desktop WinSta0\exebox-DMTARMUBZWO2RQC7CO33E3NBBO is not WinSta0\Default |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | d0 | cold |  | light_share_high never_foreground | 0336-cold-d0 |
| 2 | B | cold |  | light_share_high never_foreground | 0337-cold-B |
| 3 | d3 | cold |  | never_foreground | 0338-cold-d3 |
| 4 | d0 | 1 |  | never_foreground | 0339-d0-r1 |
| 5 | B | 1 |  | light_share_high never_foreground | 0340-B-r1 |
| 6 | d3 | 1 |  | never_foreground | 0341-d3-r1 |

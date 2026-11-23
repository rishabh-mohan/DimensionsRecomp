# Timing matrix: Codegen B checks (Agents 9 + 10) + n-prof (Agent 7): functional gate for B = devoffB-bin (MENU step: Agent 10's route), then one profile run each of A = devoff2-bin, B and N = native2-bin (profile only, not for timing)

- matrix: <workspace>\bench\agent8\run\matrix-codegen-check.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261122-0357
- started 2026-11-22 03:57, ended 04:09; 3 runs (0 OK), 3 scored; desktop WinSta0\exebox-XPN3CMN3BEX3PGBKSJT6XJ757P
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 3 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

> **FUNCTIONAL ONLY**: 3 of 3 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group profile: ref a-prof (ref arm of the group), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| a-prof | 0/1 | 0 | 0 |  (..) |  |  |  |  |  |  |  |  |  |  | ref |
| b-prof | 0/1 | 0 | 0 |  (..) |  |  |  |  |  |  |  |  |  |  | no OK runs |
| n-prof | 0/1 | 0 | 0 |  (..) |  |  |  |  |  |  |  |  |  |  | no OK runs |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | a-prof | 1 | PROFILE | False |  | 8.01 | 70 | 10154 | 6.579 | 78.402 | 1520 | 31 | 2.717 | 0.149 | wm_close 3.3 s | ticks_skipped | 0357-a-prof-r1 | PROFILE ONLY, NOT FOR TIMING / not timing: profiler on, desktop WinSta0\exebox-XPN3CMN3BEX3PGBKSJT6XJ757P is not WinSta0\Default |
| 2 | 1 | b-prof | 1 | PROFILE | False |  | 11 | 70 | 10179 | 6.416 | 78.506 | 1632 | 28 | 2.64 | 0.202 | wm_close 4.4 s |  | 0401-b-prof-r1 | PROFILE ONLY, NOT FOR TIMING / not timing: profiler on, desktop WinSta0\exebox-XPN3CMN3BEX3PGBKSJT6XJ757P is not WinSta0\Default |
| 3 | 1 | n-prof | 1 | PROFILE | False |  | 13 | 70 | 10616 | 10.764 | 51.7311 | 671 | 0 | 2.107 | 0.013 | wm_close 1.1 s |  | 0405-n-prof-r1 | PROFILE ONLY, NOT FOR TIMING / not timing: profiler on, desktop WinSta0\exebox-XPN3CMN3BEX3PGBKSJT6XJ757P is not WinSta0\Default |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | a-prof | 1 |  | ticks_skipped | 0357-a-prof-r1 |

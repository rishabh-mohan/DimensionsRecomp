# Timing matrix: Session 3 functional checks (agent slot, hidden desktop, NOT timing): d0t = devoff2 + REX_TIMER_WAIT_BLOCKING=1, d11t = window 3's d11 + REX_TIMER_WAIT_BLOCKING=1 (Agent 11), d0f = devoff2

- matrix: <workspace>\bench\agent8\run\matrix-s3-functional.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261122-0349
- started 2026-11-22 03:49, ended 03:56; 3 runs (3 OK), 3 scored; desktop WinSta0\exebox-C4D4RL5LGHXYUJHMNAZUZLCAQD
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 3 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

> **FUNCTIONAL ONLY**: 3 of 3 runs are not valid timing (desktop, LogonUI, build processes, profiler or no complete window). Do not use these numbers as timing results.

## Group s3: ref d0f (ref arm of the group), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d0f | 1/1 | 0 | 0 | 9.4 (9.4..9.4) | 0 | 80.93 | 131.98 | 705.3 | 9.6 | 52.16 | 2.24 |  |  |  | ref |
| d0t | 1/1 | 0 | 0 | 7.62 (7.62..7.62) | 0 | 73.72 | 116.78 | 483.5 | 14.4 | 78.01 | 2 | -19 | -8.9 | -31.4 | no noise band |
| d11t | 1/1 | 0 | 0 | 7.17 (7.17..7.17) | 0 | 71.31 | 96.52 | 687.6 | 2.4 | 61.96 | 1.77 | -23.8 | -11.9 | -2.5 | no noise band |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | d0t | 1 | OK | False |  | 9.03 | 60 | 3901 | 7.622 | 73.717 | 403 | 12 | 1.996 | 0.322 | wm_close 3.9 s | never_foreground | 0349-d0t-r1 | not timing: desktop WinSta0\exebox-C4D4RL5LGHXYUJHMNAZUZLCAQD is not WinSta0\Default |
| 2 | 1 | d11t | 1 | OK | False |  | 10.03 | 60 | 3098 | 7.167 | 71.31 | 573 | 2 | 1.772 | 0.181 | wm_close 3 s | never_foreground | 0352-d11t-r1 | not timing: desktop WinSta0\exebox-C4D4RL5LGHXYUJHMNAZUZLCAQD is not WinSta0\Default |
| 3 | 1 | d0f | 1 | OK | False |  | 9 | 60 | 2609 | 9.405 | 80.929 | 588 | 8 | 2.235 | 0.117 | wm_close 1.1 s | ticks_skipped never_foreground | 0354-d0f-r1 | not timing: desktop WinSta0\exebox-C4D4RL5LGHXYUJHMNAZUZLCAQD is not WinSta0\Default |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | d0t | 1 |  | never_foreground | 0349-d0t-r1 |
| 2 | d11t | 1 |  | never_foreground | 0352-d11t-r1 |
| 3 | d0f | 1 |  | ticks_skipped never_foreground | 0354-d0f-r1 |

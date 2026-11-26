# Timing matrix: S5 natcmp (M16): n4bp60 vs ship60 (default) or nat60, back to back, quiet-gated, attract-long pad, 3D-only score (one arm per run-matrix call)

- matrix: <workspace>\build\agent16\natcmp\matrix-natcmp.json (copy in matrix.json); out: <workspace>\build\agent16\natcmp\matrix\20261126-015410\01-prime-ship60
- started 2026-11-26 01:54, ended 01:58; 1 runs (1 OK), 1 scored; desktop WinSta0\Default
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 1 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

## Group base: ref ship60 (ref arm of the group), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ship60 | 1/1 | 1 | 0 | 18.68 (18.68..18.68) | 0 | 48.95 | 97.59 | 348.7 | 2.67 | 47.91 | 1.13 |  |  |  | ref |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | ship60 | 1 | OK | True |  | 5.01 | 90 | 8624 | 18.675 | 48.946 | 1046 | 8 | 1.129 | 0.016349721706865 | wm_close 0.7 s |  | 0154-ship60-r1 |  |

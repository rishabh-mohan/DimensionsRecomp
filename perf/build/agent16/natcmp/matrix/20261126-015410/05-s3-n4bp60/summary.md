# Timing matrix: S5 natcmp (M16): n4bp60 vs ship60 (default) or nat60, back to back, quiet-gated, attract-long pad, 3D-only score (one arm per run-matrix call)

- matrix: <workspace>\build\agent16\natcmp\matrix-natcmp.json (copy in matrix.json); out: <workspace>\build\agent16\natcmp\matrix\20261126-015410\05-s3-n4bp60
- started 2026-11-26 02:14, ended 02:19; 1 runs (1 OK), 1 scored; desktop WinSta0\Default
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 1 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

## Group base: ref n4bp60 (first arm (no ref set)), no noise band (ref has < 2 OK runs)

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| n4bp60 | 1/1 | 1 | 0 | 16.76 (16.76..16.76) | 0 | 64.9 | 117.98 | 273.3 | 6.67 | 48.33 | 1.09 |  |  |  | ref |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | n4bp60 | 1 | OK | True |  | 4.01 | 90 | 8700 | 16.7611 | 64.9007 | 820 | 20 | 1.09 | 0 | wm_close 0.6 s |  | 0214-n4bp60-r1 |  |

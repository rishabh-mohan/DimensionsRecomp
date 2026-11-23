# Timing matrix: Window 5, S3d line (Agent 8's task #10 draft, promoted by Agent 1 at 16:42 after W4b): S4 baseline + timer modes. base = devoff3 (S3d); s0, d11, d11t, d11p = devoff4 (S4a)

- matrix: <workspace>\bench\agent8\run\matrix-window5-s3d.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261122-1756
- started 2026-11-22 17:56, ended 18:29; 16 runs (16 OK), 15 scored; desktop WinSta0\Default
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 15 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

## Group w5: ref base (ref arm of the group), noise band +-20.4 %

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| base | 3/3 | 3 | 0 | 2.55 (2.41..2.93) | 20.4 | 7.49 | 9.66 | 0 | 0 | 355.56 | 3.17 |  |  |  | ref |
| s0 | 3/3 | 3 | 0 | 2.69 (2.52..2.76) | 9.1 | 7.58 | 9.87 | 0 | 0 | 333.37 | 3.22 | 5.5 | 1.1 |  | within noise |
| d11 | 3/3 | 3 | 0 | 2.61 (2.56..2.62) | 2.3 | 7.45 | 9.91 | 0 | 0 | 351.34 | 3.17 | 2.6 | -0.5 |  | within noise |
| d11t | 3/3 | 3 | 0 | 2.65 (2.55..3.03) | 18.2 | 7.84 | 10.45 | 0 | 0 | 338.5 | 2.74 | 4 | 4.6 |  | within noise |
| d11p | 3/3 | 3 | 0 | 2.62 (2.58..2.64) | 2.5 | 7.72 | 10.65 | 0 | 0 | 343.34 | 2.75 | 3.1 | 3.1 |  | within noise |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | base | 0 | OK | True |  | 6.01 | 60 | 11875 | 2.437 | 5.156 | 0 | 0 | 2.719 | 0.966 | wm_close 0.7 s | light_share_high | 1756-cold-base |  |
| 2 | 1 | base | 1 | OK | True |  | 5.01 | 60 | 19230 | 2.411 | 6.434 | 0 | 0 | 2.901 | 0.944 | wm_close 0.7 s | light_share_high | 1757-base-r1 |  |
| 3 | 1 | s0 | 1 | OK | True |  | 5.01 | 60 | 16669 | 2.687 | 7.579 | 0 | 0 | 3.193 | 0.869 | wm_close 0.7 s | light_share_high | 1800-s0-r1 |  |
| 4 | 1 | d11 | 1 | OK | True |  | 5.01 | 60 | 17519 | 2.62 | 7.182 | 0 | 0 | 3.18 | 0.894 | wm_close 0.7 s | light_share_high | 1802-d11-r1 |  |
| 5 | 1 | d11t | 1 | OK | True |  | 5.01 | 60 | 16925 | 2.647 | 7.841 | 0 | 0 | 2.719 | 0.886 | wm_close 0.7 s | light_share_high | 1804-d11t-r1 |  |
| 6 | 1 | d11p | 1 | OK | True |  | 5.02 | 60 | 17168 | 2.624 | 7.724 | 0 | 0 | 2.766 | 0.892 | wm_close 0.7 s | light_share_high | 1806-d11p-r1 |  |
| 7 | 2 | s0 | 2 | OK | True |  | 5.01 | 60 | 15496 | 2.764 | 8.285 | 0 | 0 | 3.38 | 0.822 | wm_close 0.9 s | light_share_high | 1808-s0-r2 |  |
| 8 | 2 | d11 | 2 | OK | True |  | 4.01 | 60 | 17567 | 2.612 | 7.454 | 0 | 0 | 3.187 | 0.903 | wm_close 0.8 s | light_share_high | 1810-d11-r2 |  |
| 9 | 2 | d11t | 2 | OK | True |  | 5 | 60 | 17938 | 2.547 | 7.585 | 0 | 0 | 2.67 | 0.916 | wm_close 0.8 s | light_share_high | 1813-d11t-r2 |  |
| 10 | 2 | d11p | 2 | OK | True |  | 4.01 | 60 | 17847 | 2.58 | 7.496 | 0 | 0 | 2.689 | 0.917 | wm_close 0.8 s | light_share_high | 1815-d11p-r2 |  |
| 11 | 2 | base | 2 | OK | True |  | 4.02 | 60 | 14462 | 2.931 | 8.107 | 0 | 0 | 3.456 | 0.765 | wm_close 0.8 s | light_share_high | 1817-base-r2 |  |
| 12 | 3 | d11 | 3 | OK | True |  | 4.02 | 60 | 17624 | 2.56 | 7.593 | 0 | 0 | 3.156 | 0.902 | wm_close 0.8 s | light_share_high | 1819-d11-r3 |  |
| 13 | 3 | d11t | 3 | OK | True |  | 5.01 | 60 | 13858 | 3.028 | 9.952 | 0 | 0 | 2.835 | 0.763 | wm_close 0.9 s | light_share_high | 1821-d11t-r3 |  |
| 14 | 3 | d11p | 3 | OK | True |  | 5.01 | 60 | 16769 | 2.645 | 8.262 | 0 | 0 | 2.783 | 0.881 | wm_close 0.9 s | light_share_high | 1823-d11p-r3 |  |
| 15 | 3 | base | 3 | OK | True |  | 4.02 | 60 | 17778 | 2.546 | 7.494 | 0 | 0 | 3.15 | 0.9 | wm_close 0.8 s | light_share_high | 1825-base-r3 |  |
| 16 | 3 | s0 | 3 | OK | True |  | 5.02 | 60 | 18000 | 2.52 | 7.37 | 0 | 0 | 3.081 | 0.909 | wm_close 0.8 s | light_share_high | 1827-s0-r3 |  |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | base | cold |  | light_share_high | 1756-cold-base |
| 2 | base | 1 |  | light_share_high | 1757-base-r1 |
| 3 | s0 | 1 |  | light_share_high | 1800-s0-r1 |
| 4 | d11 | 1 |  | light_share_high | 1802-d11-r1 |
| 5 | d11t | 1 |  | light_share_high | 1804-d11t-r1 |
| 6 | d11p | 1 |  | light_share_high | 1806-d11p-r1 |
| 7 | s0 | 2 |  | light_share_high | 1808-s0-r2 |
| 8 | d11 | 2 |  | light_share_high | 1810-d11-r2 |
| 9 | d11t | 2 |  | light_share_high | 1813-d11t-r2 |
| 10 | d11p | 2 |  | light_share_high | 1815-d11p-r2 |
| 11 | base | 2 |  | light_share_high | 1817-base-r2 |
| 12 | d11 | 3 |  | light_share_high | 1819-d11-r3 |
| 13 | d11t | 3 |  | light_share_high | 1821-d11t-r3 |
| 14 | d11p | 3 |  | light_share_high | 1823-d11p-r3 |
| 15 | base | 3 |  | light_share_high | 1825-base-r3 |
| 16 | s0 | 3 |  | light_share_high | 1827-s0-r3 |

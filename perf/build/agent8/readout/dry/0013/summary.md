# Timing matrix: Window 3: devoff2 (ref) vs baseline, devoff2 + Agent 11 ON bundle, native2 N0 (and devoff2 + Agent 12 ON bundle if it fits). Uncapped, title loop, no input

- matrix: <workspace>\bench\agent8\run\matrix-window3.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261122-0013
- started 2026-11-22 00:13, ended 01:16; 19 runs (19 OK), 16 scored; desktop WinSta0\Default
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians

## Group w3: ref d0 (ref arm of the group), noise band +-1.7 %

| arm | OK/runs | valid | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d0 | 4/4 | 4 | 7.07 (6.98..7.1) | 1.7 | 12.23 | 14.16 | 0.3 | 0 | 162.86 | 3.52 |  |  |  | ref |
| base | 4/4 | 4 | 7.12 (7.1..7.16) | 0.8 | 12.35 | 14.49 | 0 | 0 | 160.8 | 3.5 | 0.8 | 0.9 | -100 | within noise |
| d11 | 4/4 | 4 | 7.14 (3.4..7.19) | 53.1 | 12.25 | 14.29 | 0 | 0 | 159.04 | 3.59 | 1 | 0.2 | -100 | within noise |
| n0 | 4/4 | 4 | 6.71 (6.55..6.87) | 4.8 | 11.34 | 14.13 | 0 | 0 | 143.22 | 2.45 | -5.1 | -7.3 | -100 | FASTER (outside noise) |

## Runs

| # | round | arm | rep | status | valid | boot s | frames | median ms | p99 ms | >33 | >100 | cpu | close | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | d0 | 0 | OK | True | 7.03 | 9904 | 3.184 | 5.925 | 1 | 1 | 3.02 | wm_close 0.8 s | 0013-cold-d0 |  |
| 2 | cold | base | 0 | OK | True | 6.02 | 6328 | 3.87 | 11.199 | 1 | 1 | 3.58 | wm_close 1.8 s | 0014-cold-base |  |
| 3 | cold | n0 | 0 | OK | True | 16.15 | 4368 | 6.5994 | 11.5162 | 0 | 0 | 2.44 | wm_close 3.4 s | 0016-cold-n0 |  |
| 4 | 1 | d0 | 1 | OK | True | 7.75 | 8182 | 7.047 | 12.283 | 1 | 0 | 3.356 | wm_close 1 s | 0018-d0-r1 |  |
| 5 | 1 | base | 1 | OK | True | 9.02 | 8017 | 7.155 | 12.324 | 0 | 0 | 3.457 | wm_close 1 s | 0022-base-r1 |  |
| 6 | 1 | d11 | 1 | OK | True | 34.06 | 14728 | 3.401 | 7.488 | 0 | 0 | 3.476 | wm_close 1.9 s | 0025-d11-r1 |  |
| 7 | 1 | n0 | 1 | OK | True | 20.7 | 7169 | 6.6907 | 11.374 | 0 | 0 | 2.442 | wm_close 0.9 s | 0030-n0-r1 |  |
| 8 | 2 | base | 2 | OK | True | 8.06 | 8044 | 7.126 | 12.22 | 0 | 0 | 3.414 | wm_close 1 s | 0033-base-r2 |  |
| 9 | 2 | d11 | 2 | OK | True | 42.42 | 8014 | 7.114 | 12.575 | 0 | 0 | 3.516 | wm_close 5 s | 0038-d11-r2 |  |
| 10 | 2 | n0 | 2 | OK | True | 9.41 | 6835 | 6.8749 | 12.5905 | 0 | 0 | 2.55 | wm_close 2.4 s | 0042-n0-r2 |  |
| 11 | 2 | d0 | 2 | OK | True | 9.06 | 8365 | 6.977 | 11.931 | 0 | 0 | 3.616 | wm_close 1 s | 0046-d0-r2 |  |
| 12 | 3 | d11 | 3 | OK | True | 9.05 | 7890 | 7.187 | 12.215 | 0 | 0 | 3.787 | wm_close 0.9 s | 0048-d11-r3 |  |
| 13 | 3 | n0 | 3 | OK | True | 17.5 | 7329 | 6.5546 | 10.9675 | 0 | 0 | 2.381 | wm_close 1.5 s | 0054-n0-r3 |  |
| 14 | 3 | d0 | 3 | OK | True | 25.04 | 8076 | 7.1 | 12.388 | 0 | 0 | 3.494 | wm_close 1.5 s | 0056-d0-r3 |  |
| 15 | 3 | base | 3 | OK | True | 30.5 | 8043 | 7.101 | 12.478 | 0 | 0 | 3.564 | wm_close 4.2 s | 0101-base-r3 |  |
| 16 | 4 | n0 | 4 | OK | True | 25.96 | 7153 | 6.7235 | 11.3027 | 0 | 0 | 2.416 | wm_close 0.8 s | 0104-n0-r4 |  |
| 17 | 4 | d0 | 4 | OK | True | 8.03 | 8105 | 7.087 | 12.18 | 0 | 0 | 3.613 | wm_close 0.9 s | 0106-d0-r4 |  |
| 18 | 4 | base | 4 | OK | True | 7.75 | 8038 | 7.121 | 12.369 | 0 | 0 | 3.573 | wm_close 3.2 s | 0109-base-r4 |  |
| 19 | 4 | d11 | 4 | OK | True | 7.67 | 7876 | 7.156 | 12.292 | 0 | 0 | 3.598 | wm_close 1.9 s | 0113-d11-r4 |  |

# Timing matrix: Quiet window 1: baseline-bin vs devoff1-bin, both at defaults. Title/attract loop, no input needed

- matrix: <workspace>\bench\agent8\run\matrix-base-vs-devoff1.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261121-2232
- started 2026-11-21 22:32, ended 23:02; 12 runs (11 OK), 10 scored; desktop WinSta0\Default
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians

## Group ab: ref base (ref arm of the group), noise band +-0.1 %

| arm | OK/runs | valid | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| base | 5/5 | 5 | 16.66 (16.66..16.67) | 0.1 | 18.59 | 20.75 | 0 | 0 | 60 | 2.12 |  |  |  | ref |
| r0 | 4/5 | 4 | 16.67 (16.66..16.67) | 0 | 19.51 | 23.38 | 0.2 | 0 | 60 | 2.2 | 0 | 4.9 |  | within noise |

## Runs

| # | round | arm | rep | status | valid | boot s | frames | median ms | p99 ms | >33 | >100 | cpu | close | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | base | 0 | OK | True | 10.01 | 1789 | 16.661 | 18.79 | 1 | 1 | 2.15 | wm_close 0.9 s | 2232-cold-base |  |
| 2 | cold | r0 | 0 | OK | True | 9 | 1801 | 16.656 | 19.667 | 0 | 0 | 2.132 | wm_close 0.6 s | 2233-cold-r0 |  |
| 3 | 1 | base | 1 | OK | True | 6.02 | 3601 | 16.656 | 19.379 | 0 | 0 | 2.221 | wm_close 0.8 s | 2235-base-r1 |  |
| 4 | 1 | r0 | 1 | OK | True | 8.01 | 3601 | 16.669 | 19.528 | 0 | 0 | 2.292 | wm_close 0.9 s | 2237-r0-r1 |  |
| 5 | 2 | r0 | 2 | OK | True | 8.01 | 3601 | 16.67 | 23.95 | 0 | 0 | 2.421 | wm_close 2.6 s | 2240-r0-r2 |  |
| 6 | 2 | base | 2 | OK | True | 8.01 | 3601 | 16.656 | 18.594 | 0 | 0 | 2.134 | wm_close 1.3 s | 2243-base-r2 |  |
| 7 | 3 | base | 3 | OK | True | 8.01 | 3601 | 16.666 | 22.5 | 0 | 0 | 2.291 | wm_close 0.9 s | 2246-base-r3 |  |
| 8 | 3 | r0 | 3 | PROBLEM | True | 10.01 | 3601 | 16.657 | 21.154 | 0 | 0 | 2.412 | wm_close 1.2 s | 2248-r0-r3 | crash artifacts: C:\Users\<user>\AppData\Local\CrashDumps\fakedimensions.exe.48456.dmp, <workspace>\build\agent8\matrix\20261121-2232\runs\2248-r0-r3\fakedimensions.exe.48456.dmp |
| 9 | 4 | r0 | 4 | OK | True | 7.01 | 3601 | 16.663 | 19.437 | 0 | 0 | 2.087 | wm_close 0.9 s | 2251-r0-r4 |  |
| 10 | 4 | base | 4 | OK | True | 7.02 | 3601 | 16.666 | 18.198 | 0 | 0 | 2.047 | wm_close 0.8 s | 2254-base-r4 |  |
| 11 | 5 | base | 5 | OK | True | 7.01 | 3601 | 16.661 | 18.074 | 0 | 0 | 1.911 | wm_close 0.8 s | 2257-base-r5 |  |
| 12 | 5 | r0 | 5 | OK | True | 6.01 | 3601 | 16.665 | 19.493 | 1 | 0 | 1.999 | wm_close 0.8 s | 2259-r0-r5 |  |

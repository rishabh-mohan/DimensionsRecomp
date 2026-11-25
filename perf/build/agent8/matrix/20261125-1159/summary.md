# Timing matrix: Window CF2 (M8, session 3): confirmation of the shipped native default. nf = build/agent2/nativefinal-bin (N-A: FINAL native exe on the old SDK DLLs, miss cache ON by build default), plain launch, DEFAULT ARM, vs mc = native4b-bin + LEGO_NATIVE_SHADER_MISS_CACHE=1 (W8a's mc as timed). Optional: n0 (W8a's reference, miss cache OFF). W8a route and frames, 6 round-robin rounds, round 1 discarded

- matrix: <workspace>\bench\agent8\run\matrix-windowCF2.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261125-1159
- started 2026-11-25 11:59, ended 12:26; 13 runs (13 OK), 12 scored; desktop WinSta0\Default
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 12 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

## Group cf2: ref mc (ref arm of the group), noise band +-0.8 %

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mc | 6/6 | 6 | 0 | 2.15 (2.15..2.16) | 0.8 | 3.1 | 3.77 | 0 | 0 | 459.71 | 1.83 |  |  |  | ref |
| nf | 6/6 | 6 | 0 | 2.15 (2.13..2.15) | 1 | 3.08 | 3.78 | 0 | 0 | 460.18 | 1.78 | -0.1 | -0.5 |  | within noise |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | nf | 0 | OK | True |  | 5.01 | 60 | 12488 | 2.3801 | 2.8475 | 0 | 0 | 1.106 | 0.999679692504805 | wm_close 0.5 s | light_share_high | 1159-cold-nf |  |
| 2 | 1 | nf | 1 | OK | True |  | 4.01 | 60 | 23285 | 2.1304 | 2.7509 | 0 | 0 | 1.618 | 0.999914107794718 | wm_close 0.6 s | light_share_high | 1201-nf-r1 |  |
| 3 | 1 | mc | 1 | OK | True |  | 4.01 | 60 | 22915 | 2.1517 | 3.1241 | 0 | 0 | 1.803 | 0.999825441850316 | wm_close 0.5 s | light_share_high | 1203-mc-r1 |  |
| 4 | 2 | mc | 2 | OK | True |  | 5.01 | 60 | 21977 | 2.1644 | 4.4341 | 0 | 0 | 1.861 | 0.991081585293716 | wm_close 0.5 s | light_share_high | 1205-mc-r2 |  |
| 5 | 2 | nf | 2 | OK | True |  | 4.01 | 60 | 23077 | 2.1477 | 2.9653 | 0 | 0 | 1.833 | 0.999913333622221 | wm_close 0.5 s | light_share_high | 1207-nf-r2 |  |
| 6 | 3 | nf | 3 | OK | True |  | 4.01 | 60 | 22942 | 2.1449 | 3.202 | 0 | 0 | 1.774 | 0.998561590096766 | wm_close 0.5 s | light_share_high | 1209-nf-r3 |  |
| 7 | 3 | mc | 3 | OK | True |  | 4.02 | 60 | 23104 | 2.1478 | 2.835 | 0 | 0 | 1.769 | 0.999956717451524 | wm_close 0.5 s | light_share_high | 1211-mc-r3 |  |
| 8 | 4 | mc | 4 | OK | True |  | 4.01 | 60 | 22977 | 2.1513 | 3.0975 | 0 | 0 | 1.89 | 0.999825912869391 | wm_close 0.5 s | light_share_high | 1213-mc-r4 |  |
| 9 | 4 | nf | 4 | OK | True |  | 4.02 | 60 | 23104 | 2.1483 | 2.8643 | 0 | 0 | 1.829 | 0.999913434903047 | wm_close 0.5 s | light_share_high | 1215-nf-r4 |  |
| 10 | 5 | nf | 5 | OK | True |  | 4.01 | 60 | 22889 | 2.1514 | 3.2108 | 0 | 0 | 1.778 | 0.998165057451178 | wm_close 0.6 s | light_share_high | 1217-nf-r5 |  |
| 11 | 5 | mc | 5 | OK | True |  | 4.01 | 60 | 23072 | 2.1483 | 2.9038 | 0 | 0 | 1.835 | 0.999913314840499 | wm_close 0.5 s | light_share_high | 1219-mc-r5 |  |
| 12 | 6 | mc | 6 | OK | True |  | 4.01 | 60 | 22994 | 2.1477 | 3.1023 | 0 | 0 | 1.811 | 0.999826041576063 | wm_close 0.5 s | light_share_high | 1222-mc-r6 |  |
| 13 | 6 | nf | 6 | OK | True |  | 4.01 | 60 | 22909 | 2.1503 | 3.212 | 0 | 0 | 1.835 | 0.999650792265049 | wm_close 0.5 s | light_share_high | 1224-nf-r6 |  |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | nf | cold |  | light_share_high | 1159-cold-nf |
| 2 | nf | 1 |  | light_share_high | 1201-nf-r1 |
| 3 | mc | 1 |  | light_share_high | 1203-mc-r1 |
| 4 | mc | 2 |  | light_share_high | 1205-mc-r2 |
| 5 | nf | 2 |  | light_share_high | 1207-nf-r2 |
| 6 | nf | 3 |  | light_share_high | 1209-nf-r3 |
| 7 | mc | 3 |  | light_share_high | 1211-mc-r3 |
| 8 | mc | 4 |  | light_share_high | 1213-mc-r4 |
| 9 | nf | 4 |  | light_share_high | 1215-nf-r4 |
| 10 | nf | 5 |  | light_share_high | 1217-nf-r5 |
| 11 | mc | 5 |  | light_share_high | 1219-mc-r5 |
| 12 | mc | 6 |  | light_share_high | 1222-mc-r6 |
| 13 | nf | 6 |  | light_share_high | 1224-nf-r6 |

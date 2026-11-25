# Timing matrix: Window CF1 (M8, session 3): confirmation of the shipped Xenos defaults. ship = build/agent2/devfinal-bin, plain launch (the FINAL defaults = WC win3), DEFAULT ARM, vs s0 = devoff4b-bin with every switch OFF (WC's s0). Optional: win3 (WC's arm on devoff4b, the anchor) and dfoff (devfinal with the D7 OFF set). 6 round-robin rounds, round 1 discarded

- matrix: <workspace>\bench\agent8\run\matrix-windowCF1.json (copy in matrix.json); out: <workspace>\build\agent8\matrix\20261125-1255
- started 2026-11-25 12:55, ended 13:34; 19 runs (19 OK), 18 scored; desktop WinSta0\Default
- numbers: per arm the median of the run medians (min..max); deltas against the ref arm of the group; noise band = the ref arm's run-to-run spread (max-min)/median of its run medians
- flagged: 0 of 18 scored runs carry an excluding flag (light_phase, window_before_floor, or a sys flag on the interactive desktop) and are left out of the numbers below; see Flagged runs

## Group cf1: ref s0 (ref arm of the group), noise band +-6.2 %

| arm | OK/runs | valid | flagged | median ms (min..max) | spread % | p99 ms | p99.9 ms | >33/min | >100/min | fps | cpu cores | d median % | d p99 % | d >33/min % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s0 | 6/6 | 6 | 0 | 2.02 (1.97..2.1) | 6.2 | 4.9 | 5.69 | 0 | 0 | 450.58 | 2.48 |  |  |  | ref |
| ship | 6/6 | 6 | 0 | 2.11 (2.1..2.21) | 5 | 4.14 | 4.66 | 0 | 0 | 494.24 | 1.54 | 4.4 | -15.5 |  | within noise |
| win3 | 6/6 | 6 | 0 | 2.15 (2.1..2.2) | 4.6 | 4.13 | 4.68 | 0 | 0 | 492.95 | 1.55 | 6 | -15.7 |  | within noise |

## Runs

| # | round | arm | rep | status | valid | excl | boot s | ff->win s | frames | median ms | p99 ms | >33 | >100 | cpu | light | close | flags | run dir | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | ship | 0 | OK | True |  | 4 | 60 | 14563 | 2.102 | 4.107 | 0 | 0 | 1.356 | 0.998008652063448 | wm_close 0.4 s | light_share_high | 1255-cold-ship |  |
| 2 | 1 | ship | 1 | OK | True |  | 4 | 60 | 24829 | 2.207 | 3.917 | 0 | 0 | 1.449 | 0.999113939345121 | wm_close 0.5 s | light_share_high | 1257-ship-r1 |  |
| 3 | 1 | s0 | 1 | OK | True |  | 4.01 | 60 | 22696 | 2.016 | 4.817 | 0 | 0 | 2.5 | 0.977793443778639 | wm_close 0.6 s | light_share_high | 1259-s0-r1 |  |
| 4 | 1 | win3 | 1 | OK | True |  | 4.01 | 60 | 24631 | 2.103 | 4.164 | 0 | 0 | 1.503 | 0.997401648329341 | wm_close 0.5 s | light_share_high | 1301-win3-r1 |  |
| 5 | 2 | s0 | 2 | OK | True |  | 4.01 | 60 | 22750 | 1.97 | 4.88 | 0 | 0 | 2.454 | 0.974021978021978 | wm_close 3.2 s | light_share_high | 1303-s0-r2 |  |
| 6 | 2 | win3 | 2 | OK | True |  | 4 | 60 | 24804 | 2.168 | 4.014 | 0 | 0 | 1.492 | 0.998105144331559 | wm_close 0.5 s | light_share_high | 1305-win3-r2 |  |
| 7 | 2 | ship | 2 | OK | True |  | 4.03 | 60 | 24684 | 2.102 | 4.16 | 0 | 0 | 1.452 | 0.997690811861935 | wm_close 0.6 s | light_share_high | 1307-ship-r2 |  |
| 8 | 3 | win3 | 3 | OK | True |  | 4 | 60 | 24093 | 2.181 | 4.13 | 0 | 0 | 1.744 | 0.9968870626323 | wm_close 0.7 s | light_share_high | 1309-win3-r3 |  |
| 9 | 3 | ship | 3 | OK | True |  | 5.01 | 60 | 24114 | 2.195 | 4.038 | 0 | 0 | 1.798 | 0.99813386414531 | wm_close 0.6 s | light_share_high nongame_load | 1311-ship-r3 |  |
| 10 | 3 | s0 | 3 | OK | True |  | 5 | 60 | 22406 | 2.044 | 4.975 | 0 | 0 | 2.465 | 0.974114076586629 | wm_close 0.5 s | light_share_high | 1313-s0-r3 |  |
| 11 | 4 | ship | 4 | OK | True |  | 4.02 | 60 | 24741 | 2.102 | 4.179 | 0 | 0 | 1.508 | 0.996685663473586 | wm_close 0.5 s | light_share_high | 1315-ship-r4 |  |
| 12 | 4 | s0 | 4 | OK | True |  | 3.02 | 60 | 22654 | 2 | 4.994 | 0 | 0 | 2.452 | 0.971439922309526 | wm_close 0.5 s | light_share_high | 1317-s0-r4 |  |
| 13 | 4 | win3 | 4 | OK | True |  | 4.01 | 60 | 24701 | 2.101 | 4.183 | 0 | 0 | 1.439 | 0.996599327962431 | wm_close 0.5 s | light_share_high | 1319-win3-r4 |  |
| 14 | 5 | s0 | 5 | OK | True |  | 4.01 | 60 | 22280 | 2.034 | 4.921 | 0 | 0 | 2.49 | 0.972127468581688 | wm_close 0.5 s | light_share_high | 1321-s0-r5 |  |
| 15 | 5 | win3 | 5 | OK | True |  | 4.02 | 60 | 24654 | 2.124 | 4.133 | 0 | 0 | 1.579 | 0.99801249290176 | wm_close 0.5 s | light_share_high | 1323-win3-r5 |  |
| 16 | 5 | ship | 5 | OK | True |  | 4.01 | 60 | 24282 | 2.11 | 4.197 | 0 | 0 | 1.542 | 0.996211185240096 | wm_close 0.4 s | light_share_high | 1325-ship-r5 |  |
| 17 | 6 | win3 | 6 | OK | True |  | 4.85 | 60.2 | 24642 | 2.2 | 4.02 | 0 | 0 | 1.517 | 0.998539079620161 | wm_close 0.6 s | light_share_high | 1328-win3-r6 |  |
| 18 | 6 | ship | 6 | OK | True |  | 4.01 | 60 | 24786 | 2.118 | 4.12 | 0 | 0 | 1.496 | 0.997942386831276 | wm_close 0.5 s | light_share_high | 1330-ship-r6 |  |
| 19 | 6 | s0 | 6 | OK | True |  | 4.01 | 60 | 22105 | 2.095 | 4.858 | 0 | 0 | 2.509 | 0.975842569554399 | wm_close 0.5 s | light_share_high | 1332-s0-r6 |  |

## Flagged runs

Excluding flags take the run out of the numbers above (it stays in results.csv; matrix_recheck.py --keep-flagged puts it back). Info flags are notes only.

| # | arm | rep | excluding flags | info flags | run dir |
|---|---|---|---|---|---|
| 1 | ship | cold |  | light_share_high | 1255-cold-ship |
| 2 | ship | 1 |  | light_share_high | 1257-ship-r1 |
| 3 | s0 | 1 |  | light_share_high | 1259-s0-r1 |
| 4 | win3 | 1 |  | light_share_high | 1301-win3-r1 |
| 5 | s0 | 2 |  | light_share_high | 1303-s0-r2 |
| 6 | win3 | 2 |  | light_share_high | 1305-win3-r2 |
| 7 | ship | 2 |  | light_share_high | 1307-ship-r2 |
| 8 | win3 | 3 |  | light_share_high | 1309-win3-r3 |
| 9 | ship | 3 |  | light_share_high nongame_load | 1311-ship-r3 |
| 10 | s0 | 3 |  | light_share_high | 1313-s0-r3 |
| 11 | ship | 4 |  | light_share_high | 1315-ship-r4 |
| 12 | s0 | 4 |  | light_share_high | 1317-s0-r4 |
| 13 | win3 | 4 |  | light_share_high | 1319-win3-r4 |
| 14 | s0 | 5 |  | light_share_high | 1321-s0-r5 |
| 15 | win3 | 5 |  | light_share_high | 1323-win3-r5 |
| 16 | ship | 5 |  | light_share_high | 1325-ship-r5 |
| 17 | win3 | 6 |  | light_share_high | 1328-win3-r6 |
| 18 | ship | 6 |  | light_share_high | 1330-ship-r6 |
| 19 | s0 | 6 |  | light_share_high | 1332-s0-r6 |

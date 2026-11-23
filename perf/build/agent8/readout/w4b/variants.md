# Read-out variants: W4b 20261122-1541 (ref d0)

- script: build/agent8/scratch/readout_variants.py (read-only); inputs: build/agent8/readout/w4b/xcheck/xcheck_runs.csv, build/agent8/readout/w4b/scan/bins.csv
- decision rule = R5 (agent8-window3.md L821): better/worse only when every run of the arm lies outside the reference min..max; no verdict when n < 3; paired by round is support only.
- R3/R4/R6 drops are ignored in every variant here (the strict result is rules.md); timing claims only from rows whose decision is better/worse.

### all: every scored run (16)

| arm | n | runs (seq) | fps | p50 ms | p99 ms | 1% low fps | game cores | vs d0: fps / p50 / p99 / 1% low / cores | decision on fps / p50 | paired fps by round |
|---|---|---|---|---|---|---|---|---|---|---|
| d0 | 4 | 2, 9, 12, 15 | 239.7 (213.9..270.4) | 3.399 (3.069..3.734) | 10.73 (9.92..10.96) | 83.4 (82.5..85.9) | 3.44 (3.34..3.53) | ref | ref | - |
| B | 4 | 3, 6, 13, 16 | 255.1 (230.8..317.1) | 3.234 (2.884..3.530) | 10.50 (9.40..11.52) | 86.6 (75.5..93.4) | 3.39 (3.14..3.48) | +6.4% overlap / -4.9% overlap / -2.2% overlap / +3.8% overlap / -1.5% overlap | overlap / overlap | +13.6% (3 / 4 up); r1 +23.7% r2 -13.3% r3 +3.5% r4 +28.9% |
| d11t | 4 | 5, 8, 11, 14 | 237.7 (206.4..277.2) | 3.363 (3.025..3.857) | 10.94 (9.87..12.17) | 82.1 (72.7..87.3) | 2.92 (2.81..3.00) | -0.8% overlap / -1.1% overlap / +1.9% overlap / -1.6% overlap / -15.3% better | overlap / overlap | +0.4% (2 / 4 up); r1 -19.5% r2 -18.4% r3 +24.3% r4 +19.2% |
| d3 | 4 | 4, 7, 10, 17 | 248.9 (198.4..298.6) | 3.215 (2.894..4.264) | 10.49 (9.71..12.90) | 85.2 (70.6..90.5) | 3.41 (3.18..3.52) | +3.8% overlap / -5.4% overlap / -2.3% overlap / +2.1% overlap / -0.9% overlap | overlap / overlap | +0.3% (2 / 4 up); r1 -9.9% r2 +10.4% r3 -11.0% r4 +24.7% |

### no6: valid-timing runs only (15; without 1551-B-r2)

| arm | n | runs (seq) | fps | p50 ms | p99 ms | 1% low fps | game cores | vs d0: fps / p50 / p99 / 1% low / cores | decision on fps / p50 | paired fps by round |
|---|---|---|---|---|---|---|---|---|---|---|
| d0 | 4 | 2, 9, 12, 15 | 239.7 (213.9..270.4) | 3.399 (3.069..3.734) | 10.73 (9.92..10.96) | 83.4 (82.5..85.9) | 3.44 (3.34..3.53) | ref | ref | - |
| B | 3 | 3, 13, 16 | 275.8 (230.8..317.1) | 3.033 (2.884..3.435) | 10.01 (9.40..10.99) | 89.7 (83.5..93.4) | 3.35 (3.14..3.48) | +15.1% overlap / -10.8% overlap / -6.7% overlap / +7.5% overlap / -2.7% overlap | overlap / overlap | +23.7% (3 / 3 up); r1 +23.7% r3 +3.5% r4 +28.9% |
| d11t | 4 | 5, 8, 11, 14 | 237.7 (206.4..277.2) | 3.363 (3.025..3.857) | 10.94 (9.87..12.17) | 82.1 (72.7..87.3) | 2.92 (2.81..3.00) | -0.8% overlap / -1.1% overlap / +1.9% overlap / -1.6% overlap / -15.3% better | overlap / overlap | +0.4% (2 / 4 up); r1 -19.5% r2 -18.4% r3 +24.3% r4 +19.2% |
| d3 | 4 | 4, 7, 10, 17 | 248.9 (198.4..298.6) | 3.215 (2.894..4.264) | 10.49 (9.71..12.90) | 85.2 (70.6..90.5) | 3.41 (3.18..3.52) | +3.8% overlap / -5.4% overlap / -2.3% overlap / +2.1% overlap / -0.9% overlap | overlap / overlap | +0.3% (2 / 4 up); r1 -9.9% r2 +10.4% r3 -11.0% r4 +24.7% |

### noflag: without the flagged runs seq 3,4,5,6,7,10 (10 left)

| arm | n | runs (seq) | fps | p50 ms | p99 ms | 1% low fps | game cores | vs d0: fps / p50 / p99 / 1% low / cores | decision on fps / p50 | paired fps by round |
|---|---|---|---|---|---|---|---|---|---|---|
| d0 | 4 | 2, 9, 12, 15 | 239.7 (213.9..270.4) | 3.399 (3.069..3.734) | 10.73 (9.92..10.96) | 83.4 (82.5..85.9) | 3.44 (3.34..3.53) | ref | ref | - |
| B | 2 | 13, 16 | 253.3 (230.8..275.8) | 3.234 (3.033..3.435) | 10.50 (10.01..10.99) | 86.6 (83.5..89.7) | 3.42 (3.35..3.48) | +5.7% no verdict (n 2 vs 4) / -4.9% no verdict (n 2 vs 4) / -2.2% no verdict (n 2 vs 4) / +3.8% no verdict (n 2 vs 4) / -0.8% no verdict (n 2 vs 4) | no verdict (n 2 vs 4) / no verdict (n 2 vs 4) | +16.2% (2 / 2 up); r3 +3.5% r4 +28.9% |
| d11t | 3 | 8, 11, 14 | 254.9 (220.6..277.2) | 3.158 (3.025..3.568) | 10.38 (9.87..12.17) | 83.6 (72.7..87.3) | 2.90 (2.81..2.94) | +6.3% overlap / -7.1% overlap / -3.3% overlap / +0.2% overlap / -15.9% better | overlap / overlap | +19.2% (2 / 3 up); r2 -18.4% r3 +24.3% r4 +19.2% |
| d3 | 1 | 17 | 266.8 (266.8..266.8) | 3.082 (3.082..3.082) | 9.87 (9.87..9.87) | 90.5 (90.5..90.5) | 3.37 (3.37..3.37) | +11.3% no verdict (n 1 vs 4) / -9.3% no verdict (n 1 vs 4) / -8.0% no verdict (n 1 vs 4) / +8.5% no verdict (n 1 vs 4) / -2.0% no verdict (n 1 vs 4) | no verdict (n 1 vs 4) / no verdict (n 1 vs 4) | +24.7% (1 / 1 up); r4 +24.7% |

Flagged runs: 1545-B-r1 (seq 3, 317.1 fps), 1547-d3-r1 (seq 4, 231.0 fps), 1549-d11t-r1 (seq 5, 206.4 fps), 1551-B-r2 (seq 6, 234.5 fps), 1553-d3-r2 (seq 7, 298.6 fps), 1600-d3-r3 (seq 10, 198.4 fps)

### slowbins: median fps of each run's slow-state bins (>= 90 % of sys.csv rows E<800 MHz), descriptive only

| seq | run | arm | round | slow bins | slow-bin fps (median) | fast bins (E<800 <= 10 %) | fast-bin fps (median) | window fps |
|---|---|---|---|---|---|---|---|---|
| 2 | 1542-d0-r1 | d0 | 1 | 1 | 170.8 | 3 | 302.6 | 256.4 |
| 3 | 1545-B-r1 | B | 1 | 1 | 219.7 | 3 | 379.4 | 317.1 |
| 4 | 1547-d3-r1 | d3 | 1 | 3 | 181.5 | 1 | 333.3 | 231.0 |
| 5 | 1549-d11t-r1 | d11t | 1 | 4 | 193.4 | 0 | - | 206.4 |
| 6 | 1551-B-r2 | B | 2 | 3 | 206.7 | 1 | 259.6 | 234.5 |
| 7 | 1553-d3-r2 | d3 | 2 | 2 | 227.9 | 2 | 379.9 | 298.6 |
| 8 | 1556-d11t-r2 | d11t | 2 | 4 | 228.2 | 0 | - | 220.6 |
| 9 | 1558-d0-r2 | d0 | 2 | 4 | 252.2 | 1 | 373.2 | 270.4 |
| 10 | 1600-d3-r3 | d3 | 3 | 5 | 212.2 | 0 | - | 198.4 |
| 11 | 1602-d11t-r3 | d11t | 3 | 5 | 277.6 | 0 | - | 277.2 |
| 12 | 1604-d0-r3 | d0 | 3 | 5 | 220.2 | 0 | - | 223.1 |
| 13 | 1606-B-r3 | B | 3 | 5 | 224.3 | 0 | - | 230.8 |
| 14 | 1608-d11t-r4 | d11t | 4 | 5 | 259.1 | 0 | - | 254.9 |
| 15 | 1611-d0-r4 | d0 | 4 | 5 | 216.7 | 0 | - | 213.9 |
| 16 | 1613-B-r4 | B | 4 | 4 | 264.5 | 0 | - | 275.8 |
| 17 | 1615-d3-r4 | d3 | 4 | 5 | 254.9 | 0 | - | 266.8 |

| arm | n | slow-bin fps median (min..max) | vs d0 | paired by round |
|---|---|---|---|---|
| d0 (all) | 4 | 218.5 (170.8..252.2) | ref | - |
| B (all) | 4 | 222.0 (206.7..264.5) | +1.6% (overlap, descriptive) | +12.0% (3 / 4 up); r1 +28.7% r2 -18.0% r3 +1.8% r4 +22.1% |
| d11t (all) | 4 | 243.6 (193.4..277.6) | +11.5% (overlap, descriptive) | +16.4% (3 / 4 up); r1 +13.2% r2 -9.5% r3 +26.1% r4 +19.5% |
| d3 (all) | 4 | 220.1 (181.5..254.9) | +0.7% (overlap, descriptive) | +1.3% (2 / 4 up); r1 +6.3% r2 -9.6% r3 -3.7% r4 +17.6% |
| d0 (valid only) | 4 | 218.5 (170.8..252.2) | ref | - |
| B (valid only) | 3 | 224.3 (219.7..264.5) | +2.7% (overlap, descriptive) | +22.1% (3 / 3 up); r1 +28.7% r3 +1.8% r4 +22.1% |
| d11t (valid only) | 4 | 243.6 (193.4..277.6) | +11.5% (overlap, descriptive) | +16.4% (3 / 4 up); r1 +13.2% r2 -9.5% r3 +26.1% r4 +19.5% |
| d3 (valid only) | 4 | 220.1 (181.5..254.9) | +0.7% (overlap, descriptive) | +1.3% (2 / 4 up); r1 +6.3% r2 -9.6% r3 -3.7% r4 +17.6% |


# Read-out variants: W5 20261122-1756 (ref base; flag = R6 BG+ run 1821-d11t-r3)

- script: build/agent8/scratch/readout_variants.py (read-only); inputs: build/agent8/readout/w5/xcheck/xcheck_runs.csv, build/agent8/readout/w5/scan/bins.csv
- decision rule = R5 (agent8-window3.md L821): better/worse only when every run of the arm lies outside the reference min..max; no verdict when n < 3; paired by round is support only.
- R3/R4/R6 drops are ignored in every variant here (the strict result is rules.md); timing claims only from rows whose decision is better/worse.

### all: every scored run (15)

| arm | n | runs (seq) | fps | p50 ms | p99 ms | 1% low fps | game cores | vs base: fps / p50 / p99 / 1% low / cores | decision on fps / p50 | paired fps by round |
|---|---|---|---|---|---|---|---|---|---|---|
| base | 3 | 2, 11, 15 | 355.6 (289.2..384.6) | 2.546 (2.411..2.931) | 7.49 (6.43..8.11) | 118.1 (107.0..135.6) | 3.15 (2.90..3.46) | ref | ref | - |
| d11 | 3 | 4, 8, 12 | 351.3 (350.3..352.5) | 2.612 (2.560..2.620) | 7.45 (7.18..7.59) | 120.1 (115.8..125.9) | 3.18 (3.16..3.19) | -1.2% overlap / +2.6% overlap / -0.5% overlap / +1.7% overlap / +0.9% overlap | overlap / overlap | -0.9% (1 / 3 up); r1 -8.9% r2 +21.5% r3 -0.9% |
| d11p | 3 | 6, 10, 14 | 343.3 (335.3..356.9) | 2.624 (2.580..2.645) | 7.72 (7.50..8.26) | 114.8 (105.4..117.7) | 2.77 (2.69..2.78) | -3.4% overlap / +3.1% overlap / +3.1% overlap / -2.8% overlap / -12.2% better | overlap / overlap | -5.7% (1 / 3 up); r1 -10.7% r2 +23.4% r3 -5.7% |
| d11t | 3 | 5, 9, 13 | 338.5 (277.1..358.7) | 2.647 (2.547..3.028) | 7.84 (7.58..9.95) | 113.1 (90.6..119.7) | 2.72 (2.67..2.84) | -4.8% overlap / +4.0% overlap / +4.6% overlap / -4.3% overlap / -13.7% better | overlap / overlap | -12.0% (1 / 3 up); r1 -12.0% r2 +24.0% r3 -22.1% |
| s0 | 3 | 3, 7, 16 | 333.4 (309.9..360.0) | 2.687 (2.520..2.764) | 7.58 (7.37..8.29) | 118.4 (105.7..119.7) | 3.19 (3.08..3.38) | -6.2% overlap / +5.5% overlap / +1.1% overlap / +0.2% overlap / +1.3% overlap | overlap / overlap | +1.2% (2 / 3 up); r1 -13.3% r2 +7.1% r3 +1.2% |

### noflag: without the flagged runs seq 13 (14 left)

| arm | n | runs (seq) | fps | p50 ms | p99 ms | 1% low fps | game cores | vs base: fps / p50 / p99 / 1% low / cores | decision on fps / p50 | paired fps by round |
|---|---|---|---|---|---|---|---|---|---|---|
| base | 3 | 2, 11, 15 | 355.6 (289.2..384.6) | 2.546 (2.411..2.931) | 7.49 (6.43..8.11) | 118.1 (107.0..135.6) | 3.15 (2.90..3.46) | ref | ref | - |
| d11 | 3 | 4, 8, 12 | 351.3 (350.3..352.5) | 2.612 (2.560..2.620) | 7.45 (7.18..7.59) | 120.1 (115.8..125.9) | 3.18 (3.16..3.19) | -1.2% overlap / +2.6% overlap / -0.5% overlap / +1.7% overlap / +0.9% overlap | overlap / overlap | -0.9% (1 / 3 up); r1 -8.9% r2 +21.5% r3 -0.9% |
| d11p | 3 | 6, 10, 14 | 343.3 (335.3..356.9) | 2.624 (2.580..2.645) | 7.72 (7.50..8.26) | 114.8 (105.4..117.7) | 2.77 (2.69..2.78) | -3.4% overlap / +3.1% overlap / +3.1% overlap / -2.8% overlap / -12.2% better | overlap / overlap | -5.7% (1 / 3 up); r1 -10.7% r2 +23.4% r3 -5.7% |
| d11t | 2 | 5, 9 | 348.6 (338.5..358.7) | 2.597 (2.547..2.647) | 7.71 (7.58..7.84) | 116.4 (113.1..119.7) | 2.69 (2.67..2.72) | -2.0% no verdict (n 2 vs 3) / +2.0% no verdict (n 2 vs 3) / +2.9% no verdict (n 2 vs 3) / -1.4% no verdict (n 2 vs 3) / -14.5% no verdict (n 2 vs 3) | no verdict (n 2 vs 3) / no verdict (n 2 vs 3) | +6.0% (1 / 2 up); r1 -12.0% r2 +24.0% |
| s0 | 3 | 3, 7, 16 | 333.4 (309.9..360.0) | 2.687 (2.520..2.764) | 7.58 (7.37..8.29) | 118.4 (105.7..119.7) | 3.19 (3.08..3.38) | -6.2% overlap / +5.5% overlap / +1.1% overlap / +0.2% overlap / +1.3% overlap | overlap / overlap | +1.2% (2 / 3 up); r1 -13.3% r2 +7.1% r3 +1.2% |

Flagged runs: 1821-d11t-r3 (seq 13, 277.1 fps)

### slowbins: median fps of each run's slow-state bins (>= 90 % of sys.csv rows E<800 MHz), descriptive only

| seq | run | arm | round | slow bins | slow-bin fps (median) | fast bins (E<800 <= 10 %) | fast-bin fps (median) | window fps |
|---|---|---|---|---|---|---|---|---|
| 2 | 1757-base-r1 | base | 1 | 0 | - | 2 | 411.0 | 384.6 |
| 3 | 1800-s0-r1 | s0 | 1 | 3 | 319.5 | 0 | - | 333.4 |
| 4 | 1802-d11-r1 | d11 | 1 | 3 | 343.3 | 0 | - | 350.3 |
| 5 | 1804-d11t-r1 | d11t | 1 | 4 | 332.8 | 0 | - | 338.5 |
| 6 | 1806-d11p-r1 | d11p | 1 | 4 | 334.1 | 0 | - | 343.3 |
| 7 | 1808-s0-r2 | s0 | 2 | 4 | 305.8 | 0 | - | 309.9 |
| 8 | 1810-d11-r2 | d11 | 2 | 3 | 351.2 | 0 | - | 351.3 |
| 9 | 1813-d11t-r2 | d11t | 2 | 2 | 330.5 | 0 | - | 358.7 |
| 10 | 1815-d11p-r2 | d11p | 2 | 5 | 364.5 | 0 | - | 356.9 |
| 11 | 1817-base-r2 | base | 2 | 5 | 281.3 | 0 | - | 289.2 |
| 12 | 1819-d11-r3 | d11 | 3 | 3 | 342.1 | 0 | - | 352.5 |
| 13 | 1821-d11t-r3 | d11t | 3 | 5 | 270.7 | 0 | - | 277.1 |
| 14 | 1823-d11p-r3 | d11p | 3 | 4 | 332.7 | 0 | - | 335.3 |
| 15 | 1825-base-r3 | base | 3 | 0 | - | 0 | - | 355.6 |
| 16 | 1827-s0-r3 | s0 | 3 | 1 | 339.1 | 0 | - | 360.0 |

| arm | n | slow-bin fps median (min..max) | vs base | paired by round |
|---|---|---|---|---|
| base (all) | 1 | 281.3 (281.3..281.3) | ref | - |
| d11 (all) | 3 | 343.3 (342.1..351.2) | +22.0% (no verdict (n 3 vs 1), descriptive) | +24.9% (1 / 1 up); r2 +24.9% |
| d11p (all) | 3 | 334.1 (332.7..364.5) | +18.8% (no verdict (n 3 vs 1), descriptive) | +29.6% (1 / 1 up); r2 +29.6% |
| d11t (all) | 3 | 330.5 (270.7..332.8) | +17.5% (no verdict (n 3 vs 1), descriptive) | +17.5% (1 / 1 up); r2 +17.5% |
| s0 (all) | 3 | 319.5 (305.8..339.1) | +13.6% (no verdict (n 3 vs 1), descriptive) | +8.7% (1 / 1 up); r2 +8.7% |
| base (valid only) | 1 | 281.3 (281.3..281.3) | ref | - |
| d11 (valid only) | 3 | 343.3 (342.1..351.2) | +22.0% (no verdict (n 3 vs 1), descriptive) | +24.9% (1 / 1 up); r2 +24.9% |
| d11p (valid only) | 3 | 334.1 (332.7..364.5) | +18.8% (no verdict (n 3 vs 1), descriptive) | +29.6% (1 / 1 up); r2 +29.6% |
| d11t (valid only) | 3 | 330.5 (270.7..332.8) | +17.5% (no verdict (n 3 vs 1), descriptive) | +17.5% (1 / 1 up); r2 +17.5% |
| s0 (valid only) | 3 | 319.5 (305.8..339.1) | +13.6% (no verdict (n 3 vs 1), descriptive) | +8.7% (1 / 1 up); r2 +8.7% |


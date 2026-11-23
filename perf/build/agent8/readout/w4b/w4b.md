# W4b read-out add-on (Agent 7, task #29): <workspace>\build\agent8\matrix\20261122-1541

Window 4 (Agent 8, session 3): B = devoffB (codegen B) vs d0 = devoff2 (primary), then d3 = devoff3; W4b adds d11t = window 3's d11 + REX_TIMER_WAIT_BLOCKING=1

- command: `python bench\agent7\w4b_readout\w4b_readout.py build\agent8\matrix\20261122-1541 --scene-floor 0.02 -o build\agent8\readout\w4b\w4b.md --json build\agent8\readout\w4b\w4b.json`
- reference arm: d0; 17 result rows, 16 scored, 15 kept (kept = scored, frame stats, no real problems, valid timing, not excluded)
- window: each run's scored window as the runner cut it (frames.json window.first_row / rows of the frame csv it names); frames with a frame time <= 0 left out
- fps = frames / summed frame time; p50, p99 nearest-rank; 1% low = 1000 / mean of the slowest max(1, n // 100) frame times, in fps; >33 ms/min = frames over 33 ms per minute of summed frame time; arm cells = median (min..max) across the kept runs; n<3! = fewer than 3 kept runs

> **CPU SATURATED**: 5 of 15 kept runs with sys.csv had a median busy share >= 0.97 in the window (SAT): the game shared the CPU with >= 8.2 cores of other work (median). More load (Defender) cannot raise that reading; it takes CPU from the game. Treat the timing of SAT runs as contended; SAT runs are left out of the clean table.

## Arms (kept runs)

| arm | ref | n | fps | fps spread % | p50 ms | p99 ms | 1% low fps | >33 ms/min | slow state in window | scene flags | background cores (BG+ / SAT runs) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| d0 | * | 4 | 239.7 (213.9..270.4) | 23.6 | 3.399 (3.069..3.734) | 10.73 (9.92..10.96) | 83.4 (82.5..85.9) | 0.0 (0.0..0.0) | 4 of 4 | 0 | 8.1 (7.9..8.4) (0 / 2) |
| B |  | 3 | 275.8 (230.8..317.1) | 31.3 | 3.033 (2.884..3.435) | 10.01 (9.40..10.99) | 89.7 (83.5..93.4) | 0.0 (0.0..0.0) | 3 of 3 | 0 | 7.6 (6.8..8.2) (0 / 0) |
| d3 |  | 4 | 248.9 (198.4..298.6) | 40.3 | 3.215 (2.894..4.264) | 10.49 (9.71..12.90) | 85.2 (70.6..90.5) | 0.0 (0.0..0.0) | 4 of 4 | 0 | 7.9 (7.5..8.2) (0 / 2) |
| d11t |  | 4 | 237.7 (206.4..277.2) | 29.8 | 3.363 (3.025..3.857) | 10.94 (9.87..12.17) | 82.1 (72.7..87.3) | 0.0 (0.0..0.0) | 4 of 4 | 0 | 8.5 (8.0..8.7) (0 / 1) |

Deltas against d0: arm median vs d0 median; better / worse only when every run of the arm lies outside the d0 range, else overlap.

| arm | n vs n | d fps | d p50 | d p99 | d 1% low | d >33 ms/min | paired d fps by round: median (rounds up / rounds) |
|---|---|---|---|---|---|---|---|
| B | 3 vs 4 | +15.1% overlap | -10.8% overlap | -6.7% overlap | +7.5% overlap | +0.0/min overlap | +23.7% (3 / 3) |
| d3 | 4 vs 4 | +3.8% overlap | -5.4% overlap | -2.3% overlap | +2.1% overlap | +0.0/min overlap | +0.3% (2 / 4) |
| d11t | 4 vs 4 | -0.8% overlap | -1.1% overlap | +1.9% overlap | -1.6% overlap | +0.0/min overlap | +0.4% (2 / 4) |

## Arms without runs that have the slow state in the window, a scene flag or a background flag

(no kept runs)

## Runs

| seq | round | arm | rep | kept | fps | p50 ms | p99 ms | 1% low fps | >33 ms/min | window s | check | draws/frame p50 (mean) | scene | phase | slow (recheck) | slow (timerq) | game cores | background cores (p90; busy %) | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | d0 | 0 | no | 325.9 | 3.081 | 5.87 | 147.0 | 0.0 | 30.0 | ok | 226 (226) | 0.000 | normal (DAT fails 34, <4.5 ms 0.92) | no | no / 0% | 2.92 | 8.1 (p90 8.8; busy 91%) | cold (unscored) |
| 2 | 1 | d0 | 1 | yes | 256.4 | 3.234 | 10.77 | 84.3 | 0.0 | 50.0 | ok | 226 (226) | 0.000 loo | normal (DAT fails 34, <4.5 ms 0.81) | 93 s / 35% ! | 93 s / 22% | 3.37~ | >=8.4 (p90 8.7; busy 99%) SAT | - |
| 3 | 1 | B | 1 | yes | 317.1 | 2.884 | 9.40 | 93.4 | 0.0 | 50.0 | ok | 226 (226) | 0.000 | normal (DAT fails 34, <4.5 ms 0.87) | 94 s / 32% ! | 94 s / 19% | 3.14~ | 6.8 (p90 8.2; busy 81%) | - |
| 4 | 1 | d3 | 1 | yes | 231.0 | 3.347 | 11.10 | 83.3 | 0.0 | 50.0 | ok | 226 (226) | 0.000 | normal (DAT fails 34, <4.5 ms 0.67) | 76 s / 70% ! | 76 s / 35% | 3.45~ | >=8.1 (p90 8.4; busy 98%) SAT | - |
| 5 | 1 | d11t | 1 | yes | 206.4 | 3.857 | 11.49 | 80.6 | 0.0 | 50.0 | ok | 226 (226) | 0.000 | normal (DAT fails 34, <4.5 ms 0.56) | 61 s / 96% ! | 61 s / 42% | 3.00~ | >=8.6 (p90 8.8; busy 97%) SAT | - |
| 6 | 2 | B | 2 | no | 234.5 | 3.530 | 11.52 | 75.5 | 0.0 | 50.0 | ok | 226 (226) | 0.000 | normal (DAT fails 34, <4.5 ms 0.65) | 1 s / 64% ! | 1 s / 32% | 3.43~ | >=8.2 (p90 8.4; busy 97%) SAT | not timing |
| 7 | 2 | d3 | 2 | yes | 298.6 | 2.894 | 9.71 | 87.1 | 0.0 | 50.0 | ok | 226 (226) | 0.000 | normal (DAT fails 34, <4.5 ms 0.82) | 84 s / 54% ! | 84 s / 26% | 3.18~ | 7.7 (p90 8.2; busy 93%) | - |
| 8 | 2 | d11t | 2 | yes | 220.6 | 3.568 | 12.17 | 72.7 | 0.0 | 50.0 | ok | 226 (226) | 0.000 | normal (DAT fails 34, <4.5 ms 0.60) | 63 s / 96% ! | 63 s / 46% | 2.94~ | 8.7 (p90 8.9; busy 97%) | - |
| 9 | 2 | d0 | 2 | yes | 270.4 | 3.069 | 9.92 | 82.5 | 0.0 | 50.0 | ok | 226 (226) | 0.000 loo | normal (DAT fails 34, <4.5 ms 0.75) | 72 s / 76% ! | 72 s / 37% | 3.34~ | 7.9 (p90 8.2; busy 94%) | - |
| 10 | 3 | d3 | 3 | yes | 198.4 | 4.264 | 12.90 | 70.6 | 0.0 | 50.0 | ok | 226 (226) | 0.000 | normal (DAT fails 34, <4.5 ms 0.51) | 54 s / 100% ! | 54 s / 52% | 3.52~ | >=8.2 (p90 8.4; busy 98%) SAT | - |
| 11 | 3 | d11t | 3 | yes | 277.2 | 3.025 | 9.87 | 83.6 | 0.0 | 50.0 | ok | 226 (226) | 0.000 | normal (DAT fails 34, <4.5 ms 0.75) | 1 s / 96% ! | 1 s / 81% | 2.81~ | 8.0 (p90 8.6; busy 91%) | - |
| 12 | 3 | d0 | 3 | yes | 223.1 | 3.565 | 10.70 | 85.9 | 0.0 | 50.0 | ok | 226 (226) | 0.000 loo | normal (DAT fails 34, <4.5 ms 0.60) | 2 s / 100% ! | 2 s / 90% | 3.53~ | 8.1 (p90 8.3; busy 97%) | - |
| 13 | 3 | B | 3 | yes | 230.8 | 3.435 | 10.99 | 83.5 | 0.0 | 50.0 | ok | 226 (226) | 0.000 | normal (DAT fails 34, <4.5 ms 0.63) | 4 s / 100% ! | 4 s / 97% | 3.48~ | 8.2 (p90 8.3; busy 97%) | - |
| 14 | 4 | d11t | 4 | yes | 254.9 | 3.158 | 10.38 | 87.3 | 0.0 | 50.0 | ok | 226 (226) | 0.000 | normal (DAT fails 34, <4.5 ms 0.70) | 1 s / 100% ! | 1 s / 85% | 2.90~ | 8.4 (p90 8.9; busy 94%) | - |
| 15 | 4 | d0 | 4 | yes | 213.9 | 3.734 | 10.96 | 82.5 | 0.0 | 50.0 | ok | 226 (226) | 0.000 loo | normal (DAT fails 34, <4.5 ms 0.56) | 4 s / 100% ! | 4 s / 96% | 3.52~ | >=8.1 (p90 8.4; busy 97%) SAT | - |
| 16 | 4 | B | 4 | yes | 275.8 | 3.033 | 10.01 | 89.7 | 0.0 | 50.0 | ok | 226 (226) | 0.000 | normal (DAT fails 34, <4.5 ms 0.74) | 3 s / 90% ! | 3 s / 90% | 3.35 | 7.6 (p90 8.1; busy 91%) | - |
| 17 | 4 | d3 | 4 | yes | 266.8 | 3.082 | 9.87 | 90.5 | 0.0 | 50.0 | ok | 226 (226) | 0.000 | normal (DAT fails 34, <4.5 ms 0.72) | 1 s / 98% ! | 1 s / 93% | 3.37~ | 7.5 (p90 8.1; busy 91%) | - |

## 10 s bins of each run's scored window

- bins: consecutive 10 s of summed frame time from the start of the scored window (the frames of the Runs table); a frame belongs to the bin in which it ends; a last part shorter than 5 s is merged into the bin before it (a 50.01 s window gives 5 bins, the last one 40-50.01 s); bin start and end times are in the --json output (runs[].stat_bins)
- per bin, as for the whole window: p99 nearest-rank; 1% low = 1000 / mean of the slowest max(1, n // 100) frame times of the bin, in fps; >33 ms/min = frames over 33 ms per minute of the bin's summed frame time (the count in brackets); `-` = no such bin (a shorter window)
- arm rows: the median per bin across the kept runs of the arm (n = kept runs with that bin); the whole window column of an arm row is the arm table cell, median (min..max)

### fps per 10 s

| seq | run | kept | 0-10 s | 10-20 s | 20-30 s | 30-40 s | 40-50 s | whole window |
|---|---|---|---|---|---|---|---|---|
| 1 | 1541-cold-d0 | no | 297.0 | 332.6 | 347.9 | - | - | 325.9 |
| 2 | 1542-d0-r1 | yes | 327.9 | 301.4 | 302.6 | 179.3 | 170.8 | 256.4 |
| 3 | 1545-B-r1 | yes | 358.6 | 383.4 | 379.4 | 244.7 | 219.7 | 317.1 |
| 4 | 1547-d3-r1 | yes | 333.3 | 268.6 | 167.0 | 204.5 | 181.5 | 231.0 |
| 5 | 1549-d11t-r1 | yes | 172.0 | 183.5 | 237.1 | 236.2 | 203.2 | 206.4 |
| 6 | 1551-B-r2 | no | 289.9 | 199.9 | 206.7 | 216.2 | 259.6 | 234.5 |
| 7 | 1553-d3-r2 | yes | 359.3 | 400.5 | 277.6 | 251.5 | 204.3 | 298.6 |
| 8 | 1556-d11t-r2 | yes | 231.9 | 243.0 | 170.5 | 213.4 | 243.9 | 220.6 |
| 9 | 1558-d0-r2 | yes | 373.2 | 258.0 | 246.5 | 270.7 | 204.0 | 270.4 |
| 10 | 1600-d3-r3 | yes | 154.5 | 180.0 | 212.2 | 228.9 | 216.5 | 198.4 |
| 11 | 1602-d11t-r3 | yes | 278.0 | 276.2 | 277.6 | 282.1 | 271.9 | 277.2 |
| 12 | 1604-d0-r3 | yes | 227.3 | 217.8 | 220.3 | 254.1 | 195.8 | 223.1 |
| 13 | 1606-B-r3 | yes | 224.3 | 224.0 | 259.2 | 206.4 | 239.8 | 230.8 |
| 14 | 1608-d11t-r4 | yes | 232.0 | 236.1 | 259.1 | 268.6 | 278.7 | 254.9 |
| 15 | 1611-d0-r4 | yes | 234.8 | 216.7 | 196.4 | 172.4 | 249.3 | 213.9 |
| 16 | 1613-B-r4 | yes | 262.8 | 286.0 | 318.8 | 266.2 | 245.2 | 275.8 |
| 17 | 1615-d3-r4 | yes | 242.5 | 288.4 | 299.5 | 248.6 | 254.9 | 266.8 |
| | **d0** median, 4 kept | | 281.3 (n=4) | 237.9 (n=4) | 233.4 (n=4) | 216.7 (n=4) | 199.9 (n=4) | 239.7 (213.9..270.4) |
| | **B** median, 3 kept | | 262.8 (n=3) | 286.0 (n=3) | 318.8 (n=3) | 244.7 (n=3) | 239.8 (n=3) | 275.8 (230.8..317.1) |
| | **d3** median, 4 kept | | 287.9 (n=4) | 278.5 (n=4) | 244.9 (n=4) | 238.7 (n=4) | 210.4 (n=4) | 248.9 (198.4..298.6) |
| | **d11t** median, 4 kept | | 232.0 (n=4) | 239.6 (n=4) | 248.1 (n=4) | 252.4 (n=4) | 257.9 (n=4) | 237.7 (206.4..277.2) |

### p99 ms per 10 s

| seq | run | kept | 0-10 s | 10-20 s | 20-30 s | 30-40 s | 40-50 s | whole window |
|---|---|---|---|---|---|---|---|---|
| 1 | 1541-cold-d0 | no | 5.74 | 5.60 | 6.05 | - | - | 5.87 |
| 2 | 1542-d0-r1 | yes | 5.82 | 5.50 | 5.46 | 12.15 | 11.91 | 10.77 |
| 3 | 1545-B-r1 | yes | 5.80 | 5.52 | 5.34 | 10.88 | 11.33 | 9.40 |
| 4 | 1547-d3-r1 | yes | 5.61 | 11.00 | 12.06 | 10.99 | 11.11 | 11.10 |
| 5 | 1549-d11t-r1 | yes | 12.31 | 11.46 | 10.57 | 11.10 | 11.34 | 11.49 |
| 6 | 1551-B-r2 | no | 9.71 | 13.03 | 12.49 | 12.37 | 8.36 | 11.52 |
| 7 | 1553-d3-r2 | yes | 5.46 | 4.75 | 9.41 | 10.69 | 12.63 | 9.71 |
| 8 | 1556-d11t-r2 | yes | 11.78 | 11.19 | 13.99 | 12.11 | 9.96 | 12.17 |
| 9 | 1558-d0-r2 | yes | 5.13 | 10.45 | 11.79 | 10.03 | 11.17 | 9.92 |
| 10 | 1600-d3-r3 | yes | 13.75 | 13.24 | 12.88 | 11.64 | 11.63 | 12.90 |
| 11 | 1602-d11t-r3 | yes | 9.72 | 10.81 | 10.01 | 8.86 | 9.46 | 9.87 |
| 12 | 1604-d0-r3 | yes | 10.70 | 10.61 | 10.92 | 9.65 | 11.28 | 10.70 |
| 13 | 1606-B-r3 | yes | 11.23 | 11.33 | 10.18 | 11.35 | 10.42 | 10.99 |
| 14 | 1608-d11t-r4 | yes | 10.41 | 11.00 | 10.00 | 9.23 | 9.70 | 10.38 |
| 15 | 1611-d0-r4 | yes | 10.80 | 10.70 | 11.13 | 11.73 | 9.46 | 10.96 |
| 16 | 1613-B-r4 | yes | 10.77 | 9.54 | 8.55 | 10.10 | 10.78 | 10.01 |
| 17 | 1615-d3-r4 | yes | 10.61 | 9.01 | 8.95 | 9.92 | 10.48 | 9.87 |
| | **d0** median, 4 kept | | 8.26 (n=4) | 10.53 (n=4) | 11.03 (n=4) | 10.88 (n=4) | 11.22 (n=4) | 10.73 (9.92..10.96) |
| | **B** median, 3 kept | | 10.77 (n=3) | 9.54 (n=3) | 8.55 (n=3) | 10.88 (n=3) | 10.78 (n=3) | 10.01 (9.40..10.99) |
| | **d3** median, 4 kept | | 8.11 (n=4) | 10.01 (n=4) | 10.74 (n=4) | 10.84 (n=4) | 11.37 (n=4) | 10.49 (9.71..12.90) |
| | **d11t** median, 4 kept | | 11.09 (n=4) | 11.09 (n=4) | 10.29 (n=4) | 10.16 (n=4) | 9.83 (n=4) | 10.94 (9.87..12.17) |

### 1% low fps per 10 s

| seq | run | kept | 0-10 s | 10-20 s | 20-30 s | 30-40 s | 40-50 s | whole window |
|---|---|---|---|---|---|---|---|---|
| 1 | 1541-cold-d0 | no | 146.5 | 154.9 | 140.6 | - | - | 147.0 |
| 2 | 1542-d0-r1 | yes | 142.6 | 153.5 | 158.3 | 78.4 | 73.3 | 84.3 |
| 3 | 1545-B-r1 | yes | 153.1 | 157.4 | 160.6 | 84.8 | 79.4 | 93.4 |
| 4 | 1547-d3-r1 | yes | 155.9 | 81.8 | 78.8 | 82.3 | 84.4 | 83.3 |
| 5 | 1549-d11t-r1 | yes | 76.2 | 81.6 | 88.8 | 80.4 | 81.2 | 80.6 |
| 6 | 1551-B-r2 | no | 84.5 | 71.7 | 70.1 | 73.7 | 106.8 | 75.5 |
| 7 | 1553-d3-r2 | yes | 165.6 | 189.4 | 91.3 | 83.4 | 72.4 | 87.1 |
| 8 | 1556-d11t-r2 | yes | 74.4 | 74.7 | 68.5 | 72.6 | 83.4 | 72.7 |
| 9 | 1558-d0-r2 | yes | 176.8 | 80.0 | 74.5 | 82.2 | 75.7 | 82.5 |
| 10 | 1600-d3-r3 | yes | 60.7 | 71.0 | 72.2 | 77.6 | 75.4 | 70.6 |
| 11 | 1602-d11t-r3 | yes | 80.9 | 78.5 | 84.2 | 91.5 | 86.3 | 83.6 |
| 12 | 1604-d0-r3 | yes | 85.7 | 89.1 | 84.0 | 91.7 | 82.3 | 85.9 |
| 13 | 1606-B-r3 | yes | 83.5 | 78.8 | 86.1 | 80.8 | 89.9 | 83.5 |
| 14 | 1608-d11t-r4 | yes | 87.6 | 83.6 | 88.1 | 92.0 | 89.2 | 87.3 |
| 15 | 1611-d0-r4 | yes | 80.3 | 87.5 | 81.7 | 76.1 | 91.3 | 82.5 |
| 16 | 1613-B-r4 | yes | 87.2 | 95.3 | 99.3 | 89.3 | 83.5 | 89.7 |
| 17 | 1615-d3-r4 | yes | 83.8 | 100.5 | 99.4 | 93.9 | 83.2 | 90.5 |
| | **d0** median, 4 kept | | 114.1 (n=4) | 88.3 (n=4) | 82.9 (n=4) | 80.3 (n=4) | 79.0 (n=4) | 83.4 (82.5..85.9) |
| | **B** median, 3 kept | | 87.2 (n=3) | 95.3 (n=3) | 99.3 (n=3) | 84.8 (n=3) | 83.5 (n=3) | 89.7 (83.5..93.4) |
| | **d3** median, 4 kept | | 119.9 (n=4) | 91.2 (n=4) | 85.1 (n=4) | 82.8 (n=4) | 79.3 (n=4) | 85.2 (70.6..90.5) |
| | **d11t** median, 4 kept | | 78.6 (n=4) | 80.1 (n=4) | 86.2 (n=4) | 86.0 (n=4) | 84.8 (n=4) | 82.1 (72.7..87.3) |

### >33 ms/min per 10 s

| seq | run | kept | 0-10 s | 10-20 s | 20-30 s | 30-40 s | 40-50 s | whole window |
|---|---|---|---|---|---|---|---|---|
| 1 | 1541-cold-d0 | no | 0.0 (0) | 0.0 (0) | 0.0 (0) | - | - | 0.0 (0) |
| 2 | 1542-d0-r1 | yes | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) |
| 3 | 1545-B-r1 | yes | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) |
| 4 | 1547-d3-r1 | yes | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) |
| 5 | 1549-d11t-r1 | yes | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) |
| 6 | 1551-B-r2 | no | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) |
| 7 | 1553-d3-r2 | yes | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) |
| 8 | 1556-d11t-r2 | yes | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) |
| 9 | 1558-d0-r2 | yes | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) |
| 10 | 1600-d3-r3 | yes | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) |
| 11 | 1602-d11t-r3 | yes | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) |
| 12 | 1604-d0-r3 | yes | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) |
| 13 | 1606-B-r3 | yes | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) |
| 14 | 1608-d11t-r4 | yes | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) |
| 15 | 1611-d0-r4 | yes | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) |
| 16 | 1613-B-r4 | yes | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) |
| 17 | 1615-d3-r4 | yes | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) | 0.0 (0) |
| | **d0** median, 4 kept | | 0.0 (n=4) | 0.0 (n=4) | 0.0 (n=4) | 0.0 (n=4) | 0.0 (n=4) | 0.0 (0.0..0.0) |
| | **B** median, 3 kept | | 0.0 (n=3) | 0.0 (n=3) | 0.0 (n=3) | 0.0 (n=3) | 0.0 (n=3) | 0.0 (0.0..0.0) |
| | **d3** median, 4 kept | | 0.0 (n=4) | 0.0 (n=4) | 0.0 (n=4) | 0.0 (n=4) | 0.0 (n=4) | 0.0 (0.0..0.0) |
| | **d11t** median, 4 kept | | 0.0 (n=4) | 0.0 (n=4) | 0.0 (n=4) | 0.0 (n=4) | 0.0 (n=4) | 0.0 (0.0..0.0) |

## Scene check (draws per frame against the pooled d0 windows)

- distance: 1-D Wasserstein distance between the time-weighted distributions of ln(1 + perf.csv draw_calls) over the scored windows (0.10 ~ draws about 10 % apart on average; +-1 draw jitter ~0.005; same-scene runs on 2026-11-22 0.000-0.005, window 3's light-phase run 0025-d11-r1 0.036); `loo` = a reference run against the pool of the other reference runs
- reference pool: 4 kept runs (1542-d0-r1, 1558-d0-r2, 1604-d0-r3, 1611-d0-r4); time-weighted draws/frame p50 226, mean 226
- threshold: max(floor 0.020, 2.0 x largest leave-one-out distance 0.000) = 0.020
- flagged SCENE?: none
- per-run time-weighted mean draws/frame per 10 s of the window are in the --json output (draws_10s)

## Slow state

- slow (recheck): matrix_recheck.slow_state, imported read-only from bench/agent8/run/matrix_recheck.py: E-cores under 800 MHz for 3+ sys.csv samples in a row; onset s after the first-frame signal / share of window samples; `!` = such a stretch overlaps the window (Agent 11: not a result); `no` = never; `-` = no sys.csv
- scored runs with the slow state in the window: 1542-d0-r1, 1545-B-r1, 1547-d3-r1, 1549-d11t-r1, 1551-B-r2, 1553-d3-r2, 1556-d11t-r2, 1558-d0-r2, 1600-d3-r3, 1602-d11t-r3, 1604-d0-r3, 1606-B-r3, 1608-d11t-r4, 1611-d0-r4, 1613-B-r4, 1615-d3-r4
- slow (timerq): bench/agent11/timerq_slowstate.ps1, ran `powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_slowstate.ps1 -Root <workspace>\build\agent8\matrix -Since 20261122-1541 -EMhz 800 -MinRows 3`; onset s after the first frame / share of the samples from the first frame to the last sample; 17 of 17 runs matched

## Background load (system CPU minus the game's CPU over the scored window)

- system = logical CPUs x min(1, cpu_util_pct / cpu_perf_pct) per sys.csv sample whose interval centre lies in the window (_Total % Processor Utility / % Processor Performance = the busy share without the frequency scaling); game = the slope of proc.csv cpu_s over the same interval; background = system - game
- game cores = cpu_s over the whole scored window (`~` = run.json window_cpu_cores_mean, where proc.csv does not cover the window); background cell = median (p90; median busy %) over the window samples
- SAT = median busy share >= 0.97: no spare CPU, so the background reading is a floor (`>=`): more load cannot raise it, it takes CPU from the game instead
- BG+ = not SAT and background > reference + 1.0 cores; reference: median of this matrix's 10 unsaturated scored runs (20261122-0013 has none) = 7.94 cores
- reference dir 20261122-0013: 16 scored runs, 0 with sys.csv (0 of them SAT), so it gives no background value; game cores there (median per arm, proc.csv over the scored window): d0 3.43 (n=4), base 3.42 (n=4), d11 3.47 (n=4), n0 2.33 (n=4)
- SAT runs: 1542-d0-r1, 1547-d3-r1, 1549-d11t-r1, 1551-B-r2, 1600-d3-r3, 1611-d0-r4
- BG+ runs: none

## Checks

- per run: 17 of 17 runs with a window agree with frames.json (frames, mean fps, p50, p99, >33) and with results.csv fps_mean
- arm fps (median of the kept runs) vs run-matrix summary.md (median of results.csv fps_mean over scored OK runs that are not excluded): d0 239.710 vs 239.710; B 275.803 vs 255.130 (DIFFERENT: kept sets differ); d3 248.875 vs 248.875; d11t 237.738 vs 237.738


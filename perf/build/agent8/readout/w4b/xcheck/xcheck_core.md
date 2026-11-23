# Independent cross-check: W4b (Window 4b, matrix 20261122-1541)

- helper of Agent 8, own code: `build/agent8/readout/w4b/xcheck/xcheck.py w4b` (stdlib, reads only; no runner/add-on code imported)
- inputs: <workspace>\build\agent8\matrix\20261122-1541 (results.csv, runs/*/perf.csv, run.json, frames.json, proc.csv, threads.csv); add-on JSON <workspace>\build\agent8\readout\w4b\w4b.json (read as data for the comparison)
- reference arm: d0

## Definitions

      window   perf.csv data rows with 17 integer fields (malformed rows and a last line without newline are not rows);
               first row = the first row whose end offset (byte after its newline) is past run.json
               measure_start.perf_csv_bytes; last row = the shortest run of rows from there whose frame_time_us sum
               (values <= 0 count 0) reaches params.seconds (50 s scored, 30 s cold)
      frames   window rows with frame_time_us > 0 (zero rows stay in the row count only)
      fps      frames / (sum of their frame_time_us / 1e6)            [fps_wall = frames / run.json window_wall_s, info]
      median   nearest rank: sorted[ceil(n * 1/2) - 1] (lower middle for even n); p99 sorted[ceil(n * 99/100) - 1];
               p99.9 sorted[ceil(n * 999/1000) - 1]
      1% low   1e6 * k / (sum of the k largest frame times in us), k = max(1, n // 100)   (Agent 7 add-on, task #26)
      >33      frame_time_us > 33000; >100: > 100000
      cores    game CPU in the window: mean of proc.csv cpu_cores over the rows with phase 'measure' (one row per runner
               sample = run-timing's winCores; proc.csv rounds each to 0.01); slope = cpu_s(last measure row) -
               cpu_s(row before the first measure row), divided by the t_s difference (info)
      timerq   threads.csv busy_pct of the row named rex::thread::TimerQueue (thread-cpu.ps1: thread CPU s / driver window
               s x 100; the driver window starts 1-3 s after the frame window and ends at the measure-end mark)
      arm      over the arm's runs: statistics.median (mean of the two middle values for even n), min, max; delta = arm
               median / reference median - 1; decision: better / worse only when every run of the arm lies outside the
               reference's min..max (fps higher = better, ms lower = better), else overlap; paired by round: per round
               arm / reference - 1, median over the rounds, rounds up (fps) / rounds faster (ms)

## Per run (cold included)

| seq | round | arm | run | scored | valid | rows (first) | frames | window s | fps | fps_wall | median ms | p99 ms | p99.9 ms | max ms | 1% low fps (k) | >33 | >100 | game cores (n) | cores slope | run.json cores | TimerQueue busy % (max 1 s) | runner check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cold | d0 | 1541-cold-d0 | no | yes | 9776 (22440) | 9776 | 30.001 | 325.852 | 325.779 | 3.081 | 5.871 | 7.727 | 15.602 | 147.0 (97) | 0 | 0 | 2.920 (30) | 2.919 | 2.919 | - (no threads.csv) | ok |
| 2 | 1 | d0 | 1542-d0-r1 | yes | yes | 12821 (24060) | 12821 | 50.011 | 256.363 | 256.400 | 3.234 | 10.766 | 12.873 | 24.178 | 84.3 (128) | 0 | 0 | 3.367 (50) | 3.367 | 3.366 | 47.2 (75.3) | ok |
| 3 | 1 | B | 1545-B-r1 | yes | yes | 15857 (24360) | 15857 | 50.001 | 317.135 | 317.104 | 2.884 | 9.398 | 12.118 | 18.994 | 93.4 (158) | 0 | 0 | 3.141 (50) | 3.141 | 3.142 | 41.4 (78.3) | ok |
| 4 | 1 | d3 | 1547-d3-r1 | yes | yes | 11549 (22980) | 11549 | 50.001 | 230.974 | 231.004 | 3.347 | 11.098 | 13.137 | 19.364 | 83.3 (115) | 0 | 0 | 3.449 (50) | 3.449 | 3.449 | 55.5 (75.5) | ok |
| 5 | 1 | d11t | 1549-d11t-r1 | yes | yes | 10321 (23400) | 10321 | 50.000 | 206.420 | 206.473 | 3.857 | 11.494 | 13.265 | 23.665 | 80.6 (103) | 0 | 0 | 3.004 (50) | 3.004 | 3.004 | 6.0 (11.5) | ok |
| 6 | 2 | B | 1551-B-r2 | yes | NO | 11723 (23400) | 11723 | 50.001 | 234.457 | 234.456 | 3.530 | 11.518 | 14.963 | 20.690 | 75.5 (117) | 0 | 0 | 3.430 (50) | 3.429 | 3.430 | 55.9 (72.1) | ok |
| 7 | 2 | d3 | 1553-d3-r2 | yes | yes | 14932 (24060) | 14932 | 50.001 | 298.632 | 298.658 | 2.894 | 9.709 | 13.112 | 22.999 | 87.1 (149) | 0 | 0 | 3.179 (50) | 3.178 | 3.179 | 46.8 (78.6) | ok |
| 8 | 2 | d11t | 1556-d11t-r2 | yes | yes | 11029 (25860) | 11029 | 50.004 | 220.563 | 220.580 | 3.568 | 12.170 | 15.293 | 18.173 | 72.7 (110) | 0 | 0 | 2.938 (50) | 2.937 | 2.937 | 5.0 (11.7) | ok |
| 9 | 2 | d0 | 1558-d0-r2 | yes | yes | 13523 (23100) | 13523 | 50.002 | 270.449 | 270.458 | 3.069 | 9.923 | 14.085 | 19.352 | 82.5 (135) | 0 | 0 | 3.340 (50) | 3.340 | 3.340 | 53.6 (74.7) | ok |
| 10 | 3 | d3 | 1600-d3-r3 | yes | yes | 9923 (20400) | 9923 | 50.008 | 198.429 | 198.472 | 4.264 | 12.899 | 15.490 | 31.011 | 70.6 (99) | 0 | 0 | 3.523 (50) | 3.523 | 3.523 | 61.3 (72.5) | ok |
| 11 | 3 | d11t | 1602-d11t-r3 | yes | yes | 13859 (20400) | 13859 | 50.004 | 277.160 | 277.268 | 3.025 | 9.865 | 15.010 | 15.896 | 83.6 (138) | 0 | 0 | 2.813 (50) | 2.812 | 2.812 | 5.1 (11.0) | ok |
| 12 | 3 | d0 | 1604-d0-r3 | yes | yes | 11154 (19260) | 11154 | 50.005 | 223.058 | 223.103 | 3.565 | 10.698 | 12.650 | 15.148 | 85.9 (111) | 0 | 0 | 3.528 (50) | 3.527 | 3.527 | 60.6 (78.3) | ok |
| 13 | 3 | B | 1606-B-r3 | yes | yes | 11538 (16080) | 11538 | 50.001 | 230.756 | 230.777 | 3.435 | 10.989 | 13.190 | 16.156 | 83.5 (115) | 0 | 0 | 3.481 (50) | 3.480 | 3.480 | 61.5 (75.9) | ok |
| 14 | 4 | d11t | 1608-d11t-r4 | yes | yes | 12747 (17400) | 12747 | 50.005 | 254.914 | 254.952 | 3.158 | 10.377 | 12.420 | 19.126 | 87.3 (127) | 0 | 0 | 2.895 (50) | 2.896 | 2.896 | 5.6 (17.8) | ok |
| 15 | 4 | d0 | 1611-d0-r4 | yes | yes | 10696 (19140) | 10696 | 50.001 | 213.917 | 213.946 | 3.734 | 10.965 | 13.862 | 20.275 | 82.5 (106) | 0 | 0 | 3.517 (50) | 3.518 | 3.517 | 62.6 (82.3) | ok |
| 16 | 4 | B | 1613-B-r4 | yes | yes | 13791 (19020) | 13791 | 50.003 | 275.803 | 275.764 | 3.033 | 10.008 | 12.266 | 15.629 | 89.7 (137) | 0 | 0 | 3.350 (50) | 3.349 | 3.349 | 54.3 (69.9) | ok |
| 17 | 4 | d3 | 1615-d3-r4 | yes | yes | 13339 (18420) | 13339 | 50.001 | 266.777 | 266.800 | 3.082 | 9.874 | 12.034 | 20.516 | 90.5 (133) | 0 | 0 | 3.371 (50) | 3.372 | 3.372 | 56.2 (70.5) | ok |

Runner check = every run compared with frames.json (first_row, rows, zero_rows, rows_by_end_bytes, rows_total, bad_rows, frames, window_s, mean_fps, median, p99, p99.9, max, >33, >100, share < 4.5 ms), results.csv (frames, window_s, fps_mean, median_ms, p99_ms, p999_ms, max_ms, over33, over100, light_share, cpu_cores_mean) and run.json (window_cpu_cores_mean, window_cpu_samples); tolerance: counts exact, ms |d| <= 0.01 ms and <= 0.1 %, others <= 0.1 %, shares <= 0.001.

### Differences vs frames.json / results.csv / run.json above tolerance

- none above tolerance (17 runs, 29 fields each)

### Differences vs the add-on JSON (Agent 8 read-out, per run: frames, window_s, fps, p50, p99, 1% low, >33, game cores)

- none above tolerance

## Arms: every scored run (16; B includes run 6 = 1551-B-r2, valid_timing=False)

| arm | n | runs | fps | median ms | p99 ms | 1% low fps | game cores (mean) | TimerQueue busy % |
|---|---|---|---|---|---|---|---|---|
| d0 (ref) | 4 | 1542-d0-r1, 1558-d0-r2, 1604-d0-r3, 1611-d0-r4 | 239.7 (213.9..270.4) | 3.399 (3.069..3.734) | 10.73 (9.92..10.96) | 83.4 (82.5..85.9) | 3.44 (3.34..3.53) (3.438) | 57.1 (47.2..62.6) |
| B | 4 | 1545-B-r1, 1551-B-r2, 1606-B-r3, 1613-B-r4 | 255.1 (230.8..317.1) | 3.234 (2.884..3.530) | 10.50 (9.40..11.52) | 86.6 (75.5..93.4) | 3.39 (3.14..3.48) (3.350) | 55.1 (41.4..61.5) |
| d3 | 4 | 1547-d3-r1, 1553-d3-r2, 1600-d3-r3, 1615-d3-r4 | 248.9 (198.4..298.6) | 3.215 (2.894..4.264) | 10.49 (9.71..12.90) | 85.2 (70.6..90.5) | 3.41 (3.18..3.52) (3.381) | 55.9 (46.8..61.3) |
| d11t | 4 | 1549-d11t-r1, 1556-d11t-r2, 1602-d11t-r3, 1608-d11t-r4 | 237.7 (206.4..277.2) | 3.363 (3.025..3.857) | 10.94 (9.87..12.17) | 82.1 (72.7..87.3) | 2.92 (2.81..3.00) (2.913) | 5.3 (5.0..6.0) |

Deltas vs d0 (arm median / ref median - 1; decision: better/worse only when every run lies outside the ref min..max)

| arm | n vs n | d fps | d median | d p99 | d 1% low | d game cores | paired fps by round: median (up / rounds); per round | paired median ms: median rel (faster / rounds); median diff ms (min..max) | paired game cores: median rel; median diff (min..max); per round |
|---|---|---|---|---|---|---|---|---|---|
| B | 4 vs 4 | +6.4% overlap | -4.9% overlap | -2.2% overlap | +3.8% overlap | -1.5% overlap | +13.6% (3 / 4); r1 +23.7% r2 -13.3% r3 +3.5% r4 +28.9% | -7.2% (3 / 4); -0.240 (-0.701..0.461) | -3.0%; -0.107 (-0.225..0.089); r1 -6.7% r2 +2.7% r3 -1.3% r4 -4.8% |
| d3 | 4 vs 4 | +3.8% overlap | -5.4% overlap | -2.3% overlap | +2.1% overlap | -0.9% overlap | +0.3% (2 / 4); r1 -9.9% r2 +10.4% r3 -11.0% r4 +24.7% | -1.1% (2 / 4); -0.031 (-0.652..0.699) | -2.1%; -0.075 (-0.161..0.082); r1 +2.4% r2 -4.8% r3 -0.1% r4 -4.1% |
| d11t | 4 vs 4 | -0.8% overlap | -1.1% overlap | +1.9% overlap | -1.6% overlap | -15.3% better | +0.4% (2 / 4); r1 -19.5% r2 -18.4% r3 +24.3% r4 +19.2% | +0.6% (2 / 4); -0.020 (-0.576..0.623) | -14.9%; -0.512 (-0.715..-0.363); r1 -10.8% r2 -12.1% r3 -20.3% r4 -17.7% |

Extra pairs (same rules; first arm vs second arm)

| arm vs | n vs n | d fps | d median | d p99 | d 1% low | d game cores | paired fps by round: median (up / rounds); per round | paired median ms: median rel (faster / rounds); median diff ms (min..max) | paired game cores: median rel; median diff (min..max); per round |
|---|---|---|---|---|---|---|---|---|---|
| d11t vs d0 | 4 vs 4 | -0.8% overlap | -1.1% overlap | +1.9% overlap | -1.6% overlap | -15.3% better | +0.4% (2 / 4); r1 -19.5% r2 -18.4% r3 +24.3% r4 +19.2% | +0.6% (2 / 4); -0.020 (-0.576..0.623) | -14.9%; -0.512 (-0.715..-0.363); r1 -10.8% r2 -12.1% r3 -20.3% r4 -17.7% |

## Arms: scored runs without run 6 (1551-B-r2) = valid_timing runs (15)

| arm | n | runs | fps | median ms | p99 ms | 1% low fps | game cores (mean) | TimerQueue busy % |
|---|---|---|---|---|---|---|---|---|
| d0 (ref) | 4 | 1542-d0-r1, 1558-d0-r2, 1604-d0-r3, 1611-d0-r4 | 239.7 (213.9..270.4) | 3.399 (3.069..3.734) | 10.73 (9.92..10.96) | 83.4 (82.5..85.9) | 3.44 (3.34..3.53) (3.438) | 57.1 (47.2..62.6) |
| B | 3 | 1545-B-r1, 1606-B-r3, 1613-B-r4 | 275.8 (230.8..317.1) | 3.033 (2.884..3.435) | 10.01 (9.40..10.99) | 89.7 (83.5..93.4) | 3.35 (3.14..3.48) (3.324) | 54.3 (41.4..61.5) |
| d3 | 4 | 1547-d3-r1, 1553-d3-r2, 1600-d3-r3, 1615-d3-r4 | 248.9 (198.4..298.6) | 3.215 (2.894..4.264) | 10.49 (9.71..12.90) | 85.2 (70.6..90.5) | 3.41 (3.18..3.52) (3.381) | 55.9 (46.8..61.3) |
| d11t | 4 | 1549-d11t-r1, 1556-d11t-r2, 1602-d11t-r3, 1608-d11t-r4 | 237.7 (206.4..277.2) | 3.363 (3.025..3.857) | 10.94 (9.87..12.17) | 82.1 (72.7..87.3) | 2.92 (2.81..3.00) (2.913) | 5.3 (5.0..6.0) |

Deltas vs d0 (arm median / ref median - 1; decision: better/worse only when every run lies outside the ref min..max)

| arm | n vs n | d fps | d median | d p99 | d 1% low | d game cores | paired fps by round: median (up / rounds); per round | paired median ms: median rel (faster / rounds); median diff ms (min..max) | paired game cores: median rel; median diff (min..max); per round |
|---|---|---|---|---|---|---|---|---|---|
| B | 3 vs 4 | +15.1% overlap | -10.8% overlap | -6.7% overlap | +7.5% overlap | -2.7% overlap | +23.7% (3 / 3); r1 +23.7% r3 +3.5% r4 +28.9% | -10.8% (3 / 3); -0.350 (-0.701..-0.130) | -4.8%; -0.167 (-0.225..-0.047); r1 -6.7% r3 -1.3% r4 -4.8% |
| d3 | 4 vs 4 | +3.8% overlap | -5.4% overlap | -2.3% overlap | +2.1% overlap | -0.9% overlap | +0.3% (2 / 4); r1 -9.9% r2 +10.4% r3 -11.0% r4 +24.7% | -1.1% (2 / 4); -0.031 (-0.652..0.699) | -2.1%; -0.075 (-0.161..0.082); r1 +2.4% r2 -4.8% r3 -0.1% r4 -4.1% |
| d11t | 4 vs 4 | -0.8% overlap | -1.1% overlap | +1.9% overlap | -1.6% overlap | -15.3% better | +0.4% (2 / 4); r1 -19.5% r2 -18.4% r3 +24.3% r4 +19.2% | +0.6% (2 / 4); -0.020 (-0.576..0.623) | -14.9%; -0.512 (-0.715..-0.363); r1 -10.8% r2 -12.1% r3 -20.3% r4 -17.7% |

Extra pairs (same rules; first arm vs second arm)

| arm vs | n vs n | d fps | d median | d p99 | d 1% low | d game cores | paired fps by round: median (up / rounds); per round | paired median ms: median rel (faster / rounds); median diff ms (min..max) | paired game cores: median rel; median diff (min..max); per round |
|---|---|---|---|---|---|---|---|---|---|
| d11t vs d0 | 4 vs 4 | -0.8% overlap | -1.1% overlap | +1.9% overlap | -1.6% overlap | -15.3% better | +0.4% (2 / 4); r1 -19.5% r2 -18.4% r3 +24.3% r4 +19.2% | +0.6% (2 / 4); -0.020 (-0.576..0.623) | -14.9%; -0.512 (-0.715..-0.363); r1 -10.8% r2 -12.1% r3 -20.3% r4 -17.7% |

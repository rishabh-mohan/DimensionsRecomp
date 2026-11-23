# Independent cross-check: W5 (Window 5, matrix 20261122-1756)

- helper of Agent 8, own code: `build/agent8/readout/w4b/xcheck/xcheck.py w5` (stdlib, reads only; no runner/add-on code imported)
- inputs: <workspace>\build\agent8\matrix\20261122-1756 (results.csv, runs/*/perf.csv, run.json, frames.json, proc.csv, threads.csv); add-on JSON <workspace>\build\agent8\readout\w5\w5.json (read as data for the comparison)
- reference arm: base

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
| 1 | cold | base | 1756-cold-base | no | yes | 11875 (25920) | 11875 | 30.001 | 395.824 | 395.977 | 2.437 | 5.156 | 6.733 | 10.595 | 171.6 (118) | 0 | 0 | 2.719 (30) | 2.720 | 2.719 | - (no threads.csv) | ok |
| 2 | 1 | base | 1757-base-r1 | yes | yes | 19230 (26880) | 19230 | 50.001 | 384.596 | 384.546 | 2.411 | 6.434 | 8.412 | 12.068 | 135.6 (192) | 0 | 0 | 2.901 (50) | 2.901 | 2.901 | 39.5 (69.3) | ok |
| 3 | 1 | s0 | 1800-s0-r1 | yes | yes | 16669 (24240) | 16669 | 50.001 | 333.373 | 333.297 | 2.687 | 7.579 | 9.866 | 17.355 | 118.4 (166) | 0 | 0 | 3.193 (50) | 3.192 | 3.193 | 50.6 (71.4) | ok |
| 4 | 1 | d11 | 1802-d11-r1 | yes | yes | 17519 (23940) | 17519 | 50.005 | 350.343 | 350.551 | 2.620 | 7.182 | 9.268 | 13.376 | 125.9 (175) | 0 | 0 | 3.180 (50) | 3.180 | 3.180 | 49.0 (66.1) | ok |
| 5 | 1 | d11t | 1804-d11t-r1 | yes | yes | 16925 (25080) | 16925 | 50.000 | 338.498 | 338.572 | 2.647 | 7.841 | 10.447 | 16.011 | 113.1 (169) | 0 | 0 | 2.719 (50) | 2.719 | 2.719 | 4.5 (10.0) | ok |
| 6 | 1 | d11p | 1806-d11p-r1 | yes | yes | 17168 (23760) | 17168 | 50.002 | 343.344 | 343.257 | 2.624 | 7.724 | 10.651 | 17.631 | 114.8 (171) | 0 | 0 | 2.765 (50) | 2.766 | 2.766 | 5.2 (11.5) | ok |
| 7 | 2 | s0 | 1808-s0-r2 | yes | yes | 15496 (24540) | 15496 | 50.003 | 309.902 | 309.918 | 2.764 | 8.285 | 10.853 | 19.374 | 105.7 (154) | 0 | 0 | 3.380 (50) | 3.381 | 3.380 | 55.4 (67.5) | ok |
| 8 | 2 | d11 | 1810-d11-r2 | yes | yes | 17567 (24540) | 17567 | 50.000 | 351.337 | 351.373 | 2.612 | 7.454 | 9.907 | 13.477 | 120.1 (175) | 0 | 0 | 3.187 (50) | 3.187 | 3.187 | 51.1 (64.9) | ok |
| 9 | 2 | d11t | 1813-d11t-r2 | yes | yes | 17938 (24240) | 17938 | 50.001 | 358.750 | 358.799 | 2.547 | 7.585 | 9.380 | 17.194 | 119.7 (179) | 0 | 0 | 2.671 (50) | 2.670 | 2.670 | 4.0 (8.9) | ok |
| 10 | 2 | d11p | 1815-d11p-r2 | yes | yes | 17847 (24240) | 17847 | 50.002 | 356.926 | 356.948 | 2.580 | 7.496 | 9.853 | 15.438 | 117.7 (178) | 0 | 0 | 2.689 (50) | 2.689 | 2.689 | 4.2 (11.3) | ok |
| 11 | 2 | base | 1817-base-r2 | yes | yes | 14462 (23700) | 14462 | 50.001 | 289.232 | 289.223 | 2.931 | 8.107 | 10.721 | 14.982 | 107.0 (144) | 0 | 0 | 3.456 (50) | 3.456 | 3.456 | 60.5 (72.3) | ok |
| 12 | 3 | d11 | 1819-d11-r3 | yes | yes | 17624 (22500) | 17624 | 50.002 | 352.469 | 352.426 | 2.560 | 7.593 | 10.253 | 13.479 | 115.8 (176) | 0 | 0 | 3.156 (50) | 3.156 | 3.156 | 47.5 (73.4) | ok |
| 13 | 3 | d11t | 1821-d11t-r3 | yes | yes | 13858 (19380) | 13858 | 50.008 | 277.116 | 277.171 | 3.028 | 9.952 | 12.123 | 15.725 | 90.6 (138) | 0 | 0 | 2.835 (50) | 2.836 | 2.835 | 4.5 (14.2) | ok |
| 14 | 3 | d11p | 1823-d11p-r3 | yes | yes | 16769 (24780) | 16769 | 50.005 | 335.346 | 335.398 | 2.645 | 8.262 | 10.726 | 14.512 | 105.4 (167) | 0 | 0 | 2.784 (50) | 2.783 | 2.783 | 5.9 (13.7) | ok |
| 15 | 3 | base | 1825-base-r3 | yes | yes | 17778 (23760) | 17778 | 50.000 | 355.559 | 355.510 | 2.546 | 7.494 | 9.665 | 14.476 | 118.1 (177) | 0 | 0 | 3.150 (50) | 3.150 | 3.150 | 49.0 (75.6) | ok |
| 16 | 3 | s0 | 1827-s0-r3 | yes | yes | 18000 (23280) | 18000 | 50.002 | 359.988 | 359.850 | 2.520 | 7.370 | 9.769 | 13.270 | 119.7 (180) | 0 | 0 | 3.080 (50) | 3.080 | 3.081 | 46.5 (64.0) | ok |

Runner check = every run compared with frames.json (first_row, rows, zero_rows, rows_by_end_bytes, rows_total, bad_rows, frames, window_s, mean_fps, median, p99, p99.9, max, >33, >100, share < 4.5 ms), results.csv (frames, window_s, fps_mean, median_ms, p99_ms, p999_ms, max_ms, over33, over100, light_share, cpu_cores_mean) and run.json (window_cpu_cores_mean, window_cpu_samples); tolerance: counts exact, ms |d| <= 0.01 ms and <= 0.1 %, others <= 0.1 %, shares <= 0.001.

### Differences vs frames.json / results.csv / run.json above tolerance

- none above tolerance (16 runs, 29 fields each)

### Differences vs the add-on JSON (Agent 8 read-out, per run: frames, window_s, fps, p50, p99, 1% low, >33, game cores)

- none above tolerance

## Arms: every scored run (15, all valid_timing)

| arm | n | runs | fps | median ms | p99 ms | 1% low fps | game cores (mean) | TimerQueue busy % |
|---|---|---|---|---|---|---|---|---|
| base (ref) | 3 | 1757-base-r1, 1817-base-r2, 1825-base-r3 | 355.6 (289.2..384.6) | 2.546 (2.411..2.931) | 7.49 (6.43..8.11) | 118.1 (107.0..135.6) | 3.15 (2.90..3.46) (3.169) | 49.0 (39.5..60.5) |
| s0 | 3 | 1800-s0-r1, 1808-s0-r2, 1827-s0-r3 | 333.4 (309.9..360.0) | 2.687 (2.520..2.764) | 7.58 (7.37..8.29) | 118.4 (105.7..119.7) | 3.19 (3.08..3.38) (3.218) | 50.6 (46.5..55.4) |
| d11 | 3 | 1802-d11-r1, 1810-d11-r2, 1819-d11-r3 | 351.3 (350.3..352.5) | 2.612 (2.560..2.620) | 7.45 (7.18..7.59) | 120.1 (115.8..125.9) | 3.18 (3.16..3.19) (3.174) | 49.0 (47.5..51.1) |
| d11t | 3 | 1804-d11t-r1, 1813-d11t-r2, 1821-d11t-r3 | 338.5 (277.1..358.7) | 2.647 (2.547..3.028) | 7.84 (7.58..9.95) | 113.1 (90.6..119.7) | 2.72 (2.67..2.84) (2.742) | 4.5 (4.0..4.5) |
| d11p | 3 | 1806-d11p-r1, 1815-d11p-r2, 1823-d11p-r3 | 343.3 (335.3..356.9) | 2.624 (2.580..2.645) | 7.72 (7.50..8.26) | 114.8 (105.4..117.7) | 2.77 (2.69..2.78) (2.746) | 5.2 (4.2..5.9) |

Deltas vs base (arm median / ref median - 1; decision: better/worse only when every run lies outside the ref min..max)

| arm | n vs n | d fps | d median | d p99 | d 1% low | d game cores | paired fps by round: median (up / rounds); per round | paired median ms: median rel (faster / rounds); median diff ms (min..max) | paired game cores: median rel; median diff (min..max); per round |
|---|---|---|---|---|---|---|---|---|---|
| s0 | 3 vs 3 | -6.2% overlap | +5.5% overlap | +1.1% overlap | +0.2% overlap | +1.3% overlap | +1.2% (2 / 3); r1 -13.3% r2 +7.1% r3 +1.2% | -1.0% (2 / 3); -0.026 (-0.167..0.276) | -2.2%; -0.070 (-0.076..0.292); r1 +10.1% r2 -2.2% r3 -2.2% |
| d11 | 3 vs 3 | -1.2% overlap | +2.6% overlap | -0.5% overlap | +1.7% overlap | +0.9% overlap | -0.9% (1 / 3); r1 -8.9% r2 +21.5% r3 -0.9% | +0.5% (1 / 3); 0.014 (-0.319..0.209) | +0.2%; 0.005 (-0.269..0.279); r1 +9.6% r2 -7.8% r3 +0.2% |
| d11t | 3 vs 3 | -4.8% overlap | +4.0% overlap | +4.6% overlap | -4.3% overlap | -13.7% better | -12.0% (1 / 3); r1 -12.0% r2 +24.0% r3 -22.1% | +9.8% (1 / 3); 0.236 (-0.384..0.482) | -10.0%; -0.315 (-0.785..-0.182); r1 -6.3% r2 -22.7% r3 -10.0% |
| d11p | 3 vs 3 | -3.4% overlap | +3.1% overlap | +3.1% overlap | -2.8% overlap | -12.2% better | -5.7% (1 / 3); r1 -10.7% r2 +23.4% r3 -5.7% | +3.9% (1 / 3); 0.099 (-0.351..0.213) | -11.6%; -0.367 (-0.767..-0.136); r1 -4.7% r2 -22.2% r3 -11.6% |

Extra pairs (same rules; first arm vs second arm)

| arm vs | n vs n | d fps | d median | d p99 | d 1% low | d game cores | paired fps by round: median (up / rounds); per round | paired median ms: median rel (faster / rounds); median diff ms (min..max) | paired game cores: median rel; median diff (min..max); per round |
|---|---|---|---|---|---|---|---|---|---|
| d11 vs s0 | 3 vs 3 | +5.4% overlap | -2.8% overlap | -1.6% overlap | +1.4% overlap | -0.4% overlap | +5.1% (2 / 3); r1 +5.1% r2 +13.4% r3 -2.1% | -2.5% (2 / 3); -0.067 (-0.152..0.040) | -0.4%; -0.013 (-0.193..0.075); r1 -0.4% r2 -5.7% r3 +2.4% |
| d11t vs s0 | 3 vs 3 | +1.5% overlap | -1.5% overlap | +3.5% overlap | -4.5% overlap | -14.8% better | +1.5% (2 / 3); r1 +1.5% r2 +15.8% r3 -23.0% | -1.5% (2 / 3); -0.040 (-0.217..0.508) | -14.8%; -0.474 (-0.709..-0.245); r1 -14.8% r2 -21.0% r3 -8.0% |
| d11p vs s0 | 3 vs 3 | +3.0% overlap | -2.3% overlap | +1.9% overlap | -3.0% overlap | -13.4% better | +3.0% (2 / 3); r1 +3.0% r2 +15.2% r3 -6.8% | -2.3% (2 / 3); -0.063 (-0.184..0.125) | -13.4%; -0.428 (-0.691..-0.297); r1 -13.4% r2 -20.4% r3 -9.6% |
| d11t vs d11 | 3 vs 3 | -3.7% overlap | +1.3% overlap | +5.2% overlap | -5.8% overlap | -14.5% better | -3.4% (1 / 3); r1 -3.4% r2 +2.1% r3 -21.4% | +1.0% (1 / 3); 0.027 (-0.065..0.468) | -14.5%; -0.461 (-0.516..-0.320); r1 -14.5% r2 -16.2% r3 -10.2% |
| d11p vs d11 | 3 vs 3 | -2.3% overlap | +0.5% overlap | +3.6% overlap | -4.4% overlap | -13.0% better | -2.0% (1 / 3); r1 -2.0% r2 +1.6% r3 -4.9% | +0.2% (1 / 3); 0.004 (-0.032..0.085) | -13.0%; -0.415 (-0.498..-0.372); r1 -13.0% r2 -15.6% r3 -11.8% |
| d11p vs d11t | 3 vs 3 | +1.4% overlap | -0.9% overlap | -1.5% overlap | +1.5% overlap | +1.7% overlap | +1.4% (2 / 3); r1 +1.4% r2 -0.5% r3 +21.0% | -0.9% (2 / 3); -0.023 (-0.383..0.033) | +0.7%; 0.018 (-0.052..0.046); r1 +1.7% r2 +0.7% r3 -1.8% |

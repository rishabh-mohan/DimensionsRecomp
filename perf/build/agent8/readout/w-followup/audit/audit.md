# Task #20 follow-up audit: W6, W9, W5b, W4c (read-only)

Generated 2026-11-23 06:37:17 by `build/agent8/readout/w-followup/audit/audit.py` (helper of Agent 8). Inputs: `build/agent8/matrix/<stamp>/` for W6-1=20261123-0009, W9-1=20261123-0108, W5b-1=20261123-0155, W4c=20261123-0239, W6-2=20261123-0313, W9-2=20261123-0401, W5b-2=20261123-0451. Writes only into `build/agent8/readout/w-followup/audit/`.

## Findings (summary)

Helper of Agent 8, task #20, read-only. 7 folders, 135 runs (128 scored). ng_t = time-based busy logical CPUs minus game cores (occupancy); ng_u = utility-based, Agent 1 style (reads ~1 core higher at these clocks). Values are 50 s window values unless stated. Details are in sections 1-5 below.

**1. Slow state.** timerq_slowstate_3mode.ps1 found 0 slow-state runs in every folder and arm: onset_s '-', slow_pct 0 (timerq3-<stamp>.csv/.txt). sys.csv agrees: 0 E-cluster samples below 800 MHz in any warm-up or window. The lowest 1 s E sample was 1446 MHz in a window and 1378 MHz in a warm-up (0143-q500-r4).

**2. sys.csv audit.** No window or warm-up had any change in AC, scheme (Balanced), overlay (best_performance), screensaver, input desktop or user input; only batt_pct changed (98 to 100 % on AC). fg_game was 100 % in all 135 runs. Folder medians: ng_t 2.37-2.58 cores, ng_u 3.34-3.51, game 1.87-2.55, P util 61.7-64.2 %, E 1955-2108 MHz. A run is flagged if it is above the rest's max with robust z >= 3, or has >= 12 burst seconds. fps rank: 1 = slowest scored run in the folder; fps_rel = fps / arm median.

| folder | flagged runs (window ng_t mean; fps) |
|---|---|
| W6-1 0009 | 0023-p2fc-r2 (3.95; fps_rel 0.916, 9.4-core burst at the window start), 0025-s0-r2 (4.09; slowest, 368.1) |
| W9-1 0108 | 0122-q125-r2 (2.50, 1 s max 6.61; rank 7), 0124-q250-r2 (2.57, 13 bursts; rank 5); no fps effect |
| W5b-1 0155 | 0213-d11t-r3 (3.36; slowest, 371.7), 0209-d11p-r3 (3.07; rank 3) |
| W4c 0239 | 0253-B-r4 (3.09; slowest, 382.0) |
| W6-2 0313 | 0339-p2fc-r4 (2.96, 1 s max 8.17; fps_rel 0.961) |
| W9-2 0401 | 0407-q125-r1 (4.06), 0423-q125-r3 (4.03), 0409-q250-r1 (3.72), 0417-q250-r2 (2.91): the 4 slowest runs of the folder (365.0, 368.4, 378.2, 379.1) |
| W5b-2 0451 | 0453-d11-r1 (3.53; fastest, 393.0), 0455-d11t-r1 (3.37; slowest, 367.1), 0457-d11p-r1 (3.76; rank 17), 0510-d11t-r3 (2.87; rank 4) |

Per arm: arm medians of ng_t are 2.22-2.72, except W9-2 q125 (3.16) and q250 (3.03).
- **W9-2:** all 4 flagged runs are q125 or q250. The arm fps medians are 378.9 (q125) and 382.8 (q250) with them, and 390.2 and 387.8 without them (n 2 each). W9-1 has 389.5 and 389.3. off, q0 and q500 differ between W9-1 and W9-2 by <= 1.5 fps.
- **W5b-2:** d11t is 382.0 with 0455 and 0510, and 385.0 without them (W5b-1: 384.2).
- **Other folders:** dropping the flagged runs moves arm medians by <= 2.5 fps (W6-1 p2fc 466.3 to 468.8).

Spearman ng_t vs fps_rel over scored runs, in time order: -0.75, -0.54, -0.67, -0.36 (ns), -0.50, -0.75, -0.23 (ns). Arm fps with/without flagged runs: scratch_flagfps.py over runs.csv.

**CrossDeviceService holdback before W5b-2.** No sys.csv covers 04:46-04:49: W9-2's last window ended 04:44:02, and W5b-2's cold run started 04:51:59. So the holdback itself is not in the data.
- **Cold run:** normal. Window ng_t 2.55, warm-up 1.94 (W5b-1 cold: 2.39 / 1.93).
- **First scored runs:** about +1 core extra load. ng_t was 3.53, 3.37, 3.76 and 2.84 in runs 2-5 (04:54:46-05:01:48), with warm-ups 2.55-3.80.
- **After that:** back to ~2.5 from 0501 (05:03), apart from three single runs at 2.87-2.90 (0510, 0520, 0524).
- **Rolling median:** the 30 s rolling median of ng_t is above the folder baseline (2.43) + 0.5 in 386 of 2070 samples. The first is at 04:55:02 and most fall in 04:55-05:03 (W5b-1: 30 samples, mostly 0213).
- **Same arm, W5b-2 minus W5b-1 (ng_t median):** d11 -0.03, d11t +0.09, d11p +0.16.

The extra load starts ~6 min after the holdback window, during the first scored run. It cannot be tied to CrossDeviceService or any other process: the matrix folders have no per-process data for non-game processes.

**3. The 45.67 ms frame (0313/0352-p2f-r5).**
- **Where:** window frame #2849 (perf.csv data row 27329, file line 27331). T 7.443-7.489 s from the window start (measure_start 03:53:12.640); estimated wall 03:53:20.06.
- **sys.csv, the sample that contains it (03:53:19.4-20.4):**
  - busy_t 4.83 to 7.40;
  - ng_t 2.13 to 5.08 cores (ng_u 5.50);
  - E util 39.8 to 65.4 %;
  - P 1986 to 1667 MHz, E 2017 to 1781 MHz, cpu perf 121 to 106 %;
  - the next sample is still raised: ng_t 4.69, P/E 1660/1717 MHz.
- **proc.csv:** game cores 2.68 to 2.23; threads 72, handles 1296, commit 1198 MB, free RAM 13.1 GB, responding.
- **gpu.csv:** 832 MHz, 87-88 °C. In the sample 0.58 s after the frame, util drops 100 to 81 % and power 15.7 to 14.74 W.
- **perf.csv counters:** pipeline and texture misses 0.
- **game.log:** no line within 2 s. The nearest is a Toypad write ~8.8 s earlier, before the window.

It is the only frame over 33 ms in W6. All 21 of the run's frames over 6 ms are at T 7.43-8.00 s.

**Frames over 16.7 ms in W6.** In scored runs: 12 frames in 3 runs, all in W6-2.
- 0352-p2f-r5: 9 frames, T 7.44-8.00 s, 19.05-45.67 ms.
- 0325-p2f-r2: 2 frames, T 16.33 s (18.05 ms) and T 28.33 s (16.99 ms).
- 0329-s0-r2: 1 frame, T 28.09 s (17.35 ms).

None in W6-1, in any p2 or p2fc run, or in any cold run. Frames over 16.7 ms / scored frames, pass 1 and pass 2: p2 0/99826 and 0/96223; p2f 0/98748 and 11/96565; p2fc 0/114740 and 0/116549; s0 0/98470 and 1/97681. The 0325 and 0329 frames have no burst in their sample: ng_t 2.91, 3.16 and 2.11, E 1915-2049 MHz.

**4. game.log: Agent 8's zeros confirmed.** All 135 runs have 0 STUCK-LOCK lines (so no owner sites), 0 [error], 0 [critical], 0 hang lines and 0 .dmp files. There are also no WerFault markers, and driver.err is empty. Warnings come in 6 distinct patterns. Five appear in all 135 runs (stubs and missing INSTALL*.DAT/HDR files). The sixth is a single line in W9-1 0128-off-r2 (game.log L100, 01:30:55, at shutdown after the window): "[core] Shutdown wedged past the close request; hard-exiting."

**E1. W6-2 tail episode: 0325-0339 (8 runs) vs the other 12.**
- **Counts:** my counts of frames over 6 ms match Agent 8's (33/40/58/40/34/44/40/34; 0352: 21).
- **What separates the groups:** only the frames. Frames over 6 ms, median 40 vs 3 (perm p 0.001); fps_rel -0.5 % (p 0.005).
- **What does not:** no host-side metric differs.
  - CPU: ng_t 2.56 vs 2.51 (p 0.52), ng_u, burst seconds, warm-up ng_t, P util, P/E MHz, E util.
  - Game process: game cores, threads (72), handles, commit; free RAM 13.07 GB in both groups.
  - GPU: clock 832 MHz in both, temp 87.9 °C in both, power and util, thermal-throttle share 100 % in both.
  - Other: pipeline/texture misses 0, interrupt rate.
- **Per second:** seconds that hold a frame over 6 ms do not carry more non-game CPU. The median difference is +0.07 cores. It is higher in 5 of 8 EP runs (sign p 0.73) and in 11 of all 20 runs (p 0.82); pooled rho 0.105, n 999.
- **Process:** none can be named. proc.csv covers only the game, and there is no per-process or disk data.
- **Battery:** batt_pct reached 100 % at 0325, the first EP run, and stayed there after the episode, so it does not track the episode.

**E2. W4c.**
- **0251-B-r3:** 20 of its 22 frames over 6 ms fall in two 1 s samples, wall 02:53:20-21:
  - T 33.8 s: 5 frames, max 16.51 ms;
  - T 34.8 s: 15 frames, max 20.66 ms.
  - In those samples: ng_t 4.23 and 5.16 (run ~2.2), E util 59-64 %, P 1800/1654 MHz and E 1802/1681 MHz (from ~1950-2070). ng_t stays raised for ~3 s.
  - The next sample shows GPU util 96 % and 14.89 W. The nearest game.log line is a Toypad exchange at T 30.28 s.
- **0253-B-r4:** no single burst, but non-game load is raised across the whole run.
  - ng_t 3.09 (highest of 12); E util 47.8 vs 41.7 %; P/E 1823/1837 MHz (lowest of 12); 21 burst seconds.
  - It is largest in 0-30 s: ng_t 3.30-3.65 per 10 s bin, E 1750-1828 MHz.
  - Its frames over 6 ms are spread over all bins, and its GPU looks like the other runs. It is the slowest W4c run (382.0).

**E3. W6-1 bursts.**
- **0023-p2fc-r2:** 28 of its 31 frames in 0-10 s are in the first two samples (T 0.8 s: 18, T 1.8 s: 10).
  - In those two samples: ng_t 9.38 and 7.17, P 1351-1461 MHz, E 1490-1507 MHz, P util 79.6 %, E util 89 %.
  - ng_t stays ~4.5-5.8 to T 12 s (run mean 3.95, flagged). GPU util is 57-77 % in 0-10 s.
- **0039-p2-r4:** all 17 frames are at T 15.8-19.8 s.
  - ng_t is 3.56-5.56 at T 15.8-21.8 s (from ~2.2), E ~1590-1660 MHz, GPU util 89-93 %. No log lines.
- **0031-s0-r3 and 0037-s0-r4:** frames are spread over the run with no host signal. Hot-bin ng_t is 2.57 vs 2.59 and 2.36 vs 2.59, and clocks and GPU are unchanged.

**E4. 0352, first 10 s.**
- All 21 frames over 6 ms are at T 7.43-8.00 s.
- The 1 s samples ending at T 7.8, 8.8 and 9.8 s show a non-game burst: ng_t 5.08, 4.69 and 3.90 (2.0-2.5 before), E util 65 %, P 1667 / E 1781 MHz.
- GPU util is 81 % at 14.74 W in the T 8.8 s sample.
- The only nearby game.log line is a Toypad exchange at T -1.36 s.

**Common pattern.** Clustered tails (0352, 0251-B-r3, the start of 0023, 0039) coincide with 1-3 s non-game CPU bursts of +1.4 to +7 cores. P/E clocks drop by ~200-400 MHz, and a GPU util/power dip follows in the next sample. Spread tails (the W6-2 EP runs, 0031, 0037) show no host signal in the available data.

**E5. Idle gate and first runs.**
- **No pre-run data:** there is no gate log in the matrix folders, and the sys sampler starts with the game, so no idle samples exist before a run. The gap before the cold run was 356 s (0239) and 449 s (0313); runs are 9 s apart.
- **CPU clocks:**
  - Cold-run warm-ups run at full turbo: P/E 3301/2980 MHz (0009), 3139/2857 (0239), 3324/3043 (0313).
  - Clocks are back to ~1.8-2.06 GHz in the cold window.
  - Scored warm-ups and windows run at ~1.9-2.1 GHz, with no extra clock in the first runs.
- **GPU clocks:**
  - The first scored runs run above the steady clock: 1257/1134/1013 MHz (0010/0012/0014), 1021/855 (0241/0243), 1069/884 (0315/0317).
  - Later runs sit at 832 MHz.
  - Throttle reason 0x20 is set in 100 % of GPU samples of all scored runs.
  - GPU temp at the window start (mean of the first 5 gpu.csv samples, median per group) is 86.2-86.8 °C in runs 2-3 vs 87.0-87.7 °C in the rest.
- **fps_rel:**
  - Cold runs 1.04-1.17.
  - Runs 2-3, median: 1.152 (0009), 1.110 (0108), 1.069 (0155), 1.053 (0239), 1.054 (0313), 1.032 (0401), 0.991 (0451).
  - The rest 1.000.
- **Spearman GPU MHz vs fps_rel:** 0.53, 0.70, 0.65, 0.65, 0.52 (p <= 0.021) in the first five folders; 0.03 and -0.01 (ns) in W9-2 and W5b-2. In those two folders the early runs carry extra non-game load:
  - W5b-2 runs 2-3 (0453, 0455) have ng_t 3.53 and 3.37;
  - in W9-2, run 2 (0403-off-r1, 408.9 fps, rel 1.062) is fast and run 3 (0405-q0-r1, ng_t 2.67) is not, and runs 4-5 (0407, 0409) are flagged.
- **Reading:** the fast first runs follow GPU clock headroom before the MX570 heat-soaks to its thermal-limited 832 MHz. CPU clocks do not explain them. Caveat: p2fc runs (~470 fps) run at ~88 % GPU util, so they are less GPU-bound.

**Data limits.**
- No per-process data for non-game processes (proc.csv is the game only).
- No disk counters.
- No CPU temperature (thermal zone no_data).
- gpu.csv has no rows for cold runs.
- No quiet-gate log in the matrix folders.

## Method

- 1 s sys.csv samples, interval (previous epoch, epoch]; phase by the sample midpoint: window = run.json measure_start..measure_end, warm-up = first frame..measure_start.
- busy_t (time based, logical CPUs of 12) = 4*min(1, p_util/100*1700/p_eff) + 8*min(1, e_util/100*f_E/e_eff), f_E = 1.5*base_mhz - 850 (from 12*base = 4*1700 + 8*f_E). util_LP (utility units) = 4*p_util/100 + 8*e_util/100. game = slope of proc.csv cpu_s over the same interval. **ng_t = busy_t - game** (non-game CPU occupancy, cores), **ng_u = util_LP - game** (utility based, Agent 1 style).
- With P and E clocks at ~1.96-1.98 GHz (above the 1.7 GHz nominal), utility over-counts busy time by eff/nominal, so ng_u reads ~1 core above ng_t here; ng_t is the occupancy number. No run of these folders had the slow state (E < 800 MHz), so neither measure is clock-distorted the way W4b/W5 were.
- "non-game" includes everything outside legodimensions.exe: the run harness samplers (sys-csv, thread-cpu driver with NVML, proc sampler), dwm, the GPU driver/kernel (DPC/ISR), Defender and other services. There is no per-process data for non-game processes in the matrix folders.
- Flag rule per folder (scored runs): value above the max of the other scored runs AND robust z = (v - median_rest)/(1.4826*MAD_rest) >= 3 AND v - median_rest >= 0.2 cores (means) / 0.5 cores (1 s max); bursts: 1 s window samples above the folder-pooled p90 of ng_t (expected ~5 of 50), flagged at >= 12; any power/overlay/AC/input/fg/desktop change in the window.

## 1. Slow state (bench/agent11/timerq_slowstate_3mode.ps1, E < 800 MHz for 3+ samples after the first frame)

| window | folder | arm | mode | runs | slow runs | onset_s (run:onset) | mean slow_pct | max slow_pct | ms1 lines | flags |
|---|---|---|---|---|---|---|---|---|---|---|
| W6-1 | 0009 | cold-s0 | spin | 1 | 0 | - | 0.0 | 0.0 | 0 | - |
| W6-1 | 0009 | s0 | spin | 5 | 0 | - | 0.0 | 0.0 | 0 | - |
| W6-1 | 0009 | p2 | spin | 5 | 0 | - | 0.0 | 0.0 | 0 | - |
| W6-1 | 0009 | p2f | spin | 5 | 0 | - | 0.0 | 0.0 | 0 | - |
| W6-1 | 0009 | p2fc | spin | 5 | 0 | - | 0.0 | 0.0 | 0 | - |
| W9-1 | 0108 | cold-off | spin | 1 | 0 | - | 0.0 | 0.0 | 0 | - |
| W9-1 | 0108 | off | spin | 4 | 0 | - | 0.0 | 0.0 | 0 | - |
| W9-1 | 0108 | q0 | spin | 4 | 0 | - | 0.0 | 0.0 | 0 | - |
| W9-1 | 0108 | q125 | spin | 4 | 0 | - | 0.0 | 0.0 | 0 | - |
| W9-1 | 0108 | q250 | spin | 4 | 0 | - | 0.0 | 0.0 | 0 | - |
| W9-1 | 0108 | q500 | spin | 4 | 0 | - | 0.0 | 0.0 | 0 | - |
| W5b-1 | 0155 | cold-d11 | spin | 1 | 0 | - | 0.0 | 0.0 | 1 | - |
| W5b-1 | 0155 | d11 | spin | 6 | 0 | - | 0.0 | 0.0 | 1 | - |
| W5b-1 | 0155 | d11t | blocking | 6 | 0 | - | 0.0 | 0.0 | 1 | - |
| W5b-1 | 0155 | d11p | precise | 6 | 0 | - | 0.0 | 0.0 | 1 | - |
| W4c | 0239 | cold-d0 | spin | 1 | 0 | - | 0.0 | 0.0 | 0 | - |
| W4c | 0239 | d0 | spin | 6 | 0 | - | 0.0 | 0.0 | 0 | - |
| W4c | 0239 | B | spin | 6 | 0 | - | 0.0 | 0.0 | 0 | - |
| W6-2 | 0313 | cold-s0 | spin | 1 | 0 | - | 0.0 | 0.0 | 0 | - |
| W6-2 | 0313 | s0 | spin | 5 | 0 | - | 0.0 | 0.0 | 0 | - |
| W6-2 | 0313 | p2 | spin | 5 | 0 | - | 0.0 | 0.0 | 0 | - |
| W6-2 | 0313 | p2f | spin | 5 | 0 | - | 0.0 | 0.0 | 0 | - |
| W6-2 | 0313 | p2fc | spin | 5 | 0 | - | 0.0 | 0.0 | 0 | - |
| W9-2 | 0401 | cold-off | spin | 1 | 0 | - | 0.0 | 0.0 | 0 | - |
| W9-2 | 0401 | off | spin | 4 | 0 | - | 0.0 | 0.0 | 0 | - |
| W9-2 | 0401 | q0 | spin | 4 | 0 | - | 0.0 | 0.0 | 0 | - |
| W9-2 | 0401 | q125 | spin | 4 | 0 | - | 0.0 | 0.0 | 0 | - |
| W9-2 | 0401 | q250 | spin | 4 | 0 | - | 0.0 | 0.0 | 0 | - |
| W9-2 | 0401 | q500 | spin | 4 | 0 | - | 0.0 | 0.0 | 0 | - |
| W5b-2 | 0451 | cold-d11 | spin | 1 | 0 | - | 0.0 | 0.0 | 1 | - |
| W5b-2 | 0451 | d11 | spin | 6 | 0 | - | 0.0 | 0.0 | 1 | - |
| W5b-2 | 0451 | d11t | blocking | 6 | 0 | - | 0.0 | 0.0 | 1 | - |
| W5b-2 | 0451 | d11p | precise | 6 | 0 | - | 0.0 | 0.0 | 1 | - |

Cross-check from sys.csv (all runs, window + warm-up samples, n=14710): e_eff min 1378 MHz, samples with E < 800 MHz: 0; p_eff min 1232 MHz; overlay values best_performance; scheme values Balanced.
timerq3 .txt files are the script's console tables (PowerShell `>` = UTF-16); the .csv files hold the same rows.

## 2. sys.csv disturbance audit (scored window, 50 s; cold runs shown unscored, 30 s)

Busy-share check (model B, window + warm-up samples): busy_P raw > 1.02 in 0.0 % (max 1.076), busy_E raw > 1.02 in 0.0 % (max 1.000); base_mhz 1568-1700; Bbase fallback samples 0. A busy share above 1 would mean the formula over-counts; values stay <= ~1, so the time-based reading holds.

### W6-1 (20261123-0009): 21 runs, 20 scored; folder-pooled ng_t p90 3.57, ng_u p90 4.32

| # | run | win wall | fps | game | ng_t mean | ng_t max | ng_u mean | ng_u max | z_t | z_u | z_t arm | bursts t/u | P util % | E MHz (min) | fg % | idle min s | change in window | change in run | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0009-cold-s0 (unscored) | 00:10:07-00:10:37 | 399.4 | 2.52 | 3.81 | 9.07 | 4.25 | 7.78 | - | - | - | - | 64.6 | 1841 (1558) | 100 | 1368 | none | none | - |
| 2 | 0010-s0-r1 | 00:11:50-00:12:40 | 446.1 | 2.43 | 2.53 | 4.30 | 3.48 | 4.72 | 0.3 | 0.8 | -0.4 | 2/3 | 64.3 | 2006 (1771) | 100 | 1471 | none | none | - |
| 3 | 0012-p2-r1 | 00:13:53-00:14:43 | 441.7 | 2.47 | 2.42 | 3.78 | 3.39 | 4.69 | -1.0 | -0.3 | -1.5 | 1/2 | 66.4 | 2021 (1841) | 100 | 1595 | none | none | - |
| 4 | 0014-p2f-r1 | 00:15:57-00:16:47 | 425.7 | 2.55 | 2.45 | 3.43 | 3.36 | 4.03 | -0.7 | -0.7 | -0.5 | 0/0 | 65.3 | 1986 (1859) | 100 | 1718 | none | none | - |
| 5 | 0016-p2fc-r1 | 00:18:00-00:18:50 | 473.1 | 2.32 | 2.25 | 3.57 | 3.43 | 4.63 | -2.8 | 0.3 | -1.5 | 1/1 | 67.0 | 2112 (1930) | 100 | 1842 | none | none | - |
| 6 | 0019-p2-r2 | 00:20:04-00:20:54 | 402.3 | 2.49 | 2.46 | 4.86 | 3.39 | 5.51 | -0.6 | -0.3 | -0.7 | 2/2 | 63.9 | 2005 (1863) | 100 | 1965 | none | none | - |
| 7 | 0021-p2f-r2 | 00:22:07-00:22:57 | 387.8 | 2.59 | 2.46 | 4.64 | 3.33 | 4.73 | -0.6 | -1.0 | -0.4 | 1/1 | 62.8 | 1983 (1696) | 100 | 2089 | none | none | - |
| 8 | 0023-p2fc-r2 | 00:24:11-00:25:01 | 426.9 | 2.21 | 3.95 | 9.38 | 4.64 | 8.05 | 16.1 | 13.8 | 11.3 | 26/30 | 63.4 | 1852 (1490) | 100 | 2212 | none | none | FLAG: ngU_mean 4.64 > rest max 4.38 (rest med 3.40, z 13.8) | ngB_max 9.38 > rest max 6.68 (rest med 4.30, z 8.3) | ngU_max 8.05 > rest max 6.45 (rest med 4.87, z 6.6) | ng_t bursts 26/50 > folder p90 3.57 |
| 9 | 0025-s0-r2 | 00:26:14-00:27:04 | 368.1 | 2.58 | 4.09 | 6.68 | 4.38 | 6.45 | 17.7 | 10.9 | 36.9 | 28/24 | 62.9 | 1778 (1540) | 100 | 2336 | none | none | FLAG: ngB_mean 4.09 > rest max 3.95 (rest med 2.50, z 17.7) | ng_t bursts 28/50 > folder p90 3.57 |
| 10 | 0027-p2f-r3 | 00:28:18-00:29:08 | 387.7 | 2.52 | 2.40 | 3.75 | 3.34 | 4.70 | -1.2 | -1.0 | -1.7 | 1/2 | 64.1 | 2012 (1773) | 100 | 2459 | none | none | - |
| 11 | 0029-p2fc-r3 | 00:30:21-00:31:11 | 466.3 | 2.24 | 2.44 | 4.63 | 3.55 | 5.19 | -0.9 | 1.7 | -0.3 | 3/4 | 65.6 | 2084 (1827) | 100 | 2583 | none | none | - |
| 12 | 0031-s0-r3 | 00:32:25-00:33:15 | 384.9 | 2.49 | 2.59 | 5.18 | 3.46 | 5.13 | 1.0 | 0.6 | 1.0 | 2/2 | 65.6 | 1978 (1708) | 100 | 2706 | none | none | - |
| 13 | 0033-p2-r3 | 00:34:28-00:35:18 | 385.0 | 2.60 | 2.50 | 4.26 | 3.32 | 4.54 | -0.3 | -1.2 | -0.1 | 5/3 | 63.3 | 1958 (1713) | 100 | 2830 | none | none | - |
| 14 | 0035-p2fc-r4 | 00:36:32-00:37:22 | 471.2 | 2.33 | 2.38 | 3.97 | 3.47 | 5.01 | -1.5 | 0.8 | -0.5 | 1/3 | 64.2 | 2075 (1878) | 100 | 2954 | none | none | - |
| 15 | 0037-s0-r4 | 00:38:36-00:39:26 | 385.2 | 2.53 | 2.54 | 4.01 | 3.42 | 4.19 | 0.4 | 0.2 | -0.2 | 1/0 | 67.5 | 1978 (1741) | 100 | 3077 | none | none | - |
| 16 | 0039-p2-r4 | 00:40:39-00:41:29 | 381.9 | 2.52 | 2.87 | 5.56 | 3.59 | 5.31 | 4.2 | 2.1 | 7.2 | 9/7 | 63.8 | 1926 (1587) | 100 | 3201 | none | none | - |
| 17 | 0041-p2f-r4 | 00:42:43-00:43:33 | 386.8 | 2.55 | 2.57 | 4.22 | 3.39 | 4.54 | 0.8 | -0.3 | 2.6 | 2/2 | 64.1 | 1967 (1740) | 100 | 3324 | none | none | - |
| 18 | 0043-s0-r5 | 00:44:46-00:45:36 | 385.2 | 2.50 | 2.47 | 4.71 | 3.36 | 5.34 | -0.5 | -0.7 | -2.1 | 2/2 | 63.8 | 1986 (1800) | 100 | 3448 | none | none | - |
| 19 | 0045-p2-r5 | 00:46:50-00:47:40 | 385.6 | 2.51 | 2.55 | 4.39 | 3.40 | 4.87 | 0.5 | -0.2 | 1.3 | 4/2 | 62.9 | 1984 (1730) | 100 | 3571 | none | none | - |
| 20 | 0047-p2f-r5 | 00:48:53-00:49:43 | 386.8 | 2.56 | 2.52 | 4.22 | 3.37 | 4.95 | 0.3 | -0.5 | 1.6 | 3/2 | 62.7 | 1972 (1840) | 100 | 3695 | none | none | - |
| 21 | 0049-p2fc-r5 | 00:50:57-00:51:47 | 457.2 | 2.28 | 2.64 | 5.27 | 3.70 | 5.66 | 1.6 | 3.4 | 1.7 | 5/8 | 65.7 | 2045 (1704) | 100 | 3819 | none | none | - |

Folder: ng_t mean median 2.51 [2.25..4.09], ng_u mean median 3.41 [3.32..4.64], game median 2.50 cores, P util median 64.1 %, E MHz median 1985 (min 1490). Spearman (scored runs): ng_t mean vs fps_rel rho -0.75 (n=20, p=0.000); ng_u mean vs fps_rel rho -0.39 (p=0.095); run order vs ng_t mean rho 0.39 (p=0.094).
Flagged: 0023-p2fc-r2: ngU_mean 4.64 > rest max 4.38 (rest med 3.40, z 13.8) | ngB_max 9.38 > rest max 6.68 (rest med 4.30, z 8.3) | ngU_max 8.05 > rest max 6.45 (rest med 4.87, z 6.6) | ng_t bursts 26/50 > folder p90 3.57; 0025-s0-r2: ngB_mean 4.09 > rest max 3.95 (rest med 2.50, z 17.7) | ng_t bursts 28/50 > folder p90 3.57

### W9-1 (20261123-0108): 21 runs, 20 scored; folder-pooled ng_t p90 3.05, ng_u p90 4.06

| # | run | win wall | fps | game | ng_t mean | ng_t max | ng_u mean | ng_u max | z_t | z_u | z_t arm | bursts t/u | P util % | E MHz (min) | fg % | idle min s | change in window | change in run | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0108-cold-off (unscored) | 01:09:57-01:10:27 | 438.5 | 2.34 | 2.09 | 4.31 | 3.87 | 5.41 | - | - | - | - | 76.1 | 2370 (1790) | 100 | 4959 | none | none | - |
| 2 | 0110-off-r1 | 01:11:39-01:12:29 | 443.7 | 2.51 | 2.45 | 3.61 | 3.37 | 4.61 | 0.4 | -0.7 | -7.6 | 6/3 | 64.2 | 2004 (1788) | 100 | 5061 | none | none | - |
| 3 | 0112-q0-r1 | 01:13:42-01:14:32 | 414.6 | 2.50 | 2.46 | 4.10 | 3.53 | 4.97 | 0.4 | 1.0 | -0.4 | 5/4 | 67.2 | 2040 (1813) | 100 | 5183 | none | none | - |
| 4 | 0114-q125-r1 | 01:15:44-01:16:34 | 395.5 | 1.82 | 2.22 | 3.88 | 3.41 | 4.56 | -0.7 | -0.3 | -0.8 | 3/3 | 63.3 | 2167 (1819) | 100 | 5306 | none | none | - |
| 5 | 0116-q250-r1 | 01:17:46-01:18:36 | 389.9 | 1.71 | 2.18 | 4.20 | 3.42 | 5.28 | -0.8 | -0.2 | -8.2 | 1/2 | 62.9 | 2178 (1815) | 100 | 5428 | none | none | - |
| 6 | 0118-q500-r1 | 01:19:48-01:20:38 | 390.7 | 1.70 | 2.16 | 3.33 | 3.42 | 4.66 | -0.9 | -0.2 | -2.7 | 1/3 | 62.3 | 2208 (2000) | 100 | 5550 | none | none | - |
| 7 | 0120-q0-r2 | 01:21:51-01:22:41 | 388.5 | 2.49 | 2.37 | 3.87 | 3.48 | 4.57 | 0.0 | 0.5 | -1.2 | 4/3 | 65.0 | 2067 (1846) | 100 | 5673 | none | none | - |
| 8 | 0122-q125-r2 | 01:23:53-01:24:43 | 387.8 | 1.89 | 2.50 | 6.61 | 3.59 | 6.33 | 0.5 | 1.6 | 7.9 | 9/12 | 63.0 | 2092 (1676) | 100 | 5795 | none | none | FLAG: ngB_max 6.61 > rest max 6.10 (rest med 4.12, z 6.8) |
| 9 | 0124-q250-r2 | 01:25:56-01:26:46 | 386.1 | 1.91 | 2.57 | 6.08 | 3.59 | 5.81 | 0.9 | 1.6 | 27.7 | 13/12 | 61.7 | 2078 (1618) | 100 | 5918 | none | none | FLAG: ng_t bursts 13/50 > folder p90 3.05 |
| 10 | 0126-q500-r2 | 01:27:58-01:28:48 | 390.1 | 1.70 | 2.23 | 4.17 | 3.44 | 5.21 | -0.6 | 0.1 | 0.5 | 2/5 | 61.7 | 2180 (1817) | 100 | 6040 | none | none | - |
| 11 | 0128-off-r2 | 01:30:01-01:30:51 | 385.8 | 2.52 | 2.55 | 3.93 | 3.36 | 4.35 | 0.9 | -0.8 | 2.2 | 6/4 | 62.5 | 1959 (1677) | 100 | 6162 | none | none | - |
| 12 | 0131-q125-r3 | 01:32:06-01:32:56 | 389.6 | 1.73 | 2.20 | 4.90 | 3.37 | 5.68 | -0.8 | -0.7 | -0.9 | 1/3 | 62.0 | 2154 (1812) | 100 | 6288 | none | none | - |
| 13 | 0133-q250-r3 | 01:34:08-01:34:58 | 389.7 | 1.73 | 2.26 | 3.45 | 3.45 | 4.85 | -0.5 | 0.2 | -0.1 | 1/4 | 63.3 | 2151 (1877) | 100 | 6410 | none | none | - |
| 14 | 0135-q500-r3 | 01:36:11-01:37:01 | 389.4 | 1.73 | 2.25 | 4.19 | 3.45 | 5.23 | -0.6 | 0.2 | 1.1 | 4/4 | 60.8 | 2164 (1859) | 100 | 6533 | none | none | - |
| 15 | 0137-off-r3 | 01:38:13-01:39:03 | 383.1 | 2.52 | 2.54 | 5.39 | 3.36 | 5.69 | 0.8 | -0.8 | 0.2 | 7/4 | 62.7 | 1974 (1726) | 100 | 6655 | none | none | - |
| 16 | 0139-q0-r3 | 01:40:16-01:41:06 | 382.0 | 2.49 | 2.77 | 6.10 | 3.70 | 5.63 | 1.8 | 2.8 | 2.4 | 11/11 | 65.1 | 2001 (1553) | 100 | 6778 | none | none | - |
| 17 | 0141-q250-r4 | 01:42:19-01:43:09 | 389.0 | 1.73 | 2.27 | 4.25 | 3.43 | 5.40 | -0.4 | -0.1 | 0.1 | 4/3 | 61.6 | 2142 (1805) | 100 | 6901 | none | none | - |
| 18 | 0143-q500-r4 | 01:44:21-01:45:11 | 390.1 | 1.73 | 2.20 | 3.78 | 3.43 | 5.17 | -0.8 | -0.1 | -1.2 | 2/4 | 61.1 | 2186 (1942) | 100 | 7023 | none | none | - |
| 19 | 0145-off-r4 | 01:46:24-01:47:14 | 386.6 | 2.50 | 2.53 | 3.98 | 3.36 | 4.50 | 0.7 | -0.8 | -0.3 | 3/2 | 62.6 | 1967 (1738) | 100 | 7145 | none | none | - |
| 20 | 0147-q0-r4 | 01:48:26-01:49:16 | 385.5 | 2.48 | 2.58 | 4.43 | 3.62 | 5.02 | 1.0 | 1.9 | 0.9 | 10/8 | 64.5 | 2039 (1776) | 100 | 7268 | none | none | - |
| 21 | 0149-q125-r4 | 01:50:29-01:51:19 | 389.4 | 1.86 | 2.37 | 4.12 | 3.51 | 5.28 | -0.0 | 0.8 | 4.2 | 6/6 | 63.4 | 2125 (1871) | 100 | 7390 | none | none | - |

Folder: ng_t mean median 2.37 [2.16..2.77], ng_u mean median 3.44 [3.36..3.70], game median 1.87 cores, P util median 62.8 %, E MHz median 2108 (min 1553). Spearman (scored runs): ng_t mean vs fps_rel rho -0.54 (n=20, p=0.013); ng_u mean vs fps_rel rho -0.35 (p=0.135); run order vs ng_t mean rho 0.27 (p=0.244).
Flagged: 0122-q125-r2: ngB_max 6.61 > rest max 6.10 (rest med 4.12, z 6.8); 0124-q250-r2: ng_t bursts 13/50 > folder p90 3.05

### W5b-1 (20261123-0155): 19 runs, 18 scored; folder-pooled ng_t p90 3.35, ng_u p90 3.96

| # | run | win wall | fps | game | ng_t mean | ng_t max | ng_u mean | ng_u max | z_t | z_u | z_t arm | bursts t/u | P util % | E MHz (min) | fg % | idle min s | change in window | change in run | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0155-cold-d11 (unscored) | 01:56:33-01:57:03 | 419.0 | 2.55 | 2.39 | 3.64 | 3.36 | 4.85 | - | - | - | - | 66.1 | 2012 (1849) | 100 | 7755 | none | none | - |
| 2 | 0157-d11-r1 | 01:58:15-01:59:05 | 415.1 | 2.46 | 2.46 | 4.12 | 3.36 | 4.89 | -2.3 | 0.2 | -6.4 | 2/4 | 63.2 | 1995 (1774) | 100 | 7856 | none | none | - |
| 3 | 0159-d11t-r1 | 02:00:18-02:01:08 | 407.0 | 2.29 | 2.59 | 3.96 | 3.40 | 4.66 | 0.3 | 0.9 | 0.1 | 6/6 | 61.5 | 1961 (1746) | 100 | 7979 | none | none | - |
| 4 | 0201-d11p-r1 | 02:02:20-02:03:10 | 395.9 | 2.32 | 2.45 | 4.19 | 3.23 | 4.84 | -2.7 | -2.0 | -3.2 | 1/1 | 60.9 | 1955 (1829) | 100 | 8102 | none | none | - |
| 5 | 0203-d11t-r2 | 02:04:23-02:05:13 | 385.7 | 2.29 | 2.36 | 4.50 | 3.21 | 5.10 | -5.0 | -2.4 | -1.7 | 1/1 | 61.6 | 1984 (1853) | 100 | 8225 | none | none | - |
| 6 | 0205-d11p-r2 | 02:06:25-02:07:15 | 384.9 | 2.38 | 2.58 | 4.71 | 3.30 | 5.02 | 0.3 | -0.8 | 0.3 | 5/5 | 61.8 | 1926 (1776) | 100 | 8347 | none | none | - |
| 7 | 0207-d11-r2 | 02:08:28-02:09:18 | 384.0 | 2.53 | 2.66 | 5.45 | 3.45 | 5.34 | 2.5 | 1.9 | 16.5 | 6/6 | 62.0 | 1962 (1651) | 100 | 8470 | none | none | - |
| 8 | 0209-d11p-r3 | 02:10:30-02:11:20 | 381.8 | 2.37 | 3.07 | 5.76 | 3.59 | 5.28 | 12.2 | 4.3 | 13.0 | 15/13 | 59.2 | 1861 (1562) | 100 | 8592 | none | none | FLAG: ng_t bursts 15/50 > folder p90 3.35 |
| 9 | 0211-d11-r3 | 02:12:33-02:13:23 | 381.5 | 2.59 | 2.57 | 6.20 | 3.36 | 5.67 | 0.1 | 0.2 | 3.6 | 5/5 | 62.6 | 1957 (1629) | 100 | 8715 | none | none | - |
| 10 | 0213-d11t-r3 | 02:14:35-02:15:25 | 371.7 | 2.39 | 3.36 | 8.04 | 3.81 | 7.72 | 19.2 | 8.3 | 8.5 | 17/15 | 60.3 | 1838 (1446) | 100 | 8837 | none | none | FLAG: ngB_mean 3.36 > rest max 3.07 (rest med 2.56, z 19.2) | ngU_mean 3.81 > rest max 3.59 (rest med 3.34, z 8.3) | ngB_max 8.04 > rest max 6.20 (rest med 4.50, z 4.2) | ngU_max 7.72 > rest max 6.17 (rest med 4.98, z 6.1) | ng_t bursts 17/50 > folder p90 3.35 |
| 11 | 0215-d11-r4 | 02:16:38-02:17:28 | 384.2 | 2.58 | 2.53 | 4.18 | 3.34 | 4.46 | -0.3 | 0.0 | -0.2 | 5/4 | 64.2 | 1949 (1682) | 100 | 8960 | none | none | - |
| 12 | 0217-d11t-r4 | 02:18:40-02:19:30 | 383.3 | 2.29 | 2.76 | 5.23 | 3.50 | 5.82 | 4.8 | 2.7 | 2.1 | 9/9 | 60.6 | 1930 (1765) | 100 | 9082 | none | none | - |
| 13 | 0219-d11p-r4 | 02:20:43-02:21:33 | 384.8 | 2.33 | 2.56 | 3.93 | 3.32 | 4.51 | 0.0 | -0.4 | 0.0 | 3/4 | 62.5 | 1948 (1743) | 100 | 9205 | none | none | - |
| 14 | 0221-d11t-r5 | 02:22:47-02:23:37 | 382.4 | 2.31 | 2.56 | 5.95 | 3.33 | 6.17 | -0.0 | -0.2 | -0.1 | 5/5 | 61.5 | 1955 (1656) | 100 | 9328 | none | none | - |
| 15 | 0223-d11p-r5 | 02:24:49-02:25:39 | 385.1 | 2.32 | 2.49 | 5.12 | 3.25 | 4.98 | -1.7 | -1.7 | -1.9 | 1/2 | 62.1 | 1955 (1661) | 100 | 9451 | none | none | - |
| 16 | 0225-d11-r5 | 02:26:52-02:27:42 | 385.1 | 2.54 | 2.54 | 4.20 | 3.35 | 4.74 | -0.2 | 0.1 | -0.1 | 2/2 | 63.4 | 1952 (1813) | 100 | 9574 | none | none | - |
| 17 | 0227-d11p-r6 | 02:28:54-02:29:44 | 386.2 | 2.29 | 2.56 | 4.84 | 3.31 | 5.18 | 0.0 | -0.5 | -0.0 | 2/2 | 61.1 | 1946 (1790) | 100 | 9696 | none | none | - |
| 18 | 0229-d11-r6 | 02:30:57-02:31:47 | 385.7 | 2.54 | 2.54 | 3.32 | 3.34 | 4.05 | -0.2 | -0.0 | 0.1 | 0/3 | 63.2 | 1959 (1784) | 100 | 9818 | none | none | - |
| 19 | 0231-d11t-r6 | 02:32:59-02:33:49 | 385.1 | 2.29 | 2.49 | 3.89 | 3.31 | 4.68 | -1.6 | -0.6 | -0.4 | 4/3 | 61.1 | 1972 (1758) | 100 | 9941 | none | none | - |

Folder: ng_t mean median 2.56 [2.36..3.36], ng_u mean median 3.34 [3.21..3.81], game median 2.35 cores, P util median 61.7 %, E MHz median 1955 (min 1446). Spearman (scored runs): ng_t mean vs fps_rel rho -0.67 (n=18, p=0.004); ng_u mean vs fps_rel rho -0.53 (p=0.026); run order vs ng_t mean rho -0.04 (p=0.872).
Flagged: 0209-d11p-r3: ng_t bursts 15/50 > folder p90 3.35; 0213-d11t-r3: ngB_mean 3.36 > rest max 3.07 (rest med 2.56, z 19.2) | ngU_mean 3.81 > rest max 3.59 (rest med 3.34, z 8.3) | ngB_max 8.04 > rest max 6.20 (rest med 4.50, z 4.2) | ngU_max 7.72 > rest max 6.17 (rest med 4.98, z 6.1) | ng_t bursts 17/50 > folder p90 3.35

### W4c (20261123-0239): 13 runs, 12 scored; folder-pooled ng_t p90 3.28, ng_u p90 3.89

| # | run | win wall | fps | game | ng_t mean | ng_t max | ng_u mean | ng_u max | z_t | z_u | z_t arm | bursts t/u | P util % | E MHz (min) | fg % | idle min s | change in window | change in run | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0239-cold-d0 (unscored) | 02:40:51-02:41:21 | 426.5 | 2.49 | 2.94 | 5.40 | 3.66 | 5.25 | - | - | - | - | 64.4 | 1921 (1649) | 100 | 10412 | none | none | - |
| 2 | 0241-d0-r1 | 02:42:32-02:43:22 | 421.8 | 2.52 | 2.47 | 4.04 | 3.36 | 4.76 | -0.4 | 0.7 | 0.5 | 2/5 | 63.7 | 1988 (1779) | 100 | 10514 | none | none | - |
| 3 | 0243-B-r1 | 02:44:35-02:45:25 | 388.5 | 2.55 | 2.52 | 4.29 | 3.36 | 5.04 | 0.5 | 0.8 | -1.2 | 3/2 | 64.7 | 1980 (1798) | 100 | 10637 | none | none | - |
| 4 | 0245-B-r2 | 02:46:38-02:47:28 | 383.9 | 2.56 | 2.58 | 4.90 | 3.39 | 5.47 | 1.7 | 1.7 | 0.3 | 5/6 | 64.5 | 1958 (1647) | 100 | 10759 | none | none | - |
| 5 | 0247-d0-r2 | 02:48:40-02:49:30 | 385.0 | 2.53 | 2.44 | 4.14 | 3.31 | 4.38 | -0.8 | -1.0 | -1.2 | 4/5 | 62.7 | 1979 (1780) | 100 | 10882 | none | none | - |
| 6 | 0249-d0-r3 | 02:50:43-02:51:33 | 386.4 | 2.51 | 2.48 | 4.08 | 3.36 | 4.71 | -0.3 | 0.6 | 1.0 | 3/6 | 64.9 | 1979 (1822) | 100 | 11004 | none | none | - |
| 7 | 0251-B-r3 | 02:52:46-02:53:36 | 383.4 | 2.60 | 2.56 | 5.16 | 3.32 | 5.19 | 1.4 | -0.6 | -0.2 | 7/6 | 63.9 | 1937 (1638) | 100 | 11127 | none | none | - |
| 8 | 0253-B-r4 | 02:54:48-02:55:38 | 382.0 | 2.70 | 3.09 | 5.28 | 3.61 | 5.39 | 10.6 | 7.3 | 7.6 | 21/12 | 62.1 | 1837 (1634) | 100 | 11250 | none | none | FLAG: ngB_mean 3.09 > rest max 2.62 (rest med 2.48, z 10.6) | ngU_mean 3.61 > rest max 3.41 (rest med 3.33, z 7.3) | ngB_max 5.28 > rest max 5.16 (rest med 4.14, z 4.9) | ng_t bursts 21/50 > folder p90 3.28 |
| 9 | 0255-d0-r4 | 02:56:51-02:57:41 | 385.0 | 2.54 | 2.45 | 3.90 | 3.31 | 4.35 | -0.7 | -0.9 | -0.4 | 2/4 | 62.8 | 1977 (1821) | 100 | 11373 | none | none | - |
| 10 | 0257-d0-r5 | 02:58:53-02:59:43 | 385.1 | 2.59 | 2.52 | 3.98 | 3.33 | 4.46 | 0.6 | -0.5 | 2.3 | 3/3 | 62.6 | 1957 (1767) | 100 | 11495 | none | none | - |
| 11 | 0259-B-r5 | 03:00:56-03:01:46 | 383.9 | 2.57 | 2.62 | 5.13 | 3.41 | 5.13 | 2.4 | 2.0 | 0.9 | 5/6 | 63.9 | 1947 (1679) | 100 | 11618 | none | none | - |
| 12 | 0301-B-r6 | 03:02:59-03:03:49 | 385.9 | 2.61 | 2.45 | 4.30 | 3.26 | 4.92 | -0.7 | -1.9 | -2.3 | 3/3 | 62.7 | 1966 (1782) | 100 | 11741 | none | none | - |
| 13 | 0303-d0-r6 | 03:05:03-03:05:53 | 385.6 | 2.50 | 2.43 | 4.13 | 3.33 | 4.60 | -1.0 | -0.4 | -1.6 | 2/2 | 64.6 | 2000 (1789) | 100 | 11865 | none | none | - |

Folder: ng_t mean median 2.50 [2.43..3.09], ng_u mean median 3.34 [3.26..3.61], game median 2.55 cores, P util median 63.8 %, E MHz median 1972 (min 1634). Spearman (scored runs): ng_t mean vs fps_rel rho -0.36 (n=12, p=0.249); ng_u mean vs fps_rel rho 0.05 (p=0.886); run order vs ng_t mean rho -0.16 (p=0.611).
Flagged: 0253-B-r4: ngB_mean 3.09 > rest max 2.62 (rest med 2.48, z 10.6) | ngU_mean 3.61 > rest max 3.41 (rest med 3.33, z 7.3) | ngB_max 5.28 > rest max 5.16 (rest med 4.14, z 4.9) | ng_t bursts 21/50 > folder p90 3.28

### W6-2 (20261123-0313): 21 runs, 20 scored; folder-pooled ng_t p90 3.21, ng_u p90 4.04

| # | run | win wall | fps | game | ng_t mean | ng_t max | ng_u mean | ng_u max | z_t | z_u | z_t arm | bursts t/u | P util % | E MHz (min) | fg % | idle min s | change in window | change in run | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0313-cold-s0 (unscored) | 03:14:27-03:14:57 | 448.3 | 2.40 | 2.37 | 3.40 | 3.39 | 4.17 | - | - | - | - | 66.7 | 2045 (1881) | 100 | 12428 | none | none | - |
| 2 | 0315-s0-r1 | 03:16:09-03:16:59 | 417.3 | 2.49 | 2.62 | 4.67 | 3.50 | 5.29 | 0.8 | 0.9 | 0.3 | 8/5 | 64.0 | 1983 (1761) | 100 | 12531 | none | batt_pct changes [{"t_s": 22.591, "epoch_s": 1795425328.61, "from": 98, "to": 99}] | - |
| 3 | 0317-p2-r1 | 03:18:13-03:19:03 | 394.2 | 2.55 | 2.46 | 4.04 | 3.34 | 4.86 | -0.7 | -0.7 | -2.2 | 4/2 | 64.8 | 1990 (1779) | 100 | 12655 | none | none | - |
| 4 | 0319-p2f-r1 | 03:20:16-03:21:06 | 387.7 | 2.56 | 2.44 | 3.66 | 3.34 | 4.55 | -0.9 | -0.8 | -4.6 | 3/3 | 62.9 | 1996 (1788) | 100 | 12778 | none | none | - |
| 5 | 0321-p2fc-r1 | 03:22:20-03:23:10 | 471.3 | 2.27 | 2.26 | 4.24 | 3.42 | 5.29 | -2.3 | 0.1 | -4.3 | 2/4 | 65.8 | 2105 (1912) | 100 | 12901 | none | none | - |
| 6 | 0323-p2-r2 | 03:24:23-03:25:13 | 385.6 | 2.57 | 2.50 | 3.68 | 3.34 | 4.50 | -0.3 | -0.7 | -0.5 | 6/4 | 64.2 | 1973 (1768) | 100 | 13025 | none | none | - |
| 7 | 0325-p2f-r2 | 03:26:27-03:27:17 | 385.9 | 2.52 | 2.57 | 3.95 | 3.45 | 4.59 | 0.4 | 0.4 | 1.0 | 8/6 | 63.9 | 1979 (1744) | 100 | 13148 | none | batt_pct changes [{"t_s": 43.583, "epoch_s": 1795425966.874, "from": 99, "to": 100}] | - |
| 8 | 0327-p2fc-r2 | 03:28:30-03:29:20 | 470.3 | 2.29 | 2.39 | 3.95 | 3.52 | 4.98 | -1.3 | 1.1 | -0.2 | 3/5 | 65.0 | 2084 (1958) | 100 | 13272 | none | none | - |
| 9 | 0329-s0-r2 | 03:30:34-03:31:24 | 381.9 | 2.52 | 2.61 | 4.62 | 3.46 | 4.89 | 0.7 | 0.4 | 0.2 | 5/4 | 64.9 | 1971 (1771) | 100 | 13395 | none | none | - |
| 10 | 0331-p2f-r3 | 03:32:37-03:33:27 | 385.9 | 2.56 | 2.46 | 3.44 | 3.34 | 4.25 | -0.6 | -0.7 | -3.5 | 1/1 | 64.1 | 1976 (1893) | 100 | 13519 | none | none | - |
| 11 | 0333-p2fc-r3 | 03:34:41-03:35:31 | 468.1 | 2.25 | 2.39 | 3.90 | 3.53 | 4.77 | -1.2 | 1.1 | -0.2 | 1/5 | 66.1 | 2094 (1928) | 100 | 13642 | none | none | - |
| 12 | 0335-s0-r3 | 03:36:44-03:37:34 | 383.7 | 2.50 | 2.71 | 5.17 | 3.52 | 5.25 | 1.6 | 1.1 | 2.5 | 10/8 | 62.7 | 1961 (1673) | 100 | 13766 | none | none | - |
| 13 | 0337-p2-r3 | 03:38:48-03:39:38 | 383.9 | 2.56 | 2.55 | 4.64 | 3.38 | 5.22 | 0.3 | -0.4 | 0.9 | 3/3 | 62.5 | 1965 (1840) | 100 | 13889 | none | none | - |
| 14 | 0339-p2fc-r4 | 03:40:51-03:41:41 | 451.5 | 2.22 | 2.96 | 8.17 | 3.89 | 7.45 | 3.5 | 4.6 | 16.1 | 13/16 | 65.5 | 2008 (1545) | 100 | 14013 | none | none | FLAG: ngB_mean 2.96 > rest max 2.91 (rest med 2.52, z 3.5) | ngU_mean 3.89 > rest max 3.63 (rest med 3.41, z 4.6) | ngB_max 8.17 > rest max 5.52 (rest med 4.22, z 6.6) | ngU_max 7.45 > rest max 5.74 (rest med 4.97, z 6.6) | ng_t bursts 13/50 > folder p90 3.21 |
| 15 | 0341-s0-r4 | 03:42:54-03:43:44 | 385.0 | 2.57 | 2.55 | 4.66 | 3.37 | 5.23 | 0.2 | -0.5 | -0.8 | 4/4 | 64.3 | 1951 (1702) | 100 | 14136 | none | none | - |
| 16 | 0343-p2-r4 | 03:44:58-03:45:48 | 385.2 | 2.44 | 2.52 | 4.56 | 3.41 | 5.02 | -0.2 | -0.1 | -0.1 | 4/3 | 64.8 | 1978 (1818) | 100 | 14260 | none | none | - |
| 17 | 0345-p2f-r4 | 03:47:01-03:47:51 | 386.5 | 2.61 | 2.54 | 4.22 | 3.35 | 4.78 | 0.2 | -0.6 | 0.4 | 6/4 | 62.8 | 1962 (1704) | 100 | 14383 | none | none | - |
| 18 | 0348-s0-r5 | 03:49:05-03:49:55 | 385.6 | 2.56 | 2.40 | 4.17 | 3.28 | 4.87 | -1.2 | -1.2 | -4.1 | 1/2 | 63.3 | 1991 (1852) | 100 | 14507 | none | none | - |
| 19 | 0350-p2-r5 | 03:51:09-03:51:59 | 375.5 | 2.51 | 2.91 | 5.52 | 3.63 | 5.74 | 3.1 | 2.1 | 10.6 | 11/11 | 64.1 | 1934 (1662) | 100 | 14630 | none | none | - |
| 20 | 0352-p2f-r5 | 03:53:12-03:54:02 | 385.1 | 2.51 | 2.55 | 5.08 | 3.41 | 5.50 | 0.3 | -0.1 | 0.7 | 3/4 | 64.1 | 1974 (1717) | 100 | 14754 | none | none | - |
| 21 | 0354-p2fc-r5 | 03:55:16-03:56:06 | 469.8 | 2.25 | 2.44 | 4.01 | 3.54 | 4.97 | -0.9 | 1.3 | 0.5 | 3/6 | 66.1 | 2080 (1930) | 100 | 14878 | none | none | - |

Folder: ng_t mean median 2.53 [2.26..2.96], ng_u mean median 3.42 [3.28..3.89], game median 2.52 cores, P util median 64.2 %, E MHz median 1979 (min 1545). Spearman (scored runs): ng_t mean vs fps_rel rho -0.50 (n=20, p=0.026); ng_u mean vs fps_rel rho -0.54 (p=0.014); run order vs ng_t mean rho 0.17 (p=0.499).
Flagged: 0339-p2fc-r4: ngB_mean 2.96 > rest max 2.91 (rest med 2.52, z 3.5) | ngU_mean 3.89 > rest max 3.63 (rest med 3.41, z 4.6) | ngB_max 8.17 > rest max 5.52 (rest med 4.22, z 6.6) | ngU_max 7.45 > rest max 5.74 (rest med 4.97, z 6.6) | ng_t bursts 13/50 > folder p90 3.21

### W9-2 (20261123-0401): 21 runs, 20 scored; folder-pooled ng_t p90 4.06, ng_u p90 4.69

| # | run | win wall | fps | game | ng_t mean | ng_t max | ng_u mean | ng_u max | z_t | z_u | z_t arm | bursts t/u | P util % | E MHz (min) | fg % | idle min s | change in window | change in run | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0401-cold-off (unscored) | 04:02:22-04:02:52 | 450.0 | 2.48 | 2.30 | 3.06 | 3.25 | 3.97 | - | - | - | - | 64.5 | 2016 (1944) | 100 | 15303 | none | none | - |
| 2 | 0403-off-r1 | 04:04:04-04:04:54 | 408.9 | 2.44 | 2.38 | 4.09 | 3.36 | 4.92 | -0.5 | -1.0 | -1.0 | 1/1 | 64.7 | 2028 (1837) | 100 | 15406 | none | none | - |
| 3 | 0405-q0-r1 | 04:06:08-04:06:58 | 385.8 | 2.49 | 2.67 | 4.43 | 3.71 | 5.03 | 0.6 | 1.2 | 12.9 | 3/3 | 66.3 | 2024 (1773) | 100 | 15529 | none | none | - |
| 4 | 0407-q125-r1 | 04:08:11-04:09:01 | 365.0 | 2.15 | 4.06 | 8.60 | 4.62 | 7.33 | 4.8 | 6.3 | 43.9 | 18/16 | 61.7 | 1841 (1504) | 100 | 15653 | none | none | FLAG: ngB_mean 4.06 > rest max 4.03 (rest med 2.48, z 4.8) | ngU_mean 4.62 > rest max 4.57 (rest med 3.51, z 6.3) | ngB_max 8.60 > rest max 7.87 (rest med 4.60, z 4.4) | ng_t bursts 18/50 > folder p90 4.06 |
| 5 | 0409-q250-r1 | 04:10:16-04:11:06 | 378.2 | 2.11 | 3.72 | 5.86 | 4.36 | 6.05 | 3.8 | 4.9 | 2.4 | 23/20 | 61.6 | 1879 (1579) | 100 | 15778 | none | none | FLAG: ng_t bursts 23/50 > folder p90 4.06 |
| 6 | 0411-q500-r1 | 04:12:20-04:13:10 | 388.7 | 1.73 | 2.31 | 4.76 | 3.52 | 5.33 | -0.6 | 0.1 | 0.2 | 2/3 | 62.4 | 2184 (1800) | 100 | 15902 | none | none | - |
| 7 | 0413-q0-r2 | 04:14:24-04:15:14 | 385.1 | 2.46 | 2.36 | 5.09 | 3.50 | 5.86 | -0.5 | -0.1 | -1.6 | 1/1 | 65.9 | 2082 (1813) | 100 | 16025 | none | none | - |
| 8 | 0415-q125-r2 | 04:16:27-04:17:17 | 391.0 | 1.76 | 2.28 | 3.86 | 3.47 | 5.05 | -0.7 | -0.2 | -45.2 | 0/2 | 60.0 | 2153 (1970) | 100 | 16149 | none | none | - |
| 9 | 0417-q250-r2 | 04:18:30-04:19:20 | 379.1 | 1.93 | 2.91 | 7.87 | 3.87 | 8.08 | 1.3 | 2.1 | -0.3 | 8/7 | 64.4 | 2053 (1500) | 100 | 16272 | none | none | FLAG: ngU_max 8.08 > rest max 7.33 (rest med 5.20, z 6.6) |
| 10 | 0419-q500-r2 | 04:20:34-04:21:24 | 385.8 | 2.03 | 3.36 | 5.32 | 4.24 | 5.52 | 2.7 | 4.2 | 36.1 | 7/9 | 62.2 | 1922 (1659) | 100 | 16395 | none | none | - |
| 11 | 0421-off-r2 | 04:22:38-04:23:28 | 382.2 | 2.54 | 2.92 | 4.98 | 3.62 | 5.50 | 1.3 | 0.5 | 3.0 | 5/3 | 62.1 | 1905 (1647) | 100 | 16520 | none | none | - |
| 12 | 0423-q125-r3 | 04:24:41-04:25:32 | 368.4 | 2.13 | 4.03 | 7.56 | 4.57 | 6.71 | 4.7 | 6.1 | 43.3 | 14/17 | 62.9 | 1834 (1543) | 100 | 16643 | none | none | FLAG: ng_t bursts 14/50 > folder p90 4.06 |
| 13 | 0425-q250-r3 | 04:26:45-04:27:35 | 386.4 | 1.98 | 3.14 | 5.28 | 4.04 | 5.67 | 2.0 | 3.0 | 0.2 | 8/7 | 62.4 | 1971 (1619) | 100 | 16767 | none | none | - |
| 14 | 0427-q500-r3 | 04:28:48-04:29:38 | 389.8 | 1.73 | 2.21 | 3.24 | 3.44 | 4.56 | -0.9 | -0.3 | -3.2 | 0/0 | 62.4 | 2177 (1986) | 100 | 16890 | none | none | - |
| 15 | 0429-off-r3 | 04:30:52-04:31:42 | 385.2 | 2.52 | 2.48 | 4.47 | 3.35 | 5.06 | -0.3 | -1.1 | -0.5 | 1/1 | 64.5 | 1977 (1799) | 100 | 17014 | none | none | - |
| 16 | 0431-q0-r3 | 04:32:55-04:33:45 | 387.2 | 2.46 | 2.38 | 4.30 | 3.49 | 5.20 | -0.5 | -0.1 | -1.5 | 1/1 | 66.7 | 2068 (1919) | 100 | 17137 | none | none | - |
| 17 | 0433-q250-r4 | 04:34:59-04:35:49 | 389.1 | 1.79 | 2.26 | 4.06 | 3.43 | 4.87 | -0.8 | -0.4 | -2.6 | 0/1 | 62.2 | 2139 (1884) | 100 | 17261 | none | none | - |
| 18 | 0435-q500-r4 | 04:37:02-04:37:52 | 389.8 | 1.71 | 2.29 | 3.94 | 3.51 | 5.16 | -0.7 | -0.0 | -0.1 | 0/1 | 61.6 | 2167 (1971) | 100 | 17384 | none | none | - |
| 19 | 0438-off-r4 | 04:39:05-04:39:55 | 384.6 | 2.49 | 2.68 | 4.60 | 3.49 | 4.93 | 0.6 | -0.1 | 1.3 | 3/2 | 63.9 | 1954 (1718) | 100 | 17507 | none | none | - |
| 20 | 0440-q0-r4 | 04:41:09-04:41:59 | 384.0 | 2.46 | 2.81 | 5.28 | 3.73 | 5.26 | 1.0 | 1.3 | 18.7 | 5/4 | 65.3 | 1996 (1625) | 100 | 17631 | none | none | - |
| 21 | 0442-q125-r4 | 04:43:12-04:44:02 | 389.4 | 1.79 | 2.25 | 3.99 | 3.43 | 4.73 | -0.8 | -0.4 | -45.9 | 0/1 | 62.1 | 2138 (1843) | 100 | 17754 | none | none | - |

Folder: ng_t mean median 2.58 [2.21..4.06], ng_u mean median 3.51 [3.35..4.62], game median 2.12 cores, P util median 62.4 %, E MHz median 2026 (min 1500). Spearman (scored runs): ng_t mean vs fps_rel rho -0.75 (n=20, p=0.000); ng_u mean vs fps_rel rho -0.78 (p=0.000); run order vs ng_t mean rho -0.33 (p=0.166).
Flagged: 0407-q125-r1: ngB_mean 4.06 > rest max 4.03 (rest med 2.48, z 4.8) | ngU_mean 4.62 > rest max 4.57 (rest med 3.51, z 6.3) | ngB_max 8.60 > rest max 7.87 (rest med 4.60, z 4.4) | ng_t bursts 18/50 > folder p90 4.06; 0409-q250-r1: ng_t bursts 23/50 > folder p90 4.06; 0417-q250-r2: ngU_max 8.08 > rest max 7.33 (rest med 5.20, z 6.6); 0423-q125-r3: ng_t bursts 14/50 > folder p90 4.06

### W5b-2 (20261123-0451): 19 runs, 18 scored; folder-pooled ng_t p90 3.73, ng_u p90 4.24

| # | run | win wall | fps | game | ng_t mean | ng_t max | ng_u mean | ng_u max | z_t | z_u | z_t arm | bursts t/u | P util % | E MHz (min) | fg % | idle min s | change in window | change in run | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0451-cold-d11 (unscored) | 04:53:03-04:53:33 | 441.8 | 2.48 | 2.55 | 4.97 | 3.39 | 5.09 | - | - | - | - | 63.2 | 1979 (1666) | 100 | 18345 | none | none | - |
| 2 | 0453-d11-r1 | 04:54:46-04:55:36 | 393.0 | 2.60 | 3.53 | 7.49 | 4.07 | 6.32 | 9.7 | 7.7 | 67.2 | 12/16 | 65.7 | 1866 (1487) | 100 | 18447 | none | none | FLAG: ng_t bursts 12/50 > folder p90 3.73 |
| 3 | 0455-d11t-r1 | 04:56:51-04:57:41 | 367.1 | 2.36 | 3.37 | 5.48 | 4.00 | 5.49 | 8.3 | 6.9 | 12.3 | 15/15 | 63.5 | 1882 (1659) | 100 | 18572 | none | none | FLAG: ng_t bursts 15/50 > folder p90 3.73 |
| 4 | 0457-d11p-r1 | 04:58:54-04:59:44 | 386.0 | 2.37 | 3.76 | 5.50 | 4.15 | 5.80 | 11.9 | 8.5 | 6.2 | 22/16 | 58.5 | 1776 (1691) | 100 | 18696 | none | none | FLAG: ngB_mean 3.76 > rest max 3.53 (rest med 2.51, z 11.9) | ngU_mean 4.15 > rest max 4.07 (rest med 3.35, z 8.5) | ng_t bursts 22/50 > folder p90 3.73 |
| 5 | 0459-d11t-r2 | 05:00:58-05:01:48 | 376.6 | 2.34 | 2.84 | 4.40 | 3.60 | 5.04 | 3.1 | 2.7 | 4.8 | 6/10 | 61.7 | 1941 (1754) | 100 | 18819 | none | none | - |
| 6 | 0501-d11p-r2 | 05:03:01-05:03:51 | 385.4 | 2.27 | 2.46 | 3.49 | 3.29 | 4.21 | -0.5 | -0.5 | -0.9 | 0/0 | 62.3 | 1972 (1860) | 100 | 18943 | none | none | - |
| 7 | 0504-d11-r2 | 05:05:05-05:05:55 | 385.2 | 2.55 | 2.50 | 4.38 | 3.38 | 5.17 | -0.3 | 0.2 | -0.2 | 1/1 | 62.7 | 1984 (1780) | 100 | 19067 | none | none | - |
| 8 | 0506-d11p-r3 | 05:07:08-05:07:58 | 385.9 | 2.35 | 2.56 | 3.81 | 3.32 | 4.52 | 0.4 | -0.3 | -0.5 | 2/3 | 60.3 | 1943 (1809) | 100 | 19190 | none | none | - |
| 9 | 0508-d11-r3 | 05:09:12-05:10:02 | 385.0 | 2.59 | 2.50 | 3.79 | 3.33 | 4.27 | -0.3 | -0.3 | -0.3 | 1/1 | 62.5 | 1962 (1791) | 100 | 19314 | none | none | - |
| 10 | 0510-d11t-r3 | 05:11:16-05:12:06 | 379.3 | 2.31 | 2.87 | 7.60 | 3.57 | 6.96 | 3.5 | 2.4 | 5.3 | 7/6 | 62.6 | 1917 (1539) | 100 | 19437 | none | none | FLAG: ngB_max 7.60 > rest max 7.49 (rest med 4.37, z 3.9) | ngU_max 6.96 > rest max 6.32 (rest med 4.95, z 3.4) |
| 11 | 0512-d11-r4 | 05:13:19-05:14:09 | 385.4 | 2.57 | 2.51 | 4.33 | 3.35 | 4.95 | -0.2 | -0.2 | 0.2 | 1/1 | 62.4 | 1974 (1830) | 100 | 19561 | none | none | - |
| 12 | 0514-d11t-r4 | 05:15:23-05:16:13 | 384.7 | 2.34 | 2.44 | 4.23 | 3.28 | 4.94 | -0.6 | -0.5 | -0.8 | 1/1 | 62.2 | 1978 (1788) | 100 | 19684 | none | none | - |
| 13 | 0516-d11p-r4 | 05:17:26-05:18:16 | 385.5 | 2.38 | 2.43 | 3.64 | 3.22 | 4.27 | -0.7 | -1.1 | -1.0 | 0/1 | 62.6 | 1961 (1826) | 100 | 19808 | none | none | - |
| 14 | 0518-d11t-r5 | 05:19:30-05:20:20 | 385.7 | 2.36 | 2.49 | 3.99 | 3.30 | 4.67 | -0.3 | -0.5 | -0.6 | 1/1 | 63.1 | 1965 (1861) | 100 | 19931 | none | none | - |
| 15 | 0520-d11p-r5 | 05:21:33-05:22:23 | 375.6 | 2.37 | 2.90 | 5.64 | 3.55 | 5.57 | 3.7 | 2.1 | 1.7 | 8/7 | 63.3 | 1912 (1642) | 100 | 20055 | none | none | - |
| 16 | 0522-d11-r5 | 05:23:37-05:24:27 | 385.0 | 2.53 | 2.43 | 4.37 | 3.31 | 4.89 | -0.8 | -0.4 | -4.1 | 1/1 | 63.8 | 1992 (1846) | 100 | 20178 | none | none | - |
| 17 | 0524-d11p-r6 | 05:25:40-05:26:30 | 382.1 | 2.37 | 2.88 | 5.50 | 3.52 | 5.35 | 3.5 | 1.8 | 1.6 | 10/7 | 61.2 | 1902 (1594) | 100 | 20302 | none | none | - |
| 18 | 0526-d11-r6 | 05:27:44-05:28:34 | 385.2 | 2.51 | 2.55 | 4.48 | 3.39 | 5.05 | 0.3 | 0.3 | 2.9 | 1/2 | 64.1 | 1975 (1844) | 100 | 20426 | none | none | - |
| 19 | 0528-d11t-r6 | 05:29:47-05:30:37 | 385.4 | 2.37 | 2.45 | 3.82 | 3.26 | 4.61 | -0.6 | -0.8 | -0.8 | 1/1 | 62.2 | 1963 (1840) | 100 | 20549 | none | none | - |

Folder: ng_t mean median 2.53 [2.43..3.76], ng_u mean median 3.36 [3.22..4.15], game median 2.37 cores, P util median 62.6 %, E MHz median 1961 (min 1487). Spearman (scored runs): ng_t mean vs fps_rel rho -0.23 (n=18, p=0.348); ng_u mean vs fps_rel rho -0.34 (p=0.165); run order vs ng_t mean rho -0.48 (p=0.048).
Flagged: 0453-d11-r1: ng_t bursts 12/50 > folder p90 3.73; 0455-d11t-r1: ng_t bursts 15/50 > folder p90 3.73; 0457-d11p-r1: ngB_mean 3.76 > rest max 3.53 (rest med 2.51, z 11.9) | ngU_mean 4.15 > rest max 4.07 (rest med 3.35, z 8.5) | ng_t bursts 22/50 > folder p90 3.73; 0510-d11t-r3: ngB_max 7.60 > rest max 7.49 (rest med 4.37, z 3.9) | ngU_max 6.96 > rest max 6.32 (rest med 4.95, z 3.4)

### Per-arm summary (scored runs; medians over runs of per-run window values)

| window | arm | n | fps med | game med | ng_t mean med [min..max] | ng_t 1 s max | ng_u mean med [min..max] | P util med % | E MHz med (min) | E<800 max % | fg min % | flagged |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| W6-1 | p2 | 5 | 385.6 | 2.51 | 2.50 [2.42..2.87] | 5.56 | 3.39 [3.32..3.59] | 63.8 | 1984 (1587) | 0 | 100 | - |
| W6-1 | p2f | 5 | 387.7 | 2.55 | 2.46 [2.40..2.57] | 4.64 | 3.36 [3.33..3.39] | 64.1 | 1983 (1696) | 0 | 100 | - |
| W6-1 | p2fc | 5 | 466.3 | 2.28 | 2.44 [2.25..3.95] | 9.38 | 3.55 [3.43..4.64] | 65.6 | 2075 (1490) | 0 | 100 | 0023-p2fc-r2 |
| W6-1 | s0 | 5 | 385.2 | 2.50 | 2.54 [2.47..4.09] | 6.68 | 3.46 [3.36..4.38] | 64.3 | 1978 (1540) | 0 | 100 | 0025-s0-r2 |
| W9-1 | off | 4 | 386.2 | 2.52 | 2.53 [2.45..2.55] | 5.39 | 3.36 [3.36..3.37] | 62.7 | 1970 (1677) | 0 | 100 | - |
| W9-1 | q0 | 4 | 387.0 | 2.49 | 2.52 [2.37..2.77] | 6.10 | 3.57 [3.48..3.70] | 65.1 | 2039 (1553) | 0 | 100 | - |
| W9-1 | q125 | 4 | 389.5 | 1.84 | 2.29 [2.20..2.50] | 6.61 | 3.46 [3.37..3.59] | 63.1 | 2139 (1676) | 0 | 100 | 0122-q125-r2 |
| W9-1 | q250 | 4 | 389.3 | 1.73 | 2.27 [2.18..2.57] | 6.08 | 3.44 [3.42..3.59] | 62.3 | 2146 (1618) | 0 | 100 | 0124-q250-r2 |
| W9-1 | q500 | 4 | 390.1 | 1.72 | 2.22 [2.16..2.25] | 4.19 | 3.44 [3.42..3.45] | 61.4 | 2183 (1817) | 0 | 100 | - |
| W5b-1 | d11 | 6 | 384.6 | 2.54 | 2.54 [2.46..2.66] | 6.20 | 3.35 [3.34..3.45] | 63.2 | 1958 (1629) | 0 | 100 | - |
| W5b-1 | d11p | 6 | 385.0 | 2.32 | 2.56 [2.45..3.07] | 5.76 | 3.30 [3.23..3.59] | 61.5 | 1947 (1562) | 0 | 100 | 0209-d11p-r3 |
| W5b-1 | d11t | 6 | 384.2 | 2.29 | 2.57 [2.36..3.36] | 8.04 | 3.36 [3.21..3.81] | 61.3 | 1958 (1446) | 0 | 100 | 0213-d11t-r3 |
| W4c | B | 6 | 383.9 | 2.58 | 2.57 [2.45..3.09] | 5.28 | 3.38 [3.26..3.61] | 63.9 | 1953 (1634) | 0 | 100 | 0253-B-r4 |
| W4c | d0 | 6 | 385.3 | 2.53 | 2.46 [2.43..2.52] | 4.14 | 3.33 [3.31..3.36] | 63.2 | 1979 (1767) | 0 | 100 | - |
| W6-2 | p2 | 5 | 385.2 | 2.55 | 2.52 [2.46..2.91] | 5.52 | 3.38 [3.34..3.63] | 64.2 | 1973 (1662) | 0 | 100 | - |
| W6-2 | p2f | 5 | 385.9 | 2.56 | 2.54 [2.44..2.57] | 5.08 | 3.35 [3.34..3.45] | 63.9 | 1976 (1704) | 0 | 100 | - |
| W6-2 | p2fc | 5 | 469.8 | 2.25 | 2.39 [2.26..2.96] | 8.17 | 3.53 [3.42..3.89] | 65.8 | 2084 (1545) | 0 | 100 | 0339-p2fc-r4 |
| W6-2 | s0 | 5 | 385.0 | 2.52 | 2.61 [2.40..2.71] | 5.17 | 3.46 [3.28..3.52] | 64.0 | 1971 (1673) | 0 | 100 | - |
| W9-2 | off | 4 | 384.9 | 2.50 | 2.58 [2.38..2.92] | 4.98 | 3.42 [3.35..3.62] | 64.2 | 1966 (1647) | 0 | 100 | - |
| W9-2 | q0 | 4 | 385.5 | 2.46 | 2.52 [2.36..2.81] | 5.28 | 3.60 [3.49..3.73] | 66.1 | 2046 (1625) | 0 | 100 | - |
| W9-2 | q125 | 4 | 378.9 | 1.96 | 3.16 [2.25..4.06] | 8.60 | 4.02 [3.43..4.62] | 61.9 | 1990 (1504) | 0 | 100 | 0407-q125-r1,0423-q125-r3 |
| W9-2 | q250 | 4 | 382.8 | 1.96 | 3.03 [2.26..3.72] | 7.87 | 3.95 [3.43..4.36] | 62.3 | 2012 (1500) | 0 | 100 | 0409-q250-r1,0417-q250-r2 |
| W9-2 | q500 | 4 | 389.2 | 1.73 | 2.30 [2.21..3.36] | 5.32 | 3.51 [3.44..4.24] | 62.3 | 2172 (1659) | 0 | 100 | - |
| W5b-2 | d11 | 6 | 385.2 | 2.56 | 2.51 [2.43..3.53] | 7.49 | 3.36 [3.31..4.07] | 63.3 | 1974 (1487) | 0 | 100 | 0453-d11-r1 |
| W5b-2 | d11p | 6 | 385.4 | 2.37 | 2.72 [2.43..3.76] | 5.64 | 3.42 [3.22..4.15] | 61.8 | 1928 (1594) | 0 | 100 | 0457-d11p-r1 |
| W5b-2 | d11t | 6 | 382.0 | 2.35 | 2.66 [2.44..3.37] | 7.60 | 3.44 [3.26..4.00] | 62.4 | 1952 (1539) | 0 | 100 | 0455-d11t-r1,0510-d11t-r3 |

### Folder level, in time order (scored runs)

| window | folder | windows | n | ng_t mean med [min..max] | ng_u mean med [min..max] | game med | P util med | E MHz med | flagged runs |
|---|---|---|---|---|---|---|---|---|---|
| W6-1 | 20261123-0009 | 00:11-00:51 | 20 | 2.51 [2.25..4.09] | 3.41 [3.32..4.64] | 2.50 | 64.1 | 1985 | 2 |
| W9-1 | 20261123-0108 | 01:11-01:51 | 20 | 2.37 [2.16..2.77] | 3.44 [3.36..3.70] | 1.87 | 62.8 | 2108 | 2 |
| W5b-1 | 20261123-0155 | 01:58-02:33 | 18 | 2.56 [2.36..3.36] | 3.34 [3.21..3.81] | 2.35 | 61.7 | 1955 | 2 |
| W4c | 20261123-0239 | 02:42-03:05 | 12 | 2.50 [2.43..3.09] | 3.34 [3.26..3.61] | 2.55 | 63.8 | 1972 | 1 |
| W6-2 | 20261123-0313 | 03:16-03:56 | 20 | 2.53 [2.26..2.96] | 3.42 [3.28..3.89] | 2.52 | 64.2 | 1979 | 1 |
| W9-2 | 20261123-0401 | 04:04-04:44 | 20 | 2.58 [2.21..4.06] | 3.51 [3.35..4.62] | 2.12 | 62.4 | 2026 | 4 |
| W5b-2 | 20261123-0451 | 04:54-05:30 | 18 | 2.53 [2.43..3.76] | 3.36 [3.22..4.15] | 2.37 | 62.6 | 1961 | 4 |

### W5b-2 (0451) vs W5b-1 (0155): CrossDeviceService holdback check

Agent 8's note: the quiet gate held W5b-2 back while CrossDeviceService ran at 0.7-0.9 core, 04:46-04:49; W5b-2's cold run started 04:51:59. No sys.csv covers 04:46-04:49 (W9-2's last run ended ~04:44). A carry-over would show as higher ng_t in W5b-2 than in W5b-1 for the same arm, largest in the first runs.

| arm | n 1/2 | ng_t mean med 1 / 2 | diff | ng_u mean med 1 / 2 | diff | game 1 / 2 | P util 1 / 2 | E MHz 1 / 2 | fps 1 / 2 |
|---|---|---|---|---|---|---|---|---|---|
| d11 | 6/6 | 2.54 / 2.51 | -0.03 | 3.35 / 3.36 | 0.01 | 2.54 / 2.56 | 63.2 / 63.3 | 1958 / 1974 | 384.6 / 385.2 |
| d11t | 6/6 | 2.57 / 2.66 | 0.09 | 3.36 / 3.44 | 0.07 | 2.29 / 2.35 | 61.3 / 62.4 | 1958 / 1952 | 384.2 / 382.0 |
| d11p | 6/6 | 2.56 / 2.72 | 0.16 | 3.30 / 3.42 | 0.11 | 2.32 / 2.37 | 61.5 / 61.8 | 1947 / 1928 | 385.0 / 385.4 |

W5b-2 runs in order (window ng_t mean / ng_u mean; warm-up ng_t mean):

| # | run | window | ng_t mean | ng_u mean | warm-up ng_t mean | game |
|---|---|---|---|---|---|---|
| 1 | 0451-cold-d11 (unscored) | 04:53:03-04:53:33 | 2.55 | 3.39 | 1.94 | 2.48 |
| 2 | 0453-d11-r1 | 04:54:46-04:55:36 | 3.53 | 4.07 | 2.55 | 2.60 |
| 3 | 0455-d11t-r1 | 04:56:51-04:57:41 | 3.37 | 4.00 | 3.80 | 2.36 |
| 4 | 0457-d11p-r1 | 04:58:54-04:59:44 | 3.76 | 4.15 | 3.62 | 2.37 |
| 5 | 0459-d11t-r2 | 05:00:58-05:01:48 | 2.84 | 3.60 | 3.48 | 2.34 |
| 6 | 0501-d11p-r2 | 05:03:01-05:03:51 | 2.46 | 3.29 | 3.16 | 2.27 |
| 7 | 0504-d11-r2 | 05:05:05-05:05:55 | 2.50 | 3.38 | 2.38 | 2.55 |
| 8 | 0506-d11p-r3 | 05:07:08-05:07:58 | 2.56 | 3.32 | 2.58 | 2.35 |
| 9 | 0508-d11-r3 | 05:09:12-05:10:02 | 2.50 | 3.33 | 2.55 | 2.59 |
| 10 | 0510-d11t-r3 | 05:11:16-05:12:06 | 2.87 | 3.57 | 2.45 | 2.31 |
| 11 | 0512-d11-r4 | 05:13:19-05:14:09 | 2.51 | 3.35 | 2.53 | 2.57 |
| 12 | 0514-d11t-r4 | 05:15:23-05:16:13 | 2.44 | 3.28 | 2.35 | 2.34 |
| 13 | 0516-d11p-r4 | 05:17:26-05:18:16 | 2.43 | 3.22 | 2.46 | 2.38 |
| 14 | 0518-d11t-r5 | 05:19:30-05:20:20 | 2.49 | 3.30 | 2.38 | 2.36 |
| 15 | 0520-d11p-r5 | 05:21:33-05:22:23 | 2.90 | 3.55 | 2.45 | 2.37 |
| 16 | 0522-d11-r5 | 05:23:37-05:24:27 | 2.43 | 3.31 | 2.46 | 2.53 |
| 17 | 0524-d11p-r6 | 05:25:40-05:26:30 | 2.88 | 3.52 | 2.48 | 2.37 |
| 18 | 0526-d11-r6 | 05:27:44-05:28:34 | 2.55 | 3.39 | 2.47 | 2.51 |
| 19 | 0528-d11t-r6 | 05:29:47-05:30:37 | 2.45 | 3.26 | 2.45 | 2.37 |

First 3 scored runs vs the other 15, ng_t mean median: W5b-2 3.53 vs 2.50; W5b-1 2.46 vs 2.56. Cold runs (window/warm-up ng_t mean): W5b-1 0155-cold-d11 2.39/1.93, W5b-2 0451-cold-d11 2.55/1.94.

## 3. Frames over 16.7 ms in W6 (0009 = W6-1, 0313 = W6-2)

Window rows = frames.json window.first_row .. first_row+rows-1 (0-based data rows of perf.csv, header excluded; checked against window.start_bytes per run: "row conv" 0 = match). T = summed frame_time_us from the window start (T start = frame began, T end = frame ended). Wall time: measure_start epoch + T end, minus 0..59 unflushed rows at the start mark (perf.csv flushes every 60 rows), i.e. up to "lag" s earlier; the est. wall is the middle of that range. sys/proc values are the 1 s sample containing it.

### 3.1 The 45.67 ms frame: 20261123-0313/0352-p2f-r5

- frames.json window: first_row 24480, rows 19258, start_bytes 1161434; row convention offset 0 (0 = first_row is the 0-based data row starting at start_bytes).
- The frame: window frame #2849 (0-based), perf.csv data row 27329 (file line 27331 incl. header), **45.67 ms**, T start 7.443 s, **T end 7.489 s** from the window start (15.0 % into the 50 s window).
- measure_start 03:53:12.640 (epoch 1795427592.640); estimated wall of the frame end 03:53:19.984 .. 03:53:20.129 (lag 0.144 s).

perf.csv rows around it (per-frame counters):

| data row | file line | frame_time_us | fps | draw_calls | command_buffer_stalls | vertices_processed | xma_frames_decoded | audio_frame_latency_us | buffer_queue_depth | functions_dispatched | interrupt_dispatches | active_threads | apc_queue_depth | critical_region_contentions | texture_cache_hits | texture_cache_misses | pipeline_cache_hits | pipeline_cache_misses |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 27326 | 27328 | 8014 | 124 | 226 | 0 | 1022 | 0 | 0 | 8 | 19 | 17 | 30 | 0 | 0 | 2 | 0 | 7 | 0 |
| 27327 | 27329 | 9526 | 104 | 226 | 0 | 1022 | 0 | 0 | 8 | 19 | 17 | 30 | 0 | 0 | 2 | 0 | 7 | 0 |
| 27328 | 27330 | 1699 | 588 | 226 | 0 | 1022 | 0 | 0 | 0 | 13 | 13 | 30 | 0 | 0 | 2 | 0 | 7 | 0 |
| 27329 | 27331 | 45670 | 21 | 226 | 0 | 1022 | 0 | 0 | 8 | 62 | 55 | 30 | 0 | 0 | 2 | 0 | 7 | 0 |
| 27330 | 27332 | 13869 | 72 | 226 | 0 | 1022 | 0 | 0 | 8 | 27 | 23 | 30 | 0 | 0 | 2 | 0 | 7 | 0 |
| 27331 | 27333 | 4003 | 249 | 226 | 0 | 1022 | 0 | 0 | 0 | 12 | 12 | 30 | 0 | 0 | 2 | 0 | 7 | 0 |
| 27332 | 27334 | 1673 | 597 | 226 | 0 | 1022 | 0 | 0 | 0 | 12 | 12 | 30 | 0 | 0 | 2 | 0 | 7 | 0 |

sys.csv samples (1 s; "in" = the interval containing the frame end estimate range):

| in | wall (end) | phase | cpu util | perf | P util | E util | P MHz | E MHz | busy_t | util_LP | game | ng_t | ng_u | idle_s | fg | desktop | overlay |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  | 03:53:19.421 | window | 48.5 | 121.3 | 65.7 | 39.8 | 1986 | 2017 | 4.83 | 5.81 | 2.70 | 2.13 | 3.12 | 14759.8 | 1 | Default | best_performance |
| Y | 03:53:20.430 | window | 65.2 | 105.7 | 64.7 | 65.4 | 1667 | 1781 | 7.40 | 7.82 | 2.32 | 5.08 | 5.50 | 14760.8 | 1 | Default | best_performance |
|  | 03:53:21.427 | window | 60.2 | 102.4 | 61.2 | 59.8 | 1660 | 1717 | 7.06 | 7.23 | 2.37 | 4.69 | 4.86 | 14761.8 | 1 | Default | best_performance |

proc.csv rows (game process; each row covers the second before it):

| covers | wall | t_s | phase | cpu_cores | cpu_s | ws_mb | commit_mb | threads | handles | responding | log_lines | perf_csv_bytes | free_ram_gb | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  | 03:53:18.650 | 70.02 | measure | 2.77 | 164.13 | 705 | 1198 | 72 | 1296 | True | 91 | 1273710 | 13.10 |  |
|  | 03:53:19.640 | 71.01 | measure | 2.68 | 166.78 | 705 | 1198 | 72 | 1296 | True | 91 | 1290975 | 13.10 |  |
| Y | 03:53:20.630 | 72.00 | measure | 2.23 | 168.98 | 706 | 1198 | 72 | 1296 | True | 91 | 1302491 | 13.12 |  |
|  | 03:53:21.640 | 73.01 | measure | 2.40 | 171.41 | 706 | 1198 | 72 | 1296 | True | 91 | 1322647 | 13.12 |  |

gpu.csv (NVML, MX570; time = driver start + t_s):

| wall | dt to frame s | pstate | gr MHz | mem MHz | temp C | power W | util gpu | util mem | throttle |
|---|---|---|---|---|---|---|---|---|---|
| 03:53:18.694 | -1.36 | P0 | 832 | 6001 | 88 | 15.73 | 100 | 26 | 0x20 |
| 03:53:19.564 | -0.49 | P0 | 832 | 6001 | 88 | 15.71 | 100 | 25 | 0x20 |
| 03:53:20.634 | 0.58 | P0 | 832 | 6001 | 87 | 14.74 | 81 | 20 | 0x20 |
| 03:53:21.504 | 1.45 | P0 | 832 | 6001 | 88 | 14.75 | 100 | 26 | 0x20 |

game.log entries within 2 s of the frame: none

threads.csv top threads (whole window): 31084 Main XThread (F800002C) 79.6% (max 90.8%); 13236 GPU Commands (F8000018) 59.2% (max 76.4%); 13932 XThread366C (F80001A8) 53.5% (max 76.6%); 14132 rex::thread::TimerQueue 23.9% (max 37.4%); 22948  8.9% (max 16.1%); 20092 XThread4E7C (F8000144) 8.7% (max 12.9%)

### 3.2 Per run (scored W6 runs; cold runs listed last)

| pass | run | arm | frames | >16.7 | >33 | max ms | p99.9 ms | row conv | vs frames.json | spikes within 0.4 s of Toypad | Toypad ex. with a >16.7 ms frame | max ms within 0.4 s of each Toypad ex. | baseline 0.8 s bin max med / p90 | lag s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0009 | 0012-p2-r1 | p2 | 22087 | 0 | 0 | 6.00 | 5.62 | 0 | ok | 0/0 | 0/2 | 5.6 5.7 | 5.5 / 5.8 | 0.121 |
| 0009 | 0019-p2-r2 | p2 | 20116 | 0 | 0 | 6.22 | 5.63 | 0 | ok | 0/0 | 0/1 | 5.1 | 5.4 / 5.9 | 0.139 |
| 0009 | 0033-p2-r3 | p2 | 19252 | 0 | 0 | 6.29 | 5.66 | 0 | ok | 0/0 | 0/1 | 5.4 | 5.4 / 5.8 | 0.146 |
| 0009 | 0039-p2-r4 | p2 | 19093 | 0 | 0 | 9.51 | 5.95 | 0 | ok | 0/0 | 0/1 | 4.9 | 5.3 / 5.8 | 0.147 |
| 0009 | 0045-p2-r5 | p2 | 19278 | 0 | 0 | 6.40 | 5.70 | 0 | ok | 0/0 | 0/1 | 6.1 | 5.5 / 5.9 | 0.146 |
| 0313 | 0317-p2-r1 | p2 | 19711 | 0 | 0 | 6.12 | 5.58 | 0 | ok | 0/0 | 0/1 | 5.1 | 5.4 / 5.8 | 0.143 |
| 0313 | 0323-p2-r2 | p2 | 19279 | 0 | 0 | 6.09 | 5.56 | 0 | ok | 0/0 | 0/1 | 5.0 | 5.4 / 5.6 | 0.146 |
| 0313 | 0337-p2-r3 | p2 | 19195 | 0 | 0 | 12.60 | 7.98 | 0 | ok | 0/0 | 0/1 | 5.5 | 5.8 / 10.2 | 0.147 |
| 0313 | 0343-p2-r4 | p2 | 19263 | 0 | 0 | 8.30 | 5.66 | 0 | ok | 0/0 | 0/1 | 5.2 | 5.5 / 5.9 | 0.144 |
| 0313 | 0350-p2-r5 | p2 | 18775 | 0 | 0 | 7.65 | 5.71 | 0 | ok | 0/0 | 0/1 | 5.2 | 5.5 / 5.9 | 0.149 |
| 0009 | 0014-p2f-r1 | p2f | 21286 | 0 | 0 | 6.27 | 5.55 | 0 | ok | 0/0 | 0/1 | 5.1 | 5.4 / 5.8 | 0.130 |
| 0009 | 0021-p2f-r2 | p2f | 19392 | 0 | 0 | 7.66 | 5.55 | 0 | ok | 0/0 | 0/1 | 5.4 | 5.3 / 5.7 | 0.145 |
| 0009 | 0027-p2f-r3 | p2f | 19386 | 0 | 0 | 6.92 | 5.69 | 0 | ok | 0/0 | 0/1 | 5.5 | 5.4 / 6.0 | 0.144 |
| 0009 | 0041-p2f-r4 | p2f | 19342 | 0 | 0 | 11.73 | 5.51 | 0 | ok | 0/0 | 0/1 | 5.4 | 5.4 / 5.7 | 0.145 |
| 0009 | 0047-p2f-r5 | p2f | 19342 | 0 | 0 | 6.32 | 5.67 | 0 | ok | 0/0 | 0/1 | 5.4 | 5.5 / 5.8 | 0.145 |
| 0313 | 0319-p2f-r1 | p2f | 19387 | 0 | 0 | 6.59 | 5.58 | 0 | ok | 0/0 | 0/1 | 5.1 | 5.4 / 5.8 | 0.144 |
| 0313 | 0325-p2f-r2 | p2f | 19297 | 2 | 0 | 18.05 | 7.54 | 0 | ok | 0/2 | 0/1 | 5.5 | 5.6 / 12.0 | 0.144 |
| 0313 | 0331-p2f-r3 | p2f | 19296 | 0 | 0 | 14.43 | 8.11 | 0 | ok | 0/0 | 0/1 | 5.0 | 5.8 / 10.0 | 0.145 |
| 0313 | 0345-p2f-r4 | p2f | 19327 | 0 | 0 | 6.22 | 5.57 | 0 | ok | 0/0 | 0/1 | 5.6 | 5.3 / 5.9 | 0.146 |
| 0313 | 0352-p2f-r5 | p2f | 19258 | 9 | 1 | 45.67 | 6.40 | 0 | ok | 0/9 | 0/1 | 5.2 | 5.4 / 5.7 | 0.144 |
| 0009 | 0016-p2fc-r1 | p2fc | 23654 | 0 | 0 | 5.88 | 5.64 | 0 | ok | 0/0 | 0/2 | 5.6 5.4 | 5.5 / 5.8 | 0.126 |
| 0009 | 0023-p2fc-r2 | p2fc | 21347 | 0 | 0 | 9.11 | 6.25 | 0 | ok | 0/0 | 0/2 | 5.4 5.0 | 5.6 / 6.1 | 0.136 |
| 0009 | 0029-p2fc-r3 | p2fc | 23316 | 0 | 0 | 6.34 | 5.61 | 0 | ok | 0/0 | 0/2 | 5.6 5.7 | 5.5 / 5.8 | 0.126 |
| 0009 | 0035-p2fc-r4 | p2fc | 23561 | 0 | 0 | 6.14 | 5.68 | 0 | ok | 0/0 | 0/2 | 5.7 5.5 | 5.5 / 5.8 | 0.127 |
| 0009 | 0049-p2fc-r5 | p2fc | 22862 | 0 | 0 | 6.04 | 5.78 | 0 | ok | 0/0 | 0/2 | 5.7 5.8 | 5.5 / 5.9 | 0.129 |
| 0313 | 0321-p2fc-r1 | p2fc | 23564 | 0 | 0 | 6.21 | 5.69 | 0 | ok | 0/0 | 0/2 | 5.5 6.0 | 5.6 / 5.9 | 0.124 |
| 0313 | 0327-p2fc-r2 | p2fc | 23514 | 0 | 0 | 16.05 | 7.24 | 0 | ok | 0/0 | 0/2 | 10.6 9.7 | 5.8 / 10.1 | 0.128 |
| 0313 | 0333-p2fc-r3 | p2fc | 23403 | 0 | 0 | 13.85 | 6.49 | 0 | ok | 0/0 | 0/2 | 5.2 6.0 | 5.8 / 10.2 | 0.126 |
| 0313 | 0339-p2fc-r4 | p2fc | 22576 | 0 | 0 | 10.79 | 6.85 | 0 | ok | 0/0 | 0/2 | 6.4 5.3 | 5.7 / 8.5 | 0.130 |
| 0313 | 0354-p2fc-r5 | p2fc | 23492 | 0 | 0 | 6.14 | 5.65 | 0 | ok | 0/0 | 0/2 | 5.8 5.3 | 5.4 / 5.9 | 0.126 |
| 0009 | 0010-s0-r1 | s0 | 22304 | 0 | 0 | 6.91 | 5.54 | 0 | ok | 0/0 | 0/2 | 5.1 5.0 | 5.3 / 5.8 | 0.123 |
| 0009 | 0025-s0-r2 | s0 | 18404 | 0 | 0 | 9.69 | 5.78 | 0 | ok | 0/0 | 0/2 | 5.8 5.8 | 5.5 / 6.0 | 0.154 |
| 0009 | 0031-s0-r3 | s0 | 19245 | 0 | 0 | 9.48 | 6.15 | 0 | ok | 0/0 | 0/1 | 5.1 | 5.7 / 6.7 | 0.144 |
| 0009 | 0037-s0-r4 | s0 | 19258 | 0 | 0 | 7.11 | 6.36 | 0 | ok | 0/0 | 0/1 | 6.5 | 6.1 / 6.5 | 0.143 |
| 0009 | 0043-s0-r5 | s0 | 19259 | 0 | 0 | 6.52 | 5.68 | 0 | ok | 0/0 | 0/1 | 5.4 | 5.4 / 5.9 | 0.145 |
| 0313 | 0315-s0-r1 | s0 | 20868 | 0 | 0 | 8.53 | 5.54 | 0 | ok | 0/0 | 0/2 | 5.5 4.8 | 5.3 / 5.9 | 0.134 |
| 0313 | 0329-s0-r2 | s0 | 19097 | 1 | 0 | 17.35 | 8.95 | 0 | ok | 0/1 | 0/1 | 5.6 | 6.7 / 12.2 | 0.146 |
| 0313 | 0335-s0-r3 | s0 | 19185 | 0 | 0 | 16.09 | 8.30 | 0 | ok | 0/0 | 0/1 | 7.1 | 5.8 / 10.2 | 0.146 |
| 0313 | 0341-s0-r4 | s0 | 19252 | 0 | 0 | 6.64 | 5.59 | 0 | ok | 0/0 | 0/1 | 5.3 | 5.4 / 5.8 | 0.146 |
| 0313 | 0348-s0-r5 | s0 | 19279 | 0 | 0 | 7.66 | 5.74 | 0 | ok | 0/0 | 0/1 | 5.9 | 5.5 / 6.0 | 0.146 |
| 0009 | 0009-cold-s0 (unscored) | cold-s0 | 11985 | 0 | 0 | 8.60 | 6.25 | 0 | ok | 0/0 | 0/1 | 6.1 | 5.4 / 7.1 | 0.140 |
| 0313 | 0313-cold-s0 (unscored) | cold-s0 | 13448 | 0 | 0 | 11.36 | 8.21 | 0 | ok | 0/0 | 0/1 | 7.7 | 7.3 / 10.1 | 0.117 |

### 3.3 Every frame over 16.7 ms (scored W6 runs: 12 frames in 3 runs; cold runs: 0)

| pass | run | arm | win frame # | data row | T start s | T end s | ms | est. wall | sys sample | P util | E MHz | ng_t | ng_u | game | proc cores | pipe miss | tex miss | cb stalls | crit cont | nearest Toypad dt s | nearest game.log line dt s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0313 | 0325-p2f-r2 | p2f | 6278 | 30698 | 16.330 | 16.348 | 18.05 | 03:26:43.350 | 03:26:43 | 62.9 | 1990 | 2.91 | 3.85 | 2.45 | 2.44 | 0 | 0 | 0 | 0 | 13.685 | 13.685 Toypad[Write] 0B 16 55 0A B1 09 8C 9C CC |
| 0313 | 0325-p2f-r2 | p2f | 10912 | 35332 | 28.327 | 28.344 | 16.99 | 03:26:55.346 | 03:26:55 | 62.8 | 1915 | 3.16 | 3.94 | 2.55 | 2.55 | 0 | 0 | 0 | 0 | 1.689 | 1.689 Toypad[Write] 0B 16 55 0A B1 09 8C 9C CC |
| 0313 | 0352-p2f-r5 | p2f | 2849 | 27329 | 7.443 | 7.489 | 45.67 | 03:53:20.057 | 03:53:20 | 64.7 | 1781 | 5.08 | 5.50 | 2.32 | 2.23 | 0 | 0 | 0 | 0 | -8.778 | -8.771 Toypad[Write] 0B 16 55 0A B3 08 0D C4 3F |
| 0313 | 0352-p2f-r5 | p2f | 2864 | 27344 | 7.575 | 7.601 | 25.70 | 03:53:20.169 | 03:53:20 | 64.7 | 1781 | 5.08 | 5.50 | 2.32 | 2.23 | 0 | 0 | 0 | 0 | -8.890 | -8.883 Toypad[Write] 0B 16 55 0A B3 08 0D C4 3F |
| 0313 | 0352-p2f-r5 | p2f | 2876 | 27356 | 7.628 | 7.652 | 24.17 | 03:53:20.220 | 03:53:20 | 64.7 | 1781 | 5.08 | 5.50 | 2.32 | 2.23 | 0 | 0 | 0 | 0 | -8.941 | -8.934 Toypad[Write] 0B 16 55 0A B3 08 0D C4 3F |
| 0313 | 0352-p2f-r5 | p2f | 2932 | 27412 | 7.831 | 7.850 | 19.05 | 03:53:20.418 | 03:53:20* | 64.7 | 1781 | 5.08 | 5.50 | 2.32 | 2.23 | 0 | 0 | 0 | 0 | -9.139 | -9.132 Toypad[Write] 0B 16 55 0A B3 08 0D C4 3F |
| 0313 | 0352-p2f-r5 | p2f | 2933 | 27413 | 7.850 | 7.874 | 23.83 | 03:53:20.441 | 03:53:21* | 61.2 | 1717 | 4.69 | 4.86 | 2.37 | 2.23 | 0 | 0 | 0 | 0 | -9.162 | -9.155 Toypad[Write] 0B 16 55 0A B3 08 0D C4 3F |
| 0313 | 0352-p2f-r5 | p2f | 2934 | 27414 | 7.874 | 7.901 | 27.47 | 03:53:20.469 | 03:53:21* | 61.2 | 1717 | 4.69 | 4.86 | 2.37 | 2.23 | 0 | 0 | 0 | 0 | -9.190 | -9.183 Toypad[Write] 0B 16 55 0A B3 08 0D C4 3F |
| 0313 | 0352-p2f-r5 | p2f | 2945 | 27425 | 7.930 | 7.950 | 20.20 | 03:53:20.518 | 03:53:21 | 61.2 | 1717 | 4.69 | 4.86 | 2.37 | 2.23 | 0 | 0 | 0 | 0 | -9.239 | -9.232 Toypad[Write] 0B 16 55 0A B3 08 0D C4 3F |
| 0313 | 0352-p2f-r5 | p2f | 2947 | 27427 | 7.959 | 7.980 | 20.54 | 03:53:20.548 | 03:53:21 | 61.2 | 1717 | 4.69 | 4.86 | 2.37 | 2.23 | 0 | 0 | 0 | 0 | -9.269 | -9.262 Toypad[Write] 0B 16 55 0A B3 08 0D C4 3F |
| 0313 | 0352-p2f-r5 | p2f | 2948 | 27428 | 7.980 | 8.004 | 24.56 | 03:53:20.572 | 03:53:21 | 61.2 | 1717 | 4.69 | 4.86 | 2.37 | 2.23 | 0 | 0 | 0 | 0 | -9.293 | -9.286 Toypad[Write] 0B 16 55 0A B3 08 0D C4 3F |
| 0313 | 0329-s0-r2 | s0 | 10661 | 35201 | 28.088 | 28.105 | 17.35 | 03:31:02.295 | 03:31:03 | 67.2 | 2049 | 2.11 | 3.11 | 2.41 | 2.41 | 0 | 0 | 0 | 0 | 2.074 | 2.074 Toypad[Write] 0B 16 55 0A B1 09 9A 55 8C |

(* = the lag range spans two sys.csv samples.) Toypad exchange = game.log Toypad[Write]/[Read] lines within 0.25 s; dt = log time - frame estimate (positive: the log line is later).

Per arm and pass (scored): 0009 p2: 5 runs, 0 frames >16.7 ms, 0 >33 ms (of 99826 frames); 0313 p2: 5 runs, 0 frames >16.7 ms, 0 >33 ms (of 96223 frames); 0009 p2f: 5 runs, 0 frames >16.7 ms, 0 >33 ms (of 98748 frames); 0313 p2f: 5 runs, 11 frames >16.7 ms, 1 >33 ms (of 96565 frames); 0009 p2fc: 5 runs, 0 frames >16.7 ms, 0 >33 ms (of 114740 frames); 0313 p2fc: 5 runs, 0 frames >16.7 ms, 0 >33 ms (of 116549 frames); 0009 s0: 5 runs, 0 frames >16.7 ms, 0 >33 ms (of 98470 frames); 0313 s0: 5 runs, 1 frames >16.7 ms, 0 >33 ms (of 97681 frames)

## 4. game.log, dumps and crash markers (all runs, all 7 folders)

Per run: game.log lines; levels from the `[time] [level] [cat]` prefix; STUCK = any line containing "stuck" (case-insensitive), STUCK-LOCK owner site parsed from site=/owner= if present; [error]/[critical] by level or literal tag; hang = \bhang(s|ing|ed)?\b or \bhung\b; alarm = exception/access violation/fatal/assert/abort/deadlock/watchdog/crash. .dmp/.mdmp/.hdmp searched in the run dir, user\ and user\* (one level). run.json werfault_seen / foreign_crash_dumps.

| window | folder | runs | game.log | lines | info | warning | [error] | [critical] | STUCK | STUCK-LOCK | owner sites | hang | alarm | other levels | .dmp | werfault_seen | foreign dumps | driver.err non-empty |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| W6-1 | 20261123-0009 | 21 | 21 | 2290 | 1282 | 840 | 0 | 0 | 0 | 0 | - | 0 | 0 | - | 0 | 0 | 0 | 0 |
| W9-1 | 20261123-0108 | 21 | 21 | 2096 | 1087 | 841 | 0 | 0 | 0 | 0 | - | 0 | 0 | - | 0 | 0 | 0 | 0 |
| W5b-1 | 20261123-0155 | 19 | 19 | 1906 | 994 | 760 | 0 | 0 | 0 | 0 | - | 0 | 0 | - | 0 | 0 | 0 | 0 |
| W4c | 20261123-0239 | 13 | 13 | 1286 | 662 | 520 | 0 | 0 | 0 | 0 | - | 0 | 0 | - | 0 | 0 | 0 | 0 |
| W6-2 | 20261123-0313 | 21 | 21 | 2270 | 1262 | 840 | 0 | 0 | 0 | 0 | - | 0 | 0 | - | 0 | 0 | 0 | 0 |
| W9-2 | 20261123-0401 | 21 | 21 | 2101 | 1093 | 840 | 0 | 0 | 0 | 0 | - | 0 | 0 | - | 0 | 0 | 0 | 0 |
| W5b-2 | 20261123-0451 | 19 | 19 | 1910 | 998 | 760 | 0 | 0 | 0 | 0 | - | 0 | 0 | - | 0 | 0 | 0 | 0 |

Example lines for non-zero categories: none (no stuck/error/critical/hang/alarm line in any game.log).

sys.err.txt distinct lines (runs): "sys-csv: counters failed at init: tz_temp:no_data tz_passive:no_data" (135)

Runner logs (`logs/*.txt`, text only) keyword counts per folder, with examples:

| window | folder | files | lines | stuck | dmp/dump | crash | hang/hung | error | critical | werfault | exception | CrossDevice/gate | .dmp (root/logs) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| W6-1 | 20261123-0009 | 21 | 2151 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| W9-1 | 20261123-0108 | 21 | 2151 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| W5b-1 | 20261123-0155 | 19 | 1945 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| W4c | 20261123-0239 | 13 | 1327 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| W6-2 | 20261123-0313 | 21 | 2151 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| W9-2 | 20261123-0401 | 21 | 2151 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| W5b-2 | 20261123-0451 | 19 | 1945 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - |

## 5. Follow-up items (Agent 8, 11:57Z)

Sources per run: sys.csv (host, 1 s), proc.csv (legodimensions.exe only, 1 s; its free_ram_gb is system-wide), gpu.csv (NVML, window only, ~1.07 s), perf.csv (per frame). **There is no per-process data for other processes and no disk counter in the matrix folders**, so a non-game process cannot be named from these files; the proxies are ng_t/ng_u (host CPU minus game), free RAM, P/E clocks, the GPU state and the game's own counters. Frame counts use T end (summed frame_time_us from the window start) in 10 s bins; per-second rows map each frame to the sys sample containing measure_start + T end - lag/2. "A8 >6" = Agent 8's count from mine/*.md, for checking. thermal % = share of GPU samples with an NVML thermal throttle bit (0x20 SW / 0x40 HW).

### 5.1 W6-2 (0313) tail episode 03:24-03:40: the 8 EP runs vs the other 12 scored runs

| # | run | win wall | fps | fps_rel | >6/>10/>16.7 | A8 >6 | max ms | ng_t mean | ng_t max | ng_u mean | bursts | wu ng_t | P util | P MHz | E MHz | game | threads/handles | commit MB | free GB min | GPU MHz (min) | GPU C mean/max | GPU W | GPU util | thermal % | pipe all/>6fr | batt % | build procs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0313-cold-s0 (unscored) | 03:14:27-03:14:57 | 448.3 | - | 39/5/0 |  | 11.36 | 2.37 | 3.40 | 3.39 | - | 1.77 | 66.7 | 2057 | 2045 | 2.40 | 72/1292 | 1197 | 13.14 | - (-) | -/- | - | - | - | 0/0 | 98-98 | [] |
| 2 | 0315-s0-r1 | 03:16:09-03:16:59 | 417.3 | 1.084 | 3/0/0 |  | 8.53 | 2.62 | 4.67 | 3.50 | 8 | 2.36 | 64.0 | 1972 | 1983 | 2.49 | 72/1294 | 1195 | 12.90 | 1069 (832) | 86.7/87 | 17.30 | 95.3 | 100 | 0/0 | 99-99 | [] |
| 3 | 0317-p2-r1 | 03:18:13-03:19:03 | 394.2 | 1.023 | 1/0/0 |  | 6.12 | 2.46 | 4.04 | 3.34 | 4 | 2.28 | 64.8 | 1977 | 1990 | 2.55 | 72/1297 | 1193 | 13.08 | 884 (832) | 86.2/87 | 15.79 | 98.9 | 100 | 0/0 | 99-99 | [] |
| 4 | 0319-p2f-r1 | 03:20:16-03:21:06 | 387.7 | 1.005 | 5/0/0 |  | 6.59 | 2.44 | 3.66 | 3.34 | 3 | 2.40 | 62.9 | 1969 | 1996 | 2.56 | 72/1297 | 1199 | 13.07 | 832 (832) | 86.3/87 | 15.48 | 99.5 | 100 | 0/0 | 99-99 | [] |
| 5 | 0321-p2fc-r1 | 03:22:20-03:23:10 | 471.3 | 1.003 | 2/0/0 |  | 6.21 | 2.26 | 4.24 | 3.42 | 2 | 2.51 | 65.8 | 2120 | 2105 | 2.27 | 72/1297 | 1196 | 13.07 | 832 (832) | 87.5/88 | 16.38 | 88.4 | 100 | 0/0 | 99-99 | [] |
| 6 | 0323-p2-r2 | 03:24:23-03:25:13 | 385.6 | 1.001 | 1/0/0 |  | 6.09 | 2.50 | 3.68 | 3.34 | 6 | 2.37 | 64.2 | 1950 | 1973 | 2.57 | 72/1297 | 1196 | 13.04 | 832 (832) | 87.0/87 | 15.55 | 99.9 | 100 | 0/0 | 99-99 | [] |
| 7 | 0325-p2f-r2 EP | 03:26:27-03:27:17 | 385.9 | 1.000 | 33/11/2 | 33 | 18.05 | 2.57 | 3.95 | 3.45 | 8 | 2.71 | 63.9 | 1968 | 1979 | 2.52 | 72/1298 | 1202 | 13.03 | 832 (832) | 87.0/87 | 15.62 | 99.6 | 100 | 0/0 | 100-100 | [] |
| 8 | 0327-p2fc-r2 EP | 03:28:30-03:29:20 | 470.3 | 1.001 | 40/7/0 | 40 | 16.05 | 2.39 | 3.95 | 3.52 | 3 | 2.38 | 65.0 | 2083 | 2084 | 2.29 | 72/1294 | 1193 | 13.10 | 832 (832) | 88.0/88 | 16.48 | 86.6 | 100 | 0/0 | 100-100 | [] |
| 9 | 0329-s0-r2 EP | 03:30:34-03:31:24 | 381.9 | 0.992 | 58/12/1 | 58 | 17.35 | 2.61 | 4.62 | 3.46 | 5 | 2.34 | 64.9 | 1952 | 1971 | 2.52 | 72/1295 | 1204 | 13.02 | 832 (832) | 87.6/88 | 15.64 | 99.5 | 100 | 0/0 | 100-100 | [] |
| 10 | 0331-p2f-r3 EP | 03:32:37-03:33:27 | 385.9 | 1.000 | 40/7/0 | 40 | 14.43 | 2.46 | 3.44 | 3.34 | 1 | 2.47 | 64.1 | 1973 | 1976 | 2.56 | 72/1297 | 1195 | 13.08 | 832 (832) | 87.5/88 | 15.68 | 99.6 | 100 | 0/0 | 100-100 | [] |
| 11 | 0333-p2fc-r3 EP | 03:34:41-03:35:31 | 468.1 | 0.996 | 34/7/0 | 34 | 13.85 | 2.39 | 3.90 | 3.53 | 1 | 2.34 | 66.1 | 2099 | 2094 | 2.25 | 72/1299 | 1190 | 13.08 | 832 (832) | 88.3/89 | 16.54 | 88.8 | 100 | 0/0 | 100-100 | [] |
| 12 | 0335-s0-r3 EP | 03:36:44-03:37:34 | 383.7 | 0.997 | 44/8/0 | 44 | 16.09 | 2.71 | 5.17 | 3.52 | 10 | 2.61 | 62.7 | 1934 | 1961 | 2.50 | 72/1297 | 1195 | 13.07 | 832 (832) | 88.0/88 | 15.69 | 99.7 | 100 | 0/0 | 100-100 | [] |
| 13 | 0337-p2-r3 EP | 03:38:48-03:39:38 | 383.9 | 0.996 | 40/7/0 | 40 | 12.60 | 2.55 | 4.64 | 3.38 | 3 | 2.63 | 62.5 | 1951 | 1965 | 2.56 | 72/1298 | 1196 | 13.11 | 832 (832) | 87.8/88 | 15.69 | 99.6 | 100 | 0/0 | 100-100 | [] |
| 14 | 0339-p2fc-r4 EP | 03:40:51-03:41:41 | 451.5 | 0.961 | 34/3/0 | 34 | 10.79 | 2.96 | 8.17 | 3.89 | 13 | 2.45 | 65.5 | 2003 | 2008 | 2.22 | 72/1296 | 1191 | 13.07 | 832 (832) | 88.3/89 | 16.35 | 86.5 | 100 | 0/0 | 100-100 | [] |
| 15 | 0341-s0-r4 | 03:42:54-03:43:44 | 385.0 | 1.000 | 3/0/0 |  | 6.64 | 2.55 | 4.66 | 3.37 | 4 | 2.44 | 64.3 | 1946 | 1951 | 2.57 | 72/1299 | 1203 | 13.08 | 832 (832) | 88.0/88 | 15.75 | 99.5 | 100 | 0/0 | 100-100 | [] |
| 16 | 0343-p2-r4 | 03:44:58-03:45:48 | 385.2 | 1.000 | 6/0/0 |  | 8.30 | 2.52 | 4.56 | 3.41 | 4 | 2.48 | 64.8 | 1979 | 1978 | 2.44 | 72/1294 | 1199 | 13.09 | 832 (832) | 88.0/88 | 15.73 | 99.6 | 100 | 0/0 | 100-100 | [] |
| 17 | 0345-p2f-r4 | 03:47:01-03:47:51 | 386.5 | 1.002 | 2/0/0 |  | 6.22 | 2.54 | 4.22 | 3.35 | 6 | 2.45 | 62.8 | 1935 | 1962 | 2.61 | 72/1301 | 1193 | 13.02 | 832 (832) | 88.0/88 | 15.74 | 99.4 | 100 | 0/0 | 100-100 | [] |
| 18 | 0348-s0-r5 | 03:49:05-03:49:55 | 385.6 | 1.001 | 5/0/0 |  | 7.66 | 2.40 | 4.17 | 3.28 | 1 | 2.52 | 63.3 | 1972 | 1991 | 2.56 | 72/1297 | 1203 | 13.08 | 832 (832) | 88.0/88 | 15.70 | 99.8 | 100 | 0/0 | 100-100 | [] |
| 19 | 0350-p2-r5 | 03:51:09-03:51:59 | 375.5 | 0.975 | 6/0/0 |  | 7.65 | 2.91 | 5.52 | 3.63 | 11 | 2.56 | 64.1 | 1909 | 1934 | 2.51 | 72/1295 | 1197 | 13.05 | 832 (832) | 87.9/88 | 15.62 | 98.2 | 100 | 0/0 | 100-100 | [] |
| 20 | 0352-p2f-r5 | 03:53:12-03:54:02 | 385.1 | 0.998 | 21/14/9 | 21 (all 0-10) | 45.67 | 2.55 | 5.08 | 3.41 | 3 | 2.46 | 64.1 | 1962 | 1974 | 2.51 | 72/1296 | 1198 | 13.09 | 832 (832) | 87.9/88 | 15.72 | 99.5 | 100 | 0/0 | 100-100 | [] |
| 21 | 0354-p2fc-r5 | 03:55:16-03:56:06 | 469.8 | 1.000 | 3/0/0 |  | 6.14 | 2.44 | 4.01 | 3.54 | 3 | 2.32 | 66.1 | 2089 | 2080 | 2.25 | 72/1296 | 1190 | 13.08 | 832 (832) | 88.6/89 | 16.63 | 88.1 | 100 | 0/0 | 100-100 | [] |

EP (n=8) vs other scored runs (n=12): median [min..max], difference of medians, two-sided permutation p (5000 perms), separation:

| metric | EP | other | diff | perm p | separation |
|---|---|---|---|---|---|
| >6 ms frames | 40 [33..58] | 3 [1..21] | 37 | 0.001 | all EP > all other |
| >10 ms frames | 7 [3..12] | 0 [0..14] | 7 | 0.171 | - |
| max frame ms | 15.24 [10.79..18.05] | 6.61 [6.09..45.67] | 8.63 | 0.003 | - |
| fps_rel | 0.997 [0.961..1.001] | 1.001 [0.975..1.084] | -0.005 | 0.005 | - |
| ng_t mean | 2.56 [2.39..2.96] | 2.51 [2.26..2.91] | 0.05 | 0.524 | - |
| ng_t 1 s max | 4.29 [3.44..8.17] | 4.23 [3.66..5.52] | 0.05 | 0.980 | - |
| ng_u mean | 3.49 [3.34..3.89] | 3.39 [3.28..3.63] | 0.10 | 0.137 | - |
| ng_t bursts | 4 [1..13] | 4 [1..11] | 0 | 1.000 | - |
| warm-up ng_t | 2.46 [2.34..2.71] | 2.45 [2.28..2.56] | 0.02 | 0.758 | - |
| P util % | 64.5 [62.5..66.1] | 64.2 [62.8..66.1] | 0.4 | 0.585 | - |
| E util % | 42.5 [39.2..43.9] | 41.9 [38.2..44.7] | 0.6 | 0.375 | - |
| P MHz | 1970 [1934..2099] | 1971 [1909..2120] | -0 | 0.998 | - |
| E MHz | 1978 [1961..2094] | 1981 [1934..2105] | -3 | 0.893 | - |
| game cores | 2.51 [2.22..2.56] | 2.53 [2.25..2.61] | -0.02 | 0.548 | - |
| game threads | 72 [72..72] | 72 [72..72] | 0 | 1.000 | - |
| game handles | 1297 [1294..1299] | 1297 [1294..1301] | 0 | 0.699 | - |
| game commit MB | 1195 [1190..1204] | 1197 [1190..1203] | -2 | 0.400 | - |
| free RAM GB min | 13.07 [13.02..13.11] | 13.07 [12.90..13.09] | 0.00 | 1.000 | - |
| GPU MHz mean | 832 [832..832] | 832 [832..1069] | 0 | 1.000 | - |
| GPU MHz min | 832 [832..832] | 832 [832..832] | 0 | 1.000 | - |
| GPU temp C | 87.9 [87.0..88.3] | 87.9 [86.2..88.6] | -0.0 | 0.983 | - |
| GPU power W | 15.69 [15.62..16.54] | 15.74 [15.48..17.30] | -0.05 | 0.444 | - |
| GPU util % | 99.5 [86.5..99.7] | 99.4 [88.1..99.9] | 0.1 | 0.752 | - |
| GPU thermal-throttle share | 1.00 [1.00..1.00] | 1.00 [1.00..1.00] | 0.00 | 1.000 | - |
| pipeline misses | 0 [0..0] | 0 [0..0] | 0 | 1.000 | - |
| texture misses | 0 [0..0] | 0 [0..0] | 0 | 1.000 | - |
| cb stalls | 11688 [321..12417] | 11900 [472..13075] | -212 | 0.661 | - |
| crit contentions | 0 [0..0] | 0 [0..0] | 0 | 1.000 | - |
| interrupt_dispatches /s | 4473.4 [4437.7..5232.7] | 4474.7 [4379.7..5241.8] | -1.3 | 0.958 | - |

Spearman across the 20 scored runs, >6 ms frame count vs: fps_rel rho -0.69 (p 0.000); ng_t mean rho 0.31 (p 0.192); ng_t 1 s max rho 0.16 (p 0.502); ng_u mean rho 0.38 (p 0.094); ng_t bursts rho -0.02 (p 0.934); warm-up ng_t rho 0.31 (p 0.175); P util % rho -0.10 (p 0.695); E util % rho 0.23 (p 0.341); P MHz rho -0.05 (p 0.827); E MHz rho -0.11 (p 0.646); game cores rho -0.24 (p 0.334); game threads rho - (p -); game handles rho -0.10 (p 0.638); game commit MB rho 0.07 (p 0.762); free RAM GB min rho 0.23 (p 0.336); GPU MHz mean rho -0.39 (p 0.099); GPU MHz min rho - (p -); GPU temp C rho 0.24 (p 0.327); GPU power W rho -0.19 (p 0.404); GPU util % rho 0.07 (p 0.776); GPU thermal-throttle share rho - (p -); pipeline misses rho - (p -); texture misses rho - (p -); cb stalls rho -0.12 (p 0.604); crit contentions rho - (p -); interrupt_dispatches /s rho -0.33 (p 0.177)

Per second (window seconds with >= 50 frames): seconds containing a >6 ms frame vs the other seconds. Pooled medians, the median of the per-run differences, runs with difference >0 / <0 and a two-sided sign test across runs (seconds within a run are autocorrelated, so no pooled p). Keys: ngB = ng_t, ngU = ng_u, gutil/gr/temp = GPU util/MHz/C, pcores = game cores (proc.csv), free = free RAM GB, intr = interrupt_dispatches summed over the frames of that second.

EP runs (213 spike seconds, 187 other seconds):

| metric (per s) | seconds with >6 ms frame: median | other seconds: median | median per-run diff | runs diff >0 / <0 | sign p |
|---|---|---|---|---|---|
| ngB | 2.49 | 2.40 | 0.07 | 5/3 | 0.727 |
| ngU | 3.45 | 3.36 | 0.09 | 6/2 | 0.289 |
| p_util | 64.39 | 64.30 | 0.05 | 5/3 | 0.727 |
| e_util | 41.18 | 40.63 | 1.01 | 5/3 | 0.727 |
| p_eff | 2000.50 | 2013.00 | 1.25 | 4/4 | 1.000 |
| e_eff | 2011.00 | 2015.00 | 12.00 | 6/2 | 0.289 |
| game | 2.43 | 2.45 | -0.03 | 3/5 | 0.727 |
| gutil | 100.00 | 100.00 | 0.00 | 2/1 | 1.000 |
| gr | 832.00 | 832.00 | 0.00 | 0/0 | - |
| temp | 88.00 | 88.00 | 0.00 | 1/1 | 1.000 |
| pcores | 2.43 | 2.43 | -0.01 | 3/5 | 0.727 |
| free | 13.09 | 13.08 | 0.00 | 1/0 | 1.000 |
| intr | 4485.00 | 4525.00 | -24.25 | 0/8 | 0.008 |

All 20 scored 0313 runs (249 spike seconds, 751 other seconds); pooled per-second Spearman of the >6 ms count vs ng_t: rho 0.105 (n=999):

| metric (per s) | seconds with >6 ms frame: median | other seconds: median | median per-run diff | runs diff >0 / <0 | sign p |
|---|---|---|---|---|---|
| ngB | 2.49 | 2.40 | 0.07 | 11/9 | 0.824 |
| ngU | 3.47 | 3.34 | 0.09 | 13/7 | 0.263 |
| p_util | 64.39 | 64.33 | 0.24 | 13/7 | 0.263 |
| e_util | 41.31 | 40.43 | 1.01 | 11/9 | 0.824 |
| p_eff | 1998.00 | 1997.00 | -12.00 | 8/12 | 0.503 |
| e_eff | 2008.50 | 1999.00 | 8.50 | 12/8 | 0.503 |
| game | 2.44 | 2.49 | -0.02 | 9/11 | 0.824 |
| gutil | 100.00 | 100.00 | 0.00 | 3/5 | 0.727 |
| gr | 832.00 | 832.00 | 0.00 | 1/0 | 1.000 |
| temp | 88.00 | 88.00 | 0.00 | 1/4 | 0.375 |
| pcores | 2.44 | 2.48 | -0.01 | 8/11 | 0.648 |
| free | 13.09 | 13.09 | 0.00 | 4/1 | 0.375 |
| intr | 4484.00 | 4505.00 | -23.00 | 4/16 | 0.012 |

### 5.2 W4c (0239): 0251-B-r3 (burst at 30-40 s) and 0253-B-r4 (spread) vs the other scored runs

| # | run | win wall | fps | fps_rel | >6/>10/>16.7 | A8 >6 | max ms | ng_t mean | ng_t max | ng_u mean | bursts | wu ng_t | P util | P MHz | E MHz | game | threads/handles | commit MB | free GB min | GPU MHz (min) | GPU C mean/max | GPU W | GPU util | thermal % | pipe all/>6fr | batt % | build procs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0239-cold-d0 (unscored) | 02:40:51-02:41:21 | 426.5 | - | 14/3/0 |  | 10.99 | 2.94 | 5.40 | 3.66 | - | 1.77 | 64.4 | 1929 | 1921 | 2.49 | 72/1296 | 1196 | 13.18 | - (-) | -/- | - | - | - | 0/0 | 100-100 | [] |
| 2 | 0241-d0-r1 | 02:42:32-02:43:22 | 421.8 | 1.095 | 1/0/0 |  | 6.03 | 2.47 | 4.04 | 3.36 | 2 | 2.42 | 63.7 | 1972 | 1988 | 2.52 | 72/1302 | 1194 | 13.11 | 1021 (832) | 86.7/87 | 16.81 | 98.2 | 100 | 0/0 | 100-100 | [] |
| 3 | 0243-B-r1 | 02:44:35-02:45:25 | 388.5 | 1.012 | 2/0/0 |  | 7.39 | 2.52 | 4.29 | 3.36 | 3 | 2.43 | 64.7 | 1965 | 1980 | 2.55 | 72/1299 | 1198 | 13.10 | 855 (832) | 86.1/87 | 15.56 | 99.3 | 100 | 0/0 | 100-100 | [] |
| 4 | 0245-B-r2 | 02:46:38-02:47:28 | 383.9 | 1.000 | 1/0/0 |  | 6.08 | 2.58 | 4.90 | 3.39 | 5 | 2.97 | 64.5 | 1954 | 1958 | 2.56 | 72/1299 | 1193 | 13.09 | 832 (832) | 86.8/87 | 15.43 | 99.7 | 100 | 0/0 | 100-100 | [] |
| 5 | 0247-d0-r2 | 02:48:40-02:49:30 | 385.0 | 0.999 | 3/0/0 |  | 7.08 | 2.44 | 4.14 | 3.31 | 4 | 2.79 | 62.7 | 1980 | 1979 | 2.53 | 72/1294 | 1199 | 13.07 | 832 (832) | 87.0/87 | 15.48 | 99.8 | 100 | 0/0 | 100-100 | [] |
| 6 | 0249-d0-r3 | 02:50:43-02:51:33 | 386.4 | 1.003 | 1/0/0 |  | 6.08 | 2.48 | 4.08 | 3.36 | 3 | 2.37 | 64.9 | 1965 | 1979 | 2.51 | 72/1298 | 1198 | 13.06 | 832 (832) | 87.0/87 | 15.58 | 99.6 | 100 | 0/0 | 100-100 | [] |
| 7 | 0251-B-r3 FOCUS | 02:52:46-02:53:36 | 383.4 | 0.999 | 22/15/5 | 22 (20 in 30-40) | 20.66 | 2.56 | 5.16 | 3.32 | 7 | 2.45 | 63.9 | 1921 | 1937 | 2.60 | 72/1298 | 1194 | 13.09 | 832 (832) | 87.0/87 | 15.56 | 99.8 | 100 | 0/0 | 100-100 | [] |
| 8 | 0253-B-r4 FOCUS | 02:54:48-02:55:38 | 382.0 | 0.995 | 35/7/0 | 35 (8/2/12/9/4) | 14.07 | 3.09 | 5.28 | 3.61 | 21 | 2.42 | 62.1 | 1823 | 1837 | 2.70 | 72/1295 | 1195 | 13.07 | 832 (832) | 87.0/87 | 15.54 | 99.2 | 100 | 0/0 | 100-100 | [] |
| 9 | 0255-d0-r4 | 02:56:51-02:57:41 | 385.0 | 0.999 | 6/1/0 |  | 10.26 | 2.45 | 3.90 | 3.31 | 2 | 2.71 | 62.8 | 1951 | 1977 | 2.54 | 72/1301 | 1204 | 13.07 | 832 (832) | 87.1/88 | 15.61 | 99.8 | 100 | 0/0 | 100-100 | [] |
| 10 | 0257-d0-r5 | 02:58:53-02:59:43 | 385.1 | 0.999 | 3/0/0 |  | 6.25 | 2.52 | 3.98 | 3.33 | 3 | 2.34 | 62.6 | 1933 | 1957 | 2.59 | 72/1296 | 1193 | 13.08 | 832 (832) | 87.4/88 | 15.61 | 99.5 | 100 | 0/0 | 100-100 | [] |
| 11 | 0259-B-r5 | 03:00:56-03:01:46 | 383.9 | 1.000 | 2/0/0 |  | 6.05 | 2.62 | 5.13 | 3.41 | 5 | 2.75 | 63.9 | 1930 | 1947 | 2.57 | 72/1297 | 1198 | 13.04 | 832 (832) | 87.4/88 | 15.59 | 99.6 | 100 | 0/0 | 100-100 | [] |
| 12 | 0301-B-r6 | 03:02:59-03:03:49 | 385.9 | 1.005 | 0/0/0 |  | 5.99 | 2.45 | 4.30 | 3.26 | 3 | 2.41 | 62.7 | 1935 | 1966 | 2.61 | 72/1298 | 1199 | 13.10 | 832 (832) | 87.6/88 | 15.63 | 99.9 | 100 | 0/0 | 100-100 | [] |
| 13 | 0303-d0-r6 | 03:05:03-03:05:53 | 385.6 | 1.001 | 3/0/0 |  | 6.45 | 2.43 | 4.13 | 3.33 | 2 | 2.26 | 64.6 | 1986 | 2000 | 2.50 | 72/1301 | 1196 | 13.10 | 832 (832) | 87.7/88 | 15.65 | 99.7 | 100 | 0/0 | 100-100 | [] |

Value (rank among the 12 scored runs, 1 = highest) of each focus run, and the other runs' median [min..max]:

| metric | 0251-B-r3 | 0253-B-r4 | other runs |
|---|---|---|---|
| >6 ms frames | 22 (2) | 35 (1) | 2 [0..6] |
| >10 ms frames | 15 (1) | 7 (2) | 0 [0..1] |
| max frame ms | 20.66 (1) | 14.07 (2) | 6.17 [5.99..10.26] |
| fps_rel | 0.999 (11) | 0.995 (12) | 1.000 [0.999..1.095] |
| ng_t mean | 2.56 (4) | 3.09 (1) | 2.48 [2.43..2.62] |
| ng_t 1 s max | 5.16 (2) | 5.28 (1) | 4.13 [3.90..5.13] |
| ng_u mean | 3.32 (9) | 3.61 (1) | 3.34 [3.26..3.41] |
| ng_t bursts | 7 (2) | 21 (1) | 3 [2..5] |
| warm-up ng_t | 2.45 (5) | 2.42 (8) | 2.42 [2.26..2.97] |
| P util % | 63.9 (6) | 62.1 (12) | 63.8 [62.6..64.9] |
| E util % | 42.1 (5) | 47.8 (1) | 41.7 [40.6..42.7] |
| P MHz | 1921 (11) | 1823 (12) | 1959 [1930..1986] |
| E MHz | 1937 (11) | 1837 (12) | 1978 [1947..2000] |
| game cores | 2.60 (3) | 2.70 (1) | 2.54 [2.50..2.61] |
| game threads | 72 (1) | 72 (1) | 72 [72..72] |
| game handles | 1298 (7) | 1295 (11) | 1299 [1294..1302] |
| game commit MB | 1194 (10) | 1195 (8) | 1198 [1193..1204] |
| free RAM GB min | 13.09 (5) | 13.07 (8) | 13.09 [13.04..13.11] |
| GPU MHz mean | 832 (3) | 832 (3) | 832 [832..1021] |
| GPU MHz min | 832 (1) | 832 (1) | 832 [832..832] |
| GPU temp C | 87.0 (6) | 87.0 (6) | 87.0 [86.1..87.7] |
| GPU power W | 15.56 (9) | 15.54 (10) | 15.60 [15.43..16.81] |
| GPU util % | 99.8 (2) | 99.2 (11) | 99.7 [98.2..99.9] |
| GPU thermal-throttle share | 1.00 (1) | 1.00 (1) | 1.00 [1.00..1.00] |
| pipeline misses | 0 (1) | 0 (1) | 0 [0..0] |
| texture misses | 0 (1) | 0 (1) | 0 [0..0] |
| cb stalls | 13035 (6) | 11053 (11) | 12991 [7959..13205] |
| crit contentions | 0 (1) | 0 (1) | 0 [0..0] |
| interrupt_dispatches /s | 4451.2 (11) | 4438.7 (12) | 4468.3 [4455.3..4796.4] |

0251-B-r3: most >6 ms frames in bin 30-40 s (20 of 22); that bin vs the mean of the other bins: ng_t 3.19 vs 2.41, ng_t 1 s max 5.16 vs 3.27, ng_u 3.75 vs 3.22, P util 63.5 vs 64.0, P MHz 1850 vs 1939, E MHz 1851 vs 1958, game 2.56 vs 2.61, GPU MHz 832 vs 832, GPU C 87.0 vs 87.0, GPU util 99.4 vs 99.9, free RAM GB 13.10 vs 13.10.

| bin s | frames | >6 | >10 | max ms | secs | ng_t | ng_t max | ng_u | P util | E util | P MHz | E MHz | game | GPU MHz | GPU C | GPU W | GPU util | proc cores | free GB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0-10 | 3849 | 1 | 0 | 6.08 | 10 | 2.64 | 3.92 | 3.37 | 63.8 | 42.6 | 1899 | 1935 | 2.59 | 832 | 87.0 | 15.55 | 100.0 | 2.62 | 13.11 |
| 10-20 | 3862 | 1 | 0 | 6.04 | 10 | 2.29 | 2.85 | 3.13 | 64.2 | 40.3 | 1954 | 1974 | 2.67 | 832 | 87.0 | 15.58 | 99.9 | 2.62 | 13.10 |
| 20-30 | 3856 | 0 | 0 | 5.77 | 10 | 2.35 | 3.64 | 3.19 | 65.0 | 40.0 | 1967 | 1961 | 2.61 | 832 | 87.0 | 15.58 | 100.0 | 2.64 | 13.10 |
| 30-40 | 3751 | 20 | 15 | 20.66 | 10 | 3.19 | 5.16 | 3.75 | 63.5 | 47.2 | 1850 | 1851 | 2.56 | 832 | 87.0 | 15.52 | 99.4 | 2.58 | 13.10 |
| 40-50 | 3855 | 0 | 0 | 5.52 | 10 | 2.35 | 2.69 | 3.18 | 63.0 | 40.4 | 1935 | 1964 | 2.57 | 832 | 87.0 | 15.56 | 99.9 | 2.55 | 13.10 |

0253-B-r4: most >6 ms frames in bin 20-30 s (12 of 35); that bin vs the mean of the other bins: ng_t 3.44 vs 3.01, ng_t 1 s max 4.37 vs 4.10, ng_u 3.79 vs 3.57, P util 60.3 vs 62.5, P MHz 1762 vs 1838, E MHz 1758 vs 1857, game 2.79 vs 2.68, GPU MHz 832 vs 832, GPU C 87.0 vs 87.0, GPU util 99.2 vs 99.2, free RAM GB 13.08 vs 13.09.

| bin s | frames | >6 | >10 | max ms | secs | ng_t | ng_t max | ng_u | P util | E util | P MHz | E MHz | game | GPU MHz | GPU C | GPU W | GPU util | proc cores | free GB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0-10 | 3751 | 8 | 3 | 12.35 | 10 | 3.30 | 5.28 | 3.77 | 62.9 | 49.5 | 1795 | 1828 | 2.71 | 832 | 87.0 | 15.42 | 98.2 | 2.76 | 13.10 |
| 10-20 | 3831 | 2 | 0 | 8.77 | 10 | 3.65 | 4.60 | 3.93 | 59.9 | 52.0 | 1752 | 1750 | 2.63 | 832 | 87.0 | 15.55 | 99.7 | 2.65 | 13.09 |
| 20-30 | 3835 | 12 | 1 | 14.07 | 10 | 3.44 | 4.37 | 3.79 | 60.3 | 52.1 | 1762 | 1758 | 2.79 | 832 | 87.0 | 15.55 | 99.2 | 2.78 | 13.08 |
| 30-40 | 3849 | 9 | 2 | 11.91 | 10 | 2.40 | 3.30 | 3.19 | 63.6 | 41.3 | 1943 | 1951 | 2.66 | 832 | 87.0 | 15.57 | 99.5 | 2.64 | 13.09 |
| 40-50 | 3837 | 4 | 1 | 11.44 | 10 | 2.69 | 3.21 | 3.37 | 63.6 | 44.3 | 1861 | 1900 | 2.71 | 832 | 87.0 | 15.60 | 99.4 | 2.72 | 13.08 |

0251-B-r3 per second, T 25-45 s:

| T end s | wall | frames | >6 | max ms | pipe | tex | cbs | crit | intr | ng_t | ng_u | P util | E util | P MHz | E MHz | game | proc cores | threads | ws MB | free GB | GPU MHz | GPU C | GPU W | GPU util | throttle |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 25.81 | 02:53:12 | 381 | 0 | 5.68 | 0 | 0 | 297 | 0 | 4420 | 2.19 | 3.09 | 64.3 | 38.3 | 2045 | 1966 | 2.55 | 2.56 | 72 | 702 | 13.10 | 832 | 87 | 15.57 | 100 | 0x20 |
| 26.82 | 02:53:13 | 392 | 0 | 5.77 | 0 | 0 | 279 | 0 | 4535 | 2.29 | 3.11 | 65.4 | 40.1 | 1863 | 1964 | 2.71 | 2.55 | 72 | 702 | 13.10 | 832 | 87 | 15.54 | 100 | 0x20 |
| 27.83 | 02:53:14 | 389 | 0 | 5.25 | 0 | 0 | 295 | 0 | 4510 | 1.88 | 2.83 | 65.0 | 35.4 | 2069 | 2047 | 2.60 | 2.75 | 72 | 702 | 13.09 | 832 | 87 | 15.61 | 100 | 0x20 |
| 28.81 | 02:53:15 | 383 | 0 | 5.33 | 0 | 0 | 259 | 0 | 4432 | 2.73 | 3.61 | 66.2 | 44.4 | 1933 | 1983 | 2.58 | 2.57 | 72 | 702 | 13.09 | 832 | 87 | 15.64 | 100 | 0x20 |
| 29.82 | 02:53:16 | 385 | 0 | 5.38 | 0 | 0 | 303 | 0 | 4475 | 1.70 | 2.54 | 64.2 | 34.3 | 2026 | 1973 | 2.77 | 2.59 | 72 | 702 | 13.09 | 832 | 87 | 15.54 | 100 | 0x20 |
| 30.83 | 02:53:17 | 393 | 0 | 5.09 | 0 | 0 | 291 | 0 | 4541 | 1.81 | 2.80 | 64.9 | 34.7 | 2078 | 2066 | 2.57 | 2.82 | 72 | 702 | 13.09 | 832 | 87 | 15.54 | 100 | 0x20 |
| 31.83 | 02:53:18 | 389 | 0 | 4.85 | 0 | 0 | 260 | 0 | 4500 | 2.60 | 3.32 | 61.7 | 44.0 | 1936 | 1893 | 2.67 | 2.52 | 72 | 702 | 13.10 | 832 | 87 | 15.64 | 100 | 0x20 |
| 32.81 | 02:53:19 | 384 | 0 | 5.81 | 0 | 0 | 274 | 0 | 4443 | 2.13 | 2.99 | 65.5 | 36.0 | 1958 | 1967 | 2.51 | 2.70 | 72 | 702 | 13.09 | 832 | 87 | 15.67 | 100 | 0x20 |
| 33.83 | 02:53:20 | 363 | 5 | 16.51 | 0 | 0 | 187 | 0 | 4281 | 4.23 | 4.92 | 69.3 | 59.1 | 1800 | 1802 | 2.58 | 2.48 | 72 | 702 | 13.09 | 832 | 87 | 15.64 | 100 | 0x20 |
| 34.81 | 02:53:21 | 303 | 15 | 20.66 | 0 | 0 | 69 | 0 | 3718 | 5.16 | 5.19 | 62.5 | 64.0 | 1654 | 1681 | 2.43 | 2.60 | 72 | 702 | 13.11 | 832 | 87 | 15.62 | 100 | 0x20 |
| 35.82 | 02:53:22 | 376 | 0 | 5.60 | 0 | 0 | 157 | 0 | 4386 | 3.87 | 3.84 | 58.7 | 50.6 | 1665 | 1638 | 2.55 | 2.39 | 72 | 702 | 13.09 | 832 | 87 | 14.89 | 96 | 0x20 |
| 36.82 | 02:53:23 | 384 | 0 | 5.54 | 0 | 0 | 205 | 0 | 4461 | 3.80 | 4.17 | 64.4 | 51.4 | 1818 | 1789 | 2.52 | 2.59 | 72 | 702 | 13.11 | 832 | 87 | 15.44 | 100 | 0x20 |
| 37.83 | 02:53:24 | 386 | 0 | 5.64 | 0 | 0 | 271 | 0 | 4478 | 2.54 | 3.27 | 64.0 | 41.5 | 1942 | 1921 | 2.61 | 2.50 | 72 | 702 | 13.10 | 832 | 87 | 15.56 | 100 | 0x20 |
| 38.83 | 02:53:25 | 387 | 0 | 5.10 | 0 | 0 | 214 | 0 | 4483 | 3.30 | 3.91 | 63.7 | 49.1 | 1790 | 1865 | 2.56 | 2.63 | 72 | 702 | 13.10 | 832 | 87 | 15.58 | 98 | 0x20 |
| 39.83 | 02:53:26 | 388 | 0 | 5.14 | 0 | 0 | 263 | 0 | 4493 | 2.44 | 3.07 | 59.9 | 41.0 | 1861 | 1892 | 2.61 | 2.55 | 72 | 702 | 13.10 | 832 | 87 | 15.59 | 100 | 0x20 |
| 40.82 | 02:53:27 | 387 | 0 | 5.06 | 0 | 0 | 283 | 0 | 4478 | 2.23 | 3.07 | 60.0 | 37.8 | 1946 | 2027 | 2.35 | 2.63 | 72 | 702 | 13.10 | 832 | 87 | 15.60 | 100 | 0x20 |
| 41.82 | 02:53:28 | 385 | 0 | 5.49 | 0 | 0 | 276 | 0 | 4468 | 2.68 | 3.55 | 62.7 | 43.3 | 1925 | 1978 | 2.43 | 2.29 | 72 | 702 | 13.10 | 832 | 87 | 15.61 | 100 | 0x20 |
| 42.81 | 02:53:29 | 380 | 0 | 5.35 | 0 | 0 | 272 | 0 | 4411 | 2.11 | 2.86 | 61.2 | 37.2 | 1856 | 1956 | 2.57 | 2.46 | 72 | 702 | 13.10 | 832 | 87 | 15.51 | 100 | 0x20 |
| 43.82 | 02:53:30 | 389 | 0 | 5.20 | 0 | 0 | 279 | 0 | 4510 | 2.19 | 3.07 | 60.5 | 40.2 | 1884 | 1936 | 2.57 | 2.59 | 72 | 702 | 13.10 | 832 | 87 | 15.53 | 100 | 0x20 |
| 44.82 | 02:53:31 | 379 | 0 | 5.05 | 0 | 0 | 264 | 0 | 4406 | 2.69 | 3.43 | 62.2 | 45.9 | 1931 | 1917 | 2.72 | 2.56 | 72 | 702 | 13.09 | 832 | 87 | 15.55 | 100 | 0x20 |

game.log entries at T 25-45 s (4): T 30.28 02:53:16.523 [info] [core] Toypad[Write] 0B 16 55 0A B1 09 DE BD 09 2F 19 14 1B 7E B2 00 00 00 00 00 00 00  || T 30.28 02:53:16.523 [info] [core] Toypad[Read ] 0B 0C 55 09 09 6F A6 6A AA 9C 1B 6C B1 64 00 00 00 00 00 00 00 00  || T 30.29 02:53:16.525 [info] [core] Toypad[Write] 0B 16 55 0A B3 0A F3 44 88 31 82 B0 BE A0 9C 00 00 00 00 00 00 00  || T 30.29 02:53:16.527 [info] [core] Toypad[Read ] 0B 0C 55 09 0A 6A A5 DB 42 99 05 94 B3 79 00 00 00 00 00 00 00 00 

### 5.3 W6-1 (0009) short bursts: 0023-p2fc-r2, 0031-s0-r3, 0037-s0-r4, 0039-p2-r4

| # | run | win wall | fps | fps_rel | >6/>10/>16.7 | A8 >6 | max ms | ng_t mean | ng_t max | ng_u mean | bursts | wu ng_t | P util | P MHz | E MHz | game | threads/handles | commit MB | free GB min | GPU MHz (min) | GPU C mean/max | GPU W | GPU util | thermal % | pipe all/>6fr | batt % | build procs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0009-cold-s0 (unscored) | 00:10:07-00:10:37 | 399.4 | - | 23/0/0 |  | 8.60 | 3.81 | 9.07 | 4.25 | - | 1.82 | 64.6 | 1817 | 1841 | 2.52 | 72/1299 | 1190 | 13.51 | - (-) | -/- | - | - | - | 0/0 | 100-100 | [] |
| 2 | 0010-s0-r1 | 00:11:50-00:12:40 | 446.1 | 1.158 | 3/0/0 |  | 6.91 | 2.53 | 4.30 | 3.48 | 2 | 3.45 | 64.3 | 1994 | 2006 | 2.43 | 72/1300 | 1197 | 13.47 | 1257 (832) | 86.8/87 | 19.44 | 92.5 | 100 | 0/0 | 100-100 | [] |
| 3 | 0012-p2-r1 | 00:13:53-00:14:43 | 441.7 | 1.146 | 1/0/0 |  | 6.00 | 2.42 | 3.78 | 3.39 | 1 | 3.04 | 66.4 | 2017 | 2021 | 2.47 | 72/1299 | 1202 | 13.47 | 1134 (1087) | 86.7/87 | 17.78 | 96.8 | 100 | 0/0 | 100-100 | [] |
| 4 | 0014-p2f-r1 | 00:15:57-00:16:47 | 425.7 | 1.098 | 1/0/0 |  | 6.27 | 2.45 | 3.43 | 3.36 | 0 | 2.46 | 65.3 | 1975 | 1986 | 2.55 | 72/1299 | 1202 | 13.50 | 1013 (990) | 86.1/87 | 16.57 | 98.3 | 100 | 0/0 | 100-100 | [] |
| 5 | 0016-p2fc-r1 | 00:18:00-00:18:50 | 473.1 | 1.015 | 0/0/0 |  | 5.88 | 2.25 | 3.57 | 3.43 | 1 | 2.32 | 67.0 | 2137 | 2112 | 2.32 | 72/1299 | 1198 | 13.52 | 832 (832) | 86.4/87 | 16.18 | 88.1 | 100 | 0/0 | 100-100 | [] |
| 6 | 0019-p2-r2 | 00:20:04-00:20:54 | 402.3 | 1.043 | 4/0/0 |  | 6.22 | 2.46 | 4.86 | 3.39 | 2 | 2.37 | 63.9 | 1990 | 2005 | 2.49 | 72/1304 | 1196 | 13.50 | 909 (840) | 86.0/87 | 15.66 | 98.7 | 100 | 0/0 | 100-100 | [] |
| 7 | 0021-p2f-r2 | 00:22:07-00:22:57 | 387.8 | 1.000 | 3/0/0 |  | 7.66 | 2.46 | 4.64 | 3.33 | 1 | 2.68 | 62.8 | 1958 | 1983 | 2.59 | 72/1297 | 1195 | 13.51 | 832 (832) | 86.3/87 | 15.46 | 99.9 | 100 | 0/0 | 100-100 | [] |
| 8 | 0023-p2fc-r2 FOCUS | 00:24:11-00:25:01 | 426.9 | 0.916 | 40/0/0 | 40 (31 in 0-10) | 9.11 | 3.95 | 9.38 | 4.64 | 26 | 2.94 | 63.4 | 1922 | 1852 | 2.21 | 72/1296 | 1197 | 13.43 | 869 (832) | 86.8/87 | 15.82 | 81.9 | 100 | 0/0 | 100-100 | [] |
| 9 | 0025-s0-r2 | 00:26:14-00:27:04 | 368.1 | 0.956 | 5/0/0 |  | 9.69 | 4.09 | 6.68 | 4.38 | 28 | 4.59 | 62.9 | 1759 | 1778 | 2.58 | 72/1301 | 1200 | 13.36 | 832 (832) | 86.6/87 | 15.23 | 96.8 | 100 | 0/0 | 100-100 | [] |
| 10 | 0027-p2f-r3 | 00:28:18-00:29:08 | 387.7 | 1.000 | 6/0/0 |  | 6.92 | 2.40 | 3.75 | 3.34 | 1 | 2.38 | 64.1 | 1991 | 2012 | 2.52 | 72/1299 | 1197 | 13.39 | 832 (832) | 87.0/87 | 15.57 | 99.4 | 100 | 0/0 | 100-100 | [] |
| 11 | 0029-p2fc-r3 | 00:30:21-00:31:11 | 466.3 | 1.000 | 2/0/0 |  | 6.34 | 2.44 | 4.63 | 3.55 | 3 | 2.54 | 65.6 | 2096 | 2084 | 2.24 | 72/1295 | 1189 | 13.33 | 832 (832) | 88.0/88 | 16.35 | 87.9 | 100 | 0/0 | 100-100 | [] |
| 12 | 0031-s0-r3 FOCUS | 00:32:25-00:33:15 | 384.9 | 0.999 | 29/0/0 | 29 (2/7/1/10/9) | 9.48 | 2.59 | 5.18 | 3.46 | 2 | 2.44 | 65.6 | 1971 | 1978 | 2.49 | 72/1300 | 1198 | 13.37 | 832 (832) | 87.1/88 | 15.59 | 99.7 | 100 | 0/0 | 100-100 | [] |
| 13 | 0033-p2-r3 | 00:34:28-00:35:18 | 385.0 | 0.999 | 3/0/0 |  | 6.29 | 2.50 | 4.26 | 3.32 | 5 | 2.39 | 63.3 | 1960 | 1958 | 2.60 | 72/1299 | 1194 | 13.38 | 832 (832) | 87.3/88 | 15.62 | 99.5 | 100 | 0/0 | 100-100 | [] |
| 14 | 0035-p2fc-r4 | 00:36:32-00:37:22 | 471.2 | 1.011 | 2/0/0 |  | 6.14 | 2.38 | 3.97 | 3.47 | 1 | 2.38 | 64.2 | 2091 | 2075 | 2.33 | 72/1300 | 1195 | 13.36 | 832 (832) | 88.2/89 | 16.52 | 88.4 | 100 | 0/0 | 100-100 | [] |
| 15 | 0037-s0-r4 FOCUS | 00:38:36-00:39:26 | 385.2 | 1.000 | 43/0/0 | 43 (10/14/4/8/7) | 7.11 | 2.54 | 4.01 | 3.42 | 1 | 2.59 | 67.5 | 1967 | 1978 | 2.53 | 72/1295 | 1204 | 13.35 | 832 (832) | 87.9/88 | 15.65 | 99.5 | 100 | 0/0 | 100-100 | [] |
| 16 | 0039-p2-r4 FOCUS | 00:40:39-00:41:29 | 381.9 | 0.990 | 17/0/0 | 17 (all 10-20) | 9.51 | 2.87 | 5.56 | 3.59 | 9 | 2.32 | 63.8 | 1901 | 1926 | 2.52 | 72/1301 | 1194 | 13.33 | 832 (832) | 87.7/88 | 15.61 | 98.8 | 100 | 0/0 | 100-100 | [] |
| 17 | 0041-p2f-r4 | 00:42:43-00:43:33 | 386.8 | 0.998 | 1/1/0 |  | 11.73 | 2.57 | 4.22 | 3.39 | 2 | 2.91 | 64.1 | 1941 | 1967 | 2.55 | 72/1298 | 1201 | 13.33 | 832 (832) | 87.8/88 | 15.69 | 99.3 | 100 | 0/0 | 100-100 | [] |
| 18 | 0043-s0-r5 | 00:44:46-00:45:36 | 385.2 | 1.000 | 4/0/0 |  | 6.52 | 2.47 | 4.71 | 3.36 | 2 | 2.41 | 63.8 | 1982 | 1986 | 2.50 | 72/1294 | 1204 | 13.33 | 832 (832) | 87.9/88 | 15.69 | 99.5 | 100 | 0/0 | 100-100 | [] |
| 19 | 0045-p2-r5 | 00:46:50-00:47:40 | 385.6 | 1.000 | 6/0/0 |  | 6.40 | 2.55 | 4.39 | 3.40 | 4 | 2.42 | 62.9 | 1950 | 1984 | 2.51 | 72/1296 | 1194 | 13.32 | 832 (832) | 87.8/88 | 15.68 | 99.8 | 100 | 0/0 | 100-100 | [] |
| 20 | 0047-p2f-r5 | 00:48:53-00:49:43 | 386.8 | 0.998 | 3/0/0 |  | 6.32 | 2.52 | 4.22 | 3.37 | 3 | 2.71 | 62.7 | 1946 | 1972 | 2.56 | 72/1297 | 1193 | 13.29 | 832 (832) | 87.9/88 | 15.67 | 99.4 | 100 | 0/0 | 100-100 | [] |
| 21 | 0049-p2fc-r5 | 00:50:57-00:51:47 | 457.2 | 0.981 | 3/0/0 |  | 6.04 | 2.64 | 5.27 | 3.70 | 5 | 2.34 | 65.7 | 2033 | 2045 | 2.28 | 72/1293 | 1198 | 13.27 | 832 (832) | 88.6/89 | 16.41 | 88.5 | 100 | 0/0 | 100-100 | [] |

0023-p2fc-r2: most >6 ms frames in bin 0-10 s (31 of 40); that bin vs the mean of the other bins: ng_t 5.77 vs 3.49, ng_t 1 s max 9.38 vs 4.32, ng_u 5.71 vs 4.37, P util 63.6 vs 63.3, P MHz 1664 vs 1986, E MHz 1653 vs 1901, game 2.31 vs 2.20, GPU MHz 973 vs 846, GPU C 86.1 vs 87.0, GPU util 68.6 vs 84.7, free RAM GB 13.46 vs 13.44.

| bin s | frames | >6 | >10 | max ms | secs | ng_t | ng_t max | ng_u | P util | E util | P MHz | E MHz | game | GPU MHz | GPU C | GPU W | GPU util | proc cores | free GB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0-10 | 3394 | 31 | 0 | 8.81 | 10 | 5.77 | 9.38 | 5.71 | 63.6 | 68.5 | 1664 | 1653 | 2.31 | 973 | 86.1 | 15.15 | 68.6 | 2.36 | 13.46 |
| 10-20 | 4297 | 2 | 0 | 6.05 | 10 | 3.84 | 4.95 | 4.56 | 61.8 | 53.7 | 1929 | 1844 | 2.22 | 881 | 86.8 | 15.73 | 80.6 | 2.23 | 13.45 |
| 20-30 | 4615 | 4 | 0 | 6.14 | 10 | 3.34 | 3.92 | 4.30 | 64.3 | 48.7 | 2011 | 1936 | 2.17 | 840 | 87.0 | 16.10 | 87.1 | 2.17 | 13.45 |
| 30-40 | 4472 | 1 | 0 | 6.11 | 10 | 3.42 | 4.44 | 4.34 | 63.8 | 50.0 | 2002 | 1914 | 2.22 | 832 | 87.0 | 15.97 | 84.4 | 2.21 | 13.44 |
| 40-50 | 4569 | 2 | 0 | 9.11 | 10 | 3.36 | 3.99 | 4.27 | 63.2 | 48.9 | 2004 | 1911 | 2.18 | 832 | 87.0 | 16.04 | 86.6 | 2.19 | 13.43 |

0023-p2fc-r2 per second, T 0-12 s:

| T end s | wall | frames | >6 | max ms | pipe | tex | cbs | crit | intr | ng_t | ng_u | P util | E util | P MHz | E MHz | game | proc cores | threads | ws MB | free GB | GPU MHz | GPU C | GPU W | GPU util | throttle |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.80 | 00:24:11 | 186 | 18 | 8.81 | 0 | 0 | 0 | 0 | 2537 | 9.38 | 8.05 | 79.6 | 89.0 | 1351 | 1490 | 2.25 | 2.76 | 72 | 711 | 13.49 | - | - | - | - | - |
| 1.80 | 00:24:12 | 245 | 10 | 7.45 | 0 | 0 | 0 | 0 | 3205 | 7.17 | 6.32 | 67.2 | 75.6 | 1461 | 1507 | 2.42 | 2.12 | 72 | 711 | 13.48 | 1065 | 86 | 14.46 | 57 | 0x20 |
| 2.78 | 00:24:13 | 335 | 1 | 7.03 | 0 | 0 | 0 | 0 | 4005 | 4.98 | 4.97 | 59.2 | 62.3 | 1650 | 1684 | 2.39 | 2.51 | 72 | 711 | 13.45 | 975 | 86 | 15.09 | 69 | 0x20 |
| 3.79 | 00:24:14 | 352 | 0 | 5.64 | 0 | 0 | 0 | 0 | 4169 | 5.74 | 5.87 | 62.9 | 70.4 | 1711 | 1662 | 2.28 | 2.35 | 72 | 711 | 13.45 | 1020 | 86 | 15.21 | 67 | 0x20 |
| 4.79 | 00:24:15 | 372 | 0 | 5.68 | 0 | 0 | 0 | 0 | 4354 | 4.91 | 5.15 | 60.6 | 62.6 | 1749 | 1684 | 2.29 | 2.26 | 72 | 711 | 13.45 | 990 | 87 | 15.19 | 70 | 0x20 |
| 5.79 | 00:24:16 | 386 | 0 | 5.31 | 0 | 0 | 0 | 0 | 4476 | 4.73 | 5.03 | 59.0 | 62.3 | 1769 | 1716 | 2.31 | 2.29 | 72 | 711 | 13.45 | 907 | 86 | 15.32 | 77 | 0x20 |
| 6.79 | 00:24:17 | 359 | 0 | 5.52 | 0 | 0 | 0 | 0 | 4225 | 5.32 | 5.55 | 62.0 | 67.4 | 1734 | 1685 | 2.33 | 2.33 | 72 | 711 | 13.44 | 937 | 86 | 15.26 | 72 | 0x20 |
| 7.79 | 00:24:18 | 367 | 1 | 7.41 | 0 | 0 | 0 | 0 | 4309 | 5.16 | 5.39 | 60.9 | 65.2 | 1744 | 1683 | 2.26 | 2.33 | 72 | 711 | 13.45 | 967 | 86 | 15.27 | 65 | 0x20 |
| 8.79 | 00:24:19 | 386 | 1 | 6.34 | 0 | 0 | 0 | 0 | 4467 | 4.50 | 4.80 | 61.5 | 58.5 | 1743 | 1722 | 2.34 | 2.24 | 72 | 711 | 13.44 | 937 | 86 | 15.32 | 74 | 0x20 |
| 9.79 | 00:24:20 | 356 | 0 | 5.25 | 0 | 0 | 0 | 0 | 4207 | 5.79 | 6.01 | 62.6 | 71.3 | 1728 | 1699 | 2.20 | 2.37 | 72 | 711 | 13.45 | 960 | 86 | 15.19 | 66 | 0x20 |
| 10.79 | 00:24:21 | 390 | 0 | 5.20 | 0 | 0 | 0 | 0 | 4510 | 4.25 | 4.55 | 56.2 | 56.0 | 1799 | 1734 | 2.17 | 2.15 | 72 | 711 | 13.44 | 937 | 87 | 15.16 | 71 | 0x20 |
| 11.80 | 00:24:22 | 390 | 0 | 4.87 | 0 | 0 | 0 | 0 | 4519 | 4.95 | 5.40 | 60.1 | 65.8 | 1825 | 1703 | 2.27 | 2.18 | 72 | 711 | 13.44 | 922 | 87 | 15.38 | 74 | 0x20 |

game.log entries at T 0-12 s (2): T 4.32 00:24:15.329 [info] [sys] C1 keep-watch: 57344 protects kept so far || T 9.85 00:24:20.853 [info] [sys] C1 keep-watch: 61440 protects kept so far

0031-s0-r3: most >6 ms frames in bin 30-40 s (10 of 29); that bin vs the mean of the other bins: ng_t 2.57 vs 2.59, ng_t 1 s max 3.33 vs 3.88, ng_u 3.48 vs 3.46, P util 66.9 vs 65.3, P MHz 1984 vs 1968, E MHz 1985 vs 1976, game 2.49 vs 2.49, GPU MHz 832 vs 832, GPU C 87.2 vs 87.1, GPU util 99.9 vs 99.6, free RAM GB 13.38 vs 13.39.

| bin s | frames | >6 | >10 | max ms | secs | ng_t | ng_t max | ng_u | P util | E util | P MHz | E MHz | game | GPU MHz | GPU C | GPU W | GPU util | proc cores | free GB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0-10 | 3846 | 2 | 0 | 7.16 | 10 | 2.64 | 3.84 | 3.54 | 65.6 | 41.5 | 1980 | 1980 | 2.40 | 832 | 87.0 | 15.57 | 99.3 | 2.40 | 13.39 |
| 10-20 | 3856 | 7 | 0 | 7.51 | 10 | 2.65 | 3.44 | 3.50 | 64.3 | 42.9 | 1964 | 1950 | 2.51 | 832 | 87.0 | 15.59 | 99.9 | 2.51 | 13.40 |
| 20-30 | 3827 | 1 | 0 | 8.58 | 10 | 2.52 | 5.18 | 3.32 | 64.3 | 41.1 | 1926 | 1975 | 2.54 | 832 | 87.1 | 15.56 | 99.3 | 2.55 | 13.38 |
| 30-40 | 3849 | 10 | 0 | 9.48 | 10 | 2.57 | 3.33 | 3.48 | 66.9 | 41.2 | 1984 | 1985 | 2.49 | 832 | 87.2 | 15.60 | 99.9 | 2.50 | 13.38 |
| 40-50 | 3867 | 9 | 0 | 6.54 | 10 | 2.54 | 3.06 | 3.47 | 66.9 | 41.3 | 2001 | 2000 | 2.51 | 832 | 87.4 | 15.64 | 99.8 | 2.49 | 13.38 |

0037-s0-r4: most >6 ms frames in bin 10-20 s (14 of 43); that bin vs the mean of the other bins: ng_t 2.36 vs 2.59, ng_t 1 s max 2.91 vs 3.35, ng_u 3.32 vs 3.44, P util 68.4 vs 67.2, P MHz 2027 vs 1952, E MHz 2012 vs 1970, game 2.53 vs 2.53, GPU MHz 832 vs 832, GPU C 87.9 vs 87.9, GPU util 99.6 vs 99.4, free RAM GB 13.35 vs 13.36.

| bin s | frames | >6 | >10 | max ms | secs | ng_t | ng_t max | ng_u | P util | E util | P MHz | E MHz | game | GPU MHz | GPU C | GPU W | GPU util | proc cores | free GB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0-10 | 3810 | 10 | 0 | 6.94 | 10 | 2.80 | 4.01 | 3.57 | 67.3 | 43.2 | 1916 | 1942 | 2.57 | 832 | 87.6 | 15.57 | 99.2 | 2.59 | 13.36 |
| 10-20 | 3861 | 14 | 0 | 7.11 | 10 | 2.36 | 2.91 | 3.32 | 68.4 | 38.9 | 2027 | 2012 | 2.53 | 832 | 87.9 | 15.65 | 99.6 | 2.52 | 13.35 |
| 20-30 | 3862 | 4 | 0 | 6.41 | 10 | 2.59 | 3.34 | 3.48 | 67.2 | 41.0 | 1977 | 1979 | 2.48 | 832 | 88.0 | 15.67 | 99.7 | 2.48 | 13.35 |
| 30-40 | 3871 | 8 | 0 | 6.72 | 10 | 2.47 | 2.93 | 3.35 | 67.0 | 39.4 | 1961 | 1991 | 2.48 | 832 | 88.0 | 15.67 | 99.2 | 2.47 | 13.36 |
| 40-50 | 3854 | 7 | 0 | 6.34 | 10 | 2.49 | 3.12 | 3.37 | 67.5 | 40.7 | 1954 | 1968 | 2.59 | 832 | 88.0 | 15.68 | 99.4 | 2.58 | 13.36 |

0039-p2-r4: most >6 ms frames in bin 10-20 s (17 of 17); that bin vs the mean of the other bins: ng_t 3.46 vs 2.73, ng_t 1 s max 5.56 vs 3.88, ng_u 3.99 vs 3.49, P util 63.6 vs 63.9, P MHz 1842 vs 1916, E MHz 1856 vs 1944, game 2.49 vs 2.52, GPU MHz 832 vs 832, GPU C 87.7 vs 87.7, GPU util 98.2 vs 98.9, free RAM GB 13.35 vs 13.35.

| bin s | frames | >6 | >10 | max ms | secs | ng_t | ng_t max | ng_u | P util | E util | P MHz | E MHz | game | GPU MHz | GPU C | GPU W | GPU util | proc cores | free GB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0-10 | 3781 | 0 | 0 | 5.95 | 10 | 2.79 | 3.94 | 3.56 | 64.7 | 43.4 | 1917 | 1946 | 2.50 | 832 | 87.3 | 15.58 | 98.4 | 2.52 | 13.35 |
| 10-20 | 3755 | 17 | 0 | 9.51 | 10 | 3.46 | 5.56 | 3.99 | 63.6 | 49.2 | 1842 | 1856 | 2.49 | 832 | 87.7 | 15.59 | 98.2 | 2.48 | 13.35 |
| 20-30 | 3800 | 0 | 0 | 5.75 | 10 | 3.28 | 5.23 | 3.80 | 62.9 | 47.6 | 1846 | 1846 | 2.53 | 832 | 87.5 | 15.50 | 97.3 | 2.53 | 13.34 |
| 30-40 | 3874 | 0 | 0 | 5.65 | 10 | 2.33 | 3.09 | 3.23 | 64.1 | 40.1 | 1951 | 1996 | 2.55 | 832 | 88.0 | 15.68 | 99.8 | 2.56 | 13.35 |
| 40-50 | 3883 | 0 | 0 | 5.84 | 10 | 2.51 | 3.27 | 3.36 | 63.9 | 41.4 | 1950 | 1989 | 2.51 | 832 | 88.0 | 15.70 | 100.0 | 2.49 | 13.35 |

0039-p2-r4 per second, T 8-22 s:

| T end s | wall | frames | >6 | max ms | pipe | tex | cbs | crit | intr | ng_t | ng_u | P util | E util | P MHz | E MHz | game | proc cores | threads | ws MB | free GB | GPU MHz | GPU C | GPU W | GPU util | throttle |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 8.80 | 00:40:48 | 385 | 0 | 5.30 | 0 | 0 | 258 | 0 | 4458 | 1.98 | 2.81 | 63.4 | 35.3 | 2004 | 2012 | 2.56 | 2.41 | 72 | 704 | 13.34 | 832 | 87 | 15.32 | 100 | 0x20 |
| 9.81 | 00:40:49 | 390 | 0 | 5.95 | 0 | 0 | 253 | 0 | 4517 | 2.40 | 3.38 | 65.0 | 40.6 | 2044 | 2019 | 2.46 | 2.59 | 72 | 704 | 13.34 | 832 | 88 | 15.54 | 100 | 0x20 |
| 10.81 | 00:40:50 | 386 | 0 | 5.31 | 0 | 0 | 253 | 0 | 4481 | 2.61 | 3.46 | 62.8 | 42.5 | 1974 | 1949 | 2.45 | 2.44 | 72 | 704 | 13.35 | 832 | 88 | 15.67 | 100 | 0x20 |
| 11.80 | 00:40:51 | 381 | 0 | 5.27 | 0 | 0 | 283 | 0 | 4417 | 2.20 | 3.16 | 65.5 | 38.5 | 1991 | 2031 | 2.54 | 2.45 | 72 | 704 | 13.35 | 832 | 88 | 15.68 | 100 | 0x20 |
| 12.80 | 00:40:52 | 388 | 0 | 5.43 | 0 | 0 | 260 | 0 | 4489 | 2.96 | 3.90 | 67.7 | 46.0 | 1938 | 1998 | 2.49 | 2.57 | 72 | 704 | 13.35 | 832 | 88 | 15.65 | 100 | 0x20 |
| 13.80 | 00:40:53 | 389 | 0 | 5.22 | 0 | 0 | 298 | 0 | 4501 | 1.87 | 2.75 | 64.2 | 33.7 | 2035 | 2022 | 2.51 | 2.48 | 72 | 704 | 13.35 | 832 | 88 | 15.70 | 100 | 0x20 |
| 14.81 | 00:40:54 | 395 | 0 | 5.63 | 0 | 0 | 297 | 0 | 4566 | 2.16 | 3.14 | 65.5 | 37.6 | 1998 | 2028 | 2.49 | 2.52 | 72 | 704 | 13.35 | 832 | 87 | 15.72 | 100 | 0x20 |
| 15.81 | 00:40:55 | 384 | 3 | 8.74 | 0 | 0 | 172 | 0 | 4457 | 3.56 | 4.25 | 63.7 | 53.7 | 1840 | 1863 | 2.60 | 2.48 | 72 | 704 | 13.35 | 832 | 88 | 15.73 | 99 | 0x20 |
| 16.81 | 00:40:56 | 376 | 1 | 6.28 | 0 | 0 | 117 | 0 | 4382 | 3.94 | 4.41 | 64.4 | 54.8 | 1831 | 1778 | 2.55 | 2.62 | 72 | 704 | 13.35 | 832 | 88 | 15.65 | 100 | 0x20 |
| 17.81 | 00:40:57 | 365 | 0 | 5.70 | 0 | 0 | 53 | 0 | 4288 | 5.04 | 5.04 | 61.3 | 62.6 | 1617 | 1660 | 2.42 | 2.53 | 72 | 704 | 13.36 | 832 | 88 | 15.55 | 100 | 0x20 |
| 18.81 | 00:40:58 | 340 | 7 | 9.51 | 0 | 0 | 0 | 0 | 4059 | 5.56 | 5.31 | 61.9 | 64.8 | 1621 | 1587 | 2.35 | 2.39 | 72 | 704 | 13.36 | 832 | 87 | 15.42 | 93 | 0x20 |
| 19.80 | 00:40:59 | 349 | 6 | 7.58 | 0 | 0 | 61 | 0 | 4137 | 4.70 | 4.49 | 59.0 | 58.2 | 1574 | 1643 | 2.53 | 2.34 | 72 | 704 | 13.35 | 832 | 87 | 15.10 | 90 | 0x20 |
| 20.81 | 00:41:00 | 354 | 0 | 5.64 | 0 | 0 | 30 | 0 | 4192 | 5.23 | 5.05 | 61.2 | 64.8 | 1636 | 1654 | 2.58 | 2.57 | 72 | 704 | 13.35 | 832 | 87 | 15.01 | 89 | 0x20 |
| 21.80 | 00:41:01 | 377 | 0 | 4.98 | 0 | 0 | 92 | 0 | 4385 | 3.81 | 3.89 | 59.6 | 50.9 | 1641 | 1723 | 2.56 | 2.58 | 72 | 704 | 13.34 | 832 | 87 | 15.24 | 89 | 0x20 |

game.log entries at T 8-22 s (0): none

### 5.4 0352-p2f-r5: the first 10 s (21 frames >6 ms per Agent 8, the 45.67 ms frame at T 7.44-7.49 s)

0352-p2f-r5: most >6 ms frames in bin 0-10 s (21 of 21); that bin vs the mean of the other bins: ng_t 3.12 vs 2.41, ng_t 1 s max 5.08 vs 3.01, ng_u 3.83 vs 3.31, P util 63.7 vs 64.3, P MHz 1869 vs 1985, E MHz 1914 vs 1990, game 2.51 vs 2.51, GPU MHz 832 vs 832, GPU C 87.8 vs 88.0, GPU util 97.7 vs 99.9, free RAM GB 13.11 vs 13.10.

| bin s | frames | >6 | >10 | max ms | secs | ng_t | ng_t max | ng_u | P util | E util | P MHz | E MHz | game | GPU MHz | GPU C | GPU W | GPU util | proc cores | free GB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0-10 | 3703 | 21 | 14 | 45.67 | 10 | 3.12 | 5.08 | 3.83 | 63.7 | 47.3 | 1869 | 1914 | 2.51 | 832 | 87.8 | 15.47 | 97.7 | 2.50 | 13.11 |
| 10-20 | 3883 | 0 | 0 | 5.57 | 10 | 2.36 | 3.02 | 3.22 | 63.4 | 40.7 | 1965 | 1981 | 2.57 | 832 | 87.9 | 15.72 | 99.9 | 2.56 | 13.10 |
| 20-30 | 3895 | 0 | 0 | 5.74 | 10 | 2.39 | 2.89 | 3.32 | 65.0 | 40.2 | 2002 | 2012 | 2.50 | 832 | 88.0 | 15.77 | 100.0 | 2.51 | 13.10 |
| 30-40 | 3887 | 0 | 0 | 5.91 | 10 | 2.42 | 2.98 | 3.32 | 64.8 | 41.0 | 1989 | 1982 | 2.55 | 832 | 88.0 | 15.78 | 99.9 | 2.57 | 13.10 |
| 40-50 | 3890 | 0 | 0 | 5.71 | 10 | 2.49 | 3.14 | 3.38 | 63.8 | 40.8 | 1985 | 1983 | 2.43 | 832 | 88.0 | 15.79 | 99.8 | 2.42 | 13.10 |

Per second, T 0-12 s:

| T end s | wall | frames | >6 | max ms | pipe | tex | cbs | crit | intr | ng_t | ng_u | P util | E util | P MHz | E MHz | game | proc cores | threads | ws MB | free GB | GPU MHz | GPU C | GPU W | GPU util | throttle |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.79 | 03:53:13 | 323 | 0 | 5.33 | 0 | 0 | 72 | 0 | 3765 | 3.12 | 4.07 | 66.1 | 47.7 | 1835 | 2003 | 2.39 | 2.30 | 72 | 705 | 13.14 | - | - | - | - | - |
| 1.78 | 03:53:14 | 373 | 0 | 5.12 | 0 | 0 | 159 | 0 | 4347 | 2.54 | 3.27 | 62.4 | 43.2 | 1854 | 1927 | 2.68 | 2.41 | 72 | 705 | 13.10 | 832 | 88 | 15.67 | 99 | 0x20 |
| 2.79 | 03:53:15 | 389 | 0 | 5.81 | 0 | 0 | 210 | 0 | 4513 | 2.83 | 3.61 | 64.2 | 45.8 | 1869 | 1920 | 2.62 | 2.75 | 72 | 705 | 13.10 | 832 | 88 | 15.52 | 99 | 0x20 |
| 3.79 | 03:53:16 | 392 | 0 | 5.67 | 0 | 0 | 260 | 0 | 4530 | 2.04 | 2.98 | 63.0 | 36.1 | 2059 | 2053 | 2.43 | 2.59 | 72 | 705 | 13.10 | 832 | 87 | 15.68 | 100 | 0x20 |
| 4.79 | 03:53:17 | 388 | 0 | 5.27 | 0 | 0 | 255 | 0 | 4491 | 2.92 | 3.90 | 64.8 | 47.0 | 2004 | 2016 | 2.45 | 2.38 | 72 | 705 | 13.10 | 832 | 88 | 15.73 | 100 | 0x20 |
| 5.78 | 03:53:18 | 385 | 0 | 5.78 | 0 | 0 | 246 | 0 | 4458 | 1.93 | 2.78 | 64.2 | 36.5 | 2010 | 1967 | 2.71 | 2.47 | 72 | 705 | 13.10 | 832 | 88 | 15.70 | 100 | 0x20 |
| 6.78 | 03:53:19 | 387 | 0 | 5.57 | 0 | 0 | 254 | 0 | 4483 | 2.13 | 3.12 | 65.7 | 39.8 | 1986 | 2017 | 2.70 | 2.77 | 72 | 705 | 13.10 | 832 | 88 | 15.73 | 100 | 0x20 |
| 7.79 | 03:53:20 | 296 | 15 | 45.67 | 0 | 0 | 69 | 0 | 3660 | 5.08 | 5.50 | 64.7 | 65.4 | 1667 | 1781 | 2.32 | 2.68 | 72 | 705 | 13.10 | 832 | 88 | 15.71 | 100 | 0x20 |
| 8.79 | 03:53:21 | 334 | 6 | 27.47 | 0 | 0 | 55 | 0 | 4017 | 4.69 | 4.86 | 61.2 | 59.8 | 1660 | 1717 | 2.37 | 2.23 | 72 | 706 | 13.12 | 832 | 87 | 14.74 | 81 | 0x20 |
| 9.78 | 03:53:22 | 377 | 0 | 5.66 | 0 | 0 | 79 | 0 | 4385 | 3.90 | 4.18 | 60.7 | 51.9 | 1747 | 1742 | 2.40 | 2.40 | 72 | 706 | 13.12 | 832 | 88 | 14.75 | 100 | 0x20 |
| 10.78 | 03:53:23 | 392 | 0 | 5.32 | 0 | 0 | 250 | 0 | 4532 | 1.82 | 2.52 | 59.4 | 34.1 | 1912 | 1959 | 2.59 | 2.41 | 72 | 706 | 13.10 | 832 | 87 | 15.67 | 100 | 0x20 |
| 11.79 | 03:53:24 | 394 | 0 | 5.17 | 0 | 0 | 250 | 0 | 4548 | 1.97 | 2.93 | 61.4 | 36.2 | 2076 | 2050 | 2.42 | 2.65 | 72 | 706 | 13.10 | 832 | 88 | 15.74 | 100 | 0x20 |

game.log entries at T -2..12 s (4): T -1.36 03:53:11.279 [info] [core] Toypad[Write] 0B 16 55 0A B1 07 83 D3 77 09 76 66 62 87 B2 00 00 00 00 00 00 00  || T -1.36 03:53:11.281 [info] [core] Toypad[Read ] 0B 0C 55 09 07 7C 00 46 B5 C8 DA 72 66 56 00 00 00 00 00 00 00 00  || T -1.35 03:53:11.286 [info] [core] Toypad[Write] 0B 16 55 0A B3 08 0D C4 3F 61 74 B6 FC 3E EF 00 00 00 00 00 00 00  || T -1.35 03:53:11.286 [info] [core] Toypad[Read ] 0B 0C 55 09 08 A5 55 07 EF E0 E0 04 4C 66 00 00 00 00 00 00 00 00 

>6 ms frames (T end s, ms): 7.43/8.01, 7.44/9.53, 7.49/45.67, 7.50/13.87, 7.54/13.95, 7.56/15.10, 7.58/13.08, 7.60/25.70, 7.65/24.17, 7.73/6.40, 7.74/6.83, 7.76/12.04, 7.78/8.58, 7.78/6.18, 7.85/19.05, 7.87/23.83, 7.90/27.47, 7.95/20.20, 7.96/8.88, 7.98/20.54, 8.00/24.56

### 5.5 First runs after the idle gate: CPU clocks and GPU thermal state

The quiet/idle gate is not logged in the matrix folders (runner logs hold only run-timing lines; there is no gate log), so its timing is not visible here. "gap" = previous run's last sys sample (for a cold run, the previous folder's last run) to this run's first sys sample. "pre" = sys samples before the game process exists (host only; busy_t = all-host busy cores). fps_rel of a cold run = its fps / the base arm's scored median (the cold window is 30 s from +30 s, so it is not strictly comparable). GPU values are window means (gpu.csv covers the window only).

W6-1 (20261123-0009):

| # | run | start | gap s | pre n | pre busy_t | pre P/E MHz | wu P/E MHz | win P/E MHz | res eff MHz | fps | fps_rel | median ms | GPU MHz mean (first5/last5) | GPU C first5/mean/max | GPU W | GPU util | thermal % | >6 frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0009-cold-s0 (unscored) | 00:09:05 | - | 0 | - | -/- | 3301/2980 | 1817/1841 | 1834 | 399.4 | 1.037 | 2.367 | - (-/-) | -/-/- | - | - | - | 23 |
| 2 | 0010-s0-r1 | 00:10:47 | 9 | 0 | - | -/- | 1872/1910 | 1994/2006 | 2002 | 446.1 | 1.158 | 2.079 | 1257 (1296/1213) | 86.4/86.8/87 | 19.44 | 92.5 | 100 | 3 |
| 3 | 0012-p2-r1 | 00:12:51 | 9 | 0 | - | -/- | 1918/1940 | 2017/2021 | 2021 | 441.7 | 1.146 | 2.047 | 1134 (1162/1126) | 86.2/86.7/87 | 17.78 | 96.8 | 100 | 1 |
| 4 | 0014-p2f-r1 | 00:14:54 | 9 | 0 | - | -/- | 2003/2009 | 1975/1986 | 1982 | 425.7 | 1.098 | 2.197 | 1013 (1045/996) | 86.0/86.1/87 | 16.57 | 98.3 | 100 | 1 |
| 5 | 0016-p2fc-r1 | 00:16:58 | 9 | 0 | - | -/- | 2097/2094 | 2137/2112 | 2125 | 473.1 | 1.015 | 2.135 | 832 (832/832) | 86.0/86.4/87 | 16.18 | 88.1 | 100 | 0 |
| 6 | 0019-p2-r2 | 00:19:01 | 9 | 0 | - | -/- | 2013/2026 | 1990/2005 | 2001 | 402.3 | 1.043 | 2.350 | 909 (997/909) | 86.4/86.0/87 | 15.66 | 98.7 | 100 | 4 |
| 7 | 0021-p2f-r2 | 00:21:05 | 9 | 0 | - | -/- | 1945/1972 | 1958/1983 | 1974 | 387.8 | 1.000 | 2.463 | 832 (832/832) | 86.6/86.3/87 | 15.46 | 99.9 | 100 | 3 |
| 8 | 0023-p2fc-r2 | 00:23:08 | 9 | 0 | - | -/- | 2014/2017 | 1922/1852 | 1875 | 426.9 | 0.916 | 2.307 | 869 (991/832) | 86.2/86.8/87 | 15.82 | 81.9 | 100 | 40 |
| 9 | 0025-s0-r2 | 00:25:12 | 9 | 0 | - | -/- | 1682/1705 | 1759/1778 | 1770 | 368.1 | 0.956 | 2.602 | 832 (832/832) | 86.0/86.6/87 | 15.23 | 96.8 | 100 | 5 |
| 10 | 0027-p2f-r3 | 00:27:15 | 9 | 0 | - | -/- | 2015/2020 | 1991/2012 | 2006 | 387.7 | 1.000 | 2.436 | 832 (832/832) | 87.0/87.0/87 | 15.57 | 99.4 | 100 | 6 |
| 11 | 0029-p2fc-r3 | 00:29:19 | 9 | 0 | - | -/- | 2055/2045 | 2096/2084 | 2093 | 466.3 | 1.000 | 2.139 | 832 (832/832) | 87.8/88.0/88 | 16.35 | 87.9 | 100 | 2 |
| 12 | 0031-s0-r3 | 00:31:23 | 9 | 0 | - | -/- | 2030/2023 | 1971/1978 | 1975 | 384.9 | 0.999 | 2.445 | 832 (832/832) | 87.0/87.1/88 | 15.59 | 99.7 | 100 | 29 |
| 13 | 0033-p2-r3 | 00:33:26 | 9 | 0 | - | -/- | 1980/2000 | 1960/1958 | 1959 | 385.0 | 0.999 | 2.472 | 832 (832/832) | 87.0/87.3/88 | 15.62 | 99.5 | 100 | 3 |
| 14 | 0035-p2fc-r4 | 00:35:30 | 9 | 0 | - | -/- | 2074/2070 | 2091/2075 | 2084 | 471.2 | 1.011 | 2.157 | 832 (832/832) | 88.0/88.2/89 | 16.52 | 88.4 | 100 | 2 |
| 15 | 0037-s0-r4 | 00:37:33 | 9 | 0 | - | -/- | 1989/1975 | 1967/1978 | 1976 | 385.2 | 1.000 | 2.429 | 832 (832/832) | 87.6/87.9/88 | 15.65 | 99.5 | 100 | 43 |
| 16 | 0039-p2-r4 | 00:39:37 | 9 | 0 | - | -/- | 2015/2015 | 1901/1926 | 1917 | 381.9 | 0.990 | 2.488 | 832 (832/832) | 87.2/87.7/88 | 15.61 | 98.8 | 100 | 17 |
| 17 | 0041-p2f-r4 | 00:41:40 | 9 | 0 | - | -/- | 1910/1932 | 1941/1967 | 1959 | 386.8 | 0.998 | 2.454 | 832 (832/832) | 87.2/87.8/88 | 15.69 | 99.3 | 100 | 1 |
| 18 | 0043-s0-r5 | 00:43:44 | 9 | 0 | - | -/- | 2019/2008 | 1982/1986 | 1986 | 385.2 | 1.000 | 2.457 | 832 (832/832) | 87.2/87.9/88 | 15.69 | 99.5 | 100 | 4 |
| 19 | 0045-p2-r5 | 00:45:48 | 9 | 0 | - | -/- | 2002/2008 | 1950/1984 | 1971 | 385.6 | 1.000 | 2.471 | 832 (832/832) | 87.0/87.8/88 | 15.68 | 99.8 | 100 | 6 |
| 20 | 0047-p2f-r5 | 00:47:51 | 9 | 0 | - | -/- | 1929/1953 | 1946/1972 | 1963 | 386.8 | 0.998 | 2.455 | 832 (832/832) | 87.4/87.9/88 | 15.67 | 99.4 | 100 | 3 |
| 21 | 0049-p2fc-r5 | 00:49:55 | 9 | 0 | - | -/- | 2084/2080 | 2033/2045 | 2044 | 457.2 | 0.981 | 2.178 | 832 (832/832) | 88.0/88.6/89 | 16.41 | 88.5 | 100 | 3 |

W4c (20261123-0239):

| # | run | start | gap s | pre n | pre busy_t | pre P/E MHz | wu P/E MHz | win P/E MHz | res eff MHz | fps | fps_rel | median ms | GPU MHz mean (first5/last5) | GPU C first5/mean/max | GPU W | GPU util | thermal % | >6 frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0239-cold-d0 (unscored) | 02:39:49 | 356 | 0 | - | -/- | 3139/2857 | 1929/1921 | 1924 | 426.5 | 1.107 | 2.186 | - (-/-) | -/-/- | - | - | - | 14 |
| 2 | 0241-d0-r1 | 02:41:31 | 9 | 0 | - | -/- | 2007/2009 | 1972/1988 | 1982 | 421.8 | 1.095 | 2.246 | 1021 (1111/934) | 86.8/86.7/87 | 16.81 | 98.2 | 100 | 1 |
| 3 | 0243-B-r1 | 02:43:34 | 9 | 0 | - | -/- | 1996/2008 | 1965/1980 | 1975 | 388.5 | 1.012 | 2.472 | 855 (1066/832) | 86.8/86.1/87 | 15.56 | 99.3 | 100 | 2 |
| 4 | 0245-B-r2 | 02:45:36 | 9 | 0 | - | -/- | 1902/1934 | 1954/1958 | 1957 | 383.9 | 1.000 | 2.512 | 832 (832/832) | 86.6/86.8/87 | 15.43 | 99.7 | 100 | 1 |
| 5 | 0247-d0-r2 | 02:47:39 | 9 | 0 | - | -/- | 1920/1938 | 1980/1979 | 1981 | 385.0 | 0.999 | 2.471 | 832 (832/832) | 87.0/87.0/87 | 15.48 | 99.8 | 100 | 3 |
| 6 | 0249-d0-r3 | 02:49:42 | 9 | 0 | - | -/- | 2013/2008 | 1965/1979 | 1975 | 386.4 | 1.003 | 2.451 | 832 (832/832) | 87.0/87.0/87 | 15.58 | 99.6 | 100 | 1 |
| 7 | 0251-B-r3 | 02:51:45 | 9 | 0 | - | -/- | 1990/1979 | 1921/1937 | 1932 | 383.4 | 0.999 | 2.502 | 832 (832/832) | 87.0/87.0/87 | 15.56 | 99.8 | 100 | 22 |
| 8 | 0253-B-r4 | 02:53:47 | 9 | 0 | - | -/- | 1991/1990 | 1823/1837 | 1831 | 382.0 | 0.995 | 2.491 | 832 (832/832) | 87.0/87.0/87 | 15.54 | 99.2 | 100 | 35 |
| 9 | 0255-d0-r4 | 02:55:50 | 9 | 0 | - | -/- | 1937/1958 | 1951/1977 | 1969 | 385.0 | 0.999 | 2.493 | 832 (832/832) | 87.0/87.1/88 | 15.61 | 99.8 | 100 | 6 |
| 10 | 0257-d0-r5 | 02:57:52 | 9 | 0 | - | -/- | 2004/2014 | 1933/1957 | 1948 | 385.1 | 0.999 | 2.491 | 832 (832/832) | 87.0/87.4/88 | 15.61 | 99.5 | 100 | 3 |
| 11 | 0259-B-r5 | 02:59:55 | 9 | 0 | - | -/- | 1949/1962 | 1930/1947 | 1941 | 383.9 | 1.000 | 2.498 | 832 (832/832) | 87.0/87.4/88 | 15.59 | 99.6 | 100 | 2 |
| 12 | 0301-B-r6 | 03:01:57 | 9 | 0 | - | -/- | 1995/1993 | 1935/1966 | 1954 | 385.9 | 1.005 | 2.510 | 832 (832/832) | 87.0/87.6/88 | 15.63 | 99.9 | 100 | 0 |
| 13 | 0303-d0-r6 | 03:04:01 | 9 | 0 | - | -/- | 2030/2022 | 1986/2000 | 1996 | 385.6 | 1.001 | 2.465 | 832 (832/832) | 87.2/87.7/88 | 15.65 | 99.7 | 100 | 3 |

W6-2 (20261123-0313):

| # | run | start | gap s | pre n | pre busy_t | pre P/E MHz | wu P/E MHz | win P/E MHz | res eff MHz | fps | fps_rel | median ms | GPU MHz mean (first5/last5) | GPU C first5/mean/max | GPU W | GPU util | thermal % | >6 frames |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0313-cold-s0 (unscored) | 03:13:24 | 449 | 0 | - | -/- | 3324/3043 | 2057/2045 | 2051 | 448.3 | 1.164 | 1.986 | - (-/-) | -/-/- | - | - | - | 39 |
| 2 | 0315-s0-r1 | 03:15:07 | 9 | 0 | - | -/- | 2045/2045 | 1972/1983 | 1982 | 417.3 | 1.084 | 2.270 | 1069 (999/1128) | 86.6/86.7/87 | 17.30 | 95.3 | 100 | 3 |
| 3 | 0317-p2-r1 | 03:17:11 | 9 | 0 | - | -/- | 2028/2026 | 1977/1990 | 1987 | 394.2 | 1.023 | 2.418 | 884 (985/832) | 86.4/86.2/87 | 15.79 | 98.9 | 100 | 1 |
| 4 | 0319-p2f-r1 | 03:19:14 | 9 | 0 | - | -/- | 2003/2018 | 1969/1996 | 1987 | 387.7 | 1.005 | 2.446 | 832 (832/832) | 86.2/86.3/87 | 15.48 | 99.5 | 100 | 5 |
| 5 | 0321-p2fc-r1 | 03:21:18 | 9 | 0 | - | -/- | 2076/2061 | 2120/2105 | 2117 | 471.3 | 1.003 | 2.108 | 832 (832/832) | 87.0/87.5/88 | 16.38 | 88.4 | 100 | 2 |
| 6 | 0323-p2-r2 | 03:23:21 | 9 | 0 | - | -/- | 2015/2009 | 1950/1973 | 1965 | 385.6 | 1.001 | 2.469 | 832 (832/832) | 87.0/87.0/87 | 15.55 | 99.9 | 100 | 1 |
| 7 | 0325-p2f-r2 | 03:25:24 | 9 | 0 | - | -/- | 1973/1967 | 1968/1979 | 1976 | 385.9 | 1.000 | 2.442 | 832 (832/832) | 87.0/87.0/87 | 15.62 | 99.6 | 100 | 33 |
| 8 | 0327-p2fc-r2 | 03:27:28 | 9 | 0 | - | -/- | 2050/2075 | 2083/2084 | 2087 | 470.3 | 1.001 | 2.175 | 832 (832/832) | 87.8/88.0/88 | 16.48 | 86.6 | 100 | 40 |
| 9 | 0329-s0-r2 | 03:29:32 | 9 | 0 | - | -/- | 2025/2021 | 1952/1971 | 1966 | 381.9 | 0.992 | 2.476 | 832 (832/832) | 87.0/87.6/88 | 15.64 | 99.5 | 100 | 58 |
| 10 | 0331-p2f-r3 | 03:31:35 | 9 | 0 | - | -/- | 1964/1992 | 1973/1976 | 1974 | 385.9 | 1.000 | 2.449 | 832 (832/832) | 87.0/87.5/88 | 15.68 | 99.6 | 100 | 40 |
| 11 | 0333-p2fc-r3 | 03:33:39 | 9 | 0 | - | -/- | 2095/2080 | 2099/2094 | 2098 | 468.1 | 0.996 | 2.129 | 832 (832/832) | 88.0/88.3/89 | 16.54 | 88.8 | 100 | 34 |
| 12 | 0335-s0-r3 | 03:35:42 | 9 | 0 | - | -/- | 1974/1976 | 1934/1961 | 1951 | 383.7 | 0.997 | 2.467 | 832 (832/832) | 87.8/88.0/88 | 15.69 | 99.7 | 100 | 44 |
| 13 | 0337-p2-r3 | 03:37:46 | 9 | 0 | - | -/- | 1957/1966 | 1951/1965 | 1960 | 383.9 | 0.996 | 2.486 | 832 (832/832) | 87.4/87.8/88 | 15.69 | 99.6 | 100 | 40 |
| 14 | 0339-p2fc-r4 | 03:39:49 | 9 | 0 | - | -/- | 2075/2065 | 2003/2008 | 2010 | 451.5 | 0.961 | 2.195 | 832 (832/832) | 88.0/88.3/89 | 16.35 | 86.5 | 100 | 34 |
| 15 | 0341-s0-r4 | 03:41:52 | 9 | 0 | - | -/- | 1964/1982 | 1946/1951 | 1949 | 385.0 | 1.000 | 2.476 | 832 (832/832) | 88.0/88.0/88 | 15.75 | 99.5 | 100 | 3 |
| 16 | 0343-p2-r4 | 03:43:56 | 9 | 0 | - | -/- | 2000/2002 | 1979/1978 | 1979 | 385.2 | 1.000 | 2.448 | 832 (832/832) | 87.8/88.0/88 | 15.73 | 99.6 | 100 | 6 |
| 17 | 0345-p2f-r4 | 03:45:59 | 9 | 0 | - | -/- | 1975/1990 | 1935/1962 | 1952 | 386.5 | 1.002 | 2.472 | 832 (832/832) | 87.8/88.0/88 | 15.74 | 99.4 | 100 | 2 |
| 18 | 0348-s0-r5 | 03:48:03 | 9 | 0 | - | -/- | 1997/1997 | 1972/1991 | 1986 | 385.6 | 1.001 | 2.477 | 832 (832/832) | 87.6/88.0/88 | 15.70 | 99.8 | 100 | 5 |
| 19 | 0350-p2-r5 | 03:50:07 | 9 | 0 | - | -/- | 1986/1980 | 1909/1934 | 1926 | 375.5 | 0.975 | 2.527 | 832 (832/832) | 87.6/87.9/88 | 15.62 | 98.2 | 100 | 6 |
| 20 | 0352-p2f-r5 | 03:52:10 | 9 | 0 | - | -/- | 2005/2005 | 1962/1974 | 1971 | 385.1 | 0.998 | 2.443 | 832 (832/832) | 87.8/87.9/88 | 15.72 | 99.5 | 100 | 21 |
| 21 | 0354-p2fc-r5 | 03:54:14 | 9 | 0 | - | -/- | 2099/2089 | 2089/2080 | 2086 | 469.8 | 1.000 | 2.128 | 832 (832/832) | 88.0/88.6/89 | 16.63 | 88.1 | 100 | 3 |

All 7 folders: cold run / runs 2-3 (median) / the rest (median); Spearman over scored runs vs fps_rel:

| window | folder | fps_rel cold | fps_rel runs 2-3 | fps_rel rest | GPU C first5 | GPU MHz mean | GPU thermal % | win P MHz | rho GPU MHz vs fps_rel | rho GPU C vs fps_rel | rho run order vs fps_rel |
|---|---|---|---|---|---|---|---|---|---|---|---|
| W6-1 | 0009 | 1.037 | 1.152 | 1.000 | - / 86.3 / 87.0 | - / 1196 / 832 | - / 100 / 100 | 1817 / 2006 / 1969 | 0.53 (p 0.017) | -0.36 (p 0.120) | -0.60 (p 0.007) |
| W9-1 | 0108 | 1.135 | 1.110 | 1.000 | - / 86.8 / 87.0 | - / 1087 / 832 | - / 100 / 100 | 2440 / 2004 / 2189 | 0.70 (p 0.000) | -0.52 (p 0.024) | -0.59 (p 0.008) |
| W5b-1 | 0155 | 1.089 | 1.069 | 1.000 | - / 86.5 / 87.0 | - / 941 / 832 | - / 100 / 100 | 2016 / 1970 / 1939 | 0.65 (p 0.000) | -0.11 (p 0.651) | -0.20 (p 0.414) |
| W4c | 0239 | 1.107 | 1.053 | 1.000 | - / 86.8 / 87.0 | - / 938 / 832 | - / 100 / 100 | 1929 / 1968 / 1943 | 0.65 (p 0.021) | -0.21 (p 0.522) | -0.26 (p 0.437) |
| W6-2 | 0313 | 1.164 | 1.054 | 1.000 | - / 86.5 / 87.7 | - / 976 / 832 | - / 100 / 100 | 2057 / 1975 / 1969 | 0.52 (p 0.005) | -0.47 (p 0.038) | -0.50 (p 0.026) |
| W9-2 | 0401 | 1.169 | 1.032 | 0.999 | - / 86.2 / 87.1 | - / 898 / 832 | - / 100 / 100 | 2010 / 2031 / 2052 | 0.03 (p 0.897) | 0.44 (p 0.056) | 0.25 (p 0.292) |
| W5b-2 | 0451 | 1.147 | 0.991 | 1.000 | - / 86.7 / 87.0 | - / 1045 / 832 | - / 100 / 100 | 1963 / 1839 / 1953 | -0.01 (p 0.990) | 0.20 (p 0.447) | 0.03 (p 0.909) |

### 5.6 W5b-2 (0451) extra load after the CrossDeviceService holdback: timeline (W5b-1 for comparison)

Warm-up + window sys samples of all runs in time order; baseline = median ng_t of runs 8 onwards; "above" = 30 s rolling median of ng_t > baseline + 0.5 core. pre = host-only samples before the game starts (busy_t of the whole host).

20261123-0155: baseline ng_t 2.43; above in 30 of 2068 samples; first 02:11:09, last 02:26:16; per run: 0209-d11p-r3 3, 0213-d11t-r3 21, 0225-d11-r5 6

| # | run | start | pre n | pre busy_t | wu ng_t | win ng_t | win ng_t max | samples above |
|---|---|---|---|---|---|---|---|---|
| 1 | 0155-cold-d11 | 01:55:31 | 0 | - | 1.93 | 2.39 | 3.64 | 0 |
| 2 | 0157-d11-r1 | 01:57:14 | 0 | - | 2.35 | 2.46 | 4.12 | 0 |
| 3 | 0159-d11t-r1 | 01:59:16 | 0 | - | 2.50 | 2.59 | 3.96 | 0 |
| 4 | 0201-d11p-r1 | 02:01:19 | 0 | - | 2.56 | 2.45 | 4.19 | 0 |
| 5 | 0203-d11t-r2 | 02:03:22 | 0 | - | 2.30 | 2.36 | 4.50 | 0 |
| 6 | 0205-d11p-r2 | 02:05:24 | 0 | - | 2.50 | 2.58 | 4.71 | 0 |
| 7 | 0207-d11-r2 | 02:07:27 | 0 | - | 2.56 | 2.66 | 5.45 | 0 |
| 8 | 0209-d11p-r3 | 02:09:29 | 0 | - | 2.51 | 3.07 | 5.76 | 3 |

20261123-0451: baseline ng_t 2.43; above in 386 of 2070 samples; first 04:55:02, last 05:26:45; per run: 0453-d11-r1 34, 0455-d11t-r1 110, 0457-d11p-r1 106, 0459-d11t-r2 75, 0501-d11p-r2 44, 0520-d11p-r5 16, 0526-d11-r6 1

| # | run | start | pre n | pre busy_t | wu ng_t | win ng_t | win ng_t max | samples above |
|---|---|---|---|---|---|---|---|---|
| 1 | 0451-cold-d11 | 04:52:01 | 0 | - | 1.94 | 2.55 | 4.97 | 0 |
| 2 | 0453-d11-r1 | 04:53:43 | 0 | - | 2.55 | 3.53 | 7.49 | 34 |
| 3 | 0455-d11t-r1 | 04:55:48 | 0 | - | 3.80 | 3.37 | 5.48 | 110 |
| 4 | 0457-d11p-r1 | 04:57:52 | 0 | - | 3.62 | 3.76 | 5.50 | 106 |
| 5 | 0459-d11t-r2 | 04:59:56 | 0 | - | 3.48 | 2.84 | 4.40 | 75 |
| 6 | 0501-d11p-r2 | 05:01:59 | 0 | - | 3.16 | 2.46 | 3.49 | 44 |
| 7 | 0504-d11-r2 | 05:04:03 | 0 | - | 2.38 | 2.50 | 4.38 | 0 |
| 8 | 0506-d11p-r3 | 05:06:06 | 0 | - | 2.58 | 2.56 | 3.81 | 0 |

### 5.7 game.log warning lines (section 4 add-on): top patterns (digits/hex masked) over all 7 folders

| pattern | lines | runs with it | per folder |
|---|---|---|---|
| [krnl] [NtCreateFile] FAILED: path='d:\INSTALL#_#.DAT' -> # | 4590 | 135/135 | W6-1:714 W9-1:714 W5b-1:646 W4c:442 W6-2:714 W9-2:714 W5b-2:646 |
| [krnl] Stub XFileFsDeviceInformation! | 270 | 135/135 | W6-1:42 W9-1:42 W5b-1:38 W4c:26 W6-2:42 W9-2:42 W5b-2:38 |
| [krnl] IoDismountVolumeByFileHandle(#) - stub | 270 | 135/135 | W6-1:42 W9-1:42 W5b-1:38 W4c:26 W6-2:42 W9-2:42 W5b-2:38 |
| [krnl] [NtCreateFile] FAILED: path='d:\INSTALL#_#.HDR' -> # | 135 | 135/135 | W6-1:21 W9-1:21 W5b-1:19 W4c:13 W6-2:21 W9-2:21 W5b-2:19 |
| [krnl] __imp__XamBackgroundDownloadSetMode STUB | 135 | 135/135 | W6-1:21 W9-1:21 W5b-1:19 W4c:13 W6-2:21 W9-2:21 W5b-2:19 |
| [core] Shutdown wedged past the close request; hard-exiting. | 1 | 1/135 | W9-1:1 |

6 distinct warning patterns in total; patterns present in fewer than half of the runs: [core] Shutdown wedged past the close request; hard-exiting. (1 runs)

## Files

- `build/agent8/readout/w-followup/audit/audit.md`
- `build/agent8/readout/w-followup/audit/audit.json`
- `build/agent8/readout/w-followup/audit/runs.csv`
- `build/agent8/readout/w-followup/audit/spikes.csv`
- `build/agent8/readout/w-followup/audit/gamelog.csv`
- `build/agent8/readout/w-followup/audit/audit.py`
- `build/agent8/readout/w-followup/audit/audit5.py`
- `build/agent8/readout/w-followup/audit/findings.md`
- `build/agent8/readout/w-followup/audit/timerq3-20261123-0009.csv` / `.txt` (W6-1)
- `build/agent8/readout/w-followup/audit/timerq3-20261123-0108.csv` / `.txt` (W9-1)
- `build/agent8/readout/w-followup/audit/timerq3-20261123-0155.csv` / `.txt` (W5b-1)
- `build/agent8/readout/w-followup/audit/timerq3-20261123-0239.csv` / `.txt` (W4c)
- `build/agent8/readout/w-followup/audit/timerq3-20261123-0313.csv` / `.txt` (W6-2)
- `build/agent8/readout/w-followup/audit/timerq3-20261123-0401.csv` / `.txt` (W9-2)
- `build/agent8/readout/w-followup/audit/timerq3-20261123-0451.csv` / `.txt` (W5b-2)

Runtime 77.7 s.

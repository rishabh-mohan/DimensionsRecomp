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


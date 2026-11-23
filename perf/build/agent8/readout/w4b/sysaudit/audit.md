# W4b disturbance audit (read-only): D4 = build\agent8\matrix\20261122-1541

Helper of Agent 8, 2026-11-22 ~20:10. Inputs (read-only): runs\*\sys.csv, proc.csv, run.json and results.csv (fps_mean). Scripts in this dir: sysaudit.py and extra.py (stdlib, `python -B`). Full tables:
- report.md: window, warm-up and context per run, group comparison, bursts, activity, Spearman, cross-matrix.
- extra.md: slow/fast-state split, 10 s bins for runs 3, 4, 9 and 10.

Data: runs.csv (per run x phase), samples.csv (per 1 s sample), activity.csv (samples inside each logged activity interval), summary.json.

## 1. Method and formula

- **Window and warm-up.** Window = run.json measure_start..measure_end (epoch). A 1 s sys.csv sample counts if the centre of its interval is inside (50 samples per scored run, 30 for the cold run). Warm-up = ff_signal_epoch_s..measure_start. Sample spacing: median 1.000 s, max 1.067 s, no gaps.
- **Busy-share check** (1850 window and warm-up samples):
  - Total: cpu_util_pct/cpu_perf_pct has max 1.000, with 0.2 % of samples > 1.00 and none > 1.02. So "busy time share = util/perf" holds for the total.
  - P cluster: p_util/(p_eff/1700) has max 1.034, 0.1 % of samples > 1.02.
  - E cluster: e_util/(e_eff/base_mhz) has 1.8 % of samples > 1.02 (max 1.031). With e_util/(e_eff/f_E), where f_E = 1.5*base_mhz - 850 (an empirical fit; base_mhz ranged 1585-1700), the max is 1.003 and none are > 1.02.
- **Time-based busy LPs (used):** busy_t = 4*min(1, p_util*1700/(100*p_eff)) + 8*min(1, e_util*f_E/(100*e_eff)), in logical CPUs of 12. The add-on's 12*min(1, util/perf) (column ngA) gives the same per-run medians within 0.03.
- **Work-based LPs (Agent 1's method):** util_LP = 4*p_util/100 + 8*e_util/100, i.e. work in nominal-clock cores.
- **Game CPU:** game = slope of proc.csv cpu_s over the same samples. It equals the proc.csv cpu_cores mean and the run.json value (report.md context table).
- **Non-game CPU,** per 1 s sample, reported as median / mean / p90 / max per run:
  - ng_t = busy_t - game (time-based; this is the add-on's "background").
  - ng_u = util_LP - game (work-based).
  - Caveat: ng_u subtracts game CPU *time* from frequency-scaled work, so in the slow state it under-counts non-game work by about 2/3 of the game's E-core time. The P/E split of the game's threads is not in sys.csv or proc.csv.
- **Other definitions.**
  - P busy % and E busy % = the clipped cluster shares above.
  - P sat % = share of samples with P busy >= 97 %.
  - P MHz and E MHz = means of p_eff and e_eff.
  - Slow state = e_eff < 800 MHz.
  - Burst = a 1 s sample above the pooled p90 of the rest group.
  - Spearman rho uses a two-sided permutation p (5000 permutations). fps_rel = fps / median fps of the same build (valid runs).

## 2. Context

- **Unchanged in every run:** fg_game 100 %, input_desktop Default, screensaver 0, ac 1, overlay best_efficiency, one scheme.
- **No user input:** window idle_min rose from 690 s (cold run) to 2741 s.
- **Run flags:** ticks_skipped 0 everywhere. build_procs 0 except run 6: 3 clang++ in the window and 1 in the warm-up (that run is already valid_timing=False).
- **Missing data:** the tz_* columns are empty, so thermal limits cannot be checked.
- **P clock:** flat at 1852-1940 MHz in all scored windows.
- **E clock:** this is the variable.
  - In the slow state (79 % of window samples), e_util is pinned at ~33 %, E busy is 99.9 % and E runs at ~550-600 MHz.
  - Runs 2-9 began their windows partly in the fast state (E<800 share 34-96 %).
  - From run 10 (16:01:21) on, the slow state persisted: runs 10-17 windows are 90-100 % slow, and warm-ups 11-17 are 68-95 % slow.

## 3. Window table

F = run with known activity. Columns: game, busy_t, ng_* and P/E busy are in cores/LPs or %. MHz = mean e_eff.

| # | run | fps | game | busy_t | ng_t med (p90/max) | ng_u med (mean) | P busy | E busy | P util | P sat | E MHz | E<800 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1541-cold-d0 (unscored) | 325.9 | 2.92 | 10.60 | 8.11 (8.81/8.99) | 8.27 (8.36) | 86.4 | 89.3 | 102.7 | 23 | 1730 | 0 |
| 2 | 1542-d0-r1 | 256.4 | 3.37 | 11.64 | 8.39 (8.75/8.96) | 8.09 (6.24) | 95.2 | 98.0 | 105.9 | 48 | 1152 | 36 |
| 3 F | 1545-B-r1 | 317.1 | 3.14 | 9.98 | 6.76 (8.16/8.30) | 5.20 (4.91) | 79.5 | 85.1 | 87.4 | 2 | 1175 | 34 |
| 4 F | 1547-d3-r1 | 231.0 | 3.45 | 11.27 | 8.12 (8.43/8.94) | 3.19 (4.21) | 90.6 | 95.5 | 99.4 | 28 | 830 | 70 |
| 5 F | 1549-d11t-r1 | 206.4 | 3.00 | 11.56 | 8.59 (8.82/9.78) | 3.63 (3.69) | 91.4 | 98.8 | 99.5 | 12 | 573 | 96 |
| 6 F | 1551-B-r2 (invalid) | 234.5 | 3.43 | 11.59 | 8.19 (8.41/8.90) | 3.38 (4.32) | 92.3 | 98.8 | 102.7 | 18 | 767 | 64 |
| 7 F | 1553-d3-r2 | 298.6 | 3.18 | 10.30 | 7.66 (8.18/8.78) | 3.31 (4.58) | 80.2 | 88.7 | 91.0 | 6 | 1031 | 54 |
| 8 | 1556-d11t-r2 | 220.6 | 2.94 | 11.53 | 8.67 (8.87/9.05) | 3.75 (3.87) | 90.5 | 98.9 | 100.8 | 10 | 587 | 96 |
| 9 | 1558-d0-r2 | 270.4 | 3.34 | 10.85 | 7.85 (8.22/8.58) | 3.21 (3.86) | 83.5 | 93.9 | 94.8 | 0 | 785 | 78 |
| 10 F | 1600-d3-r3 | 198.4 | 3.52 | 11.73 | 8.20 (8.37/8.65) | 3.27 (3.27) | 93.3 | 99.9 | 103.3 | 15 | 551 | 100 |
| 11 | 1602-d11t-r3 | 277.2 | 2.81 | 10.78 | 8.02 (8.65/9.36) | 3.59 (3.64) | 80.0 | 94.7 | 91.0 | 0 | 613 | 96 |
| 12 | 1604-d0-r3 | 223.1 | 3.53 | 11.55 | 8.06 (8.25/8.55) | 3.16 (3.17) | 90.2 | 99.3 | 101.0 | 4 | 555 | 100 |
| 13 | 1606-B-r3 | 230.8 | 3.48 | 11.62 | 8.15 (8.31/8.88) | 3.24 (3.23) | 90.9 | 99.8 | 101.1 | 2 | 545 | 100 |
| 14 | 1608-d11t-r4 | 254.9 | 2.90 | 11.21 | 8.39 (8.85/9.35) | 3.64 (3.63) | 85.4 | 97.5 | 96.0 | 4 | 573 | 100 |
| 15 | 1611-d0-r4 | 213.9 | 3.52 | 11.62 | 8.14 (8.38/8.81) | 3.22 (3.21) | 91.5 | 99.5 | 101.7 | 8 | 553 | 100 |
| 16 | 1613-B-r4 | 275.8 | 3.35 | 10.76 | 7.56 (8.10/8.83) | 3.17 (3.19) | 82.2 | 93.5 | 92.4 | 2 | 638 | 90 |
| 17 | 1615-d3-r4 | 266.8 | 3.37 | 10.78 | 7.49 (8.10/8.59) | 3.08 (3.07) | 81.6 | 94.0 | 93.1 | 0 | 610 | 98 |

**State split** (scored windows, extra.md):

| state | n | ng_t | ng_u | E busy |
|---|---|---|---|---|
| fast (E >= 800 MHz) | 144 | 6.76 | 6.15 | 83.6 % |
| slow (E < 800 MHz) | 652 | 8.14 | 3.26 | 99.9 % |

**Warm-ups** (report.md):

| warm-ups | E MHz | E<800 | ng_t | ng_u | P util | P sat | E busy |
|---|---|---|---|---|---|---|---|
| runs 2-9 | 1594-1780 | 0-5 % | 5.16-7.54 | 5.62-7.59 | 75-95 | 0-15 % | 67-88 % |
| run 10 | 1423 | 10 % | 8.64 | 8.36 | 110.6 | 49 % | 99.2 % |
| runs 11-17 (mostly slow) | 602-883 | 68-95 % | – | 3.09-3.80 | – | – | – |

## 4. Runs with known activity vs the rest

Flagged = {3, 4, 5, 6, 7, 10} (n=6). Rest = {2, 8, 9, 11-17} (n=10). Values are medians over runs [min..max].

| metric | flagged | rest | flagged above rest max |
|---|---|---|---|
| ng_t med | 8.16 [6.76..8.59] | 8.10 [7.49..8.67] | none (run 3 is lowest of all) |
| ng_t p90 | 8.39 [8.16..8.82] | 8.34 [8.10..8.87] | none |
| ng_u med | 3.35 [3.19..5.20] | 3.23 [3.08..8.09] | none |
| ng_u mean | 4.26 [3.27..4.91] | 3.43 [3.07..6.24] | none |
| P busy % | 91.0 [79.5..93.3] | 87.8 [80.0..95.2] | none |
| P util % | 99.4 [87.4..103.3] | 98.4 [91.0..105.9] | none |
| P sat share | 0.13 [0.02..0.28] | 0.03 [0.00..0.48] | none |
| E busy % | 97.1 [85.1..99.95] | 97.7 [93.5..99.8] | run 10 (99.95, saturation) |
| E<800 share | 0.67 [0.34..1.00] | 0.97 [0.36..1.00] | – |
| slow-state ng_t | 8.15 [8.00..8.60] | 8.10 [7.51..8.68] | none |
| slow-state ng_u | 3.17 [2.97..3.61] | 3.19 [3.09..3.74] | none |
| slow-state P util | 100.2 [95.6..103.2] | 99.6 [91.7..102.1] | run 10 (103.2) |

- **Higher flagged ng_u mean and P sat.** Both come from the clock-state mix, not from activity. Runs 3, 4, 6 and 7 began their windows in the fast state, where ng_u is high (fast-state ng_u medians 5.47-6.37). Run 2 (rest) shows the same: 32 fast samples, fast ng_u 8.36.
- **Bursts.** Rest-pooled p90: ng_t 8.69, ng_u 4.13.
  - ng_u: 143 window samples above p90, 136 of them in the fast state, i.e. the window starts of runs 2, 3, 4, 6, 7 and 9. Per run: run 2 32/50, run 3 33/50, run 4 15/50, run 6 19/50, run 7 23/50, run 9 11/50, run 10 0/50.
  - ng_t: 75 samples above p90, 60 of them in the slow state. They are concentrated in the d11t runs (5: 20/50, 8: 23/50, 14: 11/49) because those runs have lower game CPU (2.81-3.00). Flagged runs: 3: 0, 4: 4, 6: 1, 7: 1, 10: 0.

## 5. Logged activity vs 1 s samples

Full detail is in report.md "Known activity" and activity.csv.

| activity | where | finding |
|---|---|---|
| A2 prep-b4 15:46:11-22 | run 3: last 8 s of warm-up + first 4 s of window | 10 s bins: ng_t 5.31-5.73 rises to 7.08 / 6.73, ng_u 5.44-6.32 rises to 6.78 / 6.44, i.e. about +1.4 time-based and +0.5-1 work-based cores. 0 samples above the ng_t p90. Run 3 had the highest fps of the matrix (317). |
| A2 shell 15:47:17-19 | between runs 3 and 4 | no game samples |
| A2 shell 15:47:40-44 | run 4 warm-up, 50 s before its window | 5 samples: ng_t mean 8.25 (max 9.15) vs warm-up median 7.04; ng_u 8.27 vs 7.14; 2 of 5 above the ng_t p90. 10 s bin 15:47:43: ng_t 8.04 / ng_u 8.21 vs 5.51-7.56 / 6.33-7.53 in later warm-up bins. |
| A11 reads/write 15:48-15:55 | runs 4-7 | no distinct signal beyond the fast-state window starts (which run 2 also shows) |
| A9 clang++ ~15:51-15:53 | end of run 5 window; run 6 | run 5 overlap: ng_t 8.41 vs run median 8.59, ng_u 3.68 vs 3.63. Run 6 is unremarkable (ng_t 8.19, ng_u 3.38). |
| A11 listings/Get-Process 16:01:54-16:02:36 | run 10 window (27 samples) | ng_t 8.17 vs run median 8.20, ng_u 3.27 vs 3.27, 0 samples above p90. No visible effect: the E cluster was already saturated. |
| **unlogged** 16:00:31-16:01:20 | run 10 warm-up | 10 s bins: ng_t 8.32-8.76, ng_u 7.89-9.28, P util 103-117, E busy 97-100 % at 1375-1630 MHz. Then E fell to 835 MHz (16:01:21 bin) and to ~550 MHz for the whole window and the rest of the matrix. No logged activity at that time. |

## 6. Correlation with window fps (Spearman)

Columns: all scored runs (n=16) / valid runs only (n=15, run 6 excluded), then fps_rel (n=16 / n=15).

| metric | rho vs fps | rho vs fps_rel |
|---|---|---|
| ng_t med | -0.73 (p 0.003) / -0.75 (p 0.001) | -0.58 / -0.60 |
| ng_u med | +0.08 (p 0.78) / +0.06 | +0.12 / +0.14 |
| ng_u mean | +0.32 (p 0.24) / +0.31 | +0.26 / +0.34 |
| P busy % | -0.77 (p 0.001) / -0.83 | -0.80 / -0.80 |
| P util % | -0.76 / -0.81 | -0.78 / -0.77 |
| P sat share | -0.52 (p 0.04) / -0.57 | -0.51 / -0.50 |
| E busy % | -0.91 / -0.90 | -0.84 / -0.84 |
| E MHz | +0.75 / +0.78 | +0.65 / +0.74 |
| E<800 share | -0.62 / -0.65 | -0.44 / -0.55 |
| game cores | -0.47 (p 0.07) / -0.43 | -0.58 / -0.54 |
| idle_min | -0.07 / -0.10 | -0.05 / -0.12 |

- Work-based non-game CPU does not track fps. Time-based non-game CPU, P busy and the E-clock state do.
- ng_t, P busy and E busy are mechanically tied to the E-clock state, so this is correlation through a common factor, not proof of cause.

## 7. Assessment (factual)

- **Inside the windows:** no scored window has elevated non-game CPU by either metric, overall or state-matched. No logged activity lines up with a burst in a scored window.
- **Run 6:** already invalid (clang++). In sys.csv it is unremarkable.
- **Run 10, the only candidate.** It was the slowest run: fps 198, fps_rel 0.80.
  - Its warm-up (16:00:31-16:01:20) carried more non-game work than any other warm-up: ng_u 8.36 vs 5.62-7.59. During it the E cluster was saturated at high clock and P sat was 49 %. The source is not logged.
  - In its window it has the highest slow-state P util (103.2 vs rest max 102.1). Otherwise the window is indistinguishable from runs 12, 13 and 15.
  - Call: possibly disturbed before the window, by an unattributed load.
- **Runs 3 and 4:** about +1-core bumps in time with A2's activity, in warm-up or the first seconds of the window, within normal range. Not disturbed.
- **Time trend (not a disturbance):** runs 10-17 ran entirely in the slow E state, while runs 2-9 began their windows partly fast.

## 8. Gap: non-game (work) 3.3 vs add-on "background" 8.14

- **The 8.14 reproduces.** The add-on's 8.14 is the time-based number: ng_t median over scored windows = 8.13 (ngA 8.14).
- **Why it is ~8.** In 79 % of window samples the 8 E cores are 100 % busy at ~1/3 clock. So ng_t is about 4*P busy + 8 - game, which is about 8.1 by construction. That is occupancy, not demand:
  - The same background work fills about 3x the time at 550 MHz.
  - The number saturates at 12 - game - P idle.
  - ng_t rises as the clock falls (fast 6.76 to slow 8.14) while ng_u falls (6.15 to 3.26).
- **The work-based number has its own limit.** In the slow state ng_u is structurally pinned: E work is capped at 8 x 0.333, so ng_u is about 2.67 + 4*P util/100 - game, roughly 3.2-3.4 whatever the background demand. Extra load then shows up as less CPU for the game (higher P busy, lower fps), not as higher ng_u.
- **Which definition is right for "other load on the machine":** the CPU work of non-game processes.
  - From sys.csv this is best approximated by work-based non-game CPU in unsaturated (fast-state) samples.
  - The proper source is per-process CPU (process sampler or ETW).
  - The time-based busy - game number should be read as occupancy / a SAT flag, not as other agents' load.
  - For reference, no-game per-process baselines are about 3-3.7 LPs (W4b pre-start, Agent 8 15:05) and 2.8-3.1 (W5, Agent 1, MsMpEng ~0.9).
- **W4b vs W5 at comparable clocks.** Work-based non-game in fast-state warm-ups:

| warm-ups | W4b | W5 |
|---|---|---|
| fast-state warm-ups | runs 2-9: 5.62-7.59 | 1757-base-r1: 4.88 |
| cold run | 8.27 | 6.38 |

So W4b had about 1-3 nominal cores more non-game work while other agents were active.
- **Open caveat.** Even unsaturated, non-game with the game running exceeds the no-game baseline (W5 fast state ng_t ~5.6-5.7, ng_u 4.8-5.7 vs ~3). Possible causes:
  - work induced by the game but charged to other processes (DWM, driver/DPC, samplers);
  - under-counted game CPU.

  sys.csv cannot split this.

# W5 disturbance audit (read-only): D5 = build\agent8\matrix\20261122-1756

Helper of Agent 8, 2026-11-22 ~20:10. The method, formulas and the gap discussion are the same as in ..\..\w4b\sysaudit\audit.md (sections 1 and 8), produced by the same scripts (w4b\sysaudit\sysaudit.py and extra.py).

Files in this dir:
- report.md: all tables.
- extra.md: slow/fast split, 10 s bins for 1757, 1808, 1817, 1819 and 1821, plus 1757 window coverage.
- runs.csv, samples.csv, activity.csv, summary.json.

## 1. Checks and context

- **Busy-share check** (1740 samples): util/perf max 0.994 (none > 1.00). E raw with f_E = 1.5*base-850 has max 1.002; with base_mhz, 1.6 % of samples are > 1.02. P raw max 0.983.
- **Unchanged in every run:** fg_game 100 %, input_desktop Default, screensaver 0, ac 1, overlay best_efficiency, one scheme.
- **Run flags:** ticks_skipped 0 and build_procs 0 everywhere.
- **No user input:** last input ~17:56:00; window idle_min rose from 74 s to 1974 s.
- **Missing data:** the tz_* columns are empty.
- **P clock:** flat at 1920-1945 MHz. P sat is 0 except 1804 (2 %).
- **1757-base-r1 wall-clock step.**
  - The QPC window is 50.007 s, but the epoch span measure_start..end is 58.3 s (17:59:00.680-17:59:58.985). sys.csv has a 9.29 s epoch gap at 17:59:48, i.e. the system clock stepped about +8.3 s inside the window.
  - The window holds 50 sys samples by epoch; 7 of them have no proc value. Game cores come from run.json (2.90).
  - No real-time samples appear to be lost.

## 2. Window table

S = one of Agent 1's 3 slow runs. MHz = mean e_eff.

| # | run | fps | game | busy_t | ng_t med (p90/max) | ng_u med (mean) | P busy | E busy | P util | E MHz | E<800 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1756-cold-base (unscored) | 395.8 | 2.72 | 8.31 | 5.55 (6.36/7.84) | 5.70 (6.05) | 64.7 | 71.6 | 77.4 | 1683 | 0 |
| 2 | 1757-base-r1 | 384.6 | 2.90* | 8.66 | 5.70 (7.38/8.20) | 4.40 (4.27) | 64.5 | 76.0 | 73.3 | 1174 | 26 |
| 3 | 1800-s0-r1 | 333.4 | 3.19 | 10.47 | 7.33 (8.05/8.62) | 3.54 (3.53) | 76.4 | 92.7 | 86.4 | 725 | 68 |
| 4 | 1802-d11-r1 | 350.3 | 3.18 | 10.28 | 7.16 (7.73/8.04) | 3.41 (3.38) | 73.7 | 91.7 | 84.3 | 719 | 86 |
| 5 | 1804-d11t-r1 | 338.5 | 2.72 | 10.18 | 7.51 (8.35/9.08) | 3.56 (3.57) | 72.3 | 91.0 | 82.6 | 676 | 94 |
| 6 | 1806-d11p-r1 | 343.3 | 2.77 | 10.12 | 7.51 (8.33/8.89) | 3.41 (3.42) | 72.5 | 90.3 | 82.6 | 660 | 88 |
| 7 S | 1808-s0-r2 | 309.9 | 3.38 | 10.80 | 7.65 (8.05/8.75) | 3.03 (3.01) | 80.3 | 94.9 | 91.5 | 597 | 94 |
| 8 | 1810-d11-r2 | 351.3 | 3.19 | 9.95 | 6.72 (7.63/8.48) | 3.04 (3.04) | 71.3 | 88.7 | 80.9 | 699 | 86 |
| 9 | 1813-d11t-r2 | 358.8 | 2.67 | 9.41 | 6.62 (7.83/9.11) | 3.32 (3.33) | 67.0 | 84.1 | 76.4 | 728 | 76 |
| 10 | 1815-d11p-r2 | 356.9 | 2.69 | 9.60 | 6.88 (7.89/8.70) | 3.19 (3.22) | 67.4 | 86.4 | 76.8 | 684 | 94 |
| 11 S | 1817-base-r2 | 289.2 | 3.46 | 11.42 | 8.01 (8.17/8.69) | 3.20 (3.19) | 86.7 | 99.4 | 98.5 | 554 | 100 |
| 12 | 1819-d11-r3 | 352.5 | 3.16 | 9.85 | 6.69 (7.74/8.21) | 3.10 (3.11) | 70.6 | 87.9 | 80.0 | 725 | 76 |
| 13 S | 1821-d11t-r3 | 277.1 | 2.84 | 11.00 | 8.17 (8.53/9.62) | 3.39 (3.41) | 80.8 | 97.1 | 91.4 | 550 | 100 |
| 14 | 1823-d11p-r3 | 335.3 | 2.78 | 10.37 | 7.85 (8.38/8.99) | 3.30 (3.30) | 73.5 | 92.9 | 83.8 | 609 | 96 |
| 15 | 1825-base-r3 | 355.6 | 3.15 | 9.81 | 6.60 (7.70/8.37) | 3.13 (3.14) | 70.2 | 87.5 | 79.4 | 740 | 72 |
| 16 | 1827-s0-r3 | 360.0 | 3.08 | 9.66 | 6.45 (7.58/8.35) | 3.18 (3.16) | 68.8 | 86.3 | 77.9 | 749 | 74 |

\* run.json window_cpu_cores_mean (no proc slope for this window).

- **No SAT runs:** busy_t max is 11.42 of 12.
- **Add-on reference:** the add-on's W5 reference background of 7.16 equals the ng_t median over scored runs (7.158).
- **Warm-ups:**
  - Cold run: ng_u 6.38 at E 1965 MHz.
  - 1757: 4.88 at 1767 MHz, 0 % slow.
  - 1800: 4.91 (35 % slow).
  - Other warm-ups: 3.24-3.85 (E<800 33-67 %; 1821 93 %).

## 3. Agent 1's claims

- **Non-game ~3.0-3.6 LPs (utility x threads minus game), ~6 in the cold run.** Reproduced: ng_u mean is 3.01-3.57 in 14 of 15 scored runs. The exceptions:
  - 1757-base-r1 is 4.27: 74 % of its window is in the fast state, with fast-sample median 4.77.
  - The cold run is 6.05 mean / 5.70 median.

  Caveat: in the slow state this number is structurally pinned near 3.2-3.4 (E work capped at 8 x 0.333), so it does not show extra demand there (W4b audit, section 8).
- **The 3 slow runs (1808, 1817, 1821) vs the 12 others** (medians [min..max]):

| metric | slow runs | others | check |
|---|---|---|---|
| P util | 91.5 [91.4..98.5] | 80.4 [73.3..86.4] | all 3 above the others' max ✓ |
| E MHz | 554 [550..597] | 722 [609..1174] | all 3 below the others' min ✓ |
| E busy | 97.1 [94.9..99.4] | 88.3 [76.0..92.9] | all 3 above |
| P busy | 80.8 [80.3..86.7] | 71.0 [64.5..76.4] | all 3 above |
| E<800 share | 1.00 [0.94..1.00] | 0.81 [0.26..0.96] | – |
| P MHz | 1931 [1923..1938] | 1934 [1920..1945] | flat ✓ |
| ng_t | 8.01 [7.65..8.17] | 6.80 [5.70..7.85] | 1817 and 1821 above the others' max |
| ng_u | 3.20 [3.03..3.39] | 3.31 [3.04..4.40] | not elevated; 1808 is below the others' min |
| game cores | 3.38 [2.84..3.46] | 3.08 [2.67..3.19] | +0.1-0.3 over same-build peers |

  Slow-state samples only: P util 94.6 vs 80.4, ng_u 3.20 vs 3.25, ng_t 8.01 vs 7.00.

## 4. Logged activity

| activity | overlap | finding |
|---|---|---|
| A1 cron 18:10 | 1808 window (44 samples) | ng_u 2.99 (run median 3.03), 0 samples above the ng_u p90 (3.79). The E clock was already low from 18:09:14 in the warm-up. |
| A1 reply 18:21-18:22 | end of 1819's window (20 samples) | ng_u 3.04, 0 samples above p90 |
| A1 reply 18:21-18:22 | 1821 boot, warm-up and first 21 s of window | warm-up ng_u median 3.53 (other warm-ups 3.24-3.85); window overlap ng_u 3.45, 3 samples above p90. 1821's warm-up was the only one in the slow state from 18:21:48 on. |

- 2 of the 3 slow runs overlap an Agent 1 turn (no commands). 1817 overlaps nothing and is just as slow.
- Bursts (rest p90: ng_t 8.05, ng_u 3.79):
  - ng_u: only 1757 has a cluster, 26/43 samples, all in its fast-state first ~25 s.
  - ng_t: concentrated in the slow runs (1817 19/50, 1821 31/50) and the d11t/d11p runs (lower game CPU).

## 5. Correlation with window fps (Spearman, n=15, all scored runs valid; game n=14)

| metric | rho vs fps | rho vs fps_rel |
|---|---|---|
| ng_t med | -0.94 (p<0.001) | -0.88 |
| ng_u med | -0.03 (p 0.92) | +0.11 |
| ng_u mean | -0.02 | +0.15 |
| P busy % | -0.96 | -0.93 |
| P util % | -0.95 | -0.93 |
| E busy % | -0.98 | -0.96 |
| E MHz | +0.85 | +0.83 |
| E<800 share | -0.69 | -0.73 |
| game cores | -0.46 (p 0.11) | -0.52 |
| idle_min | +0.04 | -0.10 |

## 6. W5 vs W4b

Medians over scored runs:

| metric | W5 | W4b |
|---|---|---|
| ng_t | 7.16 | 8.13 |
| ng_u med | 3.30 | 3.29 |
| ng_u mean | 3.30 | 3.67 |
| busy_t | 10.12 | 11.40 |
| P busy / P util | 72 / 83 | 90 / 99 |
| E busy | 90 | 98 |
| E MHz | 699 | 611 |
| E<800 share | 0.86 | 0.96 |
| game | 3.12 | 3.36 (different builds) |

- **ng_t.** W4b's higher ng_t comes mostly from more time in the saturated slow state.
- **ng_u.** The equal ng_u medians are structural (slow state: 3.27 vs 3.26).
- **Comparable clocks.** Where clocks are comparable, i.e. fast-state warm-ups at ~1.6-1.8 GHz E, W4b's non-game work was higher:

| sample | W4b | W5 |
|---|---|---|
| fast-state warm-ups | 5.62-7.59 | 4.88 (1757) |
| cold-run warm-up | 8.27 | 6.38 |

So W4b ran about 1-3 nominal cores higher, consistent with other agents working. W5's slow state (and its 3 slow runs) occurred without logged activity, with Defender at ~0.9 core.

## 7. Assessment (factual)

- No W5 run shows a non-game work burst attributable to logged activity.
- The 3 slow runs match Agent 1's description: P util 91-98.5 %, E ~550-600 MHz, E saturated. Their work-based non-game CPU is not elevated; their time-based non-game CPU is high because E sat at ~1/3 clock.
- What drives the E-clock drop is not visible in sys.csv: tz_* is empty, and power-limit data is not logged.

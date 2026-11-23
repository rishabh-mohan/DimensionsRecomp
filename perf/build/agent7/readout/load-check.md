# Load checks for the W9 / W5b read-outs (load_check.py)

- inputs: `build/agent7/readout/pool-W9.md`, `pool-W5b.md` (section 8 run tables) and ng_t from `build/agent8/readout/w-followup/audit/audit.md` section 2 (135 runs read)
- loaded run = ng_t >= 2.8 non-game busy cores (window mean); baselines = medians of the same arm's kept runs below that
- "cores at constant core x MHz" = baseline cores x baseline eff MHz / run eff MHz: what the run would use if it did the same cycles per second at its lower clock; rest = observed - that

## W9

### Host load per pass (audit ng_t)

- W9-1: ng_t median 2.37 [2.16..2.77] over 20 kept runs; 0 at or above 2.8; median of the rest 2.37; Spearman rho(ng_t, raw fps) across runs -0.73 (n 20, p 0.000), within arm -0.85 (p 0.000, approximate)
- W9-2: ng_t median 2.58 [2.21..4.06] over 20 kept runs; 8 at or above 2.8; median of the rest 2.33; Spearman rho(ng_t, raw fps) across runs -0.82 (n 20, p 0.000), within arm -0.78 (p 0.000, approximate)

### Loaded runs vs the same arm

| arm | runs with ng_t < 2.8 | median fps | median raw ms | median T-std ms | median cores | median eff MHz |
|---|---|---|---|---|---|---|
| off | 7 | 385.8 | 2.458 | 2.437 | 2.520 | 1966 |
| q0 | 7 | 385.8 | 2.472 | 2.460 | 2.490 | 2040 |
| q125 | 6 | 389.5 | 2.303 | 2.309 | 1.805 | 2170 |
| q250 | 5 | 389.1 | 2.324 | 2.329 | 1.730 | 2171 |
| q500 | 7 | 389.8 | 2.310 | 2.313 | 1.730 | 2205 |

| run | arm | ng_t | eff MHz (vs arm) | fps (vs arm) | raw median ms (vs arm) | T-std median ms (vs arm) | cores (vs arm) | cores at constant core x MHz | rest |
|---|---|---|---|---|---|---|---|---|---|
| 0407-q125-r1 | q125 | 4.06 | 1857 (-14.4 %) | 365.0 (-6.3 %) | 2.477 (+7.6 %) | 2.444 (+5.8 %) | 2.15 (+0.34) | 2.11 | +0.04 |
| 0423-q125-r3 | q125 | 4.03 | 1853 (-14.6 %) | 368.4 (-5.4 %) | 2.510 (+9.0 %) | 2.488 (+7.7 %) | 2.13 (+0.32) | 2.11 | +0.02 |
| 0409-q250-r1 | q250 | 3.72 | 1894 (-12.8 %) | 378.2 (-2.8 %) | 2.460 (+5.9 %) | 2.453 (+5.3 %) | 2.11 (+0.38) | 1.98 | +0.13 |
| 0419-q500-r2 | q500 | 3.36 | 1947 (-11.7 %) | 385.8 (-1.0 %) | 2.356 (+2.0 %) | 2.356 (+1.9 %) | 2.03 (+0.30) | 1.96 | +0.07 |
| 0425-q250-r3 | q250 | 3.14 | 1996 (-8.1 %) | 386.4 (-0.7 %) | 2.356 (+1.4 %) | 2.360 (+1.3 %) | 1.98 (+0.25) | 1.88 | +0.10 |
| 0421-off-r2 | off | 2.92 | 1907 (-3.0 %) | 382.2 (-0.9 %) | 2.469 (+0.4 %) | 2.441 (+0.2 %) | 2.54 (+0.02) | - (spin arm) | - |
| 0417-q250-r2 | q250 | 2.91 | 2075 (-4.4 %) | 379.1 (-2.6 %) | 2.377 (+2.3 %) | 2.377 (+2.1 %) | 1.93 (+0.20) | 1.81 | +0.12 |
| 0440-q0-r4 | q0 | 2.81 | 1996 (-2.2 %) | 384.0 (-0.5 %) | 2.473 (+0.0 %) | 2.458 (-0.1 %) | 2.46 (-0.03) | - (spin arm) | - |

### Thread cycles (busy % x eff GHz; a rough cycle rate)

| group | runs | Main XThread | GPU Commands |
|---|---|---|---|
| off | 8 | 152.9-169.7 (median 156.7) | 111.6-123.7 (median 116.4) |
| q0 | 8 | 150.2-163.2 (median 155.8) | 114.7-119.8 (median 117.4) |
| q125-q500, ng_t < 2.8 | 18 | 135.4-149.5 (median 142.7) | 95.9-107.5 (median 102.5) |
| q125-q500, ng_t >= 2.8 | 6 | 142.6-147.3 (median 146.3) | 101.2-108.5 (median 105.1) |

Per loaded q run: 0407-q125-r1 Main 142.6 GPU 107.7; 0409-q250-r1 Main 146.0 GPU 106.3; 0417-q250-r2 Main 147.3 GPU 108.5; 0419-q500-r2 Main 146.8 GPU 104.0; 0423-q125-r3 Main 146.6 GPU 103.0; 0425-q250-r3 Main 145.9 GPU 101.2

### Cores differences between arms (pooled linear CI, all 5 arms in the pool)

- full pool: q500 - off (n 8 v 8): -0.749 [-0.861, -0.637] * (df 35); q500 - q250 (n 8 v 8): -0.104 [-0.216, +0.008] (df 35); q500 - q125 (n 8 v 8): -0.133 [-0.245, -0.020] * (df 35); q250 - q125 (n 8 v 8): -0.029 [-0.141, +0.083] (df 35)
- no-lowclk: q500 - off (n 7 v 8): -0.788 [-0.849, -0.727] * (df 31); q500 - q250 (n 7 v 7): -0.107 [-0.170, -0.044] * (df 31); q500 - q125 (n 7 v 6): -0.088 [-0.154, -0.022] * (df 31); q250 - q125 (n 7 v 6): +0.019 [-0.047, +0.085] (df 31)
- no-slow-q: q500 - off (n 8 v 8): -0.749 [-0.826, -0.672] * (df 31); q500 - q250 (n 8 v 6): -0.051 [-0.134, +0.032] (df 31); q500 - q125 (n 8 v 6): -0.049 [-0.132, +0.034] (df 31); q250 - q125 (n 6 v 6): +0.002 [-0.087, +0.090] (df 31)
- no-flagged: q500 - off (n 7 v 8): -0.788 [-0.841, -0.735] * (df 28); q500 - q250 (n 7 v 5): -0.069 [-0.130, -0.009] * (df 28); q500 - q125 (n 7 v 5): -0.071 [-0.132, -0.011] * (df 28); q250 - q125 (n 5 v 5): -0.002 [-0.067, +0.063] (df 28)

### Paired per-round counts

- q0 vs off, raw median ms, all rounds: n 8, higher 8/8 (sign p 0.008), mean +2.65 %, median +0.45 %, per round r1 +12.43, r2 +0.49, r3 +0.12, r4 +1.31, r5 +6.02, r6 +0.12, r7 +0.41, r8 +0.28
- q0 vs off, raw median ms, without each pass's round 1: n 6, higher 6/6 (sign p 0.031), mean +0.45 %, median +0.35 %, per round r2 +0.49, r3 +0.12, r4 +1.31, r6 +0.12, r7 +0.41, r8 +0.28
- q0 vs off, T-std median ms, all rounds: n 8, higher 8/8 (sign p 0.008), mean +2.84 %, median +0.82 %, per round r1 +12.06, r2 +0.86, r3 +0.32, r4 +1.48, r5 +6.05, r6 +0.78, r7 +0.78, r8 +0.41
- q0 vs off, T-std median ms, without each pass's round 1: n 6, higher 6/6 (sign p 0.031), mean +0.77 %, median +0.78 %, per round r2 +0.86, r3 +0.32, r4 +1.48, r6 +0.78, r7 +0.78, r8 +0.41
- q500 vs off, raw fps, all rounds: n 8, higher 6/8 (sign p 0.289), mean -1.22 %, median +1.03 %, per round r1 -11.95, r2 +1.11, r3 +1.64, r4 +0.91, r5 -4.94, r6 +0.94, r7 +1.19, r8 +1.35
- q500 vs off, raw fps, without each pass's round 1: n 6, higher 6/6 (sign p 0.031), mean +1.19 %, median +1.15 %, per round r2 +1.11, r3 +1.64, r4 +0.91, r6 +0.94, r7 +1.19, r8 +1.35
- q500 vs off, raw median ms, all rounds: n 8, higher 1/8 (sign p 0.070), mean -3.18 %, median -5.86 %, per round r1 +10.27, r2 -6.21, r3 -6.76, r4 -5.75, r5 -0.39, r6 -4.58, r7 -6.06, r8 -5.96
- q500 vs off, raw median ms, without each pass's round 1: n 6, higher 0/6 (sign p 0.031), mean -5.89 %, median -6.01 %, per round r2 -6.21, r3 -6.76, r4 -5.75, r6 -4.58, r7 -6.06, r8 -5.96
- q125 vs off, raw fps, all rounds: n 8, higher 5/8 (sign p 0.727), mean -2.43 %, median +0.62 %, per round r1 -10.86, r2 +0.52, r3 +1.70, r4 +0.72, r5 -10.74, r6 +2.30, r7 -4.36, r8 +1.25
- q125 vs off, raw fps, without each pass's round 1: n 6, higher 5/6 (sign p 0.219), mean +0.35 %, median +0.99 %, per round r2 +0.52, r3 +1.70, r4 +0.72, r6 +2.30, r7 -4.36, r8 +1.25
- q250 vs off, raw fps, all rounds: n 8, higher 5/8 (sign p 0.727), mean -2.07 %, median +0.19 %, per round r1 -12.13, r2 +0.08, r3 +1.72, r4 +0.62, r5 -7.51, r6 -0.81, r7 +0.31, r8 +1.17
- q250 vs off, raw fps, without each pass's round 1: n 6, higher 5/6 (sign p 0.219), mean +0.52 %, median +0.47 %, per round r2 +0.08, r3 +1.72, r4 +0.62, r6 -0.81, r7 +0.31, r8 +1.17
- q500 vs off, raw fps, without rounds holding a flagged run (no-flagged list): n 7, higher 5/7 (sign p 0.453), mean -1.52 %, median +1.11 %, per round r1 -11.95, r2 +1.11, r3 +1.64, r4 +0.91, r5 -4.94, r7 +1.19, r8 +1.35
- q500 vs off, raw median ms, without rounds holding a flagged run (no-flagged list): n 7, higher 1/7 (sign p 0.125), mean -2.98 %, median -5.96 %, per round r1 +10.27, r2 -6.21, r3 -6.76, r4 -5.75, r5 -0.39, r7 -6.06, r8 -5.96

## W5b

### Host load per pass (audit ng_t)

- W5b-1: ng_t median 2.56 [2.36..3.36] over 18 kept runs; 2 at or above 2.8; median of the rest 2.55; Spearman rho(ng_t, raw fps) across runs -0.65 (n 18, p 0.004), within arm -0.67 (p 0.002, approximate)
- W5b-2: ng_t median 2.53 [2.43..3.76] over 18 kept runs; 7 at or above 2.8; median of the rest 2.49; Spearman rho(ng_t, raw fps) across runs -0.11 (n 18, p 0.660), within arm -0.32 (p 0.193, approximate)

### Loaded runs vs the same arm

| arm | runs with ng_t < 2.8 | median fps | median raw ms | median T-std ms | median cores | median eff MHz |
|---|---|---|---|---|---|---|
| d11 | 11 | 385.1 | 2.512 | 2.512 | 2.540 | 1957 |
| d11t | 8 | 385.2 | 2.518 | 2.520 | 2.300 | 1966 |
| d11p | 8 | 385.4 | 2.502 | 2.502 | 2.325 | 1948 |

| run | arm | ng_t | eff MHz (vs arm) | fps (vs arm) | raw median ms (vs arm) | T-std median ms (vs arm) | cores (vs arm) | cores at constant core x MHz | rest |
|---|---|---|---|---|---|---|---|---|---|
| 0457-d11p-r1 | d11p | 3.76 | 1780 (-8.6 %) | 386.0 (+0.1 %) | 2.457 (-1.8 %) | 2.450 (-2.1 %) | 2.37 (+0.04) | 2.54 | -0.17 |
| 0453-d11-r1 | d11 | 3.53 | 1848 (-5.6 %) | 393.0 (+2.1 %) | 2.483 (-1.2 %) | 2.484 (-1.1 %) | 2.60 (+0.06) | - (spin arm) | - |
| 0455-d11t-r1 | d11t | 3.37 | 1873 (-4.7 %) | 367.1 (-4.7 %) | 2.647 (+5.1 %) | 2.639 (+4.7 %) | 2.37 (+0.07) | 2.41 | -0.04 |
| 0213-d11t-r3 | d11t | 3.36 | 1829 (-7.0 %) | 371.7 (-3.5 %) | 2.606 (+3.5 %) | 2.589 (+2.7 %) | 2.39 (+0.09) | 2.47 | -0.08 |
| 0209-d11p-r3 | d11p | 3.07 | 1854 (-4.8 %) | 381.8 (-0.9 %) | 2.544 (+1.7 %) | 2.546 (+1.8 %) | 2.37 (+0.04) | 2.44 | -0.07 |
| 0520-d11p-r5 | d11p | 2.90 | 1906 (-2.2 %) | 375.6 (-2.6 %) | 2.586 (+3.4 %) | 2.586 (+3.4 %) | 2.38 (+0.05) | 2.38 | +0.00 |
| 0524-d11p-r6 | d11p | 2.88 | 1901 (-2.4 %) | 382.1 (-0.9 %) | 2.529 (+1.1 %) | 2.529 (+1.1 %) | 2.37 (+0.04) | 2.38 | -0.01 |
| 0510-d11t-r3 | d11t | 2.87 | 1916 (-2.5 %) | 379.3 (-1.5 %) | 2.528 (+0.4 %) | 2.516 (-0.2 %) | 2.31 (+0.01) | 2.36 | -0.05 |
| 0459-d11t-r2 | d11t | 2.84 | 1937 (-1.5 %) | 376.6 (-2.2 %) | 2.582 (+2.5 %) | 2.581 (+2.4 %) | 2.34 (+0.04) | 2.33 | +0.01 |

Loaded runs vs d11's ng_t < 2.8 median fps (385.1): 0457-d11p-r1 d11p +0.2 %; 0453-d11-r1 d11 +2.1 %; 0455-d11t-r1 d11t -4.7 %; 0213-d11t-r3 d11t -3.5 %; 0209-d11p-r3 d11p -0.9 %; 0520-d11p-r5 d11p -2.5 %; 0524-d11p-r6 d11p -0.8 %; 0510-d11t-r3 d11t -1.5 %; 0459-d11t-r2 d11t -2.2 %

### Cores differences (pooled linear CI)

- full pool: d11t - d11 (n 12 v 12): -0.219 [-0.251, -0.188] * (df 33); d11p - d11 (n 12 v 12): -0.203 [-0.235, -0.172] * (df 33); d11t - d11p (n 12 v 12): -0.016 [-0.047, +0.016] (df 33)

### Paired per-round counts

- d11t vs d11, raw median ms, all rounds: n 12, higher 11/12 (sign p 0.006), mean +1.33 %, median +0.46 %, per round r1 +2.58, r2 -1.27, r3 +2.52, r4 +0.24, r5 +0.24, r6 +1.08, r7 +6.60, r8 +2.79, r9 +0.28, r10 +0.04, r11 +0.56, r12 +0.36
- d11t vs d11, raw median ms, without each pass's round 1: n 10, higher 9/10 (sign p 0.021), mean +0.68 %, median +0.32 %, per round r2 -1.27, r3 +2.52, r4 +0.24, r5 +0.24, r6 +1.08, r8 +2.79, r9 +0.28, r10 +0.04, r11 +0.56, r12 +0.36
- d11p vs d11, raw median ms, all rounds: n 12, higher 5/12 (sign p 0.774), mean +0.53 %, median -0.38 %, per round r1 +6.42, r2 -0.67, r3 +0.08, r4 -0.83, r5 +0.32, r6 -0.60, r7 -1.05, r8 -0.52, r9 -0.24, r10 -0.52, r11 +3.19, r12 +0.76
- d11p vs d11, raw median ms, without each pass's round 1: n 10, higher 4/10 (sign p 0.754), mean +0.10 %, median -0.38 %, per round r2 -0.67, r3 +0.08, r4 -0.83, r5 +0.32, r6 -0.60, r8 -0.52, r9 -0.24, r10 -0.52, r11 +3.19, r12 +0.76
- d11t vs d11, raw fps, all rounds: n 12, higher 3/12 (sign p 0.146), mean -1.28 %, median -0.47 %, per round r1 -1.95, r2 +0.44, r3 -2.57, r4 -0.23, r5 -0.70, r6 -0.16, r7 -6.59, r8 -2.23, r9 -1.48, r10 -0.18, r11 +0.18, r12 +0.05
- d11t vs d11, raw fps, without each pass's round 1: n 10, higher 3/10 (sign p 0.344), mean -0.69 %, median -0.21 %, per round r2 +0.44, r3 -2.57, r4 -0.23, r5 -0.70, r6 -0.16, r8 -2.23, r9 -1.48, r10 -0.18, r11 +0.18, r12 +0.05
- d11p vs d11, raw fps, all rounds: n 12, higher 7/12 (sign p 0.774), mean -0.73 %, median +0.04 %, per round r1 -4.63, r2 +0.23, r3 +0.08, r4 +0.16, r5 +0.00, r6 +0.13, r7 -1.78, r8 +0.05, r9 +0.23, r10 +0.03, r11 -2.44, r12 -0.80
- d11p vs d11, raw fps, without each pass's round 1: n 10, higher 7/10 (sign p 0.344), mean -0.23 %, median +0.07 %, per round r2 +0.23, r3 +0.08, r4 +0.16, r5 +0.00, r6 +0.13, r8 +0.05, r9 +0.23, r10 +0.03, r11 -2.44, r12 -0.80
- d11t vs d11, raw p99 ms, all rounds: n 12, higher 7/12 (sign p 0.774), mean +1.18 %, median +1.25 %, per round r1 +1.76, r2 +1.25, r3 +4.08, r4 +0.00, r5 +2.25, r6 -0.41, r7 +1.83, r8 +1.24, r9 +5.24, r10 -0.83, r11 -1.85, r12 -0.42
- d11t vs d11, raw p99 ms, without each pass's round 1: n 10, higher 5/10 (sign p 1.000), mean +1.06 %, median +0.62 %, per round r2 +1.25, r3 +4.08, r4 +0.00, r5 +2.25, r6 -0.41, r8 +1.24, r9 +5.24, r10 -0.83, r11 -1.85, r12 -0.42
- d11p vs d11, raw p99 ms, all rounds: n 12, higher 4/12 (sign p 0.388), mean +0.07 %, median -0.21 %, per round r1 +3.74, r2 -0.84, r3 -2.04, r4 -0.41, r5 -0.20, r6 -1.65, r7 +0.00, r8 -0.21, r9 +0.63, r10 +0.62, r11 -0.21, r12 +1.46
- d11p vs d11, raw p99 ms, without each pass's round 1: n 10, higher 3/10 (sign p 0.344), mean -0.28 %, median -0.21 %, per round r2 -0.84, r3 -2.04, r4 -0.41, r5 -0.20, r6 -1.65, r8 -0.21, r9 +0.63, r10 +0.62, r11 -0.21, r12 +1.46
- d11t vs d11, raw median ms, without rounds holding an audit-flagged run: n 9, higher 8/9 (sign p 0.039), mean +0.73 %, median +0.36 %, per round r1 +2.58, r2 -1.27, r4 +0.24, r5 +0.24, r6 +1.08, r8 +2.79, r10 +0.04, r11 +0.56, r12 +0.36
- d11t vs d11, raw fps, without rounds holding an audit-flagged run: n 9, higher 3/9 (sign p 0.508), mean -0.53 %, median -0.18 %, per round r1 -1.95, r2 +0.44, r4 -0.23, r5 -0.70, r6 -0.16, r8 -2.23, r10 -0.18, r11 +0.18, r12 +0.05
- d11p vs d11, raw median ms, without rounds holding an audit-flagged run: n 10, higher 4/10 (sign p 0.754), mean +0.73 %, median -0.38 %, per round r1 +6.42, r2 -0.67, r4 -0.83, r5 +0.32, r6 -0.60, r8 -0.52, r9 -0.24, r10 -0.52, r11 +3.19, r12 +0.76
- d11p vs d11, raw fps, without rounds holding an audit-flagged run: n 10, higher 6/10 (sign p 0.754), mean -0.70 %, median +0.04 %, per round r1 -4.63, r2 +0.23, r4 +0.16, r5 +0.00, r6 +0.13, r8 +0.05, r9 +0.23, r10 +0.03, r11 -2.44, r12 -0.80

- check: t_crit(35) = 2.0301, t_crit(7) = 2.3646, t_crit(11) = 2.2010

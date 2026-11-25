## CF1 read-out tables (readout_cf.py; bootstrap 10000 draws, seed 1; check-defaults D9936C56)
out dir: `build\agent8\matrix\20261125-1255`; runs 19; ncpu 12

> Note (M10 C2): a raw "equal" claim printed below for a tail metric (p99, 1% low) is quoted as "not shown different" (n.s.d.) in the READOUT; tails are never claimed equal. Non-tail metrics (fps, cores) may be called equal only by the CI-within-margin rule.

### Runs

| run | rnd | pos | arm | counts | proof | func | sys.csv | runner flags (info / excl.) | GPU MHz | eff MHz | non-game (M12 / sys) | fps | p99 | 1% low ms | cores | median | STUCK | misses | stop_line |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1255-cold-ship | 0 | 1 | ship | - | PASS | PASS | 31 | light_share_high / - | - | 3040 | 5.80 / 2.36 | 485.4 | 4.107 | 4.342 | 1.36 | 2.102 | 0 | 0 | set |
| 1257-ship-r1 | 1 | 1 | ship | Y | PASS | PASS | 31 | light_share_high / - | 1635 | 2299 | 3.30 / 1.53 | 496.6 | 3.917 | 4.155 | 1.45 | 2.207 | 0 | 0 | set |
| 1259-s0-r1 | 1 | 2 | s0 | Y | PASS | PASS | 31 | light_share_high / - | 1627 | 1993 | 3.23 / 1.84 | 453.9 | 4.817 | 5.185 | 2.50 | 2.016 | 0 | 0 | set |
| 1301-win3-r1 | 1 | 3 | win3 | Y | PASS | PASS | 31 | light_share_high / - | 1582 | 2275 | 3.26 / 1.59 | 492.6 | 4.164 | 4.381 | 1.50 | 2.103 | 0 | 0 | set |
| 1303-s0-r2 | 2 | 1 | s0 | Y | PASS | PASS | 31 | light_share_high / - | 1575 | 2018 | 3.15 / 1.70 | 455.0 | 4.880 | 5.234 | 2.45 | 1.970 | 0 | 0 | set |
| 1305-win3-r2 | 2 | 2 | win3 | Y | PASS | PASS | 31 | light_share_high / - | 1560 | 2320 | 3.16 / 1.47 | 496.1 | 4.014 | 4.303 | 1.49 | 2.168 | 0 | 0 | set |
| 1307-ship-r2 | 2 | 3 | ship | Y | PASS | PASS | 31 | light_share_high / - | 1552 | 2301 | 3.25 / 1.52 | 493.7 | 4.160 | 4.365 | 1.45 | 2.102 | 0 | 0 | set |
| 1309-win3-r3 | 3 | 1 | win3 | Y | PASS | PASS | 31 | light_share_high / - | 1560 | 2061 | 4.10 / 2.56 | 481.9 | 4.130 | 5.079 | 1.74 | 2.181 | 0 | 0 | set |
| 1311-ship-r3 | 3 | 2 | ship | Y | PASS | PASS | 31 | light_share_high nongame_load / - | 1552 | 1977 | 4.40 FLAG / 2.87 | 482.3 | 4.038 | 4.325 | 1.80 | 2.195 | 0 | 0 | set |
| 1313-s0-r3 | 3 | 3 | s0 | Y | PASS | PASS | 31 | light_share_high / - | 1560 | 2012 | 3.23 / 1.83 | 448.1 | 4.975 | 5.316 | 2.47 | 2.044 | 0 | 0 | set |
| 1315-ship-r4 | 4 | 1 | ship | Y | PASS | PASS | 31 | light_share_high / - | 1552 | 2324 | 3.14 / 1.44 | 494.8 | 4.179 | 4.419 | 1.51 | 2.102 | 0 | 0 | set |
| 1317-s0-r4 | 4 | 2 | s0 | Y | PASS | PASS | 31 | light_share_high / - | 1552 | 2026 | 3.14 / 1.73 | 453.1 | 4.994 | 5.376 | 2.45 | 2.000 | 0 | 0 | set |
| 1319-win3-r4 | 4 | 3 | win3 | Y | PASS | PASS | 31 | light_share_high / - | 1537 | 2335 | 3.13 / 1.47 | 494.0 | 4.183 | 4.424 | 1.44 | 2.101 | 0 | 0 | set |
| 1321-s0-r5 | 5 | 1 | s0 | Y | PASS | PASS | 31 | light_share_high / - | 1522 | 1991 | 3.32 / 1.88 | 445.6 | 4.921 | 5.278 | 2.49 | 2.034 | 0 | 0 | set |
| 1323-win3-r5 | 5 | 2 | win3 | Y | PASS | PASS | 31 | light_share_high / - | 1530 | 2257 | 3.29 / 1.66 | 493.1 | 4.133 | 4.342 | 1.58 | 2.124 | 0 | 0 | set |
| 1325-ship-r5 | 5 | 3 | ship | Y | PASS | PASS | 31 | light_share_high / - | 1552 | 2187 | 3.58 / 2.00 | 485.6 | 4.197 | 4.507 | 1.54 | 2.110 | 0 | 0 | set |
| 1328-win3-r6 | 6 | 1 | win3 | Y | PASS | PASS | 31 | light_share_high / - | 1537 | 2260 | 3.51 / 1.84 | 492.8 | 4.020 | 4.289 | 1.52 | 2.200 | 0 | 0 | set |
| 1330-ship-r6 | 6 | 2 | ship | Y | PASS | PASS | 31 | light_share_high / - | 1537 | 2305 | 3.18 / 1.48 | 495.7 | 4.120 | 4.330 | 1.50 | 2.118 | 0 | 0 | set |
| 1332-s0-r6 | 6 | 3 | s0 | Y | PASS | PASS | 31 | light_share_high / - | 1507 | 1948 | 3.48 / 2.21 | 442.1 | 4.858 | 5.212 | 2.51 | 2.095 | 0 | 0 | set |

### Void and exclusion list

- arm ship: not void
- arm s0: not void
- arm win3: not void
- 1255-cold-ship (round 0, ship): runner: scored=False status=OK valid=True excluded=False 

M12 host-load gate: scored non-game median 3.25 cores, threshold 4.25; flagged: 1311-ship-r3 4.40

GPU plateau: round-2 counted runs 1575, 1560, 1552 MHz; rounds 3-6 median 1544 MHz; round 2 on plateau (>= 97 %): yes
GPU MHz by round (median of scored runs): r1 1627, r2 1560, r3 1560, r4 1552, r5 1530, r6 1537
sys sampler: stop_line set on 19/19 runs; sample_ms_max max -

### Headline: rounds 2-6, counted runs, M12-flagged runs kept

n per arm: ship 5, s0 5, win3 5

| arm | n | fps mean (median of runs) | p99 ms | 1% low ms | cores | median ms | GPU MHz | eff MHz |
|---|---|---|---|---|---|---|---|---|
| ship | 5 | 493.7 | 4.160 | 4.365 | 1.51 | 2.110 | 1552 | 2301 |
| s0 | 5 | 448.1 | 4.921 | 5.278 | 2.47 | 2.034 | 1552 | 2012 |
| win3 | 5 | 493.1 | 4.130 | 4.342 | 1.52 | 2.168 | 1537 | 2260 |

| pair | metric | A | B | A vs B % | 95% CI % | margin | claim | paired rounds % [t-CI] (A<B) |
|---|---|---|---|---|---|---|---|---|
| ship vs s0 | fps mean | 493.669 | 448.109 | +10.2 | [+6.8, +11.5] | - | ship higher | +9.3 [+7.2, +11.4] (0/5) |
| ship vs s0 | p99 ms | 4.160 | 4.921 | -15.5 | [-17.9, -13.9] | - | ship lower | -16.0 [-18.1, -13.8] (5/5) |
| ship vs s0 | 1% low ms | 4.365 | 5.278 | -17.3 | [-19.2, -14.6] | - | ship lower | -16.9 [-18.8, -15.0] (5/5) |
| ship vs s0 | process cores | 1.508 | 2.465 | -38.8 | [-41.1, -27.1] | - | ship lower | -37.2 [-43.5, -30.1] (5/5) |
| ship vs s0 | median ms (info) | 2.110 | 2.034 | +3.7 | [+0.7, +7.9] | - | ship higher | +4.8 [+1.7, +8.0] (0/5) |
| win3 vs s0 | fps mean | 493.067 | 448.109 | +10.0 | [+7.5, +11.4] | - | win3 higher | +9.5 [+7.6, +11.5] (0/5) |
| win3 vs s0 | p99 ms | 4.130 | 4.921 | -16.1 | [-19.5, -14.7] | - | win3 lower | -16.8 [-17.7, -16.0] (5/5) |
| win3 vs s0 | 1% low ms | 4.342 | 5.278 | -17.7 | [-19.6, -3.8] | - | win3 lower | -15.2 [-22.0, -7.9] (5/5) |
| win3 vs s0 | process cores | 1.517 | 2.465 | -38.5 | [-41.6, -29.2] | - | win3 lower | -37.3 [-42.8, -31.4] (5/5) |
| win3 vs s0 | median ms (info) | 2.168 | 2.034 | +6.6 | [+2.8, +9.8] | - | win3 higher | +6.2 [+3.5, +9.1] (0/5) |
| ship vs win3 | fps mean | 493.669 | 493.067 | +0.1 | [-2.2, +2.4] | ±2 | not shown different | -0.2 [-1.2, +0.8] (2/5) |
| ship vs win3 | p99 ms | 4.160 | 4.130 | +0.7 | [-2.2, +4.0] | ±5 | equal | +1.0 [-1.8, +4.0] (2/5) |
| ship vs win3 | 1% low ms | 4.365 | 4.342 | +0.5 | [-16.5, +3.8] | ±5 | not shown different | -2.0 [-11.2, +8.2] (2/5) |
| ship vs win3 | process cores | 1.508 | 1.517 | -0.6 | [-15.6, +18.5] | ±5 | not shown different | +0.3 [-3.9, +4.5] (3/5) |
| ship vs win3 | median ms (info) | 2.110 | 2.168 | -2.7 | [-4.2, +1.2] | ±3 | not shown different | -1.4 [-3.7, +1.1] (3/5) |

### Rounds 2-6 without M12-flagged runs

n per arm: ship 4, s0 5, win3 5

| arm | n | fps mean (median of runs) | p99 ms | 1% low ms | cores | median ms | GPU MHz | eff MHz |
|---|---|---|---|---|---|---|---|---|
| ship | 4 | 494.2 | 4.170 | 4.392 | 1.50 | 2.106 | 1552 | 2303 |
| s0 | 5 | 448.1 | 4.921 | 5.278 | 2.47 | 2.034 | 1552 | 2012 |
| win3 | 5 | 493.1 | 4.130 | 4.342 | 1.52 | 2.168 | 1537 | 2260 |

| pair | metric | A | B | A vs B % | 95% CI % | margin | claim | paired rounds % [t-CI] (A<B) |
|---|---|---|---|---|---|---|---|---|
| ship vs s0 | fps mean | 494.240 | 448.109 | +10.3 | [+7.9, +11.6] | - | ship higher | +9.7 [+7.1, +12.3] (0/4) |
| ship vs s0 | p99 ms | 4.170 | 4.921 | -15.3 | [-17.2, -13.9] | - | ship lower | -15.2 [-16.4, -14.0] (4/4) |
| ship vs s0 | 1% low ms | 4.392 | 5.278 | -16.8 | [-18.7, -14.6] | - | ship lower | -16.5 [-18.6, -14.3] (4/4) |
| ship vs s0 | process cores | 1.502 | 2.465 | -39.1 | [-41.7, -37.4] | - | ship lower | -39.5 [-41.6, -37.3] (4/4) |
| ship vs s0 | median ms (info) | 2.106 | 2.034 | +3.5 | [+0.5, +6.9] | - | ship higher | +4.1 [+0.4, +8.0] (0/4) |
| win3 vs s0 | fps mean | 493.067 | 448.109 | +10.0 | [+7.5, +11.4] | - | win3 higher | +9.5 [+7.6, +11.5] (0/5) |
| win3 vs s0 | p99 ms | 4.130 | 4.921 | -16.1 | [-19.5, -14.7] | - | win3 lower | -16.8 [-17.7, -16.0] (5/5) |
| win3 vs s0 | 1% low ms | 4.342 | 5.278 | -17.7 | [-19.6, -3.8] | - | win3 lower | -15.2 [-22.0, -7.9] (5/5) |
| win3 vs s0 | process cores | 1.517 | 2.465 | -38.5 | [-41.6, -29.2] | - | win3 lower | -37.3 [-42.8, -31.4] (5/5) |
| win3 vs s0 | median ms (info) | 2.168 | 2.034 | +6.6 | [+2.8, +9.8] | - | win3 higher | +6.2 [+3.5, +9.1] (0/5) |
| ship vs win3 | fps mean | 494.240 | 493.067 | +0.2 | [-1.5, +2.6] | ±2 | not shown different | -0.3 [-1.8, +1.1] (2/4) |
| ship vs win3 | p99 ms | 4.170 | 4.130 | +1.0 | [-0.3, +4.1] | ±5 | equal | +1.9 [-0.6, +4.4] (1/4) |
| ship vs win3 | 1% low ms | 4.392 | 4.342 | +1.2 | [-15.8, +3.8] | ±5 | not shown different | +1.5 [-1.1, +4.2] (1/4) |
| ship vs win3 | process cores | 1.502 | 1.517 | -1.0 | [-16.3, +4.2] | ±5 | not shown different | -0.4 [-5.8, +5.2] (3/4) |
| ship vs win3 | median ms (info) | 2.106 | 2.168 | -2.9 | [-4.3, +0.2] | ±3 | not shown different | -1.9 [-4.7, +1.1] (3/4) |

### Side note: rounds 1-6 (with round 1; never decides)

n per arm: ship 6, s0 6, win3 6

| arm | n | fps mean (median of runs) | p99 ms | 1% low ms | cores | median ms | GPU MHz | eff MHz |
|---|---|---|---|---|---|---|---|---|
| ship | 6 | 494.2 | 4.140 | 4.347 | 1.50 | 2.114 | 1552 | 2300 |
| s0 | 6 | 450.6 | 4.901 | 5.256 | 2.48 | 2.025 | 1556 | 2002 |
| win3 | 6 | 492.9 | 4.131 | 4.361 | 1.51 | 2.146 | 1548 | 2268 |

| pair | metric | A | B | A vs B % | 95% CI % | margin | claim | paired rounds % [t-CI] (A<B) |
|---|---|---|---|---|---|---|---|---|
| ship vs s0 | fps mean | 494.240 | 450.584 | +9.7 | [+7.1, +11.1] | - | ship higher | +9.3 [+7.7, +10.9] (0/6) |
| ship vs s0 | p99 ms | 4.140 | 4.901 | -15.5 | [-19.1, -13.9] | - | ship lower | -16.4 [-18.4, -14.4] (6/6) |
| ship vs s0 | 1% low ms | 4.347 | 5.256 | -17.3 | [-19.7, -15.0] | - | ship lower | -17.4 [-19.3, -15.5] (6/6) |
| ship vs s0 | process cores | 1.502 | 2.478 | -39.4 | [-42.0, -32.6] | - | ship lower | -38.0 [-43.2, -32.3] (6/6) |
| ship vs s0 | median ms (info) | 2.114 | 2.025 | +4.4 | [+2.2, +9.2] | - | ship higher | +5.5 [+2.5, +8.7] (0/6) |
| win3 vs s0 | fps mean | 492.950 | 450.584 | +9.4 | [+7.8, +10.9] | - | win3 higher | +9.4 [+7.9, +10.9] (0/6) |
| win3 vs s0 | p99 ms | 4.131 | 4.901 | -15.7 | [-18.8, -14.2] | - | win3 lower | -16.3 [-17.8, -14.7] (6/6) |
| win3 vs s0 | 1% low ms | 4.361 | 5.256 | -17.0 | [-19.1, -9.6] | - | win3 lower | -15.3 [-20.4, -9.8] (6/6) |
| win3 vs s0 | process cores | 1.510 | 2.478 | -39.1 | [-41.1, -33.2] | - | win3 lower | -37.8 [-42.0, -33.2] (6/6) |
| win3 vs s0 | median ms (info) | 2.146 | 2.025 | +6.0 | [+2.9, +8.9] | - | win3 higher | +5.9 [+3.7, +8.2] (0/6) |
| ship vs win3 | fps mean | 494.240 | 492.950 | +0.3 | [-1.8, +1.5] | ±2 | equal | -0.1 [-0.9, +0.8] (2/6) |
| ship vs win3 | p99 ms | 4.140 | 4.131 | +0.2 | [-3.7, +3.5] | ±5 | equal | -0.1 [-3.8, +3.7] (3/6) |
| ship vs win3 | 1% low ms | 4.347 | 4.361 | -0.3 | [-9.3, +2.7] | ±5 | not shown different | -2.5 [-9.7, +5.2] (3/6) |
| ship vs win3 | process cores | 1.502 | 1.510 | -0.5 | [-10.4, +10.6] | ±5 | not shown different | -0.4 [-3.9, +3.2] (4/6) |
| ship vs win3 | median ms (info) | 2.114 | 2.146 | -1.5 | [-3.6, +3.6] | ±3 | not shown different | -0.3 [-3.5, +2.9] (3/6) |

### Rounds 3-6 (info only; round 2 is on the plateau)

n per arm: ship 4, s0 4, win3 4

| arm | n | fps mean (median of runs) | p99 ms | 1% low ms | cores | median ms | GPU MHz | eff MHz |
|---|---|---|---|---|---|---|---|---|
| ship | 4 | 490.2 | 4.149 | 4.375 | 1.53 | 2.114 | 1552 | 2246 |
| s0 | 4 | 446.8 | 4.948 | 5.297 | 2.48 | 2.039 | 1537 | 2002 |
| win3 | 4 | 492.9 | 4.131 | 4.383 | 1.55 | 2.152 | 1537 | 2258 |

| pair | metric | A | B | A vs B % | 95% CI % | margin | claim | paired rounds % [t-CI] (A<B) |
|---|---|---|---|---|---|---|---|---|
| ship vs s0 | fps mean | 490.216 | 446.849 | +9.7 | [+7.5, +11.5] | - | ship higher | +9.5 [+6.5, +12.5] (0/4) |
| ship vs s0 | p99 ms | 4.149 | 4.948 | -16.1 | [-18.5, -14.1] | - | ship lower | -16.3 [-19.2, -13.3] (4/4) |
| ship vs s0 | 1% low ms | 4.375 | 5.297 | -17.4 | [-19.2, -14.8] | - | ship lower | -17.0 [-19.7, -14.2] (4/4) |
| ship vs s0 | process cores | 1.525 | 2.478 | -38.4 | [-40.3, -27.4] | - | ship lower | -36.2 [-44.8, -26.3] (4/4) |
| ship vs s0 | median ms (info) | 2.114 | 2.039 | +3.7 | [+0.9, +7.7] | - | ship higher | +4.3 [+0.2, +8.6] (0/4) |
| win3 vs s0 | fps mean | 492.950 | 446.849 | +10.3 | [+7.7, +11.4] | - | win3 higher | +9.7 [+6.9, +12.5] (0/4) |
| win3 vs s0 | p99 ms | 4.131 | 4.948 | -16.5 | [-18.8, -14.7] | - | win3 lower | -16.6 [-17.6, -15.7] (4/4) |
| win3 vs s0 | 1% low ms | 4.383 | 5.297 | -17.3 | [-19.5, -4.1] | - | win3 lower | -14.6 [-24.2, -3.8] (4/4) |
| win3 vs s0 | process cores | 1.548 | 2.478 | -37.5 | [-41.9, -29.6] | - | win3 lower | -36.8 [-44.6, -28.0] (4/4) |
| win3 vs s0 | median ms (info) | 2.152 | 2.039 | +5.6 | [+1.8, +8.7] | - | win3 higher | +5.3 [+3.8, +6.9] (0/4) |
| ship vs win3 | fps mean | 490.216 | 492.950 | -0.6 | [-2.2, +1.7] | ±2 | not shown different | -0.2 [-1.6, +1.3] (1/4) |
| ship vs win3 | p99 ms | 4.149 | 4.131 | +0.4 | [-2.3, +3.1] | ±5 | equal | +0.4 [-2.8, +3.8] (2/4) |
| ship vs win3 | 1% low ms | 4.375 | 4.383 | -0.2 | [-16.1, +3.4] | ±5 | not shown different | -2.8 [-15.7, +12.0] (2/4) |
| ship vs win3 | process cores | 1.525 | 1.548 | -1.5 | [-14.2, +16.1] | ±5 | not shown different | +1.0 [-4.3, +6.6] (2/4) |
| ship vs win3 | median ms (info) | 2.114 | 2.152 | -1.8 | [-4.1, +2.5] | ±3 | not shown different | -0.9 [-4.0, +2.2] (2/4) |

### Order (N1): position within the round, headline set

| arm | positions (1st/2nd/3rd) | metric | median at 1st | median at later | n 1st / later |
|---|---|---|---|---|---|
| ship | 1/2/2 | fps mean | 494.812 | 489.644 | 1 / 4 |
| ship | 1/2/2 | p99 ms | 4.179 | 4.140 | 1 / 4 |
| ship | 1/2/2 | 1% low ms | 4.419 | 4.347 | 1 / 4 |
| ship | 1/2/2 | process cores | 1.508 | 1.519 | 1 / 4 |
| s0 | 2/1/2 | fps mean | 450.292 | 448.109 | 2 / 3 |
| s0 | 2/1/2 | p99 ms | 4.901 | 4.975 | 2 / 3 |
| s0 | 2/1/2 | 1% low ms | 5.256 | 5.316 | 2 / 3 |
| s0 | 2/1/2 | process cores | 2.472 | 2.465 | 2 / 3 |
| win3 | 2/2/1 | fps mean | 487.345 | 494.016 | 2 / 3 |
| win3 | 2/2/1 | p99 ms | 4.075 | 4.133 | 2 / 3 |
| win3 | 2/2/1 | 1% low ms | 4.684 | 4.342 | 2 / 3 |
| win3 | 2/2/1 | process cores | 1.631 | 1.492 | 2 / 3 |

### Claims (S1) and WC comparison (S2), headline set

- ship vs s0, fps mean: +10.2 % [+6.8, +11.5] -> ship higher
- ship vs s0, p99 ms: -15.5 % [-17.9, -13.9] -> ship lower
- ship vs s0, 1% low ms: -17.3 % [-19.2, -14.6] -> ship lower
- ship vs s0, process cores: -38.8 % [-41.1, -27.1] -> ship lower
- win3 vs s0, fps mean: +10.0 % [+7.5, +11.4] -> win3 higher
- win3 vs s0, p99 ms: -16.1 % [-19.5, -14.7] -> win3 lower
- win3 vs s0, 1% low ms: -17.7 % [-19.6, -3.8] -> win3 lower
- win3 vs s0, process cores: -38.5 % [-41.6, -29.2] -> win3 lower
- ship vs win3, fps mean: +0.1 % [-2.2, +2.4] -> not shown different
- ship vs win3, p99 ms: +0.7 % [-2.2, +4.0] -> equal
- ship vs win3, 1% low ms: +0.5 % [-16.5, +3.8] -> not shown different
- ship vs win3, process cores: -0.6 % [-15.6, +18.5] -> not shown different
- CF1 overall: ship vs win3 equal / not shown different on all four: yes; ship vs s0 fps CI > 0 and cores CI < 0: yes -> the shipped defaults reproduce win3

| pair | metric | CF1 % [CI] | WC pooled % [CI] | S2 |
|---|---|---|---|---|
| ship vs s0 | fps mean | +10.2 [+6.8, +11.5] | +7.7 [+6.3, +8.7] | consistent |
| ship vs s0 | p99 ms | -15.5 [-17.9, -13.9] | -14.8 [-17.1, -14.0] | consistent |
| ship vs s0 | 1% low ms | -17.3 [-19.2, -14.6] | -17.0 [-18.0, -14.9] | consistent |
| ship vs s0 | process cores | -38.8 [-41.1, -27.1] | -38.7 [-40.3, -35.2] | consistent |
| win3 vs s0 | fps mean | +10.0 [+7.5, +11.4] | +7.7 [+6.3, +8.7] | consistent |
| win3 vs s0 | p99 ms | -16.1 [-19.5, -14.7] | -14.8 [-17.1, -14.0] | consistent |
| win3 vs s0 | 1% low ms | -17.7 [-19.6, -3.8] | -17.0 [-18.0, -14.9] | consistent |
| win3 vs s0 | process cores | -38.5 [-41.6, -29.2] | -38.7 [-40.3, -35.2] | consistent |


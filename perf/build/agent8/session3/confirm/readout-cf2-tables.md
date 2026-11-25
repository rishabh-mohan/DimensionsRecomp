## CF2 read-out tables (readout_cf.py; bootstrap 10000 draws, seed 1; check-defaults D9936C56)
out dir: `build\agent8\matrix\20261125-1159`; runs 13; ncpu 12

> Note (M10 C2): a raw "equal" claim printed below for a tail metric (p99, 1% low) is quoted as "not shown different" (n.s.d.) in the READOUT; tails are never claimed equal. Non-tail metrics (fps, cores) may be called equal only by the CI-within-margin rule.

### Runs

| run | rnd | pos | arm | counts | proof | func | sys.csv | runner flags (info / excl.) | GPU MHz | eff MHz | non-game (M12 / sys) | fps | p99 | 1% low ms | cores | median | STUCK | misses | stop_line |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1159-cold-nf | 0 | 1 | nf | - | PASS | PASS | 31 | light_share_high / - | - | 3132 | 6.39 / 2.52 | 416.3 | 2.848 | 3.136 | 1.11 | 2.380 | 0 | 26 | set |
| 1201-nf-r1 | 1 | 1 | nf | Y | PASS | PASS | 31 | light_share_high / - | 1740 | 2454 | 3.95 / 1.80 | 465.7 | 2.751 | 3.102 | 1.62 | 2.130 | 0 | 26 | set |
| 1203-mc-r1 | 1 | 2 | mc | Y | PASS | PASS | 31 | light_share_high / - | 1740 | 2197 | 3.70 / 1.93 | 458.3 | 3.124 | 3.427 | 1.80 | 2.152 | 0 | 26 | set |
| 1205-mc-r2 | 2 | 1 | mc | Y | PASS | PASS | 31 | light_share_high / - | 1740 | 2118 | 3.91 / 2.29 | 439.5 | 4.434 | 5.097 | 1.86 | 2.164 | 0 | 26 | set |
| 1207-nf-r2 | 2 | 2 | nf | Y | PASS | PASS | 31 | light_share_high / - | 1740 | 2210 | 3.52 / 1.79 | 461.5 | 2.965 | 3.252 | 1.83 | 2.148 | 0 | 26 | set |
| 1209-nf-r3 | 3 | 1 | nf | Y | PASS | PASS | 31 | light_share_high / - | 1740 | 2190 | 3.67 / 1.90 | 458.8 | 3.202 | 4.239 | 1.77 | 2.145 | 0 | 26 | set |
| 1211-mc-r3 | 3 | 2 | mc | Y | PASS | PASS | 31 | light_share_high / - | 1740 | 2233 | 3.48 / 1.71 | 462.1 | 2.835 | 3.171 | 1.77 | 2.148 | 0 | 26 | set |
| 1213-mc-r4 | 4 | 1 | mc | Y | PASS | PASS | 31 | light_share_high / - | 1740 | 2164 | 3.63 / 1.94 | 459.5 | 3.098 | 3.427 | 1.89 | 2.151 | 0 | 26 | set |
| 1215-nf-r4 | 4 | 2 | nf | Y | PASS | PASS | 31 | light_share_high / - | 1740 | 2231 | 3.44 / 1.69 | 462.1 | 2.864 | 3.173 | 1.83 | 2.148 | 0 | 26 | set |
| 1217-nf-r5 | 5 | 1 | nf | Y | PASS | PASS | 31 | light_share_high / - | 1740 | 2207 | 3.52 / 1.81 | 457.8 | 3.211 | 3.978 | 1.78 | 2.151 | 0 | 26 | set |
| 1219-mc-r5 | 5 | 2 | mc | Y | PASS | PASS | 31 | light_share_high / - | 1740 | 2223 | 3.45 / 1.67 | 461.4 | 2.904 | 3.192 | 1.83 | 2.148 | 0 | 26 | set |
| 1222-mc-r6 | 6 | 1 | mc | Y | PASS | PASS | 31 | light_share_high / - | 1740 | 2184 | 3.50 / 1.82 | 459.9 | 3.102 | 3.475 | 1.81 | 2.148 | 0 | 26 | set |
| 1224-nf-r6 | 6 | 2 | nf | Y | PASS | PASS | 31 | light_share_high / - | 1740 | 2174 | 3.67 / 1.92 | 458.2 | 3.212 | 3.566 | 1.84 | 2.150 | 0 | 26 | set |

### Void and exclusion list

- arm nf: not void
- arm mc: not void
- 1159-cold-nf (round 0, nf): runner: scored=False status=OK valid=True excluded=False 

M12 host-load gate: scored non-game median 3.58 cores, threshold 4.58; flagged: none

GPU plateau: round-2 counted runs 1740, 1740 MHz; rounds 3-6 median 1740 MHz; round 2 on plateau (>= 97 %): yes
GPU MHz by round (median of scored runs): r1 1740, r2 1740, r3 1740, r4 1740, r5 1740, r6 1740
sys sampler: stop_line set on 13/13 runs; sample_ms_max max -
Thread CPU ms per frame (3 busiest threads, busy% x window / frames; no thread is named render in native threads.csv):

- nf (headline runs, median): Main XThread 1.552, XThread66F4 1.192, rex::thread::TimerQueue 0.502, XThread834C 1.155
- mc (headline runs, median): Main XThread 1.547, XThread6714 1.251, rex::thread::TimerQueue 0.515, XThreadB2C8 1.138

### Headline: rounds 2-6, counted runs, M12-flagged runs kept

n per arm: nf 5, mc 5

| arm | n | fps mean (median of runs) | p99 ms | 1% low ms | cores | median ms | GPU MHz | eff MHz |
|---|---|---|---|---|---|---|---|---|
| nf | 5 | 458.8 | 3.202 | 3.566 | 1.83 | 2.148 | 1740 | 2207 |
| mc | 5 | 459.9 | 3.098 | 3.427 | 1.83 | 2.148 | 1740 | 2184 |

| pair | metric | A | B | A vs B % | 95% CI % | margin | claim | paired rounds % [t-CI] (A<B) |
|---|---|---|---|---|---|---|---|---|
| nf vs mc | fps mean | 458.826 | 459.878 | -0.2 | [-0.8, +4.2] | ±3 | not shown different | +0.7 [-2.2, +3.8] (3/5) |
| nf vs mc | p99 ms | 3.202 | 3.098 | +3.4 | [-39.8, +11.8] | ±5 | not shown different | -4.4 [-26.7, +24.8] (2/5) |
| nf vs mc | 1% low ms | 3.566 | 3.427 | +4.0 | [-44.7, +23.7] | ±5 | not shown different | +0.2 [-30.3, +44.0] (2/5) |
| nf vs mc | process cores | 1.829 | 1.835 | -0.3 | [-4.7, +3.3] | ±5 | equal | -1.3 [-3.7, +1.3] (3/5) |
| nf vs mc | median ms (info) | 2.148 | 2.148 | +0.0 | [-0.7, +0.1] | ±3 | equal | -0.2 [-0.6, +0.3] (3/5) |

### Rounds 2-6 without M12-flagged runs

no M12-flagged run: same as the headline.

### Side note: rounds 1-6 (with round 1; never decides)

n per arm: nf 6, mc 6

| arm | n | fps mean (median of runs) | p99 ms | 1% low ms | cores | median ms | GPU MHz | eff MHz |
|---|---|---|---|---|---|---|---|---|
| nf | 6 | 460.2 | 3.084 | 3.409 | 1.80 | 2.148 | 1740 | 2208 |
| mc | 6 | 459.7 | 3.100 | 3.427 | 1.82 | 2.150 | 1740 | 2190 |

| pair | metric | A | B | A vs B % | 95% CI % | margin | claim | paired rounds % [t-CI] (A<B) |
|---|---|---|---|---|---|---|---|---|
| nf vs mc | fps mean | 460.178 | 459.707 | +0.1 | [-0.6, +2.6] | ±3 | equal | +0.9 [-1.4, +3.2] (3/6) |
| nf vs mc | p99 ms | 3.084 | 3.100 | -0.5 | [-25.9, +9.8] | ±5 | not shown different | -5.7 [-23.1, +15.7] (3/6) |
| nf vs mc | 1% low ms | 3.409 | 3.427 | -0.5 | [-29.5, +19.9] | ±5 | not shown different | -1.5 [-25.4, +30.0] (3/6) |
| nf vs mc | process cores | 1.804 | 1.823 | -1.1 | [-7.5, +1.6] | ±5 | not shown different | -2.8 [-7.1, +1.7] (4/6) |
| nf vs mc | median ms (info) | 2.148 | 2.150 | -0.1 | [-0.6, +0.1] | ±3 | equal | -0.3 [-0.8, +0.2] (4/6) |

### Rounds 3-6 (info only; round 2 is on the plateau)

n per arm: nf 4, mc 4

| arm | n | fps mean (median of runs) | p99 ms | 1% low ms | cores | median ms | GPU MHz | eff MHz |
|---|---|---|---|---|---|---|---|---|
| nf | 4 | 458.5 | 3.206 | 3.772 | 1.80 | 2.149 | 1740 | 2198 |
| mc | 4 | 460.7 | 3.001 | 3.309 | 1.82 | 2.148 | 1740 | 2204 |

| pair | metric | A | B | A vs B % | 95% CI % | margin | claim | paired rounds % [t-CI] (A<B) |
|---|---|---|---|---|---|---|---|---|
| nf vs mc | fps mean | 458.497 | 460.650 | -0.5 | [-0.8, +0.3] | ±3 | equal | -0.3 [-1.3, +0.6] (3/4) |
| nf vs mc | p99 ms | 3.206 | 3.001 | +6.9 | [-4.5, +12.4] | ±5 | not shown different | +4.6 [-9.4, +20.7] (1/4) |
| nf vs mc | 1% low ms | 3.772 | 3.309 | +14.0 | [-4.1, +28.3] | ±5 | not shown different | +12.2 [-14.4, +47.0] (1/4) |
| nf vs mc | process cores | 1.804 | 1.823 | -1.1 | [-4.9, +2.3] | ±5 | equal | -1.2 [-4.8, +2.6] (2/4) |
| nf vs mc | median ms (info) | 2.149 | 2.148 | +0.1 | [-0.2, +0.2] | ±3 | equal | -0.0 [-0.3, +0.2] (2/4) |

### Order (N1): position within the round, headline set

| arm | positions (1st/2nd/3rd) | metric | median at 1st | median at later | n 1st / later |
|---|---|---|---|---|---|
| nf | 2/3/0 | fps mean | 458.298 | 461.529 | 2 / 3 |
| nf | 2/3/0 | p99 ms | 3.206 | 2.965 | 2 / 3 |
| nf | 2/3/0 | 1% low ms | 4.108 | 3.252 | 2 / 3 |
| nf | 2/3/0 | process cores | 1.776 | 1.833 | 2 / 3 |
| mc | 3/2/0 | fps mean | 459.536 | 461.748 | 3 / 2 |
| mc | 3/2/0 | p99 ms | 3.102 | 2.869 | 3 / 2 |
| mc | 3/2/0 | 1% low ms | 3.475 | 3.181 | 3 / 2 |
| mc | 3/2/0 | process cores | 1.861 | 1.802 | 3 / 2 |

### Claims (S1) and WC comparison (S2), headline set

- nf vs mc, fps mean: -0.2 % [-0.8, +4.2] -> not shown different
- nf vs mc, p99 ms: +3.4 % [-39.8, +11.8] -> not shown different
- nf vs mc, 1% low ms: +4.0 % [-44.7, +23.7] -> not shown different
- nf vs mc, process cores: -0.3 % [-4.7, +3.3] -> equal
- CF2 overall: the shipped native default reproduces mc
- S2: CF2 has no WC counterpart. Context only: W8a mc vs n0 median about -29 %, fps about +44 % (READOUT-NIGHT).


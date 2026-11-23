# T-std read-out: 20261122-1541

- title: Window 4 (Agent 8, session 3): B = devoffB (codegen B) vs d0 = devoff2 (primary), then d3 = devoff3; W4b adds d11t = window 3's d11 + REX_TIMER_WAIT_BLOCKING=1
- dir: `<workspace>\build\agent8\matrix\20261122-1541`
- command: `python -B build\agent7\w4b-noise\readout.py build\agent8\matrix\20261122-1541 -o build\agent7\w4b-noise\check-readout\check-w4b.md --json build\agent7\w4b-noise\check-readout\check-w4b.json`
- ref **d0** (matrix.json arm "ref": true); arms B, d3, d11t; rounds 1, 2, 3, 4; kept 15 of 17 runs (d0 4, B 3, d3 4, d11t 4); left out: 1541-cold-d0 (cold (unscored)); 1551-B-r2 (not valid timing).
- T split: light = frame time < 4.5 ms; hT_ref = 0.531 (the median heavy-time share of the kept runs).
- G11 power: OK: overlay best_efficiency 17/17; scheme Balanced 17/17; AC 1 17/17; saver 0 17/17; no change inside any window
- note: rounds without every arm: 2 (B-block handles this; check the order is round-robin)

## Read-out

- **Primary: B-block T-std.** Round effect on median ms: F = 7.03 on (3, 8), p = 0.012 < 0.05, so B-block T-std applies (df = runs - arms - rounds + 1); T-std is shown beside it.
- median ms vs d0 (B-block T-std): B -2.5 [-5.0, +0.0]; d3 -1.5 [-3.7, +0.8]; d11t -0.5 [-2.8, +1.8].
- fps vs d0 (B-block T-std): B +6.0 [+0.5, +11.8] *; d3 +2.3 [-2.5, +7.4]; d11t +2.5 [-2.3, +7.6].
- CIs that exclude 0 (B-block T-std): median ms and fps: B fps +6.0 [+0.5, +11.8] *; tails: none. That is 12 tests (3 arms x 4 metrics) at 5 %, so about 0.6 can be `*` by chance.
- Guards: (a) light share F = 0.40 on (3, 11), p = 0.756: OK; (b) raw agrees for every arm; (c) 7 of 15 kept runs flagged (d11t-r1, d11t-r2, d3-r3, d0-r3, B-r3, d11t-r4, d0-r4). G11: OK.

## T-std and B-block T-std

Round terms of B-block T-std vs round 1: median ms: round 2 -4.0 %, round 3 -3.1 %, round 4 -3.9 %; F = 7.03 on (3, 8), p = 0.012. fps: round 2 +7.1 %, round 3 +5.7 %, round 4 +6.7 %; F = 4.48 on (3, 8), p = 0.040.

Cells: the GM delta vs d0 in %, with the pooled 95 % CI; `*` = the CI excludes 0. Bold = the primary. d0 band = (max - min) / median of d0's runs (summary.md). 4 vs 4 band = the 95 % half-width for two arms of 4 runs.

| method | metric | d0 band % | pooled CV % | 4 vs 4 band % | df | B (n=3) | d3 (n=4) | d11t (n=4) |
|---|---|---|---|---|---|---|---|---|
| T-std | median ms | 7.8 | 2.3 | 3.6 | 11 | -2.1 [-5.8, +1.8] | -1.5 [-4.9, +2.1] | -0.5 [-4.0, +3.1] |
| **B-block T-std** | median ms | 3.6 | 1.4 | 2.3 | 8 | -2.5 [-5.0, +0.0] | -1.5 [-3.7, +0.8] | -0.5 [-2.8, +1.8] |
| T-std | fps | 12.7 | 4.1 | 6.6 | 11 | +5.2 [-1.8, +12.8] | +2.3 [-4.0, +9.1] | +2.5 [-3.9, +9.3] |
| **B-block T-std** | fps | 6.4 | 3.0 | 4.9 | 8 | +6.0 [+0.5, +11.8] * | +2.3 [-2.5, +7.4] | +2.5 [-2.3, +7.6] |

### Tails (noisier)

| method | metric | d0 band % | pooled CV % | 4 vs 4 band % | df | B (n=3) | d3 (n=4) | d11t (n=4) |
|---|---|---|---|---|---|---|---|---|
| T-std | p99 ms | 10.6 | 4.9 | 7.9 | 11 | -1.0 [-8.8, +7.4] | +2.7 [-4.8, +10.8] | +1.3 [-6.1, +9.3] |
| **B-block T-std** | p99 ms | 7.8 | 4.4 | 7.5 | 8 | -0.8 [-8.5, +7.5] | +2.7 [-4.5, +10.5] | +1.3 [-5.8, +8.9] |
| T-std | 1 % low fps | 10.0 | 5.7 | 9.2 | 11 | +3.0 [-6.3, +13.3] | -1.9 [-10.2, +7.1] | -2.4 [-10.6, +6.7] |
| **B-block T-std** | 1 % low fps | 10.7 | 4.7 | 8.0 | 8 | +1.5 [-6.7, +10.5] | -1.9 [-9.2, +5.9] | -2.4 [-9.6, +5.4] |

### Median deltas on median ms (the summary.md form)

Verdicts against each method's own d0 band: all `within`.

| method | B | d3 | d11t |
|---|---|---|---|
| raw | -10.8 | -5.4 | -1.1 |
| T-std | -0.8 | -0.6 | +0.2 |
| B-block T-std | -1.9 | -1.1 | -0.4 |

## Guards

**(a) Light share** (the share of frames < light_ms) per arm: d0 0.680, B 0.746, d3 0.683, d11t 0.652. One-way F = 0.40 on (3, 11), p = 0.756. No arm moves the mix.

**(b) Raw GM deltas** with the pooled 95 % CI. They must not contradict B-block T-std:

| method | metric | d0 band % | pooled CV % | 4 vs 4 band % | df | B (n=3) | d3 (n=4) | d11t (n=4) |
|---|---|---|---|---|---|---|---|---|
| raw | median ms | 19.6 | 12.2 | 20.9 | 11 | -8.3 [-25.3, +12.6] | -0.9 [-18.1, +19.8] | -0.1 [-17.4, +20.8] |
| raw | fps | 23.6 | 14.7 | 25.6 | 11 | +13.5 [-11.3, +45.2] | +2.5 [-18.4, +28.8] | -0.7 [-21.0, +24.7] |

Raw CI vs the B-block T-std CI (overlap = agrees): median ms: B agrees, d3 agrees, d11t agrees; fps: B agrees, d3 agrees, d11t agrees.

**(c) Host flag** (sys.json window P util >= 90 % and E-core MHz < 600): 7 of 15 kept runs (d11t-r1, d11t-r2, d3-r3, d0-r3, B-r3, d11t-r4, d0-r4).
Residual = leave-one-out on median ms: 100 (v / GM of the other runs of its arm - 1) %, + = slower. The flag is a warning, not a correction.

| run | P util % | E MHz | light share | raw | T-std | B-block T-std |
|---|---|---|---|---|---|---|
| 1549-d11t-r1 | 99.5 | 573 | 0.560 | +19.0 | +3.4 | -0.4 |
| 1556-d11t-r2 | 100.8 | 587 | 0.599 | +7.2 | -0.5 | +1.3 |
| 1600-d3-r3 | 103.3 | 551 | 0.513 | +37.5 | +0.6 | +1.0 |
| 1604-d0-r3 | 101.0 | 555 | 0.600 | +6.9 | -1.3 | -0.9 |
| 1606-B-r3 | 101.1 | 545 | 0.626 | +16.1 | -0.8 | +0.3 |
| 1608-d11t-r4 | 96.1 | 573 | 0.701 | -8.9 | -2.0 | -0.5 |
| 1611-d0-r4 | 101.7 | 553 | 0.565 | +13.7 | -3.4 | -1.9 |

Mean of the flagged runs: raw +13.1, T-std -0.6 (-4 % of raw), B-block T-std -0.1 (-1 % of raw). RMS of the other kept runs: raw 10.9, T-std 3.1, B-block T-std 1.7.

## Runs

| seq | round | arm | run | kept | raw median ms | T-std median ms | raw fps | T-std fps | light share | P util % | E MHz | flag | overlay |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | d0 | 1541-cold-d0 | no: cold (unscored) | 3.081 | 3.543 | 325.9 | 264.0 | 0.923 | 104.0 | 1729 |  | best_efficiency |
| 2 | 1 | d0 | 1542-d0-r1 | yes | 3.234 | 3.389 | 256.4 | 224.7 | 0.808 | 105.9 | 1163 |  | best_efficiency |
| 3 | 1 | B | 1545-B-r1 | yes | 2.884 | 3.172 | 317.1 | 257.7 | 0.870 | 87.1 | 1194 |  | best_efficiency |
| 4 | 1 | d3 | 1547-d3-r1 | yes | 3.347 | 3.264 | 231.0 | 240.8 | 0.671 | 99.4 | 830 |  | best_efficiency |
| 5 | 1 | d11t | 1549-d11t-r1 | yes | 3.857 | 3.288 | 206.4 | 241.8 | 0.560 | 99.5 | 573 | yes | best_efficiency |
| 6 | 2 | B | 1551-B-r2 | no: not valid timing | 3.530 | 3.414 | 234.5 | 242.5 | 0.654 | 102.7 | 767 |  | best_efficiency |
| 7 | 2 | d3 | 1553-d3-r2 | yes | 2.894 | 3.109 | 298.6 | 258.1 | 0.824 | 91.0 | 1031 |  | best_efficiency |
| 8 | 2 | d11t | 1556-d11t-r2 | yes | 3.568 | 3.194 | 220.6 | 251.1 | 0.599 | 100.8 | 587 | yes | best_efficiency |
| 9 | 2 | d0 | 1558-d0-r2 | yes | 3.069 | 3.177 | 270.4 | 256.7 | 0.746 | 94.8 | 804 |  | best_efficiency |
| 10 | 3 | d3 | 1600-d3-r3 | yes | 4.264 | 3.189 | 198.4 | 248.4 | 0.513 | 103.3 | 551 | yes | best_efficiency |
| 11 | 3 | d11t | 1602-d11t-r3 | yes | 3.025 | 3.186 | 277.2 | 261.4 | 0.749 | 91.2 | 612 |  | best_efficiency |
| 12 | 3 | d0 | 1604-d0-r3 | yes | 3.565 | 3.191 | 223.1 | 253.1 | 0.600 | 101.0 | 555 | yes | best_efficiency |
| 13 | 3 | B | 1606-B-r3 | yes | 3.435 | 3.139 | 230.8 | 256.5 | 0.626 | 101.1 | 545 | yes | best_efficiency |
| 14 | 4 | d11t | 1608-d11t-r4 | yes | 3.158 | 3.158 | 254.9 | 254.9 | 0.701 | 96.1 | 573 | yes | best_efficiency |
| 15 | 4 | d0 | 1611-d0-r4 | yes | 3.734 | 3.141 | 213.9 | 251.1 | 0.565 | 101.7 | 553 | yes | best_efficiency |
| 16 | 4 | B | 1613-B-r4 | yes | 3.033 | 3.157 | 275.8 | 262.7 | 0.743 | 92.4 | 638 |  | best_efficiency |
| 17 | 4 | d3 | 1615-d3-r4 | yes | 3.082 | 3.142 | 266.8 | 260.2 | 0.723 | 93.1 | 610 |  | best_efficiency |


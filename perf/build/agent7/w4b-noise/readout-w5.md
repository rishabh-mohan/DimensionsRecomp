# T-std read-out: 20261122-1756

- title: Window 5, S3d line (Agent 8's task #10 draft, promoted by Agent 1 at 16:42 after W4b): S4 baseline + timer modes. base = devoff3 (S3d); s0, d11, d11t, d11p = devoff4 (S4a)
- dir: `<workspace>\build\agent8\matrix\20261122-1756`
- command: `python -B build\agent7\w4b-noise\readout.py build\agent8\matrix\20261122-1756 -o build\agent7\w4b-noise\readout-w5.md --json build\agent7\w4b-noise\readout-w5.json`
- ref **base** (matrix.json arm "ref": true); arms s0, d11, d11t, d11p; rounds 1, 2, 3; kept 15 of 16 runs (base 3, s0 3, d11 3, d11t 3, d11p 3); left out: 1756-cold-base (cold (unscored)).
- T split: light = frame time < 4.5 ms; hT_ref = 0.213 (the median heavy-time share of the kept runs).
- G11 power: OK: overlay best_efficiency 16/16; scheme Balanced 16/16; AC 1 16/16; saver 0 16/16; no change inside any window

## Read-out

- **Primary: T-std.** No round effect on median ms: F = 0.24 on (2, 8), p = 0.793 >= 0.05, so T-std applies (df = runs - arms); B-block T-std is shown beside it.
- median ms vs base (T-std): s0 +1.1 [-2.7, +5.0]; d11 +1.2 [-2.5, +5.2]; d11t +2.4 [-1.4, +6.4]; d11p +1.5 [-2.3, +5.4].
- fps vs base (T-std): s0 -1.4 [-4.6, +2.0]; d11 -0.8 [-4.0, +2.6]; d11t -2.6 [-5.7, +0.7]; d11p -1.6 [-4.8, +1.7].
- CIs that exclude 0 (T-std): median ms and fps: none; tails: d11t p99 ms +8.8 [+1.0, +17.2] *. That is 16 tests (4 arms x 4 metrics) at 5 %, so about 0.8 can be `*` by chance.
- Guards: (a) light share F = 0.33 on (4, 10), p = 0.850: OK; (b) raw agrees for every arm; (c) 3 of 15 kept runs flagged (s0-r2, base-r2, d11t-r3). G11: OK.

## T-std and B-block T-std

Round terms of B-block T-std vs round 1: median ms: round 2 +0.8 %, round 3 -0.2 %; F = 0.24 on (2, 8), p = 0.793. fps: round 2 -0.7 %, round 3 -0.5 %; F = 0.17 on (2, 8), p = 0.846.

Cells: the GM delta vs base in %, with the pooled 95 % CI; `*` = the CI excludes 0. Bold = the primary. base band = (max - min) / median of base's runs (summary.md). 4 vs 4 band = the 95 % half-width for two arms of 4 runs.

| method | metric | base band % | pooled CV % | 4 vs 4 band % | df | s0 (n=3) | d11 (n=3) | d11t (n=3) | d11p (n=3) |
|---|---|---|---|---|---|---|---|---|---|
| **T-std** | median ms | 6.5 | 2.1 | 3.3 | 10 | +1.1 [-2.7, +5.0] | +1.2 [-2.5, +5.2] | +2.4 [-1.4, +6.4] | +1.5 [-2.3, +5.4] |
| B-block T-std | median ms | 5.7 | 2.3 | 3.8 | 8 | +1.1 [-3.1, +5.5] | +1.2 [-3.0, +5.7] | +2.4 [-1.9, +6.9] | +1.5 [-2.8, +5.9] |
| **T-std** | fps | 5.8 | 1.8 | 2.9 | 10 | -1.4 [-4.6, +2.0] | -0.8 [-4.0, +2.6] | -2.6 [-5.7, +0.7] | -1.6 [-4.8, +1.7] |
| B-block T-std | fps | 5.1 | 2.0 | 3.3 | 8 | -1.4 [-5.0, +2.4] | -0.8 [-4.4, +3.0] | -2.6 [-6.2, +1.2] | -1.6 [-5.2, +2.1] |

### Tails (noisier)

| method | metric | base band % | pooled CV % | 4 vs 4 band % | df | s0 (n=3) | d11 (n=3) | d11t (n=3) | d11p (n=3) |
|---|---|---|---|---|---|---|---|---|---|
| **T-std** | p99 ms | 6.9 | 4.1 | 6.7 | 10 | +2.8 [-4.6, +10.8] | +0.5 [-6.7, +8.3] | +8.8 [+1.0, +17.2] * | +5.3 [-2.2, +13.5] |
| B-block T-std | p99 ms | 4.1 | 3.4 | 5.6 | 8 | +2.8 [-3.5, +9.5] | +0.5 [-5.7, +7.0] | +8.8 [+2.1, +15.9] * | +5.3 [-1.1, +12.2] |
| **T-std** | 1 % low fps | 6.9 | 5.0 | 8.2 | 10 | -2.5 [-11.0, +6.8] | -0.4 [-9.1, +9.1] | -8.1 [-16.1, +0.7] | -6.3 [-14.4, +2.7] |
| B-block T-std | 1 % low fps | 3.5 | 3.6 | 6.1 | 8 | -2.5 [-9.0, +4.4] | -0.4 [-7.0, +6.7] | -8.1 [-14.2, -1.6] * | -6.3 [-12.5, +0.4] |

### Median deltas on median ms (the summary.md form)

Verdicts against each method's own base band: all `within`.

| method | s0 | d11 | d11t | d11p |
|---|---|---|---|---|
| raw | +5.5 | +2.6 | +4.0 | +3.1 |
| T-std | +2.3 | +2.5 | +2.7 | +2.1 |
| B-block T-std | +1.4 | +1.7 | +2.5 | +1.9 |

## Guards

**(a) Light share** (the share of frames < light_ms) per arm: base 0.870, s0 0.866, d11 0.900, d11t 0.855, d11p 0.897. One-way F = 0.33 on (4, 10), p = 0.850. No arm moves the mix.

**(b) Raw GM deltas** with the pooled 95 % CI. They must not contradict T-std:

| method | metric | base band % | pooled CV % | 4 vs 4 band % | df | s0 (n=3) | d11 (n=3) | d11t (n=3) | d11p (n=3) |
|---|---|---|---|---|---|---|---|---|---|
| raw | median ms | 20.4 | 6.5 | 10.7 | 10 | +1.3 [-9.9, +14.0] | -0.9 [-11.9, +11.5] | +4.3 [-7.3, +17.3] | -0.2 [-11.3, +12.3] |
| raw | fps | 26.8 | 9.7 | 16.4 | 10 | -2.0 [-17.8, +16.8] | +3.1 [-13.5, +22.9] | -5.2 [-20.5, +13.0] | +1.3 [-15.0, +20.7] |

Raw CI vs the T-std CI (overlap = agrees): median ms: s0 agrees, d11 agrees, d11t agrees, d11p agrees; fps: s0 agrees, d11 agrees, d11t agrees, d11p agrees.

**(c) Host flag** (sys.json window P util >= 90 % and E-core MHz < 600): 3 of 15 kept runs (s0-r2, base-r2, d11t-r3).
Residual = leave-one-out on median ms: 100 (v / GM of the other runs of its arm - 1) %, + = slower. The flag is a warning, not a correction.

| run | P util % | E MHz | light share | raw | T-std | B-block T-std |
|---|---|---|---|---|---|---|
| 1808-s0-r2 | 91.5 | 597 | 0.822 | +6.2 | +1.0 | +0.1 |
| 1817-base-r2 | 98.5 | 554 | 0.765 | +18.3 | +5.4 | +4.5 |
| 1821-d11t-r3 | 91.4 | 551 | 0.763 | +16.6 | +3.8 | +4.4 |

Mean of the flagged runs: raw +13.7, T-std +3.4 (25 % of raw), B-block T-std +3.0 (22 % of raw). RMS of the other kept runs: raw 5.4, T-std 2.1, B-block T-std 2.1.

## Runs

| seq | round | arm | run | kept | raw median ms | T-std median ms | raw fps | T-std fps | light share | P util % | E MHz | flag | overlay |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | base | 1756-cold-base | no: cold (unscored) | 2.437 | 2.567 | 395.8 | 365.1 | 0.966 | 77.4 | 1683 |  | best_efficiency |
| 2 | 1 | base | 1757-base-r1 | yes | 2.411 | 2.496 | 384.6 | 362.7 | 0.944 | 73.3 | 1174 |  | best_efficiency |
| 3 | 1 | s0 | 1800-s0-r1 | yes | 2.687 | 2.639 | 333.4 | 344.3 | 0.869 | 86.4 | 725 |  | best_efficiency |
| 4 | 1 | d11 | 1802-d11-r1 | yes | 2.620 | 2.620 | 350.3 | 350.3 | 0.894 | 84.3 | 719 |  | best_efficiency |
| 5 | 1 | d11t | 1804-d11t-r1 | yes | 2.647 | 2.625 | 338.5 | 344.6 | 0.886 | 82.6 | 676 |  | best_efficiency |
| 6 | 1 | d11p | 1806-d11p-r1 | yes | 2.624 | 2.610 | 343.3 | 347.0 | 0.892 | 82.4 | 659 |  | best_efficiency |
| 7 | 2 | s0 | 1808-s0-r2 | yes | 2.764 | 2.616 | 309.9 | 345.4 | 0.822 | 91.5 | 597 | yes | best_efficiency |
| 8 | 2 | d11 | 1810-d11-r2 | yes | 2.612 | 2.625 | 351.3 | 348.6 | 0.903 | 80.9 | 699 |  | best_efficiency |
| 9 | 2 | d11t | 1813-d11t-r2 | yes | 2.547 | 2.575 | 358.7 | 351.3 | 0.916 | 76.4 | 729 |  | best_efficiency |
| 10 | 2 | d11p | 1815-d11p-r2 | yes | 2.580 | 2.609 | 356.9 | 348.5 | 0.917 | 76.8 | 684 |  | best_efficiency |
| 11 | 2 | base | 1817-base-r2 | yes | 2.931 | 2.663 | 289.2 | 342.3 | 0.765 | 98.5 | 554 | yes | best_efficiency |
| 12 | 3 | d11 | 1819-d11-r3 | yes | 2.560 | 2.564 | 352.5 | 351.2 | 0.902 | 80.0 | 725 |  | best_efficiency |
| 13 | 3 | d11t | 1821-d11t-r3 | yes | 3.028 | 2.699 | 277.1 | 335.6 | 0.763 | 91.4 | 551 | yes | best_efficiency |
| 14 | 3 | d11p | 1823-d11p-r3 | yes | 2.645 | 2.608 | 335.3 | 345.7 | 0.881 | 83.8 | 609 |  | best_efficiency |
| 15 | 3 | base | 1825-base-r3 | yes | 2.546 | 2.556 | 355.6 | 353.7 | 0.900 | 79.4 | 740 |  | best_efficiency |
| 16 | 3 | s0 | 1827-s0-r3 | yes | 2.520 | 2.542 | 360.0 | 354.4 | 0.909 | 77.9 | 749 |  | best_efficiency |


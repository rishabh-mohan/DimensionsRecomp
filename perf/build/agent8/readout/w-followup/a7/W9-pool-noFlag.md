# T-std read-out: W9

- title: Window 9 (Agent 8, run-2 task #7 follow-up): #24 GPU-wait back-off sweep on devoff4b (S4b + S4c). off (back-off OFF, nothing set) vs Q = 0 / 125 / 250 / 500 us (LEGO_GPU_WAIT_BACKOFF_US) with spin 30 us
- dir: `<workspace>\build\agent8\readout\w-followup\pool\W9`
- command: `python -B build\agent7\w4b-noise\readout.py build\agent8\readout\w-followup\pool\W9 --drop 0122-q125-r2,0124-q250-r2,0407-q125-r1,0409-q250-r1,0417-q250-r2,0423-q125-r3 -o build\agent8\readout\w-followup\a7\W9-pool-noFlag.md --json build\agent8\readout\w-followup\a7\W9-pool-noFlag.json`
- ref **off** (matrix.json arm "ref": true); arms q0, q125, q250, q500; rounds 1, 2, 3, 4, 5, 6, 7, 8; kept 34 of 42 runs (off 8, q0 8, q125 5, q250 5, q500 8); left out: 0108-cold-off (cold (unscored)); 0122-q125-r2 (--drop); 0124-q250-r2 (--drop); 0401-cold-off (cold (unscored)); 0407-q125-r1 (--drop); 0409-q250-r1 (--drop); 0417-q250-r2 (--drop); 0423-q125-r3 (--drop).
- T split: light = frame time < 4.5 ms; hT_ref = 0.034 (the median heavy-time share of the kept runs).
- G11 power: OK: overlay best_performance 42/42; scheme Balanced 42/42; AC 1 42/42; saver 0 42/42; no change inside any window; the overlay is not W5's best_efficiency, so compare arms within this window only, not with W5's absolute numbers
- note: rounds without every arm: 2, 5, 6, 7 (B-block handles this; check the order is round-robin)

## Read-out

- **Primary: T-std.** No round effect on median ms: F = 2.05 on (7, 22), p = 0.094 >= 0.05, so T-std applies (df = runs - arms); B-block T-std is shown beside it.
- median ms vs off (T-std): q0 +2.8 [-0.4, +6.0]; q125 -2.9 [-6.3, +0.6]; q250 -2.3 [-5.7, +1.3]; q500 -2.5 [-5.5, +0.6].
- fps vs off (T-std): q0 -1.6 [-4.3, +1.1]; q125 -3.1 [-6.0, -0.0] *; q250 -3.4 [-6.4, -0.4] *; q500 -2.8 [-5.4, -0.2] *.
- CIs that exclude 0 (T-std): median ms and fps: q125 fps -3.1 [-6.0, -0.0] *, q250 fps -3.4 [-6.4, -0.4] *, q500 fps -2.8 [-5.4, -0.2] *; tails: q125 p99 ms -2.4 [-2.8, -2.0] *, q250 p99 ms -1.8 [-2.2, -1.3] *, q500 p99 ms -0.8 [-1.2, -0.4] *, q125 1 % low fps +5.9 [+3.5, +8.4] *, q250 1 % low fps +5.2 [+2.8, +7.6] *, q500 1 % low fps +2.3 [+0.3, +4.4] *. That is 16 tests (4 arms x 4 metrics) at 5 %, so about 0.8 can be `*` by chance.
- Guards: (a) light share F = 52.84 on (4, 29), p = < 0.001: WARNING, an arm may move the mix; (b) raw agrees for every arm; (c) 0 of 34 kept runs flagged. G11: OK.

## T-std and B-block T-std

Round terms of B-block T-std vs round 1: median ms: round 2 +5.3 %, round 3 +5.0 %, round 4 +4.9 %, round 5 +3.4 %, round 6 +5.3 %, round 7 +5.2 %, round 8 +4.9 %; F = 2.05 on (7, 22), p = 0.094. fps: round 2 -4.3 %, round 3 -4.5 %, round 4 -4.1 %, round 5 -2.9 %, round 6 -4.6 %, round 7 -4.2 %, round 8 -4.2 %; F = 2.22 on (7, 22), p = 0.072.

Cells: the GM delta vs off in %, with the pooled 95 % CI; `*` = the CI excludes 0. Bold = the primary. off band = (max - min) / median of off's runs (summary.md). 4 vs 4 band = the 95 % half-width for two arms of 4 runs.

| method | metric | off band % | pooled CV % | 4 vs 4 band % | df | q0 (n=8) | q125 (n=5) | q250 (n=5) | q500 (n=8) |
|---|---|---|---|---|---|---|---|---|---|
| **T-std** | median ms | 15.8 | 3.0 | 4.5 | 29 | +2.8 [-0.4, +6.0] | -2.9 [-6.3, +0.6] | -2.3 [-5.7, +1.3] | -2.5 [-5.5, +0.6] |
| B-block T-std | median ms | 11.6 | 2.7 | 4.1 | 22 | +2.8 [-0.1, +5.7] | -2.7 [-5.9, +0.6] | -2.0 [-5.2, +1.3] | -2.5 [-5.2, +0.3] |
| **T-std** | fps | 14.3 | 2.6 | 3.9 | 29 | -1.6 [-4.3, +1.1] | -3.1 [-6.0, -0.0] * | -3.4 [-6.4, -0.4] * | -2.8 [-5.4, -0.2] * |
| B-block T-std | fps | 9.2 | 2.3 | 3.5 | 22 | -1.6 [-4.0, +0.8] | -3.2 [-5.9, -0.4] * | -3.6 [-6.3, -0.9] * | -2.8 [-5.2, -0.5] * |

### Tails (noisier)

| method | metric | off band % | pooled CV % | 4 vs 4 band % | df | q0 (n=8) | q125 (n=5) | q250 (n=5) | q500 (n=8) |
|---|---|---|---|---|---|---|---|---|---|
| **T-std** | p99 ms | 1.4 | 0.4 | 0.6 | 29 | -0.3 [-0.7, +0.1] | -2.4 [-2.8, -2.0] * | -1.8 [-2.2, -1.3] * | -0.8 [-1.2, -0.4] * |
| B-block T-std | p99 ms | 1.0 | 0.4 | 0.5 | 22 | -0.3 [-0.6, +0.1] | -2.4 [-2.8, -2.0] * | -1.8 [-2.2, -1.3] * | -0.8 [-1.2, -0.4] * |
| **T-std** | 1 % low fps | 7.9 | 2.0 | 2.9 | 29 | +1.6 [-0.4, +3.7] | +5.9 [+3.5, +8.4] * | +5.2 [+2.8, +7.6] * | +2.3 [+0.3, +4.4] * |
| B-block T-std | 1 % low fps | 6.4 | 2.0 | 3.0 | 22 | +1.6 [-0.5, +3.8] | +6.4 [+3.8, +9.1] * | +5.2 [+2.7, +7.8] * | +2.3 [+0.2, +4.5] * |

### Median deltas on median ms (the summary.md form)

Verdicts against each method's own off band: all `within`.

| method | q0 | q125 | q250 | q500 |
|---|---|---|---|---|
| raw | +0.5 | -6.6 | -5.5 | -6.0 |
| T-std | +0.8 | -5.5 | -4.5 | -5.0 |
| B-block T-std | +1.0 | -4.8 | -4.2 | -4.6 |

## Guards

**(a) Light share** (the share of frames < light_ms) per arm: off 0.968, q0 0.970, q125 0.991, q250 0.989, q500 0.984. One-way F = 52.84 on (4, 29), p = < 0.001. p < 0.05: an arm may move the mix, which T-std hides. Read T-light, T-heavy and the raw rows.

| method | metric | off band % | pooled CV % | 4 vs 4 band % | df | q0 (n=8) | q125 (n=5) | q250 (n=5) | q500 (n=8) |
|---|---|---|---|---|---|---|---|---|---|
| T-light | median ms | 16.2 | 3.1 | 4.6 | 29 | +2.9 [-0.4, +6.2] | -2.4 [-5.9, +1.2] | -1.9 [-5.4, +1.8] | -2.1 [-5.2, +1.0] |
| T-heavy | median ms | 0.8 | 0.3 | 0.5 | 29 | -0.5 [-0.9, -0.2] * | -3.2 [-3.6, -2.8] * | -2.5 [-2.9, -2.1] * | -1.3 [-1.7, -1.0] * |
| T-light | fps | 14.5 | 2.7 | 4.0 | 29 | -1.7 [-4.4, +1.1] | -3.2 [-6.2, -0.1] * | -3.6 [-6.5, -0.5] * | -2.9 [-5.6, -0.2] * |
| T-heavy | fps | 5.2 | 1.2 | 1.8 | 29 | +1.2 [-0.0, +2.5] | +4.3 [+2.8, +5.8] * | +3.8 [+2.3, +5.3] * | +1.9 [+0.6, +3.2] * |

**(b) Raw GM deltas** with the pooled 95 % CI. They must not contradict T-std:

| method | metric | off band % | pooled CV % | 4 vs 4 band % | df | q0 (n=8) | q125 (n=5) | q250 (n=5) | q500 (n=8) |
|---|---|---|---|---|---|---|---|---|---|
| raw | median ms | 16.4 | 3.2 | 4.7 | 29 | +2.6 [-0.7, +6.0] | -3.9 [-7.4, -0.3] * | -3.2 [-6.7, +0.5] | -3.3 [-6.4, -0.1] * |
| raw | fps | 16.0 | 2.9 | 4.3 | 29 | -1.4 [-4.3, +1.6] | -0.9 [-4.2, +2.5] | -1.4 [-4.7, +2.0] | -1.3 [-4.2, +1.7] |

Raw CI vs the T-std CI (overlap = agrees): median ms: q0 agrees, q125 agrees, q250 agrees, q500 agrees; fps: q0 agrees, q125 agrees, q250 agrees, q500 agrees.

**(c) Host flag** (sys.json window P util >= 90 % and E-core MHz < 600): 0 of 34 kept runs.

## Runs

| seq | round | arm | run | kept | raw median ms | T-std median ms | raw fps | T-std fps | light share | P util % | E MHz | flag | overlay |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | off | 0108-cold-off | no: cold (unscored) | 2.143 | 2.135 | 438.5 | 442.7 | 0.976 | 76.0 | 2370 |  | best_performance |
| 2 | 1 | off | 0110-off-r1 | yes | 2.083 | 2.080 | 443.7 | 444.7 | 0.982 | 64.2 | 2004 |  | best_performance |
| 3 | 1 | q0 | 0112-q0-r1 | yes | 2.342 | 2.332 | 414.6 | 417.8 | 0.975 | 67.2 | 2040 |  | best_performance |
| 4 | 1 | q125 | 0114-q125-r1 | yes | 2.297 | 2.303 | 395.5 | 392.0 | 0.992 | 63.3 | 2167 |  | best_performance |
| 5 | 1 | q250 | 0116-q250-r1 | yes | 2.293 | 2.299 | 389.9 | 386.5 | 0.992 | 62.9 | 2178 |  | best_performance |
| 6 | 1 | q500 | 0118-q500-r1 | yes | 2.297 | 2.300 | 390.7 | 389.2 | 0.986 | 62.3 | 2208 |  | best_performance |
| 7 | 2 | q0 | 0120-q0-r2 | yes | 2.475 | 2.462 | 388.5 | 392.6 | 0.970 | 65.0 | 2067 |  | best_performance |
| 8 | 2 | q125 | 0122-q125-r2 | no: --drop | 2.319 | 2.323 | 387.8 | 385.5 | 0.988 | 63.0 | 2092 |  | best_performance |
| 9 | 2 | q250 | 0124-q250-r2 | no: --drop | 2.341 | 2.342 | 386.1 | 385.4 | 0.984 | 61.7 | 2078 |  | best_performance |
| 10 | 2 | q500 | 0126-q500-r2 | yes | 2.310 | 2.312 | 390.1 | 388.8 | 0.986 | 61.8 | 2180 |  | best_performance |
| 11 | 2 | off | 0128-off-r2 | yes | 2.463 | 2.441 | 385.8 | 392.0 | 0.964 | 62.5 | 1959 |  | best_performance |
| 12 | 3 | q125 | 0131-q125-r3 | yes | 2.296 | 2.303 | 389.6 | 386.1 | 0.992 | 62.0 | 2154 |  | best_performance |
| 13 | 3 | q250 | 0133-q250-r3 | yes | 2.302 | 2.308 | 389.7 | 386.0 | 0.992 | 63.3 | 2151 |  | best_performance |
| 14 | 3 | q500 | 0135-q500-r3 | yes | 2.319 | 2.322 | 389.4 | 388.2 | 0.985 | 60.8 | 2164 |  | best_performance |
| 15 | 3 | off | 0137-off-r3 | yes | 2.487 | 2.466 | 383.1 | 388.7 | 0.968 | 62.8 | 1974 |  | best_performance |
| 16 | 3 | q0 | 0139-q0-r3 | yes | 2.490 | 2.474 | 382.0 | 387.3 | 0.967 | 65.1 | 2001 |  | best_performance |
| 17 | 4 | q250 | 0141-q250-r4 | yes | 2.324 | 2.329 | 389.0 | 386.4 | 0.989 | 61.6 | 2142 |  | best_performance |
| 18 | 4 | q500 | 0143-q500-r4 | yes | 2.310 | 2.311 | 390.1 | 389.7 | 0.983 | 61.1 | 2186 |  | best_performance |
| 19 | 4 | off | 0145-off-r4 | yes | 2.451 | 2.431 | 386.6 | 392.3 | 0.966 | 62.6 | 1967 |  | best_performance |
| 20 | 4 | q0 | 0147-q0-r4 | yes | 2.483 | 2.467 | 385.5 | 389.9 | 0.969 | 64.5 | 2039 |  | best_performance |
| 21 | 4 | q125 | 0149-q125-r4 | yes | 2.315 | 2.323 | 389.4 | 386.2 | 0.991 | 63.4 | 2125 |  | best_performance |
| 22 | 0 | off | 0401-cold-off | no: cold (unscored) | 1.984 | 1.972 | 450.0 | 454.9 | 0.976 | 64.5 | 2016 |  | best_performance |
| 23 | 5 | off | 0403-off-r1 | yes | 2.325 | 2.312 | 408.9 | 412.8 | 0.974 | 64.7 | 2028 |  | best_performance |
| 24 | 5 | q0 | 0405-q0-r1 | yes | 2.465 | 2.452 | 385.8 | 390.0 | 0.970 | 66.3 | 2024 |  | best_performance |
| 25 | 5 | q125 | 0407-q125-r1 | no: --drop | 2.477 | 2.443 | 365.0 | 374.3 | 0.956 | 61.7 | 1841 |  | best_performance |
| 26 | 5 | q250 | 0409-q250-r1 | no: --drop | 2.460 | 2.452 | 378.2 | 380.4 | 0.976 | 61.6 | 1879 |  | best_performance |
| 27 | 5 | q500 | 0411-q500-r1 | yes | 2.316 | 2.319 | 388.7 | 387.5 | 0.985 | 62.4 | 2184 |  | best_performance |
| 28 | 6 | q0 | 0413-q0-r2 | yes | 2.472 | 2.460 | 385.1 | 389.2 | 0.970 | 65.9 | 2082 |  | best_performance |
| 29 | 6 | q125 | 0415-q125-r2 | yes | 2.295 | 2.301 | 391.0 | 387.2 | 0.993 | 60.0 | 2153 |  | best_performance |
| 30 | 6 | q250 | 0417-q250-r2 | no: --drop | 2.377 | 2.376 | 379.1 | 379.5 | 0.981 | 64.5 | 2053 |  | best_performance |
| 31 | 6 | q500 | 0419-q500-r2 | yes | 2.356 | 2.355 | 385.8 | 386.1 | 0.981 | 62.2 | 1922 |  | best_performance |
| 32 | 6 | off | 0421-off-r2 | yes | 2.469 | 2.440 | 382.2 | 390.2 | 0.962 | 62.1 | 1905 |  | best_performance |
| 33 | 7 | q125 | 0423-q125-r3 | no: --drop | 2.510 | 2.487 | 368.4 | 374.2 | 0.964 | 62.9 | 1834 |  | best_performance |
| 34 | 7 | q250 | 0425-q250-r3 | yes | 2.356 | 2.359 | 386.4 | 385.3 | 0.985 | 62.4 | 1971 |  | best_performance |
| 35 | 7 | q500 | 0427-q500-r3 | yes | 2.309 | 2.311 | 389.8 | 389.3 | 0.983 | 62.4 | 2177 |  | best_performance |
| 36 | 7 | off | 0429-off-r3 | yes | 2.458 | 2.436 | 385.2 | 391.5 | 0.964 | 64.5 | 1977 |  | best_performance |
| 37 | 7 | q0 | 0431-q0-r3 | yes | 2.468 | 2.455 | 387.2 | 391.8 | 0.969 | 66.7 | 2068 |  | best_performance |
| 38 | 8 | q250 | 0433-q250-r4 | yes | 2.324 | 2.329 | 389.1 | 386.7 | 0.989 | 62.2 | 2139 |  | best_performance |
| 39 | 8 | q500 | 0435-q500-r4 | yes | 2.319 | 2.320 | 389.8 | 389.4 | 0.983 | 61.6 | 2167 |  | best_performance |
| 40 | 8 | off | 0438-off-r4 | yes | 2.466 | 2.447 | 384.6 | 390.0 | 0.966 | 63.9 | 1954 |  | best_performance |
| 41 | 8 | q0 | 0440-q0-r4 | yes | 2.473 | 2.457 | 384.0 | 389.0 | 0.968 | 65.3 | 1996 |  | best_performance |
| 42 | 8 | q125 | 0442-q125-r4 | yes | 2.309 | 2.314 | 389.4 | 386.8 | 0.989 | 62.1 | 2138 |  | best_performance |


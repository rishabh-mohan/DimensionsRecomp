# W5b: pooled numbers (pool_readout.py)

Base arm `d11`. Kept runs: scored, status OK, valid timing, not excluded, minus --drop 0209-d11p-r3, 0213-d11t-r3, 0453-d11-r1, 0455-d11t-r1, 0457-d11p-r1, 0510-d11t-r3. A round is (pass, round).
Paired = per round, arm vs base in the same round; % values are exp(mean log ratio) - 1 with a 95 % t-CI; sign count = rounds where the arm is lower (ms, cores) or higher (fps).

| pass | dir | results.csv sha256 | matrix.json sha256 |
|---|---|---|---|
| 1 | `build/agent8/matrix/20261123-0155` | `5A08241AA965ADE4` | `23575AAAE9DCBB85` |
| 2 | `build/agent8/matrix/20261123-0451` | `8C6CC5147A7470E2` | `23575AAAE9DCBB85` |

## Runs per arm

| arm | pass | planned (scored) | timed (OK, valid, not excluded) | kept | cold run |
|---|---|---|---|---|---|
| d11 | 1 | 6 | 6 | 6 | 0155-cold-d11 2.306 ms |
| d11 | 2 | 6 | 6 | 5 | 0451-cold-d11 2.094 ms |
| d11t | 1 | 6 | 6 | 5 | - |
| d11t | 2 | 6 | 6 | 4 | - |
| d11p | 1 | 6 | 6 | 5 | - |
| d11p | 2 | 6 | 6 | 5 | - |

## pooled: per arm vs base `d11`

| arm | n | median ms (median of runs) | vs base (pooled medians) | paired median | lower in | fps median | vs base | fps mean | paired fps | CPU cores | paired cores | frames mean (min-max) | band (max-min)/median | CV |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d11 | 11 | 2.512 | - | - | - | 385.1 | - | 387.4 | - | 2.544 | - | 19370 (19074-20755) | 10.1 % | 2.8 % |
| d11t | 9 | 2.519 | +0.3 % | +0.7 [-0.2, +1.7] | 1/9 (p 0.039) | 385.1 | +0.0 % | 386.2 | -0.5 [-1.3, +0.2] | 2.320 | -0.214 [-0.249, -0.178] | 19312 (18832-20353) | 9.3 % | 2.6 % |
| d11p | 10 | 2.505 | -0.3 % | +0.7 [-0.9, +2.4] | 6/10 (p 0.754) | 385.3 | +0.0 % | 385.1 | -0.7 [-1.9, +0.5] | 2.340 | -0.200 [-0.237, -0.162] | 19258 (18778-19798) | 6.0 % | 1.5 % |

Per-round median ms difference (arm - base):

- d11t: p1 r1 +0.059, p1 r2 -0.032, p1 r4 +0.006, p1 r5 +0.006, p1 r6 +0.027, p2 r2 +0.070, p2 r4 +0.001, p2 r5 +0.014, p2 r6 +0.009
- d11p: p1 r1 +0.147, p1 r2 -0.017, p1 r4 -0.021, p1 r5 +0.008, p1 r6 -0.015, p2 r2 -0.013, p2 r3 -0.006, p2 r4 -0.013, p2 r5 +0.080, p2 r6 +0.019

Tail (results.csv): mean p99 / p99.9 ms, worst frame, frames over 33 ms; paired p99.9 diff vs base:

| arm | p99 mean | p99.9 mean | p99.9 median | max ms | over 33 ms | paired p99.9 diff ms | higher in |
|---|---|---|---|---|---|---|---|
| d11 | 4.809 | 5.382 | 5.378 | 10.27 | 0 | - | - |
| d11t | 4.818 | 6.094 | 5.356 | 26.37 | 0 | +0.733 [-0.852, +2.319] | 4/9 (p 1.000) |
| d11p | 4.813 | 5.428 | 5.381 | 11.56 | 0 | +0.069 [-0.082, +0.219] | 6/10 (p 0.754) |

## pass 1: per arm vs base `d11`

| arm | n | median ms (median of runs) | vs base (pooled medians) | paired median | lower in | fps median | vs base | fps mean | paired fps | CPU cores | paired cores | frames mean (min-max) | band (max-min)/median | CV |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d11 | 6 | 2.515 | - | - | - | 384.6 | - | 389.3 | - | 2.539 | - | 19463 (19074-20755) | 10.1 % | 3.9 % |
| d11t | 5 | 2.498 | -0.7 % | +0.6 [-1.2, +2.3] | 1/5 (p 0.375) | 385.1 | +0.1 % | 388.7 | -0.5 [-1.6, +0.6] | 2.295 | -0.234 [-0.290, -0.177] | 19436 (19119-20353) | 7.4 % | 3.1 % |
| d11p | 5 | 2.500 | -0.6 % | +0.9 [-2.8, +4.7] | 3/5 (p 1.000) | 385.1 | +0.1 % | 387.4 | -0.8 [-3.5, +1.9] | 2.328 | -0.201 [-0.270, -0.132] | 19370 (19243-19798) | 3.0 % | 1.2 % |

Per-round median ms difference (arm - base):

- d11t: p1 r1 +0.059, p1 r2 -0.032, p1 r4 +0.006, p1 r5 +0.006, p1 r6 +0.027
- d11p: p1 r1 +0.147, p1 r2 -0.017, p1 r4 -0.021, p1 r5 +0.008, p1 r6 -0.015

Tail (results.csv): mean p99 / p99.9 ms, worst frame, frames over 33 ms; paired p99.9 diff vs base:

| arm | p99 mean | p99.9 mean | p99.9 median | max ms | over 33 ms | paired p99.9 diff ms | higher in |
|---|---|---|---|---|---|---|---|
| d11 | 4.806 | 5.397 | 5.422 | 7.82 | 0 | - | - |
| d11t | 4.832 | 6.651 | 5.356 | 26.37 | 0 | +1.295 [-2.130, +4.719] | 3/5 (p 1.000) |
| d11p | 4.789 | 5.350 | 5.315 | 8.88 | 0 | -0.006 [-0.174, +0.162] | 2/5 (p 1.000) |

## pass 2: per arm vs base `d11`

| arm | n | median ms (median of runs) | vs base (pooled medians) | paired median | lower in | fps median | vs base | fps mean | paired fps | CPU cores | paired cores | frames mean (min-max) | band (max-min)/median | CV |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d11 | 5 | 2.512 | - | - | - | 385.2 | - | 385.2 | - | 2.550 | - | 19258 (19250-19271) | 0.6 % | 0.2 % |
| d11t | 4 | 2.519 | +0.3 % | +0.9 [-1.0, +2.9] | 0/4 (p 0.125) | 385.0 | -0.0 % | 383.1 | -0.5 [-2.3, +1.3] | 2.352 | -0.188 [-0.246, -0.131] | 19156 (18832-19288) | 2.5 % | 1.2 % |
| d11p | 5 | 2.515 | +0.1 % | +0.5 [-1.4, +2.5] | 3/5 (p 1.000) | 385.4 | +0.1 % | 382.9 | -0.6 [-2.0, +0.8] | 2.351 | -0.199 [-0.267, -0.131] | 19145 (18778-19295) | 3.5 % | 1.4 % |

Per-round median ms difference (arm - base):

- d11t: p2 r2 +0.070, p2 r4 +0.001, p2 r5 +0.014, p2 r6 +0.009
- d11p: p2 r2 -0.013, p2 r3 -0.006, p2 r4 -0.013, p2 r5 +0.080, p2 r6 +0.019

Tail (results.csv): mean p99 / p99.9 ms, worst frame, frames over 33 ms; paired p99.9 diff vs base:

| arm | p99 mean | p99.9 mean | p99.9 median | max ms | over 33 ms | paired p99.9 diff ms | higher in |
|---|---|---|---|---|---|---|---|
| d11 | 4.814 | 5.363 | 5.351 | 10.27 | 0 | - | - |
| d11t | 4.802 | 5.397 | 5.348 | 6.77 | 0 | +0.032 [-0.196, +0.259] | 1/4 (p 0.625) |
| d11p | 4.837 | 5.507 | 5.455 | 11.56 | 0 | +0.144 [-0.179, +0.466] | 4/5 (p 0.375) |

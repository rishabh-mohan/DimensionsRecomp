# W5b: pooled numbers (pool_readout.py)

Base arm `d11`. Kept runs: scored, status OK, valid timing, not excluded. A round is (pass, round).
Paired = per round, arm vs base in the same round; % values are exp(mean log ratio) - 1 with a 95 % t-CI; sign count = rounds where the arm is lower (ms, cores) or higher (fps).

| pass | dir | results.csv sha256 | matrix.json sha256 |
|---|---|---|---|
| 1 | `build/agent8/matrix/20261123-0155` | `5A08241AA965ADE4` | `23575AAAE9DCBB85` |
| 2 | `build/agent8/matrix/20261123-0451` | `8C6CC5147A7470E2` | `23575AAAE9DCBB85` |

## Runs per arm

| arm | pass | planned (scored) | timed (OK, valid, not excluded) | kept | cold run |
|---|---|---|---|---|---|
| d11 | 1 | 6 | 6 | 6 | 0155-cold-d11 2.306 ms |
| d11 | 2 | 6 | 6 | 6 | 0451-cold-d11 2.094 ms |
| d11t | 1 | 6 | 6 | 6 | - |
| d11t | 2 | 6 | 6 | 6 | - |
| d11p | 1 | 6 | 6 | 6 | - |
| d11p | 2 | 6 | 6 | 6 | - |

## pooled: per arm vs base `d11`

| arm | n | median ms (median of runs) | vs base (pooled medians) | paired median | lower in | fps median | vs base | fps mean | paired fps | CPU cores | paired cores | frames mean (min-max) | band (max-min)/median | CV |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d11 | 12 | 2.511 | - | - | - | 385.1 | - | 387.9 | - | 2.549 | - | 19393 (19074-20755) | 10.1 % | 2.7 % |
| d11t | 12 | 2.524 | +0.5 % | +1.3 [+0.0, +2.6] | 1/12 (p 0.006) | 384.0 | -0.3 % | 382.8 | -1.3 [-2.5, -0.0] | 2.329 | -0.220 [-0.248, -0.192] | 19143 (18357-20353) | 11.9 % | 2.9 % |
| d11p | 12 | 2.505 | -0.3 % | +0.5 [-0.8, +1.9] | 7/12 (p 0.774) | 385.3 | +0.0 % | 384.9 | -0.7 [-1.7, +0.2] | 2.345 | -0.204 [-0.235, -0.173] | 19248 (18778-19798) | 6.0 % | 1.5 % |

Per-round median ms difference (arm - base):

- d11t: p1 r1 +0.059, p1 r2 -0.032, p1 r3 +0.064, p1 r4 +0.006, p1 r5 +0.006, p1 r6 +0.027, p2 r1 +0.164, p2 r2 +0.070, p2 r3 +0.007, p2 r4 +0.001, p2 r5 +0.014, p2 r6 +0.009
- d11p: p1 r1 +0.147, p1 r2 -0.017, p1 r3 +0.002, p1 r4 -0.021, p1 r5 +0.008, p1 r6 -0.015, p2 r1 -0.026, p2 r2 -0.013, p2 r3 -0.006, p2 r4 -0.013, p2 r5 +0.080, p2 r6 +0.019

Tail (results.csv): mean p99 / p99.9 ms, worst frame, frames over 33 ms; paired p99.9 diff vs base:

| arm | p99 mean | p99.9 mean | p99.9 median | max ms | over 33 ms | paired p99.9 diff ms | higher in |
|---|---|---|---|---|---|---|---|
| d11 | 4.818 | 5.429 | 5.390 | 10.27 | 0 | - | - |
| d11t | 4.875 | 6.088 | 5.479 | 26.37 | 0 | +0.659 [-0.475, +1.793] | 6/12 (p 1.000) |
| d11p | 4.821 | 5.450 | 5.429 | 11.56 | 0 | +0.021 [-0.126, +0.168] | 6/12 (p 1.000) |

## pass 1: per arm vs base `d11`

| arm | n | median ms (median of runs) | vs base (pooled medians) | paired median | lower in | fps median | vs base | fps mean | paired fps | CPU cores | paired cores | frames mean (min-max) | band (max-min)/median | CV |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d11 | 6 | 2.515 | - | - | - | 384.6 | - | 389.3 | - | 2.539 | - | 19463 (19074-20755) | 10.1 % | 3.9 % |
| d11t | 6 | 2.514 | -0.0 % | +0.9 [-0.7, +2.5] | 1/6 (p 0.219) | 384.2 | -0.1 % | 385.9 | -0.9 [-2.1, +0.4] | 2.311 | -0.229 [-0.273, -0.184] | 19295 (18588-20353) | 10.3 % | 3.4 % |
| d11p | 6 | 2.502 | -0.5 % | +0.8 [-2.1, +3.7] | 3/6 (p 1.000) | 385.0 | +0.1 % | 386.5 | -0.7 [-2.7, +1.4] | 2.336 | -0.203 [-0.256, -0.151] | 19324 (19091-19798) | 4.4 % | 1.4 % |

Per-round median ms difference (arm - base):

- d11t: p1 r1 +0.059, p1 r2 -0.032, p1 r3 +0.064, p1 r4 +0.006, p1 r5 +0.006, p1 r6 +0.027
- d11p: p1 r1 +0.147, p1 r2 -0.017, p1 r3 +0.002, p1 r4 -0.021, p1 r5 +0.008, p1 r6 -0.015

Tail (results.csv): mean p99 / p99.9 ms, worst frame, frames over 33 ms; paired p99.9 diff vs base:

| arm | p99 mean | p99.9 mean | p99.9 median | max ms | over 33 ms | paired p99.9 diff ms | higher in |
|---|---|---|---|---|---|---|---|
| d11 | 4.806 | 5.397 | 5.422 | 7.82 | 0 | - | - |
| d11t | 4.877 | 6.557 | 5.546 | 26.37 | 0 | +1.160 [-1.452, +3.773] | 4/6 (p 0.688) |
| d11p | 4.791 | 5.383 | 5.359 | 9.84 | 0 | -0.014 [-0.143, +0.115] | 2/6 (p 0.688) |

## pass 2: per arm vs base `d11`

| arm | n | median ms (median of runs) | vs base (pooled medians) | paired median | lower in | fps median | vs base | fps mean | paired fps | CPU cores | paired cores | frames mean (min-max) | band (max-min)/median | CV |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d11 | 6 | 2.511 | - | - | - | 385.2 | - | 386.5 | - | 2.558 | - | 19323 (19250-19649) | 1.5 % | 0.5 % |
| d11t | 6 | 2.524 | +0.5 % | +1.7 [-0.9, +4.4] | 0/6 (p 0.031) | 382.0 | -0.8 % | 379.8 | -1.7 [-4.4, +1.0] | 2.347 | -0.211 [-0.261, -0.162] | 18991 (18357-19288) | 5.1 % | 2.1 % |
| d11p | 6 | 2.510 | -0.1 % | +0.3 [-1.3, +1.9] | 4/6 (p 0.688) | 385.4 | +0.1 % | 383.4 | -0.8 [-1.9, +0.4] | 2.354 | -0.204 [-0.258, -0.151] | 19172 (18778-19302) | 5.1 % | 1.7 % |

Per-round median ms difference (arm - base):

- d11t: p2 r1 +0.164, p2 r2 +0.070, p2 r3 +0.007, p2 r4 +0.001, p2 r5 +0.014, p2 r6 +0.009
- d11p: p2 r1 -0.026, p2 r2 -0.013, p2 r3 -0.006, p2 r4 -0.013, p2 r5 +0.080, p2 r6 +0.019

Tail (results.csv): mean p99 / p99.9 ms, worst frame, frames over 33 ms; paired p99.9 diff vs base:

| arm | p99 mean | p99.9 mean | p99.9 median | max ms | over 33 ms | paired p99.9 diff ms | higher in |
|---|---|---|---|---|---|---|---|
| d11 | 4.831 | 5.461 | 5.364 | 10.27 | 0 | - | - |
| d11t | 4.873 | 5.619 | 5.479 | 10.22 | 0 | +0.158 [-0.321, +0.638] | 2/6 (p 0.688) |
| d11p | 4.851 | 5.517 | 5.493 | 11.56 | 0 | +0.056 [-0.275, +0.388] | 4/6 (p 0.688) |

# W5b: pooled numbers (pool_readout.py)

Base arm `d11`. Kept runs: scored, status OK, valid timing, not excluded, minus --drop 0157-d11-r1, 0159-d11t-r1, 0201-d11p-r1, 0453-d11-r1, 0455-d11t-r1, 0457-d11p-r1. A round is (pass, round).
Paired = per round, arm vs base in the same round; % values are exp(mean log ratio) - 1 with a 95 % t-CI; sign count = rounds where the arm is lower (ms, cores) or higher (fps).

| pass | dir | results.csv sha256 | matrix.json sha256 |
|---|---|---|---|
| 1 | `build/agent8/matrix/20261123-0155` | `5A08241AA965ADE4` | `23575AAAE9DCBB85` |
| 2 | `build/agent8/matrix/20261123-0451` | `8C6CC5147A7470E2` | `23575AAAE9DCBB85` |

## Runs per arm

| arm | pass | planned (scored) | timed (OK, valid, not excluded) | kept | cold run |
|---|---|---|---|---|---|
| d11 | 1 | 6 | 6 | 5 | 0155-cold-d11 2.306 ms |
| d11 | 2 | 6 | 6 | 5 | 0451-cold-d11 2.094 ms |
| d11t | 1 | 6 | 6 | 5 | - |
| d11t | 2 | 6 | 6 | 5 | - |
| d11p | 1 | 6 | 6 | 5 | - |
| d11p | 2 | 6 | 6 | 5 | - |

## pooled: per arm vs base `d11`

| arm | n | median ms (median of runs) | vs base (pooled medians) | paired median | lower in | fps median | vs base | fps mean | paired fps | CPU cores | paired cores | frames mean (min-max) | band (max-min)/median | CV |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d11 | 10 | 2.514 | - | - | - | 385.0 | - | 384.6 | - | 2.553 | - | 19232 (19074-19284) | 2.0 % | 0.6 % |
| d11t | 10 | 2.524 | +0.4 % | +0.7 [-0.2, +1.5] | 1/10 (p 0.021) | 384.0 | -0.3 % | 382.0 | -0.7 [-1.4, +0.1] | 2.329 | -0.224 [-0.256, -0.192] | 19100 (18588-19288) | 4.4 % | 1.4 % |
| d11p | 10 | 2.508 | -0.3 % | +0.1 [-0.8, +0.9] | 6/10 (p 0.754) | 385.0 | -0.0 % | 383.7 | -0.2 [-0.8, +0.4] | 2.345 | -0.208 [-0.241, -0.175] | 19187 (18778-19309) | 3.9 % | 1.1 % |

Per-round median ms difference (arm - base):

- d11t: p1 r2 -0.032, p1 r3 +0.064, p1 r4 +0.006, p1 r5 +0.006, p1 r6 +0.027, p2 r2 +0.070, p2 r3 +0.007, p2 r4 +0.001, p2 r5 +0.014, p2 r6 +0.009
- d11p: p1 r2 -0.017, p1 r3 +0.002, p1 r4 -0.021, p1 r5 +0.008, p1 r6 -0.015, p2 r2 -0.013, p2 r3 -0.006, p2 r4 -0.013, p2 r5 +0.080, p2 r6 +0.019

Tail (results.csv): mean p99 / p99.9 ms, worst frame, frames over 33 ms; paired p99.9 diff vs base:

| arm | p99 mean | p99.9 mean | p99.9 median | max ms | over 33 ms | paired p99.9 diff ms | higher in |
|---|---|---|---|---|---|---|---|
| d11 | 4.835 | 5.407 | 5.390 | 10.27 | 0 | - | - |
| d11t | 4.886 | 6.213 | 5.479 | 26.37 | 0 | +0.805 [-0.579, +2.190] | 5/10 (p 1.000) |
| d11p | 4.821 | 5.452 | 5.429 | 11.56 | 0 | +0.044 [-0.105, +0.194] | 5/10 (p 1.000) |

## pass 1: per arm vs base `d11`

| arm | n | median ms (median of runs) | vs base (pooled medians) | paired median | lower in | fps median | vs base | fps mean | paired fps | CPU cores | paired cores | frames mean (min-max) | band (max-min)/median | CV |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d11 | 5 | 2.526 | - | - | - | 384.2 | - | 384.1 | - | 2.556 | - | 19205 (19074-19284) | 2.0 % | 0.8 % |
| d11t | 5 | 2.531 | +0.2 % | +0.6 [-1.1, +2.3] | 1/5 (p 0.375) | 383.3 | -0.2 % | 381.7 | -0.6 [-2.1, +0.8] | 2.314 | -0.241 [-0.282, -0.200] | 19083 (18588-19285) | 4.3 % | 1.8 % |
| d11p | 5 | 2.505 | -0.8 % | -0.3 [-1.0, +0.3] | 3/5 (p 1.000) | 384.9 | +0.2 % | 384.6 | +0.1 [+0.0, +0.2] | 2.338 | -0.217 [-0.268, -0.167] | 19229 (19091-19309) | 2.2 % | 0.8 % |

Per-round median ms difference (arm - base):

- d11t: p1 r2 -0.032, p1 r3 +0.064, p1 r4 +0.006, p1 r5 +0.006, p1 r6 +0.027
- d11p: p1 r2 -0.017, p1 r3 +0.002, p1 r4 -0.021, p1 r5 +0.008, p1 r6 -0.015

Tail (results.csv): mean p99 / p99.9 ms, worst frame, frames over 33 ms; paired p99.9 diff vs base:

| arm | p99 mean | p99.9 mean | p99.9 median | max ms | over 33 ms | paired p99.9 diff ms | higher in |
|---|---|---|---|---|---|---|---|
| d11 | 4.856 | 5.452 | 5.441 | 7.82 | 0 | - | - |
| d11t | 4.925 | 6.829 | 5.736 | 26.37 | 0 | +1.378 [-1.997, +4.753] | 3/5 (p 1.000) |
| d11p | 4.806 | 5.397 | 5.403 | 9.84 | 0 | -0.055 [-0.153, +0.043] | 1/5 (p 0.375) |

## pass 2: per arm vs base `d11`

| arm | n | median ms (median of runs) | vs base (pooled medians) | paired median | lower in | fps median | vs base | fps mean | paired fps | CPU cores | paired cores | frames mean (min-max) | band (max-min)/median | CV |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d11 | 5 | 2.512 | - | - | - | 385.2 | - | 385.2 | - | 2.550 | - | 19258 (19250-19271) | 0.6 % | 0.2 % |
| d11t | 5 | 2.520 | +0.3 % | +0.8 [-0.6, +2.2] | 0/5 (p 0.062) | 384.7 | -0.1 % | 382.3 | -0.7 [-2.0, +0.6] | 2.343 | -0.206 [-0.270, -0.143] | 19118 (18832-19288) | 2.5 % | 1.1 % |
| d11p | 5 | 2.515 | +0.1 % | +0.5 [-1.4, +2.5] | 3/5 (p 1.000) | 385.4 | +0.1 % | 382.9 | -0.6 [-2.0, +0.8] | 2.351 | -0.199 [-0.267, -0.131] | 19145 (18778-19295) | 3.5 % | 1.4 % |

Per-round median ms difference (arm - base):

- d11t: p2 r2 +0.070, p2 r3 +0.007, p2 r4 +0.001, p2 r5 +0.014, p2 r6 +0.009
- d11p: p2 r2 -0.013, p2 r3 -0.006, p2 r4 -0.013, p2 r5 +0.080, p2 r6 +0.019

Tail (results.csv): mean p99 / p99.9 ms, worst frame, frames over 33 ms; paired p99.9 diff vs base:

| arm | p99 mean | p99.9 mean | p99.9 median | max ms | over 33 ms | paired p99.9 diff ms | higher in |
|---|---|---|---|---|---|---|---|
| d11 | 4.814 | 5.363 | 5.351 | 10.27 | 0 | - | - |
| d11t | 4.846 | 5.596 | 5.371 | 10.22 | 0 | +0.233 [-0.347, +0.814] | 2/5 (p 1.000) |
| d11p | 4.837 | 5.507 | 5.455 | 11.56 | 0 | +0.144 [-0.179, +0.466] | 4/5 (p 0.375) |

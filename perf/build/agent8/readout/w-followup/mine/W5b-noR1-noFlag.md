# W5b: pooled numbers (pool_readout.py)

Base arm `d11`. Kept runs: scored, status OK, valid timing, not excluded, minus --drop 0157-d11-r1, 0159-d11t-r1, 0201-d11p-r1, 0209-d11p-r3, 0213-d11t-r3, 0453-d11-r1, 0455-d11t-r1, 0457-d11p-r1, 0510-d11t-r3. A round is (pass, round).
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
| d11t | 1 | 6 | 6 | 4 | - |
| d11t | 2 | 6 | 6 | 4 | - |
| d11p | 1 | 6 | 6 | 4 | - |
| d11p | 2 | 6 | 6 | 5 | - |

## pooled: per arm vs base `d11`

| arm | n | median ms (median of runs) | vs base (pooled medians) | paired median | lower in | fps median | vs base | fps mean | paired fps | CPU cores | paired cores | frames mean (min-max) | band (max-min)/median | CV |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d11 | 10 | 2.514 | - | - | - | 385.0 | - | 384.6 | - | 2.553 | - | 19232 (19074-19284) | 2.0 % | 0.6 % |
| d11t | 8 | 2.519 | +0.2 % | +0.5 [-0.4, +1.5] | 1/8 (p 0.070) | 384.9 | -0.0 % | 383.6 | -0.4 [-1.0, +0.3] | 2.324 | -0.220 [-0.257, -0.182] | 19182 (18832-19288) | 3.4 % | 1.1 % |
| d11p | 9 | 2.505 | -0.4 % | +0.1 [-0.9, +1.1] | 6/9 (p 0.508) | 385.1 | +0.0 % | 383.9 | -0.3 [-0.9, +0.4] | 2.342 | -0.207 [-0.245, -0.169] | 19198 (18778-19309) | 3.9 % | 1.1 % |

Per-round median ms difference (arm - base):

- d11t: p1 r2 -0.032, p1 r4 +0.006, p1 r5 +0.006, p1 r6 +0.027, p2 r2 +0.070, p2 r4 +0.001, p2 r5 +0.014, p2 r6 +0.009
- d11p: p1 r2 -0.017, p1 r4 -0.021, p1 r5 +0.008, p1 r6 -0.015, p2 r2 -0.013, p2 r3 -0.006, p2 r4 -0.013, p2 r5 +0.080, p2 r6 +0.019

Tail (results.csv): mean p99 / p99.9 ms, worst frame, frames over 33 ms; paired p99.9 diff vs base:

| arm | p99 mean | p99.9 mean | p99.9 median | max ms | over 33 ms | paired p99.9 diff ms | higher in |
|---|---|---|---|---|---|---|---|
| d11 | 4.835 | 5.407 | 5.390 | 10.27 | 0 | - | - |
| d11t | 4.842 | 6.206 | 5.364 | 26.37 | 0 | +0.816 [-1.015, +2.647] | 3/8 (p 0.727) |
| d11p | 4.823 | 5.441 | 5.403 | 11.56 | 0 | +0.055 [-0.113, +0.223] | 5/9 (p 1.000) |

## pass 1: per arm vs base `d11`

| arm | n | median ms (median of runs) | vs base (pooled medians) | paired median | lower in | fps median | vs base | fps mean | paired fps | CPU cores | paired cores | frames mean (min-max) | band (max-min)/median | CV |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d11 | 5 | 2.526 | - | - | - | 384.2 | - | 384.1 | - | 2.556 | - | 19205 (19074-19284) | 2.0 % | 0.8 % |
| d11t | 4 | 2.514 | -0.5 % | +0.1 [-1.5, +1.6] | 1/4 (p 0.625) | 384.2 | +0.0 % | 384.1 | -0.2 [-0.9, +0.6] | 2.296 | -0.251 [-0.296, -0.206] | 19207 (19119-19285) | 1.4 % | 0.8 % |
| d11p | 4 | 2.502 | -0.9 % | -0.4 [-1.3, +0.4] | 3/4 (p 0.625) | 385.0 | +0.2 % | 385.3 | +0.1 [-0.0, +0.3] | 2.330 | -0.218 [-0.293, -0.143] | 19263 (19243-19309) | 0.9 % | 0.4 % |

Per-round median ms difference (arm - base):

- d11t: p1 r2 -0.032, p1 r4 +0.006, p1 r5 +0.006, p1 r6 +0.027
- d11p: p1 r2 -0.017, p1 r4 -0.021, p1 r5 +0.008, p1 r6 -0.015

Tail (results.csv): mean p99 / p99.9 ms, worst frame, frames over 33 ms; paired p99.9 diff vs base:

| arm | p99 mean | p99.9 mean | p99.9 median | max ms | over 33 ms | paired p99.9 diff ms | higher in |
|---|---|---|---|---|---|---|---|
| d11 | 4.856 | 5.452 | 5.441 | 7.82 | 0 | - | - |
| d11t | 4.881 | 7.014 | 5.546 | 26.37 | 0 | +1.600 [-3.310, +6.510] | 2/4 (p 1.000) |
| d11p | 4.807 | 5.358 | 5.331 | 8.88 | 0 | -0.055 [-0.200, +0.089] | 1/4 (p 0.625) |

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

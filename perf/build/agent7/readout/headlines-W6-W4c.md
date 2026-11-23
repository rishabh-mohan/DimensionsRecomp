# W6 / W4c headline numbers recomputed from results.csv (Agent 7, task #21)

Kept runs: scored, status OK, valid timing, not excluded (cold runs out). Runner = summary.md / SESSION2.md; Agent 8 = build/agent8/readout/w-followup/mine/W6.md and W4c.md. agree = the recomputed value rounds to the posted one.

**116 claims, 2 disagree.**

| source | claim | posted | recomputed | verdict |
|---|---|---|---|---|
| W6-1 runner | s0 median of run medians, ms | 2.44 | 2.4450 | agree |
| W6-1 runner | s0 fps (median of results.csv fps_mean) | 385.15 | 385.1530 | agree |
| W6-1 runner | s0 cpu cores (mean of cpu_cores_mean) | 2.50 | 2.5038 | agree |
| W6-1 runner | p2 median of run medians, ms | 2.47 | 2.4710 | agree |
| W6-1 runner | p2 fps (median of results.csv fps_mean) | 385.56 | 385.5590 | agree |
| W6-1 runner | p2f median of run medians, ms | 2.45 | 2.4540 | agree |
| W6-1 runner | p2f fps (median of results.csv fps_mean) | 387.72 | 387.7160 | agree |
| W6-1 runner | p2fc median of run medians, ms | 2.16 | 2.1570 | agree |
| W6-1 runner | p2fc fps (median of results.csv fps_mean) | 466.3 | 466.2950 | agree |
| W6-1 runner | p2fc cpu cores (mean of cpu_cores_mean) | 2.28 | 2.2770 | agree |
| W6-1 runner | s0 band (max - min) / median, % | 21.4 | 21.3906 | agree |
| W6-1 runner | p2fc vs s0: median-of-medians delta, % | -11.8 | -11.7791 | agree |
| W6-1 runner | p2fc vs s0: fps delta (medians), % | 21 | 21.0675 | agree |
| W6-1 runner | p2fc vs s0: cores (means), core | -0.22 | -0.2268 | DISAGREE |
| W6-1 runner | C1 = p2fc - p2f median ms, round 1 | -0.06 | -0.0620 | agree |
| W6-1 runner | C1 = p2fc - p2f median ms, round 2 | -0.16 | -0.1560 | agree |
| W6-1 runner | C1 = p2fc - p2f median ms, round 3 | -0.30 | -0.2970 | agree |
| W6-1 runner | C1 = p2fc - p2f median ms, round 4 | -0.30 | -0.2970 | agree |
| W6-1 runner | C1 = p2fc - p2f median ms, round 5 | -0.28 | -0.2770 | agree |
| W6-1 runner | round 1 faster for every arm (r1 = the arm's fastest run) | yes | s0, p2, p2f, p2fc | agree |
| W6-2 runner | s0 median of run medians, ms | 2.48 | 2.4760 | agree |
| W6-2 runner | s0 fps (median of results.csv fps_mean) | 385.0 | 385.0180 | agree |
| W6-2 runner | s0 cpu cores (mean of cpu_cores_mean) | 2.53 | 2.5270 | agree |
| W6-2 runner | p2 median of run medians, ms | 2.47 | 2.4690 | agree |
| W6-2 runner | p2 fps (median of results.csv fps_mean) | 385.2 | 385.2420 | agree |
| W6-2 runner | p2 cpu cores (mean of cpu_cores_mean) | 2.53 | 2.5266 | agree |
| W6-2 runner | p2f median of run medians, ms | 2.45 | 2.4460 | agree |
| W6-2 runner | p2f fps (median of results.csv fps_mean) | 385.9 | 385.9120 | agree |
| W6-2 runner | p2f cpu cores (mean of cpu_cores_mean) | 2.55 | 2.5530 | agree |
| W6-2 runner | p2fc median of run medians, ms | 2.13 | 2.1290 | agree |
| W6-2 runner | p2fc fps (median of results.csv fps_mean) | 469.8 | 469.8300 | agree |
| W6-2 runner | p2fc cpu cores (mean of cpu_cores_mean) | 2.26 | 2.2552 | agree |
| W6-2 runner | s0 band (max - min) / median, % | 8.4 | 8.3603 | agree |
| W6-2 runner | p2fc vs s0: median-of-medians delta, % | -14 | -14.0145 | agree |
| W6-2 runner | p2fc vs s0: fps delta (medians), % | 22 | 22.0281 | agree |
| W6-2 runner | p2fc vs s0: cores (means), core | -0.27 | -0.2718 | agree |
| W6-2 runner | C1 = p2fc - p2f median ms, round 1 | -0.34 | -0.3380 | agree |
| W6-2 runner | C1 = p2fc - p2f median ms, round 2 | -0.27 | -0.2670 | agree |
| W6-2 runner | C1 = p2fc - p2f median ms, round 3 | -0.32 | -0.3200 | agree |
| W6-2 runner | C1 = p2fc - p2f median ms, round 4 | -0.28 | -0.2770 | agree |
| W6-2 runner | C1 = p2fc - p2f median ms, round 5 | -0.32 | -0.3150 | agree |
| W6-2 runner | p2fc p99 ms (median of runs) | 5.04 | 5.0380 | agree |
| W6-2 runner | s0 p99 ms (median of runs) | 5.00 | 4.9980 | agree |
| W6-2 runner | p2fc p99.9 ms (median of runs) | 6.49 | 6.4940 | agree |
| W6-2 runner | s0 p99.9 ms (median of runs) | 5.74 | 5.7440 | agree |
| W6-2 runner | p2f p99.9 ms (median of runs) | 6.40 | 6.3970 | agree |
| W6-2 runner | one >33 ms frame, in p2f r5 | p2f r5: 1 | 0352-p2f-r5: 1 | agree |
| W6 both runner | C1 faster rounds of 10 | 10 | 10.0000 | agree |
| W6 Agent 8 pooled | p2fc vs s0 pooled median of medians, % | -12.8 | -12.7539 | agree |
| W6 Agent 8 pooled | p2fc vs s0 paired median ms % | -10.3 | -10.3278 | agree |
| W6 Agent 8 pooled | p2fc vs s0 paired median ms % CI lo | -13.6 | -13.6085 | agree |
| W6 Agent 8 pooled | p2fc vs s0 paired median ms % CI hi | -6.9 | -6.9224 | agree |
| W6 Agent 8 pooled | p2fc vs s0 paired fps (frames / window) % | 18.0 | 18.0273 | agree |
| W6 Agent 8 pooled | p2fc vs s0 paired fps (frames / window) % CI lo | 14.1 | 14.1489 | agree |
| W6 Agent 8 pooled | p2fc vs s0 paired fps (frames / window) % CI hi | 22.0 | 22.0375 | agree |
| W6 Agent 8 pooled | p2fc - p2f paired median ms % | -10.7 | -10.7226 | agree |
| W6 Agent 8 pooled | p2fc - p2f paired median ms % CI lo | -13.1 | -13.0846 | agree |
| W6 Agent 8 pooled | p2fc - p2f paired median ms % CI hi | -8.3 | -8.2964 | agree |
| W6 Agent 8 pooled | p2fc - p2f paired fps % | 18.4 | 18.4184 | agree |
| W6 Agent 8 pooled | p2fc - p2f paired fps % CI lo | 15.2 | 15.1761 | agree |
| W6 Agent 8 pooled | p2fc - p2f paired fps % CI hi | 21.8 | 21.7520 | agree |
| W6 Agent 8 pooled | p2 vs s0 paired median ms % | -0.0 | -0.0010 | agree |
| W6 Agent 8 pooled | p2 vs s0 paired median ms % CI lo | -3.0 | -2.9656 | agree |
| W6 Agent 8 pooled | p2 vs s0 paired median ms % CI hi | 3.1 | 3.0542 | agree |
| W6 Agent 8 pooled | p2f vs s0 paired median ms % | 0.4 | 0.4423 | agree |
| W6 Agent 8 pooled | p2f vs s0 paired median ms % CI lo | -2.1 | -2.1473 | agree |
| W6 Agent 8 pooled | p2f vs s0 paired median ms % CI hi | 3.1 | 3.1004 | agree |
| W6 Agent 8 pooled | p2fc - s0 paired cores | -0.249 | -0.2493 | agree |
| W6 Agent 8 pooled | p2fc - s0 paired cores CI lo | -0.303 | -0.3031 | agree |
| W6 Agent 8 pooled | p2fc - s0 paired cores CI hi | -0.195 | -0.1955 | agree |
| W6 Agent 8 pooled | p2fc - p2f paired cores | -0.288 | -0.2885 | agree |
| W6 Agent 8 pooled | p2fc lower than s0 in rounds of 10 | 9 | 9.0000 | agree |
| W6 Agent 8 pooled | sign test p (9/10) | 0.021 | 0.0215 | agree |
| W6 Agent 8 pooled | s0 fps mean (frames / window) | 392.3 | 392.2894 | agree |
| W6 Agent 8 pooled | p2fc fps mean (frames / window) | 462.6 | 462.5670 | agree |
| W6 Agent 8 pooled | p2fc pass 1 fps mean | 458.9 | 458.9472 | agree |
| W6 Agent 8 pooled | p2fc pass 2 fps mean | 466.2 | 466.1868 | agree |
| W6 Agent 8 pooled | p2fc p99 mean ms | 4.981 | 4.9811 | agree |
| W6 Agent 8 pooled | s0 p99 mean ms | 5.016 | 5.0158 | agree |
| W6 Agent 8 pooled | p2fc p99.9 mean ms | 6.088 | 6.0882 | agree |
| W6 Agent 8 pooled | s0 p99.9 mean ms | 6.364 | 6.3640 | agree |
| W4c runner | d0 median of run medians, ms | 2.47 | 2.4680 | agree |
| W4c runner | d0 fps (median of results.csv fps_mean) | 385.35 | 385.3485 | agree |
| W4c runner | d0 cpu cores (mean of cpu_cores_mean) | 2.53 | 2.5327 | agree |
| W4c runner | B median of run medians, ms | 2.50 | 2.5000 | agree |
| W4c runner | B fps (median of results.csv fps_mean) | 383.91 | 383.9115 | agree |
| W4c runner | B cpu cores (mean of cpu_cores_mean) | 2.60 | 2.5960 | agree |
| W4c runner | d0 band (max - min) / median, % | 10 | 10.0081 | agree |
| W4c runner | B vs d0 median-of-medians delta, % | 1.3 | 1.2966 | agree |
| W4c runner | B vs d0 fps delta (medians), % | -0.4 | -0.3729 | agree |
| W4c runner | B - d0 cores (means), core | 0.07 | 0.0633 | DISAGREE |
| W4c runner | B p99 ms (median of runs) | 4.91 | 4.9125 | agree |
| W4c runner | d0 p99 ms (median of runs) | 4.94 | 4.9355 | agree |
| W4c runner | B p99.9 ms (median of runs) | 5.62 | 5.6220 | agree |
| W4c runner | d0 p99.9 ms (median of runs) | 5.62 | 5.6215 | agree |
| W4c runner | B - d0 median ms, round 1 | 0.23 | 0.2260 | agree |
| W4c runner | B - d0 median ms, round 2 | 0.04 | 0.0410 | agree |
| W4c runner | B - d0 median ms, round 3 | 0.05 | 0.0510 | agree |
| W4c runner | B - d0 median ms, round 4 | -0.00 | -0.0020 | agree |
| W4c runner | B - d0 median ms, round 5 | 0.01 | 0.0070 | agree |
| W4c runner | B - d0 median ms, round 6 | 0.05 | 0.0450 | agree |
| W4c runner | B slower in rounds of 6 (2-decimal ms) | 5 | 5.0000 | agree |
| W4c Agent 8 | B vs d0 paired median ms % | 2.6 | 2.5832 | agree |
| W4c Agent 8 | B vs d0 paired median ms % CI lo | -1.2 | -1.1745 | agree |
| W4c Agent 8 | B vs d0 paired median ms % CI hi | 6.5 | 6.4837 | agree |
| W4c Agent 8 | B lower in rounds of 6 | 1 | 1.0000 | agree |
| W4c Agent 8 | B vs d0 paired fps % | -1.7 | -1.6954 | agree |
| W4c Agent 8 | B vs d0 paired fps % CI lo | -4.9 | -4.9468 | agree |
| W4c Agent 8 | B vs d0 paired fps % CI hi | 1.7 | 1.6671 | agree |
| W4c Agent 8 | B - d0 paired cores | 0.063 | 0.0633 | agree |
| W4c Agent 8 | B - d0 paired cores CI lo | -0.007 | -0.0067 | agree |
| W4c Agent 8 | B - d0 paired cores CI hi | 0.133 | 0.1333 | agree |
| W4c Agent 8 | d0 fps mean | 391.5 | 391.4804 | agree |
| W4c Agent 8 | B fps mean | 384.6 | 384.6267 | agree |
| W4c Agent 8 | d0 p99 mean | 4.930 | 4.9300 | agree |
| W4c Agent 8 | B p99 mean | 4.901 | 4.9012 | agree |

## Context (not claims)

- W6 pass 1: s0 n=5 med 2.445 ms, fps med 385.15 (frames/window med 385.15, mean 393.87), cores mean 2.504, p99 med 5.056 / mean 5.032, p99.9 med 5.782 / mean 5.904, max 9.69, >33 total 0; p2 n=5 med 2.471 ms, fps med 385.56 (frames/window med 385.56, mean 399.30), cores mean 2.518, p99 med 4.957 / mean 4.946, p99.9 med 5.662 / mean 5.712, max 9.51, >33 total 0; p2f n=5 med 2.454 ms, fps med 387.72 (frames/window med 387.71, mean 394.98), cores mean 2.556, p99 med 4.933 / mean 4.922, p99.9 med 5.550 / mean 5.595, max 11.73, >33 total 0; p2fc n=5 med 2.157 ms, fps med 466.30 (frames/window med 466.29, mean 458.95), cores mean 2.277, p99 med 4.973 / mean 4.970, p99.9 med 5.682 / mean 5.792, max 9.11, >33 total 0
- W6 pass 2: s0 n=5 med 2.476 ms, fps med 385.02 (frames/window med 385.02, mean 390.71), cores mean 2.527, p99 med 4.998 / mean 5.000, p99.9 med 5.744 / mean 6.824, max 17.35, >33 total 0; p2 n=5 med 2.469 ms, fps med 385.24 (frames/window med 385.24, mean 384.88), cores mean 2.527, p99 med 5.015 / mean 4.983, p99.9 med 5.656 / mean 6.098, max 12.60, >33 total 0; p2f n=5 med 2.446 ms, fps med 385.91 (frames/window med 385.91, mean 386.24), cores mean 2.553, p99 med 4.987 / mean 4.966, p99.9 med 6.397 / mean 6.637, max 45.67, >33 total 1; p2fc n=5 med 2.129 ms, fps med 469.83 (frames/window med 469.83, mean 466.19), cores mean 2.255, p99 med 5.038 / mean 4.992, p99.9 med 6.494 / mean 6.384, max 16.05, >33 total 0
- W6 pooled: s0 n=10 med 2.462 ms, fps med 385.09 (frames/window med 385.08, mean 392.29), cores mean 2.515, p99 med 5.029 / mean 5.016, p99.9 med 5.763 / mean 6.364, max 17.35, >33 total 0; p2 n=10 med 2.470 ms, fps med 385.40 (frames/window med 385.40, mean 392.09), cores mean 2.522, p99 med 4.975 / mean 4.965, p99.9 med 5.659 / mean 5.905, max 12.60, >33 total 0; p2f n=10 med 2.447 ms, fps med 386.83 (frames/window med 386.83, mean 390.61), cores mean 2.555, p99 med 4.960 / mean 4.944, p99.9 med 5.625 / mean 6.116, max 45.67, >33 total 1; p2fc n=10 med 2.148 ms, fps med 468.94 (frames/window med 468.95, mean 462.57), cores mean 2.266, p99 med 4.995 / mean 4.981, p99.9 med 5.735 / mean 6.088, max 16.05, >33 total 0
- W4c: d0 n=6 med 2.468 ms, fps med 385.35 (frames/window med 385.35, mean 391.48), cores mean 2.533, p99 med 4.936 / mean 4.930, p99.9 med 5.621 / mean 5.612, max 10.26, >33 total 0; B n=6 med 2.500 ms, fps med 383.91 (frames/window med 383.91, mean 384.63), cores mean 2.596, p99 med 4.912 / mean 4.901, p99.9 med 5.622 / mean 5.897, max 20.66, >33 total 0

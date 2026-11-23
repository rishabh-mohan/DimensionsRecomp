# Check of Agent 7's W9 / W5b numbers against results.csv

Agent 8, task #20. Script: `build/agent8/readout/w-followup/a7check/check_a7_w9w5b.py` (run from the workspace root; it reads only results.csv and, for ng_t, `audit/runs.csv`; it shares no code with either pool_readout.py).

## Inputs

- W9 pass 1: `build/agent8/matrix/20261123-0108/results.csv` sha256 823BA531C6EC402D...
- W9 pass 2: `build/agent8/matrix/20261123-0401/results.csv` sha256 45C2D73C071E23EC...
- W5b pass 1: `build/agent8/matrix/20261123-0155/results.csv` sha256 5A08241AA965ADE4...
- W5b pass 2: `build/agent8/matrix/20261123-0451/results.csv` sha256 8C6CC5147A7470E2...
- Checked files (Agent 7, read-only): `build/agent7/readout/W9.md` (07:01), `build/agent7/readout/W5b.md` (07:21), `build/agent7/readout/pool-W9.md` (06:26), `build/agent7/readout/pool-W5b.md` (07:02), `build/agent7/readout/load-check.md` (06:40).
- W5b.md L16 cites `build/agent8/matrix/20261123-0155/results.csv` sha256 prefix 5A08241AA965ADE4: matches.
- W5b.md L17 cites `build/agent8/matrix/20261123-0451/results.csv` sha256 prefix 8C6CC5147A7470E2: matches.
- Kept runs: scored, status OK, valid_timing, not excluded; cold runs out. W9 40 (8 per arm), W5b 36 (12 per arm).
- ng_t = `win_ngB_mean` (non-game busy cores, window mean) from `build/agent8/readout/w-followup/audit/runs.csv`.
- Agree = every recomputed number rounds to the posted number at the posted decimals (ties count as agree). "agree (rounded inputs)" = it matches only when the inputs are first rounded the way the pool run tables print them (fps 1 dp, cores 2 dp, p99 2 dp, MHz 0 dp, ng_t 2 dp); load-check.md and parts of W9.md work from those tables (the W9.md pass-2 cores % also uses the printed q500 mean).
- Gap = the largest |recomputed - posted| in a claim, in last-digit units of the posted number (0.5 = a rounding tie), taking the closer of the plain recompute and, where given, the rounded-input one. Sign flip = recomputed and posted on opposite sides of 0, with the posted number at least one unit from 0.
- Not checkable from results.csv, so not checked: T-std, B-block T-std, T-light / T-heavy, 1 % low, thread busy %, sys.json util and P/E MHz, round-effect F tests, guard (b), the thread-cycle table, frame counts over 8 / 10 / 16.7 ms (results.csv has only the longest frame and the > 33 ms count), the quiet-gate process loads. Raw, CPU, count and run-level numbers are all checked; ng_t, its 1 s max and the warm-up ng_t come from the audit runs.csv.
- Categories: main = deltas, CIs and per-arm values; count = run counts; run = the per-run tables (section 8); aux = method details (band %, CV %, 4 vs 4 band, df, within-arm Spearman, t critical values) plus the per-run light share and its one-way F (light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share rounded to 3 dp, so a run can differ by 0.001 and F moves; the per-arm light means are main claims).

## Result

**912 claims, 3718 numbers: 880 agree (82 only with rounded inputs, 2 with the stated alternative), 32 disagree, 0 parse problems.**

Disagreements by gap (last-digit units): 0.5-0.6: 15; 0.6-1: 6; 1-2: 5; > 2: 6. Sign flips: 0. Hand-coded prose claims whose numbers are not on the cited line (or the next 2) of the current file: W9.md 0, W5b.md 0.

Disagreements by cause: rounding boundary (gap <= 1 unit, no flip; Agent 7 works from unrounded per-run inputs, results.csv has 3 dp): 21; light-share definition (per-run share +-0.001 and the one-way F built on it): 9; misread source column: 2 (W5b.md L70, W5b.md L215); other: 0.

| file | category | claims | numbers | agree | agree (rounded inputs) | agree (alternative) | disagree | parse |
|---|---|---|---|---|---|---|---|---|
| W9.md | main | 165 | 580 | 147 | 17 | 0 | 1 | 0 |
| W9.md | count | 15 | 31 | 15 | 0 | 0 | 0 | 0 |
| W9.md | aux | 1 | 3 | 0 | 0 | 0 | 1 | 0 |
| W5b.md | main | 137 | 569 | 116 | 14 | 1 | 6 | 0 |
| W5b.md | count | 40 | 56 | 40 | 0 | 0 | 0 | 0 |
| W5b.md | aux | 2 | 7 | 0 | 1 | 0 | 1 | 0 |
| pool-W9.md | main | 166 | 550 | 156 | 0 | 0 | 10 | 0 |
| pool-W9.md | count | 18 | 76 | 18 | 0 | 0 | 0 | 0 |
| pool-W9.md | run | 42 | 294 | 42 | 0 | 0 | 0 | 0 |
| pool-W9.md | aux | 46 | 57 | 42 | 0 | 0 | 4 | 0 |
| pool-W5b.md | main | 100 | 324 | 93 | 0 | 1 | 6 | 0 |
| pool-W5b.md | count | 18 | 46 | 18 | 0 | 0 | 0 | 0 |
| pool-W5b.md | run | 38 | 266 | 38 | 0 | 0 | 0 | 0 |
| pool-W5b.md | aux | 42 | 53 | 39 | 0 | 0 | 3 | 0 |
| load-check.md | main | 77 | 799 | 28 | 49 | 0 | 0 | 0 |
| load-check.md | aux | 5 | 7 | 4 | 1 | 0 | 0 | 0 |

Claims that do not agree (main, count, run):

| source | claim | posted | recomputed | verdict | gap (units) | sign flips | note |
|---|---|---|---|---|---|---|---|
| pool-W9.md L57 | W9 cores q250: mean; change [CI]; GM % one-way [CI]; GM % B-block [CI] | 1.86; -0.65 [-0.76, -0.53]; -25.9 [-30.1, -21.5] *; -25.9 [-30.0, -21.7] * | 1.861 -0.645 -0.757 -0.533 -25.92 -30.12 -21.48 -25.92 -29.94 -21.68 | DISAGREE | 0.60 | 0 |  |
| pool-W9.md L110 | W9 drop-p2-r1r3: raw fps q250 | -1.7 [-5.2, +1.9] | -1.68 -5.15 1.92 | DISAGREE | 0.51 | 0 |  |
| pool-W9.md L127 | W9 drop-r1-both: cpu cores change q0 | -0.04 [-0.16, +0.08] | -0.044 -0.163 0.075 | DISAGREE | 0.50 | 0 |  |
| pool-W9.md L152 | W9 pass2-only: raw fps q0 | -1.2 [-4.5, +2.2] | -1.16 -4.46 2.25 | DISAGREE | 0.50 | 0 |  |
| pool-W9.md L180 | W9 no-lowclk-no-r1: raw fps q250 | +0.5 [-0.2, +1.3] | 0.52 -0.20 1.24 | DISAGREE | 0.55 | 0 |  |
| pool-W9.md L181 | W9 no-lowclk-no-r1: raw p99 ms q0 | -1.3 [-2.8, +0.3] | -1.30 -2.82 0.24 | DISAGREE | 0.60 | 0 |  |
| pool-W9.md L193 | W9 no-flagged: raw median ms q125 | -3.9 [-7.5, -0.2] * | -3.93 -7.46 -0.26 | DISAGREE | 0.59 | 0 |  |
| pool-W9.md L194 | W9 no-flagged: raw fps q0 | -1.4 [-4.4, +1.6] | -1.41 -4.33 1.60 | DISAGREE | 0.66 | 0 |  |
| pool-W9.md L194 | W9 no-flagged: raw fps q125 | -0.9 [-4.3, +2.6] | -0.90 -4.25 2.56 | DISAGREE | 0.53 | 0 |  |
| pool-W9.md L197 | W9 no-flagged: cpu cores change q125 | -0.72 [-0.78, -0.66] | -0.716 -0.775 -0.657 | DISAGREE | 0.51 | 0 |  |
| pool-W5b.md L54 | W5b cores d11t: mean; change [CI]; GM % one-way [CI]; GM % B-block [CI] | 2.33; -0.22 [-0.25, -0.19]; -8.6 [-9.8, -7.4] *; -8.6 [-9.6, -7.6] * | 2.329 -0.220 -0.251 -0.189 -8.63 -9.80 -7.45 -8.63 -9.60 -7.65 | DISAGREE | 0.50 | 0 |  |
| pool-W5b.md L120 | W5b no-audit-flag: raw median ms d11p | +0.5 [-1.7, +2.7] | 0.52 -1.65 2.73 | DISAGREE | 0.51 | 0 |  |
| pool-W5b.md L134 | W5b no-flagged: raw median ms d11t | +0.0 [-2.3, +2.3] | 0.01 -2.25 2.32 | DISAGREE | 0.52 | 0 |  |
| pool-W5b.md L136 | W5b no-flagged: raw p99 ms d11t | +0.0 [-1.7, +1.7] | 0.03 -1.65 1.74 | DISAGREE | 0.51 | 0 |  |
| pool-W5b.md L148 | W5b no-loaded: raw median ms d11t | +0.0 [-2.3, +2.4] | 0.01 -2.25 2.33 | DISAGREE | 0.75 | 0 |  |
| pool-W5b.md L148 | W5b no-loaded: raw median ms d11p | +0.0 [-2.3, +2.4] | 0.02 -2.24 2.33 | DISAGREE | 0.67 | 0 |  |
| W9.md L285 | W9 no-flagged: cores change q125 [CI] | -0.72 [-0.78, -0.66] | -0.716 -0.775 -0.657 / rounded inputs: -0.716 -0.775 -0.658 | DISAGREE | 0.51 | 0 |  |
| W5b.md L239 | W5b no-flagged: d11t raw med GM % [CI] | +0.0 [-2.3, +2.3] | 0.01 -2.25 2.32 | DISAGREE | 0.52 | 0 |  |
| W5b.md L240 | W5b no-loaded: d11t raw med GM % [CI] | +0.0 [-2.3, +2.4] | 0.01 -2.25 2.33 | DISAGREE | 0.75 | 0 |  |
| W5b.md L256 | W5b no-loaded: d11p raw med GM % [CI] | +0.0 [-2.3, +2.4] | 0.02 -2.24 2.33 | DISAGREE | 0.67 | 0 |  |
| W5b.md L257 | W5b no-audit-flag: d11p raw med GM % [CI] | +0.5 [-1.7, +2.7] | 0.52 -1.65 2.73 | DISAGREE | 0.51 | 0 |  |
| W5b.md L70 | 0221-d11t-r5 window ng_t | 2.31 | 2.558 | DISAGREE | 24.79 | 0 | MISREAD: 2.31 is the "game" (game cores) column of audit.md L257; that row's "ng_t mean" is 2.56 (runs.csv win_ngB_mean 2.5579, z_t -0.0). Still below 2.8 and unflagged, so the point stands |
| W5b.md L215 | 0221-d11t-r5: window ng_t, p99.9 ms, longest frame ms | ng_t 2.31; p99.9 11.672 ms; longest 26.37 ms | 2.558 11.6720 26.366 | DISAGREE | 24.79 | 0 | MISREAD: 2.31 is the "game" (game cores) column of audit.md L257; that row's "ng_t mean" is 2.56 (runs.csv win_ngB_mean 2.5579, z_t -0.0). Still below 2.8 and unflagged, so the point stands |

Aux (method-detail) claims that do not agree:

| source | claim | posted | recomputed | verdict | gap (units) | sign flips | note |
|---|---|---|---|---|---|---|---|
| pool-W9.md L220 | 0112-q0-r1: light share | 0.975 | 0.9760 | DISAGREE | 1.00 | 0 | light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share rounded to 3 dp |
| pool-W9.md L246 | 0415-q125-r2: light share | 0.993 | 0.9920 | DISAGREE | 1.00 | 0 | light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share rounded to 3 dp |
| pool-W9.md L255 | 0433-q250-r4: light share | 0.989 | 0.9880 | DISAGREE | 1.00 | 0 | light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share rounded to 3 dp |
| pool-W9.md L201 | W9 light share one-way F (df1, df2) | 9.38 (4, 35) | 9.679 4 35 / posted run-table light shares: 9.797 4 35 | DISAGREE | 29.86 | 0 | light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share rounded to 3 dp |
| pool-W5b.md L248 | 0219-d11p-r4: light share | 0.973 | 0.9720 | DISAGREE | 1.00 | 0 | light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share rounded to 3 dp |
| pool-W5b.md L263 | 0508-d11-r3: light share | 0.975 | 0.9760 | DISAGREE | 1.00 | 0 | light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share rounded to 3 dp |
| pool-W5b.md L226 | W5b light share one-way F (df1, df2) | 1.18 (2, 33) | 1.214 2 33 / posted run-table light shares: 1.225 2 33 | DISAGREE | 3.43 | 0 | light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share rounded to 3 dp |
| W9.md L78 | light share one-way F (df1, df2) | 9.38 (4, 35) | 9.679 4 35 / posted run-table light shares: 9.797 4 35 | DISAGREE | 29.86 | 0 | light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share rounded to 3 dp |
| W5b.md L81 | light share one-way F (df1, df2) | 1.18 (2, 33) | 1.214 2 33 / posted run-table light shares: 1.225 2 33 | DISAGREE | 3.43 | 0 | light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share rounded to 3 dp |

Claims that agree only with a stated alternative reading:

- pool-W5b.md L226: W5b light share per arm (mean of results.csv light_share): posted 0.974 0.972 0.975; recomputed 0.9745 0.9719 0.9744 / posted run-table light shares: 0.9744 0.9719 0.9745 (agree (posted run-table light shares))
- W5b.md L81: light share per arm (mean of results.csv light_share): d11, d11t, d11p: posted 0.974 0.972 0.975; recomputed 0.9745 0.9719 0.9744 / posted run-table light shares: 0.9744 0.9719 0.9745 (agree (posted run-table light shares))

## W9 per-arm headline numbers (recomputed from results.csv)

Deltas: cores = linear one-way pooled CI; median ms and fps = GM % with the pooled one-way CI on ln (df = runs - arms), the same as the pool files' raw rows.

| subset | arm | n | median ms (median of runs) | fps median | fps mean | cores mean | cores vs off [95 % CI] | raw median ms GM % vs off [CI] | raw fps GM % vs off [CI] |
|---|---|---|---|---|---|---|---|---|---|
| all | off | 8 | 2.461 | 385.5 | 395.0 | 2.506 | - | - | - |
| all | q0 | 8 | 2.473 | 385.6 | 389.1 | 2.478 | -0.028 [-0.139, +0.084] | +2.6 [-1.0, +6.2] | -1.4 [-4.4, +1.6] |
| all | q125 | 8 | 2.312 | 389.4 | 384.5 | 1.890 | -0.616 [-0.727, -0.504] | -1.9 [-5.3, +1.6] | -2.6 [-5.5, +0.4] |
| all | q250 | 8 | 2.333 | 387.7 | 385.9 | 1.861 | -0.645 [-0.757, -0.533] | -2.1 [-5.5, +1.4] | -2.2 [-5.1, +0.8] |
| all | q500 | 8 | 2.313 | 389.8 | 389.3 | 1.757 | -0.749 [-0.861, -0.637] | -3.3 [-6.6, +0.1] | -1.3 [-4.3, +1.7] |
| pass 1 | off | 4 | 2.457 | 386.2 | 399.8 | 2.514 | - | - | - |
| pass 1 | q0 | 4 | 2.479 | 387.0 | 392.6 | 2.490 | -0.024 [-0.104, +0.056] | +3.5 [-2.7, +10.0] | -1.7 [-6.9, +3.8] |
| pass 1 | q125 | 4 | 2.306 | 389.5 | 390.6 | 1.824 | -0.690 [-0.770, -0.609] | -2.5 [-8.2, +3.7] | -2.1 [-7.3, +3.3] |
| pass 1 | q250 | 4 | 2.313 | 389.3 | 388.7 | 1.769 | -0.744 [-0.825, -0.664] | -2.1 [-7.9, +4.0] | -2.6 [-7.8, +2.8] |
| pass 1 | q500 | 4 | 2.310 | 390.1 | 390.1 | 1.716 | -0.798 [-0.878, -0.718] | -2.4 [-8.1, +3.8] | -2.2 [-7.4, +3.2] |
| pass 2 | off | 4 | 2.462 | 384.9 | 390.2 | 2.498 | - | - | - |
| pass 2 | q0 | 4 | 2.470 | 385.5 | 385.5 | 2.466 | -0.032 [-0.231, +0.168] | +1.7 [-2.4, +5.9] | -1.2 [-4.5, +2.3] |
| pass 2 | q125 | 4 | 2.393 | 378.9 | 378.4 | 1.957 | -0.542 [-0.741, -0.342] | -1.4 [-5.3, +2.8] | -3.0 [-6.3, +0.3] |
| pass 2 | q250 | 4 | 2.366 | 382.8 | 383.2 | 1.952 | -0.546 [-0.745, -0.346] | -2.1 [-6.0, +2.0] | -1.8 [-5.0, +1.6] |
| pass 2 | q500 | 4 | 2.317 | 389.2 | 388.5 | 1.798 | -0.700 [-0.900, -0.500] | -4.3 [-8.1, -0.3] | -0.4 [-3.7, +3.0] |
| no round 1 | off | 6 | 2.465 | 384.9 | 384.6 | 2.516 | - | - | - |
| no round 1 | q0 | 6 | 2.474 | 385.3 | 385.4 | 2.472 | -0.044 [-0.163, +0.075] | +0.5 [-1.5, +2.5] | +0.2 [-1.2, +1.6] |
| no round 1 | q125 | 6 | 2.312 | 389.4 | 385.9 | 1.859 | -0.656 [-0.775, -0.537] | -5.1 [-7.0, -3.2] | +0.3 [-1.1, +1.7] |
| no round 1 | q250 | 6 | 2.333 | 387.7 | 386.6 | 1.845 | -0.670 [-0.789, -0.551] | -5.2 [-7.1, -3.3] | +0.5 [-0.9, +1.9] |
| no round 1 | q500 | 6 | 2.314 | 389.8 | 389.2 | 1.771 | -0.745 [-0.864, -0.626] | -5.9 [-7.8, -4.0] | +1.2 [-0.2, +2.6] |
| no flagged | off | 8 | 2.461 | 385.5 | 395.0 | 2.506 | - | - | - |
| no flagged | q0 | 8 | 2.473 | 385.6 | 389.1 | 2.478 | -0.028 [-0.079, +0.024] | +2.6 [-0.8, +6.0] | -1.4 [-4.3, +1.6] |
| no flagged | q125 | 5 | 2.297 | 389.6 | 391.0 | 1.790 | -0.716 [-0.775, -0.657] | -3.9 [-7.5, -0.3] | -0.9 [-4.2, +2.6] |
| no flagged | q250 | 5 | 2.324 | 389.1 | 388.8 | 1.788 | -0.718 [-0.777, -0.659] | -3.2 [-6.8, +0.5] | -1.4 [-4.8, +2.0] |
| no flagged | q500 | 7 | 2.310 | 389.8 | 389.8 | 1.718 | -0.787 [-0.841, -0.734] | -3.6 [-6.8, -0.2] | -1.2 [-4.2, +1.9] |
| no r1, no flagged | off | 6 | 2.465 | 384.9 | 384.6 | 2.516 | - | - | - |
| no r1, no flagged | q0 | 6 | 2.474 | 385.3 | 385.4 | 2.472 | -0.044 [-0.108, +0.019] | +0.5 [-0.2, +1.1] | +0.2 [-0.3, +0.7] |
| no r1, no flagged | q125 | 4 | 2.303 | 389.5 | 389.8 | 1.783 | -0.733 [-0.804, -0.662] | -6.6 [-7.2, -5.9] | +1.4 [+0.8, +1.9] |
| no r1, no flagged | q250 | 4 | 2.324 | 389.1 | 388.6 | 1.807 | -0.708 [-0.779, -0.637] | -5.6 [-6.3, -5.0] | +1.0 [+0.5, +1.6] |
| no r1, no flagged | q500 | 5 | 2.310 | 389.8 | 389.8 | 1.720 | -0.796 [-0.862, -0.729] | -6.2 [-6.8, -5.6] | +1.4 [+0.9, +1.9] |

## W5b per-arm headline numbers (recomputed from results.csv)

Deltas: cores = linear one-way pooled CI; median ms and fps = GM % with the pooled one-way CI on ln (df = runs - arms), the same as the pool files' raw rows.

| subset | arm | n | median ms (median of runs) | fps median | fps mean | cores mean | cores vs d11 [95 % CI] | raw median ms GM % vs d11 [CI] | raw fps GM % vs d11 [CI] |
|---|---|---|---|---|---|---|---|---|---|
| all | d11 | 12 | 2.511 | 385.1 | 387.9 | 2.549 | - | - | - |
| all | d11t | 12 | 2.524 | 384.0 | 382.8 | 2.329 | -0.220 [-0.251, -0.189] | +1.3 [-0.8, +3.4] | -1.3 [-3.0, +0.4] |
| all | d11p | 12 | 2.505 | 385.3 | 384.9 | 2.345 | -0.204 [-0.235, -0.173] | +0.5 [-1.5, +2.6] | -0.7 [-2.4, +1.0] |
| pass 1 | d11 | 6 | 2.515 | 384.6 | 389.3 | 2.539 | - | - | - |
| pass 1 | d11t | 6 | 2.514 | 384.2 | 385.9 | 2.310 | -0.229 [-0.277, -0.180] | +0.9 [-3.0, +4.9] | -0.9 [-4.0, +2.4] |
| pass 1 | d11p | 6 | 2.502 | 385.0 | 386.5 | 2.336 | -0.203 [-0.252, -0.155] | +0.8 [-3.1, +4.8] | -0.7 [-3.8, +2.6] |
| pass 2 | d11 | 6 | 2.511 | 385.2 | 386.5 | 2.558 | - | - | - |
| pass 2 | d11t | 6 | 2.524 | 382.0 | 379.8 | 2.347 | -0.212 [-0.252, -0.171] | +1.7 [-0.2, +3.7] | -1.7 [-3.4, -0.1] |
| pass 2 | d11p | 6 | 2.510 | 385.4 | 383.4 | 2.354 | -0.205 [-0.245, -0.164] | +0.3 [-1.6, +2.2] | -0.8 [-2.4, +0.9] |
| no round 1 | d11 | 10 | 2.514 | 385.0 | 384.6 | 2.553 | - | - | - |
| no round 1 | d11t | 10 | 2.524 | 384.0 | 382.0 | 2.329 | -0.224 [-0.255, -0.193] | +0.7 [-0.3, +1.7] | -0.7 [-1.5, +0.1] |
| no round 1 | d11p | 10 | 2.508 | 385.0 | 383.7 | 2.345 | -0.208 [-0.239, -0.177] | +0.1 [-0.9, +1.1] | -0.2 [-1.0, +0.6] |
| no flagged | d11 | 11 | 2.512 | 385.1 | 387.4 | 2.544 | - | - | - |
| no flagged | d11t | 9 | 2.519 | 385.1 | 386.2 | 2.320 | -0.224 [-0.257, -0.190] | +0.4 [-1.8, +2.7] | -0.3 [-2.1, +1.5] |
| no flagged | d11p | 10 | 2.505 | 385.3 | 385.1 | 2.340 | -0.204 [-0.237, -0.171] | +0.5 [-1.6, +2.7] | -0.6 [-2.3, +1.2] |
| no r1, no flagged | d11 | 10 | 2.514 | 385.0 | 384.6 | 2.553 | - | - | - |
| no r1, no flagged | d11t | 8 | 2.519 | 384.9 | 383.6 | 2.324 | -0.229 [-0.261, -0.196] | +0.3 [-0.6, +1.3] | -0.3 [-0.9, +0.4] |
| no r1, no flagged | d11p | 9 | 2.505 | 385.1 | 383.9 | 2.342 | -0.211 [-0.242, -0.180] | -0.0 [-0.9, +0.9] | -0.2 [-0.8, +0.5] |

## All claims

| # | source | claim | posted | recomputed | verdict | gap (units) | note |
|---|---|---|---|---|---|---|---|
| 1 | pool-W9.md L18 | W9 off: planned (+cold), rows, timed, kept, failed | 8 (+2) 10 8 8 0 | 8 2 10 8 8 0 | agree | 0.00 |  |
| 2 | pool-W9.md L19 | W9 q0: planned (+cold), rows, timed, kept, failed | 8 (+0) 8 8 8 0 | 8 0 8 8 8 0 | agree | 0.00 |  |
| 3 | pool-W9.md L20 | W9 q125: planned (+cold), rows, timed, kept, failed | 8 (+0) 8 8 8 0 | 8 0 8 8 8 0 | agree | 0.00 |  |
| 4 | pool-W9.md L21 | W9 q250: planned (+cold), rows, timed, kept, failed | 8 (+0) 8 8 8 0 | 8 0 8 8 8 0 | agree | 0.00 |  |
| 5 | pool-W9.md L22 | W9 q500: planned (+cold), rows, timed, kept, failed | 8 (+0) 8 8 8 0 | 8 0 8 8 8 0 | agree | 0.00 |  |
| 6 | pool-W9.md L39 | W9 raw median ms GM % q0 vs off [95 % CI], one-way | +2.6 [-1.0, +6.2] | 2.57 -0.96 6.22 | agree | 0.39 |  |
| 7 | pool-W9.md L39 | W9 raw median ms GM % q125 vs off [95 % CI], one-way | -1.9 [-5.3, +1.6] | -1.91 -5.28 1.59 | agree | 0.18 |  |
| 8 | pool-W9.md L39 | W9 raw median ms GM % q250 vs off [95 % CI], one-way | -2.1 [-5.5, +1.4] | -2.08 -5.45 1.40 | agree | 0.48 |  |
| 9 | pool-W9.md L39 | W9 raw median ms GM % q500 vs off [95 % CI], one-way | -3.3 [-6.6, +0.1] | -3.32 -6.65 0.12 | agree | 0.48 |  |
| 10 | pool-W9.md L39 | W9 raw median ms: n per arm | 8 8 8 8 | 8 8 8 8 | agree | 0.00 |  |
| 11 | pool-W9.md L39 | W9 raw median ms: off band % ((max-min)/median), pooled CV %, 4 vs 4 band %, df | 16.4 3.4 5.1 35 | 16.42 3.45 5.08 35 | agree | 0.49 | 4 vs 4 band = 100 (exp(t s sqrt(1/2)) - 1), s = pooled SD of ln |
| 12 | pool-W9.md L40 | W9 raw fps GM % q0 vs off [95 % CI], one-way | -1.4 [-4.4, +1.6] | -1.41 -4.36 1.63 | agree | 0.43 |  |
| 13 | pool-W9.md L40 | W9 raw fps GM % q125 vs off [95 % CI], one-way | -2.6 [-5.5, +0.4] | -2.58 -5.49 0.42 | agree | 0.24 |  |
| 14 | pool-W9.md L40 | W9 raw fps GM % q250 vs off [95 % CI], one-way | -2.2 [-5.1, +0.8] | -2.18 -5.10 0.83 | agree | 0.33 |  |
| 15 | pool-W9.md L40 | W9 raw fps GM % q500 vs off [95 % CI], one-way | -1.3 [-4.3, +1.7] | -1.33 -4.27 1.71 | agree | 0.26 |  |
| 16 | pool-W9.md L40 | W9 raw fps: n per arm | 8 8 8 8 | 8 8 8 8 | agree | 0.00 |  |
| 17 | pool-W9.md L40 | W9 raw fps: off band % ((max-min)/median), pooled CV %, 4 vs 4 band %, df | 16.0 3.0 4.4 35 | 15.97 2.99 4.38 35 | agree | 0.28 | 4 vs 4 band = 100 (exp(t s sqrt(1/2)) - 1), s = pooled SD of ln |
| 18 | pool-W9.md L48 | W9 raw p99 ms GM % q0 vs off [95 % CI], one-way | -0.7 [-4.4, +3.1] | -0.73 -4.42 3.10 | agree | 0.32 |  |
| 19 | pool-W9.md L48 | W9 raw p99 ms GM % q125 vs off [95 % CI], one-way | -6.0 [-9.5, -2.3] * | -5.97 -9.46 -2.34 | agree | 0.38 |  |
| 20 | pool-W9.md L48 | W9 raw p99 ms GM % q250 vs off [95 % CI], one-way | -7.1 [-10.6, -3.5] * | -7.13 -10.58 -3.54 | agree | 0.42 |  |
| 21 | pool-W9.md L48 | W9 raw p99 ms GM % q500 vs off [95 % CI], one-way | -6.2 [-9.7, -2.6] * | -6.23 -9.71 -2.61 | agree | 0.26 |  |
| 22 | pool-W9.md L48 | W9 raw p99 ms: n per arm | 8 8 8 8 | 8 8 8 8 | agree | 0.00 |  |
| 23 | pool-W9.md L48 | W9 raw p99 ms: off band % ((max-min)/median), pooled CV %, 4 vs 4 band %, df | 7.2 3.7 5.5 35 | 7.20 3.73 5.50 35 | agree | 0.33 | 4 vs 4 band = 100 (exp(t s sqrt(1/2)) - 1), s = pooled SD of ln |
| 24 | pool-W9.md L57 | W9 off mean cores | 2.51 | 2.506 | agree | 0.41 |  |
| 25 | pool-W9.md L57 | W9 cores q0: mean; change [CI]; GM % one-way [CI]; GM % B-block [CI] | 2.48; -0.03 [-0.14, +0.08]; -1.1 [-6.7, +4.8]; -1.1 [-6.5, +4.6] | 2.478 -0.028 -0.139 0.084 -1.10 -6.70 4.83 -1.10 -6.46 4.56 | agree | 0.39 |  |
| 26 | pool-W9.md L57 | W9 cores q125: mean; change [CI]; GM % one-way [CI]; GM % B-block [CI] | 1.89; -0.62 [-0.73, -0.50]; -24.8 [-29.1, -20.3] *; -24.8 [-28.9, -20.5] * | 1.890 -0.616 -0.727 -0.504 -24.80 -29.06 -20.28 -24.80 -28.87 -20.49 | agree | 0.44 |  |
| 27 | pool-W9.md L57 | W9 cores q250: mean; change [CI]; GM % one-way [CI]; GM % B-block [CI] | 1.86; -0.65 [-0.76, -0.53]; -25.9 [-30.1, -21.5] *; -25.9 [-30.0, -21.7] * | 1.861 -0.645 -0.757 -0.533 -25.92 -30.12 -21.48 -25.92 -29.94 -21.68 | DISAGREE | 0.60 |  |
| 28 | pool-W9.md L57 | W9 cores q500: mean; change [CI]; GM % one-way [CI]; GM % B-block [CI] | 1.76; -0.75 [-0.86, -0.64]; -30.0 [-34.0, -25.8] *; -30.0 [-33.8, -26.0] * | 1.757 -0.749 -0.861 -0.637 -29.99 -33.96 -25.79 -29.99 -33.79 -25.98 | agree | 0.41 |  |
| 29 | pool-W9.md L70 | W9 paired raw median ms q0 vs off: mean +- hw (med; higher k/n) | +2.65 +- 3.70 (med +0.45; higher 8/8) | 2.648 3.699 0.447 8 8 | agree | 0.30 |  |
| 30 | pool-W9.md L70 | W9 paired raw median ms q125 vs off: mean +- hw (med; higher k/n) | -1.70 +- 5.86 (med -5.70; higher 3/8) | -1.695 5.860 -5.698 3 8 | agree | 0.47 |  |
| 31 | pool-W9.md L70 | W9 paired raw median ms q250 vs off: mean +- hw (med; higher k/n) | -1.91 +- 5.26 (med -4.55; higher 2/8) | -1.915 5.259 -4.552 2 8 | agree | 0.50 |  |
| 32 | pool-W9.md L70 | W9 paired raw median ms q500 vs off: mean +- hw (med; higher k/n) | -3.18 +- 4.85 (med -5.86; higher 1/8) | -3.179 4.848 -5.857 1 8 | agree | 0.31 |  |
| 33 | pool-W9.md L71 | W9 paired raw fps q0 vs off: mean +- hw (med; higher k/n) | -1.37 +- 2.48 (med -0.22; higher 3/8) | -1.370 2.481 -0.221 3 8 | agree | 0.13 |  |
| 34 | pool-W9.md L71 | W9 paired raw fps q125 vs off: mean +- hw (med; higher k/n) | -2.44 +- 4.64 (med +0.61; higher 5/8) | -2.435 4.639 0.609 5 8 | agree | 0.46 |  |
| 35 | pool-W9.md L71 | W9 paired raw fps q250 vs off: mean +- hw (med; higher k/n) | -2.06 +- 4.18 (med +0.20; higher 5/8) | -2.064 4.180 0.200 5 8 | agree | 0.38 |  |
| 36 | pool-W9.md L71 | W9 paired raw fps q500 vs off: mean +- hw (med; higher k/n) | -1.22 +- 4.05 (med +1.03; higher 6/8) | -1.216 4.053 1.034 6 8 | agree | 0.42 |  |
| 37 | pool-W9.md L74 | W9 paired cpu cores q0 vs off: mean +- hw (med; higher k/n) | -1.09 +- 1.40 (med -1.22; higher 1/8) | -1.090 1.397 -1.217 1 8 | agree | 0.28 |  |
| 38 | pool-W9.md L74 | W9 paired cpu cores q125 vs off: mean +- hw (med; higher k/n) | -24.51 +- 5.98 (med -26.67; higher 0/8) | -24.514 5.979 -26.672 0 8 | agree | 0.39 |  |
| 39 | pool-W9.md L74 | W9 paired cpu cores q250 vs off: mean +- hw (med; higher k/n) | -25.70 +- 5.23 (med -26.21; higher 0/8) | -25.703 5.231 -26.214 0 8 | agree | 0.43 |  |
| 40 | pool-W9.md L74 | W9 paired cpu cores q500 vs off: mean +- hw (med; higher k/n) | -29.90 +- 3.32 (med -31.30; higher 0/8) | -29.902 3.316 -31.304 0 8 | agree | 0.38 |  |
| 41 | pool-W9.md L82 | W9 pass 1: kept | 20 | 20 | agree | 0.00 |  |
| 42 | pool-W9.md L82 | W9 pass 1 alone: cores change q0 [CI] |  -0.02 [-0.10, +0.06] | -0.024 -0.104 0.056 | agree | 0.44 |  |
| 43 | pool-W9.md L82 | W9 pass 1 alone: cores change q125 [CI] |  -0.69 [-0.77, -0.61] | -0.690 -0.770 -0.609 | agree | 0.07 |  |
| 44 | pool-W9.md L82 | W9 pass 1 alone: cores change q250 [CI] |  -0.74 [-0.82, -0.66] | -0.744 -0.825 -0.664 | agree | 0.49 |  |
| 45 | pool-W9.md L82 | W9 pass 1 alone: cores change q500 [CI] |  -0.80 [-0.88, -0.72] | -0.798 -0.878 -0.718 | agree | 0.24 |  |
| 46 | pool-W9.md L83 | W9 pass 2: kept | 20 | 20 | agree | 0.00 |  |
| 47 | pool-W9.md L83 | W9 pass 2 alone: cores change q0 [CI] |  -0.03 [-0.23, +0.17] | -0.032 -0.231 0.168 | agree | 0.17 |  |
| 48 | pool-W9.md L83 | W9 pass 2 alone: cores change q125 [CI] |  -0.54 [-0.74, -0.34] | -0.542 -0.741 -0.342 | agree | 0.17 |  |
| 49 | pool-W9.md L83 | W9 pass 2 alone: cores change q250 [CI] |  -0.55 [-0.75, -0.35] | -0.546 -0.745 -0.346 | agree | 0.47 |  |
| 50 | pool-W9.md L83 | W9 pass 2 alone: cores change q500 [CI] |  -0.70 [-0.90, -0.50] | -0.700 -0.900 -0.500 | agree | 0.02 |  |
| 51 | pool-W9.md L95 | W9 no-slow-q: n per arm | 8 6 6 8 | 8 6 6 8 | agree | 0.00 |  |
| 52 | pool-W9.md L95 | W9 no-slow-q: raw median ms q0 | +2.6 [-0.6, +5.8] | 2.57 -0.60 5.83 | agree | 0.34 |  |
| 53 | pool-W9.md L95 | W9 no-slow-q: raw median ms q125 | -3.8 [-7.0, -0.5] * | -3.81 -7.02 -0.50 | agree | 0.16 |  |
| 54 | pool-W9.md L95 | W9 no-slow-q: raw median ms q250 | -3.1 [-6.3, +0.3] | -3.06 -6.29 0.28 | agree | 0.41 |  |
| 55 | pool-W9.md L95 | W9 no-slow-q: raw median ms q500 | -3.3 [-6.3, -0.2] * | -3.32 -6.31 -0.24 | agree | 0.43 |  |
| 56 | pool-W9.md L96 | W9 no-slow-q: raw fps q0 | -1.4 [-4.2, +1.4] | -1.41 -4.19 1.45 | agree | 0.50 |  |
| 57 | pool-W9.md L96 | W9 no-slow-q: raw fps q125 | -1.0 [-4.0, +2.1] | -1.04 -4.05 2.06 | agree | 0.49 |  |
| 58 | pool-W9.md L96 | W9 no-slow-q: raw fps q250 | -1.6 [-4.6, +1.5] | -1.56 -4.55 1.53 | agree | 0.47 |  |
| 59 | pool-W9.md L96 | W9 no-slow-q: raw fps q500 | -1.3 [-4.1, +1.5] | -1.33 -4.11 1.54 | agree | 0.37 |  |
| 60 | pool-W9.md L97 | W9 no-slow-q: raw p99 ms q0 | -0.7 [-2.2, +0.7] | -0.73 -2.17 0.72 | agree | 0.35 |  |
| 61 | pool-W9.md L97 | W9 no-slow-q: raw p99 ms q125 | -9.6 [-11.0, -8.1] * | -9.55 -10.96 -8.12 | agree | 0.47 |  |
| 62 | pool-W9.md L97 | W9 no-slow-q: raw p99 ms q250 | -8.4 [-9.9, -7.0] * | -8.43 -9.86 -6.98 | agree | 0.44 |  |
| 63 | pool-W9.md L97 | W9 no-slow-q: raw p99 ms q500 | -6.2 [-7.6, -4.9] * | -6.23 -7.58 -4.85 | agree | 0.47 |  |
| 64 | pool-W9.md L99 | W9 no-slow-q: cpu cores change q0 | -0.03 [-0.10, +0.05] | -0.028 -0.104 0.049 | agree | 0.44 |  |
| 65 | pool-W9.md L99 | W9 no-slow-q: cpu cores change q125 | -0.70 [-0.78, -0.62] | -0.699 -0.782 -0.616 | agree | 0.39 |  |
| 66 | pool-W9.md L99 | W9 no-slow-q: cpu cores change q250 | -0.70 [-0.78, -0.62] | -0.698 -0.781 -0.615 | agree | 0.47 |  |
| 67 | pool-W9.md L99 | W9 no-slow-q: cpu cores change q500 | -0.75 [-0.83, -0.67] | -0.749 -0.826 -0.672 | agree | 0.44 |  |
| 68 | pool-W9.md L109 | W9 drop-p2-r1r3: n per arm | 6 6 6 6 | 6 6 6 6 | agree | 0.00 |  |
| 69 | pool-W9.md L109 | W9 drop-p2-r1r3: raw median ms q0 | +2.4 [-1.6, +6.5] | 2.37 -1.63 6.52 | agree | 0.34 |  |
| 70 | pool-W9.md L109 | W9 drop-p2-r1r3: raw median ms q125 | -3.9 [-7.6, +0.0] | -3.89 -7.64 0.01 | agree | 0.43 |  |
| 71 | pool-W9.md L109 | W9 drop-p2-r1r3: raw median ms q250 | -3.0 [-6.8, +0.9] | -3.00 -6.78 0.94 | agree | 0.42 |  |
| 72 | pool-W9.md L109 | W9 drop-p2-r1r3: raw median ms q500 | -3.3 [-7.1, +0.6] | -3.34 -7.11 0.58 | agree | 0.40 |  |
| 73 | pool-W9.md L110 | W9 drop-p2-r1r3: raw fps q0 | -1.0 [-4.5, +2.6] | -1.01 -4.50 2.62 | agree | 0.20 |  |
| 74 | pool-W9.md L110 | W9 drop-p2-r1r3: raw fps q125 | -0.8 [-4.3, +2.8] | -0.84 -4.35 2.79 | agree | 0.46 |  |
| 75 | pool-W9.md L110 | W9 drop-p2-r1r3: raw fps q250 | -1.7 [-5.2, +1.9] | -1.68 -5.15 1.92 | DISAGREE | 0.51 |  |
| 76 | pool-W9.md L110 | W9 drop-p2-r1r3: raw fps q500 | -1.1 [-4.6, +2.5] | -1.13 -4.62 2.50 | agree | 0.25 |  |
| 77 | pool-W9.md L111 | W9 drop-p2-r1r3: raw p99 ms q0 | -0.8 [-2.8, +1.2] | -0.82 -2.84 1.24 | agree | 0.42 |  |
| 78 | pool-W9.md L111 | W9 drop-p2-r1r3: raw p99 ms q125 | -9.6 [-11.4, -7.7] * | -9.60 -11.44 -7.72 | agree | 0.36 |  |
| 79 | pool-W9.md L111 | W9 drop-p2-r1r3: raw p99 ms q250 | -8.1 [-10.0, -6.2] * | -8.12 -9.99 -6.21 | agree | 0.21 |  |
| 80 | pool-W9.md L111 | W9 drop-p2-r1r3: raw p99 ms q500 | -6.2 [-8.1, -4.3] * | -6.23 -8.13 -4.28 | agree | 0.35 |  |
| 81 | pool-W9.md L113 | W9 drop-p2-r1r3: cpu cores change q0 | -0.04 [-0.13, +0.06] | -0.036 -0.129 0.057 | agree | 0.42 |  |
| 82 | pool-W9.md L113 | W9 drop-p2-r1r3: cpu cores change q125 | -0.71 [-0.80, -0.62] | -0.708 -0.801 -0.615 | agree | 0.48 |  |
| 83 | pool-W9.md L113 | W9 drop-p2-r1r3: cpu cores change q250 | -0.72 [-0.81, -0.62] | -0.715 -0.808 -0.622 | agree | 0.50 |  |
| 84 | pool-W9.md L113 | W9 drop-p2-r1r3: cpu cores change q500 | -0.75 [-0.84, -0.66] | -0.749 -0.841 -0.656 | agree | 0.43 |  |
| 85 | pool-W9.md L123 | W9 drop-r1-both: n per arm | 6 6 6 6 | 6 6 6 6 | agree | 0.00 |  |
| 86 | pool-W9.md L123 | W9 drop-r1-both: raw median ms q0 | +0.5 [-1.5, +2.5] | 0.45 -1.55 2.49 | agree | 0.47 |  |
| 87 | pool-W9.md L123 | W9 drop-r1-both: raw median ms q125 | -5.1 [-7.0, -3.2] * | -5.12 -7.01 -3.19 | agree | 0.17 |  |
| 88 | pool-W9.md L123 | W9 drop-r1-both: raw median ms q250 | -5.2 [-7.1, -3.3] * | -5.21 -7.10 -3.28 | agree | 0.16 |  |
| 89 | pool-W9.md L123 | W9 drop-r1-both: raw median ms q500 | -5.9 [-7.8, -4.0] * | -5.89 -7.76 -3.98 | agree | 0.38 |  |
| 90 | pool-W9.md L124 | W9 drop-r1-both: raw fps q0 | +0.2 [-1.2, +1.6] | 0.21 -1.19 1.62 | agree | 0.25 |  |
| 91 | pool-W9.md L124 | W9 drop-r1-both: raw fps q125 | +0.3 [-1.1, +1.7] | 0.33 -1.07 1.75 | agree | 0.47 |  |
| 92 | pool-W9.md L124 | W9 drop-r1-both: raw fps q250 | +0.5 [-0.9, +1.9] | 0.52 -0.88 1.94 | agree | 0.39 |  |
| 93 | pool-W9.md L124 | W9 drop-r1-both: raw fps q500 | +1.2 [-0.2, +2.6] | 1.20 -0.21 2.62 | agree | 0.25 |  |
| 94 | pool-W9.md L125 | W9 drop-r1-both: raw p99 ms q0 | -1.3 [-4.4, +1.9] | -1.30 -4.43 1.93 | agree | 0.30 |  |
| 95 | pool-W9.md L125 | W9 drop-r1-both: raw p99 ms q125 | -8.3 [-11.2, -5.3] * | -8.28 -11.19 -5.28 | agree | 0.18 |  |
| 96 | pool-W9.md L125 | W9 drop-r1-both: raw p99 ms q250 | -8.3 [-11.3, -5.3] * | -8.35 -11.25 -5.35 | agree | 0.49 |  |
| 97 | pool-W9.md L125 | W9 drop-r1-both: raw p99 ms q500 | -6.8 [-9.7, -3.7] * | -6.77 -9.73 -3.72 | agree | 0.28 |  |
| 98 | pool-W9.md L127 | W9 drop-r1-both: cpu cores change q0 | -0.04 [-0.16, +0.08] | -0.044 -0.163 0.075 | DISAGREE | 0.50 |  |
| 99 | pool-W9.md L127 | W9 drop-r1-both: cpu cores change q125 | -0.66 [-0.78, -0.54] | -0.656 -0.775 -0.537 | agree | 0.45 |  |
| 100 | pool-W9.md L127 | W9 drop-r1-both: cpu cores change q250 | -0.67 [-0.79, -0.55] | -0.670 -0.789 -0.551 | agree | 0.12 |  |
| 101 | pool-W9.md L127 | W9 drop-r1-both: cpu cores change q500 | -0.74 [-0.86, -0.63] | -0.745 -0.864 -0.626 | agree | 0.47 |  |
| 102 | pool-W9.md L137 | W9 pass1-only: n per arm | 4 4 4 4 | 4 4 4 4 | agree | 0.00 |  |
| 103 | pool-W9.md L137 | W9 pass1-only: raw median ms q0 | +3.5 [-2.7, +10.0] | 3.46 -2.65 9.97 | agree | 0.46 |  |
| 104 | pool-W9.md L137 | W9 pass1-only: raw median ms q125 | -2.5 [-8.2, +3.7] | -2.46 -8.22 3.68 | agree | 0.45 |  |
| 105 | pool-W9.md L137 | W9 pass1-only: raw median ms q250 | -2.1 [-7.9, +4.0] | -2.11 -7.90 4.04 | agree | 0.44 |  |
| 106 | pool-W9.md L137 | W9 pass1-only: raw median ms q500 | -2.4 [-8.1, +3.8] | -2.36 -8.13 3.78 | agree | 0.40 |  |
| 107 | pool-W9.md L138 | W9 pass1-only: raw fps q0 | -1.7 [-6.9, +3.8] | -1.66 -6.86 3.84 | agree | 0.41 |  |
| 108 | pool-W9.md L138 | W9 pass1-only: raw fps q125 | -2.1 [-7.3, +3.3] | -2.13 -7.31 3.34 | agree | 0.42 |  |
| 109 | pool-W9.md L138 | W9 pass1-only: raw fps q250 | -2.6 [-7.8, +2.8] | -2.60 -7.75 2.85 | agree | 0.47 |  |
| 110 | pool-W9.md L138 | W9 pass1-only: raw fps q500 | -2.2 [-7.4, +3.2] | -2.25 -7.42 3.22 | agree | 0.48 |  |
| 111 | pool-W9.md L139 | W9 pass1-only: raw p99 ms q0 | -0.1 [-2.5, +2.3] | -0.12 -2.52 2.35 | agree | 0.48 |  |
| 112 | pool-W9.md L139 | W9 pass1-only: raw p99 ms q125 | -8.8 [-11.0, -6.6] * | -8.84 -11.04 -6.59 | agree | 0.43 |  |
| 113 | pool-W9.md L139 | W9 pass1-only: raw p99 ms q250 | -8.2 [-10.4, -5.9] * | -8.15 -10.36 -5.88 | agree | 0.49 |  |
| 114 | pool-W9.md L139 | W9 pass1-only: raw p99 ms q500 | -6.0 [-8.3, -3.7] * | -6.01 -8.27 -3.69 | agree | 0.27 |  |
| 115 | pool-W9.md L141 | W9 pass1-only: cpu cores change q0 | -0.02 [-0.10, +0.06] | -0.024 -0.104 0.056 | agree | 0.44 |  |
| 116 | pool-W9.md L141 | W9 pass1-only: cpu cores change q125 | -0.69 [-0.77, -0.61] | -0.690 -0.770 -0.609 | agree | 0.07 |  |
| 117 | pool-W9.md L141 | W9 pass1-only: cpu cores change q250 | -0.74 [-0.82, -0.66] | -0.744 -0.825 -0.664 | agree | 0.49 |  |
| 118 | pool-W9.md L141 | W9 pass1-only: cpu cores change q500 | -0.80 [-0.88, -0.72] | -0.798 -0.878 -0.718 | agree | 0.24 |  |
| 119 | pool-W9.md L151 | W9 pass2-only: n per arm | 4 4 4 4 | 4 4 4 4 | agree | 0.00 |  |
| 120 | pool-W9.md L151 | W9 pass2-only: raw median ms q0 | +1.7 [-2.4, +5.9] | 1.68 -2.40 5.92 | agree | 0.25 |  |
| 121 | pool-W9.md L151 | W9 pass2-only: raw median ms q125 | -1.4 [-5.3, +2.8] | -1.36 -5.31 2.76 | agree | 0.44 |  |
| 122 | pool-W9.md L151 | W9 pass2-only: raw median ms q250 | -2.1 [-6.0, +2.0] | -2.06 -5.99 2.03 | agree | 0.41 |  |
| 123 | pool-W9.md L151 | W9 pass2-only: raw median ms q500 | -4.3 [-8.1, -0.3] * | -4.27 -8.11 -0.28 | agree | 0.26 |  |
| 124 | pool-W9.md L152 | W9 pass2-only: raw fps q0 | -1.2 [-4.5, +2.2] | -1.16 -4.46 2.25 | DISAGREE | 0.50 |  |
| 125 | pool-W9.md L152 | W9 pass2-only: raw fps q125 | -3.0 [-6.3, +0.3] | -3.03 -6.26 0.32 | agree | 0.39 |  |
| 126 | pool-W9.md L152 | W9 pass2-only: raw fps q250 | -1.8 [-5.0, +1.6] | -1.76 -5.04 1.63 | agree | 0.39 |  |
| 127 | pool-W9.md L152 | W9 pass2-only: raw fps q500 | -0.4 [-3.7, +3.0] | -0.39 -3.72 3.04 | agree | 0.43 |  |
| 128 | pool-W9.md L153 | W9 pass2-only: raw p99 ms q0 | -1.3 [-7.7, +5.5] | -1.34 -7.72 5.48 | agree | 0.43 |  |
| 129 | pool-W9.md L153 | W9 pass2-only: raw p99 ms q125 | -3.0 [-9.3, +3.7] | -3.00 -9.28 3.70 | agree | 0.24 |  |
| 130 | pool-W9.md L153 | W9 pass2-only: raw p99 ms q250 | -6.1 [-12.2, +0.4] | -6.09 -12.17 0.40 | agree | 0.34 |  |
| 131 | pool-W9.md L153 | W9 pass2-only: raw p99 ms q500 | -6.4 [-12.5, +0.0] | -6.44 -12.49 0.02 | agree | 0.44 |  |
| 132 | pool-W9.md L155 | W9 pass2-only: cpu cores change q0 | -0.03 [-0.23, +0.17] | -0.032 -0.231 0.168 | agree | 0.17 |  |
| 133 | pool-W9.md L155 | W9 pass2-only: cpu cores change q125 | -0.54 [-0.74, -0.34] | -0.542 -0.741 -0.342 | agree | 0.17 |  |
| 134 | pool-W9.md L155 | W9 pass2-only: cpu cores change q250 | -0.55 [-0.75, -0.35] | -0.546 -0.745 -0.346 | agree | 0.47 |  |
| 135 | pool-W9.md L155 | W9 pass2-only: cpu cores change q500 | -0.70 [-0.90, -0.50] | -0.700 -0.900 -0.500 | agree | 0.02 |  |
| 136 | pool-W9.md L165 | W9 no-lowclk: n per arm | 8 6 7 7 | 8 6 7 7 | agree | 0.00 |  |
| 137 | pool-W9.md L165 | W9 no-lowclk: raw median ms q0 | +2.6 [-0.6, +5.8] | 2.57 -0.60 5.84 | agree | 0.41 |  |
| 138 | pool-W9.md L165 | W9 no-lowclk: raw median ms q125 | -3.8 [-7.0, -0.5] * | -3.81 -7.02 -0.49 | agree | 0.23 |  |
| 139 | pool-W9.md L165 | W9 no-lowclk: raw median ms q250 | -2.7 [-5.9, +0.5] | -2.74 -5.85 0.47 | agree | 0.46 |  |
| 140 | pool-W9.md L165 | W9 no-lowclk: raw median ms q500 | -3.6 [-6.6, -0.4] * | -3.55 -6.64 -0.36 | agree | 0.48 |  |
| 141 | pool-W9.md L166 | W9 no-lowclk: raw fps q0 | -1.4 [-4.2, +1.5] | -1.41 -4.21 1.47 | agree | 0.26 |  |
| 142 | pool-W9.md L166 | W9 no-lowclk: raw fps q125 | -1.0 [-4.1, +2.1] | -1.04 -4.07 2.09 | agree | 0.40 |  |
| 143 | pool-W9.md L166 | W9 no-lowclk: raw fps q250 | -1.9 [-4.8, +1.1] | -1.90 -4.78 1.08 | agree | 0.25 |  |
| 144 | pool-W9.md L166 | W9 no-lowclk: raw fps q500 | -1.2 [-4.1, +1.8] | -1.20 -4.10 1.79 | agree | 0.06 |  |
| 145 | pool-W9.md L167 | W9 no-lowclk: raw p99 ms q0 | -0.7 [-2.3, +0.9] | -0.73 -2.31 0.87 | agree | 0.32 |  |
| 146 | pool-W9.md L167 | W9 no-lowclk: raw p99 ms q125 | -9.6 [-11.1, -8.0] * | -9.55 -11.10 -7.98 | agree | 0.47 |  |
| 147 | pool-W9.md L167 | W9 no-lowclk: raw p99 ms q250 | -7.9 [-9.4, -6.3] * | -7.86 -9.37 -6.32 | agree | 0.42 |  |
| 148 | pool-W9.md L167 | W9 no-lowclk: raw p99 ms q500 | -6.4 [-8.0, -4.9] * | -6.44 -7.98 -4.88 | agree | 0.42 |  |
| 149 | pool-W9.md L169 | W9 no-lowclk: cpu cores change q0 | -0.03 [-0.09, +0.03] | -0.028 -0.087 0.032 | agree | 0.26 |  |
| 150 | pool-W9.md L169 | W9 no-lowclk: cpu cores change q125 | -0.70 [-0.76, -0.63] | -0.699 -0.763 -0.634 | agree | 0.45 |  |
| 151 | pool-W9.md L169 | W9 no-lowclk: cpu cores change q250 | -0.68 [-0.74, -0.62] | -0.680 -0.742 -0.618 | agree | 0.17 |  |
| 152 | pool-W9.md L169 | W9 no-lowclk: cpu cores change q500 | -0.79 [-0.85, -0.73] | -0.787 -0.849 -0.726 | agree | 0.42 |  |
| 153 | pool-W9.md L179 | W9 no-lowclk-no-r1: n per arm | 6 5 6 5 | 6 5 6 5 | agree | 0.00 |  |
| 154 | pool-W9.md L179 | W9 no-lowclk-no-r1: raw median ms q0 | +0.5 [-0.3, +1.2] | 0.45 -0.31 1.22 | agree | 0.47 |  |
| 155 | pool-W9.md L179 | W9 no-lowclk-no-r1: raw median ms q125 | -6.4 [-7.2, -5.7] * | -6.44 -7.19 -5.69 | agree | 0.43 |  |
| 156 | pool-W9.md L179 | W9 no-lowclk-no-r1: raw median ms q250 | -5.2 [-5.9, -4.5] * | -5.21 -5.93 -4.49 | agree | 0.27 |  |
| 157 | pool-W9.md L179 | W9 no-lowclk-no-r1: raw median ms q500 | -6.2 [-6.9, -5.4] * | -6.17 -6.92 -5.42 | agree | 0.25 |  |
| 158 | pool-W9.md L180 | W9 no-lowclk-no-r1: raw fps q0 | +0.2 [-0.5, +0.9] | 0.21 -0.51 0.93 | agree | 0.32 |  |
| 159 | pool-W9.md L180 | W9 no-lowclk-no-r1: raw fps q125 | +1.3 [+0.5, +2.0] * | 1.26 0.50 2.03 | agree | 0.40 |  |
| 160 | pool-W9.md L180 | W9 no-lowclk-no-r1: raw fps q250 | +0.5 [-0.2, +1.3] | 0.52 -0.20 1.24 | DISAGREE | 0.55 |  |
| 161 | pool-W9.md L180 | W9 no-lowclk-no-r1: raw fps q500 | +1.4 [+0.6, +2.1] * | 1.37 0.61 2.14 | agree | 0.38 |  |
| 162 | pool-W9.md L181 | W9 no-lowclk-no-r1: raw p99 ms q0 | -1.3 [-2.8, +0.3] | -1.30 -2.82 0.24 | DISAGREE | 0.60 |  |
| 163 | pool-W9.md L181 | W9 no-lowclk-no-r1: raw p99 ms q125 | -10.3 [-11.7, -8.8] * | -10.26 -11.71 -8.79 | agree | 0.38 |  |
| 164 | pool-W9.md L181 | W9 no-lowclk-no-r1: raw p99 ms q250 | -8.3 [-9.8, -6.9] * | -8.35 -9.76 -6.92 | agree | 0.49 |  |
| 165 | pool-W9.md L181 | W9 no-lowclk-no-r1: raw p99 ms q500 | -7.0 [-8.5, -5.5] * | -7.02 -8.52 -5.49 | agree | 0.15 |  |
| 166 | pool-W9.md L183 | W9 no-lowclk-no-r1: cpu cores change q0 | -0.04 [-0.12, +0.03] | -0.044 -0.116 0.028 | agree | 0.42 |  |
| 167 | pool-W9.md L183 | W9 no-lowclk-no-r1: cpu cores change q125 | -0.71 [-0.79, -0.64] | -0.711 -0.786 -0.636 | agree | 0.43 |  |
| 168 | pool-W9.md L183 | W9 no-lowclk-no-r1: cpu cores change q250 | -0.67 [-0.74, -0.60] | -0.670 -0.742 -0.599 | agree | 0.21 |  |
| 169 | pool-W9.md L183 | W9 no-lowclk-no-r1: cpu cores change q500 | -0.80 [-0.87, -0.72] | -0.796 -0.871 -0.720 | agree | 0.43 |  |
| 170 | pool-W9.md L193 | W9 no-flagged: n per arm | 8 5 5 7 | 8 5 5 7 | agree | 0.00 |  |
| 171 | pool-W9.md L193 | W9 no-flagged: raw median ms q0 | +2.6 [-0.8, +6.0] | 2.57 -0.75 6.00 | agree | 0.49 |  |
| 172 | pool-W9.md L193 | W9 no-flagged: raw median ms q125 | -3.9 [-7.5, -0.2] * | -3.93 -7.46 -0.26 | DISAGREE | 0.59 |  |
| 173 | pool-W9.md L193 | W9 no-flagged: raw median ms q250 | -3.2 [-6.8, +0.5] | -3.21 -6.77 0.49 | agree | 0.31 |  |
| 174 | pool-W9.md L193 | W9 no-flagged: raw median ms q500 | -3.6 [-6.8, -0.2] * | -3.55 -6.78 -0.21 | agree | 0.48 |  |
| 175 | pool-W9.md L194 | W9 no-flagged: raw fps q0 | -1.4 [-4.4, +1.6] | -1.41 -4.33 1.60 | DISAGREE | 0.66 |  |
| 176 | pool-W9.md L194 | W9 no-flagged: raw fps q125 | -0.9 [-4.3, +2.6] | -0.90 -4.25 2.56 | DISAGREE | 0.53 |  |
| 177 | pool-W9.md L194 | W9 no-flagged: raw fps q250 | -1.4 [-4.8, +2.0] | -1.44 -4.77 2.00 | agree | 0.44 |  |
| 178 | pool-W9.md L194 | W9 no-flagged: raw fps q500 | -1.2 [-4.2, +1.9] | -1.20 -4.23 1.93 | agree | 0.30 |  |
| 179 | pool-W9.md L195 | W9 no-flagged: raw p99 ms q0 | -0.7 [-2.1, +0.7] | -0.73 -2.12 0.68 | agree | 0.32 |  |
| 180 | pool-W9.md L195 | W9 no-flagged: raw p99 ms q125 | -9.8 [-11.2, -8.3] * | -9.77 -11.21 -8.31 | agree | 0.28 |  |
| 181 | pool-W9.md L195 | W9 no-flagged: raw p99 ms q250 | -8.8 [-10.3, -7.3] * | -8.81 -10.27 -7.33 | agree | 0.35 |  |
| 182 | pool-W9.md L195 | W9 no-flagged: raw p99 ms q500 | -6.4 [-7.8, -5.1] * | -6.44 -7.80 -5.07 | agree | 0.42 |  |
| 183 | pool-W9.md L197 | W9 no-flagged: cpu cores change q0 | -0.03 [-0.08, +0.02] | -0.028 -0.079 0.024 | agree | 0.39 |  |
| 184 | pool-W9.md L197 | W9 no-flagged: cpu cores change q125 | -0.72 [-0.78, -0.66] | -0.716 -0.775 -0.657 | DISAGREE | 0.51 |  |
| 185 | pool-W9.md L197 | W9 no-flagged: cpu cores change q250 | -0.72 [-0.78, -0.66] | -0.718 -0.777 -0.659 | agree | 0.29 |  |
| 186 | pool-W9.md L197 | W9 no-flagged: cpu cores change q500 | -0.79 [-0.84, -0.73] | -0.787 -0.841 -0.734 | agree | 0.40 |  |
| 187 | pool-W9.md L218 | 0108-cold-off: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 13154 2.143 438.5 4.97 2.34 2411 0 | 13154 2.1430 438.45 4.969 2.336 2411 0 | agree | 0.46 |  |
| 188 | pool-W9.md L218 | 0108-cold-off: light share | 0.976 | 0.9760 | agree | 0.00 |  |
| 189 | pool-W9.md L219 | 0110-off-r1: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 22187 2.083 443.7 4.74 2.52 1992 1 | 22187 2.0830 443.73 4.742 2.515 1992 1 | agree | 0.50 |  |
| 190 | pool-W9.md L219 | 0110-off-r1: light share | 0.982 | 0.9820 | agree | 0.00 |  |
| 191 | pool-W9.md L220 | 0112-q0-r1: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 20730 2.342 414.6 4.84 2.50 2040 1 | 20730 2.3420 414.57 4.836 2.503 2040 1 | agree | 0.40 |  |
| 192 | pool-W9.md L220 | 0112-q0-r1: light share | 0.975 | 0.9760 | DISAGREE | 1.00 | light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share rounded to 3 dp |
| 193 | pool-W9.md L221 | 0114-q125-r1: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19775 2.297 395.5 4.46 1.82 2193 1 | 19775 2.2970 395.50 4.459 1.819 2193 1 | agree | 0.10 |  |
| 194 | pool-W9.md L221 | 0114-q125-r1: light share | 0.992 | 0.9920 | agree | 0.00 |  |
| 195 | pool-W9.md L222 | 0116-q250-r1: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19496 2.293 389.9 4.47 1.71 2216 1 | 19496 2.2930 389.91 4.469 1.709 2216 1 | agree | 0.10 |  |
| 196 | pool-W9.md L222 | 0116-q250-r1: light share | 0.992 | 0.9920 | agree | 0.00 |  |
| 197 | pool-W9.md L223 | 0118-q500-r1: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19535 2.297 390.7 4.59 1.70 2228 1 | 19535 2.2970 390.69 4.590 1.704 2228 1 | agree | 0.40 |  |
| 198 | pool-W9.md L223 | 0118-q500-r1: light share | 0.986 | 0.9860 | agree | 0.00 |  |
| 199 | pool-W9.md L224 | 0120-q0-r2: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19424 2.475 388.5 4.90 2.49 2071 1 | 19424 2.4750 388.48 4.897 2.490 2071 1 | agree | 0.30 |  |
| 200 | pool-W9.md L224 | 0120-q0-r2: light share | 0.970 | 0.9700 | agree | 0.00 |  |
| 201 | pool-W9.md L225 | 0122-q125-r2: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19388 2.319 387.8 4.54 1.89 2120 1 | 19388 2.3190 387.75 4.540 1.893 2120 1 | agree | 0.46 |  |
| 202 | pool-W9.md L225 | 0122-q125-r2: light share | 0.988 | 0.9880 | agree | 0.00 |  |
| 203 | pool-W9.md L226 | 0124-q250-r2: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19306 2.341 386.1 4.64 1.91 2108 1 | 19306 2.3410 386.12 4.637 1.909 2108 1 | agree | 0.30 |  |
| 204 | pool-W9.md L226 | 0124-q250-r2: light share | 0.984 | 0.9840 | agree | 0.00 |  |
| 205 | pool-W9.md L227 | 0126-q500-r2: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19505 2.310 390.1 4.62 1.70 2207 1 | 19505 2.3100 390.09 4.623 1.702 2207 1 | agree | 0.30 |  |
| 206 | pool-W9.md L227 | 0126-q500-r2: light share | 0.986 | 0.9860 | agree | 0.00 |  |
| 207 | pool-W9.md L228 | 0128-off-r2: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19291 2.463 385.8 5.00 2.52 1951 1 | 19291 2.4630 385.81 4.997 2.521 1951 1 | agree | 0.30 |  |
| 208 | pool-W9.md L228 | 0128-off-r2: light share | 0.964 | 0.9640 | agree | 0.00 |  |
| 209 | pool-W9.md L229 | 0131-q125-r3: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19483 2.296 389.6 4.46 1.73 2187 1 | 19483 2.2960 389.63 4.465 1.728 2187 1 | agree | 0.50 |  |
| 210 | pool-W9.md L229 | 0131-q125-r3: light share | 0.992 | 0.9920 | agree | 0.00 |  |
| 211 | pool-W9.md L230 | 0133-q250-r3: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19485 2.302 389.7 4.46 1.73 2185 1 | 19485 2.3020 389.68 4.455 1.732 2185 1 | agree | 0.50 |  |
| 212 | pool-W9.md L230 | 0133-q250-r3: light share | 0.992 | 0.9920 | agree | 0.00 |  |
| 213 | pool-W9.md L231 | 0135-q500-r3: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19472 2.319 389.4 4.62 1.73 2201 1 | 19472 2.3190 389.41 4.619 1.729 2201 1 | agree | 0.14 |  |
| 214 | pool-W9.md L231 | 0135-q500-r3: light share | 0.985 | 0.9850 | agree | 0.00 |  |
| 215 | pool-W9.md L232 | 0137-off-r3: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19155 2.487 383.1 4.96 2.52 1966 1 | 19155 2.4870 383.09 4.965 2.522 1966 1 | agree | 0.50 |  |
| 216 | pool-W9.md L232 | 0137-off-r3: light share | 0.968 | 0.9680 | agree | 0.00 |  |
| 217 | pool-W9.md L233 | 0139-q0-r3: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19100 2.490 382.0 5.02 2.49 2003 1 | 19100 2.4900 381.98 5.017 2.486 2003 1 | agree | 0.40 |  |
| 218 | pool-W9.md L233 | 0139-q0-r3: light share | 0.967 | 0.9670 | agree | 0.00 |  |
| 219 | pool-W9.md L234 | 0141-q250-r4: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19451 2.324 389.0 4.52 1.73 2171 1 | 19451 2.3240 389.00 4.524 1.727 2171 1 | agree | 0.40 |  |
| 220 | pool-W9.md L234 | 0141-q250-r4: light share | 0.989 | 0.9890 | agree | 0.00 |  |
| 221 | pool-W9.md L235 | 0143-q500-r4: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19504 2.310 390.1 4.67 1.73 2215 1 | 19504 2.3100 390.07 4.673 1.728 2215 1 | agree | 0.30 |  |
| 222 | pool-W9.md L235 | 0143-q500-r4: light share | 0.983 | 0.9830 | agree | 0.00 |  |
| 223 | pool-W9.md L236 | 0145-off-r4: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19330 2.451 386.6 4.99 2.50 1963 1 | 19330 2.4510 386.60 4.988 2.497 1963 1 | agree | 0.30 |  |
| 224 | pool-W9.md L236 | 0145-off-r4: light share | 0.966 | 0.9660 | agree | 0.00 |  |
| 225 | pool-W9.md L237 | 0147-q0-r4: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19274 2.483 385.5 4.92 2.48 2034 1 | 19274 2.4830 385.47 4.916 2.480 2034 1 | agree | 0.40 |  |
| 226 | pool-W9.md L237 | 0147-q0-r4: light share | 0.969 | 0.9690 | agree | 0.00 |  |
| 227 | pool-W9.md L238 | 0149-q125-r4: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19468 2.315 389.4 4.48 1.86 2153 1 | 19468 2.3150 389.35 4.483 1.856 2153 1 | agree | 0.50 |  |
| 228 | pool-W9.md L238 | 0149-q125-r4: light share | 0.991 | 0.9910 | agree | 0.00 |  |
| 229 | pool-W9.md L239 | 0401-cold-off: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 13502 1.984 450.0 4.89 2.48 2016 0 | 13502 1.9840 450.05 4.892 2.484 2016 0 | agree | 0.48 |  |
| 230 | pool-W9.md L239 | 0401-cold-off: light share | 0.976 | 0.9760 | agree | 0.00 |  |
| 231 | pool-W9.md L240 | 0403-off-r1: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 20446 2.325 408.9 4.91 2.44 2027 1 | 20446 2.3250 408.91 4.912 2.438 2027 1 | agree | 0.20 |  |
| 232 | pool-W9.md L240 | 0403-off-r1: light share | 0.974 | 0.9740 | agree | 0.00 |  |
| 233 | pool-W9.md L241 | 0405-q0-r1: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19291 2.465 385.8 4.91 2.49 2030 1 | 19291 2.4650 385.80 4.913 2.493 2030 1 | agree | 0.30 |  |
| 234 | pool-W9.md L241 | 0405-q0-r1: light share | 0.970 | 0.9700 | agree | 0.00 |  |
| 235 | pool-W9.md L242 | 0407-q125-r1: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 18250 2.477 365.0 5.36 2.15 1857 1 | 18250 2.4770 364.99 5.364 2.147 1857 1 | agree | 0.40 |  |
| 236 | pool-W9.md L242 | 0407-q125-r1: light share | 0.956 | 0.9560 | agree | 0.00 |  |
| 237 | pool-W9.md L243 | 0409-q250-r1: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 18909 2.460 378.2 4.87 2.11 1894 1 | 18909 2.4600 378.18 4.867 2.106 1894 1 | agree | 0.40 |  |
| 238 | pool-W9.md L243 | 0409-q250-r1: light share | 0.976 | 0.9760 | agree | 0.00 |  |
| 239 | pool-W9.md L244 | 0411-q500-r1: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19435 2.316 388.7 4.62 1.73 2205 1 | 19435 2.3160 388.69 4.622 1.725 2205 1 | agree | 0.50 |  |
| 240 | pool-W9.md L244 | 0411-q500-r1: light share | 0.985 | 0.9850 | agree | 0.00 |  |
| 241 | pool-W9.md L245 | 0413-q0-r2: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19258 2.472 385.1 4.90 2.46 2086 1 | 19258 2.4720 385.15 4.896 2.456 2086 1 | agree | 0.48 |  |
| 242 | pool-W9.md L245 | 0413-q0-r2: light share | 0.970 | 0.9700 | agree | 0.00 |  |
| 243 | pool-W9.md L246 | 0415-q125-r2: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19549 2.295 391.0 4.45 1.75 2172 1 | 19549 2.2950 390.97 4.453 1.755 2172 1 | agree | 0.50 |  |
| 244 | pool-W9.md L246 | 0415-q125-r2: light share | 0.993 | 0.9920 | DISAGREE | 1.00 | light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share rounded to 3 dp |
| 245 | pool-W9.md L247 | 0417-q250-r2: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 18958 2.377 379.1 4.74 1.93 2075 1 | 18958 2.3770 379.15 4.743 1.934 2075 1 | agree | 0.48 |  |
| 246 | pool-W9.md L247 | 0417-q250-r2: light share | 0.981 | 0.9810 | agree | 0.00 |  |
| 247 | pool-W9.md L248 | 0419-q500-r2: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19291 2.356 385.8 4.73 2.03 1947 1 | 19291 2.3560 385.82 4.726 2.026 1947 1 | agree | 0.40 |  |
| 248 | pool-W9.md L248 | 0419-q500-r2: light share | 0.981 | 0.9810 | agree | 0.00 |  |
| 249 | pool-W9.md L249 | 0421-off-r2: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19108 2.469 382.2 5.10 2.54 1907 1 | 19108 2.4690 382.16 5.101 2.545 1907 1 | agree | 0.50 |  |
| 250 | pool-W9.md L249 | 0421-off-r2: light share | 0.962 | 0.9620 | agree | 0.00 |  |
| 251 | pool-W9.md L250 | 0423-q125-r3: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 18422 2.510 368.4 5.12 2.13 1853 1 | 18422 2.5100 368.43 5.118 2.133 1853 1 | agree | 0.34 |  |
| 252 | pool-W9.md L250 | 0423-q125-r3: light share | 0.964 | 0.9640 | agree | 0.00 |  |
| 253 | pool-W9.md L251 | 0425-q250-r3: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19321 2.356 386.4 4.63 1.98 1996 1 | 19321 2.3560 386.42 4.635 1.981 1996 1 | agree | 0.50 |  |
| 254 | pool-W9.md L251 | 0425-q250-r3: light share | 0.985 | 0.9850 | agree | 0.00 |  |
| 255 | pool-W9.md L252 | 0427-q500-r3: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19490 2.309 389.8 4.67 1.73 2205 1 | 19490 2.3090 389.79 4.665 1.731 2205 1 | agree | 0.50 |  |
| 256 | pool-W9.md L252 | 0427-q500-r3: light share | 0.983 | 0.9830 | agree | 0.00 |  |
| 257 | pool-W9.md L253 | 0429-off-r3: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19260 2.458 385.2 4.99 2.52 1975 1 | 19260 2.4580 385.19 4.992 2.519 1975 1 | agree | 0.20 |  |
| 258 | pool-W9.md L253 | 0429-off-r3: light share | 0.964 | 0.9640 | agree | 0.00 |  |
| 259 | pool-W9.md L254 | 0431-q0-r3: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19360 2.468 387.2 4.94 2.46 2071 1 | 19360 2.4680 387.19 4.944 2.457 2071 1 | agree | 0.40 |  |
| 260 | pool-W9.md L254 | 0431-q0-r3: light share | 0.969 | 0.9690 | agree | 0.00 |  |
| 261 | pool-W9.md L255 | 0433-q250-r4: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19457 2.324 389.1 4.53 1.79 2168 1 | 19457 2.3240 389.12 4.529 1.789 2168 1 | agree | 0.22 |  |
| 262 | pool-W9.md L255 | 0433-q250-r4: light share | 0.989 | 0.9880 | DISAGREE | 1.00 | light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share rounded to 3 dp |
| 263 | pool-W9.md L256 | 0435-q500-r4: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19492 2.319 389.8 4.68 1.71 2198 1 | 19492 2.3190 389.82 4.685 1.710 2198 1 | agree | 0.50 |  |
| 264 | pool-W9.md L256 | 0435-q500-r4: light share | 0.983 | 0.9830 | agree | 0.00 |  |
| 265 | pool-W9.md L257 | 0438-off-r4: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19229 2.466 384.6 4.98 2.49 1951 1 | 19229 2.4660 384.58 4.982 2.490 1951 1 | agree | 0.24 |  |
| 266 | pool-W9.md L257 | 0438-off-r4: light share | 0.966 | 0.9660 | agree | 0.00 |  |
| 267 | pool-W9.md L258 | 0440-q0-r4: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19201 2.473 384.0 4.96 2.46 1996 1 | 19201 2.4730 384.00 4.964 2.460 1996 1 | agree | 0.40 |  |
| 268 | pool-W9.md L258 | 0440-q0-r4: light share | 0.968 | 0.9680 | agree | 0.00 |  |
| 269 | pool-W9.md L259 | 0442-q125-r4: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19469 2.309 389.4 4.51 1.79 2167 1 | 19469 2.3090 389.38 4.512 1.791 2167 1 | agree | 0.20 |  |
| 270 | pool-W9.md L259 | 0442-q125-r4: light share | 0.989 | 0.9890 | agree | 0.00 |  |
| 271 | pool-W9.md L201 | W9 light share per arm (mean of results.csv light_share) | 0.968 0.970 0.983 0.986 0.984 | 0.9682 0.9699 0.9830 0.9859 0.9840 | agree | 0.25 | light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share rounded to 3 dp |
| 272 | pool-W9.md L201 | W9 light share one-way F (df1, df2) | 9.38 (4, 35) | 9.679 4 35 / posted run-table light shares: 9.797 4 35 | DISAGREE | 29.86 | light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share rounded to 3 dp |
| 273 | pool-W5b.md L17 | W5b d11: planned (+cold), rows, timed, kept, failed | 12 (+2) 14 12 12 0 | 12 2 14 12 12 0 | agree | 0.00 |  |
| 274 | pool-W5b.md L18 | W5b d11t: planned (+cold), rows, timed, kept, failed | 12 (+0) 12 12 12 0 | 12 0 12 12 12 0 | agree | 0.00 |  |
| 275 | pool-W5b.md L19 | W5b d11p: planned (+cold), rows, timed, kept, failed | 12 (+0) 12 12 12 0 | 12 0 12 12 12 0 | agree | 0.00 |  |
| 276 | pool-W5b.md L36 | W5b raw median ms GM % d11t vs d11 [95 % CI], one-way | +1.3 [-0.8, +3.4] | 1.32 -0.76 3.43 | agree | 0.43 |  |
| 277 | pool-W5b.md L36 | W5b raw median ms GM % d11p vs d11 [95 % CI], one-way | +0.5 [-1.5, +2.6] | 0.51 -1.55 2.61 | agree | 0.47 |  |
| 278 | pool-W5b.md L36 | W5b raw median ms: n per arm | 12 12 | 12 12 | agree | 0.00 |  |
| 279 | pool-W5b.md L36 | W5b raw median ms: d11 band % ((max-min)/median), pooled CV %, 4 vs 4 band %, df | 10.1 2.5 3.6 33 | 10.12 2.49 3.64 33 | agree | 0.44 | 4 vs 4 band = 100 (exp(t s sqrt(1/2)) - 1), s = pooled SD of ln |
| 280 | pool-W5b.md L37 | W5b raw fps GM % d11t vs d11 [95 % CI], one-way | -1.3 [-3.0, +0.4] | -1.30 -2.97 0.41 | agree | 0.25 |  |
| 281 | pool-W5b.md L37 | W5b raw fps GM % d11p vs d11 [95 % CI], one-way | -0.7 [-2.4, +1.0] | -0.73 -2.42 0.98 | agree | 0.35 |  |
| 282 | pool-W5b.md L37 | W5b raw fps: n per arm | 12 12 | 12 12 | agree | 0.00 |  |
| 283 | pool-W5b.md L37 | W5b raw fps: d11 band % ((max-min)/median), pooled CV %, 4 vs 4 band %, df | 8.7 2.1 3.0 33 | 8.73 2.06 3.02 33 | agree | 0.35 | 4 vs 4 band = 100 (exp(t s sqrt(1/2)) - 1), s = pooled SD of ln |
| 284 | pool-W5b.md L45 | W5b raw p99 ms GM % d11t vs d11 [95 % CI], one-way | +1.2 [-0.6, +2.9] | 1.15 -0.58 2.91 | agree | 0.47 |  |
| 285 | pool-W5b.md L45 | W5b raw p99 ms GM % d11p vs d11 [95 % CI], one-way | +0.1 [-1.6, +1.8] | 0.06 -1.65 1.81 | agree | 0.46 |  |
| 286 | pool-W5b.md L45 | W5b raw p99 ms: n per arm | 12 12 | 12 12 | agree | 0.00 |  |
| 287 | pool-W5b.md L45 | W5b raw p99 ms: d11 band % ((max-min)/median), pooled CV %, 4 vs 4 band %, df | 7.6 2.1 3.0 33 | 7.58 2.08 3.03 33 | agree | 0.32 | 4 vs 4 band = 100 (exp(t s sqrt(1/2)) - 1), s = pooled SD of ln |
| 288 | pool-W5b.md L54 | W5b d11 mean cores | 2.55 | 2.549 | agree | 0.12 |  |
| 289 | pool-W5b.md L54 | W5b cores d11t: mean; change [CI]; GM % one-way [CI]; GM % B-block [CI] | 2.33; -0.22 [-0.25, -0.19]; -8.6 [-9.8, -7.4] *; -8.6 [-9.6, -7.6] * | 2.329 -0.220 -0.251 -0.189 -8.63 -9.80 -7.45 -8.63 -9.60 -7.65 | DISAGREE | 0.50 |  |
| 290 | pool-W5b.md L54 | W5b cores d11p: mean; change [CI]; GM % one-way [CI]; GM % B-block [CI] | 2.34; -0.20 [-0.23, -0.17]; -8.0 [-9.2, -6.8] *; -8.0 [-9.0, -7.0] * | 2.345 -0.204 -0.235 -0.173 -8.00 -9.18 -6.81 -8.00 -8.98 -7.01 | agree | 0.49 |  |
| 291 | pool-W5b.md L67 | W5b paired raw median ms d11t vs d11: mean +- hw (med; higher k/n) | +1.33 +- 1.31 (med +0.46; higher 11/12) | 1.334 1.305 0.459 11 12 | agree | 0.49 |  |
| 292 | pool-W5b.md L67 | W5b paired raw median ms d11p vs d11: mean +- hw (med; higher k/n) | +0.53 +- 1.38 (med -0.38; higher 5/12) | 0.529 1.381 -0.377 5 12 | agree | 0.28 |  |
| 293 | pool-W5b.md L68 | W5b paired raw fps d11t vs d11: mean +- hw (med; higher k/n) | -1.28 +- 1.24 (med -0.47; higher 3/12) | -1.278 1.239 -0.468 3 12 | agree | 0.19 |  |
| 294 | pool-W5b.md L68 | W5b paired raw fps d11p vs d11: mean +- hw (med; higher k/n) | -0.72 +- 0.96 (med +0.04; higher 7/12) | -0.724 0.956 0.040 7 12 | agree | 0.42 |  |
| 295 | pool-W5b.md L71 | W5b paired cpu cores d11t vs d11: mean +- hw (med; higher k/n) | -8.62 +- 1.05 (med -8.90; higher 0/12) | -8.617 1.045 -8.901 0 12 | agree | 0.46 |  |
| 296 | pool-W5b.md L71 | W5b paired cpu cores d11p vs d11: mean +- hw (med; higher k/n) | -7.98 +- 1.16 (med -8.54; higher 0/12) | -7.983 1.159 -8.538 0 12 | agree | 0.29 |  |
| 297 | pool-W5b.md L79 | W5b pass 1: kept | 18 | 18 | agree | 0.00 |  |
| 298 | pool-W5b.md L79 | W5b pass 1 alone: cores change d11t [CI] |  -0.23 [-0.28, -0.18] | -0.229 -0.277 -0.180 | agree | 0.28 |  |
| 299 | pool-W5b.md L79 | W5b pass 1 alone: cores change d11p [CI] |  -0.20 [-0.25, -0.15] | -0.203 -0.252 -0.155 | agree | 0.46 |  |
| 300 | pool-W5b.md L80 | W5b pass 2: kept | 18 | 18 | agree | 0.00 |  |
| 301 | pool-W5b.md L80 | W5b pass 2 alone: cores change d11t [CI] |  -0.21 [-0.25, -0.17] | -0.212 -0.252 -0.171 | agree | 0.22 |  |
| 302 | pool-W5b.md L80 | W5b pass 2 alone: cores change d11p [CI] |  -0.20 [-0.25, -0.16] | -0.205 -0.245 -0.164 | agree | 0.48 |  |
| 303 | pool-W5b.md L92 | W5b no-slow-d11t: n per arm | 10 12 | 10 12 | agree | 0.00 |  |
| 304 | pool-W5b.md L92 | W5b no-slow-d11t: raw median ms d11t | +0.6 [-1.4, +2.7] | 0.62 -1.43 2.72 | agree | 0.32 |  |
| 305 | pool-W5b.md L92 | W5b no-slow-d11t: raw median ms d11p | +0.5 [-1.4, +2.5] | 0.51 -1.45 2.50 | agree | 0.49 |  |
| 306 | pool-W5b.md L93 | W5b no-slow-d11t: raw fps d11t | -0.7 [-2.4, +1.0] | -0.73 -2.40 0.98 | agree | 0.25 |  |
| 307 | pool-W5b.md L93 | W5b no-slow-d11t: raw fps d11p | -0.7 [-2.3, +0.9] | -0.73 -2.33 0.89 | agree | 0.35 |  |
| 308 | pool-W5b.md L94 | W5b no-slow-d11t: raw p99 ms d11t | +0.9 [-0.9, +2.7] | 0.87 -0.95 2.72 | agree | 0.46 |  |
| 309 | pool-W5b.md L94 | W5b no-slow-d11t: raw p99 ms d11p | +0.1 [-1.7, +1.8] | 0.06 -1.65 1.81 | agree | 0.48 |  |
| 310 | pool-W5b.md L96 | W5b no-slow-d11t: cpu cores change d11t | -0.22 [-0.26, -0.19] | -0.225 -0.258 -0.192 | agree | 0.47 |  |
| 311 | pool-W5b.md L96 | W5b no-slow-d11t: cpu cores change d11p | -0.20 [-0.24, -0.17] | -0.204 -0.235 -0.172 | agree | 0.46 |  |
| 312 | pool-W5b.md L106 | W5b no-0221: n per arm | 11 12 | 11 12 | agree | 0.00 |  |
| 313 | pool-W5b.md L106 | W5b no-0221: raw median ms d11t | +1.4 [-0.7, +3.6] | 1.42 -0.73 3.61 | agree | 0.30 |  |
| 314 | pool-W5b.md L106 | W5b no-0221: raw median ms d11p | +0.5 [-1.6, +2.6] | 0.51 -1.57 2.64 | agree | 0.35 |  |
| 315 | pool-W5b.md L107 | W5b no-0221: raw fps d11t | -1.3 [-3.0, +0.5] | -1.29 -3.03 0.49 | agree | 0.32 |  |
| 316 | pool-W5b.md L107 | W5b no-0221: raw fps d11p | -0.7 [-2.5, +1.0] | -0.73 -2.45 1.01 | agree | 0.49 |  |
| 317 | pool-W5b.md L108 | W5b no-0221: raw p99 ms d11t | +0.9 [-0.8, +2.7] | 0.94 -0.81 2.73 | agree | 0.43 |  |
| 318 | pool-W5b.md L108 | W5b no-0221: raw p99 ms d11p | +0.1 [-1.6, +1.8] | 0.06 -1.64 1.80 | agree | 0.39 |  |
| 319 | pool-W5b.md L110 | W5b no-0221: cpu cores change d11t | -0.22 [-0.25, -0.19] | -0.219 -0.251 -0.187 | agree | 0.34 |  |
| 320 | pool-W5b.md L110 | W5b no-0221: cpu cores change d11p | -0.20 [-0.24, -0.17] | -0.204 -0.235 -0.172 | agree | 0.46 |  |
| 321 | pool-W5b.md L120 | W5b no-audit-flag: n per arm | 9 10 | 9 10 | agree | 0.00 |  |
| 322 | pool-W5b.md L120 | W5b no-audit-flag: raw median ms d11t | +0.4 [-1.8, +2.7] | 0.40 -1.83 2.67 | agree | 0.29 |  |
| 323 | pool-W5b.md L120 | W5b no-audit-flag: raw median ms d11p | +0.5 [-1.7, +2.7] | 0.52 -1.65 2.73 | DISAGREE | 0.51 |  |
| 324 | pool-W5b.md L121 | W5b no-audit-flag: raw fps d11t | -0.3 [-2.1, +1.5] | -0.30 -2.09 1.53 | agree | 0.27 |  |
| 325 | pool-W5b.md L121 | W5b no-audit-flag: raw fps d11p | -0.6 [-2.3, +1.2] | -0.56 -2.30 1.21 | agree | 0.38 |  |
| 326 | pool-W5b.md L122 | W5b no-audit-flag: raw p99 ms d11t | +0.2 [-1.4, +1.8] | 0.19 -1.43 1.83 | agree | 0.26 |  |
| 327 | pool-W5b.md L122 | W5b no-audit-flag: raw p99 ms d11p | +0.1 [-1.5, +1.7] | 0.09 -1.48 1.68 | agree | 0.23 |  |
| 328 | pool-W5b.md L124 | W5b no-audit-flag: cpu cores change d11t | -0.22 [-0.26, -0.19] | -0.224 -0.257 -0.190 | agree | 0.36 |  |
| 329 | pool-W5b.md L124 | W5b no-audit-flag: cpu cores change d11p | -0.20 [-0.24, -0.17] | -0.204 -0.237 -0.171 | agree | 0.41 |  |
| 330 | pool-W5b.md L134 | W5b no-flagged: n per arm | 8 10 | 8 10 | agree | 0.00 |  |
| 331 | pool-W5b.md L134 | W5b no-flagged: raw median ms d11t | +0.0 [-2.3, +2.3] | 0.01 -2.25 2.32 | DISAGREE | 0.52 |  |
| 332 | pool-W5b.md L134 | W5b no-flagged: raw median ms d11p | +0.5 [-1.6, +2.7] | 0.52 -1.62 2.70 | agree | 0.20 |  |
| 333 | pool-W5b.md L135 | W5b no-flagged: raw fps d11t | +0.0 [-1.8, +1.9] | 0.01 -1.82 1.88 | agree | 0.20 |  |
| 334 | pool-W5b.md L135 | W5b no-flagged: raw fps d11p | -0.6 [-2.3, +1.2] | -0.56 -2.28 1.18 | agree | 0.38 |  |
| 335 | pool-W5b.md L136 | W5b no-flagged: raw p99 ms d11t | +0.0 [-1.7, +1.7] | 0.03 -1.65 1.74 | DISAGREE | 0.51 |  |
| 336 | pool-W5b.md L136 | W5b no-flagged: raw p99 ms d11p | +0.1 [-1.5, +1.7] | 0.09 -1.50 1.69 | agree | 0.14 |  |
| 337 | pool-W5b.md L138 | W5b no-flagged: cpu cores change d11t | -0.23 [-0.26, -0.19] | -0.226 -0.261 -0.191 | agree | 0.41 |  |
| 338 | pool-W5b.md L138 | W5b no-flagged: cpu cores change d11p | -0.20 [-0.24, -0.17] | -0.204 -0.237 -0.171 | agree | 0.41 |  |
| 339 | pool-W5b.md L148 | W5b no-loaded: n per arm | 8 8 | 8 8 | agree | 0.00 |  |
| 340 | pool-W5b.md L148 | W5b no-loaded: raw median ms d11t | +0.0 [-2.3, +2.4] | 0.01 -2.25 2.33 | DISAGREE | 0.75 |  |
| 341 | pool-W5b.md L148 | W5b no-loaded: raw median ms d11p | +0.0 [-2.3, +2.4] | 0.02 -2.24 2.33 | DISAGREE | 0.67 |  |
| 342 | pool-W5b.md L149 | W5b no-loaded: raw fps d11t | +0.0 [-1.8, +1.9] | 0.01 -1.82 1.88 | agree | 0.21 |  |
| 343 | pool-W5b.md L149 | W5b no-loaded: raw fps d11p | -0.2 [-2.0, +1.7] | -0.15 -1.98 1.71 | agree | 0.47 |  |
| 344 | pool-W5b.md L150 | W5b no-loaded: raw p99 ms d11t | +0.0 [-1.7, +1.8] | 0.03 -1.69 1.79 | agree | 0.33 |  |
| 345 | pool-W5b.md L150 | W5b no-loaded: raw p99 ms d11p | -0.2 [-1.9, +1.6] | -0.18 -1.90 1.57 | agree | 0.31 |  |
| 346 | pool-W5b.md L152 | W5b no-loaded: cpu cores change d11t | -0.23 [-0.26, -0.19] | -0.226 -0.261 -0.191 | agree | 0.41 |  |
| 347 | pool-W5b.md L152 | W5b no-loaded: cpu cores change d11p | -0.21 [-0.25, -0.18] | -0.213 -0.248 -0.177 | agree | 0.27 |  |
| 348 | pool-W5b.md L162 | W5b no-p2-first3: n per arm | 11 11 | 11 11 | agree | 0.00 |  |
| 349 | pool-W5b.md L162 | W5b no-p2-first3: raw median ms d11t | +0.8 [-1.3, +3.0] | 0.85 -1.26 3.00 | agree | 0.48 |  |
| 350 | pool-W5b.md L162 | W5b no-p2-first3: raw median ms d11p | +0.7 [-1.4, +2.8] | 0.65 -1.45 2.80 | agree | 0.50 |  |
| 351 | pool-W5b.md L163 | W5b no-p2-first3: raw fps d11t | -0.8 [-2.5, +0.9] | -0.80 -2.51 0.94 | agree | 0.39 |  |
| 352 | pool-W5b.md L163 | W5b no-p2-first3: raw fps d11p | -0.6 [-2.4, +1.1] | -0.64 -2.35 1.10 | agree | 0.46 |  |
| 353 | pool-W5b.md L164 | W5b no-p2-first3: raw p99 ms d11t | +1.1 [-0.7, +2.9] | 1.09 -0.69 2.90 | agree | 0.10 |  |
| 354 | pool-W5b.md L164 | W5b no-p2-first3: raw p99 ms d11p | +0.1 [-1.7, +1.9] | 0.06 -1.70 1.86 | agree | 0.45 |  |
| 355 | pool-W5b.md L166 | W5b no-p2-first3: cpu cores change d11t | -0.22 [-0.25, -0.19] | -0.218 -0.251 -0.186 | agree | 0.37 |  |
| 356 | pool-W5b.md L166 | W5b no-p2-first3: cpu cores change d11p | -0.20 [-0.23, -0.17] | -0.201 -0.233 -0.169 | agree | 0.33 |  |
| 357 | pool-W5b.md L176 | W5b drop-p2-r1r2: n per arm | 10 10 | 10 10 | agree | 0.00 |  |
| 358 | pool-W5b.md L176 | W5b drop-p2-r1r2: raw median ms d11t | +0.7 [-1.6, +3.0] | 0.66 -1.62 2.98 | agree | 0.44 |  |
| 359 | pool-W5b.md L176 | W5b drop-p2-r1r2: raw median ms d11p | +0.8 [-1.5, +3.1] | 0.77 -1.51 3.10 | agree | 0.31 |  |
| 360 | pool-W5b.md L177 | W5b drop-p2-r1r2: raw fps d11t | -0.7 [-2.5, +1.2] | -0.66 -2.52 1.24 | agree | 0.41 |  |
| 361 | pool-W5b.md L177 | W5b drop-p2-r1r2: raw fps d11p | -0.7 [-2.6, +1.2] | -0.71 -2.57 1.19 | agree | 0.26 |  |
| 362 | pool-W5b.md L178 | W5b drop-p2-r1r2: raw p99 ms d11t | +1.1 [-0.9, +3.1] | 1.08 -0.89 3.10 | agree | 0.17 |  |
| 363 | pool-W5b.md L178 | W5b drop-p2-r1r2: raw p99 ms d11p | +0.1 [-1.9, +2.1] | 0.10 -1.86 2.09 | agree | 0.43 |  |
| 364 | pool-W5b.md L180 | W5b drop-p2-r1r2: cpu cores change d11t | -0.22 [-0.25, -0.19] | -0.220 -0.253 -0.186 | agree | 0.36 |  |
| 365 | pool-W5b.md L180 | W5b drop-p2-r1r2: cpu cores change d11p | -0.19 [-0.23, -0.16] | -0.194 -0.227 -0.161 | agree | 0.42 |  |
| 366 | pool-W5b.md L190 | W5b drop-r1-both: n per arm | 10 10 | 10 10 | agree | 0.00 |  |
| 367 | pool-W5b.md L190 | W5b drop-r1-both: raw median ms d11t | +0.7 [-0.3, +1.7] | 0.68 -0.31 1.67 | agree | 0.26 |  |
| 368 | pool-W5b.md L190 | W5b drop-r1-both: raw median ms d11p | +0.1 [-0.9, +1.1] | 0.09 -0.89 1.08 | agree | 0.18 |  |
| 369 | pool-W5b.md L191 | W5b drop-r1-both: raw fps d11t | -0.7 [-1.5, +0.1] | -0.69 -1.49 0.12 | agree | 0.24 |  |
| 370 | pool-W5b.md L191 | W5b drop-r1-both: raw fps d11p | -0.2 [-1.0, +0.6] | -0.23 -1.04 0.58 | agree | 0.43 |  |
| 371 | pool-W5b.md L192 | W5b drop-r1-both: raw p99 ms d11t | +1.0 [-0.4, +2.4] | 1.02 -0.38 2.43 | agree | 0.33 |  |
| 372 | pool-W5b.md L192 | W5b drop-r1-both: raw p99 ms d11p | -0.3 [-1.7, +1.1] | -0.29 -1.67 1.10 | agree | 0.29 |  |
| 373 | pool-W5b.md L194 | W5b drop-r1-both: cpu cores change d11t | -0.22 [-0.25, -0.19] | -0.224 -0.255 -0.193 | agree | 0.47 |  |
| 374 | pool-W5b.md L194 | W5b drop-r1-both: cpu cores change d11p | -0.21 [-0.24, -0.18] | -0.208 -0.239 -0.177 | agree | 0.29 |  |
| 375 | pool-W5b.md L204 | W5b pass1-only: n per arm | 6 6 | 6 6 | agree | 0.00 |  |
| 376 | pool-W5b.md L204 | W5b pass1-only: raw median ms d11t | +0.9 [-3.0, +4.9] | 0.89 -2.96 4.89 | agree | 0.40 |  |
| 377 | pool-W5b.md L204 | W5b pass1-only: raw median ms d11p | +0.8 [-3.1, +4.8] | 0.76 -3.09 4.75 | agree | 0.49 |  |
| 378 | pool-W5b.md L205 | W5b pass1-only: raw fps d11t | -0.9 [-4.0, +2.4] | -0.86 -4.00 2.38 | agree | 0.40 |  |
| 379 | pool-W5b.md L205 | W5b pass1-only: raw fps d11p | -0.7 [-3.8, +2.6] | -0.68 -3.83 2.56 | agree | 0.35 |  |
| 380 | pool-W5b.md L206 | W5b pass1-only: raw p99 ms d11t | +1.5 [-1.7, +4.7] | 1.47 -1.69 4.72 | agree | 0.32 |  |
| 381 | pool-W5b.md L206 | W5b pass1-only: raw p99 ms d11p | -0.3 [-3.4, +2.9] | -0.27 -3.37 2.92 | agree | 0.28 |  |
| 382 | pool-W5b.md L208 | W5b pass1-only: cpu cores change d11t | -0.23 [-0.28, -0.18] | -0.229 -0.277 -0.180 | agree | 0.28 |  |
| 383 | pool-W5b.md L208 | W5b pass1-only: cpu cores change d11p | -0.20 [-0.25, -0.15] | -0.203 -0.252 -0.155 | agree | 0.46 |  |
| 384 | pool-W5b.md L218 | W5b pass2-only: n per arm | 6 6 | 6 6 | agree | 0.00 |  |
| 385 | pool-W5b.md L218 | W5b pass2-only: raw median ms d11t | +1.7 [-0.2, +3.7] | 1.74 -0.18 3.71 | agree | 0.44 |  |
| 386 | pool-W5b.md L218 | W5b pass2-only: raw median ms d11p | +0.3 [-1.6, +2.2] | 0.26 -1.64 2.20 | agree | 0.38 |  |
| 387 | pool-W5b.md L219 | W5b pass2-only: raw fps d11t | -1.7 [-3.4, -0.1] * | -1.73 -3.36 -0.08 | agree | 0.41 |  |
| 388 | pool-W5b.md L219 | W5b pass2-only: raw fps d11p | -0.8 [-2.4, +0.9] | -0.79 -2.43 0.88 | agree | 0.31 |  |
| 389 | pool-W5b.md L220 | W5b pass2-only: raw p99 ms d11t | +0.8 [-1.1, +2.8] | 0.84 -1.12 2.83 | agree | 0.39 |  |
| 390 | pool-W5b.md L220 | W5b pass2-only: raw p99 ms d11p | +0.4 [-1.5, +2.4] | 0.40 -1.54 2.39 | agree | 0.43 |  |
| 391 | pool-W5b.md L222 | W5b pass2-only: cpu cores change d11t | -0.21 [-0.25, -0.17] | -0.212 -0.252 -0.171 | agree | 0.22 |  |
| 392 | pool-W5b.md L222 | W5b pass2-only: cpu cores change d11p | -0.20 [-0.25, -0.16] | -0.205 -0.245 -0.164 | agree | 0.48 |  |
| 393 | pool-W5b.md L236 | 0155-cold-d11: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 12571 2.306 419.0 4.66 2.54 2014 0 | 12571 2.3060 419.01 4.661 2.545 2014 0 | agree | 0.50 |  |
| 394 | pool-W5b.md L236 | 0155-cold-d11: light share | 0.983 | 0.9830 | agree | 0.00 |  |
| 395 | pool-W5b.md L237 | 0157-d11-r1: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 20755 2.288 415.1 4.55 2.46 1989 1 | 20755 2.2880 415.09 4.551 2.456 1989 1 | agree | 0.40 |  |
| 396 | pool-W5b.md L237 | 0157-d11-r1: light share | 0.988 | 0.9880 | agree | 0.00 |  |
| 397 | pool-W5b.md L238 | 0159-d11t-r1: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 20353 2.347 407.0 4.63 2.29 1963 1 | 20353 2.3470 407.04 4.633 2.291 1963 1 | agree | 0.41 |  |
| 398 | pool-W5b.md L238 | 0159-d11t-r1: light share | 0.984 | 0.9840 | agree | 0.00 |  |
| 399 | pool-W5b.md L239 | 0201-d11p-r1: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19798 2.435 395.9 4.72 2.32 1959 1 | 19798 2.4350 395.94 4.719 2.323 1959 1 | agree | 0.44 |  |
| 400 | pool-W5b.md L239 | 0201-d11p-r1: light share | 0.979 | 0.9790 | agree | 0.00 |  |
| 401 | pool-W5b.md L240 | 0203-d11t-r2: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19285 2.496 385.7 4.85 2.29 1988 1 | 19285 2.4960 385.70 4.851 2.293 1988 1 | agree | 0.30 |  |
| 402 | pool-W5b.md L240 | 0203-d11t-r2: light share | 0.971 | 0.9710 | agree | 0.00 |  |
| 403 | pool-W5b.md L241 | 0205-d11p-r2: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19246 2.511 384.9 4.75 2.38 1928 1 | 19246 2.5110 384.91 4.748 2.375 1928 1 | agree | 0.50 |  |
| 404 | pool-W5b.md L241 | 0205-d11p-r2: light share | 0.977 | 0.9770 | agree | 0.00 |  |
| 405 | pool-W5b.md L242 | 0207-d11-r2: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19201 2.528 384.0 4.79 2.52 1952 1 | 19201 2.5280 384.00 4.794 2.525 1952 1 | agree | 0.50 |  |
| 406 | pool-W5b.md L242 | 0207-d11-r2: light share | 0.976 | 0.9760 | agree | 0.00 |  |
| 407 | pool-W5b.md L243 | 0209-d11p-r3: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19091 2.544 381.8 4.80 2.37 1854 1 | 19091 2.5440 381.80 4.800 2.372 1854 1 | agree | 0.20 |  |
| 408 | pool-W5b.md L243 | 0209-d11p-r3: light share | 0.976 | 0.9760 | agree | 0.00 |  |
| 409 | pool-W5b.md L244 | 0211-d11-r3: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19074 2.542 381.5 4.90 2.59 1953 1 | 19074 2.5420 381.47 4.900 2.588 1953 1 | agree | 0.34 |  |
| 410 | pool-W5b.md L244 | 0211-d11-r3: light share | 0.970 | 0.9700 | agree | 0.00 |  |
| 411 | pool-W5b.md L245 | 0213-d11t-r3: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 18588 2.606 371.7 5.10 2.39 1829 1 | 18588 2.6060 371.75 5.102 2.386 1829 1 | agree | 0.47 |  |
| 412 | pool-W5b.md L245 | 0213-d11t-r3: light share | 0.962 | 0.9620 | agree | 0.00 |  |
| 413 | pool-W5b.md L246 | 0215-d11-r4: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19211 2.526 384.2 4.87 2.58 1950 1 | 19211 2.5260 384.21 4.865 2.581 1950 1 | agree | 0.50 |  |
| 414 | pool-W5b.md L246 | 0215-d11-r4: light share | 0.972 | 0.9720 | agree | 0.00 |  |
| 415 | pool-W5b.md L247 | 0217-d11t-r4: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19167 2.532 383.3 4.87 2.29 1928 1 | 19167 2.5320 383.33 4.868 2.291 1928 1 | agree | 0.30 |  |
| 416 | pool-W5b.md L247 | 0217-d11t-r4: light share | 0.973 | 0.9730 | agree | 0.00 |  |
| 417 | pool-W5b.md L248 | 0219-d11p-r4: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19243 2.505 384.8 4.85 2.33 1946 1 | 19243 2.5050 384.84 4.850 2.327 1946 1 | agree | 0.39 |  |
| 418 | pool-W5b.md L248 | 0219-d11p-r4: light share | 0.973 | 0.9720 | DISAGREE | 1.00 | light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share rounded to 3 dp |
| 419 | pool-W5b.md L249 | 0221-d11t-r5: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19119 2.498 382.4 4.99 2.31 1956 1 | 19119 2.4980 382.36 4.986 2.315 1956 1 | agree | 0.50 |  |
| 420 | pool-W5b.md L249 | 0221-d11t-r5: light share | 0.972 | 0.9720 | agree | 0.00 |  |
| 421 | pool-W5b.md L250 | 0223-d11p-r5: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19254 2.500 385.1 4.87 2.32 1950 1 | 19254 2.5000 385.07 4.867 2.321 1950 1 | agree | 0.30 |  |
| 422 | pool-W5b.md L250 | 0223-d11p-r5: light share | 0.970 | 0.9700 | agree | 0.00 |  |
| 423 | pool-W5b.md L251 | 0225-d11-r5: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19254 2.492 385.1 4.88 2.54 1952 1 | 19254 2.4920 385.08 4.881 2.543 1952 1 | agree | 0.30 |  |
| 424 | pool-W5b.md L251 | 0225-d11-r5: light share | 0.970 | 0.9700 | agree | 0.00 |  |
| 425 | pool-W5b.md L252 | 0227-d11p-r6: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19309 2.489 386.2 4.76 2.30 1945 1 | 19309 2.4890 386.18 4.763 2.296 1945 1 | agree | 0.40 |  |
| 426 | pool-W5b.md L252 | 0227-d11p-r6: light share | 0.977 | 0.9770 | agree | 0.00 |  |
| 427 | pool-W5b.md L253 | 0229-d11-r6: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19284 2.504 385.7 4.84 2.54 1951 1 | 19284 2.5040 385.68 4.842 2.541 1951 1 | agree | 0.24 |  |
| 428 | pool-W5b.md L253 | 0229-d11-r6: light share | 0.972 | 0.9720 | agree | 0.00 |  |
| 429 | pool-W5b.md L254 | 0231-d11t-r6: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19257 2.531 385.1 4.82 2.29 1969 1 | 19257 2.5310 385.13 4.820 2.287 1969 1 | agree | 0.30 |  |
| 430 | pool-W5b.md L254 | 0231-d11t-r6: light share | 0.974 | 0.9740 | agree | 0.00 |  |
| 431 | pool-W5b.md L255 | 0451-cold-d11: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 13255 2.094 441.8 4.61 2.48 1974 0 | 13255 2.0940 441.81 4.613 2.480 1974 0 | agree | 0.30 |  |
| 432 | pool-W5b.md L255 | 0451-cold-d11: light share | 0.987 | 0.9870 | agree | 0.00 |  |
| 433 | pool-W5b.md L256 | 0453-d11-r1: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19649 2.483 393.0 4.92 2.60 1848 1 | 19649 2.4830 392.97 4.917 2.602 1848 1 | agree | 0.32 |  |
| 434 | pool-W5b.md L256 | 0453-d11-r1: light share | 0.976 | 0.9760 | agree | 0.00 |  |
| 435 | pool-W5b.md L257 | 0455-d11t-r1: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 18357 2.647 367.1 5.01 2.37 1873 1 | 18357 2.6470 367.13 5.008 2.365 1873 1 | agree | 0.50 |  |
| 436 | pool-W5b.md L257 | 0455-d11t-r1: light share | 0.966 | 0.9660 | agree | 0.00 |  |
| 437 | pool-W5b.md L258 | 0457-d11p-r1: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19302 2.457 386.0 4.92 2.37 1780 1 | 19302 2.4570 386.03 4.922 2.368 1780 1 | agree | 0.26 |  |
| 438 | pool-W5b.md L258 | 0457-d11p-r1: light share | 0.969 | 0.9690 | agree | 0.00 |  |
| 439 | pool-W5b.md L259 | 0459-d11t-r2: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 18832 2.582 376.6 4.88 2.34 1937 1 | 18832 2.5820 376.63 4.877 2.339 1937 1 | agree | 0.34 |  |
| 440 | pool-W5b.md L259 | 0459-d11t-r2: light share | 0.972 | 0.9720 | agree | 0.00 |  |
| 441 | pool-W5b.md L260 | 0501-d11p-r2: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19273 2.499 385.4 4.81 2.27 1973 1 | 19273 2.4990 385.44 4.807 2.274 1973 1 | agree | 0.43 |  |
| 442 | pool-W5b.md L260 | 0501-d11p-r2: light share | 0.975 | 0.9750 | agree | 0.00 |  |
| 443 | pool-W5b.md L261 | 0504-d11-r2: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19259 2.512 385.2 4.82 2.54 1982 1 | 19259 2.5120 385.18 4.821 2.545 1982 1 | agree | 0.50 |  |
| 444 | pool-W5b.md L261 | 0504-d11-r2: light share | 0.974 | 0.9740 | agree | 0.00 |  |
| 445 | pool-W5b.md L262 | 0506-d11p-r3: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19295 2.515 385.9 4.80 2.35 1942 1 | 19295 2.5150 385.89 4.804 2.354 1942 1 | agree | 0.40 |  |
| 446 | pool-W5b.md L262 | 0506-d11p-r3: light share | 0.978 | 0.9780 | agree | 0.00 |  |
| 447 | pool-W5b.md L263 | 0508-d11-r3: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19251 2.521 385.0 4.77 2.59 1957 1 | 19251 2.5210 384.99 4.774 2.590 1957 1 | agree | 0.40 |  |
| 448 | pool-W5b.md L263 | 0508-d11-r3: light share | 0.975 | 0.9760 | DISAGREE | 1.00 | light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share rounded to 3 dp |
| 449 | pool-W5b.md L264 | 0510-d11t-r3: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 18965 2.528 379.3 5.02 2.31 1916 1 | 18965 2.5280 379.29 5.021 2.311 1916 1 | agree | 0.13 |  |
| 450 | pool-W5b.md L264 | 0510-d11t-r3: light share | 0.966 | 0.9660 | agree | 0.00 |  |
| 451 | pool-W5b.md L265 | 0512-d11-r4: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19271 2.517 385.4 4.81 2.57 1967 1 | 19271 2.5170 385.42 4.814 2.569 1967 1 | agree | 0.40 |  |
| 452 | pool-W5b.md L265 | 0512-d11-r4: light share | 0.975 | 0.9750 | agree | 0.00 |  |
| 453 | pool-W5b.md L266 | 0514-d11t-r4: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19236 2.518 384.7 4.77 2.34 1982 1 | 19236 2.5180 384.72 4.767 2.342 1982 1 | agree | 0.30 |  |
| 454 | pool-W5b.md L266 | 0514-d11t-r4: light share | 0.974 | 0.9740 | agree | 0.00 |  |
| 455 | pool-W5b.md L267 | 0516-d11p-r4: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19273 2.504 385.5 4.84 2.38 1962 1 | 19273 2.5040 385.46 4.843 2.380 1962 1 | agree | 0.43 |  |
| 456 | pool-W5b.md L267 | 0516-d11p-r4: light share | 0.975 | 0.9750 | agree | 0.00 |  |
| 457 | pool-W5b.md L268 | 0518-d11t-r5: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19288 2.520 385.7 4.77 2.36 1967 1 | 19288 2.5200 385.75 4.770 2.359 1967 1 | agree | 0.49 |  |
| 458 | pool-W5b.md L268 | 0518-d11t-r5: light share | 0.974 | 0.9740 | agree | 0.00 |  |
| 459 | pool-W5b.md L269 | 0520-d11p-r5: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 18778 2.586 375.6 4.85 2.38 1906 1 | 18778 2.5860 375.55 4.847 2.375 1906 1 | agree | 0.50 |  |
| 460 | pool-W5b.md L269 | 0520-d11p-r5: light share | 0.972 | 0.9720 | agree | 0.00 |  |
| 461 | pool-W5b.md L270 | 0522-d11-r5: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19250 2.506 385.0 4.86 2.54 1989 1 | 19250 2.5060 384.99 4.855 2.535 1989 1 | agree | 0.50 |  |
| 462 | pool-W5b.md L270 | 0522-d11-r5: light share | 0.972 | 0.9720 | agree | 0.00 |  |
| 463 | pool-W5b.md L271 | 0524-d11p-r6: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19108 2.529 382.1 4.88 2.37 1901 1 | 19108 2.5290 382.14 4.882 2.373 1901 1 | agree | 0.44 |  |
| 464 | pool-W5b.md L271 | 0524-d11p-r6: light share | 0.973 | 0.9730 | agree | 0.00 |  |
| 465 | pool-W5b.md L272 | 0526-d11-r6: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19260 2.510 385.2 4.81 2.51 1966 1 | 19260 2.5100 385.19 4.807 2.510 1966 1 | agree | 0.30 |  |
| 466 | pool-W5b.md L272 | 0526-d11-r6: light share | 0.973 | 0.9730 | agree | 0.00 |  |
| 467 | pool-W5b.md L273 | 0528-d11t-r6: frames, raw median ms, raw fps, raw p99, cores, eff MHz; kept | 19268 2.519 385.4 4.79 2.37 1965 1 | 19268 2.5190 385.35 4.794 2.366 1965 1 | agree | 0.48 |  |
| 468 | pool-W5b.md L273 | 0528-d11t-r6: light share | 0.975 | 0.9750 | agree | 0.00 |  |
| 469 | pool-W5b.md L226 | W5b light share per arm (mean of results.csv light_share) | 0.974 0.972 0.975 | 0.9745 0.9719 0.9744 / posted run-table light shares: 0.9744 0.9719 0.9745 | agree (posted run-table light shares) | 0.50 | light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share rounded to 3 dp |
| 470 | pool-W5b.md L226 | W5b light share one-way F (df1, df2) | 1.18 (2, 33) | 1.214 2 33 / posted run-table light shares: 1.225 2 33 | DISAGREE | 3.43 | light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share rounded to 3 dp |
| 471 | W9.md L46 | W9 off: planned (+cold), timed, kept, failed | 8 (+2) 8 8 0 | 8 2 8 8 0 | agree | 0.00 |  |
| 472 | W9.md L47 | W9 q0: planned (+cold), timed, kept, failed | 8 8 8 0 | 8 8 8 0 | agree | 0.00 |  |
| 473 | W9.md L48 | W9 q125: planned (+cold), timed, kept, failed | 8 8 8 0 | 8 8 8 0 | agree | 0.00 |  |
| 474 | W9.md L49 | W9 q250: planned (+cold), timed, kept, failed | 8 8 8 0 | 8 8 8 0 | agree | 0.00 |  |
| 475 | W9.md L50 | W9 q500: planned (+cold), timed, kept, failed | 8 8 8 0 | 8 8 8 0 | agree | 0.00 |  |
| 476 | W9.md L99 | W9 raw median ms GM % q0 vs off [CI] | +2.6 [-1.0, +6.2] | 2.57 -0.96 6.22 | agree | 0.39 |  |
| 477 | W9.md L99 | W9 raw median ms GM % q125 vs off [CI] | -1.9 [-5.3, +1.6] | -1.91 -5.28 1.59 | agree | 0.18 |  |
| 478 | W9.md L99 | W9 raw median ms GM % q250 vs off [CI] | -2.1 [-5.5, +1.4] | -2.08 -5.45 1.40 | agree | 0.48 |  |
| 479 | W9.md L99 | W9 raw median ms GM % q500 vs off [CI] | -3.3 [-6.6, +0.1] | -3.32 -6.65 0.12 | agree | 0.48 |  |
| 480 | W9.md L103 | W9 raw fps GM % q0 vs off [CI] | -1.4 [-4.4, +1.6] | -1.41 -4.36 1.63 | agree | 0.43 |  |
| 481 | W9.md L103 | W9 raw fps GM % q125 vs off [CI] | -2.6 [-5.5, +0.4] | -2.58 -5.49 0.42 | agree | 0.24 |  |
| 482 | W9.md L103 | W9 raw fps GM % q250 vs off [CI] | -2.2 [-5.1, +0.8] | -2.18 -5.10 0.83 | agree | 0.33 |  |
| 483 | W9.md L103 | W9 raw fps GM % q500 vs off [CI] | -1.3 [-4.3, +1.7] | -1.33 -4.27 1.71 | agree | 0.26 |  |
| 484 | W9.md L106 | W9 raw p99 ms GM % q0 vs off [CI] | -0.7 [-4.4, +3.1] | -0.73 -4.42 3.10 | agree | 0.32 |  |
| 485 | W9.md L106 | W9 raw p99 ms GM % q125 vs off [CI] | -6.0 [-9.5, -2.3] * | -5.97 -9.46 -2.34 | agree | 0.38 |  |
| 486 | W9.md L106 | W9 raw p99 ms GM % q250 vs off [CI] | -7.1 [-10.6, -3.5] * | -7.13 -10.58 -3.54 | agree | 0.42 |  |
| 487 | W9.md L106 | W9 raw p99 ms GM % q500 vs off [CI] | -6.2 [-9.7, -2.6] * | -6.23 -9.71 -2.61 | agree | 0.26 |  |
| 488 | W9.md L114 | W9 off mean cores | 2.51 | 2.506 | agree | 0.41 |  |
| 489 | W9.md L114 | W9 cores q0: change [CI]; GM % one-way | -0.03 [-0.14, +0.08]; -1.1 % | -0.028 -0.139 0.084 -1.10 | agree | 0.39 |  |
| 490 | W9.md L114 | W9 cores q125: change [CI]; GM % one-way | -0.62 [-0.73, -0.50]; -24.8 %  | -0.616 -0.727 -0.504 -24.80 | agree | 0.44 |  |
| 491 | W9.md L114 | W9 cores q250: change [CI]; GM % one-way | -0.65 [-0.76, -0.53]; -25.9 %  | -0.645 -0.757 -0.533 -25.92 | agree | 0.50 |  |
| 492 | W9.md L114 | W9 cores q500: change [CI]; GM % one-way | -0.75 [-0.86, -0.64]; -30.0 %  | -0.749 -0.861 -0.637 -29.99 | agree | 0.27 |  |
| 493 | W9.md L128 | W9 paired raw median ms q0 vs off: mean +- hw (med; higher k/n) | +2.65 +- 3.70 (med +0.45; 8/8) | 2.648 3.699 0.447 8 8 | agree | 0.30 |  |
| 494 | W9.md L128 | W9 paired raw median ms q125 vs off: mean +- hw (med; higher k/n) | -1.70 +- 5.86 (med -5.70; 3/8) | -1.695 5.860 -5.698 3 8 | agree | 0.47 |  |
| 495 | W9.md L128 | W9 paired raw median ms q250 vs off: mean +- hw (med; higher k/n) | -1.91 +- 5.26 (med -4.55; 2/8) | -1.915 5.259 -4.552 2 8 | agree | 0.50 |  |
| 496 | W9.md L128 | W9 paired raw median ms q500 vs off: mean +- hw (med; higher k/n) | -3.18 +- 4.85 (med -5.86; 1/8) | -3.179 4.848 -5.857 1 8 | agree | 0.31 |  |
| 497 | W9.md L129 | W9 paired raw fps q0 vs off: mean +- hw (med; higher k/n) | -1.37 +- 2.48 (med -0.22; 3/8) | -1.370 2.481 -0.221 3 8 | agree | 0.13 |  |
| 498 | W9.md L129 | W9 paired raw fps q125 vs off: mean +- hw (med; higher k/n) | -2.44 +- 4.64 (med +0.61; 5/8) | -2.435 4.639 0.609 5 8 | agree | 0.46 |  |
| 499 | W9.md L129 | W9 paired raw fps q250 vs off: mean +- hw (med; higher k/n) | -2.06 +- 4.18 (med +0.20; 5/8) | -2.064 4.180 0.200 5 8 | agree | 0.38 |  |
| 500 | W9.md L129 | W9 paired raw fps q500 vs off: mean +- hw (med; higher k/n) | -1.22 +- 4.05 (med +1.03; 6/8) | -1.216 4.053 1.034 6 8 | agree | 0.42 |  |
| 501 | W9.md L132 | W9 paired cores q0 vs off: mean +- hw (med; higher k/n) | -1.09 +- 1.40 (1/8) | -1.090 1.397 1 8 | agree | 0.25 |  |
| 502 | W9.md L132 | W9 paired cores q125 vs off: mean +- hw (med; higher k/n) | -24.51 +- 5.98 (0/8) | -24.514 5.979 0 8 | agree | 0.39 |  |
| 503 | W9.md L132 | W9 paired cores q250 vs off: mean +- hw (med; higher k/n) | -25.70 +- 5.23 (0/8) | -25.703 5.231 0 8 | agree | 0.26 |  |
| 504 | W9.md L132 | W9 paired cores q500 vs off: mean +- hw (med; higher k/n) | -29.90 +- 3.32 (0/8) | -29.902 3.316 0 8 | agree | 0.38 |  |
| 505 | W9.md L142 | W9 tails off: median fps, median p99, p99.9 median / mean, longest frame, frames > 33 ms | 385.5 4.985 5.603 / 6.282 20.63 0 | 385.50 4.9850 5.6025 6.2819 20.630 0 | agree | 0.50 | run agrees |
| 506 | W9.md L143 | W9 tails q0: median fps, median p99, p99.9 median / mean, longest frame, frames > 33 ms | 385.65 4.915 5.594 / 5.698 9.43 0 | 385.631 4.9145 5.5940 5.6978 9.432 0 / rounded inputs: 385.650 4.9150 5.5940 5.6978 9.432 0 | agree (rounded inputs) | 0.25 |  |
| 507 | W9.md L144 | W9 tails q125: median fps, median p99, p99.9 median / mean, longest frame, frames > 33 ms | 389.4 4.498 5.077 / 5.473 23.29 0 | 389.37 4.4975 5.0770 5.4725 23.293 0 | agree | 0.50 | run agrees |
| 508 | W9.md L145 | W9 tails q250: median fps, median p99, p99.9 median / mean, longest frame, frames > 33 ms | 387.7 4.582 5.174 / 5.438 37.29 1 | 387.71 4.5820 5.1740 5.4379 37.293 1 | agree | 0.30 | run agrees |
| 509 | W9.md L146 | W9 tails q500: median fps, median p99, p99.9 median / mean, longest frame, frames > 33 ms | 389.8 4.644 5.427 / 5.449 8.12 0 | 389.80 4.6440 5.4270 5.4489 8.124 0 | agree | 0.40 |  |
| 510 | W9.md L156 | W9 pass 2 q500, off, change: cores (mean of 4 runs) | 1.80 2.4975 -0.70 (-27.9 %) | 1.798 2.49800 -0.700 -28.02 / rounded inputs: 1.800 2.49750 -0.698 -27.93 | agree (rounded inputs) | 0.28 | rounded inputs: 2-dp run cores; the % uses the printed q500 mean |
| 511 | W9.md L157 | W9 pass 2 q500, off, change: fps (median of 4) | 389.25 384.9 +1.1 % | 389.239 384.88 1.13 / rounded inputs: 389.250 384.90 1.13 | agree (rounded inputs) | 0.30 |  |
| 512 | W9.md L158 | W9 pass 2 q500, off, change: p99 ms (median of 4) | 4.675 4.985 -6.2 % | 4.6750 4.9870 -6.26 / rounded inputs: 4.6750 4.9850 -6.22 | agree (rounded inputs) | 0.19 |  |
| 513 | W9.md L159 | W9 pass 2 q500, off, change: p99.9 ms (median of 4) | 5.405 5.579 -3.1 % | 5.4045 5.5790 -3.13 | agree | 0.50 |  |
| 514 | W9.md L198 | 0407-q125-r1: ng_t (audit), eff MHz, cores, frames, fps (vs arm %), raw median ms vs arm % | 4.06 1857 2.15 18250 365.0 (-6.3 %) +7.6 % | 4.059 1857 2.147 18250 364.99 -6.29 7.56 | agree | 0.45 |  |
| 515 | W9.md L199 | 0409-q250-r1: ng_t (audit), eff MHz, cores, frames, fps (vs arm %), raw median ms vs arm % | 3.72 1894 2.11 18909 378.2 (-2.8 %) +5.9 % | 3.719 1894 2.106 18909 378.18 -2.81 5.85 | agree | 0.48 |  |
| 516 | W9.md L200 | 0417-q250-r2: ng_t (audit), eff MHz, cores, frames, fps (vs arm %), raw median ms vs arm % | 2.91 2075 1.93 18958 379.1 (-2.6 %) +2.3 % | 2.912 2075 1.934 18958 379.15 -2.56 2.28 | agree | 0.30 |  |
| 517 | W9.md L201 | 0419-q500-r2: ng_t (audit), eff MHz, cores, frames, fps (vs arm %), raw median ms vs arm % | 3.36 1947 2.03 19291 385.8 (-1.0 %) +2.0 % | 3.363 1947 2.026 19291 385.82 -1.03 1.99 | agree | 0.34 |  |
| 518 | W9.md L202 | 0421-off-r2: ng_t (audit), eff MHz, cores, frames, fps (vs arm %), raw median ms vs arm % | 2.92 1907 2.54 19108 382.2 (-0.9 %) +0.4 % | 2.922 1907 2.545 19108 382.16 -0.95 0.45 | agree | 0.48 |  |
| 519 | W9.md L203 | 0423-q125-r3: ng_t (audit), eff MHz, cores, frames, fps (vs arm %), raw median ms vs arm % | 4.03 1853 2.13 18422 368.4 (-5.4 %) +9.0 % | 4.033 1853 2.133 18422 368.43 -5.41 8.99 | agree | 0.28 |  |
| 520 | W9.md L204 | 0425-q250-r3: ng_t (audit), eff MHz, cores, frames, fps (vs arm %), raw median ms vs arm % | 3.14 1996 1.98 19321 386.4 (-0.7 %) +1.4 % | 3.142 1996 1.981 19321 386.42 -0.69 1.38 | agree | 0.23 |  |
| 521 | W9.md L205 | 0440-q0-r4: ng_t (audit), eff MHz, cores, frames, fps (vs arm %), raw median ms vs arm % | 2.81 1996 2.46 19201 384.0 (-0.5 %) +0.0 % | 2.809 1996 2.460 19201 384.00 -0.47 0.04 | agree | 0.40 |  |
| 522 | W9.md L270 | W9 all 40: n q500 | 8 | 8 | agree | 0.00 |  |
| 523 | W9.md L270 | W9 all 40: q500 raw med GM % [CI] | -3.3 [-6.6, +0.1] | -3.32 -6.65 0.12 | agree | 0.48 |  |
| 524 | W9.md L270 | W9 all 40: q500 raw fps GM % [CI] | -1.3 [-4.3, +1.7] | -1.33 -4.27 1.71 | agree | 0.26 |  |
| 525 | W9.md L270 | W9 all 40: q500 raw p99 GM % [CI] | -6.2 [-9.7, -2.6] * | -6.23 -9.71 -2.61 | agree | 0.26 |  |
| 526 | W9.md L271 | W9 no-flagged (7): n q500 | 7 | 7 | agree | 0.00 |  |
| 527 | W9.md L271 | W9 no-flagged (7): q500 raw med GM % [CI] | -3.6 [-6.8, -0.2] * | -3.55 -6.78 -0.21 | agree | 0.48 |  |
| 528 | W9.md L271 | W9 no-flagged (7): q500 raw fps GM % [CI] | -1.2 [-4.2, +1.9] | -1.20 -4.23 1.93 | agree | 0.30 |  |
| 529 | W9.md L271 | W9 no-flagged (7): q500 raw p99 GM % [CI] | -6.4 [-7.8, -5.1] * | -6.44 -7.80 -5.07 | agree | 0.42 |  |
| 530 | W9.md L272 | W9 no-lowclk (4, Agent 9): n q500 | 7 | 7 | agree | 0.00 |  |
| 531 | W9.md L272 | W9 no-lowclk (4, Agent 9): q500 raw med GM % [CI] | -3.6 [-6.6, -0.4] * | -3.55 -6.64 -0.36 | agree | 0.48 |  |
| 532 | W9.md L272 | W9 no-lowclk (4, Agent 9): q500 raw fps GM % [CI] | -1.2 [-4.1, +1.8] | -1.20 -4.10 1.79 | agree | 0.06 |  |
| 533 | W9.md L272 | W9 no-lowclk (4, Agent 9): q500 raw p99 GM % [CI] | -6.4 [-8.0, -4.9] * | -6.44 -7.98 -4.88 | agree | 0.42 |  |
| 534 | W9.md L273 | W9 no-slow-q (4): n q500 | 8 | 8 | agree | 0.00 |  |
| 535 | W9.md L273 | W9 no-slow-q (4): q500 raw med GM % [CI] | -3.3 [-6.3, -0.2] * | -3.32 -6.31 -0.24 | agree | 0.43 |  |
| 536 | W9.md L273 | W9 no-slow-q (4): q500 raw fps GM % [CI] | -1.3 [-4.1, +1.5] | -1.33 -4.11 1.54 | agree | 0.37 |  |
| 537 | W9.md L273 | W9 no-slow-q (4): q500 raw p99 GM % [CI] | -6.2 [-7.6, -4.9] * | -6.23 -7.58 -4.85 | agree | 0.47 |  |
| 538 | W9.md L274 | W9 drop-p2-r1r3: n q500 | 6 | 6 | agree | 0.00 |  |
| 539 | W9.md L274 | W9 drop-p2-r1r3: q500 raw med GM % [CI] | -3.3 [-7.1, +0.6] | -3.34 -7.11 0.58 | agree | 0.40 |  |
| 540 | W9.md L274 | W9 drop-p2-r1r3: q500 raw fps GM % [CI] | -1.1 [-4.6, +2.5] | -1.13 -4.62 2.50 | agree | 0.25 |  |
| 541 | W9.md L274 | W9 drop-p2-r1r3: q500 raw p99 GM % [CI] | -6.2 [-8.1, -4.3] * | -6.23 -8.13 -4.28 | agree | 0.35 |  |
| 542 | W9.md L275 | W9 drop-r1-both: n q500 | 6 | 6 | agree | 0.00 |  |
| 543 | W9.md L275 | W9 drop-r1-both: q500 raw med GM % [CI] | -5.9 [-7.8, -4.0] * | -5.89 -7.76 -3.98 | agree | 0.38 |  |
| 544 | W9.md L275 | W9 drop-r1-both: q500 raw fps GM % [CI] | +1.2 [-0.2, +2.6] | 1.20 -0.21 2.62 | agree | 0.25 |  |
| 545 | W9.md L275 | W9 drop-r1-both: q500 raw p99 GM % [CI] | -6.8 [-9.7, -3.7] * | -6.77 -9.73 -3.72 | agree | 0.28 |  |
| 546 | W9.md L276 | W9 no-lowclk-no-r1: n q500 | 5 | 5 | agree | 0.00 |  |
| 547 | W9.md L276 | W9 no-lowclk-no-r1: q500 raw med GM % [CI] | -6.2 [-6.9, -5.4] * | -6.17 -6.92 -5.42 | agree | 0.25 |  |
| 548 | W9.md L276 | W9 no-lowclk-no-r1: q500 raw fps GM % [CI] | +1.4 [+0.6, +2.1] * | 1.37 0.61 2.14 | agree | 0.38 |  |
| 549 | W9.md L276 | W9 no-lowclk-no-r1: q500 raw p99 GM % [CI] | -7.0 [-8.5, -5.5] * | -7.02 -8.52 -5.49 | agree | 0.15 |  |
| 550 | W9.md L277 | W9 pass 1 only: n q500 | 4 | 4 | agree | 0.00 |  |
| 551 | W9.md L277 | W9 pass 1 only: q500 raw med GM % [CI] | -2.4 [-8.1, +3.8] | -2.36 -8.13 3.78 | agree | 0.40 |  |
| 552 | W9.md L277 | W9 pass 1 only: q500 raw fps GM % [CI] | -2.2 [-7.4, +3.2] | -2.25 -7.42 3.22 | agree | 0.48 |  |
| 553 | W9.md L277 | W9 pass 1 only: q500 raw p99 GM % [CI] | -6.0 [-8.3, -3.7] * | -6.01 -8.27 -3.69 | agree | 0.27 |  |
| 554 | W9.md L278 | W9 pass 2 only: n q500 | 4 | 4 | agree | 0.00 |  |
| 555 | W9.md L278 | W9 pass 2 only: q500 raw med GM % [CI] | -4.3 [-8.1, -0.3] * | -4.27 -8.11 -0.28 | agree | 0.26 |  |
| 556 | W9.md L278 | W9 pass 2 only: q500 raw fps GM % [CI] | -0.4 [-3.7, +3.0] | -0.39 -3.72 3.04 | agree | 0.43 |  |
| 557 | W9.md L278 | W9 pass 2 only: q500 raw p99 GM % [CI] | -6.4 [-12.5, +0.0] | -6.44 -12.49 0.02 | agree | 0.44 |  |
| 558 | W9.md L284 | W9 all 40: cores change q0 [CI] | -0.03 [-0.14, +0.08] | -0.028 -0.139 0.084 | agree | 0.39 |  |
| 559 | W9.md L284 | W9 all 40: cores change q125 [CI] | -0.62 [-0.73, -0.50] | -0.616 -0.727 -0.504 | agree | 0.42 |  |
| 560 | W9.md L284 | W9 all 40: cores change q250 [CI] | -0.65 [-0.76, -0.53] | -0.645 -0.757 -0.533 | agree | 0.50 |  |
| 561 | W9.md L284 | W9 all 40: cores change q500 [CI] | -0.75 [-0.86, -0.64] | -0.749 -0.861 -0.637 | agree | 0.27 |  |
| 562 | W9.md L284 | W9 all 40: cores q500 - q250 [CI] | -0.104 [-0.216, +0.008] | -0.1040 -0.2157 0.0077 | agree | 0.28 |  |
| 563 | W9.md L284 | W9 all 40: cores q500 - q125 [CI] | -0.133 [-0.245, -0.020] * | -0.1334 -0.2451 -0.0217 / rounded inputs: -0.1325 -0.2445 -0.0205 | agree (rounded inputs) | 0.50 |  |
| 564 | W9.md L285 | W9 no-flagged: cores change q0 [CI] | -0.03 [-0.08, +0.02] | -0.028 -0.079 0.024 | agree | 0.39 |  |
| 565 | W9.md L285 | W9 no-flagged: cores change q125 [CI] | -0.72 [-0.78, -0.66] | -0.716 -0.775 -0.657 / rounded inputs: -0.716 -0.775 -0.658 | DISAGREE | 0.51 |  |
| 566 | W9.md L285 | W9 no-flagged: cores change q250 [CI] | -0.72 [-0.78, -0.66] | -0.718 -0.777 -0.659 | agree | 0.29 |  |
| 567 | W9.md L285 | W9 no-flagged: cores change q500 [CI] | -0.79 [-0.84, -0.73] | -0.787 -0.841 -0.734 | agree | 0.40 |  |
| 568 | W9.md L285 | W9 no-flagged: cores q500 - q250 [CI] | -0.069 [-0.130, -0.009] * | -0.0692 -0.1296 -0.0087 | agree | 0.39 |  |
| 569 | W9.md L285 | W9 no-flagged: cores q500 - q125 [CI] | -0.071 [-0.132, -0.011] * | -0.0714 -0.1318 -0.0109 | agree | 0.37 |  |
| 570 | W9.md L286 | W9 no-lowclk: cores change q0 [CI] | -0.03 [-0.09, +0.03] | -0.028 -0.087 0.032 | agree | 0.26 |  |
| 571 | W9.md L286 | W9 no-lowclk: cores change q125 [CI] | -0.70 [-0.76, -0.63] | -0.699 -0.763 -0.634 | agree | 0.45 |  |
| 572 | W9.md L286 | W9 no-lowclk: cores change q250 [CI] | -0.68 [-0.74, -0.62] | -0.680 -0.742 -0.618 | agree | 0.16 |  |
| 573 | W9.md L286 | W9 no-lowclk: cores change q500 [CI] | -0.79 [-0.85, -0.73] | -0.787 -0.849 -0.726 | agree | 0.34 |  |
| 574 | W9.md L286 | W9 no-lowclk: cores q500 - q250 [CI] | -0.107 [-0.170, -0.044] * | -0.1074 -0.1711 -0.0437 / rounded inputs: -0.1071 -0.1702 -0.0440 | agree (rounded inputs) | 0.25 |  |
| 575 | W9.md L286 | W9 no-lowclk: cores q500 - q125 [CI] | -0.088 [-0.154, -0.022] * | -0.0886 -0.1549 -0.0223 / rounded inputs: -0.0881 -0.1538 -0.0224 | agree (rounded inputs) | 0.42 |  |
| 576 | W9.md L287 | W9 no-slow-q: cores change q0 [CI] | -0.03 [-0.10, +0.05] | -0.028 -0.104 0.049 | agree | 0.43 |  |
| 577 | W9.md L287 | W9 no-slow-q: cores change q125 [CI] | -0.70 [-0.78, -0.62] | -0.699 -0.782 -0.616 | agree | 0.34 |  |
| 578 | W9.md L287 | W9 no-slow-q: cores change q250 [CI] | -0.70 [-0.78, -0.62] | -0.698 -0.781 -0.615 | agree | 0.47 |  |
| 579 | W9.md L287 | W9 no-slow-q: cores change q500 [CI] | -0.75 [-0.83, -0.67] | -0.749 -0.826 -0.672 | agree | 0.44 |  |
| 580 | W9.md L287 | W9 no-slow-q: cores q500 - q250 [CI] | -0.051 [-0.134, +0.032] | -0.0510 -0.1337 0.0318 | agree | 0.17 |  |
| 581 | W9.md L287 | W9 no-slow-q: cores q500 - q125 [CI] | -0.049 [-0.132, +0.034] | -0.0501 -0.1329 0.0326 / rounded inputs: -0.0492 -0.1322 0.0338 | agree (rounded inputs) | 0.17 |  |
| 582 | W9.md L288 | W9 drop-r1-both: cores change q0 [CI] | -0.04 [-0.16, +0.08] | -0.044 -0.163 0.075 / rounded inputs: -0.042 -0.161 0.077 | agree (rounded inputs) | 0.27 |  |
| 583 | W9.md L288 | W9 drop-r1-both: cores change q125 [CI] | -0.66 [-0.78, -0.54] | -0.656 -0.775 -0.537 | agree | 0.43 |  |
| 584 | W9.md L288 | W9 drop-r1-both: cores change q250 [CI] | -0.67 [-0.79, -0.55] | -0.670 -0.789 -0.551 | agree | 0.10 |  |
| 585 | W9.md L288 | W9 drop-r1-both: cores change q500 [CI] | -0.74 [-0.86, -0.63] | -0.745 -0.864 -0.626 | agree | 0.47 |  |
| 586 | W9.md L289 | W9 no-lowclk-no-r1: cores change q0 [CI] | -0.04 [-0.12, +0.03] | -0.044 -0.116 0.028 | agree | 0.42 |  |
| 587 | W9.md L289 | W9 no-lowclk-no-r1: cores change q125 [CI] | -0.71 [-0.79, -0.64] | -0.711 -0.786 -0.636 | agree | 0.43 |  |
| 588 | W9.md L289 | W9 no-lowclk-no-r1: cores change q250 [CI] | -0.67 [-0.74, -0.60] | -0.670 -0.742 -0.599 | agree | 0.12 |  |
| 589 | W9.md L289 | W9 no-lowclk-no-r1: cores change q500 [CI] | -0.80 [-0.87, -0.72] | -0.796 -0.871 -0.720 | agree | 0.43 |  |
| 590 | W9.md L290 | W9 pass 1 only: cores change q0 [CI] | -0.02 [-0.10, +0.06] | -0.024 -0.104 0.056 | agree | 0.44 |  |
| 591 | W9.md L290 | W9 pass 1 only: cores change q125 [CI] | -0.69 [-0.77, -0.61] | -0.690 -0.770 -0.609 | agree | 0.00 |  |
| 592 | W9.md L290 | W9 pass 1 only: cores change q250 [CI] | -0.74 [-0.82, -0.66] | -0.744 -0.825 -0.664 | agree | 0.49 |  |
| 593 | W9.md L290 | W9 pass 1 only: cores change q500 [CI] | -0.80 [-0.88, -0.72] | -0.798 -0.878 -0.718 | agree | 0.00 |  |
| 594 | W9.md L291 | W9 pass 2 only: cores change q0 [CI] | -0.03 [-0.23, +0.17] | -0.032 -0.231 0.168 | agree | 0.13 |  |
| 595 | W9.md L291 | W9 pass 2 only: cores change q125 [CI] | -0.54 [-0.74, -0.34] | -0.542 -0.741 -0.342 | agree | 0.17 |  |
| 596 | W9.md L291 | W9 pass 2 only: cores change q250 [CI] | -0.55 [-0.75, -0.35] | -0.546 -0.745 -0.346 | agree | 0.47 |  |
| 597 | W9.md L291 | W9 pass 2 only: cores change q500 [CI] | -0.70 [-0.90, -0.50] | -0.700 -0.900 -0.500 | agree | 0.02 |  |
| 598 | W9.md L35 | q500 cores change [CI], GM % | -0.75 core [-0.86, -0.64], -30.0 % | -0.749 -0.861 -0.637 -29.99 | agree | 0.27 |  |
| 599 | W9.md L35 | no-flagged q500 cores change [CI] | -0.79 core [-0.84, -0.73] | -0.787 -0.841 -0.734 | agree | 0.40 |  |
| 600 | W9.md L36 | pass 2 q500 vs off: cores change, cores %, fps (medians) %, p99 median q500, off | -0.70 core (-27.9 %), fps +1.1 %, p99 4.675 vs 4.985 ms | -0.700 -28.02 1.13 4.6750 4.9870 / rounded inputs: -0.698 -27.93 1.13 4.6750 4.9850 | agree (rounded inputs) | 0.30 |  |
| 601 | W9.md L37 | q0 cores change [CI] | -0.03 core [-0.14, +0.08] | -0.028 -0.139 0.084 | agree | 0.39 |  |
| 602 | W9.md L37 | q0 raw median ms higher than off in k of n rounds | 8 of 8 | 8 8 | agree | 0.00 |  |
| 603 | W9.md L38 | ng_t range of the 6 loaded q runs (audit win_ngB_mean) | 2.91 to 4.06 | 2.912 4.059 | agree | 0.18 |  |
| 604 | W9.md L38 | no-flagged cores change q125, q250, q500 | -0.72, -0.72, -0.79 | -0.716 -0.718 -0.787 | agree | 0.39 |  |
| 605 | W9.md L52 | cold runs left out | 2 | 2 | agree | 0.00 |  |
| 606 | W9.md L78 | light share per arm (mean of light_share) | 0.968 0.970 0.983 0.986 0.984 | 0.9682 0.9699 0.9830 0.9859 0.9840 | agree | 0.25 |  |
| 607 | W9.md L78 | light share one-way F (df1, df2) | 9.38 (4, 35) | 9.679 4 35 / posted run-table light shares: 9.797 4 35 | DISAGREE | 29.86 | light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share rounded to 3 dp |
| 608 | W9.md L85 | 0110-off-r1 fps (frames), 0112-q0-r1 fps, 0114-q125-r1 fps | 443.7 (22187), 414.6, 395.5 | 443.73 22187 414.57 395.50 | agree | 0.32 |  |
| 609 | W9.md L86 | 0403-off-r1 fps | 408.9 | 408.91 | agree | 0.10 |  |
| 610 | W9.md L87 | fps range of the other 6 off runs | 382.2 to 386.6 | 382.16 386.60 | agree | 0.40 |  |
| 611 | W9.md L88 | 0110-off-r1 light share vs the other 7 off runs (range) | 0.982 vs 0.962 to 0.974 | 0.9820 0.9620 0.9740 | agree | 0.00 |  |
| 612 | W9.md L88 | 0110-off-r1 eff MHz; other 7 off runs eff range | 1992; 1907 to 2027 | 1992 1907 2027 | agree | 0.00 |  |
| 613 | W9.md L135 | q500 vs off without each pass r1, raw fps: higher k of n; min, max, mean %; sign p | 6 of 6 (+0.91 to +1.64 %, mean +1.19 %, sign p 0.031) | 6 6 0.899 1.650 1.196 0.0312 / rounded inputs: 6 6 0.905 1.644 1.192 0.0312 | agree (rounded inputs) | 0.47 |  |
| 614 | W9.md L135 | q500 vs off without r1, raw median ms: lower k of n; range % | lower in 6 of 6 (-4.58 to -6.76 %) | 6 6 -4.577 -6.755 | agree | 0.49 |  |
| 615 | W9.md L136 | without r1, raw fps higher: q125 k of n, q250 k of n; misses 0423-q125-r3 %, 0417-q250-r2 % | 5 of 6, 5 of 6; -4.36 %; -0.81 % | 5 6 5 6 -4.350 -0.788 / rounded inputs: 5 6 5 6 -4.361 -0.811 | agree (rounded inputs) | 0.14 |  |
| 616 | W9.md L162 | q500 cores change [CI] | -0.75 [-0.86, -0.64] | -0.749 -0.861 -0.637 | agree | 0.27 |  |
| 617 | W9.md L163 | q500 raw p99 GM % [CI] | -6.2 % [-9.7, -2.6] | -6.23 -9.71 -2.61 | agree | 0.26 |  |
| 618 | W9.md L164 | q500 paired raw fps without r1: mean %, higher k of n | +1.19 % (6 of 6) | 1.196 6 6 / rounded inputs: 1.192 6 6 | agree (rounded inputs) | 0.21 |  |
| 619 | W9.md L166 | q500 pooled raw fps GM % [CI] | -1.3 % [-4.3, +1.7] | -1.33 -4.27 1.71 | agree | 0.26 |  |
| 620 | W9.md L171 | q0 cores change [CI] (GM % [CI]) | -0.03 [-0.14, +0.08] (-1.1 % [-6.7, +4.8]) | -0.028 -0.139 0.084 -1.10 -6.70 4.83 | agree | 0.39 |  |
| 621 | W9.md L171 | q0 paired cores: lower in k of n rounds; mean +- hw % | 7 of 8; -1.09 +- 1.40 % | 7 8 -1.090 1.397 | agree | 0.25 |  |
| 622 | W9.md L174 | q0 raw median ms higher in k of n rounds (sign p) | 8 of 8 (sign p 0.008) | 8 8 0.0078 | agree | 0.19 |  |
| 623 | W9.md L175 | q0 without r1: higher k of n (p); raw range %; mean % | 6 of 6 (p 0.031): +0.12 to +1.31 % (mean +0.45 %) | 6 6 0.0312 0.121 1.306 0.454 | agree | 0.44 |  |
| 624 | W9.md L179 | q0 raw fps GM %, raw p99 GM % | -1.4, -0.7 | -1.41 -0.73 | agree | 0.32 |  |
| 625 | W9.md L180 | light share q0 vs off | 0.970 vs 0.968 | 0.9699 0.9682 | agree | 0.25 |  |
| 626 | W9.md L185 | q125 r1/r3 (0407, 0423) cores range, mean frames (k); q250 0409/0417 mean frames (k) | 2.13 to 2.15 cores, ~18.3k; ~18.9k | 2.133 2.147 18.34 18.93 | agree | 0.36 |  |
| 627 | W9.md L207 | 0411-q500-r1, 0413-q0-r2, 0415-q125-r2: ng_t range; fps each | 2.28 to 2.36; 388.7 / 385.1 / 391.0 | 2.282 2.361 388.69 385.15 390.97 | agree | 0.48 |  |
| 628 | W9.md L208 | pass-2 kept runs from 04:28 on with ng_t >= 2.8: count; ng_t of 0440-q0-r4 | 1; 2.81 | 1 2.809 | agree | 0.11 | runs: 0440-q0-r4 |
| 629 | W9.md L209 | pass 1: runs with ng_t >= 2.8, ng_t range; pass-2 quiet median ng_t | 0 (range 2.16 to 2.77); 2.33 | 0 2.164 2.768 2.334 | agree | 0.43 |  |
| 630 | W9.md L211 | q125's other 6 runs: fps range, cores range | 387.8 to 395.5 fps at 1.73 to 1.89 cores | 387.75 395.50 1.728 1.893 | agree | 0.46 |  |
| 631 | W9.md L212 | q250's quiet runs: n; fps range, cores range | 5 quiet runs: 386.1 to 389.9 fps at 1.71 to 1.91 cores | 5 386.12 389.91 1.709 1.909 | agree | 0.16 |  |
| 632 | W9.md L219 | quiet q125-q500 runs eff range vs quiet off runs eff range | 2108 to 2228 vs 1951 to 2027 | 2108 2228 1951 2027 | agree | 0.00 |  |
| 633 | W9.md L220 | 6 loaded q runs: eff range; eff vs arm quiet median, % range | 1853 to 2075 MHz (-4 to -15 %) | 1853 2075 -4.4 -14.6 | agree | 0.42 |  |
| 634 | W9.md L221 | 0421-off-r2: eff vs off quiet median %, eff | -3 % (1907 MHz) | -3.0 1907 | agree | 0.00 |  |
| 635 | W9.md L235 | 6 loaded q runs: cores minus arm quiet median, range | +0.20 to +0.38 | 0.202 0.374 / rounded inputs: 0.200 0.380 | agree (rounded inputs) | 0.00 |  |
| 636 | W9.md L236 | 6 loaded q runs: cores at constant core x MHz, range | 1.81 to 2.11 | 1.812 2.113 | agree | 0.33 |  |
| 637 | W9.md L237 | 6 loaded q runs: rest, range | +0.02 to +0.13 | 0.020 0.122 / rounded inputs: 0.017 0.127 | agree (rounded inputs) | 0.33 |  |
| 638 | W9.md L239 | 0421-off-r2 ng_t, fps vs arm %; 0440-q0-r4 ng_t, fps vs arm % | 2.92: -0.9 %; 2.81: -0.5 % | 2.922 -0.95 2.809 -0.47 | agree | 0.33 |  |
| 639 | W9.md L241 | q runs at ng_t 2.9-3.4: fps vs arm % range | -0.7 to -2.6 % | -0.69 -2.56 | agree | 0.30 |  |
| 640 | W9.md L242 | q runs at ng_t 3.7-4.1: fps vs arm % range; raw median ms vs arm % range | -2.8 to -6.3 % (raw median ms +5.9 to +9.0 %) | -2.81 -6.29 5.85 8.99 | agree | 0.48 |  |
| 641 | W9.md L249 | three longest frames of the kept runs, ms | 37.29; 23.29; 20.63 | 37.293 23.293 20.630 | agree | 0.30 | runs: 0409-q250-r1, 0407-q125-r1, 0421-off-r2 (posted: 0409-q250-r1, 0407-q125-r1, 0421-off-r2) |
| 642 | W9.md L255 | first four scored W5b-2 runs (04:54-05:02): ng_t range | 2.84-3.76 | 2.838 3.757 | agree | 0.26 | runs: 0453-d11-r1, 0455-d11t-r1, 0457-d11p-r1, 0459-d11t-r2 |
| 643 | W9.md L305 | no-flagged raw p99 GM %: q125 vs q500 | -9.8 vs -6.4 | -9.77 -6.44 | agree | 0.42 |  |
| 644 | W9.md L311 | q500 has the largest cores drop in k of the n subsets of the section 7 table | 8 of 8 | 8 8 | agree | 0.00 |  |
| 645 | W9.md L313 | quiet rounds: raw fps GM % (drop-r1-both, no-lowclk-no-r1); raw median ms GM % (same) | +1.2 to +1.4 %; -5.9 to -6.2 % | 1.20 1.37 -5.89 -6.17 | agree | 0.30 |  |
| 646 | W9.md L314 | no-flagged q500 - q125 cores [CI] | -0.071 [-0.132, -0.011] | -0.0714 -0.1318 -0.0109 | agree | 0.37 |  |
| 647 | W9.md L120 | cores q500 - q250 [CI] | -0.104 [-0.216, +0.008] | -0.1040 -0.2157 0.0077 | agree | 0.28 |  |
| 648 | W9.md L121 | cores q500 - q125 [CI] | -0.133 [-0.245, -0.020] | -0.1334 -0.2451 -0.0217 / rounded inputs: -0.1325 -0.2445 -0.0205 | agree (rounded inputs) | 0.50 |  |
| 649 | W9.md L122 | cores q250 - q125 [CI] | -0.029 [-0.141, +0.083] | -0.0294 -0.1411 0.0823 / rounded inputs: -0.0288 -0.1408 0.0833 | agree (rounded inputs) | 0.28 |  |
| 650 | W9.md L259 | no-flagged cores change q125, q250, q500 ("-0.72 each vs -0.79") | -0.72, -0.72, -0.79 | -0.716 -0.718 -0.787 | agree | 0.38 |  |
| 651 | W9.md L302 | q500's extra saving over q250, range over the 4 pools with that column (section 7) | 0.05-0.11 | 0.051 0.107 | agree | 0.26 |  |
| 652 | W5b.md L53 | W5b d11: planned (+cold), timed, kept, failed | 12 (+2) 12 12 0 | 12 2 12 12 0 | agree | 0.00 |  |
| 653 | W5b.md L54 | W5b d11t: planned (+cold), timed, kept, failed | 12 12 12 0 | 12 12 12 0 | agree | 0.00 |  |
| 654 | W5b.md L55 | W5b d11p: planned (+cold), timed, kept, failed | 12 12 12 0 | 12 12 12 0 | agree | 0.00 |  |
| 655 | W5b.md L99 | W5b raw median ms GM % d11t vs d11 [CI] | +1.3 [-0.8, +3.4] | 1.32 -0.76 3.43 | agree | 0.43 |  |
| 656 | W5b.md L99 | W5b raw median ms GM % d11p vs d11 [CI] | +0.5 [-1.5, +2.6] | 0.51 -1.55 2.61 | agree | 0.47 |  |
| 657 | W5b.md L102 | W5b raw fps GM % d11t vs d11 [CI] | -1.3 [-3.0, +0.4] | -1.30 -2.97 0.41 | agree | 0.25 |  |
| 658 | W5b.md L102 | W5b raw fps GM % d11p vs d11 [CI] | -0.7 [-2.4, +1.0] | -0.73 -2.42 0.98 | agree | 0.35 |  |
| 659 | W5b.md L105 | W5b raw p99 ms GM % d11t vs d11 [CI] | +1.2 [-0.6, +2.9] | 1.15 -0.58 2.91 | agree | 0.47 |  |
| 660 | W5b.md L105 | W5b raw p99 ms GM % d11p vs d11 [CI] | +0.1 [-1.6, +1.8] | 0.06 -1.65 1.81 | agree | 0.46 |  |
| 661 | W5b.md L114 | W5b d11 mean cores | 2.55 | 2.549 | agree | 0.12 |  |
| 662 | W5b.md L114 | W5b cores d11t: mean; change [CI]; GM % one-way | 2.33; -0.22 [-0.25, -0.19]; -8.6 %  | 2.329 -0.220 -0.251 -0.189 -8.63 | agree | 0.30 |  |
| 663 | W5b.md L114 | W5b cores d11p: mean; change [CI]; GM % one-way | 2.34; -0.20 [-0.23, -0.17]; -8.0 %  | 2.345 -0.204 -0.235 -0.173 -8.00 | agree | 0.49 |  |
| 664 | W5b.md L126 | W5b paired raw median ms d11t vs d11: mean +- hw (med; higher k/n) | +1.33 +- 1.31 (med +0.46; 11/12) | 1.334 1.305 0.459 11 12 | agree | 0.49 |  |
| 665 | W5b.md L126 | W5b paired raw median ms d11p vs d11: mean +- hw (med; higher k/n) | +0.53 +- 1.38 (med -0.38; 5/12) | 0.529 1.381 -0.377 5 12 | agree | 0.28 |  |
| 666 | W5b.md L127 | W5b paired raw fps d11t vs d11: mean +- hw (med; higher k/n) | -1.28 +- 1.24 (med -0.47; 3/12) | -1.278 1.239 -0.468 3 12 | agree | 0.19 |  |
| 667 | W5b.md L127 | W5b paired raw fps d11p vs d11: mean +- hw (med; higher k/n) | -0.72 +- 0.96 (med +0.04; 7/12) | -0.724 0.956 0.040 7 12 | agree | 0.42 |  |
| 668 | W5b.md L130 | W5b paired cores d11t vs d11: mean +- hw (med; higher k/n) | -8.62 +- 1.05 (med -8.90; 0/12) | -8.617 1.045 -8.901 0 12 | agree | 0.46 |  |
| 669 | W5b.md L130 | W5b paired cores d11p vs d11: mean +- hw (med; higher k/n) | -7.98 +- 1.16 (med -8.54; 0/12) | -7.983 1.159 -8.538 0 12 | agree | 0.29 |  |
| 670 | W5b.md L142 | W5b tails d11: p99.9 median / mean, runs with a frame > 8 ms (max_ms), longest frame, frames > 33 ms | 5.390 / 5.429 2 10.27 0 | 5.3905 5.4291 2 10.272 0 | agree | 0.50 | run agrees |
| 671 | W5b.md L143 | W5b tails d11t: p99.9 median / mean, runs with a frame > 8 ms (max_ms), longest frame, frames > 33 ms | 5.479 / 6.088 3 26.37 0 | 5.4785 6.0882 3 26.366 0 | agree | 0.50 | run agrees |
| 672 | W5b.md L144 | W5b tails d11p: p99.9 median / mean, runs with a frame > 8 ms (max_ms), longest frame, frames > 33 ms | 5.429 / 5.450 4 11.56 0 | 5.4290 5.4502 4 11.562 0 | agree | 0.20 | run agrees |
| 673 | W5b.md L156 | W5b pass 2 mean cores: d11; d11t (change); d11p (change) | 2.5585 2.347 (-0.2115) 2.354 (-0.2045) | 2.55850 2.3470 -0.21150 2.3540 -0.20450 | agree | 0.00 |  |
| 674 | W5b.md L157 | W5b pass 2 median fps: d11; d11t (% vs d11); d11p (% vs d11) | 385.18 382.0 (-0.83 %) 385.45 (+0.07 %) | 385.182 382.00 -0.825 385.450 0.070 | agree | 0.47 |  |
| 675 | W5b.md L158 | W5b pass 2 median of the run median ms: d11, d11t, d11p | 2.51 2.52 2.51 | 2.511 2.524 2.510 | agree | 0.40 |  |
| 676 | W5b.md L159 | W5b pass 2 runner's d median %, d p99 % (medians of the run values): d11t, d11p | +0.5 / +0.4 % -0.1 / +0.6 % | 0.52 0.37 -0.06 0.57 | agree | 0.40 |  |
| 677 | W5b.md L179 | W5b d11 quiet runs (ng_t < 2.8): n, median fps, raw ms, cores, eff MHz | 11 385.1 2.512 2.540 1957 | 11 385.08 2.5120 2.5430 1957 / rounded inputs: 11 385.10 2.5120 2.5400 1957 | agree (rounded inputs) | 0.00 |  |
| 678 | W5b.md L180 | W5b d11t quiet runs (ng_t < 2.8): n, median fps, raw ms, cores, eff MHz | 8 385.2 2.518 2.300 1966 | 8 385.24 2.5185 2.3040 1966 / rounded inputs: 8 385.25 2.5185 2.3000 1966 | agree (rounded inputs) | 0.50 |  |
| 679 | W5b.md L181 | W5b d11p quiet runs (ng_t < 2.8): n, median fps, raw ms, cores, eff MHz | 8 385.4 2.502 2.325 1948 | 8 385.45 2.5020 2.3250 1948 | agree | 0.50 |  |
| 680 | W5b.md L195 | W5b loaded 0457-d11p-r1: pass, ng, eff, effp, fps, fpsp, ms, msp, cores, coresd, rest | 2 3.76 1780 (-8.6 %) 386.0 (+0.1 %) 2.457 (-1.8 %) 2.37 (+0.04) -0.17 | 2 3.757 1780 -8.62 386.03 0.15 2.4570 -1.80 2.368 0.043 -0.176 / rounded inputs: 2 3.757 1780 -8.62 386.00 0.14 2.4570 -1.80 2.370 0.045 -0.174 | agree (rounded inputs) | 0.50 |  |
| 681 | W5b.md L196 | W5b loaded 0453-d11-r1: pass, ng, eff, effp, fps, fpsp, ms, msp, cores, coresd | 2 3.53 1848 (-5.6 %) 393.0 (+2.1 %) 2.483 (-1.2 %) 2.60 (+0.06) | 2 3.527 1848 -5.57 392.97 2.05 2.4830 -1.15 2.602 0.059 / rounded inputs: 2 3.527 1848 -5.57 393.00 2.05 2.4830 -1.15 2.600 0.060 | agree (rounded inputs) | 0.49 |  |
| 682 | W5b.md L197 | W5b loaded 0455-d11t-r1: pass, ng, eff, effp, fps, fpsp, ms, msp, cores, coresd, rest | 2 3.37 1873 (-4.7 %) 367.1 (-4.7 %) 2.647 (+5.1 %) 2.37 (+0.07) -0.04 | 2 3.373 1873 -4.73 367.13 -4.70 2.6470 5.10 2.365 0.061 -0.053 / rounded inputs: 2 3.373 1873 -4.73 367.10 -4.71 2.6470 5.10 2.370 0.070 -0.044 | agree (rounded inputs) | 0.42 |  |
| 683 | W5b.md L198 | W5b loaded 0213-d11t-r3: pass, ng, eff, effp, fps, fpsp, ms, msp, cores, coresd, rest | 1 3.36 1829 (-7.0 %) 371.7 (-3.5 %) 2.606 (+3.5 %) 2.39 (+0.09) -0.08 | 1 3.362 1829 -6.97 371.75 -3.50 2.6060 3.47 2.386 0.082 -0.091 / rounded inputs: 1 3.362 1829 -6.97 371.70 -3.52 2.6060 3.47 2.390 0.090 -0.082 | agree (rounded inputs) | 0.32 |  |
| 684 | W5b.md L199 | W5b loaded 0209-d11p-r3: pass, ng, eff, effp, fps, fpsp, ms, msp, cores, coresd, rest | 1 3.07 1854 (-4.8 %) 381.8 (-0.9 %) 2.544 (+1.7 %) 2.37 (+0.04) -0.07 | 1 3.066 1854 -4.83 381.80 -0.95 2.5440 1.68 2.372 0.047 -0.071 / rounded inputs: 1 3.066 1854 -4.83 381.80 -0.95 2.5440 1.68 2.370 0.045 -0.073 | agree (rounded inputs) | 0.50 |  |
| 685 | W5b.md L200 | W5b loaded 0520-d11p-r5: pass, ng, eff, effp, fps, fpsp, ms, msp, cores, coresd, rest | 2 2.90 1906 (-2.2 %) 375.6 (-2.6 %) 2.586 (+3.4 %) 2.38 (+0.05) +0.00 | 2 2.897 1906 -2.16 375.55 -2.57 2.5860 3.36 2.375 0.050 -0.001 | agree | 0.50 |  |
| 686 | W5b.md L201 | W5b loaded 0524-d11p-r6: pass, ng, eff, effp, fps, fpsp, ms, msp, cores, coresd, rest | 2 2.88 1901 (-2.4 %) 382.1 (-0.9 %) 2.529 (+1.1 %) 2.37 (+0.04) -0.01 | 2 2.877 1901 -2.41 382.14 -0.86 2.5290 1.08 2.373 0.048 -0.009 / rounded inputs: 2 2.877 1901 -2.41 382.10 -0.87 2.5290 1.08 2.370 0.045 -0.012 | agree (rounded inputs) | 0.50 |  |
| 687 | W5b.md L202 | W5b loaded 0510-d11t-r3: pass, ng, eff, effp, fps, fpsp, ms, msp, cores, coresd, rest | 2 2.87 1916 (-2.5 %) 379.3 (-1.5 %) 2.528 (+0.4 %) 2.31 (+0.01) -0.05 | 2 2.874 1916 -2.54 379.29 -1.55 2.5280 0.38 2.311 0.007 -0.053 | agree | 0.45 |  |
| 688 | W5b.md L203 | W5b loaded 0459-d11t-r2: pass, ng, eff, effp, fps, fpsp, ms, msp, cores, coresd, rest | 2 2.84 1937 (-1.5 %) 376.6 (-2.2 %) 2.582 (+2.5 %) 2.34 (+0.04) +0.01 | 2 2.838 1937 -1.48 376.63 -2.23 2.5820 2.52 2.339 0.035 0.001 / rounded inputs: 2 2.838 1937 -1.48 376.60 -2.25 2.5820 2.52 2.340 0.040 0.006 | agree (rounded inputs) | 0.45 |  |
| 689 | W5b.md L238 | W5b all 36: n d11t | 12 | 12 | agree | 0.00 |  |
| 690 | W5b.md L238 | W5b all 36: d11t raw med GM % [CI] | +1.3 [-0.8, +3.4] | 1.32 -0.76 3.43 | agree | 0.43 |  |
| 691 | W5b.md L238 | W5b all 36: d11t raw fps GM % [CI] | -1.3 [-3.0, +0.4] | -1.30 -2.97 0.41 | agree | 0.25 |  |
| 692 | W5b.md L238 | W5b all 36: d11t cores change [CI] | -0.22 [-0.25, -0.19] | -0.220 -0.251 -0.189 | agree | 0.10 |  |
| 693 | W5b.md L239 | W5b no-flagged: runs left out | 7 | 7 | agree | 0.00 |  |
| 694 | W5b.md L239 | W5b no-flagged: n d11t | 8 | 8 | agree | 0.00 |  |
| 695 | W5b.md L239 | W5b no-flagged: d11t raw med GM % [CI] | +0.0 [-2.3, +2.3] | 0.01 -2.25 2.32 | DISAGREE | 0.52 |  |
| 696 | W5b.md L239 | W5b no-flagged: d11t raw fps GM % [CI] | +0.0 [-1.8, +1.9] | 0.01 -1.82 1.88 | agree | 0.20 |  |
| 697 | W5b.md L239 | W5b no-flagged: d11t cores change [CI] | -0.23 [-0.26, -0.19] | -0.226 -0.261 -0.191 | agree | 0.39 |  |
| 698 | W5b.md L240 | W5b no-loaded: runs left out | 9 | 9 | agree | 0.00 |  |
| 699 | W5b.md L240 | W5b no-loaded: n d11t | 8 | 8 | agree | 0.00 |  |
| 700 | W5b.md L240 | W5b no-loaded: d11t raw med GM % [CI] | +0.0 [-2.3, +2.4] | 0.01 -2.25 2.33 | DISAGREE | 0.75 |  |
| 701 | W5b.md L240 | W5b no-loaded: d11t raw fps GM % [CI] | +0.0 [-1.8, +1.9] | 0.01 -1.82 1.88 | agree | 0.21 |  |
| 702 | W5b.md L240 | W5b no-loaded: d11t cores change [CI] | -0.23 [-0.26, -0.19] | -0.226 -0.261 -0.191 | agree | 0.39 |  |
| 703 | W5b.md L241 | W5b no-audit-flag: runs left out | 6 | 6 | agree | 0.00 |  |
| 704 | W5b.md L241 | W5b no-audit-flag: n d11t | 9 | 9 | agree | 0.00 |  |
| 705 | W5b.md L241 | W5b no-audit-flag: d11t raw med GM % [CI] | +0.4 [-1.8, +2.7] | 0.40 -1.83 2.67 | agree | 0.29 |  |
| 706 | W5b.md L241 | W5b no-audit-flag: d11t raw fps GM % [CI] | -0.3 [-2.1, +1.5] | -0.30 -2.09 1.53 | agree | 0.27 |  |
| 707 | W5b.md L241 | W5b no-audit-flag: d11t cores change [CI] | -0.22 [-0.26, -0.19] | -0.224 -0.257 -0.190 | agree | 0.36 |  |
| 708 | W5b.md L242 | W5b no-slow-d11t: runs left out | 2 | 2 | agree | 0.00 |  |
| 709 | W5b.md L242 | W5b no-slow-d11t: n d11t | 10 | 10 | agree | 0.00 |  |
| 710 | W5b.md L242 | W5b no-slow-d11t: d11t raw med GM % [CI] | +0.6 [-1.4, +2.7] | 0.62 -1.43 2.72 | agree | 0.32 |  |
| 711 | W5b.md L242 | W5b no-slow-d11t: d11t raw fps GM % [CI] | -0.7 [-2.4, +1.0] | -0.73 -2.40 0.98 | agree | 0.25 |  |
| 712 | W5b.md L242 | W5b no-slow-d11t: d11t cores change [CI] | -0.22 [-0.26, -0.19] | -0.225 -0.258 -0.192 | agree | 0.43 |  |
| 713 | W5b.md L243 | W5b no-0221: runs left out | 1 | 1 | agree | 0.00 |  |
| 714 | W5b.md L243 | W5b no-0221: n d11t | 11 | 11 | agree | 0.00 |  |
| 715 | W5b.md L243 | W5b no-0221: d11t raw med GM % [CI] | +1.4 [-0.7, +3.6] | 1.42 -0.73 3.61 | agree | 0.30 |  |
| 716 | W5b.md L243 | W5b no-0221: d11t raw fps GM % [CI] | -1.3 [-3.0, +0.5] | -1.29 -3.03 0.49 | agree | 0.32 |  |
| 717 | W5b.md L243 | W5b no-0221: d11t cores change [CI] | -0.22 [-0.25, -0.19] | -0.219 -0.251 -0.187 | agree | 0.34 |  |
| 718 | W5b.md L244 | W5b no-p2-first3: runs left out | 3 | 3 | agree | 0.00 |  |
| 719 | W5b.md L244 | W5b no-p2-first3: n d11t | 11 | 11 | agree | 0.00 |  |
| 720 | W5b.md L244 | W5b no-p2-first3: d11t raw med GM % [CI] | +0.8 [-1.3, +3.0] | 0.85 -1.26 3.00 | agree | 0.48 |  |
| 721 | W5b.md L244 | W5b no-p2-first3: d11t raw fps GM % [CI] | -0.8 [-2.5, +0.9] | -0.80 -2.51 0.94 | agree | 0.39 |  |
| 722 | W5b.md L244 | W5b no-p2-first3: d11t cores change [CI] | -0.22 [-0.25, -0.19] | -0.218 -0.251 -0.186 | agree | 0.37 |  |
| 723 | W5b.md L245 | W5b drop-p2-r1r2: n d11t | 10 | 10 | agree | 0.00 |  |
| 724 | W5b.md L245 | W5b drop-p2-r1r2: d11t raw med GM % [CI] | +0.7 [-1.6, +3.0] | 0.66 -1.62 2.98 | agree | 0.44 |  |
| 725 | W5b.md L245 | W5b drop-p2-r1r2: d11t raw fps GM % [CI] | -0.7 [-2.5, +1.2] | -0.66 -2.52 1.24 | agree | 0.41 |  |
| 726 | W5b.md L245 | W5b drop-p2-r1r2: d11t cores change [CI] | -0.22 [-0.25, -0.19] | -0.220 -0.253 -0.186 | agree | 0.36 |  |
| 727 | W5b.md L246 | W5b drop-r1-both: n d11t | 10 | 10 | agree | 0.00 |  |
| 728 | W5b.md L246 | W5b drop-r1-both: d11t raw med GM % [CI] | +0.7 [-0.3, +1.7] | 0.68 -0.31 1.67 | agree | 0.26 |  |
| 729 | W5b.md L246 | W5b drop-r1-both: d11t raw fps GM % [CI] | -0.7 [-1.5, +0.1] | -0.69 -1.49 0.12 | agree | 0.24 |  |
| 730 | W5b.md L246 | W5b drop-r1-both: d11t cores change [CI] | -0.22 [-0.25, -0.19] | -0.224 -0.255 -0.193 | agree | 0.47 |  |
| 731 | W5b.md L247 | W5b pass 1 only: n d11t | 6 | 6 | agree | 0.00 |  |
| 732 | W5b.md L247 | W5b pass 1 only: d11t raw med GM % [CI] | +0.9 [-3.0, +4.9] | 0.89 -2.96 4.89 | agree | 0.40 |  |
| 733 | W5b.md L247 | W5b pass 1 only: d11t raw fps GM % [CI] | -0.9 [-4.0, +2.4] | -0.86 -4.00 2.38 | agree | 0.40 |  |
| 734 | W5b.md L247 | W5b pass 1 only: d11t cores change [CI] | -0.23 [-0.28, -0.18] | -0.229 -0.277 -0.180 | agree | 0.26 |  |
| 735 | W5b.md L248 | W5b pass 2 only: n d11t | 6 | 6 | agree | 0.00 |  |
| 736 | W5b.md L248 | W5b pass 2 only: d11t raw med GM % [CI] | +1.7 [-0.2, +3.7] | 1.74 -0.18 3.71 | agree | 0.44 |  |
| 737 | W5b.md L248 | W5b pass 2 only: d11t raw fps GM % [CI] | -1.7 [-3.4, -0.1] * | -1.73 -3.36 -0.08 | agree | 0.41 |  |
| 738 | W5b.md L248 | W5b pass 2 only: d11t cores change [CI] | -0.21 [-0.25, -0.17] | -0.212 -0.252 -0.171 | agree | 0.20 |  |
| 739 | W5b.md L254 | W5b all 36: n d11p | 12 | 12 | agree | 0.00 |  |
| 740 | W5b.md L254 | W5b all 36: d11p raw med GM % [CI] | +0.5 [-1.5, +2.6] | 0.51 -1.55 2.61 | agree | 0.47 |  |
| 741 | W5b.md L254 | W5b all 36: d11p raw fps GM % [CI] | -0.7 [-2.4, +1.0] | -0.73 -2.42 0.98 | agree | 0.35 |  |
| 742 | W5b.md L254 | W5b all 36: d11p cores change [CI] | -0.20 [-0.23, -0.17] | -0.204 -0.235 -0.173 | agree | 0.49 |  |
| 743 | W5b.md L255 | W5b no-flagged: runs left out | 7 | 7 | agree | 0.00 |  |
| 744 | W5b.md L255 | W5b no-flagged: n d11p | 10 | 10 | agree | 0.00 |  |
| 745 | W5b.md L255 | W5b no-flagged: d11p raw med GM % [CI] | +0.5 [-1.6, +2.7] | 0.52 -1.62 2.70 | agree | 0.20 |  |
| 746 | W5b.md L255 | W5b no-flagged: d11p raw fps GM % [CI] | -0.6 [-2.3, +1.2] | -0.56 -2.28 1.18 | agree | 0.38 |  |
| 747 | W5b.md L255 | W5b no-flagged: d11p cores change [CI] | -0.20 [-0.24, -0.17] | -0.204 -0.237 -0.171 | agree | 0.36 |  |
| 748 | W5b.md L256 | W5b no-loaded: runs left out | 9 | 9 | agree | 0.00 |  |
| 749 | W5b.md L256 | W5b no-loaded: n d11p | 8 | 8 | agree | 0.00 |  |
| 750 | W5b.md L256 | W5b no-loaded: d11p raw med GM % [CI] | +0.0 [-2.3, +2.4] | 0.02 -2.24 2.33 | DISAGREE | 0.67 |  |
| 751 | W5b.md L256 | W5b no-loaded: d11p raw fps GM % [CI] | -0.2 [-2.0, +1.7] | -0.15 -1.98 1.71 | agree | 0.47 |  |
| 752 | W5b.md L256 | W5b no-loaded: d11p cores change [CI] | -0.21 [-0.25, -0.18] | -0.213 -0.248 -0.177 | agree | 0.27 |  |
| 753 | W5b.md L257 | W5b no-audit-flag: runs left out | 6 | 6 | agree | 0.00 |  |
| 754 | W5b.md L257 | W5b no-audit-flag: n d11p | 10 | 10 | agree | 0.00 |  |
| 755 | W5b.md L257 | W5b no-audit-flag: d11p raw med GM % [CI] | +0.5 [-1.7, +2.7] | 0.52 -1.65 2.73 | DISAGREE | 0.51 |  |
| 756 | W5b.md L257 | W5b no-audit-flag: d11p raw fps GM % [CI] | -0.6 [-2.3, +1.2] | -0.56 -2.30 1.21 | agree | 0.38 |  |
| 757 | W5b.md L257 | W5b no-audit-flag: d11p cores change [CI] | -0.20 [-0.24, -0.17] | -0.204 -0.237 -0.171 | agree | 0.36 |  |
| 758 | W5b.md L258 | W5b no-slow-d11t: runs left out | 2 | 2 | agree | 0.00 |  |
| 759 | W5b.md L258 | W5b no-slow-d11t: n d11p | 12 | 12 | agree | 0.00 |  |
| 760 | W5b.md L258 | W5b no-slow-d11t: d11p raw med GM % [CI] | +0.5 [-1.4, +2.5] | 0.51 -1.45 2.50 | agree | 0.49 |  |
| 761 | W5b.md L258 | W5b no-slow-d11t: d11p raw fps GM % [CI] | -0.7 [-2.3, +0.9] | -0.73 -2.33 0.89 | agree | 0.35 |  |
| 762 | W5b.md L258 | W5b no-slow-d11t: d11p cores change [CI] | -0.20 [-0.24, -0.17] | -0.204 -0.235 -0.172 | agree | 0.46 |  |
| 763 | W5b.md L259 | W5b no-0221: runs left out | 1 | 1 | agree | 0.00 |  |
| 764 | W5b.md L259 | W5b no-0221: n d11p | 12 | 12 | agree | 0.00 |  |
| 765 | W5b.md L259 | W5b no-0221: d11p raw med GM % [CI] | +0.5 [-1.6, +2.6] | 0.51 -1.57 2.64 | agree | 0.35 |  |
| 766 | W5b.md L259 | W5b no-0221: d11p raw fps GM % [CI] | -0.7 [-2.5, +1.0] | -0.73 -2.45 1.01 | agree | 0.49 |  |
| 767 | W5b.md L259 | W5b no-0221: d11p cores change [CI] | -0.20 [-0.24, -0.17] | -0.204 -0.235 -0.172 | agree | 0.46 |  |
| 768 | W5b.md L260 | W5b no-p2-first3: runs left out | 3 | 3 | agree | 0.00 |  |
| 769 | W5b.md L260 | W5b no-p2-first3: n d11p | 11 | 11 | agree | 0.00 |  |
| 770 | W5b.md L260 | W5b no-p2-first3: d11p raw med GM % [CI] | +0.7 [-1.4, +2.8] | 0.65 -1.45 2.80 | agree | 0.50 |  |
| 771 | W5b.md L260 | W5b no-p2-first3: d11p raw fps GM % [CI] | -0.6 [-2.4, +1.1] | -0.64 -2.35 1.10 | agree | 0.46 |  |
| 772 | W5b.md L260 | W5b no-p2-first3: d11p cores change [CI] | -0.20 [-0.23, -0.17] | -0.201 -0.233 -0.169 | agree | 0.33 |  |
| 773 | W5b.md L261 | W5b drop-p2-r1r2: n d11p | 10 | 10 | agree | 0.00 |  |
| 774 | W5b.md L261 | W5b drop-p2-r1r2: d11p raw med GM % [CI] | +0.8 [-1.5, +3.1] | 0.77 -1.51 3.10 | agree | 0.31 |  |
| 775 | W5b.md L261 | W5b drop-p2-r1r2: d11p raw fps GM % [CI] | -0.7 [-2.6, +1.2] | -0.71 -2.57 1.19 | agree | 0.26 |  |
| 776 | W5b.md L261 | W5b drop-p2-r1r2: d11p cores change [CI] | -0.19 [-0.23, -0.16] | -0.194 -0.227 -0.161 | agree | 0.40 |  |
| 777 | W5b.md L262 | W5b drop-r1-both: n d11p | 10 | 10 | agree | 0.00 |  |
| 778 | W5b.md L262 | W5b drop-r1-both: d11p raw med GM % [CI] | +0.1 [-0.9, +1.1] | 0.09 -0.89 1.08 | agree | 0.18 |  |
| 779 | W5b.md L262 | W5b drop-r1-both: d11p raw fps GM % [CI] | -0.2 [-1.0, +0.6] | -0.23 -1.04 0.58 | agree | 0.43 |  |
| 780 | W5b.md L262 | W5b drop-r1-both: d11p cores change [CI] | -0.21 [-0.24, -0.18] | -0.208 -0.239 -0.177 | agree | 0.29 |  |
| 781 | W5b.md L263 | W5b pass 1 only: n d11p | 6 | 6 | agree | 0.00 |  |
| 782 | W5b.md L263 | W5b pass 1 only: d11p raw med GM % [CI] | +0.8 [-3.1, +4.8] | 0.76 -3.09 4.75 | agree | 0.49 |  |
| 783 | W5b.md L263 | W5b pass 1 only: d11p raw fps GM % [CI] | -0.7 [-3.8, +2.6] | -0.68 -3.83 2.56 | agree | 0.35 |  |
| 784 | W5b.md L263 | W5b pass 1 only: d11p cores change [CI] | -0.20 [-0.25, -0.15] | -0.203 -0.252 -0.155 | agree | 0.26 |  |
| 785 | W5b.md L264 | W5b pass 2 only: n d11p | 6 | 6 | agree | 0.00 |  |
| 786 | W5b.md L264 | W5b pass 2 only: d11p raw med GM % [CI] | +0.3 [-1.6, +2.2] | 0.26 -1.64 2.20 | agree | 0.38 |  |
| 787 | W5b.md L264 | W5b pass 2 only: d11p raw fps GM % [CI] | -0.8 [-2.4, +0.9] | -0.79 -2.43 0.88 | agree | 0.31 |  |
| 788 | W5b.md L264 | W5b pass 2 only: d11p cores change [CI] | -0.20 [-0.25, -0.16] | -0.205 -0.245 -0.164 | agree | 0.48 |  |
| 789 | W5b.md L42 | cores change [CI] (GM %): d11t; d11p | -0.22 [-0.25, -0.19] (-8.6 %), -0.20 [-0.23, -0.17] (-8.0 %) | -0.220 -0.251 -0.189 -8.63 -0.204 -0.235 -0.173 -8.00 | agree | 0.49 |  |
| 790 | W5b.md L42 | d11t raw median ms higher than d11 in k of n rounds | 11 of 12 | 11 12 | agree | 0.00 |  |
| 791 | W5b.md L42 | loaded runs (ng_t >= 2.8), mean fps vs the arm quiet median: d11t %, d11p %; n each | d11t -3.0 %, d11p -1.1 % (n = 4, 4) | -3.00 -1.06 4 4 | agree | 0.43 |  |
| 792 | W5b.md L43 | pass 2: d11p cores change (2 dp, 4 dp); runner's arm cores d11p, d11; d11p fps median % | -0.20 core (-0.2045; runner 2.35 - 2.56), fps +0.07 % | -0.205 -0.20450 2.354 2.558 0.070 | agree | 0.45 | the runner's -0.21 = 2.35 - 2.56 (its 2-dp arm values) |
| 793 | W5b.md L43 | pass 2: d11t cores change, d11t fps median % | d11t -0.21 core, fps -0.83 % | -0.212 -0.825 | agree | 0.47 |  |
| 794 | W5b.md L43 | pass 2 quiet runs (ng_t < 2.8): d11t n, fps range; d11 fps range | 3 quiet runs at 384.7-385.7 fps; d11 385.0-385.4 | 3 384.72 385.75 384.99 385.42 | agree | 0.49 |  |
| 795 | W5b.md L45 | first four scored W5b-2 runs: window ng_t range | 2.84-3.76 | 2.838 3.757 | agree | 0.26 | runs: 0453-d11-r1, 0455-d11t-r1, 0457-d11p-r1, 0459-d11t-r2 |
| 796 | W5b.md L57 | cold runs left out (unscored) | 2 | 2 | agree | 0.00 | runs: 0155-cold-d11, 0451-cold-d11 |
| 797 | W5b.md L68 | no-flagged: union size; n d11 / d11t / d11p | 7 runs, n = 11 / 8 / 10 | 7 11 8 10 | agree | 0.00 |  |
| 798 | W5b.md L69 | no-loaded: ng_t of 0520-d11p-r5, 0524-d11p-r6; runs left out (flagged or ng_t >= 2.8); n d11 / d11t / d11p | (2.90) (2.88); 9 runs, n = 11 / 8 / 8 | 2.897 2.877 9 11 8 8 | agree | 0.35 | unflagged kept runs at ng_t >= 2.8: 0520-d11p-r5, 0524-d11p-r6 |
| 799 | W5b.md L70 | 0221-d11t-r5 window ng_t | 2.31 | 2.558 | DISAGREE | 24.79 | MISREAD: 2.31 is the "game" (game cores) column of audit.md L257; that row's "ng_t mean" is 2.56 (runs.csv win_ngB_mean 2.5579, z_t -0.0). Still below 2.8 and unflagged, so the point stands |
| 800 | W5b.md L81 | light share per arm (mean of results.csv light_share): d11, d11t, d11p | 0.974 0.972 0.975 | 0.9745 0.9719 0.9744 / posted run-table light shares: 0.9744 0.9719 0.9745 | agree (posted run-table light shares) | 0.50 | light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share rounded to 3 dp |
| 801 | W5b.md L81 | light share one-way F (df1, df2) | 1.18 (2, 33) | 1.214 2 33 / posted run-table light shares: 1.225 2 33 | DISAGREE | 3.43 | light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share rounded to 3 dp |
| 802 | W5b.md L84 | fps of 0157-d11-r1, 0159-d11t-r1, 0201-d11p-r1; fps range of the other 33 kept runs | 415.1, 407.0, 395.9; others 367.1-393.0 | 415.09 407.04 395.94 367.13 392.97 | agree | 0.44 |  |
| 803 | W5b.md L85 | light share: those 3 (range) vs the other 33 kept runs (range) | 0.979-0.988 vs 0.962-0.978 | 0.9790 0.9880 0.9620 0.9780 | agree | 0.00 | light share: Agent 7 counts light frames from the frame data; results.csv stores frame_summary's share rounded to 3 dp |
| 804 | W5b.md L86 | round 1 raw fps % vs d11: d11t, d11p | d11t -1.95 %, d11p -4.63 % | -1.940 -4.613 / rounded inputs: -1.951 -4.625 | agree (rounded inputs) | 0.46 |  |
| 805 | W5b.md L119 | cores d11t - d11p [CI] | -0.016 [-0.047, +0.016] | -0.0161 -0.0471 0.0149 / rounded inputs: -0.0158 -0.0474 0.0158 | agree (rounded inputs) | 0.43 |  |
| 806 | W5b.md L133 | d11t without each pass r1: raw median ms higher k of n, sign p, mean %, median %; raw fps lower k of n, mean %, median % | 9 of 10 (sign p 0.021; mean +0.68 %, median +0.32 %); 7 of 10 (mean -0.69 %, median -0.21 %) | 9 10 0.0215 0.683 0.318 7 10 -0.683 -0.206 / rounded inputs: 9 10 0.0215 0.683 0.318 7 10 -0.688 -0.208 | agree (rounded inputs) | 0.48 |  |
| 807 | W5b.md L134 | d11p without each pass r1: raw median ms higher k of n, mean %, median %; raw fps higher k of n, mean %, median % | 4 of 10 (mean +0.10 %, median -0.38 %); 7 of 10 (mean -0.23 %, median +0.07 %) | 4 10 0.097 -0.377 7 10 -0.231 0.079 / rounded inputs: 4 10 0.097 -0.377 7 10 -0.234 0.065 | agree (rounded inputs) | 0.47 |  |
| 808 | W5b.md L136 | rounds with no flagged run: d11t raw median ms higher k of n, sign p, mean %, median % | 7 of 8 (sign p 0.070; mean +0.48 %, median +0.30 %) | 7 8 0.0703 0.478 0.300 | agree | 0.31 | rounds r1, r2, r4, r5, r6, r10, r11, r12 (as posted) |
| 809 | W5b.md L147 | d11t p99.9 mean without 0221-d11t-r5 | 5.58 | 5.581 | agree | 0.06 |  |
| 810 | W5b.md L148 | paired p99.9 ms difference vs d11 [CI], higher k of n: d11t; d11p | +0.659 ms [-0.475, +1.793], 6 of 12; +0.021 ms [-0.126, +0.168], 6 of 12 | 0.6592 -0.4747 1.7931 6 12 0.0211 -0.1259 0.1681 6 12 | agree | 0.25 |  |
| 811 | W5b.md L163 | pass 2 d11t: fps of 0455, 0459, 0510; the other runs: n, fps range; d11 quiet pass-2 fps range | (367.1), (376.6), (379.3); other 3 at 384.7-385.7; d11 quiet 385.0-385.4 | 367.13 376.63 379.29 3 384.72 385.75 384.99 385.42 | agree | 0.49 |  |
| 812 | W5b.md L164 | d11t median fps: pass 2; pass 2 without 0455 and 0510; pass 1 | 382.0 with them, 385.0 without; W5b first pass 384.2 | 382.00 385.03 384.23 | agree | 0.35 |  |
| 813 | W5b.md L166 | pass 1 runner summary: median fps d11 / d11t / d11p; mean cores; median-ms spread % ((max-min)/median) | fps 384.65 / 384.23 / 384.99; cores 2.54 / 2.31 / 2.34; spreads 10.1 / 10.3 / 4.4 % | 384.645 384.228 384.995 2.539 2.310 2.336 10.10 10.30 4.36 | agree | 0.45 |  |
| 814 | W5b.md L174 | cores lower than d11 in k of n rounds (smaller k of the 2 arms); section 6 cores change range: d11t, d11p | 12 of 12 rounds (both arms); d11t -0.21 to -0.23, d11p -0.19 to -0.21 | 12 12 -0.212 -0.229 -0.194 -0.213 | agree | 0.42 |  |
| 815 | W5b.md L185 | d11t raw median ms higher than d11: k of n rounds (sign p) | 11 of 12 rounds (sign p 0.006) | 11 12 0.0063 | agree | 0.35 |  |
| 816 | W5b.md L186 | d11t raw median ms higher than d11 without each pass r1: k of n (sign p) | 9 of 10 (p 0.021) | 9 10 0.0215 | agree | 0.48 |  |
| 817 | W5b.md L187 | d11t raw median ms higher than d11 in the rounds with no flagged run: k of n (sign p) | 7 of 8 (p 0.070) | 7 8 0.0703 | agree | 0.31 | rounds r1, r2, r4, r5, r6, r10, r11, r12 (as posted) |
| 818 | W5b.md L189 | d11p raw median ms higher: k of n (all), k of n (without r1), median round without r1 % | 5 of 12 rounds and 4 of 10 (median round -0.38 %) | 5 12 4 10 -0.377 | agree | 0.28 |  |
| 819 | W5b.md L206 | loaded runs: d11t n, mean fps vs arm %, mean ng_t; d11p n, mean fps %, mean ng_t | 4 runs -3.0 % at mean ng_t 3.11; 4 runs -1.1 % at 3.15 | 4 -3.00 3.112 4 -1.06 3.149 | agree | 0.43 |  |
| 820 | W5b.md L207 | loaded runs, mean eff MHz vs the arm quiet median %: d11p, d11t | -4.5 % vs -3.9 % | -4.50 -3.93 | agree | 0.29 |  |
| 821 | W5b.md L210 | the 9 loaded runs: cores minus the arm quiet median, range; rest (d11t and d11p runs), range | +0.01 to +0.09; -0.17 to +0.01 | 0.007 0.082 -0.176 0.001 / rounded inputs: 0.010 0.090 -0.174 0.006 | agree (rounded inputs) | 0.44 |  |
| 822 | W5b.md L211 | within-arm Spearman rho(ng_t, raw fps) and p (centred on pass x arm medians): pass 1; pass 2 | -0.67 (p 0.002); -0.32 (p 0.19) | -0.670 0.0024 -0.315 0.203 / rounded inputs: -0.673 0.0022 -0.321 0.193 | agree (rounded inputs) | 0.34 |  |
| 823 | W5b.md L215 | 0221-d11t-r5: window ng_t, p99.9 ms, longest frame ms | ng_t 2.31; p99.9 11.672 ms; longest 26.37 ms | 2.558 11.6720 26.366 | DISAGREE | 24.79 | MISREAD: 2.31 is the "game" (game cores) column of audit.md L257; that row's "ng_t mean" is 2.56 (runs.csv win_ngB_mean 2.5579, z_t -0.0). Still below 2.8 and unflagged, so the point stands |
| 824 | W5b.md L224 | audit 1 s max ng_t (win_ngB_max): 0213-d11t-r3, 0510-d11t-r3, 0453-d11-r1 vs 0221-d11t-r5 | 8.04, 7.60, 7.49 vs 5.95 | 8.040 7.603 7.491 5.950 | agree | 0.26 |  |
| 825 | W5b.md L270 | d11 n per section 6 pool: 12; 11 (no-flagged, no-loaded, no-audit-flag, no-p2-first3); 10 (drop-round); 6 (one-pass) | 12 11 10 6 | 12 11 10 6 | agree | 0.00 | all 11 pools as stated |
| 826 | W5b.md L285 | cold runs: 0451-cold-d11 window ng_t, warm-up ng_t; 0155-cold-d11 window, warm-up | 2.55 and warm-up 1.94 (first pass cold: 2.39 / 1.93) | 2.547 1.943 2.393 1.929 | agree | 0.34 |  |
| 827 | W5b.md L287 | first four scored W5b-2 runs: window ng_t; warm-up ng_t | 3.53 / 3.37 / 3.76 / 2.84, with warm-up ng_t 2.55 / 3.80 / 3.62 / 3.48 | 3.527 3.373 3.757 2.838 2.554 3.795 3.624 3.476 | agree | 0.46 | runs: 0453-d11-r1, 0455-d11t-r1, 0457-d11p-r1, 0459-d11t-r2 |
| 828 | W5b.md L288 | first 3 scored runs vs the other 15, median ng_t: W5b-2; W5b-1 | 3 vs 15: 3.53 vs 2.50; first pass 2.46 vs 2.56 | 3 15 3.527 2.503 2.464 2.559 | agree | 0.39 |  |
| 829 | W5b.md L291 | median ng_t of the kept runs, W5b-2 minus W5b-1: d11, d11t, d11p | d11 -0.03, d11t +0.09, d11p +0.16 | -0.032 0.093 0.160 | agree | 0.29 |  |
| 830 | W5b.md L305 | quiet runs (ng_t < 2.8): median fps, range over the 3 arms | 385.1-385.4 fps | 385.08 385.45 | agree | 0.50 |  |
| 831 | load-check.md L11 | W9-1: ng_t median, min, max, n; count >= 2.8; median of the rest; Spearman rho(ng_t, fps), n | 2.37 2.16 2.77 20 0 2.37 -0.73 20 | 2.370 2.164 2.768 20 0 2.370 -0.731 20 | agree | 0.19 |  |
| 832 | load-check.md L11 | W9-1: within-arm Spearman (centred on pass x arm medians) | -0.85 | -0.854 | agree | 0.30 |  |
| 833 | load-check.md L12 | W9-2: ng_t median, min, max, n; count >= 2.8; median of the rest; Spearman rho(ng_t, fps), n | 2.58 2.21 4.06 20 8 2.33 -0.82 20 | 2.577 2.210 4.059 20 8 2.334 -0.808 20 / rounded inputs: 2.575 2.210 4.060 20 8 2.335 -0.821 20 | agree (rounded inputs) | 0.50 |  |
| 834 | load-check.md L12 | W9-2: within-arm Spearman (centred on pass x arm medians) | -0.78 | -0.780 | agree | 0.05 |  |
| 835 | load-check.md L18 | W9 off quiet runs (ng_t < 2.8): n, median fps, raw ms, cores, eff MHz | 7 385.8 2.458 2.520 1966 | 7 385.81 2.4580 2.5150 1966 / rounded inputs: 7 385.80 2.4580 2.5200 1966 | agree (rounded inputs) | 0.00 |  |
| 836 | load-check.md L19 | W9 q0 quiet runs (ng_t < 2.8): n, median fps, raw ms, cores, eff MHz | 7 385.8 2.472 2.490 2040 | 7 385.80 2.4720 2.4860 2040 / rounded inputs: 7 385.80 2.4720 2.4900 2040 | agree (rounded inputs) | 0.00 |  |
| 837 | load-check.md L20 | W9 q125 quiet runs (ng_t < 2.8): n, median fps, raw ms, cores, eff MHz | 6 389.5 2.303 1.805 2170 | 6 389.50 2.3030 1.8050 2169.5 | agree | 0.50 |  |
| 838 | load-check.md L21 | W9 q250 quiet runs (ng_t < 2.8): n, median fps, raw ms, cores, eff MHz | 5 389.1 2.324 1.730 2171 | 5 389.12 2.3240 1.7320 2171 / rounded inputs: 5 389.10 2.3240 1.7300 2171 | agree (rounded inputs) | 0.00 |  |
| 839 | load-check.md L22 | W9 q500 quiet runs (ng_t < 2.8): n, median fps, raw ms, cores, eff MHz | 7 389.8 2.310 1.730 2205 | 7 389.82 2.3100 1.7250 2205 / rounded inputs: 7 389.80 2.3100 1.7300 2205 | agree (rounded inputs) | 0.00 |  |
| 840 | load-check.md L26 | W9 loaded 0407-q125-r1: ng, eff, effp, fps, fpsp, ms, msp, cores, coresd, const, rest | 4.06 1857 (-14.4 %) 365.0 (-6.3 %) 2.477 (+7.6 %) 2.15 (+0.34) 2.11 +0.04 | 4.059 1857 -14.40 364.99 -6.29 2.4770 7.56 2.147 0.342 2.109 0.038 | agree | 0.45 |  |
| 841 | load-check.md L27 | W9 loaded 0423-q125-r3: ng, eff, effp, fps, fpsp, ms, msp, cores, coresd, const, rest | 4.03 1853 (-14.6 %) 368.4 (-5.4 %) 2.510 (+9.0 %) 2.13 (+0.32) 2.11 +0.02 | 4.033 1853 -14.59 368.43 -5.41 2.5100 8.99 2.133 0.328 2.113 0.020 / rounded inputs: 4.033 1853 -14.59 368.40 -5.42 2.5100 8.99 2.130 0.325 2.113 0.017 | agree (rounded inputs) | 0.50 |  |
| 842 | load-check.md L28 | W9 loaded 0409-q250-r1: ng, eff, effp, fps, fpsp, ms, msp, cores, coresd, const, rest | 3.72 1894 (-12.8 %) 378.2 (-2.8 %) 2.460 (+5.9 %) 2.11 (+0.38) 1.98 +0.13 | 3.719 1894 -12.76 378.18 -2.81 2.4600 5.85 2.106 0.374 1.985 0.121 / rounded inputs: 3.719 1894 -12.76 378.20 -2.80 2.4600 5.85 2.110 0.380 1.983 0.127 | agree (rounded inputs) | 0.48 |  |
| 843 | load-check.md L29 | W9 loaded 0419-q500-r2: ng, eff, effp, fps, fpsp, ms, msp, cores, coresd, const, rest | 3.36 1947 (-11.7 %) 385.8 (-1.0 %) 2.356 (+2.0 %) 2.03 (+0.30) 1.96 +0.07 | 3.363 1947 -11.70 385.82 -1.03 2.3560 1.99 2.026 0.301 1.954 0.072 / rounded inputs: 3.363 1947 -11.70 385.80 -1.03 2.3560 1.99 2.030 0.300 1.959 0.071 | agree (rounded inputs) | 0.34 |  |
| 844 | load-check.md L30 | W9 loaded 0425-q250-r3: ng, eff, effp, fps, fpsp, ms, msp, cores, coresd, const, rest | 3.14 1996 (-8.1 %) 386.4 (-0.7 %) 2.356 (+1.4 %) 1.98 (+0.25) 1.88 +0.10 | 3.142 1996 -8.06 386.42 -0.69 2.3560 1.38 1.981 0.249 1.884 0.097 | agree | 0.39 |  |
| 845 | load-check.md L31 | W9 loaded 0421-off-r2: ng, eff, effp, fps, fpsp, ms, msp, cores, coresd | 2.92 1907 (-3.0 %) 382.2 (-0.9 %) 2.469 (+0.4 %) 2.54 (+0.02) | 2.922 1907 -3.00 382.16 -0.95 2.4690 0.45 2.545 0.030 / rounded inputs: 2.922 1907 -3.00 382.20 -0.93 2.4690 0.45 2.540 0.020 | agree (rounded inputs) | 0.48 |  |
| 846 | load-check.md L32 | W9 loaded 0417-q250-r2: ng, eff, effp, fps, fpsp, ms, msp, cores, coresd, const, rest | 2.91 2075 (-4.4 %) 379.1 (-2.6 %) 2.377 (+2.3 %) 1.93 (+0.20) 1.81 +0.12 | 2.912 2075 -4.42 379.15 -2.56 2.3770 2.28 1.934 0.202 1.812 0.122 | agree | 0.30 |  |
| 847 | load-check.md L33 | W9 loaded 0440-q0-r4: ng, eff, effp, fps, fpsp, ms, msp, cores, coresd | 2.81 1996 (-2.2 %) 384.0 (-0.5 %) 2.473 (+0.0 %) 2.46 (-0.03) | 2.809 1996 -2.16 384.00 -0.47 2.4730 0.04 2.460 -0.026 | agree | 0.43 |  |
| 848 | load-check.md L48 | W9 full pool: cores q500 - off: n, n, change [CI], df | 8 8 -0.749 -0.861 -0.637 35 | 8 8 -0.7490 -0.8607 -0.6373 35 | agree | 0.28 |  |
| 849 | load-check.md L48 | W9 full pool: cores q500 - q250: n, n, change [CI], df | 8 8 -0.104 -0.216 +0.008 35 | 8 8 -0.1040 -0.2157 0.0077 35 | agree | 0.28 |  |
| 850 | load-check.md L48 | W9 full pool: cores q500 - q125: n, n, change [CI], df | 8 8 -0.133 -0.245 -0.020 35 | 8 8 -0.1334 -0.2451 -0.0217 35 / rounded inputs: 8 8 -0.1325 -0.2445 -0.0205 35 | agree (rounded inputs) | 0.50 |  |
| 851 | load-check.md L48 | W9 full pool: cores q250 - q125: n, n, change [CI], df | 8 8 -0.029 -0.141 +0.083 35 | 8 8 -0.0294 -0.1411 0.0823 35 / rounded inputs: 8 8 -0.0288 -0.1408 0.0833 35 | agree (rounded inputs) | 0.28 |  |
| 852 | load-check.md L49 | W9 no-lowclk: cores q500 - off: n, n, change [CI], df | 7 8 -0.788 -0.849 -0.727 31 | 7 8 -0.7874 -0.8491 -0.7258 31 / rounded inputs: 7 8 -0.7877 -0.8488 -0.7266 31 | agree (rounded inputs) | 0.42 |  |
| 853 | load-check.md L49 | W9 no-lowclk: cores q500 - q250: n, n, change [CI], df | 7 7 -0.107 -0.170 -0.044 31 | 7 7 -0.1074 -0.1711 -0.0437 31 / rounded inputs: 7 7 -0.1071 -0.1702 -0.0440 31 | agree (rounded inputs) | 0.25 |  |
| 854 | load-check.md L49 | W9 no-lowclk: cores q500 - q125: n, n, change [CI], df | 7 6 -0.088 -0.154 -0.022 31 | 7 6 -0.0886 -0.1549 -0.0223 31 / rounded inputs: 7 6 -0.0881 -0.1538 -0.0224 31 | agree (rounded inputs) | 0.42 |  |
| 855 | load-check.md L49 | W9 no-lowclk: cores q250 - q125: n, n, change [CI], df | 7 6 +0.019 -0.047 +0.085 31 | 7 6 0.0189 -0.0475 0.0852 31 | agree | 0.37 |  |
| 856 | load-check.md L50 | W9 no-slow-q: cores q500 - off: n, n, change [CI], df | 8 8 -0.749 -0.826 -0.672 31 | 8 8 -0.7490 -0.8256 -0.6724 31 | agree | 0.38 |  |
| 857 | load-check.md L50 | W9 no-slow-q: cores q500 - q250: n, n, change [CI], df | 8 6 -0.051 -0.134 +0.032 31 | 8 6 -0.0510 -0.1337 0.0318 31 | agree | 0.17 |  |
| 858 | load-check.md L50 | W9 no-slow-q: cores q500 - q125: n, n, change [CI], df | 8 6 -0.049 -0.132 +0.034 31 | 8 6 -0.0501 -0.1329 0.0326 31 / rounded inputs: 8 6 -0.0492 -0.1322 0.0338 31 | agree (rounded inputs) | 0.17 |  |
| 859 | load-check.md L50 | W9 no-slow-q: cores q250 - q125: n, n, change [CI], df | 6 6 +0.002 -0.087 +0.090 31 | 6 6 0.0008 -0.0876 0.0893 31 / rounded inputs: 6 6 0.0017 -0.0871 0.0904 31 | agree (rounded inputs) | 0.40 |  |
| 860 | load-check.md L51 | W9 no-flagged: cores q500 - off: n, n, change [CI], df | 7 8 -0.788 -0.841 -0.735 28 | 7 8 -0.7874 -0.8409 -0.7340 28 / rounded inputs: 7 8 -0.7877 -0.8409 -0.7345 28 | agree (rounded inputs) | 0.50 |  |
| 861 | load-check.md L51 | W9 no-flagged: cores q500 - q250: n, n, change [CI], df | 7 5 -0.069 -0.130 -0.009 28 | 7 5 -0.0692 -0.1296 -0.0087 28 | agree | 0.39 |  |
| 862 | load-check.md L51 | W9 no-flagged: cores q500 - q125: n, n, change [CI], df | 7 5 -0.071 -0.132 -0.011 28 | 7 5 -0.0714 -0.1318 -0.0109 28 | agree | 0.37 |  |
| 863 | load-check.md L51 | W9 no-flagged: cores q250 - q125: n, n, change [CI], df | 5 5 -0.002 -0.067 +0.063 28 | 5 5 -0.0022 -0.0675 0.0631 28 | agree | 0.02 |  |
| 864 | load-check.md L55 | W9 q0 vs off, raw median ms, all rounds: n, higher k/n, sign p, mean %, median %, per-round % | 8 8/8 p 0.008 +2.65 +0.45 +12.43 +0.49 +0.12 +1.31 +6.02 +0.12 +0.41 +0.28 | 8 8 8 0.0078 2.648 0.447 12.434 0.487 0.121 1.306 6.022 0.122 0.407 0.284 | agree | 0.44 |  |
| 865 | load-check.md L56 | W9 q0 vs off, raw median ms, without each pass's round 1: n, higher k/n, sign p, mean %, median %, per-round % | 6 6/6 p 0.031 +0.45 +0.35 +0.49 +0.12 +1.31 +0.12 +0.41 +0.28 | 6 6 6 0.0312 0.454 0.345 0.487 0.121 1.306 0.122 0.407 0.284 | agree | 0.47 |  |
| 866 | load-check.md L59 | W9 q500 vs off, raw fps, all rounds: n, higher k/n, sign p, mean %, median %, per-round % | 8 6/8 p 0.289 -1.22 +1.03 -11.95 +1.11 +1.64 +0.91 -4.94 +0.94 +1.19 +1.35 | 8 6 8 0.2891 -1.216 1.034 -11.954 1.111 1.650 0.899 -4.946 0.957 1.195 1.363 / rounded inputs: 8 6 8 0.2891 -1.217 1.028 -11.945 1.115 1.644 0.905 -4.940 0.942 1.194 1.352 | agree (rounded inputs) | 0.50 |  |
| 867 | load-check.md L60 | W9 q500 vs off, raw fps, without each pass's round 1: n, higher k/n, sign p, mean %, median %, per-round % | 6 6/6 p 0.031 +1.19 +1.15 +1.11 +1.64 +0.91 +0.94 +1.19 +1.35 | 6 6 6 0.0312 1.196 1.153 1.111 1.650 0.899 0.957 1.195 1.363 / rounded inputs: 6 6 6 0.0312 1.192 1.154 1.115 1.644 0.905 0.942 1.194 1.352 | agree (rounded inputs) | 0.47 |  |
| 868 | load-check.md L61 | W9 q500 vs off, raw median ms, all rounds: n, higher k/n, sign p, mean %, median %, per-round % | 8 1/8 p 0.070 -3.18 -5.86 +10.27 -6.21 -6.76 -5.75 -0.39 -4.58 -6.06 -5.96 | 8 1 8 0.0703 -3.179 -5.857 10.274 -6.212 -6.755 -5.753 -0.387 -4.577 -6.062 -5.961 | agree | 0.49 |  |
| 869 | load-check.md L62 | W9 q500 vs off, raw median ms, without each pass's round 1: n, higher k/n, sign p, mean %, median %, per-round % | 6 0/6 p 0.031 -5.89 -6.01 -6.21 -6.76 -5.75 -4.58 -6.06 -5.96 | 6 0 6 0.0312 -5.887 -6.011 -6.212 -6.755 -5.753 -4.577 -6.062 -5.961 | agree | 0.49 |  |
| 870 | load-check.md L63 | W9 q125 vs off, raw fps, all rounds: n, higher k/n, sign p, mean %, median %, per-round % | 8 5/8 p 0.727 -2.43 +0.62 -10.86 +0.52 +1.70 +0.72 -10.74 +2.30 -4.36 +1.25 | 8 5 8 0.7266 -2.435 0.609 -10.871 0.505 1.706 0.712 -10.740 2.305 -4.350 1.249 / rounded inputs: 8 5 8 0.7266 -2.434 0.621 -10.863 0.518 1.697 0.724 -10.736 2.302 -4.361 1.248 | agree (rounded inputs) | 0.44 |  |
| 871 | load-check.md L64 | W9 q125 vs off, raw fps, without each pass's round 1: n, higher k/n, sign p, mean %, median %, per-round % | 6 5/6 p 0.219 +0.35 +0.99 +0.52 +1.70 +0.72 +2.30 -4.36 +1.25 | 6 5 6 0.2188 0.354 0.981 0.505 1.706 0.712 2.305 -4.350 1.249 / rounded inputs: 6 5 6 0.2188 0.355 0.986 0.518 1.697 0.724 2.302 -4.361 1.248 | agree (rounded inputs) | 0.47 |  |
| 872 | load-check.md L65 | W9 q250 vs off, raw fps, all rounds: n, higher k/n, sign p, mean %, median %, per-round % | 8 5/8 p 0.727 -2.07 +0.19 -12.13 +0.08 +1.72 +0.62 -7.51 -0.81 +0.31 +1.17 | 8 5 8 0.7266 -2.064 0.200 -12.130 0.080 1.720 0.622 -7.516 -0.788 0.319 1.182 / rounded inputs: 8 5 8 0.7266 -2.068 0.195 -12.125 0.078 1.723 0.621 -7.508 -0.811 0.312 1.170 | agree (rounded inputs) | 0.47 |  |
| 873 | load-check.md L66 | W9 q250 vs off, raw fps, without each pass's round 1: n, higher k/n, sign p, mean %, median %, per-round % | 6 5/6 p 0.219 +0.52 +0.47 +0.08 +1.72 +0.62 -0.81 +0.31 +1.17 | 6 5 6 0.2188 0.523 0.471 0.080 1.720 0.622 -0.788 0.319 1.182 / rounded inputs: 6 5 6 0.2188 0.515 0.466 0.078 1.723 0.621 -0.811 0.312 1.170 | agree (rounded inputs) | 0.47 |  |
| 874 | load-check.md L67 | W9 q500 vs off, raw fps, without rounds holding a flagged run (no-flagged list): n, higher k/n, sign p, mean %, median %, per-round % | 7 5/7 p 0.453 -1.52 +1.11 -11.95 +1.11 +1.64 +0.91 -4.94 +1.19 +1.35 | 7 5 7 0.4531 -1.526 1.111 -11.954 1.111 1.650 0.899 -4.946 1.195 1.363 / rounded inputs: 7 5 7 0.4531 -1.525 1.115 -11.945 1.115 1.644 0.905 -4.940 1.194 1.352 | agree (rounded inputs) | 0.50 |  |
| 875 | load-check.md L68 | W9 q500 vs off, raw median ms, without rounds holding a flagged run (no-flagged list): n, higher k/n, sign p, mean %, median %, per-round % | 7 1/7 p 0.125 -2.98 -5.96 +10.27 -6.21 -6.76 -5.75 -0.39 -6.06 -5.96 | 7 1 7 0.1250 -2.979 -5.961 10.274 -6.212 -6.755 -5.753 -0.387 -6.062 -5.961 | agree | 0.49 |  |
| 876 | load-check.md L74 | W5b-1: ng_t median, min, max, n; count >= 2.8; median of the rest; Spearman rho(ng_t, fps), n | 2.56 2.36 3.36 18 2 2.55 -0.65 18 | 2.558 2.357 3.362 18 2 2.550 -0.639 18 / rounded inputs: 2.560 2.360 3.360 18 2 2.550 -0.648 18 | agree (rounded inputs) | 0.18 |  |
| 877 | load-check.md L74 | W5b-1: within-arm Spearman (centred on pass x arm medians) | -0.67 | -0.670 | agree | 0.02 |  |
| 878 | load-check.md L75 | W5b-2: ng_t median, min, max, n; count >= 2.8; median of the rest; Spearman rho(ng_t, fps), n | 2.53 2.43 3.76 18 7 2.49 -0.11 18 | 2.530 2.425 3.757 18 7 2.491 -0.092 18 / rounded inputs: 2.530 2.430 3.760 18 7 2.490 -0.111 18 | agree (rounded inputs) | 0.14 |  |
| 879 | load-check.md L75 | W5b-2: within-arm Spearman (centred on pass x arm medians) | -0.32 | -0.315 / rounded inputs: -0.321 | agree (rounded inputs) | 0.14 |  |
| 880 | load-check.md L81 | W5b d11 quiet runs (ng_t < 2.8): n, median fps, raw ms, cores, eff MHz | 11 385.1 2.512 2.540 1957 | 11 385.08 2.5120 2.5430 1957 / rounded inputs: 11 385.10 2.5120 2.5400 1957 | agree (rounded inputs) | 0.00 |  |
| 881 | load-check.md L82 | W5b d11t quiet runs (ng_t < 2.8): n, median fps, raw ms, cores, eff MHz | 8 385.2 2.518 2.300 1966 | 8 385.24 2.5185 2.3040 1966 / rounded inputs: 8 385.25 2.5185 2.3000 1966 | agree (rounded inputs) | 0.50 |  |
| 882 | load-check.md L83 | W5b d11p quiet runs (ng_t < 2.8): n, median fps, raw ms, cores, eff MHz | 8 385.4 2.502 2.325 1948 | 8 385.45 2.5020 2.3250 1948 | agree | 0.50 |  |
| 883 | load-check.md L87 | W5b loaded 0457-d11p-r1: ng, eff, effp, fps, fpsp, ms, msp, cores, coresd, const, rest | 3.76 1780 (-8.6 %) 386.0 (+0.1 %) 2.457 (-1.8 %) 2.37 (+0.04) 2.54 -0.17 | 3.757 1780 -8.62 386.03 0.15 2.4570 -1.80 2.368 0.043 2.544 -0.176 / rounded inputs: 3.757 1780 -8.62 386.00 0.14 2.4570 -1.80 2.370 0.045 2.544 -0.174 | agree (rounded inputs) | 0.50 |  |
| 884 | load-check.md L88 | W5b loaded 0453-d11-r1: ng, eff, effp, fps, fpsp, ms, msp, cores, coresd | 3.53 1848 (-5.6 %) 393.0 (+2.1 %) 2.483 (-1.2 %) 2.60 (+0.06) | 3.527 1848 -5.57 392.97 2.05 2.4830 -1.15 2.602 0.059 / rounded inputs: 3.527 1848 -5.57 393.00 2.05 2.4830 -1.15 2.600 0.060 | agree (rounded inputs) | 0.49 |  |
| 885 | load-check.md L89 | W5b loaded 0455-d11t-r1: ng, eff, effp, fps, fpsp, ms, msp, cores, coresd, const, rest | 3.37 1873 (-4.7 %) 367.1 (-4.7 %) 2.647 (+5.1 %) 2.37 (+0.07) 2.41 -0.04 | 3.373 1873 -4.73 367.13 -4.70 2.6470 5.10 2.365 0.061 2.418 -0.053 / rounded inputs: 3.373 1873 -4.73 367.10 -4.71 2.6470 5.10 2.370 0.070 2.414 -0.044 | agree (rounded inputs) | 0.42 |  |
| 886 | load-check.md L90 | W5b loaded 0213-d11t-r3: ng, eff, effp, fps, fpsp, ms, msp, cores, coresd, const, rest | 3.36 1829 (-7.0 %) 371.7 (-3.5 %) 2.606 (+3.5 %) 2.39 (+0.09) 2.47 -0.08 | 3.362 1829 -6.97 371.75 -3.50 2.6060 3.47 2.386 0.082 2.477 -0.091 / rounded inputs: 3.362 1829 -6.97 371.70 -3.52 2.6060 3.47 2.390 0.090 2.472 -0.082 | agree (rounded inputs) | 0.32 |  |
| 887 | load-check.md L91 | W5b loaded 0209-d11p-r3: ng, eff, effp, fps, fpsp, ms, msp, cores, coresd, const, rest | 3.07 1854 (-4.8 %) 381.8 (-0.9 %) 2.544 (+1.7 %) 2.37 (+0.04) 2.44 -0.07 | 3.066 1854 -4.83 381.80 -0.95 2.5440 1.68 2.372 0.047 2.443 -0.071 / rounded inputs: 3.066 1854 -4.83 381.80 -0.95 2.5440 1.68 2.370 0.045 2.443 -0.073 | agree (rounded inputs) | 0.50 |  |
| 888 | load-check.md L92 | W5b loaded 0520-d11p-r5: ng, eff, effp, fps, fpsp, ms, msp, cores, coresd, const, rest | 2.90 1906 (-2.2 %) 375.6 (-2.6 %) 2.586 (+3.4 %) 2.38 (+0.05) 2.38 +0.00 | 2.897 1906 -2.16 375.55 -2.57 2.5860 3.36 2.375 0.050 2.376 -0.001 | agree | 0.50 |  |
| 889 | load-check.md L93 | W5b loaded 0524-d11p-r6: ng, eff, effp, fps, fpsp, ms, msp, cores, coresd, const, rest | 2.88 1901 (-2.4 %) 382.1 (-0.9 %) 2.529 (+1.1 %) 2.37 (+0.04) 2.38 -0.01 | 2.877 1901 -2.41 382.14 -0.86 2.5290 1.08 2.373 0.048 2.382 -0.009 / rounded inputs: 2.877 1901 -2.41 382.10 -0.87 2.5290 1.08 2.370 0.045 2.382 -0.012 | agree (rounded inputs) | 0.50 |  |
| 890 | load-check.md L94 | W5b loaded 0510-d11t-r3: ng, eff, effp, fps, fpsp, ms, msp, cores, coresd, const, rest | 2.87 1916 (-2.5 %) 379.3 (-1.5 %) 2.528 (+0.4 %) 2.31 (+0.01) 2.36 -0.05 | 2.874 1916 -2.54 379.29 -1.55 2.5280 0.38 2.311 0.007 2.364 -0.053 | agree | 0.45 |  |
| 891 | load-check.md L95 | W5b loaded 0459-d11t-r2: ng, eff, effp, fps, fpsp, ms, msp, cores, coresd, const, rest | 2.84 1937 (-1.5 %) 376.6 (-2.2 %) 2.582 (+2.5 %) 2.34 (+0.04) 2.33 +0.01 | 2.838 1937 -1.48 376.63 -2.23 2.5820 2.52 2.339 0.035 2.338 0.001 / rounded inputs: 2.838 1937 -1.48 376.60 -2.25 2.5820 2.52 2.340 0.040 2.334 0.006 | agree (rounded inputs) | 0.45 |  |
| 892 | load-check.md L97 | W5b loaded runs vs d11's quiet median fps: base, then % per run | 385.1 +0.2 +2.1 -4.7 -3.5 -0.9 -2.5 -0.8 -1.5 -2.2 | 385.08 0.25 2.05 -4.66 -3.46 -0.85 -2.47 -0.76 -1.50 -2.19 / rounded inputs: 385.10 0.23 2.05 -4.67 -3.48 -0.86 -2.47 -0.78 -1.51 -2.21 | agree (rounded inputs) | 0.49 |  |
| 893 | load-check.md L101 | W5b full pool: cores d11t - d11: n, n, change [CI], df | 12 12 -0.219 -0.251 -0.188 33 | 12 12 -0.2200 -0.2510 -0.1890 33 / rounded inputs: 12 12 -0.2192 -0.2508 -0.1876 33 | agree (rounded inputs) | 0.43 |  |
| 894 | load-check.md L101 | W5b full pool: cores d11p - d11: n, n, change [CI], df | 12 12 -0.203 -0.235 -0.172 33 | 12 12 -0.2039 -0.2349 -0.1729 33 / rounded inputs: 12 12 -0.2033 -0.2349 -0.1717 33 | agree (rounded inputs) | 0.33 |  |
| 895 | load-check.md L101 | W5b full pool: cores d11t - d11p: n, n, change [CI], df | 12 12 -0.016 -0.047 +0.016 33 | 12 12 -0.0161 -0.0471 0.0149 33 / rounded inputs: 12 12 -0.0158 -0.0474 0.0158 33 | agree (rounded inputs) | 0.43 |  |
| 896 | load-check.md L105 | W5b d11t vs d11, raw median ms, all rounds: n, higher k/n, sign p, mean %, median %, per-round % | 12 11/12 p 0.006 +1.33 +0.46 +2.58 -1.27 +2.52 +0.24 +0.24 +1.08 +6.60 +2.79 +0.28 +0.04 +0.56 +0.36 | 12 11 12 0.0063 1.334 0.459 2.579 -1.266 2.518 0.238 0.241 1.078 6.605 2.787 0.278 0.040 0.559 0.359 | agree | 0.49 |  |
| 897 | load-check.md L106 | W5b d11t vs d11, raw median ms, without each pass's round 1: n, higher k/n, sign p, mean %, median %, per-round % | 10 9/10 p 0.021 +0.68 +0.32 -1.27 +2.52 +0.24 +0.24 +1.08 +2.79 +0.28 +0.04 +0.56 +0.36 | 10 9 10 0.0215 0.683 0.318 -1.266 2.518 0.238 0.241 1.078 2.787 0.278 0.040 0.559 0.359 | agree | 0.48 |  |
| 898 | load-check.md L107 | W5b d11p vs d11, raw median ms, all rounds: n, higher k/n, sign p, mean %, median %, per-round % | 12 5/12 p 0.774 +0.53 -0.38 +6.42 -0.67 +0.08 -0.83 +0.32 -0.60 -1.05 -0.52 -0.24 -0.52 +3.19 +0.76 | 12 5 12 0.7744 0.529 -0.377 6.425 -0.672 0.079 -0.831 0.321 -0.599 -1.047 -0.518 -0.238 -0.516 3.192 0.757 | agree | 0.48 |  |
| 899 | load-check.md L108 | W5b d11p vs d11, raw median ms, without each pass's round 1: n, higher k/n, sign p, mean %, median %, per-round % | 10 4/10 p 0.754 +0.10 -0.38 -0.67 +0.08 -0.83 +0.32 -0.60 -0.52 -0.24 -0.52 +3.19 +0.76 | 10 4 10 0.7539 0.097 -0.377 -0.672 0.079 -0.831 0.321 -0.599 -0.518 -0.238 -0.516 3.192 0.757 | agree | 0.35 |  |
| 900 | load-check.md L109 | W5b d11t vs d11, raw fps, all rounds: n, higher k/n, sign p, mean %, median %, per-round % | 12 3/12 p 0.146 -1.28 -0.47 -1.95 +0.44 -2.57 -0.23 -0.70 -0.16 -6.59 -2.23 -1.48 -0.18 +0.18 +0.05 | 12 3 12 0.1460 -1.278 -0.468 -1.940 0.441 -2.548 -0.230 -0.706 -0.142 -6.576 -2.218 -1.482 -0.182 0.198 0.043 / rounded inputs: 12 3 12 0.1460 -1.285 -0.468 -1.951 0.443 -2.569 -0.234 -0.701 -0.156 -6.590 -2.233 -1.481 -0.182 0.182 0.052 | agree (rounded inputs) | 0.50 |  |
| 901 | load-check.md L110 | W5b d11t vs d11, raw fps, without each pass's round 1: n, higher k/n, sign p, mean %, median %, per-round % | 10 3/10 p 0.344 -0.69 -0.21 +0.44 -2.57 -0.23 -0.70 -0.16 -2.23 -1.48 -0.18 +0.18 +0.05 | 10 3 10 0.3438 -0.683 -0.206 0.441 -2.548 -0.230 -0.706 -0.142 -2.218 -1.482 -0.182 0.198 0.043 / rounded inputs: 10 3 10 0.3438 -0.688 -0.208 0.443 -2.569 -0.234 -0.701 -0.156 -2.233 -1.481 -0.182 0.182 0.052 | agree (rounded inputs) | 0.44 |  |
| 902 | load-check.md L111 | W5b d11p vs d11, raw fps, all rounds: n, higher k/n, sign p, mean %, median %, per-round % | 12 7/12 p 0.774 -0.73 +0.04 -4.63 +0.23 +0.08 +0.16 +0.00 +0.13 -1.78 +0.05 +0.23 +0.03 -2.44 -0.80 | 12 7 12 0.7744 -0.724 0.040 -4.613 0.237 0.088 0.162 -0.000 0.130 -1.767 0.069 0.234 0.010 -2.452 -0.790 / rounded inputs: 12 7 12 0.7744 -0.729 0.039 -4.625 0.234 0.079 0.156 0.000 0.130 -1.781 0.052 0.234 0.026 -2.442 -0.805 | agree (rounded inputs) | 0.48 |  |
| 903 | load-check.md L112 | W5b d11p vs d11, raw fps, without each pass's round 1: n, higher k/n, sign p, mean %, median %, per-round % | 10 7/10 p 0.344 -0.23 +0.07 +0.23 +0.08 +0.16 +0.00 +0.13 +0.05 +0.23 +0.03 -2.44 -0.80 | 10 7 10 0.3438 -0.231 0.079 0.237 0.088 0.162 -0.000 0.130 0.069 0.234 0.010 -2.452 -0.790 / rounded inputs: 10 7 10 0.3438 -0.234 0.065 0.234 0.079 0.156 0.000 0.130 0.052 0.234 0.026 -2.442 -0.805 | agree (rounded inputs) | 0.48 |  |
| 904 | load-check.md L113 | W5b d11t vs d11, raw p99 ms, all rounds: n, higher k/n, sign p, mean %, median %, per-round % | 12 7/12 p 0.774 +1.18 +1.25 +1.76 +1.25 +4.08 +0.00 +2.25 -0.41 +1.83 +1.24 +5.24 -0.83 -1.85 -0.42 | 12 8 12 0.3877 1.172 1.175 1.802 1.189 4.122 0.062 2.151 -0.454 1.851 1.162 5.174 -0.976 -1.751 -0.270 / rounded inputs: 12 7 12 0.7744 1.179 1.249 1.758 1.253 4.082 0.000 2.254 -0.413 1.829 1.245 5.241 -0.832 -1.852 -0.416 | agree (rounded inputs) | 0.48 |  |
| 905 | load-check.md L114 | W5b d11t vs d11, raw p99 ms, without each pass's round 1: n, higher k/n, sign p, mean %, median %, per-round % | 10 5/10 p 1.000 +1.06 +0.62 +1.25 +4.08 +0.00 +2.25 -0.41 +1.24 +5.24 -0.83 -1.85 -0.42 | 10 6 10 0.7539 1.041 0.612 1.189 4.122 0.062 2.151 -0.454 1.162 5.174 -0.976 -1.751 -0.270 / rounded inputs: 10 5 10 1.0000 1.056 0.622 1.253 4.082 0.000 2.254 -0.413 1.245 5.241 -0.832 -1.852 -0.416 | agree (rounded inputs) | 0.48 |  |
| 906 | load-check.md L115 | W5b d11p vs d11, raw p99 ms, all rounds: n, higher k/n, sign p, mean %, median %, per-round % | 12 4/12 p 0.388 +0.07 -0.21 +3.74 -0.84 -2.04 -0.41 -0.20 -1.65 +0.00 -0.21 +0.63 +0.62 -0.21 +1.46 | 12 5 12 0.7744 0.075 -0.226 3.691 -0.960 -2.041 -0.308 -0.287 -1.632 0.102 -0.290 0.628 0.602 -0.165 1.560 / rounded inputs: 12 4 12 0.3877 0.074 -0.205 3.736 -0.835 -2.041 -0.411 -0.205 -1.653 0.000 -0.207 0.629 0.624 -0.206 1.455 | agree (rounded inputs) | 0.49 |  |
| 907 | load-check.md L116 | W5b d11p vs d11, raw p99 ms, without each pass's round 1: n, higher k/n, sign p, mean %, median %, per-round % | 10 3/10 p 0.344 -0.28 -0.21 -0.84 -2.04 -0.41 -0.20 -1.65 -0.21 +0.63 +0.62 -0.21 +1.46 | 10 3 10 0.3438 -0.289 -0.289 -0.960 -2.041 -0.308 -0.287 -1.632 -0.290 0.628 0.602 -0.165 1.560 / rounded inputs: 10 3 10 0.3438 -0.285 -0.207 -0.835 -2.041 -0.411 -0.205 -1.653 -0.207 0.629 0.624 -0.206 1.455 | agree (rounded inputs) | 0.50 |  |
| 908 | load-check.md L117 | W5b d11t vs d11, raw median ms, without rounds holding an audit-flagged run: n, higher k/n, sign p, mean %, median %, per-round % | 9 8/9 p 0.039 +0.73 +0.36 +2.58 -1.27 +0.24 +0.24 +1.08 +2.79 +0.04 +0.56 +0.36 | 9 8 9 0.0391 0.735 0.359 2.579 -1.266 0.238 0.241 1.078 2.787 0.040 0.559 0.359 | agree | 0.48 |  |
| 909 | load-check.md L118 | W5b d11t vs d11, raw fps, without rounds holding an audit-flagged run: n, higher k/n, sign p, mean %, median %, per-round % | 9 3/9 p 0.508 -0.53 -0.18 -1.95 +0.44 -0.23 -0.70 -0.16 -2.23 -0.18 +0.18 +0.05 | 9 3 9 0.5078 -0.526 -0.182 -1.940 0.441 -0.230 -0.706 -0.142 -2.218 -0.182 0.198 0.043 / rounded inputs: 9 3 9 0.5078 -0.531 -0.182 -1.951 0.443 -0.234 -0.701 -0.156 -2.233 -0.182 0.182 0.052 | agree (rounded inputs) | 0.44 |  |
| 910 | load-check.md L119 | W5b d11p vs d11, raw median ms, without rounds holding an audit-flagged run: n, higher k/n, sign p, mean %, median %, per-round % | 10 4/10 p 0.754 +0.73 -0.38 +6.42 -0.67 -0.83 +0.32 -0.60 -0.52 -0.24 -0.52 +3.19 +0.76 | 10 4 10 0.7539 0.732 -0.377 6.425 -0.672 -0.831 0.321 -0.599 -0.518 -0.238 -0.516 3.192 0.757 | agree | 0.48 |  |
| 911 | load-check.md L120 | W5b d11p vs d11, raw fps, without rounds holding an audit-flagged run: n, higher k/n, sign p, mean %, median %, per-round % | 10 6/10 p 0.754 -0.70 +0.04 -4.63 +0.23 +0.16 +0.00 +0.13 +0.05 +0.23 +0.03 -2.44 -0.80 | 10 6 10 0.7539 -0.701 0.040 -4.613 0.237 0.162 -0.000 0.130 0.069 0.234 0.010 -2.452 -0.790 / rounded inputs: 10 6 10 0.7539 -0.704 0.039 -4.625 0.234 0.156 0.000 0.130 0.052 0.234 0.026 -2.442 -0.805 | agree (rounded inputs) | 0.48 |  |
| 912 | load-check.md L122 | t critical values (35, 7, 11) | 2.0301 2.3646 2.2010 | 2.03011 2.36462 2.20099 | agree | 0.24 |  |

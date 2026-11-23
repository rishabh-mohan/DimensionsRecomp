# Pooled read-out: W5b

- title: Window 5b (Agent 8, run-2 task #7 follow-up): TimerQueue wait modes on devoff4 (S4a), all with the 8 timer cvars. d11 (spin wait) vs d11t (blocking wait, REX_TIMER_WAIT_BLOCKING=1) vs d11p (precise wait, timer_queue_precise_wait=true)
- pass 1: `<workspace>\build\agent8\matrix\20261123-0155` (19 rows; rounds 1-6 pooled; windows 01:56:33-02:32:59; results.csv sha256 5A08241AA965ADE4...)
- pass 2: `<workspace>\build\agent8\matrix\20261123-0451` (19 rows; rounds 7-12 pooled; windows 04:53:03-05:29:47; results.csv sha256 8C6CC5147A7470E2...)
- command: `python -B build\agent7\readout\pool_readout.py build/agent8/matrix/20261123-0155 build/agent8/matrix/20261123-0451 --label W5b --self-check --variant no-slow-d11t=0455-d11t-r1,0459-d11t-r2 --variant no-0221=0221-d11t-r5 --variant no-audit-flag=0209-d11p-r3,0213-d11t-r3,0453-d11-r1,0455-d11t-r1,0457-d11p-r1,0510-d11t-r3 --variant no-flagged=0209-d11p-r3,0213-d11t-r3,0453-d11-r1,0455-d11t-r1,0457-d11p-r1,0459-d11t-r2,0510-d11t-r3 --variant no-loaded=0209-d11p-r3,0213-d11t-r3,0453-d11-r1,0455-d11t-r1,0457-d11p-r1,0459-d11t-r2,0510-d11t-r3,0520-d11p-r5,0524-d11p-r6 --variant no-p2-first3=0453-d11-r1,0455-d11t-r1,0457-d11p-r1 --variant drop-p2-r1r2=p2:r1,p2:r2 --variant drop-r1-both=p1:r1,p2:r1 --variant pass1-only=p2 --variant pass2-only=p1 -o build/agent7/readout/pool-W5b.md --json build/agent7/readout/pool-W5b.json`
- ref **d11** (matrix.json arm "ref": true); arms d11t, d11p; pooled rounds 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12; kept 36 of 38 runs (d11 12, d11t 12, d11p 12); left out: 0155-cold-d11 (cold (unscored)); 0451-cold-d11 (cold (unscored)).
- T split: light = frame time < 4.5 ms; pooled hT_ref = 0.049; per pass 1: 0.051, 2: 0.048.
- G11 power: OK: overlay best_performance 38/38; scheme Balanced 38/38; AC 1 38/38; saver 0 38/38; no change inside any window; the overlay is not W5's best_efficiency, so compare arms within this window only, not with W5's absolute numbers
- self-check pass 1 (20261123-0155): PASS, 108 numbers, max |diff| 0, primary B-block T-std / B-block T-std
- self-check pass 2 (20261123-0451): PASS, 108 numbers, max |diff| 0, primary T-std / T-std

## 1. Runs per arm (PROPOSAL.md S3)

| arm | planned (+cold) | rows | timed | kept | failed | STUCK-LOCK episodes (runs; owner sites) | hang dumps | slow-state runs (onset; low rows in window) | host CPU at each hang |
|---|---|---|---|---|---|---|---|---|---|
| d11 | 12 (+2) | 14 | 12 | 12 | 0 | 0 | 0 | 0 | - |
| d11t | 12 (+0) | 12 | 12 | 12 | 0 | 0 | 0 | 0 | - |
| d11p | 12 (+0) | 12 | 12 | 12 | 0 | 0 | 0 | 0 | - |

## 2. Primary result (pooled)

- **Primary: B-block T-std.** Round effect on median ms: F = 4.11 on (11, 22), p = 0.002 < 0.05, so B-block T-std applies (df = runs - arms - rounds + 1); T-std is shown beside it.
- Round terms of B-block T-std vs round 1: median ms: round 2 +6.0 %, round 3 +7.8 %, round 4 +6.2 %, round 5 +5.1 %, round 6 +5.8 %, round 7 +6.4 %, round 8 +6.8 %, round 9 +6.3 %, round 10 +6.1 %, round 11 +7.0 %, round 12 +6.3 %; F = 4.11 on (11, 22), p = 0.002. fps: round 2 -4.4 %, round 3 -5.6 %, round 4 -4.4 %, round 5 -4.1 %, round 6 -4.2 %, round 7 -4.8 %, round 8 -5.0 %, round 9 -4.6 %, round 10 -4.4 %, round 11 -5.0 %, round 12 -4.5 %; F = 4.20 on (11, 22), p = 0.002.
- Pass term (one-way T-std + pass block): median ms F = 2.84 on (1, 32), p = 0.102; fps F = 2.79 on (1, 32), p = 0.105.
- Arm x pass (B-block + per-arm pass terms; does an arm's delta differ between the passes?): median ms F = 0.52 on (2, 20), p = 0.601; fps F = 0.50 on (2, 20), p = 0.612; p99 F = 1.25 on (2, 20), p = 0.308; 1 % low F = 1.05 on (2, 20), p = 0.370.

Cells: the GM delta vs d11 in %, with the pooled 95 % CI; `*` = the CI excludes 0. Bold = the primary.

| method | metric | d11 band % | pooled CV % | 4 vs 4 band % | df | d11t (n=12) | d11p (n=12) |
|---|---|---|---|---|---|---|---|
| T-std | median ms | 9.0 | 2.3 | 3.4 | 33 | +1.2 [-0.7, +3.1] | +0.5 [-1.4, +2.4] |
| **B-block T-std** | median ms | 3.3 | 1.6 | 2.4 | 22 | +1.2 [-0.2, +2.6] | +0.5 [-0.9, +1.9] |
| T-std | fps | 7.0 | 1.7 | 2.5 | 33 | -1.1 [-2.5, +0.4] | -0.7 [-2.2, +0.7] |
| **B-block T-std** | fps | 2.9 | 1.2 | 1.8 | 22 | -1.1 [-2.1, -0.0] * | -0.7 [-1.8, +0.3] |
| raw | median ms | 10.1 | 2.5 | 3.6 | 33 | +1.3 [-0.8, +3.4] | +0.5 [-1.5, +2.6] |
| raw | fps | 8.7 | 2.1 | 3.0 | 33 | -1.3 [-3.0, +0.4] | -0.7 [-2.4, +1.0] |

| method | metric | d11 band % | pooled CV % | 4 vs 4 band % | df | d11t (n=12) | d11p (n=12) |
|---|---|---|---|---|---|---|---|
| T-std | p99 ms | 4.0 | 1.0 | 1.4 | 33 | +0.3 [-0.5, +1.2] | +0.0 [-0.8, +0.8] |
| **B-block T-std** | p99 ms | 1.7 | 0.7 | 1.1 | 22 | +0.3 [-0.3, +1.0] | +0.0 [-0.6, +0.6] |
| T-std | 1 % low fps | 8.2 | 4.6 | 6.9 | 33 | -2.8 [-6.5, +1.0] | -0.2 [-4.0, +3.7] |
| **B-block T-std** | 1 % low fps | 11.6 | 4.5 | 6.9 | 22 | -2.8 [-6.5, +1.0] | -0.2 [-4.0, +3.7] |
| raw | p99 ms | 7.6 | 2.1 | 3.0 | 33 | +1.2 [-0.6, +2.9] | +0.1 [-1.6, +1.8] |
| raw | 1 % low fps | 12.1 | 5.8 | 8.7 | 33 | -3.9 [-8.4, +0.8] | -0.3 [-4.9, +4.6] |

## 3. CPU (process cores and thread busy)

Change = arm mean - d11 mean with the pooled 95 % CI (linear, df = runs - arms). GM % = GM delta with the pooled CI on ln (one-way, then B-block over the pooled rounds); `*` = the CI excludes 0.

| metric | d11 mean | d11t: mean; change [95 % CI]; GM % one-way; GM % B-block | d11p: mean; change [95 % CI]; GM % one-way; GM % B-block |
|---|---|---|---|
| cpu cores | 2.55 | 2.33; -0.22 [-0.25, -0.19]; -8.6 [-9.8, -7.4] *; -8.6 [-9.6, -7.6] * | 2.34; -0.20 [-0.23, -0.17]; -8.0 [-9.2, -6.8] *; -8.0 [-9.0, -7.0] * |
| GPU Commands busy % | 60.66 | 60.98; +0.32 [-1.29, +1.94]; +0.5 [-2.0, +3.2]; +0.5 [-1.0, +2.2] | 60.94; +0.28 [-1.33, +1.90]; +0.5 [-2.1, +3.1]; +0.5 [-1.1, +2.1] |
| Main XThread busy % | 80.66 | 80.26; -0.40 [-2.48, +1.68]; -0.5 [-3.0, +2.1]; -0.5 [-2.2, +1.3] | 79.88; -0.77 [-2.85, +1.30]; -0.9 [-3.4, +1.6]; -0.9 [-2.6, +0.8] |
| TimerQueue busy % | 23.17 | 1.97; -21.19 [-21.82, -20.56]; -91.5 [-92.3, -90.7] *; -91.5 [-92.2, -90.8] * | 2.08; -21.08 [-21.72, -20.45]; -91.1 [-91.8, -90.2] *; -91.1 [-91.7, -90.3] * |

## 4. Paired within-round deltas (pooled rounds)

Within-round deltas 100 (arm - d11) / d11, one per round in which both ran: mean +- 95 % t half-width (df = rounds - 1), median, and the rounds in which the arm was higher.

| metric | d11t | d11p |
|---|---|---|
| T-std median ms | +1.19 +- 1.26 (med +0.54; higher 9/12) | +0.52 +- 1.29 (med -0.20; higher 5/12) |
| T-std fps | -1.04 +- 1.13 (med -0.38; higher 2/12) | -0.73 +- 0.79 (med -0.18; higher 5/12) |
| raw median ms | +1.33 +- 1.31 (med +0.46; higher 11/12) | +0.53 +- 1.38 (med -0.38; higher 5/12) |
| raw fps | -1.28 +- 1.24 (med -0.47; higher 3/12) | -0.72 +- 0.96 (med +0.04; higher 7/12) |
| T-std p99 ms | +0.35 +- 0.66 (med +0.35; higher 7/12) | +0.01 +- 0.59 (med -0.06; higher 6/12) |
| T-std 1 % low fps | -2.56 +- 4.31 (med -0.37; higher 5/12) | -0.17 +- 1.55 (med -0.39; higher 5/12) |
| cpu cores | -8.62 +- 1.05 (med -8.90; higher 0/12) | -7.98 +- 1.16 (med -8.54; higher 0/12) |

## 5. Per pass (each pass alone, readout.py numbers)

Cells: the primary's GM delta [95 % CI] for median ms; fps; p99; 1 % low; then the cores change [95 % CI].

| pass | kept | primary (round test) | d11t: median ms; fps; p99; 1 % low; cores (change) | d11p: median ms; fps; p99; 1 % low; cores (change) |
|---|---|---|---|---|
| 1 | 18 | B-block T-std (p = 0.001) | +0.7 [-1.1, +2.6]; -0.6 [-1.8, +0.6]; +0.6 [-0.2, +1.4]; -5.1 [-12.1, +2.5]; -0.23 [-0.28, -0.18] | +0.8 [-1.1, +2.6]; -0.7 [-1.9, +0.5]; -0.2 [-1.0, +0.6]; -0.0 [-7.4, +7.9]; -0.20 [-0.25, -0.15] |
| 2 | 18 | T-std (p = 0.993) | +1.6 [-0.3, +3.6]; -1.5 [-3.0, +0.0]; +0.1 [-1.0, +1.3]; -0.6 [-3.8, +2.7]; -0.21 [-0.25, -0.17] | +0.3 [-1.6, +2.2]; -0.8 [-2.3, +0.8]; +0.3 [-0.9, +1.5]; -0.4 [-3.5, +2.9]; -0.20 [-0.25, -0.16] |

## 6. Variants (the pool without the listed runs)

**no-slow-d11t** (left out: 0455-d11t-r1, 0459-d11t-r2): primary B-block T-std; Round terms of B-block T-std vs round 1: median ms: round 2 +6.0 %, round 3 +7.9 %, round 4 +6.3 %, round 5 +5.1 %, round 6 +5.8 %, round 7 +4.1 %, round 8 +5.8 %, round 9 +6.3 %, round 10 +6.1 %, round 11 +7.0 %, round 12 +6.3 %; F = 7.77 on (11, 20), p = < 0.001. fps: round 2 -4.4 %, round 3 -5.6 %, round 4 -4.4 %, round 5 -4.1 %, round 6 -4.2 %, round 7 -3.0 %, round 8 -4.3 %, round 9 -4.6 %, round 10 -4.4 %, round 11 -5.0 %, round 12 -4.5 %; F = 9.58 on (11, 20), p = < 0.001.

| metric | d11t (n=10) | d11p (n=12) |
|---|---|---|
| B-block T-std median ms | +0.4 [-0.7, +1.5] | +0.5 [-0.5, +1.5] |
| B-block T-std fps | -0.4 [-1.2, +0.3] | -0.7 [-1.4, -0.1] * |
| B-block T-std p99 ms | +0.3 [-0.4, +1.0] | -0.0 [-0.7, +0.7] |
| B-block T-std 1 % low fps | -3.2 [-7.2, +1.0] | -0.2 [-4.1, +3.8] |
| raw median ms | +0.6 [-1.4, +2.7] | +0.5 [-1.4, +2.5] |
| raw fps | -0.7 [-2.4, +1.0] | -0.7 [-2.3, +0.9] |
| raw p99 ms | +0.9 [-0.9, +2.7] | +0.1 [-1.7, +1.8] |
| raw 1 % low fps | -4.1 [-9.0, +1.0] | -0.3 [-5.1, +4.8] |
| cpu cores change | -0.22 [-0.26, -0.19] | -0.20 [-0.24, -0.17] |

**no-0221** (left out: 0221-d11t-r5): primary B-block T-std; Round terms of B-block T-std vs round 1: median ms: round 2 +6.0 %, round 3 +7.9 %, round 4 +6.3 %, round 5 +5.4 %, round 6 +5.8 %, round 7 +6.4 %, round 8 +6.8 %, round 9 +6.3 %, round 10 +6.1 %, round 11 +7.0 %, round 12 +6.3 %; F = 3.96 on (11, 21), p = 0.003. fps: round 2 -4.4 %, round 3 -5.6 %, round 4 -4.4 %, round 5 -4.2 %, round 6 -4.2 %, round 7 -4.8 %, round 8 -5.0 %, round 9 -4.6 %, round 10 -4.4 %, round 11 -5.0 %, round 12 -4.5 %; F = 4.01 on (11, 21), p = 0.003.

| metric | d11t (n=11) | d11p (n=12) |
|---|---|---|
| B-block T-std median ms | +1.3 [-0.2, +2.7] | +0.5 [-0.9, +1.9] |
| B-block T-std fps | -1.1 [-2.2, +0.0] | -0.7 [-1.8, +0.3] |
| B-block T-std p99 ms | +0.3 [-0.4, +0.9] | -0.0 [-0.7, +0.6] |
| B-block T-std 1 % low fps | -0.8 [-2.5, +1.0] | -0.2 [-1.9, +1.5] |
| raw median ms | +1.4 [-0.7, +3.6] | +0.5 [-1.6, +2.6] |
| raw fps | -1.3 [-3.0, +0.5] | -0.7 [-2.5, +1.0] |
| raw p99 ms | +0.9 [-0.8, +2.7] | +0.1 [-1.6, +1.8] |
| raw 1 % low fps | -1.6 [-4.2, +1.1] | -0.3 [-2.9, +2.4] |
| cpu cores change | -0.22 [-0.25, -0.19] | -0.20 [-0.24, -0.17] |

**no-audit-flag** (left out: 0209-d11p-r3, 0213-d11t-r3, 0453-d11-r1, 0455-d11t-r1, 0457-d11p-r1, 0510-d11t-r3): primary B-block T-std; Round terms of B-block T-std vs round 1: median ms: round 2 +6.0 %, round 3 +7.4 %, round 4 +6.3 %, round 5 +5.1 %, round 6 +5.8 %, round 8 +6.8 %, round 9 +6.5 %, round 10 +6.1 %, round 11 +7.0 %, round 12 +6.3 %; F = 6.41 on (10, 17), p = < 0.001. fps: round 2 -4.4 %, round 3 -5.2 %, round 4 -4.4 %, round 5 -4.1 %, round 6 -4.2 %, round 8 -5.0 %, round 9 -4.5 %, round 10 -4.4 %, round 11 -5.0 %, round 12 -4.5 %; F = 7.61 on (10, 17), p = < 0.001.

| metric | d11t (n=9) | d11p (n=10) |
|---|---|---|
| B-block T-std median ms | +0.6 [-0.6, +1.9] | +0.7 [-0.5, +1.9] |
| B-block T-std fps | -0.4 [-1.3, +0.5] | -0.7 [-1.5, +0.1] |
| B-block T-std p99 ms | +0.1 [-0.6, +0.7] | +0.2 [-0.4, +0.8] |
| B-block T-std 1 % low fps | -2.8 [-7.4, +2.0] | -0.6 [-5.1, +4.1] |
| raw median ms | +0.4 [-1.8, +2.7] | +0.5 [-1.7, +2.7] |
| raw fps | -0.3 [-2.1, +1.5] | -0.6 [-2.3, +1.2] |
| raw p99 ms | +0.2 [-1.4, +1.8] | +0.1 [-1.5, +1.7] |
| raw 1 % low fps | -3.3 [-8.6, +2.3] | -0.5 [-5.8, +5.1] |
| cpu cores change | -0.22 [-0.26, -0.19] | -0.20 [-0.24, -0.17] |

**no-flagged** (left out: 0209-d11p-r3, 0213-d11t-r3, 0453-d11-r1, 0455-d11t-r1, 0457-d11p-r1, 0459-d11t-r2, 0510-d11t-r3): primary B-block T-std; Round terms of B-block T-std vs round 1: median ms: round 2 +6.0 %, round 3 +7.3 %, round 4 +6.3 %, round 5 +5.1 %, round 6 +5.8 %, round 8 +5.7 %, round 9 +6.4 %, round 10 +6.1 %, round 11 +7.0 %, round 12 +6.3 %; F = 7.03 on (10, 16), p = < 0.001. fps: round 2 -4.4 %, round 3 -5.1 %, round 4 -4.4 %, round 5 -4.1 %, round 6 -4.2 %, round 8 -4.3 %, round 9 -4.4 %, round 10 -4.4 %, round 11 -5.0 %, round 12 -4.5 %; F = 8.85 on (10, 16), p = < 0.001.

| metric | d11t (n=8) | d11p (n=10) |
|---|---|---|
| B-block T-std median ms | +0.3 [-0.9, +1.6] | +0.7 [-0.4, +1.9] |
| B-block T-std fps | -0.2 [-1.0, +0.7] | -0.7 [-1.5, +0.0] |
| B-block T-std p99 ms | -0.1 [-0.7, +0.6] | +0.2 [-0.4, +0.8] |
| B-block T-std 1 % low fps | -2.9 [-7.8, +2.3] | -0.6 [-5.3, +4.2] |
| raw median ms | +0.0 [-2.3, +2.3] | +0.5 [-1.6, +2.7] |
| raw fps | +0.0 [-1.8, +1.9] | -0.6 [-2.3, +1.2] |
| raw p99 ms | +0.0 [-1.7, +1.7] | +0.1 [-1.5, +1.7] |
| raw 1 % low fps | -3.5 [-9.0, +2.4] | -0.5 [-5.9, +5.2] |
| cpu cores change | -0.23 [-0.26, -0.19] | -0.20 [-0.24, -0.17] |

**no-loaded** (left out: 0209-d11p-r3, 0213-d11t-r3, 0453-d11-r1, 0455-d11t-r1, 0457-d11p-r1, 0459-d11t-r2, 0510-d11t-r3, 0520-d11p-r5, 0524-d11p-r6): primary B-block T-std; Round terms of B-block T-std vs round 1: median ms: round 2 +6.1 %, round 3 +7.3 %, round 4 +6.3 %, round 5 +5.1 %, round 6 +5.8 %, round 8 +5.8 %, round 9 +6.5 %, round 10 +6.1 %, round 11 +6.1 %, round 12 +6.2 %; F = 6.87 on (10, 14), p = < 0.001. fps: round 2 -4.4 %, round 3 -5.0 %, round 4 -4.4 %, round 5 -4.1 %, round 6 -4.2 %, round 8 -4.3 %, round 9 -4.4 %, round 10 -4.4 %, round 11 -4.3 %, round 12 -4.4 %; F = 9.85 on (10, 14), p = < 0.001.

| metric | d11t (n=8) | d11p (n=8) |
|---|---|---|
| B-block T-std median ms | +0.3 [-0.9, +1.6] | +0.4 [-0.8, +1.7] |
| B-block T-std fps | -0.2 [-1.0, +0.6] | -0.5 [-1.2, +0.3] |
| B-block T-std p99 ms | -0.1 [-0.7, +0.6] | -0.0 [-0.7, +0.6] |
| B-block T-std 1 % low fps | -3.0 [-8.1, +2.3] | +0.5 [-4.8, +6.0] |
| raw median ms | +0.0 [-2.3, +2.4] | +0.0 [-2.3, +2.4] |
| raw fps | +0.0 [-1.8, +1.9] | -0.2 [-2.0, +1.7] |
| raw p99 ms | +0.0 [-1.7, +1.8] | -0.2 [-1.9, +1.6] |
| raw 1 % low fps | -3.5 [-9.2, +2.7] | +0.3 [-5.7, +6.6] |
| cpu cores change | -0.23 [-0.26, -0.19] | -0.21 [-0.25, -0.18] |

**no-p2-first3** (left out: 0453-d11-r1, 0455-d11t-r1, 0457-d11p-r1): primary B-block T-std; Round terms of B-block T-std vs round 1: median ms: round 2 +6.0 %, round 3 +7.9 %, round 4 +6.3 %, round 5 +5.1 %, round 6 +5.8 %, round 8 +6.8 %, round 9 +6.3 %, round 10 +6.1 %, round 11 +7.0 %, round 12 +6.3 %; F = 7.75 on (10, 20), p = < 0.001. fps: round 2 -4.4 %, round 3 -5.6 %, round 4 -4.4 %, round 5 -4.1 %, round 6 -4.2 %, round 8 -5.0 %, round 9 -4.6 %, round 10 -4.4 %, round 11 -5.0 %, round 12 -4.5 %; F = 8.83 on (10, 20), p = < 0.001.

| metric | d11t (n=11) | d11p (n=11) |
|---|---|---|
| B-block T-std median ms | +0.7 [-0.4, +1.8] | +0.7 [-0.4, +1.8] |
| B-block T-std fps | -0.6 [-1.4, +0.2] | -0.7 [-1.5, +0.1] |
| B-block T-std p99 ms | +0.4 [-0.3, +1.0] | +0.1 [-0.5, +0.8] |
| B-block T-std 1 % low fps | -3.3 [-7.2, +0.7] | -0.7 [-4.6, +3.5] |
| raw median ms | +0.8 [-1.3, +3.0] | +0.7 [-1.4, +2.8] |
| raw fps | -0.8 [-2.5, +0.9] | -0.6 [-2.4, +1.1] |
| raw p99 ms | +1.1 [-0.7, +2.9] | +0.1 [-1.7, +1.9] |
| raw 1 % low fps | -4.4 [-9.2, +0.7] | -0.6 [-5.6, +4.6] |
| cpu cores change | -0.22 [-0.25, -0.19] | -0.20 [-0.23, -0.17] |

**drop-p2-r1r2** (left out: p2:r1, p2:r2): primary B-block T-std; Round terms of B-block T-std vs round 1: median ms: round 2 +6.0 %, round 3 +7.8 %, round 4 +6.2 %, round 5 +5.1 %, round 6 +5.8 %, round 9 +6.3 %, round 10 +6.1 %, round 11 +7.0 %, round 12 +6.3 %; F = 9.11 on (9, 18), p = < 0.001. fps: round 2 -4.4 %, round 3 -5.6 %, round 4 -4.4 %, round 5 -4.1 %, round 6 -4.2 %, round 9 -4.6 %, round 10 -4.4 %, round 11 -5.0 %, round 12 -4.5 %; F = 10.46 on (9, 18), p = < 0.001.

| metric | d11t (n=10) | d11p (n=10) |
|---|---|---|
| B-block T-std median ms | +0.5 [-0.6, +1.6] | +0.8 [-0.3, +1.9] |
| B-block T-std fps | -0.4 [-1.2, +0.3] | -0.8 [-1.5, +0.0] |
| B-block T-std p99 ms | +0.3 [-0.4, +1.1] | +0.1 [-0.6, +0.9] |
| B-block T-std 1 % low fps | -3.4 [-7.8, +1.1] | -0.7 [-5.1, +4.0] |
| raw median ms | +0.7 [-1.6, +3.0] | +0.8 [-1.5, +3.1] |
| raw fps | -0.7 [-2.5, +1.2] | -0.7 [-2.6, +1.2] |
| raw p99 ms | +1.1 [-0.9, +3.1] | +0.1 [-1.9, +2.1] |
| raw 1 % low fps | -4.6 [-9.9, +1.1] | -0.7 [-6.2, +5.2] |
| cpu cores change | -0.22 [-0.25, -0.19] | -0.19 [-0.23, -0.16] |

**drop-r1-both** (left out: p1:r1, p2:r1): primary T-std; Round terms of B-block T-std vs round 2: median ms: round 3 +1.7 %, round 4 +0.2 %, round 5 -0.9 %, round 6 -0.2 %, round 8 +0.7 %, round 9 +0.3 %, round 10 +0.0 %, round 11 +0.9 %, round 12 +0.2 %; F = 1.61 on (9, 18), p = 0.186. fps: round 3 -1.2 %, round 4 +0.0 %, round 5 +0.4 %, round 6 +0.3 %, round 8 -0.6 %, round 9 -0.2 %, round 10 +0.1 %, round 11 -0.6 %, round 12 -0.1 %; F = 1.32 on (9, 18), p = 0.294.

| metric | d11t (n=10) | d11p (n=10) |
|---|---|---|
| T-std median ms | +0.6 [-0.4, +1.5] | +0.2 [-0.8, +1.1] |
| T-std fps | -0.5 [-1.2, +0.2] | -0.4 [-1.1, +0.3] |
| T-std p99 ms | +0.4 [-0.3, +1.1] | +0.1 [-0.7, +0.8] |
| T-std 1 % low fps | -3.7 [-7.9, +0.7] | -0.6 [-4.9, +4.0] |
| raw median ms | +0.7 [-0.3, +1.7] | +0.1 [-0.9, +1.1] |
| raw fps | -0.7 [-1.5, +0.1] | -0.2 [-1.0, +0.6] |
| raw p99 ms | +1.0 [-0.4, +2.4] | -0.3 [-1.7, +1.1] |
| raw 1 % low fps | -4.7 [-9.7, +0.7] | -0.3 [-5.5, +5.3] |
| cpu cores change | -0.22 [-0.25, -0.19] | -0.21 [-0.24, -0.18] |

**pass1-only** (left out: p2): primary B-block T-std; Round terms of B-block T-std vs round 1: median ms: round 2 +6.0 %, round 3 +7.8 %, round 4 +6.2 %, round 5 +5.1 %, round 6 +5.8 %; F = 10.14 on (5, 10), p = 0.001. fps: round 2 -4.4 %, round 3 -5.6 %, round 4 -4.4 %, round 5 -4.1 %, round 6 -4.2 %; F = 13.69 on (5, 10), p = < 0.001.

| metric | d11t (n=6) | d11p (n=6) |
|---|---|---|
| B-block T-std median ms | +0.7 [-1.1, +2.6] | +0.8 [-1.1, +2.6] |
| B-block T-std fps | -0.6 [-1.8, +0.6] | -0.7 [-1.9, +0.5] |
| B-block T-std p99 ms | +0.6 [-0.2, +1.4] | -0.2 [-1.0, +0.6] |
| B-block T-std 1 % low fps | -5.1 [-12.1, +2.5] | -0.0 [-7.4, +7.9] |
| raw median ms | +0.9 [-3.0, +4.9] | +0.8 [-3.1, +4.8] |
| raw fps | -0.9 [-4.0, +2.4] | -0.7 [-3.8, +2.6] |
| raw p99 ms | +1.5 [-1.7, +4.7] | -0.3 [-3.4, +2.9] |
| raw 1 % low fps | -6.4 [-14.8, +2.9] | -0.0 [-9.0, +9.9] |
| cpu cores change | -0.23 [-0.28, -0.18] | -0.20 [-0.25, -0.15] |

**pass2-only** (left out: p1): primary T-std; Round terms of B-block T-std vs round 7: median ms: round 8 +0.3 %, round 9 -0.1 %, round 10 -0.3 %, round 11 +0.5 %, round 12 -0.1 %; F = 0.09 on (5, 10), p = 0.993. fps: round 8 -0.2 %, round 9 +0.2 %, round 10 +0.5 %, round 11 -0.2 %, round 12 +0.3 %; F = 0.09 on (5, 10), p = 0.991.

| metric | d11t (n=6) | d11p (n=6) |
|---|---|---|
| T-std median ms | +1.6 [-0.3, +3.6] | +0.3 [-1.6, +2.2] |
| T-std fps | -1.5 [-3.0, +0.0] | -0.8 [-2.3, +0.8] |
| T-std p99 ms | +0.1 [-1.0, +1.3] | +0.3 [-0.9, +1.5] |
| T-std 1 % low fps | -0.6 [-3.8, +2.7] | -0.4 [-3.5, +2.9] |
| raw median ms | +1.7 [-0.2, +3.7] | +0.3 [-1.6, +2.2] |
| raw fps | -1.7 [-3.4, -0.1] * | -0.8 [-2.4, +0.9] |
| raw p99 ms | +0.8 [-1.1, +2.8] | +0.4 [-1.5, +2.4] |
| raw 1 % low fps | -1.4 [-5.3, +2.6] | -0.5 [-4.4, +3.6] |
| cpu cores change | -0.21 [-0.25, -0.17] | -0.20 [-0.25, -0.16] |

## 7. Guards (pooled)

- (a) Light share per arm: d11 0.974, d11t 0.972, d11p 0.975. One-way F = 1.18 on (2, 33), p = 0.320: OK.
- (b) Raw CI vs the B-block T-std CI (overlap = agrees): median ms: d11t agrees, d11p agrees; fps: d11t agrees, d11p agrees.
- (c) Host flag (sys.json window P util >= 90 % and E MHz < 600): 0 of 36 kept runs.

## 8. Runs (pooled order; host state over the measured window)

Main / GPU / TQ % = threads.csv busy % of Main XThread, GPU Commands and rex::thread::TimerQueue. eff / P / E MHz and util = sys.json window means. Low E rows = sys.csv rows in the window with E-core MHz < 800 (onset = Agent 11's slow-state onset from the first frame, - = none).

| seq | pass | round | arm | run | window start | kept | frames | raw median ms | T-std median ms | raw fps | raw p99 ms | cores | Main % | GPU % | TQ % | eff MHz | P MHz | E MHz | P util % | E util % | low E rows in window (onset s) | STUCK | light share | flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | cold | d11 | 0155-cold-d11 | 01:56:33 | no: cold (unscored) | 12571 | 2.306 | 2.321 | 419.0 | 4.66 | 2.54 | - | - | - | 2014 | 2016 | 2012 | 66.1 | 40.9 | 0/30 (-) |  | 0.983 |  |
| 2 | 1 | 1 | d11 | 0157-d11-r1 | 01:58:15 | yes | 20755 | 2.288 | 2.310 | 415.1 | 4.55 | 2.46 | 83.1 | 61.1 | 22.6 | 1989 | 1976 | 1995 | 63.2 | 41.0 | 0/50 (-) |  | 0.988 |  |
| 3 | 1 | 1 | d11t | 0159-d11t-r1 | 02:00:18 | yes | 20353 | 2.347 | 2.361 | 407.0 | 4.63 | 2.29 | 82.4 | 61.6 | 1.8 | 1963 | 1964 | 1961 | 61.5 | 40.3 | 0/50 (-) |  | 0.984 |  |
| 4 | 1 | 1 | d11p | 0201-d11p-r1 | 02:02:20 | yes | 19798 | 2.435 | 2.444 | 395.9 | 4.72 | 2.32 | 79.0 | 60.6 | 2.3 | 1959 | 1959 | 1955 | 60.9 | 38.9 | 0/50 (-) |  | 0.979 |  |
| 5 | 1 | 2 | d11t | 0203-d11t-r2 | 02:04:23 | yes | 19285 | 2.496 | 2.494 | 385.7 | 4.85 | 2.29 | 78.1 | 59.0 | 2.2 | 1988 | 1992 | 1984 | 61.6 | 38.0 | 0/50 (-) |  | 0.971 |  |
| 6 | 1 | 2 | d11p | 0205-d11p-r2 | 02:06:25 | yes | 19246 | 2.511 | 2.516 | 384.9 | 4.75 | 2.38 | 79.0 | 60.9 | 2.1 | 1928 | 1930 | 1926 | 61.8 | 40.0 | 0/49 (-) |  | 0.977 |  |
| 7 | 1 | 2 | d11 | 0207-d11-r2 | 02:08:28 | yes | 19201 | 2.528 | 2.532 | 384.0 | 4.79 | 2.52 | 81.4 | 58.9 | 22.0 | 1952 | 1937 | 1962 | 62.0 | 43.7 | 0/50 (-) |  | 0.976 |  |
| 8 | 1 | 3 | d11p | 0209-d11p-r3 | 02:10:30 | yes | 19091 | 2.544 | 2.546 | 381.8 | 4.80 | 2.37 | 81.1 | 62.6 | 1.9 | 1854 | 1838 | 1861 | 59.2 | 44.9 | 0/50 (-) |  | 0.976 |  |
| 9 | 1 | 3 | d11 | 0211-d11-r3 | 02:12:33 | yes | 19074 | 2.542 | 2.536 | 381.5 | 4.90 | 2.59 | 79.2 | 61.2 | 25.0 | 1953 | 1944 | 1957 | 62.6 | 43.1 | 0/50 (-) |  | 0.970 |  |
| 10 | 1 | 3 | d11t | 0213-d11t-r3 | 02:14:35 | yes | 18588 | 2.606 | 2.589 | 371.7 | 5.10 | 2.39 | 83.3 | 63.9 | 2.1 | 1829 | 1810 | 1838 | 60.3 | 47.3 | 0/50 (-) |  | 0.962 |  |
| 11 | 1 | 4 | d11 | 0215-d11-r4 | 02:16:38 | yes | 19211 | 2.526 | 2.523 | 384.2 | 4.87 | 2.58 | 79.8 | 61.2 | 23.9 | 1950 | 1955 | 1949 | 64.2 | 42.0 | 0/50 (-) |  | 0.972 |  |
| 12 | 1 | 4 | d11t | 0217-d11t-r4 | 02:18:40 | yes | 19167 | 2.532 | 2.531 | 383.3 | 4.87 | 2.29 | 79.4 | 60.6 | 1.9 | 1928 | 1921 | 1930 | 60.5 | 42.1 | 0/50 (-) |  | 0.973 |  |
| 13 | 1 | 4 | d11p | 0219-d11p-r4 | 02:20:43 | yes | 19243 | 2.505 | 2.503 | 384.8 | 4.85 | 2.33 | 80.6 | 60.2 | 1.7 | 1946 | 1938 | 1948 | 62.5 | 39.3 | 0/50 (-) |  | 0.973 |  |
| 14 | 1 | 5 | d11t | 0221-d11t-r5 | 02:22:47 | yes | 19119 | 2.498 | 2.492 | 382.4 | 4.99 | 2.31 | 78.5 | 60.6 | 2.1 | 1956 | 1952 | 1955 | 61.5 | 39.8 | 0/50 (-) |  | 0.972 |  |
| 15 | 1 | 5 | d11p | 0223-d11p-r5 | 02:24:49 | yes | 19254 | 2.500 | 2.495 | 385.1 | 4.87 | 2.32 | 79.5 | 58.7 | 2.5 | 1950 | 1935 | 1955 | 62.1 | 38.6 | 0/50 (-) |  | 0.970 |  |
| 16 | 1 | 5 | d11 | 0225-d11-r5 | 02:26:52 | yes | 19254 | 2.492 | 2.488 | 385.1 | 4.88 | 2.54 | 80.2 | 59.6 | 24.0 | 1952 | 1953 | 1952 | 63.4 | 42.0 | 0/50 (-) |  | 0.970 |  |
| 17 | 1 | 6 | d11p | 0227-d11p-r6 | 02:28:54 | yes | 19309 | 2.489 | 2.493 | 386.2 | 4.76 | 2.30 | 79.6 | 60.8 | 2.1 | 1945 | 1939 | 1946 | 61.1 | 39.5 | 0/50 (-) |  | 0.977 |  |
| 18 | 1 | 6 | d11 | 0229-d11-r6 | 02:30:57 | yes | 19284 | 2.504 | 2.502 | 385.7 | 4.84 | 2.54 | 81.2 | 59.8 | 23.9 | 1951 | 1936 | 1959 | 63.2 | 42.0 | 0/50 (-) |  | 0.972 |  |
| 19 | 1 | 6 | d11t | 0231-d11t-r6 | 02:32:59 | yes | 19257 | 2.531 | 2.532 | 385.1 | 4.82 | 2.29 | 77.7 | 57.4 | 1.8 | 1969 | 1961 | 1972 | 61.1 | 39.4 | 0/50 (-) |  | 0.974 |  |
| 20 | 2 | cold | d11 | 0451-cold-d11 | 04:53:03 | no: cold (unscored) | 13255 | 2.094 | 2.106 | 441.8 | 4.61 | 2.48 | - | - | - | 1974 | 1963 | 1979 | 63.2 | 41.8 | 0/30 (-) |  | 0.987 |  |
| 21 | 2 | 7 | d11 | 0453-d11-r1 | 04:54:46 | yes | 19649 | 2.483 | 2.484 | 393.0 | 4.92 | 2.60 | 88.8 | 67.3 | 25.3 | 1848 | 1818 | 1866 | 65.7 | 50.6 | 0/50 (-) |  | 0.976 |  |
| 22 | 2 | 7 | d11t | 0455-d11t-r1 | 04:56:51 | yes | 18357 | 2.647 | 2.639 | 367.1 | 5.01 | 2.37 | 85.8 | 65.4 | 2.5 | 1873 | 1861 | 1882 | 63.5 | 47.8 | 0/50 (-) |  | 0.966 |  |
| 23 | 2 | 7 | d11p | 0457-d11p-r1 | 04:58:54 | yes | 19302 | 2.457 | 2.450 | 386.0 | 4.92 | 2.37 | 84.1 | 63.8 | 2.4 | 1780 | 1786 | 1776 | 58.5 | 52.2 | 0/50 (-) |  | 0.969 |  |
| 24 | 2 | 8 | d11t | 0459-d11t-r2 | 05:00:58 | yes | 18832 | 2.582 | 2.581 | 376.6 | 4.88 | 2.34 | 83.2 | 61.1 | 1.5 | 1937 | 1928 | 1941 | 61.7 | 43.4 | 0/50 (-) |  | 0.972 |  |
| 25 | 2 | 8 | d11p | 0501-d11p-r2 | 05:03:01 | yes | 19273 | 2.499 | 2.501 | 385.4 | 4.81 | 2.27 | 78.4 | 59.2 | 1.8 | 1973 | 1969 | 1972 | 62.3 | 38.4 | 0/50 (-) |  | 0.975 |  |
| 26 | 2 | 8 | d11 | 0504-d11-r2 | 05:05:05 | yes | 19259 | 2.512 | 2.512 | 385.2 | 4.82 | 2.54 | 79.7 | 59.5 | 21.7 | 1982 | 1978 | 1984 | 62.7 | 42.7 | 0/50 (-) |  | 0.974 |  |
| 27 | 2 | 9 | d11p | 0506-d11p-r3 | 05:07:08 | yes | 19295 | 2.515 | 2.522 | 385.9 | 4.80 | 2.35 | 79.2 | 60.0 | 2.2 | 1942 | 1937 | 1943 | 60.3 | 40.8 | 0/50 (-) |  | 0.978 |  |
| 28 | 2 | 9 | d11 | 0508-d11-r3 | 05:09:12 | yes | 19251 | 2.521 | 2.523 | 385.0 | 4.77 | 2.59 | 77.9 | 59.6 | 22.3 | 1957 | 1947 | 1962 | 62.5 | 42.7 | 0/50 (-) |  | 0.975 |  |
| 29 | 2 | 9 | d11t | 0510-d11t-r3 | 05:11:16 | yes | 18965 | 2.528 | 2.516 | 379.3 | 5.02 | 2.31 | 79.3 | 60.8 | 2.2 | 1916 | 1912 | 1917 | 62.6 | 42.2 | 0/50 (-) |  | 0.966 |  |
| 30 | 2 | 10 | d11 | 0512-d11-r4 | 05:13:19 | yes | 19271 | 2.517 | 2.520 | 385.4 | 4.81 | 2.57 | 78.2 | 60.0 | 22.0 | 1967 | 1954 | 1974 | 62.4 | 42.8 | 0/50 (-) |  | 0.975 |  |
| 31 | 2 | 10 | d11t | 0514-d11t-r4 | 05:15:23 | yes | 19236 | 2.518 | 2.519 | 384.7 | 4.77 | 2.34 | 79.1 | 60.4 | 2.1 | 1982 | 1986 | 1978 | 62.2 | 39.2 | 0/50 (-) |  | 0.974 |  |
| 32 | 2 | 10 | d11p | 0516-d11p-r4 | 05:17:26 | yes | 19273 | 2.504 | 2.505 | 385.5 | 4.84 | 2.38 | 78.1 | 61.3 | 1.8 | 1962 | 1959 | 1961 | 62.6 | 38.8 | 0/50 (-) |  | 0.975 |  |
| 33 | 2 | 11 | d11t | 0518-d11t-r5 | 05:19:30 | yes | 19288 | 2.520 | 2.521 | 385.7 | 4.77 | 2.36 | 79.1 | 60.5 | 1.7 | 1967 | 1963 | 1965 | 63.1 | 39.2 | 0/50 (-) |  | 0.974 |  |
| 34 | 2 | 11 | d11p | 0520-d11p-r5 | 05:21:33 | yes | 18778 | 2.586 | 2.586 | 375.6 | 4.85 | 2.38 | 80.9 | 60.4 | 2.1 | 1906 | 1893 | 1912 | 63.3 | 42.4 | 0/50 (-) |  | 0.972 |  |
| 35 | 2 | 11 | d11 | 0522-d11-r5 | 05:23:37 | yes | 19250 | 2.506 | 2.505 | 385.0 | 4.86 | 2.54 | 78.6 | 59.5 | 23.5 | 1989 | 1987 | 1992 | 63.8 | 41.1 | 0/50 (-) |  | 0.972 |  |
| 36 | 2 | 12 | d11p | 0524-d11p-r6 | 05:25:40 | yes | 19108 | 2.529 | 2.529 | 382.1 | 4.88 | 2.37 | 79.1 | 62.8 | 2.1 | 1901 | 1897 | 1902 | 61.2 | 43.0 | 0/50 (-) |  | 0.973 |  |
| 37 | 2 | 12 | d11 | 0526-d11-r6 | 05:27:44 | yes | 19260 | 2.510 | 2.510 | 385.2 | 4.81 | 2.51 | 79.8 | 60.2 | 21.8 | 1966 | 1952 | 1975 | 64.1 | 41.7 | 0/50 (-) |  | 0.973 |  |
| 38 | 2 | 12 | d11t | 0528-d11t-r6 | 05:29:47 | yes | 19268 | 2.519 | 2.521 | 385.4 | 4.79 | 2.37 | 77.2 | 60.5 | 1.8 | 1965 | 1965 | 1963 | 62.2 | 39.3 | 0/50 (-) |  | 0.975 |  |


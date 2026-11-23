# W5b formal read-out: TimerQueue wait modes (d11 / d11t / d11p) on devoff4 (S4a)

Agent 7, 2026-11-23 (task #21). Format: `build/agent8/w-followup/PROPOSAL.md` section 3 (counts per arm; every verdict with and without the flagged runs). All inputs were read-only, and nothing was re-run. Rev 1 (Nov 23, ~07:45) applies the 11 fixes from the independent check (`check/CHECK-W5b.md`) and one slip found by Agent 8's recompute (section 10).

## Window and inputs

- **Arms** (matrix.json, sha256 prefix 23575AAAE9DCBB85 in both folders; proof in `build/agent6/wnight/RESULTS.md`, arms at L38):
  - **d11** (ref): spin wait in the TimerQueue thread (the S4a default).
  - **d11t**: env `REX_TIMER_WAIT_BLOCKING=1` (blocking wait). It logs no line of its own. run.json env_set matches matrix.json, with 0 mismatches (L57).
  - **d11p**: cvar `timer_queue_precise_wait=true` (precise wait). It logs `TimerQueue: precise wait (timer_queue_precise_wait)` once per d11p run, and the line appears 0 times in d11 and d11t (L55).
  - All arms run devoff4 (S4a) with `framerate_limit=0` and the 8 timer cvars: `host_timer_resolution_ms=1`, `host_timer_throttling_optout`, `precise_guest_sleep`, `wait_timeout_round_up`, `cs_spin`, `spinlock_pause_spin`, `clock_lockfree`, `tls_bounds_fix`. `Host timer resolution set to 1 ms (background opt-out on)` appears once per run in every arm (L56).
- **Passes:** the same matrix ran twice. The pool numbers its rounds 1-6 (pass 1) and 7-12 (pass 2).

| pass | folder | measured windows | results.csv sha256 (prefix) |
|---|---|---|---|
| 1 (W5b-1) | `build/agent8/matrix/20261123-0155` | 01:56:33-02:32:59 | 5A08241AA965ADE4 |
| 2 (W5b-2) | `build/agent8/matrix/20261123-0451` | 04:53:03-05:29:47 | 8C6CC5147A7470E2 |

- **Host state:**
  - G11 overlay: power overlay best_performance in 38 of 38 runs, scheme Balanced, AC, saver off, with no change inside any window.
  - The Defender exclusion for `build/` was in place (it was added ~23:16 on Nov 22; `perf-notes/SESSION2.md` L3171-3173).
- **Sources:**
  - `build/agent7/readout/pool-W5b.md` (+ `.json`) comes from `pool_readout.py`, with both passes pooled. Its self-check re-runs `readout.py` on each pass: PASS, 108 numbers each, max |diff| 0. The command is in its header.
  - `build/agent7/readout/load-check.md` (`load_check.py`): the loaded-run table, cores differences, paired sign counts and Spearman (W5b part: L70-122).
  - `build/agent7/readout/tail-check.md` (`tail_check.py`): long frames per run and per arm. Its median, p99, p99.9 and max match frames.json in 36 of 36 runs.
  - `build/agent7/readout/cluster-0221.txt` (`cluster_0221.py`): perf.csv, gpu.csv, proc.csv, sys.csv and game.log around the 0221-d11t-r5 cluster.
  - Agent 8's audit, `build/agent8/readout/w-followup/audit/audit.md` (the version written at 06:38; line numbers refer to it):
    - flags at L17 (W5b-1) and L21 (W5b-2);
    - the CrossDeviceService holdback at L30-37 and L416-450;
    - per-run host load, where ng_t = non-game busy cores (window mean): W5b-1 at L240-265, W5b-2 at L346-371.
  - The runner's summaries: `summary.md` L12-14 in each folder.
  - Agent 6's logdiffs: `build/agent6/wnight/RESULTS.md`.
  - The quiet gate: `perf-notes/SESSION2.md` L2260 (rule) and L3291 (the W5b-2 holdback).
- **Agreement:**
  - The B-block rows are identical to Agent 8's `build/agent8/readout/w-followup/a7/W5b-pool.md` (L27, L29, L36, L38; same tool, run on Agent 8's merged folder).
  - The cores, paired fps and p99.9 figures match Agent 8's `build/agent8/readout/w-followup/mine/W5b.md` (L27-28, L40-41).

## Verdicts

| question | verdict | all 36 kept runs | without the 7 flagged runs |
|---|---|---|---|
| Which wait mode? | **d11p, narrowly** (over d11t; both save CPU vs d11) | Both cut ~0.2 core: d11t -0.22 [-0.25, -0.19] (-8.6 % *), d11p -0.20 [-0.23, -0.17] (-8.0 % *). d11t: B-block fps -1.1 % [-2.1, -0.0] *, raw median ms higher in 11 of 12 rounds, and the window's only stutter cluster (0221-d11t-r5). d11p: fps -0.7 [-1.8, +0.3], p99 +0.0, 1 % low -0.2, with no consistent per-round cost. | The frames don't separate the arms: fps d11t -0.2 [-1.0, +0.7], d11p -0.7 [-1.5, +0.0]. The pick then rests on the loaded runs themselves (d11t lost -3.0 % fps vs d11p -1.1 % at similar load, n = 4 each; post hoc and n.s.: gap -1.9 points, Welch 95 % CI [-4.1, +0.3], p 0.083) and on 0221, which isn't flagged. |
| Runner's numbers (pass 2) | **agree** | d11p -0.20 core (-0.2045; the runner's -0.21 is 2.35 - 2.56 from rounded means), fps +0.07 %. d11t -0.21 core, fps -0.83 %. | The runner's slow d11t r1-r2 (0455, 0459) are both flagged. d11t's 3 quiet pass-2 runs ran at 384.7-385.7 fps, level with d11's (385.0-385.4). |
| W5's d11t tail lead | **not reproduced** | p99 +0.3 % [-0.3, +1.0] (W5: +8.2 % [+0.5, +16.6]). 1 % low -2.8 [-6.5, +1.0] (W5: -7.7 %), most of it from one run: -0.8 [-2.5, +1.0] without 0221. The CPU saving is reproduced, smaller (-8.6 % vs d11; W5: -13.7 % vs base, about -14.5 % vs d11). | p99 -0.1 [-0.7, +0.6]. 1 % low -2.9 [-7.8, +2.3] (0221 stays in). |
| W5b-2's quiet gate | **it worked at the start only** | It held W5b-2 back 3 min for a CrossDeviceService spike (0.68-0.87 core) and then passed. Load rose again ~6 min after the holdback (source unknown), during the first scored run, and hit the first 4 scored runs (ng_t 2.84-3.76). | All 4 are flagged. Without them, no verdict changes. |

`*` = the 95 % CI excludes 0. Deltas are vs d11 unless a row says otherwise.

## 1. Runs (PROPOSAL section 3)

| arm | planned (+cold) | timed | kept | failed | STUCK-LOCK | hang dumps | slow-state runs | host CPU at each hang |
|---|---|---|---|---|---|---|---|---|
| d11 | 12 (+2) | 12 | 12 | 0 | 0 | 0 | 0 | - |
| d11t | 12 | 12 | 12 | 0 | 0 | 0 | 0 | - |
| d11p | 12 | 12 | 12 | 0 | 0 | 0 | 0 | - |

- **Left out:** the 2 cold runs, 0155-cold-d11 and 0451-cold-d11 (unscored). Every arm has at least 3 timed runs, so every arm gets a timing verdict.
- **Host flags:** guard (c) (sys.json P util >= 90 % and E MHz < 600) flags 0 of 36 runs, and there are 0 slow-state runs (pool-W5b.md sections 1 and 7).
- **Logs** (Agent 6, RESULTS.md): no FAIL.
  - There are two NOTEs, 0215-d11-r4 (L31) and 0528-d11t-r6 (L32). Both lack `Execution complete`. This is the benign exit race that Agent 6 reports across arms on the same night (L9, L94-108).
  - The arm proofs hold in every run (L55-57; see Window and inputs).
- **Flagged runs (for "with and without").**
  - No run meets the section 3 hang criteria (0 STUCK-LOCK, 0 dumps).
  - **Agent 8 audit flags** (host load):
    - pass 1 (L17): 0209-d11p-r3 and 0213-d11t-r3;
    - pass 2 (L21): 0453-d11-r1, 0455-d11t-r1, 0457-d11p-r1 and 0510-d11t-r3.
  - **The runner's slow d11t r1-r2:** 0455-d11t-r1 (also an audit flag) and 0459-d11t-r2.
  - Their union is 7 runs: the `no-flagged` variant, with n = 11 / 8 / 10 (d11 / d11t / d11p).
  - `no-loaded` also drops the two other runs at ng_t >= 2.8, 0520-d11p-r5 (2.90) and 0524-d11p-r6 (2.88). That is 9 runs, with n = 11 / 8 / 8.
  - 0221-d11t-r5, the run with the stutter cluster, isn't flagged: its window ng_t was 2.56, a typical value (z -0.0; audit.md L257).

## 2. Method

- **Primary: B-block T-std.** The round effect on median ms is F = 4.11 on (11, 22), p = 0.002 (fps: F = 4.20, p = 0.002).
  - The effect is pass 1's round 1 alone: rounds 2-12 all sit +5.1 to +7.8 % above round 1 in median ms (pool-W5b.md L24). Pass 2's round 1 (pool round 7) is in line with the rest (+6.4 %).
  - Without each pass's round 1, the round effect is gone (p = 0.186), so `drop-r1-both` uses T-std.
- **The passes agree.**
  - Pass term: p = 0.102 (median ms), 0.105 (fps).
  - Arm x pass: p = 0.601 (median ms), 0.612 (fps), 0.308 (p99), 0.370 (1 % low).
  - So pooling is fine.
- **Guard (a) OK:** light share (frames < 4.5 ms) is d11 0.974, d11t 0.972 and d11p 0.975 (F = 1.18 on (2, 33), p = 0.320). The wait mode doesn't change the frame mix, so T-std is valid here (unlike W9).
- **Guard (b):** the raw and B-block CIs overlap for both arms, for median ms and fps. **Guard (c):** 0 host-flag runs.
- **Position effect** (pass 1, round 1):
  - The first three scored runs of pass 1 were fast: 0157-d11-r1 415.1 fps, 0159-d11t-r1 407.0, 0201-d11p-r1 395.9. Every other kept run ran at 367.1-393.0.
  - These three runs also had a lighter frame mix (light share 0.979-0.988 vs 0.962-0.978), which points to game-state warm-up.
  - Round 1's raw fps deltas therefore follow the run order: d11t -1.95 %, d11p -4.63 %. B-block takes this out; T-std and raw keep it.
- **Precision:**
  - d11's band (B-block) is 3.3 % for median ms and 2.9 % for fps, with a pooled CV of 1.6 / 1.2 %.
  - PROPOSAL section 4 expected about ±5.2 % on p99 and ±6.4 % on the 1 % low at n = 6. The pooled B-block CIs are about ±0.6 % and ±3.8 %.

## 3. Pooled results (12 runs per arm)

Cells give the % change vs d11 [95 % CI]. Bold = the primary method.

| metric | method | d11t | d11p |
|---|---|---|---|
| median ms | **B-block T-std** | +1.2 [-0.2, +2.6] | +0.5 [-0.9, +1.9] |
| | T-std | +1.2 [-0.7, +3.1] | +0.5 [-1.4, +2.4] |
| | raw | +1.3 [-0.8, +3.4] | +0.5 [-1.5, +2.6] |
| fps | **B-block T-std** | -1.1 [-2.1, -0.0] * | -0.7 [-1.8, +0.3] |
| | T-std | -1.1 [-2.5, +0.4] | -0.7 [-2.2, +0.7] |
| | raw | -1.3 [-3.0, +0.4] | -0.7 [-2.4, +1.0] |
| p99 ms | **B-block T-std** | +0.3 [-0.3, +1.0] | +0.0 [-0.6, +0.6] |
| | T-std | +0.3 [-0.5, +1.2] | +0.0 [-0.8, +0.8] |
| | raw | +1.2 [-0.6, +2.9] | +0.1 [-1.6, +1.8] |
| 1 % low fps | **B-block T-std** | -2.8 [-6.5, +1.0] | -0.2 [-4.0, +3.7] |
| | T-std | -2.8 [-6.5, +1.0] | -0.2 [-4.0, +3.7] |
| | raw | -3.9 [-8.4, +0.8] | -0.3 [-4.9, +4.6] |

**CPU.** Each cell gives the arm mean; the change vs d11 [linear 95 % CI, df 33]; the GM % (one-way).

| metric | d11 | d11t | d11p |
|---|---|---|---|
| cores | 2.55 | 2.33; -0.22 [-0.25, -0.19]; -8.6 % * | 2.34; -0.20 [-0.23, -0.17]; -8.0 % * |
| TimerQueue busy % | 23.17 | 1.97; -21.19 [-21.82, -20.56]; -91.5 % * | 2.08; -21.08 [-21.72, -20.45]; -91.1 % * |
| GPU Commands busy % | 60.66 | 60.98; +0.32 [-1.29, +1.94] | 60.94; +0.28 [-1.33, +1.90] |
| Main XThread busy % | 80.66 | 80.26; -0.40 [-2.48, +1.68] | 79.88; -0.77 [-2.85, +1.30] |

- d11t - d11p cores: -0.016 [-0.047, +0.016], n.s. (load-check.md L101).
- The TimerQueue thread's ~21-point drop is ~0.21 core, which is the whole cores saving. The other threads don't change.

**Paired within-round deltas** (12 rounds). Each cell gives the mean +- the 95 % half-width, the median round, and the number of rounds in which the arm was higher than d11.

| metric | d11t | d11p |
|---|---|---|
| raw median ms | +1.33 +- 1.31 (med +0.46; 11/12) | +0.53 +- 1.38 (med -0.38; 5/12) |
| raw fps | -1.28 +- 1.24 (med -0.47; 3/12) | -0.72 +- 0.96 (med +0.04; 7/12) |
| T-std p99 ms | +0.35 +- 0.66 (med +0.35; 7/12) | +0.01 +- 0.59 (med -0.06; 6/12) |
| T-std 1 % low fps | -2.56 +- 4.31 (med -0.37; 5/12) | -0.17 +- 1.55 (med -0.39; 5/12) |
| cores | -8.62 +- 1.05 (med -8.90; 0/12) | -7.98 +- 1.16 (med -8.54; 0/12) |

**Without each pass's round 1** (10 rounds; load-check.md L106-112):
- d11t: raw median ms is higher in 9 of 10 rounds (sign p 0.021; mean +0.68 %, median +0.32 %). Raw fps is lower in 7 of 10 (mean -0.69 %, median -0.21 %).
- d11p: raw median ms is higher in 4 of 10 (mean +0.10 %, median -0.38 %). Raw fps is higher in 7 of 10 (mean -0.23 %, median +0.07 %).

**In the 8 rounds with no flagged run** (r1, r2, r4, r5, r6, r10, r11, r12; counted from load-check.md L105): d11t's raw median ms is higher in 7 of 8 (sign p 0.070; mean +0.48 %, median +0.30 %).

**Tails.** Values are per run (tail-check.md L9-54): the median and mean over each arm's 12 kept runs, and counts summed over them.

| arm | p99.9 ms median / mean | runs with a frame > 8 ms | frames > 8 / 10 / 16.7 ms | longest frame ms | frames > 33 ms |
|---|---|---|---|---|---|
| d11 | 5.390 / 5.429 | 2 | 2 / 1 / 0 | 10.27 (0522-d11-r5) | 0 |
| d11t | 5.479 / 6.088 | 3 | 46 / 28 / 6 | 26.37 (0221-d11t-r5) | 0 |
| d11p | 5.429 / 5.450 | 4 | 6 / 2 / 0 | 11.56 (0524-d11p-r6) | 0 |

- d11t's count comes mostly from one run: 0221-d11t-r5 has 38 / 27 / 6 of those frames. The rest are 0510-d11t-r3 (7 / 1 / 0) and 0203-d11t-r2 (1 / 0 / 0).
- Without 0221, d11t's p99.9 mean is 5.58 ms.
- Paired p99.9 (Agent 8, mine/W5b.md L40-41): d11t +0.659 ms [-0.475, +1.793], higher in 6 of 12 rounds; d11p +0.021 ms [-0.126, +0.168], 6 of 12.

## 4. The runner's numbers (pass 2)

The runner's summary for pass 2, as relayed in `perf-notes/SESSION2.md` L3292-3295: d11p -0.21 core with fps unchanged; d11t -0.21 core but fps -0.8 %, with slow r1-r2.

| pass 2 (6 runs per arm) | d11 | d11t | d11p | from |
|---|---|---|---|---|
| cores (mean) | 2.5585 | 2.347 (-0.2115) | 2.354 (-0.2045) | 3-decimal per-run cores (0451 summary.md run rows; mine/W5b.md L68-70; pool-W5b.json) |
| fps (median) | 385.18 | 382.0 (-0.83 %) | 385.45 (+0.07 %) | 0451 summary.md L12-14 |
| median ms (median) | 2.51 | 2.52 | 2.51 | 0451 summary.md L12-14 |
| runner's d median / d p99 | - | +0.5 / +0.4 % | -0.1 / +0.6 % | 0451 summary.md L12-14 |

**Verdict: agree.**
- d11t's -0.2115 core rounds to -0.21. d11p's -0.2045 rounds to -0.20; the runner's -0.21 is 2.35 - 2.56 from rounded means. The difference doesn't matter.
- d11t's -0.8 % is the median of 6 runs, and 3 of them were loaded: 0455 (367.1), 0459 (376.6) and 0510 (379.3). Its other 3 ran at 384.7-385.7 fps, level with d11's quiet pass-2 runs (385.0-385.4).
  - Agent 8's audit (L25) agrees: d11t's pass-2 median is 382.0 with 0455 and 0510 and 385.0 without them (W5b-1: 384.2).
  - So "slow r1-r2" coincides with host load and is most likely caused by it (section 7). This rests on correlation only: pass 2's within-arm Spearman is -0.32 (p 0.19; load-check.md L75).
- Pass 1's runner summary (0155 summary.md L12-14) has level arm medians (fps 384.65 / 384.23 / 384.99; cores 2.54 / 2.31 / 2.34). Its median-ms spreads of 10.1 / 10.3 / 4.4 % come mostly from the fast round 1 (all of d11's, most of d11t's, about half of d11p's); the rest is loaded 0213 (d11t) and 0209 (d11p). Without round 1 they are 2.0 / 4.4 / 2.2 %.
- The pooled view says the same thing: cores -0.22 / -0.20 (both *), B-block fps -1.1 % * / -0.7 %.

## 5. d11p vs d11t vs d11

1. **CPU: the same saving.**
   - d11t -0.22 [-0.25, -0.19] and d11p -0.20 [-0.23, -0.17] core. The difference, -0.016 [-0.047, +0.016], is n.s.
   - Both savings come from the TimerQueue thread (busy 23.2 % to ~2 %). GPU Commands and Main XThread are unchanged.
   - Cores are lower than d11 in 12 of 12 rounds for both arms. Every subset in section 6 gives d11t -0.21 to -0.23 and d11p -0.19 to -0.21.
2. **Quiet runs: all three arms are level.** Runs with ng_t < 2.8 (load-check.md L79-83):

   | arm | runs | median fps | median raw ms | median cores | median eff MHz |
   |---|---|---|---|---|---|
   | d11 | 11 | 385.1 | 2.512 | 2.540 | 1957 |
   | d11t | 8 | 385.2 | 2.518 | 2.300 | 1966 |
   | d11p | 8 | 385.4 | 2.502 | 2.325 | 1948 |

3. **Median frame time: d11t has a small, consistent cost; d11p has none.**
   - d11t's raw median ms is higher than d11's in:
     - 11 of 12 rounds (sign p 0.006);
     - 9 of 10 without round 1 (p 0.021);
     - 7 of 8 in the rounds with no flagged run (p 0.070).
   - The typical size is about +0.3 % (median round +0.32 % without round 1).
   - d11p is higher in 5 of 12 rounds and 4 of 10 (median round -0.38 %).
   - Pooled, both are n.s.: B-block d11t +1.2 [-0.2, +2.6], d11p +0.5 [-0.9, +1.9].
4. **Under load, d11t lost more.** The 9 runs with ng_t >= 2.8 (audit.md W5b tables; the change vs each arm's quiet median is from load-check.md L85-95):

   | run | pass | ng_t | eff MHz (vs arm) | fps (vs arm) | raw median ms (vs arm) | cores (vs arm) | rest |
   |---|---|---|---|---|---|---|---|
   | 0457-d11p-r1 | 2 | 3.76 | 1780 (-8.6 %) | 386.0 (+0.1 %) | 2.457 (-1.8 %) | 2.37 (+0.04) | -0.17 |
   | 0453-d11-r1 | 2 | 3.53 | 1848 (-5.6 %) | 393.0 (+2.1 %) | 2.483 (-1.2 %) | 2.60 (+0.06) | - |
   | 0455-d11t-r1 | 2 | 3.37 | 1873 (-4.7 %) | 367.1 (-4.7 %) | 2.647 (+5.1 %) | 2.37 (+0.07) | -0.04 |
   | 0213-d11t-r3 | 1 | 3.36 | 1829 (-7.0 %) | 371.7 (-3.5 %) | 2.606 (+3.5 %) | 2.39 (+0.09) | -0.08 |
   | 0209-d11p-r3 | 1 | 3.07 | 1854 (-4.8 %) | 381.8 (-0.9 %) | 2.544 (+1.7 %) | 2.37 (+0.04) | -0.07 |
   | 0520-d11p-r5 | 2 | 2.90 | 1906 (-2.2 %) | 375.6 (-2.6 %) | 2.586 (+3.4 %) | 2.38 (+0.05) | +0.00 |
   | 0524-d11p-r6 | 2 | 2.88 | 1901 (-2.4 %) | 382.1 (-0.9 %) | 2.529 (+1.1 %) | 2.37 (+0.04) | -0.01 |
   | 0510-d11t-r3 | 2 | 2.87 | 1916 (-2.5 %) | 379.3 (-1.5 %) | 2.528 (+0.4 %) | 2.31 (+0.01) | -0.05 |
   | 0459-d11t-r2 | 2 | 2.84 | 1937 (-1.5 %) | 376.6 (-2.2 %) | 2.582 (+2.5 %) | 2.34 (+0.04) | +0.01 |

   - "rest" = cores minus what the arm's quiet median would need at this clock (constant core x MHz). It isn't computed for the spin arm.
   - **d11t's 4 loaded runs lost -3.0 % fps on average** at a mean ng_t of 3.11. **d11p's 4 lost -1.1 %** at a mean ng_t of 3.15.
     - d11p's loaded runs lost more clock on average than d11t's (-4.5 % vs -3.9 % eff MHz), yet less fps.
     - The most loaded run of all, 0457-d11p-r1 (3.76, -8.6 % clock), kept its fps (+0.1 %).
   - d11's only loaded run, 0453-d11-r1 (3.53), was the folder's fastest (+2.1 %). So the spin arm's loss under load isn't really measured here.
   - The cores rise under load (+0.01 to +0.09) is the clock drop: the rest is -0.17 to +0.01 core.
   - Load tracks fps within arms in pass 1: Spearman rho(ng_t, raw fps) is -0.67 within arm (p 0.002). In pass 2 it is -0.32 (p 0.19): there, the two most loaded runs, 0457-d11p-r1 and 0453-d11-r1, kept or beat their arm's fps (load-check.md L74-75).
   - n = 4 loaded runs per arm, picked after the fact: this is a pattern, not a test. For scale, the gap of -1.9 points is n.s.: Welch 95 % CI [-4.1, +0.3], p 0.083; exact permutation p 6/70 = 0.086 (`check/check_w5b.py`).
   - Mechanism (hypothesis, not tested): a blocked thread has to be woken and scheduled, and under load the wake-up may wait for a core. d11p also leaves the TimerQueue thread ~98 % idle (busy 2.08 %), yet lost less. Why isn't known from this data.
5. **Tails: one stutter cluster, in d11t.**
   - 0221-d11t-r5 (pass 1, round 5; window 02:22:47-02:23:37; ng_t 2.56, not flagged) has a p99.9 of 11.672 ms and a longest frame of 26.37 ms.
   - 19 of its 27 frames over 10 ms fall at T 32.77-33.33 s (02:23:20.0-20.5). All 24 frames over 8 ms in T 32.6-33.5 s show buffer_queue_depth 7-8 (window median 0, max 8).
   - At the same moment (cluster-0221.txt):
     - **sys.csv:** the sample at 02:23:20.965 has host CPU 69.3 % (window median 46.0), eff 1707 MHz (median 1976) and E-core util 71.6 % (median 38.0). The next sample is still slow (1644 MHz, E util 51 %). The sample before was normal (49.4 %, 1942 MHz, 42.6 %).
     - **gpu.csv:** the only sample under 90 % util in the window is at t 32.57 s: 58 %, with memory util 12 %. The window median is 100 %.
     - **proc.csv:** game cores were 2.17 / 2.16 at T 32.97 / 33.97, inside the window range 2.07-2.55 (median 2.31). So the game's own CPU didn't spike.
     - **perf.csv:** the 227 frames at T 32.6-33.5 s have 0 texture misses, 0 pipeline misses and 0 critical-region contentions.
     - **game.log:** no line falls in the cluster. The last one before it is a Toypad read 3.7 s earlier.
   - So the cluster lines up with a 1-2 s host-wide burst (E cores busy, clock down), while the game's own CPU stayed flat, the GPU went partly idle and the frame queue was full. The cause isn't identified.
   - Bigger bursts in other runs didn't cause clusters. The audit's 1 s max ng_t was 8.04 in 0213-d11t-r3, 7.60 in 0510-d11t-r3 and 7.49 in 0453-d11-r1, vs 5.95 in 0221 (audit.md L253, L359, L351, L257). Those runs had 0, 7 and 1 frames over 8 ms.
   - It is one event in 36 runs. It fell on d11t, but one event can't show that d11t is more prone.
6. **W5's d11t tail lead is not reproduced.**
   - W5b re-tests W5's d11t-vs-d11 lead at n = 6 per pass (PROPOSAL L69-72). In W5, d11t's p99 was +8.2 % [+0.5, +16.6] (T-std; B-block [+1.6, +15.3]) and its 1 % low -7.7 % (B-block [-13.8, -1.2]), both vs d11 (`build/agent8/readout/w5/READOUT.md` L167). It used 13.7 % less game CPU than base, about 14.5 % less than d11 (medians at n = 3; READOUT L28, L116, L119). The W4b/W5 noise read-out called it "a lead and not a result" (`build/agent7/w4b-noise/RESULTS.md` L103).
   - **p99:** B-block +0.3 [-0.3, +1.0] and raw +1.2 [-0.6, +2.9]. Both CIs exclude +8.2 %.
   - **1 % low:** B-block -2.8 [-6.5, +1.0] excludes -7.7 %, but raw [-8.4, +0.8] doesn't. Without 0221 it is -0.8 [-2.5, +1.0].
   - **CPU:** the saving is reproduced at a smaller size (-8.6 % vs d11 here; W5: about -14.5 % vs d11, -13.7 % vs base). W5 ran on best_efficiency and before the Defender exclusion, so only the direction compares.

## 6. With and without the flagged runs

**d11t vs d11, % [95 % CI]** (pool-W5b.md section 6; cores = change in cores):

| pool (runs left out) | n d11t | primary (round p) | median ms | fps | p99 | 1 % low | raw median ms | raw fps | cores |
|---|---|---|---|---|---|---|---|---|---|
| all 36 | 12 | B-block (0.002) | +1.2 [-0.2, +2.6] | -1.1 [-2.1, -0.0] * | +0.3 [-0.3, +1.0] | -2.8 [-6.5, +1.0] | +1.3 [-0.8, +3.4] | -1.3 [-3.0, +0.4] | -0.22 [-0.25, -0.19] |
| no-flagged (7) | 8 | B-block (< 0.001) | +0.3 [-0.9, +1.6] | -0.2 [-1.0, +0.7] | -0.1 [-0.7, +0.6] | -2.9 [-7.8, +2.3] | +0.0 [-2.3, +2.3] | +0.0 [-1.8, +1.9] | -0.23 [-0.26, -0.19] |
| no-loaded (9) | 8 | B-block (< 0.001) | +0.3 [-0.9, +1.6] | -0.2 [-1.0, +0.6] | -0.1 [-0.7, +0.6] | -3.0 [-8.1, +2.3] | +0.0 [-2.3, +2.4] | +0.0 [-1.8, +1.9] | -0.23 [-0.26, -0.19] |
| no-audit-flag (6) | 9 | B-block (< 0.001) | +0.6 [-0.6, +1.9] | -0.4 [-1.3, +0.5] | +0.1 [-0.6, +0.7] | -2.8 [-7.4, +2.0] | +0.4 [-1.8, +2.7] | -0.3 [-2.1, +1.5] | -0.22 [-0.26, -0.19] |
| no-slow-d11t (2) | 10 | B-block (< 0.001) | +0.4 [-0.7, +1.5] | -0.4 [-1.2, +0.3] | +0.3 [-0.4, +1.0] | -3.2 [-7.2, +1.0] | +0.6 [-1.4, +2.7] | -0.7 [-2.4, +1.0] | -0.22 [-0.26, -0.19] |
| no-0221 (1) | 11 | B-block (0.003) | +1.3 [-0.2, +2.7] | -1.1 [-2.2, +0.0] | +0.3 [-0.4, +0.9] | -0.8 [-2.5, +1.0] | +1.4 [-0.7, +3.6] | -1.3 [-3.0, +0.5] | -0.22 [-0.25, -0.19] |
| no-p2-first3 (3) | 11 | B-block (< 0.001) | +0.7 [-0.4, +1.8] | -0.6 [-1.4, +0.2] | +0.4 [-0.3, +1.0] | -3.3 [-7.2, +0.7] | +0.8 [-1.3, +3.0] | -0.8 [-2.5, +0.9] | -0.22 [-0.25, -0.19] |
| drop-p2-r1r2 | 10 | B-block (< 0.001) | +0.5 [-0.6, +1.6] | -0.4 [-1.2, +0.3] | +0.3 [-0.4, +1.1] | -3.4 [-7.8, +1.1] | +0.7 [-1.6, +3.0] | -0.7 [-2.5, +1.2] | -0.22 [-0.25, -0.19] |
| drop-r1-both | 10 | T-std (0.186) | +0.6 [-0.4, +1.5] | -0.5 [-1.2, +0.2] | +0.4 [-0.3, +1.1] | -3.7 [-7.9, +0.7] | +0.7 [-0.3, +1.7] | -0.7 [-1.5, +0.1] | -0.22 [-0.25, -0.19] |
| pass 1 only | 6 | B-block (0.001) | +0.7 [-1.1, +2.6] | -0.6 [-1.8, +0.6] | +0.6 [-0.2, +1.4] | -5.1 [-12.1, +2.5] | +0.9 [-3.0, +4.9] | -0.9 [-4.0, +2.4] | -0.23 [-0.28, -0.18] |
| pass 2 only | 6 | T-std (0.993) | +1.6 [-0.3, +3.6] | -1.5 [-3.0, +0.0] | +0.1 [-1.0, +1.3] | -0.6 [-3.8, +2.7] | +1.7 [-0.2, +3.7] | -1.7 [-3.4, -0.1] * | -0.21 [-0.25, -0.17] |

**d11p vs d11, % [95 % CI]:**

| pool (runs left out) | n d11p | primary | median ms | fps | p99 | 1 % low | raw median ms | raw fps | cores |
|---|---|---|---|---|---|---|---|---|---|
| all 36 | 12 | B-block | +0.5 [-0.9, +1.9] | -0.7 [-1.8, +0.3] | +0.0 [-0.6, +0.6] | -0.2 [-4.0, +3.7] | +0.5 [-1.5, +2.6] | -0.7 [-2.4, +1.0] | -0.20 [-0.23, -0.17] |
| no-flagged (7) | 10 | B-block | +0.7 [-0.4, +1.9] | -0.7 [-1.5, +0.0] | +0.2 [-0.4, +0.8] | -0.6 [-5.3, +4.2] | +0.5 [-1.6, +2.7] | -0.6 [-2.3, +1.2] | -0.20 [-0.24, -0.17] |
| no-loaded (9) | 8 | B-block | +0.4 [-0.8, +1.7] | -0.5 [-1.2, +0.3] | -0.0 [-0.7, +0.6] | +0.5 [-4.8, +6.0] | +0.0 [-2.3, +2.4] | -0.2 [-2.0, +1.7] | -0.21 [-0.25, -0.18] |
| no-audit-flag (6) | 10 | B-block | +0.7 [-0.5, +1.9] | -0.7 [-1.5, +0.1] | +0.2 [-0.4, +0.8] | -0.6 [-5.1, +4.1] | +0.5 [-1.7, +2.7] | -0.6 [-2.3, +1.2] | -0.20 [-0.24, -0.17] |
| no-slow-d11t (2) | 12 | B-block | +0.5 [-0.5, +1.5] | -0.7 [-1.4, -0.1] * | -0.0 [-0.7, +0.7] | -0.2 [-4.1, +3.8] | +0.5 [-1.4, +2.5] | -0.7 [-2.3, +0.9] | -0.20 [-0.24, -0.17] |
| no-0221 (1) | 12 | B-block | +0.5 [-0.9, +1.9] | -0.7 [-1.8, +0.3] | -0.0 [-0.7, +0.6] | -0.2 [-1.9, +1.5] | +0.5 [-1.6, +2.6] | -0.7 [-2.5, +1.0] | -0.20 [-0.24, -0.17] |
| no-p2-first3 (3) | 11 | B-block | +0.7 [-0.4, +1.8] | -0.7 [-1.5, +0.1] | +0.1 [-0.5, +0.8] | -0.7 [-4.6, +3.5] | +0.7 [-1.4, +2.8] | -0.6 [-2.4, +1.1] | -0.20 [-0.23, -0.17] |
| drop-p2-r1r2 | 10 | B-block | +0.8 [-0.3, +1.9] | -0.8 [-1.5, +0.0] | +0.1 [-0.6, +0.9] | -0.7 [-5.1, +4.0] | +0.8 [-1.5, +3.1] | -0.7 [-2.6, +1.2] | -0.19 [-0.23, -0.16] |
| drop-r1-both | 10 | T-std | +0.2 [-0.8, +1.1] | -0.4 [-1.1, +0.3] | +0.1 [-0.7, +0.8] | -0.6 [-4.9, +4.0] | +0.1 [-0.9, +1.1] | -0.2 [-1.0, +0.6] | -0.21 [-0.24, -0.18] |
| pass 1 only | 6 | B-block | +0.8 [-1.1, +2.6] | -0.7 [-1.9, +0.5] | -0.2 [-1.0, +0.6] | -0.0 [-7.4, +7.9] | +0.8 [-3.1, +4.8] | -0.7 [-3.8, +2.6] | -0.20 [-0.25, -0.15] |
| pass 2 only | 6 | T-std | +0.3 [-1.6, +2.2] | -0.8 [-2.3, +0.8] | +0.3 [-0.9, +1.5] | -0.4 [-3.5, +2.9] | +0.3 [-1.6, +2.2] | -0.8 [-2.4, +0.9] | -0.20 [-0.25, -0.16] |

Notes on the tables:
- The subsets other than pass 1 only / pass 2 only were chosen after looking at the data.
- `no-flagged` drops the union of Agent 8's audit flags and the runner's slow d11t r1-r2. `no-audit-flag` drops the audit flags only. `no-loaded` drops every run with ng_t >= 2.8.
- `no-slow-d11t` drops the 2 runs the runner named. `no-p2-first3` drops pass 2's first 3 scored runs (section 7).
- The d11 n is 12, except 11 in `no-flagged`, `no-loaded`, `no-audit-flag` and `no-p2-first3`, and 10 in the drop-round and 6 in the one-pass variants.
- Full tables, with the round terms, are in pool-W5b.md section 6.

**No verdict changes in any subset.** Three details move:
1. **d11t's fps loss** is significant only in the full pool (-1.1 % *) and in pass 2's raw fps (-1.7 % *). Without the loaded runs or round 1 it is -0.2 to -0.6 % and n.s.
2. **d11p's fps** stays at -0.4 to -0.8 % in every subset, with a `*` only in `no-slow-d11t` (-0.7 [-1.4, -0.1]). Its median round is +0.04 % (+0.07 % without round 1).
   - The pooled loss comes from four rounds: r1 -4.63 % (the position effect), r7 -1.78 % (d11's 0453 ran fast), r11 -2.44 % (0520, ng_t 2.90) and r12 -0.80 % (0524, 2.88).
   - Every other round is 0.00 to +0.23 % (load-check.md L111).
3. **d11t's 1 % low** is -2.8 to -3.7 % in every subset that keeps 0221 (-5.1 % in pass 1 only). Without 0221 it is -0.8 [-2.5, +1.0], and pass 2 alone gives -0.6.

## 7. W5b-2's quiet gate and the load after it

- **The gate rule** (`perf-notes/SESSION2.md` L2260): wait for 3 consecutive minutes in which MsMpEng, OfficeClickToRun and CrossDeviceService each use < 0.1 core.
- **What happened** (SESSION2.md L3291): the gate held W5b-2 back for 3 min while CrossDeviceService ran at 0.81 / 0.87 / 0.68 core (04:46-04:49), then passed STRICT. The runner started at 04:51:58.
- **No sys.csv covers the holdback** (audit.md L30): W9-2's last window ended 04:44:02, and W5b-2's cold run started 04:51:59.
- **The start was clean.** The cold run had window ng_t 2.55 and warm-up 1.94 (W5b-1's cold run: 2.39 / 1.93) (audit.md L31, L450).
- **Then the load rose again**, ~6 min after the holdback and during the first scored run (audit.md L32-37):
  - The first four scored runs (windows 04:54:46-05:01:48) had window ng_t 3.53 / 3.37 / 3.76 / 2.84, with warm-up ng_t 2.55 / 3.80 / 3.62 / 3.48 (audit.md L431-434). That is about +1 core of extra load.
  - First 3 scored runs vs the other 15, median ng_t: 3.53 vs 2.50 in W5b-2; 2.46 vs 2.56 in W5b-1 (audit.md L450).
  - The 30 s rolling median of ng_t is above the folder baseline (2.43) + 0.5 in 386 of 2070 samples, vs 30 in W5b-1. The first is at 04:55:02, and most fall in 04:55-05:03 (audit.md L34).
  - From 0501 (05:03) on, ng_t was back to ~2.5, apart from three single runs at 2.87-2.90 (0510-d11t-r3, 0520-d11p-r5, 0524-d11p-r6) (audit.md L33).
  - Same arm, median ng_t of W5b-2 minus W5b-1: d11 -0.03, d11t +0.09, d11p +0.16 (audit.md L422-424).
  - W5b-2 also lost the usual fast start. The median fps_rel of each folder's first two scored runs is 0.991 in W5b-2, vs 1.032-1.152 in the six other night folders (audit.md L115).
- **The source is unknown.** The matrix folders have no per-process data for non-game processes, so the load can't be tied to CrossDeviceService or anything else (audit.md L37).
- **Effect on the verdicts:** all four of the first scored runs, and 0510, are among the 7 flagged runs. 0520 and 0524 are in `no-loaded`. No verdict changes without them (section 6).
- **Recommendations for future windows:**
  - a per-run quiet check: re-check the gate's processes before each run, and wait or flag the run if one is >= 0.1 core;
  - log the top CPU processes once a second during each run, so the source of a burst can be named;
  - flag any run with window ng_t >= 2.8, or re-run it at the end;
  - rotate the round-1 order, or add unscored warm-up runs (the position effect, section 2).

## 8. Pick and follow-ups

- **Pick d11p (narrowly) over d11t.** Both beat d11 on CPU.
  - **CPU:** both save the same ~0.2 core (-8 %), from the same thread.
  - **Quiet runs:** all three arms are level (385.1-385.4 fps).
  - **d11t** has:
    - a small, consistent median-ms cost (about +0.3 %; 9 of 10 rounds without round 1);
    - a larger fps loss under load (-3.0 % vs -1.1 % at similar ng_t; n = 4 each; post hoc and n.s., p 0.083, section 5 item 4);
    - the only stutter cluster (0221).
  - **d11p** has no consistent frame cost. Its pooled -0.7 % fps comes from round 1 and three loaded or fast-ref rounds (section 6, item 2).
  - Without the flagged runs, the frames alone can't separate d11t and d11p. The pick then rests on the flagged (loaded) runs themselves (a post hoc, n.s. gap) and on 0221 (a single event). Hence "narrowly".
- **d11p vs d11:** -0.20 core (-8.0 % *) for fps -0.7 % [-1.8, +0.3] (median round +0.04 %), p99 +0.0 % and 1 % low -0.2 %. So there is no p99 or 1 % low loss beyond the spread.
- **Optional follow-up**, only if d11t is still a candidate: d11t vs d11p vs d11 under a controlled background load (e.g. a fixed synthetic E-core load), n >= 6 per arm, with the per-run quiet check (section 7). This would test whether the blocking wait is more exposed to load.

## 9. Caveats

- **Post hoc subsets and many tests.** The variants were chosen after seeing the data, except pass 1 only / pass 2 only, so treat their CIs as descriptive. There are 2 arms x 4 metrics x 3 methods, so a lone `*` can be chance.
- **The loaded-run comparison is small:** 4 runs per arm, picked by ng_t after the fact; the gap is n.s. (p 0.083).
- **ng_t is a window mean**, so short bursts (as in 0221) can matter more than the mean shows.
- **0221 is a single event** (1 of 36 runs).
- **Host state:**
  - Compare W5b only within itself. W5b, W9, W6 and W4c ran after the Defender exclusion for `build/` (~23:16 on Nov 22; SESSION2.md L3171-3173); W4b and W5 ran before it. Absolute fps, ms and cores across that line aren't comparable.
  - W5b's overlay is best_performance; W5's was best_efficiency. So the W5 comparison (section 5, item 6) is about direction and CI coverage only.
- **The quiet gate only checks at the window start** (section 7).
- **eff MHz is rough.** It is a sys.json mean over all cores and the whole window, so the constant core x MHz "rest" figures are rough (a few %).
- **Position effect:** B-block removes pass 1's fast round 1. The T-std and raw CIs still include it.

## 10. Changes after the checks (rev 1)

- **Independent check:** `check/CHECK-W5b.md` (read-only checker, ~07:35; helper `check/check_w5b.py`). It checked ~830 claims and found 11 mismatches: 0 high, 2 medium, 6 low, 3 very low. No copied number or CI was wrong.
- **Agent 8's recompute** from results.csv, with code that shares nothing with `pool_readout.py` (`build/agent8/readout/w-followup/a7check/W9-W5b-check.md`): 912 claims over W9 and W5b, 880 agree, 0 sign flips, no `*` changes.
  - 21 are rounding ties of at most 1 in the last digit (unrounded per-run inputs here, 3 dp in results.csv), e.g. L239-240 and L256-257.
  - 9 come from the light-share definition (±0.001 in 5 runs). Guard (a)'s F is 1.18 here vs 1.21 there (L81), n.s. either way.
  - 1 is a slip, at L70 and L215: 0221's window ng_t is 2.56. The 2.31 was the game-cores column of audit.md L257 (the CHECK-W5b.md checker had passed it too).
- **All fixes are in place, on the same lines**, so lines 1-326 keep the line numbers both checks cite. The pre-fix copy is `check/W5b-rev0.md`. The edits are listed in `check/fixes-rev1.txt` and were applied by `check/apply_fixes_rev1.py` (each old text found exactly once; line count unchanged).
  - #1 (L44, L227, L230): W5's -13.7 % game CPU is vs base. Vs d11 it is about -14.5 %, so "smaller" still holds.
  - #2 (L42, L212, L308, L311, L318): the loaded-run gap (-1.9 points) is now marked post hoc and n.s. (Welch p 0.083; exact permutation 6/70 = 0.086, also re-derived by hand).
  - #3, #4, #7 (L156, L152, L224): sources added or corrected.
  - #5, #8, #9 (L165, L85, L45, L286): wording ("coincides with", "points to", "rose again").
  - #6 (L166): pass 1's spreads come mostly from round 1. Without it they are 2.0 / 4.4 / 2.2 %.
  - #10 (L21, L322; also W9.md L20): the ~23:16 Defender citation. #11 (L44; also L146): "most of it from one run".
  - Agent 8's slip (L70, L215): 2.31 is now 2.56. It stays below 2.8 and unflagged, so no run set or number moves.
- **No verdict changed.**

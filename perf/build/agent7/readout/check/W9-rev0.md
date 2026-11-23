# W9 formal read-out: GPU-wait back-off sweep (#24) on devoff4b

Agent 7, 2026-11-23 (task #21). Format: `build/agent8/w-followup/PROPOSAL.md` section 3 (counts per arm; every verdict with and without the flagged runs). All inputs were read-only, and nothing was re-run.

## Window and inputs

- **Arms** (matrix.json; env proof in `build/agent6/wnight/RESULTS.md` L60-86: 42 of 42 runs OK, 0 mismatches):
  - **off** (ref): back-off off, with no `LEGO_GPU_WAIT_*` env (the S4b default).
  - **q0, q125, q250, q500**: `LEGO_GPU_WAIT_BACKOFF_US=<Q>` and `LEGO_GPU_WAIT_SPIN_US=30`, with no STATS.
  - All arms run devoff4b (S4b + S4c) with cvars `framerate_limit=0` and no C1.
- **Passes:** the same matrix ran twice. The pool numbers its rounds 1-4 (pass 1) and 5-8 (pass 2).

| pass | folder | measured windows | results.csv sha256 (prefix) |
|---|---|---|---|
| 1 | `build/agent8/matrix/20261123-0108` | 01:09:57-01:50:29 | 823BA531C6EC402D |
| 2 | `build/agent8/matrix/20261123-0401` | 04:02:22-04:43:12 | 45C2D73C071E23EC |

- **Host state:**
  - G11 overlay: power overlay best_performance in 42 of 42 runs, scheme Balanced, AC, saver off, with no change inside either window.
  - The Defender exclusion for `build/` was in place (it was added ~23:16 on Nov 22).
- **Sources:**
  - `build/agent7/readout/pool-W9.md` (+ `.json`) comes from `pool_readout.py`, with both passes pooled. Its self-check re-runs `readout.py` on each pass: PASS, 204 numbers each, max |diff| 0. The command is in its header.
  - `build/agent7/readout/load-check.md` comes from `load_check.py`. It has the loaded-run table, thread cycles, cores differences, paired sign counts and Spearman.
  - Agent 8's audit, `build/agent8/readout/w-followup/audit/audit.md` (the version written at 06:38; line numbers refer to it):
    - section 2 gives per-run host load, where ng_t = non-game busy cores (window mean): W9-1 at L211-238, W9-2 at L317-344;
    - the per-arm summary is at L373-402, and the flag lists are at L16 (W9-1) and L20 (W9-2).
  - Agent 9's clock check: `build/agent9/handoff/w9-clock-check.txt` (script `w9_clock_check.ps1`, read-only).
  - Agent 6's logdiffs: `build/agent6/wnight/RESULTS.md`.
- **Agreement:** these numbers agree with Agent 8's `build/agent8/readout/w-followup/a7/W9-pool.md` (same tool) and with the tail figures in `build/agent8/readout/w-followup/mine/W9.md`.

## Verdicts

| question | verdict | all 40 kept runs | without the 7 flagged runs |
|---|---|---|---|
| Which Q? | **q500** | Largest CPU drop: -0.75 core [-0.86, -0.64], -30.0 % *. No p99 or 1 % low loss in any method. | Same pick: -0.79 core [-0.84, -0.73]. p99 and 1 % low are better than off (T-std p99 -0.8 % *, 1 % low +2.2 % *). |
| Runner's q500 numbers (pass 2) | **agree** | -0.70 core (-27.9 %), fps +1.1 %, p99 4.675 vs 4.985 ms | The runner's numbers are pass-2 means/medians and include 0419-q500-r2. |
| q0 vs off | **drop q0** | No CPU drop: -0.03 core [-0.14, +0.08]. Raw median ms is higher in 8 of 8 rounds. | Unchanged: no q0 or off run is flagged. |
| q125/q250 instability: arm or host? | **host-triggered; the q arms are more exposed; not an arm defect** | All 6 slow q runs ran during two load bursts in pass 2 (ng_t 2.91-4.06). The same arms ran normally before, between and after the bursts. | Without the flagged runs, q125 and q250 sit next to q500: cores -0.72 each vs -0.79. |

`*` = the 95 % CI excludes 0. Deltas are vs off unless a row says otherwise.

## 1. Runs (PROPOSAL section 3)

| arm | planned (+cold) | timed | kept | failed | STUCK-LOCK | hang dumps | slow-state runs | host CPU at each hang |
|---|---|---|---|---|---|---|---|---|
| off | 8 (+2) | 8 | 8 | 0 | 0 | 0 | 0 | - |
| q0 | 8 | 8 | 8 | 0 | 0 | 0 | 0 | - |
| q125 | 8 | 8 | 8 | 0 | 0 | 0 | 0 | - |
| q250 | 8 | 8 | 8 | 0 | 0 | 0 | 0 | - |
| q500 | 8 | 8 | 8 | 0 | 0 | 0 | 0 | - |

- **Left out:** the 2 cold runs, 0108-cold-off and 0401-cold-off (unscored). Every arm has at least 3 timed runs, so every arm gets a timing verdict.
- **Host flags:** 0 rows with E-core MHz < 800 in any window, and 0 slow-state onsets (audit.md section 1, pool-W9.md section 8).
- **Logs** (Agent 6, RESULTS.md L25-33, L54, L94-137): no FAIL.
  - There are two off-arm NOTEs, and both came after the measured window:
    - `0429-off-r3` lacks `Execution complete`. This is a benign exit race; Agent 6 reports it in 6 of 135 night runs, across arms.
    - `0128-off-r2` hit the 3 s shutdown watchdog after WM_CLOSE. This is the first sighting. off has no back-off env, so it isn't #24.
  - Each q run logs the back-off init line exactly once, with its Q.
- **Flagged runs (for "with and without").**
  - No run meets the section 3 hang criteria (0 STUCK-LOCK, 0 dumps).
  - Guard (c) (sys.json P util >= 90 % and E MHz < 600) flags 0 runs.
  - Two host-load flags apply:
    - **Agent 9 lowclk**, pass 2 only (pass 1: 0 of 21). The runs are 0407-q125-r1, 0409-q250-r1, 0419-q500-r2 and 0423-q125-r3. They ran at eff ~1850-1950 MHz vs ~2200, with E util 47-54 % vs ~34 %. Agent 9 reads this as host-driven, not proven.
    - **Agent 8 audit flags:**
      - pass 1: 0122-q125-r2 and 0124-q250-r2 (load bursts, normal fps);
      - pass 2: 0407-q125-r1, 0409-q250-r1, 0417-q250-r2 and 0423-q125-r3.
  - Their union is 7 runs: the `no-flagged` variant. No off or q0 run is flagged.

## 2. Method

- **Primary: T-std.** The round effect on median ms is F = 2.35 on (7, 28), p = 0.051.
  - fps does show a round effect (p = 0.031), so B-block T-std is shown too. It gives the same deltas with narrower CIs.
- **The passes agree.**
  - Pass term: p = 0.055 (median ms).
  - Arm x pass: p = 0.902 (median ms), 0.933 (fps), 0.264 (p99), 0.435 (1 % low).
  - So pooling is fine.
- **Guard (a) WARNING: the back-off changes the frame mix.**
  - Light share (frames < 4.5 ms) per arm: off 0.968, q0 0.970, q125 0.983, q250 0.986, q500 0.984 (F = 9.38 on (4, 35), p < 0.001).
  - T-std holds off's mix fixed, so it charges the q arms for the frames they moved below 4.5 ms.
  - **A T-std fps loss on its own is not a loss.** Read raw, T-heavy, paired and CPU beside it.
- **Guard (b):** the raw and T-std CIs overlap for every arm, for both median ms and fps. **Guard (c):** 0 host-flag runs.
- **Position effect.**
  - off ran first in round 1 of both passes.
  - The first 1-3 scored runs of a pass were fast even after the cold run:
    - pass 1: 0110-off-r1 443.7 fps (22187 frames), 0112-q0-r1 414.6, 0114-q125-r1 395.5;
    - pass 2: 0403-off-r1 408.9.
  - The other off runs ran at 382.2-386.6 fps.
  - 0110-off-r1 also had a lighter frame mix (light share 0.982 vs 0.962-0.974) at a normal clock (1992 MHz; the other off runs ran at 1907-2027). So the cause is game-state warm-up rather than host load.
  - This inflates off's mean and pulls each q arm's pooled fps delta down by about 2-3 points (compare `drop-r1-both` in section 7).

## 3. Pooled results (8 runs per arm)

Cells give the % change vs off [95 % CI]. Bold = the primary method.

| metric | method | q0 | q125 | q250 | q500 |
|---|---|---|---|---|---|
| median ms | **T-std** | +2.8 [-0.5, +6.1] | -1.3 [-4.4, +2.0] | -1.3 [-4.4, +2.0] | -2.5 [-5.6, +0.7] |
| | B-block T-std | +2.8 [-0.2, +5.8] | -1.3 [-4.1, +1.7] | -1.3 [-4.1, +1.7] | -2.5 [-5.3, +0.4] |
| | raw | +2.6 [-1.0, +6.2] | -1.9 [-5.3, +1.6] | -2.1 [-5.5, +1.4] | -3.3 [-6.6, +0.1] |
| | T-heavy | -0.5 [-1.7, +0.6] | -1.8 [-3.0, -0.7] * | -1.9 [-3.0, -0.7] * | -1.3 [-2.5, -0.2] * |
| fps | **T-std** | -1.6 [-4.1, +0.9] | -4.0 [-6.4, -1.5] * | -3.8 [-6.3, -1.3] * | -2.8 [-5.3, -0.3] * |
| | B-block T-std | -1.6 [-3.8, +0.6] | -4.0 [-6.1, -1.8] * | -3.8 [-6.0, -1.7] * | -2.8 [-5.0, -0.6] * |
| | raw | -1.4 [-4.4, +1.6] | -2.6 [-5.5, +0.4] | -2.2 [-5.1, +0.8] | -1.3 [-4.3, +1.7] |
| | T-heavy | +1.2 [-1.1, +3.6] | +2.2 [-0.1, +4.6] | +1.9 [-0.5, +4.2] | +1.9 [-0.5, +4.3] |
| p99 ms | **T-std** | -0.3 [-1.3, +0.8] | -1.3 [-2.4, -0.2] * | -1.3 [-2.4, -0.2] * | -0.9 [-1.9, +0.2] |
| | raw | -0.7 [-4.4, +3.1] | -6.0 [-9.5, -2.3] * | -7.1 [-10.6, -3.5] * | -6.2 [-9.7, -2.6] * |
| 1 % low fps | **T-std** | +1.7 [-2.0, +5.5] | +2.8 [-0.9, +6.7] | +2.2 [-1.5, +6.0] | +2.4 [-1.3, +6.3] |
| | raw | +3.1 [-4.0, +10.8] | +8.3 [+0.8, +16.4] * | +9.1 [+1.5, +17.3] * | +8.7 [+1.1, +16.8] * |

**CPU.** Each cell gives the change vs off [linear 95 % CI, df 35]; the GM % is one-way.

| metric | off | q0 | q125 | q250 | q500 |
|---|---|---|---|---|---|
| cores | 2.51 | -0.03 [-0.14, +0.08]; -1.1 % | -0.62 [-0.73, -0.50]; -24.8 % * | -0.65 [-0.76, -0.53]; -25.9 % * | -0.75 [-0.86, -0.64]; -30.0 % * |
| GPU Commands busy % | 59.39 | -1.74 [-4.85, +1.37] | -9.29 [-12.40, -6.18] | -10.51 [-13.62, -7.40] | -12.14 [-15.25, -9.03] |
| Main XThread busy % | 80.35 | -3.80 [-7.93, +0.33] | -11.25 [-15.38, -7.12] | -11.40 [-15.53, -7.27] | -14.60 [-18.73, -10.47] |
| TimerQueue busy % | 23.16 | -0.80 [-2.04, +0.44] | +2.09 [+0.85, +3.33] | +1.80 [+0.56, +3.04] | +0.81 [-0.43, +2.05] |

Cores differences between the q arms (load-check.md):
- q500 - q250: -0.104 [-0.216, +0.008].
- q500 - q125: -0.133 [-0.245, -0.020] *.
- q250 - q125: -0.029 [-0.141, +0.083].

**Paired within-round deltas** (8 rounds). Each cell gives the mean +- the 95 % half-width, the median round, and the number of rounds in which the arm was higher than off.

| metric | q0 | q125 | q250 | q500 |
|---|---|---|---|---|
| raw median ms | +2.65 +- 3.70 (med +0.45; 8/8) | -1.70 +- 5.86 (med -5.70; 3/8) | -1.91 +- 5.26 (med -4.55; 2/8) | -3.18 +- 4.85 (med -5.86; 1/8) |
| raw fps | -1.37 +- 2.48 (med -0.22; 3/8) | -2.44 +- 4.64 (med +0.61; 5/8) | -2.06 +- 4.18 (med +0.20; 5/8) | -1.22 +- 4.05 (med +1.03; 6/8) |
| T-std p99 ms | -0.25 +- 0.39 (2/8) | -1.27 +- 1.71 (2/8) | -1.31 +- 0.87 (1/8) | -0.87 +- 0.42 (0/8) |
| T-std 1 % low fps | +1.75 +- 2.95 (7/8) | +3.12 +- 6.69 (6/8) | +2.32 +- 4.93 (6/8) | +2.48 +- 3.60 (6/8) |
| cores | -1.09 +- 1.40 (1/8) | -24.51 +- 5.98 (0/8) | -25.70 +- 5.23 (0/8) | -29.90 +- 3.32 (0/8) |

**Without each pass's round 1** (6 rounds; load-check.md):
- q500: raw fps is higher in 6 of 6 rounds (+0.91 to +1.64 %, mean +1.19 %, sign p 0.031), and raw median ms is lower in 6 of 6 (-4.58 to -6.76 %).
- q125 and q250: raw fps is higher in 5 of 6 rounds. The two misses are runs under load: 0423-q125-r3 (-4.36 %) and 0417-q250-r2 (-0.81 %).

**Tails.** Values are per run from results.csv: the median over each arm's 8 kept runs, and the max over those runs.

| arm | fps | p99 ms | p99.9 ms median / mean | longest frame ms | frames > 33 ms |
|---|---|---|---|---|---|
| off | 385.5 | 4.985 | 5.603 / 6.282 | 20.63 (0421-off-r2) | 0 |
| q0 | 385.65 | 4.915 | 5.594 / 5.698 | 9.43 | 0 |
| q125 | 389.4 | 4.498 | 5.077 / 5.473 | 23.29 (0407-q125-r1) | 0 |
| q250 | 387.7 | 4.582 | 5.174 / 5.438 | 37.29 (0409-q250-r1) | 1 |
| q500 | 389.8 | 4.644 | 5.427 / 5.449 | 8.12 | 0 |

The three longest frames all fell in the loaded part of pass 2 (section 6). One of them is from an off run.

## 4. q500 vs the runner's numbers

The runner's summary for pass 2: q500 -0.70 core (-28 %), fps +1.1 %, p99 4.68 vs 4.99 ms, p99.9 5.40 vs 5.58 ms.

| pass 2 | q500 | off | change | from |
|---|---|---|---|---|
| cores (mean of 4 runs) | 1.80 | 2.4975 | -0.70 (-27.9 %) | pool-W9.md section 8 |
| fps (median of 4) | 389.25 | 384.9 | +1.1 % | pool-W9.md section 8 |
| p99 ms (median of 4) | 4.675 | 4.985 | -6.2 % | pool-W9.md section 8 |
| p99.9 ms (median of 4) | 5.405 | 5.579 | -3.1 % | results.csv (as in Agent 8's mine/W9.md) |

**Verdict: agree.** The pooled view says the same thing, with tighter limits:
- cores: -0.75 [-0.86, -0.64];
- raw p99: -6.2 % [-9.7, -2.6] *;
- paired raw fps without round 1: +1.19 % (higher in 6 of 6 rounds).

The pooled raw fps GM, -1.3 % [-4.3, +1.7], is lower because it includes off's fast first runs, which the median of 4 drops.

## 5. q0 vs off

- **CPU: no drop.**
  - Cores: -0.03 [-0.14, +0.08] (-1.1 % [-6.7, +4.8]). Paired, cores are lower in 7 of 8 rounds, but only by -1.09 +- 1.40 %.
  - Thread busy changes are all n.s.: GPU Commands -1.74, Main -3.80, TimerQueue -0.80 points.
- **Frames: a small but consistent median cost.**
  - Raw median ms is higher than off in 8 of 8 rounds (sign p 0.008).
  - Without each pass's round 1, where off ran first and fast, it is still higher in 6 of 6 rounds (p 0.031): raw +0.12 to +1.31 % (mean +0.45 %), T-std +0.32 to +1.48 % (mean +0.77 %).
  - The pooled T-std delta, +2.8 [-0.5, +6.1], is n.s. and inflated by round 1. In `no-lowclk-no-r1` it is +0.8 [+0.1, +1.5] *.
- **Other metrics:** fps, p99 and 1 % low are n.s. in every method:
  - T-std: -1.6, -0.3, +1.7 %;
  - raw: -1.4, -0.7, +3.1 %.
- **Guard (a)** doesn't touch q0: its light share is the same as off's (0.970 vs 0.968).
- **Verdict: drop q0.** With Q = 0, the back-off saves no CPU and costs ~0.5-0.8 % median frame time. The saving needs Q > 0.

## 6. The q125/q250 instability: arm or host?

The question: q125 r1 and r3 (0407, 0423) ran at 2.13-2.15 cores with ~18.3k frames, and q250 r1-r2 (0409, 0417) had ~18.9k frames.

**Answer: host-triggered.**
- The slow q runs ran during two bursts of background load in pass 2. The same arms ran normally before, between and after the bursts, and throughout pass 1.
- The q arms lose more than off under such load. A likely reason is that they lose their clock headroom (point 4).
- So the q arms are more exposed to host load. This is not an arm defect.
- This agrees with Agent 9's reading of the clock data ("host-driven, not proven") and adds the load and cycle evidence below.

1. **The slow runs line up with load.**
   - Pass-2 runs with ng_t >= 2.8: audit.md W9-2 table; the change vs each arm's quiet median (ng_t < 2.8) is from load-check.md.

   | run | window start | ng_t | eff MHz | E util % | cores | frames | fps (vs arm) | raw median ms (vs arm) |
   |---|---|---|---|---|---|---|---|---|
   | 0407-q125-r1 | 04:08:11 | 4.06 | 1857 | 53.7 | 2.15 | 18250 | 365.0 (-6.3 %) | +7.6 % |
   | 0409-q250-r1 | 04:10:16 | 3.72 | 1894 | 50.1 | 2.11 | 18909 | 378.2 (-2.8 %) | +5.9 % |
   | 0417-q250-r2 | 04:18:30 | 2.91 | 2075 | 40.3 | 1.93 | 18958 | 379.1 (-2.6 %) | +2.3 % |
   | 0419-q500-r2 | 04:20:34 | 3.36 | 1947 | 47.2 | 2.03 | 19291 | 385.8 (-1.0 %) | +2.0 % |
   | 0421-off-r2 | 04:22:38 | 2.92 | 1907 | 46.0 | 2.54 | 19108 | 382.2 (-0.9 %) | +0.4 % |
   | 0423-q125-r3 | 04:24:41 | 4.03 | 1853 | 52.4 | 2.13 | 18422 | 368.4 (-5.4 %) | +9.0 % |
   | 0425-q250-r3 | 04:26:45 | 3.14 | 1996 | 44.0 | 1.98 | 19321 | 386.4 (-0.7 %) | +1.4 % |
   | 0440-q0-r4 | 04:41:09 | 2.81 | 1996 | 44.7 | 2.46 | 19201 | 384.0 (-0.5 %) | +0.0 % |

   - The runs between the two bursts were quiet and ran normally: 0411-q500-r1, 0413-q0-r2 and 0415-q125-r2 (04:12-04:17) had ng_t 2.28-2.36 and 388.7 / 385.1 / 391.0 fps.
   - From 04:28 on, every run was quiet except 0440-q0-r4 (ng_t 2.81, normal fps).
   - Pass 1 had no run at ng_t >= 2.8 (range 2.16-2.77). In pass 2, the quiet runs' median ng_t was 2.33 (load-check.md).
2. **The same arms ran normally when the host was quiet.**
   - q125's other 6 runs: 387.8-395.5 fps at 1.73-1.89 cores.
   - q250's 5 quiet runs: 386.1-389.9 fps at 1.71-1.91 cores.
3. **Load tracks fps within arms.** Spearman rho(ng_t, raw fps), centred on each pass's arm medians (load-check.md; the p-values are approximate):
   - W9-1: -0.85.
   - W9-2: -0.78.
   - Both p < 0.001.
   - The first runs of each pass were both the fastest and among the quietest, so warm-up adds to the pass-1 figure.
4. **The clock falls under load, and the q arms have more clock to lose.**
   - When the host is quiet, the q arms run ~200 MHz faster than off: eff 2108-2228 vs 1951-2027 MHz. They keep fewer cores busy.
   - Under load, the slow q runs fell to 1853-2075 MHz (-4 to -15 % vs their arm's quiet median), with E util 40-54 % vs ~34 %.
   - off's loaded run fell only 3 % (0421-off-r2, 1907 MHz).
5. **The back-off kept working.**
   - Thread cycle rates (busy % x eff GHz, load-check.md):

     | group | runs | Main XThread | GPU Commands |
     |---|---|---|---|
     | off | 8 | 152.9-169.7 (median 156.7) | 111.6-123.7 (median 116.4) |
     | q0 | 8 | 150.2-163.2 (median 155.8) | 114.7-119.8 (median 117.4) |
     | q125-q500, quiet | 18 | 135.4-149.5 (median 142.7) | 95.9-107.5 (median 102.5) |
     | q125-q500, loaded | 6 | 142.6-147.3 (median 146.3) | 101.2-108.5 (median 105.1) |

   - The loaded q runs did about the same work per second as the quiet ones (median +2.5 %), well below off. Their busy % rose because each cycle took longer.
   - Every q run logged its back-off init line once, and the env check passed 42 of 42 (Agent 6).
6. **Most of the cores rise is the clock drop.**
   - The loaded q runs used +0.20 to +0.38 more cores than their arm's quiet median.
   - At a constant core x MHz product, the same cycles at the lower clock would need 1.81-2.11 cores.
   - The rest is +0.02 to +0.13 core per run (load-check.md).
7. **The q arms are more exposed.**
   - Spin arms near the same load lost less: 0421-off-r2 (ng_t 2.92) -0.9 % fps, and 0440-q0-r4 (2.81) -0.5 %.
   - q runs lost more:
     - at ng_t 2.9-3.4: -0.7 to -2.6 %;
     - at 3.7-4.1: -2.8 to -6.3 % (raw median ms +5.9 to +9.0 %).
   - No off or q0 run saw ng_t > 3, so the spin arms' loss under the heaviest load wasn't measured. The "more exposed" reading rests on the clock data and on the ng_t ~2.9 pair (0421-off -0.9 % vs 0417-q250 -2.6 %).
   - Mechanism (hypothesis, not tested):
     - A q thread sleeps in the GPU wait, which frees cores and lets the CPU boost. Background load takes that headroom back.
     - A woken thread may also wait for a free core.
     - A spinning thread keeps its core and was never boosted, so it has less to lose.
8. **Tails:** the three longest frames of the window all fell in the loaded span:
   - 37.29 ms in 0409-q250-r1;
   - 23.29 ms in 0407-q125-r1;
   - 20.63 ms in 0421-off-r2 (an off run).
9. **Source of the load: unknown.**
   - There is no per-process sampling inside the windows.
   - Between W9-2 and W5b-2, the quiet gate held W5b-2 back 3 min while CrossDeviceService ran at 0.68-0.87 core (04:46-04:49; `perf-notes/SESSION2.md` L3291, Agent 8's note at audit.md L418). No sys.csv covers that span (audit.md L30-37).
   - The first four scored W5b-2 runs (04:54-05:02) were also loaded (ng_t 2.84-3.76; see W5b.md section 7).
   - It looks like the same kind of disturbance, but the source isn't proven.

**With and without the flagged runs:** without the 7 flagged runs, q125 and q250 sit next to q500:
- cores -0.72 each vs -0.79;
- q125 T-std p99 -2.2 % *.

So the instability changes no verdict (section 7).

## 7. With and without the flagged runs

**q500 vs off, % [95 % CI]:**

| pool (runs left out) | n q500 | primary (round p) | median ms (primary) | fps (primary) | p99 (primary) | 1 % low (primary) | raw median ms | raw fps | raw p99 | raw 1 % low |
|---|---|---|---|---|---|---|---|---|---|---|
| all 40 | 8 | T-std (0.051) | -2.5 [-5.6, +0.7] | -2.8 [-5.3, -0.3] * | -0.9 [-1.9, +0.2] | +2.4 [-1.3, +6.3] | -3.3 [-6.6, +0.1] | -1.3 [-4.3, +1.7] | -6.2 [-9.7, -2.6] * | +8.7 [+1.1, +16.8] * |
| no-flagged (7) | 7 | T-std (0.115) | -2.7 [-5.9, +0.5] | -2.8 [-5.5, +0.1] | -0.8 [-1.1, -0.4] * | +2.2 [+0.1, +4.3] * | -3.6 [-6.8, -0.2] * | -1.2 [-4.2, +1.9] | -6.4 [-7.8, -5.1] * | +8.8 [+4.3, +13.5] * |
| no-lowclk (4, Agent 9) | 7 | T-std (0.065) | -2.7 [-5.7, +0.4] | -2.8 [-5.3, -0.1] * | -0.7 [-1.2, -0.2] * | +2.2 [-0.3, +4.8] | -3.6 [-6.6, -0.4] * | -1.2 [-4.1, +1.8] | -6.4 [-8.0, -4.9] * | +8.8 [+3.9, +13.9] * |
| no-slow-q (4) | 8 | T-std (0.065) | -2.5 [-5.4, +0.5] | -2.8 [-5.3, -0.3] * | -0.7 [-1.1, -0.3] * | +2.2 [-0.0, +4.6] | -3.3 [-6.3, -0.2] * | -1.3 [-4.1, +1.5] | -6.2 [-7.6, -4.9] * | +8.7 [+4.2, +13.3] * |
| drop-p2-r1r3 | 6 | B-block T-std (0.049) | -2.5 [-5.7, +0.8] | -2.7 [-5.3, +0.1] | -0.6 [-1.2, -0.0] * | +2.7 [-0.3, +5.9] | -3.3 [-7.1, +0.6] | -1.1 [-4.6, +2.5] | -6.2 [-8.1, -4.3] * | +9.9 [+4.0, +16.2] * |
| drop-r1-both | 6 | T-std (0.555) | -5.0 [-6.6, -3.3] * | -0.6 [-1.4, +0.3] | -0.9 [-1.9, +0.1] | +3.0 [-0.5, +6.7] | -5.9 [-7.8, -4.0] * | +1.2 [-0.2, +2.6] | -6.8 [-9.7, -3.7] * | +10.3 [+3.6, +17.5] * |
| no-lowclk-no-r1 | 5 | T-std (0.986) | -5.2 [-5.9, -4.5] * | -0.4 [-1.0, +0.1] | -0.9 [-1.5, -0.3] * | +2.8 [-0.5, +6.2] | -6.2 [-6.9, -5.4] * | +1.4 [+0.6, +2.1] * | -7.0 [-8.5, -5.5] * | +10.5 [+4.3, +17.1] * |
| pass 1 only | 4 | T-std (0.104) | -1.6 [-7.2, +4.4] | -3.7 [-8.4, +1.2] | -0.7 [-1.3, -0.0] * | +1.7 [-1.7, +5.3] | -2.4 [-8.1, +3.8] | -2.2 [-7.4, +3.2] | -6.0 [-8.3, -3.7] * | +8.1 [+1.3, +15.4] * |
| pass 2 only | 4 | T-std (0.813) | -3.5 [-7.0, +0.0] | -2.0 [-4.3, +0.4] | -1.2 [-3.8, +1.5] | +3.4 [-4.6, +12.1] | -4.3 [-8.1, -0.3] * | -0.4 [-3.7, +3.0] | -6.4 [-12.5, +0.0] | +9.2 [-4.2, +24.4] |

**Cores change vs off [95 % CI]**, plus q500 vs the other q arms (load-check.md):

| pool | q0 | q125 | q250 | q500 | q500 - q250 | q500 - q125 |
|---|---|---|---|---|---|---|
| all 40 | -0.03 [-0.14, +0.08] | -0.62 [-0.73, -0.50] | -0.65 [-0.76, -0.53] | -0.75 [-0.86, -0.64] | -0.104 [-0.216, +0.008] | -0.133 [-0.245, -0.020] * |
| no-flagged | -0.03 [-0.08, +0.02] | -0.72 [-0.78, -0.66] | -0.72 [-0.78, -0.66] | -0.79 [-0.84, -0.73] | -0.069 [-0.130, -0.009] * | -0.071 [-0.132, -0.011] * |
| no-lowclk | -0.03 [-0.09, +0.03] | -0.70 [-0.76, -0.63] | -0.68 [-0.74, -0.62] | -0.79 [-0.85, -0.73] | -0.107 [-0.170, -0.044] * | -0.088 [-0.154, -0.022] * |
| no-slow-q | -0.03 [-0.10, +0.05] | -0.70 [-0.78, -0.62] | -0.70 [-0.78, -0.62] | -0.75 [-0.83, -0.67] | -0.051 [-0.134, +0.032] | -0.049 [-0.132, +0.034] |
| drop-r1-both | -0.04 [-0.16, +0.08] | -0.66 [-0.78, -0.54] | -0.67 [-0.79, -0.55] | -0.74 [-0.86, -0.63] | - | - |
| no-lowclk-no-r1 | -0.04 [-0.12, +0.03] | -0.71 [-0.79, -0.64] | -0.67 [-0.74, -0.60] | -0.80 [-0.87, -0.72] | - | - |
| pass 1 only | -0.02 [-0.10, +0.06] | -0.69 [-0.77, -0.61] | -0.74 [-0.82, -0.66] | -0.80 [-0.88, -0.72] | - | - |
| pass 2 only | -0.03 [-0.23, +0.17] | -0.54 [-0.74, -0.34] | -0.55 [-0.75, -0.35] | -0.70 [-0.90, -0.50] | - | - |

Notes on the table:
- The subsets other than pass 1 only / pass 2 only were chosen after looking at the data.
- `no-slow-q` drops the 4 runs the task named.
- `no-lowclk` drops Agent 9's 4 runs.
- `no-flagged` drops the union of Agent 9's and Agent 8's flags.
- Full tables for every arm are in pool-W9.md section 6.

**No verdict changes in any subset.** Three details move:
1. q500's T-std fps loss is significant in the full pool (-2.8 % *) but not in `no-flagged`, `drop-p2-r1r3` or `drop-r1-both`. Without round 1, raw fps turns positive (+1.2 %; +1.4 % * without the lowclk runs too). The loss comes from the position effect and the guard (a) mix shift, not from the back-off.
2. q500's extra saving over q250 is 0.05-0.11 core. It is significant in `no-flagged` and `no-lowclk` only.
3. Without the flagged runs, q125's tails beat q500's:
   - T-std p99: -2.2 [-2.6, -1.8] * vs -0.8 *;
   - raw p99: -9.8 * vs -6.4 *;
   - raw 1 % low: +15.7 * vs +8.8 *.

## 8. Pick and follow-ups

- **Pick q500.** PROPOSAL section 4's criterion is "the largest CPU drop with no p99 or 1 % low loss beyond the spread", and q500 meets it:
  - CPU: -0.75 core (-30 %) pooled and -0.79 without the flagged runs. That is the largest drop in every subset.
  - p99 and 1 % low are no worse than off in any method or subset: raw p99 -6.2 % *, raw 1 % low +8.7 % *.
  - In the quiet rounds (no round 1), raw fps is +1.2 to +1.4 % and raw median ms -5.9 to -6.2 % *.
- **Alternative: q125.** It costs ~0.07 core more (q500 - q125 = -0.071 [-0.132, -0.011] * without the flagged runs), but its tails are better in the clean subsets (section 7, item 3). Choose it if tails matter more than ~0.07-0.13 core.
- **The knee wasn't found:** the saving still grows from 250 to 500 us. An optional follow-up window would run:
  - off vs q500 vs q750 vs q1000;
  - with off not always first in round 1 (rotate the round-1 order), or with 2 unscored warm-up runs;
  - with a per-run quiet check (W5b.md section 7).

## 9. Caveats

- **Post hoc subsets and many tests.** The variants were chosen after seeing the data, except pass 1 only / pass 2 only, so treat their CIs as descriptive. There are 4 arms x 4 metrics x 3-4 methods, so a lone `*` can be chance. The verdicts above rest on results that hold across methods and subsets.
- **T-std is distorted here by guard (a)** (section 2). Don't quote W9's T-std fps alone.
- **Position effect** (section 2): off's two round-1 runs inflate its mean. Future windows should rotate the round-1 order or warm up longer.
- **Host state:**
  - Compare W9 only within itself. W9, W5b, W6 and W4c ran after the Defender exclusion for `build/` (~23:16 on Nov 22); W4b and W5 ran before it. Absolute fps, ms and cores across that line aren't comparable.
  - W9's overlay is best_performance; W5's was best_efficiency.
- **The quiet gate only checks at the window start.** The 04:08-04:27 bursts came mid-window.
- **eff MHz is rough.** It is a sys.json mean over all cores and the whole window, so the cycle and constant core x MHz figures are rough (a few %).
- **ng_t is a window mean**, so short bursts can matter more than the mean shows.

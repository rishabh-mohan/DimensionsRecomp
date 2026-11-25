# Cross-check of M8's night read-out (READOUT-NIGHT.md) - M10, 2026-11-25 06:40

Who/when: M10 (successor of Agent 10), read-only. Requested by the Overseer at 12:35Z. No game runs, no builds.
All checks ran at BelowNormal priority on the run-matrix pass dirs in build/agent8/matrix/.

## Files rated

| file | sha256 (16) | bytes |
|---|---|---|
| build/agent8/session3/READOUT-NIGHT.md | 196D312D52107819 | - |
| build/agent8/session3/readout/readout_night.py | 1A5F9BE0 (8) | 13435 |
| readout/wc.md | F34B19B3 (8) | 22970 |
| readout/w10-r1.md / w10-r2.md | A19226CA / D8710971 (8) | 7198 / 7178 |
| readout/w8a-r1.md / w8a-r2.md / -drop variants | 969A023A / 6BCFDAE8 / 707E0CEE / 9191A006 (8) | - |
| build/agent12/session3/NIGHT-GATES.md (as of now) | 6D83CF74 (8) | - |

Base: pass dirs 20261125-0315 (WC1), -0440 (WC2, reversed order), -0551 (WC3), -0519 (W10), -0359 (W8a).
Arms are from each pass's matrix.json / plan.txt.

## Verdict

**CONFIRMED.** All three parts (C, W10, W8a) hold. No BLOCKER.

- **C:**
  - win3 FASTER: fps +7.7 % [+6.3, +8.7], p99 -14.8 %, 1 % low -17.0 %, cores -38.7 %, TimerQueue 1.0-2.1 %.
  - c1np = p2fc, both +4.0 % fps.
- **W10:** NEUTRAL.
- **W8a:** mc FASTER, median -28.6 %, fps +44 %.

There are 4 SHOULDs:
- S1: the explanation of the median shape is incomplete; the conclusion stands.
- S2: the scope of the shipping claim.
- S3: the implications of dropping P2.
- S4: the clock reading on W10.

There are also 5 doc NITs. None of them changes a verdict.

## What I checked (independent of M8's script unless noted)

1. **Script review (readout_night.py):**
   - Kept rule: scored, status OK, valid_timing, not excluded, round >= min-round. Cold runs are round 0 and unscored, so they never count.
   - Nearest-rank p50/p99. The 1 % low is the mean of the slowest max(1, n/100) frames.
   - Bootstrap: percentile, 20000 draws, seed 1, indices [500] and [19499].
   - Paired cross-check: keyed by (pass, round), log ratio, t-CI.
   - TimerQueue: max busy_pct over the TimerQueue threads.
   - Slow state: longest run of e_eff < 800 inside the sys window.
   - No defect found.
2. **Frame re-read (my own dist_check.py)** over the 36 kept WC runs:
   - frames/window_s = 1000/mean(frame time) = frames.json mean_fps, identical in every arm median: s0 454.8, c1np 472.9, p2fc 472.9, win3 490.0.
   - The window frames cover window_s exactly (sum of frame times / window_s = 1.0000).
3. **Proof lines** in all 51 WC game.logs (my own proof_check.py), checked against the matrix plan notes:
   - win3: C1 on and first-kept lines, the 1 ms line, exactly 1 precise-wait line, exactly 1 back-off ON line.
   - c1np/p2fc: C1 lines, no back-off, no precise-wait.
   - s0: none of these.
   - All arms: no 'C1 verify: on' and none of the 4 bad strings.
   - **51/51 OK.** This matters because the kit's expect-w6.json has no rules for win3/c1np (NIGHT-GATES "kit coverage").
4. **Bins, env, frame source and flags** for all 5 passes:
   - WC: devoff4b-bin, perf. win3 env is the 2 GPU_WAIT keys; the others have env {}.
   - W10: devoff4b-bin vs devoff4b-cg26-bin, env {} in both.
   - W8a: native4b-bin, native frames; MISS_CACHE=1 in mc only.
   - 0 excluded runs. The only runner flag is light_share_high, on every run.
5. **GPU clock over each timed window** (my own gpu_check.py, gpu.csv):
   - Round 1 runs 1551-1718 MHz. Rounds 2-4 run 1483-1565 MHz in all 3 passes, so the plateau is reached by round 2 and the planned round-1 drop is justified.
   - All runs are SW-thermal throttled (0x20), temperature max 86-87 C.
   - Arm means over rounds 2-4: win3 ~1520, s0 ~1532, p2fc ~1540, c1np ~1547 MHz. win3 has the *lowest* GPU clock, so the GPU does not favour it.
6. **Frame content:** a sample of c1np perf.csv rows shows that short (~0.7 ms) and long (~3.8 ms) frames carry the same draw_calls (226) and vertices_processed (1022). The short frames are real rendered frames, not empty presents.
7. **Clock sensitivity (dist_check.py):** within-arm fps residual vs eff MHz gives r 0.42 and a slope of +0.54 % fps per 100 MHz (36 runs).

## Findings

### C (decides the shipping defaults)

- **Method: OK.**
  - The round-1 drop was pre-registered in the matrix plan (GPU warm-up), and item 5 confirms it.
  - With round 1 kept, the verdicts are unchanged.
  - The 3 passes include one reversed-order pass. The order residuals are small (slot within ±0.8 %, pass within ±0.6 %).
  - n = 9 per arm. A percentile bootstrap on medians of 9 runs is coarse and tends to come out narrow. However, the paired-round t-CIs and the sign counts (9/9 for fps, p99, 1 % low and cores) agree on every claimed result, so the claims are robust.

- **S1 (SHOULD, wording): the median-vs-fps caveat is handled correctly, but the stated reason is only half the picture.**
  - The frame-time distribution is **bimodal** in every arm. Pooled kept frames:

    | arm | p10 | p25 | p50 | p75 | p90 | mean | frames < 1.0 ms | > 4.0 ms |
    |---|---|---|---|---|---|---|---|---|
    | s0 | 1.146 | 1.362 | 2.009 | 2.838 | 3.563 | 2.213 | 1.9 % | 6.3 % |
    | c1np | 0.808 | 1.077 | 2.099 | 2.725 | 3.710 | 2.122 | 19.8 % | 6.3 % |
    | p2fc | 0.808 | 1.077 | 2.103 | 2.725 | 3.696 | 2.118 | 19.8 % | 6.2 % |
    | win3 | 0.649 | 1.219 | 2.116 | 2.587 | 3.228 | 2.047 | 20.8 % | 2.0 % |

  - The dominant change is a **new short-frame mode (< 1.0 ms: 1.9 % -> ~20 %) that comes with C1**: it appears in all three C1 arms and is identical in c1np and p2fc. Long-short alternation like this means frames are completing in pairs.
  - M8's "heavier body above the median" is also true for s0 (frames of 2.5-3.5 ms add 0.78 ms/f in s0 vs 0.61 in c1np), but it is the smaller part.
  - In a bimodal distribution, the median sits between the modes and moves with the weight of each mode. That is why it rises while the mean frame time falls.
  - The conclusion holds: use fps mean (= 1000/mean frame time, which is genuine throughput because the short frames carry full draw work), p99 and the 1 % low. Do not use the median.
  - win3 additionally pulls in the tail: > 4 ms frames fall 6.3 % -> 2.0 %, and time in > 3.5 ms frames falls 0.45 -> 0.26 ms/f.
  - Fix: one sentence in READOUT-NIGHT saying that the shape change is C1's bimodal short-frame mode.

- **win3's clock difference: EFFECT, not a confounder. I agree with M8, with this evidence:**
  - The arms are interleaved in Latin-square rounds, and one pass is reversed.
  - Every win3 run's eff MHz is above every s0 run's (2156-2326 vs 1939-2053).
  - The GPU clock is not higher for win3 (item 5).
  - The whole machine is thermally limited: the GPU SW-thermal throttles throughout. Fewer busy cores leave more budget, so the CPU boosts higher.
  - Size: using the within-arm slope, at most ~1.2 points of win3's +7.7 % fps is clock-mediated. The rest is direct.
  - Consequence: part of the gain is specific to this power/thermal-limited laptop. On a machine with headroom, expect somewhat less fps gain. The core saving (-0.95) is the most transferable number.

- **S2 (SHOULD, shipping scope):** the C result covers:
  - one light route (light_share_high on 51/51 runs, ~226 draws/frame);
  - uncapped (framerate_limit=0), at ~450-490 fps;
  - AC power only.

  The win3 bundle sets host_timer_resolution_ms=1 and host_timer_throttling_optout=true. Their idle and battery power cost was not measured. State these limits next to the shipping decision. At a 60 fps cap, the visible benefit is CPU headroom and tail, not fps.

- **S3 (SHOULD, keep/drop):**
  - **win3 as the shipped timer bundle: supported as timed.**
    - It is faster on every throughput and tail metric and costs about 1 core less.
    - TimerQueue < 15 % is met (1.0-2.1 %).
    - Proofs are 51/51, gates PASS, STUCK 0.
    - The watchdog lines (0504-c1np-r3, 0619-s0-r4) come after WM_CLOSE and occur in two arms, one of them the reference.
  - This window measures d11p and q500 only together: +3.6 % fps, -15.5 % p99, -34 % cores vs p2fc. The per-component evidence remains W5b/W9.
  - win3 enabled q500 through env. The code-default form is covered by my q500-default-rating (DB5D1282), whose conditions still apply.
  - **P2 ("c1np over p2fc adds nothing"):** precisely, P2 (shared_memory_single_hold_rearm) adds nothing measurable once C1 is on. All 5 contrasts have CIs within about ±2.6 %, and the paired signs are 5-6 out of 9.
  - Either choice is defensible:
    - (a) Keep P2: win3 stays exactly the timed config.
    - (b) Drop P2: simpler, but "win3 minus P2" was never timed. It needs a functional gate plus at least one confirming timing pair (vs win3) before it ships as a default.
  - I recommend (a) for this build unless P2 carries a safety cost.

### W10 (cg26 vs s0): NEUTRAL confirmed

- Every CI includes 0, with or without round 1. M8's r26 condition list matches the pass: both bins, env {} in both arms, cold first cg26 run, gates PASS, STUCK 0.
- With n = 6 per arm, the CIs only rule out effects larger than about +4 % fps / +8 % median. Read the result as "no difference detected", not "no effect".
- **S4 (SHOULD, INFO-level): cg26 ran at a higher eff clock in 6/6 rounds**, averaging +121 MHz (2117 vs 1996) at the same cores (2.40 vs 2.45).
  - The within-window slope is -2.83 % median per 100 MHz (r -0.59, n 12). The clock lift, which may itself be the pause effect (less power in spin-waits), could be masking a small per-clock cost.
  - The net effect is what counts, and it is NEUTRAL. It gives no timing reason to ship cg26 on by default.
- The cg26-r5 burst (20 frames > 8 ms in 0.54 s) is a single event. My r26 N3 watch applies only if it repeats.

### W8a (mc vs n0, native4b): mc FASTER confirmed

- 7/7 paired rounds go to mc. Dropping round 1 or 0404-mc-r2 moves the numbers by 1 point or less.
- mc's eff clock is *lower* than n0's (2142 vs 2197), so the gain is not clock-driven.
- n0 drifts slower after round 1. mc is stable at 2.137-2.209 ms.
- The n0 cold run (2.424 ms at 2784 MHz) is unscored and does not change the verdict.
- Gate dependency: W8a's gate PASS rested on M12's hand override of G9 (the `<run>` env placeholder), which the Overseer accepted at 12:32Z. The mechanical PASS comes from the runexp re-gate, whose run_gates change I rate next. The read-out stands either way, because the hand check found BAD 0.

### NITs (doc)

- N1: the C table's "fps mean" column is the arm *mean* (451.9 / 488.4), but the contrasts use the arm *median* (454.8 / 490.0). Label it, or show the median, so that +7.7 % is reproducible from the table.
- N2: the Method section says fps comes from the sys.json window. In fact it is frames.json mean_fps = frames/window_s (item 2).
- N3: NIGHT-GATES is cited as 7533DD5E, but the current file is 6D83CF74 (it adds the override acceptance and the runexp re-gate). "PASS for all 5 windows" should mention the W8a G9 override and the WC2 G8 CHECK that was cleared by hand.
- N4: the matrix plan asks for "gpu.csv: round 2 starts at the steady clock" and names 832 MHz. The read-out should record the check. The observed plateau is ~1490-1565 MHz, not 832, reached by round 2 (item 5).
- N5: state in the read-out that the per-run proof lines were checked, since the kit has no win3/c1np rules. My proof_check result (51/51 OK) can be cited.

## Conditions on using the read-out for shipping defaults

1. Ship win3 as the timed set, including P2 (or follow S3(b)).
2. Record the scope from S2 (light route, uncapped, AC, laptop thermal limit) in the decision.
3. The q500-default-rating conditions apply to the code-default q500 in the final build.
4. cg26 stays off by default; W10 gives no timing case for it.

## Read / sent

- Scratch: build/agent10/session3/scratch-readout/ (dist_check.py, gpu_check.py, proof_check.py; outputs dist_wc.out.txt, gpu_wc.out.txt, proof_wc.out.txt).
- Sent to the Overseer after writing.

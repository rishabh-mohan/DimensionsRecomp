# Night read-out 2026-11-25 (M8)

Read-only. Script: `build/agent8/session3/readout/readout_night.py`. Full tables and per-run rows are in `readout/wc.md`, `wc-<pass>.md`, `wc-r1.md`, `w10-r1.md`, `w10-r2.md`, `w8a-r1.md`, `w8a-r2.md` and `w8a-r*-drop.md`.

**Method.**
- A run is kept if it is scored, status OK, valid_timing True and not excluded.
- Per run:
  - median and p99 come from frames.json (nearest rank);
  - fps = frames.json mean_fps (= frames / window_s = 1000 / mean frame time);
  - **1 % low** = mean of the slowest 1 % of frame times in the window, re-read from the frame source. The re-read median/p99 matched frames.json on all 79 runs;
  - process cores (window mean), and eff/P/E MHz from the sys.json window;
  - TimerQueue busy % from threads.csv (window);
  - slow state: sys.csv e_eff < 800 MHz for at least 3 rows. It was 0 in every run.
- **Contrast** = difference of the arm medians of the run values (A - B), as % of B, with a 95 % percentile bootstrap CI: runs resampled within each arm, 20000 draws, seed 1.
- Cross-check: the paired-by-round log-ratio mean with a t-CI, plus the number of rounds with A < B.
- Rule: a result is claimed only when the CI excludes 0.

M12's night gates (NIGHT-GATES.md, now 6D83CF74) PASS for all 5 windows. W8a's PASS rests on M12's hand override of G9 (the `<run>` env placeholder; hand check BAD 0, accepted by the Overseer at 12:32Z; mechanical re-gate pending). WC2's G8 CHECK was cleared by hand. All 79 runs: exit 0, no WER, no dumps, 0 STUCK lines in game.log.

Proof lines: M10's proof_check (build/agent10/session3/readout-night-xcheck.md 25BF9B1C, item 3) checked all 51 WC game.logs against the plan notes: 51/51 OK. win3 has the C1, 1 ms, precise-wait and back-off ON lines; c1np/p2fc have C1 only; s0 has none; no "C1 verify: on" anywhere. This matters because the kit's expect-w6.json has no win3/c1np rules.

GPU warm-up check (matrix plan: "round 2 starts at the steady clock"; M10 xcheck item 5, gpu.csv): round 1 runs at 1551-1718 MHz, rounds 2-4 at 1483-1565 MHz in all 3 passes. The plateau is **~1500 MHz** (not the 832 MHz the plan named) and is reached by round 2, so the round-1 drop is justified. All runs are GPU SW-thermal throttled (max 86-87 C). win3 has the lowest GPU clock of the 4 arms (~1520 vs s0 ~1532), so the GPU does not favour it.

**Scope (M10 S2).** The C result covers one light route (light_share_high on 51/51 runs, ~226 draws/frame), uncapped (framerate_limit=0, ~450-490 fps), on AC power only. The idle and battery power cost of win3's host_timer_resolution_ms=1 / host_timer_throttling_optout was not measured. At a 60 fps cap the visible benefit is CPU headroom and tail, not fps.

## (1) C confirmation: WC1 0315 + WC2 0440 (reversed) + WC3 0551; rounds 2-4; 9 runs per arm

All columns are the **arm median of the run values** (the numbers the contrasts use); arm means of fps in brackets.

| arm | median ms | fps (mean) | p99 ms | 1 % low ms (fps) | cores | eff MHz (mean) | TimerQueue busy % (min-max) |
|---|---|---|---|---|---|---|---|
| s0 | 1.994 | 454.8 (451.9) | 4.921 | 5.354 (187) | 2.455 | 2019 | 19.7-22.2 |
| win3 | 2.112 | 490.0 (488.4) | 4.194 | 4.445 (225) | 1.504 | 2243 | **1.0-2.1** |
| c1np | 2.085 | 472.9 (471.1) | 4.971 | 5.298 (189) | 2.267 | 2103 | 19.2-22.1 |
| p2fc | 2.095 | 472.9 (472.2) | 4.963 | 5.319 (188) | 2.279 | 2095 | 18.7-22.0 |

| contrast | median ms | fps mean | p99 | 1 % low ms | cores |
|---|---|---|---|---|---|
| win3 vs s0 | **+5.9 % [+4.6, +7.5]** | **+7.7 % [+6.3, +8.7]** | **-14.8 % [-17.1, -14.0]** | **-17.0 % [-18.0, -14.9]** | **-38.7 % [-40.3, -35.2]** |
| c1np vs s0 | **+4.6 % [+3.7, +6.6]** | **+4.0 % [+2.9, +4.8]** | +1.0 % [-2.1, +2.6] | -1.0 % [-2.4, +1.5] | **-7.6 % [-9.2, -5.7]** |
| p2fc vs s0 | **+5.1 % [+3.7, +7.3]** | **+4.0 % [+3.3, +4.9]** | +0.9 % [-2.1, +2.0] | -0.7 % [-2.2, +1.1] | **-7.2 % [-8.5, -5.3]** |
| win3 vs p2fc | +0.8 % [-1.3, +2.0] | **+3.6 % [+2.1, +4.6]** | **-15.5 % [-17.3, -12.7]** | **-16.4 % [-17.2, -14.8]** | **-34.0 % [-35.5, -31.2]** |
| c1np vs p2fc | -0.5 % [-2.6, +1.1] | -0.0 % [-1.2, +0.7] | +0.2 % [-1.5, +2.4] | -0.4 % [-1.6, +2.0] | -0.5 % [-1.8, +0.7] |

The paired-round cross-check agrees on every bold result: for fps and cores 9/9 rounds go the same way, and for the median 8/9.

**Verdicts.**
- **win3: FASTER.**
  - Mean fps +7.7 %, p99 -15 %, 1 % low -17 %, and 0.95 fewer process cores. TimerQueue drops from about 22 % to 1-2 %, so it **meets the < 15 % gate**. s0, c1np and p2fc are all about 19-22 %, so the timer bundle with `timer_queue_precise_wait` is what moves TimerQueue.
  - Against p2fc, the extra parts (d11p + q500) add +3.6 % fps, -15 % p99 and -34 % cores.
- **c1np and p2fc: FASTER on throughput** (+4.0 % fps, -7 % cores). The tail is unchanged (p99 and 1 % low CIs include 0).
- **c1np = p2fc:** every CI includes 0, so P2 adds nothing measurable on top of fix (i) + C1.
- **The median frame time goes UP about 5 % in all three arms, while mean fps goes up 4-8 %.** The frame-time distribution is bimodal in every arm, and the main change is a **new short-frame mode that comes with C1** (M10 S1, pooled kept frames): frames < 1.0 ms go from 1.9 % in s0 to ~20 % in c1np/p2fc/win3, identical in c1np and p2fc. In a bimodal distribution the median sits between the modes and moves with their weights, so it rises while the mean frame time falls. The short frames carry full draw work (same draw_calls/vertices as long ones), so fps mean is genuine throughput. A heavier s0 body at 2.5-3.5 ms is the smaller part. win3 also pulls in the tail: frames > 4 ms fall from 6.3 % to 2.0 %. Use fps mean, p99 and the 1 % low as the verdict metrics, not median ms.

**Order and window effects.**
- Mean residual of a run's median against its arm mean:
  - by slot within the round: +0.4 / -0.3 / -0.7 / +0.8 %;
  - by pass: +0.4 / -0.6 / +0.3 % (WC2, with the reversed order, is not different);
  - by round: +0.7 / -0.6 / -0.1 %.
- Per pass, the direction is the same in all 3 passes (win3 fps +6.3 / +7.7 / +8.3 %, p99 -15.1 / -14.2 / -16.9 %; c1np and p2fc fps +3.6 to +4.4 %). With n = 3 per arm per pass, per-pass CIs are not meaningful.
- Keeping round 1 changes nothing: win3 fps +8.3 % [+7.4, +9.1], p99 -15.2 %; c1np/p2fc fps +4.7 / +4.3 %, p99 CIs still include 0.

**Clocks.**
- The arms differ in eff MHz: win3 averages 2243, s0 2019 (per-run range 2156-2326 vs 1939-2053). That follows from the lower load (fewer busy cores, more boost), so it is part of the effect, not a confounder.
- Within an arm, clock vs residual gives r = -0.27 over 36 runs (weak). M10's within-arm fps slope (+0.54 % per 100 MHz) bounds the clock-mediated part of win3's +7.7 % fps at ~1.2 points.
- WC2 0504-c1np-r3 and WC3 0619-s0-r4 each had a shutdown-watchdog line after WM_CLOSE (M12). This was outside the timed part; both runs were kept.

## (2) W10 0519: cg26 vs s0 (devoff4b-bin vs devoff4b-cg26-bin, env {}, 6 rounds)

| set | median ms | fps mean | p99 | 1 % low ms | cores |
|---|---|---|---|---|---|
| rounds 1-6 (6 vs 6) | +3.3 % [-4.4, +7.7] | +0.5 % [-1.3, +4.2] | +2.0 % [-2.3, +6.4] | +3.2 % [-1.0, +8.7] | -1.4 % [-4.1, +0.1] |
| rounds 2-6 (5 vs 5) | +2.0 % [-8.6, +8.0] | +1.1 % [-1.8, +7.0] | +3.1 % [-3.5, +7.6] | +4.4 % [-2.6, +11.7] | -2.3 % [-4.2, +0.1] |
| round 1 alone | s0-r1 1.968 ms vs cg26-r1 (its cold first launch, no cache) 2.067 ms: +5.0 %; p99 4.977 vs 5.006; 1 % low 5.452 vs 5.417 | | | | |

- **Verdict: NO DIFFERENCE detected (NEUTRAL)**, with or without round 1. Every CI includes 0. The runner's "+3.3 % median" equals my rounds 1-6 number and is noise.
- Paired rounds: fps +1.3 % [-0.4, +3.2] for rounds 1-6 and +1.8 % [+0.0, +3.6] for rounds 2-6 (lower bound at 0.0, not a claim).
- cg26-r1 was its cold first launch. Its window starts 60 s after the first frame, and its numbers sit inside the cg26 range.
- **M10 r26-cg26.md (423FE10F) conditions:**
  1. Bins: devoff4b-bin and devoff4b-cg26-bin per run.json; the bin check is the launcher's, and M12 PASS. **Met.**
  2. env_set {} in all 13 runs. **Met.**
  3. Separate caches; cg26's first run was cold (r1, scored, normal numbers). **Met.**
  4. Per-run functional check: all 6 cg26 runs exit 0, no WER, no dumps, status OK; level and K/F gating are M12's (PASS). **No cg26 FAIL, so the arm stands.**
  5. STUCK-LOCK: 0 per arm (s0 0, cg26 0; no STUCK line in any game.log). **Met.**
  6. On the timing desktop. **Met.**
  7. The result covers devoff4b arm A only.
- One note: cg26-r5 (0539) had **20 frames > 8 ms in a single 0.54 s burst** (t ≈ 24.6-25.2 s, max 19.6 ms). That gives it a 1 % low of 5.94 ms. Its sys flags were none, cpu 51 %, no input. s0 had 3 frames > 8 ms over all its runs, in s0-r1. One burst in one run cannot be attributed. M10's N3 (an added-latency watch) applies only if it repeats.

## (3) W8a 0359: mc vs n0 (native4b-bin, frames native)

| set | median ms | fps mean | p99 | 1 % low ms | cores |
|---|---|---|---|---|---|
| rounds 1-7 (7 vs 7) | **-28.6 % [-30.9, -27.5]** | **+44.2 % [+40.1, +45.5]** | **-34.1 % [-44.6, -23.7]** | **-34.3 % [-46.9, -25.4]** | -0.7 % [-4.2, +11.7] |
| rounds 2-7 | **-29.0 % [-31.0, -27.4]** | **+44.5 % [+37.0, +45.7]** | **-36.7 % [-51.5, -17.5]** | **-37.1 % [-53.7, -18.7]** | -1.5 % [-4.4, +11.8] |
| rounds 1-7 without 0404-mc-r2 | **-28.5 % [-30.9, -26.7]** | **+44.3 % [+34.6, +45.6]** | **-34.2 % [-45.7, -17.0]** | **-35.1 % [-47.5, -18.9]** | -1.0 % [-4.2, +5.6] |
| rounds 2-7 without 0404-mc-r2 | **-29.0 % [-31.0, -26.9]** | **+44.5 % [+32.0, +45.8]** | **-36.7 % [-51.6, -7.8]** | **-37.8 % [-55.0, -8.6]** | -1.8 % [-5.0, +11.2] |

- **Verdict: mc FASTER** (the #2 miss cache ON on native4b). In every variant, mc wins in every paired round (7/7, 6/6, 5/5): median about -29 %, fps about +44 %, p99 about -34 to -37 %, and 1 % low about -34 to -38 %. Process cores show no difference.
- mc is very stable: run medians 2.137-2.209 ms. n0 runs 2.795-3.087 ms and has 16 frames > 8 ms; mc has 1.
- **Cold run:** it is unscored and is not in any set. n0's cold run (2.424 ms, 30 s window) was faster than every scored n0 run, but its clock was 2784 MHz against 2120-2360 for the others. It does not change the verdict: mc's typical run is still 11 % faster than even that cold run.
- **light_share_high:** INFO on all 15 runs in both arms, so it cannot bias the contrast. Dropping flagged runs would leave no data; the flag is not a factor.
- **0404-mc-r2:** M12 flagged non-game load 4.66. Dropping it changes the results by ≤ 1 point. As a non-game-load hint, it had the highest mc cores (2.09) but a normal median (2.137).
- Order: slot ±0.6 %. By round, n0 drifts slower (r1 2.795 ms, then about 3.0 from r2 on); round 1 dropped or not, the result stands.

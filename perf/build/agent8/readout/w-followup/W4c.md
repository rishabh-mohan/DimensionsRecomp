# W4c read-out: codegen B vs d0 (one pass)

Agent 8, task #20, 2026-11-23. Method: [PROPOSAL.md](../../w-followup/PROPOSAL.md) §3. Only one pass ran; the second was skipped.

## Answer

- **B gives no gain.** Over 6 rounds, the paired median frame time is **+2.6 % [−1.2, +6.5]** (B was lower in 1 of 6 rounds). fps is **−1.7 % [−4.9, +1.7]** and CPU is **+0.063 cores [−0.007, +0.133]**. Every CI includes 0. Agent 7's T-std read-out agrees: +2.7 % [−0.8, +6.3] median and −2.0 % [−4.8, +1.0] fps.
- **W4b's fps hint did not repeat.** W4b showed B at +6.4 % fps (+15.1 % without its run 6). Tonight's fps CI tops out at +1.7 % (T-std +1.0 %), so both W4b values fall outside it. W4b ran under a different host state (see [Caveats](#caveats)), so W4c refutes the hint only for tonight's host.
- **Lead, not a finding: B may be about 1 % slower.** Without round 1 (the warm-up-biased round, see below), Agent 7's T-std gives B **+1.4 % [+0.5, +2.3]\*** median and **−0.8 % [−1.0, −0.6]\*** fps. Three things keep this a lead:
  - its light-share guard warns (F 9.53, p 0.015);
  - my paired CI just includes 0 (+1.1 [−0.1, +2.4]);
  - the cut was chosen after looking at the data.
- **Tails:** B's extra >6 ms frames all come from two back-to-back runs, 0251-B-r3 and 0253-B-r4, between 02:51 and 02:56. The per-second audit shows host CPU load in both: a 2-second burst in 0251 and raised load through 0253. Without those two runs, B's tails match d0's.
- **Health:** all 13 runs were clean. There were 0 failures, 0 KILLED, 0 STUCK-LOCK, 0 dumps and 0 slow-state runs.

**Verdict:** B has no timing gain over d0 on this host. Don't adopt B for performance. It is neutral or slightly slower and uses slightly more CPU (both leads). Telling 1 % apart from 0 would need a second pass with a GPU warm-up before scoring (see [Round 1](#round-1-and-warm-up-bias)).

## Inputs

| item | value |
|---|---|
| folder | `build/agent8/matrix/20261123-0239`: 6 rounds × 2 arms plus 1 cold d0, arm order alternating (d0 first in odd rounds) |
| matrix / results.csv | matrix.json sha E2E3E4DAAF7D30C7, results.csv A4F0ACC2CD2FB49A |
| d0 (ref) | `build/agent2/devoff2-bin` = S2 sources + S1 codegen, MANIFEST B87DC2D2CA22379F, exe 7F0B1C1C84BC66FF (170.3 MB). Same bin as W3 and W4b d0 |
| B | `build/agent2/devoffB-bin` = S2 sources + codegen B (Agent 9's recipe), MANIFEST 8709476FF4778768, exe C3F8686EBDD83340 (153.6 MB) |
| window | 02:39 to ~03:06 Nov 23; runner 26.2 min; 50 s scored window per run (cold run 30 s, unscored) |
| host | best_performance overlay in every sys.csv sample; Balanced scheme; P/E clocks ~1.95-2.0 GHz; E-clock minimum 1634 MHz, with 0 samples < 800 MHz; STRICT quiet gate at 02:39:45 (MsMpEng 0); Defender exclusion for `build/` in place |

## §3 counts

| arm | planned | timed | failed (exit ≠ 0) | KILLED | STUCK-LOCK (owner sites) | hang dumps | slow-state | flagged: G12 / sys.csv audit | host CPU at hangs |
|---|---|---|---|---|---|---|---|---|---|
| d0 | 6 + 1 cold | 6 + 1 cold | 0 | 0 | 0 (all sites 0) | 0 | 0/6 (cold 0/1) | 0 / 0 | n/a (no hangs) |
| B | 6 | 6 | 0 | 0 | 0 (all sites 0) | 0 | 0/6 | 0 / 1 (0253-B-r4) | n/a (no hangs) |

- **Exit:** every run exited 0 after a single WM_CLOSE.
- **Agent 6's kit** ([RESULTS.md](../../../agent6/wnight/RESULTS.md)): all PASS; 0 NEW/GONE/ONLY; no NOTE.
- **Audit** ([audit.md](audit/audit.md) §4): 0 [error]/[critical]/STUCK/hang/alarm lines in the 13 game.logs, 0 .dmp files, 0 WER.
- **Slow state:** Agent 11's 3-mode timerq copy found 0 slow runs ([timerq3-20261123-0239.txt](audit/timerq3-20261123-0239.txt), audit §1).
- Both arms have 6 timed runs, so both get a timing verdict.

## B vs d0 (all scored runs)

Paired values come from per-round log ratios: mean with a t-CI in %, plus a sign test. "band" is (max − min)/median over the arm's runs.

| arm | n | median ms (median of runs) | vs d0 | paired median % [95 % CI] | B lower in | fps median | fps mean | paired fps % [CI] | CPU cores | paired cores [CI] | frames mean (min-max) | band | CV |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d0 | 6 | 2.468 | – | – | – | 385.3 | 391.5 | – | 2.533 | – | 19575 (19249-21090) | 10.0 % (1.7 % without r1) | 3.9 % |
| B | 6 | 2.500 | +1.3 % | +2.6 [−1.2, +6.5] | 1/6 (p 0.219) | 383.9 | 384.6 | −1.7 [−4.9, +1.7] | 2.596 | +0.063 [−0.007, +0.133] | 19232 (19103-19427) | 1.6 % | 0.6 % |

**Agent 7's read-out** ([a7/W4c.md](a7/W4c.md)): there is no round effect (F 1.55, p 0.322), so T-std is primary.

| metric | B vs d0 (T-std) |
|---|---|
| median ms | +2.7 [−0.8, +6.3] |
| fps | −2.0 [−4.8, +1.0] |
| p99 | +0.2 [−0.4, +0.8] |
| 1 % low | −3.8 [−9.2, +1.9] |

Its guards all pass: (a) light share 0.968 vs 0.971 (F 1.52, p 0.245); (b) the raw values agree; (c) 0 of 12 runs flagged. G11 OK.

**Noise and precision:**
- PROPOSAL expected about ±2.7 % on median and ±2.3 % on fps. The pass achieved ±3.9 % / ±3.3 % paired (T-std ±3.6 % / ±2.9 %).
- Round 1 accounts for most of the width: B − d0 is +0.226 ms there, against a median of +0.041 ms over the other rounds.
- Without round 1 the paired CI is ±1.3 % on median and ±0.5 % on fps.

## Per round

| round | order | d0 run | d0 ms | B run | B ms | B − d0 ms | B − d0 fps | B − d0 cores | note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | d0 first | 0241 | 2.246 | 0243 | 2.472 | +0.226 | −33.3 | +0.022 | 0241 is the window's first scored run: 421.8 fps, +9.5 % vs d0's other runs |
| 2 | B first | 0247 | 2.471 | 0245 | 2.512 | +0.041 | −1.1 | +0.035 | |
| 3 | d0 first | 0249 | 2.451 | 0251 | 2.502 | +0.051 | −3.0 | +0.091 | 0251: 30-40 s burst of >6 ms frames |
| 4 | B first | 0255 | 2.493 | 0253 | 2.491 | −0.002 | −2.9 | +0.157 | 0253: sys.csv flag; eff_mhz 1831 (the others 1930-1996) |
| 5 | d0 first | 0257 | 2.491 | 0259 | 2.498 | +0.007 | −1.2 | −0.029 | |
| 6 | B first | 0303 | 2.465 | 0301 | 2.510 | +0.045 | +0.3 | +0.104 | |

The cold run 0239-cold-d0 measured 2.186 ms (unscored).

## Sensitivity: with and without flagged runs

| cut | runs (d0 + B) | mine: paired median % | B lower in | paired fps % | paired cores | Agent 7 primary: median % | Agent 7: fps % |
|---|---|---|---|---|---|---|---|
| all | 6 + 6 | +2.6 [−1.2, +6.5] | 1/6 | −1.7 [−4.9, +1.7] | +0.063 [−0.007, +0.133] | T-std +2.7 [−0.8, +6.3] | −2.0 [−4.8, +1.0] |
| without flagged (0253-B-r4) | 6 + 5 | +3.1 [−1.5, +8.0] | 0/5 (p 0.062) | −1.9 [−6.1, +2.5] | +0.045 [−0.023, +0.112] | T-std +2.8 [−1.1, +6.9] (guards OK) | −1.9 [−5.1, +1.4] |
| without round 1 | 5 + 5 | +1.1 [−0.1, +2.4] | 1/5 | −0.4 [−0.9, +0.0] | +0.072 [−0.017, +0.160] | T-std **+1.4 [+0.5, +2.3]\*** (light-share WARNING) | **−0.8 [−1.0, −0.6]\*** |
| without 0251 + 0253 | 6 + 4 | +3.4 [−3.3, +10.6] | 0/4 | −2.2 [−8.2, +4.3] | +0.033 [−0.054, +0.120] | T-std +2.8 [−1.7, +7.6] | −1.9 [−5.6, +2.0] |
| without round 1, 0251, 0253 | 5 + 3 | +1.3 [−0.8, +3.4] | 0/3 | −0.2 [−0.7, +0.4] | +0.037 [−0.129, +0.202] | – | – |

No cut shows a gain for B. The only CIs that exclude 0 point toward B being slower (Agent 7's round-1-free cut), and that result carries a guard warning.

## Tails

| arm | >6 ms /min | >8 ms /min | >10 ms /min | >16.7 ms /min | max ms | p99.9 median | paired p99.9 diff ms |
|---|---|---|---|---|---|---|---|
| d0 | 3.4 | 0.2 | 0.2 | 0 | 10.26 | 5.621 | – |
| B | 12.4 | 6.0 | 4.4 | 1.0 | 20.66 | 5.622 | +0.285 [−0.274, +0.843] (higher in 3/6) |
| B without 0251 + 0253 | 1.5 | 0 | 0 | 0 | 7.39 | 5.558 | −0.042 [−0.163, +0.080] (higher in 1/4) |

All of B's excess comes from two consecutive runs:
- **0251-B-r3** (02:51:43-02:53:38): 20 of its 22 frames over 6 ms fall between 30 and 40 s, including 5 frames over 16.7 ms and the 20.66 ms maximum at 33.9 s. The run-level audit does not flag it (non-game CPU 2.56 cores over the run), but the per-second data shows a host burst at that moment (audit §5.2). At T 33.8-34.8 s, non-game CPU rose to 4.2-5.2 cores (about 2 before), E-core load to 59-64 % and the P/E clocks fell to ~1650-1800 MHz. The load stayed raised (3.8-3.9 cores) for 2 more seconds. That is the same kind of burst as 0352's in W6.
- **0253-B-r4** (02:54:48-02:55:38): 35 frames over 6 ms, spread over all 10 s bins, maximum 14.07 ms. It is W4c's only flagged run. Non-game CPU averaged 3.09 cores against 2.48 for the rest (z 10.6), with 21 of 50 s above the folder's p90. Its mean E clock, 1837 MHz, was the folder's lowest.

The d0 runs on either side (0249 and 0255) were clean, and B's other 4 runs had fewer >6 ms frames than d0 (1.5 vs 3.4 per minute). Both runs carry host load in the per-second data: a short burst in 0251 and raised load through 0253, whose P/E clocks were the window's lowest. So B's tail excess is host load that landed on two consecutive B runs between 02:52 and 02:56. One pass can't fully exclude a B-specific cause.

## Round 1 and warm-up bias

- In every window tonight, the first scored run is the base arm's round 1, and it is that arm's fastest run (fps vs the arm's other runs):

  | window | first run vs the arm's others |
  |---|---|
  | W4c | +9.5 % |
  | W6 (pass 1 / pass 2) | +15.9 % / +8.6 % |
  | W9 (pass 1 / pass 2) | +15.0 % / +6.3 % |
  | W5b (pass 1 / pass 2) | +8.0 % / +2.0 % |

  Source: [xcheck.md](xcheck/xcheck.md). This biases round 1 toward the base arm.
- **Cause: GPU warm-up (audit §5.5).** After the idle gap before each window, the GPU ran above its steady 832 MHz in the first runs. In W4c that was 1021 MHz for d0-r1 and 855 MHz for B-r1; every later run sat at 832 MHz. At 832 MHz the GPU is at its thermal limit: every GPU sample carries the software thermal-throttle bit, at 86-88 °C. Run fps follows the GPU clock: Spearman rho 0.65 (p 0.021) in W4c, and 0.52-0.70 in W6-1, W6-2, W9-1 and W5b-1. W9-2 and W5b-2 show no such link (rho ≈ 0); their early runs carried extra non-game load (audit §2 and §5.6).
- **Lead: at steady state this host looks GPU-limited.** d0 and B ran at 98-100 % GPU utilisation at 832 MHz. A change that only saves CPU would then show up as fewer cores rather than more fps.
- **Suggestion for future windows:** warm the GPU before scoring, since tonight its clock settled only after 5-13 min of game load. For example, add discarded runs until gpu.csv shows the steady clock. Also rotate the first arm across rounds.

## Caveats

- **Cross-window:** W4b (`build/agent8/matrix/20261122-1541`) ran on the **best_efficiency** overlay, with P clocks flat at ~1.93 GHz and some slow-state runs. It also ran **before** the Defender exclusion for `build/` (added ~23:16 Nov 22). W4c ran on best_performance, after the exclusion, with 0 slow-state runs. Absolute numbers don't compare across the two. W4c shows that B gives no gain on tonight's host. It does not show why W4b's hint appeared.
- One pass only. The precision is below PROPOSAL's target unless round 1 is dropped.

## Gates and cross-checks

- **Agent 12** ([out-W4c-20261123-0239.txt](../../../agent12/w6-gates/night/out-W4c-20261123-0239.txt)): all applicable gates PASS (G4-G7 n/a).
  - G8 PASS: logdiff vs d0 ×7, 0 FAIL, 0 NEW.
  - G12 PASS: STRICT at 02:39:45; non-game load 3.26-3.61 (median 3.34); 0 runs flagged.
- **Cross-check** ([xcheck.md](xcheck/xcheck.md)), by an independent read-only script:
  - every results.csv item agrees with frames.json/run.json;
  - the windows reproduce;
  - the paired median is reproduced: +0.061 ms [−0.026, +0.149].

## Files

- My read-outs: [mine/W4c.md](mine/W4c.md), [mine/W4c-noFlag.md](mine/W4c-noFlag.md), [mine/W4c-noR1.md](mine/W4c-noR1.md), [mine/W4c-noEpisode.md](mine/W4c-noEpisode.md), [mine/W4c-noR1-noEp.md](mine/W4c-noR1-noEp.md) (each with a `.json`).
- Agent 7's method (`build/agent7/w4b-noise/readout.py`): [a7/W4c.md](a7/W4c.md), [a7/W4c-noFlag.md](a7/W4c-noFlag.md), [a7/W4c-noR1.md](a7/W4c-noR1.md), [a7/W4c-noEp.md](a7/W4c-noEp.md).
- Audit: [audit/audit.md](audit/audit.md), covering slow state, sys.csv disturbance, game.log, dumps and timerq3.
- Cross-check: [xcheck/xcheck.md](xcheck/xcheck.md).
- Scripts: `scripts/pool_readout.py`, `scripts/run-mine.ps1`, `scripts/run-a7.ps1`, `scripts/run-var2.ps1`.

# CF1 / CF2 read-out plan (M8, session 3; fixed before any window)

Written at 07:58 on 2026-11-25. Basis:
- M10 rating `build/agent10/session3/confirm-rating.md` 31AD69BA (SAFE-IF K1-K5, S1, S2, N1-N3).
- The Overseer's 13:56Z plan.

Nothing in this file changes after a window starts. Any deviation goes into the read-out as a deviation, with the reason.

## 0. Windows and GO lines

| window | GO (after K2 promotion) | runs | runner est. | TEST stage report |
|---|---|---|---|---|
| CF1 | `GO CF1 matrix-windowCF1.json D36A40CA5277CC7C3E127E10D5367DD892E43160D7AA834D04E2A936EE63D44F only=ship,s0,win3 repeats=6` | 1 cold (ship) + 18 | ~44 min | stage/stage-CF1-075647.txt (K3: result OK, cold run on ship, 33/33 folders) |
| CF2 | `GO CF2 matrix-windowCF2.json DF8A2D3B7D0ACA1428F3B41AC2F5E587741BA8D1C5D390CD68C3646900AE0F60 only=nf,mc repeats=6` | 1 cold (nf) + 12 | ~30 min | stage/stage-CF2-075130.txt (result OK, cold run on nf) |

- **Not used:** the 4-arm CF1 (M10) and CF2's n0 arm (N3).
- **K3 (day launcher):** the ~44 min estimate plus 10 min of slack must fit before run-day's `-StopAt`. The "latest start 06:45" line in the stage reports is the night rule and does not apply here (N2).

## 1. Preconditions, recorded in the read-out (K1, K2, K5)

- **K1:**
  - CF1 runs only after final_gate (9DCC72EE) F1, F2 and F4 have PASSed on devfinal-bin, or the Overseer has ruled a HOLD on them.
  - CF2 runs only after F5, F5w and F7 have done the same on nativefinal-bin.
  - No functional row may be running on the same bin.
- **K2:** the Overseer byte-copies the matrix to `bench/agent8/run/` (hash = GO sha256), then runs `stage-confirm.ps1 -Recheck` until it reports result OK. Only then does the GO go out.
- **K5:**
  - Timing comes only from the user's unlocked, idle desktop through run-day.
  - No M3 queue row, build or other launcher may run during the window.
  - The read-out quotes:
    - the runner preflight lines (desktop, `builds none`, power);
    - the M3 queue log lines covering the window;
    - the WINDOW-HOLD state.
  - Any run on a non-interactive desktop is FUNCTIONAL ONLY and is not scored.

## 2. Which runs count (K4)

- **Scored rounds:** rounds 2-6, every arm.
  - The cold run is never scored.
  - Round 1 appears only as a side note ("with round 1"). That number is biased against the new bins' cold caches and never decides a verdict.
  - If gpu.csv shows that round 2 is not yet on the steady clock plateau (~1500 MHz in the WC windows), the read-out says so and also gives rounds 3-6. The headline still uses rounds 2-6.
- **A run counts only if all of these hold:**
  - **Exit and functional check are clean:** exit 0, no dump or WER, level reached, K0/F0, and STUCK-LOCK judged by the finding-10 rule, counted per arm.
  - **Its sys.csv has 31 columns.** Never pool it with 24-column rows from before 07:30 2026-11-25.
  - **The runner did not flag it out of summary.md:**
    - window_before_floor (< 59.5 s);
    - input during the window;
    - foreground lost;
    - battery or battery saver;
    - power-plan change;
    - non-default desktop;
    - screensaver.
  - **Its proof passes** (`build/agent2/final/check-defaults.py` D9936C56 on game.log, plus run.json `env_set` and the bin's MANIFEST sha):

    | arm | bin (MANIFEST) | check-defaults mode | env_set must |
    |---|---|---|---|
    | ship | devfinal F9C2BE72 | `xenos` (every key `(default)`, full back-off ON 500/30 line once) | have no LEGO_GPU_WAIT_* key |
    | s0 | devoff4b DE11A914 | none of these lines: `Final defaults`, back-off, C1, precise-wait, 1 ms (and no bad strings) | have no LEGO_GPU_WAIT_* key |
    | win3 | devoff4b DE11A914 | `legacy` | hold LEGO_GPU_WAIT_BACKOFF_US=500 and LEGO_GPU_WAIT_SPIN_US=30 |
    | nf | nativefinal D7C7B706 | `native-old` | hold LEGO_NATIVE_FRAME_METRICS; not hold LEGO_NATIVE_SHADER_MISS_CACHE |
    | mc | native4b B63769FE | bad strings only (the old exe logs no miss-cache line) | hold LEGO_NATIVE_SHADER_MISS_CACHE=1 and FRAME_METRICS |

- **Void rules:**
  - A failed proof voids that run.
  - A second failed proof in the same arm voids the arm. The window then gives no verdict for any pair involving that arm and must be rerun.
  - A functional FAIL of a devfinal or nativefinal run voids the arm.
- **nf exception (final_gate S1):**
  - If a run's only native-old FAIL is the absent `Native GPU: shader miss cache ON (build default)` line, and game.log has 0 shader-miss warnings, the run is listed but not voided.
  - If it has more than 0 misses, the run is voided.
  - Every W8a run logged 26 misses, so the line is expected in every nf run.
- **Minimum:**
  - An arm needs at least 4 valid scored runs (of 5) to give a verdict. Below that, the pair reads "no verdict (n < 4)".
- **Host-load gate (M12):**
  - Runs whose non-game load is above the window median + 1 core are flagged.
  - Every verdict is given with and without them. The headline is the "with" set unless a flagged run changes the verdict, in which case both are reported and the Overseer decides.

## 3. Metrics and statistics (same definitions and code path as READOUT-NIGHT.md, M10-confirmed 25BF9B1C)

- **Per-run values:**
  - From frames.json of the 50 s window: median frame ms, fps mean, p99 ms and the 1 % low.
  - Process cores from the runner's CPU columns.
  - Per-run GPU and CPU clock medians from gpu.csv and sys.csv.
  - CF2 also reports render-thread ms/f from threads.csv.
- **Arm values:** the arm's median of per-run values. The tables label the mean column explicitly if one is shown (N1 of READOUT-NIGHT).
- **Contrast:**
  - (median arm X - median ref) / median ref, in %.
  - 95 % CI by bootstrap: resample runs within each arm with replacement, 10 000 draws, percentiles 2.5 / 97.5, fixed seed (recorded).
  - Cross-check: paired rounds (same round, X vs ref), giving the count of rounds that go the same way.
- **Verdict metrics:** fps mean, p99, the 1 % low and process cores. Median ms is reported but never decides: C1's short-frame mode makes the median move against throughput (READOUT-NIGHT S1).
- **Order (N1):** the read-out lists each run's position within its round.
  - CF1, rounds 2-6: ship is first in 1 round, second in 2 and third in 2. s0 and win3 are similar, by rotation.
  - CF2, rounds 2-6: mc is first 3 times, nf 2 times.
  - It also reports a first-vs-later position split per arm as a check.

## 4. Pre-stated margins and claims (S1)

**Difference claims** (ship vs s0, and any pair not listed under equivalence below):
- "X faster / slower / fewer cores" only if the whole 95 % CI excludes 0.
- Otherwise the result reads "overlap (not shown different)".

**Equivalence claims:** "equal" only if the whole 95 % CI lies inside the margin below.
- A CI that crosses a margin reads "not shown different" (if it includes 0) or "different" (if it excludes 0). It is never "equal".
- Margins are relative to the reference arm's median:

| pair | fps mean | p99 | 1 % low | process cores | median ms (info only) |
|---|---|---|---|---|---|
| CF1 ship vs win3 | ±2 % | ±5 % | ±5 % | ±5 % | ±3 % |
| CF2 nf vs mc | ±3 % | ±5 % | ±5 % | ±5 % | ±3 % |

- **Why these margins:**
  - The WC pooled CI half-widths with 9 runs per arm were about ±1.2 % (fps), ±1.5 % (p99) and ±2.5 % (cores).
  - With 5 runs per arm, expect roughly 1.5× wider. So ±2 % on CF1 fps is tight but reachable, and the tail metrics get ±5 %.
  - Native runs vary more (W8a), so CF2 fps gets ±3 % (M10 S1's "about ±3 %").
  - The margins are far smaller than the effects being confirmed: win3 vs s0 is +7.7 % fps and -38.7 % cores; mc vs n0 is about +44 % fps.
- **CF1 ship vs s0:** a difference claim on each verdict metric.
- **CF1 overall:** "the shipped defaults reproduce win3" needs **both** of these:
  - ship vs win3 is "equal" or "not shown different" on all four verdict metrics;
  - ship vs s0 has a CI excluding 0 in the same direction as WC on fps mean and cores.
  - If ship vs win3 is "different" on any metric, that is reported as a finding for the Overseer and M2, and the arm's proof lines are re-examined first.
- **CF2 overall:** "the shipped native default reproduces mc" needs nf vs mc to be "equal" or "not shown different" on all four verdict metrics. "Equal" is the strong form and is claimed only per S1.

## 5. Comparison with WC (S2)

- ship vs s0 is set beside WC's pooled win3 vs s0 (rounds 2-4 of WC1-WC3, READOUT-NIGHT): fps mean +7.7 % [+6.3, +8.7], p99 -14.8 %, 1 % low -17.0 %, cores -38.7 % [-40.3, -35.2]. CF1's in-window win3 vs s0 is shown the same way.
- This is a direction-and-size check only:
  - "consistent" = same sign, with CF1's CI overlapping WC's CI;
  - otherwise "differs from WC". That is a note for the Overseer, not a verdict.
- Different windows are never pooled.
- CF2 nf vs mc has no WC counterpart. W8a's mc vs n0 (median about -29 %, fps about +44 %) is quoted only as context.

## 6. Read-out deliverable

- File: `build/agent8/session3/READOUT-CF.md`. It contains:
  - the section 1 preconditions;
  - a run table (tag, round, position, proof result, flags, clocks, the four metrics);
  - a void and exclusion list with reasons;
  - the contrast tables, with and without round 1 and the M12 flags;
  - the section 4 claims and the section 5 note;
  - its own sha8.
- Script: a copy of the READOUT-NIGHT analysis under `build/agent8/session3/confirm/`, with seeds and inputs listed.
- M10 cross-checks the result before the Overseer uses it.

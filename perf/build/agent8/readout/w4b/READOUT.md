# W4b read-out: build/agent8/matrix/20261122-1541 (Agent 8, run-2 task #7)

W4b = Window 4b. It ran 15:41-16:17 on the user's desktop (WinSta0\Default, AC, no screensaver) with **the other agents
working**: 17/17 runs OK, 1 shared cold run (d0, unscored) and 4 Latin-square rounds of the 4 arms.

| arm | bin | cvars and env | TimerQueue wait |
|---|---|---|---|
| d0 (ref) | devoff2 = S2 sources + S1 codegen (window 3's d0) | none | spin |
| B | devoffB = S2 sources + codegen B | none | spin |
| d3 | devoff3 = S3 sources | none | spin |
| d11t | devoff2 | window 3's d11 bundle (Agent 11's ON bundle R3) + REX_TIMER_WAIT_BLOCKING=1 | blocking |

## What ran and how it was tested

- **Strict pass**, 19:33: `powershell -NoProfile -ExecutionPolicy Bypass -File build\agent8\scratch\w4b-readout.ps1 -Stamp 20261122-1541 -OutDir build\agent8\readout\w4b`.
  - It follows my procedure in [agent8-window3.md](../../../../perf-notes/agent8-window3.md) (L733-877). Every step exits 0.
  - Outputs: [rules.md](rules.md), [w4b.md](w4b.md) and w4b.json (Agent 7's add-on), recheck.txt and recheck-dropslow.txt, [timerq.txt](timerq.txt), [phase.txt](phase.txt) and phase.json.
  - As designed, the recheck step's `--write` added recheck.md to the W4b matrix folder. That is the only write into it.
- **With-run-6 pass**, 19:37-19:38: the W5 tool with `-All` (`w5-readout.ps1 -Stamp 20261122-1541 -ExpectRows 17 -All -OutDir build\agent8\readout\w4b\all`). Every step exits 0, and [all/rules-nodrop.md](all/rules-nodrop.md) holds all 16 scored runs.
- **Without-run-6 pass**: the 19:33 dry run of the W5 tool on W4b (`build/agent8/readout/w5-dry-1541/rules-nodrop.md`) has the 15 valid-timing runs with the drops ignored.
- **Variants**, 19:54: [variants.md](variants.md), from `build/agent8/scratch/readout_variants.py`. It has all runs, without run 6, without the flagged runs, and slow-state bins only.
- **Subagents** (read-only, no game runs):
  - a log and bin scanner ([scan/scan.md](scan/scan.md)): proof lines, game.log health, the slow-state scan, 10 s bins with E/P clocks, and correlations;
  - a sys.csv auditor ([sysaudit/report.md](sysaudit/report.md), [sysaudit/extra.md](sysaudit/extra.md), and the later [sysaudit/audit.md](sysaudit/audit.md)): non-game CPU per window on two measures, the flagged runs against the rest, the named activity against the 1 s samples, the warm-ups, and W4b against W5;
  - an independent cross-checker ([xcheck/xcheck_core.md](xcheck/xcheck_core.md), [xcheck/xcheck.md](xcheck/xcheck.md)): its own code recomputes everything from perf.csv, proc.csv and threads.csv and compares every published number. At 20:45 it also recomputed Agent 7's T-std and B-block T-std ([../tstd-xcheck/tstd.md](../tstd-xcheck/tstd.md)).
- **Agent 6's logdiff**: `build/agent6/w4b/out-20261122-1541/summary.txt`.
- **Agent 7's noise method**, 20:27: my rerun of his `noise_methods.py` and `noise_case.py`, read-only on the matrix, into [noise/](noise/) (report.md, report.json, noise-case-w4b.md, stdout.txt). It exits 0, and the files are identical to his apart from the command line.
- **Agent 11's independent check** of its 3-mode slow-state script (`build/agent11/s4a/slowstate3-check/REPORT.md`): PASS.
  - The copy reproduces the original's 17 W4b runs (onset, slow %, span, fg) with 0 flags.
  - None of its 7 edge cases occurs in W4b.
- **Tool hash.** Agent 7's add-on `bench/agent7/w4b_readout/w4b_readout.py` is sha256 `EF1ABEC8…6175C7C4` (13:31:11, 54,424 B), not the `7C7A0673…` that my notes call frozen. Agent 7 added the 10 s bins and says nothing else changed.
  - The cross-checker's own code reproduces every per-run number the add-on reports, with 0 differences above tolerance (17 runs). So the hash change does not affect any number here.

## Verdicts per arm vs d0

**Strict pass ([rules.md](rules.md)): overall FAIL, no verdict for any arm.**

- R0 drops run 6 (`1551-B-r2`, valid_timing = False: 3 clang++ processes in its warm-up and window).
- R3 drops all 16 scored runs: the slow state is in every window, with fg = 1 (see "Slow state" below).
- R6: background median 8.14 cores (max 8.67), with 5 SAT runs (1542, 1547, 1549, 1600, 1611; 1551 too).
- R1, R2, R4 (draws/frame p50 226 in every run) and R7 pass.
- R5: no verdict, because d0 has no runs left.

**Variants with the R3/R4/R6 drops ignored ([variants.md](variants.md)).** The decision rule is R5's: better or worse only
when every run of the arm lies outside d0's min..max, and no verdict when n < 3.

| variant | n (d0/B/d3/d11t) | B vs d0: fps / p50 | d3 vs d0: fps / p50 | d11t vs d0: fps / p50 |
|---|---|---|---|---|
| all scored runs (with run 6) | 4/4/4/4 | +6.4 % / -4.9 %, overlap | +3.8 % / -5.4 %, overlap | -0.8 % / -1.1 %, overlap |
| without run 6 | 4/3/4/4 | +15.1 % / -10.8 %, overlap | as above | as above |
| without the flagged runs (seq 3, 4-7, 10) | 4/2/1/3 | no verdict (n = 2) | no verdict (n = 1) | +6.3 % / -7.1 %, overlap |

| arm | fps median (min..max), all runs | without run 6 | without flagged | paired fps by round, all runs (up / rounds) | game cores vs d0 |
|---|---|---|---|---|---|
| d0 | 239.7 (213.9..270.4) | same | same | ref | 3.44 (3.34..3.53) |
| B | 255.1 (230.8..317.1) | 275.8 (230.8..317.1) | 253.3 (230.8..275.8) | +13.6 % (3 / 4); without run 6 +23.7 % (3 / 3) | -1.5 %, overlap |
| d3 | 248.9 (198.4..298.6) | same | 266.8 (n = 1) | +0.3 % (2 / 4) | -0.9 %, overlap |
| d11t | 237.7 (206.4..277.2) | same | 254.9 (220.6..277.2) | +0.4 % (2 / 4): r1 -19.5, r2 -18.4, r3 +24.3, r4 +19.2 % | **-15.3 %, better** (2.81..3.00) |

- **No frame-time verdict in any variant.** Every fps, p50, p99 and 1% low row reads overlap, or no verdict at n < 3.
- **d11t: same frame time with about 0.5 core less game CPU.** Every d11t run is below d0's lowest (2.81-3.00 against 3.34-3.53 cores) in every variant.
- **B:** paired by round it leads by +13.6 % (+23.7 % without run 6), but its best run (317.1 fps, round 1) is a flagged run. Without the flagged runs only 2 B runs are left. So this is a lead, not a verdict.
- NOTEs: B's round-1 run (317.1) and d11t's round-1 run (206.4) lie outside their arms' rounds 2+.

**Slow-state bins only (descriptive, chosen after the fact).** The per-run median fps over the 10 s bins with
E<800 MHz in >= 90 % of their sys.csv rows:

| arm | fps median (min..max) | vs d0 | paired by round (up / rounds) |
|---|---|---|---|
| d0 | 218.5 (170.8..252.2) | ref | - |
| B | 222.0 (206.7..264.5) | +1.6 %, overlap | +12.0 % (3 / 4) |
| d3 | 220.1 (181.5..254.9) | +0.7 %, overlap | +1.3 % (2 / 4) |
| d11t | 243.6 (193.4..277.6) | +11.5 %, overlap | +16.4 % (3 / 4) |

- d11t has no fast-state bin at all, while d0, B and d3 have 1-3 fast bins each in rounds 1-2 (302-380 fps). In a like-for-like slow-state comparison d11t is not slower than d0.
- That fits the mechanism: in W4b's slow state the P-cores run at ~100 % utility, and d11t frees about 0.5 core. But it is a post-hoc cut at n = 4, so it is only a lead for W6 or later.

### Agent 7's final noise method: B-block T-std (W4b has a round effect)

Agent 7's T-std method (`build/agent7/w4b-noise/RESULTS.md`):
- Split each run's frames at the runner's 4.5 ms light threshold.
- Re-mix light and heavy frames at one heavy-time share, hT_ref = 0.531 (the median of the 15 kept runs: the cold run and run 6 are out).
- Compute fps, p50, p99 and 1 % low over the reweighted frames.

W4b has a round effect: rounds 2-4 have median ms 3.1-4.0 % below round 1 (r2 / r3 / r4: −4.0 / −3.1 / −3.9 %; RESULTS.md's "3.1-4.1" is the same terms in log points). So Agent 7's rule makes **B-block T-std** primary here: arm + round, df = runs − arms − rounds + 1 = 8.

The numbers come from my rerun of his scripts ([noise/report.md](noise/report.md), noise_methods.py sha256 `A29AF479…F320B4AF`). They are identical to Agent 7's report.md apart from the command line. Cells give the GM delta vs d0 [95 % CI]; `*` = the CI excludes 0.

| method | metric | B (n = 3) | d3 (n = 4) | d11t (n = 4) |
|---|---|---|---|---|
| **B-block T-std** | median ms | −2.5 [−5.0, +0.0] | −1.5 [−3.7, +0.8] | −0.5 [−2.8, +1.8] |
| **B-block T-std** | fps | **+6.0 [+0.5, +11.8] \*** | +2.3 [−2.5, +7.4] | +2.5 [−2.3, +7.6] |
| T-std (one-way, df 11) | median ms | −2.1 [−5.8, +1.8] | −1.5 [−4.9, +2.1] | −0.5 [−4.0, +3.1] |
| T-std (one-way, df 11) | fps | +5.2 [−1.8, +12.8] | +2.3 [−4.0, +9.1] | +2.5 [−3.9, +9.3] |
| raw (guard b) | median ms | −8.3 [−25.3, +12.6] | −0.9 [−18.1, +19.8] | −0.1 [−17.4, +20.8] |
| raw (guard b) | fps | +13.5 [−11.3, +45.2] | +2.5 [−18.4, +28.8] | −0.7 [−21.0, +24.7] |

- **d0's band** ((max − min) / median, median ms): raw 19.6 %, T-std 7.8 %, B-block T-std 3.6 %.
- **Pooled CV:** 12.2 → 2.3 → 1.4 %.
- **Guards:**
  - (a) **Light share per arm:** one-way F = 0.40 on (3, 11). No arm moves the mix.
  - (b) **Raw GM deltas:** every T-std delta lies inside its raw CI, so there is no contradiction.
  - (c) **Host flag** (P util ≥ 90 % and E < 600 MHz): 7 of 15 runs, namely d11t-r1, d11t-r2, d3-r3, d0-r3, B-r3, d11t-r4 and d0-r4.
    - Their mean median-ms excess is +13.1 % raw, −0.6 % T-std and −0.1 % B-block T-std.
    - One flagged run is fast (d11t-r4), so the flag is a warning, not a correction.
- **Reading:**
  - d3 and d11t match d0 within about ±3-4 % on frame time. d11t does so with 15 % less game CPU.
  - B (codegen B) may be a few % faster: fps +5-6 %, median ms −2 to −2.5 %.
    - Only the B-block fps CI excludes 0, and B has n = 3 (run 6 is out).
    - It is one of many tests.
    - The independent recompute ([tstd.md](../tstd-xcheck/tstd.md)) reproduces +5.98 % [+0.49, +11.77], but the star is fragile. Leaving out one B or d0 run at a time keeps the CI above 0 in only 3 of 7 cases; without any round-1 or round-4 run it includes 0: without 1542-d0-r1 +3.70 [−0.97, +8.59], 1545-B-r1 +3.50 [−1.98, +9.29], 1611-d0-r4 +6.11 [−0.52, +13.19], 1613-B-r4 +6.73 [−0.19, +14.12].
    - Paired by round, B's T-std fps is +14.7 % (r1), +1.3 % (r3) and +4.6 % (r4): up in 3 of 3, most of it in round 1. B-block median ms is −2.51 [−4.96, +0.004], with the upper bound at 0.
    - So it is a **hint for codegen B**, consistent with the paired raw lead (+13.6 %, 3/4), not a verdict.
- These figures ignore the R3/R4/R6 drops, like the variants above. The strict pass still has no verdict.

## Disturbance audit (sys.csv)

Source: the auditor's [sysaudit/report.md](sysaudit/report.md) and [sysaudit/extra.md](sysaudit/extra.md), from its own
read-only script (sysaudit.py). It measures non-game CPU in each 1 s sample in two ways, in cores out of 12 logical processors:

- **ng_t, time-based:** the busy time of all cores minus the game's CPU. This is the add-on's background formula; the auditor's copy of it differs by at most 0.01 core.
- **ng_u, utility-based:** % Processor Utility (work done at the actual clock) minus the game.

An E-core that is busy at ~550 MHz counts in full in ng_t, but in ng_u only in proportion to its clock. In the slow state the
E-cores are 99-100 % busy at ~550 MHz, so ng_t reads ~8.1 cores while ng_u reads ~3.2.

Agent 1's notes (SESSION2 16:35) name the agent activity during W4b's windows. These are the flagged runs:

- run 3 (`1545-B-r1`): Agent 2's prep-b4.py dry run, 15:46:11-22 (one thread, hashing);
- run 4 (`1547-d3-r1`) warm-up: Agent 2's shell checks, 15:47:17-19 and 15:47:40-44;
- runs 4-7: Agent 11's short Python reads and one S4-DRAFT write, 15:48-15:55;
- run 6 (`1551-B-r2`): 3 clang++ processes (most likely Agent 9's #22 syntax checks, ~15:51-15:53);
- run 10 (`1600-d3-r3`, the slowest run): Agent 11's listings and Get-Process, 16:01:54-16:02:36.

**Non-game CPU per window, flagged (n = 6) vs the rest (n = 10).** Medians over runs of the per-run window medians, [min..max]:

| measure | flagged | rest | flagged runs outside the rest's range |
|---|---|---|---|
| ng_t, time-based (cores) | 8.16 [6.76..8.59] | 8.10 [7.49..8.67] | 1545-B-r1, below |
| ng_u, utility-based (cores) | 3.35 [3.19..5.20] | 3.23 [3.08..8.09] | none |
| ng_t, slow-state samples only | 8.15 [8.00..8.60] | 8.10 [7.51..8.68] | none |
| ng_u, slow-state samples only | 3.17 [2.97..3.61] | 3.19 [3.09..3.74] | none |
| game cores | 3.30 [3.00..3.52] | 3.36 [2.81..3.53] | none |
| E clock (MHz) | 799 [551..1175] | 599 [545..1152] | 1545-B-r1, above |

- **The flagged runs are not more loaded.** No flagged run is above the most loaded unflagged run on either measure, in the whole window or in the slow-state samples only. The same holds for the per-run p90s.
- **The flagged group's higher ng_u means (4.26 vs 3.43) come from the state mix, not from the agents.**
  - 5 of the 6 flagged runs are in rounds 1-2, where the E-cores spent part of the window above 800 MHz. ng_u reads 6.15 in E>=800 samples and 3.26 in E<800 samples (pooled medians).
  - 136 of the 143 window samples above the rest's ng_u p90 are E>=800 samples. The unflagged 1542-d0-r1 has the most of them (32 of 50).
- **The named activity against the 1 s samples** (a sample's wall time is the end of its 1 s interval):
  - prep-b4.py covers 8 samples of 1545's warm-up and the window's first 4 (15:46:19-22). Those 4 read ng_t 7.56 (mean), against 6.76 for the run's window. 1545 is still the fastest run (317.1 fps); it entered the slow state ~30 s into its window.
  - Shell check a (15:47:17-19) falls between runs. Check b is in 1547's warm-up (5 samples).
  - Agent 11's reads (15:48-15:55) span runs 4-7. Their window medians, ng_t 7.66-8.59 and ng_u 3.19-3.63, lie inside the rest's range.
  - Run 6's clang++ (3 in the window and 1 in the warm-up, per run.json) gives a window ng_t median of 8.19, with 1 of 50 samples above the rest's ng_t p90. R0 drops run 6 anyway (valid_timing = False).
  - Agent 11's listings in 1600's window (16:01:54-16:02:20, 27 samples): ng_t 8.17 (mean) against the run's 8.20 median, ng_u 3.27 against 3.27, and 0 samples above either p90. **Not visible.**
  - 1600 is the slowest run because it spent its whole window deep in the slow state: E 544-557 MHz and P util 102-105 %. Its slow-state P util (103.2 %) is the highest of all 16 runs. Most round 3-4 runs were in the same state.
- **What tracks fps is the host state, not the agents.** Spearman over the 16 scored runs (permutation p):
  - fps vs E busy -0.91 (p < 0.001), vs P busy -0.77 (0.001), vs E MHz +0.75 (0.001);
  - fps vs ng_t -0.73 (0.003), because ng_t rises with the E-cores' busy time in the slow state;
  - fps vs ng_u +0.08 (0.78): no relation.
  - Without run 6 (n = 15) the numbers barely move: E busy -0.90, ng_t -0.75, ng_u +0.06.
- **Data and context checks:**
  - sys.csv spacing in every warm-up and window: median 1.000 s, max 1.067 s, no gap over 1.5 s.
  - All 17 runs had the best_efficiency power overlay, AC power, the default desktop, no screensaver, and the game in the foreground for 100 % of the window.
  - The only build processes in any window are run 6's clang++.
  - The time-based busy model holds: the E-cores' busy share never exceeds 1.003.
- **Limit.** In the slow state the E-cores are already 99-100 % busy, so extra work on them cannot raise either measure; it would show only as contention. The audit rules out sustained extra load on the P-cores, which are not pinned. It cannot rule out short single-thread work on the E-cores.

**The auditor's later pass ([sysaudit/audit.md](sysaudit/audit.md), §7-8) adds three points:**

- **Run 10's warm-up is the only candidate disturbance.**
  - Run 10 is `1600-d3-r3`, the slowest run (198 fps). Its warm-up (16:00:31-16:01:20) carried more non-game work than any other warm-up: ng_u 8.36, against 5.62-7.59 for runs 2-9.
  - Its other warm-up figures: ng_t 8.64, P util 110.6, P sat 49 %, E busy 99.2 %.
  - Its 10 s bins read P util 103-117 and E busy 97-100 % at 1375-1630 MHz.
  - No agent activity is logged at that time.
  - Then E fell to 835 MHz (the 16:01:21 bin), and to ~550 MHz for the whole window and the rest of the matrix: runs 10-17 have 90-100 % slow windows.
  - In its window, run 10 has the highest slow-state P util (103.2, against a maximum of 102.1 for the rest). Otherwise the window looks like those of runs 12, 13 and 15.
  - The auditor's call: possibly disturbed before the window, by an unattributed load. Run 10 is in the flagged set, so the without-flagged variant already leaves it out.
- **W4b against W5 at comparable clocks.** Work-based non-game CPU in fast-state warm-ups:

  | warm-ups | W4b | W5 |
  |---|---|---|
  | fast-state | 5.62-7.59 (runs 2-9) | 4.88 (1757-base-r1) |
  | cold run | 8.27 | 6.38 |

  So W4b carried about 1-3 nominal cores more non-game work, while the other agents were working. Both windows come after the 08:29 Windows Update.
- **Caveat on ng_u.**
  - In the slow state, ng_u is pinned at about 3.2-3.4 whatever the background demand. E work is capped at 8 × 0.333, so ng_u ≈ 2.67 + 4 × P util / 100 − game.
  - Extra load then shows up as less CPU for the game (higher P busy, lower fps), not as a higher ng_u.
  - So in the slow state neither measure can show extra load directly. That is why the auditor's one candidate comes from a warm-up at high clock.

**Verdict impact: none.** The flagged runs are no more disturbed than the rest. Without them every frame-time row still
reads overlap or no verdict, and d11t's game CPU is still better.

## Proof (R7) and the 1 ms line

| arm | 1 ms lines per run | REX_TIMER_WAIT_BLOCKING in env_set | TimerQueue % of a core, median (min..max) | busiest 1 s |
|---|---|---|---|---|
| d0 | 0/0/0/0 | absent | 57.1 (47.2..62.6) | 82.3 |
| B | 0/0/0/0 | absent | 55.1 (41.4..61.5) | 78.3 |
| d3 | 0/0/0/0 | absent | 55.9 (46.8..61.3) | 78.6 |
| d11t | 1/1/1/1 | 1/1/1/1 | 5.3 (5.0..6.0) | 17.8 |

- **Every d11t game.log has `Host timer resolution set to 1 ms (background opt-out on)` exactly once**: 1549, 1556, 1602 and 1608. No other log has it. Three independent sources agree: my R7, the scanner, and Agent 6's logdiff.
- The scanner also checks every run's config: params.cvar, args and bin_dir equal the arm's, env_set only where the arm has it. 0 deviations in 17 runs.

## game.log health

- Scanner: 17 of 17 logs have 0 [error], 0 [critical], 0 FATAL, 0 STUCK-LOCK and a normal shutdown. Every log has the same 40 warnings in 5 types (krnl stubs, INSTALL0_2.HDR, 34 INSTALL*.DAT fails = the normal phase). No arm has a warning type the others lack.
- Agent 6's logdiff (52 gate pairs, 0 FAIL findings, plus an exact-text diff):
  - All 17 runs exit 0x0 after a single WM_CLOSE (0.74-1.13 s), with no WER, dump or STUCK.
  - B is identical to d0, even in exact text.
  - d3 has one benign handle-slot race at boot in 1600-d3-r3 (IoDismountVolumeByFileHandle 0xf8000164 instead of 0xf8000160).
  - d11t's only extra line is the 1 ms line.
  - The Toypad 8-vs-10 line counts come from harness timing, not from an arm.

## Slow state: in the foreground, and it costs fps in W4b

Source: [scan/scan.md](scan/scan.md) section 3; it agrees with my timerq.txt and R3 on every run.

- **All 16 scored runs** have E-cores under 800 MHz for 3+ sys.csv samples inside the window, with fg = 1 for 100 % of every window (no fg != 1 row between the first frame and the measure end). The cold run never enters it.
- **Onset depends on the time of day, not on the arm.** Run-time onsets are 54-94 s in rounds 1-2 (except 1551-B-r2 at 1 s) and 1-4 s in rounds 3-4. Window E<800 shares are 32-96 % in rounds 1-2 and 90-100 % in rounds 3-4.
- **In W4b the slow state marks lower fps.**
  - When the E-cores drop to ~550 MHz inside a window, that run's 10 s bins drop by 30-45 %: 1542-d0-r1 from 302 to 171-179 fps, 1545-B-r1 from 379 to 220-245, 1547-d3-r1 from 333 to 167-205, 1553-d3-r2 from 359-400 to 204-252, 1558-d0-r2 from 373 to 204-271.
  - Runs that are slow from the start run flat, at 214-277 fps.
  - Across the 16 runs (Spearman, permutation p): fps vs window E MHz rho +0.73 (p 0.002); vs E<800 share -0.62 (p 0.013); vs P util -0.76 (p 0.001). Against run order it is -0.07 (p 0.79), and against onset +0.16 (p 0.56).
- **It hits the arms unevenly in rounds 1-2.** Round 1's window E<800 shares are d0 35, B 32, d3 70 and d11t 96 %; round 2's are B 64, d3 54, d11t 96 and d0 76 %.
  - d11t's round-1 and round-2 deficits (-19.5 and -18.4 %) coincide with this. In rounds 3-4, where every run is 90-100 % slow, d11t is +24.3 and +19.2 % vs d0.
- R3 was written for a power effect that only showed up in never-foreground runs, so here it drops every run. In this window the slow state is a host state that also hits the foreground.

## 10 s bins

Source: [scan/scan.md](scan/scan.md) section 4. The scanner's bin fps equals w4b.json's stat_bins (83 bins, max |diff| 0.000).

- draws/frame p50 is 226 in every bin of every run: same scene throughout.
- 12 of 80 scored bins are slow (< 0.85 x the run's median bin), in 9 runs. 11 of the 12 have E mean < 800 MHz and P util >= 90 %.
  - The other 68 bins are mostly in the same state too (E < 800 in 54, P util >= 90 in 58). Low E clocks alone do not make a bin slow; the onset inside a run does.
- Pooled bins (n = 80, not independent): Spearman of bin fps / run median vs E MHz +0.41, vs E<800 share -0.43, vs P util -0.47.
- Unlike W5, the first bin is not regularly slower than the second: 0-10 s is slower than 10-20 s in 8 of 16 runs.
- My phase.json lists no slow bins in any run, because its criterion is stricter than the scanner's 0.85 x median rule.

## Cross-check of the recomputed medians

[xcheck/xcheck_core.md](xcheck/xcheck_core.md), from the cross-checker's own stdlib code (no runner or add-on code):

- Per run, 29 fields against frames.json, results.csv and run.json: 0 differences above tolerance in 17 runs.
- Per run against the add-on JSON (frames, window s, fps, p50, p99, 1% low, >33, game cores): 0 differences above tolerance.
- The arm tables with run 6 and without it match mine and SESSION2 16:35 exactly. Examples: d0 239.7 fps and 3.399 ms; B 255.1 / 3.234 with run 6 and 275.8 / 3.033 without it; d3 248.9 / 3.215; d11t 237.7 / 3.363.
- Its paired deltas match too: B +13.6 % (3/4) and +23.7 % (3/3) without run 6; d3 +0.3 % (2/4); d11t +0.4 % (2/4); d11t game cores -14.9 % paired.
- [xcheck/xcheck.md](xcheck/xcheck.md) (relabelled 20:09) compares 666 published numbers (summary.md, w4b.json, the without-run-6 rules-nodrop.md, recheck.txt, Agent 1's 16:35 notes): **0 MISMATCH**.
  - 16 "definition" items: documented definition differences, such as summary.md's arm CPU column and Agent 1's CPU numbers being means over runs, not medians.
  - 5 "rounding ties" (4 distinct numbers): the runner's own rounded value sits exactly on a rounding boundary. They are 1542-d0-r1 light 0.807 (frames.json 0.8075), 1608-d11t-r4 light 0.702, 1613-B-r4 light 0.742, and the d11t vs d0 game-CPU delta -0.52 (-0.5250).
- [../tstd-xcheck/tstd.md](../tstd-xcheck/tstd.md) (20:45): the cross-checker's independent recompute of Agent 7's T-std and B-block T-std from the run files, with its own numpy code. W4b: 740 of 740 numbers match his report.json, and 90 of 91 cells match RESULTS.md; the other cell is a definition difference (the round terms: 3.1-4.1 in log points, 3.1-4.0 %). **0 MISMATCH.** It also gives the leave-one-out and per-round checks under "Reading" above.

## Files

- [rules.md](rules.md) (strict), [all/rules-nodrop.md](all/rules-nodrop.md) (with run 6), `../w5-dry-1541/rules-nodrop.md` (without run 6), [variants.md](variants.md).
- [w4b.md](w4b.md) and w4b.json (add-on), [timerq.txt](timerq.txt), [phase.txt](phase.txt), recheck.txt.
- [scan/](scan/), [sysaudit/](sysaudit/) (report.md, extra.md, audit.md), [xcheck/](xcheck/).
- [noise/](noise/): Agent 7's noise method, rerun at 20:27 (report.md, report.json, noise-case-w4b.md, stdout.txt).
- [../tstd-xcheck/](../tstd-xcheck/): the independent T-std and B-block recompute for W4b and W5.
- summary.md: a copy of the runner's.

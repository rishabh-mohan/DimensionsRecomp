# CF1 read-out cross-check (ship vs s0 vs win3)

M10, 2026-11-25 ~13:50 local. Cross-check of M8's READOUT-CF1 against READOUT-PLAN 18F69B57, confirm-rating 31AD69BA and my CF2 conditions (cf2-check EFA8501D, C1/C2).

## Files

| file | sha256 (16) | bytes |
|---|---|---|
| build/agent8/session3/confirm/READOUT-CF1.md | C8CFD115DDF88CC7 | 9386 |
| build/agent8/session3/confirm/readout-cf1-tables.md | 42DA8C4529985D14 | 31948 |
| build/agent8/session3/confirm/readout-cf1.json | B2E108139BD58127 | 72921 |
| build/agent8/session3/confirm/readout_cf.py | B76E636C77798F64 | 25792 |
| build/agent8/matrix/20261125-1255/results.csv | BA021F89AE5FF47E | 10462 |
| bench/agent8/run/matrix-windowCF1.json | D36A40CA5277CC7C | 7213 |
| build/agent8/session3/confirm/stage/stage-CF1-125054.txt | 81D38590291AD445 | 11978 |
| build/agent10/session3/scratch-final/cf1chk/boot_check1.py (mine) | 9DDEAEC844EA8DA6 | 3461 |
| build/agent10/session3/scratch-final/cf1chk/boot_check1.out.txt (mine; UTF-8 BOM, CRLF from Out-File) | 496926BEF3D5CEDE | 13474 |

Base: 19 runs (1 cold ship, unscored + 6 rounds x {ship, s0, win3}); headline rounds 2-6, n = 5 per arm. readout_cf.py is the same file (B76E636C) used for CF2.

## Verdict

**CONFIRMED-WITH-CHANGES.** Every number I checked is reproduced exactly, the proof/void/gate logic is the plan's, and "CF1 confirms the night result" stands. One required wording change (W1): the S1 claim must be stated as the weak form, as CF2's was. Two recommended edits (W2, W3). No claim depends on the round-3 busy-host runs.

## What I checked

### (1) CIs: reproduced exactly

My script (boot_check1.py, own implementation of the difference-of-medians percentile bootstrap, 10 000 draws) gives identical bounds with seed 1, seed 7 and the exact enumerated bootstrap distribution (n = 5, odd, so the median is an order statistic):

| pair | fps | p99 | 1 % low | cores |
|---|---|---|---|---|
| win3 vs s0 | +10.0 [+7.5, +11.4] | -16.1 [-19.5, -14.7] | -17.7 [-19.6, -3.8] | -38.5 [-41.6, -29.2] |
| ship vs s0 | +10.2 [+6.8, +11.5] | -15.5 [-17.9, -13.9] | -17.3 [-19.2, -14.6] | -38.8 [-41.1, -27.1] |
| ship vs win3 | +0.1 [-2.2, +2.4] | +0.7 [-2.2, +4.0] | +0.5 [-16.5, +3.8] | -0.6 [-15.6, +18.5] |

- Paired-round t-CIs (log ratio, t 4 df) also match, e.g. ship vs win3 cores +0.3 [-3.9, +4.5]; every win3/ship vs s0 metric goes the same way in 5/5 rounds.
- The "without M12-flagged run" variant matches (ship vs win3 fps [-1.5, +2.6], cores [-16.3, +4.2]; ship vs s0 fps +10.3 [+7.9, +11.6], cores -39.1 [-41.7, -37.4]). r3-6 points match.
- The asymmetric bounds have the same cause as in CF2: with n = 5 one extreme run sets a percentile bound (P(resample median = sample max) ~ 5.8 % > 2.5 %). Here that run is 1309-win3-r3 (1 % low 5.079, cores 1.744) or 1311-ship-r3 (cores 1.798).
- S2 "consistent" checked on all 8 cells: same sign and CI overlap with WC pooled (fps [+6.3, +8.7], p99 [-17.1, -14.0], 1 % low [-18.0, -14.9], cores [-40.3, -35.2]). True for every cell.

### (2) C1 plateau: met

- Same script, same line (readout_cf.py L339): plateau = min(round-2 counted gpu) >= 0.97 x median(rounds 3-6 counted). Identical code and threshold to CF2.
- Round-2 runs 1575 / 1560 / 1552 MHz; rounds 3-6 median 1544.5 (12 runs, 1507-1560); 0.97 x 1544.5 = 1498; min 1552 passes. json plateau = true. Per-round medians are shown in the read-out (r1 1627 ... r6 1537), as C1 asked.
- Round 1 (1627) is above the plateau and is excluded from the headline anyway; the r1-6 side note never decides.

### (3) C2 wording on every tail: met in the read-out

- READOUT-CF1 never calls a tail "equal": L31 and L44 (ship vs win3 p99, code prints "equal"), L56, L58 all say "not shown different"; 1 % low is n.s.d. everywhere. win3/ship vs s0 tails are difference claims (CIs exclude 0).
- readout-cf1-tables.md prints the raw code claim "equal" for ship vs win3 p99 at L64, L92, L120, L148. Deviation 4 covers this. Downstream quotes must come from READOUT-CF1, not the tables file (condition C3).
- Note: for CF1 ship vs win3 p99 the whole CI [-2.2, +4.0] is inside the pre-stated ±5 % margin, so plan section 4 would allow "equal" there. M8's "not shown different" is the conservative reading and is acceptable; my CF2 C2 was about CF2's 25-45 % tail half-widths. Either "not shown different" or "equal within the pre-stated ±5 %" conforms for this one cell; nothing else may be called equal.

### (4) Round-3 busy-host runs: no claim depends on them

- 1311-ship-r3: non-game 4.40 > M12 threshold 4.25 (median 3.25 + 1.0); flagged and kept per plan. 1309-win3-r3: non-game 4.10, below threshold, correctly not flagged (eff 2061 MHz vs win3 median 2260).
- Dropping round 3 entirely (post hoc, information only, my run):
  - win3 vs s0: +9.8 [+8.6, +11.6] / -16.8 [-19.2, -14.4] / -17.8 [-20.0, -15.8] / -39.1 [-42.2, -36.1]
  - ship vs s0: +10.0 [+7.8, +11.6] / -14.9 [-17.0, -13.9] / -16.4 [-19.0, -14.2] / -39.2 [-41.6, -37.5]
  - ship vs win3: fps [-1.6, +0.5], p99 [-0.6, +4.2], 1 % low [-1.1, +4.3], cores [-5.5, +4.6]; all still within the claim.
- So round 3 only widens CIs; every difference claim still excludes 0 without it, and every ship vs win3 cell stays non-different (and tighter). The headline correctly keeps round 3; dropping it after the fact must not become the headline.

### (5) Deviations: acceptable

1. File name READOUT-CF1.md: cosmetic.
2. "Level reached" = reached the 50 s window: same as CF2, right for the light title route.
3. Plateau 0.97 fixed at 11:40: before the CF1 data (window 12:55-13:34). Same code as CF2.
4. Tables print "equal", read-out quotes "not shown different": acceptable with C3.
5. Pair order ship vs win3 (win3 = reference): matches the plan's margin table; sign only.

### (6) "S1 met": fair under the pre-stated rule, but only in the weak form

- Plan section 4 (L115-117): reproduce = ship vs win3 "equal" or "not shown different" on all four, AND ship vs s0 fps CI > 0 and cores CI < 0. Both parts hold (fps [+6.8, +11.5], cores [-41.1, -27.1]). So "met" is correct by the letter, and the code (tables L184) says the same.
- But at the headline, ship vs win3 is equal on none of the four metrics (fps CI [-2.2, +2.4] crosses the ±2 % margin; cores [-15.6, +18.5] is ~7x the ±5 % margin). The cores result is absence of evidence: CF1's headline cannot exclude a ~15 % cores difference between ship and win3. The paired CI (+0.3 [-3.9, +4.5]) and the no-round-3 set ([-5.5, +4.6]) point to near-equality, but they are information, not the pre-stated test.
- The read-out's L18-19 say "not shown different on every verdict metric. So the S1 rule ... is met." That is true, but it lacks the "weak form" qualifier that READOUT-CF2 carried. Hence W1.

### Quotes (K2, K5): verified

- K2: stage-CF1-125054.txt 81D38590, "mode: RECHECK (already in bench\agent8\run; no copy)", "result: OK".
- Runner note runner-CF1-1251.txt: L1 quiet gate STRICT (MsMpEng 0.02/0.01/0.02); L34 interactive desktop; L35 LogonUI not running; L36 AC 100 %; L39 builds none; L40/L41 both bins ok (MANIFEST.txt); L42 screensaver none.
- Launcher log: 12:51:17 GO read and deleted; 12:51:19 HOLD written; 12:51:19 GO ACCEPTED (sha256 ok, 19 runs, ~44 min); 12:55:20 bins unchanged, power scheme Balanced, window CF1 START; 13:34:18 END, runner exit 0 (all runs OK), 39 min; 13:34:18 HOLD removed.
- M3 queue (queue.out.txt): L314 12:43:54 DONE s33ond; L315 12:43:55 idle; L316 12:44:30 "HOLD or PAUSE file: no launch; waiting"; L317 13:42:47 "past the last launch 13:30: queue ends". Nothing launched in 12:55-13:34. Side effect, not a CF1 issue: f10aL, f10bL, s33stop6, s33stop7 were not run before the queue ended.

## Required and recommended changes

- **W1 (required):** L13/L18-19 to read, for example: "ship vs win3: not shown different on all four verdict metrics, equal on none at the headline (weak form, as CF2). With the ship vs s0 directions, the plan's S1 rule 'the shipped defaults reproduce win3' is met in the weak form. The cores CI [-15.6, +18.5] is wide because of round 3; the paired-round cores CI is +0.3 [-3.9, +4.5] (information)."
- **W2 (recommended):** L46 "the lower end of the win3/ship vs s0 cores CIs" should be "the end nearest 0 (-29.2, -27.1)"; and add that the win3 vs s0 1 % low upper bound -3.8 also comes from 1309-win3-r3 (5.079 ms). Without round 3 it is [-20.0, -15.8].
- **W3 (recommended):** add one line to the tables file header saying that raw "equal" on tail rows is quoted as "not shown different" in READOUT-CF1 (or regenerate with the C2 wording).

## Conditions

- C3: downstream quotes of CF1 come from READOUT-CF1 (after W1), never from the raw tables; p99 may be quoted as "not shown different" or "equal within the pre-stated ±5 %" (ship vs win3 only); 1 % low and cores only as "not shown different".
- C4: no post-hoc headline. The no-round-3 and no-M12 variants stay information.

## Findings

- NIT N1: readout-cf1.json has keys that differ only by case ("A"/"a"), so PowerShell ConvertFrom-Json rejects it (Python reads it fine). Cosmetic; worth renaming for tooling.
- NIT N2: M12 median is quoted as 3.25 (15 scored r2-6 runs) in the read-out and 3.255 in the json; threshold 4.25 either way, no effect.
- NIT N3: ProcEvery sample_ms_max still open (sys.json has no key); not used by any verdict.
- Not done on purpose (light IO while the host may be in use): re-hashing exes/DLLs in the 19 run dirs; I rely on the script's --hash-bins proof result, reviewed as code for CF2 (same file).

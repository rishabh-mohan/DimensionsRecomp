# CF1 read-out (M8, session 3): shipped Xenos defaults (ship) vs s0 and win3

Written 2026-11-25 ~13:45, strictly per `confirm/READOUT-PLAN.md` (18F69B57). Method is the same as READOUT-CF2, with M10's C1 (plateau threshold 0.97) and C2 (tails never "equal"). M10 cross-checks before use. Revised ~13:49 per M10 `cf1-check.md` (5A21C759): W1-W3 and NIT applied.

- **Window:** out dir `build/agent8/matrix/20261125-1255` (results.csv BA021F89). 19 runs = 1 cold run (ship, unscored) + 6 rounds × {ship, s0, win3}. Matrix `bench/agent8/run/matrix-windowCF1.json` D36A40CA.
- **Script:** `confirm/readout_cf.py` 9D75B69E (was B76E636C; only change: JSON keys `a`/`b` renamed `a_med`/`b_med`, and a C2 header note in the tables; numbers unchanged). It imports `confirm/readout_night.py` 1A5F9BE0, the READOUT-NIGHT code M10 confirmed (25BF9B1C).
  - Bootstrap: **10 000 draws, seed 1**, percentiles 2.5/97.5.
  - Command: `python -B readout_cf.py --window CF1 --hash-bins --json readout-cf1.json build\agent8\matrix\20261125-1255`
  - Full output: `confirm/readout-cf1-tables.md` 2D3656D5 (per-run table, every variant, order table; UTF-8). JSON: `readout-cf1.json` 321560F4.

## Verdict

**CF1 CONFIRMS the night result.**
- **win3 vs s0:** all four verdict metrics point the same way as WC's pooled result, and each CI excludes 0 and overlaps WC's CI.
  - p99, 1 % low and cores land almost on the night values.
  - fps is a little larger here: +10.0 % vs +7.7 %, with overlapping CIs.
- **ship vs s0:** the plain FINAL Xenos launch gives the same effect.
- **ship vs win3:** not shown different on all four, equal on none (weak form, as CF2). The wide cores CI comes from round 3 (host busy); the paired-round cores, +0.3 % [-3.9, +4.5], is info only.
- So the S1 rule "the shipped defaults reproduce win3" is met in its weak form.
- Nothing weakens or contradicts the night result.

## Headline: rounds 2-6, n = 5 per arm, 0 void, 1 M12 flag kept

| pair | fps mean | p99 ms | 1 % low ms | process cores |
|---|---|---|---|---|
| **win3 vs s0** | **+10.0 % [+7.5, +11.4]** | **-16.1 % [-19.5, -14.7]** | **-17.7 % [-19.6, -3.8]** | **-38.5 % [-41.6, -29.2]** |
| night WC pooled win3 vs s0 | +7.7 % [+6.3, +8.7] | -14.8 % [-17.1, -14.0] | -17.0 % [-18.0, -14.9] | -38.7 % [-40.3, -35.2] |
| S2 | consistent | consistent | consistent | consistent |
| **ship vs s0** | **+10.2 % [+6.8, +11.5]** | **-15.5 % [-17.9, -13.9]** | **-17.3 % [-19.2, -14.6]** | **-38.8 % [-41.1, -27.1]** |
| S2 | consistent | consistent | consistent | consistent |
| **ship vs win3** (margin) | +0.1 % [-2.2, +2.4] (±2) **not shown different** | +0.7 % [-2.2, +4.0] (±5) **not shown different** (C2) | +0.5 % [-16.5, +3.8] (±5) **not shown different** | -0.6 % [-15.6, +18.5] (±5) **not shown different** |

- **How to read the table:** each cell is the difference as a % of the second arm's median, with the 95 % bootstrap CI.
  - Every win3/ship vs s0 cell has a CI that excludes 0. Read: higher fps; lower p99, 1 % low ms and cores.
  - The paired-round cross-check goes the same way in 5/5 rounds for every win3/ship vs s0 metric.
- **Arm values** (median of per-run values):

  | arm | fps | p99 ms | 1 % low ms | cores | median ms (info) | GPU MHz | CPU eff MHz |
  |---|---|---|---|---|---|---|---|
  | ship | 493.7 | 4.160 | 4.365 | 1.51 | 2.110 | 1552 | 2301 |
  | win3 | 493.1 | 4.130 | 4.342 | 1.52 | 2.168 | 1537 | 2260 |
  | s0 | 448.1 | 4.921 | 5.278 | 2.47 | 2.034 | 1552 | 2012 |

- **C2:** ship vs win3 p99 has its whole CI inside ±5 %, so the code prints "equal". Per M10 C2, a tail is quoted as "not shown different", never "equal". Cores is not "equal" either: its CI is wider than ±5 %.
- **Why some CIs are wide:**
  - The ship vs win3 cores and 1 % low CIs, and the end nearest 0 of the win3/ship vs s0 cores CIs, are wide because of round 3. The win3 vs s0 1 % low bound of -3.8 % also comes from 1309-win3-r3.
  - In round 3, 1309-win3-r3 (non-game 4.10 cores, eff 2061 MHz: cores 1.74, 1 % low 5.08 ms) and 1311-ship-r3 (non-game 4.40, M12-flagged: cores 1.80) both ran on a busier host.
  - The paired-round ship vs win3 cores is +0.3 % [-3.9, +4.5] (info only).
- **Median ms (info only, never decides):** ship +3.7 % and win3 +6.6 % vs s0. Higher median with higher fps, the short-frame-mode effect described in READOUT-NIGHT S1.

## Variants (no variant changes any claim)

| set | win3 vs s0 fps / p99 / 1 % low / cores | ship vs s0 fps / p99 / 1 % low / cores | ship vs win3 fps / p99 / 1 % low / cores |
|---|---|---|---|
| **r2-6 headline** | +10.0 / -16.1 / -17.7 / -38.5 | +10.2 / -15.5 / -17.3 / -38.8 | n.s.d. ×4 |
| r2-6 without the M12-flagged run (ship n = 4) | same (no win3/s0 run flagged) | +10.3 [+7.9, +11.6] / -15.3 / -16.8 / -39.1 [-41.7, -37.4] | n.s.d. ×4 (fps [-1.5, +2.6]; cores [-16.3, +4.2]) |
| r1-6 side note (never decides) | +9.4 / -15.7 / -17.0 / -39.1 | +9.7 / -15.5 / -17.3 / -39.4 | fps "equal" [-1.8, +1.5]; p99, 1 % low, cores n.s.d. |
| r3-6 (info; round 2 is on the plateau) | +10.3 / -16.5 / -17.3 / -37.5 | +9.7 / -16.1 / -17.4 / -38.4 | n.s.d. ×4 |

(%, all win3/ship vs s0 CIs exclude 0; n.s.d. = not shown different; full CIs are in readout-cf1-tables.md.)

## Preconditions (plan section 1)

- **K1:** final_gate F1, F2 and F4 PASS on devfinal-bin (F1-F7 8/8 PASS, per the Overseer; fx rulings in `build/agent4/session3/`). Bins pinned in BIN-PINS FE4CD4FF.
- **K2:** `confirm/stage/stage-CF1-125054.txt` 81D38590 `mode: RECHECK`, `result: OK`. This is the recheck for this launcher session; the 11:24 recheck was 4BCFC35F.
- **K5:**
  - Runner preflight (`bench/agent5/day/status/runner-CF1-1251.txt`):
    - `desktop WinSta0\Default -> interactive desktop: timing can be valid`
    - `LogonUI not running`
    - `power AC (Win32_Battery status 2, charge 100 %)`
    - `builds none (...)`
    - `screensaver none`
    - devfinal-bin and devoff4b-bin `ok (MANIFEST.txt)`
    - `quiet gate: STRICT (MsMpEng 0.02/0.01/0.02, OfficeClickToRun 0.00/0.00/0.00, CrossDeviceService 0.03/0.03/0.03)`
  - Launcher log (`bench/agent5/day/status/log.txt`):
    - 12:51:17 GO read; 12:51:19 HOLD written; 12:51:19 GO ACCEPTED (sha256 ok, 19 runs, about 44 min)
    - 12:55:20 window START
    - 13:34:18 END, runner exit 0 (all runs OK), 39 min
    - 13:34:18 HOLD removed
  - M3 queue (`build/agent3/s4b/logs/queue.out.txt`, last written 12:44:30):
    - `12:43:54 DONE s33ond: exit 0 in 466 s`
    - `12:43:55 idle; waiting for: [f10aL,f10bL,s33stop6,s33stop7]`
    - `12:44:30 HOLD or PAUSE file: no launch; waiting`
    - Nothing after that, so no M3 row ran in the window (12:55:20-13:34:18). The Overseer may add M3's own lines.

## Which runs count (K4)

- **Counted:** all 18 scored runs; rounds 2-6 give 5 per arm, so n ≥ 4 holds. The cold run 1255-cold-ship is unscored by design.
- **Proof, 19/19 PASS:**
  - Every run: MANIFEST.txt sha matches the pin (devfinal F9C2BE72…, devoff4b DE11A914…); staged exe and DLL shas in the run dir match the MANIFEST (`--hash-bins`); bin_dir matches the arm.
  - ship: env_set has no LEGO_GPU_WAIT_* key; `check-defaults.py` D9936C56 `--mode xenos` PASS.
  - win3: env_set has BACKOFF_US=500 and SPIN_US=30; `--mode legacy` PASS.
  - s0: none of the `Final defaults` / back-off / C1 / precise-wait / 1 ms lines; no bad strings; no LEGO_GPU_WAIT_* key.
- **Functional, 19/19 PASS:** exit 0; no WER, dump or fatal line; STUCK-LOCK 0.
  - A ship functional FAIL would have voided the arm; there was none.
  - "Level reached" reads as "reached the 50 s window", because the timed route is the light title route.
- **Other checks:**
  - sys.csv has 31 columns on every row, in all 19 runs.
  - Runner exclusion flags: none. Info flags: `light_share_high` on every run (expected on this route); `nongame_load` on 1311-ship-r3.
  - Void list: no run void, no arm void.
- **M12 host-load gate** (w6_env_record formula): scored-run median 3.25 cores, threshold 4.25. **1 flagged: 1311-ship-r3 (4.40).** Without it, every claim stays the same (see Variants), so the headline keeps it, per the plan.
- **GPU plateau (C1, 0.97):** round-2 runs at 1575 / 1560 / 1552 MHz vs a rounds 3-6 median of 1544 MHz, so round 2 is on the plateau.
  - By round: r1 1627, r2 1560, r3 1560, r4 1552, r5 1530, r6 1537 MHz.
  - The drift from round 2 to round 6 is about -1.5 %, and the rotation balances it across arms.
  - Arm GPU medians are 1552 (ship), 1537 (win3) and 1552 (s0).
  - CPU eff MHz is lower in s0 (2012 vs ~2280), as in WC.

## Order (N1), headline set

- **Positions** (1st/2nd/3rd): ship 1/2/2, s0 2/1/2, win3 2/2/1, as planned.
- **First vs later:**
  - ship and s0 differ by ≤ 1.1 % in fps between positions.
  - win3's two first-position runs include the round-3 busy-host run, giving fps 487.3 vs 494.0 and cores 1.63 vs 1.49.
- No order effect large enough to touch a claim.

## Other observations (not verdicts)

- **Run-timing fix item 7:** run.json `sys_sampler.stop_line` is set in 19/19 runs.
- **ProcEvery re-check:** still open, because sys.json has no `sample_ms_max` key.
- **Scope (READOUT-NIGHT S2):** one light route, uncapped, AC power, this laptop. CF1 is not pooled with WC1-WC3.

## Deviations from the plan

1. **File name:** `confirm/READOUT-CF1.md` (the Overseer's instruction) instead of section 6's `READOUT-CF.md`.
2. **"Level reached":** read as "reached the 50 s window".
3. **Plateau criterion:** ≥ 97 % of the rounds 3-6 median (fixed at 11:40, before the data; M10 C1).
4. **Tail wording:** ship vs win3 p99 prints "equal" in the tables but is quoted as "not shown different" per M10 C2.
5. **Pair order:** "win3 vs ship" is computed as ship vs win3, with win3 as the reference, as in the plan's margin table. The sign flips; the claims don't.

sha8 of this file: see the report to the Overseer.

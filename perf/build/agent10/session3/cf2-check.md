# CF2 read-out cross-check (nf vs mc)

M10, 2026-11-25 ~12:40 local. Cross-check of M8's READOUT-CF2 against READOUT-PLAN and confirm-rating 31AD69BA (K1-K5, S1/S2, N1-N3).

## Files

| file | sha256 (16) | bytes |
|---|---|---|
| build/agent8/session3/confirm/READOUT-CF2.md | 5C601D91A70858DF | 8006 |
| build/agent8/session3/confirm/readout-cf2-tables.md | 6315D2DD4CB410B5 | 15540 |
| build/agent8/session3/confirm/readout-cf2.json | 2C2A517E4256823C | 39551 |
| build/agent8/session3/confirm/readout_cf.py | B76E636C77798F64 | 25792 |
| build/agent8/session3/confirm/readout_night.py | 1A5F9BE0D6B495A2 | 13435 |
| build/agent8/session3/confirm/READOUT-PLAN.md | 18F69B57C5C2BB26 | 9486 |
| build/agent10/session3/scratch-final/cf2chk/boot_check.py (mine) | 79E90DB0F8A6EE6B | 2700 |
| build/agent10/session3/scratch-final/cf2chk/boot_check.out.txt (mine) | 8F47C60F4E24FD13 | 4514 |

Base: raw data build/agent8/matrix/20261125-1159 (1 cold + 12 scored, rounds 2-6 = n 5 per arm). Launcher log bench/agent5/day/status/log.txt; runner note bench/agent5/day/status/runner-CF2-1154.txt (D20198AF); queue log build/agent3/s4b/logs/queue.out.txt.

## Verdict

**CONFIRMED.** Headline "nf reproduces mc in the weak form (S1)" stands as written. Every number I checked is reproduced exactly. The read-out already says the tails are "not shown different" rather than "equal" and gives the order/outlier explanation. No correction needed; NITs below.

## What I checked

### (1) Bootstrap / ratio CI: correct, same method as READOUT-NIGHT

- readout_night.py in confirm/ is byte-identical (1A5F9BE0) to the copy I confirmed in readout-night-xcheck 25BF9B1C. readout_cf.py calls rn.boot_diff (difference of medians / observed ref median, percentile bounds ds[int(.025n)] and ds[int(.975n)-1]) and rn.paired (log ratio, t-CI, keyed on (pass_i, round)). Same method as the night read-out.
- My own script (boot_check.py) reproduces every headline CI exactly with seed 1, with seed 7, and from the exact (enumerated) bootstrap distribution:
  - fps -0.2 % [-0.8, +4.2]
  - p99 +3.4 % [-39.8, +11.8]
  - 1 % low +4.0 % [-44.7, +23.7]
  - cores -0.3 % [-4.7, +3.3]
  - median frame +0.0 % [-0.7, +0.1]
- **The asymmetry is legitimate**, not a bug. With n = 5, the median of a resample equals the sample minimum (or maximum) with P ~ 5.8 %, which is above 2.5 %, so a single extreme run sets a bound. The extreme run is mc-r2 (1205): fps 439.52, p99 4.434, 1 % low 5.097.
  - fps upper = 457.771 / 439.52 - 1 = +4.2 %.
  - p99 lower = (3.202 - 4.434) / 3.098 = -39.8 %.
  - The point estimate (ratio of observed medians) can therefore sit near one end of the interval. This is expected for a percentile bootstrap of a median at n = 5.
- Per-run inputs (rounds 2-6) match the json:
  - fps nf [457.77, 458.17, 458.83, 461.53, 462.06]; mc [439.52, 459.54, 459.88, 461.42, 462.07]
  - p99 nf [2.864, 2.965, 3.202, 3.211, 3.212]; mc [2.835, 2.904, 3.098, 3.102, 4.434]
  - 1 % low nf [3.173, 3.252, 3.566, 3.978, 4.239]; mc [3.171, 3.192, 3.427, 3.475, 5.097]
  - cores nf [1.774, 1.778, 1.829, 1.833, 1.835]; mc [1.769, 1.811, 1.835, 1.861, 1.890]

### (2) The four deviations: acceptable

- File name/path differs from plan section 6: cosmetic (NIT N3).
- "Level reached" = the run reached its 50 s scoring window: acceptable for the light title route, where there is no level load; count True in all 12 scored runs.
- Plateau rule fixed as min(round-2 gpu) >= 0.97 x median(rounds 3-6): immaterial for CF2, because gpu is 1740 MHz in every run of every round, so it is met under any criterion. It must be applied identically (same code, same threshold) for CF1, where it can matter (condition C1).
- Thread ms/f matched by thread name rather than id: correct choice (ids change per run); no effect on any verdict metric.

### (3) Proof and void logic: 13/13

- Proof specs in readout_cf.py match the plan table: nf = MANIFEST D7C7B706, nativefinal-bin, check-defaults native-old, env without MISS_CACHE, FRAME_METRICS present; mc = MANIFEST B63769FE, native4b-bin, bad-strings check, env MISS_CACHE=1 + FRAME_METRICS.
- Void rules match the plan: 2 proof FAILs in an arm (cold run included) void the arm; a final-bin functional FAIL voids the arm; n < 4 gives no verdict.
- M12 gate = median + 1.0 core (ncpu from os.cpu_count()), as planned.
- All 13 runs: proof / functional / sys31 True, misses 26, gpu 1740, M12 flag False; count True for the 12 scored runs (cold unscored). Non-game CPU 3.44-3.95 % (cold 6.39 %, unscored). No void, no flag.

### (4) K5 quotes: verified

- runner-CF2-1154.txt: L1 quiet gate STRICT 11:59:37 (MsMpEng 0.01/0.01/0.01); L32 desktop interactive; L33 LogonUI not running; L34 AC 100 %; L37 builds none; L38/L39 both bins ok (MANIFEST.txt); L40 screensaver none.
- Launcher log: 11:54:36 GO ACCEPTED (sha256 ok); 11:54:36 HOLD written; 11:59:38 window CF2 START; 12:26:04 END, runner exit 0 (26.4 min); 12:26:04 HOLD removed. Also: power scheme Balanced; bins unchanged since GO.
- Queue isolation: queue.out.txt L308 11:22:07 DONE s33offd; L310 11:23:04 "HOLD or PAUSE file: no launch; waiting"; next line L311 is 12:34:47. No queue LAUNCH between 11:23 and 12:34, so nothing from the queue overlapped the 11:59-12:26 window.

### Wording

- The headline already limits itself to the weak form and says only cores is "equal". Line 24 states the tails are "not shown different" and that the data do not support "equal" there; line 40 reports the rounds 3-6 tail points (+6.9 % p99, +14 % 1 % low, CIs include 0) and refuses post-hoc re-scoring. That is the correct reading: on the tails, CF2 is absence of evidence (CI half-widths 25-45 %), not evidence of similarity.
- The order effect (N1: first-in-round runs have worse tails; mc first 3x, nf 2x) is reported and is a plausible explanation of the tail spread. It is unbalanced by one slot, which slightly favours nf on the tails; it does not change the verdict.

## Conditions

- C1 (for CF1): use the same plateau code and 0.97 threshold as CF2, fixed before the CF1 data are read. Report the per-round gpu medians so the check is visible.
- C2: any use of CF2 downstream must quote "weak form; tails not shown different" and must not cite CF2 as showing equal p99 / 1 % low.

## Findings

- NIT N1: 10 000 bootstrap draws vs the night default of 20 000. This is what the plan prescribes; the exact-distribution check shows the bounds are identical, so no effect.
- NIT N2: the readout_cf.py docstring says the rules were fixed "11:40, CF1 running". CF1 had not run at that time per the Overseer. Provenance wording only; I can't verify the time. Suggest correcting to "fixed 11:40, before CF2 data".
- NIT N3: output file name/path differs from plan section 6.
- NIT N4: ProcEvery sample_ms_max is still open from confirm-rating; not used by any CF2 verdict.
- NIT N5: "K0/F0" in the runner note maps in the script to the FATAL list + STUCK-LOCK (functional), bad strings (mc) and check-defaults (nf). A one-line mapping in the read-out would help.
- Not done (on purpose, to keep IO light while runs are active): exe re-hashing of the 13 run dirs. MANIFEST and env checks rely on readout_cf.py's own proof results, which I reviewed as code.

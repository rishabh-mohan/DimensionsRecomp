# CHECK.md: read-only check of task #14 (T-std read-out kit)

- **Checker:** subagent 5ce3ebb7 (read-only).
- **When:** 2026-11-22, 21:11-21:28 local.
- **Rules followed:**
  - `perf-notes/WINDOW-HOLD.txt` was absent before every command.
  - Python ran at Below Normal with `python -B`, one process at a time.
  - Nothing was written outside `check-readout/`.

**Files in `check-readout/`:**

| file | what it is |
|---|---|
| `selftest.txt` | check 1 output |
| `check-w4b.md/.json`, `check-w5.md/.json`, `run-w4b.txt`, `run-w5.txt` | check 2 re-runs |
| `indep_check.py` | my own script, described below |
| `indep.txt` | its full log: `RESULT PASS (133 passed, 0 failed)`, 149 s |

`indep_check.py` imports nothing from the kit. It parses T975 from `noise_methods.py`'s source text and uses its own F, t and chi-square code and its own one-way and two-way OLS fits.

## Summary

| check | result | key numbers |
|---|---|---|
| 1 self-test | **PASS** | `RESULT PASS (112 checks, 0 failed)`, no FAIL line, 59 s |
| 2 re-run diffs | **PASS** | md: only line 5 (`- command:`) differs (W4b 101/101 lines, W5 95/95). json: only `/command` differs; `params` is identical |
| 3a RESULTS.md rows | **PASS** | W4b: 6 table rows + 3 median-delta rows. W5: 8 + 2. All 19 verbatim |
| 3b round test | **PASS** | W4b F 7.029408 on (3, 8), p 0.0124296, so B-block T-std. W5 F 0.239340 on (2, 8), p 0.7925868, so T-std. Both match the json |
| 3c CI formula | **PASS** (one expected exception) | 26 of 28 arm cells exact. W4b B-block arm B uses the OLS variance (0.6111, not 1/3 + 1/4 = 0.5833); my own OLS reproduces it |
| 3d extra recompute | **PASS** | My own one-way and two-way OLS on the per-run values give every json number and md row I checked: 4 metrics x 3 methods x 2 windows, plus guards a and c |
| 4 REPEATS.md | **PASS** | All 7 tables x 15 cells (105 cells) and the json grid. Also s, unflagged s, timing, 33.9 min, chi-square, t0.80 and 13 text fragments |
| 5 READOUT.md | no wrong statement | 6 statements are imprecise or incomplete (see section 5) |

**Mismatches: 0.**

## 1. Self-test

`python -B build\agent7\w4b-noise\test_noise_methods.py`, Below Normal, exit 0, 59 s. The last line is `RESULT PASS (112 checks, 0 failed)`. There is no FAIL line.

## 2. Re-run diffs

Commands (Below Normal; each took about 12-13 s, exit 0):

```
python -B build\agent7\w4b-noise\readout.py build\agent8\matrix\20261122-1541 -o build\agent7\w4b-noise\check-readout\check-w4b.md --json build\agent7\w4b-noise\check-readout\check-w4b.json
python -B build\agent7\w4b-noise\readout.py build\agent8\matrix\20261122-1756 -o build\agent7\w4b-noise\check-readout\check-w5.md --json build\agent7\w4b-noise\check-readout\check-w5.json
```

- **W4b md:** 101 lines on each side. Only line 5 differs: the `- command:` line, whose `-o` and `--json` paths differ.
- **W5 md:** 95 lines on each side. Only line 5 differs, in the same way.
- **json:** I compared every key and value recursively. Each file has one differing path, `/command`. `/params` is identical because it leaves out `out` and `json`.

## 3. Independent regression

### 3a. RESULTS.md rows in the readout md

I stripped `**` and treated `\*` as `*`. Every row below was found and is present verbatim. The rows are listed in `indep.txt`, lines 13-32.

- **W4b:**
  - raw, T-std and B-block T-std on median ms and fps (6 rows);
  - median deltas: raw -10.8 / -5.4 / -1.1, T-std -0.8 / -0.6 / +0.2, B-block T-std -1.9 / -1.1 / -0.4.
- **W5:**
  - the same 6 rows, plus T-std p99 ms and T-std 1 % low fps;
  - median deltas: raw +5.5 / +2.6 / +4.0 / +3.1, T-std +2.3 / +2.5 / +2.7 / +2.1.

### 3b. Round test (F and p with my own code)

- **F**, from the json summaries: F = ((sd1² df1 - sd2² df2) / k) / sd2², with k = rounds - 1.
- **p**, by Simpson integration of the F density in two ways:
  - from 0 to F, with x = y²;
  - from F to infinity, with z = x + u / (1 - u).
- For d1 = 2, I also used the closed form (1 + 2F/d2)^(-d2/2).

| window | metric | F | df | p (mine, both ways) | json p | decision |
|---|---|---|---|---|---|---|
| W4b | median ms | 7.029408 | (3, 8) | 0.01242963 | 0.01242963 | p < 0.05, so B-block T-std; json: B-block T-std |
| W4b | fps | 4.482298 | (3, 8) | 0.03987037 | 0.03987037 | same side as median ms, so no "fps disagrees" note |
| W5 | median ms | 0.239340 | (2, 8) | 0.79258682 (closed form 0.7925868201) | 0.79258682 | T-std; json: T-std |
| W5 | fps | 0.171212 | (2, 8) | 0.84565031 | 0.84565031 | same side as median ms |

- The md prints `F = 7.03 on (3, 8), p = 0.012` (W4b) and `F = 0.24 on (2, 8), p = 0.793` (W5).
- Cross-check: the residual SS of my own one-way and two-way fits gives the same F (7.029408 and 0.239340).

### 3c. CI = exp(dl ± t sd sqrt(1/n_a + 1/n_ref)) - 1

t comes from T975, using the next lower df between entries. I checked every arm of both primary tables on median ms and fps: 28 cells.

- **T-std:** all 14 cells match the json to 1e-9. Examples:
  - W4b median ms, arm B: df 11, t 2.201, sd 0.022963, n 3/4, giving [-5.7898, +1.7716].
  - W5 median ms, arm d11t: df 10, t 2.228, sd 0.020914, n 3/3, giving [-1.4202, +6.3736].
- **B-block T-std:**
  - W5: all 8 cells exact. W5 is balanced, so each arm's variance factor is 2/3 = 1/3 + 1/3. Example: median ms d11t, df 8, t 2.306, sd 0.022713, giving [-1.8843, +6.8768].
  - W4b: arms d3 and d11t are exact. Example: median ms d3, giving [-3.7197, +0.8177].
- **Expected exception: W4b B-block T-std, arm B.**
  - Arm B has no round-2 run (1551-B-r2 is invalid), so the simple formula does not apply:

    | metric | simple formula | json |
    |---|---|---|
    | median ms | [-4.9039, -0.0542] | [-4.9596, +0.0043] |
    | fps | [+0.6153, +11.6354] | [+0.4923, +11.7720] |

  - The kit uses the OLS variance factor (X'X)⁻¹ = 0.6111 instead of 1/3 + 1/4 = 0.5833. The difference is the round imbalance.
  - My own OLS gives the json values exactly. The printed cells, -2.5 [-5.0, +0.0] and +6.0 [+0.5, +11.8] \*, are RESULTS.md's.
  - With the simple formula, the median-ms cell would read [-4.9, -0.1] \*, a false `*`.
  - This is not a kit error. The check formula does not hold for an arm that is unbalanced across rounds.

### 3d. Extra: my own recompute from the per-run values

These use the kept runs in the json and my own code only.

- **One-way fit, raw and T-std, all 4 metrics.**
  - Method: the pooled within-arm SD of ln v, with df = runs - arms.
  - These equal the json: sd, df, ref band, 4 vs 4 band, GM deltas, CIs, `*` and median deltas.
  - The md rows are identical. The raw tails are not printed.
- **Two-way OLS (Gauss-Jordan), B-block T-std, all 4 metrics.**
  - These equal the json: sd, df, round terms b, CIs and the adjusted median deltas. The md rows are identical.
  - W4b median ms: b = -0.04120, -0.03135, -0.03979.
  - The md prints `round 2 -4.0 %, round 3 -3.1 %, round 4 -3.9 %`.
  - 100 |b| = 4.12 / 3.14 / 3.98, which is RESULTS.md's "3.1-4.1 %".
- **Guard (a):** my own one-way ANOVA on the light share matches the json and md:
  - W4b: F 0.40 on (3, 11), p 0.756.
  - W5: F 0.33 on (4, 10), p 0.850.
- **Guard (b):** in the printed rows, every raw CI overlaps the primary's CI. Both windows print `raw agrees for every arm`, which is correct.
- **Guard (c):** the flagged lists, my own leave-one-out residual rows and the mean/RMS line all equal the md.
  - W4b: 7 flagged runs.
  - W5: 3 flagged runs (1808-s0-r2, 1817-base-r2, 1821-d11t-r3). Flagged mean: raw +13.7, T-std +3.4 (25 % of raw), B-block +3.0 (22 %). RMS of the other kept runs: 5.4 / 2.1 / 2.1.

## 4. REPEATS.md (my own code)

**s and unflagged s:**
- `repeats.json` cv.\*.s equals `readout-w5.json` methods['T-std'][\*]['sd_ln'] bit for bit, on df 10:

  | metric | s |
  |---|---|
  | median ms | 0.0209139 |
  | fps | 0.0182176 |
  | p99 | 0.0409649 |
  | 1 % low | 0.0501308 |

- Unflagged s: the 12 kept runs not in guards.c.flagged, df 7. Median ms 0.014685 (1.5 %), fps 0.011832 (1.2 %). Both equal `s_calm`.
- T975 table vs my own t quantile: all 22 entries agree within 6e-4.

**Timing** (W5's 16 run.json files: 15 scored + 1 cold):

| quantity | value |
|---|---|
| cold run start | 17:56:02.409 |
| first scored start | 17:57:53.683 |
| last scored run | 18:27:55.005 to 18:29:54.655 |
| cold slot | 111.274 s |
| slot | 128.666 s |
| last run | 119.650 s |
| run mean | 120.125 s |
| total | 2032.246 s = 33.87 min, printed 33.9 |

- All of these equal `repeats.json` timing.
- I rebuilt the section-2 sentence ("1.70 + 2.14 x A n min", "measured 33.9 min (17:56:02-18:29:54)") and it appears verbatim.

**Tables:** every cell of each table (2-6 arms x 3/4/5 repeats = 15 cells per table) with my own hw = 100 (exp(t975(df) s sqrt(2/n)) - 1). 105 cells, 0 mismatches.
- Tables: median ms, fps, tails, minutes, B-block (df (A-1)(n-1)), MDE (t975 plus my own t0.80) and CV 1/2/3 %.
- Examples:

  | table | (6 arms, 3 repeats) | (2 arms, 5 repeats) |
  |---|---|---|
  | median ms | ±3.8 (12) | ±3.1 (8) |
  | fps | ±3.3 | ±2.7 |
  | B-block | ±3.9 (10) | ±3.7 (4) |
  | minutes | 40.3 (18) | 23.1 (10) |
  | MDE | 5.3 | 4.3 |
  | CV 1/2/3 % | 1.8 / 3.6 / 5.5 | 1.5 / 3.0 / 4.5 |

- The `repeats.json` grid (hw, hw_block and mde80 for 4 metrics, plus minutes and df) equals my values.

**CV range and MDE:**
- My own chi-square quantiles on df 10 are 3.2470 and 20.4832. They give 0.6987-1.7549 x, which equals `repeats.json` cv_range and prints as "0.70-1.75".
- My own t0.80: df 4 0.9410, df 10 0.8791, df 24 0.8569.

**Text:** I rebuilt 12 text fragments (the short answer and sections 1, 3, 5 and 6) with my own numbers. All appear verbatim, as does the section-2 sentence.

## 5. READOUT.md vs the code as it stands

No statement is wrong for the default options. These are imprecise or incomplete:

1. **L69** says "It imports noise_methods.py and noise_case.py (unchanged) and bench/agent7/w4b_readout/w4b_readout.py".
   - readout.py loads only noise_methods.py and noise_case.py (readout.py L62-63). It gets the loader as `W = N.W` (L64), which noise_methods.py imports.
   - "(unchanged)" fits the file times: noise_methods.py was last written at 19:53:34 and noise_case.py at 19:53:40, both before readout.py was created at 20:49:28. There is no git history to check against, because the folder is gitignored.
2. **L37-40 (G11):**
   - The code has four statuses: OK, PARTIAL, MIXED and NO DATA (readout.py L199-220). READOUT.md doesn't describe PARTIAL (some runs have no power data) or NO DATA.
   - The status uses only overlay, scheme and AC (`G11_KEYS`, L79). A saver-only change inside a window still gives OK, but the G11 line lists that run under "changed inside the window" (L221-223). So "no change inside any window" holds only for overlay, scheme and AC.
3. **L16-23 (Options):** `--normal-priority` (L719) is not listed.
4. **L18** says "the G11 line prints the exact flags to use". It does so only when some round has every scored run on one unchanged overlay. Otherwise it prints "no round has every arm on one unchanged overlay" (L246-252).
5. **L46** says notes include "filters that match nothing".
   - Only `--rounds` and `--drop` give that note (L303-308).
   - An `--overlay` that matches no run gives no note. Each run is just left out with "overlay X, not --overlay Y".
6. **L62:** the self-test checks guard b on synthetic data (test_noise_methods.py L276-280) and on W5 (L397), but not on W4b. W4b does print "raw agrees for every arm", and I confirmed that from the rows.

Not a problem: L30 and L34 say "p < 0.05", while the code uses p < `--alpha` (default 0.05). L20 already says this.

## Other observations (not mismatches)

- **The 33.9-minute check is circular.** REPEATS.md section 2 says "Check: 15 runs give 33.9 min; measured 33.9 min". This holds by construction: for A n = 15 the model's terms add up to exactly last end - cold start (cold slot + 14 slots + last run). It confirms the arithmetic, not the model.
- **The T975 convention matters for one grid point.** Only the 6-arm, 5-repeat T-std cells (df 24) fall between table entries. There t = 2.086 (the df-20 entry) is used instead of the exact 2.064, so the half-widths are about 1 % wider. This is conservative and follows the stated convention.

  | cell | table t | exact t | prints |
  |---|---|---|---|
  | median ms | ±2.80 | ±2.77 | ±2.8 either way |
  | p99 | ±5.55 | ±5.49 | ±5.6 vs ±5.5 |
  | MDE | 3.97 | 3.94 | 4.0 vs 3.9 |

- **Extra W5 row:** readout-w5.md has a B-block median-delta row (+1.4 / +1.7 / +2.5 / +1.9) that RESULTS.md does not have. My own OLS reproduces it.

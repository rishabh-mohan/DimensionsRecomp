# Check of bench\agent11\timerq_slowstate_3mode.ps1 (helper for Agent 11, task #10)

2026-11-22, by a read/stage/check-only subagent of Agent 11. I did not build anything, launch the game or change any git state. I wrote files only under `build\agent11\s4a\slowstate3-check\` (scripts, outputs, this report) and `build\agent11\s4a\slowstate3-test\` (synthetic data). WINDOW-HOLD.txt was checked before every command and was never there.

## Verdict: PASS (all 4 checks)

The copy gives the original's numbers for every run in W4b and W5. It assigns the expected mode to every run, raises no flags and shows no MIXED arms there. It also behaves as specified on all 10 required synthetic cases and 12 extra probes. I found **no functional bug that affects W4b/W5**. Section 5 lists 7 fragilities, most of them minor. Some come from the original's code and were kept unchanged on purpose.

| script | sha256 at start | sha256 at end |
|---|---|---|
| bench\agent11\timerq_slowstate_3mode.ps1 | E9049B33551CA65891A90334FC56FE774F4D7C072DB0393B31929C55064CA59E | E9049B33551CA65891A90334FC56FE774F4D7C072DB0393B31929C55064CA59E |
| bench\agent11\timerq_slowstate.ps1 (frozen original) | 38A3F6AC23C57B506A51F62B53484A89F437836E0F25C44E5318322ECD1CA8F1 | 38A3F6AC23C57B506A51F62B53484A89F437836E0F25C44E5318322ECD1CA8F1 |

**Code review against the original.** I checked this with a scripted line comparison. Original lines 17-46 (the matrix/run loop up to `$onsetText`) match copy lines 49-78 exactly, except that `$blocking` is renamed `$envOn`. That covers run selection, the ff test, the sample filter, the streak/onset logic and span. The onset_s, slow_pct, span_s and fg expressions (original lines 51-54) are identical at copy lines 125-128. With `-Matrix` empty, the copy's matrix selection (line 47) is the original's line 16 unchanged. `-Matrix X` takes exactly the folder named X: the match is case-insensitive and there is no name-pattern check. The mode is set at copy lines 112-115 (spin, then blocking if env is set, then unknown if the cvar is on and there is no log, then precise if the line is present). The resulting precedence is precise > unknown > blocking > spin, which is what the brief asks for. The flag conditions at lines 107-111 match the brief. `-Property $show` makes all 13 columns print; PS 5.1's automatic view would stop at 10.

## What I ran

All commands ran from the workspace root with Windows PowerShell 5.1.26100 (`powershell -NoProfile -ExecutionPolicy Bypass -File <script> ...`) and Python 3.11.9. All are single-threaded. Every output file is in `build\agent11\s4a\slowstate3-check\`.

1. original `-Since 20261122-1541` -> `orig-since-1541.txt`. This scans 20261122-1541 and 20261122-1756 only. The other folders whose names sort after '20261122-1541' (`s3-n123-0205`, `s3-n2-0210`, `verify3*`) fail the `^\d{8}-\d{4}$` filter in both scripts.
2. copy `-Matrix 20261122-1541 -OutCsv build\agent11\s4a\slowstate3-check\w4b-3mode.csv` -> `w4b-3mode.txt`
3. original `-Since 20261122-1756` -> `orig-since-1756.txt`
4. copy `-Matrix 20261122-1756 -OutCsv ...\w5-3mode.csv` -> `w5-3mode.txt`
5. copy `-Since 20261122-1541` with no `-Matrix` -> `copy-since-1541.txt`. This checks that the copy's `-Since` path selects the same runs.
6. `python make_cases.py` built the synthetic tree in `build\agent11\s4a\slowstate3-test\`:
   - matrix `20990101-0000`: 24 case dirs. 21 should be kept and 3 should be skipped.
   - matrix `20990101-0001`: 2 dirs for the column-width probe.
   - `logs\`: logs that can only be reached through `--log_file`.

   Each case dir got copies of only `sys.csv`, `run.json` and, where needed, `game.log` from W5 runs 1815-d11p-r2, 1817-base-r2 or 1756-cold-base. Then run.json/game.log were edited. In every case `--log_file` was either rewritten (to the case's own game.log, a test log, or a missing file) or removed. The expected results are in `synth-expected.json`.
7. copy `-Root build\agent11\s4a\slowstate3-test -Matrix 20990101-0000 -OutCsv ...\synth-3mode.csv` -> `synth-3mode.txt`. The same with `-Matrix 20990101-0001` -> `synth-long.txt` / `synth-long.csv`.
8. `probe.ps1` -> `probe-out.txt` (PS 5.1 behaviour probes used as evidence in section 5)
9. `python verify.py` -> `verify-out.md` (all comparisons, appended below), then `python assemble_report.py` -> this file

## Results per check

### 1. W4b = 20261122-1541 (17 runs): PASS
- **Run set:** the same 17 runs appear in the run dir listing, the original's output (filtered to this matrix), the copy's CSV, the copy's text table, the copy's `-Since` output and the Python recompute.
- **Numbers:** for every run, onset_s, slow_pct, span_s and fg are identical between the original and the copy. The copy's `env` equals the original's `blocking` for every run: True only for d11t-r1..r4.
- **Modes:** d11t ×4 = blocking. The other 13 runs (cold-d0, d0 ×4, B ×4, d3 ×4) = spin.
- **Flags and arms:** 0 flags, 0 MIXED arms. The copy's text table equals its CSV in all 13 columns.
- **Summary line:** `precise runs: 0, with slow state: 0; blocking runs: 4, with slow state: 4; spin runs: 13, with slow state: 12`. This agrees with the original's rows for this matrix: blocking 4 (4 slow), non-blocking 13 (12 slow). Counts line: `runs with flags: 0; mixed arms: 0`.

### 2. W5 = 20261122-1756 (16 runs): PASS
- **Run set:** the same 16 runs appear in all six sources.
- **Numbers:** identical between the original and the copy. env equals blocking for every run: True only for the 3 d11t runs.
- **Modes:** base ×3, s0 ×3, d11 ×3 and cold-base = spin. d11t ×3 = blocking. d11p ×3 = precise: each d11p game.log has exactly 1 precise line, and the cvar is in both args and params.cvar.
- **Flags and arms:** 0 flags, 0 MIXED arms.
- **Summary line:** `precise runs: 3, with slow state: 3; blocking runs: 3, with slow state: 3; spin runs: 10, with slow state: 9`. Precise plus spin is 13 runs with 12 slow, which equals the original's non-blocking 13/12.

### 3. Independent Python recompute: PASS
- **Method:** `verify.py` recomputes everything from the raw sys.csv, run.json and game.log files. It was written from the brief's rules, not translated from the .ps1. Differences in approach: an explicit streak scan for onset, a per-token cvar test instead of a regex on the joined string, a structural search of env_set, and line splitting on `\r\n|\r|\n` as .NET does. It reads `--log_file` only when `<run>\game.log` is missing.
- **Per run (33/33):** all 13 columns match the copy's CSV (arm, mode, env, pcvar, precise, ms1, onset_s, slow_pct, span_s, fg, flags). The unrounded slow_raw and onset_raw agree to within 1e-9.
- **Arm tables (11 rows):** identical, including mean_slow_pct, computed .NET Framework style (scale by 10, round half to even, unscale), and mean_onset_s. The per-mode summary lines and the flags/mixed counts lines are identical too.
- **Rounding:** no unrounded value is close to a .5 tie. The closest are span 117.496 (1542-d0-r1) and 121.504 (1757-base-r1), each 0.004 away. So banker's versus half-up rounding, or differences of one unit in the last place when parsing, cannot change any printed number. Banker's rounding in PS 5.1 is confirmed: `[math]::Round(2.5,0)=2`, `[math]::Round(3.5,0)=4`.

### 4. Synthetic cases: PASS
- **Cases:** all 10 required cases (a-j) and 12 extra probes (k-w) came out exactly as expected. The per-case table is below.
- **Summary line:** `precise runs: 7, with slow state: 7; blocking runs: 5, with slow state: 5; spin runs: 7, with slow state: 6; unknown runs: 2, with slow state: 2` matches what I expected. Spin has 6 slow out of 7 because case r uses the cold-base sys.csv, which has no slow state. The `unknown` part is printed only when its count is not zero; it is missing from the W4b/W5 summaries.
- **Counts and flags table:** the counts line is `runs with flags: 10; mixed arms: 1`. The trailing flags table lists exactly the 10 flagged runs.
- **MIXED:** arm x shows mode `spin/precise` and note `MIXED`.
- **Skipped runs:** h (`ff_signal_epoch_s` = 0), s (the ff key is absent) and t (no sys.csv) are left out, as expected.
- **No real log was read:** the runs without a log (f, g, m, w) show `no_log` and ms1 = 0.
- **Python cross-check:** the Python recompute on the synthetic tree agrees with the copy in every column for all 21 kept runs, and skips the same 3.

## 5. Issues and fragilities

None of these changes any W4b/W5 result. I did not modify the script; each item has a suggested fix.

1. **The console run table can silently truncate its last column (cosmetic).** The table is printed with `Format-Table -AutoSize | Out-String -Width 240`. When a row is wider than 240 characters, PS 5.1 cuts the last column (flags) to `...` and gives no warning. I reproduced this with a 140-character arm name: `synth-long.txt` shows the flag as `precise_cvar...` (Appendix A). Real tables are about 115 characters wide, which leaves about 125 characters of room. The CSV is not affected. *Fix:* use `Out-String -Width 4096` or `Format-Table -Wrap`, or treat `-OutCsv` as the authoritative output.
2. **The pcvar test is a substring regex on the joined argument string:** `timer_queue_precise_wait(=(true|1))?(\s|$)`.
   - Probes (Appendix B): `--no_timer_queue_precise_wait` gives True because the regex has no left boundary. `--timer_queue_precise_wait false`, with the value as a separate token, also gives True (case p). `=yes` and `=on` give False.
   - Real runs only use `--timer_queue_precise_wait=true` and `timer_queue_precise_wait=true`, so there is no impact today.
   - The impact would be limited anyway, because the log line decides precise. A wrong pcvar only changes flags, or makes a run with no log show unknown instead of spin/blocking.
   - *Fix:* test each token on its own with `^(--)?timer_queue_precise_wait(=(true|1))?$` (case-insensitive). If yes/on should count as on, add them.
3. **pcvar does not look at TOML.** Only args and params.cvar are scanned. A cvar set through run.json `toml_set` or the run dir's `legodimensions.toml` would be missed. No real run does this: every `toml_set` is `{}`, and no `legodimensions.toml` in either matrix mentions timer_queue. If it did happen, a run with a log would still get mode precise (from the line) but a false `precise_line_no_cvar` flag. A run without a log would get spin/blocking instead of unknown. *Fix:* also scan `toml_set` and `<run>\legodimensions.toml`.
4. **The `--log_file` fallback can read a log outside the run dir.**
   - When `<run>\game.log` is missing, the script follows the run.json `--log_file=` path wherever it points. Case k used an absolute path and case l a quoted relative path.
   - If a run dir is copied or moved without its game.log, the script silently reads the original run's log. This is the hazard the brief warned about.
   - Relative paths are resolved against the caller's current directory. Case l passed only because the script was run from the workspace root.
   - In W4b/W5 every run has its own game.log, so the fallback is never used.
   - *Fix:* use the fallback only if it resolves to `<run>\game.log`, or add a `log_via_arg` flag when it is used, and resolve relative paths against the run dir.
5. **Arms are grouped without regard to case** (`Group-Object` default). Tags `Y-r1` and `y-r2` were merged into one arm row `Y` with runs=2 (case u; also probed in Appendix B). Real tags use consistent case, so there is no impact. *Fix:* use `Group-Object matrix, arm -CaseSensitive`, or keep this if it is intended.
6. **The env test only checks that the name is present.**
   - `{"REX_TIMER_WAIT_BLOCKING":"0"}` counts as blocking (case n). The list form `["REX_TIMER_WAIT_BLOCKING=1"]` is also detected (case o).
   - This is the original's rule, and the brief requires keeping it. But if a future matrix sets the variable to 0 to turn it off, the mode would be wrong.
   - I could not check how the game reads the value, because the timer-queue source is not among this repo's tracked files.
   - *Fix (optional):* parse the value and treat 0, false or an empty value as off. params.env carries the same information as a string.
7. **Behaviour carried over unchanged from the original** (kept on purpose so the math matches; listed for completeness):
   - **a. Short sys.csv rows are counted as slow.** If a row is missing trailing fields, e_eff_mhz is `$null`. That passes the `-ne ''` filter, and `[double]$null` is 0 (Appendix B), so the row counts as a 0 MHz low sample. All 33 real sys.csv files have all 24 fields on every row, so there is no effect. *Fix:* filter with `-not [string]::IsNullOrEmpty($_.e_eff_mhz)`.
   - **b. One bad value stops the whole scan, and skipped runs are not reported.** With `$ErrorActionPreference='Stop'` and no try/catch around the `[double]` casts, a single non-numeric value in any sys.csv ends the scan. Runs with an unreadable run.json, ff <= 0, no sys.csv or no samples are dropped without any message. *Fix:* add a try/catch per run and print a `skipped: <run> (<reason>)` list.
   - **c. `-OutCsv` formatting depends on culture and encoding.** slow_raw and onset_raw are formatted with the current culture: under de-DE, 13.5 is written as `"13,5"` (Appendix B). That is harmless on this en-US machine. `-Encoding ASCII` would also turn any non-ASCII text into `?`. *Fix:* format the raw values with the invariant culture.
   - **d. No warning for an empty matrix folder** (from reading the code). If `-Matrix` points at a folder with no `runs\` subfolder, the script prints empty tables and zero counts without a warning.

## Check results (generated by verify.py)

- **1 W4b: PASS**
  - run dirs 17; original rows 17; copy CSV rows 17; copy table rows 17; copy -Since rows 17; python rows 17 (skipped 0)
  - copy summary: `precise runs: 0, with slow state: 0; blocking runs: 4, with slow state: 4; spin runs: 13, with slow state: 12 (E below 800 MHz for 3+ samples)`; counts: `runs with flags: 0; mixed arms: 0`
  - original restricted to 20261122-1541: blocking 4 (slow 4), non-blocking 13 (slow 12)
- **2 W5: PASS**
  - run dirs 16; original rows 16; copy CSV rows 16; copy table rows 16; copy -Since rows 16; python rows 16 (skipped 0)
  - copy summary: `precise runs: 3, with slow state: 3; blocking runs: 3, with slow state: 3; spin runs: 10, with slow state: 9 (E below 800 MHz for 3+ samples)`; counts: `runs with flags: 0; mixed arms: 0`
  - original restricted to 20261122-1756: blocking 3 (slow 3), non-blocking 13 (slow 12)
- **3 python recompute: PASS**
  - 20261122-1541: 17 runs, all 13 columns + slow_raw/onset_raw (|diff| < 1e-9) compared; arm table 5 rows compared; smallest distance of any rounded value from a .5 tie: 0.0040 (1542-d0-r1 span_raw = 117.49600005149841)
  - 20261122-1756: 16 runs, all 13 columns + slow_raw/onset_raw (|diff| < 1e-9) compared; arm table 6 rows compared; smallest distance of any rounded value from a .5 tie: 0.0040 (1757-base-r1 span_raw = 121.50400018692017)
- **4 synthetic: PASS**
  - arm rows: 19 (expected 19 with case-insensitive grouping); Y/y rows: ['Y runs=2']
  - summary: `precise runs: 7, with slow state: 7; blocking runs: 5, with slow state: 5; spin runs: 7, with slow state: 6; unknown runs: 2, with slow state: 2 (E below 800 MHz for 3+ samples)`
  - counts: `runs with flags: 10; mixed arms: 1`; flags table rows: 10
  - python recompute on the synthetic tree: 21 runs, skipped ['0008-h-r1', '0020-s-r1', '0021-t-r1']; differences vs copy: none

### 1 W4b per-run comparison (o = original, c = copy CSV, p = python recompute)

| run | arm | orig blocking | copy env | copy mode | expected | onset_s o/c/p | slow_pct o/c/p | span_s o/c/p | fg o ; c ; p | pcvar | precise | ms1 | flags | ok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1541-cold-d0 | cold-d0 | False | False | spin | spin | -/-/- | 0/0/0 | 91/91/91 | 1/0 ; 1/0 ; 1/0 | False | 0 | 0 | - | yes |
| 1542-d0-r1 | d0 | False | False | spin | spin | 93/93/93 | 22/22/22 | 117/117/117 | 1/0 ; 1/0 ; 1/0 | False | 0 | 0 | - | yes |
| 1545-B-r1 | B | False | False | spin | spin | 94/94/94 | 19/19/19 | 115/115/115 | 1/0 ; 1/0 ; 1/0 | False | 0 | 0 | - | yes |
| 1547-d3-r1 | d3 | False | False | spin | spin | 76/76/76 | 35/35/35 | 115/115/115 | 1/0 ; 1/0 ; 1/0 | False | 0 | 0 | - | yes |
| 1549-d11t-r1 | d11t | True | True | blocking | blocking | 61/61/61 | 42/42/42 | 113/113/113 | 1/0 ; 1/0 ; 1/0 | False | 0 | 1 | - | yes |
| 1551-B-r2 | B | False | False | spin | spin | 1/1/1 | 32/32/32 | 113/113/113 | 1/0 ; 1/0 ; 1/0 | False | 0 | 0 | - | yes |
| 1553-d3-r2 | d3 | False | False | spin | spin | 84/84/84 | 26/26/26 | 113/113/113 | 1/0 ; 1/0 ; 1/0 | False | 0 | 0 | - | yes |
| 1556-d11t-r2 | d11t | True | True | blocking | blocking | 63/63/63 | 46/46/46 | 114/114/114 | 1/0 ; 1/0 ; 1/0 | False | 0 | 1 | - | yes |
| 1558-d0-r2 | d0 | False | False | spin | spin | 72/72/72 | 37/37/37 | 114/114/114 | 1/0 ; 1/0 ; 1/0 | False | 0 | 0 | - | yes |
| 1600-d3-r3 | d3 | False | False | spin | spin | 54/54/54 | 52/52/52 | 113/113/113 | 1/0 ; 1/0 ; 1/0 | False | 0 | 0 | - | yes |
| 1602-d11t-r3 | d11t | True | True | blocking | blocking | 1/1/1 | 81/81/81 | 113/113/113 | 1/0 ; 1/0 ; 1/0 | False | 0 | 1 | - | yes |
| 1604-d0-r3 | d0 | False | False | spin | spin | 2/2/2 | 90/90/90 | 114/114/114 | 1/0 ; 1/0 ; 1/0 | False | 0 | 0 | - | yes |
| 1606-B-r3 | B | False | False | spin | spin | 4/4/4 | 97/97/97 | 114/114/114 | 1/0 ; 1/0 ; 1/0 | False | 0 | 0 | - | yes |
| 1608-d11t-r4 | d11t | True | True | blocking | blocking | 1/1/1 | 85/85/85 | 113/113/113 | 1/0 ; 1/0 ; 1/0 | False | 0 | 1 | - | yes |
| 1611-d0-r4 | d0 | False | False | spin | spin | 4/4/4 | 96/96/96 | 113/113/113 | 1/0 ; 1/0 ; 1/0 | False | 0 | 0 | - | yes |
| 1613-B-r4 | B | False | False | spin | spin | 3/3/3 | 90/90/90 | 114/114/114 | 1/0 ; 1/0 ; 1/0 | False | 0 | 0 | - | yes |
| 1615-d3-r4 | d3 | False | False | spin | spin | 1/1/1 | 93/93/93 | 113/113/113 | 1/0 ; 1/0 ; 1/0 | False | 0 | 0 | - | yes |

Copy arm table (parsed from the copy's text output):

| matrix | arm | runs | mode | slow_runs | mean_slow_pct | mean_onset_s | note |
|---|---|---|---|---|---|---|---|
| 20261122-1541 | B | 4 | spin | 4 | 59.6 | 25 | - |
| 20261122-1541 | cold-d0 | 1 | spin | 0 | 0 | - | - |
| 20261122-1541 | d0 | 4 | spin | 4 | 61.3 | 43 | - |
| 20261122-1541 | d11t | 4 | blocking | 4 | 63.4 | 31 | - |
| 20261122-1541 | d3 | 4 | spin | 4 | 51.6 | 54 | - |

### 2 W5 per-run comparison (o = original, c = copy CSV, p = python recompute)

| run | arm | orig blocking | copy env | copy mode | expected | onset_s o/c/p | slow_pct o/c/p | span_s o/c/p | fg o ; c ; p | pcvar | precise | ms1 | flags | ok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1756-cold-base | cold-base | False | False | spin | spin | -/-/- | 0/0/0 | 91/91/91 | 1/0 ; 1/0 ; 1/0 | False | 0 | 0 | - | yes |
| 1757-base-r1 | base | False | False | spin | spin | 87/87/87 | 13/13/13 | 122/122/122 | 1/0 ; 1/0 ; 1/0 | False | 0 | 0 | - | yes |
| 1800-s0-r1 | s0 | False | False | spin | spin | 40/40/40 | 50/50/50 | 113/113/113 | 1/0 ; 1/0 ; 1/0 | False | 0 | 0 | - | yes |
| 1802-d11-r1 | d11 | False | False | spin | spin | 6/6/6 | 68/68/68 | 113/113/113 | 1/0 ; 1/0 ; 1/0 | False | 0 | 1 | - | yes |
| 1804-d11t-r1 | d11t | True | True | blocking | blocking | 13/13/13 | 66/66/66 | 113/113/113 | 1/0 ; 1/0 ; 1/0 | False | 0 | 1 | - | yes |
| 1806-d11p-r1 | d11p | False | False | precise | precise | 3/3/3 | 71/71/71 | 113/113/113 | 1/0 ; 1/0 ; 1/0 | True | 1 | 1 | - | yes |
| 1808-s0-r2 | s0 | False | False | spin | spin | 21/21/21 | 69/69/69 | 113/113/113 | 1/0 ; 1/0 ; 1/0 | False | 0 | 0 | - | yes |
| 1810-d11-r2 | d11 | False | False | spin | spin | 35/35/35 | 58/58/58 | 113/113/113 | 1/0 ; 1/0 ; 1/0 | False | 0 | 1 | - | yes |
| 1813-d11t-r2 | d11t | True | True | blocking | blocking | 1/1/1 | 62/62/62 | 113/113/113 | 1/0 ; 1/0 ; 1/0 | False | 0 | 1 | - | yes |
| 1815-d11p-r2 | d11p | False | False | precise | precise | 2/2/2 | 70/70/70 | 113/113/113 | 1/0 ; 1/0 ; 1/0 | True | 1 | 1 | - | yes |
| 1817-base-r2 | base | False | False | spin | spin | 4/4/4 | 78/78/78 | 113/113/113 | 1/0 ; 1/0 ; 1/0 | False | 0 | 0 | - | yes |
| 1819-d11-r3 | d11 | False | False | spin | spin | 2/2/2 | 70/70/70 | 113/113/113 | 1/0 ; 1/0 ; 1/0 | False | 0 | 1 | - | yes |
| 1821-d11t-r3 | d11t | True | True | blocking | blocking | 4/4/4 | 96/96/96 | 113/113/113 | 1/0 ; 1/0 ; 1/0 | False | 0 | 1 | - | yes |
| 1823-d11p-r3 | d11p | False | False | precise | precise | 2/2/2 | 80/80/80 | 113/113/113 | 1/0 ; 1/0 ; 1/0 | True | 1 | 1 | - | yes |
| 1825-base-r3 | base | False | False | spin | spin | 22/22/22 | 60/60/60 | 113/113/113 | 1/0 ; 1/0 ; 1/0 | False | 0 | 0 | - | yes |
| 1827-s0-r3 | s0 | False | False | spin | spin | 2/2/2 | 62/62/62 | 113/113/113 | 1/0 ; 1/0 ; 1/0 | False | 0 | 0 | - | yes |

Copy arm table (parsed from the copy's text output):

| matrix | arm | runs | mode | slow_runs | mean_slow_pct | mean_onset_s | note |
|---|---|---|---|---|---|---|---|
| 20261122-1756 | base | 3 | spin | 3 | 50.2 | 38 | - |
| 20261122-1756 | cold-base | 1 | spin | 0 | 0 | - | - |
| 20261122-1756 | d11 | 3 | spin | 3 | 65.3 | 14 | - |
| 20261122-1756 | d11p | 3 | precise | 3 | 73.5 | 2 | - |
| 20261122-1756 | d11t | 3 | blocking | 3 | 74.8 | 6 | - |
| 20261122-1756 | s0 | 3 | spin | 3 | 60.5 | 21 | - |

### Synthetic cases (matrix 20990101-0000)

| case | run | expected mode / flags | copy mode / flags | env | pcvar | precise | ms1 | onset/slow/span | arm | ok |
|---|---|---|---|---|---|---|---|---|---|---|
| (a) cvar on, game.log without precise line, env off | 0001-a-r1 | spin / precise_cvar_no_line | spin / precise_cvar_no_line | False | True | 0 | 1 | 2/70/113 | a | yes |
| (b) cvar on, game.log without precise line, env on | 0002-b-r1 | blocking / precise_cvar_no_line | blocking / precise_cvar_no_line | True | True | 0 | 1 | 2/70/113 | b | yes |
| (c) precise line present, no cvar, env off | 0003-c-r1 | precise / precise_line_no_cvar | precise / precise_line_no_cvar | False | False | 1 | 1 | 2/70/113 | c | yes |
| (d) env on + cvar + precise line | 0004-d-r1 | precise / env+precise | precise / env+precise | True | True | 1 | 1 | 2/70/113 | d | yes |
| (e) two precise lines (cvar on, env off) | 0005-e-r1 | precise / precise_lines>1 | precise / precise_lines>1 | False | True | 2 | 1 | 2/70/113 | e | yes |
| (f) no game.log, no --log_file, no cvar, env on | 0006-f-r1 | blocking / no_log | blocking / no_log | True | False | 0 | 0 | 4/78/113 | f | yes |
| (g) no game.log, no --log_file, cvar on, env off | 0007-g-r1 | unknown / no_log | unknown / no_log | False | True | 0 | 0 | 2/70/113 | g | yes |
| (h) ff_signal_epoch_s = 0 -> run skipped | 0008-h-r1 | skipped | absent | | | | | | | yes |
| (i) arm x run 1: spin | 0009-x-r1 | spin / - | spin / - | False | False | 0 | 0 | 4/78/113 | x | yes |
| (i) arm x run 2: precise -> arm x MIXED | 0010-x-r2 | precise / - | precise / - | False | True | 1 | 1 | 2/70/113 | x | yes |
| (j) cvar timer_queue_precise_wait=false (args + params.cvar), no precise line | 0011-j-r1 | spin / - | spin / - | False | False | 0 | 1 | 2/70/113 | j | yes |
| (k) no game.log in dir; --log_file=<absolute path> to a log with the line | 0012-k-r1 | precise / - | precise / - | False | True | 1 | 1 | 2/70/113 | k | yes |
| (l) no game.log in dir; --log_file="<relative path, quoted>" to a log with the line | 0013-l-r1 | precise / - | precise / - | False | True | 1 | 1 | 2/70/113 | l | yes |
| (m) no game.log; --log_file points to a missing file; env on | 0014-m-r1 | blocking / no_log | blocking / no_log | True | False | 0 | 0 | 4/78/113 | m | yes |
| (n) env_set {"REX_TIMER_WAIT_BLOCKING":"0"} (presence-only test => blocking) | 0015-n-r1 | blocking / - | blocking / - | True | False | 0 | 0 | 4/78/113 | n | yes |
| (o) env_set as a list ["REX_TIMER_WAIT_BLOCKING=1"] | 0016-o-r1 | blocking / - | blocking / - | True | False | 0 | 0 | 4/78/113 | o | yes |
| (p) args "--timer_queue_precise_wait" "false" as two tokens (regex false positive expected) | 0017-p-r1 | spin / precise_cvar_no_line | spin / precise_cvar_no_line | False | True | 0 | 0 | 4/78/113 | p | yes |
| (q) bare flag "--timer_queue_precise_wait" (no value) + precise line | 0018-q-r1 | precise / - | precise / - | False | True | 1 | 1 | 2/70/113 | q | yes |
| (r) no "tag" in run.json (arm from dir name); sys.csv without a slow state | 0019-r-r1 | spin / - | spin / - | False | False | 0 | 0 | -/0/91 | r | yes |
| (s) ff_signal_epoch_s key absent -> run skipped | 0020-s-r1 | skipped | absent | | | | | | | yes |
| (t) no sys.csv -> run skipped | 0021-t-r1 | skipped | absent | | | | | | | yes |
| (u) tag "Y-r1" (arm differs from u2 only by case) | 0022-Y-r1 | spin / - | spin / - | False | False | 0 | 0 | 4/78/113 | Y | yes |
| (u) tag "y-r2" | 0023-y-r2 | spin / - | spin / - | False | False | 0 | 0 | 4/78/113 | y | yes |
| (w) no game.log, no --log_file, cvar on AND env on -> unknown wins over blocking | 0024-w-r1 | unknown / no_log | unknown / no_log | True | True | 0 | 0 | 2/70/113 | w | yes |

Copy arm table for the synthetic matrix:

| matrix | arm | runs | mode | slow_runs | mean_slow_pct | mean_onset_s | note |
|---|---|---|---|---|---|---|---|
| 20990101-0000 | a | 1 | spin | 1 | 70.2 | 2 | - |
| 20990101-0000 | b | 1 | blocking | 1 | 70.2 | 2 | - |
| 20990101-0000 | c | 1 | precise | 1 | 70.2 | 2 | - |
| 20990101-0000 | d | 1 | precise | 1 | 70.2 | 2 | - |
| 20990101-0000 | e | 1 | precise | 1 | 70.2 | 2 | - |
| 20990101-0000 | f | 1 | blocking | 1 | 77.9 | 4 | - |
| 20990101-0000 | g | 1 | unknown | 1 | 70.2 | 2 | - |
| 20990101-0000 | j | 1 | spin | 1 | 70.2 | 2 | - |
| 20990101-0000 | k | 1 | precise | 1 | 70.2 | 2 | - |
| 20990101-0000 | l | 1 | precise | 1 | 70.2 | 2 | - |
| 20990101-0000 | m | 1 | blocking | 1 | 77.9 | 4 | - |
| 20990101-0000 | n | 1 | blocking | 1 | 77.9 | 4 | - |
| 20990101-0000 | o | 1 | blocking | 1 | 77.9 | 4 | - |
| 20990101-0000 | p | 1 | spin | 1 | 77.9 | 4 | - |
| 20990101-0000 | q | 1 | precise | 1 | 70.2 | 2 | - |
| 20990101-0000 | r | 1 | spin | 0 | 0 | - | - |
| 20990101-0000 | w | 1 | unknown | 1 | 70.2 | 2 | - |
| 20990101-0000 | x | 2 | spin/precise | 2 | 74 | 3 | MIXED |
| 20990101-0000 | Y | 2 | spin | 2 | 77.9 | 4 | - |

## Appendix A: column-width probe (synth-long.txt, first lines)

```text

matrix        run          arm                                                                                                                                          mode   env pcvar precise ms1 onset_s slow_pct span_s fg  flags
------        ---          ---                                                                                                                                          ----   --- ----- ------- --- ------- -------- ------ --  -----
20990101-0001 0001-long-r1 LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL spin False  True       0   1 2             70    113 1/0 precise_cvar...
20990101-0001 0002-n-r1    n                                                                                                                                            spin False False       0   0 4             78    113 1/0

```

## Appendix B: probe.ps1 output (Windows PowerShell 5.1)

```text
short csv row: missing field is null: True; passes the -ne '' filter: True; [double] of it: 0
[math]::Round(2.5,0)=2 [math]::Round(3.5,0)=4 [math]::Round(0.25,1)=0.2
pcvar regex on '--timer_queue_precise_wait=true' -> True
pcvar regex on '--timer_queue_precise_wait=TRUE' -> True
pcvar regex on '--timer_queue_precise_wait=false' -> False
pcvar regex on '--timer_queue_precise_wait false' -> True
pcvar regex on '--timer_queue_precise_wait=yes' -> False
pcvar regex on '--timer_queue_precise_wait=on' -> False
pcvar regex on '--no_timer_queue_precise_wait' -> True
pcvar regex on '--timer_queue_precise_wait=true,x' -> False
Group-Object m, a on arms 'Y','y' -> groups: 1
ConvertTo-Json of params.cvar-like hashtable: @{timer_queue_precise_wait=True}
de-DE culture: ConvertTo-Csv of 13.5 -> "13,5"; string interpolation -> 13.5
```

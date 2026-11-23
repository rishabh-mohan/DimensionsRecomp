# T-std read-out kit (Agent 7, task #14)

One command per window gives a short markdown and a json read-out of any bench/agent8 run-matrix folder (W6-W10 tonight). It is read-only on the matrix folder and writes only the `-o` and `--json` files.

## Command

```powershell
if (Test-Path perf-notes/WINDOW-HOLD.txt) { "HOLD PRESENT - stopping"; exit 1 }
(Get-Process -Id $PID).PriorityClass='BelowNormal'
python -B build\agent7\w4b-noise\readout.py build\agent8\matrix\<dir> -o <out>.md --json <out>.json
```

- The `-o` and `--json` paths can go anywhere you own; the kit only reads the matrix folder.
- It prints the header and the "Read-out" section, and writes the full markdown to `-o`. Without `-o` it prints the whole markdown.
- It lowers its own priority to Below Normal. It runs on one thread with the stdlib only. Run one window at a time.
- Options:
  - `--ref ARM`: override the ref. The default is matrix.json's arm with `"ref": true`, else `"reference"`, else the first arm.
  - `--overlay NAME --rounds 1,2`: use when G11 is MIXED; the G11 line prints the exact flags to use.
  - `--drop RUN[,RUN]`: leave out runs by name (`1808-s0-r2` or `s0-r2`).
  - `--alpha 0.05`: the level of the round test and of the light-share guard.
  - `--putil 90 --emhz 600`: the host-flag thresholds.
  - `--light-ms MS`: the T split. The default is frames.json light_ms (4.5).
  - `--all`: keep runs whose timing is not valid.
  - `--normal-priority`: don't lower the priority (the default is Below Normal).

## What it reports

- **Kept runs:** scored runs with valid timing that are not excluded and have a scored frame window. The cold run, invalid-timing runs and excluded runs are left out, as in W4b and W5. Every left-out run is listed with its reason. Any n per arm and any number of rounds work.
- **Primary result:** T-std and B-block T-std side by side. Bold marks the one that applies.
  - The round test is the nested F test of the B-block round terms on median ms: F(rounds - 1, runs - arms - rounds + 1).
  - If p < 0.05, **B-block T-std** applies, with df = runs - arms - rounds + 1. Otherwise **T-std** applies, with df = runs - arms.
  - With one round, T-std applies.
  - The text says so, and adds a note if fps disagrees.
- **Guards** (as in RESULTS.md):
  - (a) The light share per arm, with a one-way F. If p < 0.05 it warns and adds the T-light and T-heavy rows.
  - (b) The raw GM deltas with the pooled CI. For each arm, "agrees" when the raw CI overlaps the primary's CI, else CONTRADICTS.
  - (c) The host-flag list: sys.json window P util >= 90 and E-core MHz < 600. Each flagged run gets its leave-one-out residual on median ms.
- **G11 power overlay:** the overlay, scheme, AC and saver per run, from the sys.json window (run.json's copy is the fallback).
  - **OK** means one overlay, one scheme and one AC value in every run, with no change inside any window. The battery saver is listed but is not part of the rule: a saver change appears in the line ("changed inside the window") while the status stays OK.
  - **MIXED** means the overlay, scheme or AC differs between runs or changes inside a window. If some round has every arm on one unchanged overlay, the line prints the `--overlay X --rounds a,b` that reads only those rounds; otherwise it says that no round qualifies.
  - **PARTIAL** means some runs have no power data (they are listed). **NO DATA** means no run has any, so G11 is not checked.
  - If the overlay is not best_efficiency (W5's), compare arms within the window only.
- Tables: the tails (p99, 1 % low), the median deltas (the summary.md form) and a per-run table (kept or why not, raw and T-std values, light share, P util, E MHz, flag, overlay).
- The json has every number: methods, round_test (F, df, p, b, terms_pct), decision, guards, g11 and the runs.

## Reading a window in the morning

1. Header: the kept count and the left-out list, the G11 line, and any notes. Notes include rounds without every arm and `--rounds` or `--drop` values that match no run.
2. Read-out: the primary and why; the median ms and fps cells per arm (`*` = the CI excludes 0); the count of `*` expected by chance.
3. Guards line: (a) OK or WARNING, (b) agrees or CONTRADICTS, (c) the flagged runs.
4. G11 MIXED: rerun with the printed `--overlay ... --rounds ...`. G11 with another overlay: compare within the window only.
5. Choosing repeats for later windows: see [REPEATS.md](REPEATS.md) (`repeats.py`).

## Regression and self-test

```powershell
(Get-Process -Id $PID).PriorityClass='BelowNormal'; python -B build\agent7\w4b-noise\test_noise_methods.py
```

- The self-test covers noise_methods.py, readout.py and repeats.py on synthetic data, plus readout.py on W4b (`20261122-1541`) and W5 (`20261122-1756`) against RESULTS.md.
- It checks every RESULTS.md row the kit prints, character for character:
  - W4b: raw, T-std and B-block T-std on median ms and fps, plus the median-delta rows;
  - W5: also T-std p99 and 1 % low;
  - the decisions (W4b B-block T-std, W5 T-std), the light-share F, hT_ref, the flagged runs with their residuals and flag rows, the W5 B-block p99 CI of d11t, guard b and G11.
- `--no-regression` skips the matrix folders.
- One difference in convention: RESULTS.md's "rounds 2-4 have median ms 3.1-4.1 % below round 1" (W4b) is 100 |b| on ln(value). The kit prints 100 (e^b - 1) = -4.0 / -3.1 / -3.9 %, from the same fit. The self-test checks both.
- RESULTS.md's other methods (L-ls, D-*, A, A2, C, B-norm, paired, trimmed) are not in the kit. They are sensitivity checks or were not chosen. Use noise_methods.py for them.

## Files (`build/agent7/w4b-noise/`)

- `readout.py`: the kit. It imports noise_methods.py and noise_case.py (both unchanged). noise_methods.py loads `bench/agent7/w4b_readout/w4b_readout.py` (the run loader).
- `repeats.py` and `REPEATS.md`: the half-width and minutes note for choosing repeats=<n>.
- `readout-w4b.md/json` and `readout-w5.md/json`: the kit's output on W4b and W5.
- `test_noise_methods.py`: the self-test.

# W4b read-out add-on (Agent 7, task #29; 10 s bins added in task #9)

This is an optional add-on to Agent 8's W4b read-out. Agent 8 decides whether to use it.

It applies the metric rule Agent 1 adopted after #26:

- p99, the 1% low and frames over 33 ms per minute, shown next to the mean fps;
- n >= 3 runs per arm;
- the slow state for every run.

It also adds a scene check against d0 and, at Agent 1's request (06:55), a background-load column per run. Since
task #9 it also gives each run's p99, 1% low, >33 ms/min and fps in 10 s bins of its scored window.

It is read-only. It writes only the files named by `-o` and `--json`, and no `__pycache__`. It changes nothing in the W4b chain, `bench/agent8` or `harness`.

## Commands

Timing matrix (the double-click W4b run), about 3 s plus the `timerq_slowstate.ps1` call (about 12 s in all on window 3):

    python bench\agent7\w4b_readout\w4b_readout.py build\agent8\matrix\<W4b dir> -o bench\agent7\w4b_readout\out-<W4b dir>.md --json bench\agent7\w4b_readout\out-<W4b dir>.json

Any `-o` / `--json` path works; the default above keeps the matrix dir untouched.

Options:

- `--all`: agent-launched or `-Quick` matrices are functional only. Add `--all` to keep those runs; the report then carries a FUNCTIONAL ONLY banner.
- `--no-timerq`: skips the call to Agent 11's `timerq_slowstate.ps1`. The slow column from `matrix_recheck.slow_state` stays.
- `--bg-ref DIR|none` (default: window 3, `build\agent8\matrix\20261122-0013`), `--bg-ref-cores X`, `--bg-margin 1.0`, `--sat-busy 0.97`: the background reference and flags (below).
- `--scene-floor 0.015`, `--scene-factor 2.0`: the scene threshold (below).
- `--bin-s 10`: the bin length of the per-run bins, in seconds of summed frame time.

Self-test (14 tests, about 3 s):

    python bench\agent7\w4b_readout\test_w4b_readout.py

Set `W4B_SKIP_PS=1` to skip the PowerShell `timerq_slowstate.ps1` test.

## What it reports

- **Per run, over the runner's own scored window** (`frames.json` `first_row` and `rows`): fps, p50, p99, the 1% low, >33 ms/min, the window length, and a check against `frames.json` and `results.csv`.
- **Per arm:** the median and the min..max across the kept runs. An arm with fewer than 3 kept runs is marked `n<3!`.
- **Deltas against d0:** for each metric, `better` or `worse` only when every run lies outside d0's range, otherwise `overlap`. There is also a per-round paired fps delta.
- **10 s bins (task #9):** four tables (fps, p99 ms, 1% low fps, >33 ms/min with the count in brackets). Each has one row per run with a window, one column per bin, and the whole-window value last. Each arm then gets a median row over its kept runs.
  - Bins are consecutive 10 s of summed frame time from the start of the scored window, over the same frames as the Runs table.
  - A frame belongs to the bin in which it ends.
  - A last part shorter than half a bin is merged into the bin before it, so a 50.01 s window gives 5 bins.
  - Per bin, the metrics are defined as for the whole window. The 1% low uses the slowest max(1, n // 100) frames of the bin.
  - The `--json` output has every bin with its start and end (`runs[].stat_bins`) and the arm medians (`bins.arms`).
- **Scene check:** the time-weighted distance between each run's draws per frame (from `perf.csv` `draw_calls`) and the pooled d0 windows. The runner's phase flag is shown next to it (window 3 predates it).
  - A run is flagged `SCENE?` above max(0.015, 2 x the largest leave-one-out distance among the d0 runs).
  - Calibration on tonight's matrices: runs in the same scene differ by 0.000-0.005. Window 3's light-phase run `0025-d11-r1` sits at 0.036 (draws 218 vs 226, 294.6 fps), and the unscored cold runs at 0.016-0.019.
  - Native runs (`native-frames.csv`) have no guest draw counts, so they are not compared.
- **Slow state:**
  - `matrix_recheck.slow_state`, imported read-only. Its value is the onset / the share of the window, with `!` when the slow state is in the window.
  - `timerq_slowstate.ps1`, run read-only as a subprocess.
- **Background load** (system CPU minus the game's CPU over the scored window):
  - system = logical CPUs x min(1, `cpu_util_pct` / `cpu_perf_pct`) per `sys.csv` sample in the window; game = the slope of `proc.csv` `cpu_s`. The cell is the median (p90; median busy %). A `game cores` column sits beside it (`~` = `run.json` `window_cpu_cores_mean`, used where `proc.csv` doesn't cover the window).
  - `SAT`: median busy share >= 0.97. The background value is then only a floor (`>=`): more load (Defender) can't raise it, it takes CPU from the game instead. A CPU SATURATED banner says so.
  - `BG+`: not SAT, and background > reference + 1.0 cores.
  - Reference: `--bg-ref-cores`, else the median of the unsaturated scored runs in `--bg-ref`, else the median of this matrix's own unsaturated scored runs.
  - **Window 3 has no `sys.csv` in any of its 19 runs**, so it can't give the reference Agent 1 asked for. The report says so and lists window 3's game cores per arm instead: d0 3.43, base 3.42, d11 3.47, n0 2.33.
  - Every in-game window with `sys.csv` tonight was saturated: 20 runs, 03:30-06:57, busy 0.99-1.00, except `0336-cold-d0` at 0.92.
- **Repeated tables:** the arm and delta tables are repeated without the kept runs that have any of these:
  - the slow state in the window;
  - a scene flag;
  - a BG+ flag;
  - a SAT flag (unless every kept run is SAT).

## Outputs

Window 3 (`20261122-0013`): `out-0013.md` / `.json`. Re-run at 13:31 on 2026-11-22 (task #9) with the bins added; every other number is unchanged.

- 19 of 19 runs agree with `frames.json` and `results.csv`.
- Arm fps match `summary.md`: d0 162.857, base 160.802, d11 159.038, n0 143.217.
- `SCENE?` flags: `0025-d11-r1` and the two cold runs.
- No `sys.csv`, so there are no background values.
- Bins: 5 per scored run (50 s windows; the 50.01 s ones merge their 0.01 s tail into 40-50 s) and 3 per cold run (30 s).
  - p99 is 10.3-13.2 ms in every bin of every kept run except `0025-d11-r1` (the light-phase run), which has 7.1-7.6 ms.
  - Only one kept run has a frame over 33 ms: `0018-d0-r1`, one frame in 40-50 s.
  - The first bin is the slowest in 9 of the 12 d0/base/d11 runs. The d0 median is 158.3 fps in 0-10 s and 163.6-165.6 fps after.

W4b `-Quick` dry run (`20261122-0342`, with `--all`): `out-0342.md` / `.json`. These were made before the bins were added.

- 5 of 5 runs agree.
- Arm fps: d0 172.107, B 100.348, d3 94.202, d0t 166.342.
- Every run is SAT, with background >= 9.6-10.3 cores.
- The slow-state onsets agree between `matrix_recheck` and timerq: 39, 29 and 37 s.

Zero-code runs (task #33, with `--all`; FUNCTIONAL ONLY and SAT, n=1 per arm, one arm per matrix): `out-0652.md` / `.json` (n2t), `out-0655.md` / `.json` (n3t) and `out-0657.md` / `.json` (n2s). These were made before the bins were added.

- Every run agrees with `frames.json` and `results.csv`.
- Arm fps match `summary.md`: n2t 136.7, n3t 122.9, n2s 123.6.
- Every run is SAT, with background >= 10.0-10.1 cores.
- The slow state is in the window for n3t (onset 100 s) and n2s (79 s), not for n2t.
- No scene check: these are native frames.

`zero_code_bins.py` writes `zero-code-bins.txt`. For each zero-code run it gives:

- 10 s bins of the scored window: fps, frames >33 ms, p99, E/P-core MHz and busy share;
- the window split before and after the slow-state onset;
- the means of the `native-frames.csv` columns over the >33 ms frames and over the rest.

Run it (read-only, about 2 s):

    python -B bench\agent7\w4b_readout\zero_code_bins.py | Out-File -Encoding ascii bench\agent7\w4b_readout\zero-code-bins.txt

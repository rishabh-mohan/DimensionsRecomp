# Task #6 (was #30): noise methods for W4b's +-19.6 % band (Agent 7)

Designed with file tools only, 16:49-17:05. Everything below runs after Agent 1's 'go': it is read-only, takes about 10 s and uses one process. **Results: [RESULTS.md](RESULTS.md)** (19:31-20:15). The methods added after 'go' are listed under "Added after 'go'" below.

## What makes the band

- **The band.** W4b's +-19.6 % is summary.md's noise band: (max - min) / median of d0's four run medians of the frame time, 3.069..3.734 ms. On fps the same rule gives 23.6 % (213.9..270.4 fps).
- **The scene doesn't change.** Each scored W4b window has a light part and a heavy part, but the guest content is the same in both. Every row I read in `1542-d0-r1/perf.csv` has draw_calls 226, vertices_processed 1022 and pipeline hits 7.
- **Only the host timing changes.** Frames of about 3 ms (buffer_queue_depth alternating 0 / 8) become frames of about 8 ms (depth mostly 8).
- **The heavy part is Agent 11's slow state.** In `1542-d0-r1/sys.csv`:
  - e_eff_mhz falls from about 1500 to about 550 MHz at 15:44:33, 32 s into the window, and stays there to the end;
  - e_util_pct is fixed at 33.33 and p_eff_mhz stays at about 1946;
  - frames.json's light share per 10 s goes 0.94, 0.95, 0.96, 0.47, 0.40;
  - every sys.csv row has the Balanced scheme with the best_efficiency overlay.
- **What sets each run's fps:** mostly when the slow state starts. Across all arms the runner's light_share (0.51-0.87) follows fps: d3-r3 has 0.513 and 198 fps, B-r1 has 0.870 and 317 fps. This noise is random per run, not per round.

## Methods

The script is [noise_methods.py](noise_methods.py) and the self-test is [test_noise_methods.py](test_noise_methods.py). The script uses w4b_readout.py's loaders and metric definitions over the runner's own scored windows. Kept runs are the 15 that are scored, valid timing and not excluded. The cold run and B-r2 (clang++ during the run, not valid timing) are left out; `--all` puts B-r2 back.

| id | method | per-run value |
|---|---|---|
| raw | the run-matrix numbers | whole window; median ms reproduces +-19.6 % |
| A-std | phase-matched, mixed to one fixed slow-state share | Each frame is labelled S (slow state from sys.csv: e_eff_mhz < 800 for >= 3 samples, Agent 11's rule) or F, with frames within 1.5 s of a state change left out. Then fps = (1 - h_ref) fps_F + h_ref fps_S, where h_ref is the median S time share of the kept runs. p50, p99 and 1% low are taken over the frames reweighted to the same mix. |
| A-heavy | heavy-phase (S) frames only | the task's "heavy-phase frames only" |
| A-light | fast-state (F) frames only | |
| A2-std / A2-heavy | A with a frame-time classifier (rolling median of 201 frames > 5 ms) | cross-check of the sys.csv split, with the A/A2 agreement per run |
| B (paired) | within-round deltas vs d0 | per arm: the median delta over rounds, the range and a 95 % t band; on raw, A-std and A-heavy |
| B-norm | each run divided by its round's geometric mean | gives a d0 band in summary.md's form |
| C-frames / C-bins | trimmed means | the 20 % trimmed mean frame time; the trimmed mean of the five 10 s bins (the middle 3) |

**Bands.** Each method reports three bands so they can be compared with +-19.6 %:

- the d0 band defined as in summary.md;
- the pooled within-arm CV of ln(value) (15 runs, df 11);
- the 95 % band for 4 vs 4 runs.

Each arm gets its median delta with a verdict against the d0 band, plus its geometric-mean delta with a pooled 95 % CI.

**Caveat (A).** Phase-matching hides any real effect an arm has on when the slow state starts. The report therefore lists h and the slow-state spans for every run, so an arm that shifts the onset is visible.

## Added after 'go' (19:32-20:10)

A fails on W4b (9 of 15 runs are in the slow state for the whole window). A2 does not work on W5 (no heavy phase). So these were added:

| id | per-run value |
|---|---|
| A2-light | A2's light frames only |
| T-std / T-light / T-heavy | Split at the runner's light threshold (frame < 4.5 ms = light, as frames.json's `share_lt_light`). T-std weights each light frame (1 - hT_ref)/T_light and each heavy frame hT_ref/T_heavy, where hT_ref is the median heavy-time share of the kept runs. fps, p50, p99 and 1 % low are taken over the reweighted frames. **This is the recommended method.** |
| L-ls | ANCOVA of ln(raw value) on the run's light share, with arm as a factor. The CI includes the covariate-difference term, and the band is taken on the adjusted ref values. |
| D-emhz / D-putil / D-emhz+putil / D-nongame | The same ANCOVA on sys.json window covariates: E-core MHz, P util, non-game CPUs (`--cpus 12`). `cov_info` gives each covariate's per-arm means and one-way F, so an arm-affected covariate (cores, F = 8.1 in W5) is visible. |
| B-norm T-std, B paired T-std | B on the T-std values |
| B-block raw / A-heavy / T-std | The two-way model (arm + round dummies) through the same ANCOVA code, with df = runs - arms - rounds + 1. B-norm's CI uses df = runs - arms, which is too narrow. |

There are also two new scripts:

- `noise_case.py`: leave-one-out residuals per run and method from a report JSON, plus the host-state flag (sys.json P util >= 90 % and E MHz < 600). This is Agent 1's W5 noise case.
- `results_tables.py`: the per-method tables in results-tables.md.

Two checker subagents recomputed the numbers independently; see RESULTS.md, "Checks".

## After 'go'

1. Check `perf-notes/WINDOW-HOLD.txt`.
2. `python -B build\agent7\w4b-noise\test_noise_methods.py`
3. `python -B build\agent7\w4b-noise\noise_methods.py -o build\agent7\w4b-noise\report.md --json build\agent7\w4b-noise\report.json`
4. Run at most 2 read-only check subagents. One recomputes A on its own (the slow-state split and the mix); the other recomputes B and C. Both compare their numbers with report.json.
5. Write RESULTS.md with each arm's delta vs d0 and the band for each method, and the method W5's read-out should use. Then send it to Agent 8 and Agent 1.

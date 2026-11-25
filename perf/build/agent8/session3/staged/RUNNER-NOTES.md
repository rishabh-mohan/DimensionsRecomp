# Staged runner improvements (S3T-8 item 4, M8, 2026-11-25)

STAGED ONLY. Nothing in `bench/agent8/run/` was changed. These are copies; install is the Overseer's call.

## Files

| Staged file | Base (pinned original, sha256 prefix) | What |
|---|---|---|
| `run-matrix.ps1` (72370A1E737A3A34) | `bench/agent8/run/run-matrix.ps1` (1A522CDFE9DC36F8) | warm-up runs + new row columns |
| `frame_summary.py` (987E0EC03456D5DC) | `bench/agent8/run/frame_summary.py` (0A7D35873E88E50E) | tail counters, unrounded light share |
| `run-matrix.diff`, `frame_summary.diff` | | `git diff --no-index` original -> staged |
| `drivers/sys-csv.ps1`, `drivers/LdSys.cs`, `sys_summary.py`, `SAMPLER-NOTES.md` | E9.1 (see SAMPLER-NOTES.md) | per-process CPU/IO sampler, nongame_load flag |

## run-matrix.ps1

- New optional top-level matrix field `warmup_runs` (whole number 0-20, default 0), and `-WarmupRuns N` param (overrides the matrix; -1 = use matrix).
- Build-Plan: after the cold run(s), N **unscored full-length warm-up runs**, cycling over round 1's arm order so the last warm-up is the arm right before round 1's first arm (each arm gets the GPU warm before round 1 in turn). Tag `warm<j>-<arm>`, round 0.
- Plan output prints a `warm` line; estimate says `(1 cold, N warm-up)`.
- Run loop: header `WARM-UP run (unscored)`; row `scored = not (cold or warm)`; console `(warm-up)`; summary/flagged tables show `warm`.
- A warm-up run of the seed_arm runs unseeded (the seed is still taken on the first scored run).
- New appended row columns (end of row; readers using DictReader unaffected): `kind` (cold/warm/scored), `over8`, `over10`, `over16_7`, `frames_lt_light`. `light_share` now written with 15 dp (was 4).
- With `warmup_runs` absent/0 the plan is byte-identical to the original's.

## frame_summary.py

- New keys: `over_8ms`, `over_10ms`, `over_16_7ms` (frames > 8000 / 10000 / 16667 us), `frames_lt_light`.
- `share_lt_light` no longer rounded to 4 dp. All other keys identical.
- run-timing.ps1 copies the whole frames.json into run.json (`frames`), so no run-timing change is needed for the new keys.

## Tests done (offline; nothing launched)

- `test/test-plan.ps1` (AST harness, dot-sources bench common.ps1, dummy driver; does not contain the string run-matrix.ps1 on a command line):
  - parse errors 0.
  - no warm-up: staged plan + plan lines == original (diff 0; WC 17 runs / 39 min).
  - `warmup_runs 3` on the WC shape: 20 runs / 46 min; order cold-s0, warm1-win3, warm2-c1np, warm3-p2fc, s0-r1, ...
  - W10 shape + `warmup_runs 2`: 15 runs / 35 min.
  - `-WarmupRuns 5` overrides the matrix value.
  - `warmup_runs 2.5` -> rejected "warmup_runs must be a whole number 0-20" (original rejects the field as unknown).
- frame_summary.py on 2 real runs (`build/agent8/matrix/20261123-0451/runs/0528-d11t-r6`, `0526-d11-r6`): every old key identical except share_lt_light (0.975295827... vs 0.9753); frames_lt_light 18792; over_8/10/16.7 = 0.

**Untested** (needs a real run): run-loop row writing for warm rows, summary table rendering, matrix_recheck on new rows.

## Caveats

- run-timing's `light_share_high` (share_lt_light >= 0.6) can flip only for values in [0.59995, 0.6) because of the unrounding.
- `matrix_recheck.py` labels every unscored row "unscored (cold)", warm rows included (cosmetic).
- Under the launcher, `-Repeats` overrides per-arm repeats and `-ColdShared` is always on; `warmup_runs` is a matrix top-level key and run-night.ps1 does not whitelist keys, so it works through the launcher after install.

## Not staged (proposal only)

- `Execution complete` exit-sequence classification as INFO: it lives in `harness/route-report.ps1` L204-207 and Agent 6's per-run check, not in the runner. Owner's call; not edited.

## Install (only when no launcher / run-matrix is running)

1. Confirm no `run-night.ps1` / run-matrix process and no window in progress.
2. Check the base hashes above still match `bench/agent8/run/*` (else rebase the diffs).
3. Copy the staged files over `bench/agent8/run/` (+ `drivers/`). The launcher re-pins at its next start.
4. Restage any planned windows with `build/agent8/w-followup/stage-window.ps1 -PlanOnly` (pins/fingerprints change).

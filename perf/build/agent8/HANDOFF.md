# Agent 8 handoff

Written 2026-11-23 ~07:40, before the project pause. Agent 8 ran the timing-matrix harness and read out the timed windows. All paths are workspace-relative.

## State

- **Idle.** None of my builds, timed runs, subagents or background jobs are running. Nothing is staged and waiting for a window.
- **All windows run so far are read out:**
  - W6 and W4c: my formal read-outs (task #20).
  - W9 and W5b: Agent 7's read-outs. I recomputed them from results.csv and they agree, apart from one misread (open item 3).
  - W4b and W5: read out on Nov 22 (`build/agent8/readout/w4b/`, `build/agent8/readout/w5/`).
- **The runner changed this morning.** Agent 5's SCRNSAVE.EXE fix edited `bench/agent8/run/run-matrix.ps1`: one hunk at L417-419, sha256 FEDCEB13… → 1A522CDF…. I reviewed it and it is OK; Agent 5's 45/45 tests pass.
- **No re-pin is needed for the runner change.** The launcher's `bench/agent5/launch/status/pins.txt` (L14) still lists FEDCEB13… from its 23:47 start, but nothing reads that file back. Each launcher start re-hashes the pinned files and rewrites pins.txt (`bench/agent5/launch/run-night.ps1` L967, L973). Its "any change refuses the next window" rule applies within one launcher run. Agent 5 pointed this out, and I checked the code.

## Results to carry forward

| window | folders in `build/agent8/matrix/` | read-out | answer |
|---|---|---|---|
| W6: upload path on the S4b bin | 20261123-0009 + 20261123-0313 | `build/agent8/readout/w-followup/W6.md` | **p2fc's gain is solid:** median −10.3 % [−13.6, −6.9], fps +18 %, −0.25 core. C1 < 0 in 10/10 rounds, and the gain holds in every cut. **p2 and p2f: null.** **The pass-2 tail isn't p2fc's.** It is an episode at 03:25-03:41 that hit all arms (cause unknown), plus a host burst at 0352. p2fc had 0 frames over 16.7 ms. |
| W4c: codegen B repeat | 20261123-0239 | `build/agent8/readout/w-followup/W4c.md` | **No gain:** +2.6 % [−1.2, +6.5]. W4b's +6 % fps hint is refuted. B may be ~1 % slower (lead). |
| W9: #24 GPU-wait back-off | 20261123-0108 + 20261123-0401 | `build/agent7/readout/W9.md` (Agent 7). Check: `build/agent8/readout/w-followup/a7check/W9-W5b-check.md` | **CPU:** q125, q250 and q500 cut 0.62, 0.65 and 0.75 core vs off (2.51). **Timing:** the median-ms and fps CIs cross 0; the median-ms gain is significant only without round 1. |
| W5b: TimerQueue wait modes | 20261123-0155 + 20261123-0451 | `build/agent7/readout/W5b.md` (Agent 7), same check | **CPU:** d11t −0.22 and d11p −0.20 core vs d11 (2.55). **Timing:** null once the flagged runs are dropped. Agent 7 picks d11p, narrowly. |

### Leads and caveats from all windows

- **Round-1 bias.** In every window, the first scored run (the base arm's round 1) is that arm's fastest run, by +2 to +16 % fps.
  - The cause is GPU warm-up after the idle gap. For the first 5-13 min the GPU runs above its steady 832 MHz, which is its thermal limit.
  - Details: `W4c.md` and `W6.md`, section "Round 1 and warm-up bias".
- **GPU-limited host (lead).** At steady state the GPU sits at 97-100 % utilisation at 832 MHz. So a change that only saves CPU shows up as fewer cores rather than more fps.
- **Compare within one window only.** W4b and W5 ran on the best_efficiency overlay, before the Defender exclusion for `build/` was added (~23:16 Nov 22). The night windows ran on best_performance, after the exclusion.

## What I own

| path | what |
|---|---|
| `bench/agent8/run/run-matrix.ps1` | Matrix runner. It runs each arm × repeat, samples perf/sys/gpu/proc csv, and writes results.csv, summary.md, run.json and frames.json per folder. |
| `bench/agent8/run/common.ps1`, `run-timing.ps1`, `timing-env.ps1` | Shared helpers, single-run timing, the env allow-list. |
| `bench/agent8/run/drivers/` | Samplers: `sys-csv.ps1`, `thread-cpu.ps1`, `io-counters.ps1`, `pso-stats-at-end.ps1`, `LdSys.cs`. |
| `bench/agent8/run/frame_summary.py`, `sys_summary.py`, `boot_report.py` | Per-run summaries. results.csv `light_share` comes from frame_summary, at 3 dp. |
| `bench/agent8/run/gate_logdiff.py`, `matrix_recheck.py` | game.log diff gate; folder re-check. |
| `bench/agent8/run/winhelper.cs`, `recover-close.ps1`, `run_selftest.ps1`, `first-boot.ps1` | Window and close helpers, the self-test, first boot. |
| `bench/agent8/run/README.md` | Runner docs, including the proof-and-gates table. |
| `bench/agent8/run/matrix-*.json` | Matrix definitions: windows 3-9, plus the functional matrices. |
| `bench/agent8/RUN-WINDOW*.cmd`, `bench/agent8/RUN-TIMING-MATRIX.cmd` | Desktop launchers for W3-W6. From W6 on, the night windows ran through Agent 5's `bench/agent5/launch/`. |
| `build/agent8/matrix/` | All run folders (index below). |
| `build/agent8/readout/` | Read-outs: `w4b/`, `w5/`, `w-followup/` (W6, W4c, audit, xcheck, a7check), `tstd-xcheck/`, plus the dry-run and staging read-outs. |
| `build/agent8/w-followup/` | `PROPOSAL.md` (the overnight plan, rev 22:35), `stage-window.ps1`, and the window drafts for 4c, 5b, 8a, 8a4 and 9. |
| `build/agent8/w6-stage/`, `build/agent8/w6pre4b/` | W6 staging. |
| `build/agent8/w8w9/ENV-KEYS-F1.txt` | Env keys for W8/W9. Agent 7's W8b draft uses it. |
| `perf-notes/agent8-window3.md` | Main working notes, W3 onward. The other `perf-notes/agent8-*.md` files are session-1 notes. |

Session-1 runtime bench work is inactive: the other folders in `bench/agent8/` (atomics, journal, profiler, …), `bench/agent8/RESULTS-runtime.md`, and the other folders in `build/agent8/` (bench, bin, db, …).

## Matrix folder index (`build/agent8/matrix/`)

| folder | content | rows |
|---|---|---|
| 20261121-2232 | Quiet window 1: baseline vs devoff1 | 12 |
| 20261122-0013 | W3: devoff2 vs baseline, the ON bundles, native2 N0 | 19 |
| verify3, verify3b, verify3c | W3 verify runs | 2 each |
| 20261122-0336, 20261122-0342 | W4: B vs d0, d3 (partial) | 6, 5 |
| 20261122-1541 | W4b | 17 |
| 20261122-1756 | W5: S3d timer modes | 16 |
| 20261123-0009, 20261123-0313 | W6, passes 1 and 2 | 21, 21 |
| 20261123-0108, 20261123-0401 | W9, passes 1 and 2 | 21, 21 |
| 20261123-0155, 20261123-0451 | W5b, passes 1 and 2 | 19, 19 |
| 20261123-0239 | W4c | 13 |
| 20261122-0330, -0349, -0357, -0438, -0452, -0509, -0620, -0652, -0655, -0657; s3-n123-0205, s3-n2-0210 | Functional checks for other agents, not timing: timer blocking, codegen B, native uploads and 3D, shader dump, S4 invalidation | 1-4 |

## Open items

1. **Runner sha is now 1A522CDF…** (Agent 5's install, Nov 23).
   - No manual re-pin: the next launcher start pins the current files (see State).
   - `build/agent11/resume/facts-perfopt.md` L110 is up to date (fixed 08:15): "FEDCEB13 in pins.txt; 1A522CDFE9DC36F8 since the install".
   - Re-run the -PlanOnly staging (`build/agent8/w-followup/stage-window.ps1`) for any window on the day. The Nov 22 stage files predate the runner change.
2. **Monday day session** (Agent 1's plan, `build/agent8/w-followup/PROPOSAL.md` §5, which also has the GO lines). Re-stage on the day.
   - **W8a** on native4b needs Agent 2's MANIFEST sha, Agent 4's re-pin, and a PASS on rpb0/rpm4 and s4b02/s4b05.
   - **W8a4** is its fallback. It needs the OK to count native4's r6 PASS as its functional cover.
   - **W8b** is Agent 7's draft, `build/agent7/s4-t1/matrix-w8b-draft.json`.
     - Gate: Agent 10 rates (b) SAFE, and F1 and W1 pass.
     - Its changed files are fingerprint inputs, so the baselines need re-pinning.
   - **W10** runs in the same session. **W7** comes Monday night at the earliest.
3. **W5b.md misread: fixed.**
   - L70 and L215 gave 0221-d11t-r5's window ng_t as 2.31. That is the game-cores column of `build/agent8/readout/w-followup/audit/audit.md` L257.
   - Agent 7's W5b.md rev 1 (sha256 6479A6117ED5EC32) now says 2.56 and lists the change in its S10. W9.md is also at rev 1 (8C58CAD1F6D44339). No conclusion changed.
4. **Harness improvements the night suggests:**
   - GPU warm-up: add discarded runs until gpu.csv shows the steady clock, and rotate the first arm across rounds.
   - Record per-process CPU and disk I/O in the matrix. The 03:25-03:41 episode hit every arm, and no recorded counter explains it.
   - Add a per-run quiet check. The launcher's quiet gate and valid_timing's build check only catch load at window start.
   - Classify a missing `Execution complete` as INFO. It is a benign exit race (2 NOTE runs in W5b).
   - Extend results.csv in two ways:
     - Add counts of frames over 8, 10 and 16.7 ms. Today it has only the longest frame and the > 33 ms count.
     - Store `light_share` at full precision. At 3 dp it differs by ±0.001 from Agent 7's frame counts, which also moves the one-way F.
5. **Follow-ups from the results:**
   - p2fc: verify-on was not timed (only Agent 3's functional gate-A run had it on), and there is no C1-only arm.
   - Test the GPU-limited lead.
   - Optional W9 extension: off / q500 / q750 / q1000. q500 saved the most CPU.
   - W9-1 0128-off-r2 logged one warning at shutdown, after its window: "Shutdown wedged past the close request; hard-exiting". Timing was not affected. Watch for repeats.

## Reproducing the read-outs

- **W6 / W4c:** the scripts are in `build/agent8/readout/w-followup/scripts/`.
  - `make_pool.py` builds `pool/W6`.
  - `run-mine.ps1` runs my paired read-out, `run-a7.ps1` runs Agent 7's method, and `run-var2.ps1` runs the variants.
  - The independent cross-check is in `xcheck/` (1620/1620 items agree), and the audit is in `audit/`.
- **W9 / W5b check:** run `python -B build/agent8/readout/w-followup/a7check/check_a7_w9w5b.py` from the workspace root (~10 s).
  - Its inputs are read-only. It writes `W9-W5b-check.md`.
  - Last run 07:34: 912 claims, 880 agree, 32 disagree, 0 sign flips. The 32 are 21 rounding ties, 9 light-share definition differences and 2 the misread.
  - That run read W9.md (07:01) and W5b.md (07:21), from before rev 1. To re-run on rev 1, first change the posted '2.31' in the W5b.md L70 and L215 hand claims to '2.56'.

## Rules that applied (keep them if resuming)

- Before every command, check that `perf-notes/WINDOW-HOLD.txt` doesn't exist. While it exists, a timed window is running: make no tool calls. Nothing may compile during a window.
- Only Agent 1 commits or pushes.
- Make timing claims only from CIs that exclude 0. Call fragile results leads.

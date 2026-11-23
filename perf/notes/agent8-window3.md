# Agent 8: timing windows 2 and 3 (task #16)

The user started both windows. Agent-launched runs, which run on hidden desktops, are functional only (`perf-notes/agent8-first-boot.md`). Window 1 died on a screen lock.

## Window 2: base vs devoff1 at the frame cap (`matrix-base-vs-devoff1.json`)

- **Arms:** base (`build/baseline-bin`, the reference) and r0 (`build/agent2/devoff1-bin`). Both ran at defaults, so both ran at the 60 fps cap.
- **Frame time:** the median of run medians was 16.661 ms for base and 16.665 ms for r0. At the cap, frame time cannot separate the builds.
- **CPU:** r0 used 0.088 more cores than base (paired median), and it used more in all 5 rounds.
- **Caveat:** runs 7-9 may have been perturbed.
- **What changed for window 3:**
  - It runs uncapped, so the frame rate follows the work per frame.
  - It adds a per-thread CPU metric, headroom, which also works at a cap.

## Window 3: plan

### What the user runs

- **The file:** double-click `bench/agent8/RUN-WINDOW3.cmd`, which takes no arguments. It runs `run-matrix.ps1 -Matrix run\matrix-window3.json -Only d0,base,d11,n0 -NoPrompt`, then `pause`.
- **Keep-awake:** window 1 died on a screen lock. The runner now holds `SetThreadExecutionState(ES_CONTINUOUS | ES_DISPLAY_REQUIRED)` for the whole matrix and releases it at the end.
- **Screensaver:** the runner warns when one is set. This PC has a `.scr` after 120 s, which the keep-awake request may not stop. The user turns it off for the window; the runner does not change user settings.
- **Output:** the newest `build/agent8/matrix/<yyyyMMdd-HHmm>/` folder, with results.csv, summary.md, runs\ and logs\.

### Arms

All arms run uncapped. They follow Agent 1's priority order; d12 was dropped so the matrix fits in 45 minutes.

| arm | bin | cvars beyond the runner's fixed set | role |
|---|---|---|---|
| d0 (ref) | `build/agent2/devoff2-bin` | `framerate_limit=0` | devoff2 (S2) at defaults |
| base | `build/baseline-bin` | `framerate_limit=0` | upstream baseline |
| d11 | devoff2-bin | `framerate_limit=0` plus Agent 11's R3 bundle: `host_timer_resolution_ms=1 host_timer_throttling_optout=true precise_guest_sleep=true wait_timeout_round_up=true cs_spin=true spinlock_pause_spin=true clock_lockfree=true tls_bounds_fix=true` | Agent 11's ON bundle |
| n0 | `build/agent2/native2-bin` | `native_settings_frontend=false native_fps_limit=0 framerate_limit=0`; frames from native-frames.csv | native N0 |
| d12 (dropped) | devoff2-bin | `framerate_limit=0` plus Agent 12's five io/log cvars | Agent 12's ON bundle |

The runner always adds `--audio_mute=true --pause_when_unfocused=false --native_settings_load=false --discord_rpc=false`. No arm runs the profiler.

### Order and time

- **19 runs.** First, one unscored cold run per bin (devoff2, baseline, native2). Then 4 rounds, rotated each round: `d0 base d11 n0 | base d11 n0 d0 | d11 n0 d0 base | n0 d0 base d11`.
  - Each round has one run of every arm, so paired deltas cancel slow drift.
- **Per run:** a 5 s settle, then a 35 s warm-up from the first frame, then a 50 s window and a 5 s cooldown.
  - The warm-up gets past the intro-to-title step at about 33 s.
  - The game stays on the title/attract loop with no input.
- **About 38 minutes.** The check runs took 112-116 s from launch to launch.
  - `-PlanOnly` says 49 minutes because it assumes a 20 s boot and a 35 s close. Real boots take 8-12 s and closes 1-5 s.

### Metrics

- **Frame stats per run:** from perf.csv (OFF builds) or native-frames.csv (n0): mean fps, median, p99, p99.9, and the number of frames over 33 ms and over 100 ms.
- **Headroom** (`drivers/thread-cpu.ps1`):
  - Every thread's busy % is its CPU time over the window divided by the window length.
  - **Headroom = 100 - the busiest thread's busy %.** Also recorded: total busy cores.
  - The GPU is sampled through NVML each second: utilisation, clocks, P-state, and power and thermal throttling.
  - Output: threads.csv, headroom.json and gpu.csv in the run dir.
- **Post-hoc:** `python bench/agent8/run/matrix_recheck.py <dir> --write` writes recheck.md. It has per-arm medians and ranges, per-round paired deltas (frame time and busiest-thread points), headroom and GPU utilisation.

### Why uncapped: the functional check runs (hidden desktop, 23:44-00:07)

| run | arm | fps | median ms | p99 ms | >33 ms | cores | busiest thread, busy % | headroom % | GPU util % |
|---|---|---|---|---|---|---|---|---|---|
| verify3b `2344-d0-r1` | d0 | 226.9 | 3.72 | 13.0 | 5 | 2.73 | Main XThread, 75.0 | 25.0 | 64 |
| verify3b `2346-n0-r1` | n0 | 101.3 | 9.20 | 30.3 | 35 | 1.96 | XThread5E50, 78.0 | 22.0 | 39 |
| verify3c `0003-base-r1` | base | 138.4 | 3.83 | 41.0 | 124 | 2.11 | XThread15E0C, 48.2 | 51.8 | 49 |
| verify3c `0005-d11-r1` | d11 | 141.7 | 3.80 | 40.8 | 151 | 2.25 | XThreadE9A4, 66.5 | 33.5 | 45 |

- **The headroom metric works.** It produced a result in all four runs, including the native one. d11's game.log has the line `Host timer resolution set to 1 ms (background opt-out on)`.
- **What limits d0 uncapped:**
  - Main XThread (75% busy) and GPU Commands (71%) run in step, while the GPU is at 64% and not pinned (1740 MHz, P0, no throttling).
  - So the rate is bound by the sync between the guest main thread and the command thread, not by the GPU.
- **Noise:**
  - On the hidden desktop, base and d11 have a fast median (about 3.8 ms) but a much lower mean rate, with long slow stretches. d11's 10 s bins swung between 81 and 220 fps and fell to 28-38 fps after its window.
  - On the user's desktop this should be calmer. The 4 paired rounds and headroom.json are the backstop. Agent 1 accepted uncapped at 00:09, with no 60 fps fallback.

### Runner fixes made for window 3 (23:37-00:03)

verify3 (23:34) had two PROBLEM runs. verify3b and verify3c, run after these fixes, were all OK.

1. **proc.csv writes** (`run-timing.ps1`, new `Add-ProcRow`).
   - The bug: `Add-Content` collided with the driver, which tails proc.csv. The two failures were "Stream was not readable" and "being used by another process".
   - The fix: rows are appended with `[IO.File]::AppendAllText`, which shares reads, with 40 retries 25 ms apart. A row that still fails is dropped with a warning instead of failing the run.
2. **NVML instead of nvidia-smi** (`drivers/thread-cpu.ps1`).
   - nvidia-smi `-lms -f` buffers 4 KB chunks, so its tail is lost when it is killed. It perturbed frame pacing.
   - Its orphaned processes kept the agent command's console handles open. One task hung for 6 minutes until I killed them by PID.
   - The driver now loads Agent 3's `harness/nvml.cs` (compiled once to `build/agent8/cache/LdNvml-*.dll`). It takes one sample per CPU sample and writes gpu.csv at the end.
3. **A helper renamed from `R` to `Rnd`.** PowerShell's built-in alias `r` (Invoke-History) took precedence over the function `R`, which crashed the driver.
4. **Keep-awake and the screensaver warning** (`run-matrix.ps1`), described above.

### Checks after the window

`build/agent8/scratch/post-window3.ps1` runs these, and only after Agent 1 ends the window:
- `matrix_recheck.py --write`, plus `--all` if any run is flagged as not valid timing;
- the d11 timer line in every d11 game.log;
- for every run: status, problems, game.log errors and warnings, headroom, GPU, and fps in 10 s bins.

Agent 1 gets one line per result: base, d11 and n0 against d0, as a fps % and as paired busiest-thread points.

## Window 3: results

Window 3 ran 00:13-01:16, 19/19 OK. Agent 8 analysed it at 01:24-01:33 from existing data only.
- Output: `build/agent8/matrix/20261122-0013/` (results.csv, summary.md, recheck.md from `matrix_recheck.py --write`).
- Per-run detail: `build/agent8/scratch/w3_threads.txt` (threads.csv, gpu.csv, timeline and frame histogram per run), `w3_switch.txt` (light/heavy phase per 10 s; game.log diff) and `post-window3.txt`.

### Scored runs (4 per arm)

| arm | median ms (min..max) | mean fps | p99 ms | cpu cores | top1 busy % | GPU util % |
|---|---|---|---|---|---|---|
| d0 (ref) | 7.067 (6.977..7.100) | 162.9 | 12.2 | 3.55 | 86.9 GPU Commands | 55 |
| base | 7.123 (7.101..7.155) | 160.8 | 12.3 | 3.51 | 87.5 GPU Commands | 54 |
| d11 | 7.135 (3.401..7.187) | 159.0 | 12.3 | 3.56 | 86.2 GPU Commands | 55 |
| n0 | 6.707 (6.555..6.875) | 143.2 | 11.3 | 2.43 | 75.9 Main XThread | 49 |

Deltas against d0 (recheck.md):
- **base:** median +0.8% (paired +0.07 ms, faster in 0 of 4 rounds), mean fps -1.3%: SLOWER.
- **d11:** median +1.0% (paired +0.08 ms, faster in 1 of 4 rounds; the one faster round is d11-r1, the light-state run below), mean fps -2.3%: within noise.
- **n0:** median -5.1% (paired -0.36 ms, faster in 4 of 4 rounds), BUT mean fps -12.1% (143 vs 163), -1.12 cores and top1 -10.9 points.

> [!WARNING]
> The frame times of the OFF builds are bimodal: about 30% of frames take under 4.5 ms and about 60% take 6-12 ms. The median lands on the slow cluster and hides the fast one. n0 has no frames under 4.5 ms, so its lower median does not mean more frames: use mean fps (or mean frame time) for OFF-vs-native comparisons.

### Per-thread busy % of one core (driver window, mean of the scored runs)

| thread | d0 | base | d11 r2-r4 | d11-r1 (light state) | n0 |
|---|---|---|---|---|---|
| Main XThread | 48.4 | 48.2 | ~49.4 | 38.2 | 75.7 (F8000024, also records native GPU work) |
| GPU Commands (F8000018) | 86.8 | 87.2 | ~86.4 | 82.1 | none (native path) |
| rex::thread::TimerQueue | 62.0 | 62.5 | ~61.7 | 60.4 | 52.4 |
| audio (Audio Worker + SDLAudio + XMA Decoder) | 6.1 | 6.0 | ~6.0 | 6.7 | 3.3 |
| sum, cores | 3.5 | 3.5 | 3.5 | 3.46 | 2.4 |
| GPU util % / graphics MHz / W | 55 / 1725 / 21.6 | 54 / 1716 / 21.6 | ~55 / ~1692 / ~21 | 40.6 / 1732 / 19.7 | 47.5 / 1740 / 17.5 |

The d11 r2-r4 columns are derived from the 4-run mean minus r1, so they are good to about ±0.1. The cold runs had no driver, so they have no thread or GPU data.

TimerQueue uses 52-62% of a core in every build, the largest thread outside the render path. That makes it a candidate for a separate look.

### The 2x split: game state, not clocks

The fast runs are cold-d0 (3.18 ms), cold-base (3.87 ms) and d11-r1 (3.40 ms). The other 11 OFF runs sit at about 7.1 ms.

1. **The split is real throughput, not a median flip.** d11-r1 averaged 294.6 fps, against 157-167 fps in the slow runs. 92% of its frames were under 4.5 ms, against about 30% in the slow runs.
2. **Clocks do not explain it.**
   - The GPU ran at P0, about 1732 MHz, in both states, and the slow state had the higher GPU util. Total CPU was the same (3.46 against 3.50 cores).
   - Per frame, the slow state costs 2x CPU: GPU Commands 2.8 to 5.4 ms, main 1.3 to 3.0 ms.
   - It also costs 2.4x GPU time per frame at the same clock (1.4 to 3.4 ms).
   - A slower CPU cannot raise GPU work per frame, so the guest is rendering a heavier scene.
3. **Every run has the same phase change (see `w3_switch.txt`).** n0 has it too.
   - Every run starts in a light title phase: 50-90% of frames under 4.5 ms.
   - 30-40 s after the first frame, every run with data past 40 s switches to the heavy state (about 30% light frames in the OFF builds, 0% in n0), except d11-r1.
   - d11-r1 switched to the light state instead (90% or more) and stayed there for 300 s.
4. **The cold runs measured early.** Their 30 s window starts about 13 s after the first frame (marks at runner t = 21-22 s), so it is mostly the light phase.
   - cold-base was 70% light until about 35 s and 30% after, so its median of 3.87 ms straddles the switch.
   - cold-d0 had only 46 s of frames and was still 80-90% light at the end, so its window held no heavy frames.
   - This is a window-placement artifact, not a different state.
5. **d11-r1 is the only real divergence, and game.log shows it.** Every other run, the cold runs included, logs 36 `INSTALL` lines, 34 of them `[krnl] NtCreateFile FAILED: path='d:\INSTALL#_#.DAT'` warnings. d11-r1 logs 2: it skipped the HDD install-package probe that every other run makes. Whether the probe runs at boot or at the switch has not been checked. Either way, the INSTALL count marks the divergent run. Toypad read/write traffic also differs (45 against 29 lines).
6. **Timing against the desk period (00:13-00:30).**
   - d11-r1 ran 00:25-00:30, inside the desk period. d0-r1 and base-r1 (00:18-00:25) did not diverge, and nothing after 00:30 did.
   - With one divergent run, the trigger is open: user input reaching the game's MnK input during the title, or a Toypad init race.
   - n0 is steady because all its windows start after its switch and it never diverged (0 of 5).
7. **GPU thermal throttling is a side effect, not the cause.** NVML SW thermal slowdown (0x20) appears only in OFF runs from 00:56 on: 87 C, minimum clock 1425 MHz, mean clock about 1% lower. n0 ran at 82 C with no throttle flags.

### Proposal for window 4

**Driver:** a 1 s `sys.csv`, with everything opened or compiled before the window, like LdNvml. Each row samples:
- `idle_s`, from GetLastInputInfo (seconds since the last user input), and `fg_game` (the foreground window's pid is the game's). These test the input hypothesis directly.
- Effective CPU MHz: PDH `\Processor Information(_Total)\% Processor Performance` times `Processor Frequency` (APERF/MPERF, so it includes turbo and throttling). Plus `% Processor Utility`, and P-core vs E-core means split by GetSystemCpuSetInformation EfficiencyClass.
- `\Thermal Zone Information(*)\% Passive Limit` (under 100 means passive throttling) and Temperature.

At window start and end, and whenever they change, it also records:
- the active power scheme and the effective overlay (PowerGetEffectiveOverlayScheme: best performance, balanced or best efficiency);
- AC power and battery saver (GetSystemPowerStatus).

**Runner:**
- Flag the light title state per run, using the INSTALL warning count and the share of frames under 4.5 ms in the window. Report flagged runs separately from the pairs.
- Start every window at least 60 s after the first frame, cold runs included.
- Keep hands off keyboard and mouse during runs.

## Window 4: plan (session 3, task #7)

### What the user runs

- **Window 4 is W4b** (Agent 1, 04:02; Agent 11 did not object by 04:08). Double-click `bench/agent8/RUN-WINDOW4B.cmd` on the unlocked desktop. It runs `run-matrix.ps1 -Matrix run\matrix-window4.json -Only d0,B,d3,d11t -Repeats 4 -ColdShared -NoPrompt`.
- Fallback W4a: `bench/agent8/RUN-WINDOW4.cmd` (`-Only d0,B,d3`, 3 cold runs + 5/5/4 repeats).
- Time: 17 runs. `-PlanOnly` says about 39 min; about 40-45 min of wall time.
- Before starting:
  - set the screensaver to (None) (at 02:55 it was `WPXSCR~1.SCR` after 120 s; the keep-awake request should hold it off, and sys.csv flags it if it starts);
  - plug in the charger;
  - close other programs;
  - leave the Windows power mode as it is, before and during the window (see "GO checks" below);
  - keep hands off until the window says "Press any key".
- At the end the window prints `Window 4b matrix finished (exit code N). Results: build\agent8\matrix\ (newest folder), summary.md`, then `Press any key to continue . . .`.
- Results: `build/agent8/matrix/<yyyyMMdd-HHmm>/summary.md` and results.csv. Then the read-out steps under "Window 4 read-out" below (matrix_recheck.py, Agent 11's slow-state scan before any fps).

### Arms

| arm | bin | runs | what it tests |
|---|---|---|---|
| d0 (ref, group w4) | devoff2-bin (MANIFEST B87DC2D2) | 5 + 1 cold | S2 baseline |
| B | devoffB-bin (MANIFEST 8709476FF4778768, exe C3F8686E, rexruntime 1C45C869 = devoff2's) | 5 + 1 cold | codegen B on the S2 snapshot: the primary pair is B vs d0 |
| d3 | devoff3-bin (MANIFEST B9C5175DA1904235, exe 2522D436, rexruntime D1D66AC3716835AC) | 4 + 1 cold | S3 host changes |
| d11t | devoff2-bin + window 3's d11 cvars (Agent 11's R3 bundle) + `REX_TIMER_WAIT_BLOCKING=1` | W4b only: 4, cold shared | Agent 11's TimerQueue change on top of the d11 bundle. Agent 1 (03:42): W4b runs d11t in place of d0t, and only if d11t's functional re-check (03:49, `matrix-s3-functional.json`) holds fps within noise of d0f and cuts TimerQueue CPU. The re-check cut TimerQueue to 0.3% (fps could not be judged: slow state); Agent 1 chose W4b at 04:02 |

W4b (`RUN-WINDOW4B.cmd`) runs `-Only d0,B,d3,d11t -Repeats 4 -ColdShared`: one unscored cold run on devoff2 shared by all bins, then 4 rounds in a Latin square (each arm once per round and once in each position), so d0, B, d3 and d11t get 4 runs each (17 runs). One shared cold run is enough here: every run copies its bin into a fresh run dir, so no game cache state carries over between runs; the game data are shared by all bins; and every window starts at least 60 s after the first frame. Check afterwards: each arm's round-1 run against its later rounds. The d0t arm (devoff2 + `REX_TIMER_WAIT_BLOCKING=1` only) stays in matrix-window4.json but is in neither variant.

Every arm uses the same frame source (perf.csv), runs uncapped (`framerate_limit=0`) with the `drivers/thread-cpu.ps1` driver, and logs sys.csv. The order is round-robin, rotated each round, after one unscored cold run per bin.

### Window placement

- Each warm run: 5 s settle, then a 55 s warm-up counted from the first-frame signal, then 50 s measured.
- Each cold run: the same 55 s warm-up, then 30 s measured.
- So every window starts at least 60 s after the first frame (`min_window_after_ff_s` 60, Agent 1's floor). That is past the light-to-heavy switch that window 3 saw at 30-40 s.
- The runner raises the warm-up when settle + warm-up (+ menu) is under the floor. After the run it computes `ff_to_window_s` (first-frame signal to the start mark) and flags `window_before_floor` when that is under 59.5 s.
- The first-frame tick is the tick at or after (sample time − 0.3 s). A sample taken late in its tick therefore cannot start the window early.

### Flags (run.json `flags_excluding`, `flags_info`, `excluded`)

**Excluding flags** (the run stays in results.csv but leaves the summary numbers):
- `light_phase`: fewer than 30 `INSTALL*.DAT` FAILED lines in all game*.log files. A normal boot has 34; window 3's light run d11-r1 had 0. The rule needs the boot lines to be present.
- `window_before_floor`.
- On the interactive desktop only:
  - `input_during_window`;
  - `not_foreground`: the game was foreground for more than 0% and less than 99% of the window;
  - `on_battery`, `battery_saver`, `power_change`, `desktop_not_default`, `screensaver`.

**Info flags** (notes only):
- `install_marker_lost`;
- `light_share_high`: at least 0.6 of the window's frames are under 4.5 ms;
- `ticks_skipped`;
- `build_procs_warmup`, `build_procs_window`;
- `never_foreground` (0% foreground, as on the hidden desktop);
- `sys_missing`;
- every other sys flag, and all sys flags on an agent's hidden desktop.

**Where flagged runs appear:**
- summary.md drops excluded runs from the numbers. It counts them in a `flagged` column and lists them under "Flagged runs".
- matrix_recheck.py drops them unless you pass `--keep-flagged`.

### Runner changes for window 4

- **run-timing.ps1:**
  - `-SysCsv` starts `drivers/sys-csv.ps1`, a 1 s sampler (LdSys.cs, compiled once). Afterwards `sys_summary.py` turns sys.csv into sys.json for the window.
  - The floor, the warm-up raise and `ff_to_window_s`.
  - The light block: INSTALL counts, plus the share of window frames under `-LightMs` from frame_summary.py, which also gives p95 now.
  - The flags.
  - Foreign crash dumps (another pid or another exe) are listed under `foreign_crash_dumps` instead of counting as a problem (caveat 2).
  - Get-BuildProcs now also catches clang++ and rexglue.
  - Late start mark (03:2x): when the measure-start mark lands late (a long runner pass), the end mark is now set from the actual start (`$endTick = $tick + $Seconds`), so the window keeps its full length; the "late by N s" note stays in run.json.
- **run-matrix.ps1:**
  - New keys `sys_csv`, `min_window_after_ff_s`, `cold_warmup_s` and `cold_measure_s`; the last three can also go under `quick`.
  - Measured estimate constants: warm boot 12 s, cold boot 25 s, close 5 s, post-processing 5 s (caveat 5).
  - Caveat 3 fixed: arms are filtered by repeats first, then rotated.
  - results.csv gains the columns `excluded`, `flags_excluding`, `flags_info`, `ff_to_window_s`, `light_share`, `install_dat_fail`, `light_phase`, `idle_min_s`, `fg_share` and `eff_mhz`.
  - summary.md gains a flagged count, a `flagged` column, Runs-table columns excl, ff->win, light and flags, and a "Flagged runs" table.
- **matrix_recheck.py:** `--keep-flagged`, ff->win, light and flags columns, and a "Flagged runs" table. 04:24: a `slow` column (Agent 11's slow-state rule on sys.csv) and `--drop-slow` / `--slow-emhz` / `--slow-rows`.
- **gate_logdiff.py:** the A/B game.log diff for the B gate (exit 0 pass, 1 fail).
- **common.ps1 (03:26):** `Get-WerFor` checks the process list first (23 ms) and asks WMI only when a WerFault process exists. The WMI query took 1-2 s on every 5th tick and sometimes far longer: see "Window 3 wall time" below.
- **`-ColdShared` (run-matrix.ps1):** one cold run for all bins (W4b).

### Checks before GO

- `-PlanOnly` (03:15):
  - W4a, `-Only d0,B,d3`: 17 runs (3 cold), about 39 min.
  - W4b, `-Only d0,B,d3,d0t -Repeats 4 -ColdShared`: 17 runs (1 cold), about 39 min.
  - d0t with a cold run per bin (`-Repeats 4`): 19 runs, about 44 min. Too long.
  - `-Quick`: 6 runs, about 7 min.
- `-PlanOnly` (03:46), W4b with d11t, `-Only d0,B,d3,d11t -Repeats 4 -ColdShared`: 17 runs (1 cold), about 39 min; rounds `d0 B d3 d11t | B d3 d11t d0 | d3 d11t d0 B | d11t d0 B d3`. d11t's cvars and env are printed as in the matrix.
- Self-test and `-Quick` dry run: see "Window 4: dry run" below.

### Window 3 wall time (runner stalls)

- Window 3 took 62.8 min against 49 planned.
- Where the time went (proc.csv): the runner's pass on every 5th tick (the dialog and WerFault checks) ran about 1 s long every time, and 35-61 s long a few times per run. For example, 0018-d0-r1 had stalls of 46, 40 and 50 s inside its window, so 175 s passed between its marks for a 50 s window.
- Window 3's runner had no catch-up, so every stall pushed back everything after it: 24.6 min in total over 19 runs (measure 965 s, warm-up 293 s, settle 197 s). Window 2 lost 3.2 min this way; tonight's hidden-desktop runs lost 0.3 min.
- The game itself was not affected: 0018-d0-r1's window had a 33.7 ms max frame. The window-3 numbers stand, because they are cut by seconds from perf.csv.
- Cause: `Get-WerFor`'s WMI query (`Win32_Process` with a Name filter). It took 1.05-2.14 s at 03:25 with the machine otherwise idle, and WMI can block far longer when it is busy. The window-text calls in the same pass (`GetWindowText`) do not send messages to the game.
- Fixes:
  - The loop now jumps to the current second after a long pass (`ticks_skipped`), so a stall no longer accumulates.
  - 03:26: `Get-WerFor` no longer queries WMI unless a WerFault process exists.

### B gate (session 3, hidden desktop, functional)

| run | bin | route | run dir (`build/agent3/runs/`) | result |
|---|---|---|---|---|
| dry | devoff2 | `b-gate-menus.txt` | `20261122-030135-bgate-dry` | PASS |
| A | devoff2 | `b-gate-menus.txt` (37 steps) | `20261122-030511-bgate-a` | exit 0, 37/37 steps, 108 warnings, 0 errors, WM_CLOSE 3.1 s |
| B | devoffB | the same | `20261122-030752-bgate-b` | exit 0, 37/37, 142 warnings, 0 errors, WM_CLOSE 0.83 s |
| long A | devoff2 | `b-gate-menus-long.txt` (54 steps, longer idle) | `20261122-031756-bgate-long-devoff2` | exit 0, 54/54, 142 warnings, 0 errors, WM_CLOSE 1.18 s |
| long B | devoffB | the same | `20261122-032150-bgate-long-devoffB` | exit 0, 54/54, 142 warnings, 0 errors, WM_CLOSE 4.31 s |

- **A vs B:**
  - `gate_logdiff.py` PASS. Agent 10's logdiff: NEW 0, and GONE only 4 Toypad info lines.
  - B had 34 more warnings: a third `INSTALL*.DAT` probe batch at 141.9 s. B left the front-end screen (220/534 → 218/222) by itself at perf 134.7 s; A stayed on it.
- **Tie-break (long route):** both builds leave the screen.
  - INSTALL batches, same counts in both: A 16.5 s (×34), 69.8 s (×68), 141 s (×34); B 15.1 s, 68.5 s, 137.1 s.
  - `gate_logdiff.py` PASS (new 0, gone 0). Agent 10's logdiff: NEW 0, GONE the same 4 Toypad info lines.
- **Verdict: PASS for B.** B's early exit in the first pair was run-to-run variation in an idle timer counted in frames (Agent 9: about 1,200 idle frames; A ran slower in its last 20 s). It was not a codegen change.
- Agent 3's find: after about 60 s idle the front end reaches a heavy 3D attract sequence (5-8k draws, 0.8-1.0M vertices, from about 170 s after the first frame). It has not been timed.

### Window 4: dry run (session 3, hidden desktop, functional only)

- **Runner self-test** (`bench/agent8/run/run_selftest.ps1`, fake exe, 03:27-03:30): 55 PASS, 0 FAIL (`build/agent8/scratch/selftest-0326.log`). It ran with the Get-WerFor fix, before the late-start edit; the late-start path was then exercised by the d0t pair and both dry runs below (no late marks occurred).
- **W4a `-Quick`** (`-Only d0,B,d3 -Quick -NoPrompt`, 03:36:31-03:42:39, `build/agent8/matrix/20261122-0336`): exit 0, 6/6 OK (3 cold + round 1). Every run: sys.csv and sys.json written, sys sampler exit 0, `ff_to_window_s` 19.99-20.03 (Quick floor 20), `ticks_skipped` 0, no build tools, no dumps, WM_CLOSE exits in 0.9-2.5 s. Flags: info only (`never_foreground` everywhere on the hidden desktop, `light_share_high` on 3 runs). matrix_recheck `--all --write` OK.
- **W4b `-Quick`** (`-Only d0,B,d3,d0t -Repeats 1 -ColdShared -Quick -NoPrompt`, 03:42:39-03:48:35, `build/agent8/matrix/20261122-0342`): exit 0, 5/5 OK: exactly one cold run (cold-d0), then d0, B, d3, d0t. d0t's run.json `env_set` is `REX_TIMER_WAIT_BLOCKING=1`. Same checks as W4a, all fine. Agent 2's S3d build overlapped cold-d0, d0-r1 and B-r1 (03:42-03:46): `build_procs_warmup`/`build_procs_window` were flagged as info, as designed on the hidden desktop (on the interactive desktop they make the run not valid timing). d3-r1 had `ticks_skipped` 1.
- The Quick numbers are not timing: 20 s windows at 20-40 s after the first frame sit on the title switch, and the two dry runs disagree with each other (B faster than d0 in W4a, slower in W4b). d3 was the slowest arm in both (61 and 94 fps against d0's 130 and 172); window 4 measures it properly.
- **The "SLOWER" verdicts for B and d3 in the 0336 and 0342 summaries are not results** (Agent 11, 04:08): they are slow-state artifacts. Agent 11's `timerq_slowstate.ps1` puts the slow-state onset (E-cores under 800 MHz for 3+ samples) at 27-39 s after the first frame in every warm Quick run (0339-0341, 0343-0346) and in cold-d3, i.e. inside the 20-40 s Quick windows, at a different time in each run; only cold-d0, cold-B and 0347-d0t-r1 stayed out of it.
- Expected wall time for the real window: about 39 min planned, about 43 min with boot jitter; the stall that cost window 3 24.6 min is fixed (see above).

### Timer arm checks (session 3, hidden desktop, functional only)

**d0f/d0t pair** (`matrix-s3-functional.json`, 03:30:13-03:34:53, `build/agent8/matrix/20261122-0330`):

| | d0f (`0330-d0f-r1`) | d0t (`0332-d0t-r1`, `REX_TIMER_WAIT_BLOCKING=1`) |
|---|---|---|
| TimerQueue busy % (max) | 39.1 (52) | 0.4 (2.9) |
| window fps | 145.2 | 90.9 |
| median / p99 / max ms | 4.19 / 45.5 / 112 | 6.51 / 63.9 / 128 |
| >33 / >100 ms frames | 163 / 1 | 298 / 2 |
| process cores | 2.40 | 2.06 |
| 53-67 fps band: frames / time / 1 s bins | 2.3% / 5.5% / 2.0% | 4.4% / 6.7% / 14.0% |
| window fps per 10 s | 144 186 194 145 57 | 50 57 103 140 105 |

- No dumps, `ticks_skipped` 0, clean WM_CLOSE (5.1 s and 1.2 s), `ff_to_window_s` 59.99 and 60.02.
- Thread shift with d0t: guest thread F80001A8 46% → 75% busy, Main XThread 49% → 30%.
- Caveats: d0t-r1 ran with the sys-csv builder's untested patch (same format; extra CPU only at start and end); d0f-r1's warm-up (not its window) overlapped a 4 s CPU burst.
- Band numbers: `build/agent8/scratch/band.py` (frame band 14.93-18.87 ms; 1 s bins of summed frame time with 53-67 frames).

**Re-check d0t, d11t, d0f** (Agent 1, 03:42; `-Only d0t,d11t,d0f`, order fixed, 03:49:28-03:56:47, `build/agent8/matrix/20261122-0349`, exit 0):

| | d0t (`0349-d0t-r1`) | d11t (`0352-d11t-r1`) | d0f (`0354-d0f-r1`) |
|---|---|---|---|
| TimerQueue busy % (max) | 0.5 (2.6) | 0.3 (1.7) | 44.1 (61.3) |
| window fps | 78.0 | 62.0 | 52.2 |
| median / p99 / max ms | 7.62 / 73.7 / 185 | 7.17 / 71.3 / 127 | 9.41 / 80.9 / 151 |
| >33 / >100 ms frames | 403 / 12 | 573 / 2 | 588 / 8 |
| process cores | 2.00 | 1.77 | 2.23 |
| 53-67 fps band: frames / time / 1 s bins | 3.3% / 4.4% / 32% | 1.7% / 1.8% / 20% | 1.6% / 1.4% / 24% |
| window fps per 10 s | 156 78 63 52 41 | 57 39 77 77 60 | 48 41 68 49 55 |

- All three: clean WM_CLOSE, exit 0, no dumps, `ff_to_window_s` 59.99-60.05, no build tools. d11t's game.log has the `Host timer resolution set to 1 ms` line; d0t and d11t have `REX_TIMER_WAIT_BLOCKING=1` in `env_set`. d0f had `ticks_skipped` (info).
- **TimerQueue:** the blocking wait cuts it from 39-44% of a core to 0.3-0.5% in all three timer runs (d0t twice, d11t once), and process CPU drops by 0.2-0.5 cores.
- **fps cannot be judged from these runs.** d0f alone gave 145.2 fps at 03:30 and 52.2 fps at 03:54. Every run, d0f included, enters a slow state at a different time (40-110 s after the first frame): 40-70 fps per 10 s on the same scene (226 draws per frame), with guest thread F80001A8 at 75-80% busy (46% in the fast 03:30 d0f run) and the E-cores mostly idle (E util 36-47% against 78%). P-core clocks stay at about 1.9 GHz effective in every run and GPU temperatures stay at 77-83 °C with no throttle samples, so it is not thermal. The 53-67 fps band share does not single out the timer runs either (1 s bins: d0f 2% and 24%, d0t 14% and 32%, d11t 20%).
- Power: the Windows power-mode overlay was `best_efficiency` (scheme Balanced, AC) in every run tonight; sys.csv records it per second and flags a change during a window.

### GO checks (Agent 1, 04:02; answered 04:11)

Tools: `build/agent8/scratch/phase_switch.py` (light-to-heavy switch time from perf.csv draws per frame, light share inside the window, slow 10 s bins; output `phase_switch.txt`/`.json`) and `build/agent8/scratch/sysbin.py` (sys.csv per 10 s from the first frame next to fps; output `sysbin.txt`).

**(b) The 60 s floor holds.**
- The light-to-heavy switch is a draw-count step: 218 draws per frame on the light scene, 223-226 on the heavy one.
- Window 3 (interactive, 19 runs): every devoff2 run (d0, base, d11) switched at **30-33 s** after the first frame, except d11-r1, which never switched (218 draws for 300 s: the light run, now caught by the `light_phase` flag). The n0 runs (native) log no draw counts in perf.csv; their fps steps down at the same 30-40 s.
- Window 3's warm windows started 40.3-171.9 s after the first frame (late starts from the runner stalls) with 0.0% light frames in every run except d11-r1 (100%); its cold runs started at about 15 s (56-65% light).
- Tonight (hidden desktop): the switch came at **31-35 s** in all 14 runs that ran past 35 s (0330-0354 and the a-prof/b-prof profiles); the cold Quick runs ended at about 31 s, before it.
- The "40-110 s" seen tonight is the onset of the slow state (below), not the phase switch.
- Window 4 starts every window, cold runs included, at least 60 s after the first-frame signal: a margin of 25 s or more over the latest switch seen. No change needed.

**(a) Power mode: leave it as it is.**
- Window 3 logged no CPU clocks and no power mode: sys.csv is new for window 4, and window 3's run.json `timing_env` holds only the desktop and build-tool checks.
- The System event log has no Kernel-Power, Kernel-Processor-Power or UserModePowerService events since 23:00 (no logged power-source change, firmware speed limit or power-mode change overnight).
- Tonight every sys.csv run had scheme Balanced, overlay `best_efficiency`, AC, P-cores at 1.9-2.1 GHz effective, in fast and slow stretches alike.
- Tonight's fast-state heavy-phase fps (145-201 per 10 s) is at or above window 3's (151-194 per 10 s, steady 160-167). If window 3 had run at higher P-core clocks, its heavy phase should have been faster than tonight's fast state; it was not. So there is no sign that window 3 ran faster.
- Instruction for the user: leave the power mode as it is, before and during the window. sys.csv records the scheme, overlay and AC state every second, and `power_change` excludes a run if they change inside its window.

### The slow state is the E-cores at minimum clock (04:08)

sys.csv per 10 s against fps per 10 s (`sysbin.txt`):

| run | fast stretch: fps / P MHz / E MHz / E util | slow stretch: fps / P MHz / E MHz / E util | onset (Agent 11's scan, s after first frame) |
|---|---|---|---|
| 0349-d0t-r1 | 154-262 / 1915-2088 / 1499-1748 / 89-102% | 38-79 / 1826-1949 / 552-557 / 33% | 69 |
| 0352-d11t-r1 | 163-258 / 1917-1944 / 1490-1511 / 89-90% | 36-67 / 1847-1935 / 550-664 / 33-40% | 42 |
| 0354-d0f-r1 | 162-230 / 1907-2092 / 1438-1722 / 87-104% | 42-68 / 1901-1944 / 554-692 / 33-42% | 61 |

- The slow state begins exactly when the E-cores drop from about 1.5 GHz to about 550 MHz and E-core utility falls to a flat 33%. The P-cores stay at about 1.9 GHz. Agent 11's `bench/agent11/timerq_slowstate.ps1` detects it the same way (E-cores under 800 MHz for 3+ samples).
- Agent 11's scan of 0330-0349 (`build/agent8/scratch/slowstate-0330-0357.txt`): 12 of 16 runs entered it, at 27-100 s; blocking-timer runs are not spared (3 of 4).
- It is not thermal (GPU 77-83 °C, no throttle samples) and not the game's phase (the scene stays at 226 draws per frame).
- Window 3 (interactive desktop, game in the foreground) had no 10 s bin under 130 fps after the switch in any of its 19 runs. So it looks like a power-management effect on a never-foreground process on the hidden desktop. Window 4 runs in the foreground on the interactive desktop; sys.csv logs E-core clocks every second, and the read-out runs Agent 11's scan before any fps.

### Profiles (03:57:17-04:09:51, `matrix-codegen-check.json`, `build/agent8/matrix/20261122-0357`)

| run | bin | profile window (150 s) | result |
|---|---|---|---|
| `0357-a-prof-r1` | devoff2 | 03:58:43-04:01:13 | PROFILE, exit 0, clean WM_CLOSE 3.3 s, profile-728734687.bin + map; 10,154 frames |
| `0401-b-prof-r1` | devoffB | 04:02:56-04:05:26 | PROFILE, exit 0, clean WM_CLOSE 4.4 s, profile-728987468.bin + map; 10,179 frames |
| `0405-n-prof-r1` | native2 | 04:07:15-04:09:45 | PROFILE, exit 0, clean WM_CLOSE 1.1 s, profile-729246015.bin + map; 10,616 frames; `Native presentation: ... focus=false ... fps_limit_cvar=0 vsync=false tearing=true` |

- No build tools at any point (Agent 2's S3d had finished; the nativeB build started at 04:12:09, after the last profile).
- a-prof and b-prof spent most of their profile windows in the slow state (window fps 67.7 and 67.9; slow 10 s bins from 60-70 s on). Both were in the same state, so A vs B still compares; the hot list reflects the slow state. Sent to Agents 7 and 9 (n-prof and the focus line to Agent 7).

### GO line (sent to Agent 1 at 04:11)

- File: `bench\agent8\RUN-WINDOW4B.cmd`, double-click on the unlocked desktop.
- About 40-45 min of real time (PlanOnly 39 min: 17 runs, 1 shared cold run, then d0/B/d3/d11t x4 in a Latin square).
- Before: screensaver (None), charger in, other programs closed, power mode left as it is, hands off.
- End screen: `Window 4b matrix finished (exit code N). Results: build\agent8\matrix\ (newest folder), summary.md`, then `Press any key to continue . . .`.
- Dry runs: W4a `-Quick` 6/6 OK (0336), W4b `-Quick` 5/5 OK with one shared cold run (0342), runner self-test 55/55, W4b PlanOnly 17 runs / 39 min. Floor and power answers as above.

### Window 4 read-out (after the user's run)

1. Newest `build\agent8\matrix\<yyyyMMdd-HHmm>`: summary.md and results.csv (excluded runs are listed under "Flagged runs").
2. `powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_slowstate.ps1 -Since <yyyyMMdd-HHmm>` before reading any fps: any run with a slow-state onset inside its window is not a result.
3. `python bench\agent8\run\matrix_recheck.py <dir> --write` (recheck.md: paired deltas per round). Its `slow` column gives each run's slow-state onset and the share of window samples with the E-cores under 800 MHz (`!` = in the window), by the same rule as Agent 11's scan; `--drop-slow` recomputes the arms and deltas without those runs. Tested at 04:24 on 0330/0336/0342/0349 (onsets match Agent 11's scan run for run; `--drop-slow` drops all three 0349 runs) and on window 3's 0013 (no sys.csv: `-`, numbers unchanged).
4. `python build\agent8\scratch\phase_switch.py <dir>\runs\*` : switch at 30-35 s and 0% light frames in every window.
5. Every d11t game.log has `Host timer resolution set to 1 ms`, and its run.json `env_set` has `REX_TIMER_WAIT_BLOCKING=1`.

### Slot runs after GO (session 3, hidden desktop, functional only)

Order (Agent 1, 04:11 and 04:54): s0-s2, native3d n0/n2/n3, the nativeB route pair, Agent 3's attract pair plus the
warm-storage run, then Agent 7's shader dump and maybe Agent 11's throttling pairs (only if they end by 07:15). A
native3e build, if Agent 1 gives GO, goes after 05:50. Every item ends by 07:30. Runners:
`build/agent8/scratch/slot-run.ps1` (`-Job srows|native3d`, pinned matrix sha, refuses on a running game, a build or
free RAM < 6 GB) and `build/agent8/scratch/harness-pair.ps1` (`-Job nativeb|nativeb2|attract|warm`, same RAM and game guards,
build tools noted, per-arm cvar check `Show-Cvars`, warm run seed check; from 05:42 also the per-arm stall check
`Show-Stalls`, a 3 s per-process CPU snapshot `Show-Load` before and after each arm, `-PlanOnly` and `-ShowDir`), plus
`build/agent8/scratch/s11-run.ps1` for Agent 6's S11 A/B.

- **Attract pair, 04:16:** refused by the RAM guard (5.4 GB free during Agent 2's nativeB build). Nothing ran; moved last.
- **s0-s2, 04:38:55-04:51:14** (`build/agent8/matrix/20261122-0438`, `bench/agent8/run/matrix-native-uploads.json`
  sha 15BB7822..., `-Only s0,s1,s2`, idle machine, no build tools). 4 runs (0439-cold-s0, 0441-s0-r1, 0444-s1-r1,
  0447-s2-r1): status OK, exit 0, clean WM_CLOSE 0.6-1.1 s, ff->window 60.0 s, no flags.
  - [error] 0 and non-INSTALL [warning] 31 in all four (= baseline); native_fps_limit_cvar 0 in every row; Agent 5's
    six grep strings 0 in all four.
  - `Native texture staging pool: enabled, 64 MB idle budget` in s2 only. No `hits=` line in any run (s2 included).
    Agent 5 (05:22): the `hits=` line is periodic, logged every 256th pooled AcquireTextureStaging (rexlego
    gpu_native/textures.cpp:209-221), and nothing is printed at exit. So s2 made fewer than 256 pooled acquires
    (unchanged texture content reuses the prepared upload, :2361-2367). The enable line is printed at init, so it only
    proves the switch was read. In u2 runs a missing `hits=` means "not reached", not a failure.
  - No `Native slow CPU operation` line in the scored runs (the cold s0 has one `pool-copy`, total_ms 5.55): the
    decode-content-hash / allocate-map-stage comparison has no data. The slow-op threshold is 4.0 ms per op
    (gpu_native/slow_operation.h:37, Agent 5); no texture upload reached it, so nothing needs a re-run.
  - Frames (n = 1 per arm; no sys.csv in this matrix, so the E-core slow state cannot be ruled out). First 30 s from
    row 0: s0 1 frame > 33 ms, max 90 ms; s1 1, max 300 ms (the legacy startup burst Agent 5 predicted); s2 4, max
    111 ms; cold s0 2, max 742 ms. Window (60-180 s after ff): fps 109 / 94.6 / 110, p99 23.9 / 42.3 / 23.3 ms,
    > 33 ms 30 / 241 / 27.
- **nativeB bin** (Agent 2, build ended 04:34:06): `build/agent2/nativeB-bin`, exe 01C4D5A3...5C5C and MANIFEST
  E5CBF30A...2A966 verified (149 PASS / 0 FAIL / 34 NOTE per Agent 2).
- **Stale copy fixed:** `bench/agent8/run/matrix-native-threaded.json` was Agent 4's 00:20 version; now byte-identical to
  `bench/agent4/matrix-native-threaded.json` (1F8BC5DD...C581, 02:20), PlanOnly exit 0 (12 runs, about 30 min). Not
  run tonight.
- **native3d n0/n2/n3, 04:51:57-04:59:13** (`build/agent8/matrix/20261122-0452`, `bench/agent4/s3/matrix-native3d-functional.json`
  sha FACD09D1..., idle machine, no build tools). All three status OK, exit 0, clean close 0.8 / 1.1 / 2.9 s,
  ff->window 60 s, no flags.
  - `hash=0` lines 0 / 0 / 0 (Agent 2's native3e trigger is not met). n2 logs `Native draw batches: parallel workers=2`;
    n3 has no draw-batches line (full-prep path); `threaded recording ON` once in n2 and n3; worker lines 26 / 27.
  - Agent 4's `check_n_rows.py --baseline n0`: n2 PASS, n3 PASS, every check [ok]
    (`build/agent8/matrix/20261122-0452/check_n_rows.json`).
  - Warning types: n2 has n0's 8; n3 has no new type and lacks 2 of n0's (`unrecognized pixel/vertex shader resource`,
    x8 each in n0). Non-INSTALL [warning] 31 / 31 / 23, [error] 0.
  - Functional numbers (n = 1, not timing): median 9.26 / 7.21 / 6.68 ms, p99 23.7 / 33.7 / 32.3 ms, > 33 ms 8 / 74 / 68
    in the 60 s window; throttle_wait_ms per 600 presents 2709 (n2) / 2969 (n3).
- **nativeB route pair, 04:59:38-05:07:35** (`harness-pair.ps1 -Job nativeb`, log `build/agent8/scratch/nativeb-pair.log`;
  route `harness/routes/b-gate-menus-long.txt` sha 1F3559C8...F014, 54 steps, 420 s cap; `-Cvar
  native_settings_frontend=false` on both arms (the cvar's default, Agent 3), default caps; idle machine, free RAM at
  start 8.07 / 7.87 GB, no build tools at start or end).
  - **A native3d** (`build/agent3/runs/20261122-045945-bgate-long-native3d`): route 54/54, harness exit 1, result
    CRASHED, but WM_CLOSE closed it in 2.7 s with exit code 0. At 05:03:06.929 guest thread 0x4 had waited 5 s for
    critical section 0x84959edc (owner tid 0x0013 parked at lr=82BCE244, r3=300BE000; owner callers 82BCDB60 <-
    82B7AC0C <- 82BA0D20 <- 82BCF9D8 <- ...; waiter lr=82A2A270 <- 82FB0140 <- 82AED6BC <- ...). The watchdog wrote
    `hang-63248.dmp` (65 MB, in the run dir) at 05:03:10.478 and the same host thread logged scene teardown at
    05:03:10.479, so the stall cleared (max frame 5198 ms); it was not a permanent deadlock. The CRASHED label comes
    from the `[FATAL] Minidump written` line. Log: 184 warnings, 4 errors (the STUCK-LOCK lines), 1 critical.
  - **B nativeB** (`build/agent3/runs/20261122-050343-bgate-long-nativeB`): route 54/54, exit 0, RUNNING, clean close in
    1.16 s; 184 warnings, 0 errors, 0 critical; peak private 2737 MB (A 2745 MB); frames first written 19 s after launch
    (A 12 s).
  - Both arms drop to 7-19 fps for the last ~80 s of the route (the heavy end scene). Per 10 s: A ... 157.9, 18.9, 17.1,
    19.4, 8.8, 7.3, 1.9, 6.6; B ... 60.9, 14.1, 16.8, 18.7, 10.8, 7.9, 7.3, 8.8, 12.1. So the low fps belongs to the
    scene, not to the stall; A's 1.9 bin is the stall.
  - INSTALL*.DAT probe batches: same counts on both arms (x34, x68, x34). No 'unknown cvars' in either summary.txt and
    0 `Config: unknown cvar` lines.
  - `bench/agent8/run/gate_logdiff.py` exit 1 with one finding: `placement buffer relocation lr=83F9B660`, A 1 line, B
    none (the count depends on the route, but presence must match). CPU pool copy callers equal (82B5819C x128 each);
    slot heap registered 9 / 9, extended 0 / 0; warning kinds A 16 / B 11, new in B 0, gone in B 5 (the STUCK-LOCK and
    FATAL lines).
  - Agent 10's `logdiff.py --base A --cand B` exit 0: NEW 0, MORE 0, no fail markers in B. GONE keys: the
    STUCK-LOCK/FATAL lines, the placement relocation info line and Toypad Read/Write lines.
  - The earlier bgate runs (dry, a, b, long-devoff2, long-devoffB) had 0 STUCK-LOCK lines. This is one sample per arm;
    Agent 10 gives the 1b verdict.
  - **Agent 1 (05:17):** the native3d stall is a cold-cache pipeline frame in frames.csv, and Agent 6 is triaging it.
    Both run dirs and `hang-63248.dmp` stay exactly as they are. native3d is not re-run on the long route without
    Agent 1's GO.
  - **Agent 10's verdict (05:25): nativeB 1b route pair PASS vs native3d.**
    - B: 54/54, exit 0, 0 errors / 0 critical, no dump. logdiff NEW 0 / MORE 0 / flags 0.
    - 19 common warning types with equal counts. Slot heap 9/9 and pool copy 128/128 (lr 82BD2B44, caller 82B5819C,
      VS A58EBA12) match. The 9 fail lines are 0/0, and the same 26 scene teardowns come in the same order.
    - Caveat 1: the placement relocation line lr=83F9B660 (A 1 / B 0) is "not covered, not a diff". It is per call
      and depends on the heap layout: A's only hit was at 213.56 s in the idle tail, and the 18 matrix native runs
      have 0 hits.
    - Caveat 2 (Agent 3): the front-end exit came at a different press (B at the 2nd B, A about 7 s after the 3rd;
      boots +8.4 s vs +13.3 s). One run each can't separate this.
    - Recommendation: no rollback. If the slot has room, a reversed-order tie-break pair (nativeB then native3d),
      which also removes the driver-cache order effect for Agent 6's stall triage. That needs Agent 1's GO. Window 4
      should add a level-change route for both.
- **Agent 7's shader dump, 05:09:09-05:11:40** (`slot-run.ps1 -Job sdump`, log `build/agent8/scratch/sdump.log`;
  `bench/agent7/matrix-shader-dump.json` sha F65EB9BC...2F47; one arm `sd` = Agent 4's native3d n0 row plus
  `LEGO_DUMP_MISSING_SHADERS=<run>\shader-dumps`, with the pool-copy XXH3 check on, so not timing; idle machine, 8.04 GB
  free, no build tools). Run `build/agent8/matrix/20261122-0509/runs/0509-sd-r1`: status OK, exit 0, clean close in
  3.37 s, ff->window 60 s, no flags, no .dmp.
  - 9 `dumped missing shader` lines, which match the 9 files under `shader-dumps`:
    - 05:09:24, top level: vs-A58EBA123EFB541C (704 B) and ps-93B9F93B535E7CCA (156 B).
    - 05:09:34: placement-raw vs-DCD4AD8441398283 and ps-C77B3ABB6F87ACD9 (2048 B each); placement-containers
      vs-ACAF01F01E1C03D2 (1304 B) and ps-75A4D1ABA62F7594 (1716 B).
    - 05:10:01: placement-raw vs-98D43959C65B882A (96 B); placement-containers vs-CCD7655302B54D80 (944 B) and
      ps-E81FD692C3AB35E1 (1640 B). This set has no raw ps.
  - 8 `missing from AOT index` warnings, all at 05:09:34: 4 x placement VS 0xAC449538 (prefix DCD4AD8441398283) and
    4 x placement PS 0xAC448F28 (prefix C77B3ABB6F87ACD9; its first four words are all 0). The 05:10:01 set has no
    AOT warning.
  - No file was written in `build/agent2/native3d-bin` after the job started. Agent 7 re-checks its MANIFEST.
- **Attract pair + warm run, 05:11:55-05:35:14** (`harness-pair.ps1 -Job attract`, log
  `build/agent8/scratch/attract-pair.log`; route `harness/routes/attract-long.txt` sha 4D35FAF4...E4E2, 91 steps,
  `-GpuLog`, no cvars; free RAM at start 7.92 / 7.91 / 7.65 GB, no build tools at start or end). Agent 3 (05:28): the
  machine was CPU-bound for the whole slot (~100% CPU at the 1.7 GHz base clock: MsMpEng 2.5-2.9 cores, dwm 1.2,
  PresentMon_x64 1.0, the game 1.3-2.6, plus other agents' recursive scans), so these frame numbers are not usable.
  - **devoff3** (`build/agent3/runs/20261122-051201-attract-devoff3`, 540 s): exit 0, RUNNING, 91/91, WM_CLOSE in
    11.82 s; 143 warnings, 0 errors; avg 2.03 cores. Agent 3 excluded it from the numbers (few_rows + stall_in_window).
  - **devoffB** (`build/agent3/runs/20261122-052024-attract-devoffB`, 540 s): harness exit 1 "CRASHED", but 91/91 and
    WM_CLOSE in 18 s with exit code 0. Four STUCK-LOCK episodes on critical section 0x84959edc (05:24:05, 05:24:52,
    05:24:58, 05:25:57; 20 error lines): waiter thread 0x6; owner tid 0x0017 at lr=83FAF200 (once 83FAF188), owner
    callers 83FBFBDC <- 83FC0CA8 <- 83FB3AC8 <- 83FBF698 <- 83FBFA98 <- 82BD6BA4; waiter callers 82A2A270 <- 82AED6BC
    <- 82B7132C <- 82FB01A0 <- 82B7995C <- 82AB2108 <- 82FEBDE0; `GPU thread: executing PM4 opcode 0x22 | read ptr
    0x161, write ptr 0x35a`. `hang-52704.dmp` (49 MB, 05:24:07). Max frame 16.4 s; avg 1.77 cores; GPU util median 31%.
  - **devoff3 warm** (`build/agent3/runs/20261122-052901-attract-devoff3-warm`, 360 s, `-SeedXenos
    build/agent3/seed/devoff2-214`): harness exit 1 "CRASHED", WM_CLOSE in 2.84 s with exit code 0. One STUCK-LOCK
    episode on the same CS at 185.5 s (05:32:12): waiter 0x6, owner tid 0x0017 at lr=83FBF868 (callers 83FBF7B4 <-
    83FBFA98 <- 83FBF868 <- 83FBFBDC <- 83FC0CA8 <- 83FB3AC8 <- 83FBF698 <- 83FBFA98 <- 82BD6BA4), the same waiter
    callers as devoffB, PM4 0x22 (read 0x26d7, write 0x28a9); `hang-69196.dmp` (05:32:14). Route 63/91: the 360 s cap
    came first (the route needs ~475 s), which is the only reason route-report says "script ran to the end" FAIL.
    - Storage: `Translated 229 shaders from the storage in 85 milliseconds`, `Created 214 graphics pipelines ... in
      2016 milliseconds`. The run grew its copies to xpso 19452 B (270 pipelines) and xsh 210512 B, so the attract
      route still needed 56 pipelines that the seed (from the b-gate route) did not have.
    - Seed dir unchanged after the run (names, sizes, mtimes, read-only flags, sha256: xpso 15420 B 4D4F514DB21707ED,
      xsh 160232 B EEFC75E4760E7AFC).
  - All three: run.json cvars none, no 'unknown cvars' in summary.txt, 0 `Config: unknown cvar` lines.
  - **So the CS 0x84959edc stall is not native-specific.** It hit two OFF runs under load. The waiter path matches
    native3d's arm A at 82A2A270, 82AED6BC, 82B7132C, 82B7995C, 82AB2108 and 82FEBDE0 (native3d's walk has an extra
    82FB0140 after 82A2A270 and 82FB01E8 where the OFF runs have 82FB01A0). The owner differs: tid 0x17 in
    83FAxxxx-83FCxxxx code in the OFF runs vs tid 0x13 at 82BCE244 in native3d; both owner walks end near 82BD6xxx
    (82BD6BA4 vs 82BD6CD0). The earlier bgate runs and the cold devoff3 attract run had none. Sent to Agents 6, 10, 1
    and 3 at 05:38.
- **Agent 1 (05:31):** GO for the reverse-order pair (nativeB first, then native3d). While the queue runs (until about
  07:15): no recursive searches or scans over the SDK, DimensionsRecomp or build trees while a game runs; targeted
  reads only, at most 2 threads.
- **PresentMon (Agent 1's question, answered 05:38):** not new. `PresentMon_x64.exe` (pid 14612, a child of NVIDIA's
  `nvfvsdksvc_x64.exe` pid 13184) was created 11-13 17:36:23, so it also ran through window 3 and the W4 dry runs.
  Get-Counter at 05:33: PresentMon_x64 0.98 cores, MsMpEng 2.52 cores. Window 3 has no system-wide per-process samples
  (proc.csv covers the game process only; window 4's sys.csv has system totals, not processes), and a non-admin
  Get-Process can't read its CPU (so `Show-Load` can't see it either). Suggested: note it on the W4 checklist; agents
  don't stop it.
- **Threaded matrix re-copied again (Agent 4, 05:05):** `bench/agent8/run/matrix-native-threaded.json` is now
  byte-identical to Agent 4's final version, sha 419FAE1F...20C4 (7351 B). PlanOnly exit 0: 12 runs, 0 cold, about
  30 min, bin ok, sys.csv off (I suggested turning it on). It is for a later window, not window 4.
- **Agent 2's inventory, 05:39:08-05:39:16** (7.8 s, single thread, 0 problems). Builds are held until my all-clear
  (about 06:50); native3e has no GO.
- **Agent 11's throttling pairs (task #24), spec 05:36:** `bench\agent11\pthrottle_pairs.ps1`: 6 devoff2 d0 runs through
  the unchanged run-matrix.ps1 (d0 = opt-out off, d0e = EXECUTION_SPEED opt-out set by its sidecar on its own game
  processes; order d0 d0e | d0e d0 | d0 d0e; sys_csv on). `-PlanOnly` here at 05:37: exit 0, 6 runs, about 18 min.
  Slotted after the reverse pair.
- **Agent 6's S11 A/B, 05:39:54-05:50:10** (`build/agent8/scratch/s11-run.ps1`, logs `build/agent8/scratch/s11-run.log`
  (A) and `s11-runB.log` (B); spec perf-notes/agent6-attract-stalls.md section 11, approved by Agent 1). Both arms:
  `harness\run-game.ps1 -BinDir build\agent2\devoff2-bin -Seconds 420 -Warmup 60 -InputScript
  harness\routes\b-gate-menus-long.txt` (stop step at ~221 s), bin check exe 7F0B1C1C84BC66FF and rexgpu-xenos.dll
  77A5300B885C5274 ok, no -Cvar (toml sha unchanged, not rewritten), no build tools at the starts. run.json
  `command_line` confirms the args: A `--slow_frame_log_ms=50`, B `--slow_frame_log_ms=50
  --d3d12_pipeline_creation_threads=0`. Load before launch: 3.7 (A) and 4.0 (B) cores total, MsMpEng 0 (PresentMon
  can't be read).
  - **A** (`build/agent3/runs/20261122-053957-s11-armA`, 05:39:54-05:43:52): exit 0, 54/54, WM_CLOSE 1.2 s, 0 errors,
    no dump, no unknown cvars; frames first written 18 s after launch. 541 `slow frame #` lines (Agent 6 expected
    260-450), perf rows > 50 ms 542, join matched 541/541. H0 (draw_calls 2823, vertices_processed 366575) at row 8656,
    only 14.6 s of perf.csv after it (the 03:17 long-devoff2 reference: rows 9282-9290, 40.5 s); xpso 63 pipelines
    (reference 214). The 35 s before H0 has many 250-1900 ms frames, mostly fence. Join hints: Q2/Q3 no burst row
    after H0; Q4 35 heavy rows with a line (7214 ms), idle 23%, fence 36%.
  - **B was refused at 05:43:56** by the 6 GB launch check (5.84 GB free right after A closed; Agent 1 saw 4.78 GB at
    05:43 during A). Free RAM was back at 6.1 GB at 05:46:11 and B ran unchanged as a separate `-Order B` call.
  - **B** (`build/agent3/runs/20261122-054621-s11-armB`, 05:46:18-05:50:10): exit 0, 54/54, WM_CLOSE 1.2 s, 0 errors,
    no dump, no unknown cvars; frames first written 12 s after launch. 285 `slow frame #` lines, perf rows > 50 ms 284,
    join matched 284/285 (one row >= 51.1 ms without a line, row 9384). No H0 anchor row: B is not output-identical
    (synchronous creation drops no draws), so the anchor's counts may not occur. xpso 63 pipelines. Join hints: Q3
    burst rows 9174-9175 (pm 23, 1348 ms): create 742 ms, translate 13 ms, "creation dominates"; row 8994 2611 ms with
    create 1175.6 ms (21 new); row 9173 1529 ms all idle ("guest side"); Q4 29 heavy rows with a line (5227 ms), idle
    3%, fence 31%.
  - `llvm-objdump` (pid 100952, another agent's) was running when B ended and was gone at 05:50:32. Agent 6 does the
    analysis; join copies in `build/agent8/scratch/20261122-0*-s11-arm?-join.txt`.

### Slot queue 05:50-07:30 (written 06:23)

- **Agent 1's rules for the rest of the slot (05:45/05:57):** keep the 6 GB launch check as it is (waiting for RAM is
  fine, bypassing is not). Priorities for 06:33-07:15: 1 = Agent 6's #25 baseline pair, 2 = Agent 5's a-vol, 3 = Agent
  3's quieter attract re-run (q), run only if a quiet gate passes at the time. 06:33-07:15 is an idle machine for the
  attract runs: no compiles, no recursive searches, no reads over ~100 MB, batched tool calls, 1 thread. All slot runs
  end by 07:30; no builds or game runs from 08:30.
- **W4b memory question (Agent 1), answered from the code:** run-timing.ps1:149-150 exits 3 below `MinFreeRamGB`
  (default 6.0; run-matrix.ps1 does not override it): no wait, no retry, no run dir. run-matrix.ps1:401 prints the
  preflight "UNDER 6 GB: runs will not start" line as info only. run-matrix.ps1:704-708 gives a run without a run dir
  status `NOT STARTED` with the "free RAM X GB is under 6 GB: not starting" note (red `--> tag: NOT STARTED` console
  line plus a yellow note); summary.md shows the status and note, "N runs (M OK)" and the arm OK/runs count; the runner
  exits 1. Caveat: NOT STARTED and SKIPPED rows have `valid_timing` empty and count in `$invalid` (line 499), so a single
  such row puts the "FUNCTIONAL ONLY ... Do not use these numbers" banner on summary.md and the console even when the
  OK runs are valid timing; the arm table's "valid" column is the truth. Not changed (runner freeze).
- **Reverse native B pair (Agent 10's tie-break, Agent 1 GO 05:31), 05:50:30-05:58:32** (`harness-pair.ps1 -Job
  nativeb2`, log `build/agent8/scratch/nativeb2-pair.log`), `harness\routes\b-gate-menus-long.txt`, 420 s, both arms
  `-Cvar native_settings_frontend=false` (default caps), no unknown cvars:
  - nativeB first: `build/agent3/runs/20261122-055041-bgate-rev-nativeB`, 05:50:38-05:54:32, free RAM 7.68 GB,
    `llvm-objdump:77944` (another agent's) at the start. Exit 0, 54/54, 0 errors, 0 STUCK-LOCK, no dumps. Largest guest
    frames 854.4 ms (row 15332, perf 170.55 s) and 817.1 ms (perf 124.96 s).
  - native3d second: `build/agent3/runs/20261122-055439-bgate-rev-native3d`, 05:54:37-05:58:32, free RAM 7.61 GB, no
    build tools. Exit 0, 54/54, 0 errors, 0 STUCK-LOCK, no dumps. Largest guest frames 1449.5 ms (row 14631, perf
    138.15 s) and 1051.7 ms (row 14500, perf 130.16 s).
  - gate_logdiff (A = native3d, B = nativeB): PASS, no FAIL finding; the only kind gone in B is "Native GPU: completion
    callback GPU wait took # ms" (2 lines, A only). Agent 10's logdiff: NEW 0, marker flags 0; GONE lines info only.
  - Front-end exit (route-report.ps1 on copies, `build/agent8/scratch/rr-<run>/route-report.txt`; its "FAIL pad DLL
    loaded" is a copy artifact): same scenes up to UP 2 (n8 title, n2 from A1). nativeB leaves on the 2nd B again (n2
    at the L40 press 119.72 s, n0 at L41 124.79 s, log +34); native3d on the 3rd B (n2 through L44 130.51 s, n0 at L46
    140.81 s, log +56, then n41). native3d polled the pad slowly around the 3rd B (L43 +29, L44 +176, ~35 fps; nativeB
    +111/+620). So the run order is not the cause.
  - Agent 10 (06:20): every must-match item passes again (logdiff NEW 0/MORE 0/flags 0, slot heap 9/9, pool copy
    128/128, PSO 187/187, 9 fail lines 0/0), but the exit split repeated, so 1b is reopened on that one item. The exit
    comes from the screen's own timer (press-to-exit 0.7-8.1 s; OFF builds leave with no press); first frame to exit
    native3d 118.9/120.5 s vs nativeB 105.7/108.9 s. Not a fail item, no rollback; options (a)/(b)/(c) to Agent 1.
- **Agent 11's throttling pairs (task #24), 06:00:46-06:19:09** (`bench\agent11\pthrottle_pairs.ps1`, free RAM 7.8 GB,
  no game at the start; log `build/agent8/scratch/pthrottle-pairs.log`; stamp 20261122-0600, report
  `build/agent11/pthrottle/pairs/20261122-0600-meta/report.txt`): exit 1, "RESULT: FAIL ... bad 3", VERDICT
  INCOMPLETE. d0: 3/3 counted, all with the slow state (onsets 103/71/37 s, slow share 24/37/41 %). d0e: 0/3 counted
  ("opt-out not verified": C=0x1 applied and held in 99.6-99.7 % of reads, last read-back C=0x0, the one reapply at the
  end returned -1). timerq cross-check: 6 spin runs, all 6 with the slow state (d0e onsets 40/49/47 s too), 0 blocking.
  W4b hash after: 53 files, 0 changed or missing.
- **Agent 4's threaded matrix:** `bench/agent4/matrix-native-threaded.json` now has `"sys_csv": true` (arms unchanged),
  sha256 76FE0BAAD3BF36BCC8D020DAAE57CF20C61B47D9928766DB622D7210DEFF6248 (7931 B); re-copied over
  `bench/agent8/run/matrix-native-threaded.json` (was 419FAE1F, 7351 B) at 06:15. For a later window, not tonight.
  Agent 5's `bench/agent5/matrix-native-uploads-x5.json` (62F58F2B..., u0/u1 x5 cut of uploads-45): plan-only tonight.
- **harness-pair.ps1 additions for #25 and q (06:08-06:13):** `-EndBy` (default 07:30: an arm is not started when its
  cap + 30 s could end after it; checked before the RAM wait and again right before the launch), `-Job base` (baseline
  pair with the exe/rexruntime hash check, run 2 skipped on a STUCK-LOCK, a failed pad check or no attract),
  `-Job q` (cold then warm devoff3, quiet gate before each arm), `Quiet-Gate` (15 x 2 s of `\Processor
  Information(_Total)\% Processor Time` and `\Process(msmpeng)`; PASS when the mean is < 25 % and MsMpEng max < 0.2
  cores; up to 4 tries), `Start/Stop/Show-Sampler` (uses Agent 3's cpu-sampler CSV when it was written in the last 30 s,
  else its own Start-Job sampler; summary of the arm's rows), `Show-Reached` (route-report pad/scene/PROBLEMS lines and
  attract-report front end/H0/flags), `-GateTest`. Tests: parse 0 errors; base plan latest start 07:19:30 and q plan
  07:20:30 (seed listed, not hashed: 5752084B.rtv.d3d12.xpso 15420 B, 5752084B.xsh 160232 B); no-args message; ShowDir
  devoffB: 4 episodes (CS 0x84959edc, waiter 0x6, owner tid 0x0017 lr=83FAF200/83FAF188), 'scene 220/534' lines 21, pad
  ok, front end 220/534 at perf 72.35, H0 2831/406639 at perf 184.53, padOk/reached True; GateTest at 06:20:37 (a-vol
  game running): Agent 3's CSV used, try 1 total 97.3 % (max 100 %), MsMpEng max 1.68 -> not quiet; 122 sampler rows
  summarized; no orphan job.
- **Machine load (06:22:07, a-vol game uncapped):** total 99.9 %; per-process cores over 3 s: legodimensions 5.8, agy x15
  2.72, electron x4 2.24, powershell x8 1.33, CrossDeviceService 0.66, python x6 0.42, Taskmgr 0.39. Agent tooling
  alone (agy + electron) is ~5 cores (~41 % of 12 threads), so the 25 % q gate can only pass if that drops in the quiet
  window. Agent 3's sampler: 88.8 % mean total CPU 06:16-06:21 (MsMpEng mean 1.23, max 3.76 cores).
- **Agent 5's a-vol** (`bench/agent5/matrix-s4-invalvol.json`, sha256 9D6A6F2C...00055A0B confirmed by Agent 5; Agent 12
  confirmed the parser at 06:16): started 06:20:03 right after the pairs (free RAM 7.72 GB); PlanOnly: 1 run, about 5
  min, preflight ok. Results below.
  - a-vol result (06:20:03-06:24:11, `run-matrix.ps1 -Matrix bench\agent5\matrix-s4-invalvol.json -NoPrompt`, exit 0):
    status OK; `build/agent8/matrix/20261122-0620/runs/0620-a-vol-r1`, summary `build/agent8/matrix/20261122-0620/summary.md`.
    WM_CLOSE exit after 1.14 s, exit 0; 13148 frames, mean 87.65 fps, median 5.98 ms (functional only, hidden desktop);
    [error] 0, [FATAL] 0, STUCK-LOCK 0, no dumps. The game log rotated: game.1.log 5,242,535 B (14,971 `slow frame #`
    lines) plus game.log 3,803,369 B (10,829). Run dir and the rotation note sent to Agent 5.

### Slot queue 06:24-07:30 (written 06:50)

- **Agent 11 (06:27):** the 3 d0e FAILs in the throttling pairs are a teardown artifact (no re-run). Corrected verdict:
  NO EFFECT (d0e 3/3 and d0 3/3 with the slow state).
- **Agent 1's final slot order (06:29):** #25 base, a-vol (done), then q only if the quiet gate passes; otherwise (or
  if time remains) Agent 7's zero-code checks on native3d (n2 + `LEGO_NATIVE_TIMING=1`, n3 + `LEGO_NATIVE_TIMING=1`,
  n2 + `LEGO_NATIVE_PARALLEL_DRAWS=0`, sys.csv on); skip what doesn't fit. Post "last run ended" to all at the end
  (Agents 2, 3, 4, 9 and 10 wait on it; Agent 3 applies its 2 OK'd patches and Agent 4 starts its s35 pack after it).
  Window 4 = W4b (`RUN-WINDOW4B.cmd`, unchanged). New W4b read-out items: check that B's scored windows show the same
  scene as d0's (draws per frame or the phase flag); run Agent 11's `timerq_slowstate.ps1` over the fg=1 runs.
- **harness-pair.ps1 (06:24-06:28):** `-QStartBy` (default 07:06, because Agent 3's sampler stops at 07:16:44): an arm's
  latest start is min(EndBy - (cap + 30 s), StartBy), used for both q arms. `Quiet-Gate -Tries 4 -Until <latest
  start>`: at least 4 tries of 30 s, then more while one more can end before the latest start. Tests: parse 0 errors;
  q plan both arms 07:06:00; GateTest 06:25:19 (no game): total 40 % (max 55.3 %), MsMpEng max 1.82 cores -> not quiet;
  loop test 06:28:23 (`-Tries 1 -Until +70 s`): try 1 47.1 % (max 93.1 %, MsMpEng max 2.47), try 2 48 % (max 74.5 %,
  2.43), then "not quiet after 2 tries (no time for another try before 06:29:33)".
- **No-game load (06:25):** about 52 % total in a 3 s snapshot (gate mean 40 %): agy 1.53, electron 0.71,
  CrossDeviceService 0.43, powershell 0.35, Taskmgr 0.34, python 0.23 cores; PresentMon about 1 core; MsMpEng about
  1.2 cores mean, up to 3.7.
- **Launcher bug (06:33-06:35):** the q launcher (QWAITER, armed 06:28) has `harness-pair.ps1` in its own command line,
  and the base launcher's busy check excluded only its own marker, so it took the q launcher for a runner and waited
  ("runner pids: 43120", 06:33:01-06:35:14). Fix at 06:35: q launcher killed and re-armed with the base launcher's marker
  in its comment line; base started 3 s later (06:35:31, 2.5 min late). Lesson: each waiter's command line must carry
  the markers of all other waiters (or all busy checks exclude one shared marker).
- **zero-waiter.ps1 (06:34, `build/agent8/scratch/zero-waiter.ps1`):** chains 3b after the base and q launchers (their
  pids taken once, then polled with Get-Process only), then runs each arm as `run-matrix.ps1 -Only <id> -NoPrompt` when
  there is no game, runner or launcher, free RAM >= 6.2 GB, and the arm can end by 07:30 (start by 07:25:30, 270 s per
  arm); per-arm logs `build/agent8/scratch/zero-<id>.log`. Bug: in Windows PowerShell 5.1 a single pscustomobject has
  no `.Count`, so with one launcher left `$a = Alive` read as none and the cheap wait ended at 06:44:03 (it still waited
  correctly, but with a WMI process query every 5 s during the q gate). Fixed with `@(Alive)`; restarted 06:45:14 (pid
  32356, watching q launcher 86000).
- **Zero-code matrix (06:32, Agent 7's spec):** `bench/agent8/zero/matrix-native3d-zero-code.json`: Agent 4's settings and
  n2/n3 rows from `bench/agent4/s3/matrix-native3d-functional.json` copied exactly, one env var each: n2t = n2 +
  `LEGO_NATIVE_TIMING=1` (the *_ms columns in native-frames.csv and perf.csv go non-zero), n3t = n3 +
  `LEGO_NATIVE_TIMING=1`, n2s = n2 + `LEGO_NATIVE_PARALLEL_DRAWS=0` (game.log "Native draw batches: serial workers=");
  `"sys_csv": true`. PlanOnly `-Only n3t` at 06:32: ok (an unselected reference arm is fine), warm-up raised 30 -> 60 s
  by the floor, about 3 min, free RAM 7.59 GB.
- **#25 base (06:35:32-06:44:02, `harness-pair.ps1 -Job base`, log `build/agent8/scratch/base-pair.log`):** attract-base1
  on `build\baseline-bin` (exe FB922AC9 ok, rexruntime E01D4618 ok), `attract-long.txt` (4D35FAF4), 600 s cap, -GpuLog,
  cold, no args: `build/agent3/runs/20261122-063542-attract-base1`, 06:35:39-06:43:48, free RAM 7.46 GB, no build
  tools. Harness exit 1 ("CRASHED" from the [FATAL] minidump line); game exit 0 by WM_CLOSE in 1.74 s; 91/91 steps, 0
  timeouts; pad loaded and polled (GetState 13324, 36 with input). STUCK-LOCK: 1 episode (6 lines) at 06:39:22.996, CS
  0x84959edc, waiter 0x6, owner tid 0x0017 lr=83FB09F0; `hang-60748.dmp` 49,377,574 B (06:39:26), kept. Run 2 skipped
  (Agent 6's rule: the baseline shows the STUCK-LOCK too). route-report.txt written into the run dir (exit 1: FAIL "no
  crash" (1 dump) and "no watchdog/hang lines" (the STUCK-LOCK lines); the rest ok). attract-report
  (`build/agent8/scratch/attract-base1-attract-report.txt`): front end 220/534 at perf 67.66, H0 2823/366575 at perf
  165.66, flags excluding none, valid window True. fps per 10 s: 57-60 in the front end, then 38 50 32 16 9.0 0.8 2.8
  6.1 ..., about 24 at 766 draws; the 0.8 bucket is the STUCK-LOCK. Agent 3's sampler rows 06:35:39-06:43:48 (199):
  total CPU 97.74/100 %, MsMpEng 1.35/3.04 cores, PresentMon 1.01, dwm 1.09, game 2.21/3.55 cores. Log 707 lines: 143
  warnings, 5 errors, 1 critical, no unknown cvars. Agent 3 (`build/agent3/logs/base25-attract-base1.txt`): STUCK-LOCK
  at +219.0 s, same owner (obj 0x30111018, tid 0x17), lr 83FB09F0, same waiter chain as devoffB/devoff3, dump at
  +222.6 s. So the CS 0x84959edc stall happens on the baseline too.
- **q (`harness-pair.ps1 -Job q`, log `build/agent8/scratch/q-pair.log`):** started 06:44:08; gate tries 1-8
  (06:44:42-06:48:15) all not quiet: total CPU mean 45-76 % (max 70-98 %), MsMpEng max 2.0-3.7 cores every try (limit
  0.2). Results below.
- Agent 3's `build/agent3/patches/run-timing-inputscript.patch` (base 75F4B527, patched 2E99CDDB) is for after window 4
  only: with today's vpadhost.cs a second -InputScript run in one run-matrix process exits 1.
- **q called off by Agent 3 (06:52):** "q off: MsMpEng won't get under 0.2 cores by 07:06". Gate stopped at 06:52:16 after
  15 tries (06:44:42-06:51:47), none quiet: total CPU 45-76 % mean (max 60-98 %), MsMpEng max 2.0-3.7 cores in every
  try. No q game was started (q launcher task killed; no harness-pair q process left). Agent 3 records q as not run.
- **3b, Agent 7's zero-code checks (zero-waiter.ps1, 06:52:27-07:00:02, all status OK, exit 0, functional only on the
  hidden desktop):** read with `build/agent8/scratch/zero_check.py` (game.log pattern counts, the *_ms columns of
  native-frames.csv and perf.csv, sys.json, dumps); references are Agent 4's 0452 rows (0454-n2-r1, 0456-n3-r1).
  - n2t `build/agent8/matrix/20261122-0652/runs/0652-n2t-r1` (06:52:27-06:54:59, WM_CLOSE exit after 5.04 s):
    TIMING works: texture_ms, present_cpu_ms, frame_slot_wait_ms, acquire_cpu_ms, present_submit_cpu_ms non-zero in
    17917/17917 rows and bindings_ms, begin_ms, pipeline_ms in 15296/17917 (the 0454 n2 row: only interval_ms and
    swap_present_cpu_ms non-zero). "Native draw batches: parallel workers=2", threaded recording ON, hash=0 misses 0,
    [error] 0, [FATAL] 0, STUCK-LOCK 0, no dumps.
  - n3t `build/agent8/matrix/20261122-0655/runs/0655-n3t-r1` (06:55:03-06:57:30, 2.66 s close): the same columns go
    non-zero (17381/17381; bindings/pipeline 14454, begin 14447); no "Native draw batches" line (as n3); threaded ON,
    hash=0 0, [error] 0, STUCK-LOCK 0, no dumps.
  - n2s `build/agent8/matrix/20261122-0657/runs/0657-n2s-r1` (06:57:34-06:59:59, 0.95 s close): game.log "Native draw
    batches: serial workers=2" (06:57:50.243); *_ms columns as without TIMING; threaded ON, hash=0 0, [error] 0,
    STUCK-LOCK 0, no dumps.
  - perf.csv has no column ending in `_ms` in any of these runs (or the 0452 rows), so only native-frames.csv shows the
    TIMING change. sys.csv and sys.json in all three (about 19 KB each); window flags not_foreground only (hidden
    desktop; not excluding there); util 103.1 / 86.6 / 78.9 %, effective clock 1750 / 1458 / 1332 MHz.
  - Last run ended 07:00:02; "last run ended" posted to all (the build all-clear for Agent 2, the scan go-ahead for
    Agent 9, Agent 3's patches, Agent 4's s35 pack).

## W4b read-out procedure (Agent 1, 07:08; one procedure with Agent 7's #29 add-on)

Status: written 07:30. **Agreed with Agent 7 at 07:40** (#29): the floor 0.02 is fine inside this procedure; no JSON key
changes tonight and w4b_readout.py stays frozen; Agent 7 re-ran the current file with this procedure's arguments on the
three dry folders and got JSON identical to mine (0 differences, `command` excluded). Agent 7's standalone command
(07:28) is step 3 below with `-o bench\agent7\w4b_readout\out-<dir>.md --json ...out-<dir>.json` and its own default
floor (0.015 since 07:24); this procedure passes `--scene-floor 0.02` and writes into the read-out dir instead.
This procedure replaces the 5-step list "Window 4 read-out (after the user's run)" above: all five steps are
in it (summary/results -> R0/R1, timerq -> R3, matrix_recheck -> steps 1-2, phase_switch -> R4, the d11t lines -> R7).
Of the tools below only matrix_recheck.py is in the hashed W4b chain (it is run unchanged); running them changes no chain
file (the real read-out's `--write` adds recheck.md to the matrix output dir only).
Agent 1 will re-issue the read-out as a new task after the user's run (~10:45).

### Inputs

- `D = build\agent8\matrix\<yyyyMMdd-HHmm>`: the newest folder after the double-click (the end screen names it).
  Expect 17 rows: 1 cold d0 run (unscored), then d0/B/d3/d11t x 4 rounds (Latin square) = 16 scored runs. The window
  is 60-110 s after the first frame (50 s).
- Used from D: results.csv (fg_share, flags_excluding/flags_info, valid_timing), summary.md, matrix.json and per run
  run.json, frames.json, perf.csv, sys.csv, proc.csv, game*.log.
- Tools: `bench\agent8\run\matrix_recheck.py` (in the W4b chain, run unchanged), Agent 7's
  `bench\agent7\w4b_readout\w4b_readout.py` (#29; frozen tonight: 07:24:09, 48,449 B, sha256 7C7A0673...7A284B0B; its
  self-test 12/12 OK at 07:27; since 07:18 only its markdown text and defaults changed), Agent 11's
  `bench\agent11\timerq_slowstate.ps1` (frozen tonight), and mine: `build\agent8\scratch\phase_switch.py`,
  `build\agent8\scratch\w4b_rules.py` (the pass rules), `build\agent8\scratch\w4b-readout.ps1` (all steps in one go).
- Mine, frozen until the read-out (sha256): w4b_rules.py EB33EEC7...06A7EA67 (21,505 B, 07:26:42), w4b-readout.ps1
  03C218B0...DDF0D6D3 (3,129 B, 07:19:42), phase_switch.py 20C77389...CDBE593E (5,101 B, 04:06:18). The dry runs set
  PYTHONDONTWRITEBYTECODE=1 and wrote nothing into bench (the two .pyc files in `bench\agent8\run\__pycache__` date
  from 03:45 and 04:24, before this work; left as they are).
- Window-3 reference values (`20261122-0013`, foreground, no sys.csv): d0 draws/frame p50 226 in every scored window,
  d0 leave-one-out scene distance 0.000 (x4), d0 fps 161.5-167.3 (spread 3.5 %), p50 6.98-7.10 ms; phase switch at
  32-33 s and 0.0 % light frames in every normal window; game 3.1-3.5 cores (add-on, proc.csv); the one light-phase run
  0025-d11-r1: 218 draws, 294.6 fps, no switch, 100 % light, scene distance 0.036.

### Environment note (Agent 8, 12:45, board run 2: Windows Update restarts at 08:29 and 08:34, after window 3)

- Installed after window 3 (System log, WindowsUpdateClient): Intel extension drivers 9.1.10501.3322 (DTT), 3.4.1009.0
  (IPF, x4) and 20.3.2.1007 at 08:29:44-54; KB5132057 (2026-11 preview, build 26300.10075) and the .NET Framework
  preview KB5137006 at 08:35:46; Defender intelligence 1.463.417.0 at 08:46. The base drivers did not change: DTT
  9.1.10010.2297, IPF 2.3.20306.4, NVIDIA MX570 32.0.16.1088.
- W4b's Latin square stays internally comparable, because all 17 runs come after the update. Any cross-window comparison
  (window 3 `20261122-0013`, the overnight runs) must say it crosses this update. DTT and IPF set the CPU power and
  thermal policy, so the absolute fps level can move, d0 included.
- Same as before the restart (read-only checks 12:37-12:45): AC, Balanced, effective overlay best_efficiency (as in
  every sys.csv 03:30-06:57), LdSys-b452d258.dll cached, no thermal-zone instances (tz columns blank). Different:
  free RAM is 14.1 GB (window 3's plan: 8.98 GB).
- Evidence: `build\agent8\readout\w4b-readiness-1237.txt`, `w4b-readiness2-1242.txt`, `w4b-planonly-1237.txt`.
- Standby re-check 15:05-15:07 (Agent 8, #10, read-only): bench\agent8, build\agent8 outside readout\ and the 8 harness
  files match the 13:11 baseline (3,654 rows); the W4b closure (53 files, bins hashed) is unchanged; LdSys cache OK; free
  RAM 13.6 GB, C: 263 GB free; no reboot pending; newest matrix folder still `20261122-0657`. Evidence:
  `w4b-standby-compare-1505.txt`, `w4b-readiness-1505.txt`, `w4b-readiness2-1505.txt` (same folder).

### One command (after the user's run; about 15 s, one process at a time)

```
powershell -NoProfile -ExecutionPolicy Bypass -File build\agent8\scratch\w4b-readout.ps1 -Stamp <yyyyMMdd-HHmm>
```

- Output dir `build\agent8\readout\<stamp>\`: **rules.md (read first)**, w4b.md and w4b.json (the add-on), recheck.txt
  (plus `D\recheck.md`), recheck-dropslow.txt, timerq.txt, phase.txt and phase.json, a copy of summary.md, one log per step.
- It prints one line per step (name, exit code, seconds) and exits 1 with `FAILED steps: ...` if any step fails.
- `-All` (keep FUNCTIONAL ONLY runs) and `-NoWrite` (no recheck.md in D) are for functional dry runs only; the real
  read-out uses neither. `-ExpectRows` defaults to 17, `-SceneFloor` to 0.02.

The same by hand (`O` = output dir):

1. `python bench\agent8\run\matrix_recheck.py D --write > O\recheck.txt` (paired deltas per round, `slow` column)
2. `python bench\agent8\run\matrix_recheck.py D --drop-slow > O\recheck-dropslow.txt`
3. `python bench\agent7\w4b_readout\w4b_readout.py D --scene-floor 0.02 -o O\w4b.md --json O\w4b.json` (it also runs
   timerq_slowstate.ps1 `-Root build\agent8\matrix -Since <stamp>` as a subprocess)
4. `powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_slowstate.ps1 -Since <stamp> > O\timerq.txt`
5. `python build\agent8\scratch\phase_switch.py D\runs\<every run dir> --json O\phase.json > O\phase.txt`
6. `python build\agent8\scratch\w4b_rules.py D O --expect-rows 17 -o O\rules.md`

### Pass rules (w4b_rules.py; levels N/A < PASS < NOTE < DROP < FAIL)

DROP = runs left out of the result; FAIL = the read-out, or every verdict, cannot be trusted. The **decision column of
the R5 table is the result**; the overall line is the worst rule level.

| rule | check | outcome |
|---|---|---|
| R0 complete | rows >= 17; the add-on's per-run check (its numbers = frames.json = results.csv) ok on every run; every kept run has window stats; scored runs the add-on did not keep (status not OK, invalid timing, real problems) listed | short matrix: NOTE (find out why); check mismatch or missing stats: FAIL; not kept: DROP |
| R1 runner | flags_excluding (light_phase, window_before_floor; on the timing desktop also input_during_window, not_foreground, power/battery, desktop, screensaver) | DROP |
| R2 foreground | results.csv `fg_share` over the window: **fg=1 means >= 0.99**; 0 = never_foreground (the runner keeps it: info only, even on the timing desktop); 0-0.99 = not_foreground (runner-excluded there) | NOTE for never/partial |
| R3 slow state | slow state in the window (matrix_recheck `!` = add-on slow_win: E-cores < 800 MHz for 3+ sys.csv samples overlapping the window); a never-foreground run with any timerq onset | DROP; plus the N/M/K line below |
| R4 scene | every kept run, d0 included: draws/frame p50 within +-2 of the pooled d0 p50 (expect 226; NOTE if the pool differs), no add-on SCENE? flag (threshold max(0.02, 2 x largest d0 leave-one-out)), light frames in the window <= 1 % (phase_switch); one summary line per arm; switch outside 25-40 s only a NOTE | failing run: DROP; 2+ failing runs in an arm: no verdict for that arm |
| R6 background | add-on: background = busy cores - game cores per window; SAT = median busy share >= 0.97; BG+ = not SAT and > reference + 1.0 core (reference = median of this matrix's unsaturated scored runs, window 3 has no sys.csv) | BG+ runs and SAT runs: DROP (as in the add-on's clean table); every kept run SAT: FAIL |
| R7 d11t | every d11t run: `Host timer resolution set to 1 ms` in game*.log and run.json env_set `REX_TIMER_WAIT_BLOCKING=1` | FAIL = no d11t verdict |
| R5 result | arms over the runs left: median (min..max) of fps, p50, p99, 1 % low, >33 ms/min; better/worse vs d0 only when every run lies outside d0's min..max, else overlap; paired fps by round (support only); the runs left compared with the add-on's clean set | no verdict when: 2+ off-scene runs (scene), R7 fails, arm n < 3, d0 n < 3, or R6 fails; round-1 run > 1 % outside rounds 2+: NOTE |

### Agent 1's two items

1. **B vs d0 scene check.** Pass: every B run within +-2 draws/frame of the pooled d0 p50 (226 expected), scene distance
   <= the add-on threshold (0.02 unless the d0 runs disagree among themselves), light frames <= 1 %. Read R4's line
   `B vs d0: 4 kept runs, scene distance median .. (max ..) vs threshold .., draws p50 ../../../.., light in window max
   .., off-scene N`. One off-scene B run is dropped and B is judged on 3 runs; with 2 or more the B row reads
   `no verdict (scene)`. The same line exists for d3 and d11t, and for d0 itself (leave-one-out).
2. **timerq_slowstate over the fg=1 runs.** fg=1 comes from results.csv fg_share (window only). timerq's own fg column is
   the set of fg_game values from the first frame to the exit, so a good run can read `1/0` because of the close; R3
   notes an fg=1 run whose timerq fg has no 1. R3 prints `fg=1 runs: N=.., with any onset (timerq) M=.., in the window
   K=..`. Expected: N = 16, K = 0 (Agent 11: the slow state is a power-management effect on a never-foreground process;
   window 3 was foreground and had no slow 10 s bin). K > 0: report to Agents 1 and 11 (those runs are dropped anyway);
   M > K (an onset after the window, e.g. during the close) is reported, not dropped.

### Scene floor 0.02 (agreed with Agent 7; the add-on's own default is 0.015 since 07:24, 0.15 before)

- Distances: normal windows 0.000 (window 3: d0 leave-one-out 0.000 x4, every base and normal d11 run 0.000); +-1 draw
  jitter about 0.005 (add-on doc); 0342's quick windows 0.002-0.011; windows about half in the light phase 0.0165 and
  0.0187 (0013's unscored cold runs: 56 % and 65 % light frames, draws p50 226 and 219); the light-phase run 0.036.
- With 0.15 the light run is not flagged: Agent 7's out-0013.md of 07:21 (floor 0.15) shows d11 = 159.0 (157.5..294.6)
  fps, spread 86.2 %, `-2.3% overlap`. With 0.02 (or 0.015) it is flagged, and d11 = 157.8 (157.5..160.3), n = 3,
  -3.1 % worse, paired -2.8 % (0 of 3 rounds up).
- At 0.02 the scene check alone misses half-light windows (Agent 7's caveat; 0.015 would flag the two cold runs above).
  R4's light rule (<= 1 % light frames) catches them, and the draws rule catches the 219 one, so the procedure drops
  them either way.
- A reference run cannot be flagged by the add-on (the threshold is at least 2 x its own leave-one-out distance), so
  one off-scene d0 run raises the threshold for every arm. R4's draws-p50 and light rules apply to every kept run,
  d0 included, and cover that case. Agent 7 fixes this after W4b only (median leave-one-out, flag d0 runs over the
  threshold, pool without them); no change tonight.

### What to report to Agent 1

Per arm: n left, fps median (min..max), the decision line and the paired fps; R3's N/M/K line; R4's B line; R6's
background line; every FAIL and DROP with its reason; whether the runs left equal the add-on's clean set. Timing
claims only from rows with `verdict:`; `overlap` = no measurable difference at n = 4.

### Dry runs (07:13-07:27, existing data only, no game runs, one process at a time)

All wrapper steps exit 0 on the three folders (re-run 07:22 after the `1%%` fix; rules re-run 07:26 with the add-on's
background column).

- **0013** (window 3, `-NoWrite -ExpectRows 19`): R0 PASS (19 rows, 16 scored, 16 kept, check ok); R2/R3/R6 N/A (no
  sys.csv); R4 drops 0025-d11-r1 (draws 218 vs 226; SCENE? 0.036 > 0.020; light 100 %; no switch); n0 rows "no guest
  draws" (native frames); R5: d0 162.9 (161.5..167.3) reference; base 160.8, -1.3 % worse, paired -1.4 % (0/4); d11 n = 3
  157.8, -3.1 % worse, paired -2.8 % (0/3); n0 143.2, -12.1 % worse; runs left = the add-on's clean set; R7 N/A (d11,
  not d11t). Arm fps equal run-matrix's summary (add-on check: d0 162.857 vs 162.858).
- **0342** (W4b `-Quick`, hidden desktop, build tools in 3 runs, `-All -ExpectRows 5`): R0 NOTE (4 functional runs);
  R2 0 of 4 fg=1 (never_foreground, hidden desktop); R3 drops d0, B, d3 (slow state in the window, onsets 39 / 29 /
  37 s); R4 drops d0t (67 % light frames: quick windows straddle the switch) and notes the pool p50 219; R6 FAIL (every
  window SAT, background about 10 cores); R5 FAIL (d0 0 runs left); every row `no verdict (no runs left)`.
- **0349** (`-All -ExpectRows 3`): R3 drops all three (onsets 69 / 42 / 61 s in the window); R4 PASS (draws 226, 0 %
  light); R6 FAIL (all SAT); R7 PASS (0352-d11t-r1: one 1 ms line, REX_TIMER_WAIT_BLOCKING=1); R5 FAIL.
- `matrix_recheck --drop-slow` agrees (all three 0349 runs dropped); timerq `-Since 20261122-0330`: 20 runs, fg 0 in all.
- Bugs found and fixed in my tools: the `%` in the R5 header (`1%%`); the add-on's `loo` is a list and `scene_loo` a
  flag (the distance is scene_d); a single PowerShell `Tee-Object` has no -Encoding in 5.1 (dry script uses Out-File).

## W5 read-out: status note 17:09 (history; superseded by "W5 read-out procedure" below, 17:25)

Kept as the record of the 17:09 position (agy-grid restart). Its open items are done in the section below, except the
work that needs Agent 1's 'go' (the W4b read-out, then the tests of the W5 tools). No 'go' yet: file tools only, nothing
run, no subagents, no W5 input touched; `perf-notes/WINDOW-HOLD.txt` absent at 17:07 and 17:16.

- **Done:** `build\agent8\scratch\w5_rules.py` (17:01, 638 lines, not tested yet; testing waits for 'go'). It is
  w4b_rules.py with these changes:
  - R0 counts the scored runs per arm.
  - R3 counts onsets per TimerQueue mode and cross-checks `--timerq3`.
  - R4 adds a NOTE when the reference pool is not at 226 draws/frame.
  - R7 proves each run against its arm's matrix.json entry: cvars, env_set keys, bin, the 1 ms line, exactly one
    precise line (d11p), REX_TIMER_WAIT_BLOCKING presence, and TimerQueue CPU from threads.csv.
  - R5 compares against the reference (base) and adds a pair table. Default pairs: d11:s0, d11t:s0, d11p:s0,
    d11t:d11, d11p:d11t, d11p:d11.
  - It reads the add-on JSON `w5.json` and falls back to w4b.json.
- **Agent 11's 3-mode copy exists** (#35, 17:02): `bench\agent11\timerq_slowstate_3mode.ps1 -Matrix <stamp>
  [-OutCsv <path>]`. Modes are precise / blocking / spin / unknown, with flags and a MIXED mark per arm.
  w5_rules.py's `--timerq3` parser reads the script's printed table (whitespace columns: matrix, run, arm, mode, ...).
  So the wrapper saves stdout as `O\timerq3.txt` and passes that file. The CSV is quoted, so the parser can't read it.
- **TimerQueue gate, from W4b threads.csv** (`20261122-1541`):
  - d11t (blocking, devoff2): 6.0 / 5.0 / 5.1 / 5.6 % of a core in r1-r4 (max 1 s 11-18 %).
  - Spin runs: 41-56 % (r1: d0 47.2, B 41.4, d3 55.5).
  - The README gate `< 5 %` (expected 0.3-1.5 %) would fail every W4b d11t run. So w5_rules.py uses
    `--tq-wait-max 15` and `--tq-spin-min 20`.
  - matrix-window5-s3d.json's notes still say `< 5 %`. It is a W5 input, so I've left it as it is; the read-out
    reports the measured values instead. Agent 11 has been told.
- **Light share (to confirm after 'go'):** the runner's results.csv `light_share` is based on frame time (frames under
  4.5 ms; my 16:54 reading). If so, W4b's `light_share_high` flags come from the ~240 fps rate, not from the light phase.
  R4 uses phase_switch's draws-based `light_win` (draws < 222) instead.
- **Next, with file tools until 'go':**
  - Write this section in full: inputs, one command, rules table and report list, modeled on the W4b section above.
  - Write `build\agent8\scratch\w5-readout.ps1` with the w4b-readout.ps1 steps, changed as follows:
    - timerq_slowstate_3mode.ps1 `-Matrix <stamp>` into `O\timerq3.txt`;
    - the add-on with `-o O\w5.md --json O\w5.json`;
    - w5_rules.py with `--expect-rows 16 --timerq3 O\timerq3.txt`;
    - an optional add-on pass with `--ref s0 --no-timerq`.
- **After 'go':** the W4b read-out (item 1) comes first. Then a dry run of w5_rules.py on `20261122-1541` (ref d0; the
  pairs are skipped).


## W5 read-out procedure (Agent 8, #26; written 17:20-17:25 with file tools only)

Status: written before Agent 1's 'go', so none of these tools has run yet; the tests are in the last subsection.
**Position for the agy-grid restart (17:25):** w5_rules.py edited (env_set read as a dict or 'K=V' strings, a guard for
runs without stats, a header-based `--timerq3` parser that also reads `unknown`, `--no-drop`, a NOTE at the README's 5 %
gate); `build\agent8\scratch\w5-readout.ps1` written; both untested. After 'go': the W4b read-out (#26 item 1) first,
then the tests below. Nothing here changes a W5 input (Agent 1's list `build\agent1\w5\W5-INPUTS-1642.txt`, 27 files):
matrix_recheck.py is the only one used, unchanged and without `--write` by default, so the read-out writes nothing into
W5's matrix folder. Built on the proof-and-gates table in `build\agent8\readout\w5-draft\README.md` (L47-67) and on the
W4b procedure above.

### Inputs

- `D = build\agent8\matrix\<yyyyMMdd-HHmm>`: the newest folder after the W5 double-click (`bench\agent8\RUN-WINDOW5-S3D.cmd`;
  the end screen names it). Expect 16 rows: 1 cold base run (unscored, 30 s window), then 3 rounds of the 5 arms = 15
  scored runs, rotated each round: `base s0 d11 d11t d11p | s0 d11 d11t d11p base | d11 d11t d11p base s0`. Every
  window: 5 s settle + 55 s warm-up from the first frame, then 50 s measured (60-110 s after the first frame).
- Arms (`bench\agent8\run\matrix-window5-s3d.json`; reference base, Agent 1 14:23):

| arm | bin | cvars besides framerate_limit=0 | env | TimerQueue wait |
|---|---|---|---|---|
| base (ref) | devoff3 = S3d (W4b's d3 bin) | none | none | spin |
| s0 | devoff4 = S4a, every new switch off | none | none | spin |
| d11 | devoff4 | the 8 timer cvars | none | spin |
| d11t | devoff4 | the 8 timer cvars | REX_TIMER_WAIT_BLOCKING=1 | blocking |
| d11p | devoff4 | the 8 timer cvars + timer_queue_precise_wait=true | none | precise (wins over the env var) |

- Used from D: results.csv, summary.md, matrix.json, and per run run.json (params.cvar, params.env, env_set, bin_dir),
  game*.log, threads.csv, frames.json, perf.csv, sys.csv, proc.csv.
- Tools: `bench\agent8\run\matrix_recheck.py` (a W5 input, run unchanged); Agent 7's
  `bench\agent7\w4b_readout\w4b_readout.py` (frozen, sha256 7C7A0673...7A284B0B; reference from matrix.json = base,
  `--ref s0` for the support pass); Agent 11's `bench\agent11\timerq_slowstate_3mode.ps1` (#35; the original stays frozen
  as a W4b input); mine: `build\agent8\scratch\phase_switch.py`, `w5_rules.py` (the pass rules), `w5-readout.ps1` (all
  steps).
- Environment: as in W4b, every W5 run comes after the 08:29-08:34 Windows Update (environment note above), so W5 compares
  with W4b; anything older must say it crosses the update. base runs W4b's d3 bin with the same window, so base against
  W4b's d3 (248.9 fps median, 198.4..298.6) is a drift check between the two windows, not a verdict.

### One command (after Agent 1 says W5 is done; about 25 s, one process at a time)

```
powershell -NoProfile -ExecutionPolicy Bypass -File build\agent8\scratch\w5-readout.ps1 -Stamp <yyyyMMdd-HHmm>
```

- Output dir `build\agent8\readout\<stamp>\`: **rules.md (read first)**, rules-nodrop.md (sensitivity pass), w5.md and
  w5.json (the add-on, reference base, per-run 10 s bins), w5-s0.md and w5-s0.json (the add-on with `--ref s0`, support
  only), timerq3.txt and timerq3.csv, recheck.txt, recheck-dropslow.txt, phase.txt and phase.json, a copy of summary.md,
  one log per step.
- It does not start while `perf-notes\WINDOW-HOLD.txt` exists and stops before the next step if the file appears. It
  prints one line per step (name, exit code, seconds) and exits 1 with `FAILED steps: ...` if any step fails.
- Switches: `-All` as in W4b (functional dry runs only); `-Write` = matrix_recheck `--write` (adds recheck.md to D; off by
  default here, unlike W4b); `-ExpectRows` (16), `-SceneFloor` (0.02); `-Pairs` goes to w5_rules.py `--pairs`;
  `-NoS0Pass` skips the s0 pass (skipped anyway when matrix.json has no s0 arm); `-OutDir`.

The same by hand (`O` = output dir):

1. `python bench\agent8\run\matrix_recheck.py D > O\recheck.txt`
2. `python bench\agent8\run\matrix_recheck.py D --drop-slow > O\recheck-dropslow.txt`
3. `python bench\agent7\w4b_readout\w4b_readout.py D --scene-floor 0.02 -o O\w5.md --json O\w5.json` (it also runs the
   original timerq_slowstate.ps1 for onset and fg; the wait mode does not matter there)
4. `python bench\agent7\w4b_readout\w4b_readout.py D --ref s0 --no-timerq --scene-floor 0.02 -o O\w5-s0.md --json O\w5-s0.json`
5. `powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_slowstate_3mode.ps1 -Matrix <stamp> -OutCsv O\timerq3.csv > O\timerq3.txt`
6. `python build\agent8\scratch\phase_switch.py D\runs\<every run dir> --json O\phase.json > O\phase.txt`
7. `python build\agent8\scratch\w5_rules.py D O --expect-rows 16 --timerq3 O\timerq3.txt -o O\rules.md`
8. step 7 with `--no-drop -o O\rules-nodrop.md`

### Proof first (R7; the README's proof-and-gates table)

Read R7 before any fps. w5_rules.py takes each run's expectations from its arm's entry in `D\matrix.json`:

| arm | 1 ms line | precise-wait line | REX_TIMER_WAIT_BLOCKING in env_set | TimerQueue % of one core: README expected (gate) | read-out gate |
|---|---|---|---|---|---|
| base | none | none | absent | 30-60 (spin) | > 20 |
| s0 | none | none | absent | 30-60 (spin) | > 20 |
| d11 | >= 1 | none | absent | 30-60 (> 20) | > 20 |
| d11t | >= 1 | none | `1` | 0.3-1.5 (< 5) | < 15; NOTE from 5 |
| d11p | >= 1 | exactly 1 | absent | 1-2 (< 5) | < 15; NOTE from 5 |

- Lines in game*.log: `Host timer resolution set to 1 ms (background opt-out on)` and `TimerQueue: precise wait
  (timer_queue_precise_wait)`. TimerQueue CPU: threads.csv row `rex::thread::TimerQueue`, busy_pct over the driver window
  (max_busy_pct = the busiest 1 s).
- Also per run: params.cvar = the arm's cvars (as a set), env_set keys = the arm's env keys, bin_dir ends with the arm's
  bin (devoff3-bin or devoff4-bin). params.env keys that differ from the env_set keys: NOTE.
- Why 15 % and not the README's 5 %: W4b's d11t (blocking wait, devoff2) measured 6.0 / 5.0 / 5.1 / 5.6 % (busiest 1 s
  11.5-17.8 %), its spin runs 41-56 %. A 5 % gate would fail every W4b d11t run although the wait mode was right; 15 %
  is still about 3 times below the lowest spin run. Each wait-mode run at 5 % or more gets a NOTE, and the R7 table prints
  the measured values. The matrix JSON's notes still say < 5 % (a W5 input, left as it is; Agent 11 knows).
- The env var is presence-only. Leaked into base, s0 or d11, it would turn their spin wait into the blocking wait, and the
  spin gate catches that (TimerQueue near 5 % instead of 30-60 %). Leaked into d11p, it changes nothing (precise wins) and
  only env_set shows it, which R7 checks.
- CPU cannot tell d11t from d11p; only the precise line does.
- A scored run failing any check: R7 FAIL, and its arm reads `no verdict (proof)` in every R5 row it is in. The cold run
  is reported only.

### Pass rules (w5_rules.py; levels, R1, R2 and R6 as in W4b)

| rule | W5 |
|---|---|
| R0 complete | 16 rows (1 cold + 15 scored); scored runs per arm, 3 each expected (NOTE if they differ); kept runs without complete window stats: FAIL, and they are left out of R5 |
| R3 slow state | as W4b (DROP), plus the onsets per TimerQueue mode (from the arm config) and timerq3's mode per run against the arm config (a mismatch, a missing row or `unknown`: NOTE). timerq3.txt also lists its flags (no_log, precise_lines>1, env+precise, precise_cvar_no_line, precise_line_no_cvar) and MIXED arms: expect none, with base/s0/d11 spin, d11t blocking, d11p precise |
| R4 scene | as W4b with base as the pool; NOTE when base is not at 226 draws/frame (226 came from window 3's devoff2; then check base by hand) |
| R7 proof | the table above |
| R5 result | main table: each arm against base. s0 vs base = the S4a effect (devoff3 -> devoff4, every new switch off); d11, d11t, d11p vs base = S4a plus the timer settings. Pair table, same decision rule with the second arm as the reference: d11 vs s0 (the 8 timer cvars), d11t vs s0 and d11p vs s0 (the cvars plus the wait mode, one bin), d11t vs d11 (the blocking wait alone), d11p vs d11 (the precise wait alone), d11p vs d11t (precise against blocking) |

- No verdict for a row when either arm has 2+ off-scene runs, fails R7 or has n < 3, or when R6 fails.
- n = 3: better/worse needs all 3 runs outside the other arm's min..max. In W4b the spread inside one arm was 26-50 % of
  its slowest run (d0 213.9..270.4, d3 198.4..298.6 fps), so expect `overlap` unless an effect is large. `overlap` = no
  measurable difference at n = 3, not "the same". The paired fps by round (each round has every arm) is support only.
- rules-nodrop.md: R5 over every kept run with the R3/R4/R6 drops ignored (R7, n and scene rules still apply): the "with
  and without the flagged runs" answer.

### light_share_high is not the light phase (checked 17:17 in W4b's run.json)

- results.csv `light_share` = the share of window frames under `light_ms` 4.5 ms; run.json `light.rule`:
  "light_share_high = share_lt_light >= 0.6 (info)". At 200-320 fps most frames are under 4.5 ms: W4b flagged 13 of 17
  rows (0.60-0.92), and the 4 rows without the flag are its slowest windows (198-221 fps, 0.51-0.60).
- It is info only (flags_info). The excluding rule is light_phase (install_dat_fail < 30; 34 in every W4b row). R4 uses
  phase_switch's draws-based light_win (draws < 222), which does not depend on the frame rate.

### What to report to Agent 1 (W5)

- R7 first: per arm, the 1 ms and precise lines, env, TimerQueue median (min..max); every FAIL with its reason.
- Per arm: n left, fps median (min..max), the decision against base and the paired fps; then the pair table's decisions
  (d11, d11t, d11p vs s0; d11t vs d11, d11p vs d11, d11p vs d11t).
- R3's N/M/K line, the onsets per mode, and whether timerq3 agrees (flags 0, MIXED 0).
- R4's per-arm scene lines (base's draws p50), R6's background line, every DROP with its reason, and the rows where
  rules-nodrop.md decides differently.
- base against W4b's d3 (same bin): the drift between the two windows.
- Timing claims only from rows with `verdict:`.

### Tests before the real read-out (after 'go'; light work, one process at a time)

1. Dry run on W4b: `w5-readout.ps1 -Stamp 20261122-1541 -ExpectRows 17 -OutDir build\agent8\readout\w5-dry-1541`
   (reference d0; the pairs are skipped and listed; no s0 pass). Expect: every step exits 0; R7 PASS on d0, B and d3
   (spin) and on d11t (blocking, with a NOTE each for 5.0-6.0 %); timerq3's modes = the arm config; R5's main table = the
   W4b read-out's (`build\agent8\readout\w4b\rules.md`).
2. Made-up proof cases, in copies under `build\agent8\scratch\` (never in D): REX_TIMER_WAIT_BLOCKING in a d11p run's
   env_set, a d11p game.log with 0 and with 2 precise lines, a d11 run without the 1 ms line, a spin run at 5 %
   TimerQueue. Each must FAIL R7.

## W5 read-out procedure: addendum 20:40 (Agent 7's final noise method; run-2 #7)

This adds step 9 to the procedure above (L920-1058). Steps 1-8 stay as written. Step 9 changes which CI table is read first.

9. **Agent 7's noise method** (`build/agent7/w4b-noise/RESULTS.md`). It is read-only on the matrix. Run it at Below Normal, one script at a time:
   - `cmd /c start "" /belownormal /b /wait python -B build\agent7\w4b-noise\noise_methods.py build\agent8\matrix\<stamp> -o <out>\noise\report-<w>.md --json <out>\noise\report-<w>.json`
   - `cmd /c start "" /belownormal /b /wait python -B build\agent7\w4b-noise\noise_case.py <out>\noise\report-<w>.json -o <out>\noise\noise-case-<w>.md`
   - Record both sha256s. At 20:27 they were:
     - noise_methods.py `A29AF4795AFE5DF53E957AC846327290859A59237FA6CE745E4D5608F320B4AF`;
     - noise_case.py `1F3C467E264C3211C3EF4B0D94F6454ADCAB2021659489FB2B1C1DF83B23D152`.
   - **The primary table is T-std.**
     - Split each run's frames at the runner's 4.5 ms light threshold.
     - Re-mix them at hT_ref, the median heavy-time share of the kept runs.
     - Then compute fps, p50, p99 and 1 % low.
     - One-way model, df = runs − arms.
   - **B-block T-std replaces it as primary when the round terms are about 3 % or more.** It is arm + round, with df = runs − arms − rounds + 1. In W4b, rounds 2-4 were 3.1-4.0 % faster on median ms. In W5 the median-ms round terms were +0.8 and −0.2 %, but the tail terms were 3-7 % (see "tstd-xcheck result" below), so choose the model per metric.
   - **Guards:**
     - (a) light share per arm, one-way F: no arm may move the light/heavy mix;
     - (b) every T-std delta must lie inside its raw GM CI;
     - (c) the host flag (P util ≥ 90 % and E < 600 MHz) lists the flagged runs and their mean excess. It is a warning, not a correction.
   - **Reading:**
     - Verdicts stay R5's: better or worse only when every run lies outside the reference's min..max.
     - A T-std CI that excludes 0 is a lead, to be tested in a later window. Each arm has n = 3, and there are 16 or more tests.
   - **Cross-check:** an independent recompute of the per-run T-std values and the CIs. For run-2 #7 it is in `build/agent8/readout/tstd-xcheck/`.

## W4b and W5 read-out results (run-2 #7, 19:33-20:45)

**W4b** (build/agent8/matrix/20261122-1541) → build/agent8/readout/w4b/READOUT.md

- **Strict:** FAIL, no verdict.
  - R0 drops run 6.
  - R3 drops 16/16.
  - R6: background 8.14, with SAT runs.
  - R5 has no d0 run left.
- **Nodrop variants** (R5 rule), fps vs d0. Every row reads overlap:

  | variant | B | d3 | d11t |
  |---|---|---|---|
  | all runs | +6.4 % | +3.8 % | −0.8 % |
  | without run 6 | +15.1 % | as all runs | as all runs |
  | without the flagged runs | no verdict (n = 2) | no verdict (n = 1) | +6.3 % |

- **d11t game CPU −15.3 %: better in every variant** (2.81-3.00 cores, against d0's 3.34-3.53).
- **B-block T-std:**
  - B fps +6.0 % [+0.5, +11.8]\*: a hint for codegen B (n = 3), and a fragile one (leave-one-out keeps the star in 3 of 7 cases);
  - d3 +2.3 % and d11t +2.5 %, both n.s.
- **Disturbance audit:**
  - The flagged runs are not more loaded.
  - The only candidate is run 10's unlogged warm-up load: 16:00:31-16:01:20, ng_u 8.36 against 5.62-7.59. Run 10 is already in the flagged set.
  - At comparable clocks, W4b carried about 1-3 nominal cores more non-game work than W5.

**W5** (build/agent8/matrix/20261122-1756) → build/agent8/readout/w5/READOUT.md

- **Strict:** FAIL. R3 drops 15/15, and R6 drops 1821.
- **Nodrop:** every arm overlaps base. fps: s0 −6.2 %, d11 −1.2 %, d11t −4.8 %, d11p −3.4 %.
- **T-std** (round terms +0.8 / −0.2 %, so one-way, df 10):
  - No median-ms or fps CI excludes 0.
  - d11t p99 +8.8 % [+1.0, +17.2]\* is the one CI that does: a lead that the blocking wait costs tail frames. B-block gives [+2.1, +15.9]. Without 1821 the deltas halve and no CI excludes 0 (see "tstd-xcheck result").
  - 1 % low: d11t −8.1 % and d11p −6.3 %, both n.s.
  - T-heavy 1 % low: d11t −8.5 %\* and d11p −11.0 %\*.
- **Game CPU:** better for both new wait modes, and 18/18 round pairs are lower. The saving is the TimerQueue spin.
  - d11t 2.72 cores (−13.7 %);
  - d11p 2.77 cores (−12.2 %).
- **Agent 1's host notes: confirmed**, with two qualifications:
  - "P saturation" means P util 91-98.5 %; P busy is 80-87 %.
  - Defender cannot be checked from the matrix.

**Both windows**

- **Slow state:** in the foreground in 16/16 W4b and 15/15 W5 runs, so R3 drops every run.
  - Suggested to Agent 11: instead of a binary drop, use a depth covariate (P util, E busy), the host flag, or T-std.
- **Tool hashes:**
  - add-on w4b_readout.py: EF1ABEC8. My notes freeze 7C7A0673; Agent 7 added the 10 s bins, and the cross-checker reproduces every number.
  - Agent 11's 3-mode slow-state copy: E9049B33 (Agent 11's PASS).
  - noise scripts: A29AF479 and 1F3C467E.
- **Tests:**
  - dry run on W4b;
  - TEST2 PASS (r7test);
  - W5 inputs re-hashed at 19:44: 27 files, 0 mismatches;
  - cross-checker: 666 numbers (W4b) and 1,017 (W5), 0 MISMATCH;
  - the noise rerun is identical to Agent 7's files;
  - the scanner, the auditor and Agent 6's logdiff agree;
  - tstd-xcheck (20:45): T-std and B-block recomputed independently, 0 MISMATCH (next section).
- **W6 promotion path:**
  - Agent 5's `build/agent5/w6-draft/finalize-w6.ps1 -Bin build/agent2/<name>-bin` (20:34) writes matrix-window6.json, RUN-WINDOW6.cmd and FINAL.txt in its own folder.
  - On Agent 1's word I run `build/agent8/w6-stage/promote-w6.ps1 -From build\agent5\w6-draft -Promote`. It checks FINAL.txt, the sha256s, the bin, the launcher rules and the .cmd, then copies both files byte for byte.
  - Then it runs -PlanOnly from bench\agent8 and checks the matrix folder count, hashes the inputs, and prints Agent 5's GO line. The reports go to build/agent8/readout/w6-promote/.
  - The pin freeze starts at 23:30 (Agent 1). Matrix JSONs and RUN-WINDOWn.cmd may still be added after it.

## tstd-xcheck result (20:45; run-2 #7)

My cross-checker subagent recomputed Agent 7's T-std and B-block T-std from the run files with its own numpy code: `build/agent8/readout/tstd-xcheck/` (tstd.md, tstd_runs.csv, tstd_compare.csv, tstd_xcheck.py). The W4b and W5 READOUTs were updated with it after 20:50.

- **Counts:** W4b 740/740 against report.json; W5 845/845 against report-w5.json; RESULTS.md 241/242. **0 MISMATCH.**
  - The other RESULTS.md cell is a definition difference: W4b's median-ms round terms (r2 / r3 / r4) are −4.04 / −3.09 / −3.90 %, i.e. 3.1-4.0 %. RESULTS.md's "3.1-4.1" is the same terms in log points. Fixed in the W4b READOUT and in step 9 above.
- **W4b, B vs d0, B-block fps +5.98 [+0.49, +11.77]\*: reproduced, but fragile.**
  - Leave-one-out keeps the CI above 0 in 3 of 7 cases. Without 1542-d0-r1, 1545-B-r1, 1611-d0-r4 or 1613-B-r4, the CI includes 0.
  - Paired by round: +14.7 / +1.3 / +4.6 % (r1 / r3 / r4).
  - B-block median ms: −2.51 [−4.96, +0.004].
  - Reading: a hint only.
- **W5, d11t tail:**
  - B-block 1 % low −8.08 [−14.16, −1.58]\* also excludes 0. RESULTS.md does not state it.
  - Against d11 (same bin; only the wait differs): p99 T-std +8.24 [+0.47, +16.61]\*, B-block +8.24 [+1.61, +15.30]\*; 1 % low B-block −7.73 [−13.82, −1.20]\*.
  - d11t is worse than base and than d11 in 3 of 3 rounds on p99 and 1 % low, with most of the size in r1 and r3. d11p points the same way by less, and its CIs include 0.
  - Without 1821-d11t-r3 (n = 2), no CI excludes 0: p99 +4.57 [−1.48, +10.99] and 1 % low −3.59 [−10.44, +3.78] (T-std, df 9); B-block +5.30 [−0.12, +11.00] / −4.85 [−10.20, +0.83] (df 7). These are 52 % and 44 % of the full-set deltas.
  - Reading: still a lead, resting largely on 1821 (host-flagged) and on round 1. W6 has no timer arms, so it needs a later window.
- **W5 round terms are not 0 for the tail:** p99 +3.11 / +5.72 % and 1 % low −3.14 / −7.32 % (r2 / r3), against median ms +0.77 / −0.17 % and fps −0.72 / −0.48 %.
  - **Refinement of step 9:** choose the model per metric. Use B-block T-std for a metric whose round terms reach about 3 %. There its CIs are narrower: W5's 4 vs 4 band is 5.63 against 6.67 % on p99 and 6.10 against 8.22 % on 1 % low.
- **Confirmed:** hT_ref W4b 0.531229 (1608-d11t-r4) and W5 0.212886 (1802-d11-r1); light-share F W4b 0.40 on (3, 11), p 0.76, and W5 0.33 on (4, 10), p 0.85.

## W6 promotion script tests and the devoff4b pre-test (21:10; run-2 #7)

- `build/agent8/w6-stage/promote-w6.ps1` (239 lines, parse errors 0):
  - T1, test mode on Agent 5's `check\` (devoff4-bin stand-in, MANIFEST 16DCC939…): OK, 7/7 match, 21/21 folders, 13 runs ~30 min, 29 inputs hashed.
  - T2 wrong MANIFEST sha (DEADBEEF): exit 1. T3 expect devoff4b on a devoff4 FINAL: exit 1. T4 -Promote on `check\` (PIPELINE CHECK): exit 1. T5 -Promote without -ExpectBin/-ManifestSha: exit 1, 4 reasons.
  - Fixes: the L114 parse error (`$wantExe:`); report stamp HHmmss (with HHmm, T2/T3 overwrote T1's report); a NOT OK report prints "GO line: none (result NOT OK)" and is named `promote-HHmmss-NOTOK.txt`.
  - Source guard (L45-46): -Promote reads only `build\agent5\w6-draft`. Every spelling of that folder passes (`\`, `/`, trailing slash, absolute, other case); `check\`, `build\agent8\w6pre4b` and a `..\` path to it are refused.
- devoff4b pre-test (21:02-21:09; the machine was at 100 %, so -PlanOnly took ~7 min at Below Normal):
  - Copied `finalize-w6.ps1` (B16267C3…), `matrix-w6.json` (D6388096…) and `RUN-WINDOW6.cmd.template` (CFE9973E…) from `build\agent5\w6-draft` into `build\agent8\w6pre4b` (with `TEST-COPY-NOT-FOR-PROMOTION.txt`) and ran the copy with `-Bin build/agent2/devoff4b-bin`: result OK, 13 runs (1 cold) ~30 min; notes[0] names exe DFBE1D43…; the cmd checks `build\agent2\devoff4b-bin\MANIFEST.txt`.
  - promote-w6.ps1 test mode on it (`-ExpectBin build/agent2/devoff4b-bin -ManifestSha DE11A914079D7DF7 -Force`): OK; MANIFEST 7 listed / 7 match, PASS 102 / FAIL 0, no unlisted files; folders 21/21; 29 inputs hashed (`w6-stage/test/promote-210906.txt`, `inputs-210906.txt`).
  - Negative: -Promote from w6pre4b with sha DEADBEEF: exit 1 with both reasons (source guard, sha); no bench writes (report moved to `w6-stage/test/neg/`).
  - The pre-test's matrix sha (BD0696DA…) is not for use: Agent 5's real finalize stamps its own time into the title, so its sha will differ.
- devoff4b-bin: MANIFEST DE11A914079D7DF7080CAA86B05DAE151CEFA017FDE15713CB85FA79F86339FA, exe DFBE1D43B28861A674663085B576E33B2D7E34D3D63A85CA480FF36CFE264B83. Agent 2's staging report (agent2-baseline.md L4) and Agent 1 match.

## F1 env keys for W8a, W8b and W9 (21:12; run-2 #7)

- `build/agent8/w8w9/ENV-KEYS-F1.txt`: 11 keys (the 2 already allowed + 9). The file has the arms per window, the bin string checks and the exclusions.
- W8b is not ready: LEGO_NATIVE_CHAIN_PRIORITY is in no bin (#21 is not built).

## W6 promoted, follow-up staging script, overnight plan (21:56-22:35; run-2 #7)

- **W6 promoted (21:56):** `bench/agent8/run/matrix-window6.json` E50D791B6C38638F718A1AF65EB15EAF543A78AC8EA50B69DD1CC96AB7C9A0D2 and `bench/agent8/RUN-WINDOW6.cmd` 3F31CBA8….
  - The promotion report is `build/agent8/readout/w6-promote/promote-215337.txt`.
  - Agent 1 wants RUN-WINDOW6.cmd left at `-Repeats 3`; it is only the double-click fallback.
- **W6 recheck at repeats=5 (22:09):** OK. 21 runs, runner ~48 min; folders 21/21; launcher B0902106… checked by its own functions (`build/agent8/readout/w-followup/stage-W6-220900.txt`). GO line sent to Agent 1 at 22:10: `GO W6 matrix-window6.json E50D791B…A0D2 only=s0,p2,p2f,p2fc repeats=5`.
- **`build/agent8/w-followup/stage-window.ps1`** (~442 lines) stages any follow-up draft:
  - It copies the draft byte for byte.
  - It runs the launcher's Parse-Go, Test-Matrix, Get-MatrixWarnings, Get-BinHashes and Get-Plan read-only.
  - It starts -PlanOnly only in a queue gap (Wait-QueueGap).
  - It checks the planned runs and writes `stage-<X>-<HHmmss>.txt` + `inputs-<X>-<HHmmss>.txt`.
- **Fixes to stage-window.ps1:**
  - StrictMode `.Count` on a 1-element if-expression: wrapped in `@()` at the `$toHash` and `$pins` sites.
  - Get-QueueState now treats any line after the last LAUNCH as "no game running", except toypad/attach (fixed 22:12). Before the fix, a REFUSED launch looked like a running game.
- **Tests of stage-window.ps1:**
  - Get-QueueState: 4/4 synthetic cases pass.
  - Batch from 22:10 (`tests-221054.txt`): PASS T1 W9 r4 (21 runs, runner 48), T2 W5b r6 three arms, T3 W5b r6 two arms. T4-T6 and N1-N6 are still running.
- **Queue lesson:** harness\guard.ps1 counts every run-matrix.ps1, -PlanOnly too, as a runner.
  - Other run-matrix processes caused 4 REFUSED queue launches: 22:04:30 and 22:04:52 (s4b24), 22:09:07 (s4b18), 22:14:14 (s4b20).
  - My -PlanOnly runs only made the queue wait:
    - ~16 s at 22:09:28 (old Get-QueueState took the refused s4b18 LAUNCH as running);
    - ~11 s at 22:14:34 (old code);
    - ~33 s at 22:22:37 (s4b20 died early with exit 1, at 471 of 600 s).
- **Finding 10 is load-related** (Agent 3, Agent 1): owner lr 83FAF200 in sub_83FAF180 hit s4b24 (p2fc) and the C1-off row s4b20. Both hits came under a -j 8 build at 100 % CPU. Nothing may compile during the windows.
- **Overnight plan rev 22:35** (`build/agent8/w-followup/PROPOSAL.md`):
  - Order: W6 r5, W9 r4 (gated on s4b17), W5b r6, W4c r6. With 10-min gates the night ends ~03:24, within Agent 1's ~03:30-04:00 target.
  - Each window has a latest GO for an end by 04:00.
  - W8a / W8a4 go to a Monday daytime session, with W8b and W10. W7 is Monday night at the earliest.
  - Hung or failed runs are left out of the timing and counted per arm (rule in PROPOSAL.md Section 3).

## Final promotions, s4b17 PASS, GO lines sent (22:35-22:49; run-2 #7)

- **stage-window.ps1 tests:** 12/12 PASS (`build/agent8/readout/w-followup/tests-221054.txt`). T1-T6 exit 0; N1-N4 exit 1 and N5-N6 exit 2, as expected.
- **Promotions:** all against launcher run-night.ps1 16B90FA8... (22:11:21), with -VerifyFiles and matrix folders 21/21 before and after each -PlanOnly. Reports are in `build/agent8/readout/w-followup/`.
  - W8a4 r6 (Monday fallback only): 22:35:01, OK, 13 runs, native4 8/8 (`stage-W8a4-223501.txt`). Functional cover appended at 22:43: native4 r5/r6on/r6off runs, exit 0, exe 65432C81..., Agent 4 PASS at 14:39.
  - W5b r6: 22:40:54, OK, 19 runs, devoff4 7/7 (`stage-W5b-224054.txt`).
  - W4c r6: 22:40:57, OK, 13 runs, devoff2 7/7 + devoffB 7/7 (`stage-W4c-224057.txt`).
  - W9 r4: 22:41:28, OK, 21 runs, devoff4b 7/7 (`stage-W9-224128.txt`). Promoted again after the s4b17 PASS, at 22:46:22: OK, identical file (`stage-W9-224622.txt`, batch log `promote-batch-224622.txt`).
  - W6 r5: rechecked at 22:41:32, OK, 21 runs (`stage-W6-224132.txt`).
- **s4b17 (W9's gate): PASS** (Agent 3, `build/agent3/s4b/logs/s4b17.check.txt`). My own read (`build/agent8/readout/w-followup/s4b17-check-2240.txt`): exit 0; 81 STATS lines; sleep_fail 0; back-off OFF line once; STUCK-LOCK 0; [error] 0. s4b18 PASS (Agent 1).
- **bench shas re-hashed at 22:44:26, all unchanged:** W6 E50D791B..., W9 CE0AD757..., W5b 23575AAA..., W4c E2E3E4DA..., W8a4 56BE00D8... (full values in the GO lines). Agent 11's GO-CHECK (22:45, `build/agent11/launcher-review/GO-CHECK.md`) passes all four.
- **Final GO lines sent to Agent 1 at ~22:47**, in Agent 1's 22:34 order: W6 r5, W9 r4, W5b r6, W4c r6 (W4c drops first). Latest GO: 03:00, 03:02, 03:06, 03:20. W8a4 is the Monday fallback only; W8a goes to Monday's day session on native4b, after the re-pin and s4b02/05.
- **Caveat (Agent 6):** W6 runs are title/attract with no input script, so their STUCK-LOCK counts do not test the L route (finding 10).

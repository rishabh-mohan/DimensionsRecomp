# Agent 8: first boot of the OFF baseline (task #16)

Run `build/agent8/runs/1928-first`, 2026-11-21 19:28:55 - 19:40:58. Full machine-generated report:
`build/agent8/runs/1928-first/boot-report.md` (from `bench/agent8/run/boot_report.py`).
Later boots (the 20:05 warm baseline boot, the 20:08 profile dry run, the 21:25 devoff1 boot, the 23:15 native-bin crash and the 23:46 native2 boot) and the exit-linger finding are under "Later boots". After "Matrix runner status" come window 2's result, the window-3 plan, and the runner fixes made for window 3.

## One-line result (sent to Agent 1 at 19:45)

The game reached guest rendering: TU23 applied, then 23,340 guest frames in 9 m 54 s.
- **Adapter:** NVIDIA GeForce MX570.
- **Log:** 0 errors, 40 warnings.
- **Crash or hang:** no crash, no hang.
- **First guest frame:** 61.1 s after process start.
- **Memory:** peak working set 708 MB, peak commit 1193 MB, 79 threads at most.
- **Relink:** a symbolized relink is not needed.

> [!WARNING]
> Every agent command runs on its own hidden desktop, `WinSta0\exebox-<random>`. Agent-launched game runs are therefore **functional checks only**. Their frame times do not count, and the window never shows on the user's screen, even after unlock.

## Setup

| item | value |
|---|---|
| Binaries | `build/baseline-bin`: the 7 files in its MANIFEST.txt. The exe, the dll and the map are hardlinked into the run dir (checked with `fsutil hardlink list`) |
| Config | `harness/legodimensions.toml` copied beside the exe. The only change is `user_data_root = '<run>\user'` (UTF-8, no BOM; the original is kept as `.toml.orig`). `game_data_root` = `game/disc`, `update_data_root` = `game/tu23` |
| Command | `legodimensions.exe --log_file=<run>\game.log --perf_log_csv=<run>\perf.csv --native_settings_load=false --discord_rpc=false --audio_mute=true --pause_when_unfocused=false`, working directory = run dir |
| Runner | `bench/agent8/run/first-boot.ps1` (the 19:28 version), then `recover-close.ps1` after the sampler died (see Problems) |
| Machine | Desktop locked (LogonUI running since 18:07). The runner is in session 1 on desktop `exebox-*`. 12 logical CPUs. Free RAM 7.06 GB at start (6.66-7.50 GB during the run). Agent 2 was building at -j10 the whole time |

## Results

| item | value |
|---|---|
| Furthest milestone | Guest rendering. perf.csv has 23,340 rows (one per guest swap) covering 653.8 s of frame time. Median draw calls per frame: 226, with a nonzero count on every row. Title screen or menu: **not confirmable** (hidden desktop, locked session, no screenshots) |
| Adapter | **NVIDIA GeForce MX570** (vendor 0x10DE, device 0x25A6, 1934 MB dedicated). The Iris Xe was not picked |
| D3D12 | Device created 7.8 s after start: resource binding tier 3, ROV yes, tiled resources tier 4, programmable sample positions tier 2. No feature-level line is logged |
| Errors / warnings | **0 / 40.** All are `krnl` (table below). Count covers the log on disk up to 19:34:45.792; later lines were lost when the game was killed |
| Crash | **No.** No WerFault process and no dump. One WER event: `RADAR_PRE_LEAK_64` at 19:33:59 (Information). That is Windows' resource-exhaustion heuristic taking a note on a process with large commit, not a fault |
| Hang | **No.** Frames advanced until the kill, with 2.2-3.0 cores busy. 1 of 174 samples said "not responding": t=3 s, while the UI thread was creating the D3D12 device. `Process.Responding` waits up to 5 s |
| First guest frame | **19:29:56.910, 61.1 s after process start.** Method below |
| Peak RSS | **708 MB** peak working set. Peak commit 1193 MB. Threads: 79 at most, 72 at the end. Handles about 1480 |
| CPU | 2.38 cores on average after boot (sampled every 1 s) |
| Close | **Killed** after 37 s. WM_CLOSE was not deliverable: the recovery command runs on a different hidden desktop and found 0 windows (see Problems) |

### Startup timeline (game.log, seconds after process start 19:28:55.854)

| s | milestone |
|---|---|
| 6.4 | DXGI adapter: NVIDIA GeForce MX570 |
| 7.8 | D3D12 device and OS features |
| 9.8 | Presenter attached to the window; runtime construction; guest arena mapped (virtual base 0x1_0000_0000, physical base 0x2_0000_0000) |
| 10.5 | Function table initialized (code 82620000-84113BAC) |
| 14.8 | XEX patch applied: 0.0.0.3 → **0.0.23.3** (TU23) |
| 14.9 | Module launched |
| 15.4 | `Initializing shader storage for title 5752084B...` |
| *15.4 → 50.4* | ***35.0 s with no log output*** |
| 50.4 | Guest GPU `SetInterruptCallback`; 50.8 `Skip cutscenes: on` |
| 60.6 | Audio endpoint opened (Realtek, 2 ch, 48 kHz); first ToyPad traffic |
| **61.1** | **First guest frame (perf.csv row 1)** |
| 61.6 | First `d:\INSTALL0_N.HDR/DAT` probe fails (0xc000000f), then 34 more up to 67.7 s |

> [!IMPORTANT]
> **On this first boot, the biggest startup cost was the 35 s gap after `Initializing shader storage`**: 57% of the time to the first frame. **Later boots show it is a first-run cost.** The 20:05 boot of the same `baseline-bin` crossed the same gap in 0.2 s and reached the first frame at 17.7 s. devoff1, a different exe, crossed it in 0.3 s. Both ran in fresh run dirs, so their `user` dir and xsh/xpso cache were empty too (see "Later boots").

During the gap the process used about 1.5-2.2 cores. The shader cache directory `user\cache\shaders\shareable` was created at 19:29:46, the end of the gap. The cache held only 1,556 B of shaders (`5752084B.xsh`) and 732 B of pipelines (`.rtv.d3d12.xpso`) at 19:30:32. So the run dir's own cache does not explain 35 s. The code path is traced next.

### What the 35 s gap is (code reading; not yet profiled)

1. **It blocks the guest from starting.** `rex_app.cpp:622-632` logs `Initializing shader storage...` and calls `graphics_system->InitializeShaderStorage(cache_root, title_id, true)` on the launch (UI) thread. That runs *before* `main_thread->Resume()`, so no guest code runs during the gap.
2. **The UI thread only waits.**
   - With `blocking=true` and the command processor not paused, `graphics_system.cpp:378-390` posts the work to the **"GPU Commands"** thread with `CallInThread` and blocks on a `Fence`.
   - `CallInThread` (`command_processor.cpp:209-215`) only pushes to `pending_fns_`.
3. **The storage work itself starts at the END of the gap.**
   - `D3D12CommandProcessor::InitializeShaderStorage` calls the empty base, then `PipelineCache::InitializeShaderStorage` (`d3d12/pipeline_cache.cpp:222`).
   - That function creates `cache\shaders\shareable` almost first (L233-242).
   - That directory, and `cache` and `cache\shaders`, were created at **19:29:46 = 50.1-51.1 s**, the end of the gap, not 15.4 s.
4. **So the 35 s is time before the GPU Commands thread drains `pending_fns_`.**
   - That thread is created at command-processor init (`command_processor.cpp:187-194`, about 9.8 s).
   - It first runs `SetupContext()` and only then enters the loop that drains `pending_fns_` (`command_processor.cpp:249-260`).
   - `D3D12CommandProcessor::SetupContext` (`d3d12/command_processor.cpp:1117` on) creates the fence, command lists, shared memory, the **render target cache** (L1206), the descriptor heaps, the root signatures, and the texture and pipeline caches.
   - Once the loop is running, a posted function is picked up within 1-5 ms (`command_processor.cpp:279-301`). So the wait is most likely **`SetupContext()` itself, about 40 s from 9.8 s**, with the built-in pipeline and shader creation (render target cache, EDRAM paths) the main suspect. The 1.5-2.2 cores in use fit driver-side pipeline compiles.
5. **What the later boots settled.**
   - The 20:05 and 21:25 boots used fresh `user` dirs, so the xsh/xpso cache was empty both times, yet the gap was only 0.2 s and 0.3 s. So the run dir's cache is irrelevant.
   - Whatever made the first boot slow persists outside the run dir and is not per-exe, since devoff1 is a different exe.
   - The most likely candidate is the driver's own shader cache, filled by the first boot's compiles of the built-in pipelines in `SetupContext`. The first boot also ran under a -j10 build.
   - Confirming it needs one boot after clearing the driver shader cache (NVIDIA `DXCache` under `%LOCALAPPDATA%\NVIDIA`), with the profiler armed from launch, or two log lines around `SetupContext()` (a batch-2 edit in `rexglue-sdk/src/graphics`). Clearing the cache touches state outside the repo, so that is the user's call. I have not done it.
6. **What it is worth:**
   - About 35 s once per driver-cache flush: after a driver update, after a cache clean, or on a new machine. It is the user's first impression of the port, but it does not affect steady-state timing.
   - Possible fixes are unchanged: move storage init off the guest-start path (`blocking=false`, which `graphics_system.cpp:391-395` already supports), or make `SetupContext` lazy or parallel. Both need correctness review, because `blocking=true` guarantees the stored pipelines are ready before the guest draws.
   - For timing runs, the rule is one unscored cold run per bin.

## First-frame method

- **Why it is indirect:**
  - perf.csv has no timestamp column.
  - The game flushes it every 60 rows (`counter.cpp:168`) and at exit.
  - While the game runs, it holds the file without read sharing.
  - So the runner can only record the file's **size** (`FileInfo.Length`, which needs no read access).
- **The calculation:** I read four (time, size) pairs while the game ran, from `LastWriteTime` snapshots plus the final mtime. Each size lands exactly on a row boundary k, with k a multiple of 60. The first swap is then t(flush k) - Σ frame_time_us(rows 2..k).

| anchor | perf.csv bytes | rows | first swap |
|---|---|---|---|
| 19:35:19.548 | 651,166 | 13,620 | 61.06 s |
| 19:35:21.811 | 654,038 | 13,680 | 61.06 s |
| 19:35:24.084 | 656,907 | 13,740 | 61.06 s |
| 19:40:50.758 (final mtime; killed, so no exit flush) | 1,116,870 | 23,340 | 61.06 s |

- **Agreement:** the four estimates agree within 5 ms. Two of them are 5.5 minutes and 9,720 frames apart.
- **What that proves:** `frame_time_us` is the wall-clock interval between guest swaps (host QPC, `command_processor.cpp:1055-1068`). So summing frame_time_us is a valid clock, and the timing runner cuts its measure window that way.
- **Cross-check:** the recovery sampler's size readings give consistent bounds (59.3-62.6 s), slightly offset by its time-stamp skew.

## Log

| count | warning (digits normalised) |
|---|---|
| 34 | `[NtCreateFile] FAILED: path='d:\INSTALL#_#.DAT' -> 0xc000000f` (indices 2-18, each twice) |
| 2 | `Stub XFileFsDeviceInformation!` |
| 2 | `IoDismountVolumeByFileHandle(0xf8000160) - stub` |
| 1 | `[NtCreateFile] FAILED: path='d:\INSTALL0_2.HDR' -> 0xc000000f` |
| 1 | `__imp__XamBackgroundDownloadSetMode STUB` |

- The INSTALL probes are the game looking for an HDD install of the disc, which doesn't exist. They are expected and harmless.
- game.log is flushed by spdlog in batches. The file stopped at 19:34:45.792 (line 91), and the process was killed 372 s later, so that tail is lost. A graceful WM_CLOSE from the launching script avoids this.

## Frames: NOT valid timing

The game ran on a hidden desktop, so these numbers show only that it kept presenting. Do not compare them with anything.

| | all rows | after the first 60 s of frames |
|---|---|---|
| frames | 23,340 | 20,958 |
| frame_time median / p99 / p99.9 / max | 22.1 / 103.6 / 472.5 / 2826.8 ms | 23.0 / 104.2 / 473.8 / 594.2 ms |
| frames > 33.3 ms / > 100 ms | 7,334 / 264 | 6,815 / 245 |

FPS per 30 s window of frame time: 52.6, 26.7, 29.0, 26.3, 28.4, 47.8, 49.6, 52.4, 53.0, 52.6, 42.3, 38.7, 22.8, 28.2, 21.7, 24.1, 28.9, 37.9, 39.3, 23.4, 29.3. The rate alternates between about 25 and about 52 fps, which looks like the title/attract sequence.

## Problems found, and the fixes

1. **Hidden desktop per command.**
   - `GetThreadDesktop` in any agent command returns `WinSta0\exebox-<random>` with 0 top-level windows.
   - The game inherits the desktop of the command that starts it. So:
     - the user never sees it, and frame times are not representative;
     - another command cannot find its window. My recovery posted WM_CLOSE to 0 windows and had to kill the game. The original sampler, on the same desktop, did see 3 windows.
   - **Rule:** start, measure and close in ONE script, with kill-by-pid only as the fallback.
   - Agent 1 has made agent-launched runs functional-only. Timing goes into the runner that the user starts (`bench/agent8/RUN-TIMING-MATRIX.cmd`).
2. **perf.csv cannot be read while the game runs** (no read sharing). Track `FileInfo.Length`, never `Get-Content`. Map sizes to rows after exit.
3. **The sampler died at t=164 s.**
   - What happened: `Add-Content` on proc.csv collided with my own concurrent reader, and `$ErrorActionPreference='Stop'` made that fatal. The game ran on, unattended, until the recovery closed it at 19:40:58.
   - Fixed in `first-boot.ps1`:
     - one shared-read StreamWriter;
     - try/catch per sample, counted in `sample_errors`;
     - a `finally` that closes the game;
     - `Start-Process -PassThru`, so the game does not inherit the script's pipe handles. The old way kept the agent task "running" until the game exited.
   - It also now records `process_start`, `proc_t0`, `perf_csv_mtime` and `runner_desktop` in run.json.
4. **`Process.Responding` blocks for up to 5 s.**
   - The old sample order read it before the CPU counter, so one sample showed 16.3 "cores" on 12 CPUs.
   - `common.ps1` `Get-ProcSample` now reads the counters first and Responding last. `boot_report.py` drops samples above the CPU count and flags them.

## Tools (bench/agent8/run/)

| file | what |
|---|---|
| `first-boot.ps1` | Functional boot. Mirror + toml + launch + 1 s process samples (proc.csv) + log/perf.csv tracking + WM_CLOSE / kill + dumps / WER / events → run.json. `-DryRun` mirrors only (tested 19:44: parses, mirrors, writes the toml) |
| `recover-close.ps1` | Takes over a running game by exe path: extra samples, then close, artifacts and run.json |
| `boot_report.py` | Markdown report: milestones, log levels, top warnings, process peaks and timeline, frames, and the first-frame estimate from size anchors (`--anchor`, `--upper`, proc.csv bounds, final mtime) |
| `common.ps1`, `winhelper.cs` | Shared helpers. `winhelper.cs` is a copy of `harness/winhelper.cs`; Shot and Press are never used |
| `run-timing.ps1`, `timing-env.ps1`, `frame_summary.py`, `run_selftest.ps1` | Timing runner for one run, written by my subagent. The 21:12 version adds `-WarmupFrom launch\|firstframe`, `-BootTimeoutSec`, `-SettleSec`, `-MenuText/-MenuSec`, `-Frames native`, `-SeedCache`, `-TriggerAtMeasure` and the `<run>` placeholder. It always writes run.json and summary.txt (try/finally, errors become `RUNNER ERROR` problems). `Close-GameTimed` records the close timeline (post, exit seen, kill time and error, clean). Self-test 38 PASS / 0 FAIL / 0 SKIP at 21:23 |
| `run-matrix.ps1`, `../RUN-TIMING-MATRIX.cmd`, `matrix*.json` | The matrix runner that the user starts, and its matrices. Status, caveats and the list of matrices are at the end of this file |
| `drivers/pso-stats-at-end.ps1`, `drivers/io-counters.ps1` | Per-arm drivers (matrix field `"driver"`): Agent 6's PSO summary before the close, and Agent 12's host IO counters. Details at the end of this file |
| `drivers/thread-cpu.ps1` | The headroom driver used in window 3. It reads the game's per-thread CPU time every 1 s over the window into threads.csv, then writes headroom.json. A thread's busy % is its CPU s / window s × 100, and **headroom = 100 − the busiest thread's busy %**; the file also has the top 3 threads and the total busy cores. GPU samples come from NVML into gpu.csv: utilisation, clocks, P-state, power, temperature and throttle reasons |
| `matrix_recheck.py` | Post-hoc check of a matrix folder. It keeps runs whose only problems are foreign dumps or a window of at least 90% of plan. It then gives per-arm stats and deltas against each group's reference, including per-round paired deltas of frame time and busiest-thread busy %, plus headroom and GPU columns. `--write` saves recheck.md; `--all` keeps non-timing runs; `--keep-flagged` (session 3) keeps runs with an excluding window-4 flag, which are otherwise dropped and listed under "Flagged runs" |
| `drivers/sys-csv.ps1`, `drivers/LdSys.cs`, `sys_summary.py` (session 3) | The 1 s system-state log (sys.csv): idle time since the last input, foreground pid, input desktop, screensaver, CPU util and effective MHz (P- and E-core means), thermal passive limit and temperature, AC, battery saver, power scheme and overlay. run-timing starts it with `-SysCsv` (matrix key `sys_csv`). sys_summary.py writes sys.json for the window, and the sys flags come from it |
| `gate_logdiff.py` (session 3) | The B-gate log diff: `--a <A run dir> --b <B run dir>`. It FAILs on the fatal patterns in B's game.log, or on more REX_UNIMPLEMENTED lines than A. Boot lines match `GPU route:\|DXGI adapter\|Direct3D 12 device` (OFF and native logs). Exit 0 pass, 1 fail |
| `../RUN-WINDOW4.cmd`, `matrix-window4.json` (session 3) | Window 4: d0 (devoff2) against B (devoffB), then d3 (devoff3). Plan and flags are in `perf-notes/agent8-window3.md` ("Window 4: plan") |
| `../RUN-WINDOW3.cmd`, `matrix-window3.json` | Window 3: the user's no-argument double-click file and its matrix (`perf-notes/agent8-window3.md`) |
| `first-boot.ps1` options since 22:35 | `-Env 'K=V;K2=V2'`, `-StopWhenUnlocked` (closes the game when the session is unlocked, so an agent run never overlaps the user), and the machine-load columns under "The slow stretches" |
| `run-timing.ps1` and `timing-env.ps1` changes in session 3 | `-SysCsv`; `-MinWindowAfterFirstFrame` (floor and warm-up raise; `ff_to_window_s`; `window_before_floor`); `-LightMs` (light block: INSTALL*.DAT fail count, share of light frames); run.json `flags_excluding`, `flags_info` and `excluded`; foreign dumps listed under `foreign_crash_dumps` instead of counting as a problem; Get-BuildProcs now catches clang++ and rexglue. Details in `perf-notes/agent8-window3.md` ("Window 4: plan") |
| `build/agent8/scratch/`: `fps_bins.py`, `dump_exc.py`, `post-window3.ps1` | Scratch tools: fps per time bin from perf.csv or native-frames.csv; the minidump exception and C++ throw decoder used on the native-bin crash; the post-window-3 checks |

## Later boots

All of these were agent-launched on hidden desktops, so the results are functional only. Frame numbers are not valid timing.

### Startup timeline compared (seconds after process start)

| milestone | 1928-first (baseline, first boot) | 2005-dry1 (baseline, warm) | 2125-devoff1 (new exe) |
|---|---|---|---|
| DXGI adapter | 6.4 | 5.1 | 5.9 |
| D3D12 device | 7.8 | 6.2 | 7.4 |
| Presenter attached, guest arena mapped | 9.8 | 7.4 | 8.7 |
| Function table initialized | 10.5 | 8.1 | 9.2 |
| XEX + TU23 patch applied | 14.8 | 12.0 | 12.9 |
| `Initializing shader storage` | 15.4 | 12.5 | 13.0 |
| `SetInterruptCallback` (end of the gap) | **50.4** | **12.7** | **13.3** |
| Audio endpoint opened | 60.6 | 20.9 | 23.1 |
| **First guest frame** (perf.csv flush anchors) | **61.1** | **17.7** | **23.7** |
| Build load at the time | -j10 | -j3 plus an 8-thread shader job | not recorded |

### 20:05: warm boot of baseline-bin (`build/agent8/runs/2005-dry1`, dry run of the timing runner)

- `run-timing.ps1 -Warmup 75 -Seconds 30` (the 19:51 version), fresh run dir. Report: `2005-dry1/boot-report.md`.
- Gap **0.2 s**, first frame **17.7 s** (proc.csv bounds 17.6-17.7 s). 0 errors.
- Window (not valid timing):
  - 1,676 frames in 30.02 s (55.8 fps);
  - median 16.75 ms, p99 45.1 ms, p99.9 482 ms;
  - 69 frames over 33 ms, 2 over 100 ms;
  - 2.75 cores; peak working set 691 MB, commit 1188 MB.
- Close:
  - WM_CLOSE went to 3 windows: `SDL_app` plus two `UAC_InputIndicator` windows owned by the game.
  - `Window closing, shutting down...` was logged 0.14 s after the post and `Title terminated; hard-exiting process.` at 0.32 s.
  - The process lasted until 33.6 s (exit 0). See "Exit linger" below.

### 20:08: profile dry run (`build/agent8/runs/2008-dry1prof`)

- `-Warmup 30 -Seconds 20 -Profile -ProfileSeconds 20`.
- **Runner bug:**
  - The 19:51 runner died at `run-timing.ps1:196` (`Measure-Object ... .Sum` on an empty list under StrictMode) before it closed the game.
  - The game then died with the agent command, so there was no WM_CLOSE and the game.log tail was lost.
  - Fixed in the 21:12 runner, and the try/finally now guarantees the close. Not yet re-run on the real game.
- **The profile is valid but thin.**
  - `profile-700429781.bin` (169,808 B): `analyze_profile.py` read 1,842 samples over 81 threads and 112 modules.
  - The baseline sampler managed only about 23 rounds in 20 s (**about 1.15 rounds/s with 81 threads**), and only 3.8% of samples were busy.
  - **Profile windows need to be 120 s or longer.** The matrices use `profile_s` ≥ 120.
  - There is no LSPX trailer, because baseline-bin has the older sampler.

### 21:25: devoff1 (`build/agent8/runs/2125-devoff1`, `build/agent2/devoff1-bin`, all defaults)

- `first-boot.ps1 -BinDir build\agent2\devoff1-bin -Tag devoff1 -WatchSeconds 210`. Report: `2125-devoff1/boot-report.md`.
- **Result:** guest rendering, 7,610 perf.csv rows by the exit. Adapter MX570. **0 errors, 40 warnings**: the same 5 distinct krnl messages as baseline (INSTALL probes and stubs). No crash, no dump, no WER, 0 not-responding samples.
- **First frame 23.7 s, with a 0.3 s gap.** That is 6 s later than the warm baseline, all of it between `SetInterruptCallback` and the first frame. The cause is either the load at the time or a first-launch cost of a new exe; a second boot tells which, and the matrix's unscored cold run per bin covers it.
- **Process:** peak working set 690 MB, commit 1191 MB, 83 threads, 2.67 cores mean over the 210 s.
- **Close:** WM_CLOSE went to 3 windows. Hard-exit was logged about 0.2 s after the post, and the process was gone at **13.95 s**, exit 0, not killed.
- **A failed first attempt:** at 21:22 the boot printed its run dir and then exited 1 before launching, with no error text. `2122-devoff1` has only the mirror and the toml. A `-DryRun` and the retry, with output redirected to a file, both worked. Cause unknown.

### The slow stretches: not draw count; cause still open (corrected 22:40)

- **Not heavier scenes.** perf.csv `draw_calls` is flat at 218-226 per frame in the ~25 fps stretches and the ~52 fps ones alike. Agent 3 (22:30) found one step about 33 s after the first frame: `draw_calls`/`vertices` go from 218/222 (intro) to 226/1022 (title and attract). After that they stay flat while fps swings between 16 and 55 in stretches of 30-170 s.
- **Where they appeared.** In 1928-first (the first boot ever, beside a -j10 build) and in 2125-devoff1 (the first boot of a new exe, most likely beside the native-bin build, which was staged at 21:48). Not in 2005-dry1 (the second baseline boot, light load, frames 0-88 s after the first frame).
- **Two hypotheses remain:** build load, or a first-boot-of-exe cost. The runs so far cannot separate them, because both first boots also had builds beside them. My earlier heading here ("track machine load") went further than the data.
- **Caveat: proc.csv `cpu_pct_machine` is the game's own CPU** as a share of the 12 logical CPUs (`cpu_cores / 12`), not machine load. It cannot rule background load in or out. Agent 3 read its flat 20-24% as flat machine CPU; I sent the correction at 22:40.
- **New columns, from 22:35 on.** first-boot.ps1 now also records machine-wide CPU:
  - `sys_busy_pct`, from GetSystemTimes;
  - `other_cores`, the machine's busy cores minus the game's;
  - `build_procs`: clang, lld-link, ninja, dxc, cl and rexglue processes, sampled every 5 s.

  run.json gets `build_procs_at_start`, `build_procs_max`, and the means and maxima of the first two. boot_report.py shows them when present. The native boot is the first run to have them. run-timing.ps1 has only the preflight build-tool warning: it is frozen during the window, so the columns are queued for after it.
- **What will separate the hypotheses:** the matrix's unscored cold run per bin, plus ABBA order, on a quiet machine. The runner's window (60-120 s after the first frame) is past the 33 s scene step anyway.

### Exit linger after WM_CLOSE

| run | `Window closing` logged | hard-exit logged | process gone |
|---|---|---|---|
| 2005-dry1 | +0.14 s | +0.32 s | +33.6 s |
| 2125-devoff1 | about +0.0 s | about +0.2 s | +13.95 s |

- **What runs during the linger:** `rex_app.cpp:704` is `rex::FlushLogging(); std::_Exit(0);`, and `_Exit` ends in `ExitProcess`. So the 13-33 s is process teardown after the guest has stopped: DLL detach, driver teardown, or releasing the address space. Which one is unknown.
- **Supporting sign:** in 2005-dry1, `Kill()` failed with access denied at 30 s. That is what `TerminateProcess` returns for a process that is already exiting.
- **Why it matters:** the user sees a lingering process, and a relaunch inside that window may clash with the dying instance.
- **Runner handling:** the runner budgets about 35 s per close and waits up to 60 s before it kills.
- **Next step:** a WPR/ETW trace of the exit, or a debugger break during the linger. Both are functional checks.

### 23:15: native-bin throws at start (`build/agent8/runs/2315-native`)

- **What happened:** `build/agent2/native-bin` (staged 21:48) died inside `LegodimensionsApp::OnPreLaunchModule`, before the guest started and before any frame. Windows wrote two dumps of pid 93080: `legodimensions.exe.93080.dmp` (449 MB, 23:16:43) and `legodimensions.exe(1).93080.dmp` (392 MB, 23:17:01).
- **Dump 1 shows the cause:** an uncaught C++ exception (0xE06D7363). The MSVC throw info decodes to `std::runtime_error`.
  - **Throw site:** `ReadRegistryValues` +0x243 in the settings code (`settings_registry.cpp:104`). The disassembly there builds `"Native setting is not registered: " + name` (`build/agent8/scratch/dump_frame.out.txt`).
  - **Call chain**, from a stack scan against the lld-link map: `OnPreLaunchModule` → `gpu_native::NativeSettingsRuntime` ctor → `SettingsRevisionCoordinator` ctor and its `State` → the `MakeNativeRegistryBackend` lambda → `ReadRegistryValues` → throw.
  - **The missing name:** the exe's settings table names `present_fsr_sharpness_reduction` and `present_fsr_max_upsampling_passes`. rexruntime.dll is built with FidelityFX off and defines neither (`build/agent8/scratch/quick_cvar.out.txt`). Agent 7 found the same name independently (`perf-notes/agent7-present.md`).
- **Dump 2 is a consequence:** 0xC0000374 (heap corruption) on the same thread while the half-built app was being torn down. The chain is `ReXApp` dtor → `Runtime::Shutdown` → `InputSystem::Shutdown` → a free in the MnK input driver. It is worth a look later, but it did not cause the start-up failure.
- **Workaround:** `--native_settings_frontend=false`. Every native arm in my matrices now passes it, and Agents 1, 4, 6 and 7 agree. The real fix is outside my files: register the `present_fsr_*` settings when FidelityFX is off, or skip unregistered names.
- **Tool:** `build/agent8/scratch/dump_exc.py`, a stdlib minidump decoder. It prints the exception record, the C++ throw-info type chain and the registers, then scans the stack against the map. Its output is `build/agent8/scratch/dump_exc.out.txt`.

### 23:46: native2-bin runs cleanly with the frontend off (`build/agent8/matrix/verify3b/runs/2346-n0-r1`)

- **Setup:** one agent-launched run of window-3 arm n0, so the result is functional only.
  - Bin: `build/agent2/native2-bin` (S2, staged 23:22).
  - Options: `--native_settings_frontend=false --native_fps_limit=0 --framerate_limit=0`.
  - Frames come from `LEGO_NATIVE_FRAME_METRICS`.
- **Result:**
  - First frame at 12.0 s.
  - Closed cleanly by WM_CLOSE, exit 0 after 1.3 s.
  - game.log has 0 errors. The warnings are "shader not present in AOT cache" and the krnl stubs.
  - `native_fps_limit_cvar` = 0 is logged.
- **Window (not valid timing):**
  - 5,067 frames in 50.0 s = 101.3 fps.
  - Median 9.20 ms, p99 30.3 ms, p99.9 53.1 ms. 35 frames over 33 ms, 0 over 100 ms.
  - 1.96 cores. The busiest thread, guest `XThread5E50`, is 78% busy (headroom 22%). GPU 39%.
  - Peak working set 1,643 MB (commit 2,036 MB), against about 700 MB for the OFF builds.
- **Same hidden desktop, for comparison (functional only):** devoff2 (d0) ran 226.9 fps at 2.73 cores. Window 3 measures both properly (`perf-notes/agent8-window3.md`).
- native-frames.csv and perf.csv agree on the frame count, within 2 frames.

### Session 3 boots (02:47-03:05, functional, hidden desktop)

| time | run dir | bin | result |
|---|---|---|---|
| 02:47 | `build/agent8/runs/0247-devoffB` | devoffB-bin | PASS. Exit 0; first window at 1.02 s; first perf.csv flush at 10.0 s; 6698 perf rows; at most 83 threads; no dialog, WER or dump |
| 02:54 | `build/agent8/runs/0254-devoff3` | devoff3-bin | PASS. Exit 0; first window at 1.03 s; first flush at 12.0 s; 6514 perf rows; at most 84 threads; no dialog, WER or dump. Agent 9: its log matches devoffB's line for line, apart from the run dir and the ToyPad challenge bytes |
| 02:56 | `build/agent8/runs/0256-native3` | native3-bin: frontend on (no `native_settings_frontend=false`), `LEGO_NATIVE_FRAME_METRICS` set | PASS. Agent 7's `native3_boot_check.py`: A-D PASS with 2 WARNs (`native_fps_limit_cvar=240` against the ref's 0; no 'presentation cap override' line). 482 log lines; 13642 native frames with no gaps; no FSR; MANIFEST has the fix (a) hashes |
| 02:59 | `build/agent11/runs/20261122-025916-testg-default` | devoff3-bin, Agent 11's `testg_session.ps1 -Only default` | PASS. All 50 pause cycles resumed in time; exit 0; no dumps |
| 03:01 | Agent 3's B-gate harness dry run, `build/agent3/runs/*-bgate-dry` | devoff2-bin, `harness\routes\b-gate-menus.txt` | see `perf-notes/agent8-window3.md` ("B gate") |

## Matrix runner status (22:08, updated 00:25)

Window 2's result, the window-3 plan, the runner fixes made for it and its results are in `perf-notes/agent8-window3.md`. Window 3 has its own no-argument file, `bench/agent8/RUN-WINDOW3.cmd`.

### How to run it

- The user double-clicks `bench/agent8/RUN-TIMING-MATRIX.cmd`. With no arguments it runs `run/matrix-base-vs-devoff1.json`; `RUN-TIMING-MATRIX.cmd -Matrix run\<file>.json` runs another one. `run-matrix.ps1` without `-Matrix` shows a picker over `bench/agent8/run/matrix*.json`.
- Options: `-Only <ids>`, `-Repeats N`, `-Quick`, `-NoCold`, `-PlanOnly`, `-NoPrompt`, `-OutDir`.
- Output: `build/agent8/matrix/<yyyyMMdd-HHmm>/` with results.csv, summary.md, plan.txt, matrix.json, logs\ and runs\.
- On an agent's hidden desktop, preflight prints FUNCTIONAL ONLY and carries on (`-NoPrompt` skips its Enter prompt). So agents can use it for functional matrices.

### Self-tests (fake exe)

- run-timing: 38 PASS / 0 FAIL / 0 SKIP (21:23).
- run-matrix: 45 PASS / 6 FAIL / 0 SKIP (21:35-21:40, log `build/agent8/run-selftest/selftest-latest.txt`). None of the 6 affects tonight's matrix:
  - **d5** (summary.md check): a `$S`/`$s` clash (PowerShell variable names ignore case). My subagent fixed it after the run. I fixed the same kind of clash, `$d`/`$D`, at run-matrix.ps1:564.
  - **d10, d11** (native matrix): N1 was NOT STARTED because free RAM was 5.76 GB, below the runner's 6 GB launch floor. That is the environment, not the code.
  - **c13, c14, c16** (profile run): the tick catch-up in caveat 1 below.
- The fixes have not been re-tested, because the runner scripts are frozen while the user's window runs. A full re-run is queued for after it.
- Later, from 23:44 to 00:07, agent-launched functional runs of all four window-3 arms (verify3b, verify3c) ran OK with the window-3 fixes (`perf-notes/agent8-window3.md`). `drivers/thread-cpu.ps1` also passed a standalone test with a fake proc.csv. The fake-exe self-tests are still not re-run: the runner scripts stay frozen until window 3 ends.

### Known caveats (fixes queued for after the window)

> [!NOTE]
> Session 3 status: caveats 2, 3 and 5 are fixed for window 4. For caveat 1, overdue ticks are now skipped and counted (`ticks_skipped`, an info flag), and a late first-frame sample no longer starts the window early. Caveat 4: frames.json now has p95, and per-thread CPU comes from `drivers/thread-cpu.ps1`.

1. **A stall can shorten a window.** run-timing's 1 s tick loop runs overdue ticks back to back. If the measure-start tick is d s late, the window is only `Seconds - d` long and the run is flagged SHORT WINDOW (PROBLEM).
   - Check: the summary.txt line `align ... wall between marks` should read about `Seconds`.
   - Fix: schedule on elapsed time, warm up the sampling calls before launch, and add a stall hook to the self-test.
2. **Foreign crash dumps.** Any new `legodimensions.exe.<pid>.dmp` during a run counts as a problem, even when the pid is another game (another agent's).
   - Such a run is still valid: compare the dump's pid with the run's game pid in run.json.
   - Fix (drafted): these dumps go to `foreign_crash_dumps` with a note instead.
3. **Unequal repeats with roundrobin.** The rotation is applied before the arms with fewer repeats drop out, so the order is unbalanced. Fix: filter by repeats first, then rotate.
4. **Not measured by the runner itself:** `cpu_cores` is whole-process CPU, and summary.md gives median, p99 and p99.9 but no p95. Per-thread CPU now comes from `drivers/thread-cpu.ps1` (headroom.json, from window 3 on); p95 needs perf.csv.
5. **The `-PlanOnly` time estimate is high.** It assumes a 20 s boot and a 35 s close per run. Measured boots take 8-12 s and closes 1-5 s, so window 3's plan says 49 min for about 38 min of work. The fix (measured constants) is queued.

### Drivers (`bench/agent8/run/drivers/`)

An arm names a driver with `"driver"`.
- The runner starts it at the measure-start mark, passing `-GamePid` and `-RunDir`.
- After the window, the runner waits up to 120 s for the driver to exit before it sends WM_CLOSE.
- A non-zero exit or a timeout is a problem.

| driver | for | what |
|---|---|---|
| `pso-stats-at-end.ps1` | Agent 6 | Waits for the `measure end` row in proc.csv. Then it creates the `pso-stats.now` trigger (path from the game.log `PSO stats on` line, else `<run>\cache\pso-stats.now`) and waits up to 15 s for `PSO stats (pso-stats.now)` and `PSO frames`. This is needed because a native WM_CLOSE terminates the process 250 ms later, which loses the exit summary. Exit codes: 0 done (warnings in driver.out.txt), 1 trigger not creatable, 2 bad arguments, 4 timeout (1800 s) |
| `io-counters.ps1` | Agent 12, metric 3 | `GetProcessIoCounters` every 1 s into `<run>\io.csv` (t_s, read/write/other ops and MB, note). The first row is everything up to the window start: boot, menus and the level load |
| `thread-cpu.ps1` | window 3 (headroom metric) | Every 1 s during the window, it reads every game thread's CPU time and appends it to `<run>\threads.csv`. It takes one NVML GPU sample at each tick (`harness/nvml.cs`, compiled once to `build/agent8/cache/LdNvml-*.dll`). After the window it writes `<run>\gpu.csv` and `<run>\headroom.json`. headroom.json holds: busy % per thread, top 1-3, headroom = 100 − top-1 busy %, total busy cores, a `partial` flag, and GPU util mean/median/p90/max, clocks, P-states, power, temperature and power/thermal throttle sample counts. It never uses nvidia-smi |

`pso-stats-at-end.ps1` and `io-counters.ps1` parse cleanly but have not run against the real game yet; their first real use is a functional run after the window. `thread-cpu.ps1` ran in all four verify3b/verify3c runs.

### Matrices (all pass `-PlanOnly` at 22:05; run counts and times are its estimates)

| file | bins | arms (* = reference) | runs, time | for | user input |
|---|---|---|---|---|---|
| `matrix-base-vs-devoff1.json` (the .cmd default) | baseline-bin, devoff1-bin | base*, r0 | 12 (2 cold), ~41 min | quiet window 1 (Agents 1, 3) | none |
| `matrix.json` | baseline-bin, devoff1-bin | r0*, base, r1-r4 (Agent 11; r4 = R3 + object_lookup_fast_path + guest_suspend_guard), io-b (Agent 12), r0g (guest_suspend_guard alone) | 26 (2 cold), ~114 min | Agents 11, 12 | none |
| `matrix-io-level.json` | devoff1-bin | A*, B (5 io cvars); io-counters driver | 11 (1 cold), ~50 min | Agent 12 | MENU: load the story level, every run |
| `matrix-codegen.json` | devoff1-bin, codegen bin (placeholder `build/agent2/codegen1-bin`) | a*, b | 10 once staged, ~34 min | Agent 9 | none |
| `matrix-codegen-check.json` | the same | b-gate, a-prof, b-prof (profile only, not timing) | 3 once staged, ~18 min | Agent 9 | b-gate: play a level for about 2 min |
| `matrix-window3.json` (run by `../RUN-WINDOW3.cmd`) | devoff2-bin, baseline-bin, native2-bin | d0*, base, d11, n0 (x4); d12 (dropped by `-Only`) | 19 (3 cold), ~38 min measured (PlanOnly says ~49) | Agent 1: window 3 | none |
| `matrix-native-functional.json` | native2-bin (since 00:20). Every arm passes `native_settings_frontend=false`; n1-n3 also run uncapped with the thread-cpu driver | n1-n3 (threaded), f1, f2 (state calls), p1, p2 (PSO driver) | 7, ~19 min | Agents 4, 6 | none; agent-launched is fine |
| `matrix-native-tier1.json` | native-bin | n0* (x5), a1; d0*, d1 (Agent 7); t1, t2 (x5, Agent 4) | 25 (1 cold), ~75 min | Agents 4, 7 | none |
| `matrix-native-tier2.json` | native-bin | n0*, e0, e1; v0*, g1; e0-diag*, e1-diag (x1) | 18 (1 cold), ~54 min | Agent 7 | none |
| `matrix-native-tier3.json` | native-bin | d1*, d2; e1*, e2; g1*, g2 | 19 (1 cold), ~57 min | Agent 7 | none |
| `matrix-native-pso.json` | native-bin | p1, p2, p3, p4a, p4b, all with the PSO driver | 5, ~25 min | Agent 6 | none |
| `matrix-native-threaded.json` (copy of `bench/agent4`) | native2-bin (re-copied at 00:20: frontend off, uncapped, thread-cpu driver) | n0*, th1-th3 (x5) | 21 (1 cold), ~63 min | Agent 4 | none |
| `matrix-native-uploads.json` (copy of `bench/agent5`) | `build/agent2/native-batch2-bin` (not staged) | u0*, u1, u2 (x5); s0*, s1, s2 (diagnostics, x1) | 19 once staged, ~66 min | Agent 5 | none |

An arm whose bin is missing is skipped, and `-PlanOnly` prints the order and time it will have once the bin is staged. When Agent 2 stages the codegen bin, the `bin` of arm b (and b-gate, b-prof) needs the real path.

> [!WARNING]
> `matrix-native-tier1.json`, `-tier2`, `-tier3` and `-pso` still name native-bin and do not pass `native_settings_frontend=false`. As they stand, every arm in them would crash at start (see "23:15: native-bin throws at start"). Their owners (Agents 4, 6 and 7) should confirm native2-bin and the cvar before these matrices are used.

# bench/agent8/run: game runners (task #16)

| file | purpose |
|---|---|
| `..\RUN-TIMING-MATRIX.cmd` | **double-click** launcher for the timing matrix (runs `run-matrix.ps1`, then `pause`) |
| `run-matrix.ps1` | timing matrix: plan, preflight, round-robin runs of `run-timing.ps1`, `results.csv` + `summary.md` |
| `matrix.json`, `matrix-*.json` | the matrices (Agent 8's); `matrix.example.json` is a small example |
| `common.ps1` | shared helpers (mirror, toml, args, process sample, WM_CLOSE, crash artifacts). Dot-sourced by the runners. |
| `timing-env.ps1` | timing-validity helpers (desktop name, LogonUI, build processes, AC power) and `Close-GameTimed` |
| `first-boot.ps1` | functional boot: untimed, judged by the log and the process |
| `run-timing.ps1` | one timing run: boot, settle/menu, warm-up, then a fixed measure window cut from perf.csv or native-frames.csv; optional profile mode |
| `frame_summary.py` | stdlib-only frame-time statistics for any perf.csv or native-frames.csv (window by rows, byte marks or seconds) |
| `run_selftest.ps1` | self-test of all of the above (synthetic csv, real csv, end to end against a fake exe) |
| `selftest/fakegame_timing.cs` | the fake `legodimensions.exe` used by the self-test (C# 5 winexe, built with the .NET 4 csc) |
| `selftest/selftest_matrix.ps1`, `selftest/fake-driver.ps1` | self-test section (d): native csv and the matrix end to end |
| `winhelper.cs` | snapshot of `harness/winhelper.cs` (window list, WM_CLOSE, hardlink) |

Nothing here writes outside `build\agent8\**` (run dirs, self-test outputs) and `bench\agent8\run\**`.

## first-boot.ps1

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent8\run\first-boot.ps1 [-BinDir build\baseline-bin] [-Tag first] [-WatchSeconds 300] [-Cvar a=1] [-DryRun]
```
Mirrors the bin dir into `build\agent8\runs\<HHmm>-<Tag>`, writes the toml, starts the game, samples it every
1 s for `-WatchSeconds` (`proc.csv`), then WM_CLOSE / kill and crash artifacts; writes `run.json`.
`-DryRun` only mirrors and writes the toml.

## run-timing.ps1

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent8\run\run-timing.ps1 `
    [-BinDir build\baseline-bin] [-Tag timing] [-Warmup 60] [-Seconds 60] `
    [-WarmupFrom launch|firstframe] [-BootTimeoutSec 240] [-SettleSec 0] [-MenuText '...' [-MenuSec 60]] `
    [-Frames perf|native] [-Cvar 'name=value;name2=value2'] [-Env 'NAME=value'] [-Toml 'key=rawTomlValue'] `
    [-Driver script.ps1 [-DriverArgs 'a;b'] [-DriverTimeoutSec 120]] [-TriggerAtMeasure 'path;path'] `
    [-SeedCache <run dir or dir> [-SeedRecipesOnly]] `
    [-CloseTimeoutSec 60] [-MinFreeRamGB 6] [-Profile [-ProfileSeconds 30]] [-RunsRoot build\agent8\runs] [-StallSec 10]
```
- With `powershell -File`, PowerShell does not split `a,b` into an array, so list items are separated with `;`
  (a `,` stays part of the value, e.g. `-Env 'LEGO_NATIVE_PRESENT=0,0'`). `-Toml` values are raw TOML
  (`-Toml "framerate_limit=0;foo='bar'"`), applied with `Write-RunToml -Set`.
- Steps:
  1. Seed-file check, then the free-RAM check (exit 3 below `-MinFreeRamGB`), both before anything is created.
  2. Mirror and toml like first-boot.
  3. Start with `Start-Process -PassThru` (ShellExecute, no inherited pipe handles). `LEGO_SAMPLE_PROFILE*` and
     `LEGO_NATIVE_FRAME_METRICS` are removed from the environment first and only set by `-Env`/`-Profile`/`-Frames`.
  4. Sample every 1 s and mark the window start and end.
  5. Close with `Close-GameTimed`, then `Save-CrashArtifacts`, then summarise.
- `-WarmupFrom firstframe`: settle, menu, warm-up and window count from the first frame signal, recorded as
  `first_frame_signal_s` / `boot_s`. The signal is the frames csv growing past its header (perf.csv > 315 B,
  native-frames.csv > 0 B). No signal within `-BootTimeoutSec` is the problem `no first frame`: close, exit 1.
  `launch` (the default) counts from the process start. `-MenuText` or `-SettleSec` imply firstframe.
- `-Frames native` sets `LEGO_NATIVE_FRAME_METRICS=<run>\native-frames.csv` (it overrides an `-Env` value) and cuts
  the window from that file (`interval_ms`).
- `<run>` in `-Cvar`/`-Env`/`-Toml` values, `-DriverArgs` and `-TriggerAtMeasure` expands to the run dir; run.json
  keeps both forms.
- `-TriggerAtMeasure`: empty files created at the measure start (a relative path is in the run dir). They are
  recorded in `measure_triggers` (QPC, wall, epoch, t_s, error, exists_after_run).
- `-SeedCache`: copies native-pso.bin and native-pso-recipes.bin (only the recipes with `-SeedRecipesOnly`) into
  `<run>\cache\` before the start. The source is `<dir>\cache` for a run dir, else `<dir>`. Sizes and SHA256 go in
  run.json `seed_cache`. A missing file means exit 1 before anything is created.
- `-Driver`: started at the measure start with `-GamePid -RunDir` plus the args (`.ps1` via `powershell -File`).
  Output goes to driver.out.txt / driver.err.txt. After the window the runner waits up to `-DriverTimeoutSec` for it,
  then kills it (a problem).
- Close (`Close-GameTimed` in timing-env.ps1):
  - It sends WM_CLOSE to the game's windows and waits up to `-CloseTimeoutSec` (60) for the exit. It kills only after
    that; a failed kill is recorded, then it waits 60 s more.
  - The real game logs `hard-exiting` 0.3 s after WM_CLOSE but takes ~33 s to exit (std::_Exit). Any exit after
    WM_CLOSE counts as clean.
  - Everything after the start is in try/finally. On a runner error or Ctrl+C the game is still closed, and run.json
    and summary.txt are still written (`runner_error`).
- Exit code: 0 OK (or a clean profile run), 1 problem (see `problems` in run.json; also no first frame or a missing
  seed file), 3 not started.

**Hidden desktop.** Every agent `run_command` runs on its own private desktop (`WinSta0\exebox-<random>`), so a
game started by one command is invisible to `EnumWindows` from any other command. That is why start, measure and
close are one script: WM_CLOSE only reaches the game from the process tree that started it (otherwise the only
way out is a kill by pid). It also means a timing run launched from an agent renders on a hidden, non-interactive
desktop; frame times from such runs describe that situation, not a player's.

### Outputs (in the run dir)

| file | content |
|---|---|
| `proc.csv` | every 1 s: `t_s, phase (warmup/measure), alive, cpu_cores, cpu_s, ws_mb, peak_ws_mb, commit_mb, peak_commit_mb, threads, handles, responding, log_lines, perf_csv_bytes, free_ram_gb, note` |
| `perf.csv`, `game.log` | written by the game (`--perf_log_csv`, `--log_file`) |
| `frames.json` | full `frame_summary.py` result for the window |
| `run.json` | params, args, env, toml keys, `qpc_frequency`, QPC + wall clock + epoch + perf.csv bytes of `process_start_mark` / `measure_start` / `measure_end`, `window_wall_s`, close result, exit code, window CPU (mean/max cores) and memory peaks, lifetime peaks, not-responding / stall flags, dialogs, WerFault, artifacts, profile marks, `frames` (the summary numbers), `status`, `problems` |
| `summary.txt` | the human summary (also printed) |
| `profile-*.bin`, `profile-meta.json` | only with `-Profile` |

Summary numbers: frame count, window seconds (sum of frame_time_us), mean fps, frame time median / p99 / p99.9 /
max (ms), frames > 33 ms and > 100 ms; process CPU in cores (mean and max of the 1 s samples in the window; 1.0 =
one logical CPU busy), peak working set and peak commit (private bytes) among the window samples, plus the
process lifetime peaks.

**Problems are loud**: lines starting with `!!!` on the console and in summary.txt, and `status: PROBLEM` in
run.json, when the process exits during warm-up or window, perf.csv does not grow for `-StallSec` (10) s during
the window, the window has not-responding samples, the close needed a kill, the exit code is not 0, a dialog or
WerFault appears, dumps are found, the window is short, or there are no frames. The summary is still written from
whatever perf.csv exists. Note: the game flushes perf.csv every 60 frames, so below 6 fps the 10 s stall check
fires without a hang.

### perf.csv and the frame-time source

`--perf_log_csv` writes a header of 17 counter names (`rexglue-sdk/src/core/perf/counter.cpp`) and then one integer
row per guest frame swap, in CRT text mode (CRLF). There is no timestamp column. The file is `fflush`ed every 60
rows and at exit (a 4 KB CRT buffer may also spill mid-row), and the game holds it without read sharing, so the
runner tracks only its **size** while the game runs and reads it after exit.

`frame_time_us` (baseline, NATIVE_GPU=OFF): `CommandProcessor::ExecutePacketType3_XE_SWAP`
(`baseline/DimensionsRecomp/rexglue-sdk/src/graphics/command_processor.cpp:1055-1068`) sets it to the host-QPC
interval since the previous XE_SWAP packet (integer µs, truncated) and then calls `Profiler::Flip()`, which
snapshots the counters and writes the row. So it **is a swap-to-swap interval** (measured on the GPU command
processor thread when it executes the swap packet), and the first row is 0 (no previous swap). Agent 8 confirmed
on the first boot that the summed frame_time_us tracks wall clock (four flush anchors agree within 4 ms over
5.5 min). In NATIVE_GPU builds, `rexlego/src/gpu_native/device.cpp` sets the counter from its own present-to-present
counter and calls `ResetFrameCounters()` without `WriteCsvFrame()`; check that such a build still writes rows.

### Window alignment and its error

1. At tick `-Warmup` (measure start) and tick `-Warmup + -Seconds` (end) the runner records the QPC tick
   (`Stopwatch.GetTimestamp`), wall clock and the perf.csv size, before the slower process sampling.
2. After the game exits, `frame_summary.py --start-bytes <start size> --seconds <Seconds> --end-bytes <end size>`
   computes every row's end byte offset. The window starts at the first row **not** on disk at the start mark
   and contains the shortest run of rows whose frame_time_us sum is >= `-Seconds`.
3. Cross-check: the rows on disk at the end mark minus the start rows (`rows_by_end_bytes`), printed as the
   difference to the seconds cut, with the QPC wall time between the marks.

Residual error: the start mark lags the true current frame by **0 to 59 frames** (unflushed rows; up to about 1 s at
60 fps, 2 s at 30 fps), so the window starts up to 59 frames early. Its length is exact in frame time (overshoot
below one frame). The end-mark cross-check has the same 0-59 lag at both marks, so `|diff| <= 59` rows plus
jitter is expected. If the game is killed, its unflushed tail (< 60 rows) is lost, which only matters if the
window reaches the end of the file (then it is flagged SHORT).

### Percentiles

Nearest-rank on the sorted frame times of the window: `value = sorted[ceil(p * n) - 1]` (exact integer
arithmetic). Median = p50 (lower middle for even n), p99 and p99.9 the same way. Rows with frame_time_us <= 0 are
left out of the statistics and counted as `zero_rows`. `> 33 ms` and `> 100 ms` are strict (`> 33000 µs`), so a
33.3 ms frame (30 fps) counts as over 33 ms.

### frame_summary.py on any perf.csv

```powershell
python bench\agent8\run\frame_summary.py <perf.csv>                                  # whole file
python bench\agent8\run\frame_summary.py <perf.csv> --skip-seconds 60 --seconds 60   # 60 s after 60 s of frames
python bench\agent8\run\frame_summary.py <perf.csv> --skip-rows 3600 --rows 3600
python bench\agent8\run\frame_summary.py <perf.csv> --start-bytes 123456 --seconds 60 --end-bytes 456789 --json out.json
```
A last line without a newline (a file copied while being written) is dropped and reported
(`truncated_last_line`); malformed rows are counted as `bad_rows`. Exit 2 if the file is missing.

### Profile mode (`-Profile`)

PROFILE ONLY, NOT FOR TIMING: the baseline exe has the original sampler
(`baseline/DimensionsRecomp/rexlego/src/sample_profiler.cpp`), which holds `timeBeginPeriod(1)` for the whole process
as soon as `LEGO_SAMPLE_PROFILE` exists, so every guest Sleep changes. The console, summary.txt and run.json are
labelled `PROFILE ONLY, NOT FOR TIMING` and the status is `PROFILE` instead of `OK`; frame numbers are printed under
that label only.

- Env: `LEGO_SAMPLE_PROFILE=1`, `LEGO_SAMPLE_PROFILE_TRIGGER=<run>\profile.trigger`.
- Sampler semantics: it polls the trigger every 50 ms; the file appearing starts recording (after a 150 ms Beep), the
  file being deleted writes `profile-<GetTickCount64>.bin` (LSP1, no LSPX trailer) **next to the exe**, which is the
  run dir (the exe is hardlinked there), then Beeps again.
- The runner creates the trigger at the measure start and deletes it `-ProfileSeconds` later (capped at
  `-Seconds`), recording QPC before/after and wall clock for both; then waits (up to 30 s) until `profile-*.bin`
  exists and its size is stable **before** sending WM_CLOSE. `legodimensions.map` is already in the run dir
  (mirrored), else it is copied from the bin dir.
- `profile-meta.json` (flat) has `profile_trigger_start` / `profile_trigger_end` as epoch seconds (what
  `analyze_profile.py --meta` reads; it subtracts `--trigger-latency`, default 0.175 s), plus the wall clock strings,
  `qpc_frequency`, `qpc_trigger_start` / `qpc_trigger_end`, the profile and map paths. It has no `duration_s`, so the
  trigger latency is applied. The runner prints the analyser command:
  `python DimensionsRecomp\tools\native-cpu\analyze_profile.py <run>\profile-<t>.bin <run>\legodimensions.map --meta <run>\profile-meta.json`

## Self-test

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent8\run\run_selftest.ps1 [-RealCsv build\agent8\runs\1928-first\perf.csv] [-SkipE2E]
```
Prints PASS/FAIL/SKIP per check and a total (exit 1 on FAIL). Scratch, fake bin and fake run dirs go to
`build\agent8\run-selftest\`. It never starts the real game.
- (a) synthetic perf.csv files with known frame times: exact median/p99/p99.9/>33/>100/window seconds/mean fps;
  windows by rows, by byte marks (mid-row and exactly at a row end), by seconds, by skip-seconds; seconds cut past
  EOF flagged short; header-only file; truncated last line; LF file with a zero first row; missing file.
- (b) the real first-boot perf.csv: parses (17-field header, no bad rows), newline count = rows + header, first row
  is the zero, numbers after 60 s agree with Agent 8's independent count; byte-window slicing works. Frame times
  there are not valid timing (hidden desktop). SKIP if the file is missing or still locked.
- (c) end to end: builds the fake `legodimensions.exe` (C# 5, `csc /target:winexe`) with a MANIFEST.txt in the
  bin-dir format. The fake writes perf.csv with the same header, CRLF, a known frame-time pattern in real time,
  60-row flushes through a 4 KB buffer, opened with `FileShare.None`; shows a window; exits 0 on WM_CLOSE; emulates
  the trigger-file sampler. Timing run (`-Warmup 3 -Seconds 5`): exit 0, status OK, files present, one proc.csv row
  per second, closed by WM_CLOSE (not killed), perf.csv size tracked while locked, summary numbers equal the
  pattern over the reported window, window length = 5 s (+ < 1 frame), window start within the flush lag of the
  warm-up end, end-mark cross-check within 59 rows + jitter, CPU/memory and QPC marks recorded. Profile run
  (`-Profile -ProfileSeconds 2`): labels, LSP1 file in the run dir, trigger window ~2 s by wall and QPC,
  `analyze_profile.py`'s meta reader accepts profile-meta.json, closed by WM_CLOSE, profiler env only in this mode.
  With `LEGO_NATIVE_FRAME_METRICS` set, the fake behaves like a native ON build instead: perf.csv gets only its
  header, the frames go to native-frames.csv (1 KB buffered, partial rows), and it writes a fake
  `cache\native-pso*.bin` at exit.
- (d) `selftest\selftest_matrix.ps1`:
  - a synthetic native-frames.csv (ms floats, partial last row) is auto-detected;
  - run-matrix.ps1 rejects unknown fields (exit 2);
  - `-PlanOnly` shows `A B | B A`, one cold run per bin and a skipped missing-bin arm;
  - a `-Quick -Repeats 2` matrix of 2 arms against the fake exe (1 cold + 4 runs) checks results.csv, summary.md
    (group, ref, verdict, FUNCTIONAL ONLY), the menu prompt after first frame + settle, the driver, `<run>`
    expansion, triggers and cvars, and that no env leaks between runs;
  - an `order: fixed`, `frames: native` chain N1 -> N2 (seed_cache N1) -> N3 (seed_recipes_only from N2,
    `LEGO_NATIVE_PSO_CACHE=0`) checks the native window stats against the pattern and the seeded files' SHA256;
  - `run-timing.ps1 -SeedCache` with a missing file exits 1 before anything is created.

## Known limitations

- Timing runs started by an agent render on a hidden desktop (see above); the runner cannot change that.
- The window start is up to 59 frames early (flush lag); the stall check false-fires below 6 fps.
- CPU is sampled every 1 s (max cores is the max of 1 s averages); memory peaks in the window are 1 s samples, the
  lifetime peaks are the OS counters.
- `Process.Responding` can block a sample for up to 5 s if the window is hung (sampling then falls behind; the
  marks are still taken at the scheduled ticks).
- native-frames.csv is a std::ofstream with default buffering, so it is flushed irregularly:
  - the first frame signal is its first flush (any bytes);
  - the window start lags by up to one buffer of rows;
  - the stall check can false-fire;
  - the file is complete only after a normal exit (WM_CLOSE); a killed native run loses its buffered tail.
- Matrix values cannot contain `;`.
- Cold runs cap the warm-up at 10 s and the window at 30 s.
- The matrix estimate uses fixed constants: warm boot 20 s, cold boot 61 s, close 35 s.
- Matrix runs started by an agent are FUNCTIONAL ONLY (hidden desktop, usually LogonUI up). Only runs the user starts
  on the unlocked desktop give timing numbers.
- io_read_ops / io_read_bytes (GetProcessIoCounters) are not collected yet.

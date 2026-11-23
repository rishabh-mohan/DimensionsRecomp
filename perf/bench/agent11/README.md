# Agent 11 micro-benchmarks (helper A)

These are standalone Windows benchmarks for the kernel, timer, clock and global-mutex work in
`DimensionsRecomp/rexglue-sdk/`. They replicate the SDK code paths. They do not link the SDK.

Every bench includes `bench_common.h`. Its `BenchSerializer` named mutex stops two agent11 bench processes from timing
at the same moment. Each bench uses at most 2 threads and prints the machine state at start and end: AC line status,
plus CPU load from `GetSystemTimes`. `run.ps1` also records Win32_Battery BatteryStatus and Win32_Processor
LoadPercentage. Results and their interpretation are in `perf-notes/agent11-s2-benches.md`.

| bench | args | measures |
|---|---|---|
| `bench_sleep` | `[runs=5] [samples=40]` | STATUS item 1. Each run has an OLD phase (the process has not called `timeBeginPeriod`), then a NEW phase (`timeBeginPeriod(1)` plus the `ProcessPowerThrottling` IGNORE_TIMER_RESOLUTION opt-out). Rows: `Sleep(1)`, `SleepEx(1,TRUE)`, `WaitForSingleObjectEx(event,1/2 ms)`, high-res waitable timer at 500/1000/2000 us, a normal timer at 1000 us, `SleepEx(0,TRUE)` and `SwitchToThread`, all run round-robin. Then `SwitchToThread` vs `Sleep(0)` in ns/call (200k calls each). It prints `NtQueryTimerResolution` at each step, and a guest-path model table (KeDelayExecutionThread -10000/-5000, 1.5 ms wait timeout). |
| `timer_highres_check` | `[runs=5]` | Checks waitable timers used the way `Win32Timer` uses them, printing PASS/FAIL. (1) The completion APC fires on alertable waits (high-res and normal, sync and manual). (2) MANUAL_RESET with HIGH_RESOLUTION stays signaled. (3) 2 ms one-shot error with relative, absolute-coarse (SDK: `GetSystemTimeAsFileTime`) and absolute-precise due times. (4) 16 ms periodic over 100 ticks with an absolute due time: mean period and jitter. (5) After WAIT_IO_COMPLETION, `CancelWaitableTimer` leaves no stray signal. Runs alternate `timeBeginPeriod(1)` off and on. The exit code is the number of FAILs. |
| `bench_clock` | `[runs=5]` | Guest clock reads. OLD replicates the mutex `UpdateGuestClock`; NEW replicates the seqlock now in `clock.cpp`. Reports ns/call at 1 and 2 threads for ratios 1/1 and 5/3, plus OLD 5/1, the ratio the runtime actually uses, at 2T. Also: drift (guest elapsed / (host elapsed x ratio)); per-thread monotonicity under a writer that rebases about every 1 ms (alternating 5/3 and 1/1), naive (SDK) vs aligned rebase; check (a), the stale-read step-back, as a deterministic enumeration plus an empirical run with a writer rebasing every ~10 us (late-QPC reader as a positive control). |
| `bench_waitsignal` | `[runs=5] [chunks_per_mode=10]` | Two threads ping-pong on two auto-reset events, in chunks of 10k round trips with the modes interleaved. Every Set/Wait is wrapped in NONE, OLD (recursive_mutex locked twice, Retain, unlock x2, Release after the call) or NEW (acquire-load of the signature, `shared_lock`, Retain, Release after the call). Reports ns per round trip: mean, plus p50/p90/p99/max from TSC. |
| `bench_lookup` | `[runs=5] [lookups=300000]` | Item 7: `GetNativeObject` OLD (global `recursive_mutex` G taken twice) vs NEW (acquire-load of flink, `shared_lock` on a separate `shared_mutex`). Modes: 1T; 2T on the same handle; 2T on different handles; 2T where thread 2 holds G for about 2 us every 20 us. Reports thread-1 mean ns from an untimed pass, and p50/p99/p99.9/max and % >1 us from a TSC-timed pass. |

## Build and run

```powershell
# from the repo root
powershell -NoProfile -File bench\agent11\run.ps1 -Build      # build all, then run all (logs: build\agent11\a\<bench>.txt)
powershell -NoProfile -File bench\agent11\run.ps1 -Bench bench_lookup,bench_clock -Runs 5

# one bench by hand
. .\env\devshell.ps1 -Quiet
cl /nologo /O2 /std:c++20 /EHsc /W3 bench\agent11\bench_lookup.cpp /Fe:build\agent11\a\bench_lookup.exe /Fo:build\agent11\a\ winmm.lib
build\agent11\a\bench_lookup.exe 5
```

The whole set takes a few minutes of wall time. Most of it is `bench_sleep` and `timer_highres_check`, which mostly
sleep. Results on a loaded machine are noisy, so compare medians across runs, not single runs.

## Test G: pause/unpause driver (task #19)

A functional test of `ReXApp::SetGuestPaused` (`src/ui/rex_app.cpp`): N pause/unpause cycles on the running game, each
checked with the `Guest suspended/resumed (N threads)` log lines. Pass = every pause is followed by a resume in time,
the UI thread keeps answering, and the game keeps running. It is not a timing run: a game that an agent starts runs on
that command's hidden desktop, and only that command can see its window, so launch and drive in ONE command
(`testg_launch.ps1` does both). The probe is in `perf-notes/agent11-kernel.md`, "Test G driver (#19)", and the devoff1-bin results are in "Test G results (#23)".

| file | what |
|---|---|
| `testg_launch.ps1` | Starts one game in `build\agent11\runs\<time>-<name>\`: the bin dir hard-linked, `harness\legodimensions.toml` copied with `user_data_root` in the run dir, `--log_file` in the run dir, `--pause_when_unfocused=true`, plus `-Cvar "a=1,b=2"`. Runs the driver, then always closes the game (WM_CLOSE, kill after 30 s) and writes `summary.txt`. `cvars.txt` says which binary defines each cvar. Refuses to start while another `legodimensions.exe` runs. Never writes to `game\`, `harness\` or the bin dir. |
| `testg_driver.ps1` | The cycles and the verdict. `-Mode watch`: the game toggles itself (`--debug_pause_cycle_ms`, Agent 12, 20:15 batch) and the driver checks the log timestamps (a pause longer than `PeriodMs` + 5 s is LATE, no resume by then is a HANG), pings the UI thread with WM_NULL. On a hang, or when the cycles stop early, it writes `hang-<time>-threads.txt` and a minidump. The threads file gives the state and wait reason of each thread; dbghelp dumps record SuspendCount 0, so this is where suspended threads are found. If the cycles stop while the UI thread is silent, it waits for the UI-hang FAIL. `-Mode post`: the driver posts WM_NCACTIVATE / WM_ACTIVATE / WM_KILLFOCUS / WM_SETFOCUS; SDL 3.5 ignores them unless the window really is in the foreground. Writes `testg_report.txt` and `.csv`. Exit 0 PASS, 1 FAIL, 2 setup error, 3 INCONCLUSIVE. |
| `testg_win.cs` | Win32 helpers, loaded with `Add-Type` (C# 5). |
| `testg_selftest.ps1` | The driver's verdicts on synthetic logs (pass, late, hang + minidump and threads file, double suspend, stopped, stopped with a hung window, idle, dead pid, no window) and the log tailer. No game: ping.exe and a hung WinForms window stand in for it. |
| `testg_check.ps1` | Compiles `testg_win.cs` and parses the scripts. |
| `testg_session.ps1` | Task #23 in one command. Checks that the bin defines the four cvars and that no game runs, then runs half 1 (B off), half 2 (B on) and the control (`pause_safe_order=false`). The control is skipped while another `*-bin` is staged in `build\agent2`, unless `-ForceControl` is given. Runs `testg_dump.ps1` on any dump and writes `build\agent11\runs\testg-session-<time>.txt`. Options: `-BinDir`, `-Cycles`, `-PeriodMs`, `-Only b-off,b-on,control`, `-NoControl`, `-ForceControl`, `-CheckOnly`. Opt-in S3 run `-Only default` (Agent 1, 01:20): half 1 with no `--pause_safe_order`, so the build's default picks the order. It refuses (exit 2) unless the build carries the default-ON help text (`which can hang when the guest pauses`); `-NoMarkerCheck` skips that check. After the run it warns if the run dir's `cmdline.txt` or `legodimensions.toml` sets `pause_safe_order`. Exit 0 when it ran (read the verdicts), 2 when it did not start. |
| `testg_default_selftest.ps1` | No game: every `testg_session.ps1` call uses `-CheckOnly`. Checks the `-Only` filter, that devoff2 (S2, default OFF) refuses the `default` run, that the post-run check flags `pause_safe_order` in `cmdline.txt` / the toml, and that `harness\legodimensions.toml` doesn't set it. `-Devoff3 <bin>` also checks that devoff3 carries the marker. Report: `build\agent11\selftest\default-<time>.txt`. |
| `testg_dump.ps1`, `testg_dump.cs` | Offline reader for the driver's minidumps. For each thread: name, RIP/RSP, start address, and a heuristic call stack (return addresses checked against a preceding CALL) named from `legodimensions.map` or the nearest export. Then the waiting, running and UI threads. Exit 0, or 2 for a bad dump. Tested on self-test dumps, and on the 23:22 game dump from the test G control (1.0 s). Caveats: the "UI thread" line is a guess, and on the game dump it was wrong (it picked a DXGI vblank waiter). In SDL builds the UI thread is the main thread (start `wWinMainCRTStartup`). Stale return addresses can sit between real frames, and a "nearest export" name with an offset of hundreds of KB identifies only the module. |

```powershell
# test G on a build with Agent 12's #17 fix and debug cvars: half 1 (guard B off), then half 2 (guard B on)
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_launch.ps1 -BinDir <bin dir> -Name testg-b-off -Driver watch -Cycles 50 -PeriodMs 1000 -Cvar "pause_safe_order=true,guest_suspend_guard=false,debug_pause_cycle_ms=1000,debug_pause_cycle_count=50"
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_launch.ps1 -BinDir <bin dir> -Name testg-b-on -Driver watch -Cycles 50 -PeriodMs 1000 -Cvar "pause_safe_order=true,guest_suspend_guard=true,debug_pause_cycle_ms=1000,debug_pause_cycle_count=50"
# or the whole #23 session (half 1, half 2, control) in one command; -Only control -ForceControl runs the control alone
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_session.ps1
# S3 default check (Agent 8's slot, after the devoff3 boot): half 1 on the build's default pause order
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_session.ps1 -BinDir build\agent2\devoff3-bin -Only default
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_default_selftest.ps1 -Devoff3 build\agent2\devoff3-bin   # no game
# a hang dump: threads and stacks (match them with the 'Suspended' tids in hang-*-threads.txt)
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_dump.ps1 -Dump <run dir>\hang-<time>.dmp -BinDir <run dir>
# the driver alone, on a game someone else started (e.g. Agent 8's runner): watch its log
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_driver.ps1 -GamePid <pid> -Log <game.log> -Mode watch -Cycles 50 -PeriodMs 1000 -FromStart
# no game needed
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_check.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_selftest.ps1
```

## Exit-path fix (task #27)

`HalReturnToFirmware` and `XamShowDirtyDiscErrorUI` (rexglue-sdk `src/kernel/xboxkrnl/xboxkrnl_hal.cpp`,
`src/kernel/xam/xam_ui.cpp`) called CRT `exit(0/1)` on a guest thread. The fix makes them call
`rex::FlushLogging(); std::_Exit(code);`, as `ReXApp::OnClosing` does. The rationale, the reliance check and the
results are in `perf-notes/agent11-kernel.md`, "#27 exit-path fix". The staged copies, hashes, diff and results are in
`build\agent11\exitfix\`. None of these scripts needs the game, and each uses one thread.

| file | what |
|---|---|
| `exitfix_stage.ps1` | Stage (the default): copies the live files to `pristine\`, applies the exact text edits (each must match once; line endings are kept), and writes the staged copies, `HASHES.txt` and `exitfix.diff` (read-only `git diff --no-index`, repo-path headers). `-Apply`: staged → live, refused unless both live files still match their pristine hash. `-Revert`: pristine → live. Both stamp the live files' LastWriteTime with the copy time, because `Copy-Item` keeps the source's (Agent 12's catch, 00:03). |
| `exitfix_check.ps1` | Source lint per file: no CRT `exit(` outside comments; `#include <cstdlib>`; the export ends with `rex::FlushLogging(); std::_Exit(<code>);`; its original `REXKRNL_ERROR` lines are kept; no 'hard-exiting' text; the hash matches `HASHES.txt`. The default checks the staged copies; `-Live` checks the live tree; `-Pristine` is the negative control and must fail. |
| `exitfix_syntax.ps1` | clang `-fsyntax-only` with the exact dev-SDK flags (from `env\compile-one.ps1 -PrintOnly`, PCH dropped), run on the pristine copy and on the candidate. Fails on a compile error or on any diagnostic that only the candidate has. `-Live` checks the live tree. |
| `exitfix_test.ps1`, `exit_test.cpp`, `exit_test_dll.cpp` | Unit test. Builds `exit_test` as `/MD` (like the game) and as `/MT`, plus a `/MD` DLL. Each run calls `exit` / `std::_Exit` / `TerminateProcess` from a non-main thread while other threads run. Markers show which of these ran: the atexit handlers, the EXE static destructors (and whether they ran while a thread was still alive), the DLL static destructors (DLL detach), the flushed log, and an unflushed CSV. Asserts the exit codes and markers; writes `build\agent11\exitfix\test-<time>.txt`. |

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\exitfix_stage.ps1             # stage
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\exitfix_check.ps1             # lint the staged copies
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\exitfix_syntax.ps1            # syntax-only compile
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\exitfix_test.ps1              # exit-semantics unit test
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\exitfix_stage.ps1 -Apply      # after S2 + SAFE only
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\exitfix_check.ps1 -Live
```

## S3 proposal: `pause_safe_order` default ON (Agent 1, 23:41)

Text only: the change is staged in `build\agent11\safeorder\` for Agent 10's rating, and the live tree stays untouched. Neither script needs the game, and each uses one thread. The rationale is in `perf-notes/agent11-kernel.md`, section "S3 proposal".

| file | what |
|---|---|
| `safeorder_stage.ps1` | Stage (the default): copies the live `rex_app.cpp` to `pristine\` and applies the two text edits. The first sets the `pause_safe_order` default from `false` to `true` and extends its description; the second updates the comment in `SetGuestPaused`. Each edit must match once, and LF and no BOM are kept. Writes the staged copy, `HASHES.txt` and `safeorder.diff` (read-only `git diff --no-index`, repo-path headers), then runs 11 self-checks. `-Check`: is the live file still pristine? `-Apply`: staged → live, refused unless the live file still matches the pristine hash; only after Agent 10's SAFE and Agent 1's go. `-Revert`: pristine → live. Both stamp the live file's LastWriteTime with the copy time, because `Copy-Item` keeps the source's. |
| `safeorder_syntax.ps1` | `exitfix_syntax.ps1` for `rex_app.cpp`: clang `-fsyntax-only` with the dev-SDK flags (PCH dropped), on the pristine copy and on the candidate. Fails on a compile error, or on any diagnostic that only the candidate has. `-Live` checks the live tree. |
| `stage_stamp_test.ps1` | Runs byte-for-byte copies of `exitfix_stage.ps1` and `safeorder_stage.ps1` in a sandbox (`build\agent11\stamptest\<time>\`, which mirrors the repo layout). After each `-Apply` and `-Revert` it checks the hash and that the live file is stamped with the copy time. Also reproduces the hazard: a bare `Copy-Item` keeps the source stamp. Never touches the real tree. Exit 0 = all checks pass. |

```
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\safeorder_stage.ps1            # stage + self-check
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\safeorder_stage.ps1 -Check     # live still pristine?
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\safeorder_syntax.ps1           # syntax-only compile
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\stage_stamp_test.ps1           # -Apply/-Revert stamp test (sandbox)
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\safeorder_stage.ps1 -Apply     # after SAFE + Agent 1's go only
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\safeorder_syntax.ps1 -Live
```

## S3 task #10: TimerQueue CPU (Agent 1, 02:01)

Why `rex::thread::TimerQueue` keeps 52-62% of a core busy in window 3, and a fix behind an OFF cvar, `timer_queue_precise_wait`. The fix is staged in `build\agent11\timerq\stage\` for Agent 10's rating; the live tree stays untouched (Agent 1, 02:55: staged only, S4 candidate). No script here starts the game. Each uses at most 2 busy threads (the bench's timer thread and main thread) and single-threaded `cl`. Findings are in `perf-notes/agent11-kernel.md`, section "S3 TimerQueue".

| file | what |
|---|---|
| `bench_timerq.cpp` | Drives a `timer_queue.cpp` the way the game does: one 1 ms recurring timer whose callback stores a millisecond count, like xboxkrnl's KeTimeStampBundle timer, the only queue user on Windows. Modes: `run <secs> <tbp> [mask]` (timer thread CPU, callbacks/s, gaps, how stale the tick count gets), `stress <count> [spread_ms] [1/0]` (one-shots: each fires once, none early; more than 512 overflows the ring; `0` drops the 1 ms timer), `exit` (the static queue must stop with timers armed), `spin` (spin_wait costs per logical processor), `classes` (P/E masks). Built with `/DBENCH_STAGED` it links the staged copy, sets the cvar from `TIMERQ_PRECISE=1`, and defines `SleepPrecise` as `threading_win.cpp` does (`TIMERQ_NO_HIRES=1` forces its fallback). |
| `timerq_shim\rex\*.h` | Stand-ins for `rex/assert.h`, `rex/thread.h`, `rex/cvar.h`, `rex/logging.h`, so `timer_queue.cpp` compiles outside the SDK. |
| `timerq_bench.ps1` | The cause bench on the LIVE `timer_queue.cpp`: P/E classes, spin_wait costs, the 1 ms timer in spin and blocking (`REX_TIMER_WAIT_BLOCKING=1`) at the default timer resolution and at 1 ms, then spin on P cores only and on E cores only. Waits while a game runs. Log: `build\agent11\timerq\results-<time>.txt`. |
| `timerq_stage.ps1` | Stage (the default): copies the live `src/core/timer_queue.cpp` to `pristine\`, applies edits A-I (each must match once), writes the staged copy, `HASHES.txt` and `timerq.diff`, then runs 17 self-checks (diff -6/+73 in 6-9 hunks, cvar defined once with default false and kInitOnly, every `blocking_` test replaced, env var still read once, `SelectMode` once under `call_once`, LF/no BOM kept, live file untouched). `-Check`, `-Apply` (after Agent 10's SAFE and Agent 1's GO only), `-Revert`; both stamp the copy time. |
| `timerq_syntax.ps1` | `safeorder_syntax.ps1` for `timer_queue.cpp`: clang `-fsyntax-only` with the dev-SDK flags (PCH dropped), pristine vs candidate; fails on any new diagnostic. `-Live` checks the live tree. |
| `timerq_stage_bench.ps1` | Builds the bench against the live and the staged file, then: `stress 2000 50`, `stress 40 2000 0` and `exit` in 7 modes (live spin/blocking, staged spin/blocking with the cvar off, staged precise, precise + env var, precise without the high-resolution timer), checking the mode line and that only precise runs log `TimerQueue: precise wait`; then 10 s `run`s (waits while a game runs). Log: `build\agent11\timerq\stage-bench-<time>.txt`. Exit 0 = every check passed. |
| `timerq_pair.ps1` | Summarizes Agent 8's TimerQueue functional runs. It is read-only: no game, no build. The first run dir is the reference (d0f), and each further one is a test arm (d0t, d11t). For each run it reads: the `rex::thread::TimerQueue` busy % (and its busiest 1 s) and the sum over all threads from `threads.csv`; the `>33 ms` and `>100 ms` frames, mean fps, cvars, env and the sys line (P/E effective MHz and utility, power overlay) from `summary.txt`; the status, close, exit code, WerFault, `env_set` and first-frame time from `run.json`; frames per 10 s from `perf.csv`; P/E MHz and E utility per 10 s from `sys.csv`; and any `*.dmp`. A test arm passes when all of these hold: its TimerQueue busy % is at most `-MaxTimerQueuePct` (3.0); it has no more >100 ms frames than the reference; its fps is at most `-MaxFpsDropPct` (10) below the reference's; it closed cleanly with no dump; and only it sets `REX_TIMER_WAIT_BLOCKING`. Window 3's d0 and verify3b's d0 are printed for context. With no `-RunDirs` it takes the newest `*-d0f-r*`, `*-d0t-r*` and (if any) `*-d11t-r*` under `build\agent8\matrix`. Log: `build\agent11\timerq\pair-<time>.txt`. Exit 0 = every test arm passes, 1 = one fails, 2 = bad input. |
| `timerq_slowstate.ps1` | Read-only scan for the hidden-desktop "slow state" (E cores busy at minimum clock). For each run dir under `-Root` (`build/agent8/matrix`, matrices named at or after `-Since`) that has `sys.csv` and `run.json`, it prints whether `REX_TIMER_WAIT_BLOCKING` was set, the slow-state onset in seconds after the first frame (the first of `-MinRows` (3) samples in a row with `e_eff_mhz` below `-EMhz` (800)), the share of samples after the first frame in that state, the span and `fg_game`, then counts per arm type. Use it before reading fps from any run. |

```
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_bench.ps1                # cause bench (live code)
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_stage.ps1                # stage + self-check
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_stage.ps1 -Check         # live still pristine?
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_syntax.ps1               # syntax-only compile
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_stage_bench.ps1          # staged vs live, no game
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_pair.ps1 -RunDirs <d0f dir>,<d0t dir>,<d11t dir>   # Agent 8's runs
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_slowstate.ps1 -Since 20261122-0330   # slow-state scan of Agent 8's runs
```

## S4 task #19: execution-speed opt-out (Agent 1, 04:07)

Staging only. A new cvar, `host_execution_throttling_optout` (default off), opts the game out of Windows' execution-speed throttling (EcoQoS, `PROCESS_POWER_THROTTLING_EXECUTION_SPEED`) at startup. There is also a proposal for Agent 8's runner to apply the same opt-out to the game it launches. The live tree stays untouched (`-Apply` needs Agent 10's SAFE and Agent 1's GO). No script here builds or starts the game, and each is single-threaded. Findings: `perf-notes/agent11-kernel.md`, section "S4 staging (task #19)".

| file | what |
|---|---|
| `pthrottle_stage.ps1` | Stage (the default): copies the live `include/rex/threading_timing.h`, `src/core/threading_win.cpp` and `src/system/runtime.cpp` to `pristine\`, applies the edits (each must match once), writes the staged copies, `HASHES.txt` and `pthrottle.diff` (-4/+37, 7 hunks) to `build\agent11\pthrottle\stage\`, then runs 35 self-checks. Per file: BOM and newline style kept, no CR, live file untouched. On the diff: -4/+37, 4-8 hunks, 3 files, added lines <= 100 columns and ASCII, and the line delta per file. On the content: the cvar defined once with default false and read once; the field defaults to false; `KeepTimerResolutionInBackground` replaced by `OptOutOfPowerThrottling(control_mask)`; StateMask only ever 0; one `SetProcessInformation` call site, on the own process; the "Host timer resolution set to" line and the timer debug line unchanged; the new info and warn lines. `-Check` (live still pristine?), `-Apply` (after SAFE and GO only), `-Revert`: all-or-nothing with hash guards, and both stamp the copy time. |
| `pthrottle_syntax.ps1` | clang `-fsyntax-only` with the dev-SDK flags (PCH dropped) on `threading_win.cpp` and `runtime.cpp`, pristine vs staged; fails on any new diagnostic. A control compile (the staged `threading_win.cpp` with the pristine header) must fail. Report: `build\agent11\pthrottle\stage\syntax-<time>.txt`. |
| `pthrottle_test.ps1` + `pthrottle_test.cpp` | The read-back test. Checks the stage copies against `HASHES.txt` and extracts `HostTimingConfig` and the two code blocks of `threading_win.cpp` verbatim from the pristine and the staged copy (`build\agent11\pthrottle\gen\pthrottle_impl.inc`, with `#line`). Then it builds one exe with `cl /W4` and runs each scenario in a fresh child process: `ConfigureHostTiming`, then `GetProcessInformation` in the child and through the parent's handle, then `RestoreHostTiming`. It compares the calls, log lines and final state with pristine. It covers: off/on combinations; a preset state left untouched when off; simulated Windows 10 (flag 0x4 rejected) and a missing export; replace semantics; the runner's read-modify-write and the handle rights it needs. Report: `build\agent11\pthrottle\test-<time>.txt`. Exit 0 = all passed. |
| `pthrottle_runner_probe.ps1` | Tests the C# helper proposed for Agent 8's runner (`Add-Type`, Windows PowerShell 5.1) on a hidden PING.EXE child it starts itself, with `Start-Process -PassThru` and `$p.Handle` as in `run-timing.ps1`. Read-modify-write keeps the game's timer bit (C=0x4 -> 0x5). It also works through a narrow `OpenProcess` handle and clears an EcoQoS opt-in, and a plain Set replaces the state. Report: `build\agent11\pthrottle\runner-probe-<time>.txt`. |

```
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\pthrottle_stage.ps1            # stage + 35 self-checks
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\pthrottle_stage.ps1 -Check     # live still pristine?
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\pthrottle_syntax.ps1           # syntax-only compile
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\pthrottle_test.ps1             # read-back test (child processes)
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\pthrottle_runner_probe.ps1     # runner helper probe (PING.EXE child)
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\pthrottle_stage.ps1 -Apply     # after SAFE + Agent 1's GO only
```

## S4 task #24: execution-speed opt-out pairs (Agent 1, 04:54)

The runner-side opt-out from #19 part 2, runnable now without editing `bench/agent8/**` or `harness/**`.
FUNCTIONAL ONLY (hidden desktop), one game at a time, never a timing run.

| File | What it does |
|---|---|
| `pthrottle_pairs.ps1` | Wrapper. It generates a 2-arm matrix: `d0` (opt-out off) and `d0e` (opt-out on). Both use devoff2, `framerate_limit=0`, perf frames and thread-cpu. It runs Agent 8's unchanged `run-matrix.ps1` with `-NoCold`, round-robin (d0 d0e, d0e d0, d0 d0e), into `build/agent11/pthrottle/pairs/<stamp>`. Around the run it starts the sidecar, merges each read-back into run.json (`"power_throttling"`, BOM kept), runs the read-out and `timerq_slowstate.ps1`, and hashes window 4b before and after. Flags: `-PlanOnly`, `-DryRun`. |
| `pthrottle_sidecar.ps1` | Watches only `legodimensions` processes whose exe is under the pairs' `runs\` dir; other games are never opened. On `d0e` it does a read-modify-write: EXECUTION_SPEED controlled and off, other bits kept. On `d0` it only reads. It re-applies if the game's own startup call replaces the state, and writes one JSON per run. |
| `pthrottle_readout.ps1` | For each run: the read-back, plus slow-state onset and share (the `timerq_slowstate.ps1` rule: E below 800 MHz for 3+ samples after the first frame), plus E/P MHz and E utilisation in slow rows. Then per arm, and a verdict. |
| `pthrottle_w4b_hash.ps1` | sha256 of `RUN-WINDOW4B.cmd` and its closure: the scripts, `matrix-window4.json`, the helper cache and all 3 bins. `-Compare` checks against an earlier TSV. |
| `pthrottle_dryrunner.ps1` | Simulated runner for `-DryRun`. It uses a sleeper stand-in (`pthrottle_standin.exe`), not a game, and applies a game-like C=0x4 Set. |

```
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\pthrottle_pairs.ps1 -PlanOnly   # matrix check + estimate
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\pthrottle_pairs.ps1 -DryRun     # no game, ~3 min
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\pthrottle_pairs.ps1 [-MeasureS 50]   # 6 games (Agent 8's slot)
```

**Result (task #24, Agent 8's run `20261122-0600`).** NO EFFECT. The ~550 MHz E-core state came in 3/3 d0e runs with the opt-out held, and in 3/3 d0 runs. The wrapper's exit 1 was a teardown artifact: the bit reads 0 in the last poll, about 0.56 s before exit. `pthrottle_readout.ps1` now treats that as teardown (`-TeardownS 1.5`; columns `ver`, `lost_s`); its corrected output is `build/agent11/pthrottle/pairs/20261122-0600-meta/readout-v2.txt`. Details are in `perf-notes/agent11-kernel.md`, "Result (task #24)".

## Package-power sys.csv columns (Agent 1, 06:28; for after window 4)

Staged in `syscsv-pkg/`: Agent 8's sys.csv sampler plus 4 columns at the end of each row, `pkg_w,pp0_w,pp1_w,dram_w` (W, from `\Energy Meter(*)\Power`, the RAPL counters). These are new files only: Agent 8's sampler and every window-4b file stay unchanged until Agent 8 adopts the diffs after window 4. No script here starts a game. The tests run the sampler against their own PID. Findings: `perf-notes/agent11-kernel.md`, section "Package-power sys.csv columns".

| file | what |
|---|---|
| `syscsv-pkg/LdSys.cs` | the staged sampler core (one more PDH counter, 4 more columns) |
| `syscsv-pkg/LdSys.cs.diff`, `syscsv-pkg/sys_summary.py.diff` | the adoption diffs, with Agent 8's paths (`git -c core.autocrlf=false apply` from the repo root) |
| `syscsv-pkg/sys_summary.py` | Agent 8's summary with `header_ok` allowing extra trailing columns (cosmetic: nothing acts on sys.json's `header_ok`) |
| `syscsv-pkg/sys-csv.ps1` | test copy: only the repo depth and the DLL cache (`build\agent11\cache`) changed. Not for adoption |
| `syscsv-pkg/test_syscsv_pkg.ps1` | staged vs original sampler, alternating, with checks on header, fields, ranges, filled columns, the init failures, cost, and Agent 8's files and DLL cache left untouched. Out: `build\agent11\syscsv-pkg\test\<stamp>\` |
| `syscsv-pkg/test_sys_summary_compat.py` | the original vs the staged `sys_summary.py` on the newest new-format and old-format sys.csv. Out: `build\agent11\syscsv-pkg\compat\<stamp>\` |
| `syscsv-pkg/make_diffs.ps1` | writes the diffs, then runs `git apply --check` (read-only) |
| `syscsv-pkg/originals-0631.txt` | sha256 of Agent 8's `LdSys.cs` and `sys-csv.ps1` at 06:31 |

```
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\syscsv-pkg\test_syscsv_pkg.ps1 -Compare -Rounds 3   # no game, ~1.5 min
python bench\agent11\syscsv-pkg\test_sys_summary_compat.py                                                          # after the test
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\syscsv-pkg\make_diffs.ps1                          # diffs + git apply --check
```

**Result (07:21-07:23).**
- The test passed 58/58, and the compat check and both `git apply --check` runs passed.
- Idle readings: `pkg_w` ~13-14 W, `pp0_w` ~7 W; `dram_w` reads 0 on this laptop.
- Sampler CPU is the same as the original's (1.17 vs 1.15 ms per sample). Each sample waits about 1.7 ms longer in the PDH collect.

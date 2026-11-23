diff --git a/build/agent11/launcher-review/r-2128-581A03DB/README.md b/build/agent11/launcher-review/p-2214-16B90FA8/README.md
index ce339af..071b4f3 100644
--- a/build/agent11/launcher-review/r-2128-581A03DB/README.md
+++ b/build/agent11/launcher-review/p-2214-16B90FA8/README.md
@@ -20,7 +20,7 @@ Timing runs only count when they run on your own desktop, with nobody touching t
    - You can turn the screen brightness down.
    - Before a window starts, it closes ChatGPT, the Copilot app, Roblox (the player and the Store app), Task Manager and Wallpaper Engine itself. It leaves Roblox Studio and every other program alone.
 4. If it refuses to start, it says why in red and changes nothing. Possible reasons:
-   - it is already morning (after 07:30 it would run for more than 14 hours): start it in the evening
+   - the time: it only starts between 17:30 and 07:30, because it always ends at the next 07:30 and refuses to run for more than 14 hours. Start it in the evening
    - not on AC power, or Windows can't tell whether it is
    - the PC is locked
    - it was not started on your own desktop
@@ -43,8 +43,8 @@ Timing runs only count when they run on your own desktop, with nobody touching t
      If that doesn't happen within 2 hours, it skips the window.
   5. It closes the five programs again if they came back, checks everything once more, then runs the window. That is the agents' runner `bench\agent8\run\run-matrix.ps1`, which starts and closes the game again and again, about 30-40 minutes in total.
   6. It removes its HOLD note, unless the agents' hold manager already has, and waits for the next window.
-- It never starts a window that would end after 07:30, and it starts none after 06:45. At 07:30 it ends.
-- If a window is somehow still running at 07:45, it stops that window (it closes the runner and the game) and ends.
+- It never starts a window that would end after 07:30, and it starts none after 06:45.
+- At 07:30 it ends. If a window is somehow still running then, it stops that window first (it closes the runner and the game).
 
 ## What it changes on your PC, and what it puts back
 
@@ -74,7 +74,7 @@ It builds nothing, changes no code and no game files, and runs nothing except `r
 - **Fast way:** click in its window and press **Ctrl+C**.
   - It still puts everything back (screensaver, HOLD note).
   - A window that is running stops part-way (the launcher closes the runner and the game), and its numbers are lost. If the game stays open anyway, close it.
-  - If the window asks `Terminate batch job (Y/N)?`, type `Y`.
+  - If the window asks `Terminate batch job (Y/N)?`, either answer is fine: `N` shows the launcher's last lines and `The launcher was interrupted (exit code ...)`, `Y` closes the window at once.
 - **If you close the window with the X** (or the PC restarts), the launcher can't clean up:
   1. If the game is still open, close it. In Task Manager it is `legodimensions.exe`.
   2. Delete `perf-notes\WINDOW-HOLD.txt` if it is still there.
@@ -118,7 +118,7 @@ Example: `GO W6 matrix-window6.json 3F2A...64 hex... only=s0,p2,p2f,p2fc repeats
   - its `bin` is not `build/agent2/<name>-bin`, or that folder lacks `MANIFEST.txt` or `legodimensions.exe`;
   - its `env` has a key that is not one of these 11 (exact case; `build/agent8/w8w9/ENV-KEYS-F1.txt`, approved by Agent 1 at 21:14): `REX_TIMER_WAIT_BLOCKING`, `LEGO_GPU_WAIT_STATS`, `LEGO_GPU_WAIT_BACKOFF_US`, `LEGO_GPU_WAIT_SPIN_US`, `LEGO_NATIVE_FRAME_METRICS`, `LEGO_NATIVE_SHADER_MISS_CACHE`, `LEGO_NATIVE_THREADED`, `LEGO_NATIVE_PREPARE_THREADS`, `LEGO_NATIVE_SNAPSHOT_STATE`, `LEGO_NATIVE_FULL_DRAW_PREPARATION`, `LEGO_NATIVE_CHAIN_PRIORITY`;
   - **launcher rule (unattended, pinned inputs only):** it uses `menu`, `profile: true`, `triggers`, `toml` edits or `seed_cache`;
-  - its `driver` is not a plain string `drivers/<name>.ps1` (letters, digits, `_`, `-`; forward slash) naming a file in `bench\agent8\run\drivers\` (pinned). No arguments: the `{script, args}` form is refused, and so is any other runner file (it could start a game, bin, env or matrix that was never checked).
+  - its `driver` is not exactly `drivers/thread-cpu.ps1`, `drivers/pso-stats-at-end.ps1` or `drivers/io-counters.ps1`: a plain string, forward slash, exact case, and the file must be in `bench\agent8\run\drivers\` (pinned). Every other driver is refused, `drivers/sys-csv.ps1` too. No arguments: the `{script, args}` form is refused, and so is any other runner file (it could start a game, bin, env or matrix that was never checked).
 - A pinned file changed.
 - `run-matrix.ps1 -PlanOnly` reports an error or a skipped arm.
 - The runner estimate + 10 min would end after 07:30.
@@ -155,6 +155,7 @@ If any of them changes, appears or disappears, it refuses the next window. It ch
 - the bin hashes, against the ones logged at the GO;
 - the deadline (estimate + 10 min by 07:30) and the latest start (06:45);
 - the session: desktop `WinSta0\Default`, no LogonUI, AC power (the last gate sample may be a minute old);
+- no build or game process (the quiet gate's build list and `legodimensions`), checked again at that moment;
 - that the HOLD is still its own.
 
 If any fails, the log says `START REFUSED: ...` and no window runs. If they pass:
@@ -173,7 +174,13 @@ powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File bench\agent8
 - **`-NonInteractive`:** if the runner ever asked for input, it fails at once instead of waiting all night. `run-matrix.ps1` only asks without `-Matrix` or without `-NoPrompt`.
 - **Environment:** `RUN-NIGHT.cmd` clears `REX_TIMER_WAIT_BLOCKING` and `LEGO_GPU_WAIT_STATS`, and the launcher removes all 11 keys at its start (logged in yellow if one was set) and again right before the runner starts. Any other `REX_*` / `LEGO_*` variable is logged at start (`environment: other REX_*/LEGO_* variables (passed on to the runner as they are): ...`) and passed on unchanged.
 - **Output:** the runner runs as its own process. Its output goes to `status\runner-<id>-<HHmm>.out.txt` and `.err.txt` and, line by line as it comes, to the console and `status\runner-<id>-<HHmm>.txt`. The first line of that file is the launcher's quiet-gate line. The `END` line in the log ends with `out dir <path>`.
-- **While it runs**, the launcher checks every second for the STOP file and for the end time + 15 min (07:45). Either one kills the runner and every process it started (`taskkill /T /F`); in real mode it also kills a `legodimensions.exe` from `build\agent2` that started during the window in this session. The log then says `!!! <why>: the runner (pid N) and every process it started are killed now (taskkill /T /F)`, `taskkill: ...` and `runner stopped: yes`, and the `END` line says `stopped early: <why>`. If the launcher itself fails while the runner runs, it kills the runner too: the runner never runs unwatched.
+- **While it runs**, the launcher checks every second for the STOP file and for the end time (07:30, a hard stop). Either one stops the window at once:
+  - It kills the runner first, through its own process handle.
+  - Then it kills every process the runner started, parents first. It finds them by walking the parent pids down from the runner, and it only kills a process that started after the runner (creation time), so a reused pid is never hit. It walks up to 3 times, until nothing is left. There is no `taskkill`.
+  - In real mode it also kills a `legodimensions.exe` from `build\agent2` that started during the window in this session.
+  - The log says `!!! <why>: the runner (pid N) and every process it started are killed now`, `runner pid N killed`, `killed (walk k): <name>:<pid>, ...` and `runner stopped: yes`. The `END` line says `stopped early: <why>; the runner and everything it started were killed`.
+  - In the `killed (walk k)` list, `(already gone)` means the process had ended before its turn, and `(ended on its own)` means it was ending anyway and refused the kill but was gone within 3 s (usually a `conhost.exe` whose program was just killed). Both are normal. Only `(NOT killed: ...)` means a process is still running; the next walk then tries it again.
+  - If the launcher itself fails while the runner runs (`!!! launcher error while the runner was running (...)`), or someone presses Ctrl+C (`!!! the launcher was interrupted (Ctrl+C?) while the runner was running`), it kills the runner and its processes the same way: the runner never runs unwatched.
 - **After the run** it checks the pins, the matrix json and the bin hashes again. Any change adds `SUSPECT: ...` to the `END` line and to `last-result.txt`.
 
 **Quiet gate.** One sample per minute. It starts after the GO is accepted (HOLD written, programs closed). All of these must hold:
@@ -235,11 +242,11 @@ HH:mm:ss quiet gate: DEADLINE (...; after N min; window not started)
 
 States: `waiting-for-go`, `waiting-for-quiet`, `running`, `refused-at-start`, `ended`.
 
-**Exit codes:** 0 = normal end (07:30, STOP, `-MaxGo`), 2 = refused at start (also: an unknown argument, a test hook without `-DryRun`, a second launcher), 3 = launcher error. Any other code (1) means PowerShell itself failed before the launcher could log it: see the red text in the window. `RUN-NIGHT.cmd` shows a line for each and passes the code on.
+**Exit codes:** 0 = normal end (07:30, STOP, `-MaxGo`), 2 = refused at start (also: an unknown argument, a test hook without `-DryRun`, a second launcher), 3 = launcher error. Any other code means the launcher was interrupted (Ctrl+C), or PowerShell itself failed before the launcher could log it: see the text in the window and `status\log.txt`. After Ctrl+C, `state.txt` says `ended` and `interrupted (Ctrl+C?) before a normal end`. `RUN-NIGHT.cmd` shows a line for each and passes the code on.
 
 **Start log.** The first lines in `status\log.txt` show:
 
-- the start checks: desktop, LogonUI, the power line (`power AC (ACLineStatus n, BatteryFlag n, battery n %)`), the end time, the latest window start, and the time a window still running is stopped (end time + 15 min). It refuses to start when the end time is more than 14 h away (started after 07:30);
+- the start checks: desktop, LogonUI, the power line (`power AC (ACLineStatus n, BatteryFlag n, battery n %)`), the end time (07:30), the latest window start (06:45), and the time a window still running is stopped (the end time itself, 07:30). It refuses to start when the end time is more than 14 h away (a start before 17:30 or after 07:30);
 - any leftover `REX_*` / `LEGO_*` variables;
 - the pins.
 
@@ -248,16 +255,17 @@ States: `waiting-for-go`, `waiting-for-quiet`, `running`, `refused-at-start`, `e
 - Everything happens in `status-dryrun\[<tag>\]`: GO, HOLD, STOP and status files. It never touches the real `perf-notes` files.
 - It closes no apps and changes neither the screensaver, nor the keep-awake state, nor Quick Edit. It only logs "would ...".
 - It never starts a window: it prints the command instead. It does run `run-matrix.ps1 -PlanOnly`, which reads the matrix, writes nothing and starts nothing, to get the estimate.
-- The test hooks work only together with `-DryRun`: `-SampleSeconds`, `-GiveUpMinutes`, `-StrictMinutes`, `-StopAt 'HH:mm'|'yyyy-MM-dd HH:mm'`, `-StartBy` (latest window start, same format; default 06:45, or the `-StopAt` time), `-GraceMinutes` (default 15), `-MatrixDir`, `-PollSeconds`, `-MaxGo`, `-GateFixture <json>`, `-FakeRunner <script>` and `-SkipStartChecks`. Without `-DryRun` it refuses them (exit 2).
+- The test hooks work only together with `-DryRun`: `-SampleSeconds`, `-GiveUpMinutes`, `-StrictMinutes`, `-StopAt 'HH:mm'|'yyyy-MM-dd HH:mm'`, `-StartBy` (latest window start, same format; default 06:45, or the `-StopAt` time), `-GraceMinutes` (default 0: a window still running at the end time is stopped then; tests may add minutes), `-MatrixDir`, `-PollSeconds`, `-MaxGo`, `-GateFixture <json>`, `-FakeRunner <script>`, `-TestFailAfter <s>` (a simulated launcher error s seconds after the fake runner starts) and `-SkipStartChecks`. Without `-DryRun` it refuses them (exit 2).
 - An unknown argument is refused (exit 2), so a mistyped `-DryRun` can't start real mode.
-- `-FakeRunner` runs the given script instead of the runner (`build\agent5\launch-test\fake-runner.ps1` prints ticks and can start a sleeping child), to test the run, STOP during a window and the end-time kill. In a dry run the kill never touches `legodimensions.exe`.
+- `-FakeRunner` runs the given script instead of the runner (`build\agent5\launch-test\fake-runner.ps1` prints ticks and can start a sleeping child), to test the run, STOP during a window, the end-time kill, a launcher error and Ctrl+C. In a dry run the kill never touches `legodimensions.exe`.
 - `-SkipStartChecks` logs the start checks and the last checks (desktop, LogonUI, AC) instead of refusing on them, so the tests can run on an agent's hidden desktop.
 - `-GateFixture` replaces the gate's sensors with `{"samples":[{"cpu":{"MsMpEng":0.02,...},"builds":[],"ram_gb":12,"disk_gb":50,"logonui":false,"ac":true}, ...]}`.
   - The samples are used in order, and the last one repeats.
   - A field set to `"real"` (or left out) is measured on this PC.
+  - A top-level `"builds_at_start": ["ninja:4242"]` stands in for the build check in the last checks right before the start. It tests that a build that starts after the gate passed still refuses the start.
 - **Tests:** `build\agent5\launch-test\run-tests.ps1 -Group go|gate|hold|run|pin`. Results go to `build\agent5\launch-test\results\`.
-  - `go`: GO rules (hash, bins, env keys, drivers, malformed lines), start refusals (desktop, 14 h, unknown argument, hooks, a second launcher), the deadline and the latest start.
-  - `gate`: the quiet gate, including a build running, STOP, the relaxed rule and the close list (dry run, with stand-in programs).
-  - `run`: the fake runner: a normal end, STOP during a window, and the end time + grace kill (the whole process tree must be gone).
+  - `go`: GO rules (hash, bins, env keys, malformed lines, and 5 driver cases: a runner file, the `{script, args}` form, a backslash, a missing file, and `drivers/sys-csv.ps1`, which is not on the list), start refusals (desktop, 14 h, unknown argument, hooks, a second launcher), the deadline and the latest start.
+  - `gate`: the quiet gate, including a build running (the gate waits, then gives up), a build found by the last check right before the start (`START REFUSED`), STOP, the relaxed rule and the close list (dry run, with stand-in programs).
+  - `run`: the fake runner: a normal end, STOP during a window, the end-time kill, a launcher error during the window (`-TestFailAfter`) and Ctrl+C (`send-ctrlc.ps1`). The fake runner's sleeping child must be killed too, and the whole process tree must be gone.
   - `hold`: HOLD handling.
   - `pin`: changed pinned files. It edits `RUN-NIGHT.cmd` for a few seconds and puts it back, so run it alone, with no launcher running.

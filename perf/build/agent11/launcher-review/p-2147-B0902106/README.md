# Overnight launcher: RUN-NIGHT.cmd

By Agent 5 (task #4), 2026-11-22. **The first part is for you, the user.** The part for the agents starts at "For the agents".

## What it is

Timing runs only count when they run on your own desktop, with nobody touching the PC. This launcher lets the agents run timing windows while you sleep:

1. You start it once, before bed.
2. It waits until an agent says a window is ready.
3. It waits until the PC is quiet, then runs that window. A window is the agents' test runner starting and closing the game many times, for about 30-40 minutes.
4. It starts no window after 06:45, and it ends by itself at **07:30**.

## How to start it

1. Plug the laptop in (AC power). Leave the lid open.
2. Double-click **`bench\agent5\launch\RUN-NIGHT.cmd`**.
3. The window should soon say `waiting for ...\perf-notes\WINDOW-GO.txt`. **Leave the window open** and go to bed.
   - Don't lock the PC (no Win+L) and don't close the lid. A locked or sleeping PC can't run timing windows.
   - You can turn the screen brightness down.
   - Before a window starts, it closes ChatGPT, the Copilot app, Roblox (the player and the Store app), Task Manager and Wallpaper Engine itself. It leaves Roblox Studio and every other program alone.
4. If it refuses to start, it says why in red and changes nothing. Possible reasons:
   - it is already morning (after 07:30 it would run for more than 14 hours): start it in the evening
   - not on AC power, or Windows can't tell whether it is
   - the PC is locked
   - it was not started on your own desktop
   - a `perf-notes\WINDOW-STOP.txt` file exists: delete it
   - another launcher is already running
   - one of the files it checks at start is missing

## What it does during the night

- Every 15 s it checks for `perf-notes\WINDOW-GO.txt`, the agents' "window ready" note.
- When that note comes:
  1. It checks the note against strict rules (see "For the agents"). If something is wrong, it writes the reason in its log, deletes the note and goes back to waiting. Nothing is run.
  2. It writes `perf-notes\WINDOW-HOLD.txt`, which tells every agent to keep the PC quiet. If an agent already left a HOLD note there, the launcher doesn't touch it and waits until it is gone.
  3. It closes the five programs above if they are open.
  4. It waits until the PC is quiet:
     - no builds running;
     - Windows Defender, Office and the "Cross Device" service idle;
     - enough free memory and disk space.

     If that doesn't happen within 2 hours, it skips the window.
  5. It closes the five programs again if they came back, checks everything once more, then runs the window. That is the agents' runner `bench\agent8\run\run-matrix.ps1`, which starts and closes the game again and again, about 30-40 minutes in total.
  6. It removes its HOLD note, unless the agents' hold manager already has, and waits for the next window.
- It never starts a window that would end after 07:30, and it starts none after 06:45. At 07:30 it ends.
- If a window is somehow still running at 07:45, it stops that window (it closes the runner and the game) and ends.

## What it changes on your PC, and what it puts back

| What | What it does | Put back at the end? |
|---|---|---|
| Screensaver | sets it to "(None)" when it starts | yes. It was already "(None)" when I checked at 19:37 |
| Sleep and screen-off | keeps the PC and the screen awake | yes. Normal sleep comes back as soon as the launcher ends |
| ChatGPT, the Copilot app, Roblox (player and Store app), Task Manager, Wallpaper Engine | closes them when a window is accepted and again right before it starts, only in your own session. The Copilot app, the Store Roblox app and Wallpaper Engine's ui32/ui64 are closed only when the program file is in their own install folder, because other programs use the same names. Task Manager may refuse (it runs as admin); the launcher then writes that in its log and goes on. Roblox Studio is not touched | no, open them again in the morning |
| Its own window | turns off "Quick Edit", so a stray click in the window can't pause it | it only affects that window |
| The game | the runner starts `legodimensions.exe` from `build\agent2\...-bin` folders | the runner closes it after each run |

Files it uses:

- `perf-notes\WINDOW-GO.txt`: read, then deleted.
- `perf-notes\WINDOW-HOLD.txt`: written while a window waits or runs, deleted afterwards. It only ever deletes its own; the agents' hold manager may also take it over or delete it.
- `perf-notes\WINDOW-STOP.txt`: if it appears, it is read and deleted, and the launcher ends.
- `bench\agent5\launch\status\`: its own status and logs.
- `build\agent8\matrix\<date-time>\`: the runner's results.

It builds nothing, changes no code and no game files, and runs nothing except `run-matrix.ps1`.

## How to stop it

- **Normal way:** create a file named `WINDOW-STOP.txt` in the `perf-notes` folder (any content, even empty).
  - While waiting, it ends within a few seconds and puts everything back.
  - During a window, it stops the window at once: it closes the runner and the game (that window's numbers are lost), puts everything back and ends. This takes a few seconds.
- **Fast way:** click in its window and press **Ctrl+C**.
  - It still puts everything back (screensaver, HOLD note).
  - A window that is running stops part-way (the launcher closes the runner and the game), and its numbers are lost. If the game stays open anyway, close it.
  - If the window asks `Terminate batch job (Y/N)?`, type `Y`.
- **If you close the window with the X** (or the PC restarts), the launcher can't clean up:
  1. If the game is still open, close it. In Task Manager it is `legodimensions.exe`.
  2. Delete `perf-notes\WINDOW-HOLD.txt` if it is still there.
  3. Screensaver: go to Settings > Personalization > Lock screen > Screen saver.
     - Set it back to what `bench\agent5\launch\status\screensaver-saved.txt` says.
     - "ScreenSaveActive=0" plus an empty SCRNSAVE.EXE means "(None)". In that case there is nothing to do.
     - If you start the launcher again first, it moves that file to `status\screensaver-saved-unrestored-<date-time>.txt` and says so in yellow. The values to put back are then in that file.
  4. Sleep: nothing to do. Windows goes back to normal by itself.

## In the morning

- The window says "The launcher ended normally" (or why it ended). Press a key to close it.
- `bench\agent5\launch\status\last-result.txt` shows the last window and where its results are.
- `bench\agent5\launch\status\log.txt` has everything it did, with times.

---

## For the agents

**GO file.** `perf-notes\WINDOW-GO.txt` holds exactly one line of 6 tokens:

```
GO <window-id> <matrix json name in bench\agent8\run\> <sha256 of that json> only=<arm>[,<arm>...] repeats=<1-20>
```

Example: `GO W6 matrix-window6.json 3F2A...64 hex... only=s0,p2,p2f,p2fc repeats=3`.

- **window-id:** 1-32 characters from `A-Z a-z 0-9 _ . -`.
- **Matrix:** a plain file name. It must sit directly in `bench\agent8\run\`.
- **sha256:** checked against the file at GO time and again when the window starts.
- **The GO file is deleted as soon as it is read, good or bad.** It is only read while the launcher is idle, so a GO written during a window waits until that window ends.
- The result goes to `status\last-go.txt` and `status\last-result.txt`.

**It refuses a GO (logs why, deletes it, keeps waiting) when any of these holds:**

- The line is malformed.
- The sha256 does not match.
- The JSON is unreadable or has no arms.
- An `only=` arm is not in the file.
- Any arm in the file (not only the `only=` ones) breaks a rule:
  - its `bin` is not `build/agent2/<name>-bin`, or that folder lacks `MANIFEST.txt` or `legodimensions.exe`;
  - its `env` has a key that is not one of these 11 (exact case; `build/agent8/w8w9/ENV-KEYS-F1.txt`, approved by Agent 1 at 21:14): `REX_TIMER_WAIT_BLOCKING`, `LEGO_GPU_WAIT_STATS`, `LEGO_GPU_WAIT_BACKOFF_US`, `LEGO_GPU_WAIT_SPIN_US`, `LEGO_NATIVE_FRAME_METRICS`, `LEGO_NATIVE_SHADER_MISS_CACHE`, `LEGO_NATIVE_THREADED`, `LEGO_NATIVE_PREPARE_THREADS`, `LEGO_NATIVE_SNAPSHOT_STATE`, `LEGO_NATIVE_FULL_DRAW_PREPARATION`, `LEGO_NATIVE_CHAIN_PRIORITY`;
  - **launcher rule (unattended, pinned inputs only):** it uses `menu`, `profile: true`, `triggers`, `toml` edits or `seed_cache`;
  - its `driver` is not a plain string `drivers/<name>.ps1` (letters, digits, `_`, `-`; forward slash) naming a file in `bench\agent8\run\drivers\` (pinned). No arguments: the `{script, args}` form is refused, and so is any other runner file (it could start a game, bin, env or matrix that was never checked).
- A pinned file changed.
- `run-matrix.ps1 -PlanOnly` reports an error or a skipped arm.
- The runner estimate + 10 min would end after 07:30.
- The GO was read at or after the latest window start, 06:45.
- The HOLD file can't be written, or the bin files can't be hashed.
- The GO file can't be deleted. It is then not used, and it is ignored until it changes: delete it by hand.

**Warnings, not refusals.** These are logged as `WARN:` in `status\log.txt` and the window log:

- The matrix has no top-level `"sys_csv": true`, so the runs write no sys.json. Ask Agent 5 if this should refuse instead.
- The `-PlanOnly` output has a `FUNCTIONAL ONLY` line. The runner prints that when it is not on the input desktop.

**At GO acceptance** it logs:

- the `GO ACCEPTED` line;
- the sha256 of `legodimensions.exe` and `MANIFEST.txt` in each `only=` bin, as `bin build/agent2/<name>-bin/<file> sha256 <hash>`;
- the warnings above;
- the `-PlanOnly` output, in the window log only, as `plan|` lines.

**Pins.** At start it hashes these files and writes the list to `status\pins.txt`:

- itself and `RUN-NIGHT.cmd`;
- in `bench\agent8\run\`: `run-matrix.ps1`, `run-timing.ps1`, `common.ps1`, `timing-env.ps1`, `winhelper.cs`, every `*.py` / `*.cs`, and everything under `drivers\`;
- `harness\legodimensions.toml` and `harness\nvml.cs`.

If any of them changes, appears or disappears, it refuses the next window. It checks at GO time and again just before the start. A change during a run marks the result SUSPECT.

> **So after the user starts it (~23:45), nobody may edit, add or remove any of these files.** That includes adding a new `.py` or `.cs` file to `bench\agent8\run\`. New matrix `.json` files in `bench\agent8\run\` are fine: they are not pinned. Each GO names one by sha256.

**Last checks, right before the start.** First it closes the five programs again (they may have come back during the gate). In real mode it then opens the matrix json read-only and keeps it open until the runner ends, so nobody can change or delete it. Then all of these are checked again:

- the pins;
- the matrix: its sha256 and every rule above;
- the bin hashes, against the ones logged at the GO;
- the deadline (estimate + 10 min by 07:30) and the latest start (06:45);
- the session: desktop `WinSta0\Default`, no LogonUI, AC power (the last gate sample may be a minute old);
- that the HOLD is still its own.

If any fails, the log says `START REFUSED: ...` and no window runs. If they pass:

1. It logs `bins unchanged since the GO`.
2. It removes the 11 env keys from its own environment (arms set them through the matrix only).
3. It logs `power scheme at the start: ...` (from `powercfg /getactivescheme`).
4. It starts the runner.

**The command it runs.** Only this, with the 11 env keys removed from its environment:

```
powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File bench\agent8\run\run-matrix.ps1 -Matrix <json> -Only <arms> -Repeats <n> -ColdShared -NoPrompt
```

- **`-NonInteractive`:** if the runner ever asked for input, it fails at once instead of waiting all night. `run-matrix.ps1` only asks without `-Matrix` or without `-NoPrompt`.
- **Environment:** `RUN-NIGHT.cmd` clears `REX_TIMER_WAIT_BLOCKING` and `LEGO_GPU_WAIT_STATS`, and the launcher removes all 11 keys at its start (logged in yellow if one was set) and again right before the runner starts. Any other `REX_*` / `LEGO_*` variable is logged at start (`environment: other REX_*/LEGO_* variables (passed on to the runner as they are): ...`) and passed on unchanged.
- **Output:** the runner runs as its own process. Its output goes to `status\runner-<id>-<HHmm>.out.txt` and `.err.txt` and, line by line as it comes, to the console and `status\runner-<id>-<HHmm>.txt`. The first line of that file is the launcher's quiet-gate line. The `END` line in the log ends with `out dir <path>`.
- **While it runs**, the launcher checks every second for the STOP file and for the end time + 15 min (07:45). Either one kills the runner and every process it started (`taskkill /T /F`); in real mode it also kills a `legodimensions.exe` from `build\agent2` that started during the window in this session. The log then says `!!! <why>: the runner (pid N) and every process it started are killed now (taskkill /T /F)`, `taskkill: ...` and `runner stopped: yes`, and the `END` line says `stopped early: <why>`. If the launcher itself fails while the runner runs, it kills the runner too: the runner never runs unwatched.
- **After the run** it checks the pins, the matrix json and the bin hashes again. Any change adds `SUSPECT: ...` to the `END` line and to `last-result.txt`.

**Quiet gate.** One sample per minute. It starts after the GO is accepted (HOLD written, programs closed). All of these must hold:

- **CPU:** MsMpEng, OfficeClickToRun and CrossDeviceService, from CIM `Win32_Process` kernel+user time, summed per name. The last 3 samples must all have a figure (so 3 consecutive 1-minute averages) and each must be < 0.1 core.
- **Relaxed rule for MsMpEng, from 30 min after the GO** (Agent 1, 19:31): MsMpEng ≤ 1.2 cores in all 3, with max − min ≤ 0.2. It is logged as `relaxed gate` in `status\log.txt`, the window log and `status\relaxed-gate.txt`.
- **Builds and games:** in each of the 3 samples, no process matching the runner's build list (`clang*` `lld*` `ld.lld*` `llvm-*` `ninja*` `cmake*` `dxc*` `cl` `link` `lib` `mt` `rc` `msbuild*` `rexglue*` `codegen*` `sccache*` `ccache*` `rustc` `cargo`) or `legodimensions`. `clangd*` and `clang-format*` don't count (editors run them all the time).
- **Memory and disk:** RAM available ≥ 6 GB and C: free ≥ 6 GB.
- **Session:** no LogonUI (not locked) and on AC power.
  - AC comes from `GetSystemPowerStatus`. It counts as AC only when `ACLineStatus` = 1, or when `BatteryFlag` = 128 (no battery).
  - Anything else, including a failed call, counts as not on AC: the start is refused, or the gate fails.
- **HOLD:** the HOLD file must be its own (see HOLD).
- **Time limits:** the estimate + 10 min must still end by 07:30, no window starts at or after 06:45, and it gives up 120 min after the GO.

The gate result is one line (Agent 12's G12 format), written to `status\log.txt`, `status\gate.txt` and `status\window-<id>-<HHmm>.log`:

```
HH:mm:ss quiet gate: STRICT (MsMpEng a/b/c, OfficeClickToRun a/b/c, CrossDeviceService a/b/c)
HH:mm:ss quiet gate: RELAXED (...; after N min)
HH:mm:ss quiet gate: GAVE UP (...; after N min; window not started)
HH:mm:ss quiet gate: DEADLINE (...; after N min; window not started)
```

- After `GAVE UP` or `DEADLINE`, the `GATE REFUSED` line in `status\log.txt` and `status\last-result.txt` adds the last reason it waited for: `(last wait: ...)`. Each gate sample's reason is also in the log (`gate N ... -> wait: ...`). `DEADLINE` covers both time limits: `GATE REFUSED: deadline: ...` (07:30) or `GATE REFUSED: latest start: ...` (06:45).
- A `STRICT` or `RELAXED` line means the gate passed. The last checks can still refuse the start: look for `START REFUSED` or `START` in `status\log.txt` or `status\last-result.txt`.

**HOLD.** `perf-notes\WINDOW-HOLD.txt`:

- **Writing:** at GO acceptance it is written only if there is no HOLD file. The content is a marker: `HOLD window <id> by Agent 5's overnight launcher (...), pid <pid>, since <time>, token <guid>`.
- **A foreign HOLD:** any HOLD without its token is never replaced or deleted. While one exists, the gate fails (`wait: foreign HOLD ('...')`), and the window waits within the 120-min and 07:30 limits.
- **Checks:** at GO acceptance, at every gate sample and just before the start.
  - If its own HOLD has disappeared, it writes it again and logs that.
  - If someone replaced it, it leaves that one alone, logs that, and the gate fails until it is gone.
- **During the run** the launcher doesn't touch it. Agent 1's hold manager takes it over once the runner has made its matrix folder, and removes it when summary.md appears.
- **At the end** of every accepted GO (window run, gate gave up, start refused, STOP) and when the launcher ends, it deletes the HOLD only if its token is still in it. Otherwise it logs `HOLD already gone (the hold manager removed it)` or `HOLD is not this window's any more (the hold manager took it over): left as it is`. Both are normal.

**STOP.** `perf-notes\WINDOW-STOP.txt`:

- If it exists at start, the launcher refuses to start.
- While waiting for a GO, or during the gate, the launcher deletes it and ends within about a second. No window starts.
- During a window, the launcher kills the runner and everything it started within about a second (see "While it runs"), and the `END` line says `stopped early: STOP file`. Then it deletes the STOP file and ends.

**Status files** in `bench\agent5\launch\status\`:

| File | Contents |
|---|---|
| `state.txt` | state and heartbeat |
| `log.txt` | everything it did |
| `gate.txt` | gate result lines |
| `last-go.txt` | the last GO: when it was read, the line, the verdict, when it was decided |
| `last-result.txt` | the last result |
| `pins.txt` | the pinned files |
| `screensaver-saved.txt` | the user's screensaver settings |
| `screensaver-saved-unrestored-<date-time>.txt` | settings that an earlier launcher saved but could not put back |
| `relaxed-gate.txt` | the relaxed-gate values |
| `window-<id>-<HHmm>.log` | that window's log |
| `runner-<id>-<HHmm>.txt` | the runner's output |
| `runner-<id>-<HHmm>.out.txt`, `.err.txt` | the runner's raw stdout and stderr |

States: `waiting-for-go`, `waiting-for-quiet`, `running`, `refused-at-start`, `ended`.

**Exit codes:** 0 = normal end (07:30, STOP, `-MaxGo`), 2 = refused at start (also: an unknown argument, a test hook without `-DryRun`, a second launcher), 3 = launcher error. Any other code (1) means PowerShell itself failed before the launcher could log it: see the red text in the window. `RUN-NIGHT.cmd` shows a line for each and passes the code on.

**Start log.** The first lines in `status\log.txt` show:

- the start checks: desktop, LogonUI, the power line (`power AC (ACLineStatus n, BatteryFlag n, battery n %)`), the end time, the latest window start, and the time a window still running is stopped (end time + 15 min). It refuses to start when the end time is more than 14 h away (started after 07:30);
- any leftover `REX_*` / `LEGO_*` variables;
- the pins.

**Dry run:** `powershell -File run-night.ps1 -DryRun [-DryRunTag t1] ...`

- Everything happens in `status-dryrun\[<tag>\]`: GO, HOLD, STOP and status files. It never touches the real `perf-notes` files.
- It closes no apps and changes neither the screensaver, nor the keep-awake state, nor Quick Edit. It only logs "would ...".
- It never starts a window: it prints the command instead. It does run `run-matrix.ps1 -PlanOnly`, which reads the matrix, writes nothing and starts nothing, to get the estimate.
- The test hooks work only together with `-DryRun`: `-SampleSeconds`, `-GiveUpMinutes`, `-StrictMinutes`, `-StopAt 'HH:mm'|'yyyy-MM-dd HH:mm'`, `-StartBy` (latest window start, same format; default 06:45, or the `-StopAt` time), `-GraceMinutes` (default 15), `-MatrixDir`, `-PollSeconds`, `-MaxGo`, `-GateFixture <json>`, `-FakeRunner <script>` and `-SkipStartChecks`. Without `-DryRun` it refuses them (exit 2).
- An unknown argument is refused (exit 2), so a mistyped `-DryRun` can't start real mode.
- `-FakeRunner` runs the given script instead of the runner (`build\agent5\launch-test\fake-runner.ps1` prints ticks and can start a sleeping child), to test the run, STOP during a window and the end-time kill. In a dry run the kill never touches `legodimensions.exe`.
- `-SkipStartChecks` logs the start checks and the last checks (desktop, LogonUI, AC) instead of refusing on them, so the tests can run on an agent's hidden desktop.
- `-GateFixture` replaces the gate's sensors with `{"samples":[{"cpu":{"MsMpEng":0.02,...},"builds":[],"ram_gb":12,"disk_gb":50,"logonui":false,"ac":true}, ...]}`.
  - The samples are used in order, and the last one repeats.
  - A field set to `"real"` (or left out) is measured on this PC.
- **Tests:** `build\agent5\launch-test\run-tests.ps1 -Group go|gate|hold|run|pin`. Results go to `build\agent5\launch-test\results\`.
  - `go`: GO rules (hash, bins, env keys, drivers, malformed lines), start refusals (desktop, 14 h, unknown argument, hooks, a second launcher), the deadline and the latest start.
  - `gate`: the quiet gate, including a build running, STOP, the relaxed rule and the close list (dry run, with stand-in programs).
  - `run`: the fake runner: a normal end, STOP during a window, and the end time + grace kill (the whole process tree must be gone).
  - `hold`: HOLD handling.
  - `pin`: changed pinned files. It edits `RUN-NIGHT.cmd` for a few seconds and puts it back, so run it alone, with no launcher running.

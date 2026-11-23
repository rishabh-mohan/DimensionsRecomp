# Overnight launcher: RUN-NIGHT.cmd

By Agent 5 (task #4), 2026-11-22. **The first part is for you, the user.** The part for the agents starts at "For the agents".

## What it is

Timing runs only count when they run on your own desktop, with nobody touching the PC. This launcher lets the agents run timing windows while you sleep:

1. You start it once, before bed.
2. It waits until an agent says a window is ready.
3. It waits until the PC is quiet, then runs that window. A window is the agents' test runner starting and closing the game many times, for about 30-40 minutes.
4. It ends by itself at **07:30**.

## How to start it

1. Plug the laptop in (AC power). Leave the lid open.
2. Double-click **`bench\agent5\launch\RUN-NIGHT.cmd`**.
3. The window should soon say `waiting for ...\perf-notes\WINDOW-GO.txt`. **Leave the window open** and go to bed.
   - Don't lock the PC (no Win+L) and don't close the lid. A locked or sleeping PC can't run timing windows.
   - You can turn the screen brightness down.
   - It closes ChatGPT, Copilot, Roblox, Task Manager and Wallpaper Engine itself when a window starts.
4. If it refuses to start, it says why in red and changes nothing. Possible reasons:
   - on battery
   - the PC is locked
   - it was not started on your own desktop
   - a `perf-notes\WINDOW-STOP.txt` file exists: delete it
   - another launcher is already running
   - one of the files it checks at start is missing

## What it does during the night

- Every 15 s it checks for `perf-notes\WINDOW-GO.txt`, the agents' "window ready" note.
- When that note comes:
  1. It checks the note against strict rules (see "For the agents"). If something is wrong, it writes the reason in its log, deletes the note and goes back to waiting. Nothing is run.
  2. It writes `perf-notes\WINDOW-HOLD.txt`, which tells every agent to keep the PC quiet.
  3. It closes the five programs above if they are open.
  4. It waits until the PC is quiet: no builds running, Windows Defender, Office and the "Cross Device" service idle, and enough free memory and disk space. If that doesn't happen within 2 hours, it skips the window.
  5. It runs the window. That is the agents' runner `bench\agent8\run\run-matrix.ps1`, which starts and closes the game again and again, about 30-40 minutes in total.
  6. It removes the HOLD note and waits for the next window.
- It never starts a window that would end after 07:30. At 07:30 it ends.

## What it changes on your PC, and what it puts back

| What | What it does | Put back at the end? |
|---|---|---|
| Screensaver | sets it to "(None)" when it starts | yes. It was already "(None)" when I checked at 19:37 |
| Sleep and screen-off | keeps the PC and the screen awake | yes. Normal sleep comes back as soon as the launcher ends |
| ChatGPT, Copilot, Roblox, Task Manager, Wallpaper Engine | closes them when a window starts. Task Manager may refuse (it runs as admin); the launcher then just writes that in its log and goes on | no, open them again in the morning |
| Its own window | turns off "Quick Edit", so a stray click in the window can't pause it | it only affects that window |
| The game | the runner starts `legodimensions.exe` from `build\agent2\...-bin` folders | the runner closes it after each run |

Files it uses:

- `perf-notes\WINDOW-GO.txt`: read, then deleted.
- `perf-notes\WINDOW-HOLD.txt`: written while a window waits or runs, deleted afterwards.
- `perf-notes\WINDOW-STOP.txt`: if it appears, it is read and deleted, and the launcher ends.
- `bench\agent5\launch\status\`: its own status and logs.
- `build\agent8\matrix\<date-time>\`: the runner's results.

It builds nothing, changes no code and no game files, and runs nothing except `run-matrix.ps1`.

## How to stop it

- **Normal way:** create a file named `WINDOW-STOP.txt` in the `perf-notes` folder (any content, even empty).
  - While waiting, it ends within about 15 s and puts everything back.
  - During a window, it lets the window finish first (up to about 40 minutes), then ends.
- **Fast way:** click in its window and press **Ctrl+C**.
  - It still puts everything back (screensaver, HOLD note).
  - A window that is running stops part-way, and its numbers are lost. If the game stays open, close it.
  - If the window asks `Terminate batch job (Y/N)?`, type `Y`.
- **If you close the window with the X** (or the PC restarts), the launcher can't clean up:
  1. Delete `perf-notes\WINDOW-HOLD.txt` if it is still there.
  2. Screensaver: Settings > Personalization > Lock screen > Screen saver. Set it back to what `bench\agent5\launch\status\screensaver-saved.txt` says. "ScreenSaveActive=0" plus an empty SCRNSAVE.EXE means "(None)", so in that case there is nothing to do.
  3. Sleep: nothing to do. Windows goes back to normal by itself.

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
  - its `env` has a key other than `REX_TIMER_WAIT_BLOCKING` or `LEGO_GPU_WAIT_STATS` (exact case);
  - **launcher rule (unattended, pinned inputs only):** it uses `menu`, `profile: true`, `triggers`, `toml` edits or `seed_cache`;
  - its `driver` is not one of the pinned runner files.
- A pinned file changed.
- `run-matrix.ps1 -PlanOnly` reports an error or a skipped arm.
- The runner estimate + 10 min would end after 07:30.

**Pins.** At start it hashes these files and writes the list to `status\pins.txt`:

- itself and `RUN-NIGHT.cmd`;
- in `bench\agent8\run\`: `run-matrix.ps1`, `run-timing.ps1`, `common.ps1`, `timing-env.ps1`, `winhelper.cs`, every `*.py` / `*.cs`, and everything under `drivers\`;
- `harness\legodimensions.toml` and `harness\nvml.cs`.

If any of them changes, appears or disappears, it refuses the next window. It checks at GO time and again just before the start. A change during a run marks the result SUSPECT.

> **So after the user starts it (~23:45), nobody may edit, add or remove any of these files.** New matrix `.json` files in `bench\agent8\run\` are fine: they are not pinned. Each GO names one by sha256.

**The command it runs.** Only this, with `REX_TIMER_WAIT_BLOCKING` and `LEGO_GPU_WAIT_STATS` removed from its environment:

```
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent8\run\run-matrix.ps1 -Matrix <json> -Only <arms> -Repeats <n> -ColdShared -NoPrompt
```

Its output goes to the console and to `status\runner-<id>-<HHmm>.txt`. The first line of that file is the launcher's quiet-gate line.

**Quiet gate.** One sample per minute. It starts after the GO is accepted (HOLD written, programs closed). All of these must hold:

- **CPU:** MsMpEng, OfficeClickToRun and CrossDeviceService, from CIM `Win32_Process` kernel+user time, summed per name. The last 3 samples must all have a figure (so 3 consecutive 1-minute averages) and each must be < 0.1 core.
- **Relaxed rule for MsMpEng, from 30 min after the GO** (Agent 1, 19:31): MsMpEng ≤ 1.2 cores in all 3, with max − min ≤ 0.2. It is logged as `relaxed gate` in `status\log.txt`, the window log and `status\relaxed-gate.txt`.
- **Builds and games:** in each of the 3 samples, no process matching the runner's build list (`clang*` `lld*` `ninja*` `cmake*` `llvm-*` `dxc*` `cl` `link` `msbuild*` `rexglue*` `codegen*` `sccache*` `ccache*` `rustc` `cargo`) or `legodimensions`.
- **Memory and disk:** RAM available ≥ 6 GB and C: free ≥ 6 GB.
- **Session:** no LogonUI (not locked), on AC power.
- **Time limits:** the estimate + 10 min must still end by 07:30, and it gives up 120 min after the GO.

The gate result is one line (Agent 12's G12 format), written to `status\log.txt`, `status\gate.txt` and `status\window-<id>-<HHmm>.log`:

```
HH:mm:ss quiet gate: STRICT (MsMpEng a/b/c, OfficeClickToRun a/b/c, CrossDeviceService a/b/c)
HH:mm:ss quiet gate: RELAXED (...; after N min)
HH:mm:ss quiet gate: GAVE UP (...; window not started)
HH:mm:ss quiet gate: DEADLINE (...; window not started)
```

**HOLD.** `perf-notes\WINDOW-HOLD.txt` exists from GO acceptance until the window ends (or until the gate gives up). It holds a token. The launcher deletes it only if the token is still its own, so the hold manager may delete it earlier. If it disappears during the gate wait, the launcher logs that and does not write it again.

**STOP.** `perf-notes\WINDOW-STOP.txt`:

- If it exists at start, the launcher refuses to start.
- While waiting for a GO, or during the gate, the launcher deletes it and ends. No window starts.
- During a window, the window finishes first.

**Status files** in `bench\agent5\launch\status\`:

| File | Contents |
|---|---|
| `state.txt` | state and heartbeat |
| `log.txt` | everything it did |
| `gate.txt` | gate result lines |
| `last-go.txt` | the last GO read |
| `last-result.txt` | the last result |
| `pins.txt` | the pinned files |
| `screensaver-saved.txt` | the user's screensaver settings |
| `relaxed-gate.txt` | the relaxed-gate values |
| `window-<id>-<HHmm>.log` | that window's log |
| `runner-<id>-<HHmm>.txt` | the runner's output |

States: `waiting-for-go`, `waiting-for-quiet`, `running`, `refused-at-start`, `ended`.

**Exit codes:** 0 = normal end (07:30, STOP, `-MaxGo`), 2 = refused at start, 3 = launcher error.

**Dry run:** `powershell -File run-night.ps1 -DryRun [-DryRunTag t1] ...`

- Everything happens in `status-dryrun\[<tag>\]`: GO, HOLD, STOP and status files. It never touches the real `perf-notes` files.
- It closes no apps and changes neither the screensaver nor the keep-awake state. It only logs "would ...".
- It never starts a window: it prints the command instead. It does run `run-matrix.ps1 -PlanOnly`, which reads the matrix, writes nothing and starts nothing, to get the estimate.
- The test hooks work only together with `-DryRun`: `-SampleSeconds`, `-GiveUpMinutes`, `-StrictMinutes`, `-StopAt 'HH:mm'|'yyyy-MM-dd HH:mm'`, `-MatrixDir`, `-PollSeconds`, `-MaxGo`, `-GateFixture <json>` and `-SkipStartChecks`. Without `-DryRun` it refuses them (exit 2).
- `-GateFixture` replaces the gate's sensors with `{"samples":[{"cpu":{"MsMpEng":0.02,...},"builds":[],"ram_gb":12,"disk_gb":50,"logonui":false,"ac":true}, ...]}`. Samples are used in order and the last one repeats. A field set to `"real"` (or left out) is measured on this PC.
- The tests are in `build\agent5\launch-test\run-tests.ps1`, in three groups: `go`, `gate` and `pin`. Results go to `build\agent5\launch-test\results\`.

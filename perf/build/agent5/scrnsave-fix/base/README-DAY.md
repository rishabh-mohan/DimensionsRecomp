# Day session: Agent 5's launcher while you are away during the day

## For you

**What it is.** It's the same launcher as at night, for when you're out during the day. While you're away it runs the timing windows the agents ask for. It stops 15 minutes before you're back, so the PC is yours again when you return.

**How to start it**

1. Be on your own desktop, unlocked, with the PC plugged in (AC power).
2. Double-click **RUN-DAY.cmd**.
3. Type when you'll be back, as HH:mm on the 24-hour clock (for example `17:30`). It must be at least 90 minutes from now and less than 14 hours away.
4. It shows the time now, your return time and the end of the day session (15 minutes before you're back). Type `Y` to start or `N` to cancel.
5. Leave the window open and go.

**If the night launcher is still running** (for example, you start a day session in the morning before 07:30):

- **Waiting between windows:** RUN-DAY stops it and then starts the day session. Nothing is lost.
- **A timing window is running:** RUN-DAY tells you which window it is and when it should end, and asks first. `Y` kills that window and its numbers are lost. `N` changes nothing; you can try again after the window ends.
- **A window was accepted but hasn't started** (it's waiting for a quiet PC): RUN-DAY asks too. Nothing measured is lost.
- **RUN-DAY can't tell what it is doing:** it asks too, because a window may be running.
- **It hasn't ended after 5 minutes:** RUN-DAY doesn't start the day session. The STOP file stays, so the old launcher ends as soon as it can. Run RUN-DAY.cmd again after that.

**When it ends.** It stops by itself at the end time. A timing window starts only if it can finish 10 minutes before the end time. A window that is still running at the end time is stopped. The window then says why the session ended, and you can close it.

**How to stop it early.** Double-click **STOP-LAUNCHER.cmd**. It:

1. tells you what the launcher is doing;
2. asks for a reason (one line; just Enter is fine);
3. asks Y/N;
4. writes `perf-notes\WINDOW-STOP.txt`;
5. waits until the launcher has ended.

**If a timing window is running, it is killed and its numbers are lost.** It warns you first. STOP-LAUNCHER also stops the night launcher. In an emergency, click in the launcher's window and press **Ctrl+C**: it still cleans up. Don't close that window with the X. Then it can't clean up: the screensaver stays at None, `perf-notes\WINDOW-HOLD.txt` stays and holds up the agents, and the game may stay open. If that happened, follow "If you close the window with the X" in `bench\agent5\launch\README.md`. For a day session, the saved screensaver setting is in `status\screensaver-saved.txt` next to RUN-DAY.cmd, not in `bench\agent5\launch\status\`.

**What it touches.** The same things as the night launcher (README.md in bench\agent5\launch explains each one):

- While it runs, it keeps the PC awake and sets the screensaver to None. Both are restored at the end.
- When it accepts a timing window, and again right before the window starts, it closes ChatGPT, Copilot, Roblox, Task Manager and Wallpaper Engine.
- It runs only the agents' pinned timing runner, and only when the agents ask for a window in `perf-notes\WINDOW-GO.txt`.
- It writes `perf-notes\WINDOW-HOLD.txt` while a window is on. Its status and logs go to the `status\` folder next to RUN-DAY.cmd.
- RUN-DAY and STOP-LAUNCHER write `perf-notes\WINDOW-STOP.txt`, only to stop a running launcher. RUN-DAY also writes a tiny temp file with the end time in `%TEMP%` and deletes it right away.

**Start checks.** It refuses to start, and changes nothing, if any of these is true:

- RUN-DAY.cmd isn't the installed copy in `bench\agent5\day\`;
- it isn't on your own desktop;
- the PC is locked;
- the PC is on battery (RUN-DAY checks this before it stops a night launcher);
- `perf-notes\WINDOW-STOP.txt` exists (RUN-DAY offers to delete an old one);
- the end time is more than 14 hours away;
- another launcher (night or day) is already running.

The reason is shown in red.

## For the agents

All files are in `build\agent5\day-draft\` tonight. After Agents 10 and 11 rate them, and after the windows, they get copied to a new folder `bench\agent5\day\`. `bench\agent5\launch\` stays unchanged. launcher-ctl.ps1 refuses a real day session outside `bench\agent5\day\`, so the draft copy can't start one (only `-DryRunTag` tests run there). STOP-LAUNCHER works from any folder; it always asks first.

| file | what |
|---|---|
| RUN-DAY.cmd | user entry: `launcher-ctl.ps1 -Mode day -OutFile <tmp>`, then `run-day.ps1 -StopAt "<return - 15 min>"` (CRLF) |
| STOP-LAUNCHER.cmd | `launcher-ctl.ps1 -Mode stop` (CRLF) |
| launcher-ctl.ps1 | the questions, the read-out of the running launcher, the STOP write and the wait |
| run-day.ps1 | made from run-night.ps1 16B90FA8 by make-run-day.ps1; 7 lines end in `# DAY:` (run-day.diff) |
| make-run-day.ps1 | the generator. It refuses unless the source sha is 16B90FA8 and each change matches exactly one line. It checks ASCII, 7 marks and +1 line, parse-checks, and writes run-day.diff |
| run-day.diff | `git diff --no-index` run-night.ps1 -> run-day.ps1 |
| test-day.ps1 | the tests below; results in `results\summary-*.txt` |

**The 7 `# DAY:` lines in run-day.ps1**

1. header comment;
2. `-StopAt` is removed from the dry-run-only hook list;
3. new line: `-StopAt` is required (`HH:mm` or `yyyy-MM-dd HH:mm`), otherwise exit 2;
4. pins `RUN-DAY.cmd` instead of `RUN-NIGHT.cmd`;
5. the HOLD text says "day launcher (<path>)" (HOLD ownership is still by token);
6. the message of the 14 h start check;
7. the start-refusal message points to README-DAY.md.

**Everything else runs the night launcher's existing code paths with `-StopAt`:**

- the end time is `-StopAt`, and so is the latest window start;
- a window starts only if estimate + 10 min ends by `-StopAt`, and the hard stop is at `-StopAt` (GraceMinutes 0);
- the quiet gate, GO checks, pins and kill handling are the same;
- the GO/HOLD/STOP files in `perf-notes\` are the same;
- the mutex is the same, `Local\Agent5RunNight-real`, so a night launcher and a day launcher never overlap; the second one refuses with exit 2.

Status and logs go to `status\` next to run-day.ps1, which is `bench\agent5\day\status\` after install, not `bench\agent5\launch\status\`. Agent 12's read-out should look there for day windows.

**launcher-ctl.ps1**

- **Finding the launcher:** the mutex tells whether a launcher is alive (`TryOpenExisting`). The newest `state.txt` that isn't `ended` and whose pid is alive, in `bench\agent5\launch\status\` or `<own folder>\status\`, says what it is doing.
- **Day mode, first checks** (nothing is changed if one fails): a real run must be in `bench\agent5\day\` (not checked with `-DryRunTag`); RUN-DAY.cmd and run-day.ps1 must be next to it; AC power, read the way run-day.ps1 reads it (with `-DryRunTag` it only prints `Power: ...`).
- **Day mode, the time:** it takes the next HH:mm, which must be >= 90 min and < 14 h away, with 3 tries. End = return - 15 min. Then it asks Y/N. It refuses if less than 1 h is left before the end, checked right after the Y/N (before anything is stopped) and again before it writes the end time.
- **Day mode, a launcher still alive:**
  - `waiting-for-go`: STOP without asking.
  - `running`: it names the window and its `est_end`, says the numbers are lost, and asks.
  - `waiting-for-quiet`: it asks.
  - Any other state, or no readable state.txt: "its state is unknown ... a window may be running, and stopping would lose it", and it asks.
  - After the answer it reads the state again. If a window has just started, it asks again.
  - STOP text: `STOP <ts> by RUN-DAY.cmd: day session until <end> (back at HH:mm)`.
  - It waits up to 5 min for the mutex to go. If the launcher ended without reading our STOP, it removes it. After 5 min it gives up (exit 1, the STOP stays).
- **Day mode, other cases:**
  - A stale STOP with no launcher: it asks before deleting it.
- **Stop mode:**
  - No launcher: "nothing to stop", and it writes nothing.
  - Otherwise it describes the state, warns, and asks for a reason (control characters removed, max 200 characters) and Y/N. An unknown state gets "a window may be running", never "nothing is lost". If a window started in the meantime, it asks again.
  - It writes `STOP <ts> by STOP-LAUNCHER.cmd: <reason>`, never over an existing STOP (one that appears at the same moment is left as it is), and waits up to 5 min.
- **Exit codes:** 0 = go on (day) or ended / nothing to stop (stop); 1 = nothing started / not stopped.
- **Test hooks** (refused without `-DryRunTag`): `-LaunchDir`, `-ReturnTime` (comma-separated tries), `-Answer` (one Y/N letter per question), `-Reason`, `-WaitMinutes`. With a tag it uses `<LaunchDir>\status-dryrun\<tag>\` and mutex `Local\Agent5RunNight-dry-<tag>`, the files of `run-day.ps1 -DryRun -DryRunTag <tag>`.

**Tests** (`test-day.ps1`; launchers only as `run-day.ps1 -DryRun` with the fake runner)

| test | what it checks |
|---|---|
| d-return-1..5 | 25:00, now+30 min and now+15 h refused; N starts nothing; now+80 min refused, then now+100 min accepted; Y writes return - 15 min and the power check is shown; hooks without `-DryRunTag` refused |
| d-stale-1/2 | an old STOP with no launcher: N keeps it; Y deletes it and goes on |
| d-none | stop mode with no launcher: "nothing to stop", no file |
| d-unknown-1/2 | a launcher whose state is unknown (its mutex held, no state.txt): RUN-DAY and STOP-LAUNCHER say a window may be running and ask; N writes nothing |
| d-real-1..4 | REAL `run-day.ps1` without `-StopAt` or with a bad one: exit 2; with `-StopAt`: "ends at / latest window start" = `-StopAt`, then refused on the hidden desktop (exit 2); REAL `run-night.ps1 -StopAt` is still refused as a test hook |
| d-cmd | a copy of RUN-DAY.cmd with test answers: the end time reaches `run-day.ps1 -StopAt` (it then refuses on the hidden desktop) |
| d-cmd-nul, d-stopcmd-none | the real RUN-DAY.cmd in day-draft refuses (it runs only from `bench\agent5\day\`); the real STOP-LAUNCHER.cmd with empty input and no launcher: nothing to stop. Nothing started, nothing written |
| d-between | a launcher waiting for a GO is stopped by RUN-DAY without a question; STOP consumed; exit 0 |
| d-stop-n/y | STOP-LAUNCHER: N writes nothing; Y stops the launcher with the reason in the STOP line |
| d-dl | `run-day.ps1 -StopAt now+12 min`: the 7-min GO is refused for the end time |
| d-window-0..3 | the GO is accepted under `-StopAt` and pins.txt lists run-day.ps1 + RUN-DAY.cmd; during the window RUN-DAY and STOP-LAUNCHER warn and ask (N: nothing happens); Y kills the runner and its child, and the launcher ends |
| real-files, leftovers | perf-notes GO/HOLD/STOP and `bench\agent5\launch` unchanged; no processes left |

The REAL cases (d-real, d-cmd) are skipped while a real launcher runs or on the user's own desktop (WinSta0\Default).

**Results:** test-day.ps1 -Name all at 23:11:52: 27/27 PASS on run-day.ps1 D86F6DE0 and launcher-ctl.ps1 6DDE3150 (`results\summary-all-231151.txt`), with 2 `-PlanOnly` calls (d-dl, d-window). Earlier runs: 22:51 24/25 (leftovers: a false positive, filter fixed), 22:54 25/25 (before the review fixes).

Not covered by a test: the battery refusal, the "too late" check before a stop, and the second question when a window starts while RUN-DAY is asking (timing).

**Review so far:** a read-only spec read by Agent 5's subagent (23:04) found no blockers. Fixed at 23:10: the unknown state now asks (in both modes); day mode reads the state again after the answer; the time check runs before anything is stopped; AC and the files are checked first; Ctrl+C instead of the X; a STOP written at the same moment is handled; `[0-9]` in launcher-ctl's time pattern; the exit-code line in RUN-DAY.cmd; the draft folder can't start a real day session; the test guard for the user's desktop. Open, for later: (a) the day launcher doesn't see the screensaver setting saved by a night launcher that was closed with the X, because it uses its own status folder. The user section points to the night README for that case. (b) run-day.ps1 line 68 keeps `\d`, so an odd `-StopAt` typed by hand can exit 3 instead of 2. That is harmless: RUN-DAY.cmd always passes a valid time. Agents 10 and 11 review next.

**Install, after review and after the windows (not tonight)**

1. Copy RUN-DAY.cmd, STOP-LAUNCHER.cmd, launcher-ctl.ps1, run-day.ps1 and README-DAY.md (make-run-day.ps1, run-day.diff and test-day.ps1 are optional) to `bench\agent5\day\`.
2. Compare the hashes.

`bench\agent5\day\` is three levels below the repo, like `bench\agent5\launch\`, so `$Repo` resolves the same way. The running night launcher doesn't look at new files there:

- it pins only run-night.ps1, RUN-NIGHT.cmd and the `bench\agent8\run` files;
- it reads only `perf-notes\WINDOW-GO/STOP/HOLD`;
- it writes only `bench\agent5\launch\status\`.

A later option is to allow `-StopAt` in run-night.ps1 itself (a one-line hook-list change) instead of the generated copy. That needs a new review of run-night.ps1.

# Agent 1: resume after the agy-grid relaunch (paused 17:07, 2026-11-22)

## State at the pause

- **W5 has not started.** There is no `perf-notes/WINDOW-HOLD.txt` and no `WINDOW-GO.txt`, and `build/agent8/matrix` has 20 folders (the newest timed run, `20261122-1541`, is W4b).
- **Nothing is running:** no build, game or functional run.
- **Agents** hold tasks #25-#35, file tools only (no commands until 'go'). They were told to finish their current edit, end their turns and wait for a resume.
- **The 17:10 'go' timer (task-627) was cancelled,** so nothing starts on its own.
- W5 is promoted and ready: `bench/agent8/RUN-WINDOW5-S3D.cmd` 5467F1BE…, `bench/agent8/run/matrix-window5-s3d.json` 4D7D689B…; inputs in `build/agent1/w5/W5-INPUTS-1642.txt`.

## After the relaunch, in order

1. **Hold manager.** Check for it with `Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object CommandLine -like '*hold-manager.ps1*'`.
   - If it isn't running, start `build/agent1/hold/hold-manager.ps1` as a daemon (it runs until 07:30).
   - Check `build/agent1/hold/hold-manager.log`.
2. **Watcher:** start `build/agent1/hold/hold-notify.ps1 -Want present` in the background.
3. **Cron:** every 30 min, MaxIterations ~28 (until 07:30), the same check prompt as before.
4. **Agents:** resume each one on its task, with the same window rule (file tools only until 'go'; no tool calls while the HOLD file exists).
   - A2 #28, A3 #29, A4 #25, A5 #27, A6 #31, A7 #30, A8 #26, A9 #33, A10 #34, A11 #35, A12 #32.
5. **W5:**
   - **If the user is present:** run a quiet check and re-hash the inputs (re-run `build/agent1/w5/hash-w5-inputs.ps1` and diff against `W5-INPUTS-1642.txt`). The user closes Task Manager (it runs elevated) and double-clicks `bench/agent8/RUN-WINDOW5-S3D.cmd`. Send 'go' after W5.
   - **Otherwise:** send 'go' now. Agent 2 builds S4b + S4c, and W5 moves to Agent 5's overnight launcher.
6. **Log the resume in `perf-notes/SESSION2.md`.**

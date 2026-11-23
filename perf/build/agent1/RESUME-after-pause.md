# Agent 1: restart after the 18:21 pause (W5 done 18:29, 2026-11-22)

## State at the pause

- **W5 is done:** `build/agent8/matrix/20261122-1756` (16/16 OK, summary.md 18:29:58). The headline and per-run environment notes are in `perf-notes/SESSION2.md`, entry 18:34. Agent 8's formal read-out hasn't run yet.
- **Nothing is running:** no build, game or functional run, and no HOLD or GO file. `build/agent8/matrix` has 21 folders.
  - The old HOLD manager (task-16) is stopped, the cron (task-58) is cancelled, and the W5 watcher (task-93) has finished.
- **Agents** hold run-2 tasks #1-#11, with no tool calls until 'go' (mapping in SESSION2 17:41):
  - A2 #1: S4b + S4c build. A3 #2: S4b functional queue, with Toy Pad rows 7/20/23 now in.
  - A4 #3: mc_smoke_check C3. A5 #4: overnight launcher. A6 #5: W4b logdiff. A7 #6: noise method.
  - A8 #7: W4b/W5 read-outs and W6 promotion. A9 #8: Android report.
  - A10 #9: compose-check rating and launcher safety read.
  - A11 #10: S4-DRAFT/FINDINGS decision 1, the 3-mode script, and the launcher review.
  - A12 #11: P2 counter script and W6 gates.
- **Decision 1 (Toy Pad tags) has been yes since 17:27.** S4-DRAFT §4a item 1 (L377) and FINDINGS-AND-CHANGES.md L127 still say "Until you answer: no"; Agent 11 fixes them after 'go'.

## On the user's "start", in order

1. **HOLD manager (fixed version).**
   - Check that none is running: `Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object CommandLine -like '*hold-manager.ps1*'`.
   - Then start `build/agent1/hold/hold-manager.ps1` as a daemon. `build/agent1/hold/hold-manager.log` should say `start: 21 matrix folders; HOLD file present: False`.
   - Its end time is `2026-11-23T07:30` (line 9). Change it if the restart is on a later day.
2. **Cron:** `*/30 * * * *`, MaxIterations = the half-hours left until 07:30, with this prompt (put in the new HOLD manager task id):
   > Agent 1 cron check: if perf-notes/WINDOW-HOLD.txt exists (a timed window is running), make no run_command calls and hold non-urgent replies; at most read the HOLD file. Otherwise: review board messages (.agy-grid/board.md); check build/agent1/hold/hold-manager.log and that the HOLD manager (task-NEW) is still running; look for stalls (agents idle with open tasks, errored agents, a build or functional run that stopped reporting); make sure no timed run can start after 06:45 and that every timed run ends before 07:30. Log to SESSION2.md only when something changed. If nothing needs action, end the turn without tools.
3. **Ask the user when they go to bed.** They have to double-click Agent 5's launcher before then.
4. **'go' to all agents** (`@@to all`), with these notes:
   - **All:** W5 ended at 18:29 and there is no HOLD file. Check `perf-notes/WINDOW-HOLD.txt` before every command, and make no tool calls while it exists.
   - **Agent 8:** run the W5 read-out on `20261122-1756`. Inputs: Defender was at ~0.9 core when W5 started. From SESSION2 18:34: power overlay best_efficiency, P clocks flat at ~1.93 GHz, the slow runs coincide with P saturation and low E clocks, and d11t/d11p use ~13 % less game CPU.
   - **Agent 7:** W5 is a noise case for the method (the P/E util and E-clock columns against the slow runs).
   - **Agent 2:** build S4b + S4c (C1 v3) at <= 2 threads, then hand the bins to Agent 3.
   - **Agent 5:** the launcher has to be built and reviewed (Agents 10 and 11) before the user's bedtime. Report the ETA.
   - **Agent 11:** the decision-1 records.
   - **Everyone else:** proceed on your run-2 task.
5. **Log the restart** in `perf-notes/SESSION2.md`.
6. **Overnight timing:**
   - W6 needs the S4b bins and Agent 3's functional queue: ~50 min build + ~139 min queue after 'go' (~3 h 10 min).
   - The launcher (`bench/agent5/launch/RUN-NIGHT.cmd`) isn't written yet. The user starts it with a double-click.
   - Every timed run starts by 06:45 and ends before 07:30.
7. **Then continue as planned:**
   - Agent 10 rates Agent 2's compose check.
   - Native re-pin once on native4b: Agent 4's REPIN.md dry run, then `-Go` only on my word.
   - Agent 8 promotes W6 from `build/agent5/w6-draft/`.
   - Agent 3 runs the Toy Pad rows.

# S5 delta rating: M16 PSO rows kit, final (helper pins + window guard + Stop-Ours)

M10, 2026-11-25 18:36. One-pass re-check against my rating E54D1890. Static only; nothing run.

| File | sha256/16 | Bytes |
|---|---|---|
| build/agent16/RUN-PSO-ROWS.cmd | 0B4436FC422EA024 | 2758 |
| build/agent16/psorows/rows-run.ps1 | E59F2C9BE1F28892 | 27966 |
| build/agent16/psorows/pso_post.py (unchanged) | 708AD389C8438177 | 59014 |

## Verdict

**SAFE-IF R1-R5 (unchanged from E54D1890), plus D1.** S1, S2, N1 and N2 are fixed. Stop-Ours cannot hit another agent's game, and the pin list is complete for the real-run and dryrun paths.

## What I checked

- **Pins (.cmd).**
  - 12 files are pinned by full sha256 via certutil. A missing file, a mismatch or a certutil failure (H = error text or NOHASH) raises PINFAIL, which means exit 3 before rows-run starts.
  - I re-hashed all 12 at 18:33 and every pin matches: rows-run E59F2C9B, pso_post 708AD389, verify-bins 80FF4C5F, run-game C2533FDF, guard 7A71E720, winhelper 37619E3D, nvml 9F6E6E3B, runstats AE6C8B0C, toml B763DABB, attract-long 4D35FAF4, vpadhost 5D929041, xinput1_4.dll 309DF316.
- **Pin list completeness.**
  - rows-run loads guard.ps1 and winhelper.cs and runs run-game, verify-bins and pso_post.
  - run-game loads guard.ps1, winhelper.cs, vpadhost.cs (InputScript), nvml.cs (GpuLog) and the toml, copies the vpad DLL, reads the route, and runs runstats.py.
  - analyze_profile.py runs only with -Profile, which the kit never passes.
  - verify-bins and runstats import only the stdlib.
  - The bins are pinned inside rows-run by MANIFEST sha. The .cmd itself is pinned by the waiter.
- **Stop-Ours (L295-310, finally at L355).**
  - Game kill: only `legodimensions.exe` whose ExecutablePath starts with `<resolved psorows\runs>\` (the trailing backslash blocks `runs2` and the like). A process's image path is the path it was launched from. run-game launches the hard link inside our run dir, so another agent's game shows its own runs path even when its exe shares the inode. Only a game launched from psorows\runs can match, i.e. one started by this kit.
  - run-game kill: only powershell children with ParentProcessId = $PID and `run-game.ps1` on the command line.
  - It acts only while `$armActive` is set (L334-336), and it stops the trigger job first.
  - The try/catch/finally wraps the whole arm loop, so an exception or Ctrl+C in the session closes our game.
  - Closing the console window is still not guaranteed (Windows gives the process about 5 s); that remains covered by R1/R3 and manual cleanup.
- **Window guard (L107-111).** It refuses on WINDOW-GO.txt, or on any process (other than itself) whose command line matches `window-s5.ps1|RUN-WINDOW-S5|run-matrix`, in addition to guard.ps1. This is checked at start and before every arm.
- **S1 fixed.** The run-dir regex accepts `(-\d+)?` at L232 and L337, still anchored, with the CreationTime filter.
- **S2 fixed.** verify-bins runs on the arm's cold copy before every arm (L326-327). That copy also backs the warm dir's links. A FAIL stops the session.
- **N1 fixed.** The warm dir is removed without -Force (L133, L272). A read-only file now raises an error and stops the session (fail-safe).
- **N2 fixed.** The trigger job counts only a game started at or after run-dir creation minus 5 s (L239).
- **No new kill or delete sites** other than Stop-Ours. The removals are the same own-dir set as before.

## Conditions

- R1-R5 as in E54D1890 (after the window and freeze on GO; dryrun ALL PASS first; interactive unlocked desktop; P-C1/P-C2; state.txt not stale `running`).
- **D1.** While the kit runs, no agent may run commands whose command line contains `run-matrix`, `window-s5.ps1` or `RUN-WINDOW-S5` (for example a grep or git grep for those names). The guard matches any process command line, so such a command makes the next arm refuse, and that stops the rest of the session. This is fail-safe but costs arms. guard.ps1 has the same pre-existing exposure.

## Findings

- **N1 (NIT).** The window-guard regex could be limited to powershell/cmd processes with `-File`/`/c` to avoid D1's false refusals. It is not needed for safety.
- **N2 (NIT).** If Stop-Ours runs after run-game has already been stopped by Ctrl+C, it still closes the game by path. With the console closed, it may not run at all; then close any legodimensions under psorows\runs by hand.

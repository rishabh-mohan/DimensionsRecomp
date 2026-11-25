# KILL-AUDIT: process kill/close sites of the functional-run harness

Paper audit only (E2.1 for M3, 2026-11-25). Files read, nothing executed, nothing edited except this file.

**VERDICT: SAFE-IF** (1) no `perf-notes\WINDOW-HOLD.txt` appears while a queue *matrix* row runs (or the holdwatch-m tree
guard below is applied), and (2) no other agent launches a `legodimensions.exe` out of `build\agent3\runs\` in the same
~2 s as a queue row (holdwatch.ps1 picks the first match).

- The normal close path (run-game.ps1, run-timing.ps1 via run-matrix.ps1) is **pid-exact**. It posts WM_CLOSE to the
  windows of the pid it started, then calls `Kill()` on the `Process` object it got from `Process.Start` / `Start-Process -PassThru`.
  That object holds an open handle, so the pid can't be reused.
- Minecraft: not mentioned anywhere (grep `Minecraft` over harness\, build\agent3\{s4a,s4b,toypad}\, bench\agent8\run\:
  0 hits). No `taskkill`, `wmic`, `os.kill`, `psutil`, `TerminateProcess(` or Python subprocess kill in the audited scripts.
  None of them kills by name only, and none kills "all python" or "all powershell".
- Only one site can in theory hit an unrelated process such as Minecraft: **holdwatch-m.ps1:36-41** (parent-pid tree walk,
  open to parent-pid reuse). It runs only on a HOLD during a matrix row. See risk R1.

## Scope read

| File | Lines | Process actions |
|---|---|---|
| harness\run-game.ps1 | 399 | launches game (`Process.Start`, l.233); WM_CLOSE/Kill own pid (l.302-304); name queries read-only (l.84, 268-271) |
| harness\guard.ps1 (dot-sourced l.90) | 17 | read-only Win32_Process query (runner detection) |
| harness\winhelper.cs (Add-Type l.96) | 228 | `CloseAll(pid)` l.171-175: PostMessage WM_CLOSE (0x0010) to visible top-level windows whose `GetWindowThreadProcessId == pid` (EnumWindows, own desktop only) |
| harness\vpad\vpadhost.cs, nvml.cs, runstats.py | - | no process control (grep) |
| build\agent3\s4b\s4b-queue.ps1 | 262 | launches run-game / run-matrix / attach / holdwatch(-m) / sidecar; kills only its own children |
| build\agent3\s4a\attach.ps1 (started by queue l.223) | 72 | finds game (name+path+start time), read-only sampling; starts sys-csv.ps1; no kill |
| build\agent3\s4b\holdwatch.ps1 | 44 | Stop-Process of the game it found (name+path+start time) |
| build\agent3\s4b\holdwatch-m.ps1 | 52 | Stop-Process of run-matrix pid, its PPID tree, legodimensions under -Root |
| build\agent3\s4b\postcheck.ps1 | 102 | runs python checks; only sets own priority (l.13); no kill |
| build\agent3\s4b\hostload.ps1 | 50 | read-only Get-Process / Win32_Processor; no kill |
| build\agent3\s4b\wait-event.ps1 | 73 | read-only Get-Process legodimensions (status line); no kill |
| build\agent3\toypad\toypad_sidecar.py (+ ldtag, toypad_client) | 319 | file tail + TCP to 127.0.0.1 listener; no subprocess/kill |
| bench\agent8\run\run-matrix.ps1 | 731 | calls run-timing.ps1 in-process (l.658); name queries read-only (l.402, 643-644); no kill itself |
| bench\agent8\run\run-timing.ps1 | 747 | launches game (`Start-Process -PassThru`, l.222), sys-csv (l.238), driver (l.370); closes/kills only those |
| bench\agent8\run\timing-env.ps1, common.ps1 (dot-sourced) | 95 / 235 | `Close-GameTimed` / `Close-Game` on a passed Process object; read-only queries |
| bench\agent8\run\winhelper.cs | - | same `CloseAll(pid)` (l.161) |
| bench\agent8\run\drivers\*.ps1, LdSys.cs | - | no kill (LdSys `Cleanup()` l.919 only closes its own handles) |

## Kill / close sites

| # | file:line | Mechanism | Target (how chosen) | Scope | Risk |
|---|---|---|---|---|---|
| 1 | harness\run-game.ps1:302 (winhelper.cs:171-175) | PostMessage WM_CLOSE | windows owned by `$gamePid` = `[Process]::Start($psi).Id` (l.233-234) | own game only | none |
| 2 | harness\run-game.ps1:302 | `$p.CloseMainWindow()` (fallback if 0 windows) | same `$p` | own game only | none |
| 3 | harness\run-game.ps1:304 | `$p.Kill()` after -CloseTimeoutSec | same `$p` (handle held) | own game only (no tree kill in .NET Fx) | none |
| 4 | build\agent3\s4b\s4b-queue.ps1:196 | `$hw.Kill()` | holdwatch-m powershell from `Start-Process -PassThru` (l.191) | own child | none |
| 5 | build\agent3\s4b\s4b-queue.ps1:241 | `Stop-Process -Id -Force` | `$tp`/`$side`/`$hw` pids from `Start-Process -PassThru` (l.218/223/226), only when run-game REFUSED | own children | none (sys-csv grandchild of attach can be orphaned; it ends on its own) |
| 6 | build\agent3\s4b\s4b-queue.ps1:246 | `$side.Kill()` | attach.ps1 powershell (l.223) | own child | none |
| 7 | build\agent3\s4b\s4b-queue.ps1:247 | `$hw.Kill()` | holdwatch.ps1 powershell (l.226) | own child | none |
| 8 | build\agent3\s4b\s4b-queue.ps1:250 | `$tp.Kill()` | toypad sidecar python (l.218) | own child (not "all python") | none |
| 9 | build\agent3\s4b\holdwatch.ps1:38 | `Stop-Process -Id $p.Id -Force` on HOLD | `Get-Process legodimensions` where `Path -like "<repo>\build\agent3\runs\*"` and `StartTime >= NotBefore-2s`, first match (l.25-26); handle held (l.30) | a legodimensions under build\agent3\runs started at/after the row's launch | **R2 low**: could pick another agent's concurrent game from the same runs root. Can't hit Minecraft (name filter). Fail-safe miss if the row uses `-Exe` other than legodimensions.exe or another `-RunsRoot` (then nothing is stopped) |
| 10 | build\agent3\s4b\holdwatch-m.ps1:37 | `Stop-Process -Id $MatrixPid -Force` on HOLD | pid passed by queue = `$mp.Id` of its own `Start-Process` (queue l.188-193; queue holds `$mp.Handle`, l.190, so no pid reuse) | own run-matrix powershell | none |
| 11 | build\agent3\s4b\holdwatch-m.ps1:36-41 | `Stop-Process -Id -Force` on every process in `Tree $MatrixPid` | Win32_Process snapshot, recursive walk on `ParentProcessId` (l.18-27); no creation-time check, no name allowlist; also runs when `$mp` is already gone (l.36 does not check `$mp`) | intended: run-matrix descendants (game, sys-csv, driver, conhost) | **R1 medium-low**: parent-pid reuse. A process whose original parent died *before* run-matrix started, and had the same pid number, has `ParentProcessId == $MatrixPid` and is killed together with its whole subtree. Example: Minecraft Launcher starts the game and then exits. This is the only theoretical way to hit Minecraft |
| 12 | build\agent3\s4b\holdwatch-m.ps1:44-45 | `Stop-Process -Id -Force` on HOLD | `Get-Process legodimensions` where `Path -like "<repo>\build\agent3\runs\<id>-<yyyyMMdd-HHmm>\*"` (the row's unique -OutDir) | games of this matrix row only | none (unique per-row dir) |
| 13 | bench\agent8\run\run-timing.ps1:437 | `$drv.Kill()` after -DriverTimeoutSec | driver from `Start-Process -PassThru` (l.370) | own child | none |
| 14 | bench\agent8\run\run-timing.ps1:466 -> timing-env.ps1:71,75 | `[LdHarness]::CloseAll($P.Id)` WM_CLOSE | `$p` = `Start-Process legodimensions.exe -PassThru` (l.222, handle l.226) | own game only | none |
| 15 | bench\agent8\run\run-timing.ps1:466 -> timing-env.ps1:81 | `$P.Kill()` after timeout | same `$p` | own game only | none |
| 16 | bench\agent8\run\run-timing.ps1:478 | `$drv.Kill()` (finally, error/Ctrl+C) | own driver | own child | none |
| 17 | bench\agent8\run\run-timing.ps1:481 | `Close-GameTimed $p`, else `$p.Kill()` (finally) | own game `$p` | own game only | none |
| 18 | bench\agent8\run\run-timing.ps1:499 | `$sysDrv.Kill()` 10 s after stop file | sys-csv powershell from `Start-Process -PassThru` (l.238) | own child | none |
| 19 | bench\agent8\run\common.ps1:181,183,187 | `Close-Game`: CloseAll + `$P.Kill()` | a passed Process object | not on the queue/matrix path (first-boot.ps1, recover-close.ps1) | none for this harness |

Read-only process queries (no kill, listed so nothing is missed): run-game.ps1:84 (refuses if a game runs), :268-271
(WerFault `-p <gamePid>` match); s4b-queue.ps1:82-99 (quiet gate, incl. `Win32_Process Name like 'python%'` read only), :157, :171;
guard.ps1:9; attach.ps1:26; hostload.ps1:26-30; wait-event.ps1:34; postcheck.ps1:13 (own priority); run-matrix.ps1:402, 643-644;
timing-env.ps1:30, 44; common.ps1:165-169.

Out of scope but noted: bench\agent8\run\recover-close.ps1:16 (manual tool) matches `legodimensions` with an exact
`Path -eq $exe`, which is safe.

## Recommended guards (not applied)

1. **R1, holdwatch-m.ps1 `Tree`**: walk only real descendants. Read `CreationDate` in the CIM query and accept a child
   only if `child.CreationDate >= parent.CreationDate` (the standard guard against parent-pid reuse). Also skip the tree
   walk when `$mp` is `$null`, or keep the `Process` object from the first poll and walk only while it is alive. Add a
   name allowlist for the kill (`powershell|pwsh|conhost|legodimensions|python|LdSys*`), and log and skip everything
   else. Safer alternative: hold the Process object of run-matrix and rely on sites 10 and 12 only (path-scoped), with
   no tree walk.
2. **R2, holdwatch.ps1**: narrow the match to this row's run dir. The queue knows `-Tag`: pass it, and require `Path -like
   "$root\*-$Tag*\*"`. Better still: have run-game.ps1 write `<run>\game.pid` right after l.234, and have holdwatch stop exactly
   that pid (and check that its `Path` lies under that run dir).
3. Optional: run-game.ps1:84 and s4b-queue/run-matrix only *wait or refuse* on name matches. That is acceptable. If
   rows ever use `-Exe rexlego*.exe`, add that name to holdwatch's search (today holdwatch would silently not enforce the
   HOLD for such a row).

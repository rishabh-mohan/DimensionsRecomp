@echo off
setlocal
rem Window 6, S4b upload path: Agent 5's task #4 draft (build\agent5\w6-draft), written by finalize-w6.ps1 for the bin
rem build\agent2\devoff4b-bin (finalized 2026-11-22 21:16 for build/agent2/devoff4b-bin), for Agent 8 to promote to bench\agent8\RUN-WINDOW6.cmd.
rem It starts nothing when bench\agent8\run\ lacks run-matrix.ps1 or matrix-window6.json, or when the S4b bin has no
rem MANIFEST.txt or legodimensions.exe.
rem Overnight, W6 starts from Agent 5's launcher (bench\agent5\launch\RUN-NIGHT.cmd) through a GO line. Do not use this
rem file while that launcher's window is open: this is the double-click fallback for a window without the launcher.
rem Window 6 (S4-DRAFT L346): double-click on the UNLOCKED desktop, then keep hands off for about 35 minutes.
rem Runs bench\agent8\run\matrix-window6.json with no prompts, arms -Only s0,p2,p2f,p2fc -Repeats 3 -ColdShared:
rem s0 = S4b with every switch OFF, p2 = #8 P2, p2f = #8 + #5 fix (i), p2fc = #8 + #5 + #4 C1 v3 keep-watch (verify
rem off). 1 unscored cold run (all arms share the bin), then 3 rounds rotated each round: s0, p2, p2f, p2fc x3 each
rem (13 runs). All uncapped, one frame source (perf.csv), every window >= 60 s after the first frame.
rem Before: screensaver (None), AC power plugged in, PC unlocked, no other programs. The runner keeps the display on
rem while it runs, logs the system state every second (sys.csv) and flags any run that was disturbed.
rem Results: build\agent8\matrix\<yyyyMMdd-HHmm>\summary.md and results.csv (newest folder).
rem The game turns the blocking timer wait on whenever REX_TIMER_WAIT_BLOCKING exists, whatever its value (Agent 11), so
rem any inherited copy is removed here; no W6 arm sets it. LEGO_GPU_WAIT_STATS is removed for the same reason.
set "REX_TIMER_WAIT_BLOCKING="
set "LEGO_GPU_WAIT_STATS="
if not exist "%~dp0run\run-matrix.ps1" goto draft
if not exist "%~dp0run\matrix-window6.json" goto draft
if not exist "%~dp0..\..\build\agent2\devoff4b-bin\MANIFEST.txt" goto nobin
if not exist "%~dp0..\..\build\agent2\devoff4b-bin\legodimensions.exe" goto nobin
echo Window 6 timing matrix (S4b upload path: s0, p2, p2f, p2fc): about 35 minutes. Do not touch the PC until this window says "Press any key".
echo Check first: screensaver (None), charger plugged in, no other programs open.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run\run-matrix.ps1" -Matrix "%~dp0run\matrix-window6.json" -Only s0,p2,p2f,p2fc -Repeats 3 -ColdShared -NoPrompt
echo.
echo Window 6 matrix finished (exit code %errorlevel%). Results: build\agent8\matrix\ (newest folder), summary.md
pause
exit /b
:draft
echo bench\agent8\run\ has no run-matrix.ps1 or matrix-window6.json. Nothing was started.
pause
exit /b 1
:nobin
echo build\agent2\devoff4b-bin has no MANIFEST.txt or legodimensions.exe (not staged). Nothing was started.
pause
exit /b 1

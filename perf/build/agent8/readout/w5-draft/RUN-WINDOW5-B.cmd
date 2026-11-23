@echo off
setlocal
rem DRAFT (Agent 8, 2026-11-22, task #10 standby work; not approved). Window 5, B line. It lives in
rem build\agent8\readout\w5-draft\ until window 4b is done, devoffB4 is staged and Agent 1 approves it. To use it: copy
rem this file to bench\agent8\ and matrix-window5-b.json to bench\agent8\run\. From any other folder it stops and starts
rem nothing, and it also stops while build\agent2\devoffB4-bin (a PLACEHOLDER name, Agent 2's #15) has no MANIFEST.txt.
rem Window 5 (S4-DRAFT L287): double-click on the UNLOCKED desktop, then keep hands off for about 40 minutes.
rem Runs bench\agent8\run\matrix-window5-b.json with no prompts, arms -Only base,s0,d11,d11t,d11p -Repeats 3 -ColdShared:
rem base = devoffB (codegen B), s0 = devoffB4 (S4a on the B line, every new switch OFF), d11 = s0 + the 8 timer cvars,
rem d11t = d11 + REX_TIMER_WAIT_BLOCKING=1, d11p = d11 + timer_queue_precise_wait=true. 1 unscored cold run (devoffB,
rem shared by both bins), then 3 rounds rotated each round: base, s0, d11, d11t, d11p x3 each (16 runs). All uncapped,
rem one frame source (perf.csv), every window >= 60 s after the first frame.
rem Before: screensaver (None), AC power plugged in, PC unlocked, no other programs. The runner keeps the display on
rem while it runs, logs the system state every second (sys.csv) and flags any run that was disturbed.
rem Results: build\agent8\matrix\<yyyyMMdd-HHmm>\summary.md and results.csv (newest folder).
rem The game turns the blocking timer wait on whenever REX_TIMER_WAIT_BLOCKING exists, whatever its value (Agent 11), so
rem any inherited copy is removed here; the runner sets it for the d11t runs only.
set "REX_TIMER_WAIT_BLOCKING="
if not exist "%~dp0run\run-matrix.ps1" goto draft
if not exist "%~dp0run\matrix-window5-b.json" goto draft
if not exist "%~dp0..\..\build\agent2\devoffB-bin\MANIFEST.txt" goto nobin
if not exist "%~dp0..\..\build\agent2\devoffB4-bin\MANIFEST.txt" goto nobin
echo Window 5 timing matrix (B line: S4 baseline + timer modes): about 40 minutes. Do not touch the PC until this window says "Press any key".
echo Check first: screensaver (None), charger plugged in, no other programs open.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run\run-matrix.ps1" -Matrix "%~dp0run\matrix-window5-b.json" -Only base,s0,d11,d11t,d11p -Repeats 3 -ColdShared -NoPrompt
echo.
echo Window 5 matrix finished (exit code %errorlevel%). Results: build\agent8\matrix\ (newest folder), summary.md
pause
exit /b
:draft
echo This is the window 5 DRAFT (B line). Nothing was started.
echo To use it: copy it to bench\agent8\ and matrix-window5-b.json to bench\agent8\run\ (after window 4b, once devoffB4 is staged, with Agent 1's go).
pause
exit /b 1
:nobin
echo build\agent2\devoffB-bin or build\agent2\devoffB4-bin has no MANIFEST.txt (devoffB4 not staged yet?). Nothing was started.
pause
exit /b 1

@echo off
setlocal
rem Window 4 (Agent 8, session 3): double-click on the UNLOCKED desktop, then keep hands off for about 40-45 minutes.
rem Runs bench\agent8\run\matrix-window4.json with no prompts, arms -Only d0,B,d3:
rem devoff2 (ref) vs devoffB (codegen B) first, then devoff3; 3 unscored cold runs (one per bin), then round-robin
rem rounds: d0 x5, B x5, d3 x4. All uncapped, one frame source (perf.csv), every window >= 60 s after the first frame.
rem Before: screensaver (None), AC power plugged in, PC unlocked, no other programs. The runner keeps the display on
rem while it runs, logs the system state every second (sys.csv) and flags any run that was disturbed.
rem Results: build\agent8\matrix\<yyyyMMdd-HHmm>\summary.md and results.csv (newest folder).
echo Window 4 timing matrix: about 40-45 minutes. Do not touch the PC until this window says "Press any key".
echo Check first: screensaver (None), charger plugged in, no other programs open.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run\run-matrix.ps1" -Matrix "%~dp0run\matrix-window4.json" -Only d0,B,d3 -NoPrompt
echo.
echo Window 4 matrix finished (exit code %errorlevel%). Results: build\agent8\matrix\ (newest folder), summary.md
pause

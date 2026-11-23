@echo off
setlocal
rem Window 4b (Agent 8, session 3): double-click on the UNLOCKED desktop, then keep hands off for about 40-45 minutes.
rem Runs bench\agent8\run\matrix-window4.json with no prompts, arms -Only d0,B,d3,d11t -Repeats 4 -ColdShared:
rem devoff2 (ref) vs devoffB (codegen B), devoff3, and d11t = window 3's d11 (Agent 11's ON bundle) plus
rem REX_TIMER_WAIT_BLOCKING=1 (Agent 11's timer change). 1 unscored cold run (devoff2, shared by all bins), then
rem 4 rounds in a Latin square: d0, B, d3, d11t x4 each (17 runs). All uncapped, one frame source (perf.csv),
rem every window >= 60 s after the first frame.
rem Before: screensaver (None), AC power plugged in, PC unlocked, no other programs. The runner keeps the display on
rem while it runs, logs the system state every second (sys.csv) and flags any run that was disturbed.
rem Results: build\agent8\matrix\<yyyyMMdd-HHmm>\summary.md and results.csv (newest folder).
echo Window 4b timing matrix (with the timer arm): about 40-45 minutes. Do not touch the PC until this window says "Press any key".
echo Check first: screensaver (None), charger plugged in, no other programs open.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run\run-matrix.ps1" -Matrix "%~dp0run\matrix-window4.json" -Only d0,B,d3,d11t -Repeats 4 -ColdShared -NoPrompt
echo.
echo Window 4b matrix finished (exit code %errorlevel%). Results: build\agent8\matrix\ (newest folder), summary.md
pause

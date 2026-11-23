@echo off
setlocal
rem Window 3 (Agent 8, 2026-11-21): double-click on the UNLOCKED desktop, then keep hands off for about 40 minutes.
rem Runs bench\agent8\run\matrix-window3.json with no prompts and no arguments, arms -Only d0,base,d11,n0:
rem devoff2 (ref), baseline, devoff2 + Agent 11 bundle, native2 N0 (d12 = Agent 12 bundle is in the json but dropped
rem to fit 45 min); 3 unscored cold runs (one per bin), then 4 round-robin runs per arm. All uncapped.
rem The runner keeps the display on while it runs and releases that at the end.
rem Results: build\agent8\matrix\<yyyyMMdd-HHmm>\summary.md and results.csv (newest folder).
echo Window 3 timing matrix: about 40 minutes. Do not touch the PC until this window says "Press any key".
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run\run-matrix.ps1" -Matrix "%~dp0run\matrix-window3.json" -Only d0,base,d11,n0 -NoPrompt
echo.
echo Window 3 matrix finished (exit code %errorlevel%). Results: build\agent8\matrix\ (newest folder), summary.md
pause

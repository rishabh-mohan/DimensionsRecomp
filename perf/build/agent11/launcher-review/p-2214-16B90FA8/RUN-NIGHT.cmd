@echo off
rem Overnight launcher (Agent 5). Double-click once on your own desktop, unlocked, on AC power, and leave the window open.
rem It waits for timing windows that the agents announce in perf-notes\WINDOW-GO.txt and ends at 07:30.
rem To stop it: create perf-notes\WINDOW-STOP.txt (any content). README.md next to this file explains everything.
setlocal
set "REX_TIMER_WAIT_BLOCKING="
set "LEGO_GPU_WAIT_STATS="
title Overnight launcher - leave open; to stop it create perf-notes\WINDOW-STOP.txt
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-night.ps1"
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" echo The launcher ended normally (07:30, STOP file).
if "%RC%"=="2" echo The launcher did not start: the reason is in red above. Nothing was changed.
if "%RC%"=="3" echo The launcher stopped on an error: see the red line above.
if not "%RC%"=="0" if not "%RC%"=="2" if not "%RC%"=="3" echo The launcher was interrupted (exit code %RC%, e.g. Ctrl+C). If a window was running, it was stopped. See the lines above.
echo Status and logs: %~dp0status\
echo You can close this window.
pause
endlocal & exit /b %RC%

@echo off
rem Day session (Agent 5). Double-click on your own desktop, unlocked, on AC power, when you leave for 90 min to 14 h.
rem It asks when you are back, then runs the same launcher as at night until 15 min before that time.
rem If the night launcher is still running, it is stopped first (if a timing window is running, you are asked first).
rem To stop the day session: STOP-LAUNCHER.cmd. README-DAY.md next to this file explains everything.
setlocal
set "REX_TIMER_WAIT_BLOCKING="
set "LEGO_GPU_WAIT_STATS="
title Day launcher - leave open; to stop it run STOP-LAUNCHER.cmd
set "DAYF=%TEMP%\agent5-day-stopat-%RANDOM%%RANDOM%.txt"
if exist "%DAYF%" del /q "%DAYF%"
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0launcher-ctl.ps1" -Mode day -OutFile "%DAYF%"
if errorlevel 1 goto nostart
if not exist "%DAYF%" goto nostart
set "STOPAT="
set /p STOPAT=<"%DAYF%"
del /q "%DAYF%" >nul 2>&1
if "%STOPAT%"=="" goto nostart
echo.
echo Starting the day launcher. It ends at %STOPAT%.
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-day.ps1" -StopAt "%STOPAT%"
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" echo The day launcher ended normally (end time %STOPAT% or STOP file).
if "%RC%"=="2" echo The day launcher did not start: the reason is in red above. Nothing was changed.
if "%RC%"=="3" echo The day launcher stopped on an error: see the red line above.
if not "%RC%"=="0" if not "%RC%"=="2" if not "%RC%"=="3" echo The day launcher was interrupted (e.g. Ctrl+C) or PowerShell failed (exit code %RC%). If a window was running, it was stopped. See the lines above.
echo Status and logs: %~dp0status\
echo You can close this window.
pause
endlocal & exit /b %RC%

:nostart
if exist "%DAYF%" del /q "%DAYF%" >nul 2>&1
echo.
echo Nothing was started.
pause
endlocal & exit /b 1

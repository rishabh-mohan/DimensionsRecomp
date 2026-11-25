@echo off
rem Stops Agent 5's launcher (the night one or a day session). It asks a reason, writes perf-notes\WINDOW-STOP.txt
rem and waits until the launcher has ended. If a timing window is running, it is killed and its numbers are lost.
rem README-DAY.md next to this file explains it.
setlocal
title Stop Agent 5's launcher
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0launcher-ctl.ps1" -Mode stop
set "RC=%ERRORLEVEL%"
echo.
pause
endlocal & exit /b %RC%

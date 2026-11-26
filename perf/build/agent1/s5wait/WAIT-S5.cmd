@echo off
rem WAIT-S5.cmd - S5 waiter: waits for build\agent1\s5wait\GO.txt and runs the hash-pinned .cmd jobs it lists.
rem Close this window, or create STOP.txt next to it, to end it. It ends by itself at 23:30.
title S5 waiter (LEGO perf) - leave open
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wait-s5.ps1" %*
echo [wait-s5] exit %ERRORLEVEL%
timeout /t 30 >nul 2>&1

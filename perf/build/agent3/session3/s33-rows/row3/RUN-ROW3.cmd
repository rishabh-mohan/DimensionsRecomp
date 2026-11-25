@echo off
rem RUN-ROW3.cmd - #33 row 3 (the user's visible-desktop review): OFF then ON, back to back, one approval (M3).
rem   RUN-ROW3.cmd            real run (needs the interactive desktop; ~2 x 8 min + 20 s; self-closing)
rem   RUN-ROW3.cmd dryrun     no game: command lines, run-game -DryRun, watcher replay, post self-test; exit 0 = pass
rem   extra words: noauto (no automatic game-window captures), onfirst (ON then OFF), allowhidden
setlocal
set "ROW3=%~dp0"
set "DRY="
for %%A in (%*) do if /i "%%~A"=="dryrun" set "DRY=1"
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROW3%row3-run.ps1" %*
set "RC=%ERRORLEVEL%"
echo [row3] exit %RC%
if not defined DRY timeout /t 15 >nul 2>&1
exit /b %RC%

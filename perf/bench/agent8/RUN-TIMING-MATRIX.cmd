@echo off
setlocal
rem Double-click to run the quiet-window timing matrix bench\agent8\run\matrix-base-vs-devoff1.json
rem (baseline-bin vs devoff1-bin; see bench\agent8\run\README.md, "Timing matrix"). No picker prompt.
rem Extra arguments are passed through, e.g.  RUN-TIMING-MATRIX.cmd -PlanOnly
rem Another matrix:  RUN-TIMING-MATRIX.cmd -Matrix run\matrix.json   (any -Matrix argument replaces the default)
set "RM_SCRIPT=%~dp0run\run-matrix.ps1"
set "RM_DEFAULT=%~dp0run\matrix-base-vs-devoff1.json"
echo(%*| findstr /i /c:"-matrix" >nul
if not errorlevel 1 goto withmatrix
powershell -NoProfile -ExecutionPolicy Bypass -File "%RM_SCRIPT%" -Matrix "%RM_DEFAULT%" %*
goto done
:withmatrix
powershell -NoProfile -ExecutionPolicy Bypass -File "%RM_SCRIPT%" %*
:done
pause

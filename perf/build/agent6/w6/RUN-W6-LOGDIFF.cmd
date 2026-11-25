@echo off
rem Agent 6, task #16: the W6 logdiff in one command. Read-only on the matrix folder.
rem   build\agent6\w6\RUN-W6-LOGDIFF.cmd build\agent8\matrix\<W6 folder> [more w6_kit.py options]
rem Writes build\agent6\w6\out-<folder>\ : w6-summary.txt (also printed), w6-data.json, logdiff\, extra.txt.
rem Exit 0 = no FAIL, 1 = at least one FAIL, 2 = usage error, 3 = perf-notes\WINDOW-HOLD.txt exists.
rem Options given after the folder override the defaults below (argparse keeps the last one), e.g.
rem   --expect build\agent6\w6\expect-w5.json   --out <dir>   --skip-logdiff   --top 50
setlocal
rem The repo root, taken before any shift: shift also moves %0, so %~dp0 would follow the last option (2026-11-25).
set "KITROOT=%~dp0..\..\.."
if "%~1"=="" (
  echo usage: %~nx0 ^<W6 matrix folder^> [w6_kit.py options]
  exit /b 2
)
set "MDIR=%~f1"
shift
set "REST="
:collect
if "%~1"=="" goto run
set REST=%REST% %1
shift
goto collect
:run
cd /d "%KITROOT%"
if exist "perf-notes\WINDOW-HOLD.txt" (
  echo perf-notes\WINDOW-HOLD.txt exists: a timed window is running. Not starting.
  exit /b 3
)
start "" /b /belownormal /wait python -B build\agent6\w6\w6_kit.py --expect build\agent6\w6\expect-w6.json --ref s0 "%MDIR%"%REST%
set RC=%ERRORLEVEL%
echo w6_kit exit %RC% (0 = no FAIL, 1 = at least one FAIL, 2 = usage error)
exit /b %RC%

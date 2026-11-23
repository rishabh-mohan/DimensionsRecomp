@echo off
rem Agent 6, task #19: the W9 logdiff in one command. Read-only on the matrix folder.
rem   build\agent6\wnight\RUN-W9-LOGDIFF.cmd build\agent8\matrix\<W9 folder> [more w6_kit.py options]
rem Rules: build\agent6\wnight\expect-w9.json, reference arm off. Arms come from the folder's matrix.json;
rem bench\agent8\run\matrix-window9.json is used only if the folder has none.
rem Writes build\agent6\wnight\out-W9-<folder>\ : w6-summary.txt (also printed), w6-data.json, logdiff\, extra.txt.
rem Exit 0 = no FAIL, 1 = at least one FAIL, 2 = usage error, 3 = perf-notes\WINDOW-HOLD.txt exists.
rem Options given after the folder override the defaults below (argparse keeps the last one), e.g.
rem   --out <dir>   --skip-logdiff   --top 50
setlocal
if "%~1"=="" (
  echo usage: %~nx0 ^<W9 matrix folder^> [w6_kit.py options]
  exit /b 2
)
set "MDIR=%~f1"
if "%MDIR:~-1%"=="\" set "MDIR=%MDIR:~0,-1%"
for %%I in ("%MDIR%") do set "MNAME=%%~nxI"
shift
set "REST="
:collect
if "%~1"=="" goto run
set REST=%REST% %1
shift
goto collect
:run
cd /d "%~dp0..\..\.."
if exist "perf-notes\WINDOW-HOLD.txt" (
  echo perf-notes\WINDOW-HOLD.txt exists: a timed window is running. Not starting.
  exit /b 3
)
start "" /b /belownormal /wait python -B build\agent6\w6\w6_kit.py --expect build\agent6\wnight\expect-w9.json --ref off --matrix-json bench\agent8\run\matrix-window9.json --out "build\agent6\wnight\out-W9-%MNAME%" "%MDIR%"%REST%
set RC=%ERRORLEVEL%
echo w6_kit exit %RC% (0 = no FAIL, 1 = at least one FAIL, 2 = usage error)
exit /b %RC%

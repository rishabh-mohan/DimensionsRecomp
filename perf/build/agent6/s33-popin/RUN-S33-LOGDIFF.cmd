@echo off
rem #33 pop-in (d3d12_pipeline_creation_no_wait): the logdiff in one command. Read-only on the run folders.
rem Written 2026-11-25 (E5.1 for M6), from build\agent6\wnight\RUN-W9-LOGDIFF.cmd.
rem Matrix mode (Agent 8 run-matrix.ps1 folder):
rem   build\agent6\s33-popin\RUN-S33-LOGDIFF.cmd build\agent8\matrix\<s33 folder> [more w6_kit.py options]
rem   Arms come from the folder's matrix.json, else build\agent6\s33-popin\matrix-s33-draft.json.
rem   Writes build\agent6\s33-popin\out-<folder>\ : w6-summary.txt (also printed), w6-data.json, logdiff\, extra.txt.
rem Harness mode (Agent 3 harness\run-game.ps1 run dirs; the first argument starts with --):
rem   build\agent6\s33-popin\RUN-S33-LOGDIFF.cmd --run offsf=<dir> --run onsf=<dir> [--ref offsf] [--out <dir>]
rem   Arms (bin, cvars, env) come from build\agent6\s33-popin\harness-s33.json. All arguments are passed through as
rem   typed (cmd would split ARM=DIR at the '='). Relative dirs are relative to the repo root. Default output
rem   build\agent6\s33-popin\out-harness\ (plus staging\ with copies of the game*.log and run.json files).
rem Rules: build\agent6\s33-popin\expect-s33.json, reference arm offsf.
rem Exit 0 = no FAIL, 1 = at least one FAIL, 2 = usage error, 3 = perf-notes\WINDOW-HOLD.txt exists.
rem Options given later override the defaults below (argparse keeps the last one), e.g.
rem   --ref basesf   --out <dir>   --matrix-json <file>   --skip-logdiff   --top 50
setlocal
rem The repo root, taken before any shift: shift also moves %0, so %~dp0 would follow the last option.
set "KITROOT=%~dp0..\..\.."
if "%~1"=="" (
  echo usage: %~nx0 ^<s33 matrix folder^> [w6_kit.py options]
  echo    or: %~nx0 --run ARM=DIR [--run ARM=DIR ...] [w6_kit.py options]
  exit /b 2
)
set "A1=%~1"
if "%A1:~0,2%"=="--" goto harness
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
cd /d "%KITROOT%"
if exist "perf-notes\WINDOW-HOLD.txt" (
  echo perf-notes\WINDOW-HOLD.txt exists: a timed window is running. Not starting.
  exit /b 3
)
start "" /b /belownormal /wait python -B build\agent6\w6\w6_kit.py --expect build\agent6\s33-popin\expect-s33.json --ref offsf --matrix-json build\agent6\s33-popin\matrix-s33-draft.json --out "build\agent6\s33-popin\out-%MNAME%" "%MDIR%"%REST%
set RC=%ERRORLEVEL%
goto done
:harness
cd /d "%KITROOT%"
if exist "perf-notes\WINDOW-HOLD.txt" (
  echo perf-notes\WINDOW-HOLD.txt exists: a timed window is running. Not starting.
  exit /b 3
)
start "" /b /belownormal /wait python -B build\agent6\w6\w6_kit.py --expect build\agent6\s33-popin\expect-s33.json --ref offsf --matrix-json build\agent6\s33-popin\harness-s33.json --out build\agent6\s33-popin\out-harness %*
set RC=%ERRORLEVEL%
:done
echo w6_kit exit %RC% (0 = no FAIL, 1 = at least one FAIL, 2 = usage error)
exit /b %RC%
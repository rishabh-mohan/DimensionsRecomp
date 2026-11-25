@echo off
rem RUN-SMOKE3D.cmd - SMOKE-FINAL2 first-3D smoke (M8): devfinal2-bin then nativefinal2-bin, plain default arm,
rem attract-long pad route, one approval. Modelled on M3's RUN-ROW3.cmd.
rem   RUN-SMOKE3D.cmd            real run (interactive desktop; ~2 x 4.5 min + 20 s + checks, about 10 min; self-closing)
rem   RUN-SMOKE3D.cmd dryrun     no game: verify-bins, command lines, run-game -DryRun, post self-test; exit 0 = pass
rem   extra words: allowhidden, nativefirst
setlocal
set "KIT=%~dp0"
set "DRY="
for %%A in (%*) do if /i "%%~A"=="dryrun" set "DRY=1"
powershell -NoProfile -ExecutionPolicy Bypass -File "%KIT%smoke3d-run.ps1" %*
set "RC=%ERRORLEVEL%"
echo [smoke3d] exit %RC%
if not defined DRY timeout /t 15 >nul 2>&1
exit /b %RC%

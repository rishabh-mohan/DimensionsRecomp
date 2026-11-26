@echo off
rem RUN-NATIVE4BP-SMOKE.cmd - S5 0.4c (M16): native4bp attract smoke, unattended, ~6 min (withref: ~12 min).
rem Words: dryrun | allowhidden | withref. Runs smoke4bp\smoke-run.ps1; writes only build\agent16\smoke4bp.
rem Refuses unless build\agent16\pack\native4bp-bin matches smoke4bp\PIN-native4bp.txt.
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0smoke4bp\smoke-run.ps1" %*
set RC=%ERRORLEVEL%
echo RUN-NATIVE4BP-SMOKE exit %RC%
endlocal & exit /b %RC%

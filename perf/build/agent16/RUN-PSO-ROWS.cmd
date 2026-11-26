@echo off
rem RUN-PSO-ROWS.cmd - S5 (M16): PSO functional rows (2.2/2.3, native4bp-pso-bin vs native4bp-bin) or the 2.4 A/B, unattended.
rem Words: rows (~55 min) | ab (~87 min) | ab n2 (~54 min); plus dryrun | allowhidden. Runs psorows\rows-run.ps1;
rem writes only build\agent16\psorows. Refuses unless both bins match their MANIFEST pins and pass verify-bins.
rem The waiter pins only this .cmd, so every script/helper it runs is pinned here by sha256 (M10-rated set); any
rem mismatch or missing file refuses with exit 3 before anything runs.
setlocal
cd /d "%~dp0"
set "WS=%~dp0..\.."
set PINFAIL=0
call :pin "%~dp0psorows\rows-run.ps1" E59F2C9BE1F288926717019EF75CE65CDD003F151B1C324D8470D8B5BDF6C919
call :pin "%~dp0psorows\pso_post.py" 708AD389C84381770641EE48656B6BAA4DBF70897A3497155302ED07A078386B
call :pin "%WS%\build\agent2\session3\verify-bins.py" 80FF4C5F581C4B1BC02C8E98039CBA6A62BEB4CE5F0E267885F9DA7F17C9B95E
call :pin "%WS%\harness\run-game.ps1" C2533FDFE9A3A4941F14A06C243C2A82875F5C2C93F1EBC95D68B48AB3DFA55F
call :pin "%WS%\harness\guard.ps1" 7A71E72057A0C87F8E7851DB3363B103F6713C520305AFB26E0492036A3E0759
call :pin "%WS%\harness\winhelper.cs" 37619E3DA38CE249ED4C219C606085992A33C36B7046F7BEB2AC204308C1C4B3
call :pin "%WS%\harness\nvml.cs" 9F6E6E3B5C7D89FA6D2E7B08CF122C313321F1A9C90EF8295A0FA0C7776552E8
call :pin "%WS%\harness\runstats.py" AE6C8B0C2A00B70A8427C203B3DD3EB1398F41E2D3EA753FBB3FCB6A039BF8D3
call :pin "%WS%\harness\legodimensions.toml" B763DABBE2C5FE7AFA300B3013EFDEE1FB9BF33E7A0A96738BEAC4BAF474FF54
call :pin "%WS%\harness\routes\attract-long.txt" 4D35FAF4BC263C9909B893C21091E4C459FC14AE92C8BA5133E0A198EF9BE4E2
call :pin "%WS%\harness\vpad\vpadhost.cs" 5D9290416F057B073064A1DCEB30115983E05684E79BD2D999C2F2A839B65457
call :pin "%WS%\build\agent3\vpad\xinput1_4.dll" 309DF316B576D2C39715D1C2B6803F34AB92F1FAFC84315D2B65483159AC7B3B
if not "%PINFAIL%"=="0" (
  echo RUN-PSO-ROWS REFUSED: %PINFAIL% pinned file^(s^) changed or missing - re-rate before running
  echo RUN-PSO-ROWS exit 3
  endlocal & exit /b 3
)
echo RUN-PSO-ROWS pins OK ^(12 files^)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0psorows\rows-run.ps1" %*
set RC=%ERRORLEVEL%
echo RUN-PSO-ROWS exit %RC%
endlocal & exit /b %RC%

:pin
rem %1 = file, %2 = expected sha256 (upper-case hex). certutil prints: header line, hash line, status line.
set "H="
if not exist "%~1" (
  echo PIN MISSING: %~1
  set /a PINFAIL+=1
  exit /b 1
)
for /f "skip=1 delims=" %%a in ('certutil -hashfile "%~1" SHA256 2^>nul') do if not defined H set "H=%%a"
if not defined H set "H=NOHASH"
set "H=%H: =%"
if /i "%H%"=="%~2" exit /b 0
echo PIN MISMATCH: %~1 sha256 %H% expected %~2
set /a PINFAIL+=1
exit /b 1

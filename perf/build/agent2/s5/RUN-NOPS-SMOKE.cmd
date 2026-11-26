@echo off
rem RUN-NOPS-SMOKE.cmd - S5 Phase 2.1 nops-async smoke (M2) on build\agent2\s5\devs5nops-bin, up to six arms, one approval:
rem   T1 default | T2 opt-in | N1 no_wait | N2 no_wait + opt-in   (timing; only the 10 s zpd log)
rem   A1 sync-log + slow_frame_log_ms=1 | A2 A1 + opt-in            (attribution only, D2)
rem   attract-long pad route, 240 s each, 20 s settle, then nops_smoke_post.py (gates + timing/attribution report).
rem   RUN-NOPS-SMOKE.cmd               real run (interactive desktop; 6 x ~4.5 min + 5 x 20 s, about 30 min; self-closing)
rem   RUN-NOPS-SMOKE.cmd dryrun        no game: verify-bins, command lines, run-game -DryRun, post self-test; exit 0 = pass
rem   RUN-NOPS-SMOKE.cmd pinsonly      only check the sha256 pins below; exit 0 = all match, 3 = changed or missing
rem   extra words: allowhidden, arms=T1,T2,... (order), allowsubset (arms= without N1+N2), nozpd
rem   S1: every arm adds d3d12_log_occlusion_queries=true (zpd-log diag) unless nozpd; post gives the S1 verdict
rem   N2: each arm starts from a fresh <run>\user (cold shader/pipeline storage); post gates it
rem   N3: a real run needs both N1 and N2 (unless allowsubset); T1 T2 N1 N2 take PrintWindow shots
rem       at 60 120 146 152 200 s into <run>\kit-shots (read-only job; post gates 5 ok shots per arm)
rem   Pins: the waiter pins only this .cmd, so it pins the ps1, the post script and every helper they run
rem   (sha256 via certutil, before anything else; any mismatch or missing file = exit 3; fail closed: the launch also
rem   needs PINOK == the pin count, so a pin line that is skipped or removed = exit 3). Written by mkpins.py.
setlocal
set "KIT=%~dp0"
for %%W in ("%KIT%..\..\..") do set "WS=%%~fW"
set "DRY="
set "PINSONLY="
for %%A in (%*) do (
    if /i "%%~A"=="dryrun" set "DRY=1"
    if /i "%%~A"=="pinsonly" set "PINSONLY=1"
)
set "BAD=0"
set "PINOK=0"
rem PINS-BEGIN (mkpins.py)
call :pin "build\agent2\s5\nops-smoke-run.ps1" 4885AE6DA29A26BDC5419749D82557B20357FB07F47C2918C58781BB9F933EB5
call :pin "build\agent2\s5\nops_smoke_post.py" 1B869FFC496516BDC36485F8FACFCE03BC6D37377A343182026E52082B82AC5F
call :pin "harness\run-game.ps1" C2533FDFE9A3A4941F14A06C243C2A82875F5C2C93F1EBC95D68B48AB3DFA55F
call :pin "harness\guard.ps1" 7A71E72057A0C87F8E7851DB3363B103F6713C520305AFB26E0492036A3E0759
call :pin "harness\winhelper.cs" 37619E3DA38CE249ED4C219C606085992A33C36B7046F7BEB2AC204308C1C4B3
call :pin "harness\nvml.cs" 9F6E6E3B5C7D89FA6D2E7B08CF122C313321F1A9C90EF8295A0FA0C7776552E8
call :pin "harness\runstats.py" AE6C8B0C2A00B70A8427C203B3DD3EB1398F41E2D3EA753FBB3FCB6A039BF8D3
call :pin "harness\vpad\vpadhost.cs" 5D9290416F057B073064A1DCEB30115983E05684E79BD2D999C2F2A839B65457
call :pin "harness\legodimensions.toml" B763DABBE2C5FE7AFA300B3013EFDEE1FB9BF33E7A0A96738BEAC4BAF474FF54
call :pin "harness\routes\attract-long.txt" 4D35FAF4BC263C9909B893C21091E4C459FC14AE92C8BA5133E0A198EF9BE4E2
call :pin "build\agent3\vpad\xinput1_4.dll" 309DF316B576D2C39715D1C2B6803F34AB92F1FAFC84315D2B65483159AC7B3B
call :pin "build\agent2\session3\verify-bins.py" 80FF4C5F581C4B1BC02C8E98039CBA6A62BEB4CE5F0E267885F9DA7F17C9B95E
call :pin "build\agent2\final\check-defaults.py" D9936C56C5E04B98263FF0384E10908A5AA63FAEB2D8F310448ABF9DB09B53A3
rem PINS-END
if not "%BAD%"=="0" (
    echo [nops-smoke] REFUSED: %BAD% pinned file^(s^) changed or missing ^(WS %WS%^)
    if not defined DRY if not defined PINSONLY timeout /t 15 >nul 2>&1
    exit /b 3
)
rem fail closed: every pin must have been checked and matched (M10 NIT, as natcmp)
if not "%PINOK%"=="13" (
    echo [nops-smoke] REFUSED: %PINOK% of 13 pins verified ^(WS %WS%^)
    if not defined DRY if not defined PINSONLY timeout /t 15 >nul 2>&1
    exit /b 3
)
echo [nops-smoke] pins OK: 13 files ^(WS %WS%^)
if defined PINSONLY exit /b 0
powershell -NoProfile -ExecutionPolicy Bypass -File "%KIT%nops-smoke-run.ps1" %*
set "RC=%ERRORLEVEL%"
echo [nops-smoke] exit %RC%
if not defined DRY timeout /t 15 >nul 2>&1
exit /b %RC%

:pin
set "H="
if exist "%WS%\%~1" for /f "skip=1 delims=" %%H in ('certutil -hashfile "%WS%\%~1" SHA256 2^>nul') do if not defined H set "H=%%H"
if not defined H set "H=MISSING"
set "H=%H: =%"
if /i not "%H%"=="%~2" (
    echo [nops-smoke] PIN MISMATCH %~1: got %H%, pinned %~2
    set /a BAD+=1
) else (
    set /a PINOK+=1
)
exit /b 0

@echo off
rem RUN-RT-SMOKE.cmd - S5 Phase 3 T2/F3 smoke (M2), three FUNCTIONAL arms (untimed, no perf verdicts; M10 P1/P2), one approval:
rem   T2   build\agent2\s5\devs5toml-bin, harness toml: one present_effect 'fsr' rejected line, no new ERROR vs devfinal2
rem   F3A  build\agent2\s5\natives5fsr1-bin, harness toml (present_effect fsr): spatial_fsr_presented=1 (P4)
rem   F3B  natives5fsr1-bin, -Toml native-fsr1\perf-bilinear.toml (pinned): spatial_fsr_presented=0 (P4)
rem   attract-long pad route, 240 s each, fresh run dir per arm, then rt_smoke_post.py (per-arm verdicts +
rem   FSR1-vs-bilinear side-by-side PNGs into rt-smoke\post\sbs-*). F3A F3B take PrintWindow shots at 60 120 146 200 s.
rem   RUN-RT-SMOKE.cmd               real run (interactive desktop; 3 x ~4.5 min, about 15 min; self-closing)
rem   RUN-RT-SMOKE.cmd dryrun        no game: verify-bins, command lines, run-game -DryRun, post self-test; exit 0 = pass
rem   RUN-RT-SMOKE.cmd pinsonly      only check the sha256 pins below; exit 0 = all match, 3 = changed or missing
rem   extra words: allowhidden, arms=T2,F3A,F3B (subset/order)
rem   P5: bin MANIFEST pins are checked by the ps1 (fail closed, before and after every arm), one kit at a time,
rem   interactive desktop only (unless allowhidden).
rem   Pins: the waiter pins only this .cmd, so it pins the ps1, the post script, perf-bilinear.toml and every helper
rem   they run (sha256 via certutil, before anything else; any mismatch or missing file = exit 3; fail closed: the
rem   launch also needs PINOK == the pin count, so a pin line that is skipped or removed = exit 3). Written by mkpins_rt.py.
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
rem PINS-BEGIN (mkpins_rt.py)
call :pin "build\agent2\s5\rt-smoke-run.ps1" 630D1F00644E659295946E4FDC633AA76D86403102510022BB789CA3C8B832EC
call :pin "build\agent2\s5\rt_smoke_post.py" 0419882CC71BAB844A753D0B8FABA1A5DE2B58C07B539C7BFEED1F3EC7939250
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
call :pin "build\agent2\s5\native-fsr1\perf-bilinear.toml" FA47B1E31787B24D04B59E15F26D8B2ADFFC456B38E7DE24A2B5F80F24375B16
rem PINS-END
if not "%BAD%"=="0" (
    echo [rt-smoke] REFUSED: %BAD% pinned file^(s^) changed or missing ^(WS %WS%^)
    if not defined DRY if not defined PINSONLY timeout /t 15 >nul 2>&1
    exit /b 3
)
rem fail closed: every pin must have been checked and matched (M10 NIT, as natcmp)
if not "%PINOK%"=="14" (
    echo [rt-smoke] REFUSED: %PINOK% of 14 pins verified ^(WS %WS%^)
    if not defined DRY if not defined PINSONLY timeout /t 15 >nul 2>&1
    exit /b 3
)
echo [rt-smoke] pins OK: 14 files ^(WS %WS%^)
if defined PINSONLY exit /b 0
powershell -NoProfile -ExecutionPolicy Bypass -File "%KIT%rt-smoke-run.ps1" %*
set "RC=%ERRORLEVEL%"
echo [rt-smoke] exit %RC%
if not defined DRY timeout /t 15 >nul 2>&1
exit /b %RC%

:pin
set "H="
if exist "%WS%\%~1" for /f "skip=1 delims=" %%H in ('certutil -hashfile "%WS%\%~1" SHA256 2^>nul') do if not defined H set "H=%%H"
if not defined H set "H=MISSING"
set "H=%H: =%"
if /i not "%H%"=="%~2" (
    echo [rt-smoke] PIN MISMATCH %~1: got %H%, pinned %~2
    set /a BAD+=1
) else (
    set /a PINOK+=1
)
exit /b 0

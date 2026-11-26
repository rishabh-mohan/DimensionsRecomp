@echo off
rem RUN-WINDOW-S5.cmd - S5 Phase 0.3 baseline window (M8): build\agent8\s5\run-matrix.ps1 on matrix-s5-baseline.json
rem (ship60, nat60, n4bp60 x4 at cap60 + natU x2, one unscored cold run per bin first = 17 runs; attract-long pad route,
rem 3D-only score; about 94 min, worst case with every cooldown timing out about 106 min). No prompts, self-closing.
rem Refuses (exit 3) when PINS-S5.txt or any file it lists is not the rated sha256, or on a precheck in window-s5.ps1
rem (bin pins, game running, hidden desktop, day launcher busy, WINDOW-HOLD.txt).
rem   RUN-WINDOW-S5.cmd           real run (interactive desktop)
rem   RUN-WINDOW-S5.cmd dryrun    no game: prechecks reported + run-matrix -PlanOnly; exit 0 = pass
setlocal
set "KIT=%~dp0"
set "PINS_SHA=BE96CED74291A7AB9A5FCBD8B6AE3C25770760511C46F97ED0F8628A0E1305ED"
set "DRY="
for %%A in (%*) do if /i "%%~A"=="dryrun" set "DRY=1"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$k=$env:KIT; $p=Join-Path $k 'PINS-S5.txt'; if (-not (Test-Path -LiteralPath $p)) { Write-Host '[window-s5] PINS-S5.txt missing'; exit 3 }; if ((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -ne $env:PINS_SHA) { Write-Host '[window-s5] PINS-S5.txt is not the rated sha256'; exit 3 }; $n=0; $bad=0; foreach ($l in @(Get-Content -LiteralPath $p)) { if ($l -match '^([0-9A-Fa-f]{64})\s+(\S.*)$') { $n++; $r=$Matches[2].Trim(); $w=$Matches[1].ToUpperInvariant(); $f=Join-Path $k $r; if (-not (Test-Path -LiteralPath $f -PathType Leaf)) { Write-Host ('[window-s5] PIN FAIL missing ' + $r); $bad++ } elseif ((Get-FileHash -LiteralPath $f -Algorithm SHA256).Hash -ne $w) { Write-Host ('[window-s5] PIN FAIL changed ' + $r); $bad++ } } }; if ($n -lt 17) { Write-Host ('[window-s5] PINS-S5.txt lists ' + $n + ' files, expected 17'); exit 3 }; if ($bad) { exit 3 }; Write-Host ('[window-s5] rated files ok: ' + $n + ' pins match')"
if errorlevel 1 goto refused
powershell -NoProfile -ExecutionPolicy Bypass -File "%KIT%window-s5.ps1" %*
set "RC=%ERRORLEVEL%"
goto done
:refused
echo [window-s5] refused: rated files do not match PINS-S5.txt (nothing started)
set "RC=3"
:done
echo [window-s5] exit %RC%
if not defined DRY timeout /t 15 >nul 2>&1
exit /b %RC%

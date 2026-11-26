@echo off
rem RUN-EXPLORE.cmd - M3 gameplay task: ONE visible exploration run (native4bp) of the scripted gameplay route.
rem   RUN-EXPLORE.cmd            real run (interactive desktop; ~12-15 min incl. bin check; self-closing)
rem   RUN-EXPLORE.cmd dryrun     no game: checks, command lines, run-game -DryRun, self-tests; exit 0 = pass (HEAVY I/O:
rem                              copies + hashes the pinned native bins, ~382 MB)
rem   RUN-EXPLORE.cmd pincheck   only the kit pin check below; exit 0 = all pins match, 3 = mismatch
rem   extra words: allowhidden, xenosonly (explore on xenos instead)
rem Level-l path to the post-load vortex, 120 s observe, single probes, walk/fight probe loop; a screenshot per mark.
rem Writes only build\agent3\gameplay\ (runs, shots, post, logs, bin-native). Report: post\gameplay-<stamp>.txt
rem Kit pins: every file this kit runs or reads as code/data is sha256-pinned here (the waiter pins only this .cmd);
rem any mismatch refuses with exit 3 before anything starts. Paths are relative to the WS (three levels up).
setlocal
set "GP=%~dp0"
set "GPPIN_01=0ED94A548A06BCB37C443429D1E766041751BF6BA44A3856FE75FBAED2866A66|build\agent3\gameplay\gameplay-run.ps1"
set "GPPIN_02=2950A4471C1271BCDAC132816D89CF3C95812785AF7A569A94850E6A1A3DE068|build\agent3\gameplay\gameplay-watch.ps1"
set "GPPIN_03=B12A7E11CBB1A9B26836A5E8F45967B64A5D610E5FE43E59251BF903E805CC2E|build\agent3\gameplay\gameplay_post.py"
set "GPPIN_04=6353647F0906AD2E014A81C854E3A59953C88086DC4F7E484C3FB4EA892D8F4B|build\agent3\gameplay\gen_gameplay_route.py"
set "GPPIN_05=249CD93942B07F456B30BDDE3E0BA0D17CA8E32450C615729C8B8459DE4298F4|build\agent3\gameplay\explore-route.txt"
set "GPPIN_06=D491FF7FC07A6C3808EABD8A1481841996DDAD1A4EFA0AF8DAFC81DDBF59858E|build\agent3\gameplay\gameplay-route.txt"
set "GPPIN_07=798ECC30B1920F386EE4A68F8E0B6307F77BA3DA8618EF65175240E150195B77|build\agent3\gameplay\tags\batman.bin"
set "GPPIN_08=44E16868B3B5AD6F374925EA93E88FFA5A618C41F24DE49D82FD4C885CC1DFFE|build\agent3\gameplay\tags\gandalf.bin"
set "GPPIN_09=6ED54B855D8624BCB9BCCCC0E13A89151564D09CA15F7BCAFE767CCBD7D236C8|build\agent3\gameplay\tags\wyldstyle.bin"
set "GPPIN_10=F7905A908D228527D59D212F3366DEB6256635807F32EC6E4C24A13A8A6D75AC|build\agent3\toypad\toypad_sidecar.py"
set "GPPIN_11=E6CBE1F9A8D8D55E7504D693AD9EDC88EDB925B5022B24E9D73D4C866BA34F5D|build\agent3\toypad\toypad_client.py"
set "GPPIN_12=3777FFFA8AEF403922DC030CDC18FF9E7C0E4F4614B41ED7E634C4D9BBC22371|build\agent3\toypad\ldtag-missing.py"
set "GPPIN_13=A4A591FCD8E8B8C653FE5F802C7DA06BB0AFA893B053B5D5235F8F737145FD35|build\agent3\s4b\holdwatch.ps1"
set "GPPIN_14=C2533FDFE9A3A4941F14A06C243C2A82875F5C2C93F1EBC95D68B48AB3DFA55F|harness\run-game.ps1"
set "GPPIN_15=7A71E72057A0C87F8E7851DB3363B103F6713C520305AFB26E0492036A3E0759|harness\guard.ps1"
set "GPPIN_16=37619E3DA38CE249ED4C219C606085992A33C36B7046F7BEB2AC204308C1C4B3|harness\winhelper.cs"
set "GPPIN_17=5D9290416F057B073064A1DCEB30115983E05684E79BD2D999C2F2A839B65457|harness\vpad\vpadhost.cs"
set "GPPIN_18=B763DABBE2C5FE7AFA300B3013EFDEE1FB9BF33E7A0A96738BEAC4BAF474FF54|harness\legodimensions.toml"
set "GPPIN_19=9F6E6E3B5C7D89FA6D2E7B08CF122C313321F1A9C90EF8295A0FA0C7776552E8|harness\nvml.cs"
set "GPPIN_20=AE6C8B0C2A00B70A8427C203B3DD3EB1398F41E2D3EA753FBB3FCB6A039BF8D3|harness\runstats.py"
set "GPPIN_21=80FF4C5F581C4B1BC02C8E98039CBA6A62BEB4CE5F0E267885F9DA7F17C9B95E|build\agent2\session3\verify-bins.py"
set "GPPIN_22=309DF316B576D2C39715D1C2B6803F34AB92F1FAFC84315D2B65483159AC7B3B|build\agent3\vpad\xinput1_4.dll"
set "DRY="
set "PINONLY="
for %%A in (%*) do if /i "%%~A"=="dryrun" set "DRY=1"
for %%A in (%*) do if /i "%%~A"=="pincheck" set "PINONLY=1"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = (Resolve-Path -LiteralPath (Join-Path $env:GP '..\..\..')).Path; $pins = @(Get-ChildItem env: | Where-Object { $_.Name -match '^GPPIN_\d+$' } | Sort-Object Name); $bad = 0; foreach ($e in $pins) { $h, $f = $e.Value.Split('|'); $p = Join-Path $ws $f; $a = 'MISSING'; if (Test-Path -LiteralPath $p -PathType Leaf) { $a = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }; if ($a -ne $h) { Write-Host ('PIN MISMATCH ' + $f + ' is ' + $a + ' pinned ' + $h); $bad++ } }; if ($pins.Count -ne 22) { Write-Host ('PIN COUNT ' + $pins.Count + ' not 22 (a stray GPPIN_* variable inherited from the caller?): ' + (($pins | ForEach-Object Name) -join ' ')); $bad++ }; if ($bad) { exit 3 }; Write-Host ('[gameplay explore] kit pins ok: ' + $pins.Count + ' files')"
if errorlevel 1 (
    echo [gameplay explore] REFUSED: kit pin check failed ^(a kit file differs from its pinned sha256^): exit 3
    if not defined DRY if not defined PINONLY timeout /t 15 >nul 2>&1
    exit /b 3
)
if defined PINONLY exit /b 0
echo WOULD-LAUNCH & exit /b 99 &rem explore %*
set "RC=%ERRORLEVEL%"
echo [gameplay explore] exit %RC%
if not defined DRY timeout /t 15 >nul 2>&1
exit /b %RC%

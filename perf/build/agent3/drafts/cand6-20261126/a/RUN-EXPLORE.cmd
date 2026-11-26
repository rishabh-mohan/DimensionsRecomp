@echo off
rem RUN-EXPLORE.cmd - M3 gameplay task: ONE visible exploration run (native4bp) of the scripted gameplay route.
rem   RUN-EXPLORE.cmd            real run (interactive desktop; ~17-27 min incl. bin check; self-closing)
rem   RUN-EXPLORE.cmd dryrun     no game: checks, command lines, run-game -DryRun, self-tests; exit 0 = pass (HEAVY I/O:
rem                              copies + hashes the pinned native bins, ~382 MB)
rem   RUN-EXPLORE.cmd pincheck   only the kit pin check below; exit 0 = all pins match, 3 = mismatch
rem   extra words: allowhidden, xenosonly (explore on xenos instead), zone (prompt sidecar --zone answers the
rem                zone step from the pad LEDs, first pad 3 command at T0 + 45 s; the v-replace then-mark is off;
rem                default off)
rem Front-end-marker-gated boot, New Game, the story's 3 figure prompts (answered by the prompt sidecar), then 120 s
rem observe, single probes, walk/fight probe loop; a screenshot per mark. -Seconds 1500 is a cap (the route stops itself).
rem Writes only build\agent3\gameplay\ (runs, shots, post, logs, bin-native). Report: post\gameplay-<stamp>.txt
rem Kit pins: every file this kit runs or reads as code/data is sha256-pinned here (the waiter pins only this .cmd);
rem any mismatch refuses with exit 3 before anything starts. Paths are relative to the WS (three levels up).
setlocal
set "GP=%~dp0"
set "GPPIN_01=DE16A2D29C0F040ABA32EE0FFF7BAE5293DBE59172CFC7F41F54174E2EB7AA77|build\agent3\gameplay\gameplay-run.ps1"
set "GPPIN_02=4BE7E90E16F08AAA5C7E069442DF8F602E79385FE287A5FA3FD4BD9521A1F776|build\agent3\gameplay\gameplay-watch.ps1"
set "GPPIN_03=E33DF65402DF053C0DBA5328632A14A0B6B90831EA0E51B1DD319C98501C8F50|build\agent3\gameplay\gameplay_post.py"
set "GPPIN_04=2C1977DE3652DF2496F57C9D4B10D0E73008871F8DF3B516D62DB52D59004D50|build\agent3\gameplay\gen_gameplay_route.py"
set "GPPIN_05=CB271440130C47ED8CBE8FAE804BD82F4B82EBA3C8C48C77D920AA563F91831F|build\agent3\gameplay\explore-route.txt"
set "GPPIN_06=705A3A504BF6B669ECD237243C6AC93227D57EE80243A0815502B6ED173B073D|build\agent3\gameplay\gameplay-route.txt"
set "GPPIN_07=798ECC30B1920F386EE4A68F8E0B6307F77BA3DA8618EF65175240E150195B77|build\agent3\gameplay\tags\batman.bin"
set "GPPIN_08=44E16868B3B5AD6F374925EA93E88FFA5A618C41F24DE49D82FD4C885CC1DFFE|build\agent3\gameplay\tags\gandalf.bin"
set "GPPIN_09=6ED54B855D8624BCB9BCCCC0E13A89151564D09CA15F7BCAFE767CCBD7D236C8|build\agent3\gameplay\tags\wyldstyle.bin"
set "GPPIN_10=F7905A908D228527D59D212F3366DEB6256635807F32EC6E4C24A13A8A6D75AC|build\agent3\toypad\toypad_sidecar.py"
set "GPPIN_11=E6CBE1F9A8D8D55E7504D693AD9EDC88EDB925B5022B24E9D73D4C866BA34F5D|build\agent3\toypad\toypad_client.py"
set "GPPIN_12=3777FFFA8AEF403922DC030CDC18FF9E7C0E4F4614B41ED7E634C4D9BBC22371|build\agent3\toypad\ldtag.py"
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
set "GPPIN_23=1D9A6EB54B3C300AF0FEB57E266AAD072B272C808CC6087FD47CA2F39A194A4B|build\agent3\gameplay\prompt_sidecar.py"
set "GPPIN_24=A48065480D3299B5C2AD60A3E1A814B9112F3606B413174370A824F1F13B9547|build\agent3\gameplay\selftest_prompt.py"
set "GPPIN_25=3446BA57E1CFD771203F158A13B17B7457A4FE4E70FE12041C5A526454C02D63|build\agent3\toypad\fake_listener.py"
set "DRY="
set "PINONLY="
for %%A in (%*) do if /i "%%~A"=="dryrun" set "DRY=1"
for %%A in (%*) do if /i "%%~A"=="pincheck" set "PINONLY=1"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = (Resolve-Path -LiteralPath (Join-Path $env:GP '..\..\..')).Path; $pins = @(Get-ChildItem env: | Where-Object { $_.Name -match '^GPPIN_\d+$' } | Sort-Object Name); $bad = 0; foreach ($e in $pins) { $h, $f = $e.Value.Split('|'); $p = Join-Path $ws $f; $a = 'MISSING'; if (Test-Path -LiteralPath $p -PathType Leaf) { $a = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }; if ($a -ne $h) { Write-Host ('PIN MISMATCH ' + $f + ' is ' + $a + ' pinned ' + $h); $bad++ } }; if ($pins.Count -ne 25) { Write-Host ('PIN COUNT ' + $pins.Count + ' not 25 (a stray GPPIN_* variable inherited from the caller?): ' + (($pins | ForEach-Object Name) -join ' ')); $bad++ }; if ($bad) { exit 3 }; Write-Host ('[gameplay explore] kit pins ok: ' + $pins.Count + ' files')"
if errorlevel 1 (
    echo [gameplay explore] REFUSED: kit pin check failed ^(a kit file differs from its pinned sha256^): exit 3
    if not defined DRY if not defined PINONLY timeout /t 15 >nul 2>&1
    exit /b 3
)
if defined PINONLY exit /b 0
powershell -NoProfile -ExecutionPolicy Bypass -File "%GP%gameplay-run.ps1" explore %*
set "RC=%ERRORLEVEL%"
echo [gameplay explore] exit %RC%
if not defined DRY timeout /t 15 >nul 2>&1
exit /b %RC%

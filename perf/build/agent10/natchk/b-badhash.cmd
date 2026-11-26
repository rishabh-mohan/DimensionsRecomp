@echo off
rem RUN-NATCMP.cmd - S5 (M16): clean back-to-back n4bp60 vs ship60 (default) or nat60 (CMP-DESIGN.md option B), unattended.
rem Words: (none) = short, 2 ABBA pairs + 2 primes, ~35 min | full = 4 pairs + 2 primes, ~60-65 min; vs ship|nat = base arm
rem (default ship60); plus dryrun | allowhidden.
rem Runs natcmp\cmp-run.ps1, which calls Agent 8's rated S5 runner once per arm; writes only build\agent16\natcmp.
rem The waiter pins only this .cmd, so every script/helper is pinned here by sha256; any mismatch or missing file
rem refuses with exit 3 before anything runs. The runner script itself (PINS-S5) is NOT pinned here: its file name must
rem not appear on a certutil command line (M10 D1, other kits' guards match it). cmp-run.ps1 (pinned below) pins it
rem in-process with Get-FileHash before every arm (= PINS-S5 8D647918...FC8B).
setlocal
cd /d "%~dp0"
set "WS=<workspace>"
set "S5=<workspace>\build\agent8\s5"
set PINFAIL=0
set PINOK=0
call :pin "<workspace>\build\agent16\natcmp\cmp-run.ps1" 41A3F7BC5ADD3BB0C13FCD71EF0933357A92D43AD4923E8404C4C2921A1D4A31
call :pin "<workspace>\build\agent16\natcmp\cmp_post.py" 52F53DB4DB3C4E119E7B2650FA34FFA5CC615E94F42F5CDAF613766D34D59E81
call :pin "<workspace>\build\agent16\natcmp\matrix-natcmp.json" D0EE98BBF003354C37BB2F0B6339292812C36790570BB6970AB80987DEC01056
call :pin "%S5%\run-timing.ps1" 72B8C69CF96CED7FD30C363521A4D901823158C3618378CC47E1F49218D8ED70
call :pin "%S5%\score3d.py" 0000000000000000B329AF18B53E1C0BAAEEE7C15AD13115EB2F3BD19C574A11
call :pin "%S5%\common.ps1" A8975D12C0BA2EECE2538B818791409FEBECD12EAC699DFF3E2F4B98311FE393
call :pin "%S5%\timing-env.ps1" 8090AE11747A371B547654C00CBCB558FB41318EB4D04BF6F1CD05352B2544FF
call :pin "%S5%\winhelper.cs" E5C2B44CFF23E399838537917D3029810F8E6635BE9FF2F73D8F5C508B42EA56
call :pin "%S5%\frame_summary.py" 987E0EC03456D5DCDA13AE1BC75D7CC693D06FD672DDE043E58F2286231DBC36
call :pin "%S5%\sys_summary.py" 6FCE3630B13134D5AE449B0B12E9FAE5934F8B0693D92A9B5A42910591249A8F
call :pin "%S5%\drivers\sys-csv.ps1" F3F06AB013F2423E2378857EE0014969A97D88E7AA40583F703B798BAD1A9CAB
call :pin "%S5%\drivers\LdSys.cs" 4EFD5C91B5DF3F68198D616B6F99D16EE9A541A4B7641D362AF6D5C0EFF07C37
call :pin "%S5%\drivers\thread-cpu.ps1" CFDC5D790CDD9AB0741B56CC77D3A382C9817A5ADD6EB82745F89E17A3061BCD
call :pin "%WS%\harness\routes\attract-long.txt" 4D35FAF4BC263C9909B893C21091E4C459FC14AE92C8BA5133E0A198EF9BE4E2
call :pin "%WS%\harness\nvml.cs" 9F6E6E3B5C7D89FA6D2E7B08CF122C313321F1A9C90EF8295A0FA0C7776552E8
call :pin "%WS%\build\agent3\vpad\xinput1_4.dll" 309DF316B576D2C39715D1C2B6803F34AB92F1FAFC84315D2B65483159AC7B3B
call :pin "%WS%\build\agent2\session3\verify-bins.py" 80FF4C5F581C4B1BC02C8E98039CBA6A62BEB4CE5F0E267885F9DA7F17C9B95E
call :pin "%WS%\harness\guard.ps1" 7A71E72057A0C87F8E7851DB3363B103F6713C520305AFB26E0492036A3E0759
call :pin "%WS%\harness\winhelper.cs" 37619E3DA38CE249ED4C219C606085992A33C36B7046F7BEB2AC204308C1C4B3
if not "%PINFAIL%"=="0" goto :refused
if not "%PINOK%"=="19" goto :refused
echo RUN-NATCMP pins OK ^(%PINOK%/19 files; the runner script is pinned inside cmp-run.ps1^)
echo WOULD-LAUNCH
set RC=%ERRORLEVEL%
echo RUN-NATCMP exit %RC%
endlocal & exit /b %RC%

:refused
echo RUN-NATCMP REFUSED: %PINFAIL% pinned file^(s^) changed or missing, %PINOK%/19 matched - re-rate before running
echo RUN-NATCMP exit 3
endlocal & exit /b 3

:pin
rem %1 = file, %2 = expected sha256 (upper-case hex). certutil prints: header line, hash line, status line.
rem Fail closed (M10 B1): PINOK counts matches and the launch needs PINOK==19 and PINFAIL==0. The file must be CRLF.
set "H="
if not exist "%~1" (
  echo PIN MISSING: %~1
  set /a PINFAIL+=1
  exit /b 1
)
for /f "skip=1 delims=" %%a in ('certutil -hashfile "%~1" SHA256 2^>nul') do if not defined H set "H=%%a"
if not defined H set "H=NOHASH"
set "H=%H: =%"
if /i "%H%"=="%~2" (
  set /a PINOK+=1
  exit /b 0
)
echo PIN MISMATCH: %~1 sha256 %H% expected %~2
set /a PINFAIL+=1
exit /b 1

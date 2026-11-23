# Agent 5: dry-run tests for bench\agent5\launch\run-night.ps1 (task #4).
# Only dry runs: every launcher here runs with -DryRun -DryRunTag t-<name>, so its GO/HOLD/STOP/status files are in
# bench\agent5\launch\status-dryrun\t-<name>\. The real perf-notes\WINDOW-GO/HOLD/STOP files are only looked at (before
# and after every test), never written. No build, no game. Group 'gate' runs a dummy "build process" (a copy of PING.EXE
# named ninja.exe, about 25-70 s). Group 'pin' edits RUN-NIGHT.cmd and a test matrix for a few seconds and puts them
# back byte for byte: run it alone, when no other launcher is running.
# Group 'hold' puts a "foreign" HOLD file into the test's own status-dryrun folder (never into perf-notes).
# Group 'run' uses -FakeRunner (fake-runner.ps1: prints ticks, can start one sleeping child powershell) instead of the
# runner, to test a normal end, STOP during a window, the end-time kill, a launcher error (-TestFailAfter) and Ctrl+C
# (t-run-ctrlc: that launcher runs in its own hidden console, and send-ctrlc.ps1 sends Ctrl+C to that console only);
# each checks that the fake runner and its child are gone. Group 'gate' test t-close runs
# copies of PING.EXE named ChatGPT.exe / Windows10Universal.exe / copilotapphost.exe from fake-procs\; t-build-start:
# a build process at the last check right before the window starts (fixture field builds_at_start).
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File run-tests.ps1 -Group go|gate|hold|pin|run [-Only t-good,t-badhash]
#        [-StopAt 'yyyy-MM-dd HH:mm']. -StopAt is for daytime runs: without it a launcher ends at the next 07:30, which
#        is more than 14 h away after 07:30, so every start is refused. Each launcher that does not set its own end time
#        gets this one (a dry-run hook; the latest window start is then the end time). Group 'run' t-run-ok expects 07:30.
param([ValidateSet('go', 'gate', 'hold', 'pin', 'run')][string]$Group = 'go', [string[]]$Only = @(), [string]$StopAt = '')
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$Here = $PSScriptRoot
$Repo = (Resolve-Path (Join-Path $Here '..\..\..')).Path
$Launcher = Join-Path $Repo 'bench\agent5\launch\run-night.ps1'
$NightCmd = Join-Path $Repo 'bench\agent5\launch\RUN-NIGHT.cmd'
$DryBase = Join-Path $Repo 'bench\agent5\launch\status-dryrun'
$RealFiles = @(foreach ($n in @('WINDOW-GO.txt', 'WINDOW-HOLD.txt', 'WINDOW-STOP.txt')) { Join-Path $Repo "perf-notes\$n" })
$RealHold = Join-Path $Repo 'perf-notes\WINDOW-HOLD.txt'
$RealStatusLog = Join-Path $Repo 'bench\agent5\launch\status\log.txt'
$PsExe = Join-Path $PSHOME 'powershell.exe'
$Out = Join-Path $Here 'results'; New-Item -ItemType Directory -Force -Path $Out | Out-Null
$W5 = Join-Path $Repo 'bench\agent8\run\matrix-window5-s3d.json'
$RunMatrix = Join-Path $Repo 'bench\agent8\run\run-matrix.ps1'
$Ninja = Join-Path $Here 'ninja.exe'
$Only = @($Only | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$Rows = New-Object System.Collections.Generic.List[object]

function Snap-Real { return ((@($RealFiles | ForEach-Object { if (Test-Path -LiteralPath $_) { "$(Split-Path -Leaf $_)=$((Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash.Substring(0, 12))@$((Get-Item -LiteralPath $_).LastWriteTimeUtc.Ticks)" } else { "$(Split-Path -Leaf $_)=absent" } })) -join ' ') }
function Stop-IfHold {
    if (Test-Path -LiteralPath $RealHold) {
        Write-Host "REAL HOLD PRESENT ($RealHold): the tests stop now" -ForegroundColor Red
        Get-Process -Name ninja -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $Ninja } | Stop-Process -Force
        exit 4
    }
}
function Sha([string]$P) { return (Get-FileHash -LiteralPath $P -Algorithm SHA256).Hash }
function Want([string]$Name) { return (-not $Only.Count -or $Only -contains $Name) }
function Q([string]$A) { if ($A -match '\s') { return '"' + $A + '"' }; return $A }
function Write-Json($Obj, [string]$Name) { [IO.File]::WriteAllText((Join-Path $Here $Name), ($Obj | ConvertTo-Json -Depth 30), (New-Object Text.UTF8Encoding $false)) }
function S($Cpu, $Builds = @(), [double]$Ram = 12, [double]$Disk = 50) { return [ordered]@{ cpu = $Cpu; builds = $Builds; ram_gb = $Ram; disk_gb = $Disk; logonui = $false; ac = $true } }
function Cpu([double]$M, [double]$O = 0.0, [double]$C = 0.01) { return [ordered]@{ MsMpEng = $M; OfficeClickToRun = $O; CrossDeviceService = $C } }

function Setup-Fixtures {
    Copy-Item -LiteralPath $W5 -Destination (Join-Path $Here 't-good.json') -Force
    Copy-Item -LiteralPath $W5 -Destination (Join-Path $Here 't-json.json') -Force
    $fb = Join-Path $Here 'fake-bin'; New-Item -ItemType Directory -Force -Path $fb | Out-Null
    [IO.File]::WriteAllText((Join-Path $fb 'MANIFEST.txt'), "fake bin for Agent 5's launcher tests: it is never run`r`n")
    if (-not (Test-Path -LiteralPath (Join-Path $fb 'legodimensions.exe'))) { [IO.File]::WriteAllBytes((Join-Path $fb 'legodimensions.exe'), [byte[]]@()) }
    $m = [IO.File]::ReadAllText($W5) | ConvertFrom-Json
    $m.arms[0].bin = 'build/agent5/launch-test/fake-bin'
    $m.arms[1].bin = 'build/agent2/../agent5/launch-test/fake-bin'
    $m.arms[2].bin = 'build/agent2/doesnotexist-bin'
    Write-Json $m 't-badbin.json'
    $m = [IO.File]::ReadAllText($W5) | ConvertFrom-Json
    $m.arms[0].env = [pscustomobject]@{ REX_TIMER_WAIT_BLOCKING = '1'; REX_OTHER_KEY = '1' }
    $m.arms[1].env = [pscustomobject]@{ rex_timer_wait_blocking = '1' }
    Write-Json $m 't-badenv.json'
    # Driver rule: arm 0 another runner file, arm 1 the {script, args} form, arm 2 a backslash, arm 3 a missing file,
    # arm 4 a real file in drivers\ that is not on the allowlist (sys-csv.ps1).
    $m = [IO.File]::ReadAllText($W5) | ConvertFrom-Json
    $m.arms[0] | Add-Member -Force -NotePropertyName driver -NotePropertyValue 'run-timing.ps1'
    $m.arms[1] | Add-Member -Force -NotePropertyName driver -NotePropertyValue ([pscustomobject]@{ script = 'drivers/thread-cpu.ps1'; args = @('-MaxSec', '5') })
    $m.arms[2] | Add-Member -Force -NotePropertyName driver -NotePropertyValue 'drivers\thread-cpu.ps1'
    $m.arms[3] | Add-Member -Force -NotePropertyName driver -NotePropertyValue 'drivers/nonexist.ps1'
    $m.arms[4] | Add-Member -Force -NotePropertyName driver -NotePropertyValue 'drivers/sys-csv.ps1'
    Write-Json $m 't-baddrv.json'
    $fp = Join-Path $Here 'fake-procs'; New-Item -ItemType Directory -Force -Path $fp | Out-Null
    foreach ($n in @('ChatGPT', 'Windows10Universal', 'copilotapphost')) { $d = Join-Path $fp "$n.exe"; if (-not (Test-Path -LiteralPath $d)) { Copy-Item -LiteralPath "$env:SystemRoot\System32\PING.EXE" -Destination $d } }
    Write-Json @{ samples = @((S (Cpu 0.02))) } 'gate-quiet.json'
    Write-Json @{ samples = @((S (Cpu 0.02))); builds_at_start = @('ninja:4242') } 'gate-build-start.json'
    Write-Json @{ samples = @((S (Cpu 0.02 0.35))) } 'gate-busy.json'
    # builds = real process list, but only exes under this test folder (the dummy ninja.exe), not other agents' builds
    Write-Json @{ samples = @([ordered]@{ cpu = (Cpu 0.02); builds = 'real'; builds_path = ('^' + [regex]::Escape($Here + '\')); ram_gb = 12; disk_gb = 50; logonui = $false; ac = $true }) } 'gate-build-real.json'
    Write-Json @{ samples = @((S (Cpu 0.95)), (S (Cpu 1.05)), (S (Cpu 0.98)), (S (Cpu 1.10)), (S (Cpu 1.02))) } 'gate-relaxed.json'
    Write-Json @{ samples = @(for ($i = 0; $i -lt 40; $i++) { S (Cpu $(if ($i % 2) { 1.15 } else { 0.70 })) }) } 'gate-unstable.json'
    Write-Json @{ samples = @((S (Cpu 1.25))) } 'gate-toohigh.json'
    Write-Json @{ samples = @((S (Cpu 0.02) @() 5.5 5.0)) } 'gate-lowres.json'
    Write-Json @{ samples = @((@(1..8) | ForEach-Object { S (Cpu 0.02 0.35) }) + @((S (Cpu 0.02)))) } 'gate-late.json'
    if (-not (Test-Path -LiteralPath $Ninja)) { Copy-Item -LiteralPath "$env:SystemRoot\System32\PING.EXE" -Destination $Ninja }
}

# Starts one launcher. Cleans its status-dryrun\<tag>\ first unless -Keep. -Go / -Stop write those files before the start.
function Start-L([string]$Tag, [string[]]$Extra = @(), [string]$Go = '', [switch]$Stop, [switch]$NoDry, [switch]$Keep, [string]$Suffix = '', [string]$Hold = '', [switch]$OwnConsole) {
    $dir = Join-Path $DryBase $Tag
    if (-not $Keep) { if (Test-Path -LiteralPath $dir) { Remove-Item -LiteralPath $dir -Recurse -Force }; New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    if ($Hold) { [IO.File]::WriteAllText((Join-Path $dir 'WINDOW-HOLD.txt'), $Hold + "`r`n") }
    if ($Go) { [IO.File]::WriteAllText((Join-Path $dir 'WINDOW-GO.txt'), $Go + "`r`n") }
    if ($Stop) { [IO.File]::WriteAllText((Join-Path $dir 'WINDOW-STOP.txt'), "test stop`r`n") }
    $al = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Q $Launcher))
    if (-not $NoDry) { $al += @('-DryRun', '-DryRunTag', $Tag) }
    $al += @($Extra | ForEach-Object { Q $_ })
    if ($StopAt -and -not $NoDry -and $Extra -notcontains '-StopAt') { $al += @('-StopAt', (Q $StopAt)) }   # -StopAt: see Usage
    $o = Join-Path $Out "$Tag$Suffix.console.txt"
    # -OwnConsole: the launcher gets a new hidden console (t-run-ctrlc sends Ctrl+C to it); else it shares this console.
    if ($OwnConsole) { $p = Start-Process -FilePath $PsExe -ArgumentList ($al -join ' ') -RedirectStandardOutput $o -RedirectStandardError "$o.err" -PassThru -WindowStyle Hidden }
    else { $p = Start-Process -FilePath $PsExe -ArgumentList ($al -join ' ') -RedirectStandardOutput $o -RedirectStandardError "$o.err" -PassThru -NoNewWindow }
    [void]$p.Handle
    return $p
}
function Put-File([string]$Tag, [string]$Name, [string]$Text) { $d = Join-Path $DryBase $Tag; New-Item -ItemType Directory -Force -Path $d | Out-Null; [IO.File]::WriteAllText((Join-Path $d $Name), $Text + "`r`n") }
function Wait-Log([string]$Tag, [string]$Rx, [double]$Sec) {
    $f = Join-Path (Join-Path $DryBase $Tag) 'log.txt'; $t = (Get-Date).AddSeconds($Sec)
    while ((Get-Date) -lt $t) { if ((Test-Path -LiteralPath $f) -and (Select-String -LiteralPath $f -Pattern $Rx -Quiet)) { return $true }; Start-Sleep -Milliseconds 300 }
    return $false
}
function Wait-Gone([string]$Path, [double]$Sec) { $t = (Get-Date).AddSeconds($Sec); while ((Get-Date) -lt $t) { if (-not (Test-Path -LiteralPath $Path)) { return $true }; Start-Sleep -Milliseconds 200 }; return $false }
function Wait-Exit($P, [double]$Sec) { if (-not $P.WaitForExit([int]($Sec * 1000))) { try { $P.Kill() } catch { }; return 'TIMEOUT' }; return [string]$P.ExitCode }
function Log-Text([string]$Tag) { $f = Join-Path (Join-Path $DryBase $Tag) 'log.txt'; if (Test-Path -LiteralPath $f) { return [IO.File]::ReadAllText($f) }; return '' }
function File-Text([string]$Tag, [string]$Name) { $f = Join-Path (Join-Path $DryBase $Tag) $Name; if (Test-Path -LiteralPath $f) { return [IO.File]::ReadAllText($f) }; return '' }
function Wait-File([string]$Path, [double]$Sec) { $t = (Get-Date).AddSeconds($Sec); while ((Get-Date) -lt $t) { if (Test-Path -LiteralPath $Path) { return $true }; Start-Sleep -Milliseconds 200 }; return $false }
function Line-Time([string]$Tag, [string]$Rx) {
    $l = @((Log-Text $Tag) -split "`r?`n" | Where-Object { $_ -match $Rx } | Select-Object -First 1)
    if (-not $l.Count) { return $null }
    if ($l[0] -match '^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)') { return [datetime]::ParseExact($Matches[1], 'yyyy-MM-dd HH:mm:ss', $null) }
    if ($l[0] -match '^(\d\d:\d\d:\d\d) quiet gate') { return (Get-Date).Date.Add([timespan]::Parse($Matches[1])) }
    return $null
}
function Check([string]$Name, [string]$Tag, [string]$Code, [string]$WantCode, [string[]]$Has = @(), [string[]]$HasNot = @(), [string[]]$Absent = @(), [string[]]$Present = @(), [string]$Before = '', [string[]]$Extra = @(), [string]$Suffix = '') {
    $dir = Join-Path $DryBase $Tag
    $txt = Log-Text $Tag
    $con = Join-Path $Out "$Tag$Suffix.console.txt"; $ctxt = if (Test-Path -LiteralPath $con) { [IO.File]::ReadAllText($con) } else { '' }
    $fail = New-Object System.Collections.Generic.List[string]
    if ($WantCode -and $Code -ne $WantCode) { $fail.Add("exit $Code, want $WantCode") }
    foreach ($h in $Has) { if ($txt -notmatch $h -and $ctxt -notmatch $h) { $fail.Add("missing /$h/") } }
    foreach ($h in $HasNot) { if ($txt -match $h -or $ctxt -match $h) { $fail.Add("unexpected /$h/") } }
    foreach ($f in $Absent) { if (Test-Path -LiteralPath (Join-Path $dir $f)) { $fail.Add("$f is still there") } }
    foreach ($f in $Present) { if (-not (Test-Path -LiteralPath (Join-Path $dir $f))) { $fail.Add("$f is missing") } }
    if ($Before) { $after = Snap-Real; if ($after -ne $Before) { $fail.Add("REAL perf-notes files changed: before [$Before] after [$after]") } }
    foreach ($e in $Extra) { if ($e) { $fail.Add($e) } }
    $ok = ($fail.Count -eq 0)
    $Rows.Add([pscustomobject]@{ test = $Name; tag = $Tag; result = $(if ($ok) { 'PASS' } else { 'FAIL' }); exit = $Code; detail = $(if ($ok) { 'ok' } else { $fail -join ' | ' }) })
    Write-Host ('{0,-5} {1,-18} exit {2,-8} {3}' -f $(if ($ok) { 'PASS' } else { 'FAIL' }), $Name, $Code, $(if ($ok) { '' } else { $fail -join ' | ' })) -ForegroundColor $(if ($ok) { 'Green' } else { 'Red' })
}

Stop-IfHold
Setup-Fixtures
$Fx = { param($n) Join-Path $Here $n }
$Fast0 = @('-SkipStartChecks', '-MatrixDir', 'build\agent5\launch-test', '-PollSeconds', '1')
$Fast = $Fast0 + @('-SampleSeconds', '1')
$shaGood = Sha (Join-Path $Here 't-good.json')
$GoGood = "GO T1 t-good.json $shaGood only=base,s0 repeats=1"
Write-Host "group $Group; t-good.json sha256 $shaGood; real perf-notes files: $(Snap-Real)"

if ($Group -eq 'go') {
    if (Want 't-good') {
        Stop-IfHold; $b = Snap-Real
        $env:REX_TIMER_WAIT_BLOCKING = '1'; $env:REX_TEST_LEFTOVER = 'x'
        try { $p = Start-L 't-good' ($Fast + @('-MaxGo', '1', '-GateFixture', (& $Fx 'gate-quiet.json'))) -Go $GoGood } finally { Remove-Item Env:\REX_TIMER_WAIT_BLOCKING, Env:\REX_TEST_LEFTOVER -ErrorAction SilentlyContinue }
        $c = Wait-Exit $p 300
        Check 'good GO' 't-good' $c '0' -Before $b -Has @("removed REX_TIMER_WAIT_BLOCKING='1'", [regex]::Escape('passed on to the runner as they are): ') + ".*REX_TEST_LEFTOVER='x'", 'power AC.*\(ACLineStatus \d+, BatteryFlag \d+, battery ', 'GO read and deleted', 'GO ACCEPTED: window T1', 'HOLD written', 'bin build/agent2/[A-Za-z0-9_.-]+-bin/legodimensions\.exe sha256 [0-9A-F]{64}', 'bin build/agent2/[A-Za-z0-9_.-]+-bin/MANIFEST\.txt sha256 [0-9A-F]{64}', 'quiet gate: STRICT \(MsMpEng', 'bins unchanged since the GO', 'power scheme at the start: ', 'DRY RUN, would start window T1', [regex]::Escape('-NoProfile -NonInteractive -ExecutionPolicy Bypass -File '), [regex]::Escape('bench\agent8\run\run-matrix.ps1 -Matrix '), [regex]::Escape('launch-test\t-good.json -Only base,s0 -Repeats 1 -ColdShared -NoPrompt'), 'HOLD removed', '-MaxGo 1 reached', 'screensaver: would set', 'keep-awake: would request') -Absent @('WINDOW-GO.txt', 'WINDOW-HOLD.txt') -Present @('last-result.txt', 'gate.txt', 'pins.txt')
    }
    if (Want 't-badhash') {
        Stop-IfHold; $b = Snap-Real
        $p = Start-L 't-badhash' ($Fast + @('-MaxGo', '1', '-GateFixture', (& $Fx 'gate-quiet.json'))) -Go "GO T2 t-good.json $('0' * 64) only=base,s0 repeats=1"
        $c = Wait-Exit $p 240
        Check 'bad hash' 't-badhash' $c '0' -Before $b -Has @('GO REFUSED: sha256 mismatch') -HasNot @('GO ACCEPTED', 'HOLD written', 'would start') -Absent @('WINDOW-GO.txt', 'WINDOW-HOLD.txt')
    }
    if (Want 't-badbin') {
        Stop-IfHold; $b = Snap-Real
        $p = Start-L 't-badbin' ($Fast + @('-MaxGo', '1', '-GateFixture', (& $Fx 'gate-quiet.json'))) -Go "GO T3 t-badbin.json $(Sha (& $Fx 't-badbin.json')) only=d11t repeats=1"
        $c = Wait-Exit $p 240
        Check 'bin outside agent2' 't-badbin' $c '0' -Before $b -Has @("arm 'base': bin 'build/agent5/launch-test/fake-bin' is not build/agent2/<name>-bin", [regex]::Escape("arm 's0': bin 'build/agent2/../agent5/launch-test/fake-bin' is not build/agent2/<name>-bin"), "arm 'd11': build/agent2/doesnotexist-bin has no MANIFEST.txt") -HasNot @('GO ACCEPTED', 'HOLD written', 'would start') -Absent @('WINDOW-GO.txt')
    }
    if (Want 't-badenv') {
        Stop-IfHold; $b = Snap-Real
        $p = Start-L 't-badenv' ($Fast + @('-MaxGo', '1', '-GateFixture', (& $Fx 'gate-quiet.json'))) -Go "GO T4 t-badenv.json $(Sha (& $Fx 't-badenv.json')) only=d11t repeats=1"
        $c = Wait-Exit $p 240
        Check 'disallowed env key' 't-badenv' $c '0' -Before $b -Has @("(?-i)arm 'base': env key 'REX_OTHER_KEY' is not allowed", "(?-i)arm 's0': env key 'rex_timer_wait_blocking' is not allowed") -HasNot @('GO ACCEPTED', 'HOLD written', 'would start', "(?-i)env key 'REX_TIMER_WAIT_BLOCKING' is not allowed") -Absent @('WINDOW-GO.txt')
    }
    if (Want 't-driver') {
        Stop-IfHold; $b = Snap-Real
        $p = Start-L 't-driver' ($Fast + @('-MaxGo', '1', '-GateFixture', (& $Fx 'gate-quiet.json'))) -Go "GO T8 t-baddrv.json $(Sha (& $Fx 't-baddrv.json')) only=base repeats=1"
        $c = Wait-Exit $p 240
        $dm = [regex]::Escape(': driver must be drivers/thread-cpu.ps1 or drivers/pso-stats-at-end.ps1 or drivers/io-counters.ps1 as a plain string (no args, no {script, args}), a file in bench\agent8\run\drivers (it is ')
        Check 'driver rule x5' 't-driver' $c '0' -Before $b -Has @("arm 'base'$dm'run-timing\.ps1'\)", ("arm 's0'$dm'" + [regex]::Escape('{"script":"drivers/thread-cpu.ps1","args":["-MaxSec","5"]}') + "'\)"), "arm 'd11'$dm'drivers\\thread-cpu\.ps1'\)", "arm 'd11t'$dm'drivers/nonexist\.ps1'\)", "arm 'd11p'$dm'drivers/sys-csv\.ps1'\)") -HasNot @('GO ACCEPTED', 'HOLD written', 'would start') -Absent @('WINDOW-GO.txt')
    }
    if (Want 't-unknownarg') {
        Stop-IfHold; $b = Snap-Real
        $p = Start-L 't-unknownarg' @('-Bogus')
        $c = Wait-Exit $p 120
        Check 'unknown argument' 't-unknownarg' $c '2' -Before $b -Has @("refused: unknown argument\(s\) '-Bogus'") -Absent @('log.txt', 'state.txt')
    }
    if (Want 't-14h') {
        Stop-IfHold; $b = Snap-Real
        $p = Start-L 't-14h' ($Fast + @('-StopAt', (Get-Date).AddHours(15).ToString('yyyy-MM-dd HH:mm')))
        $c = Wait-Exit $p 120
        Check 'refuse: end > 14 h away' 't-14h' $c '2' -Before $b -Has @('START REFUSED: .*more than 14 h from now \(it is past 07:30\): start it in the evening') -HasNot @('screensaver', 'keep-awake', 'waiting for')
    }
    if (Want 't-latest-go') {
        Stop-IfHold; $b = Snap-Real
        $p = Start-L 't-latest-go' ($Fast + @('-MaxGo', '1', '-StartBy', (Get-Date).AddMinutes(-1).ToString('yyyy-MM-dd HH:mm'), '-GateFixture', (& $Fx 'gate-quiet.json'))) -Go $GoGood
        $c = Wait-Exit $p 240
        Check 'latest start at GO' 't-latest-go' $c '0' -Before $b -Has @('!!! the latest window start .* has passed: every GO is refused', 'GO REFUSED: latest start: the GO was read at .*, at or after the latest window start') -HasNot @('GO ACCEPTED', 'HOLD written', 'would start') -Absent @('WINDOW-GO.txt', 'WINDOW-HOLD.txt')
    }
    if (Want 't-badgo') {
        Stop-IfHold; $b = Snap-Real
        $p = Start-L 't-badgo' ($Fast + @('-MaxGo', '7', '-GateFixture', (& $Fx 'gate-quiet.json')))
        $lines = @("go T5 t-good.json $shaGood only=base repeats=1", "GO T5 t-good.json $shaGood only=base", "GO T5 t-good.json $shaGood only=base repeats=0",
                   "GO T5 t-good.json $shaGood only=base;s0 repeats=1", "GO T5 ..\t-good.json $shaGood only=base repeats=1",
                   "GO T5 t-good.json $shaGood only=base repeats=1`r`nGO T6 t-good.json $shaGood only=s0 repeats=1", "GO T5 t-good.json $shaGood only=zzz repeats=1")
        $gf = Join-Path (Join-Path $DryBase 't-badgo') 'WINDOW-GO.txt'; $notGone = 0
        foreach ($l in $lines) { Put-File 't-badgo' 'WINDOW-GO.txt' $l; if (-not (Wait-Gone $gf 120)) { $notGone++ } }
        $c = Wait-Exit $p 240
        $n = ([regex]::Matches((Log-Text 't-badgo'), 'GO REFUSED')).Count
        Check 'malformed GO x7' 't-badgo' $c '0' -Before $b -Has @("first token must be GO, not 'go'", 'GO line must have 6 tokens, it has 5', "must be repeats=<1-20>", "must be only=<arm>", 'must be a plain .json file name', 'GO file must hold exactly one line, it has 2', "only=: no arm 'zzz'") -HasNot @('GO ACCEPTED', 'HOLD written') -Extra @($(if ($n -ne 7) { "$n GO REFUSED lines, want 7" }), $(if ($notGone) { "$notGone GO files not consumed" }))
    }
    if (Want 't-startref') {
        Stop-IfHold; $b = Snap-Real
        $p = Start-L 't-startref' @('-MaxGo', '1')
        $c = Wait-Exit $p 120
        Check 'refuse: not WinSta0\Default' 't-startref' $c '2' -Before $b -Has @('START REFUSED: this is desktop ', 'not the user''s own desktop WinSta0\\Default') -HasNot @('screensaver', 'keep-awake', 'waiting for')
    }
    if (Want 't-hooks') {
        Stop-IfHold; $b = Snap-Real
        $sb = if (Test-Path -LiteralPath $RealStatusLog) { Sha $RealStatusLog } else { 'absent' }
        $p = Start-L 't-hooks' @('-MaxGo', '1', '-PollSeconds', '1') -NoDry
        $c = Wait-Exit $p 120
        $sa = if (Test-Path -LiteralPath $RealStatusLog) { Sha $RealStatusLog } else { 'absent' }
        Check 'hooks need -DryRun' 't-hooks' $c '2' -Before $b -Has @('-MaxGo -PollSeconds only work together with -DryRun') -Extra @($(if ($sa -ne $sb) { 'the real status\log.txt changed' }))
    }
    if (Want 't-mutex') {
        Stop-IfHold; $b = Snap-Real
        $p1 = Start-L 't-mutex' ($Fast + @('-GateFixture', (& $Fx 'gate-quiet.json')))
        $w = Wait-Log 't-mutex' 'waiting for ' 180
        $p2 = Start-L 't-mutex' ($Fast + @('-GateFixture', (& $Fx 'gate-quiet.json'))) -Keep -Suffix '-second'
        $c2 = Wait-Exit $p2 120
        $st = [IO.File]::ReadAllText((Join-Path (Join-Path $DryBase 't-mutex') 'state.txt'))
        Put-File 't-mutex' 'WINDOW-STOP.txt' 'test stop'
        $c1 = Wait-Exit $p1 120
        Check 'second launcher refused' 't-mutex' $c2 '2' -Before $b -Has @('START REFUSED \(pid \d+\): another launcher is already running') -Suffix '-second' -Extra @($(if (-not $w) { 'first launcher never waited' }), $(if ($st -notmatch 'waiting-for-go') { "state.txt was changed by the second launcher: $st" }), $(if ($c1 -ne '0') { "first launcher exit $c1" }))
    }
    # Deadline: the runner estimate for t-good.json only=base,s0 repeats=1, as the launcher gets it (-PlanOnly).
    if ((Want 't-deadline-go') -or (Want 't-deadline-gate') -or (Want 't-deadline-wait')) {
        $pl = @(& $PsExe -NoProfile -ExecutionPolicy Bypass -File $RunMatrix -Matrix (& $Fx 't-good.json') -Only 'base,s0' -Repeats 1 -ColdShared -NoPrompt -PlanOnly 2>&1 | ForEach-Object { "$_" })
        $em = @($pl | Where-Object { $_ -match '^estimate (\d+) runs \(\d+ cold\), about (\d+) min' })
        if (-not $em.Count) { throw "no estimate line from -PlanOnly: $($pl -join ' / ')" }
        [void]($em[0] -match 'about (\d+) min'); $est = [int]$Matches[1]
        Write-Host "runner estimate for the test GO: $est min"
    }
    if (Want 't-deadline-go') {
        Stop-IfHold; $b = Snap-Real
        $at = (Get-Date).AddMinutes($est + 5).ToString('yyyy-MM-dd HH:mm')
        $p = Start-L 't-deadline-go' ($Fast + @('-MaxGo', '1', '-StopAt', $at, '-GateFixture', (& $Fx 'gate-quiet.json'))) -Go $GoGood
        $c = Wait-Exit $p 240
        Check 'deadline at GO' 't-deadline-go' $c '0' -Before $b -Has @("GO REFUSED: deadline: estimate $est min \+ 10 min would end after") -HasNot @('GO ACCEPTED', 'HOLD written', 'would start')
    }
    $pg = $null; $pw = $null; $plg = $null
    if (Want 't-latest-gate') {
        Stop-IfHold; $bl = Snap-Real
        $n0 = Get-Date; $sbl = $n0.AddMinutes(3); $sbl = $sbl.Date.AddHours($sbl.Hour).AddMinutes($sbl.Minute)
        $plg = Start-L 't-latest-gate' ($Fast + @('-MaxGo', '1', '-StartBy', $sbl.ToString('yyyy-MM-dd HH:mm'), '-GateFixture', (& $Fx 'gate-busy.json'))) -Go $GoGood
    }
    if (Want 't-deadline-gate') {
        Stop-IfHold; $bg = Snap-Real
        $n0 = Get-Date; $dl = $n0.AddMinutes($est + 14); $dl = $dl.Date.AddHours($dl.Hour).AddMinutes($dl.Minute)
        $pg = Start-L 't-deadline-gate' ($Fast + @('-MaxGo', '1', '-StopAt', $dl.ToString('yyyy-MM-dd HH:mm'), '-GateFixture', (& $Fx 'gate-busy.json'))) -Go $GoGood
    }
    if (Want 't-deadline-wait') {
        Stop-IfHold; $bw = Snap-Real
        $n0 = Get-Date; $dw = $n0.AddMinutes(3); $dw = $dw.Date.AddHours($dw.Hour).AddMinutes($dw.Minute)
        $pw = Start-L 't-deadline-wait' ($Fast + @('-StopAt', $dw.ToString('yyyy-MM-dd HH:mm')))
    }
    if ($pg) {
        $c = Wait-Exit $pg 420
        Check 'deadline in gate' 't-deadline-gate' $c '0' -Before $bg -Has @('GO ACCEPTED', 'quiet gate: DEADLINE \(', 'window not started', 'GATE REFUSED: deadline:', 'HOLD removed') -HasNot @('would start', 'quiet gate: STRICT') -Absent @('WINDOW-HOLD.txt')
    }
    if ($pw) {
        $c = Wait-Exit $pw 420
        $st = [IO.File]::ReadAllText((Join-Path (Join-Path $DryBase 't-deadline-wait') 'state.txt'))
        Check 'deadline, no GO' 't-deadline-wait' $c '0' -Before $bw -Has @(': the launcher ends', 'launcher end: deadline, exit 0') -Extra @($(if ($st -notmatch 'how\s+deadline') { "state.txt: $st" }))
    }
    if ($plg) {
        $c = Wait-Exit $plg 420
        $tl = Line-Time 't-latest-gate' 'quiet gate: DEADLINE'
        Check 'latest start in gate' 't-latest-gate' $c '0' -Before $bl -Has @('GO ACCEPTED', 'quiet gate: DEADLINE \(', 'window not started', 'GATE REFUSED: latest start: no window starts at or after', 'HOLD removed') -HasNot @('would start', 'quiet gate: STRICT') -Absent @('WINDOW-HOLD.txt') -Extra @($(if ($null -eq $tl) { 'no DEADLINE gate line' } elseif ($tl -lt $sbl.AddSeconds(-1)) { "the gate gave up at $tl, before the latest start $sbl" }))
    }
}

if ($Group -eq 'gate') {
    if (Want 't-build') {
        Stop-IfHold; $b = Snap-Real
        $nj = Start-Process -FilePath $Ninja -ArgumentList '-n 90 127.0.0.1' -PassThru -WindowStyle Hidden; [void]$nj.Handle
        Start-Sleep -Milliseconds 500
        $p = Start-L 't-build' ($Fast0 + @('-SampleSeconds', '2', '-GiveUpMinutes', '3', '-MaxGo', '1', '-GateFixture', (& $Fx 'gate-build-real.json'))) -Go $GoGood
        $c = Wait-Exit $p 400
        if (-not $nj.HasExited) { $nj.Kill() }
        $tStrict = Line-Time 't-build' 'quiet gate: STRICT'; $tEnd = $nj.ExitTime
        $order = if ($null -eq $tStrict) { 'no STRICT line' } elseif ($tStrict -lt $tEnd.AddSeconds(-1)) { "gate passed at $tStrict, before ninja exited at $tEnd" } else { '' }
        Check 'build running' 't-build' $c '0' -Before $b -Has @("wait: build/game processes: ninja:$($nj.Id)", 'quiet gate: STRICT', 'would start window T1') -Extra @($order)
    }
    if (Want 't-build-giveup') {
        Stop-IfHold; $b = Snap-Real
        $nj = Start-Process -FilePath $Ninja -ArgumentList '-n 200 127.0.0.1' -PassThru -WindowStyle Hidden; [void]$nj.Handle
        Start-Sleep -Milliseconds 500
        $p = Start-L 't-build-giveup' ($Fast0 + @('-SampleSeconds', '2', '-GiveUpMinutes', '0.5', '-MaxGo', '1', '-GateFixture', (& $Fx 'gate-build-real.json'))) -Go $GoGood
        $c = Wait-Exit $p 300
        if (-not $nj.HasExited) { $nj.Kill() }
        Check 'build all along' 't-build-giveup' $c '0' -Before $b -Has @("wait: build/game processes: ninja:$($nj.Id)", 'quiet gate: GAVE UP \(', 'GATE REFUSED: gave up: the quiet gate did not pass in 0.5 min', 'HOLD removed') -HasNot @('would start', 'quiet gate: STRICT') -Absent @('WINDOW-HOLD.txt')
    }
    if (Want 't-build-start') {
        # The build check is repeated right before the runner starts: this fixture's gate is quiet, but its last check
        # before the window sees a build process (builds_at_start).
        Stop-IfHold; $b = Snap-Real
        $p = Start-L 't-build-start' ($Fast + @('-MaxGo', '1', '-GateFixture', (& $Fx 'gate-build-start.json'))) -Go $GoGood
        $c = Wait-Exit $p 240
        Check 'build at window start' 't-build-start' $c '0' -Before $b -Has @('GO ACCEPTED', 'quiet gate: STRICT', 'START REFUSED: .*build or game processes are running: ninja:4242', 'HOLD removed') -HasNot @('would start', 'window T1 START') -Absent @('WINDOW-HOLD.txt', 'WINDOW-GO.txt')
    }
    if (Want 't-close') {
        # Dry run: the close list is matched and logged ("would close"), nothing is closed. Copies of PING.EXE stand in.
        Stop-IfHold; $b = Snap-Real
        $fp = Join-Path $Here 'fake-procs'
        $fk = @(foreach ($n in @('ChatGPT', 'Windows10Universal', 'copilotapphost')) { $x = Start-Process -FilePath (Join-Path $fp "$n.exe") -ArgumentList '-n 400 127.0.0.1' -PassThru -WindowStyle Hidden; [void]$x.Handle; $x })
        $up = 0; $c = 'not started'
        try {
            Start-Sleep -Milliseconds 500
            $p = Start-L 't-close' ($Fast + @('-MaxGo', '1', '-GateFixture', (& $Fx 'gate-quiet.json'))) -Go $GoGood
            $c = Wait-Exit $p 300
            $up = @($fk | Where-Object { -not $_.HasExited }).Count
        } finally { foreach ($x in $fk) { try { if (-not $x.HasExited) { $x.Kill() } } catch { } } }
        $fpx = [regex]::Escape($fp + '\')
        Check 'close list (dry run)' 't-close' $c '0' -Before $b -Has @("programs \(GO accepted\): would close ChatGPT pid $($fk[0].Id)", "programs \(window start\): would close ChatGPT pid $($fk[0].Id)", "programs \(GO accepted\): left alone: Windows10Universal pid $($fk[1].Id) \(${fpx}Windows10Universal\.exe; closed only from a path matching", "programs \(GO accepted\): left alone: copilotapphost pid $($fk[2].Id) \(${fpx}copilotapphost\.exe; closed only from a path matching", 'would start window T1') -HasNot @("would close Windows10Universal pid $($fk[1].Id)", "would close copilotapphost pid $($fk[2].Id)") -Extra @($(if ($up -ne 3) { "only $up of the 3 fake programs were still running after the dry run" }))
    }
    if (Want 't-stop-start') {
        Stop-IfHold; $b = Snap-Real
        $p = Start-L 't-stop-start' $Fast -Stop
        $c = Wait-Exit $p 120
        Check 'STOP at start' 't-stop-start' $c '2' -Before $b -Has @('START REFUSED: .*WINDOW-STOP\.txt exists') -HasNot @('screensaver', 'waiting for')
    }
    if (Want 't-stop-wait') {
        Stop-IfHold; $b = Snap-Real
        $p = Start-L 't-stop-wait' $Fast
        $w = Wait-Log 't-stop-wait' 'waiting for ' 180
        Put-File 't-stop-wait' 'WINDOW-STOP.txt' 'test stop'; $t0 = Get-Date
        $c = Wait-Exit $p 120; $secs = ((Get-Date) - $t0).TotalSeconds
        Check 'STOP waiting for GO' 't-stop-wait' $c '0' -Before $b -Has @('STOP file seen \(waiting for a GO\)', 'launcher end: STOP file, exit 0') -Absent @('WINDOW-STOP.txt') -Extra @($(if (-not $w) { 'never waited' }), $(if ($secs -gt 30) { "took $([int]$secs) s to end" }))
    }
    if (Want 't-stop-gate') {
        Stop-IfHold; $b = Snap-Real
        $p = Start-L 't-stop-gate' ($Fast + @('-GiveUpMinutes', '5', '-GateFixture', (& $Fx 'gate-busy.json'))) -Go $GoGood
        $w = Wait-Log 't-stop-gate' 'GO ACCEPTED' 240; Start-Sleep -Seconds 4
        Put-File 't-stop-gate' 'WINDOW-STOP.txt' 'test stop'
        $c = Wait-Exit $p 120
        Check 'STOP in the gate' 't-stop-gate' $c '0' -Before $b -Has @('STOP file seen \(waiting for the quiet gate\)', 'HOLD removed', 'launcher end: STOP file, exit 0') -HasNot @('would start') -Absent @('WINDOW-STOP.txt', 'WINDOW-HOLD.txt') -Extra @($(if (-not $w) { 'GO never accepted' }))
    }
    if (Want 't-relaxed') {
        Stop-IfHold; $b = Snap-Real
        $p = Start-L 't-relaxed' ($Fast0 + @('-SampleSeconds', '2', '-StrictMinutes', '1', '-MaxGo', '1', '-GateFixture', (& $Fx 'gate-relaxed.json'))) -Go $GoGood
        $c = Wait-Exit $p 300
        $ta = Line-Time 't-relaxed' 'HOLD written'; $tr = Line-Time 't-relaxed' 'quiet gate: RELAXED'
        $gap = if ($ta -and $tr) { ($tr - $ta).TotalSeconds } else { -1 }
        Check 'relaxed gate' 't-relaxed' $c '0' -Before $b -Has @('strict gate for the first 1 min', 'quiet gate: RELAXED \(MsMpEng 1\.02/1\.02/1\.02', 'relaxed gate: MsMpEng accepted', 'would start window T1') -HasNot @('quiet gate: STRICT') -Present @('relaxed-gate.txt') -Extra @($(if ($gap -lt 55) { "RELAXED came $gap s after the HOLD was written (strict phase is 60 s, counted from GO acceptance)" }))
    }
    if (Want 't-unstable') {
        Stop-IfHold; $b = Snap-Real
        $p = Start-L 't-unstable' ($Fast0 + @('-SampleSeconds', '2', '-StrictMinutes', '0.05', '-GiveUpMinutes', '0.4', '-MaxGo', '1', '-GateFixture', (& $Fx 'gate-unstable.json'))) -Go $GoGood
        $c = Wait-Exit $p 300
        Check 'MsMpEng unstable' 't-unstable' $c '0' -Before $b -Has @('and not <= 1\.2 within 0\.2 of each other', 'quiet gate: GAVE UP') -HasNot @('would start', 'quiet gate: RELAXED')
    }
    if (Want 't-toohigh') {
        Stop-IfHold; $b = Snap-Real
        $p = Start-L 't-toohigh' ($Fast0 + @('-SampleSeconds', '2', '-StrictMinutes', '0.05', '-GiveUpMinutes', '0.4', '-MaxGo', '1', '-GateFixture', (& $Fx 'gate-toohigh.json'))) -Go $GoGood
        $c = Wait-Exit $p 300
        Check 'MsMpEng 1.25 stable' 't-toohigh' $c '0' -Before $b -Has @('MsMpEng not < 0\.1, and not <= 1\.2 within 0\.2 of each other \(1\.25/1\.25/1\.25\)', 'quiet gate: GAVE UP') -HasNot @('would start', 'quiet gate: RELAXED')
    }
    if (Want 't-lowres') {
        Stop-IfHold; $b = Snap-Real
        $p = Start-L 't-lowres' ($Fast + @('-GiveUpMinutes', '0.2', '-MaxGo', '1', '-GateFixture', (& $Fx 'gate-lowres.json'))) -Go $GoGood
        $c = Wait-Exit $p 240
        Check 'low RAM and disk' 't-lowres' $c '0' -Before $b -Has @('available RAM 5\.5 GB < 6', 'free on C: 5 GB < 6', 'quiet gate: GAVE UP') -HasNot @('would start')
    }
    if (Want 't-json') {
        Stop-IfHold; $b = Snap-Real
        $jp = & $Fx 't-json.json'; $orig = [IO.File]::ReadAllBytes($jp)
        $p = Start-L 't-json' ($Fast + @('-MaxGo', '1', '-GateFixture', (& $Fx 'gate-late.json'))) -Go "GO T7 t-json.json $(Sha $jp) only=base repeats=1"
        $w = Wait-Log 't-json' 'GO ACCEPTED' 240
        try { [IO.File]::AppendAllText($jp, "`r`n") ; $c = Wait-Exit $p 240 } finally { [IO.File]::WriteAllBytes($jp, $orig) }
        Check 'matrix changed in gate' 't-json' $c '0' -Before $b -Has @('START REFUSED: sha256 mismatch', 'HOLD removed') -HasNot @('would start') -Extra @($(if (-not $w) { 'GO never accepted' }))
    }
    if (Want 't-real') {
        Stop-IfHold; $b = Snap-Real
        $p = Start-L 't-real' @('-SkipStartChecks', '-MatrixDir', 'build\agent5\launch-test', '-PollSeconds', '1', '-SampleSeconds', '5', '-GiveUpMinutes', '0.4', '-MaxGo', '1') -Go $GoGood
        $c = Wait-Exit $p 300
        Check 'real sensors' 't-real' $c '0' -Before $b -Has @('gate 2 \(\+[\d.]+ min\): cpu MsMpEng \d+\.\d\d, OfficeClickToRun \d+\.\d\d, CrossDeviceService \d+\.\d\d', 'quiet gate: (STRICT|RELAXED|GAVE UP)')
        Write-Host ((@((Log-Text 't-real') -split "`r?`n" | Where-Object { $_ -match 'gate \d+ \(|quiet gate:' })) -join "`r`n")
    }
}

if ($Group -eq 'run') {
    $Fake = Join-Path $Here 'fake-runner.ps1'
    $Inv = [Globalization.CultureInfo]::InvariantCulture
    # '' when the process whose pid is in <status-dryrun\tag>\<name> is gone; else a failure text (and the test kills it).
    function Pid-Gone([string]$Tag, [string]$Name) {
        $f = Join-Path (Join-Path $DryBase $Tag) $Name
        if (-not (Test-Path -LiteralPath $f)) { return "no $Name" }
        $id = [int]([IO.File]::ReadAllText($f).Trim())
        if (Get-Process -Id $id -ErrorAction SilentlyContinue) { try { Stop-Process -Id $id -Force } catch { }; return "pid $id ($Name) was still running (killed by the test)" }
        return ''
    }
    function Read-Pid([string]$Tag, [string]$Name) { $f = Join-Path (Join-Path $DryBase $Tag) $Name; if (Test-Path -LiteralPath $f) { return [IO.File]::ReadAllText($f).Trim() }; return 'none' }
    function Start-Fake([string]$Tag, [int]$Sec, [int]$Child, [string[]]$More = @(), [switch]$OwnConsole) {
        $env:A5_FAKE_SECONDS = "$Sec"; $env:A5_FAKE_CHILD = "$Child"; $env:A5_FAKE_CODE = '0'
        try { return (Start-L $Tag ($Fast + @('-MaxGo', '1', '-GateFixture', (& $Fx 'gate-quiet.json'), '-FakeRunner', $Fake) + $More) -Go $GoGood -OwnConsole:$OwnConsole) }
        finally { Remove-Item Env:\A5_FAKE_SECONDS, Env:\A5_FAKE_CHILD, Env:\A5_FAKE_CODE -ErrorAction SilentlyContinue }
    }
    $kn = 'the runner \(pid \d+\) and every process it started are killed now'
    if (Want 't-run-ok') {
        Stop-IfHold; $b = Snap-Real
        $p = Start-Fake 't-run-ok' 3 0
        $c = Wait-Exit $p 360
        $d = Join-Path $DryBase 't-run-ok'
        $rl = @(Get-ChildItem -LiteralPath $d -Filter 'runner-T1-*.txt' -ErrorAction SilentlyContinue | Where-Object { $_.Name -notmatch '\.(out|err)\.txt$' })
        $rt = if ($rl.Count) { [IO.File]::ReadAllText($rl[0].FullName) } else { '' }
        $oe = @(Get-ChildItem -LiteralPath $d -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^runner-T1-.*\.(out|err)\.txt$' }).Count
        $lr = File-Text 't-run-ok' 'last-result.txt'
        Check 'fake runner, normal end' 't-run-ok' $c '0' -Before $b -Has @('DRY RUN, would start window T1', 'DRY RUN with -FakeRunner', 'window T1 START', 'runner pid \d+; a STOP file, or the end time \d{4}-\d\d-\d\d 07:30:00, stops it and everything it started', 'fake run tick 3', 'fake runner stderr line', 'window T1 END: runner exit 0 \(all runs OK\) after [\d.]+ min; out dir .*fake-out', 'HOLD removed', 'launcher end: -MaxGo, exit 0') -HasNot @('stopped early', 'runner call failed', 'could not be read', 'killed now', 'taskkill') -Absent @('WINDOW-HOLD.txt', 'WINDOW-GO.txt') -Extra @($(if ($rt -notmatch 'fake run tick 3' -or $rt -notmatch 'fake runner stderr line') { "runner-T1-*.txt lacks the runner's lines" }), $(if ($oe -ne 2) { "$oe of the 2 files runner-T1-*.out.txt / .err.txt" }), $(if ($lr -notmatch 'killed\s+no' -or $lr -notmatch 'runner exit 0') { "last-result.txt: $lr" }), (Pid-Gone 't-run-ok' 'fake-runner.pid'))
    }
    if (Want 't-run-stop') {
        Stop-IfHold; $b = Snap-Real
        $p = Start-Fake 't-run-stop' 120 300
        $w = Wait-File (Join-Path (Join-Path $DryBase 't-run-stop') 'fake-child.pid') 300; Start-Sleep -Seconds 2
        $cp = Read-Pid 't-run-stop' 'fake-child.pid'
        Put-File 't-run-stop' 'WINDOW-STOP.txt' 'test stop'; $t0 = Get-Date
        $c = Wait-Exit $p 240; $secs = ((Get-Date) - $t0).TotalSeconds
        Start-Sleep -Seconds 1
        Check 'STOP while running' 't-run-stop' $c '0' -Before $b -Has @('window T1 START', "!!! STOP file: $kn", 'runner pid \d+ killed', "killed \(walk 1\): [^\r\n]*:$cp\b", 'runner stopped: yes', 'window T1 END: runner exit \S* \(stopped early: STOP file; the runner and everything it started were killed\)', "STOP file seen \(while window T1 was running\): 'test stop'", 'HOLD removed', 'launcher end: STOP file, exit 0') -HasNot @('fake runner done', 'NOT killed', 'could not be read') -Absent @('WINDOW-STOP.txt', 'WINDOW-HOLD.txt') -Extra @($(if (-not $w) { 'the fake runner never started its child' }), $(if ($secs -gt 45) { "took $([int]$secs) s to end after the STOP" }), (Pid-Gone 't-run-stop' 'fake-runner.pid'), (Pid-Gone 't-run-stop' 'fake-child.pid'))
    }
    if (Want 't-run-deadline') {
        $pl = @(& $PsExe -NoProfile -ExecutionPolicy Bypass -File $RunMatrix -Matrix (& $Fx 't-good.json') -Only 'base,s0' -Repeats 1 -ColdShared -NoPrompt -PlanOnly 2>&1 | ForEach-Object { "$_" })
        $em = @($pl | Where-Object { $_ -match '^estimate (\d+) runs \(\d+ cold\), about (\d+) min' })
        if (-not $em.Count) { throw "no estimate line from -PlanOnly: $($pl -join ' / ')" }
        [void]($em[0] -match 'about (\d+) min'); $est = [int]$Matches[1]
        Stop-IfHold; $b = Snap-Real
        # -StopAt far enough away for the GO and the window start; -GraceMinutes (< 0 here) puts the end-time kill about
        # 4.5 min from now, while the fake runner (600 s) and its child still run.
        $n0 = Get-Date; $dl = $n0.AddMinutes($est + 16); $dl = $dl.Date.AddHours($dl.Hour).AddMinutes($dl.Minute)
        $grace = [math]::Round(4.5 - ($dl - $n0).TotalMinutes, 2); $hard = $dl.AddMinutes($grace)
        Write-Host "runner estimate $est min; -StopAt $($dl.ToString('HH:mm')); -GraceMinutes $grace (the window is stopped at about $($hard.ToString('HH:mm:ss')))"
        $p = Start-Fake 't-run-deadline' 600 600 @('-StopAt', $dl.ToString('yyyy-MM-dd HH:mm'), '-GraceMinutes', $grace.ToString($Inv))
        $c = Wait-Exit $p 480
        Start-Sleep -Seconds 1
        $cp = Read-Pid 't-run-deadline' 'fake-child.pid'
        $tk = Line-Time 't-run-deadline' 'reached: the runner \(pid'
        $when = if ($null -eq $tk) { 'no kill line' } elseif ($tk -lt $hard.AddSeconds(-2) -or $tk -gt $hard.AddSeconds(20)) { "killed at $tk, want about $hard" } else { '' }
        Check 'end-time kill' 't-run-deadline' $c '0' -Before $b -Has @('window T1 START', "!!! end time [^\r\n]* reached: $kn", 'runner pid \d+ killed', "killed \(walk 1\): [^\r\n]*:$cp\b", 'runner stopped: yes', 'window T1 END: runner exit \S* \(stopped early: end time [^\r\n]* reached; the runner and everything it started were killed\)', 'HOLD removed', 'launcher end: -MaxGo, exit 0') -HasNot @('fake runner done', 'NOT killed', 'could not be read') -Absent @('WINDOW-HOLD.txt') -Extra @($when, (Pid-Gone 't-run-deadline' 'fake-runner.pid'), (Pid-Gone 't-run-deadline' 'fake-child.pid'))
    }
    if (Want 't-run-error') {
        # A launcher error while the runner runs (dry-run hook -TestFailAfter: a throw in the wait loop 25 s after the start).
        Stop-IfHold; $b = Snap-Real
        $p = Start-Fake 't-run-error' 120 300 @('-TestFailAfter', '25')
        $c = Wait-Exit $p 360
        Start-Sleep -Seconds 1
        $cp = Read-Pid 't-run-error' 'fake-child.pid'
        Check 'launcher error in run' 't-run-error' $c '0' -Before $b -Has @('window T1 START', '!!! launcher error while the runner was running \(simulated launcher error \(dry-run hook -TestFailAfter 25\)\)', "!!! launcher error while the runner was running \(simulated [^\r\n]*\): $kn", 'runner pid \d+ killed', "killed \(walk 1\): [^\r\n]*:$cp\b", 'runner stopped: yes', 'window T1 END: runner exit \S* \(stopped early: launcher error while the runner was running \(simulated', 'HOLD removed', 'launcher end: -MaxGo, exit 0') -HasNot @('fake runner done', 'NOT killed', 'runner call failed', 'could not be read') -Absent @('WINDOW-HOLD.txt') -Extra @((Pid-Gone 't-run-error' 'fake-runner.pid'), (Pid-Gone 't-run-error' 'fake-child.pid'))
    }
    if (Want 't-run-ctrlc') {
        # Ctrl+C while the fake runner runs. This launcher runs in its own hidden console; send-ctrlc.ps1 attaches to that
        # console only (it refuses if it is this test's console) and sends Ctrl+C there: the launcher and the fake runner
        # get it, the fake child (its own console) does not. The launcher's exit code is recorded, not required.
        Stop-IfHold; $b = Snap-Real
        $p = Start-Fake 't-run-ctrlc' 120 300 -OwnConsole
        $w = Wait-File (Join-Path (Join-Path $DryBase 't-run-ctrlc') 'fake-child.pid') 300; Start-Sleep -Seconds 2
        $cp = Read-Pid 't-run-ctrlc' 'fake-child.pid'
        $sc = 'not sent'; $so = Join-Path $Out 't-run-ctrlc.send.txt'; $t0 = Get-Date
        if ($w -and -not $p.HasExited) {
            $h = Start-Process -FilePath $PsExe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File $(Q (Join-Path $Here 'send-ctrlc.ps1')) -TargetPid $($p.Id)" -NoNewWindow -PassThru -RedirectStandardOutput $so -RedirectStandardError "$so.err"
            [void]$h.Handle
            if ($h.WaitForExit(120000)) { $sc = "exit $($h.ExitCode)" } else { try { $h.Kill() } catch { }; $sc = 'TIMEOUT' }
            $t0 = Get-Date
        }
        $c = Wait-Exit $p 100; $secs = ((Get-Date) - $t0).TotalSeconds
        Start-Sleep -Seconds 1
        $st = File-Text 't-run-ctrlc' 'state.txt'
        $sot = if (Test-Path -LiteralPath $so) { ([IO.File]::ReadAllText($so).Trim() -split "`r?`n") -join ' / ' } else { '' }
        Write-Host "t-run-ctrlc: send-ctrlc $sc ($sot); launcher exit $c, $([int]$secs) s after the Ctrl+C; state.txt: $(($st.Trim() -split "`r?`n") -join ' | ')"
        Check 'Ctrl+C while running' 't-run-ctrlc' $c '' -Before $b -Has @('window T1 START', "!!! (the launcher was interrupted \(Ctrl\+C\?\)|launcher error) while the runner was running[^\r\n]*: $kn", "killed \(walk 1\): [^\r\n]*:$cp\b", 'runner stopped: yes', 'HOLD removed') -HasNot @('fake runner done', 'NOT killed', 'could not be read') -Absent @('WINDOW-HOLD.txt') -Extra @($(if (-not $w) { 'the fake runner never started its child' }), $(if ($sc -ne 'exit 0') { "send-ctrlc: $sc ($sot)" }), $(if ($c -eq 'TIMEOUT') { 'the launcher did not end within 100 s of the Ctrl+C' }), $(if ($st -notmatch 'state\s+ended') { "state.txt: $st" }), (Pid-Gone 't-run-ctrlc' 'fake-runner.pid'), (Pid-Gone 't-run-ctrlc' 'fake-child.pid'))
    }
}

if ($Group -eq 'pin') {
    if (Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object { $_.CommandLine -match 'run-night\.ps1' }) { throw 'another run-night.ps1 is running: the pin tests change RUN-NIGHT.cmd and would disturb it' }
    $orig = [IO.File]::ReadAllBytes($NightCmd); $origSha = Sha $NightCmd
    try {
        if (Want 't-pin-go') {
            Stop-IfHold; $b = Snap-Real
            $p = Start-L 't-pin-go' ($Fast + @('-MaxGo', '1', '-GateFixture', (& $Fx 'gate-quiet.json')))
            $w = Wait-Log 't-pin-go' 'waiting for ' 180
            [IO.File]::AppendAllText($NightCmd, "rem pin test`r`n"); Put-File 't-pin-go' 'WINDOW-GO.txt' $GoGood
            $c = Wait-Exit $p 240; [IO.File]::WriteAllBytes($NightCmd, $orig)
            Check 'pin changed before GO' 't-pin-go' $c '0' -Before $b -Has @('GO REFUSED: pinned files changed since the start: bench\\agent5\\launch\\RUN-NIGHT\.cmd changed') -HasNot @('GO ACCEPTED', 'would start') -Extra @($(if (-not $w) { 'never waited' }))
        }
        if (Want 't-pin-gate') {
            Stop-IfHold; $b = Snap-Real
            $p = Start-L 't-pin-gate' ($Fast + @('-MaxGo', '1', '-GateFixture', (& $Fx 'gate-late.json'))) -Go $GoGood
            $w = Wait-Log 't-pin-gate' 'GO ACCEPTED' 240
            [IO.File]::AppendAllText($NightCmd, "rem pin test`r`n")
            $c = Wait-Exit $p 240; [IO.File]::WriteAllBytes($NightCmd, $orig)
            Check 'pin changed in gate' 't-pin-gate' $c '0' -Before $b -Has @('START REFUSED: pinned files changed since the start: bench\\agent5\\launch\\RUN-NIGHT\.cmd changed', 'HOLD removed') -HasNot @('would start') -Extra @($(if (-not $w) { 'GO never accepted' }))
        }
    } finally { [IO.File]::WriteAllBytes($NightCmd, $orig) }
    if ((Sha $NightCmd) -ne $origSha) { Write-Host '!!! RUN-NIGHT.cmd is not back to its original bytes' -ForegroundColor Red } else { Write-Host "RUN-NIGHT.cmd restored ($origSha)" }
}

if ($Group -eq 'hold') {
    # A HOLD that is not the launcher's is never replaced or deleted, and the quiet gate fails while it exists.
    $foreign = 'HOLD by someone else (Agent 5 launcher test)'
    function Hold-Path([string]$Tag) { return (Join-Path (Join-Path $DryBase $Tag) 'WINDOW-HOLD.txt') }
    function Hold-Kept([string]$Tag) { $hf = Hold-Path $Tag; return ((Test-Path -LiteralPath $hf) -and ([IO.File]::ReadAllText($hf).Trim() -eq $foreign)) }
    function Retry([scriptblock]$Do) { for ($k = 0; $k -lt 20; $k++) { try { & $Do; return } catch { Start-Sleep -Milliseconds 100 } }; & $Do }
    if (Want 't-hold-foreign') {
        Stop-IfHold; $b = Snap-Real
        $p = Start-L 't-hold-foreign' ($Fast + @('-MaxGo', '1', '-GateFixture', (& $Fx 'gate-quiet.json'))) -Go $GoGood -Hold $foreign
        $w = Wait-Log 't-hold-foreign' 'GO ACCEPTED' 240; Start-Sleep -Seconds 8
        $kept = Hold-Kept 't-hold-foreign'; $early = (Log-Text 't-hold-foreign') -match 'would start'
        $tDel = Get-Date; Retry { Remove-Item -LiteralPath (Hold-Path 't-hold-foreign') -Force }
        $c = Wait-Exit $p 240
        $tw = Line-Time 't-hold-foreign' 'HOLD written'
        Check 'foreign HOLD at GO, then gone' 't-hold-foreign' $c '0' -Before $b -Has @('foreign HOLD \(', 'it is not replaced', 'wait: foreign HOLD', 'HOLD written', 'quiet gate: STRICT', 'would start window T1', 'HOLD removed') -Absent @('WINDOW-HOLD.txt', 'WINDOW-GO.txt') -Extra @($(if (-not $w) { 'GO never accepted' }), $(if (-not $kept) { 'the foreign HOLD was changed or deleted while it was there' }), $(if ($early) { 'the window would have started while the foreign HOLD was there' }), $(if ($tw -and $tw -lt $tDel.AddSeconds(-1)) { "HOLD written at $tw, before the foreign HOLD was gone ($tDel)" }))
    }
    if (Want 't-hold-keep') {
        Stop-IfHold; $b = Snap-Real
        $p = Start-L 't-hold-keep' ($Fast + @('-GiveUpMinutes', '0.25', '-MaxGo', '1', '-GateFixture', (& $Fx 'gate-quiet.json'))) -Go $GoGood -Hold $foreign
        $c = Wait-Exit $p 300
        $kept = Hold-Kept 't-hold-keep'
        Check 'foreign HOLD all along' 't-hold-keep' $c '0' -Before $b -Has @('wait: foreign HOLD', 'quiet gate: GAVE UP \(', 'GATE REFUSED: gave up') -HasNot @('HOLD written', 'HOLD removed', 'would start', 'quiet gate: STRICT') -Extra @($(if (-not $kept) { 'the foreign HOLD was changed or deleted' }))
        Retry { Remove-Item -LiteralPath (Hold-Path 't-hold-keep') -Force -ErrorAction SilentlyContinue }
    }
    if (Want 't-hold-gone') {
        Stop-IfHold; $b = Snap-Real
        $p = Start-L 't-hold-gone' ($Fast + @('-MaxGo', '1', '-GateFixture', (& $Fx 'gate-late.json'))) -Go $GoGood
        $w = Wait-Log 't-hold-gone' 'GO ACCEPTED' 240; Start-Sleep -Seconds 3
        $had = Test-Path -LiteralPath (Hold-Path 't-hold-gone')
        Retry { Remove-Item -LiteralPath (Hold-Path 't-hold-gone') -Force }
        $c = Wait-Exit $p 240
        $n = ([regex]::Matches((Log-Text 't-hold-gone'), 'HOLD written')).Count
        Check 'our HOLD removed in the gate' 't-hold-gone' $c '0' -Before $b -Has @('the HOLD file was removed by someone else before the window started: it is written again', 'would start window T1', 'HOLD removed') -Absent @('WINDOW-HOLD.txt') -Extra @($(if (-not $w) { 'GO never accepted' }), $(if (-not $had) { 'no HOLD file 3 s after the GO' }), $(if ($n -ne 2) { "$n 'HOLD written' lines, want 2" }))
    }
    if (Want 't-hold-taken') {
        Stop-IfHold; $b = Snap-Real
        $p = Start-L 't-hold-taken' ($Fast + @('-GiveUpMinutes', '0.3', '-MaxGo', '1', '-GateFixture', (& $Fx 'gate-late.json'))) -Go $GoGood
        $w = Wait-Log 't-hold-taken' 'GO ACCEPTED' 240; Start-Sleep -Seconds 2
        Retry { [IO.File]::WriteAllText((Hold-Path 't-hold-taken'), $foreign + "`r`n") }
        $c = Wait-Exit $p 300
        $kept = Hold-Kept 't-hold-taken'
        Check 'our HOLD taken over in the gate' 't-hold-taken' $c '0' -Before $b -Has @("this window's HOLD was replaced by someone else's", 'wait: foreign HOLD', 'quiet gate: GAVE UP \(') -HasNot @('would start', 'HOLD removed') -Extra @($(if (-not $w) { 'GO never accepted' }), $(if (-not $kept) { 'the foreign HOLD was changed or deleted' }))
        Retry { Remove-Item -LiteralPath (Hold-Path 't-hold-taken') -Force -ErrorAction SilentlyContinue }
    }
}

$sum = Join-Path $Out "summary-$Group.txt"
$txt = "group $Group, $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), run-night.ps1 $(Sha $Launcher)$(if ($StopAt) { "; -StopAt $StopAt for the launchers without their own" })`r`n" + (($Rows | Format-Table -AutoSize -Wrap | Out-String -Width 400).TrimEnd())
[IO.File]::WriteAllText($sum, $txt + "`r`n")
Write-Host $txt
Write-Host "real perf-notes files at the end: $(Snap-Real)"
if (@($Rows | Where-Object { $_.result -ne 'PASS' }).Count) { exit 1 } else { exit 0 }

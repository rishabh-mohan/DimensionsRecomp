<#
.SYNOPSIS
  Test G session (task #23): the test G runs on one bin dir, one game at a time, each one
  testg_launch.ps1 -Driver watch in its own run dir under build\agent11\runs.
    half 1   pause_safe_order=true,  guest_suspend_guard=false
    half 2   pause_safe_order=true,  guest_suspend_guard=true
    control  pause_safe_order=false, guest_suspend_guard=false (the original pause order; shows the
             test can see the hang). Skipped with -NoControl, or (unless -ForceControl) when another *-bin dir has appeared
             in build\agent2 (the native ON staging), so that the slot goes back for the native boot.
    default  guest_suspend_guard=false and NO --pause_safe_order, so the build's default picks the
             order (the S3 default-ON check). Opt-in: runs only with -Only default, and only on a build
             that carries the default-ON help text (unless -NoMarkerCheck).
  Every run adds debug_pause_cycle_ms=PeriodMs and debug_pause_cycle_count=Cycles (Agent 12, #17).

.DESCRIPTION
  Refuses to start unless the bin defines all four cvars and no other legodimensions.exe runs.
  A hung game is killed by the launcher (WM_CLOSE, then a kill after 30 s) after the driver has
  written its minidump. Writes build\agent11\runs\testg-session-<time>.txt. Exit 0 when the
  runs it started all finished (whatever their verdicts), 2 if it did not start.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_session.ps1 -CheckOnly
  powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_session.ps1
  powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_session.ps1 -Only control -ForceControl
  powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_session.ps1 -BinDir build\agent2\devoff3-bin -Only default
#>
param(
    [string]$BinDir = 'build\agent2\devoff1-bin',
    [int]$Cycles = 50,
    [int]$PeriodMs = 1000,
    [string[]]$Only = @(),
    [switch]$NoControl,
    [switch]$ForceControl,            # run the control even when another *-bin dir is staged
    [switch]$CheckOnly,
    [switch]$NoMarkerCheck   # 'default' run: skip the default-ON check (only after checking S3's rex_app.cpp hash)
)
$ErrorActionPreference = 'Stop'
$Only = @($Only | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
if (-not ('TestGWin' -as [type])) {
    Add-Type -TypeDefinition ([IO.File]::ReadAllText((Join-Path $PSScriptRoot 'testg_win.cs'))) -Language CSharp
}
$bin = $BinDir
if (-not [IO.Path]::IsPathRooted($bin)) { $bin = [IO.Path]::GetFullPath((Join-Path $root $bin)) }
$bin = $bin.TrimEnd('\')
$runsDir = Join-Path $root 'build\agent11\runs'
New-Item -ItemType Directory -Force -Path $runsDir | Out-Null
$sessionFile = Join-Path $runsDir ('testg-session-{0:yyyyMMdd-HHmmss}.txt' -f (Get-Date))
$out = New-Object 'System.Collections.Generic.List[string]'
function Say([string]$s) { $line = ('{0:HH:mm:ss} {1}' -f (Get-Date), $s); Write-Host $line; $out.Add($line) }
function Save { [IO.File]::WriteAllLines($sessionFile, $out) }

$exe = Join-Path $bin 'legodimensions.exe'
$dll = Join-Path $bin 'rexruntime.dll'
if (-not (Test-Path -LiteralPath $exe)) { Say "NOT STARTED: no legodimensions.exe in $bin"; Save; exit 2 }
$dllTime = '-'
if (Test-Path -LiteralPath $dll) { $dllTime = '{0:yyyy-MM-dd HH:mm}' -f (Get-Item -LiteralPath $dll).LastWriteTime }
Say ('bin {0}: exe {1:yyyy-MM-dd HH:mm}, rexruntime.dll {2}' -f $bin, (Get-Item -LiteralPath $exe).LastWriteTime, $dllTime)
$missing = @()
foreach ($n in 'pause_safe_order', 'guest_suspend_guard', 'debug_pause_cycle_ms', 'debug_pause_cycle_count') {
    $found = $false
    if (Test-Path -LiteralPath $dll) { $found = [TestGWin]::ContainsAscii($dll, $n) }
    if (-not $found) { $found = [TestGWin]::ContainsAscii($exe, $n) }
    if (-not $found) { $missing += $n }
}
if ($missing.Count) { Say "NOT STARTED: this build does not define $($missing -join ', ')"; Save; exit 2 }
Say 'the build defines pause_safe_order, guest_suspend_guard, debug_pause_cycle_ms and debug_pause_cycle_count'
# 'default' passes no --pause_safe_order, so the build's own default picks the pause order. On a
# default-OFF build that is the original order, which hangs (the control), so it needs the S3
# default-ON change. Its marker is the new help text, compiled into the cvar's description.
$marker = 'which can hang when the guest pauses'
if ((($Only -contains 'default') -or ($Only -contains 'testg-default')) -and -not $NoMarkerCheck) {
    $hasMarker = $false
    if (Test-Path -LiteralPath $dll) { $hasMarker = [TestGWin]::ContainsAscii($dll, $marker) }
    if (-not $hasMarker) { $hasMarker = [TestGWin]::ContainsAscii($exe, $marker) }
    if (-not $hasMarker) { Say "NOT STARTED: the 'default' run needs a pause_safe_order default-ON build, and this one lacks its help text ('$marker')"; Save; exit 2 }
    Say "the build carries the pause_safe_order default-ON help text ('$marker')"
}
$others = @([Diagnostics.Process]::GetProcessesByName('legodimensions'))
if ($others.Count) { Say ("NOT STARTED: another game is running (pid {0})" -f ((@($others | ForEach-Object { $_.Id })) -join ',')); Save; exit 2 }
if ($CheckOnly) { Say 'check only: nothing started'; Save; exit 0 }

$runs = @(
    @{ Name = 'testg-b-off'; Label = 'half 1 (safe order, B off)'; Cvar = 'pause_safe_order=true,guest_suspend_guard=false'; Control = $false },
    @{ Name = 'testg-b-on'; Label = 'half 2 (safe order, B on)'; Cvar = 'pause_safe_order=true,guest_suspend_guard=true'; Control = $false },
    @{ Name = 'testg-control'; Label = 'control (old order, B off)'; Cvar = 'pause_safe_order=false,guest_suspend_guard=false'; Control = $true },
    @{ Name = 'testg-default'; Label = 'half 1 on the build default (no --pause_safe_order, B off)'; Cvar = 'guest_suspend_guard=false'; Control = $false; OptIn = $true }
)
$launcher = Join-Path $PSScriptRoot 'testg_launch.ps1'
$rx = @{
    debug = [regex]'Debug pause cycle: every \d+ ms'
    susp  = [regex]'Guest suspended \(\d+ threads\)'
    res   = [regex]'Guest resumed \(\d+ threads\)'
    err   = [regex]'^\[[^\]]+\] \[(error|critical)\]'
}
$summary = @()
foreach ($r in $runs) {
    $short = $r.Name -replace '^testg-', ''
    if ($Only.Count -and ($Only -notcontains $r.Name) -and ($Only -notcontains $short)) { continue }
    if ($r.OptIn -and ($Only -notcontains $r.Name) -and ($Only -notcontains $short)) { continue }
    if ($r.Control) {
        if ($NoControl) { Say 'control skipped (-NoControl)'; continue }
        $native = @(Get-ChildItem -LiteralPath (Join-Path $root 'build\agent2') -Directory -Filter '*-bin' -ErrorAction SilentlyContinue | Where-Object { $_.FullName.TrimEnd('\') -ne $bin })
        if ($native.Count -and -not $ForceControl) { Say ("control skipped: another staged bin dir exists ({0}), so the slot goes back for the native boot" -f ((@($native | ForEach-Object { $_.Name })) -join ', ')); continue }
    }
    $still = @([Diagnostics.Process]::GetProcessesByName('legodimensions'))
    # The previous run's game may take a moment to go after the launcher's kill: wait up to 30 s.
    for ($w = 0; $still.Count -and $w -lt 30; $w++) { Start-Sleep -Seconds 1; $still = @([Diagnostics.Process]::GetProcessesByName('legodimensions')) }
    if ($still.Count) { Say ("{0}: NOT STARTED, a game is still running (pid {1})" -f $r.Label, ((@($still | ForEach-Object { $_.Id })) -join ',')); $summary += "$($r.Label): NOT STARTED (another game running)"; continue }
    $cv = "$($r.Cvar),debug_pause_cycle_ms=$PeriodMs,debug_pause_cycle_count=$Cycles"
    Say "$($r.Label): starting, cvars $cv"
    $before = @(Get-ChildItem -LiteralPath $runsDir -Directory -Filter "*-$($r.Name)" -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
    # 'Continue' here: under 'Stop', PowerShell 5.1 turns the child's stderr (2>&1) into a
    # terminating error, which would end this script while the launcher and game run on.
    $ErrorActionPreference = 'Continue'
    & powershell -NoProfile -ExecutionPolicy Bypass -File $launcher -BinDir $bin -Name $r.Name -Driver watch -Cycles $Cycles -PeriodMs $PeriodMs -Cvar $cv 2>&1 | ForEach-Object { Write-Host "    $_" }
    $code = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    $dir = @(Get-ChildItem -LiteralPath $runsDir -Directory -Filter "*-$($r.Name)" | Where-Object { $before -notcontains $_.FullName } | Sort-Object Name | Select-Object -Last 1)
    if (-not $dir.Count) { Say "$($r.Label): exit $code, no run dir found"; $summary += "$($r.Label): exit $code, no run dir"; continue }
    $d = $dir[0].FullName
    if ($r.OptIn) {
        # The default run is only valid if nothing set pause_safe_order: not the command line, and
        # not the toml the launcher copied into the run dir (from -Toml, harness\legodimensions.toml).
        $set = @()
        foreach ($f in 'cmdline.txt', 'legodimensions.toml') {
            $p = Join-Path $d $f
            if (-not (Test-Path -LiteralPath $p)) { $set += "$f missing"; continue }
            if ([IO.File]::ReadAllText($p) -match 'pause_safe_order') { $set += "$f sets pause_safe_order" }
        }
        if ($set.Count) { Say ("{0}: WARNING, the build default may not have picked the order: {1}" -f $r.Label, ($set -join '; ')) }
        else { Say ('{0}: cmdline.txt and legodimensions.toml do not set pause_safe_order, so the build default picked the order' -f $r.Label) }
    }
    $verdict = '(no report)'
    $rep = Join-Path $d 'testg_report.txt'
    $repText = ''
    if (Test-Path -LiteralPath $rep) { $repText = [IO.File]::ReadAllText($rep); $m = [regex]::Match($repText, '(?m)^VERDICT: (.*)$'); if ($m.Success) { $verdict = $m.Groups[1].Value.Trim() } }
    $tm = [regex]::Match($repText, '(?m)^threads: (.*)$')
    if ($tm.Success) { Say ('{0}: threads {1}' -f $r.Label, $tm.Groups[1].Value.Trim()) }
    $log = Join-Path $d 'game.log'
    $nd = 0; $ns = 0; $nr = 0; $ne = 0
    if (Test-Path -LiteralPath $log) {
        foreach ($l in (New-Object 'TestGWin+LogTail' -ArgumentList $log, $true).Read()) {
            if ($rx.debug.IsMatch($l)) { $nd++ }
            if ($rx.susp.IsMatch($l)) { $ns++ }
            if ($rx.res.IsMatch($l)) { $nr++ }
            if ($rx.err.IsMatch($l)) { $ne++ }
        }
    }
    $dumpFiles = @(Get-ChildItem -LiteralPath $d -Filter 'hang-*.dmp' -ErrorAction SilentlyContinue)
    $dumps = @($dumpFiles | ForEach-Object { '{0} ({1:N0} bytes)' -f $_.Name, $_.Length })
    foreach ($f in $dumpFiles) {
        # Where it hung: the stack report next to the dump (the run dir holds the bin's exe and .map).
        $ErrorActionPreference = 'Continue'
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'testg_dump.ps1') -Dump $f.FullName -BinDir $d 2>&1 | Select-Object -Last 40 | ForEach-Object { Write-Host "    $_" }
        $ErrorActionPreference = 'Stop'
        Say ('{0}: stack report {1}' -f $r.Label, [IO.Path]::ChangeExtension($f.FullName, '.txt'))
    }
    $stop = ''
    if (Test-Path -LiteralPath (Join-Path $d 'stop.txt')) { $stop = (Get-Content -LiteralPath (Join-Path $d 'stop.txt') | Select-Object -Last 1) }
    $line = "{0}: exit {1}, {2}; log: 'Debug pause cycle' x{3}, suspended {4}, resumed {5}, error/critical {6}; dumps: {7}; stop: {8}; run dir {9}" -f $r.Label, $code, $verdict, $nd, $ns, $nr, $ne, $(if ($dumps.Count) { $dumps -join ', ' } else { 'none' }), $stop, $d
    Say $line
    $summary += $line
}
Say 'SUMMARY'
foreach ($s in $summary) { Say "  $s" }
Say "session file: $sessionFile"
Save
exit 0

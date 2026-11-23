<#
.SYNOPSIS
  Test G launcher (task #19): starts one game in its own run dir under build\agent11\runs, optionally
  runs testg_driver.ps1 against it, then closes it (WM_CLOSE; killed if still running after 30 s).

.DESCRIPTION
  Run dir: every file of -BinDir hard-linked (copied if that fails), and -Toml copied next to the exe
  with user_data_root pointed at <run>\user. Nothing is written to game\, harness\ or -BinDir.
  Refuses to start while another legodimensions.exe runs (one game at a time) unless -Force.
  Command line: --log_file=<run>\game.log --discord_rpc=false --native_settings_load=false
  --pause_when_unfocused=true (unless -NoPauseWhenUnfocused), then each -Cvar name=value as
  --name=value. Unknown cvars are harmless (cvar.cpp stashes unrecognised --options), but
  cvars.txt records which binary defines each one, and a missing one is warned about.
  Writes <run>\cmdline.txt, game.pid, cvars.txt, game.log, testg_report.txt/.csv, stop.txt, summary.txt.
  Exit code: the driver's (0 PASS, 1 FAIL, 2 setup error, 3 INCONCLUSIVE); 2 if the game does not start.

.EXAMPLE
  # probe: can posted focus messages pause and resume the baseline on a locked desktop?
  powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_launch.ps1 -BinDir build\baseline-bin -Name probe-post -Driver post -Cycles 5
.EXAMPLE
  # test G half 1 (guard B off); half 2 is the same with guest_suspend_guard=true and -Name testg-b-on
  powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_launch.ps1 -BinDir <dev OFF build 1 bin> -Name testg-b-off -Driver watch -Cycles 50 -PeriodMs 1000 -Cvar "pause_safe_order=true,guest_suspend_guard=false,<debug timer cvars>"
#>
param(
    [string]$BinDir = 'build\baseline-bin',
    [string]$Name = 'testg',
    [string]$Toml = 'harness\legodimensions.toml',
    [string[]]$Cvar = @(),
    [switch]$NoPauseWhenUnfocused,
    [int]$BootSec = 60,               # post: boot time before the first cycle; watch: max wait for the window
    [ValidateSet('none', 'post', 'watch')][string]$Driver = 'none',
    [int]$Cycles = 50,
    [int]$PeriodMs = 1000,
    [int]$HoldMs = 1000,
    [int]$GapMs = 1000,
    [int]$FirstEventTimeoutSec = 180,
    [switch]$KeepRunning,
    [switch]$Force,
    [string]$Stop = ''                # run dir: close the game started there, then exit
)

$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
function Abs([string]$p) { if ([IO.Path]::IsPathRooted($p)) { return $p }; return [IO.Path]::GetFullPath((Join-Path $root $p)) }
if (-not ('TestGWin' -as [type])) {
    Add-Type -TypeDefinition ([IO.File]::ReadAllText((Join-Path $PSScriptRoot 'testg_win.cs'))) -Language CSharp
}

function Stop-Game([string]$run) {
    $pidFile = Join-Path $run 'game.pid'
    if (-not (Test-Path -LiteralPath $pidFile)) { Write-Host "no game.pid in $run"; return }
    $gpid = [int](Get-Content -LiteralPath $pidFile -TotalCount 1)
    try { $p = [Diagnostics.Process]::GetProcessById($gpid) } catch { Write-Host "game $gpid had already exited"; return }
    $n = [TestGWin]::CloseAll($gpid)
    $how = "WM_CLOSE to $n window(s)"
    if ($p.WaitForExit(30000)) { $how += '; exited' }
    else {
        try { $p.Kill(); [void]$p.WaitForExit(10000); $how += '; still running after 30 s, killed' }
        catch { $how += "; kill failed: $($_.Exception.Message)" }
    }
    $line = ('{0:HH:mm:ss} game {1}: {2}' -f (Get-Date), $gpid, $how)
    Write-Host $line
    Add-Content -LiteralPath (Join-Path $run 'stop.txt') -Value $line
}

if ($Stop) { Stop-Game (Abs $Stop); exit 0 }

$bin = (Abs $BinDir).TrimEnd('\')
if (-not (Test-Path -LiteralPath (Join-Path $bin 'legodimensions.exe'))) { Write-Host "no legodimensions.exe in $bin"; exit 2 }
$others = @([Diagnostics.Process]::GetProcessesByName('legodimensions'))
if ($others.Count -gt 0 -and -not $Force) {
    Write-Host ("another game is running (pid {0}); one game at a time, so not starting (-Force overrides)" -f ((@($others | ForEach-Object { $_.Id })) -join ','))
    exit 2
}

$run = Join-Path $root ('build\agent11\runs\{0:yyyyMMdd-HHmmss}-{1}' -f (Get-Date), $Name)
$user = Join-Path $run 'user'
New-Item -ItemType Directory -Force -Path $user | Out-Null
$copied = @()
foreach ($f in Get-ChildItem -LiteralPath $bin -File -Recurse) {
    if ($f.Name -ieq 'legodimensions.toml') { continue }
    $rel = $f.FullName.Substring($bin.Length + 1)
    $dst = Join-Path $run $rel
    $dir = Split-Path -Parent $dst
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    if (-not [TestGWin]::HardLink($dst, $f.FullName)) { Copy-Item -LiteralPath $f.FullName -Destination $dst; $copied += $rel }
}
if ($copied.Count) { Write-Host "copied because the hard link failed: $($copied -join ', ')" }

$tomlText = [IO.File]::ReadAllText((Abs $Toml))
$userLine = "user_data_root = '$user'"
if ($tomlText -match '(?m)^user_data_root\s*=') { $tomlText = [regex]::Replace($tomlText, '(?m)^user_data_root\s*=[^\r\n]*', $userLine.Replace('$', '$$')) }
else { $tomlText += "`r`n$userLine`r`n" }
[IO.File]::WriteAllText((Join-Path $run 'legodimensions.toml'), $tomlText)

$log = Join-Path $run 'game.log'
$exe = Join-Path $run 'legodimensions.exe'
$argv = @("--log_file=$log", '--discord_rpc=false', '--native_settings_load=false')
$names = @()
if (-not $NoPauseWhenUnfocused) { $argv += '--pause_when_unfocused=true'; $names += 'pause_when_unfocused' }
foreach ($c in $Cvar) {
    foreach ($kv in ($c -split ',')) {
        $kv = $kv.Trim().TrimStart('-')
        if ($kv) { $argv += "--$kv"; $names += ($kv -split '=')[0] }
    }
}
$argLine = (@($argv | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } })) -join ' '

$dll = Join-Path $run 'rexruntime.dll'
$cv = @(foreach ($n in ($names | Select-Object -Unique)) {
    $where = 'NOT FOUND'
    if ((Test-Path -LiteralPath $dll) -and [TestGWin]::ContainsAscii($dll, $n)) { $where = 'rexruntime.dll' }
    elseif ([TestGWin]::ContainsAscii($exe, $n)) { $where = 'legodimensions.exe' }
    '{0} = {1}' -f $n, $where
})
Set-Content -LiteralPath (Join-Path $run 'cvars.txt') -Value $cv
$missing = @($cv | Where-Object { $_ -like '*NOT FOUND' })
if ($missing.Count) { Write-Host "WARNING: this build does not define: $($missing -join '; ') (passed anyway; the runtime ignores unknown flags)" }

Set-Content -LiteralPath (Join-Path $run 'cmdline.txt') -Value ("`"$exe`" $argLine")
$p = Start-Process -FilePath $exe -ArgumentList $argLine -WorkingDirectory $run -PassThru
Set-Content -LiteralPath (Join-Path $run 'game.pid') -Value $p.Id
Write-Host ('{0:HH:mm:ss} started pid {1} in {2}' -f (Get-Date), $p.Id, $run)

$sw = [Diagnostics.Stopwatch]::StartNew()
$h = [IntPtr]::Zero
while ($sw.Elapsed.TotalSeconds -lt $BootSec -and -not $p.HasExited) {
    if ($h -eq [IntPtr]::Zero) {
        $h = [TestGWin]::MainWindow($p.Id)
        if ($h -ne [IntPtr]::Zero) { Write-Host ('{0,4:N0} s: window {1}' -f $sw.Elapsed.TotalSeconds, [TestGWin]::Describe($h)) }
    }
    if ($Driver -eq 'watch' -and $h -ne [IntPtr]::Zero) { break }
    Start-Sleep -Milliseconds 500
}
$logLen = 0
if (Test-Path -LiteralPath $log) { $logLen = (Get-Item -LiteralPath $log).Length }
Write-Host ('{0,4:N0} s: boot wait over; game.log {1} bytes' -f $sw.Elapsed.TotalSeconds, $logLen)

$code = 0
try {
    if ($p.HasExited) { Write-Host "the game exited during boot"; $code = 2 }
    elseif ($Driver -ne 'none') {
        & (Join-Path $PSScriptRoot 'testg_driver.ps1') -GamePid $p.Id -Log $log -Mode $Driver -Cycles $Cycles -PeriodMs $PeriodMs -HoldMs $HoldMs -GapMs $GapMs -FirstEventTimeoutSec $FirstEventTimeoutSec -FromStart -Out (Join-Path $run 'testg_report.txt')
        $code = $LASTEXITCODE
    }
}
catch { Write-Host "driver error: $($_.Exception.Message)`n$($_.ScriptStackTrace)"; $code = 2 }
finally {
    # always close the game: only this command can reach its window (hidden desktop)
    if ($KeepRunning -and -not $p.HasExited) { Write-Host "left running; close it with: -Stop `"$run`"" }
    else { Stop-Game $run }
}

$sum = @("run dir: $run", "exit code: $code")
if (Test-Path -LiteralPath $log) {
    $all = (New-Object 'TestGWin+LogTail' -ArgumentList $log, $true).Read()
    $errs = @($all | Where-Object { $_ -match '^\[[^\]]+\] \[(error|critical)\]' }).Count
    $pauses = @($all | Where-Object { $_ -match 'Guest (suspended|resumed) \(\d+ threads\)' })
    $sum += "game.log: $($all.Count) lines, $errs error/critical, $($pauses.Count) pause lines"
    $sum += 'last lines:'
    $sum += @($all | Select-Object -Last 12 | ForEach-Object { '  ' + $_ })
}
Set-Content -LiteralPath (Join-Path $run 'summary.txt') -Value $sum
$sum | ForEach-Object { Write-Host $_ }
exit $code

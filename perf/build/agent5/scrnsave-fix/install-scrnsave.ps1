# install-scrnsave.ps1: Agent 5, task #26. Installs the staged SCRNSAVE.EXE fix (README.md, "Install"). It first checks
# that no window and no night/day launcher is running, that the night launcher ended and put the screensaver back, and
# that the installed files are still the ones the fix was made from. Then it copies new\run-matrix.ps1 to
# bench\agent8\run\ and new\run-night.ps1 + new\README.md to bench\agent5\launch\, and compares the hashes.
# -Check: only the checks, no copy. Log: install-log.txt next to this file (repo-relative paths only).
# Run: powershell -NoProfile -ExecutionPolicy Bypass -File build\agent5\scrnsave-fix\install-scrnsave.ps1 [-Check]
param([switch]$Check)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$Here = $PSScriptRoot
$Repo = (Resolve-Path (Join-Path $Here '..\..\..')).Path
$LogFile = Join-Path $Here 'install-log.txt'
$Items = @(
    [ordered]@{ new = 'new\run-matrix.ps1'; dst = 'bench\agent8\run\run-matrix.ps1'
                before = 'FEDCEB13AB46FE790598EEFD97B5EF5FF545D5D24FADFB3BA03B1CE1CA0CBB89'; after = '1A522CDFE9DC36F8F976D374D020D8EB3102AAB4327BF10BAED31B0F369358CB' },
    [ordered]@{ new = 'new\run-night.ps1'; dst = 'bench\agent5\launch\run-night.ps1'
                before = '16B90FA8654FAC088FE5A1248DE1754918AACC7667A2126AD14723BFBF939B31'; after = '565D30D40DC5025AD63FD9B9F606724BABC167BC81FCB6FBEB6362B603977112' },
    [ordered]@{ new = 'new\README.md'; dst = 'bench\agent5\launch\README.md'
                before = '0058C8F61EEAA9F2529145B034433E2FB67344012D114E4103CE8E3A0EB43274'; after = 'B7CEBD635D847D4CB89D900B9E002B87526D487C971A03A4563EC6807B2A7965' }
)
function Sha([string]$P) { return (Get-FileHash -LiteralPath $P -Algorithm SHA256).Hash }
function Say([string]$M) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $M"
    Write-Host $line
    [IO.File]::AppendAllText($LogFile, $line + "`n", (New-Object Text.UTF8Encoding $false))
}
Say "install-scrnsave.ps1$(if ($Check) { ' -Check' }) starts"
$bad = New-Object System.Collections.Generic.List[string]

# 1. no window, no launcher
if (Test-Path -LiteralPath (Join-Path $Repo 'perf-notes\WINDOW-HOLD.txt')) { $bad.Add('perf-notes\WINDOW-HOLD.txt exists: a window is running') }
$m = $null
if ([System.Threading.Mutex]::TryOpenExisting('Local\Agent5RunNight-real', [ref]$m)) { $m.Dispose(); $bad.Add('Local\Agent5RunNight-real is held: a real night or day launcher is running') }
$procs = @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe' OR Name='pwsh.exe'" | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -and $_.CommandLine -match '(run-night|run-day)\.ps1' })
foreach ($p in $procs) { $bad.Add("a launcher process is running: pid $($p.ProcessId)") }

# 2. the night launcher ended and put the screensaver back
$st = Join-Path $Repo 'bench\agent5\launch\status'
$stateFile = Join-Path $st 'state.txt'; $ssFile = Join-Path $st 'screensaver-saved.txt'
$state = if (Test-Path -LiteralPath $stateFile) { @(Get-Content -LiteralPath $stateFile) } else { @() }
$state0 = if ($state.Count) { [string]$state[0] } else { '(no state.txt)' }
Say "night launcher state: $state0"
if ($state0 -notmatch '^state\s+ended\b') { $bad.Add("bench\agent5\launch\status\state.txt does not say 'ended': $state0") }
if (Test-Path -LiteralPath $ssFile) {
    $ss = @(Get-Content -LiteralPath $ssFile)
    $rl = @($ss | Where-Object { $_ -match '^restored ' })
    Say "screensaver-saved.txt: $($ss -join ' / ')"
    if (-not $rl.Count) { $bad.Add('bench\agent5\launch\status\screensaver-saved.txt has no restored line: the screensaver was not put back') }
} else { Say 'screensaver-saved.txt: none (the launcher never changed the screensaver)' }
$k = Get-Item -LiteralPath 'HKCU:\Control Panel\Desktop'
try {
    $names = @($k.GetValueNames())
    Say "Desktop key now: SCRNSAVE.EXE $(if ($names -contains 'SCRNSAVE.EXE') { "present '$($k.GetValue('SCRNSAVE.EXE'))'" } else { 'absent' }); ScreenSaveActive $(if ($names -contains 'ScreenSaveActive') { $k.GetValue('ScreenSaveActive') } else { 'absent' })"
} finally { $k.Close() }

# 3. the files: staged copies intact, installed copies still the ones the fix was made from
$todo = New-Object System.Collections.Generic.List[object]
foreach ($it in $Items) {
    $src = Join-Path $Here $it.new; $dst = Join-Path $Repo $it.dst
    $hs = Sha $src; $hd = Sha $dst
    if ($hs -ne $it.after) { $bad.Add("$($it.new) has sha256 $hs, not $($it.after)") }
    if ($hd -eq $it.after) { Say "$($it.dst): already installed ($($hd.Substring(0, 8)))" }
    elseif ($hd -eq $it.before) { Say "$($it.dst): $($hd.Substring(0, 8)), to be replaced by $($it.after.Substring(0, 8))"; $todo.Add($it) }
    else { $bad.Add("$($it.dst) has sha256 ${hd}: neither the 'before' $($it.before.Substring(0, 8)) nor the 'after' $($it.after.Substring(0, 8)); somebody changed it") }
}
if ($bad.Count) { foreach ($b in $bad) { Say "REFUSED: $b" }; Say 'nothing was copied'; exit 2 }
if ($Check) { Say "checks OK; $($todo.Count) file(s) would be copied (-Check: nothing copied)"; exit 0 }

# 4. copy and compare
foreach ($it in $todo) {
    Copy-Item -LiteralPath (Join-Path $Here $it.new) -Destination (Join-Path $Repo $it.dst) -Force
    $h = Sha (Join-Path $Repo $it.dst)
    if ($h -ne $it.after) { Say "ERROR: $($it.dst) has sha256 $h after the copy, not $($it.after)"; exit 3 }
    Say "installed $($it.dst): $h"
}
Say "done: $($todo.Count) file(s) copied, all three files have the 'after' hashes"
exit 0

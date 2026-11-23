# holdwatch.ps1 - Agent 3 S4b (task #29) sidecar, started by s4b-queue.ps1 next to attach.ps1 for every launch.
# A user timing window beats a functional run: if perf-notes\WINDOW-HOLD.txt appears while my game runs, this writes
# -Marker (logs\<id>.hold-abort.txt) and then stops the game at once (Stop-Process -Force; WM_CLOSE can't reach the
# hidden desktop from here). The queue records such a run as "aborted":"hold" and runs the row again after the hold.
# Finds the game like attach.ps1: process path under -RunsRoot, started at or after -NotBefore. Ends when the game
# exits. Touches nothing else (no other process, no file but -Marker).
param(
    [string]$RunsRoot = 'build\agent3\runs',
    [string]$NotBefore = '',
    [string]$Marker = '',
    [int]$FindTimeoutSec = 150,
    [int]$PollMs = 500
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
Set-Location $repo
$root = (Resolve-Path $RunsRoot).Path
$hold = Join-Path $repo 'perf-notes\WINDOW-HOLD.txt'
$nb = if ($NotBefore) { [datetime]::Parse($NotBefore) } else { (Get-Date).AddSeconds(-5) }
function Say([string]$m) { Write-Host ((Get-Date -Format 'HH:mm:ss.fff') + ' ' + $m) }

$p = $null
$t0 = Get-Date
while (-not $p -and ((Get-Date) - $t0).TotalSeconds -lt $FindTimeoutSec) {
    $p = Get-Process legodimensions -ErrorAction SilentlyContinue | Where-Object {
        try { $_.Path -like "$root\*" -and $_.StartTime -ge $nb.AddSeconds(-2) } catch { $false } } | Select-Object -First 1
    if (-not $p) { Start-Sleep -Milliseconds 250 }
}
if (-not $p) { Say "holdwatch: no game under $root started after $nb within $FindTimeoutSec s"; exit 1 }
$null = $p.Handle   # keep a handle so WaitForExit works to the end
Say "holdwatch: watching pid $($p.Id) ($($p.Path)) for $hold"
while (-not $p.WaitForExit($PollMs)) {
    if (Test-Path -LiteralPath $hold) {
        Say "holdwatch: $hold exists: stopping pid $($p.Id)"
        if ($Marker) {
            Set-Content -LiteralPath $Marker -Encoding UTF8 -Value ("hold-abort {0} pid {1} {2}" -f (Get-Date -Format 'o'), $p.Id, $p.Path)
        }
        try { Stop-Process -Id $p.Id -Force } catch { Say "holdwatch: Stop-Process failed: $($_.Exception.Message)" }
        if ($p.WaitForExit(20000)) { Say "holdwatch: pid $($p.Id) stopped" } else { Say "holdwatch: pid $($p.Id) STILL RUNNING 20 s after the stop" }
        exit 2
    }
}
Say "holdwatch: pid $($p.Id) exited by itself"
exit 0

# wait-event.ps1 - Agent 3 (run-2 task 2): waits until something in the S4b work changes, prints it and exits, so the
# background command that runs it wakes the agent. Events (checked every 5 s):
#   - new lines in logs\queue.out.txt (s4b-queue.ps1) that matter (DONE, SKIP, ABORTED, DROP, ends, HOLD, ...) or in
#     logs\postcheck.out.txt (checked / p2c / ends); every line since the last report is printed;
#   - a new or re-staged build\agent2\*-bin (its MANIFEST.txt time changes);
#   - the finalized W6 matrix build\agent5\w6-draft\matrix-window6.json appearing or changing;
#   - perf-notes\WINDOW-HOLD.txt appearing or going away;
#   - -Minutes passing (prints a short status).
# What it has reported is kept in logs\wait-event.pos.json, so an event between two runs is reported by the next run at
# once. Read-only apart from that file. -Reset starts from the current state.
param([double]$Minutes = 20, [switch]$Reset)
$ErrorActionPreference = 'SilentlyContinue'
$here = $PSScriptRoot
$repo = (Resolve-Path (Join-Path $here '..\..\..')).Path
Set-Location $repo
$logs = Join-Path $here 'logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$posf = Join-Path $logs 'wait-event.pos.json'
$qf = Join-Path $logs 'queue.out.txt'
$pf = Join-Path $logs 'postcheck.out.txt'
$hold = Join-Path $repo 'perf-notes\WINDOW-HOLD.txt'
$mx = Join-Path $repo 'build\agent5\w6-draft\matrix-window6.json'
$qWake = 'DONE |SKIP |ABORTED|DROP |ends|HOLD|still running|could not|REFUSED|runner is active'
$pWake = 'checked |p2c |ends'
function Lines([string]$p) { if (Test-Path -LiteralPath $p) { @(Get-Content -LiteralPath $p) } else { @() } }
function Bins {
    (@(Get-ChildItem -LiteralPath (Join-Path $repo 'build\agent2') -Directory | Where-Object { $_.Name -like '*-bin' } | ForEach-Object {
                $m = Join-Path $_.FullName 'MANIFEST.txt'
                if (Test-Path -LiteralPath $m) { $_.Name + '@' + (Get-Item -LiteralPath $m).LastWriteTime.ToString('MMdd-HHmmss') } else { $_.Name + '@nomanifest' }
            }) | Sort-Object) -join ' '
}
function Mx { if (Test-Path -LiteralPath $mx) { (Get-Item -LiteralPath $mx).LastWriteTime.ToString('HH:mm:ss') } else { '' } }
function Status {
    $g = @(Get-Process legodimensions -ErrorAction SilentlyContinue | ForEach-Object { "pid $($_.Id) up $([int]((Get-Date) - $_.StartTime).TotalSeconds) s" })
    $fr = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 1)
    "status $(Get-Date -Format 'HH:mm:ss'): game $(if ($g.Count) { $g -join '; ' } else { 'none' }); hold $(Test-Path -LiteralPath $hold); free $fr GB"
}
$pos = $null
if (-not $Reset -and (Test-Path -LiteralPath $posf)) { try { $pos = Get-Content -LiteralPath $posf -Raw | ConvertFrom-Json } catch { $pos = $null } }
if (-not $pos) {
    $pos = [pscustomobject]@{ q = (Lines $qf).Count; p = (Lines $pf).Count; bins = (Bins); mx = (Mx); hold = (Test-Path -LiteralPath $hold) }
    'wait-event: new start; the last lines so far:'
    Lines $qf | Select-Object -Last 4 | ForEach-Object { "  queue: $_" }
    Lines $pf | Select-Object -Last 4 | ForEach-Object { "  post:  $_" }
}
$end = (Get-Date).AddMinutes($Minutes)
while ($true) {
    $why = @()
    $ql = @(Lines $qf); $pl = @(Lines $pf)
    $q0 = [int]$pos.q; if ($ql.Count -lt $q0) { $q0 = 0 }   # the file was started again
    $p0 = [int]$pos.p; if ($pl.Count -lt $p0) { $p0 = 0 }
    $qn = @($ql | Select-Object -Skip $q0); $pn = @($pl | Select-Object -Skip $p0)
    if (@($qn | Where-Object { $_ -match $qWake }).Count) { $why += 'queue' }
    if (@($pn | Where-Object { $_ -match $pWake }).Count) { $why += 'postcheck' }
    $b = Bins; if ($b -ne [string]$pos.bins) { $why += 'bins' }
    $m = Mx; if ($m -ne [string]$pos.mx) { $why += 'w6-matrix' }
    $h = Test-Path -LiteralPath $hold
    if ($h -ne [bool]$pos.hold) { $why += $(if ($h) { 'HOLD PRESENT (no tool calls until Agent 1 resumes)' } else { 'hold gone' }) }
    if (-not $why.Count -and (Get-Date) -ge $end) { $why += "timeout $Minutes min" }
    if ($why.Count) { break }
    Start-Sleep -Seconds 5
}
"EVENT: $($why -join ', ')"
foreach ($l in $qn) { "  queue: $l" }
foreach ($l in $pn) { "  post:  $l" }
if ($b -ne [string]$pos.bins) {
    $old = @(([string]$pos.bins) -split ' ' | Where-Object { $_ }); $new = @($b -split ' ' | Where-Object { $_ })
    "  bins new/changed: $(@($new | Where-Object { $old -notcontains $_ }) -join ' ')"
    $gone = @($old | Where-Object { $new -notcontains $_ }); if ($gone.Count) { "  bins before: $($gone -join ' ')" }
}
if ($m -ne [string]$pos.mx) { "  matrix-window6.json: '$($pos.mx)' -> '$m'" }
Status
[pscustomobject]@{ q = $ql.Count; p = $pl.Count; bins = $b; mx = $m; hold = $h } | ConvertTo-Json -Compress | Set-Content -LiteralPath $posf -Encoding UTF8

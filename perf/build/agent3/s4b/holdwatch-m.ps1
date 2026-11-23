# holdwatch-m.ps1 - Agent 3 run-2 task 2: holdwatch.ps1 for the queue's matrix rows (bench\agent8\run\run-matrix.ps1
# runs several games in a row, each from run-timing.ps1 inside the run-matrix process). If perf-notes\WINDOW-HOLD.txt
# appears: writes -Marker, takes the process tree under -MatrixPid, stops run-matrix first (so no next arm starts),
# then every process of that tree (the game included), then any legodimensions process whose path is under -Root.
# Never touches a game outside that tree / -Root (a timed window's game runs elsewhere). Ends when run-matrix ends.
param(
    [string]$Root = '',
    [string]$Marker = '',
    [int]$MatrixPid = 0,
    [int]$PollMs = 500
)
$ErrorActionPreference = 'Continue'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
Set-Location $repo
$hold = Join-Path $repo 'perf-notes\WINDOW-HOLD.txt'
$rootAbs = if ($Root) { [IO.Path]::GetFullPath((Join-Path $repo $Root)) } else { '' }
function Say([string]$m) { Write-Host ((Get-Date -Format 'HH:mm:ss.fff') + ' ' + $m) }
function Tree([int]$top) {
    $all = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Select-Object ProcessId, ParentProcessId, Name)
    $out = New-Object System.Collections.Generic.List[object]
    $q = New-Object System.Collections.Generic.Queue[int]
    $q.Enqueue($top)
    while ($q.Count) {
        $p = $q.Dequeue()
        foreach ($c in $all) { if ($c.ParentProcessId -eq $p -and $c.ProcessId -ne $p -and $c.ProcessId -ne $top) { $out.Add($c); $q.Enqueue([int]$c.ProcessId) } }
    }
    return $out
}
Say "holdwatch-m: run-matrix pid $MatrixPid; games under $rootAbs"
while ($true) {
    $mp = if ($MatrixPid) { Get-Process -Id $MatrixPid -ErrorAction SilentlyContinue } else { $null }
    if (Test-Path -LiteralPath $hold) {
        if ($Marker -and -not (Test-Path -LiteralPath $Marker)) {
            Set-Content -LiteralPath $Marker -Encoding UTF8 -Value ('hold-abort {0} run-matrix pid {1} root {2}' -f (Get-Date -Format 'o'), $MatrixPid, $rootAbs)
        }
        $kids = if ($MatrixPid) { @(Tree $MatrixPid) } else { @() }
        if ($mp) { Say "HOLD: stopping run-matrix pid $MatrixPid"; try { Stop-Process -Id $MatrixPid -Force } catch { Say "  failed: $($_.Exception.Message)" } }
        foreach ($k in $kids) {
            if (Get-Process -Id $k.ProcessId -ErrorAction SilentlyContinue) {
                Say "HOLD: stopping pid $($k.ProcessId) $($k.Name) (run-matrix tree)"; try { Stop-Process -Id $k.ProcessId -Force } catch { }
            }
        }
        if ($rootAbs) {
            Get-Process legodimensions -ErrorAction SilentlyContinue | Where-Object { try { $_.Path -like "$rootAbs\*" } catch { $false } } |
                ForEach-Object { Say "HOLD: stopping game pid $($_.Id) $($_.Path)"; try { Stop-Process -Id $_.Id -Force } catch { } }
        }
        if (-not $mp) { Say 'holdwatch-m: run-matrix stopped'; exit 2 }
    } elseif ($MatrixPid -and -not $mp) {
        Say 'holdwatch-m: run-matrix ended by itself'; exit 0
    }
    Start-Sleep -Milliseconds $PollMs
}

# s4a-queue.ps1 - Agent 3 S4a (task #5) sequential game queue. FUNCTIONAL ONLY (run-game.ps1 = hidden desktop).
# Reads build\agent3\s4a\queue.jsonl, one JSON object per line ('#' lines ignored):
#   {"id":"r1","est":260,"needs":"build\\agent2\\devoff4-bin","args":["-BinDir","...","-Seconds","420","-Tag","..."]}
# and runs the first entry that is not yet in queue-state.jsonl and whose "needs" path exists (entries whose bin is
# not there yet are passed over, not dropped). One game at a time; each run gets the attach.ps1 sidecar
# (sys.csv via Agent 8's sys-csv.ps1 if its DLL is cached, threads-s4a.csv). Never launches at or after -LastLaunch,
# nor when now + est would pass -GamesClosed (such an entry is recorded as skipped). A STOP file next to this script
# ends the queue before the next launch. With nothing runnable it polls every 5 s until -LastLaunch.
param(
    [string]$LastLaunch = '14:45:00',
    [string]$GamesClosed = '14:49:30'
)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$repo = (Resolve-Path (Join-Path $here '..\..\..')).Path
Set-Location $repo
$queue = Join-Path $here 'queue.jsonl'
$state = Join-Path $here 'queue-state.jsonl'
$stop = Join-Path $here 'STOP'
$logs = Join-Path $here 'logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$runsRoot = Join-Path $repo 'build\agent3\runs'
function Say([string]$m) { Write-Host ((Get-Date -Format 'HH:mm:ss') + ' ' + $m) }
function Rec($o) { Add-Content -LiteralPath $state -Value ($o | ConvertTo-Json -Compress -Depth 5) -Encoding UTF8 }
$ll = [datetime]::Today.Add([timespan]::Parse($LastLaunch))
$gc = [datetime]::Today.Add([timespan]::Parse($GamesClosed))
$lastWait = ''
while ($true) {
    if (Test-Path -LiteralPath $stop) { Say 'STOP file: queue ends'; break }
    $now = Get-Date
    if ($now -ge $ll) { Say "past the last launch $LastLaunch`: queue ends"; break }
    $done = @()
    if (Test-Path -LiteralPath $state) { $done = @(Get-Content -LiteralPath $state | Where-Object { $_.Trim() } | ForEach-Object { ($_ | ConvertFrom-Json).id }) }
    $next = $null; $waiting = @()
    if (Test-Path -LiteralPath $queue) {
        foreach ($line in Get-Content -LiteralPath $queue) {
            $t = $line.Trim(); if (-not $t -or $t.StartsWith('#')) { continue }
            $e = $t | ConvertFrom-Json
            if ($done -contains $e.id) { continue }
            if ($e.unless -and (Test-Path -LiteralPath (Join-Path $repo $e.unless))) {
                Say "DROP $($e.id): $($e.unless) exists"; Rec ([ordered]@{ id = $e.id; skipped = "unless $($e.unless)"; at = $now.ToString('HH:mm:ss') })
                $done += $e.id; continue
            }
            if ($e.needs -and -not (Test-Path -LiteralPath (Join-Path $repo $e.needs))) { $waiting += $e.id; continue }
            $next = $e; break
        }
    }
    if (-not $next) {
        $w = $waiting -join ','
        if ($w -ne $lastWait) { Say "idle; waiting for bins: [$w]"; $lastWait = $w }
        Start-Sleep -Seconds 5; continue
    }
    if ($now.AddSeconds([double]$next.est) -gt $gc) {
        Say "SKIP $($next.id): est $($next.est) s would end after $GamesClosed"
        Rec ([ordered]@{ id = $next.id; skipped = "est $($next.est) s past $GamesClosed"; at = $now.ToString('HH:mm:ss') }); continue
    }
    if (Get-Process legodimensions -ErrorAction SilentlyContinue) {
        if ($lastWait -ne 'game') { Say "a game is running; waiting (next: $($next.id))"; $lastWait = 'game' }
        Start-Sleep -Seconds 3; continue
    }
    $lastWait = ''
    $a = @($next.args | ForEach-Object { [string]$_ })
    $ti = [array]::IndexOf($a, '-Tag'); $tag = if ($ti -ge 0) { $a[$ti + 1] } else { 'run' }
    $t0 = Get-Date
    Say "LAUNCH $($next.id): run-game $($a -join ' ')"
    $side = Start-Process powershell -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $logs "$($next.id).attach.out.txt") `
        -RedirectStandardError (Join-Path $logs "$($next.id).attach.err.txt") `
        -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $here 'attach.ps1'), '-NotBefore', $t0.ToString('o'))
    # 'Continue' for the call: native builds print to stderr ("Plume D3D12 command state cache: disabled"), the game
    # inherits run-game's stderr, and with 'Stop' that first stderr line was a terminating NativeCommandError that
    # killed run-game at 14 s and left the game orphaned (r5 attempt 1, 13:52).
    $ErrorActionPreference = 'Continue'
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo 'harness\run-game.ps1') @a *> (Join-Path $logs "$($next.id).run-game.txt")
    $ec = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if (-not $side.WaitForExit(90000)) { Say "attach for $($next.id) still running 90 s after run-game; killing it"; try { $side.Kill() } catch { } }
    $rd = Get-ChildItem -LiteralPath $runsRoot -Directory | Where-Object { $_.Name -like "*-$tag*" -and $_.CreationTime -ge $t0.AddSeconds(-2) } |
        Sort-Object CreationTime | Select-Object -Last 1
    $t1 = Get-Date
    $rn = if ($rd) { $rd.Name } else { $null }
    Say ("DONE {0}: exit {1} in {2:0} s, run {3}" -f $next.id, $ec, ($t1 - $t0).TotalSeconds, $rn)
    Rec ([ordered]@{ id = $next.id; exit = $ec; run = $rn; start = $t0.ToString('HH:mm:ss'); end = $t1.ToString('HH:mm:ss'); args = $a })
}

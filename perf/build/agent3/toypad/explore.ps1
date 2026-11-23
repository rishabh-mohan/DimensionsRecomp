# explore.ps1 - Agent 3, run-2 task 2: ONE level-route exploration run with the virtual starter tags.
# Agent 1 OK (19:42): 1-3 runs on build\agent2\devoff4-bin (S4a PASS bin, unchanged) before the S4b bins land; hidden
# desktop (harness\run-game.ps1), one game at a time, FUNCTIONAL ONLY, <= ~15 min per run, start only with >= 6 GB RAM
# free; tags through 9191 under decision 1 (memory only, path length 0); saves in <run>\user; holdwatch on.
# Beside run-game: build\agent3\s4b\holdwatch.ps1 (stops the game if perf-notes\WINDOW-HOLD.txt appears) and
# toypad_sidecar.py (places the tags on the trigger, logs <run>\toypad-events.csv). Logs: build\agent3\toypad\logs\.
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent3\toypad\explore.ps1 -Tag lx1-devoff4
param(
    [string]$BinDir = 'build\agent2\devoff4-bin',
    [string]$Route = 'build\agent3\toypad\routes\level-explore-1.txt',
    [int]$Seconds = 780,
    [string]$Tag = 'lx1-devoff4',
    [string]$TriggerMark = '',
    [double]$Delay = 2,
    [string]$ThenMark = '',            # sidecar --then-mark: an input.csv mark after which it acts again
    [double]$ThenDelay = 3,
    [string]$ThenAction = 'replace',   # replace (REMOVE the 3 tags, then LOAD them again) | remove | place
    [double]$MinFreeGB = 6
)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$repo = (Resolve-Path (Join-Path $here '..\..\..')).Path
Set-Location $repo
function Say([string]$m) { Write-Host ((Get-Date -Format 'HH:mm:ss') + ' ' + $m) }
if (Test-Path -LiteralPath (Join-Path $repo 'perf-notes\WINDOW-HOLD.txt')) { Say 'HOLD PRESENT: no launch'; exit 3 }
if (Get-Process legodimensions -ErrorAction SilentlyContinue) { Say 'a game is running: no launch'; exit 3 }
$free = (Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB
if ($free -lt $MinFreeGB) { Say ("only {0:0.00} GB RAM free (< {1}): no launch" -f $free, $MinFreeGB); exit 3 }
foreach ($p in @($BinDir, $Route)) { if (-not (Test-Path -LiteralPath $p)) { Say "missing $p"; exit 2 } }
$logs = Join-Path $here 'logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$t0 = Get-Date
$st = $t0.ToString('HHmmss')
$base = Join-Path $logs "$Tag.$st"
$marker = "$base.hold-abort.txt"
$hw = Start-Process powershell -NoNewWindow -PassThru -RedirectStandardOutput "$base.holdwatch.out.txt" `
    -RedirectStandardError "$base.holdwatch.err.txt" `
    -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $repo 'build\agent3\s4b\holdwatch.ps1'),
        '-NotBefore', $t0.ToString('o'), '-Marker', $marker)
$sa = @((Join-Path $here 'toypad_sidecar.py'), '--runs-root', 'build\agent3\runs', '--tag', $Tag,
    '--not-before', $t0.ToString('o'), '--timeout', [string]($Seconds + 240), '--delay', [string]$Delay)
if ($TriggerMark) { $sa += @('--trigger-mark', $TriggerMark, '--trigger-log', '""') }
if ($ThenMark) { $sa += @('--then-mark', $ThenMark, '--then-delay', [string]$ThenDelay, '--then-action', $ThenAction) }
$tp = Start-Process python -NoNewWindow -PassThru -RedirectStandardOutput "$base.sidecar.out.txt" `
    -RedirectStandardError "$base.sidecar.err.txt" -ArgumentList $sa
$null = $tp.Handle   # keeps the handle so ExitCode is readable after the exit (lx1 printed an empty one)
Say ("LAUNCH {0}: {1}, {2}, {3} s, {4:0.0} GB free" -f $Tag, $BinDir, $Route, $Seconds, $free)
$ErrorActionPreference = 'Continue'
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repo 'harness\run-game.ps1') -BinDir $BinDir `
    -Seconds $Seconds -Tag $Tag -InputScript $Route *> "$base.run-game.txt"
$ec = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if (-not $tp.WaitForExit(240000)) { Say 'sidecar still running 240 s after run-game; killing it'; try { $tp.Kill() } catch { } }
if (-not $hw.WaitForExit(30000)) { Say 'holdwatch still running 30 s after run-game; killing it'; try { $hw.Kill() } catch { } }
$rd = Get-ChildItem -LiteralPath (Join-Path $repo 'build\agent3\runs') -Directory |
    Where-Object { $_.Name -like "*-$Tag*" -and $_.CreationTime -ge $t0.AddSeconds(-2) } | Sort-Object CreationTime | Select-Object -Last 1
Say ("DONE {0}: run-game exit {1}, sidecar exit {2}, run {3}, hold-abort {4}, {5:0} s" -f $Tag, $ec, $tp.ExitCode,
    $(if ($rd) { $rd.Name } else { '-' }), (Test-Path -LiteralPath $marker), ((Get-Date) - $t0).TotalSeconds)

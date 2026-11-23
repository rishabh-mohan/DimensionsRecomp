# Agent 3: pad host reuse in ONE PowerShell process (what run-matrix.ps1 does with run-timing.ps1). Loads the given
# vpadhost source, runs a 7-step mini script twice (no game: the state file is just a file), then calls the patched
# runner in-process. Original vpadhost.cs: run 2 runs no steps and the runner refuses (exit 1). Reset patch: run 2 =
# run 1 and the runner passes its input checks (exit 3 at the RAM check; nothing is created).
param([Parameter(Mandatory = $true)][string]$VpadSrc, [Parameter(Mandatory = $true)][string]$Label)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
Set-Location $root
Add-Type -Path (Join-Path $root $VpadSrc)
$d = Join-Path $root 'build\agent3\test\vpadreset'
New-Item -ItemType Directory -Force -Path $d | Out-Null
$mini = Join-Path $d 'mini.txt'
Set-Content -LiteralPath $mini -Encoding ascii -Value @('mark one', 'press A 1 50 50', 'sleep 0.3', 'mark two', 'stop', 'sleep 5', 'mark never')
foreach ($r in 1..2) {
    $csv = Join-Path $d "input-$Label-$r.csv"
    $e = [Agent3Input]::Start($mini, (Join-Path $d "state-$Label-$r.bin"), $csv, (Join-Path $d 'none.log'), (Join-Path $d 'none.csv'))
    if ($e) { "$Label run $r START ERROR: $e"; continue }
    [Agent3Input]::Go(0)
    $sw = [Diagnostics.Stopwatch]::StartNew()
    while (-not [Agent3Input]::StopRequested -and $sw.Elapsed.TotalSeconds -lt 10) { Start-Sleep -Milliseconds 50 }
    Start-Sleep -Milliseconds 200
    [Agent3Input]::Halt()
    $f = [Agent3Input]::Finish()
    "$Label run $r : steps_done $($f['steps_done'])/$($f['steps_total']) last '$($f['last_step'])' stop $($f['stopped_by_script']) timeouts $($f['timeouts']) error '$($f['error'])' input.csv lines $(@(Get-Content -LiteralPath $csv).Count) after $([math]::Round($sw.Elapsed.TotalSeconds, 2)) s"
}
$runner = Join-Path $root 'build\agent3\rtpatch\run-timing.ps1'
$global:LASTEXITCODE = $null
$out = & $runner -BinDir 'build\agent3\test\fakebin2' -InputScript 'harness\routes\attract-long.txt' -MinFreeRamGB 999 -RunsRoot 'build\agent3\test\rtruns' -Tag 'rtpatch-test' 2>&1 | Out-String
"$Label runner after 2 runs in this process: exit $LASTEXITCODE :: $(($out.Trim() -replace '\s*\r?\n\s*', ' | '))"

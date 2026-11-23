# slowstate.ps1 - adapter for Agent 11's bench\agent11\timerq_slowstate.ps1 (unchanged, read-only use).
# That script scans <Root>/<yyyyMMdd-HHmm>/runs/<run>/{sys.csv,run.json} and needs run.json fields
# ff_signal_epoch_s and env_set. run-game.ps1 run dirs have started_epoch_s (run.json) and
# first_frame_s (summary.json) instead, so this copies sys.csv (source untouched) into
# build\agent3\s4a\slowstate\<yyyyMMdd-HHmm>\runs\<run>\ with a small run.json, then runs the script.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File build\agent3\s4a\slowstate.ps1 [-Since 20261122-1300] [-Runs dir1,dir2]
[CmdletBinding()]
param(
    [string]$Since = '20261122-1300',
    [string[]]$Runs = @(),
    [string]$RunsRoot = 'build\agent3\runs',
    [string]$Out = 'build\agent3\s4a\slowstate'
)
$ErrorActionPreference = 'Stop'
if ($Runs.Count -eq 0) {
    $Runs = @(Get-ChildItem -LiteralPath $RunsRoot -Directory |
        Where-Object { $_.Name -match '^\d{8}-\d{6}-' -and $_.Name.Substring(0, 13) -ge $Since } |
        Sort-Object Name | ForEach-Object { $_.FullName })
}
foreach ($r in $Runs) {
    $name = Split-Path -Leaf $r
    $sys = Join-Path $r 'sys.csv'; $rj = Join-Path $r 'run.json'; $sj = Join-Path $r 'summary.json'
    if (-not (Test-Path -LiteralPath $sys) -or -not (Test-Path -LiteralPath $rj) -or -not (Test-Path -LiteralPath $sj)) {
        Write-Host "skip $name (needs sys.csv, run.json, summary.json)"; continue
    }
    $j = Get-Content -LiteralPath $rj -Raw | ConvertFrom-Json
    $s = Get-Content -LiteralPath $sj -Raw | ConvertFrom-Json
    if ($null -eq $s.first_frame_s -or $null -eq $j.started_epoch_s) { Write-Host "skip $name (no first frame)"; continue }
    $dst = Join-Path (Join-Path (Join-Path $Out $name.Substring(0, 13)) 'runs') $name
    New-Item -ItemType Directory -Force -Path $dst | Out-Null
    Copy-Item -LiteralPath $sys -Destination (Join-Path $dst 'sys.csv') -Force
    [pscustomobject]@{
        ff_signal_epoch_s = [double]$j.started_epoch_s + [double]$s.first_frame_s
        env_set = $j.env
        source = $r
    } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $dst 'run.json') -Encoding UTF8
}
& powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_slowstate.ps1 -Root $Out -Since $Since

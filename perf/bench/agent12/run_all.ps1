# bench/agent12/run_all.ps1 -- build and run every Agent 12 test/bench sequentially.
# Logs go to build/agent12/bench/logs/<name>.md (stdout) and <name>.err (stderr).
# At most 2 threads at a time; ~7-8 min wall on the loaded shared machine (B1 ~2.5 min).
#
#   powershell -ExecutionPolicy Bypass -File bench/agent12/run_all.ps1 [-NoBuild] [-Only t1,t2,b1,b2,b3,b4,b5,b5abl] [-Tag run2]
param(
    [switch]$NoBuild,
    [string[]]$Only = @('t1', 't2', 'b1', 'b4', 'b2', 'b3', 'b5', 'b5abl'),
    [string]$Tag = 'all'
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$bin  = Join-Path $root 'build\agent12\bench'
$logs = Join-Path $bin 'logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null

if (-not $NoBuild) {
    & powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'build.ps1')
    if ($LASTEXITCODE -ne 0) { throw 'run_all: build failed' }
}

$jobs = [ordered]@{
    't1'    = @('t1_scatter_test.exe', '6000 0x7E57AB1E')
    't2'    = @('t2_watch_test.exe', '')
    'b1'    = @('b1_scatter.exe', '256 5 all')
    'b4'    = @('b4_samefile.exe', '5 128')
    'b2'    = @('b2_watch.exe', '5 100000')
    'b3'    = @('b3_open.exe', '5 1000 3')
    'b5'    = @('b5_log.exe', '5 100000000')
    'b5abl' = @('b5_log.exe', '5 100000000 ablate')
}
$failed = @()
foreach ($k in $jobs.Keys) {
    if ($Only -notcontains $k) { continue }
    $exe, $args_ = $jobs[$k]
    $out = Join-Path $logs "${k}_$Tag.md"
    $err = Join-Path $logs "${k}_$Tag.err"
    $sw = [Diagnostics.Stopwatch]::StartNew()
    cmd /c "`"$(Join-Path $bin $exe)`" $args_ > `"$out`" 2> `"$err`""
    $code = $LASTEXITCODE
    Write-Host ("[run] {0}: exit={1} ({2:N0}s) -> {3}" -f $k, $code, $sw.Elapsed.TotalSeconds, $out)
    if ($code -ne 0) { $failed += $k }
}
if ($failed.Count) { Write-Host "[run] FAILED: $($failed -join ' ')"; exit 1 }
Write-Host '[run] all OK'

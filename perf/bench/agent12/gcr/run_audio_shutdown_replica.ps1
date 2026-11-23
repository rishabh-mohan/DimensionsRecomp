# Task #22 (Agent 12): runs the audio shutdown replica (audio_shutdown_replica.cpp), old vs new path.
# Build first: bench\agent12\gcr\build_audio_shutdown_replica.cmd
# Usage: powershell -NoProfile -File bench\agent12\gcr\run_audio_shutdown_replica.ps1 -Cases "new h,old h" -Runs 1000
# -Cases is one string (powershell -File does not parse arrays): comma-separated "<old|new> <h|p|b>" pairs.
# One parent at a time; the parent runs at most -Parallel (<=2) children at once, so at most 2 busy threads.
# The full output of each case goes to build\agent12\gcr\audio_shutdown_replica.<mode>_<scenario>.log.
# The parent's RESULT line is authoritative: a child that hangs is ended by the parent, and its buffered
# stdout lines can be lost.
param(
    [string]$Cases = 'new h,old h',
    [int]$Runs = 1000,
    [int]$Parallel = 2
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$exe = Join-Path $root 'build\agent12\gcr\audio_shutdown_replica.exe'
$out = Join-Path $root 'build\agent12\gcr'
if (-not (Test-Path -LiteralPath $exe)) { Write-Output "missing $exe (run build_audio_shutdown_replica.cmd)"; exit 2 }
if ($Parallel -gt 2) { $Parallel = 2 }
Write-Output ("exe {0} sha256={1}" -f $exe, (Get-FileHash -LiteralPath $exe).Hash)
foreach ($c in ($Cases -split ',')) {
    $mode, $scn = $c.Trim() -split '\s+'
    if ($mode -notin @('old', 'new') -or $scn -notin @('h', 'p', 'b')) { Write-Output "bad case '$c'"; exit 2 }
    $log = Join-Path $out ("audio_shutdown_replica.{0}_{1}.log" -f $mode, $scn)
    $load = (Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average
    $t0 = Get-Date
    Write-Output ("{0} start {1} {2} runs={3} parallel={4} machine_cpu_load={5}%" -f $t0.ToString('HH:mm:ss'), $mode, $scn, $Runs, $Parallel, $load)
    cmd /c "`"$exe`" $mode $scn $Runs $Parallel > `"$log`" 2>&1"
    $rc = $LASTEXITCODE
    $res = Select-String -LiteralPath $log -Pattern '^RESULT' | Select-Object -Last 1
    $load2 = (Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average
    Write-Output ("{0} done {1} {2} rc={3} {4:0}s machine_cpu_load_end={5}% :: {6}" -f (Get-Date).ToString('HH:mm:ss'), $mode, $scn, $rc, ((Get-Date) - $t0).TotalSeconds, $load2, $(if ($res) { $res.Line } else { 'NO RESULT LINE' }))
}

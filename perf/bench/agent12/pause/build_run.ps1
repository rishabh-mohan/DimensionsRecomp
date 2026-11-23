# bench/agent12/pause/build_run.ps1 -- build and run the SetGuestPaused ordering replica (task #17).
#
#   powershell -ExecutionPolicy Bypass -File bench/agent12/pause/build_run.ps1 [-Runs 5] [-Cycles 1000]
#        [-MaxSeconds 20] [-Modes old,new,guard] [-Extra "g_us=40 free_us=400"] [-BuildOnly]
#
# Same compiler and flags as bench/agent12/build.ps1 (clang-cl from env/devshell.ps1, /O2).
# Outputs: build/agent12/pause/{pause_stress.exe, build.log, runs.csv, summary.md}.
# Modes are interleaved inside each run round; CPU load is sampled before every run.
param(
    [int]$Runs = 5,
    [int]$Cycles = 1000,
    [int]$MaxSeconds = 20,
    [string[]]$Modes = @('old', 'new', 'guard'),
    [string]$Extra = '',
    [switch]$BuildOnly,
    [switch]$NoBuild
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$out = Join-Path $root 'build\agent12\pause'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$exe = Join-Path $out 'pause_stress.exe'

if (-not $NoBuild) {
    Push-Location $root
    try { . .\env\devshell.ps1 -Quiet } finally { Pop-Location }
    $cc = (Get-Command clang-cl).Source
    Write-Host "[build] compiler: $cc"
    $cl = @('/nologo', '/O2', '-march=x86-64-v2', '/std:c++latest', '/EHsc', '/MD', '/W3',
        '/DNOMINMAX', '/DWIN32_LEAN_AND_MEAN', '/D_CRT_SECURE_NO_WARNINGS', '-fuse-ld=lld',
        (Join-Path $PSScriptRoot 'pause_stress.cpp'), "/Fo$out\", "/Fe$exe")
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $ErrorActionPreference = 'Continue'   # clang-cl warnings on stderr must not throw
    $o = & clang-cl @cl 2>&1 | ForEach-Object { "$_" }
    $code = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    (@("compiler: $cc") + $o) | Out-File -FilePath (Join-Path $out 'build.log') -Encoding utf8
    if ($o) { $o | Out-Host }
    Write-Host ("[build] pause_stress: exit={0} ({1:N1}s)" -f $code, $sw.Elapsed.TotalSeconds)
    if ($code -ne 0) { exit 1 }
}
if ($BuildOnly) { return }

$rows = New-Object System.Collections.Generic.List[object]
for ($r = 1; $r -le $Runs; $r++) {
    foreach ($m in $Modes) {
        $load = (Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average
        $a = @("mode=$m", "cycles=$Cycles", "seed=$r", "max_s=$MaxSeconds") + @($Extra -split ' ' | Where-Object { $_ })
        $line = & $exe @a | Where-Object { $_ -like 'RESULT *' } | Select-Object -Last 1
        if (-not $line) { throw "no RESULT line from mode=$m run=$r" }
        $h = [ordered]@{ run = $r; load_pct = $load }
        foreach ($kv in ($line -replace '^RESULT ', '') -split ' ') {
            $k, $v = $kv -split '=', 2
            $h[$k] = $v
        }
        $obj = [pscustomobject]$h
        $rows.Add($obj)
        Write-Host ("[run {0}] load={1,3}% {2}" -f $r, $load, $line)
    }
}
$csv = Join-Path $out 'runs.csv'
$rows | Export-Csv -NoTypeInformation -Path $csv
Write-Host "[run] wrote $csv"

function Stat([double[]]$v) {
    $s = $v | Sort-Object
    $med = if ($s.Count % 2) { $s[[int][math]::Floor($s.Count / 2)] } else { ($s[$s.Count / 2 - 1] + $s[$s.Count / 2]) / 2 }
    '{0:N1} [{1:N1}-{2:N1}]' -f $med, $s[0], $s[-1]
}
function Med([double[]]$v) {
    $s = $v | Sort-Object
    if ($s.Count % 2) { $s[[int][math]::Floor($s.Count / 2)] } else { ($s[$s.Count / 2 - 1] + $s[$s.Count / 2]) / 2 }
}
$steps = @('audio_fence', 'sink', 'heap', 'T', 'suspend', 'pre', 'resume')
$md = New-Object System.Collections.Generic.List[string]
$md.Add('Hangs per 1000 cycles: median [min-max] over runs')
$md.Add('')
$md.Add('| mode | runs | cycles/run (med) | hang cycles | ' + (($steps | ForEach-Object { $_ }) -join ' | ') + ' | load % (med) |')
$md.Add('|---|---|---|---|' + (($steps | ForEach-Object { '---' }) -join '|') + '|---|')
foreach ($m in $Modes) {
    $mr = @($rows | Where-Object { $_.mode -eq $m })
    if (-not $mr.Count) { continue }
    $cells = @($m, $mr.Count, (Med ($mr | ForEach-Object { [double]$_.cycles })),
        (Stat ($mr | ForEach-Object { 1000.0 * [double]$_.hang_cycles / [double]$_.cycles })))
    foreach ($s in $steps) { $cells += (Stat ($mr | ForEach-Object { 1000.0 * [double]$_."h_$s" / [double]$_.cycles })) }
    $cells += (Med ($mr | ForEach-Object { [double]$_.load_pct }))
    $md.Add('| ' + ($cells -join ' | ') + ' |')
}
$md.Add('')
$md.Add('UI-step latency, non-hang cycles, us: median [min-max] over runs of the per-run percentile')
$md.Add('')
$md.Add('| mode | pause p50 | pause p99 | pause max | unpause p50 | unpause p99 | unpause max | guest iters/s | audio ticks/s | run s |')
$md.Add('|---|---|---|---|---|---|---|---|---|---|')
foreach ($m in $Modes) {
    $mr = @($rows | Where-Object { $_.mode -eq $m })
    if (-not $mr.Count) { continue }
    $cells = @($m)
    foreach ($f in 'pause_p50_us', 'pause_p99_us', 'pause_max_us', 'unpause_p50_us', 'unpause_p99_us', 'unpause_max_us', 'guest_iters_per_s', 'audio_ticks_per_s', 'elapsed_s') {
        $cells += (Stat ($mr | ForEach-Object { [double]$_.$f }))
    }
    $md.Add('| ' + ($cells -join ' | ') + ' |')
}
$sum = Join-Path $out 'summary.md'
$md | Out-File -FilePath $sum -Encoding utf8
$md | Out-Host
Write-Host "[run] wrote $sum"

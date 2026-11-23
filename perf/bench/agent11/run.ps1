# run.ps1 - helper A's agent11 micro-benchmarks (see README.md).
# Optionally builds, then runs each bench in turn (never two at once; the
# BenchSerializer mutex in bench_common.h also serializes against helper B),
# logging to build\agent11\a\<bench>.txt behind an AC/CPU-load header.
#   powershell -NoProfile -File bench\agent11\run.ps1 [-Build] [-Bench bench_sleep,bench_clock] [-Runs 5]
param(
  [switch]$Build,
  [string[]]$Bench = @('bench_sleep', 'timer_highres_check', 'bench_clock', 'bench_waitsignal', 'bench_lookup'),
  [int]$Runs = 5
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$out = Join-Path $root 'build\agent11\a'
New-Item -ItemType Directory -Force -Path $out | Out-Null
Set-Location $root

if ($Build) {
  . (Join-Path $root 'env\devshell.ps1') -Quiet
  foreach ($b in $Bench) {
    $o = & cl /nologo /O2 /std:c++20 /EHsc /W3 "bench\agent11\$b.cpp" "/Fe:build\agent11\a\$b.exe" "/Fo:build\agent11\a\" winmm.lib 2>&1
    if ($LASTEXITCODE -ne 0) { $o | Write-Host; throw "build failed: $b" }
    Write-Host "built $b"
  }
}

$cpuTotal = 0.0
foreach ($b in $Bench) {
  $exe = Join-Path $out "$b.exe"
  $log = Join-Path $out "$b.txt"
  $bat = Get-CimInstance Win32_Battery | Select-Object -First 1
  $load = (Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average
  $hdr = '# {0}  {1:yyyy-MM-dd HH:mm:ss}  BatteryStatus={2} (2 = AC)  charge={3}%  CPU LoadPercentage={4}%  args: {5}' -f `
    $b, (Get-Date), $bat.BatteryStatus, $bat.EstimatedChargeRemaining, $load, $Runs
  Set-Content -Path $log -Value $hdr -Encoding ascii
  $so = "$log.stdout"; $se = "$log.stderr"
  $sw = [Diagnostics.Stopwatch]::StartNew()
  $p = Start-Process -FilePath $exe -ArgumentList "$Runs" -NoNewWindow -PassThru `
    -RedirectStandardOutput $so -RedirectStandardError $se
  $null = $p.Handle  # keep the handle so ExitCode/TotalProcessorTime survive exit
  $p.WaitForExit()
  $cpu = $p.TotalProcessorTime.TotalSeconds
  $cpuTotal += $cpu
  Get-Content $so | Add-Content -Path $log -Encoding ascii
  if ((Get-Item $se).Length -gt 0) { Get-Content $se | ForEach-Object { "[stderr] $_" } | Add-Content -Path $log -Encoding ascii }
  Remove-Item $so, $se -ErrorAction SilentlyContinue
  $tail = '# exit={0} wall={1:N1}s cpu={2:N1}s' -f $p.ExitCode, $sw.Elapsed.TotalSeconds, $cpu
  Add-Content -Path $log -Value $tail -Encoding ascii
  Write-Host ('{0}: {1} -> {2}' -f $b, $tail.TrimStart('# '), $log)
}
Write-Host ('total bench CPU time {0:N1} s' -f $cpuTotal)

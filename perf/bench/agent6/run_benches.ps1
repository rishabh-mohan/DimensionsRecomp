# Agent 6, task #5: build and run the CPU-only benches and tests in bench/agent6.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File bench/agent6/run_benches.ps1 [-Only a,b] [-NoRun] [-BenchArgs '...']
# Each bench is one .cpp that includes headers from DimensionsRecomp/rexlego/src. Output goes to build/agent6/bench
# (exe plus <name>.txt with the run log). Single clang process at a time; each bench uses at most 2 threads.
param([string[]]$Only = @(), [switch]$NoRun, [string]$BenchArgs = '')
$ErrorActionPreference = 'Stop'
# powershell -File passes "-Only a,b" as one string, so split on commas here.
$Only = @($Only | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$root = (Resolve-Path "$PSScriptRoot\..\..").Path
. "$root\env\devshell.ps1" | Out-Null
$src = "$root\DimensionsRecomp\rexlego\src"
$out = "$root\build\agent6\bench"
New-Item -ItemType Directory -Force $out | Out-Null
$benches = @('save_lock_hold', 'stats_off_cost', 'prepare_order_test', 'async_table_test')
$failed = @()
foreach ($name in $benches) {
  if ($Only.Count -and ($Only -notcontains $name)) { continue }
  $cpp = "$PSScriptRoot\$name.cpp"
  if (-not (Test-Path $cpp)) { Write-Host "skip $name (no source yet)"; continue }
  # include\rex\logging.h stands in for the SDK logger (captures REXLOG lines for the tests).
  & clang++ --target=x86_64-pc-windows-msvc -std=c++23 -O2 -DNOMINMAX -DWIN32_LEAN_AND_MEAN -D_CRT_SECURE_NO_WARNINGS `
      -Wall -Wextra "-I$PSScriptRoot\include" "-I$src" $cpp -o "$out\$name.exe"
  if ($LASTEXITCODE) { throw "compile failed: $name" }
  if ($NoRun) { continue }
  $runArgs = @()
  if ($BenchArgs) { $runArgs = $BenchArgs -split ' ' }
  & "$out\$name.exe" @runArgs 2>&1 | Tee-Object -FilePath "$out\$name.txt"
  if ($LASTEXITCODE) { $failed += $name }
}
if ($failed.Count) { Write-Host "FAILED: $($failed -join ', ')"; exit 1 }
Write-Host 'benches OK'

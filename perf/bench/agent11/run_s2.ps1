# run_s2.ps1 - Agent 11 session-2 bench run (no CIM/WMI queries; each bench prints AC and CPU load itself).
# Runs helper A's prebuilt benches one after another (at most 2 threads each), median of 5 runs inside each exe.
#   powershell -NoProfile -File bench\agent11\run_s2.ps1 [-Only bench_sleep,bench_clock]
param([string[]]$Only = @())
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $root
$out = 'build\agent11\a'
$jobs = @(
  @('bench_sleep', @('5', '40')),
  @('timer_highres_check', @('5')),
  @('bench_clock', @('5')),
  @('bench_waitsignal', @('5', '3')),
  @('bench_lookup', @('5', '100000'))
)
foreach ($j in $jobs) {
  $name = $j[0]; $argv = $j[1]
  if ($Only.Count -gt 0 -and -not ($Only -contains $name)) { continue }
  $exe = Join-Path $out "$name.exe"
  $log = Join-Path $out "$name.txt"
  ('# {0}  {1:yyyy-MM-dd HH:mm:ss}  args: {2}' -f $name, (Get-Date), ($argv -join ' ')) | Set-Content -Path $log -Encoding ascii
  $sw = [Diagnostics.Stopwatch]::StartNew()
  & $exe @argv 2>&1 | ForEach-Object { "$_" } | Add-Content -Path $log -Encoding ascii
  $ec = $LASTEXITCODE
  ('# exit={0} wall={1:N0}s' -f $ec, $sw.Elapsed.TotalSeconds) | Add-Content -Path $log -Encoding ascii
  Write-Host ('{0} exit={1} wall={2:N0}s -> {3}' -f $name, $ec, $sw.Elapsed.TotalSeconds, $log)
}

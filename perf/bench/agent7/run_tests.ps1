# Agent 7: run the asset-free gpu-aot fixtures that extract device.cpp / hooks_device.cpp /
# present_rect.h text, one at a time (single compiler process), and summarize pass/fail.
# Usage: powershell -NoProfile -File bench\agent7\run_tests.ps1 <tag> [test names...]
param([string]$Tag = 'baseline')
$ErrorActionPreference = 'Continue'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
. (Join-Path $root 'env\devshell.ps1') -Quiet 6>$null | Out-Null
$game = Join-Path $root 'DimensionsRecomp'
$gpu = Join-Path $game 'tools\gpu-aot'
$out = Join-Path $root "build\agent7\tests-$Tag"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$python = (Get-Command python -ErrorAction SilentlyContinue).Source
# name -> extra args ('' = pass --compiler clang++)
$tests = [ordered]@{
  'test_command_slots.py' = ''; 'test_frame_ring_transaction.py' = ''; 'test_submission_waits.py' = '';
  'test_frame_cadence.py' = ''; 'test_draw_device_view.py' = ''; 'test_gpu_timestamps.py' = '';
  'test_native_overlay.py' = ''; 'test_sampler_live_settings.py' = ''; 'test_frame_rate_settings.py' = '';
  'test_native_vsync.py' = 'none'; 'test_resize_fences.py' = ''; 'test_completion_callbacks.py' = '';
  'test_cpu_resource_wait.py' = ''; 'test_queued_frame_boundaries.py' = 'none'; 'test_threaded_callback.py' = '';
  'test_presentation_metrics.py' = 'none'
}
$only = @($args)
$lines = @()
foreach ($t in $tests.Keys) {
  if ($only.Count -and -not ($only -contains $t)) { continue }
  $dir = Join-Path $out ([IO.Path]::GetFileNameWithoutExtension($t))
  $argv = @((Join-Path $gpu $t), $dir)
  if ($tests[$t] -ne 'none') { $argv += @('--compiler', 'clang++') }
  $sw = [Diagnostics.Stopwatch]::StartNew()
  $log = & $python @argv 2>&1 | Out-String
  $code = $LASTEXITCODE
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  Set-Content -Path (Join-Path $dir 'run.log') -Value $log
  $tail = (($log -split "`r?`n") | Where-Object { $_.Trim() } | Select-Object -Last 2) -join ' | '
  if ($tail.Length -gt 300) { $tail = $tail.Substring(0, 300) }
  $lines += ('{0,-34} exit={1,-3} {2,6:N1}s  {3}' -f $t, $code, $sw.Elapsed.TotalSeconds, $tail)
}
if (-not $only.Count -or $only -contains 'test_present_rect.cpp') {
  $dir = Join-Path $out 'test_present_rect'; New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $exe = Join-Path $dir 'present-rect.exe'
  $sw = [Diagnostics.Stopwatch]::StartNew()
  $log = & clang++ -std=c++20 -UNDEBUG ('-I' + (Join-Path $game 'rexlego\src')) (Join-Path $gpu 'test_present_rect.cpp') -o $exe 2>&1 | Out-String
  $code = $LASTEXITCODE
  if ($code -eq 0) { $log += & $exe 2>&1 | Out-String; $code = $LASTEXITCODE }
  Set-Content -Path (Join-Path $dir 'run.log') -Value $log
  $tail = (($log -split "`r?`n") | Where-Object { $_.Trim() } | Select-Object -Last 2) -join ' | '
  $lines += ('{0,-34} exit={1,-3} {2,6:N1}s  {3}' -f 'test_present_rect.cpp', $code, $sw.Elapsed.TotalSeconds, $tail)
}
$lines | Set-Content -Path (Join-Path $out 'summary.txt')
$lines

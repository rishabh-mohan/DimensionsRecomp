# 1-CPU (CPU1, mask 0x2) end-to-end test of the float-blend chain on ~24 character VS, before the slot.
$ErrorActionPreference = 'Continue'
$w = '<workspace>'
$r = "$w\DimensionsRecomp"; $a = "$r\rexlego\out\native-gpu\aot"; $s = "$w\build\agent6\aot\scripts"
$exe = "$w\build\agent6\aot\gradient-build\gradient_compiler.exe"
$common = "$r\rexlego\out\native-gpu\current-compiler\gradients\source\shader_common.h"
$dxc = "$r\research\dxc-1.9.2609\bin\x64\dxc.exe"; $mc = "$w\toolchain\llvm-23.1.6\bin\llvm-mc.exe"
$env:PYTHONDONTWRITEBYTECODE = '1'
function Now { Get-Date -Format 'HH:mm:ss' }
function Run1([string]$Name, [string]$File, [string]$Arguments) {
  $psi = New-Object System.Diagnostics.ProcessStartInfo $File; $psi.Arguments = $Arguments
  $psi.UseShellExecute = $false; $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
  $t0 = Get-Date; $p = [Diagnostics.Process]::Start($psi); $p.ProcessorAffinity = [IntPtr]2
  $so = $p.StandardOutput.ReadToEndAsync(); $se = $p.StandardError.ReadToEndAsync(); $p.WaitForExit()
  Write-Host "--- $Name stdout"; Write-Host $so.Result; Write-Host "--- $Name stderr"; Write-Host $se.Result
  Write-Host "[$(Now)] end $Name exit=$($p.ExitCode) wall_s=$([math]::Round(((Get-Date)-$t0).TotalSeconds,2)) cpu_s(process only)=$([math]::Round($p.TotalProcessorTime.TotalSeconds,2))"
  return $p.ExitCode
}
foreach ($d in 'fbtest-shards','fbtest-out','fbtest-inputs','fbtest-bank') { if (Test-Path "$a\$d") { Remove-Item -Recurse -Force "$a\$d" } }
Write-Host "[$(Now)] fb chain test start"
$rc = Run1 'pick' 'python' "`"$s\pick_vs_test.py`" `"$a\shards`" `"$a\scan\corpus.tsv`" `"$a\fbtest-shards`" --count 24"
$rc = Run1 'run_shards(cpu1)' 'python' "`"$s\run_shards.py`" --shards-dir `"$a\fbtest-shards`" --out-dir `"$a\fbtest-out`" --exe `"$exe`" --common `"$common`" --cpus 1-1"
$rc = Run1 'make_float_blend_inputs' 'python' "`"$s\make_float_blend_inputs.py`" `"$a\fbtest-inputs`" --source `"$a\fbtest-out\shard00\hlsl-dump`""
$rc = Run1 'float-blend(cpu1)' 'python' "`"$r\tools\gpu-aot\build_float_blend_indices_bank.py`" `"$a\fbtest-bank`" --source `"$a\fbtest-inputs`" --dxc `"$dxc`" --llvm-mc `"$mc`""
Get-ChildItem "$a\fbtest-bank" -File -Filter 'float-blend-indices-bank.*' -ErrorAction SilentlyContinue | ForEach-Object { "$($_.Name) bytes=$($_.Length)" }
Write-Host "[$(Now)] fb chain test end"

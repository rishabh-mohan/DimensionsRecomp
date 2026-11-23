# Slot run (CPUs 4-11 = mask 0xFF0): sharded main DXIL compile -> merge -> HLSL dump merge
#   -> float-blend inputs (temporal-tool-equivalent *-vs-0-input.hlsl) -> float-blend bank (0xFC0)
#   -> instanced bank (--jobs 8, 0xFF0) -> delete shard intermediates.
# Every heavy process is pinned: shards one CPU each (run_shards.py), merge/dump/input steps on CPU4, banks on 0xFC0/0xFF0.
# -BanksOnly: skip the main compile + merges (needs aot/lego-dxil-cache.cpp and aot/hlsl-dump) - for a later slot.
param(
  [string]$StopLaunchAt = '20:10',
  [string]$KillAt = '20:14:30',
  [string]$NoNewStepAfter = '20:06',
  [switch]$SkipInstanced,
  [switch]$SkipFloatBlend,
  [switch]$BanksOnly,
  [switch]$KeepShardIntermediates
)
$ErrorActionPreference = 'Continue'
$w = '<workspace>'
$r = "$w\DimensionsRecomp"
$a = "$r\rexlego\out\native-gpu\aot"
$s = "$w\build\agent6\aot\scripts"
$exe = "$w\build\agent6\aot\gradient-build\gradient_compiler.exe"
$common = "$r\rexlego\out\native-gpu\current-compiler\gradients\source\shader_common.h"
$merge = "$w\build\agent6\aot\merge\merge_dxil_cache.exe"
$dxc = "$r\research\dxc-1.9.2609\bin\x64\dxc.exe"
$mc = "$w\toolchain\llvm-23.1.6\bin\llvm-mc.exe"
$env:PYTHONDONTWRITEBYTECODE = '1'
$kill = [datetime]::ParseExact($KillAt, 'HH:mm:ss', $null)
$noNew = [datetime]::ParseExact($NoNewStepAfter, 'HH:mm', $null)
function Now { Get-Date -Format 'HH:mm:ss' }
function Show-Files([string]$Dir, [string]$Filter) {
  Get-ChildItem $Dir -File -Filter $Filter -ErrorAction SilentlyContinue |
    ForEach-Object { "  $($_.Name) bytes=$($_.Length) sha256=$((Get-FileHash $_.FullName -Algorithm SHA256).Hash)" }
}

function Invoke-Pinned([string]$Name, [string]$File, [string]$Arguments, [long]$Mask) {
  if ((Get-Date) -ge $noNew) { Write-Host "[$(Now)] SKIP $Name (after $NoNewStepAfter)"; return 99 }
  $psi = New-Object System.Diagnostics.ProcessStartInfo $File
  $psi.Arguments = $Arguments
  $psi.UseShellExecute = $false
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $t0 = Get-Date
  $p = [Diagnostics.Process]::Start($psi)
  $p.ProcessorAffinity = [IntPtr]$Mask
  Write-Host "[$(Now)] start $Name pid=$($p.Id) mask=0x$('{0:X}' -f $Mask)"
  Write-Host "  cmd: $File $Arguments"
  $so = $p.StandardOutput.ReadToEndAsync(); $se = $p.StandardError.ReadToEndAsync()
  $killed = $false
  while (-not $p.WaitForExit(1000)) {
    if ((Get-Date) -ge $kill) { & taskkill /T /F /PID $p.Id | Out-Null; $killed = $true; break }
  }
  $p.WaitForExit()
  Write-Host "--- $Name stdout"; Write-Host $so.Result; Write-Host "--- $Name stderr"; Write-Host $se.Result
  Write-Host "[$(Now)] end $Name exit=$($p.ExitCode) killed=$killed wall_s=$([math]::Round(((Get-Date)-$t0).TotalSeconds,2)) cpu_s(process only)=$([math]::Round($p.TotalProcessorTime.TotalSeconds,2))"
  if ($killed) { return 98 }
  return $p.ExitCode
}

"[$(Now)] slot start (shards 4-11, stop-launch $StopLaunchAt, kill $KillAt, no-new-step $NoNewStepAfter, banksOnly=$BanksOnly)"
$mainDone = $false
if (-not $BanksOnly) {
  $t0 = Get-Date
  & python "$s\run_shards.py" --shards-dir "$a\shards" --out-dir "$a\shard-out" --exe $exe --common $common --cpus 4-11 --stop-launch-at $StopLaunchAt --kill-at $KillAt
  $rc = $LASTEXITCODE
  "[$(Now)] run_shards exit=$rc wall_s=$([math]::Round(((Get-Date)-$t0).TotalSeconds,2))"
  if ($rc -ne 0) { "[$(Now)] shards incomplete -> no merge; re-run this script later to resume"; exit 1 }

  $parts = Get-ChildItem "$a\shard-out" -Directory | Where-Object { Test-Path "$($_.FullName)\done.json" } |
    Sort-Object Name | ForEach-Object { "$($_.FullName)\lego-dxil-cache.cpp" } | Where-Object { Test-Path $_ }
  "[$(Now)] partial caches: $($parts.Count)"
  if (Test-Path "$a\lego-dxil-cache.cpp") { Remove-Item -Force "$a\lego-dxil-cache.cpp" }
  $args1 = "merge `"$a\lego-dxil-cache.cpp`" " + (($parts | ForEach-Object { "`"$_`"" }) -join ' ')
  $rc = Invoke-Pinned 'merge_dxil_cache' $merge $args1 0x10
  if ($rc -ne 0) { "[$(Now)] MERGE FAILED"; exit 2 }
  "[$(Now)] STAGED lego-dxil-cache.cpp bytes=$((Get-Item "$a\lego-dxil-cache.cpp").Length) sha256=$((Get-FileHash "$a\lego-dxil-cache.cpp" -Algorithm SHA256).Hash)"
  # entry-count cross-check: merged entries must equal the sum over the shard caches
  $cnt = { param($f) ([regex]::Matches([IO.File]::ReadAllText($f), '(?m)^\t\{ 0x[0-9A-F]+,')).Count }
  $sum = 0; foreach ($p in $parts) { $sum += (& $cnt $p) }
  $mergedEntries = & $cnt "$a\lego-dxil-cache.cpp"
  "[$(Now)] entries: merged=$mergedEntries sum_of_shards=$sum"

  if (Test-Path "$a\hlsl-dump") { Remove-Item -Recurse -Force "$a\hlsl-dump" }
  $dumps = (Get-ChildItem "$a\shard-out" -Directory | Sort-Object Name | ForEach-Object { "`"$($_.FullName)\hlsl-dump`"" }) -join ' '
  $rc = Invoke-Pinned 'merge_dumps' 'python' "`"$s\merge_dumps.py`" `"$a\hlsl-dump`" $dumps --manifest `"$a\shards\manifest.tsv`"" 0x10
  if ($rc -ne 0) { "[$(Now)] DUMP MERGE FAILED"; exit 3 }
  $hd = Get-ChildItem "$a\hlsl-dump" -File | Measure-Object Length -Sum
  "[$(Now)] STAGED hlsl-dump files=$($hd.Count) bytes=$($hd.Sum)"
  $mainDone = ($mergedEntries -eq $sum)
} else {
  if (-not (Test-Path "$a\lego-dxil-cache.cpp") -or -not (Test-Path "$a\hlsl-dump")) { "[$(Now)] BanksOnly needs aot/lego-dxil-cache.cpp + aot/hlsl-dump"; exit 4 }
}

if (-not $SkipFloatBlend) {
  if (Test-Path "$a\float-blend-inputs") { Remove-Item -Recurse -Force "$a\float-blend-inputs" }
  $rc = Invoke-Pinned 'make_float_blend_inputs' 'python' "`"$s\make_float_blend_inputs.py`" `"$a\float-blend-inputs`" --source `"$a\hlsl-dump`"" 0x10
  "[$(Now)] float-blend inputs exit=$rc"
  if ($rc -eq 0) {
    if (Test-Path "$a\float-blend-indices-bank") { Remove-Item -Recurse -Force "$a\float-blend-indices-bank" }
    $rc = Invoke-Pinned 'float-blend-indices-bank' 'python' "`"$r\tools\gpu-aot\build_float_blend_indices_bank.py`" `"$a\float-blend-indices-bank`" --source `"$a\float-blend-inputs`" --dxc `"$dxc`" --llvm-mc `"$mc`"" 0xFC0
    "[$(Now)] float-blend exit=$rc"
    Show-Files "$a\float-blend-indices-bank" 'float-blend-indices-bank.*'
    Show-Files "$a\float-blend-indices-bank" 'verification.json'
  }
}

if (-not $SkipInstanced) {
  if (Test-Path "$a\instanced-constants-bank") { Remove-Item -Recurse -Force "$a\instanced-constants-bank" }
  $rc = Invoke-Pinned 'instanced-constants-bank' 'python' "`"$r\tools\gpu-aot\build_instanced_constants_bank.py`" `"$a\instanced-constants-bank`" --source `"$a\hlsl-dump`" --dxc `"$dxc`" --llvm-mc `"$mc`" --jobs 8" 0xFF0
  "[$(Now)] instanced exit=$rc"
  Show-Files "$a\instanced-constants-bank" 'instanced-constants-bank.*'
  Show-Files "$a\instanced-constants-bank" 'verification.json'
}

if ($mainDone -and -not $KeepShardIntermediates) {
  $before = Get-ChildItem "$a\shard-out", "$a\shards" -Recurse -File | Measure-Object Length -Sum
  Get-ChildItem "$a\shard-out" -Directory | ForEach-Object {
    if (Test-Path "$($_.FullName)\hlsl-dump") { & cmd /c rmdir /s /q "$($_.FullName)\hlsl-dump" }
    if (Test-Path "$($_.FullName)\lego-dxil-cache.cpp") { Remove-Item -Force "$($_.FullName)\lego-dxil-cache.cpp" }
  }
  Get-ChildItem "$a\shards" -Directory | ForEach-Object { & cmd /c rmdir /s /q "$($_.FullName)" }
  $after = Get-ChildItem "$a\shard-out", "$a\shards" -Recurse -File | Measure-Object Length -Sum
  "[$(Now)] shard intermediates deleted: before files=$($before.Count) bytes=$($before.Sum) -> after files=$($after.Count) bytes=$($after.Sum) (kept: logs, done.json, status.json, driver.log, manifest.tsv)"
}
"[$(Now)] slot script end"

# Agent 7: apply the task #20 (batch 2) edits to the live tree after Agent 2's S1 announcement, then verify.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent7\b2_apply_and_verify.ps1 [-VerifyOnly] [-Tag b2-after] [-FixtureTag after3]
#   Refuses unless device.h, device.cpp and fps_counter.h still have their batch-1 hashes.
#   Verification: 18-TU syntax pass (2 at a time), gpu-aot fixtures + compare, test_fps_rects.py,
#   test_fps_counter.cpp, and hashes of every includer (to spot other agents' edits).
#   -VerifyOnly skips the edits and only reports result-hash mismatches (dry run of the checks).
#   Writes build\agent7\b2-apply-<Tag>\report.txt.
param([switch]$VerifyOnly, [string]$Tag = 'b2-after', [string]$FixtureTag = 'after3')
$ErrorActionPreference = 'Continue'  # native stderr must not abort the run (PowerShell 5.1)
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
Set-Location $root
. (Join-Path $root 'env\devshell.ps1') -Quiet 6>$null | Out-Null
$g = 'DimensionsRecomp\rexlego\src\gpu_native'
$out = "build\agent7\b2-apply-$Tag"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$report = Join-Path $out 'report.txt'
function Say($s) { $line = "[{0}] {1}" -f (Get-Date -Format 'HH:mm:ss'), $s; Write-Output $line; Add-Content -Path $report -Value $line }
function Sha16($p) { (Get-FileHash $p -Algorithm SHA256).Hash.Substring(0, 16) }
$before = [ordered]@{ 'device.h' = '12391F5CE364E280'; 'device.cpp' = '4C15043E486A6225'; 'fps_counter.h' = '79FC841E3180CA0D' }
$after = [ordered]@{ 'device.h' = '703939AA91EFEA81'; 'device.cpp' = '3D01E63142DBFB50'; 'fps_counter.h' = 'E05D6A554042B302' }
Set-Content -Path $report -Value "Agent 7 batch-2 apply/verify, VerifyOnly=$VerifyOnly"

if (-not $VerifyOnly) {
  foreach ($f in $before.Keys) {
    $h = Sha16 "$g\$f"
    if ($h -ne $before[$f]) { Say "REFUSED: $f is $h, expected $($before[$f])"; exit 2 }
  }
  Say 'live files match the batch-1 hashes; applying'
  python bench\agent7\batch2_edits.py 2>&1 | ForEach-Object { Say "  $_" }
  if ($LASTEXITCODE) { Say 'batch2_edits.py FAILED'; exit 3 }
  python bench\agent7\batch2_fps_edit.py 2>&1 | ForEach-Object { Say "  $_" }
  if ($LASTEXITCODE) { Say 'batch2_fps_edit.py FAILED'; exit 4 }
}
$bad = 0
foreach ($f in $after.Keys) {
  $p = "$g\$f"; $h = Sha16 $p
  $ok = if ($h -eq $after[$f]) { 'ok' } else { $bad++; 'MISMATCH' }
  Say ("{0,-14} {1} {2} {3}" -f $f, $h, (Get-Item $p).LastWriteTime.ToString('HH:mm:ss'), $ok)
}
if ($bad -and -not $VerifyOnly) { Say 'result hashes differ from the staged dry run; stopping'; exit 5 }

# Hashes of every device.h includer, against the pre-edit list (other agents' edits show up here).
$hashes = Join-Path $out 'hashes.txt'
$paths = @("$g\device.h", "$g\fps_counter.h") + @(Get-Content build\agent7\device_h_includers.txt |
  ForEach-Object { $_.Trim() } | Where-Object { $_ -match '^dimensionsrecomp\\.*\.(cpp|h)$' })
$paths | ForEach-Object { '{0} {1} {2}' -f (Sha16 $_), (Get-Item $_).LastWriteTime.ToString('HH:mm:ss'), $_.ToLower() } |
  Set-Content $hashes
$old = @{}; Get-Content build\agent7\syntax-b2-before\hashes.txt | ForEach-Object { $p = $_ -split ' ', 3; $old[$p[2].ToLower()] = $p[0] }
Get-Content $hashes | ForEach-Object {
  $p = $_ -split ' ', 3
  if ($old.ContainsKey($p[2]) -and $old[$p[2]] -ne $p[0]) { Say "changed since 20:2x: $($p[2]) $($old[$p[2]]) -> $($p[0])" }
}

Say 'syntax pass, 18 includers, 2 at a time'
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent7\syntax_check_includers.ps1 $Tag | Out-Null
$prev = @{}; Get-Content build\agent7\syntax-b2-before\summary.txt | ForEach-Object { $prev[($_ -split '\s+')[0]] = $_ }
Get-Content "build\agent7\syntax-$Tag\summary.txt" | ForEach-Object {
  $tu = ($_ -split '\s+')[0]
  $now = ($_ -replace '\s+[\d.]+s$', '') -replace '\s+', ' '
  $was = ($prev[$tu] -replace '\s+[\d.]+s$', '') -replace '\s+', ' '
  Say ("  {0}{1}" -f $now, $(if ($now -ne $was) { "   (before: $was)" } else { '' }))
}

Say 'fixtures'
powershell -NoProfile -File bench\agent7\run_tests.ps1 $FixtureTag | Out-Null
python bench\agent7\compare_fixtures.py baseline $FixtureTag 2>&1 | ForEach-Object { Say "  $_" }

Say 'test_fps_rects.py (live device.cpp vs build/agent7/batch1/device.cpp)'
python bench\agent7\test_fps_rects.py --out "build\agent7\test-fps-rects-$Tag" 2>&1 | Select-Object -Last 12 | ForEach-Object { Say "  $_" }
Say "  exit=$LASTEXITCODE"

Say 'test_fps_counter.cpp'
clang++ -std=c++20 -UNDEBUG -I DimensionsRecomp\rexlego\src DimensionsRecomp\tools\gpu-aot\test_fps_counter.cpp `
  -o build\agent7\obj\fps-counter-after.exe 2>&1 | ForEach-Object { Say "  $_" }
Say "  build exit=$LASTEXITCODE"
& build\agent7\obj\fps-counter-after.exe 2>&1 | ForEach-Object { Say "  $_" }
Say "  run exit=$LASTEXITCODE"
Say 'done'

# Syntax-only compile of every generated recomp TU of a variant (build/agent9/generated/<Variant>/default),
# with the real game Release flags ($GameFlagsFull from game_flags.ps1) plus a PCH of the variant's own
# legodimensions_pch.h built with the same flags (as the real CMake build does). Lowest priority:
# holds no slot itself, every clang run takes ONE Agent 9 slot for itself (slot1.ps1, same rules as
# cpu2.ps1), so a quiet window (bench/agent9/QUIET) pauses the loop between TUs; -Resume continues.
#   powershell -NoProfile -File bench/agent9/musttail/alltu.ps1 [-Variant batch] [-Resume] *> bench/agent9/musttail/alltu_<Variant>.log
# alltu_<Variant>.tsv: one row per TU (bytes, musttail sites, clang exit, wall and CPU seconds, error
# count, first error), appended as it goes. alltu_<Variant>_summary.txt: totals.
param([string]$Variant = 'musttail', [switch]$Resume)
$ErrorActionPreference = 'Continue'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
. (Join-Path $root 'env/devshell.ps1') | Out-Null
. (Join-Path $PSScriptRoot 'game_flags.ps1')
. (Join-Path $PSScriptRoot 'slot1.ps1')
$var = Join-Path $root "build/agent9/generated/$Variant/default"
if (-not (Test-Path (Join-Path $var 'legodimensions_pch.h'))) { Write-Host "alltu: variant not found: $var"; exit 2 }
$out = Join-Path $PSScriptRoot 'gen_out'
New-Item -ItemType Directory -Force $out | Out-Null
$devGen = 'DimensionsRecomp/rexlego/generated/default'
$flags = @($GameFlagsFull | ForEach-Object { if ($_ -like "-I*$devGen") { '-I' + ($var -replace '\\', '/') } else { $_ } })
if (@($GameFlagsFull | Where-Object { $_ -like "-I*$devGen" }).Count -ne 1 -or @($flags | Where-Object { $_ -match 'cmake_pch|^-include|^-c$|^-o$' }).Count) { Write-Host "alltu: unexpected game flags: $($flags -join ' ')"; exit 2 }
$tsv = Join-Path $PSScriptRoot "alltu_$Variant.tsv"
$sumFile = Join-Path $PSScriptRoot "alltu_${Variant}_summary.txt"
$reMt = [regex]'\[\[clang::musttail\]\]'
$errFile = Join-Path $out "alltu_${Variant}_last.err"
$summary = @("variant: $var (real game Release flags, -fsyntax-only, PCH of its own legodimensions_pch.h)")
$done = New-Object 'System.Collections.Generic.HashSet[string]'
if ($Resume -and (Test-Path $tsv)) { foreach ($l in (Get-Content $tsv | Select-Object -Skip 1)) { [void]$done.Add(($l -split "`t")[0]) } }
else { "tu`tbytes`tmusttail_sites`texit`twall_s`tcpu_s`terrors`tfirst_error" | Set-Content -Encoding ascii $tsv }

$pch = Join-Path $out "alltu_$Variant.pch"
$pchArgs = @()
if ($Resume -and (Test-Path $pch)) { $pchArgs = @('-include-pch', $pch); $summary += 'pch: reused (-Resume)' }
else {
  $r = Invoke-ClangInSlot (@($flags) + @('-x', 'c++-header', (Join-Path $var 'legodimensions_pch.h'), '-o', $pch)) (Join-Path $out "alltu_${Variant}_pch.log")
  $summary += ('pch build: exit={0} wall={1:n1}s cpu={2:n1}s' -f $r.code, $r.wall, $r.cpu)
  if ($r.code -eq 0) { $pchArgs = @('-include-pch', $pch) }
}

$tus = @(Get-ChildItem $var -Filter 'legodimensions_recomp.*.cpp' | Where-Object { $_.Name -match '^legodimensions_recomp\.\d+\.cpp$' } | Sort-Object { [int]($_.Name -replace '^legodimensions_recomp\.|\.cpp$', '') })
$first = -not $Resume
$total = [Diagnostics.Stopwatch]::StartNew()
foreach ($f in $tus) {
  if ($done.Contains($f.Name)) { continue }
  $s = $reMt.Matches([IO.File]::ReadAllText($f.FullName)).Count
  if ($first -and $pchArgs.Count) {
    # once: the same TU without the PCH (sanity and timing)
    $r = Invoke-ClangInSlot (@($flags) + @('-fsyntax-only', $f.FullName)) $errFile
    $summary += ('first TU ({0}) without pch: exit={1} wall={2:n1}s cpu={3:n1}s' -f $f.Name, $r.code, $r.wall, $r.cpu)
  }
  $r = Invoke-ClangInSlot (@($flags) + $pchArgs + @('-fsyntax-only', $f.FullName)) $errFile
  $errs = @(Get-Content $errFile -ErrorAction SilentlyContinue | Where-Object { $_ -match 'error:' })
  if ($r.code) { Copy-Item $errFile (Join-Path $out ('alltu_{0}_fail_{1}.err' -f $Variant, $f.BaseName)) -Force }
  if ($first -and $pchArgs.Count) { $summary += ('first TU with pch: exit={0} wall={1:n2}s cpu={2:n2}s' -f $r.code, $r.wall, $r.cpu) }
  $first = $false
  $fe = if ($errs.Count) { ($errs[0] -replace '^[A-Za-z]:[^:]*[\\/]', '' -replace "`t", ' ') } else { '' }
  ('{0}|{1}|{2}|{3}|{4:0.00}|{5:0.00}|{6}|{7}' -f $f.Name, $f.Length, $s, $r.code, $r.wall, $r.cpu, $errs.Count, ($fe -replace '\|', '/')) -replace '\|', "`t" | Add-Content -Encoding ascii $tsv
}
# totals over the whole tsv (also covers -Resume runs)
$rows = @(Get-Content $tsv | Select-Object -Skip 1 | ForEach-Object { , ($_ -split "`t") })
$pass = @($rows | Where-Object { $_[3] -eq '0' }).Count
$sites = 0; $wall = 0.0; $cpu = 0.0
foreach ($x in $rows) { $sites += [int]$x[2]; $wall += [double]$x[4]; $cpu += [double]$x[5] }
$summary += "TUs in variant: $($tus.Count)  compiled: $($rows.Count)  pass: $pass  fail: $($rows.Count - $pass)  musttail sites in compiled TUs: $sites"
$summary += ('clang wall {0:n1} s total ({1:n2} s/TU), CPU {2:n1} s total ({3:n2} s/TU); this run {4:n1} min' -f $wall, ($wall / [math]::Max(1, $rows.Count)), $cpu, ($cpu / [math]::Max(1, $rows.Count)), $total.Elapsed.TotalMinutes)
$summary | Tee-Object -FilePath $sumFile

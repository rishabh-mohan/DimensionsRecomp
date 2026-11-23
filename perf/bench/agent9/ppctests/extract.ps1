# Write build/agent9/ppctests/failures.md: for each test that does not pass in some variant (the rows of
# compare.md), the generated function it calls and the generated functions that one calls directly, per variant.
# -Stem <stem>: also write build/agent9/ppctests/<stem>.md with every generated function of that test binary.
#   powershell -NoProfile -File bench/agent9/ppctests/extract.ps1 [-Variants default,opt,crso] [-Stem instr_cr_so_fold]
param([string[]]$Variants = @('default', 'opt', 'crso'), [string]$Stem = 'instr_cr_so_fold')
$ErrorActionPreference = 'Continue'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
Set-Location $root
$base = 'build/agent9/ppctests'
$Variants = @($Variants | Where-Object { Test-Path "$base/$_/generated/ppc_test_functions.cpp" })
$tests = @(Get-Content "$base/compare.md" | Where-Object { $_ -match '^\| (\S+\.\S+) \|' } | ForEach-Object { ($_ -split '\|')[1].Trim() } | Where-Object { $_ -ne 'test' })
# test name -> symbol (symbol names are the same in every variant)
$sym = @{}; $cur = $null
foreach ($l in [IO.File]::ReadLines((Resolve-Path "$base/default/generated/ppc_test_cases.cpp"))) {
  if ($l -match '^TEST_CASE\("([^"]+)"') { $cur = $Matches[1] }
  elseif ($cur -and $l -match '^\s+(\w+)\(ctx, memory\);') { $sym[$cur] = $Matches[1]; $cur = $null }
}
function Get-Funcs([string]$file) {
  $f = @{}; $name = $null; $buf = $null
  foreach ($l in [IO.File]::ReadLines((Resolve-Path $file))) {
    if (-not $name -and $l -match '^DEFINE_REX_FUNC\((\w+)\) \{$') { $name = $Matches[1]; $buf = New-Object System.Collections.Generic.List[string] }
    if ($name) { $buf.Add($l); if ($l -eq '}') { $f[$name] = $buf; $name = $null } }
  }
  return $f
}
$funcs = @{}
foreach ($v in $Variants) { $funcs[$v] = Get-Funcs "$base/$v/generated/ppc_test_functions.cpp" }
function Add-Func($md, [string]$v, [string]$name) {
  $md.Add("$v ${name}:"); $md.Add('```cpp')
  if ($funcs[$v].ContainsKey($name)) { foreach ($l in $funcs[$v][$name]) { $md.Add($l) } } else { $md.Add('// not found') }
  $md.Add('```')
}
$md = New-Object System.Collections.Generic.List[string]
$md.Add("# Generated code behind the tests that do not pass in some variant ($($Variants -join ', '))"); $md.Add('')
foreach ($t in $tests) {
  $s = $sym[$t]
  $md.Add("## $t -> $s"); $md.Add('')
  foreach ($v in $Variants) {
    $names = @($s)
    if ($funcs[$v].ContainsKey($s)) {
      $names += @($funcs[$v][$s] | Select-String -Pattern '\b(\w+_[0-9A-F]{8})\(ctx, base\)' -AllMatches | ForEach-Object { $_.Matches } |
                  ForEach-Object { $_.Groups[1].Value } | Where-Object { $_ -ne $s } | Select-Object -Unique)
    }
    foreach ($n in $names) { Add-Func $md $v $n }
  }
  $md.Add('')
}
Set-Content -Path "$base/failures.md" -Value $md -Encoding UTF8
Write-Host "failures.md: $($tests.Count) tests, variants $($Variants -join ',')"
if ($Stem) {
  $md2 = New-Object System.Collections.Generic.List[string]
  $md2.Add("# Generated functions of $Stem ($($Variants -join ', '))"); $md2.Add('')
  foreach ($v in $Variants) {
    $md2.Add("## $v"); $md2.Add('')
    foreach ($n in @($funcs[$v].Keys | Where-Object { $_ -like "${Stem}_*" } | Sort-Object)) { Add-Func $md2 $v $n }
  }
  Set-Content -Path "$base/$Stem.md" -Value $md2 -Encoding UTF8
  Write-Host "$Stem.md written"
}

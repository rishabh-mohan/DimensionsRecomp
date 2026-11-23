# Run ppc_tests.exe for each built variant and compare per-test results.
#   powershell -NoProfile -File bench/agent9/ppctests/runtests.ps1 [-Variants default,opt,crso]
# Main pass: every test except the isolated tag and the variant's exclusions, in declaration order
# (Catch2 3.12, XML reporter). Exclusions are extra "~<name>" specs, AND-ed into the same Catch2 filter.
# Isolated pass: each test of the isolated tag in its own process. Their generated functions contain
# REX_FATAL (unresolved tail call), which ends the process with 0xC0000409 and would end the main pass.
# Excluded tests run once each in their own process for the record and are counted as 'excluded'.
# Outputs: build/agent9/ppctests/<variant>/{results.xml,isolated.txt,excluded.txt}, build/agent9/ppctests/compare.md
param([string[]]$Variants = @('default', 'opt', 'crso'), [string]$IsolateTag = 'seq_tailcall_musttail',
      # variant=test pairs. opt and opt9 have xer_as_local: XER is a per-function local that a call does not carry, so
      # cr_so_fold.test_call (mtxer in the caller, compares in the callee) gives SO = 0 there by design.
      [string[]]$Exclude = @('opt=cr_so_fold.test_call', 'opt9=cr_so_fold.test_call'))
$ErrorActionPreference = 'Continue'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
Set-Location $root
function Get-Detail($tc) {
  (@($tc.SelectNodes('.//Expression[@success="false"]') | ForEach-Object { "line $($_.line): $($_.Original.Trim()) => $($_.Expanded.Trim())" }) +
   @($tc.SelectNodes('.//Exception') | ForEach-Object { "exception: $($_.InnerText.Trim())" }) +
   @($tc.SelectNodes('.//FatalErrorCondition') | ForEach-Object { "fatal: $($_.InnerText.Trim())" })) -join '; '
}
function Invoke-Single([string]$n) {
  if (Test-Path single.xml) { Remove-Item -Force single.xml }
  & .\ppc_tests.exe "$n" --reporter xml --out single.xml 2>&1 | Out-Null
  $c = $LASTEXITCODE
  $r = "CRASH(0x{0:X8})" -f $c; $d = "own process exit 0x{0:X8}" -f $c
  try {
    [xml]$s = Get-Content -Raw single.xml
    $tc = $s.SelectSingleNode('//TestCase')
    if ($tc -and $tc.OverallResult) {
      if ($tc.OverallResult.success -eq 'true') { $r = 'pass'; $d = '' } else { $r = 'FAIL'; $d = Get-Detail $tc }
    }
  } catch {}
  return @($r, $d)
}
$res = [ordered]@{}; $why = @{}; $summary = New-Object System.Collections.Generic.List[string]
foreach ($v in $Variants) {
  $vdir = "build/agent9/ppctests/$v"
  if (-not (Test-Path "$vdir/ppc_tests.exe")) { Write-Host "$v : no exe"; continue }
  $ex = @($Exclude | Where-Object { $_.StartsWith("$v=") } | ForEach-Object { $_.Substring($v.Length + 1) })
  Push-Location $vdir
  $map = [ordered]@{}; $det = @{}
  $spec = @("~[$IsolateTag]") + @($ex | ForEach-Object { "~$_" })
  if (Test-Path results.xml) { Remove-Item -Force results.xml }
  $sw = [Diagnostics.Stopwatch]::StartNew()
  & .\ppc_tests.exe @spec --order decl --reporter xml --out results.xml 2>&1 | Out-Null
  $code = $LASTEXITCODE
  $sw.Stop()
  try {
    [xml]$x = Get-Content -Raw results.xml
    foreach ($tc in $x.SelectNodes('//TestCase')) {
      $ok = ($tc.OverallResult.success -eq 'true')
      $map[$tc.name] = if ($ok) { 'pass' } else { 'FAIL' }
      if (-not $ok) { $det[$tc.name] = Get-Detail $tc }
    }
  } catch { Write-Host "$v : results.xml unreadable ($($_.Exception.Message))" }
  $main = "{0}: main pass exit {1}, {2:n1} s, {3} test cases" -f $v, $code, $sw.Elapsed.TotalSeconds, $map.Count
  $iso = New-Object System.Collections.Generic.List[string]
  $names = @(& .\ppc_tests.exe "[$IsolateTag]" --list-tests --verbosity quiet 2>$null | Where-Object { $_.Trim() } | ForEach-Object { $_.Trim() })
  foreach ($n in $names) {
    $r, $d = Invoke-Single $n
    $map[$n] = $r; if ($d) { $det[$n] = $d }
    $iso.Add("$n : $r $d".Trim())
  }
  Set-Content -Path isolated.txt -Value $iso -Encoding UTF8
  $exl = New-Object System.Collections.Generic.List[string]
  foreach ($n in $ex) {
    $r, $d = Invoke-Single $n
    $map[$n] = 'excluded'; $det[$n] = "excluded; own run: $r $d".Trim()
    $exl.Add("$n : own run $r $d".Trim())
  }
  Set-Content -Path excluded.txt -Value $exl -Encoding UTF8
  Pop-Location
  $res[$v] = $map; $why[$v] = $det
  $cnt = @{}; foreach ($r in $map.Values) { $k = ($r -replace '\(.*', ''); $cnt[$k] = 1 + [int]$cnt[$k] }
  $s = "{0}: {1} tests: {2} pass, {3} FAIL, {4} CRASH, {5} excluded" -f $v, $map.Count, [int]$cnt['pass'], [int]$cnt['FAIL'], [int]$cnt['CRASH'], [int]$cnt['excluded']
  $summary.Add($s)
  Write-Host "$main; isolated $($names.Count); excluded $($ex.Count)"
  Write-Host $s
}
$vs = @($res.Keys)
if ($vs.Count -gt 0) {
  $all = @($vs | ForEach-Object { $res[$_].Keys }) | Sort-Object -Unique
  $lines = New-Object System.Collections.Generic.List[string]
  $lines.Add("| test | $($vs -join ' | ') | detail |"); $lines.Add('|---|' + ('---|' * $vs.Count) + '---|')
  $diff = 0; $same = 0
  foreach ($n in $all) {
    $cells = @($vs | ForEach-Object { if ($res[$_].Contains($n)) { $res[$_][$n] } else { 'missing' } })
    if (@($cells | Where-Object { $_ -ne 'pass' }).Count -eq 0) { continue }
    $d = @($vs | Where-Object { $why[$_].ContainsKey($n) } | ForEach-Object { "${_}: $($why[$_][$n])" }) -join ' / '
    $lines.Add("| $n | $($cells -join ' | ') | $($d -replace '\|', '\|') |")
    if (@($cells | Sort-Object -Unique).Count -gt 1) { $diff++ } else { $same++ }
  }
  $hdr = @("# ppc_tests per-test results: $($vs -join ' vs ')", '') + @($summary) +
         @('', "tests whose result differs between variants: $diff; not passing in every variant: $same", '')
  Set-Content -Path build/agent9/ppctests/compare.md -Value ($hdr + $lines) -Encoding UTF8
  $hdr | ForEach-Object { Write-Host $_ }
}

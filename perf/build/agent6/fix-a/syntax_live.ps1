<#
.SYNOPSIS
  Agent 6: clang -fsyntax-only of the two live fix-a TUs, through env\compile-one.ps1 -SyntaxOnly with
  build\dev\compile_commands.json (the dev game tree, LEGODIMENSIONS_NATIVE_GPU=1). Nothing is written.
  One clang at a time (1 thread). The log goes to build\agent6\fix-a\syntax-<Tag>.log.

  Expected with fix-a + commit applied: rc=0 and 0 errors for both. settings_registry.cpp keeps its 4
  existing getenv/sscanf deprecation warnings (pristine lines 133/135/148/152, after fix-a 136/138/151/155);
  settings_preferences.cpp has none.
  Written for Windows PowerShell 5.1:  powershell -NoProfile -File build\agent6\fix-a\syntax_live.ps1 -Tag post
#>
param([string]$Tag = 'live')
$ErrorActionPreference = 'Continue'
$root = '<workspace>'
Set-Location $root
$log = Join-Path $root ('build\agent6\fix-a\syntax-' + $Tag + '.log')
$lines = @('== Agent 6 syntax-only of the live fix-a TUs  {0:yyyy-MM-dd HH:mm:ss}  tag={1}' -f (Get-Date), $Tag)
$fail = 0
foreach ($rel in 'DimensionsRecomp\rexlego\src\settings_registry.cpp', 'DimensionsRecomp\rexlego\src\settings_preferences.cpp') {
  $h = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $root $rel)).Hash
  $t0 = Get-Date
  $out = @(& powershell -NoProfile -File (Join-Path $root 'env\compile-one.ps1') $rel -OutDir 'build\agent6\obj' `
             -Db 'build\dev\compile_commands.json' -SyntaxOnly 2>&1 | ForEach-Object { "$_" })
  $rc = $LASTEXITCODE
  $diag = @($out | Where-Object { $_ -match '\b(warning|error):' })
  $w = @($diag | Where-Object { $_ -match '\bwarning:' }).Count
  $e = @($diag | Where-Object { $_ -match '\berror:' }).Count
  if ($rc -ne 0 -or $e -ne 0) { $fail = 1 }
  $lines += ('{0} sha256={1} rc={2} warnings={3} errors={4} {5:N1}s' -f $rel, $h.Substring(0, 8), $rc, $w, $e, ((Get-Date) - $t0).TotalSeconds)
  $lines += @($diag | ForEach-Object { '    ' + ($_ -replace '^.*?[\\/]rexlego[\\/]', '') })
  if ($rc -ne 0) { $lines += @($out | Select-Object -Last 40 | ForEach-Object { '  | ' + $_ }) }
}
$lines += $(if ($fail) { 'SYNTAX: FAIL' } else { 'SYNTAX: OK' })
$lines | Set-Content -LiteralPath $log -Encoding UTF8
$lines
exit $fail

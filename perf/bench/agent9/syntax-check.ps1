# Syntax-check SDK translation units with the dev-tree compile database (one job, no objects).
# Usage: powershell -File bench/agent9/syntax-check.ps1 [relative/path.cpp ...]
param([string[]]$Files = @(
    'src/codegen/codegen_writer.cpp', 'src/codegen/function_graph.cpp',
    'src/codegen/builders/context.cpp', 'src/codegen/builders/control_flow.cpp',
    'src/codegen/config.cpp'))
$ErrorActionPreference = 'Stop'
$root = Resolve-Path "$PSScriptRoot/../.."
. "$root/env/devshell.ps1" | Out-Null
$db = Get-Content "$root/build/sdk-dev/compile_commands.json" -Raw | ConvertFrom-Json
$fail = 0
foreach ($f in $Files) {
  $leaf = $f.Replace('/', '\')
  $e = $db | Where-Object { $_.file.Replace('/', '\') -like "*rexglue-sdk\$leaf" } | Select-Object -First 1
  if (-not $e) { Write-Host "NO ENTRY: $f"; $fail++; continue }
  $cmd = if ($e.command) { $e.command } else { ($e.arguments | ForEach-Object { if ($_ -match '\s') { "`"$_`"" } else { $_ } }) -join ' ' }
  # Drop the object output and compile-only flags, then ask for a syntax-only run.
  $cmd = $cmd -replace '\s(-o|/Fo)\s*\S+', '' -replace '\s(-c|/c)(\s)', '$2'
  $cmd = $cmd -replace '\s(-MD|-MMD)\s', ' ' -replace '\s-MF\s*\S+', '' -replace '\s-MT\s*\S+', ''
  # The dev tree's PCH is not built; parse its header textually instead.
  $cmd = $cmd -replace '\s-Xclang\s+-include-pch\s+-Xclang\s+\S+', ''
  $flag = if ($cmd -match 'clang-cl') { '/Zs' } else { '-fsyntax-only' }
  $sw = [Diagnostics.Stopwatch]::StartNew()
  Push-Location $e.directory
  $out = cmd /c "$cmd $flag 2>&1"
  $code = $LASTEXITCODE
  Pop-Location
  $errs = @($out | Select-String -Pattern 'error' -SimpleMatch).Count
  Write-Host ("{0,-45} exit={1} errors={2} {3:n1}s" -f $f, $code, $errs, $sw.Elapsed.TotalSeconds)
  if ($code -ne 0) { $fail++; $out | Select-Object -First 40 | ForEach-Object { Write-Host "  $_" } }
}
exit $fail

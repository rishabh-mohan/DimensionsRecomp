# Agent 7: syntax-check staged copies of gpu_native headers/sources before they go into the live tree.
# The staged tree mirrors rexlego/src (build/agent7/b2-stage/src/gpu_native/...). -iquote puts it ahead of
# the -I paths for "gpu_native/..." includes; every gpu_native include uses that prefix.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent7\stage_compile.ps1 <tag> <tu.cpp>...
#   A TU that exists in the stage is compiled from the stage with the live TU's flags.
param([string]$Tag = 'stage', [Parameter(ValueFromRemainingArguments = $true)][string[]]$Tus)
$ErrorActionPreference = 'Continue'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$stage = Join-Path $root 'build\agent7\b2-stage\src'
$out = Join-Path $root "build\agent7\stage-$Tag"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$lines = @()
foreach ($tu in $Tus) {
  $live = Join-Path $root "DimensionsRecomp\rexlego\src\gpu_native\$tu"
  if ($tu -eq 'main.cpp') { $live = Join-Path $root 'DimensionsRecomp\rexlego\src\main.cpp' }
  $print = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'env\compile-one.ps1') $live `
    -OutDir (Join-Path $root 'build\agent7\obj') -Db (Join-Path $root 'build\dev\compile_commands.json') -SyntaxOnly -PrintOnly 2>&1
  $cmd = ($print | Where-Object { $_ -match 'clang\+\+\.exe' } | Select-Object -First 1)
  if (-not $cmd) { $lines += "$tu NO-COMMAND"; continue }
  $staged = Join-Path $stage "gpu_native\$tu"
  $src = if (Test-Path $staged) { $staged } else { $live }
  $exe = ($cmd -split ' ', 2)[0]
  $rest = ($cmd -split ' ', 2)[1].Replace($live, $src)
  if ($src -ne $live -and -not $rest.Contains($src)) { $lines += "$tu SOURCE-NOT-SWAPPED"; continue }
  if (-not $rest.Contains('-std=gnu++23')) { $lines += "$tu NO-STD-FLAG"; continue }
  $rest = $rest.Replace('-std=gnu++23', "-std=gnu++23 -iquote $($stage.Replace('\','/'))")
  if ($env:STAGE_EXTRA) { $rest += " $env:STAGE_EXTRA" }  # e.g. -H to list the headers each TU opened
  $log = Join-Path $out ([IO.Path]::GetFileNameWithoutExtension($tu) + '.log')
  $sw = [Diagnostics.Stopwatch]::StartNew()
  Push-Location (Join-Path $root 'build\dev')
  $p = Start-Process -FilePath $exe -ArgumentList $rest -NoNewWindow -Wait -PassThru -RedirectStandardError $log -RedirectStandardOutput "$log.out"
  Pop-Location
  $text = '' + (Get-Content $log -Raw)
  $errors = ([regex]::Matches([string]$text, 'error:')).Count
  $warnings = ([regex]::Matches([string]$text, 'warning:')).Count
  $from = if ($src -eq $staged) { 'staged' } else { 'live' }
  $lines += ('{0,-28} {1,-6} exit={2} errors={3} warnings={4} {5,5:N0}s' -f $tu, $from, $p.ExitCode, $errors, $warnings, $sw.Elapsed.TotalSeconds)
}
$lines | Set-Content (Join-Path $out 'summary.txt')
$lines

<#
.SYNOPSIS
  Agent 8: syntax-only compile check of the rexlego files changed in session 2, one at a time
  (1 thread), with the exact flags from a compile database (default build\dev = Native GPU ON).

  Extra warnings (-Wall -Wextra) are added; the exit code counts files that failed to compile
  (warnings do not fail). Warnings that point into rexlego\src are listed separately at the end.
  Log: build\agent8\compile-check.log (appended).

.EXAMPLE
  powershell -NoProfile -File bench\agent8\compile-check.ps1
  powershell -NoProfile -File bench\agent8\compile-check.ps1 -Files name_trace.cpp,scene_distance.cpp
#>
param(
    [string]$Db = 'build\dev\compile_commands.json',
    [string[]]$Files = @('discord_presence.cpp', 'cheat_engine.cpp', 'cheat_menu.cpp', 'native_skin_diagnostics.cpp',
                         'native_atomics.cpp', 'sample_profiler.cpp'),
    [switch]$NoExtraWarnings
)
$ErrorActionPreference = 'Continue'
# 'powershell -File x.ps1 -Files a.cpp,b.cpp' passes one string; split it.
$Files = @($Files | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$Root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
Set-Location $Root
$log = Join-Path $Root 'build\agent8\compile-check.log'
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
$extra = @()
if (-not $NoExtraWarnings) { $extra = @('-Wall', '-Wextra', '-Wno-unused-parameter') }
Add-Content -Path $log -Value "=== compile-check $(Get-Date -Format s) db=$Db extra=$($extra -join ' ')"
$fail = 0
$own = New-Object System.Collections.Generic.List[string]
foreach ($name in $Files) {
    $f = $name
    if (-not ($f -match '[\\/]')) { $f = "DimensionsRecomp\rexlego\src\$name" }
    $text = & powershell -NoProfile -File env\compile-one.ps1 $f -OutDir build\agent8\obj -SyntaxOnly -Db $Db @extra 2>&1 | Out-String -Width 4096
    $code = $LASTEXITCODE
    if ($code -ne 0) { $fail++ }
    $errors = ([regex]::Matches($text, ': error: ')).Count
    $warnings = ([regex]::Matches($text, ': warning: ')).Count
    $line = "--- $f exit=$code errors=$errors warnings=$warnings"
    Write-Host $line
    Add-Content -Path $log -Value $line
    Add-Content -Path $log -Value $text
    foreach ($l in ($text -split "`r?`n")) {
        if ($l -match 'rexlego[\\/]src[\\/][^:]+:\d+:\d+: (warning|error):') { $own.Add($l) }
    }
}
Add-Content -Path $log -Value '=== diagnostics in rexlego\src:'
foreach ($l in $own) { Add-Content -Path $log -Value $l; Write-Host $l }
$summary = "=== done files=$($Files.Count) failed=$fail rexlego-diagnostics=$($own.Count) $(Get-Date -Format s)"
Add-Content -Path $log -Value $summary
Write-Host $summary
exit $fail

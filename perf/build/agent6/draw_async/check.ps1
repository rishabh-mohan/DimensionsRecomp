# Syntax-checks build/agent6/draw_async/draw.cpp with draw.cpp's own command from build/dev
# (captured by compile-one -PrintOnly into printonly.txt). Read-only: -fsyntax-only, nothing written.
param([string]$Source = "$PSScriptRoot\draw.cpp")
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path "$PSScriptRoot\..\..\..").Path
$lines = Get-Content "$PSScriptRoot\printonly.txt"
$cmdline = ($lines | Where-Object { $_ -match 'clang\+\+\.exe' } | Select-Object -First 1)
$copy = (Resolve-Path $Source).Path.Replace('\', '/')
$pattern = '[A-Za-z]:[\\/][^ "]*?DimensionsRecomp[\\/]rexlego[\\/]src[\\/]gpu_native[\\/]draw\.cpp'
$hits = [regex]::Matches($cmdline, $pattern).Count
if (-not $hits) { $pattern = '(\.\.[\\/])+DimensionsRecomp[\\/]rexlego[\\/]src[\\/]gpu_native[\\/]draw\.cpp'; $hits = [regex]::Matches($cmdline, $pattern).Count }
if (-not $hits) { throw 'draw.cpp not found in the command' }
$new = [regex]::Replace($cmdline, $pattern, $copy)
# "../tt_lock_trace.h" is relative to gpu_native/.
$new += " `"-I$root\DimensionsRecomp\rexlego\src\gpu_native`""
$exe = $new.Substring(0, $new.IndexOf(' '))
$arguments = $new.Substring($new.IndexOf(' ') + 1)
Write-Host "replaced $hits occurrence(s); source $copy"
$psi = New-Object Diagnostics.ProcessStartInfo $exe, $arguments
$psi.WorkingDirectory = "$root\build\dev"
$psi.UseShellExecute = $false
$process = [Diagnostics.Process]::Start($psi)
$process.WaitForExit()
Write-Host "exit $($process.ExitCode)"
exit $process.ExitCode

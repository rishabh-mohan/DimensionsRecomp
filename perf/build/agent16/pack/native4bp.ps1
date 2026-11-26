<#
  native4bp.ps1 - E16.1, build\agent16\pack: launcher for native4bp.py (plan | pack | bin).
  Sets Idle priority + affinity 0x3 on this PowerShell first (every child inherits both), dot-sources
  env\devshell.ps1 -Jobs 1 -Quiet (clang++ + MSVC env for the lookup fixture and the recompiles), then runs
  python native4bp.py with the same arguments. Exit code = native4bp.py's.

  powershell -NoProfile -ExecutionPolicy Bypass -File build\agent16\pack\native4bp.ps1 plan --input <pack-input dir>
  powershell -NoProfile -ExecutionPolicy Bypass -File build\agent16\pack\native4bp.ps1 pack --input <pack-input dir>
  powershell -NoProfile -ExecutionPolicy Bypass -File build\agent16\pack\native4bp.ps1 bin [--pack-run <run dir>] [--bin-out native4bp-bin]
#>
$ErrorActionPreference = 'Stop'
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::Idle
$me.ProcessorAffinity = [IntPtr]3
$W = '<workspace>'
. (Join-Path $W 'env\devshell.ps1') -Jobs 1 -Quiet
$env:PYTHONDONTWRITEBYTECODE = '1'
$py = (Get-Command python -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
& $py (Join-Path $PSScriptRoot 'native4bp.py') @args
exit $LASTEXITCODE

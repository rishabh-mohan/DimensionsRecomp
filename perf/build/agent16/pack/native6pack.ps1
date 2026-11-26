<#
  native6pack.ps1 - M16, build\agent16\pack: launcher for native6pack.py (plan | pack | bin); copy of native5pack.ps1 22245C44
  with the names changed and $W derived from $PSScriptRoot (N3: no hard-coded workspace path).
  Sets Idle priority + affinity 0x3 on this PowerShell first (every child inherits both), dot-sources
  env\devshell.ps1 -Jobs 1 -Quiet (clang++ + MSVC env for the lookup fixture and the recompiles), then runs
  python native6pack.py with the same arguments. Exit code = native6pack.py's.

  powershell -NoProfile -ExecutionPolicy Bypass -File build\agent16\pack\native6pack.ps1 plan --input <pack-input dir>
  powershell -NoProfile -ExecutionPolicy Bypass -File build\agent16\pack\native6pack.ps1 pack --input <pack-input dir>
  powershell -NoProfile -ExecutionPolicy Bypass -File build\agent16\pack\native6pack.ps1 bin --pack-run <run dir> [--bin-out native6pack-bin]
#>
$ErrorActionPreference = 'Stop'
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::Idle
$me.ProcessorAffinity = [IntPtr]3
$W = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
. (Join-Path $W 'env\devshell.ps1') -Jobs 1 -Quiet
$env:PYTHONDONTWRITEBYTECODE = '1'
$py = (Get-Command python -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
& $py (Join-Path $PSScriptRoot 'native6pack.py') @args
exit $LASTEXITCODE

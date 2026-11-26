<#
  psobin.ps1 - E16.1, build\agent16\psobin: launcher for psobin.py (plan | bin).
  Sets Idle priority + affinity 0x3 on this PowerShell first (every child inherits both), dot-sources
  env\devshell.ps1 -Jobs 1 -Quiet (clang++ + MSVC env for the recompile), then runs python psobin.py with the
  same arguments. Exit code = psobin.py's.

  powershell -NoProfile -ExecutionPolicy Bypass -File build\agent16\psobin\psobin.ps1 plan --src <after-file> --sha <pinned sha256>
  powershell -NoProfile -ExecutionPolicy Bypass -File build\agent16\psobin\psobin.ps1 bin  --src <after-file> --sha <pinned sha256>
#>
$ErrorActionPreference = 'Stop'
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::Idle
$me.ProcessorAffinity = [IntPtr]3
$W = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
. (Join-Path $W 'env\devshell.ps1') -Jobs 1 -Quiet
$env:PYTHONDONTWRITEBYTECODE = '1'
$py = (Get-Command python -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
& $py (Join-Path $PSScriptRoot 'psobin.py') @args
exit $LASTEXITCODE

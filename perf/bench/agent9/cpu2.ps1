# Run one command while holding one of the two Agent 9 CPU slots (the team shares a 2-thread budget).
# Usage:
#   powershell -NoProfile -File bench/agent9/cpu2.ps1 -File <script.ps1>
#   powershell -NoProfile -File bench/agent9/cpu2.ps1 -Command "<powershell command>"
# The command runs in a child powershell in the workspace root, so dot-source the toolchain inside it:
#   -Command ". .\env\devshell.ps1 | Out-Null; clang++ ..."
# The slots are named mutexes, so a killed holder frees its slot automatically.
param([string]$File, [string]$Command)
$ErrorActionPreference = 'Stop'
if (-not $File -and -not $Command) { Write-Error 'cpu2.ps1: give -File or -Command'; exit 2 }
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
# Quiet window (timing runs): while bench/agent9/QUIET exists, wait before taking a slot.
$quietWait = [Diagnostics.Stopwatch]::StartNew()
while (Test-Path (Join-Path $PSScriptRoot 'QUIET')) { Start-Sleep -Seconds 15 }
if ($quietWait.Elapsed.TotalSeconds -gt 2) { Write-Host ("cpu2: waited {0:n0}s for the quiet window to end" -f $quietWait.Elapsed.TotalSeconds) }
$m = @([Threading.Mutex]::new($false, 'Local\agent9-cpu-0'), [Threading.Mutex]::new($false, 'Local\agent9-cpu-1'))
$wait = [Diagnostics.Stopwatch]::StartNew()
try { $i = [Threading.WaitHandle]::WaitAny([Threading.WaitHandle[]]$m) }
catch [Threading.AbandonedMutexException] { $i = $_.Exception.MutexIndex }
if ($wait.Elapsed.TotalSeconds -gt 2) { Write-Host ("cpu2: waited {0:n0}s for slot {1}" -f $wait.Elapsed.TotalSeconds, $i) }
$code = 1
try {
  Push-Location $root
  if ($File) { & powershell -NoProfile -ExecutionPolicy Bypass -File $File } else { & powershell -NoProfile -ExecutionPolicy Bypass -Command $Command }
  $code = $LASTEXITCODE
} finally {
  Pop-Location
  $m[$i].ReleaseMutex()
}
exit $code

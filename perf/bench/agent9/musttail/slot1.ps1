# Dot-source. Per-compile Agent 9 CPU slot, with the same rules as bench/agent9/cpu2.ps1:
#   Invoke-InSlot { ... }   wait while bench/agent9/QUIET exists, take whichever of the two slot
#                           mutexes is free (re-checking QUIET once it is held), run the block,
#                           release. Use it per compile so a quiet window, or Agent 9's own 2-slot
#                           jobs, get in between steps.
#   Invoke-ClangInSlot <args> <stderr file>  clang++ in one slot via Start-Process; returns
#                           code, wall seconds, CPU seconds (cc1 runs in-process in the driver).
$Agent9Quiet = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../QUIET'))
function Invoke-InSlot([scriptblock]$__slotBody) {
  $__slotSw = [Diagnostics.Stopwatch]::StartNew()
  while ($true) {
    while (Test-Path $Agent9Quiet) { Start-Sleep -Seconds 15 }
    $__slotM = @([Threading.Mutex]::new($false, 'Local\agent9-cpu-0'), [Threading.Mutex]::new($false, 'Local\agent9-cpu-1'))
    try { $__slotI = [Threading.WaitHandle]::WaitAny([Threading.WaitHandle[]]$__slotM) }
    catch [Threading.AbandonedMutexException] { $__slotI = $_.Exception.MutexIndex }
    if (-not (Test-Path $Agent9Quiet)) { break }
    $__slotM[$__slotI].ReleaseMutex(); $__slotM[0].Dispose(); $__slotM[1].Dispose()
  }
  if ($__slotSw.Elapsed.TotalSeconds -gt 2) { Write-Host ('[{0}] slot: waited {1:n0}s (quiet window or slots busy)' -f (Get-Date -Format 'HH:mm:ss'), $__slotSw.Elapsed.TotalSeconds) }
  try { & $__slotBody } finally { $__slotM[$__slotI].ReleaseMutex(); $__slotM[0].Dispose(); $__slotM[1].Dispose() }
}
function Invoke-ClangInSlot([string[]]$ClangArgs, [string]$ErrFile) {
  if (-not $script:Agent9Clang) { $script:Agent9Clang = (Get-Command clang++.exe -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source }
  $__clangArgs = @($ClangArgs | Where-Object { $_ })
  Invoke-InSlot {
    $__sw = [Diagnostics.Stopwatch]::StartNew()
    $__p = Start-Process -FilePath $script:Agent9Clang -ArgumentList $__clangArgs -NoNewWindow -PassThru -RedirectStandardError $ErrFile
    $null = $__p.Handle
    $__p.WaitForExit()
    [pscustomobject]@{ code = $__p.ExitCode; wall = $__sw.Elapsed.TotalSeconds; cpu = $__p.TotalProcessorTime.TotalSeconds }
  }
}

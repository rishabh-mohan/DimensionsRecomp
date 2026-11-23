# Agent 9 CPU slots (the team budget is 2 threads). Dot-source, then:
#   $held = Enter-Agent9Slots 2   # waits for slot 0, then slot 1 (fixed order, so no deadlock)
#   try { ... } finally { Exit-Agent9Slots $held }
# cpu2.ps1 takes ONE slot (whichever is free) for single-threaded jobs. Jobs that use 2 cores
# (gen.ps1, build-tool2.ps1 -Jobs 2) take both. Named mutexes: a killed holder frees its slots.
function Enter-Agent9Slots([int]$Count = 2) {
  # Quiet window (timing runs): while bench/agent9/QUIET exists, wait before taking any slot.
  while (Test-Path '<workspace>\bench\agent9\QUIET') { Start-Sleep -Seconds 15 }
  $held = New-Object System.Collections.ArrayList
  $wait = [Diagnostics.Stopwatch]::StartNew()
  for ($i = 0; $i -lt $Count; $i++) {
    $m = [Threading.Mutex]::new($false, "Local\agent9-cpu-$i")
    try { [void]$m.WaitOne() } catch [Threading.AbandonedMutexException] { }
    [void]$held.Add($m)
  }
  if ($wait.Elapsed.TotalSeconds -gt 2) { Write-Host ("slots: waited {0:n0}s for {1} slot(s)" -f $wait.Elapsed.TotalSeconds, $Count) }
  return , $held
}
function Exit-Agent9Slots($held) {
  foreach ($m in $held) { try { $m.ReleaseMutex() } catch { } }
}

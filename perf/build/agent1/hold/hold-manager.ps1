# Agent 1: sets perf-notes/WINDOW-HOLD.txt while a timed window runs, so agents stop even if Agent 1 is busy.
# A window = a new folder in build/agent8/matrix. Cleared when its summary.md appears, or when no game has
# run and nothing in the folder changed for 6 min. Runs until 07:30. Reads only; writes the HOLD file and its log.
$ErrorActionPreference = 'SilentlyContinue'
$w   = '<workspace>'
$m   = Join-Path $w 'build\agent8\matrix'
$h   = Join-Path $w 'perf-notes\WINDOW-HOLD.txt'
$log = Join-Path $w 'build\agent1\hold\hold-manager.log'
$end = [datetime]'2026-11-23T07:30:00'
function L([string]$t) { $s = '{0} {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $t; [IO.File]::AppendAllText($log, $s + "`n"); $s }
$known  = @(Get-ChildItem -LiteralPath $m -Directory | ForEach-Object Name)
$active = $null
L ('start: {0} matrix folders; HOLD file present: {1}' -f $known.Count, (Test-Path -LiteralPath $h))
while ((Get-Date) -lt $end) {
  if (-not $active) {
    $new = @(Get-ChildItem -LiteralPath $m -Directory | ForEach-Object Name | Where-Object { $known -notcontains $_ })
    if ($new.Count) {
      $known += $new
      $active = @($new | Sort-Object)[-1]   # @(): with one new folder, a bare string's [-1] is its last char ('6' at 17:56)
      [IO.File]::WriteAllText($h, ("HOLD since {0}: a timed window is running (build/agent8/matrix/{1}). Run no commands until this file is gone; Agent 1 sends a resume message.`n" -f (Get-Date -Format 'HH:mm:ss'), $active))
      L "HOLD set: $active"
    }
  } else {
    $d     = Join-Path $m $active
    $done  = Test-Path -LiteralPath (Join-Path $d 'summary.md')
    $lastF = Get-ChildItem -LiteralPath $d -File -Recurse | Sort-Object LastWriteTime | Select-Object -Last 1   # -Recurse: runs\ gets the per-second writes
    $game  = @(Get-Process -Name legodimensions -ErrorAction SilentlyContinue).Count
    $stale = ($game -eq 0) -and $lastF -and (((Get-Date) - $lastF.LastWriteTime).TotalMinutes -gt 6)
    if ($done -or $stale) {
      Remove-Item -LiteralPath $h -Force
      L ('HOLD cleared: {0} ({1})' -f $active, $(if ($done) { 'summary.md written' } else { 'stale: no game and no write for 6 min' }))
      $active = $null
    }
  }
  Start-Sleep -Seconds 5
}
L 'end (07:30)'

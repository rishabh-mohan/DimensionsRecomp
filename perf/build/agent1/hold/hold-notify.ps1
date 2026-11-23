# Agent 1: exits when perf-notes/WINDOW-HOLD.txt reaches the wanted state (present or absent), or at 07:30.
param([ValidateSet('present', 'absent')][string]$Want = 'present')
$h   = '<workspace>\perf-notes\WINDOW-HOLD.txt'
$end = [datetime]'2026-11-23T07:30:00'
'{0} waiting for HOLD {1}' -f (Get-Date -Format 'HH:mm:ss'), $Want
while ((Get-Date) -lt $end) {
  $p = Test-Path -LiteralPath $h
  if (($Want -eq 'present' -and $p) -or ($Want -eq 'absent' -and -not $p)) {
    '{0} HOLD {1}' -f (Get-Date -Format 'HH:mm:ss'), $Want
    if ($p) { Get-Content -LiteralPath $h }
    exit 0
  }
  Start-Sleep -Seconds 5
}
'{0} timeout' -f (Get-Date -Format 'HH:mm:ss')

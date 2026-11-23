# Agent 1: wakes me when W5 ends, without relying on the HOLD file (the hold manager took "matrix/6" as the
# window folder at 17:56:03). Light: one directory listing, one Test-Path and one Get-Process every 15 s; no WMI.
# W5 = the newest folder in build/agent8/matrix created after 17:50. Done when it has summary.md, or when no
# legodimensions process has existed for 5 min in a row (runner stopped). Exits at 07:30 at the latest.
$ErrorActionPreference = 'SilentlyContinue'
$m     = '<workspace>\build\agent8\matrix'
$since = [datetime]'2026-11-22T17:50:00'
$end   = [datetime]'2026-11-23T07:30:00'
'{0} folders created in matrix since 17:50:' -f (Get-Date -Format 'HH:mm:ss')
Get-ChildItem -LiteralPath $m -Directory | Where-Object CreationTime -gt $since | Sort-Object CreationTime | ForEach-Object {
  '  {0}  created {1:HH:mm:ss}  files: {2}' -f $_.Name, $_.CreationTime, ((Get-ChildItem -LiteralPath $_.FullName | Select-Object -First 8 | ForEach-Object Name) -join ', ')
}
$noGame = $null
while ((Get-Date) -lt $end) {
  $new = @(Get-ChildItem -LiteralPath $m -Directory | Where-Object CreationTime -gt $since | Sort-Object CreationTime)
  foreach ($d in $new) {
    if (Test-Path -LiteralPath (Join-Path $d.FullName 'summary.md')) { '{0} W5 done: {1}\summary.md exists' -f (Get-Date -Format 'HH:mm:ss'), $d.Name; exit 0 }
  }
  if (@(Get-Process -Name legodimensions).Count -eq 0) {
    if (-not $noGame) { $noGame = Get-Date }
    elseif (((Get-Date) - $noGame).TotalMinutes -ge 5) { '{0} no game process for 5 min and no summary.md (folders: {1})' -f (Get-Date -Format 'HH:mm:ss'), (($new | ForEach-Object Name) -join ', '); exit 2 }
  } else { $noGame = $null }
  Start-Sleep -Seconds 15
}
'{0} timeout (07:30)' -f (Get-Date -Format 'HH:mm:ss')

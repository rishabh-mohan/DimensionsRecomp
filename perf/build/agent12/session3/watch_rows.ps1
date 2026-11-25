# watch_rows.ps1 (M12, session 3): read-only event watcher for M3's session-3 rows.
# Exits (printing NEW: lines) as soon as an item not in watch-seen.txt exists:
#   - a run dir under build\agent3\runs with run.json (row finished), or
#   - a build\agent3\s4b\logs\<id>.check.txt / .f10.txt / .p2c.txt (postcheck output).
# Otherwise exits after -Minutes (TIMEOUT line). M12 appends processed items to watch-seen.txt itself.
# -Init records everything present now as seen and exits. Reads only; writes only watch-seen.txt on -Init.
param([int]$Minutes = 10, [int]$PollSec = 60, [switch]$Init)
$ErrorActionPreference = 'SilentlyContinue'
try { (Get-Process -Id $PID).PriorityClass = 'Idle' } catch { }
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$runs = Join-Path $repo 'build\agent3\runs'
$logs = Join-Path $repo 'build\agent3\s4b\logs'
$seenF = Join-Path $PSScriptRoot 'watch-seen.txt'
function Items {
  $a = @(Get-ChildItem -LiteralPath $runs -Directory | Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'run.json') } |
    ForEach-Object { 'run ' + $_.Name })
  $b = @(Get-ChildItem -LiteralPath $logs -File | Where-Object { $_.Name -match '\.(check|f10|p2c)\.txt$' } |
    ForEach-Object { 'log ' + $_.Name })
  $a + $b
}
if ($Init) { Items | Set-Content -LiteralPath $seenF -Encoding UTF8; "INIT $((Items).Count) items seen"; exit 0 }
$end = (Get-Date).AddMinutes($Minutes)
while ($true) {
  $seen = @{}; if (Test-Path -LiteralPath $seenF) { Get-Content -LiteralPath $seenF | ForEach-Object { $seen[$_] = 1 } }
  $new = @(Items | Where-Object { -not $seen.ContainsKey($_) })
  if ($new.Count) { Start-Sleep -Seconds 20; $new = @(Items | Where-Object { -not $seen.ContainsKey($_) }); $new | ForEach-Object { "NEW: $_" }; exit 0 }
  $g = @(Get-Process legodimensions* | ForEach-Object { "$($_.Name) pid $($_.Id) start $($_.StartTime.ToString('HH:mm:ss'))" })
  if ((Get-Date) -ge $end) { "TIMEOUT $(Get-Date -Format HH:mm:ss); game: $(if ($g.Count) { $g -join '; ' } else { 'none' })"; exit 0 }
  Start-Sleep -Seconds $PollSec
}

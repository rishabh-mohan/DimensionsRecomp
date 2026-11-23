# Agent 12, task #11 (2026-11-22): tests for p2c_check.py, make_fixtures.py and w6_env_record.py.
# Reads only, except the fixtures (build\agent12\p2c-check\fixtures\), the two JSON outputs and the
# results file. BelowNormal priority. Stops if perf-notes\WINDOW-HOLD.txt appears.
$ErrorActionPreference = 'Continue'
$w = '<workspace>'
Set-Location $w
if (Test-Path "$w\perf-notes\WINDOW-HOLD.txt") { 'HOLD EXISTS - not running'; exit 9 }
(Get-Process -Id $PID).PriorityClass = 'BelowNormal'
$p2c = 'build\agent12\p2c-check\p2c_check.py'
$mk  = 'build\agent12\p2c-check\make_fixtures.py'
$rec = 'build\agent12\w6-gates\w6_env_record.py'
$fx  = 'build\agent12\p2c-check\fixtures'
$ud  = 'build\agent3\runs\20261122-133730-s4a-udiag'
$out = 'build\agent12\p2c-check\test-results-{0}.txt' -f (Get-Date -Format 'yyyyMMdd-HHmmss')
$script:summary = @()
$script:bad = 0
function T([string]$Name, [int]$Want, [string[]]$Expect, [string[]]$A) {
  if (Test-Path "$w\perf-notes\WINDOW-HOLD.txt") { throw 'HOLD appeared - stopping' }
  $sw = [Diagnostics.Stopwatch]::StartNew()
  $o = (& python @A 2>&1 | Out-String)
  $code = $LASTEXITCODE
  $sw.Stop()
  $miss = @($Expect | Where-Object { $_ -and ($o -notmatch $_) })
  $ok = ($code -eq $Want) -and ($miss.Count -eq 0)
  if (-not $ok) { $script:bad++ }
  $hdr = '{0} {1} (exit {2}, want {3}; {4:N1} s): python {5}' -f $(if ($ok) { 'PASS' } else { 'FAIL' }), $Name, $code, $Want, $sw.Elapsed.TotalSeconds, ($A -join ' ')
  if ($miss.Count) { $hdr += "`r`n  missing: " + ($miss -join ' | ') }
  Add-Content -Path $out -Value ($hdr + "`r`n" + $o)
  $script:summary += $hdr
  $hdr
  (($o.TrimEnd() -split "`r?`n") | Select-Object -Last 8 | ForEach-Object { '    ' + $_ }) -join "`r`n"
}
"tests start $(Get-Date -Format o); python: $((Get-Command python).Source)"
"u-diag logs: " + ((Get-ChildItem $ud -File | Where-Object { $_.Name -match '\.log$|^log\.txt$' } | ForEach-Object { '{0} {1:N1} MB' -f $_.Name, ($_.Length / 1MB) }) -join ', ')
T 'p2c selftest' 0 @('SELFTEST PASS \(24/24 checks\)') @($p2c, '--selftest')
T 'S4a u-diag, real log (S4a has no s4-p2c)' 3 @('RESULT: NO DATA: \d+ slow-frame lines, none with the counter field: this build has no s4-p2c', 'memexport ', 'process 1 \(started game\.8\.log:29\): frames #2\.\.#75014') @($p2c, $ud)
T 'S4a attract u-diag, real log' 3 @('this build has no s4-p2c') @($p2c, 'build\agent3\runs\20261122-140637-s4a-udiag-attract')
T 'W5 timed run s0-r1, real log (no slow_frame_log_ms)' 3 @('no slow-frame lines: slow_frame_log_ms was not set') @($p2c, 'build\agent8\matrix\20261122-1756\runs\1800-s0-r1')
T 'missing run dir' 3 @('RESULT: NO DATA: not found') @($p2c, 'build\agent3\runs\no-such-run')
T 'usage error, no args' 2 @() @($p2c)
T '--bin on the S4a bin devoff4' 3 @('bin: the counter.s format string is in none of the \d+ \.exe/\.dll files') @($p2c, $ud, '--bin', 'build\agent2\devoff4-bin')
T 'make real-format fixtures from the u-diag log' 0 @('pass: ', 'fail: .*final T 5', 'cut: ') @($mk, $ud, $fx)
T 'fixture pass (real lines + field, F 0 T 0)' 0 @('RESULT: PASS \(total 0\)', 'T = 0: F on logged lines 0, in frames not logged 0') @($p2c, "$fx\pass", '--json', "$fx\pass.json")
T 'fixture fail (F 2 at slow line 10, +3 unlogged at 20)' 1 @('RESULT: FAIL \(total 5\)', 'T = 5: F on logged lines 2, in frames not logged 3', 'first T > 0: .*F 2, T 2', 'logged frames with F > 0: 1, max F 2') @($p2c, "$fx\fail")
T 'fixture cut (last line without the field)' 0 @('RESULT: PASS \(total 0\)', 'cut off at exit') @($p2c, "$fx\cut")
T 'w6_env_record selftest' 0 @('SELFTEST PASS \(12/12 checks\)') @($rec, '--selftest')
T 'w6_env_record on W5 + quiet-1731.log' 0 @('RECORD: overlay best_efficiency \(16/16, no change\); quiet gate RELAXED', 'NOT QUIET after 20 min', 'non-game load flag \(scored runs above the median 3\.30 \+ 1\.0 cores\): none') @($rec, 'build\agent8\matrix\20261122-1756', '--gate-log', 'build\agent1\w5\quiet-1731.log', '--json', 'build\agent12\w6-gates\w5-env-record.json')
"=== summary: $($script:summary.Count - $script:bad)/$($script:summary.Count) PASS; results in $out ==="
Add-Content -Path $out -Value ("=== summary ===`r`n" + ($script:summary -join "`r`n"))
exit $script:bad

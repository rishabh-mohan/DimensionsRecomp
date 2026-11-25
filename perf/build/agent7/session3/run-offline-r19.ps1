param([string]$Only = '')
# M7 S3T-7: selftest + offline r19_gate runs, BelowNormal, one at a time. Writes only build\agent7\session3\*.out.txt
Set-Location '<workspace>'
$s = 'build\agent7\session3'
$r = 'build\agent3\runs'
function Run1([string[]]$a, [string]$o) {
  $p = Start-Process python -ArgumentList $a -NoNewWindow -PassThru -RedirectStandardOutput $o -RedirectStandardError "$o.err"
  $h = $p.Handle; $p.PriorityClass = 'BelowNormal'; $p.WaitForExit()
  "{0} exit {1}: {2}" -f $o, $p.ExitCode, ((Get-Content $o | Select-Object -Last 1) -join '')
  $e = Get-Content "$o.err" -Raw; if ($e) { "  STDERR: $e" } else { Remove-Item "$o.err" }
}
Run1 @('-B', "$s\test_r19.py") "$s\selftest-r19.out.txt"
Run1 @('-B', "$s\check_queue_r19.py") "$s\check_queue_r19.out.txt"
Run1 @('-B', "$s\r19_gate.py", "$r\20261122-205356-s4b-01-off", '--row', 'a') "$s\offline-a-s4b01.out.txt"
Run1 @('-B', "$s\r19_gate.py", "$r\20261125-014556-cg26b0-boot-menus", '--row', 'a') "$s\offline-a-cg26b0.out.txt"
Run1 @('-B', "$s\r19_gate.py", "$r\20261125-014239-s4b-N16-title-split16", '--row', 'a') "$s\offline-a-N16.out.txt"
Run1 @('-B', "$s\r19_gate.py", "$r\20261125-014239-s4b-N16-title-split16", '--row', 'i', '--n', '16') "$s\offline-i-N16.out.txt"
Run1 @('-B', "$s\r19_gate.py", "$r\20261125-014239-s4b-N16-title-split16", '--row', 'd', '--n', '16') "$s\offline-d-N16.out.txt"
Run1 @('-B', "$s\r19_gate.py", "$r\20261122-210059-s4b-L0-off-level", '--row', 'b') "$s\offline-b-L0.out.txt"
Run1 @('-B', "$s\r19_gate.py", "$r\20261122-210059-s4b-L0-off-level", '--row', 'e') "$s\offline-e-L0.out.txt"

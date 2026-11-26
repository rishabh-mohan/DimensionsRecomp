# E10.2 review prep: rerun M12's selftests and test-run invocations from a COPY of the scripts (outputs stay here).
$ws = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$d = $PSScriptRoot
$b = "$ws\build\agent8\session3\smoke-final2\runs"; $r = "$ws\build\agent3\runs"
$route = "$ws\harness\routes\attract-long.txt"
function RunG($argList, $o) {
    $p = Start-Process python -ArgumentList $argList -WorkingDirectory $ws -RedirectStandardOutput "$o.txt" -RedirectStandardError "$o.err.txt" -NoNewWindow -PassThru
    $null = $p.Handle; try { $p.PriorityClass = 'BelowNormal' } catch {}
    $p.WaitForExit(); "$(Split-Path $o -Leaf) exit $($p.ExitCode)"
}
RunG @('-B', "$d\s5_gates.py", '--selftest') "$d\out-gates-selftest"
RunG @('-B', "$d\s5_readout.py", '--selftest') "$d\out-readout-selftest"
foreach ($sp in 120, 110, 60) {
    RunG @('-B', "$d\s5_gates.py", "$b\20261125-164755-final2-3d-xenos", "$b\20261125-165219-final2-3d-native", '--span', $sp, '--cap', 'none', '--native-default-ok', '--route', $route, '--json', "$d\out-gates-smoke-span$sp.json") "$d\out-gates-smoke-span$sp"
}
foreach ($cp in 'auto', '60') {
    RunG @('-B', "$d\s5_gates.py", "$b\20261125-164755-final2-3d-xenos", "$b\20261125-165219-final2-3d-native", '--span', 110, '--cap', $cp, '--route', $route, '--json', "$d\out-gates-smoke-span110-cap$cp.json") "$d\out-gates-smoke-span110-cap$cp"
}
foreach ($sp in 120, 180) {
    RunG @('-B', "$d\s5_gates.py", "$r\20261125-071741-s33-offsf", "$r\20261125-123609-s33-ond", '--span', $sp, '--cap', 'none', '--route', $route, '--json', "$d\out-gates-offsf-ond-span$sp.json") "$d\out-gates-offsf-ond-span$sp"
}
RunG @('-B', "$d\s5_readout.py", "$d\out-gates-smoke-span110.json", '--json', "$d\out-readout-smoke-span110.json") "$d\out-readout-smoke-span110"

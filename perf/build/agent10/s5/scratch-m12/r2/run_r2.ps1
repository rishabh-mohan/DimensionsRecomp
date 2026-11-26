# E10.2 r2 cross-check: run M12's new scripts from COPIES in this folder, one python at a time, Idle priority.
param([ValidateSet('gself', 'rself', 'synth')][string]$Which)
$ws = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
$d = $PSScriptRoot
$route = "$ws\harness\routes\attract-long.txt"
function RunG($argList, $o) {
    $p = Start-Process python -ArgumentList $argList -WorkingDirectory $ws -RedirectStandardOutput "$o.txt" -RedirectStandardError "$o.err.txt" -NoNewWindow -PassThru
    $null = $p.Handle; try { $p.PriorityClass = 'Idle' } catch {}
    $p.WaitForExit(); "$(Split-Path $o -Leaf) exit $($p.ExitCode)"
}
switch ($Which) {
    'gself' { RunG @('-B', "$d\s5_gates.py", '--selftest') "$d\out-gates-selftest" }
    'rself' { RunG @('-B', "$d\s5_readout.py", '--selftest') "$d\out-readout-selftest" }
    'synth' { RunG @('-B', "$d\s5_gates.py", "$ws\build\agent10\s5\scratch-m12\synth\20261125-165219-final2-3d-native", '--span', 110, '--cap', 'none', '--native-default-ok', '--route', $route, '--json', "$d\out-gates-synth-native.json") "$d\out-gates-synth-native" }
}

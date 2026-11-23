# run-a7.ps1 (Agent 8, task #20): make the pooled pseudo dirs, then run Agent 7's readout.py (read-only, Below Normal)
# on every pass and pool, one process at a time. Stops before the next step if perf-notes\WINDOW-HOLD.txt appears.
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
$hold = 'perf-notes\WINDOW-HOLD.txt'
if (Test-Path -LiteralPath $hold) { "not started: $hold exists"; exit 2 }
(Get-Process -Id $PID).PriorityClass = 'BelowNormal'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONIOENCODING = 'utf-8'
$M = 'build\agent8\matrix'
$O = 'build\agent8\readout\w-followup'
$P = "$O\pool"
$A = "$O\a7"
New-Item -ItemType Directory -Force $P, $A | Out-Null
$failed = @()
function Step([string]$name, [string]$cmd, [string]$log) {
    if (Test-Path -LiteralPath $hold) { "stopped before ${name}: $hold appeared"; $script:failed += "$name (hold)"; return }
    $t0 = Get-Date
    cmd /c "$cmd > `"$log`" 2>&1"
    $rc = $LASTEXITCODE
    '{0,-14} exit {1}  {2,6:N1} s  {3}' -f $name, $rc, ((Get-Date) - $t0).TotalSeconds, $log
    if ($rc -ne 0) { $script:failed += $name }
}
"start $(Get-Date -Format 'HH:mm:ss')"
Step 'pool-W6'  "python -B $O\scripts\make_pool.py $P\W6 $M\20261123-0009 $M\20261123-0313" "$P\W6.log"
Step 'pool-W9'  "python -B $O\scripts\make_pool.py $P\W9 $M\20261123-0108 $M\20261123-0401" "$P\W9.log"
Step 'pool-W5b' "python -B $O\scripts\make_pool.py $P\W5b $M\20261123-0155 $M\20261123-0451" "$P\W5b.log"
$targets = [ordered]@{
    'W6-pool' = "$P\W6"; 'W6-p1' = "$M\20261123-0009"; 'W6-p2' = "$M\20261123-0313"; 'W4c' = "$M\20261123-0239";
    'W9-pool' = "$P\W9"; 'W9-p1' = "$M\20261123-0108"; 'W9-p2' = "$M\20261123-0401";
    'W5b-pool' = "$P\W5b"; 'W5b-p1' = "$M\20261123-0155"; 'W5b-p2' = "$M\20261123-0451"
}
foreach ($k in $targets.Keys) {
    Step $k "python -B build\agent7\w4b-noise\readout.py $($targets[$k]) -o $A\$k.md --json $A\$k.json" "$A\$k.log"
}
if ($failed.Count) { "FAILED: $($failed -join ', ')"; exit 1 }
"done $(Get-Date -Format 'HH:mm:ss')"

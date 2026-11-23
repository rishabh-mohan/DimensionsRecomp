# run-var2.ps1 (Agent 8, task #20): the "without the sys.csv-flagged runs" variants from audit/audit.md section 2.
# W6: drop 0023-p2fc-r2 + 0025-s0-r2 (W6-1 flags), 0339-p2fc-r4 (W6-2 flag) and 0352-p2f-r5 (the 45.67 ms burst).
# W4c: drop 0253-B-r4 (the only W4c flag). Read-only on the matrix folders, Below Normal, HOLD-checked per step.
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
$hold = 'perf-notes\WINDOW-HOLD.txt'
if (Test-Path -LiteralPath $hold) { "not started: $hold exists"; exit 2 }
(Get-Process -Id $PID).PriorityClass = 'BelowNormal'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONIOENCODING = 'utf-8'
$M = 'build\agent8\matrix'
$O = 'build\agent8\readout\w-followup'
$S = "$O\scripts\pool_readout.py"
$R7 = 'build\agent7\w4b-noise\readout.py'
$failed = @()
function Step([string]$name, [string]$cmd, [string]$log) {
    if (Test-Path -LiteralPath $hold) { "stopped before ${name}: $hold appeared"; $script:failed += "$name (hold)"; return }
    cmd /c "$cmd > `"$log`" 2>&1"
    $rc = $LASTEXITCODE
    '{0,-22} exit {1}  {2}' -f $name, $rc, ((Get-Content -LiteralPath $log -TotalCount 1) -join '')
    if ($rc -ne 0) { $script:failed += $name }
}
$W6 = "$M\20261123-0009 $M\20261123-0313"
$fl6 = '0023-p2fc-r2,0025-s0-r2,0339-p2fc-r4,0352-p2f-r5'
$W4 = "$M\20261123-0239"
Step 'W6-noAudit'  "python -B $S --name W6 --base s0 --contrast p2fc-p2f --contrast p2f-p2 --tails --drop $fl6 --md $O\mine\W6-noAudit.md --json $O\mine\W6-noAudit.json $W6" "$O\mine\W6-noAudit.log"
Step 'W4c-noFlag'  "python -B $S --name W4c --base d0 --tails --drop 0253-B-r4 --md $O\mine\W4c-noFlag.md --json $O\mine\W4c-noFlag.json $W4" "$O\mine\W4c-noFlag.log"
Step 'a7:W6-pool-noAudit' "python -B $R7 $O\pool\W6 --drop $fl6 -o $O\a7\W6-pool-noAudit.md --json $O\a7\W6-pool-noAudit.json" "$O\a7\W6-pool-noAudit.log"
Step 'a7:W4c-noFlag' "python -B $R7 $W4 --drop 0253-B-r4 -o $O\a7\W4c-noFlag.md --json $O\a7\W4c-noFlag.json" "$O\a7\W4c-noFlag.log"
if ($failed.Count) { "FAILED: $($failed -join ', ')"; exit 1 }
"done $(Get-Date -Format 'HH:mm:ss')"

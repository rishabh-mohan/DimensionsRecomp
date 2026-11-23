# run-mine.ps1 (Agent 8, task #20): pool_readout.py on W6 / W4c / W9 / W5b plus the sensitivity variants, and
# Agent 7's readout.py on the same variants. Read-only on the matrix folders, Below Normal, HOLD-checked per step.
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
New-Item -ItemType Directory -Force "$O\mine", "$O\a7" | Out-Null
$failed = @()
function Step([string]$name, [string]$cmd, [string]$log) {
    if (Test-Path -LiteralPath $hold) { "stopped before ${name}: $hold appeared"; $script:failed += "$name (hold)"; return }
    cmd /c "$cmd > `"$log`" 2>&1"
    $rc = $LASTEXITCODE
    '{0,-18} exit {1}  {2}' -f $name, $rc, ((Get-Content -LiteralPath $log -TotalCount 1) -join '')
    if ($rc -ne 0) { $script:failed += $name }
}
$W6 = "$M\20261123-0009 $M\20261123-0313"
$W6c = '--name W6 --base s0 --contrast p2fc-p2f --contrast p2f-p2 --tails'
$ep6 = '0325-p2f-r2,0327-p2fc-r2,0329-s0-r2,0331-p2f-r3,0333-p2fc-r3,0335-s0-r3,0337-p2-r3,0339-p2fc-r4'
$ep4 = '0251-B-r3,0253-B-r4'
$jobs = [ordered]@{
    'W6'            = "$W6c"
    'W6-no0352'     = "$W6c --drop 0352-p2f-r5"
    'W6-noR1'       = "$W6c --drop-rounds 1"
    'W6-noEpisode'  = "$W6c --drop $ep6"
    'W6-noR1-noEp'  = "$W6c --drop-rounds 1 --drop $ep6,0352-p2f-r5"
}
foreach ($k in $jobs.Keys) { Step $k "python -B $S $($jobs[$k]) --md $O\mine\$k.md --json $O\mine\$k.json $W6" "$O\mine\$k.log" }
$W4 = "$M\20261123-0239"
$jobs = [ordered]@{
    'W4c'           = '--name W4c --base d0 --tails'
    'W4c-noR1'      = '--name W4c --base d0 --tails --drop-rounds 1'
    'W4c-noEpisode' = "--name W4c --base d0 --tails --drop $ep4"
    'W4c-noR1-noEp' = "--name W4c --base d0 --tails --drop-rounds 1 --drop $ep4"
}
foreach ($k in $jobs.Keys) { Step $k "python -B $S $($jobs[$k]) --md $O\mine\$k.md --json $O\mine\$k.json $W4" "$O\mine\$k.log" }
Step 'W9'       "python -B $S --name W9 --base off --md $O\mine\W9.md --json $O\mine\W9.json $M\20261123-0108 $M\20261123-0401" "$O\mine\W9.log"
Step 'W9-noR1'  "python -B $S --name W9 --base off --drop-rounds 1 --md $O\mine\W9-noR1.md --json $O\mine\W9-noR1.json $M\20261123-0108 $M\20261123-0401" "$O\mine\W9-noR1.log"
Step 'W5b'      "python -B $S --name W5b --base d11 --md $O\mine\W5b.md --json $O\mine\W5b.json $M\20261123-0155 $M\20261123-0451" "$O\mine\W5b.log"
Step 'W5b-noR1' "python -B $S --name W5b --base d11 --drop-rounds 1 --md $O\mine\W5b-noR1.md --json $O\mine\W5b-noR1.json $M\20261123-0155 $M\20261123-0451" "$O\mine\W5b-noR1.log"
# Agent 7's readout.py on the same variants (pool dirs from run-a7.ps1; pool rounds: pass 2 round r = r + 5 for W6)
$P = "$O\pool"
$a7 = [ordered]@{
    'W6-pool-no0352' = "$P\W6 --drop 0352-p2f-r5"
    'W6-pool-noR1'   = "$P\W6 --rounds 2,3,4,5,7,8,9,10"
    'W6-pool-noEp'   = "$P\W6 --drop $ep6"
    'W4c-noR1'       = "$W4 --rounds 2,3,4,5,6"
    'W4c-noEp'       = "$W4 --drop $ep4"
}
foreach ($k in $a7.Keys) { Step "a7:$k" "python -B $R7 $($a7[$k]) -o $O\a7\$k.md --json $O\a7\$k.json" "$O\a7\$k.log" }
if ($failed.Count) { "FAILED: $($failed -join ', ')"; exit 1 }
"done $(Get-Date -Format 'HH:mm:ss')"

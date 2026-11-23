# run-var3.ps1 (Agent 8, task #20): W9 / W5b without the sys.csv-flagged runs (audit/audit.md section 2), plus
# Agent 7's readout.py without round 1 on the W9 / W5b pools, for the check of Agent 7's W9/W5b headline numbers.
# Read-only on the matrix folders, Below Normal, HOLD-checked per step.
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
$P = "$O\pool"
$failed = @()
function Step([string]$name, [string]$cmd, [string]$log) {
    if (Test-Path -LiteralPath $hold) { "stopped before ${name}: $hold appeared"; $script:failed += "$name (hold)"; return }
    cmd /c "$cmd > `"$log`" 2>&1"
    $rc = $LASTEXITCODE
    '{0,-22} exit {1}  {2}' -f $name, $rc, ((Get-Content -LiteralPath $log -TotalCount 1) -join '')
    if ($rc -ne 0) { $script:failed += $name }
}
$p9 = @("$M\20261123-0108", "$M\20261123-0401")
$p5 = @("$M\20261123-0155", "$M\20261123-0451")
# audit section 2 flags: W9-1 0122/0124, W9-2 0407/0409/0417/0423; W5b-1 0209/0213, W5b-2 0453/0455/0457/0510
$fl9 = '0122-q125-r2,0124-q250-r2,0407-q125-r1,0409-q250-r1,0417-q250-r2,0423-q125-r3'
$fl5 = '0209-d11p-r3,0213-d11t-r3,0453-d11-r1,0455-d11t-r1,0457-d11p-r1,0510-d11t-r3'
foreach ($pair in @(@($fl9, $p9), @($fl5, $p5))) {
    foreach ($n in $pair[0].Split(',')) {
        $hit = @($pair[1] | Where-Object { Select-String -LiteralPath "$_\results.csv" -SimpleMatch $n -Quiet })
        if ($hit.Count -ne 1) { "drop name $n found in $($hit.Count) pass folders"; exit 3 }
    }
}
"drop names OK"
$W9 = $p9 -join ' '
$W5 = $p5 -join ' '
Step 'W9-noFlag'       "python -B $S --name W9 --base off --drop $fl9 --md $O\mine\W9-noFlag.md --json $O\mine\W9-noFlag.json $W9" "$O\mine\W9-noFlag.log"
Step 'W9-noR1-noFlag'  "python -B $S --name W9 --base off --drop-rounds 1 --drop $fl9 --md $O\mine\W9-noR1-noFlag.md --json $O\mine\W9-noR1-noFlag.json $W9" "$O\mine\W9-noR1-noFlag.log"
Step 'W5b-noFlag'      "python -B $S --name W5b --base d11 --drop $fl5 --md $O\mine\W5b-noFlag.md --json $O\mine\W5b-noFlag.json $W5" "$O\mine\W5b-noFlag.log"
Step 'W5b-noR1-noFlag' "python -B $S --name W5b --base d11 --drop-rounds 1 --drop $fl5 --md $O\mine\W5b-noR1-noFlag.md --json $O\mine\W5b-noR1-noFlag.json $W5" "$O\mine\W5b-noR1-noFlag.log"
# Agent 7's readout.py on the pools (make_pool.py): round 1 of each pass = pool rounds 1 and offset+1
foreach ($w in 'W9', 'W5b') {
    $pj = Get-Content -LiteralPath "$P\$w\pool.json" -Raw | ConvertFrom-Json
    $skip = @(1, ([int]$pj.passes[1].round_offset + 1))
    $keep = (1..([int]$pj.rounds) | Where-Object { $skip -notcontains $_ }) -join ','
    "$w pool: $($pj.rounds) rounds, pass-2 offset $($pj.passes[1].round_offset), noR1 keeps $keep"
    $fl = if ($w -eq 'W9') { $fl9 } else { $fl5 }
    Step "a7:$w-pool-noFlag" "python -B $R7 $P\$w --drop $fl -o $O\a7\$w-pool-noFlag.md --json $O\a7\$w-pool-noFlag.json" "$O\a7\$w-pool-noFlag.log"
    Step "a7:$w-pool-noR1"   "python -B $R7 $P\$w --rounds $keep -o $O\a7\$w-pool-noR1.md --json $O\a7\$w-pool-noR1.json" "$O\a7\$w-pool-noR1.log"
}
if ($failed.Count) { "FAILED: $($failed -join ', ')"; exit 1 }
"done $(Get-Date -Format 'HH:mm:ss')"

# postcheck.ps1 - Agent 3 S4a (task #5): runs s4a_check.py for each run the queue finishes (reads queue-state.jsonl).
# Read-only on run dirs; writes build\agent3\s4a\checks\<run>.{txt,json} and logs\<id>.check.txt. Ends at -Until.
param([string]$Until = '14:55:00')
$ErrorActionPreference = 'Continue'
$here = $PSScriptRoot
$repo = (Resolve-Path (Join-Path $here '..\..\..')).Path
Set-Location $repo
$state = Join-Path $here 'queue-state.jsonl'
$logs = Join-Path $here 'logs'
$runs = 'build\agent3\runs'
$ref = "$runs\20261122-131206-s4a-ref-devoff3"
$nref = "$runs\20261122-055439-bgate-rev-native3d"
$u2 = "$runs\20261122-131746-s102-r2-warm-devoff3"
$tOn = Join-Path $repo 'build\agent3\s4a\trace\r6on-t'
$tOff = Join-Path $repo 'build\agent3\s4a\trace\r6off-t'
$end = [datetime]::Today.Add([timespan]::Parse($Until))
$seen = @{}
function Say([string]$m) { Write-Host ((Get-Date -Format 'HH:mm:ss') + ' ' + $m) }
function Check([string]$id, [string[]]$a) {
    & python build\agent3\s4a\s4a_check.py @a *> (Join-Path $logs "$id.check.txt")
    Say "checked $id (exit $LASTEXITCODE): $($a -join ' ')"
}
while ((Get-Date) -lt $end) {
    if (Test-Path -LiteralPath $state) {
        $recs = @(Get-Content -LiteralPath $state | Where-Object { $_.Trim() } | ForEach-Object { $_ | ConvertFrom-Json })
        $by = @{}
        foreach ($r in $recs) { if ($r.run) { $by[$r.id] = "$runs\$($r.run)" } }
        function B([string]$id, [string]$fb) { if ($by.ContainsKey($id)) { $by[$id] } else { $fb } }
        foreach ($r in $recs) {
            if (-not $r.run -or $seen.ContainsKey($r.id)) { continue }
            $seen[$r.id] = 1
            if (Test-Path -LiteralPath (Join-Path $logs "$($r.id).check.txt")) { continue }  # checked by an earlier postcheck
            $c = "$runs\$($r.run)"
            $r1 = B 'r1' $ref
            switch -Regex ($r.id) {
                '^r1$' { Check 'r1' @('--cand', $c, '--base', $ref) }
                '^r2$' { Check 'r2' @('--cand', $c, '--base', $r1, '--allow-new', 'S4 upload hash|slow frame') }
                '^(r3|r7)$' { Check $r.id @('--cand', $c, '--base', $r1, '--base', $ref) }
                '^r4$' { Check 'r4' @('--cand', $c, '--base', $r1, '--tq-ref', $r1) }
                '^r5$' { Check 'r5' @('--cand', $c, '--base', $nref) }
                '^r6on$' { Check 'r6on' @('--cand', $c, '--base', (B 'r5' $nref)) }
                '^r6off$' {
                    Check 'r6off' @('--cand', $c, '--base', (B 'r5' $nref))
                    if ($by.ContainsKey('r6on')) {
                        Check 'r6on-vs-r6off' @('--cand', $by['r6on'], '--base', $c, '--out-dir', 'build\agent3\s4a\checks\vs-trace-off')
                        & python build\agent4\r2t6\mc_smoke_check.py --off $c --on $by['r6on'] --off-trace $tOff --on-trace $tOn *> (Join-Path $logs 'r6-mc_smoke_check.txt')
                        Say "mc_smoke_check exit $LASTEXITCODE"
                        & python build\agent10\nb\warntypes.py --run "OFF=$c" --run "ON=$($by['r6on'])" *> (Join-Path $logs 'r6-warntypes.txt')
                        Say "warntypes exit $LASTEXITCODE"
                    }
                }
                '^r3n$' { Check 'r3n' @('--cand', $c, '--base', (B 'r5' $nref)) }
                '^U4$' { Check 'U4' @('--cand', $c, '--base', $u2) }
                '^F4$' { Check 'F4' @('--cand', $c, '--base', (B 'U4' $u2)) }
                '^(F3a|F3b|F3c|F3d|F1t|F2)$' { Check $r.id @('--cand', $c, '--base', $u2) }
                default { Check $r.id @('--cand', $c) }
            }
        }
    }
    Start-Sleep -Seconds 10
}
Say 'postcheck ends'

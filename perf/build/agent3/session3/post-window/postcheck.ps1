# postcheck.ps1 - Agent 3 S4b (task #29): runs s4b_check.py for each run s4b-queue.ps1 finishes (reads
# queue-state.jsonl; records without a run or with "aborted" are passed over). No python while
# perf-notes\WINDOW-HOLD.txt exists (a user timing window). Read-only on run dirs; writes build\agent3\s4b\checks\
# <run>.{txt,json} (joined\<run>\game.log for runs with rotated logs) and logs\<id>.check.txt. Ends at -Until.
# Bases and allowed NEW families per row: build/agent7/s4b-queue/QUEUE.md (a base row that has no run yet falls back
# to the S4a reference).
param([string]$Until = '23:59:00')
$ErrorActionPreference = 'Continue'
$here = $PSScriptRoot
$repo = (Resolve-Path (Join-Path $here '..\..\..')).Path
Set-Location $repo
# Below Normal for itself, so the python checks it starts (which inherit it) never compete with the game
try { (Get-Process -Id $PID).PriorityClass = 'BelowNormal' } catch { }
$state = Join-Path $here 'queue-state.jsonl'
$logs = Join-Path $here 'logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$hold = Join-Path $repo 'perf-notes\WINDOW-HOLD.txt'
$runs = 'build\agent3\runs'
$R1 = "$runs\20261122-133333-s4a-r1-off-devoff4"     # S4a r1 OFF devoff4 (PASS)
$REF = "$runs\20261122-131206-s4a-ref-devoff3"       # S4a reference devoff3
$RN = "$runs\20261122-141355-s4a-r5-off-native4"     # S4a r5 OFF native4 (the passing re-run)
$N3D = "$runs\20261122-055439-bgate-rev-native3d"    # B-gate native3d
$RA = "$runs\20261122-140637-s4a-udiag-attract"      # S4a attract, u-diag cvars (4 rotated logs)
$RT = "$runs\20261122-133730-s4a-udiag"              # S4a title, uncapped, u-diag cvars (9 rotated logs)
$LX2 = "$runs\20261122-201420-lx2-devoff4"           # run-2 L-route exploration on devoff4 (OFF), exit 0 (route level-explore-2)
$end = [datetime]::Today.Add([timespan]::Parse($Until))
$seen = @{}
function Say([string]$m) {
    # also to logs\postcheck.out.txt (build\agent3\s4b\wait-event.ps1 reads it)
    $l = (Get-Date -Format 'HH:mm:ss') + ' ' + $m; Write-Host $l
    try { Add-Content -LiteralPath (Join-Path $logs 'postcheck.out.txt') -Value $l -Encoding UTF8 } catch { }
}
function Check([string]$id, [string[]]$a) {
    while (Test-Path -LiteralPath $hold) { Start-Sleep -Seconds 10 }
    & python build\agent3\s4b\s4b_check.py --row $id @a *> (Join-Path $logs "$id.check.txt")
    Say "checked $id (exit $LASTEXITCODE): $($a -join ' ')"
}
# run-2 task 2: P2's fallback counter (G4/R6) with Agent 12's build\agent12\p2c-check\p2c_check.py on every row that has
# slow_frame_log_ms=1 (s4b08*, s4b23, w6*): logs\<id>.p2c.txt (last line RESULT: ...) and logs\<id>.p2c.json.
# Exit 0 = PASS (total 0), 1 = FAIL, 3 = NO DATA/PARTIAL, 4 = ERROR.
function P2c([string]$id, [string]$run) {
    while (Test-Path -LiteralPath $hold) { Start-Sleep -Seconds 10 }
    & python -B build\agent12\p2c-check\p2c_check.py $run --json (Join-Path $logs "$id.p2c.json") *> (Join-Path $logs "$id.p2c.txt")
    Say "p2c $id (exit $LASTEXITCODE): $run"
}
# session 3 (M3): the strict finding-10 rule (build\agent3\session3\f10_rule.py) on the L-route rows: logs\<id>.f10.txt
# (last line RESULT: PASS/WARN/FAIL) and logs\<id>.f10.json. Exit 0 = PASS, 1 = WARN (finding 10 only), 2 = FAIL, 4 = ERROR.
function F10([string]$id, [string]$run) {
    while (Test-Path -LiteralPath $hold) { Start-Sleep -Seconds 10 }
    & python -B build\agent3\session3\f10_rule.py $run --json (Join-Path $logs "$id.f10.json") *> (Join-Path $logs "$id.f10.txt")
    Say "f10 $id (exit $LASTEXITCODE): $run"
}
# 01:58 (M10 review N3): the Window C / CG26 proof lines (build\agent3\session3\wc_proof.py) on win3f, c1npf, cg26b0,
# cg26L: logs\<id>.wc.txt (last line RESULT: PASS/MISS). Exit 0 = PASS, 1 = a proof miss, 2 = usage.
function WC([string]$id, [string]$run, [string]$arm) {
    while (Test-Path -LiteralPath $hold) { Start-Sleep -Seconds 10 }
    & python -B build\agent3\session3\wc_proof.py $run $arm *> (Join-Path $logs "$id.wc.txt")
    Say "wc $id $arm (exit $LASTEXITCODE): $run"
}
# post-window (M3): #33 row 1a/1b with Agent 6's kit (build\agent6\s33-popin\TESTPLAN.md): RUN-S33-LOGDIFF.cmd, ref = the
# OFF arm, never --allow-new for no_wait; the sf row also gets s33_fields.py. Writes logs\<id>.s33.txt and
# checks\s33-row1a|s33-row1b\. Exit codes as the kit's (0 = PASS).
function S33([string]$id, [string]$bArm, [string]$bRun, [string]$oArm, [string]$oRun) {
    while (Test-Path -LiteralPath $hold) { Start-Sleep -Seconds 10 }
    $f = Join-Path $logs "$id.s33.txt"
    if (-not $bRun) { Say "s33 $id SKIP: no $bArm run"; "SKIP: no $bArm run" | Set-Content -LiteralPath $f; return }
    $row = if ($oArm -eq 'off') { 's33-row1a' } else { 's33-row1b' }
    & cmd /c build\agent6\s33-popin\RUN-S33-LOGDIFF.cmd --run "$bArm=$bRun" --run "$oArm=$oRun" --ref $oArm `
        --matrix-json build\agent6\s33-popin\harness-s33.json --out "build\agent3\s4b\checks\$row" *> $f
    $x = $LASTEXITCODE
    if ($oArm -eq 'offsf') {
        & python -B build\agent6\s33-popin\s33_fields.py --arm "offsf=$oRun" --out (Join-Path $logs "$id.s33fields.txt") *>> $f
        $x = "$x/fields $LASTEXITCODE"
    }
    Say "s33 $id $row (exit $x): $bRun vs $oRun"
}
while ((Get-Date) -lt $end) {
    if (Test-Path -LiteralPath $hold) { Start-Sleep -Seconds 10; continue }
    if (Test-Path -LiteralPath $state) {
        $recs = @(Get-Content -LiteralPath $state | Where-Object { $_.Trim() } | ForEach-Object { $_ | ConvertFrom-Json } |
            Where-Object { $_.run -and -not $_.aborted })
        $by = @{}
        foreach ($r in $recs) { $by[[string]$r.id] = "$runs\$($r.run)" }
        function B([string]$id, [string]$fb) { if ($by.ContainsKey($id)) { $by[$id] } else { $fb } }
        foreach ($r in $recs) {
            $id = [string]$r.id
            if ($seen.ContainsKey($id)) { continue }
            $seen[$id] = 1
            if (Test-Path -LiteralPath (Join-Path $logs "$id.check.txt")) { continue }  # checked by an earlier postcheck
            $c = "$runs\$($r.run)"
            $b1 = B 's4b01' $R1
            switch -Regex ($id) {
                '^s4b01$' { Check $id @('--cand', $c, '--base', $R1, '--base', $REF) }
                '^s4b02$' { Check $id @('--cand', $c, '--base', $RN, '--base', $N3D) }
                '^s4b03$' { Check $id @('--cand', $c, '--base', $RA) }
                '^s4b04$' { Check $id @('--cand', $c, '--base', $b1, '--allow-new', 'C1 keep-watch|C1 verify') }
                '^s4b06$' { Check $id @('--cand', $c, '--base', $b1, '--allow-new', 'C1 keep-watch') }
                '^s4b05$' { Check $id @('--cand', $c, '--base', (B 's4b02' $RN), '--allow-new', 'C1 keep-watch') }
                '^s4b08' { Check $id @('--cand', $c, '--base', (B 's4b03' $RA), '--allow-new', 'slow frame|memexport full-buffer') }
                '^s4b09$' { Check $id @('--cand', $c, '--base', $b1, '--allow-new', 'deferred_counters') }
                '^s4b1[013]$' { Check $id @('--cand', $c, '--base', $b1, '--allow-new', 'd3d12_submit_split') }
                '^s4b12$' { Check $id @('--cand', $c, '--base', (B 's4b03' $RA), '--allow-new', 'd3d12_submit_split') }
                '^s4b14$' { Check $id @('--cand', $c, '--base', $b1) }
                '^s4b15$' { Check $id @('--cand', $c, '--base', (B 's4b14' $b1), '--allow-new', 'd3d12_submit_split') }
                '^s4b16$' { Check $id @('--cand', $c, '--base', (B 's4b09' $b1), '--allow-new', 'd3d12_submit_split|deferred_counters') }
                '^s4b17$' { Check $id @('--cand', $c, '--base', (B 's4b03' $RA), '--allow-new', 'GPU wait') }
                '^s4b18$' { Check $id @('--cand', $c, '--base', $b1, '--allow-new', 'GPU wait') }
                '^s4b(19|21|22)$' { Check $id @('--cand', $c, '--base', $b1) }
                '^s4b24$' { Check $id @('--cand', $c, '--base', $b1, '--allow-new', 'C1 keep-watch') }
                '^s4b25$' { Check $id @('--cand', $c, '--base', $RT, '--allow-new', 'd3d12_submit_split') }
                # run-2 task 2: the L route (level load, Toy Pad tags) and the W6 untimed runs (W6-GATES.md v2)
                '^s4bL0$' { Check $id @('--cand', $c, '--base', $LX2) }
                '^s4b07$' { Check $id @('--cand', $c, '--base', (B 's4bL0' $LX2), '--allow-new', 'C1 keep-watch|C1 verify') }
                '^s4b20$' { Check $id @('--cand', $c, '--base', (B 's4bL0' $LX2)) }
                '^s4b23$' { Check $id @('--cand', $c, '--base', (B 's4bL0' $LX2), '--allow-new', 'slow frame|memexport full-buffer') }
                '^w6s1$' { Check $id @('--cand', $c, '--base', $RT, '--allow-new', 'slow frame|memexport full-buffer|S[#\d] upload hash') }
                '^w6s2$' { Check $id @('--cand', $c, '--base', (B 'w6s1' $RT), '--allow-new', 'C1 keep-watch|slow frame|memexport full-buffer|S[#\d] upload hash') }
                '^w6gA$' { Check $id @('--cand', $c, '--base', (B 's4bL0' $LX2), '--allow-new', 'C1 keep-watch|C1 verify|slow frame|memexport full-buffer') }
                '^w6s3$' { Check $id @('--cand', $c, '--base', (B 's4b03' $RA), '--allow-new', 'C1 keep-watch|slow frame|memexport full-buffer') }
                # 21:25 extra row: gate A without verify (W6's p2fc arm on the L route)
                '^w6gB$' { Check $id @('--cand', $c, '--base', (B 's4bL0' $LX2), '--allow-new', 'C1 keep-watch|slow frame|memexport full-buffer') }
                # 22:55: Agent 6's direct test for finding 10 (Agent 1 22:44), L route + tags + slow_frame_log_ms=1
                # task #23 (Agent 1, 11-23 06:23): the second pair f10a2/f10b2 is checked the same way
                '^f10a(2|3|L)?$' { Check $id @('--cand', $c, '--base', (B 's4bL0' $LX2), '--allow-new', 'slow frame|memexport full-buffer') }
                '^f10b(2|3|L)?$' { Check $id @('--cand', $c, '--base', (B 's4bL0' $LX2), '--allow-new', 'C1 keep-watch|slow frame|memexport full-buffer') }
                # session 3 (M3, build\agent3\session3\RUNPLANS.md): s4bLV (p2fc + verify, 1800 s), s4bV0 + s4b07r (C1-off
                # verify control and its row-7 twin), s4bQ5 (GPU wait quantum 500 us); f10a3/f10b3, f10aL/f10bL above
                '^s4bLV$' { Check $id @('--cand', $c, '--base', (B 's4bL0' $LX2), '--allow-new', 'C1 keep-watch|C1 verify|slow frame|memexport full-buffer') }
                '^(s4bV0|s4b07r)$' { Check $id @('--cand', $c, '--base', (B 's4bL0' $LX2), '--allow-new', 'C1 keep-watch|C1 verify') }
                '^s4bQ5$' { Check $id @('--cand', $c, '--base', $b1, '--allow-new', 'GPU wait') }
                '^s4bN(16|4)$' { Check $id @('--cand', $c, '--base', $RT, '--allow-new', 'd3d12_submit_split') }
                # 01:48 Overseer: Window C functional gates (matrix-windowC.json arms win3, c1np) on the L route; cg26b0
                # (CG26 bin boot, = s4b01's args) takes the default (base s4b01)
                '^win3f$' { Check $id @('--cand', $c, '--base', (B 's4bL0' $LX2), '--allow-new', 'C1 keep-watch|GPU wait|TimerQueue|Host timer|precise') }
                '^c1npf$' { Check $id @('--cand', $c, '--base', (B 's4bL0' $LX2), '--allow-new', 'C1 keep-watch') }
                '^cg26L$' { Check $id @('--cand', $c, '--base', (B 's4bL0' $LX2)) }
                # post-window (M3, build\agent3\session3\post-window\POSTWIN-PLAN.md): the C1-verify fix pair on
                # devoff4bv-bin (base s4bL0, as s4bV0/s4b07r) and the #33 identity rows 1a/1b (attract-long, -GpuLog).
                # s33off/s33offsf are checked against their own base arm; no allow-new for no_wait (TESTPLAN).
                '^(s4bV0f|s4b07f)$' { Check $id @('--cand', $c, '--base', (B 's4bL0' $LX2), '--allow-new', 'C1 keep-watch|C1 verify') }
                '^s33base2?$' { Check $id @('--cand', $c, '--base', (B 's4b03' $RA)) }
                '^s33basesf$' { Check $id @('--cand', $c, '--base', (B 's33base' $RA), '--allow-new', 'slow frame|memexport full-buffer') }
                '^s33off$' { Check $id @('--cand', $c, '--base', (B 's33base' $RA)) }
                '^s33offsf$' { Check $id @('--cand', $c, '--base', (B 's33basesf' $RA)) }
                default { Check $id @('--cand', $c, '--base', $b1) }
            }
            if ($id -match '^(s4b08|s4b23$|w6|f10b(2|3|L)?$|s4bLV$|win3f$)') { P2c $id $c }
            if ($id -match '^(f10[ab](2|3|L)?|s4bLV|s4bV0f?|s4b07[rf]|win3f|c1npf|cg26L)$') { F10 $id $c }
            $wcArm = @{ win3f = 'win3'; c1npf = 'c1np'; cg26b0 = 'cg26'; cg26L = 'cg26' }[$id]
            if ($wcArm) { WC $id $c $wcArm }
            # #33 row 1a after s33off, row 1b after s33offsf (both arms' runs needed; else a SKIP line)
            if ($id -eq 's33off') { S33 $id 'base' (B 's33base' '') 'off' $c }
            if ($id -eq 's33offsf') { S33 $id 'basesf' (B 's33basesf' '') 'offsf' $c }
        }
    }
    Start-Sleep -Seconds 10
}
Say 'postcheck ends'

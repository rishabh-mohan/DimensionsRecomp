# postcheck.ps1 - Agent 3 S4b (task #29): runs s4b_check.py for each run s4b-queue.ps1 finishes (reads
# queue-state.jsonl; records without a run or with "aborted" are passed over). No python while
# perf-notes\WINDOW-HOLD.txt exists (a user timing window). Read-only on run dirs; writes build\agent3\s4b\checks\
# <run>.{txt,json} (joined\<run>\game.log for runs with rotated logs) and logs\<id>.check.txt. Ends at -Until.
# Bases and allowed NEW families per row: build/agent7/s4b-queue/QUEUE.md (a base row that has no run yet falls back
# to the S4a reference).
# DRAFT (M3, 11-25 07:50, build\agent3\final-fx\FX-PLAN.md): the F1-F7 rows on M2's FINAL bins. Install = copy over
# build\agent3\s4b\postcheck.ps1 (it reads $PSScriptRoot\queue-state.jsonl). Each fx row: s4b_check as a reading, then
# M12's build\agent12\session3\final_gate.py (exit 0 PASS / 1 FAIL / 4 HOLD / 2 usage) -> logs\<id>.fx.txt. The F5 matrix
# row (queue-state record with matrix_out, no run) is gated per arm run (fx5, fx5w) plus the F5w seed check.
# -FxAuto: write build\agent3\final-fx\fx-ok-<id> only on final_gate exit 0 and a clean reading; else M3 decides by hand.
param([string]$Until = '23:59:00', [switch]$FxAuto)
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
    $global:LASTEXITCODE = -1
    & python build\agent3\s4b\s4b_check.py --row $id @a *> (Join-Path $logs "$id.check.txt")
    Say "checked $id (exit $LASTEXITCODE): $($a -join ' ')"
}
# run-2 task 2: P2's fallback counter (G4/R6) with Agent 12's build\agent12\p2c-check\p2c_check.py on every row that has
# slow_frame_log_ms=1 (s4b08*, s4b23, w6*): logs\<id>.p2c.txt (last line RESULT: ...) and logs\<id>.p2c.json.
# Exit 0 = PASS (total 0), 1 = FAIL, 3 = NO DATA/PARTIAL, 4 = ERROR.
function P2c([string]$id, [string]$run) {
    while (Test-Path -LiteralPath $hold) { Start-Sleep -Seconds 10 }
    $global:LASTEXITCODE = -1
    & python -B build\agent12\p2c-check\p2c_check.py $run --json (Join-Path $logs "$id.p2c.json") *> (Join-Path $logs "$id.p2c.txt")
    Say "p2c $id (exit $LASTEXITCODE): $run"
}
# session 3 (M3): the strict finding-10 rule (build\agent3\session3\f10_rule.py) on the L-route rows: logs\<id>.f10.txt
# (last line RESULT: PASS/WARN/FAIL) and logs\<id>.f10.json. Exit 0 = PASS, 1 = WARN (finding 10 only), 2 = FAIL, 4 = ERROR.
function F10([string]$id, [string]$run) {
    while (Test-Path -LiteralPath $hold) { Start-Sleep -Seconds 10 }
    $global:LASTEXITCODE = -1
    & python -B build\agent3\session3\f10_rule.py $run --json (Join-Path $logs "$id.f10.json") *> (Join-Path $logs "$id.f10.txt")
    Say "f10 $id (exit $LASTEXITCODE): $run"
}
# 01:58 (M10 review N3): the Window C / CG26 proof lines (build\agent3\session3\wc_proof.py) on win3f, c1npf, cg26b0,
# cg26L: logs\<id>.wc.txt (last line RESULT: PASS/MISS). Exit 0 = PASS, 1 = a proof miss, 2 = usage.
function WC([string]$id, [string]$run, [string]$arm) {
    while (Test-Path -LiteralPath $hold) { Start-Sleep -Seconds 10 }
    $global:LASTEXITCODE = -1
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
    # 07:06: the kit refuses to write inside build/agent3, so it writes to %TEMP%\m3-s33\<row> and the result is copied
    # to checks\<row> afterwards
    $tmp = Join-Path $env:TEMP "m3-s33\$row"
    $dst = "build\agent3\s4b\checks\$row"
    # 07:10 (M10 Q1): start from empty TEMP and checks dirs so no stale kit output survives
    if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force }
    if (Test-Path -LiteralPath $dst) { Remove-Item -LiteralPath $dst -Recurse -Force }
    & cmd /c build\agent6\s33-popin\RUN-S33-LOGDIFF.cmd --run "$bArm=$bRun" --run "$oArm=$oRun" --ref $oArm `
        --matrix-json build\agent6\s33-popin\harness-s33.json --out $tmp *> $f
    $x = $LASTEXITCODE
    Add-Content -LiteralPath $f -Value "kit exit $x (RUN-S33-LOGDIFF, ref $oArm; out %TEMP%\m3-s33\$row -> $dst)"
    # 07:10 (M10 Q2): copy only when the kit ran (exit 0/1); a failed copy is logged and marks $x
    if ($x -eq 0 -or $x -eq 1) {
        try { New-Item -ItemType Directory -Force -Path $dst -ErrorAction Stop | Out-Null
              Copy-Item -Path (Join-Path $tmp '*') -Destination $dst -Recurse -Force -ErrorAction Stop }
        catch { Add-Content -LiteralPath $f -Value "COPY FAILED: $($_.Exception.Message)"; $x = "$x/copy FAIL" }
    }
    if ($oArm -eq 'offsf') {
        $global:LASTEXITCODE = -1
        & python -B build\agent6\s33-popin\s33_fields.py --arm "offsf=$oRun" --out (Join-Path $logs "$id.s33fields.txt") *>> $f
        $x = "$x/fields $LASTEXITCODE"
        Add-Content -LiteralPath $f -Value "s33_fields exit $($x.Split(' ')[-1])"
    }
    Say "s33 $id $row (exit $x): $bRun vs $oRun"
}
# FINAL F rows (M3 draft): queue id -> final_gate row. fx3/fx6 run on the OFF bins (Overseer 07:44, M10 AE8EB2A5);
# final_gate v2 9DCC72EE maps F3 -> devfinal-off-bin and F6 -> nativefinal-off-bin (Overseer 07:55 ruling 2).
$FXD = 'build\agent3\final-fx'
$N0 = 'build\agent8\matrix\20261125-0359\runs\0400-n0-r1'   # M12 FINAL-F-GATES d: the native4b n0 ref for F5
$FxGate = @{ fx1 = 'F1'; fx2 = 'F2'; fx3 = 'F3'; fx4 = 'F4'; fx5 = 'F5'; fx5w = 'F5w'; fx6 = 'F6'; fx7 = 'F7' }
$FxNewX = 'Final defaults|C1 keep-watch|GPU wait|TimerQueue|Host timer|precise'
$FxNewN = 'shader miss cache|startup pipeline|pipeline cache'
$FgPath = 'build\agent12\session3\final_gate.py'
$FgPin = '73F946E70D58606097C5EDC84FC83345368DB8B341E8B489701A17D38498DFF3'   # M10 F256C60D pin 73F946E7 (v3, frozen)
$NfCache = 'build\agent2\nativefinal-bin\cache'
function FX([string]$id, [string]$run, [string[]]$extra) {
    while (Test-Path -LiteralPath $hold) { Start-Sleep -Seconds 10 }
    $g = $FxGate[$id]
    $f = Join-Path $logs "$id.fx.txt"
    # 08:06 (M10 F256C60D C1): final_gate is pinned; hash it before each call, a mismatch means no gate and no marker
    $fs = try { (Get-FileHash -LiteralPath $FgPath -Algorithm SHA256 -ErrorAction Stop).Hash } catch { 'unreadable' }
    if ($fs -ne $FgPin) {
        "final_gate sha mismatch: $fs (pin $FgPin)" | Set-Content -LiteralPath $f
        Say "fx $id ${g}: final_gate sha mismatch ($fs): no gate, no marker"
        return 'SHA'
    }
    $global:LASTEXITCODE = -1   # S1: a python that never ran cannot leave an old exit 0 behind
    & python -B $FgPath $run $g @extra *> $f
    $x = $LASTEXITCODE
    Add-Content -LiteralPath $f -Value "final_gate sha256 $($fs.Substring(0, 16)) (pin match)"
    Add-Content -LiteralPath $f -Value "final_gate exit $x (row $g; $run $($extra -join ' '))"
    Say "fx $id $g (final_gate exit $x): $run"
    return $x
}
# a FAIL or HOLD stops the chain (M10 G4): no fx-ok marker, so the next fx row never starts
function FxMark([string]$id, $x, [bool]$ok, [string]$why) {
    $m = Join-Path $FXD "fx-ok-$id"
    # S1: the last F-GATE line in logs\<id>.fx.txt must read PASS as well as exit 0
    $gl = @(Select-String -LiteralPath (Join-Path $logs "$id.fx.txt") -Pattern '^F-GATE ' -ErrorAction SilentlyContinue)
    $gp = ($gl.Count -gt 0) -and ($gl[-1].Line.Trim() -match '^F-GATE \S+ \S+: PASS$')
    if (-not $gp) { $ok = $false; $why = "$why; no F-GATE PASS line" }
    # S2: fx-ok-fx2 is what lets fx5 start; fx5 needs a cold nativefinal-bin (no cache\ dir)
    if ($id -eq 'fx2' -and (Test-Path -LiteralPath $NfCache)) {
        $ok = $false; $why = "$why; S2 STOP: $NfCache exists"
        Say "fx fx2: S2 STOP: $NfCache exists, fx5 must not start: M3 reports"
    }
    if ($FxAuto -and $x -eq 0 -and $ok) {
        "auto by postcheck $(Get-Date -Format 'HH:mm:ss'): final_gate exit 0; $why" | Set-Content -LiteralPath $m -Encoding ascii
        Say "fx ${id}: wrote fx-ok-$id ($why)"
    } else { Say "fx ${id}: no auto marker (final_gate exit $x; $why; FxAuto $([bool]$FxAuto)): M3 decides" }
}
function HintOk([string]$id) { [bool](Select-String -LiteralPath (Join-Path $logs "$id.check.txt") -Pattern '^VERDICT HINT PASS\?' -Quiet) }
# F5w carry-over proof (M10 G1): fx5w's run.json seed_cache names fx5's cache\, both files, same sha256 as fx5's cache now
function SeedOk([string]$a, [string]$w) {
    try {
        $sc = (Get-Content -LiteralPath (Join-Path $w 'run.json') -Raw | ConvertFrom-Json).seed_cache
        if (-not $sc) { return 'no seed_cache in fx5w run.json' }
        $want = [IO.Path]::GetFullPath((Join-Path $a 'cache')).TrimEnd('\')
        $src = [IO.Path]::GetFullPath([string]$sc.source_dir).TrimEnd('\')
        if ($src -ne $want) { return "seed source_dir $src is not $want" }
        if ($sc.recipes_only) { return 'seed recipes_only' }
        $names = @($sc.files | ForEach-Object { [string]$_.name })
        if ($names.Count -ne 2 -or 'native-pso.bin' -notin $names -or 'native-pso-recipes.bin' -notin $names) { return "seed files $($names -join ',')" }
        foreach ($s in @($sc.files)) {
            $h = (Get-FileHash -LiteralPath (Join-Path $want $s.name) -Algorithm SHA256).Hash
            if ($h -ne [string]$s.sha256) { return "seed $($s.name) sha256 differs from fx5 cache" }
        }
        return ''
    } catch { return "seed check error: $($_.Exception.Message)" }
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
                # FINAL F rows (draft): a reading only; final_gate below is the gate
                '^fx(1|3|4)$' { Check $id @('--cand', $c, '--base', $b1, '--allow-new', $FxNewX) }
                '^fx2$' { Check $id @('--cand', $c, '--base', (B 's4bL0' $LX2), '--allow-new', $FxNewX) }
                '^fx(6|7)$' { Check $id @('--cand', $c, '--base', $RN, '--allow-new', $FxNewN) }
                default { Check $id @('--cand', $c, '--base', $b1) }
            }
            if ($id -match '^(s4b08|s4b23$|w6|f10b(2|3|L)?$|s4bLV$|win3f$)') { P2c $id $c }
            if ($id -match '^(f10[ab](2|3|L)?|s4bLV|s4bV0f?|s4b07[rf]|win3f|c1npf|cg26L)$') { F10 $id $c }
            $wcArm = @{ win3f = 'win3'; c1npf = 'c1np'; cg26b0 = 'cg26'; cg26L = 'cg26' }[$id]
            if ($wcArm) { WC $id $c $wcArm }
            # #33 row 1a after s33off, row 1b after s33offsf (both arms' runs needed; else a SKIP line)
            if ($id -eq 's33off') { S33 $id 'base' (B 's33base' '') 'off' $c }
            if ($id -eq 's33offsf') { S33 $id 'basesf' (B 's33basesf' '') 'offsf' $c }
            if ($FxGate.ContainsKey($id)) {
                $ex = if ($id -eq 'fx4') { @('--pair', (B 'fx1' '')) } else { @() }
                if ($id -eq 'fx4' -and -not (B 'fx1' '')) { Say 'fx fx4: no fx1 run for --pair'; $ex = @() }
                $x = FX $id $c $ex
                FxMark $id $x (HintOk $id) "s4b_check hint PASS? $(HintOk $id)"
            }
        }
        # the F5 matrix row: one record with matrix_out; gate its fx5 and fx5w arm runs
        $mrecs = @(Get-Content -LiteralPath $state | Where-Object { $_.Trim() } | ForEach-Object { $_ | ConvertFrom-Json } |
            Where-Object { $_.matrix_out -and -not $_.aborted -and [string]$_.id -eq 'fx5' })
        foreach ($r in $mrecs) {
            if ($seen.ContainsKey('fx5')) { continue }
            $seen['fx5'] = 1
            if (Test-Path -LiteralPath (Join-Path $logs 'fx5.fx.txt')) { continue }
            $od = [string]$r.matrix_out
            if (-not [IO.Path]::IsPathRooted($od)) { $od = Join-Path $repo $od }
            $a = @(Get-ChildItem -LiteralPath (Join-Path $od 'runs') -Directory -Filter '*-fx5-r1' -ErrorAction SilentlyContinue)
            $w = @(Get-ChildItem -LiteralPath (Join-Path $od 'runs') -Directory -Filter '*-fx5w-r1' -ErrorAction SilentlyContinue)
            if ($a.Count -ne 1) { "SKIP: $($a.Count) fx5 run dirs in $od (matrix exit $($r.exit))" | Set-Content -LiteralPath (Join-Path $logs 'fx5.fx.txt'); Say "fx fx5 SKIP: $($a.Count) fx5 runs"; continue }
            $ar = $a[0].FullName
            # matrix run.json has close{} not close_method, so s4b_check always lists 'close None' as a BASE miss here
            Check 'fx5' @('--cand', $ar, '--base', $N0, '--allow-new', $FxNewN)
            $x = FX 'fx5' $ar @('--ref', $N0)
            FxMark 'fx5' $x $true 'matrix arm run (reading not used: close None by design)'
            if ($w.Count -ne 1) { "SKIP: $($w.Count) fx5w run dirs in $od (matrix exit $($r.exit))" | Set-Content -LiteralPath (Join-Path $logs 'fx5w.fx.txt'); Say "fx fx5w SKIP: $($w.Count) fx5w runs"; continue }
            $wr = $w[0].FullName
            Check 'fx5w' @('--cand', $wr, '--base', $ar, '--allow-new', $FxNewN)
            $x = FX 'fx5w' $wr @('--first', $ar, '--ref', $N0)
            $sd = SeedOk $ar $wr
            Add-Content -LiteralPath (Join-Path $logs 'fx5w.fx.txt') -Value ("seed check: " + $(if ($sd) { "FAIL $sd" } else { 'PASS (fx5 cache\ -> fx5w cache\, 2 files, sha256 equal)' }))
            FxMark 'fx5w' $x (-not $sd) "seed check $(if ($sd) { $sd } else { 'PASS' })"
        }
    }
    Start-Sleep -Seconds 10
}
Say 'postcheck ends'

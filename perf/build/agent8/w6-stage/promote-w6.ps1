# Agent 8, run-2 task #7 item 4: promote W6 from Agent 5's finalize output (build\agent5\w6-draft\finalize-w6.ps1).
# Usage (from the repo root):
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent8\w6-stage\promote-w6.ps1 [-ExpectBin build/agent2/devoff4-bin] [-ManifestSha 16DCC939...]
#       test: reads Agent 5's pipeline check (build\agent5\w6-draft\check\), copies into build\agent8\w6-stage\test\,
#       writes nothing in bench\.
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent8\w6-stage\promote-w6.ps1 -From build\agent5\w6-draft -Promote -ExpectBin build/agent2/devoff4b-bin -ManifestSha <Agent 2's staging report>
#       on Agent 1's word (after Agent 3's S4b queue passes): copies matrix-window6.json to bench\agent8\run\ and
#       RUN-WINDOW6.cmd to bench\agent8\ byte for byte (so the sha256 in Agent 5's GO line stays valid).
#       Reports go to build\agent8\readout\w6-promote\. -Promote requires -ExpectBin and -ManifestSha.
# Both modes, in this order:
#   FINAL.txt (result OK; -Promote refuses a PIPELINE CHECK) and the sha256s it records;
#   the bin: FINAL.txt's bin = -ExpectBin, MANIFEST.txt sha256 starts with -ManifestSha (Agent 2's staging report),
#     every file MANIFEST.txt lists has its sha256 and size, no FAIL check line, legodimensions.exe = FINAL.txt's;
#   the launcher's rules, checked again (bin in every arm, env keys, no menu/profile/triggers/toml/seed_cache, driver
#     present, the only= arms exist, sys_csv) and the promotion text (no DRAFT; -Promote: no PIPELINE CHECK);
#   the .cmd (CRLF, the bin, -Only/-Repeats of the GO line, REX_TIMER_WAIT_BLOCKING cleared);
#   then the copy, run-matrix.ps1 -PlanOnly from bench\agent8 (Below Normal, starts nothing), the matrix folder count
#   before and after, the input hashes and the GO line.
# It never writes perf-notes\WINDOW-GO.txt (Agent 1 does), never adds .py or .cs files, and stops if WINDOW-HOLD.txt exists.
param(
    [string]$From = 'build\agent5\w6-draft\check',
    [string]$ExpectBin = '',
    [string]$ManifestSha = '',
    [switch]$Promote,
    [switch]$Force,
    [int]$QueueGapS = 20
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$Repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
function Stop-IfHold { if (Test-Path -LiteralPath (Join-Path $Repo 'perf-notes\WINDOW-HOLD.txt')) { Write-Host 'perf-notes\WINDOW-HOLD.txt exists: a timed window is running. Nothing more done.' -ForegroundColor Red; exit 4 } }
Stop-IfHold
(Get-Process -Id $PID).PriorityClass = 'BelowNormal'
function Sha([string]$P) { return (Get-FileHash -LiteralPath $P -Algorithm SHA256).Hash }
function Rel([string]$P) { if ($P.StartsWith($Repo + '\', [StringComparison]::OrdinalIgnoreCase)) { return $P.Substring($Repo.Length + 1) }; return $P }
# Agent 3's S4b queue: harness\guard.ps1 counts every run-matrix.ps1 process (-PlanOnly too) as a runner, so a -PlanOnly
# that starts just as the queue launches makes that launch fail (20:57). -PlanOnly therefore starts only while a queue
# game runs, at least -QueueGapS after its LAUNCH (and 30 s before its -Seconds end), or when the queue is idle.
function Get-QueueState([string]$Q) {
    $tail = @(Get-Content -LiteralPath $Q -Tail 60)
    $now = Get-Date
    $s = @{ Now = $now; LastT = $null; Last = ''; LaunchT = $null; LaunchSec = 0; DoneAfter = $false }
    for ($i = $tail.Count - 1; $i -ge 0; $i--) {
        if ($tail[$i] -notmatch '^(\d\d):(\d\d):(\d\d) (\S+)') { continue }
        $t = $now.Date.AddHours([int]$Matches[1]).AddMinutes([int]$Matches[2]).AddSeconds([int]$Matches[3])
        if ($t -gt $now.AddMinutes(5)) { $t = $t.AddDays(-1) }
        $kind = $Matches[4]
        if ($null -eq $s.LastT) { $s.LastT = $t; $s.Last = $tail[$i] }
        if ($kind -eq 'DONE') { $s.DoneAfter = $true }
        elseif ($kind -eq 'LAUNCH') { $s.LaunchT = $t; if ($tail[$i] -match ' -Seconds (\d+)') { $s.LaunchSec = [int]$Matches[1] }; break }
    }
    return $s
}
function Wait-QueueGap([int]$GapS, [int]$IdleS, [int]$MaxS) {
    $q = Join-Path $Repo 'build\agent3\s4b\logs\queue.out.txt'
    if (-not (Test-Path -LiteralPath $q)) { return 'no queue log, no wait' }
    $t0 = Get-Date
    while ($true) {
        Stop-IfHold
        $s = Get-QueueState $q
        $waited = [int](($s.Now - $t0).TotalSeconds)
        if ($null -ne $s.LaunchT -and -not $s.DoneAfter) {
            $el = ($s.Now - $s.LaunchT).TotalSeconds
            if ($el -ge $GapS -and ($s.LaunchSec -eq 0 -or $el -le $s.LaunchSec - 30)) { return ('a queue game runs (LAUNCH {0:HH:mm:ss}, {1:N0} s ago); -PlanOnly at {2:HH:mm:ss} after {3} s of waiting' -f $s.LaunchT, $el, $s.Now, $waited) }
        } elseif ($null -ne $s.LastT -and ($s.Now - $s.LastT).TotalSeconds -ge $IdleS) { return ('the queue is idle (last line {0:HH:mm:ss}: {1}); -PlanOnly at {2:HH:mm:ss} after {3} s of waiting' -f $s.LastT, $s.Last, $s.Now, $waited) }
        if ($waited -ge $MaxS) { return ('no safe gap in {0} s; -PlanOnly anyway at {1:HH:mm:ss}' -f $MaxS, $s.Now) }
        Start-Sleep -Seconds 5
    }
}
$stamp = Get-Date -Format 'HHmmss'
$when = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$fail = New-Object System.Collections.Generic.List[string]
$notes = New-Object System.Collections.Generic.List[string]
$L = New-Object System.Collections.Generic.List[string]
$mode = if ($Promote) { 'PROMOTE (writes bench\agent8\run\matrix-window6.json and bench\agent8\RUN-WINDOW6.cmd)' } else { 'TEST (copies to build\agent8\w6-stage\test\, no bench writes)' }

# 1. Agent 5's output
$src = if ([IO.Path]::IsPathRooted($From)) { $From } else { Join-Path $Repo $From }
$src = (Resolve-Path -LiteralPath $src).Path
$agent5Dir = Join-Path $Repo 'build\agent5\w6-draft'
if ($Promote -and $src.TrimEnd('\') -ne $agent5Dir) { $fail.Add("-Promote reads only Agent 5's build\agent5\w6-draft, not $(Rel $src)") }
foreach ($f in @('FINAL.txt', 'matrix-window6.json', 'RUN-WINDOW6.cmd')) { if (-not (Test-Path -LiteralPath (Join-Path $src $f) -PathType Leaf)) { throw "$src has no $f" } }
$srcM = Join-Path $src 'matrix-window6.json'; $srcC = Join-Path $src 'RUN-WINDOW6.cmd'; $srcF = Join-Path $src 'FINAL.txt'
$final = @(Get-Content -LiteralPath $srcF)
$isCheck = $final[0] -match 'PIPELINE CHECK'
if ($final[0] -notmatch '-Bin (build/agent2/[A-Za-z0-9][A-Za-z0-9_.-]*-bin)(\s|$)') { throw 'FINAL.txt line 1 has no -Bin build/agent2/<name>-bin' }
$bin = $Matches[1]
$leaf = $bin.Substring('build/agent2/'.Length)
if ($final[1] -ne 'result: OK') { $fail.Add("FINAL.txt says '$($final[1])'") }
if ($Promote -and $isCheck) { $fail.Add('FINAL.txt is a PIPELINE CHECK with a stand-in bin: never promoted') }
function Get-FinalSha([string]$Name) {
    $ln = @($final | Where-Object { $_ -match ('^' + [regex]::Escape($Name) + '\s+sha256 [0-9A-F]{64}') })
    if ($ln.Count -ne 1) { throw "FINAL.txt: no single sha256 line for $Name" }
    [void]($ln[0] -match 'sha256 ([0-9A-F]{64})'); return $Matches[1]
}
$wantM = Get-FinalSha 'matrix-window6.json'
$wantC = Get-FinalSha 'RUN-WINDOW6.cmd'
$exeLn = @($final | Where-Object { $_ -match ('^bin ' + [regex]::Escape($bin) + '\s+legodimensions\.exe sha256 [0-9A-F]{64}') })
if ($exeLn.Count -ne 1) { throw "FINAL.txt: no single 'bin $bin legodimensions.exe sha256' line" }
[void]($exeLn[0] -match 'sha256 ([0-9A-F]{64})'); $wantExe = $Matches[1]
$goLn = @($final | Where-Object { $_ -match '^GO W6 matrix-window6\.json [0-9A-F]{64} only=\S+ repeats=\d+$' })
if ($goLn.Count -ne 1) { throw 'FINAL.txt: no single GO line' }
$go = $goLn[0]
[void]($go -match '^GO W6 matrix-window6\.json ([0-9A-F]{64}) only=(\S+) repeats=(\d+)$')
$goSha = $Matches[1]; $only = $Matches[2]; $repeats = [int]$Matches[3]
$onlyList = @($only -split ',' | Where-Object { $_ })
if ($goSha -ne $wantM) { $fail.Add("GO line sha256 $goSha is not FINAL.txt's matrix sha256 $wantM") }
$srcMSha = Sha $srcM; $srcCSha = Sha $srcC
if ($srcMSha -ne $wantM) { $fail.Add("source matrix-window6.json sha256 $srcMSha is not FINAL.txt's $wantM (changed after finalize?)") }
if ($srcCSha -ne $wantC) { $fail.Add("source RUN-WINDOW6.cmd sha256 $srcCSha is not FINAL.txt's $wantC (changed after finalize?)") }

# 2. the bin: the one Agent 1 named, MANIFEST.txt pinned to Agent 2's staging report, every listed file intact
if ($ExpectBin) { $eb = ($ExpectBin -replace '\\', '/').TrimEnd('/'); if ($eb -ne $bin) { $fail.Add("FINAL.txt's bin is $bin, not the expected $eb") } }
elseif ($Promote) { $fail.Add('-Promote needs -ExpectBin (the bin Agent 1 named)') }
$binDir = Join-Path $Repo ($bin -replace '/', '\')
$binHash = @{}; $manSha = ''; $manNote = 'no MANIFEST.txt'; $manHead = @()
if (-not (Test-Path -LiteralPath $binDir -PathType Container)) { $fail.Add("$bin does not exist") }
else {
    foreach ($f in @(Get-ChildItem -LiteralPath $binDir -File)) { $binHash[$f.Name] = Sha $f.FullName }
    foreach ($f in @('MANIFEST.txt', 'legodimensions.exe')) { if (-not $binHash.ContainsKey($f)) { $fail.Add("$bin has no $f") } }
}
if ($binHash.ContainsKey('MANIFEST.txt')) {
    $manPath = Join-Path $binDir 'MANIFEST.txt'
    $manSha = $binHash['MANIFEST.txt']
    $man = @(Get-Content -LiteralPath $manPath)
    $manHead = @($man | Select-Object -First 2)
    if ($ManifestSha) {
        if ($ManifestSha -notmatch '^[0-9A-Fa-f]{8,64}$') { $fail.Add("-ManifestSha '$ManifestSha' is not 8-64 hex digits") }
        elseif (-not $manSha.StartsWith($ManifestSha.ToUpperInvariant())) { $fail.Add("$bin MANIFEST.txt sha256 $manSha does not start with $ManifestSha (Agent 2's staging report)") }
    } elseif ($Promote) { $fail.Add("-Promote needs -ManifestSha (from Agent 2's staging report)") }
    $listedNames = New-Object System.Collections.Generic.List[string]; $matched = 0
    foreach ($ln in $man) {
        if ($ln.StartsWith('#')) { continue }
        $c = $ln -split "`t"
        if ($c.Count -lt 4 -or $c[3] -notmatch '^[0-9A-F]{64}$') { continue }
        $nm = $c[0]; $listedNames.Add($nm)
        if (-not $binHash.ContainsKey($nm)) { $fail.Add("MANIFEST.txt lists $nm, which $bin lacks"); continue }
        $len = (Get-Item -LiteralPath (Join-Path $binDir $nm)).Length
        if ($binHash[$nm] -ne $c[3] -or [string]$len -ne $c[1]) { $fail.Add("$bin\$nm differs from its MANIFEST.txt line (sha256 or size)") } else { $matched++ }
    }
    if ($listedNames.Count -lt 1) { $fail.Add('MANIFEST.txt lists no files') }
    $unlisted = @($binHash.Keys | Where-Object { $_ -ne 'MANIFEST.txt' -and -not $listedNames.Contains($_) } | Sort-Object)
    $nPass = @($man | Where-Object { $_ -match '^#\s+PASS\b' }).Count
    $nFail = @($man | Where-Object { $_ -match '^#\s+FAIL\b' }).Count
    if ($nFail) { $fail.Add("MANIFEST.txt has $nFail FAIL check line(s)") }
    $manNote = "MANIFEST.txt sha256 $manSha; $($listedNames.Count) files listed, $matched match by sha256 and size; check lines PASS $nPass, FAIL $nFail; unlisted files: $(if ($unlisted.Count) { $unlisted -join ', ' } else { 'none' })"
    if ($unlisted.Count) { $notes.Add("files in $bin that MANIFEST.txt does not list: $($unlisted -join ', ')") }
    if ((Get-Item -LiteralPath $manPath).LastWriteTime -gt (Get-Item -LiteralPath $srcF).LastWriteTime) { $notes.Add('MANIFEST.txt is newer than FINAL.txt: the bin was staged again after the finalize (the exe and MANIFEST checks above still apply)') }
}
$exeSha = if ($binHash.ContainsKey('legodimensions.exe')) { $binHash['legodimensions.exe'] } else { '' }
if ($exeSha -and $exeSha -ne $wantExe) { $fail.Add("$bin legodimensions.exe sha256 $exeSha is not FINAL.txt's $wantExe (finalize again)") }

# 3. the matrix, checked again here (the launcher's rules, run-night.ps1 Test-Matrix, plus the promotion text)
$bytes = [IO.File]::ReadAllBytes($srcM)
if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) { $fail.Add('matrix-window6.json starts with a BOM') }
$m = [IO.File]::ReadAllText($srcM) | ConvertFrom-Json
if ([string]$m.title -cmatch 'DRAFT') { $fail.Add('matrix title still says DRAFT') }
if ([string]@($m.notes)[0] -cmatch '^DRAFT') { $fail.Add('matrix notes[0] is still the DRAFT note') }
if ($Promote -and (([string]$m.title + ' ' + [string]@($m.notes)[0]) -match 'PIPELINE CHECK')) { $fail.Add('matrix title or notes[0] says PIPELINE CHECK') }
if (-not ([string]@($m.notes)[0]).Contains($exeSha)) { $fail.Add("matrix notes[0] does not name this bin's legodimensions.exe sha256") }
if ($m.sys_csv -ne $true) { $fail.Add('sys_csv is not true') }
$allowedEnv = @('REX_TIMER_WAIT_BLOCKING', 'LEGO_GPU_WAIT_STATS')
$ids = @(); $envUsed = @()
foreach ($a in @($m.arms)) {
    $id = [string]$a.id; $ids += $id
    $ab = ([string]$a.bin -replace '\\', '/').TrimEnd('/')
    if ($ab -ne $bin) { $fail.Add("arm ${id}: bin '$ab' is not $bin") }
    foreach ($k in @('menu', 'profile', 'triggers', 'toml', 'seed_cache')) { if ($null -ne $a.PSObject.Properties[$k]) { $fail.Add("arm ${id}: has a $k field") } }
    if ($null -ne $a.PSObject.Properties['env'] -and $null -ne $a.env) { foreach ($pp in $a.env.PSObject.Properties) { $envUsed += "${id}:$($pp.Name)"; if ($allowedEnv -cnotcontains $pp.Name) { $fail.Add("arm ${id}: env key '$($pp.Name)' is not allowed") } } }
    $dr = if ($null -ne $a.PSObject.Properties['driver']) { [string]$a.driver } else { '' }
    if (-not $dr) { $fail.Add("arm ${id}: no driver (the launcher needs it pinned)") }
    elseif (-not (Test-Path -LiteralPath (Join-Path $Repo ('bench\agent8\run\' + ($dr -replace '/', '\'))) -PathType Leaf)) { $fail.Add("arm ${id}: driver $dr is not in bench\agent8\run") }
}
foreach ($o in $onlyList) { if ($ids -cnotcontains $o) { $fail.Add("only=: the matrix has no arm '$o'") } }

# 4. the .cmd
$cmdTxt = [IO.File]::ReadAllText($srcC)
if ($cmdTxt -match "(?<!`r)`n") { $fail.Add('RUN-WINDOW6.cmd has bare LF line ends') }
if ($cmdTxt -match '__BIN__|__WHEN__') { $fail.Add('RUN-WINDOW6.cmd still has template fields') }
if (-not $cmdTxt.Contains("build\agent2\$leaf\MANIFEST.txt")) { $fail.Add("RUN-WINDOW6.cmd does not check build\agent2\$leaf\MANIFEST.txt") }
if (-not $cmdTxt.Contains("-Only $only -Repeats $repeats -ColdShared -NoPrompt")) { $fail.Add("RUN-WINDOW6.cmd does not run -Only $only -Repeats $repeats -ColdShared -NoPrompt") }
if (-not $cmdTxt.Contains('set "REX_TIMER_WAIT_BLOCKING="')) { $fail.Add('RUN-WINDOW6.cmd does not clear REX_TIMER_WAIT_BLOCKING') }

# 5. the copy (only when every check above passed)
if ($Promote) {
    $dstM = Join-Path $Repo 'bench\agent8\run\matrix-window6.json'; $dstC = Join-Path $Repo 'bench\agent8\RUN-WINDOW6.cmd'
    $rep = Join-Path $Repo 'build\agent8\readout\w6-promote'
} else {
    $rep = Join-Path $PSScriptRoot 'test'
    $dstM = Join-Path $rep 'matrix-window6.json'; $dstC = Join-Path $rep 'RUN-WINDOW6.cmd'
}
New-Item -ItemType Directory -Force -Path $rep | Out-Null
$copied = $false; $plan = @(); $code = $null; $before = $null; $after = $null; $dstMSha = '-'; $dstCSha = '-'
$H = New-Object System.Collections.Generic.List[string]
if (-not $fail.Count) {
    foreach ($pair in @(@($srcM, $dstM, $srcMSha), @($srcC, $dstC, $srcCSha))) {
        if ((Test-Path -LiteralPath $pair[1]) -and ((Sha $pair[1]) -ne $pair[2]) -and -not $Force) { $fail.Add("$(Rel $pair[1]) exists with another sha256; -Force replaces it") }
    }
}
if (-not $fail.Count) {
    Stop-IfHold
    Copy-Item -LiteralPath $srcM -Destination $dstM -Force
    Copy-Item -LiteralPath $srcC -Destination $dstC -Force
    $copied = $true
    $dstMSha = Sha $dstM; $dstCSha = Sha $dstC
    if ($dstMSha -ne $wantM) { $fail.Add('the copied matrix-window6.json has another sha256') }
    if ($dstCSha -ne $wantC) { $fail.Add('the copied RUN-WINDOW6.cmd has another sha256') }

    # 6. the runner's own plan, from bench\agent8 (-PlanOnly reads the matrix and starts nothing)
    $matrixRoot = Join-Path $Repo 'build\agent8\matrix'
    $notes.Add('queue gap: ' + (Wait-QueueGap $QueueGapS 120 600))
    $before = @(Get-ChildItem -LiteralPath $matrixRoot -Directory).Count
    Stop-IfHold
    $mArg = if ($Promote) { 'run\matrix-window6.json' } else { $dstM }
    Push-Location (Join-Path $Repo 'bench\agent8')
    $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { $plan = @(& (Join-Path $PSHOME 'powershell.exe') -NoProfile -ExecutionPolicy Bypass -File 'run\run-matrix.ps1' -Matrix $mArg -Only $only -Repeats $repeats -ColdShared -NoPrompt -PlanOnly 2>&1 | ForEach-Object { "$_" }); $code = $LASTEXITCODE }
    finally { $ErrorActionPreference = $old; Pop-Location }
    $after = @(Get-ChildItem -LiteralPath $matrixRoot -Directory).Count
    $est = @($plan | Where-Object { $_ -match '^estimate\s+\d+ runs \(\d+ cold\), about \d+ min' })
    $bad = @($plan | Where-Object { $_ -match '^!!! (ERROR|SKIPPED ARM|MATRIX ERROR)' -or $_ -match '^\s+SKIP ' })
    if ($code -ne 0) { $fail.Add("run-matrix.ps1 -PlanOnly exit $code") }
    if ($bad.Count) { $fail.Add("run-matrix.ps1 -PlanOnly: $($bad -join ' / ')") }
    $expRuns = 1 + $onlyList.Count * $repeats
    if (-not $est.Count) { $fail.Add('run-matrix.ps1 -PlanOnly printed no estimate line') }
    else { [void]($est[0] -match '^estimate\s+(\d+) runs'); if ([int]$Matches[1] -ne $expRuns) { $fail.Add("-PlanOnly plans $($Matches[1]) runs, not 1 cold + $($onlyList.Count) x $repeats = $expRuns") } }
    if ($after -ne $before) { $fail.Add("build\agent8\matrix had $before folders before -PlanOnly and $after after") }

    # 7. the inputs the window reads
    $runDir = Join-Path $Repo 'bench\agent8\run'
    $other = New-Object System.Collections.Generic.List[string]
    $other.Add($dstM); $other.Add($dstC)
    foreach ($n in @('run-matrix.ps1', 'run-timing.ps1', 'common.ps1', 'timing-env.ps1', 'winhelper.cs')) { $other.Add((Join-Path $runDir $n)) }
    foreach ($f in @(Get-ChildItem -LiteralPath $runDir -File | Where-Object { ($_.Extension -eq '.py' -or $_.Extension -eq '.cs') -and $_.Name -ne 'winhelper.cs' } | Sort-Object Name)) { $other.Add($f.FullName) }
    foreach ($f in @(Get-ChildItem -LiteralPath (Join-Path $runDir 'drivers') -File -Recurse | Sort-Object FullName)) { $other.Add($f.FullName) }
    foreach ($n in @('harness\legodimensions.toml', 'harness\nvml.cs', 'bench\agent5\launch\RUN-NIGHT.cmd', 'bench\agent5\launch\run-night.ps1')) { $other.Add((Join-Path $Repo $n)) }
    foreach ($p in $other) {
        if (Test-Path -LiteralPath $p -PathType Leaf) { $fi = Get-Item -LiteralPath $p; $H.Add(('{0}  {1,11}  {2}  {3}' -f (Sha $p), $fi.Length, $fi.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'), (Rel $p))) }
        else { $H.Add("MISSING  $(Rel $p)"); $fail.Add("input missing: $(Rel $p)") }
    }
    foreach ($nm in @($binHash.Keys | Sort-Object)) { $p = Join-Path $binDir $nm; $fi = Get-Item -LiteralPath $p; $H.Add(('{0}  {1,11}  {2}  {3}' -f $binHash[$nm], $fi.Length, $fi.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'), (Rel $p))) }
}

# 8. the report
$L.Add("W6 promotion (Agent 8, run-2 task #7, build\agent8\w6-stage\promote-w6.ps1), $when")
$L.Add("mode: $mode")
$L.Add("result: $(if ($fail.Count) { 'NOT OK: ' + ($fail -join ' | ') } else { 'OK' })")
$L.Add("from: $(Rel $src)  (FINAL.txt: $($final[0]))")
$L.Add("bin: $bin (expected: $(if ($ExpectBin) { $ExpectBin } else { '-' }))  legodimensions.exe sha256 $exeSha (FINAL.txt $wantExe)")
$L.Add("$manNote (Agent 2's staging report: $(if ($ManifestSha) { $ManifestSha } else { '-' }))")
$L.Add("matrix-window6.json  FINAL.txt $wantM  copy $dstMSha  -> $(Rel $dstM)")
$L.Add("RUN-WINDOW6.cmd      FINAL.txt $wantC  copy $dstCSha  -> $(Rel $dstC)")
$L.Add("arms in the matrix: $($ids -join ', '); env keys: $(if ($envUsed.Count) { $envUsed -join ', ' } else { 'none' }); run: only=$only repeats=$repeats -ColdShared")
$L.Add("matrix folders before/after -PlanOnly: $before / $after")
$L.Add("GO line$(if (-not $Promote) { ' (TEST: for the stand-in check only; never use it)' }): $(if ($fail.Count) { 'none (result NOT OK)' } else { $go })")
foreach ($x in $notes) { $L.Add("NOTE: $x") }
$L.Add('')
$L.Add('--- MANIFEST.txt (first 2 lines)')
foreach ($x in $manHead) { $L.Add($x) }
$L.Add('')
$L.Add("--- bench\agent8> powershell -File run\run-matrix.ps1 -Matrix $(if ($Promote) { 'run\matrix-window6.json' } else { Rel $dstM }) -Only $only -Repeats $repeats -ColdShared -NoPrompt -PlanOnly  (exit $code)")
foreach ($x in $plan) { $L.Add($x) }
$utf8 = New-Object Text.UTF8Encoding $false
$repPath = Join-Path $rep ("promote-$stamp" + $(if ($fail.Count) { '-NOTOK' } else { '' }) + '.txt')
[IO.File]::WriteAllText($repPath, (($L -join "`r`n") + "`r`n"), $utf8)
if ($H.Count) {
    $hPath = Join-Path $rep "inputs-$stamp.txt"
    $hh = @("W6 inputs (Agent 8, promote-w6.ps1), $when, mode $(if ($Promote) { 'PROMOTE' } else { 'TEST' }): sha256, bytes, last write, path") + @($H)
    [IO.File]::WriteAllText($hPath, (($hh -join "`r`n") + "`r`n"), $utf8)
}
$show = 10 + $notes.Count
Write-Host ($L[0..$show] -join "`r`n")
foreach ($x in @($plan | Where-Object { $_ -match '^estimate' })) { Write-Host $x }
Write-Host "written: $(Rel $repPath)$(if ($H.Count) { ' and inputs-' + $stamp + '.txt (' + $H.Count + ' files)' })"
if ($fail.Count) { exit 1 } else { exit 0 }

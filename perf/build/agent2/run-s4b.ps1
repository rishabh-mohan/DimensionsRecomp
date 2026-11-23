# Agent 2 - S4b builds (board run 2, task #1 = old #28, Agent 1): snap1 at S4b (prep-s4b.py: S4a + C1 -> M1 -> P2c ->
# r1r2 -> #26 tool, every new switch OFF, + S4c #24 + #30 OFF) -> build/agent2/devoff4b-bin and native4b-bin.
# Run as a run_command background task, alone in its command (the driver guard skips this script's own ancestors);
# build/agent2/stop-snap.ps1 kills it.
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\run-s4b.ps1 -Stage off -C1 v3 [-Jobs 8] [-DryRun]
#       SDK build + install (snap1-sdk, -SkipConfigure: no new SDK file; every target, so the codegen tool too), then the
#       devoff4b game build (snap1-off) WITH the configure (S4c changes rexlego/CMakeLists.txt), then
#       stage-snap-bin.ps1 -Variant off -> build/agent2/devoff4b-bin
#   ... -Stage native -C1 v3     native4b game build (snap1-on) with the explicit configure, then stage-snap-bin.ps1
#       -Variant native -> build/agent2/native4b-bin. Needs devoff4b-bin first (it links against the S4b install).
#   ... -Stage nativecfg -C1 v3  only the snap1-on configure + gen-check + gate (build-snap -NoBuild, tag snap4bcfg), for
#       Agent 4's read-only re-pin dry run while the OFF game compiles; needs the S4b SDK installed.
# Every step runs Below Normal (this process's priority class; Windows children inherit it) and is polled every 15 s:
#   perf-notes/WINDOW-HOLD.txt appears -> the step's process tree is killed (within ~15 s), exit 30: wait for Agent 1;
#   free RAM < 4 GB on 2 polls in a row -> the step is killed and restarted at -j6, then -j4 (ninja resumes);
#   at or after -KillAt (the overnight launcher refuses to start while clang/ninja run) -> killed, exit 31.
# Guards before anything builds: no HOLD file, no start at or after -Latest, -Jobs capped at 8, no other snapshot build
# driver, S4b-notes.txt present and naming the -C1 variant, snap-patch.py verify S4b PASS, PATCHES-S4b.tsv = 16 rows and
# every snap1 copy == its after-hash, the out folder not staged yet; native: devoff4b-bin staged and install/bin
# rexruntime.dll and rexgpu-xenos.dll == devoff4b-bin's. -DryRun: the guards (the S4b ones PENDING until prep-s4b.py has
# applied) and the planned commands; nothing is built.
# stage-snap-bin.ps1 gets -PatchTagList S1,S2,S3,S3d,S4a,S4b, the S4a literals + S4b-strings.tsv's (16+ chars, per
# binary) and no -CompareBin; each staged file is compared with devoff4-bin / native4-bin here instead: rexruntime.dll,
# rexgpu-xenos.dll and the exe must differ. The S4c environment names must be in the OFF exe and NOT in the native one.
# Log: build/agent2/snap4b-run.txt (+ build-snap's snap4b-steps.txt and logs, and snap4b-stage-<stage>.log).
param([ValidateSet('off', 'native', 'nativecfg')][string]$Stage = 'off', [int]$Jobs = 8, [string]$C1 = '',
    [string]$Latest = '23:00', [string]$KillAt = '23:40', [switch]$DryRun)
$ErrorActionPreference = 'Continue'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass = 'BelowNormal'
$R = '<workspace>'
$A = "$R\build\agent2"
$hold = "$R\perf-notes\WINDOW-HOLD.txt"
$SnapTag = 'S4b'; $tag = 'snap4b'
$runLog = "$A\$tag-run.txt"
$notes = "$A\$SnapTag-notes.txt"
$strTsv = "$A\$SnapTag-strings.tsv"
$killAtTs = [TimeSpan]::Parse($KillAt + ':00')
function Log([string]$m) {
    $line = "$(Get-Date -Format HH:mm:ss) [$SnapTag $Stage$(if ($DryRun) { ' dry-run' })] $m"
    $line | Out-File -Append -Encoding utf8 $runLog
    Write-Host $line
}
function Sha([string]$p) { (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash }
function FreeGB { (Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB }
function Q([string]$s) { if ($s -eq '' -or $s -match '\s') { '"' + $s + '"' } else { $s } }
function KillTree([int]$id) {
    & taskkill /T /F /PID $id 2>&1 | Out-Null
    Start-Sleep -Seconds 2
    $left = @(Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and $_.Name -match '^(clang|ninja|cmake|lld|ld\.lld|llvm|cmd|prelink)' -and $_.CommandLine -match 'agent2[\\/]+snap1' })
    foreach ($q in $left) { Log "  orphan $($q.ProcessId) $($q.Name): killed"; & taskkill /T /F /PID $q.ProcessId 2>&1 | Out-Null }
}
$script:prioLogged = $false
function RunPolled([string]$what, [string[]]$argv, [string]$outFile) {
    # powershell -File <argv>: the exit code is the script's exit code (1 on an unhandled error)
    $argStr = '-NoProfile -ExecutionPolicy Bypass -File ' + (($argv | ForEach-Object { Q $_ }) -join ' ')
    Log "BEGIN $what : $argStr"
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $sp = @{ FilePath = 'powershell.exe'; ArgumentList = $argStr; PassThru = $true; NoNewWindow = $true }
    if ($outFile) { $sp['RedirectStandardOutput'] = $outFile; $sp['RedirectStandardError'] = "$outFile.err" }
    $p = Start-Process @sp
    $null = $p.Handle
    $low = 0; $result = $null
    while (-not $p.WaitForExit(15000)) {
        if (Test-Path -LiteralPath $hold) { $result = 'HOLD'; break }
        if ((Get-Date).TimeOfDay -ge $killAtTs) { $result = 'KILLAT'; break }
        $free = FreeGB
        if ($free -lt 4) { $low++; Log ("  free RAM {0:N2} GB < 4 GB ({1} poll(s) in a row)" -f $free, $low) } else { $low = 0 }
        if ($low -ge 2) { $result = 'LOWRAM'; break }
        if (-not $script:prioLogged) {
            $cl = @(Get-Process -Name 'clang*', 'ninja' -ErrorAction SilentlyContinue)
            if ($cl.Count) {
                Log ("  priority: {0}" -f (($cl | Select-Object -First 4 | ForEach-Object { "$($_.Name) $($_.Id) $($_.PriorityClass)" }) -join '; '))
                $script:prioLogged = $true
            }
        }
    }
    if ($result) {
        Log "  $result : killing the step tree (pid $($p.Id))"
        KillTree $p.Id
        Log ("END   $what $result wall={0:N1}s" -f $sw.Elapsed.TotalSeconds)
        return $result
    }
    $p.WaitForExit()
    $code = $p.ExitCode
    Log ("END   $what exit=$code wall={0:N1}s freeC={1:N2}GB freeRAM={2:N2}GB" -f $sw.Elapsed.TotalSeconds, ((Get-PSDrive C).Free / 1GB), (FreeGB))
    return $code
}
function RunJobs([string]$what, [scriptblock]$mk) {
    # the step at -Jobs, restarted at -j6 and -j4 on low RAM; HOLD / KILLAT end the driver
    foreach ($j in @($Jobs, 6, 4) | Where-Object { $_ -le $Jobs } | Select-Object -Unique) {
        $c = RunPolled "$what -j$j" (& $mk $j) ''
        if ($c -eq 'HOLD') { Log "STOP: $hold appeared; the step tree is killed; waiting for Agent 1's resume (re-run this driver: ninja resumes)"; exit 30 }
        if ($c -eq 'KILLAT') { Log "STOP: it is $KillAt (the overnight launcher needs clang/ninja gone)"; exit 31 }
        if ($c -ne 'LOWRAM') { return $c }
        Log "  restarting $what below -j$j (free RAM < 4 GB)"
    }
    Log "STOP: free RAM < 4 GB even at -j4"; exit 32
}
# ---- guards (nothing is built or written before they pass, except this log)
if (-not $C1) { Log 'STOP: give -C1 v2|v3 (Agent 1 sets the C1 variant; prep-s4b.py --c1 must match)'; exit 2 }
if (Test-Path -LiteralPath $hold) { Log "STOP: $hold exists"; exit 30 }
if ((Get-Date).TimeOfDay -ge [TimeSpan]::Parse($Latest + ':00')) { Log "STOP: no build starts at or after $Latest"; exit 3 }
if ($Jobs -gt 8) { Log "-Jobs $Jobs capped at 8 (Agent 1)"; $Jobs = 8 }
$anc = @{}; $cur = $PID
for ($i = 0; $i -lt 30; $i++) {
    $pp = (Get-CimInstance Win32_Process -Filter "ProcessId=$cur" -ErrorAction SilentlyContinue).ParentProcessId
    if (-not $pp -or $anc.ContainsKey([int]$pp)) { break }
    $anc[[int]$pp] = 1; $cur = $pp
}
$drv = @(Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and -not $anc.ContainsKey([int]$_.ProcessId) -and $_.CommandLine -match 'run-b\.ps1|b-chain\.ps1|rb-chain\.ps1|run-(s2|s3|s3d|s3e|nb|rb1|rb2|s4a|s4b|b4)\.ps1|prep-(s4a|s4b|b4)\.py|build-snap\.ps1|stage-snap-bin\.ps1' })
if ($drv.Count) { Log "STOP: another snapshot build driver is running (pid $($drv[0].ProcessId): $($drv[0].CommandLine))"; exit 4 }
Log ("guards: no HOLD file; -Jobs $Jobs; -C1 $C1; priority {0}; free RAM {1:N1} GB; free C: {2:N1} GB" -f [Diagnostics.Process]::GetCurrentProcess().PriorityClass, (FreeGB), ((Get-PSDrive C).Free / 1GB))
$prepped = @(Get-ChildItem -LiteralPath "$A\snap1" -Filter "STATE-$SnapTag-*.tsv" -File | Where-Object { $_.Name -notmatch 'reverted' }).Count -gt 0
if (-not $prepped) {
    if (-not $DryRun) { Log "STOP: snap1 is not at $SnapTag (no STATE-$SnapTag-*.tsv: run prep-s4b.py --c1 $C1 first)"; exit 5 }
    Log "PENDING: prep-s4b.py has not applied yet (no STATE-$SnapTag-*.tsv); notes / verify / PATCHES guards run after it"
} else {
    if (-not (Test-Path -LiteralPath $notes)) { Log "STOP: $notes is missing (prep-s4b.py writes it)"; exit 4 }
    if (-not (Select-String -LiteralPath $notes -SimpleMatch "C1 = $C1 (" -Quiet)) { Log "STOP: $(Split-Path -Leaf $notes) does not name C1 = $C1 (snap1 was prepared with another C1)"; exit 4 }
    $vo = "$A\$tag-verify-$Stage.txt"
    & python "$A\snap-patch.py" verify $SnapTag > $vo 2>&1
    $vc = $LASTEXITCODE
    Log "verify $SnapTag : exit $vc : $(@(Get-Content $vo)[0])"
    if ($vc -ne 0) { Log "STOP: snap1 is not $SnapTag (see $(Split-Path -Leaf $vo))"; exit 5 }
    $pt = "$A\snap1\PATCHES-$SnapTag.tsv"
    $rows = @(Get-Content -Encoding UTF8 -LiteralPath $pt | Where-Object { $_ -and -not $_.StartsWith('#') })
    if ($rows.Count -ne 16) { Log "STOP: PATCHES-$SnapTag.tsv has $($rows.Count) data rows, not 16"; exit 6 }
    foreach ($row in $rows) {
        $c = @($row -split "`t")
        $h = Sha ("$A\snap1\DimensionsRecomp\" + $c[0].Replace('/', '\'))
        if ($h -ne $c[2].ToUpper()) { Log "STOP: snap1 $($c[0]) is $($h.Substring(0, 16)), but PATCHES-$SnapTag.tsv says $($c[2].Substring(0, 16))"; exit 6 }
        Log ("  {0}: {1} -> {2} == snap1" -f $c[0], $c[1].Substring(0, [Math]::Min(16, $c[1].Length)), $h.Substring(0, 16))
    }
}
# ---- strings: the S4a literals + S4b-strings.tsv (16+ chars), per binary
$rt = [Collections.Generic.List[string]]@('audio_shutdown_detach_worker', 'leave it running and leak what it can still reach', 'physical_protect_hold_global_lock', 'timer_queue_precise_wait')
$xe = [Collections.Generic.List[string]]@('shared_memory_upload_hash_log', 'shared_memory_single_hold_rearm')
$exe = [Collections.Generic.List[string]]@('which can hang when the guest pauses')
$absent = [Collections.Generic.List[string]]@()
$nat = $Stage -ne 'off'
if ($nat) { foreach ($s in 'LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD', 'LEGO_NATIVE_FPS_CELL_RECTS', 'LEGO_NATIVE_TEXTURE_STAGING_POOL', 'LEGO_NATIVE_SHADER_MISS_CACHE') { $exe.Add($s) } }
$tsv = $(if (Test-Path -LiteralPath $strTsv) { $strTsv } else { @(Get-ChildItem -LiteralPath "$A\s4b" -Filter 'S4b-strings.tsv' -Recurse -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1 | ForEach-Object { $_.FullName }) })
if ($tsv) {
    foreach ($l in @(Get-Content -Encoding UTF8 -LiteralPath $tsv | Where-Object { $_ -and -not $_.StartsWith('#') })) {
        $c = @($l -split "`t")
        if ($c[0].Length -lt 16) { continue }
        switch ($c[3]) {
            'rexruntime.dll' { $rt.Add($c[0]) }
            'rexgpu-xenos.dll' { $xe.Add($c[0]) }
            'OFF exe' { if ($nat) { $absent.Add($c[0]) } else { $exe.Add($c[0]) } }
            'native exe' { if ($nat) { $exe.Add($c[0]) } else { $absent.Add($c[0]) } }
        }
    }
    Log "strings from $($tsv.Substring($R.Length + 1)): rexruntime.dll [$($rt -join ', ')]; rexgpu-xenos.dll [$($xe -join ', ')]; exe [$($exe -join ', ')]; exe must NOT contain [$($absent -join ', ')]"
} else { Log 'STOP: no S4b-strings.tsv (prep-s4b.py writes it)'; exit 4 }
$bs = "$A\build-snap.ps1"
$I = "$A\snap1-sdk\install\bin"
if ($Stage -eq 'nativecfg') {
    $mk = { param($j) @($bs, '-Phase', 'game', '-Native', '-Tag', "${tag}cfg", '-Jobs', "$j", '-NoBuild') }
    if ($DryRun) { Log "PLAN: $((& $mk $Jobs) -join ' ')"; Log 'DRY-RUN done: nothing built'; exit 0 }
    foreach ($d in 'rexruntime.dll', 'rexgpu-xenos.dll') {
        $sd = "$R\build\agent2\snap1\DimensionsRecomp\rexglue-sdk\out\win-amd64\Release\$d"
        if ((Sha "$I\$d") -ne (Sha $sd)) { Log "STOP: install/bin/$d != the SDK out tree's (the S4b SDK is not installed yet)"; exit 4 }
    }
    $c = RunJobs 'native configure (-NoBuild)' $mk
    Log "native configure exit $c; gate: $(@(Get-Content "$A\${tag}cfg-native-gate.log" -ErrorAction SilentlyContinue | Select-String '^RESULT:' | ForEach-Object { $_.Line }) -join ' ')"
    exit $c
}
$B = $(if ($Stage -eq 'off') { "$A\snap1-off" } else { "$A\snap1-on" })
$O = $(if ($Stage -eq 'off') { "$A\devoff4b-bin" } else { "$A\native4b-bin" })
$ref = $(if ($Stage -eq 'off') { "$A\devoff4-bin" } else { "$A\native4-bin" })
$refL = Split-Path -Leaf $ref
if (Test-Path -LiteralPath "$O\MANIFEST.txt") { Log "STOP: $(Split-Path -Leaf $O) is already staged (MANIFEST.txt exists)"; exit 4 }
if ($Stage -eq 'native') {
    if (-not (Test-Path -LiteralPath "$A\devoff4b-bin\MANIFEST.txt")) {
        if (-not $DryRun) { Log 'STOP: devoff4b-bin is not staged (native4b links against the S4b snap1-sdk/install that -Stage off builds)'; exit 4 }
        Log 'PENDING: devoff4b-bin is not staged yet'
    } else {
        foreach ($d in 'rexruntime.dll', 'rexgpu-xenos.dll') {
            if ((Sha "$I\$d") -ne (Sha "$A\devoff4b-bin\$d")) { Log "STOP: install/bin/$d != devoff4b-bin's (the SDK changed after devoff4b)"; exit 4 }
        }
    }
}
if ($Stage -eq 'off') {
    $mkSdk = { param($j) @($bs, '-Phase', 'sdk', '-Tag', $tag, '-Jobs', "$j", '-KeepGoing', '-SkipConfigure') }
    $mkGame = { param($j) @($bs, '-Phase', 'game', '-Tag', $tag, '-Jobs', "$j", '-KeepGoing') }
    $mkAgain = { param($j) @($bs, '-Phase', 'game', '-Tag', "${tag}r", '-Jobs', "$j", '-KeepGoing', '-SkipConfigure') }
} else {
    $mkSdk = $null
    $mkGame = { param($j) @($bs, '-Phase', 'game', '-Native', '-Tag', $tag, '-Jobs', "$j", '-PrelinkJobs', "$j", '-KeepGoing') }
    $mkAgain = { param($j) @($bs, '-Phase', 'game', '-Native', '-Tag', "${tag}r", '-Jobs', "$j", '-PrelinkJobs', "$j", '-KeepGoing', '-SkipConfigure') }
}
$bt = $tag
$what = $(if ($Stage -eq 'off') { "dev OFF build 4b (S4b = S4a + SDK C1 $C1 + M1 + P2c + r1r2 + #26 tool with every new switch OFF + S4c #24 and #30 OFF): NATIVE_GPU=OFF" }
    else { "native build 4b (S4b = S4a + SDK C1 $C1 + M1 + P2c + r1r2 + #26 tool with every new switch OFF + C1 memory_watch.cpp + S4c CMake): NATIVE_GPU=ON with Agent 6 AOT inputs" })
$stageArgsFor = { param($bt_) @("$A\stage-snap-bin.ps1", '-Variant', $(if ($Stage -eq 'off') { 'off' } else { 'native' }), '-SnapTag', $SnapTag, '-BuildTag', $bt_, '-OutDir', $O,
        '-PatchTagList', 'S1,S2,S3,S3d,S4a,S4b', '-RuntimeStrings', ($rt -join ','), '-XenosStrings', ($xe -join ','), '-ExeStrings', ($exe -join ','),
        '-ManifestNotesFile', $notes, '-WhatText', $what) }
if ($DryRun) {
    if ($mkSdk) { Log "PLAN 1: powershell -File $((& $mkSdk $Jobs) -join ' ')" }
    Log "PLAN 2: powershell -File $((& $mkGame $Jobs) -join ' ')"
    Log "PLAN 3 (only if $(Split-Path -Leaf $B)/rexruntime.dll != install/bin): rename exe + map to *.pre-$SnapTag, powershell -File $((& $mkAgain $Jobs) -join ' ')"
    Log "PLAN 4: powershell $('-NoProfile -ExecutionPolicy Bypass -File ' + ((& $stageArgsFor $tag | ForEach-Object { Q $_ }) -join ' '))"
    Log "PLAN 5: compare each staged file with $refL (rexruntime.dll, rexgpu-xenos.dll, legodimensions.exe must differ); exe must not contain [$($absent -join ', ')]"
    Log 'DRY-RUN done: nothing built'
    exit 0
}
$t0 = [Diagnostics.Stopwatch]::StartNew()
Log "START $SnapTag $Stage (tag $tag, -j $Jobs, Below Normal) -> $(Split-Path -Leaf $O)"
if ($mkSdk) {
    $c = RunJobs 'sdk build + install' $mkSdk
    if ($c -ne 0) { Log "STOP: build-snap.ps1 -Phase sdk exit $c (see $tag-steps.txt)"; exit 10 }
}
$c = RunJobs "$Stage game build" $mkGame
if ($c -ne 0) { Log "STOP: build-snap.ps1 -Phase game exit $c (see $tag-steps.txt)"; exit 10 }
$h2 = Sha "$I\rexruntime.dll"
$h1 = Sha "$B\rexruntime.dll"
if ($h1 -ne $h2) {
    Log ("rexruntime.dll in {0} ({1}) != install/bin ({2}): the exe did not relink; renaming exe + map to *.pre-{3}, relinking" -f
        (Split-Path -Leaf $B), $h1.Substring(0, 16), $h2.Substring(0, 16), $SnapTag)
    foreach ($f in 'legodimensions.exe', 'legodimensions.map') {
        $p = "$B\$f"; $dst = "$p.pre-$SnapTag"
        if (Test-Path -LiteralPath $dst) { $dst = "$dst-$(Get-Date -Format HHmmss)" }
        if (Test-Path -LiteralPath $p) { Rename-Item -LiteralPath $p -NewName (Split-Path -Leaf $dst); Log "  renamed $f -> $(Split-Path -Leaf $dst)" }
    }
    $c = RunJobs 'relink' $mkAgain
    if ($c -ne 0) { Log "STOP: relink build-snap.ps1 exit $c (see ${tag}r-steps.txt)"; exit 11 }
    $bt = "${tag}r"
    $h1 = Sha "$B\rexruntime.dll"
    if ($h1 -ne $h2) { Log "STOP: rexruntime.dll in $(Split-Path -Leaf $B) still differs from install/bin after the relink"; exit 12 }
}
Log "rexruntime.dll in $(Split-Path -Leaf $B) == install/bin ($($h2.Substring(0, 16)))"
$tuSnap = "$A\snap1\DimensionsRecomp\rexlego\src\gpu_wait_backoff.cpp"
Log "S4c TU in snap1: $((Sha $tuSnap).Substring(0, 16)) (want 01D9F8F3 LF or 34D281E0 CRLF)"
$stLog = "$A\$tag-stage-$Stage.log"
$c = RunPolled 'stage' (& $stageArgsFor $bt) $stLog
if ($c -eq 'HOLD') { Log "STOP: $hold appeared during staging; killed; re-run after Agent 1's resume (the out folder may need removing if MANIFEST.txt is missing)"; exit 30 }
foreach ($l in @(Get-Content $stLog | Select-Object -Last 2)) { Log "  $l" }
if ($c -ne 0) { Log "STOP: stage-snap-bin.ps1 exit $c (see $(Split-Path -Leaf $stLog))"; exit 13 }
$bad = 0
foreach ($f in @(Get-ChildItem -LiteralPath $O -File | Where-Object { $_.Name -ne 'MANIFEST.txt' } | Sort-Object Name)) {
    $h = Sha $f.FullName; $rp = Join-Path $ref $f.Name
    $cmp = $(if (-not (Test-Path -LiteralPath $rp)) { "not in $refL" } elseif ((Sha $rp) -eq $h) { "== $refL" } else { "differs from $refL" })
    if ($f.Name -in 'rexruntime.dll', 'rexgpu-xenos.dll', 'legodimensions.exe' -and $cmp -ne "differs from $refL") { $cmp += ' : FAIL, the S4b changes must be in it'; $bad++ }
    Log ("  staged {0}: {1} B, sha256 {2}; {3}" -f $f.Name, $f.Length, $h, $cmp)
}
$exeText = [Text.Encoding]::ASCII.GetString([IO.File]::ReadAllBytes("$O\legodimensions.exe"))
foreach ($s in $absent) {
    $has = $exeText.Contains($s)
    Log ("  legodimensions.exe {0} '{1}'{2}" -f $(if ($has) { 'CONTAINS' } else { 'does not contain' }), $s, $(if ($has) { ' : FAIL (S4c is for OFF builds only)' } else { ' (ok)' }))
    if ($has) { $bad++ }
}
$exeText = $null; [GC]::Collect()
Log ("  staged MANIFEST.txt: {0} B, sha256 {1}" -f (Get-Item -LiteralPath "$O\MANIFEST.txt").Length, (Sha "$O\MANIFEST.txt"))
$man = @(Get-Content -Encoding UTF8 -LiteralPath "$O\MANIFEST.txt")
$cnt = @(foreach ($t in 'S1', 'S2', 'S3', 'S3d', 'S4a', 'S4b') { "$t $(@($man | Where-Object { $_.StartsWith("#   $t ") }).Count)" })
$np = @($man | Where-Object { $_.StartsWith('#   PASS ') }).Count; $nf = @($man | Where-Object { $_.StartsWith('#   FAIL ') }).Count
$nn = @($man | Where-Object { $_.StartsWith('#   NOTE ') }).Count
Log "  MANIFEST patch rows: $($cnt -join ' / '); checks: $np PASS / $nf FAIL / $nn NOTE"
$pat = (@($rt) + @($xe) + @($exe) | Select-Object -Skip 0 | Where-Object { $_ -match '^[A-Za-z0-9_]+$' } | ForEach-Object { [regex]::Escape($_) }) -join '|'
foreach ($l in @($man | Where-Object { $_ -match "contains '($pat)'" })) { Log "  $($l.Trim())" }
if ($Stage -eq 'native') { Log "  native GPU fingerprint: $((Get-Content "$B\native-gpu-build.txt" -Raw).Trim())" }
if ($bad) { Log "STOP: $bad FAIL(s) in the comparison with $refL / the absent-string check"; exit 15 }
Log ("DONE $SnapTag $Stage, total wall {0:N1}s" -f $t0.Elapsed.TotalSeconds)
exit 0

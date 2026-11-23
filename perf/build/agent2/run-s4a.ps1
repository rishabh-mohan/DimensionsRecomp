# Agent 2 - S4a builds (task #4, board run 2): snap1 at S4a (prep-s4a.py: S3d + SDK #7 u diag, #8 P2, #5 fix (i),
# #38 precise wait, new switches all default OFF, + #32 warm-boot fix always on, + #2 miss cache, native only) ->
# build/agent2/devoff4-bin and native4-bin. Run as a run_command background task; it stops at the first failure;
# build/agent2/stop-snap.ps1 kills it.
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\run-s4a.ps1 -Stage off
#       SDK build + install (snap1-sdk, -SkipConfigure: 5 changed .cpp files, no new file), then the devoff4 game build
#       (snap1-off, -SkipConfigure), then stage-snap-bin.ps1 -Variant off -> build/agent2/devoff4-bin
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\run-s4a.ps1 -Stage native
#       native4 game build (snap1-on) with the explicit configure, as S3d, then stage-snap-bin.ps1 -Variant native
#       -> build/agent2/native4-bin. Needs devoff4-bin first (it links against the S4a snap1-sdk/install).
# Guards before anything builds: no start at or after -Latest (13:50: builds end by 14:00), -Jobs capped at 10, no other
# snapshot build driver, S4a-notes.txt present, snap-patch.py verify S4a PASS, PATCHES-S4a.tsv = 6 rows and every snap1
# copy == its after-hash, the out folder not staged yet; native: devoff4-bin staged and install/bin rexruntime.dll and
# rexgpu-xenos.dll == devoff4-bin's. Relink contingency as run-s3.ps1 (not started at or after 13:58).
# stage-snap-bin.ps1 gets -PatchTagList S1,S2,S3,S3d,S4a (its default for S4a would skip S3d) and no -CompareBin (the
# S4a SDK DLLs differ by design); each staged file is compared with devoff3-bin / native3d-bin here instead, and
# rexruntime.dll and rexgpu-xenos.dll must differ (the S4a SDK changes are compiled into them).
# Log: build/agent2/snap4a-run.txt (+ build-snap's snap4a-steps.txt and logs, and snap4a-stage-<stage>.log).
param([ValidateSet('off', 'native')][string]$Stage = 'off', [int]$Jobs = 10, [string]$Latest = '13:50')
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
$A = "$R\build\agent2"
$SnapTag = 'S4a'; $tag = 'snap4a'
$runLog = "$A\$tag-run.txt"
$notes = "$A\$SnapTag-notes.txt"
# literals of 16+ chars: kept from S3 (pause_safe_order description tail in the exe; Agent 12's #22 cvar name and
# description in rexruntime.dll; Agent 5's / Agent 7's environment toggles in the native exe) + the 4 new S4a cvars
# (rexruntime.dll: xmemory.cpp and timer_queue.cpp (rexcore); rexgpu-xenos.dll: both shared_memory.cpp) + the #2 toggle
$rtStrings = 'audio_shutdown_detach_worker,leave it running and leak what it can still reach,physical_protect_hold_global_lock,timer_queue_precise_wait'
$xeStrings = 'shared_memory_upload_hash_log,shared_memory_single_hold_rearm'
$exeStrings = 'which can hang when the guest pauses'
if ($Stage -eq 'native') { $exeStrings += ',LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD,LEGO_NATIVE_FPS_CELL_RECTS,LEGO_NATIVE_TEXTURE_STAGING_POOL,LEGO_NATIVE_SHADER_MISS_CACHE' }
function Log([string]$m) {
    $line = "$(Get-Date -Format HH:mm:ss) [$SnapTag $Stage] $m"
    $line | Out-File -Append -Encoding utf8 $runLog
    Write-Host $line
}
function Run([string]$what, [string[]]$argv, [string]$out) {
    # powershell -File <argv>: the exit code is the script's exit code (1 on an unhandled error)
    Log "BEGIN $what : $($argv -join ' ')"
    $sw = [Diagnostics.Stopwatch]::StartNew()
    if ($out) { & powershell -NoProfile -ExecutionPolicy Bypass -File @argv > $out 2>&1 }
    else { & powershell -NoProfile -ExecutionPolicy Bypass -File @argv | Out-Null }
    $code = $LASTEXITCODE
    Log ("END   $what exit=$code wall={0:N1}s freeC={1:N2}GB" -f $sw.Elapsed.TotalSeconds, ((Get-PSDrive C).Free / 1GB))
    return $code
}
function Sha([string]$p) { (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash }
# guards (nothing is built or written before they pass, except this log)
if ((Get-Date).TimeOfDay -ge [TimeSpan]::Parse($Latest + ':00')) { Log "STOP: no build starts at or after $Latest (builds end by 14:00)"; exit 3 }
if ($Jobs -gt 10) { Log "-Jobs $Jobs capped at 10"; $Jobs = 10 }
$drv = @(Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -match 'run-b\.ps1|b-chain\.ps1|rb-chain\.ps1|run-(s2|s3|s3d|s3e|nb|rb1|rb2)\.ps1|prep-s4a\.py|build-snap\.ps1|stage-snap-bin\.ps1' })
if ($drv.Count) { Log "STOP: another snapshot build driver is running (pid $($drv[0].ProcessId): $($drv[0].CommandLine))"; exit 4 }
if (-not (Test-Path -LiteralPath $notes)) { Log "STOP: $notes is missing (prep-s4a.py writes it)"; exit 4 }
$vo = "$A\$tag-verify-$Stage.txt"
& python "$A\snap-patch.py" verify $SnapTag > $vo 2>&1
$vc = $LASTEXITCODE
Log "verify $SnapTag : exit $vc : $(@(Get-Content $vo)[0])"
if ($vc -ne 0) { Log "STOP: snap1 is not $SnapTag (see $(Split-Path -Leaf $vo))"; exit 5 }
$pt = "$A\snap1\PATCHES-$SnapTag.tsv"
$rows = @(Get-Content -Encoding UTF8 -LiteralPath $pt | Where-Object { $_ -and -not $_.StartsWith('#') })
if ($rows.Count -ne 6) { Log "STOP: PATCHES-$SnapTag.tsv has $($rows.Count) data rows, not 6"; exit 6 }
foreach ($row in $rows) {
    $c = @($row -split "`t")
    $h = Sha ("$A\snap1\DimensionsRecomp\" + $c[0].Replace('/', '\'))
    if ($h -ne $c[2].ToUpper()) { Log "STOP: snap1 $($c[0]) is $($h.Substring(0, 16)), but PATCHES-$SnapTag.tsv says $($c[2].Substring(0, 16))"; exit 6 }
    Log ("  {0}: {1} -> {2} == snap1" -f $c[0], $c[1].Substring(0, 16), $h.Substring(0, 16))
}
$B = $(if ($Stage -eq 'off') { "$A\snap1-off" } else { "$A\snap1-on" })
$O = $(if ($Stage -eq 'off') { "$A\devoff4-bin" } else { "$A\native4-bin" })
$ref = $(if ($Stage -eq 'off') { "$A\devoff3-bin" } else { "$A\native3d-bin" })
$refL = Split-Path -Leaf $ref
if (Test-Path -LiteralPath "$O\MANIFEST.txt") { Log "STOP: $(Split-Path -Leaf $O) is already staged (MANIFEST.txt exists)"; exit 4 }
$I = "$A\snap1-sdk\install\bin"
if ($Stage -eq 'native') {
    if (-not (Test-Path -LiteralPath "$A\devoff4-bin\MANIFEST.txt")) { Log 'STOP: devoff4-bin is not staged (native4 links against the S4a snap1-sdk/install that -Stage off builds)'; exit 4 }
    foreach ($d in 'rexruntime.dll', 'rexgpu-xenos.dll') {
        if ((Sha "$I\$d") -ne (Sha "$A\devoff4-bin\$d")) { Log "STOP: install/bin/$d != devoff4-bin's (the SDK changed after devoff4)"; exit 4 }
    }
}
$bs = "$A\build-snap.ps1"
if ($Stage -eq 'off') {
    $first = @($bs, '-Phase', 'all', '-Tag', $tag, '-Jobs', "$Jobs", '-KeepGoing', '-SkipConfigure')
    $again = @($bs, '-Phase', 'game', '-Tag', "${tag}r", '-Jobs', "$Jobs", '-KeepGoing', '-SkipConfigure')
} else {
    $first = @($bs, '-Phase', 'game', '-Native', '-Tag', $tag, '-Jobs', "$Jobs", '-PrelinkJobs', "$Jobs", '-KeepGoing')
    $again = @($bs, '-Phase', 'game', '-Native', '-Tag', "${tag}r", '-Jobs', "$Jobs", '-PrelinkJobs', "$Jobs", '-KeepGoing', '-SkipConfigure')
}
$t0 = [Diagnostics.Stopwatch]::StartNew()
Log "START $SnapTag $Stage (tag $tag, -j $Jobs) -> $(Split-Path -Leaf $O)"
$c = Run 'build' $first ''
if ($c -ne 0) { Log "STOP: build-snap.ps1 exit $c (see $tag-steps.txt)"; exit 10 }
$bt = $tag
$h2 = Sha "$I\rexruntime.dll"
$h1 = Sha "$B\rexruntime.dll"
if ($h1 -ne $h2) {
    if ((Get-Date).TimeOfDay -ge [TimeSpan]'13:58:00') { Log 'STOP: the exe did not relink and it is 13:58 (builds end by 14:00); no relink'; exit 14 }
    Log ("rexruntime.dll in {0} ({1}) != install/bin ({2}): the exe did not relink; renaming exe + map to *.pre-{3}, relinking" -f
        (Split-Path -Leaf $B), $h1.Substring(0, 16), $h2.Substring(0, 16), $SnapTag)
    foreach ($f in 'legodimensions.exe', 'legodimensions.map') {
        $p = "$B\$f"; $dst = "$p.pre-$SnapTag"
        if (Test-Path -LiteralPath $dst) { $dst = "$dst-$(Get-Date -Format HHmmss)" }
        if (Test-Path -LiteralPath $p) { Rename-Item -LiteralPath $p -NewName (Split-Path -Leaf $dst); Log "  renamed $f -> $(Split-Path -Leaf $dst)" }
    }
    $c = Run 'relink' $again ''
    if ($c -ne 0) { Log "STOP: relink build-snap.ps1 exit $c (see ${tag}r-steps.txt)"; exit 11 }
    $bt = "${tag}r"
    $h1 = Sha "$B\rexruntime.dll"
    if ($h1 -ne $h2) { Log "STOP: rexruntime.dll in $(Split-Path -Leaf $B) still differs from install/bin after the relink"; exit 12 }
}
Log "rexruntime.dll in $(Split-Path -Leaf $B) == install/bin ($($h2.Substring(0, 16)))"
# no apostrophes in the passed values (powershell -File)
$what = $(if ($Stage -eq 'off') { 'dev OFF build 4 (S4a = S3d + SDK #7 #8 #5(i) #38 with every new switch OFF + #32 always on): NATIVE_GPU=OFF' }
    else { 'native build 4 (S4a = S3d + SDK #7 #8 #5(i) #38 with every new switch OFF + #32 always on + #2 miss cache, OFF by default): NATIVE_GPU=ON with Agent 6 AOT inputs' })
$stageArgs = @("$A\stage-snap-bin.ps1", '-Variant', $Stage, '-SnapTag', $SnapTag, '-BuildTag', $bt, '-OutDir', $O,
    '-PatchTagList', 'S1,S2,S3,S3d,S4a', '-RuntimeStrings', $rtStrings, '-XenosStrings', $xeStrings, '-ExeStrings', $exeStrings,
    '-ManifestNotesFile', $notes, '-WhatText', $what)
$stLog = "$A\$tag-stage-$Stage.log"
$c = Run 'stage' $stageArgs $stLog
foreach ($l in @(Get-Content $stLog | Select-Object -Last 2)) { Log "  $l" }
if ($c -ne 0) { Log "STOP: stage-snap-bin.ps1 exit $c (see $(Split-Path -Leaf $stLog))"; exit 13 }
$bad = 0
foreach ($f in @(Get-ChildItem -LiteralPath $O -File | Where-Object { $_.Name -ne 'MANIFEST.txt' } | Sort-Object Name)) {
    $h = Sha $f.FullName; $rp = Join-Path $ref $f.Name
    $cmp = $(if (-not (Test-Path -LiteralPath $rp)) { "not in $refL" } elseif ((Sha $rp) -eq $h) { "== $refL" } else { "differs from $refL" })
    if ($f.Name -in 'rexruntime.dll', 'rexgpu-xenos.dll' -and $cmp -ne "differs from $refL") { $cmp += ' : FAIL, the S4a SDK changes must be in it'; $bad++ }
    Log ("  staged {0}: {1} B, sha256 {2}; {3}" -f $f.Name, $f.Length, $h, $cmp)
}
Log ("  staged MANIFEST.txt: {0} B, sha256 {1}" -f (Get-Item -LiteralPath "$O\MANIFEST.txt").Length, (Sha "$O\MANIFEST.txt"))
$man = @(Get-Content -Encoding UTF8 -LiteralPath "$O\MANIFEST.txt")
$cnt = @(foreach ($t in 'S1', 'S2', 'S3', 'S3d', 'S4a') { "$t $(@($man | Where-Object { $_.StartsWith("#   $t ") }).Count)" })
$np = @($man | Where-Object { $_.StartsWith('#   PASS ') }).Count; $nf = @($man | Where-Object { $_.StartsWith('#   FAIL ') }).Count
$nn = @($man | Where-Object { $_.StartsWith('#   NOTE ') }).Count
Log "  MANIFEST patch rows: $($cnt -join ' / '); checks: $np PASS / $nf FAIL / $nn NOTE"
foreach ($l in @($man | Where-Object { $_ -match "contains '(shared_memory_upload_hash_log|shared_memory_single_hold_rearm|physical_protect_hold_global_lock|timer_queue_precise_wait|LEGO_NATIVE_SHADER_MISS_CACHE)'" })) { Log "  $($l.Trim())" }
if ($Stage -eq 'native') { Log "  native GPU fingerprint: $((Get-Content "$B\native-gpu-build.txt" -Raw).Trim())" }
if ($bad) { Log "STOP: $bad staged SDK DLL(s) identical to $refL"; exit 15 }
Log ("DONE $SnapTag $Stage, total wall {0:N1}s" -f $t0.Elapsed.TotalSeconds)
exit 0

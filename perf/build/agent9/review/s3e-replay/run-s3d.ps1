# Agent 2 - native3d: snap1 at S3d -> build/agent2/native3d-bin, at Agent 1's explicit GO only. S3d = S3 + exactly
# Agent 4's live write of rexlego/src/gpu_native/draw.cpp: prep-s3d.py <sha256> --go HH:MM writes S3d-rules.txt and
# S3d-notes.txt, then snap-patch.py apply S3d build\agent2\S3d-rules.txt --note-file=build\agent2\S3d-notes.txt.
# Native only: draw.cpp is not compiled into OFF builds (snap1-off compile_commands.json lists no gpu_native file), so
# devoff3-bin stays the OFF build of S3d; the SDK is not rebuilt (no SDK file changed since S3). The generated code
# stays the pinned S1 output, as in S1-S3. Run as a run_command background task; it stops at the first failure;
# build/agent2/stop-snap.ps1 kills it.
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\run-s3d.ps1 [-Jobs 10] [-ExtraExeStrings 'a,b']
#       native3d game build (snap1-on, tag snap3d) with the explicit configure, as S2/S3 (the native GPU fingerprint
#       hashes draw.cpp), then stage-snap-bin.ps1 -Variant native -SnapTag S3d -> build/agent2/native3d-bin with
#       -CompareBin native3-bin: every staged file but the exe and map must equal native3's, and the exe must differ.
#       -ExtraExeStrings: more comma-free literals of 16+ chars the exe must contain (e.g. new in Agent 4's draw.cpp).
# Guards before anything builds: no start 08:30-12:00 (no builds from 08:30), -Jobs capped at 10, native3-bin staged,
# no other snapshot build driver running, S3d-notes.txt present, snap-patch.py verify S3d PASS (snap1 == the latest
# STATE-S3d-*.tsv), PATCHES-S3d.tsv holds exactly the draw.cpp row and snap1's draw.cpp has its after-hash.
# If the tree's rexruntime.dll differs from snap1-sdk/install/bin after the build (the exe did not relink), the exe
# and map are renamed *.pre-S3d and the game phase runs again as tag snap3dr (gen-check + gate + relink), as in
# run-s3.ps1. Nothing is hand-copied.
# Log: build/agent2/snap3d-run.txt (+ build-snap's snap3d-steps.txt and logs, and snap3d-stage-native.log).
param([int]$Jobs = 10, [string]$ExtraExeStrings = '')
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
$A = "$R\build\agent2"
$SnapTag = 'S3d'; $Stage = 'native'; $tag = 'snap3d'; $Rel = 'rexlego/src/gpu_native/draw.cpp'
$runLog = "$A\$tag-run.txt"
$notes = "$A\$SnapTag-notes.txt"
$ref = "$A\native3-bin"
# literals of 16+ chars, as native3 (run-s3.ps1): the tail of Agent 12's pause_safe_order description (exe), Agent
# 12's #22 cvar name and description (rexruntime.dll), Agent 5's / Agent 7's environment toggles (native exe)
$rtStrings = 'audio_shutdown_detach_worker,leave it running and leak what it can still reach'
$exeStrings = 'which can hang when the guest pauses,LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD,LEGO_NATIVE_FPS_CELL_RECTS,LEGO_NATIVE_TEXTURE_STAGING_POOL'
if ($ExtraExeStrings.Trim()) { $exeStrings += ',' + $ExtraExeStrings.Trim() }
function Log([string]$m) {
    $line = "$(Get-Date -Format HH:mm:ss) [$SnapTag] $m"
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
# guards (nothing is built or written before they pass, except this log)
$tod = (Get-Date).TimeOfDay
if ($tod -ge [TimeSpan]'08:30:00' -and $tod -lt [TimeSpan]'12:00:00') { Log 'STOP: no builds from 08:30 (session-3 rule)'; exit 3 }
if ($Jobs -gt 10) { Log "-Jobs $Jobs capped at 10"; $Jobs = 10 }
if (-not (Test-Path -LiteralPath "$ref\MANIFEST.txt")) { Log "STOP: native3-bin is not staged (no $ref\MANIFEST.txt; it is the -CompareBin reference)"; exit 4 }
$drv = @(Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -match 'run-b\.ps1|b-chain\.ps1|prep-b\.py|run-s2\.ps1|run-s3\.ps1|build-snap\.ps1|stage-snap-bin\.ps1' })
if ($drv.Count) { Log "STOP: another snapshot build driver is running (pid $($drv[0].ProcessId): $($drv[0].CommandLine))"; exit 4 }
if (-not (Test-Path -LiteralPath $notes)) { Log "STOP: $notes is missing (the $SnapTag MANIFEST notes; prep-s3d.py writes it)"; exit 4 }
$vo = "$A\$tag-verify-$Stage.txt"
& python "$A\snap-patch.py" verify $SnapTag > $vo 2>&1
$vc = $LASTEXITCODE
Log "verify $SnapTag : exit $vc : $(@(Get-Content $vo)[0])"
if ($vc -ne 0) { Log "STOP: snap1 is not $SnapTag (see $(Split-Path -Leaf $vo))"; exit 5 }
$pt = "$A\snap1\PATCHES-$SnapTag.tsv"
$rows = @(); if (Test-Path -LiteralPath $pt) { $rows = @(Get-Content -Encoding UTF8 -LiteralPath $pt | Where-Object { $_ -and -not $_.StartsWith('#') }) }
$pc = $(if ($rows.Count) { @($rows[0] -split "`t") } else { @('', '', '') })
if ($rows.Count -ne 1 -or $pc[0] -ne $Rel -or $pc.Count -lt 3) { Log "STOP: PATCHES-$SnapTag.tsv must hold exactly the $Rel row ($($rows.Count) data row(s), first '$($pc[0])')"; exit 6 }
$snapDraw = "$A\snap1\DimensionsRecomp\" + $Rel.Replace('/', '\')
$hs = (Get-FileHash -LiteralPath $snapDraw).Hash
if ($hs -ne $pc[2].ToUpper()) { Log "STOP: snap1 $Rel is $($hs.Substring(0, 16)), but PATCHES-$SnapTag.tsv says $($pc[2].Substring(0, 16))"; exit 6 }
Log ("PATCHES-{0}.tsv: 1 row, {1} {2} -> {3}; snap1 copy == after" -f $SnapTag, $Rel, $pc[1].Substring(0, 16).ToUpper(), $hs.Substring(0, 16))
$hl = (Get-FileHash -LiteralPath ("$R\DimensionsRecomp\" + $Rel.Replace('/', '\'))).Hash
if ($hl -ne $hs) { Log "NOTE: live $Rel is now $($hl.Substring(0, 16)) (written again after the $SnapTag apply); native3d builds snap1's $($hs.Substring(0, 16))" }
$B = "$A\snap1-on"; $O = "$A\native3d-bin"
$inst = "$A\snap1-sdk\install\bin\rexruntime.dll"
$bs = "$A\build-snap.ps1"
$first = @($bs, '-Phase', 'game', '-Native', '-Tag', $tag, '-Jobs', "$Jobs", '-PrelinkJobs', "$Jobs", '-KeepGoing')
$again = @($bs, '-Phase', 'game', '-Native', '-Tag', "${tag}r", '-Jobs', "$Jobs", '-PrelinkJobs', "$Jobs", '-KeepGoing', '-SkipConfigure')
$t0 = [Diagnostics.Stopwatch]::StartNew()
Log "START $SnapTag $Stage (tag $tag, -j $Jobs) -> $(Split-Path -Leaf $O)"
$c = Run 'build' $first ''
if ($c -ne 0) { Log "STOP: build-snap.ps1 exit $c (see $tag-steps.txt)"; exit 10 }
$bt = $tag
$h2 = (Get-FileHash -LiteralPath $inst).Hash
$h1 = (Get-FileHash -LiteralPath "$B\rexruntime.dll").Hash
if ($h1 -ne $h2) {
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
    $h1 = (Get-FileHash -LiteralPath "$B\rexruntime.dll").Hash
    if ($h1 -ne $h2) { Log "STOP: rexruntime.dll in $(Split-Path -Leaf $B) still differs from install/bin after the relink"; exit 12 }
}
Log "rexruntime.dll in $(Split-Path -Leaf $B) == install/bin ($($h2.Substring(0, 16)))"
# no apostrophes in the passed values (powershell -File)
$stageArgs = @("$A\stage-snap-bin.ps1", '-Variant', $Stage, '-SnapTag', $SnapTag, '-BuildTag', $bt, '-OutDir', $O,
    '-RuntimeStrings', $rtStrings, '-ExeStrings', $exeStrings, '-ManifestNotesFile', $notes, '-CompareBin', $ref,
    '-CompareWhy', "S3d changed $Rel", '-WhatText', 'native build 3d (S3 + the Agent 4 draw.cpp write): NATIVE_GPU=ON with Agent 6 AOT inputs')
$stLog = "$A\$tag-stage-$Stage.log"
$c = Run 'stage' $stageArgs $stLog
foreach ($l in @(Get-Content $stLog | Where-Object { $_ -match 'native3-bin' })) { Log "  $l" }
foreach ($l in @(Get-Content $stLog | Select-Object -Last 2)) { Log "  $l" }
if ($c -ne 0) { Log "STOP: stage-snap-bin.ps1 exit $c (see $(Split-Path -Leaf $stLog))"; exit 13 }
foreach ($f in 'legodimensions.exe', 'legodimensions.map', 'rexruntime.dll', 'rexgpu-xenos.dll', 'MANIFEST.txt') {
    $p = "$O\$f"
    if (Test-Path -LiteralPath $p) { Log ("  staged {0}: {1} B, sha256 {2}" -f $f, (Get-Item -LiteralPath $p).Length, (Get-FileHash -LiteralPath $p).Hash) }
}
$man = @(Get-Content -Encoding UTF8 -LiteralPath "$O\MANIFEST.txt")
$cnt = @(foreach ($t in 'S1', 'S2', 'S3', 'S3d') { "$t $(@($man | Where-Object { $_.StartsWith("#   $t ") }).Count)" })
$np = @($man | Where-Object { $_.StartsWith('#   PASS ') }).Count; $nf = @($man | Where-Object { $_.StartsWith('#   FAIL ') }).Count
$nn = @($man | Where-Object { $_.StartsWith('#   NOTE ') }).Count
Log "  MANIFEST patch rows: $($cnt -join ' / '); checks: $np PASS / $nf FAIL / $nn NOTE"
Log "  native GPU fingerprint: $((Get-Content "$B\native-gpu-build.txt" -Raw).Trim())"
Log ("DONE $SnapTag $Stage, total wall {0:N1}s" -f $t0.Elapsed.TotalSeconds)
exit 0

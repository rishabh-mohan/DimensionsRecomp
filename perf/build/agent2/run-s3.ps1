# Agent 2 - S3 builds from snap1 after snap-patch.py apply S3 (Agent 10's build/agent10/s3/S3-include.tsv, sha256
# A1E7C83F7CFA1372..., 28 INCLUDE / 0 EXCLUDE vs STATE-S2-2315), run as a run_command background task. It stops at the
# first failure; build/agent2/stop-snap.ps1 kills it.
# S3's build inputs: game commit 001336f + SDK commit c5fe668 plus the pre-sprint plume and simde edits, as in S1/S2
# (Agent 1, 02:22; recorded in PATCHES-S3.tsv, STATE-S3-*.tsv and each MANIFEST from build/agent2/S3-notes.txt). The
# generated code stays the pinned S1 output (gen-check against baseline/), as in S1/S2; only build B uses batch-nolr.
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\run-s3.ps1 -Stage off
#       SDK build + install (snap1-sdk, -SkipConfigure: no CMake input changed; of the 3 new SDK files, flush_mode.h is
#       a header that no CMake glob lists and the 2 test inputs are unused with tests off), then the devoff3 game build
#       (snap1-off, -SkipConfigure: no game file is new and the OFF tree has no CONFIGURE_DEPENDS glob), then
#       stage-snap-bin.ps1 -Variant off -> build/agent2/devoff3-bin
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\run-s3.ps1 -Stage native
#       native3 game build (snap1-on) with the explicit configure, as S2, then stage-snap-bin.ps1 -Variant native
#       -> build/agent2/native3-bin. Run it after -Stage off: it links against the snap1-sdk/install that stage installs.
# Guards before anything builds: no start 08:30-12:00 (no builds from 08:30), -Jobs capped at 10, build B staged
# (build/agent2/devoffB-bin/MANIFEST.txt: S3 rebuilds snap1-sdk/install, which B links against) and no B driver
# running, S3-notes.txt present, snap-patch.py verify S3 PASS (snap1 == the latest STATE-S3-*.tsv).
# rexruntime.dll reaches a game tree only through the exe's POST_BUILD copy (rexglue_helpers.cmake:105-108). If the
# tree's copy differs from snap1-sdk/install/bin after the build (the exe did not relink), the exe and map are renamed
# *.pre-<SnapTag> and the game phase runs again as tag <tag>r (gen-check + gate + relink). Nothing is hand-copied.
# Log: build/agent2/<tag>-run.txt (+ build-snap's <tag>-steps.txt and logs, and <tag>-stage-<stage>.log).
param([ValidateSet('off', 'native')][string]$Stage = 'off', [int]$Jobs = 10, [string]$SnapTag = 'S3')
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
$A = "$R\build\agent2"
if ($SnapTag -notmatch '^S(\d+)$') { Write-Host "bad -SnapTag $SnapTag"; exit 2 }
$N = $Matches[1]
$tag = "snap$N"
$runLog = "$A\$tag-run.txt"
$notes = "$A\$SnapTag-notes.txt"
# literals of 16+ chars. New in S3 (in neither devoff2-bin nor native2-bin, checked 02:31): the tail of Agent 12's
# pause_safe_order description 'Off: the original order, which can hang when the guest pauses' (exe, both variants);
# stage-snap-bin.ps1 splits on commas, so only the comma-free tail is given. Kept from S2 as presence checks: Agent
# 12's #22 cvar name and description (rexruntime.dll) and Agent 5's / Agent 7's environment toggles (native exe).
$rtStrings = 'audio_shutdown_detach_worker,leave it running and leak what it can still reach'
$exeStrings = 'which can hang when the guest pauses'
if ($Stage -eq 'native') { $exeStrings += ',LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD,LEGO_NATIVE_FPS_CELL_RECTS,LEGO_NATIVE_TEXTURE_STAGING_POOL' }
function Log([string]$m) {
    $line = "$(Get-Date -Format HH:mm:ss) [$Stage] $m"
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
if (-not (Test-Path -LiteralPath "$A\devoffB-bin\MANIFEST.txt")) {
    Log 'STOP: build B is not staged (no devoffB-bin\MANIFEST.txt); S3 rebuilds snap1-sdk/install, which B links against'; exit 4
}
$bdrv = @(Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -match 'run-b\.ps1|b-chain\.ps1|prep-b\.py' })
if ($bdrv.Count) { Log "STOP: a build B driver is still running (pid $($bdrv[0].ProcessId))"; exit 4 }
if (-not (Test-Path -LiteralPath $notes)) { Log "STOP: $notes is missing (the $SnapTag MANIFEST notes)"; exit 4 }
$vo = "$A\$tag-verify-$Stage.txt"
& python "$A\snap-patch.py" verify $SnapTag > $vo 2>&1
$vc = $LASTEXITCODE
Log "verify $SnapTag : exit $vc : $(@(Get-Content $vo)[0])"
if ($vc -ne 0) { Log "STOP: snap1 is not $SnapTag (see $(Split-Path -Leaf $vo))"; exit 5 }
$B = $(if ($Stage -eq 'off') { "$A\snap1-off" } else { "$A\snap1-on" })
$O = $(if ($Stage -eq 'off') { "$A\devoff$N-bin" } else { "$A\native$N-bin" })
$inst = "$A\snap1-sdk\install\bin\rexruntime.dll"
$bs = "$A\build-snap.ps1"
if ($Stage -eq 'off') {
    $first = @($bs, '-Phase', 'all', '-Tag', $tag, '-Jobs', "$Jobs", '-KeepGoing', '-SkipConfigure')
    $again = @($bs, '-Phase', 'game', '-Tag', "${tag}r", '-Jobs', "$Jobs", '-KeepGoing', '-SkipConfigure')
} else {
    $first = @($bs, '-Phase', 'game', '-Native', '-Tag', $tag, '-Jobs', "$Jobs", '-PrelinkJobs', "$Jobs", '-KeepGoing')
    $again = @($bs, '-Phase', 'game', '-Native', '-Tag', "${tag}r", '-Jobs', "$Jobs", '-PrelinkJobs', "$Jobs",
        '-KeepGoing', '-SkipConfigure')
}
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
$stageArgs = @("$A\stage-snap-bin.ps1", '-Variant', $Stage, '-SnapTag', $SnapTag, '-BuildTag', $bt, '-RuntimeStrings', $rtStrings,
    '-ExeStrings', $exeStrings, '-ManifestNotesFile', $notes)
$stLog = "$A\$tag-stage-$Stage.log"
$c = Run 'stage' $stageArgs $stLog
foreach ($l in @(Get-Content $stLog | Select-Object -Last 2)) { Log "  $l" }
if ($c -ne 0) { Log "STOP: stage-snap-bin.ps1 exit $c (see $(Split-Path -Leaf $stLog))"; exit 13 }
foreach ($f in 'legodimensions.exe', 'legodimensions.map', 'rexruntime.dll', 'MANIFEST.txt') {
    $p = "$O\$f"
    if (Test-Path -LiteralPath $p) { Log ("  staged {0}: {1} B, sha256 {2}" -f $f, (Get-Item -LiteralPath $p).Length, (Get-FileHash -LiteralPath $p).Hash) }
}
if ($Stage -eq 'native') { Log "  native GPU fingerprint: $((Get-Content "$B\native-gpu-build.txt" -Raw).Trim())" }
Log ("DONE $SnapTag $Stage, total wall {0:N1}s" -f $t0.Elapsed.TotalSeconds)
exit 0

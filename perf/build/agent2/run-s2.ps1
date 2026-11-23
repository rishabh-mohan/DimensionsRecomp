# Agent 2 - batch 2 builds from S2 (snap-patch.py apply S2 onto build/agent2/snap1), run after Agent 1 ends the quiet
# window, as a run_command background task. It stops at the first failure; build/agent2/stop-snap.ps1 kills it.
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\run-s2.ps1 -Stage off
#       SDK build + install (snap1-sdk, -SkipConfigure: no CMake input changed and no SDK file is new), then the devoff2
#       game build (snap1-off, -SkipConfigure: the OFF tree has no CONFIGURE_DEPENDS glob), then
#       stage-snap-bin.ps1 -Variant off -> build/agent2/devoff2-bin
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\run-s2.ps1 -Stage native
#       native2 game build (snap1-on) WITH the explicit configure: S2 adds gpu_native/upload_legacy_paths.h, so the
#       CONFIGURE_DEPENDS glob (rexlego/CMakeLists.txt:731) would re-run CMake inside the build anyway. Configuring
#       first keeps the order configure (incl. the new prepare_plume.py --check) -> gen-check -> gate -> compile.
#       Then stage-snap-bin.ps1 -Variant native -> build/agent2/native2-bin
# rexruntime.dll reaches a game tree only through the exe's POST_BUILD copy (rexglue_helpers.cmake:105-108). If the
# tree's copy differs from snap1-sdk/install/bin after the build (the exe did not relink), the exe and map are renamed
# *.pre-<SnapTag> and the game phase runs again as tag <tag>r (gen-check + gate + relink). Nothing is hand-copied.
# Log: build/agent2/<tag>-run.txt (+ build-snap's <tag>-steps.txt and logs, and <tag>-stage-<stage>.log).
param([ValidateSet('off', 'native')][string]$Stage = 'off', [int]$Jobs = 10, [string]$SnapTag = 'S2')
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
$A = "$R\build\agent2"
if ($SnapTag -notmatch '^S(\d+)$') { Write-Host "bad -SnapTag $SnapTag"; exit 2 }
$tag = 'snap' + $Matches[1]
$runLog = "$A\$tag-run.txt"
# S2-specific literals (16+ chars, new in S2; none is in the S1 sources): Agent 12's #22 cvar name and description
# (rexruntime.dll) and Agent 5's / Agent 7's new environment toggles (native exe)
$rtStrings = 'audio_shutdown_detach_worker,leave it running and leak what it can still reach'
$exeStrings = 'LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD,LEGO_NATIVE_FPS_CELL_RECTS,LEGO_NATIVE_TEXTURE_STAGING_POOL'
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
$B = $(if ($Stage -eq 'off') { "$A\snap1-off" } else { "$A\snap1-on" })
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
Log "START $SnapTag $Stage (tag $tag, -j $Jobs)"
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
$stageArgs = @("$A\stage-snap-bin.ps1", '-Variant', $Stage, '-SnapTag', $SnapTag, '-BuildTag', $bt, '-RuntimeStrings', $rtStrings)
if ($Stage -eq 'native') { $stageArgs += @('-ExeStrings', $exeStrings) }
$stLog = "$A\$tag-stage-$Stage.log"
$c = Run 'stage' $stageArgs $stLog
foreach ($l in @(Get-Content $stLog | Select-Object -Last 2)) { Log "  $l" }
if ($c -ne 0) { Log "STOP: stage-snap-bin.ps1 exit $c (see $(Split-Path -Leaf $stLog))"; exit 13 }
Log ("DONE $SnapTag $Stage, total wall {0:N1}s" -f $t0.Elapsed.TotalSeconds)
exit 0

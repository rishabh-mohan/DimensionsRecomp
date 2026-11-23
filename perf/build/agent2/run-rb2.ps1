# Agent 2 - rollback build RB2 on an S3 base, at Agent 1's GO only (task #14): a clone of
# build/agent9/repin/rb2-nomusttail/run-b.ps1 (Agent 9's re-pin of run-b.ps1 for recipe step 9.2), made by
# build/agent2/make-rb-clones.py (diffs: build/agent2/RB-diffs). Agent 1, 03:11: the base is snap1's current tree (S3
# or S3d) in the new copy build\agent2\snapB3 (prep-rb2.py); snapB and snapB-off stay untouched; A = devoff3-bin.
# Changed from the re-pin: snapB -> snapB3 (copy, game tree snapB3-off, build tag, logs, notes), -Out
# devoffRB2-bin, -SnapTag (default: the tag prep-rb2.py copied, read from snapB3-manifest-notes.txt; another value
# is refused), -Compare devoff3-bin (it must be staged; -Out must not be), the S3 exe string (as devoff3), the guards
# (08:30-12:00, -Jobs <= 10, no other snapshot build driver) and the staged-hash log lines.
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\run-rb2.ps1 [-Jobs 10] [-SkipConfigure] [-NoBuild]
# The re-pin's text follows (snapB renamed snapB3).
# Agent 2 - codegen build B (Agent 9's codegen option, perf-notes/agent9-codegen.md "Session 2: regen+build recipe")
# from build/agent2/snapB3 (prepared by prep-b.py), run only when Agent 1 schedules it, as a run_command background
# task. It stops at the first failure; build/agent2/stop-snap.ps1 kills it.
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\run-b.ps1 [-Jobs 10] [-SkipConfigure] [-NoBuild]
# 0. Refuses (exit 3) unless the install tree is build\agent9\install\batch-nolr (Agent 1, 02:05: never install\batch,
#    whose skip_lr is unsafe for LEGO), its SHA256SUMS.txt is the pinned 24CE1493... and snapB3's
#    legodimensions_config.toml is the pinned E60EAF1C... (= configs\batch-nolr.toml). -Install exists only for the
#    negative test.
# 1. build-snap.ps1 -Phase game -Tag snapB3 -SnapDir build\agent2\snapB3\DimensionsRecomp -GameDir build\agent2\snapB3-off
#    -CodegenExe build\agent2\codegen-frozen\codegen-frozen2.exe -GenBase build\agent9\install\batch-nolr\generated
#    -KeepGoing: OFF configure (fresh tree; skipped with -SkipConfigure) -> gen-check (batch-nolr reference) -> gate (432
#    = 430 TUs + init + register) -> full build (PCH + 430 TUs + init + register). -k 0, so one run lists every failing
#    TU (a musttail failure is Agent 9's rollback 2). -NoBuild stops after the gate.
# 2. rexruntime.dll in snapB3-off must equal snap1-sdk/install/bin (the exe's POST_BUILD copy; a fresh tree always links).
# 3. stage-snap-bin.ps1 -Variant off -SnapTag <prep tag> -BuildTag snapB3 -GameTree snapB3-off -OutDir build\agent2\devoffRB2-bin
#    -GameSnap snapB3\DimensionsRecomp -CompareBin build\agent2\devoff3-bin (A) -ManifestNotesFile snapB3-manifest-notes.txt
# Log: build/agent2/snapB3-run.txt (+ build-snap's snapB3-steps.txt and snapB3-*.log, and snapB3-stage.log).
param([int]$Jobs = 10, [switch]$SkipConfigure, [switch]$NoBuild, [string]$Out = 'devoffRB2-bin', [string]$SnapTag = '',
    [string]$Compare = 'devoff3-bin', [string]$Install = 'build\agent9\install\rb2-nomusttail')
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
$A = "$R\build\agent2"
$runLog = "$A\snapB3-run.txt"
$snapB3 = "$A\snapB3\DimensionsRecomp"; $gameB = "$A\snapB3-off"; $notes = "$A\snapB3-manifest-notes.txt"
# the S3 SDK, as devoff3 (run-s3.ps1): Agent 12's #22 cvar name and description are in rexruntime.dll, and the tail of
# Agent 12's pause_safe_order description (share/rex_app.cpp, compiled into the game) is in the exe
$rtStrings = 'audio_shutdown_detach_worker,leave it running and leak what it can still reach'
$exeStrings = 'which can hang when the guest pauses'
function Log([string]$m) {
    $line = "$(Get-Date -Format HH:mm:ss) [B] $m"
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
# guards (task #14): no start 08:30-12:00 (no builds from 08:30), -Jobs capped at 10, no other snapshot build driver
# (\bb-chain: not this script's own rb-chain.ps1 parent)
$tod = (Get-Date).TimeOfDay
if ($tod -ge [TimeSpan]'08:30:00' -and $tod -lt [TimeSpan]'12:00:00') { Log 'STOP: no builds from 08:30 (session-3 rule)'; exit 3 }
if ($Jobs -gt 10) { Log "-Jobs $Jobs capped at 10"; $Jobs = 10 }
$drv = @(Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -match 'run-b\.ps1|\bb-chain\.ps1|run-s2\.ps1|run-s3\.ps1|run-s3d\.ps1|run-rb1\.ps1|run-nb\.ps1|build-snap\.ps1|stage-snap-bin\.ps1' })
if ($drv.Count) { Log "STOP: another snapshot build driver is running (pid $($drv[0].ProcessId): $($drv[0].CommandLine))"; exit 4 }
$t0 = [Diagnostics.Stopwatch]::StartNew()
Log "START rollback build RB2 (snapshot copy $snapB3, game tree $gameB, -j $Jobs, install tree $Install)"
# 0. only install\batch-nolr, with the pinned hashes; checked before anything is built or written
$nolr = "$R\build\agent9\install\rb2-nomusttail"  # rollback re-pin (Agent 9, recipe step 9.2): was batch-nolr
$inst = $(if ([IO.Path]::IsPathRooted($Install)) { $Install } else { Join-Path $R $Install })
$inst = [IO.Path]::GetFullPath($inst).TrimEnd('\')
if ($inst -ne $nolr) { Log "STOP: refusing install tree $inst : build B uses only $nolr (install\batch has skip_lr, unsafe for LEGO); nothing built"; exit 3 }
$it = Get-Item -LiteralPath $nolr -Force -ErrorAction SilentlyContinue
if (-not $it -or $it.LinkType) { Log "STOP: $nolr is missing or a link"; exit 3 }
$sumsSha = (Get-FileHash -LiteralPath "$nolr\SHA256SUMS.txt").Hash
if ($sumsSha -ne '8BDE87171405EC9611B89CD75BADC400DD93BC371CFBA3634B7B446FCF9D7B14') { Log "STOP: $nolr\SHA256SUMS.txt is $sumsSha, not the pinned 8BDE8717..."; exit 3 }
if (-not (Test-Path $notes)) { Log 'STOP: run prep-rb2.py first (no snapB3-manifest-notes.txt)'; exit 2 }
$tl = @(Select-String -LiteralPath $notes -Pattern '^snapB3 = build/agent2/snap1/DimensionsRecomp at (S\d+[a-z]*), copied by prep-rb2\.py ')
if ($tl.Count -ne 1) { Log 'STOP: snapB3-manifest-notes.txt was not written by prep-rb2.py (no snapshot tag line)'; exit 2 }
$prepTag = $tl[0].Matches[0].Groups[1].Value
if (-not $SnapTag) { $SnapTag = $prepTag } elseif ($SnapTag -ne $prepTag) { Log "STOP: -SnapTag $SnapTag, but prep-rb2.py copied snap1 at $prepTag"; exit 3 }
if (-not (Test-Path -LiteralPath "$A\$Compare\MANIFEST.txt")) { Log "STOP: $Compare is not staged (no MANIFEST.txt; it is the -CompareBin reference)"; exit 4 }
if (Test-Path -LiteralPath "$A\$Out\MANIFEST.txt") { Log "STOP: $Out is already staged (MANIFEST.txt exists); pass another -Out"; exit 4 }
Log "snapshot tag $SnapTag (the prep-rb2.py copy); A = $Compare; out $Out"
$cfgSha = (Get-FileHash -LiteralPath "$snapB3\rexlego\legodimensions_config.toml").Hash
if ($cfgSha -ne 'FC034D495DAC395F45CDC0AC0DC7BFD88C8D2046A09590B88563B63BE1C82924') { Log "STOP: snapB3 legodimensions_config.toml is $cfgSha, not the pinned rb2-nomusttail config FC034D49..."; exit 3 }
Log "pins match: install tree $nolr (SHA256SUMS.txt $($sumsSha.Substring(0, 16))), snapB3 config $($cfgSha.Substring(0, 16))"
$bsArgs = @("$A\build-snap.ps1", '-Phase', 'game', '-Tag', 'snapB3', '-Jobs', "$Jobs", '-KeepGoing', '-SnapDir', $snapB3,
    '-GameDir', $gameB, '-CodegenExe', "$A\codegen-frozen\codegen-frozen2.exe", '-GenBase', "$nolr\generated")
if ($SkipConfigure) { $bsArgs += '-SkipConfigure' }
if ($NoBuild) { $bsArgs += '-NoBuild' }
$c = Run 'build' $bsArgs ''
if ($c -ne 0) { Log "STOP: build-snap.ps1 exit $c (see snapB3-steps.txt)"; exit 10 }
if ($NoBuild) { Log ("DONE -NoBuild (configure, gen-check, gate), total wall {0:N1}s" -f $t0.Elapsed.TotalSeconds); exit 0 }
$h2 = (Get-FileHash -LiteralPath "$A\snap1-sdk\install\bin\rexruntime.dll").Hash
$h1 = (Get-FileHash -LiteralPath "$gameB\rexruntime.dll").Hash
if ($h1 -ne $h2) { Log "STOP: rexruntime.dll in snapB3-off ($($h1.Substring(0, 16))) != snap1-sdk/install/bin ($($h2.Substring(0, 16)))"; exit 11 }
Log "rexruntime.dll in snapB3-off == install/bin ($($h2.Substring(0, 16)))"
$what = "codegen build B: dev OFF build from $SnapTag with Agent 9's rb2-nomusttail codegen options (rollback step 9.2), NATIVE_GPU=OFF"
$cgNote = "codegen: Agent 9's rb2-nomusttail options (build/agent9/install/rb2-nomusttail, 429 TUs, no skip_lr; rollback step 9.2: batch-nolr minus musttail_calls; the snapB3 generated output hash-checked against that install tree by gen-check.py --base; the codegen-frozen2.exe stand-in writes nothing)"
$stageArgs = @("$A\stage-snap-bin.ps1", '-Variant', 'off', '-SnapTag', $SnapTag, '-BuildTag', 'snapB3', '-GameTree', $gameB,
    '-OutDir', "$A\$Out", '-GameSnap', $snapB3, '-CompareBin', "$A\$Compare", '-RuntimeStrings', $rtStrings,
    '-ExeStrings', $exeStrings, '-WhatText', $what, '-CodegenNote', $cgNote, '-ManifestNotesFile', $notes)
$stLog = "$A\snapB3-stage.log"
$c = Run 'stage' $stageArgs $stLog
foreach ($l in @(Get-Content $stLog | Select-Object -Last 2)) { Log "  $l" }
if ($c -ne 0) { Log "STOP: stage-snap-bin.ps1 exit $c (see $(Split-Path -Leaf $stLog))"; exit 13 }
foreach ($f in 'legodimensions.exe', 'legodimensions.map', 'rexruntime.dll', 'rexgpu-xenos.dll', 'MANIFEST.txt') {
    $p = "$A\$Out\$f"
    if (Test-Path -LiteralPath $p) { Log ("  staged {0}: {1} B, sha256 {2}" -f $f, (Get-Item -LiteralPath $p).Length, (Get-FileHash -LiteralPath $p).Hash) }
}
$man = @(Get-Content -Encoding UTF8 -LiteralPath "$A\$Out\MANIFEST.txt")
$cnt = @(foreach ($t in 'S1', 'S2', 'S3', 'S3d') { "$t $(@($man | Where-Object { $_.StartsWith("#   $t ") }).Count)" })
$np = @($man | Where-Object { $_.StartsWith('#   PASS ') }).Count; $nf = @($man | Where-Object { $_.StartsWith('#   FAIL ') }).Count
$nn = @($man | Where-Object { $_.StartsWith('#   NOTE ') }).Count
Log "  MANIFEST patch rows: $($cnt -join ' / '); checks: $np PASS / $nf FAIL / $nn NOTE"
Log ("DONE rollback build RB2 -> $Out, total wall {0:N1}s" -f $t0.Elapsed.TotalSeconds)
exit 0

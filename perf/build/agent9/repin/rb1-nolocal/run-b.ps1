# Agent 2 - codegen build B (Agent 9's codegen option, perf-notes/agent9-codegen.md "Session 2: regen+build recipe")
# from build/agent2/snapB (prepared by prep-b.py), run only when Agent 1 schedules it, as a run_command background
# task. It stops at the first failure; build/agent2/stop-snap.ps1 kills it.
#   powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\run-b.ps1 [-Jobs 10] [-SkipConfigure] [-NoBuild]
# 0. Refuses (exit 3) unless the install tree is build\agent9\install\batch-nolr (Agent 1, 02:05: never install\batch,
#    whose skip_lr is unsafe for LEGO), its SHA256SUMS.txt is the pinned 24CE1493... and snapB's
#    legodimensions_config.toml is the pinned E60EAF1C... (= configs\batch-nolr.toml). -Install exists only for the
#    negative test.
# 1. build-snap.ps1 -Phase game -Tag snapB -SnapDir build\agent2\snapB\DimensionsRecomp -GameDir build\agent2\snapB-off
#    -CodegenExe build\agent2\codegen-frozen\codegen-frozen2.exe -GenBase build\agent9\install\batch-nolr\generated
#    -KeepGoing: OFF configure (fresh tree; skipped with -SkipConfigure) -> gen-check (batch-nolr reference) -> gate (432
#    = 430 TUs + init + register) -> full build (PCH + 430 TUs + init + register). -k 0, so one run lists every failing
#    TU (a musttail failure is Agent 9's rollback 2). -NoBuild stops after the gate.
# 2. rexruntime.dll in snapB-off must equal snap1-sdk/install/bin (the exe's POST_BUILD copy; a fresh tree always links).
# 3. stage-snap-bin.ps1 -Variant off -SnapTag S2 -BuildTag snapB -GameTree snapB-off -OutDir build\agent2\devoffB-bin
#    -GameSnap snapB\DimensionsRecomp -CompareBin build\agent2\devoff2-bin (A) -ManifestNotesFile snapB-manifest-notes.txt
# Log: build/agent2/snapB-run.txt (+ build-snap's snapB-steps.txt and snapB-*.log, and snapB-stage.log).
param([int]$Jobs = 10, [switch]$SkipConfigure, [switch]$NoBuild, [string]$Out = 'devoffB-bin', [string]$SnapTag = 'S2',
    [string]$Compare = 'devoff2-bin', [string]$Install = 'build\agent9\install\rb1-nolocal')
$ErrorActionPreference = 'Continue'
$R = '<workspace>'
$A = "$R\build\agent2"
$runLog = "$A\snapB-run.txt"
$snapB = "$A\snapB\DimensionsRecomp"; $gameB = "$A\snapB-off"; $notes = "$A\snapB-manifest-notes.txt"
# the same SDK as devoff2 (S2): Agent 12's #22 cvar name and description are in rexruntime.dll
$rtStrings = 'audio_shutdown_detach_worker,leave it running and leak what it can still reach'
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
$t0 = [Diagnostics.Stopwatch]::StartNew()
Log "START codegen build B from $SnapTag (snapshot copy $snapB, game tree $gameB, -j $Jobs, install tree $Install)"
# 0. only install\batch-nolr, with the pinned hashes; checked before anything is built or written
$nolr = "$R\build\agent9\install\rb1-nolocal"  # rollback re-pin (Agent 9, recipe step 9.1): was batch-nolr
$inst = $(if ([IO.Path]::IsPathRooted($Install)) { $Install } else { Join-Path $R $Install })
$inst = [IO.Path]::GetFullPath($inst).TrimEnd('\')
if ($inst -ne $nolr) { Log "STOP: refusing install tree $inst : build B uses only $nolr (install\batch has skip_lr, unsafe for LEGO); nothing built"; exit 3 }
$it = Get-Item -LiteralPath $nolr -Force -ErrorAction SilentlyContinue
if (-not $it -or $it.LinkType) { Log "STOP: $nolr is missing or a link"; exit 3 }
$sumsSha = (Get-FileHash -LiteralPath "$nolr\SHA256SUMS.txt").Hash
if ($sumsSha -ne 'A966CF18E3EC736F5685CA413A93C7E97B436547560E285894D43D4E1A9ED917') { Log "STOP: $nolr\SHA256SUMS.txt is $sumsSha, not the pinned A966CF18..."; exit 3 }
if (-not (Test-Path $notes)) { Log 'STOP: run prep-b.py first (no snapB-manifest-notes.txt)'; exit 2 }
$cfgSha = (Get-FileHash -LiteralPath "$snapB\rexlego\legodimensions_config.toml").Hash
if ($cfgSha -ne 'AE9F8F967FBB264919A63463CA4958F856C18A0405A4895440D6C36A31084EEC') { Log "STOP: snapB legodimensions_config.toml is $cfgSha, not the pinned rb1-nolocal config AE9F8F96..."; exit 3 }
Log "pins match: install tree $nolr (SHA256SUMS.txt $($sumsSha.Substring(0, 16))), snapB config $($cfgSha.Substring(0, 16))"
$bsArgs = @("$A\build-snap.ps1", '-Phase', 'game', '-Tag', 'snapB', '-Jobs', "$Jobs", '-KeepGoing', '-SnapDir', $snapB,
    '-GameDir', $gameB, '-CodegenExe', "$A\codegen-frozen\codegen-frozen2.exe", '-GenBase', "$nolr\generated")
if ($SkipConfigure) { $bsArgs += '-SkipConfigure' }
if ($NoBuild) { $bsArgs += '-NoBuild' }
$c = Run 'build' $bsArgs ''
if ($c -ne 0) { Log "STOP: build-snap.ps1 exit $c (see snapB-steps.txt)"; exit 10 }
if ($NoBuild) { Log ("DONE -NoBuild (configure, gen-check, gate), total wall {0:N1}s" -f $t0.Elapsed.TotalSeconds); exit 0 }
$h2 = (Get-FileHash -LiteralPath "$A\snap1-sdk\install\bin\rexruntime.dll").Hash
$h1 = (Get-FileHash -LiteralPath "$gameB\rexruntime.dll").Hash
if ($h1 -ne $h2) { Log "STOP: rexruntime.dll in snapB-off ($($h1.Substring(0, 16))) != snap1-sdk/install/bin ($($h2.Substring(0, 16)))"; exit 11 }
Log "rexruntime.dll in snapB-off == install/bin ($($h2.Substring(0, 16)))"
$what = "codegen build B: dev OFF build from $SnapTag with Agent 9's rb1-nolocal codegen options (rollback step 9.1), NATIVE_GPU=OFF"
$cgNote = "codegen: Agent 9's rb1-nolocal options (build/agent9/install/rb1-nolocal, 434 TUs, no skip_lr; rollback step 9.1: batch-nolr minus ctr_as_local, xer_as_local, reserved_as_local, cr_as_local, cr_compare_so_zero; the snapB generated output hash-checked against that install tree by gen-check.py --base; the codegen-frozen2.exe stand-in writes nothing)"
$stageArgs = @("$A\stage-snap-bin.ps1", '-Variant', 'off', '-SnapTag', $SnapTag, '-BuildTag', 'snapB', '-GameTree', $gameB,
    '-OutDir', "$A\$Out", '-GameSnap', $snapB, '-CompareBin', "$A\$Compare", '-RuntimeStrings', $rtStrings,
    '-WhatText', $what, '-CodegenNote', $cgNote, '-ManifestNotesFile', $notes)
$stLog = "$A\snapB-stage.log"
$c = Run 'stage' $stageArgs $stLog
foreach ($l in @(Get-Content $stLog | Select-Object -Last 2)) { Log "  $l" }
if ($c -ne 0) { Log "STOP: stage-snap-bin.ps1 exit $c (see $(Split-Path -Leaf $stLog))"; exit 13 }
Log ("DONE codegen build B -> $Out, total wall {0:N1}s" -f $t0.Elapsed.TotalSeconds)
exit 0
